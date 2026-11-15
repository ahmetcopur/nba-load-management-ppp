#!/usr/bin/env python3
"""Read-only semantic check of PPP star eligibility, separate from legacy replay.

A matching frozen hash does not exempt report-only rows from the declared rule.
Never patches the historical builder or writes a replacement analysis panel.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(REPO))
from scripts.data_rebuild.private_source_paths import under_git


def boolean(series: pd.Series, label: str) -> pd.Series:
    values = series.astype(str).str.lower()
    allowed = {"true": True, "false": False, "1": True, "0": False,
               "1.0": True, "0.0": False}
    if not values.isin(allowed).all():
        raise ValueError(f"Missing or invalid boolean in {label}")
    return values.map(allowed).astype(bool)


def evaluate(panel: pd.DataFrame, calendar: pd.DataFrame) -> dict:
    keys = ["season", "nba_player_id"]
    fields = keys + ["star_at_opening_night", "current_season_all_star",
                     "current_all_star_effective_date"]
    if not set(fields) <= set(calendar) or not set(keys + [
            "player_team_game_id", "game_date_et", "star_PPP_it",
            "from_boxscore_roster", "at_risk_for_new_onset_harm",
            "absence_onset_harm"]) <= set(panel):
        raise ValueError("Panel/calendar missing required columns")
    if calendar[keys].isna().any().any() or calendar.duplicated(keys).any():
        raise ValueError("Calendar identities must be nonmissing and unique")
    if panel.player_team_game_id.isna().any() or panel.player_team_game_id.duplicated().any():
        raise ValueError("Panel player-team-game identities must be nonmissing and unique")
    for frame in (panel, calendar):
        if frame[keys].isna().any().any():
            raise ValueError("Missing season/player identity")
    # Project explicitly: panel copies of calendar fields must not hide differences.
    data = panel.drop(columns=[c for c in fields if c not in keys and c in panel]).merge(
        calendar[fields], on=keys, how="left", validate="many_to_one", indicator=True)
    if not data._merge.eq("both").all():
        raise ValueError("Calendar does not cover every panel player-season")
    opening = boolean(data.star_at_opening_night, "star_at_opening_night")
    selected = boolean(data.current_season_all_star, "current_season_all_star")
    effective = pd.to_datetime(data.current_all_star_effective_date, errors="coerce")
    dates = pd.to_datetime(data.game_date_et, errors="raise")
    if (selected & effective.isna()).any():
        raise ValueError("Selected current All-Star has no valid effective date")
    expected = opening | (selected & dates.ge(effective))
    actual = boolean(data.star_PPP_it, "star_PPP_it")
    mismatch = expected.ne(actual)
    roster = boolean(data.from_boxscore_roster, "from_boxscore_roster")
    risk = boolean(data.at_risk_for_new_onset_harm, "at_risk_for_new_onset_harm")
    onset = boolean(data.absence_onset_harm, "absence_onset_harm")
    by_season = []
    for season in sorted(data.season.unique()):
        mask = mismatch & data.season.eq(season)
        by_season.append({"season": season, "mismatched_rows": int(mask.sum()),
                          "at_risk": int((mask & risk).sum()),
                          "onsets": int((mask & onset).sum())})
    return {"status": "FAIL_DECLARED_STAR_DEFINITION" if mismatch.any() else "pass",
            "rows": len(data), "mismatched_rows": int(mismatch.sum()),
            "mismatched_report_only_rows": int((mismatch & ~roster).sum()),
            "mismatched_at_risk_rows": int((mismatch & risk).sum()),
            "mismatched_onsets": int((mismatch & onset).sum()), "by_season": by_season,
            "rule": "opening star OR (selected current-season All-Star AND date >= effective date)",
            "scope": "Semantic comparison against versioned calendar; not primary-source award verification",
            "analysis_panel_modified": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--panel", type=Path, required=True)
    p.add_argument("--calendar", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.output.is_symlink() or under_git(a.output):
        raise ValueError("Use a new private report outside Git")
    if any(a.output.resolve() == x.resolve() for x in (a.panel, a.calendar)):
        raise ValueError("Report must not overwrite an input")
    hashes = {x: hashlib.file_digest(x.open("rb"), "sha256").hexdigest()
              for x in (a.panel, a.calendar)}
    report = evaluate(pd.read_csv(a.panel, low_memory=False), pd.read_csv(a.calendar))
    if any(hashlib.file_digest(x.open("rb"), "sha256").hexdigest() != h
           for x, h in hashes.items()):
        raise RuntimeError("Input changed during semantic audit")
    report["source_sha256"] = {"panel": hashes[a.panel], "calendar": hashes[a.calendar]}
    report["inputs_unchanged"] = True
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(json.dumps(report, indent=2))
    if report["mismatched_rows"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
