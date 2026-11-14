# October 2026: corrected-chronology sensitivity and archived-output reproducibility

> **Independently completed, November 8:** GitHub Actions [run 42516634023](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/42516634023) executed all ten released October scripts from the pinned shared repository in isolation and passed all **33** archived executable-CSV comparisons, with maximum absolute deviation **1.1457501614131615e-13**. This is a genuine fresh frozen-analysis replay. It is separate from the supplied external corrected-chronology October pass. Details: [independent CI evidence](../validation/october_corrected_chronology_2026-11-08/frozen_ci_independent_replay.json).

**As of November 8, 2026.** This is an *additive sensitivity*, not a rewrite of the original frozen August or October research results.

## Verification provenance and boundaries

The attached October corrected-chronology patch reports running the original ten October 2026 executable scripts twice on an immutable checkout of the shared research repository: once using the published frozen cadence panel, and once using the separately reconstructed corrected-chronology panel. It reports all **33 executable archived October output tables** matching the frozen rerun (maximum numerical discrepancy approximately 1.2168e-13), plus **704 coefficient comparison rows** from corrected and frozen analyses.

The original shared repository commit **0bd713d97e8d519df5700ef473da34aba4495223** was verified to contain all ten historical scripts and their archived outputs. The supplied result JSON, headline 24-row CSV, eight joint-test rows, and reported four collinear-control swaps were inspected for consistency. The updated working branch contains a more stringent reproducibility runner and an **independent frozen-only GitHub Actions job** that now executes the public archived scripts. The complete corrected Oct rerun itself was executed in the supplied external environment, not independently repeated in this ChatGPT environment.

**The source patch's claim that all sample sizes are identical needs qualification:** the main DDD and most headline models retain their N, but several event-time and event-window samples decrease by **9, 23, or 32 observations**. These changes are documented rather than concealed.

The shared repository's summary_estimates.csv is hand-authored, not an output of one of the ten executable scripts, so it is excluded from the 33-output reproducibility gate.

## Estimates reported in supplied corrected Oct rerun

| Analysis | Frozen estimate | Corrected chronology | Frozen p | Corrected p |
|---|---:|---:|---:|---:|
| National-partner TV DDD (full controls, N=180,530) | +2.63045 pp | **+2.67423 pp** | 0.04608 | 0.04263 |
| Harmonized linear-only TV DDD (full controls) | +1.23897 pp | **+1.28237 pp** | 0.34745 | 0.33087 |
| All-Star-only national partner | +2.98669 pp | **+3.03123 pp** | 0.02207 | 0.02023 |
| All-Star-only linear TV | +1.60968 pp | +1.65381 pp | 0.21621 | 0.20397 |
| One-game home/road shift (N=180,087) | +1.40600 pp | **+1.37799 pp** | 0.09349 | 0.10094 |
| Longer-absence home/road placebo | −0.25805 pp | −0.25982 pp | 0.71942 | 0.71764 |
| Return hazard, harmonized linear TV (N=50,370) | +4.95380 pp | +4.81175 pp | 0.14163 | 0.15510 |
| Return hazard, national-partner TV | +5.08288 pp | +4.94015 pp | 0.11060 | 0.12328 |

The supplied result set includes all 24 manuscript/headline/method-audit rows in [manuscript estimates comparison](../validation/october_corrected_chronology_2026-11-08/manuscript_estimates_frozen_vs_corrected.csv) and eight joint tests in [joint-test comparison](../validation/october_corrected_chronology_2026-11-08/joint_tests_frozen_vs_corrected.csv).

The 704-row source-patch coefficient comparison reports a maximum absolute coefficient movement of **0.70854 percentage points** in a noisy exploratory event-time model (standard errors approximately 5 pp). Four rows are intentionally not interpreted as numerical effects because the perfectly collinear games-before-10 and distance-from-65 regressors swap which one is retained by the solver.

### Joint tests

- Event-window repair/return test, harmonized linear TV: χ²(6) = 15.64, p=0.01579 → χ²(6) = 14.81, p=0.02178, N=22,151 → 22,142.
- Event-window repair/return test, national-partner TV: χ²(6) = 12.26, p=0.05633 → χ²(6) = 11.42, p=0.07610, N=23,713 → 23,704.
- Joint pretrend remains null: linear p=0.61584 → 0.65881 and partner p=0.61615 → 0.65914. Its N stays 180,530.
- Event-window onset samples shrink by 23 and prevalence samples by 32 under both national-TV definitions.

### Manuscript implications

If an updated paper adopts the scientifically corrected chronology, the main national-partner DDD becomes approximately **+2.67 pp [0.09, 5.26], p=0.043** and the linear-only estimate approximately **+1.28 pp [−1.30, 3.87], p=0.331**. The home/road one-game result becomes +1.38 pp, p=0.101, just beyond a conventional 10% significance cutoff. The October cadence onset count becomes **12,729**, previously 12,731; star onsets become **1,634**, previously 1,635. A decision about primary manuscript estimates must not be made on p-values alone; correcting demonstrably wrong report-game links is a data-integrity issue. The historical archived estimates should remain transparently available.

**Not rerun by these ten released scripts:** paired one-game-minus-longer contrast (frozen +1.66 pp, p≈0.154), descriptive onset/prevalence rates, raw triple difference (about 1.92 pp), spell-duration tables and figures. They require recovery and execution of their own upstream code before an updated manuscript can be considered complete.

## Separate August latest-pre-tip report error

I independently inspected the original **248,730-row** August analysis-ready panel in the preserved historical archive. Exactly **34 player-game rows** have a selected injury-report timestamp outside the 24-hour pre-tip screen, all for the two incorrectly dated February 2022 Toronto Raptors games: **16** Bulls–Raptors and **18** Heat–Raptors. **Nineteen** have a report timestamp after the original recorded tip. All 34 IDs match the supplied external audit exactly.

The problem is not simply a long acceptable pre-tip reporting window: report identities for these games include unrelated reports from October 2021 and April 2022. The October cadence-reconstruction fixes do NOT automatically fix these August latest-pre-tip and taxonomy outcomes. The independent screen is reproducible with scripts/data_rebuild/audit_august_base_report_links.py.

## Reproduce from immutable sources

The Oct shared repository must be a **clean detached checkout** at commit 0bd713d97e8d519df5700ef473da34aba4495223. Use Python 3.12 and requirements-october-lock.txt (pandas 3.0.5); **do not use this environment for the earlier cadence Stage-6 builder, which requires pandas 2.2.3**.

For independent archived-frozen reproduction in CI or locally:

    python scripts/data_rebuild/october_corrected_chronology.py \
      --shared-repo ../nba-ppp-star-availability \
      --work data_rebuild/output/october_frozen_only \
      --frozen-only

For the full corrected sensitivity, in a new work folder:

    python scripts/data_rebuild/october_corrected_chronology.py \
      --shared-repo ../nba-ppp-star-availability \
      --corrected-panel /absolute/path/to/corrected_chronology_panel.csv.gz \
      --work data_rebuild/output/october_corrected \
      --python /path/to/python3.12_october

The runner verifies the shared repository commit and clean tree, original frozen panel hash, and the independently reproduced **uncompressed** corrected panel SHA-256 (2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67). It fails on missing original outputs, nonmatching tables, unexpected coefficient-row count, missing corrected-run outputs, and nonzero executable returns. Results are written only into fresh isolated directories.

**PR #4 remains a draft.** The rest of full Level C, August upstream reconstruction, descriptive manuscript statistics and additional source-specific analyses remain open. The frozen original releases and manuscript were not overwritten.
