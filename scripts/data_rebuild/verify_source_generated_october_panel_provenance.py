#!/usr/bin/env python3
"""Fail-closed provenance bridge for source-rebuilt Oct panel -> 10 released scripts.

Check a sanitized real-original-input execution record (the actual locally
source-generated October panel) against the freshly fetched, pinned original
October public release panel. This is equality of decoded full CSV content,
not a claim that CI can open private NBA report ZIPs. The released ten
scripts use the public file, which is byte-identical after gzip decoding to
the independently source-generated private panel; therefore their deterministic
input cells are identical.

Inputs are checked against the declared source evidence field names, selected
PDF counts, original data-generation stage and exact 122,661,378-byte digest.
Never take a checksum alone from an arbitrary unverified JSON report.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / (
    "validation/level_c_injury_pdf_real_2026-11-10/"
    "source_generated_october_cadence_panel_and_four_models.json"
)
EXPECTED_SHA = "3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac"
EXPECTED_BYTES = 122661378
EXPECTED_PDFS = 355
EXPECTED_STAGE6_MODELS = 4
EXPECTED_SOURCE_PANEL_ROWS = 248778
EXPECTED_STAGE6_ZIP = "821b50373d0ab6f27237d05f2d1d2b32f669f2bbbcd25e7fe0cdd5cd8292b221"


def hash_decoded_gzip(path: Path) -> tuple[str, int]:
    sha, count = hashlib.sha256(), 0
    with gzip.open(path, "rb") as src:
        for data in iter(lambda: src.read(1024 * 1024), b""):
            sha.update(data)
            count += len(data)
    return sha.hexdigest(), count


def validate_real_source_evidence(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ValueError("Original-source provenance record must be a JSON object")
    panel = record.get("full_harmonized_panel_exact") or {}
    if (not isinstance(panel, dict)
        or panel.get("all_original_and_rebuilt_decoded_CSV_bytes_equal") is not True
        or panel.get("sha256") != EXPECTED_SHA
        or panel.get("decoded_bytes") != EXPECTED_BYTES):
        raise ValueError("Real-original-PDF October panel equality evidence absent or changed")
    raw = record.get("original_2025_harmonized_pdf_reparse") or {}
    if (not isinstance(raw, dict)
        or raw.get("actual_selected_original_pdfs") != EXPECTED_PDFS
        or raw.get("parsed_report_rows") != 13762):
        raise ValueError("Original 2025 cadence-PDF extraction evidence absent or changed")
    if record.get("generated_full_harmonized_player_game_rows") != EXPECTED_SOURCE_PANEL_ROWS:
        raise ValueError("Original independently built October panel row count changed")
    specs = record.get("original_stage6_four_models") or []
    comparison = record.get("original_model_comparison") or {}
    if (len(specs) != EXPECTED_STAGE6_MODELS
        or comparison.get("all_four_models_match") is not True):
        raise ValueError("Original four Stage-6 source-generated model results are unverified")
    if record.get("original_stage6_zip_sha256") != EXPECTED_STAGE6_ZIP:
        raise ValueError("Original source-code and panel-stage package fingerprint changed")
    limits = record.get("limitations") or {}
    if (limits.get("raw_2020_21_reason_differences_unresolved") != 93
        or limits.get("original_harmonized_report_choice_metadata_inherited") is not True
        or limits.get("new_GitHub_script_not_independently_rerun_from_clean_checkout_with_all_private_zips") is not True):
        raise ValueError("Original-source research limitations were dropped or changed")
    return {
        "source_generated_original_selected_2025_harmonized_PDFs": EXPECTED_PDFS,
        "source_generated_october_panel_rows": EXPECTED_SOURCE_PANEL_ROWS,
        "source_generated_4_stage6_models": True,
        "historical_2020_reason_difference_remains_unresolved": True,
        "independent_original_full_october_private_input_execution_claimed": False,
    }


def verify_equality(public_panel: Path, evidence: Path = EVIDENCE) -> dict:
    if not evidence.is_file():
        raise FileNotFoundError(f"Sanitized original-source evidence file not found: {evidence}")
    if not public_panel.is_file():
        raise FileNotFoundError(f"Pinned public October panel missing: {public_panel}")
    evidence_data = validate_real_source_evidence(
        json.loads(evidence.read_text(encoding="utf-8"))
    )
    digest, length = hash_decoded_gzip(public_panel)
    if digest != EXPECTED_SHA or length != EXPECTED_BYTES:
        raise ValueError(
            f"Original public panel differs from actual independently generated "
            f"private-source evidence: decoded_sha={digest}, decoded_bytes={length}"
        )
    return {
        "status": "pass",
        "comparison": "Full decoded public October CSV equals the recorded SHA256 of the actual independently rebuilt private original-PDF source-generated October panel",
        "original_source_report": str(evidence),
        "public_original_panel": str(public_panel),
        "identical_full_decoded_csv_sha256": digest,
        "identical_full_decoded_csv_bytes": length,
        "source_data_provenance": evidence_data,
        "source_generated_player_level_rows_reopened_by_public_CI": False,
        "full_10_script_from_original_private_PDFs_directly_executed_in_CI": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-october-panel", required=True, type=Path)
    parser.add_argument("--source-evidence", type=Path, default=EVIDENCE)
    parser.add_argument("--report", type=Path)
    a = parser.parse_args()
    result = verify_equality(a.public_october_panel, a.source_evidence)
    serialized = json.dumps(result, indent=2) + "\n"
    if a.report is not None:
        if a.report.exists():
            raise FileExistsError("Refusing to overwrite earlier provenance certificate")
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(serialized, encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
