#!/usr/bin/env python3
"""Level C check of advance national-TV assignments against raw release PDFs.

Reads the five archived release-time "schedule by date" PDFs (2021-22 to
2025-26) inside packages/03_announced_tv_six_seasons.zip, rebuilds every
schedule row independently from the PDF text (one cell per text line), and
compares it with
  1. the archived parsed rows (source_schedule_rows_2021_22_to_2025_26.csv),
  2. the source_page, source_line and network_announced of every fixture in
     data_intermediate/announced_tv_six_seasons.csv for those seasons.
2020-21 used web pages, not a PDF, and is reported as outside this check.
Reads the archive only. Writes one JSON report.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

import pandas as pd
import pymupdf

ROOT = "nba_announced_tv_six_seasons_v1/seasons_2021_22_to_2025_26_audit/"
SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
DAY = re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\.$")
DATE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2}$")
TIME = re.compile(r"^(\d{1,2}:\d{2} (AM|PM)|TBD)$")
GAME = re.compile(r"^\d{1,4}$")
# Single-letter schedule markers printed after the network column.
# R: ESPN Radio, C or I: Cup group play, A to E: arena notes.
MARKERS = {"R", "A", "B", "C", "D", "E", "I"}
# Page headers, footers and legends that follow the last row of a page.
FOOTER = re.compile(r"SUBJECT TO CHANGE|SCHEDULE|AS OF|^PAGE \d+ of \d+|^#| = | - ")
# The archive records NBA TV Center Court broadcasts as NBA TV.
CENTER_COURT = "NBA TV (CC)"
FAIL_KEYS = ["duplicate_page_lines_in_pdf", "rows_only_in_pdf", "rows_only_in_archived_parse",
             "network_mismatches", "fixtures_not_found_on_stated_page",
             "fixture_network_mismatches"]


def pdf_rows(data: bytes):
    """Return (page, cells) for every schedule row in one PDF.

    A row starts at a weekday cell followed by a date cell, with the game
    number cell before it when the season prints one.
    """
    rows = []
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        for page_number, page in enumerate(doc, start=1):
            lines = [x.strip() for x in page.get_text().splitlines() if x.strip()]
            starts = []
            for i in range(len(lines) - 1):
                if DAY.match(lines[i]) and DATE.match(lines[i + 1]):
                    starts.append(i - 1 if i and GAME.match(lines[i - 1]) else i)
            for n, start in enumerate(starts):
                end = starts[n + 1] if n + 1 < len(starts) else len(lines)
                rows.append((page_number, lines[start:end]))
    return rows


def split_cells(cells):
    """Some rows put a time and the network, or the network and R, in one line."""
    out = []
    for cell in cells:
        m = re.match(r"^(\d{1,2}:\d{2} [AP]M|TBD)\s+(.+)$", cell)
        parts = [m.group(1), m.group(2)] if m else [cell]
        for part in parts:
            if len(part) > 2 and part[-2] == " " and part[-1] in MARKERS:
                out.extend([part[:-2].strip(), part[-1]])
            else:
                out.append(part)
    return out


def parse(cells):
    """Split cells into date, away, home, local, ET and trailing tokens."""
    cells = split_cells(cells)
    date = next(i for i, c in enumerate(cells) if DATE.match(c))
    times = [i for i, c in enumerate(cells) if TIME.match(c)]
    if len(times) < 2:
        raise ValueError(f"Row without local and ET times: {cells}")
    local, et = times[0], times[1]
    # 2024-25 and 2025-26 print "Away at Home" ("vs" at neutral sites).
    teams = [c for c in cells[date + 1:local] if c not in ("at", "vs")]
    if len(teams) != 2:
        raise ValueError(f"Row without exactly two team cells: {cells}")
    # The page footer after the last row of a page is not part of the row.
    trailing = []
    for cell in cells[et + 1:]:
        if FOOTER.search(cell):
            break
        trailing.append(cell)
    network = " ".join(c for c in trailing if c not in MARKERS) or None
    return {"away": teams[0], "home": teams[1],
            "center_court": network == CENTER_COURT,
            "network": "NBA TV" if network == CENTER_COURT else network,
            "line": " ".join(cells[:et + 1] + trailing)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shared-repo", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError("Write the report to a new file")
    package = args.shared_repo / "packages/03_announced_tv_six_seasons.zip"
    table = pd.read_csv(args.shared_repo / "data_intermediate/announced_tv_six_seasons.csv",
                        low_memory=False)
    report = {"package_sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
              "seasons": {}}
    with zipfile.ZipFile(package) as z:
        archived = pd.read_csv(io.BytesIO(z.read(ROOT + "source_schedule_rows_2021_22_to_2025_26.csv")))
        for season in SEASONS:
            data = z.read(ROOT + f"raw_pdfs/{season}_schedule_by_date.pdf")
            pdf = pd.DataFrame([dict(parse(cells), source_page=page)
                                for page, cells in pdf_rows(data)])
            key = ["source_page", "line"]
            arch = archived[archived.season.eq(season)].rename(columns={"source_line": "line"})
            joined = arch.merge(pdf, on=key, how="outer", indicator=True,
                                suffixes=("_archived", "_pdf"))
            both = joined[joined._merge.eq("both")]
            fixtures = table[table.season.eq(season) & table.source_line.notna()].rename(
                columns={"source_line": "line"})
            fx = fixtures.merge(pdf, on=key, how="left", indicator=True,
                                suffixes=("_table", "_pdf"))
            found = fx[fx._merge.eq("both")]
            report["seasons"][season] = {
                "pdf_sha256": hashlib.sha256(data).hexdigest(),
                "pdf_rows": len(pdf),
                "duplicate_page_lines_in_pdf": int(pdf.duplicated(key).sum()),
                "archived_parsed_rows": len(arch),
                "rows_matched_exactly": len(both),
                "rows_only_in_pdf": int(joined._merge.eq("right_only").sum()),
                "rows_only_in_archived_parse": int(joined._merge.eq("left_only").sum()),
                "network_mismatches": int(both.network_announced.fillna("").ne(
                    both.network.fillna("")).sum()),
                "network_counts_pdf": pdf.network.fillna("none").value_counts().to_dict(),
                "nba_tv_center_court_rows_recorded_as_nba_tv": int(pdf.center_court.sum()),
                "network_mismatch_examples": both[both.network_announced.fillna("").ne(
                    both.network.fillna(""))].head(6)[["line", "network_announced", "network"]]
                .astype(str).to_dict("records"),
                "fixtures_with_source_line": len(fixtures),
                "fixtures_not_found_on_stated_page": int(fx._merge.ne("both").sum()),
                "fixture_network_mismatches": int(found.network_announced.fillna("").ne(
                    found.network.fillna("")).sum()),
                "fixtures_without_source_line": int(
                    table[table.season.eq(season)].source_line.isna().sum()),
                "unmatched_examples": joined[joined._merge.ne("both")].head(6)[
                    key + ["_merge"]].astype(str).to_dict("records"),
            }
    report["outside_check"] = ("2020-21 advance TV came from archived ESPN/TNT/NBA TV "
                               "web pages, not a release PDF")
    failures = {season: {k: v[k] for k in FAIL_KEYS if v[k]}
                for season, v in report["seasons"].items()
                if any(v[k] for k in FAIL_KEYS)}
    report["all_release_rows_and_networks_match"] = not failures
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps(report, indent=2, default=str))
    if failures:
        raise SystemExit(f"Release PDF and TV table disagree: {failures}")


if __name__ == "__main__":
    main()
