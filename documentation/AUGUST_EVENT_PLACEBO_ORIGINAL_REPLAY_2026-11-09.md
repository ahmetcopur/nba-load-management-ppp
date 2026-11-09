# August prior-event pretrend and false PPP dates — source-faithful frozen replay

**Audit date:** November 9, 2026  
**Draft PR:** https://github.com/ahmetcopur/nba-load-management-ppp/pull/4

## What was independently reproduced

The original August release's scripts/portable/run_prior_event_placebo_checks.py was executed **unchanged** in a clean working copy of the immutable original research source commit 0bd713d97e8d519df5700ef473da34aba4495223.

Original published numerical references were extracted from packages/05_identification_falsification_stage2.zip, under nba_identification_falsification_stage2_v1/prior_tv_audit/:

- event_study_tv_definitions.csv — **10** season-specific Star × TV contrasts (five seasons relative to 2022–23 under each of the two TV definitions).
- joint_pretrend_tests.csv — **2** tests of the 2020–21 and 2021–22 coefficients jointly equal to zero relative to 2022–23.
- preperiod_placebo_policy_dates.csv — **4** artificial pre-policy start date contrasts (2021–22 and 2022–23 under legacy-partner and harmonized-linear TV).

The source ZIP's CRC is checked, exact reference members and unique model keys are verified, and missing, additional, or changed samples cause failure. The released source-risk input is checked against original decompressed SHA-256:

    d6e82ba61d99fb27ec4877b1c0b05fed76c5cb8fa4bf5b6322742b7049ae9635

**Independent GitHub Actions run [42566394732](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42566394732) passed the entire frozen Stage-05 statistical reproduction.** The new runner executed the exact portable script and compared every source-archived numerical result.

| Original archived comparison | Source reference rows | Maximum independent difference |
|---|---:|---:|
| Event-study estimate coefficients | 10 | 1.776e-14 percentage points |
| Event-study clustered SE | 10 | 6.173e-6 percentage points |
| Event-study p-value | 10 | 1.336e-6 |
| Joint pretrend chi-square | 2 | 9.279e-6 |
| Joint pretrend p-value | 2 | 2.007e-6 |
| Fake-policy coefficients | 4 | 5.579e-15 percentage points |
| Fake-policy clustered SE | 4 | 1.043e-5 percentage points |
| Fake-policy p-value | 4 | 2.691e-6 |

All archived sample-size and degrees-of-freedom fields are exact. The environment-specific clustered covariance differences are bounded explicitly (coefficient <= 1e-8 pp, SE/CI/test-statistic <= 0.001 in their original units, p <= 1e-4); the actual differences are far smaller. No statistical output byte identity is claimed.

Machine-readable replay evidence:
validation/august_corrected_latest_pre_tip_2026-11-09/falsification_stage05_original_frozen_ci_reproduction.json

## Why corrected August chronology must be treated separately

The already independently source-rebuilt **180,831-row corrected August latest-pre-tip risk panel** repairs the February 2022 Toronto fixture chronology, injury report assignment and player-game histories. The historical six-season announced-TV source still keys Chicago at Toronto to February 1 and Miami at Toronto to February 3, the reverse of the games' true played dates. Direct joining without correction would lose 46 corrected risk records.

The new runner scripts/data_rebuild/run_august_prior_event_placebos_from_release.py uses the independently verified TV source correction: it copies the original TV table, changes **only** two source date and UTC-tip lookup keys, and checks that all corrected risk records join, with original networks preserved. It then runs the same original published August script a second time and emits season-by-season, joint-pretrend and placebo differences. The original source and frozen panels are never modified.

**Corrected run is prepared but NOT executed in this session:** the historical private 180,831-row source-corrected model risk CSV is not in the public repository or available connected files. The script requires its independently checked decoded SHA-256:

    5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3

Accordingly, this report makes **no claim about updated corrected-chronology pretrend or placebo p-values**. They must be run rather than extrapolated from the corrected main-effect estimate.

## Executable reproduction commands

Use a clean detached checkout of the original shared source at 0bd713d97e8d519df5700ef473da34aba4495223 and Python 3.12 with requirements-october-lock.txt. Frozen mode:

    python scripts/data_rebuild/run_august_prior_event_placebos_from_release.py \
      --shared-repo ../nba-ppp-star-availability \
      --work data_rebuild/output/august_prior_event_frozen \
      --frozen-only

Corrected private input mode with a separate new work directory:

    python scripts/data_rebuild/run_august_prior_event_placebos_from_release.py \
      --shared-repo ../nba-ppp-star-availability \
      --corrected-panel /path/to/private/source_corrected_august_model_risk.csv.gz \
      --work data_rebuild/output/august_prior_event_corrected

Expected corrected files include corrected_vs_frozen_event_study_tv_definitions.csv, corrected_vs_frozen_joint_pretrend_tests.csv, corrected_vs_frozen_preperiod_placebo_policy_dates.csv, plus august_prior_event_placebo_replay.json and original executable logs. Report these results as sensitivity, not replacement of the original frozen study.

## Scientific limitations and next stage

These tests probe differential pre-policy timing and the stability of an observational TV association under fake policy dates; they are **not** exact Fisher randomization tests or a causal proof that the 2023 Player Participation Policy alone changed behavior.

The corrected August panel carries over award/star/Cup classifications and two date-encoded historical game IDs from the original freeze. Independent primary-source reconstruction of those indicators, the nonlinear and multinomial August checks, the full six-season raw PDF source-to-paper Level C and final manuscript/figure reconciliation remain open. PR #4 should remain an unmerged draft.
