"""Tests for original NBA's explicitly named August 14, 2025 Cup broadcasts."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.data_rebuild import verify_official_nba_cup_2025_named_broadcasts as check


class Named2025BroadcastTests(unittest.TestCase):
    def setUp(self):
        self.source = check.load_source(check.SOURCE)

    def test_actual_nine_named_original_press_announcement_tuples(self):
        x = check.verify_named_source(self.source)
        self.assertEqual(x["original_2025_08_14_named_Cup_game_rows"], 9)
        self.assertEqual(x["network_breakdown"], {"Prime": 4, "NBC/Peacock": 2, "ESPN": 3})
        self.assertFalse(x["2025_08_13_entire_first_release_recovered"])

    def test_row_loss_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "expected nine"):
            check.verify_named_source(self.source.iloc[:-1])

    def test_same_day_same_network_opponent_swaps_rejected(self):
        bad = self.source.copy()
        bad.loc[0, "home_team"] = "Memphis Grizzlies"
        bad.loc[1, "home_team"] = "Philadelphia 76ers"
        with self.assertRaisesRegex(ValueError, "tuple changed"):
            check.verify_named_source(bad)

    def test_network_swap_fails_even_if_overall_counts_unchanged(self):
        bad = self.source.copy()
        bad.loc[0, "source_announced_network"] = "ESPN"
        bad.loc[4, "source_announced_network"] = "Prime"
        with self.assertRaisesRegex(ValueError, "tuple changed"):
            check.verify_named_source(bad)

    def test_backdating_to_unverified_aug13_is_rejected(self):
        bad = self.source.copy()
        bad.loc[0, "source_announcement_date_et"] = "2025-08-13"
        with self.assertRaisesRegex(ValueError, "publication date"):
            check.verify_named_source(bad)

    def test_bad_game_day_fails(self):
        bad = self.source.copy()
        bad.loc[0, "game_date_et"] = "2025-11-01"
        with self.assertRaisesRegex(ValueError, "tuple changed"):
            check.verify_named_source(bad)

    def test_changed_original_source_url_fails(self):
        bad = self.source.copy()
        bad.loc[0, "source_url"] = "https://example.org/non-original"
        with self.assertRaisesRegex(ValueError, "press-release URL changed"):
            check.verify_named_source(bad)

    def test_duplicate_named_fixture_fails(self):
        bad = self.source.copy()
        bad.loc[1, list(check.KEYS)] = bad.loc[0, list(check.KEYS)].tolist()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            check.verify_named_source(bad)

    def test_wrong_original_zip_fails_before_member_read(self):
        with tempfile.TemporaryDirectory() as d:
            cup_path, freeze_path = Path(d) / "cup.zip", Path(d) / "freeze.zip"
            cup_path.write_bytes(b"not the original private Cup")
            freeze_path.write_bytes(b"not the original private full freeze")
            with self.assertRaisesRegex(ValueError, "private Cup ZIP digest differs"):
                check.compare_original_archives(self.source, cup_path, freeze_path)

    def test_2025_source_does_not_claim_full_original_group_verification(self):
        x = check.verify_named_source(self.source)
        self.assertFalse(x["2025_all_60_group_game_networks_checked"])
        self.assertFalse(x["all_18_Cup_knockout_game_networks_checked"])


if __name__ == "__main__":
    unittest.main()
