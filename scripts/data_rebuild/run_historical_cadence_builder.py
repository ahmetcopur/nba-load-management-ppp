#!/usr/bin/env python3
"""Replay the original cadence builder using restored historical input folders.

Creates a temporary copy with ONLY hardcoded input/output paths redirected;
all scientific computation remains in the original executed script.
"""
from pathlib import Path
import argparse
import hashlib
from importlib import metadata
import json
import os
import platform
import re
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/executed/06_cadence_harmonized_identification/build_harmonized_panel_and_models.py"
NEEDED = [
    "analysis/nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz",
    "cadence_2025/player_crosswalk_final.csv",
    "cadence_work/selector/nba_canonical_snapshot_selector_v1",
    "cadence_work/s4/2022-23/team_game_final_pre_tip_status_harmonized.csv",
    "cadence_work/s4/2023-24/team_game_final_pre_tip_status_harmonized.csv",
    "cadence_work/season_parsed/2020-21/s1_snapshot_rows_corrected.csv",
    "cadence_work/season_parsed/2021-22/s1_snapshot_rows_harmonized.csv",
    "cadence_work/season_parsed/2022-23/s1_snapshot_rows_regular_season.csv",
    "cadence_work/season_parsed/2023-24/audit_2023_24_pre_s4_outputs/s1_snapshot_rows_regular_season.csv",
    "cadence_work/season_parsed/2024-25/s1_snapshot_rows_regular_season_real.csv",
    "cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv",
    "cadence_work/player_alias_table.csv",
    "cadence_work/selector/nba_canonical_snapshot_selector_v1/2025-26_game_snapshot_join_harmonized_canonical.csv",
]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historical-root", required=True, type=Path)
    p.add_argument("--output", type=Path, default=REPO / "data_rebuild/output/historical_cadence")
    p.add_argument("--check-only", action="store_true")
    a = p.parse_args()
    root = a.historical_root.resolve()
    missing = [str(root / name) for name in NEEDED if not (root / name).exists()]
    if missing:
        print("Missing upstream inputs:", file=sys.stderr)
        print("\n".join(" - " + path for path in missing), file=sys.stderr)
        raise SystemExit(2)
    script = SCRIPT.read_text()
    root_pattern = r"^ROOT=Path\('/mnt/data/nba_continue'\)$"
    out_pattern = r"^OUT=ROOT/'cadence_harmonized_results'; OUT.mkdir\(exist_ok=True\)$"
    if len(re.findall(root_pattern, script, re.M)) != 1 or len(re.findall(out_pattern, script, re.M)) != 1:
        raise RuntimeError("Original paths changed; inspect builder before executing")
    if a.check_only:
        print("All historical season parse and basic builder prerequisites found.")
        return
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    script = re.sub(root_pattern, lambda _: "ROOT=Path(" + repr(str(root)) + ")", script, count=1, flags=re.M)
    script = re.sub(out_pattern, lambda _: "OUT=Path(" + repr(str(out)) + "); OUT.mkdir(parents=True,exist_ok=True)",
                    script, count=1, flags=re.M)
    packages = ("numpy", "pandas", "scipy", "statsmodels", "scikit-learn",
                "pdfplumber", "pymupdf")
    versions = {}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = None
    provenance = {
        "historical_executed_builder_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        "python": sys.version,
        "platform": platform.platform(),
        "package_versions": versions,
        "input_root": str(root),
        "output": str(out),
        "thread_settings": {"OPENBLAS_NUM_THREADS": "2", "OMP_NUM_THREADS": "2"},
        "warning": "Historical replay uses upstream intermediate data, not raw source reconstruction."
    }
    (out / "replay_environment.json").write_text(json.dumps(provenance, indent=2) + "\n")
    env = dict(os.environ, OPENBLAS_NUM_THREADS="2", OMP_NUM_THREADS="2")
    with tempfile.TemporaryDirectory(prefix="nba_cadence_builder_") as tmp:
        modified = Path(tmp) / SCRIPT.name
        modified.write_text(script)
        subprocess.run([sys.executable, str(modified)], env=env, check=True, cwd=str(root))
    print("Historical outputs:", out)

if __name__ == "__main__":
    main()
