#!/usr/bin/env python3
"""Validate a user-supplied corrected August at-risk CSV ZIP, then run two
exact-original-script August sensitivities.

Accepts a ZIP containing ONE player_game_panel_model_at_risk_analysis_ready.csv
(or .csv.gz). Mac Finder metadata is ignored. Rejects ZIP bombs, ambiguity,
unexpected corrected content hashes, duplicates, wrong row counts and invalid
input headers. Does not publish/share the ZIP or its contents.

The source-corrected private August model-risk CSV's *decompressed* SHA-256 is
frozen at the previously independently audited version. Neither runner executes
unless that exact scientific input is confirmed.

The original frozen public panel and TV source are staged read-only by the
downstream runners. The ZIP is never pushed to the GitHub repository.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from zipfile import ZipFile

EXPECTED_SHA = "5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3"
EXPECTED_ROWS = 180831
SOURCE_NAME = "player_game_panel_model_at_risk_analysis_ready.csv"
MAX_UNCOMPRESSED = 1024 * 1024 * 1024
CHUNK = 1024 * 1024
# The model risk subset has no at_risk_for_new_onset column: every row is at risk.
REQUIRED = {
    "player_team_game_id", "season", "game_date_et", "team", "opponent",
    "game_id", "is_home", "star_PPP_it", "postPPP",
    "announced_tv_primary", "absence_onset",
}
PIPELINES = (
    ("heterogeneity", "run_august_heterogeneity_from_release.py"),
    ("pretrend-placebo", "run_august_prior_event_placebos_from_release.py"),
)


def sha_of_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(CHUNK), b""):
            digest.update(part)
    return digest.hexdigest()


def pick_source(archive: ZipFile):
    acceptable = {SOURCE_NAME, SOURCE_NAME + ".gz"}
    matches = []
    for member in archive.infolist():
        if member.is_dir():
            continue
        filename = member.filename.replace("\\", "/")
        if filename.startswith("__MACOSX/") or Path(filename).name.startswith("._"):
            continue
        if Path(filename).name not in acceptable:
            continue
        if stat.S_IFMT(member.external_attr >> 16) == stat.S_IFLNK:
            raise ValueError("ZIP payload is a symlink; expected an actual CSV file")
        if member.file_size > MAX_UNCOMPRESSED:
            raise ValueError("ZIP entry exceeds the permitted uncompressed input limit")
        matches.append(member)
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one {SOURCE_NAME}[.gz] in the ZIP; "
            f"found {len(matches)}"
        )
    return matches[0]


def extract_and_verify(source_zip: Path, destination: Path,
                       expected_sha: str = EXPECTED_SHA,
                       expected_rows: int = EXPECTED_ROWS):
    if destination.exists():
        raise FileExistsError("Use a fresh corrected input file destination")
    destination.parent.mkdir(parents=True, exist_ok=True)
    info = {}
    try:
        with ZipFile(source_zip) as archive:
            invalid = archive.testzip()
            if invalid is not None:
                raise ValueError(f"ZIP CRC verification failed: {invalid}")
            member = pick_source(archive)
            info["zip_payload_member"] = member.filename
            info["zip_payload_bytes"] = member.file_size
            count_bytes = 0
            digest = hashlib.sha256()
            with archive.open(member) as compressed:
                if member.filename.endswith(".csv.gz"):
                    # Preserve original gzip data and verify its decoded bytes.
                    with destination.open("wb") as saved:
                        for block in iter(lambda: compressed.read(CHUNK), b""):
                            saved.write(block)
                            count_bytes += len(block)
                            if count_bytes > MAX_UNCOMPRESSED:
                                raise ValueError("ZIP payload exceeded size limit")
                    with gzip.open(destination, "rb") as decoded:
                        uncompressed_bytes = 0
                        for block in iter(lambda: decoded.read(CHUNK), b""):
                            uncompressed_bytes += len(block)
                            if uncompressed_bytes > MAX_UNCOMPRESSED:
                                raise ValueError("Decoded gzip input exceeded size limit")
                            digest.update(block)
                else:
                    # Deterministically gzip a raw CSV without changing its content.
                    with destination.open("wb") as out, gzip.GzipFile(
                        fileobj=out, mode="wb", filename="", mtime=0
                    ) as zipped:
                        uncompressed_bytes = 0
                        for block in iter(lambda: compressed.read(CHUNK), b""):
                            uncompressed_bytes += len(block)
                            if uncompressed_bytes > MAX_UNCOMPRESSED:
                                raise ValueError("Decoded CSV input exceeded size limit")
                            digest.update(block)
                            zipped.write(block)
            actual = digest.hexdigest()
            info["decoded_sha256"] = actual
            info["decoded_bytes"] = uncompressed_bytes
            if actual != expected_sha:
                raise ValueError(
                    f"Corrected August panel SHA mismatch: {actual}, "
                    f"expected {expected_sha}. This archive may be a different "
                    "freeze; no models were run."
                )

        with gzip.open(destination, "rt", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)
            missing = REQUIRED.difference(header)
            if missing:
                raise ValueError(f"Missing required panel columns: {sorted(missing)}")
            key = header.index("player_team_game_id")
            seen = set()
            rows = 0
            for record in reader:
                rows += 1
                if record[key] in seen:
                    raise ValueError(f"Duplicate player_team_game_id: {record[key]}")
                seen.add(record[key])
        if rows != expected_rows:
            raise ValueError(f"Unexpected August at-risk row count: {rows} != {expected_rows}")
        info.update({
            "rows": rows,
            "unique_player_team_game_ids": len(seen),
            "columns": len(header),
            "expected_source_identity_passed": True,
            "compressed_output_sha256": sha_of_file(destination),
        })
        return info
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


def run_analyses(panel: Path, shared_repo: Path, root: Path, python: str):
    if not shared_repo.is_dir():
        raise FileNotFoundError(f"Missing pinned source checkout: {shared_repo}")
    tools = Path(__file__).resolve().parent
    results = {}
    for label, executable in PIPELINES:
        work = root / label
        args = [python, str(tools / executable),
                "--shared-repo", str(shared_repo),
                "--corrected-panel", str(panel),
                "--work", str(work)]
        subprocess.run(args, cwd=tools.parent.parent, check=True, timeout=3600)
        report_name = ("august_heterogeneity_replay.json" if label == "heterogeneity"
                       else "august_prior_event_placebo_replay.json")
        report = work / report_name
        if not report.exists():
            raise RuntimeError(f"{label}: corrected original-script output missing")
        summary = json.loads(report.read_text())
        required_flag = ("corrected_predeclared_models" if label == "heterogeneity"
                         else "corrected_tables")
        if required_flag not in summary:
            raise RuntimeError(f"{label}: corrected results not present in report")
        results[label] = {
            "report": str(report),
            "source_reproduction_passed": True,
            "corrected_result": required_flag,
        }
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-zip", type=Path, required=True)
    parser.add_argument("--shared-repo", type=Path,
                        help="Clean checkout of immutable original NBA research commit")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true",
                        help="Verify contents and hash only; do not run models")
    args = parser.parse_args()
    inp = args.input_zip.resolve()
    out = args.output_root.resolve()
    shared = args.shared_repo.resolve() if args.shared_repo else None
    if not inp.is_file():
        raise FileNotFoundError(inp)
    if out.exists():
        raise FileExistsError("Select a new output root to preserve historical data")
    if not args.verify_only and shared is None:
        parser.error("--shared-repo is required for model execution")
    if shared and (shared == out or out in shared.parents
                   or shared in out.parents):
        raise ValueError("Output directory must be outside original research repo")
    if out == inp.parent or out in inp.parents:
        raise ValueError("Output directory must not contain the original archive")
    out.mkdir(parents=True)
    panel = out / "input" / (SOURCE_NAME + ".gz")
    outcome = {
        "source_zip": str(inp),
        "source_zip_sha256": sha_of_file(inp),
        "scientific_input": extract_and_verify(inp, panel),
        "private_zip_never_uploaded": True,
    }
    if not args.verify_only:
        outcome["analyses"] = run_analyses(panel, shared, out, sys.executable)
    else:
        outcome["analysis_executed"] = False
    path = out / "august_corrected_zip_replay_summary.json"
    path.write_text(json.dumps(outcome, indent=2) + "\n")
    print(json.dumps(outcome, indent=2))


if __name__ == "__main__":
    main()
