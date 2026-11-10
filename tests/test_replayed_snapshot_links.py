"""Strict synthetic regressions for real-PDF to archived-game-selector identity audit.

Only verifies the fail-closed audit tool. Actual private PDFs and original
selector ZIP must be accepted separately; no synthetic test is Level-C proof.
"""
import csv
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.data_rebuild.audit_replayed_snapshot_links import verify


SEASON = "2022-23"
PUBLISHED = "2023-01-02T18:00:00+00:00"
TIP = "2023-01-02T20:00:00+00:00"
SELECTOR_FIELDS = [
    "game_id", "snapshot_basename", "published_timestamp_utc", "matchup_norm",
    "tip_timestamp_utc", "minutes_before_tip", "inferred_clean_teams",
    "listed_teams", "both_teams_usable",
]


def csv_text(fields, rows):
    from io import StringIO
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def selector(game, basename, matchup, **overrides):
    d = {
        "game_id": game,
        "snapshot_basename": basename,
        "published_timestamp_utc": PUBLISHED,
        "matchup_norm": matchup,
        "tip_timestamp_utc": TIP,
        "minutes_before_tip": "120",
        "inferred_clean_teams": "0",
        "listed_teams": "2",
        "both_teams_usable": "True",
    }
    d.update(overrides)
    return d


class ReparsedSnapshotLinkTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.archive = self.root / "canonical.zip"
        self.logs = self.root / "reparsed_log.csv"
        self.rows = self.root / "reparsed_rows.csv"
        self.full = [selector("FD2022_1", "a.pdf", "AAA@BBB"),
                     selector("FD2022_2", "b.pdf", "CCC@DDD")]
        self.harmonized = [dict(x) for x in self.full]
        self.logs_data = [
            {"source_file": "/safe/a.pdf", "snapshot_timestamp_utc": PUBLISHED, "status": "ok"},
            {"source_file": "/safe/b.pdf", "snapshot_timestamp_utc": PUBLISHED, "status": "ok"},
        ]
        self.rows_data = [
            {"source_file": "/safe/a.pdf", "snapshot_timestamp_utc": PUBLISHED, "matchup_norm": "AAA@BBB"},
            {"source_file": "/safe/b.pdf", "snapshot_timestamp_utc": PUBLISHED, "matchup_norm": "CCC@DDD"},
        ]
        self.season = SEASON
        self.write()

    def write(self, duplicate_member=False):
        with ZipFile(self.archive, "w") as z:
            for panel, records in (("full", self.full), ("harmonized", self.harmonized)):
                name = f"nba_canonical_snapshot_selector_v1/{self.season}_game_snapshot_join_{panel}_canonical.csv"
                text = csv_text(SELECTOR_FIELDS, records)
                z.writestr(name, text)
                if duplicate_member and panel == "full":
                    # Zipfile can store duplicated names; verifier must never choose one silently.
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        z.writestr(name, text)
        self.logs.write_text(csv_text(["source_file", "snapshot_timestamp_utc", "status"], self.logs_data))
        self.rows.write_text(csv_text(["source_file", "snapshot_timestamp_utc", "matchup_norm"], self.rows_data))

    def run_audit(self):
        return verify(self.archive, self.season, self.rows, self.logs,
                      expected_games=2)

    def test_exact_links_and_clocks_pass(self):
        result = self.run_audit()
        self.assertTrue(result["passed"])
        for p in result["panels"].values():
            self.assertEqual(p["selected_games"], 2)
            self.assertEqual(p["selected_pdf_logs_verified"], 2)
            self.assertFalse(p["problems"])

    def test_duplicate_selected_game_id_fails(self):
        self.full[1]["game_id"] = self.full[0]["game_id"]
        self.write()
        with self.assertRaisesRegex(ValueError, "duplicate_game_id"):
            self.run_audit()

    def test_missing_game_id_fails(self):
        self.full[0]["game_id"] = ""
        self.write()
        with self.assertRaisesRegex(ValueError, "empty_game_id"):
            self.run_audit()

    def test_forged_clean_inference_does_not_waive_missing_matchup(self):
        self.rows_data.pop()
        self.full[1].update(inferred_clean_teams="2", listed_teams="0")
        self.harmonized[1].update(inferred_clean_teams="2", listed_teams="0")
        self.write()
        with self.assertRaisesRegex(ValueError, "missing_selected_matchup"):
            self.run_audit()

    def test_known_2023_clean_exception_is_allowed_once(self):
        self.season = "2023-24"
        for records in (self.full, self.harmonized):
            records[1].update(game_id="FD2023_5", inferred_clean_teams="2",
                              listed_teams="0")
        self.rows_data.pop()
        self.write()
        result = self.run_audit()
        self.assertEqual(result["panels"]["full"]["inferred_clean_game_ids"], ["FD2023_5"])
        self.assertTrue(result["passed"])

    def test_2023_known_clean_exception_requires_exact_flags(self):
        self.season = "2023-24"
        for records in (self.full, self.harmonized):
            records[1].update(game_id="FD2023_5", inferred_clean_teams="1",
                              listed_teams="0")
        self.rows_data.pop()
        self.write()
        with self.assertRaisesRegex(ValueError, "missing_selected_matchup"):
            self.run_audit()

    def test_missing_or_failed_parser_log_fails(self):
        self.logs_data[0]["status"] = "error"
        self.write()
        with self.assertRaisesRegex(ValueError, "missing_or_failed_pdf_parse"):
            self.run_audit()

    def test_duplicate_parser_log_identity_fails(self):
        self.logs_data.append(dict(self.logs_data[0]))
        self.write()
        with self.assertRaisesRegex(ValueError, "Duplicate source PDF"):
            self.run_audit()

    def test_non_pre_tip_source_fails(self):
        self.full[0]["tip_timestamp_utc"] = "2023-01-02T17:00:00+00:00"
        self.full[0]["minutes_before_tip"] = "-60"
        self.write()
        with self.assertRaisesRegex(ValueError, "selected_pdf_not_pre_tip"):
            self.run_audit()

    def test_incorrect_snapshot_age_fails(self):
        self.full[0]["minutes_before_tip"] = "119"
        self.write()
        with self.assertRaisesRegex(ValueError, "incorrect_recorded_snapshot_age"):
            self.run_audit()

    def test_full_and_harmonized_game_sets_must_agree(self):
        self.harmonized[1]["game_id"] = "FD2022_BAD"
        self.write()
        with self.assertRaisesRegex(ValueError, "canonical game sets differ"):
            self.run_audit()

    def test_duplicate_selector_archive_members_fail(self):
        self.write(duplicate_member=True)
        with self.assertRaisesRegex(ValueError, "Expected one canonical selector ZIP member"):
            self.run_audit()

    def test_missing_required_selector_column_fails(self):
        with ZipFile(self.archive, "w") as z:
            for panel, rows in (("full", self.full), ("harmonized", self.harmonized)):
                name = f"nba_canonical_snapshot_selector_v1/{self.season}_game_snapshot_join_{panel}_canonical.csv"
                z.writestr(name, csv_text([x for x in SELECTOR_FIELDS if x != "tip_timestamp_utc"],
                                          [{k: v for k, v in row.items() if k != "tip_timestamp_utc"}
                                           for row in rows]))
        with self.assertRaisesRegex(ValueError, "Missing selector fields"):
            self.run_audit()


if __name__ == "__main__":
    unittest.main()
