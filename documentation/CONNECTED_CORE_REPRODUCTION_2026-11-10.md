# Connected reproduction: player-ID resolution to final NBA player-game core

**Status, November 10, 2026:** Executed against the recovered original private source packages. Independently regenerated the resolved player-ID table and fed it into the original player-game finalizer; all ten original output files matched exactly (gzip files compared after decompression). This is a connected **data-generation** step, not a checksum-only audit. Its input starts at an archived selected-report CSV, not raw PDFs.

## One-command runner

From a clean checkout of the draft PR #4 branch, create an environment using the committed reconstruction requirements:

    python3 -m venv .venv
    . .venv/bin/activate
    python -m pip install -r requirements-builder-lock.txt

Keep the following four original private ZIPs together outside the repository: nba_player_game_at_risk_core_v1.zip; nba_player_crosswalk_final_v1.zip; nba_boxscore_roster_frame_v2_output_upload.zip; nba_game_covariates_v1.zip.

    python scripts/data_rebuild/run_connected_player_game_core.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/connected-core-2026-11-10"

The **output directory must not exist**, must not reside inside a Git checkout, and must not be nested in the original ZIP directory. A failed run may leave a partial directory; use a new name for a retry. The script verifies the four original ZIP SHA-256 values before any output, refuses changed original script bytes and never modifies raw archives.

The tested reconstruction environment is Python 3.13.5, pandas 2.2.3, NumPy 2.3.5 (see requirements-builder-lock.txt). These are *not* documented as the original researchers' historical versions.

## What the command creates

It starts with the original archived selected-report rows and independently reruns the sequence:

1. Reviewed season/team/name crosswalk; ambiguous aliases rejected, then only unique reviewed aliases and unique official box-score roster names used as fallback.
2. Original status-priority deduplication: Out, Doubtful, Questionable, Probable, Available. Result: **73,438** resolved player-report rows, 33 columns.
3. Source-hash pinned original finalizer, with **only** its hard-coded filesystem root redirected to the new private output directory. The source code's injury status, absence/risk-set, spell, and provisional taxonomy rules are unchanged.
4. Combine **248,571** official box-score player-games, **159** report-only players and original game/team report and schedule covariates.
5. Generate all core panel CSV outputs and compare their entire decoded bytes against the historical frozen reference.

No private PDFs, raw ZIPs, player-report rows, or reconstructed player-level CSVs are committed to GitHub.

## Exact connected private run

| Independently generated stage / archived output | Result | Frozen equality |
|---|---:|---|
| Resolved player-report table (33 fields) | 73,438 records | Exact |
| Final core player-game panel | 248,730 rows | Exact decoded CSV |
| At-risk onset model panel | 180,829 rows | Exact decoded CSV |
| Provisional absence spells | 13,723 rows | Exact decoded CSV |
| Report-only roster additions | 159 rows | Exact CSV |
| Season summary | six seasons | Exact CSV |
| Onset type by season | six seasons | Exact CSV |
| Designation status by season | six seasons | Exact CSV |
| Taxonomy review sample | 300 records | Exact CSV |
| Core QA JSON | all recorded metrics | Exact bytes |

The finalizer also reports **12,710** absence onsets, no duplicate player-game keys, no missing player IDs and no missing game covariates. Direct reviewed crosswalk assignments: 72,819; reviewed alias fallback: 606; unique roster-name fallback: 15; unresolved: zero.

For compressed files the exactness gate compares all **decompressed** CSV bytes. Gzip header timestamps can differ even when every CSV byte is identical.

[Real-input sanitized source fingerprints and all ten decoded-output hashes](../validation/level_c_injury_pdf_real_2026-11-10/connected_identity_to_core_exact_2026-11-10.json)

[One-command executable](../scripts/data_rebuild/run_connected_player_game_core.py) | [Original player-ID resolver replay](../scripts/data_rebuild/verify_player_identity_replay.py) | [Synthetic fail-closed tests](../tests/test_connected_player_game_core.py)

The new runner has explicit checks for immutable original finalizer code, exact output schema and values, unique ZIP members, private output location, missing or modified inputs, and the historical core release counts. Synthetic regression tests are run in GitHub Actions. **GitHub-hosted CI has no private source ZIPs; the real-input acceptance was executed locally with equivalent original source stages before packaging the single command.**

## Remaining end-to-end data dependencies

**This command does not yet start from raw official NBA PDFs.** The original PDF parse/report selection/reason mapping stages were independently verified in earlier source-audit runs, but their outputs have not all been connected into one command generating the selected-report CSV input. Separately, the player-game core lacks independently regenerated original award/All-Star/All-NBA star history, NBA Cup labels, age/biographical metadata, reviewed frozen injury taxonomy, and manuscript-ready TV/regression enrichments.

The 2020–21 PDF layout issue remains: **93** free-text reason fields differ in a diagnostic reparse (25 rows selected into games); player IDs and status fields match. Do not silently substitute that reparse's reasons.

The next stage is to connect the PDF-derived selected report rows into this executable core, then reconstruct reviewed analysis-ready variables from their actual upstream award/taxonomy/TV files instead of copying final labels from a frozen output. Only then refit the manuscript specifications.

See [Issue #5](https://github.com/ahmetcopur/nba-load-management-ppp/issues/5) for remaining scientific gates. Preserve the frozen research and keep PR #4 **draft and unmerged**.


## Extension: one-command core plus source-coded All-Star/All-NBA history

The previous core-stage run was extended in a real private execution to the historical **star award enrichment**. The source-coded original All-Star/All-NBA builder from the authentic nba_player_game_at_risk_star_v1.zip was checked for the exact source SHA-256, relocated to the new private output root by changing **only four hard-coded /mnt/data/ path prefixes**, and executed against the newly rebuilt core panel.

All **12** original non-manifest star package files reproduced exactly, including the original embedded award lists, source builder code, 248,730-row full star panel, 180,829-row at-risk star panel, complete season-level star calendar, and QA metrics.

### Preferred combined command

Put a **fifth original ZIP**, nba_player_game_at_risk_star_v1.zip, in the same private archive directory as the four core-stage ZIPs. Then run:

    python scripts/data_rebuild/reproduce_core_and_stars.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/core-and-stars-run"

This is a **new, separate output directory** that must not yet exist. The umbrella command verifies availability and SHA-256 of the star archive **before** executing the initial core stage; it then runs source-pinned identity resolution, the original core finalizer, all ten core byte comparisons, the original source-coded star builder, and all twelve star output comparisons.

For an already accepted connected core result, run only the star extension:

    python scripts/data_rebuild/run_connected_star_enrichment.py \
      --archive-dir "$HOME/nba-original-zips" \
      --core-run-dir "$HOME/nba-private-rebuild/connected-core-2026-11-10"

The star-only command requires a valid **connected_core_reproduction_report.json** with the exact ten-file acceptance marker, and rechecks that generated core outputs still match the immutable original. It rejects an already existing star-output directory or star ZIP because the archived star builder contains historical directory-deletion and ZIP-unlink operations; neither destructive path can be pointed at any prior run or original source.

| Independently run star stage | Result |
|---|---:|
| Original All-Star/All-NBA award input rows | 358 |
| Player-game core rows | 248,730 |
| At-risk star panel rows | 180,829 |
| Star-designated player-game observations | 23,166 |
| Midseason current-All-Star transition rows | 1,019 |
| Missing star-status labels | 0 |
| Full comparison to the frozen star package | **12/12 substantive original files exact** |

[Original-star replay evidence and decoded-byte SHA values](../validation/level_c_injury_pdf_real_2026-11-10/connected_core_and_star_exact_2026-11-10.json) | [Standalone original star runner](../scripts/data_rebuild/run_connected_star_enrichment.py) | [One-command core+star runner](../scripts/data_rebuild/reproduce_core_and_stars.py) | [Synthetic safety/regression tests](../tests/test_connected_star_enrichment.py)

**Scientific qualification:** the original award lists are embedded in the historically archived source code. This reproduces their application exactly but **does not independently verify all 358 awards/replacements from the cited official NBA announcements**. Similarly, the NBA Cup lookup and original full analysis-ready taxonomy/regression sources are further dependencies; Cup/TV/manuscript results are not automatically certified by this stage. The original star archive's file_manifest_sha256.csv describes compressed gzip members, whose headers may have different timestamps; the twelve substantive source/output files were compared over their *entire decoded contents* instead.


## Extension: NBA Cup lookup-based enrichment (new source implementation)

The real-input connected reproduction was extended by **one further generated
stage**: source-coded All-Star panels were enriched with game-level 2023–26
NBA Cup flags and interactions from the immutable historical
nba_player_game_at_risk_star_cup_v1.zip lookup. The original archived
build_cup_flags_v1.py file is only a short explanatory **stub**, so this
stage is an explicitly **new implementation** of the historical lookup
transformation, not a claim that the original Cup Python code was rerun.

The new code joins all 7,230 games in the immutable lookup, carries
the source-identified 198 regular-season Cup fixtures (60 group,
four quarterfinal, two semifinal games per Cup season), generates the 13
additional model columns, clears the historical cup_game_pending flag, and
retains the unique player-team-game key across trade-team transitions.

### Run core + original stars + Cup in one command

Include a **sixth private ZIP**, nba_player_game_at_risk_star_cup_v1.zip,
alongside the other original core/star archives, then:

    python scripts/data_rebuild/reproduce_core_and_stars.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/core-stars-cup" \
      --with-cup

This command constructs and validates the original identity/core and
source-coded All-Star/All-NBA stages, then creates the Cup panels and spells
from the source game-level lookup. The output directory must be NEW and
outside the Git repository. The standalone final step is also available
for an already accepted core+star run:

    python scripts/data_rebuild/run_connected_cup_enrichment.py \
      --archive-dir "$HOME/nba-original-zips" \
      --work-dir "$HOME/nba-private-rebuild/core-and-stars-run"

The standalone stage checks both prior success reports, both original
star/Cup source ZIP hashes and original Cup game-stage counts. Each large
panel is generated in a distinct subprocess to avoid memory carryover
between the full panel, onset-risk subset, and spell table. The stage
then compares the entire DECODED output CSV against the original
immutable source archive; any difference is a hard failure.

### Real original-input generated results

| Freshly generated Cup-stage table | Rows | Fields | Exact frozen comparison |
|---|---:|---:|---|
| Full Cup player-game panel | 248,730 | 115 | Yes, all decoded CSV bytes |
| At-risk Cup panel | 180,829 | 61 | Yes, all decoded CSV bytes |
| Cup-enriched absence-spell panel | 13,723 | 37 | Yes, all decoded CSV bytes |

The original lookup itself has 7,230 unique game IDs and 198 Cup
regular-season fixtures. The full three-panel equality is recorded,
including exact decoded SHA-256 values, in the
[sanitized connected Cup evidence](../validation/level_c_injury_pdf_real_2026-11-10/connected_cup_lookup_exact_2026-11-10.json).
New implementation: [Cup lookup-to-panel builder](../scripts/data_rebuild/run_connected_cup_enrichment.py);
[synthetic failure tests](../tests/test_connected_cup_enrichment.py).

**Scope limitation:** Cup schedules and dates in cup_game_lookup.csv
are INHERITED from the original research package. The new generator
independently performs the merge/interaction/spell construction, but
does NOT independently recreate or prove the lookup's official NBA
2023–26 release-time evidence. That is a separate upstream validation
task. The complete raw-PDF and manuscript regression path is likewise
still not one continuous executed dependency graph. No original/frozen
data or private PDFs were modified or pushed to GitHub.


## First original-PDF entrypoint: 2025–26 source rows

An independently executed next-stage run replaced the **entire original
2025–26 selected-report CSV input** with player-report records **generated
directly from the saved original NBA injury-report PDFs**. The two original
2025 private raw ZIPs passed the pinned original archive SHA-256 checks and
the unmodified historical parser had original source SHA-256
197c29d46dfea221c381664b96a05453737df55d7b8dd5d5e6f44e49b69e0e06.

- Reparsed **729 original 2025–26 league PDF reports** from the initial plus
  later targeted archives.
- Reproduced **13,968 2025–26 selected player-report rows**, including every
  one of the **22 original CSV fields** with **zero missing or extra complete
  records**. This comparison was an order-independent complete-record
  multiset, NOT only a row count.
- Replaced only the 2025–26 selected rows inside the 73,547-row historical
  report input; the other **59,579 selected source rows from 2020–21
  through 2024–25** remain explicitly archived historical inputs.
- Independently regenerated the **73,438 player-ID table** from this mixed
  source, then ran the unchanged original core and star scripts and the
  source Cup-lookup reimplementation in a **fresh output directory**.
- All **10 core, 12 star and three Cup full decoded CSV outputs matched**
  their exact frozen references. No core, onset, absence, star or Cup
  model field changed.

The original **source-selected PDF identity and published timestamp**
choices remain inputs from the original canonical game map in this
specific run. Those choices have been independently reconstructed from
the saved initial/targeted report manifests in the earlier
[2025 selector audit](../validation/level_c_injury_pdf_real_2026-11-10/independent_2025_manifest_selection.json),
but this particular 2025 PDF-to-row entrypoint does not rerun the
manifest selector algorithm.

### One-command entrypoint (original 2025 PDFs included)

Place the same original six core/star/Cup ZIPs alongside **two
additional original raw report ZIPs** in the private source folder:

- audit_2025_26_upload.zip
- audit_2025_26_targeted_upload.zip

With eight immutable original ZIPs in the private folder, from a clean
checkout of audit-rebuild-reliability-2026-11:

    python scripts/data_rebuild/reproduce_core_and_stars.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/raw2025-core-stars-cup" \
      --from-original-2025-pdfs \
      --pdf-workers 4 \
      --with-cup

This newly packaged invocation performs the original 2025 PDF parse
and **full 22-field frozen-row acceptance** in a disposable private
scratch directory before feeding the generated rows into the original
source-pinned identity resolver/finalizer, the historical star builder
and the Cup lookup stage. It fails closed on altered raw ZIPs,
missing/ambiguous PDFs, parser mismatch, altered 2025 complete records,
changed player-ID allocations and changed final outputs.

The equivalent exact-input **constituent transformations were
independently executed** in the model's local private environment and
their combined output validated, but the *newly committed umbrella CLI*
has **not yet separately been run with all eight real private ZIPs from
a clean checkout**. Its synthetic CI tests cover source metadata
matching, original-row schema/values, safety and the optional CLI.
Do not mistake synthetic CI alone for execution of this full private
pipeline. The already executed empirical evidence is preserved in
[2025 original PDFs to 25 exact downstream outputs](../validation/level_c_injury_pdf_real_2026-11-10/fresh_2025_pdfs_to_connected_core_stars_cup.json).

Standalone selected-report parser, which emits private source rows
without changing original archives:

    python scripts/data_rebuild/rebuild_2025_selected_from_pdfs.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/parsed-2025-selected" \
      --workers 4

Its generated CSV can also be injected into the standalone core
runner with --reparsed-2025-selected-csv. Both private output directories
must be new and outside any Git checkout.

**Still not full six-season raw-source reproduction:** this 2025
entrypoint fixes one season's raw source input; it retains the other
five seasons' selected player-report rows and inherited official
award/Cup/TV/covariate source assumptions. The 2020–21 fixed-width
extractor still has **93 reason-text differences**, of which **25**
occur in 12 selected games. Do not replace those source reasons with
the current diagnostic reparse. The end-to-end manuscript model
calculation and original TV/award/Cup release provenance checks remain
separate steps. PR #4 stays draft.


## Five-season original NBA PDF entrypoint: 2021–22 through 2025–26

A further real original-source execution has now progressed beyond 2025-only.
We recovered the authentic 2021–22, 2022–23, 2023–24 and 2024–25
raw NBA injury-report ZIPs, verified their immutable complete ZIP SHA-256s
against the original inventory, and independently reparsed **every
saved selected original PDF** using the correct unchanged original
season-layout parser.

| Season | Authentic saved selected NBA PDFs parsed | Complete selected player-report rows | Exact matches among 22 frozen fields |
|---|---:|---:|---|
| 2021–22 | 570 | 12,527 | All |
| 2022–23 | 584 | 11,499 | All |
| 2023–24 | 564 | 12,897 | All |
| 2024–25 | 573 | 14,065 | All |
| 2025–26 (already executed previously) | 729 | 13,968 | All |
| **Five-season total** | **3,020** | **64,956** | **0 complete-record differences** |

The two **early-layout** seasons (2021–22 and 2022–23) require the
original immutable parser_2021_2022.py, SHA-256
321d9c8d807325209fbcb6174ec6d82df4ba845c156d7d52158f0ea44714ab3e.
The three **later-layout** seasons require the immutable
parser_2023plus.py, SHA-256
197c29d46dfea221c381664b96a05453737df55d7b8dd5d5e6f44e49b69e0e06.
Using the later parser on 2022 original PDFs yields zero extracted
rows; using the correct earlier parser reproduces 11,499 exact
selected rows. The original older parser produced 40 nonfatal
warnings for selected 2021 PDFs and 42 for selected 2022 PDFs;
the later parser produced zero warnings in selected 2023 and two
in selected 2024 PDFs. Despite these warnings every reconstructed
selected player-record field matches the archived source. One
duplicate 2021 selected report record is eliminated with the
original exact key-based duplicate rule.

The legacy original 2021–22 fixture joins include two corrected
Toronto game assignments. The source-coded literal matchup
map for CHI@TOR and MIA@TOR is retained in the new generator,
and all 12,527 complete 2021 selected records match the historical
reference. This is an **original source rule**, not an output-field
patch based on a reference player row.

The private source-input integration then replaced **all 64,956
archived selected rows** from those five seasons with newly extracted
original-PDF records, retaining only the 8,591 2020–21 selected
report rows from the frozen source. The 73,547-row six-season
source table was passed into the independently rerun original
crosswalk/alias/official roster identity resolver, then the unchanged
historical core finalizer and source-coded All-Star/All-NBA builder,
and the original Cup lookup reimplementation.

**Actual connected generated result:** all **10 core, 12 star, and
three Cup outputs reproduce exactly**, including all 73,438 final
resolved player-report rows, 248,730 player-game rows, 180,829 at-risk
rows, 12,710 absence onsets, 13,723 spells and 159 report-only
roster additions. The acceptance checks compare entire CSV
byte streams after gzip decompression where necessary; they do
not merely compare summary counts. All original ZIPs, source
PDFs and original frozen datasets were left unchanged.

### Preferred five-season raw-source command

Add four original raw ZIPs to the previous eight-ZIP source directory:

- audit_2021_22_upload.zip
- audit_2022_23_upload.zip
- audit_2023_24_upload.zip
- audit_2024_25_upload.zip

With **12 immutable original ZIPs** in the private directory, use
the newly committed five-season source generator and integrated command:

    python scripts/data_rebuild/reproduce_core_and_stars.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/raw2021-to-2025-core-stars-cup" \
      --from-original-2021-2025-pdfs \
      --pdf-workers 8 \
      --with-cup

The command regenerates selected PDF records for 2021–24 and
2025 separately in disposable private scratch areas; it
checks every season's complete frozen 22-field row multiset
before inserting it into the original identity resolver,
runs the original core finalizer, original award/star builder
and source-Cup enrichment, and fails closed on any final
decoded byte difference. It refuses original ZIP SHA drift,
missing/ambiguous original PDF names, unsupported 2020
raw replacement, missing source fields and an already existing
private output directory. It never writes player-level
data into the Git repository.

You can also run the upstream raw 2021–24 generator alone:

    python scripts/data_rebuild/rebuild_2021_2024_selected_from_pdfs.py \
      --archive-dir "$HOME/nba-original-zips" \
      --output-dir "$HOME/nba-private-rebuild/raw2021-to-2024-selected" \
      --workers 8

[2021–24 authentic-PDF parser and original report choice connector](../scripts/data_rebuild/rebuild_2021_2024_selected_from_pdfs.py) |
[Multi-season source-to-core input guard](../scripts/data_rebuild/run_connected_player_game_core.py) |
[Five-season real private output acceptance evidence](../validation/level_c_injury_pdf_real_2026-11-10/five_seasons_real_pdfs_to_25_exact_core_star_cup_outputs.json) |
[Fail-closed synthetic tests](../tests/test_raw_2021_2024_to_connected_core.py)

**Reproduction status qualification:** all five-season original-PDF
source and successive identity/core/star/Cup transformations were
executed on a private working environment with genuine original
input archives. The *new GitHub 12-ZIP one-command wrapper* has
not separately been accepted end to end from a fresh checkout
with those original ZIPs; its synthetic CI tests exercise its
interface, source comparators and failure modes, but CI has
no raw ZIPs. Do not substitute synthetic CI for true raw-source
acceptance evidence.

**Remaining critical gap:** 2020–21 still uses the authoritative
original selected rows because a current 617-PDF diagnostic parser
run leaves **93 free-text reason mismatches**, of which **25
selected player records across 12 games** are affected.
The original report-choice metadata for 2021–25 remains
an inherited source input to the five-season PDF connector,
although it has been independently reconstructed and checked
in separate audits. Complete independent award announcement,
Cup announcement, TV source, roster-name adjudication and
manuscript model refitting are also still pending. Do not
mark the original frozen paper end-to-end reproducible or merge
draft PR #4 solely because this stage passes.
