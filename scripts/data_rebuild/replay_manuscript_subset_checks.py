#!/usr/bin/env python3
"""Reexecute five existing manuscript Table-4 checks with original model functions.

The old manuscript reports rounded benchmarks only for these checks. Their
baseline comparison is explicitly at published precision, not decoded-byte
identity to a nonexistent archived executable table. Primary legacy gates are
unchanged. No specification search or new TV definition is performed.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.data_rebuild import reproduce_october_scientific_v2 as core
from scripts.data_rebuild.october_corrected_chronology import verify_shared_commit,SHARED_COMMIT
from scripts.data_rebuild.run_full_october_suite_from_generated_panel import verify_october_runtime

MARKER='# Original main result reproduction and all-star-only check (both TV definitions).'
SPECS=[('exclude_2025','announced_tv_primary',['2020-21','2021-22','2022-23','2023-24','2024-25'],149873,2.22),
       ('exclude_pandemic_linear','tv_harmonized_linear',['2022-23','2023-24','2024-25','2025-26'],123449,2.24),
       ('exclude_pandemic_partner','announced_tv_primary',['2022-23','2023-24','2024-25','2025-26'],123449,3.68),
       ('common_sample_partner','announced_tv_primary',['2021-22','2022-23','2023-24','2024-25'],123074,1.94),
       ('common_sample_add_nba_tv','partner_plus_nba_tv',['2021-22','2022-23','2023-24','2024-25'],123074,.85)]


def broaden_known_tv(frame):
    known={'NBA TV','ESPN','TNT','ABC','ABC/ESPN'}
    if not set(frame.network_announced.dropna())<=known:
        raise ValueError('Unexpected historical network encoding in complete-coverage seasons')
    flags=frame.announced_tv_primary.map(core.rules.strict_bool)
    return (flags|frame.network_announced.eq('NBA TV')).astype(float)


def validate_panels(root):
    expected={'legacy':core.CORRECTED_SHA,core.PRIMARY:'9dde4578c852f15c317c1214718e1eabe9f60b740b5f2ddb4fed15b53185802f'}
    paths={}
    for name,h in expected.items():
        p=root/('chronology__'+name)/core.PANEL;core.no_symlink(p)
        if not p.is_file() or core.identities(p)['decoded_sha256']!=h:
            raise ValueError('Actual accepted scientific/legacy panel required: '+name)
        paths[name]=p
    return paths


def build(root,shared,out):
    core.fresh_output(out,[root,shared]);panels=validate_panels(root)
    verify_shared_commit(shared);environment=verify_october_runtime(Path(sys.executable))
    source=shared/'scripts/october_2026/run_base.py';text=source.read_text();source_sha=core.sha(source)
    if text.count(MARKER)!=1:raise ValueError('Original model function boundary changed')
    prefix=text.split(MARKER)[0];results={};out.mkdir(parents=True)
    for version,panel in panels.items():
        case=out/version;inputs=case/'inputs';(inputs/'data_intermediate').mkdir(parents=True);(inputs/'data_final').mkdir()
        shutil.copy2(panel,inputs/'data_intermediate'/core.PANEL)
        shutil.copy2(shared/'data_final/player_game_panel_analysis_ready.csv.gz',inputs/'data_final/player_game_panel_analysis_ready.csv.gz')
        before=core.sha(panel)
        line=next(x for x in prefix.splitlines() if x.startswith('W=Path('))
        code=prefix.replace(line,f"W=Path({str(inputs)!r}); O=Path({str(case)!r}); O.mkdir(parents=True,exist_ok=True)")
        fill="D['star_allstar_only']=D.groupby(['nba_player_id','season']).star_allstar_only.ffill().bfill().fillna(D.star_PPP_it).astype(float)"
        if code.count(fill)!=1:raise ValueError('Original All-Star-only fill context changed')
        code=code.replace(fill,"_join_missing=int(D.star_allstar_only.isna().sum())\n"+fill)
        code+=f'''\nimport json\nfrom scripts.data_rebuild.replay_manuscript_subset_checks import broaden_known_tv\nSPECS={SPECS!r}\nRESULTS=[]\nfor label,tv,seasons,expected_n,reference in SPECS:\n q=R.loc[R.season.isin(seasons)].copy()\n if tv=='partner_plus_nba_tv':q[tv]=broaden_known_tv(q)\n T,V=triple(q,tv,'star_PPP_it',label)\n row=T.loc[T.term.eq('triple')].iloc[0]\n if not bool(row.converged):raise ValueError('Original subset fit did not converge')\n if int(row.n)!=expected_n:raise ValueError('Historical manuscript subset sample differs')\n if {version!r}=='legacy' and abs(float(row.estimate_pp)-reference)>.005:raise ValueError('Legacy manuscript rounded coefficient differs')\n RESULTS.append({{'name':label,'tv':tv,'seasons':seasons,'n':int(row.n),'estimate_pp':float(row.estimate_pp),'se_pp':float(row.se_pp),'low_pp':float(row.low_pp),'high_pp':float(row.high_pp),'p':float(row.p),'iterations':int(row.iterations),'converged':bool(row.converged)}})\nreport={{'models':RESULTS,'AllStar_only_vs_PPP_at_risk_differences':int(R.star_allstar_only.ne(R.star_PPP_it).sum()),'missing_exact_AllStar_only_join_before_fill':_join_missing,'original_model_functions_unchanged':True}}\n(O/'subset_report.json').write_text(json.dumps(report,indent=2)+'\\n')\n'''
        required={n:core.sha(inputs/n) for n in ('data_intermediate/'+core.PANEL,'data_final/player_game_panel_analysis_ready.csv.gz')}
        receipt=core.execute(code.encode(),inputs,case/'execution',required,panel_mode=False)
        report=json.loads((case/'subset_report.json').read_text());report['actual_execution']=receipt
        if core.sha(panel)!=before:raise ValueError('Accepted source panel changed')
        results[version]=report;core.save(case/'acceptance.json',report)
    if core.sha(source)!=source_sha:raise ValueError('Original model source changed')
    verify_shared_commit(shared)
    report={'status':'passed_original_function_and_historical_rounded_baseline_gates','original_source_sha256':source_sha,
            'original_source_commit':SHARED_COMMIT,'environment':environment,
            'comparison_scope':'Legacy N exact; legacy coefficients at original manuscript rounded precision. All complete original model output tables retained.',
            'scope':'Five already documented manuscript subset checks; no specification search','results':results}
    core.save(out/'manuscript_subset_comparison.json',report);return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('scientific-run','shared-repo','output-root'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=build(a.scientific_run.absolute(),a.shared_repo.absolute(),a.output_root.absolute())
    print(json.dumps({'status':r['status'],'models_per_version':5}))


if __name__=='__main__':main()
