#!/usr/bin/env python3
"""Re-execute frozen canonical NBA 2020–21 / 2024–25 report-selector code.

Read-only validation against private original/archive inputs. This replays the
original canonical selection function and compares full game and team status
columns with archived canonical output, plus published season metrics. Optional
fresh 2020 rows are verified output from the preceding original-PDF stage; this
script does not itself reparse PDFs, rebuild identities, or rerun regressions.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

BUILDER_SHA256 = '3e2c3f975a9d6f0828655cfade2a11a8418c0a3b3af3789a307949780666031f'
BUILDER_MEMBER = 'nba_canonical_snapshot_selector_v1/build_canonical_snapshot_selector_v1.py'
CANONICAL_PREFIX = 'nba_canonical_snapshot_selector_v1/'
ALLOWED_SEASONS = ('2020-21','2024-25')
FULL_2020_SOURCE = 's1_snapshot_rows_2020_21_from_original_PDFs.csv'
PDF_PARSER_2020_SHA256 = '77fb85d6e0634c01d0ddb0739294c0ed044671b5b93b0affbbf9ec943a7ef6ee'
PDF_ARCHIVE_2020_SHA256 = 'e310c8149701fb16cda9b1a136fbfcf9af8af8de9ca2ed09080f364a493c272c'
SEASON_INPUTS = {
    '2020-21': {
        'manifest': ('audit_2020_21_upload.zip', 'audit_2020_21/report_manifest.csv'),
        'parsed_rows': ('audit_2020_21_corrected_outputs.zip', 's1_snapshot_rows_corrected.csv'),
        'schedule': ('audit_2020_21_s4_join_results_rechecked.zip','s4_games_2020_21_normalized.csv'),
        'expected_games': 1080,
    },
    '2024-25': {
        'manifest': ('audit_2024_25_pre_s4_outputs_corrected.zip','report_manifest_regular_season.csv'),
        'parsed_rows': ('audit_2024_25_pre_s4_outputs_corrected.zip','s1_snapshot_rows_regular_season.csv'),
        'schedule': ('audit_2024_25_s4_join_results.zip','s4_games_2024_25_normalized.csv'),
        'expected_games': 1230,
    },
}
GAME_SCIENTIFIC_FIELDS = frozenset({
    'published_timestamp_utc','snapshot_basename','minutes_before_tip',
    'usable_team_games','not_submitted_team_games','both_teams_usable',
    'inferred_clean_teams','listed_teams','qc_selected_within_30m',
    'matchup_norm','tip_timestamp_utc',
})
TEAM_SCIENTIFIC_FIELDS = frozenset({
    'selected_snapshot_utc','snapshot_basename','minutes_before_tip',
    'team_final_status','usable_submitted_status','inferred_no_listed_players',
    'n_player_rows','n_out','n_available',
})


def file_sha256(path:Path)->str:
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):
            digest.update(data)
    return digest.hexdigest()


def member_bytes(path:Path,member:str)->bytes:
    if not path.is_file():
        raise FileNotFoundError(path)
    with ZipFile(path) as archive:
        if archive.namelist().count(member)!=1:
            raise ValueError(f'Expected exactly one ZIP member: {path.name}::{member}')
        return archive.read(member)


def original_builder(canonical_zip: Path):
    content=member_bytes(canonical_zip,BUILDER_MEMBER)
    actual=hashlib.sha256(content).hexdigest()
    if actual!=BUILDER_SHA256:
        raise ValueError(f'Historical selector Python source differs from pinned immutable original: {actual}')
    # Only execute the pinned original function declarations; do not run its
    # historical top-level file-loading statements with hard-coded paths.
    decoded=content.decode('utf-8')
    boundary='# load inputs 2020, 2024'
    if decoded.count(boundary)!=1:
        raise ValueError('Original builder no longer has the trusted source boundary')
    prefix=decoded.split(boundary,1)[0]
    # The immutable source initializes a /mnt/data output folder at import
    # time. Only the function declarations are needed; never create a
    # historical environment-specific folder while replaying them.
    output_setup="OUT=Path('/mnt/data/nba_canonical_snapshot_selector_v1')\nOUT.mkdir(exist_ok=True)\n"
    if prefix.count(output_setup)!=1:
        raise ValueError('Original builder top-level output setup changed')
    namespace={}
    exec(compile(prefix.replace(output_setup,'',1),BUILDER_MEMBER,'exec'),namespace)
    return namespace['build_season']


def csv_from_zip(archive_dir:Path,record:tuple[str,str])->pd.DataFrame:
    data=member_bytes(archive_dir/record[0],record[1])
    return pd.read_csv(io.BytesIO(data))


def verified_fresh_2020_rows(archive_dir:Path, source:Path, acceptance:Path)->pd.DataFrame:
    """Require actual original-PDF parser evidence, then compare every source cell."""
    if source.is_symlink() or acceptance.is_symlink() or not source.is_file() or not acceptance.is_file():
        raise FileNotFoundError('Fresh 2020 PDF rows and acceptance report must be real private files')
    if source.name!=FULL_2020_SOURCE or source.parent!=acceptance.parent:
        raise ValueError('Fresh 2020 PDF rows and acceptance report must be siblings at the expected path')
    report=json.loads(acceptance.read_text())
    if (report.get('status')!='pass' or report.get('source_pdf_count')!=617
            or report.get('fresh_original_617_PDF_execution_in_this_invocation') is not True
            or report.get('source_reason_text_replaced_with_archived_value') is not False
            or report.get('original_2020_source_parser_sha256')!=PDF_PARSER_2020_SHA256
            or report.get('original_2020_raw_zip_sha256')!=PDF_ARCHIVE_2020_SHA256
            or file_sha256(archive_dir/'audit_2020_21_upload.zip')!=PDF_ARCHIVE_2020_SHA256
            or report.get('parsed_original_source',{}).get('every_original_column_and_full_record_exact') is not True
            or report.get('parsed_original_source',{}).get('columns')!=15
            or report.get('parsed_original_source',{}).get('rows')!=41780
            or report.get('full_source_rows_filename')!=FULL_2020_SOURCE
            or report.get('full_source_rows_sha256')!=file_sha256(source)):
        raise ValueError('Fresh 2020 raw-PDF parser acceptance is missing, stale, or incomplete')
    archived=csv_from_zip(archive_dir,SEASON_INPUTS['2020-21']['parsed_rows'])
    fresh=pd.read_csv(source,low_memory=False)
    if list(fresh.columns)!=list(archived.columns) or len(fresh)!=41780 or len(archived)!=41780:
        raise ValueError('Fresh 2020 source parsed-row schema/count differs')
    def records(frame):
        normalized=pd.read_csv(io.StringIO(frame.to_csv(index=False)),dtype=str,keep_default_na=False)
        return Counter(normalized.itertuples(index=False,name=None))
    if records(fresh)!=records(archived):
        raise ValueError('Fresh 2020 original-PDF parsed rows differ from historical complete records')
    return fresh


def compare_records(candidate:pd.DataFrame,ref:pd.DataFrame, keys:list[str],required:frozenset[str],
                    expected_rows:int):
    if not set(keys)|required<=set(candidate.columns):
        raise ValueError(f'Candidate missing scientific fields: {sorted((set(keys)|required)-set(candidate.columns))}')
    if not set(keys)|required<=set(ref.columns):
        raise ValueError(f'Original published output missing scientific fields: {sorted((set(keys)|required)-set(ref.columns))}')
    if set(candidate.columns) != set(ref.columns):
        raise ValueError(f'Original canonical output schema differs: missing={sorted(set(ref.columns)-set(candidate.columns))}, extra={sorted(set(candidate.columns)-set(ref.columns))}')
    if len(candidate)!=expected_rows or len(ref)!=expected_rows:
        raise ValueError(f'Unexpected reconstructed/reference rows: {len(candidate)} / {len(ref)}; expected {expected_rows}')
    if candidate.duplicated(keys).any() or ref.duplicated(keys).any():
        raise ValueError(f'Duplicate game/team identity keys: {keys}')
    c=candidate.set_index(keys).sort_index()
    r=ref.set_index(keys).sort_index()
    if not c.index.equals(r.index):
        raise ValueError('Candidate/reference game or team identity sets disagree')
    common=[col for col in ref.columns if col in candidate.columns and col not in keys]
    discrepancies={}
    for col in common:
        x=c[col].astype(str).str.strip()
        y=r[col].astype(str).str.strip()
        if (n:=int(x.ne(y).sum())):
            discrepancies[col]=n
    if discrepancies:
        raise ValueError(f'Original canonical outputs drift: {discrepancies}')
    return {'rows':expected_rows,'compared_columns_including_keys':len(common)+len(keys),
            'all_scientific_fields_matched':True,'differences':0,
            'not_compared_reference_columns':sorted(set(ref.columns)-set(candidate.columns)),
            'additional_source_schedule_columns':sorted(set(candidate.columns)-set(ref.columns))}


def check_metrics(observed:dict,original:pd.Series)->dict:
    columns=['games','games_with_pre_tip_pdf','pre_tip_pdf_pct','team_games',
             'usable_team_games','usable_team_game_pct','games_both_teams_usable',
             'both_teams_usable_pct','not_yet_submitted_team_games',
             'inferred_clean_team_games','median_minutes_before_tip',
             'within_30m_games','within_30m_pct']
    errors={}
    for c in columns:
        if c not in observed or c not in original:
            raise ValueError(f'Missing canonical season metric {c}')
        if not math.isclose(float(observed[c]),float(original[c]),rel_tol=1e-10,abs_tol=1e-9):
            errors[c]={'recomputed':float(observed[c]),'reference':float(original[c])}
    if errors:
        raise ValueError(f'Canonical season metrics drift: {errors}')
    return {'metrics_compared':len(columns),'differences':0}


def verify(archive_dir:Path, seasons:tuple[str,...]=ALLOWED_SEASONS,
           generated_dir:Path|None=None,
           fresh_2020_rows:Path|None=None, fresh_2020_acceptance:Path|None=None)->dict:
    if not seasons or len(seasons)!=len(set(seasons)) or not set(seasons)<=set(ALLOWED_SEASONS):
        raise ValueError('Choose one or both canonical-rebuilt seasons without duplicates')
    if bool(fresh_2020_rows)!=bool(fresh_2020_acceptance) or (fresh_2020_rows and '2020-21' not in seasons):
        raise ValueError('Fresh 2020 source rows/report require one another and the 2020–21 season')
    canonical_zip=archive_dir/'nba_canonical_snapshot_selector_v1.zip'
    builder=original_builder(canonical_zip)
    metrics_ref=pd.read_csv(io.BytesIO(member_bytes(canonical_zip,CANONICAL_PREFIX+'canonical_six_season_metrics.csv')))
    result={
      'scope':'Original canonical selector algorithm replay against pinned historical manifest/schedule and verified parsed rows; per-season source input declared below',
      'builder_original_sha256':BUILDER_SHA256,'private_raw_archives_committed':False,
      'original_frozen_dataset_modified':False,'all_selected_season_cases_passed':False,
      'inputs':{},'cases':[],
    }
    generated={}
    for season in seasons:
        spec=SEASON_INPUTS[season]
        manifest=csv_from_zip(archive_dir,spec['manifest'])
        rows=(verified_fresh_2020_rows(archive_dir,fresh_2020_rows,fresh_2020_acceptance)
              if season=='2020-21' and fresh_2020_rows else csv_from_zip(archive_dir,spec['parsed_rows']))
        sched=csv_from_zip(archive_dir,spec['schedule'])
        result['inputs'][season]={label:{'archive':file[0],'member':file[1],
                             'archive_sha256':file_sha256(archive_dir/file[0])}
                             for label,file in spec.items() if label!='expected_games'}
        result['inputs'][season]['parsed_rows_consumed']=(
            {'kind':'recomputed_intermediate', 'origin':'original_injury_PDFs', 'path':str(fresh_2020_rows),
             'sha256':file_sha256(fresh_2020_rows),'rows':len(rows),
             'historical_report_timestamps_inherited':True}
            if season=='2020-21' and fresh_2020_rows else
            {'kind':'archived_computational_intermediate','archive':spec['parsed_rows'][0]})
        for panel,tokens,panel_name in (
          ('full',None,'full_canonical'),
          ('harmonized',['01PM','05PM','08PM'],'harmonized_0130_1730_2030')):
            result_g,result_t,met=builder(season,io.BytesIO(sched.to_csv(index=False).encode('utf-8')),
                                          manifest,rows,tokens,panel_name)
            if season == '2020-21':
                # Recovered 2020 schedule uses snake_case for these four
                # metadata fields. Frozen canonical output uses title case.
                result_g=result_g.rename(columns={'away_team':'Away Team',
                    'home_team':'Home Team','location':'Location','result':'Result'})
            reference_g=pd.read_csv(io.BytesIO(member_bytes(canonical_zip,
                  CANONICAL_PREFIX+f'{season}_game_snapshot_join_{panel}_canonical.csv')))
            reference_t=pd.read_csv(io.BytesIO(member_bytes(canonical_zip,
                  CANONICAL_PREFIX+f'{season}_team_game_status_{panel}_canonical.csv')))
            expected_metric=metrics_ref.loc[(metrics_ref['season']==season)&(metrics_ref['panel']==panel_name)]
            if len(expected_metric)!=1:
                raise ValueError(f'Expected exactly one frozen metric row for {season}/{panel_name}')
            game=compare_records(result_g,reference_g,['game_id'],GAME_SCIENTIFIC_FIELDS,spec['expected_games'])
            team=compare_records(result_t,reference_t,['game_id','team_role'],TEAM_SCIENTIFIC_FIELDS,2*spec['expected_games'])
            metrics=check_metrics(met,expected_metric.iloc[0])
            result['cases'].append({'season':season,'panel':panel,'game':game,'team':team,'metrics':metrics})
            generated[f'{season}_game_snapshot_join_{panel}_canonical.csv']=result_g
            generated[f'{season}_team_game_status_{panel}_canonical.csv']=result_t
    result['all_selected_season_cases_passed']=True
    result['canonical_original_zip_sha256']=file_sha256(canonical_zip)
    if generated_dir is not None:
        generated_dir=generated_dir.resolve()
        if generated_dir==archive_dir.resolve() or archive_dir.resolve() in generated_dir.parents:
            raise ValueError('Generated selectors must be outside original archive directory')
        generated_dir.mkdir(parents=True,exist_ok=False)
        result['generated_selector_tables']={}
        for filename,frame in generated.items():
            target=generated_dir/filename
            frame.to_csv(target,index=False)
            result['generated_selector_tables'][filename]={
                'rows':len(frame),'sha256':file_sha256(target),
                'generated_from_original_pdfs_directly':bool(fresh_2020_rows and filename.startswith('2020-21_')),
                'input_rows_are_pinned_historical_parser_outputs':not (fresh_2020_rows and filename.startswith('2020-21_')),
            }
        (generated_dir/'selector_replay_manifest.json').write_text(
            json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-dir',type=Path,required=True)
    parser.add_argument('--seasons',nargs='+',choices=ALLOWED_SEASONS,default=list(ALLOWED_SEASONS))
    parser.add_argument('--output',type=Path)
    parser.add_argument('--generated-dir',type=Path,
                        help='Export validated new selector CSVs to a fresh private directory; parsed-row inputs remain historical archives')
    parser.add_argument('--fresh-2020-source-rows',type=Path,
                        help='Verified full 617-PDF parsed rows from the preceding source stage')
    parser.add_argument('--fresh-2020-acceptance',type=Path,
                        help='Unmodified original-PDF source acceptance report matching the parsed-row SHA')
    args=parser.parse_args()
    result=verify(args.archive_dir,tuple(args.seasons),args.generated_dir,
                  args.fresh_2020_source_rows,args.fresh_2020_acceptance)
    rendered=json.dumps(result,indent=2)+'\n'
    if args.output:
        if args.output.exists():
            raise FileExistsError(f'Refusing to overwrite prior replay report: {args.output}')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered)
    print(rendered,end='')


if __name__=='__main__':
    main()
