"""Synthetic failure-mode coverage for original NBA player-ID replay."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from scripts.data_rebuild.verify_player_identity_replay import (
    BUILDER_MEMBER, compare_exact, immutable_original_helpers, resolve,
)


def h():
    def clean(x):
        return "" if pd.isna(x) else " ".join(str(x).split())
    def team(x):
        return clean(x).casefold()
    def full(x):
        v = clean(x)
        if "," in v:
            last, first = v.split(",", 1)
            return clean(first + " " + last)
        return v
    def person(x):
        return clean(x).casefold()
    return {"clean": clean, "norm_team": team,
            "full_report_name": full, "norm_person": person}


def report(name, game="G1", status="Out"):
    return {
        "season": "2023-24", "game_id": game, "team_norm": "Boston Celtics",
        "player_name": name, "current_status": status, "reason": "Illness",
        "team_submission_status": "submitted",
    }


class IdentitySourceReplayTests(unittest.TestCase):
    def setUp(self):
        self.xw = pd.DataFrame([{
            "season": "2023-24", "team_norm": "boston celtics",
            "player_name": "Direct, One", "nba_player_id": 101,
            "nba_player_name": "One Direct", "resolution_method": "auto_accepted",
            "resolution_status": "auto_accepted",
        }])
        self.alias = pd.DataFrame([{
            "report_full_name": "Two Alias", "nba_player_id": 102,
            "nba_player_name": "Two Alias",
        }])
        self.roster = pd.DataFrame([{
            "season": "2023-24", "team": "Boston Celtics",
            "nba_player_id": 103, "nba_player_name": "Three Roster",
        }])
        self.selected = pd.DataFrame([
            report("Direct, One"), report("Alias, Two"),
            report("Roster, Three"),
        ])

    def test_direct_reviewed_alias_and_roster_fallback_are_separate(self):
        r, counts = resolve(self.selected, self.xw, self.alias, self.roster, h())
        self.assertEqual([counts[k] for k in ("crosswalk_matched",
                            "reviewed_alias_fallback", "unique_roster_name_fallback",
                            "unresolved_before_final_dedup")], [1, 1, 1, 0])
        self.assertEqual(set(r.nba_player_id.astype(int)), {101, 102, 103})

    def test_ambiguous_alias_is_not_accepted(self):
        aliases = pd.concat([self.alias, pd.DataFrame([{
            "report_full_name": "Two Alias", "nba_player_id": 999,
            "nba_player_name": "Imposter",
        }])], ignore_index=True)
        _, counts = resolve(self.selected, self.xw, aliases, self.roster, h())
        self.assertEqual(counts["reviewed_alias_fallback"], 0)
        self.assertEqual(counts["unresolved_before_final_dedup"], 1)

    def test_duplicate_status_uses_original_severity_priority(self):
        rows = pd.concat([self.selected, pd.DataFrame([report(
            "Direct, One", status="Available")])], ignore_index=True)
        final, counts = resolve(rows, self.xw, self.alias, self.roster, h())
        self.assertEqual(len(final), 3)
        record = final[final.nba_player_id.eq(101)].iloc[0]
        self.assertEqual(record.current_status, "Out")
        self.assertEqual(counts["final_player_report_rows"], 3)

    def test_missing_original_source_report_field_fails(self):
        with self.assertRaisesRegex(ValueError, "Selected source report rows missing"):
            resolve(self.selected.drop(columns=["reason"]),
                    self.xw, self.alias, self.roster, h())

    def test_exact_all_fields_are_compared_not_only_ids(self):
        result, _ = resolve(self.selected, self.xw, self.alias, self.roster, h())
        self.assertTrue(compare_exact(result, result.iloc[::-1])[
            "all_player_ids_and_fields_exact"])
        changed = result.copy()
        changed.loc[changed.index[0], "reason"] = "Different"
        with self.assertRaisesRegex(ValueError, "replay changed fields"):
            compare_exact(changed, result)

    def test_changed_player_id_causes_replay_failure(self):
        result, _ = resolve(self.selected, self.xw, self.alias, self.roster, h())
        changed = result.copy()
        changed.loc[changed.index[0], "nba_player_id"] = 999
        with self.assertRaisesRegex(ValueError, "replay changed fields"):
            compare_exact(changed, result)

    def test_missing_reference_metadata_column_fails(self):
        result, _ = resolve(self.selected, self.xw, self.alias, self.roster, h())
        with self.assertRaisesRegex(ValueError, "schema drift"):
            compare_exact(result.drop(columns=["status_severity"]), result)

    def test_duplicate_player_id_same_game_team_rejected(self):
        result, _ = resolve(self.selected, self.xw, self.alias, self.roster, h())
        duplicate = pd.concat([result, result.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "Duplicate final"):
            compare_exact(duplicate, result)

    def test_original_immutable_builder_cannot_be_silently_replaced(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "nba_player_game_at_risk_core_v1.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr(BUILDER_MEMBER, "print('tampered')\n")
            with self.assertRaisesRegex(ValueError, "source SHA-256 changed"):
                immutable_original_helpers(Path(root))


if __name__ == "__main__":
    unittest.main()
