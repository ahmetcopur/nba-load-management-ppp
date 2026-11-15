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
