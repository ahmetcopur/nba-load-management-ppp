from pathlib import Path
import tempfile
import unittest
import pandas as pd
from scripts.data_rebuild.rebuild_2021_full_candidates import candidate_inventory
from scripts.data_rebuild.verify_2021_2023_selector_rebuild import verify
from scripts.data_rebuild.inject_2021_generated_inputs import inject


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


if __name__=="__main__":unittest.main()
