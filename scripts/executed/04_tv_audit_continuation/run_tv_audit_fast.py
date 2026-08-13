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

# counts in all 7,230 source games, not just model-complete games
source=tv.copy();source['disney_narrow']=source.network_announced.fillna('').isin({'ABC','ESPN','ABC/ESPN','ABC|ESPN'}).astype(int)
counts=source.groupby('season').agg(games=('fixture_row','size'),legacy_primary=('announced_tv_primary','sum'),disney_narrow=('disney_narrow','sum'),nba_tv=('announced_nba_tv','sum')).reset_index()
print('COUNTS\n',counts.to_string(index=False))
results=[]
# benchmark just to confirm exact replication
results.append(fit(df,'announced_tv_primary','season','Legacy primary benchmark'))
results.append(fit(df[df.season!='2025-26'],'announced_tv_primary','season','Legacy primary exclude 2025-26'))
results.append(fit(df[df.season!='2025-26'],'announced_tv_primary','teamseason','Legacy primary exclude 2025-26 team-season FE'))
results.append(fit(df,'tv_narrow_disney','season','Narrow Disney full six seasons'))
results.append(fit(df,'tv_narrow_disney','teamseason','Narrow Disney team-season FE'))
# broad only period with complete NBA TV schedule and old rights regime
mid=df[df.season.isin(['2021-22','2022-23','2023-24','2024-25'])]
results.append(fit(mid,'tv_primary_plus_nbatv','season','Broad primary+NBA TV 2021-22 to 2024-25'))
# leave-one-out legacy
for s in sorted(df.season.unique()):
    results.append(fit(df[df.season!=s],'announced_tv_primary','season',f'Legacy leave out {s}'))
r=pd.DataFrame(results)
print('\nRESULTS\n',r[['label','estimate_pp','low_pp','high_pp','p','n','iterations']].to_string(index=False))
out=Path('/mnt/data/nba_continue/tv_audit_results');out.mkdir(exist_ok=True)
counts.to_csv(out/'tv_source_counts.csv',index=False);r.to_csv(out/'tv_model_results.csv',index=False)
