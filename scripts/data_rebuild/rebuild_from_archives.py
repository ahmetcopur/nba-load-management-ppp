#!/usr/bin/env python3
"""Replay a historical NBA cadence panel from archived intermediate sources.

This is NOT raw-boxscore-to-canonical-panel reconstruction. Fail on any
restoration, parsing, building, or frozen-panel comparison error.
"""
import argparse
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "scripts/data_rebuild"
DEFAULT_OUT = REPO / "data_rebuild/output/historical_cadence"


def call(name, args):
    command = [sys.executable, str(TOOLS / name), *map(str, args)]
    print("RUN:", " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT,
                        help="Separate, ignored directory for rebuilt panel and model outputs")
    parser.add_argument("--reference", type=Path,
                        default=REPO / "data_intermediate/player_team_game_harmonized_cadence.csv.gz")
    parser.add_argument("--skip-stage6-model-comparison", action="store_true",
                        help="Explicitly skip historical Stage-6 coefficient validation")
    parser.add_argument("--skip-2025-parse", action="store_true",
                        help="Requires a previously independently verified 2025 parsed-row CSV")
    parser.add_argument("--check-only", action="store_true",
                        help="Check ZIP archive member mappings without writing/executing anything")
    args = parser.parse_args()
    restore_args = ["--archive-dir", args.archive_dir,
                    "--historical-root", args.historical_root]
    if args.check_only:
        call("restore_historical_layout.py", [*restore_args, "--check-only"])
        print("Archive layout inspected. No files written, PDFs parsed or models run.")
        return
    call("restore_historical_layout.py", restore_args)
    if args.skip_2025_parse:
        existing = (args.historical_root /
                    "cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv")
        if not existing.is_file():
            raise SystemExit(f"--skip-2025-parse requires a verified existing file: {existing}")
    else:
        call("reparse_2025_selected.py", ["--historical-root", args.historical_root])
    call("run_historical_cadence_builder.py",
         ["--historical-root", args.historical_root, "--output", args.output])
    candidate = args.output / "player_team_game_harmonized_cadence.csv.gz"
    call("compare_panels.py", ["--reference", args.reference, "--candidate", candidate,
                              "--output", args.output / "panel_comparison.json"])
    call("validate_cadence_panel.py", ["--panel", candidate, "--expect-frozen",
                                     "--output", args.output / "panel_invariants.json"])
    if not args.skip_stage6_model_comparison:
        call("compare_stage6_models.py",
             ["--candidate", args.output / "cadence_harmonized_model_results.csv",
              "--output", args.output / "stage6_model_comparison.json"])
    print("PASS: historical intermediate replay matches frozen panel"
          + (" (historical Stage-6 model check skipped)." if args.skip_stage6_model_comparison
             else " and archived Stage-6 coefficients."))


if __name__ == "__main__":
    main()
