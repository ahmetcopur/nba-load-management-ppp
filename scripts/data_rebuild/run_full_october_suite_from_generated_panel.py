#!/usr/bin/env python3
"""Run all TEN original October scripts on a newly source-rebuilt cadence panel.

The source-rebuilt harmonized panel is accepted only when its exact original
decoded SHA-256, canonical path, and private source-generation acceptance
report all agree. The ten original October analysis scripts are then run
UNCHANGED from a clean, pinned historical Git checkout using their separate
pandas-3 Python runtime. All 33 archived model/audit outputs are compared
with the published frozen tables, including every text cell and all numerical
cells to the existing predeclared 1e-9 tolerance (runtime seconds excluded).

This intentionally requires an independent October Python 3.12 / pandas
3.0.5 environment; the upstream PDF/core builder uses pandas 2.2.3.
Archived non-panel auxiliaries from the historical public source checkout
remain input dependencies. No private original archives, selected-report rows,
or manuscript files are committed or modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.data_rebuild.october_corrected_chronology import (
    PANEL, NUMERICAL_TOLERANCE, EXPECTED_ARCHIVED_OUTPUTS,
    digest_gzip_payload, verify_shared_commit, prepare, run_all,
    reproduction, require_reproduction,
)

SOURCE_OCTOBER_PANEL_SHA256 = (
    "3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac"
)
SOURCE_REPORT_NAME = "october_cadence_reproduction_report.json"
SOURCE_PANEL_REL = Path(
    "cadence_harmonized_results/player_team_game_harmonized_cadence.csv.gz"
)
EXPECTED_ORIGINAL_2025_HARMONIZED_PDFS = 355
EXPECTED_STAGE6_MODEL_COUNT = 4
EXPECTED_OUTPUT_COUNT = 33


def check_private_destination(shared: Path, source_panel: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing October analysis replay: {output}")
    if not shared.is_dir() or not source_panel.is_file():
        raise FileNotFoundError("Original shared checkout and source-rebuilt cadence panel required")
    if output == shared or shared in output.parents or output in shared.parents:
        raise ValueError("October replay cannot overwrite or nest in the original shared checkout")
    if output == source_panel or output in source_panel.parents or source_panel in output.parents:
        raise ValueError("October replay output must not overlap the source-generated panel")
    if any((p / ".git").exists() for p in (output, *output.parents)):
        raise ValueError("Private output must not be written inside any Git checkout")


def verify_source_generated_panel(source_panel: Path) -> dict:
    """Accept only the original-stage execution's canonical, checked output."""
    source_panel = source_panel.resolve()
    if source_panel.relative_to(source_panel.parent).name != SOURCE_PANEL_REL.name:
        raise ValueError("Selected October panel filename differs from original source stage")
    if source_panel.parent.name != SOURCE_PANEL_REL.parent.name:
        raise ValueError("October panel must be in source builder's cadence_harmonized_results/")
    source_root = source_panel.parent.parent
    report_path = source_root / SOURCE_REPORT_NAME
    if not report_path.is_file():
        raise FileNotFoundError(f"Source-generated October acceptance report missing: {report_path}")
    if any((p / ".git").exists() for p in (source_panel, *source_panel.parents)):
        raise ValueError("Private October source-generated panel may not reside in Git checkout")
    record = json.loads(report_path.read_text(encoding="utf-8"))
    if record.get("status") != "pass":
        raise ValueError("Historical October source-generation stage not accepted")
    if record.get("original_source_stages_executed") != [
        "historical_panel", "historical_models"
    ]:
        raise ValueError("Original historical October panel and four models must first pass")
    prior = record.get("full_decoded_harmonized_panel_exact") or {}
    if not prior.get("identical_decoded_bytes"):
        raise ValueError("Source-generation report does not prove exact decoded panel")
    if prior.get("decoded_sha256") != SOURCE_OCTOBER_PANEL_SHA256:
        raise ValueError("Source-generation report gives an unexpected panel fingerprint")
    source = record.get("source_2025_harmonized") or {}
    if source.get("fresh_original_pdfs_parsed") != EXPECTED_ORIGINAL_2025_HARMONIZED_PDFS:
        raise ValueError("Source October stage did not parse 355 original harmonized 2025 PDFs")
    models = record.get("four_original_October_model_results") or {}
    if not models.get("matched") or models.get("model_specifications") != EXPECTED_STAGE6_MODEL_COUNT:
        raise ValueError("Original historical October Stage-6 models did not match")
    actual = digest_gzip_payload(source_panel)
    if actual != SOURCE_OCTOBER_PANEL_SHA256:
        raise ValueError(f"Regenerated panel bytes differ from pinned October payload: {actual}")
    return {
        "regenerated_panel_decoded_sha256": actual,
        "real_original_2025_cadence_pdfs": EXPECTED_ORIGINAL_2025_HARMONIZED_PDFS,
        "prior_stage6_original_model_specs_exact": EXPECTED_STAGE6_MODEL_COUNT,
        "original_october_panel_source_accepted": True,
    }


def verify_october_runtime(python: Path) -> dict:
    code = (
        "import sys,pandas,numpy,scipy,statsmodels,json;"
        "print(json.dumps({'python':sys.version.split()[0],"
        "'pandas':pandas.__version__,'numpy':numpy.__version__,"
        "'scipy':scipy.__version__,'statsmodels':statsmodels.__version__}))"
    )
    process = subprocess.run(
        [str(python), "-c", code], capture_output=True,
        text=True, check=True, timeout=30,
    )
    versions = json.loads(process.stdout.strip())
    if (not versions["python"].startswith("3.12.")
        or versions["pandas"] != "3.0.5"
        or versions["numpy"] != "2.5.2"
        or versions["scipy"] != "1.18.0"
        or versions["statsmodels"] != "0.14.6"):
        raise ValueError(f"October source-model environment differs from pinned lock: {versions}")
    return versions


def run(shared_repo: Path, rebuilt_panel: Path, work_dir: Path, *,
        october_python: Path) -> dict:
    shared_repo, rebuilt_panel, work_dir = (
        shared_repo.resolve(), rebuilt_panel.resolve(), work_dir.resolve()
    )
    check_private_destination(shared_repo, rebuilt_panel, work_dir)
    source = verify_source_generated_panel(rebuilt_panel)
    verify_shared_commit(shared_repo)
    runtime = verify_october_runtime(october_python.resolve())
    # Create only after *all* preflight checks. Never modify historical checkout.
    work_dir.mkdir(parents=True, exist_ok=False)
    child = work_dir / "original_october_ten_scripts_from_new_panel"
    prepare(shared_repo, child, rebuilt_panel)
    run_all(child, str(october_python.resolve()))
    results = reproduction(child)
    require_reproduction(results, tolerance=NUMERICAL_TOLERANCE)
    if len(results) != EXPECTED_OUTPUT_COUNT:
        raise ValueError("Archived original October result file count changed")
    largest = max(float(r["max_abs_numeric_difference"]) for r in results.values())
    if largest > NUMERICAL_TOLERANCE:
        raise ValueError("Original October source-derived coefficient inference changed")
    report = {
        "status": "pass",
        "scope": "Source-generated October cadence player-game panel -> all 10 unchanged public historical October scripts -> 33 original archived result tables",
        "source_stage": source,
        "october_release_python_runtime": runtime,
        "all_original_ten_october_scripts_ran": True,
        "original_33_reference_output_comparisons": len(results),
        "maximum_absolute_numeric_difference": largest,
        "numerical_tolerance": NUMERICAL_TOLERANCE,
        "all_original_reference_text_cells_equal": True,
        "source_generated_data_replaced_shared_archived_panel": True,
        "archived_non_panel_auxiliary_sources_still_used": True,
        "original_source_inputs_or_manuscript_modified": False,
        "private_player_level_files_pushed_to_GitHub": False,
        "result_files": results,
    }
    (work_dir / "original_ten_october_models_from_source.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shared-repo", type=Path, required=True,
                        help="Clean original historical repository at pinned October source commit")
    parser.add_argument("--generated-october-panel", type=Path, required=True,
                        help="Previously accepted source-generated cadence panel CSV.gz")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="NEW private destination outside both Git checkouts and input trees")
    parser.add_argument("--october-python", type=Path, required=True,
                        help="Python 3.12 interpreter with immutable requirements-october-lock.txt")
    a = parser.parse_args()
    result = run(a.shared_repo, a.generated_october_panel,
                 a.output_dir, october_python=a.october_python)
    print(json.dumps({
        key: val for key, val in result.items() if key != "result_files"
    }, indent=2))


if __name__ == "__main__":
    main()
