#!/usr/bin/env python3
"""Check scientific invariants of the published or rebuilt NBA cadence panel.

A passing check verifies internal consistency, not that the inputs were
independently regenerated from raw NBA PDF/boxscore data.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "data_intermediate/player_team_game_harmonized_cadence.csv.gz"
SEASONS = {"2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"}


def as_binary(series: pd.Series, label: str) -> pd.Series:
    values = series.astype("string").str.strip().str.casefold().map({
        "true": True, "false": False, "1": True, "0": False,
        "1.0": True, "0.0": False
    })
    if values.isna().any():
        raise ValueError(f"{label} has {int(values.isna().sum())} unknown/missing boolean values")
    return values.astype(bool)


def inspect_panel(path: Path, expect_frozen: bool = False) -> dict:
    frame = pd.read_csv(path, low_memory=False)
    required = {"player_team_game_id", "game_id", "season",
                "at_risk_for_new_onset_harm", "absence_onset_harm",
                "absence_now_harm"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError("Missing mandatory columns: " + ", ".join(missing))
    if frame.columns.duplicated().any():
        raise ValueError("Panel has duplicated column labels")
    if frame["player_team_game_id"].isna().any() or \
       frame["player_team_game_id"].duplicated().any():
        raise ValueError("Player-team-game IDs must be unique and nonmissing")
    if frame["game_id"].isna().any() or frame["season"].isna().any():
        raise ValueError("Game and season fields cannot be missing")
    observed_seasons = set(frame["season"].astype(str).unique())
    if observed_seasons != SEASONS:
        raise ValueError(f"Unexpected season coverage: {sorted(observed_seasons)}")
    at_risk = as_binary(frame["at_risk_for_new_onset_harm"], "at_risk")
    onset = as_binary(frame["absence_onset_harm"], "onset")
    absent = as_binary(frame["absence_now_harm"], "currently_absent")
    if (onset & ~at_risk).any():
        raise ValueError("New absence onset occurs outside the onset risk set")
    if (onset & ~absent).any():
        raise ValueError("New absence onset exists where current absence is false")
    data = {
        "rows": int(len(frame)),
        "distinct_games": int(frame["game_id"].nunique()),
        "seasons": sorted(observed_seasons),
        "risk_rows": int(at_risk.sum()),
        "onsets": int(onset.sum()),
        "invariants_passed": True,
        "scope_note": "Integrity checks only; independent data reconstruction not established."
    }
    if expect_frozen:
        expected = {"rows": 248778, "distinct_games": 7230,
                    "risk_rows": 180664, "onsets": 12731}
        wrong = {k: {"observed": data[k], "expected": v}
                 for k, v in expected.items() if data[k] != v}
        if wrong:
            raise ValueError("Frozen October cadence panel counts differ: " + json.dumps(wrong))
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, default=DEFAULT)
    parser.add_argument("--expect-frozen", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = inspect_panel(args.panel, args.expect_frozen)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
