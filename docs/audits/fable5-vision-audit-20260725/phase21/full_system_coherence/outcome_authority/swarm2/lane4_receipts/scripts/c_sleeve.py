"""LANE 4: sleeve-surface breadth ceiling, effective breadth, and per-sleeve economics.
Population: R1_ESTATE_ROWS_V2.json.gz (22,354 quote-corrected walked trades, 29 sleeves).
Read-only. Writes only to lane4 scratch."""
import gzip, json, numpy as np, pandas as pd
from pathlib import Path
from collections import Counter
REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane4")
rng = np.random.default_rng(20260812)

rows = json.load(gzip.open(REPO/"docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz","rt"))
df = pd.DataFrame(rows)
df['entry'] = pd.to_datetime(df.entry_utc, utc=True, format='mixed')
df['day'] = df.entry.dt.strftime('%Y-%m-%d')
df['r'] = pd.to_numeric(df.r_new_mid, errors='coerce')
df = df[df.r.notna()].copy()
span_days = (df.entry.max()-df.entry.min()).days
span_months = span_days/30.4369
res = {'population': {'trades': int(len(df)), 'sleeves': int(df.sleeve.nunique()),
  'symbols': int(df.symbol.nunique()), 'timeframes': sorted(df.tf.unique().tolist()),
  'span_start': str(df.entry.min()), 'span_end': str(df.entry.max()),
  'span_days': int(span_days), 'span_months': round(span_months,2),
  'trades_per_month_all_sleeves': round(len(df)/span_months,2)}}

# cluster map from the live code
import sys; sys.path.insert(0, str(REPO))
try:
    from src.components.ultimate_book.admission import cluster_of
    df['cluster'] = df.sleeve.map(lambda s: cluster_of(s) or 'UNKNOWN')
    res['cluster_source'] = 'src.components.ultimate_book.admission.cluster_of'
except Exception as e:
    df['cluster'] = 'UNKNOWN'; res['cluster_source'] = f'FAILED: {e}'

ARMED = ['crypto','energy_agri','sub_xvol_pullback']
res['armed_set'] = ARMED
# forward window (2025+) matches the estate's published convention
fwd = df[df.entry >= '2025-01-01'].copy()
fwd_months = (fwd.entry.max()-fwd.entry.min()).days/30.4369
res['forward_window'] = {'trades': int(len(fwd)), 'months': round(fwd_months,2)}

def sleeve_table(d, months):
    g = d.groupby('sleeve').agg(n=('r','size'), mean_r=('r','mean'), sd_r=('r','std'),
        days=('day','nunique'), symbols=('symbol','nunique'))
    g['trades_per_month'] = g.n/months
    g['days_per_month'] = g.days/months
    g['se'] = g.sd_r/np.sqrt(g.n)
    g['t'] = g.mean_r/g.se
    g['total_r'] = g.mean_r*g.n
    g['r_per_month'] = g.total_r/months
    g['armed'] = g.index.isin(ARMED)
    g['cluster'] = [d[d.sleeve==s].cluster.iloc[0] for s in g.index]
    return g.sort_values('r_per_month', ascending=False)

for label, d, mo in (('all_years', df, span_months), ('forward_2025plus', fwd, fwd_months)):
    g = sleeve_table(d, mo)
    res[f'sleeve_table_{label}'] = json.loads(g.round(5).to_json(orient='index'))
    arm = g[g.armed]; un = g[~g.armed]
    res[f'summary_{label}'] = {
      'months': round(mo,2),
      'armed_3': {'sleeves':int(len(arm)),'trades':int(arm.n.sum()),'trades_per_month':round(float(arm.trades_per_month.sum()),3),
                  'total_r':round(float(arm.total_r.sum()),3),'r_per_month':round(float(arm.r_per_month.sum()),4),
                  'mean_r_per_trade':round(float(arm.total_r.sum()/arm.n.sum()),5)},
      'unarmed_26':{'sleeves':int(len(un)),'trades':int(un.n.sum()),'trades_per_month':round(float(un.trades_per_month.sum()),3),
                  'total_r':round(float(un.total_r.sum()),3),'r_per_month':round(float(un.r_per_month.sum()),4),
                  'mean_r_per_trade':round(float(un.total_r.sum()/un.n.sum()),5)},
      'unarmed_positive_sleeves': sorted(un[un.mean_r>0].index.tolist()),
      'unarmed_positive_count': int((un.mean_r>0).sum()),
      'all_29': {'trades_per_month':round(float(g.trades_per_month.sum()),3),
                 'r_per_month':round(float(g.r_per_month.sum()),4)}}

# ---- effective breadth on the sleeve surface: day-portfolio variance ratio
def eff_breadth(d, label, unit_cols=('day',)):
    mu = float(d.r.mean()); s2 = float(d.r.var(ddof=1))
    g = d.groupby(list(unit_cols))['r'].agg(['sum','count'])
    K = g['count'].to_numpy().astype(float); S = g['sum'].to_numpy()
    resid = S - K*mu; varS = float(np.sum(resid**2)/(len(resid)-1))
    Kbar = float(K.mean()); K2 = float((K**2).mean())
    rho = (varS/s2 - Kbar)/max(K2-Kbar, 1e-12)
    boots=[]; idx=np.arange(len(K))
    for _ in range(400):
        b = rng.choice(idx, size=len(idx), replace=True)
        v=float(np.sum(resid[b]**2)/(len(b)-1)); kb=float(K[b].mean()); k2=float((K[b]**2).mean())
        boots.append((v/s2-kb)/max(k2-kb,1e-12))
    lo,hi = np.percentile(boots,[2.5,97.5])
    return {'label':label,'groups':int(len(K)),'K_mean':Kbar,'per_bet_mean':mu,'per_bet_sd':float(np.sqrt(s2)),
            'variance_inflation':varS/(Kbar*s2),'rho_bar':float(rho),'rho_ci95':[float(lo),float(hi)],
            'N_eff_per_group':float(Kbar/(1+(Kbar-1)*max(rho,0.0)))}
res['effective_breadth'] = {
  'all29_same_day': eff_breadth(df,'all 29 sleeves, same trading day'),
  'armed3_same_day': eff_breadth(df[df.sleeve.isin(ARMED)],'armed 3, same trading day'),
  'all29_same_day_cluster': eff_breadth(df,'all 29, same (day,cluster)',('day','cluster')),
}
# sleeve-pair correlation on day-mean R
sd = df.groupby(['day','sleeve'])['r'].mean().unstack()
sd = sd.loc[:, sd.notna().sum()>=60]
C = sd.corr(min_periods=40)
v = C.to_numpy()[np.triu_indices(len(C),k=1)]; v=v[np.isfinite(v)]
res['sleeve_pair_correlation'] = {'sleeves':int(len(C)),'pairs':int(len(v)),'mean':float(np.mean(v)),
  'median':float(np.median(v)),'p05':float(np.percentile(v,5)),'p95':float(np.percentile(v,95)),
  'frac_above_0p3': float(np.mean(v>0.3)),
  'top10': sorted([(C.index[i],C.columns[j],float(C.iat[i,j])) for i in range(len(C)) for j in range(i+1,len(C)) if np.isfinite(C.iat[i,j])], key=lambda t:-t[2])[:10]}

# ---- throttle A/B on the sleeve surface: one-per-(sleeve,symbol,day), cluster cap
def apply_throttles(d, *, sleeves, one_per_sleeve_symbol_day=True, cluster_cap=True, exempt=('jpy',)):
    x = d[d.sleeve.isin(sleeves)].sort_values('entry').copy()
    if one_per_sleeve_symbol_day:
        x = x.groupby(['sleeve','symbol','day'], as_index=False).first()
        x = x.sort_values('entry')
    if cluster_cap:
        keep=[]; seen={}
        for i,row in enumerate(x.itertuples()):
            c=row.cluster; k=(c,row.day)
            if c in exempt or c in (None,'UNKNOWN'): keep.append(True); continue
            bar = str(row.entry)
            if k not in seen: seen[k]=bar; keep.append(True)
            elif seen[k]==bar: keep.append(True)
            else: keep.append(False)
        x = x[np.asarray(keep)]
    return x
def stat(x, months, label):
    if len(x)==0: return {'label':label,'trades':0}
    r = x.r.to_numpy()
    return {'label':label,'trades':int(len(x)),'trades_per_month':round(len(x)/months,3),
      'days':int(x.day.nunique()),'days_per_month':round(x.day.nunique()/months,3),
      'mean_r':round(float(r.mean()),5),'sd_r':round(float(r.std(ddof=1)),5),
      'total_r':round(float(r.sum()),3),'r_per_month':round(float(r.sum())/months,4),
      't':round(float(r.mean()/(r.std(ddof=1)/np.sqrt(len(r)))),3)}
ALL = sorted(df.sleeve.unique().tolist())
res['ladder_sleeve_surface'] = {}
for wl, d, mo in (('all_years',df,span_months), ('forward_2025plus',fwd,fwd_months)):
    cells = {
     'L0_armed3_full_throttles': stat(apply_throttles(d,sleeves=ARMED), mo, 'armed 3, one/sleeve/symbol/day + cluster cap'),
     'L1_armed3_no_cluster_cap': stat(apply_throttles(d,sleeves=ARMED,cluster_cap=False), mo, 'armed 3, cluster cap OFF'),
     'L2_armed3_no_day_cap':     stat(apply_throttles(d,sleeves=ARMED,one_per_sleeve_symbol_day=False), mo, 'armed 3, per-day cap OFF'),
     'L3_armed3_no_caps':        stat(apply_throttles(d,sleeves=ARMED,one_per_sleeve_symbol_day=False,cluster_cap=False), mo, 'armed 3, both caps OFF'),
     'L4_all29_full_throttles':  stat(apply_throttles(d,sleeves=ALL), mo, 'ALL 29 sleeves, both caps ON'),
     'L5_all29_no_caps':         stat(apply_throttles(d,sleeves=ALL,one_per_sleeve_symbol_day=False,cluster_cap=False), mo, 'ALL 29, both caps OFF'),
    }
    res['ladder_sleeve_surface'][wl]=cells
(OUT/"C_SLEEVE_SURFACE_V1.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res['population'], indent=1))
print(json.dumps(res['summary_all_years'], indent=1))
print(json.dumps(res['summary_forward_2025plus'], indent=1))
print(json.dumps(res['effective_breadth'], indent=1))
print(json.dumps(res['ladder_sleeve_surface'], indent=1))
