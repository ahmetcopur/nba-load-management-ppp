#!/usr/bin/env python3
"""Independently re-extract original NBA advance-announced broadcast schedules.

Source data: original NBA preseason by-date PDFs (2021–22 through 2025–26)
and original 2020–21 ESPN/ABC, Warner Bros. Discovery TNT/NBA TV press HTML.
The original research broadcast-source and final fixture tables are used ONLY
for exact field-wise acceptance checks, never to generate source TV labels.

This verifier requires two immutable private archive packages and emits
ONLY aggregate counts and SHA-256s; it must never commit player-level
injury records or individual broadcast source schedule rows.

Limitations: original 2020–21 second-half NBA TV HTML is a highlights
page without a complete game table; leave its missing classifications
UNKNOWN, not zero. The 90 2023–25 Cup-determined matchups are not known
at the preseason schedule release. Matching played fixtures to original
announcements and correctness of source archive collection are separate
provenance assumptions, checked here only for internal mapping consistency.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import io
import json
from pathlib import Path
import re
from zipfile import ZipFile

import pandas as pd

INVENTORY_SHA = "365e86f47078b093585445ab8dd6143b74b14df3afdfc1af4e4f063305823d1f"
FREEZE_SHA = "621ebcd45f2fe886ae87749e9d45b6b8416cfc8fcad5edb3e50a8c4486f670e1"
ORIGINAL_TV_PACKAGE_SHA = "13c6a13bace590e4116046f3258d666c1c62e0768a910051bca7883429078867"
TV_PACKAGE = "nba_load_management_final_freeze_2026-08-12/packages/03_announced_tv_six_seasons.zip"
BASE = "nba_announced_tv_six_seasons_v1/"
MODERN = BASE + "seasons_2021_22_to_2025_26_audit/"
LEGACY = BASE + "season_2020_21_audit/"
BROADCAST_PDF_SHA = {
    "2021-22": "bbfb82f61ccd23714b61c78ce0dcabdf2b64d67655590fcfaeffb176b9b2e027",
    "2022-23": "f98d5b6273d3c7793a74b356f1fceba1f1a47656572b2825645bf5794ac9ef81",
    "2023-24": "7e31cf6d8ca00f92fab8b28bd973b90d0f2c4f6beead11bcf4e487f9e63ed29a",
    "2024-25": "a6ad5d18e773d24d885c5b376df6d7fc44578590996e679f611049fc3b9687f0",
    "2025-26": "98a06493d0a107cc410853ad230e67d48858777a2baf76ac77d089cbeaf2435d",
}
BROADCAST_HTML_SHA = {
    "espn_abc_first": "ad8d3332882037a27e469a51270ef874d1c51782be4532838f9799c47f08af73",
    "espn_abc_second": "a47e5fc96c579f7bfb0af90beaa89a2ba378b01265bc811a8a388205e537ac3a",
    "tnt_first": "50edda58484c5ddc6f69bf7fc90e86fc2c9a9c2a1b3276122d7235568c90a0f6",
    "tnt_second": "5301ae5b894f2ba9d7b63c8aeea8f3821ae3e49d4052d0e8c6916e6507787367",
    "nbatv_first": "bd5985b91e4a96fa96c92528bbbf8f23496264a19e2b139f1403b4192942f288",
    "nbatv_second": "e124eba45fea2d0ceb2420b12f58f5f50fcd3cfdddf1cb37ad20ecbc616ef366",
}
OFFICIAL_RELEASES = {
    "2021-22": "https://pr.nba.com/2021-22-nba-schedule-75th-anniversary-season/",
    "2022-23": "https://pr.nba.com/2022-23-nba-schedule/",
    "2023-24": "https://pr.nba.com/2023-24-nba-regular-season-schedule/",
    "2024-25": "https://pr.nba.com/2024-25-nba-regular-season-schedule/",
    "2025-26": "https://pr.nba.com/2025-26-nba-regular-season-schedule/",
}
OFFICIAL_2020_RELEASES = {
    "espn_abc_first": "https://espnpressroom.com/press-release/espn-abc-combine-to-nationally-televise-49-games-during-first-half-of-2020-21-nba-regular-season/",
    "espn_abc_second": "https://espnpressroom.com/press-release/espn-and-abc-combine-to-nationally-televise-49-nba-games-in-second-half-of-2020-21-regular-season/",
    "tnt_first": "https://press.wbd.com/us/media-release/nba-tnts-2020-21-regular-season-schedule-feature-66-games-highlighted-marquee-0",
    "tnt_second": "https://press.wbd.com/ca/media-release/tnt-sports/nba-tnt/nba-tnts-2020-21-regular-season-second-half-schedule-feature-31-games-televised",
    "nbatv_first": "https://press.wbd.com/na/media-release/tnt-sports/nba-digital/nba-tv-televise-107-games-during-2020-21-regular-season-0",
    "nbatv_second": "https://press.wbd.com/na/media-release/tnt-sports/nba-digital/nba-tvs-2020-21-regular-season-second-half-coverage-feature-lakers-nets-clippers",
}
TEAM = {
    "Atlanta":"Atlanta Hawks","Boston":"Boston Celtics",
    "Brooklyn":"Brooklyn Nets","Charlotte":"Charlotte Hornets",
    "Chicago":"Chicago Bulls","Cleveland":"Cleveland Cavaliers",
    "Dallas":"Dallas Mavericks","Denver":"Denver Nuggets",
    "Detroit":"Detroit Pistons","Golden State":"Golden State Warriors",
    "Houston":"Houston Rockets","Indiana":"Indiana Pacers",
    "LA Clippers":"LA Clippers","L.A. Lakers":"Los Angeles Lakers",
    "Memphis":"Memphis Grizzlies","Miami":"Miami Heat",
    "Milwaukee":"Milwaukee Bucks","Minnesota":"Minnesota Timberwolves",
    "New Orleans":"New Orleans Pelicans","New York":"New York Knicks",
    "Oklahoma City":"Oklahoma City Thunder","Orlando":"Orlando Magic",
    "Philadelphia":"Philadelphia 76ers","Phoenix":"Phoenix Suns",
    "Portland":"Portland Trail Blazers","Sacramento":"Sacramento Kings",
    "San Antonio":"San Antonio Spurs","Toronto":"Toronto Raptors",
    "Utah":"Utah Jazz","Washington":"Washington Wizards",
}
# NBA PDF printed column positions; these are not inferred from the frozen
# source CSV. Last 2025 local tip time sometimes begins before the column edge.
PDF_COORDS = {
    "2021-22":(190,285,370,470),
    "2022-23":(195,284,375,492),
    "2023-24":(188,282,367,465),
    "2024-25":(187,280,375,481),
    "2025-26":(165,253,354,446),
}
PDF_NETWORKS = {"ABC","ESPN","TNT","NBA TV","ABC/ESPN","Prime","Peacock","NBC/Peacock"}
DATE_TOKEN = re.compile(r"^\d{1,2}/\d{1,2}/\d{2}$")
TIP_TOKEN = re.compile(r"^\d{1,2}:\d{2}$")
MONTH = {"Dec":12,"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5}
MONTH_DATE = re.compile(r"(Dec|Jan|Feb|Mar|Apr|May)\.?[\s,]*(\d{1,2})",re.I)
PRIMARY_NETWORK = {
    season: ({"ABC","ABC/ESPN","ESPN","TNT"} if season != "2025-26"
             else {"ABC","ABC/ESPN","ESPN","NBC/Peacock","Peacock","Prime"})
    for season in BROADCAST_PDF_SHA
}


def require(condition: bool, reason: str):
    if not condition:
        raise ValueError("Original NBA broadcast source mismatch: "+reason)


def digest(file: Path) -> str:
    h=sha256()
    with file.open("rb") as src:
        for block in iter(lambda: src.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def member(archive: ZipFile, name: str) -> bytes:
    require(archive.namelist().count(name)==1, f"source ZIP member missing/duplicate: {name}")
    return archive.read(name)


def parse_pdf_rows(data: bytes, season: str) -> list[dict]:
    """Original printed day/date/teams/network from independent PDF word positions."""
    import fitz  # PyMuPDF, needed only for the private original-input audit.
    require(season in PDF_COORDS,"unsupported original NBA schedule source season")
    low,cut,high,net_x=PDF_COORDS[season]
    out=[]
    pdf=fitz.open(stream=data,filetype="pdf")
    for pnum,page in enumerate(pdf,1):
        groups=defaultdict(list)
        for x0,y0,x1,y1,word,*_ in page.get_text("words"):
            groups[round(y0/2)*2].append((x0,word))
        for words in groups.values():
            dates=[word for x,word in words if DATE_TOKEN.match(word) and 90<x<175]
            if not dates:
                continue
            require(len(dates)==1,f"{season} original PDF page {pnum}: ambiguous game date")
            date=pd.to_datetime(dates[0],format="%m/%d/%y").strftime("%Y-%m-%d")
            away=" ".join(w for x,w in words if low<=x<cut and w not in {"at","vs"})
            home=" ".join(w for x,w in words
                if cut<=x<high and w not in {"at","vs"} and not TIP_TOKEN.match(w))
            nw=[w for x,w in words if x>=net_x and w in
                {"ABC","ESPN","TNT","NBA","TV","ABC/ESPN","Prime","Peacock","NBC/Peacock"}]
            network=" ".join(x for x in nw)
            require(network in PDF_NETWORKS|{""},
                    f"{season} original PDF page {pnum}: unsupported network {network}")
            require(away in TEAM and home in TEAM,
                    f"{season} original PDF page {pnum}: unknown NBA teams: {away} at {home}")
            out.append({
                "season":season,"date":date,"away":TEAM[away],
                "home":TEAM[home],"network":network,"source_page":pnum,
            })
    return out


def parse_2020_date(s: str, previous: str|None=None) -> str|None:
    found=MONTH_DATE.search(s)
    if not found:return previous
    month=MONTH[found.group(1).title()]
    return f"{2020 if month==12 else 2021}-{month:02d}-{int(found.group(2)):02d}"


def parse_matchup(s: str) -> tuple[str,str]|None:
    s=re.sub(r"\s+"," ",s).strip()
    for sep in (" at "," vs. "," vs "):
        if sep in s:
            first,second=s.split(sep,1)
            return first.rstrip("*").strip(),second.rstrip("*").strip()
    return None


def parse_2020_html(data: bytes, source_key: str) -> list[dict]:
    """Matchup-specified original ESPN/WBD release tables; excludes TBD and radio."""
    from bs4 import BeautifulSoup
    require(source_key in BROADCAST_HTML_SHA,"unknown original 2020 media release")
    soup=BeautifulSoup(data,"html.parser")
    out=[]
    for number,table in enumerate(soup.find_all("table"),1):
        if source_key=="espn_abc_second" and number>=3:
            continue # third ESPN second-half table is RADIO, not TV
        previous=None
        for rowno,tr in enumerate(table.find_all("tr"),1):
            cells=[x.get_text(" ",strip=True) for x in tr.find_all(["th","td"])]
            if rowno==1 or not cells:continue
            if source_key.startswith("espn_abc"):
                if len(cells)<3:continue
                if source_key=="espn_abc_first" and number==4:
                    dt="2020-12-25"
                    matchup=parse_matchup(cells[1])
                    platforms={x.strip() for x in cells[2].split(",")}
                    net=("ABC/ESPN" if {"ABC","ESPN"}<=platforms else
                         "ABC" if "ABC" in platforms else "ESPN")
                else:
                    previous=parse_2020_date(cells[0],previous);dt=previous
                    matchup=parse_matchup(cells[-1])
                    net=("ABC" if (source_key=="espn_abc_first" and number in (1,2))
                         or (source_key=="espn_abc_second" and number==2) else "ESPN")
            else:
                if len(cells)<4:continue
                previous=parse_2020_date(cells[1],previous);dt=previous
                matchup=parse_matchup(cells[-1])
                net="TNT" if source_key.startswith("tnt") else "NBA TV"
            if matchup is None or dt is None:continue
            away,home=matchup
            if away.upper() in {"TBD","TBA"} or home.upper() in {"TBD","TBA"}:
                continue
            out.append({
                "source_key":source_key,"table_number":number,
                "row_number":rowno,"date":dt,"away":away,"home":home,
                "network":net,
                "segment":"first_half" if source_key.endswith("_first") else "second_half",
            })
    return out


def source_2020_counts(rows: list[dict]) -> dict:
    counts=Counter(r["source_key"] for r in rows)
    expected={"espn_abc_first":49,"espn_abc_second":46,
              "tnt_first":36,"tnt_second":27,"nbatv_first":61,
              "nbatv_second":0}
    require(dict(counts)=={k:v for k,v in expected.items() if v},
            "2020 49+46+36+27+61 original released matchup rows")
    key=lambda row:(row["segment"],row["date"],row["away"],row["home"])
    unique={key(r) for r in rows}
    require(len(rows)==219 and len(unique)==218,
            "2020 duplicate national television announcement not handled")
    return {"independently_reparsed_specified_broadcast_rows":219,
            "unique_original_announced_matchups":218,
            "source_2020_by_release":expected}


def verify_original_sources(inventory_zip: Path, freeze_zip: Path) -> dict:
    require(digest(inventory_zip)==INVENTORY_SHA,"original source inventory ZIP SHA-256 drift")
    require(digest(freeze_zip)==FREEZE_SHA,"original frozen research release ZIP SHA-256 drift")
    with ZipFile(inventory_zip) as inventory, ZipFile(freeze_zip) as outer:
        tv_bytes=member(outer,TV_PACKAGE)
        require(sha256(tv_bytes).hexdigest()==ORIGINAL_TV_PACKAGE_SHA,
                "original frozen national-TV package SHA-256 drift")
        with ZipFile(io.BytesIO(tv_bytes)) as frozen:
            published=pd.read_csv(io.BytesIO(member(
                frozen,MODERN+"source_schedule_rows_2021_22_to_2025_26.csv")),
                keep_default_na=False)
            mapped=pd.read_csv(io.BytesIO(member(
                frozen,MODERN+"announced_tv_2021_22_to_2025_26_v2.csv")),
                keep_default_na=False)
            html_reference=pd.read_csv(io.BytesIO(member(
                frozen,LEGACY+"parsed_source_rows_all.csv")),
                keep_default_na=False)
            legacy_mapped=pd.read_csv(io.BytesIO(member(
                frozen,LEGACY+"announced_tv_2020_21_v2.csv")),
                keep_default_na=False)
            original_matches=pd.read_csv(io.BytesIO(member(
                frozen,LEGACY+"matched_source_games.csv")),
                keep_default_na=False)
            combined=pd.read_csv(io.BytesIO(member(
                frozen,BASE+"announced_tv_six_seasons.csv")),
                keep_default_na=False)

            actual_pdfs=[]
            pdf_counts={}
            for season,expected_sha in BROADCAST_PDF_SHA.items():
                suffix=f"{season}_schedule_by_date.pdf"
                pdf_data=member(inventory,"broadcast_sources/"+suffix)
                require(sha256(pdf_data).hexdigest()==expected_sha,
                        f"{season} original preseason NBA source PDF SHA drift")
                require(pdf_data==member(frozen,MODERN+"raw_pdfs/"+suffix),
                        f"{season} archived original NBA PDF differs from original freeze")
                parsed=parse_pdf_rows(pdf_data,season)
                pdf_counts[season]=len(parsed)
                require(len(parsed)==(1230 if season in ("2021-22","2022-23") else 1200),
                        f"{season} NBA PDF source game count")
                ref=published.loc[published.season.eq(season)].sort_values("source_id")
                require(len(ref)==len(parsed),f"{season} archived TV source rows incomplete")
                for r,raw in zip(ref.to_dict("records"),parsed):
                    require((r["announced_date_et"],r["announced_away_team"],
                             r["announced_home_team"],r["network_announced"])==
                            (raw["date"],raw["away"],raw["home"],raw["network"]),
                            f"{season} original PDF row {r['source_id']} broadcast/date/opponent differs")
                actual_pdfs.extend(parsed)

            require(len(actual_pdfs)==6060 and len(mapped)==6150,
                    "five full original PDF schedule release row count changed")
            require(not pd.DataFrame(actual_pdfs).duplicated(
                        ["season","date","away","home"]).any(),
                    "duplicate original PDF schedule matchup/date")
            expected_pdf={(x["season"],x["date"],x["away"],x["home"]):x["network"]
                          for x in actual_pdfs}
            mapped_selected=0;not_yet_known=Counter()
            counts=Counter()
            for r in mapped.to_dict("records"):
                season=r["season"]
                if str(r["listed_at_release"])=="True":
                    key=(season,r["announced_date_et"],r["announced_away_team"],
                         r["announced_home_team"])
                    require(key in expected_pdf,
                            f"{season} published game not actually listed in original PDF")
                    network=expected_pdf[key]
                    require(r["network_announced"]==network,
                            f"{season} wrong national-TV network after historical game remapping")
                    require(str(r["announced_tv_primary"])=="True" if
                            network in PRIMARY_NETWORK[season] else
                            str(r["announced_tv_primary"])=="False",
                            f"{season} primary national broadcaster wrongly coded")
                    require(str(r["announced_nba_tv"])=="True" if network=="NBA TV" else
                            str(r["announced_nba_tv"])=="False",
                            f"{season} NBA TV separated sensitivity definition wrongly coded")
                    mapped_selected+=1
                    if network in PRIMARY_NETWORK[season]:counts[season]+=1
                else:
                    require(season in {"2023-24","2024-25","2025-26"} and
                            r["announced_tv_status"]=="matchup_tbd_at_schedule_release" and
                            not r["network_announced"] and
                            str(r["announced_tv_primary"])=="False",
                            "Post-initial-release NBA Cup unknown matchup incorrectly assigned TV")
                    not_yet_known[season]+=1
            require(mapped_selected==6060 and
                    dict(not_yet_known)=={y:30 for y in ("2023-24","2024-25","2025-26")},
                    "Original NBA Cup TBD game flags missing for one release")
            require(dict(counts)=={"2021-22":162,"2022-23":163,"2023-24":160,
                                    "2024-25":163,"2025-26":237},
                    "Primary TV classifications from original PDFs differ")

            original_html=[]
            for key,expected_sha in BROADCAST_HTML_SHA.items():
                html=member(inventory,"broadcast_sources/"+key+".html")
                require(sha256(html).hexdigest()==expected_sha,
                        f"2020 {key} original broadcaster newsroom HTML SHA drift")
                require(html==member(frozen,LEGACY+"raw_html/"+key+".html"),
                        f"2020 {key} raw broadcast page differs from frozen archive")
                original_html.extend(parse_2020_html(html,key))
            legacy=source_2020_counts(original_html)
            by_coordinates={
                (r["source_key"],r["table_number"],r["row_number"]):r for r in original_html
            }
            require(len(by_coordinates)==len(html_reference)==219,
                    "2020 original 219 source rows not uniquely identified")
            for old in html_reference.to_dict("records"):
                raw=by_coordinates.get((old["source_key"],old["table_number"],old["row_number"]))
                require(raw is not None and
                        (raw["date"],raw["away"],raw["home"],raw["network"])==
                        (old["announced_date_et"],old["announced_away_team"],
                         old["announced_home_team"],old["network_announced"]),
                        "2020 original broadcaster HTML row disagrees with source research CSV")

            key=lambda row:(row["segment"],row["date"],row["away"],row["home"])
            unique={}
            for row in original_html:
                unique.setdefault(key(row),set()).add(row["network"])
            matched_source_keys=set()
            matched_primary=set()
            matched_tv=set()
            for r in original_matches.to_dict("records"):
                k=(r["release_segment"],r["announced_date_et"],
                   r["announced_away_team"],r["announced_home_team"])
                require(k in unique,"original 2020 played fixture lacks source newsroom matchup")
                network="|".join(sorted(unique[k]))
                require(network.replace("ABC|ESPN","ABC/ESPN")==
                        r["network_announced"].replace("ABC|ESPN","ABC/ESPN"),
                        "original 2020 played matchup broadcaster changed")
                matched_source_keys.add(k)
                if any(x in {"ABC","ABC/ESPN","ESPN","TNT"} for x in unique[k]):
                    matched_primary.add(int(r["fixture_row"]))
                if "NBA TV" in unique[k]:
                    matched_tv.add(int(r["fixture_row"]))
            require(len(matched_source_keys)==217 and len(unique)==218 and
                    len(matched_primary)==156 and len(matched_tv)==61,
                    "2020 original source matched broadcaster game count differs")
            require(len(legacy_mapped)==1080 and
                    {int(x["fixture_row"]) for x in legacy_mapped.to_dict("records")
                     if str(x["announced_tv_primary"])=="True"}==matched_primary and
                    {int(x["fixture_row"]) for x in legacy_mapped.to_dict("records")
                     if str(x["announced_nba_tv"])=="True"}==matched_tv,
                    "2020 historical primary-TV/first-half NBA TV game labels differ")
            require(sum(str(x["announced_nba_tv"])=="" for x in
                        legacy_mapped.to_dict("records"))==542,
                    "Missing 2020 second-half NBA TV must stay unknown")
            require(len(combined)==7230 and
                    combined.groupby("season").size().to_dict()==
                    {"2020-21":1080,**{s:1230 for s in BROADCAST_PDF_SHA}},
                    "original combined six-season TV treatment panel altered")
            for source_data in (legacy_mapped,mapped):
                subset=combined[combined.season.isin(source_data.season.unique())]
                for original in source_data.to_dict("records"):
                    match=subset[(subset.season==original["season"]) &
                                 (subset.fixture_row==original["fixture_row"])]
                    require(len(match)==1,"historical combined six-season game IDs changed")
                    one=match.iloc[0]
                    for field in ("network_announced","announced_tv_primary",
                                  "announced_nba_tv","announced_tv_status"):
                        require(str(original[field])==str(one[field]),
                                f"combined six-season original broadcast field changed: {field}")

            return {
                "status":"PASS_INDEPENDENT_FIRST_PARTY_NBA_BROADCAST_SOURCE_REEXTRACTION",
                "source_original_pdfs_reparsed":5,
                "source_original_html_pages_reparsed":6,
                "original_2021_2025_PDF_game_rows":6060,
                "independent_full_2021_2025_pdf_date_away_home_network_differences":0,
                "2021_2025_mapped_game_rows":6150,
                "2021_2025_original_TBD_Cup_games_correctly_not_announced":90,
                "2021_2025_exact_primary_TV_games":sum(counts.values()),
                "primary_games_by_season":dict(counts),
                "original_2020_HTML_broadcaster_specified_rows":219,
                "original_2020_independent_date_team_network_disagreements":0,
                "original_2020_distinct_matchups":218,
                "original_2020_unique_announcements_matched_to_played_fixtures":217,
                "original_2020_primary_national_games_confirmed":156,
                "original_2020_first_half_NBA_TV_games_confirmed":61,
                "original_2020_second_half_NBA_TV_missing_unknown_games":542,
                "combined_original_six_season_games":7230,
                "combined_original_primary_national_games":156+sum(counts.values()),
                "source_inventory_sha256":INVENTORY_SHA,
                "original_research_freeze_sha256":FREEZE_SHA,
                "original_immutable_TV_release_package_sha256":ORIGINAL_TV_PACKAGE_SHA,
                "official_NBA_release_pages":OFFICIAL_RELEASES,
                "original_2020_broadcaster_press_pages":OFFICIAL_2020_RELEASES,
                "limitations":{
                    "original_2020_NBA_TV_second_half_complete":False,
                    "2023_2025_Cup_matchups_unknown_at_preseason_release":90,
                    "exact_original_PDF_byte_hash_redownloaded_from_live_NBA_CDN":False,
                    "complete_official_report_archive_source_coverage_independently_proven":False,
                    "individual_postponed_fixture_mapping_to_actual_played_NBA_game_independently_checked":False,
                    "official_six_season_original_TV_source_rows_reextracted_from_saved_original_first_party_files":True,
                    "original_historical_dataset_or_manuscript_modified":False,
                    "private_player_level_data_uploaded_to_GitHub":False,
                },
            }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historical-source-inventory",type=Path,required=True)
    p.add_argument("--original-final-freeze",type=Path,required=True)
    p.add_argument("--output-report",type=Path,
                   help="NEW JSON path for aggregate-only acceptance evidence")
    args=p.parse_args()
    result=verify_original_sources(
        args.historical_source_inventory.resolve(strict=True),
        args.original_final_freeze.resolve(strict=True))
    serialized=json.dumps(result,indent=2)+"\n"
    if args.output_report is not None:
        if args.output_report.exists():
            raise FileExistsError("Refusing to overwrite prior original NBA TV source audit")
        args.output_report.parent.mkdir(parents=True,exist_ok=True)
        args.output_report.write_text(serialized,encoding="utf-8")
    print(serialized)


if __name__=="__main__":
    main()
