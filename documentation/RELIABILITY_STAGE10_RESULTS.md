# Stage 10 — Reliability / Repairable-System Extension

## Status

FROZEN after pre-specified primary analyses and event-time sensitivities.

Stages 1–9 remain unchanged. Stage 10 is an extension of the frozen empirical
pipeline and does not replace the original onset-based inferential results.

## Conceptual framework

Player availability is treated as a two-state repairable process:

- Available -> Absent: failure / new absence onset
- Absent -> Available: repair / return

The extension studies whether the 2023 Player Participation Policy changed not
only absence onset behavior but also return hazards, absence duration, and
transition timing around advance-announced national-TV games.

No result is interpreted as evidence of deceptive intent without independent
evidence of intent.

## Construction QA

Frozen full panel:
- player-team-game rows: 248,730
- players: 1,125
- team-games: 14,460
- unique player_team_game_id: yes

TV mapping:
- legacy TV team-games: 2,082
- harmonized-linear TV team-games: 1,880
- missing harmonized TV mappings: 0

Repair panel:
- repair-risk rows: 62,996
- primary non-left-censored repair-risk rows: 51,605
- returns to availability: 12,088
- raw return rate: 19.19%
- missing previous-spell metadata: 0
- continuing-spell ID mismatches: 0

Duration panel:
- observed non-left-censored onset spells: 12,710
- completed: 11,247
- right-censored: 1,463
- completed one-game spells: 5,269
- completed <=2-game spells: 7,072

Event-window QA:
- legacy anchors: 2,082
- harmonized anchors: 1,880
- isolated legacy anchors: 246
- isolated harmonized anchors: 250

## Primary repair-hazard results

Outcome:
Return to availability conditional on being absent in the immediately preceding
consecutive team game and belonging to a non-left-censored absence spell.

Primary legacy-TV DDD:
+5.450 pp
SE 3.159 pp
95% CI [-0.742, 11.642]
p = 0.0845
N = 51,605

Harmonized-TV sensitivity:
+5.279 pp
SE 3.323 pp
95% CI [-1.235, 11.792]
p = 0.1122
N = 51,605

Played-return sensitivity:
- legacy: +5.512 pp, p = 0.0815
- harmonized: +5.800 pp, p = 0.0775

The raw cells show that the positive repair DDD is driven primarily by relative
deterioration in star repair probabilities on non-TV games rather than a large
absolute post-PPP increase in star return probability on TV games.

## Injury-category repair analyses

Pre-specified secondary subgroup estimates:

Vague spells:
- legacy: -9.558 pp, p = 0.1015
- harmonized: -10.163 pp, p = 0.1002

Specific spells:
- legacy: +10.110 pp, p = 0.0160
- harmonized: +9.054 pp, p = 0.0573

A direct specific-minus-vague contrast was estimated after observing the
subgroup divergence and is therefore exploratory/post-hoc:

- legacy: +19.669 pp, SE 7.352, p = 0.0075
- harmonized: +19.218 pp, SE 7.867, p = 0.0146

The contrast is hypothesis-generating and is not treated as a pre-specified
confirmatory test.

## Short-spell analyses

Exactly one-game spell when next game is TV:
- legacy: +1.693 pp, p = 0.7891
- harmonized: +1.496 pp, p = 0.8260

<=2-game spell when a TV game occurs within the next two team games:
- legacy: +3.540 pp, p = 0.4763
- harmonized: +2.931 pp, p = 0.5774

These analyses provide no evidence that approaching national-TV games generated
more very short star absence spells post-PPP.

## Nearest-TV event-time analysis

Event window:
-3, -2, -1, 0, +1, +2, +3 team games relative to the uniquely nearest
advance-announced TV game.

Equal-distance ties are excluded.

Joint tests of event-time heterogeneity:

Onset:
- legacy p = 0.5377
- harmonized p = 0.6761

Absence prevalence:
- legacy p = 0.6549
- harmonized p = 0.7085

Repair:
- legacy p = 0.0865
- harmonized p = 0.0281

No return spike is observed at event time 0.

An apparent repair decline at +3 relative to event time 0 appears in the
nearest-TV specification:

Legacy:
- delta(+3 vs 0) = -14.655 pp
- p = 0.0155
- within-model BH q = 0.0929

Harmonized:
- delta(+3 vs 0) = -16.440 pp
- p = 0.0075
- within-model BH q = 0.0449

## Event-time robustness

### Isolated TV anchors

Legacy:
- delta(+3 vs 0) = -2.627 pp
- p = 0.8704
- BH q = 0.9801
- joint event-time p = 0.9999

Harmonized:
- delta(+3 vs 0) = -12.159 pp
- p = 0.4227
- BH q = 0.9380
- joint event-time p = 0.7292

### Inverse-overlap-weighted stacked windows

Legacy:
- delta(+3 vs 0) = -10.071 pp
- p = 0.0145
- BH q = 0.0872
- joint event-time p = 0.1343

Harmonized:
- delta(+3 vs 0) = -10.643 pp
- p = 0.0166
- BH q = 0.0998
- joint event-time p = 0.1604

The +3 feature therefore does not satisfy the pre-specified robustness standard
across event-window constructions and is not treated as a robust substantive
finding.

## Frozen Stage-10 interpretation

Treating player availability as a repairable two-state process reveals
suggestive heterogeneity in the return transition but does not uncover a robust
short-maintenance signature around advance-announced national-TV games.

The post-PPP star x national-TV differential in return probability is positive
but imprecisely estimated and appears to reflect relative preservation of star
return rates on TV games alongside deterioration on non-TV games rather than a
large absolute TV-game return increase.

Very short absence spells do not become detectably more common when
national-TV games approach, and event-time analyses show no systematic
redistribution of absence onset or prevalence around TV games.

An exploratory analysis indicates substantial divergence between specific- and
vague-injury repair differentials, but this direct contrast was identified
after inspecting the pre-specified subgroup estimates and should be interpreted
as hypothesis-generating.

Overall, Stage 10 provides additional evidence about absence dynamics without
establishing strategic or disguised load-management behavior.
