# NBA Disguised Load Management Project — Final Analysis Freeze

Freeze date: **2026-08-12**

This package freezes the completed empirical analysis for the six-season NBA Player Participation Policy project.

## Rebuild the final corrected analysis datasets

**Start here:** [One-command final dataset reconstruction](scripts/data_rebuild/reproduce_final_datasets.py) · [private source ZIP setup, expected outputs and exact SHA-256 checks](documentation/REPRODUCE_FINAL_DATASETS.md).

From the **original private historical source archives**, regenerate the November 2026 accepted **corrected August latest-pre-tip full/at-risk panels** and the **corrected October cadence-harmonized player-game panel** with the original scientific builders. The command refuses changed frozen baselines, wrong corrected dataset hashes, incorrect risk/onset counts or Stage-6 estimates. Use a **fresh private directory outside Git**. Optional independent six-season raw injury-PDF baseline verification and the original ten-script October regressions are separately available.

This is an executable reproducibility route to the **datasets used in analysis**, not merely a repository of historical model estimates. The user-owned NBA PDFs, raw box-score data, manually adjudicated source mappings, and generated private player-game rows are not committed. Read the documentation's explicit intermediate-source versus raw-PDF lineage boundary before asserting full raw-to-corrected source acceptance.

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

### Independent first-party national-TV source audit — November 11

The project now has an **independent source-level check of the advance-announced
national-TV treatment**. We re-extracted the date, visitor, host and network
from all five original NBA preseason by-date PDF releases (2021–22 through
2025–26), verifying **6,060/6,060 complete broadcast source rows exactly**
and all 6,150 corresponding original played-game treatment classifications.
The **90 original Cup-driven TBD matchups** retain an explicitly unknown
at-release status rather than being backfilled.

For 2020–21, we independently parsed the first/second-half original
ESPN/ABC, TNT and NBA TV announcement HTML. All **219 specified original
broadcast rows** match, mapping to **156 truly matchup-announced primary-TV
games** and 61 verified first-half NBA TV games. Importantly, **542
second-half NBA TV classifications remain unknown** because the saved
original broadcaster source does not contain the complete static schedule.
Together, the verified six-season original national-TV dataset contains
**1,041 primary matchup-announced games across 7,230 fixtures**.

[Original first-party TV-source reparser](scripts/data_rebuild/verify_official_nba_tv_announcements.py) ·
[Sanitized verified original PDF/HTML audit](validation/level_c_injury_pdf_real_2026-11-10/official_NBA_advance_TV_six_season_original_PDF_HTML_source_replay_2026-11-11.json) ·
[Complete methods, commands and limitations](documentation/CONNECTED_CORE_REPRODUCTION_2026-11-10.md).

This is **source-defined treatment verification**, not proof of a
causal policy effect. Live NBA CDN bytes were not separately
re-downloaded, every postponed-game assignment has not been
independently checked against official NBA boxscore logs, and
the original incomplete 2020–21 NBA TV sensitivity limitation remains.

### November 11, 2026 — all six original PDF seasons accepted through August models

The original **2020–21 PDF reason-text discrepancy is resolved**: a fresh
complete parse of all **617 original reports** regenerated 41,780 original
15-field source rows, including all previously differing reason strings,
without borrowing the frozen reason text. Combined with the 3,020
original PDFs from 2021–22 through 2025–26, the resulting **3,637
original NBA injury reports** feed all 73,547 selected reports and
73,438 resolved player identities, **10/10 exact core, 12/12 exact
All-Star and 3/3 exact Cup outputs**.

The newly generated six-season core also passed original reviewed
taxonomy reconstruction: both **248,730 full** and **180,829
at-risk** reviewed modeling files reproduce *all* original
decoded bytes. The unchanged original August player/team-season
fixed-effects model was actually refitted on that six-original-PDF-season
input; **all 44 model coefficients and both focal rows match the
historical research**, including +3.1493 percentage points
(p=.01668) for the original headline triple interaction.

For an independent primary-source check rather than an internal
replay, the original NBA Cup game lookup was compared against
the **official NBA 2023, 2024 and 2025 tournament group draws
and schedules**: **180/180 group opponent fixtures** and all
**18 knockout stage/dates** satisfy those original NBA
releases, with each of the 30 teams playing four group opponents
(2 home, 2 away).

[Fresh six-source reviewed data acceptance](validation/level_c_injury_pdf_real_2026-11-10/six_original_pdf_seasons_to_exact_reviewed_analysis_ready_2026-11-11.json) ·
[Original August model execution](validation/level_c_injury_pdf_real_2026-11-10/six_original_pdf_seasons_to_original_august_FE_models_2026-11-11.json) ·
[Independent NBA Cup source audit](validation/level_c_injury_pdf_real_2026-11-10/official_NBA_cup_2023_2025_group_and_calendar_source_audit.json) ·
[Current full scientific runbook](documentation/CONNECTED_CORE_REPRODUCTION_2026-11-10.md).

**Scope:** The human-reviewed injury-reason and award/crosswalk
judgments, official advance TV scheduling and inherited game
covariates are not yet fully independently source-validated.
Exact per-game NBA Cup dates and broadcast providers remain
separate verification tasks. The new monolithic clean-checkout
private ZIP command and the final full manuscript
reconciliation remain open. **PR #4 stays draft and unmerged**.

## Connected private-source reconstruction (November 2026)

An additional executable pipeline now rebuilds historical player IDs, the full
player-game core and the dynamic All-Star/All-NBA star labels from the **private
original source packages**, rather than only rerunning regressions on frozen CSVs.

From the audit branch, with the five required original ZIPs staged together
**outside Git**, use this command with a new private output directory:

    python scripts/data_rebuild/reproduce_core_and_stars.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/core-and-stars"

The **original October cadence-harmonized panel** has now also been
rebuilt from source-derived data, using the 2021–25 original-PDF-based
analysis-ready core and **355 freshly parsed original 2025 harmonized
injury PDFs**, together with original historical parser and selector
inputs. The full generated **248,778-row** harmonized player-game CSV
matches the frozen October panel **byte-for-byte after decompression**.
The original separately archived Stage-6 model script then reproduced
all **four TV/control models**, including +2.63045 pp (p=.04608)
for national partners and +1.23897 pp (p=.34745) for linear TV.

Add `--with-october-cadence` alongside
`--from-original-2021-2025-pdfs --with-analysis-ready` in the combined
command to include this source-derived October construction.
The frozen all-in-one builder has a documented `norm()` name-shadowing
bug in its model section; the new runner executes its unchanged
panel-building code, then the original separate working model script.
[Real original-source October acceptance](validation/level_c_injury_pdf_real_2026-11-10/source_generated_october_cadence_panel_and_four_models.json)
and [full original-source runbook](documentation/CONNECTED_CORE_REPRODUCTION_2026-11-10.md).

The original **player/team-season fixed-effects model** has also been
rerun on the newly generated five-PDF-season analysis-ready input.
The original absence-onset triple-interaction coefficient is
**+3.1493 percentage points (p = 0.01668)**; all 44
original coefficient rows match to floating-point precision.
To reproduce this further stage, also include the original private
reviewed `nba_player_game_analysis_ready_v1.zip` and add
`--with-analysis-ready --with-original-teamseason-models`
to the five-season command below. The released model source
and reference results are already pinned inside the repository's
`packages/02_first_pass_models.zip`.

[Real source-derived model execution evidence](validation/level_c_injury_pdf_real_2026-11-10/five_raw_seasons_to_original_teamseason_fe_models.json).
This is the August latest-pre-tip original model, not the entire
October harmonized manuscript suite; the 2020–21 original PDF
reason parsing and official award/Cup/TV provenance remain open.

The latest source-to-core extension now supports **five original NBA injury-PDF
seasons (2021–22 through 2025–26)**. With the four 2021–24
original raw ZIPs added to the previous eight original inputs, use:

    python scripts/data_rebuild/reproduce_core_and_stars.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/raw2021-2025-core-stars-cup" \
      --from-original-2021-2025-pdfs --with-cup

**3,020 authentic original selected PDFs generated 64,956 complete player-report
records, all 22 fields exact.** Those five seasons' PDF-derived rows
were then consumed by the reconstructed original identity/core and
award/star builders and Cup lookup transformation; **25/25 frozen output
files reproduced exactly**. Only the 8,591 records from 2020–21
remain archived source inputs because of its unresolved reason-field
extraction differences. The newly packaged umbrella command still
requires its own fresh 12-ZIP acceptance; the corresponding original
source stages were executed and compared in the private work area.

[Five-season actual source evidence](validation/level_c_injury_pdf_real_2026-11-10/five_seasons_real_pdfs_to_25_exact_core_star_cup_outputs.json)
and [full original-PDF runbook](documentation/CONNECTED_CORE_REPRODUCTION_2026-11-10.md).

For an optional **2025–26 original NBA PDF input** (instead of
inheriting that season's selected-report rows), also include
`audit_2025_26_upload.zip` and `audit_2025_26_targeted_upload.zip`
in your private source directory, and add `--from-original-2025-pdfs`
to the command (alongside `--with-cup`). This now rebuilds all
13,968 selected 2025–26 source rows from **729 original PDFs**,
requires an exact comparison across **all 22 original fields**, and
runs the fresh records through the connected core/star/Cup stages.

The independently executed source-substitution run reproduced
**10/10 core, 12/12 star and 3/3 Cup outputs exactly**. The other
five seasons' selected rows are still archived inputs, and the
newly packaged single-command eight-ZIP variant requires its own
direct clean-checkout private-input acceptance. See the
[raw-2025 source report](validation/level_c_injury_pdf_real_2026-11-10/fresh_2025_pdfs_to_connected_core_stars_cup.json).

For the now-executed **Cup-lookup enrichment** as well, include
nba_player_game_at_risk_star_cup_v1.zip in the private directory and add
the --with-cup switch to the same command. The new Cup builder produces the
248,730-row full, 180,829-row at-risk and 13,723-spell Cup-enriched CSVs;
all three match the frozen package after decompression. **The Cup lookup itself
is inherited from the original archive**, not independently regenerated
from NBA schedule announcements.

In a separate real-input execution, the independently rebuilt player-ID table
was consumed by the original unchanged core finalizer, producing **248,730**
player-games, **180,829** at-risk rows and **12,710** absence onsets; all
**10 core outputs** matched the frozen source. The original historical
All-Star/All-NBA source-coded builder was then run on this new core and all
**12 substantive star outputs** matched their frozen references.

The single-command wrapper and standalone scripts have public CI regression
tests, but **CI cannot access the private original ZIPs**; the real-input
acceptance was run locally using the same underlying stages.

Full runbook: [Connected core-and-star reproduction](documentation/CONNECTED_CORE_REPRODUCTION_2026-11-10.md).
Source evidence: [exact connected core](validation/level_c_injury_pdf_real_2026-11-10/connected_identity_to_core_exact_2026-11-10.json)
and [exact connected star enrichment](validation/level_c_injury_pdf_real_2026-11-10/connected_core_and_star_exact_2026-11-10.json).

**Not yet raw-PDF-to-manuscript reproducibility:** the input selected-report
rows, reviewed award lists, game covariates and subsequent Cup/taxonomy/TV/model
stages remain distinct source dependencies. The frozen originals are not
modified and PR #4 remains draft.

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


## November 8, 2026 — manuscript descriptives and August source-join audit

The previously missing October cadence-paper raw TV triple difference, onset/prevalence rate cells, one-game home/road rates, censor-safe completed-spell duration table, and paired one-game-minus-longer home/road regression have now been independently rebuilt from original frozen and corrected-chronology panels. The frozen figures match the October manuscript to recorded precision; corrected raw triple is **+1.9665 pp** (frozen +1.9199 pp) and corrected paired contrast is **+1.6378 pp**, p=.1602 (frozen +1.6640 pp, p=.1536). See [reproduction code](scripts/data_rebuild/rebuild_missing_october_paper_statistics.py), [scientific write-up](documentation/OCTOBER_MISSING_PAPER_STATISTICS_2026-11-08.md) and [comparison evidence](validation/october_missing_paper_statistics_2026-11-08/paper_statistic_deltas.json).

A separate [original August source-level audit](documentation/AUGUST_TORONTO_SOURCE_REPORT_JOIN_AUDIT_2026-11-08.md) discovered **17 misassigned selected-report rows** from October 2021 and April 2022 caused by a season-wide CHI@TOR/MIA@TOR matchup override. Repair must use **source match numbers** and fix only February source games 430 and 784, then rebuild downstream latest-pre-tip/taxonomy. The **17 upstream report rows** are not the same population as the **34 downstream player-game timing anomalies**. This is a confirmed audit, not a completed August panel rebuild. PR #4 remains a draft, original frozen research files unchanged.


### November 8–9: August category-onset FDR after source correction

All **8 August category-specific models** (vague, specific, explicit rest and other absence, each under legacy-partner and harmonized linear TV) were refitted on the corrected latest-pre-tip panel. Original frozen coefficients and BH/Holm-adjusted results reproduce; [GitHub Actions 42525522273](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42525522273) independently reran the exact unchanged August category-FDR release and passed all 8 historical benchmarks. The explicit-rest corrected interaction is **+0.61513 pp, BH q=0.05097** under legacy national-partner TV, and **+0.69993 pp, q=0.01840** under harmonized TV; no adjusted-significance interpretation changes. A second source defect was found: the archived announced-TV fixture table has the two February Toronto matchup **date keys swapped**. The uncorrected date-key join loses **46 corrected at-risk rows**. Changing only two TV lookup dates/UTC tips (preserving original release networks) restores all **180,831** corrected source joins. See [full eight-model audit](documentation/AUGUST_CATEGORY_FDR_CORRECTED_CHRONOLOGY_2026-11-08.md), [numerical comparisons](validation/august_corrected_latest_pre_tip_2026-11-08/category_fdr_full_corrected_vs_frozen.csv) and [TV-source QA](validation/august_corrected_latest_pre_tip_2026-11-08/advance_tv_source_date_key_audit.json). Exact published-script correction runner: [run_august_category_fdr_from_release.py](scripts/data_rebuild/run_august_category_fdr_from_release.py). Original freezes unchanged; PR #4 stays draft.


## November 9, 2026 — independent August predeclared heterogeneity replay

The original August four-predeclared-subgroup × two-TV-definition heterogeneity executable is now reproduced independently in [GitHub Actions 42565348218](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42565348218). All eight archived four-way interaction coefficients match to approximately 2.8e-14 percentage points; the maximum clustered-SE drift is 1.44e-5 pp and the largest BH-q drift is 2.55e-6. **None** of the eight heterogeneity differences passes the predeclared within-TV-family four-test BH correction. The original release did not estimate age/career-stage heterogeneity because it lacks reliable metadata; this remains intentionally unestimated.

Reproducer: [run_august_heterogeneity_from_release.py](scripts/data_rebuild/run_august_heterogeneity_from_release.py), [scientific audit and runbook](documentation/AUGUST_PREDECLARED_HETEROGENEITY_REPLAY_2026-11-09.md), [immutable CI evidence](validation/august_corrected_latest_pre_tip_2026-11-09/heterogeneity_original_frozen_ci_reproduction.json). A corrected-sensitivity command is implemented with the independently validated two-source-row TV date rekey, but **it has NOT been executed in this session** because the separately verified private 180,831-row August corrected model-risk file is not available in the public repo or connected file search. No corrected subgroup coefficient is claimed. PR #4 remains draft; original frozen source and results unchanged.


## November 9, 2026 — original August event study and pre-policy placebos reproduced

A second **independent GitHub Actions replay** verified the original August Stage-05 falsification archive: 10 season-specific Star×TV event-study coefficients, 2 joint pretrend tests, and 4 fake-PPP start-date placebo regressions. The unchanged archived source reproduces every reference coefficient and sample-count benchmark in `packages/05_identification_falsification_stage2.zip`; largest coefficient deviation is **1.78e-14 pp** and largest clustered SE drift **1.04e-5 pp**. [CI run 42566394732](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42566394732) completed the Stage-05 original replay successfully.

Script: [run_august_prior_event_placebos_from_release.py](scripts/data_rebuild/run_august_prior_event_placebos_from_release.py); [scientific audit](documentation/AUGUST_EVENT_PLACEBO_ORIGINAL_REPLAY_2026-11-09.md); [CI provenance](validation/august_corrected_latest_pre_tip_2026-11-09/falsification_stage05_original_frozen_ci_reproduction.json). The corrected-chronology path is implemented with an independent copy of the two-date advance-TV source repair but has **not been executed** because the verified private source-corrected August risk panel is not present in the public repository or connected files. No corrected event-study/pretrend/placebo estimates are claimed. PR #4 remains draft; historical originals and manuscript unchanged.
