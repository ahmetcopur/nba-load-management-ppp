#!/usr/bin/env python3
"""Read-only 2020–21 injury-PDF parser reason-text drift measurement.

Compares the complete archived parsed CSV against a candidate source reparse.
Never repairs or transfers reason strings. Differences in any column other than
'reason' are blocking identity errors. Outputs only sanitized aggregate counts.
A non-exact output exits nonzero, including the known 93-reason diagnostic.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import json
from pathlib import Path


def read_rows(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames
        if not columns or len(columns) != len(set(columns)):
            raise ValueError(f"Missing/duplicate CSV headers in {path}")
        if not {"reason", "source_file"} <= set(columns):
            raise ValueError(f"Missing reason/source_file provenance in {path}")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError(f"Malformed CSV contains extra unnamed fields: {path}")
    return columns, rows


def summarize(reference: Path, candidate: Path):
    ref_columns, ref_rows = read_rows(reference)
    cand_columns, cand_rows = read_rows(candidate)
    if ref_columns != cand_columns:
        raise ValueError("Column names/order changed between reference and candidate")
    key_cols = [column for column in ref_columns if column != "reason"]

    def grouped(rows):
        groups = defaultdict(Counter)
        for row in rows:
            key = tuple(row[column] for column in key_cols)
            groups[key][row["reason"]] += 1
        return groups

    left = grouped(ref_rows)
    right = grouped(cand_rows)
    count_left = Counter({k: sum(c.values()) for k, c in left.items()})
    count_right = Counter({k: sum(c.values()) for k, c in right.items()})
    if count_left != count_right:
        missing = sum((count_left - count_right).values())
        extra = sum((count_right - count_left).values())
        raise ValueError(
            f"Non-reason field identities drifted: missing={missing}, extra={extra}; "
            "do not interpret as a reason-only formatting difference"
        )

    changed = 0
    pdfs = set()
    source_idx = key_cols.index("source_file")
    for key, ref_counts in left.items():
        candidate_counts = right[key]
        n = sum((ref_counts - candidate_counts).values())
        if n:
            changed += n
            pdfs.add(Path(key[source_idx]).name)

    return {
        "scope": "2020–21 archived parsed CSV versus private PDF reparse",
        "reason_diff_only": True,
        "reference_rows": len(ref_rows),
        "candidate_rows": len(cand_rows),
        "non_reason_key_multisets_identical": True,
        "reason_records_differing": changed,
        "source_pdfs_with_reason_drift": len(pdfs),
        "exact_complete_record_multiset_match": changed == 0,
        "accepted_as_exact_replay": changed == 0,
        "reason_values_or_player_identifiers_exposed": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = summarize(a.reference, a.candidate)
    if a.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing diagnostic: {a.output}")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(result, indent=2) + "\n"
    a.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not result["accepted_as_exact_replay"]:
        raise SystemExit(
            f"NOT AN EXACT HISTORICAL REPLAY: {result['reason_records_differing']} "
            f"reason-field mismatches across {result['source_pdfs_with_reason_drift']} PDFs"
        )


if __name__ == "__main__":
    main()
