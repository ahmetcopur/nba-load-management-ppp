#!/usr/bin/env python3
"""Independently select 2025–26 latest pre-tip NBA injury PDF from two original manifests.

Checks the originally saved report inventory, not reports never collected, and
does not reparse PDF bodies, reconstruct identity joins or refit models.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

EXPECTED_ZIPS = {
    'audit_2025_26_upload.zip':
        'a0cdcb4b9e594a1b1fb63489aa43087f6c13f5b34ab3661b596c2941089c9f70',
    'audit_2025_26_targeted_upload.zip':
        '8a9c08e3aa92f5400cc866201051653e13b89cc6a56b5aae7deb2ad9e0f718ea',
}
CADENCE_SUFFIX = tuple('_'+s+'.pdf' for s in
    ('01PM','05PM','08PM','01_30PM','05_30PM','08_30PM'))
EXPECTED_COUNT = {'initial':1497,'targeted':3526,'full':5023,'harmonized':507,'games':1230}


def sha256_file(path:Path)->str:
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_member(path:Path,member:str)->pd.DataFrame:
    with ZipFile(path) as z:
        if z.namelist().count(member)!=1:
            raise ValueError(f'Archive member not unique/present: {path.name}::{member}')
        return pd.read_csv(io.BytesIO(z.read(member)))


def manifest_part(df:pd.DataFrame, ts_col:str, label:str)->pd.DataFrame:
    for column in ['exists','local_path',ts_col]:
        if column not in df:
            raise ValueError(f'{label}: missing {column}')
    present=df.loc[df['exists'].astype(str).str.casefold().isin(['true','1'])].copy()
    timestamps=pd.to_datetime(present[ts_col],utc=True,errors='raise')
    if timestamps.isna().any():
        raise ValueError(f'{label}: missing present PDF timestamp')
    paths=present.local_path
    if paths.isna().any():
        raise ValueError(f'{label}: missing present PDF local_path')
    names=paths.astype(str).str.rsplit('/',n=1).str[-1]
    if not names.str.endswith('.pdf').all():
        raise ValueError(f'{label}: non-PDF marked present')
    return pd.DataFrame({'published':timestamps,'basename':names,'source':label})


def select_from_inventory(source:pd.DataFrame,schedule:pd.DataFrame)->pd.DataFrame:
    if source.published.duplicated().any() or source.basename.duplicated().any():
        raise ValueError('Duplicate source PDF basename or publication timestamp across archives')
    if schedule.game_id.duplicated().any() or schedule.game_id.isna().any():
        raise ValueError('Schedule has duplicate or missing game IDs')
    original=schedule[['game_id','tip_timestamp_utc']].copy()
    original['tip']=pd.to_datetime(original.tip_timestamp_utc,utc=True,errors='raise')
    if original.tip.isna().any():
        raise ValueError('Schedule missing tip timestamp')
    selected=pd.merge_asof(original.sort_values('tip'),source.sort_values('published'),
              left_on='tip',right_on='published',direction='backward',
              allow_exact_matches=False)
    if selected.published.isna().any():
        raise ValueError('Game with no saved source PDF strictly before tip')
    selected['age_minutes']=(selected.tip-selected.published).dt.total_seconds()/60
    if (selected.age_minutes<=0).any():
        raise ValueError('Selected source report at/after tip')
    return selected


def compare_selection(candidate:pd.DataFrame,reference:pd.DataFrame,panel:str)->dict:
    required={'game_id','snapshot_basename','published_timestamp_utc','minutes_before_tip'}
    if not required<=set(reference.columns):
        raise ValueError('Original canonical selector lacks required fields')
    if len(candidate)!=EXPECTED_COUNT['games'] or len(reference)!=EXPECTED_COUNT['games']:
        raise ValueError(f'{panel}: wrong game count candidate/reference')
    if reference.game_id.isna().any() or reference.game_id.duplicated().any():
        raise ValueError(f'{panel}: frozen reference duplicate or missing game ID')
    merged=candidate.merge(
        reference[['game_id','snapshot_basename','published_timestamp_utc','minutes_before_tip']],
        on='game_id',how='outer',validate='one_to_one',indicator=True)
    if not merged['_merge'].eq('both').all():
        raise ValueError(f'{panel}: game identities differ')
    expected_time=pd.to_datetime(merged.published_timestamp_utc,utc=True,errors='raise')
    problems={
        'wrong_pdf_basename':int(merged.basename.ne(merged.snapshot_basename).sum()),
        'wrong_publication_time':int(merged.published.ne(expected_time).sum()),
        'wrong_minutes_before_tip':int(((merged.age_minutes-
                      pd.to_numeric(merged.minutes_before_tip,errors='raise')).abs()>1e-6).sum()),
    }
    if any(problems.values()):
        raise ValueError(f'{panel}: independent original manifest selection differs: {problems}')
    return {'panel':panel,'games':len(merged),'exact_pdf_matches':len(merged),
            'exact_publication_time_matches':len(merged),
            'pre_tip_time_discrepancies':0,'problems':problems,
            'initial_source_selections':int(merged.source.eq('initial').sum()),
            'targeted_source_selections':int(merged.source.eq('targeted').sum())}


def verify(archive_dir:Path)->dict:
    found_hashes={}
    for basename,expected in EXPECTED_ZIPS.items():
        path=archive_dir/basename
        if not path.is_file():
            raise FileNotFoundError(path)
        observed=sha256_file(path)
        if observed!=expected:
            raise ValueError(f'Original source ZIP SHA256 mismatch: {basename}')
        found_hashes[basename]=observed
    early=manifest_part(read_member(archive_dir/'audit_2025_26_upload.zip',
                    'audit_2025_26/report_manifest.csv'),
                    'published_timestamp_utc','initial')
    targeted=manifest_part(read_member(archive_dir/'audit_2025_26_targeted_upload.zip',
                    'audit_2025_26_targeted/report_manifest.csv'),
                    'report_timestamp_utc','targeted')
    if len(early)!=EXPECTED_COUNT['initial'] or len(targeted)!=EXPECTED_COUNT['targeted']:
        raise ValueError('Original present PDF source counts changed')
    union=pd.concat([early,targeted],ignore_index=True)
    if len(union)!=EXPECTED_COUNT['full']:
        raise ValueError('Original union PDF source count changed')
    harmonized=union.loc[union.basename.str.endswith(CADENCE_SUFFIX)].copy()
    if len(harmonized)!=EXPECTED_COUNT['harmonized']:
        raise ValueError('Original harmonized cadence source count changed')
    schedule=read_member(archive_dir/'audit_2025_26_s4_join_results.zip',
                         's4_games_2025_26_normalized.csv')
    if len(schedule)!=EXPECTED_COUNT['games']:
        raise ValueError('Unexpected season schedule game count')
    results=[]
    for panel, source in [('full',union),('harmonized',harmonized)]:
        rebuilt=select_from_inventory(source,schedule)
        frozen=read_member(archive_dir/'nba_canonical_snapshot_selector_v1.zip',
           f'nba_canonical_snapshot_selector_v1/2025-26_game_snapshot_join_{panel}_canonical.csv')
        results.append(compare_selection(rebuilt,frozen,panel))
    return {
        'season':'2025-26','source_zip_sha256':found_hashes,
        'present_original_pdf_timestamps':{
          'initial':len(early),'targeted':len(targeted),'unique_full':len(union),
          'eligible_harmonized':len(harmonized)},
        'scope':'Independently reconstructed latest saved strictly pre-tip PDF per game; not full source completeness or body parsing',
        'all_available_source_selection_matches':True,'panels':results,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive-dir',type=Path,required=True)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    result=verify(args.archive_dir)
    rendered=json.dumps(result,indent=2)+'\n'
    if args.output:
        if args.output.exists():
            raise FileExistsError(f'Will not overwrite existing selector evidence: {args.output}')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered)
    print(rendered,end='')


if __name__=='__main__':
    main()
