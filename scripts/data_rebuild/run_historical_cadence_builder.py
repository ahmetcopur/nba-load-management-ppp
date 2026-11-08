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
import time

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
# Original builder writes these eight files before the historical norm.sf error.
PRE_MODEL_OUTPUTS = [
    "harmonized_game_snapshot_map.csv",
    "harmonized_team_game_report_status.csv",
    "harmonized_selected_report_rows_all.csv.gz",
    "harmonized_unmatched_report_players.csv",
    "harmonized_selected_report_player_rows.csv.gz",
    "player_team_game_harmonized_cadence.csv.gz",
    "cadence_panel_counts_by_season.csv",
    "snapshot_selection_comparison.csv",
]
HISTORICAL_MODEL_CRASH = "AttributeError: 'function' object has no attribute 'sf'"

def check_pandas(version):
    if int(version.split(".")[0]) >= 3:
        raise SystemExit(f"pandas {version} changes historical object.fillna(False) behavior and corrupts the onset risk set. "
                         "Use requirements-builder-lock.txt (pandas 2.x)")

def accept_historical_exit(returncode, stderr, out, started):
    if returncode == 0:
        return "completed"
    final_lines = [line for line in stderr.strip().splitlines() if line.strip()][-1:]
    if final_lines != [HISTORICAL_MODEL_CRASH]:
        return None
    invalid = [name for name in PRE_MODEL_OUTPUTS
               if not (out / name).is_file() or
               (out / name).stat().st_mtime < started]
    if invalid:
        return None
    return "panel written; model section stopped at known historical norm.sf error"

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
    check_pandas(metadata.version("pandas"))
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
    env = dict(os.environ, OPENBLAS_NUM_THREADS="2", OMP_NUM_THREADS="2")
    started = time.time() - 1
    with tempfile.TemporaryDirectory(prefix="nba_cadence_builder_") as tmp:
        modified = Path(tmp) / SCRIPT.name
        modified.write_text(script)
        run = subprocess.run([sys.executable, str(modified)], env=env,
                             capture_output=True, text=True, cwd=str(root))
    print(run.stdout)
    print(run.stderr, file=sys.stderr)
    outcome = accept_historical_exit(run.returncode, run.stderr, out, started)
    if outcome is None:
        raise SystemExit(f"Historical cadence builder failed (exit {run.returncode}); see stderr above")
    provenance["builder_outcome"] = outcome
    (out / "replay_environment.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print("Historical outputs:", out, "|", outcome)

if __name__ == "__main__":
    main()
