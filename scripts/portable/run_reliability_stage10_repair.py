from pathlib import Path
import json

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups


REPO = Path(__file__).resolve().parents[2]
INPUT = (
    REPO
    / "data_intermediate/reliability_stage10/repair_risk_panel.csv.gz"
)
OUT = REPO / "results/portable_reliability_stage10"
OUT.mkdir(parents=True, exist_ok=True)


def boolish(s):
    if pd.api.types.is_bool_dtype(s):
        return s.fillna(False).astype(bool)
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce").fillna(0).ne(0)
    return (
        s.astype(str).str.strip().str.lower()
        .isin({"true", "1", "yes", "y", "t"})
    )


def group_codes(s):
    return pd.factorize(s, sort=False)[0]


def demean_once(a, codes):
    out = np.empty_like(a, dtype=float)
    n_groups = int(codes.max()) + 1
    counts = np.bincount(codes, minlength=n_groups).astype(float)

    for j in range(a.shape[1]):
        sums = np.bincount(
            codes,
            weights=a[:, j],
            minlength=n_groups,
        )
        means = sums / counts
        out[:, j] = a[:, j] - means[codes]

    return out


def absorb_two_fe(a, code1, code2, tol=1e-10, max_iter=1000):
    z = np.asarray(a, dtype=float).copy()

    for _ in range(max_iter):
        old = z.copy()
        z = demean_once(z, code1)
        z = demean_once(z, code2)

        if np.max(np.abs(z - old)) < tol:
            break
    else:
        raise RuntimeError("FE absorption did not converge.")

    return z


def make_design(df, tv_col):
    x = pd.DataFrame(index=df.index)

    star = df["star_stage10"].astype(float)
    post = df["postPPP_stage10"].astype(float)
    tv = df[tv_col].astype(float)

    x["tv"] = tv
    x["star"] = star
    x["star_post"] = star * post
    x["star_tv"] = star * tv
    x["post_tv"] = post * tv
    x["star_post_tv"] = star * post * tv

    age = df["spell_age_bin"].astype(str)

    for level in ["2", "3", "4-5", "6-10", "11+"]:
        x[f"age_{level}"] = age.eq(level).astype(float)

    x["home"] = (
        df["team_role"].astype(str).str.lower().eq("home")
    ).astype(float)

    x["rest_days_cap4"] = (
        pd.to_numeric(
            df["rest_days_between_games"],
            errors="coerce",
        ).clip(lower=0, upper=4)
    )

    x["three_in_four"] = boolish(
        df["three_games_in_four_days"]
    ).astype(float)

    x["four_in_six"] = boolish(
        df["four_games_in_six_days"]
    ).astype(float)

    x["travel_1000km"] = (
        pd.to_numeric(
            df["travel_km_since_previous_game"],
            errors="coerce",
        ) / 1000.0
    )

    x["elo_win_prob"] = pd.to_numeric(
        df["team_win_probability_elo"],
        errors="coerce",
    )

    x["cup_game"] = boolish(df["cup_game"]).astype(float)

    return x


def fit_model(df, outcome, tv_col, label):
    x = make_design(df, tv_col)
    y = pd.to_numeric(df[outcome], errors="coerce")

    needed = pd.concat([y.rename("y"), x], axis=1)
    ok = needed.notna().all(axis=1)

    d = df.loc[ok].copy()
    y = y.loc[ok].astype(float)
    x = x.loc[ok].astype(float)

    player_codes = group_codes(
        d["nba_player_id"].astype(str)
    )
    teamseason_codes = group_codes(
        d["team"].astype(str)
        + "|"
        + d["season"].astype(str)
    )

    joint = np.column_stack(
        [y.to_numpy(), x.to_numpy()]
    )

    residualized = absorb_two_fe(
        joint,
        player_codes,
        teamseason_codes,
    )

    yr = residualized[:, 0]
    xr = residualized[:, 1:]

    # Drop columns completely absorbed by fixed effects.
    keep = np.nanstd(xr, axis=0) > 1e-12
    names = list(x.columns[keep])
    xr = xr[:, keep]

    rank = np.linalg.matrix_rank(xr)

    if rank != xr.shape[1]:
        raise RuntimeError(
            f"{label}: design rank {rank}/{xr.shape[1]}"
        )

    if "star_post_tv" not in names:
        raise RuntimeError(
            f"{label}: focal coefficient absorbed/dropped."
        )

    model = sm.OLS(yr, xr).fit()

    # statsmodels/NumPy compatibility:
    # use integer codes rather than object/string cluster arrays.
    cluster_player_codes = group_codes(
        d["nba_player_id"].astype(str)
    )
    cluster_game_codes = group_codes(
        d["game_id"].astype(str)
    )

    cov_both, _, _ = cov_cluster_2groups(
        model,
        cluster_player_codes,
        cluster_game_codes,
        use_correction=True,
    )

    focal_idx = names.index("star_post_tv")

    beta = float(model.params[focal_idx])
    se = float(np.sqrt(cov_both[focal_idx, focal_idx]))

    z = beta / se
    p = float(2 * stats.norm.sf(abs(z)))
    lo = beta - 1.96 * se
    hi = beta + 1.96 * se

    result = {
        "model": label,
        "outcome": outcome,
        "tv_definition": tv_col,
        "N": int(len(d)),
        "players": int(d["nba_player_id"].nunique()),
        "games": int(d["game_id"].nunique()),
        "coefficient": beta,
        "se": se,
        "ci_low": float(lo),
        "ci_high": float(hi),
        "p_value": p,
        "coefficient_pp": beta * 100,
        "se_pp": se * 100,
        "ci_low_pp": lo * 100,
        "ci_high_pp": hi * 100,
        "design_rank": int(rank),
        "design_columns": int(xr.shape[1]),
    }

    return result


def raw_cells(df, outcome, tv_col):
    d = df.copy()

    d["star"] = d["star_stage10"].astype(int)
    d["post"] = d["postPPP_stage10"].astype(int)
    d["tv"] = d[tv_col].astype(int)

    tab = (
        d.groupby(["star", "post", "tv"])[outcome]
        .agg(["size", "sum", "mean"])
        .reset_index()
    )

    return tab


print("Loading repair-risk panel...", flush=True)
df = pd.read_csv(INPUT, low_memory=False)

primary = df.loc[
    boolish(df["repair_primary_eligible"])
].copy()

print("Primary repair-risk rows:", len(primary))

results = []

# Primary outcome.
results.append(
    fit_model(
        primary,
        "return_available_today",
        "tv_legacy",
        "Primary repair hazard — legacy TV",
    )
)

results.append(
    fit_model(
        primary,
        "return_available_today",
        "tv_harmonized",
        "Repair hazard — harmonized TV",
    )
)

# Participation sensitivity.
results.append(
    fit_model(
        primary,
        "return_played_today",
        "tv_legacy",
        "Played-return sensitivity — legacy TV",
    )
)

results.append(
    fit_model(
        primary,
        "return_played_today",
        "tv_harmonized",
        "Played-return sensitivity — harmonized TV",
    )
)

# Frozen onset-category secondary analyses.
for category in ["vague", "specific"]:
    sub = primary.loc[
        primary["prev_onset_category4"].eq(category)
    ].copy()

    for tv_col, tv_name in [
        ("tv_legacy", "legacy"),
        ("tv_harmonized", "harmonized"),
    ]:
        results.append(
            fit_model(
                sub,
                "return_available_today",
                tv_col,
                f"{category} repair hazard — {tv_name}",
            )
        )

res = pd.DataFrame(results)
res.to_csv(
    OUT / "repair_hazard_results.csv",
    index=False,
)

for tv_col in ["tv_legacy", "tv_harmonized"]:
    raw_cells(
        primary,
        "return_available_today",
        tv_col,
    ).to_csv(
        OUT / f"repair_raw_cells_{tv_col}.csv",
        index=False,
    )

summary = {
    "primary_risk_rows": int(len(primary)),
    "primary_returns_available": int(
        boolish(primary["return_available_today"]).sum()
    ),
    "results": results,
}

(OUT / "repair_hazard_results.json").write_text(
    json.dumps(summary, indent=2)
)

print("\nREPAIR HAZARD RESULTS")
print(
    res[
        [
            "model",
            "N",
            "coefficient_pp",
            "se_pp",
            "ci_low_pp",
            "ci_high_pp",
            "p_value",
            "design_rank",
            "design_columns",
        ]
    ].to_string(index=False)
)

print("\nWROTE:", OUT)
