import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from scripts.data_rebuild import rebuild_2025_full_candidates as source
from scripts.data_rebuild import generate_2025_selector_inputs as selector
from scripts.data_rebuild.inject_2021_generated_inputs import input_files


class SavedCandidateTests(unittest.TestCase):
    def test_tampered_original_inventory_archive_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"audit_2025_26_upload.zip").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError,"ZIP hash differs"):
                source.inventory(root)

    def test_unaccepted_2025_handoff_cannot_be_requested(self):
        with self.assertRaisesRegex(ValueError,"Unsupported"):
            input_files("2025-26")

    def test_tampered_fresh_source_cannot_fall_back_to_archived_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);fresh=root/"fresh";fresh.mkdir();archives=root/"archives";archives.mkdir()
            (fresh/"candidate_acceptance.json").write_text(json.dumps({"status":"pass","full_candidate_rows_sha256":"wrong"}))
            (fresh/"full_candidate_rows.csv").write_text("changed\n")
            with patch.object(selector,"file_sha256",side_effect=lambda p:source.S4_SHA if p.name==source.S4_ZIP else hashlib.sha256(p.read_bytes()).hexdigest()):
                with self.assertRaisesRegex(ValueError,"provenance hash"):
                    selector.generate(archives,fresh,root/"generated")
            self.assertFalse((root/"generated").exists())

    def test_unverified_s4_schedule_rejected_before_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archives=root/"archives";archives.mkdir();fresh=root/"fresh";fresh.mkdir();(archives/source.S4_ZIP).write_bytes(b"altered")
            with self.assertRaisesRegex(ValueError,"S4 schedule"):
                selector.generate(archives,fresh,root/"generated")

    def test_status_join_requires_original_report_game_date(self):
        raw=pd.DataFrame({"source_file":["cadence_selected/a.pdf"]*3,
                          "matchup_norm":["HOU@OKC"]*3,
                          "game_date_raw":["10/21/2025",None,"10/22/2025"]})
        chosen=pd.DataFrame({"game_id":["G1"],"basename":["a.pdf"]})
        schedule=pd.DataFrame({"game_id":["G1"],"matchup_norm":["HOU@OKC"],
                               "game_date_et":["2025-10-21"]})
        result=selector.date_matched_status_rows(raw,chosen,schedule)
        self.assertEqual(result.game_date_raw.tolist(),["10/21/2025"])
        self.assertEqual(len(raw),3)

    def test_status_join_rejects_ambiguous_schedule_game_keys(self):
        raw=pd.DataFrame({"source_file":["a.pdf"],"matchup_norm":["HOU@OKC"],"game_date_raw":["10/21/2025"]})
        chosen=pd.DataFrame({"game_id":["G1"],"basename":["a.pdf"]})
        schedule=pd.DataFrame({"game_id":["G1","G1"],"matchup_norm":["HOU@OKC"]*2,
                               "game_date_et":["2025-10-21"]*2})
        with self.assertRaises(pd.errors.MergeError):
            selector.date_matched_status_rows(raw,chosen,schedule)

    def test_archived_metadata_contradiction_is_detected_without_modification(self):
        games=pd.DataFrame({"game_id":["G1"],"inferred_clean_teams":[0]})
        teams=pd.DataFrame({"game_id":["G1","G1"],"team_role":["away","home"],
                            "inferred_no_listed_players":[True,True]})
        self.assertEqual(selector.archived_metadata_inconsistencies(games,teams),1)
        self.assertEqual(games.inferred_clean_teams.tolist(),[0])

    def test_original_targeted_design_archive_tamper_is_rejected(self):
        from scripts.data_rebuild.verify_2025_targeted_plan import verify
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"design.zip";path.write_bytes(b"altered")
            with self.assertRaisesRegex(ValueError,"SHA-256 differs"):
                verify(Path(directory),path)


if __name__=="__main__":unittest.main()
