"""Fail-closed tests of new reviewed analysis-ready continuation from raw-PDF core.

Private reviewed-source ZIP and confidential source records are kept outside
GitHub CI. Original reviewed-label recomputation is separately tested in the
existing analysis-ready bridge suite.
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.data_rebuild import reproduce_core_and_stars as runner


class FiveRawSeasonsToAnalysisReadyIntegrationTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.archives = self.root / "originals"
        self.archives.mkdir()
        self.dest = self.root / "new_private_output"

    def test_master_CLI_has_all_five_original_PDF_seasons_and_reviewed_taxonomy(self):
        script = Path(__file__).resolve().parents[1] / "scripts/data_rebuild/reproduce_core_and_stars.py"
        completed = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=self.root, capture_output=True, text=True, timeout=20
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--from-original-2021-2025-pdfs", completed.stdout)
        self.assertIn("--with-analysis-ready", completed.stdout)
        self.assertIn("--with-original-teamseason-models", completed.stdout)
        self.assertIn("--with-cup", completed.stdout)

    def test_raw_2025_only_and_full_five_season_flags_are_mutually_exclusive(self):
        with patch.object(runner, "immutable_original_star_source"), \
             patch.object(runner, "sha256_file", return_value=runner.REVIEWED_ZIP_SHA256):
            with self.assertRaisesRegex(ValueError, "Choose one raw PDF scope"):
                runner.reproduce(
                    self.archives, self.dest,
                    from_original_2025_pdfs=True,
                    from_original_2021_2025_pdfs=True,
                    include_analysis_ready=True,
                )
        self.assertFalse(self.dest.exists())

    def test_tampered_reviewed_label_package_rejected_before_output(self):
        with patch.object(runner, "immutable_original_star_source"), \
             patch.object(runner, "sha256_file", return_value="changed"):
            with self.assertRaisesRegex(ValueError, "reviewed official-reason"):
                runner.reproduce(
                    self.archives, self.dest,
                    from_original_2021_2025_pdfs=True,
                    include_analysis_ready=True,
                )
        self.assertFalse(self.dest.exists())

    def test_original_models_must_use_new_reviewed_analysis_ready_panel(self):
        with patch.object(runner, "immutable_original_star_source"):
            with self.assertRaisesRegex(ValueError, "requires --with-analysis-ready"):
                runner.reproduce(
                    self.archives, self.dest,
                    from_original_2021_2025_pdfs=True,
                    include_original_teamseason_models=True,
                )
        self.assertFalse(self.dest.exists())

    def test_missing_reviewed_label_package_fails_before_core_staging(self):
        with patch.object(runner, "immutable_original_star_source"):
            with self.assertRaises(FileNotFoundError):
                runner.reproduce(self.archives, self.dest, include_analysis_ready=True)
        self.assertFalse(self.dest.exists())


if __name__ == "__main__":
    unittest.main()
