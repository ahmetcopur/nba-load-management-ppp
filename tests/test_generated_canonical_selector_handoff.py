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


if __name__ == "__main__":
    unittest.main()
