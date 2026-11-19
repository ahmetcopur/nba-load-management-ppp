#!/usr/bin/env python3
"""Narrow provenance audit of original August 2026 Toronto selected-report join.

The historical builder had a season-wide matchup-only override. It incorrectly
pulled 7 October 2021 Bulls/Raptors rows and 10 April 2022 Heat/Raptors rows
into the two February 2022 games. This audits but does not rebuild August.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import pandas as pd

SOURCE_SWAPS={
    430:"2021-22|20220204T0030Z|Miami Heat@Toronto Raptors",
    784:"2021-22|20220202T0030Z|Chicago Bulls@Toronto Raptors",
}
EXPECTED={
    46:(7,"CHI@TOR","2021-22|20211025T2330Z|Chicago Bulls@Toronto Raptors"),
    430:(10,"MIA@TOR",SOURCE_SWAPS[430]),
    784:(9,"CHI@TOR",SOURCE_SWAPS[784]),
    1172:(10,"MIA@TOR","2021-22|20220403T2300Z|Miami Heat@Toronto Raptors"),
}
EXPECTED_HISTORICAL_BUILDER_SHA="738b78fa9fd9f3cdd9f4b4eb6756b424680959cacb85cfc354a6d6affa915fef"

def audit(core_zip):
    with zipfile.ZipFile(core_zip) as z:
        source=z.read("nba_player_game_at_risk_core_v1/build_selected_report_and_identity_stage.py")
        digest=hashlib.sha256(source).hexdigest()
        if digest!=EXPECTED_HISTORICAL_BUILDER_SHA:
            raise RuntimeError(f"Historical August builder SHA changed: {digest}")
        text=source.decode("utf-8")
        if 'selected["matchup_norm"].isin(toronto_fix)' not in text:
            raise RuntimeError("Original matchup-only Toronto override is absent")
        selected=pd.read_csv(z.open(
            "nba_player_game_at_risk_core_v1/selected_report_rows_all.csv"),low_memory=False)
        mapping=pd.read_csv(z.open(
            "nba_player_game_at_risk_core_v1/canonical_game_snapshot_map.csv"),low_memory=False)
    subset=selected[
        (selected.season=="2021-22") &
        selected.source_match_number.isin(EXPECTED)
    ].copy()
    if len(subset)!=36:
        raise RuntimeError(f"Expected 36 original Toronto report rows, got {len(subset)}")
    original_ids={}
    for source_num,(count,matchup,expected_game) in EXPECTED.items():
        block=subset[subset.source_match_number.eq(source_num)]
        matched=mapping[(mapping.season=="2021-22") &
                        mapping.source_match_number.eq(source_num)]
        if len(block)!=count or len(matched)!=1 or set(block.matchup_norm)!={matchup}:
            raise RuntimeError(f"Source row provenance mismatch: match {source_num}")
        original_ids[source_num]=matched.game_id.iloc[0]
    repaired=subset.copy()
    canonical=mapping[mapping.season=="2021-22"].set_index(
        "source_match_number").game_id
    repaired["corrected_game_id"]=repaired.source_match_number.map(canonical)
    for source_num,game_id in SOURCE_SWAPS.items():
        repaired.loc[repaired.source_match_number.eq(source_num),"corrected_game_id"]=game_id
    repaired["changed_game_id"]=repaired.game_id.ne(repaired.corrected_game_id)
    changed=repaired.loc[repaired.changed_game_id]
    if len(changed)!=17 or set(changed.source_match_number)!={46,1172}:
        raise RuntimeError("Unexpected historical unrelated-matchup report contamination")
    for source_num,(count,matchup,expected_game) in EXPECTED.items():
        block=repaired[repaired.source_match_number.eq(source_num)]
        if set(block.corrected_game_id)!={expected_game}:
            raise RuntimeError(f"Corrected source {source_num} maps to wrong physical game")
    details=(repaired.groupby(["source_match_number","game_id",
                "corrected_game_id","snapshot_basename"])
             .size().reset_index(name="rows").to_dict("records"))
    result={
        "scope":"August original selected-report mapping audit only; no corrected taxonomy or paper model",
        "historical_builder_sha256":digest,
        "original_selected_report_rows":len(selected),
        "four_source_match_rows":len(repaired),
        "unrelated_october_april_rows_wrongly_attached_to_february":int(len(changed)),
        "source_46_october_rows":7, "source_1172_april_rows":10,
        "two_genuine_february_source_match_numbers":[430,784],
        "details":details,
        "safe_mapping_rule":"Use season and source_match_number for physical game identity; override only source matches 430 and 784, never all CHI@TOR or MIA@TOR rows.",
        "limit":"The original August 248730-row panel, injury taxonomy, onset and models have NOT been reconstructed."
    }
    return result,repaired

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-zip",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    result,repaired=audit(args.core_zip)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    repaired.to_csv(args.output.with_suffix(".csv"),index=False)
    print(json.dumps({k:v for k,v in result.items() if k!="details"},indent=2))

if __name__=="__main__":
    main()
