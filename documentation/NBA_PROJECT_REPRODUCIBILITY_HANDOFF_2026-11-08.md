# NBA Load Management / Player Participation Policy Project
## Comprehensive reproducibility, GitHub, source-data and execution handoff
**As of:** 2026-11-08 (Europe/Istanbul)  
**Document purpose:** A self-contained project handoff describing what the NBA research studies, what artifacts exist, what has been demonstrably reproduced, what was implemented on GitHub, what local archives to inspect, and the exact outstanding work.  
**Status:** Frozen-data → historical Stage-6 regressions independently reproduced; original historical intermediate → cadence panel reconstruction NOT yet run successfully; original raw NBA PDF/boxscore → full analysis dataset NOT yet reproduced.


> **NOV 9 CORRECTED AUGUST RUNS AND COMPLETION REPORT:** The corrected August risk panel was rebuilt from source and matches `5a5d286b…`. Corrected heterogeneity, placebo/pretrend, category FDR, preferred models, the executed stage 02/04/05 scripts and the nonlinear stage were all run after frozen gates passed. A six-season chronology audit and a release-PDF TV check were also run. See [the completion report](REPRODUCIBILITY_COMPLETION_REPORT_2026-11-09.md), [August results](AUGUST_CORRECTED_REPLAYS_2026-11-09.md) and [manuscript reconciliation](MANUSCRIPT_RECONCILIATION_CORRECTED_CHRONOLOGY_2026-11-09.md). Treat the "not yet run" statements below as historical.

> **NOV 9 INDEPENDENT AUGUST STAGE-05 REPLAY:** The original prior-event falsification script now independently reproduces all 10 season-specific event-study contrasts, 2 joint pretrend tests and 4 fake-policy-date placebo estimates from the actual Stage-05 historical archive. [CI 42566394732](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42566394732) passes coefficient precision at ~1.8e-14 pp, standard errors ~1.0e-5 pp, all archive samples and keys exact. [Full scientific runbook](AUGUST_EVENT_PLACEBO_ORIGINAL_REPLAY_2026-11-09.md), [script](../scripts/data_rebuild/run_august_prior_event_placebos_from_release.py). **Corrected event-study and placebo estimates not independently rerun in this session**, pending the verified separate original source-derived August corrected risk panel. The original paper and archived data were not changed; PR #4 stays draft.


> **NOV 9 AUGUST PREDECLARED HETEROGENEITY:** All eight original four-way heterogeneity estimates from unchanged released source passed public original-frozen GitHub Actions [42565348218](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42565348218): four predefined comparisons (back-to-back, weak opponent, high workload, near 65) × two TV definitions, original samples and BH FDR families exactly preserved; coefficients agree within 2.75e-14 pp and maximum BH q deviation 2.55e-6. No interaction heterogeneity survives original q<0.05. Age/career was explicitly not estimated in original study. [Original-script replay and corrected sensitivity pathway](AUGUST_PREDECLARED_HETEROGENEITY_REPLAY_2026-11-09.md) now committed. Corrected August subgroup **numbers not yet produced** in this session because the private verified 180,831-risk-row input is not available; code fails closed on wrong decoded SHA and fixes two obsolete announcement TV source date keys only on a copy. Subsequent original nonlinear/pretrend/placebo, awarded-star/Cup source repairs, and manuscript Level C remain unfinished. Original frozen outputs remain unchanged; PR #4 is draft.


> **NOV 8–9 AUGUST CATEGORY CONTINUATION:** Source-corrected August latest-pre-tip data were used to refit all eight four-category onset regressions with original BH/Holm multiple testing (two TV families). Legacy explicit-rest coefficient +0.6178→+0.6151 pp, BH q .05046→.05097; harmonized explicit-rest +0.7026→+0.6999 pp, q .01824→.01840. No multiplicity-adjusted interpretation flips. The exact unchanged original August FDR release executable was independently rerun in [GitHub Actions 42525522273](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42525522273), passing eight frozen anchors. **New source mismatch:** the frozen advance-TV source table itself has February 2022 Toronto game date keys inverted. Joining the corrected panel by those old keys leaves 46 player-game rows without TV; copy the TV source and amend only the two source date/UTC-tip keys, preserving the original announced networks and original schedule lines. All 180,831 corrected risk rows then match. [Full report](AUGUST_CATEGORY_FDR_CORRECTED_CHRONOLOGY_2026-11-08.md). Frozen historical files and paper unchanged; this does not close all-original-source award/Cup/game-ID or six-season Level C.

> **LATEST ADDITIONAL MANUSCRIPT/PROVENANCE CHECKS — Nov 8:** The missing original October raw TV triple, prevalence/onset rate tables, censor-safe duration statistics, one-game home/road rates, and paired home one-game-minus-longer contrast have been independently rebuilt against the original and corrected cadence panels. Raw national-TV DDD +1.91991 → +1.96652 pp; paired home difference +1.66405 (p=.1536) → +1.63781 (p=.1602). All original reported frozen cells reproduce; see [October missing statistics](OCTOBER_MISSING_PAPER_STATISTICS_2026-11-08.md). A separate [August source archive audit](AUGUST_TORONTO_SOURCE_REPORT_JOIN_AUDIT_2026-11-08.md) confirms an original season-wide matchup override misattached **17 source report rows** from October 2021/April 2022 to the February Raptors games. Fix exact source match numbers, then rerun original August panel plus taxonomy rather than patching only final labels. PR #4 still draft; neither original frozen panel modified.

> **Verified frozen October rerun:** [CI run 42516634023](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42516634023) independently executed ten original October scripts and reproduced 33 of 33 released executable result tables, maximum difference 1.15e-13. The user-supplied corrected-chronology pass is not independently rerun in that public CI; see the provenance distinction in [October audit](OCTOBER_CORRECTED_CHRONOLOGY_RESULTS_2026-11-08.md).


> **November 8 October paper-level continuation:** The ten executable October release scripts were run twice by the supplied coding session. Reported frozen results reproduce all 33 archived executable tables (maximum floating difference 1.2e-13); the corrected-chronology variant produces 704 coefficient rows, with national-partner DDD +2.63045→+2.67423 pp, linear-only +1.23897→+1.28237 pp, and home one-game +1.40600→+1.37799 pp. Some event-window sample counts shrink by 9, 23 or 32; main model samples remain the same. The integrated GitHub runner includes an independently executable public frozen-only 33-table CI gate. In the original August panel, **34 mis-linked report rows** were independently verified, matching the supplied evidence exactly. See [October corrected paper-level audit](OCTOBER_CORRECTED_CHRONOLOGY_RESULTS_2026-11-08.md). The frozen paper has not been rewritten and remaining descriptive/paired/duration tables, August source rebuild, and full Level C are unfinished. Treat earlier statements that October analyses have not been run as historical.


> **Nov 8 corrected-chronology continuation:** An independent full Stage-6 *sensitivity* now corrects the two 2021–22 Raptors fixture dates **and** their report selection and player histories, not merely the game control columns. It reproduces the submitted patch's 20 report-designation changes, 10 onset-risk changes, two fewer onset events (Kyle Lowry, Khem Birch), and four revised Stage-6 coefficients. Legacy national-partner full controls +2.63045→+2.67423 pp; harmonized linear-only +1.23897→+1.28237 pp, sample sizes unchanged. Code and detailed evidence in [date swap audit](LEVEL_C_FULL_BOXSCORE_VERIFICATION_AND_DATE_SWAP_AUDIT_2026-11-08.md). **Important:** Historical frozen game IDs still encode their former incorrect dates, and this is NOT a full corrected six-season raw-source or August-model reconstruction. The older worklist below describes an earlier status.

> **LATEST November 8, 2026 Level-C update:** Reported full original JSON → archived V2 → base-panel reconstruction has now passed with all 7,230 unique IDs, 248,571 roster rows, zero archived/derived differences, and a [published SHA-256 manifest](../validation/level_c_boxscore_2026-11-08/boxscore_json_sha256_manifest.csv). This was executed in a separate Mac/cloud environment; this session independently checked all manifest game IDs against the archived V2 crosswalk but did **not** independently rehash all raw JSON files. Critically, two 2021–22 Raptors fixture dates are reversed. The pandas-3 historical matcher reported their actual 48-hour gap as 2.88 minutes. Independent replay of the archived game covariate code with corrected dates changes rest, back-to-back, travel, and sequential Elo variables. Read [scientific review](LEVEL_C_FULL_BOXSCORE_VERIFICATION_AND_DATE_SWAP_AUDIT_2026-11-08.md). **The full paper-level Level C remains incomplete.** A conditional frozen-outcome control-only Stage-6 refit has now run: legacy +2.63045 to +2.63318 pp, harmonized linear +1.23897 to +1.24167 pp. This is NOT a full corrected-chronology outcome/report-source reconstruction; see the detailed Level-C date audit. Earlier handoff sections reflect prior status and should be read as history.

> **CRITICAL NOVEMBER 8, 2026 STATUS UPDATE:** Independent original-input **Level-B** reconstruction has now succeeded: the original corrected 2024–25 ZIP was recovered, the reconstructed panel is byte-identical to the archived panel after gzip decompression, and all four archived Stage-6 regressions match to rounding error. Full December 2025 exact-clock re-selection/reparse/rebuild/model sensitivity has also been independently executed: 21 affected games, 733 changed timing/designation rows, zero onset/risk/outcome changes. See [independent validation](LEVEL_B_REPLAY_RESULTS_2026-11-08.md). **Level C**, starting with *all* raw NBA JSON and PDF sources, remains open; the newly integrated PR #4 production CLI still needs a fresh full private-archive acceptance run. The older handoff text below preserves the earlier historical state and should not supersede this update.

> **Accuracy rule:** A successful unit test, source-metadata join, file checksum, frozen-panel self-comparison, or model rerun on frozen inputs must never be described as complete raw-data reconstruction. Preserve the archived research results unchanged, report any differences, and distinguish observed source evidence from assumptions.

---

## 1. GitHub links and current branches

| Purpose | Exact URL / reference | Status as checked on 2026-11-08 |
| --- | --- | --- |
| **Primary working repository** | https://github.com/ahmetcopur/nba-load-management-ppp | Main project, public, frozen research results and reconstruction code |
| **Shared research/provenance repository** | https://github.com/OEKundakcioglu/nba-ppp-star-availability | Contains historical source inventory and October 2026 reproduction guides |
| **Current hardening PR** | https://github.com/ahmetcopur/nba-load-management-ppp/pull/4 | **Open draft; NOT merged** |
| **Current work branch** | audit-rebuild-reliability-2026-11 | Head when checked: bdac116616fd1d789acbd31a19c4c314ae1dcf7c; the new handoff commit will advance this SHA |
| **Default branch** | main | Contains the prior PR #1 and PR #2 work; checked SHA fb67ba6f41fdfb64f5d06c63583577ce569f3027 |
| **Initial data-rebuild PR** | https://github.com/ahmetcopur/nba-load-management-ppp/pull/1 | Previously merged |
| **Archive restoration PR** | https://github.com/ahmetcopur/nba-load-management-ppp/pull/2 | Merged on Nov 8, 2026; original limitations later discovered |
| **Latest fully successful CI on PR #4 before this handoff** | https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42493012027 | Passed 24 synthetic tests, panel invariants, real source-metadata join, archive member checks and real regression rerun |
| **First successful independent Stage-6 model replay** | https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42491869499 | All 4 historical coefficient rows matched archived output within declared tolerance |
| **Pinned shared source-inventory commit** | https://github.com/OEKundakcioglu/nba-ppp-star-availability/tree/0bd713d97e8d519df5700ef473da34aba4495223 | Do not silently substitute the moving main branch |

The PR #4 documentation and scripts can be read at:
https://github.com/ahmetcopur/nba-load-management-ppp/tree/audit-rebuild-reliability-2026-11/scripts/data_rebuild

Key current documentation:
- https://github.com/ahmetcopur/nba-load-management-ppp/blob/audit-rebuild-reliability-2026-11/documentation/HISTORICAL_ARCHIVES_REPLAY_2026-11.md
- https://github.com/ahmetcopur/nba-load-management-ppp/blob/main/documentation/DATA_REBUILD_PROVENANCE.md
- https://github.com/ahmetcopur/nba-load-management-ppp/blob/main/documentation/FROZEN_SPECIFICATION.md
- https://github.com/ahmetcopur/nba-load-management-ppp/blob/main/documentation/RAW_DATA_AND_REPRODUCIBILITY_SCOPE.md
- https://github.com/OEKundakcioglu/nba-ppp-star-availability/blob/0bd713d97e8d519df5700ef473da34aba4495223/provenance/historical_sources/README.md
- https://github.com/OEKundakcioglu/nba-ppp-star-availability/blob/0bd713d97e8d519df5700ef473da34aba4495223/documentation/OCTOBER_2026_REPRODUCIBILITY.md

**Important:** PR #4 is intentionally a draft. Passing GitHub Actions is NOT permission to merge it as an archive-to-panel reproduction without executing the recovered private ZIP inputs.

---

## 2. Scientific project: what are we trying to study?

**Project:** NBA disguised load management after the NBA Player Participation Policy (PPP), evaluating star-player absence onset and advance-announced national television exposure across **six regular seasons, 2020–21 through 2025–26**.

The main question is whether star players' new absences changed after the PPP era and whether that relationship differs for games announced for national TV. The main interaction is **Star × PostPPP × AnnouncedTV**. PostPPP is 1 beginning with the **2023–24** season.

**Frozen research definitions**
- Unit: player × team × game, not a player-season summary.
- Star at opening night: All-Star or All-NBA in the previous three seasons; a current-season new All-Star becomes a star following that season's All-Star Game.
- Outcome: first eligible game of a new absence spell (**onset**), not total absence prevalence. Ongoing absences are excluded from the onset risk set.
- Main model: linear probability model, player fixed effects, team-season fixed effects, full pregame controls, standard errors clustered two ways by player and game.
- Controls: home, back-to-back, three games in four days, four in six, travel since previous game, absolute timezone shift, road-trip game number, signed pregame Elo advantage, weak opponent, opponent back-to-back, rest advantage, travel disadvantage, NBA Cup, minutes in prior 10 roster games, games already played, distance from 65 games.
- Report timing: distinguish latest usable pre-tip report versus harmonized common Eastern Time checkpoints (1:30/5:30/8:30 ET); these can change observed labels, sample and onset risk set.
- TV: distinguish advance-announced national-partner games (includes 2025–26 streaming-only partner games in the October manuscript) from the linear-only sensitivity. **Do not conflate the historical 'legacy' variable label with the current paper's causal interpretation or call linear-only exposure the headline specification.**

**Interpretation caveat:** The PPP, 65-game award threshold and In-Season Tournament occurred together. The evidence is observational; even an identical reproduced coefficient cannot isolate the PPP's independent causal effect.

**The historical August 12 freeze and the October 25 paper/revisions differ.** The August latest-pre-tip models and taxonomy outputs cannot be relabeled as October cadence-harmonized results.

---

## 3. Exact existing sample counts and selected model results

### October cadence-harmonized analysis counts

| Measure | Frozen value |
| --- | ---: |
| Regular seasons | 6 |
| Unique scheduled games | 7,230 |
| Player-team-game rows | 248,778 |
| At-risk player-team-game rows | 180,664 |
| New absence onsets | 12,731 |
| Full-control complete-case regression observations | 180,530 |
| Selected 2025–26 game records used by the 2025 report parser | 1,230 |

Be careful: **180,530** is the *full-control model complete-case count*, not the 180,664 underlying onset risk observations.

### Independently recalculated Stage-6 historical model results

The original Stage-6 regression script was rerun on the already-frozen cadence panel using pinned Python requirements in an isolated GitHub Actions job. Its output was compared with the archived Stage-6 coefficient CSV; **all four specifications matched**, with no deviations beyond the predefined **0.001 percentage-point** coefficient/SE/CI tolerance and **0.001 absolute** p-value tolerance.

| Archived Stage-6 definition | Controls | N | Triple-interaction estimate (pp) | 95% CI (pp) | p |
| --- | --- | ---: | ---: | --- | ---: |
| legacy_primary | full | 180,530 | +2.63044859 | +0.04574938 to +5.21514780 | 0.04607647 |
| legacy_primary | none | 180,664 | +2.63276878 | +0.03437995 to +5.23115761 | 0.04704073 |
| harmonized_linear | full | 180,530 | +1.23897037 | −1.34567798 to +3.82361871 | 0.34745329 |
| harmonized_linear | none | 180,664 | +1.25111261 | −1.34935998 to +3.85158519 | 0.34569368 |

Source: https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42491869499

The two full-control numbers correspond numerically to the October paper's headline TV/sensitivity contrast: about +2.63 pp (95% CI 0.05–5.22) versus +1.24 pp (−1.35–3.82). Still preserve which *executed code, model sample, report timing and TV variable* produced each table.

**Verified claim:** Recalculating Stage-6 regressions conditional on the *published frozen panel* works.  
**Not verified:** Reproducing the frozen panel from the private historical inputs, or the original upstream raw NBA archive.

Do not mix these counts with the distinct August taxonomy/analysis-ready QA summary (e.g. 248,730 full rows / 180,829 model-risk rows in that earlier package). The two datasets answer different, historically frozen stages.

---

## 4. Source provenance and what is actually archived

### Injury reports
A separate historical audit inventory in the shared repository records:
- **37,342 URL candidates checked**; these are *not* 37,342 acquired PDFs.
- **27,755 saved official NBA injury-report PDFs** in **seven physical ZIP archives**; their source audit calculated member SHA-256 digests and matched original manifests.
- **7,230 primary-sample games** mapped to exact selected reports; **2,054 unique saved PDFs** selected under the primary/latest-pre-tip sample.
- These **2,054 primary selected PDFs must not be assumed identical to the harmonized common-checkpoint selections** used in the Stage-6 cadence build.
- 2020–21 saved archive contains **617 successful PDFs**, not the 5,088 candidate URL checks sometimes described as verified by an old README.
- 2025–26 includes 1,497 hourly-filename PDFs plus 3,526 targeted quarter-hour PDFs: **5,023 saved PDFs**, not a complete all-day mirror.
- **21 selected game records involving eight PDFs on December 19–21, 2025** have PDF header timestamps 15 minutes later than filename/manifest times. All are still pre-tip by printed header time, but exact common-checkpoint eligibility must be independently recalculated before claiming a corrected-clock build.
- Original access/download timestamps are missing. HTTP Last-Modified and ZIP timestamps cannot be substituted for download timestamps.

Inventory paths in the shared repository's provenance/historical_sources:
- NBA_Source_Inventory.csv
- injury_report_inventory.csv.gz
- injury_archive_summary.csv
- primary_sample_report_map.csv.gz
- archived_game_report_links.csv.gz
- boxscore_source_map.csv.gz
- selected_report_timestamp_exceptions.csv
- ORIGINAL_SOURCE_MEMBER_SHA256.json
- verify_source_and_coding.py

### NBA boxscore cache
The source map includes **7,230 official NBA game IDs** and expected cache paths, along with candidate API endpoints. **The original raw JSON payloads have not been verified/recovered as a complete 7,230-file cache.** A boxscore output ZIP is *not automatically proof* that the underlying per-game raw JSON files survive. No per-JSON original byte hashes were preserved for an independent identity check. The exact provider endpoint used per game is also not proven from the candidate templates.

### Schedules, broadcast TV, awards and covariates
The historical inventory references six original FixtureDownload-format source CSVs (nba-2020-UTC.csv through nba-2025-UTC.csv), five official 2021–26 NBA schedule PDFs, and six 2020–21 archived broadcaster announcement HTML pages. Source attribution and coverage limitations remain. Verify source bytes, archived code, publication date, transformations, season corrections, streaming-only inclusion, NBA Cup flags, player-award histories, venues/time zones and Elo logic before calling them fully raw-reconstructed.

---

## 5. The three separate reproduction milestones

| Level | Objective | Actual status |
| --- | --- | --- |
| **A. Frozen panel → historical regressions** | Rerun the original Stage-6 models from the repository's already-published cadence CSV and match all four archived coefficient rows | **VERIFIED** on GitHub Actions |
| **B. Archived intermediate ZIPs + selected 2025–26 PDFs → cadence panel → historical models** | Restore the canonical panel, selector/status maps, five seasons' already-parsed reports; reparse selected 2025 PDFs; recompute Stage-6 panel and models; compare all rows/results | **CODE PREPARED / CI TESTED, BUT NOT YET EXECUTED ON THE ORIGINAL 13 PRIVATE ZIPs** |
| **C. Original six-season raw injury PDFs + NBA live boxscore JSON + original schedule/award/TV sources → all intermediate panels → all frozen outputs** | Independently reproduce ingestion, resolution, timing selection, taxonomy, covariates, complete-case samples and paper tables end to end | **NOT YET DONE**; raw boxscore cache and other upstream execution artifacts still need inspection/recovery |

A completed Level B cannot honestly be advertised as Level C.

---

## 6. Work completed so far (chronology)

### Initial archive/reproducibility scaffolding (PR #1, merged)
Added source audit, source-lineage join, historical builder runner, keyed panel comparator, and a scope/limitations guide. This was initially described too optimistically: it had not yet executed against the complete original archives.

### Recovery / 13-ZIP replay scaffolding (PR #2, merged)
Identified and brought copies of the historical archive filenames from the user's ChatGPT file library into a temporary working area during prior attempts. Added source-to-directory restoration, a 2025 PDF parser wrapper, and one-command orchestration. Added GitHub Actions plus tests. PR #2 was merged on November 8, but it had **unverified ZIP internal member paths** and other reliability problems. The earlier runtime/container failed before the full historical ZIP run could be validated.

### Audit and correction branch (PR #4, OPEN DRAFT)
Corrections committed and passing CI:
1. Read the actual ZIP member listings; select exact, unique basenames and reject missing or ambiguous matches before copying.
2. Check all six canonical snapshot selector maps and four specific canonical team-status maps; two other season status tables come from S4 outputs.
3. Reject conflicting player-ID alias tables rather than picking a different mapping silently.
4. Avoid writable hardlinks into original PDF ZIPs. Copy source ZIPs and SHA-256 check member copies.
5. Record full archive SHA-256s, copied member hashes, original executed source SHA, Python and package versions.
6. Make **--check-only** genuinely read-only and propagate the chosen model output directory.
7. Verify selected 2025–26 PDF basenames exist in the recovered archives and reject conflicting copies of the same basename.
8. Correct the scientific provenance join: verify harmonized selected PDFs against the *full* injury-report inventory, **not** the different primary latest-pre-tip selection map. Require archived computed hashes to agree with original manifest hashes where inventory evidence is available.
9. Check the original 2025–26 parser's per-file log. Its worker catches individual PDF errors without necessarily failing the process, so an exit code of zero is insufficient. Check every unique (basename, snapshot timestamp), parse status, zero-row exception and total extracted rows; fail closed.
10. Validate the frozen cadence panel's six-season coverage, unique IDs, total rows, unique games, risk-set size, number of onsets, and that an onset implies both at-risk and currently absent.
11. Add Stage-6 coefficient comparison against four reference model specifications; do not overwrite the original coefficients.
12. Install pinned analysis versions from requirements-lock.txt in CI, and pin the public shared source inventory by immutable Git SHA.
13. Add an **independent real computation**, running the historical run_cadence_models_fast.py on the frozen panel and comparing all four result rows; this succeeded.
14. Add regression tests for nested ZIP paths, ambiguous/missing members, hash tampering, conflicting alias tables, missing PDFs, conflicting PDF copies, full-inventory checks, silently caught parse errors, zero-row outcomes, duplicate IDs, impossible onset logic, coefficient drift and missing specifications.
15. Preserve all original frozen data, analysis scripts, archived estimates and manuscript results. The new scripts write output into Git-ignored data_rebuild/output/.

**Latest verified PR #4 result when this handoff was written:** CI run #42493012027 passed **24 automated tests**, frozen-panel invariants, the 7,230-game source-lineage join, checks of real published archive members and the independent four-model Stage-6 replay. **These are not a successful run of the 13 private input archives.**

---

## 7. What code currently exists, and what each script does

| Repository path (under scripts/data_rebuild/) | Function / limitations |
| --- | --- |
| audit_raw_inputs.py | Verify inventory-listed PDF objects and, if supplied separately, cached boxscore JSON format/game IDs. Does not rebuild canonical panel. |
| build_source_lineage.py | Join 7,230 primary selected game-report references with NBA boxscore IDs. It indexes source lineage; it does not parse PDFs or reconstruct player rows. |
| restore_historical_layout.py | Preflight/read the 13 ZIP archives, restore expected intermediate files, preserve archive/member hashes; stops on ambiguous paths. Internal ZIP members not yet independently inspected in the recovered originals. |
| reparse_2025_selected.py | Audit source PDFs and invoke the original 2025 selected-PDF parser; reconcile source selection and per-file parser log; originally historical parser depends on Linux multiprocessing semantics. |
| run_historical_cadence_builder.py | Run an isolated temporary copy of the original Stage-6 cadence-panel builder with only hardcoded root/output paths redirected; writes panel/model outputs. |
| rebuild_from_archives.py | Orchestrates restore, 2025 parsing, Stage-6 historical build, strict CSV comparison, panel invariants and coefficient checks. **Never treat it as tested on the 13 original archives until an actual run is logged.** |
| compare_panels.py | Strict keyed/string-cell panel comparison. A formatting-only float difference might require manual interpretation; never silently normalize a mismatch into acceptance. |
| validate_cadence_panel.py | Scientific shape/count/logic checks of panel, not a source-to-panel proof. |
| compare_stage6_models.py | Compare archived four-specification historical coefficient table to newly produced model results using stated tolerances. |
| replay_stage6_from_frozen.py | **Actually run** the original Stage-6 regression script on an isolated copy of the frozen panel, compare coefficients, record environment and SHA hashes. GitHub verified this. |

Other important repository files:
- scripts/executed/06_cadence_harmonized_identification/parse_2025_selected.py
- scripts/executed/06_cadence_harmonized_identification/build_harmonized_panel_and_models.py
- scripts/executed/06_cadence_harmonized_identification/run_cadence_models_fast.py
- data_intermediate/player_team_game_harmonized_cadence.csv.gz
- data_final/player_game_panel_analysis_ready.csv.gz
- data_final/qa_summary.json
- packages/01_analysis_ready_panel.zip
- packages/06_cadence_harmonized_identification.zip
- requirements-lock.txt
- tests/test_data_rebuild.py
- .github/workflows/data-rebuild-tests.yml

Also review the shared repository's scripts/october_2026/ model runners and the October manuscript results after Stage-6 replay has passed.

---

## 8. EXACT LOCAL ARCHIVE FILENAMES TO INSPECT FIRST

These filenames were **located in the user's ChatGPT file library during this conversation**, and several were materialized previously to a temporary model container directory (/mnt/data/nba_archives). They are **not confirmed to exist on the user's own Mac/PC** and they are **not automatically included in GitHub**. Confirm actual local directory, archive identity and ZIP-member listings instead of inferring them from filenames.

### Group A — 13 required inputs for the CURRENT Level-B replay command

Put *these exact filenames* in one local archive directory; see Section 10 for preflight commands.

| # | Exact ZIP filename | What to inspect / expected role |
| ---: | --- | --- |
| 1 | **nba_player_game_analysis_ready_v1.zip** | Original canonical player-game analysis-ready panel; expected member basename player_game_panel_analysis_ready.csv.gz |
| 2 | **nba_player_crosswalk_final_v1.zip** | Reviewed player-name/ID crosswalk; expected player_crosswalk_final.csv; check for optional player_alias_table.csv |
| 3 | **nba_player_game_at_risk_core_v1.zip** | Earlier parser and roster-building scripts; expected parser_2023plus.py |
| 4 | **nba_canonical_snapshot_selector_v1.zip** | Six game-to-snapshot selector maps and four canonical team status maps; validate each exact season-specific CSV and checkpoint selection |
| 5 | **audit_2020_21_corrected_outputs.zip** | 2020–21 parsed report rows; expected s1_snapshot_rows_corrected.csv |
| 6 | **audit_2021_22_cadence_outputs.zip** | 2021–22 parsed report rows; expected s1_snapshot_rows_harmonized.csv |
| 7 | **audit_2022_23_pre_s4_outputs.zip** | 2022–23 parsed rows; expected s1_snapshot_rows_regular_season.csv |
| 8 | **audit_2022_23_s4_join_results.zip** | 2022–23 harmonized team-game submitted-status file |
| 9 | **audit_2023_24_pre_s4_outputs.zip** | 2023–24 parsed rows; expected s1_snapshot_rows_regular_season.csv |
| 10 | **audit_2023_24_s4_join_results.zip** | 2023–24 harmonized team-game submitted-status file |
| 11 | **audit_2024_25_pre_s4_outputs_corrected.zip** | **Corrected**, not earlier uncorrected, 2024–25 parsed rows; expected s1_snapshot_rows_regular_season_real.csv |
| 12 | **audit_2025_26_upload.zip** | Original hourly-filename official NBA injury-report PDFs; check integrity, basename collisions and timestamps |
| 13 | **audit_2025_26_targeted_upload.zip** | Targeted quarter-hour PDF archive used by harmonized 2025–26 report selection |

All 13 exact names were visible in the user's file library listing; the first-tier restoration program is written to require them. **Presence in the Library does not mean actual ZIP-internal members and file hashes have already been verified.**

### Group B — original source archives and upstream recovery packages (priority after Group A)

These were also visible in the user's Library and matter for Level C, the from-scratch pipeline:

| Exact filename | Why inspect it |
| --- | --- |
| **audit_2020_21_upload.zip** | Original 2020–21 official NBA injury-report PDFs; only 617 saved PDFs in historical audit |
| **audit_2021_22_upload.zip** | Original 2021–22 NBA PDF archive |
| **audit_2022_23_upload.zip** | Original 2022–23 NBA PDF archive |
| **audit_2023_24_upload.zip** | Original 2023–24 NBA PDF archive |
| **audit_2024_25_upload.zip** | Original 2024–25 NBA PDF archive |
| **NBA_Historical_Source_Inventory.zip** | Historical source-manifest and SHA inventory; match source archives, original URLs and 21 clock exceptions |
| **nba_boxscore_roster_frame_v1.zip** | Original boxscore/roster ingestion code; inspect API clients and raw_json path expectations |
| **nba_boxscore_roster_frame_v2_output_upload.zip** | Boxscore derived output package; determine whether it actually contains raw per-game JSON cache or only tabular output |
| **nba_boxscore_roster_frame_v2_repair.zip** | Boxscore repair logic; compare IDs, duplicate matches, endpoint templates and canonical roster mapping |
| **nba_player_game_at_risk_star_cup_v1.zip** | Star, policy, NBA Cup merge and risk-set code/outputs |
| **nba_game_covariates_v1.zip** | Elo, rest, travel, home/road, venue coordinates, time-zone covariate pipeline |
| **nba_announced_tv_six_seasons_v1.zip** | Joined six-season national TV exposures and underlying TV source records |
| **nba_announced_tv_2020_21_v2_final.zip** | Especially important because 2020–21 TV announcement coverage is incomplete |
| **nba-2025-26-share.zip** | Separate 2025–26 source-sharing archive: inspect for exact report/boxscore/selector assets before assuming its contents |
| **nba_player_crosswalk_static_v1.zip** and **nba_player_crosswalk_v1_1.zip** | Previous ID matching/crosswalk histories, useful to understand reviewed alias corrections |

The seven official injury-report physical archives described in the inventory comprise Groups A + B (2020–21 to 2024–25 upload ZIPs plus the 2025–26 hourly and targeted ZIPs). Their filenames are not interchangeable with the derived pre-S4/S4 ZIPs.

### Group C — specific audit, frozen-model and timing-exception packages (inspect to validate, NOT to substitute silently)

- **audit_2020_21_s4_join_results_rechecked.zip**
- **audit_2021_22_s4_join_results.zip**
- **audit_2024_25_s4_join_results.zip**
- **audit_2025_26_s4_join_results.zip**
- **audit_2024_25_pre_s4_outputs.zip** (older, pre-correction version — compare to corrected version)
- **nba_cadence_harmonized_identification_v1.zip** (original Stage-6 scripts/results)
- **NBA_Cadence_Harmonized_Reruns_2026-10-25.zip** (October analyses and original input packages)
- **NBA_Reruns_Results_and_Code_2026-10-25.zip** (October executed scripts and result tables)
- **NBA_Method_Audit_Reproducibility.zip** (October methodological audit)
- **nba_load_management_final_reproducibility_freeze_2026-08-12.zip** (August freeze bundle)
- **nba_december_2025_exact_clock_pdf_audit_patch.zip** (exact-clock audit patch)
- **nba_exact_clock_candidate_review.zip** (time-exception candidates)
- **nba_october_clock_sensitivity_patch.zip** (clock sensitivity)
- **nba_source_validation_provenance_patch.zip** (source validation addendum)
- **nba_october_2026_reproducibility_completion.zip** (October stage completion)
- **nba_taxonomy_validation_scored_v1.zip**, **NBA_Coding_Agreement.zip** and **NBA_Blinded_Human_Coding.zip** (classification/coder provenance)
- **audit_2025_26_upload(1).zip** (duplicate-name file in Library; determine whether it is byte-identical before preferring either)
- **nba_announced_tv_2020_21_v1.zip**, **nba_announced_tv_v1.zip**, **nba_announced_tv_v2_final.zip** (historical TV versions, not necessarily current headline inputs)

Do not equate multiple historical versions with one correct ground truth. Preserve their version labels, release dates, digests and original lineage.

---

## 9. Recommended directory structure on your computer (do not commit raw files)

~~~text
nba-project-working/
├── nba-load-management-ppp/                  # Git clone; PR #4 branch
├── nba-ppp-star-availability/                # Shared metadata, pin SHA
├── local_original_archives/                  # The 13 Group-A ZIPs and optional others
│   ├── nba_player_game_analysis_ready_v1.zip
│   ├── nba_player_crosswalk_final_v1.zip
│   ├── nba_player_game_at_risk_core_v1.zip
│   ├── nba_canonical_snapshot_selector_v1.zip
│   ├── audit_2020_21_corrected_outputs.zip
│   ├── audit_2021_22_cadence_outputs.zip
│   ├── audit_2022_23_pre_s4_outputs.zip
│   ├── audit_2022_23_s4_join_results.zip
│   ├── audit_2023_24_pre_s4_outputs.zip
│   ├── audit_2023_24_s4_join_results.zip
│   ├── audit_2024_25_pre_s4_outputs_corrected.zip
│   ├── audit_2025_26_upload.zip
│   └── audit_2025_26_targeted_upload.zip
└── source_notes/                             # Manual archive/source audit notes
~~~

The project writes regenerated data, logs and model CSVs into **nba-load-management-ppp/data_rebuild/output/**, which is ignored by Git. Keep raw PDFs, JSON, unlicensed source documents and all unpublished original archives outside Git history. Share manifests and transformation code, not a public dump of NBA source documents without verifying reuse permissions.

---

## 10. Precise runbook: commands and what each one actually tests

**Use Linux** or a suitable Linux container/VM for the original 2025 PDF parser. The historical script uses ProcessPoolExecutor without a multiprocessing main guard; a default macOS spawn context can fail. Python **3.12** and requirements-lock.txt were verified for model analysis. PDF-specific modules/dependencies may need additional original-environment inspection.

First clone and select branches:

~~~bash
git clone https://github.com/ahmetcopur/nba-load-management-ppp.git
git clone https://github.com/OEKundakcioglu/nba-ppp-star-availability.git
cd nba-load-management-ppp
git fetch origin
git switch audit-rebuild-reliability-2026-11
cd ../nba-ppp-star-availability
git checkout --detach 0bd713d97e8d519df5700ef473da34aba4495223
cd ../nba-load-management-ppp
python3 -m pip install -r requirements-lock.txt
~~~

Next choose the **actual absolute path to the Group-A ZIP directory** and run a read-only archive preflight:

~~~bash
python3 scripts/data_rebuild/rebuild_from_archives.py \
  --archive-dir ../local_original_archives \
  --historical-root data_rebuild/output/nba_continue \
  --check-only
~~~

This checks whether all 13 named ZIPs exist, locates exact required member basenames, and detects duplicate/ambiguous candidate matches. **Passing means the ZIP layout is plausible, not that the historical data are correct.** If it fails, inspect the reported ZIP member names and historical code; do not rename or swap outputs without understanding why.

A simple manual ZIP listing on your own computer (example):

~~~bash
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile
base = Path("../local_original_archives")
for zippath in sorted(base.glob("*.zip")):
    with ZipFile(zippath) as z:
        files = [i for i in z.infolist() if not i.is_dir()]
        print(f"\n{zippath.name}: {len(files)} members")
        for member in files[:20]:
            print(" ", member.filename, member.file_size)
PY
~~~

Run existing source-metadata verification, then historical source lineage:

~~~bash
python3 ../nba-ppp-star-availability/provenance/historical_sources/verify_source_and_coding.py
python3 scripts/data_rebuild/build_source_lineage.py \
  --source ../nba-ppp-star-availability/provenance/historical_sources
~~~

These steps validate published metadata, **not actual raw NBA JSON payloads**.

Run the historical intermediate-to-panel replay only after checking the parser's dependencies and original archive bytes:

~~~bash
python3 scripts/data_rebuild/rebuild_from_archives.py \
  --archive-dir ../local_original_archives \
  --historical-root data_rebuild/output/nba_continue \
  --metadata-dir ../nba-ppp-star-availability/provenance/historical_sources
~~~

Expected outputs to inspect under data_rebuild/output/:
- nba_continue/restore_provenance.json — source ZIP and extracted-member SHA-256s;
- nba_continue/cadence_work/season_parsed/2025-26/s1_parse_log_harmonized_selected.csv — check all per-document parse statuses;
- nba_continue/cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv;
- nba_continue/cadence_work/season_parsed/2025-26/selected_pdf_sha256_audit.json;
- historical_cadence/harmonized_game_snapshot_map.csv;
- historical_cadence/harmonized_team_game_report_status.csv;
- historical_cadence/harmonized_unmatched_report_players.csv — expected to be empty if identity resolution succeeds;
- historical_cadence/player_team_game_harmonized_cadence.csv.gz — newly generated panel;
- historical_cadence/cadence_panel_counts_by_season.csv;
- historical_cadence/cadence_harmonized_model_results.csv;
- historical_cadence/panel_comparison.json;
- historical_cadence/panel_invariants.json;
- historical_cadence/stage6_model_comparison.json;
- historical_cadence/replay_environment.json.

The builder's source file also produces additional QA outputs; preserve and review all of them. A failed parser, missing identity, unexpected row count or mismatch is an **investigation trigger**. Never patch produced results to force them to the reference numbers.

Finally, rerun the proven model-only diagnostic independently from the frozen panel if desired:

~~~bash
python3 scripts/data_rebuild/replay_stage6_from_frozen.py
~~~

Outputs: data_rebuild/output/stage6_replay/cadence_harmonized_model_results.csv and replay_verification.json. This **already passed** in GitHub CI.

---

## 11. Known engineering/scientific failure modes to inspect before accepting Level B

1. **Archive member layout not yet tested against the 13 private ZIPs.** The new exact-basename discovery is defensive but might reject legitimate nested duplicates/alternate versions. Inspect actual members and manually resolve true provenance. Do not bypass checks to obtain green tests.
2. **2025 parser may need extra PDF dependencies**, or Linux multiprocessing support; the pinned statistical lockfile alone cannot certify its execution environment.
3. **Per-file parser errors may be swallowed by the historical worker.** The new log reconciliation explicitly detects this; zero parsed rows need manual justification, not blanket acceptance.
4. **Harmonized common-checkpoint selections and primary latest-pre-tip selections differ.** Compare selected PDFs against the full inventory using archive/member SHA-256 and verify checkpoint intent. The 2,054 primary selected PDF count is not a harmonized checkpoint count.
5. **21 timestamp exceptions / eight selected 2025 reports** need an independently documented exact-clock re-selection sensitivity. The current historical byte-for-byte replay and the corrected-clock sensitivity must be labeled separately.
6. **Player crosswalk/alias duplicates** could change report-to-roster identity, denominator and onset definitions. Reject conflicting alias tables and inspect all unmatched names.
7. **Input and output reproducibility:** ZIP hashes, source script SHA-256, environment, package versions, timezones, row keys, per-season QA, and full numerical result comparison should be saved, with run timestamps and exact command line.
8. **Strict panel comparison is intentionally conservative.** A CSV field may serialize floats differently while representing the same numeric value. Document and classify any differences, and validate scientific equivalence separately rather than automatically ignoring them.
9. **Input provenance is not independently proven solely by checksum agreement of a new copy.** Need original manifest/URL/time conventions where available.
10. **Complete 7,230 raw boxscore JSON cache not yet verified.** Derived CSVs cannot replace checking the original gameId, roster statuses, and endpoint/caching conventions.
11. **Paper alignment:** the October paper uses national-partner TV including streaming-only partner games; historical filenames/variable labels alone do not define the correct manuscript exposure. Distinguish October runs from August baseline and latest-pre-tip specifications.
12. **Data licensing and immutability:** never rewrite originals or commit raw licensed PDFs/JSON unless rights permit.

---

## 12. Remaining work: prioritized checklist and acceptance gates

### Priority 0 — protect original evidence
- [ ] Inventory every real local ZIP with filename, size, SHA-256, ZIP-member list, ZIP integrity test, and original location. Save manifest separately.
- [ ] Confirm whether any locally present original file differs from the ChatGPT Library copy; do not treat same name as same bytes.
- [ ] Preserve raw source archives read-only; use a fresh output directory for each replay attempt.

### Priority 1 — complete Level B historical replay
- [ ] Locate the 13 Group-A ZIPs on the actual execution computer or mount them to a Linux VM/container.
- [ ] Run the read-only archive member preflight. Resolve genuine member naming or missing files without changing scientific definitions.
- [ ] Inspect the archived parser's actual Python dependencies and install a pinned environment supporting PDF parsing.
- [ ] Verify all 2025 selected PDF basename+timestamp pairs, manifest SHA-256s, and archive copies; distinguish common-time from latest-pre-tip selection.
- [ ] Reparse 2025 selected PDF reports; verify no parse errors and reconcile log and row totals. Manually review zero-row PDFs.
- [ ] Run the untouched historical cadence builder through its portable wrapper.
- [ ] Verify row uniqueness, six-season coverage, 248,778 player-team-game rows, 7,230 games, 180,664 risk rows, 12,731 onsets, and correct risk/onset logic.
- [ ] Compare **every key and value** to the frozen cadence panel; log any drift. Preserve exceptions as evidence rather than quietly normalizing.
- [ ] Rerun and compare the four historical Stage-6 regressions; save coefficient comparison and environment provenance.
- [ ] Once evidence exists, update PR #4 with actual private-archive replay output summaries and reviewer-readable logs; only then consider merging.

### Priority 2 — original raw input reconstruction (Level C)
- [ ] Inspect all seven original official injury-PDF ZIP archives, reconcile 27,755 saved source objects and known candidate URL failures.
- [ ] Recover the **7,230 original raw per-game official NBA boxscore JSONs**, if still available in backups; find relative raw_json paths, inspect whether boxscore ZIPs contain them, hash them, and validate game IDs and source endpoint candidates.
- [ ] Recover/re-run 2020–21 through 2024–25 PDF parsing and snapshot-selection transformations, including submitted/no-listed-player handling.
- [ ] Rebuild canonical roster denominator, player ID crosswalk and team-game joins from original boxscore/source inputs.
- [ ] Rebuild six-season fixture and national-TV schedule tables from archived sources, including publication timing, six fixture CSVs, streaming-only national partner coverage and NBA Cup flags.
- [ ] Recreate dynamic stars, Elo/rest/travel/venue covariates, and risk-set/absence onset from source tables.
- [ ] Reconstruct taxonomy and separate October identification/robustness/model tables as appropriate, with explicit version and sample provenance.
- [ ] Run a **separate** exact-clock timing sensitivity for the 21 exceptions. Do not overwrite the unchanged historical selector without marking a scientifically new variant.

### Priority 3 — presentation and publication quality
- [ ] Produce a complete source → transform → dataset → model dependency graph, automatically checked row counts and a reproducible make/CLI entrypoint.
- [ ] Provide a controlled data-access or source-acquisition plan for licensed PDFs/JSON that cannot be republished.
- [ ] Publish checksums, environment information, commands, acceptance reports, research limitations, and an explicit unable-to-reconstruct report for irretrievable sources.
- [ ] Preserve manuscript and report versioning, including August frozen versus October 25 estimates.
- [ ] Consider additional independent human coding validation and complete source attribution as separate scientific-quality milestones; do not convert missing source evidence into invented files.

---

## 13. What success actually looks like

**Level A — DONE:** GitHub CI reruns all four historical Stage-6 model specifications from the frozen cadence panel; coefficients and uncertainty estimates match the archived numerical references.

**Level B — NOT YET VERIFIED:** Another researcher can start with the named 13 historical ZIP archives, produce the same player-team-game cadence panel using the documented original logic and selected 2025 PDF parser, and get exactly matching rows, meaningful scientific column values and archived model estimates, with no unexplained missing or conflicting identities and a saved full provenance log.

**Level C — NOT YET VERIFIED:** Another researcher can start with original official NBA report PDFs, raw game JSON payloads, historical schedules/broadcast releases and recognition/covariate sources, generate all intermediate data and final tables by scripted transforms without relying on preassembled canonical panels, and reproduce every frozen claim under a documented environment. Where sources are irretrievable or copyrighted, that limitation must be explicitly disclosed.

**Don't claim any outcome is 'fully reproduced' without identifying which level was actually tested.**

---

## 14. Where the work stopped, and immediate next action

The original source archives were visible in the user's ChatGPT Library; earlier attempts materialized several copies under /mnt/data/nba_archives in a transient assistant container, but subsequent container/Python calls failed. That environment failure prevented direct inspection and execution of the 13 ZIPs. The current run cannot verify files physically stored on the user's own laptop. The GitHub connection could, however, create scripts, document provenance, and execute GitHub Actions on the **public frozen panel**, which provided the successful independent Stage-6 model result.

**Next action for a new work session or local operator:** Start with the 13 exact Group-A ZIP files, perform the read-only member preflight on Linux, check all source hashes and the historical PDF parser dependencies, execute the Level-B replay, and save actual comparison logs. Do not merge PR #4 or present this as full raw source reproduction until that evidence is obtained. After Level B, move systematically upstream to the original boxscore cache and six-season raw report pipeline.

**Tracking links:**  
Primary repo: https://github.com/ahmetcopur/nba-load-management-ppp  
Current draft PR: https://github.com/ahmetcopur/nba-load-management-ppp/pull/4  
Shared source lineage: https://github.com/OEKundakcioglu/nba-ppp-star-availability  
Verified independent regression run: https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42491869499

*End of handoff. This document is intended to be updated with actual historical archive run manifests and comparison reports once they exist; it should not itself be treated as evidence that those runs have occurred.*
