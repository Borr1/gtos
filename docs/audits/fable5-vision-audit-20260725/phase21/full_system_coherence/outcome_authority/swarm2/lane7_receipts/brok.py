import numpy as np, glob, pandas as pd, json
M='/Users/borr/.claude/jobs/adb9e69b/tmp/m1'
# FN -> FTMO symbol equivalence (same underlying, different broker naming)
EQ={'GER30':'GER40_cash','NDX100':'US100_cash','SPX500':'US500_cash','UK100':'UK100_cash','JP225':'JP225_cash',
    'UKOUSD':'UKOIL_cash','USOUSD':'USOIL_cash','US30':'US30_cash'}
def stats(f):
    z=np.load(f,allow_pickle=True); s=str(z['symbol']); t=z['minute_utc']; n=z['n']; sp=z['sp_sum']/np.maximum(n,1)
    mid=(z['bh']+z['bl']+z['ah']+z['al'])/4.0
    hr=((t*60)//3600)%24
    return s,pd.DataFrame({'hour':hr,'sp':sp,'mid':mid,'n':n})
F={};N={}
for f in glob.glob(f'{M}/FTMO_*.npz'):
    s,d=stats(f); F[s]=d
for f in glob.glob(f'{M}/redacted_account_*.npz'):
    s,d=stats(f); N[EQ.get(s,s)]=d
rows=[]
for s in sorted(set(F)&set(N)):
    a=F[s]; b=N[s]
    aw=np.average(a.sp,weights=a.n); bw=np.average(b.sp,weights=b.n)
    am=np.average(a.mid,weights=a.n); bm=np.average(b.mid,weights=b.n)
    rows.append(dict(symbol=s, ftmo_spread=aw, fn_spread=bw, ftmo_mid=am, fn_mid=bm,
        ftmo_bps=aw/am*1e4, fn_bps=bw/bm*1e4, fn_over_ftmo=(bw/bm)/(aw/am),
        ftmo_min=int(a.n.sum()), fn_min=int(b.n.sum())))
t=pd.DataFrame(rows).sort_values('fn_over_ftmo')
pd.set_option('display.width',250)
print('=== (E) BROKER SPREAD ARBITRAGE — true tick spreads, same 2026-06-18..07-24 window, both hosts ===')
print(t.round(4).to_string(index=False))
print()
print('cheaper on FTMO:', int((t.fn_over_ftmo>1.02).sum()), ' cheaper on redacted_account:', int((t.fn_over_ftmo<0.98).sum()), ' within 2%:', int(((t.fn_over_ftmo>=0.98)&(t.fn_over_ftmo<=1.02)).sum()))
t.to_json('/Users/borr/.claude/jobs/adb9e69b/tmp/broker_spread.json',orient='records')
