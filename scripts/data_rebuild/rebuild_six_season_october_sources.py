"""Connect existing six original-PDF parsers/selectors to actual October inputs.

Scientific-output acceptance and historical-artifact equivalence are separate.
Only the explicitly documented 2025 two-field metadata exception is allowed.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from scripts.data_rebuild.rebuild_2020_selected_from_pdfs import rebuild as parse_2020, FULL_SOURCE_FILE, safe_output
from scripts.data_rebuild.rebuild_2021_full_candidates import rebuild as parse_recent
from scripts.data_rebuild.rebuild_2025_full_candidates import rebuild as parse_2025, S4_ZIP, S4_SHA
from scripts.data_rebuild.verify_canonical_selector_replay import verify as select_2020, csv_from_zip, file_sha256
from scripts.data_rebuild.verify_2021_2023_selector_rebuild import verify as select_recent, PINNED
from scripts.data_rebuild.generate_2024_selector_inputs import generate as select_2024
from scripts.data_rebuild.generate_2025_selector_inputs import generate as audit_2025
from scripts.data_rebuild.inject_generated_canonical_selectors import inject as inject_2020, RAW_2020_TARGET, RELATIVE
from scripts.data_rebuild.inject_2021_generated_inputs import input_files
from scripts.data_rebuild.experiment_2025_team_metadata import require_team_only_difference, GAME, TEAM, ROWS, tree_hashes, panel_summary, FROZEN_HASH
from scripts.data_rebuild.restore_historical_layout import build_plan, restore
from scripts.data_rebuild.run_historical_cadence_builder import verify_required_inputs

SEASONS=("2020-21","2021-22","2022-23","2023-24","2024-25","2025-26")
EXTRA_ZIPS={"audit_2021_22_s4_join_results.zip":PINNED["audit_2021_22_s4_join_results.zip"],S4_ZIP:S4_SHA}
EXPERIMENT_SHA="9b7aaa38fd70ecad43d0056884a2f777ebd5a5e549161b763428ad55b056fc4e"
EXPECTED_COUNTS={"2020-21":(617,41780),"2021-22":(5567,398715),"2022-23":(4101,354146),
                 "2023-24":(4097,388878),"2024-25":(4078,418059),"2025-26":(5023,599225)}


def save(path,data):
    path.write_text(json.dumps(data,indent=2)+"\n")


def originals(archives):
    from scripts.data_rebuild.reproduce_final_datasets import SOURCE_HASHES, SELECTOR_SCHEDULE_EXTRA_ZIPS
    expected=SOURCE_HASHES|SELECTOR_SCHEDULE_EXTRA_ZIPS|EXTRA_ZIPS
    for name,digest in expected.items():
        path=archives/name
        if path.is_symlink() or not path.is_file() or file_sha256(path)!=digest:
            raise ValueError("Original six-season archive missing or SHA differs: "+name)
    return expected


def controlled_exception():
    path=Path(__file__).resolve().parents[2]/"validation/2025_team_metadata_experiment_2026-11-15/experiment_acceptance.json"
    if file_sha256(path)!=EXPERIMENT_SHA:
        raise ValueError("Accepted controlled 2025 experiment evidence differs")
    evidence=json.loads(path.read_text())
    if (evidence.get("status")!="pass" or not evidence["corrected_models"]["scientific_model_cells_exact"]
            or not evidence["corrected_panel"]["exact_decoded_bytes"]
            or evidence.get("historical_team_artifact_equivalence") is not False):
        raise ValueError("No accepted scientific-output-only 2025 exception")
    return {"fields":["team_final_status","inferred_no_listed_players"],"differing_rows_per_panel":1598,
            "controlled_experiment_evidence_sha256":EXPERIMENT_SHA,"historical_artifact_equivalence":False,
            "original_S4_team_join_recovered":False,"archived_values_substituted_for_generated_values":False}


def generate_2025(archives,source,output):
    frames={}
    audit=audit_2025(archives,source,output/"audit",audit_only=True,diagnostic_frames=frames)
    if audit.get("status")!="blocked_legacy_team_metadata":
        raise ValueError("Known 2025 metadata exception changed; inspect before acceptance")
    exception=controlled_exception(); generated={}; comparisons={}
    for panel in ("full","harmonized"):
        for kind in ("game_snapshot_join","team_game_status"):
            name=f"2025-26_{kind}_{panel}_canonical.csv"
            original=csv_from_zip(archives,("nba_canonical_snapshot_selector_v1.zip","nba_canonical_snapshot_selector_v1/"+name))
            frame=frames[name]
            keys=["game_id","team_role"] if kind=="team_game_status" else ["game_id"]
            if frame.duplicated(keys).any():raise ValueError("Duplicate fresh 2025 identity")
            frame=frame.set_index(keys).reindex(pd.MultiIndex.from_frame(original[keys]) if len(keys)>1 else original.game_id).reset_index()
            frame=frame[list(original)]
            dst=output/name;frame.to_csv(dst,index=False)
            if kind=="team_game_status":
                ref=output/(name+".historical-reference.csv");original.to_csv(ref,index=False)
                comparisons[name]=require_team_only_difference(ref,dst)
            generated[name]={"sha256":file_sha256(dst),"rows":len(frame)}
    names=set(frames[Path(GAME).name].snapshot_basename)
    raw=pd.read_csv(source/"full_candidate_rows.csv",low_memory=False)
    chosen=raw.loc[raw.source_file.map(lambda x:Path(x).name).isin(names)]
    if len(names)!=355 or set(chosen.source_file.map(lambda x:Path(x).name))!=names:
        raise ValueError("Incomplete fresh 2025 selected source set")
    name="2025-26_fresh_candidate_rows.csv";chosen.to_csv(output/name,index=False)
    generated[name]={"sha256":file_sha256(output/name),"rows":len(chosen)}
    report={"source_inputs_ready":True,"historical_artifact_equivalence":False,"exception":exception,
            "metadata_comparisons":comparisons,"generated_files":generated,
            "full_candidate_rows_sha256":file_sha256(source/"full_candidate_rows.csv")}
    save(output/"scientific_source_handoff.json",report)
    return report


def checked_season(record):
    source=Path(record["source"]); generated=Path(record["generated"])
    if (not source.is_dir() or not generated.is_dir() or source.is_symlink() or generated.is_symlink()
            or not record.get("source_sha256") or not record.get("generated_sha256")
            or tree_hashes(source)!=record["source_sha256"] or tree_hashes(generated)!=record["generated_sha256"]):
        raise ValueError("Generated season source/selector changed or missing")
    return source,generated


def build(archives,output,*,fresh_2020=None,resume=False):
    archives,output=archives.resolve(),output.resolve()
    expected=originals(archives);controlled_exception()
    if not resume:safe_output(archives,output);output.mkdir(parents=True)
    elif not output.is_dir() or output.is_symlink():raise ValueError("Invalid source-stage resume directory")
    cases={}
    for season in SEASONS:
        checkpoint=output/(season+".ready.json")
        if checkpoint.exists():
            if not resume:raise FileExistsError(checkpoint)
            record=json.loads(checkpoint.read_text());checked_season(record);cases[season]=record;continue
        source=(fresh_2020.resolve() if fresh_2020 and season=="2020-21" else output/(season+"_source"))
        generated=output/(season+"_selectors")
        if season=="2020-21":
            if not fresh_2020:parse_2020(archives,source,emit_full_source_rows=True)
            select_2020(archives,generated_dir=generated,fresh_2020_rows=source/FULL_SOURCE_FILE,
                        fresh_2020_acceptance=source/"2020_21_original_pdf_source_acceptance.json")
        elif season=="2025-26":
            parse_2025(archives,source);generate_2025(archives,source,generated)
        else:
            parse_recent(archives,source,season=season)
            if season=="2024-25":select_2024(archives,source,generated)
            else:select_recent(archives,(season,),source/"full_candidate_rows.csv",source/"full_candidate_parse_log.csv",generated,
                               fresh_candidate_dir=source if season!="2021-22" else None)
        record={"season":season,"source":str(source),"generated":str(generated),
                "source_sha256":tree_hashes(source),"generated_sha256":tree_hashes(generated),
                "pdfs":EXPECTED_COUNTS[season][0],"rows":EXPECTED_COUNTS[season][1]}
        save(checkpoint,record);cases[season]=record
    result={"all_six_source_inputs_ready":True,"cases":cases,"original_archive_sha256":expected,
            "scientific_output_acceptance":False,"historical_artifact_equivalence":False,
            "metadata_only_exception":controlled_exception(),"publication_acquisition_metadata_inherited":True}
    save(output/"six_season_sources.json",result)
    return result


def inject(archives,sources,historical):
    from scripts.data_rebuild.reproduce_final_datasets import under_git
    if any(p.is_symlink() or under_git(p) for p in (archives,sources,historical)):
        raise ValueError("Private source handoff roots must be real and outside Git")
    archives,sources,historical=(p.resolve() for p in (archives,sources,historical))
    if sources==historical or sources in historical.parents or historical in sources.parents:
        raise ValueError("Generated sources and historical input roots must be disjoint")
    originals(archives);exception=controlled_exception()
    report=json.loads((sources/"six_season_sources.json").read_text())
    if report.get("all_six_source_inputs_ready") is not True or set(report.get("cases",{}))!=set(SEASONS):
        raise ValueError("All six original-PDF source stages are required; no archived fallback")
    cases={s:checked_season(report["cases"][s]) for s in SEASONS}
    records={};paths=[]
    records["2020-21"]=inject_2020(cases["2020-21"][1],historical,historical/"generated_selector_handoff.json",require_raw_2020=True)
    paths.extend([str(RAW_2020_TARGET),str(RELATIVE/"2020-21_game_snapshot_join_harmonized_canonical.csv"),str(RELATIVE/"2020-21_team_game_status_harmonized_canonical.csv")])
    # The existing 2020 helper also checks/transiently stages historical 2024
    # selectors. They are replaced by fresh 2024 sources BEFORE any builder runs.
    for season in SEASONS[1:5]:
        source,generated=cases[season]
        report_path=historical/(season+"_generated_source_handoff.json")
        # Release each season's CSV comparison allocations before starting the
        # next. Scientific comparisons remain the existing original handoff.
        subprocess.run([sys.executable,"-m","scripts.data_rebuild.inject_2021_generated_inputs",
                        "--generated-dir",str(generated),"--source-dir",str(source),
                        "--historical-root",str(historical),"--season",season,"--report",str(report_path)],
                       cwd=Path(__file__).resolve().parents[2],check=True)
        records[season]=json.loads(report_path.read_text())
        paths.extend(str(x) for x in input_files(season).values())
    source,generated=cases["2025-26"]
    provenance=json.loads((generated/"scientific_source_handoff.json").read_text())
    raw=json.loads((source/"candidate_acceptance.json").read_text())
    if (raw.get("status")!="pass" or raw.get("fresh_original_PDF_execution") is not True
            or raw.get("pdfs")!=5023 or raw.get("rows")!=599225
            or raw.get("full_candidate_rows_sha256")!=file_sha256(source/"full_candidate_rows.csv")
            or raw.get("full_candidate_rows_sha256")!=provenance.get("full_candidate_rows_sha256")):
        raise ValueError("2025 complete original-PDF source provenance differs")
    if provenance.get("exception")!=exception or not provenance.get("source_inputs_ready"):
        raise ValueError("2025 scientific exception provenance differs")
    destinations={Path(GAME).name:GAME,Path(TEAM).name:TEAM,"2025-26_fresh_candidate_rows.csv":ROWS}
    # Re-check the documented metadata mismatch against the ACTUAL builder input.
    require_team_only_difference(historical/TEAM,generated/Path(TEAM).name)
    if (historical/ROWS).exists():raise ValueError("2025 archived parsed-row fallback is forbidden in six-season mode")
    for name,dest in destinations.items():
        src=generated/name
        if file_sha256(src)!=provenance["generated_files"][name]["sha256"]:
            raise ValueError("Fresh 2025 generated input hash differs")
        target=historical/dest
        if target.is_symlink():raise ValueError("Symlinked source destination")
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_name(target.name+".six-source.tmp")
        with src.open("rb") as left,temporary.open("xb") as right:shutil.copyfileobj(left,right)
        if file_sha256(temporary)!=file_sha256(src):raise ValueError("Source changed during handoff")
        temporary.replace(target);paths.append(dest)
    if len(paths)!=18 or len(set(paths))!=18:raise ValueError("Incomplete six-season actual input inventory")
    required={p:file_sha256(historical/p) for p in paths}
    verify_required_inputs(historical,required)
    result={"all_six_source_inputs_injected":True,"required_input_sha256":required,"season_handoffs":records,
            "legacy_2020_helper_transient_2024_tables_replaced_before_any_builder":True,
            "metadata_only_exception":exception,"scientific_output_acceptance":False,
            "historical_artifact_equivalence":False,"source_manifest_sha256":file_sha256(sources/"six_season_sources.json")}
    save(historical/"six_season_required_inputs.json",required)
    save(historical/"six_season_source_handoff.json",result)
    return result


def consumption(historical,builder_output):
    handoff=json.loads((historical/"six_season_source_handoff.json").read_text())
    wanted=handoff.get("required_input_sha256",{})
    if len(wanted)!=18 or handoff.get("all_six_source_inputs_injected") is not True:
        raise ValueError("Missing complete six-season handoff")
    verify_required_inputs(historical,wanted)
    actual=json.loads((builder_output/"replay_environment.json").read_text())["generated_input_consumption"]
    if actual.get("required_sha256")!=wanted or set(actual.get("original_builder_opened_paths",[]))!=set(wanted) or actual.get("pre_and_post_execution_hashes_match") is not True:
        raise ValueError("Original builder did not consume all 18 generated inputs")
    return actual


def cumulative(archives,sources,output):
    orchestrator_sha256=file_sha256(Path(__file__))
    archives,sources,output=archives.resolve(),sources.resolve(),output.resolve()
    safe_output(archives,output);safe_output(sources,output);originals(archives)
    output.mkdir(parents=True);historical=output/"historical_inputs"
    restore(archives,historical,build_plan(archives));handoff=inject(archives,sources,historical)
    from scripts.data_rebuild.reproduce_final_datasets import TOOLS
    cmd=[sys.executable,str(TOOLS/"run_historical_cadence_builder.py"),"--historical-root",str(historical),"--output",str(output/"october"),
         "--required-input-hashes",str(historical/"six_season_required_inputs.json")]
    with (output/"builder.log").open("w") as log:
        subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
    opened=consumption(historical,output/"october")
    summary=panel_summary(output/"october/player_team_game_harmonized_cadence.csv.gz")
    if summary["decoded_sha256"]!=FROZEN_HASH:raise ValueError("Cumulative scientific panel decoded hash differs")
    if file_sha256(Path(__file__))!=orchestrator_sha256:raise ValueError("Orchestrator changed during cumulative execution")
    revision=subprocess.run(["git","rev-parse","HEAD"],cwd=Path(__file__).resolve().parents[2],capture_output=True,text=True)
    result={"scientific_output_verdict":"pass","historical_artifact_verdict":"2025_metadata_exception_unresolved",
            "orchestrator_sha256":orchestrator_sha256,"repository_head":revision.stdout.strip() if revision.returncode==0 else None,
            "all_six_original_PDF_sources_consumed":True,"panel":summary,"actual_consumption":opened,
            "handoff":handoff,"command":cmd,"corrected_final_datasets_rebuilt":False}
    save(output/"cumulative_acceptance.json",result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="action",required=True)
    for name in ("build","inject","cumulative"):
        q=sub.add_parser(name);q.add_argument("--archive-dir",type=Path,required=True)
        if name=="build":
            q.add_argument("--output-dir",type=Path,required=True);q.add_argument("--fresh-2020-source-dir",type=Path);q.add_argument("--resume",action="store_true")
        else:
            q.add_argument("--sources-dir",type=Path,required=True)
            q.add_argument("--historical-root" if name=="inject" else "--output-root",type=Path,required=True)
    a=p.parse_args()
    if a.action=="build":result=build(a.archive_dir,a.output_dir,fresh_2020=a.fresh_2020_source_dir,resume=a.resume)
    elif a.action=="inject":result=inject(a.archive_dir,a.sources_dir,a.historical_root)
    else:result=cumulative(a.archive_dir,a.sources_dir,a.output_root)
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
