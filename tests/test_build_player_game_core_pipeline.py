"""Offline tests for actually BUILDING the NBA core in an isolated workspace.

Synthetic fixtures only; original private ZIPs are deliberately never in CI.
"""
from __future__ import annotations

import gzip
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from scripts.data_rebuild import build_player_game_core_pipeline as pipeline


def make_gzip(data: bytes, mtime: int) -> bytes:
    target = io.BytesIO()
    with gzip.GzipFile(fileobj=target, mode="wb", mtime=mtime) as gz:
        gz.write(data)
    return target.getvalue()


class RebuildCorePipelineTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.archives = self.root / "originals"
        self.archives.mkdir()
        self.work = self.root / "rebuild"
        self.work.mkdir()

    def test_decoded_gzip_compare_ignores_header_timestamp_only(self):
        original = b"id,status\n1,Out\n2,Available\n"
        frozen = self.archives / "core.zip"
        name = "nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz"
        with ZipFile(frozen, "w") as z:
            z.writestr(name, make_gzip(original, mtime=5))
        local = self.work / "player_game_panel_core.csv.gz"
        local.write_bytes(make_gzip(original, mtime=90))
        observed = pipeline.csv_content_sha256(local, is_gzip=True)
        expected = pipeline.frozen_csv_content_sha256(frozen, name, is_gzip=True)
        self.assertEqual(observed, expected)

    def test_generated_csv_change_is_not_accepted(self):
        original = b"id,status\n1,Out\n"
        with ZipFile(self.archives / pipeline.CORE_ZIP, "w") as z:
            z.writestr("nba_player_game_at_risk_core_v1/a.csv.gz",
                       make_gzip(original, mtime=5))
        output = self.work / "nba_player_game_at_risk_core_v1"
        output.mkdir()
        (output / "a.csv.gz").write_bytes(make_gzip(b"id,status\n1,Available\n", mtime=90))
        with patch.object(pipeline, "OUTPUT_NAMES", ("a.csv.gz",)):
            with self.assertRaisesRegex(ValueError, "differs from frozen CSV"):
                pipeline.compare_core_outputs(self.archives, self.work)

    def test_exact_source_member_staged_in_private_workspace(self):
        with ZipFile(self.archives / "original.zip", "w") as z:
            z.writestr("source/n.csv", "x,y\n1,2\n")
        original = pipeline.STAGED_INPUTS
        with patch.object(pipeline, "STAGED_INPUTS",
                          (("original.zip", "source/n.csv", "subdir/staged.csv"),)):
            pipeline.stage_input_files(self.archives, self.work)
            self.assertEqual((self.work / "subdir/staged.csv").read_text(),
                             "x,y\n1,2\n")
            with self.assertRaises(FileExistsError):
                pipeline.stage_input_files(self.archives, self.work)
        self.assertEqual(pipeline.STAGED_INPUTS, original)

    def test_missing_source_member_rejected(self):
        with ZipFile(self.archives / "original.zip", "w") as z:
            z.writestr("source/a.csv", "a\n")
        with patch.object(pipeline, "STAGED_INPUTS",
                          (("original.zip", "source/absent.csv", "stage.csv"),)):
            with self.assertRaisesRegex(ValueError, "Missing/duplicate"):
                pipeline.stage_input_files(self.archives, self.work)

    def test_original_finalizer_is_pinned_and_only_root_retargeted(self):
        script = (b'from pathlib import Path\nROOT=Path("/mnt/data")\n'
                  b'print(ROOT / "original.csv")\n')
        with ZipFile(self.archives / pipeline.CORE_ZIP, "w") as z:
            z.writestr(pipeline.FINALIZER_MEMBER, script)
        with patch.object(pipeline, "FINALIZER_SHA256",
                          hashlib.sha256(script).hexdigest()):
            adapter = pipeline.original_finalizer_adapter(self.archives, self.work)
        observed = adapter.read_bytes()
        self.assertIn(str(self.work).encode(), observed)
        self.assertNotIn(b'ROOT=Path("/mnt/data")', observed)
        self.assertIn(b'print(ROOT / "original.csv")', observed)

    def test_changed_original_finalizer_rejected(self):
        with ZipFile(self.archives / pipeline.CORE_ZIP, "w") as z:
            z.writestr(pipeline.FINALIZER_MEMBER, b"print('imposter')\n")
        with self.assertRaisesRegex(ValueError, "finalizer SHA-256 differs"):
            pipeline.original_finalizer_adapter(self.archives, self.work)

    def test_existing_output_directory_rejected_without_side_effects(self):
        marker = self.work / "do_not_touch"
        marker.write_text("preserve")
        with self.assertRaises(FileExistsError):
            pipeline.run_pipeline(self.archives, self.work)
        self.assertEqual(marker.read_text(), "preserve")

    def test_output_inside_source_directory_rejected(self):
        with self.assertRaisesRegex(ValueError, "separate from"):
            pipeline.run_pipeline(self.archives, self.archives / "child")

    def test_original_source_zip_tamper_rejected(self):
        with patch.object(pipeline, "IDENTITY_ZIPS",
                          {"changed.zip": hashlib.sha256(b"expected").hexdigest()}):
            with patch.object(pipeline, "GAME_ZIP", "game.zip"):
                with patch.object(pipeline, "GAME_SHA256",
                                  hashlib.sha256(b"game").hexdigest()):
                    (self.archives / "changed.zip").write_bytes(b"tampered")
                    (self.archives / "game.zip").write_bytes(b"game")
                    with self.assertRaisesRegex(ValueError, "Original source ZIP changed"):
                        pipeline.verify_archives(self.archives)


if __name__ == "__main__":
    unittest.main()
