#!/usr/bin/env python3
"""Reparse archived cadence-selected 2025-26 NBA PDFs with the historical parser.

Before executing the untouched parser logic, verify every selected PDF basename
exists and no conflicting PDFs share a selected basename across archives.
This does not correct the 21 known PDF-header/manifest timestamp exceptions.
"""
from collections import defaultdict
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[2]
ORIGINAL = REPO / "scripts/executed/06_cadence_harmonized_identification/parse_2025_selected.py"
SELECTOR = "cadence_work/selector/nba_canonical_snapshot_selector_v1/2025-26_game_snapshot_join_harmonized_canonical.csv"
PARSER = "cadence_core_full/nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py"
RAW_ZIPS = ("cadence_2025/audit_2025_26_upload.zip",
            "cadence_2025/audit_2025_26_targeted_upload.zip")


def audit_selected(root: Path, metadata_dir: Path | None = None):
    with (root / SELECTOR).open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if "snapshot_basename" not in (reader.fieldnames or ()):
            raise ValueError("2025 selector is missing snapshot_basename")
        rows = list(reader)
    if len(rows) != 1230:
        raise ValueError(f"Expected 1,230 selected 2025-26 games, got {len(rows)}")
    selected = {r["snapshot_basename"] for r in rows}
    if not selected or any(not name.endswith(".pdf") for name in selected):
        raise ValueError("2025 selector contains missing/invalid PDF basenames")
    found = defaultdict(list)
    for source in RAW_ZIPS:
        with zipfile.ZipFile(root / source) as z:
            for member in z.namelist():
                basename = Path(member).name
                if basename not in selected or not member.lower().endswith(".pdf"):
                    continue
                h = hashlib.sha256()
                with z.open(member) as stream:
                    for data in iter(lambda: stream.read(1024 * 1024), b""):
                        h.update(data)
                found[basename].append({"archive": source, "member": member,
                                        "sha256": h.hexdigest()})
    missing = sorted(selected - found.keys())
    conflicting = {
        basename: entries for basename, entries in found.items()
        if len({v["sha256"] for v in entries}) != 1
    }
    if missing or conflicting:
        raise ValueError(f"2025 report archives incomplete or ambiguous: "
                         f"{len(missing)} missing; {len(conflicting)} conflicting "
                         f"basenames. Missing sample: {missing[:10]}; "
                         f"conflict sample: {list(conflicting)[:10]}")
    inventory_checked = False
    if metadata_dir is not None:
        # IMPORTANT: the primary_sample_report_map.csv.gz records latest-pre-tip
        # *canonical* selections, which may differ from the harmonized common-
        # checkpoint selector used above. Never require the two sets to match.
        inventory_path = metadata_dir / "injury_report_inventory.csv.gz"
        inventory = {}
        expected_by_basename = defaultdict(set)
        source_archives = {Path(x).name for x in RAW_ZIPS}
        with gzip.open(inventory_path, "rt", encoding="utf-8-sig", newline="") as stream:
            for record in csv.DictReader(stream):
                if record["archive"] not in source_archives:
                    continue
                if record["pdf_present"].casefold() != "true":
                    continue
                member = record["archive_member"]
                basename = Path(member).name
                if basename not in selected:
                    continue
                key = (record["archive"], member)
                digest = record["computed_sha256"]
                if (record.get("hash_status") != "match" or
                        record.get("manifest_sha256") != digest):
                    raise ValueError(f"Archived PDF lacks manifest hash verification: {key}")
                if not digest or len(digest) != 64:
                    raise ValueError(f"Selected PDF has missing/invalid archived digest: {key}")
                if key in inventory and inventory[key] != digest:
                    raise ValueError(f"Conflicting archived inventory digests: {key}")
                inventory[key] = digest
                expected_by_basename[basename].add(digest)
        for name in sorted(selected):
            if name not in expected_by_basename:
                raise ValueError(f"Harmonized selected PDF missing from FULL injury inventory: {name}")
            if len(expected_by_basename[name]) != 1:
                raise ValueError(f"Conflicting archived digests for selected PDF basename: {name}")
            expected = next(iter(expected_by_basename[name]))
            for candidate in found[name]:
                key = (Path(candidate["archive"]).name, candidate["member"])
                if inventory.get(key) != candidate["sha256"] or candidate["sha256"] != expected:
                    raise ValueError(f"PDF digest or member mismatch against FULL inventory: {key}")
        inventory_checked = True
    return {
        "source_inventory_sha256_verified": inventory_checked,
        "selected_games": len(rows),
        "distinct_selected_pdfs": len(selected),
        "distinct_pdf_basenames_verified": len(found),
        "duplicate_identical_pdf_basenames": sum(len(v) > 1 for v in found.values()),
        "sha256_by_basename": {key: items[0]["sha256"]
                              for key, items in sorted(found.items())},
        "warning": ("These are filename/hash checks, not an audit of the PDF-header "
                    "clock or the 21 known December 2025 timestamp exceptions."),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", required=True, type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--metadata-dir", type=Path,
                        help="Optional shared-repo provenance/historical_sources FULL PDF inventory for SHA-256s")
    args = parser.parse_args()
    root = args.historical_root.resolve()
    required = [SELECTOR, PARSER, *RAW_ZIPS]
    missing = [str(root / r) for r in required if not (root / r).is_file()]
    if missing:
        raise SystemExit("Missing parser prerequisites:\n" + "\n".join(missing))
    original = ORIGINAL.read_text()
    pattern = r"^ROOT=Path\('/mnt/data/nba_continue'\)$"
    if len(re.findall(pattern, original, flags=re.MULTILINE)) != 1:
        raise RuntimeError("Original 2025 parser ROOT line changed; review before replay")
    audit = audit_selected(root, args.metadata_dir)
    if args.check_only:
        print(json.dumps({k: v for k, v in audit.items()
                          if k != "sha256_by_basename"}, indent=2))
        return
    modified = re.sub(pattern, lambda _: f"ROOT=Path({str(root)!r})",
                      original, count=1, flags=re.MULTILINE)
    with tempfile.TemporaryDirectory(prefix="nba_2025_cadence_") as tmp:
        executable = Path(tmp) / "parse_2025_selected.py"
        executable.write_text(modified)
        env = dict(os.environ, OPENBLAS_NUM_THREADS="2", OMP_NUM_THREADS="2")
        subprocess.run([sys.executable, str(executable)], cwd=root, env=env, check=True)
    result = root / "cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv"
    if not result.is_file() or result.stat().st_size == 0:
        raise RuntimeError("Historical parser did not produce selected 2025-26 rows")
    log = root / "cadence_work/season_parsed/2025-26/selected_pdf_sha256_audit.json"
    log.write_text(json.dumps(audit, indent=2) + "\n")
    print("2025-26 parsed rows generated:", result)
    print("Selected PDF hash audit:", log)


if __name__ == "__main__":
    main()
