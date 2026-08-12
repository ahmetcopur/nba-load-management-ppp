# Frozen Specification

## Main estimand
`Star_it × PostPPP_t × AnnouncedTV_g`

## Policy timing
`PostPPP = 1` beginning in 2023-24.

## Dynamic star definition
At opening night, a player is a star if selected to an All-Star or All-NBA team in any of the prior three seasons. Newly selected current-season All-Stars become stars after that season's All-Star Game.

## Main outcome
`new_absence_onset = 1` only on the first eligible game of a new absence spell. Ongoing absence-spell games are excluded from the onset risk set.

## Main model
Linear probability model:
- player fixed effects;
- team-season fixed effects;
- full pregame control set;
- two-way clustered SE by player and game.

## Full control set
- home;
- back-to-back;
- 3-in-4;
- 4-in-6;
- travel distance since previous game;
- absolute timezone shift;
- road-trip game number;
- signed pregame Elo advantage;
- opponent bottom quartile;
- opponent back-to-back;
- rest advantage;
- travel disadvantage;
- NBA Cup status;
- minutes in prior 10 roster games;
- games played before current game;
- distance to 65 games.

## TV definitions
1. `legacy_primary`: original advance-announced national-TV definition retained as the historical main specification.
2. `harmonized_linear`: cross-season harmonized linear-national definition used as mandatory sensitivity.

The legacy definition must never be silently replaced by the harmonized definition or vice versa.

## Report timing definitions
1. `latest_pre_tip`: latest usable official NBA injury report strictly before scheduled tip.
2. `harmonized_common_times`: common 1:30/5:30/8:30 ET checkpoints; outcomes and risk set rebuilt upstream.

## Classification mechanism
Conditional sample: new injury onsets whose frozen class is `vague` or `specific`.
Outcome: 1 = vague, 0 = specific.

## Frozen taxonomy classes
`explicit_rest`, `illness`, `other_non_injury`, `specific`, `vague`, `unknown`.

## Heterogeneity definitions
- Back-to-back: current game is second night of a B2B.
- Weak opponent: opponent in pregame bottom quartile.
- High recent workload: prior-10-game minutes >= season-specific 75th percentile, requiring at least 10 prior roster games.
- Near 65 threshold: within 0-15 games short of 65, compare 0-5 short vs 6-15 short.
- Age/career stage: **not executed** because reliable age/full-career metadata were not available in the frozen panel.

## Freeze rule
After 2026-08-12, new specifications may be added only as clearly labeled extensions based on:
- genuinely new data;
- externally motivated reviewer requests;
- correction of a documented bug;
- a new predeclared research question.

They must not overwrite the frozen estimates.
