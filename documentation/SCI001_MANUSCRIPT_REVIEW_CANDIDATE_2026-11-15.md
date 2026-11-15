# SCI-001 manuscript and review candidate — November 15, 2026

The separate revised manuscript has been compiled and inspected on all 21 pages.
The original November 13 LaTeX and 20-page PDF are unchanged. The new copy is a
private review deliverable, not a publication, signed certification or approved
scientific freeze. PR #4 remains draft/unmerged; Issue #5 stays open.

## Actual computational acceptance

The [authentic corrected-builder report](AUTHENTIC_SCI001_CORRECTED_BUILDER_2026-11-15.md)
records the localized retained-intermediate reconstruction, all four original
models, actual input-open evidence and all ten downstream scripts. No expensive
PDF, roster or panel reconstruction was repeated for the manuscript update.

| Current SCI-001 primary model | Estimate (pp) | 95% CI | p | N |
| --- | ---: | --- | ---: | ---: |
| National-partner TV, full controls | 3.063532484315 | [0.510829, 5.616236] | .018661654 | 180,530 |
| Linear-only TV, full controls | 1.661214200215 | [-0.892440, 4.214868] | .202299392 | 180,530 |

The scientific panel decoded SHA-256 is
`9dde4578c852f15c317c1214718e1eabe9f60b740b5f2ddb4fed15b53185802f`.
The legacy corrected panel remains separately verified at
`2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67`.
Both contain 248,778 rows, 180,664 at risk and 12,729 onsets. Exactly 49 star
flags change; outcomes, risk sets, controls and all other panel cells do not.

The manuscript's five existing Table 4 subset checks required refreshing. The
new runner executes the original `run_base.py` model-function prefix from clean
shared commit `0bd713d97e8d519df5700ef473da34aba4495223`, with its original fixed
effects, controls, convergence and covariance calculations. It substitutes only
private input/output paths and adds fixed calls for the already documented
samples. Both accepted legacy and scientific panel hashes are required.

```bash
python3.12 -m venv "$HOME/.venvs/nba-october-analysis"
"$HOME/.venvs/nba-october-analysis/bin/python" -m pip install -r requirements-october-lock.txt
"$HOME/.venvs/nba-october-analysis/bin/python" scripts/data_rebuild/replay_manuscript_subset_checks.py \
  --scientific-run /absolute/private/scientific-execution \
  --shared-repo /absolute/private/pinned-clean-shared-checkout \
  --output-root /absolute/private/new-manuscript-subset-execution
```

The scientific run must already contain accepted `chronology__legacy/` and
`chronology__october_scientific_v2/` panels; the shared checkout must contain its
original All-Star-only linkage input. The command uses a fresh output directory.
It executes five models per version and saves complete coefficient tables,
source hashes, actual input-open receipts and before/after input hashes.

| Existing subset | SCI-001 estimate (pp) | p | N |
| --- | ---: | ---: | ---: |
| Exclude 2025–26; both TV definitions coincide | 2.604135 | .054209 | 149,873 |
| Exclude 2020–21/2021–22; linear-only | 2.197736 | .205862 | 123,449 |
| Exclude 2020–21/2021–22; national-partner | 3.647712 | .028065 | 123,449 |
| Common 2021–22 through 2024–25; national-partner | 1.951796 | .185064 | 123,074 |
| Same common sample, adding NBA TV | 0.863119 | .434566 | 123,074 |

All ten fits converged and consumed the required new inputs. Legacy sample sizes
match exactly; coefficients reproduce the old manuscript at its published
two-decimal precision. This is **not** an exact decoded-byte comparison to a
historical subset-results CSV, which was not supplied. The existing complete
panel identities and original primary-model gates are unchanged. Network codes
outside the documented common-sample set, malformed booleans, missing or changed
panels and overwritten output paths fail closed.

[Aggregate coefficients](../validation/october_scientific_v2_2026-11-15/manuscript_subset_models.csv)
and [actual execution provenance](../validation/october_scientific_v2_2026-11-15/authentic_manuscript_subset_acceptance.json)
contain no player-level records.

## SCI-002 scope decision

Retain the original roster-record workload convention in the primary SCI-001
version and describe it literally. The physical-game reinterpretation remains
blocked: six player/timestamp groups contain twelve distinct game associations,
four at-risk onsets and one positive-minute record. One positive-minute group
also contains a zero-minute at-risk association. No missing acquisition clock,
within-timestamp physical order or historical intention is fabricated.

The already executed original `audit_models.py` omission check removes all
three workload/progress controls. National-partner TV is +3.052996 pp (95% CI
[0.492387, 5.613604], p=.019445), and linear-only is +1.663073 pp (95% CI
[-0.903473, 4.229618], p=.204069), both N=180,530. Reporting these existing checks
bounds observed dependence on that control family; it does not validate a unique
physical-history definition. No new sensitivity specification was searched for
or adopted to force the main result.

## Manuscript preparation and inspection

The authentic matching editable source was located. Compiling it unmodified
produces extracted text identical to the owner's current 20-page PDF. A separate
SCI-001 copy then updates the abstract, raw cells, Table 4, home/road results,
return/timing checks, conclusion and source limitations. Both empirical figures
were regenerated from accepted aggregate counts with descriptive 95% Wilson
intervals. Historical latest-pre-tip wording/composition analyses remain
explicitly historical; no pending human classifications were invented.

The 21-page revision compiled without undefined references/citations, missing
glyphs or overfull boxes. All pages were visually inspected, with full-page
checks of Table 4, Figure 3 and Table 5. The source and PDF hashes are recorded
in the [review-candidate manifest](../validation/october_scientific_v2_2026-11-15/review_release_candidate.json).
The new manuscript and source package remain private; the public repository
contains only code, aggregate results, scope decisions and artifact hashes.

## Remaining review gates

Scientific-output acceptance and historical-artifact provenance remain separate.
This is an authenticated retained-intermediate execution, not a newly repeated
complete-candidate PDF plus original-JSON reconstruction. Original acquisition
clocks, reviewed decisions and the known 2025 two-field metadata exception stay
inherited and declared. The separate 203-description adjudication, independent
human scientific review, publication-rights review and owner final approval are
not supplied by successful computation. They have no fabricated signatures.

The candidate is prepared for that review. No release tag, merge, issue closure
or submission was performed. The missing full-source run and blocked physical
sensitivity remain accurately disclosed rather than being called completed.
