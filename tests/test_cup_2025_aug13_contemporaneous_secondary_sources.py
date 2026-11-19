"""Tier-isolated original-first-date NBA Cup 2025 verification tests."""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from scripts.data_rebuild import verify_cup_2025_aug13_contemporaneous_secondary_sources as check
from scripts.data_rebuild import verify_official_nba_cup_2025_aug13_team_press_sources as first_party


class Aug13SecondTierCupTests(unittest.TestCase):
    def setUp(self):
        self.second = check.load(check.SECONDARY)
        self.first = first_party.load_source(first_party.DEFAULT_SOURCE)

    def test_source_only_14_additional_19_original_first_party_33_total(self):
        result=check.validate_sources(self.second,self.first)
        self.assertEqual(result["original_NBA_Aug13_first_party_fixtures_unchanged"],19)
        self.assertEqual(result["second_tier_distinct_game_identities"],14)
        self.assertEqual(result["distinct_first_party_plus_secondary"],33)
        self.assertEqual(result["secondary_only_original_group_coverage"],{"WB":7,"EB":7})
        self.assertEqual(result["cross_report_duplicate_matches"],2)

    def test_aug14_revised_pelicans_source_does_not_claim_unmodified_aug13(self):
        x=check.validate_sources(self.second,self.first)
        self.assertEqual(x["secondary_unique_with_no_known_next_day_revision"],11)
        self.assertEqual(x["secondary_unique_requiring_Aug13_pre_revision_evidence"],3)
        self.assertFalse(x["full_original_2025_Aug13_60_game_by_day_PDF_verified"])

    def test_all_network_blanks_are_unknown_not_negative(self):
        x=check.validate_sources(self.second,self.first)
        self.assertTrue(x["unmentioned_networks_are_unknown_not_no_national_TV"])
        self.assertEqual(self.second.source_positively_named_network.value_counts()[""],10)

    def test_team_home_away_date_swap_fails(self):
        altered=self.second.copy()
        altered.loc[0,["away_team","home_team"]]=altered.loc[0,["home_team","away_team"]].tolist()
        with self.assertRaisesRegex(ValueError,"exact date/host/network"):
            check.validate_sources(altered,self.first)

    def test_double_reported_pelicans_lakers_duplicate_drift_fails(self):
        altered=self.second.copy()
        mask=altered.reporting_team.eq("New Orleans Pelicans") & altered.away_team.eq("Los Angeles Lakers")
        self.assertEqual(mask.sum(),1)
        altered.loc[mask,"game_date_et"]="2025-11-21"
        with self.assertRaisesRegex(ValueError,"exact date/host/network"):
            check.validate_sources(altered,self.first)

    def test_source_publisher_is_NOT_relabelled_NBA_first_party(self):
        altered=self.second.copy()
        altered.loc[0,"source_evidence_tier"]="original_NBA_team_first_party"
        with self.assertRaisesRegex(ValueError,"source URL / source tier"):
            check.validate_sources(altered,self.first)

    def test_subsequently_edited_pelicans_source_cannot_be_silent(self):
        altered=self.second.copy()
        altered.loc[altered.reporting_team.eq("New Orleans Pelicans"),
                    "source_updated_date_if_known"]=""
        with self.assertRaisesRegex(ValueError,"source URL / source tier / revision date"):
            check.validate_sources(altered,self.first)

    def test_no_fake_tV_zero_flags(self):
        altered=self.second.copy()
        altered.loc[altered.source_positively_named_network.eq(""),"source_positively_named_network"]="NO NATIONAL"
        with self.assertRaisesRegex(ValueError,"exact date/host/network"):
            check.validate_sources(altered,self.first)

    def test_original_five_team_first_party_cannot_be_removed(self):
        with self.assertRaisesRegex(ValueError,"20 appearances"):
            check.validate_sources(self.second,self.first.iloc[:-1])

    def test_original_Cup_zip_tampering_fails_before_parsing(self):
        with tempfile.TemporaryDirectory() as folder:
            z=Path(folder)/"not_original_cup.zip"
            z.write_bytes(b"do not accept this as immutable research")
            with self.assertRaisesRegex(ValueError,"immutable Cup ZIP SHA-256 drift"):
                check.check_original_private(self.second,self.first,z)


if __name__ == "__main__":
    unittest.main()
