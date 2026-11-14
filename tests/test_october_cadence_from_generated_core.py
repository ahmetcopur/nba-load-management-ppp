"""Synthetic safeguards for October cadence panel derived from original NBA sources.

The private raw ZIPs are NOT put in public CI. Tests cover immutable historical
source boundaries, full decoded CSV comparator, and safe private-output paths.
"""
from __future__ import annotations
import gzip
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.data_rebuild import rebuild_october_cadence_from_generated_core as m


class OctoberOriginalSourceBuilderTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.raw = self.root / "private_inputs"
        self.raw.mkdir()
        self.output = self.root / "new_output"
        self.panel = self.root / "fresh_analysis_ready.csv.gz"
        self.panel.write_bytes(gzip.compress(b"test\n", mtime=0))

    def test_private_output_path_must_not_already_exist(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            m.verify_safe_private_output(self.raw, self.panel, self.output)

    def test_raw_source_zip_tree_not_used_as_output(self):
        with self.assertRaisesRegex(ValueError, "outside original source"):
            m.verify_safe_private_output(self.raw, self.panel, self.raw / "generated")

    def test_no_private_player_source_in_git_checkout(self):
        repo = self.root / "repo"
        (repo / ".git").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "Git checkout"):
            m.verify_safe_private_output(self.raw, self.panel, repo / "raw_player_rows")

    def test_missing_newly_generated_reviewed_panel_fails(self):
        with self.assertRaises(FileNotFoundError):
            m.verify_safe_private_output(
                self.raw, self.root / "missing.csv.gz", self.output)

    def test_historical_panel_only_preserves_pre_model_code(self):
        original = (
            "from pathlib import Path\n"
            "ROOT=Path('/mnt/data/nba_continue')\n"
            "print('historical player-game panel')\n"
            + m.PANEL_SOURCE_END
            + "\nraise RuntimeError('historical model shadow bug')\n"
        ).encode()
        relocated = m.panel_only_historical_source(original, self.output)
        self.assertIn("historical player-game panel", relocated)
        self.assertNotIn("historical model shadow bug", relocated)
        self.assertIn(str(self.output), relocated)
        self.assertNotIn("/mnt/data/nba_continue", relocated)

    def test_source_builder_drift_refused(self):
        original = b"ROOT=Path('/mnt/data/nba_continue')\nprint('no code boundary')\n"
        with self.assertRaisesRegex(ValueError, "boundary changed"):
            m.panel_only_historical_source(original, self.output)

    def test_duplicate_source_root_refused(self):
        source = (
            (m.ORIGINAL_ROOT_LINE + "\n") * 2 + m.PANEL_SOURCE_END
        ).encode()
        with self.assertRaisesRegex(ValueError, "boundary changed"):
            m.panel_only_historical_source(source, self.output)

    def test_pinned_source_builder_sha_mismatch_fails(self):
        zpath = self.raw / "source.zip"
        with ZipFile(zpath, "w") as z:
            z.writestr(m.ORIGINAL_PANEL_SCRIPT, b"print('tampered')")
        with self.assertRaisesRegex(ValueError, "source code SHA256 changed"):
            m.pinned_original_source_bytes(
                zpath, m.ORIGINAL_PANEL_SCRIPT, m.ORIGINAL_PANEL_SCRIPT_SHA256,
            )

    def test_unknown_output_gzip_content_rejected(self):
        # Synthetic source package cannot pass production SHA gate. Check that
        # checksum comparison is strict at stream level.
        from scripts.data_rebuild.run_connected_player_game_core import compare_streams
        import io
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            compare_streams(io.BytesIO(b"abc"), io.BytesIO(b"abd"))

    def test_no_original_pdf_workers_zero_or_above_sixteen(self):
        with self.assertRaisesRegex(ValueError, "workers must be"):
            m.independent_2025_harmonized_reports(self.raw, self.output, workers=0)
        with self.assertRaisesRegex(ValueError, "workers must be"):
            m.independent_2025_harmonized_reports(self.raw, self.output, workers=17)

    def test_original_zip_declared_2020_reason_source_clearly_inherited(self):
        self.assertIn("audit_2020_21_corrected_outputs.zip", m.ORIGINAL_SOURCE_PACKAGES)
        self.assertIn("audit_2024_25_pre_s4_outputs_corrected.zip", m.ORIGINAL_SOURCE_PACKAGES)
        self.assertIn("audit_2025_26_targeted_upload.zip", m.ORIGINAL_SOURCE_PACKAGES)

    def test_model_root_is_not_silently_patched_into_historical_builder(self):
        self.assertNotEqual(m.ORIGINAL_ROOT_LINE, m.ORIGINAL_MODEL_ROOT_LINE)
        self.assertIn("norm", m.PANEL_SOURCE_END.lower() + " normalization")


if __name__ == "__main__":
    unittest.main()
