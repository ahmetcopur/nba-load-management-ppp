from pathlib import Path
import re, math, unicodedata, json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm
from scipy.sparse import csr_matrix
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups

ROOT=Path('/mnt/data/nba_continue')
SELROOT=ROOT/'cadence_work/selector/nba_canonical_snapshot_selector_v1'
OUT=ROOT/'cadence_harmonized_results'; OUT.mkdir(exist_ok=True)
BASE=ROOT/'analysis/nba_player_game_analysis_ready_v1/player_game_panel_analysis_ready.csv.gz'
XW=ROOT/'cadence_2025/player_crosswalk_final.csv'
SEASONS=['2020-21','2021-22','2022-23','2023-24','2024-25','2025-26']

def clean(v):
    if v is None or (isinstance(v,float) and np.isnan(v)): return ''
    return re.sub(r'\s+',' ',str(v)).strip()
def norm(v):
    s=unicodedata.normalize('NFKD',clean(v)).encode('ascii','ignore').decode().lower()
    s=re.sub(r'[^a-z0-9]+',' ',s); return re.sub(r'\s+',' ',s).strip()
def norm_team(v):
    s=norm(v); return 'los angeles clippers' if s=='la clippers' else s
def asbool(s):
    if s.dtype==bool:return s
    return s.astype(str).str.lower().map({'true':True,'false':False,'1':True,'0':False,'1.0':True,'0.0':False}).fillna(False)

def basename_series(s): return s.fillna('').map(lambda x:Path(str(x)).name)

print('loading base',flush=True)
base=pd.read_csv(BASE,low_memory=False)
base['nba_player_id']=pd.to_numeric(base.nba_player_id,errors='raise').astype('Int64')
base['team_norm']=base.team.map(norm_team)
for c in ['from_boxscore_roster','played_bool','starter','coach_decision_dnp','star_PPP_it','postPPP','cup_game','announced_tv_primary','announced_nba_tv','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back']:
    if c in base: base[c]=asbool(base[c])
# Start from official boxscore roster only; canonical-specific report-only additions are discarded.
roster=base[base.from_boxscore_roster].copy()
assert len(roster)==248571, len(roster)
# Actual fixture map, correcting source-schedule anomalies.
game_map=(base[['season','source_match_number','game_id']].drop_duplicates()
          .drop_duplicates(['season','source_match_number']))
assert not game_map.duplicated(['season','source_match_number']).any()
role_map=base[['game_id','team_role','team','opponent']].drop_duplicates(['game_id','team_role'])

# Selected snapshot maps.
selparts=[]
for s in SEASONS:
    d=pd.read_csv(SELROOT/f'{s}_game_snapshot_join_harmonized_canonical.csv')
    d['source_match_number']=pd.to_numeric(d['Match Number'],errors='raise').astype(int)
    d=d.merge(game_map,on=['season','source_match_number'],how='left',validate='one_to_one',suffixes=('_fd',''))
    assert d['game_id'].notna().all()
    d['report_matchup_norm']=d['matchup_norm'].astype(str)
    # Known upstream FixtureDownload swaps already repaired in the canonical panel.
    if s=='2021-22':
        d.loc[d.source_match_number.eq(430),'report_matchup_norm']='CHI@TOR'
        d.loc[d.source_match_number.eq(784),'report_matchup_norm']='MIA@TOR'
    selparts.append(d[['season','source_match_number','game_id','report_matchup_norm','snapshot_basename','published_timestamp_utc','minutes_before_tip','qc_selected_within_30m']])
selmap=pd.concat(selparts,ignore_index=True)
assert len(selmap)==7230
selmap.to_csv(OUT/'harmonized_game_snapshot_map.csv',index=False)

# Team-game status: canonical selector where available, otherwise season S4 output.
status_files={
 '2020-21':SELROOT/'2020-21_team_game_status_harmonized_canonical.csv',
 '2021-22':SELROOT/'2021-22_team_game_status_harmonized_canonical.csv',
 '2022-23':ROOT/'cadence_work/s4/2022-23/team_game_final_pre_tip_status_harmonized.csv',
 '2023-24':ROOT/'cadence_work/s4/2023-24/team_game_final_pre_tip_status_harmonized.csv',
 '2024-25':SELROOT/'2024-25_team_game_status_harmonized_canonical.csv',
 '2025-26':SELROOT/'2025-26_team_game_status_harmonized_canonical.csv',
}
status=[]
for s,p in status_files.items():
    x=pd.read_csv(p); x['season']=s
    # FD game_id -> source match number via selected map.
    fd=selparts[SEASONS.index(s)][['game_id_fd','source_match_number','game_id']] if 'game_id_fd' in selparts[SEASONS.index(s)].columns else None
    # selparts no longer retained game_id_fd after subset; parse FD suffix safely.
    x['source_match_number']=pd.to_numeric(x['game_id'].astype(str).str.extract(r'(\d+)$')[0],errors='raise').astype(int)
    x=x.drop(columns=['game_id']).merge(game_map[game_map.season.eq(s)],on=['season','source_match_number'],how='left',validate='many_to_one')
    x=x.drop(columns=[c for c in ['team','team_norm'] if c in x.columns])
    x=x.merge(role_map,on=['game_id','team_role'],how='left',validate='many_to_one')
    x['team_norm']=x.team.map(norm_team)
    x['usable_submitted_status']=asbool(x['usable_submitted_status'])
    x['inferred_no_listed_players']=asbool(x['inferred_no_listed_players']) if 'inferred_no_listed_players' in x else False
    status.append(x[['season','game_id','team_role','team','team_norm','team_final_status','usable_submitted_status','inferred_no_listed_players','minutes_before_tip']])
team_status=pd.concat(status,ignore_index=True)
assert len(team_status)==14460, len(team_status)
assert not team_status.duplicated(['game_id','team_norm']).any()
team_status.to_csv(OUT/'harmonized_team_game_report_status.csv',index=False)

# Parsed snapshot sources.
parsed_paths={
 '2020-21':ROOT/'cadence_work/season_parsed/2020-21/s1_snapshot_rows_corrected.csv',
 '2021-22':ROOT/'cadence_work/season_parsed/2021-22/s1_snapshot_rows_harmonized.csv',
 '2022-23':ROOT/'cadence_work/season_parsed/2022-23/s1_snapshot_rows_regular_season.csv',
 '2023-24':ROOT/'cadence_work/season_parsed/2023-24/audit_2023_24_pre_s4_outputs/s1_snapshot_rows_regular_season.csv',
 '2024-25':ROOT/'cadence_work/season_parsed/2024-25/s1_snapshot_rows_regular_season_real.csv',
 '2025-26':ROOT/'cadence_work/season_parsed/2025-26/s1_snapshot_rows_harmonized_selected.csv',
}
selected_rows=[]
for s,p in parsed_paths.items():
    print('selecting rows',s,flush=True)
    x=pd.read_csv(p,low_memory=False)
    x['snapshot_basename']=basename_series(x['source_file'])
    x['matchup_norm']=x['matchup_norm'].fillna('').astype(str)
    m=selmap[selmap.season.eq(s)]
    # Join selected snapshot and literal matchup to its actual game.
    y=x.merge(m[['game_id','source_match_number','report_matchup_norm','snapshot_basename','published_timestamp_utc','minutes_before_tip','qc_selected_within_30m']],
              left_on=['snapshot_basename','matchup_norm'],right_on=['snapshot_basename','report_matchup_norm'],how='inner',validate='many_to_many')
    # Same PDF+matchup should correspond to one scheduled game in a season.
    dupmap=m.groupby(['snapshot_basename','report_matchup_norm']).game_id.nunique()
    if (dupmap>1).any():
        # Rare same matchup selecting same report on distinct dates would require game-date disambiguation.
        bad=dupmap[dupmap>1]
        raise RuntimeError(f'{s}: ambiguous snapshot+matchup mappings: {bad.head()}')
    y['season']=s; y['team_norm']=y.team_norm.fillna('').map(norm_team)
    selected_rows.append(y)
selected=pd.concat(selected_rows,ignore_index=True)
for c in ['player_name','current_status','reason']:
    selected[c]=selected[c].fillna('').map(clean)
# Remove exact duplicates only.
selected=selected.drop_duplicates(['season','game_id','team_norm','player_name','current_status','reason','team_submission_status'])
selected.to_csv(OUT/'harmonized_selected_report_rows_all.csv.gz',index=False,compression='gzip')
print('selected report rows',len(selected),flush=True)

# Resolve player IDs via frozen crosswalk.
xw=pd.read_csv(XW,low_memory=False)
xw['team_norm']=xw.team_norm.map(norm_team); xw['player_name']=xw.player_name.fillna('').map(clean)
xkey=xw[['season','team_norm','player_name','nba_player_id','nba_player_name','resolution_method','resolution_status']].drop_duplicates()
pr=selected[selected.player_name.ne('')].copy()
pr=pr.merge(xkey,on=['season','team_norm','player_name'],how='left',validate='many_to_one')
# Some harmonized checkpoints surface historical report-name variants that were not
# present in the frozen *canonical-snapshot* crosswalk. Resolve them using the same
# reviewed fallbacks used in the original identity pipeline, without fuzzy matching.
def flip_last_first(v):
    s=clean(v)
    if ',' in s:
        a,b=s.split(',',1)
        return clean(b)+' '+clean(a)
    return s

# Fallback 1: identities already observed in the canonical final panel under exactly
# the same report name, season, and team. This is the strongest fallback because it
# reuses a previously resolved report-row identity.
canon_alias=(base.loc[base.report_player_name.notna(),
                      ['season','team_norm','report_player_name','nba_player_id','nba_player_name']]
             .copy())
canon_alias['player_name']=canon_alias.report_player_name.map(clean)
canon_alias=canon_alias.drop(columns='report_player_name').drop_duplicates()
counts=canon_alias.groupby(['season','team_norm','player_name']).nba_player_id.nunique()
canon_alias=canon_alias.merge(counts.rename('_n'),on=['season','team_norm','player_name'])
canon_alias=canon_alias[canon_alias._n.eq(1)].drop(columns='_n').drop_duplicates(['season','team_norm','player_name'])
need=pr.nba_player_id.isna()
if need.any():
    z=pr.loc[need,['season','team_norm','player_name']].merge(
        canon_alias,on=['season','team_norm','player_name'],how='left',validate='many_to_one')
    pr.loc[need,'nba_player_id']=z.nba_player_id.to_numpy()
    pr.loc[need,'nba_player_name']=z.nba_player_name.to_numpy()
    pr.loc[need & pr.nba_player_id.notna(),'resolution_method']='canonical_report_alias'
    pr.loc[need & pr.nba_player_id.notna(),'resolution_status']='resolved'

# Fallback 2: reviewed global alias table from the original project. Match only when
# a normalized report name maps uniquely to one NBA player ID.
alias_path=ROOT/'cadence_work/player_alias_table.csv'
if alias_path.exists() and pr.nba_player_id.isna().any():
    a=pd.read_csv(alias_path)
    a['name_norm']=a.report_full_name.map(norm)
    ac=a.groupby('name_norm').nba_player_id.nunique()
    a=a.merge(ac.rename('_n'),on='name_norm')
    a=a[a._n.eq(1)][['name_norm','nba_player_id','nba_player_name']].drop_duplicates('name_norm')
    need=pr.nba_player_id.isna()
    tmp=pr.loc[need,['player_name']].copy()
    tmp['name_norm']=tmp.player_name.map(lambda x:norm(flip_last_first(x)))
    z=tmp.merge(a,on='name_norm',how='left',validate='many_to_one')
    pr.loc[need,'nba_player_id']=z.nba_player_id.to_numpy()
    pr.loc[need,'nba_player_name']=z.nba_player_name.to_numpy()
    pr.loc[need & pr.nba_player_id.notna(),'resolution_method']='reviewed_alias_table'
    pr.loc[need & pr.nba_player_id.notna(),'resolution_status']='resolved'

# Fallback 3: exact normalized First Last name within the season-team official
# boxscore roster, again only where the mapping is unique.
if pr.nba_player_id.isna().any():
    rr=roster[['season','team_norm','nba_player_id','nba_player_name']].drop_duplicates().copy()
    rr['name_norm']=rr.nba_player_name.map(norm)
    rc=rr.groupby(['season','team_norm','name_norm']).nba_player_id.nunique()
    rr=rr.merge(rc.rename('_n'),on=['season','team_norm','name_norm'])
    rr=rr[rr._n.eq(1)].drop(columns='_n').drop_duplicates(['season','team_norm','name_norm'])
    need=pr.nba_player_id.isna()
    tmp=pr.loc[need,['season','team_norm','player_name']].copy()
    tmp['name_norm']=tmp.player_name.map(lambda x:norm(flip_last_first(x)))
    z=tmp.merge(rr,on=['season','team_norm','name_norm'],how='left',validate='many_to_one')
    pr.loc[need,'nba_player_id']=z.nba_player_id.to_numpy()
    pr.loc[need,'nba_player_name']=z.nba_player_name.to_numpy()
    pr.loc[need & pr.nba_player_id.notna(),'resolution_method']='unique_team_roster_name'
    pr.loc[need & pr.nba_player_id.notna(),'resolution_status']='resolved'

missing=pr[pr.nba_player_id.isna()].copy()
missing.to_csv(OUT/'harmonized_unmatched_report_players.csv',index=False)
print('unmatched player rows',len(missing),'unique names',missing[['season','team_norm','player_name']].drop_duplicates().shape[0],flush=True)
if len(missing):
    raise RuntimeError('Identity fallbacks did not resolve all harmonized report player rows; inspect output.')
pr['nba_player_id']=pd.to_numeric(pr.nba_player_id,errors='raise').astype('Int64')
pr=pr.drop_duplicates(['game_id','team_norm','nba_player_id'])
pr.to_csv(OUT/'harmonized_selected_report_player_rows.csv.gz',index=False,compression='gzip')

# Add harmonized report-only players beyond the official boxscore roster.
keys=['game_id','team_norm','nba_player_id']
existing=roster[keys].drop_duplicates().assign(_in_roster=True)
extras=pr.merge(existing,on=keys,how='left')
extras=extras[extras._in_roster.isna()].copy()
print('harmonized report-only additions',len(extras),flush=True)
# Template team-game covariates from a boxscore roster row.
template=(roster.sort_values('nba_player_id').drop_duplicates(['game_id','team_norm']).copy())
extra_rows=[]
# player-season status lookup for star fields / name metadata.
playerseason=base.sort_values('game_date_et').drop_duplicates(['season','nba_player_id'],keep='last').set_index(['season','nba_player_id'])
for r in extras.itertuples(index=False):
    t=template[(template.game_id==r.game_id)&(template.team_norm==r.team_norm)]
    if t.empty: raise RuntimeError(f'no template for {r.game_id} {r.team_norm}')
    row=t.iloc[0].copy()
    # Clear player-specific boxscore/report fields.
    row['nba_player_id']=r.nba_player_id; row['nba_player_name']=r.nba_player_name; row['position']=''
    row['from_boxscore_roster']=False; row['boxscore_player_status']=''; row['played_bool']=False; row['starter']=False
    row['minutes_played']=0.0; row['points']=np.nan; row['not_playing_reason']=''; row['not_playing_description']=''; row['coach_decision_dnp']=False
    row['player_game_id']=str(r.game_id)+'|'+str(r.nba_player_id)
    row['player_team_game_id']=str(r.game_id)+'|'+str(row['team'])+'|'+str(r.nba_player_id)
    ps=playerseason.loc[(r.season,r.nba_player_id)] if (r.season,r.nba_player_id) in playerseason.index else None
    if ps is not None:
        for c in ['star_prior_all_star_3yr','star_prior_all_nba_3yr','star_at_opening_night','current_season_all_star','all_star_game_date','current_all_star_effective_date','prior_award_seasons','star_status_basis']:
            if c in row.index: row[c]=ps[c]
        # Star dynamic status on this game date.
        opening=bool(ps.get('star_at_opening_night',False))
        eff=pd.to_datetime(ps.get('current_all_star_effective_date'),errors='coerce')
        gd=pd.to_datetime(row['game_date_et'])
        row['star_PPP_it']=opening or (pd.notna(eff) and gd>=eff)
    else:
        row['star_PPP_it']=False
    extra_rows.append(row)
if extra_rows:
    denominator=pd.concat([roster,pd.DataFrame(extra_rows)],ignore_index=True,sort=False)
else: denominator=roster.copy()
assert not denominator.duplicated(keys).any()

# Merge harmonized report designations and team status.
rm=pr[keys+['player_name','current_status','reason','snapshot_basename','published_timestamp_utc','minutes_before_tip']].rename(columns={
    'player_name':'report_player_name','current_status':'designation_status_raw','reason':'designation_reason_raw',
    'published_timestamp_utc':'snapshot_timestamp_utc'})
panel=denominator.drop(columns=[c for c in ['team_final_status','inferred_no_listed_players','report_outcome_observed','listed_on_final_report','designation_status','designation_reason','snapshot_basename','snapshot_timestamp_utc','minutes_before_tip','report_player_name','report_qc_selected_within_30m','team_qc_selected_within_30m'] if c in denominator.columns])
panel=panel.merge(rm,on=keys,how='left',validate='one_to_one')
panel=panel.merge(team_status[['game_id','team_norm','team_final_status','usable_submitted_status','inferred_no_listed_players','minutes_before_tip']].rename(columns={'minutes_before_tip':'team_snapshot_minutes_before_tip'}),on=['game_id','team_norm'],how='left',validate='many_to_one')
assert panel.usable_submitted_status.notna().all()
panel['report_outcome_observed']=panel.usable_submitted_status.astype(bool)
panel['listed_on_final_report']=panel.designation_status_raw.notna()
panel['designation_status']=np.where(~panel.report_outcome_observed,pd.NA,np.where(panel.listed_on_final_report,panel.designation_status_raw,'Not Listed'))
panel['designation_reason']=np.where(panel.listed_on_final_report,panel.designation_reason_raw,pd.NA)

# Recompute absence using the original deterministic rule.
played=panel.played_bool.astype(bool)
coach=panel.not_playing_reason.fillna('').str.contains('COACH',case=False,na=False)
panel['coach_decision_dnp_harm']=(~played) & (coach | (panel.boxscore_player_status.fillna('').eq('ACTIVE') & panel.not_playing_reason.fillna('').eq('')))
absbox=panel.not_playing_reason.fillna('').str.contains('INJURY|REST|PERSONAL|GLEAGUE|HEALTH_AND_SAFETY|SUSPENSION|NOT_WITH_TEAM|TRADE|INELIGIBLE|RECONDITIONING|CONCUSSION|SELF_ISOLATING|ILLNESS',case=False,regex=True,na=False)
panel['absence_now_harm']=(~played) & (
    panel.designation_status_raw.fillna('').str.casefold().eq('out') | absbox |
    (panel.boxscore_player_status.fillna('').eq('INACTIVE') & ~panel.coach_decision_dnp_harm) |
    (~panel.from_boxscore_roster.astype(bool) & panel.designation_status_raw.fillna('').str.casefold().eq('out')))

# Recompute workload and risk set after cadence-specific report-only union.
panel=panel.sort_values(['nba_player_id','season','game_date_et','tip_utc','game_id']).reset_index(drop=True)
gps=panel.groupby(['nba_player_id','season'],sort=False,group_keys=False)
panel['games_played_before_game_harm']=gps.played_bool.transform(lambda s:s.astype(int).cumsum().shift(fill_value=0))
panel['minutes_sum_prior_10_roster_games_harm']=gps.minutes_played.transform(lambda s:s.fillna(0).shift(1).rolling(10,min_periods=1).sum())
panel['dist_to_65_before_game_harm']=65-panel.games_played_before_game_harm
panel=panel.sort_values(['nba_player_id','season','team_norm','team_game_number','tip_utc']).reset_index(drop=True)
g=panel.groupby(['nba_player_id','season','team_norm'],sort=False)
panel['prev_team_game_number_harm']=g.team_game_number.shift(1)
panel['prev_absence_harm']=g.absence_now_harm.shift(1)
panel['consecutive_roster_observation_harm']=panel.prev_team_game_number_harm.eq(panel.team_game_number-1)
panel['at_risk_for_new_onset_harm']=panel.report_outcome_observed & panel.consecutive_roster_observation_harm & ~panel.prev_absence_harm.fillna(False)
panel['absence_onset_harm']=panel.at_risk_for_new_onset_harm & panel.absence_now_harm

# Harmonized TV definition from stage 2.
old_linear={'ABC','ESPN','ABC/ESPN','ABC|ESPN','TNT'}
new_linear={'ABC','ESPN','ABC/ESPN','ABC|ESPN','NBC/Peacock'}
panel['tv_harmonized_linear']=np.where(panel.season.eq('2025-26'),panel.network_announced.fillna('').isin(new_linear),panel.network_announced.fillna('').isin(old_linear)).astype(float)

# Save bounded panel.
outcols=['player_team_game_id','game_id','season','source_match_number','game_date_et','tip_utc','team','opponent','team_norm','nba_player_id','nba_player_name','from_boxscore_roster','played_bool','minutes_played','team_game_number','star_PPP_it','postPPP','cup_game','announced_tv_primary','network_announced','tv_harmonized_linear','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel_km_since_previous_game','absolute_timezone_shift_hours','road_trip_game_number','signed_elo_advantage','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadvantage_km','designation_status','designation_reason','report_outcome_observed','absence_now_harm','at_risk_for_new_onset_harm','absence_onset_harm','games_played_before_game_harm','minutes_sum_prior_10_roster_games_harm','dist_to_65_before_game_harm','snapshot_basename','snapshot_timestamp_utc','team_snapshot_minutes_before_tip']
panel[outcols].to_csv(OUT/'player_team_game_harmonized_cadence.csv.gz',index=False,compression='gzip')

# QA comparisons.
canon=base.groupby('season').agg(canonical_rows=('player_team_game_id','size'),canonical_at_risk=('at_risk_for_new_onset','sum'),canonical_onsets=('absence_onset','sum')).reset_index()
harm=panel.groupby('season').agg(harm_rows=('player_team_game_id','size'),harm_at_risk=('at_risk_for_new_onset_harm','sum'),harm_onsets=('absence_onset_harm','sum'),harm_report_only=('from_boxscore_roster',lambda s:int((~s.astype(bool)).sum()))).reset_index()
qa=canon.merge(harm,on='season')
qa['delta_rows']=qa.harm_rows-qa.canonical_rows; qa['delta_at_risk']=qa.harm_at_risk-qa.canonical_at_risk; qa['delta_onsets']=qa.harm_onsets-qa.canonical_onsets
qa.to_csv(OUT/'cadence_panel_counts_by_season.csv',index=False)
# Snapshot difference rate.
canonical_snap=base[['game_id','snapshot_basename']].dropna().drop_duplicates('game_id').rename(columns={'snapshot_basename':'canonical_snapshot'})
harm_snap=selmap[['game_id','snapshot_basename']].rename(columns={'snapshot_basename':'harmonized_snapshot'})
scomp=harm_snap.merge(canonical_snap,on='game_id',how='left')
scomp['snapshot_changed']=scomp.harmonized_snapshot.ne(scomp.canonical_snapshot)
scomp.to_csv(OUT/'snapshot_selection_comparison.csv',index=False)

# Model: player + team-season FE, full controls, two-way player/game clustering.
def projector(groups):
    codes,uni=pd.factorize(groups,sort=False); n=len(codes); k=len(uni)
    G=csr_matrix((np.ones(n),(np.arange(n),codes)),shape=(n,k)); cnt=np.asarray(G.sum(0)).ravel()
    return G,cnt
def absorb(A,g1,g2,tol=1e-10,max_iter=200):
    A=np.asarray(A,float).copy(); G1,c1=projector(g1); G2,c2=projector(g2)
    for it in range(max_iter):
        old=A.copy() if it<3 or it%5==0 else None
        A-=G1@((G1.T@A)/c1[:,None]); A-=G2@((G2.T@A)/c2[:,None])
        if old is not None and np.max(np.abs(A-old))<tol: break
    return A,it+1

def fit(tvcol,label,controls=True):
    d=panel[panel.at_risk_for_new_onset_harm].copy()
    for c in ['star_PPP_it','postPPP','announced_tv_primary','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game']:
        d[c]=asbool(d[c]).astype(float)
    d['absence_onset_harm']=d.absence_onset_harm.astype(float)
    d['tv_model']=d[tvcol].astype(float)
    d['star_post']=d.star_PPP_it*d.postPPP; d['star_tv']=d.star_PPP_it*d.tv_model; d['post_tv']=d.postPPP*d.tv_model; d['triple']=d.star_PPP_it*d.postPPP*d.tv_model
    d['elo_100']=d.signed_elo_advantage/100.0; d['travel_1000']=d.travel_km_since_previous_game/1000.0; d['travel_disadv_1000']=d.travel_disadvantage_km/1000.0
    d['minutes10_100']=d.minutes_sum_prior_10_roster_games_harm/100.0; d['games_before_10']=d.games_played_before_game_harm/10.0; d['dist65_10']=d.dist_to_65_before_game_harm/10.0
    lower=['star_PPP_it','tv_model','star_post','star_tv','post_tv','triple']
    ctr=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadv_1000','cup_game','minutes10_100','games_before_10','dist65_10'] if controls else []
    terms=lower+ctr
    keepcols=['absence_onset_harm','nba_player_id','game_id','team','season']+terms
    d=d[keepcols].replace([np.inf,-np.inf],np.nan).dropna().copy(); d['teamseason']=d.team.astype(str)+'|'+d.season.astype(str)
    A,it=absorb(d[['absence_onset_harm']+terms].to_numpy(float),d.nba_player_id,d.teamseason)
    y=A[:,0]; X=A[:,1:]; nonzero=(X*X).sum(0)>1e-12; X=X[:,nonzero]; names=[n for n,k in zip(terms,nonzero) if k]
    res=sm.OLS(y,X).fit(); j=names.index('triple')
    cov,_,_=cov_cluster_2groups(res,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0],use_correction=True)
    beta=float(res.params[j]); se=float(np.sqrt(max(cov[j,j],0))); z=beta/se; p=2*norm.sf(abs(z))
    return {'definition':label,'controls':'full' if controls else 'none','n':len(d),'estimate_pp':100*beta,'se_pp':100*se,'low_pp':100*(beta-1.96*se),'high_pp':100*(beta+1.96*se),'p':p,'iterations':it}

rows=[]
for tvcol,label in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
    rows.append(fit(tvcol,label,True)); rows.append(fit(tvcol,label,False))
res=pd.DataFrame(rows); res.to_csv(OUT/'cadence_harmonized_model_results.csv',index=False)

summary={
 'base_boxscore_roster_rows':int(len(roster)),
 'harmonized_report_only_additions':int(len(extras)),
 'harmonized_full_rows':int(len(panel)),
 'harmonized_at_risk_rows':int(panel.at_risk_for_new_onset_harm.sum()),
 'harmonized_absence_onsets':int(panel.absence_onset_harm.sum()),
 'games_snapshot_changed_vs_latest_pretip':int(scomp.snapshot_changed.sum()),
 'games_total':int(len(scomp)),
 'snapshot_changed_pct':float(100*scomp.snapshot_changed.mean()),
 'unmatched_report_player_rows':int(len(missing)),
}
(OUT/'qa_summary.json').write_text(json.dumps(summary,indent=2))
print('\nQA'); print(json.dumps(summary,indent=2)); print('\nBY SEASON'); print(qa.to_string(index=False)); print('\nMODELS'); print(res.to_string(index=False))
