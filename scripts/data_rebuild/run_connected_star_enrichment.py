#!/usr/bin/env python3
"""Continue a successful connected core reproduction through the original star builder.

Original 2017–2026 All-Star and All-NBA source lists are embedded in the
historically archived builder: this replays the frozen lists and implementation,
not independent validation of official award announcements.

The original source hash is pinned, and its only adaptation is to redirect four
hard-coded /mnt/data/ paths to an already accepted private core-run directory.
All twelve historical non-manifest outputs are compared to the original ZIP,
with the gzip envelope ignored. The derived file_manifest_sha256.csv is excluded
from exact comparison because generated gzip timestamps can legitimately differ.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import os
import subprocess
import sys
from zipfile import ZipFile
import gzip

from scripts.data_rebuild.run_connected_player_game_core import (
    SOURCE_CORE_ZIP, compare_frozen_core_outputs, compare_streams,
    sha256_file,
)

STAR_ZIP = "nba_player_game_at_risk_star_v1.zip"
STAR_ZIP_SHA256 = (
    "6513069ffc81535edc2af04acbb7550f227fb074ea51241e0e800cebe9f1eb70"
)
STAR_BUILDER_MEMBER = "nba_player_game_at_risk_star_v1/build_star_status_v1.py"
STAR_BUILDER_SHA256 = (
    "90de4a115d5434c3616ca2f52e3457d846a2e079d58136653831b50aa054877b"
)
EXPECTED_OLD_ROOT_OCCURRENCES = 4
STAR_OUTPUTS = (
    "README.md",
    "absence_spells_provisional_star.csv.gz",
    "build_star_status_v1.py",
    "player_game_panel_model_at_risk_star.csv.gz",
    "player_game_panel_star.csv.gz",
    "player_season_star_status_calendar.csv",
    "qa_summary.json",
    "selected_report_player_rows.csv",
    "star_award_history.csv",
    "star_summary_by_season.csv",
    "taxonomy_validation_sample_300.csv",
    "team_game_report_status.csv",
)
EXPECTED_QA_COUNTS = {
    "player_game_rows": 248730,
    "missing_star_status_rows": 0,
    "star_player_game_rows": 23166,
    "true_midseason_star_transition_rows": 1019,
    "at_risk_rows": 180829,
    "absence_onsets": 12710,
    "award_rows": 358,
    "award_unmatched_rows": 0,
}


def validate_private_star_destination(archive_dir: Path, core_run_dir: Path) -> None:
    archive_dir, core_run_dir = archive_dir.resolve(), core_run_dir.resolve()
    if not archive_dir.is_dir() or not core_run_dir.is_dir():
        raise FileNotFoundError("Original ZIP directory and completed private core-run directory required")
    if archive_dir == core_run_dir or archive_dir in core_run_dir.parents:
        raise ValueError("Private star run cannot be inside the original source ZIP directory")
    if any((parent / ".git").exists() for parent in (core_run_dir, *core_run_dir.parents)):
        raise ValueError("Private player-level outputs cannot be written in a Git checkout")
    if (core_run_dir / "nba_player_game_at_risk_star_v1").exists():
        raise FileExistsError("A star-enriched output directory already exists; refusing destructive historical rebuild")
    if (core_run_dir / STAR_ZIP).exists():
        raise FileExistsError("A previous generated star ZIP exists; refusing original script ZIP unlink")
    if (core_run_dir / "build_star_status_v1.py").exists():
        raise FileExistsError("Original star builder staged earlier; use a new core run directory")
    report_path = core_run_dir / "connected_core_reproduction_report.json"
    if not report_path.is_file():
        raise FileNotFoundError("A successful connected core runner report is required")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("status") != "pass" or not report.get("all_ten_outputs_identical_after_gzip_decoding"):
        raise ValueError("Connected core output has not passed all ten exact frozen output checks")


def immutable_original_star_source(star_archive: Path) -> bytes:
    if not star_archive.is_file():
        raise FileNotFoundError(f"Original archived star source not found: {star_archive}")
    if sha256_file(star_archive) != STAR_ZIP_SHA256:
        raise ValueError("Original All-Star and All-NBA star source ZIP hash changed")
    with ZipFile(star_archive) as archive:
        if archive.namelist().count(STAR_BUILDER_MEMBER) != 1:
            raise ValueError("Archived star builder missing or duplicated")
        original = archive.read(STAR_BUILDER_MEMBER)
    if hashlib.sha256(original).hexdigest() != STAR_BUILDER_SHA256:
        raise ValueError("Original All-Star/All-NBA star builder source SHA256 changed")
    if original.decode("utf-8").count("/mnt/data/") != EXPECTED_OLD_ROOT_OCCURRENCES:
        raise ValueError("Historical star builder no longer has four expected path prefixes")
    return original


def write_root_relocated_builder(original: bytes, private_root: Path) -> Path:
    """Redirect only the original four hard-coded paths; no algorithm edits."""
    text = original.decode("utf-8")
    if text.count("/mnt/data/") != EXPECTED_OLD_ROOT_OCCURRENCES:
        raise ValueError("Original star script hard-coded path layout changed")
    prefix = str(private_root.resolve()) + "/"
    if "\n" in prefix or "'" in prefix or '"' in prefix:
        raise ValueError("Private run path contains unsafe quote or newline")
    modified = text.replace("/mnt/data/", prefix)
    staged = private_root / "build_star_status_v1.py"
    adapted = private_root / "original_star_builder_private_root.py"
    if staged.exists() or adapted.exists():
        raise FileExistsError("Star builder staging file already exists")
    # The original script copies this untouched source into its output ZIP.
    staged.write_bytes(original)
    adapted.write_text(modified, encoding="utf-8")
    return adapted


def compare_original_star_outputs(source_archive: Path, root: Path) -> dict:
    results = {}
    with ZipFile(source_archive) as archive:
        for name in STAR_OUTPUTS:
            member = "nba_player_game_at_risk_star_v1/" + name
            if archive.namelist().count(member) != 1:
                raise ValueError(f"Missing/duplicate original star output: {member}")
            candidate = root / "nba_player_game_at_risk_star_v1" / name
            if not candidate.is_file():
                raise FileNotFoundError(f"Rebuilt star stage lacks {name}")
            with archive.open(member) as archived, candidate.open("rb") as rebuilt:
                if name.endswith(".gz"):
                    with gzip.GzipFile(fileobj=archived) as a, gzip.GzipFile(fileobj=rebuilt) as b:
                        outcome = compare_streams(a, b)
                else:
                    outcome = compare_streams(archived, rebuilt)
                results[name] = outcome
    return results


def run_star(archive_dir: Path, core_run_dir: Path, *, timeout_seconds: int = 900) -> dict:
    archive_dir, core_run_dir = archive_dir.resolve(), core_run_dir.resolve()
    validate_private_star_destination(archive_dir, core_run_dir)
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    star_archive = archive_dir / STAR_ZIP
    original = immutable_original_star_source(star_archive)

    # Catch post-report modification of the earlier rebuilt core before using it.
    frozen_core_zip = archive_dir / SOURCE_CORE_ZIP
    compare_frozen_core_outputs(frozen_core_zip, core_run_dir)

    relocated_script = write_root_relocated_builder(original, core_run_dir)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    process = subprocess.run(
        [sys.executable, str(relocated_script)], cwd=core_run_dir,
        env=env, capture_output=True, text=True,
        check=False, timeout=timeout_seconds,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"Original archived star script exited {process.returncode}: "
            + (process.stderr + "\n" + process.stdout)[-2000:]
        )
    output = compare_original_star_outputs(star_archive, core_run_dir)
    summary_file = core_run_dir / "nba_player_game_at_risk_star_v1/qa_summary.json"
    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    mismatch = {
        field: {"observed": summary.get(field), "expected": expected}
        for field, expected in EXPECTED_QA_COUNTS.items()
        if summary.get(field) != expected
    }
    if mismatch:
        raise ValueError(f"Original star stage scientific QA counts differ: {mismatch}")
    report = {
        "status": "pass",
        "scope": "Rebuilt player-game core -> unchanged source-pinned original All-Star/All-NBA star logic. Official award lists inherited from source-coded history.",
        "original_star_zip_sha256": STAR_ZIP_SHA256,
        "original_star_builder_sha256": STAR_BUILDER_SHA256,
        "star_qa_counts": {name: summary[name] for name in EXPECTED_QA_COUNTS},
        "outputs": output,
        "all_twelve_star_outputs_exact": True,
        "manifest_comparison_excluded_due_to_gzip_header_nondeterminism": True,
        "historical_award_lists_independently_verified_against_nba_releases": False,
        "nba_cup_or_manuscript_enrichment_complete": False,
        "original_private_source_zip_modified": False,
    }
    (core_run_dir / "connected_star_reproduction_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", required=True, type=Path)
    p.add_argument("--core-run-dir", required=True, type=Path)
    p.add_argument("--timeout-seconds", type=int, default=900)
    args = p.parse_args()
    print(json.dumps(
        run_star(args.archive_dir, args.core_run_dir,
                 timeout_seconds=args.timeout_seconds), indent=2
    ))


if __name__ == "__main__":
    main()
