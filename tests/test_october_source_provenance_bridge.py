"""Provenance bridge tests: real-source evidence and decoded public panel equality."""
from __future__ import annotations
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.data_rebuild import verify_source_generated_october_panel_provenance as m


def valid_record():
    return {
        "full_harmonized_panel_exact": {
            "decoded_bytes": m.EXPECTED_BYTES,
            "all_original_and_rebuilt_decoded_CSV_bytes_equal": True,
            "sha256": m.EXPECTED_SHA,
        },
        "original_2025_harmonized_pdf_reparse": {
            "actual_selected_original_pdfs": 355,
            "parsed_report_rows": 13762,
        },
        "generated_full_harmonized_player_game_rows": 248778,
        "original_stage6_zip_sha256": m.EXPECTED_STAGE6_ZIP,
        "original_stage6_four_models": [{"spec":i} for i in range(4)],
        "original_model_comparison": {"all_four_models_match": True},
        "limitations": {
            "raw_2020_21_reason_differences_unresolved": 93,
            "original_harmonized_report_choice_metadata_inherited": True,
            "new_GitHub_script_not_independently_rerun_from_clean_checkout_with_all_private_zips": True,
        },
    }


class OriginalSourceOctoberPanelProvenanceTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.record=self.root/"evidence.json"
        self.public=self.root/"shared_original_panel.csv.gz"
        self.record.write_text(json.dumps(valid_record()))
        self.public.write_bytes(gzip.compress(b"synthetic public panel",mtime=0))

    def test_synthetic_complete_source_record_passes(self):
        self.assertTrue(m.validate_real_source_evidence(valid_record())[
            "source_generated_4_stage6_models"])

    def test_missing_source_original_pdf_count_refused(self):
        value=valid_record()
        value["original_2025_harmonized_pdf_reparse"]["actual_selected_original_pdfs"]=0
        with self.assertRaisesRegex(ValueError,"355|extraction evidence"):
            m.validate_real_source_evidence(value)

    def test_source_equality_cannot_be_inferred_from_gzip_header(self):
        payload=b"synthetic public panel"
        self.public.write_bytes(gzip.compress(payload,mtime=42))
        sha, count=m.hash_decoded_gzip(self.public)
        import hashlib
        self.assertEqual(sha,hashlib.sha256(payload).hexdigest())
        self.assertEqual(count,len(payload))

    def test_tampered_panel_fingerprint_refused(self):
        value=valid_record()
        value["full_harmonized_panel_exact"]["sha256"]="tampered"
        with self.assertRaisesRegex(ValueError,"equality evidence"):
            m.validate_real_source_evidence(value)

    def test_missing_scientific_limitations_refused(self):
        value=valid_record()
        value["limitations"].pop("raw_2020_21_reason_differences_unresolved")
        with self.assertRaisesRegex(ValueError,"limitations"):
            m.validate_real_source_evidence(value)

    def test_wrong_number_of_original_models_refused(self):
        value=valid_record()
        value["original_stage6_four_models"].pop()
        with self.assertRaisesRegex(ValueError,"four Stage-6"):
            m.validate_real_source_evidence(value)

    def test_source_zip_drift_refused(self):
        value=valid_record()
        value["original_stage6_zip_sha256"]="changed"
        with self.assertRaisesRegex(ValueError,"fingerprint changed"):
            m.validate_real_source_evidence(value)

    def test_public_gzip_digest_mismatch_refused_even_if_evidence_claims_pass(self):
        with self.assertRaisesRegex(ValueError,"public panel differs"):
            m.verify_equality(self.public,self.record)

    def test_match_of_actual_decoded_public_bytes_passes(self):
        with patch.object(m,"hash_decoded_gzip",
                          return_value=(m.EXPECTED_SHA,m.EXPECTED_BYTES)):
            result=m.verify_equality(self.public,self.record)
        self.assertEqual(result["status"],"pass")
        self.assertFalse(result["full_10_script_from_original_private_PDFs_directly_executed_in_CI"])

    def test_wrong_public_byte_length_refused_even_if_SHA_matches(self):
        with patch.object(m,"hash_decoded_gzip",
                          return_value=(m.EXPECTED_SHA,12)):
            with self.assertRaisesRegex(ValueError,"public panel differs"):
                m.verify_equality(self.public,self.record)

    def test_real_committed_evidence_matches_expected_schema(self):
        record=json.loads(m.EVIDENCE.read_text(encoding="utf-8"))
        data=m.validate_real_source_evidence(record)
        self.assertEqual(data["source_generated_original_selected_2025_harmonized_PDFs"],355)

    def test_missing_public_panel_refused(self):
        with self.assertRaisesRegex(FileNotFoundError,"public October panel"):
            m.verify_equality(self.root/"missing.gz",self.record)


if __name__=="__main__":
    unittest.main()
