"""Reconstruct selection/status from saved 2025 inventory and fresh PDF bodies."""
import io
import json
from pathlib import Path
import pandas as pd
from scripts.data_rebuild.rebuild_2025_full_candidates import inventory,S4_ZIP,S4_SHA
from scripts.data_rebuild.rebuild_2020_selected_from_pdfs import safe_output
from scripts.data_rebuild.verify_2025_manifest_selector import (
    CADENCE_SUFFIX,select_from_inventory,compare_selection,read_member,
)
from scripts.data_rebuild.verify_canonical_selector_replay import original_builder,csv_from_zip,file_sha256,check_metrics
from scripts.data_rebuild.verify_2021_2023_selector_rebuild import (
    submitted_precedence,source_snapshot_counts,normalized_frame_equal,canonical_export_order,
)


def date_matched_status_rows(raw,selection,schedule):
    """Diagnostic source join using report date, PDF and matchup; missing dates stay missing."""
    linked=selection[["game_id","basename"]].merge(
        schedule[["game_id","matchup_norm","game_date_et"]],on="game_id",validate="one_to_one")
    linked=linked[["basename","matchup_norm","game_date_et"]].drop_duplicates()
    candidate=raw.copy()
    candidate["basename"]=candidate.source_file.map(lambda name:Path(name).name)
    candidate["game_date_et"]=pd.to_datetime(candidate.game_date_raw,format="%m/%d/%Y",errors="raise").dt.strftime("%Y-%m-%d")
    matched=candidate.merge(linked,on=["basename","matchup_norm","game_date_et"],how="inner",validate="many_to_one")
    return matched[list(raw.columns)]


def archived_metadata_inconsistencies(games,teams):
    if games.game_id.duplicated().any() or teams.duplicated(["game_id","team_role"]).any():
        raise ValueError("Duplicate archived game/team identity")
    total=teams.groupby("game_id").inferred_no_listed_players.sum()
    observed=games.game_id.map(total)
    if observed.isna().any():raise ValueError("Archived team identity missing for a game")
    return int(observed.ne(games.inferred_clean_teams).sum())


def generate(archives,source,output,prior_parse_log=None,audit_only=False,diagnostic_frames=None):
    if diagnostic_frames is not None and not audit_only:
        raise ValueError("Diagnostic frames require explicit audit-only mode")
    archives,source,output=archives.resolve(),source.resolve(),output.resolve()
    safe_output(archives,output)
    safe_output(source,output)
    if output.exists():raise FileExistsError(output)
    if file_sha256(archives/S4_ZIP)!=S4_SHA:raise ValueError("Original 2025 S4 schedule ZIP differs")
    report=json.loads((source/"candidate_acceptance.json").read_text())
    for filename,key in (("full_candidate_rows.csv","full_candidate_rows_sha256"),
                         ("full_candidate_parse_log.csv","full_candidate_log_sha256"),
                         ("candidate_inventory.csv","candidate_inventory_sha256")):
        path=source/filename
        if path.is_symlink() or not path.is_file() or file_sha256(path)!=report.get(key):
            raise ValueError("Fresh 2025 source provenance hash differs")
    if (report.get("status")!="pass" or report.get("pdfs")!=5023 or report.get("rows")!=599225
            or report.get("fresh_original_PDF_execution") is not True):
        raise ValueError("Complete saved 2025 candidate parse required")
    meta=inventory(archives)
    raw=pd.read_csv(source/"full_candidate_rows.csv",low_memory=False)
    if len(raw)!=599225:raise ValueError("Fresh 2025 candidate rows incomplete")
    schedule=read_member(archives/S4_ZIP,"s4_games_2025_26_normalized.csv")
    builder=original_builder(archives/"nba_canonical_snapshot_selector_v1.zip")
    metrics=csv_from_zip(archives,("nba_canonical_snapshot_selector_v1.zip",
                                 "nba_canonical_snapshot_selector_v1/canonical_six_season_metrics.csv"))
    frames={};cases=[];selected_names=None
    def compare(a,b,keys):
        try:
            return normalized_frame_equal(a,b,keys,strict_schema=True)
        except ValueError as error:
            if not audit_only:raise
            left,right=a.set_index(keys).sort_index(),b.set_index(keys).sort_index()
            if not left.index.equals(right.index) or set(left)!=set(right):raise
            differences={}
            for column in left:
                x,y=left[column],right[column]
                if column in ("tip_timestamp_utc","tip_timestamp_et","selected_snapshot_utc"):
                    x=pd.to_datetime(x,utc=True).astype(str);y=pd.to_datetime(y,utc=True).astype(str)
                else:x=x.astype(str).str.strip();y=y.astype(str).str.strip()
                count=int(x.ne(y).sum())
                if count:differences[column]=count
            return {"rows":len(a),"accepted":False,"different_cells_by_field":differences,
                    "strict_comparison_error":str(error)}
    for panel,label in (("full","full_canonical"),("harmonized","harmonized_0130_1730_2030")):
        eligible=meta if panel=="full" else meta.loc[meta.basename.str.endswith(CADENCE_SUFFIX)]
        if len(eligible)!=(5023 if panel=="full" else 507):
            raise ValueError("Saved 2025 cadence candidate inventory differs")
        independent=select_from_inventory(eligible,schedule)
        original_game=csv_from_zip(archives,("nba_canonical_snapshot_selector_v1.zip",
            f"nba_canonical_snapshot_selector_v1/2025-26_game_snapshot_join_{panel}_canonical.csv"))
        selection=compare_selection(independent,original_game,panel)
        manifest=eligible.rename(columns={"published":"published_timestamp_utc"}).copy()
        manifest["exists"]=True
        status_rows=date_matched_status_rows(raw,independent,schedule)
        games,teams,met=builder("2025-26",io.StringIO(schedule.to_csv(index=False)),manifest,status_rows,None,label)
        mixed=submitted_precedence(teams,status_rows,builder.__globals__["norm_team"])
        usable=teams.groupby("game_id").usable_submitted_status.sum()
        games["usable_team_games"]=games.game_id.map(usable).astype(int)
        games["not_submitted_team_games"]=2-games.usable_team_games
        games["both_teams_usable"]=games.usable_team_games.eq(2)
        all_counts,pre_counts,_=source_snapshot_counts(raw,manifest,"2025-26",panel,games,CADENCE_SUFFIX)
        games["n_all_linked_snapshots"]=all_counts;games["n_pre_tip_linked_snapshots"]=pre_counts
        regimes=meta.set_index("basename").source.map({"initial":"hourly","targeted":"quarter_hour_targeted"})
        games["snapshot_cadence_regime"]=games.snapshot_basename.map(regimes)
        teams["snapshot_cadence_regime"]=teams.snapshot_basename.map(regimes)
        teams["team_final_status"]=teams.team_final_status.replace({"submitted_with_listed_players":"submitted"})
        original_team=csv_from_zip(archives,("nba_canonical_snapshot_selector_v1.zip",
            f"nba_canonical_snapshot_selector_v1/2025-26_team_game_status_{panel}_canonical.csv"))
        games,teams=canonical_export_order(games,teams)
        games=games.rename(columns={"away_team":"Away Team","home_team":"Home Team",
                                    "location":"Location","result":"Result"})
        games=games[list(original_game)];teams=teams[list(original_team)]
        game_check=compare(games,original_game,["game_id"])
        team_check=compare(teams,original_team,["game_id","team_role"])
        met.update(usable_team_games=int(teams.usable_submitted_status.sum()),
                   usable_team_game_pct=float(teams.usable_submitted_status.mean()*100),
                   not_yet_submitted_team_games=int(teams.team_final_status.eq("not_yet_submitted").sum()),
                   games_both_teams_usable=int(games.both_teams_usable.sum()),
                   both_teams_usable_pct=float(games.both_teams_usable.mean()*100))
        try:
            metric_check=check_metrics(met,metrics.loc[metrics.season.eq("2025-26") & metrics.panel.eq(label)].iloc[0])
        except ValueError as error:
            if not audit_only:raise
            metric_check={"accepted":False,"strict_comparison_error":str(error)}
        inconsistent=archived_metadata_inconsistencies(original_game,original_team)
        cases.append({"panel":panel,"selection":selection,"game":game_check,"team":team_check,
                      "metrics":metric_check,"mixed_submitted_placeholder_rows":len(mixed),
                      "archived_games_with_inconsistent_game_team_inferred_clean_counts":inconsistent})
        frames[f"2025-26_game_snapshot_join_{panel}_canonical.csv"]=games
        frames[f"2025-26_team_game_status_{panel}_canonical.csv"]=teams
        if panel=="harmonized":selected_names=set(games.snapshot_basename)
    if len(selected_names)!=355:raise ValueError("2025 selected PDF count differs")
    if audit_only:
        blocked=any(case[key].get("accepted") is False for case in cases for key in ("game","team","metrics"))
        result={"status":"blocked_legacy_team_metadata" if blocked else "source_comparisons_pass",
                "all_replays_exact":not blocked,"cases":cases,
                "full_candidate_rows_sha256":report["full_candidate_rows_sha256"],
                "no_generated_selector_tables_accepted_or_substituted":True,
                "original_S4_team_join_program_not_recovered":True}
        output.mkdir(parents=True)
        (output/"source_selection_audit.json").write_text(json.dumps(result,indent=2)+"\n")
        if diagnostic_frames is not None:
            diagnostic_frames.update(frames)
        return result
    chosen=raw.loc[raw.source_file.map(lambda name:Path(name).name).isin(selected_names)].copy()
    if prior_parse_log is not None:
        log=pd.read_csv(prior_parse_log)
        if log.source_file.duplicated().any() or set(log.source_file)!=selected_names or not log.status.eq("ok").all():
            raise ValueError("Historical source-file ordering log differs from newly reconstructed selection")
        if int(log.extracted_rows.sum())!=len(chosen):
            raise ValueError("Fresh selected 2025 PDF rows differ from original parse counts")
        clocks=meta.set_index("basename").published
        if not pd.to_datetime(log.snapshot_timestamp_utc,utc=True).reset_index(drop=True).equals(
                log.source_file.map(clocks).reset_index(drop=True)):
            raise ValueError("Historical parser log clocks differ from newly reconstructed selection")
        ranks={name:i for i,name in enumerate(log.source_file)}
        chosen["_rank"]=chosen.source_file.map(lambda name:ranks[Path(name).name])
        chosen=chosen.sort_values("_rank",kind="stable").drop(columns="_rank")
    frames["2025-26_fresh_candidate_rows.csv"]=chosen
    output.mkdir(parents=True)
    result={"all_replays_exact":True,"cases":cases,"generated_files":{},
            "full_candidate_rows_sha256":report["full_candidate_rows_sha256"],
            "full_candidate_log_sha256":report["full_candidate_log_sha256"],
            "historical_source_file_order_inherited_from_parse_log":prior_parse_log is not None,
            "original_saved_candidate_selection_reconstructed":True,
            "missing_unsaved_quarter_hour_reports_not_invented":True}
    for name,frame in frames.items():
        path=output/name;frame.to_csv(path,index=False)
        result["generated_files"][name]={"rows":len(frame),"sha256":file_sha256(path)}
    (output/"selector_acceptance.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir",type=Path,required=True)
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--audit-only",action="store_true")
    a=p.parse_args()
    result=generate(a.archive_dir,a.source_dir,a.output_dir,audit_only=a.audit_only)
    print(json.dumps(result,indent=2))
    if result.get("all_replays_exact") is not True:raise SystemExit(2)


if __name__=="__main__":main()
