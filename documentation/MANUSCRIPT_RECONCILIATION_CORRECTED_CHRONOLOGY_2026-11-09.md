# Manuscript reconciliation: corrected-chronology results (proposed changes)

**Status: proposed changes only.** This document does not modify the published October 25 manuscript (`manuscript/october_2026/main.tex` in the shared repository), its PDF, or any frozen dataset. Every value labeled "corrected" comes from the **corrected-chronology** sensitivity, which fixes the swapped dates and report links of two February 2022 Toronto games. The frozen values remain the historical record.

Rules applied here:
1. A corrected value is listed only when the same code first reproduced the frozen published value.
2. October cadence-harmonized results and August latest-pre-tip results stay in separate tables and are never mixed.
3. No specification is chosen or dropped because of its p-value. Every reported specification keeps its original role.
4. Values whose generating output could not be located or rerun are listed as unverified rather than estimated.

Sources: [October corrected rerun](OCTOBER_CORRECTED_CHRONOLOGY_RESULTS_2026-11-08.md), [October paper statistics](OCTOBER_MISSING_PAPER_STATISTICS_2026-11-08.md) (independently rerun on Nov 9 with zero numeric difference), and [August replays](AUGUST_CORRECTED_REPLAYS_2026-11-09.md).

## A. October cadence-harmonized results (the manuscript's primary construction)

| Manuscript location | Published | Frozen rerun | Corrected chronology |
|---|---|---|---|
| Abstract, Sec. 5, Table 4: national-partner DDD | +2.63 pp [0.05, 5.22], p = .046, N = 180,530 | +2.630 [0.046, 5.215], p = .0461 | **+2.67 pp [0.09, 5.26], p = .043**, N = 180,530 |
| Abstract, Sec. 5, Table 4: linear-TV-only DDD | +1.24 pp [−1.35, 3.82], p = .347 | +1.239 [−1.346, 3.824], p = .3475 | **+1.28 pp [−1.30, 3.87], p = .331** |
| Sec. 5: relative star decline outside TV / on TV | 3.31 / 1.39 pp | 3.312 / 1.392 | **3.31 / 1.34 pp** |
| Sec. 5: raw triple difference | 1.92 pp | 1.91991 | **1.97 pp** (1.96652) |
| Abstract, Conclusion: star onset before / after 2023 | 10.6% / 9.2% | 826/7,790, 809/8,792 | 10.6% / 9.2% (825/7,790, 809/8,792) |
| Abstract: star absent-game share | 28.3% / 27.5% | 28.31 / 27.47 | unchanged |
| Table 1, Sec. 3: cadence player-team-games / at-risk / onsets | 248,778 / 180,664 / 12,731 | same | 248,778 / 180,664 / **12,729** |
| App. B: star onsets, completed | 1,635; 1,415 (713 + 702) | same | **1,634; 1,414 (712 + 702)** |
| Sec. 5.5, Table 7: star pre-reform onsets, completed, mean | 826, 713, 2.63 games | same | **825, 712**, 2.63 games (2.633) |
| Sec. 5.5: censored star spells, observed mean | 113 / 107; 5.38 / 7.47 | same | unchanged |
| Table 4: All-Star-only, national-partner | +2.99 [0.43, 5.54], p = .022 | +2.987, p = .0221 | **+3.03 [0.47, 5.59], p = .020** |
| Table 4: All-Star-only, linear-only | +1.61 [−0.94, 4.16], p = .216 | +1.610, p = .2162 | **+1.65 [−0.90, 4.21], p = .204** |
| Sec. 5.3, Table 5: one-game home/road shift | +1.41 [−0.24, 3.05], p = .093, N = 180,087 | +1.406, p = .0935 | **+1.38 [−0.27, 3.02], p = .101** |
| Table 5: one-game, excluding Cup | +1.34, p = .111 | +1.338, p = .1111 | **+1.31 [−0.34, 2.96], p = .120** |
| Table 5: one-game, excluding 2020-22 | +3.12, p = .010 | +3.118, p = .0104 | unchanged (+3.118, p = .0104) |
| Table 5: one-game, All-Star-only | +1.41 [−0.23, 3.05], p = .093 | +1.409, p = .0925 | **+1.38 [−0.26, 3.03], p = .100** |
| Table 5: longer-spell placebo | −0.26 [−1.67, 1.15], p = .719 | −0.258, p = .7194 | −0.26 [−1.67, 1.15], p = .718 |
| Table 5, App. C: paired one-game minus longer | +1.66 [−0.62, 3.95], p = .154 | +1.66405, p = .1536 | **+1.64 [−0.65, 3.92], p = .160** |
| App. A: joint pretrend | χ²(2) = 0.97, p = .616 | 0.969, p = .6161 | **χ²(2) = 0.83, p = .659** |
| App. A: placebo start 2021-22 | +1.27 [−2.52, 5.06], p = .511, N = 87,788 | +1.270, p = .5110 | **+1.21 [−2.62, 5.04], p = .537** |
| App. A: placebo start 2022-23 | −0.31 [−3.97, 3.34], p = .867 | −0.313, p = .8667 | **−0.25 [−3.87, 3.38], p = .895** |
| Table A2: omit recent minutes and games | +2.62 [0.03, 5.21], p = .048 | +2.619, p = .0477 | **+2.66 [0.07, 5.26], p = .044** |
| Table A2: schedule controls, no Elo | +2.62 [0.02, 5.21], p = .048 | +2.617, p = .0479 | **+2.66 [0.07, 5.25], p = .044** |
| Table A2: FE only, N = 180,664 | +2.63 [0.03, 5.23], p = .047 | +2.633, p = .0470 | **+2.68 [0.08, 5.28], p = .044** |
| Table A2: player/team-season clustering | +2.63 [0.16, 5.10], p = .037 | +2.630, p = .0367 | **+2.67 [0.21, 5.14], p = .033** |
| Table A2: linear-only, omit recent minutes and games | +1.24 [−1.36, 3.84], p = .350 | +1.240, p = .3495 | **+1.28 [−1.31, 3.88], p = .332** |
| Sec. 5: absence prevalence triple | +0.94 [−3.43, 5.30], p = .674 | +0.936, p = .6743 | +0.94 [−3.43, 5.30], p = .674 |
| App. return hazard, national-partner / linear | +5.08 / +4.95 pp | 5.083 / 4.954 | **+4.94 / +4.81 pp** (p .123 / .155) |
| Event-window repair and return test, linear / partner | p = .016 / .056 | same | **p = .022 / .076**; N 22,151 → 22,142 and 23,713 → 23,704 |

Unchanged October items: national-TV team-games (2,082 national-partner, 1,880 linear-only), the 101 streaming-only games, 1,125 unique players, and the 248,778-row cadence panel. Event-time and short-spell timing estimates move by at most 0.71 pp with SEs near 5 pp, and the event-window onset and prevalence samples shrink by 23 and 32. None changes sign in a reported headline.

## B. August latest-pre-tip results cited in the manuscript (sensitivity construction)

| Manuscript location | Published | Frozen rerun | Corrected chronology |
|---|---|---|---|
| Sec. 6, Table 4: national-partner, player + team-season FE | +3.15 [0.57, 5.73], p = .017, N = 180,695 | +3.14926 (original executable and reimplementation) | **+3.20 [0.62, 5.78], p = .015**, N = 180,697 |
| Sec. 6: linear-TV-only, same FE | +1.77, p = .177 | +1.77466 | **+1.82 [−0.75, 4.40], p = .166** |
| Sec. 6: earlier player + season FE estimate | +3.41 | +3.41098, p = .0087 | **+3.46, p = .0079** |
| Table 1: latest-pre-tip player-team-games / at-risk / onsets | 248,730 / 180,829 / 12,710 | same | **248,728 / 180,831 / 12,707** |
| Wording mechanism, vague vs specific (player + season FE) | −8.42 [−23.96, 7.12], p = .288, N = 6,256 | −8.41672 | **−7.91 [−23.41, 7.60], p = .318**, N = 6,259 |
| Wording mechanism, player + team-season FE | −7.18, p = .387 | −7.18123 | **−6.63, p = .423** |
| Category FDR, explicit rest, national-partner | +0.62 pp, BH q = .050 | +0.61781, q = .0505 | **+0.62 pp [0.13, 1.10], BH q = .051** |
| Category FDR, explicit rest, linear-only | +0.70 pp, BH q = .018 | +0.70262, q = .0182 | **+0.70 pp [0.22, 1.18], BH q = .018** |
| Predeclared heterogeneity | none detectable after BH | smallest q .393 | none detectable, smallest q .400 |
| Latest-pre-tip joint pretrend | p ≈ .433 | .4327 | **p = .479** |
| Permutation placebo, two-sided p | .09 (partner), .26 (linear) | .09 / .26 | see the August report, stage 2 |
| Star wording counts, pre-reform | vague 370, other 35, unknown 43 | same | **vague 371, other 34, unknown 42** (one star onset removed, one reclassified) |
| Nonlinear logit DDD, national-partner / linear-only | 2.44 / 0.83 pp | exact to full precision | 2.03 / 1.28 pp, inside the solver's row-order spread (2.09 to 2.44 / 0.83 to 1.25 on unchanged data), so not a substantive change |
| Nonlinear vague vs specific, national-partner / linear-only | −5.42 / −4.43 | exact | −5.18 / −3.60, still negative |

Latest-pre-tip raw eight-cell TV triple: 2.428 → 2.476 pp. Pre-reform star at-risk and onsets on national-partner TV: 1,441 and 99 → 1,439 and 98.

## C. Not verified in this session

These manuscript numbers remain as published and are not reconciled, because their generating output was not located among the rerun scripts or was not rerun.
- NBA TV common-sample check (+1.88 → +0.83 pp, 2021-22 to 2024-25).
- Archived latest-pre-tip All-Star-only estimate (+3.12 pp, p = .018) and the archived latest-pre-tip stacked contrast (+1.61 pp, p = .171, N = 180,186).
- Season-by-season star and nonstar wording tables, other-wording components, and the nonstar team-cover table, beyond the class counts in section B.
- Figures 1 and 2 (the underlying onset cells are reproduced in section A).

## D. Proposed corrected-chronology text

If an updated paper adopts the corrected chronology, the main sentences would read as follows. Each would carry a footnote stating that two 2021-22 Toronto games were misdated in the archived schedule and that the published frozen estimates remain available.

- Abstract: "Compared with nonstars, star onset improves less in national-TV games than elsewhere by 2.67 percentage points (95% CI 0.09 to 5.26). This estimate falls to 1.28 points (95% CI −1.30 to 3.87) when streaming-only games count as non-TV."
- Section 5: "The decline in star onset relative to nonstars is 3.31 percentage points outside TV and 1.34 points on TV, giving a raw triple difference of 1.97 points. The adjusted estimate is +2.67 pp (95% CI [0.09, 5.26]; p = .043; N = 180,530)."
- Section 5.3: "The cadence-harmonized one-game estimate is 1.38 pp (95% CI [−0.27, 3.02]; p = .101; N = 180,087). ... A paired one-game-minus-longer-spell regression gives +1.64 pp (95% CI [−0.65, 3.92]; p = .160)."
- Section 6: "Using latest-pre-tip reports instead gives a national-partner estimate of 3.20 pp (p = .015) and a linear-TV-only estimate of 1.82 pp (p = .166)."

## E. Effect on interpretation

The corrected chronology moves the headline DDDs by about +0.044 pp (October) and +0.046 pp (August), roughly 3% of one standard error. The national-partner estimate stays just inside conventional significance, the linear-only estimate stays insignificant, the one-game home shift stays around p = .10, and the paired contrast stays uncertain. Pretrend and placebo tests stay null, and no heterogeneity or wording result changes. The manuscript's qualitative conclusions do not change. The only conventional threshold crossed is by the one-game home shift, whose p-value moves from .093 to .101 (All-Star-only version .093 to .100). The manuscript never calls this result significant and already describes it as uncertain, so its wording can stay.
