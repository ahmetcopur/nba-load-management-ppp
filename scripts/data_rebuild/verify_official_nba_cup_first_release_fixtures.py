#!/usr/bin/env python3
"""Fail-closed first-release NBA Cup source audit for the 2023 and 2024 groups.

The source fixture CSV was independently transcribed from the NBA's first
published group-play "by day" PDFs, not generated from the research lookups:

2023-08-15: https://ak-static.cms.nba.com/wp-content/uploads/sites/46/2023/08/NBA-In-Season-Tournament-Schedule-as-of-8-15-23.pdf
2024-08-13: https://ak-static.cms.nba.com/wp-content/uploads/sites/46/2024/08/Emirates-NBA-Cup-2024-Group-Play-Schedule-as-of-8-13-24.pdf

Source-only mode checks the independent public transcription, not the research
data. For actual private acceptance, supply BOTH original immutable research
archives, which compare all 120 group fixtures to the original Cup game lookup
and date/away/home/network to the frozen later NBA preseason PDF source rows.

This does NOT validate 2025-26 first-release Cup fixtures, knockout-round
broadcasts, subsequent broadcast revisions, or the causal interpretation.
Never upload the original private archives or raw player-level records.
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
    from scripts.data_rebuild import verify_official_NBA_cup_groups as cup_groups
    from scripts.data_rebuild import verify_official_nba_tv_announcements as tv_source
except ModuleNotFoundError:
    import verify_official_NBA_cup_groups as cup_groups
    import verify_official_nba_tv_announcements as tv_source

REPO = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPO / "validation/official_nba_cup_2023_2024_first_release_group_fixtures.csv"
FIELDS = (
    "season", "first_release_date", "game_date_et", "away_team",
    "home_team", "first_release_network",
)
RELEASES = {"2023-24": "2023-08-15", "2024-25": "2024-08-13"}
NETWORK_COUNTS = {
    "2023-24": {"ESPN": 8, "TNT": 6, "NBA TV": 2, "": 44},
    "2024-25": {"ESPN": 6, "TNT": 8, "NBA TV": 3, "": 43},
}
DAY_COUNTS = {
    "2023-24": {
        "2023-11-03": 7, "2023-11-10": 9, "2023-11-14": 10,
        "2023-11-17": 11, "2023-11-21": 5, "2023-11-24": 10,
        "2023-11-28": 8,
    },
    "2024-25": {
        "2024-11-12": 8, "2024-11-15": 12, "2024-11-19": 6,
        "2024-11-22": 8, "2024-11-26": 5, "2024-11-29": 10,
        "2024-12-03": 11,
    },
}
KEY = ("season", "game_date_et", "away_team", "home_team")


def require(ok: bool, what: str) -> None:
    if not ok:
        raise ValueError("NBA Cup first-release source mismatch: " + what)


def as_keys(frame: pd.DataFrame, fields=KEY) -> set[tuple]:
    return set(map(tuple, frame.loc[:, list(fields)].astype(str).itertuples(index=False, name=None)))


def validate_first_release(source: pd.DataFrame) -> dict:
    require(tuple(source.columns) == FIELDS, "fixture source CSV column schema")
    require(len(source) == 120, "expected 120 genuine first-release group fixtures")
    require(set(source.season) == set(RELEASES), "only 2023-24/2024-25")
    require(not source.loc[:, list(KEY)].isna().any().any(), "missing fixture identity")
    require(not source.duplicated(list(KEY)).any(), "duplicate group fixture identity")

    report = {}
    for season, release_date in RELEASES.items():
        selected = source.loc[source.season.eq(season)]
        require(len(selected) == 60, f"{season} not 60 games")
        require(set(selected.first_release_date) == {release_date},
                f"{season} wrong first-announcement publication date")
        require(Counter(selected.game_date_et) == Counter(DAY_COUNTS[season]),
                f"{season} mismatched game day allocation")
        require(Counter(selected.first_release_network) == Counter(NETWORK_COUNTS[season]),
                f"{season} source broadcast counts inconsistent with NBA release")

        team_group = {}
        for label, group in cup_groups.GROUPS[season].items():
            for team in group.split("|"):
                require(team not in team_group, f"{season} duplicate group membership")
                team_group[team] = label
        require(len(team_group) == 30, f"{season} source group coverage")

        pairs, home, away = set(), Counter(), Counter()
        for record in selected.itertuples(index=False):
            require(record.home_team in team_group and record.away_team in team_group,
                    f"{season} team not in original NBA group draw")
            label = team_group[record.home_team]
            require(record.away_team != record.home_team
                    and team_group[record.away_team] == label,
                    f"{season} incompatible official NBA group opponents")
            pair = (label, *sorted((record.away_team, record.home_team)))
            require(pair not in pairs, f"{season} repeated official Cup group opponent pair")
            pairs.add(pair)
            home[record.home_team] += 1
            away[record.away_team] += 1
        require(len(pairs) == 60, f"{season} all 60 unique group pairs missing")
        require(all(home[t] == 2 and away[t] == 2 for t in team_group),
                f"{season} 2-home/2-away design not preserved")
        report[season] = {
            "source_fixture_rows": 60,
            "first_release_date": release_date,
            "unique_group_pairs": len(pairs),
            "all_30_clubs_two_home_two_away": True,
            "broadcast_counts_including_separate_NBA_TV": NETWORK_COUNTS[season],
            "group_games_per_official_date": DAY_COUNTS[season],
        }
    return report


def load_source(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, dtype=str)


def compare_to_private_archives(source: pd.DataFrame, cup_zip: Path, freeze_zip: Path) -> dict:
    """Actually check the immutable 2023/24 original game and TV research rows."""
    require(sha256(cup_zip.read_bytes()).hexdigest() == cup_groups.ARCHIVE_SHA256,
            "original private Cup ZIP digest differs")
    require(sha256(freeze_zip.read_bytes()).hexdigest() == tv_source.FREEZE_SHA,
            "original immutable frozen project ZIP digest differs")

    with ZipFile(cup_zip) as archive:
        cup_csv = archive.read(cup_groups.ARCHIVE_MEMBER)
    cup = pd.read_csv(io.BytesIO(cup_csv), low_memory=False, dtype={
        "season": str, "game_date_et": str, "away_team": str, "home_team": str,
    })
    cup = cup.loc[cup.season.isin(RELEASES) & cup.cup_stage.eq("group_play")]
    require(len(cup) == 120, "original private Cup stage lookup not 120 group games")
    require(not cup.duplicated(list(KEY)).any(), "private Cup identity duplicated")

    source_keys, original_keys = as_keys(source), as_keys(cup)
    require(source_keys == original_keys,
            f"official release to private Cup mismatch: {len(source_keys - original_keys)} "
            f"missing from research, {len(original_keys - source_keys)} extra in research")

    with ZipFile(freeze_zip) as frozen_project:
        packaged = frozen_project.read(tv_source.TV_PACKAGE)
    require(sha256(packaged).hexdigest() == tv_source.ORIGINAL_TV_PACKAGE_SHA,
            "original announced-TV nested ZIP digest differs")
    with ZipFile(io.BytesIO(packaged)) as tvzip:
        archived = pd.read_csv(io.BytesIO(tvzip.read(
            tv_source.MODERN + "source_schedule_rows_2021_22_to_2025_26.csv"
        )), keep_default_na=False, dtype=str)
    archived = archived.loc[archived.season.isin(RELEASES)]
    require(len(archived) == 2400, "original 2023-25 full-preseason schedule source missing")
    translated = archived.rename(columns={
        "announced_date_et": "game_date_et",
        "announced_away_team": "away_team",
        "announced_home_team": "home_team",
        "network_announced": "first_release_network",
    })
    compare_cols = list(KEY) + ["first_release_network"]
    subset = translated.loc[translated.loc[:, list(KEY)].apply(tuple, axis=1).isin(source_keys)]
    require(len(subset) == 120 and not subset.duplicated(list(KEY)).any(),
            "Cup group first release not 120 unique original preseason PDF rows")
    actual_rows = as_keys(subset, compare_cols)
    source_rows = as_keys(source, compare_cols)
    require(source_rows == actual_rows,
            f"network or game mapping drift: {len(source_rows - actual_rows)} official "
            f"first-release rows differ from original main NBA season PDF")

    return {
        "status": "PASS_EXACT_ORIGINAL_PRIVATE_CUP_AND_TV_SOURCE_MATCH",
        "cup_group_fixtures_exact": 120,
        "first_release_network_fields_exact": 120,
        "original_archive_cup_sha256": cup_groups.ARCHIVE_SHA256,
        "original_archive_freeze_sha256": tv_source.FREEZE_SHA,
        "source_fixture_mismatches": 0,
        "source_network_mismatches": 0,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-csv", type=Path, default=DEFAULT_SOURCE)
    p.add_argument("--source-only", action="store_true",
                   help="Validate public first-release fixture transcription only")
    p.add_argument("--original-cup-zip", type=Path)
    p.add_argument("--original-freeze-zip", type=Path)
    p.add_argument("--output-report", type=Path)
    args = p.parse_args()
    require(args.source_only or (args.original_cup_zip and args.original_freeze_zip),
            "private acceptance requires both original ZIPs; otherwise use --source-only")
    require(args.source_only or not (
        (args.original_cup_zip is None) != (args.original_freeze_zip is None)
    ), "partial original ZIP inputs are not accepted")
    result = {
        "status": "PASS_PUBLIC_FIRST_RELEASE_TRANSCRIPTION_ONLY",
        "source_fixture_validation": validate_first_release(load_source(args.source_csv)),
        "sources": {
            "2023-24": "https://ak-static.cms.nba.com/wp-content/uploads/sites/46/2023/08/NBA-In-Season-Tournament-Schedule-as-of-8-15-23.pdf",
            "2024-25": "https://ak-static.cms.nba.com/wp-content/uploads/sites/46/2024/08/Emirates-NBA-Cup-2024-Group-Play-Schedule-as-of-8-13-24.pdf",
        },
        "2025_26_exact_first_release_per_fixture_verified": False,
        "all_198_original_Cup_games_independently_verified": False,
    }
    if not args.source_only:
        result["private_archive_comparison"] = compare_to_private_archives(
            load_source(args.source_csv), args.original_cup_zip, args.original_freeze_zip
        )
        result["status"] = "PASS_PRIVATE_2023_2024_FIRST_RELEASE_RECONCILIATION"
    if args.output_report:
        require(not args.output_report.exists(), "refusing to overwrite an existing report")
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        args.output_report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
