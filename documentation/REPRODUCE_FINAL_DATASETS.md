# Reproduce the final corrected NBA analysis datasets

This is the canonical entry point for the February 2022 Toronto corrected chronology:

**[scripts/data_rebuild/reproduce_final_datasets.py](../scripts/data_rebuild/reproduce_final_datasets.py)**

It runs the pre-existing original August and October source reconstruction scripts, checks the frozen historical baseline, applies Toronto corrections to private copies, independently checks complete decoded CSV SHA-256 fingerprints, verifies player-game keys, counts and Stage-6 estimates, and creates a single private acceptance manifest.

**The code is public; the original injury reports, box-score files and generated individual-level player data are NOT.** Bring the original research ZIP archives separately. Do not use a downloaded final dataset as a substitute for the source archives.

The [supplied authentic targeted October execution](AUTHENTIC_2020_OCTOBER_DOWNSTREAM_2026-11-14.md) reports all three fresh 2020 inputs actually opened and all eight frozen intermediate outputs matching decoded bytes. This establishes the targeted original-builder path; corrected final panels were not rebuilt in that test.

## The generated final files

The targeted acceptance command also supports `--season 2022-23`. It reparses all 4,101 original regular-season candidates, generates the game selector, the actual S4 team-status input, and full regular-season parsed rows, then traces their use by October. The required sources are already in the existing private ZIP inventory. See [authentic isolated 2022 parser/selector results and pending downstream gate](ORIGINAL_2022_CANDIDATE_SELECTOR_2026-11-14.md). Select a new output root for the test.

For the next targeted season, the same acceptance command accepts `--season 2021-22`. Supply the original `audit_2021_22_s4_join_results.zip` alongside the existing archive inventory and choose a new output root. It parses all 5,567 original hourly PDFs, exports verified full/harmonized selectors, and substitutes the new harmonized rows and game/team tables before tracing their use by October. See [authentic isolated 2021 source/selector results and outstanding downstream gate](ORIGINAL_2021_CANDIDATE_SELECTOR_2026-11-14.md). This does not run the three corrected final datasets.

### Targeted 2020 downstream acceptance after the accepted nine-stage run

Run `python -m scripts.data_rebuild.accept_2020_raw_selector_downstream --archive-dir /archives --prior-run-root /runs/linux-amd64-json-selectors-003 --output-root /runs/raw-2020-downstream-001` in the pinned Linux amd64 builder environment. The prior run root and all source ZIPs must be mounted read-only; the new output must be absent and private. This command reparses only the 617 original 2020 PDFs (or revalidates an explicitly supplied `--fresh-2020-source-dir`), regenerates the 2020/2024 selector tables, copies the prior historical input tree, substitutes fresh 2020 row/selector files, and runs the original October builder. A Python audit hook observes the original subprocess opening all three required 2020 files; their hashes must be identical before and after execution. All eight original intermediate outputs are compared as complete decoded bytes to the prior frozen run, the new panel must match the immutable frozen hash, and the original frozen Stage-6 model gate executes. Success writes private `downstream_acceptance.json`. This test concerns the frozen October builder; it does not rerun corrected chronology or constitute a new three-final-dataset acceptance. The supplied authentic run passed; see the linked targeted acceptance record above.

| File under the private final/ folder | Purpose | Rows | Decoded CSV SHA-256 |
|---|---|---:|---|
| august_latest_pre_tip_full.csv.gz | Corrected August full analysis-ready panel | 248,728 | 2acd7448a357163951700c99df33a6949e20b19afc2219e6f8c3082b14d3619d |
| august_latest_pre_tip_at_risk.csv.gz | Corrected August latest-pre-tip regression input | 180,831 | 5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3 |
| october_cadence_player_games.csv.gz | Corrected October common-time primary model panel | 248,778 | 2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67 |
| corrected_august_provisional_spells.csv.gz | Corrected provisional absence spells, NOT newly human-adjudicated taxonomy | — | Captured in manifest |
| final_dataset_manifest.json | Input ZIP hashes, final data hashes, QA counts, Stage-6 models, private stage logs | — | — |

Expected at-risk/onset counts: August **180,831 / 12,707**; October **180,664 / 12,729**. The primary corrected regression has 180,530 complete cases; national-partner TV effect **+2.674231729 pp (p=.042633966)**, linear-only **+1.282369453 pp (p=.330867541)**. These are *acceptance checks*, never substitutions into an input.

**August latest-pre-tip and October cadence data are intentionally distinct.** Do not mix their reports, eligible risk sets, or spell histories.

## Run from a clean checkout

Use Python 3.12, the pinned requirements-builder-lock.txt dependency set (pandas 2.x), the private authentic source ZIPs, and an output destination that does not exist and is outside every Git checkout.

~~~bash
git clone https://github.com/ahmetcopur/nba-load-management-ppp.git
cd nba-load-management-ppp
git switch audit-rebuild-reliability-2026-11

python3.12 -m venv "$HOME/venvs/nba-builder"
source "$HOME/venvs/nba-builder/bin/activate"
python -m pip install -r requirements-builder-lock.txt

# Get exact required historical source ZIP names.
python scripts/data_rebuild/reproduce_final_datasets.py --list-inputs

# Confirm all named ZIP files exist and outputs can be created privately.
python scripts/data_rebuild/reproduce_final_datasets.py \
  --archive-dir "$HOME/private/nba-original-zips" \
  --output-root "$HOME/private/nba-final-run-001" \
  --check-only

# REBUILD the three corrected final analysis CSVs from original input ZIPs.
python scripts/data_rebuild/reproduce_final_datasets.py \
  --archive-dir "$HOME/private/nba-original-zips" \
  --output-root "$HOME/private/nba-final-run-001"
~~~

Use a new output directory per run (e.g. run-002). Never overwrite the original ZIPs, the frozen release or an earlier successful manifest. A failed stage leaves its private logs and partial intermediates, but never writes an accepted final_dataset_manifest.json.

### Optional: original raw-PDF source checks

In addition to the original historical ZIPs, obtain the original six-season injury-report PDF archives listed by the --list-inputs command. Then add the --verify-original-pdfs flag.

~~~bash
python scripts/data_rebuild/reproduce_final_datasets.py \
  --archive-dir "$HOME/private/nba-original-zips" \
  --output-root "$HOME/private/nba-final-with-pdfs-001" \
  --verify-original-pdfs
~~~

**Precise scope:** the extra original-PDF stage rebuilds the six-season frozen player core, verifies it independently, and then **feeds the directly PDF-derived, identity-resolved 73,438 selected player-report rows into the August baseline and Toronto-corrected finalizer**, after enforcing exact equality across all 33 historical source fields. The source-derived August core is used to generate the corrected latest-pre-tip analysis-ready outputs. Other historical inputs (covariates, team-game reports, roster, manual awards/Cup/TV mappings) still come from pinned original ZIPs. The October cadence correction still uses historical selected-report intermediates; the PDF-derived original reviewed base is substituted after exact decoded-hash comparison, while season-specific report selection is not injected. This is a partial raw-to-corrected source path, not an assertion that every historical source is re-downloaded or manually adjudicated. Original official box-score JSON verification can be connected to the August finalizer using the additional options below.

### Optional: connect original NBA box-score JSON to the August finalizer

The original 7,230 JSON cache is **additional private input**; it is not in the 22 historical ZIPs. The original V1 output directory must contain `raw_json/` (7,185 original files) and `download_log.csv`. The V2 `raw_json_discovery/` directory must contain the other 45 original files. Supply the original `nba_boxscore_roster_frame_v2_repair.zip`; the `repair_boxscore_rosters.py` **member inside it** must have SHA-256 `c3d1c8be0dd80f5249935bac8c5de4811dc37cbb6810a98e93202a19e0b32fd0`. The ZIP container hash itself is recorded during verification but not pinned because the historical evidence pins the executable member. The historical roster repair needs pandas 3.0.5, separately from the pandas 2.2.3 final builder:

~~~bash
python3.12 -m venv "$HOME/venvs/nba-boxscore"
"$HOME/venvs/nba-boxscore/bin/python" -m pip install -r requirements-boxscore-lock.txt

python scripts/data_rebuild/reproduce_final_datasets.py \
  --archive-dir "$HOME/private/nba-original-zips" \
  --output-root "$HOME/private/nba-final-raw-001" \
  --verify-original-pdfs \
  --boxscore-v1 "$HOME/private/nba_boxscore_roster_frame_v1_output" \
  --boxscore-discovery "$HOME/private/nba_boxscore_roster_frame_v2_output/raw_json_discovery" \
  --boxscore-repair-zip "$HOME/private/nba_boxscore_roster_frame_v2_repair.zip" \
  --boxscore-python "$HOME/venvs/nba-boxscore/bin/python" \
  --check-only

# Remove --check-only and choose a new --output-root for the real execution.
~~~

The raw-cache verifier checks JSON structure, original logged byte lengths, every present JSON SHA-256, 7,230 official game identities, the archived four roster tables and the frozen box-score base. Only its fully matched rebuilt `game_roster_players.csv` feeds the **private** original August finalizer and corrected August copy. The handoff checks every non-path source cell and player/game identity. The historical and regenerated `raw_json_path` values identify the same season/game JSON but differ in their machine-specific prefixes; the private finalizer input retains the historical path while using regenerated values for all other fields. The manifest reports that explicit exception and the number of path differences. The finalizer still requires the exact frozen baseline hash. Original per-game download hashes were never retained, so present-file hashes cannot establish original download-byte provenance. The original PDF baseline stage and October selector still use the archived roster; this option does not make the October cadence fully raw-boxscore-derived.

On runs with all four `--boxscore-*` inputs, stage `01b_json_pdf_original_reviewed_base` rebuilds the original reviewed analysis base **from the original-PDF and original-NBA-JSON-derived August baseline core**, requiring exact decoded output equality before the October base handoff. This connection passed in the [authentic combined `linux-amd64-json-selectors-003` run](AUTHENTIC_SELECTOR_JSON_FINAL_RUN_2026-11-14.md). The October season selectors and their team statuses remain a separate provenance boundary.

### Optional: regenerate and feed 2020–21/2024–25 selectors from historical parsed rows

Place the original `audit_2020_21_s4_join_results_rechecked.zip` and `audit_2024_25_s4_join_results.zip` next to the 22 original ZIPs. `--list-inputs` prints their pinned SHA-256 hashes. Add `--rebuild-2020-2024-selectors-from-historical-rows` to a fresh run. The original selector algorithm is executed, both full and harmonized game/team tables are checked against archival rows, keys and metrics, and the four harmonized tables are copied into the private October input directory before the builder runs. The other four seasons' selectors remain inherited. **This option still uses historically parsed report rows and schedules from archives, not newly parsed original PDFs.** See the [season-by-season selector dependency audit](OCTOBER_SELECTOR_DEPENDENCY_AUDIT_2026-11-14.md) and the [successful authentic combined run](AUTHENTIC_SELECTOR_JSON_FINAL_RUN_2026-11-14.md).

To instead feed **fresh 2020–21 raw-PDF-derived full rows** into that selector and October's 2020 parsed-row input, add `--rebuild-2020-selector-from-original-pdfs` to the same command together with `--verify-original-pdfs`. The 2020 PDF parser reuses the existing six-season raw-source stage and retains the 41,780 verified full source rows privately. The selector checks their complete record equality and SHA-256, runs the original selection algorithm, and requires its newly generated game/team tables and full parsed rows at the October handoff. In an isolated authentic 617-PDF execution, the 41,780 original rows, 8,591 selected rows, four 2020 selector tables and all 13 metrics per panel matched; a full final-dataset run **with this new flag** has not yet executed. Historical report publication clocks and the 2024 parsed rows remain inherited. The [dependency inventory](FINAL_DATASET_DEPENDENCY_GRAPH_2026-11-14.json) lists other computational and reviewed inputs.

**Apple Silicon execution:** the historical frozen August baseline requires the Linux amd64 floating-point serialization; a native macOS arm64 run can fail the exact original core checksum in seven Elo/travel fields. For the PDF plus original NBA JSON run, use one Linux amd64 container with two isolated Python environments. From the repository checkout, with Docker running:

~~~bash
mkdir -p "$HOME/nba-reproduction-runs"
docker run --rm --platform linux/amd64 \
  -v "$PWD:/repo:ro" \
  -v "$HOME/nba-original-zips:/archives:ro" \
  -v "$HOME/nba-load-audit/nba_boxscore_roster_frame_v1_output:/boxscore-v1:ro" \
  -v "$HOME/nba-load-audit/nba_boxscore_roster_frame_v2_output/raw_json_discovery:/boxscore-discovery:ro" \
  -v "$HOME/nba-load-audit/nba_boxscore_roster_frame_v2_repair.zip:/repair.zip:ro" \
  -v "$HOME/nba-reproduction-runs:/runs" \
  -w /repo python:3.12-slim sh -lc '
    python -m venv /tmp/nba-boxscore &&
    /tmp/nba-boxscore/bin/python -m pip install --no-cache-dir -r requirements-boxscore-lock.txt &&
    python -m pip install --no-cache-dir -r requirements-builder-lock.txt &&
    python scripts/data_rebuild/reproduce_final_datasets.py \
      --archive-dir /archives --output-root /runs/linux-amd64-json-001 \
      --verify-original-pdfs --boxscore-v1 /boxscore-v1 \
      --boxscore-discovery /boxscore-discovery --boxscore-repair-zip /repair.zip \
      --boxscore-python /tmp/nba-boxscore/bin/python'
~~~

Choose a **new** output-root name per attempt. The mounts for the repository, archives and raw JSON are read-only; only `/runs` is writable. Keep failed native macOS output separate. If a stage fails, examine its private log in the corresponding `/runs` directory. The earlier successful 22-ZIP run used Linux amd64 without the extra original JSON handoff; its success does not establish that this additional stage passes.

If **all** build stages completed successfully but a later manifest check failed, fix the checker in Git and use `--finalize-existing` with the same source and output paths. It requires one ordered successful start/finish record and log for every planned stage, rechecks all 22 source ZIP hashes, the raw repair script, all three decoded dataset hashes and counts, original PDF baseline, the full boxscore and August handoff reports, corrected model estimates, and then writes `final/` and the manifest. It refuses an existing `final/`; it never runs a builder or silently resumes an incomplete stage. The manifest marks the stages as reused from the completed private run. For the completed `linux-amd64-json-002` stages, from a Mac checkout with both private source paths available:

~~~bash
source "$HOME/.venvs/nba-builder/bin/activate"
python scripts/data_rebuild/reproduce_final_datasets.py \
  --archive-dir "$HOME/nba-original-zips" \
  --output-root "$HOME/nba-reproduction-runs/linux-amd64-json-002" \
  --verify-original-pdfs \
  --boxscore-v1 "$HOME/nba-load-audit/nba_boxscore_roster_frame_v1_output" \
  --boxscore-discovery "$HOME/nba-load-audit/nba_boxscore_roster_frame_v2_output/raw_json_discovery" \
  --boxscore-repair-zip "$HOME/nba-load-audit/nba_boxscore_roster_frame_v2_repair.zip" \
  --boxscore-python "$HOME/venvs/nba-boxscore/bin/python" \
  --finalize-existing
~~~

## Source-to-final dependency boundaries

| Source or decision | Current reconstruction and downstream consumer | Status |
|---|---|---|
| 3,637 original NBA injury-report PDFs | Original parser, player identity resolution and 73,438 selected rows; source handoff to August original/corrected finalizer and original reviewed analysis base, then October base handoff | Connected when `--verify-original-pdfs`; season-specific October selector remains archived |
| 7,230 original NBA box-score JSONs, original download log, repair source ZIP | Full V2 roster replay; non-path fields and normalized source JSON identity feed August original/corrected finalizer | Connected only with all four `--boxscore-*` options; original PDF baseline and October selector still inherit roster |
| Canonical snapshot/game and team selection | Six season maps from `nba_canonical_snapshot_selector_v1.zip`; 2022/23 team status from S4 archives | Historical replay and independent selector verifiers exist, but newly rebuilt selector files are not yet fed into corrected October |
| 2020–24 parsed season report rows | Five individual `audit_*` archives in `restore_historical_layout.py` | Historical intermediate replay in October; not a live raw-PDF-to-October handoff |
| 2025–26 report rows | Original upload and targeted-upload ZIPs; October builder reparses | Connected from the supplied original source archives |
| Player crosswalk and alias decisions | `nba_player_crosswalk_final_v1.zip`; alias table checked for conflicting archive copies | Human identity decisions inherited, SHA-pinned ZIP |
| Game covariates, scheduling and travel/Elo | `nba_game_covariates_v1.zip` plus February 2022 physical-game date correction/recalculation | Historical covariates inherited; corrected values recalculated |
| Star/award, Cup, announced TV, reviewed injury taxonomy | Historical source tables and versioned classification decisions | Inherited; source audits exist, no fresh human adjudication in this command |

All required historical ZIP SHA-256 values are pinned in `scripts/data_rebuild/final_source_sha256.json`. `restore_historical_layout.py` enumerates exact October intermediate members and rejects ambiguity. Inspect the private `logs/stages.jsonl`, `00b_original_boxscore/boxscore_json_sha256_manifest.csv` and `final/final_dataset_manifest.json` to distinguish completed source stages from inherited inputs. Passing the three final CSV hashes does not establish the unresolved raw-PDF-to-October-selector or new human-classification handoffs.

### Optional: all 33 October model tables

To run the ten original archived October scripts against the newly built corrected October panel, supply a clean historical analysis-code checkout at immutable commit **0bd713d97e8d519df5700ef473da34aba4495223** and a separate October Python environment matching requirements-october-lock.txt:

~~~bash
  --october-shared-repo "$HOME/src/nba-ppp-star-availability" \
  --october-python "$HOME/venvs/nba-october-original/bin/python"
~~~

This invokes october_corrected_chronology.py, rechecks the original archived 33 tables, then checks for the expected 704 corrected coefficient comparison rows. Without this option, the standard four corrected Stage-6 model fits still run.

## Existing scientific scripts actually connected

1. **rebuild_august_core_from_source_archives.py:** validate original ZIP hashes; optionally inject source-PDF-derived player-report rows after exact 33-field and 73,438-row verification; execute original finalizer, correct two Toronto physical-game dates, rebuild covariates, report assignments and absence histories, rerun original finalizer.
2. **build_august_analysis_ready_sensitivity.py:** produce corrected full and at-risk August files using the original locked reviewed medical-reason taxonomy. Unknown active reason labels fail rather than being guessed.
3. **rebuild_from_archives.py:** restore original selected report and source-intermediate ZIPs; reparse original 2025 harmonized sources, build original frozen October cadence and re-execute original four Stage-6 models.
4. **fixture_date_chronology_sensitivity.py:** separately correct Toronto chronology and original report links; rebuild October cadence panel and fit all four corrected Stage-6 models.
5. **reproduce_final_datasets.py:** independently hash/decode and count all final CSVs, verify unique player-game keys, sample sizes and focal model coefficients, copy accepted files and emit manifest.

All private data remain outside Git. The original star/award/Cup/taxonomy and announced TV judgments are inherited from pinned upstream records and are not automatically adjudicated anew.

## Verification boundary

The recommended `--verify-original-pdfs` path also substitutes the PDF-derived original reviewed full base into the private October replay after both it and the restored archived base match decoded SHA-256 `5154317fc52157716cf22f7c5a535259e9f073b3391fd52d78a01faaf8d96d77`. The October season report selector still uses archived intermediates. All 22 required ZIPs are SHA-256 pinned in `scripts/data_rebuild/final_source_sha256.json`; `--check-only` verifies their complete bytes. The original per-game NBA box-score JSON is supplied only with the optional four `--boxscore-*` inputs; this feeds the August finalizer but not the October selector. Historical reviewed injury, award, Cup and TV decisions remain inherited inputs.

An authentic private Linux amd64 run **completed** the new PDF-to-October handoff and every final dataset/model acceptance gate. The private manifest and stage evidence were retained and independently checked. See [the 2026-11-13 authentic run record](AUTHENTIC_FINAL_DATASET_RUN_2026-11-13.md) for exact hashes, model values, environment, native macOS floating-point failure, and remaining provenance boundaries. The original frozen ZIPs were never edited. The Stage-6 package hash typo (`...f2bbb...` versus actual `...f2ebb...`) and missing `pdfplumber` lock entry were discovered and fixed during the authentic runs.

The new entry point has **synthetic unit tests** in tests/test_reproduce_final_datasets.py and GitHub Actions. These test orchestration, duplicate-key rejection, checksums, models and private output safety. **CI cannot access private original ZIPs**. Do not claim this umbrella command completed a private original-source acceptance solely because CI passed; that requires running the command against authentic ZIPs and preserving its generated manifest.

The separate outstanding 203-description **human injury-label review** and historical source provenance exceptions are tracked in [Issue #5](https://github.com/ahmetcopur/nba-load-management-ppp/issues/5). These are scientific review questions; their resolution must not bypass or alter the data integrity gates.

[PR #4](https://github.com/ahmetcopur/nba-load-management-ppp/pull/4) contains the public scripts; it remains a draft until final private end-to-end execution and review.
