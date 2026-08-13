from pathlib import Path
import pandas as pd, numpy as np, statsmodels.api as sm
from scipy.sparse import csr_matrix, hstack, csc_matrix
from scipy.sparse.linalg import splu
from scipy.stats import norm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
ROOT=Path('/mnt/data/nba_continue')
AP=ROOT/'analysis_unpack/nba_player_game_analysis_ready_v1/player_game_panel_model_at_risk_analysis_ready.csv.gz'
TP=ROOT/'tv/nba_announced_tv_six_seasons_v1/announced_tv_six_seasons.csv'
df=pd.read_csv(AP,low_memory=False); tv=pd.read_csv(TP,low_memory=False)
def b(s): return s.astype(float) if s.dtype==bool else s.map(lambda x:1.0 if str(x).lower() in {'true','1','1.0'} else 0.0)
for c in ['star_PPP_it','postPPP','announced_tv_primary','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game','absence_onset']: df[c]=b(df[c])
df['home_team']=np.where(df.is_home==1,df.team,df.opponent);df['away_team']=np.where(df.is_home==1,df.opponent,df.team)
keys=['season','game_date_et','home_team','away_team']; tv2=tv[keys+['network_announced']].drop_duplicates(keys);df=df.merge(tv2,on=keys,how='left',validate='many_to_one')
old={'ABC','ESPN','ABC/ESPN','ABC|ESPN','TNT'};new={'ABC','ESPN','ABC/ESPN','ABC|ESPN','NBC/Peacock'}
df['tv_harmonized_linear']=np.where(df.season=='2025-26',df.network_announced.fillna('').isin(new),df.network_announced.fillna('').isin(old)).astype(float)
df['elo_100']=df.signed_elo_advantage/100;df['travel_1000']=df.travel_km_since_previous_game/1000;df['travel_disadv_1000']=df.travel_disadvantage_km/1000;df['minutes10_100']=df.minutes_sum_prior_10_roster_games/100;df['games_before_10']=df.games_played_before_game/10;df['dist65_10']=df.dist_to_65_before_game/10
controls=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadv_1000','cup_game','minutes10_100','games_before_10','dist65_10']

def prepare(tvcol):
 d=df.copy();d['tv_model']=d[tvcol];d['star_post']=d.star_PPP_it*d.postPPP;d['star_tv']=d.star_PPP_it*d.tv_model;d['post_tv']=d.postPPP*d.tv_model;d['triple']=d.star_PPP_it*d.postPPP*d.tv_model
 terms=['star_PPP_it','tv_model','star_post','star_tv','post_tv','triple']+controls
 keep=['absence_onset','nba_player_id','game_id','team','season','game_date_et']+terms
 d=d[keep].replace([np.inf,-np.inf],np.nan).dropna().copy();d['teamseason']=d.team.astype(str)+'|'+d.season.astype(str)
 return d,terms

def build_D(d):
 n=len(d); pc,pu=pd.factorize(d.nba_player_id,sort=False); tc,tu=pd.factorize(d.teamseason,sort=False)
 npg=len(pu); nt=len(tu)
 # player centered time in years
 dates=pd.to_datetime(d.game_date_et);t=(dates-dates.min()).dt.total_seconds().to_numpy()/86400/365.25
 counts=np.bincount(pc,minlength=npg);tmean=np.bincount(pc,weights=t,minlength=npg)/counts;tcen=t-tmean[pc]
 G=csr_matrix((np.ones(n),(np.arange(n),pc)),shape=(n,npg))
 H=csr_matrix((tcen,(np.arange(n),pc)),shape=(n,npg))
 # Drop one team-season dummy to remove global intercept dependency with player intercepts.
 mask=tc>0
 T=csr_matrix((np.ones(mask.sum()),(np.where(mask)[0],tc[mask]-1)),shape=(n,nt-1))
 D=hstack([G,H,T],format='csc')
 return D

def fit(tvcol,label):
 d,terms=prepare(tvcol);A=d[['absence_onset']+terms].to_numpy(float);D=build_D(d)
 # Solve normal equations once for all RHS. Tiny ridge only for numerical stability; scale is negligible vs counts.
 M=(D.T@D).tocsc(); ridge=1e-10
 M=M + ridge*csc_matrix(np.eye(M.shape[0]))
 lu=splu(M)
 coef=lu.solve(np.asarray(D.T@A))
 R=A-D@coef
 y=np.asarray(R[:,0]).ravel();X=np.asarray(R[:,1:])
 keep=(X*X).sum(0)>1e-12;X=X[:,keep];names=[x for x,k in zip(terms,keep) if k]
 res=sm.OLS(y,X).fit();j=names.index('triple');cov,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0],use_correction=True)
 se=np.sqrt(max(cov[j,j],0));bt=res.params[j];p=2*norm.sf(abs(bt/se));return {'definition':label,'n':len(d),'estimate_pp':100*bt,'se_pp':100*se,'low_pp':100*(bt-1.96*se),'high_pp':100*(bt+1.96*se),'p':p,'fe_columns':D.shape[1],'ridge':ridge}
rows=[fit('announced_tv_primary','legacy_primary'),fit('tv_harmonized_linear','harmonized_linear')]
out=ROOT/'identification_stage2_results/player_linear_trends_sparse_exact.csv';pd.DataFrame(rows).to_csv(out,index=False);print(pd.DataFrame(rows).to_string(index=False))
