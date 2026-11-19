"""Synthetic negative tests for original August source-match/report mapping audit."""
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import pandas as pd

SOURCE=Path(__file__).resolve().parents[1]/"scripts/data_rebuild/audit_august_toronto_source_game_join.py"
spec=importlib.util.spec_from_file_location("august_toronto_source_audit",SOURCE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class AugustPhysicalGameMappingTests(unittest.TestCase):
    def make_archive(self,root,wrong_count=False):
        source=b'selected["matchup_norm"].isin(toronto_fix)\n'
        rows=[]
        canonical=[]
        for match_number,(count,matchup,expected_game) in m.EXPECTED.items():
            if match_number==430:
                original="2021-22|20220202T0030Z|Chicago Bulls@Toronto Raptors"
            elif match_number==784:
                original="2021-22|20220204T0030Z|Miami Heat@Toronto Raptors"
            else:
                original=expected_game
            canonical.append({"season":"2021-22","source_match_number":match_number,"game_id":original})
            if wrong_count and match_number==46:count-=1
            for i in range(count):
                old_game=(m.SOURCE_SWAPS[784] if matchup=="CHI@TOR" else m.SOURCE_SWAPS[430])
                rows.append({"season":"2021-22","source_match_number":match_number,
                             "matchup_norm":matchup,"game_id":old_game,
                             "snapshot_basename":f"source_{match_number}.pdf",
                             "player_name":f"player_{i}"})
        path=root/"original_core.zip"
        with ZipFile(path,"w") as z:
            z.writestr("nba_player_game_at_risk_core_v1/build_selected_report_and_identity_stage.py",source)
            z.writestr("nba_player_game_at_risk_core_v1/selected_report_rows_all.csv",
                       pd.DataFrame(rows).to_csv(index=False))
            z.writestr("nba_player_game_at_risk_core_v1/canonical_game_snapshot_map.csv",
                       pd.DataFrame(canonical).to_csv(index=False))
        return path, hashlib.sha256(source).hexdigest()

    def test_only_unrelated_october_and_april_reports_are_rehomed(self):
        with tempfile.TemporaryDirectory() as temp:
            z,sha=self.make_archive(Path(temp))
            with patch.object(m,"EXPECTED_HISTORICAL_BUILDER_SHA",sha):
                summary, rows=m.audit(z)
            self.assertEqual(summary["four_source_match_rows"],36)
            self.assertEqual(summary["unrelated_october_april_rows_wrongly_attached_to_february"],17)
            moved=rows.loc[rows.changed_game_id]
            self.assertEqual(moved.source_match_number.value_counts().to_dict(),{1172:10,46:7})
            for num,(_,_,game_id) in m.EXPECTED.items():
                self.assertEqual(set(rows.loc[rows.source_match_number.eq(num),"corrected_game_id"]),{game_id})

    def test_unexpected_source_count_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            z,sha=self.make_archive(Path(temp),wrong_count=True)
            with patch.object(m,"EXPECTED_HISTORICAL_BUILDER_SHA",sha):
                with self.assertRaisesRegex(RuntimeError,"Expected 36"):
                    m.audit(z)

    def test_changed_original_builder_hash_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            z,sha=self.make_archive(Path(temp))
            with self.assertRaisesRegex(RuntimeError,"SHA changed"):
                m.audit(z)

if __name__=="__main__":
    unittest.main()
