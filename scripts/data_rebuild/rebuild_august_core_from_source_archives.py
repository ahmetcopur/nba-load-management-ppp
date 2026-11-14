#!/usr/bin/env python3
"""Rebuild the August core from verified original ZIPs, then source-correct Toronto.

Baseline executes the untouched historical finalizer and MUST reproduce its
archived uncompressed CSV SHA. The variant corrects only two documented game
dates and the four impacted source match-number report associations before
executing the SAME finalizer. Frozen game_id keys remain unchanged and retain
their original (wrong) encoded tip dates solely for row alignment.

Does not claim the reviewed taxonomy/award/Cup or August models are rebuilt.
Never changes original archives, published panels or source files.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

import pandas as pd

SOURCE_ZIPS = {
    "core": ("nba_player_game_at_risk_core_v1.zip",
             "a0f82ebcf6117554a4ce1064ab79db9cf93acc5a53fa25000343810843e659f6"),
    "covariates": ("nba_game_covariates_v1.zip",
             "4351756b74446577dabc8418b539c95dfb6e0ae6e3d8766bbee1c528d709c224"),
    "roster": ("nba_boxscore_roster_frame_v2_output_upload.zip",
             "45eeade023037506d1b07ebc601c273ec442f6620adc3ab836a3d40b8774f561"),
}
FINALIZER_SHA = "a0271f01f551dbbe1abedfac7ca8fefb9c865cd9b58a33185a3b7cbc991f8bfc"
BASELINE_UNCOMPRESSED_SHA = "253bf017095a8be45f4c7bb4a0abcc9b942a8db6311f91131c9fd12c7ab46de3"
OLD_CHI = "2021-22|20220202T0030Z|Chicago Bulls@Toronto Raptors"
OLD_MIA = "2021-22|20220204T0030Z|Miami Heat@Toronto Raptors"
SOURCE_TO_FROZEN = {
    46: "2021-22|20211025T2330Z|Chicago Bulls@Toronto Raptors",
    430: OLD_MIA,
    784: OLD_CHI,
    1172: "2021-22|20220403T2300Z|Miami Heat@Toronto Raptors",
}
CORRECT_TIPS = {OLD_CHI: "2022-02-04T00:30:00Z", OLD_MIA: "2022-02-02T00:30:00Z"}
ELO_COLUMNS = [
    "home_elo_pre", "away_elo_pre", "home_rank_pre", "away_rank_pre",
    "elo_home_court_points", "elo_home_advantage_signed",
    "home_win_probability_elo", "elo_mov_multiplier", "elo_update_home",
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def decompressed_digest(path: Path) -> str:
    h = hashlib.sha256()
    with gzip.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def unpack(archives: Path, root: Path):
    members = {
        "core": [
            "selected_report_player_rows.csv", "selected_report_rows_all.csv",
            "canonical_game_snapshot_map.csv", "team_game_report_status.csv",
            "finalize_player_game_panel.py",
        ],
        "covariates": ["game_level_covariates.csv", "team_game_covariates.csv",
                       "build_game_covariates.py"],
        "roster": ["game_roster_players.csv"],
    }
    for key, (name, checksum) in SOURCE_ZIPS.items():
        path = archives / name
        if digest(path) != checksum:
            raise ValueError(f"Unexpected source archive SHA-256: {path}")
        with ZipFile(path) as archive:
            for basename in members[key]:
                found = [n for n in archive.namelist() if n.endswith("/" + basename)]
                if len(found) != 1:
                    raise ValueError(f"{name}: ambiguous source member {basename}")
                dest = root / found[0]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.read(found[0]))
    source = root / "nba_player_game_at_risk_core_v1/finalize_player_game_panel.py"
    if digest(source) != FINALIZER_SHA:
        raise ValueError("Historical August executable SHA-256 differs")
    alias = root / "boxscore_v2_upload_inspect/nba_boxscore_roster_frame_v2_output"
    alias.mkdir(parents=True, exist_ok=True)
    (alias / "game_roster_players.csv").symlink_to(
        root / "nba_boxscore_roster_frame_v2_output/game_roster_players.csv")
    return source


def run_original_finalizer(root: Path):
    src = root / "nba_player_game_at_risk_core_v1/finalize_player_game_panel.py"
    text = src.read_text()
    if text.count('ROOT=Path("/mnt/data")') != 1:
        raise RuntimeError("Original executable path marker changed")
    executable = root / "execute_original_august_finalizer.py"
    executable.write_text(text.replace(
        'ROOT=Path("/mnt/data")', "ROOT=Path(" + repr(str(root)) + ")"))
    envroot = root / "nba_player_game_at_risk_core_v1"
    with (root / "finalizer_stdout.txt").open("w") as out, \
         (root / "finalizer_stderr.txt").open("w") as err:
        subprocess.run([sys.executable, str(executable)],
                       stdout=out, stderr=err, cwd=root, check=True, timeout=1500)
    qa = json.loads((envroot / "qa_summary.json").read_text())
    if (qa.get("missing_game_covariate_rows") != 0
            or qa.get("duplicate_player_game_keys") != 0
            or qa.get("unmatched_report_player_rows") != 0):
        raise RuntimeError(f"Original August finalizer QA failed: {qa}")
    return qa


def correct_sources(root: Path):
    gp = root / "nba_game_covariates_v1/game_level_covariates.csv"
    games = pd.read_csv(gp, low_memory=False)
    games["tip_utc"] = pd.to_datetime(games.tip_utc, utc=True)
    for game, true_tip in CORRECT_TIPS.items():
        mask = games.game_id.eq(game)
        if mask.sum() != 1:
            raise RuntimeError(f"Expected exactly one source game: {game}")
        stamp = pd.Timestamp(true_tip)
        games.loc[mask, "tip_utc"] = stamp
        games.loc[mask, "game_date_et"] = (
            stamp.tz_convert("America/New_York").date().isoformat())
        games.loc[mask, "source_match_number"] = 784 if game == OLD_CHI else 430
    if games.duplicated(["season", "source_match_number"]).any():
        raise RuntimeError("Corrected source matches are not unique")
    games.to_csv(gp, index=False)

    builder = root / "nba_game_covariates_v1/build_game_covariates.py"
    spec = importlib.util.spec_from_file_location("historical_august_game_covariates", builder)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    games["neutral_site"] = games.neutral_site.astype(bool)
    updated = module.build_team_games(module.attach_elo(games.drop(columns=ELO_COLUMNS)))
    if len(updated) != 14460 or updated.duplicated(["game_id", "team"]).any():
        raise RuntimeError("Corrected game covariate frame invalid")
    duplication = updated.groupby(["season", "team", "game_date_et"]).game_id.nunique()
    if duplication.gt(1).any():
        raise RuntimeError(f"Duplicate team-date persists: {duplication[duplication.gt(1)].to_dict()}")
    updated.to_csv(root / "nba_game_covariates_v1/team_game_covariates.csv", index=False)

    rp = root / "nba_boxscore_roster_frame_v2_output/game_roster_players.csv"
    roster = pd.read_csv(rp, low_memory=False)
    for game, true_tip in CORRECT_TIPS.items():
        mask = roster.game_id.eq(game)
        if mask.sum() != 33:
            raise RuntimeError(f"Expected exactly 33 original roster rows: {game}")
        stamp = pd.Timestamp(true_tip)
        roster.loc[mask, "tip_utc"] = str(stamp)
        roster.loc[mask, "game_date_et"] = stamp.tz_convert(
            "America/New_York").date().isoformat()
        roster.loc[mask, "source_match_number"] = 784 if game == OLD_CHI else 430
    roster.to_csv(rp, index=False)

    core = root / "nba_player_game_at_risk_core_v1"
    for filename, expected in [
        ("selected_report_player_rows.csv", {46: 7, 430: 8, 784: 9, 1172: 10}),
        ("selected_report_rows_all.csv", {46: 7, 430: 10, 784: 9, 1172: 10}),
    ]:
        path = core / filename
        df = pd.read_csv(path, low_memory=False)
        for match, target in SOURCE_TO_FROZEN.items():
            mask = df.season.eq("2021-22") & df.source_match_number.eq(match)
            if mask.sum() != expected[match]:
                raise RuntimeError(f"{filename} unexpected source match {match}")
            df.loc[mask, "game_id"] = target
        if filename.startswith("selected_report_player") and df.duplicated(
                ["game_id", "team_norm", "nba_player_id"]).any():
            raise RuntimeError("Corrected selected report player duplicate IDs")
        df.to_csv(path, index=False)

    cp = core / "canonical_game_snapshot_map.csv"
    selectors = pd.read_csv(cp)
    for match in (430, 784):
        mask = selectors.season.eq("2021-22") & selectors.source_match_number.eq(match)
        if mask.sum() != 1:
            raise RuntimeError(f"Canonical selector missing source match {match}")
        selectors.loc[mask, "game_id"] = SOURCE_TO_FROZEN[match]
        stamp = pd.Timestamp(CORRECT_TIPS[SOURCE_TO_FROZEN[match]])
        selectors.loc[mask, "tip_utc"] = str(stamp)
        selectors.loc[mask, "game_date_et"] = stamp.tz_convert(
            "America/New_York").date().isoformat()
    selectors.to_csv(cp, index=False)

    sp = core / "team_game_report_status.csv"
    statuses = pd.read_csv(sp)
    chi = statuses.game_id.eq(OLD_CHI) & statuses.season.eq("2021-22")
    mia = statuses.game_id.eq(OLD_MIA) & statuses.season.eq("2021-22")
    if chi.sum() != 2 or mia.sum() != 2:
        raise RuntimeError("Unexpected original team status groups")
    statuses.loc[chi, "game_id"] = OLD_MIA
    statuses.loc[mia, "game_id"] = OLD_CHI
    statuses.loc[chi & statuses.team_role.eq("away"), ["team", "team_norm"]] = [
        "Miami Heat", "miami heat"]
    statuses.loc[mia & statuses.team_role.eq("away"), ["team", "team_norm"]] = [
        "Chicago Bulls", "chicago bulls"]
    if statuses.duplicated(["season", "game_id", "team_norm"]).any():
        raise RuntimeError("Corrected August team-status keys duplicated")
    statuses.to_csv(sp, index=False)


def compare_core(oldpath: Path, newpath: Path):
    columns = ["game_id", "team", "nba_player_id", "nba_player_name",
               "from_boxscore_roster", "absence_now", "absence_onset",
               "at_risk_for_new_onset", "designation_status"]
    old = pd.read_csv(oldpath, usecols=columns, dtype=str, keep_default_na=False)
    new = pd.read_csv(newpath, usecols=columns, dtype=str, keep_default_na=False)
    key = ["game_id", "team", "nba_player_id"]
    joint = old.merge(new, on=key, how="outer", validate="one_to_one",
                      suffixes=("_frozen", "_corrected"), indicator=True)
    removed = joint[joint["_merge"].eq("left_only")]
    added = joint[joint["_merge"].eq("right_only")]
    if len(old) != 248730 or len(new) != 248728 or len(removed) != 2 or len(added):
        raise RuntimeError("Unexpected core row/key changes")
    removed_names = set(removed.nba_player_name_frozen)
    if removed_names != {"Devon Dotson", "Javonte Smart"}:
        raise RuntimeError(f"Unexpected removed report-only players: {removed_names}")
    changed = {}
    for col in ("absence_now", "absence_onset", "at_risk_for_new_onset",
                "designation_status"):
        a, b = joint[col + "_frozen"], joint[col + "_corrected"]
        changed[col] = int((joint["_merge"].eq("both") & a.ne(b)).sum())
    if changed != {"absence_now": 2, "absence_onset": 3,
                   "at_risk_for_new_onset": 12, "designation_status": 32}:
        raise RuntimeError(f"Unexpected corrected August core row changes: {changed}")
    return {"removed_names": sorted(removed_names), "changed_fields": changed}



def inject_raw_pdf_rebuilt_selected_players(reference_path: Path,
                                            generated_path: Path, *,
                                            expected_rows: int = 73438,
                                            expected_columns: int = 33) -> dict:
    """Use exact source-PDF-derived player rows as inputs to the original finalizer.

    The raw original-PDF reconstruction must independently have been accepted
    by the six-season identity/core runner. Require every key and all 33
    report-player fields to agree with the original historical source archive
    before substitution. This cannot repair or re-adjudicate external Cup,
    awards, TV or manually reviewed injury labels.
    """
    if reference_path.is_symlink() or generated_path.is_symlink():
        raise RuntimeError("Refusing source-player CSV symlinks")
    if not generated_path.is_file() or not reference_path.is_file():
        raise FileNotFoundError("Original frozen and PDF-rebuilt source player rows required")
    original = pd.read_csv(reference_path, dtype=str, keep_default_na=False,
                           low_memory=False)
    rebuilt = pd.read_csv(generated_path, dtype=str, keep_default_na=False,
                          low_memory=False)
    keys = ["game_id", "team_norm", "nba_player_id"]
    if (set(original.columns) != set(rebuilt.columns)
            or len(original) != len(rebuilt)
            or original.duplicated(keys).any()
            or rebuilt.duplicated(keys).any()):
        raise ValueError("PDF-rebuilt player source schema, row count or keys differ")
    orig = original.set_index(keys, drop=False)
    fresh = rebuilt.set_index(keys, drop=False)
    if not orig.index.is_unique or not fresh.index.is_unique:
        raise ValueError("Duplicate PDF-derived source player keys")
    if set(orig.index) != set(fresh.index):
        raise ValueError("PDF-rebuilt report-player identities do not match original")
    fresh = fresh.loc[orig.index, original.columns]
    mismatches = {}
    for name in original.columns:
        old = orig[name].fillna("NULL").astype(str).str.strip()
        new = fresh[name].fillna("NULL").astype(str).str.strip()
        differences = int(old.ne(new).sum())
        if differences:
            mismatches[name] = differences
    if mismatches:
        raise ValueError(f"Source-PDF-derived report-player fields differ: {mismatches}")
    if len(fresh) != expected_rows or len(fresh.columns) != expected_columns:
        raise ValueError("Historical report-player source cardinality changed")
    # Keep original canonical row ordering, but write the newly regenerated
    # values themselves. The downstream unchanged original finalizer must
    # reproduce the complete historical core SHA before any chronology repair.
    target = reference_path.with_name("source_pdf_rebuilt_player_rows.tmp.csv")
    if target.exists():
        raise FileExistsError("Temporary source handoff already exists")
    fresh.to_csv(target, index=False)
    target.replace(reference_path)
    return {
        "source": "Original NBA injury PDFs -> player-ID resolution -> selected report players",
        "original_rows_and_fields": [len(fresh), len(fresh.columns)],
        "all_field_values_equal_to_archived_historical_reference": True,
        "generated_source_csv_sha256": digest(generated_path),
        "source_rows_injected_into_original_finalizer_and_corrected_copy": True,
    }


def inject_verified_raw_boxscore_roster(reference_path: Path, generated_path: Path) -> dict:
    """Feed the independently rebuilt NBA JSON roster to the original finalizer.

    Require exact identity, schema and all non-path cells before substitution.
    Machine-specific source paths must resolve to the same season/game JSON.
    """
    if any(p.is_symlink() or not p.is_file() for p in (reference_path, generated_path)):
        raise FileNotFoundError("Missing or symlinked original/rebuilt boxscore roster")
    original = pd.read_csv(reference_path, dtype=str, keep_default_na=False, low_memory=False)
    rebuilt = pd.read_csv(generated_path, dtype=str, keep_default_na=False, low_memory=False)
    keys = ["game_id", "team", "nba_player_id"]
    if (set(original.columns) != set(rebuilt.columns)
            or not {*keys, "nba_game_id", "raw_json_path"} <= set(original.columns)):
        raise ValueError("Rebuilt boxscore roster schema differs")
    if original.duplicated(keys).any() or rebuilt.duplicated(keys).any():
        raise ValueError("Duplicate original/rebuilt boxscore roster identity")
    left = original.set_index(keys)
    right = rebuilt.set_index(keys)
    if len(left) != len(right) or set(left.index) != set(right.index):
        raise ValueError("Rebuilt boxscore roster game/player identities differ")
    right = right.loc[left.index, left.columns]
    compared = left.columns.drop("raw_json_path")
    if not left[compared].equals(right[compared]):
        changed = left[compared].ne(right[compared]).sum()
        raise ValueError("Rebuilt boxscore roster source fields differ: "
                         + str(changed[changed.gt(0)].to_dict()))
    import re
    def source_id(value: str, game_id: str) -> tuple[str, str]:
        match = re.search(r"(?:^|/)(20\d{2}_\d{2})/boxscore_(002\d{7})\.json$",
                          value.replace("\\", "/"))
        season = f"{2000 + int(game_id[3:5])}_{(int(game_id[3:5]) + 1) % 100:02d}"
        if not match or match.groups() != (season, game_id):
            raise ValueError("Boxscore raw_json_path does not identify the row's season/game JSON")
        return match.groups()
    # game_id is the study's canonical fixture key; nba_game_id is the
    # official 002... identifier embedded in the original JSON filename.
    for name, frame in (("archived", left), ("rebuilt", right)):
        for path, game_id in zip(frame["raw_json_path"], frame["nba_game_id"]):
            source_id(path, game_id)
    path_differences = int(left["raw_json_path"].ne(right["raw_json_path"]).sum())
    temporary = reference_path.with_name("verified_raw_json_roster.tmp.csv")
    if temporary.exists():
        raise FileExistsError(temporary)
    # Preserve the original environment's provenance path. All data fields
    # from the independently rebuilt JSON-derived roster are written.
    right["raw_json_path"] = left["raw_json_path"]
    right.reset_index()[list(original.columns)].to_csv(temporary, index=False)
    temporary.replace(reference_path)
    return {"original_nba_json_roster_fed_to_original_august_finalizer": True,
            "rows": len(right), "columns": len(original.columns),
            "generated_roster_sha256": digest(generated_path),
            "exact_non_path_cell_equality_to_archived_roster": True,
            "raw_json_path_values_differing_by_environment": path_differences,
            "both_source_paths_identify_same_season_and_game_json": True,
            "historical_raw_json_path_preserved_in_private_finalizer_input": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archives", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--rebuilt-original-selected-players", type=Path,
                        help="Optional six-season original-PDF-derived selected_report_player_rows.csv; exact 33-field equality required before injecting into both finalizer passes")
    parser.add_argument("--rebuilt-original-boxscore-roster", type=Path,
                        help="Optional raw-NBA-JSON-derived verified game_roster_players.csv")
    args = parser.parse_args()
    output = args.output_root.resolve()
    if output.exists():
        raise FileExistsError("Use a fresh output directory; never overwrite original replay")
    output.mkdir(parents=True)
    baseline = output / "baseline"
    baseline.mkdir()
    unpack(args.archives.resolve(), baseline)
    raw_pdf_handoff = (
        inject_raw_pdf_rebuilt_selected_players(
            baseline / "nba_player_game_at_risk_core_v1/selected_report_player_rows.csv",
            args.rebuilt_original_selected_players.resolve())
        if args.rebuilt_original_selected_players else None
    )
    raw_boxscore_handoff = (
        inject_verified_raw_boxscore_roster(
            baseline / "nba_boxscore_roster_frame_v2_output/game_roster_players.csv",
            args.rebuilt_original_boxscore_roster.resolve())
        if args.rebuilt_original_boxscore_roster else None
    )
    baseline_qa = run_original_finalizer(baseline)
    historical = baseline / "nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz"
    if decompressed_digest(historical) != BASELINE_UNCOMPRESSED_SHA:
        raise RuntimeError("Historical August core CSV did not reproduce original byte-for-byte")

    variant = output / "corrected_source"
    shutil.copytree(baseline, variant, symlinks=False, ignore=shutil.ignore_patterns(
        "player_game_panel_core.csv.gz", "player_game_panel_model_at_risk.csv.gz",
        "absence_spells_provisional.csv.gz", "taxonomy_validation_sample_300.csv",
        "qa_summary.json", "summary_by_season.csv", "finalizer_stdout.txt",
        "finalizer_stderr.txt", "execute_original_august_finalizer.py",
    ))
    alias = variant / "boxscore_v2_upload_inspect/nba_boxscore_roster_frame_v2_output/game_roster_players.csv"
    # copytree dereferences the old *internal* link; restore the new variant's link.
    alias.unlink()
    alias.symlink_to(variant / "nba_boxscore_roster_frame_v2_output/game_roster_players.csv")
    correct_sources(variant)
    variant_qa = run_original_finalizer(variant)
    expected = {"final_player_game_rows": 248728, "at_risk_rows": 180831,
                "absence_onsets": 12707, "report_only_roster_additions": 157}
    for key, value in expected.items():
        if variant_qa.get(key) != value:
            raise RuntimeError(f"Corrected August core {key}: {variant_qa.get(key)} != {value}")
    corrected = variant / "nba_player_game_at_risk_core_v1/player_game_panel_core.csv.gz"
    changes = compare_core(historical, corrected)
    report = {
        "scope": "Original August core finalizer, source-corrected two Toronto physical games; review-star/Cup and taxonomy downstream not yet rebuilt",
        "source_zip_sha256": {key: value[1] for key, value in SOURCE_ZIPS.items()},
        "raw_original_pdf_selected_player_rows_handoff": raw_pdf_handoff,
        "raw_original_boxscore_roster_handoff": raw_boxscore_handoff,
        "historical_finalizer_sha256": FINALIZER_SHA,
        "frozen_original_csv_reproduced_exactly_uncompressed_sha256": BASELINE_UNCOMPRESSED_SHA,
        "baseline_qa": baseline_qa,
        "corrected_qa": variant_qa,
        "changed_core": changes,
        "official_true_tip_utc": CORRECT_TIPS,
        "source_match_to_retained_frozen_key": SOURCE_TO_FROZEN,
        "unresolved_key_warning": "Two retained frozen game_id strings still encode the original incorrect date, for stable key comparisons. source_match_number and actual tip/date have been corrected.",
        "limitations": "Does NOT independently rebuild award/Cup flags, reviewed taxonomy or full August regressions.",
    }
    (output / "august_core_source_correction_report.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("baseline_qa", "corrected_qa")}, indent=2))


if __name__ == "__main__":
    main()
