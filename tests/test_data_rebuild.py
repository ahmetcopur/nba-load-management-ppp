"""Offline tests for NBA data-rebuild tooling; no original NBA archives needed."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "scripts/data_rebuild" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compare = load("compare_panels")
restore = load("restore_historical_layout")
reparse = load("reparse_2025_selected")
verify = load("verify_cadence_panel")


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
    def test_hash_checked_copy_and_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            archive, output = Path(d) / "source.zip", Path(d) / "test.csv"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("data/test.csv", "x\n1\n")
            with zipfile.ZipFile(archive) as z:
                self.assertEqual(restore.copy_member(z, "data/test.csv", output)["status"], "copied")
                self.assertEqual(restore.copy_member(z, "data/test.csv", output)["status"], "already-matched")
                output.write_text("tampered")
                with self.assertRaises(ValueError):
                    restore.copy_member(z, "data/test.csv", output)

    def test_unique_basename_lookup_and_ambiguity(self):
        with tempfile.TemporaryDirectory() as d:
            archive = Path(d) / "source.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("prefix/target.csv", "x\n")
            with zipfile.ZipFile(archive) as z:
                self.assertEqual(restore.resolve_member(z, "other/target.csv"), "prefix/target.csv")
            with zipfile.ZipFile(archive, "a") as z:
                z.writestr("duplicate/target.csv", "x\n")
            with zipfile.ZipFile(archive) as z:
                with self.assertRaises(ValueError):
                    restore.resolve_member(z, "other/target.csv")

    def test_archive_preflight_validates_selector_and_original_files(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "archives", Path(d) / "historical"
            src.mkdir()
            byarchive = {}
            for destination, archive, preferred, optional in restore.INPUTS:
                if not optional:
                    byarchive.setdefault(archive, []).append((f"source_bundle/{preferred}", "test\n"))
            for basename in restore.SELECTOR_FILES:
                byarchive.setdefault(restore.SELECTOR_ZIP, []).append(
                    (f"selector/{basename}", "snapshot_basename,published_timestamp_utc\n"
                     "Injury-Report_2025-12-19_05PM.pdf,2025-12-19T22:30:00Z\n"))
            for raw in restore.RAW_2025:
                byarchive.setdefault(raw, []).append(
                    ("pdf/Injury-Report_2025-12-19_05PM.pdf", "%PDF-synthetic"))
            for name, members in byarchive.items():
                with zipfile.ZipFile(src / name, "w") as z:
                    for path, body in members:
                        z.writestr(path, body)
            plan = restore.plan(src)
            self.assertEqual(sum(x.get("status") == "optional-absent" for x in plan), 1)
            self.assertEqual(len(plan), len(restore.INPUTS) + len(restore.SELECTOR_FILES))
            restored = restore.restore(src, out)
            self.assertEqual(len(restored), len(plan) + len(restore.RAW_2025))
            self.assertEqual(reparse.check_inputs(out), 1)
            # A clean archive/restore is not a completed panel replay.
            self.assertFalse((out / "cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv").exists())

    def test_silent_parser_error_in_log_is_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "cadence_work/season_parsed/2025-26"
            folder.mkdir(parents=True)
            (folder / "s1_parse_log_harmonized_selected.csv").write_text(
                "source_file,status\nx.pdf,parse_error\n")
            (folder / "s1_snapshot_rows_harmonized_selected.csv").write_text(
                "source_file,matchup_norm,player_name,current_status,reason\n"
                "x.pdf,LAL@BOS,Someone,Out,Injury\n")
            with self.assertRaises(RuntimeError):
                reparse.verify_outputs(Path(d), 1)


if __name__ == "__main__":
    unittest.main()
