# 2022–23 original regular-season candidate PDFs to October inputs

The original raw ZIP contains 5,541 saved PDFs including dates outside the regular season. The complete historical selector candidate set is the **4,101 available regular-season PDFs**, October 18, 2022 through April 9, 2023. The original manifest records each PDF's SHA-256 and publication clock. These historical observations remain versioned inputs; acquisition times are not invented.

The existing full-candidate parser now accepts `--season 2022-23` and uses the identical SHA-pinned original early parser from the original core archive. An authentic isolated invocation verified all candidate payload hashes and parsed all 4,101 PDFs. The generated **354,146 full candidate records and 4,101 parse-log records** matched all original fields and complete-record multisets. Full candidate CSV SHA-256: `1809b0c4b2228c2c62ed46a934f5f98243d155ab21472e1977e513488fc5ee66`; log SHA-256: `68eee365908e764be75e8112e296cfafe0f9d6bf4831ad0793ecfc62652be1a6`.

The original selector consumed the newly parsed full candidates, applied the existing submitted-placeholder precedence, and reproduced both full/harmonized game and team tables and all 13 season metrics. Original source-file completion order is inherited solely to serialize freshly generated parsed values. Deterministic game/tie and team-role ordering and the original 2022 S4 CRLF interface are preserved.

| Generated harmonized October input | Rows | Complete CSV SHA-256 |
| --- | ---: | --- |
| Canonical game selector | 1,230 | `f7322d22edcdf96b74448d2849a2b29ccaa6453b9968ced65427e55461751af4` |
| S4 team-game report status | 2,460 | `4ffdbe4c4b7c0205405702e23c831d1cf6d87e3ec56c6a1b3b4ba56576238110` |
| Full regular-season parsed rows | 354,146 | `c71832d9935a774625638d5c9987ca1bd005553bdecaf2ef60143cf61e1c734e` |

All three generated input files match the original reference bytes after the declared serialization steps. The private handoff replaces the actual `cadence_work/s4/2022-23/team_game_final_pre_tip_status_harmonized.csv` consumed by October, rather than an unused canonical team table.

Use the existing targeted command with `--season 2022-23`, the accepted prior private run, and a new output root. It requires the existing original raw/pre-S4/S4/core/canonical ZIPs, runs the parser and selector, substitutes the three inputs, and requires actual original-builder opens and unchanged input hashes before all eight decoded output and frozen model gates can pass. **Actual full October builder execution with these new 2022 inputs remains pending.** No new corrected final datasets were generated. The canonical final runner still inherits this season until that integration is accepted; PR #4 is draft and Issue #5 stays open.
