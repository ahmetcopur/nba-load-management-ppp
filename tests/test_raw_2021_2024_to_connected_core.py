"""Synthetic original 2021–24 NBA PDF reconstruction and source-to-core tests.

The private 2,291 genuine PDFs are never committed to GitHub CI. Real source
execution is separately evidenced and CI fails closed on source/selector drift.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import pandas as pd

from scripts.data_rebuild import rebuild_2021_2024_selected_from_pdfs as mod
from scripts.data_rebuild.run_connected_player_game_core import inject_reparsed_seasons

COLUMNS = [
    "season", "source_file", "report_date", "snapshot_timestamp_utc",
    "game_date_raw", "game_time_et_raw", "matchup", "matchup_norm",
    "team", "team_norm", "player_name", "player_name_norm",
    "current_status", "reason", "team_submission_status",
    "snapshot_basename", "canonical_game_id", "source_match_number",
    "published_timestamp_utc", "game_id", "minutes_before_tip",
    "qc_selected_within_30m",
]


def source_row(season="2022-23", matchup="AAA@BBB"):
    name = "Injury-Report_2022-10-18_06PM.pdf"
    return {
        "season": season, "source_file": mod.original_source_file(season, name),
        "report_date": "2022-10-18",
        "snapshot_timestamp_utc": "2022-10-18T22:30:00+00:00",
        "game_date_raw": "10/18/2022", "game_time_et_raw": "07:30 (ET)",
        "matchup": matchup, "matchup_norm": matchup,
        "team": "Team A", "team_norm": "team a",
        "player_name": "One, Player", "player_name_norm": "one player",
        "current_status": "Out", "reason": "Illness",
        "team_submission_status": "submitted",
    }


def choice(season="2022-23", matchup="AAA@BBB", game="GAME1"):
    return {
        "snapshot_basename": "Injury-Report_2022-10-18_06PM.pdf",
        "matchup_norm": matchup, "canonical_game_id": "FD2022_1",
        "source_match_number": 1,
        "published_timestamp_utc": "2022-10-18T22:30:00+00:00",
        "game_id": game, "minutes_before_tip": 60.0,
        "qc_selected_within_30m": False,
        "season": season,
    }


HELPERS = {"norm_team": lambda x: str(x).lower(),
           "clean": lambda x: " ".join(str(x).split())}


class HistoricalOriginalPDFConnectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archives = self.root / "source"
        self.archives.mkdir()

    def test_selected_original_parser_is_early_for_2021_and_2022(self):
        self.assertEqual(mod.SEASONS["2021-22"]["parser"], "early")
        self.assertEqual(mod.SEASONS["2022-23"]["parser"], "early")
        self.assertEqual(mod.SEASONS["2023-24"]["parser"], "late")
        self.assertEqual(mod.SEASONS["2024-25"]["parser"], "late")

    def test_original_2021_source_file_is_basename_only(self):
        name = "Injury-Report_2021-10-21_05PM.pdf"
        self.assertEqual(mod.original_source_file("2021-22", name), name)
        self.assertEqual(mod.original_source_file("2023-24", name),
                         "audit_2023_24/pdf/" + name)

    def test_selected_report_columns_recreated_from_source_pdf_row(self):
        row = source_row()
        metadata = choice()
        actual = mod.assemble_selected_rows(
            [(metadata["snapshot_basename"], row)],
            {(metadata["snapshot_basename"], metadata["matchup_norm"]): metadata},
            "2022-23", COLUMNS, HELPERS,
        )
        self.assertEqual(list(actual.columns), COLUMNS)
        self.assertEqual(actual.iloc[0].player_name, "One, Player")
        self.assertEqual(actual.iloc[0].reason, "Illness")
        self.assertEqual(actual.iloc[0].game_id, "GAME1")

    def test_2021_toronto_source_fixture_rekey_is_explicit(self):
        row = source_row("2021-22", "CHI@TOR")
        meta = choice("2021-22", "CHI@TOR", "wrong-legacy-source-number")
        actual = mod.assemble_selected_rows(
            [(meta["snapshot_basename"], row)],
            {(meta["snapshot_basename"], meta["matchup_norm"]): meta},
            "2021-22", COLUMNS, HELPERS,
        )
        self.assertEqual(actual.iloc[0].game_id, mod.TORONTO_SOURCE_GAME_REKEY["CHI@TOR"])

    def test_unknown_original_pdf_matchup_cannot_join_other_game(self):
        row = source_row(matchup="OTHER@OTHER")
        meta = choice()
        with self.assertRaisesRegex(ValueError, "outside selected game"):
            mod.assemble_selected_rows(
                [(meta["snapshot_basename"], row)],
                {(meta["snapshot_basename"], meta["matchup_norm"]): meta},
                "2022-23", COLUMNS, HELPERS,
            )

    def test_all_22_original_record_fields_compared_in_any_order(self):
        src = source_row()
        src.update(choice())
        table = pd.DataFrame([src, {**src, "player_name": "Two, Player"}])[COLUMNS]
        with patch.dict(mod.SEASONS["2022-23"], {"rows": 2}):
            result = mod.compare_original_22_fields(
                table.iloc[::-1], table, "2022-23",
            )
        self.assertEqual(result["selected_player_report_rows"], 2)
        self.assertTrue(result["complete_original_row_multiset_exact"])

    def test_changed_source_reason_fails_even_if_row_count_same(self):
        src = source_row()
        src.update(choice())
        ref = pd.DataFrame([src])[COLUMNS]
        observed = ref.copy()
        observed.loc[0, "reason"] = "Different"
        with patch.dict(mod.SEASONS["2022-23"], {"rows": 1}):
            with self.assertRaisesRegex(ValueError, "22-field full-record mismatch"):
                mod.compare_original_22_fields(observed, ref, "2022-23")

    def test_missing_source_column_fails_without_model_fallback(self):
        src = source_row()
        src.update(choice())
        ref = pd.DataFrame([src])[COLUMNS]
        with self.assertRaisesRegex(ValueError, "22-column schema mismatch"):
            mod.compare_original_22_fields(ref.drop(columns=["reason"]), ref, "2022-23")

    def test_source_zip_rejects_duplicate_original_pdf_basenames(self):
        name = "Injury-Report_2022-10-18_06PM.pdf"
        zipfile = self.archives / "source.zip"
        with ZipFile(zipfile, "w") as archive:
            archive.writestr("first/" + name, b"PDF-A")
            archive.writestr("second/" + name, b"PDF-B")
        with self.assertRaisesRegex(ValueError, "Ambiguous original PDF basename"):
            mod.stage_original_pdfs(zipfile, {name}, self.root)

    def test_original_source_zip_missing_selected_pdf_rejected(self):
        with ZipFile(self.archives / "source.zip", "w") as archive:
            archive.writestr("unrelated.pdf", b"none")
        with self.assertRaisesRegex(ValueError, "Missing original source PDFs"):
            mod.stage_original_pdfs(
                self.archives / "source.zip", {"Injury-Report_2022-10-18_06PM.pdf"},
                self.root
            )

    def test_existing_output_folder_is_not_overwritten(self):
        dest = self.root / "old_output"
        dest.mkdir()
        with self.assertRaises(FileExistsError):
            mod.safe_private_directory(self.archives, dest)

    def test_raw_player_rows_cannot_be_generated_in_git_checkout(self):
        git = self.root / "repo"
        (git / ".git").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "inside Git checkout"):
            mod.safe_private_directory(self.archives, git / "private")

    def test_2020_source_replacement_is_deliberately_rejected(self):
        with self.assertRaisesRegex(ValueError, "Only 2021"):
            inject_reparsed_seasons(
                pd.DataFrame(), {"2020-21": self.root / "not_existing.csv"}
            )

    def test_original_source_filename_and_season_choices_strict(self):
        self.assertEqual(
            mod.accepted_source_filename("2024-25"),
            "selected_report_rows_2024_25_from_original_PDFs.csv",
        )
        with self.assertRaisesRegex(ValueError, "Unknown supported"):
            mod.accepted_source_filename("2020-21")


if __name__ == "__main__":
    unittest.main()
