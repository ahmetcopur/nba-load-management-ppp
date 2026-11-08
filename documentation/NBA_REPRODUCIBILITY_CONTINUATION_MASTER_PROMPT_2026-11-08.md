# COPY-PASTE MASTER PROMPT — NBA LOAD MANAGEMENT DATA REPRODUCIBILITY

> **CRITICAL UPDATED CONTINUATION STATUS (Nov 8, 2026):** The complete 7,230 raw NBA boxscore JSON → archived V2 roster → base-panel replay was reported successful in the latest supplied execution patch, with a 7,230-row [checksum manifest](../validation/level_c_boxscore_2026-11-08/boxscore_json_sha256_manifest.csv). This ChatGPT session independently cross-checked all 7,230 official game IDs against archived V2 and verified the executed repair-script SHA and two schedule-date errors, but did not itself reparse all raw JSON bytes. Read [Level-C results and corrected schedule scientific risks](LEVEL_C_FULL_BOXSCORE_VERIFICATION_AND_DATE_SWAP_AUDIT_2026-11-08.md) **before following older instructions below**. Two 2021–22 fixture dates were swapped (Bulls @ Raptors and Heat @ Raptors); historical pandas-3 matching shrank their 48-hour errors to 2.88 minutes. Original archived Elo/rest/travel code was independently rerun with a separate corrected-date input; results **do change**, though no corrected player-game regression has yet been run. The immediate scientific priority is to propagate corrected dates/covariates to an isolated panel and rerun the original October specifications, while preserving historical frozen results. Full Level C remains incomplete across six-season injury, TV, awards and other upstream sources.

> **UPDATED NOVEMBER 8, 2026 — READ BEFORE FOLLOWING THIS PROMPT:** The original corrected 2024–25 ZIP has been recovered from the ChatGPT file library. An independent local replay has **already** reconstructed the frozen 248,778-row cadence panel byte-identically after decompression from the actual 13 historical ZIPs; all 4 Stage-6 coefficients reproduce. The full December 2025 printed-header exact-clock sensitivity also executed independently with the original corrected 2024 input; 21 games and 733 rows have source/timing/designation changes, **zero onset/risk/absence changes**, and the same 4 model results. See [current independently verified results](LEVEL_B_REPLAY_RESULTS_2026-11-08.md) and GitHub PR #4 CI. The immediate next engineering task is a clean-root production CLI acceptance run on those ZIPs and then Level-C raw-source reconstruction; do NOT repeat the older Level-B 'not yet executed' claim below as the current status. This prompt's older sections preserve the earlier timeline for traceability.

**Last verified:** November 8, 2026. This is an instruction prompt for a new AI research/coding session, not evidence that unfinished steps were completed.

## ROLE AND IMMEDIATE MISSION

You are taking over an existing empirical NBA Player Participation Policy (PPP) / load-management research project. Act as an exceptionally rigorous senior data engineer, statistical research programmer, reproducibility auditor and GitHub maintainer. Do not start a new research project, change estimands, silently fill missing data, or rewrite frozen results.

**Your task:** CONTINUE the existing GitHub work. Inspect actual repository code and actual ZIP-file contents, identify and correct genuinely demonstrated problems, run the historical data reconstruction if the original source archives are available, validate every stage against the original archived data and analytical specifications, commit well-tested changes to the existing PR branch, and clearly distinguish verified work from unverified steps. You should work, not merely give generic suggestions. If an environment cannot run the historical archives, develop a concrete executable preflight/validation path, run the portions that can run, and explain exactly what blocks the rest.

**Accuracy matters more than making tests green.** Do not call a reproduction successful without independently executing and comparing the correct outputs.

## CURRENT GITHUB PROJECT AND TRACKING REFERENCES

- Primary repository: **https://github.com/ahmetcopur/nba-load-management-ppp**
- Source/provenance shared repository: **https://github.com/OEKundakcioglu/nba-ppp-star-availability**
- Current working branch: **audit-rebuild-reliability-2026-11**
- Open draft PR: **https://github.com/ahmetcopur/nba-load-management-ppp/pull/4** (on Nov 8, open and unmerged; verify state again)
- Earlier PRs #1 and #2 have been merged into main. PR #2 introduced an archive-replay scaffold but contained scientifically meaningful unverified archive assumptions; PR #4 addresses them.
- Detailed handoff document (READ FIRST):
  **https://github.com/ahmetcopur/nba-load-management-ppp/blob/audit-rebuild-reliability-2026-11/documentation/NBA_PROJECT_REPRODUCIBILITY_HANDOFF_2026-11-08.md**
- Execution guide:
  **https://github.com/ahmetcopur/nba-load-management-ppp/blob/audit-rebuild-reliability-2026-11/documentation/HISTORICAL_ARCHIVES_REPLAY_2026-11.md**
- Source-lineage code / full inventory: **https://github.com/OEKundakcioglu/nba-ppp-star-availability/tree/0bd713d97e8d519df5700ef473da34aba4495223/provenance/historical_sources**
- Pinned shared source commit: `0bd713d97e8d519df5700ef473da34aba4495223`
- Successful real regression replay: **https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42491869499**
- Successful most recent full PR CI at handoff: **https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42493012027**
- Historical August freeze: **2026-08-12**; important October paper revisions: **2026-10-25**. DO NOT mix August and October definitions.

First retrieve current GitHub/PR/CI state and compare with this handoff; preserve intervening changes, never overwrite them. Read the repository README, `FROZEN_SPECIFICATION.md`, `RAW_DATA_AND_REPRODUCIBILITY_SCOPE.md`, `DATA_REBUILD_PROVENANCE.md`, `HISTORICAL_ARCHIVES_REPLAY_2026-11.md`, and the comprehensive handoff document above. If GitHub is not connected, explain which operations cannot be completed; do not claim a push.

## THE RESEARCH YOU MUST PRESERVE

Research question: Does the incidence of new star-player absence spells differ between nationally televised and other NBA games after the NBA Player Participation Policy (PPP), using 2020–21 through 2025–26 regular-season data? The core estimand is **Star × PostPPP × AnnouncedTV**. `PostPPP=1` beginning in 2023–24. Star status dynamically reflects All-Star/All-NBA in the preceding three seasons and newly selected current-season All-Stars after the All-Star Game.

Unit: **player × team × game**. Main outcome: **onset of a NEW absence spell** among eligible at-risk observations, NOT simple absence prevalence. Ongoing spell games are excluded from the onset risk set. Main inferential model: linear probability model with player and team-season fixed effects, full pregame controls, and player/game two-way clustered standard errors. Controls: home, back-to-back, 3-in-4, 4-in-6, rest, travel, timezone, road-trip number, Elo advantage, weak opponent, opponent back-to-back, travel disadvantage, NBA Cup, recent playing minutes, prior games played, and distance to 65 games.

**Critical scientific distinctions:**
1. The **October headline national-partner advance-TV measure includes 2025–26 streaming-only partner games**; harmonized **linear-only** exposure is a mandatory sensitivity. Historical "legacy"/"harmonized" names must be interpreted in the exact executable context and not blindly relabeled.
2. The **latest-pre-tip** official injury-report selector and **harmonized common-time (1:30/5:30/8:30 ET)** selector are different. Their selected PDFs need not be identical. In particular, do NOT compare a harmonized PDF selection to `primary_sample_report_map.csv.gz` as though both represented the same rule.
3. August frozen latest-pre-tip models and October cadence-harmonized models are different stages. Preserve original estimates, samples, results and taxonomies.
4. Results are **observational**; PPP, the 65-game awards rule and NBA Cup timing overlap. The model cannot independently isolate PPP causality.

**Frozen October cadence counts:** six seasons; **7,230 games**, **248,778 player-team-game rows**, **180,664 at-risk rows**, **12,731 new onset events**; **180,530 full-control complete-case observations**. The historical 2025–26 selector contains **1,230 game records**. Do not confuse 180,530 complete cases with 180,664 at-risk rows, or the different August data counts.

## VERIFIED VS. UNVERIFIED STATUS — KEEP THIS DISTINCTION

**Verified, Level A:** Original historical Stage-6 regression code was independently rerun on the *already published frozen cadence CSV* in GitHub Actions with historical pinned dependencies. All four archived Stage-6 specifications reproduced within predeclared numerical tolerance (0.001 pp for estimates/SE/CIs; 0.001 absolute for p-values):
- legacy_primary / full: n=180,530, estimate **+2.6304485902 pp**, 95% CI **+0.0457493786 to +5.2151478017**, p≈0.04607647.
- legacy_primary / none: n=180,664, estimate **+2.6327687804 pp**, CI **+0.0343799520 to +5.2311576087**, p≈0.04704073.
- harmonized_linear / full: n=180,530, estimate **+1.2389703651 pp**, CI **−1.3456779812 to +3.8236187114**, p≈0.34745329.
- harmonized_linear / none: n=180,664, estimate **+1.2511126065 pp**, CI **−1.3493599800 to +3.8515851930**, p≈0.34569368.
- The last verified GitHub Actions run passed **24 automated tests**, frozen panel scientific checks, a real 7,230-game metadata join, real public archive-member checks, and the four real regressions. These checks cannot prove the frozen panel itself was reconstructed.

**NOT verified, Level B:** Replay the actual **13 original historical ZIPs** to restore the canonical base panel/selected snapshots/season parses, reparse 2025–26 selected injury-report PDFs, rebuild the 248,778-row cadence panel, and match every row, cell and archived Stage-6 coefficient. Scripts exist and synthetic tests pass but **the real 13-archive execution has NOT succeeded / was not directly executed**, due to a failing transient assistant container in earlier sessions. Do not assert local ZIP contents were verified.

**NOT verified, Level C:** Generate all six-season canonical roster data, season-by-season injury-report parsing, exact report checkpoint selection, player crosswalk, TV schedule, star histories, covariates, taxonomy, risk set, and complete paper models **from the ORIGINAL raw NBA injury-report PDFs, raw live boxscore JSON and original schedule/award/broadcast sources**, not already assembled intermediate CSVs.

## EXACT ORIGINAL ARCHIVES TO INSPECT FIRST — LEVEL B (13 REQUIRED)

These exact filenames were *found in the user's ChatGPT file library*. Their presence **on the user's physical computer** or in your execution environment has NOT been proven. Ask for them only if not available through attached files, connected sources, or available local folders. Do not silently substitute a similarly named version. Locate and inspect every ZIP's member manifest, sizes, SHA-256 and expected role:

1. `nba_player_game_analysis_ready_v1.zip` — canonical base panel, `player_game_panel_analysis_ready.csv.gz`.
2. `nba_player_crosswalk_final_v1.zip` — reviewed `player_crosswalk_final.csv` and potential `player_alias_table.csv`.
3. `nba_player_game_at_risk_core_v1.zip` — historical `parser_2023plus.py` and upstream construction code.
4. `nba_canonical_snapshot_selector_v1.zip` — six season snapshot join maps and four canonical team-status maps.
5. `audit_2020_21_corrected_outputs.zip` — 2020–21 parsed rows.
6. `audit_2021_22_cadence_outputs.zip` — 2021–22 parsed rows.
7. `audit_2022_23_pre_s4_outputs.zip` — 2022–23 parsed rows.
8. `audit_2022_23_s4_join_results.zip` — 2022–23 final harmonized team-game status.
9. `audit_2023_24_pre_s4_outputs.zip` — 2023–24 parsed rows.
10. `audit_2023_24_s4_join_results.zip` — 2023–24 final harmonized team-game status.
11. `audit_2024_25_pre_s4_outputs_corrected.zip` — corrected 2024–25 parsed rows.
12. `audit_2025_26_upload.zip` — original 2025–26 hourly PDF archive.
13. `audit_2025_26_targeted_upload.zip` — original 2025–26 targeted quarter-hour PDF archive.

Also inspect these specifically named **Group B upstream** local/Library archives for Level C:
- `audit_2020_21_upload.zip`
- `audit_2021_22_upload.zip`
- `audit_2022_23_upload.zip`
- `audit_2023_24_upload.zip`
- `audit_2024_25_upload.zip`
- `NBA_Historical_Source_Inventory.zip`
- `nba_boxscore_roster_frame_v1.zip`
- `nba_boxscore_roster_frame_v2_output_upload.zip`
- `nba_boxscore_roster_frame_v2_repair.zip`
- `nba_player_game_at_risk_star_cup_v1.zip`
- `nba_game_covariates_v1.zip`
- `nba_announced_tv_six_seasons_v1.zip`
- `nba_announced_tv_2020_21_v2_final.zip`
- `nba-2025-26-share.zip`
- `nba_player_crosswalk_static_v1.zip` and `nba_player_crosswalk_v1_1.zip`.

**Group C quality-control/previous-results archives** worth inspecting when appropriate:
`audit_2020_21_s4_join_results_rechecked.zip`,
`audit_2021_22_s4_join_results.zip`,
`audit_2024_25_s4_join_results.zip`,
`audit_2025_26_s4_join_results.zip`,
`nba_cadence_harmonized_identification_v1.zip`,
`NBA_Cadence_Harmonized_Reruns_2026-10-25.zip`,
`NBA_Reruns_Results_and_Code_2026-10-25.zip`,
`NBA_Method_Audit_Reproducibility.zip`,
`nba_load_management_final_reproducibility_freeze_2026-08-12.zip`,
`nba_december_2025_exact_clock_pdf_audit_patch.zip`,
`nba_exact_clock_candidate_review.zip`,
`nba_october_clock_sensitivity_patch.zip`,
`nba_source_validation_provenance_patch.zip`,
`nba_october_2026_reproducibility_completion.zip`,
`nba_taxonomy_validation_scored_v1.zip`,
`NBA_Coding_Agreement.zip`,
`NBA_Blinded_Human_Coding.zip`, and `audit_2025_26_upload(1).zip` (determine whether identical to the unnumbered archive; never assume).

Do not confuse source PDF archives with processed `pre_s4_outputs` or `s4_join_results` ZIPs.

## PREVIOUS WORK ALREADY COMMITTED ON GITHUB

Files under `scripts/data_rebuild/`:
- `audit_raw_inputs.py` — selected/full raw report SHA audit and JSON cache structure/ID checks.
- `build_source_lineage.py` — 7,230 primary-source report-to-boxscore metadata join.
- `restore_historical_layout.py` — source ZIP preflight, exact basename matching, conflict checks, non-destructive copies, whole-ZIP and member SHA-256 provenance. Needs real private ZIP validation.
- `reparse_2025_selected.py` — original 2025 PDF parser wrapper, selected basename+timestamp reconciliation, full-inventory hashes and per-PDF parse log/zero-row safeguards.
- `run_historical_cadence_builder.py` — isolated original model/panel build with path-only rewrite.
- `rebuild_from_archives.py` — Level-B orchestration.
- `compare_panels.py` — keyed strict all-cell comparison.
- `validate_cadence_panel.py` — six-season, ID, risk/onset and frozen count invariants.
- `compare_stage6_models.py` — all four historical model specification/coefficient checks.
- `replay_stage6_from_frozen.py` — proven, independent Level-A Stage-6 regression recalculation.

Source executable logic is preserved in `scripts/executed/06_cadence_harmonized_identification/` (`parse_2025_selected.py`, `build_harmonized_panel_and_models.py`, `run_cadence_models_fast.py`). Regression tests are at `tests/test_data_rebuild.py`; GitHub Actions at `.github/workflows/data-rebuild-tests.yml`. The frozen reference is `data_intermediate/player_team_game_harmonized_cadence.csv.gz`, with reference model outputs in `packages/06_cadence_harmonized_identification.zip`. Use `requirements-lock.txt` (Python 3.12 for tested analysis), not only floating dependencies.

**Important discovered pitfalls**:
- Earlier restore code **guessed ZIP internal paths**, causing an unverified replay.
- Earlier `--check-only` **wrote data**; fixed to read-only.
- Earlier 2025 SHA test erroneously compared harmonized snapshots to the latest-pre-tip primary selection map; corrected to the **full** `injury_report_inventory.csv.gz`.
- Historical 2025 parser catches worker errors and may exit 0 despite bad PDFs; now require full parse-log reconciliation and explicit manual review of zero-row parses.
- Player alias conflicts can change identity joins; reject conflicts rather than picking one silently.
- Raw ZIPs must be copied, NOT writable-hardlinked to originals.
- The original PDF parser uses top-level multiprocessing `ProcessPoolExecutor` and may fail under macOS spawn semantics. Use a Linux execution environment for faithful Level-B replay. Verify PDF parser dependencies beyond the statistical lockfile.

## SOURCE-INVENTORY FACTS AND SPECIAL CASES

The historical inventory has **37,342 candidate report URL checks** and **27,755 saved, individually hash-verified PDF objects** across seven archives. The primary 7,230-game report map uses **2,054 distinct selected primary PDFs**; that 2,054 count is NOT a verified harmonized-selected report count. The 2020–21 archive contains 617 saved PDFs, not 5,088 saved reports. There are **21 affected game selections linked to eight December 19–21, 2025 PDFs** with 15-minute discrepancies between PDF header and filename/manifest times. Source audits report that these remain pre-tip; checkpoint eligibility still requires a separate exact-clock sensitivity. The archive includes missing original collection timestamps — do not infer them. Original **7,230 per-game raw NBA boxscore JSON payloads have not been verified/recovered as a complete cache**; tabular boxscore output or candidate endpoints alone are insufficient proof.

Additional source groups include six original `nba-2020-UTC.csv` through `nba-2025-UTC.csv` fixture CSVs, five original NBA 2021–26 schedule PDFs, and six archived 2020–21 broadcaster announcement pages. Reconstructing TV, streaming-only coverage, venue/travel/Elo and star recognition is Level C and requires actual original transforms/sources.

## NEXT ACTIONS — PLEASE EXECUTE IN ORDER, DO NOT JUST RECOMMEND

**Stage 0 — reconnaissance and provenance**
1. Check exact current GitHub PR #4 and branch status; look at its latest successful and failing CI runs and logs. Read the existing handoff and current code.
2. Search available file mounts, connected file library and local provided folders for the 13 Level-B archives; confirm actual accessible paths. Their names in the user's file library are not evidence they exist on the local computer. Never invent an archive's member names/hashes.
3. Inventory each original ZIP: whole-file SHA-256 and size; ZIP integrity; member names; sizes; collision/multiple basename checks; select exact expected internal inputs. Compare source hashes to any historical manifest reference. Report absent or irretrievable originals.
4. Validate original PDF parser dependencies and runner OS. Keep source archives immutable.

**Stage 1 — historical intermediate-to-panel (Level B)**
5. On Linux, run read-only preflight from repository root:
```bash
python3 scripts/data_rebuild/rebuild_from_archives.py \
  --archive-dir /path/to/13_original_zips \
  --historical-root data_rebuild/output/nba_continue \
  --check-only
```
6. Diagnose preflight member/path errors against actual ZIP contents; correct code only when supported by original archive evidence. Never pick a similar member by guess or relax an assertion simply to pass.
7. Audit 2025 harmonized selected PDFs using the **full** source inventory, with original-manifest digests. Run the original parser, fail if any per-document parse error is recorded, reconcile all (PDF basename, timestamp) pairs and extracted row counts. Zero-row outputs require manual justification.
8. Run true Level-B reconstruction (after verifying original inputs and environment):
```bash
python3 scripts/data_rebuild/rebuild_from_archives.py \
  --archive-dir /path/to/13_original_zips \
  --historical-root data_rebuild/output/nba_continue \
  --metadata-dir ../nba-ppp-star-availability/provenance/historical_sources
```
9. Require strict keyed comparison with `data_intermediate/player_team_game_harmonized_cadence.csv.gz`; report row-level discrepancies and potentially meaningful differences, no forced normalization. Check 248,778 rows / 7,230 games / 180,664 risk rows / 12,731 new onsets, missing/unmatched identities, all six season QA tables.
10. Rerun four historical Stage-6 models **from the reconstructed panel** and compare coefficients/SE/CIs/p-values to the archived reference; save results and complete source/script/env digests. Stage-6 model-only replay from the *frozen* panel is already verified, so do not count that again as evidence of Level B.
11. If all steps actually pass, update PR #4 with exact run manifests and evidence; if not, leave draft and report the precise blocker.

**Stage 2 — from original NBA raw source data (Level C)**
12. Locate/recover original boxscore JSON files for all 7,230 NBA game IDs. Inspect derived ZIPs for actual raw payloads, record source URLs/endpoints as candidates unless proven, verify IDs/roster status, hash and parse all raw payloads.
13. Rebuild 2020–21 through 2024–25 PDF parsing and checkpoints from original archived PDFs; join official status, team-games and player identities, with explicit missing/ambiguous cases.
14. Rebuild six-season fixture/TV schedules and national-partner streaming inclusion; awards/star classification; NBA Cup, travel, Elo, timezone, rest and other covariates; taxonomy and all distinct frozen model families. Compare at every intermediate boundary.
15. Run a *separately labeled*, preregistered exact-clock checkpoint sensitivity for the 21 affected 2025 games. Do not overwrite historical results.
16. Produce a reproducible dependency graph, pinned environments, acquisition/provenance limitations, source-to-final scripts, unit/integration tests, human-readable release notes, and a credible unverified-source list.

**Scientific and safety rules throughout**
- Preserve frozen inputs/outputs and the original executed code. Changes go to new scripts/docs and ignored output directories; no opportunistic model specification changes.
- Use original per-game/per-player identities and immutable source manifests; fail closed on duplicates, missing data and contradictory manifests.
- No silent imputations or fabricated data. Do not claim original source download timestamps exist.
- Run and inspect tests; report failures and quantitative differences even if inconvenient.
- Keep raw NBA PDFs, licensed third-party broadcast assets and private full JSON caches out of public Git without rights review; publish code, manifests and permissible derived aggregates instead.
- Never merge PR #4 until actual Level-B archive replay passes and has defensible evidence. Avoid rewriting unrelated Git work; keep PR reviewable.
- Do not promise background work or future delivery without executing an authorized recurring/scheduled tool.

## REQUESTED RESPONSE FORMAT AND DELIVERABLES

First summarize: (a) actual GitHub/CI state, (b) actual available private archives vs library-only filenames, and (c) highest-priority scientifically meaningful next step. Then DO the work with available tools. As you advance, provide concrete commits/PR links, commands, test output, SHA/row-count logs and a file-by-file source inventory with status **verified / inferred / missing**. Describe the exact boundary of what has been replicated. If blocked, present the precise missing filename, expected member/schema, error and the shortest user action needed to unblock; do not misrepresent a partial dry run as successful historical reproduction.

**Begin by inspecting PR #4 and actual available 13 private ZIPs. Prioritize getting a genuine Level-B replay over adding more cosmetic code or documentation.**
