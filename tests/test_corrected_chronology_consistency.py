"""Synthetic tests for the six-season chronology and identity audit."""
import importlib.util
from pathlib import Path
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "chron", ROOT / "scripts/data_rebuild/audit_corrected_chronology_consistency.py")
chron = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chron)


def games(rows):
    """rows: (game_id, team, opponent, date, tip, number, rest, b2b)."""
    frame = pd.DataFrame(rows, columns=["game_id", "team", "opponent", "game_date_et",
                                        "tip_utc", "team_game_number",
                                        "rest_days_between_games", "back_to_back"])
    frame["season"] = "2021-22"
    frame["tip"] = pd.to_datetime(frame.tip_utc, utc=True)
    return frame


def schedule(chi_date="2022-02-03", chi_tip="2022-02-04 00:30:00+00:00"):
    g1 = "2021-22|20220202T0030Z|Chicago Bulls@Toronto Raptors"
    g2 = "2021-22|20220202T0100Z|Orlando Magic@Chicago Bulls"
    return games([
        (g2, "Chicago Bulls", "Orlando Magic", "2022-02-01", "2022-02-02 01:00:00+00:00", "1", "", "False"),
        (g2, "Orlando Magic", "Chicago Bulls", "2022-02-01", "2022-02-02 01:00:00+00:00", "1", "", "False"),
        (g1, "Chicago Bulls", "Toronto Raptors", chi_date, chi_tip, "2",
         "1" if chi_date == "2022-02-03" else "-1", "False"),
        (g1, "Toronto Raptors", "Chicago Bulls", chi_date, chi_tip, "1", "", "False"),
    ])


class PanelCheckTests(unittest.TestCase):
    def test_clean_schedule_passes(self):
        report = chron.panel_checks(schedule(), 0)
        for key in ("duplicate_team_dates", "unmirrored_team_games",
                    "et_date_not_equal_tip_date", "team_game_number_out_of_tip_order",
                    "rest_days_arithmetic_mismatches", "back_to_back_not_rest_zero"):
            self.assertEqual(report[key], 0, key)

    def test_team_playing_twice_on_one_date_is_flagged(self):
        bad = schedule("2022-02-01", "2022-02-02 00:30:00+00:00")
        report = chron.panel_checks(bad, 0)
        self.assertEqual(report["duplicate_team_dates"], 1)
        self.assertGreater(report["team_game_number_out_of_tip_order"], 0)

    def test_et_date_must_follow_utc_tip(self):
        bad = schedule(chi_tip="2022-02-03 00:30:00+00:00")
        self.assertEqual(chron.panel_checks(bad, 0)["et_date_not_equal_tip_date"], 2)

    def test_unmirrored_game_flagged(self):
        bad = schedule()
        bad.loc[3, "opponent"] = "Miami Heat"
        self.assertGreater(chron.panel_checks(bad, 0)["unmirrored_team_games"], 0)


class MovedGameTests(unittest.TestCase):
    def test_moved_games_listed_and_unrelated_moves_detected(self):
        frozen = schedule("2022-02-01", "2022-02-02 00:30:00+00:00")
        corrected = schedule()
        moved = chron.moved_games(frozen, corrected)
        self.assertEqual(list(moved["games_with_moved_date_or_tip"]),
                         ["2021-22|20220202T0030Z|Chicago Bulls@Toronto Raptors"])
        corrected.loc[corrected.team.eq("Orlando Magic"), "tip_utc"] = "2022-02-02 02:00:00+00:00"
        corrected.loc[corrected.team.eq("Chicago Bulls") & corrected.opponent.eq("Orlando Magic"),
                      "tip_utc"] = "2022-02-02 02:00:00+00:00"
        self.assertEqual(len(chron.moved_games(frozen, corrected)
                             ["games_with_moved_date_or_tip"]), 2)

    def test_dropped_game_reported(self):
        frozen = schedule()
        corrected = frozen[~frozen.game_id.str.contains("Orlando")]
        self.assertEqual(len(chron.moved_games(frozen, corrected)["games_only_in_frozen"]), 1)


if __name__ == "__main__":
    unittest.main()
