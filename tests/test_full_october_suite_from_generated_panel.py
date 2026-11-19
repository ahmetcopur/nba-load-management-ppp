"""Fail-closed tests for ten original October scripts on a NEW source-generated panel.

No original user NBA ZIPs or per-player reports are placed in public CI.
Testing ensures that a frozen/reference panel cannot masquerade as the new
accepted source, that 2025 original-PDF lineage is required, that the full
33-output archived replay is enforced, and that the pandas-3 October runtime
is never silently replaced by the pandas-2 upstream builder environment.
"""
from __future__ import annotations

import gzip
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.data_rebuild import run_full_october_suite_from_generated_panel as m


class SourceGeneratedTenOctoberScriptsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.shared = self.root / "clean_shared_source"
        self.shared.mkdir()
        self.source = self.root / "source_generated_october"
        self.panel = (self.source /
            "cadence_harmonized_results/player_team_game_harmonized_cadence.csv.gz")
        self.panel.parent.mkdir(parents=True)
        self.panel.write_bytes(gzip.compress(b"real-generated-panel\n", mtime=0))
        self.out = self.root / "new_private_suite"
        self.acceptance = {
            "status": "pass",
            "original_source_stages_executed": [
                "historical_panel", "historical_models"],
            "full_decoded_harmonized_panel_exact": {
                "identical_decoded_bytes": True,
                "decoded_sha256": m.SOURCE_OCTOBER_PANEL_SHA256,
            },
            "source_2025_harmonized": {"fresh_original_pdfs_parsed": 355},
            "four_original_October_model_results": {
                "matched": True, "model_specifications": 4,
            },
        }
        self.write_acceptance()

    def write_acceptance(self):
        (self.source / m.SOURCE_REPORT_NAME).write_text(
            json.dumps(self.acceptance), encoding="utf-8"
        )

    def test_existing_output_must_not_be_overwritten(self):
        self.out.mkdir()
        with self.assertRaises(FileExistsError):
            m.check_private_destination(self.shared, self.panel, self.out)

    def test_historical_git_checkout_not_a_private_output(self):
        (self.shared / ".git").mkdir()
        with self.assertRaisesRegex(ValueError, "original shared checkout"):
            m.check_private_destination(
                self.shared, self.panel, self.shared / "new-output"
            )

    def test_missing_source_generated_report_rejected(self):
        (self.source / m.SOURCE_REPORT_NAME).unlink()
        with self.assertRaisesRegex(FileNotFoundError, "acceptance report missing"):
            m.verify_source_generated_panel(self.panel)

    def test_frozen_panel_path_not_accepted_as_generated(self):
        copied = self.root / "old_archived_panel.csv.gz"
        copied.write_bytes(self.panel.read_bytes())
        with self.assertRaisesRegex(ValueError, "filename differs"):
            m.verify_source_generated_panel(copied)

    def test_fake_2025_raw_pdf_provenance_rejected(self):
        self.acceptance["source_2025_harmonized"]["fresh_original_pdfs_parsed"] = 0
        self.write_acceptance()
        with self.assertRaisesRegex(ValueError, "355 original harmonized"):
            m.verify_source_generated_panel(self.panel)

    def test_original_stage6_must_be_reproduced_before_all_ten(self):
        self.acceptance["four_original_October_model_results"]["matched"] = False
        self.write_acceptance()
        with self.assertRaisesRegex(ValueError, "Stage-6 models did not match"):
            m.verify_source_generated_panel(self.panel)

    def test_missing_historical_source_execution_is_rejected(self):
        self.acceptance["original_source_stages_executed"] = ["historical_panel"]
        self.write_acceptance()
        with self.assertRaisesRegex(ValueError, "panel and four models"):
            m.verify_source_generated_panel(self.panel)

    def test_forged_report_cannot_substitute_changed_panel_bytes(self):
        with self.assertRaisesRegex(ValueError, "panel bytes differ"):
            m.verify_source_generated_panel(self.panel)

    def test_source_report_and_true_byte_digest_are_required(self):
        with patch.object(m, "digest_gzip_payload",
                          return_value=m.SOURCE_OCTOBER_PANEL_SHA256):
            verdict = m.verify_source_generated_panel(self.panel)
        self.assertTrue(verdict["original_october_panel_source_accepted"])

    def test_python_pandas_3_version_must_match_october_lock(self):
        good = dict(python="3.12.3", pandas="3.0.5", numpy="2.5.2",
                    scipy="1.18.0", statsmodels="0.14.6")
        with patch.object(m.subprocess, "run",
            return_value=subprocess.CompletedProcess(["python"],0,
                             stdout=json.dumps(good))) as call:
            self.assertEqual(m.verify_october_runtime(Path("/fake/python"))["pandas"], "3.0.5")
            self.assertIn("import sys,pandas", call.call_args.args[0][2])
        good["pandas"] = "2.2.3"
        with patch.object(m.subprocess, "run",
            return_value=subprocess.CompletedProcess(["python"],0,
                             stdout=json.dumps(good))):
            with self.assertRaisesRegex(ValueError, "October source-model environment differs"):
                m.verify_october_runtime(Path("/fake/python"))

    def test_all_ten_rerun_receives_new_panel_and_compares_all_33(self):
        pretend_result = {
            f"model_{index}.csv": {
                "archived": True, "same_shape": True,
                "differing_text_cells": 0,
                "max_abs_numeric_difference": 1e-14
            }
            for index in range(33)
        }
        patches = [
            patch.object(m, "verify_source_generated_panel",
                         return_value={"regenerated_panel_decoded_sha256":
                                       m.SOURCE_OCTOBER_PANEL_SHA256}),
            patch.object(m, "verify_shared_commit"),
            patch.object(m, "verify_october_runtime",
                         return_value={"python":"3.12.3","pandas":"3.0.5"}),
            patch.object(m, "prepare"),
            patch.object(m, "run_all"),
            patch.object(m, "reproduction", return_value=pretend_result),
        ]
        with patches[0], patches[1], patches[2], patches[3] as prepare, \
             patches[4] as run_all, patches[5]:
            report = m.run(self.shared, self.panel, self.out,
                           october_python=Path("/fake/python"))
        self.assertEqual(report["original_33_reference_output_comparisons"], 33)
        self.assertEqual(prepare.call_args.args[2], self.panel.resolve())
        self.assertTrue(run_all.called)
        self.assertTrue((self.out / "original_ten_october_models_from_source.json").is_file())

    def test_missing_one_of_33_output_comparisons_rejected(self):
        result = {
            f"model_{i}.csv": {
                "archived": True, "same_shape": True,
                "differing_text_cells": 0,
                "max_abs_numeric_difference": 0.0,
            }
            for i in range(32)
        }
        with patch.object(m, "verify_source_generated_panel", return_value={}), \
             patch.object(m, "verify_shared_commit"), \
             patch.object(m, "verify_october_runtime", return_value={}), \
             patch.object(m, "prepare"), patch.object(m, "run_all"), \
             patch.object(m, "reproduction", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "Expected 33"):
                m.run(self.shared, self.panel, self.out,
                      october_python=Path("/fake/python"))

    def test_direct_cli_has_separate_runtime_option(self):
        script = Path(__file__).resolve().parents[1] / (
            "scripts/data_rebuild/run_full_october_suite_from_generated_panel.py"
        )
        result = subprocess.run(
            [__import__("sys").executable, str(script), "--help"],
            cwd=self.root, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--october-python", result.stdout)
        self.assertIn("--generated-october-panel", result.stdout)


if __name__ == "__main__":
    unittest.main()
