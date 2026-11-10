# Connected reproduction: player-ID resolution to final NBA player-game core

**Status, November 10, 2026:** Executed against the recovered original private source packages. Independently regenerated the resolved player-ID table and fed it into the original player-game finalizer; all ten original output files matched exactly (gzip files compared after decompression). This is a connected **data-generation** step, not a checksum-only audit. Its input starts at an archived selected-report CSV, not raw PDFs.

## One-command runner

From a clean checkout of the draft PR #4 branch, create an environment using the committed reconstruction requirements:

    python3 -m venv .venv
    . .venv/bin/activate
    python -m pip install -r requirements-builder-lock.txt

Keep the following four original private ZIPs together outside the repository: nba_player_game_at_risk_core_v1.zip; nba_player_crosswalk_final_v1.zip; nba_boxscore_roster_frame_v2_output_upload.zip; nba_game_covariates_v1.zip.

    python scripts/data_rebuild/run_connected_player_game_core.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/connected-core-2026-11-10"

The **output directory must not exist**, must not reside inside a Git checkout, and must not be nested in the original ZIP directory. A failed run may leave a partial directory; use a new name for a retry. The script verifies the four original ZIP SHA-256 values before any output, refuses changed original script bytes and never modifies raw archives.

The tested reconstruction environment is Python 3.13.5, pandas 2.2.3, NumPy 2.3.5 (see requirements-builder-lock.txt). These are *not* documented as the original researchers' historical versions.

## What the command creates

It starts with the original archived selected-report rows and independently reruns the sequence:

1. Reviewed season/team/name crosswalk; ambiguous aliases rejected, then only unique reviewed aliases and unique official box-score roster names used as fallback.
2. Original status-priority deduplication: Out, Doubtful, Questionable, Probable, Available. Result: **73,438** resolved player-report rows, 33 columns.
3. Source-hash pinned original finalizer, with **only** its hard-coded filesystem root redirected to the new private output directory. The source code's injury status, absence/risk-set, spell, and provisional taxonomy rules are unchanged.
4. Combine **248,571** official box-score player-games, **159** report-only players and original game/team report and schedule covariates.
5. Generate all core panel CSV outputs and compare their entire decoded bytes against the historical frozen reference.

No private PDFs, raw ZIPs, player-report rows, or reconstructed player-level CSVs are committed to GitHub.

## Exact connected private run

| Independently generated stage / archived output | Result | Frozen equality |
|---|---:|---|
| Resolved player-report table (33 fields) | 73,438 records | Exact |
| Final core player-game panel | 248,730 rows | Exact decoded CSV |
| At-risk onset model panel | 180,829 rows | Exact decoded CSV |
| Provisional absence spells | 13,723 rows | Exact decoded CSV |
| Report-only roster additions | 159 rows | Exact CSV |
| Season summary | six seasons | Exact CSV |
| Onset type by season | six seasons | Exact CSV |
| Designation status by season | six seasons | Exact CSV |
| Taxonomy review sample | 300 records | Exact CSV |
| Core QA JSON | all recorded metrics | Exact bytes |

The finalizer also reports **12,710** absence onsets, no duplicate player-game keys, no missing player IDs and no missing game covariates. Direct reviewed crosswalk assignments: 72,819; reviewed alias fallback: 606; unique roster-name fallback: 15; unresolved: zero.

For compressed files the exactness gate compares all **decompressed** CSV bytes. Gzip header timestamps can differ even when every CSV byte is identical.

[Real-input sanitized source fingerprints and all ten decoded-output hashes](../validation/level_c_injury_pdf_real_2026-11-10/connected_identity_to_core_exact_2026-11-10.json)

[One-command executable](../scripts/data_rebuild/run_connected_player_game_core.py) | [Original player-ID resolver replay](../scripts/data_rebuild/verify_player_identity_replay.py) | [Synthetic fail-closed tests](../tests/test_connected_player_game_core.py)

The new runner has explicit checks for immutable original finalizer code, exact output schema and values, unique ZIP members, private output location, missing or modified inputs, and the historical core release counts. Synthetic regression tests are run in GitHub Actions. **GitHub-hosted CI has no private source ZIPs; the real-input acceptance was executed locally with equivalent original source stages before packaging the single command.**

## Remaining end-to-end data dependencies

**This command does not yet start from raw official NBA PDFs.** The original PDF parse/report selection/reason mapping stages were independently verified in earlier source-audit runs, but their outputs have not all been connected into one command generating the selected-report CSV input. Separately, the player-game core lacks independently regenerated original award/All-Star/All-NBA star history, NBA Cup labels, age/biographical metadata, reviewed frozen injury taxonomy, and manuscript-ready TV/regression enrichments.

The 2020–21 PDF layout issue remains: **93** free-text reason fields differ in a diagnostic reparse (25 rows selected into games); player IDs and status fields match. Do not silently substitute that reparse's reasons.

The next stage is to connect the PDF-derived selected report rows into this executable core, then reconstruct reviewed analysis-ready variables from their actual upstream award/taxonomy/TV files instead of copying final labels from a frozen output. Only then refit the manuscript specifications.

See [Issue #5](https://github.com/ahmetcopur/nba-load-management-ppp/issues/5) for remaining scientific gates. Preserve the frozen research and keep PR #4 **draft and unmerged**.


## Extension: one-command core plus source-coded All-Star/All-NBA history

The previous core-stage run was extended in a real private execution to the historical **star award enrichment**. The source-coded original All-Star/All-NBA builder from the authentic nba_player_game_at_risk_star_v1.zip was checked for the exact source SHA-256, relocated to the new private output root by changing **only four hard-coded /mnt/data/ path prefixes**, and executed against the newly rebuilt core panel.

All **12** original non-manifest star package files reproduced exactly, including the original embedded award lists, source builder code, 248,730-row full star panel, 180,829-row at-risk star panel, complete season-level star calendar, and QA metrics.

### Preferred combined command

Put a **fifth original ZIP**, nba_player_game_at_risk_star_v1.zip, in the same private archive directory as the four core-stage ZIPs. Then run:

    python scripts/data_rebuild/reproduce_core_and_stars.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/core-and-stars-run"

This is a **new, separate output directory** that must not yet exist. The umbrella command verifies availability and SHA-256 of the star archive **before** executing the initial core stage; it then runs source-pinned identity resolution, the original core finalizer, all ten core byte comparisons, the original source-coded star builder, and all twelve star output comparisons.

For an already accepted connected core result, run only the star extension:

    python scripts/data_rebuild/run_connected_star_enrichment.py \
      --archive-dir "$HOME/nba-original-zips" \
      --core-run-dir "$HOME/nba-private-rebuild/connected-core-2026-11-10"

The star-only command requires a valid **connected_core_reproduction_report.json** with the exact ten-file acceptance marker, and rechecks that generated core outputs still match the immutable original. It rejects an already existing star-output directory or star ZIP because the archived star builder contains historical directory-deletion and ZIP-unlink operations; neither destructive path can be pointed at any prior run or original source.

| Independently run star stage | Result |
|---|---:|
| Original All-Star/All-NBA award input rows | 358 |
| Player-game core rows | 248,730 |
| At-risk star panel rows | 180,829 |
| Star-designated player-game observations | 23,166 |
| Midseason current-All-Star transition rows | 1,019 |
| Missing star-status labels | 0 |
| Full comparison to the frozen star package | **12/12 substantive original files exact** |

[Original-star replay evidence and decoded-byte SHA values](../validation/level_c_injury_pdf_real_2026-11-10/connected_core_and_star_exact_2026-11-10.json) | [Standalone original star runner](../scripts/data_rebuild/run_connected_star_enrichment.py) | [One-command core+star runner](../scripts/data_rebuild/reproduce_core_and_stars.py) | [Synthetic safety/regression tests](../tests/test_connected_star_enrichment.py)

**Scientific qualification:** the original award lists are embedded in the historically archived source code. This reproduces their application exactly but **does not independently verify all 358 awards/replacements from the cited official NBA announcements**. Similarly, the NBA Cup lookup and original full analysis-ready taxonomy/regression sources are further dependencies; Cup/TV/manuscript results are not automatically certified by this stage. The original star archive's file_manifest_sha256.csv describes compressed gzip members, whose headers may have different timestamps; the twelve substantive source/output files were compared over their *entire decoded contents* instead.
