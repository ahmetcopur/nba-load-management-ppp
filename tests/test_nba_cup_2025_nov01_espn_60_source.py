"""Later ESPN 60/60 2025 Cup fixture verification, NOT Aug13 first-release gate."""
from __future__ import annotations

import unittest

from scripts.data_rebuild import verify_nba_cup_2025_nov01_espn_60_groups as audit
from scripts.data_rebuild import verify_official_nba_cup_2025_aug13_team_press_sources as original
from scripts.data_rebuild import verify_cup_2025_aug13_contemporaneous_secondary_sources as secondary
from scripts.data_rebuild import verify_official_nba_cup_2025_named_broadcasts as aug14
from scripts.data_rebuild import verify_official_nba_cup_2025_all_15_national_broadcasts as nba


class LaterESPN60FixtureSourceTests(unittest.TestCase):
    def setUp(self):
        self.espn=audit.load(audit.SOURCE)
        self.first=original.load_source(original.DEFAULT_SOURCE)
        self.second=secondary.load(secondary.SECONDARY)
        self.nine=aug14.load_source(aug14.SOURCE)
        self.fifteen=nba.load(nba.SOURCE)

    def verify(self, espn=None):
        return audit.verify(
            self.espn if espn is None else espn,self.first,self.second,
            self.nine,self.fifteen
        )

    def test_complete_60_later_ESPN_game_tuples_all_33_contemporaneous_and_15_national(self):
        r=self.verify()
        self.assertEqual(r["2025_later_ESPN_editorial_complete_group_fixtures_exact"],60)
        self.assertEqual(r["original_Aug13_NBA_team_first_party_fixtures_crosschecked"],19)
        self.assertEqual(r["additional_Aug13_first_dated_secondary_source_fixtures_crosschecked"],14)
        self.assertEqual(r["NBA_named_national_source_fixture_and_network_matches"],15)
        self.assertTrue(r["all_30_teams_two_home_two_away"])

    def test_not_false_original_Aug13_full_release_claim(self):
        r=self.verify()
        self.assertEqual(r["source_editorial_date"],"2025-11-01")
        self.assertFalse(r["2025_original_NBA_Cup_first_Aug13_PDF_recovered"])
        self.assertFalse(r["original_2025_full_60_first_release_networks_independently_checked"])
        self.assertFalse(r["original_private_NBA_Cup_archive_60_rows_checked"])
        self.assertEqual(r["blank_ESPN_article_network_means"],
                         "UNREPORTED_NOT_VERIFIED_NEGATIVE")

    def test_missing_later_editorial_game_fails(self):
        with self.assertRaisesRegex(ValueError,"does not have 60"):
            self.verify(self.espn.iloc[:-1])

    def test_changing_away_team_fails_even_with_unchanged_date_and_network(self):
        changed=self.espn.copy()
        changed.loc[0,"away_team"]="Denver Nuggets"
        with self.assertRaisesRegex(ValueError,"out-of-group"):
            self.verify(changed)

    def test_original_first_party_opponent_swap_fails_even_if_day_count_unchanged(self):
        changed=self.espn.copy()
        a=changed[changed.away_team.eq("Toronto Raptors")].index[0]
        changed.loc[a,"away_team"]="Cleveland Cavaliers"
        with self.assertRaises(ValueError):
            self.verify(changed)

    def test_later_editorial_date_cannot_be_backdated_to_Aug13(self):
        changed=self.espn.copy()
        changed.loc[0,"source_publication_date"]="2025-08-13"
        with self.assertRaisesRegex(ValueError,"falsely backdated"):
            self.verify(changed)

    def test_changed_original_publisher_link_fails(self):
        changed=self.espn.copy()
        changed.loc[0,"source_url"]="https://example.org"
        with self.assertRaisesRegex(ValueError,"original ESPN/ABC7"):
            self.verify(changed)

    def test_wrong_Prime_provider_detected_even_though_15_games_unchanged(self):
        changed=self.espn.copy()
        i=changed[changed.positively_named_network.eq("Prime")].index[0]
        changed.loc[i,"positively_named_network"]="ESPN"
        with self.assertRaisesRegex(ValueError,"national network counts"):
            self.verify(changed)

    def test_swap_ESPN_and_Prime_labels_preserving_aggregate_counts_fails(self):
        changed=self.espn.copy()
        a=changed[changed.positively_named_network.eq("Prime")].index[0]
        b=changed[changed.positively_named_network.eq("ESPN")].index[0]
        changed.loc[a,"positively_named_network"]="ESPN"
        changed.loc[b,"positively_named_network"]="Prime"
        self.assertEqual(changed.positively_named_network.value_counts().to_dict(),
                         self.espn.positively_named_network.value_counts().to_dict())
        with self.assertRaisesRegex(ValueError,"national network differs"):
            self.verify(changed)

    def test_Peacock_provider_does_not_get_mistaken_for_negative_no_TV(self):
        changed=self.espn.copy()
        i=changed[changed.positively_named_network.eq("Peacock")].index[0]
        changed.loc[i,"positively_named_network"]=""
        with self.assertRaisesRegex(ValueError,"network counts"):
            self.verify(changed)

    def test_two_home_two_away_invariant_detects_bad_source_host(self):
        changed=self.espn.copy()
        i=changed.loc[changed.away_team.eq("Atlanta Hawks")].index[0]
        # Deliberately preserve valid group but change home-market assignment.
        a,h=changed.loc[i,["away_team","home_team"]].to_list()
        changed.loc[i,["away_team","home_team"]]=[h,a]
        with self.assertRaises(ValueError):
            self.verify(changed)


if __name__=="__main__":
    unittest.main()
