# Data-publication and history review — November 15

**Public identification alone does not establish confidentiality, and public source access does not establish unrestricted redistribution rights.** These records are research-derived NBA observations, not demonstrated access to a private clinical database. This review makes no determination that their presence is unlawful. The owner must establish the relevant publication basis, source attribution, applicable historical terms and research commitments before a release.

The [current NBA terms](https://www.nba.com/termsofuse) impose content-use conditions; historical applicability and permissions remain unverified. No blanket academic redistribution license or study-specific consent/permission document was located in the reviewed repository. That absence is not proof that permission does not exist. Do not represent this computational review as legal clearance.

## Four diagnostic files

All four use player/team/game keys, player names and frozen/corrected values. The designation comparison contains categorical participation statuses, not unrestricted clinical records or a newly collected medical diagnosis.

| File under `validation/fixture_date_chronology_2026-11-08/` | Rows | Recommendation |
|---|---:|---|
| `changed_absence_now_harm.csv` | 0 | Retain the header-only evidence: no individual records are exposed. |
| `changed_absence_onset_harm.csv` | 2 | Aggregate transition counts plus unchanged-outcome totals can demonstrate the correction publicly. Keep named keys privately unless the owner documents both redistribution basis and a specific verification need. |
| `changed_at_risk_for_new_onset_harm.csv` | 10 | Same proportional recommendation. Identifiers permit exact linking but are not necessary to report the size/direction of the risk-set correction. |
| `changed_designation_status.csv` | 20 | Prefer aggregate old/new status transitions publicly. Named excerpts could be justified only with documented attribution/permissions and a deliberate research-purpose decision; do not automatically call them confidential. |

These are publication recommendations, not an instruction to delete existing evidence. No file was redacted or removed.

## Broader exposure already in the repository

The four diagnostics are not the main scale of publication. The tracked inventory also contains:

- `data_final/player_game_panel_analysis_ready.csv.gz`: **248,730** player-game rows, names/IDs and public designation/reason text.
- `data_final/player_game_panel_model_at_risk_analysis_ready.csv.gz`: **180,829** rows with identifiers and taxonomy fields.
- `data_final/absence_spells_taxonomy_frozen.csv.gz`: **13,723** named spells and public designation text.
- `data_intermediate/player_team_game_harmonized_cadence.csv.gz`: **248,778** named player-team-games and designation fields.
- `validation/taxonomy_validation_sample_300_original.csv`: **300** identified sampled spells and descriptions.
- Both `packages/07_taxonomy_validation_scored.zip` and `validation/taxonomy_scoring_package_mechanical_agreement.zip` contain a member named **`coder1_coder2_scored_PRIVATE.csv`**, with coding/spell IDs and labels. Its filename indicates a publication-intent question; it does not by itself prove legal confidentiality. Spell IDs embed linkable identifiers.

[Publication inventory](../validation/scientific_integrity_audit_2026-11-15/publication_inventory.json) records headers/counts and whether each file/archive existed in PR #4's base. No player rows or diagnoses are reproduced in this new report. Identifier-free wording examples may still be source excerpts; the header-based scan is not exhaustive legal or privacy certification.

## Minimum owner decision

1. Document which public/derived records may be distributed, under which attribution/permission basis, and which research inputs remain restricted. Assess the bulk panels and PRIVATE-named archive members as well as the four diagnostics.
2. Where individual keys add little review value, approve an aggregate public summary and private keyed verification evidence. Do not silently change frozen archives merely to make publication easier.
3. If prospective removal/redaction is required, explicitly approve the change and preserve a private historical copy. A normal deletion does **not** remove earlier Git objects, existing clones or prior downloads. History rewriting requires separate explicit approval and cannot guarantee recovery of previously distributed copies.

The audit added only synthetic tests, code and aggregate documentation. No new raw source archive or individual player record was committed. No history rewrite, deletion or data publication was performed.
