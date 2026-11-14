"""Offline smoke tests for reproducibility tooling; no private NBA data required."""
import csv
import gzip
import hashlib
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
parser2025 = load("reparse_2025_selected")
panelcheck = load("validate_cadence_panel")
modelcheck = load("compare_stage6_models")


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

    def test_conflicting_player_alias_archives_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            archive_folder = Path(d)
            self.make_archives(archive_folder)
            for name, value in (
                ("nba_player_crosswalk_final_v1.zip", "player_id=1\n"),
                ("nba_player_game_at_risk_core_v1.zip", "player_id=2\n")
            ):
                with zipfile.ZipFile(archive_folder / name, "a") as z:
                    z.writestr("metadata/player_alias_table.csv", value)
            with self.assertRaisesRegex(ValueError, "Conflicting player alias"):
                restore.build_plan(archive_folder)

    def test_repeated_restore_detects_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            archive_folder, output = folder / "archives", folder / "output"
            archive_folder.mkdir()
            self.make_archives(archive_folder)
            plan = restore.build_plan(archive_folder)
            manifests = restore.archive_manifests(archive_folder, plan)
            self.assertEqual(len(manifests),
                             len({name for _, name, _ in plan} | set(restore.RAW_2025)))
            for record in manifests:
                self.assertEqual(record["sha256"],
                                 restore.sha256(archive_folder / record["archive"]))
            first = restore.restore(archive_folder, output, plan)
            self.assertEqual(len(first), len(plan) + len(restore.RAW_2025))
            second = restore.restore(archive_folder, output, plan)
            self.assertTrue(all(item["state"] == "unchanged" for item in second))
            target = output / restore.FILES[0][0]
            target.write_text("modified")
            with self.assertRaisesRegex(RuntimeError, "differs"):
                restore.restore(archive_folder, output, plan)



class Selected2025PdfAuditTests(unittest.TestCase):
    def make_input(self, root, conflicting=False):
        from pathlib import Path
        selector = root / parser2025.SELECTOR
        selector.parent.mkdir(parents=True, exist_ok=True)
        with selector.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["snapshot_basename", "game_id",
                                                        "published_timestamp_utc"])
            writer.writeheader()
            for i in range(1230):
                writer.writerow({"snapshot_basename": "selected.pdf", "game_id": i,
                                 "published_timestamp_utc": "2025-11-01T12:00:00Z"})
        for i, name in enumerate(parser2025.RAW_ZIPS):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target, "w") as z:
                if i == 0 or conflicting:
                    z.writestr("old/pdf/selected.pdf", f"PDF content {i}" if conflicting else "same")
                else:
                    z.writestr("old/pdf/unselected.pdf", "different")

    def test_missing_selected_pdf_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_input(root)
            with zipfile.ZipFile(root / parser2025.RAW_ZIPS[0], "w") as z:
                z.writestr("old/pdf/unselected.pdf", "other")
            with self.assertRaisesRegex(ValueError, "missing"):
                parser2025.audit_selected(root)

    def test_selected_pdf_present(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_input(root)
            report = parser2025.audit_selected(root)
            self.assertEqual(report["selected_games"], 1230)
            self.assertEqual(report["distinct_selected_pdfs"], 1)

    def test_selected_pdf_against_full_inventory_not_primary_selector(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_input(root)
            metadata = root / "inventory"
            metadata.mkdir()
            inventory_path = metadata / "injury_report_inventory.csv.gz"
            source_zip = Path(parser2025.RAW_ZIPS[0]).name

            def write_inventory(digest):
                with gzip.open(inventory_path, "wt", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=[
                        "archive", "archive_member", "pdf_present",
                        "computed_sha256", "manifest_sha256", "hash_status"])
                    writer.writeheader()
                    writer.writerow({
                        "archive": source_zip, "archive_member": "old/pdf/selected.pdf",
                        "pdf_present": "true", "computed_sha256": digest,
                        "manifest_sha256": digest, "hash_status": "match"})
                    writer.writerow({
                        "archive": source_zip, "archive_member": "other/unselected.pdf",
                        "pdf_present": "true", "computed_sha256": "0" * 64,
                        "manifest_sha256": "0" * 64, "hash_status": "match"})

            # The canonical/latest-pre-tip primary selection explicitly differs
            # from the harmonized selected PDF; audit must NOT read this map.
            with gzip.open(metadata / "primary_sample_report_map.csv.gz",
                           "wt", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["season", "archive_member"])
                writer.writeheader()
                writer.writerow({"season": "2025-26", "archive_member": "other/primary_only.pdf"})

            write_inventory(hashlib.sha256(b"same").hexdigest())
            self.assertTrue(parser2025.audit_selected(root, metadata)[
                "source_inventory_sha256_verified"])
            write_inventory("f" * 64)
            with self.assertRaisesRegex(ValueError, "digest or member mismatch"):
                parser2025.audit_selected(root, metadata)

    def make_parse_log(self, root, status="ok", extracted_rows=2):
        folder = root / "cadence_work/season_parsed/2025-26"
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "s1_parse_log_harmonized_selected.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=[
                "source_file", "snapshot_timestamp_utc", "status",
                "extracted_rows", "warning"])
            writer.writeheader()
            writer.writerow({
                "source_file": "selected.pdf",
                "snapshot_timestamp_utc": "2025-11-01T12:00:00Z",
                "status": status,
                "extracted_rows": str(extracted_rows),
                "warning": ""})
        with (folder / "s1_snapshot_rows_harmonized_selected.csv").open(
                "w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["player_name"])
            writer.writeheader()
            for i in range(extracted_rows):
                writer.writerow({"player_name": f"P{i}"})

    def test_2025_parser_log_fully_reconciles(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_input(root)
            self.make_parse_log(root)
            result = parser2025.verify_parse_log(root)
            self.assertEqual(result["successful_pdf_parses"], 1)
            self.assertEqual(result["parsed_player_rows"], 2)

    def test_2025_parser_caught_error_blocks_replay(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_input(root)
            self.make_parse_log(root, status="parse_error", extracted_rows=0)
            with self.assertRaisesRegex(RuntimeError, "failed/unknown statuses"):
                parser2025.verify_parse_log(root)

    def test_2025_parser_zero_rows_requires_manual_approval(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_input(root)
            self.make_parse_log(root, status="zero_rows", extracted_rows=0)
            with self.assertRaisesRegex(RuntimeError, "zero rows"):
                parser2025.verify_parse_log(root)
            result = parser2025.verify_parse_log(root, allow_zero_rows=True)
            self.assertTrue(result["zero_rows_explicitly_allowed"])

    def test_2025_parser_missing_selected_log_blocks_replay(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_input(root)
            self.make_parse_log(root)
            folder = root / "cadence_work/season_parsed/2025-26"
            with (folder / "s1_parse_log_harmonized_selected.csv").open(
                    "w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=[
                    "source_file", "snapshot_timestamp_utc", "status", "extracted_rows"])
                writer.writeheader()
                writer.writerow({
                    "source_file": "unexpected.pdf",
                    "snapshot_timestamp_utc": "2025-11-01T12:00:00Z",
                    "status": "ok", "extracted_rows": 2})
            with self.assertRaisesRegex(RuntimeError, "does not match selected snapshots"):
                parser2025.verify_parse_log(root)

    def test_conflicting_duplicate_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_input(root, conflicting=True)
            with self.assertRaisesRegex(ValueError, "conflicting"):
                parser2025.audit_selected(root)



class CadencePanelInvariantTests(unittest.TestCase):
    def make_panel(self, path, invalid_onset=False):
        import pandas as pd
        seasons = sorted(panelcheck.SEASONS)
        data = [{
            "player_team_game_id": f"g{i}|team|p",
            "game_id": f"g{i}",
            "season": season,
            "at_risk_for_new_onset_harm": i == 0 and not invalid_onset,
            "absence_onset_harm": i == 0,
            "absence_now_harm": i == 0,
        } for i, season in enumerate(seasons)]
        pd.DataFrame(data).to_csv(path, index=False)

    def test_invariant_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "valid.csv"
            self.make_panel(path)
            r = panelcheck.inspect_panel(path)
            self.assertEqual(r["rows"], 6)
            self.assertEqual(r["onsets"], 1)

    def test_onset_without_risk_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.csv"
            self.make_panel(path, invalid_onset=True)
            with self.assertRaisesRegex(ValueError, "outside the onset risk set"):
                panelcheck.inspect_panel(path)

    def test_frozen_expected_counts_do_not_accept_fabricated_small_panel(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "small.csv"
            self.make_panel(path)
            with self.assertRaisesRegex(ValueError, "counts differ"):
                panelcheck.inspect_panel(path, expect_frozen=True)



class Stage6ModelComparisonTests(unittest.TestCase):
    def make_models(self):
        return [
            {"definition": definition, "controls": controls, "n": "180530",
             "estimate_pp": "1.2345", "se_pp": "0.123", "low_pp": "0.993",
             "high_pp": "1.476", "p": "0.02"}
            for definition, controls in sorted(modelcheck.EXPECTED)
        ]

    def test_stage6_exact_replay(self):
        rows = self.make_models()
        self.assertTrue(modelcheck.compare(rows, rows)["matched"])

    def test_stage6_changed_effect_fails(self):
        before, after = self.make_models(), self.make_models()
        after[0]["estimate_pp"] = "1.5"
        self.assertFalse(modelcheck.compare(before, after)["matched"])

    def test_stage6_missing_specification_fails(self):
        rows = self.make_models()
        self.assertFalse(modelcheck.compare(rows, rows[:-1])["matched"])

if __name__ == "__main__":
    unittest.main()
