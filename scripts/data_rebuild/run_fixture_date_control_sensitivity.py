#!/usr/bin/env python3
"""Conditional fixed-outcome Stage-6 regression sensitivity to two fixture-date swaps.

Recomputes the ORIGINAL historical team-game Elo/rest/travel covariates after
correcting two official NBA 2021-22 game dates. Verifies every pre-correction
model control agrees with the frozen cadence panel before replacement.
Refits the archived historical Stage-6 model executable on the new controls,
leaving IDs, outcomes, stars, TV, snapshots, prior playing history FIXED.

This is NOT a complete corrected-source or corrected player-chronology rebuild.
All files are generated outside the frozen original directories.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

import numpy as np
import pandas as pd

from audit_fixture_date_swap_covariates import (
    CORRECTED_TIP_UTC, ELO_COLUMNS, EXPECTED_ZIP_SHA, EXPECTED_CODE_SHA,
    KEY, file_sha, replay, source_tables, compare_rows,
)

REPO = Path(__file__).resolve().parents[2]
MODEL_COLUMNS_TO_UPDATE = [
    "back_to_back", "three_games_in_four_days", "four_games_in_six_days",
    "travel_km_since_previous_game", "absolute_timezone_shift_hours",
    "road_trip_game_number", "signed_elo_advantage",
    "opponent_bottom_quartile_pre", "opponent_back_to_back",
    "rest_advantage_days", "travel_disadvantage_km",
]
STAGE6_CODE_SHA = "f33950c15302f281830bbb5f047ca84b744a77d9039c8a313f158c63374001d3"


def compare_baseline_and_replace(panel: pd.DataFrame, baseline: pd.DataFrame,
                                 corrected: pd.DataFrame):
    reference = panel.merge(
        baseline[KEY + MODEL_COLUMNS_TO_UPDATE],
        on=KEY, validate="many_to_one", suffixes=["_panel", "_historical"]
    )
    if len(reference) != len(panel):
        raise ValueError("Historical team-game source is missing panel rows")
    for col in MODEL_COLUMNS_TO_UPDATE:
        a = reference[col + "_panel"]
        b = reference[col + "_historical"]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            difference = ((a.astype(float) - b.astype(float)).abs().fillna(0).gt(1e-8)
                          | a.isna().ne(b.isna()))
        else:
            difference = a.fillna("").astype(str).ne(b.fillna("").astype(str))
        if difference.any():
            raise RuntimeError(f"Historical {col} differs from frozen panel in {int(difference.sum())} rows")
    new = panel.merge(
        corrected[KEY + MODEL_COLUMNS_TO_UPDATE],
        on=KEY, validate="many_to_one", suffixes=["", "_corrected"]
    )
    if len(new) != len(panel):
        raise ValueError("Corrected team-game source is missing panel rows")
    changes = {}
    for col in MODEL_COLUMNS_TO_UPDATE:
        old, replacement = new[col], new[col + "_corrected"]
        if pd.api.types.is_numeric_dtype(old) and pd.api.types.is_numeric_dtype(replacement):
            mask = ((old.astype(float) - replacement.astype(float)).abs().fillna(0).gt(1e-8)
                    | old.isna().ne(replacement.isna()))
        else:
            mask = old.fillna("").astype(str).ne(replacement.fillna("").astype(str))
        changes[col] = {
            "changed_player_game_rows": int(mask.sum()),
            "changed_games": int(new.loc[mask, "game_id"].nunique()),
        }
        new[col] = replacement
        new.drop(columns=col + "_corrected", inplace=True)
    if list(new.columns) != list(panel.columns):
        raise RuntimeError("Corrected panel accidentally changed column order or schema")
    if not new["player_team_game_id"].equals(panel["player_team_game_id"]):
        raise RuntimeError("Corrected panel changed player-game ID/order")
    frozen = [
        "absence_onset_harm", "absence_now_harm", "at_risk_for_new_onset_harm",
        "star_PPP_it", "announced_tv_primary", "tv_harmonized_linear", "postPPP",
        "games_played_before_game_harm", "minutes_sum_prior_10_roster_games_harm",
        "dist_to_65_before_game_harm", "snapshot_basename", "snapshot_timestamp_utc",
    ]
    for col in frozen:
        if not new[col].equals(panel[col]):
            raise RuntimeError(f"Controlled experiment unintentionally changed {col}")
    return new, changes


def archived_stage6_script(z: zipfile.ZipFile):
    code = z.read("scripts/run_cadence_models_fast.py")
    if hashlib.sha256(code).hexdigest() != STAGE6_CODE_SHA:
        raise RuntimeError("Archived Stage-6 regression executable SHA-256 differs")
    return code.decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--covariates-zip", required=True, type=Path)
    parser.add_argument("--stage6-zip", required=True, type=Path)
    parser.add_argument("--frozen-panel", type=Path,
                        default=REPO / "data_intermediate/player_team_game_harmonized_cadence.csv.gz")
    parser.add_argument("--output-root", type=Path,
                        default=REPO / "data_rebuild/output/corrected_fixture_controls")
    args = parser.parse_args()
    covar_zip, stage6_zip, output_root = (args.covariates_zip.resolve(),
                                           args.stage6_zip.resolve(),
                                           args.output_root.resolve())
    if file_sha(covar_zip) != EXPECTED_ZIP_SHA:
        raise RuntimeError("Original historical game-covariate ZIP SHA-256 changed")
    code, games, archived_team_games = source_tables(covar_zip)
    if hashlib.sha256(code).hexdigest() != EXPECTED_CODE_SHA:
        raise RuntimeError("Original game-covariate executable SHA-256 changed")
    games["tip_utc"] = pd.to_datetime(games["tip_utc"], utc=True)
    games["neutral_site"] = games["neutral_site"].astype(bool)
    with tempfile.TemporaryDirectory(prefix="nba_elo_covariate_replay_") as temp:
        root = Path(temp)
        historical = replay(code, games, root)
        baseline_difference, _, _ = compare_rows(archived_team_games, historical)
        if baseline_difference:
            raise RuntimeError(f"Original team-game baseline failed: {baseline_difference}")
        changed_games = games.copy()
        for game_id, new_utc in CORRECTED_TIP_UTC.items():
            mask = changed_games.game_id.eq(game_id)
            if mask.sum() != 1:
                raise RuntimeError(f"Expected exactly one game in raw table: {game_id}")
            tip = pd.Timestamp(new_utc)
            changed_games.loc[mask, "tip_utc"] = tip
            changed_games.loc[mask, "game_date_et"] = tip.tz_convert(
                "America/New_York").date().isoformat()
        corrected = replay(code, changed_games, root)

    original_panel = pd.read_csv(args.frozen_panel.resolve(), low_memory=False)
    variant, changes = compare_baseline_and_replace(original_panel, historical, corrected)
    output_dir = output_root / "cadence_harmonized_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate = output_dir / "player_team_game_harmonized_cadence.csv.gz"
    variant.to_csv(candidate, index=False, compression="gzip")
    with zipfile.ZipFile(stage6_zip) as archive:
        source = archived_stage6_script(archive)
        original_models = pd.read_csv(archive.open(
            "results/cadence_harmonized_model_results.csv"))
    historic_root = "ROOT=Path('/mnt/data/nba_continue'); OUT=ROOT/'cadence_harmonized_results'"
    if source.count(historic_root) != 1:
        raise RuntimeError("Original historical Stage-6 model input root changed")
    adjusted_source = source.replace(historic_root,
        "ROOT=Path(" + repr(str(output_root)) + "); OUT=ROOT/'cadence_harmonized_results'")
    runner = output_root / "original_stage6_models_corrected_controls.py"
    runner.write_text(adjusted_source)
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1",
           "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    result = subprocess.run(
        [sys.executable, str(runner)], env=env, cwd=str(output_root),
        capture_output=True, text=True, check=True, timeout=600
    )
    (output_root / "stage6_stdout.txt").write_text(result.stdout)
    (output_root / "stage6_stderr.txt").write_text(result.stderr)
    rebuilt_models = pd.read_csv(output_dir / "cadence_harmonized_model_results.csv")
    comparison = rebuilt_models.merge(
        original_models, on=["definition", "controls"], suffixes=["_corrected", "_frozen"],
        how="outer", validate="one_to_one", indicator=True
    )
    if len(comparison) != 4 or not comparison["_merge"].eq("both").all():
        raise RuntimeError("Stage-6 coefficient variants no longer align")
    if not comparison.n_corrected.equals(comparison.n_frozen):
        raise RuntimeError("Conditional covariate sensitivity changed complete-case sample sizes")
    for field in ["estimate_pp", "se_pp", "low_pp", "high_pp", "p"]:
        comparison[field + "_difference"] = (
            comparison[field + "_corrected"] - comparison[field + "_frozen"]
        )
    columns = (["definition", "controls", "n_frozen", "n_corrected"]
               + [f + "_frozen" for f in ["estimate_pp", "se_pp", "p"]]
               + [f + "_corrected" for f in ["estimate_pp", "se_pp", "p"]]
               + [f + "_difference" for f in ["estimate_pp", "se_pp", "p"]])
    comparison[columns].to_csv(output_root / "model_delta.csv", index=False)
    report = {
        "scope": "Conditional model-control sensitivity only: frozen outcomes, TV, IDs and player histories",
        "original_game_covariate_zip_sha256": EXPECTED_ZIP_SHA,
        "original_game_covariate_code_sha256": EXPECTED_CODE_SHA,
        "original_stage6_model_code_sha256": STAGE6_CODE_SHA,
        "historical_team_game_baseline_differing_cells": 0,
        "historical_team_game_baseline_columns": len(archived_team_games.columns),
        "corrections": CORRECTED_TIP_UTC,
        "changed_panel_controls": changes,
        "model_differences": comparison[columns].to_dict("records"),
        "warning": "Not a complete corrected-source analysis: do not reinterpret frozen game IDs, outcomes, report selection, TV, star status or prior playing histories as independently reconstructed.",
    }
    (output_root / "conditional_sensitivity_report.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2)[:15000])


if __name__ == "__main__":
    main()
