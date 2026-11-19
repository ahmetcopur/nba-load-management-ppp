#!/usr/bin/env python3
"""Independent 2025 NBA Cup 60-game Nov 1 ESPN editorial source comparison.

ESPN's November 1, 2025 NBA Cup article republishes all 60 group game
dates, visitors, home teams and 15 positively identified broadcasts.
https://abc7ny.com/post/2025-nba-cup-schedule-format-groups-updates-more/18031782/

This is an **independent later ESPN/ABC7 source**, NOT the still-unrecovered
original NBA Aug 13 by-day official PDF and NOT a first-release timestamp.
A game in this November article cannot itself prove an August announcement.

Strictly cross-check all 60 dates + home/away + five-team group membership
and 2-home/2-away, plus the previously sourced NBA Aug13 first-party 19,
Aug13 first-dated secondary 14 (with article edit caveats), and NBA by
Aug21 official national 15 network labels. Blank ESPN article TV labels
remain UNREPORTED/UNKNOWN, not verified non-national.
No real private research archive is read or accepted by this public check.
"""
from __future__ import annotations

import argparse
from collections import Counter
from zipfile import ZipFile
import io
import json
from pathlib import Path

import pandas as pd

try:
    from scripts.data_rebuild import verify_official_NBA_cup_groups as cup
    from scripts.data_rebuild import verify_official_nba_cup_2025_aug13_team_press_sources as aug13_nba
    from scripts.data_rebuild import verify_cup_2025_aug13_contemporaneous_secondary_sources as aug13_secondary
    from scripts.data_rebuild import verify_official_nba_cup_2025_named_broadcasts as aug14_nine
    from scripts.data_rebuild import verify_official_nba_cup_2025_all_15_national_broadcasts as nba15
    from scripts.data_rebuild import compare_nba_cup_exact_source_rows as exact_join
    from scripts.data_rebuild import hash_original_archive_streaming as stream_hash
except ModuleNotFoundError:
    import verify_official_NBA_cup_groups as cup
    import verify_official_nba_cup_2025_aug13_team_press_sources as aug13_nba
    import verify_cup_2025_aug13_contemporaneous_secondary_sources as aug13_secondary
    import verify_official_nba_cup_2025_named_broadcasts as aug14_nine
    import verify_official_nba_cup_2025_all_15_national_broadcasts as nba15
    import compare_nba_cup_exact_source_rows as exact_join
    import hash_original_archive_streaming as stream_hash

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"validation/nba_cup_2025_nov01_espn_editorial_60_group_fixtures.csv"
ORIGIN="https://abc7ny.com/post/2025-nba-cup-schedule-format-groups-updates-more/18031782/"
COLUMNS=("season","source_publication_date","game_date_et","away_team","home_team",
         "positively_named_network","source_url")
KEY=("season","game_date_et","away_team","home_team")
DAY_COUNTS={"2025-10-31":8,"2025-11-07":11,"2025-11-14":9,"2025-11-21":9,
            "2025-11-25":3,"2025-11-26":9,"2025-11-28":11}
NETWORK_COUNTS={"Prime":10,"Peacock":2,"ESPN":3,"":45}


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("2025 ESPN later editorial Cup exact source mismatch: "+why)


def load(path: Path) -> pd.DataFrame:
    return pd.read_csv(path,keep_default_na=False,dtype=str)


def keys(frame: pd.DataFrame) -> set[tuple]:
    require(all(name in frame.columns for name in KEY),
            "a source fixture identity column is missing")
    return set(frame.loc[:,list(KEY)].itertuples(index=False,name=None))


def verify(espn: pd.DataFrame, first: pd.DataFrame,
           second: pd.DataFrame, nine: pd.DataFrame,
           national: pd.DataFrame) -> dict:
    aug13_secondary.validate_sources(second,first)
    nba15.validate_15(national,nine)
    require(tuple(espn.columns)==COLUMNS,"ESPN source fixture CSV schema")
    require(len(espn)==60,"independent later ESPN source does not have 60 group fixtures")
    require(not espn.isna().any().any(),"unexpected implicit blank/null source fields")
    require(set(espn.season)=={"2025-26"},"wrong NBA 2025 Cup season")
    require(set(espn.source_publication_date)=={"2025-11-01"},
            "later editorial publication date falsely backdated")
    require(set(espn.source_url)=={ORIGIN},"source is not original ESPN/ABC7 URL")
    require(not espn.duplicated(list(KEY)).any(),"duplicate 2025 Cup source game")
    require(Counter(espn.game_date_et)==Counter(DAY_COUNTS),
            "independent ESPN Cup calendar day allocation drift")
    require(Counter(espn.positively_named_network)==Counter(NETWORK_COUNTS),
            "independently reported ESPN Cup national network counts drift")

    team_group={}
    expected_pairs=set()
    home,away=Counter(),Counter()
    for group,members in cup.GROUPS["2025-26"].items():
        all_teams=members.split("|")
        for t in all_teams:
            require(t not in team_group,"duplicate original NBA Cup group membership")
            team_group[t]=group
        for i,t in enumerate(all_teams):
            for opponent in all_teams[i+1:]:
                expected_pairs.add((group,*sorted((t,opponent))))
    require(len(team_group)==30 and len(expected_pairs)==60,
            "original NBA Cup 2025 official group draw incomplete")
    source_pairs=set()
    for r in espn.itertuples(index=False):
        require(r.away_team in team_group and r.home_team in team_group,
                "ESPN source uses unrecognized NBA club")
        require(r.away_team!=r.home_team and team_group[r.away_team]==team_group[r.home_team],
                "ESPN lists out-of-group NBA Cup 2025 opponents")
        p=(team_group[r.home_team],*sorted((r.away_team,r.home_team)))
        require(p not in source_pairs,"repeated same-group opponent pair")
        source_pairs.add(p)
        home[r.home_team]+=1
        away[r.away_team]+=1
    require(source_pairs==expected_pairs,
            "ESPN later schedule does not have every official unique group matchup")
    require(all(home[team]==2 and away[team]==2 for team in team_group),
            "one of 30 clubs not exactly two home and two away")

    all_keys=keys(espn)
    original_keys=keys(first)
    contemporary_keys=keys(second)
    require(len(original_keys)==19 and original_keys<=all_keys,
            "not all 19 original NBA Aug13 press fixtures match later ESPN schedule")
    require(len(contemporary_keys)==14 and contemporary_keys<=all_keys,
            "not all 14 separate Aug13 secondary fixtures match later ESPN schedule")
    require(original_keys.isdisjoint(contemporary_keys),
            "original first-party and secondary coverage unexpectedly overlaps")
    nba_keys=keys(national)
    require(len(nba_keys)==15 and nba_keys<=all_keys,
            "a nationally listed 2025 Cup game is missing from later ESPN fixture list")

    advertised={}
    for r in espn.itertuples(index=False):
        if r.positively_named_network:
            advertised[(r.season,r.game_date_et,r.away_team,r.home_team)]=r.positively_named_network
    require(len(advertised)==15,"unexpected positive network row count")
    for r in national.itertuples(index=False):
        k=(r.season,r.game_date_et,r.away_team,r.home_team)
        label=advertised.get(k)
        # NBA explicitly described NBCUniversal as NBC/Peacock; the later
        # ABC7 schedule lists its two November Tuesday games as Peacock.
        normalized="NBC/Peacock" if label=="Peacock" else label
        require(normalized==r.source_announced_network,
                "later ESPN published national network differs from original NBA.com "
                f"named 15 for {r.game_date_et}")

    return {
        "status":"PASS_2025_ESPNAUTHORED_NOV01_60_GROUP_SOURCE_CROSSCHECK_ONLY",
        "2025_original_NBA_Cup_first_Aug13_PDF_recovered":False,
        "2025_later_ESPN_editorial_complete_group_fixtures_exact":60,
        "source_editorial_date":"2025-11-01",
        "ESPN_group_matchups_and_dates":DAY_COUNTS,
        "all_30_teams_two_home_two_away":True,
        "original_Aug13_NBA_team_first_party_fixtures_crosschecked":19,
        "additional_Aug13_first_dated_secondary_source_fixtures_crosschecked":14,
        "secondary_next_day_edited_article_fixture_caveats_still_unresolved":3,
        "NBA_named_national_source_fixture_and_network_matches":15,
        "ESPN_article_positive_named_broadcast_counts":NETWORK_COUNTS,
        "blank_ESPN_article_network_means":"UNREPORTED_NOT_VERIFIED_NEGATIVE",
        "original_2025_full_60_first_release_networks_independently_checked":False,
        "original_private_NBA_Cup_archive_60_rows_checked":False,
    }



def compare_original_private_later_60(espn: pd.DataFrame,
                                      first: pd.DataFrame,
                                      second: pd.DataFrame,
                                      nine: pd.DataFrame,
                                      national: pd.DataFrame,
                                      original_cup_zip: Path) -> dict:
    """After full SHA pin, compare all 60 later ESPN game tuples to original Cup.

    This must NOT be interpreted as validation of the missing August 13
    original NBA Cup first-release binary or its first-published networks.
    """
    verify(espn,first,second,nine,national)
    require(stream_hash.sha256_file(original_cup_zip)==cup.ARCHIVE_SHA256,
            "original private Cup ZIP full SHA-256 mismatch")
    with ZipFile(original_cup_zip) as archive:
        lookup=pd.read_csv(io.BytesIO(archive.read(cup.ARCHIVE_MEMBER)),
                           dtype=str,keep_default_na=False,low_memory=False)
    require(len(lookup)==7230 and not lookup.game_id.duplicated().any(),
            "original six-season Cup game research lookup not 7,230 distinct games")
    original=lookup.loc[lookup.season.eq("2025-26") &
                        lookup.cup_stage.eq("group_play")]
    require(len(original)==60,
            "original private 2025 Cup group-play game rows not exactly 60")
    exact_join.exact_group_fixture_join(espn,original,expected=60)
    return {
        "status":"PASS_PRIVATE_CUP_2025_ALL_60_LATER_ESPN_GROUP_FIXTURE_ROWS",
        "original_Cup_source_ZIP_SHA256":cup.ARCHIVE_SHA256,
        "later_ESPN_2025_group_fixture_date_away_home_original_private_matches":60,
        "NBA_original_aug13_complete_first_release_independently_recovered":False,
        "original_aug13_network_treatment_certified":False,
        "source_editorial_publication_date":"2025-11-01",
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-csv",type=Path,default=SOURCE)
    parser.add_argument("--original-cup-zip",type=Path)
    parser.add_argument("--output-report",type=Path)
    a=parser.parse_args()
    report=verify(
        load(a.source_csv),
        aug13_nba.load_source(aug13_nba.DEFAULT_SOURCE),
        aug13_secondary.load(aug13_secondary.SECONDARY),
        aug14_nine.load_source(aug14_nine.SOURCE),
        nba15.load(nba15.SOURCE),
    )
    if a.original_cup_zip:
        report["private_original_comparison"]=compare_original_private_later_60(
            load(a.source_csv),
            aug13_nba.load_source(aug13_nba.DEFAULT_SOURCE),
            aug13_secondary.load(aug13_secondary.SECONDARY),
            aug14_nine.load_source(aug14_nine.SOURCE),
            nba15.load(nba15.SOURCE),
            a.original_cup_zip
        )
        report["status"]="PASS_PRIVATE_2025_LATER_ESPN_ALL_60_FIXTURES_ONLY"
    if a.output_report:
        require(not a.output_report.exists(),"do not overwrite a previous source report")
        a.output_report.parent.mkdir(parents=True,exist_ok=True)
        a.output_report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
