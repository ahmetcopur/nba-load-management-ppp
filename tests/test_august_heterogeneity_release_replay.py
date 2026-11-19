"""Fail-closed tests for August four-predeclared-test heterogeneity replay."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

import pandas as pd

SOURCE = (Path(__file__).resolve().parents[1]
          / "scripts/data_rebuild/run_august_heterogeneity_from_release.py")
sys.path.insert(0, str(SOURCE.parent))
spec = importlib.util.spec_from_file_location("august_heterogeneity_source", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sample_rows():
    rows = []
    for tv in sorted(mod.TV_VARIANTS):
        for group in sorted(mod.GROUPS):
            n = 22443 if group == "near_65_threshold" else (
                139535 if group == "high_recent_workload" else 180695
            )
            h1 = 6717 if group == "near_65_threshold" else (
                34886 if group == "high_recent_workload" else
                (32924 if group == "back_to_back" else 48268)
            )
            rows.append({
                "heterogeneity": group,
                "tv_definition": tv,
                "definition": "Original frozen hypothesis for " + group,
                "n": n, "games": 2300, "players": 500,
                "h1_n": h1, "h0_n": n - h1,
                "ddd_h0_pp": 2.0, "ddd_h1_pp": 3.0,
                "difference_h1_minus_h0_pp": 1.0,
                "ddd_h0_se_pp": 1.1, "ddd_h1_se_pp": 1.4,
                "difference_se_pp": 1.2,
                "ddd_h0_p": 0.2, "ddd_h1_p": 0.3,
                "heterogeneity_p": 0.4, "heterogeneity_q_bh": 0.6,
                "iterations": 120,
            })
    return pd.DataFrame(rows)


class ReproductionBenchmarkTests(unittest.TestCase):
    def test_exact_eight_hypotheses_and_frozen_counts(self):
        original = sample_rows()
        diffs = mod.verify_published(original, original.copy())
        self.assertEqual(set(diffs), set(mod.ABSOLUTE_TOLERANCES))
        self.assertEqual(max(diffs.values()), 0.0)

    def test_missing_or_replaced_hypothesis_rejected(self):
        original = sample_rows()
        with self.assertRaisesRegex(RuntimeError, "Missing or extra"):
            mod.verify_published(original, original.iloc[:-1])
        bad = original.copy()
        bad.loc[0, "heterogeneity"] = "subgroup_selected_after_seeing_result"
        with self.assertRaisesRegex(RuntimeError, "Missing or extra"):
            mod.verify_published(original, bad)

    def test_frozen_coefficient_drift_is_strict(self):
        baseline = sample_rows()
        changed = baseline.copy()
        changed.loc[0, "difference_h1_minus_h0_pp"] += 0.01
        with self.assertRaisesRegex(RuntimeError, "failed"):
            mod.verify_published(baseline, changed)

    def test_se_and_fdr_tolerance_is_bounded(self):
        baseline = sample_rows()
        tiny = baseline.copy()
        tiny.loc[0, "difference_se_pp"] += 0.0000025
        tiny.loc[0, "heterogeneity_q_bh"] += 0.000003
        mod.verify_published(baseline, tiny)
        tiny.loc[0, "heterogeneity_q_bh"] += 0.02
        with self.assertRaisesRegex(RuntimeError, "failed"):
            mod.verify_published(baseline, tiny)

    def test_subgroup_sample_drift_is_fatal(self):
        baseline = sample_rows()
        changed = baseline.copy()
        changed.loc[0, "h1_n"] += 1
        with self.assertRaisesRegex(RuntimeError, "failed"):
            mod.verify_published(baseline, changed)

    def test_corrected_four_test_family_and_sample_coverage(self):
        baseline = sample_rows()
        corrected = baseline.copy()
        corrected["n"] += 2
        corrected["h0_n"] += 2
        corrected["difference_h1_minus_h0_pp"] += 0.04
        table = mod.compare_corrected(baseline, corrected)
        self.assertEqual(len(table), 8)
        self.assertTrue(table["difference_h1_minus_h0_pp_delta"].round(8).eq(0.04).all())
        corrected.loc[0, "h1_n"] += 1
        with self.assertRaisesRegex(RuntimeError, "coverage"):
            mod.compare_corrected(baseline, corrected)

    def test_corrected_cannot_gain_new_subgroup(self):
        baseline = sample_rows()
        corrected = baseline.copy()
        corrected.loc[0, "heterogeneity"] = "post_hoc_group"
        with self.assertRaisesRegex(RuntimeError, "changed the predeclared"):
            mod.compare_corrected(baseline, corrected)


if __name__ == "__main__":
    unittest.main()
