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
