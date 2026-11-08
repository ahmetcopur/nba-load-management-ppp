"""Offline invariant tests for the fixture-date / covariate sensitivity."""
import importlib.util
from pathlib import Path
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/data_rebuild/audit_fixture_date_swap_covariates.py"
spec = importlib.util.spec_from_file_location("nba_fixture_covariate_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class CovariateDiffTests(unittest.TestCase):
    def make_rows(self):
        return pd.DataFrame([
            {"game_id": "g1", "team": "A", "rest_days_between_games": 2,
             "back_to_back": False, "team_elo_pre": 1550.0,
             "previous_tip_utc": pd.NaT, "back_to_back_type": ""},
            {"game_id": "g2", "team": "A", "rest_days_between_games": 1,
             "back_to_back": False, "team_elo_pre": 1550.0,
             "previous_tip_utc": pd.Timestamp("2022-02-01T00:30:00Z"),
             "back_to_back_type": ""},
        ])

    def test_identical_tables(self):
        rows = self.make_rows()
        counts, magnitudes, examples = audit.compare_rows(rows, rows.copy())
        self.assertFalse(counts)
        self.assertFalse(examples)
        self.assertEqual(magnitudes["team_elo_pre"]["max_absolute_difference"], 0.0)

    def test_nearzero_numeric_drift_does_not_create_false_positive(self):
        left = self.make_rows()
        right = left.copy()
        right.loc[1, "team_elo_pre"] += 1e-10
        counts, _, _ = audit.compare_rows(left, right)
        self.assertFalse(counts)

    def test_material_schedule_and_rating_differences_detected(self):
        left = self.make_rows()
        right = left.copy()
        right.loc[1, "back_to_back"] = True
        right.loc[1, "team_elo_pre"] += 13.6
        right.loc[1, "rest_days_between_games"] = 2
        counts, magnitudes, _ = audit.compare_rows(left, right)
        self.assertEqual(counts["team_elo_pre"], 1)
        self.assertEqual(counts["rest_days_between_games"], 1)
        self.assertEqual(counts["back_to_back"], 1)
        self.assertGreater(magnitudes["team_elo_pre"]["max_absolute_difference"], 13)

    def test_missing_datetime_and_empty_text_are_equivalent(self):
        a = self.make_rows()
        b = a.copy()
        b["previous_tip_utc"] = b["previous_tip_utc"].astype(str).replace({"NaT": ""})
        b["back_to_back_type"] = None
        counts, _, _ = audit.compare_rows(a, b)
        self.assertFalse(counts)

    def test_duplicate_team_game_keys_rejected(self):
        a = self.make_rows()
        b = pd.concat([a, a.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "Duplicate team-game"):
            audit.compare_rows(a, b)

    def test_only_two_predefined_historical_fixtures_corrected(self):
        self.assertEqual(len(audit.CORRECTED_TIP_UTC), 2)
        self.assertEqual(set(audit.CORRECTED_TIP_UTC.values()),
                         {"2022-02-04T00:30:00Z", "2022-02-02T00:30:00Z"})


if __name__ == "__main__":
    unittest.main()
