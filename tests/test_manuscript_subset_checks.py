"""Contract tests; synthetic fixtures do not replace authentic private execution."""
from pathlib import Path
import tempfile
import unittest
import pandas as pd
from scripts.data_rebuild import replay_manuscript_subset_checks as run


class ManuscriptSubsetChecks(unittest.TestCase):
    def test_missing_or_changed_panel_never_substitutes_archived_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(ValueError):run.validate_panels(root)
            p=root/'chronology__legacy'/run.core.PANEL;p.parent.mkdir()
            pd.DataFrame({'changed':[1]}).to_csv(p,index=False,compression='gzip')
            with self.assertRaisesRegex(ValueError,'accepted scientific/legacy panel'):
                run.validate_panels(root)

    def test_unknown_network_is_rejected_instead_of_invented(self):
        frame=pd.DataFrame({'network_announced':['unreviewed network'],'announced_tv_primary':[False]})
        with self.assertRaisesRegex(ValueError,'Unexpected historical network'):
            run.broaden_known_tv(frame)

    def test_historical_broad_tv_preserves_typed_false_and_adds_only_nba_tv(self):
        frame=pd.DataFrame({'network_announced':[None,'NBA TV','ESPN',None],
                            'announced_tv_primary':['False','False','True',False]})
        self.assertEqual(run.broaden_known_tv(frame).tolist(),[0.,1.,1.,0.])
        frame.loc[0,'announced_tv_primary']='unclassified'
        with self.assertRaises(ValueError):run.broaden_known_tv(frame)


if __name__=='__main__':unittest.main()
