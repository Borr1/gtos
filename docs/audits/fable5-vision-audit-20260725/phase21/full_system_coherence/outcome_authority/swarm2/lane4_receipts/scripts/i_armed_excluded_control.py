"""LANE 4 second adversarial control: same out-of-selection basket with the three ARMED
sleeves removed, so nothing in the cohort was selected on the forward window.
Produces I_ARMED_EXCLUDED_CONTROL_V1.json. Read-only."""
import gzip,json,numpy as np,pandas as pd
from pathlib import Path
from scipy import stats
REPO=Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
rows=json.load(gzip.open(REPO/"docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz","rt"))
df=pd.DataFrame(rows); df['entry']=pd.to_datetime(df.entry_utc,utc=True,format='mixed')
df['day']=df.entry.dt.strftime('%Y-%m-%d'); df['r']=pd.to_numeric(df.r_new_mid,errors='coerce')
df=df.dropna(subset=['r']); ARMED={'crypto','energy_agri','sub_xvol_pullback'}
pre=df[df.entry<'2025-01-01']; fwd=df[df.entry>='2025-01-01']
pre_m=(pre.entry.max()-pre.entry.min()).days/30.4369; fwd_m=(fwd.entry.max()-fwd.entry.min()).days/30.4369
gp=pre.groupby('sleeve')['r'].agg(n='size',mean='mean')
K=(stats.norm.ppf(0.975)+stats.norm.ppf(0.80))**2; out={}
for c in (0.038,0.05):
    sel=[s for s in gp[(gp['mean']>c)&(gp.n>=20)].index if s not in ARMED]
    sub=fwd[fwd.sleeve.isin(sel)]; r=sub.r.to_numpy()
    m=float(r.mean()); sd=float(r.std(ddof=1)); n=len(r); tpm=n/fwd_m
    dp=np.asarray([float(dd.r.mean()) for _,dd in sub.groupby('day')])
    out[f'c_{c}_ARMED_EXCLUDED']={'sleeves':sel,'n_sleeves':len(sel),'fwd_trades':n,
      'fwd_trades_per_month':round(tpm,2),'fwd_days_per_month':round(sub.day.nunique()/fwd_m,2),
      'mean_r_spread_only':round(m,5),'sd':round(sd,4),'t':round(m/(sd/np.sqrt(n)),3),
      'net_R_per_month_after_c':round((m-c)*tpm,3),'day_portfolio_mean':round(float(dp.mean()),5),
      'day_portfolio_sd':round(float(dp.std(ddof=1)),5),
      'day_portfolio_t':round(float(dp.mean()/(dp.std(ddof=1)/np.sqrt(len(dp)))),3),
      'N_eff_per_day_implied':round(float((sd/dp.std(ddof=1))**2),2),
      'months_to_reject_at_measured_edge':round(K*(sd/max(m-c,1e-9))**2/tpm,3)}
print(json.dumps(out,indent=1,default=str))
