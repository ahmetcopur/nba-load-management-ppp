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


## November 2026 reproducibility follow-up (separate from the frozen results)

The historical Stage-6 models have now been **independently recalculated from the already-published frozen cadence panel** using the original executable and pinned Python requirements. All four archived specifications matched within the declared tolerances in [GitHub Actions run #42491869499](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42491869499).

```bash
python3 -m pip install -r requirements-lock.txt
python3 scripts/data_rebuild/replay_stage6_from_frozen.py
```

This validates **panel-to-regression reproducibility**, not the upstream creation of the canonical dataset from original NBA boxscore JSON and multi-season injury PDFs. A separate archive-to-panel replay runner is documented in [Historical archive replay](documentation/HISTORICAL_ARCHIVES_REPLAY_2026-11.md), including the needed local original ZIPs, PDF-source provenance verification, original-model comparison, and remaining unverified gaps. The archived results and August freeze remain unchanged. All historical intermediate-to-panel replay steps must be executed and checked before claiming full source-data reproducibility.

## November 8, 2026 independent Level-B milestone

Using the original corrected 2024–25 ZIP, all 13 historical intermediate inputs plus selected 2025 PDFs were independently replayed to a cadence panel that is **byte-identical after decompression** to the 248,778-row archived panel. All four Stage-6 coefficients matched the reference. The full printed-header exact-clock December 2025 sensitivity was also independently rerun with original corrected inputs; it changes 733 player-game rows, but **zero** absence/onset/risk-set values or Stage-6 models. See [Level-B verification and sensitivity details](documentation/LEVEL_B_REPLAY_RESULTS_2026-11-08.md). A separate builder dependency lock and historical fast-model runner fix are on the open PR #4 branch. This milestone is *not* all-six-season raw PDF/boxscore JSON-to-paper Level C reproducibility.


## November 2026 Level-C raw boxscore JSON verifier

An additive offline verifier for original NBA boxscore JSON cache files is available at [verify_boxscore_cache.py](scripts/data_rebuild/verify_boxscore_cache.py), with [runbook and acceptance criteria](documentation/LEVEL_C_BOXSCORE_CACHE_VERIFICATION.md). It invokes the archived historical V2 repair program with --no-download, checks each original JSON game ID/schema/download-log size, hashes raw files, and compares all four regenerated output CSVs against archived V2 tables and the canonical base panel.

**Verified:** The original archived V2 roster's 248,571 boxscore rows agree with the published canonical base-panel rows on all comparable keys and values. Automated negative tests of the new verifier pass in GitHub Actions.

**Not verified:** The original 7,230 raw NBA JSONs have not been supplied here for the complete offline run. The reported 7,185 + 45 cache split is from a separate Mac environment and has not been independently audited. The new verifier does not change the frozen research outputs or establish complete Level-C raw-data reconstruction.
\n## November 8, 2026 raw boxscore cache milestone and schedule-date integrity caveat

A separate full 7,230-file raw NBA JSON → V2 roster reconstruction was reported successful, with all 248,571 player rows matching archived V2 and the canonical base panel, and a [complete checksum manifest](validation/level_c_boxscore_2026-11-08/boxscore_json_sha256_manifest.csv). Independent review verified the manifest's exact 7,230 game-ID set against archived V2 and the original repair-script one-line difference. Original JSON bytes were not transferred to this review environment for a second full rehash/replay. See [full evidence and limits](documentation/LEVEL_C_FULL_BOXSCORE_VERIFICATION_AND_DATE_SWAP_AUDIT_2026-11-08.md).

**Do not mistake reproducibility for data correctness:** two 2021–22 Raptors fixture dates are swapped in the frozen input; the historical pandas-3 time-unit bug hides 48-hour offsets as 2.88 minutes. An independent archived-covariate replay shows changes to rest/back-to-back/travel and pregame Elo after correcting the two dates. The **conditional frozen-outcome control-only** Stage-6 refit has now also been run; the legacy primary interaction moves from +2.63045 pp to +2.63318 pp, while harmonized linear moves from +1.23897 pp to +1.24167 pp. A full corrected-source reconstruction of playing history, report selection and policy model inputs remains outstanding, as does the remaining all-source Level C work. Historical frozen outputs are unchanged.\n

## November 8, 2026: corrected game-chronology Stage-6 sensitivity

A separate [verified Stage-6 corrected-chronology sensitivity](documentation/LEVEL_C_FULL_BOXSCORE_VERIFICATION_AND_DATE_SWAP_AUDIT_2026-11-08.md) now corrects the two 2021–22 Toronto fixture dates, their selected injury reports, original game covariates, and team/player-game playing histories before rerunning the untouched historical Stage-6 builder and four fast regressions. The independent run matches the original source patch's **20 designation changes**, **10 onset-risk changes** and **two removed ongoing-absence onsets** (Kyle Lowry and Khem Birch). Total new absence onsets move from **12,731 to 12,729**. National-partner full-control interaction changes **+2.63045 → +2.67423 pp**; harmonized linear-only full-control **+1.23897 → +1.28237 pp**. The historical frozen panels and all published originals remain untouched. This is a Stage-6 sensitivity only and does not complete all raw-source Level-C paper reproduction. Code: [fixture_date_chronology_sensitivity.py](scripts/data_rebuild/fixture_date_chronology_sensitivity.py). Validation: [November 2026 evidence](validation/fixture_date_chronology_2026-11-08/fixture_date_chronology_sensitivity.json).


## November 8, 2026 — October release rerun and corrected chronology

The ten original October release scripts have been packaged into an immutable [two-panel comparison runner](scripts/data_rebuild/october_corrected_chronology.py), including a public frozen-only CI path that must independently reproduce all **33 archived executable CSV outputs**. The supplied corrected-chronology run finds national-partner DDD **+2.63045 → +2.67423 pp**, linear-only DDD **+1.23897 → +1.28237 pp**, and one-game home/road **+1.40600 → +1.37799 pp**. Some event-window N values decrease by **9–32** despite unchanged main DDD N. See [full documented comparison](documentation/OCTOBER_CORRECTED_CHRONOLOGY_RESULTS_2026-11-08.md), [24 manuscript rows](validation/october_corrected_chronology_2026-11-08/manuscript_estimates_frozen_vs_corrected.csv), and [joint tests](validation/october_corrected_chronology_2026-11-08/joint_tests_frozen_vs_corrected.csv).

An independent read of the original August panel confirmed **34** incorrectly linked report-timestamp rows from the same two February 2022 Raptors games, across no other games; the source freeze was not modified. These August inputs and remaining descriptive tables need separate work. PR #4 remains a draft. The supplied corrected October rerun is external execution evidence; do not confuse its verification status with the independent public frozen-only CI runner.


**Independently reproduced October release:** [GitHub Actions 42516634023](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42516634023) successfully reran ten original public October scripts and matched all 33 archived output CSVs (max difference 1.15e-13). The corrected October sensitivity was run externally and its source/summary audited; its full corrected pass was not independently rerun inside public CI.
