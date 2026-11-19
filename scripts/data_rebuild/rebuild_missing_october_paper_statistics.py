#!/usr/bin/env python3
"""Recreate missing October manuscript descriptives and paired home/road model.

Faithful to the published cadence-harmonized definitions in October 2026.
Freeze gate reproduces author-reported cells before a corrected variant is accepted.
Never mutates original panel or historical manuscript.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.linalg as la
from scipy.sparse import csr_matrix
from scipy.stats import norm
from statsmodels.api import OLS
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups

FROZEN_CSV_SHA='3c161f954a217fe6996934bd86dc027a9b6968a868097052af21ac11a6d07eac'
CORRECTED_CSV_SHA='2409b501cd89f9b7d6a92d5cacad7c602de67aa903e5b05bd2c481618745cd67'
HOME_CONTROLS=['back_to_back','three_games_in_four_days','four_games_in_six_days',
 'travel_1000','absolute_timezone_shift_hours','road_trip_game_number',
 'minutes10_100','games_before_10','dist65_10']
TERMS=['star','tv','starpost','startv','posttv','triple']+HOME_CONTROLS


def uncompressed_sha(path):
    import gzip
    hasher=hashlib.sha256()
    with gzip.open(path,'rb') as source:
        for block in iter(lambda:source.read(1<<20),b''):
            hasher.update(block)
    return hasher.hexdigest()


def prepare(panel):
    data=panel.copy()
    if data.player_team_game_id.duplicated().any():
        raise ValueError('Duplicate player-team-game IDs')
    if len(data)!=248778 or data.game_id.nunique()!=7230:
        raise ValueError('Unexpected canonical cadence panel size')
    data=data.sort_values(['season','team','nba_player_id','team_game_number','game_id']).copy()
    grouped=data.groupby(['season','team','nba_player_id'],sort=False)
    data['next_game']=grouped.team_game_number.shift(-1)
    data['next_absent']=grouped.absence_now_harm.shift(-1)
    data['next_obs']=grouped.report_outcome_observed.shift(-1)
    data['can_see_next']=((data.next_game==data.team_game_number+1)&
                          (data.next_obs==True)).astype(bool)
    data['onegame']=((data.absence_onset_harm==True)&data.can_see_next&
                     (data.next_absent==False)).astype(bool)
    data['longer']=((data.absence_onset_harm==True)&data.can_see_next&
                    (data.next_absent==True)).astype(bool)
    return data


def descriptive(data):
    risk=data[data.at_risk_for_new_onset_harm]
    onset=(risk.groupby(['star_PPP_it','postPPP','announced_tv_primary'],observed=True)
        .agg(at_risk=('player_team_game_id','size'),onsets=('absence_onset_harm','sum'))
        .reset_index())
    onset['onset_rate_pct']=100*onset.onsets/onset.at_risk
    prevalence=(data[data.report_outcome_observed]
        .groupby(['star_PPP_it','postPPP'],observed=True)
        .agg(observed=('player_team_game_id','size'),absent=('absence_now_harm','sum'))
        .reset_index())
    prevalence['absent_share_pct']=100*prevalence.absent/prevalence.observed
    eligible=risk[(~risk.absence_onset_harm)|risk.can_see_next]
    home=(eligible.groupby(['star_PPP_it','postPPP','is_home'],observed=True)
        .agg(at_risk=('player_team_game_id','size'),onegame_onsets=('onegame','sum'))
        .reset_index())
    home['onegame_rate_pct']=100*home.onegame_onsets/home.at_risk
    rates=onset.set_index(['star_PPP_it','postPPP','announced_tv_primary']).onset_rate_pct
    gap=lambda post: (rates[True,post,True]-rates[False,post,True]
                      -rates[True,post,False]+rates[False,post,False])
    raw_triple=float(gap(True)-gap(False))
    return onset,prevalence,home,raw_triple


def spell_lengths(data):
    """Count consecutive observed absent team-games after each known onset.

    A spell is completed only if the next consecutive observed team-game is
    available. Missing/incomplete observation, season/team boundary, or end of
    the team-season is right censoring; duration is then only a lower bound.
    """
    data=data.reset_index(drop=True)
    group=data.groupby(['season','team','nba_player_id'],sort=False).ngroup().to_numpy()
    tnum=data.team_game_number.to_numpy()
    absent=data.absence_now_harm.to_numpy(dtype=bool)
    seen=data.report_outcome_observed.to_numpy(dtype=bool)
    onset=data.absence_onset_harm.to_numpy(dtype=bool)
    star=data.star_PPP_it.to_numpy(dtype=bool)
    post=data.postPPP.to_numpy(dtype=bool)
    keys=data.player_team_game_id.to_numpy()
    episodes=[]
    for i in np.flatnonzero(onset):
        j=i; length=1; completed=False
        while (j+1<len(data) and group[j+1]==group[j] and
               tnum[j+1]==tnum[j]+1 and seen[j+1]):
            if not absent[j+1]:
                completed=True
                break
            length+=1
            j+=1
        episodes.append({'onset_id':str(keys[i]),'star':bool(star[i]),
                         'post':bool(post[i]),'observed_games':length,
                         'completed':completed})
    spells=pd.DataFrame.from_records(episodes)
    grouped=[]
    for (star,post),slice_ in spells.groupby(['star','post'],observed=True):
        good=slice_[slice_.completed]
        censored=slice_[~slice_.completed]
        grouped.append({'star':bool(star),'post':bool(post),
            'onsets':len(slice_),'completed':len(good),'right_censored':len(censored),
            'completed_mean_games':float(good.observed_games.mean()),
            'completed_median_games':float(good.observed_games.median()),
            'completed_onegame_pct':float(100*(good.observed_games==1).mean()),
            'censored_observed_mean_lower_bound':float(censored.observed_games.mean())})
    return pd.DataFrame(grouped),spells


def paired_home_model(data):
    """Original October run_home.py FE, controls and 2-way clusters.

    Dependent variable is onegame minus longer on the exact same observation;
    this directly estimates the paired contrast with the outcomes' covariance.
    """
    d=data.copy()
    d['teamseason']=d.team+'|'+d.season
    for c in ['star_PPP_it','postPPP','is_home','back_to_back',
              'three_games_in_four_days','four_games_in_six_days']:
        d[c]=d[c].astype(float)
    d['travel_1000']=d.travel_km_since_previous_game/1000
    d['minutes10_100']=d.minutes_sum_prior_10_roster_games_harm/100
    d['games_before_10']=d.games_played_before_game_harm/10
    d['dist65_10']=d.dist_to_65_before_game_harm/10
    risk=d[d.at_risk_for_new_onset_harm].copy()
    eligible=risk[(~risk.absence_onset_harm)|risk.can_see_next].copy()
    eligible['paired']=eligible.onegame.astype(float)-eligible.longer.astype(float)
    eligible['star']=eligible.star_PPP_it
    eligible['tv']=eligible.is_home
    eligible['starpost']=eligible.star*eligible.postPPP
    eligible['startv']=eligible.star*eligible.tv
    eligible['posttv']=eligible.postPPP*eligible.tv
    eligible['triple']=eligible.star*eligible.postPPP*eligible.tv
    groups=['nba_player_id','teamseason','game_id']
    cols=list(dict.fromkeys(['paired','nba_player_id','game_id']+groups+TERMS))
    df=eligible[cols].replace([np.inf,-np.inf],np.nan).dropna().copy()
    values=df[['paired']+TERMS].to_numpy(float)
    operators=[]
    for g in groups:
        codes,levels=pd.factorize(df[g],sort=False)
        mat=csr_matrix((np.ones(len(codes)),(np.arange(len(codes)),codes)),
                       shape=(len(codes),len(levels)))
        count=np.asarray(mat.sum(axis=0)).ravel()
        operators.append((mat,count))
    converged=False
    for iteration in range(240):
        if iteration%5==0: old=values.copy()
        for mat,count in operators:
            values-=mat@((mat.T@values)/count[:,None])
        if iteration%5==0 and np.max(np.abs(values-old))<1e-8:
            converged=True
            break
    if not converged:
        raise RuntimeError('Original three-way FE demeaning did not converge')
    X=values[:,1:]
    survives=(X*X).sum(0)>1e-12
    X=X[:,survives]
    names=[term for term,keep in zip(TERMS,survives) if keep]
    Q,R,piv=la.qr(X,mode='economic',pivoting=True,check_finite=False)
    rank=int(np.sum(np.abs(np.diag(R))>1e-9*abs(R[0,0])))
    keep=np.sort(piv[:rank]);X=X[:,keep];names=[names[i] for i in keep]
    if 'triple' not in names:
        raise RuntimeError('Triple interaction dropped from paired model')
    model=OLS(values[:,0],X).fit()
    clusters_player=pd.factorize(df.nba_player_id)[0]
    clusters_game=pd.factorize(df.game_id)[0]
    variance,_,_=cov_cluster_2groups(model,clusters_player,clusters_game,use_correction=True)
    i=names.index('triple')
    beta=float(model.params[i]);se=float(np.sqrt(max(0,variance[i,i])))
    if not se>0:
        raise RuntimeError('Invalid paired regression standard error')
    return {'n':int(len(df)),'estimate_pp':100*beta,'se_pp':100*se,
            'low_pp':100*(beta-1.96*se),'high_pp':100*(beta+1.96*se),
            'p':float(2*norm.sf(abs(beta/se))), 'iterations':int(iteration+1),
            'converged':converged,'rank':int(rank)}


def compute(path):
    df=prepare(pd.read_csv(path,low_memory=False))
    onset,prev,home,triple=descriptive(df)
    duration,spells=spell_lengths(df)
    model=paired_home_model(df)
    result={'onset_cells':onset.to_dict('records'),
            'prevalence_cells':prev.to_dict('records'),
            'home_onegame_cells':home.to_dict('records'),
            'duration':duration.to_dict('records'),
            'raw_triple_difference_pp':triple,
            'paired_home_onegame_minus_longer':model,
            'totals':{'rows':len(df),'risk_rows':int(df.at_risk_for_new_onset_harm.sum()),
                      'onsets':int(df.absence_onset_harm.sum()),
                      'observed_rows':int(df.report_outcome_observed.sum()),
                      'completed_spells':int(spells.completed.sum())}}
    return result


def verify_frozen(result):
    if result['totals']['onsets']!=12731 or result['totals']['risk_rows']!=180664:
        raise RuntimeError('Frozen onset/risk benchmark mismatch')
    expected={(True,False):(826,713,2.629734,63.534362),
              (True,True):(809,702,2.703704,64.672365),
              (False,False):(4791,4119,3.742413,42.437485),
              (False,True):(6305,5590,3.616995,46.618962)}
    for row in result['duration']:
        count,done,avg,one=expected[row['star'],row['post']]
        if (row['onsets']!=count or row['completed']!=done
            or abs(row['completed_mean_games']-avg)>1e-4
            or abs(row['completed_onegame_pct']-one)>1e-4):
            raise RuntimeError(f'Frozen manuscript duration not reproduced: {row}')
    if abs(result['raw_triple_difference_pp']-1.9199065788012053)>1e-7:
        raise RuntimeError('Frozen manuscript raw triple mismatch')
    p=result['paired_home_onegame_minus_longer']
    if (p['n']!=180087 or abs(p['estimate_pp']-1.6640489534898748)>1e-5
        or abs(p['se_pp']-1.1661649666433418)>1e-5):
        raise RuntimeError('Frozen published paired home/road estimate not reproduced')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen-panel',type=Path,required=True)
    parser.add_argument('--corrected-panel',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not args.frozen_panel.is_file():raise FileNotFoundError(args.frozen_panel)
    digest=uncompressed_sha(args.frozen_panel)
    if digest!=FROZEN_CSV_SHA:raise RuntimeError(f'Unexpected frozen cadence panel {digest}')
    frozen=compute(args.frozen_panel)
    verify_frozen(frozen)
    report={'scope':'Manuscript descriptive rates, completed-spell durations, and paired onegame-minus-longer home/road regression',
            'frozen_csv_sha256':digest,'frozen':frozen,'frozen_manuscript_identity_passed':True,
            'method':'Original October cadence-harmonized report/risk definitions; paired 3-way FE cluster-by-player+game specification'}
    if args.corrected_panel:
        corrected_sha=uncompressed_sha(args.corrected_panel)
        if corrected_sha!=CORRECTED_CSV_SHA:raise RuntimeError(f'Unexpected corrected panel {corrected_sha}')
        report['corrected_csv_sha256']=corrected_sha
        report['corrected']=compute(args.corrected_panel)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS frozen identity, paired estimate',frozen['paired_home_onegame_minus_longer'])
    if 'corrected' in report:
        print('PASS corrected paired estimate',report['corrected']['paired_home_onegame_minus_longer'])
        print('Raw DDD frozen/corrected',frozen['raw_triple_difference_pp'],report['corrected']['raw_triple_difference_pp'])

if __name__=='__main__':main()
