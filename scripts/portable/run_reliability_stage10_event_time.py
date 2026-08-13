from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from statsmodels.stats.multitest import multipletests


REPO = Path(__file__).resolve().parents[2]

EVENT_PATH = (
    REPO
    / "data_intermediate/reliability_stage10/"
      "tv_event_transition_panel.csv.gz"
)

PANEL_PATH = (
    REPO
    / "data_final/player_game_panel_analysis_ready.csv.gz"
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

    raise RuntimeError("FE absorption failed.")


def nearest_assignments(events, tv_definition):
    e = events.loc[
        events["tv_definition"].eq(tv_definition)
    ].copy()

    e["abs_tau"] = e["event_time"].abs()

    # One physical player-team-game can appear around several TV anchors.
    # First remove accidental duplicate representations of the same anchor.
    e = e.drop_duplicates(
        [
            "player_team_game_id",
            "anchor_team_game_number",
        ]
    )

    min_dist = (
        e.groupby("player_team_game_id")["abs_tau"]
        .transform("min")
    )

    nearest = e.loc[
        e["abs_tau"].eq(min_dist)
    ].copy()

    # Exact halfway points between two TV games have two equally near anchors.
    tie_count = (
        nearest.groupby("player_team_game_id")[
            "anchor_team_game_number"
        ]
        .transform("nunique")
    )

    tied_ids = nearest.loc[
        tie_count.gt(1),
        "player_team_game_id",
    ].unique()

    nearest = nearest.loc[
        ~nearest["player_team_game_id"].isin(tied_ids)
    ].copy()

    if nearest["player_team_game_id"].duplicated().any():
        raise RuntimeError(
            f"{tv_definition}: nearest assignment still duplicated."
        )

    keep = [
        "player_team_game_id",
        "event_time",
        "anchor_team_game_number",
        "anchor_game_id",
        "anchor_game_date_et",
    ]

    nearest = nearest[keep].copy()
    nearest["tv_definition"] = tv_definition

    qa = {
        "tv_definition": tv_definition,
        "assigned_player_team_games": int(len(nearest)),
        "ties_excluded": int(len(tied_ids)),
        "event_time_counts": {
            str(int(k)): int(v)
            for k, v in
            nearest["event_time"]
            .value_counts()
            .sort_index()
            .items()
        },
    }

    return nearest, qa


def schedule_controls(df):
    x = pd.DataFrame(index=df.index)

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


def make_design(df, include_spell_age=False):
    x = pd.DataFrame(index=df.index)

    star = df["star_stage10"].astype(float)
    post = df["postPPP_stage10"].astype(float)

    # tau=0 is the reference event-time position.
    x["star"] = star
    x["star_post"] = star * post

    for k in TAUS:
        if k == 0:
            continue

        tau = df["event_time"].eq(k).astype(float)

        label = (
            f"m{abs(k)}"
            if k < 0
            else f"p{k}"
        )

        x[f"tau_{label}"] = tau
        x[f"star_tau_{label}"] = star * tau
        x[f"post_tau_{label}"] = post * tau
        x[f"star_post_tau_{label}"] = (
            star * post * tau
        )

    controls = schedule_controls(df)

    for c in controls:
        x[c] = controls[c]

    if include_spell_age:
        age = df["spell_age_bin"].astype(str)

        for level in ["2", "3", "4-5", "6-10", "11+"]:
            x[f"age_{level}"] = (
                age.eq(level).astype(float)
            )

    return x


def fit_event_model(
    df,
    outcome,
    label,
    include_spell_age=False,
):
    y = pd.to_numeric(
        df[outcome],
        errors="coerce",
    )

    x = make_design(
        df,
        include_spell_age=include_spell_age,
    )

    complete = pd.concat(
        [y.rename("y"), x],
        axis=1,
    ).notna().all(axis=1)

    d = df.loc[complete].copy()
    y = y.loc[complete].astype(float)
    x = x.loc[complete].astype(float)

    gp = codes(
        d["nba_player_id"].astype(str)
    )

    gts = codes(
        d["team"].astype(str)
        + "|"
        + d["season"].astype(str)
    )

    z = np.column_stack(
        [y.to_numpy(), x.to_numpy()]
    )

    zr = absorb_two_fe(
        z,
        gp,
        gts,
    )

    yr = zr[:, 0]
    xr = zr[:, 1:]

    keep = np.nanstd(
        xr,
        axis=0,
    ) > 1e-12

    names = list(x.columns[keep])
    xr = xr[:, keep]

    rank = np.linalg.matrix_rank(xr)

    if rank != xr.shape[1]:
        raise RuntimeError(
            f"{label}: rank deficient "
            f"{rank}/{xr.shape[1]}"
        )

    model = sm.OLS(
        yr,
        xr,
    ).fit()

    cp = codes(
        d["nba_player_id"].astype(str)
    )

    cg = codes(
        d["game_id"].astype(str)
    )

    cov, _, _ = cov_cluster_2groups(
        model,
        cp,
        cg,
        use_correction=True,
    )

    base_name = "star_post"

    if base_name not in names:
        raise RuntimeError(
            f"{label}: star_post missing."
        )

    j0 = names.index(base_name)

    rows = []

    for k in TAUS:
        if k == 0:
            b = float(model.params[j0])
            var = float(cov[j0, j0])

            delta = np.nan
            delta_se = np.nan
            delta_p = np.nan

        else:
            label_k = (
                f"m{abs(k)}"
                if k < 0
                else f"p{k}"
            )

            n = f"star_post_tau_{label_k}"

            if n not in names:
                raise RuntimeError(
                    f"{label}: missing {n}"
                )

            j = names.index(n)

            delta = float(model.params[j])
            delta_se = float(np.sqrt(cov[j, j]))
            delta_p = float(
                2 * stats.norm.sf(
                    abs(delta / delta_se)
                )
            )

            b = float(
                model.params[j0]
                + model.params[j]
            )

            var = float(
                cov[j0, j0]
                + cov[j, j]
                + 2 * cov[j0, j]
            )

        se = np.sqrt(var)

        rows.append(
            {
                "model": label,
                "event_time": k,
                "N": int(len(d)),
                "coefficient_pp": 100 * b,
                "se_pp": 100 * se,
                "ci_low_pp": 100 * (
                    b - 1.96 * se
                ),
                "ci_high_pp": 100 * (
                    b + 1.96 * se
                ),
                "p_value": float(
                    2 * stats.norm.sf(
                        abs(b / se)
                    )
                ),
                "delta_vs_tau0_pp": (
                    100 * delta
                    if np.isfinite(delta)
                    else np.nan
                ),
                "delta_vs_tau0_se_pp": (
                    100 * delta_se
                    if np.isfinite(delta_se)
                    else np.nan
                ),
                "delta_vs_tau0_p": delta_p,
                "rank": int(rank),
                "columns": int(xr.shape[1]),
            }
        )

    # Joint H0: all event-time Star×Post differentials
    # equal the tau=0 differential.
    interaction_names = []

    for k in TAUS:
        if k == 0:
            continue

        label_k = (
            f"m{abs(k)}"
            if k < 0
            else f"p{k}"
        )

        interaction_names.append(
            f"star_post_tau_{label_k}"
        )

    idx = [
        names.index(n)
        for n in interaction_names
    ]

    bvec = np.asarray(
        model.params
    )[idx]

    v = cov[np.ix_(idx, idx)]

    stat = float(
        bvec.T
        @ np.linalg.pinv(v)
        @ bvec
    )

    df_wald = int(
        np.linalg.matrix_rank(v)
    )

    joint_p = float(
        stats.chi2.sf(
            stat,
            df_wald,
        )
    )

    return pd.DataFrame(rows), {
        "model": label,
        "N": int(len(d)),
        "joint_equal_event_time_stat": stat,
        "joint_df": df_wald,
        "joint_p": joint_p,
    }


def add_stage10_flags(panel):
    panel = panel.copy()

    panel["star_stage10"] = boolish(
        panel["star_PPP_it"]
    ).astype(int)

    panel["postPPP_stage10"] = (
        panel["season"]
        .astype(str)
        .isin(
            {"2023-24", "2024-25", "2025-26"}
        )
        .astype(int)
    )

    panel["new_absence_onset"] = boolish(
        panel["absence_onset"]
    ).astype(int)

    panel["currently_absent"] = boolish(
        panel["absence_now"]
    ).astype(int)

    panel["onset_risk"] = boolish(
        panel["at_risk_for_new_onset"]
    )

    return panel


print("Loading inputs...", flush=True)

events = pd.read_csv(
    EVENT_PATH,
    low_memory=False,
)

panel = add_stage10_flags(
    pd.read_csv(
        PANEL_PATH,
        low_memory=False,
    )
)

repair = pd.read_csv(
    REPAIR_PATH,
    low_memory=False,
)


all_results = []
joint_results = []
assignment_qas = []


for tvdef in [
    "legacy_primary",
    "harmonized_linear",
]:
    assignment, qa = nearest_assignments(
        events,
        tvdef,
    )

    assignment_qas.append(qa)

    # -----------------------------------------------------
    # Onset
    # -----------------------------------------------------

    onset = panel.merge(
        assignment,
        on="player_team_game_id",
        how="inner",
        validate="one_to_one",
    )

    onset = onset.loc[
        onset["onset_risk"]
    ].copy()

    r, j = fit_event_model(
        onset,
        "new_absence_onset",
        f"Onset — {tvdef}",
        include_spell_age=False,
    )

    r["tv_definition"] = tvdef
    all_results.append(r)
    joint_results.append(j)

    # -----------------------------------------------------
    # Current absence prevalence
    # -----------------------------------------------------

    prevalence = panel.merge(
        assignment,
        on="player_team_game_id",
        how="inner",
        validate="one_to_one",
    )

    r, j = fit_event_model(
        prevalence,
        "currently_absent",
        f"Absence prevalence — {tvdef}",
        include_spell_age=False,
    )

    r["tv_definition"] = tvdef
    all_results.append(r)
    joint_results.append(j)

    # -----------------------------------------------------
    # Repair
    # -----------------------------------------------------

    rep = repair.merge(
        assignment,
        on="player_team_game_id",
        how="inner",
        validate="one_to_one",
    )

    rep = rep.loc[
        boolish(
            rep["repair_primary_eligible"]
        )
    ].copy()

    rep["return_available_today_int"] = boolish(
        rep["return_available_today"]
    ).astype(int)

    r, j = fit_event_model(
        rep,
        "return_available_today_int",
        f"Repair — {tvdef}",
        include_spell_age=True,
    )

    r["tv_definition"] = tvdef
    all_results.append(r)
    joint_results.append(j)


results = pd.concat(
    all_results,
    ignore_index=True,
)

results["delta_vs_tau0_q_bh"] = np.nan

for model_name, idx in results.groupby("model").groups.items():
    idx = list(idx)
    subidx = [
        i for i in idx
        if results.loc[i, "event_time"] != 0
    ]

    pvals = results.loc[
        subidx,
        "delta_vs_tau0_p",
    ].to_numpy()

    results.loc[
        subidx,
        "delta_vs_tau0_q_bh",
    ] = multipletests(
        pvals,
        method="fdr_bh",
    )[1]

joint = pd.DataFrame(
    joint_results
)

results.to_csv(
    OUT / "nearest_tv_event_time_results.csv",
    index=False,
)

joint.to_csv(
    OUT / "nearest_tv_event_time_joint_tests.csv",
    index=False,
)


print("\nASSIGNMENT QA")

for q in assignment_qas:
    print(q)


print("\nEVENT-TIME COEFFICIENTS")

print(
    results[
        [
            "model",
            "event_time",
            "N",
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
    ].to_string(index=False)
)


print("\nJOINT EVENT-TIME TESTS")

print(
    joint.to_string(index=False)
)

print("\nWROTE:", OUT)
