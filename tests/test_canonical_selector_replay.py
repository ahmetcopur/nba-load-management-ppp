"""Synthetic fail-closed tests. Real ZIP replay is a separate private-input gate."""
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import pandas as pd

from scripts.data_rebuild.verify_canonical_selector_replay import (
    compare_records, check_metrics, original_builder, member_bytes
)


class OriginalSelectorReplayTests(unittest.TestCase):
    FIELDS=frozenset({'published_timestamp_utc','minutes_before_tip'})

    def setUp(self):
        self.orig=pd.DataFrame([
            {'game_id':'G1','published_timestamp_utc':'2020-12-23T00:00:00+00:00',
             'minutes_before_tip':60,'listed_teams':2},
            {'game_id':'G2','published_timestamp_utc':'2020-12-24T00:00:00+00:00',
             'minutes_before_tip':30,'listed_teams':1}
        ])

    def compare(self,candidate):
        return compare_records(candidate,self.orig,['game_id'],self.FIELDS,2)

    def test_exact_rows_out_of_order_pass(self):
        self.assertEqual(self.compare(self.orig.iloc[::-1])['differences'],0)

    def test_selection_timestamp_change_fails(self):
        candidate=self.orig.copy()
        candidate.loc[0,'published_timestamp_utc']='2020-12-23T00:30:00+00:00'
        with self.assertRaisesRegex(ValueError,'published_timestamp_utc'):
            self.compare(candidate)

    def test_game_id_mismatch_fails(self):
        candidate=self.orig.copy()
        candidate.loc[1,'game_id']='G_OTHER'
        with self.assertRaisesRegex(ValueError,'identity'):
            self.compare(candidate)

    def test_duplicate_game_id_fails(self):
        candidate=self.orig.copy()
        candidate.loc[1,'game_id']='G1'
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            self.compare(candidate)

    def test_non_scientific_reference_field_change_also_fails(self):
        candidate=self.orig.copy()
        candidate.loc[1,'listed_teams']=0
        with self.assertRaisesRegex(ValueError,'listed_teams'):
            self.compare(candidate)

    def test_missing_scientific_column_fails(self):
        candidate=self.orig.drop(columns=['minutes_before_tip'])
        with self.assertRaisesRegex(ValueError,'missing scientific'):
            self.compare(candidate)

    def test_missing_non_scientific_reference_column_fails(self):
        candidate=self.orig.drop(columns=['listed_teams'])
        with self.assertRaisesRegex(ValueError,'output schema differs'):
            self.compare(candidate)

    def test_row_count_drift_fails(self):
        with self.assertRaisesRegex(ValueError,'Unexpected'):
            self.compare(self.orig.head(1))

    def test_original_builder_source_tamper_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'canon.zip'
            with ZipFile(path,'w') as z:
                z.writestr(
                    'nba_canonical_snapshot_selector_v1/build_canonical_snapshot_selector_v1.py',
                    b'def build_season(*args): return (None,None,None)\n')
            with self.assertRaisesRegex(ValueError,'differs from pinned immutable original'):
                original_builder(path)

    def test_missing_zip_member_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'source.zip'
            with ZipFile(path,'w') as z:
                z.writestr('not-selected.csv','a\n1\n')
            with self.assertRaisesRegex(ValueError,'Expected exactly one ZIP member'):
                member_bytes(path,'selected.csv')

    def test_metric_value_change_fails(self):
        original={k:10 for k in [
            'games','games_with_pre_tip_pdf','pre_tip_pdf_pct','team_games',
            'usable_team_games','usable_team_game_pct','games_both_teams_usable',
            'both_teams_usable_pct','not_yet_submitted_team_games',
            'inferred_clean_team_games','median_minutes_before_tip',
            'within_30m_games','within_30m_pct']}
        self.assertEqual(check_metrics(original,pd.Series(original))['differences'],0)
        original['games']=11
        with self.assertRaisesRegex(ValueError,'metrics drift'):
            check_metrics(original,pd.Series(dict.fromkeys(original,10)))


if __name__=='__main__':
    unittest.main()
