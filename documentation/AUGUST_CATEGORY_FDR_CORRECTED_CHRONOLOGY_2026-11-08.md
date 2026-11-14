# August category-specific onset sensitivity after the Toronto game-date correction

**Research status: November 8–9, 2026.** This is a separate August latest-pre-tip sensitivity, not a replacement of the historical August or October paper. Draft PR: https://github.com/ahmetcopur/nba-load-management-ppp/pull/4

## The additional advance-TV source problem

The original six-season release-TV fixture table is keyed to **Bulls at Toronto on February 1, 2022** and **Heat at Toronto on February 3, 2022**. The games actually took place **February 3 (Bulls)** and **February 1 (Heat)**, respectively. The archived TV table records Bulls without national TV and Heat with TNT based on their original advance-announced network assignments. Those *game-specific release-time assignments* are intentionally retained; this does not establish which network carried the rescheduled game live.

An unmodified date/team TV join leaves **46 of 180,831** corrected August at-risk player-game rows unmatched (24 Bulls, 22 Heat). This is unacceptable for reproducing the original published category analysis. Correct only these two source lookup rows' game_date_et and tip_utc, keeping their original network_announced, announced_tv_primary, source lines and all other release metadata. I independently checked that this repairs the join to **180,831/180,831** matched rows, with **zero** TV exposure mismatches and no duplicate keys. The original public TV source remains untouched; a copied source table is used for the sensitivity.

## Original four-outcome category FDR model

Original unchanged script: scripts/portable/run_category_fdr.py at shared commit 0bd713d97e8d519df5700ef473da34aba4495223. Original archived benchmark: results/category_focal_fdr.csv.

Four distinct outcomes are vague-injury onset, specific-injury onset, explicit-rest onset, and other-absence onset. There are two announcement-TV exposure definitions: legacy primary partner and harmonized linear. For each TV definition the family of **four** category tests receives separate Benjamini–Hochberg FDR and Holm corrections; the primary overall-absence endpoint is not included in this family. Original specification includes player and team-season fixed effects, 16 controls including distance to 65, and two-way standard error clustering by player/game.

The original frozen release has **180,695** complete-case model rows; the corrected August risk panel has **180,697**. All eight archived frozen coefficient and adjusted-p benchmarks reproduce in the independent local numerical implementation. The separate GitHub Actions job executes the exact original released source and checks eight frozen specifications using explicitly bounded cross-environment numeric tolerances.

### All eight corrected August category estimates

| Announced-TV exposure | Outcome | Frozen interaction (pp) | Corrected interaction (pp) | Corrected unadjusted p | Corrected BH q | Corrected Holm p |
|---|---|---:|---:|---:|---:|---:|
| Legacy national partner | Vague injury | +1.5912 | +1.5970 | .07048 | .14097 | .21145 |
| Legacy national partner | Specific injury | +0.5607 | +0.5416 | .37585 | .50113 | .75170 |
| Legacy national partner | **Explicit rest** | +0.6178 | **+0.6151** | .01274 | **.05097** | .05097 |
| Legacy national partner | Other absence | +0.3796 | +0.4418 | .50960 | .50960 | .75170 |
| Harmonized linear | Vague injury | +1.0156 | +1.0213 | .25246 | .50492 | .75738 |
| Harmonized linear | Specific injury | +0.1094 | +0.0897 | .88230 | .98864 | 1.00000 |
| Harmonized linear | **Explicit rest** | +0.7026 | **+0.6999** | .00460 | **.01840** | .01840 |
| Harmonized linear | Other absence | −0.0529 | +0.0095 | .98864 | .98864 | 1.00000 |

The legacy-primary explicit-rest BH q is **0.05046 frozen versus 0.05097 corrected**: both are just above 0.05. Harmonized linear explicit-rest q is **0.01824 frozen versus 0.01840 corrected**, below 0.05 in both cases. Neither vague nor specific injury nor other absence becomes BH significant. This is a stable descriptive association, NOT proof of a causal policy-induced reporting mechanism. The explicit-rest category is rare and subject to floor-effect warnings.

Unrounded eight-model coefficient, sample, SE and BH/Holm comparison:
validation/august_corrected_latest_pre_tip_2026-11-08/category_fdr_full_corrected_vs_frozen.csv

## Provenance and reproducibility

The corrected risk input was rebuilt from the original source archives through original August finalizer, original covariate builder and historically reviewed taxonomy mapping. The corrected gzip-decoded risk CSV has SHA-256 **5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3**. The original frozen model-risk CSV has decoded SHA-256 **d6e82ba61d99fb27ec4877b1c0b05fed76c5cb8fa4bf5b6322742b7049ae9635**.

An independent local reimplementation executed all eight frozen and corrected specifications and recomputed both multiplicity adjustments. It also verified both TV families using the original release-time network attached by physical game ID instead of the incorrect original date keys.

The integrated script scripts/data_rebuild/run_august_category_fdr_from_release.py now directly executes the UNCHANGED original historical category-FDR script, first on published frozen inputs and then on a separate corrected-panel sensitivity with exactly the two TV source lookup keys re-dated. The public frozen-only branch is reproducible in GitHub Actions; the corrected branch requires the local source-derived input, which is not published to the repo. **Do not claim the newly integrated corrected original-executable CLI itself has already been executed inside GitHub Actions.**

Frozen-only command from a clean pinned original shared checkout:

    python scripts/data_rebuild/run_august_category_fdr_from_release.py \
      --shared-repo ../nba-ppp-star-availability \
      --work /new/output/august_category_frozen \
      --frozen-only

Full corrected branch with locally rebuilt, checksum-verified 180,831-row risk input:

    python scripts/data_rebuild/run_august_category_fdr_from_release.py \
      --shared-repo ../nba-ppp-star-availability \
      --corrected-panel /path/to/august/corrected_model_at_risk.csv.gz \
      --work /new/output/august_category_corrected

Under the pinned October/analysis Python environment, the exact original model outputs may differ from old frozen SE by a few millionths of a percentage point. Benchmarks require coefficient difference below 1e-8 pp, SE/CI difference below 0.001 pp, and p/FDR/Holm difference below 1e-4. Report actual deviation rather than pretending outputs are byte-identical.

## Remaining limitations

This is **August latest-pre-tip**, not October cadence. Original star/award and Cup flags remain inherited from the frozen panel; two stable game IDs retain old date-encoded strings for comparison. All-original-source award/Cup/TV game-identity correction, full August placebo/heterogeneity/nonlinear suites, manuscript and figure reconciliation, and six-season raw-report PDF Level C are still outstanding. Leave PR #4 a draft and keep original research freezes unchanged.
