"""No private inputs: 2021–23 source-selector verifier failure-mode tests."""
from __future__ import annotations
import unittest

import pandas as pd

from scripts.data_rebuild.verify_2021_2023_selector_rebuild import (
    normalized_frame_equal, submitted_precedence, source_snapshot_counts,
)


def norm_team(value):
    return str(value).lower().strip()


class HistoricalSelectorSourceTests(unittest.TestCase):
    def test_source_submitted_overrides_mixed_placeholder_only(self):
        teams = pd.DataFrame([
            {"game_id": "G1", "snapshot_basename": "a.pdf",
             "matchup_norm": "AAA@BBB", "team_norm": "alpha",
             "team_final_status": "not_yet_submitted", "usable_submitted_status": False},
            {"game_id": "G1", "snapshot_basename": "a.pdf",
             "matchup_norm": "AAA@BBB", "team_norm": "beta",
             "team_final_status": "not_yet_submitted", "usable_submitted_status": False},
        ])
        raw = pd.DataFrame([
            {"source_file": "somewhere/a.pdf", "matchup_norm": "AAA@BBB",
             "team": "Alpha", "team_submission_status": "submitted"},
            {"source_file": "somewhere/a.pdf", "matchup_norm": "AAA@BBB",
             "team": "Alpha", "team_submission_status": "not_yet_submitted"},
            {"source_file": "somewhere/a.pdf", "matchup_norm": "AAA@BBB",
             "team": "Beta", "team_submission_status": "not_yet_submitted"},
        ])
        changed = submitted_precedence(teams, raw, norm_team)
        self.assertEqual(changed, ["G1"])
        self.assertTrue(bool(teams.iloc[0].usable_submitted_status))
        self.assertEqual(teams.iloc[0].team_final_status, "submitted_with_listed_players")
        self.assertFalse(bool(teams.iloc[1].usable_submitted_status))

    def test_other_matchup_cannot_override_missing_team(self):
        team = pd.DataFrame([{"game_id": "G1", "snapshot_basename": "a.pdf",
            "matchup_norm": "AAA@BBB", "team_norm": "alpha",
            "team_final_status": "not_yet_submitted", "usable_submitted_status": False}])
        raw = pd.DataFrame([{"source_file": "a.pdf", "matchup_norm": "AAA@CCC",
             "team": "alpha", "team_submission_status": "submitted"}])
        self.assertEqual(submitted_precedence(team, raw, norm_team), [])
        self.assertFalse(bool(team.iloc[0].usable_submitted_status))

    def test_strict_schema_rejects_missing_metadata_column(self):
        original = pd.DataFrame({"game_id": ["G1"], "report": ["abc"], "metadata": [1]})
        with self.assertRaisesRegex(ValueError, "Frozen output schema changed"):
            normalized_frame_equal(original.drop(columns=["metadata"]),
                                   original, ["game_id"], strict_schema=True)

    def test_all_game_columns_match_order_independently(self):
        ref = pd.DataFrame({"game_id": ["G1", "G2"],
                            "tip_timestamp_utc": ["2023-01-01T20:00:00+00:00",
                                                  "2023-01-02T20:00:00+00:00"],
                            "metric": [1, 2]})
        cand = ref.iloc[::-1].copy()
        cand["tip_timestamp_utc"] = pd.to_datetime(cand.tip_timestamp_utc, utc=True).astype(str)
        self.assertEqual(normalized_frame_equal(cand, ref, ["game_id"],
                         strict_schema=True)["differences"], 0)

    def test_wrong_team_status_fails(self):
        ref = pd.DataFrame({"game_id": ["G1"], "team_role": ["away"],
                            "team_final_status": ["submitted"]})
        cand = ref.copy()
        cand.loc[0, "team_final_status"] = "not_yet_submitted"
        with self.assertRaisesRegex(ValueError, "selector differs"):
            normalized_frame_equal(cand, ref, ["game_id", "team_role"], strict_schema=False)

    def test_duplicate_identity_fails(self):
        ref = pd.DataFrame({"game_id": ["G1", "G2"], "status": ["a", "b"]})
        cand = ref.copy()
        cand.loc[1, "game_id"] = "G1"
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            normalized_frame_equal(cand, ref, ["game_id"], strict_schema=True)

    def test_repeated_same_matchup_other_date_is_excluded(self):
        rows = pd.DataFrame([
            {"matchup_norm": "AAA@BBB", "game_date_raw": "11/01/2022",
             "source_file": "report_01PM.pdf",
             "snapshot_timestamp_utc": "2022-11-01T17:30:00+00:00"},
            {"matchup_norm": "AAA@BBB", "game_date_raw": "11/01/2022",
             "source_file": "report_05PM.pdf",
             "snapshot_timestamp_utc": "2022-11-01T21:30:00+00:00"},
            {"matchup_norm": "AAA@BBB", "game_date_raw": "02/01/2023",
             "source_file": "next_01PM.pdf",
             "snapshot_timestamp_utc": "2023-02-01T17:30:00+00:00"},
        ])
        games = pd.DataFrame([{
            "game_id": "G1", "matchup_norm": "AAA@BBB",
            "game_date_et": "2022-11-01",
            "tip_timestamp_utc": "2022-11-01T20:00:00+00:00",
        }])
        all_counts, before, fallbacks = source_snapshot_counts(
            rows, pd.DataFrame(), "2022-23", "full", games)
        self.assertEqual((all_counts, before, fallbacks), ([2], [1], []))
        harm, pre, _ = source_snapshot_counts(rows, pd.DataFrame(),
                                              "2022-23", "harmonized", games)
        self.assertEqual((harm, pre), ([2], [1]))

    def test_missing_matchup_fails_for_undocumented_game(self):
        rows = pd.DataFrame([{"matchup_norm": "CCC@DDD", "game_date_raw": "10/25/2023",
               "source_file": "a_01PM.pdf",
               "snapshot_timestamp_utc": "2023-10-25T17:30:00+00:00"}])
        games = pd.DataFrame([{"game_id": "G_OTHER", "matchup_norm": "AAA@BBB",
              "game_date_et": "2023-10-25",
              "tip_timestamp_utc": "2023-10-25T23:00:00+00:00"}])
        with self.assertRaisesRegex(ValueError, "Undocumented no-matchup"):
            source_snapshot_counts(rows, pd.DataFrame(),
                                   "2023-24", "full", games)

    def test_known_2023_clean_game_fallback_is_derived_from_manifest(self):
        rows = pd.DataFrame([{"matchup_norm": "CCC@DDD", "game_date_raw": "10/25/2023",
             "source_file": "z_01PM.pdf",
             "snapshot_timestamp_utc": "2023-10-25T17:30:00+00:00"}])
        manifest = pd.DataFrame([
            {"exists": True, "report_date": "2023-10-24", "url_token": "05PM",
             "published_timestamp_utc": "2023-10-24T21:30:00+00:00"},
            {"exists": True, "report_date": "2023-10-25", "url_token": "01PM",
             "published_timestamp_utc": "2023-10-25T17:30:00+00:00"},
            {"exists": True, "report_date": "2023-10-25", "url_token": "08PM",
             "published_timestamp_utc": "2023-10-26T00:30:00+00:00"},
        ])
        games = pd.DataFrame([{"game_id": "FD2023_5", "matchup_norm": "BOS@NYK",
              "game_date_et": "2023-10-25",
              "tip_timestamp_utc": "2023-10-25T23:00:00+00:00"}])
        all_, pre, missing = source_snapshot_counts(rows, manifest,
                                        "2023-24", "full", games)
        self.assertEqual((all_, pre, missing), ([3], [2], ["FD2023_5"]))
        harm, hpre, missing = source_snapshot_counts(rows, manifest,
                                  "2023-24", "harmonized", games)
        self.assertEqual((harm, hpre, missing), ([3], [2], ["FD2023_5"]))


if __name__ == "__main__":
    unittest.main()
