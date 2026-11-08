# NBA cadence panel: restored-archives replay (November 2026)

## Scope

Reconstruct the published cadence-harmonized player-team-game panel from **original historical intermediate ZIP outputs**, while re-parsing the selected 2025–26 NBA injury report PDFs. This is not yet a from-scratch rebuild starting with all raw PDFs/boxscore JSONs; the pre-existing canonical roster/policy/covariate panel is an input.

The previous scripts in `scripts/data_rebuild/` handle source lineage, PDF/boxscore audits, historical builder execution and strict comparison. This extension adds a reproducible layout-restoration stage, 2025 selected-PDF parser replay, and one-command orchestration.

## Source archives recovered in ChatGPT file library

These exact *existing* historical ZIP names are required in a **local directory** (they are not embedded in Git):

```text
nba_player_game_analysis_ready_v1.zip
nba_player_crosswalk_final_v1.zip
nba_player_game_at_risk_core_v1.zip
nba_canonical_snapshot_selector_v1.zip
audit_2020_21_corrected_outputs.zip
audit_2021_22_cadence_outputs.zip
audit_2022_23_pre_s4_outputs.zip
audit_2022_23_s4_join_results.zip
audit_2023_24_pre_s4_outputs.zip
audit_2023_24_s4_join_results.zip
audit_2024_25_pre_s4_outputs_corrected.zip
audit_2025_26_upload.zip
audit_2025_26_targeted_upload.zip
```

Additional season audits (`audit_2020_21_s4_join_results_rechecked.zip`, `audit_2024_25_s4_join_results.zip`, `audit_2025_26_s4_join_results.zip`) are useful for independent validation but not needed to populate the specific inputs read by the frozen October cadence builder.

## Execute

Prepare a folder containing the named ZIPs. From the repository root:

```bash
python3 -m pip install -r requirements-lock.txt
python3 scripts/data_rebuild/rebuild_from_archives.py \
  --archive-dir /path/to/nba_archives \
  --historical-root data_rebuild/output/nba_continue \
  --metadata-dir ../nba-ppp-star-availability/provenance/historical_sources
```

The entrypoint (1) inspects all historical ZIP members by exact basename and rejects missing or duplicate matches *before copying*, (2) copies verified historical intermediate data and records SHA-256 hashes into the original directory structure, (3) audits that each selected 2025–26 PDF exists and is not in conflict between source archives before running the unmodified historical parser via a temporary path-adjusted copy, (4) runs the archived cadence-panel builder via a temporary path-adjusted copy, and (5) compares the generated CSV to `data_intermediate/player_team_game_harmonized_cadence.csv.gz`. For `--metadata-dir`, first clone `https://github.com/OEKundakcioglu/nba-ppp-star-availability` into the relative folder shown, or supply another exact path to its `provenance/historical_sources` directory. This enables digest comparison of selected 2025–26 PDFs against the published game-to-source map. Without this option, the parser still checks that selected PDFs exist and rejects conflicting duplicate basenames, but does **not** independently verify their hashes against that public inventory.

All computations and artifacts are written under Git-ignored `data_rebuild/output/` except for the locally restored 2025 PDF files under the same ignored folder.

Read-only archive member inspection (does not copy files or run the historical parser):

```bash
python3 scripts/data_rebuild/rebuild_from_archives.py \
  --archive-dir /path/to/nba_archives \
  --historical-root data_rebuild/output/nba_continue --check-only
```

Pre-verified parsed 2025 CSV can be reused with `--skip-2025-parse` to avoid repeating that step. Only use that option when the existing file has been independently validated; otherwise it defeats raw-PDF parsing coverage.

## QA

GitHub Actions `data-rebuild-tests.yml` runs Python syntax compilation, synthetic CSV panel-difference tests, archive-copy/hash tampering detection, and a self-compare of the frozen cadence panel. These are tooling tests and archived public package layout checks, **not** evidence of a successful historical reconstruction using the 13 original source archives. The full rebuild must pass an actual independent run before declaring raw-source replication.

Expected frozen cadence panel from the October manuscript: **248,778 player-team-game rows, 180,664 onset-risk records, and 12,731 new onsets**. Any divergent counts, identity join failures, or strict comparison mismatches are blocking issues. Report them; never force them to the expected count.

## Known scientific limitations

- Historical 2025 PDF parser uses archive timestamp conventions. Twenty-one December 2025 selected games map to eight PDFs whose actual header clocks differ by 15 minutes from the manifest; a corrected checkpoint selector is a separate scientific sensitivity, not part of byte-for-byte historical reproduction.
- The full historical canonical roster/boxscore, schedule, award, TV and covariate assembly is not independently rebuilt in this particular replay.
- The original raw NBA archive download times were not recorded. Do not infer them from ZIP member timestamps.
- Source downloads and parser execution are not automatically equivalent to validation of the final model estimates; run the archived October regression scripts after comparing the rebuilt panel.
- Reproducing prior results does not isolate the effect of the NBA Player Participation Policy from simultaneous rule changes.

## GitHub state

This is an additive development branch. Do not overwrite frozen datasets, original research scripts or historical manifests. Preserve any reconstruction logs outside the public Git history unless source licensing and privacy have been reviewed.

## November 8 audit and verification boundary

PR #2 passed five synthetic tests and a real published 7,230-game *metadata join*. Those checks were not proof of the 248,778-row panel's independent construction: self-comparing a frozen CSV is tautological. The earlier ZIP restoration script also assumed unverified internal paths and could write output during a supposedly read-only check. PR #4 corrects these limitations.

What an actual end-to-end historical **intermediate-to-panel replay** would need to establish:

1. **Source authenticity and integrity.** Preserve a full manifest mapping each of the 13 real archive names, archive SHA-256 digests, resolved input members and member digests. The newly recorded SHA-256 of a copy establishes copy integrity, not independent trust in the source archive.
2. **Exact source replay.** Run the original 2025–26 selected-PDF parser on the restored original two 2025–26 ZIPs. Audit duplicate/missing PDF basenames. Independently review the 21 clock exceptions; that is a separate sensitivity.
3. **Dataset identity.** Run the historical cadence builder and compare the generated CSV against the frozen October panel by row keys and values, including 248,778 player–team–games, 180,664 onset-risk observations and 12,731 onsets. A strict mismatch is a failed replay, not a request to patch values until they match.
4. **Analysis reproducibility.** Only after #3 passes, rerun the published October models against the rebuilt panel and compare estimates with scientific numeric tolerances. Source/analysis reconciliation cannot be inferred from green unit tests.
5. **Full raw-to-final reproduction.** This is a **different, larger milestone**, requiring re-creation of canonical NBA rosters/boxscore JSON ingestion, 2020–21 through 2024–25 injury-report parsing and cadence selection, broadcast schedules, star/award histories, game covariates, and taxonomy construction. None of those should be described as regenerated when simply restored as existing intermediate CSVs.

If an archive's member basename is missing/ambiguous, stop and inspect the original ZIP contents. Do not automatically select a different data file with a similar name.

## Dependency and acceptance status

For the reconstruction, install the historical versions in `requirements-lock.txt` rather than the unpinned `requirements.txt`. This lockfile covers the analysis packages, but the historical PDF parser's additional dependencies must still be verified from its original package before claiming an environment-complete raw-PDF parser replay. Record Python and dependency versions when running.

`python3 scripts/data_rebuild/validate_cadence_panel.py --expect-frozen` independently checks six-season coverage, unique player-team-game keys, the 7,230 game count, 248,778 rows, 180,664 at-risk observations, 12,731 onsets, and the logical condition that every onset is in-risk and currently absent. This is an **invariant check of the published data**, not evidence that the data were independently reconstructed.

## Historical coefficient acceptance check

Once the historical cadence panel is replayed, the orchestrator also checks `cadence_harmonized_model_results.csv` against the four **Stage-6 historical model** specifications in `packages/06_cadence_harmonized_identification.zip`. This compares specification keys, sample sizes, effect/SE/CI values with a 0.001 percentage-point tolerance and p-values with a 0.001 absolute tolerance. An explicit `--skip-stage6-model-comparison` flag bypasses that check, but such a run should not be called full historical analysis replication. The Stage-6 legacy/harmonized labels are **not** identical to the October 25 paper's national-partner TV versus linear-only definitions; do not misreport them as the October manuscript estimates.

All archived coefficients, frozen panels and original scripts remain unchanged; rebuilt values and comparison reports stay under `data_rebuild/output/`.

## Independently verified model-only replay (GitHub Actions)

The original Stage-6 model source can be rerun **without the private historical archives** using the published frozen cadence panel. This validates model computation, **not creation of the frozen panel**:

```bash
python3 -m pip install -r requirements-lock.txt
python3 scripts/data_rebuild/replay_stage6_from_frozen.py
```

The wrapper checks the unchanged historical `run_cadence_models_fast.py` executable, creates an isolated temporary input root, reruns all four historical Stage-6 specifications, and compares estimates and SEs against `packages/06_cadence_harmonized_identification.zip`. It writes a source/input SHA-256 and environment provenance report under `data_rebuild/output/stage6_replay/`.

**Verified in GitHub CI run 42491869499 (November 8, 2026)**: all four Stage-6 models were recalculated and matched the archived results within the declared 0.001 percentage-point and 0.001 p-value tolerances. Full-control legacy TV = +2.63044859 pp (95% CI +0.04574938 to +5.21514780; n=180,530), harmonized linear TV = +1.23897037 pp (95% CI -1.34567798 to +3.82361871; n=180,530). These are conditional regressions on the already-frozen panel; their replication does not establish original raw NBA data ingestion or a causal policy effect.

## Correct provenance source for 2025 selected PDFs

The harmonized checkpoint selector is intentionally **different** from the primary latest-pre-tip report selector. Do not compare their selected PDF sets or require exact equality of `primary_sample_report_map.csv.gz`. `reparse_2025_selected.py --metadata-dir` instead checks the **full** `injury_report_inventory.csv.gz` to verify selected 2025–26 PDF archive/member identities, stored original-manifest matching SHA-256 digests, and actual recovered ZIP bytes. Duplicate selected PDF basenames with conflicting contents are rejected. This does not resolve the 21 reported PDF-header/manifest clock exceptions.

The updated restoration log records the SHA-256 of each *complete input ZIP* as well as each extracted member, and copies raw ZIPs instead of using hard links, protecting the originals from accidental mutation.



## PDF parser completeness and platform safety

The historical 2025–26 PDF parser catches individual PDF errors inside its worker pool; a process exit code of zero is therefore **not** sufficient to call the PDF parsing stage successful. The replay wrapper now reconciles every selected (`snapshot_basename`, `published_timestamp_utc`) pair against the historical `s1_parse_log_harmonized_selected.csv`, rejects duplicates, failed/missing logs, and mismatched row totals, and rejects `zero_rows` reports unless separately reviewed. After manual confirmation of legitimate empty PDF results, the standalone `reparse_2025_selected.py --allow-zero-rows` option can be used; the default one-command runner intentionally does not silently bypass this check.

The original historical parser uses top-level `ProcessPoolExecutor` code without a multiprocessing main guard. **Linux is the supported execution target for this historical replay**, as a default macOS spawn context may not execute that original file safely. Do not change the original parser or reinterpret its results merely to obtain a successful run on another OS. Verify the parser's additional PDF library requirements from the original archival package; the pinned analysis lockfile by itself does not establish a fully specified PDF parsing environment.

The public source inventory used by `--metadata-dir` should be pinned to shared repository commit `0bd713d97e8d519df5700ef473da34aba4495223` (the same immutable commit used by CI). This inventory contains `injury_report_inventory.csv.gz`; do not substitute the primary latest-pre-tip report map for a harmonized common-checkpoint selection.
