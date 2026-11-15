# Scientific-integrity audit — November 15, 2026

**Scientific freeze is blocked by a verified star-classification defect, not by a failed hash check.** The accepted panel and its four regressions reproduce numerically, but the October builder incorrectly promotes some nonstars in its report-only roster branch. This AI-assisted computational review is not external independent human approval.

Reviewed implementation: `31fcef0d32bf88233c7dd994307c64ee2b4d3777`. Current manuscript: private `NBA_PPP_Manuscript.pdf`, November 13 version; its exact digest is in [review scope](../validation/scientific_integrity_audit_2026-11-15/review_scope.json). The older October 25 paper is historical, not the version used for the discrepancy register. Frozen files, original programs, model definitions and manuscript were not changed.

## 1. Material finding: the declared star rule is not implemented for all rows

[Original builder lines 227–235](../scripts/executed/06_cadence_harmonized_identification/build_harmonized_panel_and_models.py#L227) copy the correct opening-night and current-season-selection flags into report-only additions, but then calculate:

```python
opening or (pd.notna(eff) and gd >= eff)
```

The second branch omits **current-season All-Star selection**. The calendar supplies an effective date for nonstars too. Merely passing that date therefore turns them into stars. This violates both the manuscript's stated definition and the [NBA policy definition](https://pr.nba.com/nba-board-of-governors-approves-player-participation-policy).

A complete join to the SHA-pinned original 6,750-row player-season calendar found **49 erroneous flags, all report-only rows**. Twelve are at-risk onsets: nine pre-policy and three post-policy. There are no missing calendar identities. The other 248,729 panel rows agree with the calendar rule. [Failing semantic check](../validation/scientific_integrity_audit_2026-11-15/star_definition_check.json) records aggregates and input digests; it contains no newly published player records.

A separate RAM-copy sensitivity applied the declared predicate `opening or (current_selection and date >= effective_date)`. It changed only the star indicator, not absences, risk eligibility, game identities, controls or sample size. This is an audit variant, **not a newly accepted final dataset**:

| Specification | Legacy estimate (pp) | Star-rule variant (pp) | Variant SE | Variant p | N |
|---|---:|---:|---:|---:|---:|
| National-partner, full | 2.674232 | 3.063532 | 1.302400 | .018662 | 180,530 |
| Linear-only, full | 1.282369 | 1.661214 | 1.302885 | .202299 | 180,530 |
| National-partner, none | 2.676885 | 3.064284 | 1.309969 | .019325 | 180,664 |
| Linear-only, none | 1.294851 | 1.671870 | 1.311584 | .202417 | 180,664 |

The full-control national estimate moves by **0.3893 pp**, about 15% of its legacy value. The direction and broad sensitivity to TV coding persist, but the published numerical claim is affected. A more significant p-value does not justify choosing a definition; the predicate was identified from the written eligibility rule before the sensitivity results were inspected. [All variant models](../validation/scientific_integrity_audit_2026-11-15/star_rule_sensitivity.json).

The minimum repair is a separately versioned one-predicate scientific correction, followed by an actual October-builder execution using authenticated retained source-stage inputs. Refresh affected star-stratified results and assign new scientific-version hashes only after review. Keep all historical targets and artifacts intact. Do not repeat 23,483 PDF parses merely to change this downstream predicate.

## 2. Identification: defensible observational comparison, not an isolated PPP effect

The policy starts with 2023–24. The three earlier seasons are pre-period; 2023–24 through 2025–26 are post-period. The main exposure is announced national-partner TV, with a same-sample linear-only alternative. The fitted coefficient is on **star × post × TV**, with all estimable lower-order interactions, player effects, team-season effects and the listed controls. Team-season effects absorb the common post main effect; its absence as a separate regressor is appropriate.

A positive coefficient means the star/nonstar change is more positive for absence onset on TV than off TV, conditional on the specification. It is not a direct estimate of the overall policy effect or proof of successful TV enforcement. Non-TV stars are still subject to the wider policy; Cup games also receive policy protection; nonstars may respond through substitution. These groups are not randomized untreated controls.

Identification requires the untreated star/nonstar TV differential to have evolved comparably across periods. TV scheduling, star eligibility, roster composition and injury/reporting processes can change endogenously. The award minimum and Cup start in the same season; pandemic-era pre-seasons and the 2025 broadcast expansion add substantial composition differences. Fixed effects do not remove differential star-TV shocks. Prior workload/games-played controls can also be affected by the policy, so the full-control regression is not automatically a total causal effect.

The current manuscript sections 4.4 and 6 already acknowledge much of this correctly. Keep those qualifications. Corrected legacy pretrend p≈.659 and pre-period placebo p≈.537/.895 do not establish parallel trends or adequate power. See [recorded joint tests](../validation/october_corrected_chronology_2026-11-08/joint_tests_frozen_vs_corrected.csv). The identification logic follows [Olden and Møen](https://doi.org/10.1093/ectj/utac010); serial-dependence concerns are illustrated by [Bertrand, Duflo and Mullainathan](https://www.nber.org/papers/w8841). Neither reference establishes that the necessary assumptions hold in these NBA data.

## 3. Estimation and uncertainty independently checked

A separate group-projection implementation residualized the accepted panel to a maximum group mean below 1e-10, then estimated OLS and two-way player/game covariance. All four sample sizes match. Maximum differences from original executed outputs were approximately **2e-14 pp for coefficients, 1.35e-10 pp for SEs, 2.65e-10 pp for interval limits and 4.22e-11 for p-values**. This is numerical agreement, not byte identity; the independent algorithm's iteration/runtime metadata differ. [Numerical checks](../validation/scientific_integrity_audit_2026-11-15/independent_numeric_checks.json).

The LPM interaction is directly in probability units; multiplying by 100 gives percentage points. The code uses normal-reference two-sided p-values and beta ±1.96 SE intervals. This implementation is consistent with its stated convention, rather than an exact small-sample inference guarantee.

Player/game clustering captures repeated-player dependence and within-physical-game shocks. It does not cover every shared team/time disturbance. On the unchanged legacy full-control model, supplemental player/calendar-date clustering gives national p=.04749 (940 date clusters), and player/team-season gives p=.03349 (180 clusters); linear-only remains nonsignificant. These are limited exploratory covariance diagnostics, not preferred replacements or proof against all dependence. No broad model search or bootstrap campaign was conducted.

There is exact design redundancy: `dist_to_65 = 65 - games_played_before_game`. After fixed-effect removal, full X has rank 21 for 22 columns. Removing the redundant column changes fitted values by less than 1e-15 and leaves the focal coefficient unchanged; a tiny covariance finite-sample correction changes. Individual coefficients on the two redundant terms are not separately identified. Their joint inclusion does not account independently for award incentives. Also, appearances are not the CBA's full minutes-qualified award-eligibility counter; this control must be described as a proxy, not a verified eligibility margin.

The current paper explicitly disclaims preregistration. Nominal p-values must not be presented as family-wide discovery control. BH correction within specified event-time/category families is not correction over the whole study. The two TV definitions overlap heavily, so neither independence nor a statistically significant difference between their coefficients follows from one p-value being below .05. Wide mechanism intervals do not establish no relabeling or retiming. The current paper generally phrases these null results appropriately.

## 4. Outcomes, risk sets and time integrity

Independent calculation found zero discrepancies in the implemented onset/risk formulas, zero post-period indicator discrepancies, and no duplicate player-team-game keys. There are 207 report-only rows. Recorded selected player-report timestamps are all strictly before actual tipoff; team lead times are nonnegative. These checks validate the saved timestamps, not unavailable historical acquisition observations.

The outcome uses nonparticipation combined with an Out report, specified boxscore absence reasons, or inactive status, excluding the coach-decision/active-without-reason convention. It covers injuries, illness and some nonmedical absences; it is not a medically validated injury or discretionary-rest measure. A return means leaving this coded absence state, not clinical recovery.

Risk requires a usable **current** report, a consecutive prior roster observation within player-season-team, and previous coded nonabsence. Trades/reentry and the first observed game reset eligibility. Of the risk observations, **798 follow a prior roster game without a usable injury report**; prior availability can still be inferred from its boxscore. The manuscript should specify that detail rather than implying both reports are required. Conditioning on current report availability and prior availability defines a selected hazard population. Cadence harmonization does not remove all roster/report-selection or reporting-behavior differences.

An additional narrow measurement concern is documented: eight rows represent four same-player/physical-game pairs on different teams. This is allowed by the declared player-team-game identity. All have zero current-game minutes. Reordering the tied records changes six prior-ten-row workload values, two in the risk set. Thus this is **row-order dependence/current-row counting**, not observed leakage of future played minutes. Clarify the intended physical-game versus roster-row window in the new scientific version; it does not justify deleting valid team records.

The Toronto chronology correction preserves old key strings for compatibility while correcting actual tip/date fields, report links and derived histories. Do not read dates from the key strings. The source TV validator explicitly retains the 90 original Cup-TBD matchups as not announced instead of backfilling later opponents. Original postponement mappings, neutral-site designations and announcement clocks retain declared provenance limits. The star timeline normally respects prior-three-season awards and post-All-Star activation; the report-only exception in section 1 is the verified failure.

The original Elo code uses pre-update own/opponent ratings and only then applies results. Its cross-team rankings are updated between tip-time groups; without end-time metadata, strict real-time availability of every rank input is not established for overlapping games. No new outcome-leak claim or release blocker is inferred from that timing question alone. The existing no-Elo sensitivity applies to the legacy specification, not proof of every historical timestamp.

## 5. Human labels and genuine execution evidence

The separate `NBA_Coding_Agreement.zip` was retrieved and its original supplied label columns independently rescored: **260/300 agreement, κ=.834881321**. This supports the manuscript's arithmetic. Independence/blinding rests on the archive's owner attestation; coder identities/completion dates are absent. This was a development sample, not held-out validation or medical truth. The older Claude 300/300 exercise is distinct. The incomplete 203-description adjudication mainly limits category-specific claims, not the all-cause onset definition; it must not be represented as completed.

The archived six-season evidence has 14 ordered stage events for seven finished stages, all successful. Frozen and corrected October receipts record all 18 generated file opens and unchanged hashes. Direct decompression of all three archived final panels reproduces the accepted digests. Their four original model outputs also agree with the independent refits. [Evidence check](../validation/scientific_integrity_audit_2026-11-15/execution_evidence_check.json).

This audit did not rerun the full source pipeline or reobserve all 26 original source ZIPs. It checked the retained output bytes, receipts and available pinned inputs. Historical authentic PDF execution remains evidence of **conditional computational reproduction**. The original JSON cache was verified in earlier separate runs; no authentic combined six-season PDF+JSON run is established. Inherited crosswalks, covariates, enrichments, review decisions and original clock metadata remain declared inputs, not magically regenerated by matching final hashes.

The established 2025 two-field metadata exception remains separate: its controlled experiment found no effect on the tested panels/models. The newly discovered star error is a different code path and supplies no contradictory evidence about that experiment. Preserve historical-artifact and numerical-output verdicts, and add the new failing semantic verdict; do not relabel an old computational pass as scientific validation.

## 6. Decision and stopping point

[Findings register](../validation/scientific_integrity_audit_2026-11-15/findings.json), [manuscript register](MANUSCRIPT_AUDIT_2026-11-15.md), [publication review](DATA_PUBLICATION_REVIEW_2026-11-15.md), [reviewer guide](PR4_SCIENTIFIC_REVIEWER_GUIDE.md), and [release decisions](RELEASE_SCOPE_DECISION_2026-11-15.md) contain the remaining actions.

Do not freeze the scoped scientific release with an undisclosed known eligibility error. Repair that branch in a separate scientific version, validate the small workload-history ambiguity, refresh affected outputs/manuscript with approval, resolve publication permissions, and obtain independent human review. Additional primary-source reconstruction is not a prerequisite for a transparently scoped Release A unless it changes a scientific conclusion. Keep PR #4 draft, Issue #5 open, and historical evidence intact.
