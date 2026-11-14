# Authentic original-PDF and NBA-JSON final dataset run — 2026-11-13

**Branch:** `audit-rebuild-reliability-2026-11` (PR #4, draft).  
**Code:** `18abb2dda84fef34128cbb9643c5f9481080c939` for the seven executed Linux amd64 stages; `ab45ad376d60d2582c39f74ba1a92c687fba685b` for strict finalization of those completed stages.  
**Private output:** `~/nba-reproduction-runs/linux-amd64-json-002/final/`.  
**Evidence reviewed:** the user-supplied private `NBA_PPP_Raw_JSON_Final_Evidence.zip`, SHA-256 `ec428dbf309a9f3c335af648517941869ec91d5312455ef6ce582d18827122c5`. This ZIP contains seven JSON/JSONL reports, not the original JSONs, PDFs or player-level CSVs. The source bytes and final CSVs were checked by the recorded private run; the reports were independently cross-checked against pinned repository expectations here. They were not independently reexecuted in this workspace.

## Execution and checks

The 22 supplied original historical ZIP hashes exactly match `scripts/data_rebuild/final_source_sha256.json`. The `stages.jsonl` evidence has exactly one ordered start and successful finish for each stage: original six-season PDF baseline, original 7,230-JSON box-score roster, August source correction, August analysis-ready, frozen October cadence, PDF-derived October base handoff, and corrected October cadence. `--finalize-existing` checked that evidence and all dataset/model gates after a post-stage checker path error was corrected; the manifest explicitly records `stages_reused_from_completed_private_run: true`.

The original NBA JSON cache verifier reports 7,185 V1 and 45 discovery JSON files, 7,230 unique official game IDs, no filename/season mismatch and no discrepancy from 7,185 logged V1 byte lengths. The SHA-pinned original repair script rebuilt all four V2 tables with zero missing/extra keys or differing comparable cells: 7,230 game crosswalk rows, 7,230 game manifest rows, 248,571 roster rows and 14,460 team-game rows. All 248,571 roster rows match the published base panel on comparable data. The source-to-August handoff compared every non-path cell exactly, validated the season and official JSON game ID encoded in both paths, and retained the historical `raw_json_path` because all 248,571 regenerated paths have a container-specific prefix. The original frozen August baseline and corrected finalizer passed after this handoff.

| Accepted corrected CSV | Rows | At risk | Onsets | Complete decoded CSV SHA-256 |
|---|---:|---:|---:|---|
| August latest-pre-tip full | 248,728 | 180,831 | 12,707 | `2acd7448a357163951700c99df33a6949e20b19afc2219e6f8c3082b14d3619d` |
| August latest-pre-tip at-risk | 180,831 | 180,831 | 12,707 | `5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3` |
| October cadence-harmonized full | 248,778 | 180,664 | 12,729 | `2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67` |

All four corrected Stage-6 models were run. The full-control specifications each use 180,530 complete cases. The corrected legacy national-partner TV estimate is **+2.674231729 pp**, SE **1.319124173 pp**, p **.042633966**; the linear-TV-only estimate is **+1.282369453 pp**, SE **1.318810930 pp**, p **.330867541**. These match the independently pinned accepted targets within the runner's `1e-8` coefficient/p-value tolerance. The detailed model report also records the no-controls fits. The corrected October report records the two physical-game chronology changes, report reassignment, scheduling/history changes and resulting model refits.

[GitHub Actions run 43472186400](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/43472186400) passed **11/11** jobs for the finalization commit. Those public tests have no access to the private original sources and are separate from this authentic execution.

## Boundaries and retained evidence

This is a successful **original PDF + original NBA JSON to corrected August** path, plus a PDF-derived original reviewed analysis base handoff into corrected October. The original six-season PDF baseline and October season-specific selector still inherit historical roster/selection intermediates, and October does **not** consume a newly rebuilt raw-PDF season selector or the JSON-derived roster directly. Historical game covariates and manually reviewed injury, identity, star/award, Cup and TV decisions remain pinned inherited inputs. Original per-game download SHA-256 values were not preserved; the new cache manifest hashes the current 7,230 JSON bytes and checks the original download log's recorded sizes. These limitations remain tracked in [Issue #5](https://github.com/ahmetcopur/nba-load-management-ppp/issues/5); PR #4 stays draft and unmerged.

The failed native macOS run and the first Linux JSON run are retained separately. The former failed frozen Elo/travel byte comparison on arm64; the latter completed raw-source stages but failed on a machine-dependent `raw_json_path` comparison. The accepted Linux run completed every builder and was finalized only after the incorrect August report lookup path was fixed. Neither earlier failure wrote an accepted manifest. The private source ZIPs and frozen release files were not modified, and no raw archives or player-level CSVs were uploaded to GitHub.
