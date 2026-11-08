#!/usr/bin/env python3
"""Corrected-chronology Stage-6 SENSITIVITY, not replacement of historical output.

Correct two verified February 2022 fixture dates; recompute original rest/travel/
Elo and team-game fields; reconnect each game to its true historical report;
recalculate original player histories/onsets using the untouched Stage-6 builder;
then execute the original separate four-specification regression script.

Requires a verified Level-B historical replay root plus original covariate ZIP.
Never writes to the original replay root, original ZIPs, or frozen references.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

import pandas as pd
import audit_fixture_date_swap_covariates as cov

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "scripts/data_rebuild"
BASE = "analysis/nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz"
SEL = "cadence_work/selector/nba_canonical_snapshot_selector_v1"
MATCH_SWAPS = {430: 784, 784: 430}
EXPECTED_MATCHUPS = {430: "MIA@TOR", 784: "CHI@TOR"}
FAST_SOURCE_SHA = "f33950c15302f281830bbb5f047ca84b744a77d9039c8a313f158c63374001d3"
FAST_ROOT_LINE = "ROOT=Path('/mnt/data/nba_continue'); OUT=ROOT/'cadence_harmonized_results'"


def invoke(name: str, *arguments):
    cmd = [sys.executable, str(TOOLS / name), *(str(x) for x in arguments)]
    print("RUN", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=REPO, check=True)


def correct_team_games(zip_path: Path):
    if cov.file_sha(zip_path) != cov.EXPECTED_ZIP_SHA:
        raise RuntimeError("Source covariate ZIP SHA-256 differs from frozen provenance")
    code, source, archived = cov.source_tables(zip_path)
    if hashlib.sha256(code).hexdigest() != cov.EXPECTED_CODE_SHA:
        raise RuntimeError("Original game-covariate script SHA-256 differs")
    source["tip_utc"] = pd.to_datetime(source["tip_utc"], utc=True)
    source["neutral_site"] = source["neutral_site"].astype(bool)
    updated = source.copy()
    for game, new_tip in cov.CORRECTED_TIP_UTC.items():
        mask = updated.game_id.eq(game)
        if mask.sum() != 1:
            raise RuntimeError(f"Expected exactly one affected fixture: {game}")
        tip = pd.Timestamp(new_tip)
        updated.loc[mask, "tip_utc"] = tip
        updated.loc[mask, "game_date_et"] = tip.tz_convert("America/New_York").date().isoformat()
    with tempfile.TemporaryDirectory(prefix="nba_fixture_covariate_code_") as folder:
        before = cov.replay(code, source, Path(folder))
        after = cov.replay(code, updated, Path(folder))
    if cov.compare_rows(archived, before)[0]:
        raise RuntimeError("Original covariate builder baseline does not reproduce archive")
    return before, after, cov.compare_rows(before, after)[0]


def equal_cells(a: pd.Series, b: pd.Series):
    """Return boolean Series; parse only unequal strings, never blindly parse names as dates."""
    left = a.fillna("").astype(str).str.strip()
    right = b.fillna("").astype(str).str.strip()
    equal = left.str.casefold().eq(right.str.casefold()).astype(bool)
    pending = ~equal
    if not pending.any():
        return equal
    x, y = pd.to_numeric(left[pending], errors="coerce"), pd.to_numeric(right[pending], errors="coerce")
    numeric = x.notna() & y.notna()
    if numeric.any():
        indices = numeric.index[numeric]
        equal.loc[indices] = (x.loc[indices] - y.loc[indices]).abs().le(1e-8).to_numpy()
    unresolved = ~equal
    date_candidates = (
        left[unresolved].str.match(r"^\d{4}-\d\d-\d\d")
        & right[unresolved].str.match(r"^\d{4}-\d\d-\d\d")
    )
    if date_candidates.any():
        positions = date_candidates.index[date_candidates]
        da = pd.to_datetime(left.loc[positions], utc=True, errors="coerce", format="mixed")
        db = pd.to_datetime(right.loc[positions], utc=True, errors="coerce", format="mixed")
        equal.loc[positions] = (da.notna() & db.notna() & da.eq(db)).to_numpy()
    return equal.astype(bool)


def serialize_like(old: str, new):
    if pd.isna(new):
        return ""
    if isinstance(new, bool) or str(new) in ("True", "False"):
        return str(new).lower() == "true" and "True" or "False"
    if isinstance(new, pd.Timestamp):
        return str(new)
    try:
        num = float(new)
    except (ValueError, TypeError):
        return str(new)
    return str(int(num)) if "." not in old and num.is_integer() else repr(num)


def fix_base(base_path: Path, before: pd.DataFrame, after: pd.DataFrame, changed: dict):
    if base_path.is_symlink():
        raise RuntimeError(f"Refusing to write through source symlink: {base_path}")
    base = pd.read_csv(base_path, dtype=str, keep_default_na=False, low_memory=False)
    key = ["game_id", "team"]
    if base.duplicated(["player_team_game_id"]).any():
        raise RuntimeError("Duplicate canonical player-game IDs")
    columns = [name for name in changed if name in base.columns]
    old = base[key].merge(before[key + columns].astype(object), on=key, how="left", validate="many_to_one")
    updated = base[key].merge(after[key + columns].astype(object), on=key, how="left", validate="many_to_one")
    if len(old) != len(base) or len(updated) != len(base):
        raise RuntimeError("Original covariate replay changes canonical base row count")
    record = {}
    for col in columns:
        a = old[col].astype(str).where(old[col].notna(), "")
        b = updated[col].astype(str).where(updated[col].notna(), "")
        if not equal_cells(base[col], a).all():
            raise RuntimeError(f"Original covariate {col} differs from frozen canonical base")
        mask = ~equal_cells(a, b)
        base.loc[mask, col] = [
            serialize_like(previous, new)
            for previous, new in zip(base.loc[mask, col], updated.loc[mask, col])
        ]
        record[col] = {"rows": int(mask.sum()), "games": int(base.loc[mask, "game_id"].nunique())}
    base.to_csv(base_path, index=False, compression="gzip")
    return record


def fix_selectors(root: Path):
    folder = root / SEL
    map_file = folder / "2021-22_game_snapshot_join_harmonized_canonical.csv"
    status_file = folder / "2021-22_team_game_status_harmonized_canonical.csv"
    for file in (map_file, status_file):
        if file.is_symlink():
            raise RuntimeError(f"Refusing to write through source symlink: {file}")
    games = pd.read_csv(map_file)
    for match, original_matchup in EXPECTED_MATCHUPS.items():
        selected = games["Match Number"].eq(match)
        if selected.sum() != 1 or games.loc[selected, "matchup_norm"].iloc[0] != original_matchup:
            raise RuntimeError(f"Unexpected original selector match {match}")
        required_date = "2022-02-01" if match == 430 else "2022-02-03"
        if games.loc[selected, "game_date_et"].iloc[0] != required_date:
            raise RuntimeError(f"Unexpected original report date for selector match {match}")
    mask = games["Match Number"].isin(MATCH_SWAPS)
    games.loc[mask, "Match Number"] = games.loc[mask, "Match Number"].map(MATCH_SWAPS)
    games.to_csv(map_file, index=False)
    teams = pd.read_csv(status_file)
    mapping = {"FD2021_430": "FD2021_784", "FD2021_784": "FD2021_430"}
    if teams.game_id.isin(mapping).sum() != 4:
        raise RuntimeError("Expected two team statuses per original affected game")
    teams["game_id"] = teams["game_id"].replace(mapping)
    teams.to_csv(status_file, index=False)


def compare_panels(frozen_path: Path, candidate_path: Path, output: Path):
    frozen = pd.read_csv(frozen_path, dtype=str, keep_default_na=False).set_index("player_team_game_id")
    new = pd.read_csv(candidate_path, dtype=str, keep_default_na=False).set_index("player_team_game_id")
    if frozen.index.has_duplicates or new.index.has_duplicates:
        raise RuntimeError("Duplicate reconstructed player-game keys")
    if set(frozen.columns) != set(new.columns) or set(frozen.index) != set(new.index):
        raise RuntimeError("Rebuilt panel has unexpected columns or missing/extra player-game keys")
    new = new.loc[frozen.index, frozen.columns]
    mismatch = frozen.ne(new)
    changed = mismatch.any(axis=1)
    affected = frozen.game_id.isin(cov.CORRECTED_TIP_UTC)
    report = {
        "reference_rows": len(frozen), "rebuilt_rows": len(new),
        "only_reference": 0, "only_rebuilt": 0,
        "changed_rows": int(changed.sum()),
        "changed_rows_in_the_two_games": int((changed & affected).sum()),
        "changed_games": int(frozen.loc[changed, "game_id"].nunique()),
        "changed_cells_by_column": {
            name: int(mismatch[name].sum()) for name in mismatch
            if mismatch[name].any()
        },
        "risk_rows": int(new.at_risk_for_new_onset_harm.eq("True").sum()),
        "onsets": int(new.absence_onset_harm.eq("True").sum()),
    }
    for field in ("absence_now_harm", "at_risk_for_new_onset_harm",
                  "absence_onset_harm", "designation_status"):
        indices = frozen.index[mismatch[field]]
        pd.DataFrame({
            "player_team_game_id": indices,
            "game_id": frozen.loc[indices, "game_id"],
            "player": frozen.loc[indices, "nba_player_name"],
            "frozen": frozen.loc[indices, field],
            "corrected": new.loc[indices, field],
        }).to_csv(output / f"changed_{field}.csv", index=False)
    return report


def rerun_original_models(panel_path: Path, stage6_zip: Path, output: Path):
    with zipfile.ZipFile(stage6_zip) as archive:
        source = archive.read("scripts/run_cadence_models_fast.py")
        archived_rows = pd.read_csv(io.BytesIO(
            archive.read("results/cadence_harmonized_model_results.csv")
        ))
    if hashlib.sha256(source).hexdigest() != FAST_SOURCE_SHA:
        raise RuntimeError("Archived fast model source hash mismatch")
    script = source.decode("utf-8")
    if script.count(FAST_ROOT_LINE) != 1:
        raise RuntimeError("Original fast model ROOT marker missing or duplicated")
    with tempfile.TemporaryDirectory(prefix="nba_chronology_stage6_") as folder:
        root = Path(folder)
        inputs = root / "cadence_harmonized_results"
        inputs.mkdir()
        shutil.copy2(panel_path, inputs / "player_team_game_harmonized_cadence.csv.gz")
        runnable = script.replace(FAST_ROOT_LINE,
            f"ROOT=Path({str(root)!r}); OUT=ROOT/'cadence_harmonized_results'")
        runner = root / "run_cadence_models_fast.py"
        runner.write_text(runnable, encoding="utf-8")
        environment = {**os.environ, "OPENBLAS_NUM_THREADS": "1",
                       "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
        result = subprocess.run([sys.executable, str(runner)],
                                cwd=root, env=environment, capture_output=True,
                                text=True, check=True, timeout=900)
        target = inputs / "cadence_harmonized_model_results.csv"
        if not target.is_file():
            raise RuntimeError("Historical Stage-6 executable did not produce model coefficients")
        dest = output / "stage6_models"
        dest.mkdir()
        shutil.copy2(target, dest / "cadence_harmonized_model_results.csv")
        (dest / "stdout.txt").write_text(result.stdout)
        (dest / "stderr.txt").write_text(result.stderr)
    rebuilt = pd.read_csv(output / "stage6_models/cadence_harmonized_model_results.csv")
    key = ["definition", "controls"]
    if archived_rows.duplicated(key).any() or rebuilt.duplicated(key).any():
        raise RuntimeError("Duplicate model specification keys")
    models = archived_rows.merge(rebuilt, on=key, how="outer",
                                suffixes=("_frozen", "_corrected"),
                                indicator=True, validate="one_to_one")
    if len(models) != 4 or not models["_merge"].eq("both").all():
        raise RuntimeError("Missing, extra or unmatched Stage-6 model specifications")
    if not models.n_frozen.eq(models.n_corrected).all():
        raise RuntimeError("Corrected chronology changed model complete-case N")
    return [
        {
            "definition": row.definition, "controls": row.controls,
            "n_frozen": int(row.n_frozen), "n_corrected": int(row.n_corrected),
            "estimate_pp_frozen": row.estimate_pp_frozen,
            "estimate_pp_corrected": row.estimate_pp_corrected,
            "change_pp": row.estimate_pp_corrected - row.estimate_pp_frozen,
            "se_pp_corrected": row.se_pp_corrected,
            "p_frozen": row.p_frozen, "p_corrected": row.p_corrected,
        }
        for row in models.itertuples(index=False)
    ]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--replay-root", required=True, type=Path)
    p.add_argument("--variant-root", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--covariates-zip", required=True, type=Path)
    p.add_argument("--reference", type=Path,
                   default=REPO / "data_intermediate/player_team_game_harmonized_cadence.csv.gz")
    p.add_argument("--stage6-zip", type=Path,
                   default=REPO / "packages/06_cadence_harmonized_identification.zip")
    a = p.parse_args()
    original, variant, output = (
        a.replay_root.resolve(), a.variant_root.resolve(), a.output.resolve()
    )
    if variant.exists():
        raise SystemExit(f"Corrected variant root must be newly created: {variant}")
    if original == variant or original in variant.parents or variant in original.parents:
        raise SystemExit("Original and variant roots overlap")
    if original == output or original in output.parents or variant == output or variant in output.parents:
        raise SystemExit("Source, variant and output directories must be separate")
    # Resolve source ZIP symlinks to independent copies; never write through
    # original source ZIP, base panel or selector files.
    shutil.copytree(original, variant, symlinks=False,
                    ignore=lambda directory, names: [
                        n for n in names if n == "source_pdfs"
                    ])
    output.mkdir(parents=True, exist_ok=True)

    before, after, cov_changes = correct_team_games(a.covariates_zip.resolve())
    base_changes = fix_base(variant / BASE, before, after, cov_changes)
    fix_selectors(variant)
    invoke("run_historical_cadence_builder.py", "--historical-root", variant,
           "--output", output)
    candidate = output / "player_team_game_harmonized_cadence.csv.gz"
    if not candidate.is_file():
        raise RuntimeError("Historical builder did not produce corrected cadence panel")
    panel_changes = compare_panels(a.reference.resolve(), candidate, output)
    models = rerun_original_models(candidate, a.stage6_zip.resolve(), output)
    report = {
        "scope": "Separate SENSITIVITY: corrected two 2021-22 fixture dates, report links and histories; historical frozen inputs unchanged",
        "source_covariates_zip_sha256": cov.EXPECTED_ZIP_SHA,
        "original_covariate_code_sha256": cov.EXPECTED_CODE_SHA,
        "original_stage6_model_sha256": FAST_SOURCE_SHA,
        "base_panel_cells_changed": base_changes,
        "panel_vs_frozen": panel_changes,
        "stage6_models": models,
        "not_rebuilt": "Other frozen analyses outside cadence Stage-6; all-six-season raw-source-to-paper Level C",
    }
    (output / "fixture_date_chronology_sensitivity.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
