#!/usr/bin/env python3
"""Independently compare ORIGINAL NBA Cup lookups to official league group draws.

Authoritative original NBA releases (not the historical research lookup):
  2023 group draw  https://www.nba.com/news/2023-in-season-tournament-group-play
       Cup dates   https://www.nba.com/news/nba-in-season-tournament-key-dates-schedule
  2024 group draw  https://www.nba.com/news/2024-nba-cup-group-draw-results
       Cup dates   https://www.nba.com/news/2024-emirates-nba-cup-tracker
  2025 group draw  https://www.nba.com/news/2025-nba-cup-group-draw-results
       Cup dates   https://www.nba.com/news/in-season-tournament-101

The league publishes 6 groups of five teams per season: all ten unordered
group matchups must occur once, each club plays four different opponents,
twice home/twice away, and all games occur on officially scheduled Cup
nights. Quarterfinals and semifinals must fall on their official dates.

This is a meaningful independent official NBA source check of all 180
group-stage *opponent fixtures* and all 18 knockout *stage dates*.
It does NOT validate each fixture's original official home/away calendar
date against a published per-game release, broadcasters or TV schedules.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import io
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

ARCHIVE = "nba_player_game_at_risk_star_cup_v1.zip"
ARCHIVE_SHA256 = "65c4756b86dfb5757bb84b6be13eafb952375aaa6ce49fc1ddddc6224a4faf70"
ARCHIVE_MEMBER = "nba_player_game_at_risk_star_cup_v1/cup_game_lookup.csv"

# Explicitly transcribed from the original contemporaneous NBA group draws.
GROUPS = {
    "2023-24": {
        "WA": "Memphis Grizzlies|Phoenix Suns|Portland Trail Blazers|Los Angeles Lakers|Utah Jazz",
        "WB": "Denver Nuggets|New Orleans Pelicans|Dallas Mavericks|LA Clippers|Houston Rockets",
        "WC": "Sacramento Kings|Golden State Warriors|Minnesota Timberwolves|Oklahoma City Thunder|San Antonio Spurs",
        "EA": "Philadelphia 76ers|Cleveland Cavaliers|Atlanta Hawks|Indiana Pacers|Detroit Pistons",
        "EB": "Milwaukee Bucks|New York Knicks|Miami Heat|Washington Wizards|Charlotte Hornets",
        "EC": "Boston Celtics|Brooklyn Nets|Toronto Raptors|Chicago Bulls|Orlando Magic",
    },
    "2024-25": {
        "WA": "Minnesota Timberwolves|LA Clippers|Sacramento Kings|Houston Rockets|Portland Trail Blazers",
        "WB": "Oklahoma City Thunder|Phoenix Suns|Los Angeles Lakers|Utah Jazz|San Antonio Spurs",
        "WC": "Denver Nuggets|Dallas Mavericks|New Orleans Pelicans|Golden State Warriors|Memphis Grizzlies",
        "EA": "New York Knicks|Orlando Magic|Philadelphia 76ers|Brooklyn Nets|Charlotte Hornets",
        "EB": "Milwaukee Bucks|Indiana Pacers|Miami Heat|Toronto Raptors|Detroit Pistons",
        "EC": "Boston Celtics|Cleveland Cavaliers|Chicago Bulls|Atlanta Hawks|Washington Wizards",
    },
    "2025-26": {
        "WA": "Oklahoma City Thunder|Minnesota Timberwolves|Sacramento Kings|Phoenix Suns|Utah Jazz",
        "WB": "Los Angeles Lakers|LA Clippers|Memphis Grizzlies|Dallas Mavericks|New Orleans Pelicans",
        "WC": "Houston Rockets|Denver Nuggets|Golden State Warriors|Portland Trail Blazers|San Antonio Spurs",
        "EA": "Cleveland Cavaliers|Indiana Pacers|Atlanta Hawks|Toronto Raptors|Washington Wizards",
        "EB": "Boston Celtics|Detroit Pistons|Orlando Magic|Brooklyn Nets|Philadelphia 76ers",
        "EC": "New York Knicks|Milwaukee Bucks|Chicago Bulls|Miami Heat|Charlotte Hornets",
    },
}
# Original NBA official Cup-night and knockout dates; title seasons are season_end.
DATES = {
    "2023-24": {
        "group_play": "2023-11-03|2023-11-10|2023-11-14|2023-11-17|2023-11-21|2023-11-24|2023-11-28",
        "quarterfinal": "2023-12-04|2023-12-05", "semifinal": "2023-12-07",
    },
    "2024-25": {
        "group_play": "2024-11-12|2024-11-15|2024-11-19|2024-11-22|2024-11-26|2024-11-29|2024-12-03",
        "quarterfinal": "2024-12-10|2024-12-11", "semifinal": "2024-12-14",
    },
    "2025-26": {
        "group_play": "2025-10-31|2025-11-07|2025-11-14|2025-11-21|2025-11-25|2025-11-26|2025-11-28",
        "quarterfinal": "2025-12-09|2025-12-10", "semifinal": "2025-12-13",
    },
}
OFFICIAL_NBA = {
    "2023-24": {
        "groups": "https://www.nba.com/news/2023-in-season-tournament-group-play",
        "dates": "https://www.nba.com/news/nba-in-season-tournament-key-dates-schedule",
    },
    "2024-25": {
        "groups": "https://www.nba.com/news/2024-nba-cup-group-draw-results",
        "dates": "https://www.nba.com/news/2024-emirates-nba-cup-tracker",
    },
    "2025-26": {
        "groups": "https://www.nba.com/news/2025-nba-cup-group-draw-results",
        "dates": "https://www.nba.com/news/in-season-tournament-101",
    },
}
ROUND_COUNTS = {"group_play": 60, "quarterfinal": 4, "semifinal": 2}


def require(condition: bool, description: str) -> None:
    if not condition:
        raise ValueError("Official NBA Cup source mismatch: " + description)


def check_season(season: str, records: pd.DataFrame) -> dict:
    if season not in GROUPS:
        raise ValueError(f"Unsupported historical original NBA Cup season: {season}")
    groups = GROUPS[season]
    team_group = {}
    for group, fixture_teams in groups.items():
        teams = fixture_teams.split("|")
        require(len(teams) == 5 and len(set(teams)) == 5,
                f"{season} source group {group} not five distinct teams")
        for team in teams:
            require(team not in team_group, f"{season} NBA team assigned to more than one group")
            team_group[team] = group
    require(len(team_group) == 30 and len(groups) == 6,
            f"{season} original NBA group draw has fewer than 30 teams")
    require(len(records) == 66, f"{season} not 66 regular-season tournament games")
    require(records.cup_stage.value_counts().to_dict() == ROUND_COUNTS,
            f"{season} original NBA Cup stage breakdown not 60/4/2")
    allowed = {stage: set(dates.split("|")) for stage, dates in DATES[season].items()}
    for stage, stage_rows in records.groupby("cup_stage"):
        dates = set(stage_rows.game_date_et.astype(str))
        require(dates == allowed[stage],
                f"{season} {stage} dates not official original NBA Cup calendar")
    group_rows = records.loc[records.cup_stage.eq("group_play")]
    home, away, group_pairs, group_count = Counter(), Counter(), defaultdict(list), Counter()
    for record in group_rows.itertuples(index=False):
        require(record.home_team in team_group and record.away_team in team_group,
                f"{season} unrecognized team on group schedule")
        label = team_group[record.home_team]
        require(label == team_group[record.away_team] and record.home_team != record.away_team,
                f"{season} game opponents not in same official original NBA group")
        group_pairs[label].append(tuple(sorted((record.away_team, record.home_team))))
        home[record.home_team] += 1
        away[record.away_team] += 1
        group_count[label] += 1
    require(group_count == {key: 10 for key in groups},
            f"{season} group schedule not 10 distinct matchups per official group")
    for team in team_group:
        require(home[team] == 2 and away[team] == 2,
                f"{season} {team} not 2 home + 2 away group games")
    for label, fixture_teams in groups.items():
        teams = fixture_teams.split("|")
        pairings = {tuple(sorted((team, opponent)))
                    for i, team in enumerate(teams) for opponent in teams[i + 1:]}
        require(set(group_pairs[label]) == pairings and len(group_pairs[label]) == 10,
                f"{season} {label}: not every official group opponent paired exactly once")
    for row in records.itertuples(index=False):
        for flag, target in (
            ("cup_group_play", "group_play"),
            ("cup_quarterfinal", "quarterfinal"),
            ("cup_semifinal", "semifinal"),
        ):
            require(bool(getattr(row, flag)) == (row.cup_stage == target),
                    f"{season} cup flag {flag} contradicts published stage")
        require(bool(row.cup_knockout) == row.cup_stage in ("quarterfinal", "semifinal"),
                f"{season} knockout flag contradicts published stage")

    return {
        "source_releases": OFFICIAL_NBA[season],
        "official_groups_checked": 6,
        "original_unique_unordered_group_fixture_pairs_checked": 60,
        "all_30_teams_exactly_4_group_games_and_2_home_2_away": True,
        "original_quarterfinal_games_on_official_dates": 4,
        "original_semifinal_games_on_official_dates": 2,
        "championship_not_in_regular_season_model": True,
        "group_games_by_date": {str(k): int(v) for k, v in
                                group_rows.groupby("game_date_et").size().to_dict().items()},
        "quarterfinal_games_by_date": {str(k): int(v) for k, v in
                                       records.loc[records.cup_stage.eq("quarterfinal")].
                                       groupby("game_date_et").size().to_dict().items()},
        "semifinal_games_by_date": {str(k): int(v) for k, v in
                                   records.loc[records.cup_stage.eq("semifinal")].
                                   groupby("game_date_et").size().to_dict().items()},
    }


def verify_original_cup_lookup(private_zip: Path) -> dict:
    private_zip = private_zip.resolve()
    require(sha256(private_zip.read_bytes()).hexdigest() == ARCHIVE_SHA256,
            "original private Cup game-stage ZIP SHA-256 drift")
    with ZipFile(private_zip) as archive:
        require(archive.namelist().count(ARCHIVE_MEMBER) == 1,
                "original 7,230-game Cup stage lookup missing or duplicate")
        lookup = pd.read_csv(io.BytesIO(archive.read(ARCHIVE_MEMBER)), low_memory=False)
    require(len(lookup) == 7230 and lookup.game_id.notna().all() and
            not lookup.game_id.duplicated().any(),
            "original six-season Cup source not 7,230 unique games")
    cup = lookup.loc[lookup.cup_game].copy()
    require(len(cup) == 198 and set(cup.season) == set(GROUPS),
            "original 2023–25 regular-season Cup source must contain 198 games")
    seasons = {season: check_season(season, cup.loc[cup.season.eq(season)])
               for season in GROUPS}
    return {
        "status": "PASS_OFFICIAL_NBA_GROUP_FIXTURE_AND_DATE_SOURCE_CHECK",
        "original_Cup_source_ZIP_SHA256": ARCHIVE_SHA256,
        "historical_six_season_games": len(lookup),
        "original_regular_season_Cup_games": len(cup),
        "original_official_NBA_Cup_groups_checked": 18,
        "group_stage_unordered_opponent_fixtures_checked": 180,
        "knockout_stage_games_on_official_dates_checked": 18,
        "seasons": seasons,
        "research_boundaries": {
            "independent_group_draw_and_official_tournament_date_source_check": True,
            "individual_fixture_away_home_date_against_separate_original_NBA_game_release_checked": False,
            "source_Cup_broadcast_and_TV_classifications_independently_checked": False,
            "original_official_primary_source_all_198_per_game_release_rows_rebuilt": False,
            "NBA_championship_game_excluded_from_regular_season_data": True,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-cup-zip", type=Path, required=True)
    p.add_argument("--output-report", type=Path, help="New sanitized JSON report outside Git")
    args = p.parse_args()
    result = verify_original_cup_lookup(args.original_cup_zip)
    output = json.dumps(result, indent=2) + "\n"
    if args.output_report:
        if args.output_report.exists():
            raise FileExistsError("Refusing to overwrite existing official Cup source acceptance")
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        args.output_report.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
