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
