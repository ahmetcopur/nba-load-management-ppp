"""Small independent logic tests for the August latest-pre-tip raw-rate rerun."""
import importlib.util
from pathlib import Path
import sys
import unittest

import pandas as pd

SCRIPT = (Path(__file__).resolve().parents[1] /
          "scripts/data_rebuild/run_august_descriptive_sensitivity.py")
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("august_descriptives", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AugustDescriptiveTests(unittest.TestCase):
    @staticmethod
    def synthetic():
        records = []
        for star in (False, True):
            for post in (False, True):
                for tv in (False, True):
                    for row in range(10):
                        records.append({
                            "player_team_game_id": f"{star}|{post}|{tv}|{row}",
                            "star_PPP_it": star,
                            "postPPP": post,
                            "announced_tv_primary": tv,
                            "at_risk_for_new_onset": True,
                            "absence_onset": row < (2 if star and post and tv else 1),
                            "report_outcome_observed": True,
                            "absence_now": row == 0,
                            "designation_class_frozen": "vague" if row == 0 else "not_absent",
                        })
        return pd.DataFrame(records)

    def test_eight_cell_raw_triple_difference_uses_at_risk_rows(self):
        frame = self.synthetic()
        result = mod.cells(frame)
        self.assertEqual(result["risk_rows"], 80)
        self.assertEqual(result["new_onsets"], 9)
        self.assertEqual(len(result["eight_tv_onset_cells"]), 8)
        self.assertAlmostEqual(result["unadjusted_tv_triple_difference_pp"], 10.0)
        self.assertEqual(sum(x["observed"] for x in result["pooled_prevalence"]), 80)

    def test_missing_tv_cell_rejected(self):
        frame = self.synthetic()
        frame = frame[
            ~(frame.star_PPP_it & frame.postPPP & frame.announced_tv_primary)
        ].copy()
        with self.assertRaisesRegex(RuntimeError, "eight-cell"):
            mod.cells(frame)

    def test_frozen_benchmark_rejects_off_by_one(self):
        with self.assertRaisesRegex(RuntimeError, "risk/onset"):
            mod.frozen_gate({
                "risk_rows": 180829, "new_onsets": 12709,
                "unadjusted_tv_triple_difference_pp": mod.TV_FROZEN_RAW_DDD,
                "pooled_onset": [],
            })


if __name__ == "__main__":
    unittest.main()
