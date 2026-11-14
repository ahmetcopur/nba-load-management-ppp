# 2023–24 full original regular-season PDFs to October inputs

The complete historical regular-season candidate inventory contains **4,097 original PDFs**, October 24, 2023 through April 14, 2024. Each original payload was verified against its preserved manifest SHA-256 before parsing. Original publication clocks, acquisition observations and original source-file completion order remain declared inherited metadata.

An authentic isolated invocation of the extended existing candidate runner parsed every PDF using the immutable later parser, SHA-256 `197c29d46dfea221c381664b96a05453737df55d7b8dd5d5e6f44e49b69e0e06`. All **388,878 full records and 4,097 parse-log records** matched the archived complete record multisets. Full fresh candidate CSV SHA-256: `8d5be1c719b5d63357a9e095b69d03b29db97dd32bf344c73a76ad4468ec77e9`; log SHA-256: `140a6efe61f2a7c7346554eaba1129e41c56db4a1ca9dc6d0104fe29f8c40c0d`.

The original selector consumed these fresh rows and reproduced full/harmonized game and team tables (1,230 games and 2,460 teams per panel) and all 13 season metrics. The historical submitted-placeholder precedence and the existing `FD2023_5` clean-game fallback were preserved. CSV interface ordering and ISO ET timestamp serialization were retained, with LF line endings for this season's S4 table.

| Generated harmonized October input | Rows | Complete CSV SHA-256 |
| --- | ---: | --- |
| Canonical game selector | 1,230 | `b14508fd5f5ca446cbcd657435523a503afbdb6cf1354656a630455132776171` |
| Actual S4 team-status table | 2,460 | `ab5df0f94dfb7dfcdd1f5a4b584d7beb6841042f507321fd58825071fd8d2296` |
| Full regular-season parsed rows | 388,878 | `e8e5af4e55118e3ec9ac4fd1146f12f6cf8ec0fbf7f90d25ca5fa576ed9c2e37` |

All three generated input files matched archived bytes and the isolated private handoff passed. The actual parsed-row destination includes the historical `audit_2023_24_pre_s4_outputs/` subdirectory; the team status goes to the S4 path read by October.

The existing targeted runner now accepts `--season 2023-24`. It generates these values, substitutes all three actual inputs, and requires original-builder file opens, unchanged input hashes, eight exact decoded output comparisons and original frozen model gates. **The supplied authentic targeted October run passed**, including three required file opens and eight exact decoded outputs; see [the downstream execution record](AUTHENTIC_2023_OCTOBER_DOWNSTREAM_2026-11-14.md). Canonical final runner integration and a new corrected three-final-dataset run are also outstanding. No private source bytes or player-level records were committed; PR #4 remains draft and Issue #5 stays open.
