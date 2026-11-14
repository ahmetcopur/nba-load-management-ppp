#!/usr/bin/env python3
"""Pure exact-row comparators for Cup original-archive joins.

This module deliberately does NOT open private files, infer provider history,
or claim a historical archive has been checked. The calling entry points must
first independently validate first-party source rows AND verify the original
immutable ZIP's complete pinned SHA-256.

Keeping exact comparison separate from ZIP access makes it possible to test
both successful joins AND subtle row-level failures using synthetic fixtures
in public CI. All exact joins treat missing/extra and DUPLICATE keys as errors.
No fuzzy date, name, broadcaster normalization or score-based matching.
"""
from __future__ import annotations

from collections import Counter

import pandas as pd


MATCH = ("season", "game_date_et", "away_team", "home_team")
TV = (*MATCH, "first_release_network")
KNOCKOUT = ("season", "game_date_et", "cup_stage")


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise ValueError("Cup original-archive exact join failed: " + msg)


def records(frame: pd.DataFrame, columns: tuple[str, ...]) -> list[tuple[str, ...]]:
    require(all(x in frame.columns for x in columns),
            f"missing required columns: {set(columns)-set(frame.columns)}")
    selected = frame.loc[:, list(columns)]
    require(not selected.isna().any().any(),
            f"null values in original archive comparison fields {columns}")
    # Preserve literal "NBA TV" vs "" vs "NBC/Peacock" vs "Prime".
    return [tuple(x) for x in selected.itertuples(index=False, name=None)]


def unique_values(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> set[tuple]:
    items=records(frame,columns)
    require(len(items)==len(set(items)), f"{label} duplicated on {columns}")
    return set(items)


def exact_group_fixture_join(source: pd.DataFrame,
                             archive_cup: pd.DataFrame,
                             expected: int,
                             subset: bool=False) -> dict:
    """Compare real source date/away/home tuple with original Cup lookup.

    Source/archived columns must already be restricted to the relevant
    season/stage, and the archive must be full-SHA-pinned by the caller.
    subset=True is allowed only for a documented partial original release.
    """
    require(len(source)==expected, "unexpected source fixture count")
    require(len(archive_cup)>=expected, "original archive has fewer group rows")
    known=unique_values(source,MATCH,"independent public source fixture")
    frozen=unique_values(archive_cup,MATCH,"original frozen Cup fixture")
    missing=known-frozen
    extra=frozen-known
    require(not missing and (subset or not extra),
            f"date/away/home group mismatch: {len(missing)} source rows missing "
            f"and {len(extra)} original rows extra")
    require(len(known)==expected, "not every source row is a distinct game")
    return {
        "source_fixture_exact":len(known),
        "original_archive_game_count":len(frozen),
        "exact_full_match":not subset,
        "source_keys_missing_from_original":0,
    }


def exact_first_release_network_join(
    source: pd.DataFrame, original_full_season_pdf: pd.DataFrame,
    expected: int, subset: bool=False,
) -> dict:
    """Compare exact original source fields including network literal."""
    require(len(source)==expected, "unexpected source national-TV comparison count")
    our_keys=unique_values(source,MATCH,"initial Cup source TV fixture")
    pdf_keys=unique_values(original_full_season_pdf,MATCH,
                           "original league preseason PDF fixture")
    require(our_keys <= pdf_keys,
            f"original preseason PDF missing {len(our_keys-pdf_keys)} source fixture keys")
    # Only match the named subset, not all 1,200 regular-season PDF rows.
    filt=original_full_season_pdf.loc[
        original_full_season_pdf.loc[:,list(MATCH)].apply(tuple,axis=1).isin(our_keys)
    ]
    require(len(filt)==expected, "wrong number of original NBA PDF Cup fixture rows")
    ours=unique_values(source,TV,"original Cup first-release network row")
    theirs=unique_values(filt,TV,"original NBA preseason network row")
    missing,extra=ours-theirs,theirs-ours
    require(not missing and not extra,
            f"exact (date,away,home,network) TV mismatch: {len(missing)} "
            f"source tuples not in original PDF and {len(extra)} PDF tuples not in source")
    return {
        "exact_NBA_source_network_rows":expected,
        "national_provider_source_row_mismatches":0,
        "blank_vs_national_network_strictly_distinguished":True,
    }


def knockout_identity_source(row) -> tuple:
    return (
        row.season,row.game_date_et,row.cup_stage,
        *sorted((row.participant_1,row.participant_2)),
    )


def knockout_identity_original(row) -> tuple:
    return (
        row.season,row.game_date_et,row.cup_stage,
        *sorted((row.away_team,row.home_team)),
    )


def exact_knockout_fixture_join(source: pd.DataFrame,
                                original_knockout: pd.DataFrame) -> dict:
    """Compare all 18 games; six neutral-site home designations remain OPEN."""
    require(len(source)==18 and len(original_knockout)==18,
            "expected exactly 18 knockout fixture identities on both sides")
    ours=[knockout_identity_source(r) for r in source.itertuples(index=False)]
    theirs=[knockout_identity_original(r)
            for r in original_knockout.itertuples(index=False)]
    require(len(set(ours))==18 and len(set(theirs))==18,
            "knockout source/original contains duplicate fixture identities")
    source_only=set(ours)-set(theirs)
    original_only=set(theirs)-set(ours)
    require(not source_only and not original_only,
            f"knockout date/stage/unordered participants drift: "
            f"{len(source_only)} source-only and {len(original_only)} archive-only")

    qf_s=source.loc[source.cup_stage.eq("quarterfinal")]
    qf_a=original_knockout.loc[original_knockout.cup_stage.eq("quarterfinal")]
    require(len(qf_s)==12 and len(qf_a)==12,
            "knockout quarterfinal source or original not 12 games")
    s=unique_values(qf_s,(*MATCH,"cup_stage"),"original NBA quarterfinal source")
    a=unique_values(qf_a,(*MATCH,"cup_stage"),"original private Cup quarterfinal")
    require(s==a, "knockout quarterfinal ordered home/away source drift")
    require(len(source.loc[source.cup_stage.eq("semifinal")])==6 and
            len(original_knockout.loc[original_knockout.cup_stage.eq("semifinal")])==6,
            "neutral semifinals not six games")
    return {
        "original_knockout_stage_date_unordered_pair_rows_exact":18,
        "original_quarterfinal_ordered_home_away_rows_exact":12,
        "neutral_semifinal_nominal_home_team_verified":False,
        "original_archive_knockout_source_mismatches":0,
    }
