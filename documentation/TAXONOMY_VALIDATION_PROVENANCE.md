# Taxonomy Validation Provenance

The 300-spell validation should be described precisely.

## What happened
- The frozen v2 taxonomy was developed after an earlier assistant-supported review.
- A blinded handoff sheet was subsequently coded by **Claude**, not by an independent human coder.
- The Claude coding matched the locked coder-1 reference on **300/300** items (100% agreement; Cohen's kappa = 1.000).
- The study author subsequently reported manually reviewing the same labeling task and agreeing with all 300 classifications.

## Correct description
Use language such as:

> The frozen taxonomy was subjected to blinded cross-model recoding and a separate manual author review. Both reproduced all 300 sampled classifications. Because the human review was performed by a study author rather than an external independent coder, these exercises are treated as reproducibility checks rather than independent external inter-rater validation.

## Do not write
- "A second independent human coder achieved kappa = 1.00."
- "The taxonomy has been externally validated by human double-coding."

External human coding remains a publication-strengthening option, not a completed step in this freeze.

## Separate September 27 human-coding archive, examined November 15

The earlier narrative above describes the Claude/author 300-of-300 exercise. It must not be conflated with the subsequently supplied private `NBA_Coding_Agreement.zip`. The latter has two original supplied 300-label files; an independent rescore gives **260/300 agreement, kappa .834881321**. Its recorded owner attestation confirms separate human coding and blinding; coder identities/completion dates were not supplied. These labels are development-sample consistency evidence, not held-out medical validation. See the [scientific audit](SCIENTIFIC_INTEGRITY_AUDIT_2026-11-15.md) and [sanitized numerical evidence](../validation/scientific_integrity_audit_2026-11-15/independent_numeric_checks.json). This clarification preserves the historical account and does not establish external reviewer identity.
