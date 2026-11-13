#!/usr/bin/env python3
"""Rebuild the two final corrected NBA analysis panels from pinned private archives.

This is an ORCHESTRATOR for original scientific builders already versioned in
scripts/data_rebuild/. The public repository contains the code and frozen
reference values; the user supplies the original source ZIPs privately.

Outputs (all under a fresh private --output-root/final/):
  august_latest_pre_tip_full.csv.gz
  august_latest_pre_tip_at_risk.csv.gz
  october_cadence_player_games.csv.gz
  corrected_august_provisional_spells.csv.gz
  final_dataset_manifest.json

The default path begins at authenticated historical source INTERMEDIATES.
--verify-original-pdfs reparses all six seasons of original injury PDFs and
feeds selected rows into both August finalizer passes. Optional --boxscore-*
inputs rebuild the original NBA JSON roster and feed it to the August finalizer.
Other sources and the corrected October selector still use archived intermediates.
Source-code, manually reviewed injury, award/Cup/TV lookup decisions are
inherited as documented. No raw NBA data is written into Git.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "scripts" / "data_rebuild"
REFERENCE_CADENCE = REPO / "data_intermediate" / "player_team_game_harmonized_cadence.csv.gz"
STAGE6_ZIP = REPO / "packages" / "06_cadence_harmonized_identification.zip"
SOURCE_HASHES = json.loads((TOOLS / "final_source_sha256.json").read_text())
# Hash of repair_boxscore_rosters.py INSIDE the ZIP, not of the ZIP container.
REPAIR_SCRIPT_SHA256 = "c3d1c8be0dd80f5249935bac8c5de4811dc37cbb6810a98e93202a19e0b32fd0"

# Provenance: union of the immutable August core ZIPs and the historical
# cadence restoration layout in restore_historical_layout.py.
REQUIRED_ZIPS = (
    "nba_player_game_at_risk_core_v1.zip",
    "nba_game_covariates_v1.zip",
    "nba_boxscore_roster_frame_v2_output_upload.zip",
    "nba_player_game_analysis_ready_v1.zip",
    "nba_player_crosswalk_final_v1.zip",
    "nba_canonical_snapshot_selector_v1.zip",
    "audit_2020_21_corrected_outputs.zip",
    "audit_2021_22_cadence_outputs.zip",
    "audit_2022_23_pre_s4_outputs.zip",
    "audit_2022_23_s4_join_results.zip",
    "audit_2023_24_pre_s4_outputs.zip",
    "audit_2023_24_s4_join_results.zip",
    "audit_2024_25_pre_s4_outputs_corrected.zip",
    "audit_2025_26_upload.zip",
    "audit_2025_26_targeted_upload.zip",
)
RAW_PDF_EXTRA_ZIPS = (
    "nba_player_game_at_risk_star_v1.zip",
    "nba_player_game_at_risk_star_cup_v1.zip",
    "audit_2020_21_upload.zip",
    "audit_2021_22_upload.zip",
    "audit_2022_23_upload.zip",
    "audit_2023_24_upload.zip",
    "audit_2024_25_upload.zip",
)
EXPECTED = {
    "august_latest_pre_tip_full": {
        "filename": "august_latest_pre_tip_full.csv.gz",
        "decoded_sha256": "2acd7448a357163951700c99df33a6949e20b19afc2219e6f8c3082b14d3619d",
        "rows": 248728, "risk": 180831, "onsets": 12707,
        "risk_field": "at_risk_for_new_onset", "onset_field": "absence_onset",
    },
    "august_latest_pre_tip_at_risk": {
        "filename": "august_latest_pre_tip_at_risk.csv.gz",
        "decoded_sha256": "5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3",
        "rows": 180831, "risk": 180831, "onsets": 12707,
        "risk_field": None, "onset_field": "absence_onset",
    },
    "october_cadence_player_games": {
        "filename": "october_cadence_player_games.csv.gz",
        "decoded_sha256": "2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67",
        "rows": 248778, "risk": 180664, "onsets": 12729,
        "risk_field": "at_risk_for_new_onset_harm",
        "onset_field": "absence_onset_harm",
    },
}
EXPECTED_MODELS = {
    ("legacy_primary", "full"): (2.6742317292365767, 0.0426339657858416),
    ("harmonized_linear", "full"): (1.2823694527266445, 0.3308675408175164),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decoded_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_panel(path: Path, spec: dict) -> dict:
    """Independently count outcomes and verify the FULL decoded CSV fingerprint."""
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"Missing or symlinked generated dataset: {path}")
    if decoded_sha256(path) != spec["decoded_sha256"]:
        raise ValueError(f"Corrected panel decoded SHA-256 differs: {path}")
    rows = 0
    risk = 0
    onsets = 0
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"player_team_game_id", spec["onset_field"]}
        if spec["risk_field"]:
            required.add(spec["risk_field"])
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing required columns in {path}: {sorted(required - set(reader.fieldnames or []))}")
        keys = set()
        for row in reader:
            ident = row["player_team_game_id"]
            if not ident or ident in keys:
                raise ValueError(f"Missing/duplicate player-game key in {path}")
            keys.add(ident)
            rows += 1
            risk += (row[spec["risk_field"]] == "True") if spec["risk_field"] else 1
            onsets += row[spec["onset_field"]] == "True"
    actual = {"rows": rows, "risk": risk, "onsets": onsets}
    for field, expected in ((f, spec[f]) for f in actual):
        if actual[field] != expected:
            raise ValueError(f"{path}: {field} {actual[field]} != expected {expected}")
    return {**actual, "decoded_sha256": spec["decoded_sha256"],
            "compressed_sha256": sha256_file(path), "compressed_bytes": path.stat().st_size}


def verify_model_report(report: Path) -> dict:
    if not report.is_file():
        raise FileNotFoundError(f"Stage-6 corrected model report missing: {report}")
    content = json.loads(report.read_text(encoding="utf-8"))
    counts = content.get("panel_vs_frozen", {})
    if counts.get("rebuilt_rows") != 248778 or counts.get("risk_rows") != 180664 or counts.get("onsets") != 12729:
        raise ValueError("Corrected Stage-6 panel counts do not meet accepted scientific invariants")
    rows = content.get("stage6_models", [])
    if len(rows) != 4:
        raise ValueError("The original four Stage-6 models were not all executed")
    observed = {(x["definition"], x["controls"]): x for x in rows}
    if len(observed) != 4 or not set(EXPECTED_MODELS).issubset(observed):
        raise ValueError("Corrected Stage-6 specification identities have changed")
    for key, (beta, p) in EXPECTED_MODELS.items():
        model = observed[key]
        if model["n_corrected"] != 180530:
            raise ValueError(f"Wrong complete-case sample for {key}")
        if abs(float(model["estimate_pp_corrected"]) - beta) > 1e-8:
            raise ValueError(f"Corrected Stage-6 coefficient differs for {key}")
        if abs(float(model["p_corrected"]) - p) > 1e-8:
            raise ValueError(f"Corrected Stage-6 p-value differs for {key}")
    return {"models": len(rows), "primary_beta_pp": observed[("legacy_primary", "full")]["estimate_pp_corrected"],
            "linear_beta_pp": observed[("harmonized_linear", "full")]["estimate_pp_corrected"]}



# Expected decoded originals. These are independently pinned by the
# original finalizer and original historical October builder.
PDF_BASELINE_EXPECTED = {
    "august_full_core": (
        "00_original_pdf_baseline/nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz",
        "01_august_core/baseline/nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz",
        "253bf017095a8be45f4c7bb4a0abcc9b942a8db6311f91131c9fd12c7ab46de3",
    ),
    "october_frozen_cadence": (
        "00_original_pdf_baseline/original_october_cadence_from_generated_core/cadence_harmonized_results/player_team_game_harmonized_cadence.csv.gz",
        "04_frozen_cadence/player_team_game_harmonized_cadence.csv.gz",
        "3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac",
    ),
}


def verify_raw_pdf_baseline_link(root: Path) -> dict:
    """Prove raw-PDF rebuilt original panels equal correction-stage originals.

    This verifies equality of scientific frozen inputs. It does not claim the
    correction stages directly used newly parsed PDF rows as file inputs.
    """
    comparisons = {}
    for key, (pdf_relative, archive_relative, expected) in PDF_BASELINE_EXPECTED.items():
        pdf_panel = root / pdf_relative
        archive_panel = root / archive_relative
        if not pdf_panel.is_file() or not archive_panel.is_file():
            raise FileNotFoundError(f"Missing raw-PDF/core baseline: {key}")
        pdf_digest = decoded_sha256(pdf_panel)
        archive_digest = decoded_sha256(archive_panel)
        if pdf_digest != expected or archive_digest != expected:
            raise ValueError(
                f"Original raw-PDF and historical-intermediate frozen baselines differ: "
                f"{key}, pdf={pdf_digest}, archive={archive_digest}, expected={expected}"
            )
        comparisons[key] = {
            "raw_pdf_rebuilt_decoded_sha256": pdf_digest,
            "correction_source_baseline_decoded_sha256": archive_digest,
            "exact_full_csv_equal_via_sha256": True,
        }
    return comparisons


def under_git(path: Path) -> bool:
    return any((m.is_file() or (m.is_dir() and (m / "HEAD").is_file()))
               for node in (path, *path.parents) for m in (node / ".git",))


def preflight(archive_dir: Path, output_root: Path, verify_original_pdfs: bool) -> list[str]:
    if not archive_dir.is_dir() or archive_dir.is_symlink():
        raise FileNotFoundError("Private --archive-dir must be an existing real directory")
    if under_git(archive_dir) or under_git(output_root):
        raise ValueError("Private source archives and output must be OUTSIDE every Git worktree")
    if output_root.exists():
        raise FileExistsError(f"Output root must be new and absent: {output_root}")
    if not output_root.parent.is_dir():
        raise FileNotFoundError(f"Create private output parent first: {output_root.parent}")
    if archive_dir == output_root or archive_dir in output_root.parents or output_root in archive_dir.parents:
        raise ValueError("Private input and output directories must not overlap")
    if not REFERENCE_CADENCE.is_file() or not STAGE6_ZIP.is_file():
        raise FileNotFoundError("Required published frozen cadence reference or Stage-6 package missing")
    required = list(REQUIRED_ZIPS) + (list(RAW_PDF_EXTRA_ZIPS) if verify_original_pdfs else [])
    missing = [filename for filename in required if not (archive_dir / filename).is_file()]
    if missing:
        raise FileNotFoundError("Missing original ZIP(s): " + ", ".join(missing))
    if set(REQUIRED_ZIPS) | set(RAW_PDF_EXTRA_ZIPS) != set(SOURCE_HASHES):
        raise RuntimeError("Source inventory differs from required ZIP names")
    for name in required:
        path = archive_dir / name
        if path.is_symlink() or sha256_file(path) != SOURCE_HASHES[name]:
            raise ValueError(f"Original ZIP SHA-256 differs or is symlinked: {name}")
    return required


def preflight_original_boxscores(v1: Path | None, discovery: Path | None,
                                repair: Path | None, python: Path | None,
                                *, verify_original_pdfs: bool,
                                output: Path | None = None) -> bool:
    """Check the optional raw-cache sources before creating an output directory."""
    provided = (v1, discovery, repair, python)
    if not any(value is not None for value in provided):
        return False
    if not all(value is not None for value in provided):
        raise ValueError("Original boxscore handoff requires all four --boxscore-* options")
    if not verify_original_pdfs:
        raise ValueError("Original boxscore handoff requires --verify-original-pdfs")
    assert v1 is not None and discovery is not None and repair is not None and python is not None
    for directory in (v1, discovery):
        if directory.is_symlink() or not directory.is_dir() or under_git(directory):
            raise ValueError(f"Original boxscore cache must be a real private directory: {directory}")
        if output and (directory == output or directory in output.parents or output in directory.parents):
            raise ValueError("Original boxscore cache and output directories must not overlap")
    if not (v1 / "raw_json").is_dir() or not (v1 / "download_log.csv").is_file():
        raise FileNotFoundError("Original V1 cache requires raw_json/ and download_log.csv")
    if not python.is_file() or not os.access(python, os.X_OK):
        raise FileNotFoundError(f"Boxscore Python executable missing: {python}")
    version = subprocess.run([str(python), "-c", "import pandas; print(pandas.__version__)"],
                             text=True, capture_output=True, check=True).stdout.strip()
    if version != "3.0.5":
        raise RuntimeError(f"Original roster repair requires pandas 3.0.5 (got {version})")
    if repair.is_symlink() or not repair.is_file() or under_git(repair):
        raise FileNotFoundError(f"Original repair ZIP missing or inside Git: {repair}")
    with zipfile.ZipFile(repair) as archive:
        matches = [name for name in archive.namelist()
                   if not name.endswith("/") and Path(name).name == "repair_boxscore_rosters.py"]
        if len(matches) != 1 or Path(matches[0]).is_absolute() or ".." in Path(matches[0]).parts or "\\" in matches[0]:
            raise ValueError("Original boxscore repair ZIP must contain one safe repair_boxscore_rosters.py")
        if hashlib.sha256(archive.read(matches[0])).hexdigest() != REPAIR_SCRIPT_SHA256:
            raise ValueError("Original boxscore repair script SHA-256 differs")
    return True


def stage_commands(archives: Path, root: Path, *, verify_original_pdfs: bool,
                   october_shared_repo: Path | None = None,
                   october_python: Path | None = None,
                   boxscore_v1: Path | None = None,
                   boxscore_discovery: Path | None = None,
                   boxscore_repair_zip: Path | None = None,
                   boxscore_python: Path | None = None) -> list[tuple[str, list[str]]]:
    python = sys.executable
    def tool(name: str, *args: object) -> list[str]:
        return [python, str(TOOLS / name), *[str(x) for x in args]]
    august = root / "01_august_core"
    historical = root / "03_historical_cadence_inputs"
    cadence = root / "04_frozen_cadence"
    correction = root / "06_corrected_cadence"
    work = []
    if verify_original_pdfs:
        work.append(("00_independent_original_six_pdf_baseline",
                     tool("reproduce_core_and_stars.py", "--archive-dir", archives,
                          "--output-dir", root / "00_original_pdf_baseline",
                          "--from-original-2020-2025-pdfs", "--with-cup",
                          "--with-analysis-ready", "--with-october-cadence")))
    if boxscore_v1 is not None:
        if not all((boxscore_discovery, boxscore_repair_zip, boxscore_python)) or not verify_original_pdfs:
            raise ValueError("Original boxscore stage requires all cache paths and --verify-original-pdfs")
        work.append(("00b_original_nba_json_boxscore_roster",
                     [str(boxscore_python), str(TOOLS / "verify_boxscore_cache.py"),
                      "--v1-output", str(boxscore_v1),
                      "--discovery", str(boxscore_discovery),
                      "--fixtures", str(root / "00_original_pdf_baseline/nba_game_covariates_v1/game_level_covariates.csv"),
                      "--repair-zip", str(boxscore_repair_zip),
                      "--reference-zip", str(archives / "nba_boxscore_roster_frame_v2_output_upload.zip"),
                      "--base-panel", str(REPO / "data_final/player_game_panel_analysis_ready.csv.gz"),
                      "--output", str(root / "00b_original_boxscore")]))
    work.extend([
        ("01_august_source_correction",
         tool("rebuild_august_core_from_source_archives.py", "--archives", archives,
              "--output-root", august, *(
                  ["--rebuilt-original-selected-players",
                   root / "00_original_pdf_baseline/nba_player_game_at_risk_core_v1/selected_report_player_rows.csv"]
                  if verify_original_pdfs else []
              ), *(
                  ["--rebuilt-original-boxscore-roster", root / "00b_original_boxscore/game_roster_players.csv"]
                  if boxscore_v1 is not None else []
              ))),
        ("02_august_analysis_ready",
         tool("build_august_analysis_ready_sensitivity.py",
              "--historical-core", august / "baseline/nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz",
              "--corrected-core", august / "corrected_source/nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz",
              "--analysis-ready-zip", archives / "nba_player_game_analysis_ready_v1.zip",
              "--output-dir", root / "02_corrected_august")),
        ("03_frozen_cadence",
         tool("rebuild_from_archives.py", "--archive-dir", archives,
              "--historical-root", historical, "--output", cadence,
              "--reference", REFERENCE_CADENCE)),
        ("04_corrected_cadence",
         tool("fixture_date_chronology_sensitivity.py",
              "--replay-root", historical, "--variant-root", root / "05_corrected_cadence_inputs",
              "--output", correction, "--covariates-zip", archives / "nba_game_covariates_v1.zip",
              "--reference", REFERENCE_CADENCE, "--stage6-zip", STAGE6_ZIP)),
    ])
    if verify_original_pdfs:
        work.insert(-1, ("03b_pdf_derived_october_base_handoff",
                         tool("inject_verified_october_base.py",
                              "--source", root / "00_original_pdf_baseline/analysis_ready_from_generated_core/player_game_panel_analysis_ready.csv.gz",
                              "--target", historical / "analysis/nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz",
                              "--report", root / "03b_pdf_derived_october_base_handoff.json")))
    if october_shared_repo is not None:
        if october_python is None:
            raise ValueError("Corrected October 10-script replay requires --october-python")
        work.append(("05_october_33_tables_from_corrected",
                     [str(october_python),
                      str(TOOLS / "october_corrected_chronology.py"),
                      "--shared-repo", str(october_shared_repo),
                      "--corrected-panel", str(correction / "player_team_game_harmonized_cadence.csv.gz"),
                      "--work", str(root / "07_corrected_october_models"),
                      "--python", str(october_python)]))
    return work


def run_stage(root: Path, name: str, command: list[str]) -> str:
    logfile = root / "logs" / (name + ".log")
    logfile.parent.mkdir(parents=True, exist_ok=True)
    event_log = logfile.parent / "stages.jsonl"
    def record(event):
        with event_log.open("a") as f:
            f.write(json.dumps({"time_utc": datetime.now(timezone.utc).isoformat(),
                                "stage": name, **event}, sort_keys=True) + "\n")
    record({"event": "start", "command": command, "stdout_log": str(logfile.relative_to(root))})
    print(f"RUN {name}: {' '.join(command)}", flush=True)
    with logfile.open("w", encoding="utf-8") as stream:
        status = subprocess.run(command, cwd=REPO, stdout=stream,
                                stderr=subprocess.STDOUT, env={
                                    **os.environ, "OPENBLAS_NUM_THREADS": "1",
                                    "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                                })
    record({"event": "finish", "exit_code": status.returncode})
    if status.returncode:
        raise RuntimeError(f"{name} failed (exit {status.returncode}); private log: {logfile}")
    return str(logfile.relative_to(root))


def build(archives: Path, output: Path, *, verify_original_pdfs: bool = False,
          october_shared_repo: Path | None = None,
          october_python: Path | None = None,
          boxscore_v1: Path | None = None,
          boxscore_discovery: Path | None = None,
          boxscore_repair_zip: Path | None = None,
          boxscore_python: Path | None = None) -> dict:
    archives, output = archives.resolve(), output.resolve()
    original_zips = preflight(archives, output, verify_original_pdfs)
    raw_boxscore = preflight_original_boxscores(
        boxscore_v1, boxscore_discovery, boxscore_repair_zip, boxscore_python,
        verify_original_pdfs=verify_original_pdfs, output=output)
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10+ required")
    from importlib.metadata import version
    pandas_version = version("pandas")
    if int(pandas_version.split(".")[0]) != 2:
        raise RuntimeError(f"Source builder must run with pandas 2.x (got {pandas_version})")
    commands = stage_commands(archives, output, verify_original_pdfs=verify_original_pdfs,
                              october_shared_repo=october_shared_repo,
                              october_python=october_python,
                              boxscore_v1=boxscore_v1, boxscore_discovery=boxscore_discovery,
                              boxscore_repair_zip=boxscore_repair_zip,
                              boxscore_python=boxscore_python)
    output.mkdir(parents=True, exist_ok=False)
    try:
        logs = {name: run_stage(output, name, cmd) for name, cmd in commands}
        august = output / "02_corrected_august"
        cadence = output / "06_corrected_cadence"
        source_paths = {
            "august_latest_pre_tip_full": august / "player_game_panel_analysis_ready.csv.gz",
            "august_latest_pre_tip_at_risk": august / "player_game_panel_model_at_risk_analysis_ready.csv.gz",
            "october_cadence_player_games": cadence / "player_team_game_harmonized_cadence.csv.gz",
        }
        inspected = {key: inspect_panel(source_paths[key], spec)
                     for key, spec in EXPECTED.items()}
        models = verify_model_report(cadence / "fixture_date_chronology_sensitivity.json")
        pdf_baseline = verify_raw_pdf_baseline_link(output) if verify_original_pdfs else None
        handoff = None
        if verify_original_pdfs:
            handoff = json.loads((output / "03b_pdf_derived_october_base_handoff.json").read_text())
            if handoff["substituted_input_decoded_sha256"] != "5154317fc52157716cf22f7c5a535259e9f073b3391fd52d78a01faaf8d96d77":
                raise ValueError("PDF-derived October base handoff differs")
        analysis_qa = json.loads((august / "corrected_august_analysis_ready_qa.json").read_text())
        raw_boxscore_report = None
        if raw_boxscore:
            raw_boxscore_report = json.loads((output / "00b_original_boxscore/boxscore_cache_verification.json").read_text())
            august_report = json.loads((august / "august_core_source_correction_report.json").read_text())
            handoff_report = august_report.get("raw_original_boxscore_roster_handoff")
            if (raw_boxscore_report.get("scope") != "full 7,230-game cache"
                    or not raw_boxscore_report.get("matched") or not handoff_report
                    or not handoff_report.get("exact_non_path_cell_equality_to_archived_roster")
                    or not handoff_report.get("both_source_paths_identify_same_season_and_game_json")):
                raise ValueError("Original NBA JSON roster handoff was not fully verified")
        if (analysis_qa.get("corrected_full_rows") != 248728
                or analysis_qa.get("corrected_risk_rows") != 180831
                or analysis_qa.get("corrected_onsets") != 12707):
            raise ValueError("Corrected August taxonomy/analysis-ready stage invariants failed")
        # Only move the accepted copies into the clearly named final data folder.
        final = output / "final"
        final.mkdir()
        for key, spec in EXPECTED.items():
            shutil.copy2(source_paths[key], final / spec["filename"])
        spells = output / "01_august_core/corrected_source/nba_player_game_at_risk_core_v1/absence_spells_provisional.csv.gz"
        if not spells.is_file():
            raise FileNotFoundError("Corrected provisional absence spell output missing")
        shutil.copy2(spells, final / "corrected_august_provisional_spells.csv.gz")
        manifest = {
            "status": "pass",
            "scope": "Pinned original historical source ZIP intermediates -> source-corrected August/latest-pre-tip and October/cadence final analysis panels",
            "source_level": ("six-season source-PDF-derived player report rows feed corrected August; "
                             "the PDF-derived original reviewed base feeds corrected October after exact hash validation; "
                             + ("verified original NBA JSON roster also feeds August; " if raw_boxscore else "")
                             + "October season report selection, roster, covariates and reviewed decisions remain inherited"),
            "all_six_original_injury_PDF_baseline_rebuilt": verify_original_pdfs,
            "original_PDF_data_fed_directly_into_corrected_augmentation": False,
            "raw_PDF_rebuilt_selected_player_reports_fed_to_corrected_August_core": verify_original_pdfs,
            "raw_PDF_rebuilt_cadence_report_selection_fed_to_corrected_October": False,
            "raw_PDF_rebuilt_original_analysis_base_fed_to_corrected_October": bool(handoff),
            "original_NBA_JSON_roster_fed_to_corrected_August": raw_boxscore,
            "original_NBA_JSON_roster_2020_2025_verification": raw_boxscore_report,
            "pdf_to_october_base_handoff": handoff,
            "raw_pdf_baseline_exact_compatibility": pdf_baseline,
            "original_manual_taxonomy_awards_cup_tv_decisions_inherited": True,
            "original_archives_and_frozen_panels_unmodified": True,
            "input_archives_sha256": {name: sha256_file(archives / name) for name in original_zips},
            "outputs": inspected,
            "stage6_corrected_models": models,
            "stage_logs": logs,
            "structured_stage_log": "logs/stages.jsonl",
            "provisional_spells": {
                "filename": "corrected_august_provisional_spells.csv.gz",
                "compressed_sha256": sha256_file(final / "corrected_august_provisional_spells.csv.gz"),
                "not_a_reviewed_final_taxonomy": True,
            },
        }
        if october_shared_repo:
            saved = output / "07_corrected_october_models/october_corrected_chronology.json"
            if not saved.is_file():
                raise FileNotFoundError("Optional corrected 10-script October output missing")
            suite = json.loads(saved.read_text(encoding="utf-8"))
            if not suite.get("reproduction_passed") or suite.get("sensitivity_rows") != 704:
                raise ValueError("Corrected original October suite acceptance failed")
            manifest["corrected_october_suite"] = {
                "reproduction_passed": True, "sensitivity_rows": 704,
                "report": str(saved.relative_to(output)),
            }
        (final / "final_dataset_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return manifest
    except BaseException:
        # Incomplete intermediates and private logs are retained for debugging,
        # but no success manifest is written.
        print(f"INCOMPLETE: no accepted manifest. Inspect private logs under {output / 'logs'}",
              file=sys.stderr, flush=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-inputs", action="store_true",
                        help="Print required private original ZIP filenames and exit")
    parser.add_argument("--archive-dir", type=Path,
                        help="Private directory of the authentic original ZIPs, outside Git")
    parser.add_argument("--output-root", type=Path,
                        help="New private destination that does not exist yet")
    parser.add_argument("--verify-original-pdfs", action="store_true",
                        help="Additionally rebuild six original PDF seasons into an independently verified FROZEN baseline; corrected stages still use source-intermediate ZIPs")
    parser.add_argument("--boxscore-v1", type=Path,
                        help="Private original V1 boxscore output with raw_json/ and download_log.csv")
    parser.add_argument("--boxscore-discovery", type=Path,
                        help="Private V2 raw_json_discovery directory (45 original JSONs)")
    parser.add_argument("--boxscore-repair-zip", type=Path,
                        help="SHA-256-pinned original V2 roster repair source ZIP")
    parser.add_argument("--boxscore-python", type=Path,
                        help="Separate Python 3.12 environment with requirements-boxscore-lock.txt (pandas 3)")
    parser.add_argument("--october-shared-repo", type=Path,
                        help="Optional clean shared October code checkout at immutable commit 0bd713d9...; rerun all 10 scripts")
    parser.add_argument("--october-python", type=Path,
                        help="Separate original October analysis Python environment for ten-script replay")
    parser.add_argument("--check-only", action="store_true",
                        help="Preflight required source ZIP filenames and paths; do not run builders")
    args = parser.parse_args()
    if args.list_inputs:
        print(json.dumps({
            "required_historical_source_ZIPs": REQUIRED_ZIPS,
            "additional_if_verify_original_pdfs": RAW_PDF_EXTRA_ZIPS,
            "sha256_by_zip": SOURCE_HASHES,
        }, indent=2))
        return
    if args.archive_dir is None or args.output_root is None:
        parser.error("--archive-dir and --output-root are required except with --list-inputs")
    archives, output = args.archive_dir.resolve(), args.output_root.resolve()
    raw_options = dict(boxscore_v1=args.boxscore_v1, boxscore_discovery=args.boxscore_discovery,
                       boxscore_repair_zip=args.boxscore_repair_zip, boxscore_python=args.boxscore_python)
    if args.check_only:
        required = preflight(archives, output, args.verify_original_pdfs)
        boxscore = preflight_original_boxscores(*raw_options.values(), verify_original_pdfs=args.verify_original_pdfs,
                                                output=output)
        print(json.dumps({"status": "preflight-only", "required_zips_present_and_sha256_verified": required,
                          "original_boxscore_cache_paths_and_repair_zip_verified": boxscore,
                          "output_root_untouched": True}, indent=2))
        return
    manifest = build(
        archives, output, verify_original_pdfs=args.verify_original_pdfs,
        october_shared_repo=args.october_shared_repo,
        october_python=args.october_python,
        **raw_options,
    )
    print(json.dumps({
        "status": manifest["status"],
        "final_dataset_dir": str(output / "final"),
        "outputs": {name: {key: value[key] for key in ("rows", "risk", "onsets", "decoded_sha256")}
                    for name, value in manifest["outputs"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()
