# Level C — NBA Cup 2025 West B / East B second-tier August 13 source bridge

**Audit date: November 11, 2026. Original research frozen.**

## Scope, primary source boundary, and publication chronology

The [five original first-party NBA team announcements from August 13, 2025](../validation/official_nba_cup_2025_aug13_five_team_press_releases.csv)
still establish **exactly 19 of the 60 original Cup group-game
date/visitor/host identities** at NBA-original-team-publication level. That
count **DOES NOT INCREASE** in this extension because no new original
NBA.com 2025 August 13 first-team story or NBA original August 13 full
60-game by-date PDF has been recovered.

However, contemporaneous *non-NBA* coverage, originally dated **August 13,
2025**, includes full four-fixture schedules for **Lakers, Pelicans, Celtics
and 76ers**, previously uncovered in the original NBA first-party tier:

| Reporting club | Date/source and provenance | Four games from original same-day press | Status |
|---|---|---:|---|
| Lakers | [Silver Screen and Roll, original Aug 13](https://www.silverscreenandroll.com/lakers-news/93107/lakers-nba-cup-schedule-dates-grizzlies-pelicans-clippers-mavericks) | 4 | Original same-day **secondary** reporting |
| Pelicans | [WVUE / FOX 8, first published Aug 13, **updated Aug 14**](https://www.wsfa.com/2025/08/14/new-orleans-pelicans-nba-cup-schedule-released/) | 4 | **Post-publication edit caveat**, exact initial Aug 13 content not independently archived |
| Celtics | [CBS Boston, updated Aug 13](https://www.cbsnews.com/boston/news/boston-celtics-nba-cup-schedule-amazon-prime/) | 4 | Original same-day **secondary** reporting |
| 76ers | [Sixers Wire, Aug 13, via Yahoo Sports syndication](https://sports.yahoo.com/article/sixers-schedule-nba-cup-group-181855855.html) | 4 | Original same-day **secondary** syndicated reporting |

The sanitized, factual [16-row secondary-news fixture CSV](../validation/nba_cup_2025_aug13_four_contemporaneous_secondary_reports.csv)
records actual **source first-posted date**, **source update date**,
source publisher/tier, date, away, home, and **only the broadcaster explicitly
named in that particular article**. As with the original first-party
tier, blank broadcast is **not the same as "no national TV."**

There are **two independently duplicated fixtures** among the four articles:
- Lakers at Pelicans, November 14, 2025 — mentioned by Lakers AND Pelicans reporting.
- Celtics at 76ers, October 31, 2025 — mentioned by Celtics AND 76ers reporting.

Thus the 16 article records establish 14 **distinct** identified matchup
date/home/away tuples, 7 in **West Group B** and 7 in **East Group B**.
There is **no overlap** between these 14 and the previous original-NBA.com
tier's 19 matches, producing **33/60 total unique dated matchup tuples
with original-Aug-13-dated sourcing**, with crucial qualification:
**19 first-party NBA**, **11 secondary without a known next-day edit**,
**3 unique games supported only by the Pelicans later-updated article**.

**Do not claim 33 first-party cases or 33 immutable August 13 source bytes.**
The exact initial August 13 version of the later-updated Pelicans story was
not recovered. Its 3 unique fixture rows are a separately marked provenance
exception: original publication August 13, currently displayed story revised
August 14. Some websites may also silently modify articles without metadata,
so any time-stamped source is not equal to an immutable archived binary.

### Source tier and complete-cup group coverage

| 2025 NBA Cup group | Previous *NBA original-team August 13* | Contemporaneous *non-NBA* added | Combined distinct fixture evidence | Still unverified without separate original source |
|---|---:|---:|---:|---:|
| West A | 4 | 0 | 4/10 | 6 |
| West B | 0 | 7 | 7/10 | 3 |
| West C | 4 | 0 | 4/10 | 6 |
| East A | 7 | 0 | 7/10 | 3 |
| East B | 0 | 7 | 7/10 | 3 |
| East C | 4 | 0 | 4/10 | 6 |
| **All** | **19** | **14** | **33/60** | **27** |

The **19** first-party fixtures are untouched and are verified separately.
The newly sourced 7 West B and 7 East B games still need **first-party NBA
original first-release PDF / contemporary original first-party team** source
recovery to graduate their provenance from secondary to first-party.

Only positive source-named national TV:
Lakers at Grizzlies (Prime), Clippers at Lakers (**NBC** as written in the
Lakers' article), Mavericks at Lakers (Prime), Celtics at 76ers (Prime,
independently named twice), and Pistons at Celtics (ESPN). Network blanks
are **UNKNOWN** for that source. The later [NBA.com fifteen group national
games by August 21](../validation/official_nba_cup_2025_aug21_all_15_national_group_broadcasts.csv)
and [NBA Communications Aug 14 statement](https://pr.nba.com/2025-26-nba-regular-season-schedule/)
can independently corroborate national network labels but **cannot be
represented as independent August 13 first-release binary source evidence**.
In particular, `NBC` and `NBC/Peacock` are distribution descriptions;
reconciling exact model categories is a later, explicitly controlled step.

## Executable source verification

[The strict secondary source verifier](../scripts/data_rebuild/verify_cup_2025_aug13_contemporaneous_secondary_sources.py)
imports and validates the separate original first-party five-team public
check before checking the additional media source. It requires all 16
exact article row tuples, original source URLs, tier labels and update
dates, 2 home + 2 away for each club, correct original Cup opponent groups,
the two independently duplicated games, disjointness from the 19
first-party tuples and unchanged positive network mentions.

[Its 10 fail-closed tests](../tests/test_cup_2025_aug13_contemporaneous_secondary_sources.py)
reject made-up source-date changes, source-tier upgrades, removal of the
next-day Pelicans caveat, false negative national-TV claims, changed
hosts and dates, removed first-party evidence and tampered private archives.

```bash
python -m unittest discover -s tests -p test_cup_2025_aug13_contemporaneous_secondary_sources.py -v
python scripts/data_rebuild/verify_cup_2025_aug13_contemporaneous_secondary_sources.py --source-only
```

## Strict exact original-private source comparison remains UNEXECUTED

If and only if the authentic immutable original
`nba_player_game_at_risk_star_cup_v1.zip` (SHA-256:
`65c4756b86dfb5757bb84b6be13eafb952375aaa6ce49fc1ddddc6224a4faf70`)
is supplied **privately** in the local runtime, run:

```bash
python scripts/data_rebuild/verify_cup_2025_aug13_contemporaneous_secondary_sources.py \
  --original-cup-zip /PRIVATE/PATH/nba_player_game_at_risk_star_cup_v1.zip \
  --output-report /PRIVATE/PATH/2025_cup_33_contemporaneous_original_fixture_joins.json
```

This rejects archive SHA-256 drift and compares all **33 unique
date/away/home source tuples** to the original 7,230-game private Cup
lookup with all 60 original 2025 Cup group games present. The original
private ZIP bytes are not accessible in this session, so the
**33-row private acceptance is NOT run and NOT claimed**.

**Next:** recover original first-party 2025 Aug 13 NBA Cup 60-row
schedule binary or contemporaneous NBA team announcements, prioritize the
remaining **3 West B, 3 East B, 6 West A, 6 West C, 3 East A, 6 East C**
fixture tuples; verify original TV release timing without hindsight and
run strict private source archive comparison.

Original frozen research files, coefficients, manuscript, prior historic
validation reports untouched. PR #4 remains **draft/unmerged** and
Issue #5 remains **open**.
