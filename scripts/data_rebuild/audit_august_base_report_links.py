#!/usr/bin/env python3
"""Audit August base-panel report-to-tip timing WITHOUT changing the frozen data.

The 24-hour window is an anomaly screen, not a general rule invalidating all
otherwise legitimate older reports. For these 34 rows, separately inspect the
mismatched matchup and report identity before making a scientific correction.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "data_final/player_game_panel_analysis_ready.csv.gz"
TWO_AFFECTED_GAMES = {
    "2021-22|20220202T0030Z|Chicago Bulls@Toronto Raptors": 16,
    "2021-22|20220204T0030Z|Miami Heat@Toronto Raptors": 18,
}
FIELDS = ["game_id","tip_utc","team","nba_player_name","designation_status",
          "snapshot_basename","snapshot_timestamp_utc","player_team_game_id"]


def audit(source: Path) -> pd.DataFrame:
    data = pd.read_csv(source, dtype=str, keep_default_na=False, low_memory=False)
    missing = set(FIELDS) - set(data.columns)
    if missing:
        raise ValueError(f"Missing expected historical base columns: {sorted(missing)}")
    if data.player_team_game_id.duplicated().any():
        raise ValueError("Historical base has duplicate player-team-game keys")
    tip = pd.to_datetime(data.tip_utc, utc=True, errors="coerce")
    report = pd.to_datetime(data.snapshot_timestamp_utc, utc=True, errors="coerce")
    lead = (tip - report).dt.total_seconds()/3600
    flagged = report.notna() & tip.notna() & (lead.lt(0) | lead.gt(24))
    result = data.loc[flagged, FIELDS].copy()
    result["report_lead_hours"] = lead.loc[flagged]
    result = result.sort_values(["game_id","team","nba_player_name"]).reset_index(drop=True)
    actual = result.game_id.value_counts().to_dict()
    if actual != TWO_AFFECTED_GAMES:
        raise RuntimeError(f"Unexpected affected game set/counts: {actual}")
    if len(result) != 34 or result.player_team_game_id.nunique() != 34:
        raise RuntimeError("August report timing audit count/key invariant failed")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path,
                        default=REPO / "data_rebuild/output/august_bad_report_links.csv")
    parser.add_argument("--compare-ids", type=Path,
                        help="Optional external evidence CSV to compare all flagged player-game IDs")
    args = parser.parse_args()
    result = audit(args.source.resolve())
    if args.compare_ids:
        expected = pd.read_csv(args.compare_ids, dtype=str)
        if "player_team_game_id" not in expected:
            raise ValueError("Evidence CSV has no player_team_game_id")
        if set(expected.player_team_game_id) != set(result.player_team_game_id):
            raise RuntimeError("August report-timing audit does not match external row-level evidence")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"PASS: {len(result)} historical August report-link anomalies, "
          f"{result.game_id.nunique()} games; {result.report_lead_hours.lt(0).sum()} reports after tip")


if __name__ == "__main__":
    main()
