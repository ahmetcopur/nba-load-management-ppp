"""Pure unit tests; real frozen manuscript identity is checked in CI separately."""
import importlib.util
from pathlib import Path
import unittest

import pandas as pd

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/data_rebuild/rebuild_missing_october_paper_statistics.py"
spec=importlib.util.spec_from_file_location("nba_paper_missing", SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ObservedDurationTests(unittest.TestCase):
    def test_completed_two_game_spell_and_right_censored_onset(self):
        data=pd.DataFrame([
            {"season":"2021-22","team":"A","nba_player_id":"1","team_game_number":1,
             "game_id":"g1","absence_now_harm":True,"report_outcome_observed":True,
             "absence_onset_harm":True,"star_PPP_it":True,"postPPP":False,"player_team_game_id":"a1"},
            {"season":"2021-22","team":"A","nba_player_id":"1","team_game_number":2,
             "game_id":"g2","absence_now_harm":True,"report_outcome_observed":True,
             "absence_onset_harm":False,"star_PPP_it":True,"postPPP":False,"player_team_game_id":"a2"},
            {"season":"2021-22","team":"A","nba_player_id":"1","team_game_number":3,
             "game_id":"g3","absence_now_harm":False,"report_outcome_observed":True,
             "absence_onset_harm":False,"star_PPP_it":True,"postPPP":False,"player_team_game_id":"a3"},
            {"season":"2021-22","team":"B","nba_player_id":"2","team_game_number":10,
             "game_id":"g10","absence_now_harm":True,"report_outcome_observed":True,
             "absence_onset_harm":True,"star_PPP_it":False,"postPPP":False,"player_team_game_id":"b10"},
        ])
        summary, spells=m.spell_lengths(data)
        self.assertEqual(len(spells),2)
        self.assertEqual(spells.completed.tolist(),[True,False])
        self.assertEqual(spells.observed_games.tolist(),[2,1])
        self.assertEqual(summary.onsets.sum(),2)
        self.assertEqual(summary.completed.sum(),1)

    def test_gap_or_unobserved_next_game_censors_spell(self):
        d=pd.DataFrame([
            {"season":"2021-22","team":"A","nba_player_id":"1","team_game_number":1,
             "game_id":"g1","absence_now_harm":True,"report_outcome_observed":True,
             "absence_onset_harm":True,"star_PPP_it":True,"postPPP":False,"player_team_game_id":"a1"},
            {"season":"2021-22","team":"A","nba_player_id":"1","team_game_number":3,
             "game_id":"g3","absence_now_harm":False,"report_outcome_observed":True,
             "absence_onset_harm":False,"star_PPP_it":True,"postPPP":False,"player_team_game_id":"a3"},
        ])
        _,spells=m.spell_lengths(d)
        self.assertFalse(bool(spells.completed.iloc[0]))
        self.assertEqual(spells.observed_games.iloc[0],1)
        d.loc[1,"team_game_number"]=2
        d.loc[1,"report_outcome_observed"]=False
        _,spells=m.spell_lengths(d)
        self.assertFalse(bool(spells.completed.iloc[0]))


class RawRateTests(unittest.TestCase):
    def test_exact_did_of_differences_uses_risk_not_prevalence(self):
        rows=[]
        for star in (False,True):
            for post in (False,True):
                for tv in (False,True):
                    for j in range(10):
                        rows.append({
                            "star_PPP_it":star,"postPPP":post,"announced_tv_primary":tv,
                            "at_risk_for_new_onset_harm":True,
                            "absence_onset_harm":(j<2 if star and post and tv else j<1),
                            "report_outcome_observed":True,"absence_now_harm":False,
                            "can_see_next":True,"onegame":False,"is_home":False,
                            "player_team_game_id":str(len(rows)),
                        })
        onset, prevalence, home, triple=m.descriptive(pd.DataFrame(rows))
        self.assertEqual(len(onset),8)
        self.assertEqual(onset.at_risk.sum(),80)
        self.assertAlmostEqual(triple,10.0)
        self.assertEqual(prevalence.observed.sum(),80)
        self.assertEqual(home.at_risk.sum(),80)

    def test_benchmark_gate_refuses_changed_frozen_counts(self):
        with self.assertRaisesRegex(RuntimeError,"Frozen onset/risk"):
            m.verify_frozen({
                "totals":{"onsets":12729,"risk_rows":180664},
                "duration":[], "raw_triple_difference_pp":1.92,
                "paired_home_onegame_minus_longer":{"n":180087,"estimate_pp":1.664,"se_pp":1.166},
            })


if __name__=="__main__":
    unittest.main()
