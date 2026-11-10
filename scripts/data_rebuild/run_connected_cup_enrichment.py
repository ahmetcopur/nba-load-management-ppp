#!/usr/bin/env python3
"""Rebuild NBA Cup enrichment from the frozen ORIGINAL game-stage lookup.

This is a NEW source-lookup reimplementation because the archived historical
build_cup_flags_v1.py contains only a documentation stub. It starts from a
freshly generated source-pinned star panel, not the frozen Cup-enriched panel.

The original Cup lookup itself remains an inherited source assumption until
the 2023–26 NBA schedule announcements are independently reconstructed.
All three generated full/model/spell panels are compared as entire decoded
CSV byte streams against their historical published counterparts.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.data_rebuild.run_connected_player_game_core import (
    compare_streams, read_member, sha256_file,
)
from scripts.data_rebuild.run_connected_star_enrichment import (
    STAR_ZIP, STAR_ZIP_SHA256,
)

CUP_ARCHIVE = "nba_player_game_at_risk_star_cup_v1.zip"
CUP_ARCHIVE_SHA256 = (
    "65c4756b86dfb5757bb84b6be13eafb952375aaa6ce49fc1ddddc6224a4faf70"
)
CUP_PREFIX = "nba_player_game_at_risk_star_cup_v1/"
OUT_FOLDER = "nba_player_game_at_risk_star_cup_v1"
FLAG_COLS = (
    "cup_stage", "cup_game", "cup_group_play",
    "cup_quarterfinal", "cup_semifinal", "cup_knockout",
)
EXTRA_COLS = FLAG_COLS + (
    "cup_round_order", "cup_flag_version", "player_team_game_id",
    "star_postPPP", "star_postPPP_announcedTV",
    "star_cup_game", "star_postPPP_cup_game",
)
SPELL_EXTRA_COLS = (
    "start_game_date_from_panel", "onset_cup_game", "onset_cup_stage",
    "onset_cup_group_play", "onset_cup_knockout",
    "onset_cup_quarterfinal", "onset_cup_semifinal",
)
STAGES = {
    "full": ("player_game_panel_star.csv.gz", "player_game_panel_star_cup.csv.gz", 248730),
    "risk": ("player_game_panel_model_at_risk_star.csv.gz",
             "player_game_panel_model_at_risk_star_cup.csv.gz", 180829),
    "spells": ("absence_spells_provisional_star.csv.gz",
               "absence_spells_provisional_star_cup.csv.gz", 13723),
}
STAGE_ORDER = {"none": 0, "group_play": 1, "quarterfinal": 2, "semifinal": 3}
EXPECTED_CUP_GAMES = {"2023-24": 66, "2024-25": 66, "2025-26": 66}


def original_lookup(source_zip: Path) -> pd.DataFrame:
    data = read_member(source_zip, CUP_PREFIX + "cup_game_lookup.csv")
    lookup = pd.read_csv(io.BytesIO(data), low_memory=False)
    required = {"game_id", "season", "game_date_et", *FLAG_COLS}
    if not required <= set(lookup):
        raise ValueError(f"Original Cup source lookup fields missing: {required-set(lookup)}")
    if len(lookup) != 7230 or lookup.game_id.isna().any() or lookup.game_id.duplicated().any():
        raise ValueError("Original Cup game-stage lookup must have 7,230 unique game IDs")
    if lookup.cup_stage.isna().any() or not lookup.cup_stage.isin(STAGE_ORDER).all():
        raise ValueError("Unknown or missing original NBA Cup round label")
    if int(lookup.cup_game.sum()) != 198:
        raise ValueError("Original Cup source does not contain 198 regular-season games")
    actual = lookup.loc[lookup.cup_game].groupby("season").size().to_dict()
    if actual != EXPECTED_CUP_GAMES:
        raise ValueError(f"NBA Cup official-stage season count drift: {actual}")
    for season in EXPECTED_CUP_GAMES:
        stages = lookup.loc[lookup.season.eq(season) & lookup.cup_game].cup_stage.value_counts()
        if stages.to_dict() != {"group_play": 60, "quarterfinal": 4, "semifinal": 2}:
            raise ValueError(f"NBA Cup group/quarter/semifinal count drift: {season}")
    return lookup


def add_cup_flags(source: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    required = {
        "game_id", "team", "nba_player_id", "star_PPP_it",
        "postPPP", "announced_tv_primary", "cup_game_pending",
    }
    if not required <= set(source):
        raise ValueError(f"Freshly built star source columns missing: {required-set(source)}")
    data = source.merge(lookup[["game_id", *FLAG_COLS]], on="game_id",
                        how="left", sort=False, validate="many_to_one")
    if data.cup_stage.isna().any():
        raise ValueError("Missing original Cup classification for a player-game record")
    # The source star panel contains provisional cup_game_pending flags.
    # The validated official Cup lookup resolves that placeholder for ALL rows.
    data["cup_game_pending"] = False
    data["cup_round_order"] = data.cup_stage.map(STAGE_ORDER).astype(int)
    data["cup_flag_version"] = "official_dates_v1"
    data["player_team_game_id"] = (
        data.game_id.astype(str) + "|" + data.team.astype(str) + "|"
        + data.nba_player_id.astype("Int64").astype(str)
    )
    if data.player_team_game_id.duplicated().any():
        raise ValueError("Composite player-team-game identifier must be unique")
    data["star_postPPP"] = data.star_PPP_it & data.postPPP
    data["star_postPPP_announcedTV"] = data.star_postPPP & data.announced_tv_primary
    data["star_cup_game"] = data.star_PPP_it & data.cup_game
    data["star_postPPP_cup_game"] = data.star_postPPP & data.cup_game
    return data[list(source.columns) + list(EXTRA_COLS)]


def add_cup_to_spells(source: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    if "start_game_id" not in source:
        raise ValueError("Original star spell table has no start_game_id")
    renamed = lookup[[
        "game_id", "game_date_et", "cup_game", "cup_stage",
        "cup_group_play", "cup_quarterfinal", "cup_semifinal", "cup_knockout"
    ]].rename(columns={
        "game_id": "start_game_id", "game_date_et": "start_game_date_from_panel",
        "cup_game": "onset_cup_game", "cup_stage": "onset_cup_stage",
        "cup_group_play": "onset_cup_group_play",
        "cup_quarterfinal": "onset_cup_quarterfinal",
        "cup_semifinal": "onset_cup_semifinal",
        "cup_knockout": "onset_cup_knockout",
    })
    result = source.merge(renamed, on="start_game_id",
                          how="left", sort=False, validate="many_to_one")
    if result.onset_cup_stage.isna().any():
        raise ValueError("Unmatched original absence-spell start game in Cup lookup")
    return result[list(source.columns) + list(SPELL_EXTRA_COLS)]


def build_one_stage(archive_dir: Path, work_dir: Path, stage: str) -> dict:
    if stage not in STAGES:
        raise ValueError("Unknown private Cup enrichment stage")
    source_name, output_name, expected_rows = STAGES[stage]
    source = work_dir / "nba_player_game_at_risk_star_v1" / source_name
    destination = work_dir / OUT_FOLDER / output_name
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing Cup stage output: {destination}")
    if not destination.parent.is_dir():
        raise FileNotFoundError("Private Cup enrichment output directory not staged")
    lookup = original_lookup(archive_dir / CUP_ARCHIVE)
    records = pd.read_csv(source, low_memory=False)
    if len(records) != expected_rows:
        raise ValueError(f"Fresh star {stage} rows differ from historical source")
    rebuilt = add_cup_to_spells(records, lookup) if stage == "spells" else add_cup_flags(records, lookup)
    if len(rebuilt) != expected_rows:
        raise ValueError("Cup enrichment changed player or spell row count")
    rebuilt.to_csv(destination, index=False, compression="gzip")
    return {"stage": stage, "rows": len(rebuilt), "output": output_name}


def compare_original_cup_output(source_zip: Path, generated: Path, output_name: str) -> dict:
    member = CUP_PREFIX + output_name
    original_gzip = read_member(source_zip, member)
    if not generated.is_file():
        raise FileNotFoundError(f"Private Cup stage output missing: {generated}")
    with gzip.GzipFile(fileobj=io.BytesIO(original_gzip)) as old, gzip.open(generated, "rb") as fresh:
        return compare_streams(old, fresh)


def check_private_run(archive_dir: Path, work_dir: Path) -> None:
    archive_dir, work_dir = archive_dir.resolve(), work_dir.resolve()
    if not archive_dir.is_dir() or not work_dir.is_dir():
        raise FileNotFoundError("Original source ZIPs and prior private core+star output required")
    if archive_dir == work_dir or archive_dir in work_dir.parents:
        raise ValueError("Cup output cannot be written in original source archive folder")
    if any((parent / ".git").exists() for parent in (work_dir, *work_dir.parents)):
        raise ValueError("Private Cup player-level rows cannot be written into a Git checkout")
    for file, marker in (
        ("connected_core_reproduction_report.json", "all_ten_outputs_identical_after_gzip_decoding"),
        ("connected_star_reproduction_report.json", "all_twelve_star_outputs_exact"),
    ):
        path = work_dir / file
        if not path.is_file():
            raise FileNotFoundError(f"Accepted original-source stage report missing: {file}")
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") != "pass" or not record.get(marker):
            raise ValueError(f"Upstream original-source stage not accepted: {file}")
    if (work_dir / OUT_FOLDER).exists():
        raise FileExistsError("Cup stage output directory exists; refusing to overwrite")
    for filename, expected in (
        (CUP_ARCHIVE, CUP_ARCHIVE_SHA256),
        (STAR_ZIP, STAR_ZIP_SHA256),
    ):
        if sha256_file(archive_dir / filename) != expected:
            raise ValueError(f"Original archived Cup/star package SHA-256 changed: {filename}")


def run_cup(archive_dir: Path, work_dir: Path, *, timeout_seconds: int = 900) -> dict:
    archive_dir, work_dir = archive_dir.resolve(), work_dir.resolve()
    check_private_run(archive_dir, work_dir)
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    # Validate original report-game universe before writing any output.
    original_lookup(archive_dir / CUP_ARCHIVE)
    cup_out = work_dir / OUT_FOLDER
    cup_out.mkdir(parents=True, exist_ok=False)
    outputs = {}
    for stage, (_, output_name, _) in STAGES.items():
        # Independent subprocesses keep the original large panel read/write
        # from retaining memory across stages and avoid incomplete gzip files.
        args = [
            sys.executable, str(Path(__file__).resolve()), "--archive-dir", str(archive_dir),
            "--work-dir", str(work_dir), "--internal-stage", stage,
        ]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        proc = subprocess.run(args, cwd=work_dir, env=env,
                              capture_output=True, text=True,
                              check=False, timeout=timeout_seconds)
        if proc.returncode != 0:
            raise RuntimeError(
                f"Private Cup {stage} subprocess failed with {proc.returncode}: "
                + (proc.stderr + "\n" + proc.stdout)[-1000:]
            )
        outputs[output_name] = compare_original_cup_output(
            archive_dir / CUP_ARCHIVE, cup_out / output_name, output_name,
        )
    report = {
        "status": "pass",
        "scope": "New original-Cup-lookup to freshly rebuilt source-pinned star panels and spells; the 2023-26 historical lookup is inherited, not independently recreated from official announcements",
        "source_cup_zip_sha256": CUP_ARCHIVE_SHA256,
        "source_star_zip_sha256": STAR_ZIP_SHA256,
        "expected_regular_season_cup_games": 198,
        "full_player_game_rows": STAGES["full"][2],
        "at_risk_rows": STAGES["risk"][2],
        "absence_spell_rows": STAGES["spells"][2],
        "exact_decoded_outputs": outputs,
        "all_three_primary_cup_tables_exact": True,
        "original_cup_lookup_independently_rebuilt_from_official_schedules": False,
        "model_regressions_executed_from_new_cup_panel": False,
        "frozen_source_outputs_modified": False,
    }
    (work_dir / "connected_cup_reproduction_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--timeout-seconds", type=int, default=900)
    p.add_argument("--internal-stage", choices=STAGES, help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.internal_stage:
        print(json.dumps(build_one_stage(a.archive_dir, a.work_dir, a.internal_stage)))
    else:
        print(json.dumps(run_cup(a.archive_dir, a.work_dir,
                                 timeout_seconds=a.timeout_seconds), indent=2))


if __name__ == "__main__":
    main()
