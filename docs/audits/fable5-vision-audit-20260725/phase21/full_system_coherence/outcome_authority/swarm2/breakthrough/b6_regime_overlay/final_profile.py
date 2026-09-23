"""B6 step 11 — profile the one object that survives (the ex-ante cost gate) by side and by day
direction, and restate the SHORT-leg secondary non-degenerately."""
import numpy as np, pandas as pd, json, math, warnings
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C
df=C.build_master(); P=df[df.elig&df.filled].copy().sort_values('date')
m=pd.read_csv('daily_direction_index.csv',parse_dates=['date']).set_index('date')['dir_idx']
days=sorted(P.date.unique())
for q,nm in ((0.25,'thr25'),(1/3.,'thr33'),(0.5,'thr50')):
    P[nm]=P.date.map({dt:(P[P.date<dt].cost_r.quantile(q) if (P.date<dt).sum()>500 else np.nan) for dt in days})
U=P[P.thr25.notna()].copy(); U['dir']=U.date.map(m)
qt=pd.qcut(m.reindex(sorted(U.date.unique())).dropna(),3,labels=[0,1,2]); U['q']=U.date.map(qt)
print('=== THE COST GATE, PROFILED (cheapest prior-data quartile, walk-forward) ===')
res={}
for nm,lab in (('thr25','q=0.25'),('thr33','q=0.33'),('thr50','q=0.50')):
    S=U[U.cost_r<=U[nm]]
    b=C.day_boot_mean(S.net_r,S.date,seed=53)
    pm=S.groupby('month',observed=True).net_r.mean().reindex(['feb','apr','may','jun','jul'])
    res[lab]=dict(n=int(len(S)),mean=round(float(S.net_r.mean()),5),dirinfo=round(float(S.dirinfo_r.mean()),5),
      cost=round(float(S.cost_r.mean()),5),ci=[round(float(np.quantile(b,.025)),5),round(float(np.quantile(b,.975)),5)],
      p_le0=round(float((b<=0).mean()),4),months_pos=int((pm>0).sum()),
      per_month={k:round(float(v),5) for k,v in pm.items()},
      long=round(float(S[S.side=='LONG'].net_r.mean()),5),short=round(float(S[S.side=='SHORT'].net_r.mean()),5))
    print('  %-8s n=%6d net %+0.5f di %+0.5f cost %.4f  LONG %+0.5f SHORT %+0.5f  m+ %d/5  %s'%(
      lab,len(S),S.net_r.mean(),S.dirinfo_r.mean(),S.cost_r.mean(),
      S[S.side=='LONG'].net_r.mean(),S[S.side=='SHORT'].net_r.mean(),int((pm>0).sum()),
      ' '.join('%+.3f'%v for v in pm.values)))
S=U[U.cost_r<=U.thr25]
print('\n  by day-direction tercile (Q0 = most DOWN):')
rows=[]
for t in (0,1,2):
    s=S[S.q==t]
    rows.append(dict(t=int(t),n=int(len(s)),all=round(float(s.net_r.mean()),5),
       long=round(float(s[s.side=='LONG'].net_r.mean()),5),short=round(float(s[s.side=='SHORT'].net_r.mean()),5)))
    print('   Q%d n=%5d  all %+0.5f  LONG %+0.5f  SHORT %+0.5f'%(t,len(s),s.net_r.mean(),
       s[s.side=='LONG'].net_r.mean(),s[s.side=='SHORT'].net_r.mean()))
print('\n=== SHORT-LEG SECONDARY, restated non-degenerately ===')
tr2=m.shift(1).rolling(2,min_periods=1).mean(); U['sig']=U.date.map(tr2)
U['contr']=((U.side=='SHORT')&(U.sig>0))|((U.side=='LONG')&(U.sig<0))
G=U[U.cost_r<=U.thr25]
for lab,mask in (('cost-gate SHORT leg vs cost-gate all',(G.side=='SHORT')),
                 ('cost-gate LONG  leg vs cost-gate all',(G.side=='LONG'))):
    T=G[mask]
    dt=T.groupby('date',observed=True).net_r.mean(); dc=G.groupby('date',observed=True).net_r.mean()
    d=(dt-dc).dropna()
    rng=np.random.default_rng(9); b=np.array([d.iloc[rng.integers(0,len(d),len(d))].mean() for _ in range(4000)])
    print('  %-38s days=%3d paired %+0.5f sd %.4f P(<=0) %.4f | abs %+0.5f'%(lab,len(d),d.mean(),d.std(),(b<=0).mean(),T.net_r.mean()))
    res['sec_'+lab[:14]]=dict(days=int(len(d)),paired=round(float(d.mean()),5),p_le0=round(float((b<=0).mean()),4),
                              abs_mean=round(float(T.net_r.mean()),5))
# absolute short-leg bar: is the SHORT leg of the cost gate >= the LONG leg? and is it >0 on down days?
sd_=G[G.side=='SHORT']; b=C.day_boot_mean(sd_.net_r,sd_.date,seed=61)
print('  cost-gate SHORT absolute: %+0.5f 95%%CI [%+0.5f,%+0.5f] P(<=0) %.4f  n=%d'%(
   sd_.net_r.mean(),np.quantile(b,.025),np.quantile(b,.975),(b<=0).mean(),len(sd_)))
dn=sd_[sd_.q==0]; b2=C.day_boot_mean(dn.net_r,dn.date,seed=67)
print('  cost-gate SHORT on DOWN-tercile days: %+0.5f 95%%CI [%+0.5f,%+0.5f] P(<=0) %.4f n=%d'%(
   dn.net_r.mean(),np.quantile(b2,.025),np.quantile(b2,.975),(b2<=0).mean(),len(dn)))
res['cost_gate_short_downdays']=dict(mean=round(float(dn.net_r.mean()),5),n=int(len(dn)),
   ci=[round(float(np.quantile(b2,.025)),5),round(float(np.quantile(b2,.975)),5)],p_le0=round(float((b2<=0).mean()),4))
res['direction_terciles_costgate']=rows
json.dump(res,open('final_profile.json','w'),indent=1)
