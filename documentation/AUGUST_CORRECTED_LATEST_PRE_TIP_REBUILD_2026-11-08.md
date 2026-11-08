# August 2026 latest-pre-tip source correction: original core, reviewed taxonomy and regression sensitivity


## Subsequent source-TV and category-FDR check

The historical advance-TV fixture table itself still has Bulls at Toronto keyed February 1 and Heat at Toronto keyed February 3. On the corrected 180,831-row August risk set a date/team merge with that unchanged table produces **46 unmatched rows** (24 Chicago, 22 Miami). Updating only the TWO source TV lookup date/UTC-tip keys to the real physical dates, while preserving original as-announced networks and release source lines, restores **180,831 matched** rows, no duplicate keys, no primary-TV disagreements. See [TV-source QA](../validation/august_corrected_latest_pre_tip_2026-11-08/advance_tv_source_date_key_audit.json). This is an advance-announcement assignment check, not a validation of live rescheduled-game broadcasts.

The four August mutually exclusive injury/absence onset categories were rerun for both original national-partner and harmonized linear TV using the historical player+team-season FE model, player/game clustering, and BH/Holm corrections within each four-test exposure family. Legacy explicit-rest corrected coefficient is **+0.61513 pp**, BH q **0.05097** (frozen q 0.05046), both just above 5%; harmonized explicit-rest **+0.69993 pp**, BH q **0.01840** (frozen q 0.01824), both below 5%. Other categories remain BH nonsignificant. Full report: [August category FDR](AUGUST_CATEGORY_FDR_CORRECTED_CHRONOLOGY_2026-11-08.md). The original exact release script has independently passed all eight frozen-model checks in GitHub Actions. Its corrected variant was computed locally with original-equivalent modeling and independently verified game-level TV joins; the new integrated original-executable corrected runner itself still requires one private-archive acceptance run.

**Audit date:** November 8, 2026  
**Working repository:** https://github.com/ahmetcopur/nba-load-management-ppp  
**Draft PR:** https://github.com/ahmetcopur/nba-load-management-ppp/pull/4  
**Scope:** A separate source-corrected sensitivity, not a replacement of the August 12 historical freeze.

## Source cause

The original 2021–22 schedule gives Heat at Raptors on February 1, 2022 and Bulls at Raptors on February 3, 2022. The later archived February game identifiers/date encodings were transposed. An August builder workaround mapped all 2021–22 report rows for these matchups to the February games, pulling **17 source report rows** from unrelated October 25 and April 3 Toronto matchups. A separate frozen August panel audit identified **34 player-game report-to-tip timing anomalies**. Those numbers describe distinct upstream and derived objects.

The source correction keeps October match 46 and April match 1172 with their own reports and remaps only February source matches 430 (Miami, Feb 1) and 784 (Chicago, Feb 3). Exact date-encoded frozen game identifiers were retained only for side-by-side row comparisons; the official source match numbers and UTC tip times were corrected.

## Exact August core reproducibility gate

Original source ZIP SHA-256 values:

| Source ZIP | SHA-256 |
|---|---|
| nba_player_game_at_risk_core_v1.zip | a0f82ebcf6117554a4ce1064ab79db9cf93acc5a53fa25000343810843e659f6 |
| nba_game_covariates_v1.zip | 4351756b74446577dabc8418b539c95dfb6e0ae6e3d8766bbee1c528d709c224 |
| nba_boxscore_roster_frame_v2_output_upload.zip | 45eeade023037506d1b07ebc601c273ec442f6620adc3ab836a3d40b8774f561 |
| nba_player_game_analysis_ready_v1.zip | a3d991bdaf41cbdba734abbd43853b495b27fbb96576743259413fcd50eb9155 |

Historical original August finalizer executable SHA-256: a0271f01f551dbbe1abedfac7ca8fefb9c865cd9b58a33185a3b7cbc991f8bfc.

After redirecting only the historical absolute input root to a clean archive staging area, the original finalizer produced an **exact byte match after gzip decompression** to the archived original August core: SHA-256 253bf017095a8be45f4c7bb4a0abcc9b942a8db6311f91131c9fd12c7ab46de3. Only after that baseline passed did the same historical finalizer run on corrected source dates, report links, team-game statuses, per-game roster data, original Elo/rest/travel covariates and chronological playing histories.

| August core quantity | Frozen | Corrected source-sensitivity |
|---|---:|---:|
| Player-team-game rows | 248,730 | **248,728** |
| Report-only roster additions | 159 | **157** |
| At-risk player-games | 180,829 | **180,831** |
| New absence onsets | 12,710 | **12,707** |
| Observed spells | 13,723 | **13,718** |
| Missing game covariates | 0 | 0 |
| Duplicate player-game identifiers | 0 | 0 |

Exactly two erroneous report-only player-game records disappear: **Devon Dotson** and **Javonte Smart**, inadvertently introduced via unrelated game injury reports. Within common keys, **32 report designation statuses**, **12 onset-risk flags**, **3 onset flags**, and **2 absence-now flags** change. Three pre-policy new onsets disappear: **Kyle Lowry**, **Khem Birch**, and **Yuta Watanabe**. Official national TV remains unchanged: February 1 Miami at Toronto was TNT; February 3 Chicago at Toronto was not national-partner TV.

## Reviewed v2 taxonomy and analysis-ready sensitivity

The archived v2 reviewed official injury reason-to-class mapping was reconstructed and verified against all **248,730 historical frozen player rows**, with zero class or onset-type disagreement, zero conflicting historical reason classifications, and 2,182 known reviewed reason keys. All corrected active reasons are already represented in this historical reviewed dictionary; the tool rejects any unseen reason rather than silently inventing a diagnosis.

The source-corrected reviewed full panel contains **248,728 rows and 125 columns**. The corrected model risk subset has **180,831 rows**. Relative to shared frozen keys, **18 reviewed class cells and 18 reviewed onset-type cells** differ.

Historical full reviewed panel decoded SHA-256: 5154317fc52157716cf22f7c5a535259e9f073b3391fd52d78a01faaf8d96d77. Corrected full panel decoded SHA-256: 2acd7448a357163951700c99df33a6949e20b19afc2219e6f8c3082b14d3619d. Corrected model risk set decoded SHA-256: 5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3.

**Limits:** All historical award/star and NBA Cup flags are inherited by stable player-team-game key, not independently regenerated from original award and Cup releases. Two historical game identifiers still embed erroneous dates for comparison only. Neither the complete six-season source pipeline nor a new independent human review of taxonomy was performed.

## Published August model anchors versus source-corrected results

Three published August specifications were independently reimplemented from their original released definitions: two primary player + team-season fixed-effect DDD models (national-partner and harmonized linear TV) and the conditional vague-versus-specific injury description model with player + season fixed effects. Two-way SE clustering is by player and physical game.

The frozen coefficient and sample count for each of the three match the released source to numerical precision. The independent runtime's clustered standard errors differ from the historical release by at most **0.000636 percentage points**, so **exact byte-for-byte published statistical output replication is NOT claimed**. The independent GitHub Actions frozen-model job checks these gates on the original public data.

| Model | Published original estimate | Corrected estimate | Original N → corrected N | Corrected p |
|---|---:|---:|---:|---:|
| National-partner TV, full controls | **+3.149256 pp** | **+3.195511 pp** | 180,695 → **180,697** | **0.01519** |
| Harmonized linear-only TV, full controls | +1.774657 pp | **+1.820402 pp** | 180,695 → **180,697** | **0.16582** |
| Conditional vague versus specific injury wording | −8.416721 pp | **−7.906071 pp** | 6,256 → **6,259** | **0.31756** |

Corrected national-partner 95% CI: **[+0.616, +5.775] pp**; harmonized linear-only CI: **[−0.754, +4.395] pp**; injury wording CI: **[−23.410, +7.598] pp**. Qualitative conclusions do not reverse. The main latest-pre-tip national-TV interaction rises by approximately +0.0463 pp, small next to its ~1.32 pp clustered standard error.

These August latest-pre-tip models are not the October cadence-harmonized headline specifications (+2.63045 frozen → +2.67423 pp corrected). Keep both timing constructions separately identified.

## Reproducibility files and commands

New scripts in this PR:
- scripts/data_rebuild/rebuild_august_core_from_source_archives.py — exact original finalizer baseline, source match/date corrections and re-run of same original executable.
- scripts/data_rebuild/build_august_analysis_ready_sensitivity.py — verified historical reviewed-class baseline, safe taxonomy transfer and analysis-ready/full model risk outputs.
- scripts/data_rebuild/run_august_preferred_model_sensitivity.py — frozen 3-model coefficient and N gate with explicit SE-tolerance, then corrected regressions.
- tests/test_august_reviewed_taxonomy_transfer.py and tests/test_august_preferred_model_sensitivity.py — negative tests for unknown/conflicting reasons, wrong keys, coefficients, N and numeric SE tolerances.
- validation/august_corrected_latest_pre_tip_2026-11-08 — source and model SHA/QA summaries, no raw licensed NBA files.

Representative commands with separate output roots:

    python scripts/data_rebuild/rebuild_august_core_from_source_archives.py \
      --archives /path/to/original_zip_archive_folder \
      --output-root data_rebuild/output/august_core_new

    python scripts/data_rebuild/build_august_analysis_ready_sensitivity.py \
      --historical-core data_rebuild/output/august_core_new/baseline/nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz \
      --corrected-core data_rebuild/output/august_core_new/corrected_source/nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz \
      --analysis-ready-zip /path/to/nba_player_game_analysis_ready_v1.zip \
      --output-dir data_rebuild/output/august_reviewed_new

    python scripts/data_rebuild/run_august_preferred_model_sensitivity.py \
      --corrected-panel data_rebuild/output/august_reviewed_new/player_game_panel_analysis_ready.csv.gz \
      --output data_rebuild/output/august_models_new.json

The original finalizer and local corrected variant, original reviewed taxonomy baseline, and three-model refits were independently exercised and checked. The **newly committed integrated production CLI itself has not yet been separately executed end-to-end** on an entirely fresh private archive root. Passing its unit tests and equivalent local staging steps is not a substitute for this last acceptance gate.

## Remaining work before paper-level completion

1. Execute the three committed production scripts as one chain from fresh original archives; validate byte-verified baseline, exact corrected counts, changed player identities, official report source provenance and model outputs.
2. Recover true official physical-game identifiers for both misdated February fixtures rather than retaining the old date-encoded alignment IDs; independently regenerate award/star, Cup and advance national-TV source classifications where necessary.
3. Rerun the complete August research suite beyond these three estimators, including placebo/pretrend, categorical mechanisms, nonlinear/heterogeneity and original latest-pre-tip descriptive tables and figures, each against published frozen anchors first.
4. Complete original six-season PDF and schedule/TV source-to-final Level C, then reconcile all manuscript numbers and figures transparently. Do not select preferred variants based on a p-value change.

**PR #4 remains an unmerged draft. The historical August/October frozen data and paper are unchanged.**
