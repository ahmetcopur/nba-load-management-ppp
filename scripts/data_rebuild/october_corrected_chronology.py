#!/usr/bin/env python3
"""Replay the ten original October scripts on frozen and corrected-chronology panels.

The immutable shared repository supplies executed October scripts and archived
reference outputs. First establish exact numerical frozen-output reproduction;
only then compare the corrected-chronology sensitivity. Do not modify originals.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import pandas as pd

SHARED_COMMIT = "0bd713d97e8d519df5700ef473da34aba4495223"
SCRIPTS = ("run_base", "run_event", "run_placebo", "run_home", "run_home_extra",
           "run_timing", "run_event_window_harmonized", "run_event_window_legacy",
           "audit_models", "audit_cluster")
PANEL = "data_intermediate/player_team_game_harmonized_cadence.csv.gz"
FROZEN_SHA256 = "5483fc07465b84b20d29f54f0c49da53bef367cba712ad174111f3a7a794d8cd"
CORRECTED_CSV_SHA256 = "2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67"
RENAMED = {
    "event_window_joint_tests_linear.csv": "event_window_joint_tests.csv",
    "event_window_joint_tests_national_partner.csv": "event_window_joint_tests.csv",
}
EVENT_WINDOW_TV = {
    "event_window_joint_tests_linear.csv": "tv_harmonized_linear",
    "event_window_joint_tests_national_partner.csv": "announced_tv_primary",
}
NUMERICAL_TOLERANCE = 1e-9
EXPECTED_ARCHIVED_OUTPUTS = 33
EXPECTED_SENSITIVITY_ROWS = 704


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_gzip_payload(path: Path) -> str:
    h = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_shared_commit(shared: Path) -> None:
    result = subprocess.run(["git", "-C", str(shared), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True)
    if result.stdout.strip() != SHARED_COMMIT:
        raise RuntimeError(f"Shared Oct source is {result.stdout.strip()}, not {SHARED_COMMIT}")
    status = subprocess.run(["git", "-C", str(shared), "status", "--porcelain"],
                            capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise RuntimeError("Shared Oct checkout has local modifications; use clean pinned source")
    if digest_file(shared / PANEL) != FROZEN_SHA256:
        raise RuntimeError("Shared Oct frozen cadence panel SHA-256 mismatch")
    for name in SCRIPTS:
        if not (shared / "scripts/october_2026" / f"{name}.py").is_file():
            raise FileNotFoundError(f"Missing released October script: {name}")


def prepare(shared: Path, folder: Path, panel: Path | None) -> None:
    if folder.exists():
        raise FileExistsError(f"Replay folder must be new: {folder}")
    folder.mkdir(parents=True)
    for part in ("scripts/october_2026", "data_intermediate", "data_final",
                 "results/october_2026/archive", "results/october_2026/audit_archive"):
        shutil.copytree(shared / part, folder / part, symlinks=False)
    if panel is not None:
        shutil.copy2(panel, folder / PANEL)


def run_all(folder: Path, executable: str) -> None:
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "2", "OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2"}
    for name in SCRIPTS:
        with (folder / f"{name}.log").open("w") as log:
            code = subprocess.run([executable, f"scripts/october_2026/{name}.py"],
                                  cwd=folder, env=env, stdout=log,
                                  stderr=subprocess.STDOUT).returncode
        if code:
            raise RuntimeError(f"{name}.py exited {code}; see {folder / (name+'.log')}")


def outputs(folder: Path) -> dict[str, Path]:
    base = folder / "results/october_2026/recomputed"
    return {path.relative_to(base).as_posix(): path for path in base.rglob("*.csv")}


def compare_tables(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    """Check numeric, boolean, text and missing cells, including mixed columns."""
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return {"same_shape": False, "max_abs_numeric_difference": None,
                "differing_text_cells": None}
    worst, text = 0.0, 0
    for col in a.columns:
        if col == "seconds":
            continue
        left, right = a[col], b[col]
        if pd.api.types.is_bool_dtype(left) or pd.api.types.is_bool_dtype(right):
            eq = (left.astype("string").eq(right.astype("string"))
                  | (left.isna() & right.isna())).fillna(False)
            text += int((~eq).sum())
            continue
        x, y = pd.to_numeric(left, errors="coerce"), pd.to_numeric(right, errors="coerce")
        numeric = x.notna() & y.notna()
        if numeric.any():
            worst = max(worst, float((x[numeric] - y[numeric]).abs().max()))
        both_missing = left.isna() & right.isna()
        unmatched = ~numeric & ~both_missing
        ltxt, rtxt = left.fillna("").astype(str), right.fillna("").astype(str)
        text += int((unmatched & (ltxt.ne(rtxt) | left.isna().ne(right.isna()))).sum())
    return {"same_shape": True, "max_abs_numeric_difference": worst,
            "differing_text_cells": text}


def reproduction(frozen: Path) -> dict[str, dict]:
    report = {}
    for rel, path in sorted(outputs(frozen).items()):
        name = Path(rel).name
        sub = "audit_archive" if rel.startswith("audit/") else "archive"
        reference = frozen / "results/october_2026" / sub / RENAMED.get(name, name)
        if not reference.is_file():
            report[rel] = {"archived": False}
            continue
        archived = pd.read_csv(reference)
        if name in EVENT_WINDOW_TV:
            archived = (archived[archived.tv.eq(EVENT_WINDOW_TV[name])]
                        .rename(columns={"n_before_control_drop": "n"}).reset_index(drop=True))
        report[rel] = {"archived": True, **compare_tables(archived, pd.read_csv(path))}
    return report


def require_reproduction(report: dict, tolerance=NUMERICAL_TOLERANCE) -> None:
    if len(report) != EXPECTED_ARCHIVED_OUTPUTS:
        raise RuntimeError(f"Expected {EXPECTED_ARCHIVED_OUTPUTS} October archived output comparisons, got {len(report)}")
    errors = {name: result for name, result in report.items()
              if not result.get("archived") or not result.get("same_shape")
              or result.get("differing_text_cells")
              or result.get("max_abs_numeric_difference", float("inf")) > tolerance}
    if errors:
        raise RuntimeError("Frozen October release does not reproduce archived tables: " + repr(errors))


def sensitivity(frozen: Path, corrected: Path) -> pd.DataFrame:
    before, after = outputs(frozen), outputs(corrected)
    if set(before) != set(after):
        raise RuntimeError(f"Frozen and corrected October output files differ: {sorted(set(before)^set(after))}")
    rows = []
    for rel in sorted(before):
        a, b = pd.read_csv(before[rel]), pd.read_csv(after[rel])
        est = next((col for col in ("estimate_pp", "coef_pp") if col in a.columns), None)
        label = next((col for col in ("term", "name") if col in a.columns), None)
        if est is None or label is None:
            continue
        if est not in b or label not in b or a[label].duplicated().any() or b[label].duplicated().any():
            raise RuntimeError(f"{rel}: estimate schema mismatch or duplicate row labels")
        joint = a.merge(b, on=label, how="outer", suffixes=("_f", "_c"),
                        indicator=True, validate="one_to_one")
        for record in joint.to_dict("records"):
            swap = record["_merge"] != "both"
            if swap and record[label] not in ("games_before_10", "dist65_10"):
                raise RuntimeError(f"{rel}: term {record[label]} present in only one run")
            value = lambda field, side: record.get(f"{field}_{side}", np.nan)
            ncol = "n" if "n" in a.columns else "N"
            rows.append({
                "file": rel, "row": record[label], "collinear_swap": swap,
                "estimate_frozen": value(est, "f"),
                "estimate_corrected": value(est, "c"),
                "change": np.nan if swap else value(est, "c")-value(est, "f"),
                "se_frozen": value("se_pp", "f"),
                "p_frozen": value("p", "f"), "p_corrected": value("p", "c"),
                "n_frozen": value(ncol, "f"), "n_corrected": value(ncol, "c"),
            })
    return pd.DataFrame(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--shared-repo", type=Path, required=True)
    p.add_argument("--corrected-panel", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--python", default=sys.executable)
    args = p.parse_args()
    shared, panel, work = args.shared_repo.resolve(), args.corrected_panel.resolve(), args.work.resolve()
    if not panel.is_file():
        raise FileNotFoundError(panel)
    if shared == work or shared in work.parents or work in shared.parents or work == panel.parent or work in panel.parents:
        raise RuntimeError("Replay output overlaps original source repository or corrected panel")
    verify_shared_commit(shared)
    actual = digest_gzip_payload(panel)
    if actual != CORRECTED_CSV_SHA256:
        raise RuntimeError(f"Corrected chronology decompressed panel hash mismatch: {actual}")
    frozen, corrected = work / "frozen", work / "corrected"
    prepare(shared, frozen, None)
    prepare(shared, corrected, panel)
    run_all(frozen, args.python)
    reproduced = reproduction(frozen)
    require_reproduction(reproduced)
    run_all(corrected, args.python)
    models = sensitivity(frozen, corrected)
    if len(models) != EXPECTED_SENSITIVITY_ROWS:
        raise RuntimeError(f"Expected {EXPECTED_SENSITIVITY_ROWS} October coefficient rows, got {len(models)}")
    models.to_csv(work / "october_corrected_vs_frozen.csv", index=False)
    shifts = models[(models.n_frozen.notna()) & (models.n_corrected.notna()) &
                    (models.n_frozen != models.n_corrected)]
    report = {
        "scope": "Separate corrected-chronology October sensitivity; historical inputs unchanged",
        "shared_source_commit": SHARED_COMMIT,
        "frozen_panel_sha256": FROZEN_SHA256,
        "corrected_panel_gzip_sha256": digest_file(panel),
        "corrected_panel_uncompressed_sha256": actual,
        "reproduction_passed": True,
        "reproduction_files_compared": len(reproduced),
        "reproduction_max_abs_numeric_difference":
            max(result["max_abs_numeric_difference"] for result in reproduced.values()),
        "reproduction_detail": reproduced,
        "sensitivity_rows": len(models),
        "sensitivity_max_abs_change": float(models.change.abs().max()),
        "sensitivity_collinear_swaps": models.loc[models.collinear_swap, ["file","row"]].to_dict("records"),
        "event_window_sample_changes": shifts[["file", "row", "n_frozen", "n_corrected"]].to_dict("records"),
        "note": "Main model N unchanged; selected event-window model samples shrink after chronology correction.",
    }
    (work / "october_corrected_chronology.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report.items()
                      if k not in ("reproduction_detail", "event_window_sample_changes")}, indent=2))


if __name__ == "__main__":
    main()
