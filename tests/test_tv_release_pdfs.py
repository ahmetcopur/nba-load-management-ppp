"""Row parser tests for the release-PDF advance-TV verifier (no PDFs needed)."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "tvpdf", ROOT / "scripts/data_rebuild/verify_tv_release_pdfs.py")
tvpdf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tvpdf)


class ParseTests(unittest.TestCase):
    def test_numbered_row_with_network(self):
        row = tvpdf.parse(["784", "Thu.", "2/3/22", "Miami", "Toronto", "7:30 PM", "7:30 PM", "TNT"])
        self.assertEqual((row["away"], row["home"], row["network"]),
                         ("Miami", "Toronto", "TNT"))
        self.assertEqual(row["line"], "784 Thu. 2/3/22 Miami Toronto 7:30 PM 7:30 PM TNT")

    def test_row_without_network(self):
        row = tvpdf.parse(["430", "Thu.", "12/16/21", "Chicago", "Toronto", "7:30 PM", "7:30 PM"])
        self.assertIsNone(row["network"])

    def test_merged_time_network_and_marker_cells_are_split(self):
        row = tvpdf.parse(["491", "Sat.", "12/25/21", "Brooklyn", "L.A. Lakers",
                           "5:00 PM", "8:00 PM ABC/ESPN R"])
        self.assertEqual(row["network"], "ABC/ESPN")
        self.assertTrue(row["line"].endswith("8:00 PM ABC/ESPN R"))

    def test_at_and_vs_separators_and_venue_markers(self):
        row = tvpdf.parse(["Sat.", "11/1/25", "Dallas", "vs", "Detroit",
                           "8:00 PM", "10:00 PM", "Peacock", "A"])
        self.assertEqual((row["away"], row["home"], row["network"]),
                         ("Dallas", "Detroit", "Peacock"))
        row = tvpdf.parse(["61", "Tue.", "10/22/24", "New York", "at", "Boston",
                           "7:30 PM", "7:30 PM", "TNT", "R"])
        self.assertEqual(row["home"], "Boston")

    def test_page_footer_is_not_part_of_the_row(self):
        row = tvpdf.parse(["104", "Tue.", "11/2/21", "Miami", "Dallas", "6:30 PM", "7:30 PM",
                           "TNT", "SUBJECT TO CHANGE", "PAGE 2 of 23"])
        self.assertEqual(row["line"], "104 Tue. 11/2/21 Miami Dallas 6:30 PM 7:30 PM TNT")
        row = tvpdf.parse(["1230", "Sun.", "4/10/22", "Utah", "Portland", "TBD", "TBD",
                           "R = ESPN Radio"])
        self.assertIsNone(row["network"])

    def test_center_court_recorded_as_nba_tv_and_flagged(self):
        row = tvpdf.parse(["5", "Wed.", "11/13/24", "Utah", "at", "Denver", "7:00 PM",
                           "9:00 PM", "NBA TV (CC)"])
        self.assertEqual(row["network"], "NBA TV")
        self.assertTrue(row["center_court"])

    def test_malformed_rows_fail(self):
        with self.assertRaisesRegex(ValueError, "times"):
            tvpdf.parse(["1", "Tue.", "10/19/21", "Brooklyn", "Milwaukee", "TNT"])
        with self.assertRaisesRegex(ValueError, "two team"):
            tvpdf.parse(["1", "Tue.", "10/19/21", "Brooklyn", "7:00 PM", "7:30 PM"])


if __name__ == "__main__":
    unittest.main()
