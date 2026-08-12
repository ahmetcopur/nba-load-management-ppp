from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
import pandas as pd, numpy as np, statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from scipy.stats import norm, chi2
from scipy.sparse import csr_matrix
import warnings
warnings.filterwarnings('ignore')
AP=REPO_ROOT/'data_final/player_game_panel_model_at_risk_analysis_ready.csv.gz'
TP=REPO_ROOT/'data_intermediate/announced_tv_six_seasons.csv'
df=pd.read_csv(AP,low_memory=False); tv=pd.read_csv(TP,low_memory=False)
def b(s):
    if s.dtype==bool:return s.astype(float)
    return s.map(lambda x:1.0 if str(x).lower() in {'true','1','1.0'} else 0.0)
for c in ['star_PPP_it','postPPP','announced_tv_primary','announced_nba_tv','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game','absence_onset']:
    df[c]=b(df[c])
df['home_team']=np.where(df.is_home==1,df.team,df.opponent);df['away_team']=np.where(df.is_home==1,df.opponent,df.team)
keys=['season','game_date_et','home_team','away_team']
tv2=tv[keys+['network_announced','announced_tv_status']].drop_duplicates(keys)
df=df.merge(tv2,on=keys,how='left',validate='many_to_one');assert df.announced_tv_status.notna().all()
old_linear={'ABC','ESPN','ABC/ESPN','ABC|ESPN','TNT'}; new_linear={'ABC','ESPN','ABC/ESPN','ABC|ESPN','NBC/Peacock'}
df['tv_harmonized_linear']=np.where(df.season=='2025-26',df.network_announced.fillna('').isin(new_linear),df.network_announced.fillna('').isin(old_linear)).astype(float)
df['elo_100']=df.signed_elo_advantage/100;df['travel_1000']=df.travel_km_since_previous_game/1000;df['travel_disadv_1000']=df.travel_disadvantage_km/1000;df['minutes10_100']=df.minutes_sum_prior_10_roster_games/100;df['games_before_10']=df.games_played_before_game/10;df['dist65_10']=df.dist_to_65_before_game/10
controls=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadv_1000','cup_game','minutes10_100','games_before_10']

def projector(groups):
    codes,uniques=pd.factorize(groups,sort=False);n=len(codes);k=len(uniques);G=csr_matrix((np.ones(n),(np.arange(n),codes)),shape=(n,k));counts=np.asarray(G.sum(0)).ravel();return G,counts

def absorb(A,g1,g2,tol=1e-10,max_iter=150):
    G1,c1=projector(g1);G2,c2=projector(g2)
    for it in range(max_iter):
        old=A.copy() if it<3 or it%5==0 else None
        A-=G1@((G1.T@A)/c1[:,None]);A-=G2@((G2.T@A)/c2[:,None])
        if old is not None and np.max(np.abs(A-old))<tol:break
    return A,it+1

def fit_design(d,terms):
    d=d[['absence_onset','nba_player_id','game_id','season']+terms].replace([np.inf,-np.inf],np.nan).dropna().copy()
    A=d[['absence_onset']+terms].to_numpy(float);A,it=absorb(A,d.nba_player_id,d.season)
    y=A[:,0];X=A[:,1:];keep=(X*X).sum(0)>1e-12;X=X[:,keep];names=[x for x,k in zip(terms,keep) if k]
    res=sm.OLS(y,X).fit();cov,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0],use_correction=True)
    return d,res,cov,names,it

def event_study(data,tvcol,label):
    d=data.copy();d['tv_model']=d[tvcol];d['star_tv']=d.star_PPP_it*d.tv_model
    base='2022-23'; seasons=['2020-21','2021-22','2023-24','2024-25','2025-26']
    terms=['star_PPP_it','tv_model','star_tv']
    for s in seasons:
        ind=(d.season==s).astype(float);d[f'star_s_{s}']=d.star_PPP_it*ind;d[f'tv_s_{s}']=d.tv_model*ind;d[f'st_{s}']=d.star_tv*ind;terms += [f'star_s_{s}',f'tv_s_{s}',f'st_{s}']
    terms+=controls
    dd,res,cov,names,it=fit_design(d,terms);beta=res.params;se=np.sqrt(np.maximum(np.diag(cov),0));p=2*norm.sf(abs(beta/se));lo=beta-1.96*se;hi=beta+1.96*se
    rows=[]
    for s in seasons:
        j=names.index(f'st_{s}');rows.append({'definition':label,'season':s,'estimate_pp':100*beta[j],'se_pp':100*se[j],'low_pp':100*lo[j],'high_pp':100*hi[j],'p':p[j]})
    # joint null 2020-21 = 0 and 2021-22 = 0 relative to 2022-23
    idx=[names.index('st_2020-21'),names.index('st_2021-22')];bv=beta[idx];V=cov[np.ix_(idx,idx)];stat=float(bv.T@np.linalg.pinv(V)@bv);jp=float(chi2.sf(stat,2))
    return rows,{'definition':label,'n':len(dd),'joint_pretrend_chi2':stat,'df':2,'p':jp,'iterations':it}

def placebo(data,tvcol,fake_start,label):
    # restrict to three actual pre-PPP seasons
    d=data[data.season.isin(['2020-21','2021-22','2022-23'])].copy(); order={'2020-21':0,'2021-22':1,'2022-23':2};cut=order[fake_start]
    d['fake_post']=d.season.map(order).ge(cut).astype(float);d['tv_model']=d[tvcol];d['star_post_fake']=d.star_PPP_it*d.fake_post;d['star_tv_fake']=d.star_PPP_it*d.tv_model;d['post_tv_fake']=d.fake_post*d.tv_model;d['triple_fake']=d.star_PPP_it*d.fake_post*d.tv_model
    terms=['star_PPP_it','tv_model','star_post_fake','star_tv_fake','post_tv_fake','triple_fake']+controls
    dd,res,cov,names,it=fit_design(d,terms);j=names.index('triple_fake');se=np.sqrt(max(cov[j,j],0));bta=res.params[j];pv=2*norm.sf(abs(bta/se));return {'definition':label,'fake_start':fake_start,'n':len(dd),'estimate_pp':100*bta,'se_pp':100*se,'low_pp':100*(bta-1.96*se),'high_pp':100*(bta+1.96*se),'p':pv,'iterations':it}

rows=[];tests=[];pls=[]
for tvcol,label in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
    r,t=event_study(df,tvcol,label);rows+=r;tests.append(t)
    pls.append(placebo(df,tvcol,'2021-22',label));pls.append(placebo(df,tvcol,'2022-23',label))
out=REPO_ROOT/'results/portable_identification_stage2';out.mkdir(parents=True,exist_ok=True)
pd.DataFrame(rows).to_csv(out/'event_study_tv_definitions.csv',index=False);pd.DataFrame(tests).to_csv(out/'joint_pretrend_tests.csv',index=False);pd.DataFrame(pls).to_csv(out/'preperiod_placebo_policy_dates.csv',index=False)
print('JOINT PRETREND');print(pd.DataFrame(tests).to_string(index=False));print('\nPLACEBOS');print(pd.DataFrame(pls).to_string(index=False));print('\nEVENT');print(pd.DataFrame(rows).to_string(index=False))
