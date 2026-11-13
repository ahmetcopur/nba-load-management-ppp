"""Offline fail-closed tests for the FINAL dataset reconstruction entry point.

All data here are tiny synthetic fixtures. These are software tests, NOT
scientific verification against the original private NBA source archives.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.data_rebuild import reproduce_final_datasets as final


class FinalDatasetEntrypointTests(unittest.TestCase):
    def test_expected_final_artifacts_are_distinct_and_pinned(self):
        self.assertEqual(len(final.EXPECTED), 3)
        self.assertEqual(len({v["filename"] for v in final.EXPECTED.values()}), 3)
        self.assertEqual(final.EXPECTED["august_latest_pre_tip_full"]["rows"], 248728)
        self.assertEqual(final.EXPECTED["august_latest_pre_tip_at_risk"]["rows"], 180831)
        self.assertEqual(final.EXPECTED["october_cadence_player_games"]["rows"], 248778)
        self.assertEqual(final.EXPECTED["october_cadence_player_games"]["onsets"], 12729)
        for spec in final.EXPECTED.values():
            self.assertEqual(len(spec["decoded_sha256"]), 64)

    def test_build_commands_connect_real_source_stages_in_order(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            jobs = final.stage_commands(root / "archives", root / "run",
                                        verify_original_pdfs=False)
            self.assertEqual([name for name, _ in jobs], [
                "01_august_source_correction", "02_august_analysis_ready",
                "03_frozen_cadence", "04_corrected_cadence",
            ])
            commands = [cmd for _, cmd in jobs]
            self.assertTrue(commands[0][1].endswith("rebuild_august_core_from_source_archives.py"))
            self.assertTrue(commands[1][1].endswith("build_august_analysis_ready_sensitivity.py"))
            self.assertTrue(commands[2][1].endswith("rebuild_from_archives.py"))
            self.assertTrue(commands[3][1].endswith("fixture_date_chronology_sensitivity.py"))
            self.assertIn(str(root / "run/01_august_core/corrected_source/nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz"), commands[1])
            self.assertIn(str(root / "run/03_historical_cadence_inputs"), commands[3])
            self.assertIn(str(root / "archives/nba_game_covariates_v1.zip"), commands[3])
            self.assertIn(str(final.STAGE6_ZIP), commands[3])

    def test_optional_raw_pdf_verification_is_distinct_preceding_stage(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            jobs = final.stage_commands(p / "archives", p / "out",
                                        verify_original_pdfs=True)
            self.assertEqual(len(jobs), 6)
            self.assertEqual(jobs[4][0], "03b_pdf_derived_october_base_handoff")
            self.assertTrue(jobs[0][1][1].endswith("reproduce_core_and_stars.py"))
            for required in ("--from-original-2020-2025-pdfs",
                             "--with-analysis-ready", "--with-october-cadence"):
                self.assertIn(required, jobs[0][1])
            self.assertEqual(jobs[1][0], "01_august_source_correction")
            self.assertIn("--rebuilt-original-selected-players", jobs[1][1])
            self.assertIn(str(p / "out/00_original_pdf_baseline/nba_player_game_at_risk_core_v1/selected_report_player_rows.csv"), jobs[1][1])

    def test_october_pdf_base_handoff_accepts_equal_bytes_and_rejects_tampering(self):
        from scripts.data_rebuild import inject_verified_october_base as bridge
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            source, target, report = (p / name for name in ("pdf.gz", "historical.gz", "report.json"))
            payload = b"player_team_game_id\na\n"
            expected = hashlib.sha256(payload).hexdigest()
            for path in (source, target):
                with gzip.open(path, "wb") as f:
                    f.write(payload)
            result = bridge.inject(source, target, report, expected=expected)
            self.assertEqual(result["substituted_input_decoded_sha256"], expected)
            with self.assertRaises(FileExistsError):
                bridge.inject(source, target, report, expected=expected)
            report.unlink()
            with gzip.open(target, "wb") as f:
                f.write(b"tampered")
            with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
                bridge.inject(source, target, report, expected=expected)

    def test_optional_october_models_require_explicit_external_python(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            with self.assertRaisesRegex(ValueError, "october-python"):
                final.stage_commands(p / "archives", p / "out", verify_original_pdfs=False,
                                     october_shared_repo=p / "checkout")
            jobs = final.stage_commands(
                p / "archives", p / "out", verify_original_pdfs=False,
                october_shared_repo=p / "checkout", october_python=p / "venv/bin/python",
            )
            self.assertTrue(jobs[-1][1][1].endswith("october_corrected_chronology.py"))
            self.assertIn("--corrected-panel", jobs[-1][1])

    def test_private_output_and_archive_locations_rejected_inside_git(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p / ".git").mkdir()
            (p / ".git/HEAD").write_text("ref: refs/heads/main\n")
            arc = p / "source"
            arc.mkdir()
            with self.assertRaisesRegex(ValueError, "OUTSIDE"):
                final.preflight(arc, p / "result", False)

    def test_missing_source_is_blocking_in_check_only(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            arc = p / "archives"
            arc.mkdir()
            with self.assertRaisesRegex(FileNotFoundError, "Missing original ZIP"):
                final.preflight(arc, p / "out", False)

    def test_never_overwrite_existing_results(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            arc, out = p / "source", p / "output"
            arc.mkdir()
            out.mkdir()
            with self.assertRaises(FileExistsError):
                final.preflight(arc, out, False)

    def write_panel(self, path, columns, rows):
        with gzip.open(path, "wt", newline="", encoding="utf-8") as stream:
            w = csv.DictWriter(stream, fieldnames=columns)
            w.writeheader()
            w.writerows(rows)

    def spec_for(self, path, *, rows=2, risk=1, onsets=1):
        return {"decoded_sha256": final.decoded_sha256(path),
                "rows": rows, "risk": risk, "onsets": onsets,
                "risk_field": "at_risk_for_new_onset", "onset_field": "absence_onset"}

    def test_panel_full_hash_counts_and_unique_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fake.csv.gz"
            self.write_panel(path,
                             ["player_team_game_id", "at_risk_for_new_onset", "absence_onset"],
                             [{"player_team_game_id": "a", "at_risk_for_new_onset": "True",
                               "absence_onset": "True"},
                              {"player_team_game_id": "b", "at_risk_for_new_onset": "False",
                               "absence_onset": "False"}])
            result = final.inspect_panel(path, self.spec_for(path))
            self.assertEqual(result["rows"], 2)
            self.assertEqual(result["risk"], 1)
            self.assertEqual(result["onsets"], 1)
            self.assertEqual(result["compressed_sha256"], final.sha256_file(path))

    def test_panel_tampered_payload_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fake.csv.gz"
            cols = ["player_team_game_id", "at_risk_for_new_onset", "absence_onset"]
            self.write_panel(path, cols, [{"player_team_game_id": "a",
                                         "at_risk_for_new_onset": "True",
                                         "absence_onset": "True"}])
            spec = self.spec_for(path, rows=1, risk=1, onsets=1)
            self.write_panel(path, cols, [{"player_team_game_id": "a",
                                         "at_risk_for_new_onset": "True",
                                         "absence_onset": "False"}])
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                final.inspect_panel(path, spec)

    def test_panel_duplicate_keys_rejected_even_if_hash_matches(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fake.csv.gz"
            cols = ["player_team_game_id", "at_risk_for_new_onset", "absence_onset"]
            self.write_panel(path, cols, [
                {"player_team_game_id": "a", "at_risk_for_new_onset": "True", "absence_onset": "True"},
                {"player_team_game_id": "a", "at_risk_for_new_onset": "False", "absence_onset": "False"},
            ])
            with self.assertRaisesRegex(ValueError, "duplicate"):
                final.inspect_panel(path, self.spec_for(path))

    def test_corrected_models_must_match_keys_coefficients_and_p_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "models.json"
            source = {"panel_vs_frozen": {"rebuilt_rows": 248778, "risk_rows": 180664, "onsets": 12729},
                      "stage6_models": [
                          {"definition": "legacy_primary", "controls": "full", "n_corrected": 180530,
                           "estimate_pp_corrected": 2.6742317292365767,
                           "p_corrected": 0.0426339657858416},
                          {"definition": "harmonized_linear", "controls": "full", "n_corrected": 180530,
                           "estimate_pp_corrected": 1.2823694527266445,
                           "p_corrected": 0.3308675408175164},
                          {"definition": "legacy_primary", "controls": "none", "n_corrected": 180664,
                           "estimate_pp_corrected": 2.676885, "p_corrected": 0.04353177},
                          {"definition": "harmonized_linear", "controls": "none", "n_corrected": 180664,
                           "estimate_pp_corrected": 1.294851, "p_corrected": 0.32912241},
                      ]}
            path.write_text(json.dumps(source), encoding="utf-8")
            self.assertEqual(final.verify_model_report(path)["models"], 4)
            source["stage6_models"][0]["p_corrected"] += 0.01
            path.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "p-value"):
                final.verify_model_report(path)

    def test_original_pdf_derived_report_rows_direct_handoff_and_integrity(self):
        import pandas as pd
        from scripts.data_rebuild import rebuild_august_core_from_source_archives as august

        original = pd.DataFrame([
            {"game_id": "g1", "team_norm": "A", "nba_player_id": "1",
             "designation_status": "Out", "designation_reason": "Left ankle sprain"},
            {"game_id": "g2", "team_norm": "B", "nba_player_id": "2",
             "designation_status": "Questionable", "designation_reason": "Right knee soreness"},
        ])
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            target = p / "selected_report_player_rows.csv"
            pdf = p / "rebuilt_from_pdfs.csv"
            original.to_csv(target, index=False)
            original.iloc[::-1].to_csv(pdf, index=False)
            report = august.inject_raw_pdf_rebuilt_selected_players(
                target, pdf, expected_rows=2, expected_columns=5)
            self.assertTrue(report["source_rows_injected_into_original_finalizer_and_corrected_copy"])
            self.assertEqual(pd.read_csv(target, dtype=str).to_dict("records"), original.to_dict("records"))
            target_before = target.read_bytes()
            amended = original.copy()
            amended.loc[0, "designation_reason"] = "Tampered clinical wording"
            amended.to_csv(pdf, index=False)
            with self.assertRaisesRegex(ValueError, "fields differ"):
                august.inject_raw_pdf_rebuilt_selected_players(
                    target, pdf, expected_rows=2, expected_columns=5)
            self.assertEqual(target.read_bytes(), target_before)

    def test_optional_raw_pdf_baseline_links_to_identical_archive_input(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            payload = b"player_team_game_id\nexample\n"
            hash_value = hashlib.sha256(payload).hexdigest()
            mapping = {
                "august_full_core": ("raw/august.csv.gz", "archived/august.csv.gz", hash_value),
                "october_frozen_cadence": ("raw/october.csv.gz", "archived/october.csv.gz", hash_value),
            }
            for pdf, archive, _ in mapping.values():
                for filename in (pdf, archive):
                    target = root / filename
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with gzip.open(target, "wb") as output:
                        output.write(payload)
            with mock.patch.object(final, "PDF_BASELINE_EXPECTED", mapping):
                result = final.verify_raw_pdf_baseline_link(root)
                self.assertEqual(set(result), set(mapping))
                self.assertTrue(result["august_full_core"]["exact_full_csv_equal_via_sha256"])
                with gzip.open(root / "raw/august.csv.gz", "wb") as output:
                    output.write(b"changed source input")
                with self.assertRaisesRegex(ValueError, "baselines differ"):
                    final.verify_raw_pdf_baseline_link(root)

    def test_list_inputs_does_not_require_private_archives_or_pandas(self):
        process = subprocess.run([sys.executable, str(final.TOOLS / "reproduce_final_datasets.py"),
                                  "--list-inputs"], cwd=ROOT, capture_output=True,
                                 text=True, check=True)
        obj = json.loads(process.stdout)
        self.assertIn("nba_game_covariates_v1.zip", obj["required_historical_source_ZIPs"])
        self.assertIn("audit_2020_21_upload.zip", obj["additional_if_verify_original_pdfs"])


if __name__ == "__main__":
    unittest.main()
