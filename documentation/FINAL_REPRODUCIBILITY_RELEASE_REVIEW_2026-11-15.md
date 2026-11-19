# Final reproducibility and release review — November 15

**Decision: ready for independent review with declared limitations; a combined raw-source release freeze remains blocked.** No new authentic six-season PDF + 7,230 NBA JSON execution was performed in this audit. The authentic JSON payload cache is not accessible here. PR #4 stays draft/unmerged; Issue #5 remains open. No release tag was created.

Reviewed evidence head: `c0ce14f2765fc1da7968a786b220ee16c4655349`. The accepted six-season execution used `ddef0b805bc3615cec8caa19c798e36e4c4df9be`. This review's code changes are safety/instrumentation changes, not executions of the combined pipeline. [Machine-readable audit](../validation/final_release_audit_2026-11-15/audit.json).

## A. Combined execution and cache availability

The canonical runner already combines both features into **nine stages**. The JSON verifier executes in its separate pandas 3.0.5 environment; its newly generated roster feeds the original and corrected August finalizers. The baseline core then feeds `01b_json_pdf_original_reviewed_base`, whose decoded output must match before the corrected October base handoff. All six source reconstructions feed the frozen October builder; the corrected builder must consume all 18 inputs after only the two declared 2021 selector files are chronologically adjusted. There is no permitted archived-roster fallback after failure of the JSON stage. The initial independent PDF verification baseline still uses the archived roster; it is a reference check, distinct from the subsequent JSON-derived August baseline.

This is static compatibility and focused-test evidence, not a new authentic combined acceptance. The November 14 JSON run predates the latest six-season combination; the November 15 seven-stage six-season run did not parse original JSONs. Combining those two past successes is not proof that the new nine-stage execution succeeded.

The workspace inventory found **zero official game JSON payload files**, and **zero raw-game-JSON-containing archives among 43 distinct ZIP name/size pairs**. Verification JSON reports were excluded from payload counts. Searches for the documented cache names found repair/code ZIPs, derived roster outputs and evidence, not the complete cache. The historical user-machine `nba-load-audit` paths are not mounted in this Linux environment. This does not establish that those files have been lost from the owner's computer.

Required unavailable inputs are the original V1 directory with **7,185 JSONs and `download_log.csv`**, plus **45 original discovery JSONs**. The 25,704-byte repair ZIP and 8,709-byte V1 code ZIP cannot replace those payloads. The 9,727,277-byte V2 output ZIP contains derived tables; the small JSON evidence ZIP contains verification reports. Downloading current NBA responses would not establish the original snapshot identities.

### Combined command on a machine holding the authentic cache

From the repository root, with all 26 pinned source ZIPs in the private archive directory and Docker available, use a new output name. Validate host directories/files exist first: Docker's `--mount` refuses nonexistent sources. The command intentionally installs the two separate locked environments; `--check-only` must pass before any builder starts.

```bash
mkdir -p "$HOME/nba-reproduction-runs"
docker run --rm --platform linux/amd64 \
  --mount "type=bind,source=$PWD,target=/repo,readonly" \
  --mount "type=bind,source=$HOME/nba-original-zips,target=/archives,readonly" \
  --mount "type=bind,source=$HOME/nba-load-audit/nba_boxscore_roster_frame_v1_output,target=/boxscore-v1,readonly" \
  --mount "type=bind,source=$HOME/nba-load-audit/nba_boxscore_roster_frame_v2_output/raw_json_discovery,target=/boxscore-discovery,readonly" \
  --mount "type=bind,source=$HOME/nba-load-audit/nba_boxscore_roster_frame_v2_repair.zip,target=/repair.zip,readonly" \
  --mount "type=bind,source=$HOME/nba-reproduction-runs,target=/runs" \
  -w /repo python:3.12-slim sh -ec '
    python -m venv /tmp/nba-builder
    /tmp/nba-builder/bin/python -m pip install --no-cache-dir -r requirements-builder-lock.txt
    python -m venv /tmp/nba-boxscore
    /tmp/nba-boxscore/bin/python -m pip install --no-cache-dir -r requirements-boxscore-lock.txt
    set -- --archive-dir /archives --output-root /runs/linux-amd64-six-pdf-json-001 \
      --verify-original-pdfs --rebuild-six-season-october-sources \
      --boxscore-v1 /boxscore-v1 --boxscore-discovery /boxscore-discovery \
      --boxscore-repair-zip /repair.zip --boxscore-python /tmp/nba-boxscore/bin/python
    /tmp/nba-builder/bin/python scripts/data_rebuild/reproduce_final_datasets.py "$@" --check-only
    /tmp/nba-builder/bin/python scripts/data_rebuild/reproduce_final_datasets.py "$@"
  '
```

This is a runnable command, **not a record of a run performed here**. Before release, resolve the selected Python image to an immutable digest and record it with interpreter/package versions; the convenience tag above is mutable. Do not use `--finalize-existing` to represent old stages as executions of the new safety checks.

Inspect `logs/stages.jsonl`, `00b_original_boxscore/boxscore_cache_verification.json`, `01_august_core/august_core_source_correction_report.json`, both August `finalizer_input_consumption.json` reports, the two October `replay_environment.json` reports, and `final/final_dataset_manifest.json`. New guards require both August finalizers to actually open the report/roster inputs and leave their before/after hashes unchanged; acceptance rehashes those inputs again. Both October builders must report all 18 generated files actually opened. Keep all player records, payloads and full private reports outside Git.

Independently hash new outputs using `set -o pipefail; gzip -cd FILE.csv.gz | sha256sum`. Perform the schema/key/count checks and compare every scientific regression field; elapsed `seconds` can differ. Preserve both scientific and historical-artifact verdicts.

## B. Existing scientific acceptance, revalidated without reconstruction

The three **existing November 15 seven-stage outputs** were decoded and rehashed during this audit. All 26 private original ZIPs were also rehashed and remain unchanged. No prior final dataset was copied to a new run root. These are integrity checks on accepted outputs, not fresh combined results.

| Existing dataset | Rows | At risk | Onsets | Decoded SHA-256 |
|---|---:|---:|---:|---|
| August full | 248,728 | 180,831 | 12,707 | `2acd7448a357163951700c99df33a6949e20b19afc2219e6f8c3082b14d3619d` |
| August at risk | 180,831 | 180,831 | 12,707 | `5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3` |
| October cadence | 248,778 | 180,664 | 12,729 | `2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67` |

| Previously executed corrected model | N | Estimate (pp) | p |
|---|---:|---:|---:|
| National-partner, full | 180,530 | 2.6742317292365767 | .0426339657858416 |
| Linear-only, full | 180,530 | 1.2823694527266445 | .3308675408175164 |
| National-partner, none | 180,664 | 2.676885495644326 | .0435317747821202 |
| Linear-only, none | 180,664 | 1.2948513321879846 | .3291224141374449 |

The earlier [six-season verification](SIX_SEASON_CONNECTED_REPRODUCTION.md) records exact scientific-field equality, including SEs/confidence limits, and explicitly separates runtime metadata. Those models were not reexecuted in this audit. No contradictory scientific finding emerged.

## C. Dependency and provenance review

The existing machine-readable graph uses an older A–E vocabulary. In **this review**, A means recomputed/consumed authentic source, B means versioned human/methodological/metadata input, C means inherited computational intermediate, D means unresolved evidence. Old graph B maps to review C; old D maps to review B; old E maps to review D. Mixed nodes must retain mixed classifications. A graph's available optional mode is not evidence that it executed in the accepted seven-stage run.

| Input family | Review class and actual boundary | Consequence / smallest justified next action |
|---|---|---|
| Six-season PDF rows, canonical selectors, team statuses | A; observed in accepted cumulative and final PDF run | 18 actual opens per October builder; historical clocks remain B/D. No further reparsing required until the fresh combined test. |
| NBA JSON roster and fixture/official-ID crosswalk | C in seven-stage run; A in prior separate authentic JSON execution | Available code is connected when all JSON options are supplied. Supply authentic cache and run the existing nine-stage command. Original download hashes were not preserved; current hashes cannot certify acquisition-time bytes (D). |
| Original publication/acquisition manifests and S4 schedules | B for saved immutable observations; D for unavailable observations/snapshots | Hash-pinned historical inputs are required. Do not invent times or infer unavailability from missing evidence. Exact schedules are inputs to algorithms, not newly recollected primary evidence. |
| Game covariates, Elo, rest, travel, fixture/venue mappings | C, with pinned source schedules; documented chronology calculations are rerun | Original calculation replay exists, but the final path still inherits non-date covariate inputs. This is a real primary-source completeness boundary, not a human adjudication. Smallest further connection would feed the independently replayed covariate tables and require complete-cell equality; this audit does not initiate that campaign. |
| Player/report identities and alias crosswalks | A for replayed selected-report assignment, B for reviewed alias choices, C for inherited October crosswalk serialization | Preserve reviewed mappings. Deterministic crosswalk replay has code but the October leaf still restores the historical table. Connecting that generated leaf would need exact key/cell checks, not new identity guesses. |
| Awards and star timelines | B for original lookup/identity decisions; C for inherited calculated timeline/enrichment values | Separate source lookup choices from calculable transforms. Original replay exists; direct final enrichment still inherits annotations. Exact final hashes establish replay with these inputs, not independently recollected awards. |
| Cup and advance-TV mappings | B for documented mapping/nominal-host decisions; C for inherited computed joins; D for unavailable original announcement/acquisition observations | Source schedules and reviewed mappings are pinned. No new Cup/TV adjudication is justified to relabel this as raw-source complete. |
| Reviewed injury taxonomy | B | Legitimate human-reviewed input; no replacement classification was invented. Independent human classification review remains a separate scientific task. |
| 2025 S4 team join | A for generated variant consumed; D for missing original join implementation | Preserve the established exception below. Historical-artifact reconstruction is incomplete. |

The complete restored leaf inventory and generating-script references remain in [the dependency graph](FINAL_DATASET_DEPENDENCY_GRAPH_2026-11-14.json). The surviving C inputs affect scientific values, so an unrestricted “every computational intermediate regenerated from primary sources” claim is unsupported. They do not invalidate the demonstrated exact reconstruction **conditional on the explicitly pinned research inputs**. Source authenticity and independent human judgment remain different questions from numerical reproducibility.

### Established 2025 exception

The controlled experiment already established 1,598 rows/3,196 cells differing only in `team_final_status` and `inferred_no_listed_players`, with unchanged `usable_submitted_status`, complete scientific panels and all four regressions. The original join program remains missing. No new contradictory evidence appeared; the experiment was not reopened. Preserve `scientific_output_verdict: pass` for the accepted PDF run and `historical_artifact_verdict: 2025_metadata_exception_unresolved`. A new combined run has no scientific verdict yet.

## D. Engineering and publication review

Focused changes enforce fresh/private/disjoint/symlink-safe standalone JSON outputs; reject missing V1 log records and incorrect 7,185/45 full-cache partitions; rehash all JSONs, download log, repair source, fixture/reference/base inputs after repair; trace actual August report/roster reads; recheck their digests in final acceptance; and retain that consumption proof in the native manifest. The original scientific programs and immutable expected hashes were not changed. Existing original repair-member SHA checks and its documented one-line QA serialization fix remain intact.

**652 local tests passed.** New tests cover source mutation, missing log metadata, symlinked payloads/output paths, existing/Git/overlapping output roots, source partitions, the combined nine-stage plan, no downstream fallback after JSON failure, August subprocess omissions/mutations and corrupted consumption evidence. Synthetic tests are not authentic combined acceptance. An additional real execution of the pinned **original August finalizer only**, with historical archived inputs, exercised the new actual-open wrapper and reproduced baseline core SHA `253bf017095a8be45f4c7bb4a0abcc9b942a8db6311f91131c9fd12c7ab46de3`; both required inputs were read and remained unchanged. This small probe did not parse any raw JSON or rerun the six-season pipeline.

The full PR changed-file inventory at the reviewed evidence head contains 298 text files. No newly added raw JSON payloads, source ZIPs or private bulk final datasets were found; the largest added file is a 1,163,163-byte per-game SHA manifest. Common credential-pattern scanning found no matches, which is not a guarantee against every possible secret. Frozen inputs and repository history were not rewritten. Machine-specific scratch paths appear in a dated historical command record, not an active runtime requirement; new instructions use mounted private paths.

**Publication decision still required:** four existing chronology diagnostic CSVs contain 0, 2, 10 and 20 player-game records respectively (`changed_absence_now_harm`, `changed_absence_onset_harm`, `changed_at_risk_for_new_onset_harm`, `changed_designation_status`, under `validation/fixture_date_chronology_2026-11-08/`). These are derived individual-level diagnostic rows, even though the underlying athletes are public figures. This audit does not assume their publication is authorized. No additional player rows were published, and no historical evidence was deleted. Owner review must decide whether the existing records are suitable for a release and, if necessary, explicitly authorize remediation.

## E. Release checklist and answers

- [x] Existing six-season cumulative and final scientific results accepted and current output bytes rehashed.
- [x] Existing runner supports both feature sets; focused failure/consumption tests pass.
- [x] Source requirements, inherited computational leaves and human decisions distinguished.
- [x] Separate 2025 scientific/artifact verdicts retained.
- [ ] Authentic fresh nine-stage PDF+JSON execution; independent hashes, keys/schemas/counts and all scientific model fields verified.
- [ ] Owner publication/privacy decision on existing diagnostic player records.
- [ ] Final CI green at the proposed freeze commit; immutable execution-image identity recorded.
- [ ] Owner approval of freeze/tag/merge. No tag or merge performed.

**Q1 — Can both paths execute together?** The existing nine-stage plan supports it and focused tests pass; successful authentic combined execution is **not yet demonstrated**.

**Q2 — Did that combined run reproduce all three hashes?** **Not demonstrated; no combined run occurred.** Existing seven-stage outputs still have all three accepted hashes.

**Q3 — Did all four models reproduce exactly?** **Yes in the previously accepted six-season PDF run; not demonstrated in a new combined execution.** Runtime `seconds` is excluded only from scientific equality.

**Q4 — Are inherited computational and human inputs transparent?** **The enumerated inputs are now classified explicitly in this review and linked inventory.** This is disclosure, not a claim that class C has been eliminated or every historical observation is recoverable.

**Q5 — Does unresolved provenance materially undermine the results?** No new scientific discrepancy was found. The known 2025 difference demonstrably does not change these results. Missing cache/clock evidence and inherited computational leaves limit primary-source independence/authenticity claims; they are not proof that the accepted numerical results are wrong.

**Q6 — Ready for review/freeze?** **Independent review: yes, with these declared limits. Combined raw-source freeze: not yet.** Retain `c0ce14f`/`ddef0b8` as the accepted PDF evidence/execution points. After the remaining gates pass, propose an immutable `nba-ppp-reproducibility-2026-11` tag at the actually executed and CI-verified final commit, subject to owner approval. Do not tag the current audit as a passed combined execution.
