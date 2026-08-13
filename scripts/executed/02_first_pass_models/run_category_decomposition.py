from pathlib import Path
import pandas as pd, numpy as np, statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')
D='/mnt/data/nba_player_game_analysis_ready_v1/player_game_panel_model_at_risk_analysis_ready.csv.gz'
df=pd.read_csv(D,low_memory=False)
def b(s): return s.astype(float) if s.dtype==bool else s.map(lambda x:1.0 if str(x).lower() in {'true','1','1.0'} else 0.0)
bs=['star_PPP_it','postPPP','announced_tv_primary','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game','absence_onset','vague_onset_frozen','specific_onset_frozen','explicit_rest_onset_frozen','other_absence_onset_frozen']
for c in bs: df[c]=b(df[c])
df['star_post']=df.star_PPP_it*df.postPPP; df['star_tv']=df.star_PPP_it*df.announced_tv_primary; df['post_tv']=df.postPPP*df.announced_tv_primary; df['triple']=df.star_PPP_it*df.postPPP*df.announced_tv_primary
df['elo_100']=df.signed_elo_advantage/100; df['travel_1000']=df.travel_km_since_previous_game/1000; df['travel_disadv_1000']=df.travel_disadvantage_km/1000; df['minutes10_100']=df.minutes_sum_prior_10_roster_games/100; df['games_before_10']=df.games_played_before_game/10; df['dist65_10']=df.dist_to_65_before_game/10
terms=['star_PPP_it','announced_tv_primary','star_post','star_tv','post_tv','triple','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadv_1000','cup_game','minutes10_100','games_before_10','dist65_10']
outcomes=['absence_onset','vague_onset_frozen','specific_onset_frozen','explicit_rest_onset_frozen','other_absence_onset_frozen']
keep=outcomes+terms+['nba_player_id','season','game_id']
d=df[keep].replace([np.inf,-np.inf],np.nan).dropna().copy()
A=d[outcomes+terms].to_numpy(float)

def demean(A,g):
 c,u=pd.factorize(g,sort=False); n=len(u); cnt=np.bincount(c,minlength=n).astype(float)
 sums=np.column_stack([np.bincount(c,weights=A[:,j],minlength=n) for j in range(A.shape[1])])
 return A-sums[c]/cnt[c,None]
for it in range(100):
 old=A.copy() if it%5==0 else None
 A=demean(A,d.nba_player_id); A=demean(A,d.season)
 if old is not None:
  delta=np.max(np.abs(A-old))
  if delta<1e-10: break
print('iterations',it+1,'delta',delta)
Y=A[:,:len(outcomes)]; X=A[:,len(outcomes):]
valid=(X*X).sum(0)>1e-12; X=X[:,valid]; names=[n for n,k in zip(terms,valid) if k]
rows=[]; tabs=[]
for yi,yname in enumerate(outcomes):
 res=sm.OLS(Y[:,yi],X).fit()
 cov,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0])
 se=np.sqrt(np.maximum(np.diag(cov),0)); beta=res.params; p=2*norm.sf(np.abs(beta/se))
 tab=pd.DataFrame({'outcome':yname,'term':names,'estimate':beta,'se':se,'p':p,'low':beta-1.96*se,'high':beta+1.96*se})
 tabs.append(tab)
 r=tab[tab.term=='triple'].iloc[0]
 rows.append({'outcome':yname,'n':len(d),'estimate':r.estimate,'se':r.se,'p':r.p,'low':r.low,'high':r.high,'r2':res.rsquared})
out=Path('/mnt/data/_model_run'); out.mkdir(exist_ok=True)
pd.concat(tabs).to_csv(out/'category_models_coefficients.csv',index=False)
pd.DataFrame(rows).to_csv(out/'category_models_focal.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
