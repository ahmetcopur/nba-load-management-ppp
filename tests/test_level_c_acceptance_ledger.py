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
        self.assertEqual(result["source_evidence_files_checked"], 5)
        self.assertEqual(
            result["verified"]["six_seasons_original_core_star_Cup_full_output_files_exact"],25)
        self.assertEqual(result["status"],"ACCEPTED_COMPONENTS_WITH_OPEN_RESEARCH_GATES")

    def test_2020_mismatch_resolved_at_source_not_every_provenance_gate(self):
        result = ledger.audit(self.actual)
        self.assertTrue(
            result["verified"]["original_2020_reason_only_drift_resolved_at_source_row_level"])
        self.assertTrue(
            result["still_open"]["direct_fresh_reparse_of_all_617_original_2020_PDFs_with_repaired_CLI"])
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
        self.assertTrue(result["still_open"]["six_season_new_analysis_ready_and_original_August_October_model_rerun"])
        self.assertTrue(result["still_open"]["independent_star_awards_Cup_TV_and_game_covariate_provenance"])

    def test_missing_original_evidence_document_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(FileNotFoundError,"historical evidence not found"):
                ledger.read_evidence(Path(tmp))


if __name__=="__main__":
    unittest.main()
