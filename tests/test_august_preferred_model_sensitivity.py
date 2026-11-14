"""Negative tests for August latest-pre-tip manuscript-model reproduction gates."""
import importlib.util
from pathlib import Path
import unittest

import pandas as pd

SCRIPT = (Path(__file__).resolve().parents[1] /
          "scripts/data_rebuild/run_august_preferred_model_sensitivity.py")
spec = importlib.util.spec_from_file_location("august_models", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AugustModelValidationTests(unittest.TestCase):
    def test_historical_frozen_anchor_requires_coeff_n_and_se(self):
        true = {
            name: {"n": n, "estimate_pp": estimate, "se_pp": se}
            for name, (n, estimate, se) in mod.FROZEN_ANCHORS.items()
        }
        identity = mod.verify_frozen(true)
        self.assertEqual(set(identity), set(mod.FROZEN_ANCHORS))
        for field, delta in (("n", 1), ("estimate_pp", 0.01), ("se_pp", 0.01)):
            wrong = {key: value.copy() for key, value in true.items()}
            wrong["onset_national_partner"][field] += delta
            with self.assertRaisesRegex(RuntimeError, "Cannot verify original"):
                mod.verify_frozen(wrong)

    def test_historical_small_standard_error_numerical_drift_is_explicit(self):
        values = {
            name: {"n": n, "estimate_pp": estimate, "se_pp": se + 0.000636}
            for name, (n, estimate, se) in mod.FROZEN_ANCHORS.items()
        }
        checks = mod.verify_frozen(values)
        self.assertAlmostEqual(
            checks["vague_conditional"]["se_abs_difference_pp"],
            0.000636, places=9,
        )

    def test_nonbinary_and_null_in_binary_fields_fail_closed(self):
        for value in ("Not Listed", None, "maybe", "2", ""):
            with self.assertRaisesRegex(RuntimeError, "non-binary"):
                mod.strict_binary(pd.Series(["True", value]), "flag")
        self.assertEqual(
            mod.strict_binary(pd.Series(["True", "false", 0, "1.0"]), "flag").tolist(),
            [1.0, 0.0, 0.0, 1.0],
        )

    def test_corrected_and_frozen_sha_pins_differ(self):
        self.assertNotEqual(mod.CORRECTED_SHA, mod.FROZEN_SHA)
        self.assertEqual(len(mod.FROZEN_SHA), 64)
        self.assertEqual(len(mod.CORRECTED_SHA), 64)
        self.assertEqual(mod.CORRECTED_N["vague_conditional"], 6259)


if __name__ == "__main__":
    unittest.main()
