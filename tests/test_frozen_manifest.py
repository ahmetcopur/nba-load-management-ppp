"""Every file listed in MANIFEST_SHA256.csv must still match the August 12 freeze."""
from __future__ import annotations

import csv
import hashlib
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "MANIFEST_SHA256.csv"

# README.md is the repository's living front page. It first diverged from the
# frozen manifest on main in commit 29a8103 (2026-08-13), before the November
# audit branch existed. Its frozen bytes remain retrievable from 0693cf4.
# No other exception is allowed; adding one must be a deliberate, reviewed change.
LIVING_DOCUMENTS = {"README.md"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_rows():
    with MANIFEST.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class FrozenManifestTests(unittest.TestCase):
    def test_manifest_shape(self):
        rows = manifest_rows()
        self.assertEqual(len(rows), 33)
        paths = [row["relative_path"] for row in rows]
        self.assertEqual(len(paths), len(set(paths)), "duplicate manifest entries")
        self.assertTrue(LIVING_DOCUMENTS <= set(paths))

    def test_every_frozen_file_matches_size_and_sha256(self):
        problems = []
        for row in manifest_rows():
            relative = row["relative_path"]
            if relative in LIVING_DOCUMENTS:
                continue
            path = REPO / relative
            if path.is_symlink() or not path.is_file():
                problems.append(f"{relative}: missing or not a regular file")
                continue
            if path.stat().st_size != int(row["size_bytes"]):
                problems.append(f"{relative}: size {path.stat().st_size} != {row['size_bytes']}")
            elif sha256(path) != row["sha256"]:
                problems.append(f"{relative}: SHA-256 differs from the freeze")
        self.assertEqual(problems, [], "Frozen files changed; add an addendum instead of editing them")


if __name__ == "__main__":
    unittest.main()
