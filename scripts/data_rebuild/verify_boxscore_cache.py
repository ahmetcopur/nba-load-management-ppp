#!/usr/bin/env python3
"""Audit original cached NBA boxscore JSON and replay the historical V2 roster builder.

--allow-partial is for isolated sample verification. Full mode demands all 7,230
valid, unique official game IDs and a complete archived roster-frame comparison.

The original repair code executes with --no-download; no NBA network calls are
made. The original raw JSON bytes are NOT committed to the repository.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
GAME_ID_RE = re.compile(r"^002(\d{2})(\d{5})$")
OUTPUTS = {
    "game_roster_players.csv": ["game_id", "team", "nba_player_id"],
    "canonical_game_id_crosswalk.csv": ["game_id"],
    "game_boxscore_manifest.csv": ["game_id"],
    "team_game_roster_counts.csv": ["game_id", "team"],
}
REPAIR_ARCHIVED_SHA256 = "c3d1c8be0dd80f5249935bac8c5de4811dc37cbb6810a98e93202a19e0b32fd0"
REPAIR_EXECUTED_SHA256 = "d825588e760482d7720f572cc2b66da48f7e3ce25c2866ecfbee709983cbcf39"
REPAIR_QA_LINE = '    (output / "qa_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")'
REPAIR_QA_CAST = '    summary["complete"] = bool(summary["complete"])'
TEXT_FIELDS = [
    "player_game_id", "season", "source_match_number", "tip_utc",
    "game_date_et", "team_role", "opponent", "nba_player_name", "position",
    "boxscore_player_status", "starter", "not_playing_reason",
    "not_playing_description",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_log_index(log_path: Path):
    log = pd.read_csv(log_path, dtype=str, keep_default_na=False)
    needed = {"status", "raw_json_path", "bytes", "endpoint_name"}
    if not needed.issubset(log):
        raise ValueError(f"Original download log missing columns: {sorted(needed - set(log))}")
    successes = log[log.status.str.startswith("ok") & log.raw_json_path.ne("")]
    found: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for record in successes.itertuples(index=False):
        full = str(record.raw_json_path).replace("\\", "/")
        if "/raw_json/" not in full:
            raise ValueError(f"Original successful download path has no /raw_json/: {full}")
        relative = full.split("/raw_json/", 1)[1]
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"Unsafe download-log relative path: {relative}")
        found[relative].append((int(record.bytes), str(record.endpoint_name)))
    for relative, values in found.items():
        if len({size for size, _ in values}) != 1:
            raise ValueError(f"Conflicting originally logged payload sizes for {relative}: {values}")
    return {relative: values[-1] for relative, values in found.items()}


def hash_cache(roots: dict[str, Path], log_path: Path) -> pd.DataFrame:
    logged = download_log_index(log_path)
    rows = []
    for source, root in roots.items():
        if not root.is_dir():
            raise FileNotFoundError(f"Raw NBA JSON cache directory missing: {root}")
        for path in sorted(root.rglob("boxscore_*.json")):
            raw = path.read_bytes()
            try:
                payload = json.loads(raw)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
            game = payload.get("game") if isinstance(payload, dict) else None
            if not isinstance(game, dict):
                raise ValueError(f"No game object in {path}")
            game_id = str(game.get("gameId", ""))
            if not GAME_ID_RE.fullmatch(game_id):
                raise ValueError(f"Invalid official gameId in {path}: {game_id}")
            for side in ("homeTeam", "awayTeam"):
                team = game.get(side)
                if not isinstance(team, dict) or team.get("teamId") is None:
                    raise ValueError(f"{path}: invalid {side} team object/id")
            if pd.isna(pd.to_datetime(game.get("gameTimeUTC"), utc=True, errors="coerce")):
                raise ValueError(f"{path}: missing/unparseable official gameTimeUTC")
            expected_season = f"{2000 + int(game_id[3:5])}_{(int(game_id[3:5]) + 1) % 100:02d}"
            relative = f"{path.parent.name}/{path.name}"
            log_size, endpoint = logged.get(relative, (None, None)) if source == "v1_raw_json" else (None, None)
            rows.append({
                "source": source,
                "season_folder": path.parent.name,
                "file": path.name,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "payload_game_id": game_id,
                "name_matches_payload": path.name == f"boxscore_{game_id}.json",
                "season_matches_payload": path.parent.name == expected_season,
                "logged_bytes": log_size,
                "logged_endpoint": endpoint,
            })
    if not rows:
        raise ValueError("No raw boxscore JSON files were discovered")
    return pd.DataFrame(rows)


def single_archive_member(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [n for n in archive.namelist()
               if not n.endswith("/") and Path(n).name == basename]
    if len(matches) != 1:
        raise ValueError(f"{archive.filename}: expected exactly one {basename}, found {matches}")
    if ".." in Path(matches[0]).parts or Path(matches[0]).is_absolute():
        raise ValueError(f"Unsafe archive member: {matches[0]}")
    return matches[0]


def historically_executed_repair_source(repair_zip: Path, optional_local_script: Path | None = None):
    """Reconstruct and byte-verify the one-line QA serialization fix.

    The historical ZIP has the executable except for a single final numpy-bool
    serialization fix. Do not permit arbitrary code via --repair-script.
    """
    with zipfile.ZipFile(repair_zip) as archive:
        member = single_archive_member(archive, "repair_boxscore_rosters.py")
        archived_bytes = archive.read(member)
    if hashlib.sha256(archived_bytes).hexdigest() != REPAIR_ARCHIVED_SHA256:
        raise RuntimeError("Unexpected archived V2 repair script bytes; review provenance")
    archived = archived_bytes.decode("utf-8")
    if archived.count(REPAIR_QA_LINE) != 1 or REPAIR_QA_CAST in archived:
        raise RuntimeError("Original repair source does not match the documented one-line fix")
    executed = archived.replace(REPAIR_QA_LINE,
                                REPAIR_QA_CAST + "\n" + REPAIR_QA_LINE, 1).encode("utf-8")
    if hashlib.sha256(executed).hexdigest() != REPAIR_EXECUTED_SHA256:
        raise RuntimeError("Rebuilt historically executed repair script SHA-256 mismatch")
    if optional_local_script is not None and optional_local_script.read_bytes() != executed:
        raise RuntimeError("Supplied --repair-script is not byte-identical to the verified executed script")
    return executed


def run_repair(repair_zip: Path, v1_output: Path, discovery: Path,
               fixtures: Path, work: Path, partial: bool, repair_script: Path | None = None):
    project = work / "project"
    (project / "nba_game_covariates_v1").mkdir(parents=True)
    (project / "nba_game_covariates_v1" / "game_level_covariates.csv").symlink_to(fixtures)
    (project / "v1").mkdir()
    (project / "v1" / "raw_json").symlink_to(v1_output / "raw_json")
    output = project / "v2_output"
    output.mkdir()
    (output / "raw_json_discovery").symlink_to(discovery)
    code = work / "source"
    code.mkdir()
    executed_bytes = historically_executed_repair_source(repair_zip, repair_script)
    (code / "repair_boxscore_rosters.py").write_bytes(executed_bytes)
    command = [
        sys.executable, "-I", str(code / "repair_boxscore_rosters.py"),
        "--project-root", str(project),
        "--v1-output", "v1", "--output", "v2_output",
        "--no-download",
    ]
    result = subprocess.run(command, cwd=work, capture_output=True, text=True)
    (work / "repair_stdout.txt").write_text(result.stdout)
    (work / "repair_stderr.txt").write_text(result.stderr)
    # The archived program intentionally exits 2 if any fixture is missing.
    if result.returncode not in ((0, 2) if partial else (0,)):
        raise RuntimeError(
            f"Original repair script exited {result.returncode} unexpectedly:\n"
            f"{result.stderr[-3000:]}\n{result.stdout[-3000:]}")
    qa = output / "qa_summary.json"
    if not qa.exists():
        raise RuntimeError("Original repair script did not create qa_summary.json")
    return output, sha256(code / "repair_boxscore_rosters.py"), json.loads(qa.read_text()), result.returncode


def unique_key_table(frame: pd.DataFrame, key: list[str], label: str):
    if not set(key).issubset(frame.columns):
        raise ValueError(f"{label} missing key columns {sorted(set(key) - set(frame.columns))}")
    if frame[key].eq("").any().any():
        raise ValueError(f"{label} contains blank key values")
    if frame.duplicated(key).any():
        examples = frame.loc[frame.duplicated(key, keep=False), key].head(5).to_dict("records")
        raise ValueError(f"{label} contains duplicate keys, e.g. {examples}")


def compare_with_archive(output: Path, reference_zip: Path, partial: bool):
    report = {}
    with zipfile.ZipFile(reference_zip) as archive:
        for basename, keys in OUTPUTS.items():
            member = single_archive_member(archive, basename)
            original = pd.read_csv(archive.open(member), dtype=str, keep_default_na=False)
            new = pd.read_csv(output / basename, dtype=str, keep_default_na=False)
            if list(original.columns) != list(new.columns):
                raise ValueError(f"{basename}: archive and rebuilt columns differ")
            if partial:
                original = original[original.game_id.isin(set(new.game_id))]
            unique_key_table(original, keys, f"{basename} archived")
            unique_key_table(new, keys, f"{basename} rebuilt")
            common_columns = [col for col in new.columns if col != "raw_json_path"]
            merged = original[common_columns].merge(
                new[common_columns], on=keys, how="outer",
                validate="one_to_one", suffixes=("_archive", "_rebuilt"), indicator=True)
            both = merged[merged["_merge"] == "both"]
            differences = {
                col: int(both[f"{col}_archive"].ne(both[f"{col}_rebuilt"]).sum())
                for col in common_columns if col not in keys
            }
            report[basename] = {
                "reference_rows": len(original), "rebuilt_rows": len(new),
                "only_reference": int(merged["_merge"].eq("left_only").sum()),
                "only_rebuilt": int(merged["_merge"].eq("right_only").sum()),
                "differing_cells": {k: v for k, v in differences.items() if v},
            }
    return report


def iso_minutes(value):
    match = re.fullmatch(r"PT(\d+)M([\d.]+)S", str(value))
    return int(match[1]) + float(match[2]) / 60 if match else np.nan


def numeric_disagreement(left: pd.Series, right: pd.Series, absolute_tolerance=1e-9):
    """Unknown/invalid numeric text is never silently treated as equal to missing."""
    l, r = pd.to_numeric(left, errors="coerce"), pd.to_numeric(right, errors="coerce")
    invalid = (left.ne("") & l.isna()) | (right.ne("") & r.isna())
    missing_disagreement = l.isna() ^ r.isna()
    different = (~l.isna() & ~r.isna() & (l - r).abs().gt(absolute_tolerance))
    return invalid | missing_disagreement | different


def compare_with_base(output: Path, base_panel: Path):
    roster = pd.read_csv(output / "game_roster_players.csv", dtype=str, keep_default_na=False)
    base = pd.read_csv(base_panel, dtype=str, keep_default_na=False, low_memory=False)
    if "from_boxscore_roster" not in base:
        raise ValueError("Canonical base panel lacks from_boxscore_roster")
    base = base[base.from_boxscore_roster.str.lower().isin(("true", "1", "1.0"))]
    base = base[base.game_id.isin(set(roster.game_id))]
    keys = ["game_id", "team", "nba_player_id"]
    unique_key_table(roster, keys, "rebuilt roster")
    unique_key_table(base, keys, "base panel boxscore rows")
    merged = roster.merge(base, on=keys, how="outer", validate="one_to_one",
                          suffixes=("_v2", "_base"), indicator=True)
    both = merged[merged["_merge"] == "both"]
    missing = [field for field in TEXT_FIELDS
               if f"{field}_v2" not in both or f"{field}_base" not in both]
    if missing:
        raise ValueError(f"Missing comparable base-panel columns: {missing}")
    differences = {
        field: int(both[f"{field}_v2"].ne(both[f"{field}_base"]).sum())
        for field in TEXT_FIELDS
    }
    differences["nba_game_id"] = int(numeric_disagreement(
        both["nba_game_id_v2"], both["nba_game_id_base"]).sum())
    differences["points"] = int(numeric_disagreement(
        both["points_v2"], both["points_base"]).sum())
    differences["played_vs_played_bool"] = int(both["played"].str.lower().ne(
        both["played_bool"].str.lower()).sum())
    minutes = both["minutes_iso"].map(iso_minutes)
    numeric_minutes = pd.to_numeric(both["minutes_played"], errors="coerce")
    malformed_iso = both["minutes_iso"].ne("") & minutes.isna()
    malformed_base = both["minutes_played"].ne("") & numeric_minutes.isna()
    minutes_difference = ((minutes.isna() ^ numeric_minutes.isna()) |
                          (minutes.notna() & numeric_minutes.notna() &
                           (minutes - numeric_minutes).abs().gt(1e-9)) |
                          malformed_iso | malformed_base)
    differences["minutes_vs_minutes_played"] = int(minutes_difference.sum())
    return {
        "rebuilt_rows": len(roster), "base_boxscore_rows": len(base),
        "only_rebuilt": int(merged["_merge"].eq("left_only").sum()),
        "only_base": int(merged["_merge"].eq("right_only").sum()),
        "differing_fields": {k: v for k, v in differences.items() if v},
    }


def cache_stats(manifest: pd.DataFrame, partial: bool):
    source = manifest[manifest.source == "v1_raw_json"]
    unique_game_ids = int(manifest.payload_game_id.nunique())
    result = {
        "json_files": len(manifest),
        "v1_files": len(source),
        "discovery_files": int(manifest.source.eq("v2_discovery").sum()),
        "distinct_payload_game_ids": unique_game_ids,
        "name_payload_mismatches": int((~manifest.name_matches_payload).sum()),
        "season_payload_mismatches": int((~manifest.season_matches_payload).sum()),
        "v1_files_missing_from_log": int(source.logged_bytes.isna().sum()),
        "v1_size_differs_from_log": int((
            source.logged_bytes.notna() &
            source.bytes.ne(source.logged_bytes)).sum()),
        "logged_endpoints": source.logged_endpoint.value_counts(dropna=False).to_dict(),
    }
    if (result["name_payload_mismatches"] or result["season_payload_mismatches"]
            or result["v1_size_differs_from_log"]
            or unique_game_ids != len(manifest)):
        raise RuntimeError(f"Raw JSON cache mismatches or duplicate IDs: {result}")
    if not partial and len(manifest) != 7230:
        raise RuntimeError(f"Expected exactly 7,230 official raw game JSONs, found {len(manifest)}")
    return result


def check_repair_qa(qa: dict, cache: dict, partial: bool, exit_code: int):
    expected = cache["distinct_payload_game_ids"]
    if int(qa.get("valid_unique_official_boxscores_available", -1)) != expected:
        raise RuntimeError(f"Original repair scanned wrong number of JSONs: {qa}")
    if int(qa.get("matched_fixture_games", -1)) != expected:
        raise RuntimeError(f"Original repair did not match every supplied JSON to a fixture: {qa}")
    if int(qa.get("unused_official_boxscores", -1)) != 0:
        raise RuntimeError(f"Original repair left unmatched extra official JSONs: {qa}")
    if int(qa.get("player_rows", -1)) <= 0 or int(qa.get("team_game_rows", -1)) != expected * 2:
        raise RuntimeError(f"Original repair has invalid roster/team totals: {qa}")
    if not partial and (exit_code != 0 or not qa.get("complete")
                        or int(qa.get("requested_fixture_games", -1)) != 7230):
        raise RuntimeError(f"Original repair did not complete all 7,230 fixtures: {qa}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-output", type=Path, required=True,
                        help="nba_boxscore_roster_frame_v1_output (raw_json/ and download_log.csv)")
    parser.add_argument("--discovery", type=Path, required=True,
                        help="nba_boxscore_roster_frame_v2_output/raw_json_discovery")
    parser.add_argument("--fixtures", type=Path, required=True,
                        help="nba_game_covariates_v1/game_level_covariates.csv")
    parser.add_argument("--repair-zip", type=Path, required=True)
    parser.add_argument("--repair-script", type=Path,
                        help="Optional original Mac script; must match the byte-verified one-line historical variant")
    parser.add_argument("--reference-zip", type=Path, required=True)
    parser.add_argument("--base-panel", type=Path,
                        default=REPO / "data_final/player_game_panel_analysis_ready.csv.gz")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-partial", action="store_true",
                        help="sample only; archive/base comparisons are restricted to supplied game IDs")
    args = parser.parse_args()
    v1, discovery, out_dir = (
        args.v1_output.resolve(), args.discovery.resolve(), args.output.resolve())
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = hash_cache(
        {"v1_raw_json": v1 / "raw_json", "v2_discovery": discovery},
        v1 / "download_log.csv")
    manifest.to_csv(out_dir / "boxscore_json_sha256_manifest.csv", index=False)
    cache = cache_stats(manifest, args.allow_partial)
    with tempfile.TemporaryDirectory(prefix="nba_boxscore_verify_") as scratch:
        scratch_dir = Path(scratch)
        rebuilt, script_sha, qa, code = run_repair(
            args.repair_zip.resolve(), v1, discovery, args.fixtures.resolve(),
            scratch_dir, args.allow_partial,
            args.repair_script.resolve() if args.repair_script else None)
        check_repair_qa(qa, cache, args.allow_partial, code)
        archive = compare_with_archive(rebuilt, args.reference_zip.resolve(), args.allow_partial)
        base = compare_with_base(rebuilt, args.base_panel.resolve())
        for basename in OUTPUTS:
            (out_dir / basename).write_bytes((rebuilt / basename).read_bytes())
        (out_dir / "repair_stdout.txt").write_text((scratch_dir / "repair_stdout.txt").read_text())
        (out_dir / "repair_stderr.txt").write_text((scratch_dir / "repair_stderr.txt").read_text())
    match = (
        all(not row["only_reference"] and not row["only_rebuilt"] and not row["differing_cells"]
            for row in archive.values())
        and not base["only_rebuilt"] and not base["only_base"] and not base["differing_fields"]
    )
    report = {
        "scope": "sample" if args.allow_partial else "full 7,230-game cache",
        "matched": match,
        "cache": cache,
        "archived_repair_script_sha256": REPAIR_ARCHIVED_SHA256,
        "original_repair_script_sha256": script_sha,
        "repair_source_mode": "SHA-256-verified archived source plus historical one-line QA serialization fix",
        "reference_zip_sha256": sha256(args.reference_zip),
        "fixtures_sha256": sha256(args.fixtures),
        "rebuilt_qa_summary": qa,
        "vs_archived_v2_output": archive,
        "vs_base_panel_boxscore_rows": base,
        "verification_note": "New SHA-256 manifest records present bytes. It cannot certify the original download hashes, which were not preserved.",
    }
    (out_dir / "boxscore_cache_verification.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not match:
        raise SystemExit("Rebuilt V2 roster differs from archived reference or canonical boxscore base")


if __name__ == "__main__":
    main()
