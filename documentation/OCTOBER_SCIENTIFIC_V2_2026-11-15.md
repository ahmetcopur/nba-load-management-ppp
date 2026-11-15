# Separate October scientific version: SCI-001 and bounded SCI-002

**Current verdict: implementation tested; authentic scientific acceptance pending.**
No new October panel hash or revised regression estimate is accepted by this
change. The retained authentic six-season source tree is not available in the
current execution workspace. The task explicitly permits completing code,
tests and execution instructions under that condition. PR #4 remains draft;
Issue #5 remains open. No manuscript, historical dataset, original executed
script, historical acceptance target, release tag or Git history is modified.

## Scientific versions

| Explicit version | Star predicate | Workload | Role |
| --- | --- | --- | --- |
| `legacy` | Immutable original | Original roster-row history | Numerical/hash control |
| `october_scientific_v2` | Calendar opening star OR actual current All-Star AND effective date reached | Original roster-row history | Proposed SCI-001-only primary |
| `october_workload_physical_sensitivity_v1` | Original | Distinct observed physical games | Unadopted SCI-002-only sensitivity |
| `october_scientific_v2_physical_sensitivity_v1` | Corrected | Distinct observed physical games | Unadopted combined sensitivity |

The original implementation and declared star rule were inspected in audit
commit `dbc12ddf6f51161b583f51e358c3e48aac0f5543`. The original report-only
branch omitted `current_season_all_star`. A SHA-pinned, context-checked patch
is rendered into each **new private** execution folder. Its exact unified diff,
canonical-source hash and actually executed wrapper hash are saved there.
The original builder SHA-256 remains
`81cab67185083572051b44cefbf836acfe6e1860ccf27dd812dc3729aa2a9272`.

Both ordinary roster rows and report-only rows use the same authoritative
player-season calendar. Boolean strings are decoded explicitly; missing or
duplicate calendar identities, unknown flags and selected players without an
effective date fail. A missing base-panel player-season lookup may be resolved
by the calendar, but missing calendar coverage cannot default to a star flag.
Opening stars remain eligible throughout the season. New current-season
selections do not retroactively affect dates before their effective date.

The original embedded regression section has a documented name-collision exit.
The versioned executable stops explicitly **after all eight panel outputs**;
the separately SHA-pinned original fast four-model executable then runs against
the newly generated panel. The unmodified legacy control permits only the
previously documented exact error and only after all eight fresh outputs exist.
No model, covariance formula, fixed effect, control, SCI-003 redundant regressor
or complete-case rule is edited.

## SCI-002 definition decision

The original code literally shifts and rolls over **roster observations** within
player-season. The manuscript's general recent-workload wording does not settle
how duplicate team associations for one physical game should count. The prior
audit's tied-row findings are diagnostic evidence, not authorization to change
the primary model definition. Thus the SCI-001-only primary retains this rule.

The optional alternative collapses player-season-game identities, uses the one
consistent positive minutes value (or zero), and counts participation once.
The prior ten **observed distinct games** supply minutes; current/future minutes
are excluded. Trades do not reset history; a season does. Two team associations
for one game receive identical history. No absent/unobserved game is imputed.
Conflicting positive minutes, conflicting event chronology or simultaneous
distinct games fail for review instead of being ordered arbitrarily. This is
a transparent sensitivity, **not** a recovered historical intention or adopted
new scientific definition. Authentic effects on data and models remain pending.

## Required retained inputs and independent authentication

Use the complete accepted November 15 six-season private run, including:

- `final/final_dataset_manifest.json` and `logs/stages.jsonl`;
- `00c_six_season_sources/six_season_sources.json`, all six source/generated
  trees named by that manifest, preserving its original bytes;
- `03_historical_cadence_inputs/`: all 18 freshly generated parsed/game/team
  inputs, the reviewed original base and original crosswalk/alias auxiliaries;
- the original evidence ZIP and all 26 archives pinned by the accepted public
  manifest, including `nba_player_game_at_risk_star_v1.zip`.

The source manifest is authenticated through the previously reviewed evidence
ZIP, not merely trusted because it says `pass`. Source/candidate counts and all
recorded tree hashes are revalidated. Relocated run roots are supported by
mapping original absolute path references relative to the recorded run root;
the source manifest itself must remain unchanged. Paths escaping that root,
symlinks, source/output overlaps, wrong archive hashes, missing generated inputs,
incomplete stage records and dirty/uncommitted code are rejected.

The evidence ZIP has 37 members and contains final panels and receipts but no
complete parsed-row payload files. It cannot replace the retained source tree.
Archived parsed rows or final CSVs are never substituted to make preflight pass.
The original NBA JSON cache is not required for this localized correction.

## Private Linux amd64 execution

### Explicit earlier retained-intermediate alternative

The owner subsequently supplied the complete November 14
`linux-amd64-json-selectors-003` input tree. Its separately pinned source profile
is `validation/october_scientific_v2_2026-11-15/retained_003_source_profile.json`.
Fifteen of eighteen inputs have the same bytes as November 15. The older 2020
rows and 2025 team table match actual original archive members; the 2025 selected
rows have successful historical receipts for 355 reports/47,187 records. Their
original PDF bytes are rehashed against both SHA-pinned source ZIPs. This is an
explicit **inherited-intermediate** scope, not a new complete candidate-PDF run.
The six-season raw-source gate above is unchanged and never falls back to it.

For this exact bundle, add `--retained-intermediates`, point `--retained-run` at
its separately extracted directory and `--retained-evidence` at the owner's
original uploaded ZIP. The remaining command and scientific gates are identical.
The archive directory needs the original pinned covariates, star calendar,
2020 corrected rows, canonical selector and player-crosswalk ZIPs. The two
original 2025 ZIPs and historical parse receipts are already inside this bundle.
All eight actual builder cases and their models must still pass before this
scope can produce a primary acceptance manifest. It cannot assert recovery of
the lost November 15 source trees or fresh full-candidate execution.

Use a clean committed checkout on Python 3.12 / Linux amd64. Keep originals
read-only (for example read-only container mounts); create a new private output
root outside every Git checkout. Set these variables to actual existing private
locations before executing the following commands:

```bash
export NBA_RETAINED_RUN="/absolute/path/to/accepted-six-season-run"
export NBA_RETAINED_EVIDENCE="/absolute/path/to/NBA_PPP_Six_Season_Reproduction_Evidence_2026-11-15.zip"
export NBA_ARCHIVE_DIR="/absolute/path/to/nba-original-zips"
export NBA_V2_OUTPUT="/absolute/path/to/new-october-scientific-v2-001"

python3.12 -m venv "$HOME/.venvs/nba-scientific-v2-builder"
"$HOME/.venvs/nba-scientific-v2-builder/bin/python" -m pip install -r requirements-builder-lock.txt

"$HOME/.venvs/nba-scientific-v2-builder/bin/python" scripts/data_rebuild/reproduce_october_scientific_v2.py \
  --retained-run "$NBA_RETAINED_RUN" \
  --retained-evidence "$NBA_RETAINED_EVIDENCE" \
  --archive-dir "$NBA_ARCHIVE_DIR" \
  --output-root "$NBA_V2_OUTPUT" \
  --include-workload-sensitivities --check-only

"$HOME/.venvs/nba-scientific-v2-builder/bin/python" scripts/data_rebuild/reproduce_october_scientific_v2.py \
  --retained-run "$NBA_RETAINED_RUN" \
  --retained-evidence "$NBA_RETAINED_EVIDENCE" \
  --archive-dir "$NBA_ARCHIVE_DIR" \
  --output-root "$NBA_V2_OUTPUT" \
  --include-workload-sensitivities
```

Omit `--include-workload-sensitivities` for just the legacy/SCI-001 pair.
With it, eight panels are actually built: four definitions under frozen dates
and four under corrected chronology, each with all four original regressions.
This does not reparse 23,483 PDFs or rebuild the three unrelated final datasets.

The documented February Toronto correction regenerates original Elo/rest/travel
and changes only the declared reviewed base plus two 2021 selector files. The
original chronology gates run on matching legacy controls. Each new version
also gets a complete frozen-vs-chronology diagnostic and date-aware star check.

## Output and verification contract

`scientific_version_manifest.json` is published exclusively and atomically only
after every requested case, comparison and source-immutability check succeeds.
Its status is `primary_verified_secondary_pending`, not full scientific approval.
Every case retains:

- Actual file-open traces for every mandatory generated input, before/after
  hashes, original source identity, rendered patch and subprocess logs.
- Complete decoded panel SHA-256 plus compressed-file identity, schema, counts,
  star/nonstar risk/onset counts and raw eight TV cells.
- Complete stable-player-team-game-key CSV-cell comparison, independent of row
  order. Whole decoded-byte hashes retain row order; these are distinct checks.
- Private full keyed change records; the SCI-001-only comparison authorizes
  **only** `star_PPP_it`, and requires all seven auxiliary outputs unchanged.
- Independent all-row star semantics on frozen and corrected chronology panels.
- Four original model results with SE, CI, p, N, iterations, original inference
  specification and complete-case key-set hashes; paired numerical differences.

Legacy panel hashes and recorded four-model numerical controls remain required.
A legacy panel cannot satisfy SCI-001 acceptance. New accepted hashes are not
predeclared or filled from the earlier RAM-only sensitivity. Failed execution
does not publish a successful manifest. Runtime seconds are excluded only from
the additional scientific model-table identity; the complete table is retained.

## Secondary analyses: separate version-aware command

Use the original shared source commit `0bd713d97e8d519df5700ef473da34aba4495223`
in a separate clean checkout, and the separate pandas-3 October lock:

```bash
python3.12 -m venv "$HOME/.venvs/nba-scientific-v2-october"
"$HOME/.venvs/nba-scientific-v2-october/bin/python" -m pip install -r requirements-october-lock.txt
"$HOME/.venvs/nba-scientific-v2-october/bin/python" scripts/data_rebuild/run_october_scientific_v2_suite.py \
  --scientific-run "$NBA_V2_OUTPUT" \
  --shared-repo /absolute/path/to/clean-pinned-october-checkout \
  --output-root /absolute/path/to/new-october-scientific-v2-secondary-001 \
  --include-workload-sensitivities
```

The new command revalidates primary execution receipts, input hashes, actual
source/panel identities and corrected semantics. It runs the same ten original
scripts unchanged on corrected-chronology controls and selected new versions.
Each subprocess must actually open the newly staged panel; audit scripts get an
explicit `NBA_AUDIT_PANEL` override. The inherited original August auxiliary
for All-Star-only variants remains hash-verified, with its original grouped-fill
transformation unchanged. All 33 CSV outputs must exist. Complete keyed table
differences include samples, p-values and convergence flags; collinear term
label swaps are explicit. New tables are **not** forced to equal old archives.
This command never changes the legacy 33-output acceptance gates.

The secondary manifest's calculation/comparison status is not approval:
nonconvergence, all affected figures, exact paper values and scientific review
still need assessment. See the [impact register](../validation/october_scientific_v2_2026-11-15/downstream_impact.json).

## Manuscript and release proposal

No numeric replacement is proposed until authentic builder and downstream
execution succeed. At that point, replace the affected October star-based raw
cells, four Stage-6 estimates/SE/CI/p/N, downstream tables, home/road figure,
event-study/robustness statements and reported sample identities using the
accepted new outputs. Keep legacy numbers explicitly historical. Explain the
omitted selection predicate and the unchanged scientific eligibility rule.
Evaluate full-model/linear-only uncertainty separately; crossing a p threshold
does not establish a difference between estimates or a causal PPP effect.

SCI-001 is code-corrected but empirically pending. SCI-002 is bounded as an
unadopted sensitivity. The 2025 two-field metadata exception (1,598 rows,
3,196 cells) remains preserved and is not reopened. Expanded original JSON plus
six-season PDF execution, independent classification/award-source review and
publication/privacy decisions remain outside this localized acceptance.
Release A is not ready for a revised scientific freeze or manuscript approval.

## Required acceptance questions

| Question | Evidence-based answer for this implementation |
| --- | --- |
| Q1: Separate incorrect-predicate fix? | Yes: explicit `october_scientific_v2`; original SHA and commands unchanged. |
| Q2: Actual complete authenticated builder execution? | No: retained source tree unavailable; actual preflight exited 2 before output creation. |
| Q3: Every newly generated row correct? | Not established on authentic data. Synthetic rule tests pass; production requires an independent all-row semantic check. |
| Q4: Exactly expected classifications changed? | Pending complete authentic cell comparison. The prior 49-row finding is not forced as a target. |
| Q5: New decoded October hash? | None assigned. |
| Q6: Newly executed authentic four-model results? | None. Only the real original four-model executable on synthetic data was executed in this change. |
| Q7: Difference from earlier audit-only sensitivity? | Cannot establish until the actual builder runs. RAM-only figures are not adopted. |
| Q8: SCI-002 effect and adopted rule? | Authentic new effects pending. Original roster-row rule retained in SCI-001 primary; deterministic physical-game rule is an unadopted sensitivity. |
| Q9: Changed secondary results/statements? | No new authentic changes claimed. All 33 original CSV outputs and affected paper figures/statistics are registered as pending. |
| Q10: Material unresolved errors? | SCI-001 empirical acceptance remains open; workload ambiguity, original specification/rank and scientific limitations remain documented. |
| Q11: Expanded PDF+JSON/provenance? | Combined execution still unverified and not required here. Known 2025 metadata exception preserved; human decisions and original-source evidence boundaries remain inherited. |
| Q12: Ready for scientific freeze/manuscript approval? | No. Code is available for review; authentic reconstruction, downstream results/figures and independent scientific approval remain necessary. |

Local verification: **685 tests passed, 0 failed**, including **28** new
scientific-version tests. The expected negative controls reject the legacy
predicate, source tampering, omitted reads and incomplete execution; they are
passing tests of failure handling, not hidden infrastructure failures.
