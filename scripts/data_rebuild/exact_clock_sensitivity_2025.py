#!/usr/bin/env python3
"""Separate sensitivity: replace 2025–26 nominal checkpoints with printed PDF clocks.

Never modify the frozen historical replay root. Re-select affected reports, reparse,
rebuild panel, quantify changes and rerun the original Stage-6 fast regressions.
This is NOT a replacement for the unchanged historical frozen estimate.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile

import fitz
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "scripts/data_rebuild"
SEL = "cadence_work/selector/nba_canonical_snapshot_selector_v1"
ZIPS = ("cadence_2025/audit_2025_26_upload.zip",
        "cadence_2025/audit_2025_26_targeted_upload.zip")
LABEL = "SENSITIVITY_exact_clock_header_at_or_before_checkpoint"
HEADER = re.compile(r"Injury Report:\s*(\d{2}/\d{2}/\d{2})\s+(\d{1,2}:\d{2})\s*(AM|PM)")


def call(name, args):
    command = [sys.executable, str(TOOLS / name), *map(str, args)]
    print("RUN:", " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO, check=True)


def header_inventory(root):
    rows = []
    for source in ZIPS:
        with zipfile.ZipFile(root / source) as z:
            for member in z.namelist():
                if not member.lower().endswith(".pdf"):
                    continue
                data = z.read(member)
                with fitz.open(stream=data, filetype="pdf") as doc:
                    match = HEADER.search(doc[0].get_text())
                if not match:
                    raise RuntimeError(f"Missing PDF printed header time: {member}")
                naive = pd.Timestamp(pd.to_datetime(
                    f"{match[1]} {match[2]} {match[3]}",
                    format="%m/%d/%y %I:%M %p"))
                local = naive.tz_localize("America/New_York",
                                          ambiguous="NaT", nonexistent="NaT")
                rows.append({
                    "archive": Path(source).name, "member": member,
                    "basename": Path(member).name,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "header_utc": local.tz_convert("UTC") if not pd.isna(local) else pd.NaT,
                })
    inventory = pd.DataFrame(rows)
    duplicates = inventory.groupby("basename").sha256.nunique()
    if (duplicates > 1).any():
        raise RuntimeError(f"Conflicting PDF copies: {list(duplicates[duplicates > 1].index)[:5]}")
    return inventory.drop_duplicates("basename")


def candidates(selector, inventory):
    headers = inventory.set_index("basename").header_utc
    selector = selector.copy()
    selector["nominal"] = pd.to_datetime(selector.published_timestamp_utc, utc=True)
    selector["tip"] = pd.to_datetime(selector.tip_timestamp_utc, utc=True)
    selector["header"] = selector.snapshot_basename.map(headers)
    if selector.header.isna().any():
        raise RuntimeError("Selected PDF is missing from original archive or has unknown printed clock")
    late = selector[selector.header > selector.nominal]
    chosen = []
    for row in late.itertuples():
        eligible = inventory[inventory.header_utc.notna() & (inventory.header_utc <= row.nominal)]
        best = eligible[eligible.header_utc.eq(eligible.header_utc.max())]
        if len(best) != 1:
            raise RuntimeError(f"Ambiguous exact-clock PDF for {row.game_id}: {best.basename.tolist()}")
        selected = best.iloc[0]
        chosen.append({
            "game_id": row.game_id, "match_number": int(row._2),
            "matchup_norm": row.matchup_norm, "nominal_utc": row.nominal.isoformat(),
            "original_basename": row.snapshot_basename,
            "original_header_utc": row.header.isoformat(),
            "candidate_basename": selected.basename,
            "candidate_header_utc": selected.header_utc.isoformat(),
            "candidate_sha256": selected.sha256,
            "candidate_min_before_checkpoint": (row.nominal - selected.header_utc).total_seconds() / 60,
            "candidate_min_before_tip": (row.tip - selected.header_utc).total_seconds() / 60,
        })
    summary = {
        "archived_pdfs_scanned": len(inventory),
        "pdfs_with_dst_ambiguous_clock": int(inventory.header_utc.isna().sum()),
        "selected_games": len(selector),
        "selected_pdfs": int(selector.snapshot_basename.nunique()),
        "games_printed_after_checkpoint": len(late),
        "pdfs_printed_after_checkpoint": int(late.snapshot_basename.nunique()),
        "games_printed_at_or_after_tip": int((selector.header >= selector.tip).sum()),
        "printed_minus_nominal_minutes": sorted(
            ((late.header - late.nominal).dt.total_seconds() / 60).unique().tolist()),
    }
    return pd.DataFrame(chosen), summary


def apply_selector(root, selected):
    path = root / SEL / "2025-26_game_snapshot_join_harmonized_canonical.csv"
    games = pd.read_csv(path)
    for row in selected.itertuples():
        positions = games.index[games.game_id.eq(row.game_id)]
        if len(positions) != 1 or games.loc[positions[0], "snapshot_basename"] != row.original_basename:
            raise RuntimeError(f"Original selector game row mismatch: {row.game_id}")
        lead = (pd.Timestamp(games.loc[positions[0], "tip_timestamp_utc"])
                - pd.Timestamp(row.candidate_header_utc)).total_seconds() / 60
        games.loc[positions, [
            "snapshot_basename", "published_timestamp_utc", "minutes_before_tip",
            "qc_selected_within_30m", "selector_version",
        ]] = [row.candidate_basename, row.candidate_header_utc,
              lead, lead <= 30, LABEL]
    games.to_csv(path, index=False)


def norm_team(value):
    if pd.isna(value):
        return ""
    name = " ".join(str(value).lower().replace(".", "").replace("'", "").split())
    return {"la clippers": "los angeles clippers"}.get(name, name)


def apply_status(root, selected):
    rows = pd.read_csv(
        root / "cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv",
        low_memory=False)
    rows["bn"] = rows.source_file.astype(str).str.rsplit("/", n=1).str[-1]
    rows["tn"] = rows.team_norm.map(norm_team)
    path = root / SEL / "2025-26_team_game_status_harmonized_canonical.csv"
    teams = pd.read_csv(path)
    log = []
    for row in selected.itertuples():
        for idx in teams.index[teams.game_id.eq(row.game_id)]:
            subset = rows[
                rows.bn.eq(row.candidate_basename)
                & rows.matchup_norm.eq(teams.loc[idx, "matchup_norm"])
                & rows.tn.eq(teams.loc[idx, "team_norm"])
            ]
            if len(subset) and "not_yet_submitted" in set(
                    subset.team_submission_status.dropna().astype(str)):
                status, usable = "not_yet_submitted", False
            elif len(subset):
                status, usable = "submitted", True
            else:
                status, usable = "submitted_no_listed_players", True
            lead = (pd.Timestamp(teams.loc[idx, "tip_timestamp_utc"])
                    - pd.Timestamp(row.candidate_header_utc)).total_seconds() / 60
            log.append({
                "game_id": row.game_id, "team_norm": teams.loc[idx, "team_norm"],
                "old_status": teams.loc[idx, "team_final_status"],
                "new_status": status,
                "old_inferred": bool(teams.loc[idx, "inferred_no_listed_players"]),
                "new_inferred": len(subset) == 0,
            })
            teams.loc[idx, [
                "selected_snapshot_utc", "minutes_before_tip",
                "team_final_status", "usable_submitted_status",
                "inferred_no_listed_players", "qc_selected_within_30m",
                "selector_version",
            ]] = [row.candidate_header_utc, lead, status, usable,
                  len(subset) == 0, lead <= 30, LABEL]
    teams.to_csv(path, index=False)
    return pd.DataFrame(log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-root", type=Path, required=True)
    parser.add_argument("--variant-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata-dir", type=Path, required=True)
    parser.add_argument("--reference", type=Path, default=REPO / "data_intermediate/player_team_game_harmonized_cadence.csv.gz")
    args = parser.parse_args()
    src, root, out = (args.replay_root.resolve(),
                      args.variant_root.resolve(), args.output.resolve())
    if root.exists():
        raise SystemExit(f"Sensitivity root must be new: {root}")
    shutil.copytree(
        src, root, symlinks=True,
        ignore=lambda directory, names: [
            name for name in names
            if name == "source_pdfs" or
            (name == "2025-26" and Path(directory).name == "season_parsed")
        ])
    out.mkdir(parents=True, exist_ok=True)
    selector = pd.read_csv(root / SEL / "2025-26_game_snapshot_join_harmonized_canonical.csv")
    inventory = header_inventory(root)
    selected, summary = candidates(selector, inventory)
    selected.to_csv(out / "exact_clock_candidates.csv", index=False)
    print(json.dumps(summary, indent=2))
    apply_selector(root, selected)
    call("reparse_2025_selected.py",
         ["--historical-root", root, "--metadata-dir", args.metadata_dir])
    status_log = apply_status(root, selected)
    status_log.to_csv(out / "exact_clock_team_status_changes.csv", index=False)
    call("run_historical_cadence_builder.py",
         ["--historical-root", root, "--output", out])

    reference = pd.read_csv(args.reference, dtype=str, keep_default_na=False).set_index("player_team_game_id")
    new = pd.read_csv(out / "player_team_game_harmonized_cadence.csv.gz",
                      dtype=str, keep_default_na=False).set_index("player_team_game_id")
    if set(reference.index) != set(new.index):
        raise RuntimeError("Exact-clock panel differs in player-team-game keys")
    new = new.loc[reference.index]
    affected = (reference.season.eq("2025-26")
                & reference.source_match_number.astype(int).isin(set(selected.match_number)))
    changed = (reference != new).any(axis=1)
    result = {
        "scope": "SENSITIVITY; historical outputs unchanged", **summary,
        "candidate_pdfs": int(selected.candidate_basename.nunique()),
        "team_status_changes": int((status_log.old_status != status_log.new_status).sum()),
        "affected_rows": int(affected.sum()),
        "changed_rows": int(changed.sum()),
        "changed_rows_outside_affected_games": int((changed & ~affected).sum()),
        "changed_cells": {
            col: int(reference[col].ne(new[col]).sum())
            for col in reference.columns if reference[col].ne(new[col]).any()
        },
        "affected_risk_rows": int(new.at_risk_for_new_onset_harm[affected].eq("True").sum()),
        "affected_onsets": int(new.absence_onset_harm[affected].eq("True").sum()),
    }
    changes = (reference.designation_status.ne(new.designation_status)
               | reference.designation_reason.ne(new.designation_reason))
    pd.DataFrame({
        "player_team_game_id": reference.index[changes],
        "player": reference.nba_player_name[changes],
        "status_historical": reference.designation_status[changes],
        "status_exact_clock": new.designation_status[changes],
        "reason_historical": reference.designation_reason[changes],
        "reason_exact_clock": new.designation_reason[changes],
        "absence_now_harm": new.absence_now_harm[changes],
    }).to_csv(out / "exact_clock_designation_changes.csv", index=False)
    (out / "exact_clock_panel_comparison.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    # Run original Stage-6 models on this new variant and check coefficients.
    call("replay_stage6_from_frozen.py",
         ["--panel", out / "player_team_game_harmonized_cadence.csv.gz",
          "--output-dir", out / "stage6_models"])


if __name__ == "__main__":
    main()
