#!/usr/bin/env python3
"""Carry source-corrected August core to a labeled analysis-ready SENSITIVITY.

The original reviewed v2 taxonomy is reproduced for every frozen row using a
case-folded official-report reason to class lookup, with an exact no-conflicts
gate. All active corrected official report reasons must have known historical
reviewed labels: do NOT silently classify unseen reasons.

The original award/star/Cup flags are explicitly INHERITED by the immutable
player_team_game_id, not independently regenerated. The two incorrect-date
game_id keys remain retained for comparison. This is not full Level-C.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

ANALYSIS_ZIP_SHA = "a3d991bdaf41cbdba734abbd43853b495b27fbb96576743259413fcd50eb9155"
EXPECTED_CORE_OLD = 248730
EXPECTED_CORE_NEW = 248728
EXCLUDED_CORE = {
    "star_PPP_it", "star_status_pending", "cup_game_pending",
    "taxonomy_version",
}
FLAGS = {
    "vague_onset_frozen": "vague_injury_onset",
    "specific_onset_frozen": "specific_injury_onset",
    "explicit_rest_onset_frozen": "explicit_rest_onset",
    "other_absence_onset_frozen": "other_absence_onset",
}


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_member(archive: ZipFile, basename: str, **kwargs):
    member = [x for x in archive.namelist() if x.endswith("/" + basename)]
    if len(member) != 1:
        raise RuntimeError(f"Missing or ambiguous archived analysis table: {basename}")
    with gzip.GzipFile(fileobj=archive.open(member[0])) as f:
        return pd.read_csv(f, dtype=str, keep_default_na=False,
                           low_memory=False, **kwargs)


def index_core(df: pd.DataFrame):
    df = df.copy()
    df["player_team_game_id"] = (
        df.game_id + "|" + df.team + "|" + df.nba_player_id)
    if df.player_team_game_id.duplicated().any():
        raise RuntimeError("Duplicate player-team-game keys")
    return df.set_index("player_team_game_id", drop=False)


def reason_key(series: pd.Series):
    return series.fillna("").astype(str).str.strip().str.casefold()


def reviewed_reason_lookup(frozen: pd.DataFrame):
    active = frozen[frozen.absence_now.eq("True")].copy()
    active["reason_key"] = reason_key(active.designation_reason)
    conflict = active.groupby("reason_key").designation_class_frozen.nunique()
    if conflict.gt(1).any():
        raise RuntimeError(f"Reviewed taxonomy has conflicting official reasons: {conflict[conflict.gt(1)]}")
    return (active.drop_duplicates("reason_key")
            .set_index("reason_key").designation_class_frozen.to_dict())


def official_reason_classes(df: pd.DataFrame, dictionary: dict):
    cls = pd.Series("not_absent", index=df.index, dtype="object")
    absent = df.absence_now.eq("True")
    keys = reason_key(df.loc[absent, "designation_reason"])
    missing = keys[~keys.isin(dictionary)]
    if len(missing):
        raise RuntimeError(f"New official injury wording requires review: {missing.unique()[:20]}")
    cls.loc[absent] = keys.map(dictionary)
    onset = pd.Series("", index=df.index, dtype="object")
    risk = df.at_risk_for_new_onset.eq("True")
    onset.loc[risk & ~absent] = "plays"
    for category, label in (("specific", "specific_injury_onset"),
                             ("vague", "vague_injury_onset"),
                             ("explicit_rest", "explicit_rest_onset")):
        onset.loc[risk & absent & cls.eq(category)] = label
    onset.loc[risk & absent &
              ~cls.isin(["specific", "vague", "explicit_rest"])] = "other_absence_onset"
    return cls, onset


def baseline_taxonomy_gate(original: pd.DataFrame, archived: pd.DataFrame, labels: dict):
    if set(original.index) != set(archived.index):
        raise RuntimeError("Original core is not the exact archived player-game ID set")
    expected_class, expected_onset = official_reason_classes(original, labels)
    if not expected_class.equals(archived.designation_class_frozen):
        raise RuntimeError("Cannot reproduce historical reviewed taxonomy classes")
    if not expected_onset.equals(archived.onset_type_frozen):
        raise RuntimeError("Cannot reproduce historical frozen onset types")
    for field, target in FLAGS.items():
        expected = expected_onset.eq(target).astype(str)
        if not expected.equals(archived[field]):
            raise RuntimeError(f"Historical taxonomy flag baseline differs: {field}")


def corrected_analysis_ready(original, corrected, archived):
    if len(original) != EXPECTED_CORE_OLD or len(corrected) != EXPECTED_CORE_NEW:
        raise RuntimeError("Unexpected original/corrected core row count")
    if set(corrected.index) - set(original.index):
        raise RuntimeError("Corrected core introduced unforeseen player-game keys")
    if set(archived.index) != set(original.index):
        raise RuntimeError("Archived final and original core keys do not match")
    labels = reviewed_reason_lookup(archived)
    baseline_taxonomy_gate(original, archived, labels)

    result = archived.loc[corrected.index].copy()
    before = original.loc[corrected.index]
    deltas = {}
    for field in before.columns.intersection(result.columns):
        if field in EXCLUDED_CORE or field == "player_team_game_id":
            continue
        a, b = before[field], corrected[field]
        changed = a.ne(b)
        if not changed.any():
            continue
        indices = changed.index[changed]
        numeric_a = pd.to_numeric(a.loc[indices], errors="coerce")
        numeric_b = pd.to_numeric(b.loc[indices], errors="coerce")
        near = numeric_a.notna() & numeric_b.notna() & (
            numeric_a - numeric_b).abs().le(1e-8)
        changed.loc[indices[near]] = False
        if changed.any():
            result.loc[changed, field] = b.loc[changed]
            deltas[field] = int(changed.sum())

    for frozen_alias, original_field in (
        ("designation_class_provisional_v1", "designation_class_provisional"),
        ("onset_type_provisional_v1", "onset_type"),
        ("vague_onset_provisional_v1", "vague_onset"),
    ):
        result[frozen_alias] = result[original_field]

    classes, onsets = official_reason_classes(result, labels)
    result["designation_class_frozen"] = classes
    result["onset_type_frozen"] = onsets
    for field, target in FLAGS.items():
        result[field] = onsets.eq(target).astype(str)

    if (result.player_team_game_id.duplicated().any()
            or int(result.at_risk_for_new_onset.eq("True").sum()) != 180831
            or int(result.absence_onset.eq("True").sum()) != 12707):
        raise RuntimeError("Corrected August player-game risk/onset invariants fail")
    return result, labels, deltas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-core", type=Path, required=True)
    parser.add_argument("--corrected-core", type=Path, required=True)
    parser.add_argument("--analysis-ready-zip", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError("Use a new output directory; do not overwrite frozen data")
    if sha256(args.analysis_ready_zip.resolve()) != ANALYSIS_ZIP_SHA:
        raise RuntimeError("Original August reviewed analysis-ready ZIP SHA differs")

    orig = index_core(pd.read_csv(args.historical_core.resolve(),
                    dtype=str, keep_default_na=False, low_memory=False))
    corr = index_core(pd.read_csv(args.corrected_core.resolve(),
                    dtype=str, keep_default_na=False, low_memory=False))
    with ZipFile(args.analysis_ready_zip.resolve()) as archive:
        frozen = read_member(archive, "player_game_panel_analysis_ready.csv.gz")
        model_cols = read_member(
            archive, "player_game_panel_model_at_risk_analysis_ready.csv.gz",
            nrows=1).columns.tolist()
        if frozen.player_team_game_id.duplicated().any():
            raise RuntimeError("Historical reviewed final keys duplicated")
        frozen = frozen.set_index("player_team_game_id", drop=False)
        output.mkdir(parents=True)
        variant, dictionary, fields = corrected_analysis_ready(orig, corr, frozen)
        full_columns = frozen.columns.tolist()
        variant = variant.loc[:, full_columns]
        risk = variant.at_risk_for_new_onset.eq("True")
        subset = variant.loc[risk, model_cols]
        if len(subset) != 180831:
            raise RuntimeError("Corrected final risk-set selection unexpectedly differs")
        variant.to_csv(output / "player_game_panel_analysis_ready.csv.gz",
                       index=False, compression="gzip")
        subset.to_csv(output / "player_game_panel_model_at_risk_analysis_ready.csv.gz",
                      index=False, compression="gzip")

    report = {
        "scope": "Corrected August latest-pre-tip sensitivity with retained stable IDs and frozen awards/Cup flags",
        "archived_reviewed_taxonomy_source_sha256": ANALYSIS_ZIP_SHA,
        "reviewed_historical_reason_classes": len(dictionary),
        "reviewed_taxonomy_frozen_baseline_exact_match": True,
        "unknown_active_corrected_reasons": 0,
        "original_full_rows": len(orig), "corrected_full_rows": len(variant),
        "original_risk_rows": 180829, "corrected_risk_rows": len(subset),
        "original_onsets": 12710,
        "corrected_onsets": int(variant.absence_onset.eq("True").sum()),
        "changed_reviewed_class_cells": int(variant.designation_class_frozen.ne(
            frozen.loc[variant.index, "designation_class_frozen"]).sum()),
        "changed_reviewed_onset_type_cells": int(variant.onset_type_frozen.ne(
            frozen.loc[variant.index, "onset_type_frozen"]).sum()),
        "source_core_field_changes": fields,
        "qualification": "Star/award/Cup flags inherited from original reviewed analysis-ready rows; 2 frozen game_id strings encode obsolete tips. This is a sensitivity, not independently reconstructed awards or new human-coded taxonomy.",
    }
    (output / "corrected_august_analysis_ready_qa.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items()
                      if k != "source_core_field_changes"}, indent=2))


if __name__ == "__main__":
    main()
