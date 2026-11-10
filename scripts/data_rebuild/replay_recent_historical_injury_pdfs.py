#!/usr/bin/env python3
"""Replay real 2024–25 or selected 2025–26 NBA injury PDFs against frozen rows.

Requires the PRIVATE original source ZIPs and source-provenance metadata at
OEKundakcioglu/nba-ppp-star-availability@0bd713d97e8d519df5700ef473da34aba4495223.
Never writes original archives, publishes raw PDFs, or changes frozen releases.
This is PDF-to-row replay against an ARCHIVED selector, not independent selector
choice or end-to-end causal estimation.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
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

try:
    from scripts.data_rebuild.verify_historical_injury_archives import verify as verify_archives
except ModuleNotFoundError:
    from verify_historical_injury_archives import verify as verify_archives

PARSER_MEMBER = "nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py"
PARSER_SHA256 = "197c29d46dfea221c381664b96a05453737df55d7b8dd5d5e6f44e49b69e0e06"
CORE_PREFIX = "nba_player_game_at_risk_core_v1/"
REFERENCE_2024 = {
    "manifest": "report_manifest_regular_season.csv",
    "rows": "s1_snapshot_rows_regular_season.csv",
    "logs": "s1_parse_log_regular_season.csv",
}
ROW_FIELDS = (
    "season", "source_file", "report_date", "snapshot_timestamp_utc",
    "game_date_raw", "game_time_et_raw", "matchup", "matchup_norm",
    "team", "team_norm", "player_name", "player_name_norm",
    "current_status", "reason", "team_submission_status",
)
_PARSER = None


def read_member_csv(archive: ZipFile, name: str) -> list[dict[str, str]]:
    with io.TextIOWrapper(archive.open(name), encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        if not columns or len(columns) != len(set(columns)):
            raise ValueError(f"Missing/duplicate CSV fields in {name}")
        result = list(reader)
        if any(None in row for row in result):
            raise ValueError(f"Malformed CSV data in {name}")
        return result


def row_key(row: dict[str, object]) -> tuple[str, ...]:
    return tuple("" if row.get(key) is None else str(row[key]) for key in ROW_FIELDS)


def reference_groups(rows: list[dict[str, str]], source_key: str):
    groups = defaultdict(Counter)
    for row in rows:
        if not set(ROW_FIELDS) <= set(row):
            raise ValueError("Reference rows missing complete original parser fields")
        groups[row[source_key]][row_key(row)] += 1
    return groups


def init_parser(path: str) -> None:
    global _PARSER
    spec = importlib.util.spec_from_file_location("_pinned_nba_pdf_parser", path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot import pinned original parser")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _PARSER = module.parse_pdf


def parse_task(task):
    filename, path, season, report_date, timestamp, source_file, matchups = task
    if _PARSER is None:
        raise RuntimeError("Pinned original PDF parser worker not initialized")
    rows, pages, warning = _PARSER(
        Path(path), season=season, report_date=report_date,
        snapshot_utc=timestamp, source_file=source_file
    )
    chosen = rows if matchups is None else [r for r in rows if r["matchup_norm"] in matchups]
    return filename, chosen, len(rows), pages, warning


def prep_source_files(archive_dir: Path, archives: tuple[str, ...],
                      required: set[str], target: Path):
    found = {}
    for archive_name in archives:
        with ZipFile(archive_dir / archive_name) as archive:
            for member in archive.namelist():
                if not member.lower().endswith(".pdf"):
                    continue
                basename = Path(member).name
                if basename not in required:
                    continue
                if basename in found:
                    raise ValueError(f"Ambiguous duplicate PDF basename across original ZIPs: {basename}")
                path = target / basename
                if not re.fullmatch(r"Injury-Report_\d{4}-\d\d-\d\d_[A-Za-z0-9_]+\.pdf", basename):
                    raise ValueError(f"Unexpected PDF filename: {basename}")
                path.write_bytes(archive.read(member))
                found[basename] = (member, str(path))
    if set(found) != required:
        raise ValueError(f"Missing original source PDFs: {len(required - set(found))}")
    return found


def replay(mode: str, archive_dir: Path, metadata_dir: Path, core_path: Path,
           reference_2024: Path | None, *, workers: int = 4) -> dict[str, object]:
    if workers < 1 or workers > 16:
        raise ValueError("workers must be 1..16")
    archives = (("audit_2024_25_upload.zip",) if mode == "2024-25" else
                ("audit_2025_26_upload.zip", "audit_2025_26_targeted_upload.zip"))
    provenance = verify_archives(archive_dir, metadata_dir, archives)
    if not provenance["all_indexed_pdf_members_verified"] or not provenance["pinned_provenance_verified"]:
        raise ValueError("Original source ZIP/inventory provenance checks did not pass")

    with ZipFile(core_path) as core:
        parser_bytes = core.read(PARSER_MEMBER)
        if hashlib.sha256(parser_bytes).hexdigest() != PARSER_SHA256:
            raise ValueError("Original historical parser SHA-256 differs from pinned version")

        if mode == "2024-25":
            if reference_2024 is None:
                raise ValueError("--reference-2024-zip required for 2024-25")
            with ZipFile(reference_2024) as frozen:
                manifest = read_member_csv(frozen, REFERENCE_2024["manifest"])
                original_rows = read_member_csv(frozen, REFERENCE_2024["rows"])
                original_logs = read_member_csv(frozen, REFERENCE_2024["logs"])
            selected = [r for r in manifest if r["exists"].strip().lower() in ("true", "1")]
            if len(selected) != 4078 or len(original_rows) != 418059:
                raise ValueError("2024-25 reference manifest/rows do not match frozen release")
            expected = reference_groups(original_rows, "source_file")
            logs = {r["source_file"]: r for r in original_logs}
            if len(logs) != 4078 or len(set(r["local_path"] for r in selected)) != 4078:
                raise ValueError("Duplicate or missing original 2024 PDF source identities")
            source_files = {Path(r["local_path"]).name for r in selected}
            expected_selected_rows = 418059
            expected_files = 4078
        elif mode == "2025-26":
            selected = [r for r in read_member_csv(core, CORE_PREFIX + "canonical_game_snapshot_map.csv")
                        if r["season"] == "2025-26"]
            original_rows = [r for r in read_member_csv(core, CORE_PREFIX + "selected_report_rows_all.csv")
                             if r["season"] == "2025-26"]
            original_logs = [r for r in read_member_csv(core, CORE_PREFIX + "selected_snapshot_parse_log.csv")
                             if r["season"] == "2025-26"]
            expected = reference_groups(original_rows, "snapshot_basename")
            logs = {r["snapshot_basename"]: r for r in original_logs}
            source_files = {r["snapshot_basename"] for r in selected}
            if (len(selected) != 1230 or len(source_files) != 729
                    or len(original_rows) != 13968 or len(logs) != 729
                    or len(original_logs) != 729):
                raise ValueError("2025-26 frozen selection/row/parser-log input changed")
            expected_selected_rows = 13968
            expected_files = 729
        else:
            raise ValueError("mode must be 2024-25 or 2025-26")

        with TemporaryDirectory(prefix="nba_private_pdf_replay_") as temp:
            tempdir = Path(temp)
            parser_path = tempdir / "pinned_parser_2023plus.py"
            parser_path.write_bytes(parser_bytes)
            staged = prep_source_files(archive_dir, archives, source_files, tempdir)
            tasks = []
            if mode == "2024-25":
                for row in selected:
                    source = row["local_path"]
                    basename = Path(source).name
                    tasks.append((basename, staged[basename][1], mode, row["report_date"],
                                  row["published_timestamp_utc"], source, None))
            else:
                games = defaultdict(list)
                for row in selected:
                    games[row["snapshot_basename"]].append(row)
                for basename, selected_games in games.items():
                    stamps = {row["published_timestamp_utc"] for row in selected_games}
                    if len(stamps) != 1:
                        raise ValueError(f"One 2025 PDF has multiple published timestamps: {basename}")
                    report_date = re.search(r"Injury-Report_(\d{4}-\d\d-\d\d)_", basename).group(1)
                    tasks.append((basename, staged[basename][1], mode, report_date,
                                  next(iter(stamps)), basename,
                                  {row["matchup_norm"] for row in selected_games}))

            mismatched_rows = 0
            mismatched_logs = 0
            parsed_files = 0
            selected_rows_count = 0
            # No raw player data, reason fields or parsed rows are persisted.
            with ProcessPoolExecutor(max_workers=workers, initializer=init_parser,
                                     initargs=(str(parser_path),)) as executor:
                for basename, result_rows, whole_pdf_rows, pages, warning in executor.map(parse_task, tasks):
                    parsed_files += 1
                    selected_rows_count += len(result_rows)
                    source_ref = staged[basename][0] if mode == "2024-25" else basename
                    reference = expected.pop(source_ref, Counter())
                    candidate = Counter(row_key(row) for row in result_rows)
                    if reference != candidate:
                        mismatched_rows += 1
                    reference_log = logs.pop(source_ref, None)
                    if reference_log is None:
                        mismatched_logs += 1
                    else:
                        checks = {
                            "pages": str(pages),
                            ("extracted_rows" if mode == "2024-25" else "rows"): str(whole_pdf_rows),
                            "status": "ok" if whole_pdf_rows else "zero_rows",
                            "warning": warning or "",
                        }
                        if mode == "2024-25":
                            matching = next(r for r in selected if r["local_path"] == source_ref)
                            checks["snapshot_timestamp_utc"] = matching["published_timestamp_utc"]
                        if any(reference_log.get(k, "") != v for k, v in checks.items()):
                            mismatched_logs += 1

    report = {
        "scope": "Verified original raw PDF -> archived full-record/parser-log replay only",
        "season": mode,
        "pinned_parser_sha256": PARSER_SHA256,
        "original_archive_provenance_passed": True,
        "pdf_files_reparsed": parsed_files,
        "expected_pdf_files": expected_files,
        "selected_report_rows_reparsed": selected_rows_count,
        "expected_selected_report_rows": expected_selected_rows,
        "pdfs_with_row_multiset_differences": mismatched_rows,
        "pdfs_with_parser_log_differences": mismatched_logs,
        "unmatched_reference_record_groups": len(expected),
        "unmatched_reference_parser_log_groups": len(logs),
        "independently_rebuilt_report_selector": False,
        "end_to_end_model_rebuilt": False,
    }
    report["passed"] = (
        parsed_files == expected_files
        and selected_rows_count == expected_selected_rows
        and not mismatched_rows and not mismatched_logs
        and not expected and not logs
    )
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("2024-25", "2025-26"), required=True)
    p.add_argument("--archive-dir", type=Path, required=True)
    p.add_argument("--metadata-dir", type=Path, required=True)
    p.add_argument("--core-zip", type=Path, required=True)
    p.add_argument("--reference-2024-zip", type=Path)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    result = replay(a.mode, a.archive_dir, a.metadata_dir, a.core_zip,
                    a.reference_2024_zip, workers=a.workers)
    rendered = json.dumps(result, indent=2) + "\n"
    if a.output:
        if a.output.exists():
            raise FileExistsError(f"Refusing to overwrite existing audit: {a.output}")
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not result["passed"]:
        raise SystemExit("Original PDF-to-archived-rows replay mismatch; frozen data unchanged")


if __name__ == "__main__":
    main()
