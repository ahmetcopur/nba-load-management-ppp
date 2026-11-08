#!/usr/bin/env python3
"""Isolated sensitivity for two confirmed 2021–22 fixture-date swaps.

Replays the *original* 2026 game-covariate functions from the archived ZIP,
first proving exact scientific baseline equivalence for all team-game columns.
Changes only the two verified tip/date input cells in a copy, then recomputes
chronological Elo, team schedule load, rest, travel and opponent covariates.

Does NOT mutate the original archive, frozen player-game panel, or models.
No claim about PPP coefficients is made until corrected covariates are
propagated to the frozen analysis sample and the original models are rerun.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EXPECTED_ZIP_SHA = "4351756b74446577dabc8418b539c95dfb6e0ae6e3d8766bbee1c528d709c224"
EXPECTED_CODE_SHA = "268140c52c68a1f19ed1ab756f772519c460dc552938281e6ee62a1cbe087862"
ZIP_ROOT = "nba_game_covariates_v1/"
CORRECTED_TIP_UTC = {
    "2021-22|20220202T0030Z|Chicago Bulls@Toronto Raptors": "2022-02-04T00:30:00Z",
    "2021-22|20220204T0030Z|Miami Heat@Toronto Raptors": "2022-02-02T00:30:00Z",
}
ELO_COLUMNS = [
    "home_elo_pre", "away_elo_pre", "home_rank_pre", "away_rank_pre",
    "elo_home_court_points", "elo_home_advantage_signed",
    "home_win_probability_elo", "elo_mov_multiplier", "elo_update_home",
]
KEY = ["game_id", "team"]


def file_sha(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_tables(zip_path: Path):
    with zipfile.ZipFile(zip_path) as z:
        code = z.read(ZIP_ROOT + "build_game_covariates.py")
        games = pd.read_csv(z.open(ZIP_ROOT + "game_level_covariates.csv"),
                            low_memory=False)
        teams = pd.read_csv(z.open(ZIP_ROOT + "team_game_covariates.csv"),
                            low_memory=False)
    return code, games, teams


def replay(code: bytes, games: pd.DataFrame, temp: Path):
    script = temp / "original_build_game_covariates.py"
    script.write_bytes(code)
    spec = importlib.util.spec_from_file_location("original_game_covariates", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    master = games.drop(columns=ELO_COLUMNS)
    with_elo = module.attach_elo(master)
    return module.build_team_games(with_elo)


def compare_rows(left: pd.DataFrame, right: pd.DataFrame, *, tolerance=1e-8):
    if set(left.columns) != set(right.columns):
        raise ValueError(f"Different covariate columns: {sorted(set(left.columns)^set(right.columns))}")
    if left.duplicated(KEY).any() or right.duplicated(KEY).any():
        raise ValueError("Duplicate team-game keys in one side of comparison")
    frame = left.merge(right, on=KEY, suffixes=["_old", "_new"],
                       how="outer", validate="one_to_one", indicator=True)
    if len(frame) != len(left) or len(frame) != len(right) or not frame["_merge"].eq("both").all():
        raise ValueError("Different sets of team-game keys")
    counts, magnitudes, examples = {}, {}, {}
    for name in left.columns:
        if name in KEY:
            continue
        old, new = frame[name+"_old"], frame[name+"_new"]
        if name == "previous_tip_utc":
            a = pd.to_datetime(old, utc=True, errors="coerce")
            b = pd.to_datetime(new, utc=True, errors="coerce")
            mask = a.isna().ne(b.isna()) | (
                a.notna() & b.notna() & (a-b).abs().gt(pd.Timedelta("1ms"))
            )
        elif pd.api.types.is_numeric_dtype(old) and pd.api.types.is_numeric_dtype(new):
            a, b = old.astype(float), new.astype(float)
            diff = (a-b).abs()
            mask = diff.fillna(0).gt(tolerance) | old.isna().ne(new.isna())
            magnitudes[name] = {
                "max_absolute_difference": float(diff.max()) if diff.notna().any() else None,
                "changed_greater_than_0_01": int(diff.gt(0.01).sum()),
                "changed_greater_than_0_1": int(diff.gt(0.1).sum()),
                "changed_greater_than_1": int(diff.gt(1).sum()),
                "changed_greater_than_5": int(diff.gt(5).sum()),
            }
        else:
            mask = old.fillna("").astype(str).ne(new.fillna("").astype(str))
        amount = int(mask.sum())
        if amount:
            counts[name] = amount
            examples[name] = frame.loc[mask, KEY].head(10).to_dict("records")
    return counts, magnitudes, examples


def run(archive_path: Path):
    if file_sha(archive_path) != EXPECTED_ZIP_SHA:
        raise ValueError("Original game-covariate ZIP SHA-256 changed; inspect the historical source")
    code, games, reference = source_tables(archive_path)
    if hashlib.sha256(code).hexdigest() != EXPECTED_CODE_SHA:
        raise ValueError("Original covariate-building source script SHA-256 changed")
    games["tip_utc"] = pd.to_datetime(games["tip_utc"], utc=True)
    games["neutral_site"] = games["neutral_site"].astype(bool)
    with tempfile.TemporaryDirectory(prefix="nba_date_swap_covariates_") as folder:
        temp = Path(folder)
        historical = replay(code, games, temp)
        baseline_counts, _, _ = compare_rows(reference, historical)
        if baseline_counts:
            raise RuntimeError(f"Original archived covariate baseline failed: {baseline_counts}")
        corrected_games = games.copy()
        for game_id, tip in CORRECTED_TIP_UTC.items():
            mask = corrected_games.game_id.eq(game_id)
            if mask.sum() != 1:
                raise ValueError(f"Expected exactly one original fixture for {game_id}")
            date = pd.Timestamp(tip)
            corrected_games.loc[mask, "tip_utc"] = date
            corrected_games.loc[mask, "game_date_et"] = (
                date.tz_convert("America/New_York").date().isoformat()
            )
        updated = replay(code, corrected_games, temp)
        changed, magnitudes, examples = compare_rows(historical, updated)
        return {
            "scope": "Sensitivity only: two confirmed fixture UTC/ET dates corrected; frozen IDs unchanged",
            "source_zip_sha256": EXPECTED_ZIP_SHA,
            "source_executable_sha256": EXPECTED_CODE_SHA,
            "archived_team_game_rows": len(reference),
            "baseline_differing_cells": 0,
            "baseline_columns_checked": len(reference.columns),
            "corrections": CORRECTED_TIP_UTC,
            "changed_team_game_cells_by_column": changed,
            "numeric_effect_sizes": magnitudes,
            "changed_key_examples": examples,
            "warning": (
                "Replays original Elo and team-game covariate code. "
                "This is NOT a rebuilt player-game panel or refitted policy regression; "
                "game_id retains historical date text to preserve row identity."
            ),
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--covariates-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path,
                        default=REPO / "data_rebuild/output/fixture_date_swap_covariate_impact.json")
    args = parser.parse_args()
    report = run(args.covariates_zip.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    summary = {
        "baseline_differing_cells": report["baseline_differing_cells"],
        "team_game_rows": report["archived_team_game_rows"],
        "affected_columns": report["changed_team_game_cells_by_column"],
        "elo": report["numeric_effect_sizes"].get("team_elo_pre"),
        "full_report": str(args.output),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
