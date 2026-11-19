# November 11, 2026: independent actual NBA Cup knockout game sources (2023–25)

## What is now checked from first-party NBA sources

This component extends the Level-C original NBA Cup group-draw/date audit with
the **actual 18 historical knockout quarterfinal and semifinal** game
matchups, dates, *realized broadcast networks* and winning teams.
The original primary-source transcriptions are in
[the 18-game knockout reference](../validation/official_nba_cup_2023_2025_eighteen_knockout_fixture_sources.csv).

| Season | Quarterfinals: known source away/home | Neutral semifinals: unordered pair | Realized named TV networks |
| --- | ---: | ---: | --- |
| 2023–24 | 4 | 2 | TNT 5, ESPN 1 |
| 2024–25 | 4 | 2 | TNT 4, ESPN 1, ABC 1 |
| 2025–26 | 4 | 2 | Prime 6 |
| **All** | **12** | **6** | **18** |

**Quarterfinals were hosted in home markets** with a meaningful conventional
home/away designation. The **semifinals played at neutral-site Las Vegas**.
The original NBA result headlines often say e.g. “Bucks vs Pacers” or “Knicks
vs Magic” without establishing the **nominal statistical league home side**.
Accordingly, the six source rows have *blank* `home_team` and `away_team`
and use the **unordered participant pair** as primary source identity.
A direct league game log could resolve the six nominal designations, but
inferring them from a headline or which team wins is not valid.

### Contemporaneous NBA source chronology

This audit uses source URLs tied to historical **dated** original NBA
announcements, together with NBA.com actual result trackers.

**2023:** The original Nov 1, 2023 NBA Communications
[knockout national schedule announcement](https://pr.nba.com/nba-announces-broadcast-schedule-on-abc-espn-and-tnt-for-knockout-rounds-of-inaugural-in-season-tournament/)
specified **all four TNT quarterfinal slots**, then one ESPN and one TNT
semifinal broadcast **with the opponent matchups not yet known**.
The NBA's dated [Nov 29 qualifier/fixture release](https://www.nba.com/news/nba-starting-5-nov-29-2023)
listed the four exact original home-market pairings. The dated
[Dec 7 semifinals announcement](https://www.nba.com/news/nba-starting-5-dec-7-2023)
named the actual Bucks/Pacers ESPN and Lakers/Pelicans TNT/TruTV games.
The original [2023 tournament results](https://www.nba.com/news/nba-in-season-tournament-key-dates-schedule)
confirm which team actually won each of the six games.

**2024:** The NBA's dated [Dec 4 qualifier announcement](https://www.nba.com/news/starting-5-dec-4-emirates-nba-cup-knockout-rounds-set-after-huge-night)
and [Dec 4 knockout broadcaster list](https://www.nba.com/news/emirates-nba-cup-2024-clinching-elimination-scenarios)
identify the four quarterfinal home-market matchups and TNT/TNT/ESPN/TNT.
But the two semifinal national TV slots were still **TBD opponents**.
The Dec 12 [semifinal article](https://www.nba.com/news/starting-5-dec-12-2024)
identifies actual Bucks/Hawks TNT and Thunder/Rockets ABC and
[Dec 14 NBA scores](https://www.nba.com/news/nightly-pulse-nba-news-highlights-from-dec-14)
confirm game winners.

**2025:** NBA.com's dated [Dec 9 quarterfinal preview](https://www.nba.com/news/starting-5-dec-9-2025)
identifies Heat at Magic, Knicks at Raptors, Suns at Thunder, Spurs at Lakers
on **Prime**. The dated [Dec 12 NBA semifinals announcement](https://www.nba.com/news/full-schedule-emirates-nba-cup-semifinals-media-availability)
names Knicks/Magic and Spurs/Thunder at the Las Vegas neutral site on Prime,
and the NBA [2025 Cup results and format page](https://www.nba.com/news/in-season-tournament-101)
confirms the actual game results. These first-party dates do not prove that
the knockout *opponents* were known in the August full-season release.
The preseason announcement concerned **scheduled broadcasting slots**, not
the eventual knockout participants.

The 2023, 2024 and 2025 **championships are excluded** because they are not
regular-season games in the study. The source rows contain actual **post-qualification
broadcast provider** as `game_network`: this is **not** automatically the same
variable as *first advance-announced opponent-specific national TV*.

## Rerunnable source-only acceptance in GitHub CI

Use the new [original-source knockout verifier](../scripts/data_rebuild/verify_official_nba_cup_knockout_original_fixtures.py)
and [mutation tests](../tests/test_official_nba_cup_knockout_original_fixtures.py):

```bash
python scripts/data_rebuild/verify_official_nba_cup_knockout_original_fixtures.py --source-only
python -m unittest discover -s tests -p test_official_nba_cup_knockout_original_fixtures.py -v
```

It checks every original date, stage, participant pair, 12 ordinary
quarterfinal home/away fixtures, realized network, result winner,
source URL, and the six explicitly neutral-site semifinal caveats.
It fails closed on altered source record, stage counts, wrong game date,
unexpected extra/missing game, host inversion, network swap or source URL/date.
This is still **public original-source reproduction**, NOT execution
against the original private Cup lookup.

## Private original Cup lookup acceptance — separate and still open

This command must run in a local clean checkout with the authentic
immutable `nba_player_game_at_risk_star_cup_v1.zip`
SHA-256 `65c4756b86dfb5757bb84b6be13eafb952375aaa6ce49fc1ddddc6224a4faf70`:

```bash
python scripts/data_rebuild/verify_official_nba_cup_knockout_original_fixtures.py \
  --original-cup-zip /PRIVATE/PATH/nba_player_game_at_risk_star_cup_v1.zip \
  --output-report /PRIVATE/PATH/NBA_2023_2025_Cup_knockout_original_source_compare.json
```

It independently matches all **18** original research Cup game rows by
`season, date, cup_stage, unordered participant pair` and all **12**
quarterfinals by ordered `season, date, AWAY, HOME`.
It **deliberately does not** certify which nominal home team the league
assigned to the six neutral semifinals, or the first public availability
of specific opponents, or the Cup-specific TV model treatment flags.

**This strict private command has not been executed in this continuation**
because the original pinned ZIP bytes are not accessible. No original
private source files are uploaded or edited by the public test.

## Scope still open

- All 2023/2024 original private 120 group-row+TV comparisons and the 2025
  15-named-national-group-row private comparisons;
- Complete first Aug 13, 2025 60-group-game release binary/date/network
  reconstruction;
- Original 18 knockout **private Cup lookup** match, the six independent
  NBA game-log nominal home/away designations, and original announced-TV
  **timing/treatment** relation to initially opponent-TBD knockout slots;
- Full original awards/crosswalk/taxonomy/game-covariate independent
  verification and remaining private end-to-end and manuscript gates.

Never change original frozen research data, manuscript, or historical
evidence to make a comparison pass. PR #4 remains DRAFT/UNMERGED and
Issue #5 remains OPEN.
