# November 11, 2026 — NBA Cup 2023/24 FIRST-release fixture and TV-source audit

## Scope and chronology

The earlier Level-C Cup audit independently verified all 180 group-stage
**unordered opponent pairs** across 2023–25 and the official stage-night
calendars. It did not compare individual date + away + home + first-announced
network tuples to separate contemporaneous published game-by-game releases.

This follow-up supplies a new **120-row independent public-source reference**
for the **entire 2023 and 2024 Cup Group Play seasons**:
[official source fixtures](../validation/official_nba_cup_2023_2024_first_release_group_fixtures.csv).
This is a factual transcription of the **DAY / DATE / AWAY / HOME / NAT TV**
columns from the NBA's separately issued *first Cup schedule releases*,
**not** copied from the project's original research lookup.

- [2023 original August 15 first-release 3-page group schedule](https://ak-static.cms.nba.com/wp-content/uploads/sites/46/2023/08/NBA-In-Season-Tournament-Schedule-as-of-8-15-23.pdf). [Official NBA publication](https://pr.nba.com/nba-announces-group-play-schedule-for-inaugural-in-season-tournament/).
- [2024 original August 13 first-release 3-page group schedule](https://ak-static.cms.nba.com/wp-content/uploads/sites/46/2024/08/Emirates-NBA-Cup-2024-Group-Play-Schedule-as-of-8-13-24.pdf). [Official NBA publication](https://pr.nba.com/emirates-nba-cup-2024-group-play-schedule/).

The full 2023–24 league season release was **August 17**, and the full
2024–25 league season release was **August 15**. Thus these group-game
matchups and their listed networks were known *earlier* than the later general
preseason NBA schedule-by-date PDF. This does **not** imply any misclassification:
the earlier main-PDF audit already checked all five later preseason PDFs
against frozen TV assignments. Here the important issue is first-publication
provenance, not automatically reclassifying any group fixture.

## Independently transcribed source-only invariants

| Invariant | 2023–24 | 2024–25 |
|---|---:|---:|
| Complete group fixture rows | 60 | 60 |
| Distinct group pairings | 60 | 60 |
| All clubs with 2 home + 2 away | 30 | 30 |
| ESPN game labels | 8 | 6 |
| TNT game labels | 6 | 8 |
| Separate NBA TV game labels | 2 | 3 |
| No announced national network (blank) | 44 | 43 |

2023 date distribution: November 3:7; 10:9; 14:10; 17:11; 21:5;
24:10; 28:8.

2024 date distribution: November 12:8; 15:12; 19:6; 22:8; 26:5;
29:10; December 3:11.

These counts are compared to the two first-publication PDFs and independently
checked against the official group draws in the executable source-only gate.
The network field must not collapse separate NBA TV into ESPN/TNT.

Run the source-only, private-input-free validation:

```bash
python scripts/data_rebuild/verify_official_nba_cup_first_release_fixtures.py --source-only
python -m unittest discover -s tests -p test_official_nba_cup_first_release_fixtures.py -v
```

**The source-only gate does not constitute the private original research-row
comparison.** It rejects wrong fixture counts, duplicates, group violations,
home/away errors, date allocation drift, release-date changes, and network
count drift, but cannot prove that a malicious swap of two same-date,
same-network valid opponents is absent. That is why the next gate is the
exact private original lookup comparison below.

## Complete private original research-row acceptance (still needs execution)

The new [fail-closed verifier](../scripts/data_rebuild/verify_official_nba_cup_first_release_fixtures.py)
can directly compare the 120 official first-release rows to:

1. The unchanged **original** `nba_player_game_at_risk_star_cup_v1.zip`,
   pinned to SHA-256 `65c4756b86dfb5757bb84b6be13eafb952375aaa6ce49fc1ddddc6224a4faf70`.
   This verifies all **120 exact (season, date, away, home)** group games.
2. The unchanged **original** `nba_load_management_final_freeze_2026-08-12.zip`,
   pinned to SHA-256 `621ebcd45f2fe886ae87749e9d45b6b8416cfc8fcad5edb3e50a8c4486f670e1`.
   Within it, the pinned original TV package contains the original NBA
   preseason-by-date PDF parsed source rows. Compare all **120 exact
   (season, date, away, home, network)** tuples.

```bash
python scripts/data_rebuild/verify_official_nba_cup_first_release_fixtures.py \
  --original-cup-zip /PRIVATE/PATH/nba_player_game_at_risk_star_cup_v1.zip \
  --original-freeze-zip /PRIVATE/PATH/nba_load_management_final_freeze_2026-08-12.zip \
  --output-report /PRIVATE/PATH/new_nba_cup_2023_2024_comparison.json
```

The two paths are placeholders; use the actual original archives, never
upload them. The script compares data **without modifying** originals,
does not overwrite an existing report, and refuses any unpinned archives.
Only an actual successful run of that strict command permits claiming
**120/120 private fixture/network research-row reconciliation**.

## Important open 2025 and knockout boundaries

The original [NBA August 14, 2025 full-season release](https://pr.nba.com/2025-26-nba-regular-season-schedule/)
explicitly says the 60 Cup Group Play games were announced **August 13**,
and the 30 Cup-dependent December fixtures were still unassigned.
A surviving official [2025 original group draw](https://www.nba.com/news/2025-nba-cup-group-draw-results)
and later [NBA Cup national broadcast details](https://www.nba.com/news/2025-26-schedule-announced)
also help check networks. However an equivalent **complete original
August 13, 2025, 60-row Cup-first-release schedule PDF** has not yet been
retrieved and independently transcribed here. The 2025 general preseason
main PDF had already passed its separate 1,200-row source audit.
Do not present that later PDF as proof of the earlier Cup PDF's binary contents.

All three years' **18 quarterfinal/semifinal actual game-date/away/home
tuples and broadcast providers** remain separate open direct original-source
checks. The original 90 cross-season Cup-dependent TBD fixtures are the
December *knockout/replacement* slots, not the 180 already known group
fixtures. The NBA Cup Championship is not a regular-season game.
Do not infer a causal identification claim from any of these source checks.

## Project handling

Original frozen archives, panel, paper, and regression outputs remain
unchanged. Keep PR #4 **draft/unmerged**, Issue #5 **open** until complete
source-validity and manuscript reconciliation. CI public-source tests do not
simulate a successful original-private-archive execution.
