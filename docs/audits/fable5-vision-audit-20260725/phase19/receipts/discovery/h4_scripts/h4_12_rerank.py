"""h4: the cell hunt object — per-symbol edge:cost at the k=5 TRAIL025 contract, re-costed on live truth."""
import sys, json, statistics as st, collections, datetime as dt
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
E='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/'
sys.path.insert(0,D); sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
import w0_ws
from src.utils import broker_clock as BC
PSY=json.load(open(D+'/E_ATMKT_PERSYMBOL_V1.json'))
HRS=json.load(open(D+'/h4_SPREAD_HOURAWARE_V1.json'))['per_symbol']
DEC=json.load(open(D+'/h4_TOLL_DECOMP_V1.json'))
CT=json.load(open(D+'/h4_CORRECTED_TOLL_V1.json'))
SW={r['symbol']:r for r in CT['per_symbol']}
EX=CT['exit_slip_by_class_bps']
rows=w0_ws.load(); RULE=BC.resolve_rule('FTMO-Server3')
sy={x['name']:x for x in (json.loads(l) for l in open(E+'ftmo_symbols_get.jsonl'))}
BMAP={'SPX500':'US500.cash','NAS100':'US100.cash','US30_cash':'US30.cash','UK100':'UK100.cash',
      'GER40':'GER40.cash','JP225':'JP225.cash','UKOIL_cash':'UKOIL.cash','USOIL_cash':'USOIL.cash'}
CLS={'BTCUSD':'crypto','ETHUSD':'crypto','XAUUSD':'metals','XAGUSD':'metals'}
def cls(s):
    if s in CLS: return CLS[s]
    if s in ('UK100','JP225','GER40','NAS100','SPX500','US30_cash'): return 'index'
    if 'OIL' in s.upper(): return 'energy'
    return 'fx'
def nightly(sym,side,px):
    s=sy.get(BMAP.get(sym,sym));
    if not s: return None
    v=s.get('swap_long') if side=='LONG' else s.get('swap_short')
    if v is None: return None
    if s.get('swap_mode')==1: return (-v)*s.get('point',0)/px*1e4
    if s.get('swap_mode') in (5,6): return (-v)/100.0/360.0*1e4
    return None
# per-symbol expected swap charge per trade at 2 h (January pool hour mix, triple-swap aware)
swapc={}
for sym in PSY:
    g=[r for r in rows if r['symbol']==sym]
    tot=0.0
    for r in g:
        t=dt.datetime.fromisoformat(r['decision_time_utc'])
        b0=BC.utc_to_broker_naive(t,RULE); b1=BC.utc_to_broker_naive(t+dt.timedelta(hours=2),RULE)
        if b1.date()==b0.date(): continue
        b=nightly(sym,r['side'],r['entry_price'])
        if b is None: continue
        s=sy.get(BMAP.get(sym,sym)) or {}
        m=3.0 if (s.get('swap_rollover3days') is not None and b1.weekday()==(s['swap_rollover3days']-1)%7) else 1.0
        tot+=max(b,0.0)*m
    swapc[sym]=tot/len(g) if g else 0.0
tab=[]
for sym,v in PSY.items():
    c0=v['cost_bps']; e=v['edge_bps']
    s0=DEC[sym]['spread_bps'] or 0.0; s1=HRS.get(sym,{}).get('hour_aware_mean_bps',s0)
    c1=SW[sym]['comm_live_bps']; sl=SW[sym]['slip_live_bps']
    c_corr=s1+c1+sl
    c_all=c_corr+swapc[sym]+EX.get(cls(sym),EX['fx'])
    tab.append(dict(symbol=sym,n=v['n'],edge_bps=e,by_month=v['by_month'],t=v['t'],
      cost_pub=c0,ratio_pub=v['ratio'],
      cost_corrected=round(c_corr,4),ratio_corrected=round(e/c_corr,4),
      cost_all_in=round(c_all,4),ratio_all_in=round(e/c_all,4),
      swap_bps=round(swapc[sym],4),exit_slip_bps=round(EX.get(cls(sym),EX['fx']),4),
      net_pub=round(e-c0,4),net_corrected=round(e-c_corr,4),net_all_in=round(e-c_all,4)))
tab.sort(key=lambda r:-r['ratio_all_in'])
print('=== k=5 TRAIL025 at-market, 3 months, RE-COSTED ON LIVE TRUTH ===')
print('{:12s} {:>5s} {:>8s} {:>8s} {:>7s} {:>9s} {:>7s} {:>9s} {:>7s}'.format('sym','n','edge','costPub','ratPub','costCorr','ratCorr','costAllIn','ratAll'))
for r in tab:
    print('{:12s} {:5d} {:8.4f} {:8.4f} {:7.3f} {:9.4f} {:7.3f} {:9.4f} {:7.3f}'.format(
      r['symbol'],r['n'],r['edge_bps'],r['cost_pub'],r['ratio_pub'],r['cost_corrected'],r['ratio_corrected'],
      r['cost_all_in'],r['ratio_all_in']))
N=sum(r['n'] for r in tab)
for k in ('cost_pub','cost_corrected','cost_all_in'):
    print('  weighted %-14s %.4f bps'%(k,sum(r[k]*r['n'] for r in tab)/N))
print('  weighted edge          %.4f bps'%(sum(r['edge_bps']*r['n'] for r in tab)/N))
print('  cells with ratio>1: pub %d  corrected %d  all-in %d'%(
  sum(1 for r in tab if r['ratio_pub']>1),sum(1 for r in tab if r['ratio_corrected']>1),sum(1 for r in tab if r['ratio_all_in']>1)))
json.dump(dict(contract='k5_TRAIL025_at_market_3months',n_total=N,per_symbol=tab,
  weighted_cost_pub=round(sum(r['cost_pub']*r['n'] for r in tab)/N,4),
  weighted_cost_corrected=round(sum(r['cost_corrected']*r['n'] for r in tab)/N,4),
  weighted_cost_all_in=round(sum(r['cost_all_in']*r['n'] for r in tab)/N,4),
  weighted_edge=round(sum(r['edge_bps']*r['n'] for r in tab)/N,4)),
  open(D+'/h4_PERSYMBOL_RERANK_V1.json','w'),indent=1)
