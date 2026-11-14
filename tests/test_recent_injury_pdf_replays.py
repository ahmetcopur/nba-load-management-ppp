"""Synthetic strict-input tests for reproducible recent original PDF parser replays."""
import csv
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from scripts.data_rebuild.replay_recent_historical_injury_pdfs import (
    ROW_FIELDS, prep_source_files, reference_groups, row_key, read_member_csv,
)


class RecentPdfReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.mkdir(exist_ok=True)
        self.archive = self.root / "original.zip"
        self.archive2 = self.root / "later.zip"
        self.dest = self.root / "scratch"
        self.dest.mkdir()
        self.pdf = "Injury-Report_2026-04-12_08_15PM.pdf"
        self.pdf2 = "Injury-Report_2025-10-21_06PM.pdf"

    def test_full_row_key_preserves_reason_differences(self):
        values = {k: "value" for k in ROW_FIELDS}
        values["reason"] = "knee"
        a = row_key(values)
        values["reason"] = "ankle"
        self.assertNotEqual(a, row_key(values))
        self.assertEqual(len(a), len(ROW_FIELDS))

    def test_row_key_normalizes_missing_none_only(self):
        base = {k: None for k in ROW_FIELDS}
        normalized = row_key(base)
        self.assertEqual(normalized, ("",) * len(ROW_FIELDS))

    def test_reference_groups_preserve_duplicate_record_multiplicity(self):
        values = {k: "" for k in ROW_FIELDS}
        values["snapshot_basename"] = self.pdf
        result = reference_groups([values, values], "snapshot_basename")
        self.assertEqual(result[self.pdf][row_key(values)], 2)

    def test_reference_groups_reject_missing_reason_column(self):
        values = {k: "" for k in ROW_FIELDS if k != "reason"}
        values["snapshot_basename"] = self.pdf
        with self.assertRaisesRegex(ValueError, "missing complete original parser fields"):
            reference_groups([values], "snapshot_basename")

    def write_zip(self, name, contents):
        with ZipFile(self.root / name, "w") as z:
            for key, val in contents.items():
                z.writestr(key, val)

    def test_exact_expected_source_pdf_is_staged_without_extraction_paths(self):
        self.write_zip("original.zip", {"audit/pdf/" + self.pdf: b"%PDF-test"})
        files = prep_source_files(self.root, ("original.zip",), {self.pdf}, self.dest)
        self.assertEqual(set(files), {self.pdf})
        self.assertEqual((self.dest / self.pdf).read_bytes(), b"%PDF-test")

    def test_missing_original_source_pdf_rejected(self):
        self.write_zip("original.zip", {"audit/pdf/" + self.pdf: b"%PDF-test"})
        with self.assertRaisesRegex(ValueError, "Missing original source PDFs"):
            prep_source_files(self.root, ("original.zip",), {self.pdf2}, self.dest)

    def test_duplicate_basename_across_archives_rejected(self):
        self.write_zip("original.zip", {"first/" + self.pdf: b"%PDF-first"})
        self.write_zip("later.zip", {"second/" + self.pdf: b"%PDF-second"})
        with self.assertRaisesRegex(ValueError, "Ambiguous duplicate PDF basename"):
            prep_source_files(self.root, ("original.zip", "later.zip"),
                              {self.pdf}, self.dest)

    def test_unexpected_source_pdf_filename_rejected(self):
        self.write_zip("original.zip", {"audit/pdf/evil.pdf": b"%PDF-bad"})
        with self.assertRaisesRegex(ValueError, "Unexpected PDF filename"):
            prep_source_files(self.root, ("original.zip",), {"evil.pdf"}, self.dest)

    def test_read_member_csv_rejects_duplicate_headers(self):
        self.write_zip("original.zip", {"rows.csv": "reason,reason\nabc,xyz\n"})
        with ZipFile(self.archive) as z:
            with self.assertRaisesRegex(ValueError, "Missing/duplicate CSV fields"):
                read_member_csv(z, "rows.csv")

    def test_read_member_csv_rejects_malformed_extra_columns(self):
        self.write_zip("original.zip", {"rows.csv": "reason\nabc,xyz\n"})
        with ZipFile(self.archive) as z:
            with self.assertRaisesRegex(ValueError, "Malformed CSV data"):
                read_member_csv(z, "rows.csv")


if __name__ == "__main__":
    unittest.main()
