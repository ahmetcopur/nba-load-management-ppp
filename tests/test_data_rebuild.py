"""Offline smoke tests for reproducibility tooling; no private NBA data required."""
import csv
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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




class SourceArchivePlanTests(unittest.TestCase):
    def make_archives(self, folder):
        """Synthetic stand-ins for the complete historical ZIP list."""
        spec = {}
        for _, archive, basename in restore.FILES:
            spec.setdefault(archive, []).append(f"old_project/final/{basename}")
        spec[restore.SELECTOR_ZIP] = [
            f"nested/selector/{basename}" for basename in restore.SELECTOR_NAMES
        ]
        for archive in restore.RAW_2025:
            spec[archive] = ["pdf/Injury-Report_2025-12-20_05PM.pdf"]
        for archive, members in spec.items():
            with zipfile.ZipFile(folder / archive, "w") as z:
                for member in members:
                    z.writestr(member, "test fixture\n")
        return spec

    def test_nested_zip_names_are_resolved_without_assuming_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            archive_folder = Path(d)
            self.make_archives(archive_folder)
            plan = restore.build_plan(archive_folder)
            self.assertEqual(len(plan), len(restore.FILES) + len(restore.SELECTOR_NAMES))
            self.assertEqual(len({dest for dest, _, _ in plan}), len(plan))
            self.assertTrue(any(member.startswith("old_project/final/")
                                for _, _, member in plan))

    def test_ambiguous_basename_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            archive_folder = Path(d)
            self.make_archives(archive_folder)
            archive = archive_folder / restore.FILES[0][1]
            with zipfile.ZipFile(archive, "a") as z:
                z.writestr("another/location/" + restore.FILES[0][2], "other")
            with self.assertRaisesRegex(ValueError, "found 2"):
                restore.build_plan(archive_folder)

    def test_missing_archive_is_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as d:
            archive_folder = Path(d)
            self.make_archives(archive_folder)
            (archive_folder / restore.SELECTOR_ZIP).unlink()
            with self.assertRaisesRegex(FileNotFoundError, "Missing archive"):
                restore.build_plan(archive_folder)

    def test_repeated_restore_detects_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            archive_folder, output = folder / "archives", folder / "output"
            archive_folder.mkdir()
            self.make_archives(archive_folder)
            plan = restore.build_plan(archive_folder)
            first = restore.restore(archive_folder, output, plan)
            self.assertEqual(len(first), len(plan) + len(restore.RAW_2025))
            second = restore.restore(archive_folder, output, plan)
            self.assertTrue(all(item["state"] == "unchanged" for item in second))
            target = output / restore.FILES[0][0]
            target.write_text("modified")
            with self.assertRaisesRegex(RuntimeError, "differs"):
                restore.restore(archive_folder, output, plan)

if __name__ == "__main__":
    unittest.main()
