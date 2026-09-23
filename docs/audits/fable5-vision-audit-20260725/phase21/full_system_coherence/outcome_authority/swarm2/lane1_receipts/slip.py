"""True barrier-crossing slippage: first tick whose EXIT-SIDE quote crosses the booked barrier,
then the achievable fill AT that tick.  This is the one engine optimism that does NOT cancel."""
import pandas as pd, numpy as np, gzip, pickle, os, json
TICK="/Users/borr/GTOSActive/vps-ticks-20260726/ftmo"
MAP={'NAS100':'US100_cash','SPX500':'US500_cash','GER40':'GER40_cash','JP225':'JP225_cash','UK100':'UK100_cash'}
def to_utc(s):
    bn=pd.to_datetime(s,unit="s")
    return (bn-pd.Timedelta(hours=7)).dt.tz_localize("America/New_York",ambiguous=False,
             nonexistent="shift_forward").dt.tz_convert("UTC")
D=pd.read_pickle('tick_fills.pkl')
D=D[D.state.isin(['STOP','TARGET'])]
print("barrier-resolved rows in tick window:",len(D),flush=True)
out=[]
for sym,g in D.groupby('symbol'):
    bs=MAP.get(sym,sym); f=f"{TICK}/FTMO_{bs}_ticks_20260618_to_20260726.csv.gz"
    if not os.path.exists(f): continue
    t=pd.read_csv(f,usecols=['time_msc','bid','ask']); t['tu']=to_utc(t.time_msc/1000.0)
    t=t.sort_values('tu'); t=t[t.ask>=t.bid]
    tv=t.tu.values.astype('datetime64[ns]'); bid=t.bid.values; ask=t.ask.values
    rows=[]
    for _,r in g.iterrows():
        a=np.searchsorted(tv,np.datetime64(r.ft.tz_localize(None)))
        z=np.searchsorted(tv,np.datetime64(r.tt.tz_localize(None)),side='right')
        z=min(z+1,len(tv))
        if z<=a: continue
        d=1.0 if r.side=='LONG' else -1.0
        lvl=r.stop if r.state=='STOP' else r.target
        ex=bid[a:z] if d>0 else ask[a:z]          # exit side
        cross=(ex<=lvl) if (d>0)==(r.state=='STOP') else (ex>=lvl)
        if not cross.any(): continue
        j=int(np.argmax(cross)); fill=ex[j]
        # engine booked at lvl.  realised R deficit vs engine, in R units (+ve = engine optimistic)
        opt=d*(lvl-fill)/r.risk
        rows.append(dict(symbol=sym,state=r.state,side=r.side,opt=opt,lvl=lvl,fill=fill,
                         risk=r.risk,ticks_scanned=int(z-a)))
    out+= rows
    print("  ",sym,len(rows),flush=True)
S=pd.DataFrame(out); S.to_pickle('slip.pkl')
print("\n"+"="*90)
print("=== TRUE BARRIER-CROSSING SLIPPAGE (R units; +ve = the engine's booked price is BETTER than achievable) ===")
for st in ['STOP','TARGET']:
    s=S[S.state==st]
    print(f"  {st:7s} n={len(s):6d} mean={s.opt.mean():+.5f} median={s.opt.median():+.5f} "
          f"p75={s.opt.quantile(.75):+.4f} p95={s.opt.quantile(.95):+.4f} p99={s.opt.quantile(.99):+.4f} "
          f"frac>0={float((s.opt>0).mean()):.3f}")
pS=(S.state=='STOP').mean(); pT=(S.state=='TARGET').mean()
b=pS*S[S.state=='STOP'].opt.mean()+pT*S[S.state=='TARGET'].opt.mean()
print(f"\n  barrier-mix in this sample: STOP {pS:.3f} / TARGET {pT:.3f}")
print(f"  ENGINE OPTIMISM per barrier-resolved trade = {b:+.5f} R")
print(f"  (barrier-resolved are 74.2% of all resolved rows -> {0.742*b:+.5f} R per resolved trade)")
json.dump(dict(stop_mean=float(S[S.state=='STOP'].opt.mean()),target_mean=float(S[S.state=='TARGET'].opt.mean()),
    n_stop=int((S.state=='STOP').sum()),n_target=int((S.state=='TARGET').sum()),
    optimism_per_barrier_trade=float(b),optimism_per_resolved_trade=float(0.742*b)),
    open('slip_summary.json','w'),indent=2)
