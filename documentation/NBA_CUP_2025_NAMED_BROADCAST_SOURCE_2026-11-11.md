# NBA Cup 2025 — original NBA dated public releases, nine Aug 14 + fifteen by Aug 21

**Scope: source-only first-party evidence, NOT full 2025 first-release audit.**

## Original dated primary source

NBA Communications published [NBA announces schedule for 2025–26 regular season](https://pr.nba.com/2025-26-nba-regular-season-schedule/)
on **August 14, 2025**. It confirms that the **60 NBA Cup 2025 group-play games were announced on August 13**, before the August 14 full-season schedule. But the August 14 release directly spells out only some of the specific Cup group game dates, teams, and national broadcasters.

The actual independent, exact, nine-row subset is:
[2025 NBA Cup original-source named national games](../validation/official_nba_cup_2025_aug14_named_group_broadcasts.csv).

| Game date | Visiting team | Home team | Source network |
|---|---|---|---|
| 2025-10-31 | Boston Celtics | Philadelphia 76ers | Prime |
| 2025-10-31 | Los Angeles Lakers | Memphis Grizzlies | Prime |
| 2025-11-25 | Orlando Magic | Philadelphia 76ers | NBC/Peacock |
| 2025-11-25 | LA Clippers | Los Angeles Lakers | NBC/Peacock |
| 2025-11-26 | Detroit Pistons | Boston Celtics | ESPN |
| 2025-11-26 | Minnesota Timberwolves | Oklahoma City Thunder | ESPN |
| 2025-11-26 | Houston Rockets | Golden State Warriors | ESPN |
| 2025-11-28 | Milwaukee Bucks | New York Knicks | Prime |
| 2025-11-28 | Dallas Mavericks | Los Angeles Lakers | Prime |

These are **nine specifically identified games**, not the entire 2025 national-TV Cup coverage. The named subset has **Prime 4**, **NBC/Peacock 2**, and **ESPN 3**.

**Critical temporal distinction:** `source_announcement_date_et=2025-08-14` is the documented original NBA source publication date on which this precise nine-game evidence was independently verified. It does not imply these games were first announced that day, nor prove they all appeared in the original separately issued **August 13 Cup group-play PDF**. Even though the NBA confirms a complete prior Cup group schedule existed, that full original August 13 60-row PDF has not been independently retrieved, transcribed and joined in this audit.

The NBA also states that its NBA TV schedule would be announced later. That is not a basis for backfilling absent source evidence as a verified 2025 preseason NBA TV negative.

## Strict executable source-only and private checks

Run the [2025 named-source validator](../scripts/data_rebuild/verify_official_nba_cup_2025_named_broadcasts.py):

```bash
python scripts/data_rebuild/verify_official_nba_cup_2025_named_broadcasts.py --source-only
python -m unittest discover -s tests -p test_official_nba_cup_2025_named_broadcasts.py -v
```

The source-only command verifies all nine exact (game day, away, home, network) tuples, source URL and publication date, game-stage membership against the independent original NBA group-draw transcription, and network breakdown. The nine known rows are hard-coded into the verifier **separately from the CSV** so even a same-day/same-network row swap triggers failure.

To actually verify these nine rows against the **original immutable private research data** (and the later original season by-date NBA PDF parser output), provide the exact original Cup ZIP and historical research freeze ZIP:

```bash
python scripts/data_rebuild/verify_official_nba_cup_2025_named_broadcasts.py \
  --original-cup-zip /PRIVATE/PATH/nba_player_game_at_risk_star_cup_v1.zip \
  --original-freeze-zip /PRIVATE/PATH/nba_load_management_final_freeze_2026-08-12.zip \
  --output-report /PRIVATE/PATH/2025_Cup_original_nine_named_broadcasts.json
```

The command rejects modified archives by **full original SHA-256**, compares the nine matchups against the private original 60-game 2025 Cup group-stage lookup, then verifies exact date/opponent/network against the original NBA **later full-season** parsed source PDF. A pass of that private command is required before claiming original-archive acceptance. It has **not been executed in this check**. No private source ZIPs or original player-level data are uploaded.

## Still open

- Recover a dated complete August 13, 2025 *original first Cup group announcement* and independently verify its **60 game-by-game day/away/home/network rows**.
- Complete direct original 2023/2024 120-row private Cup/TV first-release joins.
- Direct original NBA sources for the **six actual quarterfinal/semifinal games per season (18 across 2023–25)** with first announcement time, matchup, game date, home/away, and original provider; championship separately excluded from regular-season modeling.
- Compare postponed/changed game mappings and historical broadcast changes separately, without treating source publication and game-day appearance as interchangeable.
- Keep human-reviewed taxonomy/crosswalk, award history, all other scientific covariates, master clean-checkout ZIP invocation, and manuscript reconciliation as distinct open research gates.

This does not revise any historical model coefficient or retroactively change the frozen national-TV exposure coding. No original data or manuscript modified. **PR #4 stays draft/unmerged, Issue #5 open.**

## November 11 follow-up — complete 15-game *national group-play* subset (additional NBA.com source)

The NBA's [2025–26 national TV schedule article](https://www.nba.com/news/2025-26-schedule-announced), updated **August 21, 2025**, explicitly names all **15 2025 NBA Cup Group Play national broadcasts**: **ten Prime**, **two NBC/Peacock**, and **three ESPN**. This adds six previously unnamed Prime games to the nine directly evidenced in the separately dated August 14 primary NBA Communications release.

The new [complete national subset 15-row source CSV](../validation/official_nba_cup_2025_aug21_all_15_national_group_broadcasts.csv) is independently checked by [the fail-closed complete national 15 verifier](../scripts/data_rebuild/verify_official_nba_cup_2025_all_15_national_broadcasts.py) with [ten mutation/failure tests](../tests/test_official_nba_cup_2025_all_15_national_broadcasts.py).

The six *additional* Prime matchup/network tuples from the later NBA.com article are:
- November 7: Houston Rockets at San Antonio Spurs; Golden State Warriors at Denver Nuggets.
- November 14: Miami Heat at New York Knicks; Golden State Warriors at San Antonio Spurs.
- November 21: Indiana Pacers at Cleveland Cavaliers; Denver Nuggets at Houston Rockets.

These six are **verified by August 21 NBA article**, not independently proven to have had the exact same original public network assignments on **August 13**. The first nine retain their independently evidenced **August 14** publication dates in the earlier source. We do not silently backdate the six later-verified rows.

The 15-row source-only checker verifies exact date, opponents, provider and correct official 2025 five-team group membership. It cross-checks inclusion of all original nine August 14 explicitly named tuples. The separately packaged private original research archive comparison can verify whether all 15 were coded exactly in the frozen NBA Cup lookup and later main-season TV PDF, but **that private command has not been run**.

```bash
python scripts/data_rebuild/verify_official_nba_cup_2025_all_15_national_broadcasts.py --source-only
python -m unittest discover -s tests -p test_official_nba_cup_2025_all_15_national_broadcasts.py -v

# Strict acceptance only with the two actual PRIVATE original source ZIPs:
python scripts/data_rebuild/verify_official_nba_cup_2025_all_15_national_broadcasts.py \
  --original-cup-zip /PRIVATE/PATH/nba_player_game_at_risk_star_cup_v1.zip \
  --original-freeze-zip /PRIVATE/PATH/nba_load_management_final_freeze_2026-08-12.zip \
  --output-report /PRIVATE/PATH/2025_Cup_original_fifteen_national_joins.json
```

**Remain open:** the complete August 13 **60-game** first-release Cup PDF and its potentially distinct original network statuses; source-national flags on the **other 45 group games**; all **18 historical knockout per-game exact source/mapping** verifications; full original private archive execution; and all broader causal/manuscript gates. Original NBA Cup championship excluded from regular season. PR draft; Issue open; no original data/manuscript modified.

---

