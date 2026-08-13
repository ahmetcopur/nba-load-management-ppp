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

# 3) Stratified TV-exposure permutation placebo (not literal Fisher RI because TV assignment is observational).
# FWL: fixed effects = player + team-season. Fixed finite nuisance = star, star_post, controls.
# Permute game-level TV indicator within season x calendar-month strata, preserving exact TV counts per stratum.
def permutation_test(data,tvcol,label,B=99,seed=20260811):
    d=data.copy()
    d['tv_model']=d[tvcol].astype(float)
    d['star_post']=d.star_PPP_it*d.postPPP
    fixed=['star_PPP_it','star_post']+controls
    keep=['absence_onset','nba_player_id','game_id','team','season','game_date_et','star_PPP_it','postPPP','tv_model']+fixed
    # dedupe repeated fixed names
    keep=list(dict.fromkeys(keep))
    d=d[keep].replace([np.inf,-np.inf],np.nan).dropna().copy()
    d['teamseason']=d.team.astype(str)+'|'+d.season.astype(str)
    d['month']=pd.to_datetime(d.game_date_et).dt.strftime('%m')
    # game-level table; TV is identical for the two team sides / player rows.
    game=d[['game_id','season','month','tv_model']].drop_duplicates('game_id').copy()
    assert game.groupby('game_id').size().max()==1
    # map game ID to row-level index in game table
    game_index={g:i for i,g in enumerate(game.game_id)}
    row_game_idx=d.game_id.map(game_index).to_numpy()
    # FE residualization projectors are reused.
    Gp,cp,_,_=projector(d.nba_player_id); Gt,ct,_,_=projector(d.teamseason)
    def mfe(A,tol=2e-6,max_iter=45):
        A=np.asarray(A,float).copy()
        for it in range(max_iter):
            old=A.copy() if it<2 or it%5==0 else None
            A-=Gp@((Gp.T@A)/cp[:,None]); A-=Gt@((Gt.T@A)/ct[:,None])
            if old is not None and np.max(np.abs(A-old))<tol: break
        return A
    # transform y and fixed nuisance once
    YZ=np.column_stack([d.absence_onset.to_numpy(float), d[fixed].to_numpy(float)])
    YZf=mfe(YZ); yf=YZf[:,0]; Zf=YZf[:,1:]
    # remove absorbed/degenerate nuisance and QR-project it out
    kz=(Zf*Zf).sum(0)>1e-12; Zf=Zf[:,kz]
    # use compact QR; ~18 columns only
    Q,_=np.linalg.qr(Zf,mode='reduced')
    yr=yf-Q@(Q.T@yf)
    star=d.star_PPP_it.to_numpy(float); post=d.postPPP.to_numpy(float)
    def beta_for_game_tv(game_tv):
        tvr=game_tv[row_game_idx]
        W=np.column_stack([tvr,star*tvr,post*tvr,star*post*tvr])
        Wf=mfe(W)
        # FWL cross-products: avoid constructing M_Q W at row level.
        qtw=Q.T@Wf
        gram=Wf.T@Wf-qtw.T@qtw
        rhs=Wf.T@yr  # yr is orthogonal to Q
        beta=np.linalg.solve(gram,rhs)
        return float(beta[3])
    observed=beta_for_game_tv(game.tv_model.to_numpy(float))
    rng=np.random.default_rng(seed)
    strata=[np.asarray(idx,dtype=int) for idx in game.reset_index(drop=True).groupby(['season','month'],sort=False).indices.values()]
    vals=np.empty(B)
    base=game.tv_model.to_numpy(float)
    t0=time.time()
    for bidx in range(B):
        perm=base.copy()
        for idx in strata:
            perm[idx]=rng.permutation(perm[idx])
        vals[bidx]=beta_for_game_tv(perm)
    p_two=(1+np.sum(np.abs(vals)>=abs(observed)))/(B+1)
    p_upper=(1+np.sum(vals>=observed))/(B+1)
    row={'definition':label,'B':B,'seed':seed,'n':len(d),'games':len(game),'strata':len(strata),'observed_pp':100*observed,
         'perm_mean_pp':100*vals.mean(),'perm_sd_pp':100*vals.std(ddof=1),'perm_q025_pp':100*np.quantile(vals,.025),
         'perm_q975_pp':100*np.quantile(vals,.975),'p_two_sided':p_two,'p_upper':p_upper,'elapsed_sec':time.time()-t0,
         'permutation_unit':'game','stratification':'season x calendar month','interpretation':'randomization-style placebo; national-TV assignment is observational, so not an exact Fisher test'}
    pd.DataFrame({'permuted_estimate_pp':100*vals}).to_csv(OUT/f'permutation_draws_{label}.csv',index=False)
    return row


perm_rows=[]
for tvcol,label in [('announced_tv_primary','legacy_primary')]:
    perm_rows.append(permutation_test(df,tvcol,label,B=99,seed=20260811))
pd.DataFrame(perm_rows).to_csv(OUT/'stratified_tv_permutation_placebo.csv',index=False)
print(pd.DataFrame(perm_rows).to_string(index=False))
