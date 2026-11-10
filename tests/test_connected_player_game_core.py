"""Synthetic checks for connected historical player-ID -> player-game reconstruction.

The real 94MB private core ZIP and its original box-score/crosswalk/covariate
companions are not on public CI. These tests check the CLI, fail-closed safety
and gzip-stable full-output comparison; private execution is a separate gate.
"""
from __future__ import annotations
import gzip
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings
from zipfile import ZipFile

from scripts.data_rebuild.run_connected_player_game_core import (
    COMPARISON_FILES, FINALIZER_MEMBER, check_private_output_path,
    compare_frozen_core_outputs, compare_streams, execute,
    extract_exact_member, source_pinned_finalizer,
    write_relocated_finalizer,
)


class ConnectedCoreRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archives = self.root / "private-input"
        self.archives.mkdir()
        self.output = self.root / "private-output"

    def test_direct_cli_can_load_without_custom_pythonpath(self):
        script = Path(__file__).resolve().parents[1] / "scripts/data_rebuild/run_connected_player_game_core.py"
        proc = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=self.root, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--archive-dir", proc.stdout)

    def test_clean_output_path_outside_input_is_allowed(self):
        check_private_output_path(self.archives, self.output)

    def test_existing_output_refused_to_prevent_overwrite(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            check_private_output_path(self.archives, self.output)

    def test_output_inside_source_archive_dir_is_refused(self):
        with self.assertRaisesRegex(ValueError, "outside the original archive"):
            check_private_output_path(self.archives, self.archives / "rebuild")

    def test_git_checkout_output_is_refused_even_when_nonexisting(self):
        repo_root = self.root / "repository"
        (repo_root / ".git").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "outside any Git checkout"):
            check_private_output_path(self.archives, repo_root / "private-output")

    def test_identical_decoded_streams_compare_with_sha256(self):
        out = compare_streams(io.BytesIO(b"alpha\nbeta\n"), io.BytesIO(b"alpha\nbeta\n"))
        self.assertTrue(out["identical_decoded_bytes"])
        self.assertEqual(out["decoded_bytes"], 11)
        self.assertEqual(out["decoded_sha256"], out["generated_decoded_sha256"])

    def test_one_byte_difference_fails(self):
        with self.assertRaisesRegex(ValueError, "Reconstructed output bytes differ"):
            compare_streams(io.BytesIO(b"a,b\n1,2\n"), io.BytesIO(b"a,b\n1,9\n"))

    def test_truncation_fails(self):
        with self.assertRaisesRegex(ValueError, "Reconstructed output bytes differ"):
            compare_streams(io.BytesIO(b"abc"), io.BytesIO(b"ab"))

    def test_known_member_extraction_is_byte_exact(self):
        zip_path = self.archives / "data.zip"
        with ZipFile(zip_path, "w") as zip_archive:
            zip_archive.writestr("safe/reference.csv", b"id,name\n1,test\n")
        destination = self.output / "reference.csv"
        extract_exact_member(zip_path, "safe/reference.csv", destination)
        self.assertEqual(destination.read_bytes(), b"id,name\n1,test\n")

    def test_missing_or_duplicate_member_is_refused(self):
        zip_path = self.archives / "data.zip"
        with ZipFile(zip_path, "w") as zip_archive:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                zip_archive.writestr("rows.csv", b"one")
                zip_archive.writestr("rows.csv", b"two")
        with self.assertRaisesRegex(ValueError, "Missing or duplicate source member"):
            extract_exact_member(zip_path, "rows.csv", self.output / "rows.csv")

    def test_all_ten_frozen_outputs_checked_with_gzip_timestamps_ignored(self):
        archive_path = self.archives / "core.zip"
        target = self.output / "nba_player_game_at_risk_core_v1"
        target.mkdir(parents=True)
        with ZipFile(archive_path, "w") as archive:
            for filename in COMPARISON_FILES:
                decoded = ("value," + filename + "\n").encode()
                if filename.endswith(".gz"):
                    reference = gzip.compress(decoded, mtime=0)
                    new_bytes = gzip.compress(decoded, mtime=1)
                    self.assertNotEqual(reference, new_bytes)
                else:
                    reference = new_bytes = decoded
                archive.writestr("nba_player_game_at_risk_core_v1/" + filename, reference)
                (target / filename).write_bytes(new_bytes)
        comparison = compare_frozen_core_outputs(archive_path, self.output)
        self.assertEqual(len(comparison), 10)
        self.assertTrue(all(item["identical_decoded_bytes"] for item in comparison.values()))

    def test_any_mismatched_final_output_blocks_acceptance(self):
        archive_path = self.archives / "core.zip"
        target = self.output / "nba_player_game_at_risk_core_v1"
        target.mkdir(parents=True)
        with ZipFile(archive_path, "w") as archive:
            for filename in COMPARISON_FILES:
                encoded = gzip.compress(b"same\n", mtime=0) if filename.endswith(".gz") else b"same\n"
                archive.writestr("nba_player_game_at_risk_core_v1/" + filename, encoded)
                (target / filename).write_bytes(encoded)
        (target / "summary_by_season.csv").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "Reconstructed output bytes differ"):
            compare_frozen_core_outputs(archive_path, self.output)

    def test_finalizer_source_must_have_original_pinned_sha(self):
        zip_path = self.archives / "nba_player_game_at_risk_core_v1.zip"
        with ZipFile(zip_path, "w") as archive:
            archive.writestr(FINALIZER_MEMBER, 'ROOT=Path("/mnt/data")\n# tampered\n')
        with self.assertRaisesRegex(ValueError, "historical finalizer source changed"):
            source_pinned_finalizer(self.archives)

    def test_root_redirection_is_single_known_line(self):
        self.output.mkdir()
        source = b'from pathlib import Path\nROOT=Path("/mnt/data")\nprint(ROOT)\n'
        target = write_relocated_finalizer(source, self.output)
        text = target.read_text()
        self.assertIn(repr(str(self.output.resolve())), text)
        self.assertNotIn('ROOT=Path("/mnt/data")', text)
        self.assertEqual(text.count("print(ROOT)"), 1)

    def test_missing_raw_input_fails_without_creating_result_directory(self):
        with self.assertRaises(FileNotFoundError):
            execute(self.archives, self.output, timeout_seconds=3)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
