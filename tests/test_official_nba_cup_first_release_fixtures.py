"""Fail-closed source-only and private-archive interface tests for first-release Cup audit.

These tests use the public transcribed NBA Cup game schedule only.
Private original game/TV ZIP comparisons remain a separate local acceptance.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from scripts.data_rebuild import verify_official_nba_cup_first_release_fixtures as cup


class CupFirstReleaseSourceTests(unittest.TestCase):
    def setUp(self):
        self.reference = cup.load_source(cup.DEFAULT_SOURCE)

    def test_all_120_original_group_source_rows_pass(self):
        result = cup.validate_first_release(self.reference)
        self.assertEqual(sum(s["source_fixture_rows"] for s in result.values()), 120)
        self.assertEqual(result["2023-24"]["broadcast_counts_including_separate_NBA_TV"]["NBA TV"], 2)
        self.assertEqual(result["2024-25"]["broadcast_counts_including_separate_NBA_TV"]["NBA TV"], 3)

    def test_exact_first_release_source_dates(self):
        self.assertEqual(cup.RELEASES["2023-24"], "2023-08-15")
        self.assertEqual(cup.RELEASES["2024-25"], "2024-08-13")

    def test_missing_source_fixture_fails(self):
        with self.assertRaisesRegex(ValueError, "120 genuine"):
            cup.validate_first_release(self.reference.iloc[:-1])

    def test_wrong_group_opponent_fails(self):
        altered = self.reference.copy()
        altered.loc[0, "home_team"] = "Toronto Raptors"
        with self.assertRaisesRegex(ValueError, "incompatible official NBA group"):
            cup.validate_first_release(altered)

    def test_wrong_match_date_fails(self):
        altered = self.reference.copy()
        altered.loc[0, "game_date_et"] = "2023-11-04"
        with self.assertRaisesRegex(ValueError, "game day allocation"):
            cup.validate_first_release(altered)

    def test_wrong_first_release_date_fails(self):
        altered = self.reference.copy()
        altered.loc[0, "first_release_date"] = "2023-08-17"
        with self.assertRaisesRegex(ValueError, "publication date"):
            cup.validate_first_release(altered)

    def test_wrong_first_release_network_fails(self):
        altered = self.reference.copy()
        altered.loc[0, "first_release_network"] = "TNT"
        with self.assertRaisesRegex(ValueError, "broadcast counts"):
            cup.validate_first_release(altered)

    def test_duplicate_fixture_fails(self):
        altered = self.reference.copy()
        altered.loc[1, list(cup.KEY)] = altered.loc[0, list(cup.KEY)].to_list()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            cup.validate_first_release(altered)

    def test_unsourced_2025_fixture_cannot_be_sneaked_into_source(self):
        altered = self.reference.copy()
        altered.loc[0, "season"] = "2025-26"
        with self.assertRaisesRegex(ValueError, "only 2023-24"):
            cup.validate_first_release(altered)

    def test_changed_private_archive_rejected_before_parsing_game(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "cup.zip", Path(d) / "freeze.zip"
            a.write_bytes(b"not the original Cup archive")
            b.write_bytes(b"not the original freeze archive")
            with self.assertRaisesRegex(ValueError, "private Cup ZIP digest differs"):
                cup.compare_to_private_archives(self.reference, a, b)


if __name__ == "__main__":
    unittest.main()
