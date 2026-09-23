"""LANE 4 (F): the paired-treatment channel + breadth as a function of the cost line."""
import gzip, json, numpy as np, pandas as pd, sys
from pathlib import Path
from scipy import stats
REPO=Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
OUT=Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane4"); res={}
K=(stats.norm.ppf(0.975)+stats.norm.ppf(0.80))**2

rows=json.load(gzip.open(REPO/"docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz","rt"))
df=pd.DataFrame(rows); df['entry']=pd.to_datetime(df.entry_utc,utc=True,format='mixed')
df['day']=df.entry.dt.strftime('%Y-%m-%d')
for c in ('r_old','r_new_low','r_new_mid','r_new_high'): df[c]=pd.to_numeric(df[c],errors='coerce')
df=df.dropna(subset=['r_new_mid','r_old'])
fwd=df[df.entry>='2025-01-01']; fwd_m=(fwd.entry.max()-fwd.entry.min()).days/30.4369
all_m=(df.entry.max()-df.entry.min()).days/30.4369

def paired(d, a, b, label, months, rate):
    x=(d[b]-d[a]).to_numpy(); x=x[np.isfinite(x)]
    m=float(x.mean()); s=float(x.std(ddof=1)); n=len(x)
    out={'label':label,'n':n,'mean_delta_R':round(m,6),'sd_delta_R':round(s,6),
         'se':round(s/np.sqrt(n),6),'t':round(m/(s/np.sqrt(n)),3),
         'sd_ratio_vs_unpaired': round(s/float(d[b].std(ddof=1)),4),
         'trades_per_month_available': round(rate,1)}
    for eff in (0.01,0.02,0.05,0.10):
        nn=K*(s/eff)**2
        out[f'n_to_detect_{eff}R']=int(np.ceil(nn))
        out[f'months_to_detect_{eff}R']=round(nn/rate,3)
        out[f'weeks_to_detect_{eff}R']=round(nn/rate*4.348,2)
    return out
rate_all29 = len(fwd)/fwd_m
rate_armed = len(fwd[fwd.sleeve.isin(['crypto','energy_agri','sub_xvol_pullback'])])/fwd_m
res['paired_treatment_channel']={
 'estate_all29_quote_correction_old_to_mid': paired(fwd,'r_old','r_new_mid','quote-side correction (r_old -> r_new_mid)',fwd_m,rate_all29),
 'estate_all29_cost_band_low_to_high': paired(fwd,'r_new_low','r_new_high','cost band low -> high (a pure cost treatment)',fwd_m,rate_all29),
 'armed3_only_cost_band': paired(fwd[fwd.sleeve.isin(['crypto','energy_agri','sub_xvol_pullback'])],'r_new_low','r_new_high','cost band, armed 3 only',fwd_m,rate_armed),
 'unpaired_reference_sd_all29': round(float(fwd.r_new_mid.std(ddof=1)),4),
 'unpaired_reference_sd_armed3': round(float(fwd[fwd.sleeve.isin(['crypto','energy_agri','sub_xvol_pullback'])].r_new_mid.std(ddof=1)),4),
}
# ---- breadth as a function of the residual cost line ----
g=fwd.groupby('sleeve')['r_new_mid'].agg(n='size',mean='mean',sd='std')
g=g[g.n>=20]; g['tpm']=g.n/fwd_m
curve={}
for c in (0.00,0.01,0.02,0.03,0.038,0.05,0.075,0.10,0.15,0.25,0.50,1.00):
    sel=g[g['mean']>c]
    curve[f'residual_cost_{c}R']={'sleeves_clearing':int(len(sel)),
      'trades_per_month':round(float(sel.tpm.sum()),2),
      'net_R_per_month_after_that_cost':round(float(((sel['mean']-c)*sel.tpm).sum()),3),
      'sleeves':sorted(sel.index.tolist())}
res['breadth_vs_cost_line']=curve
res['cost_components_funnel_median']={'note':'from the candidate cache, median per-trade cost components in R',
  }
pop=pd.read_parquet("/tmp/lane_i/pop.parquet")
el=pop[pop.eligible]
for c in ('cost_r','spread_r','commission_r','expected_slippage_r','swap_cost_r'):
    res['cost_components_funnel_median'][c]=round(float(el[c].median()),5)
res['cost_components_funnel_median']['residual_after_spread_median']=round(
  float((el.commission_r+el.expected_slippage_r+el.swap_cost_r).median()),5)
(OUT/"G_PAIRED_AND_COSTLINE_V1.json").write_text(json.dumps(res,indent=1,default=str))
print(json.dumps(res['paired_treatment_channel'],indent=1))
print(json.dumps(res['breadth_vs_cost_line'],indent=1))
print(json.dumps(res['cost_components_funnel_median'],indent=1))
