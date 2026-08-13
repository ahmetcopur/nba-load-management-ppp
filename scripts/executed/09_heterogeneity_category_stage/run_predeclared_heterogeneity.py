from pathlib import Path
import json, hashlib, warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.sparse import csr_matrix
from scipy.stats import norm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from statsmodels.stats.multitest import multipletests
warnings.filterwarnings('ignore')

ROOT=Path('/mnt/data/nba_heterogeneity_work')
AP=ROOT/'nba_player_game_analysis_ready_v1/player_game_panel_model_at_risk_analysis_ready.csv.gz'
TP=Path('/mnt/data/nba_continue/nba_announced_tv_six_seasons_v1.zip')
OUT=Path('/mnt/data/nba_heterogeneity_predeclared_v1')
OUT.mkdir(parents=True,exist_ok=True)

# tv package already unpacked elsewhere? unpack directly if needed
import zipfile
TVUN=ROOT/'tv_unpack'
TVUN.mkdir(exist_ok=True)
with zipfile.ZipFile(TP) as z:
    z.extractall(TVUN)
tv_path=list(TVUN.rglob('announced_tv_six_seasons.csv'))[0]

df=pd.read_csv(AP,low_memory=False)
tv=pd.read_csv(tv_path,low_memory=False)

def b(s):
    if s.dtype==bool:return s.astype(float)
    return s.map(lambda x:1.0 if str(x).strip().lower() in {'true','1','1.0'} else 0.0)

bool_cols=['star_PPP_it','postPPP','announced_tv_primary','announced_nba_tv','is_home','back_to_back',
           'three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre',
           'opponent_back_to_back','cup_game','absence_onset']
for c in bool_cols: df[c]=b(df[c])

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

# scaled controls identical to standard model
df['elo_100']=pd.to_numeric(df.signed_elo_advantage,errors='coerce')/100.0
df['travel_1000']=pd.to_numeric(df.travel_km_since_previous_game,errors='coerce')/1000.0
df['travel_disadv_1000']=pd.to_numeric(df.travel_disadvantage_km,errors='coerce')/1000.0
df['minutes10_100']=pd.to_numeric(df.minutes_sum_prior_10_roster_games,errors='coerce')/100.0
df['games_before_10']=pd.to_numeric(df.games_played_before_game,errors='coerce')/10.0
df['dist65_10']=pd.to_numeric(df.dist_to_65_before_game,errors='coerce')/10.0
base_controls=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days',
          'travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100',
          'opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days',
          'travel_disadv_1000','cup_game','minutes10_100','games_before_10','dist65_10']

# PREDECLARED heterogeneity definitions
# 1: second night of B2B
# 2: opponent bottom quartile pregame
# 3: workload top quartile within season, only after >=10 prior roster games
# 4: within 15 games short of 65, compare 0-5 short vs 6-15 short

# workload thresholds calculated without outcome use
eligible_work=pd.to_numeric(df.games_played_before_game,errors='coerce')>=10
work_q75=(df.loc[eligible_work].groupby('season')['minutes_sum_prior_10_roster_games'].quantile(.75).to_dict())
df['high_workload_q75']=0.0
for s,q in work_q75.items():
    mask=eligible_work & (df.season==s)
    df.loc[mask,'high_workload_q75']=(pd.to_numeric(df.loc[mask,'minutes_sum_prior_10_roster_games'],errors='coerce')>=q).astype(float)

dist=pd.to_numeric(df.dist_to_65_before_game,errors='coerce')
df['near_65_prethreshold']=(dist.between(0,5,inclusive='both')).astype(float)

specs=[
    dict(name='back_to_back', h='back_to_back', sample=np.ones(len(df),dtype=bool), remove=['back_to_back'], definition='Current game is the second night of a back-to-back.'),
    dict(name='weak_opponent', h='opponent_bottom_quartile_pre', sample=np.ones(len(df),dtype=bool), remove=['opponent_bottom_quartile_pre'], definition='Opponent is in the pregame bottom quartile of the strength distribution.'),
    dict(name='high_recent_workload', h='high_workload_q75', sample=eligible_work.to_numpy(), remove=['minutes10_100'], definition='Prior-10-game minutes at or above the season-specific 75th percentile; sample requires at least 10 prior roster games.'),
    dict(name='near_65_threshold', h='near_65_prethreshold', sample=dist.between(0,15,inclusive='both').fillna(False).to_numpy(), remove=['dist65_10','games_before_10'], definition='Among player-games 0-15 games short of 65, H=1 means 0-5 games short and H=0 means 6-15 games short.'),
]

# sparse FE absorption helpers
def projector(groups):
    codes, uniques=pd.factorize(groups,sort=False)
    n=len(codes); k=len(uniques)
    G=csr_matrix((np.ones(n),(np.arange(n),codes)),shape=(n,k))
    counts=np.asarray(G.sum(axis=0)).ravel()
    return G,counts

def absorb(A,g1,g2,tol=1e-10,max_iter=250):
    A=np.asarray(A,float).copy()
    G1,c1=projector(g1); G2,c2=projector(g2)
    for it in range(max_iter):
        old=A.copy() if it<3 or it%5==0 else None
        A-=G1@((G1.T@A)/c1[:,None])
        A-=G2@((G2.T@A)/c2[:,None])
        if old is not None and np.max(np.abs(A-old))<tol: break
    return A,it+1

def interactions(d,tvcol,hcol):
    d=d.copy()
    d['S']=d.star_PPP_it.astype(float);d['P']=d.postPPP.astype(float);d['T']=d[tvcol].astype(float);d['H']=d[hcol].astype(float)
    # complete factorial lower-order terms through four-way
    terms=[]
    factors=['S','P','T','H']
    from itertools import combinations
    for r in range(1,5):
        for comb in combinations(factors,r):
            name=''.join(comb)
            v=np.ones(len(d))
            for c in comb:v*=d[c].to_numpy(float)
            d[name]=v
            terms.append(name)
    return d,terms

def fit_one(data,tvcol,spec):
    d=data.loc[spec['sample']].copy()
    d,inter=interactions(d,tvcol,spec['h'])
    ctr=[c for c in base_controls if c not in spec['remove']]
    cols=['absence_onset','nba_player_id','game_id','team','season']+inter+ctr
    d=d[cols].replace([np.inf,-np.inf],np.nan).dropna()
    A=d[['absence_onset']+inter+ctr].to_numpy(float)
    teamseason=d.team.astype(str)+'|'+d.season.astype(str)
    A,it=absorb(A,d.nba_player_id,teamseason)
    y=A[:,0];X=A[:,1:]
    raw_names=inter+ctr
    keep=(X*X).sum(0)>1e-12
    X=X[:,keep];names=[n for n,k in zip(raw_names,keep) if k]
    res=sm.OLS(y,X).fit()
    cov,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0],use_correction=True)
    beta=np.asarray(res.params); cov=np.asarray(cov)
    if 'SPT' not in names or 'SPTH' not in names: raise RuntimeError(f'missing focal terms {spec["name"]} {tvcol}')
    j=names.index('SPT'); k=names.index('SPTH')
    b0=beta[j]; v0=cov[j,j]
    bdiff=beta[k]; vdiff=cov[k,k]
    b1=b0+bdiff; v1=v0+vdiff+2*cov[j,k]
    se0=np.sqrt(max(v0,0)); sed=np.sqrt(max(vdiff,0)); se1=np.sqrt(max(v1,0))
    p0=2*norm.sf(abs(b0/se0)); pdiff=2*norm.sf(abs(bdiff/sed)); p1=2*norm.sf(abs(b1/se1))
    h=d['H'].to_numpy(float)
    # descriptive cell sizes within model-complete sample
    return {
        'heterogeneity':spec['name'],'definition':spec['definition'],'tv_definition':tvcol,
        'n':len(d),'games':d.game_id.nunique(),'players':d.nba_player_id.nunique(),
        'h1_n':int((h==1).sum()),'h0_n':int((h==0).sum()),
        'ddd_h0_pp':100*b0,'ddd_h0_se_pp':100*se0,'ddd_h0_p':p0,
        'ddd_h1_pp':100*b1,'ddd_h1_se_pp':100*se1,'ddd_h1_p':p1,
        'difference_h1_minus_h0_pp':100*bdiff,'difference_se_pp':100*sed,'heterogeneity_p':pdiff,
        'iterations':it
    }

rows=[]
for spec in specs:
    for tvcol in ['announced_tv_primary','tv_harmonized_linear']:
        print('running',spec['name'],tvcol,flush=True)
        rows.append(fit_one(df,tvcol,spec))
res=pd.DataFrame(rows)
# FDR adjustment within each TV family across the 4 predeclared heterogeneity tests
res['heterogeneity_q_bh']=np.nan
for tvcol,g in res.groupby('tv_definition'):
    idx=g.index
    res.loc[idx,'heterogeneity_q_bh']=multipletests(g.heterogeneity_p.values,method='fdr_bh')[1]

res.to_csv(OUT/'heterogeneity_results.csv',index=False)
pd.DataFrame([{'season':s,'workload_q75_minutes_prior10':q} for s,q in work_q75.items()]).to_csv(OUT/'workload_thresholds.csv',index=False)

# counts/rates descriptive (not causal), by H and TV definition / star / post
cell_rows=[]
for spec in specs:
    dd=df.loc[spec['sample']].copy()
    for tvcol in ['announced_tv_primary','tv_harmonized_linear']:
        for hval in [0,1]:
            x=dd[dd[spec['h']]==hval]
            for S in [0,1]:
                for P in [0,1]:
                    for T in [0,1]:
                        z=x[(x.star_PPP_it==S)&(x.postPPP==P)&(x[tvcol]==T)]
                        cell_rows.append({'heterogeneity':spec['name'],'tv_definition':tvcol,'H':hval,'star':S,'post':P,'tv':T,'n':len(z),'absence_onset_rate':z.absence_onset.mean() if len(z) else np.nan})
pd.DataFrame(cell_rows).to_csv(OUT/'heterogeneity_raw_cells.csv',index=False)

# age/career status note
(OUT/'age_career_stage_status.md').write_text('''# Age / career-stage heterogeneity status\n\nThis predeclared dimension was **not estimated in v1**. The frozen analysis-ready panel has NBA player IDs but no reliable birthdate, age-on-game-date, rookie year, or full-career experience field. The six-season observation window must not be used to infer career age because veteran careers are left-censored. A future age/career-stage test should first merge an external, player-ID-resolved metadata table (preferably official NBA birthdate/experience data), freeze the derived age/career bins, and only then estimate the four-way heterogeneity interaction.\n''')

summary={
    'stage':'predeclared heterogeneity v1',
    'model':'LPM, player + team-season FE, two-way player + game clustering',
    'outcome':'new absence onset',
    'tv_definitions':['legacy announced_tv_primary','harmonized linear national TV'],
    'predeclared_tests_completed':['back_to_back','weak_opponent','high_recent_workload','near_65_threshold'],
    'predeclared_test_pending':'age/career stage (metadata unavailable in frozen panel)',
    'multiple_testing':'Benjamini-Hochberg FDR within each TV-definition family (4 tests)',
}
(OUT/'results_summary.json').write_text(json.dumps(summary,indent=2))

readme='''# NBA PPP — Predeclared Heterogeneity v1\n\nThis package estimates whether the focal Star × PostPPP × TV difference-in-difference-in-differences varies across four predeclared, already-observed dimensions. The model retains player and team-season fixed effects and two-way player/game clustered inference.\n\n## Frozen subgroup definitions\n\n1. **Back-to-back:** current game is the second night of a back-to-back.\n2. **Weak opponent:** pregame bottom-quartile opponent indicator.\n3. **High recent workload:** prior-10-roster-game minutes >= the season-specific 75th percentile; estimation sample requires at least 10 prior roster games.\n4. **65-game proximity:** among player-games 0-15 games short of 65, compare 0-5 short (H=1) with 6-15 short (H=0).\n5. **Age/career stage:** intentionally not estimated in v1 because the frozen panel lacks a reliable age/experience field.\n\nFor each binary H, the regression includes the complete Star × PostPPP × TV × H factorial. `difference_h1_minus_h0_pp` is the formal four-way interaction. `heterogeneity_q_bh` applies Benjamini-Hochberg FDR correction across the four tests separately within each TV-definition family.\n\nThese are heterogeneity analyses, not replacements for the frozen main effect.\n'''
(OUT/'README.md').write_text(readme)

# copy script
import shutil
shutil.copy2(__file__,OUT/'run_predeclared_heterogeneity.py')
# manifest
mans=[]
for p in sorted(OUT.iterdir()):
    if p.is_file() and p.name!='file_manifest_sha256.csv':
        mans.append({'file':p.name,'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
pd.DataFrame(mans).to_csv(OUT/'file_manifest_sha256.csv',index=False)
print(res[['heterogeneity','tv_definition','ddd_h0_pp','ddd_h1_pp','difference_h1_minus_h0_pp','heterogeneity_p','heterogeneity_q_bh','n']].to_string(index=False))
