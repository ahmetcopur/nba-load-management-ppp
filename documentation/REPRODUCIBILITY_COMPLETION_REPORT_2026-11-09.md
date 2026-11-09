# Reproducibility audit: scientific completion report

**Date:** November 9, 2026. **Repository:** `ahmetcopur/nba-load-management-ppp`, branch `audit-rebuild-reliability-2026-11`, draft PR #4 (unmerged). **Research source:** `OEKundakcioglu/nba-ppp-star-availability` at `0bd713d97e8d519df5700ef473da34aba4495223`.

This report covers what was executed and what it established. Detailed results are in [August corrected replays](AUGUST_CORRECTED_REPLAYS_2026-11-09.md), [manuscript reconciliation](MANUSCRIPT_RECONCILIATION_CORRECTED_CHRONOLOGY_2026-11-09.md), [October corrected chronology](OCTOBER_CORRECTED_CHRONOLOGY_RESULTS_2026-11-08.md), [October paper statistics](OCTOBER_MISSING_PAPER_STATISTICS_2026-11-08.md) and [Level B replay](LEVEL_B_REPLAY_RESULTS_2026-11-08.md). Frozen datasets, original ZIPs, raw files and the published manuscript were not modified.

## 1. Bottom line

The archived analyses reproduce. Every released August and October analysis rerun here matches its archived output before any corrected data were used: coefficients to about 1e-14 in the exact-solver stages, the permutation placebo to 0.005 pp with identical p-values, and the nonlinear stage exactly. Two 2021-22 Toronto games had swapped dates in the archived schedule, so their injury-report links pointed at other games. Correcting them moves the headline estimates by about 3% of a standard error and changes no conclusion. The data also contain no other chronology fault of this kind across six seasons.

## 2. What was executed

| Analysis | Frozen gate | Corrected run |
|---|---|---|
| Level B archive-to-panel replay (Nov 8) | panel byte-identical after decompression, Stage-6 rows within 1e-14 | n/a |
| October 10 released scripts, 33 outputs (Nov 8) | all 33 pass, max 1.1e-13 | done, 704 coefficient rows |
| October paper statistics: rates, durations, raw triple, paired contrast | published cells pass, rerun Nov 9 with zero difference | done |
| August core finalizer from source ZIPs | byte-identical to the archived core | done (248,728 rows) |
| August reviewed taxonomy transfer | all 248,730 frozen cells pass | done, corrected risk panel `5a5d286b…` |
| August predeclared heterogeneity (8 tests) | pass, 2.8e-14 | done |
| August event study, pretrends, fake-date placebos (16) | pass, 1.8e-14 | done |
| August category FDR (8) | pass | done |
| August first-pass models, executed scripts (10 tables) | pass, 1.1e-14 including SEs | done |
| August TV audit, executed scripts (5 tables) | pass, 4.1e-14 | done |
| August stage-2 identification, executed scripts (6 tables) | pass; permutation within 0.0048 pp, p exact | done |
| August preferred models, reimplementation (3) | coefficients exact, SE within 0.00064 pp | done, matches the executed scripts exactly |
| August nonlinear and multinomial | exact to full precision in the pinned environment | done; changes inside solver noise |
| Six-season chronology and identity audit | frozen has 2 duplicate team-dates and 2 rest errors | corrected has none; only 2 games moved |
| Release-PDF advance TV (2021-22 to 2025-26) | 6,060 of 6,060 rows and networks match | n/a |
| Raw boxscore JSON tips (7,230 games) | 7,224 exact | 7,226 exact; the other 4 are 2-minute Election Day 2022 tips |

## 3. Verified headline numbers

October cadence-harmonized panel (the manuscript's primary construction):

| Quantity | Published | Corrected chronology |
|---|---|---|
| National-partner DDD | +2.630 pp, p = .046 | **+2.674 pp [0.09, 5.26], p = .043** |
| Linear-only DDD | +1.239 pp, p = .347 | **+1.282 pp [−1.30, 3.87], p = .331** |
| Raw national-TV triple difference | +1.920 pp | **+1.967 pp** |
| One-game home/road shift | +1.406 pp, p = .093 | +1.378 pp, p = .101 |
| Paired one-game minus longer | +1.664 pp, p = .154 | **+1.638 pp, p = .160** |
| Joint pretrend | p = .616 | p = .659 |
| Onsets | 12,731 | 12,729 |

August latest-pre-tip panel (sensitivity construction):

| Quantity | Published | Corrected chronology |
|---|---|---|
| National-partner DDD, player + team-season FE | +3.149 pp, p = .017 | **+3.196 pp [0.62, 5.78], p = .015** |
| Linear-only DDD | +1.775 pp, p = .177 | **+1.820 pp, p = .166** |
| Vague vs specific | −8.417 pp, p = .288 | **−7.906 pp, p = .318** |
| Explicit rest, national-partner | +0.618, BH q = .050 | **+0.615, BH q = .051** |
| Explicit rest, linear-only | +0.703, BH q = .018 | **+0.700, BH q = .018** |
| Heterogeneity, smallest BH q | .393 | .400 |
| Joint pretrend | p = .433 | p = .479 |
| Permutation placebo p (partner / linear) | .09 / .26 | .09 / .26 |

All ten values listed in the audit request as previously reported (October 2.630→2.674, 1.239→1.282, 1.920→1.967, 1.664→1.638; August 3.149→3.196, 1.775→1.820, −8.417→−7.906; explicit rest +0.615 with q≈.051 and +0.700 with q≈.018) were reproduced independently in this session.

## 4. Source corrections

Release schedule game 430 (Chicago at Toronto, Dec 16, 2021) was postponed and played Feb 3, 2022 as NBA game 0022100430. Release game 784 (Miami at Toronto, Feb 3, TNT) was moved to Feb 1 as NBA game 0022100784. FixtureDownload numbers these two games the other way round. The archived base panel paired one numbering with the other's dates, so it had each game on the other's date. As a result it showed the Bulls and the Heat each playing twice in one day, and it attached reports from October 2021 and April 2022 games to them.

The correction changes only these two games, everywhere: dates and tips in both panels, official NBA IDs, report links, report-only roster rows (two removed), rest, back-to-back, travel, time-zone and three-in-four flags, and the TV lookup keys (networks kept by the release-time rule). Histories and risk sets were recomputed by the original finalizer. The audit confirms that no other game's date or tip changed in either panel, and that corrected August and October agree on all 7,230 games. Elo is path-dependent, so its values move slightly in later games (at most 9.9 points in 2021-22, under 0.23 afterward). That is the original Elo rule applied to the true order.

Retained as explicit limitations. Award lists (All-Star, All-NBA), PPP star status and Cup flags are inherited by stable key and were not regenerated from primary award or Cup releases. Their date rules were verified on both panels, and the 2021-22 All-Star switch date (Feb 21) cannot be crossed by the move. The project key `game_id` keeps the old date encoding for comparison with the frozen panel. The official IDs are in `nba_game_id`.

## 5. Reproducibility levels

| Level | Status |
|---|---|
| A, frozen data to published estimates | complete for every released August and October script, plus the paper statistics |
| B, archived intermediates to frozen panel | complete for the October cadence panel (byte-identical) and the August core (byte-identical) |
| C, raw sources to panel | boxscore JSON to roster frame: exact for all 7,230 games. Raw tips: 7,226 exact. Release-PDF TV 2021-22 to 2025-26: exact. Injury-report PDFs 2024-25: reparsed and matching (Nov 8). December 2025 exact-clock PDFs: checked |
| C, still open | 2020–21 through 2023–24 *raw upload ZIP filenames* were subsequently recovered in the user's Library, but ZIP members, PDF hashes and source reparses remain unverified. The complete 2025–26 raw PDF set was not reparsed here. 2020–21 TV web pages and primary award/Cup source tables were not independently reconstructed |

The subsequent [private-source recovery audit](PRIVATE_SOURCE_RECOVERY_AUDIT_2026-11-09.md) located four named 2020–21 through 2023–24 upload ZIPs in the file library. Their **content and hashes are not yet verified**; the next step is to inspect those actual archives using the original public provenance inventory and then perform source-PDF reparses. The original primary award and Cup source files are still required to independently reconstruct August star and Cup flags.

## 6. Code defects found and fixed

| Defect | Effect | Fix |
|---|---|---|
| pandas 3 dtype check in the taxonomy gate | the corrected chain could not run under the pinned analysis environment | value and order comparison, test, pandas-3 CI step |
| ZIP runner required a nonexistent column | would have rejected the genuine corrected ZIP | requirement removed, duplicate-ID check and real-header test added |
| Portable scripts drop `dist65_10` | harmless for identified coefficients, but shifts SEs (≤0.009%) and the permutation placebo | suite now runs the executed originals with only `/mnt/data` redirected |
| Archived `player_linear_trends.csv` came from the sparse exact script | an iterative copy with the same file name never converged | gate maps the archive to the correct script |
| Nonlinear solver tolerance (original code) | row order alone moves the estimate by about 0.35 pp | documented, unchanged, not reinterpreted |

## 7. Manuscript implications

No published conclusion changes. National-partner TV stays just inside 5% under both report constructions, linear-only stays insignificant, the home/road one-game shift stays uncertain (p .093 → .101), the paired contrast stays uncertain, pretrends and placebos stay null, and no heterogeneity or wording mechanism appears. Proposed corrected text is in the [reconciliation](MANUSCRIPT_RECONCILIATION_CORRECTED_CHRONOLOGY_2026-11-09.md), which also lists the manuscript numbers not verified here: the NBA TV common-sample check, two archived latest-pre-tip side estimates, the season-level wording tables and the figures.

## 8. GitHub status (updated after this report's original local run)

The paragraph below replaces an obsolete snapshot that said GitHub was inaccessible. The original correction patch **was committed and pushed** to `audit-rebuild-reliability-2026-11` (commits `0a7f49d`, `7ac75bd`, `334277e`). [Draft PR #4](https://github.com/ahmetcopur/nba-load-management-ppp/pull/4) remains open and **unmerged**. [GitHub Actions run 42582389410](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42582389410) completed with **11/11 jobs successful**, including the first public independently executed August original-stage suites; it did not run the corrected private risk dataset.

A subsequent November 9 continuation recovered and opened the user's real `player_game_panel_model_at_risk_analysis_ready.csv.zip` and established that it contains **180,829** rows and decoded SHA-256 `d6e82ba6…`, not the earlier reported corrected 180,831-row panel `5a5d286b…`. The same continuation discovered four named 2020–24 raw upload archives but could not inspect their members because the local execution environment stopped responding. See the linked [source recovery audit](PRIVATE_SOURCE_RECOVERY_AUDIT_2026-11-09.md).

New raw-archive SHA/inventory verification code and synthetic tests were added to the draft PR. Green synthetic checks, whether historical or new, must **never** be described as successful private-source Level-C acceptance. Do not merge before scientific review and remaining source acceptance.

## 9. Scientific assessment

The study's computational record is now reproducible from archived intermediates through every released estimate, and from raw sources for box scores, tips and release-time TV. The one data fault found is real but small, and it is now corrected everywhere it reaches. The substantive picture is unchanged and remains modest. Under the national-partner definition, the post-2023 star-by-TV interaction is about +2.7 pp (cadence) or +3.2 pp (latest-pre-tip), with p near .04 and .015. It disappears under the linear-only definition. Pretrend tests pass, but the permutation placebo is only borderline (p = .09). The PPP, the 65-game rule and the Cup started together, so none of these comparisons isolates the PPP. The manuscript's cautious wording fits the corrected evidence as well as it fit the frozen evidence.
