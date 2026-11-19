# Executable player-game core rebuild (November 10, 2026)

This moves beyond verifying precomputed artifacts: **the original six-season finalization algorithm has been executed again**, generating player-game records, the report-only roster union, onset/absence outcomes and the at-risk modeling input.

## One command

New source: [build_player_game_core_pipeline.py](../scripts/data_rebuild/build_player_game_core_pipeline.py)

The script expects these four original user-owned ZIP packages in a private archive folder outside the repository:

- nba_player_game_at_risk_core_v1.zip
- nba_player_crosswalk_final_v1.zip
- nba_boxscore_roster_frame_v2_output_upload.zip
- nba_game_covariates_v1.zip

Use the historical pandas-2 environment described in [requirements-builder-lock.txt](../requirements-builder-lock.txt).

    python3 -m venv .venv-rebuild
    source .venv-rebuild/bin/activate
    python -m pip install -r requirements-builder-lock.txt

    python scripts/data_rebuild/build_player_game_core_pipeline.py \
      --archive-dir /private/nba_source_zip_archives \
      --output-dir /private/new_nba_core_reconstruction

This **generates fresh data files**. It checks SHA-256 of the four original packages, reads source selected reports, reruns the original reviewed player-ID crosswalk/alias/roster fallback and status-priority deduplication, then runs the unchanged original historical finalizer in a safe separate workspace, adapting only its hard-coded ROOT directory. It compares each regenerated CSV with the original frozen release. The output destination must not exist; source archives and frozen releases are never overwritten. Generated private records must not be committed.

Final output directory: /private/new_nba_core_reconstruction/nba_player_game_at_risk_core_v1/

- player_game_panel_core.csv.gz — 248,730 rows, 92 fields
- player_game_panel_model_at_risk.csv.gz — 180,829 rows, 39 fields
- report_only_roster_additions.csv — 159 rows
- absence_spells_provisional.csv.gz — observed and censored spell records
- season summaries, classification counts, taxonomy review sample

The root output folder also receives an identity stage report and pipeline_rebuild_report.json.

## Executed real-input acceptance

A local run on the authentic private historical archives generated **73,438 independently resolved player-report rows** (72,819 reviewed crosswalk matches, 606 reviewed alias fallbacks, 15 unique official roster-name fallbacks, zero unresolved). The actual unchanged finalization script (SHA-256 a0271f01f551dbbe1abedfac7ca8fefb9c865cd9b58a33185a3b7cbc991f8bfc) then generated **248,730 player-game rows, 180,829 at-risk rows, 159 report-only roster additions, 12,710 onset events and 13,723 observed absence spells**.

**All eight regenerated output CSVs were exactly equal to the frozen reference CSV bytes after gzip decompression**. The gzip headers naturally have different creation timestamps; the *contents* are exact. See [public sanitized checksums and counts](../validation/level_c_injury_pdf_real_2026-11-10/connected_identity_to_core_execution.json). No private ZIP, individual PDF, or player-level output was committed.

Synthetic tests covering original-script tampering, changed output CSVs, changed source ZIPs, ZIP member ambiguity, pre-existing output destinations, unsafe output paths and gzip timestamp differences are in [test_build_player_game_core_pipeline.py](../tests/test_build_player_game_core_pipeline.py) and GitHub CI. CI tests **do not access private original ZIPs**.

## Explicit boundaries

This is a **connected archived-source-intermediate -> player identities -> final core** pipeline, not yet the full raw-PDF-to-statistical-paper workflow. The archived selected_report_rows_all.csv and team_game_report_status.csv enter as upstream original inputs; their PDF parsers and historical selectors were investigated in earlier independent audit stages but are not orchestrated within this new command.

Reviewed manual crosswalk identity decisions are inherited; reproducing them does not re-adjudicate their correctness. The analysis-ready stage also uses reviewed taxonomy, awards/star, Cup and TV source metadata that have not all been independently rebuilt. The original 2020–21 parser leaves 93 free-text reason-field mismatches across 44 saved PDFs, including 25 selected records across 12 games.

**Next build task:** derive a reproducible analysis-ready table from these newly generated core files, explicitly label inherited/manual classifications, and invoke the original statistical scripts on that generated table rather than on a copied frozen output. Continue tracking the 2020 source layout and manual-source limitations in [Issue #5](https://github.com/ahmetcopur/nba-load-management-ppp/issues/5).

The publication datasets and manuscript remain frozen; [PR #4](https://github.com/ahmetcopur/nba-load-management-ppp/pull/4) stays draft.


## Newly connected analysis-ready generation

A second real local execution **took the newly generated 248,730-row core** and independently produced the complete 248,730-row reviewed analysis-ready table and 180,829-row analysis-ready modeling subset. Both generated outputs were **byte-for-byte equal to the frozen CSV after gzip decompression**, not merely equal in row count:

| Generated CSV | Rows | Decoded CSV SHA-256 |
|---|---:|---|
| player_game_panel_analysis_ready.csv.gz | 248,730 | 5154317fc52157716cf22f7c5a535259e9f073b3391fd52d78a01faaf8d96d77 |
| player_game_panel_model_at_risk_analysis_ready.csv.gz | 180,829 | d6e82ba61d99fb27ec4877b1c0b05fed76c5cb8fa4bf5b6322742b7049ae9635 |

The analysis-ready bridge [build_analysis_ready_from_generated_core.py](../scripts/data_rebuild/build_analysis_ready_from_generated_core.py) confirms exact player-team-game row identities and semantic equivalence of **all 92 original core fields**, except four known later enrichment fields (taxonomy_version, star_PPP_it, star_status_pending and cup_game_pending). It harmonizes numerical *serialization* only after values match within 1e-8. It regenerates the reviewed official-reason categories and onset labels from the generated core using the **2,182-key archived reviewed-reason dictionary**, and reconstructs all four frozen onset-category booleans and three provisional category aliases.

**Scientific provenance:** 24 extra reviewed analysis fields and four later-enriched core fields—including star/award, Cup and other source annotations—are inherited unchanged from the SHA-256-pinned historical analysis-ready package. This preserves source lineage but does not claim those values were independently generated from primary award/Cup announcements. The frozen source review was assistant single-coded, without independent double-coding.

[Executed two-output private-input acceptance record](../validation/level_c_injury_pdf_real_2026-11-10/connected_new_core_to_analysis_ready_execution.json) identifies both exact regenerated decoded CSV hashes. The real local replay was split into two bounded jobs, then their valid gzip streams joined for the complete decoded-byte comparison.

### One command for both actual build stages

New wrapper: [rebuild_core_to_analysis_ready.py](../scripts/data_rebuild/rebuild_core_to_analysis_ready.py). With **five original private ZIP files** in one folder—the four listed above plus nba_player_game_analysis_ready_v1.zip—run:

    python scripts/data_rebuild/rebuild_core_to_analysis_ready.py \
      --archive-dir /private/nba_source_zip_archives \
      --output-root /private/new_nba_reproduction

The wrapper calls the newly executable player-ID/roster/onset core builder, then the generated-core -> reviewed-taxonomy/analysis-ready builder, **writing newly generated full and at-risk tables**, verifying original source/code SHA-256 and every rebuilt CSV, then creating a single connected_rebuild_manifest.json. Use a new private output folder each run; never commit original ZIPs or generated private player-game rows.

This is now a **working historical selected-report-intermediate → model-analysis-ready reproduction entrypoint**. Upstream per-season original-PDF parsing and historically saved report selection have been separately audited, but are **not yet orchestrated from raw PDFs by this wrapper**. Primary-source star/Cup and reviewed injury labels remain inherited, and released regressions have not yet been invoked against these *newly generated* analysis-ready tables.

The next build step is to connect the released August model runner to the newly written analysis-ready modeling CSV and compare coefficients, tables and model rows with the frozen release. The separate October cadence panel requires its own source-construction branch and must not be conflated with the August risk panel.
