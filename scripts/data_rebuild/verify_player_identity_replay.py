#!/usr/bin/env python3
"""Verify original report-player to NBA-player identity resolution from private ZIPs.

Read-only; compare all 33 fields of the rebuilt selected-report player table
against immutable archived reference. The selected-report input itself is an
archived intermediate, not a fresh PDF extraction. No private files uploaded.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

EXPECTED = {
    "nba_player_game_at_risk_core_v1.zip":
        "a0f82ebcf6117554a4ce1064ab79db9cf93acc5a53fa25000343810843e659f6",
    "nba_player_crosswalk_final_v1.zip":
        "6ac400125d33a4e44e0f0a4a068f83762425da28bc1d86ce8fc3de8e6ccb3def",
    "nba_boxscore_roster_frame_v2_output_upload.zip":
        "45eeade023037506d1b07ebc601c273ec442f6620adc3ab836a3d40b8774f561",
}
BUILDER_MEMBER = "nba_player_game_at_risk_core_v1/build_selected_report_and_identity_stage.py"
BUILDER_SHA256 = "738b78fa9fd9f3cdd9f4b4eb6756b424680959cacb85cfc354a6d6affa915fef"
REPORT_FIELDS = ("season", "game_id", "team_norm", "player_name",
                 "current_status", "reason", "team_submission_status")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_member(path: Path, member: str) -> bytes:
    with ZipFile(path) as archive:
        if archive.namelist().count(member) != 1:
            raise ValueError(f"Original ZIP member missing/duplicate: {path.name}::{member}")
        return archive.read(member)


def csv_from_zip(root: Path, filename: str, member: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(read_member(root / filename, member)), low_memory=False)


def immutable_original_helpers(root: Path) -> dict:
    code = read_member(root / "nba_player_game_at_risk_core_v1.zip", BUILDER_MEMBER)
    if hashlib.sha256(code).hexdigest() != BUILDER_SHA256:
        raise ValueError("Original identity-stage source SHA-256 changed")
    source = code.decode("utf-8")
    # The original next statement DELETES/recreates its output directory.
    # Execute only the immutable helper definitions, never historical top-level I/O.
    boundary = "if OUT.exists(): shutil.rmtree(OUT)"
    if source.count(boundary) != 1:
        raise ValueError("Pinned original identity source safety boundary changed")
    namespace = {}
    exec(compile(source.split(boundary, 1)[0], BUILDER_MEMBER, "exec"), namespace)
    return {name: namespace[name] for name in
            ("clean", "norm_team", "full_report_name", "norm_person")}


def resolve(selected: pd.DataFrame, crosswalk: pd.DataFrame, alias: pd.DataFrame,
            roster: pd.DataFrame, h: dict) -> tuple[pd.DataFrame, dict]:
    """Replay only original source's player identity and final status-priority stage."""
    clean, norm_team, full_name, norm_person = (
        h["clean"], h["norm_team"], h["full_report_name"], h["norm_person"])
    required = set(REPORT_FIELDS)
    if not required <= set(selected):
        raise ValueError(f"Selected source report rows missing columns: {required-set(selected)}")
    selected = selected.copy()
    selected["team_norm"] = selected.team_norm.fillna("").map(norm_team)
    for column in ("player_name", "current_status", "reason"):
        selected[column] = selected[column].fillna("").map(clean)
    selected = selected.drop_duplicates([
        "season", "game_id", "team_norm", "player_name", "current_status",
        "reason", "team_submission_status",
    ])
    pr = selected[selected.player_name.ne("")].copy()
    xw = crosswalk.copy()
    xw["team_norm"] = xw.team_norm.map(norm_team)
    xw["player_name"] = xw.player_name.fillna("").map(clean)
    cols = ["season", "team_norm", "player_name", "nba_player_id",
            "nba_player_name", "resolution_method", "resolution_status"]
    xkey = xw[cols].drop_duplicates()
    pr = pr.merge(xkey, on=["season", "team_norm", "player_name"],
                  how="left", validate="many_to_one")
    pr["nba_player_id"] = pd.to_numeric(pr.nba_player_id, errors="coerce").astype("Int64")
    base_matched = int(pr.nba_player_id.notna().sum())
    pr["report_full_name"] = pr.player_name.map(full_name)
    pr["report_name_fallback_norm"] = pr.report_full_name.map(norm_person)
    alias = alias.copy()
    alias["report_name_fallback_norm"] = alias.report_full_name.map(norm_person)
    alias_unique = (alias.groupby("report_name_fallback_norm")
        .filter(lambda rows: rows.nba_player_id.nunique() == 1)
        .drop_duplicates("report_name_fallback_norm")[
            ["report_name_fallback_norm", "nba_player_id", "nba_player_name"]]
        .rename(columns={"nba_player_id": "alias_player_id",
                         "nba_player_name": "alias_player_name"}))
    pr = pr.merge(alias_unique, on="report_name_fallback_norm",
                  how="left", validate="many_to_one")
    alias_missing = pr.nba_player_id.isna() & pr.alias_player_id.notna()
    alias_count = int(alias_missing.sum())
    pr.loc[alias_missing, "nba_player_id"] = pd.to_numeric(
        pr.loc[alias_missing, "alias_player_id"], errors="coerce").astype("Int64")
    pr.loc[alias_missing, "nba_player_name"] = pr.loc[alias_missing, "alias_player_name"]
    pr.loc[alias_missing, "resolution_method"] = "fallback_reviewed_alias_table"

    roster = roster[["season", "team", "nba_player_id", "nba_player_name"]].copy()
    roster["team_norm"] = roster.team.map(norm_team)
    roster["report_name_fallback_norm"] = roster.nba_player_name.map(norm_person)
    roster_unique = (roster.groupby(["season", "team_norm", "report_name_fallback_norm"])
        .filter(lambda rows: rows.nba_player_id.nunique() == 1)
        .drop_duplicates(["season", "team_norm", "report_name_fallback_norm"])[
            ["season", "team_norm", "report_name_fallback_norm", "nba_player_id",
             "nba_player_name"]]
        .rename(columns={"nba_player_id": "roster_player_id",
                         "nba_player_name": "roster_player_name"}))
    pr = pr.merge(roster_unique,
        on=["season", "team_norm", "report_name_fallback_norm"],
        how="left", validate="many_to_one")
    roster_missing = pr.nba_player_id.isna() & pr.roster_player_id.notna()
    roster_count = int(roster_missing.sum())
    pr.loc[roster_missing, "nba_player_id"] = pd.to_numeric(
        pr.loc[roster_missing, "roster_player_id"], errors="coerce").astype("Int64")
    pr.loc[roster_missing, "nba_player_name"] = pr.loc[roster_missing, "roster_player_name"]
    pr.loc[roster_missing, "resolution_method"] = "fallback_unique_boxscore_name"
    pr["nba_player_id"] = pd.to_numeric(pr.nba_player_id, errors="coerce").astype("Int64")
    unresolved = int(pr.nba_player_id.isna().sum())
    severity = {"Out": 5, "Doubtful": 4, "Questionable": 3,
                "Probable": 2, "Available": 1, "": 0}
    pr["status_severity"] = pr.current_status.map(severity).fillna(0)
    pr = pr.sort_values(["game_id", "team_norm", "nba_player_id", "status_severity"])
    pr = pr.drop_duplicates(["game_id", "team_norm", "nba_player_id"], keep="last")
    summary = {
        "source_selected_report_rows_after_original_key_dedup": len(selected),
        "named_player_rows_before_identity_dedup": base_matched + alias_count + roster_count + unresolved,
        "crosswalk_matched": base_matched,
        "reviewed_alias_fallback": alias_count,
        "unique_roster_name_fallback": roster_count,
        "unresolved_before_final_dedup": unresolved,
        "final_player_report_rows": len(pr),
    }
    return pr, summary


def compare_exact(rebuilt: pd.DataFrame, reference: pd.DataFrame) -> dict:
    if set(rebuilt.columns) != set(reference.columns):
        raise ValueError(f"Identity output schema drift: {set(rebuilt)-set(reference)}, {set(reference)-set(rebuilt)}")
    keys = ["game_id", "team_norm", "nba_player_id"]
    if rebuilt.duplicated(keys).any() or reference.duplicated(keys).any():
        raise ValueError("Duplicate final player-game-team identity keys")
    if len(rebuilt) != len(reference):
        raise ValueError(f"Identity output row count drift: {len(rebuilt)} versus {len(reference)}")
    left = rebuilt.sort_values(keys).reset_index(drop=True)
    right = reference.sort_values(keys).reset_index(drop=True)
    mismatches = {}
    for field in reference.columns:
        a = left[field].fillna("NULL").astype(str).str.strip()
        b = right[field].fillna("NULL").astype(str).str.strip()
        n = int(a.ne(b).sum())
        if n:
            mismatches[field] = n
    if mismatches:
        raise ValueError(f"Exact frozen player identity replay changed fields: {mismatches}")
    return {"rows": len(right), "fields_compared": len(right.columns),
            "all_player_ids_and_fields_exact": True, "mismatches": {}}


def verify(root: Path) -> dict:
    hashes = {}
    for filename, expected in EXPECTED.items():
        actual = sha256_file(root / filename)
        if actual != expected:
            raise ValueError(f"Original identity ZIP hash mismatch: {filename}")
        hashes[filename] = actual
    h = immutable_original_helpers(root)
    src = csv_from_zip(root, "nba_player_game_at_risk_core_v1.zip",
                       "nba_player_game_at_risk_core_v1/selected_report_rows_all.csv")
    reference = csv_from_zip(root, "nba_player_game_at_risk_core_v1.zip",
                       "nba_player_game_at_risk_core_v1/selected_report_player_rows.csv")
    xw = csv_from_zip(root, "nba_player_crosswalk_final_v1.zip",
                       "nba_player_crosswalk_final_v1/player_crosswalk_final.csv")
    alias = csv_from_zip(root, "nba_player_crosswalk_final_v1.zip",
                       "nba_player_crosswalk_final_v1/player_alias_table.csv")
    roster = csv_from_zip(root, "nba_boxscore_roster_frame_v2_output_upload.zip",
                       "nba_boxscore_roster_frame_v2_output/game_roster_players.csv")
    rebuilt, counts = resolve(src, xw, alias, roster, h)
    comparison = compare_exact(rebuilt, reference)
    if (comparison["rows"] != 73438 or comparison["fields_compared"] != 33
            or counts["crosswalk_matched"] != 72819
            or counts["reviewed_alias_fallback"] != 606
            or counts["unique_roster_name_fallback"] != 15
            or counts["unresolved_before_final_dedup"] != 0):
        raise ValueError("Unexpected original identity-stage release cardinalities")
    return {
        "scope": "Archived selected player-report rows -> crosswalk/alias/roster identity -> frozen selected_report_player_rows, not raw PDF or full player-game models",
        "source_zip_sha256": hashes,
        "original_identity_source_sha256": BUILDER_SHA256,
        "source_counts": counts, "exact_reference_comparison": comparison,
        "private_files_written_or_uploaded": False,
        "full_source_to_player_game_model_complete": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = verify(args.archive_dir)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"Refusing to overwrite previous identity acceptance: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
