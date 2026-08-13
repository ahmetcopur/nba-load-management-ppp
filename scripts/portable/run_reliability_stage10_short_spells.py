from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups


REPO = Path(__file__).resolve().parents[2]

SPELL_PATH = (
    REPO
    / "data_intermediate/reliability_stage10/"
      "absence_spell_duration_panel.csv.gz"
)

PLAYER_PATH = (
    REPO
    / "data_final/player_game_panel_analysis_ready.csv.gz"
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
            a[:, j] - sums[g] / counts[g]
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


def fit(df, outcome, tv_col, label):
    y = pd.to_numeric(
        df[outcome],
        errors="coerce",
    )

    x = make_design(df, tv_col)

    complete = pd.concat(
        [y.rename("y"), x],
        axis=1,
    ).notna().all(axis=1)

    d = df.loc[complete].copy()
    y = y.loc[complete].astype(float)
    x = x.loc[complete].astype(float)

    g_player = codes(
        d["nba_player_id"].astype(str)
    )

    g_teamseason = codes(
        d["team"].astype(str)
        + "|"
        + d["season"].astype(str)
    )

    z = np.column_stack(
        [y.to_numpy(), x.to_numpy()]
    )

    zr = absorb_two_fe(
        z,
        g_player,
        g_teamseason,
    )

    yr = zr[:, 0]
    xr = zr[:, 1:]

    keep = np.nanstd(
        xr, axis=0
    ) > 1e-12

    names = list(x.columns[keep])
    xr = xr[:, keep]

    rank = np.linalg.matrix_rank(xr)

    if rank != xr.shape[1]:
        raise RuntimeError(
            f"{label}: rank {rank}/{xr.shape[1]}"
        )

    m = sm.OLS(
        yr,
        xr,
    ).fit()

    cp = codes(
        d["nba_player_id"].astype(str)
    )

    cg = codes(
        d["start_game_id"].astype(str)
    )

    cov, _, _ = cov_cluster_2groups(
        m,
        cp,
        cg,
        use_correction=True,
    )

    j = names.index("star_post_tv")

    b = float(m.params[j])
    se = float(np.sqrt(cov[j, j]))
    p = float(
        2 * stats.norm.sf(abs(b / se))
    )

    return {
        "model": label,
        "N": int(len(d)),
        "spells": int(d["spell_id"].nunique()),
        "coefficient_pp": 100 * b,
        "se_pp": 100 * se,
        "ci_low_pp": 100 * (b - 1.96 * se),
        "ci_high_pp": 100 * (b + 1.96 * se),
        "p_value": p,
        "rank": int(rank),
        "columns": int(xr.shape[1]),
    }


print("Loading spells...", flush=True)

spells = pd.read_csv(
    SPELL_PATH,
    low_memory=False,
)

panel = pd.read_csv(
    PLAYER_PATH,
    low_memory=False,
)


# ---------------------------------------------------------
# Keep observed, non-left-censored onsets
# ---------------------------------------------------------

spells = spells.loc[
    boolish(spells["duration_primary_universe"])
].copy()

spells["duration"] = pd.to_numeric(
    spells["duration_games_observed"],
    errors="coerce",
)

spells["completed"] = boolish(
    spells["completed_spell"]
)

spells["star_stage10"] = (
    spells["star_stage10"].astype(int)
)

spells["postPPP_stage10"] = (
    spells["postPPP_stage10"].astype(int)
)


# ---------------------------------------------------------
# Censoring-safe duration outcomes
# ---------------------------------------------------------

# Exactly one game:
# known if spell completed OR already observed for >=2 games.
spells["one_game_known"] = (
    spells["completed"]
    | spells["duration"].ge(2)
)

spells["one_game_safe"] = np.where(
    spells["one_game_known"],
    (
        spells["completed"]
        & spells["duration"].eq(1)
    ).astype(float),
    np.nan,
)


# <=2 games:
# known if spell completed OR already observed for >=3 games.
spells["le2_known"] = (
    spells["completed"]
    | spells["duration"].ge(3)
)

spells["le2_safe"] = np.where(
    spells["le2_known"],
    (
        spells["completed"]
        & spells["duration"].le(2)
    ).astype(float),
    np.nan,
)


# ---------------------------------------------------------
# Attach onset-game controls
# ---------------------------------------------------------

onset_cols = [
    "season",
    "team",
    "nba_player_id",
    "game_id",
    "team_game_number",
    "team_role",
    "rest_days_between_games",
    "three_games_in_four_days",
    "four_games_in_six_days",
    "travel_km_since_previous_game",
    "team_win_probability_elo",
    "cup_game",
]

onset = panel[
    onset_cols
].copy()

onset = onset.rename(
    columns={
        "game_id": "start_game_id",
        "team_game_number": "start_team_game_number",
    }
)

keys = [
    "season",
    "team",
    "nba_player_id",
    "start_game_id",
    "start_team_game_number",
]

if onset.duplicated(keys).any():
    raise RuntimeError(
        "Onset-control merge key is not unique."
    )

spells = spells.merge(
    onset,
    on=keys,
    how="left",
    validate="many_to_one",
)


# ---------------------------------------------------------
# Exposure definitions
# ---------------------------------------------------------

# One-game spell mechanism:
# Is the immediately following team game TV?
spells["next1_legacy"] = pd.to_numeric(
    spells["next1_tv_legacy"],
    errors="coerce",
)

spells["next1_harmonized"] = pd.to_numeric(
    spells["next1_tv_harmonized"],
    errors="coerce",
)


# <=2 mechanism:
# Require two subsequent scheduled games so the exposure
# window has identical meaning for every spell.
for tvdef in ["legacy", "harmonized"]:

    n1 = pd.to_numeric(
        spells[f"next1_tv_{tvdef}"],
        errors="coerce",
    )

    n2 = pd.to_numeric(
        spells[f"next2_tv_{tvdef}"],
        errors="coerce",
    )

    spells[f"next2_window_complete_{tvdef}"] = (
        n1.notna() & n2.notna()
    )

    spells[f"tv_next2_{tvdef}"] = np.where(
        spells[f"next2_window_complete_{tvdef}"],
        ((n1 == 1) | (n2 == 1)).astype(float),
        np.nan,
    )


# ---------------------------------------------------------
# Models
# ---------------------------------------------------------

results = []

results.append(
    fit(
        spells.loc[
            spells["one_game_known"]
            & spells["next1_legacy"].notna()
        ],
        "one_game_safe",
        "next1_legacy",
        "One-game spell — next game legacy TV",
    )
)

results.append(
    fit(
        spells.loc[
            spells["one_game_known"]
            & spells["next1_harmonized"].notna()
        ],
        "one_game_safe",
        "next1_harmonized",
        "One-game spell — next game harmonized TV",
    )
)

results.append(
    fit(
        spells.loc[
            spells["le2_known"]
            & spells["next2_window_complete_legacy"]
        ],
        "le2_safe",
        "tv_next2_legacy",
        "<=2-game spell — TV within next 2 legacy",
    )
)

results.append(
    fit(
        spells.loc[
            spells["le2_known"]
            & spells["next2_window_complete_harmonized"]
        ],
        "le2_safe",
        "tv_next2_harmonized",
        "<=2-game spell — TV within next 2 harmonized",
    )
)

res = pd.DataFrame(results)

res.to_csv(
    OUT / "short_spell_results.csv",
    index=False,
)

print("\nSHORT-SPELL RESULTS")
print(res.to_string(index=False))


# ---------------------------------------------------------
# Raw eight-cell tables
# ---------------------------------------------------------

raw_specs = [
    (
        "one_game_safe",
        "next1_legacy",
        spells["one_game_known"]
        & spells["next1_legacy"].notna(),
    ),
    (
        "one_game_safe",
        "next1_harmonized",
        spells["one_game_known"]
        & spells["next1_harmonized"].notna(),
    ),
    (
        "le2_safe",
        "tv_next2_legacy",
        spells["le2_known"]
        & spells["next2_window_complete_legacy"],
    ),
    (
        "le2_safe",
        "tv_next2_harmonized",
        spells["le2_known"]
        & spells["next2_window_complete_harmonized"],
    ),
]

for outcome, tv, mask in raw_specs:
    q = spells.loc[mask].copy()

    q["star"] = q["star_stage10"].astype(int)
    q["post"] = q["postPPP_stage10"].astype(int)

    tab = (
        q.groupby(
            ["star", "post", tv]
        )[outcome]
        .agg(["size", "sum", "mean"])
        .reset_index()
    )

    path = (
        OUT
        / f"raw_{outcome}_{tv}.csv"
    )

    tab.to_csv(
        path,
        index=False,
    )

print("\nWROTE:", OUT)
