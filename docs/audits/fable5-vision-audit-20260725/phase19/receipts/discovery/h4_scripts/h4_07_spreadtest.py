"""h4: does the hour-aware spread model beat the flat median AT REAL FILL INSTANTS?"""
import sys, json, statistics as st, collections, datetime as dt
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
from src.utils import broker_clock as BC
TICK=json.load(open(D+'/L10X_TICK_SPREAD_V1.json'))
L=json.load(open(D+'/h4_FILL_LEDGER_RAW.json'))
RULES={'ftmo':BC.resolve_rule('FTMO-Server3'),'redacted_account':BC.resolve_rule('redacted_account-Server 2')}
# broker symbol -> tick-archive key (the archive keys use the broker's own naming)
keys=set(TICK)
def tk_for(broker,bsym):
    for cand in (bsym, bsym.replace('.cash','_cash'), bsym.replace('.','_')):
        k=f'{broker}:{cand}'
        if k in keys: return TICK[k]
    return None
rec=[];miss=collections.Counter()
for x in L:
    if not (x['ask'] and x['bid'] and x['broker']): continue
    tk=tk_for(x['broker'],x['bsym'])
    if not tk or not tk.get('spread_bps_median'): miss[f"{x['broker']}:{x['bsym']}"]+=1; continue
    mid=(x['ask']+x['bid'])/2.0
    real=(x['ask']-x['bid'])/mid*1e4
    t=dt.datetime.fromisoformat(x['t'])
    bh=BC.utc_to_broker_naive(t,RULES[x['broker']]).hour
    byh=tk.get('spread_bps_median_by_broker_hour') or {}
    ha=byh.get(str(bh))
    rec.append(dict(k=f"{x['broker']}:{x['bsym']}",bh=bh,real=real,flat=tk['spread_bps_median'],hour=ha))
print('fills with tick coverage:',len(rec),' missing:',dict(miss))
have=[r for r in rec if r['hour'] is not None]
def summ(name,err):
    e=[abs(x) for x in err]
    print(f'{name:22s} n={len(err):3d} MAE={st.mean(e):7.4f} bias={st.mean(err):+8.4f} med|e|={st.median(e):7.4f} RMSE={ (st.mean([x*x for x in err]))**.5:7.4f}')
summ('flat median',[r['flat']-r['real'] for r in have])
summ('hour-aware median',[r['hour']-r['real'] for r in have])
# ratio form
print('\nmean model/real ratio  flat: %.4f   hour-aware: %.4f'%(
  st.mean([r['flat']/r['real'] for r in have if r['real']>0]),
  st.mean([r['hour']/r['real'] for r in have if r['real']>0])))
print('mean real spread bps at live fills: %.4f ; flat model mean %.4f ; hour-aware mean %.4f'%(
  st.mean([r['real'] for r in have]), st.mean([r['flat'] for r in have]), st.mean([r['hour'] for r in have])))
json.dump(dict(n=len(have),
  flat=dict(MAE=round(st.mean([abs(r['flat']-r['real']) for r in have]),4),bias=round(st.mean([r['flat']-r['real'] for r in have]),4)),
  hour_aware=dict(MAE=round(st.mean([abs(r['hour']-r['real']) for r in have]),4),bias=round(st.mean([r['hour']-r['real'] for r in have]),4)),
  mean_real_bps=round(st.mean([r['real'] for r in have]),4),
  mean_flat_bps=round(st.mean([r['flat'] for r in have]),4),
  mean_hour_bps=round(st.mean([r['hour'] for r in have]),4),
  missing=dict(miss)), open(D+'/h4_SPREAD_MODEL_TEST_V1.json','w'), indent=1)
