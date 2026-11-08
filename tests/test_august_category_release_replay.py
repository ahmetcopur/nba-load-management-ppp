"""Fail-closed tests for August original category-FDR source and February TV rekey."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

import pandas as pd

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/data_rebuild/run_august_category_fdr_from_release.py"
spec=importlib.util.spec_from_file_location("august_category_release",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TVProvenanceTests(unittest.TestCase):
    def make(self,root):
        tv=pd.DataFrame([
            {"season":"2021-22","home_team":"Toronto Raptors","away_team":"Chicago Bulls",
             "game_date_et":"2022-02-01","tip_utc":"2022-02-02T00:30:00Z","tip_et":"19:30",
             "announced_tv_primary":False,"network_announced":None,
             "announced_tv_status":"listed_non_national_at_release","fixture_row":759,
             "source_line":"2021-22 original released Chicago Toronto listing"},
            {"season":"2021-22","home_team":"Toronto Raptors","away_team":"Miami Heat",
             "game_date_et":"2022-02-03","tip_utc":"2022-02-04T00:30:00Z","tip_et":"19:30",
             "announced_tv_primary":True,"network_announced":"TNT",
             "announced_tv_status":"listed_primary_national_at_release","fixture_row":777,
             "source_line":"2021-22 original released Miami Toronto TNT listing"}
        ])
        tv_path=root/"tv.csv"
        tv.to_csv(tv_path,index=False)
        corrected=pd.DataFrame([
            {"season":"2021-22","game_date_et":"2022-02-03","team":"Chicago Bulls",
             "opponent":"Toronto Raptors","game_id":"frozen_20220202_bulls",
             "is_home":False,"announced_tv_primary":False},
            {"season":"2021-22","game_date_et":"2022-02-01","team":"Miami Heat",
             "opponent":"Toronto Raptors","game_id":"frozen_20220204_heat",
             "is_home":False,"announced_tv_primary":True},
        ])
        panel=root/"risk.csv.gz"
        corrected.to_csv(panel,index=False,compression="gzip")
        return tv_path,panel

    def test_date_join_fails_prior_to_fix_but_passes_after(self):
        with tempfile.TemporaryDirectory() as td:
            tv,panel=self.make(Path(td))
            before=mod.original_source_tv_matches_panel(panel,tv)
            self.assertEqual(int(before.announced_tv_status.isna().sum()),2)
            details=mod.repair_announcement_fixture_keys(tv,panel,expected_rows=2)
            self.assertEqual(len(details),2)
            self.assertEqual({x["old_date"] for x in details},{"2022-02-01","2022-02-03"})
            after=mod.original_source_tv_matches_panel(panel,tv)
            self.assertEqual(int(after.announced_tv_status.isna().sum()),0)
            self.assertEqual(after.announced_tv_primary_panel.tolist(),[False,True])
            data=pd.read_csv(tv)
            self.assertEqual(set(data.network_announced.dropna()),{"TNT"})
            self.assertEqual(set(data.source_line.str.contains("original released")),{True})
            self.assertEqual(data.loc[data.away_team.eq("Chicago Bulls"),"game_date_et"].iloc[0],"2022-02-03")
            self.assertEqual(data.loc[data.away_team.eq("Miami Heat"),"game_date_et"].iloc[0],"2022-02-01")

    def test_wrong_historical_primary_exposure_fails(self):
        with tempfile.TemporaryDirectory() as td:
            tv,panel=self.make(Path(td))
            frame=pd.read_csv(tv)
            frame.loc[frame.away_team.eq("Miami Heat"),"announced_tv_primary"]=False
            frame.to_csv(tv,index=False)
            with self.assertRaisesRegex(RuntimeError,"exposure differs"):
                mod.repair_announcement_fixture_keys(tv,panel,expected_rows=2)

    def test_missing_original_source_pair_fails(self):
        with tempfile.TemporaryDirectory() as td:
            tv,panel=self.make(Path(td))
            frame=pd.read_csv(tv)
            frame.loc[frame.away_team.eq("Miami Heat"),"game_date_et"]="2022-02-02"
            frame.to_csv(tv,index=False)
            with self.assertRaisesRegex(RuntimeError,"expected one entry"):
                mod.repair_announcement_fixture_keys(tv,panel,expected_rows=2)

    def test_duplicate_source_tv_fixture_lookup_fails(self):
        with tempfile.TemporaryDirectory() as td:
            tv,panel=self.make(Path(td))
            frame=pd.read_csv(tv)
            pd.concat([frame,frame.iloc[[0]]],ignore_index=True).to_csv(tv,index=False)
            with self.assertRaisesRegex(RuntimeError,"Duplicate source TV fixture"):
                mod.original_source_tv_matches_panel(panel,tv)


class SourceComparatorTests(unittest.TestCase):
    @staticmethod
    def rows():
        out=[]
        for tv in mod.EXPECTED_TV:
            for outcome in mod.EXPECTED_OUTCOMES:
                out.append({"tv_definition":tv,"outcome":outcome,"n":180695,
                            "estimate_pp":1.0,"se_pp":1.3,"low_pp":-1.548,
                            "high_pp":3.548,"p":0.2,"q_bh":0.8,"p_holm":0.8})
        return pd.DataFrame(out)

    def test_original_eight_models_must_match(self):
        original=self.rows()
        diffs=mod.compare_baseline(original,original.copy())
        self.assertEqual(len(diffs),7)
        self.assertEqual(max(diffs.values()),0)
        changed=original.copy()
        changed.loc[0,"p_holm"]=0.7
        with self.assertRaisesRegex(RuntimeError,"does not reproduce"):
            mod.compare_baseline(original,changed)
        with self.assertRaisesRegex(RuntimeError,"missing/extra"):
            mod.compare_baseline(original,changed.iloc[:-1])

    def test_corrected_model_sample_change_must_be_exact(self):
        frozen=self.rows()
        variant=frozen.copy()
        variant["n"]=180697
        got=mod.delta_table(frozen,variant)
        self.assertEqual(len(got),8)
        variant.loc[0,"n"]=180698
        with self.assertRaisesRegex(RuntimeError,"sample drift"):
            mod.delta_table(frozen,variant)


if __name__=="__main__":
    unittest.main()
