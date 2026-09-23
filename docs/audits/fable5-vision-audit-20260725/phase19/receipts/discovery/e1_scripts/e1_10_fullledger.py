"""e1 step 10: era-true recost over the FULL MISSED_OPPORTUNITY ledger (all months).
The 82% of the ledger outside the diagnostic pool carries NO opportunity_net_proxy_r, so this
pass reads ZERO economics - it is a pure decidability measurement."""
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
@lru_cache(maxsize=400000)
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
res={'note':'FULL ledger, all rows (pool and non-pool). No economics field is read anywhere in this pass.'}
for mo in ('JAN','FEB','MAR','APR','MAY'):
    n=0; skipped=0; F=[]; E=[]; H=[]; pf=pe=ph=0; cn=cpf=cpe=0
    for l in gzip.open(f'/tmp/e1x/e1_slice_{mo}.jsonl.gz','rt'):
        r=json.loads(l)
        ep,sl,spr,tc,dtu=r['entry_price'],r['stop_loss'],r['spread_r'],r['expected_cost_r'],r['decision_time_utc']
        if ep in (None,0) or sl is None or spr is None or tc is None or not dtu: skipped+=1; continue
        rd=abs(ep-sl)
        if rd<=0: skipped+=1; continue
        s=r['symbol']; hr=str(dtu)[:13]+':00:00'
        a=spx(s,hr,'mid'); b=spx(s,hr,'high')
        if a is None: skipped+=1; continue
        oth=cpx(s,ep)/rd+max(SLIP.get(SLIPMAP.get(s,''),0.0) or 0.0,0.0)/rd
        es,et=a/rd,a/rd+oth; hs,ht=b/rd,b/rd+oth
        n+=1; F.append(tc); E.append(et); H.append(ht)
        okf=(spr<=0.10+1e-12 and tc<=0.15+1e-12); oke=(es<=0.10+1e-12 and et<=0.15+1e-12); okh=(hs<=0.10+1e-12 and ht<=0.15+1e-12)
        pf+=okf; pe+=oke; ph+=okh
        if s in CEIL: cn+=1; cpf+=okf; cpe+=oke
    res[mo]={'rows_costed':n,'rows_skipped':skipped,
      'frozen_cost_mean':m(F),'eratrue_mid_cost_mean':m(E),'eratrue_high_cost_mean':m(H),
      'ratio_mid':round(st.mean(F)/st.mean(E),4),'ratio_high':round(st.mean(F)/st.mean(H),4),
      'pass_frozen':pf,'pass_eratrue_mid':pe,'pass_eratrue_high':ph,
      'frac_frozen':round(pf/n,5),'frac_eratrue_mid':round(pe/n,5),'frac_eratrue_high':round(ph/n,5),
      'restored_rows':pe-pf,'restored_pct':round((pe-pf)/max(1,pf)*100,2),
      'CEILING_n':cn,'CEILING_pass_frozen':cpf,'CEILING_pass_eratrue_mid':cpe}
    print(mo,'n',n,'skipped',skipped,flush=True)
json.dump(res,open(f'{D}/E1_FULLLEDGER_ERATRUE_V1.json','w'),indent=1)
print(f"\n{'mo':<5}{'n':>8}{'frozC':>9}{'eraC':>9}{'ratio':>7}{'passF':>8}{'passE':>8}{'restored':>10}{'rest%':>8}{'ceilN':>8}{'ceilPF':>8}{'ceilPE':>8}")
for mo in ('JAN','FEB','MAR','APR','MAY'):
    v=res[mo]
    print(f"{mo:<5}{v['rows_costed']:>8}{v['frozen_cost_mean']:>9.4f}{v['eratrue_mid_cost_mean']:>9.4f}{v['ratio_mid']:>7.2f}{v['pass_frozen']:>8}{v['pass_eratrue_mid']:>8}{v['restored_rows']:>10}{v['restored_pct']:>8.1f}{v['CEILING_n']:>8}{v['CEILING_pass_frozen']:>8}{v['CEILING_pass_eratrue_mid']:>8}")
