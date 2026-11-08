#!/usr/bin/env python3
"""Reassemble inputs for the *historical* NBA cadence builder from local ZIPs.

This is replay from intermediate artifacts, NOT source-PDF/boxscore-to-paper
reconstruction. Archive members are resolved by exact basename, never assumed
directory prefixes. Missing/ambiguous matches fail before any files are written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import zipfile

# Frozen builder's required inputs. (Destination within nba_continue, source ZIP,
# exact basename, NOT a guessed ZIP-internal path.)
FILES = [
    ("analysis/nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz",
     "nba_player_game_analysis_ready_v1.zip", "player_game_panel_analysis_ready.csv.gz"),
    ("cadence_2025/player_crosswalk_final.csv",
     "nba_player_crosswalk_final_v1.zip", "player_crosswalk_final.csv"),
    ("cadence_core_full/nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py",
     "nba_player_game_at_risk_core_v1.zip", "parser_2023plus.py"),
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
     "audit_2023_24_pre_s4_outputs.zip", "s1_snapshot_rows_regular_season.csv"),
    ("cadence_work/season_parsed/2024-25/s1_snapshot_rows_regular_season_real.csv",
     "audit_2024_25_pre_s4_outputs_corrected.zip", "s1_snapshot_rows_regular_season_real.csv"),
]
# The source builder uses 6 season-specific maps and these 4 canonical team
# submission-status maps (the 2022/23 status files come from their S4 archives).
SEASONS = ("2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26")
SELECTOR_NAMES = tuple(f"{s}_game_snapshot_join_harmonized_canonical.csv" for s in SEASONS) + tuple(
    f"{s}_team_game_status_harmonized_canonical.csv"
    for s in ("2020-21", "2021-22", "2024-25", "2025-26")
)
SELECTOR_ZIP = "nba_canonical_snapshot_selector_v1.zip"
SELECTOR_DEST = "cadence_work/selector/nba_canonical_snapshot_selector_v1"
RAW_2025 = ("audit_2025_26_upload.zip", "audit_2025_26_targeted_upload.zip")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_member(z: zipfile.ZipFile, basename: str) -> str:
    """Exact basename; reject duplicate/ambiguous matches, including extra copies."""
    candidates = [n for n in z.namelist() if not n.endswith("/")
                  and Path(n).name == basename]
    if len(candidates) != 1:
        example = ", ".join(candidates[:12]) if candidates else "none"
        raise ValueError(f"{z.filename}: expected exactly one '{basename}', "
                         f"found {len(candidates)}: {example}")
    member = candidates[0]
    parts = Path(member).parts
    if Path(member).is_absolute() or ".." in parts or "\\" in member:
        raise ValueError(f"Unsafe ZIP member: {member}")
    info = z.getinfo(member)
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode) or not info.file_size:
        raise ValueError(f"Refusing symlink or empty ZIP file: {member}")
    return member


def build_plan(archives: Path):
    """Fully preflight required ZIPs and ZIP-internal paths without writing."""
    required = {archive for _, archive, _ in FILES} | {SELECTOR_ZIP, *RAW_2025}
    missing = sorted(a for a in required if not (archives / a).is_file())
    if missing:
        raise FileNotFoundError("Missing archive(s): " + ", ".join(missing))
    plan = []
    for dest, archive, basename in FILES:
        with zipfile.ZipFile(archives / archive) as z:
            member = resolve_member(z, basename)
        plan.append((dest, archive, member))
    with zipfile.ZipFile(archives / SELECTOR_ZIP) as z:
        for basename in SELECTOR_NAMES:
            member = resolve_member(z, basename)
            plan.append((f"{SELECTOR_DEST}/{basename}", SELECTOR_ZIP, member))
    # Historical alias matching is optional. Do not assert it exists in a
    # guessed archive; original builder can use its own identity fallbacks.
    for archive in ("nba_player_crosswalk_final_v1.zip",
                    "nba_player_game_at_risk_core_v1.zip"):
        with zipfile.ZipFile(archives / archive) as z:
            matches = [n for n in z.namelist() if Path(n).name == "player_alias_table.csv"]
            if len(matches) > 1:
                raise ValueError(f"Ambiguous optional aliases in {archive}: {matches}")
            if matches:
                plan.append(("cadence_work/player_alias_table.csv", archive,
                             resolve_member(z, "player_alias_table.csv")))
                break
    destinations = [item[0] for item in plan]
    if len(destinations) != len(set(destinations)):
        raise ValueError("Output destination collision in archive restoration plan")
    return plan


def save_member(z: zipfile.ZipFile, member: str, output: Path):
    info = z.getinfo(member)
    if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
        raise ValueError(f"Not a regular file: {member}")
    expected = hashlib.sha256()
    with z.open(info) as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            expected.update(chunk)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise RuntimeError(f"Symlink destination is not allowed: {output}")
    if output.exists():
        if not output.is_file() or sha256(output) != expected.hexdigest():
            raise RuntimeError(f"Existing destination differs: {output}")
        state = "unchanged"
    else:
        with z.open(info) as stream, output.open("xb") as dest:
            shutil.copyfileobj(stream, dest, length=1024 * 1024)
        if sha256(output) != expected.hexdigest():
            raise RuntimeError(f"SHA-256 mismatch after copying: {output}")
        state = "restored"
    return {"path": str(output), "bytes": info.file_size,
            "sha256": expected.hexdigest(), "state": state}


def restore(archives: Path, root: Path, plan):
    records = []
    for dest, archive, member in plan:
        with zipfile.ZipFile(archives / archive) as z:
            record = save_member(z, member, root / dest)
        records.append({"source_archive": archive, "source_member": member, **record})
    for archive in RAW_2025:
        source, target = archives / archive, root / "cadence_2025" / archive
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            raise RuntimeError(f"Symlink destination is not allowed: {target}")
        if target.exists():
            if not target.is_file() or sha256(source) != sha256(target):
                raise RuntimeError(f"Existing original PDF archive differs: {target}")
            state = "unchanged"
        else:
            try:
                target.hardlink_to(source)
                state = "hardlinked"
            except OSError:
                shutil.copy2(source, target)
                state = "copied"
        records.append({"source_archive": archive, "source_member": "(entire archive)",
                        "path": str(target), "sha256": sha256(target),
                        "bytes": target.stat().st_size, "state": state})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true",
                        help="Validate archive members without writing files")
    args = parser.parse_args()
    archives, root = args.archive_dir.resolve(), args.historical_root.resolve()
    plan = build_plan(archives)
    if args.check_only:
        print(json.dumps({"status": "source-member-plan-only",
                          "input_members": [{"destination": dst, "archive": arc, "member": mem}
                                            for dst, arc, mem in plan],
                          "unverified_raw_pdf_archives": list(RAW_2025)}, indent=2))
        return
    records = restore(archives, root, plan)
    provenance = root / "restore_provenance.json"
    provenance.parent.mkdir(parents=True, exist_ok=True)
    provenance.write_text(json.dumps({"replay_scope": "historical-intermediate",
                                      "records": records}, indent=2) + "\n")
    print(f"Restored or verified {len(records)} files. Provenance: {provenance}")


if __name__ == "__main__":
    main()
