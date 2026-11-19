"""Offline replay of the original 3,526-URL acquisition-plan generator."""
from dataclasses import asdict
import hashlib
import io
import json
from pathlib import Path
import sys
import types
from zipfile import ZipFile
import pandas as pd
from scripts.data_rebuild.rebuild_2025_full_candidates import S4_ZIP,S4_SHA
from scripts.data_rebuild.verify_canonical_selector_replay import file_sha256,member_bytes

DESIGN_SHA="f17354dc244e7650fb5f92f4b41f292e9229055b00d4506948e62951b8f53919"
SCRIPT_SHA="7abb429122470e747c5f85ba6997d9957b146b8dc1a2e77e4ede69a1fad08f2d"
PREFIX="audit_2025_26_targeted_plan/"


def verify(archives,design_zip):
    if file_sha256(design_zip)!=DESIGN_SHA or file_sha256(archives/S4_ZIP)!=S4_SHA:
        raise ValueError("Original acquisition design/schedule SHA-256 differs")
    with ZipFile(design_zip) as archive:
        body=archive.read(PREFIX+"download_nba_2025_26_targeted.py")
        if hashlib.sha256(body).hexdigest()!=SCRIPT_SHA:
            raise ValueError("Original acquisition generator source differs")
        reference=pd.read_csv(io.BytesIO(archive.read(PREFIX+"target_plan.csv")),dtype=str,keep_default_na=False)
    decoded=body.decode()
    if decoded.count("def write_csv(")!=1:
        raise ValueError("Original offline function boundary changed")
    prefix=decoded.split("def write_csv(",1)[0]
    # Only remove imports for unused network routines; scientific candidate
    # generation declarations remain the SHA-verified original code.
    for line in ("import requests\n","from requests.adapters import HTTPAdapter\n","from urllib3.util.retry import Retry\n"):
        if prefix.count(line)!=1:raise ValueError("Original offline import boundary changed")
        prefix=prefix.replace(line,"",1)
    module=types.ModuleType("_pinned_original_2025_candidate_plan")
    sys.modules[module.__name__]=module
    exec(compile(prefix,"original_2025_candidate_plan","exec"),module.__dict__)
    schedule=pd.read_csv(io.BytesIO(member_bytes(archives/S4_ZIP,"s4_games_2025_26_normalized.csv")))
    original_interface=pd.DataFrame({
        "Date":pd.to_datetime(schedule.tip_timestamp_utc,utc=True).dt.strftime("%d/%m/%Y %H:%M"),
        "Away Team":schedule.away_team,"Home Team":schedule.home_team})
    parsed=module.parse_schedule(io.StringIO(original_interface.to_csv(index=False)))
    generated=pd.DataFrame([asdict(row) for row in module.build_candidates(
        parsed,pd.Timestamp("2025-12-22T09:00:00-05:00").tz_convert(module.ET),4)]).fillna("")
    a,b=generated.set_index("filename").sort_index(),reference.set_index("filename").sort_index()
    if len(a)!=3526 or not a.index.equals(b.index) or list(a)!=list(b) or not a.equals(b):
        raise ValueError("Original targeted acquisition plan does not reproduce all fields")
    return {"status":"pass","original_design_zip_sha256":DESIGN_SHA,
            "original_generator_sha256":SCRIPT_SHA,"targeted_urls":3526,
            "all_six_original_plan_fields_exact":True,"fallback_hours":4,
            "network_requests_performed":False,"full_quarter_hour_archive_claimed":False,
            "historical_download_observations_not_regenerated":True}


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-dir",type=Path,required=True)
    p.add_argument("--design-zip",type=Path,required=True)
    a=p.parse_args();print(json.dumps(verify(a.archive_dir,a.design_zip),indent=2))


if __name__=="__main__":main()
