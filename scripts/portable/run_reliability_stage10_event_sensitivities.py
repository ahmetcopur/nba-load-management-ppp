from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups


REPO = Path(__file__).resolve().parents[2]

EVENT_PATH = (
    REPO
    / "data_intermediate/reliability_stage10/"
      "tv_event_transition_panel.csv.gz"
)

REPAIR_PATH = (
    REPO
    / "data_intermediate/reliability_stage10/"
      "repair_risk_panel.csv.gz"
)

OUT = REPO / "results/portable_reliability_stage10"
OUT.mkdir(parents=True, exist_ok=True)

TAUS = [-3, -2, -1, 0, 1, 2, 3]


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
    return pd.factorize(
        s,
        sort=False,
    )[0]


def demean_once(a, g):
    out = np.empty_like(
        a,
        dtype=float,
    )

    ng = int(g.max()) + 1

    counts = np.bincount(
        g,
        minlength=ng,
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


def weighted_demean_once(a, g, w):
    out = np.empty_like(
        a,
        dtype=float,
    )

    ng = int(g.max()) + 1

    weight_sum = np.bincount(
        g,
        weights=w,
        minlength=ng,
    )

    if np.any(weight_sum <= 0):
        raise RuntimeError(
            "Non-positive fixed-effect group weight."
        )

    for j in range(a.shape[1]):
        weighted_sum = np.bincount(
            g,
            weights=w * a[:, j],
            minlength=ng,
        )

        means = (
            weighted_sum
            / weight_sum
        )

        out[:, j] = (
            a[:, j]
            - means[g]
        )

    return out


def absorb_two_fe(
    a,
    g1,
    g2,
    tol=1e-10,
    max_iter=1000,
):
    z = np.asarray(
        a,
        dtype=float,
    ).copy()

    for _ in range(max_iter):
        old = z.copy()

        z = demean_once(
            z,
            g1,
        )

        z = demean_once(
            z,
            g2,
        )

        if (
            np.max(
                np.abs(z - old)
            )
            < tol
        ):
            return z

    raise RuntimeError(
        "Unweighted FE absorption failed."
    )


def absorb_two_fe_weighted(
    a,
    g1,
    g2,
    w,
    tol=1e-10,
    max_iter=1000,
):
    z = np.asarray(
        a,
        dtype=float,
    ).copy()

    w = np.asarray(
        w,
        dtype=float,
    )

    for _ in range(max_iter):
        old = z.copy()

        z = weighted_demean_once(
            z,
            g1,
            w,
        )

        z = weighted_demean_once(
            z,
            g2,
            w,
        )

        if (
            np.max(
                np.abs(z - old)
            )
            < tol
        ):
            return z

    raise RuntimeError(
        "Weighted FE absorption failed."
    )


def make_design(df):
    x = pd.DataFrame(
        index=df.index
    )

    star = (
        df["star_stage10"]
        .astype(float)
    )

    post = (
        df["postPPP_stage10"]
        .astype(float)
    )

    # tau = 0 reference position.
    x["star"] = star
    x["star_post"] = (
        star * post
    )

    for k in TAUS:
        if k == 0:
            continue

        tau = (
            df["event_time"]
            .eq(k)
            .astype(float)
        )

        suffix = (
            f"m{abs(k)}"
            if k < 0
            else f"p{k}"
        )

        x[f"tau_{suffix}"] = tau

        x[f"star_tau_{suffix}"] = (
            star * tau
        )

        x[f"post_tau_{suffix}"] = (
            post * tau
        )

        x[f"star_post_tau_{suffix}"] = (
            star * post * tau
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
        .clip(
            lower=0,
            upper=4,
        )
    )

    x["three_in_four"] = (
        boolish(
            df[
                "three_games_in_four_days"
            ]
        )
        .astype(float)
    )

    x["four_in_six"] = (
        boolish(
            df[
                "four_games_in_six_days"
            ]
        )
        .astype(float)
    )

    x["travel_1000km"] = (
        pd.to_numeric(
            df[
                "travel_km_since_previous_game"
            ],
            errors="coerce",
        )
        / 1000.0
    )

    x["elo_win_prob"] = (
        pd.to_numeric(
            df[
                "team_win_probability_elo"
            ],
            errors="coerce",
        )
    )

    x["cup_game"] = (
        boolish(
            df["cup_game"]
        )
        .astype(float)
    )

    age = (
        df["spell_age_bin"]
        .astype(str)
    )

    for level in [
        "2",
        "3",
        "4-5",
        "6-10",
        "11+",
    ]:
        x[f"age_{level}"] = (
            age.eq(level)
            .astype(float)
        )

    return x


def fit_event_model(
    df,
    model_label,
    weight_col=None,
):
    y = (
        boolish(
            df[
                "return_available_today"
            ]
        )
        .astype(float)
    )

    x = make_design(df)

    complete = pd.concat(
        [
            y.rename("y"),
            x,
        ],
        axis=1,
    ).notna().all(axis=1)

    if weight_col is not None:
        weights = pd.to_numeric(
            df[weight_col],
            errors="coerce",
        )

        complete &= (
            weights.notna()
            & weights.gt(0)
        )

    d = df.loc[
        complete
    ].copy()

    y = y.loc[
        complete
    ].astype(float)

    x = x.loc[
        complete
    ].astype(float)

    if weight_col is None:
        w = np.ones(
            len(d),
            dtype=float,
        )
    else:
        w = (
            pd.to_numeric(
                d[weight_col],
                errors="raise",
            )
            .to_numpy(
                dtype=float
            )
        )

    gp = codes(
        d[
            "nba_player_id"
        ].astype(str)
    )

    gts = codes(
        d["team"].astype(str)
        + "|"
        + d["season"].astype(str)
    )

    z = np.column_stack(
        [
            y.to_numpy(),
            x.to_numpy(),
        ]
    )

    if weight_col is None:
        zr = absorb_two_fe(
            z,
            gp,
            gts,
        )
    else:
        zr = absorb_two_fe_weighted(
            z,
            gp,
            gts,
            w,
        )

    yr = zr[:, 0]
    xr = zr[:, 1:]

    keep = (
        np.nanstd(
            xr,
            axis=0,
        )
        > 1e-12
    )

    names = list(
        x.columns[keep]
    )

    xr = xr[:, keep]

    rank = np.linalg.matrix_rank(
        xr
    )

    if rank != xr.shape[1]:
        raise RuntimeError(
            f"{model_label}: "
            f"rank deficient "
            f"{rank}/{xr.shape[1]}"
        )

    # For the weighted stacked model,
    # sqrt(w) transforms the residualized
    # WLS problem into OLS.
    sqrt_w = np.sqrt(w)

    yr_fit = (
        yr * sqrt_w
    )

    xr_fit = (
        xr * sqrt_w[:, None]
    )

    model = sm.OLS(
        yr_fit,
        xr_fit,
    ).fit()

    cluster_player = codes(
        d[
            "nba_player_id"
        ].astype(str)
    )

    cluster_game = codes(
        d[
            "game_id"
        ].astype(str)
    )

    cov, _, _ = cov_cluster_2groups(
        model,
        cluster_player,
        cluster_game,
        use_correction=True,
    )

    if "star_post" not in names:
        raise RuntimeError(
            f"{model_label}: "
            "star_post absent."
        )

    j0 = names.index(
        "star_post"
    )

    rows = []

    for k in TAUS:
        if k == 0:
            b = float(
                model.params[j0]
            )

            var = float(
                cov[j0, j0]
            )

            delta = np.nan
            delta_se = np.nan
            delta_p = np.nan

        else:
            suffix = (
                f"m{abs(k)}"
                if k < 0
                else f"p{k}"
            )

            interaction = (
                f"star_post_tau_{suffix}"
            )

            if interaction not in names:
                raise RuntimeError(
                    f"{model_label}: "
                    f"missing {interaction}"
                )

            j = names.index(
                interaction
            )

            delta = float(
                model.params[j]
            )

            delta_var = float(
                cov[j, j]
            )

            delta_se = float(
                np.sqrt(
                    delta_var
                )
            )

            delta_p = float(
                2
                * stats.norm.sf(
                    abs(
                        delta
                        / delta_se
                    )
                )
            )

            b = float(
                model.params[j0]
                + model.params[j]
            )

            var = float(
                cov[j0, j0]
                + cov[j, j]
                + 2
                * cov[j0, j]
            )

        se = float(
            np.sqrt(var)
        )

        p = float(
            2
            * stats.norm.sf(
                abs(b / se)
            )
        )

        rows.append(
            {
                "model": model_label,
                "event_time": k,
                "stacked_N": int(
                    len(d)
                ),
                "unique_player_team_games": int(
                    d[
                        "player_team_game_id"
                    ].nunique()
                ),
                "sum_weights": float(
                    w.sum()
                ),
                "coefficient_pp": (
                    100 * b
                ),
                "se_pp": (
                    100 * se
                ),
                "ci_low_pp": (
                    100
                    * (
                        b
                        - 1.96 * se
                    )
                ),
                "ci_high_pp": (
                    100
                    * (
                        b
                        + 1.96 * se
                    )
                ),
                "p_value": p,
                "delta_vs_tau0_pp": (
                    100 * delta
                    if np.isfinite(
                        delta
                    )
                    else np.nan
                ),
                "delta_vs_tau0_se_pp": (
                    100 * delta_se
                    if np.isfinite(
                        delta_se
                    )
                    else np.nan
                ),
                "delta_vs_tau0_p": (
                    delta_p
                ),
                "rank": int(
                    rank
                ),
                "columns": int(
                    xr.shape[1]
                ),
            }
        )

    result = pd.DataFrame(
        rows
    )

    result[
        "delta_vs_tau0_q_bh"
    ] = np.nan

    idx = result.index[
        result["event_time"].ne(0)
    ]

    result.loc[
        idx,
        "delta_vs_tau0_q_bh",
    ] = multipletests(
        result.loc[
            idx,
            "delta_vs_tau0_p",
        ].to_numpy(),
        method="fdr_bh",
    )[1]

    interaction_names = []

    for k in TAUS:
        if k == 0:
            continue

        suffix = (
            f"m{abs(k)}"
            if k < 0
            else f"p{k}"
        )

        interaction_names.append(
            f"star_post_tau_{suffix}"
        )

    interaction_idx = [
        names.index(n)
        for n in interaction_names
    ]

    bvec = np.asarray(
        model.params
    )[interaction_idx]

    v = cov[
        np.ix_(
            interaction_idx,
            interaction_idx,
        )
    ]

    joint_stat = float(
        bvec.T
        @ np.linalg.pinv(v)
        @ bvec
    )

    joint_df = int(
        np.linalg.matrix_rank(v)
    )

    joint_p = float(
        stats.chi2.sf(
            joint_stat,
            joint_df,
        )
    )

    joint = {
        "model": model_label,
        "stacked_N": int(
            len(d)
        ),
        "unique_player_team_games": int(
            d[
                "player_team_game_id"
            ].nunique()
        ),
        "sum_weights": float(
            w.sum()
        ),
        "joint_stat": (
            joint_stat
        ),
        "joint_df": (
            joint_df
        ),
        "joint_p": (
            joint_p
        ),
    }

    return result, joint


def isolated_event_rows(
    events,
    tv_definition,
):
    e = events.loc[
        events[
            "tv_definition"
        ].eq(tv_definition)
        & boolish(
            events[
                "isolated_anchor"
            ]
        )
    ].copy()

    e = e.drop_duplicates(
        [
            "player_team_game_id",
            "anchor_team_game_number",
        ]
    )

    duplicate_rows = int(
        e[
            "player_team_game_id"
        ].duplicated().sum()
    )

    if duplicate_rows != 0:
        raise RuntimeError(
            f"{tv_definition}: "
            "isolated windows unexpectedly "
            f"overlap for {duplicate_rows} rows."
        )

    return e


def weighted_event_rows(
    events,
    tv_definition,
):
    e = events.loc[
        events[
            "tv_definition"
        ].eq(tv_definition)
    ].copy()

    e = e.drop_duplicates(
        [
            "player_team_game_id",
            "anchor_team_game_number",
        ]
    )

    e["stack_weight"] = (
        pd.to_numeric(
            e[
                "stack_weight"
            ],
            errors="raise",
        )
    )

    sums = (
        e.groupby(
            "player_team_game_id"
        )["stack_weight"]
        .sum()
    )

    max_weight_error = float(
        np.max(
            np.abs(
                sums.to_numpy()
                - 1.0
            )
        )
    )

    if max_weight_error > 1e-10:
        raise RuntimeError(
            f"{tv_definition}: "
            "stack weights do not sum to 1. "
            f"max error={max_weight_error}"
        )

    return e, max_weight_error


print(
    "Loading event and repair panels...",
    flush=True,
)

events = pd.read_csv(
    EVENT_PATH,
    low_memory=False,
)

repair = pd.read_csv(
    REPAIR_PATH,
    low_memory=False,
)

repair = repair.loc[
    boolish(
        repair[
            "repair_primary_eligible"
        ]
    )
].copy()

if repair[
    "player_team_game_id"
].duplicated().any():
    raise RuntimeError(
        "Repair panel is not unique "
        "by player_team_game_id."
    )


all_results = []
all_joint = []
qa_rows = []


for tv_definition in [
    "legacy_primary",
    "harmonized_linear",
]:

    # =====================================================
    # 1. ISOLATED ANCHORS
    # =====================================================

    iso = isolated_event_rows(
        events,
        tv_definition,
    )

    iso_anchor_count = int(
        iso[
            ["season", "team", "anchor_team_game_number"]
        ].drop_duplicates().shape[0]
    )

    iso_merged = iso.merge(
        repair,
        on="player_team_game_id",
        how="inner",
        validate="one_to_one",
        suffixes=("_event", ""),
    )

    qa_rows.append(
        {
            "tv_definition": (
                tv_definition
            ),
            "design": (
                "isolated_anchor"
            ),
            "anchors": (
                iso_anchor_count
            ),
            "event_rows_before_repair_filter": int(
                len(iso)
            ),
            "repair_risk_rows": int(
                len(iso_merged)
            ),
            "unique_repair_player_team_games": int(
                iso_merged[
                    "player_team_game_id"
                ].nunique()
            ),
            "sum_weights": float(
                len(iso_merged)
            ),
            "max_weight_sum_error": (
                0.0
            ),
        }
    )

    result, joint = fit_event_model(
        iso_merged,
        (
            "Repair isolated anchors — "
            + tv_definition
        ),
        weight_col=None,
    )

    result[
        "tv_definition"
    ] = tv_definition

    result[
        "design"
    ] = "isolated_anchor"

    joint[
        "tv_definition"
    ] = tv_definition

    joint[
        "design"
    ] = "isolated_anchor"

    all_results.append(
        result
    )

    all_joint.append(
        joint
    )


    # =====================================================
    # 2. INVERSE-OVERLAP WEIGHTED STACK
    # =====================================================

    weighted, weight_error = (
        weighted_event_rows(
            events,
            tv_definition,
        )
    )

    weighted_anchor_count = int(
        weighted[
            ["season", "team", "anchor_team_game_number"]
        ].drop_duplicates().shape[0]
    )

    weighted_merged = (
        weighted.merge(
            repair,
            on="player_team_game_id",
            how="inner",
            validate="many_to_one",
            suffixes=("_event", ""),
        )
    )

    # Every underlying repair observation should still
    # have total stacked weight one after the repair-risk
    # restriction because eligibility is invariant across
    # its stacked representations.
    repair_weight_sums = (
        weighted_merged
        .groupby(
            "player_team_game_id"
        )["stack_weight"]
        .sum()
    )

    repair_weight_error = float(
        np.max(
            np.abs(
                repair_weight_sums.to_numpy()
                - 1.0
            )
        )
    )

    if repair_weight_error > 1e-10:
        raise RuntimeError(
            f"{tv_definition}: "
            "repair stacked weights fail "
            "sum-to-one QA. "
            f"max error={repair_weight_error}"
        )

    qa_rows.append(
        {
            "tv_definition": (
                tv_definition
            ),
            "design": (
                "inverse_overlap_weighted"
            ),
            "anchors": (
                weighted_anchor_count
            ),
            "event_rows_before_repair_filter": int(
                len(weighted)
            ),
            "repair_risk_rows": int(
                len(weighted_merged)
            ),
            "unique_repair_player_team_games": int(
                weighted_merged[
                    "player_team_game_id"
                ].nunique()
            ),
            "sum_weights": float(
                weighted_merged[
                    "stack_weight"
                ].sum()
            ),
            "max_weight_sum_error": (
                repair_weight_error
            ),
        }
    )

    result, joint = fit_event_model(
        weighted_merged,
        (
            "Repair weighted stack — "
            + tv_definition
        ),
        weight_col="stack_weight",
    )

    result[
        "tv_definition"
    ] = tv_definition

    result[
        "design"
    ] = (
        "inverse_overlap_weighted"
    )

    joint[
        "tv_definition"
    ] = tv_definition

    joint[
        "design"
    ] = (
        "inverse_overlap_weighted"
    )

    all_results.append(
        result
    )

    all_joint.append(
        joint
    )


results = pd.concat(
    all_results,
    ignore_index=True,
)

joint = pd.DataFrame(
    all_joint
)

qa = pd.DataFrame(
    qa_rows
)


results.to_csv(
    OUT
    / "repair_event_time_sensitivity_results.csv",
    index=False,
)

joint.to_csv(
    OUT
    / "repair_event_time_sensitivity_joint_tests.csv",
    index=False,
)

qa.to_csv(
    OUT
    / "repair_event_time_sensitivity_qa.csv",
    index=False,
)


print("\nSENSITIVITY QA")

print(
    qa.to_string(
        index=False
    )
)


print("\nREPAIR EVENT-TIME SENSITIVITIES")

print(
    results[
        [
            "design",
            "tv_definition",
            "event_time",
            "stacked_N",
            "unique_player_team_games",
            "sum_weights",
            "coefficient_pp",
            "se_pp",
            "ci_low_pp",
            "ci_high_pp",
            "p_value",
            "delta_vs_tau0_pp",
            "delta_vs_tau0_se_pp",
            "delta_vs_tau0_p",
            "delta_vs_tau0_q_bh",
        ]
    ].to_string(
        index=False
    )
)


print("\nJOINT SENSITIVITY TESTS")

print(
    joint[
        [
            "design",
            "tv_definition",
            "stacked_N",
            "unique_player_team_games",
            "sum_weights",
            "joint_stat",
            "joint_df",
            "joint_p",
        ]
    ].to_string(
        index=False
    )
)


print("\n+3 VERSUS TV-GAME SUMMARY")

plus3 = results.loc[
    results[
        "event_time"
    ].eq(3)
].copy()

print(
    plus3[
        [
            "design",
            "tv_definition",
            "coefficient_pp",
            "p_value",
            "delta_vs_tau0_pp",
            "delta_vs_tau0_se_pp",
            "delta_vs_tau0_p",
            "delta_vs_tau0_q_bh",
        ]
    ].to_string(
        index=False
    )
)


print(
    "\nWROTE:",
    OUT,
)
