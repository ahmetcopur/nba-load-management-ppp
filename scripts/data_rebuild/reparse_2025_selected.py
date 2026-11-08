#!/usr/bin/env python3
"""Replay the original 2025–26 selected-report parser and validate its QA log.

Uses the original parser script, changing only its hard-coded ROOT in a
temporary copy. Critical: the original script catches individual PDF parsing
errors, so process exit zero alone is NOT a successful run.
"""
import argparse
import csv
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[2]
ORIGINAL = REPO / "scripts/executed/06_cadence_harmonized_identification/parse_2025_selected.py"


def check_inputs(root: Path) -> int:
    required = [
        "cadence_work/selector/nba_canonical_snapshot_selector_v1/2025-26_game_snapshot_join_harmonized_canonical.csv",
        "cadence_core_full/nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py",
        "cadence_2025/audit_2025_26_upload.zip",
        "cadence_2025/audit_2025_26_targeted_upload.zip",
    ]
    missing = [r for r in required if not (root / r).is_file()]
    if missing:
        raise FileNotFoundError("Missing 2025 parser input(s): " + ", ".join(missing))
    selector = root / required[0]
    with selector.open(newline="", encoding="utf-8-sig") as stream:
        selected = list(csv.DictReader(stream))
    if not selected or any("snapshot_basename" not in r or
                           "published_timestamp_utc" not in r for r in selected):
        raise ValueError("Empty or wrong-schema 2025 selected snapshot map")
    snapshots = {(r["snapshot_basename"], r["published_timestamp_utc"]) for r in selected}
    basenames = {name for name, timestamp in snapshots}
    if "" in basenames or any(not timestamp for _, timestamp in snapshots):
        raise ValueError("Blank 2025 snapshot filename")
    found = set()
    for file in (root / required[2], root / required[3]):
        with zipfile.ZipFile(file) as z:
            found.update(Path(name).name for name in z.namelist()
                         if name.lower().endswith(".pdf"))
    missing_pdfs = basenames.difference(found)
    if missing_pdfs:
        raise FileNotFoundError(
            f"Missing {len(missing_pdfs)} selected PDF snapshots in both archives: "
            + ", ".join(sorted(missing_pdfs)[:10]))
    return snapshots


def verify_outputs(root: Path, expected_snapshots: set[tuple[str, str]]) -> None:
    folder = root / "cadence_work/season_parsed/2025-26"
    log_path = folder / "s1_parse_log_harmonized_selected.csv"
    rows_path = folder / "s1_snapshot_rows_harmonized_selected.csv"
    for path in (log_path, rows_path):
        if not path.is_file() or not path.stat().st_size:
            raise RuntimeError(f"2025 parser did not produce a nonempty file: {path}")
    with log_path.open(newline="", encoding="utf-8-sig") as stream:
        logs = list(csv.DictReader(stream))
    actual_snapshots = {(r.get("source_file", ""), r.get("snapshot_timestamp_utc", ""))
                        for r in logs}
    if len(logs) != len(expected_snapshots) or actual_snapshots != expected_snapshots:
        raise RuntimeError("2025 parse logs do not match the exact selected (PDF, timestamp) pairs")
    errors = [r for r in logs if r.get("status") != "ok"]
    if errors:
        raise RuntimeError(
            f"{len(errors)} 2025 PDF snapshots had parse errors/zero rows. "
            f"See {log_path}; examples: {errors[:3]}")
    with rows_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"source_file", "matchup_norm", "player_name", "current_status", "reason"}
        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError(f"2025 parser output missing columns: {required-set(reader.fieldnames or [])}")
        first = next(reader, None)
    if first is None:
        raise RuntimeError("2025 parsed rows CSV has no observations")
    print(f"Verified {len(logs)} selected report PDF+timestamp pairs parsed successfully; output: {rows_path}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historical-root", required=True, type=Path)
    p.add_argument("--check-only", action="store_true")
    a = p.parse_args()
    root = a.historical_root.resolve()
    snapshots = check_inputs(root)
    original = ORIGINAL.read_text()
    pattern = r"^ROOT=Path\('/mnt/data/nba_continue'\)$"
    if len(re.findall(pattern, original, flags=re.MULTILINE)) != 1:
        raise RuntimeError("Original parser ROOT line changed; inspect before replay")
    if a.check_only:
        print(f"PASS: {len(snapshots)} selected 2025 PDF+timestamp pairs available; parser not executed.")
        return
    modified = re.sub(pattern, lambda _: f"ROOT=Path({str(root)!r})", original,
                      count=1, flags=re.MULTILINE)
    with tempfile.TemporaryDirectory(prefix="nba_2025_cadence_") as tmp:
        executable = Path(tmp) / "parse_2025_selected.py"
        executable.write_text(modified)
        env = dict(os.environ, OPENBLAS_NUM_THREADS="2", OMP_NUM_THREADS="2")
        subprocess.run([sys.executable, str(executable)], cwd=root, env=env, check=True)
    verify_outputs(root, snapshots)


if __name__ == "__main__":
    main()
