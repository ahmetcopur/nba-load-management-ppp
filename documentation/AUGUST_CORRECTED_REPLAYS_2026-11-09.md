# August 2026 latest-pre-tip analyses: frozen replays and corrected-chronology results

**Date:** November 9, 2026. **Scope:** a separate corrected-chronology sensitivity. The August 12 frozen data, the October 25 manuscript and every archived output are unchanged. PR #4 stays a draft.

Everything below was executed in this session from the archived source ZIPs and the pinned shared repository (commit `0bd713d97e8d519df5700ef473da34aba4495223`, clean checkout). Each corrected result was produced only after the same code reproduced the archived frozen output. Evidence files are in [validation/august_corrected_replays_2026-11-09](../validation/august_corrected_replays_2026-11-09/).

## 1. Corrected August risk panel identity

The uploaded `player_game_panel_model_at_risk_analysis_ready.csv.zip` was not reachable from this session. The file attached to the request (`player_game_panel_analysis_ready.csv.gz`) is byte-identical to the frozen full panel in `data_final` (decoded SHA-256 `5154317f…`, 248,730 rows), so it is not the corrected file. Instead the corrected panel was rebuilt from the four original source ZIPs with the committed chain, and it reproduces the expected file exactly.

| Step | Result |
|---|---|
| Source ZIPs (core, covariates, roster, analysis-ready) | all four SHA-256 values match the documented hashes |
| Original August finalizer on the unchanged sources | decoded output SHA-256 `253bf017…`, byte-identical to the archived core |
| Same finalizer on corrected sources | 248,728 rows, 180,831 at risk, 12,707 onsets |
| Reviewed taxonomy baseline gate | 2,182 reviewed reason keys reproduce all 248,730 frozen class, onset-type and flag cells |
| Corrected full panel | decoded SHA-256 `2acd7448…`, 248,728 rows, 125 columns |
| Corrected model risk panel | decoded SHA-256 **`5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3`**, 180,831 rows, 72 columns in the frozen column order, 180,831 unique `player_team_game_id` values |

The same two outputs were produced under pandas 3.0.5 and pandas 2.2.3. The panel was then zipped under the expected member name and passed through `run_august_corrected_zip_replays.py`, which checked ZIP CRC, member name, decoded SHA, columns, row count and unique IDs before running anything.

Two defects in previously committed code surfaced during this first end-to-end execution. Both are fixed here, with tests.

- `build_august_analysis_ready_sensitivity.py` compared Series with `.equals`, which under pandas 3 also requires identical dtypes (`object` versus the new `str`). Every class, onset and flag value matched, but the gate failed. CI ran this test only under pandas 2, which hid the problem. The comparison now requires an identical index and identical values and ignores the string dtype.
- `run_august_corrected_zip_replays.py` required an `at_risk_for_new_onset` column, which the model risk panel does not have (every row is at risk), so it would have rejected the genuine corrected ZIP after its SHA check passed. The requirement is removed, a duplicate-ID check is added, and a test now pins the requirement set to the real 72-column header.

If you still want the uploaded ZIP itself checked, copy `player_game_panel_model_at_risk_analysis_ready.csv.zip` into `~/Downloads` on the linked computer. Its decoded CSV must hash to the value above.

## 2. Corrected advance-TV join

All 180,831 corrected risk rows join the release-time TV table after the two February 2022 Toronto lookup keys are moved to the real dates. Without that change, 46 rows (22 Miami, 24 Chicago) would be unmatched. Exactly two TV rows change, only in `game_date_et` and `tip_utc`. Networks are unchanged (Miami at Toronto was announced on TNT, Chicago at Toronto was not national), there are no duplicate keys and no primary-TV disagreements.

The release PDF explains the original swap. Release game 430 was Chicago at Toronto on Dec 16, 2021 (postponed). Release game 784 was Miami at Toronto on Feb 3, 2022, on TNT. The raw NBA boxscore JSON shows game 0022100430 (Chicago) was played Feb 3 and game 0022100784 (Miami) on Feb 1. FixtureDownload's match numbers are crossed relative to these NBA IDs, and joining one numbering to the other by number recreates the swap. Under the historical rule, a rescheduled game keeps its release-time network (for example Dallas at Houston on ESPN moved 46 days, Golden State at Dallas on TNT moved 3 days), so keeping TNT for the Heat game at Feb 1 follows the original definition. The rekeyed rows keep their stale `mapping_method` and `schedule_date_shift_days` metadata. No analysis reads those fields. See [the two-game crosswalk](../validation/august_corrected_replays_2026-11-09/toronto_feb2022_physical_game_crosswalk.csv).

## 3. Predeclared heterogeneity

`run_august_heterogeneity_from_release.py` ran the released `run_predeclared_heterogeneity.py` unchanged. The frozen rerun reproduces all 8 archived estimates (coefficients within 2.8e-14, SEs within 1.4e-5 pp, p and q within 2.6e-6). The table gives the star × post × TV DDD within each subgroup (H0 is outside the subgroup, H1 inside), the heterogeneity contrast H1 − H0, and BH q across the four predeclared tests within each TV family. Confidence intervals are ±1.96 SE, consistent with the script's normal p-values.

| Subgroup | TV | Run | N (H0/H1) | H0 DDD (SE) | H1 DDD (SE) | H1 − H0 (SE) | 95% CI | p | BH q |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Back-to-back | National-partner | frozen | 180,695 (147,771/32,924) | +2.640 (1.161) | −2.843 (5.164) | −5.484 (5.188) | [−15.65, 4.69] | 0.290 | 0.393 |
| Back-to-back | National-partner | corrected | 180,697 (147,749/32,948) | +2.689 (1.166) | −2.646 (5.113) | −5.335 (5.145) | [−15.42, 4.75] | 0.300 | 0.400 |
| Back-to-back | Linear-only | frozen | 180,695 (147,771/32,924) | +1.392 (1.146) | −4.855 (5.135) | −6.247 (5.098) | [−16.24, 3.75] | 0.221 | 0.441 |
| Back-to-back | Linear-only | corrected | 180,697 (147,749/32,948) | +1.441 (1.151) | −4.659 (5.083) | −6.100 (5.053) | [−16.00, 3.80] | 0.227 | 0.455 |
| High recent workload | National-partner | frozen | 139,535 (104,649/34,886) | +0.245 (2.464) | +3.884 (1.636) | +3.639 (2.871) | [−1.99, 9.27] | 0.205 | 0.393 |
| High recent workload | National-partner | corrected | 139,536 (104,650/34,886) | +0.438 (2.459) | +3.869 (1.642) | +3.431 (2.881) | [−2.22, 9.08] | 0.234 | 0.400 |
| High recent workload | Linear-only | frozen | 139,535 (104,649/34,886) | −1.371 (2.356) | +2.755 (1.690) | +4.126 (2.870) | [−1.50, 9.75] | 0.151 | 0.441 |
| High recent workload | Linear-only | corrected | 139,536 (104,650/34,886) | −1.179 (2.350) | +2.739 (1.696) | +3.918 (2.879) | [−1.73, 9.56] | 0.174 | 0.455 |
| Near 65-game threshold | National-partner | frozen | 22,443 (15,726/6,717) | +0.410 (3.013) | +5.741 (4.202) | +5.330 (5.085) | [−4.64, 15.30] | 0.294 | 0.393 |
| Near 65-game threshold | National-partner | corrected | 22,443 (15,726/6,717) | +0.410 (3.013) | +5.741 (4.202) | +5.331 (5.085) | [−4.64, 15.30] | 0.294 | 0.400 |
| Near 65-game threshold | Linear-only | frozen | 22,443 (15,726/6,717) | +1.428 (3.107) | +3.571 (4.000) | +2.143 (5.055) | [−7.76, 12.05] | 0.672 | 0.672 |
| Near 65-game threshold | Linear-only | corrected | 22,443 (15,726/6,717) | +1.428 (3.107) | +3.571 (4.000) | +2.143 (5.055) | [−7.76, 12.05] | 0.671 | 0.671 |
| Weak opponent | National-partner | frozen | 180,695 (132,427/48,268) | +3.426 (1.399) | +5.059 (3.748) | +1.633 (3.902) | [−6.01, 9.28] | 0.675 | 0.675 |
| Weak opponent | National-partner | corrected | 180,697 (132,429/48,268) | +3.474 (1.398) | +5.066 (3.748) | +1.593 (3.902) | [−6.06, 9.24] | 0.683 | 0.683 |
| Weak opponent | Linear-only | frozen | 180,695 (132,427/48,268) | +1.839 (1.355) | +5.348 (3.847) | +3.508 (3.975) | [−4.28, 11.30] | 0.378 | 0.503 |
| Weak opponent | Linear-only | corrected | 180,697 (132,429/48,268) | +1.886 (1.355) | +5.354 (3.847) | +3.468 (3.976) | [−4.33, 11.26] | 0.383 | 0.511 |

No heterogeneity contrast is significant before or after correction (smallest BH q 0.393 frozen, 0.400 corrected), so the interpretation is unchanged. The back-to-back split moves 24 player-games into the back-to-back group because the corrected Feb 1 Heat game is the second night of a back-to-back for Toronto. Some within-subgroup DDDs are individually significant (for example national-partner outside back-to-backs, +2.69 pp, p = 0.021, and inside the high-workload group, +3.87 pp, p = 0.018). Those describe the main effect within a subset and are not evidence of heterogeneity. Age and career stage were not estimated because the frozen source has no reliable metadata for them.

## 4. Prior-event placebos and pretrends

`run_august_prior_event_placebos_from_release.py` ran the released script unchanged. The frozen rerun reproduces all 16 archived numbers (coefficients within 1.8e-14). The placebo dates are the archived ones and were not changed.

| Test | Frozen | Corrected |
|---|---:|---:|
| Joint pretrend, national-partner (χ²(2), p, N) | 1.675, p = 0.433, 180,695 | 1.473, p = 0.479, 180,697 |
| Joint pretrend, linear-only | 1.676, p = 0.432 | 1.474, p = 0.479 |
| Fake PPP start 2021-22 (both TV definitions) | +2.083 pp [−1.44, 5.61], p = 0.246, N = 87,787 | +2.020 pp [−1.55, 5.58], p = 0.267, N = 87,789 |
| Fake PPP start 2022-23 (both TV definitions) | +0.156 pp [−3.43, 3.74], p = 0.932 | +0.223 pp [−3.34, 3.78], p = 0.902 |

The two TV definitions coincide before 2023, so each fake-date placebo is identical under both. Season event estimates relative to 2022-23 (national-partner / linear-only):

| Season | Frozen | Corrected |
|---|---|---|
| 2020-21 | −0.728 (p 0.714) / −0.729 (0.713) | −0.728 (0.714) / −0.728 (0.714) |
| 2021-22 | +2.122 (0.341) / +2.123 (0.341) | +1.988 (0.372) / +1.989 (0.372) |
| 2023-24 | +2.903 (0.162) / +2.900 (0.162) | +2.902 (0.162) / +2.899 (0.163) |
| 2024-25 | +3.630 (0.059) / +3.620 (0.060) | +3.631 (0.059) / +3.620 (0.060) |
| 2025-26 | +4.347 (0.031) / +0.200 (0.922) | +4.350 (0.031) / +0.203 (0.921) |

The correction moves only the 2021-22 season estimate noticeably (−0.134 pp) and the pretrend tests remain null.

## 5. Category mechanisms (four-category FDR)

The committed runner's own private-input acceptance run is now done. The frozen rerun matches all 8 archived estimates.

| TV | Category | Frozen (q) | Corrected [95% CI] | p | BH q | Holm |
|---|---|---:|---:|---:|---:|---:|
| National-partner | Explicit rest | +0.618 (0.050) | +0.615 [0.13, 1.10] | 0.013 | 0.051 | 0.051 |
| National-partner | Vague injury | +1.591 (0.144) | +1.597 [−0.13, 3.33] | 0.070 | 0.141 | 0.211 |
| National-partner | Specific injury | +0.561 (0.478) | +0.542 [−0.66, 1.74] | 0.376 | 0.501 | 0.752 |
| National-partner | Other absence | +0.380 (0.569) | +0.442 [−0.87, 1.75] | 0.510 | 0.510 | 0.752 |
| Linear-only | Explicit rest | +0.703 (0.018) | +0.700 [0.22, 1.18] | 0.005 | 0.018 | 0.018 |
| Linear-only | Vague injury | +1.016 (0.511) | +1.021 [−0.73, 2.77] | 0.252 | 0.505 | 0.757 |
| Linear-only | Specific injury | +0.109 (0.936) | +0.090 [−1.10, 1.28] | 0.882 | 0.989 | 1.000 |
| Linear-only | Other absence | −0.053 (0.936) | +0.010 [−1.30, 1.32] | 0.989 | 0.989 | 1.000 |

The explicit-rest result stays just above 5% under national-partner TV (q 0.0505 → 0.0510) and below it under linear-only TV (q 0.0182 → 0.0184). This is a sparse outcome, and the manuscript already flags its floor effect. The pattern is the same as before, and the borderline q should not be read as a change in conclusion.

## 6. Other released August specifications

`run_august_released_suite_from_release.py` (new) runs the original **executed** scripts of three archived stages. Each script is copied with only its hard-coded `/mnt/data` root changed to a fresh sandbox, the inputs sit at their historical relative paths, and each copy's original SHA-256 and substitution count are recorded. The `scripts/portable` copies are not used, because they differ from the executed originals: besides paths, they drop the exactly collinear control `dist65_10` (equal to 6.5 minus `games_before_10`). For exact solvers this leaves every identified coefficient unchanged, but it shifts clustered SEs by up to 0.009% through the regressor count and changes the permutation placebo slightly (see below). The heterogeneity, category and placebo runners above use the portable copies and reproduce their archives to 1e-14 in coefficients. Their SE differences of up to 1.4e-5 pp probably have the same cause. The executed heterogeneity and category scripts were not rerun to confirm this.

For the collinear pair, the gate compares the identified slope `games_before_10 − dist65_10`, because a solver may split it across both terms or keep one.

Frozen gates ([suite report](../validation/august_corrected_replays_2026-11-09/august_released_suite_replay.json)):

| Stage (archived package) | Executed scripts | Archived tables | Frozen reproduction |
|---|---|---:|---|
| First-pass models (02) | baseline and robustness, category decomposition, season event study, team-season FE | 10 | all pass; coefficients within 1.1e-14, SEs and p within 1.3e-13, identified collinear slope within 1e-16 |
| TV audit (04) | TV-definition models, identification checks | 5 | all pass; within 4.1e-14 |
| Identification stage 2 (05) | standard/COVID and clustering sensitivity, sparse exact player trends | 3 | all pass; within 8.3e-13 (SE 6.6e-8) |
| Identification stage 2 (05) | 99-draw stratified TV permutation, legacy and harmonized | 3 | p-values exact (0.09, 0.26); estimates within 0.0048 pp under the documented 0.01 pp tolerance |

Two archive facts came out of this. First, the archived `player_linear_trends.csv` is the sparse exact solve (`run_player_trends_sparse_exact.py`). The iterative script writes a file with the same name, but its estimate (3.262) stops at its 150-iteration cap and was never archived. Second, the permutation script QR-factors a nuisance matrix holding both collinear controls. Its near-null direction comes from rounding, so the archived draws cannot be reproduced bit for bit on another LAPACK build. Its p-values reproduce exactly, its observed statistic differs from the exact model by 0.004 pp, and the portable copy, which drops `dist65_10`, returns the exact model value. The wider tolerance applies only to these three files and is recorded in the report.

Corrected results, executed scripts (percentage points; latest-pre-tip; player + team-season FE unless noted):

| Specification | Frozen | Corrected |
|---|---|---|
| National-partner DDD, player + team-season FE (preferred) | +3.149 [0.57, 5.73], p = .0167, N = 180,695 | **+3.196 [0.62, 5.78], p = .0152**, N = 180,697 |
| Linear-only DDD, same model | +1.775 [−0.80, 4.35], p = .177 | **+1.820 [−0.75, 4.40], p = .166** |
| National-partner, player + season FE (benchmark) | +3.411, p = .0087 | +3.455, p = .0079 |
| Leave one season out (2020-21 … 2025-26) | +2.74, +4.39, +3.15, +3.49, +3.64, +2.92 | +2.81, +4.39, +3.22, +3.53, +3.69, +2.96 (all p < .05) |
| Exclude 2025-26, team-season FE | +2.728, p = .046 | +2.771, p = .043 |
| Exclude 2020-21 and 2021-22 (national / linear) | +3.839 (p .021) / +2.414 (p .162) | +3.839 (p .021) / +2.414 (p .162) |
| Player linear trends, sparse exact (national / linear) | +3.258 (p .0136) / +2.151 (p .103) | +3.305 (p .0123) / +2.196 (p .096) |
| Clustering alternatives, national-partner p range (6 schemes) | .008 to .034 | .007 to .032 |
| Permutation placebo, observed / two-sided p (national) | +3.154, p = 0.09 | +3.195, p = 0.09 |
| Permutation placebo, observed / two-sided p (linear) | +1.780, p = 0.26 | +1.820, p = 0.26 |
| National-partner plus NBA TV, 2021-22 to 2024-25 | +1.078, p = .343 | +1.106, p = .331 |
| Narrow Disney definition, six seasons / team-season FE | +1.724 (p .136) / +1.429 (p .220) | +1.713 (p .138) / +1.420 (p .222) |
| Extensive margin, player + season FE: baseline / no controls / excl. Cup / excl. 2020-21 / opening-night star / plus NBA TV | +3.41 / +3.41 / +3.69 / +2.74 / +2.65 / +1.83 | +3.46 / +3.46 / +3.74 / +2.81 / +2.69 / +1.85 |
| Vague vs specific, player + season FE (N) | −8.417 [−23.96, 7.12], p = .288 (6,256) | **−7.906 [−23.41, 7.60], p = .318** (6,259) |
| Vague vs specific, player + team-season FE | −7.181, p = .387 | −6.626, p = .423 |
| Vague vs specific, excl. 2020-21 / excl. Cup / provisional v1 labels | −8.71 / −7.70 / −2.12 | −8.03 / −7.19 / −1.82 (all p > .3) |
| Category decomposition, player + season FE (vague / specific / rest / other) | +1.60 / +0.75 / +0.63 / +0.43 | +1.60 / +0.74 / +0.63 / +0.49 |
| Raw eight-cell TV triple (absence / vague / specific) | +2.428 / +0.994 / +0.749 | +2.476 / +1.003 / +0.733 |

Every corrected estimate keeps its sign, and nothing crosses the 5% line. At the 10% line one result moves, the linear-only player-trend estimate (p = .103 to .096). The full long-format comparisons (2,971 first-pass, 232 TV-audit and stage-2 rows) are in the validation folder.

## 7. Nonlinear and multinomial stage

`run_august_nonlinear_diagnostic.py` (new) runs the released penalized-logit and multinomial scripts unchanged. They differ from the executed copies only in path constants. The run used the pinned environment of `nonlinear-repro.yml` (pandas 2.2.3, NumPy 2.3.5, SciPy 1.17.0, scikit-learn 1.8.0) with two BLAS threads.

The frozen rerun reproduces the archived package exactly, to full printed precision: national-partner extensive DDD 2.440028376624094 pp, linear-only 0.8271277966067004, vague-vs-specific −5.417689535691139 and −4.432835828041859, and all ten multinomial values. The original reproducibility note reported that this stage did not reproduce across environments (2.12 or 2.51 pp elsewhere). It does reproduce in this environment.

| Nonlinear quantity (pp) | Frozen | Corrected |
|---|---:|---:|
| Extensive DDD, national-partner / linear-only | 2.440 / 0.827 | 2.033 / 1.279 |
| Vague vs specific, national-partner / linear-only | −5.418 / −4.433 | −5.181 / −3.597 |
| Multinomial vague, national-partner / linear-only | 0.378 / 0.154 | 0.469 / 0.108 |

These changes are about ten times the LPM changes, and the cause is numerical. With the frozen data unchanged and only the row order shuffled (three seeds), the same script returns national-partner 2.09 to 2.44 and linear-only 0.83 to 1.25. The solver (`lbfgs`, tol 1e-4) stops before the high-dimensional fixed-effect logit converges, so its estimate depends on row order at the ±0.35 pp level. The corrected changes fall inside that range and cannot be attributed to the chronology correction. What does hold is the sign pattern the manuscript relies on: the extensive DDD stays positive, the vague-vs-specific contrast stays negative, and the stage remains a functional-form check without inferential p-values. The row-shuffle diagnostic is a labeled check outside the released code and does not change any reported value.

## 8. Source consistency across six seasons

`audit_corrected_chronology_consistency.py` (new) checks the frozen and corrected August and October panels at team-game level ([report](../validation/august_corrected_replays_2026-11-09/chronology_consistency_audit.json)).

| Check | Frozen | Corrected |
|---|---:|---:|
| Games / team-games | 7,230 / 14,460 | 7,230 / 14,460 |
| Duplicate player-team-game IDs | 0 | 0 |
| Duplicate team-dates | **2** | 0 |
| Rest-day arithmetic mismatches (August) | **2** | 0 |
| Unmirrored team-games, ET date not equal to tip date, team-game numbers out of tip order | 0 | 0 |
| Games whose date or tip moved (August and October) | | exactly the 2 Toronto games |
| Corrected August vs corrected October date and tip disagreements | | 0 of 7,230 |
| Raw boxscore JSON tip and date, exact (all 7,230 games) | 7,224 | 7,226 |

The frozen panels had two physically impossible schedules. The Bulls had two games on Feb 1, 2022 (at Toronto, and at home to Orlando 30 minutes later), and the Heat had two on Feb 3 (at San Antonio and at Toronto). The four remaining raw-JSON differences are the Election Day 2022 games, which tipped 2 minutes later than scheduled.

Covariates change only where the moved dates reach. Rest days change for 5 team-games, back-to-back for 4, travel for 7, time-zone shift for 4, three-in-four for 4, and opponent rest for 5, all in 2021-22 and all for Chicago, Miami, Toronto or their opponents. Elo is path-dependent, so it changes for 10,702 team-games across later seasons. The largest change is 9.9 Elo points in 2021-22, under 0.23 in 2022-23, and about zero by 2025-26. TV indicators do not change.

Inherited fields were checked for date dependence. Award lists, star status and Cup flags are inherited from the original reviewed rows by stable key and were not regenerated from primary award or Cup releases (a limitation). The date rules that use them hold exactly on both panels. The post-selection All-Star flag equals "selected and game date on or after the effective date", PPP star equals prior-three-year All-Star or All-NBA plus a selection added after the effective date, and post-PPP equals season 2023-24 or later. The 2021-22 effective date is Feb 21, 2022, the day after the All-Star Game, so a Feb 1 to Feb 3 move cannot cross it, and 2021-22 has no Cup games. The two moved games therefore cannot carry a stale star or Cup flag.

Both corrected panels already carry the official NBA IDs in `nba_game_id` (Chicago 0022100430, Miami 0022100784). Only the project key `game_id` keeps the old date encoding, for stable comparison with the frozen panel. Renaming it would change the pinned corrected SHA.

## 9. Level C check of release-time TV

`verify_tv_release_pdfs.py` (new) rebuilds every schedule row from the five archived release PDFs (2021-22 to 2025-26) and compares it with the archived parse and with the TV fixture table ([report](../validation/august_corrected_replays_2026-11-09/tv_release_pdf_verification.json)).

| Season | PDF rows | Exact page and line match | Network mismatches | Fixtures found on stated page |
|---|---:|---:|---:|---:|
| 2021-22 | 1,230 | 1,230 | 0 | 1,230 of 1,230 |
| 2022-23 | 1,230 | 1,230 | 0 | 1,230 of 1,230 |
| 2023-24 | 1,200 | 1,200 | 0 | 1,200 of 1,200 |
| 2024-25 | 1,200 | 1,200 | 0 | 1,200 of 1,200 |
| 2025-26 | 1,200 | 1,200 | 0 | 1,200 of 1,200 |

The 90 fixtures without a release line are Cup games whose matchups were set after release. Sixteen 2024-25 "NBA TV (CC)" (Center Court) rows are recorded as NBA TV, which neither national-partner definition uses. 2020-21 came from archived web pages, not a PDF, and is outside this check.

## 10. Reproduce

    python scripts/data_rebuild/rebuild_august_core_from_source_archives.py --archives ARCHIVES --output-root OUT/core
    python scripts/data_rebuild/build_august_analysis_ready_sensitivity.py \
      --historical-core OUT/core/baseline/nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz \
      --corrected-core OUT/core/corrected_source/nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz \
      --analysis-ready-zip ARCHIVES/nba_player_game_analysis_ready_v1.zip --output-dir OUT/reviewed
    # zip OUT/reviewed/player_game_panel_model_at_risk_analysis_ready.csv.gz's CSV as the expected member, then
    python scripts/data_rebuild/run_august_corrected_zip_replays.py --input-zip ZIP --shared-repo SHARED --output-root OUT/zip
    RISK=OUT/zip/input/player_game_panel_model_at_risk_analysis_ready.csv.gz
    python scripts/data_rebuild/run_august_category_fdr_from_release.py --shared-repo SHARED --work OUT/fdr --corrected-panel $RISK
    python scripts/data_rebuild/run_august_released_suite_from_release.py --shared-repo SHARED --work OUT/suite --corrected-panel $RISK
    python scripts/data_rebuild/run_august_preferred_model_sensitivity.py --frozen-panel SHARED/data_final/player_game_panel_analysis_ready.csv.gz \
      --corrected-panel OUT/reviewed/player_game_panel_analysis_ready.csv.gz --output OUT/preferred.json
    python scripts/data_rebuild/audit_corrected_chronology_consistency.py --august-frozen ... --august-corrected ... \
      --cadence-frozen ... --cadence-corrected ... --raw-json RAW_JSON --output OUT/chronology.json
    python scripts/data_rebuild/verify_tv_release_pdfs.py --shared-repo SHARED --output OUT/tv_pdf.json
    # nonlinear stage, pinned nonlinear-repro.yml environment, run from scripts/data_rebuild
    OPENBLAS_NUM_THREADS=2 python run_august_nonlinear_diagnostic.py --shared-repo SHARED --work OUT/nonlinear --corrected-panel $RISK

ARCHIVES holds the four August source ZIPs, SHARED is a clean checkout of the shared repository at `0bd713d`, and the models use Python 3.12 with `requirements-october-lock.txt`. Corrected panels, raw JSON and source ZIPs are private and are not committed.
