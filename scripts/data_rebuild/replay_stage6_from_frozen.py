#!/usr/bin/env python3
"""Independently rerun archived Stage-6 models on the *frozen* player-game panel.

This verifies the statistical computation conditional on the already-published
October cadence panel. It is NOT a raw-source-to-panel reproduction.
The historical executable logic is copied without changes except ROOT's path.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import version

from compare_stage6_models import archived_rows, candidate_rows, compare

REPO = Path(__file__).resolve().parents[2]
ORIGINAL = REPO / "scripts/executed/06_cadence_harmonized_identification/run_cadence_models_fast.py"
FROZEN = REPO / "data_intermediate/player_team_game_harmonized_cadence.csv.gz"
ARCHIVE = REPO / "packages/06_cadence_harmonized_identification.zip"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, default=FROZEN)
    parser.add_argument("--reference-zip", type=Path, default=ARCHIVE)
    parser.add_argument("--output-dir", type=Path,
                        default=REPO / "data_rebuild/output/stage6_replay")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be a positive number of seconds")
    src = ORIGINAL.read_text(encoding="utf-8")
    line = "ROOT=Path('/mnt/data/nba_continue'); OUT=ROOT/'cadence_harmonized_results'"
    if src.count(line) != 1:
        raise RuntimeError("Historical Stage-6 runner root path has changed; inspect before replay")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nba_stage6_model_replay_") as temp:
        root = Path(temp).resolve()
        stage6 = root / "cadence_harmonized_results"
        stage6.mkdir()
        input_copy = stage6 / "player_team_game_harmonized_cadence.csv.gz"
        shutil.copy2(args.panel, input_copy)
        if digest(args.panel) != digest(input_copy):
            raise RuntimeError("Frozen panel SHA-256 changed during staging")
        # The only source change is the historical machine's hardcoded root.
        patched = src.replace(line,
            "ROOT=Path(" + repr(str(root)) + "); OUT=ROOT/'cadence_harmonized_results'")
        script = root / "run_cadence_models_fast.py"
        script.write_text(patched, encoding="utf-8")
        environment = {**os.environ, "OPENBLAS_NUM_THREADS": "1",
                       "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
        command = [sys.executable, str(script)]
        try:
            result = subprocess.run(command, cwd=root, env=environment,
                                    capture_output=True, text=True, check=True,
                                    timeout=args.timeout)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout or "", file=sys.stderr)
            print(exc.stderr or "", file=sys.stderr)
            raise
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        produced = stage6 / "cadence_harmonized_model_results.csv"
        if not produced.is_file():
            raise RuntimeError("Original Stage-6 script finished without model result CSV")
        target = output / "cadence_harmonized_model_results.csv"
        shutil.copy2(produced, target)
    verdict = compare(archived_rows(args.reference_zip), candidate_rows(target),
                      pp_tol=0.001, p_tol=0.001)
    provenance = {
        "experiment": "frozen-panel-to-Stage-6-models",
        "not_reproduced": "raw-source-to-player-game panel",
        "original_executable_sha256": digest(ORIGINAL),
        "frozen_input_sha256": digest(args.panel),
        "archived_reference_sha256": digest(args.reference_zip),
        "python": sys.version,
        "numpy_version": version("numpy"),
        "pandas_version": version("pandas"),
        "statsmodels_version": version("statsmodels"),
        "scipy_version": version("scipy"),
        "environment_threads": "1",
        "acceptance": verdict,
    }
    (output / "replay_verification.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps({"matched": verdict["matched"],
                      "models": verdict["model_specifications"],
                      "errors": verdict["errors"],
                      "output": str(target)}, indent=2))
    if not verdict["matched"]:
        raise SystemExit("Replayed Stage-6 models differ from historical archive; see replay_verification.json")


if __name__ == "__main__":
    main()
