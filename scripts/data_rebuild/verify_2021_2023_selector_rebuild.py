#!/usr/bin/env python3
"""Strict original-source reconstruction for 2021–22 through 2023–24 selectors.

Read-only: original immutable selector function, original season manifests,
historical parser outputs (freshly reparsed 2021–22), original schedules.
The 2020/2024 generic selector needs the historical 2021–23 precedence rule:
an actual submitted row outranks a mixed 'not_yet_submitted' placeholder.
A single documented 2023–24 clean-game row-count fallback is source-derived.
Does not change the frozen archive, PDF parser or manuscript.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path

import pandas as pd

from scripts.data_rebuild.verify_canonical_selector_replay import (
    original_builder, csv_from_zip, file_sha256, member_bytes, check_metrics
)

SEASONS = ("2021-22", "2022-23", "2023-24")
PINNED = {
    "nba_canonical_snapshot_selector_v1.zip": "fa724ee6cd341b0322c311258f472f0ad7dfeeea4683cf2e406a48fe0d1f94a7",
    "audit_2021_22_upload.zip": "1e027ce6aa2a44292c3d27ba7bbfb24fcab61ded922b7ca6ba1c4211f9984339",
    "audit_2021_22_cadence_outputs.zip": "861ccc5ea82834632b6fc9c477be318aaa09ea9a243d4a990f93051af148b420",
    "audit_2021_22_s4_join_results.zip": "63d1c60a16a016dd6618813eb88a6d5f47f9d8a2093026166c715b6b9098cec9",
    "audit_2022_23_pre_s4_outputs.zip": "dd750f6f95e907ed55cf673ce08ee321062aac03b09ec79aa4abffadae94513b",
    "audit_2022_23_s4_join_results.zip": "fbbdcca334f0c904ae48f76551dc50319db346f487e90a77eacacd5839df97c6",
    "audit_2023_24_pre_s4_outputs.zip": "edd411a4dd1ad113f32492d2e9fd96a842727628566d56b9b797c3913d19abbf",
    "audit_2023_24_s4_join_results.zip": "9d59f4f0dde7aed9b8dacfd3706b55f24c1aa9a17cf1e6bdc093eb498570d5e7",
}
EXPECTED_2021_PARSER = "321d9c8d807325209fbcb6174ec6d82df4ba845c156d7d52158f0ea44714ab3e"
CADENCE_SUFFIX = ("_01PM.pdf", "_05PM.pdf", "_08PM.pdf")
METRIC_FIELDS = 13


def canonical_export_order(games, teams):
    """Preserve the historical CSV interface's deterministic tie ordering."""
    games=games.copy()
    games["tip_timestamp_utc"]=pd.to_datetime(games.tip_timestamp_utc,utc=True).map(lambda value:value.isoformat())
    games=games.sort_values(["tip_timestamp_utc","Match Number"],kind="stable").reset_index(drop=True)
    rank={key:i for i,key in enumerate(games.game_id)}
    teams=teams.copy()
    teams["_game_order"]=teams.game_id.map(rank)
    if teams["_game_order"].isna().any():
        raise ValueError("Export team references unknown game")
    teams=teams.sort_values(["_game_order","team_role"],kind="stable").drop(columns="_game_order").reset_index(drop=True)
    return games,teams


def normalized_frame_equal(candidate: pd.DataFrame, reference: pd.DataFrame,
                           keys: list[str], *, strict_schema: bool) -> dict:
    if strict_schema and set(candidate.columns) != set(reference.columns):
        raise ValueError(f"Frozen output schema changed: missing={set(reference)-set(candidate)}, extra={set(candidate)-set(reference)}")
    if not set(reference.columns) <= set(candidate.columns):
        raise ValueError(f"Frozen reference fields missing: {set(reference)-set(candidate)}")
    if candidate.duplicated(keys).any() or reference.duplicated(keys).any():
        raise ValueError(f"Duplicate game/team identity: {keys}")
    if len(candidate) != len(reference):
        raise ValueError(f"Row counts differ: {len(candidate)} versus {len(reference)}")
    candidate = candidate.set_index(keys).sort_index()
    reference = reference.set_index(keys).sort_index()
    if not candidate.index.equals(reference.index):
        raise ValueError(f"Game/team identity keys disagree: {keys}")
    discrepancies = {}
    for field in reference.columns:
        if field in keys:
            continue
        if field in ("tip_timestamp_utc", "tip_timestamp_et", "selected_snapshot_utc"):
            left = pd.to_datetime(candidate[field], utc=True).astype(str)
            right = pd.to_datetime(reference[field], utc=True).astype(str)
        else:
            left = candidate[field].astype(str).str.strip()
            right = reference[field].astype(str).str.strip()
        number = int(left.ne(right).sum())
        if number:
            discrepancies[field] = number
    if discrepancies:
        raise ValueError(f"Source-rebuilt selector differs from frozen fields: {discrepancies}")
    return {"rows": len(reference), "reference_fields_compared": len(reference.columns),
            "differences": 0, "all_reference_fields_match": True}


def verify_2021_harmonized_reference(archive_dir: Path, rows: pd.DataFrame,
                                    logs: pd.DataFrame) -> dict:
    source_zip = archive_dir / "audit_2021_22_cadence_outputs.zip"
    parser = member_bytes(source_zip, "nba_injury_fitz_parser_v3.py")
    if hashlib.sha256(parser).hexdigest() != EXPECTED_2021_PARSER:
        raise ValueError("The original 2021–22 parser bytes differ")
    ref_rows = csv_from_zip(archive_dir, ("audit_2021_22_cadence_outputs.zip",
                                         "s1_snapshot_rows_harmonized.csv"))
    ref_log = csv_from_zip(archive_dir, ("audit_2021_22_cadence_outputs.zip",
                                        "s1_parse_log_harmonized.csv"))
    if len(rows) != 398715 or len(logs) != 5567:
        raise ValueError("2021 full-hourly original-PDF reparse rows/log counts unexpected")
    if len(ref_rows) != 58631 or len(ref_log) != 696:
        raise ValueError("Frozen 2021 harmonized reference counts unexpected")
    if logs.status.astype(str).ne("ok").any() or logs.duplicated(["source_file", "snapshot_timestamp_utc"]).any():
        raise ValueError("Failed/duplicate original 2021 PDF parse logs")
    for field in ref_rows.columns:
        if field not in rows:
            raise ValueError(f"2021 full reparse missing {field}")
    chosen = set(ref_log.source_file)
    filtered = rows.loc[rows.source_file.isin(chosen), ref_rows.columns]
    selected_logs = logs.loc[logs.source_file.isin(chosen), ref_log.columns]
    def multiset(df):
        return Counter(tuple("NULL" if pd.isna(v) else str(v)
                             for v in item) for item in df.itertuples(index=False, name=None))
    if multiset(filtered) != multiset(ref_rows) or multiset(selected_logs) != multiset(ref_log):
        raise ValueError("Fresh 2021 full-hourly parser output does not reproduce frozen harmonized source")
    if len(filtered) != 58631 or len(selected_logs) != 696:
        raise ValueError("2021 selected-source PDF or row counts disagree")
    return {"total_parsed_pdfs": 5567, "total_parsed_rows": 398715,
            "harmonized_pdfs_exact": 696, "harmonized_rows_exact": 58631,
            "full_hourly_reference_available": False}


def submitted_precedence(team_rows: pd.DataFrame, raw_rows: pd.DataFrame, norm_team) -> list[str]:
    """Correct only mixed submitted+placeholder rows, using independent source evidence."""
    required = {"source_file", "matchup_norm", "team", "team_submission_status"}
    if not required <= set(raw_rows):
        raise ValueError(f"Source row columns missing: {required-set(raw_rows)}")
    confirmed = raw_rows.loc[raw_rows.team_submission_status.eq("submitted"),
                             ["source_file", "matchup_norm", "team"]].drop_duplicates()
    keys = set(zip(confirmed.source_file.astype(str).str.rsplit("/", n=1).str[-1],
                   confirmed.matchup_norm, confirmed.team.map(norm_team)))
    changed = []
    for idx, row in team_rows.loc[team_rows.team_final_status.eq("not_yet_submitted")].iterrows():
        if (row.snapshot_basename, row.matchup_norm, row.team_norm) in keys:
            team_rows.at[idx, "team_final_status"] = "submitted_with_listed_players"
            team_rows.at[idx, "usable_submitted_status"] = True
            changed.append(str(row.game_id))
    return changed


def source_snapshot_counts(rows: pd.DataFrame, manifest: pd.DataFrame,
                           season: str, panel: str, games: pd.DataFrame) -> tuple[list[int], list[int], list[str]]:
    raw = rows[["matchup_norm", "game_date_raw", "source_file", "snapshot_timestamp_utc"]].copy()
    raw["game_date_et"] = pd.to_datetime(raw.game_date_raw, format="%m/%d/%Y", errors="raise").dt.strftime("%Y-%m-%d")
    raw = raw.drop_duplicates(["matchup_norm", "game_date_et", "source_file"])
    if panel == "harmonized":
        raw = raw.loc[raw.source_file.str.endswith(CADENCE_SUFFIX)]
    raw["pub"] = pd.to_datetime(raw.snapshot_timestamp_utc, utc=True, errors="raise")
    grouped = {key: group.pub for key, group in raw.groupby(["matchup_norm", "game_date_et"], sort=False)}
    all_counts, pre_counts, fallback_ids = [], [], []
    for game in games.itertuples():
        pubs = grouped.get((game.matchup_norm, str(game.game_date_et)))
        if pubs is None:
            if (season, str(game.game_id)) != ("2023-24", "FD2023_5"):
                raise ValueError(f"Undocumented no-matchup source report game: {season}::{game.game_id}")
            fallback_ids.append(str(game.game_id))
            day = pd.Timestamp(game.game_date_et)
            nearby = {str((day - pd.Timedelta(days=1)).date()), str(day.date())}
            subset = manifest.loc[manifest.exists.astype(str).str.lower().isin(("true", "1"))
                                  & manifest.report_date.isin(nearby)]
            if panel == "harmonized":
                subset = subset.loc[subset.url_token.isin(("01PM", "05PM", "08PM"))]
            pubs = pd.to_datetime(subset.published_timestamp_utc, utc=True, errors="raise")
            if len(pubs) == 0:
                raise ValueError("Documented clean-game fallback has no original report timestamps")
        all_counts.append(len(pubs))
        pre_counts.append(int((pubs < pd.Timestamp(game.tip_timestamp_utc)).sum()))
    if set(fallback_ids) != ({"FD2023_5"} if season == "2023-24" else set()):
        raise ValueError(f"Historical clean-game source fallback set differs: {fallback_ids}")
    return all_counts, pre_counts, fallback_ids


def verify(archive_dir: Path, seasons: tuple[str, ...], rows_2021: Path | None,
           log_2021: Path | None, generated_dir: Path | None = None,
           fresh_candidate_dir: Path | None = None) -> dict:
    if not seasons or len(set(seasons)) != len(seasons) or not set(seasons) <= set(SEASONS):
        raise ValueError("Select valid unique seasons from 2021–22 through 2023–24")
    if generated_dir is not None and seasons not in (("2021-22",),("2022-23",)):
        raise ValueError("Generated downstream export currently requires 2021–22 alone")
    if generated_dir is not None and seasons==("2022-23",) and fresh_candidate_dir is None:
        raise ValueError("2022 generated selectors require fresh full candidate source")
    needed = {"nba_canonical_snapshot_selector_v1.zip"}
    generated = {}
    for season in seasons:
        stem = season.replace("-", "_")
        needed.add(f"audit_{stem}_s4_join_results.zip")
        needed.add(f"audit_{stem}_upload.zip" if season == "2021-22"
                   else f"audit_{stem}_pre_s4_outputs.zip")
        if season == "2021-22":
            needed.add("audit_2021_22_cadence_outputs.zip")
    digests = {}
    for filename in sorted(needed):
        observed = file_sha256(archive_dir / filename)
        if observed != PINNED[filename]:
            raise ValueError(f"Original archived source package SHA-256 differs: {filename}")
        digests[filename] = observed
    builder = original_builder(archive_dir / "nba_canonical_snapshot_selector_v1.zip")
    norm_team = builder.__globals__["norm_team"]
    metrics = csv_from_zip(archive_dir, ("nba_canonical_snapshot_selector_v1.zip",
                          "nba_canonical_snapshot_selector_v1/canonical_six_season_metrics.csv"))
    report = {"scope": "Original pinned selection function adapted to documented original 2021–23 status precedence; original input manifests/parsed rows/schedules; not end-to-end models",
              "original_zips_sha256_verified": digests,
              "fresh_2021_pdf_reparse": None, "panels": [], "all_replays_exact": False}
    for season in seasons:
        stem = season.replace("-", "_")
        archive_s4 = f"audit_{stem}_s4_join_results.zip"
        if season == "2021-22":
            if not rows_2021 or not log_2021:
                raise ValueError("2021 full original-PDF rows and parser log paths required")
            raw = pd.read_csv(rows_2021, low_memory=False)
            logs = pd.read_csv(log_2021, low_memory=False)
            report["fresh_2021_pdf_reparse"] = verify_2021_harmonized_reference(archive_dir, raw, logs)
            manifest = csv_from_zip(archive_dir, ("audit_2021_22_upload.zip",
                                    "audit_2021_22/report_manifest.csv"))
        else:
            pre = f"audit_{stem}_pre_s4_outputs.zip"
            prefix = f"audit_{stem}_pre_s4_outputs/" if season == "2023-24" else ""
            manifest = csv_from_zip(archive_dir, (pre, prefix + "report_manifest_regular_season.csv"))
            raw = csv_from_zip(archive_dir, (pre, prefix + "s1_snapshot_rows_regular_season.csv"))
            if season=="2022-23" and fresh_candidate_dir is not None:
                from scripts.data_rebuild.rebuild_2021_full_candidates import verify_2022_reference
                accepted=json.loads((fresh_candidate_dir/"candidate_acceptance.json").read_text())
                rows_2021=fresh_candidate_dir/"full_candidate_rows.csv"
                log_2021=fresh_candidate_dir/"full_candidate_parse_log.csv"
                if (accepted.get("status")!="pass" or accepted.get("season")!="2022-23"
                        or accepted.get("fresh_original_PDF_execution") is not True
                        or file_sha256(rows_2021)!=accepted.get("full_candidate_rows_sha256")
                        or file_sha256(log_2021)!=accepted.get("full_candidate_log_sha256")):
                    raise ValueError("2022 fresh source provenance missing or hash differs")
                raw=pd.read_csv(rows_2021,low_memory=False)
                logs=pd.read_csv(log_2021)
                report["fresh_2022_pdf_reparse"]=verify_2022_reference(archive_dir,raw,logs)
        schedule = csv_from_zip(archive_dir, (archive_s4, f"s4_games_{stem}_normalized.csv"))
        if len(schedule) != 1230:
            raise ValueError(f"Expected 1,230 NBA games in {season}")
        for panel, tokens, name in (("full", None, "full_canonical"),
                                     ("harmonized", ["01PM", "05PM", "08PM"],
                                      "harmonized_0130_1730_2030")):
            games, teams, initial_metrics = builder(season, io.StringIO(schedule.to_csv(index=False)),
                                                    manifest, raw, tokens, name)
            if len(games) != 1230 or len(teams) != 2460:
                raise ValueError(f"Unexpected {season}/{panel} game/team count")
            mixed = submitted_precedence(teams, raw, norm_team)
            team_usable = teams.groupby("game_id").usable_submitted_status.sum()
            games["usable_team_games"] = games.game_id.map(team_usable).astype(int)
            games["not_submitted_team_games"] = 2 - games.usable_team_games
            games["both_teams_usable"] = games.usable_team_games.eq(2)
            count_all, count_pre, fallbacks = source_snapshot_counts(raw, manifest, season, panel, games)
            games["n_all_linked_snapshots"] = count_all
            games["n_pre_tip_linked_snapshots"] = count_pre
            games = games.rename(columns={"away_team": "Away Team", "home_team": "Home Team",
                                          "location": "Location", "result": "Result"})
            original_game = csv_from_zip(archive_dir,
                           ("nba_canonical_snapshot_selector_v1.zip",
                            f"nba_canonical_snapshot_selector_v1/{season}_game_snapshot_join_{panel}_canonical.csv"))
            game_result = normalized_frame_equal(games, original_game, ["game_id"], strict_schema=True)
            teams["team_final_status"] = teams.team_final_status.replace(
                 {"submitted_with_listed_players": "submitted"})
            teams["panel"] = "full_hourly" if panel == "full" else "harmonized_01PM_05PM_08PM"
            original_team = csv_from_zip(archive_dir,
                 (archive_s4, f"team_game_final_pre_tip_status_{panel}.csv"))
            team_result = normalized_frame_equal(teams, original_team,
                                                  ["game_id", "team_role"], strict_schema=False)
            actual_metric = dict(initial_metrics)
            actual_metric["usable_team_games"] = int(teams.usable_submitted_status.sum())
            actual_metric["usable_team_game_pct"] = float(teams.usable_submitted_status.mean() * 100)
            actual_metric["not_yet_submitted_team_games"] = int(
                 teams.team_final_status.eq("not_yet_submitted").sum())
            actual_metric["games_both_teams_usable"] = int(games.both_teams_usable.sum())
            actual_metric["both_teams_usable_pct"] = float(games.both_teams_usable.mean() * 100)
            reference_metric = metrics.loc[(metrics.season == season) & (metrics.panel == name)]
            if len(reference_metric) != 1:
                raise ValueError(f"Missing or duplicate original metric row {season}/{name}")
            metric_result = check_metrics(actual_metric, reference_metric.iloc[0])
            if generated_dir is not None:
                canonical_team = (original_team if season=="2022-23" else csv_from_zip(archive_dir,
                    ("nba_canonical_snapshot_selector_v1.zip",
                     f"nba_canonical_snapshot_selector_v1/{season}_team_game_status_{panel}_canonical.csv")))
                computed_team = teams.copy()
                if season!="2022-23":
                    computed_team["panel"] = name
                    computed_team["selector_version"] = "canonical_v1_latest_verified_pdf_strictly_before_tip"
                computed_team = computed_team[list(canonical_team.columns)]
                normalized_frame_equal(computed_team, canonical_team, ["game_id","team_role"], strict_schema=True)
                export_games,export_teams=canonical_export_order(games,computed_team)
                export_games=export_games[list(original_game.columns)]
                generated[f"{season}_game_snapshot_join_{panel}_canonical.csv"] = export_games
                generated[f"{season}_team_game_status_{panel}_canonical.csv"] = export_teams
            assert metric_result["metrics_compared"] == METRIC_FIELDS
            report["panels"].append({
                "season": season, "panel": panel,
                "game": game_result, "team": team_result, "metrics": metric_result,
                "mixed_submitted_placeholder_team_rows": len(mixed),
                "mixed_placeholder_game_ids": sorted(set(mixed)),
                "clean_game_source_fallback_ids": fallbacks,
            })
    report["all_replays_exact"] = True
    if generated_dir is not None:
        if generated_dir.exists() or archive_dir.resolve() in generated_dir.resolve().parents:
            raise ValueError("Generated selector directory must be fresh and outside original archives")
        generated_dir.mkdir(parents=True)
        report["generated_files"] = {}
        for name, frame in generated.items():
            path=generated_dir/name
            # The original 2022 S4 csv.writer output used CRLF.
            frame.to_csv(path,index=False,lineterminator="\r\n" if name.startswith("2022-23_team_") else "\n")
            report["generated_files"][name]={"rows":len(frame),"sha256":file_sha256(path)}
        if seasons in (("2021-22",),("2022-23",)):
            is2022=seasons==("2022-23",)
            reference_log = csv_from_zip(archive_dir,(
                "audit_2022_23_pre_s4_outputs.zip" if is2022 else "audit_2021_22_cadence_outputs.zip",
                "s1_parse_log_regular_season.csv" if is2022 else "s1_parse_log_harmonized.csv"))
            harmonized = raw.loc[raw.source_file.isin(set(reference_log.source_file))].copy()
            if reference_log.source_file.duplicated().any():
                raise ValueError("Duplicate original parse-log source ordering")
            # Archived parser workers completed out of chronological order.
            # Reuse only their source-file sequence, never archived row values.
            rank={name:i for i,name in enumerate(reference_log.source_file)}
            harmonized["_source_order"]=harmonized.source_file.map(rank)
            harmonized=harmonized.sort_values("_source_order",kind="stable").drop(columns="_source_order")
            report["historical_source_file_order_inherited_from_parse_log"]=True
            path=generated_dir/("2022-23_fresh_candidate_rows.csv" if is2022 else "2021-22_fresh_harmonized_rows.csv")
            harmonized.to_csv(path,index=False)
            report["generated_files"][path.name]={"rows":len(harmonized),"sha256":file_sha256(path)}
            report["full_candidate_rows_sha256"]=file_sha256(rows_2021)
            report["full_candidate_log_sha256"]=file_sha256(log_2021)
        (generated_dir/"selector_acceptance.json").write_text(json.dumps(report,indent=2)+"\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir", type=Path, required=True)
    p.add_argument("--seasons", nargs="+", choices=SEASONS, default=list(SEASONS))
    p.add_argument("--reparsed-2021-rows", type=Path)
    p.add_argument("--reparsed-2021-log", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--generated-dir", type=Path)
    p.add_argument("--fresh-candidate-dir", type=Path)
    a = p.parse_args()
    report = verify(a.archive_dir, tuple(a.seasons),
                    a.reparsed_2021_rows, a.reparsed_2021_log,a.generated_dir,a.fresh_candidate_dir)
    result = json.dumps(report, indent=2) + "\n"
    if a.output:
        if a.output.exists():
            raise FileExistsError(f"Refusing to overwrite historical acceptance record: {a.output}")
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(result, encoding="utf-8")
    print(result, end="")


if __name__ == "__main__":
    main()
