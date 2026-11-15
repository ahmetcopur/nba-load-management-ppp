"""Authentic control/experimental test of two disputed 2025 team fields.

This is scientific-output equivalence, NOT historical selector acceptance.
Both conditions use fresh 2025 PDF rows; other seasons inherit pinned inputs.
Private checkpoints allow explicit --resume without trusting altered files.
"""
import argparse
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from scripts.data_rebuild.accept_2020_raw_selector_downstream import decoded_hash, FROZEN_HASH
from scripts.data_rebuild.generate_2025_selector_inputs import generate
from scripts.data_rebuild.rebuild_2020_selected_from_pdfs import safe_output
from scripts.data_rebuild.rebuild_2025_full_candidates import S4_ZIP, S4_SHA
from scripts.data_rebuild.reproduce_final_datasets import SOURCE_HASHES, TOOLS, verify_model_report
from scripts.data_rebuild.restore_historical_layout import build_plan, restore, SELECTOR_DEST
from scripts.data_rebuild.run_historical_cadence_builder import PRE_MODEL_OUTPUTS, SCRIPT
from scripts.data_rebuild.verify_canonical_selector_replay import file_sha256

BUILDER_SHA = "81cab67185083572051b44cefbf836acfe6e1860ccf27dd812dc3729aa2a9272"
CORRECTED_SHA = "2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67"
TEAM = SELECTOR_DEST + "/2025-26_team_game_status_harmonized_canonical.csv"
GAME = SELECTOR_DEST + "/2025-26_game_snapshot_join_harmonized_canonical.csv"
ROWS = "cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv"
DISPUTED = {"team_final_status", "inferred_no_listed_players"}


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+"\n")


def tree_hashes(root):
    result = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("Input/output tree symlink is not permitted")
        if path.is_file():
            result[str(path.relative_to(root))] = file_sha256(path)
    return result


def compare_csv(left, right, keys=None):
    """Complete string-cell comparisons, separately from decoded-byte equality."""
    a = pd.read_csv(left, dtype=str, keep_default_na=False)
    b = pd.read_csv(right, dtype=str, keep_default_na=False)
    result = {"control_decoded_sha256": decoded_hash(left), "experimental_decoded_sha256": decoded_hash(right),
              "control_rows": len(a), "experimental_rows": len(b), "schema_equal": list(a)==list(b),
              "only_control_columns": sorted(set(a)-set(b)), "only_experimental_columns": sorted(set(b)-set(a)),
              "key_columns": keys, "row_order_equal": len(a)==len(b)}
    result["exact_decoded_bytes"] = result["control_decoded_sha256"]==result["experimental_decoded_sha256"]
    if keys:
        if a.duplicated(keys).any() or b.duplicated(keys).any():
            raise ValueError("Duplicate comparison identity")
        result["row_order_equal"] = a[keys].equals(b[keys])
        a, b = a.set_index(keys), b.set_index(keys)
        result.update(only_control_keys=len(a.index.difference(b.index)), only_experimental_keys=len(b.index.difference(a.index)))
        a, b = a.sort_index(), b.sort_index()
        same_keys = a.index.equals(b.index)
    else:
        same_keys = len(a)==len(b)
    result["aligned_identities_equal"] = same_keys
    if same_keys and result["schema_equal"]:
        changed = a.ne(b)
        result.update(differing_rows=int(changed.any(axis=1).sum()), differing_cells=int(changed.to_numpy().sum()),
                      differences_by_column={c:int(changed[c].sum()) for c in changed if changed[c].any()})
    return result


def require_team_only_difference(control, experimental):
    result = compare_csv(control, experimental, ["game_id", "team_role"])
    if (not result["schema_equal"] or not result["aligned_identities_equal"] or not result["row_order_equal"]
            or set(result.get("differences_by_column", {})) != DISPUTED or result["differing_rows"] != 1598
            or any(n != 1598 for n in result["differences_by_column"].values())):
        raise ValueError("Inputs differ beyond the two documented team fields")
    return result


def panel_summary(path):
    frame = pd.read_csv(path, low_memory=False)
    if frame.player_team_game_id.duplicated().any():
        raise ValueError("Duplicate scientific player-game identity")
    return {"rows":len(frame), "games":int(frame.game_id.nunique()),
            "at_risk":int(frame.at_risk_for_new_onset_harm.sum()), "onsets":int(frame.absence_onset_harm.sum()),
            "columns":list(frame), "decoded_sha256":decoded_hash(path)}


def stage(output, label, command, result_root, resume):
    checkpoint = output/(label+".execution.json")
    if checkpoint.exists():
        old = json.loads(checkpoint.read_text())
        if not resume or old.get("command") != command or old.get("output_sha256") != tree_hashes(result_root):
            raise ValueError("Completed stage checkpoint or outputs changed")
        return old
    if result_root.exists():
        raise ValueError("Incomplete stage retained; choose a fresh experiment output root: "+label)
    with (output/(label+".log")).open("w") as log:
        status = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode
    if status:
        raise RuntimeError(label+" failed; inspect private log")
    result = {"command":command, "wrapper_exit_status":status, "output_sha256":tree_hashes(result_root)}
    save(checkpoint, result)
    return result


def run(archives, source, output, resume=False):
    archives, source, output = (p.resolve() for p in (archives, source, output))
    if not resume:
        safe_output(archives, output); safe_output(source, output)
    elif not output.is_dir() or output.is_symlink() or (output/"experiment_acceptance.json").exists():
        raise ValueError("Resume requires an unfinished real private experiment root")
    if platform.system()!="Linux" or platform.machine()!="x86_64":
        raise ValueError("Authentic experiment requires Linux amd64")
    if file_sha256(SCRIPT)!=BUILDER_SHA:
        raise ValueError("Original scientific builder SHA differs")
    plan = build_plan(archives)
    needed = {x[1] for x in plan}|{"audit_2025_26_upload.zip", "audit_2025_26_targeted_upload.zip", "nba_game_covariates_v1.zip", S4_ZIP}
    original = {}
    for name in sorted(needed):
        path = archives/name
        if path.is_symlink() or file_sha256(path)!=(S4_SHA if name==S4_ZIP else SOURCE_HASHES[name]):
            raise ValueError("Original experiment archive hash differs: "+name)
        original[name]=file_sha256(path)
    code_paths = [Path(__file__), SCRIPT, *[TOOLS/name for name in (
        "generate_2025_selector_inputs.py", "run_historical_cadence_builder.py", "fixture_date_chronology_sensitivity.py")]]
    identity = {"source_hashes":tree_hashes(source), "archive_hashes":original,
                "code_hashes":{str(p.relative_to(TOOLS.parents[1])):file_sha256(p) for p in code_paths}}
    if resume:
        if json.loads((output/"experiment_identity.json").read_text())!=identity:
            raise ValueError("Original source, archive, or code identity changed before resume")
    else:
        output.mkdir(parents=True); save(output/"experiment_identity.json", identity)
        frames = {}
        audit = generate(archives, source, output/"source_audit", audit_only=True, diagnostic_frames=frames)
        if audit.get("status")!="blocked_legacy_team_metadata":
            raise ValueError("Documented experiment premise changed")
        common = output/"common_inputs"; restore(archives, common, plan)
        fresh_game, fresh_team = frames[Path(GAME).name], frames[Path(TEAM).name]
        selected_names = set(fresh_game.snapshot_basename)
        if len(selected_names)!=355:
            raise ValueError("Fresh selected PDF identities differ")
        raw = pd.read_csv(source/"full_candidate_rows.csv", low_memory=False)
        chosen = raw.loc[raw.source_file.map(lambda s:Path(s).name).isin(selected_names)]
        if set(chosen.source_file.map(lambda s:Path(s).name))!=selected_names:
            raise ValueError("Missing freshly parsed selected report")
        (common/ROWS).parent.mkdir(parents=True, exist_ok=True)
        chosen.to_csv(common/ROWS, index=False); fresh_game.to_csv(common/GAME, index=False)
        for name in ("control", "experimental"):
            shutil.copytree(common, output/(name+"_inputs"))
        old = pd.read_csv(common/TEAM)
        if fresh_team.duplicated(["game_id", "team_role"]).any():
            raise ValueError("Duplicate generated team identity")
        fresh_team = fresh_team.set_index(["game_id", "team_role"]).reindex(pd.MultiIndex.from_frame(old[["game_id", "team_role"]])).reset_index()
        fresh_team[list(old)].to_csv(output/"experimental_inputs"/TEAM, index=False)
        difference = require_team_only_difference(output/"control_inputs"/TEAM, output/"experimental_inputs"/TEAM)
        fingerprints = {name:tree_hashes(output/(name+"_inputs")) for name in ("control", "experimental")}
        if set(fingerprints["control"])!=set(fingerprints["experimental"]) or {
                p for p in fingerprints["control"] if fingerprints["control"][p]!=fingerprints["experimental"][p]}!={TEAM}:
            raise ValueError("Non-team experiment input file differs")
        save(output/"input_fingerprints.json", fingerprints); save(output/"input_difference.json", difference)
    fingerprints = json.loads((output/"input_fingerprints.json").read_text())
    conditions = {name:output/(name+"_inputs") for name in ("control", "experimental")}
    for name, root in conditions.items():
        if tree_hashes(root)!=fingerprints[name]:
            raise ValueError("Prepared condition input changed")
    execution = {}; frozen = {}; corrected = {}
    def command(script, *args):
        return [sys.executable, str(TOOLS/script), *map(str,args)]
    for name, root in conditions.items():
        required = output/(name+"_required_inputs.json")
        save(required, {p:fingerprints[name][p] for p in (ROWS, GAME, TEAM)})
        frozen[name]=output/(name+"_frozen")
        execution[name]=stage(output,name+"_frozen",command("run_historical_cadence_builder.py",
            "--historical-root",root,"--output",frozen[name],"--required-input-hashes",required),frozen[name],resume)
        if tree_hashes(root)!=fingerprints[name]:
            raise ValueError("Input modified by original builder")
    comparisons = {}
    for filename in PRE_MODEL_OUTPUTS:
        keys = (["player_team_game_id"] if filename.startswith("player_team_game_") else
                ["game_id","team_role"] if filename=="harmonized_team_game_report_status.csv" else None)
        comparisons[filename]=compare_csv(frozen["control"]/filename, frozen["experimental"]/filename,keys)
        if filename=="harmonized_team_game_report_status.csv":
            require_team_only_difference(frozen["control"]/filename, frozen["experimental"]/filename)
        elif not comparisons[filename]["exact_decoded_bytes"]:
            raise ValueError("Unexpected downstream output difference: "+filename)
    frozen_summaries = {name:panel_summary(p/"player_team_game_harmonized_cadence.csv.gz") for name,p in frozen.items()}
    save(output/"frozen_comparison.json", {"outputs":comparisons,"panels":frozen_summaries})
    if any(v["decoded_sha256"]!=FROZEN_HASH for v in frozen_summaries.values()):
        raise ValueError("Scientific frozen panel differs from accepted hash")
    model_checks = {}
    for name, root in conditions.items():
        corrected[name]=output/(name+"_corrected")
        execution[name+"_corrected"]=stage(output,name+"_corrected",command("fixture_date_chronology_sensitivity.py",
            "--replay-root",root,"--variant-root",output/(name+"_chronology_inputs"),"--output",corrected[name],
            "--covariates-zip",archives/"nba_game_covariates_v1.zip","--required-input-hashes",output/(name+"_required_inputs.json")),corrected[name],resume)
        model_checks[name]=verify_model_report(corrected[name]/"fixture_date_chronology_sensitivity.json")
    panel = compare_csv(corrected["control"]/"player_team_game_harmonized_cadence.csv.gz",
                        corrected["experimental"]/"player_team_game_harmonized_cadence.csv.gz",["player_team_game_id"])
    models = compare_csv(corrected["control"]/"stage6_models/cadence_harmonized_model_results.csv",
                         corrected["experimental"]/"stage6_models/cadence_harmonized_model_results.csv",["definition","controls"])
    if not panel["exact_decoded_bytes"] or panel["control_decoded_sha256"]!=CORRECTED_SHA or not models["exact_decoded_bytes"] or models["control_rows"]!=4:
        raise ValueError("Corrected panel or all four models differ")
    if any(tree_hashes(root)!=fingerprints[name] for name,root in conditions.items()) or tree_hashes(source)!=identity["source_hashes"] or any(file_sha256(archives/k)!=v for k,v in original.items()):
        raise ValueError("Original condition inputs or sources changed during experiment")
    result = {"status":"pass","outcome":"metadata_only_for_executed_scientific_outputs",
        "historical_team_artifact_equivalence":False,"original_S4_team_join_recovered":False,
        "cumulative_six_season_raw_source_execution":False,"other_seasons_inherit_pinned_historical_inputs":True,
        "identity":identity,"input_fingerprints":fingerprints,"input_difference":json.loads((output/"input_difference.json").read_text()),
        "execution":execution,"frozen_outputs":comparisons,"frozen_panels":frozen_summaries,
        "corrected_panel":panel,"corrected_panels":{n:panel_summary(p/"player_team_game_harmonized_cadence.csv.gz") for n,p in corrected.items()},
        "corrected_models":models,"model_target_checks":model_checks,
        "model_results":{n:json.loads((p/"fixture_date_chronology_sensitivity.json").read_text())["stage6_models"] for n,p in corrected.items()},
        "consumption":{n:json.loads((p/"replay_environment.json").read_text()) for n,p in {**frozen,**{n+"_corrected":p for n,p in corrected.items()}}.items()}}
    save(output/"experiment_acceptance.json",result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir",type=Path,required=True)
    p.add_argument("--fresh-source-dir",type=Path,required=True)
    p.add_argument("--output-root",type=Path,required=True)
    p.add_argument("--resume",action="store_true")
    a=p.parse_args(); result=run(a.archive_dir,a.fresh_source_dir,a.output_root,a.resume)
    print(json.dumps({"status":result["status"],"outcome":result["outcome"]}))


if __name__=="__main__":main()
