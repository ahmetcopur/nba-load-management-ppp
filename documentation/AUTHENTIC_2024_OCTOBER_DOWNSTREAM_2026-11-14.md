# Supplied authentic 2024–25 October downstream acceptance — 2026-11-14

The user supplied successful targeted Linux amd64 execution output for code commit `835a016094395c633d21024e9d22fc43396981bb`. The transcript SHA-256 is `37bb59c105f7510af87d92e63f0bd9a9bad132f81ab99671b21dd94c02c9a899`. Its JSON object was independently parsed and the internal acceptance assertions checked. Private output CSV bytes and separate model files were not uploaded or independently rehashed here.

The report states `status: pass`, `season: 2024-25`, and `fresh_source_reused: false`. All 4,078 original regular-season candidate PDFs were parsed in this invocation; the full 418,059-row source CSV hash is `265c8ca38f218a275fa49b077602e109aaca16abcf1105db8f9bdfb18e087b89`. The existing original canonical selector consumed these source-derived records; see [the parser/selector record](ORIGINAL_2024_CANDIDATE_SELECTOR_2026-11-14.md).

The original October subprocess trace records actual reads of all three required generated inputs, with unchanged pre/post execution hashes:

| Consumed input | Rows | SHA-256 |
| --- | ---: | --- |
| Harmonized game selector | 1,230 | `1849e96a96ce0ac0353ee6e695dde0c61fefdccf16c4c0eb08edd22ff51dbdf6` |
| Harmonized canonical team status | 2,460 | `80625b8351ede91229fca4cd7044c5da44438ec7c112820a8851c266535cdd66` |
| Parsed records in original `_real` file order | 418,059 | `4c7b9fb396163b6491f1d49ba67be46c70f9b167f9561425fe8ab12f3a0e4165` |

All **eight original frozen October intermediate outputs** matched the accepted prior run as complete decoded bytes. The frozen panel SHA-256 is `3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac`. The targeted runner reports success only after original frozen Stage-6 model gates and panel invariants succeed; detailed model files were not included in the transcript. [CI run 43623639914](https://github.com/ahmetcopur/nba-load-management-ppp/actions/runs/43623639914) succeeded for the executed code.

This supports the 2024–25 targeted original-PDF-to-selector-to-October gate. Original publication metadata and source-file serialization order remain inherited. Five seasons (2020–21 through 2024–25) now have **separate** targeted downstream proofs reusing the other seasons. They do not constitute a new cumulative six-season reconstruction. The report explicitly records `corrected_final_panel_rebuilt: false`; canonical final-runner integration, 2025 selection provenance and a combined corrected three-final-dataset execution remain outstanding. PR #4 stays draft and Issue #5 stays open.
