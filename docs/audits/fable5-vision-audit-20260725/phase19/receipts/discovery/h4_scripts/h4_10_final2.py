"""h4 FINAL v2: fixed swap modes, pool-weighted exit slip, corrected toll."""
import sys, json, statistics as st, collections, datetime as dt
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
E='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/'
sys.path.insert(0,D); sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
import w0_ws
from src.utils import broker_clock as BC
rows=w0_ws.load()
DEC=json.load(open(D+'/h4_TOLL_DECOMP_V1.json'))
HRS=json.load(open(D+'/h4_SPREAD_HOURAWARE_V1.json'))['per_symbol']
RULE=BC.resolve_rule('FTMO-Server3')
sy={x['name']:x for x in (json.loads(l) for l in open(E+'ftmo_symbols_get.jsonl'))}
BMAP={'SPX500':'US500.cash','NAS100':'US100.cash','US30_cash':'US30.cash','UK100':'UK100.cash',
      'GER40':'GER40.cash','JP225':'JP225.cash','UKOIL_cash':'UKOIL.cash','USOIL_cash':'USOIL.cash'}
def nightly_bps(sym,side,px):
    s=sy.get(BMAP.get(sym,sym))
    if not s: return None
    mode=s.get('swap_mode'); v=s.get('swap_long') if side=='LONG' else s.get('swap_short')
    if v is None: return None
    if mode==1: return (-v)*s.get('point',0)/px*1e4
    if mode in (5,6): return (-v)/100.0/360.0*1e4          # annual pct -> nightly bps
    return None
swp_tab={}
for sym in sorted(set(r['symbol'] for r in rows)):
    px=st.median([r['entry_price'] for r in rows if r['symbol']==sym])
    s=sy.get(BMAP.get(sym,sym)) or {}
    swp_tab[sym]=dict(broker_symbol=BMAP.get(sym,sym), swap_mode=s.get('swap_mode'),
        roll3=s.get('swap_rollover3days'), median_px=round(px,4),
        long_bps_per_night=round(nightly_bps(sym,'LONG',px),4) if nightly_bps(sym,'LONG',px) is not None else None,
        short_bps_per_night=round(nightly_bps(sym,'SHORT',px),4) if nightly_bps(sym,'SHORT',px) is not None else None)
cc=[]; ncross=0; triple=0
for r in rows:
    t=dt.datetime.fromisoformat(r['decision_time_utc'])
    b0=BC.utc_to_broker_naive(t,RULE); b1=BC.utc_to_broker_naive(t+dt.timedelta(hours=2),RULE)
    if b1.date()==b0.date(): continue
    ncross+=1
    b=nightly_bps(r['symbol'],r['side'],r['entry_price'])
    if b is None: continue
    mult=1.0
    s=sy.get(BMAP.get(r['symbol'],r['symbol'])) or {}
    if s.get('swap_rollover3days') is not None and b1.weekday()==(s['swap_rollover3days']-1)%7:
        mult=3.0; triple+=1
    cc.append(max(b,0.0)*mult)
swap_pool_bps=sum(cc)/len(rows)
print('=== SWAP AT 2 h (FTMO clock + FTMO spec truth, triple-swap aware) ===')
print('crossing rows %d/%d = %.4f ; triple-swap nights %d'%(ncross,len(rows),ncross/len(rows),triple))
print('mean adverse charge on crossing rows: %.4f bps ; median %.4f ; p90 %.4f'%(st.mean(cc),st.median(cc),sorted(cc)[int(.9*len(cc))]))
print('=> POOL-AVERAGE UNCHARGED SWAP = %.4f bps  (the toll charges 0)'%swap_pool_bps)

# ---- exit slip, weighted by the POOL's own class mix
CLS={'BTCUSD':'crypto','ETHUSD':'crypto','XAUUSD':'metals','XAGUSD':'metals'}
def cls(s):
    if s in CLS: return CLS[s]
    if s in ('UK100','JP225','GER40','NAS100','SPX500','US30_cash'): return 'index'
    if 'OIL' in s.upper(): return 'energy'
    return 'fx'
SS=json.load(open(D+'/L10_STOP_SLIP_CLEAN_V1.json'))
SL=json.load(open(D+'/h4_SLIPPAGE_TRUTH_V1.json'))
ebps={c:SS['by_class'][c]['mean']*SL['by_class'][c]['median_rd_bps'] for c in SS['by_class']}
share=collections.Counter()
for sym,v in DEC.items():
    if v['n_atmkt']: share[cls(sym)]+=v['n_atmkt']
tot=sum(share.values())
exit_pool=sum(ebps.get(c,ebps['fx'])*n for c,n in share.items())/tot   # energy -> fx proxy
print('\n=== EXIT (STOP) SLIPPAGE in bps, pool-class-weighted ===')
for c in sorted(share): print('  %-8s pool share %.4f  live exit slip %.4f bps'%(c,share[c]/tot,ebps.get(c,ebps['fx'])))
print('  POOL-WEIGHTED UNCHARGED EXIT SLIPPAGE = %.4f bps'%exit_pool)

LIVE_COMM_BPS={'BTCUSD':6.4957,'ETHUSD':6.4674,'UKOIL_cash':5.1738,'USOIL_cash':5.3706,'XAGUSD':0.3222}
LIVE_SLIP_BPS=0.1165
out=[];W=0;T0=0;Tsp=0;T1=0
for sym,v in DEC.items():
    n=v['n_atmkt'] or 0
    if not n: continue
    s0=v['spread_bps'] or 0.0; s1=HRS.get(sym,{}).get('hour_aware_mean_bps',s0)
    c0=v['comm_bps']; c1=LIVE_COMM_BPS.get(sym,c0); l0=v['slip_bps']
    t0=s0+c0+l0; tsp=s1+c0+l0; t1=s1+c1+LIVE_SLIP_BPS
    out.append(dict(symbol=sym,n_atmkt=n,spread_flat_bps=round(s0,4),spread_hour_bps=round(s1,4),
      comm_model_bps=round(c0,4),comm_live_bps=round(c1,4),slip_model_bps=round(l0,4),slip_live_bps=LIVE_SLIP_BPS,
      toll_model_bps=round(t0,4),toll_corrected_bps=round(t1,4),delta_bps=round(t1-t0,4),
      swap_long_bps_night=swp_tab[sym]['long_bps_per_night'],swap_short_bps_night=swp_tab[sym]['short_bps_per_night']))
    W+=n;T0+=t0*n;Tsp+=tsp*n;T1+=t1*n
T0/=W;Tsp/=W;T1/=W
ladder=[('published (e-stack)',2.4428),('my reproduction',round(T0,4)),
        ('+ hour-aware spread',round(Tsp,4)),('+ live commission + live entry slip',round(T1,4)),
        ('+ uncharged swap at 2h',round(T1+swap_pool_bps,4)),
        ('+ uncharged exit slippage',round(T1+swap_pool_bps+exit_pool,4))]
print('\n=== TOLL LADDER, January at-market cohort n=%d ==='%W)
for k,v in ladder: print('  %-38s %8.4f bps'%(k,v))
print('  ratio all-in / published: %.4f'%((T1+swap_pool_bps+exit_pool)/2.4428))
print('  edge/cost at published toll: 0.231/2.4428 = %.4f'%(0.231/2.4428))
print('  edge/cost at all-in toll   : 0.231/%.4f = %.4f'%(T1+swap_pool_bps+exit_pool,0.231/(T1+swap_pool_bps+exit_pool)))
json.dump(dict(n_atmkt=W,ladder=dict(ladder),per_symbol=out,swap_table=swp_tab,
  swap_uncharged_bps=round(swap_pool_bps,4),n_cross=ncross,cross_share=round(ncross/len(rows),6),
  n_triple=triple,exit_slip_uncharged_bps=round(exit_pool,4),exit_slip_by_class_bps={k:round(v,4) for k,v in ebps.items()},
  pool_class_share={k:round(v/tot,4) for k,v in share.items()},
  live_comm_bps=LIVE_COMM_BPS,live_slip_bps=LIVE_SLIP_BPS),
  open(D+'/h4_CORRECTED_TOLL_V1.json','w'),indent=1)
