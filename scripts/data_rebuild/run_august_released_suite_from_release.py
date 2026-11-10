#!/usr/bin/env python3
"""Rerun the remaining released August scripts, frozen first, then corrected.

Stages (original executed scripts in scripts/executed at shared commit 0bd713d):
  first_pass   02_first_pass_models: baseline and robustness models,
               category decomposition, season event study, team-season FE.
  tv_audit     04_tv_audit_continuation: TV-definition models, source counts,
               event study, joint pretrend, fake-date placebos.
  stage2       05_identification_falsification_stage2: standard/COVID and
               clustering sensitivity, sparse exact player linear trends,
               99-draw stratified TV permutation placebos.

The executed scripts hard-code /mnt/data. Each copy changes only that root to
a fresh sandbox, and the inputs are placed at the historical relative paths.
(The scripts/portable copies are not used: they also drop the exactly
collinear dist65_10 control, which changes the permutation placebo
numerically.) The frozen rerun must match every archived package table (exact
text and counts, coefficients within 1e-7, inference columns within 1e-3)
before the corrected panel is run. The corrected run repairs only the two
February 2022 Toronto TV lookup keys in its copy. Original files stay read-only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

import numpy as np
import pandas as pd

from run_august_category_fdr_from_release import (
    SHARED_SHA, PANEL, TV, sha, repair_announcement_fixture_keys,
)

ORIGINAL_RISK_SHA = "d6e82ba61d99fb27ec4877b1c0b05fed76c5cb8fa4bf5b6322742b7049ae9635"
CORRECTED_RISK_SHA = "5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3"
PORTABLE = Path("scripts/portable")
EXECUTED = Path("scripts/executed")
HISTORICAL_ROOT = "/mnt/data"
SANDBOX = "mnt_data"
RISK = "player_game_panel_model_at_risk_analysis_ready.csv.gz"
PANEL_LOCATIONS = [
    f"nba_player_game_analysis_ready_v1/{RISK}",
    f"nba_continue/analysis/nba_player_game_analysis_ready_v1/{RISK}",
    f"nba_continue/analysis_unpack/nba_player_game_analysis_ready_v1/{RISK}",
]
TV_LOCATION = "nba_continue/tv/nba_announced_tv_six_seasons_v1/announced_tv_six_seasons.csv"
OUTPUT_DIRS = ["_model_run", "nba_continue/tv_audit_results",
               "nba_continue/identification_stage2_results"]
M = f"{SANDBOX}/_model_run/"
T = f"{SANDBOX}/nba_continue/tv_audit_results/"
I = f"{SANDBOX}/nba_continue/identification_stage2_results/"
FIRST = "nba_policy_models_first_pass_v1/"
TVA = "tv_audit_results/"
S2 = "nba_identification_falsification_stage2_v1/results/"

# output path -> (archived member, key columns). An empty key aligns by row.
STAGES = {
    "first_pass": {
        "package": "packages/02_first_pass_models.zip",
        "executed": "02_first_pass_models",
        "scripts": ["run_baseline_and_robustness_models.py",
                    "run_category_decomposition.py",
                    "run_season_event_study.py",
                    "run_teamseason_fixed_effects.py"],
        "outputs": {
            M + "all_model_coefficients.csv":
                (FIRST + "all_model_coefficients.csv", ["model", "term"]),
            M + "focal_triple_interaction_results.csv":
                (FIRST + "focal_triple_interaction_results.csv", ["model"]),
            M + "raw_policy_cells.csv":
                (FIRST + "raw_policy_cells.csv",
                 ["star_PPP_it", "postPPP", "announced_tv_primary"]),
            M + "raw_ddd.json": (FIRST + "raw_ddd.json", None),
            M + "category_models_coefficients.csv":
                (FIRST + "category_models_coefficients.csv", ["outcome", "term"]),
            M + "category_models_focal.csv":
                (FIRST + "category_models_focal.csv", ["outcome"]),
            M + "season_event_study_absence.csv":
                (FIRST + "season_event_study_absence.csv", ["season"]),
            M + "season_event_study_all_coefficients.csv":
                (FIRST + "season_event_study_all_coefficients.csv", ["term"]),
            M + "teamseason_fe_coefficients.csv":
                (FIRST + "teamseason_fe_coefficients.csv", ["outcome", "term"]),
            M + "teamseason_fe_focal.csv":
                (FIRST + "teamseason_fe_focal.csv", ["outcome"]),
        },
    },
    "tv_audit": {
        "package": "packages/04_tv_audit_continuation.zip",
        "executed": "04_tv_audit_continuation",
        # run_tv_linear_check.py only prints, so it is not rerun.
        "scripts": ["run_tv_audit_fast.py", "run_identification_checks.py"],
        "outputs": {
            T + "tv_model_results.csv": (TVA + "tv_model_results.csv", ["label"]),
            T + "tv_source_counts.csv": (TVA + "tv_source_counts.csv", ["season"]),
            T + "event_study_tv_definitions.csv":
                (TVA + "event_study_tv_definitions.csv", ["definition", "season"]),
            T + "joint_pretrend_tests.csv":
                (TVA + "joint_pretrend_tests.csv", ["definition"]),
            T + "preperiod_placebo_policy_dates.csv":
                (TVA + "preperiod_placebo_policy_dates.csv", ["definition", "fake_start"]),
        },
    },
    "stage2": {
        "package": "packages/05_identification_falsification_stage2.zip",
        "executed": "05_identification_falsification_stage2",
        # The two permutation scripts write the same summary file name, so
        # each runs in its own sandbox and the summaries are combined.
        "scripts": ["run_standard_clustering_and_iterative_trends.py",
                    "run_player_trends_sparse_exact.py"],
        "separate": ["run_permutation_legacy_99.py",
                     "run_permutation_harmonized_99.py"],
        "outputs": {
            I + "standard_and_covid_sensitivity.csv":
                (S2 + "standard_and_covid_sensitivity.csv", ["definition", "sample"]),
            I + "clustering_sensitivity.csv":
                (S2 + "clustering_sensitivity.csv", ["definition", "cluster"]),
            # The archived player_linear_trends.csv is the sparse exact solve.
            # The iterative script's own trend file is not archived.
            I + "player_linear_trends_sparse_exact.csv":
                (S2 + "player_linear_trends.csv", ["definition"]),
            # The permutation script QR-factors a nuisance matrix that holds
            # both collinear controls, so its null direction comes from
            # rounding and differs across LAPACK builds (about 0.005 pp).
            # These three files use PERMUTATION_TOL instead of COEF_TOL.
            I + "stratified_tv_permutation_placebo.csv":
                (S2 + "stratified_tv_permutation_placebo.csv", ["definition"], "permutation"),
            I + "permutation_draws_legacy_primary.csv":
                (S2 + "permutation_draws_legacy_primary.csv", [], "permutation"),
            I + "permutation_draws_harmonized_linear.csv":
                (S2 + "permutation_draws_harmonized_linear.csv", [], "permutation"),
        },
    },
}
RUNTIME = {"seconds", "elapsed_sec"}
# dist65_10 = 6.5 - games_before_10, so only their difference is identified.
# One solver splits it across both terms, another keeps one term; compare the
# identified slope games_before_10 - dist65_10 instead of the arbitrary split.
COLLINEAR = {"games_before_10", "dist65_10"}
SLOPE = "games_before_10 - dist65_10"
INFERENCE = re.compile(
    r"(^|_)(se|std_error|z|t|p|p_value|p_two_sided|p_upper|low|high|ci|chi2)(_|$)")
COEF_TOL = 1e-7
INFERENCE_TOL = 1e-3
PERMUTATION_TOL = 0.01


def verify_shared(shared: Path):
    head = subprocess.run(["git", "-C", str(shared), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    if head != SHARED_SHA:
        raise RuntimeError(f"Shared source commit is {head}, not {SHARED_SHA}")
    dirty = subprocess.run(["git", "-C", str(shared), "status", "--porcelain"],
                           check=True, capture_output=True, text=True).stdout.strip()
    if dirty:
        raise RuntimeError("Shared source checkout has local changes")
    if sha(shared / PANEL, decoded=True) != ORIGINAL_RISK_SHA:
        raise RuntimeError("Original August risk panel hash differs")


def stage_script(shared: Path, root: Path, stage_dir: str, script: str):
    """Copy one executed script, changing only its /mnt/data root."""
    source = shared / EXECUTED / stage_dir / script
    text = source.read_text(encoding="utf-8")
    count = text.count(HISTORICAL_ROOT)
    if not count:
        raise RuntimeError(f"{script}: no historical root to redirect")
    target = root / "scripts" / script
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.replace(HISTORICAL_ROOT, str(root / SANDBOX)), encoding="utf-8")
    return {"script": f"{EXECUTED}/{stage_dir}/{script}", "sha256": sha(source),
            "root_substitutions": count}


def prepare(shared: Path, root: Path, stage_dir: str, scripts, panel: Path | None,
            *, rekey_corrected_tv: bool = False):
    if root.exists():
        raise FileExistsError(f"Fresh replay directory required: {root}")
    sandbox = root / SANDBOX
    for rel in PANEL_LOCATIONS:
        (sandbox / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(panel if panel is not None else shared / PANEL, sandbox / rel)
    (sandbox / TV_LOCATION).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(shared / TV, sandbox / TV_LOCATION)
    for rel in OUTPUT_DIRS:
        (sandbox / rel).mkdir(parents=True, exist_ok=True)
    provenance = [stage_script(shared, root, stage_dir, s) for s in scripts]
    rekeys = None
    if rekey_corrected_tv:
        if panel is None:
            raise ValueError("TV rekeying is permitted only with a corrected risk panel")
        rekeys = repair_announcement_fixture_keys(sandbox / TV_LOCATION,
                                                  sandbox / PANEL_LOCATIONS[0])
    return provenance, rekeys


def execute(root: Path, scripts, python: str):
    for script in scripts:
        log = root / f"{Path(script).stem}.log"
        with log.open("w", encoding="utf-8") as stream:
            subprocess.run([python, str(root / "scripts" / script)], cwd=root,
                           stdout=stream, stderr=subprocess.STDOUT,
                           timeout=7200, check=True)


def run_stage(shared: Path, root: Path, spec: dict, panel: Path | None,
              python: str, *, rekey_corrected_tv: bool = False):
    provenance, rekeys = prepare(
        shared, root, spec["executed"], spec["scripts"], panel,
        rekey_corrected_tv=rekey_corrected_tv)
    execute(root, spec["scripts"], python)
    pieces = []
    for script in spec.get("separate", []):
        sub = root.parent / f"{root.name}__{Path(script).stem}"
        more, _ = prepare(shared, sub, spec["executed"], [script], panel,
                          rekey_corrected_tv=rekey_corrected_tv)
        provenance += more
        execute(sub, [script], python)
        out = sub / I
        for draw in out.glob("permutation_draws_*.csv"):
            shutil.copy2(draw, root / I / draw.name)
        pieces.append(pd.read_csv(out / "stratified_tv_permutation_placebo.csv"))
    if pieces:
        pd.concat(pieces, ignore_index=True).to_csv(
            root / I / "stratified_tv_permutation_placebo.csv", index=False)
    missing = [rel for rel in spec["outputs"] if not (root / rel).is_file()]
    if missing:
        raise RuntimeError(f"Executed scripts did not write: {missing}")
    return provenance, rekeys


def json_table(text: str):
    data = json.loads(text)
    return pd.DataFrame({"key": list(data), "value": list(data.values())})


def read_table(path: Path):
    if path.suffix == ".json":
        return json_table(path.read_text())
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


def align(left: pd.DataFrame, right: pd.DataFrame, key):
    """Merge two versions of a table on its key columns (row order if none)."""
    if key is None:
        key = ["key"]
    left, right = left.copy(), right.copy()
    if not key:
        if len(left) != len(right):
            raise RuntimeError("Positional tables differ in length")
        left["_row"] = right["_row"] = range(len(left))
        key = ["_row"]
    for frame in (left, right):
        if frame.duplicated(key).any():
            raise RuntimeError(f"Duplicate table keys {key}")
    joined = left.merge(right, on=key, how="outer", suffixes=("_a", "_b"),
                        indicator=True)
    return joined, key


def has_collinear_pair(frame: pd.DataFrame, key):
    return bool(key) and "term" in key and "estimate" in frame


def identified_slope(frame: pd.DataFrame, key):
    """games_before_10 - dist65_10 per model group (a missing term counts as 0)."""
    pair = frame[frame.term.isin(COLLINEAR)]
    signed = pair.estimate.where(pair.term.eq("games_before_10"), -pair.estimate)
    groups = [k for k in key if k != "term"]
    if not groups:
        return pd.Series({"all": signed.sum()}) if len(pair) else pd.Series(dtype=float)
    return signed.groupby([pair[g] for g in groups]).sum()


def slope_pairs(left: pd.DataFrame, right: pd.DataFrame, key):
    a, b = identified_slope(left, key), identified_slope(right, key)
    index = a.index.union(b.index)
    return a.reindex(index, fill_value=0.0), b.reindex(index, fill_value=0.0)


def compare(left: pd.DataFrame, right: pd.DataFrame, key):
    """Return max coefficient and inference differences, text diffs, unmatched rows."""
    slope_difference = None
    if has_collinear_pair(left, key):
        a, b = slope_pairs(left, right, key)
        slope_difference = float((a - b).abs().max()) if len(a) else 0.0
        left = left[~left.term.isin(COLLINEAR)]
        right = right[~right.term.isin(COLLINEAR)]
    joined, key = align(left, right, key)
    unmatched = joined[joined._merge.ne("both")]
    both = joined[joined._merge.eq("both")]
    report = {"rows": len(both), "unmatched_rows": len(unmatched),
              "identified_slope_max_difference": slope_difference,
              "max_coefficient_difference": 0.0, "max_inference_difference": 0.0,
              "differing_text_cells": 0}
    for col in left.columns:
        if col in key or col in RUNTIME or f"{col}_b" not in both:
            continue
        a, b = both[f"{col}_a"], both[f"{col}_b"]
        if a.dtype == bool or b.dtype == bool:
            a, b = a.astype(str), b.astype(str)
        na, nb = pd.to_numeric(a, errors="coerce"), pd.to_numeric(b, errors="coerce")
        numeric = na.notna() & nb.notna()
        if numeric.any():
            diff = float((na[numeric] - nb[numeric]).abs().max())
            field = ("max_inference_difference" if INFERENCE.search(col)
                     else "max_coefficient_difference")
            report[field] = max(report[field], diff)
        text = ~numeric & ~(a.isna() & b.isna())
        report["differing_text_cells"] += int(
            (a[text].astype(str) != b[text].astype(str)).sum())
    return report


def frozen_gate(shared: Path, root: Path, spec: dict):
    reports = {}
    with zipfile.ZipFile(shared / spec["package"]) as package:
        for rel, (member, key, *kind) in spec["outputs"].items():
            coef_tol = PERMUTATION_TOL if kind == ["permutation"] else COEF_TOL
            if member.endswith(".json"):
                archived = json_table(package.read(member).decode())
            else:
                archived = pd.read_csv(package.open(member),
                                       keep_default_na=False, na_values=[""])
            rerun = read_table(root / rel)
            result = compare(archived, rerun, key)
            ok = (result["unmatched_rows"] == 0
                  and result["differing_text_cells"] == 0
                  and (result["identified_slope_max_difference"] or 0.0) <= COEF_TOL
                  and result["max_coefficient_difference"] <= coef_tol
                  and result["max_inference_difference"] <= INFERENCE_TOL)
            reports[rel] = dict(result, archived_member=member, reproduced=ok,
                                coefficient_tolerance=coef_tol)
    failed = [k for k, v in reports.items() if not v["reproduced"]]
    return reports, failed


def deltas(frozen_root: Path, corrected_root: Path, spec: dict):
    rows = []
    for rel, (_, key, *_kind) in spec["outputs"].items():
        frozen, corrected = read_table(frozen_root / rel), read_table(corrected_root / rel)
        if has_collinear_pair(frozen, key):
            a, b = slope_pairs(frozen, corrected, key)
            for group in a.index:
                label = " | ".join(map(str, group if isinstance(group, tuple) else (group,)))
                rows.append({"file": rel, "row": f"{label} | {SLOPE}",
                             "column": "estimate", "frozen": float(a[group]),
                             "corrected": float(b[group]),
                             "delta": float(b[group] - a[group]),
                             "identified_combination": True})
            frozen = frozen[~frozen.term.isin(COLLINEAR)]
            corrected = corrected[~corrected.term.isin(COLLINEAR)]
        joined, used = align(frozen, corrected, key)
        if joined._merge.ne("both").any():
            raise RuntimeError(f"{rel}: rows present in only one run")
        for record in joined.to_dict("records"):
            label = " | ".join(str(record[k]) for k in used)
            for col in [c[:-2] for c in joined.columns if c.endswith("_a")]:
                if col in RUNTIME:
                    continue
                a, b = record[f"{col}_a"], record[f"{col}_b"]
                try:
                    fa, fb = float(a), float(b)
                    delta = fb - fa
                except (TypeError, ValueError):
                    fa, fb, delta = a, b, None
                rows.append({"file": rel, "row": label, "column": col,
                             "frozen": fa, "corrected": fb, "delta": delta,
                             "identified_combination": False})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shared-repo", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--corrected-panel", type=Path)
    ap.add_argument("--baseline-panel", type=Path,
                    help="Independently rebuilt analysis-ready at-risk model CSV; "
                         "must have the exact decoded frozen release SHA-256")
    ap.add_argument("--frozen-only", action="store_true")
    ap.add_argument("--stages", nargs="+", default=list(STAGES), choices=list(STAGES))
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()
    shared, work = args.shared_repo.resolve(), args.work.resolve()
    if not args.frozen_only and args.corrected_panel is None:
        ap.error("Supply --corrected-panel, or use --frozen-only")
    if work.exists() or shared in work.parents or work in shared.parents:
        raise RuntimeError("Use a new output root outside the shared repository")
    verify_shared(shared)
    corrected = args.corrected_panel.resolve() if args.corrected_panel else None
    baseline = args.baseline_panel.resolve(strict=True) if args.baseline_panel else None
    if baseline is not None and sha(baseline, decoded=True) != ORIGINAL_RISK_SHA:
        raise RuntimeError("Independently built baseline risk CSV differs from released analysis-ready input")
    if corrected is not None and sha(corrected, decoded=True) != CORRECTED_RISK_SHA:
        raise RuntimeError("Corrected August risk panel hash differs")

    summary = {"shared_commit": SHARED_SHA, "original_risk_sha256": ORIGINAL_RISK_SHA,
               "baseline_input": "independently_generated_analysis_ready_panel"
                   if baseline is not None else "historical_frozen_release",
               "independently_generated_baseline_checked_decoded_sha256":
                   ORIGINAL_RISK_SHA if baseline is not None else None,
               "stages": {}}
    for name in args.stages:
        spec = STAGES[name]
        frozen_root = work / name / "frozen"
        provenance, _ = run_stage(shared, frozen_root, spec, baseline, args.python,
                                  rekey_corrected_tv=False)
        gate, failed = frozen_gate(shared, frozen_root, spec)
        record = {"package": spec["package"],
                  "package_sha256": sha(shared / spec["package"]),
                  "executed_scripts": provenance,
                  "frozen_gate": gate, "frozen_reproduced": not failed}
        summary["stages"][name] = record
        if failed:
            record["corrected_run"] = "not run: frozen outputs did not reproduce"
            continue
        if corrected is not None:
            corrected_root = work / name / "corrected"
            _, record["tv_rekeys"] = run_stage(shared, corrected_root, spec, corrected,
                                               args.python, rekey_corrected_tv=True)
            table = deltas(frozen_root, corrected_root, spec)
            path = work / f"{name}_corrected_vs_frozen.csv"
            table.to_csv(path, index=False)
            record["corrected_risk_sha256"] = CORRECTED_RISK_SHA
            record["corrected_vs_frozen"] = str(path)
            record["identified_slope_rows"] = int(table.identified_combination.sum())
    work.mkdir(parents=True, exist_ok=True)
    (work / "august_released_suite_replay.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps({k: {"frozen_reproduced": v["frozen_reproduced"],
                          "failed": [f for f, g in v["frozen_gate"].items()
                                     if not g["reproduced"]]}
                      for k, v in summary["stages"].items()}, indent=2))
    if any(not v["frozen_reproduced"] for v in summary["stages"].values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
