from pathlib import Path
import importlib.util, csv, json, hashlib, zipfile
import numpy as np, pandas as pd
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC=str(REPO_ROOT/'scripts/portable/run_nonlinear_multinomial_stage.py')
spec=importlib.util.spec_from_file_location('m',SRC);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OUT=REPO_ROOT/'results/portable_nonlinear_multinomial_final';OUT.mkdir(parents=True,exist_ok=True)

def write_csv(path,rows):
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

d=m.load_canonical()
# Primary extensive and classification
ext=[];cls=[];sens=[]
for tvcol,tvlab in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
    f=m.fit_binary(d,'absence_onset',tvcol,False,None,C=10.0,max_iter=500); r=m.summarize_binary(f,'latest_pre_tip',tvlab,'new_absence_onset');ext.append(r);print('EXT',tvlab,r['average_probability_ddd_pp'],flush=True)

d['vague_vs_specific']=np.where(d.onset_type_frozen.eq('vague_injury_onset'),1,np.where(d.onset_type_frozen.eq('specific_injury_onset'),0,np.nan))
mask=lambda x:x['vague_vs_specific'].notna()
for tvcol,tvlab in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
    f=m.fit_binary(d,'vague_vs_specific',tvcol,False,mask,C=10.0,max_iter=500);r=m.summarize_binary(f,'latest_pre_tip',tvlab,'vague_vs_specific_conditional_on_injury_onset');cls.append(r);print('CLS',tvlab,r['average_probability_ddd_pp'],flush=True)

# Multinomial: direct 5-state competing-risk diagnostic
multi=[]
for tvcol,tvlab in [('announced_tv_primary','legacy_primary'),('tv_harmonized_linear','harmonized_linear')]:
    f=m.multinomial_fit(d,tvcol,C=1.0); vals=m.multinomial_ddd(f);print('MULTI',tvlab,vals,flush=True)
    for k,v in vals.items(): multi.append({'tv_definition':tvlab,'C':1.0,'class':k,'average_probability_ddd_pp':float(v),'n':len(f['data']),'iterations':int(f['model'].n_iter_[0]),'seconds':float(f['seconds'])})

# Frozen LPM reference
lpm=pd.read_csv(REPO_ROOT/'results/canonical_vs_cadence_model_comparison.csv').to_dict('records')
write_csv(OUT/'extensive_nonlinear_primary.csv',ext)
write_csv(OUT/'classification_nonlinear_primary.csv',cls)
write_csv(OUT/'multinomial_softmax_ddd.csv',multi)
write_csv(OUT/'frozen_lpm_reference.csv',lpm)
E={r['tv_definition']:r for r in ext};C={r['tv_definition']:r for r in cls};M={(r['tv_definition'],r['class']):r for r in multi}
readme=f'''# Nonlinear + Multinomial Robustness v1

This stage is a functional-form robustness check after the identification/falsification and taxonomy-reproducibility stages. Inferential claims remain anchored to the already-frozen two-way-clustered LPM.

## Binary nonlinear model
Sparse logistic regression with player and team-season indicators, all lower-order Star/PostPPP/TV terms, and the same pregame controls. `C=10` is the primary weak-ridge stabilization.

### New absence onset
- Legacy TV: nonlinear average DDD **{E['legacy_primary']['average_probability_ddd_pp']:.2f} pp**, focal interaction OR **{E['legacy_primary']['triple_odds_ratio']:.2f}**.
- Harmonized TV: nonlinear average DDD **{E['harmonized_linear']['average_probability_ddd_pp']:.2f} pp**, focal interaction OR **{E['harmonized_linear']['triple_odds_ratio']:.2f}**.

The frozen latest-pre-tip LPM estimates were +3.15 pp and +1.77 pp respectively; cadence-harmonized LPM estimates were +2.63 pp and +1.24 pp. Nonlinearity therefore does not remove the exposure-measurement sensitivity.

### Vague vs specific, conditional on injury onset
- Legacy TV: nonlinear average DDD **{C['legacy_primary']['average_probability_ddd_pp']:.2f} pp**, OR **{C['legacy_primary']['triple_odds_ratio']:.2f}**.
- Harmonized TV: nonlinear average DDD **{C['harmonized_linear']['average_probability_ddd_pp']:.2f} pp**, OR **{C['harmonized_linear']['triple_odds_ratio']:.2f}**.

The sign remains negative. The nonlinear model therefore provides no support for an increase in vague rather than specific labeling in the focal policy cell.

## Five-state multinomial competing-risk diagnostic
States: plays, specific injury onset, vague injury onset, explicit rest onset, other absence onset. Player and team-season indicators and the same covariates are used; `C=1` stabilizes sparse categories. These are point-estimate diagnostics, not new significance tests.

Legacy-TV DDD (pp): plays {M[('legacy_primary','plays')]['average_probability_ddd_pp']:.2f}; specific {M[('legacy_primary','specific')]['average_probability_ddd_pp']:.2f}; vague {M[('legacy_primary','vague')]['average_probability_ddd_pp']:.2f}; rest {M[('legacy_primary','rest')]['average_probability_ddd_pp']:.2f}; other {M[('legacy_primary','other')]['average_probability_ddd_pp']:.2f}.

Harmonized-TV DDD (pp): plays {M[('harmonized_linear','plays')]['average_probability_ddd_pp']:.2f}; specific {M[('harmonized_linear','specific')]['average_probability_ddd_pp']:.2f}; vague {M[('harmonized_linear','vague')]['average_probability_ddd_pp']:.2f}; rest {M[('harmonized_linear','rest')]['average_probability_ddd_pp']:.2f}; other {M[('harmonized_linear','other')]['average_probability_ddd_pp']:.2f}.

The category effects sum to approximately zero by construction. There is no clean multinomial pattern in which the post-PPP star/TV differential shifts specifically into vague injury wording.

## Freeze decision
**Functional-form robustness is complete.** The nonlinear results preserve the same substantive conclusion: a positive availability pattern under the legacy TV definition, materially weaker under harmonized exposure measurement, and no supported vague-label mechanism.

## Next stage
Freeze a small set of heterogeneity hypotheses before looking at coefficients: back-to-back status, weak opponents, workload, age/career stage, and distance to the 65-game threshold. Avoid broad subgroup fishing.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
(OUT/'results_summary.json').write_text(json.dumps({'extensive':ext,'classification':cls,'multinomial':multi},indent=2),encoding='utf-8')
(OUT/'run_nonlinear_multinomial_stage.py').write_bytes(Path(SRC).read_bytes())
(OUT/'finalize_nonlinear_multinomial_v1.py').write_bytes(Path(__file__).read_bytes())
manifest=[]
for p in sorted(OUT.iterdir()):
    if p.is_file() and p.name!='file_manifest_sha256.csv':manifest.append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
write_csv(OUT/'file_manifest_sha256.csv',manifest)
zp=REPO_ROOT/'results/portable_nonlinear_multinomial_robustness_v1.zip'
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):z.write(p,arcname=p.name)
print('PACKAGE',zp,flush=True)
