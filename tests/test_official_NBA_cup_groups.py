"""Synthetic full-round-robin checks against official 2023–25 NBA Cup groups.

Never upload source ZIPs or individual NBA injury reports to public CI.
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from scripts.data_rebuild import verify_official_NBA_cup_groups as m


def synthetic_season(season: str) -> pd.DataFrame:
    rows = []
    dates = {round_: value.split("|") for round_, value in m.DATES[season].items()}

    def add(stage, away, home, day):
        rows.append({
            "cup_stage": stage, "away_team": away, "home_team": home,
            "game_date_et": day, "cup_game": True,
            "cup_group_play": stage == "group_play",
            "cup_quarterfinal": stage == "quarterfinal",
            "cup_semifinal": stage == "semifinal",
            "cup_knockout": stage in ("quarterfinal", "semifinal"),
        })

    for group, team_list in m.GROUPS[season].items():
        teams = team_list.split("|")
        for k, (i, j) in enumerate(combinations(range(5), 2)):
            # Orient the complete K5 group matchups as a balanced tournament.
            # Each team has exactly 2 home games and 2 away games.
            if (j - i) % 5 in (1, 2):
                home, away = teams[i], teams[j]
            else:
                home, away = teams[j], teams[i]
            add("group_play", away, home,
                dates["group_play"][len(rows) % len(dates["group_play"])])
    knockout_days = dates["quarterfinal"]
    for i in range(4):
        add("quarterfinal", f"Away {i}", f"Home {i}", knockout_days[i // 2])
    for i in range(2):
        add("semifinal", f"Semifinal Away {i}", f"Semifinal Home {i}",
            dates["semifinal"][0])
    return pd.DataFrame(rows)


class OriginalOfficialCupSourceCheckTests(unittest.TestCase):
    def test_all_three_official_original_season_calendars_and_group_draws(self):
        for season in m.GROUPS:
            with self.subTest(season=season):
                check = m.check_season(season, synthetic_season(season))
                self.assertEqual(check["original_unique_unordered_group_fixture_pairs_checked"], 60)
                self.assertEqual(check["original_quarterfinal_games_on_official_dates"], 4)
                self.assertTrue(check["all_30_teams_exactly_4_group_games_and_2_home_2_away"])

    def test_an_original_cup_fixture_on_wrong_night_fails(self):
        records = synthetic_season("2025-26")
        records.loc[0, "game_date_et"] = "2025-11-06"
        with self.assertRaisesRegex(ValueError, "dates not official"):
            m.check_season("2025-26", records)

    def test_group_game_between_wrong_official_NBA_groups_fails(self):
        season = "2024-25"
        records = synthetic_season(season)
        records.loc[0, "away_team"] = m.GROUPS[season]["WB"].split("|")[0]
        with self.assertRaisesRegex(ValueError, "not in same official original NBA group"):
            m.check_season(season, records)

    def test_extra_game_after_sixty_plus_six_fails(self):
        r = synthetic_season("2023-24")
        r = pd.concat([r, r.iloc[:1]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "not 66"):
            m.check_season("2023-24", r)

    def test_missing_one_official_opponent_fixture_fails(self):
        season = "2025-26"
        r = synthetic_season(season)
        r.loc[1, ["home_team", "away_team"]] = r.loc[0, ["home_team", "away_team"]].to_numpy()
        with self.assertRaises(ValueError):
            m.check_season(season, r)

    def test_group_team_with_three_home_one_away_is_rejected(self):
        season = "2023-24"
        r = synthetic_season(season)
        r.loc[0, ["home_team", "away_team"]] = r.loc[0, ["away_team", "home_team"]].to_numpy()
        with self.assertRaisesRegex(ValueError, "2 home"):
            m.check_season(season, r)

    def test_wrong_knockout_stage_boolean_fails(self):
        season = "2024-25"
        r = synthetic_season(season)
        r.loc[r.cup_stage.eq("semifinal"), "cup_knockout"] = False
        with self.assertRaisesRegex(ValueError, "knockout flag"):
            m.check_season(season, r)

    def test_non_official_quarterfinal_date_fails(self):
        season = "2023-24"
        r = synthetic_season(season)
        r.loc[r.cup_stage.eq("quarterfinal"), "game_date_et"] = "2023-12-06"
        with self.assertRaisesRegex(ValueError, "dates not official"):
            m.check_season(season, r)

    def test_archive_missing_does_not_generate_fake_official_reconstruction(self):
        with self.assertRaises(FileNotFoundError):
            m.verify_original_cup_lookup(Path("/tmp/nba-not-a-real-source.zip"))

    def test_original_group_announcements_are_distinct_2023_2024_2025(self):
        self.assertEqual(len(m.OFFICIAL_NBA), 3)
        self.assertNotEqual(m.GROUPS["2023-24"]["WA"], m.GROUPS["2024-25"]["WA"])
        self.assertNotEqual(m.GROUPS["2024-25"]["WA"], m.GROUPS["2025-26"]["WA"])
        self.assertTrue(all(v["groups"].startswith("https://www.nba.com/news/")
                            for v in m.OFFICIAL_NBA.values()))


if __name__ == "__main__":
    unittest.main()
