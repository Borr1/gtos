"""B6 step 1 — reproduce Lane 6 as control, then walk the causality ladder."""
import numpy as np, pandas as pd, json, math, warnings, sys
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C
from panel import make_panel

df=C.build_master()
res={}

def evaluate(fd, cols, alpha=10.0, causal_scaler=True, label=''):
    X=fd[cols].fillna(0.0).to_numpy(float)
    y=fd.y.to_numpy(float); w=fd.n.to_numpy(float); d=fd.date.to_numpy()
    ud=np.array(sorted(set(d)))
    if not causal_scaler:
        mu=X.mean(0); sd=X.std(0); sd[sd<1e-12]=1.0; X=(X-mu)/sd
    p=C.wf_ridge(X,y,w,d,ud,alpha=alpha,causal_scaler=causal_scaler)
    ok=~np.isnan(p)
    rho=stats.spearmanr(p[ok],y[ok])
    sel=ok&(p>0)
    r_sel=np.average(y[sel],weights=w[sel]) if sel.sum()>3 else float('nan')
    r_all=np.average(y[ok],weights=w[ok])
    return dict(label=label,n_feat=len(cols),n_oos=int(ok.sum()),n_days=int(len(set(d[ok]))),
                rho=round(float(rho.statistic),5),p=float('%.3g'%rho.pvalue),
                n_sel=int(sel.sum()),trades=int(w[sel].sum()),
                r_sel=round(float(r_sel),5),r_all=round(float(r_all),5),
                delta=round(float(r_sel-r_all),5)),p,ok

print('='*96)
print('STEP 1 — REPRODUCTION OF LANE 6 (control): global scaler, same-day regime, Lane-6 feature set')
print('='*96)
fd0,B0=make_panel(df, regime_lag=0)
print('panel: %d family-days after warm-up, %d families, %d days'%(len(fd0),len(B0['fams']),fd0.date.nunique()))
ARMS0={'M0 family only':B0['FAM'],'M1 family+momentum':B0['FAM']+B0['MOM'],
       'M2 family+regime':B0['FAM']+B0['REG'],'M3 family+regime+int':B0['FAM']+B0['REG']+B0['INT'],
       'M4 FULL':B0['FAM']+B0['REG']+B0['INT']+B0['MOM'],'M5 regime only':B0['REG'],
       'M6 regime+int only':B0['REG']+B0['INT'],'M7 momentum only':B0['MOM']}
tab=[]
print('%-24s %6s %8s %10s %9s %10s %10s'%('arm','n_oos','rho','p','trades','R/tr sel','delta'))
for name,cols in ARMS0.items():
    r,_,_=evaluate(fd0,cols,causal_scaler=False,label=name)
    tab.append(r); print('%-24s %6d %+8.4f %10s %9d %+10.5f %+10.5f'%(name,r['n_oos'],r['rho'],r['p'],r['trades'],r['r_sel'],r['delta']))
res['repro_lane6']=tab
json.dump(res,open('repro.json','w'),indent=1)
