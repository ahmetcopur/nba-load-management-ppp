"""Offline tests for the historical Level-B repair and exact-clock sensitivity.

Run with requirements-builder-lock.txt (pandas 2.x, PyMuPDF).
Original private NBA PDFs/ZIPs are intentionally not required for unit tests.
"""
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    file = ROOT / "scripts/data_rebuild" / (name + ".py")
    spec = importlib.util.spec_from_file_location("levelb_" + name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load("run_historical_cadence_builder")
restorer = load("restore_historical_layout")
reparse = load("reparse_2024_25_from_pdfs")
clock = load("exact_clock_sensitivity_2025")


class HistoricalBuilderTests(unittest.TestCase):
    def test_pandas3_is_rejected(self):
        with self.assertRaises(SystemExit):
            builder.check_pandas("3.0.5")
        builder.check_pandas("2.2.3")

    def test_known_model_crash_accepted_only_after_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            for filename in builder.PRE_MODEL_OUTPUTS:
                (output / filename).write_text("fresh\n")
            started = output.stat().st_mtime - 10
            self.assertIsNotNone(builder.accept_historical_exit(
                1, "traceback\n" + builder.HISTORICAL_MODEL_CRASH + "\n", output, started))
            self.assertIsNone(builder.accept_historical_exit(
                1, "KeyError: 'team'\n", output, started))
            self.assertEqual(builder.accept_historical_exit(0, "", output, started), "completed")

    def test_stale_or_missing_output_blocks_known_crash(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            for filename in builder.PRE_MODEL_OUTPUTS[:-1]:
                (output / filename).write_text("old\n")
            self.assertIsNone(builder.accept_historical_exit(
                1, builder.HISTORICAL_MODEL_CRASH, output, 0))
            (output / builder.PRE_MODEL_OUTPUTS[-1]).write_text("old\n")
            started = max((output / filename).stat().st_mtime
                          for filename in builder.PRE_MODEL_OUTPUTS) + 10
            self.assertIsNone(builder.accept_historical_exit(
                1, builder.HISTORICAL_MODEL_CRASH, output, started))


class OriginalArchiveFallbackTests(unittest.TestCase):
    def test_corrected_archive_is_required_by_default(self):
        self.assertTrue(any(archive == restorer.CORRECTED_2024
                            for _, archive, _ in restorer.FILES))

    def test_only_explicit_fallback_omits_corrected_archive(self):
        remaining = restorer.without_corrected_2024(restorer.FILES)
        self.assertFalse(any(archive == restorer.CORRECTED_2024
                             for _, archive, _ in remaining))
        self.assertEqual(len(remaining), len(restorer.FILES) - 1)

    def test_missing_original_archive_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            archives = Path(td)
            required = {archive for _, archive, _ in restorer.FILES}
            required |= {restorer.SELECTOR_ZIP, *restorer.RAW_2025}
            for archive in required:
                members = [basename for _, label, basename in restorer.FILES
                           if label == archive]
                if archive == restorer.SELECTOR_ZIP:
                    members = list(restorer.SELECTOR_NAMES)
                if not members:
                    members = ["source.pdf"]
                with zipfile.ZipFile(archives / archive, "w") as z:
                    for member in members:
                        z.writestr(member, "test\n")
            (archives / restorer.CORRECTED_2024).unlink()
            with self.assertRaises(FileNotFoundError):
                restorer.build_plan(archives)
            plan = restorer.build_plan(archives, restorer.without_corrected_2024(restorer.FILES))
            self.assertFalse(any(label == restorer.CORRECTED_2024 for _, label, _ in plan))


class SourceReparseEquivalenceTests(unittest.TestCase):
    def test_row_order_does_not_change_semantic_equality(self):
        df = pd.DataFrame({"x": ["A", "B", "A"], "y": ["1", "2", "1"]})
        self.assertTrue(reparse.same_rows(df, df.iloc[[2, 0, 1]].copy()))
        changed = df.copy()
        changed.loc[2, "y"] = "other"
        self.assertFalse(reparse.same_rows(df, changed))

    def test_reproduce_historical_not_submitted_count_quirk(self):
        rows = pd.DataFrame([
            {"source_file": "audit/pdf/R1.pdf", "matchup_norm": "AAA@BBB",
             "team_norm": "team a", "player_name": "Alpha",
             "current_status": "Out", "team_submission_status": "submitted"},
            {"source_file": "audit/pdf/R1.pdf", "matchup_norm": "AAA@BBB",
             "team_norm": "team a", "player_name": "Beta",
             "current_status": "Available", "team_submission_status": "submitted"},
            {"source_file": "audit/pdf/R1.pdf", "matchup_norm": "AAA@BBB",
             "team_norm": "team b", "player_name": None,
             "current_status": None, "team_submission_status": "not_yet_submitted"},
        ])
        teams = pd.DataFrame([
            {"snapshot_basename": "R1.pdf", "matchup_norm": "AAA@BBB", "team_norm": "team a"},
            {"snapshot_basename": "R1.pdf", "matchup_norm": "AAA@BBB", "team_norm": "team b"},
        ])
        result = reparse.selector_fields(rows, teams)
        self.assertEqual(result.team_final_status.tolist(),
                         ["submitted_with_listed_players", "not_yet_submitted"])
        self.assertEqual(result.n_player_rows.tolist(), [2, 2])


class ExactClockSelectionTests(unittest.TestCase):
    def test_reselect_prior_printed_report_for_late_header(self):
        printed = pd.DataFrame([
            {"basename": "old.pdf",
             "header_utc": pd.Timestamp("2025-12-19T20:45:00Z"),
             "sha256": "a" * 64},
            {"basename": "new.pdf",
             "header_utc": pd.Timestamp("2025-12-19T21:45:00Z"),
             "sha256": "b" * 64},
        ])
        selected = pd.DataFrame([{
            "game_id": "g1", "Match Number": 11,
            "matchup_norm": "AAA@BBB",
            "published_timestamp_utc": "2025-12-19T21:30:00+00:00",
            "tip_timestamp_utc": "2025-12-20T00:30:00+00:00",
            "snapshot_basename": "new.pdf",
        }])
        candidates, summary = clock.candidates(selected, printed)
        self.assertEqual(summary["games_printed_after_checkpoint"], 1)
        self.assertEqual(candidates.iloc[0].candidate_basename, "old.pdf")
        self.assertEqual(int(candidates.iloc[0].match_number), 11)

    def test_missing_selected_pdf_header_rejected(self):
        selected = pd.DataFrame([{
            "game_id": "g1", "Match Number": 11,
            "matchup_norm": "AAA@BBB", "published_timestamp_utc": "2025-12-19T21:30:00Z",
            "tip_timestamp_utc": "2025-12-20T00:30:00Z",
            "snapshot_basename": "missing.pdf",
        }])
        printed = pd.DataFrame([{
            "basename": "old.pdf", "header_utc": pd.Timestamp("2025-12-19T20:00:00Z"),
            "sha256": "a" * 64,
        }])
        with self.assertRaisesRegex(RuntimeError, "missing"):
            clock.candidates(selected, printed)


if __name__ == "__main__":
    unittest.main()
