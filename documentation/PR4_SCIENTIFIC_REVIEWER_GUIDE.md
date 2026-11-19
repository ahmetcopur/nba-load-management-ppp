# PR #4: scientific dependency reviewer guide

Start with **SCI-001**, not the long commit chronology. This review is AI-assisted; it does not constitute external human PR approval. Keep the PR draft.

| Priority | Component | First inspection / acceptance question |
|---|---|---|
| 1 | Star classification | [Original report-only branch](../scripts/executed/06_cadence_harmonized_identification/build_harmonized_panel_and_models.py#L227), [failing semantic evidence](../validation/scientific_integrity_audit_2026-11-15/star_definition_check.json). Does every current-season promotion require actual selection? |
| 2 | Scientific consequence | [Independent refits](../validation/scientific_integrity_audit_2026-11-15/independent_numeric_checks.json), [isolated star-rule variant](../validation/scientific_integrity_audit_2026-11-15/star_rule_sensitivity.json). Distinguish correct estimation of legacy values from semantic correctness. |
| 3 | Risk and history | Original cadence builder lines 257–279; `rebuild_missing_october_paper_statistics.py` for duration/next-game censoring. Examine current versus previous report availability, trade/reentry reset, coach DNPs and tied physical-game workload windows. |
| 4 | Injury-source selection | `rebuild_six_season_october_sources.py`, per-season historical parsers/selectors and handoffs. Check complete candidates, submitted placeholders, timestamp semantics, 18 actual opens, and allowed chronology changes. Do not infer source consumption solely from a standalone hash match. |
| 5 | Identity / chronology | `verify_player_identity_replay.py`, `rebuild_august_core_from_source_archives.py`, `fixture_date_chronology_sensitivity.py`. Inspect versioned aliases, the two Toronto fixtures and old date-bearing key strings versus actual dates. |
| 6 | Regression | [Executed fast model](../scripts/executed/06_cadence_harmonized_identification/run_cadence_models_fast.py). Review all interactions, player/team-season effects, missing-control selection, covariance/reference distribution and the redundant games/dist65 pair. |
| 7 | Ingestion / immutable sources | `final_source_sha256.json`, `restore_historical_layout.py`, `verify_boxscore_cache.py`. Check whole-archive/member identity, private destinations, guarded extraction, no network repair, source immutability and no silent raw-JSON fallback. |
| 8 | Final acceptance | `reproduce_final_datasets.py`, stage logs, final manifests. Historical decoded hashes establish computational replay, not eligibility semantics or causal identification. No fresh combined PDF+JSON success is established. |
| 9 | Taxonomy / co-interventions | Archived star/calendar source, reviewed taxonomy bridge, Cup and announced-TV verifiers. Separate human decisions and acquisition observations from unconnected computational leaves. Human κ=.835 archive is distinct from Claude κ=1. |
| 10 | Publication / manuscript | [Publication review](DATA_PUBLICATION_REVIEW_2026-11-15.md), [current-PDF discrepancy register](MANUSCRIPT_AUDIT_2026-11-15.md). Review bulk panels and PRIVATE-named members, not only four diagnostics. |

## Reexecute the inexpensive semantic gate first

Extract `player_season_star_status_calendar.csv` from the SHA-pinned original star ZIP into a private location. Use the accepted corrected cadence file:

```bash
python scripts/data_rebuild/audit_star_status_against_calendar.py \
  --panel /private/final/october_cadence_player_games.csv.gz \
  --calendar /private/star_calendar.csv \
  --output /private/review/star_semantics_001.json
```

**Expected on the currently accepted panel: exit 1, 49 mismatches, 12 risk/onset rows.** This is a successful detection of a scientific failure, not a source-rebuild crash. The report has no row-level identifiers, and the input file is never edited.

## Reexecute the independent numerical checks

With `requirements-builder-lock.txt` in Python 3.12, use the original star ZIP and the private `NBA_Coding_Agreement.zip`:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python \
  validation/scientific_integrity_audit_2026-11-15/reproduce_numeric_audit.py \
  --panel /private/final/october_cadence_player_games.csv.gz \
  --star-archive /private/nba_player_game_at_risk_star_v1.zip \
  --coding-archive /private/NBA_Coding_Agreement.zip \
  --output /private/review/independent_models_001.json
```

Repeat with a **new** report path and `--apply-declared-star-rule` for the isolated RAM-copy sensitivity. It writes no replacement panel and never updates legacy targets. The same public program was executed for all four original and all four variant specifications. Its independent projection stopping rule differs from the historical executable; compare numerical statistical fields, not iteration/runtime byte identity. This diagnostic program does not grant release acceptance.

The [findings register](../validation/scientific_integrity_audit_2026-11-15/findings.json) states which checks are actual executions, inherited-evidence checks, remaining assumptions and pending new-builder acceptance. Do not start an expensive full raw-source reconstruction until the small downstream scientific correction and intended release scope have been agreed.
