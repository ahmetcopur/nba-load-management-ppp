#!/usr/bin/env python3
"""Explicit SCI-001 correction from the authenticated retained six-season run.

No historical command, source, acceptance target or frozen panel is modified.
The physical-game workload convention is an OPTIONAL, unadopted sensitivity.
"""
from __future__ import annotations
import argparse
import csv
import difflib
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import zipfile
import pandas as pd
import numpy as np
from scipy.stats import norm

REPO=Path(__file__).resolve().parents[2]
if __package__ in (None,''):sys.path.insert(0,str(REPO))
from scripts.data_rebuild.private_source_paths import under_git
from scripts.data_rebuild import fixture_date_chronology_sensitivity as chronology
from scripts.data_rebuild import run_historical_cadence_builder as legacy
from scripts.data_rebuild import october_scientific_v2_rules as rules
from scripts.data_rebuild.october_scientific_v2_compare import compare, summary, identities
from scripts.data_rebuild.audit_star_status_against_calendar import evaluate as semantic_check
from scripts.data_rebuild.restore_historical_layout import build_plan

SOURCE=legacy.SCRIPT
PANEL='player_team_game_harmonized_cadence.csv.gz'
CALENDAR='scientific/star_calendar.csv'
STAR_ARCHIVE='nba_player_game_at_risk_star_v1.zip'
STAR_SHA='6513069ffc81535edc2af04acbb7550f227fb074ea51241e0e800cebe9f1eb70'
FROZEN_SHA='3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac'
CORRECTED_SHA='2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67'
BASE_SHA='5154317fc52157716cf22f7c5a535259e9f073b3391fd52d78a01faaf8d96d77'
PUBLIC=REPO/'validation/six_season_end_to_end_2026-11-15/final_dataset_manifest.json'
EVIDENCE_REF=REPO/'validation/scientific_integrity_audit_2026-11-15/execution_evidence_check.json'
PRIMARY='october_scientific_v2'
AUX=['cadence_2025/player_crosswalk_final.csv','cadence_work/player_alias_table.csv']
ENV={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(path,value):
    temporary=path.with_name(path.name+'.pending')
    with temporary.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    os.link(temporary,path)  # Exclusive publication; never overwrite an existing manifest.
    temporary.unlink()


def no_symlink(path):
    if any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('Unexpected symlink in private path')


def fresh_output(output,inputs):
    no_symlink(output.absolute())
    if output.exists() or under_git(output):raise ValueError('Use a fresh output root OUTSIDE Git')
    out=output.resolve()
    for path in inputs:
        path=path.resolve()
        if out==path or out in path.parents or path in out.parents:
            raise ValueError('Scientific output and source paths must be disjoint')


def expected_inputs():
    return json.loads(PUBLIC.read_text())['six_season_generated_input_consumption']['required_sha256']


def runtime():
    from importlib.metadata import version
    expected={'pandas':'2.2.3','numpy':'2.3.5','scipy':'1.17.0','statsmodels':'0.14.6'}
    actual={k:version(k) for k in expected}
    if sys.version_info[:2]!=(3,12) or sys.platform!='linux' or platform.machine().lower() not in ('x86_64','amd64'):
        raise ValueError('Scientific acceptance requires Python 3.12 on Linux amd64')
    if actual!=expected:raise ValueError('Use requirements-builder-lock.txt: '+str(actual))
    return {'python':sys.version,'platform':platform.platform(),'packages':actual}


def code_identity():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip():
        raise ValueError('Scientific acceptance requires a clean committed checkout')
    files=[SOURCE,Path(__file__),REPO/'scripts/data_rebuild/october_scientific_v2_rules.py',
           REPO/'scripts/data_rebuild/october_scientific_v2_compare.py',
           REPO/'scripts/data_rebuild/retained_scientific_inputs.py',
           REPO/'scripts/data_rebuild/audit_star_status_against_calendar.py',
           REPO/'scripts/data_rebuild/fixture_date_chronology_sensitivity.py',
           REPO/'scripts/data_rebuild/audit_fixture_date_swap_covariates.py']
    return {'commit':head,'file_sha256':{str(p.relative_to(REPO)):sha(p) for p in files}}


def safe_relative(name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name:raise ValueError('Unsafe relative input path')
    return p


def tree_hashes(path):
    no_symlink(path)
    if not path.is_dir():raise FileNotFoundError(path)
    result={}
    for p in sorted(path.rglob('*')):
        if p.is_symlink():raise ValueError('Symlinked retained source member')
        if p.is_file():result[str(p.relative_to(path))]=sha(p)
    return result


def preflight(retained,evidence,archives,output):
    fresh_output(output,[retained,evidence,archives])
    required=expected_inputs(); root=retained/'03_historical_cadence_inputs'
    needed=[retained/'final/final_dataset_manifest.json',retained/'logs/stages.jsonl',
            retained/'00c_six_season_sources/six_season_sources.json',evidence,
            *(root/n for n in required),root/chronology.BASE,*(root/n for n in AUX)]
    public=json.loads(PUBLIC.read_text())
    archive_hashes=public['input_archives_sha256']
    needed += [archives/n for n in archive_hashes]
    missing=[str(p) for p in needed if not p.is_file()]
    if missing:raise FileNotFoundError('Missing authenticated retained inputs:\n'+'\n'.join(missing))
    for p in needed:no_symlink(p)
    if under_git(retained) or under_git(archives):raise ValueError('Private source trees must be outside Git')
    if sha(evidence)!=json.loads(EVIDENCE_REF.read_text())['evidence_zip_sha256']:
        raise ValueError('Retained evidence ZIP SHA-256 differs from reviewed November 15 evidence')
    for n,h in archive_hashes.items():
        if sha(archives/n)!=h:raise ValueError('Original archive SHA-256 differs: '+n)
    native=json.loads((retained/'final/final_dataset_manifest.json').read_text())
    if (native.get('status')!='pass' or native.get('six_original_PDF_season_inputs_consumed') is not True
            or native.get('input_archives_sha256')!=archive_hashes
            or native.get('six_season_generated_input_consumption',{}).get('required_sha256')!=required):
        raise ValueError('Retained final acceptance is incomplete or inconsistent')
    for k,v in public['outputs'].items():
        if native.get('outputs',{}).get(k,{}).get('decoded_sha256')!=v['decoded_sha256']:
            raise ValueError('Retained output acceptance identities differ')
    events=[json.loads(x) for x in (retained/'logs/stages.jsonl').read_text().splitlines()]
    names=list(public['stage_logs'])
    # JSON object ordering in sanitized reports is not execution ordering.
    starts=[e.get('stage') for e in events if e.get('event')=='start']
    if len(starts)!=7 or set(starts)!=set(names) or [(e.get('stage'),e.get('event')) for e in events]!=[(n,e) for n in starts for e in ('start','finish')]:
        raise ValueError('Retained stage receipts are missing, duplicated or unordered')
    if any(e.get('exit_code')!=0 for e in events if e.get('event')=='finish'):
        raise ValueError('Retained stages did not finish successfully')
    with zipfile.ZipFile(evidence) as z:
        handoff=json.loads(z.read('fresh_run/03_historical_cadence_inputs/six_season_source_handoff.json'))
    src_manifest=retained/'00c_six_season_sources/six_season_sources.json'
    if sha(src_manifest)!=handoff['source_manifest_sha256']:
        raise ValueError('Retained source-stage manifest differs from authenticated execution evidence')
    src=json.loads(src_manifest.read_text())
    from scripts.data_rebuild.rebuild_six_season_october_sources import EXPECTED_COUNTS,controlled_exception
    if src.get('all_six_source_inputs_ready') is not True or set(src.get('cases',{}))!=set(EXPECTED_COUNTS) or src.get('original_archive_sha256')!=archive_hashes:
        raise ValueError('Incomplete retained six-season source provenance')
    old_log=Path(native['structured_stage_log'])
    if not old_log.is_absolute() or old_log.name!='stages.jsonl' or old_log.parent.name!='logs':
        raise ValueError('Expected original private run-root identity in manifest')
    oldroot=old_log.parents[1]; snapshots={p:sha(p) for p in needed}
    for season,record in src['cases'].items():
        if (record.get('pdfs'),record.get('rows'))!=EXPECTED_COUNTS[season]:raise ValueError('Retained candidate inventory differs')
        for field in ('source','generated'):
            old=Path(record[field])
            if not old.is_relative_to(oldroot):raise ValueError('Source-stage path escapes the accepted run')
            current=retained/safe_relative(str(old.relative_to(oldroot)))
            observed=tree_hashes(current)
            if observed!=record[field+'_sha256']:raise ValueError('Retained source/selector tree changed: '+season)
            snapshots.update({current/n:h for n,h in observed.items()})
    legacy.verify_required_inputs(root,required)
    if identities(root/chronology.BASE)['decoded_sha256']!=BASE_SHA:
        raise ValueError('Retained original reviewed analysis base differs')
    # Compare the inherited identity decisions to their original pinned archive members.
    plan=build_plan(archives)
    for name in AUX:
        matches=[(a,m) for d,a,m in plan if d==name]
        if len(matches)!=1:raise ValueError('Missing original identity input: '+name)
        a,m=matches[0]
        with zipfile.ZipFile(archives/a) as z:
            h=hashlib.file_digest(z.open(m),'sha256').hexdigest()
        if sha(root/name)!=h:raise ValueError('Inherited crosswalk/alias source differs')
    if sha(archives/STAR_ARCHIVE)!=STAR_SHA:raise ValueError('Original star archive differs')
    return {'root':root,'required':required,'source_snapshot':snapshots,
            'source_manifest_sha256':sha(src_manifest),'original_archives':archive_hashes,
            'metadata_only_exception':controlled_exception(),'recorded_original_root':str(oldroot)}


def audit_prefix(wanted,trace):
    return ("import sys as _asys, os as _aos, json as _ajson, atexit as _aexit\n"
            f"_awanted={wanted!r}\n_aseen=set()\n"
            "def _aopen(event,args):\n"
            "    if event=='open' and isinstance(args[0],(str,bytes)):\n"
            "        path=_aos.path.realpath(_aos.fsdecode(args[0]))\n"
            "        if path in _awanted:\n"
            "            mode=args[1]\n"
            "            if mode is not None and any(c in mode for c in 'wax+'): raise RuntimeError('Attempted source write')\n"
            "            if mode is None and args[2] & _aos.O_ACCMODE != _aos.O_RDONLY: raise RuntimeError('Attempted source write')\n"
            "            _aseen.add(_awanted[path])\n"
            "_asys.addaudithook(_aopen)\n"
            f"def _asave():\n    with open({str(trace)!r},'w') as f:_ajson.dump(sorted(_aseen),f)\n"
            "_aexit.register(_asave)\n")


def execute(source:bytes,input_root:Path,output:Path,required:dict,source_name='builder.py',panel_mode=True,allow_legacy_crash=False,environment=None):
    """Execute actual staged code, observe reads, reject source drift and stale output."""
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True)
    legacy.verify_required_inputs(input_root,required)
    trace=output/'opened_inputs.json'
    text=source.decode()
    if panel_mode:
        root="ROOT=Path('/mnt/data/nba_continue')"
        out="OUT=ROOT/'cadence_harmonized_results'; OUT.mkdir(exist_ok=True)"
        if text.count(root)!=1 or text.count(out)!=1:raise ValueError('Original path markers changed')
        text=text.replace(root,f'ROOT=Path({str(input_root)!r})').replace(out,f'OUT=Path({str(output)!r}); OUT.mkdir(exist_ok=True)')
    wanted={str((input_root/n).resolve()):n for n in required}
    prefix=f'import sys\nsys.path.insert(0,{str(REPO)!r})\n'+audit_prefix(wanted,trace)
    runner=output/source_name;runner.write_text(prefix+text)
    started=time.time()-1
    run=subprocess.run([sys.executable,str(runner)],cwd=input_root,env=environment or ENV,capture_output=True,text=True)
    (output/'stdout.log').write_text(run.stdout);(output/'stderr.log').write_text(run.stderr)
    legacy.verify_required_inputs(input_root,required)
    opened=json.loads(trace.read_text()) if trace.is_file() else []
    # Alias fallback is branch-dependent; required always includes all 18 generated files.
    mandatory=set(required)-{'cadence_work/player_alias_table.csv'}
    if not mandatory<=set(opened):raise ValueError('Builder did not read every mandatory generated input')
    if panel_mode:
        outcome=legacy.accept_historical_exit(run.returncode,run.stderr,output,started) if allow_legacy_crash else ('completed' if run.returncode==0 else None)
        if outcome is None or any(not (output/n).is_file() for n in legacy.PRE_MODEL_OUTPUTS):
            raise RuntimeError('Actual builder did not complete all original panel outputs')
    elif run.returncode:
        raise RuntimeError('Staged original executable failed; inspect private stderr.log')
    else:outcome='completed'
    result={'executed_sha256':sha(runner),'canonical_source_sha256':hashlib.sha256(source).hexdigest(),
            'exit_code':run.returncode,'outcome':outcome,'actual_opened_inputs':opened,
            'required_input_sha256':required,'pre_and_post_hashes_equal':True}
    save(output/'execution_receipt.json',result)
    return result


def sample_identities(panel):
    cols=['player_team_game_id','nba_player_id','game_id','team','season',
          'at_risk_for_new_onset_harm','absence_onset_harm','star_PPP_it','postPPP',
          'announced_tv_primary','tv_harmonized_linear','is_home','back_to_back',
          'three_games_in_four_days','four_games_in_six_days','travel_km_since_previous_game',
          'absolute_timezone_shift_hours','road_trip_game_number','signed_elo_advantage',
          'opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days',
          'travel_disadvantage_km','cup_game','minutes_sum_prior_10_roster_games_harm',
          'games_played_before_game_harm','dist_to_65_before_game_harm']
    d=pd.read_csv(panel,usecols=cols);d=d.loc[d.at_risk_for_new_onset_harm].copy()
    controls=cols[11:]
    finite=np.isfinite(d[controls].astype(float)).all(axis=1)
    def digest(frame):return {'n':len(frame),'key_sha256':hashlib.sha256(('\n'.join(sorted(frame.player_team_game_id))+'\n').encode()).hexdigest()}
    return {'full':digest(d.loc[finite]),'none':digest(d)}


def run_models(panel,output):
    # Same original definitions, fixed effects, controls, covariance and cutoffs.
    source=REPO/'scripts/executed/06_cadence_harmonized_identification/run_cadence_models_fast.py'
    if sha(source)!=chronology.FAST_SOURCE_SHA:raise ValueError('Original fast model source differs')
    output.mkdir();input_root=output/'inputs';inner=input_root/'cadence_harmonized_results';inner.mkdir(parents=True)
    target=inner/PANEL;shutil.copy2(panel,target)
    before=sha(panel);data=source.read_text();old=chronology.FAST_ROOT_LINE
    if data.count(old)!=1:raise ValueError('Original model root marker changed')
    data=data.replace(old,f"ROOT=Path({str(input_root)!r}); OUT=ROOT/'cadence_harmonized_results'")
    receipt=execute(data.encode(),input_root,output/'execution',{'cadence_harmonized_results/'+PANEL:sha(target)},
                    source_name='original_fast_models.py',panel_mode=False)
    if sha(panel)!=before:raise ValueError('Generated panel changed during model execution')
    result=inner/'cadence_harmonized_model_results.csv'
    d=pd.read_csv(result);keys=['definition','controls'];expected={(x,c) for x in ('legacy_primary','harmonized_linear') for c in ('full','none')}
    if d.duplicated(keys).any() or set(zip(d.definition,d.controls))!=expected:raise ValueError('Missing or extra model specifications')
    samples=sample_identities(panel)
    for r in d.itertuples():
        vals=[r.estimate_pp,r.se_pp,r.low_pp,r.high_pp,r.p,r.iterations]
        if not np.isfinite(vals).all() or r.se_pp<=0 or r.iterations>=160 or int(r.n)!=samples[r.controls]['n']:
            raise ValueError('Invalid model/sample/convergence result')
        if abs(r.low_pp-(r.estimate_pp-1.96*r.se_pp))>1e-8 or abs(r.high_pp-(r.estimate_pp+1.96*r.se_pp))>1e-8:
            raise ValueError('Model confidence interval inconsistent')
        if abs(r.p-2*norm.sf(abs(r.estimate_pp/r.se_pp)))>1e-10:raise ValueError('Model p-value inconsistent')
    scientific=output/'model_results_scientific.csv';d.drop(columns=['seconds']).sort_values(keys).to_csv(scientific,index=False)
    return {'models':d.to_dict('records'),'samples':samples,'complete_result_csv':identities(result),
            'scientific_result_csv':identities(scientific),'execution':receipt,
            'specification':'Original player + team-season FE LPM; two-way player/game clustering; normal reference; no SCI-003 or covariance modification'}


def copy_inputs(auth,dest,calendar_bytes):
    dest.mkdir(parents=True)
    names=list(auth['required'])+[chronology.BASE]+AUX
    for name in names:
        target=dest/safe_relative(name);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(auth['root']/name,target)
    c=dest/CALENDAR;c.parent.mkdir();c.write_bytes(calendar_bytes)
    return {n:sha(dest/n) for n in names}|{CALENDAR:sha(c)}


def require_semantics(panel,calendar,star_corrected):
    report=semantic_check(pd.read_csv(panel),pd.read_csv(calendar))
    if star_corrected and report['status']!='pass':raise ValueError('New scientific panel fails every-row star semantics')
    return report


def verify_panel_identity(stats,phase,version):
    if stats['rows']!=248778 or stats['games']!=7230 or len(stats['seasons'])!=6:
        raise ValueError('Unexpected generated scientific panel identities')
    ref=FROZEN_SHA if phase=='frozen' else CORRECTED_SHA
    if version=='legacy' and stats['decoded_sha256']!=ref:raise ValueError('Legacy hash verification FAILED')
    if rules.VERSIONS[version][0] and stats['decoded_sha256'] in (FROZEN_SHA,CORRECTED_SHA):
        raise ValueError('Legacy panel cannot be accepted as corrected scientific version')


def verify_legacy_models(models,phase):
    reference=json.loads((PUBLIC.parent/'verification.json').read_text())['stage6_models']
    observed={(r['definition'],r['controls']):r for r in models}
    if len(observed)!=4:raise ValueError('Legacy four-model control incomplete')
    for ref in reference:
        r=observed[ref['definition'],ref['controls']]
        side='frozen' if phase=='frozen' else 'corrected'
        for field in ('estimate_pp','p','n'):
            if abs(r[field]-ref[field+'_'+side])>1e-9:
                raise ValueError('Legacy model numerical control failed: '+field)
        if side=='corrected' and abs(r['se_pp']-ref['se_pp_corrected'])>1e-9:
            raise ValueError('Legacy model numerical control failed: SE')


def model_deltas(old,new):
    result=[]
    for r in new['models']:
        p=next(x for x in old['models'] if (x['definition'],x['controls'])==(r['definition'],r['controls']))
        result.append({'definition':r['definition'],'controls':r['controls'],
                       'legacy':p,'versioned':r,
                       'differences':{k:r[k]-p[k] for k in ('estimate_pp','se_pp','low_pp','high_pp','p','n')},
                       'same_complete_case_keys':old['samples'][r['controls']]==new['samples'][r['controls']]})
    return result


def build(retained,evidence,archives,output,*,workload_sensitivities=False,retained_intermediates=False):
    if retained_intermediates:
        from scripts.data_rebuild.retained_scientific_inputs import preflight as older_preflight
        auth=older_preflight(retained,evidence,archives,output)
    else:auth=preflight(retained,evidence,archives,output)
    environment=runtime();code=code_identity()
    output.mkdir(parents=True,exist_ok=False)
    events=output/'stages.jsonl'
    def event(value):
        with events.open('a') as f:f.write(json.dumps(value)+'\n')
    original=SOURCE.read_bytes()
    if hashlib.sha256(original).hexdigest()!=rules.ORIGINAL_SHA256:raise ValueError('Original scientific source differs')
    with zipfile.ZipFile(archives/STAR_ARCHIVE) as z:
        names=[n for n in z.namelist() if Path(n).name=='player_season_star_status_calendar.csv']
        if len(names)!=1:raise ValueError('Ambiguous original star calendar')
        calendar=z.read(names[0])
    frozen=output/'inputs_frozen';input_hashes=copy_inputs(auth,frozen,calendar)
    corrected=output/'inputs_chronology';shutil.copytree(frozen,corrected)
    before,after,changed=chronology.correct_team_games(archives/'nba_game_covariates_v1.zip')
    base_changes=chronology.fix_base(corrected/chronology.BASE,before,after,changed)
    chronology.fix_selectors(corrected)
    adjusted=chronology.chronology_generated_hashes(corrected,auth['required'])
    corrected_hashes={n:sha(corrected/n) for n in input_hashes}
    allowed_inputs={chronology.BASE,*(chronology.SEL+'/'+n for n in ('2021-22_game_snapshot_join_harmonized_canonical.csv','2021-22_team_game_status_harmonized_canonical.csv'))}
    if {n for n in input_hashes if input_hashes[n]!=corrected_hashes[n]}!=allowed_inputs:
        raise ValueError('Chronology changed an unauthorized input or failed to change its declared inputs')
    versions=['legacy',PRIMARY]
    if workload_sensitivities:versions+=list(rules.VERSIONS)[2:]
    cases={}; comparisons={}
    try:
        for phase,root,hashes in [('frozen',frozen,input_hashes),('chronology',corrected,corrected_hashes)]:
            for version in versions:
                name=phase+'__'+version;case=output/name;star,work=rules.VERSIONS[version]
                event({'stage':name,'event':'start','scientific_version':version})
                source=rules.render_source(original,version)
                required={n:h for n,h in hashes.items() if n!=CALENDAR or star}
                receipt=execute(source,root,case,required,allow_legacy_crash=(version=='legacy'))
                (case/'scientific_patch.diff').write_text(''.join(difflib.unified_diff(original.decode().splitlines(True),source.decode().splitlines(True),fromfile='immutable_original',tofile=version)))
                panel=case/PANEL;stats=summary(panel)
                verify_panel_identity(stats,phase,version)
                sem=require_semantics(panel,root/CALENDAR,star)
                models=run_models(panel,case/'models')
                if version=='legacy':verify_legacy_models(models['models'],phase)
                result={'scientific_version':version,'phase':phase,'panel':stats,'builder':receipt,'semantic_star_check':sem,'four_models':models,
                        'workload_rule':'prior_10_distinct_observed_physical_games_SENSITIVITY_NOT_ADOPTED' if work else 'original_roster_row_history'}
                if version!='legacy':
                    allowed=({'star_PPP_it'} if star else set())|(set(rules.WORKLOAD_COLUMNS) if work else set())
                    auxiliary={}
                    for auxiliary_name in legacy.PRE_MODEL_OUTPUTS:
                        if auxiliary_name!=PANEL:
                            old_aux=output/(phase+'__legacy')/auxiliary_name
                            new_aux=case/auxiliary_name
                            if identities(old_aux)['decoded_sha256']!=identities(new_aux)['decoded_sha256']:
                                raise ValueError('Scientific patch unexpectedly changed report/identity auxiliary: '+auxiliary_name)
                            auxiliary[auxiliary_name]=identities(new_aux)['decoded_sha256']
                    result['unchanged_auxiliary_output_sha256']=auxiliary
                    ctrl=output/(phase+'__legacy')/PANEL
                    result['vs_legacy']=compare(ctrl,panel,allowed,case/'private_keyed_changes.jsonl')
                    result['four_model_vs_legacy']=model_deltas(cases[phase+'__legacy']['four_models'],models)
                    if star and not work and models['samples']!=cases[phase+'__legacy']['four_models']['samples']:
                        raise ValueError('Star-only correction unexpectedly changed model samples')
                    if not star and work:
                        old=cases[phase+'__legacy']['four_models']['models']
                        for r in models['models']:
                            if r['controls']=='none':
                                prev=next(x for x in old if x['definition']==r['definition'] and x['controls']=='none')
                                if any(abs(r[k]-prev[k])>1e-10 for k in ['estimate_pp','se_pp','low_pp','high_pp','p','n']):
                                    raise ValueError('Workload-only variant changed a no-controls model')
                cases[name]=result;save(case/'case_manifest.json',result)
                event({'stage':name,'event':'finish','exit_code':0})
        for version in versions:
            a=output/('frozen__'+version)/PANEL;b=output/('chronology__'+version)/PANEL
            # Date boundary crossings are evaluated by every-row semantics on BOTH versions.
            comparisons[version]=compare(a,b,None,output/('private_chronology_changes__'+version+'.jsonl'))
        # Original chronology gates stay unchanged and use their matching legacy controls.
        legacy_chron=chronology.compare_panels(output/'frozen__legacy'/PANEL,output/'chronology__legacy'/PANEL,output/'chronology__legacy')
        if any(sha(p)!=h for p,h in auth['source_snapshot'].items()):raise ValueError('Retained source changed during scientific reconstruction')
        if code_identity()!=code:raise ValueError('Scientific code changed during execution')
        manifest={'status':'primary_verified_secondary_pending','scientific_version':PRIMARY,'parent_legacy_version':'October corrected chronology',
                  'code':code,'environment':environment,'original_builder_sha256':rules.ORIGINAL_SHA256,'original_model_sha256':chronology.FAST_SOURCE_SHA,
                  'source_manifest_sha256':auth['source_manifest_sha256'],'original_archives_sha256':auth['original_archives'],
                  'input_files_unchanged':True,'all_cases':cases,'within_version_chronology_comparisons':comparisons,
                  'legacy_chronology_check':legacy_chron,'chronology_base_changes':base_changes,'adjusted_generated_hashes':adjusted,
                  'historical_artifact_verdict':auth.get('historical_artifact_verdict','not_exact_2025_metadata_only_exception_preserved'),'metadata_only_exception':auth['metadata_only_exception'],
                  'source_profile':{k:auth[k] for k in ('source_scope','source_profile_sha256','bundle_sha256','verified_original_archives_in_this_execution','November15_input_comparison','selected_2025_PDF_hash_audit') if k in auth},
                  'workload_definition_adopted':False,'secondary_results_status':'not_yet_verified','human_approval':'pending',
                  'limitations':['Original JSON+PDF combination not established','Versioned reviewed/clock inputs inherited','SCI-002 physical-game rule is a sensitivity, not an inferred historical intention']}
        save(output/'scientific_version_manifest.json',manifest)
        return manifest
    except BaseException:
        event({'event':'incomplete','accepted_manifest_written':False})
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['retained-run','retained-evidence','archive-dir','output-root']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--check-only',action='store_true')
    p.add_argument('--include-workload-sensitivities',action='store_true')
    p.add_argument('--retained-intermediates',action='store_true',help='Explicit owner-uploaded November14 intermediate profile; --retained-evidence is its ZIP. Not the six-season raw-source mode.')
    a=p.parse_args()
    for name in ('retained_run','retained_evidence','archive_dir','output_root'):
        setattr(a,name,getattr(a,name).absolute())
    try:
        if a.check_only:
            if a.retained_intermediates:
                from scripts.data_rebuild.retained_scientific_inputs import preflight as older_preflight
                older_preflight(a.retained_run,a.retained_evidence,a.archive_dir,a.output_root)
            else:preflight(a.retained_run,a.retained_evidence,a.archive_dir,a.output_root)
            print(json.dumps({'status':'preflight_pass','no_builder_executed':True,'output_root_untouched':True}));return
        m=build(a.retained_run,a.retained_evidence,a.archive_dir,a.output_root,workload_sensitivities=a.include_workload_sensitivities,retained_intermediates=a.retained_intermediates)
        print(json.dumps({'status':m['status'],'manifest':str(a.output_root/'scientific_version_manifest.json')}))
    except (ValueError,FileNotFoundError,RuntimeError) as e:
        print(json.dumps({'status':'blocked','reason':str(e),'scientific_acceptance':False}),file=sys.stderr)
        raise SystemExit(2)


if __name__=='__main__':main()
