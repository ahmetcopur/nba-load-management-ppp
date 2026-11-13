#!/usr/bin/env python3
"""Substitute independently computed 2020/2024 selectors into private October inputs.

The generator still consumes pinned historical parsed rows and schedules. This
handoff does not establish original-PDF-to-selector reconstruction.
"""
from __future__ import annotations

import argparse
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
EXPECTED = {
    "2020-21_game_snapshot_join_harmonized_canonical.csv": (["game_id"], GAME_SCIENTIFIC_FIELDS, 1080),
    "2020-21_team_game_status_harmonized_canonical.csv": (["game_id", "team_role"], TEAM_SCIENTIFIC_FIELDS, 2160),
    "2024-25_game_snapshot_join_harmonized_canonical.csv": (["game_id"], GAME_SCIENTIFIC_FIELDS, 1230),
    "2024-25_team_game_status_harmonized_canonical.csv": (["game_id", "team_role"], TEAM_SCIENTIFIC_FIELDS, 2460),
}


def inject(generated_dir: Path, historical_root: Path, report: Path) -> dict:
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
    records = []
    for name, (keys, fields, expected_rows) in EXPECTED.items():
        source, target = generated_dir / name, historical_root / RELATIVE / name
        if any(path.is_symlink() or not path.is_file() for path in (source, target)):
            raise FileNotFoundError(f"Missing/symlinked source or historical selector: {name}")
        item = provenance.get("generated_selector_tables", {}).get(name, {})
        if (item.get("sha256") != file_sha256(source) or item.get("rows") != expected_rows
                or item.get("generated_from_original_pdfs_directly") is not False
                or item.get("input_rows_are_pinned_historical_parser_outputs") is not True):
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
    result = {
        "scope": "2020/2024 selector algorithm replay from pinned historical parser rows, manifests and schedules; not direct original PDF parsing",
        "generated_selectors_fed_to_october_historical_builder": True,
        "other_four_seasons_still_inherited": True,
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
    args = p.parse_args()
    print(json.dumps(inject(args.generated_dir, args.historical_root, args.report), indent=2))


if __name__ == "__main__":
    main()
