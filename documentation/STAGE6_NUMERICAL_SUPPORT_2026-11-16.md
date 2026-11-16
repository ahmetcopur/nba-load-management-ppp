# Stage-6 estimator: supported platform and numerical guards (November 16, 2026)

The historical estimator `scripts/executed/06_cadence_harmonized_identification/run_cadence_models_fast.py` is immutable and has not been edited. This note records why its output is trusted only on one platform, and what now enforces that.

## The issue

The full-control design includes both `games_before_10` and `dist65_10 = 6.5 - games_before_10`. After fixed-effect absorption the design has 22 columns but rank 21. statsmodels' pinv-based OLS drops the null direction only when its singular-value ratio falls below `rcond = 1e-15`.

Measurements on the public frozen panel (`3c161f95…`), with `requirements-lock.txt` and Python 3.12:

| Platform | numpy BLAS | Smallest/largest singular value | Legacy full-control result | Harmonized full-control result | Replay verdict |
| --- | --- | --- | --- | --- | --- |
| Linux x86-64 (linux/amd64 container) | scipy-openblas | 3.6e-16 (null direction dropped) | +2.6304485902 pp, SE 1.3187 | +1.2389703651 pp | matches archive |
| macOS arm64 | Apple Accelerate | 1.7e-15 (null direction kept) | +2.6295 pp, **SE 27,765 pp, p = .9999** | **ZeroDivisionError** | fails |

The no-control models have full rank and agree on both platforms.

A separately versioned diagnostic that drops the redundant `dist65_10` column (run outside the repository; the historical executable is unchanged) reproduces the Linux values on macOS: +2.6304485902 pp, SE 1.31872 pp, p = .04608. So the accepted Linux estimates, standard errors and p-values are correct. The macOS failure is a covariance-computation failure, not evidence against the published values.

Audit finding SCI-003 (`validation/scientific_integrity_audit_2026-11-15/findings.json`) rated this "low", with "only a tiny finite-sample covariance correction". That holds on Linux/OpenBLAS but not across platforms, so for reproducibility its effective severity is high. The audit record itself is left unchanged as historical evidence.

## What now enforces it

`scripts/data_rebuild/stage6_numerics.py` is used by every caller of the historical estimator: `replay_stage6_from_frozen.py`, `reproduce_october_scientific_v2.py`, `fixture_date_chronology_sensitivity.py`, `run_fixture_date_control_sensitivity.py` and `rebuild_october_cadence_from_generated_core.py`.

1. **Platform guard.** It refuses to run the estimator except on Linux x86-64 with numpy linked to OpenBLAS (GitHub Actions `ubuntu-latest`, or a `linux/amd64` container). `NBA_STAGE6_ALLOW_UNSUPPORTED_PLATFORM=1` permits an explicitly labelled diagnostic run elsewhere.
2. **Output check on every platform.** Each full-control SE must be within 0.5–2× its full-rank no-control SE. Observed ratios are 0.995 on the real panel and 1.03–1.05 on the synthetic test panel; a kept null direction inflates the SE by orders of magnitude. A finite but exploded SE is therefore rejected rather than accepted.

No accepted estimate, hash, tolerance or historical target changed. Tests: `tests/test_stage6_numerics.py`.
