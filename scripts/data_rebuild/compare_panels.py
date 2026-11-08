#!/usr/bin/env python3
"""Strict, keyed comparison of a rebuilt panel against the published panel."""
import argparse
import json
from pathlib import Path
import pandas as pd

def compare(reference, candidate, key="player_team_game_id", max_examples=10):
    a = pd.read_csv(reference, dtype=str, keep_default_na=False)
    b = pd.read_csv(candidate, dtype=str, keep_default_na=False)
    report = {"reference_rows": len(a), "candidate_rows": len(b),
              "missing_columns": sorted(set(a) - set(b)),
              "extra_columns": sorted(set(b) - set(a))}
    if key not in a.columns or key not in b.columns:
        raise ValueError(f"Required key missing: {key}")
    for label, frame in (("reference", a), ("candidate", b)):
        if frame[key].duplicated().any() or frame[key].eq("").any():
            raise ValueError(f"{label} has duplicated or empty {key}")
    a, b = a.set_index(key), b.set_index(key)
    report["missing_keys"] = len(a.index.difference(b.index))
    report["extra_keys"] = len(b.index.difference(a.index))
    common = a.index.intersection(b.index)
    report["common_keys"] = len(common)
    counts, examples = {}, []
    for col in sorted(set(a) & set(b)):
        x, y = a.loc[common, col], b.loc[common, col]
        mismatch = x.ne(y)
        n = int(mismatch.sum())
        if n:
            counts[col] = n
            for k in x.index[mismatch][:max(0, max_examples - len(examples))]:
                examples.append({"key": str(k), "column": col,
                                 "reference": str(x.loc[k]), "candidate": str(y.loc[k])})
    report["mismatched_cell_counts"] = counts
    report["examples"] = examples
    report["exact_match"] = not any((report["missing_columns"], report["extra_columns"],
                                      report["missing_keys"], report["extra_keys"], counts))
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--key", default="player_team_game_id")
    p.add_argument("--output", type=Path, default=Path("data_rebuild/output/panel_comparison.json"))
    a = p.parse_args()
    result = compare(a.reference, a.candidate, a.key)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2)[:5000])
    raise SystemExit(0 if result["exact_match"] else 1)

if __name__ == "__main__":
    main()
