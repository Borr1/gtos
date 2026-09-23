"""e1 step 7: is any PRE-DECLARED cell of the RESTORED universe (rows the frozen gate
refused that a real-cost gate admits) positive net-at-real-cost in all five months?
Grid declared before evaluation: session(4) x stopwidth tercile(3) x cost cohort(3) = 36 cells.
Control: current_breaker_re_entry excluded throughout (98.61% of the Jan un-takeable artifact)."""
import json, gzip, statistics as st
from collections import defaultdict
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
TICK=json.load(open(f'{D}/L10X_TICK_SPREAD_V1.json')); LIVE=json.load(open(f'{D}/L10X_LIVE_COST_PRICEUNITS_V1.json'))
TMAP={'XAUUSD':'XAUUSD','UK100':'UK100_cash','SPX500':'US500_cash','NAS100':'US100_cash','US30_cash':'US30_cash','GBPUSD':'GBPUSD','GER40':'GER40_cash','JP225':'JP225_cash','USDCAD':'USDCAD','BTCUSD':'BTCUSD','EURJPY':'EURJPY','ETHUSD':'ETHUSD','XAGUSD':'XAGUSD','USDCHF':'USDCHF','USDJPY':'USDJPY','EURGBP':'EURGBP','NZDUSD':'NZDUSD','EURUSD':'EURUSD','UKOIL_cash':'UKOIL_cash','GBPJPY':'GBPJPY','AUDJPY':'AUDJPY','USOIL_cash':'USOIL_cash','AUDUSD':'AUDUSD','CHFJPY':'CHFJPY'}
JPYCOMM=0.00808905; USDCOMM=5.00048e-05
COMM={'EURUSD':USDCOMM,'GBPUSD':USDCOMM,'AUDUSD':USDCOMM,'NZDUSD':USDCOMM,'USDJPY':JPYCOMM,'GBPJPY':JPYCOMM,'EURJPY':JPYCOMM,'AUDJPY':JPYCOMM,'CHFJPY':JPYCOMM,'XAUUSD':0.0576,'XAGUSD':0.001}
SLIP={k:LIVE[k]['slip_px'] for k in LIVE}
SLIPMAP={'XAUUSD':'ftmo:XAUUSD','SPX500':'ftmo:US500.cash','US30_cash':'ftmo:US30.cash','UK100':'ftmo:UK100.cash','GER40':'ftmo:GER40.cash','JP225':'ftmo:JP225.cash','BTCUSD':'ftmo:BTCUSD','ETHUSD':'ftmo:ETHUSD','EURUSD':'ftmo:EURUSD','GBPUSD':'ftmo:GBPUSD','USDJPY':'ftmo:USDJPY','GBPJPY':'ftmo:GBPJPY'}
BTC=39.2778/88599.74*1e4
CEIL=('SPX500','NAS100','JP225','UK100','GER40','US30_cash','ETHUSD','EURJPY','CHFJPY')
FLOOR=('USOIL_cash','UKOIL_cash','BTCUSD')
def rb(s):
    t=TICK.get('ftmo:'+TMAP.get(s,s)); return t.get('spread_bps_median') if t else None
def cpx(s,ep):
    if s=='BTCUSD': return BTC*ep/1e4
    if s=='ETHUSD': return 1.09905
    if s in ('USDCHF','USDCAD'): return USDCOMM*ep
    if s=='EURGBP': return USDCOMM*0.74
    return COMM.get(s,0.0)
def m(v): return round(st.mean(v),6) if v else None
def cohort(s): return 'CEILING' if s in CEIL else ('FLOOR' if s in FLOOR else 'OTHER')
MO=('JAN','FEB','MAR','APR','MAY')
cells=defaultdict(lambda: defaultdict(list)); tot={}
for mo in MO:
    R=[]
    for l in gzip.open(f'/tmp/e1x/e1_slice_{mo}.jsonl.gz','rt'):
        r=json.loads(l)
        if r['missed_opportunity_r_scoreability_status']!='diagnostic_opportunity_r_scoreable': continue
        if r['opportunity_net_proxy_r'] is None: continue
        if r['origin_family']=='current_breaker_re_entry': continue
        ep,sl,spr,tc=r['entry_price'],r['stop_loss'],r['spread_r'],r['expected_cost_r']
        if ep in (None,0) or sl is None or spr is None or tc is None: continue
        rd=abs(ep-sl)
        if rd<=0: continue
        b=rb(r['symbol'])
        if b is None: continue
        cost=r['cost_r'] if r['cost_r'] is not None else tc
        rspr=(b*ep/1e4)/rd; rtot=rspr+cpx(r['symbol'],ep)/rd+max(SLIP.get(SLIPMAP.get(r['symbol'],''),0.0) or 0.0,0.0)/rd
        R.append({'rdp':rd/abs(ep)*100.0,'g':r['opportunity_net_proxy_r']+cost,'rtot':rtot,
          'pf':(spr<=0.10+1e-12 and tc<=0.15+1e-12),'pr':(rspr<=0.10+1e-12 and rtot<=0.15+1e-12),
          'ses':r['route_session'] or 'none','coh':cohort(r['symbol']),'sym':r['symbol'],'fam':r['origin_family']})
    R.sort(key=lambda x:x['rdp']); n=len(R)
    for i,x in enumerate(R): x['tw']=('T1_tight','T2_mid','T3_wide')[min(2,int(3*i/n))]
    NEW=[x for x in R if x['pr'] and not x['pf']]
    tot[mo]={'n_pool_exbrk':n,'n_restored':len(NEW),'restored_net_at_real':m([x['g']-x['rtot'] for x in NEW]),
             'restored_gross':m([x['g'] for x in NEW])}
    for x in NEW: cells[(x['ses'],x['tw'],x['coh'])][mo].append(x['g']-x['rtot'])
    for x in NEW: cells[('ANY',x['tw'],x['coh'])][mo].append(x['g']-x['rtot'])
    for x in NEW: cells[(x['ses'],'ANY',x['coh'])][mo].append(x['g']-x['rtot'])
out={'per_month_totals':tot,'cells':{}}
rows=[]
for k,v in cells.items():
    if len(v)<5: continue
    ns=[len(v[mo]) for mo in MO]
    if min(ns)<30: continue
    mus=[st.mean(v[mo]) for mo in MO]
    rec={'cell':'|'.join(k),'n_by_month':ns,'n_total':sum(ns),'mean_by_month':[round(x,5) for x in mus],
         'pooled_mean':round(sum(sum(v[mo]) for mo in MO)/sum(ns),6),'months_positive':sum(1 for x in mus if x>0)}
    out['cells']['|'.join(k)]=rec; rows.append(rec)
rows.sort(key=lambda r:(-r['months_positive'],-r['pooled_mean']))
json.dump(out,open(f'{D}/E1_RESTORED_GRID_V1.json','w'),indent=1)
print('per-month restored cohort (ex-breaker):')
for mo in MO:
    t=tot[mo]; print(f"  {mo} pool_exbrk={t['n_pool_exbrk']:>6} restored={t['n_restored']:>6} gross={t['restored_gross']:>9.4f} net_at_real={t['restored_net_at_real']:>9.4f}")
print(f"\ncells evaluated: {len(rows)}  (declared grid 4x3x3 + ANY margins, min n=30/month)")
print(f"{'cell':<40}{'nTot':>7}{'mo+':>5}{'pooled':>9}  per-month means")
for r in rows[:16]:
    print(f"{r['cell']:<40}{r['n_total']:>7}{r['months_positive']:>5}{r['pooled_mean']:>9.4f}  {r['mean_by_month']}")
