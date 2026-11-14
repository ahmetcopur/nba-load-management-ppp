#!/usr/bin/env python3
"""Six-season chronology and identity audit of frozen and corrected panels.

Checks, at team-game level, for the August latest-pre-tip full panel and the
October cadence panel (frozen and corrected):
duplicate player-team-game keys, duplicate team-dates, two mirrored teams per
game, ET date equal to the UTC tip converted to New York time, consecutive
team_game_number in tip order, and (August) rest/back-to-back arithmetic.

Across versions it lists every game whose date or tip moved (it must be the
two February 2022 Toronto games only), checks that corrected August and
corrected October agree on every game's date and tip, and optionally compares
every official nba_game_id with the raw NBA boxscore JSON tip time.

Reads inputs only. Writes one JSON report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

EXPECTED_MOVED = {
    "2021-22|20220202T0030Z|Chicago Bulls@Toronto Raptors",
    "2021-22|20220204T0030Z|Miami Heat@Toronto Raptors",
}
TEAM_GAME = ["game_id", "team"]


def team_games(path: Path, columns: list[str]):
    data = pd.read_csv(path, low_memory=False, dtype=str, keep_default_na=False)
    duplicates = int(data.player_team_game_id.duplicated().sum())
    keep = [c for c in columns if c in data.columns]
    games = data[keep].drop_duplicates(TEAM_GAME).copy()
    games["tip"] = pd.to_datetime(games.tip_utc, utc=True)
    return games, duplicates, len(data)


def panel_checks(games: pd.DataFrame, player_key_duplicates: int):
    report = {"team_games": len(games), "games": int(games.game_id.nunique()),
              "duplicate_player_team_game_ids": player_key_duplicates}
    # Conflicting attributes for the same team-game.
    report["team_game_rows_with_conflicting_dates"] = int(
        games.duplicated(TEAM_GAME).sum())
    report["duplicate_team_dates"] = int(
        games.duplicated(["team", "game_date_et"]).sum())
    per_game = games.groupby("game_id").team.nunique()
    report["games_without_exactly_two_teams"] = int(per_game.ne(2).sum())
    mirror = games.merge(games, left_on=["game_id", "team", "opponent"],
                         right_on=["game_id", "opponent", "team"], how="left",
                         suffixes=("", "_other"), indicator=True)
    report["unmirrored_team_games"] = int(mirror._merge.ne("both").sum())
    report["games_with_inconsistent_date_or_tip"] = int(
        games.groupby("game_id")[["game_date_et", "tip_utc"]].nunique()
        .gt(1).any(axis=1).sum())
    et_date = games.tip.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    report["et_date_not_equal_tip_date"] = int(et_date.ne(games.game_date_et).sum())

    ordered = games.sort_values(["season", "team", "tip"])
    expected = ordered.groupby(["season", "team"]).cumcount() + 1
    numbers = pd.to_numeric(ordered.team_game_number, errors="coerce")
    report["team_game_number_out_of_tip_order"] = int(numbers.ne(expected).sum())

    if "rest_days_between_games" in ordered:
        dates = pd.to_datetime(ordered.game_date_et)
        gap = dates.groupby([ordered.season, ordered.team]).diff().dt.days - 1
        rest = pd.to_numeric(ordered.rest_days_between_games, errors="coerce")
        known = gap.notna()
        report["rest_days_arithmetic_mismatches"] = int(
            (rest[known] != gap[known]).sum())
        b2b = ordered.back_to_back.eq("True")
        report["back_to_back_not_rest_zero"] = int(
            (b2b[known] != gap[known].eq(0)).sum())
    return report


def moved_games(frozen: pd.DataFrame, corrected: pd.DataFrame):
    left = frozen.drop_duplicates("game_id").set_index("game_id")
    right = corrected.drop_duplicates("game_id").set_index("game_id")
    common = left.index.intersection(right.index)
    changed = [g for g in common
               if (left.at[g, "game_date_et"], left.at[g, "tip_utc"])
               != (right.at[g, "game_date_et"], right.at[g, "tip_utc"])]
    return {
        "games_only_in_frozen": sorted(set(left.index) - set(right.index)),
        "games_only_in_corrected": sorted(set(right.index) - set(left.index)),
        "games_with_moved_date_or_tip": {
            g: {"frozen": [left.at[g, "game_date_et"], left.at[g, "tip_utc"]],
                "corrected": [right.at[g, "game_date_et"], right.at[g, "tip_utc"]]}
            for g in sorted(changed)},
    }


def covariate_changes(frozen: pd.DataFrame, corrected: pd.DataFrame, fields):
    joined = frozen.merge(corrected, on=TEAM_GAME, suffixes=("_f", "_c"))
    result = {}
    for field in fields:
        if f"{field}_f" not in joined:
            continue
        a = pd.to_numeric(joined[f"{field}_f"], errors="coerce")
        b = pd.to_numeric(joined[f"{field}_c"], errors="coerce")
        numeric = a.notna() & b.notna()
        changed = (numeric & (a - b).abs().gt(1e-9)) | (
            ~numeric & joined[f"{field}_f"].ne(joined[f"{field}_c"]))
        rows = joined.loc[changed]
        result[field] = {
            "changed_team_games": int(changed.sum()),
            "by_season": rows.season_f.value_counts().sort_index().to_dict(),
            "teams": sorted(rows.team.unique().tolist()) if changed.sum() <= 40 else
                     f"{rows.team.nunique()} teams",
        }
    return result


def date_dependent_flags(path: Path):
    """Check that inherited star and Cup flags follow date rules on this panel.

    The award lists themselves are inherited, but whether a player counts as a
    current-season All-Star in a game depends on the game date. If these rules
    hold on the corrected dates, the two moved games cannot carry a stale flag.
    """
    cols = ["season", "game_date_et", "current_season_all_star",
            "current_all_star_effective_date", "current_season_all_star_post_game",
            "star_current_all_star_added", "star_prior_all_star_3yr",
            "star_prior_all_nba_3yr", "star_PPP_it", "cup_game", "postPPP"]
    d = pd.read_csv(path, usecols=cols, dtype=str, keep_default_na=False)
    post = (d.current_season_all_star.eq("True")
            & d.current_all_star_effective_date.ne("")
            & d.game_date_et.ge(d.current_all_star_effective_date))
    prior = d.star_prior_all_star_3yr.eq("True") | d.star_prior_all_nba_3yr.eq("True")
    added = post & ~prior
    star = prior | added
    text = lambda x: x.astype(str)
    return {
        "post_all_star_rule_mismatches": int(text(post).ne(d.current_season_all_star_post_game).sum()),
        "added_star_rule_mismatches": int(text(added).ne(d.star_current_all_star_added).sum()),
        "ppp_star_rule_mismatches": int(text(star).ne(d.star_PPP_it).sum()),
        "post_ppp_season_rule_mismatches": int(text(d.season.isin(
            ["2023-24", "2024-25", "2025-26"])).ne(d.postPPP).sum()),
        "cup_games_in_2021_22": int(d[d.season.eq("2021-22")].cup_game.eq("True").sum()),
        "all_star_effective_dates_2021_22": sorted(
            d[d.season.eq("2021-22") & d.current_all_star_effective_date.ne("")]
            .current_all_star_effective_date.unique().tolist()),
    }


def raw_json_tips(games: pd.DataFrame, raw_roots: list[Path]):
    tips = {}
    paths = [p for root in raw_roots for p in sorted(root.rglob("boxscore_*.json"))]
    for path in paths:
        game = json.loads(path.read_text()).get("game", {})
        tips[str(game.get("gameId"))] = (game.get("gameTimeUTC"),
                                         str(game.get("gameCode", ""))[:8])
    known = games[games.nba_game_id.ne("")].drop_duplicates("game_id").copy()
    known["nba"] = known.nba_game_id.map(lambda x: f"00{int(float(x))}")
    known["json_tip"] = known.nba.map(lambda g: tips.get(g, (None, None))[0])
    known["json_date"] = known.nba.map(lambda g: tips.get(g, (None, None))[1])
    missing = known.json_tip.isna()
    json_tip = pd.to_datetime(known.json_tip, utc=True)
    minutes = (json_tip - known.tip).abs().dt.total_seconds() / 60
    date_ok = known.json_date.eq(known.game_date_et.str.replace("-", ""))
    off = known[~missing & (minutes.gt(0) | ~date_ok)]
    return {
        "raw_json_files": len(tips),
        "panel_games_with_nba_id": len(known),
        "panel_games_missing_from_raw_json": int(missing.sum()),
        "exact_tip_and_date": int((~missing & minutes.eq(0) & date_ok).sum()),
        "differences": [
            {"game_id": r.game_id, "nba_game_id": r.nba, "panel_tip": r.tip_utc,
             "json_tip": r.json_tip, "minutes": float(m)}
            for r, m in zip(off.itertuples(), minutes[off.index])],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--august-frozen", type=Path, required=True)
    ap.add_argument("--august-corrected", type=Path, required=True)
    ap.add_argument("--cadence-frozen", type=Path, required=True)
    ap.add_argument("--cadence-corrected", type=Path, required=True)
    ap.add_argument("--raw-json", type=Path, nargs="+",
                    help="Folders of raw NBA boxscore JSON (searched recursively)")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError("Write the audit to a new file")

    aug_cols = ["game_id", "nba_game_id", "season", "game_date_et", "tip_utc",
                "team", "opponent", "team_game_number", "rest_days_between_games",
                "back_to_back", "travel_km_since_previous_game",
                "absolute_timezone_shift_hours", "signed_elo_advantage",
                "opponent_rest_days_between_games", "three_games_in_four_days"]
    cad_cols = ["game_id", "season", "game_date_et", "tip_utc", "team", "opponent",
                "team_game_number", "back_to_back", "travel_km_since_previous_game",
                "signed_elo_advantage", "announced_tv_primary", "tv_harmonized_linear"]
    panels = {
        "august_frozen": team_games(args.august_frozen, aug_cols),
        "august_corrected": team_games(args.august_corrected, aug_cols),
        "cadence_frozen": team_games(args.cadence_frozen, cad_cols),
        "cadence_corrected": team_games(args.cadence_corrected, cad_cols),
    }
    report = {"inputs": {k: str(getattr(args, k)) for k in
                         ("august_frozen", "august_corrected",
                          "cadence_frozen", "cadence_corrected")}}
    report["panels"] = {k: panel_checks(g, d) for k, (g, d, _) in panels.items()}
    for name in ("august", "cadence"):
        frozen, corrected = panels[f"{name}_frozen"][0], panels[f"{name}_corrected"][0]
        moved = moved_games(frozen, corrected)
        moved["only_expected_two_games_moved"] = (
            set(moved["games_with_moved_date_or_tip"]) == EXPECTED_MOVED
            and not moved["games_only_in_frozen"]
            and not moved["games_only_in_corrected"])
        moved["covariate_changes"] = covariate_changes(
            frozen, corrected,
            ["rest_days_between_games", "back_to_back", "travel_km_since_previous_game",
             "absolute_timezone_shift_hours", "three_games_in_four_days",
             "opponent_rest_days_between_games", "signed_elo_advantage",
             "announced_tv_primary", "tv_harmonized_linear"])
        report[f"{name}_frozen_vs_corrected"] = moved

    a = panels["august_corrected"][0].drop_duplicates("game_id").set_index("game_id")
    c = panels["cadence_corrected"][0].drop_duplicates("game_id").set_index("game_id")
    common = a.index.intersection(c.index)
    disagree = [g for g in common if (a.at[g, "game_date_et"], a.at[g, "tip_utc"])
                != (c.at[g, "game_date_et"], c.at[g, "tip_utc"])]
    report["corrected_august_vs_corrected_cadence"] = {
        "common_games": len(common),
        "august_only_games": len(a.index.difference(c.index)),
        "cadence_only_games": len(c.index.difference(a.index)),
        "date_or_tip_disagreements": disagree,
    }
    report["date_dependent_inherited_flags"] = {
        "august_frozen": date_dependent_flags(args.august_frozen),
        "august_corrected": date_dependent_flags(args.august_corrected),
    }
    if args.raw_json:
        report["august_corrected_vs_raw_boxscore_json"] = raw_json_tips(
            panels["august_corrected"][0], args.raw_json)
        report["august_frozen_vs_raw_boxscore_json"] = raw_json_tips(
            panels["august_frozen"][0], args.raw_json)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
