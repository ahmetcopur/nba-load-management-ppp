# Nonlinear / Multinomial Reproducibility Note

The frozen nonlinear robustness results are preserved in
`packages/08_nonlinear_multinomial_robustness.zip`.

## Provenance verification

The following were verified byte-for-byte against the archived analysis:

- `run_nonlinear_multinomial_stage.py`
- canonical at-risk player-game panel
- announced-TV crosswalk
- cadence-harmonized player-team-game panel

The archived executed script and the script contained inside the frozen package
have identical SHA256 hashes.

## Numerical reproducibility

The nonlinear stage uses regularized logistic and multinomial logistic
regression. Re-execution produced modestly different point estimates across
computational environments despite identical code and input data.

Frozen primary nonlinear absence DDD:
- Legacy TV: 2.4400 pp
- Harmonized TV: 0.8271 pp

macOS re-execution:
- Legacy TV: 2.1152 pp
- Harmonized TV: 1.4429 pp

GitHub Actions Ubuntu re-execution:
- Legacy TV: 2.5060 pp
- Harmonized TV: 1.2827 pp

The conditional vague-vs-specific estimates remained negative across all
executions, and the qualitative comparison between the legacy and harmonized
TV definitions was preserved.

Accordingly, this stage should be interpreted as a functional-form diagnostic,
not as the inferential anchor of the study. Statistical inference remains
anchored to the frozen two-way-clustered linear probability models.

The archived frozen result files remain the reported results for this stage.
Portable re-execution is expected to reproduce the substantive conclusions,
but exact floating-point coefficients are environment-sensitive.
