#!/usr/bin/env python3
"""Reproduce original August latest-pre-tip primary and wording estimates, then
refit identical estimators on a separately rebuilt, source-corrected sensitivity.

This is a faithful *reimplementation* of:
- scripts/portable/run_tv_audit_fast.py: primary player+team-season FE onset LPM;
- scripts/portable/run_baseline_and_robustness_models.py: conditional vague
  versus specific LPM with player+season FE;
from the pinned historical NBA research release (Aug 2026).
Both use two-way SE clustering by player and physical game.

Frozen coefficient and N must match the published release; frozen SE permitted
absolute difference <= 0.001 percentage point because the independent numeric
environment differs slightly from the historical archived execution.

Original files are read-only. Frozen award/Cup indicators and two retained
date-encoded game IDs in the corrected sensitivity are NOT source-rebuilt.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.stats import norm
from statsmodels.api import OLS
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups

REPO = Path(__file__).resolve().parents[2]
FROZEN_SHA = "5154317fc52157716cf22f7c5a535259e9f073b3391fd52d78a01faaf8d96d77"
CORRECTED_SHA = "2acd7448a357163951700c99df33a6949e20b19afc2219e6f8c3082b14d3619d"
FROZEN_ANCHORS = {
    "onset_national_partner": (180695, 3.14925625567831, 1.31564272555179),
    "onset_harmonized_linear": (180695, 1.7746566172121114, 1.313416621212169),
    "vague_conditional": (6256, -8.416720679962859, 7.92847960295119),
}
CORRECTED_N = {
    "onset_national_partner": 180697,
    "onset_harmonized_linear": 180697,
    "vague_conditional": 6259,
}
OLD_LINEAR = {"ABC", "ESPN", "ABC/ESPN", "ABC|ESPN", "TNT"}
NEW_LINEAR = {"ABC", "ESPN", "ABC/ESPN", "ABC|ESPN", "NBC/Peacock"}
CTRL = [
    "is_home", "back_to_back", "three_games_in_four_days",
    "four_games_in_six_days", "travel_1000",
    "absolute_timezone_shift_hours", "road_trip_game_number", "elo_100",
    "opponent_bottom_quartile_pre", "opponent_back_to_back",
    "rest_advantage_days", "travel_disadv_1000", "cup_game",
    "minutes10_100", "games_before_10",
]
RAW_COLS = [
    "player_team_game_id", "nba_player_id", "game_id", "team", "season",
    "network_announced", "at_risk_for_new_onset", "absence_onset",
    "vague_onset_frozen", "specific_onset_frozen",
    "star_PPP_it", "postPPP", "announced_tv_primary", "is_home",
    "back_to_back", "three_games_in_four_days", "four_games_in_six_days",
    "opponent_bottom_quartile_pre", "opponent_back_to_back", "cup_game",
    "signed_elo_advantage", "travel_km_since_previous_game",
    "travel_disadvantage_km", "minutes_sum_prior_10_roster_games",
    "games_played_before_game", "absolute_timezone_shift_hours",
    "road_trip_game_number", "rest_advantage_days",
]
MODEL_TERMS = [
    "star_PPP_it", "tv_model", "star_post", "star_tv_m",
    "post_tv_m", "triple_m",
] + CTRL


def uncompressed_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as data:
        for chunk in iter(lambda: data.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_binary(series: pd.Series, name: str):
    values = series.astype(str).str.strip().str.lower()
    if not values.isin({"true", "false", "1", "0", "1.0", "0.0"}).all():
        raise RuntimeError(f"Unexpected missing/non-binary value in {name}")
    return values.isin({"true", "1", "1.0"}).astype(float)


def load_frame(path: Path, corrected: bool):
    observed_hash = uncompressed_sha256(path)
    expected = CORRECTED_SHA if corrected else FROZEN_SHA
    if observed_hash != expected:
        raise RuntimeError(f"Input decompressed SHA mismatch: {observed_hash} != {expected}")
    data = pd.read_csv(path, usecols=RAW_COLS, low_memory=False)
    if len(data) != (248728 if corrected else 248730):
        raise RuntimeError("Unexpected August full panel length")
    if data.player_team_game_id.duplicated().any():
        raise RuntimeError("Duplicate player-team-game ID")
    at_risk = strict_binary(data.at_risk_for_new_onset, "at_risk_for_new_onset")
    expected_risk = 180831 if corrected else 180829
    if int(at_risk.sum()) != expected_risk:
        raise RuntimeError("August at-risk population differs from archived QA")
    data = data.loc[at_risk.eq(1)].copy()
    flags = [
        "star_PPP_it", "postPPP", "announced_tv_primary", "is_home",
        "back_to_back", "three_games_in_four_days", "four_games_in_six_days",
        "opponent_bottom_quartile_pre", "opponent_back_to_back", "cup_game",
        "absence_onset", "vague_onset_frozen", "specific_onset_frozen",
    ]
    for name in flags:
        data[name] = strict_binary(data[name], name)
    # The original 2025-26 TV audit defines harmonized linear television
    # from the advance-announced network, not from actual broadcast metadata.
    data["tv_harmonized_linear"] = np.where(
        data.season.eq("2025-26"),
        data.network_announced.fillna("").isin(NEW_LINEAR),
        data.network_announced.fillna("").isin(OLD_LINEAR),
    ).astype(float)
    data["elo_100"] = data.signed_elo_advantage / 100
    data["travel_1000"] = data.travel_km_since_previous_game / 1000
    data["travel_disadv_1000"] = data.travel_disadvantage_km / 1000
    data["minutes10_100"] = data.minutes_sum_prior_10_roster_games / 100
    data["games_before_10"] = data.games_played_before_game / 10
    data["star_post"] = data.star_PPP_it * data.postPPP
    if int(data.absence_onset.sum()) != (12707 if corrected else 12710):
        raise RuntimeError("Unexpected August new-onset total")
    return data, observed_hash


def sparse_group_projector(groups):
    codes, uniques = pd.factorize(groups, sort=False)
    matrix = csr_matrix(
        (np.ones(len(codes)), (np.arange(len(codes)), codes)),
        shape=(len(codes), len(uniques)),
    )
    return matrix, np.asarray(matrix.sum(axis=0)).ravel()


def parameter_result(df, y_col, tv_col, *, player_teamseason: bool):
    d = df.copy()
    d["tv_model"] = d[tv_col]
    d["star_tv_m"] = d.star_PPP_it * d.tv_model
    d["post_tv_m"] = d.postPPP * d.tv_model
    d["triple_m"] = d.star_PPP_it * d.postPPP * d.tv_model
    columns = list(dict.fromkeys(
        [y_col, "nba_player_id", "game_id", "team", "season"] + MODEL_TERMS
    ))
    d = d[columns].replace([np.inf, -np.inf], np.nan).dropna().copy()
    if len(d) < 5000:
        raise RuntimeError("Unexpected tiny August regression sample")
    values = d[[y_col] + MODEL_TERMS].to_numpy(float)
    if player_teamseason:
        # Faithful to historical run_tv_audit_fast.py, including 100 passes.
        g2 = d.team.astype(str) + "|" + d.season.astype(str)
        groups = [sparse_group_projector(d.nba_player_id),
                  sparse_group_projector(g2)]
        for iteration in range(100):
            old = values.copy() if iteration < 3 or iteration % 5 == 0 else None
            for matrix, counts in groups:
                values -= matrix @ ((matrix.T @ values) / counts[:, None])
            if old is not None and np.max(np.abs(values - old)) < 1e-10:
                break
    else:
        # Faithful to historical run_baseline_and_robustness_models.py,
        # which absorbs player and season with np.add.at group means.
        g1, idx1 = pd.factorize(d.nba_player_id, sort=False)
        g2, idx2 = pd.factorize(d.season, sort=False)
        counts1 = np.bincount(g1, minlength=len(idx1)).astype(float)
        counts2 = np.bincount(g2, minlength=len(idx2)).astype(float)
        for iteration in range(200):
            old = values.copy() if iteration < 5 or iteration % 10 == 0 else None
            sums = np.zeros((len(idx1), values.shape[1]))
            np.add.at(sums, g1, values)
            values -= sums[g1] / counts1[g1, None]
            sums = np.zeros((len(idx2), values.shape[1]))
            np.add.at(sums, g2, values)
            values -= sums[g2] / counts2[g2, None]
            if old is not None and np.max(np.abs(values - old)) < 1e-11:
                break
    y, X = values[:, 0], values[:, 1:]
    survives = (X * X).sum(axis=0) > 1e-12
    X = X[:, survives]
    names = [name for name, keep in zip(MODEL_TERMS, survives) if keep]
    if "triple_m" not in names:
        raise RuntimeError("Star x post-policy x national-TV interaction not identified")
    fitted = OLS(y, X).fit()
    covariance, _, _ = cov_cluster_2groups(
        fitted,
        pd.factorize(d.nba_player_id)[0],
        pd.factorize(d.game_id)[0],
        use_correction=True,
    )
    i = names.index("triple_m")
    beta = float(fitted.params[i])
    se = float(np.sqrt(max(covariance[i, i], 0)))
    if not np.isfinite(se) or se <= 0:
        raise RuntimeError("Nonpositive clustered uncertainty")
    return {
        "n": int(len(d)), "estimate_pp": 100 * beta, "se_pp": 100 * se,
        "low_pp": 100 * (beta - 1.96 * se),
        "high_pp": 100 * (beta + 1.96 * se),
        "p": float(2 * norm.sf(abs(beta / se))),
        "demean_iterations": iteration + 1,
        "FE": "player+teamseason" if player_teamseason else "player+season",
        "clustered_by": ["nba_player_id", "game_id"],
    }


def three_models(df):
    outputs = {
        "onset_national_partner": parameter_result(
            df, "absence_onset", "announced_tv_primary", player_teamseason=True),
        "onset_harmonized_linear": parameter_result(
            df, "absence_onset", "tv_harmonized_linear", player_teamseason=True),
    }
    injury = df[
        df.vague_onset_frozen.eq(1) | df.specific_onset_frozen.eq(1)
    ].copy()
    outputs["vague_conditional"] = parameter_result(
        injury, "vague_onset_frozen", "announced_tv_primary",
        player_teamseason=False,
    )
    return outputs


def verify_frozen(results):
    errors = {}
    for name, (n, estimate, se) in FROZEN_ANCHORS.items():
        found = results[name]
        if (found["n"] != n or
                abs(found["estimate_pp"] - estimate) > 1e-8 or
                abs(found["se_pp"] - se) > 0.001):
            errors[name] = {"expected": (n, estimate, se), "actual": found}
    if errors:
        raise RuntimeError(f"Cannot verify original released August model anchors: {errors}")
    return {
        name: {
            "released_n": n, "released_estimate_pp": estimate, "released_se_pp": se,
            "coefficient_abs_difference_pp": abs(results[name]["estimate_pp"] - estimate),
            "se_abs_difference_pp": abs(results[name]["se_pp"] - se),
        }
        for name, (n, estimate, se) in FROZEN_ANCHORS.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-panel", type=Path,
                        default=REPO / "data_final/player_game_panel_analysis_ready.csv.gz")
    parser.add_argument("--corrected-panel", type=Path,
                        help="Verified August source-corrected 248728-row latest-pre-tip panel")
    parser.add_argument("--output", type=Path,
                        default=REPO / "data_rebuild/output/august_primary_sensitivity.json")
    args = parser.parse_args()
    frozen, frozen_sha = load_frame(args.frozen_panel.resolve(), corrected=False)
    frozen_results = three_models(frozen)
    identity = verify_frozen(frozen_results)
    report = {
        "scope": "August latest-pre-tip source-corrected sensitivity; three original released model specifications reimplemented",
        "historical_frozen_uncompressed_sha256": frozen_sha,
        "published_benchmark_checked": True,
        "frozen_anchors": identity,
        "frozen_results": frozen_results,
        "standard_error_replay_warning": "Independent numerical runtime can differ up to 0.001 percentage points from released SE; coefficients and N gate at 1e-8.",
    }
    if args.corrected_panel:
        corrected, corrected_sha = load_frame(
            args.corrected_panel.resolve(), corrected=True)
        model_results = three_models(corrected)
        for name, expected in CORRECTED_N.items():
            if model_results[name]["n"] != expected:
                raise RuntimeError(f"Corrected August {name} N mismatch")
        report["corrected_results"] = model_results
        report["corrected_uncompressed_sha256"] = corrected_sha
        report["model_estimate_delta_pp"] = {
            name: model_results[name]["estimate_pp"] - frozen_results[name]["estimate_pp"]
            for name in FROZEN_ANCHORS
        }
        report["limitation"] = ("The corrected panel carries forward archived "
            "star/award and Cup indicators and two frozen date-encoded game IDs; "
            "this is not an independently rebuilt complete source-to-paper Level C.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "frozen_benchmark_passed": True,
        "frozen": frozen_results,
        "corrected": report.get("corrected_results"),
    }, indent=2))


if __name__ == "__main__":
    main()
