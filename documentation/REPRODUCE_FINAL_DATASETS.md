# Reproduce the final corrected NBA analysis datasets

This is the canonical entry point for the February 2022 Toronto corrected chronology:

**[scripts/data_rebuild/reproduce_final_datasets.py](../scripts/data_rebuild/reproduce_final_datasets.py)**

It runs the pre-existing original August and October source reconstruction scripts, checks the frozen historical baseline, applies Toronto corrections to private copies, independently checks complete decoded CSV SHA-256 fingerprints, verifies player-game keys, counts and Stage-6 estimates, and creates a single private acceptance manifest.

**The code is public; the original injury reports, box-score files and generated individual-level player data are NOT.** Bring the original research ZIP archives separately. Do not use a downloaded final dataset as a substitute for the source archives.

## The generated final files

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

**Precise scope:** the extra original-PDF stage rebuilds the six-season frozen player core, verifies it independently, and then **feeds the directly PDF-derived, identity-resolved 73,438 selected player-report rows into the August baseline and Toronto-corrected finalizer**, after enforcing exact equality across all 33 historical source fields. The source-derived August core is used to generate the corrected latest-pre-tip analysis-ready outputs. Other historical inputs (covariates, team-game reports, roster, manual awards/Cup/TV mappings) still come from pinned original ZIPs. The October cadence correction still uses historical selected-report intermediates; the PDF-derived original reviewed base is substituted after exact decoded-hash comparison, while season-specific report selection is not injected. This is a partial raw-to-corrected source path, not an assertion that every historical source is re-downloaded or manually adjudicated. Original official box-score JSON verification is handled separately by verify_boxscore_cache.py and associated provenance scripts.

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

The recommended `--verify-original-pdfs` path also substitutes the PDF-derived original reviewed full base into the private October replay after both it and the restored archived base match decoded SHA-256 `5154317fc52157716cf22f7c5a535259e9f073b3391fd52d78a01faaf8d96d77`. The October season report selector still uses archived intermediates. All 22 required ZIPs are SHA-256 pinned in `scripts/data_rebuild/final_source_sha256.json`; `--check-only` verifies their complete bytes. The original per-game NBA box-score JSON is not supplied to this command; the inherited roster ZIP is pinned and the raw JSON cache check remains separate. Historical reviewed injury, award, Cup and TV decisions remain inherited inputs.

An authentic private Linux amd64 run **completed** the new PDF-to-October handoff and every final dataset/model acceptance gate. The private manifest and stage evidence were retained and independently checked. See [the 2026-11-13 authentic run record](AUTHENTIC_FINAL_DATASET_RUN_2026-11-13.md) for exact hashes, model values, environment, native macOS floating-point failure, and remaining provenance boundaries. The original frozen ZIPs were never edited. The Stage-6 package hash typo (`...f2bbb...` versus actual `...f2ebb...`) and missing `pdfplumber` lock entry were discovered and fixed during the authentic runs.

The new entry point has **synthetic unit tests** in tests/test_reproduce_final_datasets.py and GitHub Actions. These test orchestration, duplicate-key rejection, checksums, models and private output safety. **CI cannot access private original ZIPs**. Do not claim this umbrella command completed a private original-source acceptance solely because CI passed; that requires running the command against authentic ZIPs and preserving its generated manifest.

The separate outstanding 203-description **human injury-label review** and historical source provenance exceptions are tracked in [Issue #5](https://github.com/ahmetcopur/nba-load-management-ppp/issues/5). These are scientific review questions; their resolution must not bypass or alter the data integrity gates.

[PR #4](https://github.com/ahmetcopur/nba-load-management-ppp/pull/4) contains the public scripts; it remains a draft until final private end-to-end execution and review.
