# NBA Cup Level C — positive synthetic joins and one-command ORIGINAL private acceptance

**November 11, 2026 — audit workflow extension. Original manuscript and all frozen research outputs unchanged.**

## Why this was necessary

The earlier source-only verifier tests correctly rejected altered original
ZIP SHA-256s and mutation of original-source CSVs, but they **did not drive
the downstream, exact source-to-original archive join with a successful
positive test**. That meant a real original ZIP could be hash-authentic
and still fail for a coding error at the join. The inverse danger was that
an accidentally permissive comparison could silently accept a wrong
historical row.

The [new strict reusable comparator](../scripts/data_rebuild/compare_nba_cup_exact_source_rows.py)
is now called directly by the actual original-private entry points for:
- 2023/2024 original 120 first-Cup-release group fixtures (exact away,
  home, date, network versus original Cup lookup and later original
  preseason NBA schedule PDF);
- 2023–2025 18 actual knockout games (exact opponents/date/stage and
  12 quarterfinal venue-host assignments, but **not** the nominal home
  designations of the six neutral-site semifinals);
- 2025 original **19** dated first-party team-report Cup fixtures;
- 2025 original **33** first-party-plus-secondary same-day-dated Cup
  fixtures (three later-edited Pelicans article exceptions remain);
- 2025 **15** nationally listed NBA Cup group games by original NBA
  Aug 21 article (date/home/away and original later NBA preseason
  TV PDF network labels, **not** proof that each was publicly
  broadcast-announced on Aug 13).

The underlying source/reporting tiers, announcement-time caveats and
model-treatment exclusions have not changed.

## What the new public CI actually proves

[17 exact 2023/24 group+knockout synthetic positive/negative tests](../tests/test_nba_cup_original_archive_exact_join_synthetic.py)
and [10 2025 19/33/15 source join synthetic tests](../tests/test_nba_cup_2025_partial_archive_join_synthetic.py)
now exercise the **actual comparison function** with in-memory synthetic
original lookup rows. Their coverage includes:

- a correct exact 120 group key join and a correct 120 literal
  broadcast field join;
- positive 19 and 33 partial source fixtures inside a complete-looking
  synthetic 60-game original lookup;
- the 15 NBA-named national group fixtures joining to a synthetic later
  preseason broadcast source;
- a correct all-18 historical knockout fixture join and exact 12
  quarterfinal home/away assignments;
- **negative** wrong dates, opponent, incorrect home side,
  duplicate/missing game, unknown columns, NBA TV vs blank
  classification drift, same-day ESPN/TNT swaps preserving
  aggregate network totals, NBC vs NBC/Peacock and Prime vs
  Amazon Prime changes, wrong stage, swapped quarterfinal host;
- **intentionally unverified** nominal host side of six
  Las Vegas semifinals, even when its source pair/date matches.

These are powerful tests of join implementation, **not checks against
the two original private ZIPs**; the synthetic "archive" frames were
created *by the tests*.

The [private runner orchestration tests](../tests/test_original_cup_private_source_acceptance_runner.py)
also use *MOCKED* private join calls, authentic original SHA-gate
rejection for altered fake source ZIPs, and strict no-overwrite tests.
They demonstrate that all seven private component subcommands are required
and that one component failure or wrong row count aborts the report,
not that original private bytes were checked.

## One-command original PRIVATE acceptance — not yet executed in this chat

The seven verified real-archive subcommands are now composed in
[one read-only master runner](../scripts/data_rebuild/run_original_cup_private_source_acceptance.py).

On a **private local checked-out copy**, use the authentic historical
archives, **not** reconstructions or re-zipped substitutes:

- `nba_player_game_at_risk_star_cup_v1.zip` pinned full original
  SHA-256 `65c4756b86dfb5757bb84b6be13eafb952375aaa6ce49fc1ddddc6224a4faf70`.
- `nba_load_management_final_freeze_2026-08-12.zip` pinned full
  original SHA-256 `621ebcd45f2fe886ae87749e9d45b6b8416cfc8fcad5edb3e50a8c4486f670e1`.

```bash
python scripts/data_rebuild/run_original_cup_private_source_acceptance.py \
  --original-cup-zip /PRIVATE/PATH/nba_player_game_at_risk_star_cup_v1.zip \
  --original-freeze-zip /PRIVATE/PATH/nba_load_management_final_freeze_2026-08-12.zip \
  --output-report /PRIVATE/NEW/NBA_Cup_Level_C_original_private_source_acceptance.json
```

The runner first checks the **entire original ZIP file hashes**, then
executes independent source validations plus all **seven** pinned
original-data gates. It writes a **new aggregate JSON only after every
component fully passes**. It never overwrites an existing report,
does not include source row records or original player-level data,
and does not write to any original research archive.
All expected row counts/statuses are explicitly rechecked before success.

The component gate numbers are overlapping subsets, **NOT**
additive: 198 historical actual Cup games, 120 original 2023+2024 first
Cup release matches+network fields, 19 original 2025 August 13
first-party matchups, 33 combined first-party/secondary date/host
matchups, 9 August 14 2025 original NBA named broadcast rows,
15 August 21 2025 NBA original named broadcast rows, and 18
historical actual knockout date/stage/participants (12
quarterfinal ordered hosts). The 9 national rows are included
in the later 15; 19 original team games are included in the 33
combined first/secondary fixture coverage.

**This exact private command was NOT executed in this work session:**
the required original ZIP byte streams are unavailable in the
environment or GitHub text connector. A report of public CI test success
must not be described as original research source-data acceptance.

Even an actual original-private full PASS above would **not**
close Issue #5: original *August 13 2025* complete **60-game** first
Cup-source binary and exact first-announced network timestamps remain
open; the six neutral-site semifinal nominal hosts require separate
NBA original game-log confirmation; historical 2020 second-half
NBA TV complete coverage, independent star award history,
human-reviewed medical-label contents and player identity,
non-TV game covariates, complete original master pipeline run
from all six required ZIPs, causal assumptions and manuscript
reconciliation all remain independent research gates.

Keep PR #4 **DRAFT/UNMERGED**, Issue #5 **OPEN**, and the original
frozen data, model and paper intact.
