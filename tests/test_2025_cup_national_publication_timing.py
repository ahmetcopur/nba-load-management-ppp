"""Prevent hindsight/backdating in first-party/secondary 2025 Cup TV source joins."""
from __future__ import annotations

import unittest

from scripts.data_rebuild import audit_2025_cup_national_publication_timing as audit
from scripts.data_rebuild import verify_cup_2025_aug13_contemporaneous_secondary_sources as secondary
from scripts.data_rebuild import verify_official_nba_cup_2025_aug13_team_press_sources as first
from scripts.data_rebuild import verify_official_nba_cup_2025_named_broadcasts as aug14
from scripts.data_rebuild import verify_official_nba_cup_2025_all_15_national_broadcasts as aug21


class Cup2025ProspectiveTVSourceTests(unittest.TestCase):
    def setUp(self):
        self.first=first.load_source(first.DEFAULT_SOURCE)
        self.second=secondary.load(secondary.SECONDARY)
        self.nine=aug14.load_source(aug14.SOURCE)
        self.fifteen=aug21.load(aug21.SOURCE)

    def run_audit(self):
        return audit.verify(self.first,self.second,self.nine,self.fifteen)

    def test_named_national_sources_original_chronology_is_six_four_five(self):
        result=self.run_audit()
        self.assertEqual(result["network_first_verified_by_date_counts"],
                         {"2025-08-13":6,"2025-08-14":4,"2025-08-21":5})
        self.assertEqual(result["National_games_with_Aug13_first_dated_fixture_evidence"],9)
        self.assertEqual(result["national_games_without_Aug13_game_specific_source"],6)

    def test_source_tiers_remain_three_original_six_secondary_six_missing(self):
        result=self.run_audit()
        rows=result["per_national_game_evidence"]
        self.assertEqual(sum(r["matchup_in_original_Aug_13_NBA_team_first_party"] for r in rows),3)
        self.assertEqual(sum(r["matchup_in_Aug_13_first_dated_secondary_news"] for r in rows),6)
        self.assertEqual(sum(not r["matchup_in_original_Aug_13_NBA_team_first_party"] and
                             not r["matchup_in_Aug_13_first_dated_secondary_news"]
                             for r in rows),6)

    def test_nov7_warriors_denver_network_not_backdated_from_later_NBA(self):
        result=self.run_audit()
        rows=[r for r in result["per_national_game_evidence"]
              if r["game_date_et"]=="2025-11-07" and
              r["away_team"]=="Golden State Warriors"]
        self.assertEqual(len(rows),1)
        self.assertTrue(rows[0]["matchup_in_original_Aug_13_NBA_team_first_party"])
        self.assertFalse(rows[0]["specific_national_network_positively_named_in_Aug_13_article"])
        self.assertEqual(rows[0]["earliest_network_independently_verified_by_date"],"2025-08-21")

    def test_nov25_orlando_philadelphia_known_team_before_network(self):
        result=self.run_audit()
        rows=[r for r in result["per_national_game_evidence"]
              if r["game_date_et"]=="2025-11-25" and
              r["away_team"]=="Orlando Magic"]
        self.assertEqual(len(rows),1)
        self.assertTrue(rows[0]["matchup_in_Aug_13_first_dated_secondary_news"])
        self.assertFalse(rows[0]["specific_national_network_positively_named_in_Aug_13_article"])
        self.assertEqual(rows[0]["earliest_network_independently_verified_by_date"],"2025-08-14")

    def test_lakers_clippers_NBC_original_news_normalizes_to_NBC_Peacock(self):
        result=self.run_audit()
        rows=[r for r in result["per_national_game_evidence"]
              if r["away_team"]=="LA Clippers" and r["home_team"]=="Los Angeles Lakers"]
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["national_network_as_confirmed_by_Aug_21"],"NBC/Peacock")
        self.assertEqual(rows[0]["positive_Aug_13_network_if_any"],"NBC/Peacock")
        self.assertEqual(rows[0]["earliest_network_independently_verified_by_date"],"2025-08-13")

    def test_change_original_secondary_positive_network_is_rejected(self):
        fake=self.second.copy()
        ix=fake.loc[fake.source_positively_named_network.eq("NBC")].index
        self.assertEqual(len(ix),1)
        fake.loc[ix,"source_positively_named_network"]="Prime"
        with self.assertRaisesRegex(ValueError,"exact date/host/network"):
            audit.verify(self.first,fake,self.nine,self.fifteen)

    def test_first_party_original_press_audit_is_mandatory(self):
        with self.assertRaisesRegex(ValueError,"20 appearances"):
            audit.verify(self.first.iloc[:-1],self.second,self.nine,self.fifteen)

    def test_original_Aug14_nine_cannot_be_later_relabelled(self):
        fake=self.nine.copy()
        fake.loc[0,"source_announced_network"]="ESPN"
        with self.assertRaisesRegex(ValueError,"named 2025 original NBA broadcast"):
            audit.verify(self.first,self.second,fake,self.fifteen)

    def test_later_fifteen_NBA_network_row_change_fails(self):
        fake=self.fifteen.copy()
        fake.loc[0,"source_announced_network"]="ESPN"
        with self.assertRaisesRegex(ValueError,"published national exact"):
            audit.verify(self.first,self.second,self.nine,fake)

    def test_original_private_acceptance_is_not_claimed_by_public_crosswalk(self):
        r=self.run_audit()
        self.assertFalse(r["original_private_Cup_or_TV_archives_compared"])
        self.assertFalse(r["original_Aug13_NBA_group_first_release_60_game_binary_recovered"])
        self.assertFalse(r["all_2025_Cup_national_actual_broadcasts_preknown_as_Aug13_opponent_specific"])


if __name__=="__main__":
    unittest.main()
