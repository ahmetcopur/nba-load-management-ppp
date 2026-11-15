"""Explicit earlier-intermediate profile for the localized SCI-001 correction.

This does not substitute archived files into the six-season raw-source mode.
Only the owner's separately authenticated retained bundle is accepted here.
Every scientific output/legacy/model gate in the scientific runner still runs.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import zipfile

PROFILE='validation/october_scientific_v2_2026-11-15/retained_003_source_profile.json'
PROFILE_SHA='4c0556b15a711011ab48c763aa7c865c6ef5bd39409812179f3c28127ad4ed17'


def verify_profile(repo):
    p=repo/PROFILE
    with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!=PROFILE_SHA:raise ValueError('Retained source profile was changed')
    return json.loads(p.read_text())


def preflight(retained,bundle,archives,output):
    from scripts.data_rebuild import reproduce_october_scientific_v2 as runner
    from scripts.data_rebuild.reparse_2025_selected import audit_selected,verify_parse_log
    from scripts.data_rebuild.rebuild_six_season_october_sources import controlled_exception
    from scripts.data_rebuild.private_source_paths import under_git
    runner.fresh_output(output,[retained,bundle,archives])
    profile=verify_profile(runner.REPO);root=retained/'03_historical_cadence_inputs'
    wanted=runner.expected_inputs();pins=profile['input_sha256']
    if set(pins)!=set(wanted)|{runner.chronology.BASE,*runner.AUX}:
        raise ValueError('Retained profile input inventory differs')
    if not bundle.is_file() or runner.sha(bundle)!=profile['bundle_sha256']:
        raise ValueError('Owner-uploaded retained bundle SHA-256 differs')
    if under_git(retained) or under_git(archives):raise ValueError('Retained sources must be outside Git')
    runner.no_symlink(bundle);runner.no_symlink(retained);runner.no_symlink(archives)
    snapshot={bundle:runner.sha(bundle)}
    for name,h in pins.items():
        p=root/runner.safe_relative(name);runner.no_symlink(p)
        if not p.is_file() or runner.sha(p)!=h:raise ValueError('Retained input missing or changed: '+name)
        snapshot[p]=h
    for name,h in profile['receipt_sha256'].items():
        p=retained/runner.safe_relative(name);runner.no_symlink(p)
        if not p.is_file() or runner.sha(p)!=h:raise ValueError('Retained receipt missing or changed: '+name)
        snapshot[p]=h
    m=json.loads((retained/'final/final_dataset_manifest.json').read_text())
    public=json.loads(runner.PUBLIC.read_text())
    if m.get('status')!='pass' or not m.get('original_archives_and_frozen_panels_unmodified'):
        raise ValueError('Earlier retained run was not accepted')
    for name,r in public['outputs'].items():
        if m.get('outputs',{}).get(name,{}).get('decoded_sha256')!=r['decoded_sha256']:
            raise ValueError('Earlier retained final identity differs')
    original_archives=m['input_archives_sha256']
    if not original_archives or any(public['input_archives_sha256'].get(n)!=h for n,h in original_archives.items()):
        raise ValueError('Earlier archive provenance differs from pinned originals')
    events=[json.loads(x) for x in (retained/'logs/stages.jsonl').read_text().splitlines()]
    stages=[e['stage'] for e in events if e.get('event')=='start']
    if (len(stages)!=9 or len(set(stages))!=9
            or [(e.get('stage'),e.get('event')) for e in events]!=[(n,s) for n in stages for s in ('start','finish')]
            or any(e.get('exit_code')!=0 for e in events if e.get('event')=='finish')):
        raise ValueError('Earlier retained stage execution incomplete')
    matched=sum(pins[n]==h for n,h in wanted.items())
    differences={n:{'retained_sha256':pins[n],'November15_sha256':h} for n,h in wanted.items() if pins[n]!=h}
    if matched!=15 or differences!=profile['differs_from_November15']:
        raise ValueError('Retained source-profile differences are unexplained')
    # Independently open actual original archives; a self-reported pass is insufficient.
    references={
        'audit_2020_21_corrected_outputs.zip': [('s1_snapshot_rows_corrected.csv','cadence_work/season_parsed/2020-21/s1_snapshot_rows_corrected.csv')],
        'nba_canonical_snapshot_selector_v1.zip': [('nba_canonical_snapshot_selector_v1/2025-26_team_game_status_harmonized_canonical.csv','cadence_work/selector/nba_canonical_snapshot_selector_v1/2025-26_team_game_status_harmonized_canonical.csv')],
        'nba_player_crosswalk_final_v1.zip': [('nba_player_crosswalk_final_v1/player_crosswalk_final.csv',runner.AUX[0]),('nba_player_crosswalk_final_v1/player_alias_table.csv',runner.AUX[1])],
        'nba_game_covariates_v1.zip': [],runner.STAR_ARCHIVE: [],
    }
    verified={}
    for name,members in references.items():
        path=archives/name;runner.no_symlink(path)
        if not path.is_file() or runner.sha(path)!=public['input_archives_sha256'][name]:
            raise ValueError('Pinned original source archive missing/changed: '+name)
        snapshot[path]=runner.sha(path);verified[name]=snapshot[path]
        with zipfile.ZipFile(path) as z:
            for member,target in members:
                with z.open(member) as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
                if digest!=pins[target]:raise ValueError('Original archive member does not match retained input: '+target)
    # Original selected-PDF bytes are present in this bundle. Audit them against
    # the two complete original archive hashes and the historical parse receipt.
    for name in ('audit_2025_26_upload.zip','audit_2025_26_targeted_upload.zip'):
        p=root/'cadence_2025'/name
        if runner.sha(p)!=public['input_archives_sha256'][name]:raise ValueError('Original 2025 archive differs')
        snapshot[p]=runner.sha(p);verified[name]=snapshot[p]
    audit=audit_selected(root);recorded=json.loads((root/'cadence_work/season_parsed/2025-26/selected_pdf_sha256_audit.json').read_text())
    if audit['sha256_by_basename']!=recorded['sha256_by_basename'] or audit['distinct_selected_pdfs']!=355:
        raise ValueError('Selected original PDF identity changed')
    for name,h in audit['sha256_by_basename'].items():
        p=root/'cadence_work/season_parsed/2025-26/pdf'/name;runner.no_symlink(p)
        if runner.sha(p)!=h:raise ValueError('Retained selected PDF differs from original archive')
        snapshot[p]=h
    parse=verify_parse_log(root)
    if runner.identities(root/runner.chronology.BASE)['decoded_sha256']!=runner.BASE_SHA:
        raise ValueError('Retained reviewed analysis base differs')
    return {'root':root,'required':{n:pins[n] for n in wanted},'source_snapshot':snapshot,
            'source_manifest_sha256':runner.sha(retained/'final/final_dataset_manifest.json'),
            'original_archives':original_archives,'metadata_only_exception':controlled_exception(),
            'historical_artifact_verdict':'retained_legacy_intermediates_inherited_not_six_season_raw_reexecution',
            'source_scope':profile['scope'],'source_profile_sha256':PROFILE_SHA,
            'bundle_sha256':profile['bundle_sha256'],'verified_original_archives_in_this_execution':verified,
            'November15_input_comparison':{'identical':matched,'different':differences},
            'selected_2025_PDF_hash_audit':{'pdfs':355,'all_archived_PDF_digests_equal':True,
                                         'parse_receipt':parse,'fresh_candidate_parse_executed':False}}
