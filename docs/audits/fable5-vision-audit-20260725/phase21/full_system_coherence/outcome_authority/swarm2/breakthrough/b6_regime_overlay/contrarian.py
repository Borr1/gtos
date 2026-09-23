"""B6 step 7b — the reversal measurement. Daily direction is ANTI-persistent (trailing-2 rho -0.389,
p 1e-4), so the momentum-side rule is the wrong sign. Test the contrarian side rule, walk-forward,
alone and crossed with the ex-ante cost gate."""
import numpy as np, pandas as pd, json, math, warnings
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C
df=C.build_master(); P=df[df.elig&df.filled].copy().sort_values('date')
mkt=pd.read_csv('daily_direction_index.csv',parse_dates=['date']).set_index('date')
m=mkt['dir_idx'].dropna()
def report(S,ctrl,lab,seed=17,months=('feb','apr','may','jun','jul')):
    if len(S)<50: print('  %-34s too small'%lab); return None
    b=C.day_boot_mean(S.net_r,S.date,seed=seed)
    pm=S.groupby('month',observed=True).net_r.mean().reindex(list(months))
    d=dict(label=lab,n=int(len(S)),mean=round(float(S.net_r.mean()),5),ctrl=round(float(ctrl),5),
      dirinfo=round(float(S.dirinfo_r.mean()),5),cost=round(float(S.cost_r.mean()),5),
      se_day=round(float(C.day_cluster_se(S.net_r,S.date)),5),
      ci=[round(float(np.quantile(b,.025)),5),round(float(np.quantile(b,.975)),5)],
      p_le0=round(float((b<=0).mean()),4),months_pos=int((pm>0).sum()),
      total=round(float(S.net_r.sum()),2),days=int(S.date.nunique()),
      per_month={k:(round(float(v),5) if pd.notna(v) else None) for k,v in pm.items()},
      long_n=int((S.side=='LONG').sum()),
      long_mean=round(float(S[S.side=='LONG'].net_r.mean()),5) if (S.side=='LONG').any() else None,
      short_mean=round(float(S[S.side=='SHORT'].net_r.mean()),5) if (S.side=='SHORT').any() else None)
    print('  %-34s n=%6d net %+0.5f (ctrl %+0.5f) di %+0.5f cost %.4f  P(<=0) %.4f  m+ %d/%d  %s'%(
      lab,d['n'],d['mean'],d['ctrl'],d['dirinfo'],d['cost'],d['p_le0'],d['months_pos'],len(months),
      ' '.join('%+.3f'%v if pd.notna(v) else ' n/a' for v in pm.values)))
    return d
out=[]
print('=== CONTRARIAN SIDE RULE: take the side OPPOSITE the trailing direction state ===')
for K in (1,2,3,5):
    tr=m.shift(1).rolling(K,min_periods=max(1,K//2)).mean()
    sig=P.date.map(tr)
    S=P[((P.side=='SHORT')&(sig>0))|((P.side=='LONG')&(sig<0))]
    out.append(report(S,P[sig.notna()].net_r.mean(),'contrarian K=%d'%K))
print('\n=== CONTRARIAN x EX-ANTE COST GATE (walk-forward cost quantile on strictly prior data) ===')
days=sorted(P.date.unique())
for q in (0.25,1/3.,0.5):
    thr={dt:(P[P.date<dt].cost_r.quantile(q) if (P.date<dt).sum()>500 else np.nan) for dt in days}
    P['thr']=P.date.map(thr)
    for K in (2,3,5):
        tr=m.shift(1).rolling(K,min_periods=max(1,K//2)).mean(); sig=P.date.map(tr)
        S=P[(((P.side=='SHORT')&(sig>0))|((P.side=='LONG')&(sig<0)))&(P.cost_r<=P.thr)&P.thr.notna()]
        ctrl=P[P.thr.notna()].net_r.mean()
        out.append(report(S,ctrl,'contrarian K=%d x cost q=%.2f'%(K,q),seed=19))
print('\n=== control: MOMENTUM side x cost gate (the wrong-sign arm, for the A/B) ===')
thr={dt:(P[P.date<dt].cost_r.quantile(1/3.) if (P.date<dt).sum()>500 else np.nan) for dt in days}
P['thr']=P.date.map(thr)
for K in (2,3,5):
    tr=m.shift(1).rolling(K,min_periods=max(1,K//2)).mean(); sig=P.date.map(tr)
    S=P[(((P.side=='LONG')&(sig>0))|((P.side=='SHORT')&(sig<0)))&(P.cost_r<=P.thr)&P.thr.notna()]
    out.append(report(S,P[P.thr.notna()].net_r.mean(),'MOMENTUM K=%d x cost q=0.33'%K,seed=23))
print('\n=== cost gate ALONE on the same universe (the component control) ===')
S=P[(P.cost_r<=P.thr)&P.thr.notna()]; out.append(report(S,P[P.thr.notna()].net_r.mean(),'cost q=0.33 alone',seed=29))
json.dump([o for o in out if o],open('contrarian.json','w'),indent=1)
