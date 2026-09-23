"""e1 step 9: DEFINITIVE re-cost using src/costs/spread_model.py (era-true, per-row timestamp,
independent instrument from l10's flat July tick median). Both mid and high band.
Commission/slippage kept identical to l10 so only the spread term changes."""
import sys, json, gzip, datetime as dt, statistics as st
from functools import lru_cache
from collections import defaultdict
sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
from src.costs import spread_model as sm
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
LIVE=json.load(open(f'{D}/L10X_LIVE_COST_PRICEUNITS_V1.json'))
MAP={'SPX500':'US500.cash','NAS100':'US100.cash','JP225':'JP225.cash','UK100':'UK100.cash','GER40':'GER40.cash',
     'US30_cash':'US30.cash','USOIL_cash':'USOIL.cash','UKOIL_cash':'UKOIL.cash'}
JPYCOMM=0.00808905; USDCOMM=5.00048e-05
COMM={'EURUSD':USDCOMM,'GBPUSD':USDCOMM,'AUDUSD':USDCOMM,'NZDUSD':USDCOMM,'USDJPY':JPYCOMM,'GBPJPY':JPYCOMM,
 'EURJPY':JPYCOMM,'AUDJPY':JPYCOMM,'CHFJPY':JPYCOMM,'XAUUSD':0.0576,'XAGUSD':0.001}
SLIP={k:LIVE[k]['slip_px'] for k in LIVE}
SLIPMAP={'XAUUSD':'ftmo:XAUUSD','SPX500':'ftmo:US500.cash','US30_cash':'ftmo:US30.cash','UK100':'ftmo:UK100.cash',
 'GER40':'ftmo:GER40.cash','JP225':'ftmo:JP225.cash','BTCUSD':'ftmo:BTCUSD','ETHUSD':'ftmo:ETHUSD',
 'EURUSD':'ftmo:EURUSD','GBPUSD':'ftmo:GBPUSD','USDJPY':'ftmo:USDJPY','GBPJPY':'ftmo:GBPJPY'}
BTC=39.2778/88599.74*1e4
CEIL=('SPX500','NAS100','JP225','UK100','GER40','US30_cash','ETHUSD','EURJPY','CHFJPY')
@lru_cache(maxsize=200000)
def spx(sym,iso_hour,band):
    t=dt.datetime.fromisoformat(iso_hour).replace(tzinfo=dt.timezone.utc)
    try: return sm.spread_price(MAP.get(sym,sym),'FTMO',t,band=band).spread_price
    except Exception: return None
def cpx(s,ep):
    if s=='BTCUSD': return BTC*ep/1e4
    if s=='ETHUSD': return 1.09905
    if s in ('USDCHF','USDCAD'): return USDCOMM*ep
    if s=='EURGBP': return USDCOMM*0.74
    return COMM.get(s,0.0)
def m(v): return round(st.mean(v),6) if v else None
res={'method':'spread term from src/costs/spread_model.spread_price(FTMO, per-row decision hour, band); commission+slippage identical to l10x_06.'}
for mo in ('JAN','FEB','MAR','APR','MAY'):
    R=[]; miss=defaultdict(int)
    for l in gzip.open(f'/tmp/e1x/e1_slice_{mo}.jsonl.gz','rt'):
        r=json.loads(l)
        if r['missed_opportunity_r_scoreability_status']!='diagnostic_opportunity_r_scoreable': continue
        if r['opportunity_net_proxy_r'] is None: continue
        ep,sl,spr,tc,dtu=r['entry_price'],r['stop_loss'],r['spread_r'],r['expected_cost_r'],r['decision_time_utc']
        if ep in (None,0) or sl is None or spr is None or tc is None or not dtu: continue
        rd=abs(ep-sl)
        if rd<=0: continue
        hr=str(dtu)[:13]+':00:00'
        sm_mid=spx(r['symbol'],hr,'mid'); sm_hi=spx(r['symbol'],hr,'high')
        if sm_mid is None: miss[r['symbol']]+=1; continue
        cost=r['cost_r'] if r['cost_r'] is not None else tc
        oth=cpx(r['symbol'],ep)/rd+max(SLIP.get(SLIPMAP.get(r['symbol'],''),0.0) or 0.0,0.0)/rd
        R.append({'sym':r['symbol'],'g':r['opportunity_net_proxy_r']+cost,'f':tc,'fs':spr,
          'es':sm_mid/rd,'et':sm_mid/rd+oth,'hs':sm_hi/rd,'ht':sm_hi/rd+oth,
          'fam':r['origin_family'],'ses':r['route_session']})
    n=len(R)
    pf=[x for x in R if x['fs']<=0.10+1e-12 and x['f']<=0.15+1e-12]
    pe=[x for x in R if x['es']<=0.10+1e-12 and x['et']<=0.15+1e-12]
    ph=[x for x in R if x['hs']<=0.10+1e-12 and x['ht']<=0.15+1e-12]
    C=[x for x in R if x['sym'] in CEIL]
    res[mo]={'n':n,'missing':dict(miss),
      'frozen_cost_mean':m([x['f'] for x in R]),'eratrue_mid_cost_mean':m([x['et'] for x in R]),
      'eratrue_high_cost_mean':m([x['ht'] for x in R]),
      'ratio_frozen_over_eratrue_mid':round(st.mean([x['f'] for x in R])/st.mean([x['et'] for x in R]),4),
      'ratio_frozen_over_eratrue_high':round(st.mean([x['f'] for x in R])/st.mean([x['ht'] for x in R]),4),
      'gate_pass_frozen':len(pf),'gate_pass_eratrue_mid':len(pe),'gate_pass_eratrue_high':len(ph),
      'frac_frozen':round(len(pf)/n,5),'frac_eratrue_mid':round(len(pe)/n,5),'frac_eratrue_high':round(len(ph)/n,5),
      'CEILING':{'n':len(C),'frozen':m([x['f'] for x in C]),'eratrue_mid':m([x['et'] for x in C]),
        'ratio':round(st.mean([x['f'] for x in C])/st.mean([x['et'] for x in C]),3),
        'pass_frozen':sum(1 for x in C if x['fs']<=0.10+1e-12 and x['f']<=0.15+1e-12),
        'pass_eratrue_mid':sum(1 for x in C if x['es']<=0.10+1e-12 and x['et']<=0.15+1e-12),
        'pass_eratrue_high':sum(1 for x in C if x['hs']<=0.10+1e-12 and x['ht']<=0.15+1e-12)},
      'gross_all':m([x['g'] for x in R]),'gross_pass_frozen':m([x['g'] for x in pf]),
      'gross_pass_eratrue_mid':m([x['g'] for x in pe]),
      'net_eratrue_on_frozen_book':m([x['g']-x['et'] for x in pf]),
      'net_eratrue_on_eratrue_book':m([x['g']-x['et'] for x in pe]),
      'error_frozen_minus_eratrue_ALL':m([x['f']-x['et'] for x in R]),
      'error_frozen_minus_eratrue_PASSED':m([x['f']-x['et'] for x in pf])}
    # per-symbol overcharge at era truth
    per=defaultdict(list)
    for x in R: per[x['sym']].append(x)
    res[mo]['per_symbol_ratio']={k:round(st.median([x['f'] for x in v])/max(1e-12,st.median([x['et'] for x in v])),3) for k,v in per.items()}
    print(mo,'done n=',n,flush=True)
json.dump(res,open(f'{D}/E1_ERATRUE_RECOST_V1.json','w'),indent=1)
print(f"\n{'mo':<5}{'n':>7}{'frozC':>9}{'eraC':>9}{'ratio':>7}{'eraHiC':>9}{'rHi':>6}{'passF':>7}{'passE':>7}{'passEHi':>8}{'ceilPF':>8}{'ceilPE':>8}{'errAll':>9}{'errPass':>9}")
for mo in ('JAN','FEB','MAR','APR','MAY'):
    v=res[mo]; c=v['CEILING']
    print(f"{mo:<5}{v['n']:>7}{v['frozen_cost_mean']:>9.4f}{v['eratrue_mid_cost_mean']:>9.4f}{v['ratio_frozen_over_eratrue_mid']:>7.2f}{v['eratrue_high_cost_mean']:>9.4f}{v['ratio_frozen_over_eratrue_high']:>6.2f}{v['gate_pass_frozen']:>7}{v['gate_pass_eratrue_mid']:>7}{v['gate_pass_eratrue_high']:>8}{c['pass_frozen']:>8}{c['pass_eratrue_mid']:>8}{v['error_frozen_minus_eratrue_ALL']:>9.4f}{v['error_frozen_minus_eratrue_PASSED']:>9.4f}")
