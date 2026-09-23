"""B6 step 7 — THE CONSTRUCTIVE VARIANT. The pool is strongly direction-conditional (L-S swings
-0.245 -> +0.311 across direction quintiles). Is the day's direction predictable from strictly
prior information? If yes, a CAUSAL side overlay exists where the family overlay did not."""
import numpy as np, pandas as pd, json, math, warnings
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C
df=C.build_master(); P=df[df.elig&df.filled].copy()
mkt=pd.read_csv('daily_direction_index.csv',parse_dates=['date']).set_index('date')
m=mkt['dir_idx'].dropna()

print('=== 1) IS THE DAILY DIRECTION INDEX PERSISTENT? ===')
for L in (1,2,3,5,10,20):
    a=m.shift(L).dropna(); b=m.reindex(a.index)
    r=stats.spearmanr(a,b)
    print('  lag %-3d rho %+.4f p %.4f  n=%d'%(L,r.statistic,r.pvalue,len(a)))
for K in (2,3,5,10,20):
    tr=m.shift(1).rolling(K,min_periods=max(2,K//2)).mean()
    ok=tr.notna()&m.notna()
    r=stats.spearmanr(tr[ok],m[ok])
    print('  trailing-%-3d mean vs today: rho %+.4f p %.4f  hit-rate(sign agree) %.3f'%(
        K,r.statistic,r.pvalue,float((np.sign(tr[ok])==np.sign(m[ok])).mean())))

print('\n=== 2) THE CAUSAL SIDE OVERLAY: take the side matching the trailing direction state ===')
res={}
for K in (1,2,3,5,10,20):
    tr=m.shift(1).rolling(K,min_periods=max(1,K//2)).mean()
    sig=P.date.map(tr)
    take_long=sig>0
    S=P[((P.side=='LONG')&take_long)|((P.side=='SHORT')&(sig<0))].copy()
    ctrl=P[sig.notna()]
    b=C.day_boot_mean(S.net_r,S.date,seed=11)
    pm=S.groupby('month',observed=True).net_r.mean().reindex(['feb','apr','may','jun','jul'])
    res['K%d'%K]=dict(n=int(len(S)),mean=round(float(S.net_r.mean()),5),
      ctrl=round(float(ctrl.net_r.mean()),5),
      dirinfo=round(float(S.dirinfo_r.mean()),5),
      se=round(float(C.day_cluster_se(S.net_r,S.date)),5),
      ci=[round(float(np.quantile(b,.025)),5),round(float(np.quantile(b,.975)),5)],
      p_le0=round(float((b<=0).mean()),4),
      months_pos=int((pm>0).sum()),per_month={k:round(float(v),5) for k,v in pm.items()})
    print('  K=%-3d n=%6d  net %+0.5f (ctrl %+0.5f)  dirinfo %+0.5f  se %.5f  P(<=0) %.4f  months+ %d/5  %s'%(
      K,len(S),S.net_r.mean(),ctrl.net_r.mean(),S.dirinfo_r.mean(),C.day_cluster_se(S.net_r,S.date),
      (b<=0).mean(),int((pm>0).sum()),' '.join('%+.3f'%v for v in pm.values)))

print('\n=== 3) ORACLE side rule (same-day direction sign, NOT deployable) — the ceiling ===')
sig=P.date.map(m)
O=P[((P.side=='LONG')&(sig>0))|((P.side=='SHORT')&(sig<0))]
print('  oracle-side n=%d net %+0.5f dirinfo %+0.5f  vs pool %+0.5f'%(len(O),O.net_r.mean(),O.dirinfo_r.mean(),P.net_r.mean()))
print('  => headroom of a PERFECT daily direction call: %+0.5f R/trade'%(O.net_r.mean()-P.net_r.mean()))

print('\n=== 4) CROSS-SECTIONAL version: per-SYMBOL trailing direction (24 symbols, more signal) ===')
E=df[df.elig].copy()
g=E.groupby(['symbol','date'],observed=True).trend_state_m15
sy=(g.apply(lambda s:s.isin(['strong_up','up']).mean())-g.apply(lambda s:s.isin(['strong_down','down']).mean())).rename('d').reset_index()
sy=sy.sort_values(['symbol','date'])
for K in (1,2,3,5,10):
    sy['tr']=sy.groupby('symbol',observed=True).d.transform(lambda s:s.shift(1).rolling(K,min_periods=max(1,K//2)).mean())
    mp=sy.set_index(['symbol','date']).tr
    key=pd.MultiIndex.from_arrays([P.symbol,P.date])
    sig2=pd.Series(key.map(mp),index=P.index)
    S=P[((P.side=='LONG')&(sig2>0))|((P.side=='SHORT')&(sig2<0))]
    ctrl=P[sig2.notna()]
    b=C.day_boot_mean(S.net_r,S.date,seed=13)
    pm=S.groupby('month',observed=True).net_r.mean().reindex(['feb','apr','may','jun','jul'])
    res['SYM_K%d'%K]=dict(n=int(len(S)),mean=round(float(S.net_r.mean()),5),ctrl=round(float(ctrl.net_r.mean()),5),
       dirinfo=round(float(S.dirinfo_r.mean()),5),ci=[round(float(np.quantile(b,.025)),5),round(float(np.quantile(b,.975)),5)],
       p_le0=round(float((b<=0).mean()),4),months_pos=int((pm>0).sum()),
       per_month={k:round(float(v),5) for k,v in pm.items()})
    print('  symbol-K=%-3d n=%6d  net %+0.5f (ctrl %+0.5f) dirinfo %+0.5f  P(<=0) %.4f  months+ %d/5  %s'%(
      K,len(S),S.net_r.mean(),ctrl.net_r.mean(),S.dirinfo_r.mean(),(b<=0).mean(),int((pm>0).sum()),
      ' '.join('%+.3f'%v for v in pm.values)))
json.dump(res,open('side_overlay.json','w'),indent=1)
