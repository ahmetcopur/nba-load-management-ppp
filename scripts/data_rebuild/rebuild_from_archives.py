#!/usr/bin/env python3
"""Replay a historical NBA cadence panel from archived intermediate sources.

An optional verified 2020 PDF-derived selector can replace its restored table;
the other seasons and inputs remain archived. Fail on any
restoration, parsing, building, or frozen-panel comparison error.

Run under requirements-builder-lock.txt; pandas 3 changes the original risk-set logic.
"""
import argparse
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "scripts/data_rebuild"
DEFAULT_OUT = REPO / "data_rebuild/output/historical_cadence"


def call(name, args):
    command = [sys.executable, str(TOOLS / name), *map(str, args)]
    print("RUN:", " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--metadata-dir", type=Path,
                        help="Historical source inventory from the shared GitHub repository")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT,
                        help="Separate, ignored directory for rebuilt panel and model outputs")
    parser.add_argument("--reference", type=Path,
                        default=REPO / "data_intermediate/player_team_game_harmonized_cadence.csv.gz")
    parser.add_argument("--skip-stage6-model-comparison", action="store_true",
                        help="Explicitly skip historical Stage-6 coefficient validation")
    parser.add_argument("--skip-2025-parse", action="store_true",
                        help="Requires a previously independently verified 2025 parsed-row CSV")
    parser.add_argument("--reparse-2024-25-from-pdfs", action="store_true",
                        help="Explicit fallback only if the original corrected 2024-25 ZIP is unavailable")
    parser.add_argument("--generated-selector-dir", type=Path,
                        help="After historical restoration, substitute independently regenerated 2020/2024 selectors with exact field/key gates; other seasons stay inherited")
    parser.add_argument("--require-raw-2020-selector", action="store_true",
                        help="Require the regenerated 2020 selector to consume verified fresh original-PDF parsed rows")
    parser.add_argument("--check-only", action="store_true",
                        help="Check ZIP archive member mappings without writing/executing anything")
    args = parser.parse_args()
    if args.require_raw_2020_selector and not args.generated_selector_dir:
        parser.error("--require-raw-2020-selector requires --generated-selector-dir")
    restore_args = ["--archive-dir", args.archive_dir,
                    "--historical-root", args.historical_root]
    if args.reparse_2024_25_from_pdfs:
        if not args.metadata_dir:
            raise SystemExit("--reparse-2024-25-from-pdfs requires --metadata-dir")
        restore_args.append("--skip-2024-25-corrected")
    if args.check_only:
        call("restore_historical_layout.py", [*restore_args, "--check-only"])
        print("Archive layout inspected. No files written, PDFs parsed or models run.")
        return
    call("restore_historical_layout.py", restore_args)
    if args.generated_selector_dir:
        call("inject_generated_canonical_selectors.py",
             ["--generated-dir", args.generated_selector_dir,
              "--historical-root", args.historical_root,
              "--report", args.historical_root / "generated_selector_handoff.json",
              *(["--require-raw-2020"] if args.require_raw_2020_selector else [])])
    if args.reparse_2024_25_from_pdfs:
        call("reparse_2024_25_from_pdfs.py",
             ["--historical-root", args.historical_root,
              "--pdf-zip", args.archive_dir / "audit_2024_25_upload.zip",
              "--pre-s4-zip", args.archive_dir / "audit_2024_25_pre_s4_outputs.zip",
              "--selector-zip", args.archive_dir / "nba_canonical_snapshot_selector_v1.zip",
              "--metadata-dir", args.metadata_dir])
    if args.skip_2025_parse:
        existing = (args.historical_root /
                    "cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv")
        if not existing.is_file():
            raise SystemExit(f"--skip-2025-parse requires a verified existing file: {existing}")
    else:
        parse_args = ["--historical-root", args.historical_root]
        if args.metadata_dir:
            parse_args.extend(["--metadata-dir", args.metadata_dir])
        call("reparse_2025_selected.py", parse_args)
    call("run_historical_cadence_builder.py",
         ["--historical-root", args.historical_root, "--output", args.output])
    candidate = args.output / "player_team_game_harmonized_cadence.csv.gz"
    call("compare_panels.py", ["--reference", args.reference, "--candidate", candidate,
                              "--output", args.output / "panel_comparison.json"])
    call("validate_cadence_panel.py", ["--panel", candidate, "--expect-frozen",
                                     "--output", args.output / "panel_invariants.json"])
    if not args.skip_stage6_model_comparison:
        # The original builder crashes at its model stage; the archived model
        # table comes from the separate historical fast regression executable.
        call("replay_stage6_from_frozen.py",
             ["--panel", candidate, "--output-dir", args.output / "stage6_models"])
    print("PASS: historical intermediate replay matches frozen panel"
          + (" (historical Stage-6 model check skipped)." if args.skip_stage6_model_comparison
             else " and archived Stage-6 coefficients."))


if __name__ == "__main__":
    main()
