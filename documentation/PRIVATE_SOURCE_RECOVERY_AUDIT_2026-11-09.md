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

| Source archive filename | Library object bytes | Expected indexed PDFs (pinned public inventory) | Internal PDF/hash verification |
|---|---:|---:|---|
| `audit_2020_21_upload.zip` | 11,098,653 | 617 | not inspected |
| `audit_2021_22_upload.zip` | 95,811,520 | 5,567 | not inspected |
| `audit_2022_23_upload.zip` | 133,659,142 | 5,541 | not inspected |
| `audit_2023_24_upload.zip` | 375,865,765 | 5,441 | not inspected |

The original shared research repository at pinned commit `0bd713d97e8d519df5700ef473da34aba4495223` records these exact archive SHA-256 values in `provenance/historical_sources/injury_archive_summary.csv`:

- 2020–21: `e310c8149701fb16cda9b1a136fbfcf9af8af8de9ca2ed09080f364a493c272c`
- 2021–22: `1e027ce6aa2a44292c3d27ba7bbfb24fcab61ded922b7ca6ba1c4211f9984339`
- 2022–23: `bea1adeac75384c75102b469a1daab43c76501caada2c3402b1e7cfa133732c0`
- 2023–24: `9cca3e58d2a8e6babce58e54dea5aeb05fa043cb034bc9065d4074e5e171daba`

These are **expected inventory values**, not locally computed confirmation. Note also that the inventory contains substantially fewer raw PDFs for 2020–21; archive identity alone cannot establish complete league coverage.

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

## 6. Follow-on verification: immutable public source-inventory gates

The historical archive verifier now also checks the **exact original provenance-file Git blob SHA-1 IDs** from pinned source commit `0bd713d97e8d519df5700ef473da34aba4495223` before reading any supplied archive checksum. It independently requires the originally published ZIP SHA-256 for each of these four seasons and the published PDF inventory counts (617, 5,567, 5,541, 5,441; combined 17,166). A self-consistent but modified inventory is rejected. These pinning rules are enforced by default in the CLI; synthetic fixtures use an explicit Python-only test bypass.

The [new GitHub Actions public reference gate](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42587846467) successfully fetched the exact immutable source commit, verified both original inventory blob IDs, compared all four published ZIP hashes, and counted all 17,166 indexed present PDF rows. The [machine-readable public reference evidence](../validation/level_c_injury_archive_source_inventory_2026-11-09.json) reports the reference identities and explicitly marks every **private source ZIP as not yet verified**.

This does **not** establish that the recovered private ZIP bytes match. The local Python/container runtime still raises `ClientError` even for a trivial probe. Original archive hash and member acceptance remains blocked in the current execution environment; no pass/fail claim is made for any actual private ZIP.

### Exact private-input acceptance command

In a clean local checkout of PR #4, keep the original raw ZIPs in a private folder outside the git working tree (e.g. `$HOME/nba_original_archives`). Prepare the source provenance from the pinned original research commit (not moving `main`):

```bash
git clone https://github.com/OEKundakcioglu/nba-ppp-star-availability.git nba_pinned_source
git -C nba_pinned_source checkout 0bd713d97e8d519df5700ef473da34aba4495223

python3 scripts/data_rebuild/verify_historical_injury_archives.py \
  --archive-dir "$HOME/nba_original_archives" \
  --metadata-dir nba_pinned_source/provenance/historical_sources \
  --output data_rebuild/output/private_injury_archives_2020_24.json
```

The command is read-only with respect to the original ZIPs and never extracts files. Treat a successful result as a **raw archive/hash identity gate only**, not a PDF reparse or manuscript reproduction. If the command reports an unindexed extra PDF, retain that count and review the difference rather than silently modifying source files.

Remaining work is tracked in [Issue #5](https://github.com/ahmetcopur/nba-load-management-ppp/issues/5). PR #4 stays **draft and unmerged**.
