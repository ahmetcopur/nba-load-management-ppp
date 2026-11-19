"""Offline tests for immutable October release replay and comparison safeguards."""
import gzip
import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/data_rebuild/october_corrected_chronology.py"
spec = importlib.util.spec_from_file_location("october_corrected_chronology", SCRIPT)
octo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(octo)


def write(folder, rel, frame):
    path = folder / "results/october_2026/recomputed" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


class CompareTablesTests(unittest.TestCase):
    def test_ignores_runtime_and_shared_missing_values(self):
        a = pd.DataFrame({"name":["m"], "coef_pp":[2.63], "converged":[True],
                          "seconds":[5.7], "dropped_terms":[np.nan]})
        b = a.copy()
        b["seconds"] = 19.9
        result = octo.compare_tables(a,b)
        self.assertTrue(result["same_shape"])
        self.assertEqual(result["max_abs_numeric_difference"],0)
        self.assertEqual(result["differing_text_cells"],0)

    def test_numeric_and_boolean_differences_reported(self):
        a = pd.DataFrame({"term":["triple"],"estimate_pp":[2.63],"converged":[True]})
        b = pd.DataFrame({"term":["triple"],"estimate_pp":[2.67],"converged":[False]})
        result = octo.compare_tables(a,b)
        self.assertAlmostEqual(result["max_abs_numeric_difference"],0.04)
        self.assertEqual(result["differing_text_cells"],1)
        self.assertFalse(octo.compare_tables(a,pd.concat([b,b]))["same_shape"])

    def test_mixed_numeric_and_text_differences_not_silenced(self):
        a = pd.DataFrame({"mixed":["1.0","missing","2"]})
        b = pd.DataFrame({"mixed":["1","surprise","2"]})
        report = octo.compare_tables(a,b)
        self.assertEqual(report["max_abs_numeric_difference"],0)
        self.assertEqual(report["differing_text_cells"],1)

    def test_missing_vs_empty_text_is_reported(self):
        a = pd.DataFrame({"x":[np.nan]})
        b = pd.DataFrame({"x":[""]})
        self.assertEqual(octo.compare_tables(a,b)["differing_text_cells"],1)


class FrozenArchiveTests(unittest.TestCase):
    def test_event_window_joint_archive_split(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            archive = folder / "results/october_2026/archive"
            archive.mkdir(parents=True)
            (folder / "results/october_2026/audit_archive").mkdir()
            combined = pd.DataFrame({
                "tv":["tv_harmonized_linear","announced_tv_primary"],
                "outcome":["repair","repair"],
                "n_before_control_drop":[22151,23713],
                "wald_chi2_6":[15.6,12.3],"p":[0.016,0.056],
            })
            combined.to_csv(archive / "event_window_joint_tests.csv",index=False)
            write(folder,"event_window_joint_tests_linear.csv",
                  combined.iloc[[0]].rename(columns={"n_before_control_drop":"n"}))
            write(folder,"event_window_joint_tests_national_partner.csv",
                  combined.iloc[[1]].rename(columns={"n_before_control_drop":"n"}))
            report = octo.reproduction(folder)
            self.assertEqual(len(report),2)
            self.assertTrue(all(x["same_shape"] and not x["differing_text_cells"]
                                for x in report.values()))

    def test_frozen_reproduction_requires_every_archived_file(self):
        valid = {f"item{i}.csv":{"archived":True,"same_shape":True,
                 "max_abs_numeric_difference":0.0,"differing_text_cells":0}
                 for i in range(octo.EXPECTED_ARCHIVED_OUTPUTS)}
        octo.require_reproduction(valid)
        with self.assertRaisesRegex(RuntimeError,"Expected"):
            octo.require_reproduction({"only.csv":valid["item0.csv"]})
        valid["item0.csv"] = dict(valid["item0.csv"],max_abs_numeric_difference=0.5)
        with self.assertRaisesRegex(RuntimeError,"does not reproduce"):
            octo.require_reproduction(valid)


class SensitivityTests(unittest.TestCase):
    def model(self,terms,values):
        return pd.DataFrame({"term":terms,"estimate_pp":values,
                             "se_pp":[1.0]*len(terms),"p":[0.5]*len(terms),
                             "n":[100]*len(terms)})

    def test_matches_terms_and_flags_collinear_swap(self):
        with tempfile.TemporaryDirectory() as d:
            before,after=Path(d)/"before",Path(d)/"after"
            write(before,"models.csv",self.model(["triple","games_before_10"],[2.63,1.01]))
            write(after,"models.csv",self.model(["dist65_10","triple"],[-1.01,2.67]))
            result=octo.sensitivity(before,after)
            self.assertAlmostEqual(result[result.row=="triple"].iloc[0].change,0.04)
            self.assertEqual(sorted(result[result.collinear_swap].row),
                             ["dist65_10","games_before_10"])

    def test_unexpected_missing_term_fails(self):
        with tempfile.TemporaryDirectory() as d:
            before,after=Path(d)/"before",Path(d)/"after"
            write(before,"models.csv",self.model(["triple","elo_100"],[2.63,0.1]))
            write(after,"models.csv",self.model(["triple"],[2.67]))
            with self.assertRaisesRegex(RuntimeError,"present in only one run"):
                octo.sensitivity(before,after)

    def test_missing_corrected_result_file_fails(self):
        with tempfile.TemporaryDirectory() as d:
            before,after=Path(d)/"before",Path(d)/"after"
            write(before,"model.csv",self.model(["triple"],[2.63]))
            with self.assertRaisesRegex(RuntimeError,"output files differ"):
                octo.sensitivity(before,after)


class ProvenanceTests(unittest.TestCase):
    def test_gzip_container_metadata_is_not_scientific_identity(self):
        with tempfile.TemporaryDirectory() as d:
            left,right=Path(d)/"a.csv.gz",Path(d)/"b.csv.gz"
            for path,timestamp in ((left,0),(right,5)):
                with gzip.GzipFile(filename=str(path),mode="wb",mtime=timestamp) as stream:
                    stream.write(b"col\nA\n")
            self.assertEqual(octo.digest_gzip_payload(left),
                             octo.digest_gzip_payload(right))
            self.assertNotEqual(octo.digest_file(left),octo.digest_file(right))

    def test_shared_repository_sha_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            import subprocess
            subprocess.run(["git","init","-q",str(root)],check=True)
            subprocess.run(["git","-C",str(root),"-c","user.name=Test",
                            "-c","user.email=test@example.com","commit",
                            "--allow-empty","-qm","test"],check=True)
            with self.assertRaisesRegex(RuntimeError,"not"):
                octo.verify_shared_commit(root)


if __name__ == "__main__":
    unittest.main()
