"""Fail-closed 2025-08-13 ORIGINAL first-party NBA team Cup fixture source tests."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.data_rebuild import verify_official_nba_cup_2025_aug13_team_press_sources as check


class OriginalAug13TeamCupSourceTests(unittest.TestCase):
    def setUp(self):
        self.frame = check.load_source(check.DEFAULT_SOURCE)

    def test_five_original_team_stories_20_appearances_nineteen_games(self):
        report = check.validate_source(self.frame)
        self.assertEqual(report["original_same_day_2025_08_13_first_party_team_articles"], 5)
        self.assertEqual(report["original_press_game_appearances"], 20)
        self.assertEqual(report["independent_distinct_original_fixture_identities"], 19)
        self.assertTrue(report["cross_source_identical_indiana_at_toronto_2025_11_26"])

    def test_an_original_article_which_does_not_name_national_TV_must_remain_unknown(self):
        report = check.validate_source(self.frame)
        self.assertEqual(report["first_party_positively_named_Prime_games"], 1)
        self.assertEqual(report["non_named_network_classification"], "UNKNOWN_NOT_NEGATIVE")
        self.assertFalse(report["2025_all_60_original_first_release_fixture_identities_checked"])
        self.assertFalse(report["original_private_Cup_game_lookup_source_join_executed"])

    def test_removing_one_article_row_fails(self):
        with self.assertRaisesRegex(ValueError,"20 appearances"):
            check.validate_source(self.frame.iloc[:-1])

    def test_swapping_a_home_team_and_visitor_breaks_original_source(self):
        bad=self.frame.copy()
        bad.loc[0,["away_team","home_team"]]=bad.loc[0,["home_team","away_team"]].tolist()
        with self.assertRaisesRegex(ValueError,"date/opponents/provider tuple"):
            check.validate_source(bad)

    def test_changing_only_game_date_fails_exact_source_comparison(self):
        bad=self.frame.copy()
        bad.loc[0,"game_date_et"]="2025-11-28"
        with self.assertRaisesRegex(ValueError,"date/opponents/provider tuple"):
            check.validate_source(bad)

    def test_2025_aug13_original_published_date_cannot_be_changed(self):
        bad=self.frame.copy()
        bad.loc[0,"source_release_date"]="2025-08-14"
        with self.assertRaisesRegex(ValueError,"release dates"):
            check.validate_source(bad)

    def test_one_team_fake_source_url_fails(self):
        bad=self.frame.copy()
        bad.loc[0,"original_2025_08_13_NBA_team_press_url"]="https://example.invalid"
        with self.assertRaisesRegex(ValueError,"URL not NBA original"):
            check.validate_source(bad)

    def test_false_source_non_national_cannot_be_inserted(self):
        bad=self.frame.copy()
        bad.loc[0,"positively_named_network"]="NO NATIONAL TV"
        with self.assertRaisesRegex(ValueError,"date/opponents/provider tuple"):
            check.validate_source(bad)

    def test_an_indiana_toronto_original_source_disagreement_fails(self):
        bad=self.frame.copy()
        mask=(bad.source_reporting_team=="Indiana Pacers") & (
            bad.home_team=="Toronto Raptors")
        self.assertEqual(mask.sum(),1)
        bad.loc[mask,"game_date_et"]="2025-11-25"
        with self.assertRaisesRegex(ValueError,"date/opponents/provider tuple"):
            check.validate_source(bad)

    def test_private_zip_tampering_fails_before_original_game_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/"not-original-cup.zip"
            fake.write_bytes(b"not the original private historical NBA Cup ZIP")
            with self.assertRaisesRegex(ValueError,"private Cup ZIP SHA-256 differs"):
                check.original_private_compare(self.frame,fake)


if __name__=="__main__":
    unittest.main()
