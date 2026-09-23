"""LANE 4 adversarial control: select sleeves on PRE-2025, score on 2025+.
Produces H_OUT_OF_SELECTION_CONTROL_V1.json. Read-only."""
import gzip,json,numpy as np,pandas as pd
from pathlib import Path
from scipy import stats
REPO=Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
rows=json.load(gzip.open(REPO/"docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz","rt"))
df=pd.DataFrame(rows); df['entry']=pd.to_datetime(df.entry_utc,utc=True,format='mixed')
df['r']=pd.to_numeric(df.r_new_mid,errors='coerce'); df=df.dropna(subset=['r'])
pre=df[df.entry<'2025-01-01']; fwd=df[df.entry>='2025-01-01']
pre_m=(pre.entry.max()-pre.entry.min()).days/30.4369; fwd_m=(fwd.entry.max()-fwd.entry.min()).days/30.4369
gp=pre.groupby('sleeve')['r'].agg(n='size',mean='mean'); gp['tpm']=gp.n/pre_m
gf=fwd.groupby('sleeve')['r'].agg(n='size',mean='mean',sd='std'); gf['tpm']=gf.n/fwd_m
out={'pre_2025_months':round(pre_m,1),'fwd_months':round(fwd_m,2)}
for c in (0.0,0.02,0.038,0.05,0.10):
    sel=gp[(gp['mean']>c)&(gp.n>=20)].index; sub=fwd[fwd.sleeve.isin(sel)]
    if len(sub)==0: out[f'c_{c}']={'sleeves':0}; continue
    out[f'c_{c}']={'sleeves_selected_on_pre2025':int(len(sel)),'fwd_trades':int(len(sub)),
      'fwd_trades_per_month':round(len(sub)/fwd_m,2),'fwd_mean_r':round(float(sub.r.mean()),5),
      'fwd_net_R_per_month_after_cost_c':round(float((sub.r.mean()-c)*len(sub)/fwd_m),3),
      'fwd_t':round(float(sub.r.mean()/(sub.r.std(ddof=1)/np.sqrt(len(sub)))),3)}
j=gp.join(gf,lsuffix='_pre',rsuffix='_fwd',how='inner'); j=j[(j.n_pre>=20)&(j.n_fwd>=20)]
out['sign_persistence']={'sleeves':int(len(j)),
  'frac_sign_agree':round(float((np.sign(j.mean_pre)==np.sign(j.mean_fwd)).mean()),4),
  'spearman':[round(float(v),4) for v in stats.spearmanr(j.mean_pre,j.mean_fwd)],
  'pearson':[round(float(v),4) for v in stats.pearsonr(j.mean_pre,j.mean_fwd)]}
print(json.dumps(out,indent=1,default=str))
