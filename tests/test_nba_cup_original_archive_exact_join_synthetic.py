"""Positive AND negative exact archive-row joins, using synthetic frozen rows.

The source reference fixtures are public only. Every "archive" DataFrame in
these tests is constructed inside this test; NONE is an actual immutable
original research ZIP, and passing this suite NEVER certifies a private join.
This suite directly drives the same strict comparators the real ZIP entry
points now invoke after checking SHA-256.
"""
from __future__ import annotations

import unittest

import pandas as pd

from scripts.data_rebuild import compare_nba_cup_exact_source_rows as join
from scripts.data_rebuild import verify_official_nba_cup_first_release_fixtures as group
from scripts.data_rebuild import verify_official_nba_cup_knockout_original_fixtures as ko


class SourceExactRowMatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.group=group.load_source(group.DEFAULT_SOURCE)
        cls.knockouts=ko.load(ko.SOURCE)

    def synthetic_group_original(self):
        return self.group.loc[:,list(join.MATCH)].copy().assign(cup_stage="group_play")

    def synthetic_network_pdf(self):
        # Includes 2400 source rows in the REAL original frozen release,
        # but this is a synthetic minimal fixture PDF for a join test.
        return self.group.loc[:,list(join.TV)].copy()

    def synthetic_knockout_original(self):
        frame=self.knockouts.loc[:,[
            "season","game_date_et","cup_stage","away_team","home_team",
            "participant_1","participant_2"
        ]].copy()
        # The "home" team for neutral games is arbitrary and is intentionally
        # NOT validated by the scientific comparator.
        semis=frame.cup_stage.eq("semifinal")
        frame.loc[semis,"away_team"]=frame.loc[semis,"participant_1"]
        frame.loc[semis,"home_team"]=frame.loc[semis,"participant_2"]
        return frame.loc[:,["season","game_date_et","cup_stage","away_team","home_team"]]

    def test_positive_120_group_source_to_synthetic_original(self):
        result=join.exact_group_fixture_join(self.group,self.synthetic_group_original(),120)
        self.assertEqual(result["source_fixture_exact"],120)
        self.assertTrue(result["exact_full_match"])

    def test_positive_120_network_tuples_to_synthetic_original_PDF(self):
        r=join.exact_first_release_network_join(
            self.group,self.synthetic_network_pdf(),120)
        self.assertEqual(r["exact_NBA_source_network_rows"],120)
        self.assertTrue(r["blank_vs_national_network_strictly_distinguished"])

    def test_negative_one_original_Cup_game_wrong_host(self):
        original=self.synthetic_group_original()
        original.loc[0,"home_team"]="Toronto Raptors"
        with self.assertRaisesRegex(ValueError,"date/away/home group mismatch"):
            join.exact_group_fixture_join(self.group,original,120)

    def test_negative_one_original_Cup_game_wrong_date(self):
        original=self.synthetic_group_original()
        original.loc[0,"game_date_et"]="2023-11-04"
        with self.assertRaisesRegex(ValueError,"date/away/home group mismatch"):
            join.exact_group_fixture_join(self.group,original,120)

    def test_negative_one_original_Cup_game_missing_even_with_same_size(self):
        original=self.synthetic_group_original()
        original.loc[0, list(join.MATCH)]=original.loc[1,list(join.MATCH)].to_list()
        with self.assertRaisesRegex(ValueError,"duplicated"):
            join.exact_group_fixture_join(self.group,original,120)

    def test_negative_network_label_wrong_but_game_identity_correct(self):
        pdf=self.synthetic_network_pdf()
        index=self.group[self.group.first_release_network.eq("ESPN")].index[0]
        pdf.loc[index,"first_release_network"]="TNT"
        with self.assertRaisesRegex(ValueError,"TV mismatch"):
            join.exact_first_release_network_join(self.group,pdf,120)

    def test_negative_swap_two_broadcasts_preserving_aggregate_counts(self):
        pdf=self.synthetic_network_pdf()
        a=self.group[self.group.first_release_network.eq("ESPN")].index[0]
        b=self.group[self.group.first_release_network.eq("TNT")].index[0]
        pdf.loc[a,"first_release_network"]="TNT"
        pdf.loc[b,"first_release_network"]="ESPN"
        self.assertEqual(self.group.first_release_network.value_counts().to_dict(),
                         pdf.first_release_network.value_counts().to_dict())
        with self.assertRaisesRegex(ValueError,"TV mismatch"):
            join.exact_first_release_network_join(self.group,pdf,120)

    def test_negative_blank_means_unknown_not_a_verified_network(self):
        pdf=self.synthetic_network_pdf()
        index=self.group[self.group.first_release_network.eq("")].index[0]
        pdf.loc[index,"first_release_network"]="NBA TV"
        with self.assertRaisesRegex(ValueError,"TV mismatch"):
            join.exact_first_release_network_join(self.group,pdf,120)

    def test_negative_PDF_duplicate_exact_game_not_ignored(self):
        pdf=self.synthetic_network_pdf()
        pdf.loc[0,list(join.MATCH)]=pdf.loc[1,list(join.MATCH)].to_list()
        with self.assertRaisesRegex(ValueError,"duplicated"):
            join.exact_first_release_network_join(self.group,pdf,120)

    def test_positive_18_knockout_original_rows_with_nominal_home_semis(self):
        result=join.exact_knockout_fixture_join(
            self.knockouts,self.synthetic_knockout_original())
        self.assertEqual(result["original_knockout_stage_date_unordered_pair_rows_exact"],18)
        self.assertEqual(result["original_quarterfinal_ordered_home_away_rows_exact"],12)
        self.assertFalse(result["neutral_semifinal_nominal_home_team_verified"])

    def test_negative_knockout_one_wrong_opponent_same_season(self):
        original=self.synthetic_knockout_original()
        original.loc[0,"away_team"]="Dallas Mavericks"
        with self.assertRaisesRegex(ValueError,"date/stage/unordered"):
            join.exact_knockout_fixture_join(self.knockouts,original)

    def test_negative_knockout_one_wrong_game_date(self):
        original=self.synthetic_knockout_original()
        original.loc[0,"game_date_et"]="2023-12-05"
        with self.assertRaisesRegex(ValueError,"date/stage/unordered"):
            join.exact_knockout_fixture_join(self.knockouts,original)

    def test_negative_knockout_wrong_stage(self):
        original=self.synthetic_knockout_original()
        original.loc[0,"cup_stage"]="semifinal"
        with self.assertRaisesRegex(ValueError,"date/stage/unordered"):
            join.exact_knockout_fixture_join(self.knockouts,original)

    def test_negative_quarterfinal_home_away_reverse_is_rejected(self):
        original=self.synthetic_knockout_original()
        row=original.loc[0,["away_team","home_team"]].to_list()
        original.loc[0,["away_team","home_team"]]=list(reversed(row))
        with self.assertRaisesRegex(ValueError,"ordered home/away"):
            join.exact_knockout_fixture_join(self.knockouts,original)

    def test_neutral_semi_nominal_home_swap_stays_explicitly_unverified(self):
        original=self.synthetic_knockout_original()
        i=original[original.cup_stage.eq("semifinal")].index[0]
        row=original.loc[i,["away_team","home_team"]].to_list()
        original.loc[i,["away_team","home_team"]]=list(reversed(row))
        r=join.exact_knockout_fixture_join(self.knockouts,original)
        self.assertFalse(r["neutral_semifinal_nominal_home_team_verified"])

    def test_negative_knockout_duplicate_even_if_counterfactual_slot_copied(self):
        original=self.synthetic_knockout_original()
        original.loc[1,list(join.KNOCKOUT)+["away_team","home_team"]]=(
            original.loc[0,list(join.KNOCKOUT)+["away_team","home_team"]].to_list())
        with self.assertRaisesRegex(ValueError,"duplicate"):
            join.exact_knockout_fixture_join(self.knockouts,original)

    def test_negative_missing_source_or_archive_columns(self):
        original=self.synthetic_group_original().drop(columns=["home_team"])
        with self.assertRaisesRegex(ValueError,"missing required columns"):
            join.exact_group_fixture_join(self.group,original,120)


if __name__ == "__main__":
    unittest.main()
