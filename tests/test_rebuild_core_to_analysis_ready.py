"""Safe CLI orchestration tests for the real core->analysis-ready pipeline."""
import tempfile
import unittest
from pathlib import Path

from scripts.data_rebuild.rebuild_core_to_analysis_ready import (
    REQUIRED_PRIVATE_ZIPS, plan
)


class ConnectedRebuildPlanTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.archives = self.base / "archives"
        self.archives.mkdir()
        for name in REQUIRED_PRIVATE_ZIPS:
            (self.archives / name).write_bytes(b"synthetic-placeholder")

    def test_launches_actual_core_and_analysis_builders(self):
        out = self.base / "new_run"
        core, analysis = plan(self.archives, out)
        self.assertIn("build_player_game_core_pipeline.py", core[1])
        self.assertIn("build_analysis_ready_from_generated_core.py", analysis[1])
        self.assertIn("player_game_panel_core.csv.gz", analysis[analysis.index("--generated-core") + 1])
        self.assertIn(str(out / "core_rebuild"), core)
        self.assertIn(str(out / "analysis_ready_rebuild"), analysis)
        self.assertFalse(out.exists())

    def test_original_archive_missing_fails_before_creation(self):
        (self.archives / REQUIRED_PRIVATE_ZIPS[-1]).unlink()
        out = self.base / "no_run"
        with self.assertRaisesRegex(FileNotFoundError, "required original private ZIP packages absent"):
            plan(self.archives, out)
        self.assertFalse(out.exists())

    def test_existing_output_is_never_overwritten(self):
        out = self.base / "existing"
        out.mkdir()
        (out / "preserve.txt").write_text("stay")
        with self.assertRaises(FileExistsError):
            plan(self.archives, out)
        self.assertEqual((out / "preserve.txt").read_text(), "stay")

    def test_source_path_inside_output_rejected(self):
        with self.assertRaisesRegex(ValueError, "separate directory"):
            plan(self.archives, self.archives / "new_run")

    def test_output_ancestor_of_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "separate directory"):
            plan(self.archives, self.base)

    def test_invalid_timeout_rejected(self):
        with self.assertRaisesRegex(ValueError, "Timeout must be positive"):
            plan(self.archives, self.base / "new_run", timeout=0)


if __name__ == "__main__":
    unittest.main()
