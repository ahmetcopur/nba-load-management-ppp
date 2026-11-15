# Six original-PDF seasons connected to corrected datasets

The canonical CLI option `--rebuild-six-season-october-sources` connects the six previously tested source reconstructions to the actual October builder. It requires `--verify-original-pdfs` and replaces the older partial selector switches. It does not claim recovery of the original 2025 S4 team-join program.

The original 2020 parser/selector and the existing complete 2021–24 candidate parsers/selectors are reused. All 5,023 saved 2025 candidate PDFs feed the existing source diagnostic. The source-derived 2025 game selectors and player-report records are consumed alongside its source-derived team status. Only the two documented team fields may differ from the historical table, in exactly 1,598 rows per panel; schemas, keys, order, observability and every other field must match. The historical-artifact verdict remains `2025_metadata_exception_unresolved`, separately from scientific acceptance. The pinned [controlled experiment](CONTROLLED_2025_TEAM_METADATA_EXPERIMENT.md) supports this explicit exception. No archived values replace mismatching source-derived values.

## Inputs and environment

Use Linux amd64, Python 3.12 and `requirements-builder-lock.txt`. Supply the existing 22 pinned original ZIPs plus four schedule/status ZIPs (26 total):

- `audit_2020_21_s4_join_results_rechecked.zip`
- `audit_2021_22_s4_join_results.zip`
- `audit_2024_25_s4_join_results.zip`
- `audit_2025_26_s4_join_results.zip`

The runner lists and verifies their full SHA-256 values; missing archives or changed hashes fail preflight. All archives and output directories must be real directories outside every Git checkout. Original publication/acquisition metadata, schedules, manually reviewed identity/taxonomy decisions and the declared source mappings remain versioned historical inputs. The separate optional `--boxscore-*` arguments still require the user's authentic original NBA JSON cache; without them, the historical SHA-verified roster source is explicitly inherited.

```bash
python3.12 -m venv /private/nba-builder
/private/nba-builder/bin/python -m pip install -r requirements-builder-lock.txt
/private/nba-builder/bin/python scripts/data_rebuild/reproduce_final_datasets.py --list-inputs
/private/nba-builder/bin/python scripts/data_rebuild/reproduce_final_datasets.py --archive-dir /private/nba-original-zips --output-root /private/nba-six-final-001 --verify-original-pdfs --rebuild-six-season-october-sources --check-only
```

## First: one cumulative October gate

This reparses all six complete relevant saved candidate sets, generates the selectors, restores a new private input tree, injects all six source-derived inputs, runs the original October builder, traces all 18 actual file opens and verifies the complete decoded panel hash. It does not rebuild final corrected datasets or copy previous final panels.

```bash
python -m scripts.data_rebuild.rebuild_six_season_october_sources build --archive-dir /private/nba-original-zips --output-dir /private/nba-six-candidate-sources
python -m scripts.data_rebuild.rebuild_six_season_october_sources cumulative --archive-dir /private/nba-original-zips --sources-dir /private/nba-six-candidate-sources --output-root /private/nba-six-cumulative-001
```

Only a matching `3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac` decoded hash permits the cumulative scientific verdict to pass. Input fingerprints, pre/post checks, source/selector provenance and the separate historical-artifact verdict are in `cumulative_acceptance.json`. `build --resume` may reuse completed per-season source/selector checkpoints only after revalidating the original ZIPs and every generated source/selector file hash; incomplete stages never fall back to archived rows.

## Then: a fresh canonical three-dataset run

After the cumulative gate succeeds, use a new, absent output root:

```bash
python scripts/data_rebuild/reproduce_final_datasets.py --archive-dir /private/nba-original-zips --output-root /private/nba-six-final-001 --verify-original-pdfs --rebuild-six-season-october-sources
```

This new run executes the original PDF baseline for August and retains the fresh full 2020 source rows. It reuses that run's own 2020 rows for its selector, freshly reparses the other complete candidate seasons, and feeds all six generated inputs to the frozen and corrected October builders. It does not reuse the cumulative gate's panels or copy historical final datasets into the output. The baseline and source stages use the existing parsers; this connection adds orchestration rather than duplicate parser implementations.

The chronology wrapper verifies all 18 original handoff hashes, applies the documented February 2022 changes, and permits hash changes only in the two corrected 2021 selector tables. The corrected builder must open all 18 resulting files with unchanged before/after hashes. Unexpected changes to any other generated input fail acceptance.

The final manifest requires the three accepted complete decoded hashes, counts, and all four original corrected Stage-6 specifications with their respective complete-case samples. Its `scientific_output_verdict` and `historical_artifact_verdict` are separate. The final folder and accepted manifest are written only after every check passes. Original frozen files and archives remain untouched; private row-level outputs are never committed.

The 2020 handoff reuses its older validator, which temporarily checks/stages historical 2024 selectors before the fresh 2024 handoff replaces them. No builder runs between these steps. The definitive consumption evidence is the final 18-file map and the original subprocess's actual opens, rather than any transitional helper's earlier scope label.

Authentic cumulative and fresh final execution results must be recorded separately from these implementation instructions. Synthetic CI cannot substitute for those runs. PR #4 remains draft/unmerged and Issue #5 stays open for remaining provenance questions.

## Authentic cumulative gate — November 15

The source build genuinely reparsed **23,483 PDFs into 2,200,803 records** across the six seasons. The successful cumulative execution used clean commit `ddef0b805bc3615cec8caa19c798e36e4c4df9be`, opened all 18 generated files, preserved their pre/post hashes and generated frozen panel SHA-256 `3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac`: 248,778 rows, 7,230 games, 180,664 at-risk observations and 12,731 frozen onsets. This is a single actual original October builder run with all six new source sets, rather than six isolated season proofs.

Seven of eight frozen outputs also match the previously accepted frozen outputs byte-for-byte after decompression. Only `harmonized_team_game_report_status.csv` differs, in the documented 1,598 rows/3,196 cells of the two 2025 metadata fields; schemas, row order, all 14,460 keys, and every other field match. [Sanitized cumulative evidence](../validation/six_season_cumulative_2026-11-15/cumulative_acceptance.json) records all hashes, source handoffs, actual opens and separate verdicts.

Two earlier assembly attempts exited 137 before any October builder started. The large in-memory comparisons and RAM-backed private staging were addressed by isolated season handoffs, a stronger complete-byte-identity CSV fast path with streaming shape/count checks, and disk-backed private directories outside actual Git checkouts. The older helper path guards were aligned with the canonical runner's existing actual-Git boundary rule; real repositories, ignored paths within them and linked worktrees are still rejected. The generated PDF/selector outputs were revalidated and reused rather than reparsed. Failed attempts were retained privately and were never labeled accepted scientific executions.

The fresh three-dataset canonical run was started only after this cumulative gate passed. Its final acceptance is a separate result.

## Fresh canonical acceptance — November 15

A new, absent output root was used with clean code commit `ddef0b805bc3615cec8caa19c798e36e4c4df9be`:

```bash
python scripts/data_rebuild/reproduce_final_datasets.py --archive-dir /workspace/scratch/321f026f14f6/nba-six-private/originals --output-root /workspace/scratch/321f026f14f6/nba-six-private/final-001 --verify-original-pdfs --rebuild-six-season-october-sources
```

Python was `/tmp/nba-metadata-env/bin/python` with the pinned builder lock; temporary work was directed to a separate disk-backed private directory. All **seven stages passed**, without `--finalize-existing` or reuse of previous completed stages. The run generated its own PDF baseline and full candidate sources; the 2020 selector consumed that run's own fresh full 2020 baseline rows. All six raw source CSV hashes independently match the separately generated cumulative source run. Every source directory lies inside this new run's root, rather than a prior run or final-dataset folder.

| Newly generated dataset | Rows | At risk | Onsets | Complete decoded CSV SHA-256 |
|---|---:|---:|---:|---|
| August full | 248,728 | 180,831 | 12,707 | `2acd7448a357163951700c99df33a6949e20b19afc2219e6f8c3082b14d3619d` |
| August at risk | 180,831 | 180,831 | 12,707 | `5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3` |
| October cadence | 248,778 | 180,664 | 12,729 | `2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67` |

GNU `gzip -cd` with `pipefail` piped to `sha256sum` independently verified all three hashes after the runner finished. Separate streaming CSV scans verified schemas, unique player-game keys, row counts, at-risk counts and onsets. All 26 original ZIPs were rehashed after execution and remained unchanged. The execution checkout remained clean; no frozen files were edited.

Both the fresh frozen and corrected builders opened all 18 generated inputs and preserved their pre/post hashes. The chronology stage changed only the two declared 2021 selector files' hashes; all other generated files stayed unchanged. The PDF-derived original reviewed base also genuinely fed the corrected builder after its complete decoded baseline hash passed.

| Original Stage-6 specification | N | Estimate (pp) | p |
|---|---:|---:|---:|
| National-partner, full controls | 180,530 | 2.6742317292365767 | .0426339657858416 |
| Linear-only, full controls | 180,530 | 1.2823694527266445 | .3308675408175164 |
| National-partner, no controls | 180,664 | 2.676885495644326 | .0435317747821202 |
| Linear-only, no controls | 180,664 | 1.2948513321879846 | .3291224141374449 |

All four actually executed. Every scientific model CSV cell, including SEs, confidence limits and iterations, also matches the independently accepted controlled corrected run exactly. Elapsed `seconds` remains explicitly excluded from scientific equality, with full unequal model CSV hashes retained. No scientific tolerance or accepted dataset checksum was weakened.

The resulting native manifest reports **`scientific_output_verdict: pass`** and separately **`historical_artifact_verdict: 2025_metadata_exception_unresolved`**. [Independent verification](../validation/six_season_end_to_end_2026-11-15/verification.json) and [sanitized native manifest](../validation/six_season_end_to_end_2026-11-15/final_dataset_manifest.json) preserve source hashes, output hashes, all four models, commands, stage events and actual-open evidence.

This establishes the requested six-season PDF-to-corrected-dataset execution, not reconstruction of every historical acquisition event or primary NBA JSON payload. The original roster/crosswalk and reviewed award/Cup/TV/taxonomy inputs remain explicitly pinned historical inputs; the optional JSON cache stage was not executed because its original payload cache was not present in this execution environment. The original 2025 S4 team-join program and exact legacy team metadata remain unresolved. No new human medical classification or manuscript revision was performed. PR #4 remains draft/unmerged; Issue #5 remains open.
