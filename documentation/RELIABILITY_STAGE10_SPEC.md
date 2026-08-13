# Stage 10 — Reliability / Repairable Availability Analysis

Status: pre-specified before estimation.

## Concept

Treat each player as a repairable component alternating between an available
state and an absent state.

Available -> Absent is a failure/absence onset.
Absent -> Available is a repair/return transition.

This stage extends the frozen onset analysis by studying both sides of the
availability process. It does not replace or modify the frozen Stage 1-9
results.

## Primary analysis 1 — Return / repair hazard

Risk set:
player-team-games for which the player was absent in the immediately preceding
team game and remains observable on the roster/current game.

Outcome:
return_today = 1 when the player transitions from absent in the previous team
game to available in the current team game.

Primary estimand:
Star x PostPPP x AnnouncedTV.

Primary model:
LPM with player and team-season fixed effects, the same admissible pregame
controls as the frozen main model, and two-way clustered inference where
appropriate.

Primary exposure:
legacy advance-announced national TV.

Mandatory sensitivity:
harmonized national-TV definition.

Spell age will be controlled flexibly rather than assuming a constant repair
hazard.

## Primary analysis 2 — Absence duration

Analyze new absence spells using games missed as the time scale.

Primary outcomes:
- one_game_spell
- spell_le_2_games
- duration / survival of the absence spell

Primary comparison:
Star x PostPPP, with emphasis on whether an advance-announced national-TV game
occurs within the next one or two scheduled team games.

Right-censored spells at the end of observation must not be treated as completed
spells.

Vague, specific, explicit-rest, and other classifications use the already-frozen
onset taxonomy.

## Primary analysis 3 — TV-centered transition timing

For each advance-announced national-TV game, characterize player transitions
over event time -3 through +3 team games.

Outcomes:
- new absence onset
- return from absence
- currently absent

Primary quantity of interest:
whether the Star x PostPPP differential changes across event time.

This is a timing/mechanism diagnostic, not a new causal identification design.

Overlapping TV-event windows must be handled explicitly rather than silently
duplicating observations.

## Secondary analyses

1. Return hazard separately for vague and specific injury spells.
2. One-game and <=2-game spell probabilities by frozen onset category.
3. Failure hazard as a flexible function of games since previous return.
4. Team-level k-out-of-n roster availability only as a secondary descriptive
   extension.

## Interpretation constraints

A short vague absence followed by return for a TV game may be described as a
maintenance-like observable signature. It must not be called a fake injury or
intentional disguised rest without independent evidence of intent.

The Stage 1-9 LPM results remain the inferential anchor of the project.

## Frozen implementation details

### Observation key

The analytical unit is player x team x game. `player_team_game_id` is the
unique row identifier. `player_game_id` is not globally unique because a player
may have team-specific roster observations for both teams in the same physical
game after a transaction.

### Repair-hazard primary specification

Primary risk set:
- absent in the immediately preceding consecutive team game;
- previous absence spell successfully identified;
- previous spell is not left-censored;
- observed spell age is at least one game.

Primary outcome:
`return_available_today`.

This defines repair as transition from the project-frozen absence state to an
available state. Actual game participation is not required for the primary
outcome; `return_played_today` is a sensitivity outcome.

Primary exposure:
legacy advance-announced national television.

Mandatory sensitivity:
harmonized-linear national television.

Primary estimand:
Star x PostPPP x AnnouncedTV.

Fixed effects:
- player;
- team x season.

Repair baseline hazard:
flexible indicators for absence-spell age:
1, 2, 3, 4-5, 6-10, 11+ games.

Pregame adjustment variables:
- home;
- rest days between games, capped at 4;
- three games in four days;
- four games in six days;
- travel distance since previous team game, measured per 1000 km;
- pregame Elo win probability;
- Cup-game indicator.

Player workload variables measured after absence onset are deliberately excluded
from the primary repair model because they can themselves be affected by the
ongoing absence spell.

Inference:
two-way clustering by player and physical game.

Secondary repair analyses:
- `return_played_today`;
- vague-onset spells only;
- specific-onset spells only.

### TV-centered event timing

Because +/-3 national-TV windows overlap heavily, the primary timing analysis
will assign each player-team-game to its uniquely nearest TV anchor within
three team games. Equal-distance ties are excluded.

Isolated TV anchors and inverse-overlap-weighted stacked windows are
sensitivities rather than the primary event-time analysis.

### Event-time robustness specifications

The repair event-time pattern is subjected to two pre-specified sensitivity
analyses.

1. Isolated-anchor analysis:
   Only TV anchors with no other same-team TV anchor within six team games are
   retained. Their +/-3 windows therefore do not overlap. The repair model is
   otherwise identical to the primary nearest-TV specification.

2. Inverse-overlap-weighted stacked analysis:
   All +/-3 TV-anchor windows are retained. When one underlying
   player-team-game belongs to multiple TV windows, each stacked representation
   receives weight 1 / overlap_count, so total weight for an underlying
   player-team-game equals one. Fixed-effect absorption and estimation use
   these weights.

Both sensitivities retain:
- the primary non-left-censored repair risk set;
- return to availability as the outcome;
- player and team-season fixed effects;
- flexible spell-age controls;
- the frozen pregame schedule controls;
- two-way clustering by player and physical game;
- legacy TV and harmonized-linear TV definitions.

Event time 0 remains the reference position. The primary robustness quantity
of interest is the event-time +3 difference relative to event time 0.
Within each event-time model, the six nonzero event-time contrasts versus
event time 0 are additionally reported with Benjamini-Hochberg adjusted
p-values.
