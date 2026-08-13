from pathlib import Path
import json, time, warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm, t as student_t
from scipy.sparse import csr_matrix
from statsmodels.stats.sandwich_covariance import cov_cluster, cov_cluster_2groups
warnings.filterwarnings('ignore')

ROOT=Path('/mnt/data/nba_continue')
AP=ROOT/'analysis_unpack/nba_player_game_analysis_ready_v1/player_game_panel_model_at_risk_analysis_ready.csv.gz'
TP=ROOT/'tv/nba_announced_tv_six_seasons_v1/announced_tv_six_seasons.csv'
OUT=ROOT/'identification_stage2_results'; OUT.mkdir(exist_ok=True)

df=pd.read_csv(AP,low_memory=False)
tv=pd.read_csv(TP,low_memory=False)

def b(s):
    if s.dtype==bool: return s.astype(float)
    return s.map(lambda x:1.0 if str(x).lower() in {'true','1','1.0'} else 0.0)
for c in ['star_PPP_it','postPPP','announced_tv_primary','announced_nba_tv','is_home','back_to_back',
          'three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre',
          'opponent_back_to_back','cup_game','absence_onset']:
    df[c]=b(df[c])

# Attach network labels and define harmonized linear national TV as in the TV audit.
df['home_team']=np.where(df.is_home==1,df.team,df.opponent)
df['away_team']=np.where(df.is_home==1,df.opponent,df.team)
keys=['season','game_date_et','home_team','away_team']
tv2=tv[keys+['network_announced','announced_tv_status']].drop_duplicates(keys)
df=df.merge(tv2,on=keys,how='left',validate='many_to_one')
assert df.announced_tv_status.notna().all()
old_linear={'ABC','ESPN','ABC/ESPN','ABC|ESPN','TNT'}
new_linear={'ABC','ESPN','ABC/ESPN','ABC|ESPN','NBC/Peacock'}
df['tv_harmonized_linear']=np.where(df.season=='2025-26',
    df.network_announced.fillna('').isin(new_linear),
    df.network_announced.fillna('').isin(old_linear)).astype(float)

# Scaled controls identical to the first-pass model.
df['elo_100']=df.signed_elo_advantage/100.0
df['travel_1000']=df.travel_km_since_previous_game/1000.0
df['travel_disadv_1000']=df.travel_disadvantage_km/1000.0
df['minutes10_100']=df.minutes_sum_prior_10_roster_games/100.0
df['games_before_10']=df.games_played_before_game/10.0
df['dist65_10']=df.dist_to_65_before_game/10.0
controls=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days',
          'travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100',
          'opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days',
          'travel_disadv_1000','cup_game','minutes10_100','games_before_10','dist65_10']

def projector(groups):
    codes, uniques=pd.factorize(groups,sort=False)
    n=len(codes); k=len(uniques)
    G=csr_matrix((np.ones(n),(np.arange(n),codes)),shape=(n,k))
    counts=np.asarray(G.sum(axis=0)).ravel()
    return G,counts,codes,len(uniques)

def absorb_means(A,g1,g2,tol=1e-10,max_iter=200):
    A=np.asarray(A,float).copy()
    G1,c1,_,_=projector(g1); G2,c2,_,_=projector(g2)
    for it in range(max_iter):
        old=A.copy() if it<3 or it%5==0 else None
        A-=G1@((G1.T@A)/c1[:,None])
        A-=G2@((G2.T@A)/c2[:,None])
        if old is not None and np.max(np.abs(A-old))<tol: break
    return A,it+1

class PlayerTrendAbsorber:
    """Alternating projection: player intercept+linear calendar trend, then team-season FE."""
    def __init__(self, players, teamseason, time_value):
        pc,pu=pd.factorize(players,sort=False); self.np=len(pu); n=len(pc)
        tc,tu=pd.factorize(teamseason,sort=False); self.nt=len(tu)
        self.Gp=csr_matrix((np.ones(n),(np.arange(n),pc)),shape=(n,self.np))
        self.Gt=csr_matrix((np.ones(n),(np.arange(n),tc)),shape=(n,self.nt))
        self.pcount=np.asarray(self.Gp.sum(0)).ravel(); self.tcount=np.asarray(self.Gt.sum(0)).ravel()
        t=np.asarray(time_value,float)
        tmean=np.asarray(self.Gp.T@t).ravel()/self.pcount
        tcx=t-tmean[pc]
        self.Hp=csr_matrix((tcx,(np.arange(n),pc)),shape=(n,self.np))
        self.tss=np.asarray(self.Hp.T@tcx).ravel()
        self.good=self.tss>1e-14
    def proj_player(self,A):
        means=(self.Gp.T@A)/self.pcount[:,None]
        R=A-self.Gp@means
        cross=self.Hp.T@R
        slopes=np.zeros_like(cross); slopes[self.good]=cross[self.good]/self.tss[self.good,None]
        return R-self.Hp@slopes
    def proj_teamseason(self,A):
        means=(self.Gt.T@A)/self.tcount[:,None]
        return A-self.Gt@means
    def absorb(self,A,tol=1e-8,max_iter=150):
        A=np.asarray(A,float).copy()
        for it in range(max_iter):
            old=A.copy() if it<3 or it%5==0 else None
            A=self.proj_player(A); A=self.proj_teamseason(A)
            if old is not None and np.max(np.abs(A-old))<tol: break
        return A,it+1

def prep_model(data,tvcol):
    d=data.copy()
    d['tv_model']=d[tvcol].astype(float)
    d['star_post']=d.star_PPP_it*d.postPPP
    d['star_tv']=d.star_PPP_it*d.tv_model
    d['post_tv']=d.postPPP*d.tv_model
    d['triple']=d.star_PPP_it*d.postPPP*d.tv_model
    terms=['star_PPP_it','tv_model','star_post','star_tv','post_tv','triple']+controls
    keep=['absence_onset','nba_player_id','game_id','team','season','game_date_et']+terms
    d=d[keep].replace([np.inf,-np.inf],np.nan).dropna().copy()
    d['teamseason']=d.team.astype(str)+'|'+d.season.astype(str)
    d['date_cluster']=pd.to_datetime(d.game_date_et).dt.strftime('%Y-%m-%d')
    return d,terms

def fit_standard(data,tvcol):
    d,terms=prep_model(data,tvcol)
    A=d[['absence_onset']+terms].to_numpy(float)
    A,it=absorb_means(A,d.nba_player_id,d.teamseason)
    y=A[:,0]; X=A[:,1:]
    keep=(X*X).sum(0)>1e-12; X=X[:,keep]; names=[x for x,k in zip(terms,keep) if k]
    res=sm.OLS(y,X).fit()
    j=names.index('triple')
    return d,res,names,j,it

def coef_from_cov(res,cov,j,df_t=None):
    beta=float(res.params[j]); se=float(np.sqrt(max(cov[j,j],0)))
    stat=beta/se if se>0 else np.nan
    if df_t is None: p=float(2*norm.sf(abs(stat))); crit=1.96
    else: p=float(2*student_t.sf(abs(stat),df_t)); crit=float(student_t.ppf(.975,df_t))
    return beta,se,p,beta-crit*se,beta+crit*se,stat

# 1) Standard player + team-season FE, clustering sensitivity, and COVID sensitivity.
cluster_rows=[]; standard_rows=[]
for tvcol,label in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
    d,res,names,j,it=fit_standard(df,tvcol)
    # baseline two-way player-game
    pg,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0],use_correction=True)
    beta,se,p,lo,hi,z=coef_from_cov(res,pg,j)
    standard_rows.append({'definition':label,'sample':'all_six','n':len(d),'estimate_pp':100*beta,'se_pp':100*se,'low_pp':100*lo,'high_pp':100*hi,'p':p,'fe':'player+teamseason','clusters':'player+game','iterations':it})
    # one-way cluster variants
    variants=[('player',d.nba_player_id),('game',d.game_id),('team',d.team),('date',d.date_cluster)]
    for nm,g in variants:
        cov=cov_cluster(res,pd.factorize(g)[0],use_correction=True)
        ng=pd.Series(g).nunique(); dft=(ng-1 if nm in {'team','date'} else None)
        bb,ss,pp,ll,hh,zz=coef_from_cov(res,cov,j,dft)
        cluster_rows.append({'definition':label,'cluster':nm,'n_clusters':ng,'estimate_pp':100*bb,'se_pp':100*ss,'low_pp':100*ll,'high_pp':100*hh,'p':pp,'reference_df':dft if dft is not None else np.nan})
    # two-way team-date and player-game
    for nm,g1,g2 in [('player+game',d.nba_player_id,d.game_id),('team+date',d.team,d.date_cluster)]:
        cov,_,_=cov_cluster_2groups(res,pd.factorize(g1)[0],pd.factorize(g2)[0],use_correction=True)
        ng1=pd.Series(g1).nunique(); ng2=pd.Series(g2).nunique(); dft=(min(ng1,ng2)-1 if nm=='team+date' else None)
        bb,ss,pp,ll,hh,zz=coef_from_cov(res,cov,j,dft)
        cluster_rows.append({'definition':label,'cluster':nm,'n_clusters':f'{ng1}+{ng2}','estimate_pp':100*bb,'se_pp':100*ss,'low_pp':100*ll,'high_pp':100*hh,'p':pp,'reference_df':dft if dft is not None else np.nan})
    # COVID-era exclusion: remove both 2020-21 and 2021-22 (baseline already has season FE, so a COVID dummy would be absorbed)
    sub=df[~df.season.isin(['2020-21','2021-22'])]
    ds,ress,namess,js,its=fit_standard(sub,tvcol)
    covs,_,_=cov_cluster_2groups(ress,pd.factorize(ds.nba_player_id)[0],pd.factorize(ds.game_id)[0],use_correction=True)
    bb,ss,pp,ll,hh,zz=coef_from_cov(ress,covs,js)
    standard_rows.append({'definition':label,'sample':'exclude_2020_21_and_2021_22','n':len(ds),'estimate_pp':100*bb,'se_pp':100*ss,'low_pp':100*ll,'high_pp':100*hh,'p':pp,'fe':'player+teamseason','clusters':'player+game','iterations':its})

# 2) Player-specific linear calendar trends + team-season FE.
trend_rows=[]
for tvcol,label in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
    d,terms=prep_model(df,tvcol)
    dates=pd.to_datetime(d.game_date_et)
    tdays=(dates-dates.min()).dt.total_seconds().to_numpy()/86400.0
    # scale to years to improve conditioning; player centered internally.
    tyears=tdays/365.25
    A=d[['absence_onset']+terms].to_numpy(float)
    absorber=PlayerTrendAbsorber(d.nba_player_id,d.teamseason,tyears)
    At,it=absorber.absorb(A)
    y=At[:,0]; X=At[:,1:]
    keep=(X*X).sum(0)>1e-12; X=X[:,keep]; names=[x for x,k in zip(terms,keep) if k]
    res=sm.OLS(y,X).fit(); j=names.index('triple')
    cov,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0],use_correction=True)
    bb,ss,pp,ll,hh,zz=coef_from_cov(res,cov,j)
    trend_rows.append({'definition':label,'n':len(d),'estimate_pp':100*bb,'se_pp':100*ss,'low_pp':100*ll,'high_pp':100*hh,'p':pp,'iterations':it,'fe':'player intercept + player linear calendar trend + teamseason','clusters':'player+game'})


pd.DataFrame(standard_rows).to_csv(OUT/'standard_and_covid_sensitivity.csv',index=False)
pd.DataFrame(cluster_rows).to_csv(OUT/'clustering_sensitivity.csv',index=False)
pd.DataFrame(trend_rows).to_csv(OUT/'player_linear_trends.csv',index=False)
print('STANDARD / COVID')
print(pd.DataFrame(standard_rows).to_string(index=False))
print('\nPLAYER TRENDS')
print(pd.DataFrame(trend_rows).to_string(index=False))
print('\nCLUSTERING')
print(pd.DataFrame(cluster_rows).to_string(index=False))
