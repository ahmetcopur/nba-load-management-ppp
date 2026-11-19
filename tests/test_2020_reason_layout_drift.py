"""Synthetic checks: 2020–21 PDF reason text must never be silently accepted."""
import csv
import gzip
from pathlib import Path
import tempfile
import unittest

from scripts.data_rebuild.audit_2020_reason_layout_drift import summarize

FIELDS = ["source_file", "snapshot_timestamp_utc", "team", "player_name",
          "status", "reason"]


def write_csv(path, rows):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "wt", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


class HistoricalReasonDriftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.original = self.root / "original.csv.gz"
        self.candidate = self.root / "candidate.csv"
        self.rows = [
            dict(source_file="reportA.pdf", snapshot_timestamp_utc="2020-12-22T18:00:00",
                 team="A", player_name="Alpha", status="Out", reason="Left knee soreness"),
            dict(source_file="reportA.pdf", snapshot_timestamp_utc="2020-12-22T18:00:00",
                 team="A", player_name="Beta", status="Out", reason="Right ankle"),
            dict(source_file="reportB.pdf", snapshot_timestamp_utc="2020-12-23T18:00:00",
                 team="B", player_name="Gamma", status="Out", reason="Illness"),
        ]
        write_csv(self.original, self.rows)
        write_csv(self.candidate, list(reversed(self.rows)))

    def test_order_independent_exact_replay(self):
        result = summarize(self.original, self.candidate)
        self.assertTrue(result["accepted_as_exact_replay"])
        self.assertEqual(result["reason_records_differing"], 0)

    def test_wrap_error_flagged_without_player_or_reason_leakage(self):
        copy = [dict(row) for row in self.rows]
        copy[0]["reason"] = "Left knee"
        copy[1]["reason"] = "soreness Right ankle"
        write_csv(self.candidate, copy)
        result = summarize(self.original, self.candidate)
        self.assertFalse(result["accepted_as_exact_replay"])
        self.assertEqual(result["reason_records_differing"], 2)
        self.assertEqual(result["source_pdfs_with_reason_drift"], 1)
        self.assertNotIn("Alpha", repr(result))
        self.assertNotIn("soreness", repr(result))

    def test_wrong_player_identity_is_not_classed_as_reason_drift(self):
        copy = [dict(row) for row in self.rows]
        copy[0]["player_name"] = "Wrong"
        write_csv(self.candidate, copy)
        with self.assertRaisesRegex(ValueError, "Non-reason field identities drifted"):
            summarize(self.original, self.candidate)

    def test_mismatched_status_is_blocking(self):
        copy = [dict(row) for row in self.rows]
        copy[0]["status"] = "Available"
        write_csv(self.candidate, copy)
        with self.assertRaisesRegex(ValueError, "Non-reason field identities drifted"):
            summarize(self.original, self.candidate)

    def test_missing_record_is_blocking(self):
        write_csv(self.candidate, self.rows[:-1])
        with self.assertRaisesRegex(ValueError, "Non-reason field identities drifted"):
            summarize(self.original, self.candidate)

    def test_missing_reason_column_is_blocking(self):
        with self.candidate.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=[col for col in FIELDS if col != "reason"])
            writer.writeheader()
            writer.writerows([{k:v for k,v in r.items() if k != "reason"} for r in self.rows])
        with self.assertRaisesRegex(ValueError, "Missing reason/source_file"):
            summarize(self.original, self.candidate)


if __name__ == "__main__":
    unittest.main()
