import json, gzip, statistics as st
from collections import defaultdict
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted'
OUT=f'{D}/L10X_SPREAD_BPS_V1.json'
# --- REAL: every live pretrade capture that carries a captured broker quote
real=defaultdict(list)
realbroker=defaultdict(set)
n_cap=0;n_skip=0
for l in open(f'{BASE}/05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl'):
    r=json.loads(l); p=r.get('pretrade_cost_model')
    if not isinstance(p,dict): continue
    tc=p.get('tick_cost') or {}
    if tc.get('source_status')!='captured': n_skip+=1; continue
    bid=tc.get('bid'); ask=tc.get('ask'); sp=tc.get('spread_price')
    if not bid or not ask or sp is None: n_skip+=1; continue
    mid=(bid+ask)/2.0
    if mid<=0: n_skip+=1; continue
    sym=p.get('broker_symbol') or p.get('symbol')
    real[sym].append(sp/mid*1e4); n_cap+=1
    realbroker[sym].add(((p.get('profile') or {}).get('broker')))
# --- FROZEN: January pool, spread in price units = spread_r * risk_distance
froz=defaultdict(list); frozr=defaultdict(list); n_pool=0
for l in gzip.open(f'{D}/w0_WORKING_SET.jsonl.gz','rt'):
    r=json.loads(l)
    sr=r.get('spread_r'); rd=r.get('risk_distance'); ep=r.get('entry_price'); sym=r.get('symbol')
    if sr is None or not rd or not ep: continue
    froz[sym].append(sr*rd/ep*1e4); frozr[sym].append(sr); n_pool+=1
def s(v):
    v=sorted(v); n=len(v)
    return {'n':n,'mean':round(st.mean(v),4),'median':round(v[n//2],4),'p10':round(v[max(0,int(.10*n))],4),'p90':round(v[min(n-1,int(.90*n))],4)}
# --- symbol alias map: pool surface -> broker symbol at each firm
ALIAS={'US500.cash':['US500.cash','SPX500'],'US30.cash':['US30.cash','US30'],'US100.cash':['US100.cash','NDX100'],
 'GER40.cash':['GER40.cash','GER30'],'UK100.cash':['UK100.cash','UK100'],'JP225.cash':['JP225.cash','JP225'],
 'SPX500':['SPX500','US500.cash'],'NAS100':['US100.cash','NDX100'],'AUS200.cash':['AUS200.cash']}
res={'method':'spread expressed in basis points of mid price so the two populations are unit-matched. REAL = captured broker bid/ask at live decision instants. FROZEN = January pool spread_r * risk_distance / entry_price.',
     'n_real_captures':n_cap,'n_real_skipped':n_skip,'n_pool_rows':n_pool}
res['real_by_symbol']={k:s(v) for k,v in sorted(real.items(), key=lambda kv:-len(kv[1]))}
res['frozen_by_symbol_bps']={k:s(v) for k,v in sorted(froz.items(), key=lambda kv:-len(kv[1]))}
res['frozen_spread_r_by_symbol']={k:s(v) for k,v in sorted(frozr.items(), key=lambda kv:-len(kv[1]))}
# --- overlap ratio
ov={}
for psym,fv in froz.items():
    cands=ALIAS.get(psym,[psym])
    hit=None
    for c in cands:
        if c in real and len(real[c])>=3: hit=c; break
    if not hit: continue
    fm=st.median(fv); rm=st.median(real[hit])
    ov[psym]={'broker_symbol':hit,'n_pool':len(fv),'n_real':len(real[hit]),
              'frozen_bps_median':round(fm,4),'real_bps_median':round(rm,4),
              'ratio_frozen_over_real':round(fm/rm,3) if rm else None,
              'frozen_spread_r_median':round(st.median(frozr[psym]),5)}
res['overlap_ratio']=dict(sorted(ov.items(), key=lambda kv:-kv[1]['ratio_frozen_over_real']))
rs=[v['ratio_frozen_over_real'] for v in ov.values() if v['ratio_frozen_over_real']]
res['overlap_summary']={'n_symbols':len(rs),'median_ratio':round(st.median(rs),3),'mean_ratio':round(st.mean(rs),3),
                        'min':round(min(rs),3),'max':round(max(rs),3),
                        'pool_rows_covered':sum(v['n_pool'] for v in ov.values()),
                        'pool_rows_covered_frac':round(sum(v['n_pool'] for v in ov.values())/n_pool,4)}
json.dump(res,open(OUT,'w'),indent=1)
print('real captures',n_cap,'skipped',n_skip,'pool rows',n_pool)
print('OVERLAP SUMMARY',json.dumps(res['overlap_summary']))
print(f"{'poolsym':<14}{'brk':<12}{'nP':>6}{'nR':>5}{'frozBps':>10}{'realBps':>9}{'ratio':>8}{'frozSprR':>10}")
for k,v in res['overlap_ratio'].items():
    print(f"{k:<14}{v['broker_symbol']:<12}{v['n_pool']:>6}{v['n_real']:>5}{v['frozen_bps_median']:>10}{v['real_bps_median']:>9}{v['ratio_frozen_over_real']:>8}{v['frozen_spread_r_median']:>10}")
