"""e1 step 6: SELECTION ON THE COST MODEL'S OWN ERROR.
The gate keeps rows where frozen cost is LOW. Frozen cost is low exactly where the
frozen model is most wrong in the CHEAP direction. So the admitted book is adversely
selected on the error term. Measure E[frozen-real | passed] vs E[frozen-real | all]."""
import json, gzip, statistics as st
from collections import defaultdict
import importlib.util, sys
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
spec=importlib.util.spec_from_file_location('e1b',f'{D}/e1_scripts/e1_05_boundary.py')
# re-implement load() inline (avoid executing step5's main body)
TICK=json.load(open(f'{D}/L10X_TICK_SPREAD_V1.json'))
LIVE=json.load(open(f'{D}/L10X_LIVE_COST_PRICEUNITS_V1.json'))
TMAP={'XAUUSD':'XAUUSD','UK100':'UK100_cash','SPX500':'US500_cash','NAS100':'US100_cash','US30_cash':'US30_cash',
 'GBPUSD':'GBPUSD','GER40':'GER40_cash','JP225':'JP225_cash','USDCAD':'USDCAD','BTCUSD':'BTCUSD','EURJPY':'EURJPY',
 'ETHUSD':'ETHUSD','XAGUSD':'XAGUSD','USDCHF':'USDCHF','USDJPY':'USDJPY','EURGBP':'EURGBP','NZDUSD':'NZDUSD',
 'EURUSD':'EURUSD','UKOIL_cash':'UKOIL_cash','GBPJPY':'GBPJPY','AUDJPY':'AUDJPY','USOIL_cash':'USOIL_cash',
 'AUDUSD':'AUDUSD','CHFJPY':'CHFJPY'}
JPYCOMM=0.00808905; USDCOMM=5.00048e-05
COMM={'EURUSD':USDCOMM,'GBPUSD':USDCOMM,'AUDUSD':USDCOMM,'NZDUSD':USDCOMM,'USDJPY':JPYCOMM,'GBPJPY':JPYCOMM,
 'EURJPY':JPYCOMM,'AUDJPY':JPYCOMM,'CHFJPY':JPYCOMM,'XAUUSD':0.0576,'XAGUSD':0.001}
SLIP={k:LIVE[k]['slip_px'] for k in LIVE}
SLIPMAP={'XAUUSD':'ftmo:XAUUSD','SPX500':'ftmo:US500.cash','US30_cash':'ftmo:US30.cash','UK100':'ftmo:UK100.cash',
 'GER40':'ftmo:GER40.cash','JP225':'ftmo:JP225.cash','BTCUSD':'ftmo:BTCUSD','ETHUSD':'ftmo:ETHUSD',
 'EURUSD':'ftmo:EURUSD','GBPUSD':'ftmo:GBPUSD','USDJPY':'ftmo:USDJPY','GBPJPY':'ftmo:GBPJPY'}
BTC=39.2778/88599.74*1e4
def rb(s):
    t=TICK.get('ftmo:'+TMAP.get(s,s)); return t.get('spread_bps_median') if t else None
def cpx(s,ep):
    if s=='BTCUSD': return BTC*ep/1e4
    if s=='ETHUSD': return 1.09905
    if s in ('USDCHF','USDCAD'): return USDCOMM*ep
    if s=='EURGBP': return USDCOMM*0.74
    return COMM.get(s,0.0)
def m(v): return round(st.mean(v),6) if v else None
res={}
for mo in ('JAN','FEB','MAR','APR','MAY'):
    R=[]
    for l in gzip.open(f'/tmp/e1x/e1_slice_{mo}.jsonl.gz','rt'):
        r=json.loads(l)
        if r['missed_opportunity_r_scoreability_status']!='diagnostic_opportunity_r_scoreable': continue
        if r['opportunity_net_proxy_r'] is None: continue
        ep,sl,spr,tc=r['entry_price'],r['stop_loss'],r['spread_r'],r['expected_cost_r']
        if ep in (None,0) or sl is None or spr is None or tc is None: continue
        rd=abs(ep-sl)
        if rd<=0: continue
        b=rb(r['symbol'])
        if b is None: continue
        cost=r['cost_r'] if r['cost_r'] is not None else tc
        rspr=(b*ep/1e4)/rd
        rtot=rspr+cpx(r['symbol'],ep)/rd+max(SLIP.get(SLIPMAP.get(r['symbol'],''),0.0) or 0.0,0.0)/rd
        R.append({'g':r['opportunity_net_proxy_r']+cost,'f':tc,'r':rtot,'e':tc-rtot,
                  'pf':(spr<=0.10+1e-12 and tc<=0.15+1e-12),'sym':r['symbol']})
    P=[x for x in R if x['pf']]; Q=[x for x in R if not x['pf']]
    res[mo]={'n':len(R),'n_pass':len(P),
      'ALL':{'frozen':m([x['f'] for x in R]),'real':m([x['r'] for x in R]),'error_frozen_minus_real':m([x['e'] for x in R])},
      'PASSED':{'frozen':m([x['f'] for x in P]),'real':m([x['r'] for x in P]),'error_frozen_minus_real':m([x['e'] for x in P]),
                'gross':m([x['g'] for x in P]),'net_at_frozen':m([x['g']-x['f'] for x in P]),'net_at_real':m([x['g']-x['r'] for x in P])},
      'REFUSED':{'frozen':m([x['f'] for x in Q]),'real':m([x['r'] for x in Q]),'error_frozen_minus_real':m([x['e'] for x in Q]),
                'gross':m([x['g'] for x in Q]),'net_at_real':m([x['g']-x['r'] for x in Q])},
      'SELECTION_ON_ERROR_R_per_trade':round(st.mean([x['e'] for x in P])-st.mean([x['e'] for x in R]),6),
      'UNDERCHARGE_ON_THE_ADMITTED_BOOK':round(st.mean([x['r'] for x in P])-st.mean([x['f'] for x in P]),6),
      'refused_but_real_net_positive':sum(1 for x in Q if x['g']-x['r']>0),
      'refused_real_net_positive_mean_R':m([x['g']-x['r'] for x in Q if x['g']-x['r']>0])}
json.dump(res,open(f'{D}/E1_SELECTION_ON_ERROR_V1.json','w'),indent=1)
print(f"{'mo':<5}{'n':>7}{'nPass':>7}{'errAll':>9}{'errPass':>9}{'errRef':>9}{'selErr':>9}{'underAdm':>10}{'netFroz':>9}{'netReal':>9}")
for mo,v in res.items():
    print(f"{mo:<5}{v['n']:>7}{v['n_pass']:>7}{v['ALL']['error_frozen_minus_real']:>9.4f}{v['PASSED']['error_frozen_minus_real']:>9.4f}{v['REFUSED']['error_frozen_minus_real']:>9.4f}{v['SELECTION_ON_ERROR_R_per_trade']:>9.4f}{v['UNDERCHARGE_ON_THE_ADMITTED_BOOK']:>10.4f}{v['PASSED']['net_at_frozen']:>9.4f}{v['PASSED']['net_at_real']:>9.4f}")
