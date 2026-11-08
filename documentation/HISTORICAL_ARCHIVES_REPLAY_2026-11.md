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

The entrypoint (1) inspects all historical ZIP members by exact basename and rejects missing or duplicate matches *before copying*, (2) copies verified historical intermediate data and records SHA-256 hashes into the original directory structure, (3) audits that each selected 2025–26 PDF exists and is not in conflict between source archives before running the unmodified historical parser via a temporary path-adjusted copy, (4) runs the archived cadence-panel builder via a temporary path-adjusted copy, and (5) compares the generated CSV to `data_intermediate/player_team_game_harmonized_cadence.csv.gz`. All computations and artifacts are written under Git-ignored `data_rebuild/output/` except for the locally restored 2025 PDF files under the same ignored folder.

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
