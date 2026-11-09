#!/usr/bin/env python3
"""Reproduce original August pretrend and pre-PPP fake-date placebo outputs.

Uses unchanged scripts/portable/run_prior_event_placebo_checks.py at the pinned
original research commit and original archived outputs in
packages/05_identification_falsification_stage2.zip.

Corrected mode requires the separately verified private 180831-row August
latest-pre-tip risk panel; it repairs only the two old announcement-TV source
DATE/tip keys, preserving original as-announced network classifications.

Frozen originals, archive, source and historical figures remain read-only.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

import numpy as np
import pandas as pd

from run_august_category_fdr_from_release import (
    PANEL, TV, SHARED_SHA, sha, verify_shared,
    original_source_tv_matches_panel, repair_announcement_fixture_keys,
)

SOURCE_SCRIPT = Path("scripts/portable/run_prior_event_placebo_checks.py")
STAGE05_ARCHIVE = Path("packages/05_identification_falsification_stage2.zip")
STAGE05_PREFIX = "nba_identification_falsification_stage2_v1/prior_tv_audit/"
REPLAY_PREFIX = Path("results/portable_identification_stage2")
BENCHMARKS = {
    "event_study_tv_definitions.csv": {
        "key": ["definition", "season"], "n_rows": 10,
        "exact": [], "coefficient": ["estimate_pp"],
        "uncertainty": ["se_pp", "low_pp", "high_pp"],
        "probabilities": ["p"],
    },
    "joint_pretrend_tests.csv": {
        "key": ["definition"], "n_rows": 2,
        "exact": ["n", "df"], "coefficient": [],
        "uncertainty": ["joint_pretrend_chi2"],
        "probabilities": ["p"],
    },
    "preperiod_placebo_policy_dates.csv": {
        "key": ["definition", "fake_start"], "n_rows": 4,
        "exact": ["n"], "coefficient": ["estimate_pp"],
        "uncertainty": ["se_pp", "low_pp", "high_pp"],
        "probabilities": ["p"],
    },
}
TV_FAMILIES = {"legacy_primary", "harmonized_linear"}
FROZEN_RISK_SHA = "d6e82ba61d99fb27ec4877b1c0b05fed76c5cb8fa4bf5b6322742b7049ae9635"
CORRECTED_RISK_SHA = "5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3"
TOL_COEFFICIENT_PP = 1e-8
TOL_UNCERTAINTY = 0.001
TOL_P = 1e-4


def reference_tables(archive: Path):
    if not archive.is_file():
        raise FileNotFoundError(archive)
    results = {}
    with ZipFile(archive) as z:
        bad = z.testzip()
        if bad is not None:
            raise RuntimeError(f"Original Stage-05 archive ZIP CRC failed: {bad}")
        for name, schema in BENCHMARKS.items():
            member = STAGE05_PREFIX + name
            if z.namelist().count(member) != 1:
                raise RuntimeError(f"Original Stage-05 reference missing: {member}")
            frame = pd.read_csv(io.BytesIO(z.read(member)))
            if (len(frame) != schema["n_rows"]
                    or frame.duplicated(schema["key"]).any()
                    or set(frame.definition) != TV_FAMILIES):
                raise RuntimeError(f"Unexpected original archived falsification rows: {name}")
            results[name] = frame
    return results


def stage(shared: Path, root: Path, panel: Path | None = None):
    if root.exists():
        raise FileExistsError(f"Only clean new replay roots are allowed: {root}")
    for rel in (SOURCE_SCRIPT, PANEL, TV):
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(shared / rel, dest)
    if panel is not None:
        shutil.copy2(panel, root / PANEL)


def run_original(root: Path, executable: str):
    log = root / "prior_event_placebo.log"
    with log.open("w", encoding="utf-8") as out:
        subprocess.run(
            [executable, str(root / SOURCE_SCRIPT)],
            cwd=root, stdout=out, stderr=subprocess.STDOUT,
            timeout=1500, check=True,
        )
    results = {}
    for name, schema in BENCHMARKS.items():
        target = root / REPLAY_PREFIX / name
        if not target.is_file():
            raise RuntimeError(f"Original executable omitted {name}")
        table = pd.read_csv(target)
        if (len(table) != schema["n_rows"]
                or table.duplicated(schema["key"]).any()
                or set(table.definition) != TV_FAMILIES):
            raise RuntimeError(f"Original executable emitted unexpected {name} results")
        results[name] = table
    return results


def verify_archived(references: dict, rebuilt: dict):
    worst = {}
    for name, schema in BENCHMARKS.items():
        archived = references[name]
        new = rebuilt[name]
        keys = schema["key"]
        joint = archived.merge(
            new, on=keys, how="outer", indicator=True,
            suffixes=("_archived", "_rebuilt"), validate="one_to_one",
        )
        if len(joint) != schema["n_rows"] or not joint["_merge"].eq("both").all():
            raise RuntimeError(f"{name}: archived versus regenerated spec identity failure")
        values = {}
        for field in schema["exact"]:
            if not joint[f"{field}_archived"].eq(joint[f"{field}_rebuilt"]).all():
                raise RuntimeError(f"{name}: mismatch in exact {field} counts")
        for fields, limit in (
            (schema["coefficient"], TOL_COEFFICIENT_PP),
            (schema["uncertainty"], TOL_UNCERTAINTY),
            (schema["probabilities"], TOL_P),
        ):
            for field in fields:
                difference = (
                    joint[f"{field}_archived"] - joint[f"{field}_rebuilt"]
                ).abs()
                maximum = float(difference.max())
                if not np.isfinite(maximum) or maximum > limit:
                    raise RuntimeError(
                        f"{name}: {field} archived difference {maximum} > {limit}"
                    )
                values[field] = maximum
        worst[name] = values
    return worst


def compare_variant(baseline: dict, corrected: dict):
    result = {}
    for name, schema in BENCHMARKS.items():
        joint = baseline[name].merge(
            corrected[name], on=schema["key"], how="outer",
            indicator=True, suffixes=("_frozen", "_corrected"),
            validate="one_to_one",
        )
        if len(joint) != schema["n_rows"] or not joint["_merge"].eq("both").all():
            raise RuntimeError(f"{name}: corrected run changed original falsification specs")
        for field in schema["coefficient"] + schema["uncertainty"] + schema["probabilities"]:
            joint[field + "_delta"] = (
                joint[field + "_corrected"] - joint[field + "_frozen"]
            )
        result[name] = joint.drop(columns="_merge")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shared-repo", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--corrected-panel", type=Path)
    parser.add_argument("--frozen-only", action="store_true")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    shared, work = args.shared_repo.resolve(), args.work.resolve()
    corrected = args.corrected_panel.resolve() if args.corrected_panel else None
    if not args.frozen_only and corrected is None:
        parser.error("Supply --corrected-panel or --frozen-only")
    if corrected is not None and not corrected.is_file():
        raise FileNotFoundError(corrected)
    if (work.exists() or work == shared or work in shared.parents
            or shared in work.parents
            or (corrected is not None and
                (work == corrected or work in corrected.parents
                 or corrected in work.parents))):
        raise RuntimeError("Replay output must be a new independent root")

    verify_shared(shared)
    if sha(shared / PANEL, decoded=True) != FROZEN_RISK_SHA:
        raise RuntimeError("Original August risk panel decoded SHA mismatch")
    refs = reference_tables(shared / STAGE05_ARCHIVE)
    frozen = work / "frozen"
    stage(shared, frozen)
    matched = original_source_tv_matches_panel(frozen / PANEL, frozen / TV)
    if len(matched) != 180829 or matched.announced_tv_status.isna().any():
        raise RuntimeError("Original frozen pretrend TV source join failed")
    baseline = run_original(frozen, args.python)
    benchmark = verify_archived(refs, baseline)

    report = {
        "research_stage": "August prior-event pretrend and pre-PPP fake-date falsifications",
        "shared_commit": SHARED_SHA,
        "original_script_sha256": sha(shared / SOURCE_SCRIPT),
        "original_archive_sha256": sha(shared / STAGE05_ARCHIVE),
        "original_risk_decoded_sha256": FROZEN_RISK_SHA,
        "original_frozen_results_verified": True,
        "reproduced_models": {"event_season_interactions": 10,
                              "joint_pretrend_tests": 2, "fake_policy_date_placebos": 4},
        "max_archived_deviations": benchmark,
        "limits": "Historical August analysis; placebo date checks do not identify causal effects.",
    }
    if corrected is not None:
        variant_hash = sha(corrected, decoded=True)
        if variant_hash != CORRECTED_RISK_SHA:
            raise RuntimeError(f"Corrected August risk panel SHA mismatch: {variant_hash}")
        other = work / "corrected"
        stage(shared, other, corrected)
        source_rekeys = repair_announcement_fixture_keys(other / TV, other / PANEL)
        new = run_original(other, args.python)
        deltas = compare_variant(baseline, new)
        for name, table in deltas.items():
            table.to_csv(work / ("corrected_vs_frozen_" + name), index=False)
        report.update({
            "corrected_risk_decoded_sha256": variant_hash,
            "source_TV_date_only_rekeys": source_rekeys,
            "corrected_tables": {
                name: table.replace({np.nan: None}).to_dict("records")
                for name, table in deltas.items()
            },
            "corrected_limit": (
                "Private source-rebuilt August latest-pre-tip sensitivity inherits "
                "original award/star/Cup flags and two old date-encoded game IDs."
            ),
        })
    work.mkdir(parents=True, exist_ok=True)
    (work / "august_prior_event_placebo_replay.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "original_frozen_results_verified": True,
        "n_original_result_tables": len(benchmark),
        "worst_numeric_differences": benchmark,
        "corrected_run_executed": corrected is not None,
    }, indent=2))


if __name__ == "__main__":
    main()
