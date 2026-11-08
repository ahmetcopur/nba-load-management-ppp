# Rebuilding NBA research datasets: source provenance and replay

**Status: partial pipeline, not yet an end-to-end raw-PDF/JSON-to-paper replication.**
The published August freeze, October analyses, and original executed scripts remain unmodified.

## Already reproducible

The repository includes the original executed cadence-panel builder, October regression reruns, and frozen analysis-ready datasets. Historical provenance metadata covers 7,230 games and identifies 2,054 selected injury-report PDF objects from 27,755 archived PDFs. Metadata and checksums are not the original raw PDF or boxscore bytes.

## Commands (from repository root)

Build the deterministic 7,230-game report-to-boxscore lineage CSV:

    python3 scripts/data_rebuild/build_source_lineage.py

Audit recovered injury PDFs and boxscore JSON objects (paths are illustrative):

    python3 scripts/data_rebuild/audit_raw_inputs.py --archive-dir /path/to/seven_archives --boxscore-root /path/to/boxscore_cache --scope selected --verify-archive-sha256

Pass --scope all to verify all 27,755 archived PDFs instead of the 2,054 selected objects. This audit validates JSON game IDs and structure, not original unrecorded JSON byte checksums. The archive SHA-256 comparison verifies original ZIP bytes when enabled.

Check whether restored historical intermediate files are present, then replay the original builder unchanged (except on-the-fly path substitution in a temporary copy):

    python3 -m pip install -r requirements.txt
    python3 scripts/data_rebuild/run_historical_cadence_builder.py --historical-root /path/to/nba_continue --check-only
    python3 scripts/data_rebuild/run_historical_cadence_builder.py --historical-root /path/to/nba_continue

Compare the resulting panel against the frozen dataset:

    python3 scripts/data_rebuild/compare_panels.py --reference data_intermediate/player_team_game_harmonized_cadence.csv.gz --candidate data_rebuild/output/historical_cadence/player_team_game_harmonized_cadence.csv.gz

Results are written under data_rebuild/output/ and excluded from Git. The panel comparator deliberately reports every differing column/key instead of silently normalizing values.

## Inputs not yet recovered or reconstructed

- Seven season-specific original NBA injury-report ZIP archives and 7,230 original official boxscore JSON payloads are not mirrored in this Git repository.
- The original cadence builder depends on the historical canonical panel, per-season parsed report rows, checkpoint selector, team-game status outputs, player crosswalk, alias tables, schedule/TV assembly and covariates. The public source inventory cannot replace these intermediate stages.
- Historical schedule inputs include six FixtureDownload-format season CSVs; national-TV reconstruction includes five official 2021–26 NBA schedule PDFs and 2020–21 broadcast announcement HTML archives.
- Twenty-one selected games share eight December 2025 reports with a 15-minute discrepancy between manifest and PDF-header timestamps; report selection requires a corrected exact-clock audit before claiming complete reproducibility.
- Original collection times are unavailable. Do not substitute file archive dates or publication dates for actual download times.

## Scientific scope

October's primary national partner TV measure includes streaming-only games in 2025–26; the linear-only TV exposure is a sensitivity. The historical August and October models estimate different variants of reporting cadence and TV exposure. These scripts do not relabel, overwrite, or claim to causally identify the PPP effect.

Read documentation/OCTOBER_2026_REPRODUCIBILITY.md, documentation/RAW_DATA_AND_REPRODUCIBILITY_SCOPE.md and provenance/historical_sources/README.md for the historical audit.
