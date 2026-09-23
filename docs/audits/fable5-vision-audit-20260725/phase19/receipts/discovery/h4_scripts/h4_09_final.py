"""h4 FINAL: nightly swap truth, exit-slip in bps, and the CORRECTED toll."""
import sys, json, statistics as st, collections, datetime as dt
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
E='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/'
sys.path.insert(0,D); sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
import w0_ws
from e_lib import TMAP
from src.utils import broker_clock as BC
rows=w0_ws.load()
PS={r['symbol']:r for r in json.load(open(D+'/E_PRICESPACE_V1.json'))['per_symbol_live_realisable']}
DEC=json.load(open(D+'/h4_TOLL_DECOMP_V1.json'))
HRS=json.load(open(D+'/h4_SPREAD_HOURAWARE_V1.json'))['per_symbol']
RULE=BC.resolve_rule('FTMO-Server3')
sy={x['name']:x for x in (json.loads(l) for l in open(E+'ftmo_symbols_get.jsonl'))}
BMAP={'SPX500':'US500.cash','NAS100':'US100.cash','US30_cash':'US30.cash','UK100':'UK100.cash',
      'GER40':'GER40.cash','JP225':'JP225.cash','UKOIL_cash':'UKOIL.cash','USOIL_cash':'USOIL.cash'}
# ---------- nightly swap in bps, FTMO spec truth
swp={}
for sym in sorted(set(r['symbol'] for r in rows)):
    b=BMAP.get(sym,sym); s=sy.get(b)
    if not s: swp[sym]=None; continue
    g=[r for r in rows if r['symbol']==sym]
    px=st.median([r['entry_price'] for r in g])
    mode=s.get('swap_mode'); pt=s.get('point')
    def nb(v):
        if mode==1: return (-v)*pt/px*1e4            # points/night, negative = charge
        if mode in (5,6): return (-v)/360.0*1e4      # annual pct
        return None
    swp[sym]=dict(swap_mode=mode, long_bps=nb(s.get('swap_long')), short_bps=nb(s.get('swap_short')),
                  broker_symbol=b, median_px=round(px,4), roll3=s.get('swap_rollover3days'))
# adverse-side nightly swap per row, only for rows crossing rollover in 2 h
cross_cost=[]; ncross=0
for r in rows:
    t=dt.datetime.fromisoformat(r['decision_time_utc'])
    if BC.utc_to_broker_naive(t+dt.timedelta(hours=2),RULE).date()==BC.utc_to_broker_naive(t,RULE).date(): continue
    ncross+=1
    v=swp.get(r['symbol'])
    if not v: continue
    b=v['long_bps'] if r['side']=='LONG' else v['short_bps']
    if b is None: continue
    cross_cost.append(max(b,0.0))       # charge only adverse swap; credits not banked
print('=== SWAP TRUTH (FTMO symbol specs, nightly) ===')
print('rows crossing rollover in 2h:',ncross,' costed:',len(cross_cost))
print('mean adverse nightly swap on crossing rows: %.4f bps ; median %.4f'%(st.mean(cross_cost),st.median(cross_cost)))
print('=> pool-average uncharged swap = %.4f bps'%(sum(cross_cost)/len(rows)))
swap_pool_bps=sum(cross_cost)/len(rows)

# ---------- exit (stop) slippage in bps, from l10's clean stop exits x live rd_bps by class
SS=json.load(open(D+'/L10_STOP_SLIP_CLEAN_V1.json'))
SL=json.load(open(D+'/h4_SLIPPAGE_TRUTH_V1.json'))
exit_bps={}
for c,v in SS['by_class'].items():
    rd=SL['by_class'].get(c,{}).get('median_rd_bps')
    if rd: exit_bps[c]=dict(n=v['n'],slip_r_mean=v['mean'],live_rd_bps=rd,bps=round(v['mean']*rd,4))
tot_n=sum(v['n'] for v in exit_bps.values())
exit_pooled=sum(v['bps']*v['n'] for v in exit_bps.values())/tot_n
print('\n=== EXIT (STOP) SLIPPAGE, converted to bps at LIVE stop widths ===')
for c,v in exit_bps.items(): print('  %-8s n=%3d  %+.6f R x %.3f rd_bps = %+.4f bps'%(c,v['n'],v['slip_r_mean'],v['live_rd_bps'],v['bps']))
print('  pooled n=%d  %+.4f bps  [the toll charges ZERO for this]'%(tot_n,exit_pooled))

# ---------- CORRECTED TOLL
LIVE_COMM_BPS={'BTCUSD':6.4957,'ETHUSD':6.4674,'UKOIL_cash':5.1738,'USOIL_cash':5.3706,'XAGUSD':0.3222}
LIVE_COMM_SRC={'BTCUSD':'MEASURED ftmo RT median (n=15 entry/14 exit deals); model used 39.2778 px / 88599.74 pool px, the wrong price level',
 'ETHUSD':'MEASURED ftmo RT median (n=8/7); model froze 1.09905 px at ETH 1746 and applied it at pool ETH ~3069',
 'UKOIL_cash':'TRANSFERRED redacted_account RT (n=3 entry, $5.00/lot, identical 100-bbl contract at both firms); model charged 0',
 'USOIL_cash':'TRANSFERRED redacted_account RT (n=3 entry, $5.00/lot, identical 100-bbl contract); model charged 0',
 'XAGUSD':'MEASURED redacted_account 0.1611 bps entry-only x2 for FTMO two-sided schedule; model charged 0.1110'}
LIVE_SLIP_BPS=0.1165     # measured mean entry slippage, n=140 real fills, denomination-free
out=[]; W=0; T0=0; T1=0
for sym,v in DEC.items():
    n=v['n_atmkt'] or 0
    if not n: continue
    spr0=v['spread_bps'] or 0.0
    spr1=HRS.get(sym,{}).get('hour_aware_mean_bps', spr0)
    cm0=v['comm_bps']; cm1=LIVE_COMM_BPS.get(sym,cm0)
    sl0=v['slip_bps']; sl1=LIVE_SLIP_BPS
    t0=spr0+cm0+sl0; t1=spr1+cm1+sl1
    out.append(dict(symbol=sym,n_atmkt=n,spread_flat=round(spr0,4),spread_hour=round(spr1,4),
      comm_model=round(cm0,4),comm_live=round(cm1,4),slip_model=round(sl0,4),slip_live=sl1,
      toll_model=round(t0,4),toll_corrected=round(t1,4),delta=round(t1-t0,4)))
    W+=n; T0+=t0*n; T1+=t1*n
T0/=W; T1/=W
print('\n=== CORRECTED TOLL, January at-market cohort (n=%d) ==='%W)
print('  swarm-published toll                : 2.4428 bps   (my reproduction 2.4429)')
print('  + hour-aware spread                 : %.4f bps'%(T0 + (T1-T0)*0))
print('  corrected (spread+comm+entry slip)  : %.4f bps'%T1)
print('  + uncharged swap on rollover rows   : %.4f bps'%(T1+swap_pool_bps))
print('  + uncharged exit slippage           : %.4f bps'%(T1+swap_pool_bps+exit_pooled))
print('  ratio vs published                  : %.4f'%((T1+swap_pool_bps+exit_pooled)/2.4428))
print('\n{:12s} {:>6s} {:>8s} {:>8s} {:>8s} {:>8s} {:>9s} {:>9s} {:>8s}'.format('sym','n','sprFlat','sprHour','commMod','commLive','tollMod','tollCorr','delta'))
for r in sorted(out,key=lambda r:-r['delta']):
    print('{:12s} {:6d} {:8.4f} {:8.4f} {:8.4f} {:8.4f} {:9.4f} {:9.4f} {:+8.4f}'.format(
      r['symbol'],r['n_atmkt'],r['spread_flat'],r['spread_hour'],r['comm_model'],r['comm_live'],
      r['toll_model'],r['toll_corrected'],r['delta']))
json.dump(dict(per_symbol=out, n_atmkt=W,
  toll_published=2.4428, toll_reproduced=2.4429,
  toll_corrected_3term=round(T1,4),
  swap_uncharged_bps=round(swap_pool_bps,4), exit_slip_uncharged_bps=round(exit_pooled,4),
  toll_all_in=round(T1+swap_pool_bps+exit_pooled,4),
  ratio_vs_published=round((T1+swap_pool_bps+exit_pooled)/2.4428,4),
  live_comm_sources=LIVE_COMM_SRC, live_slip_bps=LIVE_SLIP_BPS,
  swap_nightly_by_symbol={k:v for k,v in swp.items()},
  exit_slip_by_class=exit_bps),
  open(D+'/h4_CORRECTED_TOLL_V1.json','w'), indent=1)
