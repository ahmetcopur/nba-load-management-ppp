# NBA data reconstruction: methodological and engineering audit (8 November 2026)

## Bottom line

The existing research repository reproduces many *analyses* from archived
analysis-ready data, but is **not yet a complete raw-source-to-final-data
reconstruction**. The historical cadence-panel builder starts with an already
assembled canonical roster/award/schedule/TV/covariate panel, frozen checkpoint
selection maps, and earlier-season parsed injury-report CSVs. Replaying that
builder is valuable, but calling it an independent raw-data rebuild would be
incorrect.

No original frozen datasets, outcome definitions or manuscript coefficients
are changed by this audit.

## Evidence levels

| Layer | Input | Current status | What passing means |
| --- | --- | --- | --- |
| Original source inventory | 37,342 injury-report URL checks; 27,755 archived PDFs (metadata); 7,230 game/boxscore IDs | Metadata is published in the shared repository, raw PDF ZIPs occur in historical file library; raw boxscore JSON cache is not published | Source lineage and provenance checks, **not** independent source parsing |
| Canonical upstream panel | Previously combined roster, star, fixture, TV, workload, game covariates | Frozen analysis-ready CSV supplied | **Cannot** independently regenerate these source-derived fields yet |
| Injury-report parsing/selection | Earlier-season parsed CSVs and fixed checkpoint mapping; original 2025 PDFs/parser | Archived processing files located in file library, ZIP member contents still require on-disk inspection | At best a historical intermediate-data replay |
| Harmonized cadence panel | Original builder + restored inputs | Runner and QA implemented, *full execution not yet independently verified* | Must match all published keys, variables and frozen counts |
| Statistical estimates | Panel, executed regression scripts | Rerun scripts in repository | Can reproduce conditional numerical estimates, subject to environment/tolerance |
| Scientific inference | Observational comparison around 2023 policy/rule changes | Multiple simultaneous changes | **Does not** identify PPP's isolated causal effect |

## Specific bugs found and addressed in this branch

1. **Unverified hardcoded ZIP internal paths.** Restoration now preflights every
   required source member; exact paths are preferred and only a *unique* basename
   match is accepted. Ambiguities and missing required members produce errors.
   The original ZIPs still need on-disk inspection to confirm actual matches.
2. **Incorrect selector completeness criterion.** Previous code required an
   arbitrary count of 15 CSVs; the builder needs six season selected-snapshot
   files and four season team-status files. Those **specific** ten members are
   now required.
3. **Incorrect clean-checkout `--check-only` behavior.** It used to check for
   the 2025 parsed output before running the parser. It now verifies restored
   archives and 2025 source PDF availability without requiring that output.
4. **Silent historical PDF parse failures.** The archived parser catches and
   records per-file errors without necessarily failing its process. The new
   wrapper fails unless every selected file has an `ok` parse-log row and
   the parsed CSV exists with necessary columns.
5. **Unnecessary mandatory alias file.** The original builder uses
   `player_alias_table.csv` *only if present*; it is no longer required by
   the preflight. Any identity-join failure remains fatal inside the builder.
6. **Insufficient panel validation.** Rebuilt output must pass independent
   player-team-game ID uniqueness, valid onset/risk boolean semantics, all six
   seasons, 248,778 rows, 180,664 risk observations, 12,731 onsets, *then*
   an all-column comparison against frozen reference.
7. **Misleading CI interpretation.** CI's frozen-data self-comparison is now
   labeled a comparator smoke test; no CI check claims to have processed the
   private original raw archives.

## Version and provenance safeguards

- GitHub Actions checks a **pinned commit**
  `0bd713d97e8d519df5700ef473da34aba4495223` in
  `OEKundakcioglu/nba-ppp-star-availability` to avoid silently changing the
  cross-repository report/boxscore source maps.
- Original executed scripts are preserved byte-for-byte; replay wrappers alter
  only their hard-coded location paths in temporary copies.
- Input restoration is non-destructive, SHA-256 logs each extracted archive
  member, and refuses overwrites with different bytes.
- Generated files are written under the Git-ignored `data_rebuild/output/`.
- The 21 December 2025 selected-report timestamp exceptions remain unresolved
  for an exact-clock recomputation. Preserving the historical selection is
  *not* proof it is timestamp-correct.

## Acceptance criteria before claiming a complete rebuild

1. Inspect actual recovered ZIP member names, SHA-256 hashes and schemas;
   require the ZIP restore preflight to pass against all 13 archival input ZIPs.
2. Re-run all selected 2025 injury PDFs and verify every parse-log record.
3. Re-run the historical cadence builder, verify its intermediate QA tables,
   and compare the reconstructed player-team-game panel **against** (not to
   itself) the released CSV.
4. Independently reconstruct the canonical panel and earlier seasons' injury
   parser/selection outputs from documented raw PDFs, official boxscore JSON,
   TV announcements, fixture inputs, recognition sources and covariates.
5. Perform sensitivity analysis for the 21 selected timestamp exceptions;
   do not silently substitute the corrected dataset for the historical freeze.
6. Re-run models on the independently regenerated panel and compare published
   coefficients, risk-set definitions and uncertainty estimates.

Only steps 1–3 would establish **historical intermediate-data reproducibility**.
Steps 4–6 are needed for a stronger end-to-end, scientifically auditable
raw-source-to-paper replication.

## Run

From repository root with the 13 named archives stored locally (not committed):

```bash
python3 scripts/data_rebuild/restore_historical_layout.py \
  --archive-dir /path/to/nba_archives \
  --historical-root data_rebuild/output/nba_continue \
  --preflight

python3 scripts/data_rebuild/rebuild_from_archives.py \
  --archive-dir /path/to/nba_archives \
  --historical-root data_rebuild/output/nba_continue
```

If a ZIP member is missing or ambiguous, **stop** and inspect which historical
release produced the intended file. Do not substitute a similarly named CSV
without checking its season, schema, methods and provenance.
