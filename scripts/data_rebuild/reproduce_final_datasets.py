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
--verify-original-pdfs additionally rebuilds all six seasons of raw injury
PDFs into an independently checked *frozen baseline*. Its PDF outputs do NOT
silently replace the source intermediate archives in the correction stages.
Source-code, manually reviewed injury, award/Cup/TV lookup decisions are
inherited as documented. No raw NBA data is written into Git.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "scripts" / "data_rebuild"
REFERENCE_CADENCE = REPO / "data_intermediate" / "player_team_game_harmonized_cadence.csv.gz"
STAGE6_ZIP = REPO / "packages" / "06_cadence_harmonized_identification.zip"

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


def under_git(path: Path) -> bool:
    return any((node / ".git").exists() for node in (path, *path.parents))


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
    return required


def stage_commands(archives: Path, root: Path, *, verify_original_pdfs: bool,
                   october_shared_repo: Path | None = None,
                   october_python: Path | None = None) -> list[tuple[str, list[str]]]:
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
    work.extend([
        ("01_august_source_correction",
         tool("rebuild_august_core_from_source_archives.py", "--archives", archives,
              "--output-root", august)),
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
    print(f"RUN {name}: {' '.join(command)}", flush=True)
    with logfile.open("w", encoding="utf-8") as stream:
        status = subprocess.run(command, cwd=REPO, stdout=stream,
                                stderr=subprocess.STDOUT, env={
                                    **os.environ, "OPENBLAS_NUM_THREADS": "1",
                                    "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                                })
    if status.returncode:
        raise RuntimeError(f"{name} failed (exit {status.returncode}); private log: {logfile}")
    return str(logfile.relative_to(root))


def build(archives: Path, output: Path, *, verify_original_pdfs: bool = False,
          october_shared_repo: Path | None = None,
          october_python: Path | None = None) -> dict:
    archives, output = archives.resolve(), output.resolve()
    original_zips = preflight(archives, output, verify_original_pdfs)
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10+ required")
    from importlib.metadata import version
    pandas_version = version("pandas")
    if int(pandas_version.split(".")[0]) != 2:
        raise RuntimeError(f"Source builder must run with pandas 2.x (got {pandas_version})")
    commands = stage_commands(archives, output, verify_original_pdfs=verify_original_pdfs,
                              october_shared_repo=october_shared_repo,
                              october_python=october_python)
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
        analysis_qa = json.loads((august / "corrected_august_analysis_ready_qa.json").read_text())
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
            "source_level": "historical archived intermediates; optional independently source-PDF-rebuilt frozen baseline",
            "all_six_original_injury_PDF_baseline_rebuilt": verify_original_pdfs,
            "original_PDF_data_fed_directly_into_corrected_augmentation": False,
            "original_manual_taxonomy_awards_cup_tv_decisions_inherited": True,
            "original_archives_and_frozen_panels_unmodified": True,
            "input_archives_sha256": {name: sha256_file(archives / name) for name in original_zips},
            "outputs": inspected,
            "stage6_corrected_models": models,
            "stage_logs": logs,
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
        }, indent=2))
        return
    if args.archive_dir is None or args.output_root is None:
        parser.error("--archive-dir and --output-root are required except with --list-inputs")
    archives, output = args.archive_dir.resolve(), args.output_root.resolve()
    if args.check_only:
        required = preflight(archives, output, args.verify_original_pdfs)
        print(json.dumps({"status": "preflight-only", "required_zips_present": required,
                          "output_root_untouched": True}, indent=2))
        return
    manifest = build(
        archives, output, verify_original_pdfs=args.verify_original_pdfs,
        october_shared_repo=args.october_shared_repo,
        october_python=args.october_python,
    )
    print(json.dumps({
        "status": manifest["status"],
        "final_dataset_dir": str(output / "final"),
        "outputs": {name: {key: value[key] for key in ("rows", "risk", "onsets", "decoded_sha256")}
                    for name, value in manifest["outputs"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()
