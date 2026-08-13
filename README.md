# NBA Disguised Load Management Project — Final Analysis Freeze

Freeze date: **2026-08-12**

This package freezes the completed empirical analysis for the six-season NBA Player Participation Policy project.

## What is frozen

- Empirical window: 2020-21 through 2025-26 regular seasons.
- Unit: player × team × game.
- Main outcome: onset of a new absence spell among player-games at risk.
- Main estimand: `Star × PostPPP × AnnouncedTV`.
- Main inferential model: linear probability model with player and team-season fixed effects, full pregame controls, and two-way clustered standard errors by player and game.
- Original/legacy advance-national-TV definition is retained as the historical main exposure.
- Harmonized national-TV and cadence-harmonized injury-report timing are mandatory sensitivities and must be reported alongside the legacy result.
- Injury-label taxonomy is frozen at v2.
- Heterogeneity definitions are frozen as executed; age/career-stage heterogeneity was not run because reliable metadata were not in the frozen panel.

No additional specification should replace the frozen suite merely because it gives a more favorable coefficient.

## Directory guide

- `results/FINAL_RESULTS_TABLE.csv` — single master table of the frozen estimates and diagnostics.
- `results/CORE_MANUSCRIPT_RESULTS.csv` — compact set for the main paper.
- `documentation/CLAIMS_AND_LIMITATIONS.md` — what the paper can and cannot say.
- `documentation/FROZEN_SPECIFICATION.md` — exact analytical choices.
- `documentation/MANUSCRIPT_READY_RESULTS.md` — suggested results wording.
- `documentation/TAXONOMY_VALIDATION_PROVENANCE.md` — correct description of the 300-spell validation.
- `documentation/RAW_DATA_AND_REPRODUCIBILITY_SCOPE.md` — what is and is not bundled.
- `data_final/` — final analysis-ready panels and frozen spell taxonomy.
- `packages/` — exact milestone packages in execution order.
- `validation/` — taxonomy scoring artifacts.
- `MANIFEST_SHA256.csv` — hashes for every file in this freeze.

## Quick reproduction

Create a Python 3.12 environment and install the frozen analysis dependencies.
See `requirements.txt` and `requirements-lock.txt` for the dependency set.

The scripts in `scripts/portable/` use repository-relative paths and rerun the analysis from the bundled analysis-ready inputs. Generated portable outputs are written under `results/portable_*` and are intentionally not version-controlled.

The inferential anchor of the study is the two-way-clustered linear probability model. The penalized nonlinear/logistic and multinomial stage is a functional-form diagnostic. Its qualitative conclusions reproduce across tested environments, but exact floating-point point estimates are computational-environment sensitive. The archived values in `packages/08_nonlinear_multinomial_robustness.zip` remain the frozen reported results. See `documentation/NONLINEAR_REPRODUCIBILITY_NOTE.md`.

## Reproduction order

1. Analysis-ready panel.
2. First-pass models.
3. TV-definition audit.
4. Identification/falsification checks.
5. Cadence-harmonized rebuild.
6. Taxonomy scoring/reproducibility check.
7. Nonlinear and multinomial checks.
8. Predeclared heterogeneity and category decomposition.

The milestone ZIPs contain the corresponding executed scripts and outputs.

## Scope warning

This is an **analysis reproducibility freeze**, not a complete raw-source mirror. The multi-season raw NBA injury-report PDFs and all raw live-data JSON should remain archived separately. See `documentation/RAW_DATA_AND_REPRODUCIBILITY_SCOPE.md`.
