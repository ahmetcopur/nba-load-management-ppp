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
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.data_rebuild.run_connected_player_game_core import execute
from scripts.data_rebuild.run_connected_star_enrichment import (
    immutable_original_star_source, run_star, STAR_ZIP,
)


def reproduce(archive_dir: Path, output_dir: Path, *,
              timeout_seconds: int = 900) -> dict:
    archive_dir, output_dir = archive_dir.resolve(), output_dir.resolve()
    # Validate that this original star package is available BEFORE creating
    # any private reconstructed core output. The stage runner rechecks it.
    immutable_original_star_source(archive_dir / STAR_ZIP)
    core = execute(archive_dir, output_dir, timeout_seconds=timeout_seconds)
    star = run_star(archive_dir, output_dir, timeout_seconds=timeout_seconds)
    result = {
        "status": "pass",
        "scope": "Original archived selected-report inputs -> independently rebuilt player IDs -> original finalizer -> source-pinned award/star enrichment.",
        "core_identity_rows": core["identity"]["frozen_comparison"]["rows"],
        "core_final_player_game_rows": core["original_finalizer_summary"]["final_player_game_rows"],
        "core_at_risk_rows": core["original_finalizer_summary"]["at_risk_rows"],
        "core_exact_output_files": len(core["compared_original_outputs"]),
        "star_exact_output_files": len(star["outputs"]),
        "full_pipeline_starts_at_raw_injury_pdfs": False,
        "official_award_history_independently_verified": False,
        "nba_cup_and_model_enrichment_rebuilt": False,
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
    args = p.parse_args()
    print(json.dumps(
        reproduce(args.archive_dir, args.output_dir, timeout_seconds=args.timeout_seconds),
        indent=2
    ))


if __name__ == "__main__":
    main()
