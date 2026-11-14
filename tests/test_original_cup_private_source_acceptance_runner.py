"""Safeguards for the single-command ORIGINAL PRIVATE Cup source acceptance CLI.

Public tests use incorrect fake ZIPs and a MOCKED dispatcher, never execute a
historical private archive or claim exact original source acceptance. Positive
original-data checks can only occur using the actual pinned original ZIPs in
an external private runtime. Exact comparator positive/negative data tests
are separately tested in test_nba_cup_*_synthetic.py.
"""
from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from scripts.data_rebuild import run_original_cup_private_source_acceptance as runner


class CupPrivateMasterCLIOrchestrationTests(unittest.TestCase):
    def test_missing_original_sources_fail_before_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaisesRegex(ValueError,"both original private ZIP paths must exist"):
                runner.original_sha_pins(root/"unknown-cup.zip",root/"unknown-freeze.zip")

    def test_identical_source_paths_rejected_even_if_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/"wrong-archive.zip"
            a.write_bytes(b"wrong private source")
            with self.assertRaisesRegex(ValueError,"different files"):
                runner.original_sha_pins(a,a)

    def test_modified_private_Cup_zip_rejected_before_original_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            a,b=root/"cup.zip",root/"freeze.zip"
            a.write_bytes(b"tampered")
            b.write_bytes(b"tampered other")
            with self.assertRaisesRegex(ValueError,"Cup ZIP SHA-256 mismatch"):
                runner.run_original_private_cup_acceptance(a,b)

    def test_existing_report_refused_before_archives_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/"never_overwrite.json"
            out.write_text("DO NOT CHANGE ME",encoding="utf-8")
            with mock.patch.object(sys,"argv",[
                "run_original_cup_private_source_acceptance.py",
                "--original-cup-zip",str(root/"missing-cup"),
                "--original-freeze-zip",str(root/"missing-freeze"),
                "--output-report",str(out)]):
                with self.assertRaisesRegex(ValueError,"refusing to overwrite"):
                    runner.main()
            self.assertEqual(out.read_text(encoding="utf-8"),"DO NOT CHANGE ME")

    def test_report_aliasing_an_original_archive_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            cup_path=root/"cup.zip"
            with mock.patch.object(sys,"argv",[
                "script","--original-cup-zip",str(cup_path),
                "--original-freeze-zip",str(root/"freeze.zip"),
                "--output-report",str(cup_path)]):
                # If the target doesn't yet exist, alias check is separate.
                with self.assertRaisesRegex(ValueError,"report path must not"):
                    runner.main()

    def mock_complete_run(self, forced_bad_status=None, tamper_metric=None):
        return_values=[
            ("group_prior","verify_original_cup_lookup",{
                "status":"PASS_OFFICIAL_NBA_GROUP_FIXTURE_AND_DATE_SOURCE_CHECK",
                "group_stage_unordered_opponent_fixtures_checked":180,
                "knockout_stage_games_on_official_dates_checked":18}),
            ("cup_2023_24","compare_to_private_archives",{
                "status":"PASS_EXACT_ORIGINAL_PRIVATE_CUP_AND_TV_SOURCE_MATCH",
                "cup_group_fixtures_exact":120,
                "first_release_network_fields_exact":120}),
            ("cup_2025_19","original_private_compare",{
                "status":"PASS_19_SAME_DAY_ORIGINAL_TEAM_RELEASES_TO_PRIVATE_CUP_LOOKUP",
                "independent_Aug13_source_fixtures_exact_against_original_Cup":19}),
            ("cup_2025_33","check_original_private",{
                "status":"PASS_ORIGINAL_PRIVATE_CUP_33_CONTEMPORANEOUS_FIXTURE_IDENTITIES",
                "independently_transcribed_source_date_host_away_tuples_in_original_Cup":33}),
            ("cup_2025_9tv","compare_original_archives",{
                "status":"PASS_NINE_ORIGINAL_PRIVATE_CUP_AND_TV_SOURCE_TUPLES",
                "source_Cup_game_tuples_exact":9,
                "source_preseason_PDF_network_tuples_exact":9}),
            ("cup_2025_15tv","compare_original_private",{
                "status":"PASS_15_ORIGINAL_PRIVATE_2025_NAMED_NATIONAL_CUP_GAME_TUPLES",
                "original_Cup_fixture_tuples_exact":15,
                "original_preseason_PDF_network_tuples_exact":15}),
            ("later_60","compare_original_private_later_60",{
                "status":"PASS_PRIVATE_CUP_2025_ALL_60_LATER_ESPN_GROUP_FIXTURE_ROWS",
                "later_ESPN_2025_group_fixture_date_away_home_original_private_matches":60}),
            ("knockout","compare_original_private",{
                "status":"PASS_18_ORIGINAL_CUP_ARCHIVE_DATE_UNORDERED_OPPONENTS_AND_12_QF_HOME_AWAY",
                "original_knockout_season_date_stage_opponent_pairs_exact":18,
                "original_quarterfinal_home_away_source_rows_exact":12}),
        ]
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(runner,"original_sha_pins"))
            called=[]
            for mod,name,result in return_values:
                if forced_bad_status==(mod,name):
                    result={**result,"status":"FAILED_AND_MUST_NOT_BE_ACCEPTED"}
                if tamper_metric and tamper_metric[:2]==(mod,name):
                    result={**result,tamper_metric[2]:-1}
                observed=stack.enter_context(
                    mock.patch.object(getattr(runner,mod),name,return_value=result))
                called.append((mod,name,observed))
            outcome=None
            error=None
            try:
                outcome=runner.run_original_private_cup_acceptance(
                    Path("/synthetic/cup.zip"),Path("/synthetic/freeze.zip"))
            except ValueError as e:
                error=e
            return outcome,error,called

    def test_eight_private_subtasks_are_not_skipped_in_mocked_dispatcher(self):
        result,error,called=self.mock_complete_run()
        self.assertIsNone(error)
        self.assertEqual(len(called),8)
        self.assertTrue(all(p.call_count==1 for _,_,p in called))
        self.assertEqual(result["original_private_2025_first_dated_second_tier_aug13_combined_fixtures_exact"],33)
        self.assertEqual(result["original_private_2025_later_Nov01_ESPN_full_fixture_date_home_away_exact"],60)
        self.assertFalse(result["2025_original_Aug13_all_60_first_release_pdf_recovered"])
        self.assertFalse(result["neutral_semifinal_nominal_home_side_source_verified"])
        self.assertFalse(result["all_original_scientific_and_manuscript_gates_closed"])
        self.assertFalse(result["ready_to_merge_PR4"])

    def test_one_wrong_component_status_aborts_entire_master_report(self):
        result,error,_=self.mock_complete_run(
            forced_bad_status=("cup_2025_15tv","compare_original_private"))
        self.assertIsNone(result)
        self.assertRegex(str(error),"strict original-private source subcheck failed")

    def test_eighth_2025_later_ESPN_source_rejects_bad_date_home_away_count(self):
        result,error,_=self.mock_complete_run(
            tamper_metric=("later_60","compare_original_private_later_60",
                           "later_ESPN_2025_group_fixture_date_away_home_original_private_matches"))
        self.assertIsNone(result)
        self.assertRegex(str(error),"later ESPN full 60 actual fixture original lookup mismatch")

    def test_one_wrong_component_row_count_aborts_entire_master_report(self):
        result,error,_=self.mock_complete_run(
            tamper_metric=("knockout","compare_original_private",
                           "original_quarterfinal_home_away_source_rows_exact"))
        self.assertIsNone(result)
        self.assertRegex(str(error),"quarterfinal host mappings incomplete")


if __name__=="__main__":
    unittest.main()
