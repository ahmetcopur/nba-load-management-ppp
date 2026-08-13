from pathlib import Path
import zipfile, shutil, importlib.util, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd

ROOT=Path('/mnt/data/nba_continue')
SEL=ROOT/'cadence_work/selector/nba_canonical_snapshot_selector_v1/2025-26_game_snapshot_join_harmonized_canonical.csv'
OUT=ROOT/'cadence_work/season_parsed/2025-26'
PDF=OUT/'pdf'; PDF.mkdir(parents=True,exist_ok=True)
parser_path=ROOT/'cadence_core_full/nba_player_game_at_risk_core_v1/parsers/parser_2023plus.py'
spec=importlib.util.spec_from_file_location('p23',parser_path); mod=importlib.util.module_from_spec(spec); sys.modules['p23']=mod; spec.loader.exec_module(mod)

d=pd.read_csv(SEL)
meta=d[['snapshot_basename','published_timestamp_utc']].drop_duplicates().copy()
meta['report_date']=pd.to_datetime(meta.published_timestamp_utc,utc=True).dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d')
needed=set(meta.snapshot_basename)
zips=[ROOT/'cadence_2025/audit_2025_26_upload.zip',ROOT/'cadence_2025/audit_2025_26_targeted_upload.zip']
found={}
for zp in zips:
    with zipfile.ZipFile(zp) as z:
        bybase={Path(n).name:n for n in z.namelist() if n.lower().endswith('.pdf')}
        for b in list(needed - set(found)):
            if b in bybase:
                dest=PDF/b
                with z.open(bybase[b]) as src, open(dest,'wb') as dst: shutil.copyfileobj(src,dst)
                found[b]=dest
missing=needed-set(found)
if missing: raise SystemExit(f'missing {len(missing)} PDFs: {sorted(missing)[:10]}')

def work(row):
    b,snap,date=row
    try:
        rows,pages,warn=mod.parse_pdf(found[b],season='2025-26',report_date=date,snapshot_utc=snap,source_file=f'cadence_selected/{b}')
        return rows,{'source_file':b,'snapshot_timestamp_utc':snap,'pages':pages,'extracted_rows':len(rows),'status':'ok' if rows else 'zero_rows','warning':warn or ''}
    except Exception as e:
        return [],{'source_file':b,'snapshot_timestamp_utc':snap,'pages':None,'extracted_rows':0,'status':'parse_error','warning':f'{type(e).__name__}: {e}'}

rows=[];logs=[]
items=list(meta[['snapshot_basename','published_timestamp_utc','report_date']].itertuples(index=False,name=None))
with ProcessPoolExecutor(max_workers=8) as ex:
    futs=[ex.submit(work,x) for x in items]
    for i,f in enumerate(as_completed(futs),1):
        rr,ll=f.result();rows.extend(rr);logs.append(ll)
        if i%50==0: print('parsed',i,'/',len(items),'rows',len(rows),flush=True)
pd.DataFrame(rows).to_csv(OUT/'s1_snapshot_rows_harmonized_selected.csv',index=False)
pd.DataFrame(logs).to_csv(OUT/'s1_parse_log_harmonized_selected.csv',index=False)
print('done files',len(items),'rows',len(rows),'errors',sum(x['status']=='parse_error' for x in logs))
