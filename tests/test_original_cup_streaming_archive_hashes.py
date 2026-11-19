"""Memory-bounded SHA-256 and original archive digest gating tests.

No genuine research ZIP is present in public CI; these are synthetic binary
files and intentional hash mismatches only. They do not establish anything
about the user's immutable original ZIP content.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.data_rebuild import hash_original_archive_streaming as streaming
from scripts.data_rebuild import run_original_cup_private_source_acceptance as runner


class OriginalArchiveStreamingDigestTests(unittest.TestCase):
    def test_exact_sha256_matches_python_for_multi_chunk_binary(self):
        payload=(b"\x00\xfforiginal-archive\n"*90000)+b"\x00last"
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"synthetic-private-cup.zip"
            file.write_bytes(payload)
            expected=hashlib.sha256(payload).hexdigest()
            for block in (1,7,256,8192,65536,1<<20,1<<21):
                self.assertEqual(streaming.sha256_file(file,block),expected)

    def test_empty_archive_has_correct_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"empty.dat"
            path.touch()
            self.assertEqual(streaming.sha256_file(path),
                             hashlib.sha256(b"").hexdigest())

    def test_invalid_chunk_size_fails(self):
        with self.assertRaisesRegex(ValueError,"positive"):
            streaming.sha256_file(Path("not-used.zip"),0)

    def test_missing_source_file_fails(self):
        with self.assertRaises(FileNotFoundError):
            streaming.sha256_file(Path("/no/such/private-original-source.zip"))

    def test_runner_hash_is_streamed_and_never_uses_Path_read_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cup=Path(tmp)/"fake-cup.zip"
            freeze=Path(tmp)/"fake-freeze.zip"
            cup.write_bytes(b"correctly-digested but fictional Cup")
            freeze.write_bytes(b"correctly-digested but fictional freeze")
            with mock.patch.object(Path,"read_bytes",
                                   side_effect=AssertionError("no full ZIP read allowed")):
                with self.assertRaisesRegex(ValueError,"Cup ZIP SHA-256 mismatch"):
                    runner.original_sha_pins(cup,freeze)

    def test_runner_validates_both_streamed_pins_when_testing_with_fake_pins(self):
        with tempfile.TemporaryDirectory() as tmp:
            cup=Path(tmp)/"fake-cup.zip";freeze=Path(tmp)/"fake-freeze.zip"
            cup.write_bytes(b"synthetic-Cup");freeze.write_bytes(b"synthetic-Freeze")
            with mock.patch.object(runner.group_prior,"ARCHIVE_SHA256",
                                   hashlib.sha256(cup.read_bytes()).hexdigest()), \
                 mock.patch.object(runner.tv,"FREEZE_SHA",
                                   hashlib.sha256(freeze.read_bytes()).hexdigest()):
                with mock.patch.object(Path,"read_bytes",
                                       side_effect=AssertionError("no full ZIP read allowed")):
                    runner.original_sha_pins(cup,freeze)
                freeze.write_bytes(b"one byte difference in frozen original")
                with self.assertRaisesRegex(ValueError,"freeze ZIP SHA-256 mismatch"):
                    runner.original_sha_pins(cup,freeze)


if __name__ == "__main__":
    unittest.main()
