#!/usr/bin/env python3
"""Substitute independently computed 2020/2024 selectors into private October inputs.

The generator normally consumes pinned historical parsed rows and schedules.
With --require-raw-2020, its 2020 parsed rows must originate from the fresh
617-PDF stage; historical report clocks and the 2024 rows remain inherited.
"""
from __future__ import annotations

import argparse
from collections import Counter
import io
import json
from pathlib import Path
import shutil

import pandas as pd

if __package__:
    from .verify_canonical_selector_replay import (
        GAME_SCIENTIFIC_FIELDS, TEAM_SCIENTIFIC_FIELDS, compare_records, file_sha256,
    )
else:
    from verify_canonical_selector_replay import (
        GAME_SCIENTIFIC_FIELDS, TEAM_SCIENTIFIC_FIELDS, compare_records, file_sha256,
    )

RELATIVE = Path("cadence_work/selector/nba_canonical_snapshot_selector_v1")
RAW_2020_TARGET = Path("cadence_work/season_parsed/2020-21/s1_snapshot_rows_corrected.csv")
RAW_2020_EXPECTED_ROWS = 41780
EXPECTED = {
    "2020-21_game_snapshot_join_harmonized_canonical.csv": (["game_id"], GAME_SCIENTIFIC_FIELDS, 1080),
    "2020-21_team_game_status_harmonized_canonical.csv": (["game_id", "team_role"], TEAM_SCIENTIFIC_FIELDS, 2160),
    "2024-25_game_snapshot_join_harmonized_canonical.csv": (["game_id"], GAME_SCIENTIFIC_FIELDS, 1230),
    "2024-25_team_game_status_harmonized_canonical.csv": (["game_id", "team_role"], TEAM_SCIENTIFIC_FIELDS, 2460),
}


def inject(generated_dir: Path, historical_root: Path, report: Path,
           require_raw_2020: bool = False) -> dict:
    generated_dir, historical_root = generated_dir.resolve(), historical_root.resolve()
    if generated_dir == historical_root or generated_dir in historical_root.parents or historical_root in generated_dir.parents:
        raise ValueError("Generated selectors and historical inputs must be disjoint")
    if report.exists() or report.is_symlink():
        raise FileExistsError(report)
    source_manifest = generated_dir / "selector_replay_manifest.json"
    if source_manifest.is_symlink() or not source_manifest.is_file():
        raise FileNotFoundError("Source selector replay manifest missing or symlinked")
    provenance = json.loads(source_manifest.read_text())
    if not provenance.get("all_selected_season_cases_passed") or len(provenance.get("cases", [])) != 4:
        raise ValueError("2020/2024 selector algorithm replay was not fully accepted")
    original_2020=provenance.get("inputs", {}).get("2020-21", {}).get("parsed_rows_consumed", {})
    if require_raw_2020 and (original_2020.get("kind")!="recomputed_intermediate" or
                             original_2020.get("origin")!="original_injury_PDFs" or
                             original_2020.get("historical_report_timestamps_inherited") is not True):
        raise ValueError("Strict 2020 handoff requires fresh original-PDF parsed rows")
    raw_source = None
    raw_record = None
    if require_raw_2020:
        raw_source = Path(original_2020.get("path", ""))
        raw_target = historical_root / RAW_2020_TARGET
        if (raw_source.is_symlink() or not raw_source.is_file() or
                raw_target.is_symlink() or not raw_target.is_file() or
                raw_source == raw_target or
                file_sha256(raw_source) != original_2020.get("sha256")):
            raise ValueError("Fresh 2020 parsed-row source missing or hash changed")
        source_rows, restored_rows = pd.read_csv(raw_source), pd.read_csv(raw_target)
        if (list(source_rows.columns) != list(restored_rows.columns) or
                len(source_rows) != RAW_2020_EXPECTED_ROWS or
                len(restored_rows) != RAW_2020_EXPECTED_ROWS):
            raise ValueError("Fresh 2020 October parsed-row schema/count differs")
        def records(frame):
            normalized=pd.read_csv(io.StringIO(frame.to_csv(index=False)),dtype=str,keep_default_na=False)
            return Counter(normalized.itertuples(index=False,name=None))
        if records(source_rows) != records(restored_rows):
            raise ValueError("Fresh 2020 October parsed-row values differ from restored source")
        raw_record = {"source_sha256": file_sha256(raw_source),
                      "restored_sha256": file_sha256(raw_target),
                      "rows": len(source_rows), "consumed_path": str(RAW_2020_TARGET)}
    records = []
    for name, (keys, fields, expected_rows) in EXPECTED.items():
        source, target = generated_dir / name, historical_root / RELATIVE / name
        if any(path.is_symlink() or not path.is_file() for path in (source, target)):
            raise FileNotFoundError(f"Missing/symlinked source or historical selector: {name}")
        item = provenance.get("generated_selector_tables", {}).get(name, {})
        raw_2020=bool(require_raw_2020 and name.startswith("2020-21_"))
        if (item.get("sha256") != file_sha256(source) or item.get("rows") != expected_rows
                or item.get("generated_from_original_pdfs_directly") is not raw_2020
                or item.get("input_rows_are_pinned_historical_parser_outputs") is raw_2020):
            raise ValueError(f"Generated selector manifest mismatch: {name}")
        comparison = compare_records(pd.read_csv(source), pd.read_csv(target), keys, fields, expected_rows)
        records.append({"filename": name, "source_sha256": item["sha256"],
                        "archived_sha256": file_sha256(target), "comparison": comparison,
                        "consumed_path": str((RELATIVE / name).as_posix())})
    # All tables pass before any private historical input is replaced.
    for record in records:
        source = generated_dir / record["filename"]
        target = historical_root / RELATIVE / record["filename"]
        temporary = target.with_name(target.name + ".generated.tmp")
        with source.open("rb") as stream, temporary.open("xb") as dest:
            shutil.copyfileobj(stream, dest)
        if file_sha256(temporary) != record["source_sha256"]:
            raise ValueError("Generated selector changed during private substitution")
        temporary.replace(target)
    if raw_record:
        target = historical_root / RAW_2020_TARGET
        temporary = target.with_name(target.name + ".generated.tmp")
        with raw_source.open("rb") as stream, temporary.open("xb") as dest:
            shutil.copyfileobj(stream, dest)
        if file_sha256(temporary) != raw_record["source_sha256"]:
            raise ValueError("Fresh 2020 source rows changed during private substitution")
        temporary.replace(target)
    result = {
        "scope": "2020/2024 selector algorithm replay from pinned historical parser rows, manifests and schedules; not direct original PDF parsing",
        "generated_selectors_fed_to_october_historical_builder": True,
        "other_four_seasons_still_inherited": True,
        "fresh_original_PDF_2020_selector_rows_fed_downstream": require_raw_2020,
        "fresh_original_PDF_2020_parsed_rows_fed_to_october_builder": bool(raw_record),
        "fresh_2020_parsed_rows_handoff": raw_record,
        "historical_2020_report_timestamps_still_inherited": require_raw_2020,
        "replay_manifest_sha256": file_sha256(source_manifest),
        "tables": records,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--generated-dir", type=Path, required=True)
    p.add_argument("--historical-root", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--require-raw-2020", action="store_true")
    args = p.parse_args()
    print(json.dumps(inject(args.generated_dir, args.historical_root, args.report,
                            require_raw_2020=args.require_raw_2020), indent=2))


if __name__ == "__main__":
    main()
