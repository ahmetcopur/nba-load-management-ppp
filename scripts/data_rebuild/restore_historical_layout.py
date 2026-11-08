#!/usr/bin/env python3
"""Restore original historical cadence inputs from separately archived research ZIPs.

No estimates or scientific logic are modified. Every copied file is checksum
logged. Existing files with different bytes cause an error, not an overwrite.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

# Destination in nba_continue, source ZIP basename, exact ZIP member.
FILES = [
 ("analysis/nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz",
  "nba_player_game_analysis_ready_v1.zip",
  "nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz"),
 ("cadence_2025/player_crosswalk_final.csv",
  "nba_player_crosswalk_final_v1.zip",
  "nba_player_crosswalk_final_v1/player_crosswalk_final.csv"),
 ("cadence_work/player_alias_table.csv",
  "nba_player_crosswalk_final_v1.zip",
  "nba_player_crosswalk_final_v1/player_alias_table.csv"),
 ("cadence_core_full/nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py",
  "nba_player_game_at_risk_core_v1.zip",
  "nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py"),
 ("cadence_work/s4/2022-23/team_game_final_pre_tip_status_harmonized.csv",
  "audit_2022_23_s4_join_results.zip", "team_game_final_pre_tip_status_harmonized.csv"),
 ("cadence_work/s4/2023-24/team_game_final_pre_tip_status_harmonized.csv",
  "audit_2023_24_s4_join_results.zip", "team_game_final_pre_tip_status_harmonized.csv"),
 ("cadence_work/season_parsed/2020-21/s1_snapshot_rows_corrected.csv",
  "audit_2020_21_corrected_outputs.zip", "s1_snapshot_rows_corrected.csv"),
 ("cadence_work/season_parsed/2021-22/s1_snapshot_rows_harmonized.csv",
  "audit_2021_22_cadence_outputs.zip", "s1_snapshot_rows_harmonized.csv"),
 ("cadence_work/season_parsed/2022-23/s1_snapshot_rows_regular_season.csv",
  "audit_2022_23_pre_s4_outputs.zip", "s1_snapshot_rows_regular_season.csv"),
 ("cadence_work/season_parsed/2023-24/audit_2023_24_pre_s4_outputs/s1_snapshot_rows_regular_season.csv",
  "audit_2023_24_pre_s4_outputs.zip",
  "audit_2023_24_pre_s4_outputs/s1_snapshot_rows_regular_season.csv"),
 ("cadence_work/season_parsed/2024-25/s1_snapshot_rows_regular_season_real.csv",
  "audit_2024_25_pre_s4_outputs_corrected.zip", "s1_snapshot_rows_regular_season_real.csv"),
]
SELECTOR_ZIP = "nba_canonical_snapshot_selector_v1.zip"
PREFIX = "nba_canonical_snapshot_selector_v1/"
SELECTOR_DEST = "cadence_work/selector/nba_canonical_snapshot_selector_v1"

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def save_member(z, member, output):
    info = z.getinfo(member)
    if info.is_dir():
        raise ValueError("Expected a file: " + member)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise RuntimeError("Refusing to write through symlink: " + str(output))
    expected = hashlib.sha256()
    with z.open(info) as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            expected.update(chunk)
    if output.exists():
        if sha256(output) != expected.hexdigest():
            raise RuntimeError("Existing file differs: " + str(output))
        state = "unchanged"
    else:
        with z.open(info) as src, output.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        if sha256(output) != expected.hexdigest():
            raise RuntimeError("Copy hash mismatch: " + str(output))
        state = "restored"
    return {"path": str(output), "sha256": expected.hexdigest(), "bytes": output.stat().st_size,
            "state": state}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", type=Path, required=True)
    p.add_argument("--historical-root", type=Path, required=True)
    args = p.parse_args()
    root = args.historical_root.resolve()
    archives = args.archive_dir.resolve()
    records = []
    missing = sorted({name for _, name, _ in FILES} | {SELECTOR_ZIP,
                      "audit_2025_26_upload.zip", "audit_2025_26_targeted_upload.zip"})
    missing = [name for name in missing if not (archives / name).is_file()]
    if missing:
        raise SystemExit("Missing archives: " + ", ".join(missing))
    for dest, archive, member in FILES:
        with zipfile.ZipFile(archives / archive) as z:
            record = save_member(z, member, root / dest)
        records.append({"source_archive": archive, "member": member, **record})
    with zipfile.ZipFile(archives / SELECTOR_ZIP) as z:
        members = [n for n in z.namelist() if n.startswith(PREFIX) and n.endswith(".csv")]
        if len(members) < 15:
            raise RuntimeError("Unexpectedly incomplete selector ZIP")
        for member in sorted(members):
            basename = Path(member).name
            record = save_member(z, member, root / SELECTOR_DEST / basename)
            records.append({"source_archive": SELECTOR_ZIP, "member": member, **record})
    for archive in ("audit_2025_26_upload.zip", "audit_2025_26_targeted_upload.zip"):
        src, dest = archives / archive, root / "cadence_2025" / archive
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink():
            raise RuntimeError("Symlink destination not permitted: " + str(dest))
        if dest.exists():
            if sha256(src) != sha256(dest):
                raise RuntimeError("Existing archive differs: " + str(dest))
            state = "unchanged"
        else:
            try:
                dest.hardlink_to(src)
                state = "hardlinked"
            except OSError:
                shutil.copy2(src, dest)
                state = "copied"
        records.append({"source_archive": archive, "member": "(full archive)",
                        "path": str(dest), "sha256": sha256(dest),
                        "bytes": dest.stat().st_size, "state": state})
    log = root / "restore_provenance.json"
    log.write_text(json.dumps({"records": records}, indent=2) + "\n")
    print(f"Verified {len(records)} inputs; provenance written to {log}")

if __name__ == "__main__":
    main()
