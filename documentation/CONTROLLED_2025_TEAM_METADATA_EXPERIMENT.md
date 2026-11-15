# Controlled 2025–26 team-status experiment

This isolates the scientific effect of the two unresolved legacy team-status fields. It does not relax `generate_2025_selector_inputs.py`'s historical-artifact acceptance: strict generation still fails on the documented 1,598-row discrepancies. Diagnostic frames are available only with explicit audit-only execution and are never represented as accepted historical selector tables.

The runner restores the other seasons and the reviewed base, crosswalk and scheduling inputs from SHA-256-pinned original archives. Both conditions consume the same freshly reconstructed 2025 game selector and the same freshly parsed rows from the complete 5,023 saved-PDF candidate set. The control retains the historical 2025 team table; the experimental condition consumes the complete source-derived team table. Before execution, the runner requires identical file inventories and hashes except for that table, unchanged schema/keys/row order, exactly 1,598 differing rows, and differences confined to `team_final_status` and `inferred_no_listed_players`. In particular, `usable_submitted_status` must remain identical.

The original October scientific script is SHA-256-pinned and unchanged. The existing path-redirection wrapper additionally traces actual opens and checks before/after hashes of the three 2025 files. The original script's known post-panel `norm.sf` failure is recorded explicitly; an unrelated crash fails acceptance. The independent original fast model program executes all four corrected specifications separately.

All eight frozen outputs receive independent decoded SHA-256 and complete string-cell comparisons. Player-game comparisons use unique `player_team_game_id` keys. The only permitted differing output is the team-status table, with precisely the two documented fields. The accepted frozen panel hash is required. The existing Toronto chronology correction then actually executes for both conditions, including actual-open tracing of the unchanged generated 2025 inputs. Both corrected panels must match the accepted hash and every one of the four model output rows must match between conditions; all four must also satisfy existing corrected model targets.

## Command

Run in Linux amd64 with Python 3.12 and `requirements-builder-lock.txt`. Keep sources and outputs outside Git. Alongside the historical restoration archives, supply `nba_game_covariates_v1.zip` and the original `audit_2025_26_s4_join_results.zip`, pinned to `6ad1013984693abc852b4a8cf2fcf3aad6dc1a9eb555ef35d121f95ca4c9989c`.

Reuse an existing complete candidate directory only after its acceptance report and every source-file hash pass validation. Otherwise generate it with the existing original parser:

```bash
python -m scripts.data_rebuild.rebuild_2025_full_candidates --archive-dir /private/originals --output-dir /private/2025-candidates
python -m scripts.data_rebuild.experiment_2025_team_metadata --archive-dir /private/originals --fresh-source-dir /private/2025-candidates --output-root /private/2025-team-experiment
```

The private output contains input fingerprints, original archive/code identities, per-stage execution checkpoints and logs, frozen comparisons, both corrected panels and models, actual-open evidence and, **only after all gates pass**, `experiment_acceptance.json`. No final panel is copied from a prior run. Stage checkpoints hash every output file. Explicit `--resume` revalidates sources, code and prepared conditions and rejects changed checkpoints or incomplete stage output directories. It does not silently overwrite partial scientific results.

## Static dependency trace

In the original builder `scripts/executed/06_cadence_harmonized_identification/build_harmonized_panel_and_models.py`, lines 74–89 read, normalize, join by stable game/team identities, and export the team metadata without filtering observations by either disputed value. Lines 248–252 discard inherited base metadata, join the reconstructed team status, and derive outcome observability solely from `usable_submitted_status`. Lines 257–280 compute absence, histories and onset risk without either disputed field. The bounded `outcols` at lines 287–288 excludes both disputed fields. Season QA, snapshot comparison and regressions use this bounded scientific data and unaffected selectors. The correction changes only documented 2021–22 fixture controls/report links and reruns that same original builder; the separate fast model script reads the bounded panel. This trace is a hypothesis about propagation, not experimental evidence by itself.

## Acceptance scope

Even a passing controlled experiment proves neither recovered original S4 team-join logic nor cumulative six-season reconstruction. Original publication/acquisition metadata and human-reviewed inputs remain declared historical inputs. The five prior targeted raw-season runs are separate proofs. Cumulative canonical integration and an authentic new combined final-dataset run remain separate gates.

The November 15 execution was started after the previous temporary environment was lost. Its result will be recorded separately; the incomplete November 14 attempt is not claimed as accepted.
