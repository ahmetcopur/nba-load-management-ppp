"""Strict full-candidate 2021/2022 source/selector handoff into private October inputs."""
from collections import Counter
import io
import json
from pathlib import Path
import shutil
import pandas as pd
from scripts.data_rebuild.verify_canonical_selector_replay import file_sha256
from scripts.data_rebuild.verify_2021_2023_selector_rebuild import normalized_frame_equal

RELATIVE=Path("cadence_work/selector/nba_canonical_snapshot_selector_v1")
ROW_TARGET=Path("cadence_work/season_parsed/2021-22/s1_snapshot_rows_harmonized.csv")
FILES={
    "2021-22_game_snapshot_join_harmonized_canonical.csv":RELATIVE/"2021-22_game_snapshot_join_harmonized_canonical.csv",
    "2021-22_team_game_status_harmonized_canonical.csv":RELATIVE/"2021-22_team_game_status_harmonized_canonical.csv",
    "2021-22_fresh_harmonized_rows.csv":ROW_TARGET,
}


def input_files(season):
    if season=="2021-22":return FILES
    if season!="2022-23":raise ValueError("Unsupported fresh source handoff season")
    return {
        "2022-23_game_snapshot_join_harmonized_canonical.csv":RELATIVE/"2022-23_game_snapshot_join_harmonized_canonical.csv",
        "2022-23_team_game_status_harmonized_canonical.csv":Path("cadence_work/s4/2022-23/team_game_final_pre_tip_status_harmonized.csv"),
        "2022-23_fresh_candidate_rows.csv":Path("cadence_work/season_parsed/2022-23/s1_snapshot_rows_regular_season.csv"),
    }


def inject(generated, source, historical, season="2021-22"):
    files=input_files(season)
    pdfs,count=(4101,354146) if season=="2022-23" else (5567,398715)
    report=json.loads((generated/"selector_acceptance.json").read_text())
    raw=json.loads((source/"candidate_acceptance.json").read_text())
    if (raw.get("status")!="pass" or raw.get("fresh_original_PDF_execution") is not True
            or raw.get("pdfs")!=pdfs or raw.get("rows")!=count or not report.get("all_replays_exact")):
        raise ValueError("Incomplete original 2021 candidate source/selector acceptance")
    for filename,key in (("full_candidate_rows.csv","full_candidate_rows_sha256"),
                         ("full_candidate_parse_log.csv","full_candidate_log_sha256")):
        path=source/filename
        if path.is_symlink() or not path.is_file() or file_sha256(path)!=raw.get(key) or raw[key]!=report.get(key):
            raise ValueError("2021 raw source hash/provenance differs")
    records=[]
    for name,relative in files.items():
        src,dst=generated/name,historical/relative
        if any(p.is_symlink() or not p.is_file() for p in (src,dst)):
            raise ValueError("Missing/symlinked generated or restored 2021 input")
        if file_sha256(src)!=report.get("generated_files",{}).get(name,{}).get("sha256"):
            raise ValueError("Generated 2021 input hash differs")
        a,b=pd.read_csv(src,low_memory=False),pd.read_csv(dst,low_memory=False)
        if name.endswith(("fresh_harmonized_rows.csv","fresh_candidate_rows.csv")):
            def rows(frame):
                d=pd.read_csv(io.StringIO(frame.to_csv(index=False)),dtype=str,keep_default_na=False)
                return Counter(d.itertuples(index=False,name=None))
            if list(a)!=list(b) or len(a)!=(354146 if season=="2022-23" else 58631) or rows(a)!=rows(b):
                raise ValueError("2021 harmonized source complete records differ")
        else:
            normalized_frame_equal(a,b,["game_id"] if "game_snapshot" in name else ["game_id","team_role"],strict_schema=True)
        records.append({"path":str(relative),"source_sha256":file_sha256(src),"rows":len(a)})
    for name,relative in files.items():
        dst=historical/relative
        temporary=dst.with_name(dst.name+".generated.tmp")
        with (generated/name).open("rb") as a,temporary.open("xb") as b:shutil.copyfileobj(a,b)
        if file_sha256(temporary)!=file_sha256(generated/name):raise ValueError("2021 source changed during copy")
        temporary.replace(dst)
    return {"season":season,"fresh_original_candidate_PDFs":pdfs,
            "generated_rows_and_selectors_substituted":True,"tables":records,
            "publication_metadata_inherited":True}
