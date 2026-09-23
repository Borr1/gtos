"""h4 core measurement: spread hour-awareness, slippage, swap-at-2h, exit slip, corrected toll."""
import sys, json, statistics as st, collections, datetime as dt
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
sys.path.insert(0,D); sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
import w0_ws
from e_lib import TMAP
from src.utils import broker_clock as BC
TICK=json.load(open(D+'/L10X_TICK_SPREAD_V1.json'))
PS={r['symbol']:r for r in json.load(open(D+'/E_PRICESPACE_V1.json'))['per_symbol_live_realisable']}
rows=w0_ws.load()
RULE=BC.resolve_rule('FTMO-Server3')
print('rule', RULE.name if hasattr(RULE,'name') else RULE)

def agg(v,r=6):
    v=[x for x in v if x is not None]
    if not v: return None
    s=sorted(v)
    def q(p): return s[max(0,min(len(s)-1,int(round(p*(len(s)-1)))))]
    return dict(n=len(v),mean=round(st.mean(v),r),median=round(q(.5),r),p10=round(q(.1),r),p90=round(q(.9),r),
                min=round(min(v),r),max=round(max(v),r))

# ---------- B. SPREAD: flat median vs hour-aware, on the pool's own hour distribution
res_hour={}
hourmiss=collections.Counter()
for sym in sorted(set(r['symbol'] for r in rows)):
    tk=TICK.get('ftmo:'+TMAP.get(sym,sym))
    if not tk or not tk.get('spread_bps_median'): continue
    byh=tk.get('spread_bps_median_by_broker_hour') or {}
    g=[r for r in rows if r['symbol']==sym]
    vals=[]
    for r in g:
        t=dt.datetime.fromisoformat(r['decision_time_utc'])
        bh=BC.utc_to_broker_naive(t, RULE).hour
        v=byh.get(str(bh))
        if v is None: hourmiss[sym]+=1; continue
        vals.append(v)
    if not vals: continue
    res_hour[sym]=dict(n=len(g), n_hour_covered=len(vals),
        flat_median_bps=round(tk['spread_bps_median'],4),
        hour_aware_mean_bps=round(st.mean(vals),4),
        ratio=round(st.mean(vals)/tk['spread_bps_median'],4),
        n_atmkt=PS.get(sym,{}).get('n'))
print('\n--- SPREAD: flat per-symbol median vs pool-hour-weighted (broker hour) ---')
print('{:12s} {:>6s} {:>9s} {:>11s} {:>7s}'.format('sym','nAtMkt','flatMed','hourAware','ratio'))
for s in sorted(res_hour, key=lambda s:-(res_hour[s]['n_atmkt'] or 0)):
    v=res_hour[s]
    print('{:12s} {:6d} {:9.4f} {:11.4f} {:7.4f}'.format(s, v['n_atmkt'] or 0, v['flat_median_bps'], v['hour_aware_mean_bps'], v['ratio']))
wn=sum(v['n_atmkt'] for v in res_hour.values() if v['n_atmkt'])
flat=sum(v['flat_median_bps']*v['n_atmkt'] for v in res_hour.values() if v['n_atmkt'])/wn
hra =sum(v['hour_aware_mean_bps']*v['n_atmkt'] for v in res_hour.values() if v['n_atmkt'])/wn
print(f'\nat-market weighted spread: flat {flat:.4f} bps  hour-aware {hra:.4f} bps  ratio {hra/flat:.4f}')
json.dump(dict(per_symbol=res_hour, weighted_flat_bps=round(flat,4), weighted_hour_aware_bps=round(hra,4),
    ratio=round(hra/flat,4), n_weight=wn, hour_missing=dict(hourmiss)),
    open(D+'/h4_SPREAD_HOURAWARE_V1.json','w'), indent=1)
