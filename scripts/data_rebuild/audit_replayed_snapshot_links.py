#!/usr/bin/env python3
"""Fail closed on historical game-selector to source-reparsed injury-PDF linkage.

Checks the existing archived selector against independently generated PDF rows
and parser logs. Does not recreate selectors, player identities or model panels.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

ALLOWED_SEASONS = ("2021-22", "2022-23", "2023-24")
# Documented original clean-team inference; no blanket waiver for missing games.
KNOWN_CLEAN_INFERENCES = {
    "2021-22": set(),
    "2022-23": set(),
    "2023-24": {"FD2023_5"},
}
REQUIRED_LOG = {"source_file", "snapshot_timestamp_utc", "status"}
REQUIRED_ROWS = {"source_file", "snapshot_timestamp_utc", "matchup_norm"}
REQUIRED_SELECTOR = {
    "game_id", "snapshot_basename", "published_timestamp_utc", "matchup_norm",
    "tip_timestamp_utc", "minutes_before_tip", "inferred_clean_teams",
    "listed_teams", "both_teams_usable",
}


def read_csv(path: Path, required: set[str]):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not required <= set(reader.fieldnames or ()):
            raise ValueError(f"Missing required CSV columns in {path}")
        yield from reader


def zip_csv(archive: ZipFile, member: str, required: set[str]):
    with io.TextIOWrapper(archive.open(member), encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not required <= set(reader.fieldnames or ()):
            raise ValueError(f"Missing selector fields: {member}")
        yield from reader


def verify(selector_zip: Path, season: str, rows_csv: Path, logs_csv: Path,
           *, expected_games: int = 1230):
    if season not in ALLOWED_SEASONS:
        raise ValueError(f"Unexpected season {season!r}")
    if expected_games <= 0:
        raise ValueError("expected_games must be positive")

    logs = {}
    for row in read_csv(logs_csv, REQUIRED_LOG):
        key = (Path(row["source_file"]).name, row["snapshot_timestamp_utc"])
        if key in logs:
            raise ValueError(f"Duplicate source PDF+timestamp parser log: {key}")
        logs[key] = row["status"]
    matchups = set()
    for row in read_csv(rows_csv, REQUIRED_ROWS):
        matchups.add((Path(row["source_file"]).name,
                      row["snapshot_timestamp_utc"], row["matchup_norm"]))

    findings = {
        "season": season,
        "scope": "archived selector versus independently PDF-reparsed CSV/log; NOT selector reconstruction",
        "panels": {},
    }
    game_sets = {}
    with ZipFile(selector_zip) as archive:
        member_names = archive.namelist()
        for panel in ("full", "harmonized"):
            member = f"nba_canonical_snapshot_selector_v1/{season}_game_snapshot_join_{panel}_canonical.csv"
            if member_names.count(member) != 1:
                raise ValueError(f"Expected one canonical selector ZIP member {member}, got {member_names.count(member)}")
            selected = list(zip_csv(archive, member, REQUIRED_SELECTOR))
            problems = Counter()
            selected_games = set()
            clean_inferences = []
            age_min = None
            age_max = None
            if len(selected) != expected_games:
                raise ValueError(f"{season} {panel}: expected {expected_games} games, found {len(selected)}")
            for record in selected:
                game_id = record["game_id"]
                if not game_id:
                    problems["empty_game_id"] += 1
                if game_id in selected_games:
                    problems["duplicate_game_id"] += 1
                selected_games.add(game_id)
                basename = record["snapshot_basename"]
                timestamp = record["published_timestamp_utc"]
                matchup = record["matchup_norm"]
                key = (basename, timestamp)
                if not basename.lower().endswith(".pdf") or not timestamp:
                    problems["missing_pdf_identity"] += 1
                if logs.get(key) != "ok":
                    problems["missing_or_failed_pdf_parse"] += 1
                if (basename, timestamp, matchup) not in matchups:
                    if (game_id in KNOWN_CLEAN_INFERENCES[season]
                            and record["inferred_clean_teams"] == "2"
                            and record["listed_teams"] == "0"
                            and record["both_teams_usable"] == "True"):
                        clean_inferences.append(game_id)
                    else:
                        problems["missing_selected_matchup"] += 1
                try:
                    tip = datetime.fromisoformat(record["tip_timestamp_utc"])
                    published = datetime.fromisoformat(timestamp)
                    age = (tip - published).total_seconds() / 60
                    recorded = float(record["minutes_before_tip"])
                    if age <= 0:
                        problems["selected_pdf_not_pre_tip"] += 1
                    if abs(age - recorded) > 1e-6:
                        problems["incorrect_recorded_snapshot_age"] += 1
                    age_min = age if age_min is None else min(age_min, age)
                    age_max = age if age_max is None else max(age_max, age)
                except (ValueError, TypeError):
                    problems["timestamp_parse_error"] += 1
            if set(clean_inferences) != KNOWN_CLEAN_INFERENCES[season]:
                problems["known_clean_inference_mismatch"] += 1
            findings["panels"][panel] = {
                "selected_games": len(selected),
                "unique_game_ids": len(selected_games),
                "selected_pdf_logs_verified": len(selected) - problems["missing_or_failed_pdf_parse"],
                "explicit_both_teams_inferred_clean": len(clean_inferences),
                "inferred_clean_game_ids": sorted(clean_inferences),
                "minimum_minutes_pre_tip": age_min,
                "maximum_minutes_pre_tip": age_max,
                "problems": dict(problems),
            }
            game_sets[panel] = selected_games
    bad = {panel: outcome["problems"] for panel, outcome in findings["panels"].items()
           if outcome["problems"]}
    if bad:
        raise ValueError(f"Reparsed historical selector source links failed: {bad}")
    if game_sets["full"] != game_sets["harmonized"]:
        raise ValueError(f"{season}: full and harmonized canonical game sets differ")
    findings["passed"] = True
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selector-zip", type=Path, required=True)
    p.add_argument("--season", choices=ALLOWED_SEASONS, required=True)
    p.add_argument("--reparsed-rows", type=Path, required=True)
    p.add_argument("--reparsed-log", type=Path, required=True)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    report = verify(a.selector_zip, a.season, a.reparsed_rows, a.reparsed_log)
    rendered = json.dumps(report, indent=2) + "\n"
    if a.output:
        if a.output.exists():
            raise FileExistsError(f"Refusing to overwrite existing verification: {a.output}")
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
