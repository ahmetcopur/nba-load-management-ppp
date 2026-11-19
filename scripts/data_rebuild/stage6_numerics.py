"""Numerical safeguards around the immutable historical Stage-6 estimator.

`scripts/executed/06_cadence_harmonized_identification/run_cadence_models_fast.py`
is never edited. Its full-control design is exactly rank-deficient:
`dist65_10 = 6.5 - games_before_10`, so after fixed-effect absorption the two
columns are collinear (22 columns, rank 21). statsmodels' pinv-based OLS drops
the null direction only when its singular-value ratio falls below
rcond = 1e-15. Measured on the public frozen panel:

* Linux x86-64, numpy wheels with OpenBLAS: ratio about 3.6e-16, the direction
  is dropped, and the archived results reproduce exactly.
* macOS arm64, numpy wheels with Apple Accelerate: ratio about 1.7e-15, the
  direction is kept, and the clustered covariance explodes (legacy full-control
  SE about 27,765 pp) or divides by zero (harmonized full control).

Point estimates are identified either way. Only the covariance is unreliable,
and a finite but exploded SE passes simple finiteness checks. These guards:

1. `require_supported_platform()` refuses unsupported platforms clearly before
   the estimator runs. Set NBA_STAGE6_ALLOW_UNSUPPORTED_PLATFORM=1 only for
   diagnostics; the results are then labelled as unsupported.
2. `validate_model_rows()` rejects invalid output on any platform. Each
   full-control SE must be within SE_RATIO_LIMITS of its no-control SE. The
   no-control design has full rank, so its covariance is stable. Adding
   controls cannot plausibly change the clustered SE of the focal interaction
   by more than a factor of two here (observed ratio 0.99 to 1.05 on the real
   and synthetic panels), while a kept null direction inflates it by orders of
   magnitude.
"""
from __future__ import annotations

import math
import os
import platform

OVERRIDE_ENV = "NBA_STAGE6_ALLOW_UNSUPPORTED_PLATFORM"
SE_RATIO_LIMITS = (0.5, 2.0)
SUPPORTED_DESCRIPTION = "Linux x86-64 with numpy linked to OpenBLAS (the GitHub Actions ubuntu-latest and linux/amd64 container environment)"


class Stage6NumericalError(RuntimeError):
    """Raised when historical Stage-6 output is numerically invalid."""


class UnsupportedStage6Platform(RuntimeError):
    """Raised when the historical estimator would run outside its validated platform."""


def blas_name() -> str:
    try:
        import numpy
        config = numpy.show_config(mode="dicts")
        return str(config["Build Dependencies"]["blas"]["name"])
    except Exception:  # Older numpy or unusual builds: report, do not guess.
        return "unknown"


def platform_identity() -> dict:
    return {"system": platform.system(), "machine": platform.machine(), "blas": blas_name()}


def is_supported(identity: dict) -> bool:
    return (identity["system"] == "Linux"
            and identity["machine"].lower() in {"x86_64", "amd64"}
            and "openblas" in identity["blas"].lower())


def platform_status(environ=None) -> dict:
    """Report (never raise) whether the estimator may run here; for preflight output."""
    environ = os.environ if environ is None else environ
    identity = platform_identity()
    supported = is_supported(identity)
    override = (not supported) and environ.get(OVERRIDE_ENV) == "1"
    return {**identity, "supported_platform": supported, "unsupported_platform_override": override}


def require_supported_platform(environ=None) -> dict:
    status = platform_status(environ)
    identity = {k: status[k] for k in ("system", "machine", "blas")}
    supported, override = status["supported_platform"], status["unsupported_platform_override"]
    if not supported and not override:
        raise UnsupportedStage6Platform(
            f"The historical Stage-6 estimator is validated only on {SUPPORTED_DESCRIPTION}; "
            f"this machine is {identity}. Its rank-deficient full-control covariance is not "
            f"reliable here (see scripts/data_rebuild/stage6_numerics.py). Run in a linux/amd64 "
            f"container, or set {OVERRIDE_ENV}=1 for an explicitly unsupported diagnostic run.")
    return status


def _number(row: dict, field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError):
        raise Stage6NumericalError(f"Stage-6 row lacks numeric {field}: {row}") from None
    if not math.isfinite(value):
        raise Stage6NumericalError(f"Non-finite Stage-6 {field}: {row}")
    return value


def validate_model_rows(rows) -> dict:
    """Validate the four historical Stage-6 rows (or any full/none pairs).

    Returns the full-to-none SE ratios. Raises Stage6NumericalError otherwise.
    """
    rows = list(rows)
    by_key = {}
    for row in rows:
        key = (str(row["definition"]), str(row["controls"]))
        if key in by_key:
            raise Stage6NumericalError(f"Duplicate Stage-6 specification {key}")
        for field in ("estimate_pp", "low_pp", "high_pp"):
            _number(row, field)
        se = _number(row, "se_pp")
        p = _number(row, "p")
        if se <= 0:
            raise Stage6NumericalError(f"Non-positive Stage-6 standard error: {row}")
        if not 0 < p <= 1:
            raise Stage6NumericalError(f"Stage-6 p-value outside (0, 1]: {row}")
        by_key[key] = se
    ratios = {}
    for (definition, controls), se in sorted(by_key.items()):
        if controls != "full":
            continue
        baseline = by_key.get((definition, "none"))
        if baseline is None:
            raise Stage6NumericalError(f"No full-rank no-control row to check {definition} against")
        ratio = se / baseline
        low, high = SE_RATIO_LIMITS
        if not low <= ratio <= high:
            raise Stage6NumericalError(
                f"{definition} full-control SE {se:.6g} pp is {ratio:.3g} times its no-control SE "
                f"{baseline:.6g} pp (allowed {low}-{high}). This is the rank-deficient covariance "
                f"failure described in scripts/data_rebuild/stage6_numerics.py; do not use these values.")
        ratios[definition] = ratio
    if not ratios:
        raise Stage6NumericalError("No full-control Stage-6 rows to validate")
    return {"se_ratio_full_to_none": ratios, "se_ratio_limits": list(SE_RATIO_LIMITS)}
