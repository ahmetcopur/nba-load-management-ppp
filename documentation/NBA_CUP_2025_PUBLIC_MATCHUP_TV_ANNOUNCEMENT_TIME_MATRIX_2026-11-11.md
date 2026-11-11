# NBA Cup 2025 — prospective national-broadcast announcement timestamp matrix

**Audit: November 11, 2026. Original published research datasets and paper unchanged.**

## Why "played on national television" is not "preseason opponent-specific TV announced"

This scientific check addresses a source-time inference boundary. We have:
1. Original **NBA-hosted Aug 13, 2025** team news announcements for **19** distinct Cup group matchups. [First-party source rows](../validation/official_nba_cup_2025_aug13_five_team_press_releases.csv).
2. First-published **Aug 13** reporting in independent media for **14 additional** West B/East B matches, with **three later-edited Pelicans-only** source exceptions. [Secondary source rows](../validation/nba_cup_2025_aug13_four_contemporaneous_secondary_reports.csv).
3. NBA Communications dated **Aug 14, 2025**, expressly naming **nine** national 2025 Cup group matchups and broadcasting providers. [Nine original first-party network rows](../validation/official_nba_cup_2025_aug14_named_group_broadcasts.csv).
4. NBA.com's national schedule article last updated **Aug 21, 2025**, naming all **15** nationally broadcast 2025 Cup group matches. [Fifteen national named rows](../validation/official_nba_cup_2025_aug21_all_15_national_group_broadcasts.csv).

**The original Aug 13 complete league 60-game first-release schedule PDF is still missing.** Exact first-release matchup date/opponent/home/away and national-network announcement timestamps must be independently verified to avoid applying future matchup information to earlier research exposures.

## Exact published-source crosswalk

The new [automated network/matchup publication-time matrix](../scripts/data_rebuild/audit_2025_cup_national_publication_timing.py) strictly revalidates all four separate source datasets and joins their full original date + visitor + home keys.

| Evidence question | Count | Interpretation |
| --- | ---: | --- |
| National NBA Cup group games later specifically named by NBA | 15 | Definitively listed in original NBA.com August 21 article |
| National games with same-day first-dated Aug 13 matchup evidence | 9 | 3 NBA first-party, 6 contemporaneous secondary |
| National games WITHOUT independently identified Aug 13 per-game source in this audit | 6 | NOT necessarily unannounced in reality; simply not independently recovered here |
| National networks **positively named by the Aug 13 articles** | **6** | 1 first-party, 5 secondary; positively known from these contemporaneous sources |
| Other national networks independently verified by the original **Aug 14** NBA Communications release | **4** | Not stated in corresponding Aug 13 source article, or no Aug 13 game source |
| Remaining national networks independently verified only by **Aug 21** NBA.com article in this audit | **5** | Must not be retrospectively treated as established on Aug 13 by these sources |

**Network verification timeline: six by Aug 13, four by Aug 14, five by Aug 21**, based on the **specific sources recovered here**, not absolute claims about the first-ever announcement from any broadcaster. All 15 networks may in fact have been announced on the original Aug 13 full schedule; that binary is absent here, and earlier broadcaster promotions could exist. This audit refuses to assert those as facts without the source.

The first party NBA Aug 13 fixture sources independently name only the Pacers @ Cavaliers November 21 **Prime** broadcast. The other five positive TV mentions are from second-tier news dated Aug 13. Blank first-party/team article network fields are **UNKNOWN** rather than verified negative.

Three important examples:

- **Golden State Warriors @ Denver Nuggets, Nov 7**: exact matchup appears in Denver's **Aug 13 original NBA team article**, which does **not positively name Prime**. The separate Aug 21 NBA.com source confirms **Prime**. Do not assign an unsupported Aug 13 network timestamp from the Denver article alone.
- **Orlando Magic @ Philadelphia 76ers, Nov 25**: same-day Aug 13 secondary Sixers coverage gives the matchup, not its TV network. NBA Communications on **Aug 14** directly states **NBC/Peacock**.
- **LA Clippers @ Los Angeles Lakers, Nov 25**: the Aug 13 Lakers article affirmatively describes **NBC**; NBA later explicitly describes the same game as **NBC/Peacock**, the NBCUniversal television/streaming distribution. The audit normalizes those *positive* labels but never treats any blank as false.

Every per-game source-time classification is emitted by the verifier as a reproducible public-only JSON report with flags for first-party versus secondary, next-day edit caveats, positive original-network source and the earliest independently verified date.

## Rerun public source-provenance audit

```bash
python -m unittest discover -s tests -p test_2025_cup_national_publication_timing.py -v
python scripts/data_rebuild/audit_2025_cup_national_publication_timing.py \
  --output-report /PRIVATE/NEW/2025_cup_network_first_verifiable_source_timing.json
```

**This is NOT a model-treatment or private original research row audit.**
No original private source research ZIP was opened by these public tests.
It is still essential to run the separate SHA-pinned original Cup and TV
research source-verifier commands in a private clean checkout, and to
recover the full original Aug 13 league Cup schedule to validate all 60
initial game/broadcast fixture tuples.

## Remaining Level C gates and release discipline

- 27 additional 2025 Cup group fixtures still lack a contemporaneous
  game-by-game source in the combined Aug 13 first-party + second-tier
  audit, and 14 of the 33 sources are not original NBA team publications.
- The 2025 original first-release 60-game NBA-by-day PDF remains unrecovered;
  the 3 Pelicans-only later-edited Aug 13 reports need immutable initial
  revision evidence for **as-published Aug 13 exact tuple** claims.
- Execute pinned original-private **2023/24 120-game**, **2025 33-game
  contemporaneous date tuple**, and **2023–25 18 knockout game** exact
  source joins; check six neutral-site nominal hosts separately.
- Independently verify remaining human reviewed injury labels, player
  crosswalk, awards and non-TV covariates; run the full clean-checkout
  original source ZIP flow; reconcile manuscript claims, corrected
  chronology and sensitivity estimates, then independent scientific review.

Do NOT merge PR #4, close Issue #5, overwrite immutable originals,
rewrite historical acceptance evidence, or change manuscript effect
sizes from this public-source crosswalk alone.
