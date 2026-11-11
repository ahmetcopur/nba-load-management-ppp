#!/usr/bin/env python3
"""A prospective-information provenance matrix, NOT retrospective TV backfill.

Cross-check independently verified public 2025 NBA Cup inputs:
  (1) Five original NBA team news articles dated 2025-08-13: 19 fixtures
  (2) Four second-tier news reports first dated 2025-08-13: 14 fixtures
      (three uniquely tied only to an article edited on Aug 14)
  (3) NBA Communications original Aug 14 named nine TV games
  (4) NBA.com article updated Aug 21 listing all 15 national group games

For each of 15 nationally carried games, distinguish the date the MATCHUP
was demonstrably published and the date a SPECIFIC NETWORK was independently
named. All 15 were eventually televised nationally, but that truth must NEVER
be backfilled into the original Aug 13 matchup-specific TV treatment. Blank
networks in an individual first-release article mean UNREPORTED/UNKNOWN.

This is a public source-reconciliation audit. Original frozen research TV
treatment/fixture files are not opened, compared, edited or certified here.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

try:
    from scripts.data_rebuild import verify_cup_2025_aug13_contemporaneous_secondary_sources as secondary
    from scripts.data_rebuild import verify_official_nba_cup_2025_aug13_team_press_sources as first_party
    from scripts.data_rebuild import verify_official_nba_cup_2025_all_15_national_broadcasts as national
    from scripts.data_rebuild import verify_official_nba_cup_2025_named_broadcasts as aug14
except ModuleNotFoundError:
    import verify_cup_2025_aug13_contemporaneous_secondary_sources as secondary
    import verify_official_nba_cup_2025_aug13_team_press_sources as first_party
    import verify_official_nba_cup_2025_all_15_national_broadcasts as national
    import verify_official_nba_cup_2025_named_broadcasts as aug14

DATE_FIRST = "2025-08-13"
DATE_NINE = "2025-08-14"
DATE_ALL = "2025-08-21"
KEYS = ("season", "game_date_et", "away_team", "home_team")


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise ValueError("NBA Cup 2025 publication-time TV matrix mismatch: " + msg)


def key(record) -> tuple:
    return tuple(str(getattr(record, c)) for c in KEYS)


def verify(
    original_team,
    contemporaneous_news,
    aug14_nine,
    aug21_fifteen,
) -> dict:
    secondary.validate_sources(contemporaneous_news, original_team)
    national.validate_15(aug21_fifteen, aug14_nine)

    first_map={}
    for row in original_team.itertuples(index=False):
        k=key(row)
        first_map.setdefault(k, set()).add(row.positively_named_network)
    second_map={}
    edited_only=set()
    for row in contemporaneous_news.itertuples(index=False):
        k=key(row)
        second_map.setdefault(k, set()).add(row.source_positively_named_network)
    # A game is "edited only" when its one and only second-tier citation is
    # the Pelicans story, first dated Aug 13 but later edited on Aug 14.
    for row in contemporaneous_news.itertuples(index=False):
        k=key(row)
        if row.reporting_team == "New Orleans Pelicans" and (
            sum(key(other)==k for other in contemporaneous_news.itertuples(index=False)) == 1
        ):
            edited_only.add(k)

    national_rows={key(row):row for row in aug21_fifteen.itertuples(index=False)}
    earlier_keys={key(row) for row in aug14_nine.itertuples(index=False)}
    require(len(national_rows)==15 and len(earlier_keys)==9,
            "named network source cardinalities")
    require(earlier_keys<=set(national_rows),"original nine not inside later 15")

    positive_on_first=set()
    source_overlap=set()
    earliest={}
    output=[]
    for k, row in sorted(national_rows.items()):
        first=k in first_map
        second=k in second_map
        is_known=first or second
        if is_known: source_overlap.add(k)
        raw_nets=(first_map.get(k,set())|second_map.get(k,set()))-{"",}
        canonical={("NBC/Peacock" if network=="NBC" else network)
                   for network in raw_nets}
        require(len(canonical)<=1,"conflicting Aug 13 positively published networks")
        reported=next(iter(canonical),"UNKNOWN_IN_AUG13_FIXTURE_SOURCE")
        assert row.source_announced_network in {"Prime","ESPN","NBC/Peacock"}
        if canonical:
            require(reported==row.source_announced_network,
                    "original Aug 13 positively published network disagrees with NBA Aug 21")
            positive_on_first.add(k)
            known_by=DATE_FIRST
        else:
            known_by=DATE_NINE if k in earlier_keys else DATE_ALL
        earliest[known_by]=earliest.get(known_by,0)+1
        output.append({
            "game_date_et":row.game_date_et,
            "away_team":row.away_team,
            "home_team":row.home_team,
            "national_network_as_confirmed_by_Aug_21":row.source_announced_network,
            "matchup_in_original_Aug_13_NBA_team_first_party":first,
            "matchup_in_Aug_13_first_dated_secondary_news":second,
            "secondary_first_date_article_edited_next_day_only":k in edited_only,
            "specific_national_network_positively_named_in_Aug_13_article":bool(canonical),
            "positive_Aug_13_network_if_any":reported,
            "earliest_network_independently_verified_by_date":known_by,
            "in_original_Aug14_NBA_Communications_named_nine":k in earlier_keys,
        })

    require(len(source_overlap)==9,
            "expected 9 exact national games to overlap 33 contemporaneous fixtures")
    require(len(positive_on_first)==6,
            "only six of overlapping 9 network assignments positively named Aug 13")
    require(earliest=={DATE_FIRST:6,DATE_NINE:4,DATE_ALL:5},
            "separate earliest named-network chronology not 6/4/5")
    require(Counter((r["matchup_in_original_Aug_13_NBA_team_first_party"],
                     r["matchup_in_Aug_13_first_dated_secondary_news"])
                    for r in output) == {(True,False):3,(False,True):6,(False,False):6},
            "strict separation of 3 original, 6 second-tier, 6 not in either date fixture source")
    return {
        "status":"PASS_PUBLIC_2025_CUP_NATIONAL_GAME_AND_NETWORK_RELEASE_TIMING_EVIDENCE",
        "national_2025_Cup_group_games_in_NBA_com_later_source":15,
        "National_games_with_Aug13_first_dated_fixture_evidence":9,
        "of_those_aug13_source_NBA_first_party":3,
        "of_those_aug13_source_secondary":6,
        "national_games_without_Aug13_game_specific_source":6,
        "named_network_verified_by_Aug13_sources":6,
        "named_network_only_verified_by_Aug14_NBA_announcement_not_Aug13_sources":4,
        "named_network_only_verified_by_Aug21_NBA_later_article":5,
        "network_first_verified_by_date_counts":earliest,
        "original_Aug13_NBA_group_first_release_60_game_binary_recovered":False,
        "original_private_Cup_or_TV_archives_compared":False,
        "all_2025_Cup_national_actual_broadcasts_preknown_as_Aug13_opponent_specific":False,
        "per_national_game_evidence":output,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-report",type=Path)
    args=p.parse_args()
    report=verify(
        first_party.load_source(first_party.DEFAULT_SOURCE),
        secondary.load(secondary.SECONDARY),
        aug14.load_source(aug14.SOURCE),
        national.load(national.SOURCE),
    )
    if args.output_report:
        require(not args.output_report.exists(),"refuse overwriting previous source evidence")
        args.output_report.parent.mkdir(parents=True,exist_ok=True)
        args.output_report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
