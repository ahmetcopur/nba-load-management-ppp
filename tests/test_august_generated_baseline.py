"""Source-identity and strict TV rekey separation in August regression runner."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.data_rebuild import run_august_released_suite_from_release as runner


class RebuiltAugustBaselineTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.shared = self.root / "pinned_shared"
        self.shared.mkdir()
        (self.shared / runner.TV).parent.mkdir(parents=True)
        (self.shared / runner.TV).write_text("TV original\n")
        (self.shared / runner.PANEL).parent.mkdir(parents=True)
        (self.shared / runner.PANEL).write_bytes(b"original frozen risk panel")
        original_script = self.shared / runner.EXECUTED / "teststage" / "run.py"
        original_script.parent.mkdir(parents=True)
        original_script.write_text("from pathlib import Path\nROOT='/mnt/data'\nprint(ROOT)\n")
        self.generated = self.root / "new_generated_baseline.csv.gz"
        self.generated.write_bytes(b"independently built CSV input")

    def test_new_baseline_stages_without_any_corrected_tv_rekey(self):
        output = self.root / "baseline"
        with patch.object(runner, "repair_announcement_fixture_keys",
                          side_effect=AssertionError("baseline must not rekey TV")):
            provenance, rekeys = runner.prepare(
                self.shared, output, "teststage", ["run.py"], self.generated,
                rekey_corrected_tv=False)
        self.assertIsNone(rekeys)
        self.assertEqual(len(provenance), 1)
        for relative in runner.PANEL_LOCATIONS:
            self.assertEqual((output / runner.SANDBOX / relative).read_bytes(),
                             self.generated.read_bytes())
        self.assertEqual((output / runner.SANDBOX / runner.TV_LOCATION).read_text(),
                         "TV original\n")

    def test_corrected_panel_rekeying_only_when_explicit(self):
        output = self.root / "corrected"
        with patch.object(runner, "repair_announcement_fixture_keys",
                          return_value={"fixture_keys_repaired": 2}) as mock:
            _, rekeys = runner.prepare(
                self.shared, output, "teststage", ["run.py"], self.generated,
                rekey_corrected_tv=True)
        mock.assert_called_once()
        self.assertEqual(rekeys["fixture_keys_repaired"], 2)

    def test_no_panel_cannot_rekey_tv(self):
        with self.assertRaisesRegex(ValueError, "only with a corrected risk panel"):
            runner.prepare(self.shared, self.root / "bad", "teststage",
                           ["run.py"], None, rekey_corrected_tv=True)

    def test_existing_baseline_sandbox_not_overwritten(self):
        destination = self.root / "already"
        destination.mkdir()
        marker = destination / "preserve"
        marker.write_text("existing")
        with self.assertRaises(FileExistsError):
            runner.prepare(self.shared, destination, "teststage",
                           ["run.py"], self.generated, rekey_corrected_tv=False)
        self.assertEqual(marker.read_text(), "existing")


if __name__ == "__main__":
    unittest.main()
