# Data statement

This repository publishes player-level NBA data so that the study's analyses can be checked and rerun. This statement says what the data is, where it comes from, and on what terms it is shared.

## What is included

| File | Contents |
| --- | --- |
| `data_final/player_game_panel_analysis_ready.csv.gz` | 248,730 player-team-game rows, 2020–21 to 2025–26 regular seasons |
| `data_final/player_game_panel_model_at_risk_analysis_ready.csv.gz` | 180,829 at-risk rows used in the August models |
| `data_final/absence_spells_taxonomy_frozen.csv.gz` | 13,723 absence spells with their frozen classification |
| `data_intermediate/player_team_game_harmonized_cadence.csv.gz` | 248,778 player-team-game rows used in the October models |
| `validation/taxonomy_validation_sample_300_original.csv` and the taxonomy scoring packages | The 300-spell classification sample and its two coders' labels |

Rows identify players by NBA player ID and name, and include the injury-report designation (for example Out or Questionable) and the reason text the NBA published.

## Sources

- **Injury designations and reasons:** the NBA's official pre-game injury reports, which the league publishes as PDF files.
- **Participation, minutes and game details:** NBA box-score data published by the league.
- **All-Star and All-NBA selections, schedules and national-TV listings:** public NBA releases, documented in `documentation/`.

No data was collected from players, teams or medical providers, and nothing in this repository comes from non-public records. Classifications such as "vague" or "specific" absence reasons are the study's own coding of the published text, not medical diagnoses.

## Terms of use

- **Code** in this repository is released under the MIT licence (see `LICENSE`).
- **Data** is shared only to allow verification and replication of this study. No licence to the data is granted. Rights in the underlying records remain with their original sources, and any reuse must follow those sources' terms.

## Corrections and removal requests

To report an error, or to ask for a record to be corrected or removed (for example as a player or rights holder), open an issue on this repository. Note that removal from the current files does not remove earlier versions from the Git history.

## Versions

The adopted primary October analysis is the SCI-001-corrected panel. Frozen and legacy versions are kept as historical references; see `README.md` and `documentation/SCI001_ADOPTION_DECISION_2026-11-16.md`.
