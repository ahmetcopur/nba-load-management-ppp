#!/usr/bin/env python3
"""Substitute a verified PDF-derived original base in the private October replay."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

ORIGINAL_FULL_SHA = "5154317fc52157716cf22f7c5a535259e9f073b3391fd52d78a01faaf8d96d77"

def decoded_sha256(path):
    h = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def inject(source: Path, target: Path, report: Path, *, expected=ORIGINAL_FULL_SHA):
    if source == target or source.resolve() == target.resolve():
        raise ValueError("Source and target must be distinct")
    for path in (source, target):
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError(f"Missing or symlinked source: {path}")
    if report.exists() or report.is_symlink():
        raise FileExistsError(report)
    a, b = decoded_sha256(source), decoded_sha256(target)
    if a != expected or b != expected:
        raise ValueError(f"Original base SHA-256 differs: {a}, {b}, expected {expected}")
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".pdf_base_", delete=False) as f:
        temporary = Path(f.name)
    try:
        shutil.copyfile(source, temporary)
        if decoded_sha256(temporary) != expected:
            raise ValueError("PDF source changed while copying")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    result = {"pdf_derived_original_base_directly_fed_to_corrected_october": True,
              "source_decoded_sha256": a, "restored_baseline_decoded_sha256": b,
              "substituted_input_decoded_sha256": decoded_sha256(target),
              "october_season_report_rows_still_inherited": True}
    report.write_text(json.dumps(result, indent=2) + "\n")
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "target", "report"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(inject(a.source, a.target, a.report), indent=2))
