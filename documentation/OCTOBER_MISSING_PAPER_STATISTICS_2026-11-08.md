# Missing October 2026 manuscript statistics — independently reconstructed

**November 8, 2026.** This is an additive, separately named corrected-chronology sensitivity, not a replacement of the frozen October manuscript or source archives.

The independently executed replay in scripts/data_rebuild/rebuild_missing_october_paper_statistics.py recreates the four published onset/prevalence comparisons, 8 TV onset-risk cells, raw national-partner triple difference, 8 one-game home/road cells, censored-duration summary, and the missing paired one-game minus longer-spell regression. It first verifies the published frozen manuscript benchmark before comparing the corrected chronology.

| Statistic | Frozen manuscript | Corrected chronology |
|---|---:|---:|
| All new onsets | 12,731 | **12,729** |
| Pre-policy star new onsets | 826 | **825** |
| Pre-policy nonstar new onsets | 4,791 | **4,790** |
| Star pre-policy national-TV onset | 104/1,447 = 7.187% | **103/1,445 = 7.128%** |
| Nonstar pre-policy national-TV onset | 547/10,366 = 5.277% | **546/10,365 = 5.268%** |
| Unadjusted national-TV triple difference | +1.919907 pp | **+1.966524 pp** |
| Paired home one-game minus longer contrast | +1.664049 pp | **+1.637814 pp** |
| Paired 95% interval | [−0.622, 3.950] pp | **[−0.648, 3.924] pp** |
| Paired p-value | 0.153597 | **0.160212** |
| Star pooled absence prevalence pre | 3,093/10,925 = 28.31% | unchanged |
| Star pooled absence prevalence post | 3,350/12,194 = 27.47% | unchanged |

The unadjusted TV triple difference uses **all 180,664 onset-risk player-games**, not the adjusted complete-case sample. It is the post-minus-pre change in the star/nonstar gap on TV minus the corresponding gap off TV, and increases by **0.046617 pp**. Do not mistake it for the regression-adjusted national-partner DDD estimate of +2.67423 pp.

## Paired home/road regression

The previously missing paired contrast was recovered using the original released October home/road model's **same eligible 180,087 player-game records, nine home specification covariates, player/team-season/physical-game fixed effects and two-way clusters by player and game**. Its dependent variable is onegame minus longer on the *same* row, which correctly estimates the variance of the paired contrast. A naive subtraction of two separately computed standard errors would be wrong.

Frozen: coefficient **1.6640489535 pp**, standard error **1.1661649666 pp**, CI [−0.621634, 3.949732], p=0.1535968151. This reproduces the manuscript's +1.66 [−0.62, 3.95], p=.154.

Corrected: coefficient **1.6378139042 pp**, standard error **1.1662354115 pp**, CI [−0.648008, 3.923635], p=0.1602117927. Neither version demonstrates a statistically established difference between the one-game and longer-spell home/road effects.

## Completed spell durations

A spell begins at an observed onset and continues through consecutively numbered, observed, absent team-games. It is **completed only when the next consecutive team-game shows availability**; a missing observation, nonconsecutive next game, team/season boundary or no observed return censors the spell. Mean, median and one-game share use only completed spells; censored observed durations are lower bounds.

| Group | Period | Frozen onset/completed | Corrected onset/completed | Frozen mean | Corrected mean | One-game share frozen → corrected |
|---|---|---:|---:|---:|---:|---:|
| Star | Pre | 826 / 713 | **825 / 712** | 2.6297 | **2.6334** | 63.53% → 63.48% |
| Star | Post | 809 / 702 | 809 / 702 | 2.7037 | 2.7037 | 64.67% → 64.67% |
| Nonstar | Pre | 4,791 / 4,119 | **4,790 / 4,118** | 3.7424 | **3.7433** | 42.44% → 42.42% |
| Nonstar | Post | 6,305 / 5,590 | 6,305 / 5,590 | 3.6170 | 3.6170 | 46.62% → 46.62% |

The frozen counts, means and one-game shares **match the October manuscript's completed-spell table at displayed precision**. Pre-policy stars still have 113 right-censored onsets; pre-policy nonstars 672; post-policy censored counts stay 107 and 715. The correction removes one completed pre-policy spell in each group, not absence prevalence.

## One-game home/road raw rates

The manuscript's pre-policy **star road** one-game count changes 280/3,896 (7.19%) → **279/3,896 (7.16%)**. Pre-policy star home remains 173/3,844 (4.50%), post-policy road remains 257/4,405 (5.83%), and post-policy home 197/4,348 (4.53%). The pre-policy nonstar home count changes 861 → **860** out of 39,831; all other nonstar home/road one-game cells remain unchanged.

## Reproduction and scientific boundary

Script: scripts/data_rebuild/rebuild_missing_october_paper_statistics.py. Full independent local result file: october_missing_paper_statistics_replay.json, and committed summary: validation/october_missing_paper_statistics_2026-11-08/paper_statistic_deltas.json.

Use the released October Python environment (requirements-october-lock.txt), not the earlier pandas-2 Level-B builder environment. An exact decompressed frozen CSV SHA-256 and historical manuscript benchmarks are required before corrected estimates are calculated.

    python scripts/data_rebuild/rebuild_missing_october_paper_statistics.py \
      --frozen-panel data_intermediate/player_team_game_harmonized_cadence.csv.gz \
      --corrected-panel /absolute/path/to/corrected_chronology.csv.gz \
      --output data_rebuild/output/october_missing_paper_stats.json

CI omits corrected-panel and independently reproduces the frozen manuscript against the public pinned source. The 2020–26 full Level-C raw-source-to-manuscript process remains unfinished, especially August latest-pre-tip taxonomy and other manuscript figures. Original historical releases are not overwritten. The resulting observational estimates cannot identify the PPP separately from the concurrent 65-game award threshold and Cup changes.
