"""Tests for original Stage-05 event-time and fake-policy placebo replay guards."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile
import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/data_rebuild/run_august_prior_event_placebos_from_release.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("original_august_placebos", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def frames():
    events = []
    for definition in sorted(mod.TV_FAMILIES):
        for season in ("2020-21", "2021-22", "2023-24", "2024-25", "2025-26"):
            events.append({"definition": definition, "season": season,
                           "estimate_pp": 2.0, "se_pp": 1.2,
                           "low_pp": -0.352, "high_pp": 4.352, "p": 0.1})
    joints = [{"definition": x, "n": 180695, "df": 2,
               "joint_pretrend_chi2": 0.8, "p": 0.67, "iterations": 100}
              for x in sorted(mod.TV_FAMILIES)]
    placebos = []
    for definition in sorted(mod.TV_FAMILIES):
        for fake_start in ("2021-22", "2022-23"):
            placebos.append({"definition": definition, "fake_start": fake_start,
                             "n": 87788, "estimate_pp": 0.4, "se_pp": 1.5,
                             "low_pp": -2.54, "high_pp": 3.34,
                             "p": 0.78, "iterations": 100})
    return {
        "event_study_tv_definitions.csv": pd.DataFrame(events),
        "joint_pretrend_tests.csv": pd.DataFrame(joints),
        "preperiod_placebo_policy_dates.csv": pd.DataFrame(placebos),
    }


class AugustFalsificationReplayTests(unittest.TestCase):
    def test_original_three_archived_tables_are_faithfully_identified(self):
        baseline = frames()
        report = mod.verify_archived(baseline, {k: v.copy() for k, v in baseline.items()})
        self.assertEqual(len(report), 3)
        self.assertTrue(all(all(v == 0 for v in item.values())
                            for item in report.values()))

    def test_frozen_coefficient_sample_and_probability_drift_rejected(self):
        baseline = frames()
        changed = {k: v.copy() for k, v in baseline.items()}
        changed["event_study_tv_definitions.csv"].loc[0, "estimate_pp"] += 0.01
        with self.assertRaisesRegex(RuntimeError, "estimate_pp archived difference"):
            mod.verify_archived(baseline, changed)
        changed = {k: v.copy() for k, v in baseline.items()}
        changed["joint_pretrend_tests.csv"].loc[0, "n"] += 1
        with self.assertRaisesRegex(RuntimeError, "exact n counts"):
            mod.verify_archived(baseline, changed)
        changed = {k: v.copy() for k, v in baseline.items()}
        changed["preperiod_placebo_policy_dates.csv"].loc[0, "p"] += 0.02
        with self.assertRaisesRegex(RuntimeError, "p archived difference"):
            mod.verify_archived(baseline, changed)

    def test_corrected_inputs_cannot_add_posthoc_placebo_specification(self):
        baseline = frames()
        changed = {k: v.copy() for k, v in baseline.items()}
        changed["preperiod_placebo_policy_dates.csv"].loc[0, "fake_start"] = "2020-21"
        with self.assertRaisesRegex(RuntimeError, "changed original falsification specs"):
            mod.compare_variant(baseline, changed)
        clean = {k: v.copy() for k, v in baseline.items()}
        clean["preperiod_placebo_policy_dates.csv"]["estimate_pp"] += 0.04
        deltas = mod.compare_variant(baseline, clean)
        self.assertAlmostEqual(deltas["preperiod_placebo_policy_dates.csv"].estimate_pp_delta.mean(), 0.04)

    def test_stage05_archive_must_include_all_three_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "stage05.zip"
            tables = frames()
            with ZipFile(archive, "w") as z:
                for name, table in tables.items():
                    z.writestr(mod.STAGE05_PREFIX + name, table.to_csv(index=False))
            selected = mod.reference_tables(archive)
            self.assertEqual(set(selected), set(tables))
            missing = Path(td) / "incomplete.zip"
            with ZipFile(missing, "w") as z:
                z.writestr(mod.STAGE05_PREFIX + "event_study_tv_definitions.csv",
                           tables["event_study_tv_definitions.csv"].to_csv(index=False))
            with self.assertRaisesRegex(RuntimeError, "reference missing"):
                mod.reference_tables(missing)


if __name__ == "__main__":
    unittest.main()
