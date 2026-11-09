# November 9 source-recovery audit: private risk ZIP and 2020–24 archives

This is a follow-on to [the November 9 completion report](REPRODUCIBILITY_COMPLETION_REPORT_2026-11-09.md). It preserves the frozen research, does not modify any model, and explicitly separates verified local file content from uninspected archive names.

## 1. Independent real-input ZIP check

The file `player_game_panel_model_at_risk_analysis_ready.csv.zip` was recovered from the user's ChatGPT file library and its **actual ZIP bytes** were inspected locally before the container runtime stopped responding.

| Property | Inspected private ZIP | Corrected August risk dataset expected by prior executed chain |
|---|---|---|
| Compressed bytes | 9,050,929 | Different private rebuilt ZIP, previously reported |
| ZIP SHA-256 | `44d8293bea4415e44bcae7d804dfb981dce63b4944f14f31734866603ed97143` | `72cf35000af88f9dd6b28aab2ea5202590eb9d4b69c5ba44634ed12ec5d0c11f` (prior local report) |
| Decoded CSV SHA-256 | `d6e82ba61d99fb27ec4877b1c0b05fed76c5cb8fa4bf5b6322742b7049ae9635` | `5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3` |
| Decoded CSV bytes | 150,056,294 | 150,058,845 (prior recorded compressed-input audit) |
| Rows | **180,829** | **180,831** |
| Columns | 72 | 72 |
| Unique `player_team_game_id` | 180,829 | 180,831 |

The real ZIP passed `ZipFile.testzip()`, contains exactly one CSV and an ignorable `__MACOSX/` resource-fork entry, and has zero missing/duplicate player-team-game IDs. This is **not** the corrected August risk dataset. Its 180,829-row shape matches the frozen risk-panel size, although an exact byte comparison with the frozen published risk CSV has not yet been performed. **Never label this particular uploaded ZIP as a corrected private-input acceptance run.** The corrected estimates in the earlier report were generated from a *separate source-rebuilt corrected panel* under the pinned historical dependency versions.

## 2. Older raw season upload archives discovered

The user's file library also contains these files, previously not accessible to the completion-report session:

| Source archive filename | Library object bytes | Present in library | Internal PDFs / hash verification |
|---|---:|---|---|
| `audit_2020_21_upload.zip` | 11,098,653 | yes | not inspected |
| `audit_2021_22_upload.zip` | 95,811,520 | yes | not inspected |
| `audit_2022_23_upload.zip` | 133,659,142 | yes | not inspected |
| `audit_2023_24_upload.zip` | 375,865,765 | yes | not inspected |

All four original archive objects were successfully materialized into the temporary model environment. Subsequent container and Python invocations failed with `ClientError`, including trivial commands. **There is currently no evidence from this session that these four ZIPs contain the expected PDFs, have valid CRC, match the recorded SHA-256 fingerprints or reparse to archived data.** Treat this as source-file discovery only, not completion of Level C.

The original 2024–25 raw archive, 2025–26 raw/targeted archives, and previous pre-S4 derived ZIPs remain separate sources with their own known historical verification.

## 3. New deterministic raw archive verifier

New code: [`verify_historical_injury_archives.py`](../scripts/data_rebuild/verify_historical_injury_archives.py) and [synthetic failure tests](../tests/test_historical_injury_archives.py).

It verifies, without extracting or changing raw files:
- Exact original archive SHA-256 against `injury_archive_summary.csv`.
- Every present indexed PDF member's SHA-256 against the exact archive/member key in `injury_report_inventory.csv.gz`, including the original manifest/hash_status gate.
- Missing PDFs, duplicate or unsafe ZIP members, archive byte drift, and wrong indexed PDF data fail the command.
- Unindexed PDFs are counted and disclosed rather than silently interpreted as independently verified.

Run from the repository root, with the original ZIPs in `/path/to/archive_dir` and the provenance directory checked out from pinned source repository commit `0bd713d97e8d519df5700ef473da34aba4495223`:

```bash
python3 scripts/data_rebuild/verify_historical_injury_archives.py \
  --archive-dir /path/to/archive_dir \
  --metadata-dir /path/to/nba-ppp-star-availability/provenance/historical_sources \
  --output data_rebuild/output/raw_injury_archive_audit.json
```

The output remains Git-ignored; do not commit original PDFs or private source ZIPs. The script is only a **raw ZIP/PDF integrity audit**, not an injury PDF parser, report selector, absence/outcome constructor, or manuscript regression rerun. Green synthetic CI jobs are not an acceptance run on these four private raw archives.

## 4. Remaining acceptance sequence

1. Run the verifier against the **actual four materialized ZIPs** and resolve any per-archive missing-source or checksum errors.
2. Reparse the original injury PDFs by season with the matching original parser and the documented selection timestamps; compare parsed row multisets and parse logs against archived pre-S4 intermediates. Verify that each chosen snapshot is pre-tip and preserve the documented December 2025 printed-clock sensitivity separately.
3. Rebuild downstream source-to-roster/report/covariate/taxonomy and August/October panels; compare frozen results first, corrected chronology second, keeping original releases untouched.
4. Regenerate award and Cup histories independently from the original award/Cup source files; until then, these columns remain inherited and **not** raw-source proven.
5. Independently reconcile the remaining manuscript common-sample and figure/wording statistics. Keep PR #4 draft and never merge or rewrite the frozen original without an explicit scientific review.

## 5. Current GitHub verification boundary

The last full replay CI run **42582389410** on commit `334277e` passed all 11 jobs. It validates published source-algorithm replay and synthetic checks, not the private four raw ZIPs. A new CI run for the raw-archive verifier tests was triggered by the subsequent code changes; its outcome must be checked separately before claiming the new script is CI-accepted.
