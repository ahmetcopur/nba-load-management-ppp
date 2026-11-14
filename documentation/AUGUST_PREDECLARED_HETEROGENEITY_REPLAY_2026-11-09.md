# August predeclared heterogeneity: independent frozen replay and corrected-chronology runbook

**Status date:** November 9, 2026  
**Draft development PR:** https://github.com/ahmetcopur/nba-load-management-ppp/pull/4  
**Published source:** OEKundakcioglu/nba-ppp-star-availability at pinned commit 0bd713d97e8d519df5700ef473da34aba4495223.

## What is independently verified

The *original, unchanged* released script scripts/portable/run_predeclared_heterogeneity.py was run by GitHub Actions on the original August 180,829-row at-risk data, and its eight published four-way interaction results were compared against the archived results/heterogeneity_results.csv.

[Independent GitHub Actions run 42565348218](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42565348218) **passed the heterogeneity job**. All eight unique specification keys and subgroup/model sample counts match. The maximum coefficient deviation was **2.75e-14 percentage points** (across the subgroup effects), the maximum two-way clustered SE deviation **1.44e-5 percentage points**, and the largest BH q-value deviation **2.55e-6**. No claim of byte-identical archived standard errors is made across numerical environments.

The new integrated runner scripts/data_rebuild/run_august_heterogeneity_from_release.py stages the published script unmodified, checks the immutable source commit and original decoded risk-panel SHA-256, runs all original models and enforces all eight published statistical/numerical benchmarks before considering any corrected variant. Its synthetic tests reject changed subgroup hypotheses, missing tests, changed sample sizes, changed coefficients and excessive p/q drift. Scientific hypothesis definitions and multiple-testing families remain unchanged.

## Original hypotheses and published frozen results

The primary heterogeneity parameter is the formal four-way Star × PostPPP × announced TV × H interaction, comparing the H=1 and H=0 DDDs. **It is not the p-value for the effect estimated within H=1.** The original four predefined heterogeneity dimensions are:

1. **Back-to-back:** current game is the second game of a back-to-back.
2. **Weak opponent:** opponent rated in the bottom quartile before tip.
3. **High recent workload:** prior ten roster-games' minutes meet or exceed the original season-specific 75th percentile, conditional on at least ten prior roster games.
4. **Near 65 games:** among players 0–15 played games from the 65-game threshold, H=1 means 0–5 short and H=0 means 6–15 short.

The release also proposed **age/career stage** but deliberately left it unestimated because no reliable age, debut-year or career-experience metadata existed in the archived panel. Never infer veteran experience from a six-season left-censored observation window.

| Predeclared H comparison | Frozen N | Legacy H1−H0 (pp) | Legacy BH q | Harmonized H1−H0 (pp) | Harmonized BH q |
|---|---:|---:|---:|---:|---:|
| Back-to-back | 180,695 | −5.484 | 0.393 | −6.247 | 0.441 |
| Weak opponent | 180,695 | +1.633 | 0.676 | +3.508 | 0.503 |
| High recent workload | 139,535 | +3.639 | 0.393 | +4.126 | 0.441 |
| Near 65-game eligibility | 22,443 | +5.330 | 0.393 | +2.143 | 0.672 |

Original raw eight-model source: results/heterogeneity_results.csv in the pinned shared research repository. Complete independently checked deviations and archival coefficients: validation/august_corrected_latest_pre_tip_2026-11-09/heterogeneity_original_frozen_ci_reproduction.json.

**No four-way interaction survives a 5% Benjamini–Hochberg correction** across the four predefined subgroup tests within either TV-exposure family. The positive legacy high-workload H1 subgroup estimate (about +3.88 pp, unadjusted subgroup p=.0176) does **not** demonstrate heterogeneity: the H1-minus-H0 interaction p=.2050 and BH q=.3927.

These tests remain observational and cannot isolate the NBA's 2023 PPP from the concurrent award-eligibility/Cup changes.

## Why the August corrected run must also fix original TV source keys

The separate August latest-pre-tip source-corrected dataset has **180,831** at-risk player-games. In the original six-season advance-announced TV table, Chicago at Toronto is keyed to February 1, 2022, and Miami at Toronto to February 3; the games actually occurred on February 3 (Chicago) and February 1 (Miami). A raw date/team join therefore misses 46 corrected player-game records, even though the game-specific historical national-TV release assignments remain known (Chicago non-national, Miami TNT).

The new runner reuses the independently tested game-identity TV source correction in run_august_category_fdr_from_release.py. It rekeys **only the two date/UTC-tip lookup columns** in a copied source-TV table while retaining the source's original announced network and metadata. It fails if any other game is unmatched, any original as-announced exposure changes, or either of the two original source rows cannot be uniquely identified.

The corrected private panel input is accepted only if its **decoded SHA-256 equals**
5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3.
The original historical at-risk decoded SHA-256 is
d6e82ba61d99fb27ec4877b1c0b05fed76c5cb8fa4bf5b6322742b7049ae9635.

The script recomputes season-specific workload quartile cutoffs from corrected observations using **the exact original procedure**, rather than freezing quartiles after the source sample changes. It does NOT add post hoc subgroups.

## Runbook

Use a clean checkout of the shared source at immutable commit 0bd713d97e8d519df5700ef473da34aba4495223. In the working PR clone use a separate Python 3.12 environment with requirements-october-lock.txt, consistent with the original release's relevant analysis packages.

First, reproduce public frozen results (already independently passed in CI):

    python scripts/data_rebuild/run_august_heterogeneity_from_release.py \
      --shared-repo ../nba-ppp-star-availability \
      --work data_rebuild/output/august_heterogeneity_frozen \
      --frozen-only

Second, execute **in a fresh output directory** with the private verified corrected August risk file:

    python scripts/data_rebuild/run_august_heterogeneity_from_release.py \
      --shared-repo ../nba-ppp-star-availability \
      --corrected-panel /path/to/august_corrected/player_game_panel_model_at_risk_analysis_ready.csv.gz \
      --work data_rebuild/output/august_heterogeneity_corrected

The output directory includes original-script logs and results; the corrected comparison writes august_heterogeneity_corrected_vs_frozen.csv and august_heterogeneity_replay.json. Neither original Git repository, official source archive nor historical frozen panel is changed.

## Work still open

**The corrected-panel heterogeneity numbers are not yet reported as independently verified.** The original private 180,831-row corrected August risk CSV was generated in an earlier local source-rebuild environment but is not present in the public GitHub repository or connected ChatGPT file search in this session. The integrated corrected-path command therefore has not been run. Do not invent corrected subgroup estimates, significance or subgroup sample sizes.

The separate age/career metadata collection, original August nonlinear/multinomial and permutation/pretrend suites, physical-game ID regeneration, independent award/star and Cup flags, and six-season raw PDF-to-paper Level-C reconstruction remain pending. The date-corrected August panel inherits frozen award and Cup indicators, so proximity-to-65 findings in particular must be interpreted as sensitivity results, not a fully reconstructed institutional incentive test.

**Keep PR #4 an unmerged draft and retain the original research freezes.**
