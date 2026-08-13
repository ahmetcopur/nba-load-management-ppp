# Analysis Scripts

## executed/

Exact copies of the scripts used during the original analysis.

These scripts are preserved unchanged for provenance and may contain
absolute paths from the environment in which the analysis was originally run.

Do not modify these files.

## portable/

Portable versions intended to run from a cloned repository.

These scripts use repository-relative paths and rerun the frozen analytical
specifications using the datasets included in or referenced by this repository.

The portable versions must not alter the statistical specification of the
corresponding executed scripts. Exact floating-point equality is not guaranteed
for the penalized nonlinear/multinomial stage; see
`documentation/NONLINEAR_REPRODUCIBILITY_NOTE.md`.
