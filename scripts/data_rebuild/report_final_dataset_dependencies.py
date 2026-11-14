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

from scripts.data_rebuild.restore_historical_layout import FILES, SELECTOR_NAMES, SELECTOR_ZIP
from scripts.data_rebuild.reproduce_final_datasets import (
    REQUIRED_ZIPS, RAW_PDF_EXTRA_ZIPS, SELECTOR_SCHEDULE_EXTRA_ZIPS,
)


def classification(path: str) -> tuple[str, str, str, str]:
    """Return source, generator, dependency class, and historical limitation."""
    if path.startswith("cadence_work/season_parsed/2020-21/"):
        return ("617 original 2020–21 injury PDFs", "rebuild_2020_selected_from_pdfs.py",
                "B with optional raw-PDF-derived full-row consumption",
                "Publication clocks/manifests inherited; raw-PDF full row and selector handoffs are opt-in.")
    if path.startswith("cadence_work/season_parsed/"):
        if "/2021-22/" in path or "/2022-23/" in path:
            return ("Original full candidate injury PDF ZIP","rebuild_2021_full_candidates.py",
                    "C","Full fresh candidate parser and targeted downstream path exist; canonical final runner remains unconnected.")
        return ("Original season injury PDF ZIP", "rebuild_2021_2024_selected_from_pdfs.py",
                "C", "Only previously selected PDFs are reparsed in the canonical runner; full selector candidates not connected.")
    if path.startswith("cadence_work/s4/"):
        return ("Original S4 report statuses and schedules", "verify_2021_2023_selector_rebuild.py",
                "C", "Historical team status remains archived at the October builder input.")
    if path.startswith("analysis/"):
        return ("Original injury PDFs, NBA JSONs and reviewed reasons", "build_analysis_ready_from_generated_core.py",
                "A (with PDF + JSON options)", "Human reviewed taxonomy and annotations remain versioned original inputs.")
    if path.startswith("cadence_2025/"):
        return ("NBA JSON identities and reviewed alias matches", "verify_player_identity_replay.py",
                "C/D", "Original alias/crosswalk decisions remain inherited at this October input.")
    return ("SHA-pinned original parser code", "rebuild_from_archives.py",
            "D", "Original executable parser is a versioned methodological input.")


def selector_class(name: str) -> tuple[str, str]:
    season=name[:7]
    if season=="2020-21":
        return ("B with optional raw-PDF-derived full-row consumption", "Original selector consumes fresh full PDF-derived rows only with explicit raw-2020 option; report clocks stay inherited.")
    if season=="2024-25":
        return ("B", "Original algorithm executes on archived parsed rows and schedules; raw-PDF candidate rows not connected.")
    if season=="2022-23":
        return ("C","Fresh full regular-season parser, selector and supplied targeted October acceptance passed; canonical final runner still unconnected.")
    if season=="2023-24":
        return ("C", "Original selector function and original PDFs exist; fresh all-candidate rows/status handoff is not connected.")
    if season=="2021-22":
        return ("C", "Full 5,567-PDF parser, selector and supplied targeted October acceptance passed; canonical final runner still unconnected.")
    return ("E", "Only selected 2025 PDFs are freshly parsed; candidate inventory/acquisition clocks remain historical selections.")


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
            "classification":status,"regenerated_value_consumed_downstream":status.startswith("B"),
            "expected_invariants":"1,080 games (2020) or 1,230 games; exact keys/scientific fields and final panel hash",
            "remaining_limitation":limitation,
        })
    upstream=[
        ("game covariates, Elo, rest, travel", "original NBA fixture and venue schedules", "nba_game_covariates_v1.zip", "run_connected_player_game_core.py", "C", "Original calculation replayed independently, but connected final correction still inherits non-date source inputs."),
        ("player participation and roster", "7,230 original NBA boxscore JSON files", "nba_boxscore_roster_frame_v2_output_upload.zip", "verify_boxscore_cache.py", "A with JSON option", "Historical raw_json_path prefix is preserved after confirming same game JSON."),
        ("injury report player identity", "Original six-season injury PDFs and human-reviewed aliases", "nba_player_crosswalk_final_v1.zip", "verify_player_identity_replay.py", "A/D", "Alias choices are versioned human decisions."),
        ("awards and star timeline", "NBA awards and All-Star records", "nba_player_game_at_risk_star_v1.zip", "run_connected_star_enrichment.py", "C/D", "Historical award lookup and reviewed identity decisions remain inherited."),
        ("NBA Cup and TV advance mapping", "Original NBA publication schedules and manual match decisions", "nba_player_game_at_risk_star_cup_v1.zip", "run_connected_cup_enrichment.py", "C/D/E", "Original announcement timing/nominal neutral hosts and some match decisions remain historical inputs."),
        ("reviewed taxonomy", "Original report text and human reviewed reason classifications", "nba_player_game_analysis_ready_v1.zip", "build_analysis_ready_from_generated_core.py", "D", "Never invent replacement human classifications."),
        ("2025 candidate report selection", "Original 2025–26 injury PDF candidate inventory", "audit_2025_26_upload.zip", "verify_2025_manifest_selector.py", "E", "Some original acquisition/selection timestamps cannot be reconstructed from selected PDFs alone."),
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
        "nodes":nodes,"final_dataset_decoded_sha256":final_hashes,
        "final_stage":"reproduce_final_datasets.py",
        "strict_six_season_raw_source_acceptance":False,
        "remaining_computational_tasks":[
            "Connect full all-candidate original PDF parser rows and canonical selector for 2021–24.",
            "Reconstruct 2025 candidate selection only to the extent original acquisition records support it.",
            "Connect fresh selector-derived team statuses, game covariates and remaining computational source maps to October.",
            "Re-run the full Linux amd64 pipeline only after newly connected stages pass isolated authentic checks.",
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
