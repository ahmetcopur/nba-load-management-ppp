# Level C — verify original NBA boxscore JSON against archived V2 and canonical base
**Status:** Verifier code and negative tests are in draft PR #4. Full 7,230-file JSON execution is still blocked on original raw files.  
**Date:** November 8, 2026

> **November 8, 2026 full-run evidence update:** A complete 7,230-JSON offline repair was reported and documented in [full verification and scientific date audit](LEVEL_C_FULL_BOXSCORE_VERIFICATION_AND_DATE_SWAP_AUDIT_2026-11-08.md), with the complete [SHA-256 manifest](../validation/level_c_boxscore_2026-11-08/boxscore_json_sha256_manifest.csv), [QA verification](../validation/level_c_boxscore_2026-11-08/boxscore_cache_verification.json) and zero differences to archived V2/base rows. The raw original JSON bytes were not uploaded here for an independent second full run, so report this as **full run supported by supplied evidence and independently checked game-ID coverage**, not new locally repeated raw-content verification. The original V2 matching has a pandas-3 timestamp-unit bug that concealed two **48-hour** fixture-date errors; see the linked audit before interpreting the covariates. The verifier now reconstructs the exact byte-verified original executed repair script automatically (optional --repair-script must match exactly). The older pending-work language below describes the earlier stage and is superseded by this note.

## Objective and scientific boundary

The independent Level-B replay already reproduces the cadence panel from original historical intermediate ZIPs. This new, narrower Level-C stage verifies the earlier input link:

7,230 original per-game NBA boxscore JSONs → original offline V2 repair program → archived V2 roster/crosswalk/manifest/team counts → canonical analysis-ready player-game panel.

A successful run of this boxscore link **does not** independently reconstruct every injury PDF, broadcaster schedule, awards/star classification, covariate or research regression.

## What is verified independently already

The original archived nba_boxscore_roster_frame_v2_output_upload.zip includes 7,230 matched fixture games, 248,571 player roster rows, and 14,460 team-game rows. Its QA declares no unmatched fixtures, unused official boxscores, missing player IDs or duplicate player/team/game rows. Maximum archived absolute tip-time difference is 2.88 minutes (not necessarily zero).

We independently extracted the original 113,977,798-byte game_roster_players.csv and the historical base panel. **All 248,571** boxscore-derived player rows match the canonical base by game/team/player ID, with **no missing or extra keys and no comparable field discrepancies**. This is derived V2 → base verification, not raw-JSON → V2 verification.

Claude reported that a linked Mac contains:
- ~/nba-load-audit/nba_boxscore_roster_frame_v1_output/raw_json/ — reportedly 7,185 original JSONs
- ~/nba-load-audit/nba_boxscore_roster_frame_v1_output/download_log.csv — original successful download sizes/endpoints
- ~/nba-load-audit/nba_boxscore_roster_frame_v2_output/raw_json_discovery/ — reportedly 45 additional JSONs (29 from 2020–21, 16 from 2024–25)
- The 48-game sample reportedly reproduced 1,615 archived roster rows.

**These Mac file counts, the 48-game sample and original JSON content have not been independently verified by this ChatGPT session.** The JSONs are absent from the attached patch and public GitHub repository.

The user also has these source ZIPs in the ChatGPT file library, but the ZIPs do NOT themselves contain the full original 7,230 JSON cache:
- nba_boxscore_roster_frame_v2_repair.zip (original repair_boxscore_rosters.py)
- nba_boxscore_roster_frame_v2_output_upload.zip (archived derived tables)
- nba_game_covariates_v1.zip (game_level_covariates.csv)

## New implementation on PR #4

- scripts/data_rebuild/verify_boxscore_cache.py validates JSON schema, gameId, filenames, season, home/away IDs, gameTimeUTC, original logged byte sizes; computes a new per-file SHA-256 manifest; executes the archived repair code with --no-download in an isolated scratch layout; checks full or partial completeness; and compares all four regenerated V2 tables with the archived ZIP and the published canonical base panel.
- tests/test_boxscore_cache.py tests malformed JSON, inconsistent game IDs, conflicting sizes, duplicate cache IDs, roster-key duplicates, invalid numeric values and incorrect partial/full QA.
- requirements-boxscore-lock.txt pins independently tested Python analysis dependencies.
- .github/workflows/data-rebuild-tests.yml runs the additional Level-C negative test job on GitHub Actions.

The original download log recorded bytes, not historical SHA-256s. New hashes prove only the current bytes. The code rejects duplicate game IDs and misleading many-to-many joins rather than coercing a match, and it will not accept missing numeric values as equal to invalid text.

## Runbook on a computer containing the original cache

Check out draft branch audit-rebuild-reliability-2026-11 from https://github.com/ahmetcopur/nba-load-management-ppp and install requirements-boxscore-lock.txt.

Supply the actual original files via these CLI arguments:
- --v1-output: original nba_boxscore_roster_frame_v1_output folder with raw_json/ and download_log.csv
- --discovery: original raw_json_discovery directory
- --fixtures: extracted nba_game_covariates_v1/game_level_covariates.csv
- --repair-zip: nba_boxscore_roster_frame_v2_repair.zip
- --reference-zip: nba_boxscore_roster_frame_v2_output_upload.zip
- --base-panel: defaults to published data_final/player_game_panel_analysis_ready.csv.gz
- --output: an ignored scratch output directory such as data_rebuild/output/boxscore_raw_verification

Example complete command (paths must be adjusted to actual local files):

    python3 scripts/data_rebuild/verify_boxscore_cache.py \
      --v1-output "$HOME/nba-load-audit/nba_boxscore_roster_frame_v1_output" \
      --discovery "$HOME/nba-load-audit/nba_boxscore_roster_frame_v2_output/raw_json_discovery" \
      --fixtures "$HOME/nba-load-audit/nba_game_covariates_v1/game_level_covariates.csv" \
      --repair-zip "$HOME/nba-load-audit/nba_boxscore_roster_frame_v2_repair.zip" \
      --reference-zip "$HOME/nba-load-audit/nba_boxscore_roster_frame_v2_output_upload.zip" \
      --output "data_rebuild/output/boxscore_raw_verification"

Run --allow-partial only on deliberately isolated small sample folders, while keeping the full original fixture CSV, download log, reference V2 ZIP and base-panel reference. The historical repair script intentionally exits with code 2 if the complete 7,230-fixture frame is missing; sample mode accepts it only when all sample game IDs map to valid fixtures and all applicable output rows match. Full mode requires repair exit 0.

Output to keep under the ignored output folder:
- boxscore_json_sha256_manifest.csv — new per-file SHA-256, size, payload game ID, season, source endpoint when logged
- boxscore_cache_verification.json — match verdict, detailed per-table comparison and complete/sample QA
- repair_stdout.txt and repair_stderr.txt — original historical executable output
- the four regenerated V2 derived CSVs, NOT the raw JSONs

## Mandatory full-mode acceptance criteria

1. Exactly **7,230** complete original files with **7,230 unique** official NBA game IDs. Every file passes JSON structure, official teams, game time and filename/season checks. Original download sizes must agree wherever logged; lack of a download log for five old smoke-cache files and 45 discovered files is preserved explicitly, not fabricated.
2. Original repair program executes offline, exits 0 and declares complete: 7,230 matched games, 14,460 team-game rows, 248,571 roster player rows, zero unused official boxscores, zero duplicate player-team-game keys, zero missing player IDs.
3. All four output CSVs match the original archived V2 tables on unique keys and comparable fields. Machine-dependent raw_json_path is the **only** intentionally excluded archive column.
4. Regenerated roster matches the published canonical base panel by player/team/game ID, with no discrepancies in comparable text, numeric, minutes or playing-status fields.
5. A reproducibility log records exact JSON hashes, original repair script SHA-256, reference ZIP SHA-256, fixture SHA-256, Python environment and any discrepancies. No values or source files are altered merely to make them match.

If any check fails, retain the error and investigate before calling this Level-C *component* verified. Do not treat 7,230 plausible filenames alone as verified JSON content. Even a full success here still leaves the remaining raw injury-report, broadcast, awards and covariate reconstruction work.

## Source-transfer note

The complete original JSON cache has not been supplied in this ChatGPT environment. Instead of transferring 7,185 individual files, archive the v1 raw_json directory and the 45-file raw_json_discovery directory separately, preserving internal season folders, and provide the original download_log.csv. Raw NBA payloads should not be published to GitHub without checking source reuse rights.

Primary GitHub: https://github.com/ahmetcopur/nba-load-management-ppp  
Current draft PR: https://github.com/ahmetcopur/nba-load-management-ppp/pull/4
