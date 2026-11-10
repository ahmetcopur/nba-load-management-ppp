"""Synthetic tests of reproducible Cup lookup transformation and original ZIP guards."""
from __future__ import annotations
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

import pandas as pd

from scripts.data_rebuild.run_connected_cup_enrichment import (
    CUP_ARCHIVE, CUP_PREFIX, add_cup_flags, add_cup_to_spells,
    check_private_run, compare_original_cup_output, original_lookup,
)
from scripts.data_rebuild.reproduce_core_and_stars import reproduce


class CupLookupStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archives = self.root / "source"
        self.work = self.root / "work"
        self.archives.mkdir()
        self.work.mkdir()
        self.lookup = pd.DataFrame([
            dict(game_id="g0", season="2022-23", game_date_et="2023-01-01",
                 cup_stage="none", cup_game=False,
                 cup_group_play=False, cup_quarterfinal=False,
                 cup_semifinal=False, cup_knockout=False),
            dict(game_id="g1", season="2023-24", game_date_et="2023-11-01",
                 cup_stage="group_play", cup_game=True,
                 cup_group_play=True, cup_quarterfinal=False,
                 cup_semifinal=False, cup_knockout=False),
            dict(game_id="g2", season="2023-24", game_date_et="2023-12-01",
                 cup_stage="quarterfinal", cup_game=True,
                 cup_group_play=False, cup_quarterfinal=True,
                 cup_semifinal=False, cup_knockout=True),
        ])
        self.source = pd.DataFrame([
            dict(game_id="g0", team="T0", nba_player_id=1,
                 star_PPP_it=True, postPPP=False,
                 announced_tv_primary=True, cup_game_pending=True),
            dict(game_id="g1", team="T1", nba_player_id=2,
                 star_PPP_it=True, postPPP=True,
                 announced_tv_primary=True, cup_game_pending=True),
            dict(game_id="g2", team="T2", nba_player_id=3,
                 star_PPP_it=False, postPPP=True,
                 announced_tv_primary=False, cup_game_pending=True),
        ])

    def test_new_flag_columns_and_interactions_are_derived_from_lookup(self):
        result = add_cup_flags(self.source, self.lookup)
        self.assertEqual(len(result), 3)
        self.assertTrue(result.cup_game_pending.eq(False).all())
        self.assertEqual(result.cup_round_order.to_list(), [0, 1, 2])
        self.assertEqual(result.star_postPPP.to_list(), [False, True, False])
        self.assertEqual(result.star_postPPP_announcedTV.to_list(), [False, True, False])
        self.assertEqual(result.star_cup_game.to_list(), [False, True, False])
        self.assertEqual(result.star_postPPP_cup_game.to_list(), [False, True, False])
        self.assertTrue(result.cup_flag_version.eq("official_dates_v1").all())

    def test_composite_player_team_game_identity_keeps_two_teams_distinct(self):
        rows = pd.concat([self.source.iloc[[0]], self.source.iloc[[0]]], ignore_index=True)
        rows.loc[1, "team"] = "Another Team"
        result = add_cup_flags(rows, self.lookup)
        self.assertTrue(result.player_team_game_id.is_unique)
        self.assertNotEqual(result.player_team_game_id.iloc[0], result.player_team_game_id.iloc[1])

    def test_duplicate_same_player_team_game_is_rejected(self):
        rows = pd.concat([self.source.iloc[[0]], self.source.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "must be unique"):
            add_cup_flags(rows, self.lookup)

    def test_unclassified_game_is_rejected(self):
        rows = self.source.copy()
        rows.loc[0, "game_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "Missing original Cup classification"):
            add_cup_flags(rows, self.lookup)

    def test_spells_map_original_start_game_to_cup_stage(self):
        spells = pd.DataFrame([
            dict(spell_id="s0", start_game_id="g0", absence_onset=True),
            dict(spell_id="s1", start_game_id="g2", absence_onset=True),
        ])
        result = add_cup_to_spells(spells, self.lookup)
        self.assertEqual(result.onset_cup_stage.to_list(), ["none", "quarterfinal"])
        self.assertEqual(result.onset_cup_knockout.to_list(), [False, True])
        self.assertEqual(result.onset_cup_game.to_list(), [False, True])

    def test_unknown_spell_start_game_is_rejected(self):
        spells = pd.DataFrame([dict(spell_id="s", start_game_id="missing")])
        with self.assertRaisesRegex(ValueError, "Unmatched original absence-spell"):
            add_cup_to_spells(spells, self.lookup)

    def test_missing_original_cup_stage_column_is_rejected(self):
        with ZipFile(self.archives / CUP_ARCHIVE, "w") as zipfile:
            zipfile.writestr(CUP_PREFIX + "cup_game_lookup.csv",
                             self.lookup.drop(columns=["cup_stage"]).to_csv(index=False))
        with self.assertRaisesRegex(ValueError, "fields missing"):
            original_lookup(self.archives / CUP_ARCHIVE)

    def test_exact_decoded_cup_output_ignores_gzip_header_timestamp(self):
        zipfile_path = self.archives / CUP_ARCHIVE
        member_name = "player_game_panel_star_cup.csv.gz"
        with ZipFile(zipfile_path, "w") as z:
            z.writestr(CUP_PREFIX + member_name, gzip.compress(b"source\n", mtime=0))
        result_file = self.work / member_name
        result_file.write_bytes(gzip.compress(b"source\n", mtime=99))
        result = compare_original_cup_output(zipfile_path, result_file, member_name)
        self.assertTrue(result["identical_decoded_bytes"])

    def test_changed_decoded_cup_output_fails(self):
        zipfile_path = self.archives / CUP_ARCHIVE
        member_name = "player_game_panel_star_cup.csv.gz"
        with ZipFile(zipfile_path, "w") as z:
            z.writestr(CUP_PREFIX + member_name, gzip.compress(b"source\n", mtime=0))
        result_file = self.work / member_name
        result_file.write_bytes(gzip.compress(b"tampered\n", mtime=0))
        with self.assertRaisesRegex(ValueError, "Reconstructed output bytes differ"):
            compare_original_cup_output(zipfile_path, result_file, member_name)

    def test_requires_successful_original_core_and_star_acceptance_reports(self):
        with self.assertRaisesRegex(FileNotFoundError, "Accepted original-source stage"):
            check_private_run(self.archives, self.work)

    def test_master_cli_offers_cup_option(self):
        script = Path(__file__).resolve().parents[1] / "scripts/data_rebuild/reproduce_core_and_stars.py"
        done = subprocess.run([sys.executable, str(script), "--help"],
                              cwd=self.root, capture_output=True, text=True, timeout=15)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("--with-cup", done.stdout)

    def test_master_refuses_missing_cup_original_before_generating_core(self):
        new_output = self.root / "not_created"
        with self.assertRaises(FileNotFoundError):
            reproduce(self.archives, new_output, include_cup=True)
        self.assertFalse(new_output.exists())


if __name__ == "__main__":
    unittest.main()
