from pathlib import Path

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
        return pd.to_numeric(
            s, errors="coerce"
        ).fillna(0).ne(0)

    return (
        s.astype(str)
        .str.strip()
        .str.lower()
        .isin({"true", "1", "yes", "y", "t"})
    )


def codes(s):
    return pd.factorize(s, sort=False)[0]


def demean_once(a, g):
    out = np.empty_like(a, dtype=float)

    ng = int(g.max()) + 1
    counts = np.bincount(
        g, minlength=ng
    ).astype(float)

    for j in range(a.shape[1]):
        sums = np.bincount(
            g,
            weights=a[:, j],
            minlength=ng,
        )

        out[:, j] = (
            a[:, j]
            - sums[g] / counts[g]
        )

    return out


def absorb_two_fe(a, g1, g2, tol=1e-10, max_iter=1000):
    z = np.asarray(a, dtype=float).copy()

    for _ in range(max_iter):
        old = z.copy()

        z = demean_once(z, g1)
        z = demean_once(z, g2)

        if np.max(np.abs(z - old)) < tol:
            return z

    raise RuntimeError("FE absorption did not converge.")


def base_design(df, tv_col):
    x = pd.DataFrame(index=df.index)

    star = df["star_stage10"].astype(float)
    post = df["postPPP_stage10"].astype(float)
    tv = df[tv_col].astype(float)

    # Same focal design as standalone repair model.
    x["tv"] = tv
    x["star"] = star
    x["star_post"] = star * post
    x["star_tv"] = star * tv
    x["post_tv"] = post * tv
    x["star_post_tv"] = star * post * tv

    age = df["spell_age_bin"].astype(str)

    for level in ["2", "3", "4-5", "6-10", "11+"]:
        x[f"age_{level}"] = (
            age.eq(level).astype(float)
        )

    x["home"] = (
        df["team_role"]
        .astype(str)
        .str.lower()
        .eq("home")
        .astype(float)
    )

    x["rest_days_cap4"] = (
        pd.to_numeric(
            df["rest_days_between_games"],
            errors="coerce",
        )
        .clip(lower=0, upper=4)
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
        )
        / 1000.0
    )

    x["elo_win_prob"] = pd.to_numeric(
        df["team_win_probability_elo"],
        errors="coerce",
    )

    x["cup_game"] = boolish(
        df["cup_game"]
    ).astype(float)

    return x


def fit_direct_contrast(df, tv_col):
    y = boolish(
        df["return_available_today"]
    ).astype(float)

    base = base_design(df, tv_col)

    complete = pd.concat(
        [y.rename("y"), base],
        axis=1,
    ).notna().all(axis=1)

    d = df.loc[complete].copy()
    y = y.loc[complete].astype(float)
    base = base.loc[complete].astype(float)

    vague = (
        d["prev_onset_category4"]
        .eq("vague")
        .astype(float)
    )

    specific = (
        d["prev_onset_category4"]
        .eq("specific")
        .astype(float)
    )

    # Fully category-specific slope blocks.
    x = pd.DataFrame(index=d.index)

    for col in base.columns:
        x[f"vague__{col}"] = (
            vague * base[col]
        )

        x[f"specific__{col}"] = (
            specific * base[col]
        )

    # Category-specific fixed effects make this equivalent to
    # estimating the two subgroup regressions separately.
    player_category = (
        d["nba_player_id"].astype(str)
        + "|"
        + d["prev_onset_category4"].astype(str)
    )

    teamseason_category = (
        d["team"].astype(str)
        + "|"
        + d["season"].astype(str)
        + "|"
        + d["prev_onset_category4"].astype(str)
    )

    g_player_cat = codes(player_category)
    g_teamseason_cat = codes(teamseason_category)

    z = np.column_stack(
        [y.to_numpy(), x.to_numpy()]
    )

    zr = absorb_two_fe(
        z,
        g_player_cat,
        g_teamseason_cat,
    )

    yr = zr[:, 0]
    xr = zr[:, 1:]

    keep = np.nanstd(
        xr, axis=0
    ) > 1e-12

    names = list(
        x.columns[keep]
    )

    xr = xr[:, keep]

    rank = np.linalg.matrix_rank(xr)

    if rank != xr.shape[1]:
        raise RuntimeError(
            f"Rank deficient: {rank}/{xr.shape[1]}"
        )

    model = sm.OLS(
        yr,
        xr,
    ).fit()

    cluster_player = codes(
        d["nba_player_id"].astype(str)
    )

    cluster_game = codes(
        d["game_id"].astype(str)
    )

    cov, _, _ = cov_cluster_2groups(
        model,
        cluster_player,
        cluster_game,
        use_correction=True,
    )

    vague_name = "vague__star_post_tv"
    specific_name = "specific__star_post_tv"

    jv = names.index(vague_name)
    js = names.index(specific_name)

    bv = float(model.params[jv])
    bs = float(model.params[js])

    sev = float(
        np.sqrt(cov[jv, jv])
    )

    ses = float(
        np.sqrt(cov[js, js])
    )

    pv = float(
        2 * stats.norm.sf(
            abs(bv / sev)
        )
    )

    ps = float(
        2 * stats.norm.sf(
            abs(bs / ses)
        )
    )

    # Direct H0:
    # DDD_specific - DDD_vague = 0
    contrast = bs - bv

    contrast_var = (
        cov[js, js]
        + cov[jv, jv]
        - 2 * cov[js, jv]
    )

    contrast_se = float(
        np.sqrt(contrast_var)
    )

    contrast_p = float(
        2 * stats.norm.sf(
            abs(
                contrast / contrast_se
            )
        )
    )

    return {
        "tv_definition": tv_col,
        "N": int(len(d)),
        "rank": int(rank),
        "columns": int(xr.shape[1]),

        "vague_ddd_pp": 100 * bv,
        "vague_se_pp": 100 * sev,
        "vague_p": pv,

        "specific_ddd_pp": 100 * bs,
        "specific_se_pp": 100 * ses,
        "specific_p": ps,

        "specific_minus_vague_pp": (
            100 * contrast
        ),
        "contrast_se_pp": (
            100 * contrast_se
        ),
        "contrast_p": contrast_p,
    }


df = pd.read_csv(
    INPUT,
    low_memory=False,
)

d = df.loc[
    boolish(
        df["repair_primary_eligible"]
    )
    & df["prev_onset_category4"].isin(
        ["vague", "specific"]
    )
].copy()

print(
    "Vague + specific repair-risk rows:",
    len(d),
)

results = [
    fit_direct_contrast(
        d,
        "tv_legacy",
    ),
    fit_direct_contrast(
        d,
        "tv_harmonized",
    ),
]

res = pd.DataFrame(results)

res.to_csv(
    OUT
    / "repair_category_direct_contrast.csv",
    index=False,
)

print("\nCORRECTED DIRECT CATEGORY CONTRAST")
print(
    res.to_string(index=False)
)
