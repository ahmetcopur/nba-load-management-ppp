"""Offline negative tests for the corrected-chronology Stage-6 sensitivity.

The real 13-archive run is a separate acceptance test; these fixtures test
fail-closed guards and selector/date alignment without private NBA PDFs.
"""
from pathlib import Path
import importlib.util
import io
import sys
import tempfile
import unittest
import zipfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/data_rebuild/fixture_date_chronology_sensitivity.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("fixture_chronology", SCRIPT)
chron = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chron)


class CellComparisonTests(unittest.TestCase):
    def test_booleans_from_equality_support_logical_negation(self):
        a = pd.Series(["1.0", "True", "2022-02-02 00:30:00+00:00", ""])
        b = pd.Series(["1", "true", "2022-02-02T00:30:00Z", ""])
        equal = chron.equal_cells(a, b)
        self.assertEqual(equal.dtype, bool)
        self.assertEqual((~equal).tolist(), [False] * 4)

    def test_difference_and_invalid_numeric_are_not_accepted(self):
        a = pd.Series(["2", "False", "2022-02-01", "not-a-number"])
        b = pd.Series(["3", "True", "2022-02-03", "3"])
        self.assertEqual(chron.equal_cells(a, b).tolist(), [False] * 4)

    def test_serialization_preserves_historical_float_boolean_and_datetime_styles(self):
        self.assertEqual(chron.serialize_like("50", 49.0), "49")
        self.assertEqual(chron.serialize_like("1.5", 2.0), "2.0")
        self.assertEqual(chron.serialize_like("False", True), "True")
        self.assertEqual(
            chron.serialize_like("2022-02-02 00:30:00+00:00",
                                 pd.Timestamp("2022-02-04T00:30:00Z")),
            "2022-02-04 00:30:00+00:00",
        )
        self.assertEqual(chron.serialize_like("x", float("nan")), "")


class SelectorDateTests(unittest.TestCase):
    def prepare(self, folder, matchups=("MIA@TOR", "CHI@TOR"), dates=("2022-02-01", "2022-02-03")):
        select = folder / chron.SEL
        select.mkdir(parents=True)
        pd.DataFrame({
            "Match Number": [429, 430, 784],
            "matchup_norm": ["X@Y", *matchups],
            "game_date_et": ["2022-01-31", *dates],
        }).to_csv(select / "2021-22_game_snapshot_join_harmonized_canonical.csv", index=False)
        pd.DataFrame({
            "game_id": ["FD2021_430", "FD2021_430", "FD2021_784", "FD2021_784", "FD2021_429"],
        }).to_csv(select / "2021-22_team_game_status_harmonized_canonical.csv", index=False)
        return select

    def test_joins_correct_reports_by_swapping_exact_match_numbers(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            directory = self.prepare(root)
            chron.fix_selectors(root)
            selected = pd.read_csv(directory / "2021-22_game_snapshot_join_harmonized_canonical.csv")
            self.assertEqual(selected["Match Number"].tolist(), [429, 784, 430])
            statuses = pd.read_csv(directory / "2021-22_team_game_status_harmonized_canonical.csv")
            self.assertEqual(statuses.game_id.tolist(),
                             ["FD2021_784", "FD2021_784", "FD2021_430", "FD2021_430", "FD2021_429"])

    def test_rejects_unexpected_matchup_or_date(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.prepare(root, matchups=("BOS@TOR", "CHI@TOR"))
            with self.assertRaisesRegex(RuntimeError, "Unexpected original selector"):
                chron.fix_selectors(root)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.prepare(root, dates=("2022-02-03", "2022-02-01"))
            with self.assertRaisesRegex(RuntimeError, "Unexpected original report date"):
                chron.fix_selectors(root)


class BaseUpdateTests(unittest.TestCase):
    def test_reproduces_original_covariate_before_replacement(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "base.csv.gz"
            frame = pd.DataFrame({
                "game_id": ["g1", "g2"], "team": ["A", "A"],
                "player_team_game_id": ["p1", "p2"], "back_to_back": ["False", "True"],
                "signed_elo_advantage": ["20.0", "30.0"],
            })
            frame.to_csv(path, index=False, compression="gzip")
            before = pd.DataFrame({"game_id": ["g1", "g2"], "team": ["A", "A"],
                                   "back_to_back": [False, True],
                                   "signed_elo_advantage": [20.0, 30.0]})
            after = before.copy()
            after.loc[1, "signed_elo_advantage"] = 31.5
            changed = chron.fix_base(path, before, after, {"signed_elo_advantage": 1})
            self.assertEqual(changed["signed_elo_advantage"]["rows"], 1)
            rebuilt = pd.read_csv(path, dtype=str)
            self.assertEqual(rebuilt.signed_elo_advantage.tolist(), ["20.0", "31.5"])
            frame.loc[0, "signed_elo_advantage"] = "99.0"
            frame.to_csv(path, index=False, compression="gzip")
            with self.assertRaisesRegex(RuntimeError, "differs from frozen canonical base"):
                chron.fix_base(path, before, after, {"signed_elo_advantage": 1})

    def test_refuses_writing_through_original_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            original = root / "archive.csv.gz"
            original.write_bytes(b"unaltered")
            link = root / "variant.csv.gz"
            link.symlink_to(original)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                chron.fix_base(link, pd.DataFrame(), pd.DataFrame(), {})
            self.assertEqual(original.read_bytes(), b"unaltered")


class ModelSafetyTests(unittest.TestCase):
    def test_rejects_unrecognized_fast_regression_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = root / "stage6.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("scripts/run_cadence_models_fast.py", "bad source")
                z.writestr("results/cadence_harmonized_model_results.csv",
                           "definition,controls,n,estimate_pp,se_pp,low_pp,high_pp,p\n")
            with self.assertRaisesRegex(RuntimeError, "source hash mismatch"):
                chron.rerun_original_models(root / "fake_panel.csv.gz", archive, root)


if __name__ == "__main__":
    unittest.main()
