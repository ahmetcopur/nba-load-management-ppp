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


if __name__=="__main__":
    unittest.main()
