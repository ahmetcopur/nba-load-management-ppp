#!/usr/bin/env python3
"""Independently rebuild original August latest-pre-tip paper descriptives.

Computes the eight onset-risk TV cells, pooled star/nonstar onset and absence
prevalence cells, and reviewed taxonomy onsets before/after PPP.
Rejects frozen values inconsistent with the original released manuscript.
An optional corrected panel is a separately hash-verified sensitivity.

This is NOT October common-time cadence and not an adjusted causal estimator.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from run_august_preferred_model_sensitivity import (
    FROZEN_SHA, CORRECTED_SHA, REPO, strict_binary, uncompressed_sha256,
)

REQUIRED_COLUMNS = [
    "player_team_game_id", "star_PPP_it", "postPPP",
    "announced_tv_primary", "at_risk_for_new_onset", "absence_onset",
    "report_outcome_observed", "absence_now", "designation_class_frozen",
]
TV_FROZEN_RAW_DDD = 2.4279876494871626


def read_panels(path: Path, *, corrected: bool):
    sha = uncompressed_sha256(path)
    if sha != (CORRECTED_SHA if corrected else FROZEN_SHA):
        raise RuntimeError("August full-panel decompressed SHA-256 failed")
    frame = pd.read_csv(path, usecols=REQUIRED_COLUMNS, low_memory=False)
    if frame.player_team_game_id.duplicated().any():
        raise RuntimeError("Player-team-game keys are not unique")
    if len(frame) != (248728 if corrected else 248730):
        raise RuntimeError("Unexpected August descriptive panel length")
    for col in REQUIRED_COLUMNS:
        if col in ("player_team_game_id", "designation_class_frozen"):
            continue
        frame[col] = strict_binary(frame[col], col).eq(1)
    return frame, sha


def cells(df):
    risk = df[df.at_risk_for_new_onset]
    onset = risk.groupby(
        ["star_PPP_it", "postPPP", "announced_tv_primary"], observed=True
    ).agg(
        n=("absence_onset", "size"),
        onsets=("absence_onset", "sum"),
    ).reset_index()
    if len(onset) != 8:
        raise RuntimeError("TV×star×period eight-cell design is incomplete")
    onset["rate_pct"] = 100 * onset.onsets / onset.n
    rates = onset.set_index(
        ["star_PPP_it", "postPPP", "announced_tv_primary"]
    ).rate_pct

    def tv_star_gap(post):
        return ((rates[True, post, True] - rates[False, post, True])
                - (rates[True, post, False] - rates[False, post, False]))
    raw_tv_ddd = float(tv_star_gap(True) - tv_star_gap(False))

    pooled = risk.groupby(
        ["star_PPP_it", "postPPP"], observed=True
    ).agg(at_risk=("absence_onset", "size"),
          onsets=("absence_onset", "sum")).reset_index()
    pooled["rate_pct"] = 100 * pooled.onsets / pooled.at_risk

    observed = df[df.report_outcome_observed]
    prevalence = observed.groupby(
        ["star_PPP_it", "postPPP"], observed=True
    ).agg(observed=("absence_now", "size"),
          absent=("absence_now", "sum")).reset_index()
    prevalence["rate_pct"] = 100 * prevalence.absent / prevalence.observed
    types = df[df.absence_onset].groupby(
        ["star_PPP_it", "postPPP", "designation_class_frozen"], observed=True,
    ).size().reset_index(name="n")
    return {
        "rows": len(df), "risk_rows": len(risk),
        "new_onsets": int(risk.absence_onset.sum()),
        "eight_tv_onset_cells": onset.to_dict("records"),
        "pooled_onset": pooled.to_dict("records"),
        "pooled_prevalence": prevalence.to_dict("records"),
        "reviewed_onset_classes": types.to_dict("records"),
        "unadjusted_tv_triple_difference_pp": raw_tv_ddd,
    }


def frozen_gate(results):
    if results["risk_rows"] != 180829 or results["new_onsets"] != 12710:
        raise RuntimeError("Frozen August risk/onset totals disagree with release")
    if abs(results["unadjusted_tv_triple_difference_pp"] - TV_FROZEN_RAW_DDD) > 1e-8:
        raise RuntimeError("Frozen August raw TV DDD differs from release")
    groups = {
        (v["star_PPP_it"], v["postPPP"]): (v["at_risk"], v["onsets"])
        for v in results["pooled_onset"]
    }
    expected = {
        (True, False): (7779, 818),
        (True, True): (8807, 810),
        (False, False): (80086, 4781),
        (False, True): (84157, 6301),
    }
    if groups != expected:
        raise RuntimeError(f"Frozen August four-group onset benchmarks differ: {groups}")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-panel", type=Path,
                        default=REPO / "data_final/player_game_panel_analysis_ready.csv.gz")
    parser.add_argument("--corrected-panel", type=Path,
                        help="Separate audited August source-corrected latest-pre-tip panel")
    parser.add_argument("--output", type=Path,
                        default=REPO / "data_rebuild/output/august_descriptive_sensitivity.json")
    args = parser.parse_args()
    original, original_sha = read_panels(args.frozen_panel.resolve(), corrected=False)
    baseline = cells(original)
    frozen_gate(baseline)
    report = {
        "scope": "August latest-pre-tip, not October cadence",
        "original_decoded_sha256": original_sha,
        "frozen_manuscript_identity_checked": True,
        "frozen": baseline,
        "interpretation_warning": (
            "Raw eight-cell TV triple difference is unadjusted, not the August "
            "fixed-effect interaction and not a causal PPP effect."
        ),
    }
    if args.corrected_panel:
        updated, updated_sha = read_panels(
            args.corrected_panel.resolve(), corrected=True)
        sensitivity = cells(updated)
        if sensitivity["risk_rows"] != 180831 or sensitivity["new_onsets"] != 12707:
            raise RuntimeError("Corrected August source-core outcome gate failed")
        report["corrected_decoded_sha256"] = updated_sha
        report["corrected"] = sensitivity
        report["raw_triple_delta_pp"] = (
            sensitivity["unadjusted_tv_triple_difference_pp"]
            - baseline["unadjusted_tv_triple_difference_pp"]
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "frozen_identity": True,
        "frozen_raw_tv_triple_pp": baseline["unadjusted_tv_triple_difference_pp"],
        "corrected_raw_tv_triple_pp": report.get("corrected", {}).get(
            "unadjusted_tv_triple_difference_pp"),
        "corrected_onsets": report.get("corrected", {}).get("new_onsets"),
    }, indent=2))


if __name__ == "__main__":
    main()
