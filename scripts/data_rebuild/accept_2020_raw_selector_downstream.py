#!/usr/bin/env python3
"""Targeted authentic raw-2020 downstream acceptance using a prior private run.

Reuses the other five seasons' verified historical inputs, never prior final
datasets. Runs the original October builder and original frozen model gate.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.data_rebuild.reproduce_final_datasets import preflight, REFERENCE_CADENCE, TOOLS
from scripts.data_rebuild.rebuild_2020_selected_from_pdfs import rebuild, FULL_SOURCE_FILE
from scripts.data_rebuild.verify_canonical_selector_replay import verify, file_sha256
from scripts.data_rebuild.inject_generated_canonical_selectors import inject, RAW_2020_TARGET, RELATIVE
from scripts.data_rebuild.run_historical_cadence_builder import PRE_MODEL_OUTPUTS, NEEDED

FROZEN_HASH = "3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac"


def decoded_hash(path):
    digest = hashlib.sha256()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(archives, prior, output, fresh_source=None):
    archives, prior, output = map(lambda p: p.resolve(), (archives, prior, output))
    if prior == output or prior in output.parents or output in prior.parents:
        raise ValueError("Prior acceptance run and new output must be disjoint")
    preflight(archives, output, True, rebuild_2020_2024_selectors=True)
    manifest = json.loads((prior/"final/final_dataset_manifest.json").read_text())
    if manifest.get("status") != "pass" or len(manifest.get("stage_logs", {})) != 9:
        raise ValueError("Expected the accepted nine-stage private run manifest")
    from scripts.data_rebuild.reproduce_final_datasets import SOURCE_HASHES, SELECTOR_SCHEDULE_EXTRA_ZIPS
    if manifest.get("input_archives_sha256") != SOURCE_HASHES | SELECTOR_SCHEDULE_EXTRA_ZIPS:
        raise ValueError("Prior private run source inventory differs")
    historical = prior/"03_historical_cadence_inputs"
    if historical.is_symlink() or not historical.is_dir():
        raise ValueError("Prior private historical input root missing or symlinked")
    for node in historical.rglob("*"):
        if node.is_symlink():
            raise ValueError("Prior historical input tree contains symlinks")
    for name in NEEDED:
        if not (historical/name).exists():
            raise FileNotFoundError(name)
    prior_outputs = prior/"04_frozen_cadence"
    if decoded_hash(prior_outputs/"player_team_game_harmonized_cadence.csv.gz") != FROZEN_HASH:
        raise ValueError("Prior frozen cadence output differs from immutable reference")
    output.mkdir()
    if fresh_source is None:
        fresh_source = output/"fresh_2020"
        rebuild(archives, fresh_source, workers=4, emit_full_source_rows=True)
    generated = output/"generated_selectors"
    verify(archives, generated_dir=generated,
           fresh_2020_rows=fresh_source/FULL_SOURCE_FILE,
           fresh_2020_acceptance=fresh_source/"2020_21_original_pdf_source_acceptance.json")
    work = output/"historical_inputs"
    shutil.copytree(historical, work)
    # A prior optional handoff report is evidence only for its own prior run.
    handoff = inject(generated, work, output/"generated_selector_handoff.json", require_raw_2020=True)
    names = [str(RAW_2020_TARGET), *[str(RELATIVE/name) for name in (
        "2020-21_game_snapshot_join_harmonized_canonical.csv",
        "2020-21_team_game_status_harmonized_canonical.csv")]]
    hashes = {name:file_sha256(work/name) for name in names}
    required = output/"required_generated_inputs.json"
    required.write_text(json.dumps(hashes, indent=2)+"\n")
    def call(script, *args):
        logfile = output/(script+".log")
        with logfile.open("w") as stream:
            subprocess.run([sys.executable,str(TOOLS/script),*map(str,args)],
                           stdout=stream,stderr=subprocess.STDOUT,check=True)
    rebuilt = output/"october_builder"
    call("run_historical_cadence_builder.py","--historical-root",work,"--output",rebuilt,
         "--required-input-hashes",required)
    comparisons = {}
    for name in PRE_MODEL_OUTPUTS:
        a,b = decoded_hash(prior_outputs/name),decoded_hash(rebuilt/name)
        comparisons[name] = {"reference_decoded_sha256":a,"generated_decoded_sha256":b,
                             "exact_decoded_bytes":a==b}
        if a != b:
            raise ValueError(f"October intermediate decoded bytes differ: {name}")
    panel = rebuilt/"player_team_game_harmonized_cadence.csv.gz"
    if decoded_hash(panel) != FROZEN_HASH:
        raise ValueError("New October frozen panel hash differs")
    call("validate_cadence_panel.py","--panel",panel,"--expect-frozen",
         "--output",output/"panel_invariants.json")
    call("replay_stage6_from_frozen.py","--panel",panel,"--output-dir",output/"models")
    result = {
        "status":"pass","scope":"Targeted raw-2020 original October builder and frozen models; other seasons reused",
        "new_full_final_dataset_run":False,"fresh_2020_source_reused":fresh_source != output/"fresh_2020",
        "source_file_sha256":file_sha256(fresh_source/FULL_SOURCE_FILE),
        "original_builder_consumption":json.loads((rebuilt/"replay_environment.json").read_text())["generated_input_consumption"],
        "intermediate_decoded_byte_comparisons":comparisons,"handoff":handoff,
        "october_frozen_panel_decoded_sha256":decoded_hash(panel),
        "corrected_final_panel_rebuilt":False,
    }
    (output/"downstream_acceptance.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir",type=Path,required=True)
    p.add_argument("--prior-run-root",type=Path,required=True)
    p.add_argument("--output-root",type=Path,required=True)
    p.add_argument("--fresh-2020-source-dir",type=Path)
    a=p.parse_args()
    print(json.dumps(run(a.archive_dir,a.prior_run_root,a.output_root,a.fresh_2020_source_dir),indent=2))


if __name__=="__main__":
    main()
