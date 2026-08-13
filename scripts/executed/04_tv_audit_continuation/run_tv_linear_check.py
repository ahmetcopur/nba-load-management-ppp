from pathlib import Path
import pandas as pd, numpy as np, statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from scipy.stats import norm
from scipy.sparse import csr_matrix
import warnings
warnings.filterwarnings('ignore')
AP='/mnt/data/nba_continue/analysis/nba_player_game_analysis_ready_v1/player_game_panel_model_at_risk_analysis_ready.csv.gz'
TP='/mnt/data/nba_continue/tv/nba_announced_tv_six_seasons_v1/announced_tv_six_seasons.csv'
df=pd.read_csv(AP,low_memory=False)
tv=pd.read_csv(TP,low_memory=False)
def b(s):
    if s.dtype==bool:return s.astype(float)
    return s.map(lambda x:1.0 if str(x).lower() in {'true','1','1.0'} else 0.0)
for c in ['star_PPP_it','postPPP','announced_tv_primary','announced_nba_tv','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game','absence_onset']:
    df[c]=b(df[c])
df['home_team']=np.where(df.is_home==1,df.team,df.opponent);df['away_team']=np.where(df.is_home==1,df.opponent,df.team)
keys=['season','game_date_et','home_team','away_team']
tv2=tv[keys+['network_announced','announced_tv_status']].drop_duplicates(keys)
df=df.merge(tv2,on=keys,how='left',validate='many_to_one');assert df.announced_tv_status.notna().all()
df['tv_narrow_disney']=df.network_announced.fillna('').isin({'ABC','ESPN','ABC/ESPN','ABC|ESPN'}).astype(float)
old_linear={'ABC','ESPN','ABC/ESPN','ABC|ESPN','TNT'}
new_linear={'ABC','ESPN','ABC/ESPN','ABC|ESPN','NBC/Peacock'}
df['tv_harmonized_linear']=np.where(df.season=='2025-26',df.network_announced.fillna('').isin(new_linear),df.network_announced.fillna('').isin(old_linear)).astype(float)
df['tv_primary_plus_nbatv']=((df.announced_tv_primary==1)|(df.announced_nba_tv==1)).astype(float)
df['star_post']=df.star_PPP_it*df.postPPP
df['elo_100']=df.signed_elo_advantage/100;df['travel_1000']=df.travel_km_since_previous_game/1000;df['travel_disadv_1000']=df.travel_disadvantage_km/1000;df['minutes10_100']=df.minutes_sum_prior_10_roster_games/100;df['games_before_10']=df.games_played_before_game/10;df['dist65_10']=df.dist_to_65_before_game/10
controls=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadv_1000','cup_game','minutes10_100','games_before_10','dist65_10']

def projector(groups):
    codes, uniques=pd.factorize(groups,sort=False)
    n=len(codes); k=len(uniques)
    G=csr_matrix((np.ones(n),(np.arange(n),codes)),shape=(n,k))
    counts=np.asarray(G.sum(axis=0)).ravel()
    return G,counts

def absorb(A,g1,g2,tol=1e-10,max_iter=100):
    G1,c1=projector(g1);G2,c2=projector(g2)
    for it in range(max_iter):
        old=A.copy() if it<3 or it%5==0 else None
        A-=G1@((G1.T@A)/c1[:,None])
        A-=G2@((G2.T@A)/c2[:,None])
        if old is not None and np.max(np.abs(A-old))<tol:break
    return A,it+1

def fit(data,tv_col,fe2,label):
    d=data.copy(); d['tv_model']=d[tv_col]; d['star_tv_m']=d.star_PPP_it*d.tv_model;d['post_tv_m']=d.postPPP*d.tv_model;d['triple_m']=d.star_PPP_it*d.postPPP*d.tv_model
    terms=['star_PPP_it','tv_model','star_post','star_tv_m','post_tv_m','triple_m']+controls
    d=d[['absence_onset','nba_player_id','game_id','team','season']+terms].replace([np.inf,-np.inf],np.nan).dropna()
    A=d[['absence_onset']+terms].to_numpy(float)
    g2=d.season if fe2=='season' else d.team.astype(str)+'|'+d.season.astype(str)
    A,it=absorb(A,d.nba_player_id,g2)
    y=A[:,0];X=A[:,1:];keep=(X*X).sum(0)>1e-12;X=X[:,keep];names=[x for x,k in zip(terms,keep) if k]
    res=sm.OLS(y,X).fit()
    cov,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0],use_correction=True)
    se=np.sqrt(np.maximum(np.diag(cov),0));beta=res.params;p=2*norm.sf(np.abs(beta/se));lo=beta-1.96*se;hi=beta+1.96*se
    j=names.index('triple_m')
    return {'label':label,'tv_col':tv_col,'fe2':fe2,'n':len(d),'games':d.game_id.nunique(),'estimate_pp':100*beta[j],'se_pp':100*se[j],'low_pp':100*lo[j],'high_pp':100*hi[j],'p':p[j],'iterations':it}

# harmonized linear checks
source=tv.copy(); old_linear={'ABC','ESPN','ABC/ESPN','ABC|ESPN','TNT'}; new_linear={'ABC','ESPN','ABC/ESPN','ABC|ESPN','NBC/Peacock'}
source['harmonized_linear']=np.where(source.season=='2025-26',source.network_announced.fillna('').isin(new_linear),source.network_announced.fillna('').isin(old_linear)).astype(int)
print(source.groupby('season')['harmonized_linear'].sum())
results=[]
results.append(fit(df,'tv_harmonized_linear','season','Harmonized linear national, full six seasons'))
results.append(fit(df,'tv_harmonized_linear','teamseason','Harmonized linear national, team-season FE'))
print(pd.DataFrame(results).to_string(index=False))
