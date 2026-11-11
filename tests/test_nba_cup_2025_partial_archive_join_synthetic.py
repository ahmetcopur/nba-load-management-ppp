"""Positive/negative synthetic frozen-archive exercises for 2025 Cup 19/33/15 joins.

The 60-game "original" archive here is fabricated IN MEMORY for testing and
is never claimed to be the immutable original NBA research archive. The
production commands still require full original SHA-256 pinning before calling
these exact matchers.
"""
from __future__ import annotations

import unittest

import pandas as pd

from scripts.data_rebuild import compare_nba_cup_exact_source_rows as join
from scripts.data_rebuild import verify_official_nba_cup_2025_aug13_team_press_sources as original_teams
from scripts.data_rebuild import verify_cup_2025_aug13_contemporaneous_secondary_sources as news
from scripts.data_rebuild import verify_official_nba_cup_2025_all_15_national_broadcasts as national


class Partial2025OriginalSourceJoinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first=original_teams.load_source(original_teams.DEFAULT_SOURCE)
        cls.second=news.load(news.SECONDARY)
        cls.fifteen=national.load(national.SOURCE)
        cls.nineteen=cls.first.drop_duplicates(list(join.MATCH)).copy()
        cls.thirtythree=pd.concat([cls.first,cls.second],ignore_index=True).drop_duplicates(list(join.MATCH))
        assert len(cls.nineteen)==19 and len(cls.thirtythree)==33

    def synthetic_original_full_60(self):
        frame=self.thirtythree.loc[:,list(join.MATCH)].copy()
        other=pd.DataFrame([
            {"season":"2025-26","game_date_et":"2025-11-28",
             "away_team":f"FICTIONAL AWAY {i}","home_team":f"FICTIONAL HOME {i}"}
            for i in range(27)
        ])
        frame=pd.concat([frame,other],ignore_index=True)
        self.assertEqual(len(frame),60)
        return frame

    def test_positive_19_original_NBA_team_source_to_synthetic_60(self):
        r=join.exact_group_fixture_join(self.nineteen,self.synthetic_original_full_60(),19,True)
        self.assertEqual(r["source_fixture_exact"],19)
        self.assertFalse(r["exact_full_match"])

    def test_positive_33_combined_source_tiers_to_synthetic_60(self):
        r=join.exact_group_fixture_join(self.thirtythree,self.synthetic_original_full_60(),33,True)
        self.assertEqual(r["source_fixture_exact"],33)
        self.assertEqual(r["original_archive_game_count"],60)

    def test_negative_19_missing_game_from_synthetic_private_archive(self):
        original=self.synthetic_original_full_60()
        original.loc[0,"game_date_et"]="2025-11-20"
        with self.assertRaisesRegex(ValueError,"date/away/home group mismatch"):
            join.exact_group_fixture_join(self.nineteen,original,19,True)

    def test_negative_33_source_missing_even_when_archive_retains_sixty(self):
        original=self.synthetic_original_full_60()
        original.loc[25,"home_team"]="SOME OTHER HOST"
        with self.assertRaisesRegex(ValueError,"date/away/home group mismatch"):
            join.exact_group_fixture_join(self.thirtythree,original,33,True)

    def test_negative_original_archive_fixture_duplicate_is_not_silently_ignored(self):
        original=self.synthetic_original_full_60()
        original.loc[50,list(join.MATCH)]=original.loc[51,list(join.MATCH)].to_list()
        with self.assertRaisesRegex(ValueError,"duplicated"):
            join.exact_group_fixture_join(self.thirtythree,original,33,True)

    def test_positive_15_later_NBA_named_national_Cup_games_as_partial_subset(self):
        archive=self.fifteen.loc[:,list(join.MATCH)].copy()
        remainder=self.synthetic_original_full_60()
        archive=pd.concat([archive,remainder],ignore_index=True).drop_duplicates(list(join.MATCH))
        r=join.exact_group_fixture_join(self.fifteen,archive,15,True)
        self.assertEqual(r["source_fixture_exact"],15)

    def test_positive_15_later_NBA_network_labels_exact_from_synthetic_PDF(self):
        renamed=self.fifteen.rename(
            columns={"source_announced_network":"first_release_network"})
        r=join.exact_first_release_network_join(renamed,renamed.copy(),15)
        self.assertEqual(r["exact_NBA_source_network_rows"],15)

    def test_negative_15_exact_2025_network_labels_are_not_fuzzy_normalized(self):
        renamed=self.fifteen.rename(
            columns={"source_announced_network":"first_release_network"})
        fake=renamed.copy()
        idx=fake[fake.first_release_network.eq("Prime")].index[0]
        fake.loc[idx,"first_release_network"]="Amazon Prime"
        with self.assertRaisesRegex(ValueError,"TV mismatch"):
            join.exact_first_release_network_join(renamed,fake,15)

    def test_negative_NBC_Peacock_vs_NBC_requires_explicit_source_date_mapping(self):
        renamed=self.fifteen.rename(
            columns={"source_announced_network":"first_release_network"})
        fake=renamed.copy()
        idx=fake[fake.first_release_network.eq("NBC/Peacock")].index[0]
        fake.loc[idx,"first_release_network"]="NBC"
        with self.assertRaisesRegex(ValueError,"TV mismatch"):
            join.exact_first_release_network_join(renamed,fake,15)

    def test_partial_source_cannot_be_accidentally_claimed_complete(self):
        with self.assertRaisesRegex(ValueError,"original rows extra"):
            join.exact_group_fixture_join(self.nineteen,self.synthetic_original_full_60(),19,False)


if __name__=="__main__":
    unittest.main()
