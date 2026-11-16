# Decision record: adopt SCI-001 as the primary October analysis (November 16, 2026)

**Decision.** The repository owner adopts the SCI-001-corrected October panel (`october_scientific_v2`, decoded SHA-256 `9dde4578c852f15c317c1214718e1eabe9f60b740b5f2ddb4fed15b53185802f`) as the primary October analysis. The legacy and frozen results are kept, unchanged, as historical references.

## Rationale: conformance to the pre-stated rule

The star definition was written down before this correction existed. [FROZEN_SPECIFICATION.md](FROZEN_SPECIFICATION.md) (line 10), committed with the August 12, 2026 freeze (`0693cf4`), says:

> At opening night, a player is a star if selected to an All-Star or All-NBA team in any of the prior three seasons. Newly selected current-season All-Stars become stars after that season's All-Star Game.

The original October builder broke this rule for report-only additions: it omitted the `current_season_all_star` condition (`scripts/executed/06_cadence_harmonized_identification/build_harmonized_panel_and_models.py:232-235`). As a result, 49 non-star report-only rows were flagged as stars, including 12 at-risk onsets (9 before the policy, 3 after). The audit found this (finding SCI-001, `validation/scientific_integrity_audit_2026-11-15/findings.json`), and an independent review reproduced it from the public frozen panels. The August panels already follow the rule (0 mismatches in either `data_final` panel), so the correction also makes October consistent with August.

**The change in statistical significance is not a reason for adoption.** The correction would be adopted whichever way the estimate moved.

## Effect, reported in full

Original player + team-season fixed-effects linear probability model; two-way player/game clustering; N = 180,530 (full controls).

| October version | Status | National-partner TV, full controls | Linear-only TV, full controls |
| --- | --- | --- | --- |
| Frozen, Aug 12 (`3c161f95…`) | Historical reference | +2.630 pp, 95% CI [0.046, 5.215], p = .046 | +1.239 pp, p = .347 |
| Legacy corrected chronology (`2409b501…`) | Historical reference | +2.674 pp, 95% CI [0.089, 5.260], p = .043 | +1.282 pp, p = .331 |
| **Scientific-v2 / SCI-001 (`9dde4578…`)** | **Adopted primary** | **+3.064 pp, 95% CI [0.511, 5.616], p = .019** | **+1.661 pp, p = .202** |

The correction strengthened the national-partner estimate. The linear-only (harmonized TV) estimate remains non-significant, so that sensitivity's conclusion does not change. Publications should report the legacy estimate alongside the adopted one and state the direction of the change.

## Scope and disclosure

- **How the adopted panel was produced:** by `scripts/data_rebuild/reproduce_october_scientific_v2.py` from the owner-authenticated retained intermediates ([execution record](AUTHENTIC_SCI001_CORRECTED_BUILDER_2026-11-15.md)). The full raw-source rebuild, `reproduce_final_datasets.py`, still produces the legacy panel. Until that rebuild is extended, publications should state this.
- **Unchanged:** the frozen data, original executed scripts, legacy strict hashes and acceptance gates, and the original manuscript. Scientific-v2 changes only `star_PPP_it`; outcomes, risk sets, samples and controls are identical.
- **Not decided here:** publication permissions for player-level data (PRIV-001), external peer review, and the SCI-002 workload sensitivities, which remain unadopted.
