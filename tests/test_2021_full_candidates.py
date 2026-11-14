from pathlib import Path
import tempfile
import unittest
import pandas as pd
from scripts.data_rebuild.rebuild_2021_full_candidates import candidate_inventory,rebuild
from scripts.data_rebuild.verify_2021_2023_selector_rebuild import verify,canonical_export_order
from scripts.data_rebuild.inject_2021_generated_inputs import inject,input_files


class CandidateTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({"exists":[True]*5567,"local_path":[f"report_{i}.pdf" for i in range(5567)],
                             "published_timestamp_utc":pd.date_range("2021-01-01",periods=5567,freq="h").astype(str),
                             "sha256":["a"*64]*5567})

    def test_complete_inventory_and_original_clocks(self):
        frame=self.frame()
        self.assertEqual(len(candidate_inventory(frame,list(frame.local_path))),5567)
        frame.loc[0,"published_timestamp_utc"]=frame.loc[1,"published_timestamp_utc"]
        with self.assertRaisesRegex(ValueError,"timestamps"):
            candidate_inventory(frame,list(frame.local_path))

    def test_missing_pdf_and_duplicate_candidate_fail(self):
        frame=self.frame()
        with self.assertRaisesRegex(ValueError,"members"):
            candidate_inventory(frame,list(frame.local_path)[1:])
        frame.loc[0,"local_path"]=frame.loc[1,"local_path"]
        with self.assertRaisesRegex(ValueError,"duplicate"):
            candidate_inventory(frame,list(frame.local_path))

    def test_export_rejects_unsupported_multi_season_source(self):
        with self.assertRaisesRegex(ValueError,"2021–22 alone"):
            verify(Path("absent"),("2021-22","2022-23"),None,None,Path("out"))

    def test_missing_source_provenance_cannot_fall_back(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                inject(Path(d),Path(d),Path(d))

    def test_equal_tip_games_use_match_number_and_team_role_order(self):
        games=pd.DataFrame({"game_id":["G2","G1"],"Match Number":[2,1],
                            "tip_timestamp_utc":["2021-10-19 23:30:00+00:00"]*2})
        teams=pd.DataFrame({"game_id":["G2","G1","G2","G1"],
                            "team_role":["home","home","away","away"]})
        a,b=canonical_export_order(games,teams)
        self.assertEqual(a.game_id.tolist(),["G1","G2"])
        self.assertEqual(b.team_role.tolist(),["away","home","away","home"])
        self.assertTrue(a.tip_timestamp_utc.str.contains("T").all())

    def test_2022_complete_regular_inventory_and_s4_destination(self):
        frame=self.frame().iloc[:4101]
        self.assertEqual(len(candidate_inventory(frame,list(frame.local_path),4101)),4101)
        targets=input_files("2022-23")
        self.assertEqual(str(targets["2022-23_team_game_status_harmonized_canonical.csv"]),
                         "cadence_work/s4/2022-23/team_game_final_pre_tip_status_harmonized.csv")
        self.assertEqual(len(set(targets.values())),3)

    def test_2022_changed_original_archive_fails_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);archives=root/"archives";archives.mkdir()
            (archives/"audit_2022_23_upload.zip").write_bytes(b"altered")
            with self.assertRaisesRegex(ValueError,"ZIP hash differs"):
                rebuild(archives,root/"output",season="2022-23")
            self.assertFalse((root/"output").exists())

    def test_2022_export_rejects_archived_candidate_fallback(self):
        with self.assertRaisesRegex(ValueError,"fresh full candidate"):
            verify(Path("absent"),("2022-23",),None,None,Path("output"))


if __name__=="__main__":unittest.main()
