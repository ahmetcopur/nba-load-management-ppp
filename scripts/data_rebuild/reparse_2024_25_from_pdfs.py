#!/usr/bin/env python3
"""Optional fallback when the corrected 2024-25 intermediate ZIP is unavailable.

Reparse original 2024-25 official PDFs and require equivalence with the
previous pre-S4 parse and the frozen canonical selector fingerprint.
Do NOT use this path for canonical verification if the original corrected
archive (audit_2024_25_pre_s4_outputs_corrected.zip) is accessible.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import zipfile

import pandas as pd

PARSER = "cadence_core_full/nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py"
TARGET = "cadence_work/season_parsed/2024-25/s1_snapshot_rows_regular_season_real.csv"
WORK = "cadence_work/source_pdfs/2024-25"
PRE_S4_ROWS = "s1_snapshot_rows_regular_season.csv"
PRE_S4_MANIFEST = "report_manifest_regular_season.csv"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def one_member(archive, basename):
    matches = [name for name in archive.namelist() if Path(name).name == basename]
    if len(matches) != 1:
        raise ValueError(f"{archive.filename}: expected one {basename}, found {matches}")
    return matches[0]


def inventory_archive_sha(metadata_dir):
    with (metadata_dir / "injury_archive_summary.csv").open(newline="") as stream:
        rows = [row for row in csv.DictReader(stream)
                if row["archive"] == "audit_2024_25_upload.zip"]
    if len(rows) != 1:
        raise ValueError("The historical inventory must list the original 2024-25 archive once")
    return rows[0]["archive_sha256"]


def selector_fields(rows, status):
    """Repeat original canonical selector's per-team-game bookkeeping.

    The original selector keeps the previous nplayers for not_yet_submitted
    rows. This original historical quirk must be reproduced for exact QA
    comparison, not silently repaired within a historical replay.
    """
    def norm_team(value):
        if pd.isna(value):
            return ""
        normalized = " ".join(
            str(value).lower().replace(".", "").replace("'", "").split())
        return {"la clippers": "los angeles clippers"}.get(normalized, normalized)

    data = rows.copy()
    data["snapshot_basename"] = (
        data["source_file"].astype(str).str.replace("\\", "/", regex=False)
            .str.rsplit("/", n=1).str[-1]
    )
    data["team_norm2"] = data["team_norm"].map(norm_team)
    groups = {key: subset for key, subset in data.groupby(
        ["snapshot_basename", "matchup_norm", "team_norm2"],
        dropna=False, sort=False)}
    results = []
    nplayers = 0
    for team in status.itertuples(index=False):
        selected = groups.get((team.snapshot_basename, team.matchup_norm, team.team_norm))
        if selected is not None and len(selected):
            if "not_yet_submitted" in set(
                    selected["team_submission_status"].dropna().astype(str)):
                final = "not_yet_submitted"
            else:
                nplayers = int(selected["player_name"].notna().sum())
                final = ("submitted_with_listed_players" if nplayers > 0
                         else "submitted_no_listed_players")
            out = int(selected["current_status"].astype(str).str.lower().eq("out").sum())
            available = int(selected["current_status"].astype(str).str.lower().eq("available").sum())
        else:
            nplayers, final, out, available = 0, "submitted_no_listed_players", 0, 0
        results.append((final, nplayers, out, available))
    return pd.DataFrame(results, columns=[
        "team_final_status", "n_player_rows", "n_out", "n_available"])


def read_selector_status(selector_zip):
    with zipfile.ZipFile(selector_zip) as archive:
        return {
            panel: pd.read_csv(archive.open(one_member(
                archive, f"2024-25_team_game_status_{panel}_canonical.csv")))
            for panel in ("full", "harmonized")
        }


def check_selector_fingerprint(rows, statuses):
    report = {}
    for panel, expected in statuses.items():
        observed = selector_fields(rows, expected)
        mismatches = {
            col: int(observed[col].astype(str).ne(expected[col].astype(str)).sum())
            for col in observed.columns
        }
        report[panel] = {"team_games": len(expected), "mismatches": mismatches}
        if any(mismatches.values()):
            raise RuntimeError(f"2024-25 source reparse changes the {panel} selector: {mismatches}")
    return report


def same_rows(left, right):
    """Scientific row multiset identity, independent of worker completion order."""
    cols = list(left.columns)
    if cols != list(right.columns) or len(left) != len(right):
        return False
    return (left.sort_values(cols).reset_index(drop=True)
            .equals(right.sort_values(cols).reset_index(drop=True)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--pdf-zip", type=Path, required=True)
    parser.add_argument("--pre-s4-zip", type=Path, required=True)
    parser.add_argument("--selector-zip", type=Path, required=True)
    parser.add_argument("--metadata-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    root = args.historical_root.resolve()
    target = root / TARGET
    if target.exists():
        raise SystemExit(f"Refusing to overwrite original 2024-25 input: {target}")

    archive_sha = sha256_file(args.pdf_zip)
    expected_sha = inventory_archive_sha(args.metadata_dir)
    if archive_sha != expected_sha:
        raise RuntimeError(f"Original 2024-25 PDF archive hash mismatch: {archive_sha} != {expected_sha}")

    work = root / WORK
    work.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.pre_s4_zip) as archive:
        manifest_bytes = archive.read(one_member(archive, PRE_S4_MANIFEST))
        archived_rows = pd.read_csv(
            archive.open(one_member(archive, PRE_S4_ROWS)),
            dtype=str, keep_default_na=False)

    manifest_path = work / "audit_2024_25" / PRE_S4_MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(manifest_bytes)
    manifest = pd.read_csv(manifest_path)
    manifest = manifest[manifest["exists"].astype(str).str.lower().eq("true")]

    with zipfile.ZipFile(args.pdf_zip) as archive:
        members = set(archive.namelist())
        for row in manifest.itertuples():
            member = Path(row.local_path)
            if member.is_absolute() or ".." in member.parts or "\\" in str(row.local_path):
                raise RuntimeError(f"Unsafe PDF manifest path: {row.local_path}")
            if row.local_path not in members:
                raise RuntimeError(f"Original PDF absent: {row.local_path}")
            data = archive.read(row.local_path)
            if sha256_bytes(data) != row.sha256:
                raise RuntimeError(f"Original PDF checksum mismatch: {row.local_path}")
            destination = work / member
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)

    out_rows = work / "s1_snapshot_rows_regular_season_reparsed.csv"
    out_log = work / "s1_parse_log_regular_season_reparsed.csv"
    environment = dict(os.environ, OPENBLAS_NUM_THREADS="2", OMP_NUM_THREADS="2")
    subprocess.run([
        sys.executable, "-I", str(root / PARSER),
        "--manifest", str(manifest_path.relative_to(work)),
        "--output", str(out_rows), "--parse-log", str(out_log),
        "--workers", str(args.workers),
    ], cwd=work, env=environment, check=True)

    log = pd.read_csv(out_log)
    if len(log) != len(manifest) or set(log["status"]) != {"ok"}:
        raise RuntimeError(f"Original 2024-25 PDF parser errors: {log.status.value_counts().to_dict()}")
    parsed = pd.read_csv(out_rows, dtype=str, keep_default_na=False)
    if int(log["extracted_rows"].sum()) != len(parsed):
        raise RuntimeError("Parsed CSV row count differs from individual PDF parse logs")
    if not same_rows(parsed, archived_rows):
        raise RuntimeError("Source reparse differs from original archived pre-S4 CSV")
    fingerprint = check_selector_fingerprint(
        pd.read_csv(out_rows, low_memory=False),
        read_selector_status(args.selector_zip))

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(out_rows.read_bytes())
    log_info = {
        "status": "SOURCE-REPARSED INPUT; NOT THE ORIGINAL CORRECTED ARCHIVE",
        "builder_path": TARGET,
        "missing_original": "audit_2024_25_pre_s4_outputs_corrected.zip :: s1_snapshot_rows_regular_season_real.csv",
        "pdf_archive_sha256": archive_sha,
        "pre_s4_zip_sha256": sha256_file(args.pre_s4_zip),
        "parser_sha256": sha256_file(root / PARSER),
        "pdfs_parsed": len(manifest),
        "rows": len(parsed),
        "output_sha256": sha256_file(target),
        "identical_to_archived_pre_s4_parse_as_row_multiset": True,
        "selector_fingerprint": fingerprint,
    }
    (root / "input_2024_25_provenance.json").write_text(
        json.dumps(log_info, indent=2) + "\n")
    print(json.dumps(log_info, indent=2))


if __name__ == "__main__":
    main()
