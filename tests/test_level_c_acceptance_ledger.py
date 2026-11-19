"""Acceptance ledger tests prevent chronological evidence drift and overclaims.

These operate exclusively on sanitized, already committed historical
source-execution evidence, not private NBA player-level records.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.data_rebuild import verify_level_c_acceptance_ledger as ledger


class LevelCAcceptanceLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = ledger.read_evidence(ledger.REPO)

    def mutated(self):
        return copy.deepcopy(self.actual)

    def test_all_five_original_source_evidence_documents_cross_check(self):
        result = ledger.audit(self.actual)
        self.assertEqual(result["source_evidence_files_checked"], 10)
        self.assertEqual(
            result["verified"]["six_seasons_original_core_star_Cup_full_output_files_exact"],25)
        self.assertEqual(result["status"],"ACCEPTED_COMPONENTS_WITH_OPEN_RESEARCH_GATES")

    def test_2020_mismatch_resolved_at_source_not_every_provenance_gate(self):
        result = ledger.audit(self.actual)
        self.assertTrue(
            result["verified"]["original_2020_reason_only_drift_resolved_at_source_row_level"])
        self.assertTrue(
            result["still_open"]["separately_packaged_new_GitHub_2020_CLI_direct_private_execution"])
        self.assertTrue(result["verified"]["fresh_direct_617_original_PDFs_reparsed_and_exact_full_source"])
        self.assertFalse(result["all_research_gates_closed"])
        self.assertFalse(result["PR_4_ready_to_merge"])

    def test_original_2020_93_reason_mismatches_must_have_zero_after_repair(self):
        changed=self.mutated()
        changed["source_2020"]["source_2020"]["remaining_source_reason_mismatch_rows"]=1
        with self.assertRaisesRegex(ValueError,"reason drift"):
            ledger.audit(changed)

    def test_all_2020_source_fields_must_be_reparsed_not_copied_from_reference(self):
        changed=self.mutated()
        changed["source_2020"]["source_2020"]["borrowed_frozen_reason_values_for_repair"]=True
        with self.assertRaisesRegex(ValueError,"may not be borrowed"):
            ledger.audit(changed)

    def test_fresh_full_617_PDF_source_evidence_cannot_be_replaced_by_prior_diagnostic(self):
        changed=self.mutated()
        changed["fresh_2020"]["actual_new_private_execution"]["fresh_original_PDFs_extracted_and_parsed"]=0
        with self.assertRaisesRegex(ValueError,"fresh original 617-PDF"):
            ledger.audit(changed)

    def test_fresh_full_2020_PDF_parser_hash_must_match_original(self):
        changed=self.mutated()
        changed["fresh_2020"]["historical_original_parser_sha256"]="changed"
        with self.assertRaisesRegex(ValueError,"parser hashes"):
            ledger.audit(changed)

    def test_six_season_ID_output_full_row_count_must_match(self):
        changed=self.mutated()
        changed["six_core_star_cup"]["resolved_player_report_rows_exact"]=73437
        with self.assertRaisesRegex(ValueError,"source inputs"):
            ledger.audit(changed)

    def test_missing_one_of_25_exact_outputs_is_not_accepted(self):
        changed=self.mutated()
        changed["six_core_star_cup"]["cup_output_files_full_decoded_byte_exact"]=2
        with self.assertRaisesRegex(ValueError,"10/12/3"):
            ledger.audit(changed)

    def test_six_season_direct_master_script_cannot_be_claimed_accepted_without_proof(self):
        changed=self.mutated()
        changed["six_core_star_cup"]["limitations"][
            "newly_committed_all_six_season_master_umbrella_direct_private_run_completed"]=True
        with self.assertRaisesRegex(ValueError,"not established"):
            ledger.audit(changed)

    def test_august_model_must_be_from_rebuilt_five_season_analysis_panel(self):
        changed=self.mutated()
        changed["august_model"]["new_analysis_ready_model_input_decoded_sha256"]="bogus"
        with self.assertRaisesRegex(ValueError,"August model"):
            ledger.audit(changed)

    def test_old_october_report_is_chronologically_distinct_from_current_2020_resolution(self):
        changed=self.mutated()
        changed["october_source"]["limitations"]["raw_2020_21_reason_differences_unresolved"]=0
        with self.assertRaisesRegex(ValueError,"chronological 2020"):
            ledger.audit(changed)

    def test_exact_harmonized_panel_SHA_is_enforced(self):
        changed=self.mutated()
        changed["october_source"]["full_harmonized_panel_exact"]["sha256"]="changed"
        with self.assertRaisesRegex(ValueError,"entire decoded equality"):
            ledger.audit(changed)

    def test_all_original_model_p_values_and_source_count_are_separate(self):
        result=ledger.audit(self.actual)
        self.assertEqual(result["verified"]["five_seasons_original_August_FE_coefficient_rows_reproduced"],44)
        self.assertTrue(result["still_open"]["six_season_private_source_generated_October_model_suite_rerun"])
        self.assertTrue(result["still_open"]["independent_star_awards_and_game_covariate_provenance"])

    def test_fresh_six_season_reviewed_model_data_exact_against_previous_five_season_reference(self):
        result=ledger.audit(self.actual)
        self.assertEqual(result["verified"]["six_seasons_reviewed_analysis_ready_full_outputs_exact"],2)
        changed=self.mutated()
        changed["six_reviewed"]["actual_private_execution"]["generated_outputs"][1]["decoded_sha256"]="changed"
        with self.assertRaisesRegex(ValueError,"six-season source-derived reviewed"):
            ledger.audit(changed)

    def test_actual_six_original_PDF_season_August_model_fits_original_44_coefficients(self):
        result=ledger.audit(self.actual)
        self.assertEqual(result["verified"]["six_seasons_original_August_FE_coefficient_rows_reproduced"],44)
        changed=self.mutated()
        changed["six_august_model"]["original_complete_result_comparisons"]["teamseason_fe_coefficients.csv"]["max_absolute_numeric_difference"]=0.25
        with self.assertRaisesRegex(ValueError,"44 model result rows"):
            ledger.audit(changed)

    def test_six_original_pdf_season_August_model_source_code_must_be_original(self):
        changed=self.mutated()
        changed["six_august_model"]["original_historical_model"]["original_code_sha256"]="tampered"
        with self.assertRaisesRegex(ValueError,"model source/code"):
            ledger.audit(changed)

    def test_original_2182_human_reviewed_labels_not_overclaimed(self):
        changed=self.mutated()
        changed["six_reviewed"]["reviewed_archive_source"]["label_contents_independently_medically_adjudicated"]=True
        with self.assertRaisesRegex(ValueError,"human-reviewed"):
            ledger.audit(changed)

    def test_actual_original_NBA_Cup_group_and_knockout_dates_independent_checks(self):
        result=ledger.audit(self.actual)
        self.assertEqual(result["verified"]["independently_verified_NBA_Cup_original_group_opponent_pairings"],180)
        self.assertEqual(result["verified"]["independently_verified_NBA_Cup_knockout_stage_date_rows"],18)
        self.assertTrue(result["still_open"]["independent_NBA_Cup_exact_per_fixture_dates_and_TV_provider_provenance"])

    def test_official_NBA_Cup_source_season_must_not_be_omitted(self):
        changed=self.mutated()
        changed["official_cup"]["result_by_season"].pop()
        with self.assertRaisesRegex(ValueError,"archive release seasons are missing"):
            ledger.audit(changed)

    def test_original_Cup_verified_game_lookup_sha_must_be_immutable(self):
        changed=self.mutated()
        changed["official_cup"]["original_source_archive_sha256"]="modified"
        with self.assertRaisesRegex(ValueError,"immutable 7,230-game source"):
            ledger.audit(changed)

    def test_official_Cup_per_fixture_TV_knowledge_cannot_be_overclaimed(self):
        changed=self.mutated()
        changed["official_cup"]["research_scope_boundaries"]["official_TV_broadcast_provider_schedule_independently_verified"]=True
        with self.assertRaisesRegex(ValueError,"may not claim individual fixture dates or TV providers"):
            ledger.audit(changed)

    def test_independent_original_NBA_TV_PDF_and_HTML_broadcast_source_rows(self):
        result=ledger.audit(self.actual)
        self.assertEqual(result["verified"]["independently_extracted_original_NBA_preseason_PDF_network_rows"],6060)
        self.assertEqual(result["verified"]["independently_extracted_original_2020_broadcaster_HTML_network_rows"],219)
        self.assertEqual(result["verified"]["independently_validated_six_season_advance_announced_primary_TV_games"],1041)

    def test_an_original_2025_streaming_network_schedule_row_change_fails(self):
        changed=self.mutated()
        changed["official_tv"]["source_2021_2025"]["original_primary_TV_classification_mismatches"]=1
        with self.assertRaisesRegex(ValueError,"6,060 original NBA PDF"):
            ledger.audit(changed)

    def test_original_2020_incomplete_NBA_TV_coverage_stays_a_limitation(self):
        changed=self.mutated()
        changed["official_tv"]["source_2020_21"]["complete_original_2020_NBA_TV_second_half_schedule_recovered"]=True
        with self.assertRaisesRegex(ValueError,"incomplete NBA TV coverage"):
            ledger.audit(changed)

    def test_unknown_original_Cup_matchups_not_backfilled(self):
        changed=self.mutated()
        changed["official_tv"]["source_2021_2025"]["unannounced_Cup_determined_games"]=89
        with self.assertRaisesRegex(ValueError,"6,060 original NBA PDF"):
            ledger.audit(changed)

    def test_original_NBA_advance_TV_archive_SHA_must_not_drift(self):
        changed=self.mutated()
        changed["official_tv"]["original_source_archives"]["original_03_announced_tv_six_seasons_nested_zip_sha256"]="tampered"
        with self.assertRaisesRegex(ValueError,"broadcast PDF/HTML source archives changed"):
            ledger.audit(changed)

    def test_public_CI_does_not_claim_live_CDN_byte_redownload(self):
        changed=self.mutated()
        changed["official_tv"]["research_limitations"]["fresh_direct_re_download_and_binary_SHA_match_against_live_NBA_CDN_not_completed"]=False
        with self.assertRaisesRegex(ValueError,"may not claim future"):
            ledger.audit(changed)

    def test_missing_original_evidence_document_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(FileNotFoundError,"historical evidence not found"):
                ledger.read_evidence(Path(tmp))


if __name__=="__main__":
    unittest.main()
