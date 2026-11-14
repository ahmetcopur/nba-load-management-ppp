"""Strict source-only NBA Cup 18 actual knockout fixture and TV checks."""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from scripts.data_rebuild import verify_official_nba_cup_knockout_original_fixtures as knockout


class NBAActualKnockoutSourceTests(unittest.TestCase):
    def setUp(self):
        self.original=knockout.load(knockout.SOURCE)

    def test_all_18_source_nba_games_exact(self):
        r=knockout.validate_original_source(self.original)
        self.assertEqual(r["official_original_QF_game_date_away_home_exact_public"],12)
        self.assertEqual(r["official_original_neutral_semifinal_date_unordered_pair_exact_public"],6)
        self.assertEqual(r["official_original_realized_knockout_networks_sourced"],18)
        self.assertEqual(len(r["seasons"]),3)

    def test_six_neutral_semis_are_not_claimed_home_away_validated(self):
        r=knockout.validate_original_source(self.original)
        self.assertFalse(r["neutral_semifinal_nominal_home_team_independently_proven"])
        self.assertFalse(r["original_private_Cup_game_lookup_actual_reconciliation_run"])
        semi=self.original[self.original.cup_stage.eq("semifinal")]
        self.assertEqual(len(semi),6)
        self.assertTrue((semi.home_team=="").all() and (semi.away_team=="").all())

    def test_cup_championship_excluded(self):
        r=knockout.validate_original_source(self.original)
        self.assertTrue(r["all_three_championships_intentionally_excluded"])
        self.assertNotIn("championship",set(self.original.cup_stage))

    def test_missing_knockout_game_fails(self):
        with self.assertRaisesRegex(ValueError,"18 games incomplete"):
            knockout.validate_original_source(self.original.iloc[:-1])

    def test_wrong_quarterfinal_home_away_reversed_fails(self):
        wrong=self.original.copy()
        wrong.loc[0,["away_team","home_team"]]=wrong.loc[0,["home_team","away_team"]].tolist()
        with self.assertRaisesRegex(ValueError,"one or more source-identical"):
            knockout.validate_original_source(wrong)

    def test_wrong_semifinal_winner_fails(self):
        wrong=self.original.copy()
        i=wrong[wrong.cup_stage.eq("semifinal")].index[0]
        wrong.loc[i,"winner"]=wrong.loc[i,"participant_2"]
        with self.assertRaisesRegex(ValueError,"one or more source-identical"):
            knockout.validate_original_source(wrong)

    def test_wrong_2025_network_fails(self):
        wrong=self.original.copy()
        i=wrong[wrong.season.eq("2025-26")].index[0]
        wrong.loc[i,"game_network"]="ESPN"
        with self.assertRaisesRegex(ValueError,"one or more source-identical"):
            knockout.validate_original_source(wrong)

    def test_semifinal_home_team_cannot_be_inferred(self):
        wrong=self.original.copy()
        i=wrong[wrong.cup_stage.eq("semifinal")].index[0]
        wrong.loc[i,"home_team"]=wrong.loc[i,"winner"]
        with self.assertRaisesRegex(ValueError,"one or more source-identical"):
            knockout.validate_original_source(wrong)

    def test_premature_announcement_date_or_uncorroborated_source_rejected(self):
        wrong=self.original.copy()
        wrong.loc[0,"fixture_provider_documented_by_date"]="2023-12-20"
        with self.assertRaisesRegex(ValueError,"AFTER game"):
            knockout.validate_original_source(wrong)

        wrong=self.original.copy()
        wrong.loc[0,"fixture_provider_source_url"]="https://example.org/"
        with self.assertRaisesRegex(ValueError,"not official NBA.com"):
            knockout.validate_original_source(wrong)

    def test_original_private_archive_tampering_fails_before_lookup(self):
        with tempfile.TemporaryDirectory() as d:
            archive=Path(d)/"fake-private-original-cup.zip"
            archive.write_bytes(b"not the original historical full Cup ZIP")
            with self.assertRaisesRegex(ValueError,"full SHA-256 mismatch"):
                knockout.compare_original_private(self.original,archive)


if __name__=="__main__":
    unittest.main()
