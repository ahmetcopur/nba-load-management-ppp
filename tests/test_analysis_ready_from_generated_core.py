"""Synthetic, fail-closed tests for generated-core -> analysis-ready construction."""
import unittest
import pandas as pd

from scripts.data_rebuild.build_analysis_ready_from_generated_core import (
    ALLOWED_SOURCE_ENRICHMENTS, reconcile_one_chunk, reason_key,
)


class AnalysisReadyCoreBridgeTests(unittest.TestCase):
    def setUp(self):
        self.core = pd.DataFrame([{
            "game_id": "S|G", "team": "Team", "nba_player_id": "10",
            "nba_game_id": "22000001",
            "absence_now": "True", "at_risk_for_new_onset": "True",
            "designation_reason": "Left Knee Soreness",
            "designation_class_provisional": "vague",
            "onset_type": "vague_injury_onset",
            "vague_onset": "True",
            "taxonomy_version": "provisional_keyword_v1_requires_human_validation",
            "star_PPP_it": "",
            "star_status_pending": "True",
            "cup_game_pending": "True",
        }])
        self.frozen = self.core.copy()
        self.frozen["nba_game_id"] = "22000001.0"  # exact numeric identity, different text
        self.frozen["taxonomy_version"] = "assistant_reviewed_designation_only_v2"
        self.frozen["star_PPP_it"] = "True"
        self.frozen["star_status_pending"] = "False"
        self.frozen["cup_game_pending"] = "False"
        self.frozen["player_team_game_id"] = "S|G|Team|10"
        self.frozen["star_prior_all_nba_3yr"] = "True"
        self.frozen["designation_class_frozen"] = "vague"
        self.frozen["onset_type_frozen"] = "vague_injury_onset"
        self.frozen["designation_class_provisional_v1"] = "vague"
        self.frozen["onset_type_provisional_v1"] = "vague_injury_onset"
        self.frozen["vague_onset_provisional_v1"] = "True"
        for c in ("vague_onset_frozen", "specific_onset_frozen",
                  "explicit_rest_onset_frozen", "other_absence_onset_frozen"):
            self.frozen[c] = "True" if c == "vague_onset_frozen" else "False"
        self.labels = {"left knee soreness": "vague"}

    def test_generated_core_drives_taxonomy_and_preserves_inherited_awards(self):
        result, risk = reconcile_one_chunk(self.core, self.frozen, self.labels)
        self.assertEqual(result["designation_class_frozen"].iloc[0], "vague")
        self.assertEqual(result["star_prior_all_nba_3yr"].iloc[0], "True")
        self.assertEqual(result["nba_game_id"].iloc[0], "22000001.0")
        self.assertTrue(bool(risk.iloc[0]))
        self.assertEqual(result.columns.tolist(), self.frozen.columns.tolist())

    def test_unknown_official_reason_fails_instead_of_guessing_label(self):
        altered = self.core.copy()
        altered["designation_reason"] = "New never-reviewed official diagnosis"
        with self.assertRaisesRegex(ValueError, "requires independent taxonomy review"):
            reconcile_one_chunk(altered, self.frozen, self.labels)

    def test_player_game_key_drift_fails(self):
        altered = self.core.copy()
        altered["nba_player_id"] = "999"
        with self.assertRaisesRegex(ValueError, "row ID/order differs"):
            reconcile_one_chunk(altered, self.frozen, self.labels)

    def test_material_scientific_core_field_drift_fails(self):
        altered = self.core.copy()
        altered["nba_game_id"] = "88888888"
        with self.assertRaisesRegex(ValueError, "Non-formatting difference"):
            reconcile_one_chunk(altered, self.frozen, self.labels)

    def test_reviewed_label_conflict_fails(self):
        ref = self.frozen.copy()
        ref["designation_class_frozen"] = "specific"
        with self.assertRaisesRegex(ValueError, "Recomputed official-report taxonomy differs"):
            reconcile_one_chunk(self.core, ref, self.labels)

    def test_inherited_star_cup_values_not_overridden_from_provisional_core(self):
        result, _ = reconcile_one_chunk(self.core, self.frozen, self.labels)
        for field in ALLOWED_SOURCE_ENRICHMENTS:
            self.assertEqual(result[field].iloc[0], self.frozen[field].iloc[0])

    def test_reason_normalizer_is_unicode_casefolded(self):
        text = pd.Series(["  MİGRAINE  ", "KNEE soreness"])
        self.assertEqual(reason_key(text).iloc[1], "knee soreness")


if __name__ == "__main__":
    unittest.main()
