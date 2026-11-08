"""Offline smoke tests for reproducibility tooling; no private NBA data required."""
import csv
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    path = ROOT / "scripts/data_rebuild" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compare = load("compare_panels")
restore = load("restore_historical_layout")


def csvfile(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["player_team_game_id", "value"])
        writer.writeheader()
        writer.writerows(rows)


class PanelComparisonTests(unittest.TestCase):
    def test_identical_panels(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "panel.csv"
            csvfile(path, [{"player_team_game_id": "g1|p1", "value": "0"}])
            self.assertTrue(compare.compare(path, path)["exact_match"])

    def test_modified_cell_detected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.csv", Path(d) / "b.csv"
            csvfile(a, [{"player_team_game_id": "g1|p1", "value": "0"}])
            csvfile(b, [{"player_team_game_id": "g1|p1", "value": "1"}])
            result = compare.compare(a, b)
            self.assertFalse(result["exact_match"])
            self.assertEqual(result["mismatched_cell_counts"]["value"], 1)

    def test_missing_key_detected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.csv", Path(d) / "b.csv"
            csvfile(a, [{"player_team_game_id": "g1|p1", "value": "0"}])
            csvfile(b, [{"player_team_game_id": "g2|p1", "value": "0"}])
            result = compare.compare(a, b)
            self.assertEqual(result["missing_keys"], 1)
            self.assertEqual(result["extra_keys"], 1)

    def test_duplicate_key_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.csv", Path(d) / "b.csv"
            csvfile(a, [{"player_team_game_id": "g1|p1", "value": "0"}] * 2)
            csvfile(b, [{"player_team_game_id": "g1|p1", "value": "0"}])
            with self.assertRaises(ValueError):
                compare.compare(a, b)


class ArchiveTests(unittest.TestCase):
    def test_extraction_is_repeatable_and_hash_checked(self):
        with tempfile.TemporaryDirectory() as d:
            archive, output = Path(d) / "source.zip", Path(d) / "test.csv"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("data/test.csv", "x\n1\n")
            with zipfile.ZipFile(archive) as z:
                self.assertEqual(restore.save_member(z, "data/test.csv", output)["state"], "restored")
                self.assertEqual(restore.save_member(z, "data/test.csv", output)["state"], "unchanged")
                output.write_text("tampered")
                with self.assertRaises(RuntimeError):
                    restore.save_member(z, "data/test.csv", output)


if __name__ == "__main__":
    unittest.main()
