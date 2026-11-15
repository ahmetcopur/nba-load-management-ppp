"""Scientific aggregate/figure input validation; no private data in CI."""
from pathlib import Path
import tempfile
import unittest
import pandas as pd
from scripts.data_rebuild.run_october_scientific_v2_paper_impact import rate_cells
from scripts.data_rebuild.scientific_case_checkpoint import check_reported_models


class ScientificAggregateTests(unittest.TestCase):
    def rows(self):
        return [{'star_PPP_it':s,'postPPP':p,'is_home':h,'at_risk':100,
                 'onegame_onsets':10+int(s)+int(p)+int(h),
                 'onegame_rate_pct':10.+int(s)+int(p)+int(h)}
                for s in (False,True) for p in (False,True) for h in (False,True)]

    def test_all_eight_real_groups_required_and_false_strings_decode_correctly(self):
        rows=self.rows();rows[0]['star_PPP_it']='False'
        result=rate_cells(rows,'is_home','onegame_onsets','at_risk','onegame_rate_pct')
        self.assertEqual(result.loc[(False,False,False),'onegame_rate_pct'],10.)
        for changed in (rows[:-1],rows+[rows[0]]):
            with self.assertRaisesRegex(ValueError,'eight-cell'):
                rate_cells(changed,'is_home','onegame_onsets','at_risk','onegame_rate_pct')

    def test_contradictory_denominators_and_rates_rejected(self):
        for field,value in [('at_risk',0),('onegame_onsets',101),('onegame_rate_pct',88.)]:
            rows=self.rows();rows[0][field]=value
            with self.assertRaises(ValueError):rate_cells(rows,'is_home','onegame_onsets','at_risk','onegame_rate_pct')

    def test_changed_model_values_in_manifest_cannot_replace_actual_results(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'models.csv';pd.DataFrame([{'definition':'primary','n':100,'estimate_pp':2.5}]).to_csv(path,index=False)
            values=pd.read_csv(path).to_dict('records');check_reported_models(path,values)
            values[0]['estimate_pp']=9.
            with self.assertRaisesRegex(ValueError,'actual CSV'):check_reported_models(path,values)


if __name__=='__main__':unittest.main()
