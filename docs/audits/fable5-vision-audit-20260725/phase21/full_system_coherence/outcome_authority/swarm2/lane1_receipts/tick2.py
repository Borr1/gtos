"""(B) Test the four fill assumptions against ticks, June-18..July-24 2026."""
import pandas as pd, numpy as np, gzip, pickle, glob, os, json
TICK="/Users/borr/GTOSActive/vps-ticks-20260726/ftmo"
MAP={'NAS100':'US100_cash','SPX500':'US500_cash','GER40':'GER40_cash','JP225':'JP225_cash','UK100':'UK100_cash'}
def to_utc(s):
    bn=pd.to_datetime(s,unit="s")
    return (bn-pd.Timedelta(hours=7)).dt.tz_localize("America/New_York",ambiguous=False,
             nonexistent="shift_forward").dt.tz_convert("UTC")
rows=[]
for m in ['jun','jul']:
    for r in pickle.load(gzip.open(f'/private/tmp/laneG-walk/lg_{m}.pkl.gz','rb')):
        o=r.get('orig') or {}
        if not o.get('fill_time'): continue
        rows.append(dict(symbol=r['symbol'],side=r['side'],entry=r['entry_price'],stop=r['stop_price'],
            target=r['target_price'],risk=r['risk_price'],status=o['status'],state=o.get('state'),
            gross=o.get('gross'),fill_price=o['fill_price'],fill_time=o['fill_time'],
            term_time=o.get('terminal_time'),model_spread=r.get('spread_at_fill_price')))
c=pd.DataFrame(rows)
c['ft']=pd.to_datetime(c.fill_time,utc=True); c['tt']=pd.to_datetime(c.term_time,utc=True)
c=c[(c.ft>=pd.Timestamp('2026-06-18',tz='UTC'))&(c.tt<=pd.Timestamp('2026-07-24',tz='UTC'))]
print("rows in tick window:",len(c),flush=True)
res=[];  sprows=[]
for sym,g in c.groupby('symbol'):
    bs=MAP.get(sym,sym); f=f"{TICK}/FTMO_{bs}_ticks_20260618_to_20260726.csv.gz"
    if not os.path.exists(f): print("  skip",sym,flush=True); continue
    t=pd.read_csv(f,usecols=['time_msc','bid','ask']); t['tu']=to_utc(t.time_msc/1000.0)
    t=t.sort_values('tu'); t=t[(t.ask>=t.bid)]
    tv=t.tu.values.astype('datetime64[ns]'); bid=t.bid.values; ask=t.ask.values; sp=ask-bid
    mid=(ask+bid)/2
    # ---- unconditional spread by session (for the Roll comparison)
    hh=pd.DatetimeIndex(t.tu).hour
    for lab,msk in [('ALL',np.ones(len(t),bool)),('late',(hh>=17)),('london',(hh>=7)&(hh<12)),
                    ('newyork',(hh>=12)&(hh<17)),('tokyo',(hh<7))]:
        if msk.sum()>100:
            sprows.append(dict(symbol=sym,sess=lab,n=int(msk.sum()),
                mean_rel_spread=float(np.mean(sp[msk]/mid[msk])),
                med_rel_spread=float(np.median(sp[msk]/mid[msk]))))
    d=g.sort_values('ft'); dr=1*(d.side.values=='LONG')-1*(d.side.values=='SHORT')
    fi=np.clip(np.searchsorted(tv,d.ft.values.astype('datetime64[ns]')),0,len(tv)-1)
    ti=np.clip(np.searchsorted(tv,d.tt.values.astype('datetime64[ns]')),0,len(tv)-1)
    true_entry=np.where(dr>0,ask[fi],bid[fi])          # entry side
    true_exit =np.where(dr>0,bid[ti],ask[ti])          # exit side
    true_sp_fill=sp[fi]
    d=d.assign(true_entry=true_entry,true_exit=true_exit,true_spread_fill=true_sp_fill,
               entry_err_r=dr*(true_entry-d.fill_price.values)/d.risk.values,
               exit_err_r =dr*(true_exit -np.where(d.state.values=='STOP',d.stop.values,
                                np.where(d.state.values=='TARGET',d.target.values,np.nan)))/d.risk.values)
    res.append(d)
    print("  ok",sym,len(d),flush=True)
D=pd.concat(res); S=pd.DataFrame(sprows)
D.to_pickle('tick_fills.pkl'); S.to_csv('tick_spreads.csv',index=False)
print("\n"+"="*95)
print("=== B1. SPREAD MODEL vs TICK TRUTH at the modelled fill instant ===")
D['msr']=D.model_spread/D.risk; D['tsr']=D.true_spread_fill/D.risk
print(f"  n={len(D)}  modelled spread_r mean={D.msr.mean():.5f} median={D.msr.median():.5f}")
print(f"           TRUE tick spread_r mean={D.tsr.mean():.5f} median={D.tsr.median():.5f}")
print(f"  ratio modelled/true: mean={ (D.msr/D.tsr).mean():.4f}  median={(D.msr/D.tsr).median():.4f}")
print(f"  => spread model is {'OVERSTATED' if (D.msr/D.tsr).median()>1 else 'UNDERSTATED'} by {abs((D.msr/D.tsr).median()-1)*100:.1f}% (median ratio)")
print("\n=== B2. ENTRY FILL: true entry-side quote vs modelled fill price (R units, +ve = engine OPTIMISTIC) ===")
print(f"  n={D.entry_err_r.notna().sum()} mean={D.entry_err_r.mean():+.5f} median={D.entry_err_r.median():+.5f} "
      f"p05={D.entry_err_r.quantile(.05):+.4f} p95={D.entry_err_r.quantile(.95):+.4f}")
print("\n=== B3. EXIT FILL at the booked barrier: true exit-side quote vs booked level (R, +ve = engine OPTIMISTIC) ===")
for st in ['STOP','TARGET']:
    s=D[D.state==st]
    print(f"  {st:7s} n={len(s):6d} mean={s.exit_err_r.mean():+.5f} median={s.exit_err_r.median():+.5f} "
          f"p05={s.exit_err_r.quantile(.05):+.4f} p95={s.exit_err_r.quantile(.95):+.4f} "
          f"frac_worse_than_booked={float((s.exit_err_r>0).mean()):.3f}")
print("\n=== B4. per-symbol spread ratio ===")
q=D.groupby('symbol').apply(lambda x: pd.Series({'n':len(x),'model_r':x.msr.mean(),'true_r':x.tsr.mean(),
    'ratio_med':(x.msr/x.tsr).median()}),include_groups=False).sort_values('ratio_med')
print(q.to_string())
