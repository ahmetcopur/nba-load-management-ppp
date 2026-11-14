"""Regression tests for the repaired 2020–21 original injury-PDF layout parser.

The original 617 PDFs remain private and are not pushed to CI. These tests
reconstruct the observed multi-row PDF wrap patterns from synthetic source
lines, never from archived player-specific replacement reason strings.
"""
from __future__ import annotations
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.data_rebuild import rebuild_2020_selected_from_pdfs as m
from scripts.data_rebuild import reproduce_core_and_stars as master


def example(reason, *, name="A", team="Rockets", matchup="HOU@IND",
            file="report.pdf", status="Out"):
    return dict(reason=reason, player_name=name, team_norm=team,
                matchup_norm=matchup, source_file=file, current_status=status)


class Original2020PDFOverflowRepairTests(unittest.TestCase):
    def test_one_wrapped_reason_flows_back_to_previous_record(self):
        rows = [
            example("Injury/Illness - Bilateral Eye; Bi-lateral epidemic"),
            example("keratoconjunctivitis G League - Two-Way", name="B"),
        ]
        correct, counts = m.repair_reason_overflows(rows)
        self.assertEqual(correct[0]["reason"],
            "Injury/Illness - Bilateral Eye; Bi-lateral epidemic keratoconjunctivitis")
        self.assertEqual(correct[1]["reason"], "G League - Two-Way")
        self.assertEqual(counts["overflow_fragments_transferred"], 1)
        self.assertEqual(counts["preceding_source_reasons_completed"], 1)

    def test_same_clipped_reason_can_belong_to_two_preceding_players(self):
        clipped = "Injury/Illness - Illness; Return to play conditioning (post Self"
        rows = [
            example(clipped, name="A", team="Rockets"),
            example(clipped, name="B", team="Rockets"),
            example("Isolating) Injury/Illness - Right Ankle; Sprain",
                    name="C", team="Pacers"),
        ]
        actual, counts = m.repair_reason_overflows(rows)
        self.assertEqual(actual[0]["reason"], clipped + " Isolating)")
        self.assertEqual(actual[1]["reason"], clipped + " Isolating)")
        self.assertEqual(actual[2]["reason"], "Injury/Illness - Right Ankle; Sprain")
        self.assertEqual(counts["overflow_fragments_transferred"], 1)
        self.assertEqual(counts["preceding_source_reasons_completed"], 2)

    def test_post_protocols_reconditioning_is_not_false_positive(self):
        rows = [
            example("Injury/Illness - Left Knee; Soreness"),
            example("Injury/Illness - Illness; Post Health and Safety Protocols Reconditioning", name="B"),
        ]
        result, stats = m.repair_reason_overflows(rows)
        self.assertEqual(result, rows)
        self.assertEqual(stats["overflow_fragments_transferred"], 0)

    def test_management_word_wrap_over_standalone_protocol_reason(self):
        rows = [
            example("Injury/Illness - Left Hand; Fourth Metacarpal Fracture - Injury"),
            example("Management Health and Safety Protocols", name="B"),
        ]
        result, stats = m.repair_reason_overflows(rows)
        self.assertEqual(result[0]["reason"],
            "Injury/Illness - Left Hand; Fourth Metacarpal Fracture - Injury Management")
        self.assertEqual(result[1]["reason"], "Health and Safety Protocols")
        self.assertEqual(stats["overflow_fragments_transferred"], 1)

    def test_no_cross_pdf_continuation(self):
        rows = [
            example("Injury/Illness - Eye; epidemic", file="first.pdf"),
            example("keratoconjunctivitis G League - Two-Way", file="second.pdf"),
        ]
        result, stats = m.repair_reason_overflows(rows)
        self.assertEqual(result, rows)
        self.assertEqual(stats["overflow_fragments_transferred"], 0)

    def test_no_cross_matchup_continuation(self):
        rows = [
            example("Injury/Illness - Eye; epidemic", matchup="AAA@BBB"),
            example("keratoconjunctivitis G League - Two-Way", matchup="CCC@DDD"),
        ]
        result, stats = m.repair_reason_overflows(rows)
        self.assertEqual(result, rows)
        self.assertEqual(stats["overflow_fragments_transferred"], 0)

    def test_valid_unwrapped_reason_is_not_changed(self):
        rows = [
            example("G League - Two-Way"),
            example("Injury/Illness - Right Wrist; Fracture", name="B"),
        ]
        result, stats = m.repair_reason_overflows(rows)
        self.assertEqual(result, rows)
        self.assertEqual(stats["overflow_fragments_transferred"], 0)

    def test_repair_never_modifies_original_list(self):
        rows = [
            example("Injury/Illness - Right Quad; Injury"),
            example("Maintenance/Recovery/Management Injury/Illness - Left Knee; Soreness", name="B"),
        ]
        snapshot = copy.deepcopy(rows)
        repaired, _ = m.repair_reason_overflows(rows)
        self.assertEqual(rows, snapshot)
        self.assertNotEqual(repaired, snapshot)

    def test_all_15_original_fields_must_match_complete_records(self):
        r = example("Injury/Illness - Left Knee; Soreness")
        columns = ["source_file", "matchup_norm", "team_norm", "player_name",
                   "current_status", "reason"]
        original = pd.DataFrame([r])[columns]
        candidate = original.copy()
        outcome = m.assert_full_original_equality(candidate, original, 1, "fake")
        self.assertTrue(outcome["every_original_column_and_full_record_exact"])
        candidate.loc[0, "reason"] = "Changed"
        with self.assertRaisesRegex(ValueError, "original complete record mismatch"):
            m.assert_full_original_equality(candidate, original, 1, "fake")

    def test_missing_original_column_or_row_is_rejected(self):
        ref = pd.DataFrame([example("Out")])
        with self.assertRaisesRegex(ValueError, "schema/order differs"):
            m.assert_full_original_equality(ref.drop(columns=["reason"]), ref, 1, "source")
        with self.assertRaisesRegex(ValueError, "expected 1 records"):
            m.assert_full_original_equality(ref.iloc[0:0], ref, 1, "source")

    def test_private_output_cannot_overwrite_prior_result(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            source = base / "source"
            output = base / "output"
            source.mkdir()
            output.mkdir()
            with self.assertRaises(FileExistsError):
                m.safe_output(source, output)

    def test_original_2020_parser_archive_is_source_pinned(self):
        self.assertEqual(m.PARSER_SHA,
            "77fb85d6e0634c01d0ddb0739294c0ed044671b5b93b0affbbf9ec943a7ef6ee")
        self.assertEqual(m.EXPECTED_PDFS, 617)
        self.assertEqual(m.EXPECTED_SOURCE_ROWS, 41780)
        self.assertEqual(m.EXPECTED_SELECTED_ROWS, 8591)

    def test_six_season_master_exposes_original_2020_PDF_option(self):
        import subprocess, sys
        p = Path(__file__).resolve().parents[1] / (
            "scripts/data_rebuild/reproduce_core_and_stars.py"
        )
        with tempfile.TemporaryDirectory() as t:
            result = subprocess.run([sys.executable, str(p), "--help"],
                capture_output=True, text=True, timeout=20, cwd=t)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--from-original-2020-2025-pdfs", result.stdout)
        self.assertIn("--previous-2020-reparse-csv", result.stdout)

    def test_existing_2020_reparse_requires_six_season_scope(self):
        with tempfile.TemporaryDirectory() as t:
            raw = Path(t)
            with patch.object(master, "immutable_original_star_source"):
                with self.assertRaisesRegex(ValueError, "earlier 2020 PDF source CSV requires"):
                    master.reproduce(
                        raw, raw / "newrun",
                        previous_2020_reparse_csv=raw / "some.csv"
                    )
            self.assertFalse((raw / "newrun").exists())

    def test_six_season_and_five_season_flags_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as t:
            raw = Path(t)
            with patch.object(master, "immutable_original_star_source"):
                with self.assertRaisesRegex(ValueError, "Choose one original PDF scope"):
                    master.reproduce(raw, raw / "newrun",
                        from_original_2020_2025_pdfs=True,
                        from_original_2021_2025_pdfs=True)
            self.assertFalse((raw / "newrun").exists())


if __name__ == "__main__":
    unittest.main()
