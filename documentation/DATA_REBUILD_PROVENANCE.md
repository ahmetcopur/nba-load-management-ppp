# Rebuilding NBA datasets: provenance and historical replay

**Status: partial source-to-panel pipeline, not full raw-PDF/JSON-to-paper replication.** No frozen datasets or original executed scripts are modified.

## Repository split

- Your repository, ahmetcopur/nba-load-management-ppp, holds the original executed cadence builder, frozen datasets and these new scripts.
- The shared repository, OEKundakcioglu/nba-ppp-star-availability, additionally holds the rich provenance/historical_sources/ metadata, including the 7,230 selected game-to-report and boxscore mappings. Clone the shared repository separately for these metadata inputs.
- Original official NBA PDF and boxscore JSON archives, and several historical intermediate inputs, are not present in either checkout.

## Setup

    git clone https://github.com/OEKundakcioglu/nba-ppp-star-availability.git ../nba-ppp-star-availability
    python3 -m pip install -r requirements.txt

From your repository's root, construct an auditable 7,230-game report-to-boxscore lineage CSV:

    python3 scripts/data_rebuild/build_source_lineage.py --source ../nba-ppp-star-availability/provenance/historical_sources

Verify the original seven injury PDF archives and historical JSON cache when recovered (selected checks 2,054 PDFs; --scope all checks 27,755):

    python3 scripts/data_rebuild/audit_raw_inputs.py --metadata-dir ../nba-ppp-star-availability/provenance/historical_sources --archive-dir /path/to/seven_archives --boxscore-root /path/to/boxscore_cache --scope selected --verify-archive-sha256

The audit checks PDF hashes against the historical inventory. It checks JSON structure and matching official game IDs but cannot prove original JSON byte identity because source checksums are unavailable.

With the original upstream season parses, canonical panel, cadence selector, crosswalk and team status inputs restored under one nba_continue folder, check paths and run the unchanged historical builder through a temporary path-adjusted copy:

    python3 scripts/data_rebuild/run_historical_cadence_builder.py --historical-root /path/to/nba_continue --check-only
    python3 scripts/data_rebuild/run_historical_cadence_builder.py --historical-root /path/to/nba_continue

Compare against the original frozen panel without mutating it:

    python3 scripts/data_rebuild/compare_panels.py --reference data_intermediate/player_team_game_harmonized_cadence.csv.gz --candidate data_rebuild/output/historical_cadence/player_team_game_harmonized_cadence.csv.gz

Generated outputs go under data_rebuild/output/ and are Git-ignored. A nonzero exit from an audit or panel comparison denotes missing/differing inputs or values, not successful replication.

## Gaps requiring follow-up

- Restore the seven season-specific original NBA injury report archives and 7,230 original official NBA boxscore JSON payloads.
- Restore the original canonical base panel, per-season parsed injury reports, checkpoint selection, team-game report status, player crosswalk and alias resolution, schedule/TV assembly and covariate files; metadata cannot substitute for executed transforms.
- Preserve national-TV sources (five original NBA 2021-26 schedule PDFs and 2020-21 broadcaster HTML), six historical fixture CSVs, and star recognition sources.
- Revisit 21 selected December 2025 games involving eight PDFs with a 15-minute manifest/header timestamp discrepancy before claiming the exact cadence selector has been independently reproduced.
- Preserve the distinction between October advance national-partner TV including 2025-26 streaming-only games and the linear-TV sensitivity. Historical August estimates do not replace October paper estimates.
- Original acquisition timestamps were not recorded; do not infer them from archive/file times.

These scripts add **provenance, integrity checking, a portable historical replay entrypoint, and strict frozen-output comparison**. They do not yet reproduce the combined data directly from raw sources.
