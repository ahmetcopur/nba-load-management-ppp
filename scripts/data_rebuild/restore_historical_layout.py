#!/usr/bin/env python3
"""Restore historical NBA intermediate inputs with an audited, non-destructive ZIP mapping.

This is an intermediate-data replay, not raw boxscore-to-panel reconstruction.
ZIP members may have different parent directories across archived packages;
we only accept exact paths or a *unique* file-basename fallback. No guess is
silently accepted when more than one ZIP member could match.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

INPUTS = [
    # Destination relative to historical root, ZIP basename, original expected member,
    # optional (only if the archived builder itself regards the input as optional).
    ("analysis/nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz",
     "nba_player_game_analysis_ready_v1.zip",
     "nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz", False),
    ("cadence_2025/player_crosswalk_final.csv",
     "nba_player_crosswalk_final_v1.zip",
     "nba_player_crosswalk_final_v1/player_crosswalk_final.csv", False),
    ("cadence_work/player_alias_table.csv",
     "nba_player_crosswalk_final_v1.zip",
     "nba_player_crosswalk_final_v1/player_alias_table.csv", True),
    ("cadence_core_full/nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py",
     "nba_player_game_at_risk_core_v1.zip",
     "nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py", False),
    ("cadence_work/s4/2022-23/team_game_final_pre_tip_status_harmonized.csv",
     "audit_2022_23_s4_join_results.zip",
     "team_game_final_pre_tip_status_harmonized.csv", False),
    ("cadence_work/s4/2023-24/team_game_final_pre_tip_status_harmonized.csv",
     "audit_2023_24_s4_join_results.zip",
     "team_game_final_pre_tip_status_harmonized.csv", False),
    ("cadence_work/season_parsed/2020-21/s1_snapshot_rows_corrected.csv",
     "audit_2020_21_corrected_outputs.zip",
     "s1_snapshot_rows_corrected.csv", False),
    ("cadence_work/season_parsed/2021-22/s1_snapshot_rows_harmonized.csv",
     "audit_2021_22_cadence_outputs.zip",
     "s1_snapshot_rows_harmonized.csv", False),
    ("cadence_work/season_parsed/2022-23/s1_snapshot_rows_regular_season.csv",
     "audit_2022_23_pre_s4_outputs.zip",
     "s1_snapshot_rows_regular_season.csv", False),
    ("cadence_work/season_parsed/2023-24/audit_2023_24_pre_s4_outputs/s1_snapshot_rows_regular_season.csv",
     "audit_2023_24_pre_s4_outputs.zip",
     "audit_2023_24_pre_s4_outputs/s1_snapshot_rows_regular_season.csv", False),
    ("cadence_work/season_parsed/2024-25/s1_snapshot_rows_regular_season_real.csv",
     "audit_2024_25_pre_s4_outputs_corrected.zip",
     "s1_snapshot_rows_regular_season_real.csv", False),
]

SELECTOR_ZIP = "nba_canonical_snapshot_selector_v1.zip"
SELECTOR_DEST = "cadence_work/selector/nba_canonical_snapshot_selector_v1"
SEASONS = ("2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26")
SELECTOR_FILES = (
    tuple(f"{s}_game_snapshot_join_harmonized_canonical.csv" for s in SEASONS)
    + tuple(f"{s}_team_game_status_harmonized_canonical.csv"
            for s in ("2020-21", "2021-22", "2024-25", "2025-26"))
)
RAW_2025 = ("audit_2025_26_upload.zip", "audit_2025_26_targeted_upload.zip")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_member(archive: zipfile.ZipFile, preferred: str) -> str:
    """Use exact member or unique basename. Ambiguity is a hard failure."""
    names = [n for n in archive.namelist() if not n.endswith("/")]
    if preferred in names:
        return preferred
    basename = Path(preferred).name
    candidates = [n for n in names if Path(n).name == basename]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(
            f"{archive.filename}: missing ZIP member {preferred} (basename {basename})")
    raise ValueError(
        f"{archive.filename}: ambiguous ZIP member {basename}: {candidates[:15]}")


def copy_member(archive: zipfile.ZipFile, member: str, output: Path) -> dict:
    info = archive.getinfo(member)
    if info.is_dir():
        raise ValueError(f"{archive.filename}: directory is not a file: {member}")
    if output.is_symlink():
        raise ValueError(f"Refusing to write to symlink: {output}")
    source_hash = hashlib.sha256()
    with archive.open(info) as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            source_hash.update(chunk)
    expected = source_hash.hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        if sha256_file(output) != expected:
            raise ValueError(f"Existing file has different bytes; refuse overwrite: {output}")
        status = "already-matched"
    else:
        with archive.open(info) as src, output.open("xb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        if sha256_file(output) != expected:
            raise IOError(f"Copied file hash changed: {output}")
        status = "copied"
    return {"member": member, "output": str(output), "sha256": expected,
            "bytes": output.stat().st_size, "status": status}


def plan(archive_dir: Path) -> list[dict]:
    """Resolve every mandatory ZIP member before writing any output."""
    sources = {p[1] for p in INPUTS} | {SELECTOR_ZIP} | set(RAW_2025)
    missing = sorted(name for name in sources if not (archive_dir / name).is_file())
    if missing:
        raise FileNotFoundError("Missing source ZIP archives: " + ", ".join(missing))
    tasks = []
    for destination, zipname, preferred, optional in INPUTS:
        with zipfile.ZipFile(archive_dir / zipname) as archive:
            try:
                member = resolve_member(archive, preferred)
            except FileNotFoundError:
                if not optional:
                    raise
                tasks.append({"archive": zipname, "destination": destination,
                              "status": "optional-absent", "member": None})
                continue
        tasks.append({"archive": zipname, "destination": destination, "member": member})
    with zipfile.ZipFile(archive_dir / SELECTOR_ZIP) as archive:
        for basename in SELECTOR_FILES:
            member = resolve_member(archive, basename)
            tasks.append({"archive": SELECTOR_ZIP,
                          "destination": f"{SELECTOR_DEST}/{basename}", "member": member})
    return tasks


def restore(archive_dir: Path, root: Path) -> list[dict]:
    tasks = plan(archive_dir)
    records = []
    for task in tasks:
        if task.get("status") == "optional-absent":
            records.append(task)
            continue
        src = archive_dir / task["archive"]
        with zipfile.ZipFile(src) as archive:
            result = copy_member(archive, task["member"], root / task["destination"])
        records.append({"archive": task["archive"], **result})
    for zipname in RAW_2025:
        src, dst = archive_dir / zipname, root / "cadence_2025" / zipname
        if dst.is_symlink():
            raise ValueError(f"Refusing to replace symlink: {dst}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        original_hash = sha256_file(src)
        if dst.exists():
            if sha256_file(dst) != original_hash:
                raise ValueError(f"Existing raw PDF ZIP differs: {dst}")
            status = "already-matched"
        else:
            try:
                dst.hardlink_to(src)
                status = "hardlinked"
            except OSError:
                shutil.copy2(src, dst)
                status = "copied"
            if sha256_file(dst) != original_hash:
                raise IOError(f"Raw ZIP copy failed hash verification: {dst}")
        records.append({"archive": zipname, "member": "(whole archive)",
                        "output": str(dst), "sha256": original_hash, "status": status,
                        "bytes": dst.stat().st_size})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", required=True, type=Path)
    parser.add_argument("--historical-root", required=True, type=Path)
    parser.add_argument("--preflight", action="store_true",
                        help="Resolve source member names without writing any files")
    args = parser.parse_args()
    archives = args.archive_dir.resolve()
    root = args.historical_root.resolve()
    if args.preflight:
        tasks = plan(archives)
        print(json.dumps({"resolved_members": tasks}, indent=2))
        return
    records = restore(archives, root)
    report_path = root / "restore_provenance.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"archived_inputs": records}, indent=2) + "\n")
    print(f"Restored or verified {len(records)} input objects; provenance: {report_path}")


if __name__ == "__main__":
    main()
