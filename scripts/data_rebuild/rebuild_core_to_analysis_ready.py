#!/usr/bin/env python3
"""One-command historical selected-report -> core -> analysis-ready NBA rebuild.

Five original user-owned private source ZIPs stay outside the repository.
Executed stages do REAL computation, then compare generated CSV contents with
the frozen reference. Manual award/Cup/star metadata remain inherited, and
raw PDF extraction is not integrated into this command yet.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "scripts/data_rebuild"
REQUIRED_PRIVATE_ZIPS = (
    "nba_player_game_at_risk_core_v1.zip",
    "nba_player_crosswalk_final_v1.zip",
    "nba_boxscore_roster_frame_v2_output_upload.zip",
    "nba_game_covariates_v1.zip",
    "nba_player_game_analysis_ready_v1.zip",
)


def plan(archives: Path, output: Path, timeout: int = 900) -> tuple[list[str], list[str]]:
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
    archives = archives.resolve(strict=True)
    output = output.resolve()
    if not archives.is_dir():
        raise NotADirectoryError(f"Original package folder unavailable: {archives}")
    if output.exists():
        raise FileExistsError(f"Use a fresh output-root path; existing data stays untouched: {output}")
    if (archives == output or archives in output.parents
            or output in archives.parents):
        raise ValueError("Output must be a separate directory outside original archive tree")
    missing = [x for x in REQUIRED_PRIVATE_ZIPS if not (archives / x).is_file()]
    if missing:
        raise FileNotFoundError(f"Required original private ZIP packages absent: {missing}")
    core_output = output / "core_rebuild"
    analysis_output = output / "analysis_ready_rebuild"
    command1 = [
        sys.executable, str(TOOLS / "build_player_game_core_pipeline.py"),
        "--archive-dir", str(archives),
        "--output-dir", str(core_output),
        "--timeout", str(timeout),
    ]
    command2 = [
        sys.executable, str(TOOLS / "build_analysis_ready_from_generated_core.py"),
        "--generated-core", str(core_output / "nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz"),
        "--reviewed-source-zip", str(archives / "nba_player_game_analysis_ready_v1.zip"),
        "--output-dir", str(analysis_output),
    ]
    return command1, command2


def run(archives: Path, output: Path, timeout: int = 900):
    commands = plan(archives, output, timeout)
    output = output.resolve()
    output.mkdir(parents=True)
    for step, command in zip(("core", "analysis_ready"), commands):
        print(f"Building {step} stage from original historical source packages...", flush=True)
        subprocess.run(command, check=True, cwd=REPO, timeout=timeout)
    with (output / "core_rebuild/pipeline_rebuild_report.json").open() as stream:
        core = json.load(stream)
    with (output / "analysis_ready_rebuild/analysis_ready_rebuild_report.json").open() as stream:
        analysis = json.load(stream)
    if (not core["all_finalizer_outputs_exact_against_frozen_decoded_csv"]
            or not analysis["all_analysis_ready_outputs_match_original_decoded_csv"]):
        raise ValueError("Connected reconstruction finished without exact output equality")
    report = {
        "outcome": "COMPLETE_SELECTED_SOURCE_INTERMEDIATE_TO_ANALYSIS_READY",
        "original_packages_not_changed": True,
        "generated_player_game_rows": 248730,
        "generated_at_risk_rows": 180829,
        "core_output_decoded_csv_exact": True,
        "analysis_ready_output_decoded_csv_exact": True,
        "core_stage_report": "core_rebuild/pipeline_rebuild_report.json",
        "analysis_ready_stage_report": "analysis_ready_rebuild/analysis_ready_rebuild_report.json",
        "does_not_start_from_raw_pdf_files": True,
        "award_cup_star_human_reviewed_fields_still_inherited": True,
        "paper_regressions_not_run_by_this_entrypoint": True,
    }
    (output / "connected_rebuild_manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--timeout", type=int, default=900)
    args = p.parse_args()
    run(args.archive_dir, args.output_root, args.timeout)


if __name__ == "__main__":
    main()
