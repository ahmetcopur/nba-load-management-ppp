# Independent Level-B verification and exact-clock sensitivity
Date: November 8, 2026

Scope: historical intermediate archive -> cadence-harmonized panel -> Stage-6 regression replay. This is NOT a complete raw six-season NBA injury-PDF/boxscore-JSON-to-paper reconstruction.

## Original corrected 2024–25 input recovered

The preferred original file **audit_2024_25_pre_s4_outputs_corrected.zip** is available in the user's ChatGPT file library and was independently inspected.

- ZIP size: 13,479,653 bytes.
- ZIP SHA-256: 6b569b2f39b9f2e73087dffd3e83f11d32c5ac09fb92661d4c4b467d5b3bdcb8.
- Builder member: s1_snapshot_rows_regular_season_real.csv.
- Builder member SHA-256: 4c7b9fb396163b6491f1d49ba67be46c70f9b167f9561425fe8ab12f3a0e4165.
- Builder member: 418,059 rows and 15 columns.
- Earlier pre-S4 archive file SHA-256: 13307579612f26bb52335a40cd3556a76a4babdf459ae905b1b86b0940ce5cee.
- **Independent row-multiset comparison** of those two CSVs: identical column order and all 418,059 complete records; zero missing/extra records and zero duplicates. Byte hashes differ because record order differs.

The distinct Claude source-reparsed stand-in, with hash starting 4bda2cb4, is not independently established as row-multiset-identical to the corrected original since that stand-in's complete contents were not attached. The canonical Level-B run used the *actual corrected original*, not that fallback.

## Canonical historical intermediate-to-panel replay

An independent local container staged all 13 historical ZIPs, ran the original selected-2025 parser and original Stage-6 builder, and separately ran the original historical fast-regression script. The original builder crashed after panel output at its known norm.sf name collision; the fast regression script supplied the archived coefficients.

- 355 selected 2025–26 PDFs parsed with no errors; 47,187 player-report rows.
- Rebuilt panel: 248,778 player-team-game rows, 7,230 games, 180,664 onset-risk rows, 12,731 new onsets.
- Rebuilt and frozen panels, after decompression: **byte-identical**, each 122,661,378 bytes and SHA-256 3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac.
- The original four Stage-6 regression models on the rebuilt panel matched archived coefficient estimates, standard errors, confidence limits and p-values to floating-point precision (maximum deviation about 1.29e-14).
- Full-control legacy interaction +2.630448590 pp, CI +0.045749379 to +5.215147802, p approximately 0.04608, N=180,530.
- Full-control harmonized linear interaction +1.238970365 pp, CI −1.345677981 to +3.823618711, p approximately 0.34745, N=180,530.

## Independent FULL December 2025 corrected-clock sensitivity

I executed the supplied exact_clock_sensitivity_2025.py using the **original corrected 2024–25 historical replay root** and temporary wrappers that invoke the archived original 2025 PDF parser, cadence builder and fast regression script with only input/output paths adapted. This was an actual re-selection, reparse, panel rebuild, and four-model refit, NOT just inspection of Claude's saved results.

- 5,023 2025–26 PDFs examined; 1 ambiguous DST header excluded from selection.
- 1,230 selected games, 355 distinct selected original PDFs.
- 21 selected games used 8 PDFs printed 15 minutes later than nominal checkpoint times.
- Re-selection chose 8 earlier PDFs; 42 team-game statuses unchanged.
- 733 affected player-game rows changed; zero changed rows outside the affected 21 games.
- Field-level changes: designation_status 15, designation_reason 1, snapshot_basename 241, snapshot_timestamp_utc 241, team_snapshot_minutes_before_tip 733.
- At the affected games: 514 risk rows and 35 onsets, both unchanged.
- **Independent all-key check:** all 248,778 player-team-game IDs matched; across the full panel there were **ZERO** changed absence_onset_harm, at_risk_for_new_onset_harm, or absence_now_harm cells.
- The four original fast regressions all matched archived Stage-6 results within 0.001 pp/0.001 p-value tolerances.
- The sensitivity panel differs intentionally from the frozen panel in designation/timing fields. Uncompressed variant: 122,661,849 bytes; SHA-256 274e984692a533cf4e60ab16f61ce4423fd4d63624499806172d5dacd7e261ee.

This sensitivity does not establish independent causal effects of PPP; the policy, 65-game awards rule and NBA Cup timing overlap.

## Corrected engineering workflow

1. Refuse pandas 3 for the historical builder because the original object.fillna(False) / boolean NOT logic otherwise produces scientifically invalid risk sets.
2. Use the **separate original historical fast regression executable** after the builder writes its eight expected pre-model outputs and reaches the known norm.sf error. Other errors fail closed.
3. Prefer the **original corrected 2024–25 archive**. Only use source-PDF reparse as an explicit, prominently labeled fallback.
4. Re-run the 2025–26 clock-selection sensitivity in a separate root, never changing the original frozen panel.
5. Run offline tests under a pandas-2 / PyMuPDF environment; never confuse CI smoke tests on public frozen data with validation against the private raw archives.

## Execution environment, provenance and outstanding gates

Independent archive and full clock-sensitivity replay used Python 3.13.5, pandas 2.2.3, numpy 2.3.5, SciPy 1.17.0, statsmodels 0.14.6 and PyMuPDF/fitz 1.26.7. These are independently **tested reconstruction versions**, not known to be the exact original researchers' Python package environment.

The original shared repo provenance is pinned to commit 0bd713d97e8d519df5700ef473da34aba4495223. The original 2024 and 2025 PDF/source material and original boxscore JSON remain outside public Git.

**Verification boundary:** This independent full sensitivity ran the supplied script with **temporary local source/path wrappers** rather than a fresh checkout of the integrated production CLI. The new PR #4 scripts are separately subject to GitHub CI unit/syntax tests. A clean-root production CLI run against all original 13 ZIPs should be completed before promoting PR #4 from draft.

**Level C remains unverified:** original six-season raw PDFs, 7,230 raw NBA boxscore JSON payloads, fixture/TV source tables, star histories and covariates must still be independently parsed and combined from original inputs. Claude reports 7,185 main-cache JSON filenames plus 45 distinct discovery filenames on the user's Mac; these counts and raw JSON **contents/hashes** were not independently checked in this verification.
