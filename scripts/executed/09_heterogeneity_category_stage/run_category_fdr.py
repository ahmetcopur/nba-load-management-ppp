from pathlib import Path
import json,hashlib,warnings,zipfile
import numpy as np,pandas as pd,statsmodels.api as sm
from scipy.sparse import csr_matrix
from scipy.stats import norm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
from statsmodels.stats.multitest import multipletests
warnings.filterwarnings('ignore')
ROOT=Path('/mnt/data/nba_heterogeneity_work')
AP=ROOT/'nba_player_game_analysis_ready_v1/player_game_panel_model_at_risk_analysis_ready.csv.gz'
TVUN=ROOT/'tv_unpack'; tv_path=list(TVUN.rglob('announced_tv_six_seasons.csv'))[0]
OUT=Path('/mnt/data/nba_category_decomposition_fdr_v1');OUT.mkdir(exist_ok=True)
df=pd.read_csv(AP,low_memory=False);tv=pd.read_csv(tv_path,low_memory=False)
def b(s):
    if s.dtype==bool:return s.astype(float)
    return s.map(lambda x:1.0 if str(x).strip().lower() in {'true','1','1.0'} else 0.0)
for c in ['star_PPP_it','postPPP','announced_tv_primary','announced_nba_tv','is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','opponent_bottom_quartile_pre','opponent_back_to_back','cup_game','absence_onset','vague_onset_frozen','specific_onset_frozen','explicit_rest_onset_frozen','other_absence_onset_frozen']:
    df[c]=b(df[c])
df['home_team']=np.where(df.is_home==1,df.team,df.opponent);df['away_team']=np.where(df.is_home==1,df.opponent,df.team)
keys=['season','game_date_et','home_team','away_team'];tv2=tv[keys+['network_announced','announced_tv_status']].drop_duplicates(keys)
df=df.merge(tv2,on=keys,how='left',validate='many_to_one');assert df.announced_tv_status.notna().all()
old={'ABC','ESPN','ABC/ESPN','ABC|ESPN','TNT'};new={'ABC','ESPN','ABC/ESPN','ABC|ESPN','NBC/Peacock'}
df['tv_harmonized_linear']=np.where(df.season=='2025-26',df.network_announced.fillna('').isin(new),df.network_announced.fillna('').isin(old)).astype(float)
df['elo_100']=df.signed_elo_advantage/100;df['travel_1000']=df.travel_km_since_previous_game/1000;df['travel_disadv_1000']=df.travel_disadvantage_km/1000;df['minutes10_100']=df.minutes_sum_prior_10_roster_games/100;df['games_before_10']=df.games_played_before_game/10;df['dist65_10']=df.dist_to_65_before_game/10
controls=['is_home','back_to_back','three_games_in_four_days','four_games_in_six_days','travel_1000','absolute_timezone_shift_hours','road_trip_game_number','elo_100','opponent_bottom_quartile_pre','opponent_back_to_back','rest_advantage_days','travel_disadv_1000','cup_game','minutes10_100','games_before_10','dist65_10']
def projector(g):
 c,u=pd.factorize(g,sort=False);G=csr_matrix((np.ones(len(c)),(np.arange(len(c)),c)),shape=(len(c),len(u)));return G,np.asarray(G.sum(0)).ravel()
def absorb(A,g1,g2,tol=1e-10,max_iter=250):
 A=np.asarray(A,float).copy();G1,c1=projector(g1);G2,c2=projector(g2)
 for it in range(max_iter):
  old=A.copy() if it<3 or it%5==0 else None
  A-=G1@((G1.T@A)/c1[:,None]);A-=G2@((G2.T@A)/c2[:,None])
  if old is not None and np.max(np.abs(A-old))<tol:break
 return A,it+1
def fit(outcome,tvcol):
 d=df.copy();d['S']=d.star_PPP_it;d['P']=d.postPPP;d['T']=d[tvcol];d['SP']=d['S']*d['P'];d['ST']=d['S']*d['T'];d['PT']=d['P']*d['T'];d['SPT']=d['S']*d['P']*d['T']
 terms=['S','T','SP','ST','PT','SPT']+controls
 d=d[[outcome,'nba_player_id','game_id','team','season']+terms].replace([np.inf,-np.inf],np.nan).dropna()
 A=d[[outcome]+terms].to_numpy(float);A,it=absorb(A,d.nba_player_id,d.team.astype(str)+'|'+d.season.astype(str))
 y=A[:,0];X=A[:,1:];keep=(X*X).sum(0)>1e-12;names=[n for n,k in zip(terms,keep) if k];X=X[:,keep]
 r=sm.OLS(y,X).fit();cov,_,_=cov_cluster_2groups(r,pd.factorize(d.nba_player_id)[0],pd.factorize(d.game_id)[0],use_correction=True)
 se=np.sqrt(np.maximum(np.diag(cov),0));j=names.index('SPT');beta=r.params[j];s=se[j];p=2*norm.sf(abs(beta/s))
 return {'tv_definition':tvcol,'outcome':outcome,'n':len(d),'estimate_pp':100*beta,'se_pp':100*s,'low_pp':100*(beta-1.96*s),'high_pp':100*(beta+1.96*s),'p':p,'iterations':it}
outcomes=['vague_onset_frozen','specific_onset_frozen','explicit_rest_onset_frozen','other_absence_onset_frozen']
rows=[]
for tvc in ['announced_tv_primary','tv_harmonized_linear']:
 for o in outcomes:
  print('running',tvc,o,flush=True);rows.append(fit(o,tvc))
r=pd.DataFrame(rows);r['q_bh']=np.nan;r['p_holm']=np.nan
for tvc,g in r.groupby('tv_definition'):
 idx=g.index;r.loc[idx,'q_bh']=multipletests(g.p,method='fdr_bh')[1];r.loc[idx,'p_holm']=multipletests(g.p,method='holm')[1]
r.to_csv(OUT/'category_focal_fdr.csv',index=False)
summary={'family':'four mutually exclusive absence-onset categories','adjustments':'BH FDR and Holm within each TV definition (4 tests)','note':'absence_onset overall is not included in the category multiple-testing family because it is the primary extensive-margin endpoint.'}
(OUT/'results_summary.json').write_text(json.dumps(summary,indent=2))
(OUT/'README.md').write_text('''# Category Decomposition with Multiple-Testing Adjustment — v1\n\nThe four category-specific onset outcomes (vague, specific, explicit rest, other absence) are fit using the standard player + team-season FE LPM with player/game two-way clustered inference. The focal coefficient is Star × PostPPP × TV. Benjamini-Hochberg FDR q-values and Holm-adjusted p-values are calculated separately across the four category tests within each TV-definition family.\n\nThe primary all-absence endpoint is not included in this family because it was pre-specified as the main extensive-margin outcome rather than one of several category discoveries.\n''')
import shutil;shutil.copy2(__file__,OUT/'run_category_fdr.py')
mans=[]
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name!='file_manifest_sha256.csv':mans.append({'file':p.name,'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
pd.DataFrame(mans).to_csv(OUT/'file_manifest_sha256.csv',index=False)
print(r.to_string(index=False))
