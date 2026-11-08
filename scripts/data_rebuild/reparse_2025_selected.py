#!/usr/bin/env python3
"""Reparse 2025-26 cadence-selected reports using the archived parser/code.

Runs a temporary copy with only the historic ROOT path redirected. It requires
the original two 2025-26 injury PDF ZIPs and canonical selected-snapshot map.
"""
import argparse
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
ORIGINAL = REPO / "scripts/executed/06_cadence_harmonized_identification/parse_2025_selected.py"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historical-root", required=True, type=Path)
    p.add_argument("--check-only", action="store_true")
    a = p.parse_args()
    root = a.historical_root.resolve()
    required = [
        "cadence_work/selector/nba_canonical_snapshot_selector_v1/2025-26_game_snapshot_join_harmonized_canonical.csv",
        "cadence_core_full/nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py",
        "cadence_2025/audit_2025_26_upload.zip",
        "cadence_2025/audit_2025_26_targeted_upload.zip",
    ]
    missing = [str(root / r) for r in required if not (root / r).is_file()]
    if missing:
        raise SystemExit("Missing parser prerequisites:\n" + "\n".join(missing))
    original = ORIGINAL.read_text()
    pattern = r"^ROOT=Path\('/mnt/data/nba_continue'\)$"
    if len(re.findall(pattern, original, flags=re.MULTILINE)) != 1:
        raise RuntimeError("Original parser ROOT line changed, check before replay")
    if a.check_only:
        print("Parser prerequisites found. Original parser remains unchanged.")
        return
    modified = re.sub(pattern, lambda _: f"ROOT=Path({str(root)!r})", original,
                      count=1, flags=re.MULTILINE)
    # Keep execution outside the permanent project code; only redirected paths
    # differ. Original historical script may fail when archives or PDF layouts
    # differ, in which case a failed run is reported rather than hidden.
    with tempfile.TemporaryDirectory(prefix="nba_2025_cadence_") as tmp:
        executable = Path(tmp) / "parse_2025_selected.py"
        executable.write_text(modified)
        env = dict(os.environ, OPENBLAS_NUM_THREADS="2", OMP_NUM_THREADS="2")
        subprocess.run([sys.executable, str(executable)], cwd=root, env=env, check=True)
    output = root / "cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv"
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("2025 parser did not create expected selected report rows")
    print("2025-26 selected report rows generated:", output)

if __name__ == "__main__":
    main()
