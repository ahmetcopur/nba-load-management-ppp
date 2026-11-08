# Independent Level-B verification with the original corrected 2024–25 archive
**Verification date:** 2026-11-08  
**Scope:** historical intermediate-to-cadence-panel replay; **not** six-season raw boxscore/PDF-to-paper reproduction.

## What changed relative to the Claude handoff

The report accompanying `level_b_replay_pr4.patch` said `audit_2024_25_pre_s4_outputs_corrected.zip` was absent from the user's Mac and used a source-reparsed substitute. The **original corrected ZIP is available in the user's ChatGPT file library**, and I inspected it directly in a separate execution environment.

The corrected ZIP is 13,479,653 bytes; archive SHA-256:

`6b569b2f39b9f2e73087dffd3e83f11d32c5ac09fb92661d4c4b467d5b3bdcb8`

Its exact builder input `s1_snapshot_rows_regular_season_real.csv` has **418,059 rows and 15 columns** with SHA-256:

`4c7b9fb396163b6491f1d49ba67be46c70f9b167f9561425fe8ab12f3a0e4165`

The companion `s1_snapshot_rows_regular_season.csv` in that same corrected archive is byte-identical. Claude's re-parsed stand-in had a different recorded SHA-256 (`4bda2cb4...`); this does not prove a semantic difference, but byte identity of the substitute to the original wasn't shown. Here the *actual original* was used instead, so the 2024–25 exception is unnecessary for this replay.

## Independent execution (not simply rereading Claude's logs)

I staged the 13 historical source ZIPs in an isolated temporary folder without altering original archives. Stage-6 source scripts were extracted from `nba_cadence_harmonized_identification_v1.zip`, with only the original hardcoded input root replaced by a local path. Installed runtime: **Python 3.13.5, pandas 2.2.3, numpy 2.3.5, SciPy 1.17.0, statsmodels 0.14.6, PyMuPDF binding 1.26.7**. This is not the original 2026 research runtime; it is a *second* successful environment, distinct from Claude's claimed Python 3.12.3 / PyMuPDF 2.1 environment.

1. Original `parse_2025_selected.py` reparsed **355 selected 2025–26 PDFs**, produced **47,187 player-report rows** and logged **zero parser errors**.
2. Original `build_harmonized_panel_and_models.py` produced **72,695 selected rows**, **zero unmatched report players** and **207 report-only roster additions**.
3. The original builder then crashed *after writing the panel*, at `AttributeError: 'function' object has no attribute 'sf'`, consistent with the known `norm` name collision. The original separate `run_cadence_models_fast.py` was then executed.
4. The rebuilt compressed panel and the archived Stage-6 panel decompressed into byte-for-byte **identical 122,661,378-byte CSVs**, each containing **248,778 player–team–game rows**. Both decompressed SHA-256 values are:
   `3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac`.
   The gzip containers themselves differ due to compression metadata/serialization; decompressed bytes are the scientifically relevant identity check.
5. The original Stage-6 regression runner reproduced **all four** reference specifications, matched definition/control/sample keys, and the largest absolute difference across estimate, SE, 95% CI and p-value was approximately **1.29e-14**.
6. Additional historical output files match the archived Stage-6 package byte-for-byte: `harmonized_game_snapshot_map.csv`, `harmonized_team_game_report_status.csv`, `harmonized_unmatched_report_players.csv`, `cadence_panel_counts_by_season.csv`, and `snapshot_selection_comparison.csv`. Selected-report source intermediate files are not all mirrored in the Stage-6 ZIP, so no byte-equality claim is made for unarchived ones.

**Caution:** These findings verify a replay from **historical intermediate inputs plus selected 2025 PDFs**, *not Level C from the raw 7,230 original live boxscore JSON files and all six seasons of original PDF sources*. No separate independent exact-clock sensitivity rerun was done in this verification; those claims remain evidence supplied with Claude's patch.

## Exact reference scripts and hashes

Original Stage-6 source:
- `build_harmonized_panel_and_models.py` SHA-256 `81cab67185083572051b44cefbf836acfe6e1860ccf27dd812dc3729aa2a9272`
- `parse_2025_selected.py` SHA-256 `c97657d2ae4e2c3912e63f90552492fa2a7e776cb2efe880eaafc03eeedf6933`
- `run_cadence_models_fast.py` SHA-256 `f33950c15302f281830bbb5f047ca84b744a77d9039c8a313f158c63374001d3`
- Frozen Stage-6 ZIP member `results/player_team_game_harmonized_cadence.csv.gz` original gzip SHA-256 `5483fc07465b84b20d29f54f0c49da53bef367cba712ad174111f3a7a794d8cd`

## GitHub integration recommendation

The attached two-commit patch is **not yet applied by this audit**. Verify its exact code and evidence, then apply it to the open PR branch. Its optional `--reparse-2024-25-from-pdfs` fallback is useful when the corrected archive truly cannot be acquired locally, but **do not use that fallback in the canonical Level-B verification when the original corrected ZIP is available**. Preserve the frozen panel, source archives and the separately labeled exact-clock sensitivity. Review the complete patch's CI and archive-provenance claims before merging.

The original corrected ZIP must remain outside GitHub's public raw-data archive; the user can obtain it from their ChatGPT file library or via an explicitly shared file. The public repo should keep checksums and code, not rehost raw third-party source archives.


## Independent bounded exact-clock input check

After the Level-B panel replay, I independently executed the **candidate-selection portion** of the uploaded `exact_clock_sensitivity_2025.py` on the two original 2025–26 NBA PDF ZIPs. It opened all **5,023** archived PDFs, found **one** header with an ambiguous daylight-saving-time clock, and reconciled the harmonized selector for 1,230 games / 355 selected PDFs.

- **21** selected games map to **eight** PDFs whose printed header clocks are **15 minutes later** than their nominal checkpoint timestamps.
- **No** selected PDF has a printed time at or after the scheduled tip.
- Re-selecting the latest archived printed-clock PDF at/before each affected nominal checkpoint gives **21 candidate game rows and eight distinct replacement PDFs**, with 75–255 minutes of lead time to tipoff.
- The newly computed candidate CSV matched **every field and row** in `validation/level_b_replay_2026-11-08/exact_clock_sensitivity/exact_clock_candidates.csv` supplied with Claude's patch, after aligning by game ID. Thus its **candidate selection** is independently verified.

**Boundary:** I did **not** independently execute the entire replacement-report → designation changes → rebuilt panel → refitted-model exact-clock sensitivity. The patch reports zero changes to onsets and model coefficients, but those downstream claims should still be validated after integration and a full end-to-end sensitivity run. Do not conflate the independently verified candidate selection with verification of the entire sensitivity.
