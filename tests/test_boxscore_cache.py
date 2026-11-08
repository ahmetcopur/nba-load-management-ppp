"""Negative tests for Level-C cached NBA JSON and historical roster verification."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/data_rebuild/verify_boxscore_cache.py"
spec = importlib.util.spec_from_file_location("boxscore_cache_verifier", SCRIPT)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


def payload(game_id="0022000001"):
    return {
        "game": {
            "gameId": game_id, "gameTimeUTC": "2021-01-01T00:00:00Z",
            "homeTeam": {"teamId": 1610612737, "players": []},
            "awayTeam": {"teamId": 1610612738, "players": []},
        }
    }


def fixture(tmp, bad=False):
    root = Path(tmp)
    v1 = root / "v1"
    folder = v1 / "raw_json" / "2020_21"
    folder.mkdir(parents=True)
    file = folder / "boxscore_0022000001.json"
    file.write_text(json.dumps(payload("0022000002" if bad else "0022000001")))
    (v1 / "download_log.csv").write_text(
        "status,bytes,endpoint_name,raw_json_path\n"
        f"ok_network,{file.stat().st_size},nba_mediaops_s3,"
        "/old/raw_json/2020_21/boxscore_0022000001.json\n")
    discovery = root / "v2" / "raw_json_discovery"
    discovery.mkdir(parents=True)
    return v1, discovery


class RawCacheTests(unittest.TestCase):
    def test_valid_json_has_hash_and_log_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            v1, discovery = fixture(d)
            data = verify.hash_cache({"v1_raw_json": v1 / "raw_json",
                                      "v2_discovery": discovery}, v1 / "download_log.csv")
            self.assertEqual(len(data), 1)
            self.assertTrue(bool(data.name_matches_payload.iloc[0]))
            self.assertTrue(bool(data.season_matches_payload.iloc[0]))
            self.assertEqual(data.bytes.iloc[0], data.logged_bytes.iloc[0])
            self.assertEqual(len(data.sha256.iloc[0]), 64)
            self.assertEqual(verify.cache_stats(data, True)["distinct_payload_game_ids"], 1)

    def test_filename_mismatch_rejected_by_cache_stats(self):
        with tempfile.TemporaryDirectory() as d:
            v1, discovery = fixture(d, bad=True)
            data = verify.hash_cache({"v1_raw_json": v1 / "raw_json",
                                      "v2_discovery": discovery}, v1 / "download_log.csv")
            with self.assertRaisesRegex(RuntimeError, "mismatches"):
                verify.cache_stats(data, True)

    def test_missing_team_structure_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            v1, discovery = fixture(d)
            file = next((v1 / "raw_json").rglob("boxscore_*.json"))
            file.write_text(json.dumps({"game": {"gameId": "0022000001",
                                                 "gameTimeUTC": "2021-01-01T00:00:00Z"}}))
            with self.assertRaisesRegex(ValueError, "invalid homeTeam"):
                verify.hash_cache({"v1_raw_json": v1 / "raw_json",
                                   "v2_discovery": discovery}, v1 / "download_log.csv")

    def test_duplicate_payload_ids_across_sources_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            v1, discovery = fixture(d)
            dest = discovery / "2020_21"
            dest.mkdir()
            (dest / "boxscore_0022000001.json").write_text(json.dumps(payload()))
            data = verify.hash_cache({"v1_raw_json": v1 / "raw_json",
                                      "v2_discovery": discovery}, v1 / "download_log.csv")
            with self.assertRaisesRegex(RuntimeError, "duplicate"):
                verify.cache_stats(data, True)

    def test_7230_required_for_full_mode(self):
        with tempfile.TemporaryDirectory() as d:
            v1, discovery = fixture(d)
            data = verify.hash_cache({"v1_raw_json": v1 / "raw_json",
                                      "v2_discovery": discovery}, v1 / "download_log.csv")
            with self.assertRaisesRegex(RuntimeError, "7,230"):
                verify.cache_stats(data, False)

    def test_logged_size_mismatch_detected(self):
        with tempfile.TemporaryDirectory() as d:
            v1, discovery = fixture(d)
            text = (v1 / "download_log.csv").read_text().replace(
                ",nba_mediaops_s3,", ",nba_mediaops_s3,")
            lines = text.splitlines()
            parts = lines[1].split(",")
            parts[1] = "5"
            lines[1] = ",".join(parts)
            (v1 / "download_log.csv").write_text("\n".join(lines) + "\n")
            data = verify.hash_cache({"v1_raw_json": v1 / "raw_json",
                                      "v2_discovery": discovery}, v1 / "download_log.csv")
            with self.assertRaisesRegex(RuntimeError, "mismatches"):
                verify.cache_stats(data, True)


class ComparisonTests(unittest.TestCase):
    def test_duplicate_roster_key_is_not_merged_as_many_to_many(self):
        frame = pd.DataFrame([
            {"game_id": "g1", "team": "A", "nba_player_id": "2"},
            {"game_id": "g1", "team": "A", "nba_player_id": "2"},
        ])
        with self.assertRaisesRegex(ValueError, "duplicate keys"):
            verify.unique_key_table(frame, ["game_id", "team", "nba_player_id"], "test")

    def test_missing_numeric_is_not_silently_equal_to_bad_text(self):
        left = pd.Series(["", "4", "bad", "3"])
        right = pd.Series(["", "4.0", "", "3.1"])
        self.assertEqual(verify.numeric_disagreement(left, right).tolist(),
                         [False, False, True, True])

    def test_actual_archive_csv_comparison_rejects_missing_or_changed_cells(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            output = root / "output"
            output.mkdir()
            archived = root / "archive.zip"
            with zipfile.ZipFile(archived, "w") as z:
                for name, keys in verify.OUTPUTS.items():
                    row = {key: "g1" if key == "game_id" else "A" for key in keys}
                    row["extra"] = "original"
                    csv = pd.DataFrame([row]).to_csv(index=False)
                    z.writestr("v2/" + name, csv)
                    (output / name).write_text(csv)
            good = verify.compare_with_archive(output, archived, False)
            self.assertTrue(all(not x["differing_cells"] for x in good.values()))
            bad = pd.read_csv(output / "game_roster_players.csv", dtype=str)
            bad.loc[0, "extra"] = "tampered"
            bad.to_csv(output / "game_roster_players.csv", index=False)
            diff = verify.compare_with_archive(output, archived, False)
            self.assertEqual(diff["game_roster_players.csv"]["differing_cells"]["extra"], 1)

    def test_repair_exit_two_only_allowed_for_partial_with_complete_sample(self):
        qa = {"valid_unique_official_boxscores_available": 48,
              "matched_fixture_games": 48, "unused_official_boxscores": 0,
              "player_rows": 1615, "team_game_rows": 96,
              "requested_fixture_games": 7230, "complete": False}
        cache = {"distinct_payload_game_ids": 48}
        verify.check_repair_qa(qa, cache, True, 2)
        with self.assertRaisesRegex(RuntimeError, "all 7,230"):
            verify.check_repair_qa(qa, cache, False, 2)
        qa["matched_fixture_games"] = 47
        with self.assertRaisesRegex(RuntimeError, "did not match every"):
            verify.check_repair_qa(qa, cache, True, 2)


if __name__ == "__main__":
    unittest.main()
