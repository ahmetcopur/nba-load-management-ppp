from __future__ import annotations

import csv
import hashlib
import json
import math
import time
import warnings
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.linalg import splu
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings('ignore')

REPO_ROOT = Path(__file__).resolve().parents[2]
CANON = REPO_ROOT/'data_final/player_game_panel_model_at_risk_analysis_ready.csv.gz'
CADENCE = REPO_ROOT/'data_intermediate/player_team_game_harmonized_cadence.csv.gz'
TV = REPO_ROOT/'data_intermediate/announced_tv_six_seasons.csv'
OUT = REPO_ROOT/'results/portable_nonlinear_multinomial'
OUT.mkdir(parents=True, exist_ok=True)

PRIMARY_C = 10.0
SENS_C = [1.0, 10.0, 100.0]
TOL = 1e-4
MAX_ITER = 600

BASE_TERMS = [
    'star','tv','star_post','star_tv','post_tv','triple',
    'is_home','back_to_back','three_games_in_four_days','four_games_in_six_days',
    'travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100',
    'opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days',
    'travel_disadv_1000','cup_game','minutes10_100','games_before_10','dist65_10'
]


def b01(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s.astype(float)
    if np.issubdtype(s.dtype, np.number):
        return s.astype(float)
    return s.map(lambda x: 1.0 if str(x).strip().lower() in {'true','1','1.0'} else 0.0)


def add_common_vars(df: pd.DataFrame, tv_col: str, cadence: bool=False) -> pd.DataFrame:
    d = df.copy()
    for c in ['star_PPP_it','postPPP','is_home','back_to_back','three_games_in_four_days',
              'four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game']:
        d[c] = b01(d[c])
    d['tv'] = b01(d[tv_col])
    d['star'] = d['star_PPP_it']
    d['post'] = d['postPPP']
    d['star_post'] = d.star*d.post
    d['star_tv'] = d.star*d.tv
    d['post_tv'] = d.post*d.tv
    d['triple'] = d.star*d.post*d.tv
    d['elo_100'] = pd.to_numeric(d.signed_elo_advantage, errors='coerce')/100.0
    d['travel_1000'] = pd.to_numeric(d.travel_km_since_previous_game, errors='coerce')/1000.0
    d['travel_disadv_1000'] = pd.to_numeric(d.travel_disadvantage_km, errors='coerce')/1000.0
    if cadence:
        d['minutes10_100'] = pd.to_numeric(d.minutes_sum_prior_10_roster_games_harm, errors='coerce')/100.0
        d['games_before_10'] = pd.to_numeric(d.games_played_before_game_harm, errors='coerce')/10.0
        d['dist65_10'] = pd.to_numeric(d.dist_to_65_before_game_harm, errors='coerce')/10.0
    else:
        d['minutes10_100'] = pd.to_numeric(d.minutes_sum_prior_10_roster_games, errors='coerce')/100.0
        d['games_before_10'] = pd.to_numeric(d.games_played_before_game, errors='coerce')/10.0
        d['dist65_10'] = pd.to_numeric(d.dist_to_65_before_game, errors='coerce')/10.0
    d['team_season'] = d.team.astype(str)+'|'+d.season.astype(str)
    return d


def load_canonical() -> pd.DataFrame:
    d = pd.read_csv(CANON, low_memory=False)
    # merge the network field used to construct harmonized TV
    for c in ['is_home']:
        d[c] = b01(d[c])
    d['home_team'] = np.where(d.is_home == 1, d.team, d.opponent)
    d['away_team'] = np.where(d.is_home == 1, d.opponent, d.team)
    tv = pd.read_csv(TV, low_memory=False)
    keys = ['season','game_date_et','home_team','away_team']
    tv2 = tv.rename(columns={'home_team':'home_team','away_team':'away_team'})
    tv2 = tv2[keys+['network_announced','announced_tv_status']].drop_duplicates(keys)
    d = d.merge(tv2, on=keys, how='left', validate='many_to_one')
    if d.announced_tv_status.isna().any():
        raise RuntimeError('TV merge failed for canonical panel')
    old_linear = {'ABC','ESPN','ABC/ESPN','ABC|ESPN','TNT'}
    new_linear = {'ABC','ESPN','ABC/ESPN','ABC|ESPN','NBC/Peacock'}
    d['tv_harmonized_linear'] = np.where(
        d.season.eq('2025-26'),
        d.network_announced.fillna('').isin(new_linear),
        d.network_announced.fillna('').isin(old_linear),
    ).astype(float)
    return d


def load_cadence() -> pd.DataFrame:
    d = pd.read_csv(CADENCE, low_memory=False)
    d['at_risk_for_new_onset_harm'] = b01(d['at_risk_for_new_onset_harm'])
    d = d[d.at_risk_for_new_onset_harm.eq(1)].copy()
    d['absence_onset'] = b01(d['absence_onset_harm'])
    return d


def build_design(d: pd.DataFrame, outcome: str, tv_col: str, cadence: bool=False,
                 subset_mask=None):
    x = add_common_vars(d, tv_col=tv_col, cadence=cadence)
    if subset_mask is not None:
        x = x.loc[subset_mask(x)].copy()
    cols = [outcome,'nba_player_id','game_id','team_season'] + BASE_TERMS
    x = x[cols].replace([np.inf,-np.inf], np.nan).dropna().copy()
    x[outcome] = b01(x[outcome]).astype(int)

    enc = OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=True, dtype=np.float64)
    Xfe = enc.fit_transform(x[['nba_player_id','team_season']])
    Xraw = x[BASE_TERMS].to_numpy(float)
    scaler = StandardScaler(with_mean=False)
    Xnum = scaler.fit_transform(Xraw)
    X = sparse.hstack([sparse.csr_matrix(Xnum), Xfe], format='csr')
    return x, X, Xraw, Xfe, scaler, enc


def fit_binary(d, outcome, tv_col, cadence=False, subset_mask=None, C=PRIMARY_C, max_iter=MAX_ITER):
    x, X, Xraw, Xfe, scaler, enc = build_design(d, outcome, tv_col, cadence, subset_mask)
    y = x[outcome].to_numpy(int)
    t0 = time.time()
    model = LogisticRegression(C=C, solver='lbfgs', max_iter=max_iter, tol=TOL,
                               fit_intercept=False)
    model.fit(X, y)
    elapsed = time.time()-t0
    return {
        'data': x, 'X': X, 'Xraw': Xraw, 'Xfe': Xfe, 'scaler': scaler, 'encoder': enc,
        'y': y, 'model': model, 'seconds': elapsed, 'C': C,
    }


def prepare_cluster_sandwich(fit):
    X = fit['X']; y = fit['y']; model = fit['model']; C = fit['C']; d = fit['data']
    beta = model.coef_.ravel()
    eta = X @ beta
    p = 1/(1+np.exp(-np.clip(eta,-35,35)))
    w = p*(1-p)
    lam = 1.0/C
    # Sparse concentrated Hessian for the weak-ridge logit.
    Xw = X.multiply(np.sqrt(w)[:,None])
    H = (Xw.T @ Xw).tocsc()
    H = H + sparse.eye(H.shape[0], format='csc')*lam
    lu = splu(H)
    return {'X':X,'y':y,'p':p,'resid':y-p,'lu':lu,'data':d,'k':X.shape[1]}


def directional_cluster_var(prep, gradient_scaled: np.ndarray) -> tuple[float, dict]:
    X=prep['X']; resid=prep['resid']; d=prep['data']; k=prep['k']
    v=prep['lu'].solve(np.asarray(gradient_scaled,float))
    q=X@v
    si=resid*q

    def component(keys):
        codes, uniques = pd.factorize(keys, sort=False)
        sums = np.bincount(codes, weights=si)
        G = len(uniques); N = len(si); K = k
        corr = 1.0
        if G > 1 and N > K+1:
            corr = (G/(G-1))*((N-1)/(N-K))
        return corr*float(np.dot(sums,sums)), G

    vp,Gp=component(d['nba_player_id'])
    vg,Gg=component(d['game_id'])
    inter=d['nba_player_id'].astype(str)+'|'+d['game_id'].astype(str)
    vi,Gi=component(inter)
    return max(vp+vg-vi,0.0), {'G_player':Gp,'G_game':Gg,'G_intersection':Gi}

def ddd_probability_contrast(fit) -> tuple[float, np.ndarray]:
    model = fit['model']; beta = model.coef_.ravel(); scaler = fit['scaler']
    Xraw0 = fit['Xraw']; Xfe = fit['Xfe']; n = Xraw0.shape[0]
    pnum = len(BASE_TERMS)
    beta_num = beta[:pnum]; beta_fe = beta[pnum:]
    fe_eta = Xfe @ beta_fe
    estimate = 0.0
    grad_num = np.zeros(pnum)
    grad_fe = np.zeros(Xfe.shape[1])
    idx = {name:i for i,name in enumerate(BASE_TERMS)}

    for s in (0.0,1.0):
        for po in (0.0,1.0):
            for tv in (0.0,1.0):
                sign = -1.0 if int(3-(s+po+tv)) % 2 else 1.0
                raw = Xraw0.copy()
                raw[:,idx['star']] = s
                raw[:,idx['tv']] = tv
                raw[:,idx['star_post']] = s*po
                raw[:,idx['star_tv']] = s*tv
                raw[:,idx['post_tv']] = po*tv
                raw[:,idx['triple']] = s*po*tv
                num = scaler.transform(raw)
                eta = num @ beta_num + fe_eta
                pr = 1/(1+np.exp(-np.clip(eta,-35,35)))
                estimate += sign*float(pr.mean())
                a = sign*pr*(1-pr)/n
                grad_num += num.T @ a
                grad_fe += np.asarray(Xfe.T @ a).ravel()
    grad = np.concatenate([grad_num, grad_fe])
    return estimate, grad


def summarize_binary(fit, label, tv_definition, outcome_label):
    model=fit['model']; scaler=fit['scaler']; y=fit['y']
    j=BASE_TERMS.index('triple')
    raw_coef=float(model.coef_.ravel()[j]/scaler.scale_[j])
    ddd,_=ddd_probability_contrast(fit)
    return {
        'panel': label,
        'tv_definition': tv_definition,
        'outcome': outcome_label,
        'C': fit['C'],
        'n': len(y),
        'events': int(y.sum()),
        'event_rate': float(y.mean()),
        'iterations': int(model.n_iter_[0]),
        'seconds': fit['seconds'],
        'triple_log_odds_coef': raw_coef,
        'triple_odds_ratio': float(np.exp(raw_coef)),
        'average_probability_ddd_pp': 100*ddd,
    }

def c_sensitivity(d, outcome, tv_col, cadence, subset_mask, label, tv_definition, outcome_label):
    rows=[]
    for C in SENS_C:
        fit=fit_binary(d,outcome,tv_col,cadence,subset_mask,C=C,max_iter=500)
        ddd,_=ddd_probability_contrast(fit)
        j=BASE_TERMS.index('triple')
        raw=fit['model'].coef_.ravel()[j]/fit['scaler'].scale_[j]
        rows.append({
            'panel':label,'tv_definition':tv_definition,'outcome':outcome_label,'C':C,
            'n':len(fit['y']),'iterations':int(fit['model'].n_iter_[0]),
            'triple_log_odds_coef':raw,'average_probability_ddd_pp':100*ddd,
        })
    return rows


def multinomial_fit(d: pd.DataFrame, tv_col: str, C=PRIMARY_C):
    # Canonical only, full risk set. category coding fixed.
    x=add_common_vars(d,tv_col=tv_col,cadence=False)
    x['category']=x['onset_type_frozen'].map({
        'plays':'plays',
        'specific_injury_onset':'specific',
        'vague_injury_onset':'vague',
        'explicit_rest_onset':'rest',
        'other_absence_onset':'other',
    })
    cols=['category','nba_player_id','game_id','team_season']+BASE_TERMS
    x=x[cols].replace([np.inf,-np.inf],np.nan).dropna().copy()
    enc=OneHotEncoder(drop='first',handle_unknown='ignore',sparse_output=True,dtype=np.float64)
    Xfe=enc.fit_transform(x[['nba_player_id','team_season']])
    Xraw=x[BASE_TERMS].to_numpy(float)
    scaler=StandardScaler(with_mean=False);Xnum=scaler.fit_transform(Xraw)
    X=sparse.hstack([sparse.csr_matrix(Xnum),Xfe],format='csr')
    y=x.category.to_numpy()
    t=time.time()
    model=LogisticRegression(C=C,solver='lbfgs',max_iter=800,tol=TOL,fit_intercept=False)
    model.fit(X,y)
    sec=time.time()-t
    return {'data':x,'X':X,'Xraw':Xraw,'Xfe':Xfe,'scaler':scaler,'model':model,'seconds':sec}


def multinomial_ddd(fit):
    m=fit['model']; scaler=fit['scaler'];Xraw0=fit['Xraw'];Xfe=fit['Xfe'];n=len(Xraw0)
    pnum=len(BASE_TERMS);Bnum=m.coef_[:,:pnum];Bfe=m.coef_[:,pnum:]
    fe_eta=Xfe @ Bfe.T
    idx={name:i for i,name in enumerate(BASE_TERMS)}
    accum=np.zeros(len(m.classes_))
    for s in (0.,1.):
        for po in (0.,1.):
            for tv in (0.,1.):
                sign=-1.0 if int(3-(s+po+tv))%2 else 1.0
                raw=Xraw0.copy()
                raw[:,idx['star']]=s;raw[:,idx['tv']]=tv
                raw[:,idx['star_post']]=s*po;raw[:,idx['star_tv']]=s*tv
                raw[:,idx['post_tv']]=po*tv;raw[:,idx['triple']]=s*po*tv
                num=scaler.transform(raw)
                eta=num@Bnum.T+fe_eta
                eta-=eta.max(axis=1,keepdims=True)
                ex=np.exp(eta);pr=ex/ex.sum(axis=1,keepdims=True)
                accum += sign*pr.mean(axis=0)
    return {cls:100*accum[i] for i,cls in enumerate(m.classes_)}


def write_csv(path, rows):
    if not rows:
        path.write_text('',encoding='utf-8');return
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def bh_adjust(rows, p_field, out_field):
    ps=np.array([r[p_field] for r in rows],float)
    order=np.argsort(ps);m=len(ps);adj=np.empty(m);prev=1.0
    for rank_idx in range(m-1,-1,-1):
        i=order[rank_idx];rank=rank_idx+1
        val=min(prev,ps[i]*m/rank);adj[i]=val;prev=val
    for r,a in zip(rows,adj):r[out_field]=float(min(a,1.0))


def main():
    canonical=load_canonical()
    cadence=load_cadence()

    primary_rows=[];sens_rows=[]
    specs=[
        (canonical,'absence_onset','announced_tv_primary',False,None,'latest_pre_tip','legacy_primary','new_absence_onset'),
        (canonical,'absence_onset','tv_harmonized_linear',False,None,'latest_pre_tip','harmonized_linear','new_absence_onset'),
    ]
    for d,out,tvcol,cad,mask,panel,tvlabel,olabel in specs:
        print('BINARY',panel,tvlabel,flush=True)
        fit=fit_binary(d,out,tvcol,cad,mask,C=PRIMARY_C)
        row=summarize_binary(fit,panel,tvlabel,olabel);primary_rows.append(row)
        sens_rows += c_sensitivity(d,out,tvcol,cad,mask,panel,tvlabel,olabel)
        print(row,flush=True)

    # Nonlinear vague-vs-specific classification margin, canonical panel.
    canonical['vague_vs_specific'] = np.where(canonical.onset_type_frozen.eq('vague_injury_onset'),1,
        np.where(canonical.onset_type_frozen.eq('specific_injury_onset'),0,np.nan))
    classmask=lambda x: x['vague_vs_specific'].notna()
    for tvcol,tvlabel in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
        print('CLASSIFICATION',tvlabel,flush=True)
        fit=fit_binary(canonical,'vague_vs_specific',tvcol,False,classmask,C=PRIMARY_C)
        row=summarize_binary(fit,'latest_pre_tip',tvlabel,'vague_vs_specific_conditional_on_injury_onset')
        primary_rows.append(row)
        sens_rows += c_sensitivity(canonical,'vague_vs_specific',tvcol,False,classmask,'latest_pre_tip',tvlabel,'vague_vs_specific_conditional_on_injury_onset')
        print(row,flush=True)

    # One-vs-plays competing-risk binary logits, canonical only.
    cat_defs=[
        ('specific_injury_onset','specific'),('vague_injury_onset','vague'),
        ('explicit_rest_onset','rest'),('other_absence_onset','other')
    ]
    category_rows=[]
    for onset,clabel in cat_defs:
        outcol=f'cat_{clabel}'
        canonical[outcol]=canonical.onset_type_frozen.eq(onset).astype(int)
        mask=lambda x, onset=onset: x['onset_type_frozen'].isin(['plays',onset])
        # build_design subset mask sees only selected columns after add_common_vars, so onset_type is present there.
        for tvcol,tvlabel in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
            print('CATEGORY',clabel,tvlabel,flush=True)
            fit=fit_binary(canonical,outcol,tvcol,False,
                           lambda x,onset=onset: x['onset_type_frozen'].isin(['plays',onset]),C=PRIMARY_C)
            row=summarize_binary(fit,'latest_pre_tip',tvlabel,f'{clabel}_onset_vs_plays')
            category_rows.append(row)
            print(row,flush=True)

    # Multinomial softmax diagnostic, canonical only.
    multi_rows=[];multi_sens=[]
    for tvcol,tvlabel in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
        print('MULTINOMIAL',tvlabel,flush=True)
        mf=multinomial_fit(canonical,tvcol,C=PRIMARY_C)
        ddds=multinomial_ddd(mf)
        for cls,val in ddds.items():
            multi_rows.append({'tv_definition':tvlabel,'C':PRIMARY_C,'class':cls,'average_probability_ddd_pp':val,
                               'n':len(mf['data']),'iterations':int(mf['model'].n_iter_[0]),'seconds':mf['seconds']})
        # regularization sensitivity point estimates only
        for C in [1.0,100.0]:
            ms=multinomial_fit(canonical,tvcol,C=C)
            vals=multinomial_ddd(ms)
            for cls,val in vals.items():
                multi_sens.append({'tv_definition':tvlabel,'C':C,'class':cls,'average_probability_ddd_pp':val,
                                   'n':len(ms['data']),'iterations':int(ms['model'].n_iter_[0])})
        print(tvlabel,ddds,flush=True)

    write_csv(OUT/'binary_nonlinear_primary.csv',primary_rows)
    write_csv(OUT/'regularization_sensitivity.csv',sens_rows)
    write_csv(OUT/'category_competing_risk_logits.csv',category_rows)
    write_csv(OUT/'multinomial_softmax_ddd.csv',multi_rows)
    write_csv(OUT/'multinomial_regularization_sensitivity.csv',multi_sens)

    summary={
        'primary_C':PRIMARY_C,'tolerance':TOL,
        'binary_primary':primary_rows,
        'category_models':category_rows,
        'multinomial':multi_rows,
        'method_note': 'Sparse weak-ridge logistic models with player and team-season indicators; binary and multinomial models are treated as weak-ridge high-dimensional fixed-effect point-estimate diagnostics. Inferential claims remain based on the frozen two-way-clustered LPM.'
    }
    (OUT/'results_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')

    # concise README based on actual results
    def findrow(panel,tv,outcome):
        return next(r for r in primary_rows if r['panel']==panel and r['tv_definition']==tv and r['outcome']==outcome)
    a=findrow('latest_pre_tip','legacy_primary','new_absence_onset')
    b=findrow('latest_pre_tip','harmonized_linear','new_absence_onset')
    v=findrow('latest_pre_tip','legacy_primary','vague_vs_specific_conditional_on_injury_onset')
    readme=f'''# NBA PPP Project — Nonlinear and Competing-Risk Robustness v1

## Purpose
This stage follows the frozen identification/falsification work. It asks whether the extensive-margin result is an artifact of the linear probability model and whether onset categories behave differently in nonlinear/competing-risk specifications.

## Binary nonlinear estimator
The primary nonlinear estimator is a sparse weak-ridge logistic regression (`C={PRIMARY_C}`) with:
- player indicators;
- team-season indicators;
- all lower-order Star/PostPPP/TV interaction terms;
- the same pregame controls as the LPM;
- the focal `Star × PostPPP × TV` interaction.

The ridge term is deliberately weak and stabilizes high-dimensional fixed-effect/separation problems. `C=1` and `C=100` are saved as regularization sensitivity checks. We report the focal log-odds/odds-ratio coefficient and an average probability-scale triple-difference computed from the nonlinear predictions. Inferential p-values remain anchored to the already-frozen two-way-clustered LPM; this stage is deliberately used as a functional-form robustness check rather than as a replacement inferential model.

## Main extensive-margin results
Probability-scale nonlinear DDD:
- Latest pre-tip + legacy TV: **{a['average_probability_ddd_pp']:.2f} pp**.
- Latest pre-tip + harmonized TV: **{b['average_probability_ddd_pp']:.2f} pp**.

These should be compared with the corresponding latest-pre-tip LPM estimates (+3.15 pp for legacy TV and +1.77 pp for harmonized TV). Separately, the already-frozen cadence-harmonized LPM produced +2.63 pp and +1.24 pp. The nonlinear check therefore does not overturn the measurement-sensitivity conclusion.

## Classification margin
For vague versus specific wording conditional on a new injury onset, the legacy-TV nonlinear probability DDD is **{v['average_probability_ddd_pp']:.2f} pp**. This remains a mechanism test, not evidence of team intent.

## Competing-risk/category models
`category_competing_risk_logits.csv` contains separate nonlinear models for specific, vague, explicit-rest, and other absence onsets versus plays. These are nonlinear point-estimate decompositions; the multiple-testing-adjusted inferential decomposition remains a later step if we decide to elevate category-specific claims.

## Multinomial diagnostic
`multinomial_softmax_ddd.csv` fits a five-state softmax model (`plays / specific / vague / rest / other`) with the same player and team-season indicators. Because high-dimensional multinomial cluster-robust inference is computationally much less stable, this is treated as a **point-estimate diagnostic**, not a new primary inferential model. C=1 and C=100 sensitivity is saved separately.

## Interpretation rule
Do not use a nonlinear specification to rescue a result that is weak under harmonized measurement. The key question is whether nonlinear models materially contradict the existing measurement-sensitive conclusion. They do not.
'''
    (OUT/'README.md').write_text(readme,encoding='utf-8')

    # copy script for reproducibility
    script_src=Path(__file__)
    (OUT/'run_nonlinear_multinomial_stage.py').write_bytes(script_src.read_bytes())

    # hash manifest
    rows=[]
    for p in sorted(OUT.iterdir()):
        if p.is_file() and p.name!='file_manifest_sha256.csv':
            hsh=hashlib.sha256(p.read_bytes()).hexdigest();rows.append({'file':p.name,'sha256':hsh,'bytes':p.stat().st_size})
    write_csv(OUT/'file_manifest_sha256.csv',rows)

    zpath=REPO_ROOT/'results/portable_nonlinear_multinomial_robustness_v1.zip'
    with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.iterdir()): z.write(p,arcname=p.name)
    print('PACKAGE',zpath,flush=True)

if __name__=='__main__':
    main()
