# August 2026 latest-pre-tip source report join: root cause and verified safe matching rule

**November 8, 2026.** A source provenance audit only, not a reconstructed latest-pre-tip player-game panel or retested injury taxonomy.

The independent audit opened the original nba_player_game_at_risk_core_v1.zip, SHA-256 a0f82ebcf6117554a4ce1064ab79db9cf93acc5a53fa25000343810843e659f6, and examined the archived historical build_selected_report_and_identity_stage.py, SHA-256 738b78fa9fd9f3cdd9f4b4eb6756b424680959cacb85cfc354a6d6affa915fef.

That source contains a season-wide workaround that reassigns every 2021–22 selected report row with matchup CHI@TOR or MIA@TOR to just one of the two swapped February 2022 games. The opponent pair is not a unique physical-game identifier: each pairing recurred that season.

The original 73,547-row selected_report_rows_all.csv has **36 source report rows in the four relevant source matches**:

| Source match number | Actual original source report | Source rows | Historical August target | Correct physical-game association |
|---:|---|---:|---|---|
| 46 | October 25, 2021, 6 PM | **7** | February Bulls at Raptors | **October Bulls at Raptors** |
| 430 | February 1, 2022, 6 PM | 10 | February Heat at Raptors | **February 1 Heat at Raptors** |
| 784 | February 3, 2022, 6 PM | 9 | February Bulls at Raptors | **February 3 Bulls at Raptors** |
| 1172 | April 3, 2022, 6 PM | **10** | February Heat at Raptors | **April Heat at Raptors** |

**Exactly 17 rows** from unrelated October and April games were erroneously assigned to the February games by matchup alone. The 19 February source-report rows belong to the two real February fixtures. The safe fix must use **season plus source match number**, with exceptions for only source matches 430 and 784; it must not replace every CHI@TOR/MIA@TOR occurrence.

This **17-source-row** finding differs from the previously independently established **34 downstream player-game report-timestamp anomalies** in the 248,730-row August panel (16 Bulls–Raptors, 18 Heat–Raptors, 19 post-tip). The two counts measure different data structures and should not be equated.

## Reproduce

Original ZIP required outside GitHub's public source-controlled inputs. Run in a pandas-capable Python environment:

    python scripts/data_rebuild/audit_august_toronto_source_game_join.py \
      --core-zip /path/to/nba_player_game_at_risk_core_v1.zip \
      --output data_rebuild/output/august_toronto_source_audit.json

The script validates original builder SHA, source match numbers and exact four-group row counts, outputs a 36-row before/after physical-game mapping, and never writes into its source ZIP or the frozen August panel. Negative tests verify unrelated October/April reports remain associated with their actual games and that unexpected source changes fail.

Reproducibility evidence: validation/august_toronto_source_join_2026-11-08/source_match_reassignment_audit.json

## Not yet done

A proper corrected August source-to-final run must also correct physical fixture dates and game IDs, team-game report status, rest/travel/Elo covariates, player chronological histories and spell onsets, taxonomy classifications, and all August latest-pre-tip and label-mechanism scripts. Simply relabeling 17 selected rows without rebuilding downstream inputs is **not** sufficient. This audit does not establish which August paper coefficients change.

Historical original August and October frozen outputs and manuscript remain untouched. PR #4 should remain a draft.
