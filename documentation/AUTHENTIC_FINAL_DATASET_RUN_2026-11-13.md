# Authentic final dataset reconstruction — 2026-11-13

The private, clean Python 3.12 / pandas 2.2.3 run on Linux amd64 completed the
public `reproduce_final_datasets.py` entrypoint with all 22 authentic source ZIPs
and `--verify-original-pdfs`. The run was executed in a `python:3.12-slim`
Linux amd64 container on Apple Silicon with the repository mounted read-only,
original ZIPs mounted read-only, and output under a separate private mount.
No private player-level CSVs or raw PDFs are committed to Git.

```bash
python scripts/data_rebuild/reproduce_final_datasets.py \
  --archive-dir /archives \
  --output-root /runs/linux-amd64-001 \
  --verify-original-pdfs
```

The full input archive hashes in the private acceptance manifest match every
entry in `scripts/data_rebuild/final_source_sha256.json` (22/22). All six stages
in `logs/stages.jsonl` have exit code zero. Both original PDF-derived August core
and October cadence baselines exactly match the corresponding archived frozen
decoded CSV SHA-256 values. The PDF-derived original reviewed analysis-ready
base and the restored October base each decode to
`5154317fc52157716cf22f7c5a535259e9f073b3391fd52d78a01faaf8d96d77`;
the former was fed to the corrected October builder. The 73,438 PDF-derived,
identity-resolved August selected player rows matched all 33 archived source
fields before they fed both August finalizer passes.

| Final private dataset | Rows | At risk | Onsets | Full decoded CSV SHA-256 |
|---|---:|---:|---:|---|
| August latest-pre-tip full | 248,728 | 180,831 | 12,707 | `2acd7448a357163951700c99df33a6949e20b19afc2219e6f8c3082b14d3619d` |
| August latest-pre-tip at risk | 180,831 | 180,831 | 12,707 | `5a5d286b18029c1ba9ea1447f6237c3e7cc671df710d68b2a2bad34d4d65e1f3` |
| October cadence full | 248,778 | 180,664 | 12,729 | `2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67` |

The four original corrected Stage-6 specifications ran. The full-control
complete-case sample has 180,530 observations. National-partner TV is
`+2.674231729236583` percentage points (`p=0.0426339657858427`); linear-TV-only
is `+1.2823694527266345` percentage points (`p=0.3308675408175168`). These
values were read from the generated model report, not supplied as inputs.

The private evidence bundle `NBA_PPP_Final_Run_Evidence_2026-11-13.zip` is
preserved with the original researcher. Its SHA-256 is
`47aef092adf4125057e3c7f11e7efcb1b7ae2a1a966dc417efde04c5c411d011`;
the included final manifest SHA-256 is
`0044eeccea695433d02ce7833f88b15aca4754cd739382b3d0de6168ec62215a`.
It contains only JSON manifest, QA, model, handoff and structured stage events.
The accepted manifest's older `source_level` prose still says the corrected
cadence is entirely archived. That text is stale: the same manifest's explicit
`pdf_to_october_base_handoff` object, the handoff JSON and the completed stage
log demonstrate the exact PDF-derived original base substitution. The public
manifest description was corrected after the run; this metadata-only change
does not alter the accepted dataset bytes or the preserved run evidence.

## Reproduction environment and failure resolved

The same authentic ZIPs passed `--check-only` on macOS arm64. Running the
historical original finalizer natively on that architecture generated panels
with different floating-point serialization in seven Elo/travel fields
(for example `38.98341382733452` versus `38.98341382733451`). The selected
report rows and eight other original core outputs matched byte for byte. The
pipeline correctly refused to accept the native panels; no checksum was
weakened and no frozen data were substituted. The Linux amd64 container
reproduced the exact original panel bytes and completed all downstream stages.
Keep the failed native output separate from accepted runs.

On an Apple Silicon host with Docker, from the repository checkout:

```bash
mkdir -p "$HOME/nba-reproduction-runs"
docker run --rm --platform linux/amd64 \
  -v "$PWD:/repo:ro" \
  -v "$HOME/nba-original-zips:/archives:ro" \
  -v "$HOME/nba-reproduction-runs:/runs" \
  -w /repo python:3.12-slim \
  sh -lc 'python -m pip install --no-cache-dir -r requirements-builder-lock.txt && python scripts/data_rebuild/reproduce_final_datasets.py --archive-dir /archives --output-root /runs/linux-amd64-002 --verify-original-pdfs'
```

Use a new output root for every run. The exact accepted run used
`/runs/linux-amd64-001` and should not be overwritten.

## Remaining source boundary

The original NBA box-score JSON is not a direct input to this command. The
historical roster, game covariates, October season-specific report selection,
and validated human injury/award/Cup/TV decisions remain inherited from pinned
source archives. The original box-score cache verifier is a separate provenance
path. The outstanding independent human classification and original-source
exceptions stay open in Issue #5. This run establishes exact reproduction of
the accepted ultimate datasets from the documented mix of original PDFs and
verified historical inputs, not a complete all-primary-source reconstruction.
