# Independent first-release NBA Cup 2025 fixtures — ORIGINAL August 13, 2025 team stories

## Scientific verification level: partial primary-source original first-release identities

The historic league's August 13, 2025 full 60-game Cup Group Play
announcement (as subsequently confirmed by its [August 14 full-season press
statement](https://pr.nba.com/2025-26-nba-regular-season-schedule/))
was earlier than the main NBA by-date regular-season PDF. A complete copy
of the **August 13 original 60-game league by-day Cup PDF** has not yet
been recovered or re-extracted. Do not substitute the full-season August 14
PDF or the later realized games for the missing original August 13 binary.

But **five contemporaneous official NBA team's own August 13 news stories**
survive and establish all four Cup fixture dates, opponents, and game hosts
for each reporting club:

- [Toronto Raptors, original Aug 13](https://www.nba.com/raptors/news/raptors-announce-2025-emirates-nba-cup-schedule)
- [Indiana Pacers, original Aug 13](https://www.nba.com/pacers/news/pacers-schedule-announced-for-2025-nba-cup-group-games)
- [Phoenix Suns, original Aug 13](https://www.nba.com/suns/news/phoenix-suns-announce-schedule-for-emirates-nba-cup-2025-group-play-games)
- [Denver Nuggets, original Aug 13](https://www.nba.com/nuggets/news/analyzing-the-denver-nuggets-emirates-nba-cup-schedule)
- [Charlotte Hornets, original Aug 13](https://www.nba.com/hornets/news/hornets-schedule-announced-for-emirates-nba-cup-2025)

The original [five-team dated press transcript](../validation/official_nba_cup_2025_aug13_five_team_press_releases.csv)
contains **20 original club-game appearances** describing **19 DISTINCT**
date + visiting team + home team fixtures. The duplication is useful:
**Indiana Pacers at Toronto Raptors, November 26, 2025** is independently
published with identical date and opposing host in both the Pacers and
Raptors announcements. Each of the five reports contains four distinct
official in-group opponents, two home games and two road games.

The 19 fixtures cover all original press-announced group date/away/home
records for those clubs, **not** all 60 league group games. The original
full Cup group-draw lists, verified independently, support the group
opponent consistency checks. The original league group-stage 2025 date
distribution was previously checked for 60 group fixtures, but it is not
proof that the other 41 individually reconstructed fixture tuples were
published on August 13.

## Original press announcement nationality/network distinction

This team-source archive records only *positively stated networks*: the
[Pacers Aug 13 announcement](https://www.nba.com/pacers/news/pacers-schedule-announced-for-2025-nba-cup-group-games)
explicitly calls the **November 21 Indiana @ Cleveland** matchup a
**national Amazon Prime** broadcast.

The other 19 team-source rows have a blank
`positively_named_network` cell. This does NOT mean “not nationally
televised”, and must never be silently converted to false. For example,
the previously separately verified
[2025 national NBA.com broadcast subset](../validation/official_nba_cup_2025_aug21_all_15_national_group_broadcasts.csv)
includes **three of these 19 exact fixture identities**: Warriors @
Nuggets November 7 (Prime), Pacers @ Cavaliers November 21 (Prime) and
Nuggets @ Rockets November 21 (Prime). Only the Pacers' original Aug 13
team release itself positively names Prime. The **August 21** NBA.com
article establishes the networks of the two other games no later than
that publication; the original first-release network for those two is
NOT independently proven by these August 13 team articles.

This distinction is essential for valid advance-announced treatment,
rather than using realized TV coverage in a way that leaks future information.

## Strict source-only reproducibility

The new [source checker](../scripts/data_rebuild/verify_official_nba_cup_2025_aug13_team_press_sources.py)
and [10 fail-closed mutation tests](../tests/test_official_nba_cup_2025_aug13_team_press_sources.py)
compare the separate source CSV with the five explicitly recorded
full date/away/home fixtures, original URLs, publication date and original
2025 official group memberships. They fail on home-team reversals,
incorrect dates, made-up negative TV, missing rows, malicious source URL
changes or disagreement between the two independently reporting teams.

```bash
python -m unittest discover -s tests -p test_official_nba_cup_2025_aug13_team_press_sources.py -v
python scripts/data_rebuild/verify_official_nba_cup_2025_aug13_team_press_sources.py --source-only
```

## Private source acceptance — command PREPARED, NOT EXECUTED

With the authentic original
`nba_player_game_at_risk_star_cup_v1.zip`
(**full SHA-256**
`65c4756b86dfb5757bb84b6be13eafb952375aaa6ce49fc1ddddc6224a4faf70`),
the same verifier can compare all 19 original first-release game
identities with the exact original private historical 60-game 2025
Cup-stage lookup:

```bash
python scripts/data_rebuild/verify_official_nba_cup_2025_aug13_team_press_sources.py \
  --original-cup-zip /PRIVATE/PATH/nba_player_game_at_risk_star_cup_v1.zip \
  --output-report /PRIVATE/PATH/nba_2025_aug13_five_team_original_Cup_acceptance.json
```

The original private ZIP is not present in this session; the comparison
has **NOT run**, and no private-row equality is claimed.

## Still open

Recover the exact original first-release NBA 60-game PDF (or complete
original contemporaneous NBA club source coverage), then independently
check **all** 60 initial fixture+TV release tuples, not merely the
19 present here. Official NBA team first releases could be sourced
additionally for missing teams; keep original publication date and
network evidence separate. Current later August 2025 national subset is
15/15 named, but original-Aug-13 network coverage is not comprehensive.

Full frozen private Cup, TV, source ZIP one-command execution, and
other award/medical-label/crosswalk/covariate/manuscript reconciliation
gates remain separate and open. No original frozen research data,
model, manuscript or historical evidence modified. Keep PR #4
DRAFT/UNMERGED, Issue #5 OPEN.
