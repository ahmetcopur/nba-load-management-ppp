#!/usr/bin/env python3
"""One command: independently rebuild NBA player IDs -> core -> PPP star panel.

Starts at archived selected-report CSV rows. Original source-pinned helper,
finalizer, and All-Star/All-NBA code are used; no private original ZIP is
modified. All ten core and twelve star frozen outputs are compared exactly
(gzip comparison is on decoded CSV bytes). This does not yet rebuild original
raw PDF parsing, NBA Cup or manuscript model regressions.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.data_rebuild.run_connected_player_game_core import execute
from scripts.data_rebuild.run_connected_star_enrichment import (
    immutable_original_star_source, run_star, STAR_ZIP,
)
from scripts.data_rebuild.run_connected_cup_enrichment import (
    CUP_ARCHIVE, CUP_ARCHIVE_SHA256, run_cup,
)
from scripts.data_rebuild.run_connected_player_game_core import sha256_file
from scripts.data_rebuild.rebuild_2025_selected_from_pdfs import (
    run as rebuild_selected_2025_from_pdfs,
    OUTPUT_NAME as PDF_SELECTED_2025_OUTPUT,
)
from scripts.data_rebuild.rebuild_2021_2024_selected_from_pdfs import (
    rebuild as rebuild_selected_2021_2024_from_pdfs,
    accepted_source_filename,
    SEASONS as ORIGINAL_2021_2024_SEASONS,
)
from scripts.data_rebuild.rebuild_2020_selected_from_pdfs import (
    rebuild as rebuild_selected_2020_from_pdfs,
    SELECTED_FILE as PDF_SELECTED_2020_OUTPUT,
)
from scripts.data_rebuild.build_analysis_ready_from_generated_core import (
    build as build_analysis_ready_from_generated_core,
    REVIEWED_ZIP_SHA256,
)
from scripts.data_rebuild.run_original_teamseason_models_from_generated_panel import (
    run as run_original_teamseason_models,
)
from scripts.data_rebuild.rebuild_october_cadence_from_generated_core import (
    run as rebuild_october_cadence,
)
from scripts.data_rebuild.run_full_october_suite_from_generated_panel import (
    run as run_ten_october_from_generated_panel,
    verify_october_runtime,
)
from scripts.data_rebuild.october_corrected_chronology import verify_shared_commit


def reproduce(archive_dir: Path, output_dir: Path, *,
              timeout_seconds: int = 900, include_cup: bool = False,
              from_original_2025_pdfs: bool = False,
              from_original_2021_2025_pdfs: bool = False,
              from_original_2020_2025_pdfs: bool = False,
              previous_2020_reparse_csv: Path | None = None,
              pdf_workers: int = 4,
              include_analysis_ready: bool = False,
              include_original_teamseason_models: bool = False,
              include_october_cadence: bool = False,
              include_full_october_suite: bool = False,
              october_shared_repo: Path | None = None,
              october_python: Path | None = None) -> dict:
    archive_dir, output_dir = archive_dir.resolve(), output_dir.resolve()
    # Validate that this original star package is available BEFORE creating
    # any private reconstructed core output. The stage runner rechecks it.
    immutable_original_star_source(archive_dir / STAR_ZIP)
    if include_cup:
        path = archive_dir / CUP_ARCHIVE
        if sha256_file(path) != CUP_ARCHIVE_SHA256:
            raise ValueError("Original NBA Cup lookup package SHA-256 changed")
    if include_original_teamseason_models and not include_analysis_ready:
        raise ValueError("Original team-season model replay requires --with-analysis-ready")
    if include_october_cadence and not include_analysis_ready:
        raise ValueError("October cadence reconstruction requires --with-analysis-ready")
    if include_full_october_suite:
        if not include_october_cadence:
            raise ValueError("Original ten-script October suite requires --with-october-cadence")
        if not october_shared_repo or not october_python:
            raise ValueError("Original ten-script October suite requires both an original clean --october-shared-repo and --october-python")
        # Cheap provenance/runtime preflight before creating any private output.
        verify_shared_commit(Path(october_shared_repo).resolve())
        verify_october_runtime(Path(october_python).resolve())
    if include_analysis_ready:
        reviewed_path = archive_dir / "nba_player_game_analysis_ready_v1.zip"
        if sha256_file(reviewed_path) != REVIEWED_ZIP_SHA256:
            raise ValueError("Historical reviewed official-reason source ZIP SHA-256 changed")
    raw_scopes = [
        from_original_2025_pdfs,
        from_original_2021_2025_pdfs,
        from_original_2020_2025_pdfs,
    ]
    if sum(bool(x) for x in raw_scopes) > 1:
        raise ValueError("Choose one original PDF scope: 2025 only, 2021–25 or all 2020–25 seasons")
    if previous_2020_reparse_csv is not None and not from_original_2020_2025_pdfs:
        raise ValueError("An earlier 2020 PDF source CSV requires --from-original-2020-2025-pdfs")
    # All original PDF player-level source records are generated exclusively in
    # a disposable, private temporary folder, outside Git, and are injected
    # only after complete 22-field full-record frozen comparison.
    with TemporaryDirectory(prefix="nba_private_pdf_selected_rebuild_") as temporary:
        pdf_result = None
        early_pdf_result = None
        replacements = {}
        original_2020_result = None
        if from_original_2020_2025_pdfs:
            old_dir = Path(temporary) / "selected_2020"
            original_2020_result = rebuild_selected_2020_from_pdfs(
                archive_dir, old_dir, workers=pdf_workers,
                previous_reparse_csv=previous_2020_reparse_csv,
            )
            replacements["2020-21"] = old_dir / PDF_SELECTED_2020_OUTPUT
        if from_original_2021_2025_pdfs or from_original_2020_2025_pdfs:
            early_dir = Path(temporary) / "selected_2021_2024"
            early_pdf_result = rebuild_selected_2021_2024_from_pdfs(
                archive_dir, early_dir, workers=pdf_workers,
            )
            for season in ORIGINAL_2021_2024_SEASONS:
                replacements[season] = early_dir / accepted_source_filename(season)
        if any(raw_scopes):
            late_dir = Path(temporary) / "selected_2025"
            pdf_result = rebuild_selected_2025_from_pdfs(
                archive_dir, late_dir, workers=pdf_workers,
            )
            replacements["2025-26"] = late_dir / PDF_SELECTED_2025_OUTPUT
        core = execute(
            archive_dir, output_dir, timeout_seconds=timeout_seconds,
            reparsed_season_csvs=replacements or None,
        )
        star = run_star(archive_dir, output_dir, timeout_seconds=timeout_seconds)
        cup = run_cup(archive_dir, output_dir, timeout_seconds=timeout_seconds) if include_cup else None
        reviewed = build_analysis_ready_from_generated_core(
            output_dir / "nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz",
            archive_dir / "nba_player_game_analysis_ready_v1.zip",
            output_dir / "analysis_ready_from_generated_core",
        ) if include_analysis_ready else None
        models = run_original_teamseason_models(
            output_dir / "analysis_ready_from_generated_core/player_game_panel_model_at_risk_analysis_ready.csv.gz",
            output_dir / "original_teamseason_models_from_source",
        ) if include_original_teamseason_models else None
        october = rebuild_october_cadence(
            archive_dir,
            output_dir / "analysis_ready_from_generated_core/player_game_panel_analysis_ready.csv.gz",
            output_dir / "original_october_cadence_from_generated_core",
            workers=pdf_workers,
            timeout_seconds=timeout_seconds,
        ) if include_october_cadence else None
        october_ten = run_ten_october_from_generated_panel(
            Path(october_shared_repo),
            output_dir / "original_october_cadence_from_generated_core/cadence_harmonized_results/player_team_game_harmonized_cadence.csv.gz",
            output_dir / "original_october_full_ten_scripts_from_generated_panel",
            october_python=Path(october_python),
        ) if include_full_october_suite else None
    result = {
        "status": "pass",
        "scope": "Original archived selected-report inputs -> independently rebuilt player IDs -> original finalizer -> source-pinned award/star enrichment.",
        "core_identity_rows": core["identity"]["frozen_comparison"]["rows"],
        "core_final_player_game_rows": core["original_finalizer_summary"]["final_player_game_rows"],
        "core_at_risk_rows": core["original_finalizer_summary"]["at_risk_rows"],
        "core_exact_output_files": len(core["compared_original_outputs"]),
        "star_exact_output_files": len(star["outputs"]),
        "cup_exact_primary_output_files": len(cup["exact_decoded_outputs"]) if cup else 0,
        "cup_lookup_stage_completed": bool(cup),
        "reviewed_analysis_ready_built_from_generated_core": bool(reviewed),
        "analysis_ready_complete_original_output_matches": (
            len(reviewed["outputs"]) if reviewed else 0
        ),
        "original_teamseason_model_reproduced": bool(models),
        "october_source_derived_cadence_panel_exact": (
            bool(october and october["full_decoded_harmonized_panel_exact"]["identical_decoded_bytes"])
        ),
        "original_october_cadence_four_models_reproduced": bool(
            october and october["all_four_model_specifications_reproduced"]
        ),
        "source_generated_october_all_ten_scripts_reproduced": bool(
            october_ten and october_ten["all_original_ten_october_scripts_ran"]
        ),
        "source_generated_october_archived_outputs_compared": (
            october_ten["original_33_reference_output_comparisons"] if october_ten else 0
        ),
        "new_2025_original_harmonized_PDFs_parsed": (
            october["source_2025_harmonized"]["fresh_original_pdfs_parsed"]
            if october else 0
        ),
        "original_teamseason_model_outputs_exact": (
            len(models["models"]) if models else 0
        ),
        "original_teamseason_model_focal_results": (
            models["focal"] if models else None
        ),
        "reviewed_reason_dictionary_size": (
            reviewed["reviewed_official_reason_dictionary_size"] if reviewed else None
        ),
        "fresh_2025_pdf_source_replay": pdf_result,
        "fresh_2021_2024_pdf_source_replay": early_pdf_result,
        "source_2020_pdf_reason_wrap_replay": original_2020_result,
        "2020_original_PDFs_reparsed_in_this_invocation": (
            bool(original_2020_result and
                original_2020_result["fresh_original_617_PDF_execution_in_this_invocation"])
        ),
        "all_six_original_PDF_selected_seasons_connected": len(replacements) == 6,
        "complete_original_PDF_source_seasons": sorted(replacements),
        "fresh_selected_rows_from_original_PDFs": sum({
            "2020-21": 8591, "2021-22": 12527, "2022-23": 11499,
            "2023-24": 12897, "2024-25": 14065,
            "2025-26": 13968,
        }[season] for season in replacements),
        "full_pipeline_starts_at_raw_injury_pdfs": False,
        "2020_21_selected_source_rows_inherited": "2020-21" not in replacements,
        "2021_2025_original_PDF_rows_rebuilt": bool(from_original_2021_2025_pdfs),
        "other_five_seasons_source_rows_archived": not bool(from_original_2021_2025_pdfs),
        "official_award_history_independently_verified": False,
        "nba_cup_lookup_applied_to_rebuilt_star_outputs": bool(cup),
        "original_cup_lookup_independently_verified": False,
        "model_regressions_rebuilt_from_outputs": bool(models),
        "all_manuscript_regressions_rebuilt": False,
        "original_archives_or_frozen_published_data_modified": False,
    }
    (output_dir / "connected_core_plus_star_report.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", type=Path, required=True,
                   help="Private folder containing original core, crosswalk, roster, covariates and star ZIPs")
    p.add_argument("--output-dir", type=Path, required=True,
                   help="New private output folder, outside Git and not yet existing")
    p.add_argument("--timeout-seconds", type=int, default=900,
                   help="Per-stage subprocess timeout, seconds")
    p.add_argument("--with-cup", action="store_true",
                   help="Also rebuild NBA Cup flags from the original archived game-level lookup")
    p.add_argument("--from-original-2025-pdfs", action="store_true",
                   help="Parse 729 actual original 2025–26 PDFs into 13,968 selected report rows before identity/core; requires two extra original raw ZIPs")
    p.add_argument("--from-original-2021-2025-pdfs", action="store_true",
                   help="Reparse 2,291 authentic 2021–24 PDFs plus 729 original 2025 PDFs, connecting five seasons' selected source rows (64,956) before the core")
    p.add_argument("--from-original-2020-2025-pdfs", action="store_true",
                   help="Rebuild all six original 2020–25 selected report seasons (73,547 rows), including 617 authentic 2020–21 PDFs with reason-line continuation repair")
    p.add_argument("--previous-2020-reparse-csv", type=Path,
                   help="For six-season replay only: use a prior complete, private, original-617-PDF diagnostic source CSV (verified before repair) rather than re-parsing all 617 in this invocation")
    p.add_argument("--with-analysis-ready", action="store_true",
                   help="Rebuild the reviewed reason taxonomy and both analysis-ready tables from the new original player-game core; requires historical reviewed source ZIP")
    p.add_argument("--with-original-teamseason-models", action="store_true",
                   help="After the reviewed analysis-ready bridge, rerun the original August player/team-season fixed effects and compare all 44 original coefficient rows")
    p.add_argument("--with-october-cadence", action="store_true",
                   help="Regenerate the original October cadence-harmonized panel, parse 355 original 2025 harmonized PDFs, and reproduce four Stage-6 original models")
    p.add_argument("--with-full-october-suite", action="store_true",
                   help="After new October cadence panel passes, rerun all 10 original October scripts and compare 33 archived results")
    p.add_argument("--october-shared-repo", type=Path,
                   help="Clean independent original October Git repo checkout at the pinned historical source commit")
    p.add_argument("--october-python", type=Path,
                   help="Python 3.12 interpreter with pandas 3.0.5 and requirements-october-lock.txt; kept separate from source builder's pandas 2 environment")
    p.add_argument("--pdf-workers", type=int, default=4,
                   help="Parallel original PDF parsers when either raw-source option is set")
    args = p.parse_args()
    print(json.dumps(
        reproduce(args.archive_dir, args.output_dir, timeout_seconds=args.timeout_seconds,
                  include_cup=args.with_cup,
                  from_original_2025_pdfs=args.from_original_2025_pdfs,
                  from_original_2021_2025_pdfs=args.from_original_2021_2025_pdfs,
                  from_original_2020_2025_pdfs=args.from_original_2020_2025_pdfs,
                  previous_2020_reparse_csv=args.previous_2020_reparse_csv,
                  pdf_workers=args.pdf_workers,
                  include_analysis_ready=args.with_analysis_ready,
                  include_original_teamseason_models=args.with_original_teamseason_models,
                  include_october_cadence=args.with_october_cadence,
                  include_full_october_suite=args.with_full_october_suite,
                  october_shared_repo=args.october_shared_repo,
                  october_python=args.october_python),
        indent=2
    ))


if __name__ == "__main__":
    main()
