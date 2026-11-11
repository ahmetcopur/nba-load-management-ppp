# Level C — independently republished 2025 Cup 60-game schedule, not first release

**November 11, 2026. Historical research archives/manuscript unchanged.**

## Finding and source provenance

An independent **ESPN-authored schedule article**, distributed by ABC7 New York,
was published **November 1, 2025** with the complete 2025 NBA Cup Group
Play dated fixture list and the broadcaster explicitly named for 15 of the
60 Cup group games:

- [ESPN-authored Nov 1 NBA Cup full schedule](https://abc7ny.com/post/2025-nba-cup-schedule-format-groups-updates-more/18031782/)
- [Factual 60-row transcription, preserving source date and literal
  network strings](../validation/nba_cup_2025_nov01_espn_editorial_60_group_fixtures.csv)
- [Source-only, independently runnable exact join
  checker](../scripts/data_rebuild/verify_nba_cup_2025_nov01_espn_60_groups.py)
- [11 mutation/failure tests](../tests/test_nba_cup_2025_nov01_espn_60_source.py)

The ESPN/ABC7 original article is **not** the still-unrecovered **NBA's
August 13, 2025 first-release full Cup Group Play by-day PDF**. It was
posted after the first 2025 Cup games had already been played. It can
independently verify actual game identities/dates/hosts and 15 later
positively named broadcast slots, **not when the NBA initially announced
any specific matchup or network**. It is intentionally filed in a
**later second-party editorial corroboration tier** rather than
relabelled NBA original first-release primary evidence.

## Independently checked across all 60 group games

| Check | Result |
| --- | ---: |
| Full group dated fixture rows | 60 |
| Group distinct opponent pairings | 60/60, exactly once |
| Official five-team group draws | 6/6 |
| Each of thirty teams has two home, two away | 30/30 |
| Day-level official 2025 Cup calendar | 8 / 11 / 9 / 9 / 3 / 9 / 11 (Oct 31, Nov 7, 14, 21, 25, 26, 28) |
| Original **Aug 13 NBA first-party team** fixture source records matching later ESPN | 19/19 |
| Additional **Aug 13 first-dated secondary** fixture source records matching later ESPN | 14/14 |
| NBA's **nationally named group broadcast source** date/team/provider rows matching ESPN | 15/15 |
| Positive named broadcasters | Prime 10; Peacock 2; ESPN 3 |
| Remaining ESPN network fields | 45 **UNREPORTED IN THIS SOURCE** (not confirmed non-national) |

The 15 network comparison performs a **source-level distribution
normalization**: ESPN/ABC7 labels two 2025 November Tuesday
broadcasts **Peacock**, whereas the original NBA national schedule
labels their NBCUniversal coverage **NBC/Peacock**. No empty/unnamed
network field is converted into a negative verified TV treatment.
The dated/opponent/provider positive source keys themselves must
match one-to-one.

### Critical distinction between three separate claims

- **60/60 independently validated 2025 group fixture date, away/home:** NOW
  verified from **later November 1 ESPN editorial source** in this layer,
  subject to source reporting reliability.
- **Original August 13 2025 initial first-release fixture source:** only
  **19/60 original NBA-hosted team article** exact game tuples,
  **14 additional Aug 13 first-dated non-NBA source game tuples**,
  three of which derive from a Pelicans article edited August 14.
  The **original complete August 13 NBA by-day PDF binary has NOT been
  recovered or independently verified**.
- **First public announcement of networks at a particular date:** the
  separate [prospective-source network timing
  matrix](NBA_CUP_2025_PUBLIC_MATCHUP_TV_ANNOUNCEMENT_TIME_MATRIX_2026-11-11.md)
  supports 6 positive August 13 article mentions, four additional
  confirmed by NBA Communications August 14 and five remaining
  confirmed by NBA.com August 21 *among the sources recovered*. The
  November editorial cannot backdate those networks, nor does the
  absence of an earlier source mean a broadcaster did not announce it.

Hence the new later first-party-independent 60/60 game fixture verification
**does not change the numerator of the original first-release August 13
source audit** (19 NBA first-party, 14 additional contemporaneous
second-tier). Those are different acceptance statements.

## Rerunnable public-only source check

```bash
python -m unittest discover -s tests -p test_nba_cup_2025_nov01_espn_60_source.py -v
python scripts/data_rebuild/verify_nba_cup_2025_nov01_espn_60_groups.py \
  --output-report /PRIVATE/NEW/2025_nba_cup_espn_later_60_source_validation.json
```

The script revalidates 2025 original NBA Cup group draws and both
August 13 distinct source tiers and the 9 + 15 original NBA network
source inventories. It fails on a wrong home/away matchup, game date,
group/daily count, duplicate fixture, malformed source date/URL,
NBA original first-party crosswalk drift or a later 15-game national
provider mismatch.

The comparison uses only the **public repo's original source reference
transcriptions**, not the two original **private** NBA Cup research source
ZIPs. Its public CI success cannot establish a private research archive
acceptance. The source does not independently supply the missing
2025 initial first-release network status of all 60 games.

## Original private Cup source ZIP gate remains open

A real **source-to-original research** check must still run the
SHA-pinned [master Cup private source audit](../scripts/data_rebuild/run_original_cup_private_source_acceptance.py)
with the authentic `nba_player_game_at_risk_star_cup_v1.zip`
and `nba_load_management_final_freeze_2026-08-12.zip`
as explained in [the original private ZIP runbook](NBA_CUP_PRIVATE_ONE_COMMAND_ARCHIVE_ACCEPTANCE_2026-11-11.md).
The user has not provided these authentic bytes to this session.
Even a private match to the November ESPN schedule would prove actual
date/team source consistency, NOT original August 13 first-release
exposure timing or prospective causal model validity.

**Never silently change original treatment flags, frozen datasets,
estimates, or manuscript. PR #4 remains draft/unmerged; Issue #5 open.**
