# Raw Data and Reproducibility Scope

This freeze intentionally bundles the final analysis-ready datasets and all major model-stage packages, but it does **not** mirror every raw source object.

## Raw inputs that should remain archived separately

### Official NBA Injury Reports
Season-specific raw PDF folders used during construction:

- `audit_2020_21/pdf/`
- `audit_2021_22/pdf/`
- `audit_2022_23/pdf/`
- `audit_2023_24/pdf/`
- `audit_2024_25/pdf/`
- `audit_2025_26/pdf/`
- `audit_2025_26_targeted/pdf/`

Historical PDFs were accessed as exact timestamped NBA-hosted objects. The NBA static-content base directory is not a browsable archive.

### Official NBA live boxscore JSON
Used for roster denominator, participation, minutes, non-playing reasons, game IDs, and realized fixture mapping.

### Schedule and recognition inputs
NBA/PR-NBA materials and the initial FixtureDownload season skeleton were used for schedule, advance-TV, NBA Cup, and recognition inputs.

## What this bundle can reproduce directly
Starting from `data_final/`, the package contains or indexes the exact executed model stages needed to reproduce the frozen analysis results without rebuilding every raw PDF and JSON input.

## What is needed for a from-scratch data rebuild
A full from-scratch reconstruction additionally requires the separately retained raw official PDFs/JSON, schedule inputs, and construction scripts/caches.

Therefore call this package an **analysis reproducibility archive** rather than a fully self-contained raw-data replication archive.
