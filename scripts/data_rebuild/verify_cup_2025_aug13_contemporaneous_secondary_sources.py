#!/usr/bin/env python3
"""Second-tier CONTEMPORANEOUS REPORTING (not NBA first-party) for Cup 2025.

Four ORIGINAL articles first published August 13, 2025 describe 16
team-perspective game appearances, 14 distinct West B/East B fixtures.
One source (Pelicans via Fox 8) was updated Aug 14: first publication date
alone CANNOT prove its four exact tuples were unchanged in that original
Aug 13 version. Preserve both provenance fields; report a conservative
11-row unmodified-date secondary subset and 3 additional qualified fixtures.

The five first-party NBA team releases separately establish 19 original
Aug 13 fixture tuples; this second-tier supplement does NOT increase that
original NBA first-party count, and source TV blanks mean UNKNOWN.
The full original NBA Aug 13 sixty-game Cup release remains unavailable.

Private acceptance requires an authentic SHA-pinned original Cup ZIP and
cannot be inferred from passing public CI tests or historical final scores.
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
    from scripts.data_rebuild import verify_official_NBA_cup_groups as cup
    from scripts.data_rebuild import verify_official_nba_cup_2025_aug13_team_press_sources as nba_first_party
    from scripts.data_rebuild import compare_nba_cup_exact_source_rows as exact_join
except ModuleNotFoundError:
    import verify_official_NBA_cup_groups as cup
    import verify_official_nba_cup_2025_aug13_team_press_sources as nba_first_party
    import compare_nba_cup_exact_source_rows as exact_join

ROOT = Path(__file__).resolve().parents[2]
SECONDARY = ROOT / "validation/nba_cup_2025_aug13_four_contemporaneous_secondary_reports.csv"
FIRST_PARTY = nba_first_party.DEFAULT_SOURCE
COLUMNS = (
    "season", "source_first_published_date", "source_updated_date_if_known",
    "reporting_team", "source_evidence_tier", "game_date_et", "away_team",
    "home_team", "source_positively_named_network", "source_url",
)
KEYS = ("season", "game_date_et", "away_team", "home_team")
ARTICLE = {
    "Los Angeles Lakers": (
        "https://www.silverscreenandroll.com/lakers-news/93107/lakers-nba-cup-schedule-dates-grizzlies-pelicans-clippers-mavericks",
        "contemporaneous_news", "", (
            ("2025-10-31","Los Angeles Lakers","Memphis Grizzlies","Prime"),
            ("2025-11-14","Los Angeles Lakers","New Orleans Pelicans",""),
            ("2025-11-25","LA Clippers","Los Angeles Lakers","NBC"),
            ("2025-11-28","Dallas Mavericks","Los Angeles Lakers","Prime"),
        )),
    "New Orleans Pelicans": (
        "https://www.wsfa.com/2025/08/14/new-orleans-pelicans-nba-cup-schedule-released/",
        "contemporaneous_news_updated_next_day", "2025-08-14", (
            ("2025-10-31","New Orleans Pelicans","LA Clippers",""),
            ("2025-11-14","Los Angeles Lakers","New Orleans Pelicans",""),
            ("2025-11-21","New Orleans Pelicans","Dallas Mavericks",""),
            ("2025-11-26","Memphis Grizzlies","New Orleans Pelicans",""),
        )),
    "Boston Celtics": (
        "https://www.cbsnews.com/boston/news/boston-celtics-nba-cup-schedule-amazon-prime/",
        "contemporaneous_news", "2025-08-13", (
            ("2025-10-31","Boston Celtics","Philadelphia 76ers","Prime"),
            ("2025-11-07","Boston Celtics","Orlando Magic",""),
            ("2025-11-21","Brooklyn Nets","Boston Celtics",""),
            ("2025-11-26","Detroit Pistons","Boston Celtics","ESPN"),
        )),
    "Philadelphia 76ers": (
        "https://sports.yahoo.com/article/sixers-schedule-nba-cup-group-181855855.html",
        "contemporaneous_syndicated_news", "", (
            ("2025-10-31","Boston Celtics","Philadelphia 76ers","Prime"),
            ("2025-11-14","Philadelphia 76ers","Detroit Pistons",""),
            ("2025-11-25","Orlando Magic","Philadelphia 76ers",""),
            ("2025-11-28","Philadelphia 76ers","Brooklyn Nets",""),
        )),
}
FIRST_DATE = "2025-08-13"
ALLOWED = {"WB", "EB"}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise ValueError("Contemporaneous secondary Cup 2025 source mismatch: " + msg)


def load(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, dtype=str)


def identities(frame: pd.DataFrame) -> set[tuple]:
    return set(frame.loc[:, list(KEYS)].itertuples(index=False, name=None))


def validate_sources(second: pd.DataFrame, first: pd.DataFrame) -> dict:
    nba_first_party.validate_source(first)
    require(tuple(second.columns) == COLUMNS, "unexpected secondary source schema")
    require(len(second) == 16, "four 2025 contemporary stories must supply 16 rows")
    require(not second.isna().any().any(), "implicit missing values in CSV")
    require(set(second.season) == {"2025-26"}, "invalid 2025 season")
    require(set(second.source_first_published_date) == {FIRST_DATE},
            "secondary sources not originally dated August 13")
    require(set(second.reporting_team) == set(ARTICLE),
            "unexpected reporter or missing second-tier article")

    team_group = {}
    for group, members in cup.GROUPS["2025-26"].items():
        for team in members.split("|"):
            require(team not in team_group, "same club in multiple original groups")
            team_group[team] = group
    require(len(team_group) == 30, "original official five-team NBA groups incomplete")

    counts = Counter()
    per_article = {}
    for reporter, (url,tier,updated,exact) in ARTICLE.items():
        article = second.loc[second.reporting_team.eq(reporter)]
        require(len(article) == 4, "not four club games in " + reporter)
        require(set(article.source_url) == {url} and
                set(article.source_evidence_tier) == {tier} and
                set(article.source_updated_date_if_known) == {updated},
                "source URL / source tier / revision date changed for " + reporter)
        found = set()
        homes = aways = 0
        for row in article.itertuples(index=False):
            require(reporter in (row.away_team, row.home_team),
                    "reporting team's schedule does not involve itself")
            require(row.away_team != row.home_team and
                    row.away_team in team_group and row.home_team in team_group and
                    team_group[row.away_team] == team_group[row.home_team] and
                    team_group[row.home_team] in ALLOWED,
                    "not a distinct same-group West B / East B opponent")
            found.add((row.game_date_et,row.away_team,row.home_team,
                       row.source_positively_named_network))
            counts[tuple(getattr(row,c) for c in KEYS)] += 1
            homes += row.home_team == reporter
            aways += row.away_team == reporter
        require(found == set(exact) and len(found)==4,
                "original secondary article exact date/host/network tuples differ for "+reporter)
        require(homes == 2 and aways == 2,
                "all four club games should have 2 home and 2 away for "+reporter)
        per_article[reporter] = {"game_rows": 4, "updated_after_first_date": bool(updated > FIRST_DATE)}

    require(len(counts)==14 and sum(counts.values())==16,
            "not 14 distinct secondary fixtures from 16 records")
    two_sources = {tuple(k) for k,v in counts.items() if v == 2}
    require(two_sources == {
        ("2025-26","2025-11-14","Los Angeles Lakers","New Orleans Pelicans"),
        ("2025-26","2025-10-31","Boston Celtics","Philadelphia 76ers"),
    }, "two cross-source duplicate game identifications absent/altered")
    require(all(v in (1,2) for v in counts.values()),
            "same fixture has more than two secondary mentions")
    require(Counter(second.source_positively_named_network) ==
            {"":10,"Prime":4,"NBC":1,"ESPN":1},
            "positive networks must be explicit and blanks remain unknown")

    first_keys=identities(first)
    second_keys=identities(second)
    require(first_keys.isdisjoint(second_keys) and len(first_keys)==19,
            "second-tier source overlaps or alters 19 original first-party rows")
    by_group = Counter()
    for s,date,away,home in second_keys:
        by_group[team_group[home]] += 1
    require(dict(by_group)=={"WB":7,"EB":7},
            "secondary West B / East B grouping coverage not seven each")
    next_day_only = {k for k,v in counts.items() if v==1 and
                     k in identities(second.loc[second.reporting_team.eq("New Orleans Pelicans")])}
    require(len(next_day_only)==3,
            "expected three Pelicans-only fixtures with next-day article revision caveat")
    return {
        "status":"PASS_AUG13_CONTEMPORANEOUS_SECOND_TIER_CUP_SOURCES",
        "original_NBA_Aug13_first_party_fixtures_unchanged":19,
        "second_tier_Aug13_first_dated_fixture_appearances":16,
        "second_tier_distinct_game_identities":14,
        "secondary_only_original_group_coverage":dict(by_group),
        "cross_report_duplicate_matches":2,
        "distinct_first_party_plus_secondary":33,
        "secondary_unique_with_no_known_next_day_revision":11,
        "secondary_unique_requiring_Aug13_pre_revision_evidence":3,
        "known_updated_next_day_article":"New Orleans Pelicans",
        "positive_broadcaster_mentions_are_NOT_complete_network_census":True,
        "unmentioned_networks_are_unknown_not_no_national_TV":True,
        "NBA_first_party_original_Aug13_schedule_coverage_still":19,
        "full_original_2025_Aug13_60_game_by_day_PDF_verified":False,
        "private_original_Cup_ZIP_exact_comparison_executed":False,
        "sources":per_article,
    }


def check_original_private(second: pd.DataFrame, first: pd.DataFrame, archive: Path) -> dict:
    validate_sources(second,first)
    require(sha256(archive.read_bytes()).hexdigest() == cup.ARCHIVE_SHA256,
            "original immutable Cup ZIP SHA-256 drift")
    with ZipFile(archive) as original:
        lookup=pd.read_csv(io.BytesIO(original.read(cup.ARCHIVE_MEMBER)),
                           low_memory=False,dtype=str,keep_default_na=False)
    require(len(lookup)==7230 and not lookup.game_id.duplicated().any(),
            "original six-season Cup game inventory not 7,230 unique games")
    originals=lookup.loc[lookup.season.eq("2025-26") & lookup.cup_stage.eq("group_play")]
    require(len(originals)==60 and not originals.duplicated(list(KEYS)).any(),
            "original private 2025 Cup group stage not 60 unique games")
    combined = pd.concat([first, second], ignore_index=True)
    unique_source = combined.drop_duplicates(list(KEYS))
    exact_join.exact_group_fixture_join(
        unique_source, originals, expected=33, subset=True
    )
    return {
        "status":"PASS_ORIGINAL_PRIVATE_CUP_33_CONTEMPORANEOUS_FIXTURE_IDENTITIES",
        "independently_transcribed_source_date_host_away_tuples_in_original_Cup":33,
        "sources_first_party":19,
        "sources_contemporaneous_secondary":14,
        "updated_next_day_secondary_exceptions_still_present":3,
        "original_NBA_first_release_full_60_rows_verified":False,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--secondary-csv",type=Path,default=SECONDARY)
    p.add_argument("--original-first-party-csv",type=Path,default=FIRST_PARTY)
    p.add_argument("--source-only",action="store_true")
    p.add_argument("--original-cup-zip",type=Path)
    p.add_argument("--output-report",type=Path)
    args=p.parse_args()
    require((args.source_only and not args.original_cup_zip) or
            (not args.source_only and args.original_cup_zip is not None),
            "use --source-only without ZIP OR an original source-pinned Cup ZIP")
    second,first=load(args.secondary_csv),nba_first_party.load_source(args.original_first_party_csv)
    report=validate_sources(second,first)
    if not args.source_only:
        report["private_original"]=check_original_private(second,first,args.original_cup_zip)
        report["status"]="PASS_PRIVATE_CUP_33_TUPLE_SOURCE_COMPARISON_WITH_NEXT_DAY_LIMIT"
    if args.output_report:
        require(not args.output_report.exists(),"refuse overwrite of original scientific evidence")
        args.output_report.parent.mkdir(parents=True,exist_ok=True)
        args.output_report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
