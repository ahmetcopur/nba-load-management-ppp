"""Synthetic positive/negative tests for actual 2025 PDF-selected input connector.

No private player-level reports or raw PDFs are in GitHub CI. The actual
729-PDF, 13,968-row raw-source run is separately documented and validated.
"""
from __future__ import annotations
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import pandas as pd

from scripts.data_rebuild import rebuild_2025_selected_from_pdfs as source
from scripts.data_rebuild.run_connected_player_game_core import (
    inject_fresh_2025_selected_rows,
)

COLUMNS = [
    "season", "source_file", "report_date", "snapshot_timestamp_utc",
    "game_date_raw", "game_time_et_raw", "matchup", "matchup_norm",
    "team", "team_norm", "player_name", "player_name_norm",
    "current_status", "reason", "team_submission_status",
    "snapshot_basename", "canonical_game_id", "source_match_number",
    "published_timestamp_utc", "game_id", "minutes_before_tip",
    "qc_selected_within_30m",
]


def row(player="Test, One", game="GAME_1"):
    return {
        "season": "2025-26", "source_file": "Injury-Report_2025-10-21_01PM.pdf",
        "report_date": "2025-10-21",
        "snapshot_timestamp_utc": "2025-10-21T17:30:00+00:00",
        "game_date_raw": "10/21/2025", "game_time_et_raw": "07:30 (ET)",
        "matchup": "AAA@BBB", "matchup_norm": "AAA@BBB",
        "team": "Team A", "team_norm": "team a", "player_name": player,
        "player_name_norm": player.lower(), "current_status": "Out",
        "reason": "Illness", "team_submission_status": "submitted",
        "snapshot_basename": "Injury-Report_2025-10-21_01PM.pdf",
        "canonical_game_id": "FD2025_1",
        "source_match_number": 1, "published_timestamp_utc": "2025-10-21T17:30:00+00:00",
        "game_id": game, "minutes_before_tip": 120.0,
        "qc_selected_within_30m": False,
    }


class OriginalPDF2025InputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archives = self.root / "private_original_zips"
        self.archives.mkdir()

    def test_report_comparison_order_independent_all_22_fields(self):
        original = pd.DataFrame([row("One, Player"), row("Two, Player")])[COLUMNS]
        candidate = original.iloc[::-1]
        with patch.object(source, "EXPECTED_REPORT_ROWS", 2):
            result = source.verify_original_row_equality(candidate, original)
        self.assertTrue(result["all_complete_record_multisets_exact"])
        self.assertEqual(result["complete_original_fields_compared"], 22)

    def test_changed_reason_is_rejected_even_if_counts_match(self):
        original = pd.DataFrame([row("One, Player"), row("Two, Player")])[COLUMNS]
        candidate = original.copy()
        candidate.loc[0, "reason"] = "Changed reason"
        with patch.object(source, "EXPECTED_REPORT_ROWS", 2):
            with self.assertRaisesRegex(ValueError, "missing=1, extra=1"):
                source.verify_original_row_equality(candidate, original)

    def test_changed_status_is_rejected(self):
        original = pd.DataFrame([row("One, Player"), row("Two, Player")])[COLUMNS]
        candidate = original.copy()
        candidate.loc[1, "current_status"] = "Available"
        with patch.object(source, "EXPECTED_REPORT_ROWS", 2):
            with self.assertRaisesRegex(ValueError, "Original 2025 raw-PDF selected rows differ"):
                source.verify_original_row_equality(candidate, original)

    def test_missing_original_column_blocks_source_acceptance(self):
        original = pd.DataFrame([row("One, Player"), row("Two, Player")])[COLUMNS]
        with self.assertRaisesRegex(ValueError, "22-column schema changed"):
            source.verify_original_row_equality(original.drop(columns=["reason"]), original)

    def test_game_selector_rejects_duplicate_selected_matchup(self):
        c = pd.DataFrame([row(), row()]).rename(
            columns={"game_id": "game_id"}
        )
        with patch.object(source, "EXPECTED_GAME_COUNT", 2), \
             patch.object(source, "EXPECTED_PDF_COUNT", 1):
            with self.assertRaisesRegex(ValueError, "duplicate PDF\\+matchup"):
                source.original_2025_selection_map(c)

    def test_multiple_matchups_can_share_one_original_pdf(self):
        a = row()
        b = row()
        b["matchup_norm"], b["game_id"] = "CCC@DDD", "GAME_2"
        with patch.object(source, "EXPECTED_GAME_COUNT", 2), \
             patch.object(source, "EXPECTED_PDF_COUNT", 1):
            mapping, groups = source.original_2025_selection_map(pd.DataFrame([a, b]))
        self.assertEqual(len(mapping), 2)
        self.assertEqual(len(groups), 1)

    def test_original_parser_rows_join_original_snapshot_metadata(self):
        r = row()
        original_parsed = {k:r[k] for k in COLUMNS[:15]}
        mapper = {(r["snapshot_basename"], r["matchup_norm"]): r}
        clean = lambda x: str(x).strip()
        result = source.build_report_rows(
            [(r["snapshot_basename"], original_parsed)], mapper, COLUMNS,
            {"norm_team":lambda x:x, "clean":clean},
        )
        self.assertEqual(list(result.columns), COLUMNS)
        self.assertEqual(result.iloc[0].game_id, "GAME_1")
        self.assertEqual(result.iloc[0].reason, "Illness")

    def test_unselected_matchup_never_silently_joins_another_game(self):
        r = row()
        parsed = {k:r[k] for k in COLUMNS[:15]}
        parsed["matchup_norm"] = "OTHER@OTHER"
        mapper = {(r["snapshot_basename"], r["matchup_norm"]): r}
        with self.assertRaisesRegex(ValueError, "non-selected matchup"):
            source.build_report_rows(
                [(r["snapshot_basename"], parsed)], mapper, COLUMNS,
                {"norm_team":lambda x:x, "clean":lambda x:str(x)},
            )

    def test_private_source_output_directory_must_not_exist(self):
        destination = self.root / "prior_results"
        destination.mkdir()
        with self.assertRaises(FileExistsError):
            source.verify_safe_destination(self.archives, destination)

    def test_private_source_output_cannot_be_in_git_checkout(self):
        git = self.root / "repo"
        (git / ".git").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "inside Git checkout"):
            source.verify_safe_destination(self.archives, git / "raw-player-csv")

    def test_duplicate_pdf_name_across_two_original_archives_is_rejected(self):
        basename = "Injury-Report_2025-10-21_01PM.pdf"
        for sourcezip in source.SOURCE_ZIPS:
            with ZipFile(self.archives / sourcezip, "w") as archive:
                archive.writestr("audit/pdf/" + basename, b"pdf")
        scratch = self.root / "staged"
        scratch.mkdir()
        with self.assertRaisesRegex(ValueError, "Ambiguous duplicate"):
            source.stage_pdfs(self.archives, {basename}, scratch)

    def test_core_rejects_non_2025_replacement_before_using_it(self):
        replacement = self.root / "candidate.csv"
        pd.DataFrame([row() | {"season":"2024-25"}])[COLUMNS].to_csv(
            replacement, index=False
        )
        with self.assertRaisesRegex(ValueError, "ONLY 2025-26"):
            inject_fresh_2025_selected_rows(pd.DataFrame([row()]), replacement)

    def test_combined_cli_offers_actual_original_pdf_entrypoint(self):
        cli = Path(__file__).resolve().parents[1] / "scripts/data_rebuild/reproduce_core_and_stars.py"
        proc = subprocess.run(
            [sys.executable, str(cli), "--help"],
            cwd=self.root, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--from-original-2025-pdfs", proc.stdout)
        self.assertIn("--with-cup", proc.stdout)


if __name__ == "__main__":
    unittest.main()
