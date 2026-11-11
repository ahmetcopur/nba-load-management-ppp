#!/usr/bin/env python3
"""One-command PRIVATE Cup source acceptance with original immutable research ZIPs.

Run this locally only when BOTH original, SHA-256 pinned historical research
archives are available. It invokes all individual source-to-original
comparisons (not just source-only self-consistency) and writes one new
SANITIZED aggregate report. No original ZIPs are opened for writing.

No private original ZIP bytes are supplied to GitHub Actions. CI only
exercises the same exact comparators on SYNTHETIC fixture panels. A passing
public CI workflow is never evidence this command ran on the real archives.

Important open boundaries even after all components PASS:
* Complete standalone original Aug 13 2025 NBA Cup 60-fixture by-day PDF
  was not recovered. 19 first-party + 14 secondary contemporaneous exact
  records are partial source tiers, 3 Pelicans-only revised-story caveats.
* The six Las Vegas knockout semifinal nominal home/away designations
  require separate first-party NBA game-log corroboration.
* Actual knockout provider != original preseason announced opponent
  national TV treatment. 2020 incomplete NBA TV, awards, taxonomy,
  covariates, full original pipeline and manuscript still remain open.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

try:
    from scripts.data_rebuild import verify_official_NBA_cup_groups as group_prior
    from scripts.data_rebuild import verify_official_nba_tv_announcements as tv
    from scripts.data_rebuild import verify_official_nba_cup_first_release_fixtures as cup_2023_24
    from scripts.data_rebuild import verify_official_nba_cup_2025_aug13_team_press_sources as cup_2025_19
    from scripts.data_rebuild import verify_cup_2025_aug13_contemporaneous_secondary_sources as cup_2025_33
    from scripts.data_rebuild import verify_official_nba_cup_2025_named_broadcasts as cup_2025_9tv
    from scripts.data_rebuild import verify_official_nba_cup_2025_all_15_national_broadcasts as cup_2025_15tv
    from scripts.data_rebuild import verify_official_nba_cup_knockout_original_fixtures as knockout
except ModuleNotFoundError:
    import verify_official_NBA_cup_groups as group_prior
    import verify_official_nba_tv_announcements as tv
    import verify_official_nba_cup_first_release_fixtures as cup_2023_24
    import verify_official_nba_cup_2025_aug13_team_press_sources as cup_2025_19
    import verify_cup_2025_aug13_contemporaneous_secondary_sources as cup_2025_33
    import verify_official_nba_cup_2025_named_broadcasts as cup_2025_9tv
    import verify_official_nba_cup_2025_all_15_national_broadcasts as cup_2025_15tv
    import verify_official_nba_cup_knockout_original_fixtures as knockout


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise ValueError("Private NBA Cup original source acceptance: " + msg)


def original_sha_pins(cup_path: Path, freeze_path: Path) -> None:
    """Fail before returning ANY success if full immutable source hashes drift."""
    require(cup_path.is_file() and freeze_path.is_file(),
            "both original private ZIP paths must exist")
    require(cup_path.resolve() != freeze_path.resolve(),
            "original Cup ZIP and frozen research ZIP must be different files")
    require(sha256(cup_path.read_bytes()).hexdigest() == group_prior.ARCHIVE_SHA256,
            "immutable original NBA Cup ZIP SHA-256 mismatch")
    require(sha256(freeze_path.read_bytes()).hexdigest() == tv.FREEZE_SHA,
            "immutable original research freeze ZIP SHA-256 mismatch")


def run_original_private_cup_acceptance(cup_path: Path, freeze_path: Path) -> dict:
    """Run only genuine SHA-pinned PRIVATE archival comparisons, fail fast."""
    original_sha_pins(cup_path, freeze_path)

    full_198 = group_prior.verify_original_cup_lookup(cup_path)
    official_120 = cup_2023_24.load_source(cup_2023_24.DEFAULT_SOURCE)
    cup_2023_24.validate_first_release(official_120)
    group_120 = cup_2023_24.compare_to_private_archives(
        official_120, cup_path, freeze_path)

    team_19 = cup_2025_19.load_source(cup_2025_19.DEFAULT_SOURCE)
    cup_2025_19.validate_source(team_19)
    original_19 = cup_2025_19.original_private_compare(team_19, cup_path)

    secondary_14 = cup_2025_33.load(cup_2025_33.SECONDARY)
    cup_2025_33.validate_sources(secondary_14, team_19)
    original_33 = cup_2025_33.check_original_private(
        secondary_14, team_19, cup_path)

    national_9 = cup_2025_9tv.load_source(cup_2025_9tv.SOURCE)
    cup_2025_9tv.verify_named_source(national_9)
    original_9 = cup_2025_9tv.compare_original_archives(
        national_9, cup_path, freeze_path)

    national_15 = cup_2025_15tv.load(cup_2025_15tv.SOURCE)
    cup_2025_15tv.validate_15(national_15, national_9)
    original_15 = cup_2025_15tv.compare_original_private(
        national_15, national_9, cup_path, freeze_path)

    knockout_18 = knockout.load(knockout.SOURCE)
    knockout.validate_original_source(knockout_18)
    original_18 = knockout.compare_original_private(knockout_18, cup_path)

    # Independently check returned outcomes: a patched/errored/replaced
    # component must not be silently treated as a successful original run.
    expected = {
        "198_prior_original_Cup_group_stage_and_dates":
            (full_198,"PASS_OFFICIAL_NBA_GROUP_FIXTURE_AND_DATE_SOURCE_CHECK"),
        "120_2023_2024_first_Cup_game_and_network_rows":
            (group_120,"PASS_EXACT_ORIGINAL_PRIVATE_CUP_AND_TV_SOURCE_MATCH"),
        "19_2025_Aug13_original_team_game_rows":
            (original_19,"PASS_19_SAME_DAY_ORIGINAL_TEAM_RELEASES_TO_PRIVATE_CUP_LOOKUP"),
        "33_2025_Aug13_first_party_and_secondary_game_rows":
            (original_33,"PASS_ORIGINAL_PRIVATE_CUP_33_CONTEMPORANEOUS_FIXTURE_IDENTITIES"),
        "9_2025_Aug14_NBA_press_named_national_rows":
            (original_9,"PASS_NINE_ORIGINAL_PRIVATE_CUP_AND_TV_SOURCE_TUPLES"),
        "15_2025_Aug21_NBA_com_named_national_rows":
            (original_15,"PASS_15_ORIGINAL_PRIVATE_2025_NAMED_NATIONAL_CUP_GAME_TUPLES"),
        "18_2023_2025_knockout_date_opponent_pair_rows":
            (original_18,"PASS_18_ORIGINAL_CUP_ARCHIVE_DATE_UNORDERED_OPPONENTS_AND_12_QF_HOME_AWAY"),
    }
    for label, (result, expected_status) in expected.items():
        require(isinstance(result,dict) and result.get("status")==expected_status,
                f"strict original-private source subcheck failed: {label}")
    require(full_198["group_stage_unordered_opponent_fixtures_checked"]==180 and
            full_198["knockout_stage_games_on_official_dates_checked"]==18,
            "original full 198-game Cup source base not accepted")
    require(group_120["cup_group_fixtures_exact"]==120 and
            group_120["first_release_network_fields_exact"]==120,
            "2023/2024 120 source-release fields do not match exact originals")
    require(original_19["independent_Aug13_source_fixtures_exact_against_original_Cup"]==19,
            "2025 19 original NBA first-party fixture archive check incomplete")
    require(original_33["independently_transcribed_source_date_host_away_tuples_in_original_Cup"]==33,
            "2025 33 combined source-tier fixture archive check incomplete")
    require(original_9["source_Cup_game_tuples_exact"]==9 and
            original_9["source_preseason_PDF_network_tuples_exact"]==9,
            "2025 Aug14 nine NBA original broadcaster archive fields incomplete")
    require(original_15["original_Cup_fixture_tuples_exact"]==15 and
            original_15["original_preseason_PDF_network_tuples_exact"]==15,
            "2025 Aug21 fifteen NBA national broadcast archive fields incomplete")
    require(original_18["original_knockout_season_date_stage_opponent_pairs_exact"]==18 and
            original_18["original_quarterfinal_home_away_source_rows_exact"]==12,
            "original Cup 18 knockout or 12 quarterfinal host mappings incomplete")

    return {
        "status":"PASS_SUBSET_ORIGINAL_PRIVATE_CUP_AND_TV_SOURCE_GATES_WITH_OPEN_RESEARCH_LIMITS",
        "original_full_archive_sha256_cup":group_prior.ARCHIVE_SHA256,
        "original_full_archive_sha256_freeze":tv.FREEZE_SHA,
        "original_198_game_Cup_group_draw_and_stage_dates_replayed":198,
        "original_private_Cup_original_first_release_2023_2024_fixture_network_exact":120,
        "original_private_2025_first_party_Aug13_date_away_home_exact":19,
        "original_private_2025_first_dated_second_tier_aug13_combined_fixtures_exact":33,
        "original_private_2025_Aug14_named_national_NBA_broadcast_exact":9,
        "original_private_2025_Aug21_named_national_NBA_broadcast_exact":15,
        "original_private_2023_2025_knockout_stage_date_opponent_exact":18,
        "original_private_quarterfinal_host_assignment_exact":12,
        "neutral_semifinal_nominal_home_side_source_verified":False,
        "2025_original_Aug13_all_60_first_release_pdf_recovered":False,
        "three_2025_secondary_Pelicans_only_sources_have_later_edit_exception":True,
        "all_original_scientific_and_manuscript_gates_closed":False,
        "ready_to_merge_PR4":False,
        "original_private_source_ZIP_contents_uploaded_to_GitHub":False,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-cup-zip",type=Path,required=True)
    p.add_argument("--original-freeze-zip",type=Path,required=True)
    p.add_argument("--output-report",type=Path,required=True)
    args=p.parse_args()
    # Fail BEFORE reading any private archive if an existing result would
    # be overwritten or output path aliases either original immutable ZIP.
    target=args.output_report.resolve()
    require(not target.exists(),"refusing to overwrite an existing evidence report")
    require(target!=args.original_cup_zip.resolve() and
            target!=args.original_freeze_zip.resolve(),
            "new report path must not be one of the two original source ZIPs")
    result=run_original_private_cup_acceptance(
        args.original_cup_zip, args.original_freeze_zip
    )
    target.parent.mkdir(parents=True,exist_ok=True)
    # exclusive create ("x"), so a concurrent report is never overwritten.
    with target.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2)
        stream.write("\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
