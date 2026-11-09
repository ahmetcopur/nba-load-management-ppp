"""Safe ZIP ingestion tests for the private, corrected August at-risk panel."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

SCRIPT = (Path(__file__).resolve().parents[1]
          / "scripts/data_rebuild/run_august_corrected_zip_replays.py")
spec = importlib.util.spec_from_file_location("corrected_august_zip", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def source_bytes():
    columns = sorted(m.REQUIRED)
    record = {k: "1" for k in columns}
    record.update({
        "player_team_game_id": "g1|Toronto Raptors|123",
        "game_id": "g1", "season": "2021-22",
        "game_date_et": "2022-02-01", "team": "Toronto Raptors",
        "opponent": "Miami Heat",
    })
    return (",".join(columns) + "\n" + ",".join(record[k] for k in columns) + "\n").encode()


def zip_with(root, name, payload):
    path = root / "corrected.csv.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr(name, payload)
        archive.writestr("__MACOSX/._ignored", b"Finder metadata")
    return path


class CorrectedAugustZipTests(unittest.TestCase):
    def test_raw_csv_inside_zip_is_hashed_without_byte_reformatting(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = source_bytes()
            z = zip_with(root, m.SOURCE_NAME, raw)
            dest = root / "output" / (m.SOURCE_NAME + ".gz")
            info = m.extract_and_verify(
                z, dest, expected_sha=hashlib.sha256(raw).hexdigest(),
                expected_rows=1,
            )
            self.assertTrue(info["expected_source_identity_passed"])
            self.assertEqual(info["rows"], 1)
            self.assertEqual(info["decoded_bytes"], len(raw))
            self.assertEqual(gzip.open(dest, "rb").read(), raw)

    def test_nested_original_gzip_csv_in_zip_preserves_gzip_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = source_bytes()
            zipped = gzip.compress(raw, mtime=0)
            z = zip_with(root, "folder/" + m.SOURCE_NAME + ".gz", zipped)
            dest = root / "new" / "corrected.csv.gz"
            info = m.extract_and_verify(
                z, dest, expected_sha=hashlib.sha256(raw).hexdigest(),
                expected_rows=1,
            )
            self.assertEqual(dest.read_bytes(), zipped)
            self.assertEqual(info["decoded_sha256"], hashlib.sha256(raw).hexdigest())

    def test_different_freeze_sha_rejected_and_temporary_output_removed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            z = zip_with(root, m.SOURCE_NAME, source_bytes())
            dest = root / "other" / "bad.csv.gz"
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                m.extract_and_verify(z, dest, expected_sha="0" * 64, expected_rows=1)
            self.assertFalse(dest.exists())

    def test_more_than_one_matching_csv_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            z = root / "many.zip"
            with ZipFile(z, "w") as archive:
                archive.writestr(m.SOURCE_NAME, source_bytes())
                archive.writestr("duplicate/" + m.SOURCE_NAME, source_bytes())
            with self.assertRaisesRegex(ValueError, "exactly one"):
                m.extract_and_verify(z, root / "out.csv.gz",
                                     expected_sha=hashlib.sha256(source_bytes()).hexdigest(),
                                     expected_rows=1)

    def test_broken_row_count_or_required_header_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = source_bytes()
            z = zip_with(root, m.SOURCE_NAME, raw)
            dest = root / "incorrect.csv.gz"
            with self.assertRaisesRegex(ValueError, "row count"):
                m.extract_and_verify(
                    z, dest, expected_sha=hashlib.sha256(raw).hexdigest(),
                    expected_rows=2,
                )
            self.assertFalse(dest.exists())
            z = root / "missing_header.zip"
            payload = b"a,b\n1,2\n"
            with ZipFile(z, "w") as archive:
                archive.writestr(m.SOURCE_NAME, payload)
            with self.assertRaisesRegex(ValueError, "required panel columns"):
                m.extract_and_verify(
                    z, dest, expected_sha=hashlib.sha256(payload).hexdigest(),
                    expected_rows=1,
                )

    def test_malicious_zip_symlink_entry_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            info = ZipInfo(m.SOURCE_NAME)
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            archive = root / "symlink.zip"
            with ZipFile(archive, "w") as z:
                z.writestr(info, b"some/path")
            with self.assertRaisesRegex(ValueError, "symlink"):
                m.extract_and_verify(
                    archive, root / "output.csv.gz",
                    expected_sha=hashlib.sha256(b"some/path").hexdigest(),
                    expected_rows=1,
                )

    def test_fail_before_any_model_execution_if_source_identity_is_unknown(self):
        # The accepted real production hash remains pinned, never weakened by tests.
        self.assertEqual(
            m.EXPECTED_SHA,
            "5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3",
        )
        self.assertEqual(m.EXPECTED_ROWS, 180831)


if __name__ == "__main__":
    unittest.main()
