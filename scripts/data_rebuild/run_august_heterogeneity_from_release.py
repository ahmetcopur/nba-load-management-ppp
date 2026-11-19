#!/usr/bin/env python3
"""Reproduce the PREDECLARED August heterogeneity release; compare a corrected panel.

Runs the original scripts/portable/run_predeclared_heterogeneity.py unchanged
from pinned source commit 0bd713d. Repairs exactly two obsolete February 2022
source-TV fixture lookup DATE keys in a *copy* when corrected mode is used.
Never modifies the original published source, panels, outputs, or manuscript.

Frozen mode is fully runnable in public GitHub Actions. Corrected mode requires
the nonpublic, separately audited August latest-pre-tip 180831-row risk panel.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

# Executed as a script in the same data_rebuild directory.
from run_august_category_fdr_from_release import (
    SHARED_SHA, TV, PANEL, verify_shared, sha,
    original_source_tv_matches_panel, repair_announcement_fixture_keys,
)

REL_SCRIPT = Path("scripts/portable/run_predeclared_heterogeneity.py")
ARCHIVED_RESULTS = Path("results/heterogeneity_results.csv")
OUTPUT_RESULTS = Path("results/portable_heterogeneity/heterogeneity_results.csv")
OUTPUT_CELLS = Path("results/portable_heterogeneity/heterogeneity_raw_cells.csv")
OUTPUT_THRESHOLDS = Path("results/portable_heterogeneity/workload_thresholds.csv")
ORIGINAL_RISK_SHA = (
    "d6e82ba61d99fb27ec4877b1c0b05fed76c5cb8fa4bf5b6322742b7049ae9635"
)
CORRECTED_RISK_SHA = (
    "5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3"
)
KEY = ["heterogeneity", "tv_definition"]
GROUPS = {
    "back_to_back", "weak_opponent", "high_recent_workload",
    "near_65_threshold",
}
TV_VARIANTS = {"announced_tv_primary", "tv_harmonized_linear"}

# Original released precision is the scientific reference; estimated
# covariance/normal-tail differences between NumPy/SciPy/statsmodels wheels
# are bounded separately from coefficient fidelity.
ABSOLUTE_TOLERANCES = {
    "ddd_h0_pp": 1e-7, "ddd_h1_pp": 1e-7,
    "difference_h1_minus_h0_pp": 1e-7,
    "ddd_h0_se_pp": 1e-3, "ddd_h1_se_pp": 1e-3,
    "difference_se_pp": 1e-3,
    "ddd_h0_p": 1e-4, "ddd_h1_p": 1e-4,
    "heterogeneity_p": 1e-4, "heterogeneity_q_bh": 1e-4,
}
EXACT_COLS = ["n", "games", "players", "h1_n", "h0_n"]


def prepare(shared: Path, location: Path, panel: Path | None):
    if location.exists():
        raise FileExistsError(f"Fresh independent replay directory required: {location}")
    for relative in (REL_SCRIPT, PANEL, TV):
        dest = location / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(shared / relative, dest)
    if panel is not None:
        shutil.copy2(panel, location / PANEL)


def run_original(location: Path, python: str):
    log = location / "heterogeneity_run.log"
    with log.open("w", encoding="utf-8") as stream:
        subprocess.run(
            [python, str(location / REL_SCRIPT)],
            cwd=location,
            stdout=stream, stderr=subprocess.STDOUT,
            timeout=2400, check=True,
        )
    output = location / OUTPUT_RESULTS
    if not output.is_file():
        raise RuntimeError("Original August heterogeneity executable wrote no results")
    result = pd.read_csv(output)
    if (len(result) != 8
            or result.duplicated(KEY).any()
            or set(result.heterogeneity) != GROUPS
            or set(result.tv_definition) != TV_VARIANTS):
        raise RuntimeError("Unexpected historical predeclared eight-test family")
    for tv, group in result.groupby("tv_definition"):
        if len(group) != 4 or group.heterogeneity_q_bh.isna().any():
            raise RuntimeError(f"{tv}: incomplete predeclared FDR family")
    for path in (OUTPUT_CELLS, OUTPUT_THRESHOLDS):
        if not (location / path).is_file():
            raise RuntimeError(f"Original heterogeneity executable omitted {path}")
    return result


def verify_published(original: pd.DataFrame, rerun: pd.DataFrame):
    if original.duplicated(KEY).any() or len(original) != 8:
        raise RuntimeError("Published heterogeneity archive must have 8 unique specs")
    joined = original.merge(
        rerun, on=KEY, how="outer",
        suffixes=("_archived", "_rerun"),
        indicator=True, validate="one_to_one",
    )
    if len(joined) != 8 or not joined["_merge"].eq("both").all():
        raise RuntimeError("Missing or extra historical predeclared subgroup specification")
    errors = {}
    for col in EXACT_COLS:
        if not joined[f"{col}_archived"].eq(joined[f"{col}_rerun"]).all():
            errors[col] = "subgroup/model count or sample mismatch"
    maxima = {}
    for col, maximum in ABSOLUTE_TOLERANCES.items():
        diff = (joined[f"{col}_archived"] - joined[f"{col}_rerun"]).abs()
        observed = float(diff.max())
        maxima[col] = observed
        if not np.isfinite(observed) or observed > maximum:
            errors[col] = {"max_abs_difference": observed, "allowed": maximum}
    for col in ("definition",):
        if not joined[f"{col}_archived"].eq(joined[f"{col}_rerun"]).all():
            errors[col] = "predeclared definition text differs"
    if errors:
        raise RuntimeError("Original August heterogeneity reference failed: "
                           + json.dumps(errors, sort_keys=True))
    return maxima


def compare_corrected(frozen: pd.DataFrame, candidate: pd.DataFrame):
    joined = frozen.merge(
        candidate, on=KEY, how="outer",
        suffixes=("_frozen", "_corrected"),
        validate="one_to_one", indicator=True,
    )
    if len(joined) != 8 or not joined["_merge"].eq("both").all():
        raise RuntimeError("Corrected model changed the predeclared hypothesis family")
    if (joined.n_frozen.lt(15000).any()
            or joined.n_corrected.lt(15000).any()
            or joined.h0_n_corrected.add(joined.h1_n_corrected).ne(
                joined.n_corrected).any()):
        raise RuntimeError("Unexpected corrected subgroup sample/group coverage")
    for field in ("difference_h1_minus_h0_pp", "ddd_h0_pp", "ddd_h1_pp",
                  "heterogeneity_p", "heterogeneity_q_bh"):
        joined[field + "_delta"] = (
            joined[field + "_corrected"] - joined[field + "_frozen"]
        )
    return joined.drop(columns="_merge")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shared-repo", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--corrected-panel", type=Path)
    ap.add_argument("--frozen-only", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    shared = args.shared_repo.resolve()
    work = args.work.resolve()
    corrected = (args.corrected_panel.resolve()
                 if args.corrected_panel is not None else None)
    if not args.frozen_only and corrected is None:
        ap.error("Supply --corrected-panel, or use --frozen-only")
    if corrected is not None and not corrected.is_file():
        raise FileNotFoundError(corrected)
    if (work.exists() or work == shared or work in shared.parents
            or shared in work.parents
            or (corrected is not None and
                (work == corrected or work in corrected.parents
                 or corrected in work.parents))):
        raise RuntimeError("Replay must use a new independent output root")

    verify_shared(shared)
    for item in (REL_SCRIPT, ARCHIVED_RESULTS):
        if not (shared / item).is_file():
            raise FileNotFoundError(shared / item)
    pinned_source_hash = sha(shared / REL_SCRIPT)
    if sha(shared / PANEL, decoded=True) != ORIGINAL_RISK_SHA:
        raise RuntimeError("Original August heterogeneity risk data hash differs")

    frozen = work / "frozen"
    prepare(shared, frozen, None)
    original_join = original_source_tv_matches_panel(frozen / PANEL, frozen / TV)
    if (len(original_join) != 180829
            or original_join.announced_tv_status.isna().any()):
        raise RuntimeError("Historical August public TV source join incomplete")
    original = run_original(frozen, args.python)
    archived = pd.read_csv(shared / ARCHIVED_RESULTS)
    deviations = verify_published(archived, original)

    record = {
        "stage": "August predeclared heterogeneity v1: unchanged original executable",
        "pinned_shared_source_commit": SHARED_SHA,
        "original_heterogeneity_script_sha256": pinned_source_hash,
        "original_risk_panel_decoded_sha256": ORIGINAL_RISK_SHA,
        "frozen_model_results": len(original),
        "frozen_reproduced": True,
        "published_max_abs_differences": deviations,
        "predeclared_groups": sorted(GROUPS),
        "multiplicity": "Benjamini-Hochberg among exactly four tests per TV family",
        "not_estimated": "age/career stage: no reliable metadata in original frozen source",
        "original_public_files_unchanged": True,
    }

    if corrected is not None:
        corrected_hash = sha(corrected, decoded=True)
        if corrected_hash != CORRECTED_RISK_SHA:
            raise RuntimeError(
                f"Corrected August private input SHA mismatch: {corrected_hash}"
            )
        variant_root = work / "corrected"
        prepare(shared, variant_root, corrected)
        rekeys = repair_announcement_fixture_keys(
            variant_root / TV, variant_root / PANEL
        )
        variant = run_original(variant_root, args.python)
        table = compare_corrected(original, variant)
        table.to_csv(work / "august_heterogeneity_corrected_vs_frozen.csv",
                     index=False)
        limits = {}
        for spec in GROUPS:
            left = table[table.heterogeneity.eq(spec)]
            limits[spec] = {
                "min_corrected_N": int(left.n_corrected.min()),
                "max_corrected_N": int(left.n_corrected.max()),
            }
        record.update({
            "corrected_private_risk_decoded_sha256": corrected_hash,
            "corrected_TV_source_rekeys": rekeys,
            "corrected_predeclared_models": len(table),
            "corrected_subgroup_samples": limits,
            "corrected_results": table.replace({np.nan: None}).to_dict("records"),
            "qualifications": (
                "Corrected reviewed panel inherits original award/star and Cup "
                "flags and retains two frozen date-encoded game identifiers. "
                "No additional subgroup hypotheses invented or tested."
            ),
        })

    work.mkdir(parents=True, exist_ok=True)
    (work / "august_heterogeneity_replay.json").write_text(
        json.dumps(record, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "frozen_reproduced": True,
        "frozen_models": len(original),
        "corrected_models": record.get("corrected_predeclared_models"),
        "frozen_max_abs_numeric_differences": deviations,
    }, indent=2))


if __name__ == "__main__":
    main()
