# NBA Level C: reported complete raw boxscore replay and independently audited date errors

**Updated:** November 8, 2026  
**Branch:** audit-rebuild-reliability-2026-11  
**PR:** https://github.com/ahmetcopur/nba-load-management-ppp/pull/4

## Raw-JSON to archived roster-frame verification

The uploaded level_c_boxscore_full_verification.patch includes a complete offline 7,230-JSON replay report from the user's Mac/cloud environment. It reports successful reproduction of the archived NBA V2 roster frame and canonical base panel, with no differing comparable cells.

**Independently checked in this review:**
- The provided 7,230-row SHA-256 manifest contains 7,185 main-cache and 45 discovery JSON entries, six expected seasons, unique official NBA game IDs, and zero logged filename/season/byte-size failures.
- Its game-ID set matches all 7,230 IDs in the actual archived V2 crosswalk, with zero missing or additional IDs.
- Archived V2 output ZIP SHA-256 is 45eeade023037506d1b07ebc601c273ec442f6620adc3ab836a3d40b8774f561.
- Original archived repair script SHA-256 is c3d1c8be0dd80f5249935bac8c5de4811dc37cbb6810a98e93202a19e0b32fd0. Adding only the original one-line Boolean QA serialization fix produces executed script SHA-256 d825588e760482d7720f572cc2b66da48f7e3ce25c2866ecfbee709983cbcf39.
- The 248,571 archived V2 roster rows agree with the canonical base-panel boxscore rows on all comparable player/team/game keys and fields (previous independent review).

**Reported full original execution:** 7,230 valid unique JSONs; 7,230 matched crosswalk and manifest rows; 248,571 player rows; 14,460 team rows; zero unmatched IDs, missing player keys or output differences. Original 7,185 logged download sizes match. Report: validation/level_c_boxscore_2026-11-08/boxscore_cache_verification.json.

**Evidence boundary:** The 7,230 actual raw JSON bytes were NOT transferred to this ChatGPT environment for an independent second full execution. The evidence file and full SHA-256 manifest are sourced from the user's attached patch. The manifest as committed has SHA-256 e09d4e597ab7509c8cdc20bee94d5bf6012606c3b17fe96655a2ec6f3d418288. Original raw_json.zip was reported as SHA-256 93ab299cd1c070fd0681348988c177638af21a0e11b1af65383cd0e408d605bf but its bytes were not rehashed here.

## Reproduction environment is not the scientifically corrected environment

- Historical V2 offline repair reproduction: pandas 3.0.5, numpy 2.5.1, SciPy 1.18.0, requests 2.34.2 (per supplied environment evidence). The verification CLI reconstructs the exact executed source by applying the known one-line QA serialization change, checks exact source SHA-256 and rejects arbitrary alternative repair scripts.
- Historical Stage-6 cadence builder requires **pandas 2.2.3**, separately. Never use the boxscore requirements file for the Stage-6 builder.

The original V2 mapping code divides timestamp int64 values by 3.6e12, assuming nanoseconds. Under pandas 3, those parsed timestamps use microseconds in this context, so true time differences appear 1,000 times smaller. This reproduces the historical crosswalk but is **not correct time-distance matching**.

## Two confirmed 2021–22 NBA fixture-date swaps

| Official NBA game | Frozen fixture date, ET | Verified actual NBA date, ET | True UTC difference | Historical reported difference |
|---|---|---|---:|---:|
| Bulls at Raptors, 0022100430 | Feb 1, 2022 | **Feb 3, 2022** | **48 hours** | **2.88 minutes** |
| Heat at Raptors, 0022100784 | Feb 3, 2022 | **Feb 1, 2022** | **48 hours** | **2.88 minutes** |

Official NBA source pages:
- https://www.nba.com/game/CHI-vs-TOR-0022100430/box-score
- https://www.nba.com/game/mia-vs-tor-0022100784/box-score

The V2 crosswalk's official NBA game IDs and ordered team pairs are correct; the fixture dates in the archived model inputs are not. The new raw JSON verifier therefore audits **actual UTC differences independently** of the historical mis-scaled differences, raises an error on any previously unseen full-cache match over 36 hours, and explicitly records these two known exceptions. Historical original outputs are unchanged.

## Independent downstream covariate test

The original nba_game_covariates_v1.zip from the file library has SHA-256 4351756b74446577dabc8418b539c95dfb6e0ae6e3d8766bbee1c528d709c224; its original builder has SHA-256 268140c52c68a1f19ed1ab756f772519c460dc552938281e6ee62a1cbe087862.

An independent controlled run invoked the *original* Elo and team-game schedule functions using the archived game-level input. Baseline recreation matched all **76 columns of all 14,460 team-game rows** after normalizing only innocuous null/empty-text and null-datetime representations and tolerating numerical differences at or below 1e-8.

Correcting only the two verified official tip-UTC and Eastern game-date fields, while keeping frozen game IDs for row alignment, causes these changes:

| Covariate | Changed team-game records |
|---|---:|
| Rest days | 5 |
| Back-to-back | 4 |
| Three games in four days | 4 |
| Four games in six days | 6 |
| Travel since prior game | 7 |
| Road trip game number | 3 |
| Hours since prior game tip | 8 |
| Team pregame Elo rating, change >1e-8 | 10,681 |
| Signed pregame Elo advantage, change >1e-8 | 10,702 |

For team pregame Elo, only 767 records differ by more than 0.01, 111 by more than 0.1, six by more than 1, and three by more than 5 Elo points. Maximum absolute change: approximately 13.60 Elo points. Most propagated Elo differences are very small.

Reproduction script: scripts/data_rebuild/audit_fixture_date_swap_covariates.py. The frozen dataset and original ZIP remain unmodified.

**Critical outstanding scientific check:** Rebuild a separate player-game panel using the corrected schedule-derived rest/travel/Elo covariates and refit the primary October models with their exact original definitions. No claim is made yet about whether the published PPP × star × national-TV estimates change.

## Remaining acceptance steps

1. Run the strengthened integrated verifier against original 7,230 JSONs in a fresh compatible environment; confirm its additional actual-time-drift report and exact executed repair script SHA.
2. Rerun corrected schedule ingestion and all original game-covariate transformations from the original source schedules, TV releases, and scores; confirm impacts at each boundary.
3. Refit the original October analysis from an explicitly corrected, separately named panel. Do not overwrite published August/October freezes.
4. Continue raw six-season injury-report reconstruction, advance-announced TV and award histories, and paper-level Level-C work.
5. Keep PR #4 in draft pending production-run evidence and scientific review.

The raw NBA JSONs and official NBA injury PDFs are not uploaded publicly; this repository contains code, permissible hashes, and aggregate verification summaries.


## Additional independently executed frozen-outcome model-control sensitivity

After checking that all 11 original regression control columns in the frozen 248,778-row player-game panel matched the archived team-game covariates, I replaced only those 11 controls with the corrected-date output of the *original* historical Elo/travel/rest builder. Every player-game ID, risk/onset outcome, star status, preannounced TV, report timestamp and prior playing-history measure was kept fixed. I then ran all four archived Stage-6 regression specifications. All model sample sizes stayed unchanged.

| Historical Stage-6 model | Frozen estimate (pp) | Corrected-controls estimate (pp) | Change (pp) | Frozen p | Corrected p |
|---|---:|---:|---:|---:|---:|
| Legacy primary TV, full controls | 2.630448590 | 2.633180456 | **+0.002731865** | 0.046076466 | 0.045772941 |
| Legacy primary TV, no controls | 2.632768780 | 2.632768780 | 0 | 0.047040734 | 0.047040734 |
| Harmonized linear TV, full controls | 1.238970365 | 1.241672773 | **+0.002702408** | 0.347453286 | 0.346242395 |
| Harmonized linear TV, no controls | 1.251112606 | 1.251112606 | 0 | 0.345693676 | 0.345693676 |

Model Ns: **180,530** with full controls, **180,664** without controls. The conditional full-control coefficients move by only about **0.0027 percentage points**, much less than their sampling SEs (approximately 1.318 pp). This is evidence that correcting these *controls* alone has a small impact on these historical estimates.

**This is NOT a complete corrected-source analysis.** Changing the true game date could also alter the roster's chronological histories, absence-onset spell boundaries and pre-tip report selection. Those were **not** recomputed here. Nor were TV as-announced fields or original game IDs rebuilt. The current controlled model is an additional sensitivity, not a replacement for the published frozen original.

Reproducible script: scripts/data_rebuild/run_fixture_date_control_sensitivity.py; numerical result record: validation/level_c_boxscore_2026-11-08/corrected_fixture_controls_stage6_model_delta.json. The separately executable integrated production runner has passed syntax and synthetic tests but has not itself been rerun from a fresh private-archive root in this GitHub CI environment. The numerical results above come from an independent local equivalent of the original covariate and regression functions.


## Additional November 8, 2026 — corrected-chronology Stage-6 sensitivity (separate from control-only refit)

**Independently rerun using the original Level-B historical archive root:** The two misdated 2021–22 games were corrected in a *copy* of the base-panel fixture/covariate data; their 2021–22 selector match numbers and team status IDs were remapped to the appropriate actual-date PDFs, and the original untouched Stage-6 panel-builder and separate fast model executable were invoked with only hardcoded file roots redirected. This is a newly constructed **sensitivity panel**; the original frozen panel is unchanged.

First, independently cross-checking the original parsed 2021–22 report rows:
- `Injury-Report_2022-02-01_05PM.pdf` contains exactly **10** player listings for **Miami Heat at Toronto Raptors** (Lowry and Birch are both marked **Out**).
- `Injury-Report_2022-02-03_05PM.pdf` contains exactly **10** player listings for **Chicago Bulls at Toronto Raptors** (Lonzo Ball and Alex Caruso marked **Out**).
- The two corresponding games have **66** roster rows in the frozen Stage-6 panel, **all marked Not Listed** because the old game-to-report join mixed the date and matchup. Matching the right snapshots changes **20 designation-status cells**. National-partner TV and linear-only TV fields remain unchanged in the actual rebuilt panel.

The independent rebuilt candidate matches the entire **supplied patch evidence** on all changed onset, risk, and designation player-game IDs and every changed-cell count:
- Same **248,778** player-team-game IDs.
- **185,547** rows differ in at least one cell, mostly due to propagated very small Elo differences.
- **10** onset-risk indicator changes; total at-risk rows still **180,664**.
- **Two** new onsets removed: Kyle Lowry (Miami Heat, star, pre-policy, nationally televised), and Khem Birch (Toronto Raptors), both at the Miami–Toronto game. Their corrected game chronology follows prior absences on January 29/31. Total onsets: **12,729**, previously 12,731.
- No changes to the underlying `absence_now_harm` cells. Player-game playing history, previous-10-game minutes and distance-to-65 change for a subset of affected teams' observations as expected.
- The independently rebuilt gzip-decoded CSV contains **122,664,634 bytes**, SHA-256 `2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67`; this is a *new sensitivity variant* and must not be compared for byte equality to the original frozen panel.

| Stage-6 model | Frozen interaction (percentage points) | Corrected chronology (percentage points) | Change (pp) | Corrected p-value |
|---|---:|---:|---:|---:|
| National-partner TV, full controls | +2.63044859 | **+2.67423173** | **+0.04378314** | 0.042634 |
| National-partner TV, no controls | +2.63276878 | **+2.67688550** | **+0.04411672** | 0.043532 |
| Harmonized linear-only, full controls | +1.23897037 | **+1.28236945** | **+0.04339909** | 0.330868 |
| Harmonized linear-only, no controls | +1.25111261 | **+1.29485133** | **+0.04373873** | 0.329122 |

With controls the model sample size remains **180,530**, and without controls **180,664**. Independent coefficient differences from the supplied patch are no greater than approximately **1.3 × 10^-14**.

The +0.044 pp change is approximately 16 times the previous control-only +0.0027 pp adjustment but small relative to an approximately 1.32 pp SE. The corrected scenario does **not** reverse the sign or substantive interpretation of the historical Stage-6 TV interaction, but the underlying coding change warrants transparent disclosure. We did not isolate the causal or statistical contribution of Lowry's removed onset alone.

**Implementation safeguard:** The uploaded patch originally suppressed all nonzero model subprocess exit codes by using `replay_stage6_from_frozen.py` in an expected-mismatch context. The integrated [corrected-chronology runner](../scripts/data_rebuild/fixture_date_chronology_sensitivity.py) instead executes the original fast model code directly, verifies its original SHA-256, fails on any nonzero exit, checks all four unique specification keys and model sample sizes, and uses an independent copy of the original archive inputs to prevent source modification. Its per-cell comparison was optimized to avoid parsing 248,778 arbitrary text values as dates repeatedly.

**Scientific boundary:** This variant corrects the two fixture dates and Stage-6 history/report joins but intentionally keeps frozen `game_id` keys (which themselves encode old dates) for row-level comparability. It is not a complete source-to-paper rebuilding of the original fixture ingestion, 2020–26 report selection, TV-as-announced releases, awards, or August latest-pre-tip models. Original final 2026 manuscript tables should not be overwritten solely on the strength of this sensitivity. Further examine other analyses that depend on the original base panel, corrected game chronology and raw-schedule identification.

Reproduction code: [fixture_date_chronology_sensitivity.py](../scripts/data_rebuild/fixture_date_chronology_sensitivity.py), negative tests [test_fixture_date_chronology.py](../tests/test_fixture_date_chronology.py), and exact summary and player-key changes in [validation/fixture_date_chronology_2026-11-08](../validation/fixture_date_chronology_2026-11-08).
