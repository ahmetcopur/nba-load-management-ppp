"""Source-only and fail-closed safeguards for complete named 2025 Cup national slate."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.data_rebuild import verify_official_nba_cup_2025_all_15_national_broadcasts as check
from scripts.data_rebuild import verify_official_nba_cup_2025_named_broadcasts as earlier


class Fifteen2025NBAOfficialNationalCupTests(unittest.TestCase):
    def setUp(self):
        self.source = check.load(check.SOURCE)
        self.nine = earlier.load_source(earlier.SOURCE)

    def test_15_original_NBA_com_games_include_nine_earlier_named_release_rows(self):
        report = check.validate_15(self.source, self.nine)
        self.assertEqual(report["NBA_official_public_2025_group_national_game_rows"], 15)
        self.assertEqual(report["independently_named_in_original_Aug_14_release"], 9)
        self.assertEqual(report["national_provider_counts"],
                         {"Prime": 10, "NBC/Peacock": 2, "ESPN": 3})

    def test_2025_original_Aug13_full_Cup_release_still_explicitly_open(self):
        report = check.validate_15(self.source, self.nine)
        self.assertFalse(report["original_Aug_13_60_game_Cup_release_binary_and_all_60_rows_verified"])
        self.assertFalse(report["first_release_date_for_six_additional_games_independently_established"])

    def test_missing_NBA_named_national_game_fails(self):
        with self.assertRaisesRegex(ValueError, "not exactly 15"):
            check.validate_15(self.source.iloc[:-1], self.nine)

    def test_wrong_2025_first_party_publication_date_fails(self):
        changed = self.source.copy()
        changed.loc[0, "source_verified_by_date"] = "2025-08-13"
        with self.assertRaisesRegex(ValueError, "source update date differs"):
            check.validate_15(changed, self.nine)

    def test_wrong_NBA_source_URL_fails(self):
        changed = self.source.copy()
        changed.loc[0, "source_url"] = "https://example.org/"
        with self.assertRaisesRegex(ValueError, "not original NBA.com"):
            check.validate_15(changed, self.nine)

    def test_same_day_network_preserving_team_change_fails(self):
        changed = self.source.copy()
        changed.loc[2, "home_team"] = "Memphis Grizzlies"
        with self.assertRaisesRegex(ValueError, "exact dated matchup/network"):
            check.validate_15(changed, self.nine)

    def test_wrong_broadcaster_even_with_same_count_fails(self):
        changed = self.source.copy()
        changed.loc[0, "source_announced_network"] = "ESPN"
        changed.loc[10, "source_announced_network"] = "Prime"
        with self.assertRaisesRegex(ValueError, "exact dated matchup/network"):
            check.validate_15(changed, self.nine)

    def test_earlier_aug14_named_source_substitution_fails(self):
        earlier_changed = self.nine.copy()
        earlier_changed.loc[0, "source_announced_network"] = "ESPN"
        with self.assertRaisesRegex(ValueError, "named 2025 original NBA broadcast"):
            check.validate_15(self.source, earlier_changed)

    def test_duplicate_group_fixture_fails(self):
        changed = self.source.copy()
        changed.loc[1, list(check.KEYS)] = changed.loc[0, list(check.KEYS)].to_list()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            check.validate_15(changed, self.nine)

    def test_wrong_original_private_zips_fail_before_game_read(self):
        with tempfile.TemporaryDirectory() as root:
            cup, freeze = Path(root) / "cup.zip", Path(root) / "freeze.zip"
            cup.write_bytes(b"not original Cup")
            freeze.write_bytes(b"not original full frozen project")
            with self.assertRaisesRegex(ValueError, "original Cup source ZIP SHA-256 drift"):
                check.compare_original_private(self.source, self.nine, cup, freeze)


if __name__ == "__main__":
    unittest.main()
