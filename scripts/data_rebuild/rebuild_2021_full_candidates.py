#!/usr/bin/env python3
"""Parse complete original 2021 or 2022 selector candidates with the pinned parser."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile
import pandas as pd
from scripts.data_rebuild.replay_recent_historical_injury_pdfs import init_parser, parse_task
from scripts.data_rebuild.verify_2021_2023_selector_rebuild import (
    PINNED, EXPECTED_2021_PARSER, verify_2021_harmonized_reference,
)
from scripts.data_rebuild.verify_canonical_selector_replay import file_sha256, member_bytes
from scripts.data_rebuild.reproduce_final_datasets import SOURCE_HASHES


def candidate_inventory(manifest, names, expected_pdfs=5567):
    present=manifest.loc[manifest.exists.astype(str).str.lower().isin(("true","1"))].copy()
    if len(present)!=expected_pdfs or present.local_path.duplicated().any():
        raise ValueError("Incomplete/duplicate original 2021 candidate inventory")
    if set(present.local_path)!=set(names):
        raise ValueError("Original PDF members disagree with complete manifest")
    dates=pd.to_datetime(present.published_timestamp_utc,utc=True,errors="raise")
    if dates.isna().any() or dates.duplicated().any():
        raise ValueError("Missing/duplicate original report timestamps")
    if present.sha256.isna().any():
        raise ValueError("Original manifest missing PDF hashes")
    return present


def csv_records(frame):
    normalized=pd.read_csv(io.StringIO(frame.to_csv(index=False)),dtype=str,keep_default_na=False)
    return Counter(normalized.itertuples(index=False,name=None))


def verify_2022_reference(archives,frame,log):
    archive=archives/"audit_2022_23_pre_s4_outputs.zip"
    reference=pd.read_csv(io.BytesIO(member_bytes(archive,"s1_snapshot_rows_regular_season.csv")),low_memory=False)
    reference_log=pd.read_csv(io.BytesIO(member_bytes(archive,"s1_parse_log_regular_season.csv")))
    for actual,expected,count in ((frame,reference,354146),(log,reference_log,4101)):
        if list(actual)!=list(expected) or len(actual)!=count or csv_records(actual)!=csv_records(expected):
            raise ValueError("Fresh 2022 full candidate rows/log records differ from original")
    return {"total_parsed_pdfs":4101,"total_parsed_rows":354146,
            "all_regular_season_rows_and_logs_exact":True}


def rebuild(archives, output, workers=4, season="2021-22"):
    if season not in ("2021-22","2022-23"):
        raise ValueError("Unsupported complete candidate season")
    is2022=season=="2022-23"
    raw_zip="audit_2022_23_upload.zip" if is2022 else "audit_2021_22_upload.zip"
    dependencies=(raw_zip,"audit_2022_23_pre_s4_outputs.zip","nba_player_game_at_risk_core_v1.zip") if is2022 else (raw_zip,"audit_2021_22_cadence_outputs.zip")
    archives,output=archives.resolve(),output.resolve()
    if output.exists() or archives==output or archives in output.parents:
        raise ValueError("Fresh private output must be absent and outside original archives")
    if any((p/".git").exists() for p in (output,*output.parents)):
        raise ValueError("Private candidate rows cannot be written in Git")
    if not 1<=workers<=16:
        raise ValueError("workers must be 1..16")
    for name in dependencies:
        if file_sha256(archives/name)!=SOURCE_HASHES[name]:
            raise ValueError("Original 2021 ZIP hash differs: "+name)
    parser=(member_bytes(archives/"nba_player_game_at_risk_core_v1.zip",
                         "nba_player_game_at_risk_core_v1/parsers/parser_2021_2022.py")
            if is2022 else member_bytes(archives/"audit_2021_22_cadence_outputs.zip","nba_injury_fitz_parser_v3.py"))
    if hashlib.sha256(parser).hexdigest()!=EXPECTED_2021_PARSER:
        raise ValueError("Original 2021 parser SHA-256 differs")
    rows=[]; logs=[]
    with ZipFile(archives/raw_zip) as archive, tempfile.TemporaryDirectory(prefix="nba_candidate_pdfs_") as temporary:
        pdfs=[n for n in archive.namelist() if n.endswith(".pdf")]
        if len(pdfs)!=len(set(pdfs)):
            raise ValueError("Duplicate original PDF archive members")
        manifest=pd.read_csv(io.BytesIO(archive.read("audit_"+season.replace("-","_")+"/report_manifest.csv")))
        if is2022:
            manifest=manifest.loc[manifest.report_date.between("2022-10-18","2023-04-09")]
            wanted=set(manifest.loc[manifest.exists.astype(str).str.lower().isin(("true","1"))].local_path)
            pdfs=[name for name in pdfs if name in wanted]
        present=candidate_inventory(manifest,pdfs,4101 if is2022 else 5567)
        parser_path=Path(temporary)/"parser.py";parser_path.write_bytes(parser)
        tasks=[]
        for record in present.to_dict("records"):
            name=record["local_path"]; basename=Path(name).name
            if not basename.startswith("Injury-Report_") or "/" in basename or "\\" in basename:
                raise ValueError("Unsafe original PDF basename")
            content=archive.read(name)
            if hashlib.sha256(content).hexdigest()!=record["sha256"]:
                raise ValueError("Original PDF hash differs: "+basename)
            path=Path(temporary)/basename
            if path.exists():raise ValueError("Duplicate original PDF basename")
            path.write_bytes(content)
            tasks.append((basename,str(path),season,record["report_date"],
                          record["published_timestamp_utc"],name,None))
        by_name={task[0]:task for task in tasks}
        with ProcessPoolExecutor(max_workers=workers,initializer=init_parser,initargs=(str(parser_path),)) as pool:
            for basename, parsed, count, pages, warning in pool.map(parse_task,tasks):
                if not pages:raise ValueError("Original PDF returned no pages")
                rows.extend(parsed);task=by_name[basename]
                logs.append(dict(source_file=task[5],snapshot_timestamp_utc=task[4],
                                 pages=pages,extracted_rows=count,status="ok",warning=warning))
    frame=pd.DataFrame(rows); log=pd.DataFrame(logs)
    # Compare at the historical CSV boundary: empty parser strings become NA
    # on the same read_csv interface used by the original archived outputs.
    frame=pd.read_csv(io.StringIO(frame.to_csv(index=False)),low_memory=False)
    log=pd.read_csv(io.StringIO(log.to_csv(index=False)),low_memory=False)
    output.mkdir(parents=True,exist_ok=False)
    full=output/"full_candidate_rows.csv"; logfile=output/"full_candidate_parse_log.csv"
    frame.to_csv(full,index=False);log.to_csv(logfile,index=False)
    comparison=verify_2022_reference(archives,frame,log) if is2022 else verify_2021_harmonized_reference(archives,frame,log)
    report={"status":"pass","fresh_original_PDF_execution":True,"pdfs":len(log),
            "season":season,"source_archive_sha256":{name:SOURCE_HASHES[name] for name in dependencies},
            "rows":len(frame),"original_publication_metadata_inherited":True,
            "original_parser_sha256":EXPECTED_2021_PARSER,"comparison":comparison,
            "full_candidate_rows_sha256":file_sha256(full),"full_candidate_log_sha256":file_sha256(logfile)}
    (output/"candidate_acceptance.json").write_text(json.dumps(report,indent=2)+"\n")
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--season",choices=("2021-22","2022-23"),default="2021-22")
    a=p.parse_args();print(json.dumps(rebuild(a.archive_dir,a.output_dir,a.workers,a.season),indent=2))


if __name__=="__main__":main()
