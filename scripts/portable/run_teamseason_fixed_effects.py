from pathlib import Path
import pandas as pd, numpy as np, statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')
REPO_ROOT = Path(__file__).resolve().parents[2]

D = (
    REPO_ROOT
    / "data_final"
    / "player_game_panel_model_at_risk_analysis_ready.csv.gz"
)

OUT = REPO_ROOT / "results" / "portable_teamseason_fe"
OUT.mkdir(parents=True, exist_ok=True)
df=pd.read_csv(D,low_memory=False)
def b(s): return s.astype(float) if s.dtype==bool else s.map(lambda x:1.0 if str(x).lower() in {'true','1','1.0'} else 0.0)
for c in ['star_PPP_it','postPPP','announced_tv_primary','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game','absence_onset','vague_onset_frozen','specific_onset_frozen']:
 df[c]=b(df[c])
df['star_post']=df.star_PPP_it*df.postPPP;df['star_tv']=df.star_PPP_it*df.announced_tv_primary;df['post_tv']=df.postPPP*df.announced_tv_primary;df['triple']=df.star_PPP_it*df.postPPP*df.announced_tv_primary
df['elo_100']=df.signed_elo_advantage/100;df['travel_1000']=df.travel_km_since_previous_game/1000;df['travel_disadv_1000']=df.travel_disadvantage_km/1000;df['minutes10_100']=df.minutes_sum_prior_10_roster_games/100;df['games_before_10']=df.games_played_before_game/10;df['dist65_10']=df.dist_to_65_before_game/10
terms=['star_PPP_it','announced_tv_primary','star_post','star_tv','post_tv','triple','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadv_1000','cup_game','minutes10_100','games_before_10']

def demean(A,g):
 c,u=pd.factorize(g,sort=False); cnt=np.bincount(c,minlength=len(u)).astype(float)
 sums=np.column_stack([np.bincount(c,weights=A[:,j],minlength=len(u)) for j in range(A.shape[1])])
 return A-sums[c]/cnt[c,None]

def fit(data,outcome):
 d=data[[outcome]+terms+['nba_player_id','team','season','game_id']].replace([np.inf,-np.inf],np.nan).dropna().copy()
 A=d[[outcome]+terms].to_numpy(float); ts=d.team.astype(str)+'|'+d.season.astype(str)
 delta=None
 for it in range(300):
  old=A.copy() if it%5==0 else None
  A=demean(A,d.nba_player_id); A=demean(A,ts)
  if old is not None:
   delta=np.max(np.abs(A-old))
   if delta<1e-10: break
 y=A[:,0];X=A[:,1:]; keep=(X*X).sum(0)>1e-12; X=X[:,keep]; names=[n for n,k in zip(terms,keep) if k]
 res=sm.OLS(y,X).fit(); cov,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0]);se=np.sqrt(np.maximum(np.diag(cov),0)); beta=res.params;p=2*norm.sf(abs(beta/se))
 tab=pd.DataFrame({'term':names,'estimate':beta,'se':se,'p':p,'low':beta-1.96*se,'high':beta+1.96*se}); r=tab[tab.term=='triple'].iloc[0]
 return {'outcome':outcome,'n':len(d),'estimate':r.estimate,'se':r.se,'p':r.p,'low':r.low,'high':r.high,'r2':res.rsquared,'iterations':it+1,'delta':delta},tab
rows=[];tabs=[]
r,t=fit(df,'absence_onset');rows.append(r);t.insert(0,'outcome','absence_onset');tabs.append(t)
inj=df[(df.vague_onset_frozen==1)|(df.specific_onset_frozen==1)].copy();inj['vague_conditional']=inj.vague_onset_frozen
r,t=fit(inj,'vague_conditional');rows.append(r);t.insert(0,'outcome','vague_conditional');tabs.append(t)
out=OUT;pd.DataFrame(rows).to_csv(out/'teamseason_fe_focal.csv',index=False);pd.concat(tabs).to_csv(out/'teamseason_fe_coefficients.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
