#!/usr/bin/env python3
"""Run unchanged archived August category-FDR executable on frozen/variant panels.

The source public announcement-TV table itself carries the two obsolete Feb
2022 fixture keys. For the corrected chronology, update exactly two table
date/time keys, NOT release-time networks, before running the unchanged script.

This preserves the original four-category FDR family under EACH TV definition,
including two-way player/game clustering and original controls/FE.
Never edits the shared repo, original output or frozen panel.

Public CI can run --frozen-only; corrected execution requires a separate,
source-verified private 180831-row August latest-pre-tip risk panel.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

SHARED_SHA = "0bd713d97e8d519df5700ef473da34aba4495223"
ORIGINAL_RISK_DECODED_SHA = "ed23db38124e07e48bf8418a1c1935667a424d2e6aa41ea807dcd63e65a894f3"  # checked below in CI; see SHA gate
CORRECTED_RISK_DECODED_SHA = "5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3"
SCRIPT = Path("scripts/portable/run_category_fdr.py")
PANEL = Path("data_final/player_game_panel_model_at_risk_analysis_ready.csv.gz")
TV = Path("data_intermediate/announced_tv_six_seasons.csv")
RESULTS = Path("results/portable_category_fdr/category_focal_fdr.csv")
ARCHIVE = Path("results/category_focal_fdr.csv")
CORRECTIONS = (
    {"season":"2021-22","home_team":"Toronto Raptors","away_team":"Chicago Bulls",
     "original_date":"2022-02-01","corrected_date":"2022-02-03",
     "corrected_tip":"2022-02-04T00:30:00Z","expected_primary":False},
    {"season":"2021-22","home_team":"Toronto Raptors","away_team":"Miami Heat",
     "original_date":"2022-02-03","corrected_date":"2022-02-01",
     "corrected_tip":"2022-02-02T00:30:00Z","expected_primary":True},
)
KEY = ["tv_definition","outcome"]
EXPECTED_OUTCOMES = {
    "vague_onset_frozen","specific_onset_frozen",
    "explicit_rest_onset_frozen","other_absence_onset_frozen",
}
EXPECTED_TV = {"announced_tv_primary","tv_harmonized_linear"}
SOURCE_JOIN = ["season","game_date_et","home_team","away_team"]


def sha(path: Path, decoded=False):
    digest = hashlib.sha256()
    with (gzip.open(path, "rb") if decoded else path.open("rb")) as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_shared(shared: Path):
    head = subprocess.run(
        ["git","-C",str(shared),"rev-parse","HEAD"],
        check=True,capture_output=True,text=True,
    ).stdout.strip()
    if head != SHARED_SHA:
        raise RuntimeError(f"Shared source commit changed: {head}")
    status = subprocess.run(
        ["git","-C",str(shared),"status","--porcelain"],
        check=True,capture_output=True,text=True,
    ).stdout.strip()
    if status:
        raise RuntimeError("Source repo has uncommitted changes; use a clean checkout")
    for rel in (SCRIPT,PANEL,TV,ARCHIVE):
        if not (shared/rel).is_file():
            raise FileNotFoundError(shared/rel)


def stage(shared: Path, stage_root: Path, corrected_panel: Path|None=None):
    if stage_root.exists():
        raise FileExistsError(f"Output replay staging exists: {stage_root}")
    for file in (SCRIPT,PANEL,TV):
        dest = stage_root/file
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(shared/file,dest)
    if corrected_panel:
        shutil.copy2(corrected_panel,stage_root/PANEL)


def original_source_tv_matches_panel(panel: Path, tv_path: Path):
    """Return full risk join and require complete physical-game source consistency."""
    data = pd.read_csv(
        panel,low_memory=False,
        usecols=["season","game_date_et","game_id","team","opponent",
                 "is_home","announced_tv_primary"],
    )
    tv = pd.read_csv(tv_path,low_memory=False)
    if tv.duplicated(SOURCE_JOIN).any():
        raise RuntimeError("Duplicate source TV fixture lookup keys")
    data["home_team"] = np.where(data.is_home,data.team,data.opponent)
    data["away_team"] = np.where(data.is_home,data.opponent,data.team)
    merged = data.merge(
        tv[SOURCE_JOIN+["announced_tv_status","announced_tv_primary",
                        "network_announced"]],
        on=SOURCE_JOIN,how="left",validate="many_to_one",suffixes=("_panel","_source"),
    )
    status = merged.announced_tv_status.notna()
    valid = merged.loc[status].announced_tv_primary_panel.eq(
        merged.loc[status].announced_tv_primary_source)
    if not valid.all():
        raise RuntimeError("Archived as-announced TV exposure differs from source for matched game")
    return merged


def repair_announcement_fixture_keys(source_tv: Path, corrected_panel: Path):
    """Rekey exactly two source rows, preserving network and original release metadata."""
    tv = pd.read_csv(source_tv,low_memory=False)
    old_tv = tv.copy(deep=True)
    details=[]
    for row in CORRECTIONS:
        mask=(tv.season.eq(row["season"]) &
              tv.home_team.eq(row["home_team"]) &
              tv.away_team.eq(row["away_team"]) &
              tv.game_date_et.eq(row["original_date"]))
        if mask.sum()!=1:
            raise RuntimeError(f"Source TV expected one entry for {row['away_team']}, found {mask.sum()}")
        original=tv.loc[mask].iloc[0]
        if bool(original.announced_tv_primary) != row["expected_primary"]:
            raise RuntimeError("Original released TV exposure differs unexpectedly")
        tv.loc[mask,"game_date_et"] = row["corrected_date"]
        tv.loc[mask,"tip_utc"] = pd.Timestamp(row["corrected_tip"]).isoformat(sep=" ")
        # Both games tipped at 7:30 PM Eastern, so tip_et does not change.
        details.append({
            "away_team":row["away_team"],"home_team":row["home_team"],
            "old_date":row["original_date"],"new_date":row["corrected_date"],
            "original_network":None if pd.isna(original.network_announced)
                                else str(original.network_announced),
            "original_primary_tv":row["expected_primary"],
            "historical_fixture_row":int(original.fixture_row),
        })
    if tv.duplicated(SOURCE_JOIN).any():
        raise RuntimeError("Rekeyed TV fixture contains duplicate lookup keys")
    modified_cols=[c for c in tv.columns if not
                   tv[c].fillna("__NA__").astype(str).equals(
                       old_tv[c].fillna("__NA__").astype(str))]
    if set(modified_cols)!={"game_date_et","tip_utc"}:
        raise RuntimeError(f"Unexpected source TV columns modified: {modified_cols}")
    tv.to_csv(source_tv,index=False)
    joined=original_source_tv_matches_panel(corrected_panel,source_tv)
    if joined.announced_tv_status.isna().any():
        missing=joined.loc[joined.announced_tv_status.isna(),"game_id"].value_counts().to_dict()
        raise RuntimeError(f"Corrected game cannot join original TV source: {missing}")
    if len(joined)!=180831:
        raise RuntimeError("Corrected category input risk sample not 180831")
    return details


def run(stage_root: Path, executable: str):
    env = {**os.environ,
           "OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1"}
    log = stage_root/"category_script.log"
    with log.open("w") as outfile:
        subprocess.run([executable,str(stage_root/SCRIPT)],cwd=stage_root,
                       env=env,stdout=outfile,stderr=subprocess.STDOUT,
                       timeout=1000,check=True)
    produced = stage_root/RESULTS
    if not produced.is_file():
        raise RuntimeError("Unchanged category executable did not produce FDR table")
    result=pd.read_csv(produced)
    if (len(result)!=8 or result.duplicated(KEY).any() or
        set(result.tv_definition)!=EXPECTED_TV or
        set(result.outcome)!=EXPECTED_OUTCOMES):
        raise RuntimeError("Unexpected eight category specifications")
    for tv,group in result.groupby("tv_definition"):
        if len(group)!=4 or group.n.nunique()!=1:
            raise RuntimeError(f"{tv}: category family or N invalid")
    return result


def compare_baseline(published: pd.DataFrame, recreated: pd.DataFrame):
    if published.duplicated(KEY).any():
        raise RuntimeError("Historical reference has duplicate model identifiers")
    joined = published.merge(recreated,on=KEY,how="outer",indicator=True,
                             suffixes=("_archived","_fresh"),validate="one_to_one")
    if len(joined)!=8 or not joined._merge.eq("both").all():
        raise RuntimeError("Category benchmark missing/extra specification")
    numeric=("estimate_pp","se_pp","low_pp","high_pp","p","q_bh","p_holm")
    diffs={}
    for col in numeric:
        delta=(joined[f"{col}_archived"] - joined[f"{col}_fresh"]).abs()
        maxdelta=float(delta.max())
        if not np.isfinite(maxdelta) or maxdelta>1e-7:
            raise RuntimeError(f"Original August category {col} does not reproduce: {maxdelta}")
        diffs[col]=maxdelta
    if not joined.n_archived.eq(joined.n_fresh).all():
        raise RuntimeError("Category frozen reference Ns mismatch")
    return diffs


def delta_table(before: pd.DataFrame, after: pd.DataFrame):
    joined=before.merge(after,on=KEY,how="outer",indicator=True,
                        suffixes=("_frozen","_corrected"),validate="one_to_one")
    if len(joined)!=8 or not joined._merge.eq("both").all():
        raise RuntimeError("Category corrected outputs have missing specs")
    if not joined.n_frozen.eq(180695).all() or not joined.n_corrected.eq(180697).all():
        raise RuntimeError("Category corrected complete-case sample drift")
    joined["change_pp"]=joined.estimate_pp_corrected-joined.estimate_pp_frozen
    return joined.drop(columns="_merge")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shared-repo",required=True,type=Path)
    ap.add_argument("--work",required=True,type=Path)
    ap.add_argument("--corrected-panel",type=Path)
    ap.add_argument("--frozen-only",action="store_true")
    ap.add_argument("--python",default=sys.executable)
    args=ap.parse_args()
    shared,work=args.shared_repo.resolve(),args.work.resolve()
    corrected=args.corrected_panel.resolve() if args.corrected_panel else None
    if not args.frozen_only and corrected is None:
        ap.error("Provide --corrected-panel or --frozen-only")
    if corrected and not corrected.is_file():
        raise FileNotFoundError(corrected)
    if work.exists() or work==shared or work in shared.parents or shared in work.parents:
        raise RuntimeError("Work root must be fresh and separate from shared source")
    if corrected and (corrected==work or work in corrected.parents or corrected in work.parents):
        raise RuntimeError("Work cannot overlap corrected input")
    verify_shared(shared)
    frozen_root=work/"frozen"
    stage(shared,frozen_root)
    original=original_source_tv_matches_panel(frozen_root/PANEL,frozen_root/TV)
    if original.announced_tv_status.isna().any():
        raise RuntimeError("Original frozen game-date TV join already incomplete")
    if len(original)!=180829:
        raise RuntimeError("Unexpected historical frozen risk sample")
    baseline=run(frozen_root,args.python)
    archive=pd.read_csv(shared/ARCHIVE)
    deviations=compare_baseline(archive,baseline)
    report={
        "shared_source_commit":SHARED_SHA,
        "original_release_script_sha256":sha(shared/SCRIPT),
        "original_announcement_tv_sha256":sha(shared/TV),
        "original_risk_panel_sha256":sha(shared/PANEL,decoded=True),
        "historical_frozen_models_reproduced":8,
        "published_table_numeric_max_abs_difference":deviations,
        "correction_scope":"Only original TV table's two obsolete source-fixture date and UTC tip keys rekeyed; no published network/source announcement reassignment.",
        "frozen_unchanged":True,
    }
    if corrected:
        actual_sha=sha(corrected,decoded=True)
        if actual_sha!=CORRECTED_RISK_DECODED_SHA:
            raise RuntimeError(f"Corrected source risk SHA mismatch: {actual_sha}")
        variant_root=work/"corrected"
        stage(shared,variant_root,corrected)
        details=repair_announcement_fixture_keys(variant_root/TV,variant_root/PANEL)
        variant=run(variant_root,args.python)
        changes=delta_table(baseline,variant)
        changes.to_csv(work/"august_category_corrected_vs_frozen.csv",index=False)
        report.update({
            "corrected_risk_panel_decoded_sha256":actual_sha,
            "corrected_source_TV_rekeys":details,
            "category_replay_rows":len(changes),
            "corrected_risk_rows":180831,
            "corrected_complete_case_n":180697,
            "recomputed_adjustments":"Benjamini-Hochberg FDR and Holm per TV definition across four category-specific outcomes",
            "sensitivity_results":changes.replace({np.nan:None}).to_dict("records"),
            "source_limit":"Award/star and Cup flags inherited; two date-encoded frozen game IDs retained; no full six-season source-to-paper claim.",
        })
    work.mkdir(exist_ok=True)
    (work/"august_category_fdr_replay.json").write_text(
        json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:v for k,v in report.items()
                      if k!="sensitivity_results"},indent=2))


if __name__=="__main__":
    main()
