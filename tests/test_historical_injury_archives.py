"""Synthetic fail-closed checks for immutable NBA injury-PDF archive verification."""
import csv
import gzip
import hashlib
from unittest.mock import patch
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.data_rebuild.verify_historical_injury_archives import (verify, git_blob_sha1, PINNED_SOURCE_BLOBS, PINNED_ARCHIVES)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class HistoricalPdfArchiveVerifierTests(unittest.TestCase):
    NAME = "audit_2020_21_upload.zip"
    MEMBER = "audit_2020_21/reports/2021-01-02_03PM.pdf"
    BODY = b"%PDF-1.4\nsynthetic test; not an official NBA PDF\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / "originals"
        self.meta = self.root / "metadata"
        self.src.mkdir()
        self.meta.mkdir()
        self.write_source()

    def write_source(self, files=None):
        if files is None:
            files = {self.MEMBER: self.BODY}
        with ZipFile(self.src / self.NAME, "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)

    def write_meta(self, member=None, content_sha=None, hash_status="match"):
        member = member or self.MEMBER
        content_sha = content_sha or sha(self.BODY)
        with (self.meta / "injury_archive_summary.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["archive", "archive_sha256"])
            writer.writeheader()
            writer.writerow({"archive": self.NAME,
                             "archive_sha256": sha((self.src / self.NAME).read_bytes())})
        with gzip.open(self.meta / "injury_report_inventory.csv.gz", "wt",
                       newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "archive", "archive_member", "pdf_present", "computed_sha256",
                "manifest_sha256", "hash_status"])
            writer.writeheader()
            writer.writerow({"archive": self.NAME, "archive_member": member,
                             "pdf_present": "True", "computed_sha256": content_sha,
                             "manifest_sha256": content_sha,
                             "hash_status": hash_status})

    def call(self):
        return verify(self.src, self.meta, (self.NAME,), require_pinned_sources=False)

    def test_exact_archive_and_pdf_hashes_pass(self):
        self.write_meta()
        result = self.call()
        self.assertTrue(result["all_indexed_pdf_members_verified"])
        self.assertFalse(result["panels_rebuilt"])
        self.assertEqual(result["archives"][0]["indexed_pdf_members_verified"], 1)
        self.assertEqual(result["archives"][0]["unindexed_pdf_members"], 0)

    def test_archive_byte_change_fails_before_pdf_read(self):
        self.write_meta()
        with (self.src / self.NAME).open("ab") as f:
            f.write(b"tampered")
        with self.assertRaisesRegex(ValueError, "Original ZIP SHA mismatch"):
            self.call()

    def test_incorrect_expected_member_fails(self):
        self.write_meta(member="wrong.pdf")
        with self.assertRaisesRegex(ValueError, "indexed PDFs absent"):
            self.call()

    def test_pdf_payload_hash_mismatch_fails(self):
        self.write_meta(content_sha=sha(b"%PDF-not-the-payload"))
        with self.assertRaisesRegex(ValueError, "PDF SHA mismatch"):
            self.call()

    def test_inventory_claim_without_hash_match_is_rejected(self):
        self.write_meta(hash_status="unverified")
        with self.assertRaisesRegex(ValueError, "Unverified PDF inventory digest"):
            self.call()

    def test_unindexed_pdf_is_reported_not_confused_with_indexed(self):
        self.write_source({self.MEMBER: self.BODY, "extra.pdf": b"%PDF-extra"})
        self.write_meta()
        self.assertEqual(self.call()["archives"][0]["unindexed_pdf_members"], 1)

    def test_unsafe_member_is_rejected_even_without_extraction(self):
        self.write_source({self.MEMBER: self.BODY, "../unsafe.txt": b"x"})
        self.write_meta()
        with self.assertRaisesRegex(ValueError, "Unsafe ZIP member"):
            self.call()


    def pinned_fixture(self):
        return {
            "injury_archive_summary.csv":
                git_blob_sha1(self.meta / "injury_archive_summary.csv"),
            "injury_report_inventory.csv.gz":
                git_blob_sha1(self.meta / "injury_report_inventory.csv.gz"),
        }

    def test_pinned_source_accepts_exact_known_metadata_and_archive(self):
        self.write_meta()
        pinned_zip = sha((self.src / self.NAME).read_bytes())
        with patch.dict(PINNED_SOURCE_BLOBS, self.pinned_fixture()):
            with patch.dict(PINNED_ARCHIVES, {self.NAME: (pinned_zip, 1)}):
                result = verify(self.src, self.meta, (self.NAME,))
        self.assertTrue(result["pinned_provenance_verified"])
        self.assertEqual(result["pinned_provenance_git_blob_sha1"],
                         self.pinned_fixture())

    def test_pinned_inventory_prevents_silent_metadata_change(self):
        self.write_meta()
        pinned = self.pinned_fixture()
        with (self.meta / "injury_archive_summary.csv").open("ab") as stream:
            stream.write(b"\\n")
        with patch.dict(PINNED_SOURCE_BLOBS, pinned):
            with self.assertRaisesRegex(ValueError, "Original provenance file changed"):
                verify(self.src, self.meta, (self.NAME,))

    def test_pinned_archive_sha_rejects_rewritten_summary(self):
        self.write_meta()
        with patch.dict(PINNED_SOURCE_BLOBS, self.pinned_fixture()):
            with patch.dict(PINNED_ARCHIVES, {self.NAME: ("0" * 64, 1)}):
                with self.assertRaisesRegex(ValueError, "Archive SHA differs"):
                    verify(self.src, self.meta, (self.NAME,))

    def test_pinned_pdf_count_must_match(self):
        self.write_meta()
        pinned_zip = sha((self.src / self.NAME).read_bytes())
        with patch.dict(PINNED_SOURCE_BLOBS, self.pinned_fixture()):
            with patch.dict(PINNED_ARCHIVES, {self.NAME: (pinned_zip, 2)}):
                with self.assertRaisesRegex(ValueError, "Inventory PDF count"):
                    verify(self.src, self.meta, (self.NAME,))


if __name__ == "__main__":
    unittest.main()
