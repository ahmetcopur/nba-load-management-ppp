# Real original 2020–24 NBA injury-PDF source verification and parser replays

**Executed 2026-11-10, Python 3.13.5.** Working branch `audit-rebuild-reliability-2026-11`, PR #4 (draft). Sources: private original uploaded archive ZIP files previously located in the user's ChatGPT Library. The frozen public reference is `OEKundakcioglu/nba-ppp-star-availability@0bd713d97e8d519df5700ef473da34aba4495223`. **Do not publish the original PDFs or private ZIPs.** This document records executed checks, not synthetic CI alone.

## 1. Raw original ZIP and individual PDF identity — PASS

Recovered all four **actual** archived files from the Library, not just their filenames, and independently computed SHA-256 over the full ZIP byte streams. For provenance, independently obtained the original `injury_archive_summary.csv` and `injury_report_inventory.csv.gz` from the previously archived source-provenance patch, verifying their original immutable Git blob SHA-1 IDs `ca5188baf047e8154003b0daad1cb319af1ff3d4` and `a3273b97035c63f9e34b68bac0dddf863588adc4` before comparing any bytes.

| Season | Original ZIP | SHA-256 matches pinned source | Actual PDF hashes matched | Missing/extra indexed PDFs | ZIP all-member CRC |
|---|---|---|---:|---:|---|
| 2020–21 | `audit_2020_21_upload.zip` | yes, `e310c814…` | 617/617 | 0/0 | pass |
| 2021–22 | `audit_2021_22_upload.zip` | yes, `1e027ce6…` | 5,567/5,567 | 0/0 | pass |
| 2022–23 | `audit_2022_23_upload.zip` | yes, `bea1adea…` | 5,541/5,541 | 0/0 | pass |
| 2023–24 | `audit_2023_24_upload.zip` | yes, `9cca3e58…` | 5,441/5,441 | 0/0 | pass |
| **Total** | 4 original files, 616,435,080 compressed bytes | **all pass** | **17,166/17,166** | **0/0** | **all pass** |

All ZIP member names were unique, no unsafe paths/symlinks were present, and every indexed PDF was streamed through SHA-256 in addition to the complete ZIP CRC check. These checks establish the authenticity of **saved** source bytes, not completeness of all NBA hourly report URLs: the 2020–21 archive includes just **617 of 5,088 candidate report URLs**, with 4,471 missing original candidates.

## 2. Independent actual PDF → parser-output execution

Original season-specific parsers were read **unchanged** from the historical archives; original present PDF bytes were staged in a private scratch directory only after each PDF matched its own archived manifest SHA. Output comparisons use identical CSV headers and full **multisets of complete CSV records**, not row-order-dependent hashes or a self-compare of frozen CSVs. Each archived parser log was checked separately.

| Season/scope | Source PDFs actually reparsed | Reparsed CSV rows | Exact historical output rows? | Exact parser log? | Outcome |
|---|---:|---:|---|---|---|
| 2021–22 full hourly archive | 5,567 | 398,715 | Full hourly reference CSV unavailable | 5,567 successful PDF parses; archived 696-report subset exact | Validated full parse, partial exact reference |
| 2021–22 1PM/5PM/8PM harmonized subset | 696 | 58,631 | **Yes, 0 missing/extra records** | **Yes, 0 differences** | **PASS** |
| 2022–23 regular season | 4,101 | 354,146 | **Yes, 0 missing/extra records** | **Yes, 0 differences** | **PASS** |
| 2023–24 regular season | 4,097 | 388,878 | **Yes, 0 missing/extra records** | **Yes, 0 differences** | **PASS** |
| 2020–21 fixed-width parser, current default `pdfplumber` | 617 | 41,884 (archived 41,780) | **No** | 50 mismatched log rows | **FAIL / NOT REPRODUCED** |
| 2020–21 explicit `x_density=5.0` diagnostic | 617 | 41,780 | **No; 93 records with different reason text** | **Yes, exact** | **DIAGNOSTIC ONLY, NOT ACCEPTED** |

The 2023–24 script `nba_injury_landscape_parser_v4.py` in the pre-S4 archive and `parser_2023plus.py` in the frozen core ZIP are byte-identical, SHA-256 `197c29d46dfea221c381664b96a05453737df55d7b8dd5d5e6f44e49b69e0e06`. The original `parser_2021_2022.py` handled 2022–23 in actual source-PDF sample tests (four sampled PDFs matched exactly); the 2023+ landscape parser yielded no row boundaries on those portrait reports and **must not** be substituted. The same 2021–22 historical parser is used on 2021–22. The full 2021–22 hourly run's harmonized 696-PDF subset independently reproduces all 58,631 historical rows and its parser logs, confirming the subset is not an artifact of a separately constructed 696-row input.

### 2020–21 environment discrepancy — scientific exception

The unchanged original fixed-width `nba_injury_pdf_layout_parser.py` with current `pdfplumber==0.11.9` misaligns body text with header positions. For example, the status string `NOT YET SUBMITTED` can be split into `N` / `OT YET SUBMITTED` and changes the submission class. The original **archived reference remains authoritative**. The current default produced 41,884 instead of 41,780 rows, and 50 log rows differ.

For diagnosis only, the original `parse_pdf` implementation was invoked without editing the parser source, while explicitly setting `pdfplumber.Page.extract_text(layout=True, x_density=5.0)`. This recovers exactly 41,780 rows, all 617 parser logs and **every field except 93 free-text `reason` values across 44 source PDFs**. All row keys, player/team/game, submission status and current injury status fields agree when compared in archived within-PDF record order. The 93 reasons are commonly wrapped onto adjacent player rows. **Do not silently replace these 93 archived injury reasons**, because wording/taxonomy analyses may be affected. This diagnostic does not establish the original `pdfplumber` version or exact source-parser reproduction. Recover the historical text-extraction version/settings and require all 41,780 full rows to match before marking this season complete.

## 3. Verification scope and remaining scientific gates

This run **did not** rerun the full player-game panel, model estimates or manuscript from reconstructed PDFs. Verified raw PDFs and exact archived per-season parse outputs still must be joined via historical selectors, player identities and schedule using the original source-code rules. A green source-verification result must never imply a causal PPP-only estimate.

Further remaining Level C: reproduce 2020–21 fixed-width extraction exactly; independently reparse/verify 2024–25 and full 2025–26 in the same acceptance chain; reconstruct inherited award/All-Star/All-NBA and Cup rules from their original dated announcements; verify 2020–21 advance-TV release-time definitions; and finish manuscript common-sample/wording/figure reconciliation. **Frozen archives and the manuscript were not modified. PR #4 stays draft.**

## 4. How this was executed

The original ZIPs were mounted from the user's private file library; their original SHA-256 values and all 17,166 indexed members were independently checked against the pinned real archive inventories, not just a local smoke test. For each audited season, the archived original manifest and verified PDFs were staged under a temporary ignored directory; the original PyMuPDF-based parser was invoked on the source PDFs; the generated CSV rows and per-PDF parser logs were compared as exact full-record multisets against the original pre-S4/cadence ZIP outputs. The current isolated runtime uses Python 3.13.5, pandas 2.2.3, PyMuPDF 1.26.7 and pdfplumber 0.11.9. No original private files were pushed. The parser and input SHA information, passing and failing comparisons, and checked counts are recorded in the local consolidated execution report, with a sanitized GitHub validation record alongside this document.

## 5. Replayed-PDF to historical canonical game selector linkage (November 10 follow-up)

A further source-linked audit matched the **actual PDF-reparsed outputs and parser logs** to the archived `nba_canonical_snapshot_selector_v1.zip` full and harmonized selectors. Each 2021–22, 2022–23 and 2023–24 season has 1,230 distinct regular-season games in each of two panels (total **7,380 selected game/report records**). Every selected `(PDF basename, published_timestamp_utc)` has an `ok` parser log, and the calculated `tip_timestamp_utc - published_timestamp_utc` agrees with the selector's `minutes_before_tip` and is strictly positive. There were zero duplicate game IDs and zero unexplained missing matchup-to-reparsed-PDF links.

| Season | Full selector PDF logs matched | Harmonized PDF logs matched | Reported matchup in PDF rows | Explicit clean-team exception |
|---|---:|---:|---:|---|
| 2021–22 | 1,230 / 1,230 | 1,230 / 1,230 | 1,230 in each | none |
| 2022–23 | 1,230 / 1,230 | 1,230 / 1,230 | 1,230 in each | none |
| 2023–24 | 1,230 / 1,230 | 1,230 / 1,230 | 1,229 in each | one valid archived inference |

The single expected exception is **FD2023_5, BOS@NYK (October 25, 2023)**: the selected 5PM/6PM PDFs contain no matchup rows, and the original frozen selector explicitly records `inferred_clean_teams=2`, `listed_teams=0`, and `both_teams_usable=True`. This is an *explicit historical clean-team inference*, not a missing PDF or failed source join. No other selected matchup is missing.

[Machine-readable 7,380-link check](../validation/level_c_injury_pdf_real_2026-11-10/canonical_snapshot_selector_links.json). **Scope limitation:** this checks the existing historical selector **against independent source PDF reparses**; it does not independently regenerate the selector's choice of latest eligible report, player-ID matches, report-status propagation or final panel. That full upstream reconstruction remains in Issue #5.

## 6. Deterministic verification tools added after the first real-source audit

The underlying private PDF reparses and reference data **have not been rerun** by this later code-only improvement. The previous 7,380-link result remains recorded as source-run evidence, while the GitHub branch now has a fail-closed, standalone implementation:

- [`audit_replayed_snapshot_links.py`](../scripts/data_rebuild/audit_replayed_snapshot_links.py): read-only verifier of a recovered historical selector ZIP against reparsed CSV and parser-log files for each of the three 2021–24 seasons. It requires 1,230 distinct game IDs in each full/harmonized panel, one unambiguous ZIP member per panel, a successful parser log for each selected PDF and timestamp, matching matchup rows, strictly pre-tip timestamps, and identical game sets between the two panels. Missing-matchup clean-team inference is accepted **only** for the explicitly documented 2023–24 `FD2023_5` record with both teams recorded clean; all other missing matchups fail.
- [`audit_2020_reason_layout_drift.py`](../scripts/data_rebuild/audit_2020_reason_layout_drift.py): read-only order-independent record-multiset comparator for archived versus candidate 2020–21 parser outputs. It refuses differences in **any non-`reason` field**, counts free-text-only disagreements grouped by source PDF, and outputs **sanitized aggregate counts** without exposing player identifiers or medical-reason values. It never substitutes, normalizes, or copies candidate reason strings into the frozen dataset. A non-exact run exits nonzero, including the earlier 93-record diagnostic.
- [Synthetic failure tests for the selector validator](../tests/test_replayed_snapshot_links.py) and [for 2020 reason drift](../tests/test_2020_reason_layout_drift.py) are registered with GitHub Actions. **These synthetic tests cannot replace running the real archive inputs against the new CLI.**

To run the two actual acceptance checks from a local private scratch directory, after producing historical reparsed CSV and logs with the original season-specific parser:

```bash
python scripts/data_rebuild/audit_replayed_snapshot_links.py \
  --selector-zip /private/nba_canonical_snapshot_selector_v1.zip \
  --season 2023-24 \
  --reparsed-rows /private/2023-24/reparsed_rows.csv \
  --reparsed-log /private/2023-24/reparsed_log.csv \
  --output data_rebuild/output/2023_24_selector_link_check.json

python scripts/data_rebuild/audit_2020_reason_layout_drift.py \
  --reference /private/2020-21/archived_rows.csv \
  --candidate /private/2020-21/reparsed_rows.csv \
  --output data_rebuild/output/2020_21_reason_drift_diagnostic.json
```

The paths above are **examples**, not claims those files were materialized in the new session. The second command intentionally returns nonzero until all 2020–21 archived `reason` fields reproduce exactly. Preserve the original reference and source bytes throughout.

## 7. Later independent local repeat and exact real-header compatibility gate

A new November 10 continuation opened the **actual archived selector ZIP** and directly inspected the original CSV headers, discovering that the 2022–23 canonical selectors lack the `listed_teams` column available in 2021–22 and 2023–24. The first version of `audit_replayed_snapshot_links.py` would therefore have rejected legitimate 2022–23 input. The verifier now requires `listed_teams` only for the documented 2023–24 explicit clean-inference rule. This behavior is pinned by an additional regression test using the real legacy header layout.

For independent archived-intermediate sanity checks, the original `audit_2022_23_pre_s4_outputs.zip`, `audit_2023_24_pre_s4_outputs.zip`, `audit_2021_22_cadence_outputs.zip`, and `nba_canonical_snapshot_selector_v1.zip` files were opened in the current local environment. Both full and harmonized 2022–23 and 2023–24 selectors matched 1,230/1,230 pre-tip game/report entries per panel, without missing parser-log and matchup links, or timestamp/age disagreements. The two 2023–24 selectors each contain the already-documented `FD2023_5` clean-team exception. The 2021–22 harmonized selector also matched all 1,230 game/report links against the original 696-PDF archived harmonized logs/rows. This check uses **original archived parsed CSVs** and is independent of the earlier reported full PDF reparse—it does **not** add a new raw-PDF-to-CSV pass.

The 2020–21 **actual original source PDF reparse was also repeated** using the unchanged historical `nba_injury_pdf_layout_parser.py` (original script SHA-256 `77fb85d6e0634c01d0ddb0739294c0ed044671b5b93b0affbbf9ec943a7ef6ee`) with the explicitly labeled diagnostic `pdfplumber==0.11.9, x_density=5.0` text extraction. For execution-time safety the 617 PDFs were processed in six isolated batches (100/100/100/100/100/117). **41,780 rows reproduced, all 617 parser logs match, zero parser exceptions, no differences in any field other than `reason`.** The same **93 reason discrepancies from 44 PDFs** persist; this is a confirmed **failed exact replay**, not a resolved issue. A density sweep on an affected report did not find any setting that yielded exact full-record equality. [Sanitized independent repeated-source evidence](../validation/level_c_injury_pdf_real_2026-11-10/independent_2020_reason_density_diagnostic.json).

**CI acceptance of the new tool code:** [GitHub Actions run 42835911782](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42835911782) completed with 11/11 successful jobs, including synthetic positive/negative tests for the selector and 2020 reason-drift validators. These green code tests are distinct from, and not a substitute for, real private-input acceptance. The 2020 reason-text mismatch and downstream independent selector reconstruction remain open.


## 8. Independently recovered 2024–26 originals and executed complete reference stage replays

A follow-up local run **opened the actual private** `audit_2024_25_upload.zip`, `audit_2025_26_upload.zip`, and `audit_2025_26_targeted_upload.zip` source archives. It first checked that the two original metadata blobs still have immutable git identities `ca5188baf047e8154003b0daad1cb319af1ff3d4` and `a3273b97035c63f9e34b68bac0dddf863588adc4`, then independently streamed complete ZIP SHA-256, all member PDF SHA-256, and full ZIP CRC without uploading or altering the originals.

| Original archive | Exact pinned ZIP SHA-256 | Indexed saved PDF SHA matches | ZIP CRC | Missing/extra PDFs |
|---|---|---:|---|---|
| 2024–25, `audit_2024_25_upload.zip` | `a10cc660a45f0c3fa6ac279d540a29eae04804dc03eb16a86a1d0c6a7f363e3b` | 5,566 / 5,566 | Pass | 0 / 0 |
| 2025–26 initial, `audit_2025_26_upload.zip` | `a0cdcb4b9e594a1b1fb63489aa43087f6c13f5b34ab3661b596c2941089c9f70` | 1,497 / 1,497 | Pass | 0 / 0 |
| 2025–26 targeted, `audit_2025_26_targeted_upload.zip` | `8a9c08e3aa92f5400cc866201051653e13b89cc6a56b5aae7deb2ad9e0f718ea` | 3,526 / 3,526 | Pass | 0 / 0 |

**All seven** recovered original injury-report ZIPs now have **27,755 of 27,755 saved PDF hashes independently checked** against the original provenance. Do not confuse this with 27,755 unique league-report timestamps or complete hourly reporting coverage. The 2024–25 archive has 290 missing candidate requests, and the initial 2025–26 archive has 4,167 missing candidate requests. The 2025–26 targeted collection is an additional restricted sampling design.

### 2024–25: actual regular-season original PDF → full archived CSV reparse — EXACT

Using the original unchanged `parser_2023plus.py` recovered from the private `nba_player_game_at_risk_core_v1.zip` (SHA-256 `197c29d46dfea221c381664b96a05453737df55d7b8dd5d5e6f44e49b69e0e06`), the run reparsed **all 4,078 verified original regular-season PDFs** recorded in `audit_2024_25_pre_s4_outputs_corrected.zip`'s original manifest. It independently compared **complete 15-field CSV record multisets grouped by source PDF**, not just summary counts.

- **418,059/418,059** original reference rows independently reproduced.
- Zero missing or extra rows, zero differing per-PDF complete-record multisets.
- **4,078/4,078** reference parser logs (pages, extracted rows, status and warnings) reproduced exactly.
- Original reference ZIP and complete frozen data were not modified.

### 2025–26: original selected PDFs → frozen core row and parser-log reparse — EXACT

The run opened the frozen core `canonical_game_snapshot_map.csv`, selected-report CSV and selected-snapshot parser log inside `nba_player_game_at_risk_core_v1.zip`. It determined which saved PDFs the **1,230** regular-season games had actually selected, independently staged the **729 distinct selected original PDFs** from the two private 2025–26 archives, and ran the same original unchanged parser. Each source PDF was parsed once and the chosen matchups were filtered to the **archived selection set** before comparing full original 15-field row tuples.

- **13,968/13,968** archived selected player/report records reconstructed exactly.
- **729/729** selected PDF parser logs reproduced (counts, pages, status and warnings).
- Zero mismatches, missing reference files, or duplicated source basenames across the two original archives.

This **does not independently generate the 2025–26 selected-report choices**, nor does it verify all 5,023 available 2025–26 PDF parse outputs against a full archived hourly reference; the current acceptance is restricted to the 729 reports selected by the frozen historical model input. Full end-to-end star/awards/Cup/TV and model reassembly remain separate.

### 2020–21: quantify remaining reason-only differences in game-selected sources

Using a fresh 617-PDF `x_density=5.0` diagnostic reparse and the **actual** original `nba_canonical_snapshot_selector_v1.zip` full and harmonized 2020–21 game map, all 93 existing `reason` field differences were joined by exact `(source PDF basename, publication timestamp, matchup)`. The source corpus has 93 differing player rows in 44 PDFs, but **only 25 of these record differences are in selected game/report matchups, affecting 12 of 1,080 games** in either full or harmonized panel. Both panels give the same numbers: 25 records / 12 games. Among selected discrepant rows, statuses are **21 Out, 3 Questionable, 1 Available**. Every non-reason field, including the injury status, matches the archived CSV.

This bounds potential reason-taxonomy impact; it **does not** validate the 25 free-text reasons or imply that the main manuscript estimates were rerun. Do **not** silently adopt the diagnostic strings in a frozen release.

[Sanitized 2024–26 machine-readable evidence](../validation/level_c_injury_pdf_real_2026-11-10/extended_2024_26_source_and_replay.json). The actual source ZIPs, PDFs, and per-player reasons remain private and uncommitted. PR #4 stays draft until scientific review.

## 9. Original canonical selection algorithm: 2020–21 and 2024–25 exact re-execution

The archived `nba_canonical_snapshot_selector_v1.zip` includes its actual historical `build_canonical_snapshot_selector_v1.py`. The original `build_season` function was extracted and re-executed **without changing the selector algorithm** with original archived schedules, verified PDF report manifests, and historical parsed row inputs. For 2020–21, the S4 normalized schedule's lowercase `away_team/home_team/location/result` fields were mapped to the capitalized equivalent schedule headers present in the frozen canonical output; this is a source-schedule schema harmonization, not a change to the pre-tip rule. For 2024–25, the original schedule column names were already aligned.

| Season | Rerun of original full selector | Rerun of original harmonized selector | Result |
|---|---:|---:|---|
| 2020–21 | **1,080 / 1,080** exact game records | **1,080 / 1,080** exact game records | All compared fields match |
| 2024–25 | **1,230 / 1,230** exact game records | **1,230 / 1,230** exact game records | All compared fields match |
| **Across panel records** | | **4,620 / 4,620** | **PASS** |

The original code's `pd.merge_asof(..., direction="backward", allow_exact_matches=False)` selection was rerun rather than merely checking whether previously selected PDFs existed. Every field in the frozen canonical game selection output compared equal, with a `1e-9` numeric tolerance for floating-point serialization only. The 2024–25 run uses **418,059 rows independently reparsed from original PDFs**, as established in the preceding section. For 2020–21, selection was built from **archived parsed rows** because the current `pdfplumber` environment still cannot reproduce all reason strings; this does not affect the selection algorithm's team-status inputs, which were separately shown equal across the compatibility reparse.

The initial local comparison code reported spurious failures from schedule label aliases and a bug comparing a pandas Index directly with a whole DataFrame. Both were corrected in the **validation harness**, not in the original selector. The corrected full-column comparison passed all four panels. This is reproduction of the **original selector implementation**, not a second independently designed selector implementation, and not a full downstream player-game/award/model reconstruction.

[Sanitized machine-readable original-selector replay](../validation/level_c_injury_pdf_real_2026-11-10/original_canonical_selector_2020_2024_replay.json). Both original ZIP packages remain private, and the frozen released data were not changed.

## 10. Durable replay command for 2024–26 private original sources

The actual 2024–25 and selected 2025–26 source-reparse results above were executed directly against the private original ZIPs in the model's isolated Python environment. For repeatability beyond that temporary environment, the PR now includes [replay_recent_historical_injury_pdfs.py](../scripts/data_rebuild/replay_recent_historical_injury_pdfs.py) and [strict synthetic input tests](../tests/test_recent_injury_pdf_replays.py).

This replay CLI checks the full original ZIP SHA-256 and every indexed original PDF SHA-256 against the **pinned public source metadata**, validates all ZIP CRCs, refuses to import a parser unless its original source-code SHA-256 matches, opens only needed original PDFs in a temporary private scratch directory, and compares complete source-PDF record multisets and parser logs against the frozen reference. It outputs sanitized aggregate JSON with no player names or reasons. The command **does not independently reconstruct the report selector**.

From an active checkout of PR #4, with all original source ZIPs saved privately in one directory and an original pinned public metadata checkout:

\`\`\`bash
# 2024–25: all 4,078 original regular-season PDF parses (418,059 rows)
python scripts/data_rebuild/replay_recent_historical_injury_pdfs.py \
  --mode 2024-25 \
  --archive-dir /private/original_injury_zips \
  --metadata-dir /private/nba_pinned_source/provenance/historical_sources \
  --core-zip /private/nba_player_game_at_risk_core_v1.zip \
  --reference-2024-zip /private/audit_2024_25_pre_s4_outputs_corrected.zip \
  --workers 4 \
  --output data_rebuild/output/2024_25_original_pdf_replay.json

# 2025–26: all 729 actually selected originals (13,968 model-input rows)
python scripts/data_rebuild/replay_recent_historical_injury_pdfs.py \
  --mode 2025-26 \
  --archive-dir /private/original_injury_zips \
  --metadata-dir /private/nba_pinned_source/provenance/historical_sources \
  --core-zip /private/nba_player_game_at_risk_core_v1.zip \
  --workers 4 \
  --output data_rebuild/output/2025_26_selected_original_pdf_replay.json
\`\`\`

Both commands intentionally fail on source/row/log mismatch and refuse to overwrite any existing output JSON. Install the project's pinned historical builder/PyMuPDF dependencies first. Source ZIPs, original parser ZIPs and individual PDFs must **not** be committed to GitHub.

**Evidence boundary:** the results above were already verified using separate direct temporary Python replay scripts; until this packaged CLI is itself executed against the private originals and accepted, do not label the new CLI specifically as a green private-input run. Green CI synthetic tests validate failure behavior, not access to private ZIPs. The report and the original frozen artifacts are unchanged.

## 9. Executed *original algorithm* replay for 2020–21 and 2024–25 canonical selectors

A separate November 10 continuation **opened the authentic private historical input ZIPs** and executed the exact `build_season` function, not just the frozen selector outputs. The original `build_canonical_snapshot_selector_v1.py` was extracted from `nba_canonical_snapshot_selector_v1.zip` and SHA-256-checked as `3e2c3f975a9d6f0828655cfade2a11a8418c0a3b3af3789a307949780666031f`. Only its original imports and function definitions were run to avoid its obsolete hard-coded input paths. Input schedules, the indexed source manifest and **the original historical parsed injury-report rows** came from the authenticated private archived packages, not the canonical output being compared.

Four *independent* original-algorithm invocations were made: full and harmonized 1PM/5PM/8PM for each of 2020–21 and 2024–25. The `merge_asof` selection uses the original strict-before-tip rule, and the original function independently recalculates listed players, team submission classes, inferred-clean teams, missing statuses, and report timestamps.

| Season | Canonical panel | Games independently rebuilt | Team-game statuses independently rebuilt | Game fields compared | Team fields compared | Exact frozen match |
|---|---|---:|---:|---:|---:|---|
| 2020–21 | full | 1,080 | 2,160 | 23/23 | 21/21 | **Yes** |
| 2020–21 | harmonized | 1,080 | 2,160 | 23/23 | 21/21 | **Yes** |
| 2024–25 | full | 1,230 | 2,460 | 23/23 | 21/21 | **Yes** |
| 2024–25 | harmonized | 1,230 | 2,460 | 23/23 | 21/21 | **Yes** |
| **Total** | four executed selections | **4,620** | **9,240** | all | all | **Zero field differences** |

All **13** published canonical season metrics matched in each of the four panels (52/52 values). Key summary statistics independently recovered include 2020–21 usable team-games **2,109/2,160**, with 51 explicit not-yet-submitted statuses and 41 inferred-clean team-games; for 2024–25, full selector usable **2,442/2,460** (18 not submitted) and harmonized **2,444/2,460** (16 not submitted).

A harmless historical schedule header distinction was resolved *after* running the original function: the recovered 2020–21 normalized schedule contains `away_team`, `home_team`, `location` and `result`, whereas the frozen selector CSV uses `Away Team`, `Home Team`, `Location` and `Result`. Exactly those four output metadata columns were renamed and their values compared, producing **23/23 complete game-field matches**, without changing source values or report selection logic.

This is stronger than source-to-existing-selector linkage. The original selection **algorithm itself reproduces all game choices and all team status classifications** in both corrected seasons. It does not establish exact reproduction of all 2020–21 PDF-derived `reason` strings, since its input for that season was the **archived original corrected parsed CSV** rather than the currently failing diagnostic parser output. It does not independently rebuild the canonical selection code for seasons that the historic package simply copied through, nor does it rebuild the 2025–26 selection-rule motivation.

**Reproduction command**, with all original ZIPs held privately under `/private/original_archives/` (no extraction or private-source upload required):

```bash
python3 scripts/data_rebuild/verify_canonical_selector_replay.py \
  --archive-dir /private/original_archives \
  --output data_rebuild/output/canonical_original_selector_replay.json
```

The verifier rejects any changed original selector source SHA-256, missing ZIP members, missing or duplicate game/team IDs, unexpected row counts, field mismatches, or changed model-relevant metrics. Its ten synthetic positive/negative checks are included in GitHub CI, **which does not have access to the private source ZIPs**. Private-output acceptance was completed locally; CI only tests the checking tool.

The [sanitized machine-readable execution evidence](../validation/level_c_injury_pdf_real_2026-11-10/independent_canonical_selector_algorithm_replay.json) records original inputs' ZIP SHA-256 values, field counts, canonical metrics and scientific limitations. **No original archives, private source PDFs, frozen panels or manuscript were modified or pushed.** Keep PR #4 as a draft pending remaining source gates.
