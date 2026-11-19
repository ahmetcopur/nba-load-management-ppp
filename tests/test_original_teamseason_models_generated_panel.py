"""Synthetic original model-source and coefficient/SE reconstruction acceptance tests."""
from __future__ import annotations
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from scripts.data_rebuild.run_original_teamseason_models_from_generated_panel import (
    compare_model_outputs, run, stage_source, SOURCE_CODE_MEMBER,
    validate_private_result_path,
)


def model(outcome="absence_onset", coefficient=0.031493):
    return {
        "outcome": outcome, "n": 180829, "estimate": coefficient,
        "se": 0.013156, "p": 0.016679,
        "low": 0.005707, "high": 0.057279,
    }


class OriginalTeamSeasonModelSourceTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.result_dir = self.root / "new_model_output"

    def test_original_outcome_and_all_uncertainty_fields_order_independent(self):
        ref = pd.DataFrame([
            model(), model("vague_conditional", -0.071812)
        ])
        out = ref.iloc[::-1].copy()
        result = compare_model_outputs(ref, out, ["outcome"])
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["maximum_absolute_numeric_difference"], 0.0)

    def test_change_in_original_coefficient_fails(self):
        ref = pd.DataFrame([model()])
        out = ref.copy()
        out.loc[0, "estimate"] += 1e-5
        with self.assertRaisesRegex(ValueError, "estimate/inference differs: estimate"):
            compare_model_outputs(ref, out, ["outcome"])

    def test_changed_standard_error_fails_even_if_estimate_same(self):
        ref = pd.DataFrame([model()])
        out = ref.copy()
        out.loc[0, "se"] = 0.5
        with self.assertRaisesRegex(ValueError, "estimate/inference differs: se"):
            compare_model_outputs(ref, out, ["outcome"])

    def test_very_small_original_float_noise_is_accepted(self):
        ref = pd.DataFrame([model()])
        out = ref.copy()
        out.loc[0, "p"] += 1e-14
        self.assertTrue(compare_model_outputs(ref, out, ["outcome"])[
            "all_original_coefficient_inference_cells_match"])

    def test_duplicate_model_term_key_fails(self):
        ref = pd.DataFrame([model(), model()])
        with self.assertRaisesRegex(ValueError, "identities duplicate"):
            compare_model_outputs(ref, ref, ["outcome"])

    def test_extra_model_output_column_fails(self):
        ref = pd.DataFrame([model()])
        out = ref.copy()
        out["new_spec"] = "not frozen"
        with self.assertRaisesRegex(ValueError, "schema/order differs"):
            compare_model_outputs(ref, out, ["outcome"])

    def test_original_model_package_has_pinned_zip_bytes(self):
        package = self.root / "original_model.zip"
        with ZipFile(package, "w") as z:
            z.writestr(SOURCE_CODE_MEMBER, "print('tampered')")
        self.result_dir.mkdir()
        with self.assertRaisesRegex(ValueError, "first-pass model ZIP SHA"):
            stage_source(package, self.root / "fake.gz", self.result_dir)

    def test_reject_prior_model_result_dir(self):
        self.result_dir.mkdir()
        with self.assertRaises(FileExistsError):
            validate_private_result_path(self.result_dir, self.root / "repo")

    def test_missing_analysis_ready_source_does_not_create_result(self):
        with self.assertRaises(FileNotFoundError):
            run(self.root / "nonexistent.csv.gz", self.result_dir)
        self.assertFalse(self.result_dir.exists())

    def test_cli_supports_private_generated_analysis_ready_file(self):
        script = Path(__file__).resolve().parents[1] / "scripts/data_rebuild/run_original_teamseason_models_from_generated_panel.py"
        p = subprocess.run(
            [sys.executable, str(script), "--help"], cwd=self.root,
            capture_output=True, text=True, timeout=15
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("--generated-model-panel", p.stdout)
        self.assertIn("--historical-model-package", p.stdout)


if __name__ == "__main__":
    unittest.main()
