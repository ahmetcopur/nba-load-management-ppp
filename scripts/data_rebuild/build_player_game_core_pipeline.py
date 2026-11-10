#!/usr/bin/env python3
"""Build the original six-season NBA player-game core, not just audit its inputs.

This stages the four authenticated private historical source packages, independently
recomputes selected-report NBA player IDs using the original reviewed crosswalk,
then EXECUTES the original immutable finalizer in an isolated workspace. Every
output CSV is compared to its frozen reference (gzip bytes may differ by mtime).

Boundary: selected_report_rows_all.csv and team_game_report_status.csv are
archived upstream intermediates. This is an executable source-intermediate ->
identity -> report-only roster union -> spells -> model-at-risk pipeline,
NOT yet a continuous raw-PDF -> published-regressions pipeline.
"""
from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from verify_player_identity_replay import (
    EXPECTED as IDENTITY_ZIPS, immutable_original_helpers, resolve,
    compare_exact, csv_from_zip, sha256_file,
)

CORE_ZIP = "nba_player_game_at_risk_core_v1.zip"
GAME_ZIP = "nba_game_covariates_v1.zip"
GAME_SHA256 = "4351756b74446577dabc8418b539c95dfb6e0ae6e3d8766bbee1c528d709c224"
FINALIZER_MEMBER = "nba_player_game_at_risk_core_v1/finalize_player_game_panel.py"
FINALIZER_SHA256 = "a0271f01f551dbbe1abedfac7ca8fefb9c865cd9b58a33185a3b7cbc991f8bfc"
ROOT_DIRECTIVE = b'ROOT=Path("/mnt/data")'

# Source member -> isolated original historical path. These are *input* CSVs.
STAGED_INPUTS = (
    (CORE_ZIP, "nba_player_game_at_risk_core_v1/team_game_report_status.csv",
     "nba_player_game_at_risk_core_v1/team_game_report_status.csv"),
    ("nba_boxscore_roster_frame_v2_output_upload.zip",
     "nba_boxscore_roster_frame_v2_output/game_roster_players.csv",
     "boxscore_v2_upload_inspect/nba_boxscore_roster_frame_v2_output/game_roster_players.csv"),
    (GAME_ZIP, "nba_game_covariates_v1/game_level_covariates.csv",
     "nba_game_covariates_v1/game_level_covariates.csv"),
    (GAME_ZIP, "nba_game_covariates_v1/team_game_covariates.csv",
     "nba_game_covariates_v1/team_game_covariates.csv"),
)
OUTPUT_NAMES = (
    "player_game_panel_core.csv.gz",
    "player_game_panel_model_at_risk.csv.gz",
    "absence_spells_provisional.csv.gz",
    "report_only_roster_additions.csv",
    "summary_by_season.csv",
    "onset_type_by_season.csv",
    "designation_status_by_season.csv",
    "taxonomy_validation_sample_300.csv",
)


def verify_archives(archive_dir: Path) -> dict[str, str]:
    pinned = dict(IDENTITY_ZIPS)
    pinned[GAME_ZIP] = GAME_SHA256
    checksums = {}
    for name, expected in pinned.items():
        path = archive_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Original source ZIP missing: {path}")
        digest = sha256_file(path)
        if digest != expected:
            raise ValueError(f"Original source ZIP changed: {name}: {digest}")
        checksums[name] = digest
    return checksums


def member_bytes(archive: Path, member: str) -> bytes:
    with ZipFile(archive) as z:
        if z.namelist().count(member) != 1:
            raise ValueError(f"Expected one original ZIP member {archive.name}::{member}")
        return z.read(member)


def stage_input_files(archive_dir: Path, workspace: Path) -> None:
    for filename, member, relative in STAGED_INPUTS:
        target = workspace / relative
        if target.exists():
            raise FileExistsError(f"Refusing to replace staged source: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(archive_dir / filename) as z:
            if z.namelist().count(member) != 1:
                raise ValueError(f"Missing/duplicate original source ZIP member: {filename}::{member}")
            with z.open(member) as src, target.open("xb") as dest:
                shutil.copyfileobj(src, dest)


def identity_worker(archive_dir: Path, workspace: Path) -> None:
    # Separate process: free the large DataFrames before the finalizer starts.
    verify_archives(archive_dir)
    src = csv_from_zip(archive_dir, CORE_ZIP,
                       "nba_player_game_at_risk_core_v1/selected_report_rows_all.csv")
    ref = csv_from_zip(archive_dir, CORE_ZIP,
                       "nba_player_game_at_risk_core_v1/selected_report_player_rows.csv")
    xw = csv_from_zip(archive_dir, "nba_player_crosswalk_final_v1.zip",
                      "nba_player_crosswalk_final_v1/player_crosswalk_final.csv")
    alias = csv_from_zip(archive_dir, "nba_player_crosswalk_final_v1.zip",
                         "nba_player_crosswalk_final_v1/player_alias_table.csv")
    roster = csv_from_zip(archive_dir, "nba_boxscore_roster_frame_v2_output_upload.zip",
                          "nba_boxscore_roster_frame_v2_output/game_roster_players.csv")
    result, details = resolve(src, xw, alias, roster, immutable_original_helpers(archive_dir))
    comparison = compare_exact(result, ref)
    required_counts = {
        "crosswalk_matched": 72819, "reviewed_alias_fallback": 606,
        "unique_roster_name_fallback": 15, "unresolved_before_final_dedup": 0,
        "final_player_report_rows": 73438,
    }
    for key, expected in required_counts.items():
        if details[key] != expected:
            raise ValueError(f"Identity-stage {key} changed: {details[key]} != {expected}")
    if comparison["rows"] != 73438 or comparison["fields_compared"] != 33:
        raise ValueError("Frozen identity table shape changed")
    dest = workspace / "nba_player_game_at_risk_core_v1/selected_report_player_rows.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise FileExistsError(f"Refusing to replace original identity-stage output: {dest}")
    result.to_csv(dest, index=False)
    report = {"identity_counts": details, "complete_frozen_identity_match": comparison}
    (workspace / "identity_stage_report.json").write_text(json.dumps(report, indent=2) + "\n")
    del src, ref, xw, alias, roster, result
    gc.collect()


def original_finalizer_adapter(archive_dir: Path, workspace: Path) -> Path:
    original = member_bytes(archive_dir / CORE_ZIP, FINALIZER_MEMBER)
    digest = hashlib.sha256(original).hexdigest()
    if digest != FINALIZER_SHA256:
        raise ValueError("Original finalizer SHA-256 differs from immutable source")
    if original.count(ROOT_DIRECTIVE) != 1:
        raise ValueError("Original finalizer root directive unexpectedly changed")
    # Only historical absolute ROOT is adapted, not any model or data operation.
    new_root = ("ROOT=Path(" + repr(str(workspace)) + ")").encode("utf-8")
    rewritten = original.replace(ROOT_DIRECTIVE, new_root)
    target = workspace / "_pinned_original_finalizer_root_adapter.py"
    target.write_bytes(rewritten)
    return target


def csv_content_sha256(path: Path, *, is_gzip: bool) -> tuple[str, int]:
    digest = hashlib.sha256()
    length = 0
    opener = gzip.open if is_gzip else open
    with opener(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
            length += len(chunk)
    return digest.hexdigest(), length


def frozen_csv_content_sha256(archive: Path, member: str, *, is_gzip: bool) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    with ZipFile(archive) as z:
        if z.namelist().count(member) != 1:
            raise ValueError(f"Frozen core output member missing/duplicated: {member}")
        with z.open(member) as zipped:
            with gzip.GzipFile(fileobj=zipped) if is_gzip else zipped as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
                    count += len(chunk)
    return digest.hexdigest(), count


def compare_core_outputs(archive_dir: Path, workspace: Path) -> dict:
    output = workspace / "nba_player_game_at_risk_core_v1"
    evidence = {}
    for basename in OUTPUT_NAMES:
        local = output / basename
        if not local.is_file():
            raise FileNotFoundError(f"Finalizer did not produce {local}")
        frozen_member = f"nba_player_game_at_risk_core_v1/{basename}"
        is_gzip = basename.endswith(".gz")
        observed = csv_content_sha256(local, is_gzip=is_gzip)
        expected = frozen_csv_content_sha256(archive_dir / CORE_ZIP, frozen_member,
                                             is_gzip=is_gzip)
        if observed != expected:
            raise ValueError(f"Newly generated core output differs from frozen CSV: {basename}")
        evidence[basename] = {
            "decoded_csv_sha256": observed[0],
            "decoded_csv_bytes": observed[1],
            "decoded_contents_match_frozen": True,
            "compression_header_excluded_from_comparison": is_gzip,
        }
    return evidence


def run_pipeline(archive_dir: Path, output_dir: Path, *, timeout: int = 900) -> dict:
    archive_dir = archive_dir.resolve(strict=True)
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"Use a new, empty output destination: {output_dir}")
    if output_dir == archive_dir or output_dir in archive_dir.parents:
        raise ValueError("Output directory must not be the original source archive directory")
    checksums = verify_archives(archive_dir)
    output_dir.mkdir(parents=True)
    stage_input_files(archive_dir, output_dir)
    this_file = Path(__file__).resolve()
    child = [sys.executable, str(this_file), "--archive-dir", str(archive_dir),
             "--output-dir", str(output_dir), "--identity-worker"]
    subprocess.run(child, check=True, timeout=timeout)
    adapter = original_finalizer_adapter(archive_dir, output_dir)
    subprocess.run([sys.executable, str(adapter)], cwd=output_dir,
                   check=True, timeout=timeout)
    compared = compare_core_outputs(archive_dir, output_dir)
    with (output_dir / "identity_stage_report.json").open() as f:
        identity = json.load(f)
    report = {
        "scope": "real archived selected source rows -> independent reviewed identity -> original report-only roster union, spells and at-risk panel",
        "source_archive_sha256": checksums,
        "identity": identity,
        "source_finalizer_sha256": FINALIZER_SHA256,
        "all_finalizer_outputs_exact_against_frozen_decoded_csv": True,
        "outputs": compared,
        "frozen_inputs_or_private_raw_zips_mutated": False,
        "fresh_raw_pdf_reparsing_in_this_pipeline": False,
        "published_model_regressions_rerun_in_this_pipeline": False,
    }
    (output_dir / "pipeline_rebuild_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--timeout", default=900, type=int)
    p.add_argument("--identity-worker", action="store_true",
                   help=argparse.SUPPRESS)
    args = p.parse_args()
    if args.timeout <= 0:
        raise ValueError("Timeout must be positive")
    if args.identity_worker:
        identity_worker(args.archive_dir, args.output_dir)
    else:
        run_pipeline(args.archive_dir, args.output_dir, timeout=args.timeout)


if __name__ == "__main__":
    main()
