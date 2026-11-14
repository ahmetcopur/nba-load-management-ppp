#!/usr/bin/env python3
"""Rebuild 2020–21 selected reports from the original layout-preserving PDF parser.

The original 2020 source parser is immutable (SHA pinned). Reassign ONLY
visually wrapped reason prefixes carried into the next printed player row.
No original archived injury 'reason' is copied into the generated rows.
The original source 15-column table and selected 22-column panel are used
only to fail closed if any independently parsed row differs.

An optional --previous-reparse-csv permits reusing the earlier full 617-PDF
original-source diagnostic output; that mode is explicitly distinguished
from a NEW raw-PDF execution. Without this flag, parse all 617 PDFs afresh.
All output CSVs MUST remain private, outside Git.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

RAW_ZIP = "audit_2020_21_upload.zip"
RAW_SHA = "e310c8149701fb16cda9b1a136fbfcf9af8af8de9ca2ed09080f364a493c272c"
CORRECTED_ZIP = "audit_2020_21_corrected_outputs.zip"
CORRECTED_SHA = "295e854897027949f4e4246016c36cb53aa1cb4c55aa2331b3b3aef8bb6f3ad8"
CORE_ZIP = "nba_player_game_at_risk_core_v1.zip"
CORE_SHA = "a0f82ebcf6117554a4ce1064ab79db9cf93acc5a53fa25000343810843e659f6"
PARSER_SHA = "77fb85d6e0634c01d0ddb0739294c0ed044671b5b93b0affbbf9ec943a7ef6ee"
SELECTED_FILE = "selected_report_rows_2020_21_from_original_PDFs.csv"
FULL_SOURCE_FILE = "s1_snapshot_rows_2020_21_from_original_PDFs.csv"
EXPECTED_PDFS, EXPECTED_SOURCE_ROWS, EXPECTED_SELECTED_ROWS = 617, 41780, 8591
_PARSE = None


def digest(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def repair_reason_overflows(records: list[dict]) -> tuple[list[dict], dict]:
    """Relocate *printed* reason-column overflow to the preceding player(s).

    A second printed player may have a reason column that starts with the
    prior player's wrapped final word(s), then a new 'Injury/Illness -'
    or 'G League -' standard reason. All consecutively repeated identical
    prior reasons on the same team can share the missing tail. The literal
    'Management Health and Safety Protocols' case is recognized by printed
    official reason boundaries and a clipped prior reason ending in 'Injury'.
    No archived expected reason text is accessed or substituted.
    """
    result = [dict(x) for x in records]
    transfers, completed = 0, 0
    starters = ("Injury/Illness - ", "G League - ")
    for i in range(1, len(result)):
        current = result[i]
        reason = str(current.get("reason") or "")
        if not reason or any(reason.startswith(x) for x in starters):
            continue
        positions = [reason.index(s) for s in starters
                     if s in reason and reason.index(s) > 0]
        if reason == "Management Health and Safety Protocols":
            positions.append(len("Management "))
        if not positions:
            continue
        pos = min(positions)
        prefix = reason[:pos].strip()
        previous = result[i-1]
        if (not prefix or
            current.get("source_file") != previous.get("source_file") or
            current.get("matchup_norm") != previous.get("matchup_norm")):
            continue
        old = str(previous.get("reason") or "")
        if not old.startswith("Injury/Illness - "):
            continue
        if reason == "Management Health and Safety Protocols" and not old.endswith("Injury"):
            continue
        j = i - 1
        while j >= 0 and all(result[j].get(k) == previous.get(k) for k in
                             ("source_file", "matchup_norm", "team_norm")) and \
                             result[j].get("reason") == old:
            result[j]["reason"] = old + " " + prefix
            completed += 1
            j -= 1
        current["reason"] = reason[pos:]
        transfers += 1
    return result, {"overflow_fragments_transferred": transfers,
                    "preceding_source_reasons_completed": completed}


def full_record_counter(data: pd.DataFrame):
    # The actual CSV normalization is part of the original file interface.
    csv = data.to_csv(index=False)
    normalized = pd.read_csv(io.StringIO(csv), dtype=str, keep_default_na=False)
    return Counter(tuple(row) for row in normalized.itertuples(index=False, name=None))


def assert_full_original_equality(generated: pd.DataFrame,
                                  reference: pd.DataFrame,
                                  count: int, label: str) -> dict:
    if list(generated.columns) != list(reference.columns):
        raise ValueError(f"{label}: original 15/22-column schema/order differs")
    if len(generated) != count or len(reference) != count:
        raise ValueError(f"{label}: expected {count} records")
    actual, historical = full_record_counter(generated), full_record_counter(reference)
    if actual != historical:
        raise ValueError(f"{label}: original complete record mismatch: "
                         f"missing={sum((historical-actual).values())} "
                         f"extra={sum((actual-historical).values())}")
    return {"rows": count, "columns": len(generated.columns),
            "every_original_column_and_full_record_exact": True}


def init_original_parser(path: str):
    global _PARSE
    import pdfplumber
    spec = importlib.util.spec_from_file_location("_pinned_2020_nba_parser", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    old = pdfplumber.page.Page.extract_text
    def exact_layout(self, *args, **kwargs):
        kwargs["x_density"] = 5.0
        return old(self, *args, **kwargs)
    pdfplumber.page.Page.extract_text = exact_layout
    _PARSE = mod.parse_pdf


def parse_pdf(task):
    basename, path, source, report_date, utc = task
    rows, pages, warning = _PARSE(
        Path(path), season="2020-21", report_date=report_date,
        snapshot_utc=utc, source_file=source
    )
    if not pages or pages < 1:
        raise ValueError(f"Original 2020 PDF missing extracted pages: {basename}")
    return basename, rows, warning


def safe_output(source: Path, output: Path):
    source, output = source.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError("Original 2020 source rebuild output directory already exists")
    if not source.is_dir() or source in output.parents or output in source.parents or source == output:
        raise ValueError("Original ZIPs and output must use separate private directories")
    if any((p / ".git").exists() for p in (output, *output.parents)):
        raise ValueError("Private source rows must not be created inside Git checkout")


def rebuild(archive_dir: Path, output_dir: Path, *,
            workers: int = 4, previous_reparse_csv: Path | None = None,
            emit_full_source_rows: bool = False) -> dict:
    archive_dir, output_dir = archive_dir.resolve(), output_dir.resolve()
    safe_output(archive_dir, output_dir)
    if not 1 <= workers <= 16:
        raise ValueError("2020 original PDF workers must be 1..16")
    for filename, pinned in ((RAW_ZIP, RAW_SHA), (CORRECTED_ZIP, CORRECTED_SHA),
                             (CORE_ZIP, CORE_SHA)):
        if digest(archive_dir / filename) != pinned:
            raise ValueError(f"Immutable original source ZIP SHA changed: {filename}")
    with ZipFile(archive_dir / CORRECTED_ZIP) as zip_archive:
        parser = zip_archive.read("nba_injury_pdf_layout_parser.py")
        if hashlib.sha256(parser).hexdigest() != PARSER_SHA:
            raise ValueError("Immutable original 2020 PDF parser source changed")
        original_full = pd.read_csv(io.BytesIO(
            zip_archive.read("s1_snapshot_rows_corrected.csv")), low_memory=False)
    with ZipFile(archive_dir / CORE_ZIP) as zip_archive:
        canonical = pd.read_csv(io.BytesIO(zip_archive.read(
            "nba_player_game_at_risk_core_v1/canonical_game_snapshot_map.csv")),
            low_memory=False)
        selected_reference = pd.read_csv(io.BytesIO(zip_archive.read(
            "nba_player_game_at_risk_core_v1/selected_report_rows_all.csv")),
            low_memory=False)
    canonical = canonical.loc[canonical.season.eq("2020-21")].copy()
    selected_reference = selected_reference.loc[selected_reference.season.eq("2020-21")].copy()
    if len(canonical) != 1080:
        raise ValueError("Original 2020 canonical game selector changed")
    meta = {}
    for r in original_full[["source_file", "report_date",
                             "snapshot_timestamp_utc"]].drop_duplicates().itertuples(index=False):
        basename = Path(r.source_file).name
        if basename in meta:
            raise ValueError("Original 2020 PDF source basenames ambiguous")
        meta[basename] = (r.source_file, r.report_date, r.snapshot_timestamp_utc)
    if len(meta) != EXPECTED_PDFS:
        raise ValueError("Original 2020 source must comprise all 617 saved PDFs")
    if previous_reparse_csv is not None:
        previous = Path(previous_reparse_csv).resolve()
        if any((p / ".git").exists() for p in previous.parents):
            raise ValueError("Private raw PDF reparse cannot be inside Git")
        raw = pd.read_csv(previous, low_memory=False)
        if list(raw.columns) != list(original_full.columns):
            raise ValueError("Prior original 2020 parser output schema changed")
        if len(raw) != EXPECTED_SOURCE_ROWS:
            raise ValueError("Prior 2020 source PDF reparse is incomplete")
        # The uncorrected diagnostic must match *all nonreason fields*,
        # so an arbitrary source CSV with different rows cannot be accepted.
        nonreason = [c for c in raw.columns if c != "reason"]
        if full_record_counter(raw[nonreason]) != full_record_counter(original_full[nonreason]):
            raise ValueError("Previously parsed original PDF source identity fields differ")
        by_pdf = {name: group.to_dict("records") for name, group in
                  raw.groupby(raw.source_file.map(lambda x: Path(x).name),
                              sort=False)}
        parsed = [row for name in sorted(meta) for row in by_pdf.get(name, [])]
        if len(parsed) != EXPECTED_SOURCE_ROWS:
            raise ValueError("Previous full 617-PDF source reparse incomplete")
        fresh_pdf_execution = False
    else:
        with TemporaryDirectory(prefix="nba_private_2020_original_PDFs_") as scratch:
            tmp = Path(scratch)
            parser_file = tmp / "immutable_2020_original_parser.py"
            parser_file.write_bytes(parser)
            with ZipFile(archive_dir / RAW_ZIP) as zip_archive:
                members = [m for m in zip_archive.namelist() if m.endswith(".pdf")]
                if len(members) != EXPECTED_PDFS or \
                   {Path(m).name for m in members} != set(meta):
                    raise ValueError("2020 original raw ZIP PDF inventory differs")
                tasks = []
                for m in sorted(members):
                    basename = Path(m).name
                    file = tmp / basename
                    file.write_bytes(zip_archive.read(m))
                    source, date, utc = meta[basename]
                    tasks.append((basename, str(file), source, date, utc))
                parsed = []
                with ProcessPoolExecutor(max_workers=workers,
                                         initializer=init_original_parser,
                                         initargs=(str(parser_file),)) as pool:
                    for _, records, _ in pool.map(parse_pdf, tasks):
                        parsed.extend(records)
        fresh_pdf_execution = True

    corrected, repair = repair_reason_overflows(parsed)
    fixed_source = pd.DataFrame(corrected)[list(original_full.columns)]
    full = assert_full_original_equality(
        fixed_source, original_full, EXPECTED_SOURCE_ROWS, "2020 original raw PDFs"
    )
    fixed_source["snapshot_basename"] = fixed_source.source_file.map(lambda x: Path(x).name)
    fixed_source["published_timestamp_utc"] = fixed_source.snapshot_timestamp_utc
    keys = ["snapshot_basename", "published_timestamp_utc", "matchup_norm"]
    fields = ["canonical_game_id", "source_match_number", "game_id",
              "minutes_before_tip", "qc_selected_within_30m"]
    output = fixed_source.merge(canonical[keys+fields], on=keys,
                                how="inner", validate="many_to_many")
    output = output[list(selected_reference.columns)]
    selected = assert_full_original_equality(
        output, selected_reference, EXPECTED_SELECTED_ROWS, "2020 canonical selected reports"
    )
    output_dir.mkdir(parents=True, exist_ok=False)
    output.to_csv(output_dir / SELECTED_FILE, index=False)
    if emit_full_source_rows:
        fixed_source[list(original_full.columns)].to_csv(output_dir / FULL_SOURCE_FILE, index=False)
    evidence = {
        "status": "pass", "season": "2020-21",
        "source_pdf_count": EXPECTED_PDFS, "parsed_original_source": full,
        "selected_original_source": selected, **repair,
        "original_2020_source_parser_sha256": PARSER_SHA,
        "original_2020_raw_zip_sha256": RAW_SHA,
        "source_reason_text_replaced_with_archived_value": False,
        "fresh_original_617_PDF_execution_in_this_invocation": fresh_pdf_execution,
        "full_source_rows_filename": FULL_SOURCE_FILE if emit_full_source_rows else None,
        "full_source_rows_sha256": digest(output_dir / FULL_SOURCE_FILE) if emit_full_source_rows else None,
        "original_canonical_report_choice_metadata_inherited": True,
        "frozen_original_research_files_changed": False,
        "private_player_report_rows_committed": False,
    }
    (output_dir / "2020_21_original_pdf_source_acceptance.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--previous-reparse-csv", type=Path,
                   help="Re-use existing complete private 617-PDF diagnostic CSV instead of freshly parsing all PDFs")
    p.add_argument("--emit-full-source-rows", action="store_true",
                   help="Retain the verified 41,780 raw-PDF-derived rows privately for the October selector")
    args = p.parse_args()
    print(json.dumps(rebuild(args.archive_dir, args.output_dir,
                             workers=args.workers,
                             previous_reparse_csv=args.previous_reparse_csv,
                             emit_full_source_rows=args.emit_full_source_rows), indent=2))


if __name__ == "__main__":
    main()
