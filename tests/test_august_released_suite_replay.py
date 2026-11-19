"""Offline fail-closed tests for the released August suite replay comparator."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/data_rebuild"))
spec = importlib.util.spec_from_file_location(
    "suite", ROOT / "scripts/data_rebuild/run_august_released_suite_from_release.py")
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)


def table(estimate=2.63, se=1.32, term="triple"):
    return pd.DataFrame({"model": ["m"], "term": [term], "estimate": [estimate],
                         "std_error": [se], "n": [180695]})


class CompareTests(unittest.TestCase):
    def test_identical_tables_pass(self):
        report = suite.compare(table(), table(), ["model", "term"])
        self.assertEqual(report["unmatched_rows"], 0)
        self.assertEqual(report["max_coefficient_difference"], 0)

    def test_coefficient_and_inference_tolerances_are_separate(self):
        report = suite.compare(table(), table(estimate=2.63 + 1e-6, se=1.32 + 5e-4),
                               ["model", "term"])
        self.assertGreater(report["max_coefficient_difference"], suite.COEF_TOL)
        self.assertLess(report["max_inference_difference"], suite.INFERENCE_TOL)

    def test_count_change_is_a_coefficient_level_failure(self):
        other = table()
        other["n"] = 180697
        report = suite.compare(table(), other, ["model", "term"])
        self.assertEqual(report["max_coefficient_difference"], 2)

    def test_text_difference_counted(self):
        a = pd.DataFrame({"label": ["x"], "status": ["converged"]})
        b = pd.DataFrame({"label": ["x"], "status": ["failed"]})
        self.assertEqual(suite.compare(a, b, ["label"])["differing_text_cells"], 1)

    def test_boolean_columns_compared_as_text(self):
        a = pd.DataFrame({"label": ["x"], "converged": [True]})
        self.assertEqual(suite.compare(a, a, ["label"])["differing_text_cells"], 0)
        b = a.assign(converged=[False])
        self.assertEqual(suite.compare(a, b, ["label"])["differing_text_cells"], 1)

    def test_missing_row_reported(self):
        both = pd.concat([table(), table(term="elo_100")], ignore_index=True)
        report = suite.compare(both, table(), ["model", "term"])
        self.assertEqual(report["unmatched_rows"], 1)

    def test_collinear_split_compared_through_identified_slope(self):
        split = pd.concat([table(), table(0.5, term="games_before_10"),
                           table(-0.5, term="dist65_10")], ignore_index=True)
        kept = pd.concat([table(), table(1.0, term="games_before_10")], ignore_index=True)
        report = suite.compare(split, kept, ["model", "term"])
        self.assertEqual(report["unmatched_rows"], 0)
        self.assertEqual(report["identified_slope_max_difference"], 0)
        wrong = pd.concat([table(), table(1.2, term="games_before_10")], ignore_index=True)
        self.assertAlmostEqual(
            suite.compare(split, wrong, ["model", "term"])["identified_slope_max_difference"], 0.2)

    def test_positional_tables_need_equal_length(self):
        a = pd.DataFrame({"permuted_estimate_pp": [0.1, 0.2]})
        with self.assertRaisesRegex(RuntimeError, "length"):
            suite.compare(a, a.iloc[:1], [])

    def test_duplicate_keys_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Duplicate"):
            suite.compare(pd.concat([table(), table()]), table(), ["model", "term"])


class GateAndDeltaTests(unittest.TestCase):
    def make(self, root, estimate):
        out = root / "results/portable_first_pass"
        out.mkdir(parents=True)
        table(estimate).to_csv(out / "focal.csv", index=False)
        (out / "raw_ddd.json").write_text(json.dumps({"absence": estimate / 100}))

    def spec(self, root):
        package = root / "shared/packages/p.zip"
        package.parent.mkdir(parents=True)
        with zipfile.ZipFile(package, "w") as z:
            z.writestr("a/focal.csv", table().to_csv(index=False))
            z.writestr("a/raw_ddd.json", json.dumps({"absence": 0.0263}))
        return {"package": "packages/p.zip", "outputs": {
            "results/portable_first_pass/focal.csv": ("a/focal.csv", ["model", "term"]),
            "results/portable_first_pass/raw_ddd.json": ("a/raw_ddd.json", None)}}

    def test_frozen_gate_passes_exact_and_fails_changed_estimate(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            spec = self.spec(root)
            self.make(root / "good", 2.63)
            self.make(root / "bad", 2.64)
            _, failed = suite.frozen_gate(root / "shared", root / "good", spec)
            self.assertEqual(failed, [])
            _, failed = suite.frozen_gate(root / "shared", root / "bad", spec)
            self.assertEqual(len(failed), 2)

    def test_deltas_report_identified_slope_and_reject_other_missing_rows(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            spec = {"outputs": {"t.csv": (None, ["model", "term"])}}
            (root / "f").mkdir(); (root / "c").mkdir()
            pd.concat([table(), table(0.4, term="games_before_10")]).to_csv(
                root / "f/t.csv", index=False)
            pd.concat([table(2.67), table(-0.5, term="dist65_10")]).to_csv(
                root / "c/t.csv", index=False)
            result = suite.deltas(root / "f", root / "c", spec)
            triple = result[(result.row == "m | triple") & (result.column == "estimate")]
            self.assertAlmostEqual(triple.delta.iloc[0], 0.04)
            slope = result[result.identified_combination]
            self.assertEqual(len(slope), 1)
            self.assertAlmostEqual(slope.delta.iloc[0], 0.1)
            table(term="elo_100").to_csv(root / "c/t.csv", index=False)
            with self.assertRaisesRegex(RuntimeError, "only one run"):
                suite.deltas(root / "f", root / "c", spec)


class StageDefinitionTests(unittest.TestCase):
    def test_every_stage_compares_archived_members_with_keys(self):
        for name, spec in suite.STAGES.items():
            self.assertTrue(spec["outputs"], name)
            for rel, (member, key, *kind) in spec["outputs"].items():
                self.assertIn(kind, ([], ["permutation"]))
                self.assertTrue(rel.startswith(suite.SANDBOX + "/"), rel)
                self.assertTrue(member)
            self.assertTrue(spec["executed"])

    def test_executed_script_copy_changes_only_the_historical_root(self):
        with tempfile.TemporaryDirectory() as d:
            shared, root = Path(d) / "shared", Path(d) / "work"
            source = shared / "scripts/executed/stage/a.py"
            source.parent.mkdir(parents=True)
            source.write_text("AP='/mnt/data/nba_continue/x.csv'\nk=1\n")
            info = suite.stage_script(shared, root, "stage", "a.py")
            self.assertEqual(info["root_substitutions"], 1)
            copied = (root / "scripts/a.py").read_text()
            self.assertEqual(copied, f"AP='{root / suite.SANDBOX}/nba_continue/x.csv'\nk=1\n")
            (shared / "scripts/executed/stage/b.py").write_text("k=1\n")
            with self.assertRaisesRegex(RuntimeError, "no historical root"):
                suite.stage_script(shared, root, "stage", "b.py")

    def test_only_permutation_outputs_use_the_wider_tolerance(self):
        wide = [rel for spec in suite.STAGES.values()
                for rel, entry in spec["outputs"].items() if entry[2:] == ("permutation",)]
        self.assertEqual(len(wide), 3)
        self.assertTrue(all("permutation" in rel for rel in wide))
        self.assertLessEqual(suite.PERMUTATION_TOL, 0.01)

    def test_corrected_hash_is_pinned(self):
        self.assertEqual(suite.CORRECTED_RISK_SHA,
                         "5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3")


if __name__ == "__main__":
    unittest.main()
