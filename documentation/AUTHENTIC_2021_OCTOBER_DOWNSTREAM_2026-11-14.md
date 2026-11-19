# Supplied authentic 2021–22 October downstream acceptance — 2026-11-14

The user supplied the successful targeted Linux amd64 execution output for code commit `dbd9603eba7a2a945aa832aa34c68b4085cde683`. The attached transcript SHA-256 is `76bf43ddecb18cd68347feb2b8fdc886a9af8a6369620367749b54a521b68167`. Its JSON acceptance object was independently parsed and checked; the private CSV output bytes were not independently uploaded or rehashed in this executor.

The report states `status: pass`, season `2021-22`, and `fresh_source_reused: true`: the new full 5,567-PDF parse from the preceding failed attempt was explicitly reused after revalidation, without reparsing all PDFs. Its full 398,715-row source file hash remained `5d0451329deb92c3db8dc09ccbd7fa2facfb9ec8a405da084e9e646134b4c2a7`. The original parser and full candidate source stage are documented in [the source/selector record](ORIGINAL_2021_CANDIDATE_SELECTOR_2026-11-14.md).

The original October subprocess's audit trace records actual opens of all three required generated inputs. Pre/post execution SHA-256 values remained equal:

| Generated input | Rows | SHA-256 |
| --- | ---: | --- |
| 2021 harmonized game selections | 1,230 | `dd1e7b5f4ade4c4f6aa1a0802f40dad9c531ef2d3ecce932d5d807eeb6f72a74` |
| 2021 harmonized team statuses | 2,460 | `d8dc24a0effbbcc02592d7fe704c7adfc2b08d78090786fa3523d4f4cb9caf61` |
| 2021 freshly parsed harmonized report rows | 58,631 | `d88ca6be27612515b97f1417b590b30b0d769ea07cdb22fbf3cd49a1a275661f` |

All **eight October frozen intermediate outputs** match the accepted prior run as complete decoded bytes. The new frozen player-game panel hash is `3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac`. The command emits success only after the original frozen model gate and panel invariants pass; separate model-result files were not supplied in this transcript. [CI run 43619634368](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/43619634368) succeeded for the executed code commit.

This supports the **2021–22 targeted original-PDF-to-selector-to-October downstream gate**, including the historical submitted-placeholder precedence. Historical publication metadata and the original parse-log source-file completion sequence remain explicitly inherited. Other seasons were reused. This is not a cumulative new six-season full run: `corrected_final_panel_rebuilt: false`. The three accepted corrected final dataset hashes remain supported by the earlier authenticated final reproduction, not by this targeted test. PR #4 remains draft and Issue #5 remains open.

