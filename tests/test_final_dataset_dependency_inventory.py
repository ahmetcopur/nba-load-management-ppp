"""Keep the public dependency inventory aligned with the actual restoration map."""
import json
from pathlib import Path
import unittest

from scripts.data_rebuild.report_final_dataset_dependencies import build_report
from scripts.data_rebuild.restore_historical_layout import FILES, SELECTOR_NAMES, SELECTOR_DEST


class InventoryTests(unittest.TestCase):
    def test_every_october_restored_input_is_accounted_for(self):
        root=Path(__file__).resolve().parents[1]
        saved=json.loads((root/"documentation/FINAL_DATASET_DEPENDENCY_GRAPH_2026-11-14.json").read_text())
        self.assertEqual(saved,build_report())
        node_ids=[n["id"] for n in saved["nodes"]]
        self.assertEqual(len(node_ids),len(set(node_ids)))
        self.assertTrue({x[0] for x in FILES} <= set(node_ids))
        self.assertTrue({f"{SELECTOR_DEST}/{x}" for x in SELECTOR_NAMES} <= set(node_ids))
        self.assertFalse(saved["strict_six_season_raw_source_acceptance"])

    def test_six_source_verdicts_match_actual_cumulative_and_fresh_execution_evidence(self):
        root=Path(__file__).resolve().parents[1]
        saved=build_report();mode=saved["six_season_connected_mode"]
        self.assertEqual(len(mode["generated_input_paths"]),18)
        self.assertEqual(len(saved["required_six_season_source_zip_names"]),26)
        cumulative=json.loads((root/mode["cumulative_evidence"]).read_text())
        self.assertEqual(cumulative["scientific_output_verdict"],"pass")
        self.assertEqual(len(cumulative["actual_consumption"]["original_builder_opened_paths"]),18)
        fresh=json.loads((root/mode["fresh_three_dataset_execution_evidence"]).read_text())
        self.assertEqual(fresh["scientific_output_verdict"],"pass")
        self.assertFalse(fresh["earlier_completed_stages_reused"])
        self.assertEqual(len(fresh["source_reconstructions"]),6)
        self.assertEqual({k:v["decoded_sha256"] for k,v in fresh["datasets"].items()},saved["final_dataset_decoded_sha256"])
        self.assertEqual(len(fresh["stage6_models"]),4)
        self.assertTrue(fresh["model_comparison_to_previously_accepted_corrected_run"]["scientific_model_cells_exact"])
        self.assertFalse(fresh["scope_limits"]["historical_2025_team_metadata_equivalence"])


if __name__=="__main__":
    unittest.main()
