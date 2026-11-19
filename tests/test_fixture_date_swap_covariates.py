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

# Import the model wrapper via its real location; no full private archives needed.
import sys
sys.path.insert(0, str(SCRIPT.parent))
MODEL_SCRIPT = ROOT / "scripts/data_rebuild/run_fixture_date_control_sensitivity.py"
model_spec = importlib.util.spec_from_file_location("nba_fixture_control_model", MODEL_SCRIPT)
model = importlib.util.module_from_spec(model_spec)
model_spec.loader.exec_module(model)


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



class FixedOutcomeModelSensitivityTests(unittest.TestCase):
    def make_panel_and_controls(self):
        keys = [
            ("g1", "A", "g1|A|p1", True),
            ("g2", "A", "g2|A|p1", False),
            ("g2", "B", "g2|B|p2", True),
        ]
        panel = pd.DataFrame([{
            "game_id": game, "team": team,
            "player_team_game_id": pid,
            "absence_onset_harm": onset, "absence_now_harm": onset,
            "at_risk_for_new_onset_harm": True,
            "star_PPP_it": True, "announced_tv_primary": False,
            "tv_harmonized_linear": False, "postPPP": False,
            "games_played_before_game_harm": 1,
            "minutes_sum_prior_10_roster_games_harm": 20,
            "dist_to_65_before_game_harm": 64,
            "snapshot_basename": "s1.pdf", "snapshot_timestamp_utc": "2022-01-01Z",
            **{name: 2.0 for name in model.MODEL_COLUMNS_TO_UPDATE},
        } for game,team,pid,onset in keys])
        historical = panel[model.KEY + model.MODEL_COLUMNS_TO_UPDATE].drop_duplicates(model.KEY)
        corrected = historical.copy()
        corrected.loc[corrected.game_id.eq("g2") & corrected.team.eq("A"), "signed_elo_advantage"] = 15.6
        return panel,historical,corrected

    def test_control_only_replacement_keeps_every_frozen_outcome_and_key(self):
        panel, historical, corrected = self.make_panel_and_controls()
        changed, counts = model.compare_baseline_and_replace(panel,historical,corrected)
        self.assertEqual(counts["signed_elo_advantage"]["changed_player_game_rows"],1)
        self.assertEqual(counts["signed_elo_advantage"]["changed_games"],1)
        self.assertEqual(changed.signed_elo_advantage.tolist(),[2.0,15.6,2.0])
        self.assertEqual(changed.absence_onset_harm.tolist(),panel.absence_onset_harm.tolist())
        self.assertEqual(changed.player_team_game_id.tolist(),panel.player_team_game_id.tolist())

    def test_source_disagreement_fails_before_any_control_replacement(self):
        panel,historical,corrected = self.make_panel_and_controls()
        historical.loc[0,"back_to_back"] = 3.0
        with self.assertRaisesRegex(RuntimeError,"differs from frozen panel"):
            model.compare_baseline_and_replace(panel,historical,corrected)

if __name__ == "__main__":
    unittest.main()
