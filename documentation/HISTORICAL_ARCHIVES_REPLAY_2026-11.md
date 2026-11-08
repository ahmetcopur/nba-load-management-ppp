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
python3 -m pip install -r requirements.txt
python3 scripts/data_rebuild/rebuild_from_archives.py \
  --archive-dir /path/to/nba_archives \
  --historical-root data_rebuild/output/nba_continue
```

The entrypoint (1) copies and SHA-256 logs historical source files into the original directory structure, (2) uses the unmodified archived 2025–26 PDF parser via a temporary path-adjusted copy, (3) uses the unmodified archived cadence-panel builder via a temporary path-adjusted copy, (4) compares the generated CSV to `data_intermediate/player_team_game_harmonized_cadence.csv.gz`. All computations and artifacts are written under Git-ignored `data_rebuild/output/` except for the locally restored 2025 PDF files under the same ignored folder.

Prerequisites-only check:

```bash
python3 scripts/data_rebuild/rebuild_from_archives.py \
  --archive-dir /path/to/nba_archives \
  --historical-root data_rebuild/output/nba_continue --check-only
```

Pre-verified parsed 2025 CSV can be reused with `--skip-2025-parse` to avoid repeating that step. Only use that option when the existing file has been independently validated; otherwise it defeats raw-PDF parsing coverage.

## QA

GitHub Actions `data-rebuild-tests.yml` runs Python syntax compilation, synthetic CSV panel-difference tests, archive-copy/hash tampering detection, and a self-compare of the frozen cadence panel. These are tooling tests, not evidence of historical reconstruction. The full rebuild must pass an actual independent run before declaring raw-source replication.

Expected frozen cadence panel from the October manuscript: **248,778 player-team-game rows, 180,664 onset-risk records, and 12,731 new onsets**. Any divergent counts, identity join failures, or strict comparison mismatches are blocking issues. Report them; never force them to the expected count.

## Known scientific limitations

- Historical 2025 PDF parser uses archive timestamp conventions. Twenty-one December 2025 selected games map to eight PDFs whose actual header clocks differ by 15 minutes from the manifest; a corrected checkpoint selector is a separate scientific sensitivity, not part of byte-for-byte historical reproduction.
- The full historical canonical roster/boxscore, schedule, award, TV and covariate assembly is not independently rebuilt in this particular replay.
- The original raw NBA archive download times were not recorded. Do not infer them from ZIP member timestamps.
- Source downloads and parser execution are not automatically equivalent to validation of the final model estimates; run the archived October regression scripts after comparing the rebuilt panel.
- Reproducing prior results does not isolate the effect of the NBA Player Participation Policy from simultaneous rule changes.

## GitHub state

This is an additive development branch. Do not overwrite frozen datasets, original research scripts or historical manifests. Preserve any reconstruction logs outside the public Git history unless source licensing and privacy have been reviewed.
