"""Synthetic guards for consuming regenerated canonical selector inputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.data_rebuild import inject_generated_canonical_selectors as handoff
from scripts.data_rebuild import reproduce_final_datasets as final


class SelectorHandoffTests(unittest.TestCase):
    def prepare(self, root: Path):
        generated = root / "generated"
        target = root / "historical"
        (target / handoff.RELATIVE).mkdir(parents=True)
        generated.mkdir()
        filename = "2020-21_game_snapshot_join_harmonized_canonical.csv"
        source = generated / filename
        archived = target / handoff.RELATIVE / filename
        source.write_text("game_id,published_timestamp_utc\nG1,2020-12-23T00:00:00+00:00\n")
        archived.write_text("game_id,published_timestamp_utc\nG1,2020-12-23T00:00:00+00:00\n")
        manifest = {"all_selected_season_cases_passed": True, "cases": [{}, {}, {}, {}],
                    "generated_selector_tables": {filename: {
                        "rows": 1, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        "generated_from_original_pdfs_directly": False,
                        "input_rows_are_pinned_historical_parser_outputs": True}}}
        (generated / "selector_replay_manifest.json").write_text(json.dumps(manifest))
        return generated, target, archived, filename

    def test_verified_generated_bytes_replace_historical_october_input(self):
        with tempfile.TemporaryDirectory() as directory:
            generated, target, archived, filename = self.prepare(Path(directory))
            with patch.object(handoff, "EXPECTED", {filename: (
                    ["game_id"], frozenset({"published_timestamp_utc"}), 1)}):
                result = handoff.inject(generated, target, target / "handoff.json")
                self.assertTrue(result["generated_selectors_fed_to_october_historical_builder"])
                self.assertEqual(archived.read_bytes(), (generated / filename).read_bytes())
                with self.assertRaises(FileExistsError):
                    handoff.inject(generated, target, target / "handoff.json")

    def test_selector_timestamp_drift_blocks_substitution(self):
        with tempfile.TemporaryDirectory() as directory:
            generated, target, archived, filename = self.prepare(Path(directory))
            archived.write_text("game_id,published_timestamp_utc\nG1,2020-12-23T00:30:00+00:00\n")
            original = archived.read_bytes()
            with patch.object(handoff, "EXPECTED", {filename: (
                    ["game_id"], frozenset({"published_timestamp_utc"}), 1)}):
                with self.assertRaisesRegex(ValueError, "canonical outputs drift"):
                    handoff.inject(generated, target, target / "handoff.json")
            self.assertEqual(archived.read_bytes(), original)

    def test_optional_runner_stage_feeds_october_builder_and_blocks_missing_s4(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            jobs = final.stage_commands(p / "archives", p / "out", verify_original_pdfs=False,
                                        rebuild_2020_2024_selectors=True)
            names = [name for name, _ in jobs]
            self.assertLess(names.index("00c_historical_parser_selector_algorithm_replay"),
                            names.index("03_frozen_cadence"))
            self.assertIn("--generated-selector-dir", dict(jobs)["03_frozen_cadence"])
            archives = p / "archives"
            archives.mkdir()
            with patch.object(final, "REQUIRED_ZIPS", ()), patch.object(final, "RAW_PDF_EXTRA_ZIPS", ()), \
                 patch.object(final, "SOURCE_HASHES", {}), patch.object(final, "SELECTOR_SCHEDULE_EXTRA_ZIPS", {"missing.zip": "a"*64}):
                with self.assertRaisesRegex(ValueError, "Selector schedule ZIP"):
                    final.preflight(archives, p / "out", False,
                                    rebuild_2020_2024_selectors=True)

    def test_fresh_2020_pdf_rows_have_exact_stage_order_and_no_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "requires original-PDF"):
                final.stage_commands(root, root / "out", verify_original_pdfs=False,
                                     raw_2020_selector=True)
            stages = dict(final.stage_commands(root, root / "out", verify_original_pdfs=True,
                                               rebuild_2020_2024_selectors=True,
                                               raw_2020_selector=True))
            self.assertIn("--emit-full-2020-source-rows", stages["00_independent_original_six_pdf_baseline"])
            selector = stages["00c_historical_parser_selector_algorithm_replay"]
            self.assertIn("--fresh-2020-source-rows", selector)
            self.assertIn("--fresh-2020-acceptance", selector)
            self.assertIn("--require-raw-2020-selector", stages["03_frozen_cadence"])
            self.assertTrue(str(selector[selector.index("--fresh-2020-source-rows")+1]).startswith(str(root / "out")))

    def test_strict_handoff_rejects_archived_2020_and_accepts_declared_raw(self):
        with tempfile.TemporaryDirectory() as directory:
            generated, target, archived, filename = self.prepare(Path(directory))
            with patch.object(handoff, "EXPECTED", {filename: (
                    ["game_id"], frozenset({"published_timestamp_utc"}), 1)}):
                with self.assertRaisesRegex(ValueError, "requires fresh original-PDF"):
                    handoff.inject(generated, target, target / "handoff.json", require_raw_2020=True)
                manifest_file = generated / "selector_replay_manifest.json"
                manifest = json.loads(manifest_file.read_text())
                manifest["inputs"] = {"2020-21": {"parsed_rows_consumed": {
                    "kind": "recomputed_intermediate", "origin": "original_injury_PDFs",
                    "historical_report_timestamps_inherited": True}}}
                raw = Path(directory) / "fresh_2020.csv"
                raw.write_text("source_file,reason\nsource.pdf,knee\n")
                restored_raw = target / handoff.RAW_2020_TARGET
                restored_raw.parent.mkdir(parents=True)
                restored_raw.write_text(raw.read_text())
                manifest["inputs"]["2020-21"]["parsed_rows_consumed"].update(
                    path=str(raw), sha256=hashlib.sha256(raw.read_bytes()).hexdigest(), rows=1)
                entry = manifest["generated_selector_tables"][filename]
                entry["generated_from_original_pdfs_directly"] = True
                entry["input_rows_are_pinned_historical_parser_outputs"] = False
                manifest_file.write_text(json.dumps(manifest))
                with patch.object(handoff,"RAW_2020_EXPECTED_ROWS",1):
                    result = handoff.inject(generated, target, target / "handoff.json",
                                            require_raw_2020=True)
                self.assertTrue(result["fresh_original_PDF_2020_selector_rows_fed_downstream"])
                self.assertTrue(result["fresh_original_PDF_2020_parsed_rows_fed_to_october_builder"])
                self.assertEqual(restored_raw.read_bytes(),raw.read_bytes())


if __name__ == "__main__":
    unittest.main()
