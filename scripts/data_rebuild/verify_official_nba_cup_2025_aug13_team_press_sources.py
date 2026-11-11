#!/usr/bin/env python3
"""Verify original August 13, 2025 NBA Cup team-announced fixture identities.

Five independently published, *contemporaneous original first-party NBA team*
2025-08-13 press stories list 20 team-fixture appearances, or 19 different
date/visitor/host group-play matchups. Not the complete 60-game original NBA
Cup schedule and NOT a network census: a blank positive network means
"unreported in that team's announcement", never verified non-national.

Optional ORIGINAL, SHA-pinned private NBA Cup archive joins all 19 distinct
source fixtures to the original 7,230-game research lookup. Public CI must
not claim that private check was executed.
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

try:
    from scripts.data_rebuild import verify_official_NBA_cup_groups as cup
except ModuleNotFoundError:
    import verify_official_NBA_cup_groups as cup

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "validation/official_nba_cup_2025_aug13_five_team_press_releases.csv"
COLS = (
    "season", "source_release_date", "source_reporting_team", "game_date_et",
    "away_team", "home_team", "positively_named_network",
    "original_2025_08_13_NBA_team_press_url",
)
FIXTURE = ("season", "game_date_et", "away_team", "home_team")
SOURCE_URLS = {
    "Toronto Raptors": "https://www.nba.com/raptors/news/raptors-announce-2025-emirates-nba-cup-schedule",
    "Indiana Pacers": "https://www.nba.com/pacers/news/pacers-schedule-announced-for-2025-nba-cup-group-games",
    "Phoenix Suns": "https://www.nba.com/suns/news/phoenix-suns-announce-schedule-for-emirates-nba-cup-2025-group-play-games",
    "Denver Nuggets": "https://www.nba.com/nuggets/news/analyzing-the-denver-nuggets-emirates-nba-cup-schedule",
    "Charlotte Hornets": "https://www.nba.com/hornets/news/hornets-schedule-announced-for-emirates-nba-cup-2025",
}
# Exact source-only reference, independently recorded from each ORIGINAL Aug 13
# team press release. Entry tuple: (MM-DD, VISITOR, HOST, positively named
# TV provider). Empty TV is *unknown from this source*, NOT "no TV".
EXPECTED_SOURCE = {
    "Toronto Raptors": (
        ("10-31", "Toronto Raptors", "Cleveland Cavaliers", ""),
        ("11-07", "Toronto Raptors", "Atlanta Hawks", ""),
        ("11-21", "Washington Wizards", "Toronto Raptors", ""),
        ("11-26", "Indiana Pacers", "Toronto Raptors", ""),
    ),
    "Indiana Pacers": (
        ("10-31", "Atlanta Hawks", "Indiana Pacers", ""),
        ("11-21", "Indiana Pacers", "Cleveland Cavaliers", "Prime"),
        ("11-26", "Indiana Pacers", "Toronto Raptors", ""),
        ("11-28", "Washington Wizards", "Indiana Pacers", ""),
    ),
    "Phoenix Suns": (
        ("10-31", "Utah Jazz", "Phoenix Suns", ""),
        ("11-21", "Minnesota Timberwolves", "Phoenix Suns", ""),
        ("11-26", "Phoenix Suns", "Sacramento Kings", ""),
        ("11-28", "Phoenix Suns", "Oklahoma City Thunder", ""),
    ),
    "Denver Nuggets": (
        ("10-31", "Denver Nuggets", "Portland Trail Blazers", ""),
        ("11-07", "Golden State Warriors", "Denver Nuggets", ""),
        ("11-21", "Denver Nuggets", "Houston Rockets", ""),
        ("11-28", "San Antonio Spurs", "Denver Nuggets", ""),
    ),
    "Charlotte Hornets": (
        ("11-07", "Charlotte Hornets", "Miami Heat", ""),
        ("11-14", "Charlotte Hornets", "Milwaukee Bucks", ""),
        ("11-26", "New York Knicks", "Charlotte Hornets", ""),
        ("11-28", "Chicago Bulls", "Charlotte Hornets", ""),
    ),
}
KNOWN_DATE = "2025-08-13"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("NBA 2025 original Aug 13 Cup team release mismatch: " + reason)


def load_source(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, dtype=str)


def row_id(row) -> tuple:
    return tuple(str(getattr(row, k)) for k in FIXTURE)


def validate_source(source: pd.DataFrame) -> dict:
    require(tuple(source.columns) == COLS, "press release CSV schema differs")
    require(len(source) == 20, "five original teams must supply 20 appearances")
    require(not source.isna().any().any(), "source fields contain implicit NaN")
    require(set(source.season) == {"2025-26"}, "not 2025 Cup season")
    require(set(source.source_release_date) == {KNOWN_DATE},
            "source article release dates cannot be backdated or altered")
    require(set(source.source_reporting_team) == set(SOURCE_URLS),
            "original five announcement sources incomplete or unexpected")

    original_groups = {}
    for group, members in cup.GROUPS["2025-26"].items():
        for team in members.split("|"):
            require(team not in original_groups, "original 2025 NBA group repeated team")
            original_groups[team] = group
    require(len(original_groups) == 30, "2025 official NBA groups not 30 clubs")
    matches = Counter()
    source_counts = {}
    for reporting_team, url in SOURCE_URLS.items():
        rows = source.loc[source.source_reporting_team.eq(reporting_team)]
        require(len(rows) == 4 and set(rows.original_2025_08_13_NBA_team_press_url) == {url},
                "one team source incomplete or URL not NBA original: " + reporting_team)
        expected = set(EXPECTED_SOURCE[reporting_team])
        actual = set()
        home = away = 0
        for row in rows.itertuples(index=False):
            require(reporting_team in (row.away_team, row.home_team),
                    "reporting team's original release lists a game without itself")
            require(row.away_team != row.home_team and
                    row.away_team in original_groups and
                    row.home_team in original_groups and
                    original_groups[row.away_team] == original_groups[row.home_team],
                    "original 2025 group opponents contradict official draw")
            actual.add((row.game_date_et[5:], row.away_team, row.home_team,
                        row.positively_named_network))
            matches[row_id(row)] += 1
            home += row.home_team == reporting_team
            away += row.away_team == reporting_team
        require(actual == expected and len(actual) == 4,
                "Aug 13 original team report date/opponents/provider tuple differs: " +
                reporting_team)
        require(home == 2 and away == 2,
                "source club must play two at home/two away: " + reporting_team)
        source_counts[reporting_team] = len(rows)

    require(len(matches) == 19 and sum(matches.values()) == 20,
            "original five teams not 19 distinct game fixtures")
    duplicate = [k for k, n in matches.items() if n == 2]
    require(duplicate == [("2025-26", "2025-11-26", "Indiana Pacers", "Toronto Raptors")],
            "only Indiana@Toronto should be independently double-reported")
    require(all(n in (1, 2) for n in matches.values()),
            "same original NBA fixture appeared more than twice")
    require(Counter(source.positively_named_network) == {"": 19, "Prime": 1},
            "blank source TV is unknown; one Pacers Prime broadcast positively named")
    return {
        "status": "PASS_ORIGINAL_AUG13_FIVE_NBA_TEAM_SOURCE_ARTICLES",
        "original_same_day_2025_08_13_first_party_team_articles": 5,
        "original_press_game_appearances": 20,
        "independent_distinct_original_fixture_identities": 19,
        "cross_source_identical_indiana_at_toronto_2025_11_26": True,
        "source_reports_four_games_two_home_two_away": source_counts,
        "first_party_positively_named_Prime_games": 1,
        "non_named_network_classification": "UNKNOWN_NOT_NEGATIVE",
        "2025_all_60_original_first_release_fixture_identities_checked": False,
        "2025_original_aug13_first_cup_release_pdf_bytes_recovered": False,
        "original_private_Cup_game_lookup_source_join_executed": False,
    }


def original_private_compare(source: pd.DataFrame, cup_zip: Path) -> dict:
    """Directly verify all 19 source fixture identities in ORIGINAL Cup archive."""
    validate_source(source)
    require(sha256(cup_zip.read_bytes()).hexdigest() == cup.ARCHIVE_SHA256,
            "immutable original private Cup ZIP SHA-256 differs")
    with ZipFile(cup_zip) as z:
        original = pd.read_csv(io.BytesIO(z.read(cup.ARCHIVE_MEMBER)),
                               low_memory=False, keep_default_na=False, dtype=str)
    require(len(original) == 7230 and not original.game_id.duplicated().any(),
            "original Cup lookup not 7,230 unique games")
    stage = original.loc[original.season.eq("2025-26") &
                         original.cup_stage.eq("group_play")]
    require(len(stage) == 60, "original full 2025 Cup lookup not 60 group fixtures")
    source_games = {row_id(row) for row in source.itertuples(index=False)}
    original_games = {row_id(row) for row in stage.itertuples(index=False)}
    require(source_games <= original_games,
            "one or more original Aug 13 announcement fixtures missing from historical Cup")
    return {
        "status": "PASS_19_SAME_DAY_ORIGINAL_TEAM_RELEASES_TO_PRIVATE_CUP_LOOKUP",
        "original_Cup_archive_sha256": cup.ARCHIVE_SHA256,
        "independent_Aug13_source_fixtures_exact_against_original_Cup": 19,
        "2025_remaining_41_first_release_group_fixtures_independently_confirmed": False,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-csv",type=Path,default=DEFAULT_SOURCE)
    p.add_argument("--source-only",action="store_true")
    p.add_argument("--original-cup-zip",type=Path)
    p.add_argument("--output-report",type=Path)
    a=p.parse_args()
    require((a.source_only and not a.original_cup_zip) or
            (not a.source_only and a.original_cup_zip is not None),
            "source-only needs no ZIP, original-private comparison requires Cup ZIP")
    source=load_source(a.source_csv)
    result=validate_source(source)
    if not a.source_only:
        result["private_original"]=original_private_compare(source,a.original_cup_zip)
        result["status"]="PASS_19_ORIGINAL_PRIVATE_SOURCE_FIXTURE_IDENTITIES_ONLY"
    if a.output_report:
        require(not a.output_report.exists(),"refuse overwrite of existing source evidence")
        a.output_report.parent.mkdir(parents=True,exist_ok=True)
        a.output_report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
