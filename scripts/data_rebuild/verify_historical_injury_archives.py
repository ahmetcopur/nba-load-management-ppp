#!/usr/bin/env python3
"""Verify original NBA injury-PDF ZIPs against the pinned source inventory.

This checks raw-source authenticity and per-PDF bytes. It does NOT parse injury
statuses, rebuild a panel, or reproduce the paper. No ZIP member is extracted.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

DEFAULT_ARCHIVES = (
    "audit_2020_21_upload.zip",
    "audit_2021_22_upload.zip",
    "audit_2022_23_upload.zip",
    "audit_2023_24_upload.zip",
)
HEX = set("0123456789abcdef")

# Actual git blob IDs at immutable source commit
# OEKundakcioglu/nba-ppp-star-availability@0bd713d97e8d519df5700ef473da34aba4495223.
# This pins the provenance files even if --metadata-dir points to a copied directory.
PINNED_SOURCE_BLOBS = {
    "injury_archive_summary.csv": "ca5188baf047e8154003b0daad1cb319af1ff3d4",
    "injury_report_inventory.csv.gz": "a3273b97035c63f9e34b68bac0dddf863588adc4",
}

# Independent pinned source expectations, not learned from supplied metadata files.
PINNED_ARCHIVES = {
    "audit_2020_21_upload.zip": (
        "e310c8149701fb16cda9b1a136fbfcf9af8af8de9ca2ed09080f364a493c272c", 617),
    "audit_2021_22_upload.zip": (
        "1e027ce6aa2a44292c3d27ba7bbfb24fcab61ded922b7ca6ba1c4211f9984339", 5567),
    "audit_2022_23_upload.zip": (
        "bea1adeac75384c75102b469a1daab43c76501caada2c3402b1e7cfa133732c0", 5541),
    "audit_2023_24_upload.zip": (
        "9cca3e58d2a8e6babce58e54dea5aeb05fa043cb034bc9065d4074e5e171daba", 5441),
}


def git_blob_sha1(path: Path) -> str:
    """Compute Git's SHA-1 for a file, including the 'blob SIZE\\0' prefix."""
    digest = hashlib.sha1()
    digest.update(f"blob {path.stat().st_size}\\0".encode("ascii"))
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_pinned_inventory(metadata_dir: Path) -> dict[str, str]:
    found = {}
    for basename, expected in PINNED_SOURCE_BLOBS.items():
        path = metadata_dir / basename
        if not path.is_file():
            raise FileNotFoundError(f"Pinned source inventory missing: {path}")
        observed = git_blob_sha1(path)
        if observed != expected:
            raise ValueError(
                f"Original provenance file changed: {basename}: "
                f"git blob SHA1 {observed} != pinned {expected}"
            )
        found[basename] = observed
    return found


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_member(archive: ZipFile, name: str) -> str:
    digest = hashlib.sha256()
    with archive.open(name) as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def valid_sha(value: str) -> bool:
    return len(value) == 64 and set(value.lower()) <= HEX


def read_source_inventory(metadata_dir: Path, selected: tuple[str, ...]):
    summary_path = metadata_dir / "injury_archive_summary.csv"
    inventory_path = metadata_dir / "injury_report_inventory.csv.gz"
    with summary_path.open(newline="", encoding="utf-8-sig") as stream:
        summaries = list(csv.DictReader(stream))
    with gzip.open(inventory_path, "rt", newline="", encoding="utf-8-sig") as stream:
        inventory = list(csv.DictReader(stream))

    if not summaries or not inventory:
        raise ValueError("Source inventory or archive summary is empty")
    required_archive = {"archive", "archive_sha256"}
    required_pdf = {"archive", "archive_member", "pdf_present",
                    "computed_sha256", "manifest_sha256", "hash_status"}
    if not required_archive <= set(summaries[0]):
        raise ValueError("Archive summary is missing required provenance columns")
    if not required_pdf <= set(inventory[0]):
        raise ValueError("PDF inventory is missing required provenance columns")

    archives = {}
    for row in summaries:
        name = row["archive"]
        if name not in selected:
            continue
        if name in archives:
            raise ValueError(f"Duplicate archive summary entry: {name}")
        digest = row["archive_sha256"].strip().lower()
        if not valid_sha(digest):
            raise ValueError(f"Invalid archive SHA-256: {name}")
        archives[name] = digest

    if set(archives) != set(selected):
        raise ValueError(f"Missing archive hashes: {sorted(set(selected) - set(archives))}")

    pdfs = {name: {} for name in selected}
    for row in inventory:
        archive = row["archive"]
        if archive not in pdfs or row["pdf_present"].strip().casefold() != "true":
            continue
        member = row["archive_member"]
        if member in pdfs[archive]:
            raise ValueError(f"Duplicate PDF inventory entry: {archive}::{member}")
        if not member.lower().endswith(".pdf"):
            raise ValueError(f"Non-PDF marked as present: {archive}::{member}")
        digest = row["computed_sha256"].strip().lower()
        manifest = row["manifest_sha256"].strip().lower()
        if (not valid_sha(digest) or manifest != digest
                or row["hash_status"].strip().casefold() != "match"):
            raise ValueError(f"Unverified PDF inventory digest: {archive}::{member}")
        pdfs[archive][member] = digest
    return archives, pdfs


def validate_archive(path: Path, expected_sha: str, expected_members: dict[str, str]):
    if not path.is_file():
        raise FileNotFoundError(f"Required original ZIP not found: {path}")
    archive_sha = sha256_file(path)
    if archive_sha != expected_sha:
        raise ValueError(f"Original ZIP SHA mismatch: {path.name}: {archive_sha} != {expected_sha}")
    if not expected_members:
        raise ValueError(f"No present PDF source rows in inventory for {path.name}")
    with ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate ZIP member paths: {path.name}")
        for info in infos:
            member = PurePosixPath(info.filename)
            # No extraction is performed, but reject unsafe archives anyway.
            if member.is_absolute() or ".." in member.parts or "\\" in info.filename:
                raise ValueError(f"Unsafe ZIP member: {path.name}::{info.filename}")
            if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError(f"Symlink ZIP member: {path.name}::{info.filename}")
        actual_pdfs = {name for name in names if name.lower().endswith(".pdf")}
        missing = sorted(set(expected_members) - actual_pdfs)
        if missing:
            raise ValueError(f"{path.name}: {len(missing)} indexed PDFs absent: {missing[:5]}")
        for member, expected in expected_members.items():
            observed = sha256_member(archive, member)
            if observed != expected:
                raise ValueError(f"{path.name}::{member}: PDF SHA mismatch {observed} != {expected}")
        return {
            "archive": path.name,
            "zip_size_bytes": path.stat().st_size,
            "zip_sha256": archive_sha,
            "indexed_pdf_members_verified": len(expected_members),
            "total_pdf_members": len(actual_pdfs),
            "unindexed_pdf_members": len(actual_pdfs - set(expected_members)),
            "pdf_content_hashes_match_inventory": True,
        }


def verify(archive_dir: Path, metadata_dir: Path,
           archives: tuple[str, ...] = DEFAULT_ARCHIVES,
           *, require_pinned_sources: bool = True):
    if not archives or len(set(archives)) != len(archives):
        raise ValueError("Archive selection must be nonempty and unique")
    if any(Path(name).name != name or not name.endswith(".zip") for name in archives):
        raise ValueError("Archive arguments must be simple .zip basenames")
    pinned_metadata = verify_pinned_inventory(metadata_dir) if require_pinned_sources else {}
    expected_archives, pdfs = read_source_inventory(metadata_dir, archives)
    if require_pinned_sources:
        for name in archives:
            if name not in PINNED_ARCHIVES:
                raise ValueError(f"Archive not in pinned 2020-24 research input set: {name}")
            fixed_sha, fixed_pdf_count = PINNED_ARCHIVES[name]
            if expected_archives[name] != fixed_sha:
                raise ValueError(f"Archive SHA differs from pinned source commit: {name}")
            if len(pdfs[name]) != fixed_pdf_count:
                raise ValueError(
                    f"Inventory PDF count for {name} = {len(pdfs[name])}, "
                    f"expected {fixed_pdf_count}"
                )
    records = [validate_archive(archive_dir / name, expected_archives[name], pdfs[name])
               for name in archives]
    return {
        "audit_scope": "Raw NBA injury-report PDF archive/member SHA-256 only",
        "source_metadata_dir": str(metadata_dir),
        "all_indexed_pdf_members_verified": True,
        "pinned_provenance_verified": require_pinned_sources,
        "pinned_provenance_git_blob_sha1": pinned_metadata,
        "pdfs_parsed": False,
        "panels_rebuilt": False,
        "archives": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--metadata-dir", type=Path, required=True)
    parser.add_argument("--archives", nargs="+", default=list(DEFAULT_ARCHIVES),
                        help="Exact original ZIP basenames; defaults to 2020-21 through 2023-24")
    parser.add_argument("--output", type=Path,
                        help="Optional JSON report; never written inside the raw ZIPs")
    args = parser.parse_args()
    report = verify(args.archive_dir, args.metadata_dir, tuple(args.archives))
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        if args.output.exists():
            raise FileExistsError(f"Refusing to overwrite existing audit: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
