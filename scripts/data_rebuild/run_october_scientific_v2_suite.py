#!/usr/bin/env python3
"""Explicit, separate ten-script replay on authenticated scientific-version outputs.

Never redirects or weakens the original frozen-release acceptance command.
Comparison completion is not scientific or manuscript approval.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import os
from pathlib import Path
import shutil
import sys

REPO=Path(__file__).resolve().parents[2]
if __package__ in (None,''):sys.path.insert(0,str(REPO))
from scripts.data_rebuild import reproduce_october_scientific_v2 as primary
from scripts.data_rebuild import october_corrected_chronology as original
from scripts.data_rebuild.run_full_october_suite_from_generated_panel import verify_october_runtime

AUGUST='data_final/player_game_panel_analysis_ready.csv.gz'


def authenticate(run_root):
    """Rehash actual builder outputs/receipts; a CSV alone is not acceptance."""
    path=run_root/'scientific_version_manifest.json'
    primary.no_symlink(path)
    m=json.loads(path.read_text())
    if (m.get('status')!='primary_verified_secondary_pending'
            or m.get('scientific_version')!=primary.PRIMARY
            or m.get('input_files_unchanged') is not True
            or m.get('code')!=primary.code_identity()):
        raise ValueError('Missing, changed, or incompatible primary execution acceptance')
    cases=m['all_cases']
    for name,c in cases.items():
        if (c['phase'] not in ('frozen','chronology') or name!=c['phase']+'__'+c['scientific_version']
                or c['scientific_version'] not in primary.rules.VERSIONS):
            raise ValueError('Incorrect scientific case identity')
        folder=run_root/primary.safe_relative(name)
        receipt=json.loads((folder/'execution_receipt.json').read_text())
        expected_source=primary.rules.render_source(primary.SOURCE.read_bytes(),c['scientific_version'])
        import hashlib
        if (receipt!=c['builder'] or receipt['pre_and_post_hashes_equal'] is not True
                or receipt['canonical_source_sha256']!=hashlib.sha256(expected_source).hexdigest()
                or receipt['executed_sha256']!=primary.sha(folder/'builder.py')):
            raise ValueError('Builder execution receipt/source changed')
        root=run_root/('inputs_frozen' if c['phase']=='frozen' else 'inputs_chronology')
        primary.legacy.verify_required_inputs(root,receipt['required_input_sha256'])
        mandatory=set(primary.expected_inputs())
        if not mandatory<=set(receipt['required_input_sha256']) or not mandatory<=set(receipt['actual_opened_inputs']):
            raise ValueError('Generated-input builder consumption is incomplete')
        if primary.identities(folder/primary.PANEL)['decoded_sha256']!=c['panel']['decoded_sha256']:
            raise ValueError('Generated panel changed after primary execution')
        if c['scientific_version']=='legacy':
            wanted=primary.FROZEN_SHA if c['phase']=='frozen' else primary.CORRECTED_SHA
            if c['panel']['decoded_sha256']!=wanted:raise ValueError('Legacy acceptance differs')
        elif primary.rules.VERSIONS[c['scientific_version']][0]:
            if c['panel']['decoded_sha256'] in (primary.FROZEN_SHA,primary.CORRECTED_SHA):
                raise ValueError('Legacy dataset cannot stand in for scientific v2')
            primary.require_semantics(folder/primary.PANEL,root/primary.CALENDAR,True)
    wanted={'chronology__legacy','chronology__'+primary.PRIMARY}
    if not wanted<=set(cases):raise ValueError('Both primary and legacy chronology controls required')
    return m


def table_keys(fields):
    if 'term' in fields:return [k for k in ('model','term') if k in fields]
    if 'name' in fields:return ['name']
    if 'season' in fields:return ['season','star_PPP_it','tv_harmonized_linear','postPPP']
    if 'tv' in fields:return [k for k in ('tv','outcome') if k in fields]
    raise ValueError('Unrecognized original output identity schema')


def compare_table(left,right,diff_path):
    """All scientific cells, keyed rows; no positional coefficient matching."""
    def read(path):
        with path.open(newline='') as f:
            r=csv.DictReader(f);fields=r.fieldnames;keys=table_keys(fields)
            rows={}
            for row in r:
                key=tuple(row[k] for k in keys)
                if key in rows:raise ValueError('Duplicate downstream output identity')
                rows[key]=row
        return fields,keys,rows
    fields,keys,a=read(left);other,otherkeys,b=read(right)
    if fields!=other or keys!=otherkeys:raise ValueError('Secondary output schema changed')
    only=sorted(set(a)^set(b))
    swaps=[k for k in only if 'term' in keys and k[keys.index('term')] in ('games_before_10','dist65_10')]
    if 'term' in keys and len(swaps)!=len(only):raise ValueError('Unexpected secondary model term addition/removal')
    changed=0;numeric_max=0.;nonconverged=[]
    with diff_path.open('x') as f:
        for key in sorted(set(a)|set(b)):
            x,y=a.get(key),b.get(key);changes={}
            if x is None or y is None:changes={'row_identity':[x,y]}
            else:
                for col in fields:
                    if col=='seconds' or x[col]==y[col]:continue
                    changes[col]=[x[col],y[col]]
                    try:
                        u,v=float(x[col]),float(y[col])
                        if math.isfinite(u) and math.isfinite(v):numeric_max=max(numeric_max,abs(v-u))
                    except ValueError:pass
            if y and 'converged' in y and not primary.rules.strict_bool(y['converged']):
                nonconverged.append(list(key))
            if changes:
                changed+=1;f.write(json.dumps({'key':key,'changes':changes})+'\n')
    return {'key_columns':keys,'legacy_rows':len(a),'versioned_rows':len(b),'changed_rows':changed,
            'added_keys':[list(k) for k in sorted(set(b)-set(a))],'removed_keys':[list(k) for k in sorted(set(a)-set(b))],
            'collinear_label_swaps':[list(k) for k in swaps],
            'maximum_absolute_numeric_change':numeric_max,'nonconverged_versioned_rows':nonconverged,
            'legacy_identity':primary.identities(left),'versioned_identity':primary.identities(right),
            'comparison':'complete literal cells by keys; only runtime seconds excluded; numeric changes descriptive, not equality gates'}


def build(run_root,shared,output,include_sensitivities=False):
    primary.fresh_output(output,[run_root,shared])
    primary.no_symlink(run_root);primary.no_symlink(shared)
    before=primary.sha(run_root/'scientific_version_manifest.json')
    m=authenticate(run_root);code=primary.code_identity()
    original.verify_shared_commit(shared);environment=verify_october_runtime(Path(sys.executable))
    versions=['legacy',primary.PRIMARY]
    if include_sensitivities:versions+=list(primary.rules.VERSIONS)[2:]
    for v in versions:
        if 'chronology__'+v not in m['all_cases']:raise ValueError('Requested sensitivity was not generated by primary runner')
    output.mkdir(parents=True)
    receipts={};files={};comparisons={}
    for version in versions:
        folder=output/version;panel=run_root/('chronology__'+version)/primary.PANEL
        original.prepare(shared,folder,panel)
        required={original.PANEL:primary.sha(folder/original.PANEL)}
        scripts={n:primary.sha(folder/'scripts/october_2026'/f'{n}.py') for n in original.SCRIPTS}
        receipts[version]={}
        env={**primary.ENV,'NBA_AUDIT_PANEL':str((folder/original.PANEL).resolve())}
        for name in original.SCRIPTS:
            actual=folder/'scripts/october_2026'/f'{name}.py'
            if primary.sha(actual)!=primary.sha(shared/'scripts/october_2026'/actual.name):
                raise ValueError('Original October script changed')
            watched=dict(required)
            if name.startswith('run_'):watched[AUGUST]=primary.sha(folder/AUGUST)
            wrapper=f'import runpy\nrunpy.run_path({str(actual)!r},run_name="__main__")\n'.encode()
            receipts[version][name]=primary.execute(wrapper,folder,folder/'execution'/name,watched,
                panel_mode=False,environment=env)
            receipts[version][name]['original_source_sha256']=scripts[name]
        if scripts!={n:primary.sha(folder/'scripts/october_2026'/f'{n}.py') for n in original.SCRIPTS}:
            raise ValueError('Staged original source changed during execution')
        observed=original.outputs(folder)
        if len(observed)!=original.EXPECTED_ARCHIVED_OUTPUTS:raise ValueError('Incomplete original 33-output suite')
        files[version]={n:primary.identities(p) for n,p in observed.items()}
        if version!='legacy':
            refs=original.outputs(output/'legacy')
            if set(refs)!=set(observed):raise ValueError('Original output inventory changed')
            dest=folder/'private_differences';dest.mkdir()
            comparisons[version]={n:compare_table(refs[n],p,dest/(n.replace('/','__')+'.jsonl')) for n,p in sorted(observed.items())}
        if primary.identities(panel)['decoded_sha256']!=m['all_cases']['chronology__'+version]['panel']['decoded_sha256']:
            raise ValueError('Primary scientific panel changed during secondary analysis')
    if (primary.sha(run_root/'scientific_version_manifest.json')!=before or primary.code_identity()!=code):
        raise ValueError('Upstream primary manifest or executable source changed')
    original.verify_shared_commit(shared)
    report={'status':'calculations_compared_human_review_pending','scientific_acceptance':False,
            'primary_manifest_sha256':before,'code':code,'shared_original_commit':original.SHARED_COMMIT,
            'environment':environment,'execution':receipts,'outputs':files,'comparisons':comparisons,
            'historical_artifact_verdict':m['historical_artifact_verdict'],
            'pending':['Review all scientific changes and original convergence flags',
                       'Rebuild and inspect affected figures; approve manuscript values separately',
                       'Independent human scientific review and release decision'],
            'unchanged_inherited_auxiliary':'Original August panel used for original All-Star-only transformations; its grouped fill convention is not changed here'}
    primary.save(output/'scientific_secondary_manifest.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['scientific-run','shared-repo','output-root']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--include-workload-sensitivities',action='store_true');a=p.parse_args()
    try:
        report=build(a.scientific_run.absolute(),a.shared_repo.absolute(),a.output_root.absolute(),a.include_workload_sensitivities)
        print(json.dumps({'status':report['status'],'scientific_acceptance':False}))
    except (ValueError,FileNotFoundError,RuntimeError) as e:
        print(json.dumps({'status':'blocked','scientific_acceptance':False,'reason':str(e)}),file=sys.stderr)
        raise SystemExit(2)


if __name__=='__main__':main()
