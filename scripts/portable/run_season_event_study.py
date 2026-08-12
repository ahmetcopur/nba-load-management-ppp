from pathlib import Path
import pandas as pd,numpy as np,statsmodels.api as sm
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

OUT = REPO_ROOT / "results" / "portable_season_event_study"
OUT.mkdir(parents=True, exist_ok=True)
df=pd.read_csv(D,low_memory=False)
def b(s):return s.astype(float) if s.dtype==bool else s.map(lambda x:1.0 if str(x).lower() in {'true','1','1.0'} else 0.0)
for c in ['star_PPP_it','announced_tv_primary','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game','absence_onset']:
 df[c]=b(df[c])
df['star_tv']=df.star_PPP_it*df.announced_tv_primary
df['elo_100']=df.signed_elo_advantage/100;df['travel_1000']=df.travel_km_since_previous_game/1000;df['travel_disadv_1000']=df.travel_disadvantage_km/1000;df['minutes10_100']=df.minutes_sum_prior_10_roster_games/100;df['games_before_10']=df.games_played_before_game/10;df['dist65_10']=df.dist_to_65_before_game/10
base='2022-23'; seasons=['2020-21','2021-22','2023-24','2024-25','2025-26']
terms=['star_PPP_it','announced_tv_primary','star_tv']
for s in seasons:
 d=(df.season==s).astype(float);df[f'star_season_{s}']=df.star_PPP_it*d;df[f'tv_season_{s}']=df.announced_tv_primary*d;df[f'startv_season_{s}']=df.star_tv*d
 terms += [f'star_season_{s}',f'tv_season_{s}',f'startv_season_{s}']
controls=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadv_1000','cup_game','minutes10_100','games_before_10']
terms+=controls
keep=['absence_onset','nba_player_id','season','game_id']+terms
d=df[keep].replace([np.inf,-np.inf],np.nan).dropna().copy();A=d[['absence_onset']+terms].to_numpy(float)
def demean(A,g):
 c,u=pd.factorize(g,sort=False);cnt=np.bincount(c,minlength=len(u)).astype(float);sums=np.column_stack([np.bincount(c,weights=A[:,j],minlength=len(u)) for j in range(A.shape[1])]);return A-sums[c]/cnt[c,None]
for it in range(100):
 old=A.copy() if it%5==0 else None;A=demean(A,d.nba_player_id);A=demean(A,d.season)
 if old is not None and np.max(abs(A-old))<1e-10:break
y=A[:,0];X=A[:,1:];valid=(X*X).sum(0)>1e-12;X=X[:,valid];names=[n for n,k in zip(terms,valid) if k]
res=sm.OLS(y,X).fit();cov,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0]);se=np.sqrt(np.maximum(np.diag(cov),0));beta=res.params;p=2*norm.sf(abs(beta/se));tab=pd.DataFrame({'term':names,'estimate':beta,'se':se,'p':p,'low':beta-1.96*se,'high':beta+1.96*se})
# Base season star-TV differential is star_tv coefficient. Event differences are interaction coefficients relative to base.
rows=[{'season':base,'relative_to_2022_23':0.0,'se':0.0,'low':0.0,'high':0.0,'p':np.nan,'reference':True}]
for s in seasons:
 r=tab[tab.term==f'startv_season_{s}'].iloc[0];rows.append({'season':s,'relative_to_2022_23':r.estimate,'se':r.se,'low':r.low,'high':r.high,'p':r.p,'reference':False})
event=pd.DataFrame(rows);order=['2020-21','2021-22','2022-23','2023-24','2024-25','2025-26'];event['order']=event.season.map({s:i for i,s in enumerate(order)});event=event.sort_values('order')
out=OUT;event.to_csv(out/'season_event_study_absence.csv',index=False);tab.to_csv(out/'season_event_study_all_coefficients.csv',index=False)
print(event.to_string(index=False))
