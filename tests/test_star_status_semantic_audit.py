import unittest
import pandas as pd
from scripts.data_rebuild.audit_star_status_against_calendar import evaluate


class StarSemanticAuditTests(unittest.TestCase):
    def frames(self, opening=False, selected=False, actual=False, date='2025-03-01'):
        panel = pd.DataFrame([{'season': '2024-25', 'nba_player_id': 1,
            'player_team_game_id': 'fixture|team|1', 'game_date_et': date,
            'star_PPP_it': actual, 'from_boxscore_roster': False,
            'at_risk_for_new_onset_harm': True, 'absence_onset_harm': True}])
        calendar = pd.DataFrame([{'season': '2024-25', 'nba_player_id': 1,
            'star_at_opening_night': opening, 'current_season_all_star': selected,
            'current_all_star_effective_date': '2025-02-17'}])
        return panel, calendar

    def test_nonstar_cannot_become_star_merely_because_break_has_passed(self):
        p, c = self.frames(actual=True)
        r = evaluate(p, c)
        self.assertEqual(r['status'], 'FAIL_DECLARED_STAR_DEFINITION')
        self.assertEqual(r['mismatched_report_only_rows'], 1)
        self.assertEqual(r['mismatched_at_risk_rows'], 1)
        self.assertTrue(p.star_PPP_it.iloc[0])  # Audit never patches the panel.

    def test_opening_star_and_actual_new_allstar_are_valid(self):
        for opening, selected in [(True, False), (False, True), (True, True)]:
            p, c = self.frames(opening=opening, selected=selected, actual=True)
            self.assertEqual(evaluate(p, c)['status'], 'pass')

    def test_future_allstar_selection_cannot_label_pre_effective_games(self):
        p, c = self.frames(selected=True, actual=True, date='2025-02-01')
        self.assertEqual(evaluate(p, c)['mismatched_rows'], 1)
        p.star_PPP_it = False
        self.assertEqual(evaluate(p, c)['status'], 'pass')

    def test_missing_or_duplicate_calendar_must_not_default_to_nonstar(self):
        p, c = self.frames()
        for bad in [c.iloc[:0], pd.concat([c, c])]:
            with self.assertRaisesRegex(ValueError, 'cover|unique'):
                evaluate(p, bad)

    def test_invalid_boolean_and_missing_selected_date_are_blocking(self):
        p, c = self.frames()
        c.current_season_all_star = 'unknown'
        with self.assertRaisesRegex(ValueError, 'boolean'):
            evaluate(p, c)
        p, c = self.frames(selected=True)
        c.current_all_star_effective_date = None
        with self.assertRaisesRegex(ValueError, 'effective date'):
            evaluate(p, c)
