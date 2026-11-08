"""Pure fail-closed tests for the source-corrected August reviewed-label transfer."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

import pandas as pd

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts/data_rebuild"
spec = importlib.util.spec_from_file_location(
    "august_reviewed_transfer", SCRIPTS / "build_august_analysis_ready_sensitivity.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class LabelTransferTests(unittest.TestCase):
    @staticmethod
    def frozen():
        return pd.DataFrame({
            "player_team_game_id": ["g1|A|1", "g2|A|1", "g3|B|2"],
            "game_id": ["g1", "g2", "g3"], "team": ["A", "A", "B"],
            "nba_player_id": ["1", "1", "2"],
            "absence_now": ["False", "True", "True"],
            "at_risk_for_new_onset": ["True", "True", "False"],
            "designation_reason": ["", "Injury/Illness - Left Knee; Irritation", ""],
            "designation_class_frozen": ["not_absent", "vague", "unknown"],
            "onset_type_frozen": ["plays", "vague_injury_onset", ""],
            "vague_onset_frozen": ["False", "True", "False"],
            "specific_onset_frozen": ["False", "False", "False"],
            "explicit_rest_onset_frozen": ["False", "False", "False"],
            "other_absence_onset_frozen": ["False", "False", "False"],
        }).set_index("player_team_game_id", drop=False)

    def test_casefolded_official_reason_reuses_historical_review_label(self):
        frozen = self.frozen()
        dictionary = mod.reviewed_reason_lookup(frozen)
        candidate = frozen.copy()
        candidate.loc["g2|A|1", "designation_reason"] = (
            "Injury/Illness - Left knee; Irritation")
        classes, onsets = mod.official_reason_classes(candidate, dictionary)
        self.assertEqual(classes["g2|A|1"], "vague")
        self.assertEqual(onsets["g2|A|1"], "vague_injury_onset")
        mod.baseline_taxonomy_gate(frozen, frozen, dictionary)

    def test_unseen_reason_requires_review(self):
        frozen = self.frozen()
        unknown = frozen.copy()
        unknown.loc["g2|A|1", "designation_reason"] = "Unexpected novel diagnostic text"
        with self.assertRaisesRegex(RuntimeError, "requires review"):
            mod.official_reason_classes(
                unknown, mod.reviewed_reason_lookup(frozen))

    def test_conflicting_historical_reason_label_rejected(self):
        frozen = self.frozen().reset_index(drop=True)
        duplicate = frozen.iloc[[1]].copy()
        duplicate["player_team_game_id"] = "g4|B|2"
        duplicate["designation_class_frozen"] = "specific"
        frozen = pd.concat([frozen, duplicate], ignore_index=True)
        with self.assertRaisesRegex(RuntimeError, "conflicting official reasons"):
            mod.reviewed_reason_lookup(frozen.set_index("player_team_game_id"))

    def test_key_must_include_team(self):
        data = pd.DataFrame({
            "game_id": ["2025-g", "2025-g"],
            "team": ["Dallas Mavericks", "Philadelphia 76ers"],
            "nba_player_id": ["1629656", "1629656"],
        })
        result = mod.index_core(data)
        self.assertEqual(result.player_team_game_id.nunique(), 2)

    def test_original_reviewer_baseline_checks_onset_flags(self):
        frozen = self.frozen()
        incorrect = frozen.copy()
        incorrect.loc["g2|A|1", "vague_onset_frozen"] = "False"
        with self.assertRaisesRegex(RuntimeError, "taxonomy flag baseline differs"):
            mod.baseline_taxonomy_gate(
                frozen, incorrect, mod.reviewed_reason_lookup(frozen))


if __name__ == "__main__":
    unittest.main()
