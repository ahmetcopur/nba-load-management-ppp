"""Reparse every saved 2025–26 candidate PDF, preserving original manifest clocks."""
from concurrent.futures import ProcessPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile
import pandas as pd
from scripts.data_rebuild.verify_2025_manifest_selector import EXPECTED_ZIPS,manifest_part,select_from_inventory
from scripts.data_rebuild.verify_canonical_selector_replay import file_sha256,member_bytes
from scripts.data_rebuild.rebuild_2021_full_candidates import LATE_PARSER_SHA
from scripts.data_rebuild.replay_recent_historical_injury_pdfs import init_parser,parse_task
from scripts.data_rebuild.rebuild_2020_selected_from_pdfs import safe_output
from scripts.data_rebuild.reproduce_final_datasets import SOURCE_HASHES

S4_ZIP="audit_2025_26_s4_join_results.zip"
S4_SHA="6ad1013984693abc852b4a8cf2fcf3aad6dc1a9eb555ef35d121f95ca4c9989c"
PARTS=(
    ("initial","audit_2025_26_upload.zip","audit_2025_26/report_manifest.csv","published_timestamp_utc",1497),
    ("targeted","audit_2025_26_targeted_upload.zip","audit_2025_26_targeted/report_manifest.csv","report_timestamp_utc",3526),
)


def inventory(archives):
    parts=[]
    for label,name,member,clock,count in PARTS:
        if file_sha256(archives/name)!=EXPECTED_ZIPS[name]:
            raise ValueError("Original 2025 source ZIP hash differs: "+name)
        with ZipFile(archives/name) as archive:
            manifest=pd.read_csv(io.BytesIO(archive.read(member)))
            verified=manifest_part(manifest,clock,label)
            if len(verified)!=count:
                raise ValueError("Incomplete original saved candidate inventory")
            present=manifest.loc[manifest.exists.astype(str).str.lower().isin(("true","1"))].copy()
            pdfs=[n for n in archive.namelist() if n.endswith(".pdf")]
            if len(pdfs)!=len(set(pdfs)) or set(pdfs)!=set(present.local_path) or present.local_path.duplicated().any():
                raise ValueError("Original PDF members differ from saved candidate manifest")
            present["published"]=pd.to_datetime(present[clock],utc=True,errors="raise")
            present["basename"]=present.local_path.map(lambda value:Path(value).name)
            present["source"]=label;present["archive"]=name
            if present.sha256.isna().any():
                raise ValueError("Saved candidate manifest lacks original payload hashes")
            parts.append(present[["published","basename","source","archive","local_path","sha256"]])
    result=pd.concat(parts,ignore_index=True)
    # Same duplicate/strict-clock guard used by the verified manifest selector.
    select_from_inventory(result,pd.DataFrame({"game_id":["audit"],"tip_timestamp_utc":[result.published.max()+pd.Timedelta(minutes=1)]}))
    return result


def rebuild(archives,output,workers=4):
    archives,output=archives.resolve(),output.resolve()
    safe_output(archives,output)
    if not 1<=workers<=16:raise ValueError("workers must be 1..16")
    core=archives/"nba_player_game_at_risk_core_v1.zip"
    if file_sha256(core)!=SOURCE_HASHES[core.name]:raise ValueError("Original core source ZIP differs")
    parser=member_bytes(core,"nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py")
    if hashlib.sha256(parser).hexdigest()!=LATE_PARSER_SHA:raise ValueError("Original later parser differs")
    metadata=inventory(archives)
    gathered=[];logs=[];counts={"initial":0,"targeted":0}
    with tempfile.TemporaryDirectory(prefix="nba_2025_candidate_PDFs_") as temporary:
        parser_path=Path(temporary)/"original_parser.py";parser_path.write_bytes(parser)
        tasks=[];byname={}
        for label,name,_,_,_ in PARTS:
            with ZipFile(archives/name) as archive:
                for record in metadata.loc[metadata.source.eq(label)].to_dict("records"):
                    body=archive.read(record["local_path"])
                    if hashlib.sha256(body).hexdigest()!=record["sha256"]:
                        raise ValueError("Original candidate PDF hash differs: "+record["basename"])
                    path=Path(temporary)/record["basename"]
                    if path.exists():raise ValueError("Duplicate original candidate PDF basename")
                    path.write_bytes(body)
                    stamp=record["published"].isoformat()
                    date=record["published"].tz_convert("America/New_York").strftime("%Y-%m-%d")
                    tasks.append((record["basename"],str(path),"2025-26",date,stamp,"cadence_selected/"+record["basename"],None))
                    byname[record["basename"]]=(label,stamp)
        with ProcessPoolExecutor(max_workers=workers,initializer=init_parser,initargs=(str(parser_path),)) as pool:
            for basename,rows,count,pages,warning in pool.map(parse_task,tasks):
                if not pages or not count:raise ValueError("Candidate PDF requires explicit zero-row/error review: "+basename)
                label,stamp=byname[basename];counts[label]+=count;gathered.extend(rows)
                logs.append({"source_file":basename,"snapshot_timestamp_utc":stamp,"pages":pages,
                             "extracted_rows":count,"status":"ok","warning":warning or ""})
    if len(logs)!=5023 or counts!={"initial":133512,"targeted":465713}:
        raise ValueError("Original S4 documented complete candidate parse counts differ")
    output.mkdir(parents=True,exist_ok=False)
    rows_path=output/"full_candidate_rows.csv";log_path=output/"full_candidate_parse_log.csv"
    pd.DataFrame(gathered).to_csv(rows_path,index=False);pd.DataFrame(logs).to_csv(log_path,index=False)
    metadata.to_csv(output/"candidate_inventory.csv",index=False)
    report={"status":"pass","season":"2025-26","fresh_original_PDF_execution":True,
            "pdfs":5023,"rows":len(gathered),"rows_by_source":counts,
            "source_archive_sha256":EXPECTED_ZIPS,"original_parser_sha256":LATE_PARSER_SHA,
            "full_candidate_rows_sha256":file_sha256(rows_path),
            "full_candidate_log_sha256":file_sha256(log_path),
            "candidate_inventory_sha256":file_sha256(output/"candidate_inventory.csv"),
            "original_publication_metadata_inherited":True,
            "targeted_archive_is_not_complete_quarter_hour_inventory":True,
            "full_historical_row_reference_available":False,
            "known_21_printed_clock_exceptions_not_silently_corrected":True}
    (output/"candidate_acceptance.json").write_text(json.dumps(report,indent=2)+"\n")
    return report


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--workers",type=int,default=4)
    a=p.parse_args();print(json.dumps(rebuild(a.archive_dir,a.output_dir,a.workers),indent=2))


if __name__=="__main__":main()
