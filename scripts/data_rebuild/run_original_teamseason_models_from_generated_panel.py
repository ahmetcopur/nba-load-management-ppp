#!/usr/bin/env python3
"""Execute original frozen August player + team-season FE models on a NEW core-derived risk panel.

The historical first-pass script and its archived reference output ZIP are
SHA-256-pinned. Only source-code filesystem paths (model input and output
directory) are redirected; the statistical estimator and controls are
unchanged. Complete tables of coefficient/SE/p/CI results must match the
original research within justified 1e-10 floating-point tolerance.

This is the August latest-pre-tip model stage; not the October harmonized
or full manuscript model suite. The generation of the input panel is
performed by the separate original-PDF/core/analysis-ready pipeline.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import numpy as np
import pandas as pd

HISTORICAL_PACKAGE = (
    Path(__file__).resolve().parents[2] / "packages" / "02_first_pass_models.zip"
)
PACKAGE_SHA256 = "79682a44dab8f00e448a40772f11c2ed6d29f95ab893b1492068d8853a184ac2"
SOURCE_CODE_MEMBER = (
    "nba_policy_models_first_pass_v1/scripts/run_teamseason_fixed_effects.py"
)
SOURCE_CODE_SHA256 = "7fd6983fb1ce58469ae175a6702cf7ef667c57afa4583a32073bb7f7469d65d3"
SOURCE_PANEL_SHA256 = "d6e82ba61d99fb27ec4877b1c0b05fed76c5cb8fa4bf5b6322742b7049ae9635"
REFERENCE_PREFIX = "nba_policy_models_first_pass_v1/"
OUTPUT_NAMES = {
    "teamseason_fe_focal.csv": ["outcome"],
    "teamseason_fe_coefficients.csv": ["outcome", "term"],
}
OLD_INPUT = "D='/mnt/data/nba_player_game_analysis_ready_v1/player_game_panel_model_at_risk_analysis_ready.csv.gz'"
OLD_OUTPUT = "out=Path('/mnt/data/_model_run')"
MODEL_TOL = 1e-10


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def decoded_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for data in iter(lambda: stream.read(1048576), b""):
            h.update(data)
    return h.hexdigest()


def unique_member(archive: ZipFile, name: str) -> bytes:
    if archive.namelist().count(name) != 1:
        raise ValueError(f"Original model package member missing or duplicated: {name}")
    return archive.read(name)


def validate_private_result_path(output_dir: Path, repo_root: Path) -> None:
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing original model output: {output_dir}")
    if output_dir == repo_root or repo_root in output_dir.parents:
        raise ValueError("Private model rerun output must be outside the Git repository")
    if any((p / ".git").exists() for p in (output_dir, *output_dir.parents)):
        raise ValueError("Private modeling input/output cannot be stored inside another Git checkout")


def stage_source(model_package: Path, panel: Path,
                 output: Path) -> tuple[Path, bytes]:
    if sha256_file(model_package) != PACKAGE_SHA256:
        raise ValueError("Historical original first-pass model ZIP SHA-256 differs")
    with ZipFile(model_package) as archive:
        code = unique_member(archive, SOURCE_CODE_MEMBER)
    if hashlib.sha256(code).hexdigest() != SOURCE_CODE_SHA256:
        raise ValueError("Original executed team-season fixed-effects source code SHA differs")
    text = code.decode("utf-8")
    if text.count(OLD_INPUT) != 1 or text.count(OLD_OUTPUT) != 1:
        raise ValueError("Original model source path substitutions unsafe or no longer unique")
    changed = text.replace(OLD_INPUT, "D=" + repr(str(panel)), 1)
    changed = changed.replace(OLD_OUTPUT, "out=Path(" + repr(str(output)) + ")", 1)
    runner = output / "original_teamseason_FE_relocated_paths_only.py"
    runner.write_text(changed, encoding="utf-8")
    return runner, code


def compare_model_outputs(original: pd.DataFrame,
                          recomputed: pd.DataFrame,
                          keys: list[str]) -> dict:
    if list(original.columns) != list(recomputed.columns):
        raise ValueError("Original model table schema/order differs")
    if len(original) != len(recomputed) or not len(original):
        raise ValueError("Original model table row cardinality differs")
    if original.duplicated(keys).any() or recomputed.duplicated(keys).any():
        raise ValueError("Original model term/outcome identities duplicate")
    merged = original.merge(
        recomputed, on=keys, how="outer",
        suffixes=("_orig", "_new"), validate="one_to_one", indicator=True,
    )
    if not merged._merge.eq("both").all():
        raise ValueError("Original model outcome or coefficient identities differ")
    maxdiff = 0.0
    for field in original.columns:
        if field in keys:
            continue
        a, b = merged[field + "_orig"], merged[field + "_new"]
        na, nb = pd.to_numeric(a, errors="coerce"), pd.to_numeric(b, errors="coerce")
        if na.notna().all() and nb.notna().all():
            diff = float((na - nb).abs().max())
            if not np.isfinite(diff) or diff > MODEL_TOL:
                raise ValueError(f"Original model estimate/inference differs: {field} max {diff}")
            maxdiff = max(diff, maxdiff)
        elif not a.fillna("NULL").astype(str).equals(b.fillna("NULL").astype(str)):
            raise ValueError(f"Original model non-numeric field differs: {field}")
    return {"rows": len(original), "compared_columns": len(original.columns),
            "maximum_absolute_numeric_difference": maxdiff,
            "all_original_coefficient_inference_cells_match": True,
            "numerical_tolerance": MODEL_TOL}


def run(panel: Path, output: Path, *,
        model_package: Path = HISTORICAL_PACKAGE, timeout_seconds: int = 1800) -> dict:
    panel, output, model_package = panel.resolve(), output.resolve(), model_package.resolve()
    if timeout_seconds <= 0:
        raise ValueError("Original model timeout must be positive")
    if not panel.is_file():
        raise FileNotFoundError(f"Original source-rebuilt analysis-ready model input missing: {panel}")
    if not model_package.is_file():
        raise FileNotFoundError(f"Immutable original model package unavailable: {model_package}")
    validate_private_result_path(output, Path(__file__).resolve().parents[2])
    if decoded_sha256(panel) != SOURCE_PANEL_SHA256:
        raise ValueError("Original source-derived risk panel does not match pinned reviewed input")
    if sha256_file(model_package) != PACKAGE_SHA256:
        raise ValueError("Original first-pass package ZIP SHA-256 differs")
    output.mkdir(parents=True, exist_ok=False)
    runner, code = stage_source(model_package, panel, output)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    process = subprocess.run(
        [sys.executable, str(runner)], cwd=output,
        capture_output=True, text=True, timeout=timeout_seconds, env=env,
    )
    if process.returncode != 0:
        raise RuntimeError(f"Original source model execution failed ({process.returncode}): "
                           + (process.stderr + "\n" + process.stdout)[-1600:])
    comparisons = {}
    focal = None
    with ZipFile(model_package) as archive:
        for filename, keys in OUTPUT_NAMES.items():
            original = pd.read_csv(io.BytesIO(
                unique_member(archive, REFERENCE_PREFIX + filename)))
            observed = pd.read_csv(output / filename)
            comparisons[filename] = compare_model_outputs(original, observed, keys)
            if filename == "teamseason_fe_focal.csv":
                focal = observed[[
                    "outcome", "n", "estimate", "se", "p", "low", "high"
                ]].to_dict("records")
    report = {
        "status": "pass",
        "scope": "Fresh source-generated reviewed 180,829-row at-risk panel -> unchanged original August player + team-season FE original models only, not all manuscript specifications",
        "historical_model_package_sha256": PACKAGE_SHA256,
        "original_executed_model_source_sha256": SOURCE_CODE_SHA256,
        "input_analysis_ready_panel_decoded_sha256": SOURCE_PANEL_SHA256,
        "models": comparisons,
        "focal": focal,
        "all_original_model_estimate_and_uncertainty_tables_reproduced": True,
        "original_model_code_changed_except_path_substitution": False,
        "historical_frozen_outputs_modified": False,
    }
    (output / "reproduction_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--generated-model-panel", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--historical-model-package", type=Path,
                   default=HISTORICAL_PACKAGE)
    p.add_argument("--timeout-seconds", type=int, default=1800)
    a = p.parse_args()
    print(json.dumps(
        run(a.generated_model_panel, a.output_dir,
            model_package=a.historical_model_package,
            timeout_seconds=a.timeout_seconds), indent=2))


if __name__ == "__main__":
    main()
