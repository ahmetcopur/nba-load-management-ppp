from pathlib import Path
import json

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[2]

PANEL_PATH = REPO / "data_final/player_game_panel_analysis_ready.csv.gz"
SPELL_PATH = REPO / "data_final/absence_spells_taxonomy_frozen.csv.gz"

# Used only to recover the already-frozen harmonized TV definition at game level.
CADENCE_PATH = (
    REPO
    / "data_intermediate/player_team_game_harmonized_cadence.csv.gz"
)

OUT = REPO / "data_intermediate/reliability_stage10"
OUT.mkdir(parents=True, exist_ok=True)

POST_SEASONS = {"2023-24", "2024-25", "2025-26"}


def boolish(s):
    if pd.api.types.is_bool_dtype(s):
        return s.fillna(False).astype(bool)

    if pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce").fillna(0).ne(0)

    return (
        s.astype(str)
        .str.strip()
        .str.lower()
        .isin({"true", "1", "yes", "y", "t"})
    )


def normalize_team(s):
    return (
        s.astype(str)
        .str.lower()
        .str.strip()
        .str.replace(r"[^a-z0-9]+", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def category4(s):
    s = s.fillna("unknown").astype(str).str.strip().str.lower()

    out = pd.Series("other", index=s.index, dtype="object")
    out.loc[s.eq("specific")] = "specific"
    out.loc[s.eq("vague")] = "vague"
    out.loc[s.eq("explicit_rest")] = "explicit_rest"

    return out


print("Loading frozen inputs...", flush=True)

panel = pd.read_csv(PANEL_PATH, low_memory=False)
spells = pd.read_csv(SPELL_PATH, low_memory=False)
cadence = pd.read_csv(CADENCE_PATH, low_memory=False)

print("panel rows:", len(panel), flush=True)
print("spell rows:", len(spells), flush=True)
print("cadence rows:", len(cadence), flush=True)


# ---------------------------------------------------------------------
# 1. Basic normalization
# ---------------------------------------------------------------------

for df in (panel, spells, cadence):
    if "season" in df.columns:
        df["season"] = df["season"].astype(str)

panel["_team_key"] = normalize_team(panel["team"])
spells["_team_key"] = normalize_team(spells["team"])

panel["team_game_number"] = pd.to_numeric(
    panel["team_game_number"], errors="coerce"
)

panel["absence_now_bool"] = boolish(panel["absence_now"])
panel["played_bool_clean"] = boolish(panel["played_bool"])
panel["absence_onset_bool"] = boolish(panel["absence_onset"])

if "at_risk_for_new_onset" in panel.columns:
    panel["onset_risk_bool"] = boolish(panel["at_risk_for_new_onset"])
else:
    raise RuntimeError("Missing at_risk_for_new_onset from full panel.")

panel["star_stage10"] = boolish(panel["star_PPP_it"]).astype(int)
panel["postPPP_stage10"] = panel["season"].isin(POST_SEASONS).astype(int)

panel["tv_legacy"] = boolish(panel["announced_tv_primary"]).astype(int)


# ---------------------------------------------------------------------
# 2. Recover harmonized TV exposure from the frozen cadence panel
# ---------------------------------------------------------------------

tv_candidates = [
    "tv_harmonized_linear",
    "harmonized_linear",
    "announced_tv_harmonized_linear",
]

tv_harmonized_col = next(
    (c for c in tv_candidates if c in cadence.columns),
    None,
)

if tv_harmonized_col is None:
    raise RuntimeError(
        "Could not find harmonized TV column in cadence panel.\n"
        "Cadence columns are:\n"
        + "\n".join(cadence.columns)
    )

game_key_candidates = ["game_id", "nba_game_id"]
game_key = next(
    (
        c
        for c in game_key_candidates
        if c in cadence.columns and c in panel.columns
    ),
    None,
)

if game_key is None:
    raise RuntimeError(
        "Could not find a common game key between full and cadence panels."
    )

cadence["_team_key"] = normalize_team(cadence["team"])
cadence["_tv_harmonized"] = boolish(
    cadence[tv_harmonized_col]
).astype(int)

tv_map = (
    cadence[
        ["season", game_key, "_team_key", "_tv_harmonized"]
    ]
    .dropna(subset=[game_key])
    .drop_duplicates()
)

conflict = (
    tv_map.groupby(
        ["season", game_key, "_team_key"]
    )["_tv_harmonized"]
    .nunique()
)

if (conflict > 1).any():
    bad = conflict[conflict > 1]
    raise RuntimeError(
        f"Harmonized TV conflicts at {len(bad)} team-games."
    )

tv_map = (
    tv_map.groupby(
        ["season", game_key, "_team_key"],
        as_index=False
    )["_tv_harmonized"]
    .first()
)

panel = panel.merge(
    tv_map,
    on=["season", game_key, "_team_key"],
    how="left",
    validate="many_to_one",
)

panel["tv_harmonized"] = panel["_tv_harmonized"]


# ---------------------------------------------------------------------
# 3. Player-game transition construction
# ---------------------------------------------------------------------

sort_cols = [
    "season",
    "team",
    "nba_player_id",
    "team_game_number",
]

panel = panel.sort_values(sort_cols).reset_index(drop=True)

grp = panel.groupby(
    ["season", "team", "nba_player_id"],
    sort=False,
    dropna=False,
)

panel["prev_team_game_number"] = grp[
    "team_game_number"
].shift(1)

panel["prev_absence"] = grp[
    "absence_now_bool"
].shift(1)

panel["prev_spell_id"] = grp[
    "spell_id"
].shift(1)

panel["prev_played"] = grp[
    "played_bool_clean"
].shift(1)

panel["consecutive_observation"] = (
    panel["team_game_number"]
    == panel["prev_team_game_number"] + 1
)

panel["repair_risk"] = (
    panel["consecutive_observation"]
    & panel["prev_absence"].fillna(False)
)

panel["return_available_today"] = (
    panel["repair_risk"]
    & ~panel["absence_now_bool"]
)

panel["return_played_today"] = (
    panel["repair_risk"]
    & panel["played_bool_clean"]
)


# ---------------------------------------------------------------------
# 4. Attach previous-spell information to repair risk set
# ---------------------------------------------------------------------

spell_meta = spells[
    [
        "spell_id",
        "start_team_game_number",
        "left_censored",
        "initial_class_frozen",
        "final_class_frozen",
        "duration_games_observed",
        "available_after",
    ]
].copy()

if spell_meta["spell_id"].duplicated().any():
    raise RuntimeError("spell_id is not unique in frozen spell table.")

spell_meta = spell_meta.rename(
    columns={
        "start_team_game_number": "prev_spell_start_team_game_number",
        "left_censored": "prev_spell_left_censored",
        "initial_class_frozen": "prev_initial_class_frozen",
        "final_class_frozen": "prev_final_class_frozen",
        "duration_games_observed": "prev_spell_duration_observed",
        "available_after": "prev_spell_available_after",
    }
)

repair = panel.loc[panel["repair_risk"]].copy()

repair = repair.merge(
    spell_meta,
    left_on="prev_spell_id",
    right_on="spell_id",
    how="left",
    suffixes=("", "_spellmeta"),
    validate="many_to_one",
)

repair["prev_spell_left_censored_bool"] = boolish(
    repair["prev_spell_left_censored"]
)

repair["spell_age_entering_game"] = (
    pd.to_numeric(
        repair["prev_team_game_number"],
        errors="coerce",
    )
    - pd.to_numeric(
        repair["prev_spell_start_team_game_number"],
        errors="coerce",
    )
    + 1
)

repair["prev_onset_category4"] = category4(
    repair["prev_initial_class_frozen"]
)

repair["prev_spell_metadata_found"] = (
    repair["prev_spell_start_team_game_number"].notna()
)

repair["repair_primary_eligible"] = (
    repair["prev_spell_metadata_found"]
    & ~repair["prev_spell_left_censored_bool"]
    & repair["spell_age_entering_game"].ge(1)
)

# Useful flexible spell-age bins.
repair["spell_age_bin"] = pd.cut(
    repair["spell_age_entering_game"],
    bins=[0, 1, 2, 3, 5, 10, np.inf],
    labels=[
        "1",
        "2",
        "3",
        "4-5",
        "6-10",
        "11+",
    ],
    right=True,
)

repair.to_csv(
    OUT / "repair_risk_panel.csv.gz",
    index=False,
    compression="gzip",
)


# ---------------------------------------------------------------------
# 5. Build one row per team-game for future-TV calculations
# ---------------------------------------------------------------------

schedule_cols = [
    "season",
    "team",
    "_team_key",
    "team_game_number",
    "game_id",
    "game_date_et",
    "tv_legacy",
    "tv_harmonized",
]

schedule_cols = [
    c for c in schedule_cols if c in panel.columns
]

schedule = panel[schedule_cols].drop_duplicates()

group_keys = ["season", "team", "team_game_number"]

conflict_cols = ["tv_legacy", "tv_harmonized"]

for c in conflict_cols:
    chk = (
        schedule.groupby(group_keys)[c]
        .nunique(dropna=True)
    )

    if (chk > 1).any():
        raise RuntimeError(
            f"{c} is not constant within team-game."
        )

schedule = (
    schedule.sort_values(group_keys)
    .drop_duplicates(group_keys)
    .reset_index(drop=True)
)


# ---------------------------------------------------------------------
# 6. Absence-spell duration panel
# ---------------------------------------------------------------------

spell_panel = spells.copy()

spell_panel["absence_onset_bool"] = boolish(
    spell_panel["absence_onset"]
)
spell_panel["left_censored_bool"] = boolish(
    spell_panel["left_censored"]
)
spell_panel["available_after_bool"] = boolish(
    spell_panel["available_after"]
)

spell_panel["star_stage10"] = boolish(
    spell_panel["star_PPP_it"]
).astype(int)

spell_panel["postPPP_stage10"] = (
    spell_panel["season"]
    .astype(str)
    .isin(POST_SEASONS)
    .astype(int)
)

spell_panel["onset_category4"] = category4(
    spell_panel["initial_class_frozen"]
)

spell_panel["duration_games_observed"] = pd.to_numeric(
    spell_panel["duration_games_observed"],
    errors="coerce",
)

# Primary duration universe: an actual observed onset,
# not a spell already in progress when observation began.
spell_panel["duration_primary_universe"] = (
    spell_panel["absence_onset_bool"]
    & ~spell_panel["left_censored_bool"]
)

# A spell is considered completed only when subsequent availability
# is actually observed. Everything else remains censored.
spell_panel["completed_spell"] = (
    spell_panel["duration_primary_universe"]
    & spell_panel["available_after_bool"]
)

spell_panel["right_censored"] = (
    spell_panel["duration_primary_universe"]
    & ~spell_panel["completed_spell"]
)

spell_panel["one_game_spell"] = np.where(
    spell_panel["completed_spell"],
    (
        spell_panel["duration_games_observed"] == 1
    ).astype(float),
    np.nan,
)

spell_panel["spell_le_2_games"] = np.where(
    spell_panel["completed_spell"],
    (
        spell_panel["duration_games_observed"] <= 2
    ).astype(float),
    np.nan,
)


# Attach onset-game TV.
onset_sched = schedule[
    [
        "season",
        "team",
        "team_game_number",
        "tv_legacy",
        "tv_harmonized",
    ]
].rename(
    columns={
        "team_game_number": "start_team_game_number",
        "tv_legacy": "onset_tv_legacy",
        "tv_harmonized": "onset_tv_harmonized",
    }
)

spell_panel = spell_panel.merge(
    onset_sched,
    on=["season", "team", "start_team_game_number"],
    how="left",
    validate="many_to_one",
)


# Next team game TV.
next1 = schedule[
    [
        "season",
        "team",
        "team_game_number",
        "tv_legacy",
        "tv_harmonized",
    ]
].copy()

next1["start_team_game_number"] = (
    next1["team_game_number"] - 1
)

next1 = next1.rename(
    columns={
        "tv_legacy": "next1_tv_legacy",
        "tv_harmonized": "next1_tv_harmonized",
    }
).drop(columns="team_game_number")

spell_panel = spell_panel.merge(
    next1,
    on=["season", "team", "start_team_game_number"],
    how="left",
    validate="many_to_one",
)


# Two games after onset.
next2 = schedule[
    [
        "season",
        "team",
        "team_game_number",
        "tv_legacy",
        "tv_harmonized",
    ]
].copy()

next2["start_team_game_number"] = (
    next2["team_game_number"] - 2
)

next2 = next2.rename(
    columns={
        "tv_legacy": "next2_tv_legacy",
        "tv_harmonized": "next2_tv_harmonized",
    }
).drop(columns="team_game_number")

spell_panel = spell_panel.merge(
    next2,
    on=["season", "team", "start_team_game_number"],
    how="left",
    validate="many_to_one",
)


for tvdef in ["legacy", "harmonized"]:
    a = spell_panel[f"next1_tv_{tvdef}"]
    b = spell_panel[f"next2_tv_{tvdef}"]

    spell_panel[f"tv_within_next1_{tvdef}"] = (
        a.eq(1)
    ).astype(int)

    spell_panel[f"tv_within_next2_{tvdef}"] = (
        a.eq(1) | b.eq(1)
    ).astype(int)


spell_panel.to_csv(
    OUT / "absence_spell_duration_panel.csv.gz",
    index=False,
    compression="gzip",
)


# ---------------------------------------------------------------------
# 7. TV-centered stacked event-time panel
# ---------------------------------------------------------------------

event_base = panel.copy()

event_base["new_absence_onset"] = (
    event_base["absence_onset_bool"].astype(int)
)

event_base["currently_absent"] = (
    event_base["absence_now_bool"].astype(int)
)

event_base["return_available_today_int"] = (
    event_base["return_available_today"].astype(int)
)

event_base["return_played_today_int"] = (
    event_base["return_played_today"].astype(int)
)

event_base["repair_risk_int"] = (
    event_base["repair_risk"].astype(int)
)

event_base["onset_risk_int"] = (
    event_base["onset_risk_bool"].astype(int)
)


def make_event_stack(base, sched, tv_col, tv_name):
    anchors = sched.loc[
        sched[tv_col].eq(1)
        & sched["team_game_number"].notna()
    ].copy()

    anchors = anchors.sort_values(
        ["season", "team", "team_game_number"]
    )

    # An anchor is isolated if no other TV anchor for that team-season
    # lies close enough to make the +/-3 windows overlap.
    isolated = []

    for _, g in anchors.groupby(
        ["season", "team"],
        sort=False,
    ):
        nums = g["team_game_number"].to_numpy()

        for x in nums:
            other = nums[nums != x]
            overlap = (
                np.any(np.abs(other - x) <= 6)
                if len(other)
                else False
            )
            isolated.append(not overlap)

    anchors["isolated_anchor"] = isolated

    pieces = []

    for (season, team), ag in anchors.groupby(
        ["season", "team"],
        sort=False,
    ):
        pg = base.loc[
            (base["season"] == season)
            & (base["team"] == team)
            & base["team_game_number"].notna()
        ]

        if pg.empty:
            continue

        for _, a in ag.iterrows():
            anchor_num = a["team_game_number"]

            q = pg.loc[
                pg["team_game_number"]
                .between(anchor_num - 3, anchor_num + 3)
            ].copy()

            if q.empty:
                continue

            q["event_time"] = (
                q["team_game_number"] - anchor_num
            ).astype(int)

            q["anchor_team_game_number"] = anchor_num
            q["anchor_game_id"] = a.get("game_id", np.nan)
            q["anchor_game_date_et"] = a.get(
                "game_date_et",
                np.nan,
            )
            q["tv_definition"] = tv_name
            q["isolated_anchor"] = bool(
                a["isolated_anchor"]
            )

            pieces.append(q)

    if not pieces:
        return pd.DataFrame()

    out = pd.concat(pieces, ignore_index=True)

    row_id = "player_team_game_id"

    out["overlap_count"] = (
        out.groupby(["tv_definition", row_id])[row_id]
        .transform("size")
    )

    out["stack_weight"] = 1.0 / out["overlap_count"]

    return out


legacy_events = make_event_stack(
    event_base,
    schedule,
    "tv_legacy",
    "legacy_primary",
)

harm_events = make_event_stack(
    event_base.loc[event_base["tv_harmonized"].notna()],
    schedule.loc[schedule["tv_harmonized"].notna()],
    "tv_harmonized",
    "harmonized_linear",
)

event_panel = pd.concat(
    [legacy_events, harm_events],
    ignore_index=True,
)

event_panel.to_csv(
    OUT / "tv_event_transition_panel.csv.gz",
    index=False,
    compression="gzip",
)


# ---------------------------------------------------------------------
# 8. QA
# ---------------------------------------------------------------------

continuing = repair.loc[
    repair["absence_now_bool"]
    & repair["spell_id"].notna()
    & repair["prev_spell_id"].notna()
]

continuing_spell_mismatch = int(
    (
        continuing["spell_id"].astype(str)
        != continuing["prev_spell_id"].astype(str)
    ).sum()
)

duration_primary = spell_panel.loc[
    spell_panel["duration_primary_universe"]
]

category_counts = (
    duration_primary["onset_category4"]
    .value_counts(dropna=False)
    .to_dict()
)

event_qa = {}

if len(event_panel):
    row_id = "player_team_game_id"

    for tvdef, g in event_panel.groupby("tv_definition"):
        event_qa[tvdef] = {
            "stacked_rows": int(len(g)),
            "unique_player_games": int(g[row_id].nunique()),
            "anchors": int(
                g[
                    [
                        "season",
                        "team",
                        "anchor_team_game_number",
                    ]
                ]
                .drop_duplicates()
                .shape[0]
            ),
            "isolated_anchors": int(
                g.loc[g["isolated_anchor"]][
                    [
                        "season",
                        "team",
                        "anchor_team_game_number",
                    ]
                ]
                .drop_duplicates()
                .shape[0]
            ),
            "share_stacked_rows_with_overlap": float(
                g["overlap_count"].gt(1).mean()
            ),
            "mean_overlap_count": float(
                g["overlap_count"].mean()
            ),
        }


schedule_harmonized_missing = int(
    schedule["tv_harmonized"].isna().sum()
)

qa = {
    "inputs": {
        "player_game_rows": int(len(panel)),
        "players": int(panel["nba_player_id"].nunique()),
        "spell_rows": int(len(spells)),
        "team_games": int(len(schedule)),
        "duplicate_player_team_game_ids": int(
            panel["player_team_game_id"].duplicated().sum()
        ),
    },
    "tv_mapping": {
        "harmonized_source_column": tv_harmonized_col,
        "game_key": game_key,
        "full_panel_rows_missing_harmonized_tv": int(
            panel["tv_harmonized"].isna().sum()
        ),
        "team_games_missing_harmonized_tv": schedule_harmonized_missing,
        "legacy_tv_team_games": int(
            schedule["tv_legacy"].eq(1).sum()
        ),
        "harmonized_tv_team_games": int(
            schedule["tv_harmonized"].eq(1).sum()
        ),
    },
    "repair": {
        "risk_rows": int(len(repair)),
        "returns_available": int(
            repair["return_available_today"].sum()
        ),
        "return_available_rate": float(
            repair["return_available_today"].mean()
        )
        if len(repair)
        else None,
        "returns_played": int(
            repair["return_played_today"].sum()
        ),
        "primary_eligible_rows": int(
            repair["repair_primary_eligible"].sum()
        ),
        "left_censored_risk_rows": int(
            repair["prev_spell_left_censored_bool"].sum()
        ),
        "missing_previous_spell_metadata": int(
            (~repair["prev_spell_metadata_found"]).sum()
        ),
        "continuing_spell_id_mismatches": (
            continuing_spell_mismatch
        ),
    },
    "duration": {
        "observed_onset_non_left_censored_spells": int(
            len(duration_primary)
        ),
        "completed_spells": int(
            duration_primary["completed_spell"].sum()
        ),
        "right_censored_spells": int(
            duration_primary["right_censored"].sum()
        ),
        "one_game_completed_spells": int(
            duration_primary["one_game_spell"]
            .fillna(0)
            .sum()
        ),
        "le2_completed_spells": int(
            duration_primary["spell_le_2_games"]
            .fillna(0)
            .sum()
        ),
        "category4_counts": {
            str(k): int(v)
            for k, v in category_counts.items()
        },
    },
    "event_windows": event_qa,
}

qa_path = OUT / "reliability_stage10_qa.json"

qa_path.write_text(
    json.dumps(qa, indent=2)
)

print("\nSTAGE 10 QA")
print(json.dumps(qa, indent=2))
print("\nWROTE", OUT)
