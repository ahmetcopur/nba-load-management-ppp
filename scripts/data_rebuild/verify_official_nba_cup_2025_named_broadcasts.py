#!/usr/bin/env python3
"""Reconcile 9 NAMED 2025 NBA Cup group broadcasts from the NBA's 2025-08-14 release.

The NBA's dated first-party full-season press release identifies these nine
specific Cup group-play matchup/network tuples:
https://pr.nba.com/2025-26-nba-regular-season-schedule/

This is *NOT* the full 2025-08-13 first Cup group schedule: that independent
full first-release source is still missing. An August 14 statement corroborates
only the nine EXPLICITLY NAMED games and source-identified TV networks.
Do not backdate verified-by-August-14 statements to August 13.

Optional PRIVATE acceptance joins nine tuples to the two immutable original
pinned research archives; only aggregate statistics are emitted.
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
    from scripts.data_rebuild import hash_original_archive_streaming as stream_hash
except ModuleNotFoundError:
    import hash_original_archive_streaming as stream_hash
    import verify_official_NBA_cup_groups as cup_groups
    import verify_official_nba_tv_announcements as tv_source

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "validation/official_nba_cup_2025_aug14_named_group_broadcasts.csv"
ORIGIN = "https://pr.nba.com/2025-26-nba-regular-season-schedule/"
COLUMNS = (
    "season", "source_announcement_date_et", "game_date_et",
    "away_team", "home_team", "source_announced_network", "source_url",
)
KEYS = ("season", "game_date_et", "away_team", "home_team")
# Explicit named matchups manually read from the first-party NBA release.
# This hard-coded 9-row reference is deliberately independent of the CSV;
# moving a named game within the same date/network bucket must fail closed.
NAMED = {
    ("2025-10-31", "Boston Celtics", "Philadelphia 76ers", "Prime"),
    ("2025-10-31", "Los Angeles Lakers", "Memphis Grizzlies", "Prime"),
    ("2025-11-25", "Orlando Magic", "Philadelphia 76ers", "NBC/Peacock"),
    ("2025-11-25", "LA Clippers", "Los Angeles Lakers", "NBC/Peacock"),
    ("2025-11-26", "Detroit Pistons", "Boston Celtics", "ESPN"),
    ("2025-11-26", "Minnesota Timberwolves", "Oklahoma City Thunder", "ESPN"),
    ("2025-11-26", "Houston Rockets", "Golden State Warriors", "ESPN"),
    ("2025-11-28", "Milwaukee Bucks", "New York Knicks", "Prime"),
    ("2025-11-28", "Dallas Mavericks", "Los Angeles Lakers", "Prime"),
}
COMPARE = ("season", "game_date_et", "away_team", "home_team", "source_announced_network")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("2025 NBA Cup named broadcast source mismatch: " + reason)


def tuples(frame: pd.DataFrame, names: tuple[str, ...]) -> set[tuple]:
    return set(frame.loc[:, list(names)].itertuples(index=False, name=None))


def load_source(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, dtype=str)


def verify_named_source(source: pd.DataFrame) -> dict:
    require(tuple(source.columns) == COLUMNS, "unexpected CSV schema")
    require(len(source) == 9, "expected nine specifically named official matchups")
    require(not source.duplicated(list(KEYS)).any(), "duplicate official game")
    require(set(source.season) == {"2025-26"}, "invalid season")
    require(set(source.source_announcement_date_et) == {"2025-08-14"},
            "source date is not original publication date")
    require(set(source.source_url) == {ORIGIN}, "source NBA press-release URL changed")
    found = tuples(source, ("game_date_et", "away_team", "home_team", "source_announced_network"))
    require(found == NAMED, "named 2025 original NBA broadcast fixture tuple changed")
    groups = {}
    for label, names in cup_groups.GROUPS["2025-26"].items():
        for team in names.split("|"):
            require(team not in groups, "duplicate original NBA Cup group member")
            groups[team] = label
    require(len(groups) == 30, "2025 original NBA group list incomplete")
    for r in source.itertuples(index=False):
        require(r.away_team in groups and r.home_team in groups and
                groups[r.away_team] == groups[r.home_team] and
                r.away_team != r.home_team,
                "named broadcast is not a 2025 Cup group fixture")
    networks = dict(Counter(source.source_announced_network))
    require(networks == {"Prime": 4, "NBC/Peacock": 2, "ESPN": 3},
            "2025 named broadcast provider breakdown")
    return {
        "status": "PASS_NINE_EXPLICIT_FIRST_PARTY_AUG14_BROADCASTS_ONLY",
        "original_2025_08_14_named_Cup_game_rows": 9,
        "network_breakdown": networks,
        "verified_source_release_date": "2025-08-14",
        "2025_08_13_entire_first_release_recovered": False,
        "2025_all_60_group_game_networks_checked": False,
        "all_18_Cup_knockout_game_networks_checked": False,
    }


def compare_original_archives(source: pd.DataFrame, cup_zip: Path, freeze_zip: Path) -> dict:
    """Perform actual 9-row source/Cup/main-season-PDF joins on ORIGINAL ZIP bytes."""
    verify_named_source(source)
    require(stream_hash.sha256_file(cup_zip) == cup_groups.ARCHIVE_SHA256,
            "original private Cup ZIP digest differs")
    require(stream_hash.sha256_file(freeze_zip) == tv_source.FREEZE_SHA,
            "original private full-frozen ZIP digest differs")

    with ZipFile(cup_zip) as z:
        original_cup = pd.read_csv(io.BytesIO(z.read(cup_groups.ARCHIVE_MEMBER)),
                                   keep_default_na=False, dtype=str)
    cup = original_cup.loc[
        original_cup.season.eq("2025-26") &
        original_cup.cup_stage.eq("group_play")
    ]
    require(len(cup) == 60 and not cup.duplicated(list(KEYS)).any(),
            "original 2025 private Cup group lookup not 60 distinct games")
    source_keys = tuples(source, KEYS)
    cup_keys = tuples(cup, KEYS)
    require(source_keys <= cup_keys, "at least one original named Cup source game missing")

    with ZipFile(freeze_zip) as outer:
        nested = outer.read(tv_source.TV_PACKAGE)
    require(sha256(nested).hexdigest() == tv_source.ORIGINAL_TV_PACKAGE_SHA,
            "nested frozen TV source ZIP digest differs")
    with ZipFile(io.BytesIO(nested)) as original:
        pdf_rows = pd.read_csv(io.BytesIO(original.read(
            tv_source.MODERN + "source_schedule_rows_2021_22_to_2025_26.csv")),
            keep_default_na=False, dtype=str)
    pdf_rows = pdf_rows.loc[pdf_rows.season.eq("2025-26")]
    require(len(pdf_rows) == 1200, "2025 original full-season source PDF not 1,200 rows")
    mapped = pdf_rows.rename(columns={
        "announced_date_et": "game_date_et",
        "announced_away_team": "away_team",
        "announced_home_team": "home_team",
        "network_announced": "source_announced_network",
    })
    require(not mapped.duplicated(list(KEYS)).any(), "duplicate 2025 NBA source PDF tuple")
    official_pdf = mapped.loc[
        mapped.loc[:, list(KEYS)].apply(tuple, axis=1).isin(source_keys)
    ]
    require(len(official_pdf) == 9 and tuples(official_pdf, COMPARE) == tuples(source, COMPARE),
            "at least one announced game/network differs from original later NBA PDF")
    return {
        "status": "PASS_NINE_ORIGINAL_PRIVATE_CUP_AND_TV_SOURCE_TUPLES",
        "source_Cup_game_tuples_exact": 9,
        "source_preseason_PDF_network_tuples_exact": 9,
        "all_60_first_release_2025_games_verified": False,
        "full_2025_Cup_2025_08_13_release_recovered": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-csv", type=Path, default=SOURCE)
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--original-cup-zip", type=Path)
    parser.add_argument("--original-freeze-zip", type=Path)
    parser.add_argument("--output-report", type=Path)
    args = parser.parse_args()
    require((args.source_only and not args.original_cup_zip and not args.original_freeze_zip)
            or (not args.source_only and args.original_cup_zip and args.original_freeze_zip),
            "use source-only without private ZIPs or supply BOTH original private ZIPs")
    frame = load_source(args.source_csv)
    report = verify_named_source(frame)
    if not args.source_only:
        report["private_comparison"] = compare_original_archives(
            frame, args.original_cup_zip, args.original_freeze_zip)
        report["status"] = "PASS_NINE_PRIVATE_SOURCE_TUPLES_ONLY"
    if args.output_report:
        require(not args.output_report.exists(), "refusing overwrite of original source evidence")
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        args.output_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
