from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from scipy.stats import norm
import json, warnings, time
warnings.filterwarnings('ignore')

REPO_ROOT = Path(__file__).resolve().parents[2]

DATA = (
    REPO_ROOT
    / "data_final"
    / "player_game_panel_model_at_risk_analysis_ready.csv.gz"
)

OUT = REPO_ROOT / "results" / "portable_first_pass"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA)

# Coerce booleans robustly.
def b(s):
    if s.dtype == bool:
        return s.astype(float)
    return s.map(lambda x: 1.0 if str(x).lower() in {'true','1','1.0'} else 0.0)

for c in ['star_PPP_it','postPPP','announced_tv_primary','announced_nba_tv','is_home','back_to_back',
          'three_games_in_four_days','four_games_in_six_days','five_games_in_seven_days',
          'opponent_bottom_quartile_pre','opponent_back_to_back','cup_game','absence_onset',
          'vague_onset_frozen','specific_onset_frozen','vague_onset_provisional_v1','covid_season_2020_21']:
    df[c]=b(df[c])

# Terms: all lower-order terms needed for triple interaction; post main is absorbed by season FE.
df['star_post']=df.star_PPP_it*df.postPPP
df['star_tv']=df.star_PPP_it*df.announced_tv_primary
df['post_tv']=df.postPPP*df.announced_tv_primary
df['triple']=df.star_PPP_it*df.postPPP*df.announced_tv_primary

# Scaled controls.
df['elo_100']=df['signed_elo_advantage']/100.0
df['travel_1000']=df['travel_km_since_previous_game']/1000.0
df['travel_disadv_1000']=df['travel_disadvantage_km']/1000.0
df['minutes10_100']=df['minutes_sum_prior_10_roster_games']/100.0
df['games_before_10']=df['games_played_before_game']/10.0
df['dist65_10']=df['dist_to_65_before_game']/10.0

policy_terms=['star_PPP_it','announced_tv_primary','star_post','star_tv','post_tv','triple']
controls=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days',
          'travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100',
          'opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days',
          'travel_disadv_1000','cup_game','minutes10_100','games_before_10']

# Iterative two-way demeaning.
def absorb_two_way(A, g1, g2, tol=1e-11, max_iter=200):
    A=np.asarray(A,dtype=float).copy()
    codes1, uniques1=pd.factorize(g1, sort=False)
    codes2, uniques2=pd.factorize(g2, sort=False)
    n1=len(uniques1); n2=len(uniques2)
    counts1=np.bincount(codes1, minlength=n1).astype(float)
    counts2=np.bincount(codes2, minlength=n2).astype(float)
    for it in range(max_iter):
        old=A.copy() if it<5 or it%10==0 else None
        # subtract group1 means for every column
        sums=np.zeros((n1,A.shape[1]))
        np.add.at(sums,codes1,A)
        A-=sums[codes1]/counts1[codes1,None]
        sums=np.zeros((n2,A.shape[1]))
        np.add.at(sums,codes2,A)
        A-=sums[codes2]/counts2[codes2,None]
        if old is not None:
            delta=np.max(np.abs(A-old))
            if delta<tol:
                break
    return A, it+1

def fit_lpm(data, outcome, tv_col='announced_tv_primary', use_controls=True, label=''):
    d=data.copy()
    # rebuild terms if alternative TV definition
    d['tv_model']=d[tv_col]
    d['star_tv_m']=d.star_PPP_it*d.tv_model
    d['post_tv_m']=d.postPPP*d.tv_model
    d['triple_m']=d.star_PPP_it*d.postPPP*d.tv_model
    terms=['star_PPP_it','tv_model','star_post','star_tv_m','post_tv_m','triple_m']
    if use_controls:
        terms+=controls
    keep=[outcome,'nba_player_id','game_id','season']+terms
    d=d[keep].replace([np.inf,-np.inf],np.nan).dropna()
    y=d[outcome].astype(float).to_numpy()[:,None]
    X=d[terms].astype(float).to_numpy()
    A=np.column_stack([y,X])
    At,it=absorb_two_way(A,d['nba_player_id'],d['season'])
    yt=At[:,0]; Xt=At[:,1:]
    # drop absorbed/zero columns
    ss=(Xt**2).sum(axis=0)
    keepidx=ss>1e-12
    dropped=[t for t,k in zip(terms,keepidx) if not k]
    terms2=[t for t,k in zip(terms,keepidx) if k]
    Xt=Xt[:,keepidx]
    res=sm.OLS(yt,Xt).fit()

    if label in {
        'Extensive baseline',
        'Extensive primary+NBA TV',
        'Extensive excl Cup'
    }:
        U, s, Vh = np.linalg.svd(Xt, full_matrices=False)
        rank = np.linalg.matrix_rank(Xt)

        null_vec = Vh[-1]
        null_vec = null_vec / np.max(np.abs(null_vec))

        null_terms = sorted(
            zip(terms2, null_vec),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        print(
            "\nRANK DIAGNOSTIC:", label,
            "\n  columns =", Xt.shape[1],
            "\n  rank =", rank,
            "\n  smallest singular value =", s[-1],
            "\n  largest singular value =", s[0],
            "\n  condition =", s[0] / s[-1],
            "\n  terms =", terms2,
            "\n  null-space loadings:"
        )

        for term, loading in null_terms:
            if abs(loading) > 1e-4:
                print(f"    {term:35s} {loading:+.8f}")

        print()
    cov, cov_player, cov_game = cov_cluster_2groups(
        res,
        pd.factorize(d['nba_player_id'])[0],
        pd.factorize(d['game_id'])[0],
        use_correction=True
    )

    if label in {'Extensive primary+NBA TV', 'Extensive excl Cup'}:
        j = terms2.index('triple_m')
        print(
            "\nDIAGNOSTIC:", label,
            "\n  beta =", res.params[j],
            "\n  var two-way =", cov[j, j],
            "\n  var player =", cov_player[j, j],
            "\n  var game =", cov_game[j, j],
            "\n  condition number =", np.linalg.cond(Xt.T @ Xt),
            "\n"
        )
    se=np.sqrt(np.maximum(np.diag(cov),0))
    beta=res.params
    z=beta/se
    p=2*norm.sf(np.abs(z))
    low=beta-1.96*se; high=beta+1.96*se
    table=pd.DataFrame({'term':terms2,'estimate':beta,'std_error':se,'z':z,'p_value':p,'ci_low':low,'ci_high':high})
    return {
        'label':label,'outcome':outcome,'n':len(d),'players':d.nba_player_id.nunique(),'games':d.game_id.nunique(),
        'demean_iterations':it,'dropped':dropped,'r2_within':float(res.rsquared),'table':table
    }

results=[]
# Baseline extensive margin
results.append(fit_lpm(df,'absence_onset',label='Extensive baseline'))
# Classification margin: only vague or specific injury onset
inj=df[(df.vague_onset_frozen==1)|(df.specific_onset_frozen==1)].copy()
inj['vague_conditional']=inj.vague_onset_frozen
results.append(fit_lpm(inj,'vague_conditional',label='Classification baseline'))
# Robustness
results.append(fit_lpm(df[df.season!='2020-21'],'absence_onset',label='Extensive excl 2020-21'))
df['tv_plus_nbatv']=((df.announced_tv_primary==1)|(df.announced_nba_tv==1)).astype(float)
results.append(fit_lpm(df,'absence_onset',tv_col='tv_plus_nbatv',label='Extensive primary+NBA TV'))
results.append(fit_lpm(df[df.cup_game==0],'absence_onset',label='Extensive excl Cup'))
# opening-night star definition
alt=df.copy(); alt['star_PPP_it']=alt['star_at_opening_night'].map(lambda x: 1.0 if str(x).lower() in {'true','1','1.0'} else 0.0)
alt['star_post']=alt.star_PPP_it*alt.postPPP
results.append(fit_lpm(alt,'absence_onset',label='Extensive opening-night star'))
# no controls
results.append(fit_lpm(df,'absence_onset',use_controls=False,label='Extensive no controls'))
# classification robustness v1
inj_v1=df[(df.onset_type_provisional_v1=='vague_injury_onset')|(df.onset_type_provisional_v1=='specific_injury_onset')].copy()
inj_v1['vague_conditional_v1']=(inj_v1.onset_type_provisional_v1=='vague_injury_onset').astype(float)
results.append(fit_lpm(inj_v1,'vague_conditional_v1',label='Classification provisional v1'))
results.append(fit_lpm(inj[inj.season!='2020-21'],'vague_conditional',label='Classification excl 2020-21'))
results.append(fit_lpm(inj[inj.cup_game==0],'vague_conditional',label='Classification excl Cup'))

# Save tables and concise focal summary
out= OUT
out.mkdir(exist_ok=True)
alltabs=[]; focal=[]
for i,r in enumerate(results):
    tab=r['table'].copy(); tab.insert(0,'model',r['label']); tab['n']=r['n']; tab['players']=r['players']; tab['games']=r['games']; tab['r2_within']=r['r2_within']
    alltabs.append(tab)
    triple_term='triple_m'
    row=tab[tab.term==triple_term]
    if len(row):
        x=row.iloc[0]
        focal.append({'model':r['label'],'outcome':r['outcome'],'n':r['n'],'players':r['players'],'games':r['games'],
                      'estimate':x.estimate,'std_error':x.std_error,'p_value':x.p_value,'ci_low':x.ci_low,'ci_high':x.ci_high,
                      'r2_within':r['r2_within']})
    with open(out/f'model_{i+1:02d}_meta.json','w') as f:
        json.dump({k:v for k,v in r.items() if k!='table'},f,indent=2)

pd.concat(alltabs,ignore_index=True).to_csv(out/'all_model_coefficients.csv',index=False)
pd.DataFrame(focal).to_csv(out/'focal_triple_interaction_results.csv',index=False)

# Descriptive triple difference in raw rates using 8 cells.
cell=df.groupby(['star_PPP_it','postPPP','announced_tv_primary']).agg(n=('player_team_game_id','size'),absence=('absence_onset','sum'),vague=('vague_onset_frozen','sum'),specific=('specific_onset_frozen','sum')).reset_index()
for y in ['absence','vague','specific']:
    cell[y+'_rate']=cell[y]/cell.n
cell.to_csv(out/'raw_policy_cells.csv',index=False)

def ddd(rate):
    vals={(int(r.star_PPP_it),int(r.postPPP),int(r.announced_tv_primary)):getattr(r,rate) for r in cell.itertuples()}
    # [(post TV-star gap - nonTV-star gap) - same pre]
    return ((vals[(1,1,1)]-vals[(0,1,1)])-(vals[(1,1,0)]-vals[(0,1,0)])) - ((vals[(1,0,1)]-vals[(0,0,1)])-(vals[(1,0,0)]-vals[(0,0,0)]))
raw_ddd={k:ddd(k+'_rate') for k in ['absence','vague','specific']}
with open(out/'raw_ddd.json','w') as f: json.dump(raw_ddd,f,indent=2)
print(pd.DataFrame(focal).to_string(index=False))
print('raw ddd',raw_ddd)
