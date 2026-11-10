#!/usr/bin/env python3
"""Run the original NBA player-ID resolver AND final player-game panel builder.

This is an executable connected reconstruction from an ARCHIVED SELECTED-REPORT
CSV (not raw PDFs) to the frozen player-game core. All original input ZIPs are
read-only, hash pinned, and may stay outside the Git checkout.

The only modification to the original finalizer source is its hard-coded ROOT
path, redirected to a *new* private output directory. Its SHA-256 is checked
before that substitution. The original builder's destructive top-level setup
is never run: only its source-pinned helper functions are loaded. All results
are compared against frozen reference outputs; differences abort the run.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

# Support both "python scripts/data_rebuild/..." and package imports in tests.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.data_rebuild.verify_player_identity_replay import (
    EXPECTED as IDENTITY_ARCHIVE_SHA256,
    csv_from_zip, compare_exact, immutable_original_helpers,
    read_member, resolve, sha256_file,
)

SOURCE_CORE_ZIP = "nba_player_game_at_risk_core_v1.zip"
SOURCE_COVARIATE_ZIP = "nba_game_covariates_v1.zip"
COVARIATE_SHA256 = (
    "4351756b74446577dabc8418b539c95dfb6e0ae6e3d8766bbee1c528d709c224"
)
FINALIZER_MEMBER = "nba_player_game_at_risk_core_v1/finalize_player_game_panel.py"
FINALIZER_SHA256 = (
    "a0271f01f551dbbe1abedfac7ca8fefb9c865cd9b58a33185a3b7cbc991f8bfc"
)
ORIGINAL_ROOT_ASSIGNMENT = 'ROOT=Path("/mnt/data")'
SOURCE_MEMBERS = {
    "nba_player_game_at_risk_core_v1/team_game_report_status.csv":
        "nba_player_game_at_risk_core_v1/team_game_report_status.csv",
    "nba_boxscore_roster_frame_v2_output/game_roster_players.csv":
        "boxscore_v2_upload_inspect/nba_boxscore_roster_frame_v2_output/game_roster_players.csv",
    "nba_game_covariates_v1/game_level_covariates.csv":
        "nba_game_covariates_v1/game_level_covariates.csv",
    "nba_game_covariates_v1/team_game_covariates.csv":
        "nba_game_covariates_v1/team_game_covariates.csv",
}
SOURCE_MEMBER_ARCHIVES = {
    "nba_player_game_at_risk_core_v1/team_game_report_status.csv": SOURCE_CORE_ZIP,
    "nba_boxscore_roster_frame_v2_output/game_roster_players.csv":
        "nba_boxscore_roster_frame_v2_output_upload.zip",
    "nba_game_covariates_v1/game_level_covariates.csv": SOURCE_COVARIATE_ZIP,
    "nba_game_covariates_v1/team_game_covariates.csv": SOURCE_COVARIATE_ZIP,
}
COMPARISON_FILES = (
    "selected_report_player_rows.csv",
    "player_game_panel_core.csv.gz",
    "player_game_panel_model_at_risk.csv.gz",
    "absence_spells_provisional.csv.gz",
    "report_only_roster_additions.csv",
    "summary_by_season.csv",
    "onset_type_by_season.csv",
    "designation_status_by_season.csv",
    "taxonomy_validation_sample_300.csv",
    "qa_summary.json",
)
EXPECTED_RELEASE_COUNTS = {
    "selected_report_player_rows": 73438,
    "final_player_game_rows": 248730,
    "at_risk_rows": 180829,
    "report_only_roster_additions": 159,
    "absence_onsets": 12710,
    "observed_absence_spells": 13723,
}


def check_private_output_path(archive_dir: Path, output_dir: Path) -> None:
    """Do not silently overwrite prior outputs or write inside the raw ZIP folder."""
    source = archive_dir.resolve()
    output = output_dir.resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError("Output must be outside the original archive directory")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite any existing output: {output}")
    if any((parent / ".git").exists() for parent in (output, *output.parents)):
        raise ValueError("Output must be outside any Git checkout (it contains private rows)")
    if not source.is_dir():
        raise FileNotFoundError(f"Original ZIP directory not found: {source}")


def validate_source_archives(archive_dir: Path) -> dict[str, str]:
    expected = dict(IDENTITY_ARCHIVE_SHA256)
    expected[SOURCE_COVARIATE_ZIP] = COVARIATE_SHA256
    actual = {}
    for basename, sha in expected.items():
        path = archive_dir / basename
        if not path.is_file():
            raise FileNotFoundError(f"Required original ZIP missing: {path}")
        found = sha256_file(path)
        if found != sha:
            raise ValueError(f"Original archive SHA-256 changed: {basename}")
        actual[basename] = found
    return actual


def extract_exact_member(archive_zip: Path, member: str, destination: Path) -> None:
    """Copy just the known, hard-coded CSV member. Never extract a ZIP directory."""
    if destination.exists():
        raise FileExistsError(f"Will not overwrite staged CSV: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_zip) as archive:
        if archive.namelist().count(member) != 1:
            raise ValueError(f"Missing or duplicate source member: {archive_zip.name}::{member}")
        with archive.open(member) as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)


def compare_streams(archive_source, generated) -> dict:
    """Hash and compare full decoded byte streams in bounded memory."""
    expected_hash = hashlib.sha256()
    produced_hash = hashlib.sha256()
    expected_size = produced_size = 0
    while True:
        original = archive_source.read(1024 * 1024)
        current = generated.read(1024 * 1024)
        if original:
            expected_hash.update(original)
            expected_size += len(original)
        if current:
            produced_hash.update(current)
            produced_size += len(current)
        if original != current:
            raise ValueError("Reconstructed output bytes differ from immutable reference")
        if not original and not current:
            break
    return {
        "identical_decoded_bytes": True,
        "decoded_bytes": expected_size,
        "decoded_sha256": expected_hash.hexdigest(),
        "generated_decoded_sha256": produced_hash.hexdigest(),
    }


def compare_frozen_core_outputs(core_zip: Path, output_root: Path) -> dict:
    output = {}
    with ZipFile(core_zip) as reference:
        for name in COMPARISON_FILES:
            member = "nba_player_game_at_risk_core_v1/" + name
            if reference.namelist().count(member) != 1:
                raise ValueError(f"Reference ZIP member missing or duplicate: {member}")
            current = output_root / "nba_player_game_at_risk_core_v1" / name
            if not current.is_file():
                raise FileNotFoundError(f"Original finalizer failed to produce {current}")
            with reference.open(member) as stored, current.open("rb") as actual:
                if name.endswith(".gz"):
                    with gzip.GzipFile(fileobj=stored) as left, gzip.GzipFile(fileobj=actual) as right:
                        comparison = compare_streams(left, right)
                else:
                    comparison = compare_streams(stored, actual)
            output[name] = comparison
    return output


def source_pinned_finalizer(root: Path) -> bytes:
    original = read_member(root / SOURCE_CORE_ZIP, FINALIZER_MEMBER)
    digest = hashlib.sha256(original).hexdigest()
    if digest != FINALIZER_SHA256:
        raise ValueError(f"Original historical finalizer source changed: {digest}")
    text = original.decode("utf-8")
    if text.count(ORIGINAL_ROOT_ASSIGNMENT) != 1:
        raise ValueError("Original finalizer ROOT assignment has changed")
    # No algorithm changes: only redirect the original, hard-coded /mnt/data.
    return original


def write_relocated_finalizer(original: bytes, output_dir: Path) -> Path:
    text = original.decode("utf-8")
    if text.count(ORIGINAL_ROOT_ASSIGNMENT) != 1:
        raise ValueError("Cannot safely redirect the immutable original finalizer")
    modified = text.replace(
        ORIGINAL_ROOT_ASSIGNMENT,
        "ROOT=Path(" + repr(str(output_dir.resolve())) + ")",
        1,
    )
    path = output_dir / "original_finalizer_private_root.py"
    path.write_text(modified, encoding="utf-8")
    return path


def execute(archive_dir: Path, output_dir: Path, *, timeout_seconds: int = 900) -> dict:
    archive_dir, output_dir = archive_dir.resolve(), output_dir.resolve()
    check_private_output_path(archive_dir, output_dir)
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    source_hashes = validate_source_archives(archive_dir)
    finalizer_source = source_pinned_finalizer(archive_dir)
    helpers = immutable_original_helpers(archive_dir)

    selected = csv_from_zip(archive_dir, SOURCE_CORE_ZIP,
        "nba_player_game_at_risk_core_v1/selected_report_rows_all.csv")
    crosswalk = csv_from_zip(archive_dir, "nba_player_crosswalk_final_v1.zip",
        "nba_player_crosswalk_final_v1/player_crosswalk_final.csv")
    aliases = csv_from_zip(archive_dir, "nba_player_crosswalk_final_v1.zip",
        "nba_player_crosswalk_final_v1/player_alias_table.csv")
    roster = csv_from_zip(archive_dir,
        "nba_boxscore_roster_frame_v2_output_upload.zip",
        "nba_boxscore_roster_frame_v2_output/game_roster_players.csv")

    rebuilt_ids, identity_counts = resolve(selected, crosswalk, aliases, roster, helpers)
    frozen_ids = csv_from_zip(archive_dir, SOURCE_CORE_ZIP,
        "nba_player_game_at_risk_core_v1/selected_report_player_rows.csv")
    identity_result = compare_exact(rebuilt_ids, frozen_ids)
    if identity_result["rows"] != EXPECTED_RELEASE_COUNTS["selected_report_player_rows"]:
        raise ValueError("Original identity row count changed")
    if identity_result["fields_compared"] != 33:
        raise ValueError("Original identity schema has changed")
    if identity_counts["unresolved_before_final_dedup"] != 0:
        raise ValueError("Unresolved NBA player identities in reconstructed source")

    # Source hashes and independent player IDs have passed before writing
    # anything. This new directory is intentionally private and not Git-ignored.
    output_dir.mkdir(parents=True, exist_ok=False)
    for member, relative in SOURCE_MEMBERS.items():
        extract_exact_member(archive_dir / SOURCE_MEMBER_ARCHIVES[member],
                             member, output_dir / relative)
    output_core = output_dir / "nba_player_game_at_risk_core_v1"
    output_core.mkdir(parents=True, exist_ok=True)
    rebuilt_ids.to_csv(output_core / "selected_report_player_rows.csv", index=False)
    runner = write_relocated_finalizer(finalizer_source, output_dir)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(
        [sys.executable, str(runner)], cwd=output_dir, env=env,
        capture_output=True, text=True, timeout=timeout_seconds, check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"Immutable original finalizer returned {process.returncode}: "
            + (process.stderr + "\n" + process.stdout)[-1800:]
        )
    outputs = compare_frozen_core_outputs(
        archive_dir / SOURCE_CORE_ZIP, output_dir,
    )
    summary = json.loads((output_core / "qa_summary.json").read_text("utf-8"))
    count_disagreements = {
        key: {"actual": summary.get(key), "expected": value}
        for key, value in EXPECTED_RELEASE_COUNTS.items()
        if key != "selected_report_player_rows" and summary.get(key) != value
    }
    if count_disagreements:
        raise ValueError(f"Historical player-game finalizer scientific counts differ: {count_disagreements}")

    report = {
        "status": "pass",
        "scope": "Archived selected-report rows -> independently rebuilt identities -> original finalizer -> all frozen core outputs; NOT raw NBA PDFs to models",
        "original_archive_sha256": source_hashes,
        "original_finalizer_sha256": FINALIZER_SHA256,
        "identity": {"counts": identity_counts, "frozen_comparison": identity_result},
        "original_finalizer_summary": {
            key: summary[key] for key in EXPECTED_RELEASE_COUNTS
            if key in summary
        },
        "compared_original_outputs": outputs,
        "all_ten_outputs_identical_after_gzip_decoding": True,
        "private_source_pdfs_committed": False,
        "raw_report_selection_recomputed_here": False,
        "reviewed_awards_cup_tv_and_manuscript_rebuilt_here": False,
    }
    (output_dir / "connected_core_reproduction_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True,
                        help="Private directory containing the four pinned original ZIPs")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="New private directory OUTSIDE every Git checkout; may not already exist")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()
    result = execute(args.archive_dir, args.output_dir, timeout_seconds=args.timeout_seconds)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
