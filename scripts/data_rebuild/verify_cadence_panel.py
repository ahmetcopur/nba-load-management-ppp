#!/usr/bin/env python3
"""Validate a cadence panel independently of the historical builder asserts.

This checks structural invariants and known frozen counts; it does not prove
source accuracy or causal identification. Use on candidate AND frozen data.
"""
from pathlib import Path
import argparse
import json
import pandas as pd

EXPECTED = {"rows": 248778, "at_risk": 180664, "onsets": 12731}
REQUIRED = {"player_team_game_id", "game_id", "season", "nba_player_id",
            "at_risk_for_new_onset_harm", "absence_onset_harm"}
TRUE = {"true", "1", "1.0"}


def validate(path: Path, enforce_counts=True):
    seen = set()
    counts = {"rows": 0, "at_risk": 0, "onsets": 0}
    seasons = set()
    for chunk in pd.read_csv(path, chunksize=30000, dtype=str, keep_default_na=False):
        missing = REQUIRED.difference(chunk.columns)
        if missing:
            raise ValueError("Panel columns missing: " + ", ".join(sorted(missing)))
        ids = chunk["player_team_game_id"].tolist()
        if any(not value for value in ids) or len(set(ids)) != len(ids):
            raise ValueError("Blank/duplicate player_team_game_id within chunk")
        if seen.intersection(ids):
            raise ValueError("Duplicate player_team_game_id across chunks")
        seen.update(ids)
        risk = chunk["at_risk_for_new_onset_harm"].str.lower().isin(TRUE)
        onset = chunk["absence_onset_harm"].str.lower().isin(TRUE)
        for key, series in (("at_risk_for_new_onset_harm", chunk["at_risk_for_new_onset_harm"]),
                            ("absence_onset_harm", chunk["absence_onset_harm"])):
            if not series.str.lower().isin(TRUE | {"false", "0", "0.0"}).all():
                raise ValueError(f"Unexpected boolean encoding in {key}")
        if (onset & ~risk).any():
            raise ValueError("Absence onset outside onset-risk set")
        if chunk["nba_player_id"].eq("").any() or chunk["game_id"].eq("").any():
            raise ValueError("Blank player or game ID")
        seasons.update(chunk["season"].unique())
        counts["rows"] += len(chunk)
        counts["at_risk"] += int(risk.sum())
        counts["onsets"] += int(onset.sum())
    if seasons != {"2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"}:
        raise ValueError(f"Unexpected seasons: {sorted(seasons)}")
    if enforce_counts and counts != EXPECTED:
        raise ValueError(f"Rebuilt panel counts differ: {counts}, expected {EXPECTED}")
    return {"path": str(path), "counts": counts, "seasons": sorted(seasons),
            "frozen_count_match": counts == EXPECTED, "unique_player_team_games": len(seen)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--skip-frozen-counts", action="store_true")
    p.add_argument("--output", type=Path, default=Path("data_rebuild/output/cadence_panel_qa.json"))
    args = p.parse_args()
    report = validate(args.candidate, not args.skip_frozen_counts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
