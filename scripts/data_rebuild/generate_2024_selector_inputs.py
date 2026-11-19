"""Connect full fresh 2024 candidates to the existing verified original selector."""
import json
from pathlib import Path
import pandas as pd
from scripts.data_rebuild.verify_canonical_selector_replay import verify,csv_from_zip,file_sha256


def generate(archives,source,output):
    # The existing original selector performs all scientific computations.
    replay=verify(archives,("2024-25",),output,fresh_2024_source=source)
    acceptance=json.loads((source/"candidate_acceptance.json").read_text())
    raw=pd.read_csv(source/"full_candidate_rows.csv",low_memory=False)
    original_log=csv_from_zip(archives,("audit_2024_25_pre_s4_outputs_corrected.zip",
                                      "s1_parse_log_regular_season_real.csv"))
    if len(original_log)!=4078 or original_log.source_file.duplicated().any():
        raise ValueError("Original 2024 parsed-row file ordering is incomplete or duplicated")
    rank={name:i for i,name in enumerate(original_log.source_file)}
    raw["_source_order"]=raw.source_file.map(rank)
    if raw["_source_order"].isna().any():
        raise ValueError("Fresh 2024 record outside historical regular-season candidates")
    raw=raw.sort_values("_source_order",kind="stable").drop(columns="_source_order")
    target=output/"2024-25_fresh_candidate_rows.csv"
    raw.to_csv(target,index=False)
    files={name:{"rows":value["rows"],"sha256":value["sha256"]}
           for name,value in replay["generated_selector_tables"].items()}
    files[target.name]={"rows":len(raw),"sha256":file_sha256(target)}
    result={"all_replays_exact":True,"scope":"Fresh original 2024 PDFs through existing original canonical selector",
            "generated_files":files,"full_candidate_rows_sha256":acceptance["full_candidate_rows_sha256"],
            "full_candidate_log_sha256":acceptance["full_candidate_log_sha256"],
            "historical_source_file_order_inherited_from_parse_log":True}
    (output/"selector_acceptance.json").write_text(json.dumps(result,indent=2)+"\n")
    return result
