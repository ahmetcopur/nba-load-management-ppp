"""Synthetic fail-closed checks for 2025–26 original-manifest selector audit."""
import unittest
from unittest.mock import patch
import pandas as pd

from scripts.data_rebuild.verify_2025_manifest_selector import (
    manifest_part, select_from_inventory, compare_selection, EXPECTED_COUNT
)

PUB1=pd.Timestamp('2025-10-21T18:30:00+00:00')
PUB2=pd.Timestamp('2025-10-21T19:30:00+00:00')


class ManifestSelectorTests(unittest.TestCase):
    def setUp(self):
        self.source=pd.DataFrame([
            {'published':PUB1,'basename':'a.pdf','source':'initial'},
            {'published':PUB2,'basename':'b.pdf','source':'targeted'}])
        self.schedule=pd.DataFrame([
            {'game_id':'FD2025_1','tip_timestamp_utc':'2025-10-21T19:30:00+00:00'},
            {'game_id':'FD2025_2','tip_timestamp_utc':'2025-10-21T20:00:00+00:00'}])

    def test_tie_at_tip_selects_earlier_report(self):
        selected=select_from_inventory(self.source,self.schedule).set_index('game_id')
        self.assertEqual(selected.loc['FD2025_1','basename'],'a.pdf')
        self.assertEqual(selected.loc['FD2025_2','basename'],'b.pdf')
        self.assertEqual(selected.loc['FD2025_1','age_minutes'],60)

    def test_duplicate_source_timestamps_rejected(self):
        other=pd.concat([self.source,self.source.iloc[[0]]],ignore_index=True)
        with self.assertRaisesRegex(ValueError,'Duplicate source PDF'):
            select_from_inventory(other,self.schedule)

    def test_duplicate_games_rejected(self):
        games=self.schedule.copy()
        games.loc[1,'game_id']='FD2025_1'
        with self.assertRaisesRegex(ValueError,'duplicate or missing game IDs'):
            select_from_inventory(self.source,games)

    def test_report_only_at_tip_is_not_pre_tip(self):
        with self.assertRaisesRegex(ValueError,'no saved source PDF'):
            select_from_inventory(self.source.iloc[[1]],self.schedule)

    def test_manifest_filters_missing_pdfs(self):
        raw=pd.DataFrame([
            {'exists':True,'local_path':'x/a.pdf','published_timestamp_utc':'2025-10-21T18:30:00+00:00'},
            {'exists':False,'local_path':'x/b.pdf','published_timestamp_utc':'2025-10-21T19:30:00+00:00'}])
        kept=manifest_part(raw,'published_timestamp_utc','initial')
        self.assertEqual(kept.basename.to_list(),['a.pdf'])

    def test_manifest_rejects_non_pdf(self):
        raw=pd.DataFrame([{'exists':True,'local_path':'not_pdf.txt',
              'published_timestamp_utc':'2025-10-21T18:30:00+00:00'}])
        with self.assertRaisesRegex(ValueError,'non-PDF'):
            manifest_part(raw,'published_timestamp_utc','initial')

    def fixture(self):
        selected=select_from_inventory(self.source,self.schedule)
        reference=pd.DataFrame([{'game_id':r.game_id,'snapshot_basename':r.basename,
          'published_timestamp_utc':r.published.isoformat(),
          'minutes_before_tip':r.age_minutes} for r in selected.itertuples()])
        return selected,reference

    def test_exact_original_snapshot_choices_pass(self):
        selected,reference=self.fixture()
        with patch.dict(EXPECTED_COUNT,{'games':2}):
            output=compare_selection(selected,reference,'full')
        self.assertEqual(output['exact_pdf_matches'],2)

    def test_mismatched_report_name_fails(self):
        selected,reference=self.fixture()
        reference.loc[1,'snapshot_basename']='wrong.pdf'
        with patch.dict(EXPECTED_COUNT,{'games':2}):
            with self.assertRaisesRegex(ValueError,'wrong_pdf_basename'):
                compare_selection(selected,reference,'full')

    def test_mismatched_pretip_age_fails(self):
        selected,reference=self.fixture()
        reference.loc[1,'minutes_before_tip']+=30
        with patch.dict(EXPECTED_COUNT,{'games':2}):
            with self.assertRaisesRegex(ValueError,'wrong_minutes_before_tip'):
                compare_selection(selected,reference,'full')

    def test_game_id_mismatch_fails(self):
        selected,reference=self.fixture()
        reference['game_id']='OTHER'
        with patch.dict(EXPECTED_COUNT,{'games':2}):
            with self.assertRaisesRegex(ValueError,'duplicate or missing game ID'):
                compare_selection(selected,reference,'full')


if __name__=='__main__':
    unittest.main()
