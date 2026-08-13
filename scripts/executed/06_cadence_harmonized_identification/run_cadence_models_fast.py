from pathlib import Path
import time, numpy as np, pandas as pd, statsmodels.api as sm
from scipy.stats import norm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
ROOT=Path('/mnt/data/nba_continue'); OUT=ROOT/'cadence_harmonized_results'
panel=pd.read_csv(OUT/'player_team_game_harmonized_cadence.csv.gz',low_memory=False)
def asbool(s):
 if s.dtype==bool:return s
 return s.astype(str).str.lower().isin({'true','1','1.0'})
def demean_group(A,codes,k):
 # calculate group means columnwise with bincount
 for j in range(A.shape[1]):
  sums=np.bincount(codes,weights=A[:,j],minlength=k)
  cnt=np.bincount(codes,minlength=k)
  A[:,j]-=(sums/cnt)[codes]
 return A
def absorb_fast(A,g1,g2,tol=1e-8,max_iter=160):
 A=np.asarray(A,float).copy(); c1,u1=pd.factorize(g1,sort=False); c2,u2=pd.factorize(g2,sort=False)
 k1=len(u1);k2=len(u2)
 for it in range(max_iter):
  if it<3 or it%5==0: old=A.copy()
  A=demean_group(A,c1,k1); A=demean_group(A,c2,k2)
  if (it<3 or it%5==0) and np.max(np.abs(A-old))<tol: break
 return A,it+1

def fit(tvcol,label,controls=True):
 t=time.time(); d=panel[asbool(panel.at_risk_for_new_onset_harm)].copy()
 for c in ['star_PPP_it','postPPP','announced_tv_primary','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game']:
  d[c]=asbool(d[c]).astype(float)
 d['absence_onset_harm']=asbool(d.absence_onset_harm).astype(float); d['tv_model']=d[tvcol].astype(float)
 d['star_post']=d.star_PPP_it*d.postPPP; d['star_tv']=d.star_PPP_it*d.tv_model; d['post_tv']=d.postPPP*d.tv_model; d['triple']=d.star_PPP_it*d.postPPP*d.tv_model
 d['elo_100']=d.signed_elo_advantage/100.;d['travel_1000']=d.travel_km_since_previous_game/1000.;d['travel_disadv_1000']=d.travel_disadvantage_km/1000.
 d['minutes10_100']=d.minutes_sum_prior_10_roster_games_harm/100.;d['games_before_10']=d.games_played_before_game_harm/10.;d['dist65_10']=d.dist_to_65_before_game_harm/10.
 lower=['star_PPP_it','tv_model','star_post','star_tv','post_tv','triple']
 ctr=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadv_1000','cup_game','minutes10_100','games_before_10','dist65_10'] if controls else []
 terms=lower+ctr; keep=['absence_onset_harm','nba_player_id','game_id','team','season']+terms
 d=d[keep].replace([np.inf,-np.inf],np.nan).dropna().copy(); d['teamseason']=d.team.astype(str)+'|'+d.season.astype(str)
 A,it=absorb_fast(d[['absence_onset_harm']+terms].to_numpy(float),d.nba_player_id,d.teamseason)
 y=A[:,0];X=A[:,1:]; nz=(X*X).sum(0)>1e-12;X=X[:,nz];names=[n for n,k in zip(terms,nz) if k]
 res=sm.OLS(y,X).fit();j=names.index('triple');cov,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0],use_correction=True)
 beta=float(res.params[j]);se=float(np.sqrt(max(cov[j,j],0)));p=float(2*norm.sf(abs(beta/se)))
 out={'definition':label,'controls':'full' if controls else 'none','n':len(d),'estimate_pp':100*beta,'se_pp':100*se,'low_pp':100*(beta-1.96*se),'high_pp':100*(beta+1.96*se),'p':p,'iterations':it,'seconds':time.time()-t}
 print(out,flush=True);return out
rows=[]
for tvcol,label in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
 for controls in [True,False]: rows.append(fit(tvcol,label,controls))
pd.DataFrame(rows).to_csv(OUT/'cadence_harmonized_model_results.csv',index=False)
