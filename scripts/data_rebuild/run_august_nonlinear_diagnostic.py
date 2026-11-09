#!/usr/bin/env python3
"""Nonlinear and multinomial August stage: frozen rerun, then a paired diagnostic.

Runs the unchanged scripts/portable/finalize_nonlinear_multinomial_v1.py (which
imports run_nonlinear_multinomial_stage.py) on copied inputs, first with the
frozen August risk panel and then with the corrected one (two Toronto TV
lookup keys repaired in the copy).

The original authors document that this penalized-logit stage is not
reproducible across numeric environments (archived frozen 2.4400 / 0.8271 pp;
pinned Ubuntu CI rerun 2.5060 / 1.2827 pp). The frozen rerun is therefore
compared with both. Unless it matches the archived frozen package, the
corrected run is reported only as a same-environment paired diagnostic and is
not an accepted corrected reproduction.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pandas as pd

from run_august_category_fdr_from_release import PANEL, TV, sha, repair_announcement_fixture_keys
from run_august_released_suite_from_release import (
    CORRECTED_RISK_SHA, PORTABLE, verify_shared)

SCRIPTS = ["finalize_nonlinear_multinomial_v1.py", "run_nonlinear_multinomial_stage.py"]
PACKAGE = "packages/08_nonlinear_multinomial_robustness.zip"
OUT = Path("results/portable_nonlinear_multinomial_final")
TABLES = ["extensive_nonlinear_primary.csv", "classification_nonlinear_primary.csv",
          "multinomial_softmax_ddd.csv"]
# documentation/NONLINEAR_REPRODUCIBILITY_NOTE.md, pinned GitHub Actions rerun.
DOCUMENTED_CI = {"legacy_primary": 2.5060, "harmonized_linear": 1.2827}
EXTRA = [Path("results/canonical_vs_cadence_model_comparison.csv")]


def prepare(shared: Path, root: Path, panel: Path | None):
    if root.exists():
        raise FileExistsError(root)
    for rel in [PORTABLE / s for s in SCRIPTS] + [PANEL, TV] + EXTRA:
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(shared / rel, dest)
    if panel is not None:
        shutil.copy2(panel, root / PANEL)
        return repair_announcement_fixture_keys(root / TV, root / PANEL)
    return None


def run(root: Path, python: str):
    with (root / "nonlinear.log").open("w") as log:
        subprocess.run([python, str(root / PORTABLE / SCRIPTS[0])], cwd=root,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=14400)
    return {t: pd.read_csv(root / OUT / t) for t in TABLES}


def key_of(table: str):
    return ["tv_definition", "class"] if table.startswith("multinomial") else ["tv_definition"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shared-repo", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--corrected-panel", type=Path, required=True)
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()
    shared, work = args.shared_repo.resolve(), args.work.resolve()
    if work.exists():
        raise FileExistsError("Use a new output root")
    verify_shared(shared)
    corrected = args.corrected_panel.resolve()
    if sha(corrected, decoded=True) != CORRECTED_RISK_SHA:
        raise RuntimeError("Corrected August risk panel hash differs")

    prepare(shared, work / "frozen", None)
    frozen = run(work / "frozen", args.python)
    with zipfile.ZipFile(shared / PACKAGE) as z:
        archived = {t: pd.read_csv(z.open(t)) for t in TABLES}
    gate = {}
    for t in TABLES:
        j = archived[t].merge(frozen[t], on=key_of(t), suffixes=("_archived", "_rerun"))
        gate[t] = float((j.average_probability_ddd_pp_archived
                         - j.average_probability_ddd_pp_rerun).abs().max())
    ext = frozen[TABLES[0]].set_index("tv_definition").average_probability_ddd_pp
    ci = {k: float(round(ext[k], 4) - v) for k, v in DOCUMENTED_CI.items()}
    reproduced = all(v <= 1e-6 for v in gate.values())

    rekeys = prepare(shared, work / "corrected", corrected)
    variant = run(work / "corrected", args.python)
    rows = []
    for t in TABLES:
        j = frozen[t].merge(variant[t], on=key_of(t), suffixes=("_frozen", "_corrected"))
        for r in j.to_dict("records"):
            rows.append({"table": t, "row": " | ".join(str(r[k]) for k in key_of(t)),
                         "frozen_rerun_pp": r["average_probability_ddd_pp_frozen"],
                         "corrected_pp": r["average_probability_ddd_pp_corrected"],
                         "delta_pp": r["average_probability_ddd_pp_corrected"]
                         - r["average_probability_ddd_pp_frozen"],
                         "n_frozen": r.get("n_frozen"), "n_corrected": r.get("n_corrected")})
    pd.DataFrame(rows).to_csv(work / "nonlinear_corrected_vs_frozen_rerun.csv", index=False)
    report = {
        "archived_frozen_max_abs_difference_pp": gate,
        "archived_frozen_reproduced": reproduced,
        "difference_from_documented_ci_rerun_pp": ci,
        "tv_rekeys": rekeys,
        "status": ("corrected result accepted" if reproduced else
                   "frozen archive not reproduced in this environment; corrected values "
                   "are a same-environment paired diagnostic only"),
        "paired": rows,
    }
    (work / "august_nonlinear_diagnostic.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "paired"}, indent=2, default=str))


if __name__ == "__main__":
    main()
