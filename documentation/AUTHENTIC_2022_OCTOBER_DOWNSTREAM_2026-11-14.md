# Supplied authentic 2022–23 October downstream acceptance — 2026-11-14

The user supplied successful targeted Linux amd64 execution output for code commit `a4a7ca3326b172aef4f325cae1d4b38200930870`. The transcript SHA-256 is `9e9750ebcb4673072ad58850a1e3b3bfa29a0c37c2c5c5e2fbd3ac5837f3b3d7`. Its JSON object was independently parsed and its internal acceptance assertions checked. The private output CSV bytes and separate model output files were not uploaded or independently rehashed here.

The report states `status: pass`, `season: 2022-23`, and `fresh_source_reused: false`. All 4,101 original regular-season candidate PDFs were parsed in this invocation. The 354,146-row full candidate source hash is `1809b0c4b2228c2c62ed46a934f5f98243d155ab21472e1977e513488fc5ee66`. See the [original source/selector checks](ORIGINAL_2022_CANDIDATE_SELECTOR_2026-11-14.md).

The original October subprocess audit trace records actual reads of these three generated files, with matching pre/post execution hashes:

| Actual consumed input | Rows | SHA-256 |
| --- | ---: | --- |
| Canonical harmonized game selector | 1,230 | `f7322d22edcdf96b74448d2849a2b29ccaa6453b9968ced65427e55461751af4` |
| S4 harmonized team-game report status | 2,460 | `4ffdbe4c4b7c0205405702e23c831d1cf6d87e3ec56c6a1b3b4ba56576238110` |
| Full regular-season parsed report rows | 354,146 | `c71832d9935a774625638d5c9987ca1bd005553bdecaf2ef60143cf61e1c734e` |

All **eight original frozen October intermediate outputs** matched the accepted prior run as complete decoded bytes. The regenerated frozen panel hash was `3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac`. The targeted command reports success only after panel invariants and original frozen Stage-6 model gates pass. [CI run 43620803495](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/43620803495) succeeded for the executed commit.

This supports the 2022–23 targeted original-PDF-to-selector-to-October downstream gate. The earlier 2020 and 2021 season checks remain separate targeted executions; this was not a cumulative fresh six-season run. Publication metadata, historical source-file completion order and other declared source inputs remain inherited. The report explicitly records `corrected_final_panel_rebuilt: false`. No new corrected three-final-dataset acceptance is claimed; the canonical final runner still needs these later season integrations. PR #4 stays draft and Issue #5 stays open.
