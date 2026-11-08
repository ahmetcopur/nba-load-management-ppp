#!/usr/bin/env python3
"""Compare historical Stage-6 cadence model outputs with their archived results.

The Stage-6 coefficients are *not* automatically the October 25 manuscript
estimates. Report numerical deviations; do not overwrite historical results.
"""
import argparse
import csv
import io
import json
import math
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "packages/06_cadence_harmonized_identification.zip"
KEY = ("definition", "controls")
EXACT = ("n",)
NUMERIC = ("estimate_pp", "se_pp", "low_pp", "high_pp", "p")


def read_csv(text):
    return list(csv.DictReader(io.StringIO(text)))


def archived_rows(archive: Path):
    with zipfile.ZipFile(archive) as z:
        members = [m for m in z.namelist()
                   if Path(m).name == "cadence_harmonized_model_results.csv"]
        if len(members) != 1:
            raise ValueError(f"Expected one historical Stage-6 model CSV, found {members}")
        return read_csv(z.read(members[0]).decode("utf-8-sig"))


def candidate_rows(path: Path):
    return read_csv(path.read_text(encoding="utf-8-sig"))


def index(rows):
    found = {}
    for r in rows:
        if any(field not in r for field in (*KEY, *EXACT, *NUMERIC)):
            raise ValueError("Missing mandatory Stage-6 model result columns")
        key = tuple(r[k] for k in KEY)
        if key in found:
            raise ValueError("Duplicate model specification: " + str(key))
        found[key] = r
    return found


def compare(reference, candidate, pp_tol=0.001, p_tol=0.001):
    a, b = index(reference), index(candidate)
    errors = []
    if set(a) != set(b):
        errors.append({"reason": "different model specifications",
                       "missing": sorted(set(a) - set(b)),
                       "extra": sorted(set(b) - set(a))})
    for key in sorted(set(a) & set(b)):
        x, y = a[key], b[key]
        for field in EXACT:
            if x[field] != y[field]:
                errors.append({"specification": key, "field": field,
                               "reference": x[field], "rebuilt": y[field]})
        for field in NUMERIC:
            old, new = float(x[field]), float(y[field])
            allowed = p_tol if field == "p" else pp_tol
            if not (math.isfinite(old) and math.isfinite(new)
                    and abs(old - new) <= allowed):
                errors.append({"specification": key, "field": field,
                               "reference": old, "rebuilt": new,
                               "abs_difference": abs(old - new), "tolerance": allowed})
    return {"matched": len(errors) == 0, "model_specifications": len(a),
            "error_count": len(errors), "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-zip", type=Path, default=ARCHIVE)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pp-tolerance", type=float, default=0.001)
    parser.add_argument("--p-tolerance", type=float, default=0.001)
    args = parser.parse_args()
    result = compare(archived_rows(args.reference_zip), candidate_rows(args.candidate),
                     args.pp_tolerance, args.p_tolerance)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2)[:6000])
    raise SystemExit(0 if result["matched"] else 1)


if __name__ == "__main__":
    main()
