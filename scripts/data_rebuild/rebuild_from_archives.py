#!/usr/bin/env python3
"""Orchestrate a historical *intermediate-data* replay of the cadence panel.

This uses an existing canonical panel and archived intermediate CSVs. It does
not independently reconstruct NBA boxscore data, player awards, TV schedules
or pre-game covariates. Always validate against the frozen published output.
"""
import argparse
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts/data_rebuild"
FROZEN_PANEL = REPO / "data_intermediate/player_team_game_harmonized_cadence.csv.gz"
OUTPUT = REPO / "data_rebuild/output/historical_cadence/player_team_game_harmonized_cadence.csv.gz"


def call(name, args):
    cmd = [sys.executable, str(SCRIPTS / name), *map(str, args)]
    print("RUN:", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=REPO, check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", required=True, type=Path)
    p.add_argument("--historical-root", required=True, type=Path)
    p.add_argument("--skip-2025-parse", action="store_true",
                   help="Only if 2025 parsed rows were already independently checked")
    p.add_argument("--check-only", action="store_true",
                   help="Resolve/restore input files and check selected PDF presence; do not parse/build")
    p.add_argument("--reference", type=Path, default=FROZEN_PANEL)
    args = p.parse_args()

    call("restore_historical_layout.py",
         ["--archive-dir", args.archive_dir, "--historical-root", args.historical_root])

    if args.check_only:
        # On a clean checkout the 2025 parsed rows must not exist yet. Do NOT
        # call the builder preflight, which requires that future output.
        call("reparse_2025_selected.py",
             ["--historical-root", args.historical_root, "--check-only"])
        print("PASS: archive-member resolution and 2025 source coverage; no panel computed.")
        return

    if not args.skip_2025_parse:
        call("reparse_2025_selected.py", ["--historical-root", args.historical_root])

    call("run_historical_cadence_builder.py", ["--historical-root", args.historical_root])
    # Check row counts/uniqueness/at-risk/onsets independently from the original
    # script's own asserts, then check every cell against the frozen panel.
    call("verify_cadence_panel.py", ["--candidate", OUTPUT])
    call("compare_panels.py", ["--reference", args.reference, "--candidate", OUTPUT])
    print("PASS: archived-intermediate replay matches the frozen panel (strict CSV values).")


if __name__ == "__main__":
    main()
