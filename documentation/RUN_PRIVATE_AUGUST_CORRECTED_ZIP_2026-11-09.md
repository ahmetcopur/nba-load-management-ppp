# Run the private corrected August panel directly from its uploaded CSV ZIP

> **Executed later on November 9:** the corrected panel was rebuilt from the original source ZIPs (decoded SHA-256 `5a5d286b…`, 180,831 rows, unique IDs) and passed this runner after one fix, since `at_risk_for_new_onset` is not a column of the model risk panel. Both corrected analyses then ran. Results are in [AUGUST_CORRECTED_REPLAYS_2026-11-09.md](AUGUST_CORRECTED_REPLAYS_2026-11-09.md).

**Updated November 9, 2026.** This is an operational handoff, NOT a claim that the user's latest uploaded ZIP has passed SHA inspection or that corrected heterogeneity/placebo models were run in this session.

The user supplied the conversation attachment:

    player_game_panel_model_at_risk_analysis_ready.csv.zip

A ~9.05 MB ZIP with that name is visible as a user upload. Its actual CSV contents could not be inspected in the model's Python/container session because filesystem tools returned ClientError before executing code. **Do not mark this particular ZIP verified and do not claim its 180,831-row content matches the independently corrected panel until decoded SHA-256 is checked.**

Previously source-corrected August latest-pre-tip risk CSV expected SHA-256 of DECOMPRESSED CSV DATA:

    5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3

Expected player-game rows: 180,831.

## New ZIP-compatible entry point

    scripts/data_rebuild/run_august_corrected_zip_replays.py

The script reads a ZIP containing exactly one member named player_game_panel_model_at_risk_analysis_ready.csv or with .csv.gz suffix (optional nested directories, ignored macOS metadata). It rejects duplicate candidate members, symlinks, oversized contents, CRC failure, wrong decoded SHA-256, missing required columns and incorrect row count. It normalizes only the file container to .csv.gz without changing a single CSV byte. **The ZIP is never uploaded to or committed into GitHub.**

The integrated command first reruns original frozen August models and verifies original archive benchmarks, then runs corrected source sensitivity for:

1. Eight originally predeclared heterogeneity tests: back-to-back, weak opponent, high workload, 65-game threshold × legacy partner/harmonized TV; BH correction within each original four-test TV family.
2. August prior-event falsifications: 10 season-specific event contrasts, 2 joint pretrend tests, 4 artificial PPP policy start tests.

Both run original unchanged published executable against copied inputs. For corrected mode, exactly two February 2022 obsolete source-TV date and UTC-tip lookup keys are repaired on a copy, preserving original as-announced network classifications. Frozen historical outputs and the original user ZIP remain read-only.

## Run with locally accessible file

First create a clean checkout of OEKundakcioglu/nba-ppp-star-availability at immutable commit 0bd713d97e8d519df5700ef473da34aba4495223 and activate Python 3.12 with requirements-october-lock.txt.

**Verify ZIP identity only:**

    python scripts/data_rebuild/run_august_corrected_zip_replays.py \
      --input-zip "/path/to/player_game_panel_model_at_risk_analysis_ready.csv.zip" \
      --output-root data_rebuild/output/august_upload_verify_once \
      --verify-only

A successful output records ZIP source member, decoded SHA, 180,831 CSV rows and output gzip metadata in august_corrected_zip_replay_summary.json. On mismatch, investigate the input freeze; **do not weaken the expected SHA**.

**Run both corrected analyses (use a second new output directory):**

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    python scripts/data_rebuild/run_august_corrected_zip_replays.py \
      --input-zip "/path/to/player_game_panel_model_at_risk_analysis_ready.csv.zip" \
      --shared-repo "/path/to/clean/nba-ppp-star-availability" \
      --output-root data_rebuild/output/august_upload_full_replay_once

Expected outputs upon genuine successful execution:

- input/player_game_panel_model_at_risk_analysis_ready.csv.gz (PRIVATE intermediate; do not commit).
- heterogeneity/august_heterogeneity_replay.json and heterogeneity/august_heterogeneity_corrected_vs_frozen.csv.
- pretrend-placebo/august_prior_event_placebo_replay.json and three corrected_vs_frozen_*.csv comparison tables.
- august_corrected_zip_replay_summary.json with input checksums and execution outputs.

Tests cover synthetic raw CSV, nested gzip CSV, macOS metadata, wrong scientific digest, changed row count, missing columns, ambiguous duplicate CSV, and symlinks. [GitHub Actions 42567915025](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42567915025) passed the ZIP-ingestion unit tests. **These are synthetic software tests, not validation of the user's uploaded bytes.**

## Scientific status

The original frozen eight heterogeneity estimates, ten season event coefficients, two joint pretrend tests and four fake-policy-date placebos have been independently reproduced from original published archives under original unchanged code. **The uploaded ZIP has not been opened in this session because execution environments are failing.** Corrected subgroup/event/pretrend/placebo coefficients and p-values therefore CANNOT yet be reported. Observational analysis cannot uniquely attribute effects to the PPP, given simultaneous 65-game award eligibility and Cup changes. Corrected August awards/star/Cup flags remain inherited and two date-encoded IDs remain historical comparison identifiers.

PR #4 remains an unmerged draft until the private-input corrected run and outstanding source-level checks are completed.
