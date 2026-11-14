"""No private inputs: fail-closed tests for historical star-source continuation."""
from __future__ import annotations
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from scripts.data_rebuild.run_connected_star_enrichment import (
    STAR_OUTPUTS, STAR_BUILDER_MEMBER, STAR_ZIP,
    compare_original_star_outputs, immutable_original_star_source,
    validate_private_star_destination, write_root_relocated_builder,
)
from scripts.data_rebuild.reproduce_core_and_stars import reproduce


class ConnectedStarSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "private-zips"
        self.work = self.root / "private-work"
        self.source.mkdir()
        self.work.mkdir()
        self.report = self.work / "connected_core_reproduction_report.json"
        self.report.write_text(json.dumps({
            "status": "pass",
            "all_ten_outputs_identical_after_gzip_decoding": True,
        }))

    def test_source_based_star_cli_imports_without_explicit_pythonpath(self):
        script = Path(__file__).resolve().parents[1] / "scripts/data_rebuild/run_connected_star_enrichment.py"
        result = subprocess.run([sys.executable, str(script), "--help"],
            cwd=self.root, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--core-run-dir", result.stdout)

    def test_single_command_master_cli_imports_from_clean_cwd(self):
        script = Path(__file__).resolve().parents[1] / "scripts/data_rebuild/reproduce_core_and_stars.py"
        result = subprocess.run([sys.executable, str(script), "--help"],
            cwd=self.root, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--output-dir", result.stdout)

    def test_new_private_star_destination_is_valid(self):
        validate_private_star_destination(self.source, self.work)

    def test_existing_star_output_blocks_destructive_original_script(self):
        (self.work / "nba_player_game_at_risk_star_v1").mkdir()
        with self.assertRaises(FileExistsError):
            validate_private_star_destination(self.source, self.work)

    def test_existing_star_zip_blocks_original_unlink(self):
        (self.work / STAR_ZIP).write_bytes(b"prior private output")
        with self.assertRaisesRegex(FileExistsError, "previous generated star ZIP"):
            validate_private_star_destination(self.source, self.work)

    def test_missing_core_pass_report_blocks_star_stage(self):
        self.report.unlink()
        with self.assertRaisesRegex(FileNotFoundError, "successful connected core"):
            validate_private_star_destination(self.source, self.work)

    def test_false_core_pass_report_blocks_star_stage(self):
        self.report.write_text(json.dumps({"status": "failed",
                                            "all_ten_outputs_identical_after_gzip_decoding": True}))
        with self.assertRaisesRegex(ValueError, "has not passed"):
            validate_private_star_destination(self.source, self.work)

    def test_changed_original_star_zip_is_rejected(self):
        archive = self.source / STAR_ZIP
        with ZipFile(archive, "w") as z:
            z.writestr(STAR_BUILDER_MEMBER, b"print('malicious')\n")
        with self.assertRaisesRegex(ValueError, "ZIP hash changed"):
            immutable_original_star_source(archive)

    def test_relocation_changes_only_the_four_original_root_prefixes(self):
        original = (b"CORE = Path('/mnt/data/core')\n"
                    b"OUT = Path('/mnt/data/star')\n"
                    b"ZIP = Path('/mnt/data/star.zip')\n"
                    b"copy('/mnt/data/script.py')\n")
        adapted = write_root_relocated_builder(original, self.work)
        self.assertEqual((self.work / "build_star_status_v1.py").read_bytes(), original)
        self.assertNotIn("/mnt/data/", adapted.read_text())
        self.assertEqual(adapted.read_text().count(str(self.work.resolve())), 4)

    def test_synthetic_star_archive_matches_all_twelve_outputs_even_when_gzip_header_changes(self):
        source = self.source / STAR_ZIP
        out = self.work / "nba_player_game_at_risk_star_v1"
        out.mkdir()
        with ZipFile(source, "w") as zipfile:
            for filename in STAR_OUTPUTS:
                decoded = ("file," + filename + "\n").encode()
                if filename.endswith(".gz"):
                    expected = gzip.compress(decoded, mtime=0)
                    actual = gzip.compress(decoded, mtime=100)
                    self.assertNotEqual(expected, actual)
                else:
                    expected = actual = decoded
                zipfile.writestr("nba_player_game_at_risk_star_v1/" + filename, expected)
                (out / filename).write_bytes(actual)
        checked = compare_original_star_outputs(source, self.work)
        self.assertEqual(len(checked), 12)
        self.assertTrue(all(x["identical_decoded_bytes"] for x in checked.values()))

    def test_any_star_dataset_change_fails(self):
        source = self.source / STAR_ZIP
        out = self.work / "nba_player_game_at_risk_star_v1"
        out.mkdir()
        with ZipFile(source, "w") as zipfile:
            for filename in STAR_OUTPUTS:
                encoded = gzip.compress(b"data\n", mtime=0) if filename.endswith(".gz") else b"data\n"
                zipfile.writestr("nba_player_game_at_risk_star_v1/" + filename, encoded)
                (out / filename).write_bytes(encoded)
        (out / "star_award_history.csv").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Reconstructed output bytes differ"):
            compare_original_star_outputs(source, self.work)

    def test_master_fails_before_core_outputs_if_star_package_missing(self):
        new_dir = self.root / "not_created"
        with self.assertRaises(FileNotFoundError):
            reproduce(self.source, new_dir)
        self.assertFalse(new_dir.exists())


if __name__ == "__main__":
    unittest.main()
