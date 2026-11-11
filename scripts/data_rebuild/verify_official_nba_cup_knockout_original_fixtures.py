#!/usr/bin/env python3
"""Independently verify NBA Cup 2023-25 knockout date/opponents/provider.

Original first-party NBA quarterfinal, semifinal and result articles are
linked per record in validation/official_nba_cup_2023_2025_eighteen_knockout_fixture_sources.csv.

KEY SCIENTIFIC DISTINCTIONS:
* Official NBA tournament result articles validate the actual 18 opponents,
  dates and winners, NOT historical first-announcement dates.
* Twelve quarterfinal games were hosted in higher-seed home arenas. Six
  semifinals played in Las Vegas as NEUTRAL site. Do NOT invent source
  home/away designations for those six; the original private league game log
  may encode a nominal home team even at a neutral site.
* Before knockout qualifiers were determined, broadcasters announced TV
  stage slots with opponents TBD. This cannot be retrospectively backfilled
  as an advance-known opponent TV assignment.
* The original three championships are NOT regular-season games.

Optional strict original private Cup ZIP check compares all 18 season/date/
stage/UNORDERED-opponent tuples and all 12 quarterfinal HOME/AWAY fixtures.
Semifinal nominal home/away correctness remains unverified. Outputs aggregate
counts only; no private original player-level records may be committed.
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
    from scripts.data_rebuild import verify_official_NBA_cup_groups as original
    from scripts.data_rebuild import compare_nba_cup_exact_source_rows as exact_join
except ModuleNotFoundError:
    import verify_official_NBA_cup_groups as original
    import compare_nba_cup_exact_source_rows as exact_join

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "validation/official_nba_cup_2023_2025_eighteen_knockout_fixture_sources.csv"
COLUMNS = (
    "season", "game_date_et", "cup_stage", "away_team", "home_team",
    "participant_1", "participant_2", "winner", "game_network",
    "fixture_provider_documented_by_date", "fixture_provider_source_url",
    "result_source_url", "neutral_site",
)

# Every exact record independently read from dated NBA.com sources. Distinct
# hard-coded original public reference prevents row-swaps from passing due
# to stage/date/network aggregate preservation.
# (season, date, stage, AWAY if quarterfinal, HOME if quarterfinal,
#  two unordered participants, actual winner, network).
A = "Atlanta Hawks"; BOS = "Boston Celtics"; DAL = "Dallas Mavericks"
GSW = "Golden State Warriors"; HOU = "Houston Rockets"
IND = "Indiana Pacers"; LAL = "Los Angeles Lakers"
MIA = "Miami Heat"; MIL = "Milwaukee Bucks"
NOP = "New Orleans Pelicans"; NYK = "New York Knicks"
OKC = "Oklahoma City Thunder"; ORL = "Orlando Magic"
PHX = "Phoenix Suns"; SAC = "Sacramento Kings"
SAS = "San Antonio Spurs"; TOR = "Toronto Raptors"

EXPECTED = {
    ("2023-24","2023-12-04","quarterfinal",BOS,IND,BOS,IND,IND,"TNT"),
    ("2023-24","2023-12-04","quarterfinal",NOP,SAC,NOP,SAC,NOP,"TNT"),
    ("2023-24","2023-12-05","quarterfinal",NYK,MIL,MIL,NYK,MIL,"TNT"),
    ("2023-24","2023-12-05","quarterfinal",PHX,LAL,LAL,PHX,LAL,"TNT"),
    ("2023-24","2023-12-07","semifinal","","",IND,MIL,IND,"ESPN"),
    ("2023-24","2023-12-07","semifinal","","",LAL,NOP,LAL,"TNT"),
    ("2024-25","2024-12-10","quarterfinal",ORL,MIL,MIL,ORL,MIL,"TNT"),
    ("2024-25","2024-12-10","quarterfinal",DAL,OKC,DAL,OKC,OKC,"TNT"),
    ("2024-25","2024-12-11","quarterfinal",A,NYK,A,NYK,A,"ESPN"),
    ("2024-25","2024-12-11","quarterfinal",GSW,HOU,GSW,HOU,HOU,"TNT"),
    ("2024-25","2024-12-14","semifinal","","",A,MIL,MIL,"TNT"),
    ("2024-25","2024-12-14","semifinal","","",HOU,OKC,OKC,"ABC"),
    ("2025-26","2025-12-09","quarterfinal",MIA,ORL,MIA,ORL,ORL,"Prime"),
    ("2025-26","2025-12-09","quarterfinal",NYK,TOR,NYK,TOR,NYK,"Prime"),
    ("2025-26","2025-12-10","quarterfinal",PHX,OKC,OKC,PHX,OKC,"Prime"),
    ("2025-26","2025-12-10","quarterfinal",SAS,LAL,LAL,SAS,SAS,"Prime"),
    ("2025-26","2025-12-13","semifinal","","",NYK,ORL,NYK,"Prime"),
    ("2025-26","2025-12-13","semifinal","","",OKC,SAS,SAS,"Prime"),
}
REQUIRED_BY_STAGE = {"quarterfinal": 4, "semifinal": 2}


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("NBA Cup independently sourced knockout mismatch: " + why)


def load(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, dtype=str)


def source_signature(row) -> tuple:
    p1, p2 = sorted((row.participant_1, row.participant_2))
    return (row.season, row.game_date_et, row.cup_stage, row.away_team,
            row.home_team, p1, p2, row.winner, row.game_network)


def source_identity(row) -> tuple:
    p1, p2 = sorted((row.participant_1, row.participant_2))
    return (row.season, row.game_date_et, row.cup_stage, p1, p2)


def validate_original_source(frame: pd.DataFrame) -> dict:
    require(tuple(frame.columns) == COLUMNS, "original source schema changed")
    require(len(frame) == 18, "original 18 games incomplete")
    require(not frame.loc[:, list(COLUMNS)].isna().any().any(),
            "source fields contain NaN instead of explicit blank")
    require({source_signature(r) for r in frame.itertuples(index=False)} == EXPECTED,
            "one or more source-identical NBA opponent/date/winner/provider tuples changed")
    require(len(EXPECTED) == 18, "reference itself does not have 18 games")

    details={}
    for season, season_rows in frame.groupby("season"):
        require(season in original.DATES and season in original.GROUPS,
                "unrecognized NBA Cup official group-season")
        require(len(season_rows) == 6 and
                season_rows.cup_stage.value_counts().to_dict() == REQUIRED_BY_STAGE,
                f"{season} stage must be 4 quarterfinal and 2 semifinal")
        stage_dates = {k: set(v.split("|")) for k,v in original.DATES[season].items()}
        require(set(season_rows.loc[season_rows.cup_stage.eq("quarterfinal"),"game_date_et"]) ==
                stage_dates["quarterfinal"] and
                set(season_rows.loc[season_rows.cup_stage.eq("semifinal"),"game_date_et"]) ==
                stage_dates["semifinal"], f"{season} original NBA stage night dates differ")

        for r in season_rows.itertuples(index=False):
            require(r.winner in (r.participant_1,r.participant_2),
                    f"{season} named NBA game winner not among competitors")
            require(r.fixture_provider_documented_by_date <= r.game_date_et,
                    f"{season} NBA source published AFTER game does not establish pregame broadcast")
            require(r.fixture_provider_documented_by_date.startswith(season[:4])
                    or r.fixture_provider_documented_by_date.startswith(str(int(season[:4])+1)),
                    f"{season} implausible original source date")
            require(r.fixture_provider_source_url.startswith("https://www.nba.com/") and
                    r.result_source_url.startswith("https://www.nba.com/"),
                    f"{season} not official NBA.com source record")
            if r.cup_stage=="quarterfinal":
                require(r.neutral_site=="False" and
                        set((r.away_team,r.home_team)) ==
                        set((r.participant_1,r.participant_2)) and
                        r.away_team != r.home_team,
                        f"{season} ordinary quarterfinal home-market designation wrong")
            else:
                require(r.neutral_site=="True" and not r.away_team and not r.home_team,
                        f"{season} NEUTRAL semifinal cannot have an inferred home team")

        details[season]={
            "official_QF_actual_matchups_and_home_markets":4,
            "official_neutral_site_semifinal_actual_opponent_pairs":2,
            "per_game_realized_broadcast_sources":dict(
                Counter(season_rows.game_network)),
        }
    require(set(details)=={"2023-24","2024-25","2025-26"},
            "all three official original knockout seasons required")
    require(len({source_identity(r) for r in frame.itertuples(index=False)}) == 18,
            "source tuple duplicates")
    return {
        "status":"PASS_18_FIRST_PARTY_ACTUAL_KNOCKOUT_MATCHUPS_AND_BROADCAST_SOURCES",
        "official_original_QF_game_date_away_home_exact_public":12,
        "official_original_neutral_semifinal_date_unordered_pair_exact_public":6,
        "official_original_realized_knockout_networks_sourced":18,
        "seasons":details,
        "neutral_semifinal_nominal_home_team_independently_proven":False,
        "all_18_first_matchup_announcements_dated_at_initial_preseason_release":False,
        "original_private_Cup_game_lookup_actual_reconciliation_run":False,
        "all_three_championships_intentionally_excluded":True,
    }


def compare_original_private(frame: pd.DataFrame, archive_path: Path) -> dict:
    validate_original_source(frame)
    require(sha256(archive_path.read_bytes()).hexdigest() == original.ARCHIVE_SHA256,
            "original private Cup archive full SHA-256 mismatch")
    with ZipFile(archive_path) as z:
        lookup = pd.read_csv(io.BytesIO(z.read(original.ARCHIVE_MEMBER)),
                             low_memory=False,dtype=str,keep_default_na=False)
    require(len(lookup)==7230 and not lookup.game_id.duplicated().any(),
            "original private Cup research fixture inventory not 7,230 unique games")
    knockout = lookup.loc[lookup.cup_stage.isin(REQUIRED_BY_STAGE)]
    require(len(knockout)==18,"original private Cup stage rows not 18")

    # Independent exact-row comparator is now positively exercised with
    # synthetic original lookup frames, including wrong stage/date/teams,
    # false quarterfinal host direction and neutral semifinal source limits.
    # Original private ZIP digest and full 7,230 lookup checks above remain
    # mandatory before a user can claim an actual archive PASS.
    exact_join.exact_knockout_fixture_join(frame, knockout)

    return {
        "status":"PASS_18_ORIGINAL_CUP_ARCHIVE_DATE_UNORDERED_OPPONENTS_AND_12_QF_HOME_AWAY",
        "original_source_Cup_ZIP_SHA256":original.ARCHIVE_SHA256,
        "original_knockout_season_date_stage_opponent_pairs_exact":18,
        "original_quarterfinal_home_away_source_rows_exact":12,
        "neutral_site_semifinal_archive_nominal_home_away_independently_proven":False,
        "archive_first_announcement_time_or_network_independently_recovered":False,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-csv",type=Path,default=SOURCE)
    p.add_argument("--source-only",action="store_true")
    p.add_argument("--original-cup-zip",type=Path)
    p.add_argument("--output-report",type=Path)
    args=p.parse_args()
    require((args.source_only and not args.original_cup_zip)
            or (not args.source_only and args.original_cup_zip is not None),
            "use source-only without ZIP, or supply exact private original Cup ZIP")
    frame=load(args.source_csv)
    report=validate_original_source(frame)
    if not args.source_only:
        report["original_private_reconciliation"]=compare_original_private(frame,args.original_cup_zip)
        report["status"]="PASS_PUBLIC_AND_PRIVATE_KNOCKOUT_DATES_OPPONENTS_QF_HOSTS_ONLY"
    if args.output_report:
        require(not args.output_report.exists(),"refusing overwrite of existing scientific evidence")
        args.output_report.parent.mkdir(parents=True,exist_ok=True)
        args.output_report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
