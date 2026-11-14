#!/usr/bin/env python3
"""Rebuild selected 2025–26 injury-report ROWS from 729 original NBA PDFs.

Source images: two SHA-256-pinned original raw archive ZIPs.
Parser: unchanged SHA-256-pinned historical parser_2023plus.py.
Game/report choices, game keys, UTC clocks: original archived canonical source
map (previously independently reconstructed from original report manifests).
No player/status/reason field is borrowed from the frozen selected rows.
The frozen selected rows are used exclusively for full 22-field acceptance.

Output contains private player-level details; must be OUTSIDE a Git checkout.
This is a single-season PDF->selected-rows connector, not full raw-PDF-to-
manuscript reproducibility (other five seasons remain further dependencies).
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import hashlib
import io
import importlib.util
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
    csv_from_zip, immutable_original_helpers, sha256_file, read_member,
)
from scripts.data_rebuild.replay_recent_historical_injury_pdfs import (
    PARSER_MEMBER, PARSER_SHA256,
)

CORE_ZIP = "nba_player_game_at_risk_core_v1.zip"
CORE_SHA256 = "a0f82ebcf6117554a4ce1064ab79db9cf93acc5a53fa25000343810843e659f6"
CORE_PREFIX = "nba_player_game_at_risk_core_v1/"
SOURCE_ZIPS = {
    "audit_2025_26_upload.zip": "a0cdcb4b9e594a1b1fb63489aa43087f6c13f5b34ab3661b596c2941089c9f70",
    "audit_2025_26_targeted_upload.zip": "8a9c08e3aa92f5400cc866201051653e13b89cc6a56b5aae7deb2ad9e0f718ea",
}
OUTPUT_NAME = "2025_26_selected_report_rows_from_original_PDFs.csv"
REPORT_NAME = "2025_26_original_PDF_selected_replay.json"
EXPECTED_GAME_COUNT = 1230
EXPECTED_PDF_COUNT = 729
EXPECTED_REPORT_ROWS = 13968
EXPECTED_COLUMNS = 22
_PARSER = None


def verify_safe_destination(archive_dir: Path, output_dir: Path):
    raw, out = archive_dir.resolve(), output_dir.resolve()
    if not raw.is_dir():
        raise FileNotFoundError(f"Private original source ZIP directory not found: {raw}")
    if out.exists():
        raise FileExistsError(f"Private output path already exists: {out}")
    if out == raw or raw in out.parents or out in raw.parents:
        raise ValueError("Generated report rows must be outside source archive folder")
    if any((p / ".git").exists() for p in (out, *out.parents)):
        raise ValueError("Refusing to place private player-level report rows inside Git checkout")


def read_one_pdf_member(archive: ZipFile, member: str):
    if archive.namelist().count(member) != 1:
        raise ValueError(f"Source ZIP PDF member missing or duplicate: {member}")
    return archive.read(member)


def stage_pdfs(archive_dir: Path, needed: set[str], scratch: Path) -> dict[str, str]:
    found = {}
    for archive_name in SOURCE_ZIPS:
        with ZipFile(archive_dir / archive_name) as archive:
            for member in archive.namelist():
                name = Path(member).name
                if name not in needed or not member.lower().endswith(".pdf"):
                    continue
                if not re.fullmatch(r"Injury-Report_\d{4}-\d\d-\d\d_[A-Za-z0-9_]+\.pdf", name):
                    raise ValueError(f"Unexpected original PDF basename: {name}")
                if name in found:
                    raise ValueError(f"Ambiguous duplicate original PDF basename: {name}")
                data = read_one_pdf_member(archive, member)
                path = scratch / name
                path.write_bytes(data)
                found[name] = str(path)
    if set(found) != needed:
        raise ValueError(f"Original 2025 source ZIP missing {len(needed - set(found))} selected PDFs")
    return found


def init_parser(path: str):
    global _PARSER
    spec = importlib.util.spec_from_file_location("_nba_pinned_2025_parser", path)
    if not spec or not spec.loader:
        raise ValueError("Original 2025 PDF parser cannot be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _PARSER = module.parse_pdf


def parse_selected_pdf(task):
    name, pdf_path, timestamp, matchups = task
    if _PARSER is None:
        raise RuntimeError("Historical source parser worker was not initialized")
    report_date = re.search(r"Injury-Report_(\d{4}-\d\d-\d\d)_", name).group(1)
    records, pages, warning = _PARSER(
        Path(pdf_path), season="2025-26", report_date=report_date,
        snapshot_utc=timestamp, source_file=name,
    )
    if pages is None or pages < 1:
        raise ValueError(f"Original PDF extraction produced no pages: {name}")
    return name, [r for r in records if r["matchup_norm"] in matchups], len(records), warning


def original_2025_selection_map(canonical: pd.DataFrame):
    source = canonical.loc[canonical.season.eq("2025-26")].copy()
    if len(source) != EXPECTED_GAME_COUNT:
        raise ValueError("Expected 1,230 original 2025–26 game choices")
    required = {
        "snapshot_basename", "published_timestamp_utc", "matchup_norm",
        "canonical_game_id", "source_match_number", "game_id",
        "minutes_before_tip", "qc_selected_within_30m",
    }
    if not required <= set(source):
        raise ValueError(f"Original game selector fields missing: {required-set(source)}")
    mapping = {}
    groups = defaultdict(list)
    for r in source.to_dict("records"):
        name, matchup = str(r["snapshot_basename"]), str(r["matchup_norm"])
        if (name, matchup) in mapping:
            raise ValueError("Original game selector duplicate PDF+matchup key")
        mapping[(name, matchup)] = r
        groups[name].append(r)
    if len(mapping) != EXPECTED_GAME_COUNT or len(groups) != EXPECTED_PDF_COUNT:
        raise ValueError("Original source selected report counts changed")
    return mapping, groups


def build_report_rows(parsed: list[tuple[str, dict]], mapping: dict,
                      columns: list[str], helpers: dict):
    full = []
    for filename, source_row in parsed:
        key = (filename, str(source_row["matchup_norm"]))
        if key not in mapping:
            raise ValueError("Original PDF yielded a non-selected matchup")
        choice = mapping[key]
        r = dict(source_row)
        r.update({
            "snapshot_basename": filename,
            "canonical_game_id": choice["canonical_game_id"],
            "source_match_number": choice["source_match_number"],
            "published_timestamp_utc": choice["published_timestamp_utc"],
            "game_id": choice["game_id"],
            "minutes_before_tip": choice["minutes_before_tip"],
            "qc_selected_within_30m": choice["qc_selected_within_30m"],
        })
        full.append(r)
    if not full:
        raise ValueError("No selected original player-report rows parsed")
    if not set(columns) <= set(full[0]):
        raise ValueError(f"Parsed source does not provide 22 original fields: {set(columns)-set(full[0])}")
    frame = pd.DataFrame(full)[columns]
    frame["team_norm"] = frame.team_norm.fillna("").map(helpers["norm_team"])
    for field in ("player_name", "current_status", "reason"):
        frame[field] = frame[field].fillna("").map(helpers["clean"])
    frame = frame.drop_duplicates([
        "season", "game_id", "team_norm", "player_name",
        "current_status", "reason", "team_submission_status",
    ])
    return frame


def string_row_multiset(frame: pd.DataFrame) -> Counter:
    """Re-read actual CSV serialization before multiset comparison to handle dtypes."""
    text = frame.to_csv(index=False)
    normalized = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    return Counter(map(tuple, normalized.itertuples(index=False, name=None)))


def verify_original_row_equality(candidate: pd.DataFrame, reference: pd.DataFrame):
    if list(candidate.columns) != list(reference.columns) or len(reference.columns) != EXPECTED_COLUMNS:
        raise ValueError("Original selected-report 22-column schema changed")
    if len(candidate) != EXPECTED_REPORT_ROWS or len(reference) != EXPECTED_REPORT_ROWS:
        raise ValueError("Expected exactly 13,968 selected 2025–26 source-report rows")
    observed, frozen = string_row_multiset(candidate), string_row_multiset(reference)
    if observed != frozen:
        raise ValueError(
            f"Original 2025 raw-PDF selected rows differ from archived reference: "
            f"missing={sum((frozen-observed).values())}, extra={sum((observed-frozen).values())}"
        )
    return {
        "selected_rows": len(candidate),
        "complete_original_fields_compared": len(reference.columns),
        "all_complete_record_multisets_exact": True,
        "missing_full_records": 0, "extra_full_records": 0,
    }


def run(archive_dir: Path, output_dir: Path, *, workers: int = 4):
    archive_dir, output_dir = archive_dir.resolve(), output_dir.resolve()
    verify_safe_destination(archive_dir, output_dir)
    if workers < 1 or workers > 16:
        raise ValueError("workers must be 1..16")
    for name, expected in {CORE_ZIP: CORE_SHA256, **SOURCE_ZIPS}.items():
        if sha256_file(archive_dir / name) != expected:
            raise ValueError(f"Original private source archive SHA-256 mismatch: {name}")
    parser_bytes = read_member(archive_dir / CORE_ZIP, PARSER_MEMBER)
    if hashlib.sha256(parser_bytes).hexdigest() != PARSER_SHA256:
        raise ValueError("Original injury-report parser SHA-256 differs")
    helper = immutable_original_helpers(archive_dir)
    canonical = csv_from_zip(archive_dir, CORE_ZIP, CORE_PREFIX + "canonical_game_snapshot_map.csv")
    source_reference = csv_from_zip(archive_dir, CORE_ZIP, CORE_PREFIX + "selected_report_rows_all.csv")
    source_reference = source_reference.loc[source_reference.season.eq("2025-26")].copy()
    mapping, groups = original_2025_selection_map(canonical)
    parsed = []
    with TemporaryDirectory(prefix="nba_original_2025_pdf_") as temp:
        root = Path(temp)
        original_parser = root / "original_parser_2023plus.py"
        original_parser.write_bytes(parser_bytes)
        staged = stage_pdfs(archive_dir, set(groups), root)
        tasks = []
        for name, choices in sorted(groups.items()):
            timestamps = {str(r["published_timestamp_utc"]) for r in choices}
            if len(timestamps) != 1:
                raise ValueError(f"Original PDF has conflicting selected UTC timestamps: {name}")
            tasks.append((name, staged[name], next(iter(timestamps)),
                          {str(r["matchup_norm"]) for r in choices}))
        with ProcessPoolExecutor(
            max_workers=workers, initializer=init_parser,
            initargs=(str(original_parser),)
        ) as pool:
            for filename, records, _, _ in pool.map(parse_selected_pdf, tasks):
                parsed.extend((filename, r) for r in records)
        reconstructed = build_report_rows(
            parsed, mapping, list(source_reference.columns), helper,
        )
        acceptance = verify_original_row_equality(reconstructed, source_reference)
        # Only persist the full private player-level CSV AFTER exact acceptance.
        output_dir.mkdir(parents=True, exist_ok=False)
        generated = output_dir / OUTPUT_NAME
        reconstructed.to_csv(generated, index=False)
    report = {
        "status": "pass",
        "scope": "Original 2025–26 saved PDFs -> 22-field selected-report rows; canonical game/report choices inherited; not all seasons or manuscript",
        "private_source_zip_sha256": {CORE_ZIP: CORE_SHA256, **SOURCE_ZIPS},
        "original_parser_sha256": PARSER_SHA256,
        "original_selected_games": EXPECTED_GAME_COUNT,
        "original_pdfs_reparsed": len(groups),
        **acceptance,
        "selected_2025_rows_from_actual_raw_PDFs": True,
        "raw_player_values_copied_from_frozen_reference": False,
        "canonical_report_choice_independently_regenerated_in_this_run": False,
        "unresolved_2020_21_original_PDF_reason_discrepancy": True,
        "output_csv_filename": OUTPUT_NAME,
    }
    (output_dir / REPORT_NAME).write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    a = p.parse_args()
    print(json.dumps(run(a.archive_dir, a.output_dir, workers=a.workers), indent=2))


if __name__ == "__main__":
    main()
