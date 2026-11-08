#!/usr/bin/env python3
"""Verify original NBA source bytes against the historical source inventory.

This checks file coverage and integrity. It does NOT download sources, parse
PDFs, select checkpoints, or reconstruct the final analysis dataset.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys
import zipfile

REPO = Path(__file__).resolve().parents[2]
META = REPO / "provenance" / "historical_sources"


def rows(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def digest(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(block)
    return h.hexdigest()


def digest_file(path):
    with path.open("rb") as f:
        return digest(f)


def expected_pdfs(metadata: Path, scope: str):
    inventory = rows(metadata / "injury_report_inventory.csv.gz")
    saved = [r for r in inventory if r["pdf_present"].lower() == "true"]
    if len(inventory) != 37342 or len(saved) != 27755:
        raise ValueError("Frozen source inventory must have 37,342 URL checks and 27,755 PDFs")
    by_key = {(r["archive"], r["archive_member"]): r for r in saved}
    if len(by_key) != len(saved):
        raise ValueError("Duplicate source PDF archive/member keys")
    if scope == "all":
        return by_key
    selected = rows(metadata / "primary_sample_report_map.csv.gz")
    if len(selected) != 7230 or len({r["game_id"] for r in selected}) != 7230:
        raise ValueError("Selected report map is not 7,230 unique games")
    keys = {(r["archive"], r["archive_member"]) for r in selected}
    if len(keys) != 2054 or not keys.issubset(by_key):
        raise ValueError("Expected exactly 2,054 unique selected indexed PDFs")
    return {k: by_key[k] for k in keys}


def check_pdfs(folder: Path, metadata: Path, scope: str, check_zip_hash: bool):
    groups = defaultdict(list)
    for (archive, member), r in expected_pdfs(metadata, scope).items():
        groups[archive].append((member, r["computed_sha256"]))
    zip_hashes = {r["archive"]: r["archive_sha256"]
                  for r in rows(metadata / "injury_archive_summary.csv")}
    report = {"expected_pdfs": sum(map(len, groups.values())), "verified_pdfs": 0,
              "missing_archives": [], "missing_members": [], "unsafe_members": [],
              "zip_sha256_mismatches": [], "pdf_sha256_mismatches": []}
    for archive, members in sorted(groups.items()):
        path = folder / archive
        if not path.is_file():
            report["missing_archives"].append(archive)
            continue
        if check_zip_hash and digest_file(path) != zip_hashes.get(archive):
            report["zip_sha256_mismatches"].append(archive)
        with zipfile.ZipFile(path) as z:
            found = set(z.namelist())
            for name, expected in members:
                path_name = Path(name)
                if path_name.is_absolute() or ".." in path_name.parts:
                    report["unsafe_members"].append(f"{archive}:{name}")
                elif name not in found:
                    report["missing_members"].append(f"{archive}:{name}")
                else:
                    with z.open(name) as f:
                        actual = digest(f)
                    if actual == expected:
                        report["verified_pdfs"] += 1
                    else:
                        report["pdf_sha256_mismatches"].append(f"{archive}:{name}")
    return report


def check_boxscores(folder: Path, metadata: Path):
    inventory = rows(metadata / "boxscore_source_map.csv.gz")
    if len(inventory) != 7230 or len({r["nba_game_id"] for r in inventory}) != 7230:
        raise ValueError("Expected 7,230 unique official boxscore IDs")
    report = {"expected_json": len(inventory), "verified_json": 0,
              "missing_json": [], "invalid_json": [], "id_mismatches": []}
    for r in inventory:
        gid, season = r["nba_game_id"], r["season"]
        relative = Path("raw_json") / season / f"boxscore_{gid}.json"
        candidates = [folder / relative,
                      folder / "nba_boxscore_roster_frame_v1_output" / relative,
                      folder / season / f"boxscore_{gid}.json"]
        path = next((p for p in candidates if p.is_file()), None)
        if path is None:
            report["missing_json"].append(f"{season}/{gid}")
            continue
        try:
            with path.open(encoding="utf-8") as f:
                obj = json.load(f)
        except (OSError, ValueError) as exc:
            report["invalid_json"].append(f"{season}/{gid}: {exc}")
            continue
        game = obj.get("game", obj) if isinstance(obj, dict) else {}
        observed = str(game.get("gameId", "")) if isinstance(game, dict) else ""
        if observed != gid or not any(k in game for k in ("homeTeam", "awayTeam")):
            report["id_mismatches"].append(f"{season}/{gid}: observed={observed}")
        else:
            report["verified_json"] += 1
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, help="Location of seven audit_*_upload.zip archives")
    parser.add_argument("--boxscore-root", type=Path, help="Location of original raw_json tree")
    parser.add_argument("--scope", choices=["selected", "all"], default="selected")
    parser.add_argument("--verify-archive-sha256", action="store_true")
    parser.add_argument("--metadata-dir", type=Path, default=META)
    parser.add_argument("--output", type=Path,
                        default=REPO / "data_rebuild/output/raw_input_audit.json")
    args = parser.parse_args(argv)
    if args.archive_dir is None and args.boxscore_root is None:
        parser.error("Supply --archive-dir and/or --boxscore-root")
    result = {"scope": args.scope,
              "scope_note": "Unprovided families remain unverified. This is not raw-to-final reproduction."}
    if args.archive_dir:
        result["injury_pdfs"] = check_pdfs(args.archive_dir, args.metadata_dir,
                                          args.scope, args.verify_archive_sha256)
    if args.boxscore_root:
        result["boxscores"] = check_boxscores(args.boxscore_root, args.metadata_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2)[:4000])
    for item in ("injury_pdfs", "boxscores"):
        data = result.get(item, {})
        if not data:
            continue
        if any(isinstance(v, list) and v for v in data.values()):
            return 1
        if data.get("verified_pdfs", data.get("verified_json")) != data.get(
                "expected_pdfs", data.get("expected_json")):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
