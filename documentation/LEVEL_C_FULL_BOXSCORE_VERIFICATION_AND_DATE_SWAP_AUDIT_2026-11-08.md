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
