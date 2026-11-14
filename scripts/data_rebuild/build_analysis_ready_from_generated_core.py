#!/usr/bin/env python3
"""Build the released analysis-ready tables from a newly generated NBA core.

Recomputes reviewed official-reason injury taxonomy and onset labels from the
new core; inherits explicitly identified historical human-review, award/star,
Cup and other annotated metadata from a SHA-pinned archived release.
This is a provenance-explicit analysis-ready bridge, not independent
primary-source award/Cup collection or a replacement for second-coder review.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
from itertools import zip_longest
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

REVIEWED_ZIP_SHA256 = "a3d991bdaf41cbdba734abbd43853b495b27fbb96576743259413fcd50eb9155"
FROZEN_CORE_CSV_SHA256 = "253bf017095a8be45f4c7bb4a0abcc9b942a8db6311f91131c9fd12c7ab46de3"
SOURCE_FULL = "nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz"
SOURCE_MODEL = "nba_player_game_analysis_ready_v1/player_game_panel_model_at_risk_analysis_ready.csv.gz"
EXPECTED_FULL = 248730
EXPECTED_RISK = 180829
ALLOWED_SOURCE_ENRICHMENTS = frozenset({
    "taxonomy_version", "star_PPP_it", "star_status_pending",
    "cup_game_pending",
})
FROZEN_ONSET_FLAGS = {
    "vague_onset_frozen": "vague_injury_onset",
    "specific_onset_frozen": "specific_injury_onset",
    "explicit_rest_onset_frozen": "explicit_rest_onset",
    "other_absence_onset_frozen": "other_absence_onset",
}
PROVISIONAL_ALIASES = {
    "designation_class_provisional_v1": "designation_class_provisional",
    "onset_type_provisional_v1": "onset_type",
    "vague_onset_provisional_v1": "vague_onset",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


def decoded_gzip_sha256(stream) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    for data in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(data)
        total += len(data)
    return digest.hexdigest(), total


def archived_member(archive: ZipFile, member: str):
    if archive.namelist().count(member) != 1:
        raise ValueError(f"Missing/ambiguous archived analysis-ready member: {member}")
    return archive.open(member)


def reason_key(values: pd.Series) -> pd.Series:
    return values.fillna("").astype(str).str.strip().str.casefold()


def build_reason_dictionary(archive_path: Path, chunksize: int) -> dict[str, str]:
    labels = {}
    with ZipFile(archive_path) as z, gzip.GzipFile(
            fileobj=archived_member(z, SOURCE_FULL)) as stream:
        for chunk in pd.read_csv(stream, dtype=str, keep_default_na=False,
                                 chunksize=chunksize, low_memory=False):
            required = {"absence_now", "designation_reason", "designation_class_frozen"}
            if not required <= set(chunk):
                raise ValueError("Original reviewed official reason taxonomy fields missing")
            absent = chunk.loc[chunk.absence_now.eq("True")]
            for reason, cls in zip(reason_key(absent.designation_reason),
                                   absent.designation_class_frozen):
                old = labels.setdefault(reason, cls)
                if old != cls:
                    raise ValueError("Conflicting archived reviewed official reason labels")
    if len(labels) != 2182:
        raise ValueError(f"Reviewed reason dictionary size changed: {len(labels)}")
    return labels


def reconcile_one_chunk(core: pd.DataFrame, frozen: pd.DataFrame,
                        labels: dict[str, str]) -> tuple[pd.DataFrame, pd.Series]:
    if len(core) != len(frozen):
        raise ValueError("Core versus reviewed analysis-ready chunk row count changed")
    if not set(core.columns) <= set(frozen.columns):
        raise ValueError(f"Original core fields missing from reviewed analysis: {set(core)-set(frozen)}")
    required = {"game_id", "team", "nba_player_id", "absence_now",
                "designation_reason", "at_risk_for_new_onset"}
    if not required <= set(core) or "player_team_game_id" not in frozen:
        raise ValueError("Required core/report identity fields missing")
    keys = core.game_id + "|" + core.team + "|" + core.nba_player_id
    if not keys.astype(str).equals(frozen.player_team_game_id.astype(str)):
        raise ValueError("Rebuilt core row ID/order differs from original reviewed analysis input")

    # Check unknown official reasons before the general source-field equality
    # gate so the error is actionable and never silently guesses a new label.
    absent = core.absence_now.eq("True")
    chosen = reason_key(core.loc[absent, "designation_reason"])
    if not chosen.isin(labels).all():
        raise ValueError("New official injury-report reason requires independent taxonomy review")

    result = frozen.copy()
    for field in core.columns:
        if field in ALLOWED_SOURCE_ENRICHMENTS:
            continue   # reviewed source altered the provisional core at this stage
        left, right = core[field], frozen[field]
        if left.equals(right):
            result[field] = left
            continue
        mask = left.ne(right)
        numeric_left = pd.to_numeric(left[mask], errors="coerce")
        numeric_right = pd.to_numeric(right[mask], errors="coerce")
        if (numeric_left.isna().any() or numeric_right.isna().any()
                or (numeric_left - numeric_right).abs().gt(1e-8).any()):
            raise ValueError(f"Non-formatting difference in generated core field: {field}")
        # Reuse the archive's decimal text serialization but only after proving
        # each differing generated-core value is numerically identical.
        result[field] = left
        result.loc[mask, field] = right.loc[mask]

    risk = core.at_risk_for_new_onset.eq("True")
    classes = pd.Series("not_absent", index=core.index, dtype=object)
    classes.loc[absent] = chosen.map(labels)
    onset = pd.Series("", index=core.index, dtype=object)
    onset.loc[risk & ~absent] = "plays"
    for category, outcome in (("specific", "specific_injury_onset"),
                              ("vague", "vague_injury_onset"),
                              ("explicit_rest", "explicit_rest_onset")):
        onset.loc[risk & absent & classes.eq(category)] = outcome
    onset.loc[risk & absent &
              ~classes.isin(("specific", "vague", "explicit_rest"))] = "other_absence_onset"

    result["designation_class_frozen"] = classes
    result["onset_type_frozen"] = onset
    for alias, source in PROVISIONAL_ALIASES.items():
        if source not in core:
            raise ValueError(f"Missing original provisional taxonomy field: {source}")
        result[alias] = core[source]
    for field, outcome in FROZEN_ONSET_FLAGS.items():
        result[field] = onset.eq(outcome).astype(str)

    for field in ("designation_class_frozen", "onset_type_frozen",
                  *PROVISIONAL_ALIASES, *FROZEN_ONSET_FLAGS):
        if not result[field].astype(object).equals(frozen[field].astype(object)):
            raise ValueError(f"Recomputed official-report taxonomy differs: {field}")
    return result.loc[:, frozen.columns], risk


def verify_decoded_outputs(output_dir: Path, reviewed_zip: Path) -> dict:
    evidence = {}
    with ZipFile(reviewed_zip) as archive:
        for basename, member in (
                ("player_game_panel_analysis_ready.csv.gz", SOURCE_FULL),
                ("player_game_panel_model_at_risk_analysis_ready.csv.gz", SOURCE_MODEL)):
            with gzip.open(output_dir / basename, "rb") as output:
                observed = decoded_gzip_sha256(output)
            with gzip.GzipFile(fileobj=archived_member(archive, member)) as reference:
                expected = decoded_gzip_sha256(reference)
            if observed != expected:
                raise ValueError(f"Generated analysis-ready CSV differs from source release: {basename}")
            evidence[basename] = {
                "decoded_csv_sha256": observed[0],
                "decoded_csv_bytes": observed[1],
                "decoded_contents_match_frozen": True,
                "gzip_header_timestamp_ignored": True,
            }
    return evidence


def build(core_file: Path, reviewed_zip: Path, output_dir: Path,
          *, chunksize: int = 20000) -> dict:
    core_file = core_file.resolve(strict=True)
    reviewed_zip = reviewed_zip.resolve(strict=True)
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"Use new analysis-ready output directory: {output_dir}")
    if chunksize < 1:
        raise ValueError("Chunk size must be positive")
    if sha256_file(reviewed_zip) != REVIEWED_ZIP_SHA256:
        raise ValueError("Original reviewed analysis-ready ZIP SHA-256 has changed")
    with gzip.open(core_file, "rb") as stream:
        core_identity, _ = decoded_gzip_sha256(stream)
    if core_identity != FROZEN_CORE_CSV_SHA256:
        raise ValueError("This baseline analysis bridge requires the independently regenerated historical core")
    labels = build_reason_dictionary(reviewed_zip, chunksize)
    output_dir.mkdir(parents=True)
    full_path = output_dir / "player_game_panel_analysis_ready.csv.gz"
    model_path = output_dir / "player_game_panel_model_at_risk_analysis_ready.csv.gz"
    full_rows, risk_rows = 0, 0
    with ZipFile(reviewed_zip) as z, gzip.GzipFile(
        fileobj=archived_member(z, SOURCE_FULL)
    ) as frozen_stream, gzip.open(full_path, "wt", newline="", encoding="utf-8") as full_out, gzip.open(
        model_path, "wt", newline="", encoding="utf-8"
    ) as risk_out:
        with gzip.GzipFile(fileobj=archived_member(z, SOURCE_MODEL)) as source_model:
            model_fields = pd.read_csv(source_model, nrows=0).columns.tolist()
        generated = pd.read_csv(core_file, dtype=str, keep_default_na=False,
                                chunksize=chunksize, low_memory=False)
        original = pd.read_csv(frozen_stream, dtype=str, keep_default_na=False,
                               chunksize=chunksize, low_memory=False)
        for i, pair in enumerate(zip_longest(generated, original)):
            core, frozen = pair
            if core is None or frozen is None:
                raise ValueError("Mismatched number of generated core / original release chunks")
            out, risk = reconcile_one_chunk(core, frozen, labels)
            if not set(model_fields) <= set(out):
                raise ValueError("Rebuilt analysis-ready table lacks historical model fields")
            out.to_csv(full_out, index=False, header=(i == 0))
            out.loc[risk, model_fields].to_csv(risk_out, index=False, header=(i == 0))
            full_rows += len(out)
            risk_rows += int(risk.sum())
    if (full_rows, risk_rows) != (EXPECTED_FULL, EXPECTED_RISK):
        raise ValueError(f"Generated analysis-ready row counts changed: {full_rows}, {risk_rows}")
    evidence = verify_decoded_outputs(output_dir, reviewed_zip)
    core_columns = pd.read_csv(core_file, nrows=0).columns
    with ZipFile(reviewed_zip) as z, gzip.GzipFile(
            fileobj=archived_member(z, SOURCE_FULL)) as source:
        analyzed_columns = pd.read_csv(source, nrows=0).columns
    report = {
        "scope": "Rebuilt original core -> rederived reviewed official-reason/onset taxonomy + explicitly inherited historical annotations",
        "generated_core_decoded_sha256": core_identity,
        "reviewed_archive_sha256": REVIEWED_ZIP_SHA256,
        "reviewed_official_reason_dictionary_size": len(labels),
        "newly_generated_full_rows": full_rows,
        "newly_generated_at_risk_rows": risk_rows,
        "shared_core_fields_semantically_checked": len(core_columns),
        "recomputed_reviewed_taxonomy_fields": [
            "designation_class_frozen", "onset_type_frozen",
            *FROZEN_ONSET_FLAGS, *PROVISIONAL_ALIASES],
        "inherited_new_reviewed_metadata_fields": sorted(
            set(analyzed_columns) - set(core_columns)
            - {"designation_class_frozen", "onset_type_frozen"}
            - set(FROZEN_ONSET_FLAGS) - set(PROVISIONAL_ALIASES)),
        "historically_overridden_core_metadata_fields": sorted(ALLOWED_SOURCE_ENRICHMENTS),
        "original_primary_source_awards_cup_star_independently_rebuilt": False,
        "all_analysis_ready_outputs_match_original_decoded_csv": True,
        "outputs": evidence,
    }
    (output_dir / "analysis_ready_rebuild_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--generated-core", type=Path, required=True)
    p.add_argument("--reviewed-source-zip", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--chunk-size", type=int, default=20000)
    a = p.parse_args()
    build(a.generated_core, a.reviewed_source_zip, a.output_dir, chunksize=a.chunk_size)


if __name__ == "__main__":
    main()
