# 2024–25 full original regular-season PDFs to October inputs

The complete historical regular-season candidate set contains **4,078 original PDFs**, October 22, 2024 through April 13, 2025. An authentic isolated invocation verified every PDF payload against the original manifest SHA-256, ran the pinned later parser (`197c29d46dfea221c381664b96a05453737df55d7b8dd5d5e6f44e49b69e0e06`), and regenerated **418,059 full records and all 4,078 parse-log records** matching the historical complete record multisets.

Fresh full candidate CSV SHA-256: `265c8ca38f218a275fa49b077602e109aaca16abcf1105db8f9bdfb18e087b89`; full log SHA-256: `ed06da9fa8170138438d401e077067c8eb07fa16ca1c82480b9e638645db5cf9`.

The existing SHA-pinned original canonical selector consumed those newly generated records and reproduced full/harmonized game/team tables and all 13 metrics per panel. The small `generate_2024_selector_inputs.py` adapter calls that existing selector; it does not reimplement selection. It serializes freshly generated source rows in the original `s1_parse_log_regular_season_real.csv` source-file sequence because October reads the corrected archive's `_real` row table. Only ordering metadata is inherited; no archived row values are substituted. Original publication clocks and other recorded historical metadata remain declared inputs.

| Generated October input | Rows | Complete CSV SHA-256 |
| --- | ---: | --- |
| Harmonized canonical game selector | 1,230 | `1849e96a96ce0ac0353ee6e695dde0c61fefdccf16c4c0eb08edd22ff51dbdf6` |
| Harmonized canonical team status | 2,460 | `80625b8351ede91229fca4cd7044c5da44438ec7c112820a8851c266535cdd66` |
| Fresh records in original `_real` source-file order | 418,059 | `4c7b9fb396163b6491f1d49ba67be46c70f9b167f9561425fe8ab12f3a0e4165` |

All three generated files matched the historical reference bytes; an isolated private handoff substituted all three at the actual October input paths after record and SHA-256 checks.

The existing targeted acceptance runner now supports `--season 2024-25`: it uses the original raw/corrected-pre-S4/S4/core/canonical ZIPs already in the private inventory, executes the parser and existing selector, substitutes fresh rows and selectors, and requires actual original-builder opens, stable input hashes, all eight exact decoded outputs and original frozen model gates. **The authentic full October downstream run with this new connection is pending** in the user's complete private environment. The three corrected final datasets have not been rerun with these later integrations. Canonical final integration and 2025 source-selection work remain open; PR #4 stays draft and Issue #5 stays open.
