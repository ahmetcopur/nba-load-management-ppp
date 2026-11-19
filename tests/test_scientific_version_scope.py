"""The legacy runner and the scientific-v2 runner must never be confused."""
from __future__ import annotations

import unittest
from pathlib import Path

from scripts.data_rebuild import reproduce_final_datasets as legacy
from scripts.data_rebuild import reproduce_october_scientific_v2 as v2

REPO = Path(__file__).resolve().parents[1]
LEGACY_OCTOBER = "2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67"
SCIENTIFIC_V2 = "9dde4578c852f15c317c1214718e1eabe9f60b740b5f2ddb4fed15b53185802f"


class ScientificVersionScopeTests(unittest.TestCase):
    def test_legacy_runner_keeps_strict_hash_and_states_its_scope(self):
        self.assertEqual(legacy.EXPECTED["october_cadence_player_games"]["decoded_sha256"], LEGACY_OCTOBER)
        self.assertEqual(legacy.SCIENTIFIC_VERSION, "legacy_corrected_chronology_pre_SCI001")
        self.assertIn(SCIENTIFIC_V2, legacy.SCIENTIFIC_VERSION_NOTE)
        self.assertIn("reproduce_october_scientific_v2.py", legacy.SCIENTIFIC_VERSION_NOTE)
        self.assertIn("SCI-001", legacy.__doc__.splitlines()[0])

    def test_scientific_v2_reference_is_distinct_and_legacy_is_refused(self):
        self.assertEqual(v2.ACCEPTED_SCIENTIFIC_V2_SHA, SCIENTIFIC_V2)
        self.assertNotIn(SCIENTIFIC_V2, (v2.FROZEN_SHA, v2.CORRECTED_SHA))
        stats = {"rows": 248778, "games": 7230, "seasons": list(range(6))}
        for phase, legacy_hash in (("frozen", v2.FROZEN_SHA), ("chronology", v2.CORRECTED_SHA)):
            with self.assertRaisesRegex(ValueError, "Legacy panel cannot be accepted"):
                v2.verify_panel_identity({**stats, "decoded_sha256": legacy_hash}, phase, v2.PRIMARY)

    def test_docs_name_each_entry_point_with_its_version(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Rebuild the legacy corrected datasets (historical pipeline, pre-SCI-001)", readme)
        self.assertNotIn("## Rebuild the final corrected analysis datasets", readme)
        for name in ("REPRODUCE_FINAL_DATASETS.md", "SIX_SEASON_CONNECTED_REPRODUCTION.md"):
            text = (REPO / "documentation" / name).read_text(encoding="utf-8")
            self.assertIn("Scope: legacy corrected datasets (pre-SCI-001)", text, name)
        v2_doc = (REPO / "documentation/OCTOBER_SCIENTIFIC_V2_2026-11-15.md").read_text(encoding="utf-8")
        self.assertIn(SCIENTIFIC_V2, v2_doc)

    def test_readme_marks_adopted_and_historical_versions(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("**adopted primary**", readme)
        self.assertNotIn("proposed primary, pending human scientific review", readme)
        self.assertEqual(readme.count("| Historical reference."), 2)


if __name__ == "__main__":
    unittest.main()
