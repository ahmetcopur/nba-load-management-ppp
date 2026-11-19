"""Synthetic semantic/subprocess tests; never authentic source acceptance."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import numpy as np
import pandas as pd
from scripts.data_rebuild import october_scientific_v2_rules as rules
from scripts.data_rebuild import reproduce_october_scientific_v2 as run
from scripts.data_rebuild.october_scientific_v2_compare import compare
from scripts.data_rebuild import run_october_scientific_v2_suite as secondary
from scripts.data_rebuild import retained_scientific_inputs as retained
from scripts.data_rebuild import scientific_case_checkpoint as checkpoints


class RetainedProfileTests(unittest.TestCase):
    def test_missing_checkpoint_never_substitutes_a_panel(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);out=p/'new'
            self.assertIsNone(checkpoints.reuse_case(p/'old','unused','frozen','legacy',{},out))
            self.assertFalse(out.exists())

    def test_checkpoint_destination_and_scientific_source_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);out=p/'new';out.mkdir()
            with self.assertRaises(FileExistsError):checkpoints.reuse_case(p/'old','unused','frozen','legacy',{},out)
            old=p/'old/frozen__legacy';old.mkdir(parents=True);(old/'case_manifest.json').write_text('{}')
            with patch.object(checkpoints.subprocess,'check_output',return_value=b'changed scientific source'):
                with self.assertRaisesRegex(ValueError,'scientific code differs'):
                    checkpoints.reuse_case(p/'old','original','frozen','legacy',{},p/'out')
            self.assertFalse((p/'out').exists())

    def test_resume_arguments_must_be_paired(self):
        with self.assertRaisesRegex(ValueError,'both reuse'):
            run.build(Path('/retained'),Path('/evidence'),Path('/originals'),Path('/out'),reuse_from=Path('/previous'))

    def test_exact_owner_profile_is_pinned_and_corruption_rejected(self):
        value=retained.verify_profile(run.REPO)
        self.assertEqual(len(value['input_sha256']),21)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=root/retained.PROFILE;p.parent.mkdir(parents=True)
            p.write_text(json.dumps(value)+'\n')
            with self.assertRaisesRegex(ValueError,'profile was changed'):retained.verify_profile(root)

    def test_missing_or_wrong_bundle_never_falls_back(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            with self.assertRaisesRegex(ValueError,'bundle SHA-256 differs'):
                retained.preflight(p/'retained',p/'missing.zip',p/'originals',p/'output')
            self.assertFalse((p/'output').exists())

    def test_earlier_profile_requires_explicit_selection(self):
        args=[Path('/private/retained'),Path('/private/evidence'),Path('/private/archives'),Path('/private/new')]
        for explicit in (False,True):
            with patch.object(run,'preflight',side_effect=ValueError('new-source-gate')) as new, \
                 patch.object(retained,'preflight',side_effect=ValueError('retained-gate')) as old:
                with self.assertRaisesRegex(ValueError,'retained-gate' if explicit else 'new-source-gate'):
                    run.build(*args,retained_intermediates=explicit)
                self.assertEqual(old.call_count,int(explicit));self.assertEqual(new.call_count,int(not explicit))


class EligibilityTests(unittest.TestCase):
    def test_all_eligibility_boundaries(self):
        for opening,selected,date,expected in [
            (True,False,'2025-01-01',True),(True,False,'2025-03-01',True),
            (False,True,'2025-02-16',False),(False,True,'2025-02-17',True),
            (False,True,'2025-02-18',True),(False,False,'2025-02-18',False),
            ('False','False','2025-03-01',False),('true','0','2025-01-01',True),
            (False,False,'2025-01-01',False)]:
            with self.subTest(opening=opening,selected=selected,date=date):
                self.assertEqual(rules.eligible(opening,selected,'2025-02-17',date),expected)

    def test_missing_flags_never_become_truthy(self):
        for v in [None,pd.NA,np.nan,'unknown','',2]:
            with self.subTest(value=str(v)), self.assertRaises(ValueError):
                rules.eligible(False,v,'2025-02-17','2025-03-01')

    def test_missing_date_rules(self):
        self.assertFalse(rules.eligible(False,False,None,'2025-03-01'))
        self.assertTrue(rules.eligible(True,False,None,'2025-03-01'))
        with self.assertRaisesRegex(ValueError,'effective date'):
            rules.eligible(False,True,None,'2025-03-01')
        with self.assertRaisesRegex(ValueError,'game date'):
            rules.eligible(False,False,None,None)

    def calendar(self,root,selected=False):
        p=root/'calendar.csv'
        pd.DataFrame([{'season':'2024-25','nba_player_id':1,'star_at_opening_night':False,
                       'current_season_all_star':selected,'current_all_star_effective_date':'2025-02-17'}]).to_csv(p,index=False)
        return p

    def test_roster_and_report_only_traded_associations_share_rule(self):
        with tempfile.TemporaryDirectory() as temp:
            cal=rules.load_calendar(self.calendar(Path(temp),True))
            f=pd.DataFrame([{'season':'2024-25','nba_player_id':1,'game_date_et':'2025-02-17','team':'A'},
                            {'season':'2024-25','nba_player_id':1,'game_date_et':'2025-02-17','team':'B'}],index=[12,93])
            v=rules.flags_for_frame(f,cal)
            self.assertEqual(v.index.tolist(),[12,93]);self.assertEqual(v.tolist(),[True,True])
            self.assertEqual(rules.star_for_player(cal,'2024-25',1,'2025-02-17'),v.iloc[0])
            # The authoritative calendar can resolve a report-only player even
            # if that player has no corresponding base-panel lookup record.
            self.assertTrue(rules.star_for_player(cal,'2024-25',1,'2025-03-01'))
            with self.assertRaisesRegex(ValueError,'missing'):
                rules.star_for_player(cal,'2024-25',2,'2025-03-01')

    def test_entire_nonstar_season_stays_nonstar(self):
        with tempfile.TemporaryDirectory() as t:
            cal=rules.load_calendar(self.calendar(Path(t)))
            self.assertTrue(all(not rules.star_for_player(cal,'2024-25',1,date)
                                for date in ['2024-10-01','2025-02-17','2025-04-01']))

    def test_duplicate_missing_and_incomplete_calendars_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=self.calendar(root);c=pd.read_csv(p)
            pd.concat([c,c]).to_csv(p,index=False)
            with self.assertRaisesRegex(ValueError,'duplicated'):rules.load_calendar(p)
            c.nba_player_id=pd.NA;c.to_csv(p,index=False)
            with self.assertRaises(ValueError):rules.load_calendar(p)
            p=self.calendar(root);c=pd.read_csv(p);c.current_season_all_star=True;c.current_all_star_effective_date=None;c.to_csv(p,index=False)
            with self.assertRaisesRegex(ValueError,'effective'):rules.load_calendar(p)

    def test_exact_source_patch_does_not_change_original(self):
        original=run.SOURCE.read_bytes();before=hashlib.sha256(original).hexdigest()
        for version in rules.VERSIONS:
            source=rules.render_source(original,version);compile(source,version,'exec')
            if version=='legacy':self.assertEqual(source,original)
            elif rules.VERSIONS[version][0]:
                self.assertNotIn(b"opening or (pd.notna(eff) and gd>=eff)",source)
                self.assertIn(b"_v2_star(_v2_calendar,r.season,r.nba_player_id,row['game_date_et'])",source)
        self.assertEqual(hashlib.sha256(run.SOURCE.read_bytes()).hexdigest(),before)
        with self.assertRaisesRegex(ValueError,'SHA-256'):
            rules.render_source(original+b'\n',run.PRIMARY)

    def test_the_patched_branch_executes_the_declared_rule(self):
        # Execute the EXACT replacement statement extracted from the rendered source.
        source=rules.render_source(run.SOURCE.read_bytes(),run.PRIMARY).decode()
        line=next(l.strip() for l in source.splitlines() if "row['star_PPP_it']=_v2_star" in l)
        with tempfile.TemporaryDirectory() as temp:
            cal=rules.load_calendar(self.calendar(Path(temp)))
            from types import SimpleNamespace
            scope={'row':{'game_date_et':'2025-03-01'},'_v2_star':rules.star_for_player,
                   '_v2_calendar':cal,'r':SimpleNamespace(season='2024-25',nba_player_id=1)}
            exec(compile(line,'actual_versioned_branch','exec'),scope)
            self.assertFalse(scope['row']['star_PPP_it'])


class WorkloadTests(unittest.TestCase):
    def frame(self):
        f=pd.DataFrame([{'nba_player_id':1,'season':'2024-25','game_id':f'g{i}',
                         'tip_utc':f'2025-01-{i+1:02d}T00:00:00Z','game_date_et':f'2025-01-{i+1:02d}',
                         'minutes_played':float(i+10),'played_bool':True,'team':'A'} for i in range(13)])
        f.loc[7,['minutes_played','played_bool']]=[0.,False]
        other=f.iloc[[7]].copy();other['team']='B'
        return pd.concat([f,other],ignore_index=True)

    def test_arbitrary_tied_row_reordering_does_not_change_physical_history(self):
        f=self.frame();g=f.sample(frac=1,random_state=82)
        a=rules.physical_history(f);b=rules.physical_history(g)
        pd.testing.assert_frame_equal(a.sort_index(),b.sort_index())
        self.assertEqual(a.loc[7,rules.WORKLOAD_COLUMNS[1]],a.loc[13,rules.WORKLOAD_COLUMNS[1]])
        self.assertEqual(a.loc[12,rules.WORKLOAD_COLUMNS[1]],sum(f.loc[2:11,'minutes_played']))
        self.assertTrue(pd.api.types.is_integer_dtype(a[rules.WORKLOAD_COLUMNS[0]]))

    def test_current_and_future_minutes_are_not_in_current_history(self):
        f=self.frame();a=rules.physical_history(f)
        f.loc[12,'minutes_played']=90.;b=rules.physical_history(f)
        self.assertEqual(a.loc[12,rules.WORKLOAD_COLUMNS[1]],b.loc[12,rules.WORKLOAD_COLUMNS[1]])
        self.assertTrue(np.isnan(a.loc[0,rules.WORKLOAD_COLUMNS[1]]))

    def test_trade_does_not_reset_player_workload_but_season_does(self):
        f=self.frame();f.loc[10:12,'team']='B';a=rules.physical_history(f)
        self.assertGreater(a.loc[10,rules.WORKLOAD_COLUMNS[0]],0)
        f.loc[12,'season']='2025-26';b=rules.physical_history(f)
        self.assertEqual(b.loc[12,rules.WORKLOAD_COLUMNS[0]],0)

    def test_conflicting_simultaneous_or_missing_chronology_fails(self):
        for col,value in [('tip_utc','2025-01-20T00:00:00Z'),('minutes_played',28.)]:
            f=self.frame();f.loc[13,col]=value
            if col=='minutes_played':f.loc[7,'minutes_played']=10.
            with self.assertRaises(ValueError):rules.physical_history(f)
        f=self.frame();f.loc[1,'tip_utc']=f.loc[0,'tip_utc']
        with self.assertRaisesRegex(ValueError,'Simultaneous'):rules.physical_history(f)
        f=self.frame();f.loc[1,'tip_utc']=None
        with self.assertRaisesRegex(ValueError,'Missing'):rules.physical_history(f)


class CompleteComparisonTests(unittest.TestCase):
    def write(self,p,rows,fields=None):
        with p.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)

    def test_key_join_is_order_independent_and_all_cells_are_compared(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'a.csv',Path(t)/'b.csv';rows=[{'player_team_game_id':'a','star_PPP_it':'True','outcome':'False'},
                                                  {'player_team_game_id':'b','star_PPP_it':'False','outcome':'True'}]
            self.write(a,rows);self.write(b,rows[::-1]);self.assertEqual(compare(a,b,set())['changed_rows'],0)
            rows[0]['star_PPP_it']='False';self.write(b,rows)
            self.assertEqual(compare(a,b,{'star_PPP_it'})['changed_cells'],1)
            rows[0]['outcome']='True';self.write(b,rows)
            with self.assertRaisesRegex(ValueError,'Unauthorized'):compare(a,b,{'star_PPP_it'})

    def test_missing_duplicate_extra_and_schema_changes_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'a.csv',Path(t)/'b.csv';row={'player_team_game_id':'a','risk':'True'}
            self.write(a,[row])
            for rows in [[],[row,row],[{**row,'player_team_game_id':'new'}]]:
                self.write(b,rows,fields=list(row))
                with self.assertRaises(ValueError):compare(a,b,{'risk'})
            self.write(b,[row],fields=list(row)[::-1])
            with self.assertRaisesRegex(ValueError,'schema'):compare(a,b,{'risk'})


class ExecutionTests(unittest.TestCase):
    def test_legacy_hashes_are_still_required_and_cannot_be_scientific_v2(self):
        s={'rows':248778,'games':7230,'seasons':list(range(6)),'decoded_sha256':run.CORRECTED_SHA}
        run.verify_panel_identity(s,'chronology','legacy')
        with self.assertRaisesRegex(ValueError,'Legacy panel cannot'):
            run.verify_panel_identity(s,'chronology',run.PRIMARY)
        s['decoded_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Legacy hash verification'):
            run.verify_panel_identity(s,'chronology','legacy')

    def test_legacy_model_control_cannot_silently_accept_numerical_changes(self):
        refs=json.loads((run.PUBLIC.parent/'verification.json').read_text())['stage6_models']
        rows=[{k:r[k+'_corrected'] for k in ['estimate_pp','p','n','se_pp']} |
              {k:r[k] for k in ['definition','controls']} for r in refs]
        run.verify_legacy_models(rows,'chronology')
        rows[0]['estimate_pp']+=.01
        with self.assertRaisesRegex(ValueError,'numerical control'):run.verify_legacy_models(rows,'chronology')

    def test_actual_subprocess_reads_new_input_and_preserves_hash(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);inp=root/'inputs';inp.mkdir();file=inp/'fresh.csv';file.write_text('new scientific input')
            source=b"from pathlib import Path\nPath('fresh.csv').read_text()\n"
            receipt=run.execute(source,inp,root/'run',{'fresh.csv':run.sha(file)},panel_mode=False)
            self.assertEqual(receipt['actual_opened_inputs'],['fresh.csv'])
            self.assertTrue(receipt['pre_and_post_hashes_equal'])

    def test_missing_reads_failure_and_source_writes_fail_closed(self):
        for source in [b'pass\n',b"from pathlib import Path\nPath('fresh.csv').read_text()\nraise SystemExit(7)\n",
                       b"from pathlib import Path\nPath('fresh.csv').write_text('corrupted')\n"]:
            with self.subTest(source=source),tempfile.TemporaryDirectory() as t:
                root=Path(t);inp=root/'inputs';inp.mkdir();f=inp/'fresh.csv';f.write_text('immutable')
                with self.assertRaises((ValueError,RuntimeError)):
                    run.execute(source,inp,root/'run',{'fresh.csv':run.sha(f)},panel_mode=False)
                self.assertEqual(f.read_text(),'immutable')
                self.assertFalse((root/'run/scientific_version_manifest.json').exists())

    def test_tampered_input_does_not_start_subprocess(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);inp=root/'inputs';inp.mkdir();f=inp/'fresh.csv';f.write_text('tampered')
            with patch.object(run.subprocess,'run',side_effect=AssertionError('must not execute')):
                with self.assertRaisesRegex(ValueError,'SHA-256'):
                    run.execute(b'pass',inp,root/'run',{'fresh.csv':'0'*64},panel_mode=False)

    def test_failed_atomic_manifest_publication_leaves_no_accepted_file(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'scientific_version_manifest.json'
            with self.assertRaises(ValueError):run.save(p,{'status':'pass','bad':float('nan')})
            self.assertFalse(p.exists())
            q=Path(t)/'good.json';run.save(q,{'value':1})
            with self.assertRaises(FileExistsError):run.save(q,{'value':2})
            self.assertEqual(json.loads(q.read_text()),{'value':1})

    def test_missing_retained_inputs_never_restore_archived_rows(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);out=root/'out'
            with self.assertRaisesRegex(FileNotFoundError,'authenticated retained inputs'):
                run.preflight(root/'missing',root/'evidence.zip',root/'archives',out)
            self.assertFalse(out.exists())

    def test_private_paths_reject_overlap_and_symlinks(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);inp=root/'inputs';inp.mkdir()
            with self.assertRaisesRegex(ValueError,'disjoint'):run.fresh_output(inp/'out',[inp])
            (root/'linked').symlink_to(inp,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'symlink'):run.fresh_output(root/'linked/out',[inp])

    def test_all_four_actual_original_models_run_on_new_synthetic_panel(self):
        # Real pinned model source, synthetic CSV. This is not scientific acceptance.
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);rng=np.random.default_rng(922);rows=[]
            for game in range(120):
                for player in range(20):
                    r={'player_team_game_id':f'g{game}|{player}','nba_player_id':player+1,'game_id':f'g{game}',
                       'team':'A' if player%2 else 'B','season':'post' if game>=60 else 'pre',
                       'at_risk_for_new_onset_harm':True,'absence_onset_harm':bool(rng.random()<.09),
                       'star_PPP_it':player<5,'postPPP':game>=60,'announced_tv_primary':game%3==0,
                       'tv_harmonized_linear':float(game%4==0)}
                    for c in ['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days',
                              'opponent_bottom_quartile_pre','opponent_back_to_back','cup_game']:
                        r[c]=bool(rng.integers(0,2))
                    for c in ['travel_km_since_previous_game','absolute_timezone_shift_hours','road_trip_game_number',
                              'signed_elo_advantage','rest_advantage_days','travel_disadvantage_km','minutes_sum_prior_10_roster_games_harm']:
                        r[c]=float(rng.normal())
                    r['games_played_before_game_harm']=game
                    r['dist_to_65_before_game_harm']=65-game;rows.append(r)
            p=root/'synthetic.csv.gz';pd.DataFrame(rows).to_csv(p,index=False)
            report=run.run_models(p,root/'models')
            self.assertEqual(len(report['models']),4)
            self.assertTrue(all(r['n']==2400 for r in report['models']))
            self.assertEqual(report['execution']['actual_opened_inputs'],['cadence_harmonized_results/'+run.PANEL])


class SecondaryTests(unittest.TestCase):
    def test_incomplete_or_changed_primary_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for status in ('pass','incomplete','primary_verified_secondary_pending'):
                (root/'scientific_version_manifest.json').write_text(json.dumps({'status':status}))
                with self.assertRaisesRegex(ValueError,'primary execution'):secondary.authenticate(root)

    def write(self,path,rows):
        pd.DataFrame(rows).to_csv(path,index=False)

    def test_secondary_keyed_comparison_checks_p_values_convergence_samples(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);a=p/'a.csv';b=p/'b.csv'
            rows=[{'model':'x','term':'star_post','estimate_pp':3.,'p':.04,'n':12,'converged':True},
                  {'model':'x','term':'tv','estimate_pp':1.,'p':.4,'n':12,'converged':True}]
            self.write(a,rows);self.write(b,rows[::-1])
            self.assertEqual(secondary.compare_table(a,b,p/'same.jsonl')['changed_rows'],0)
            rows[0].update(p=.09,n=11,converged=False);self.write(b,rows)
            r=secondary.compare_table(a,b,p/'changed.jsonl')
            self.assertEqual(r['changed_rows'],1);self.assertEqual(r['nonconverged_versioned_rows'],[['x','star_post']])
            self.assertIn('"n"',(p/'changed.jsonl').read_text())

    def test_secondary_duplicate_and_unexplained_model_term_changes_fail(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);a=p/'a.csv';b=p/'b.csv';r={'term':'star','estimate_pp':3.}
            self.write(a,[r]);self.write(b,[r,r])
            with self.assertRaisesRegex(ValueError,'Duplicate'):secondary.compare_table(a,b,p/'d.jsonl')
            self.write(b,[{**r,'term':'new'}])
            with self.assertRaisesRegex(ValueError,'term addition'):secondary.compare_table(a,b,p/'e.jsonl')

    def test_collinear_labels_are_reported_rather_than_positional_matching(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);a=p/'a.csv';b=p/'b.csv'
            self.write(a,[{'term':'games_before_10','estimate_pp':1.}])
            self.write(b,[{'term':'dist65_10','estimate_pp':-1.}])
            r=secondary.compare_table(a,b,p/'difference.jsonl')
            self.assertEqual(len(r['collinear_label_swaps']),2)

    def test_explicit_environment_points_actual_subprocess_to_new_panel(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);inp=p/'inputs';inp.mkdir();panel=inp/'panel.csv';panel.write_text('new')
            code=b"import os\nfrom pathlib import Path\nPath(os.environ['NBA_AUDIT_PANEL']).read_text()\n"
            r=run.execute(code,inp,p/'run',{'panel.csv':run.sha(panel)},panel_mode=False,
                          environment={**run.ENV,'NBA_AUDIT_PANEL':str(panel)})
            self.assertEqual(r['actual_opened_inputs'],['panel.csv'])


if __name__=='__main__':unittest.main()
