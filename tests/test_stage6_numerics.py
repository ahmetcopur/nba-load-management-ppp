"""Numerical safeguards for the immutable historical Stage-6 estimator."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "scripts/data_rebuild"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import stage6_numerics as numerics  # noqa: E402
from compare_stage6_models import archived_rows  # noqa: E402

ARCHIVE = REPO / "packages/06_cadence_harmonized_identification.zip"

# Observed on macOS arm64 (Apple Accelerate) with requirements-lock.txt, public frozen panel.
MACOS_EXPLODED = [
    {"definition": "legacy_primary", "controls": "full", "estimate_pp": 2.629468727591372,
     "se_pp": 27765.140237545722, "low_pp": -54417.04539686202, "high_pp": 54422.30433431721,
     "p": 0.9999244371726642},
    {"definition": "legacy_primary", "controls": "none", "estimate_pp": 2.632768780381443,
     "se_pp": 1.3257085858884818, "low_pp": 0.0343799520400187, "high_pp": 5.231157608722867,
     "p": 0.04704073447801744},
]


class ValidateModelRowsTests(unittest.TestCase):
    def test_archived_linux_results_pass(self):
        report = numerics.validate_model_rows(archived_rows(ARCHIVE))
        self.assertEqual(set(report["se_ratio_full_to_none"]), {"legacy_primary", "harmonized_linear"})
        for ratio in report["se_ratio_full_to_none"].values():
            self.assertAlmostEqual(ratio, 0.995, delta=0.01)

    def test_exploded_rank_deficient_covariance_is_rejected(self):
        with self.assertRaisesRegex(numerics.Stage6NumericalError, "rank-deficient covariance"):
            numerics.validate_model_rows(MACOS_EXPLODED)

    def test_moderate_inflation_beyond_limit_is_rejected(self):
        rows = [dict(MACOS_EXPLODED[0], se_pp=171.05, p=0.986), MACOS_EXPLODED[1]]
        with self.assertRaises(numerics.Stage6NumericalError):
            numerics.validate_model_rows(rows)

    def test_invalid_values_are_rejected(self):
        good_full = dict(MACOS_EXPLODED[0], se_pp=1.3187, low_pp=0.0457, high_pp=5.2151, p=0.046)
        none = MACOS_EXPLODED[1]
        cases = {
            "Non-finite": [dict(good_full, estimate_pp=float("nan")), none],
            "Non-positive": [dict(good_full, se_pp=0.0), none],
            "outside": [dict(good_full, p=0.0), none],
            "lacks numeric": [{k: v for k, v in good_full.items() if k != "p"}, none],
            "Duplicate": [good_full, good_full, none],
            "No full-rank": [good_full],
            "No full-control": [none],
        }
        for message, rows in cases.items():
            with self.subTest(message=message):
                with self.assertRaisesRegex(numerics.Stage6NumericalError, message):
                    numerics.validate_model_rows(rows)
        numerics.validate_model_rows([good_full, none])


class PlatformGuardTests(unittest.TestCase):
    LINUX = {"system": "Linux", "machine": "x86_64", "blas": "scipy-openblas"}
    MAC = {"system": "Darwin", "machine": "arm64", "blas": "accelerate"}

    def test_linux_openblas_is_supported(self):
        with mock.patch.object(numerics, "platform_identity", return_value=self.LINUX):
            result = numerics.require_supported_platform(environ={})
        self.assertTrue(result["supported_platform"])
        self.assertFalse(result["unsupported_platform_override"])

    def test_other_platforms_fail_clearly(self):
        for identity in (self.MAC, {**self.LINUX, "blas": "mkl"}, {**self.LINUX, "machine": "aarch64"}):
            with self.subTest(identity=identity):
                with mock.patch.object(numerics, "platform_identity", return_value=identity):
                    with self.assertRaisesRegex(numerics.UnsupportedStage6Platform, "validated only on"):
                        numerics.require_supported_platform(environ={})

    def test_explicit_override_is_labelled(self):
        with mock.patch.object(numerics, "platform_identity", return_value=self.MAC):
            result = numerics.require_supported_platform(environ={numerics.OVERRIDE_ENV: "1"})
        self.assertFalse(result["supported_platform"])
        self.assertTrue(result["unsupported_platform_override"])

    def test_frozen_replay_refuses_before_running_estimator(self):
        import replay_stage6_from_frozen as replay
        with mock.patch.object(numerics, "platform_identity", return_value=self.MAC), \
             mock.patch.dict("os.environ", {}, clear=False) as env, \
             mock.patch.object(replay.subprocess, "run") as run, \
             mock.patch.object(sys, "argv", ["replay", "--output-dir", "/nonexistent/stage6"]):
            env.pop(numerics.OVERRIDE_ENV, None)
            with self.assertRaises(numerics.UnsupportedStage6Platform):
                replay.main()
        run.assert_not_called()


class EarlyRefusalTests(unittest.TestCase):
    MAC = PlatformGuardTests.MAC

    def test_platform_status_reports_without_raising(self):
        with mock.patch.object(numerics, "platform_identity", return_value=self.MAC):
            status = numerics.platform_status(environ={})
        self.assertFalse(status["supported_platform"])
        self.assertFalse(status["unsupported_platform_override"])

    def test_final_dataset_build_refuses_before_stages_but_finalize_may_run_anywhere(self):
        import importlib
        final = importlib.import_module("scripts.data_rebuild.reproduce_final_datasets")
        shared = importlib.import_module("scripts.data_rebuild.stage6_numerics")
        reached = RuntimeError("reached first builder stage")
        with mock.patch.object(shared, "platform_identity", return_value=self.MAC), \
             mock.patch.dict("os.environ", {}, clear=False) as env, \
             mock.patch.object(final, "preflight", return_value=[]), \
             mock.patch.object(final, "preflight_original_boxscores", return_value=None), \
             mock.patch.object(final, "stage_commands", side_effect=reached), \
             mock.patch.object(final, "completed_stage_logs", side_effect=reached), \
             mock.patch("importlib.metadata.version", return_value="2.2.3"):
            env.pop(numerics.OVERRIDE_ENV, None)
            with self.assertRaises(shared.UnsupportedStage6Platform):
                final.build(Path("/archives"), Path("/new-output"))
            with self.assertRaises(RuntimeError) as finalize:
                final.build(Path("/archives"), Path("/new-output"), finalize_existing=True)
            self.assertNotIsInstance(finalize.exception, shared.UnsupportedStage6Platform)


class CallerWiringTests(unittest.TestCase):
    """Every caller of the historical estimator must apply both guards."""

    CALLERS = ["replay_stage6_from_frozen.py", "reproduce_october_scientific_v2.py",
               "fixture_date_chronology_sensitivity.py", "run_fixture_date_control_sensitivity.py",
               "rebuild_october_cadence_from_generated_core.py"]

    def test_all_callers_use_guards(self):
        for name in self.CALLERS:
            text = (TOOLS / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn("require_supported_platform()", text)
                self.assertIn("validate_model_rows(", text)

    def test_callers_keep_guard_results_for_their_reports(self):
        # A bare call would drop an explicit unsupported-platform override from the report.
        for name in self.CALLERS:
            lines = (TOOLS / name).read_text(encoding="utf-8").splitlines()
            with self.subTest(name=name):
                bare = [line.strip() for line in lines
                        if line.strip().startswith(("require_supported_platform(", "validate_model_rows("))]
                self.assertEqual(bare, [])

    def test_chronology_rerun_records_override_and_validation(self):
        import importlib.util
        import io
        import subprocess
        import tempfile
        import zipfile
        spec = importlib.util.spec_from_file_location(
            "chronology_for_guard_test", TOOLS / "fixture_date_chronology_sensitivity.py")
        chron = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(chron)
        guard_module = sys.modules[chron.require_supported_platform.__module__]
        with zipfile.ZipFile(ARCHIVE) as archive:
            archived = archive.read("results/cadence_harmonized_model_results.csv")

        def fake_run(command, cwd, **kwargs):
            (Path(cwd) / "cadence_harmonized_results/cadence_harmonized_model_results.csv").write_bytes(archived)
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "panel.csv.gz").write_bytes(b"placeholder")
            checks = {}
            with mock.patch.object(guard_module, "platform_identity", return_value=PlatformGuardTests.MAC), \
                 mock.patch.dict("os.environ", {numerics.OVERRIDE_ENV: "1"}), \
                 mock.patch.object(chron.subprocess, "run", side_effect=fake_run):
                rows = chron.rerun_original_models(root / "panel.csv.gz", ARCHIVE, root, checks)
        self.assertEqual(len(rows), 4)
        self.assertTrue(checks["stage6_platform"]["unsupported_platform_override"])
        self.assertFalse(checks["stage6_platform"]["supported_platform"])
        self.assertEqual(set(checks["stage6_numerical_validation"]["se_ratio_full_to_none"]),
                         {"legacy_primary", "harmonized_linear"})

    def test_no_unguarded_caller_of_historical_estimator(self):
        callers = {path.name for path in TOOLS.glob("*.py")
                   if "run_cadence_models_fast" in path.read_text(encoding="utf-8")}
        # scientific_case_checkpoint only re-hashes the source; it never executes it.
        self.assertEqual(callers - {"scientific_case_checkpoint.py", "stage6_numerics.py"}, set(self.CALLERS))


if __name__ == "__main__":
    unittest.main()
