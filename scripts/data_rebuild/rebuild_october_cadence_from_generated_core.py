#!/usr/bin/env python3
"""Original October cadence panel + Stage-6 models from source-derived NBA data.

Source input: a newly REBUILT reviewed analysis-ready full panel, real
historical selected-report parser CSVs (previously verified against original
PDFs), and 355 newly parsed original 2025-26 *harmonized* report PDFs.

The historical combined October panel/model builder is source-hash pinned.
Its pre-model panel-generation section is executed with ONLY its hard-coded
ROOT path redirected. The original all-in-one model section cannot execute:
it shadows scipy.stats.norm with a local norm() text function. Rather than
edit that frozen code, execute the separate historically archived
run_cadence_models_fast.py on the freshly reconstructed exact panel.

All panel decoded bytes, four model specs, inference columns, source hashes,
report match identities and release counts are fail-closed acceptance gates.
The original 2020-21 reason text and 2021-24 parser reference intermediates
remain historical inputs, not directly re-extracted by this invocation.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.data_rebuild.rebuild_2025_selected_from_pdfs import (
    SOURCE_ZIPS as RAW_2025_ZIPS, init_parser, parse_selected_pdf,
    stage_pdfs,
)
from scripts.data_rebuild.run_connected_player_game_core import (
    compare_streams, extract_exact_member, sha256_file, read_member,
)
from scripts.data_rebuild.compare_stage6_models import (
    archived_rows, candidate_rows, compare,
)

REPO = Path(__file__).resolve().parents[2]
STAGE6_ZIP = REPO / "packages/06_cadence_harmonized_identification.zip"
STAGE6_SHA256 = "821b50373d0ab6f27237d05f2d1d2b32f669f2bbbcd25e7fe0cdd5cd8292b221"
CORE_ZIP = "nba_player_game_at_risk_core_v1.zip"
CORE_SHA256 = "a0f82ebcf6117554a4ce1064ab79db9cf93acc5a53fa25000343810843e659f6"
ORIGINAL_PARSER = "nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py"
PARSER_SHA256 = "197c29d46dfea221c381664b96a05453737df55d7b8dd5d5e6f44e49b69e0e06"
ORIGINAL_PANEL_SCRIPT = "scripts/build_harmonized_panel_and_models.py"
ORIGINAL_PANEL_SCRIPT_SHA256 = "81cab67185083572051b44cefbf836acfe6e1860ccf27dd812dc3729aa2a9272"
ORIGINAL_MODEL_SCRIPT = "scripts/run_cadence_models_fast.py"
ORIGINAL_MODEL_SCRIPT_SHA256 = "f33950c15302f281830bbb5f047ca84b744a77d9039c8a313f158c63374001d3"
ORIGINAL_ROOT_LINE = "ROOT=Path('/mnt/data/nba_continue')"
ORIGINAL_MODEL_ROOT_LINE = "ROOT=Path('/mnt/data/nba_continue'); OUT=ROOT/'cadence_harmonized_results'"
PANEL_SOURCE_END = "# Model: player + team-season FE, full controls, two-way player/game clustering."
OUTPUT_PANEL = "results/player_team_game_harmonized_cadence.csv.gz"
OUTPUT_MODELS = "results/cadence_harmonized_model_results.csv"
EXPECTED_PANEL_DECODED_SHA256 = "3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac"
ORIGINAL_SOURCE_PACKAGES = {
    "nba_canonical_snapshot_selector_v1.zip": "fa724ee6cd341b0322c311258f472f0ad7dfeeea4683cf2e406a48fe0d1f94a7",
    "audit_2020_21_corrected_outputs.zip": "295e854897027949f4e4246016c36cb53aa1cb4c55aa2331b3b3aef8bb6f3ad8",
    "audit_2021_22_cadence_outputs.zip": "861ccc5ea82834632b6fc9c477be318aaa09ea9a243d4a990f93051af148b420",
    "audit_2022_23_pre_s4_outputs.zip": "dd750f6f95e907ed55cf673ce08ee321062aac03b09ec79aa4abffadae94513b",
    "audit_2023_24_pre_s4_outputs.zip": "edd411a4dd1ad113f32492d2e9fd96a842727628566d56b9b797c3913d19abbf",
    "audit_2024_25_pre_s4_outputs_corrected.zip": "6b569b2f39b9f2e73087dffd3e83f11d32c5ac09fb92661d4c4b467d5b3bdcb8",
    "audit_2022_23_s4_join_results.zip": "fbbdcca334f0c904ae48f76551dc50319db346f487e90a77eacacd5839df97c6",
    "audit_2023_24_s4_join_results.zip": "9d59f4f0dde7aed9b8dacfd3706b55f24c1aa9a17cf1e6bdc093eb498570d5e7",
    "nba_player_crosswalk_final_v1.zip": "6ac400125d33a4e44e0f0a4a068f83762425da28bc1d86ce8fc3de8e6ccb3def",
    CORE_ZIP: CORE_SHA256,
    **RAW_2025_ZIPS,
}
# Archive member => private destination, with no arbitrary ZIP extraction.
SOURCE_CSVS = (
    ("audit_2020_21_corrected_outputs.zip", "s1_snapshot_rows_corrected.csv",
     "cadence_work/season_parsed/2020-21/s1_snapshot_rows_corrected.csv"),
    ("audit_2021_22_cadence_outputs.zip", "s1_snapshot_rows_harmonized.csv",
     "cadence_work/season_parsed/2021-22/s1_snapshot_rows_harmonized.csv"),
    ("audit_2022_23_pre_s4_outputs.zip", "s1_snapshot_rows_regular_season.csv",
     "cadence_work/season_parsed/2022-23/s1_snapshot_rows_regular_season.csv"),
    ("audit_2023_24_pre_s4_outputs.zip",
     "audit_2023_24_pre_s4_outputs/s1_snapshot_rows_regular_season.csv",
     "cadence_work/season_parsed/2023-24/audit_2023_24_pre_s4_outputs/s1_snapshot_rows_regular_season.csv"),
    ("audit_2024_25_pre_s4_outputs_corrected.zip",
     "s1_snapshot_rows_regular_season_real.csv",
     "cadence_work/season_parsed/2024-25/s1_snapshot_rows_regular_season_real.csv"),
    ("audit_2022_23_s4_join_results.zip", "team_game_final_pre_tip_status_harmonized.csv",
     "cadence_work/s4/2022-23/team_game_final_pre_tip_status_harmonized.csv"),
    ("audit_2023_24_s4_join_results.zip", "team_game_final_pre_tip_status_harmonized.csv",
     "cadence_work/s4/2023-24/team_game_final_pre_tip_status_harmonized.csv"),
    ("nba_player_crosswalk_final_v1.zip",
     "nba_player_crosswalk_final_v1/player_crosswalk_final.csv",
     "cadence_2025/player_crosswalk_final.csv"),
    ("nba_player_crosswalk_final_v1.zip",
     "nba_player_crosswalk_final_v1/player_alias_table.csv",
     "cadence_work/player_alias_table.csv"),
)


def verify_safe_private_output(archives: Path, panel: Path, output: Path) -> None:
    sources, panel, output = archives.resolve(), panel.resolve(), output.resolve()
    if not sources.is_dir() or not panel.is_file():
        raise FileNotFoundError("Original ZIP directory and newly generated reviewed core are required")
    if output.exists():
        raise FileExistsError("New October source-run directory must not exist")
    if output == sources or sources in output.parents or output in sources.parents:
        raise ValueError("Output must be outside original source ZIP directory")
    if any((p / ".git").exists() for p in (output, *output.parents)):
        raise ValueError("Refusing private player-level data inside Git checkout")
    if any((p / ".git").exists() for p in panel.parents):
        raise ValueError("Refusing private rebuilt panel inside Git checkout")


def pinned_original_source_bytes(archive: Path, member: str, expected: str) -> bytes:
    content = read_member(archive, member)
    digest = hashlib.sha256(content).hexdigest()
    if digest != expected:
        raise ValueError(f"Original October source code SHA256 changed: {member}")
    return content


def panel_only_historical_source(source: bytes, private_root: Path) -> str:
    text = source.decode("utf-8")
    if text.count(ORIGINAL_ROOT_LINE) != 1 or text.count(PANEL_SOURCE_END) != 1:
        raise ValueError("Original October panel-builder path or model boundary changed")
    # Preserve exactly the historical panel and QA code, excluding only the
    # broken all-in-one model part that shadowed scipy.stats.norm.
    panel = text.split(PANEL_SOURCE_END, 1)[0]
    return panel.replace(ORIGINAL_ROOT_LINE,
                         "ROOT=Path(" + repr(str(private_root.resolve())) + ")", 1)


def independent_2025_harmonized_reports(
    archive_dir: Path, output_root: Path, *, workers: int
) -> dict:
    if not 1 <= workers <= 16:
        raise ValueError("2025 original-PDF workers must be 1–16")
    with ZipFile(archive_dir / "nba_canonical_snapshot_selector_v1.zip") as z:
        member = "nba_canonical_snapshot_selector_v1/2025-26_game_snapshot_join_harmonized_canonical.csv"
        if z.namelist().count(member) != 1:
            raise ValueError("Original 2025 harmonized canonical selector missing/duplicated")
        canonical = pd.read_csv(io.BytesIO(z.read(member)))
    if len(canonical) != 1230 or canonical.snapshot_basename.nunique() != 355:
        raise ValueError("Original 2025 cadence report selection counts changed")
    parser_bytes = pinned_original_source_bytes(
        archive_dir / CORE_ZIP, ORIGINAL_PARSER, PARSER_SHA256,
    )
    root = output_root / "_private_raw_2025_harmonized"
    pdf_dir = root / "pdf"
    pdf_dir.mkdir(parents=True)
    parser_file = root / "unchanged_original_2025_parser.py"
    parser_file.write_bytes(parser_bytes)
    groups = defaultdict(list)
    for game in canonical.to_dict("records"):
        groups[str(game["snapshot_basename"])].append(game)
    staged = stage_pdfs(archive_dir, set(groups), pdf_dir)
    tasks = []
    for name, games in sorted(groups.items()):
        stamps = {str(g["published_timestamp_utc"]) for g in games}
        if len(stamps) != 1:
            raise ValueError("Same original 2025 selected PDF has inconsistent UTC publication time")
        tasks.append((name, staged[name], next(iter(stamps)),
                      {str(g["matchup_norm"]) for g in games}))
    records, warnings = [], 0
    with ProcessPoolExecutor(max_workers=workers,
                             initializer=init_parser,
                             initargs=(str(parser_file),)) as pool:
        for name, source_rows, _, warning in pool.map(parse_selected_pdf, tasks):
            records.extend(source_rows)
            warnings += bool(warning)
    if len(records) != 13762:
        raise ValueError(f"Original 2025 selected harmonized PDF rows changed: {len(records)}")
    result_path = (output_root /
        "cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv")
    result_path.parent.mkdir(parents=True)
    pd.DataFrame(records).to_csv(result_path, index=False)
    # Remove only our temporary *individual* PDF staging files after the
    # successful report-row parse. Output selected rows remain private.
    shutil.rmtree(root)
    return {"fresh_original_pdfs_parsed": 355,
            "fresh_2025_cadence_source_rows": len(records),
            "source_parser_warning_pdfs": warnings,
            "2025_all_player_reason_status_records_directly_parsed_from_original_PDFs": True}


def compare_full_decoded_panel(original_zip: Path, generated: Path) -> dict:
    with ZipFile(original_zip) as z:
        member = OUTPUT_PANEL
        if z.namelist().count(member) != 1:
            raise ValueError("Original October panel reference missing/ambiguous")
        with z.open(member) as old_zip, generated.open("rb") as new_zip:
            with gzip.GzipFile(fileobj=old_zip) as old, gzip.GzipFile(fileobj=new_zip) as new:
                result = compare_streams(old, new)
    if result["decoded_sha256"] != EXPECTED_PANEL_DECODED_SHA256:
        raise ValueError("Original October decoded source panel fingerprint changed")
    return result


def run(archives: Path, generated_reviewed_panel: Path, output_dir: Path,
        *, workers: int = 8, timeout_seconds: int = 900) -> dict:
    archives, output_dir = archives.resolve(), output_dir.resolve()
    generated_reviewed_panel = generated_reviewed_panel.resolve()
    verify_safe_private_output(archives, generated_reviewed_panel, output_dir)
    if timeout_seconds <= 0:
        raise ValueError("Original October panel/model subprocess timeout must be positive")
    source_digests = {}
    for filename, expected in ORIGINAL_SOURCE_PACKAGES.items():
        observed = sha256_file(archives / filename)
        if observed != expected:
            raise ValueError(f"Original NBA October dependency ZIP SHA-256 changed: {filename}")
        source_digests[filename] = observed
    if sha256_file(STAGE6_ZIP) != STAGE6_SHA256:
        raise ValueError("Original frozen October Stage6 package SHA-256 changed")
    with gzip.open(generated_reviewed_panel, "rb") as file:
        original_panel_digest = hashlib.sha256()
        for block in iter(lambda: file.read(1024 * 1024), b""):
            original_panel_digest.update(block)
    if original_panel_digest.hexdigest() != (
        "5154317fc52157716cf22f7c5a535259e9f073b3391fd52d78a01faaf8d96d77"
    ):
        raise ValueError("Original source-built reviewed full panel SHA-256 mismatch")
    panel_source = pinned_original_source_bytes(
        STAGE6_ZIP, ORIGINAL_PANEL_SCRIPT, ORIGINAL_PANEL_SCRIPT_SHA256)
    model_source = pinned_original_source_bytes(
        STAGE6_ZIP, ORIGINAL_MODEL_SCRIPT, ORIGINAL_MODEL_SCRIPT_SHA256)

    output_dir.mkdir(parents=True, exist_ok=False)
    new_base = (output_dir /
        "analysis/nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz")
    new_base.parent.mkdir(parents=True)
    shutil.copyfile(generated_reviewed_panel, new_base)

    # Whitelist historical selector outputs, not every file in the ZIP.
    selector_dir = output_dir / "cadence_work/selector/nba_canonical_snapshot_selector_v1"
    selector_dir.mkdir(parents=True)
    with ZipFile(archives / "nba_canonical_snapshot_selector_v1.zip") as archive:
        for season in ("2020-21", "2021-22", "2022-23",
                       "2023-24", "2024-25", "2025-26"):
            for table in ("game_snapshot_join_harmonized_canonical.csv",):
                member = f"nba_canonical_snapshot_selector_v1/{season}_{table}"
                if archive.namelist().count(member) != 1:
                    raise ValueError(f"Original canonical harmonized selection absent: {member}")
                (selector_dir / f"{season}_{table}").write_bytes(archive.read(member))
            if season in ("2020-21", "2021-22", "2024-25", "2025-26"):
                member = f"nba_canonical_snapshot_selector_v1/{season}_team_game_status_harmonized_canonical.csv"
                if archive.namelist().count(member) != 1:
                    raise ValueError(f"Original team-game status absent: {member}")
                (selector_dir / Path(member).name).write_bytes(archive.read(member))
    for archive, member, dest in SOURCE_CSVS:
        extract_exact_member(archives / archive, member, output_dir / dest)

    recent = independent_2025_harmonized_reports(archives, output_dir, workers=workers)
    panel_script = output_dir / "original_historical_panel_builder_panel_only.py"
    panel_script.write_text(panel_only_historical_source(panel_source, output_dir))
    generated_model = model_source.decode("utf-8")
    if generated_model.count(ORIGINAL_MODEL_ROOT_LINE) != 1:
        raise ValueError("Original separate Stage6 model script root unexpectedly changed")
    generated_model = generated_model.replace(
        ORIGINAL_MODEL_ROOT_LINE,
        "ROOT=Path(" + repr(str(output_dir)) + "); OUT=ROOT/'cadence_harmonized_results'", 1,
    )
    model_script = output_dir / "original_historical_cadence_models_paths_only.py"
    model_script.write_text(generated_model)

    env = dict(os.environ, OPENBLAS_NUM_THREADS="1",
               OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
               NUMEXPR_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    stage_results = []
    for name, executable in (("historical_panel", panel_script),
                             ("historical_models", model_script)):
        log = output_dir / f"{name}.stdout.log"
        with log.open("w", encoding="utf-8") as stream:
            p = subprocess.run(
                [sys.executable, str(executable)], cwd=output_dir, env=env,
                stdout=stream, stderr=subprocess.STDOUT,
                timeout=timeout_seconds, check=False,
            )
        if p.returncode:
            raise RuntimeError(
                f"Original source {name} exited {p.returncode}; "
                f"private log: {log}. Do not treat as accepted."
            )
        if name == "historical_panel":
            regenerated = (output_dir /
                "cadence_harmonized_results/player_team_game_harmonized_cadence.csv.gz")
            panel_comparison = compare_full_decoded_panel(STAGE6_ZIP, regenerated)
            if not panel_comparison["identical_decoded_bytes"]:
                raise ValueError("Original source-generated October panel differs")
        stage_results.append(name)
    result_csv = (output_dir /
        "cadence_harmonized_results/cadence_harmonized_model_results.csv")
    verdict = compare(archived_rows(STAGE6_ZIP), candidate_rows(result_csv),
                      pp_tol=1e-10, p_tol=1e-10)
    if not verdict["matched"] or verdict["model_specifications"] != 4:
        raise ValueError(f"Original four October cadence model results changed: {verdict['errors']}")
    result = {
        "status": "pass",
        "scope": "Newly generated reviewed player-game core + verified original 2020–24 parsed reports + 355 original 2025 harmonized PDFs -> original October cadence panel -> original separate four Stage6 models",
        "original_source_package_SHA256": source_digests,
        "historical_stage6_zip_SHA256": STAGE6_SHA256,
        "original_panel_builder_SHA256": ORIGINAL_PANEL_SCRIPT_SHA256,
        "original_separate_model_script_SHA256": ORIGINAL_MODEL_SCRIPT_SHA256,
        "historical_combined_builder_original_model_section_excluded_due_to_norm_name_collision": True,
        "source_2025_harmonized": recent,
        "original_source_stages_executed": stage_results,
        "full_decoded_harmonized_panel_exact": panel_comparison,
        "four_original_October_model_results": verdict,
        "all_four_model_specifications_reproduced": True,
        "old_2020_21_reason_rows_inherited": True,
        "historical_2021_2024_parser_output_intermediates_inherited": True,
        "official_awards_Cup_TV_lookup_crosswalk_adjudication_inherited": True,
        "original_private_archives_modified": False,
    }
    (output_dir / "october_cadence_reproduction_report.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", type=Path, required=True)
    p.add_argument("--generated-reviewed-full-panel", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--timeout-seconds", type=int, default=900)
    a = p.parse_args()
    print(json.dumps(
        run(a.archive_dir, a.generated_reviewed_full_panel, a.output_dir,
            workers=a.workers, timeout_seconds=a.timeout_seconds),
        indent=2
    ))


if __name__ == "__main__":
    main()
