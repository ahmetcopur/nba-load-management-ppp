# Controlled 2025–26 team-status experiment

This isolates the scientific effect of the two unresolved legacy team-status fields. It does not relax `generate_2025_selector_inputs.py`'s historical-artifact acceptance: strict generation still fails on the documented 1,598-row discrepancies. Diagnostic frames are available only with explicit audit-only execution and are never represented as accepted historical selector tables.

The runner restores the other seasons and the reviewed base, crosswalk and scheduling inputs from SHA-256-pinned original archives. Both conditions consume the same freshly reconstructed 2025 game selector and the same freshly parsed rows from the complete 5,023 saved-PDF candidate set. The control retains the historical 2025 team table; the experimental condition consumes the complete source-derived team table. Before execution, the runner requires identical file inventories and hashes except for that table, unchanged schema/keys/row order, exactly 1,598 differing rows, and differences confined to `team_final_status` and `inferred_no_listed_players`. In particular, `usable_submitted_status` must remain identical.

The original October scientific script is SHA-256-pinned and unchanged. The existing path-redirection wrapper additionally traces actual opens and checks before/after hashes of the three 2025 files. The original script's known post-panel `norm.sf` failure is recorded explicitly; an unrelated crash fails acceptance. The independent original fast model program executes all four corrected specifications separately.

All eight frozen outputs receive independent decoded SHA-256 and complete string-cell comparisons. Player-game comparisons use unique `player_team_game_id` keys. The only permitted differing frozen output is the team-status table, with precisely the two documented fields. The accepted frozen panel hash is required. The existing Toronto chronology correction then actually executes for both conditions, including actual-open tracing of the unchanged generated 2025 inputs. Both corrected panels must match the accepted hash. Every scientific field of the four model output rows must match exactly. Model CSV hashes remain independently reported: the original fast model program includes `seconds=time.time()-t`, so execution duration is explicitly excluded from scientific comparison. No other model column is excluded or compared with relaxed numerical tolerances.

## Command

Run in Linux amd64 with Python 3.12 and `requirements-builder-lock.txt`. Keep sources and outputs outside Git. Alongside the historical restoration archives, supply `nba_game_covariates_v1.zip` and the original `audit_2025_26_s4_join_results.zip`, pinned to `6ad1013984693abc852b4a8cf2fcf3aad6dc1a9eb555ef35d121f95ca4c9989c`.

Reuse an existing complete candidate directory only after its acceptance report and every source-file hash pass validation. Otherwise generate it with the existing original parser:

```bash
python -m scripts.data_rebuild.rebuild_2025_full_candidates --archive-dir /private/originals --output-dir /private/2025-candidates
python -m scripts.data_rebuild.experiment_2025_team_metadata --archive-dir /private/originals --fresh-source-dir /private/2025-candidates --output-root /private/2025-team-experiment
```

The private output contains input fingerprints, original archive/code identities, per-stage execution checkpoints and logs, frozen comparisons, both corrected panels and models, actual-open evidence and, **only after all gates pass**, `experiment_acceptance.json`. No final panel is copied from a prior run. Stage checkpoints hash every output file. Explicit `--resume` revalidates sources, code and prepared conditions and rejects changed checkpoints or incomplete stage output directories. One narrowly SHA-pinned compatibility case allows re-evaluation of all four completed stages from commit `70ebe218`: its first comparator rejected their different execution durations. Original execution identity and current evaluation identity are both retained, every stage checksum is revalidated, and no scientific script or input identity may change. It does not silently overwrite partial scientific results.

## Static dependency trace

In the original builder `scripts/executed/06_cadence_harmonized_identification/build_harmonized_panel_and_models.py`, lines 74–89 read, normalize, join by stable game/team identities, and export the team metadata without filtering observations by either disputed value. Lines 248–252 discard inherited base metadata, join the reconstructed team status, and derive outcome observability solely from `usable_submitted_status`. Lines 257–280 compute absence, histories and onset risk without either disputed field. The bounded `outcols` at lines 287–288 excludes both disputed fields. Season QA, snapshot comparison and regressions use this bounded scientific data and unaffected selectors. The correction changes only documented 2021–22 fixture controls/report links and reruns that same original builder; the separate fast model script reads the bounded panel. This trace is a hypothesis about propagation, not experimental evidence by itself.

## Acceptance scope

Even a passing controlled experiment proves neither recovered original S4 team-join logic nor cumulative six-season reconstruction. Original publication/acquisition metadata and human-reviewed inputs remain declared historical inputs. The five prior targeted raw-season runs are separate proofs. Cumulative canonical integration and an authentic new combined final-dataset run remain separate gates.

## Authentic November 15 result

**Outcome A: metadata-only for the tested scientific outputs.** The original builder actually opened all three intended 2025 inputs in both frozen runs and both corrected runs. Pre/post hashes, source identities and stage-output checksums passed. Both conditions shared freshly parsed selected rows from the complete 599,225-row source, SHA-256 `38d5ba587ac1109585014190841d8d7a495c8ae3fb87871e351342c6ada375ac`. Other seasons, reviewed base, crosswalk and controls were identical pinned historical inputs.

Seven of eight frozen outputs are decoded-byte identical between conditions. Only `harmonized_team_game_report_status.csv` differs: identical schema, row order, all 14,460 keys, zero missing/extra keys; exactly 1,598 rows/3,196 cells differ in `team_final_status` and `inferred_no_listed_players`. `usable_submitted_status` and every other field match. Both scientific panels have 248,778 rows, 7,230 games, 180,664 at-risk observations and 12,731 frozen onsets, and SHA-256 `3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac`.

Both Toronto corrections actually executed. Their complete 45-column panels are decoded-byte identical and independently match `2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67`, with 248,778 rows, 7,230 games, 180,664 at-risk observations and 12,729 onsets. This verifies every exported designation/reason, report assignment, roster/history, control, TV, star and Cup field through full-content equality.

| Definition | Controls | N | Estimate (pp) | p |
|---|---|---:|---:|---:|
| National-partner (`legacy_primary`) | full | 180,530 | 2.6742317292365767 | .0426339657858416 |
| Linear-only (`harmonized_linear`) | full | 180,530 | 1.2823694527266445 | .3308675408175164 |
| National-partner (`legacy_primary`) | none | 180,664 | 2.676885495644326 | .0435317747821202 |
| Linear-only (`harmonized_linear`) | none | 180,664 | 1.2948513321879846 | .3291224141374449 |

Every model field other than elapsed `seconds` is exactly equal as a CSV string, including N, coefficients, SEs, confidence limits, p values and absorption iteration counts. The control model CSV SHA-256 is `cc21087bc96b20aaebac46341193871639b39b4bf93fb900d0531063fe2b4bc8`; experimental is `378fca591bebf69472888f2142e872fbe805fe6776c48cba3d471f4de6399889`. Their four differing cells are execution durations, not estimates. These unequal hashes are retained rather than called exact artifact equality.

The first evaluator rejected these differing durations after all four scientific stages completed. Their checksummed outputs were retained and revalidated by the narrowly SHA-pinned revised evaluator. The scientific programs, inputs and panel checksums were unchanged; no models were rerun or coefficients rounded to force acceptance. [Sanitized execution evidence](../validation/2025_team_metadata_experiment_2026-11-15/experiment_acceptance.json) preserves original execution and revised evaluation identities, all source/output hashes, actual-open records and commands. [Static trace](../validation/2025_team_metadata_experiment_2026-11-15/static_dependency_trace.json) is explicitly distinct from execution evidence.

Actual command, followed by checksum-validated evaluation of the completed checkpoints:

```bash
python -m scripts.data_rebuild.experiment_2025_team_metadata --archive-dir /tmp/nba-metadata-archives --fresh-source-dir /tmp/nba-metadata-candidates --output-root /tmp/nba-team-metadata-2026-11-15-001
python -m scripts.data_rebuild.experiment_2025_team_metadata --archive-dir /tmp/nba-metadata-archives --fresh-source-dir /tmp/nba-metadata-candidates --output-root /tmp/nba-team-metadata-2026-11-15-001 --resume
```

The November 14 temporary attempt was lost before complete acceptance evidence was saved. This result comes from the November 15 execution. It neither recovers the original S4 join nor constitutes cumulative six-season execution, a new August reconstruction or a new combined three-dataset acceptance. Canonical connection of the later raw-season stages and an explicit metadata-artifact scope remain necessary before the cumulative run.
