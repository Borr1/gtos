import numpy as np, pandas as pd, json, math, warnings
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C
from panel import make_panel

df=C.build_master()

def evaluate(fd, cols, alpha=10.0, causal_scaler=True, label=''):
    X=fd[cols].fillna(0.0).to_numpy(float)
    y=fd.y.to_numpy(float); w=fd.n.to_numpy(float); d=fd.date.to_numpy()
    ud=np.array(sorted(set(d)))
    if not causal_scaler:
        mu=X.mean(0); sd=X.std(0); sd[sd<1e-12]=1.0; X=(X-mu)/sd
    p=C.wf_ridge(X,y,w,d,ud,alpha=alpha,causal_scaler=causal_scaler)
    ok=~np.isnan(p); rho=stats.spearmanr(p[ok],y[ok]); sel=ok&(p>0)
    r_sel=np.average(y[sel],weights=w[sel]) if sel.sum()>3 else float('nan')
    r_all=np.average(y[ok],weights=w[ok])
    # per-month
    mo=pd.Series(fd.date.dt.strftime('%Y-%m').to_numpy())
    pm={}
    for m in sorted(set(mo[ok])):
        g=ok&(mo==m).to_numpy(); s2=g&(p>0)
        pm[m]=round(float(np.average(y[s2],weights=w[s2])-np.average(y[g],weights=w[g])),5) if s2.sum()>3 else None
    return dict(label=label,n_feat=len(cols),n_oos=int(ok.sum()),rho=round(float(rho.statistic),5),
                p=float('%.3g'%rho.pvalue),trades=int(w[sel].sum()),
                r_sel=round(float(r_sel),5),r_all=round(float(r_all),5),
                delta=round(float(r_sel-r_all),5),months_pos=sum(1 for v in pm.values() if v and v>0),
                per_month=pm),p,ok

EXTRA=C.REGCOLS+[c+'_m5' for c in ['vol','ccvol','spread','cost','trendshare','upshare','rngpos','risk']]+\
      [c+'_d1' for c in ['vol','ccvol','spread','cost','trendshare','upshare','rngpos','risk']]+['nc_rel','nc_m5']

CFG=[
 ('L0  Lane-6 exact (global scaler, same-day regime)', dict(regime_lag=0), 'lane6', False),
 ('L1  + train-only scaler',                            dict(regime_lag=0), 'lane6', True),
 ('L2  + LAG-1 regime (causal at day open)',            dict(regime_lag=1), 'lane6', True),
 ('L3  + wider causal regime block',                    dict(regime_lag=1, reg_cols=C.REGCOLS), 'wide', True),
 ('L4  + trailing level/change state',                  dict(regime_lag=1, reg_cols=EXTRA, extra_regime=True), 'wide', True),
]
out=[]
print('%-52s %6s %8s %10s %8s %9s %s'%('rung','n_oos','rho','p','trades','delta','months+'))
for label,kw,tag,cs in CFG:
    fd,B=make_panel(df,**kw)
    cols=B['REG']+B['INT']          # M6 arm: regime + interactions only
    r,_,_=evaluate(fd,cols,causal_scaler=cs,label=label)
    r['arm']='M6'; r['cfg']=str(kw); out.append(r)
    print('%-52s %6d %+8.4f %10s %8d %+9.5f %d'%(label,r['n_oos'],r['rho'],r['p'],r['trades'],r['delta'],r['months_pos']))
print()
for label,kw,tag,cs in CFG:
    fd,B=make_panel(df,**kw)
    cols=B['FAM']+B['REG']+B['INT'] # M3 arm
    r,_,_=evaluate(fd,cols,causal_scaler=cs,label=label)
    r['arm']='M3'; r['cfg']=str(kw); out.append(r)
    print('M3 %-49s %6d %+8.4f %10s %8d %+9.5f %d'%(label,r['n_oos'],r['rho'],r['p'],r['trades'],r['delta'],r['months_pos']))
json.dump(out,open('ladder.json','w'),indent=1)
