import json, gzip, statistics as st
from collections import defaultdict
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260725/'
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted'
OUT=f'{D}/L10X_STOP_GEOMETRY_V1.json'
# LIVE: sl_distance as pct of entry price, per symbol
live=defaultdict(list)
for l in open(f'{BASE}/05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl'):
    r=json.loads(l); p=r.get('pretrade_cost_model')
    if not isinstance(p,dict): continue
    ep=p.get('entry_price'); sld=p.get('sl_distance')
    if not ep or not sld: continue
    live[p.get('broker_symbol')].append(sld/ep*100.0)
# POOL: risk_distance as pct of entry price, per symbol
pool=defaultdict(list)
for l in gzip.open(f'{D}/w0_WORKING_SET.jsonl.gz','rt'):
    r=json.loads(l); ep=r.get('entry_price'); rd=r.get('risk_distance')
    if not ep or not rd: continue
    pool[r['symbol']].append(rd/ep*100.0)
ALIAS={'NAS100':['US100.cash','NDX100'],'SPX500':['SPX500','US500.cash'],'US30_cash':['US30.cash','US30'],
 'GER40':['GER40.cash','GER30'],'UK100':['UK100.cash','UK100'],'JP225':['JP225.cash','JP225'],
 'XAUUSD':['XAUUSD'],'XAGUSD':['XAGUSD'],'BTCUSD':['BTCUSD'],'ETHUSD':['ETHUSD'],
 'EURUSD':['EURUSD'],'GBPUSD':['GBPUSD'],'USDJPY':['USDJPY'],'GBPJPY':['GBPJPY'],'AUDUSD':['AUDUSD'],
 'NZDUSD':['NZDUSD'],'EURJPY':['EURJPY'],'AUDJPY':['AUDJPY'],'CHFJPY':['CHFJPY'],'USDCHF':['USDCHF'],
 'USDCAD':['USDCAD'],'EURGBP':['EURGBP'],'UKOIL_cash':['UKOIL.cash','UKOIL'],'USOIL_cash':['USOIL.cash','USOIL']}
res={'method':'stop distance as % of entry price. LIVE = pretrade_cost_model.sl_distance/entry_price over 296 captures. POOL = risk_distance/entry_price over the 27,658-row January working set.',
     'live_by_symbol':{k:{'n':len(v),'median_pct':round(st.median(v),6)} for k,v in sorted(live.items(),key=lambda kv:-len(kv[1]))},
     'pool_by_symbol':{k:{'n':len(v),'median_pct':round(st.median(v),6)} for k,v in sorted(pool.items(),key=lambda kv:-len(kv[1]))}}
cmp={}
for ps,pv in pool.items():
    for c in ALIAS.get(ps,[ps]):
        if c in live and len(live[c])>=3:
            pm=st.median(pv); lm=st.median(live[c])
            cmp[ps]={'broker_symbol':c,'n_pool':len(pv),'n_live':len(live[c]),
                     'pool_stop_pct':round(pm,6),'live_stop_pct':round(lm,6),
                     'live_over_pool':round(lm/pm,3) if pm else None}
            break
res['matched']=dict(sorted(cmp.items(),key=lambda kv:-kv[1]['live_over_pool']))
r=[v['live_over_pool'] for v in cmp.values()]
allp=[x for v in pool.values() for x in v]; alll=[x for v in live.values() for x in v]
res['summary']={'n_symbols':len(r),'median_live_over_pool':round(st.median(r),3),'min':round(min(r),3),'max':round(max(r),3),
  'pool_all_median_stop_pct':round(st.median(allp),6),'live_all_median_stop_pct':round(st.median(alll),6),
  'pooled_ratio':round(st.median(alll)/st.median(allp),3),'n_pool_rows':len(allp),'n_live':len(alll)}
json.dump(res,open(OUT,'w'),indent=1)
print(json.dumps(res['summary'],indent=1))
print(f"{'poolsym':<12}{'brk':<12}{'nP':>6}{'nL':>4}{'poolStop%':>11}{'liveStop%':>11}{'live/pool':>10}")
for k,v in res['matched'].items():
    print(f"{k:<12}{v['broker_symbol']:<12}{v['n_pool']:>6}{v['n_live']:>4}{v['pool_stop_pct']:>11.5f}{v['live_stop_pct']:>11.5f}{v['live_over_pool']:>10}")
