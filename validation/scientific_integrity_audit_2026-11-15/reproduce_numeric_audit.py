"""Executed independent audit, not a replacement research estimator.
Uses a separate fixed-effect projection and records numerical diagnostics.
The optional star-rule sensitivity changes only a RAM copy; frozen data stay intact.
"""
from pathlib import Path
import hashlib,gzip,json,io,csv,zipfile,ast
from collections import Counter
import numpy as np,pandas as pd,statsmodels.api as sm
from scipy.stats import norm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
import argparse,sys
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO))
from scripts.data_rebuild.private_source_paths import under_git
parser=argparse.ArgumentParser(description="Read-only independent numerical audit of the accepted corrected cadence panel")
parser.add_argument('--panel',type=Path,required=True)
parser.add_argument('--star-archive',type=Path,required=True)
parser.add_argument('--coding-archive',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--apply-declared-star-rule',action='store_true',help='In-memory sensitivity only; never writes a replacement panel')
args=parser.parse_args()
if args.output.exists() or args.output.is_symlink() or under_git(args.output):raise ValueError('Use a new private output report outside Git')
inputs=[args.panel,args.star_archive,args.coding_archive]
input_hashes={p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in inputs}
if input_hashes[args.star_archive]!='6513069ffc81535edc2af04acbb7550f227fb074ea51241e0e800cebe9f1eb70':raise ValueError('Unexpected historical star archive')
panel=args.panel
with gzip.open(panel,'rb') as f: decoded=hashlib.file_digest(f,'sha256').hexdigest()
assert decoded=='2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67'
d=pd.read_csv(panel,low_memory=False)

sensitivity_changes=None
if args.apply_declared_star_rule:
 with zipfile.ZipFile(args.star_archive) as z:
  n=next(n for n in z.namelist() if Path(n).name=='player_season_star_status_calendar.csv');calendar=pd.read_csv(z.open(n))
 joined=d.merge(calendar[['season','nba_player_id','star_at_opening_night','current_season_all_star','current_all_star_effective_date']],on=['season','nba_player_id'],how='left',validate='many_to_one')
 expected_star=joined.star_at_opening_night|(joined.current_season_all_star & pd.to_datetime(joined.game_date_et).ge(pd.to_datetime(joined.current_all_star_effective_date)))
 wrong=expected_star!=d.star_PPP_it
 sensitivity_changes={'rows':int(wrong.sum()),'risk_rows':int((wrong&d.at_risk_for_new_onset_harm).sum()),'onsets':int((wrong&d.absence_onset_harm).sum())}
 d['star_PPP_it']=expected_star.to_numpy()

report={'scope':'Independent read-only scientific diagnostics on accepted corrected evidence; no source rebuild','decoded_panel_sha256':decoded,'rows':len(d),'games':int(d.game_id.nunique()),'players':int(d.nba_player_id.nunique()),'duplicates':int(d.player_team_game_id.duplicated().sum()),'risk':int(d.at_risk_for_new_onset_harm.sum()),'onsets':int(d.absence_onset_harm.sum())}
g=d.sort_values(['nba_player_id','season','team_norm','team_game_number','tip_utc']).groupby(['nba_player_id','season','team_norm'],sort=False)
prev_abs=g.absence_now_harm.shift(1);con=g.team_game_number.shift(1).eq(d.loc[g.obj.index].team_game_number-1)
s=g.obj;expected=s.report_outcome_observed&con&~prev_abs.fillna(False).astype(bool)
report['independent_risk_rule_mismatches']=int((expected!=s.at_risk_for_new_onset_harm).sum())
report['onset_rule_mismatches']=int((d.absence_onset_harm!=(d.at_risk_for_new_onset_harm&d.absence_now_harm)).sum())
report['post_indicator_mismatches']=int((d.postPPP!=d.season.isin(['2023-24','2024-25','2025-26'])).sum())
snap=pd.to_datetime(d.snapshot_timestamp_utc,utc=True,errors='coerce');tip=pd.to_datetime(d.tip_utc,utc=True)
report['listed_report_rows_at_or_after_tip']=int((snap.notna()&snap.ge(tip)).sum())
report['negative_team_report_lead_rows']=int(d.team_snapshot_minutes_before_tip.lt(0).sum())
report['report_only_rows']=int((~d.from_boxscore_roster).sum())
report['risk_after_previous_missing_report']=int((expected&~g.report_outcome_observed.shift(1).fillna(False).astype(bool)).sum())
report['season_observability']=d.groupby('season').agg(rows=('game_id','size'),report_observed=('report_outcome_observed','sum'),risk=('at_risk_for_new_onset_harm','sum'),onsets=('absence_onset_harm','sum')).reset_index().to_dict('records')
report['raw_eight_cells']=d[d.at_risk_for_new_onset_harm].groupby(['star_PPP_it','postPPP','announced_tv_primary']).agg(at_risk=('game_id','size'),onsets=('absence_onset_harm','sum')).reset_index().to_dict('records')
# Reconstruct dynamic star timing from archived immutable calendar, never from end-season star flags.
with zipfile.ZipFile(args.star_archive) as z:
 n=next(n for n in z.namelist() if Path(n).name=='player_season_star_status_calendar.csv');cal=pd.read_csv(z.open(n))
a=d.merge(cal[['season','nba_player_id','star_at_opening_night','current_season_all_star','current_all_star_effective_date']],on=['season','nba_player_id'],how='left',validate='many_to_one')
star=a.star_at_opening_night.fillna(False).astype(bool)|(a.current_season_all_star.fillna(False).astype(bool)&pd.to_datetime(a.game_date_et).ge(pd.to_datetime(a.current_all_star_effective_date)))
report['dynamic_star_mismatches_vs_versioned_calendar']=int((star!=a.star_PPP_it).sum())
report['missing_star_calendar_rows']=int(a.star_at_opening_night.isna().sum())
# Independent group projections; check orthogonality rather than only iterate-to-iterate movement.
def residualize(A,groups):
 codes=[pd.factorize(g)[0] for g in groups]
 sorters=[np.argsort(c,kind='stable') for c in codes]
 bounds=[np.r_[0,np.flatnonzero(np.diff(c[o]))+1] for c,o in zip(codes,sorters)]
 counts=[np.bincount(c) for c in codes]
 A=A.copy()
 for iteration in range(250):
  for c,o,b,n in zip(codes,sorters,bounds,counts):
   means=np.add.reduceat(A[o],b,axis=0)/n[:,None];A-=means[c]
  maxmean=max(float(np.max(np.abs(np.add.reduceat(A[o],b,axis=0)/n[:,None]))) for o,b,n in zip(sorters,bounds,counts))
  if maxmean<1e-10:return A,iteration+1,maxmean
 raise RuntimeError('Independent FE projection did not converge')
models=[]
for tv,label in [('announced_tv_primary','national_partner'),('tv_harmonized_linear','linear_only')]:
 for controls in [True,False]:
  q=d[d.at_risk_for_new_onset_harm].copy()
  for c in ['star_PPP_it','postPPP','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game']:q[c]=q[c].astype(float)
  q['tv']=q[tv].astype(float);q['starpost']=q.star_PPP_it*q.postPPP;q['startv']=q.star_PPP_it*q.tv;q['posttv']=q.postPPP*q.tv;q['triple']=q.star_PPP_it*q.postPPP*q.tv
  for name,col,factor in [('elo','signed_elo_advantage',100),('travel','travel_km_since_previous_game',1000),('travel_disadv','travel_disadvantage_km',1000),('minutes','minutes_sum_prior_10_roster_games_harm',100),('games','games_played_before_game_harm',10),('dist65','dist_to_65_before_game_harm',10)]:q[name]=q[col]/factor
  terms=['star_PPP_it','tv','starpost','startv','posttv','triple']
  if controls:terms+=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel','absolute_timezone_shift_hours','road_trip_game_number','elo','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadv','cup_game','minutes','games','dist65']
  complete=q[terms].replace([np.inf,-np.inf],np.nan).notna().all(axis=1)
  missing=q.loc[~complete,terms].isna().sum();q=q.loc[complete].copy();q['teamseason']=q.team+'|'+q.season
  A,it,orth=residualize(q[['absence_onset_harm']+terms].to_numpy(float),[q.nba_player_id,q.teamseason]);y=A[:,0];X=A[:,1:]
  nz=(X*X).sum(axis=0)>1e-12;X=X[:,nz];names=[n for n,b in zip(terms,nz) if b];j=names.index('triple')
  fit=sm.OLS(y,X).fit();cov=cov_cluster_2groups(fit,pd.factorize(q.nba_player_id)[0],pd.factorize(q.game_id)[0],use_correction=True)[0];se=np.sqrt(cov[j,j]);beta=fit.params[j]
  result={'definition':label,'controls':'full' if controls else 'none','n':len(q),'estimate_pp':float(100*beta),'se_pp':float(100*se),'p':float(2*norm.sf(abs(beta/se))),'low_pp':float(100*(beta-1.96*se)),'high_pp':float(100*(beta+1.96*se)),'columns':len(names),'rank':int(np.linalg.matrix_rank(X)),'absorption_iterations':it,'maximum_residual_group_mean':orth,'missing_rows_by_term':{k:int(v) for k,v in missing.items() if v}}
  if controls:
   k=names.index('dist65');Z=np.delete(X,k,axis=1); jj=names.index('triple');f=sm.OLS(y,Z).fit();cc=cov_cluster_2groups(f,pd.factorize(q.nba_player_id)[0],pd.factorize(q.game_id)[0],use_correction=True)[0]
   result['drop_redundant_dist65']={'rank':int(np.linalg.matrix_rank(Z)),'estimate_pp':float(100*f.params[jj]),'se_pp':float(100*np.sqrt(cc[jj,jj])),'p':float(2*norm.sf(abs(f.params[jj]/np.sqrt(cc[jj,jj])))),'max_fitted_difference':float(np.max(np.abs(f.fittedvalues-fit.fittedvalues)))}
   result['supplemental_covariance_same_fit']={}
   for name,group in [('player_teamseason',q.teamseason),('player_calendar_date',q.game_date_et)]:
    c=cov_cluster_2groups(fit,pd.factorize(q.nba_player_id)[0],pd.factorize(group)[0],use_correction=True)[0];sdev=np.sqrt(c[j,j]);result['supplemental_covariance_same_fit'][name]={'clusters_2':int(group.nunique()),'se_pp':float(100*sdev),'normal_p':float(2*norm.sf(abs(beta/sdev)))}
  models.append(result)
report['independent_models']=models
report['audit_only_star_reclassification']=sensitivity_changes
# Recalculate human agreement from the submitted source columns, not the scored comparison.
with zipfile.ZipFile(args.coding_archive) as z:
 frames=[{r['spell_id']:r for r in csv.DictReader(io.StringIO(z.read(n).decode('utf-8-sig')))} for n in ['Encoded1.csv','Encoded2.txt']]
 assert frames[0].keys()==frames[1].keys();pairs=[(row['human_class_coder_1'],frames[1][k]['human_class_coder_2']) for k,row in frames[0].items()];m1=Counter(x for x,y in pairs);m2=Counter(y for x,y in pairs);n=len(pairs);obs=sum(a==b for a,b in pairs)/n;pe=sum(m1[k]*m2[k] for k in m1)/n**2
 report['independent_human_agreement']={'n':n,'agree':int(obs*n),'kappa':(obs-pe)/(1-pe),'provenance':json.loads(z.read('coding_provenance.json')),'archive_sha256':hashlib.file_digest((args.coding_archive).open('rb'),'sha256').hexdigest()}
if any(hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=h for p,h in input_hashes.items()):raise RuntimeError('Audit input changed')
report['input_sha256']={k:v for k,v in zip(['compressed_panel','star_archive','coding_archive'],[input_hashes[p] for p in inputs])}
report['inputs_unchanged']=True
report['analysis_panel_modified']=False
args.output.parent.mkdir(parents=True,exist_ok=True)
with args.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'rows':report['rows'],'risk_errors':report['independent_risk_rule_mismatches'],'star_errors':report['dynamic_star_mismatches_vs_versioned_calendar'],'models':[{k:m[k] for k in ['definition','controls','n','estimate_pp','se_pp','p','rank','columns']} for m in models]},indent=2))
