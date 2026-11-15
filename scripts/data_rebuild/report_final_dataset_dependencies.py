#!/usr/bin/env python3
"""Public, machine-readable source-to-final dependency inventory.

This is a code-level inventory, not an empirical claim that optional private
source stages ran. It enumerates every input restored into the October builder,
the other source families used by the final runner, and the three final panels.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.data_rebuild.restore_historical_layout import FILES, SELECTOR_NAMES, SELECTOR_ZIP, SELECTOR_DEST
from scripts.data_rebuild.reproduce_final_datasets import (
    REQUIRED_ZIPS, RAW_PDF_EXTRA_ZIPS, SELECTOR_SCHEDULE_EXTRA_ZIPS,
)


def classification(path: str) -> tuple[str, str, str, str]:
    """Return source, generator, dependency class, and historical limitation."""
    if path.startswith("cadence_work/season_parsed/2020-21/"):
        return ("617 original 2020–21 injury PDFs", "rebuild_2020_selected_from_pdfs.py",
                "A/E (six-source or raw-2020 option)",
                "Fresh full rows feed October in the selected mode; original publication/acquisition clocks remain inherited.")
    if path.startswith("cadence_work/season_parsed/"):
        if any("/"+season+"/" in path for season in ("2021-22","2022-23","2023-24","2024-25")):
            return ("Original full candidate injury PDF ZIP","rebuild_2021_full_candidates.py",
                    "A (six-source option)","Full candidates and generated selectors are consumed by the canonical six-source mode; default mode still inherits intermediates.")
        return ("Original season injury PDF ZIP", "rebuild_2021_2024_selected_from_pdfs.py",
                "C", "Only previously selected PDFs are reparsed in the canonical runner; full selector candidates not connected.")
    if path.startswith("cadence_work/s4/"):
        return ("Original injury PDFs, manifests and S4 schedules", "verify_2021_2023_selector_rebuild.py",
                "A/E (six-source option)", "Source-derived team status is consumed in six-source mode; original timing metadata remains inherited.")
    if path.startswith("analysis/"):
        return ("Original injury PDFs, NBA JSONs and reviewed reasons", "build_analysis_ready_from_generated_core.py",
                "A (with PDF + JSON options)", "Human reviewed taxonomy and annotations remain versioned original inputs.")
    if path.startswith("cadence_2025/"):
        return ("NBA JSON identities and reviewed alias matches", "verify_player_identity_replay.py",
                "C/D", "Original alias/crosswalk decisions remain inherited at this October input.")
    return ("SHA-pinned original parser code", "rebuild_from_archives.py",
            "D", "Original executable parser is a versioned methodological input.")


def selector_class(name: str) -> tuple[str, str]:
    if name.startswith("2025-26"):
        return ("A/E (six-source option)", "All saved candidates feed source-derived selectors/statuses. Actual cumulative October consumption passed; two historical team fields remain a declared metadata-only artifact exception. Publication/acquisition metadata remains historical.")
    return ("A/E (six-source option)", "Complete original-PDF candidate rows and original selector outputs feed the canonical six-source mode. All 18 generated inputs were opened in the cumulative gate. Original timing metadata remains inherited; default/legacy modes retain their narrower scopes.")


def build_report() -> dict:
    nodes=[]
    for dest, archive, member in FILES:
        source, generator, status, limitation=classification(dest)
        nodes.append({
            "id":dest,"original_source":source,"generating_script":generator,
            "upstream_dependencies":[archive],"current_input":{"archive":archive,"member":member},
            "classification":status,"regenerated_value_consumed_downstream":status.startswith("A"),
            "expected_invariants":"Validated against frozen complete decoded CSV output and final panel hashes",
            "remaining_limitation":limitation,
        })
    for name in SELECTOR_NAMES:
        status, limitation=selector_class(name)
        nodes.append({
            "id":"cadence_work/selector/nba_canonical_snapshot_selector_v1/"+name,
            "original_source":"Original NBA injury PDFs, original season manifest and S4 fixture schedule",
            "generating_script":("verify_canonical_selector_replay.py" if name.startswith(("2020-21","2024-25"))
                                 else "verify_2021_2023_selector_rebuild.py" if not name.startswith("2025-26")
                                 else "verify_2025_manifest_selector.py"),
            "upstream_dependencies":[SELECTOR_ZIP,"original season parsed report rows","original schedule and manifest"],
            "current_input":{"archive":SELECTOR_ZIP,"member":name},
            "classification":status,"regenerated_value_consumed_downstream":status.startswith(("A","B")),
            "generated_input_mode":"--rebuild-six-season-october-sources",
            "expected_invariants":"1,080 games (2020) or 1,230 games; exact keys/scientific fields and final panel hash",
            "remaining_limitation":limitation,
        })
    fresh_2025_rows="cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv"
    nodes.append({"id":fresh_2025_rows,"original_source":"All 5,023 saved original 2025 injury PDFs",
                  "generating_script":"rebuild_six_season_october_sources.py",
                  "upstream_dependencies":["audit_2025_26_upload.zip","audit_2025_26_targeted_upload.zip","original season manifest and S4 schedule"],
                  "current_input":{"generated_in_six_source_mode":True},"classification":"A/E (six-source option)",
                  "regenerated_value_consumed_downstream":True,"generated_input_mode":"--rebuild-six-season-october-sources",
                  "expected_invariants":"355 selected reports derived from complete saved candidates; complete scientific panel SHA unchanged",
                  "remaining_limitation":"Original publication/acquisition observations remain inherited; unsaved reports are not invented."})
    generated_paths=sorted({p for p,_,_ in FILES if p.startswith(("cadence_work/season_parsed/","cadence_work/s4/"))}
                           |{SELECTOR_DEST+"/"+n for n in SELECTOR_NAMES}|{fresh_2025_rows})
    upstream=[
        ("game covariates, Elo, rest, travel", "original NBA fixture and venue schedules", "nba_game_covariates_v1.zip", "run_connected_player_game_core.py", "C", "Original calculation replayed independently, but connected final correction still inherits non-date source inputs."),
        ("player participation and roster", "7,230 original NBA boxscore JSON files", "nba_boxscore_roster_frame_v2_output_upload.zip", "verify_boxscore_cache.py", "A with JSON option", "Historical raw_json_path prefix is preserved after confirming same game JSON."),
        ("injury report player identity", "Original six-season injury PDFs and human-reviewed aliases", "nba_player_crosswalk_final_v1.zip", "verify_player_identity_replay.py", "A/D", "Alias choices are versioned human decisions."),
        ("awards and star timeline", "NBA awards and All-Star records", "nba_player_game_at_risk_star_v1.zip", "run_connected_star_enrichment.py", "C/D", "Historical award lookup and reviewed identity decisions remain inherited."),
        ("NBA Cup and TV advance mapping", "Original NBA publication schedules and manual match decisions", "nba_player_game_at_risk_star_cup_v1.zip", "run_connected_cup_enrichment.py", "C/D/E", "Original announcement timing/nominal neutral hosts and some match decisions remain historical inputs."),
        ("reviewed taxonomy", "Original report text and human reviewed reason classifications", "nba_player_game_analysis_ready_v1.zip", "build_analysis_ready_from_generated_core.py", "D", "Never invent replacement human classifications."),
        ("2025 candidate report selection", "5,023 original saved PDFs plus original targeted acquisition design", "audit_2025_26_upload.zip", "generate_2025_selector_inputs.py", "A/E (six-source option)", "Full saved candidate selection and the explicit source-derived metadata variant feed the cumulative builder; original clocks and exact legacy team-artifact equivalence remain unresolved."),
    ]
    for id_,source,archive,generator,status,limitation in upstream:
        nodes.append({"id":id_,"original_source":source,"generating_script":generator,
                      "upstream_dependencies":[archive],"current_input":{"archive":archive},
                      "classification":status,"regenerated_value_consumed_downstream":status.startswith("A"),
                      "expected_invariants":"Original source ZIP SHA-256 and complete final output gates",
                      "remaining_limitation":limitation})
    final_hashes={
        "august_latest_pre_tip_full":"2acd7448a357163951700c99df33a6949e20b19afc2219e6f8c3082b14d3619d",
        "august_latest_pre_tip_at_risk":"5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3",
        "october_cadence_player_games":"2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67",
    }
    return {
        "scope":"Code-level inventory; classification describes available execution modes, not proof that a private run used them.",
        "classes":{"A":"Fully reconstructed raw source and consumed downstream",
                   "B":"Algorithm reexecuted but consumed historical parsed intermediate",
                   "C":"Reconstructible source/code exists but canonical final path is unconnected",
                   "D":"Versioned historical human or methodological decision",
                   "E":"Unresolved original evidence or acquisition metadata"},
        "restored_file_count":len(FILES),"restored_selector_count":len(SELECTOR_NAMES),
        "required_source_zip_names":sorted(set(REQUIRED_ZIPS)|set(RAW_PDF_EXTRA_ZIPS)),
        "optional_selector_schedule_zip_names":sorted(SELECTOR_SCHEDULE_EXTRA_ZIPS),
        "required_six_season_source_zip_names":sorted(set(REQUIRED_ZIPS)|set(RAW_PDF_EXTRA_ZIPS)|set(SELECTOR_SCHEDULE_EXTRA_ZIPS)
                                                      |{"audit_2021_22_s4_join_results.zip","audit_2025_26_s4_join_results.zip"}),
        "nodes":nodes,"final_dataset_decoded_sha256":final_hashes,
        "final_stage":"reproduce_final_datasets.py",
        "strict_six_season_raw_source_acceptance":False,
        "six_season_connected_mode":{
            "flag":"--rebuild-six-season-october-sources",
            "required_generated_input_opens_per_builder":18,
            "generated_input_paths":generated_paths,
            "complete_candidate_PDFs":23483,"complete_candidate_rows":2200803,
            "cumulative_original_October_scientific_verdict":"pass",
            "cumulative_evidence":"validation/six_season_cumulative_2026-11-15/cumulative_acceptance.json",
            "fresh_three_dataset_execution_evidence":"validation/six_season_end_to_end_2026-11-15/verification.json",
            "fresh_three_dataset_scientific_verdict":"pass",
            "historical_artifact_verdict":"2025_metadata_exception_unresolved",
            "original_roster_and_reviewed_lookup_inputs_inherited_unless_separately_rebuilt":True,
        },
        "controlled_2025_metadata_experiment":{
            "evidence":"validation/2025_team_metadata_experiment_2026-11-15/experiment_acceptance.json",
            "frozen_and_corrected_scientific_panels_exact":True,
            "all_four_statistical_model_fields_exact":True,
            "model_execution_seconds_excluded_and_reported":True,
            "historical_team_artifact_equivalence":False,
            "cumulative_six_season_execution":False,
        },
        "remaining_computational_tasks":[
            "Revalidate the optional original NBA JSON cache path when those primary payloads are available; the accepted six-PDF-source run used the pinned historical roster input.",
            "Recover remaining historical source evidence, including exact 2025 S4 team metadata provenance, without equating that issue to scientific-output differences.",
            "Connect remaining upstream game/venue, player-crosswalk and advance-TV/Cup/award source maps where authentic primary evidence and original rules are available.",
            "Retain human-reviewed identity and medical-taxonomy decisions as versioned inputs; never algorithmically invent replacements.",
        ],
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    rendered=json.dumps(build_report(),indent=2)+"\n"
    if a.output:
        if a.output.exists():
            raise FileExistsError(a.output)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(rendered)
    else:
        print(rendered,end="")


if __name__=="__main__":
    main()
