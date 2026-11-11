#!/usr/bin/env python3
"""Audit the *current* evidence chain without rewriting historical records.

A prior evidence file can truthfully say the 2020 reason mismatch was
unresolved *at that stage*. Later source-repair evidence establishes that
the discrepancy was resolved for reconstructed source data. Preserve both
as chronological observations rather than silently rewriting older reports.

This checker enforces cross-stage row counts, immutable decoded content
digests, real execution status, review boundaries, and outstanding acceptance
gates. It never downloads any private report/PDF ZIP; those private executions
are documented in sanitized empirical evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REL = Path("validation/level_c_injury_pdf_real_2026-11-10")
EVIDENCE = {
    "source_2020": "2020_original_pdf_reason_wrap_repaired_six_season_identity_exact.json",
    "fresh_2020": "fresh_2020_617_original_PDFs_source_full_acceptance_2026-11-11.json",
    "six_core_star_cup": "six_original_pdf_seasons_to_25_exact_core_star_cup_outputs.json",
    "five_reviewed": "five_raw_seasons_to_exact_reviewed_analysis_ready.json",
    "august_model": "five_raw_seasons_to_original_teamseason_fe_models.json",
    "six_reviewed": "six_original_pdf_seasons_to_exact_reviewed_analysis_ready_2026-11-11.json",
    "six_august_model": "six_original_pdf_seasons_to_original_august_FE_models_2026-11-11.json",
    "official_cup": "official_NBA_cup_2023_2025_group_and_calendar_source_audit.json",
    "october_source": "source_generated_october_cadence_panel_and_four_models.json",
}
ORIGINAL_2020_PDFS = 617
OTHER_SEASON_PDFS = 3020
ALL_PDFS = ORIGINAL_2020_PDFS + OTHER_SEASON_PDFS
SIX_SELECTED = 73547
PLAYER_ROWS = 73438
PLAYER_GAMES = 248730
AT_RISK = 180829
ORIGINAL_CORE_DECODED_SHA = (
    "253bf017095a8be45f4c7bb4a0abcc9b942a8db6311f91131c9fd12c7ab46de3"
)
ORIGINAL_REVIEWED_MODEL_SHA = (
    "d6e82ba61d99fb27ec4877b1c0b05fed76c5cb8fa4bf5b6322742b7049ae9635"
)
OCTOBER_DECODED_SHA = (
    "3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac"
)


def require(condition: bool, explanation: str) -> None:
    if not condition:
        raise ValueError("Level-C source evidence inconsistency: " + explanation)


def read_evidence(root: Path) -> dict:
    reports = {}
    for name, filename in EVIDENCE.items():
        path = root / REL / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required historical evidence not found: {path}")
        reports[name] = json.loads(path.read_text(encoding="utf-8"))
        require(isinstance(reports[name], dict), f"{filename} not a JSON object")
    return reports


def audit(reports: dict) -> dict:
    """Check positive proof and negative boundaries, never infer absent stages."""
    require(set(reports) == set(EVIDENCE), "expected five distinct stage reports")
    source = reports["source_2020"]
    a = source["source_2020"]
    six_source = source["six_season_source"]
    require(a["original_pdfs_reparsed_in_previous_real_full_source_diagnostic"] == ORIGINAL_2020_PDFS,
            "2020 source real original 617-PDF parse missing")
    require(a["raw_source_rows"] == 41780, "2020 raw report-row cardinality")
    require(a["original_source_fields_checked"] == 15, "2020 original 15-field comparison")
    require(a["all_41780_reparsed_original_rows_match_every_archived_source_field"] is True,
            "2020 original source rows not fully exact")
    require(a["prior_reason_mismatch_rows"] == 93, "2020 original mismatch baseline changed")
    require(a["remaining_source_reason_mismatch_rows"] == 0,
            "2020 reason drift not fully resolved in new source repair")
    require(a["printed_reason_continuation_fragments_moved_back"] == 44,
            "2020 reason-wrap printed fragment count")
    require(a["earlier_rows_with_recovered_reason_tails"] == 49,
            "2020 repaired preceding injury reasons")
    require(a["borrowed_frozen_reason_values_for_repair"] is False,
            "2020 archived injury reasons may not be borrowed for source repair")
    require(a["selected_report_rows"] == 8591 and
            a["all_8591_selected_source_rows_match_every_archived_22_fields"] is True,
            "2020 full 22-column selected-source acceptance")
    require(six_source["selected_report_rows"] == SIX_SELECTED and
            six_source["all_73547_original_selected_rows_equal_as_22_field_complete_row_multisets"] is True,
            "six selected-source seasons complete equality")
    require(six_source["original_resolved_player_rows"] == PLAYER_ROWS and
            six_source["all_33_identity_fields_exact"] is True and
            six_source["unresolved_before_dedup"] == 0,
            "six-season historical player identity matching")
    require(source["caveats"]["fresh_new_617_PDF_standalone_invocation_completed_today"] is False,
            "fresh separate raw 2020 full 617-PDF command cannot be claimed as accepted")
    require(source["caveats"]["new_GitHub_master_CLI_direct_private_input_acceptance"] is False,
            "all-six original source master CLI direct acceptance not yet established")

    fresh = reports["fresh_2020"]
    reread = fresh["actual_new_private_execution"]
    require(fresh["status"] == "PASS_ACTUAL_FRESH_617_ORIGINAL_NBA_PDF_REPARSE",
            "new 617 original PDF real-input rerun not accepted")
    require(fresh["original_raw_PDF_archive"]["sha256"] ==
            a["original_raw_zip_sha256"] and
            fresh["original_reference_archive"]["sha256"] ==
            a["original_corrected_reference_zip_sha256"] and
            fresh["historical_original_parser_sha256"] ==
            a["immutable_original_parser_sha256"],
            "fresh original 2020 PDF/archive/parser hashes differ from original previous evidence")
    require(reread["fresh_original_PDFs_extracted_and_parsed"] == ORIGINAL_2020_PDFS and
            reread["complete_fresh_raw_source_rows"] == a["raw_source_rows"] and
            reread["all_source_columns_compared"] == a["original_source_fields_checked"],
            "fresh original 617-PDF, 41,780-source row or 15-column execution incomplete")
    require(reread["all_41780_full_records_identical_to_archived_corrected_source"] is True and
            reread["complete_source_record_missing_rows"] == 0 and
            reread["complete_source_record_extra_rows"] == 0,
            "fresh 2020 617-PDF full source output differs")
    require(reread["printed_reason_overflow_fragments_transferred_back"] ==
            a["printed_reason_continuation_fragments_moved_back"] and
            reread["preceding_injury_reason_records_completed"] ==
            a["earlier_rows_with_recovered_reason_tails"] and
            reread["remaining_reason_field_differences_after_source_correction"] == 0 and
            reread["published_or_frozen_reason_values_read_during_reconstruction"] is False,
            "fresh original 2020 printed reason repairs differ or used frozen reason values")
    require(reread["reparsed_source_private_CSV_SHA256"] ==
            "d8f27697d0fc03d6f199855f71b8706409a5e6058cd19414ddc11d450410b028",
            "fresh 2020 private source CSV digest differs from actual real-PDF execution")
    require(fresh["distinctions"]["separately_packaged_new_GitHub_2020_replay_CLI_direct_execution_not_proven_by_this_run"] is True,
            "separate Github standalone 2020 tool falsely claimed to be executed")

    six = reports["six_core_star_cup"]
    require(six["original_PDF_reports_reparsed_in_source"] == ALL_PDFS and
            six["raw_PDF_seasons"] == 6, "six authentic source seasons and 3,637 PDFs")
    require(six["six_season_selected_report_rows_exact_full_field"] == SIX_SELECTED and
            six["resolved_player_report_rows_exact"] == PLAYER_ROWS,
            "final core source inputs do not match six-season upstream evidence")
    require(six["source_2020_reason_field_differences_after_repair"] == 0,
            "downstream 2020 repair differs from accepted 2020 source repair")
    require(six["core_output_files_full_decoded_byte_exact"] == 10 and
            six["star_output_files_full_decoded_byte_exact"] == 12 and
            six["cup_output_files_full_decoded_byte_exact"] == 3 and
            six["all_25_frozen_output_files_exact"] is True,
            "10/12/3 exact frozen original core/star/Cup accepted files")
    require(six["original_core_finalizer_completed_exit_code"] == 0 and
            six["original_star_builder_completed_exit_code"] == 0 and
            all(value == 0 for value in six["cup_original_lookup_enrichment_subprocess_exit_codes"].values()),
            "historical private original finalizer/star/Cup process did not exit successfully")
    require(six["headline_counts"]["full_player_game_rows"] == PLAYER_GAMES and
            six["headline_counts"]["at_risk_rows"] == AT_RISK,
            "original full/at-risk player-game row counts")
    require(six["full_original_decoded_output_digests"]["core"] == ORIGINAL_CORE_DECODED_SHA,
            "historical six-season core decoded SHA changed")
    require(six["limitations"]["newly_committed_all_six_season_master_umbrella_direct_private_run_completed"] is False,
            "six-season master umbrella direct original-PDF acceptance not established")
    require(six["limitations"]["historical_human_reviewed_player_crosswalk_star_awards_taxonomy_inherited"] is True,
            "reviewed crosswalk/awards/taxonomy source provenance not independently validated")

    reviewed = reports["five_reviewed"]
    require(reviewed["fresh_source_PDFs_reparsed"] == OTHER_SEASON_PDFS and
            reviewed["archived_2020_21_selected_source_rows_inherited"] == 8591,
            "reviewed analysis-ready execution used FIVE PDF-derived seasons, not six")
    output = {x["filename"]: x for x in reviewed["generated_outputs"]}
    require(len(output) == 2 and reviewed["all_2_analysis_ready_decoded_CSVs_exact"] is True,
            "two fully decoded original reviewed modeling input outputs")
    require(output["player_game_panel_analysis_ready.csv.gz"]["rows"] == PLAYER_GAMES and
            output["player_game_panel_model_at_risk_analysis_ready.csv.gz"]["rows"] == AT_RISK and
            all(x["exact_full_csv_match"] is True for x in output.values()),
            "two original reviewed full/at-risk output cardinalities/equalities")
    require(output["player_game_panel_model_at_risk_analysis_ready.csv.gz"]["decoded_sha256"] == ORIGINAL_REVIEWED_MODEL_SHA,
            "original reviewed risk model decoded digest changed")
    require(reviewed["boundary"]["reason_to_class_dictionary_preexisting_reviewed_human_labels"] is True,
            "2,182 human-reviewed injury taxonomy labels remain source inputs")

    august = reports["august_model"]
    require(august["original_selected_PDFs_reparsed"] == OTHER_SEASON_PDFS and
            august["archived_2020_21_selected_rows"] == 8591,
            "original August FE model was executed on FIVE raw-PDF seasons")
    require(august["all_focal_and_44_coefficient_rows_reproduced"] is True and
            august["model_output_comparisons"]["teamseason_fe_coefficients.csv"]["rows"] == 44,
            "August original model full coefficient table evidence")
    require(august["new_analysis_ready_model_input_decoded_sha256"] == ORIGINAL_REVIEWED_MODEL_SHA,
            "August model does not match source-derived reviewed at-risk input")

    six_reviewed = reports["six_reviewed"]
    six_reviewed_lineage = six_reviewed["input_lineage"] if "input_lineage" in six_reviewed else six_reviewed["data_lineage"]
    six_full = six_reviewed["actual_private_execution"]
    require(six_reviewed["result"] == "PASS_ALL_SIX_SOURCE_SEASONS_REVIEWED_ANALYSIS_READY",
            "new six-season original NBA PDF derived reviewed analysis-ready stage has not passed")
    require(six_reviewed_lineage["original_pdf_reports_reparsed"] == ALL_PDFS and
            six_reviewed_lineage["original_2020_21_pdfs_newly_reparsed"] == ORIGINAL_2020_PDFS and
            six_reviewed_lineage["original_2021_22_through_2025_26_pdfs_reparsed"] == OTHER_SEASON_PDFS and
            six_reviewed_lineage["six_season_selected_report_rows"] == SIX_SELECTED and
            six_reviewed_lineage["original_resolved_report_player_rows"] == PLAYER_ROWS and
            six_reviewed_lineage["original_core_player_game_rows"] == PLAYER_GAMES,
            "six-season fresh original-NBA-source-to-reviewed data lineage contradicts earlier source evidence")
    require(six_reviewed_lineage["original_decoded_core_sha256"] == ORIGINAL_CORE_DECODED_SHA,
            "new six-season reviewed input did not originate from the original exact core")
    require(six_reviewed["reviewed_archive_source"]["historical_sha256"] == reviewed["historical_reviewed_source_sha256"] and
            six_reviewed["reviewed_archive_source"]["number_of_unique_reviewed_official_reason_labels"] == 2182 and
            six_reviewed["reviewed_archive_source"]["label_contents_independently_medically_adjudicated"] is False,
            "original human-reviewed 2,182-label taxonomy source provenance misrepresented")
    require(six_full["status"] == "success" and
            six_full["full_analysis_ready_rows"] == PLAYER_GAMES and
            six_full["at_risk_model_rows"] == AT_RISK,
            "new six-season reviewed analysis-ready full/at-risk regeneration incomplete")
    six_outputs = {x["name"]: x for x in six_full["generated_outputs"]}
    require(len(six_outputs) == 2 and
            all(x["full_decoded_contents_exact"] is True for x in six_outputs.values()),
            "both six-season reconstructed reviewed tables must match all decoded bytes")
    for filename in ("player_game_panel_analysis_ready.csv.gz",
                     "player_game_panel_model_at_risk_analysis_ready.csv.gz"):
        require(six_outputs[filename]["decoded_sha256"] == output[filename]["decoded_sha256"] and
                six_outputs[filename]["decoded_bytes"] == output[filename]["decoded_bytes"] and
                six_outputs[filename]["rows"] == output[filename]["rows"],
                f"six-season source-derived reviewed {filename} differs from accepted original")
    require(six_reviewed["scientific_limits"]["separate_new_six_season_GitHub_master_umbrella_CLI_accepted_from_clean_checkout"] is False,
            "public six-season master command falsely claimed accepted directly from private source ZIPs")

    six_august = reports["six_august_model"]
    six_august_lineage = six_august["input_lineage"]
    require(six_august["result"] == "PASS_ORIGINAL_AUGUST_FE_ON_FRESH_SIX_NBA_PDF_SEASONS" and
            six_august_lineage["original_NBA_injury_PDFs_reparsed"] == ALL_PDFS and
            six_august_lineage["original_2020_source_PDFs_freshly_reparsed"] == ORIGINAL_2020_PDFS and
            six_august_lineage["reviewed_analysis_ready_at_risk_rows"] == AT_RISK and
            six_august_lineage["reviewed_at_risk_full_decoded_sha256"] == ORIGINAL_REVIEWED_MODEL_SHA,
            "new August regression not actually fitted on the six original-source-season model input")
    require(six_august["original_historical_model"]["original_model_zip_sha256"] ==
            august["original_model_package_sha256"] and
            six_august["original_historical_model"]["original_code_sha256"] ==
            august["original_model_executed_source_sha256"] and
            six_august["original_historical_model"]["source_changes_except_original_hardcoded_input_output_paths"] is False and
            six_august["original_historical_model"]["historical_model_script_exited_successfully"] is True,
            "original August statistical model source/code not executed as originally frozen")
    new_models = six_august["original_complete_result_comparisons"]
    require(new_models["teamseason_fe_focal.csv"]["original_and_recomputed_outcome_rows"] == 2 and
            new_models["teamseason_fe_coefficients.csv"]["original_and_recomputed_coefficient_rows"] == 44 and
            all(x["max_absolute_numeric_difference"] < 1e-10 for x in new_models.values()),
            "complete original August two focal / 44 model result rows do not match")
    require(len(six_august["original_focal_estimates"]) == 2 and
            six_august["research_limitations"]["original_October_10_script_suite_executed_directly_on_six_season_rebuilt_private_panel"] is False,
            "six-season October direct full-suite execution has not yet been accepted")

    october = reports["october_source"]
    panel = october["full_harmonized_panel_exact"]
    require(october["original_2025_harmonized_pdf_reparse"]["actual_selected_original_pdfs"] == 355,
            "October 2025 harmonized original PDF source count")
    require(october["generated_full_harmonized_player_game_rows"] == 248778 and
            panel["all_original_and_rebuilt_decoded_CSV_bytes_equal"] is True and
            panel["sha256"] == OCTOBER_DECODED_SHA and
            panel["decoded_bytes"] == 122661378,
            "October original source-generated model panel entire decoded equality")
    require(october["original_model_comparison"]["all_four_models_match"] is True and
            len(october["original_stage6_four_models"]) == 4,
            "original four October models")
    require(october["limitations"]["original_harmonized_report_choice_metadata_inherited"] is True and
            october["limitations"]["new_GitHub_script_not_independently_rerun_from_clean_checkout_with_all_private_zips"] is True,
            "October original choices and separately run full private CLI are open")
    official_cup = reports["official_cup"]
    require(official_cup["status"] ==
            "PASS_INDEPENDENT_ORIGINAL_NBA_CUP_PRIMARY_SOURCE_GROUP_AND_CALENDAR_VALIDATION",
            "original NBA Cup primary-source 2023–25 audit not accepted")
    require(official_cup["original_source_archive_sha256"] ==
            "65c4756b86dfb5757bb84b6be13eafb952375aaa6ce49fc1ddddc6224a4faf70" and
            official_cup["archived_original_game_rows"] == 7230 and
            official_cup["original_regular_season_Cup_games_checked"] == 198,
            "original Cup audit did not open the immutable 7,230-game source")
    require(official_cup["group_round_robin_opponent_pairings_checked_against_official_NBA_groups"] == 180 and
            official_cup["knockout_quarterfinal_and_semifinal_games_on_official_dates_checked"] == 18 and
            official_cup["distinct_official_NBA_5_team_groups_checked"] == 18,
            "not all 180 original NBA Cup group fixtures and 18 knockout stage dates checked")
    all_original_seasons = official_cup["result_by_season"]
    require({x["season"] for x in all_original_seasons} ==
            {"2023-24", "2024-25", "2025-26"} and len(all_original_seasons) == 3,
            "independent official NBA Cup archive release seasons are missing")
    for season in all_original_seasons:
        dates = season["actual_group_game_counts_on_official_dates"]
        require(season["all_60_distinct_unordered_official_group_fixture_pairs_present_once"] is True and
                season["each_team_two_home_two_away_group_games"] is True and
                sum(dates.values()) == 60 and len(dates) == 7 and
                sum(season["quarterfinal_games_on_official_dates"].values()) == 4 and
                sum(season["semifinal_games_on_official_dates"].values()) == 2 and
                season["original_official_NBA_sources"]["original_five_team_groups"].startswith("https://www.nba.com/"),
                "not all original official group fixtures and Cup-night dates cross-checked")
    require(official_cup["research_scope_boundaries"]["all_individual_original_matchups_matched_against_the_exact_official_per_day_home_away_schedule"] is False and
            official_cup["research_scope_boundaries"]["official_TV_broadcast_provider_schedule_independently_verified"] is False,
            "Cup source verification may not claim individual fixture dates or TV providers")
    require(six["limitations"]["original_Cup_and_TV_source_releases_independently_verified"] is False,
            "older six-season original-model source report must remain chronologically unchanged")

    # The October evidence is a snapshot FROM BEFORE the 2020 repaired
    # source replay. Do not reinterpret its historical 93 as current!
    require(october["limitations"]["raw_2020_21_reason_differences_unresolved"] == 93,
            "older October audit's chronological 2020 reason status was modified")

    accepted = {
        "original_2020_reason_only_drift_resolved_at_source_row_level": True,
        "fresh_direct_617_original_PDFs_reparsed_and_exact_full_source": True,
        "six_seasons_full_22_field_selected_reports_exact": True,
        "six_seasons_original_player_IDs_exact": True,
        "six_seasons_original_core_star_Cup_full_output_files_exact": 25,
        "five_seasons_reviewed_analysis_ready_full_outputs_exact": 2,
        "five_seasons_original_August_FE_coefficient_rows_reproduced": 44,
        "six_seasons_reviewed_analysis_ready_full_outputs_exact": 2,
        "six_seasons_original_August_FE_coefficient_rows_reproduced": 44,
        "independently_verified_NBA_Cup_original_group_opponent_pairings": 180,
        "independently_verified_NBA_Cup_knockout_stage_date_rows": 18,
        "five_seasons_source_built_October_cadence_panel_exact_decoded_bytes": 122661378,
        "four_original_October_Stage6_models_exact": True,
    }
    outstanding = {
        "separately_packaged_new_GitHub_2020_CLI_direct_private_execution": True,
        "direct_clean_checkout_original_PDF_six_season_master_CLI_acceptance": True,
        "six_season_new_reviewed_analysis_ready_or_August_FE_model_rerun": False,
        "six_season_private_source_generated_October_model_suite_rerun": True,
        "direct_private_original_October_ten_script_handoff": True,
        "independent_original_PDF_inventory_completeness_against_NBA_archive": True,
        "independent_human_crosswalk_and_2182_taxonomy_label_review": True,
        "independent_star_awards_TV_and_game_covariate_provenance": True,
        "independent_NBA_Cup_exact_per_fixture_dates_and_TV_provider_provenance": True,
        "full_published_manuscript_claims_reconciliation": True,
        "independent_scientific_review_before_merge": True,
    }
    return {
        "status": "ACCEPTED_COMPONENTS_WITH_OPEN_RESEARCH_GATES",
        "source_evidence_files_checked": len(reports),
        "verified": accepted,
        "still_open": outstanding,
        "all_research_gates_closed": False,
        "private_original_PDFs_uploaded_to_public_CI": False,
        "PR_4_ready_to_merge": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repository", type=Path, default=REPO,
                   help="Local checked-out repository containing sanitized evidence")
    p.add_argument("--report", type=Path,
                   help="Optional NEW path to write an aggregate acceptance report")
    args = p.parse_args()
    result = audit(read_evidence(args.repository))
    data = json.dumps(result, indent=2) + "\n"
    if args.report is not None:
        if args.report.exists():
            raise FileExistsError("Refusing to overwrite previous Level-C status report")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(data, encoding="utf-8")
    print(data)


if __name__ == "__main__":
    main()
