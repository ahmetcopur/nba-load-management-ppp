#!/usr/bin/env python3
"""Separate scientific-version paper statistics/figures; no manuscript mutation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import pandas as pd
from scripts.data_rebuild import reproduce_october_scientific_v2 as primary
from scripts.data_rebuild import run_october_scientific_v2_suite as suite
from scripts.data_rebuild import rebuild_missing_october_paper_statistics as original


def rate_cells(records,group_column,numerator,denominator,rate):
    """Require all eight actual groups; never fill a missing rate with zero."""
    frame=pd.DataFrame(records);keys=['star_PPP_it','postPPP',group_column]
    if frame.duplicated(keys).any() or len(frame)!=8:raise ValueError('Incomplete/duplicate eight-cell table')
    for col in keys:frame[col]=frame[col].map(primary.rules.strict_bool)
    if set(map(tuple,frame[keys].to_numpy()))!={(s,p,g) for s in (False,True) for p in (False,True) for g in (False,True)}:
        raise ValueError('Unexpected descriptive identity')
    if (frame[denominator].le(0)|frame[numerator].lt(0)|frame[numerator].gt(frame[denominator])).any():
        raise ValueError('Invalid descriptive risk/onset count')
    computed=100*frame[numerator]/frame[denominator]
    if (computed-frame[rate]).abs().gt(1e-10).any():raise ValueError('Rate disagrees with counts')
    return frame.set_index(keys)


def plot_rates(records,group_column,numerator,rate,labels,title,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    table=rate_cells(records,group_column,numerator,'at_risk',rate)
    fig,axes=plt.subplots(1,2,figsize=(9,4.8),sharey=True,layout='constrained')
    colors={False:'#64748b',True:'#176b8d'}
    for ax,group in zip(axes,(False,True)):
        for star in (False,True):
            y=[float(table.loc[(star,post,group),rate]) for post in (False,True)]
            ax.plot([0,1],y,color=colors[star],marker='o',linewidth=2,label='Stars' if star else 'Nonstars')
            for x,value in enumerate(y):ax.annotate(f'{value:.2f}%',(x,value),xytext=(0,7),textcoords='offset points',ha='center',fontsize=9)
        ax.set(title=labels[group],xticks=[0,1],xticklabels=['Pre-PPP','Post-PPP'],xlim=(-.2,1.2))
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.18)
        ax.set_ylim(0,float(table[rate].max())*1.23)
    axes[0].set_ylabel('Onsets per 100 at-risk player-games');axes[1].legend(frameon=False,loc='upper right')
    fig.suptitle(title,fontsize=13)
    fig.supxlabel('Descriptive rates; SCI-001-only corrected chronology. No causal interpretation or confidence intervals.',fontsize=8)
    for suffix in ('.png','.pdf','.svg'):fig.savefig(output.with_suffix(suffix),dpi=180)
    plt.close(fig)


def build(run_root,output):
    primary.fresh_output(output,[run_root]);manifest=suite.authenticate(run_root)
    before=primary.sha(run_root/'scientific_version_manifest.json');output.mkdir(parents=True)
    reports={};inputs={}
    for version in ('legacy',primary.PRIMARY):
        path=run_root/('chronology__'+version)/primary.PANEL
        inputs[version]=primary.identities(path)
        result=original.compute(path)
        if primary.identities(path)!=inputs[version]:raise ValueError('Scientific input changed during paper calculations')
        reports[version]=result
        primary.save(output/(version+'_paper_statistics.json'),result)
        for name in ('onset_cells','prevalence_cells','home_onegame_cells','duration'):
            pd.DataFrame(result[name]).to_csv(output/(version+'_'+name+'.csv'),index=False)
    corrected=reports[primary.PRIMARY]
    plot_rates(corrected['onset_cells'],'announced_tv_primary','onsets','onset_rate_pct',
               {False:'Other games',True:'National-partner TV games'},'Absence-onset rates by TV exposure',output/'scientific_v2_raw_TV_onset_rates')
    plot_rates(corrected['home_onegame_cells'],'is_home','onegame_onsets','onegame_rate_pct',
               {False:'Road games',True:'Home games'},'One-game absence-onset rates: home and road',output/'scientific_v2_home_road_onegame_rates')
    if primary.sha(run_root/'scientific_version_manifest.json')!=before:raise ValueError('Primary manifest changed')
    source=Path(original.__file__)
    report={'status':'computed_pending_human_review','scientific_version':primary.PRIMARY,
            'primary_manifest_sha256':before,'input_panels':inputs,'statistics':reports,
            'original_statistics_source_sha256':primary.sha(source),'executed_entrypoint_sha256':primary.sha(Path(__file__)),
            'figures':{p.name:primary.identities(p) for p in sorted(output.glob('scientific_v2_*'))},
            'historical_artifact_verdict':manifest['historical_artifact_verdict'],
            'manuscript_modified':False,'plot_scope':'New descriptive review figures computed from newly built panel; not a replacement of manuscript figures without approval'}
    primary.save(output/'scientific_paper_impact.json',report);return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scientific-run',required=True,type=Path);p.add_argument('--output-root',required=True,type=Path)
    a=p.parse_args();r=build(a.scientific_run.absolute(),a.output_root.absolute())
    print(json.dumps({'status':r['status'],'manuscript_modified':False}))


if __name__=='__main__':main()
