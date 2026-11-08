#!/usr/bin/env python3
"""One-command archive-to-cadence-panel historical replay.

Rebuilds *from original archived intermediate outputs*, not directly from the
raw PDF and boxscore payloads. Recomputes the 2025-26 selected report parses
from PDFs and runs the historical cadence builder; compares with frozen output.
Exit nonzero on any mismatch. Never modifies frozen reference data.
"""
import argparse
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts/data_rebuild"

def call(name, args):
    cmd = [sys.executable, str(SCRIPTS / name), *map(str, args)]
    print("RUN:", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=REPO, check=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", required=True, type=Path,
                   help="Directory of restored original historical source ZIPs")
    p.add_argument("--historical-root", required=True, type=Path,
                   help="Local output folder (e.g. ./data_rebuild/output/nba_continue)")
    p.add_argument("--skip-2025-parse", action="store_true",
                   help="Use an existing independently verified 2025 parsed-row CSV")
    p.add_argument("--check-only", action="store_true",
                   help="Restore inputs and check parser/builder prerequisites only")
    p.add_argument("--reference", type=Path,
                   default=REPO / "data_intermediate/player_team_game_harmonized_cadence.csv.gz")
    a = p.parse_args()
    call("restore_historical_layout.py",
         ["--archive-dir", a.archive_dir, "--historical-root", a.historical_root])
    if not a.skip_2025_parse:
        call("reparse_2025_selected.py",
             ["--historical-root", a.historical_root,
              *(["--check-only"] if a.check_only else [])])
    if a.check_only:
        call("run_historical_cadence_builder.py",
             ["--historical-root", a.historical_root, "--check-only"])
        print("Prerequisite checks passed; model and panel not yet rebuilt.")
        return
    call("run_historical_cadence_builder.py", ["--historical-root", a.historical_root])
    output = REPO / "data_rebuild/output/historical_cadence/player_team_game_harmonized_cadence.csv.gz"
    call("compare_panels.py", ["--reference", a.reference, "--candidate", output])
    print("PASS: reconstructed panel exactly matches the frozen reference CSV.")

if __name__ == "__main__":
    main()
