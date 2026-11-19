#!/usr/bin/env python3
"""Verify all 15 specifically listed 2025 NBA Cup national Group Play games.

Original dated NBA source (updated Aug 21, 2025):
https://www.nba.com/news/2025-26-schedule-announced

This is an NBA-published national GAME SUBSET, not all 60 original Cup group
fixtures or the missing independent original AUG 13 Cup schedule binary.
The NBA's Aug 14 press statement directly names nine of these 15: cross-check
that earlier nine subset without treating it as the complete original release.
The first-release timing of the other six games remains unverified.

With pinned PRIVATE archives, compare exact Cup fixture and later NBA season
PDF networks. No original ZIPs or underlying player-level records are written.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import io
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

try:
    from scripts.data_rebuild import verify_official_NBA_cup_groups as groups
    from scripts.data_rebuild import verify_official_nba_tv_announcements as tv
    from scripts.data_rebuild import verify_official_nba_cup_2025_named_broadcasts as aug14
    from scripts.data_rebuild import compare_nba_cup_exact_source_rows as exact_join
    from scripts.data_rebuild import hash_original_archive_streaming as stream_hash
except ModuleNotFoundError:
    import hash_original_archive_streaming as stream_hash
    import verify_official_NBA_cup_groups as groups
    import verify_official_nba_tv_announcements as tv
    import verify_official_nba_cup_2025_named_broadcasts as aug14
    import compare_nba_cup_exact_source_rows as exact_join

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "validation/official_nba_cup_2025_aug21_all_15_national_group_broadcasts.csv"
ORIGIN = "https://www.nba.com/news/2025-26-schedule-announced"
COLS = ("season", "source_verified_by_date", "game_date_et", "away_team", "home_team",
        "source_announced_network", "source_url")
KEYS = ("season", "game_date_et", "away_team", "home_team")
FIVE = ("season", "game_date_et", "away_team", "home_team", "source_announced_network")
# Independent explicit published NBA.com game-by-game national broadcast list.
# Hardcoded reference prevents falsely passing CSV same-date or TV-bucket swaps.
ALL_15 = {
    ("2025-10-31", "Boston Celtics", "Philadelphia 76ers", "Prime"),
    ("2025-10-31", "Los Angeles Lakers", "Memphis Grizzlies", "Prime"),
    ("2025-11-07", "Houston Rockets", "San Antonio Spurs", "Prime"),
    ("2025-11-07", "Golden State Warriors", "Denver Nuggets", "Prime"),
    ("2025-11-14", "Miami Heat", "New York Knicks", "Prime"),
    ("2025-11-14", "Golden State Warriors", "San Antonio Spurs", "Prime"),
    ("2025-11-21", "Indiana Pacers", "Cleveland Cavaliers", "Prime"),
    ("2025-11-21", "Denver Nuggets", "Houston Rockets", "Prime"),
    ("2025-11-25", "Orlando Magic", "Philadelphia 76ers", "NBC/Peacock"),
    ("2025-11-25", "LA Clippers", "Los Angeles Lakers", "NBC/Peacock"),
    ("2025-11-26", "Detroit Pistons", "Boston Celtics", "ESPN"),
    ("2025-11-26", "Minnesota Timberwolves", "Oklahoma City Thunder", "ESPN"),
    ("2025-11-26", "Houston Rockets", "Golden State Warriors", "ESPN"),
    ("2025-11-28", "Milwaukee Bucks", "New York Knicks", "Prime"),
    ("2025-11-28", "Dallas Mavericks", "Los Angeles Lakers", "Prime"),
}


def require(ok: bool, what: str) -> None:
    if not ok:
        raise ValueError("NBA Cup 2025 fifteen national fixtures: " + what)


def records(frame: pd.DataFrame, fields: tuple[str, ...]) -> set[tuple]:
    return set(frame.loc[:, list(fields)].itertuples(index=False, name=None))


def load(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, dtype=str)


def validate_15(source: pd.DataFrame, nine: pd.DataFrame) -> dict:
    require(tuple(source.columns) == COLS, "CSV column schema changed")
    require(len(source) == 15, "not exactly 15 national first-party source rows")
    require(set(source.season) == {"2025-26"}, "not exactly 2025-26 season")
    require(set(source.source_verified_by_date) == {"2025-08-21"},
            "NBA.com 2025 source update date differs")
    require(set(source.source_url) == {ORIGIN}, "not original NBA.com schedule source")
    require(not source.duplicated(list(KEYS)).any(), "duplicate official national fixture")

    named = records(source, ("game_date_et", "away_team", "home_team", "source_announced_network"))
    require(named == ALL_15, "published national exact dated matchup/network mismatch")
    require(Counter(source.source_announced_network) ==
            Counter({"Prime": 10, "NBC/Peacock": 2, "ESPN": 3}),
            "NBA official TV provider totals drift")

    aug14.verify_named_source(nine)
    earlier = records(nine, ("game_date_et", "away_team", "home_team", "source_announced_network"))
    require(earlier <= named and len(named - earlier) == 6,
            "NBA Aug 14 independently named nine not exactly included in Aug 21 fifteen")

    team_group = {}
    for label, members in groups.GROUPS["2025-26"].items():
        for name in members.split("|"):
            require(name not in team_group, "duplicate original NBA Cup group assignment")
            team_group[name] = label
    require(len(team_group) == 30, "original NBA 2025 groups not complete")
    for r in source.itertuples(index=False):
        require(r.away_team in team_group and r.home_team in team_group and
                team_group[r.away_team] == team_group[r.home_team] and
                r.away_team != r.home_team,
                "published national Cup matchup not in official original 2025 group")

    return {
        "status": "PASS_15_NAMED_ORIGINAL_NBA_NATIONAL_BROADCAST_SOURCE_SUBSET",
        "NBA_official_public_2025_group_national_game_rows": 15,
        "national_provider_counts": {"Prime": 10, "NBC/Peacock": 2, "ESPN": 3},
        "independently_named_in_original_Aug_14_release": 9,
        "additional_original_NBA_com_Aug_21_named_game_rows": 6,
        "NBA_com_article_last_updated_date": "2025-08-21",
        "original_Aug_13_60_game_Cup_release_binary_and_all_60_rows_verified": False,
        "first_release_date_for_six_additional_games_independently_established": False,
        "all_2023_2025_Cup_knockout_per_game_providers_rechecked": False,
    }


def compare_original_private(source: pd.DataFrame, nine: pd.DataFrame,
                             cup_zip: Path, freeze_zip: Path) -> dict:
    validate_15(source, nine)
    require(stream_hash.sha256_file(cup_zip) == groups.ARCHIVE_SHA256,
            "original Cup source ZIP SHA-256 drift")
    require(stream_hash.sha256_file(freeze_zip) == tv.FREEZE_SHA,
            "original research freeze ZIP SHA-256 drift")
    with ZipFile(cup_zip) as z:
        original = pd.read_csv(io.BytesIO(z.read(groups.ARCHIVE_MEMBER)),
                               keep_default_na=False, dtype=str)
    original = original.loc[original.season.eq("2025-26") &
                            original.cup_stage.eq("group_play")]
    require(len(original) == 60 and not original.duplicated(list(KEYS)).any(),
            "original private 2025 Cup group lookup not 60 unique games")
    exact_join.exact_group_fixture_join(
        source, original, expected=15, subset=True
    )
    with ZipFile(freeze_zip) as outer:
        nested = outer.read(tv.TV_PACKAGE)
    require(sha256(nested).hexdigest() == tv.ORIGINAL_TV_PACKAGE_SHA,
            "nested original national TV release package changed")
    with ZipFile(io.BytesIO(nested)) as z:
        pdf_rows = pd.read_csv(io.BytesIO(z.read(
            tv.MODERN + "source_schedule_rows_2021_22_to_2025_26.csv")),
            keep_default_na=False, dtype=str)
    pdf_rows = pdf_rows.loc[pdf_rows.season.eq("2025-26")]
    require(len(pdf_rows) == 1200, "original 2025 preseason NBA release PDF not 1200 rows")
    pdf_rows = pdf_rows.rename(columns={
        "announced_date_et": "game_date_et",
        "announced_away_team": "away_team",
        "announced_home_team": "home_team",
        "network_announced": "source_announced_network",
    })
    require(not pdf_rows.duplicated(list(KEYS)).any(),
            "duplicate game identity in original PDF parser release rows")
    official_names = source.rename(columns={
        "source_announced_network": "first_release_network"
    })
    pdf_names = pdf_rows.rename(columns={
        "source_announced_network": "first_release_network"
    })
    exact_join.exact_first_release_network_join(
        official_names, pdf_names, expected=15
    )
    return {
        "status": "PASS_15_ORIGINAL_PRIVATE_2025_NAMED_NATIONAL_CUP_GAME_TUPLES",
        "original_Cup_fixture_tuples_exact": 15,
        "original_preseason_PDF_network_tuples_exact": 15,
        "original_first_Aug13_full_60_Cup_game_announcement_source_verified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-csv", type=Path, default=SOURCE)
    parser.add_argument("--earlier-nine-csv", type=Path, default=aug14.SOURCE)
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--original-cup-zip", type=Path)
    parser.add_argument("--original-freeze-zip", type=Path)
    parser.add_argument("--output-report", type=Path)
    a = parser.parse_args()
    require((a.source_only and not a.original_cup_zip and not a.original_freeze_zip)
            or (not a.source_only and a.original_cup_zip and a.original_freeze_zip),
            "source-only means no private ZIPs; private acceptance requires both original ZIPs")
    source, nine = load(a.source_csv), aug14.load_source(a.earlier_nine_csv)
    report = validate_15(source, nine)
    if not a.source_only:
        report["private_source_comparison"] = compare_original_private(
            source, nine, a.original_cup_zip, a.original_freeze_zip
        )
        report["status"] = "PASS_15_PRIVATE_ORIGINAL_SOURCE_TUPLES_ONLY"
    if a.output_report:
        require(not a.output_report.exists(), "refuse overwrite of prior scientific evidence")
        a.output_report.parent.mkdir(parents=True, exist_ok=True)
        a.output_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
