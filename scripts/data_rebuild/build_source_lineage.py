#!/usr/bin/env python3
"""Join the frozen selected injury-report and official boxscore source maps.

This produces source lineage, NOT a newly rebuilt player-game panel.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "provenance/historical_sources"

def read(path):
    op = gzip.open if path.suffix == ".gz" else open
    with op(path, "rt", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=SOURCE)
    p.add_argument("--output", type=Path, default=ROOT / "data_rebuild/output/game_source_lineage.csv")
    a = p.parse_args()
    reports = read(a.source / "primary_sample_report_map.csv.gz")
    scores = read(a.source / "boxscore_source_map.csv.gz")
    if len(reports) != 7230 or len(scores) != 7230:
        raise ValueError("Expected 7,230 selected game records in each source")
    if len({x["game_id"] for x in reports}) != 7230:
        raise ValueError("Duplicate game_id in report map")
    by_game = {}
    for x in scores:
        k = x["game_id"]
        if k in by_game:
            raise ValueError(f"Duplicate game_id in boxscore map: {k}")
        by_game[k] = x
    if set(by_game) != {x["game_id"] for x in reports}:
        raise ValueError("Selected-report and boxscore game sets differ")
    result = []
    for r in reports:
        b = by_game[r["game_id"]]
        result.append({
            "season": r["season"],
            "game_id": r["game_id"],
            "source_match_number": r.get("source_match_number", ""),
            "nba_game_id": b["nba_game_id"],
            "selected_pdf_archive": r["archive"],
            "selected_pdf_member": r["archive_member"],
            "selected_pdf_sha256": r["computed_sha256"],
            "selected_pdf_url": r.get("source_url", ""),
            "selected_manifest_timestamp_utc": r.get("published_timestamp_utc", ""),
            "selected_pdf_header_timestamp_utc": r.get("pdf_header_timestamp_utc", ""),
        })
    result.sort(key=lambda d: (d["season"], d["game_id"]))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(result[0]))
        w.writeheader()
        w.writerows(result)
    print(json.dumps({"rows": len(result), "path": str(a.output),
                      "sha256": hashlib.sha256(a.output.read_bytes()).hexdigest()}, indent=2))

if __name__ == "__main__":
    main()
