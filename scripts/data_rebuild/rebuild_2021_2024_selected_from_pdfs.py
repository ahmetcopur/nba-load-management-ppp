#!/usr/bin/env python3
"""Rebuild 2021–22 through 2024–25 selected report rows from ORIGINAL NBA PDFs.

The two original historical PDF parsers are SHA-256-pinned. For each season,
the original raw archive ZIP is SHA-256 checked, the 1,230 *archived canonical
game/report choices* supply only game IDs/timestamps and selected matchups,
and the actual player, status and reason rows come from the original PDFs.

The complete 22-column reconstructed row multiset must match the frozen
selected-report records before any new private source CSV is persisted.
This stage does not independently rebuild the saved source report selection
algorithm (that was independently checked in earlier level-C audits).
The 2020–21 parser discrepancy is deliberately NOT included.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.data_rebuild.verify_player_identity_replay import (
    immutable_original_helpers, read_member, csv_from_zip, sha256_file,
)
from scripts.data_rebuild.rebuild_2025_selected_from_pdfs import string_row_multiset

CORE_ZIP = "nba_player_game_at_risk_core_v1.zip"
CORE_SHA256 = "a0f82ebcf6117554a4ce1064ab79db9cf93acc5a53fa25000343810843e659f6"
CORE_PREFIX = "nba_player_game_at_risk_core_v1/"
ORIGINAL_PARSERS = {
    "early": ("parser_2021_2022.py",
              "321d9c8d807325209fbcb6174ec6d82df4ba845c156d7d52158f0ea44714ab3e"),
    "late": ("parser_2023plus.py",
             "197c29d46dfea221c381664b96a05453737df55d7b8dd5d5e6f44e49b69e0e06"),
}
SEASONS = {
    "2021-22": {
        "zip": "audit_2021_22_upload.zip",
        "sha256": "1e027ce6aa2a44292c3d27ba7bbfb24fcab61ded922b7ca6ba1c4211f9984339",
        "parser": "early", "pdfs": 570, "rows": 12527,
    },
    "2022-23": {
        "zip": "audit_2022_23_upload.zip",
        "sha256": "bea1adeac75384c75102b469a1daab43c76501caada2c3402b1e7cfa133732c0",
        "parser": "early", "pdfs": 584, "rows": 11499,
    },
    "2023-24": {
        "zip": "audit_2023_24_upload.zip",
        "sha256": "9cca3e58d2a8e6babce58e54dea5aeb05fa043cb034bc9065d4074e5e171daba",
        "parser": "late", "pdfs": 564, "rows": 12897,
    },
    "2024-25": {
        "zip": "audit_2024_25_upload.zip",
        "sha256": "a10cc660a45f0c3fa6ac279d540a29eae04804dc03eb16a86a1d0c6a7f363e3b",
        "parser": "late", "pdfs": 573, "rows": 14065,
    },
}
TORONTO_SOURCE_GAME_REKEY = {
    "CHI@TOR": "2021-22|20220202T0030Z|Chicago Bulls@Toronto Raptors",
    "MIA@TOR": "2021-22|20220204T0030Z|Miami Heat@Toronto Raptors",
}
_PARSER = None


def accepted_source_filename(season: str) -> str:
    if season not in SEASONS:
        raise ValueError(f"Unknown supported original-PDF source season {season}")
    return f"selected_report_rows_{season.replace('-', '_')}_from_original_PDFs.csv"


def safe_private_directory(raw_dir: Path, output_dir: Path) -> None:
    raw, out = raw_dir.resolve(), output_dir.resolve()
    if not raw.is_dir():
        raise FileNotFoundError(f"Original source ZIPs directory absent: {raw}")
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite private source rows: {out}")
    if raw == out or raw in out.parents or out in raw.parents:
        raise ValueError("Private selected-report outputs must be outside raw archives")
    if any((p / ".git").exists() for p in (out, *out.parents)):
        raise ValueError("Refusing private original NBA player-report rows inside Git checkout")


def load_original_parser(path: str) -> None:
    global _PARSER
    spec = importlib.util.spec_from_file_location("_pinned_original_nba_report_parser", path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load exact original injury-report parser")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _PARSER = module.parse_pdf


def parse_one_selected_pdf(task):
    name, path, timestamp, selected_matchups, season, source_file = task
    if _PARSER is None:
        raise RuntimeError("Original parser worker not initialized")
    match = re.fullmatch(r"Injury-Report_(\d{4}-\d\d-\d\d)_[A-Za-z0-9_]+\.pdf", name)
    if match is None:
        raise ValueError(f"Unexpected historical original PDF filename: {name}")
    extracted, pages, warning = _PARSER(
        Path(path), season=season, report_date=match.group(1),
        snapshot_utc=timestamp, source_file=source_file,
    )
    if pages is None or pages < 1:
        raise ValueError(f"No pages in historical report PDF {name}")
    return name, [r for r in extracted if r["matchup_norm"] in selected_matchups], \
        len(extracted), warning


def select_original_game_map(canonical: pd.DataFrame, season: str):
    selected = canonical.loc[canonical.season.eq(season)]
    if len(selected) != 1230:
        raise ValueError(f"{season}: historical canonical game selection count changed")
    keys = ["snapshot_basename", "matchup_norm"]
    if selected[keys].isna().any().any() or selected.duplicated(keys).any():
        raise ValueError(f"{season}: duplicate/missing original selected PDF and matchup keys")
    choices = {(r["snapshot_basename"], r["matchup_norm"]): r
               for r in selected.to_dict("records")}
    by_pdf = defaultdict(list)
    for record in selected.to_dict("records"):
        by_pdf[str(record["snapshot_basename"])].append(record)
    if len(by_pdf) != SEASONS[season]["pdfs"]:
        raise ValueError(f"{season}: original source PDF selection count changed")
    return choices, by_pdf


def original_source_file(season: str, basename: str) -> str:
    if season == "2021-22":
        return basename
    return f"audit_{season.replace('-', '_')}/pdf/{basename}"


def assemble_selected_rows(parsed: list[tuple[str, dict]],
                           mapping: dict,
                           season: str,
                           reference_columns: list[str],
                           helpers: dict) -> pd.DataFrame:
    if season not in SEASONS:
        raise ValueError("Unsupported historical season")
    if not parsed:
        raise ValueError("Original selected PDFs yielded no report records")
    reconstructed = []
    for filename, source in parsed:
        chosen = mapping.get((filename, str(source["matchup_norm"])))
        if chosen is None:
            raise ValueError("Original PDF returned a matchup outside selected game choices")
        row = dict(source)
        row.update({
            "snapshot_basename": filename,
            "canonical_game_id": chosen["canonical_game_id"],
            "source_match_number": chosen["source_match_number"],
            "published_timestamp_utc": chosen["published_timestamp_utc"],
            "game_id": chosen["game_id"],
            "minutes_before_tip": chosen["minutes_before_tip"],
            "qc_selected_within_30m": chosen["qc_selected_within_30m"],
        })
        # Reproduce the source-coded 2021 Toronto schedule-row correction.
        # This is literal matchup-key based, not taken from frozen report values.
        if season == "2021-22" and row["matchup_norm"] in TORONTO_SOURCE_GAME_REKEY:
            row["game_id"] = TORONTO_SOURCE_GAME_REKEY[row["matchup_norm"]]
        reconstructed.append(row)

    all_columns = set().union(*(set(r) for r in reconstructed))
    if not set(reference_columns) <= all_columns:
        raise ValueError(f"Original PDF parser fields missing: {set(reference_columns)-all_columns}")
    result = pd.DataFrame(reconstructed)[reference_columns]
    result["team_norm"] = result.team_norm.fillna("").map(helpers["norm_team"])
    for field in ("player_name", "current_status", "reason"):
        result[field] = result[field].fillna("").map(helpers["clean"])
    return result.drop_duplicates([
        "season", "game_id", "team_norm", "player_name",
        "current_status", "reason", "team_submission_status",
    ])


def compare_original_22_fields(rebuilt: pd.DataFrame, archived: pd.DataFrame,
                               season: str) -> dict:
    if list(rebuilt.columns) != list(archived.columns) or len(rebuilt.columns) != 22:
        raise ValueError("Original selected-report CSV 22-column schema mismatch")
    if len(rebuilt) != SEASONS[season]["rows"] or len(archived) != SEASONS[season]["rows"]:
        raise ValueError(f"{season}: original selected-report record count changed")
    observed = string_row_multiset(rebuilt)
    historical = string_row_multiset(archived)
    if observed != historical:
        raise ValueError(
            f"{season}: original-PDF selected 22-field full-record mismatch; "
            f"missing={sum((historical-observed).values())}, "
            f"extra={sum((observed-historical).values())}"
        )
    return {
        "season": season,
        "original_pdfs_reparsed": SEASONS[season]["pdfs"],
        "selected_player_report_rows": len(rebuilt),
        "all_original_columns_compared": 22,
        "missing_full_records": 0, "extra_full_records": 0,
        "complete_original_row_multiset_exact": True,
        "archived_game_report_selection_metadata_inherited": True,
        "all_player_names_statuses_reasons_sourced_from_actual_PDFs": True,
    }


def stage_original_pdfs(source_zip: Path, wanted: set[str],
                        private_pdf_root: Path) -> dict[str, Path]:
    staged = {}
    with ZipFile(source_zip) as archive:
        for member in archive.namelist():
            basename = Path(member).name
            if basename not in wanted or not member.endswith(".pdf"):
                continue
            if not re.fullmatch(
                r"Injury-Report_\d{4}-\d\d-\d\d_[A-Za-z0-9_]+\.pdf", basename
            ):
                raise ValueError("Original selected PDF basename malformed")
            if basename in staged:
                raise ValueError(f"Ambiguous original PDF basename {basename}")
            if archive.namelist().count(member) != 1:
                raise ValueError("Duplicate original ZIP member path")
            path = private_pdf_root / basename
            path.write_bytes(archive.read(member))
            staged[basename] = path
    if set(staged) != wanted:
        raise ValueError(f"Missing original source PDFs: {len(wanted-set(staged))}")
    return staged


def rebuild(archive_dir: Path, output_dir: Path, *,
            seasons: tuple[str, ...] = tuple(SEASONS),
            workers: int = 8) -> dict:
    archive_dir, output_dir = archive_dir.resolve(), output_dir.resolve()
    safe_private_directory(archive_dir, output_dir)
    if not seasons or len(seasons) != len(set(seasons)) or not set(seasons) <= set(SEASONS):
        raise ValueError("Choose unique supported original 2021–24 source seasons")
    if workers < 1 or workers > 16:
        raise ValueError("PDF parser worker count must be 1..16")
    if sha256_file(archive_dir / CORE_ZIP) != CORE_SHA256:
        raise ValueError("Original private NBA player-game core ZIP SHA changed")
    for season in seasons:
        spec = SEASONS[season]
        if sha256_file(archive_dir / spec["zip"]) != spec["sha256"]:
            raise ValueError(f"Original raw NBA report ZIP SHA changed for {season}")

    canonical = csv_from_zip(archive_dir, CORE_ZIP,
                             CORE_PREFIX + "canonical_game_snapshot_map.csv")
    references = csv_from_zip(archive_dir, CORE_ZIP,
                              CORE_PREFIX + "selected_report_rows_all.csv")
    helpers = immutable_original_helpers(archive_dir)

    reports = {}
    # Write only after original source verification and 22-field acceptance.
    output_dir.mkdir(parents=True, exist_ok=False)
    for season in seasons:
        parser_name, parser_sha = ORIGINAL_PARSERS[SEASONS[season]["parser"]]
        parser_bytes = read_member(
            archive_dir / CORE_ZIP, CORE_PREFIX + "parsers/" + parser_name
        )
        if hashlib.sha256(parser_bytes).hexdigest() != parser_sha:
            raise ValueError(f"{season}: immutable source parser SHA changed")
        choices, per_pdf = select_original_game_map(canonical, season)
        original = references.loc[references.season.eq(season)].copy()
        with TemporaryDirectory(prefix="nba_original_selected_pdf_") as private:
            temp = Path(private)
            original_parser_path = temp / "pinned_source_parser.py"
            original_parser_path.write_bytes(parser_bytes)
            staged = stage_original_pdfs(
                archive_dir / SEASONS[season]["zip"], set(per_pdf), temp
            )
            jobs = []
            for filename, selected_games in sorted(per_pdf.items()):
                timestamps = {str(x["published_timestamp_utc"])
                              for x in selected_games}
                if len(timestamps) != 1:
                    raise ValueError(f"{season}: one selected PDF has multiple original UTC clocks")
                jobs.append((
                    filename, str(staged[filename]), next(iter(timestamps)),
                    {str(x["matchup_norm"]) for x in selected_games},
                    season, original_source_file(season, filename),
                ))
            gathered = []
            warning_count = 0
            with ProcessPoolExecutor(
                max_workers=workers, initializer=load_original_parser,
                initargs=(str(original_parser_path),),
            ) as pool:
                for filename, rows, _, warning in pool.map(parse_one_selected_pdf, jobs):
                    gathered.extend((filename, row) for row in rows)
                    warning_count += bool(warning)
            candidate = assemble_selected_rows(
                gathered, choices, season, list(original.columns), helpers
            )
            comparison = compare_original_22_fields(candidate, original, season)
            private_csv = output_dir / accepted_source_filename(season)
            candidate.to_csv(private_csv, index=False)
            reports[season] = {
                **comparison,
                "source_zip_sha256": SEASONS[season]["sha256"],
                "original_parser_sha256": parser_sha,
                "parser_warning_pdfs": warning_count,
                "private_generated_filename": private_csv.name,
            }
    result = {
        "status": "pass", "seasons": reports,
        "original_pdfs_total": sum(x["original_pdfs_reparsed"] for x in reports.values()),
        "selected_rows_total": sum(x["selected_player_report_rows"] for x in reports.values()),
        "all_selected_22_field_records_exact": True,
        "historical_2020_21_reason_discrepancy_unresolved": True,
        "original_raw_archives_modified": False,
        "private_player_rows_committed": False,
    }
    (output_dir / "2021_2024_raw_pdf_report_acceptance.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--seasons", nargs="+", choices=tuple(SEASONS),
                   default=list(SEASONS))
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    print(json.dumps(
        rebuild(a.archive_dir, a.output_dir, seasons=tuple(a.seasons), workers=a.workers),
        indent=2,
    ))


if __name__ == "__main__":
    main()
