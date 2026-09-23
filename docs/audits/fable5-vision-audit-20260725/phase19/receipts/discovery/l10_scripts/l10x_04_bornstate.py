import json, statistics as st
from collections import Counter, defaultdict
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted'
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
OUT=f'{D}/L10X_LIVE_BORNSTATE_V1.json'
rows=[json.loads(l) for l in open(f'{BASE}/05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl')]
recs=[]
for r in rows:
    p=r.get('pretrade_cost_model')
    if not isinstance(p,dict): continue
    tc=p.get('tick_cost') or {}
    if tc.get('source_status')!='captured': continue
    bid=tc.get('bid'); ask=tc.get('ask'); ep=p.get('entry_price'); sl=p.get('stop_loss')
    side=(p.get('side') or '').upper(); sld=p.get('sl_distance')
    if None in (bid,ask,ep,sl) or not sld: continue
    long_= side in ('LONG','BUY') or (sl<ep)
    ref = ask if long_ else bid            # the price a market order pays
    # displacement of the INTENDED entry from the live executable price, in R (sl_distance) units
    disp = (ref-ep)/sld if long_ else (ep-ref)/sld   # >0 => market is already worse than intended entry
    # is the stop already breached at the live quote?
    breached = (ref<=sl) if long_ else (ref>=sl)
    # marketability of the intended entry as a LIMIT order
    if long_: mk = 'at_or_through_market' if ep>=ask else 'resting_below'
    else:     mk = 'at_or_through_market' if ep<=bid else 'resting_above'
    recs.append({'sym':p.get('broker_symbol'),'stage':r.get('stage'),'side':'LONG' if long_ else 'SHORT',
                 'disp_r':disp,'breached':breached,'mk':mk,'ep':ep,'ref':ref,'sl':sl,'sld':sld,
                 'ep_eq_ref':abs(ep-ref)<1e-12,
                 'eq_tol_1e6': abs(ep-ref)/max(abs(ref),1e-12) < 1e-6})
def s(v):
    v=sorted(v); n=len(v)
    if not n: return None
    return {'n':n,'mean':round(st.mean(v),6),'median':round(v[n//2],6),'p05':round(v[max(0,int(.05*n))],6),
            'p95':round(v[min(n-1,int(.95*n))],6),'min':round(v[0],6),'max':round(v[-1],6)}
res={'n':len(recs),
 'ENTRY_PRICE_IS_THE_LIVE_EXECUTABLE_QUOTE':{
    'n_exact_equal':sum(1 for r in recs if r['ep_eq_ref']),
    'frac_exact_equal':round(sum(1 for r in recs if r['ep_eq_ref'])/len(recs),4),
    'n_equal_within_1e-6_rel':sum(1 for r in recs if r['eq_tol_1e6']),
    'frac_within_1e-6_rel':round(sum(1 for r in recs if r['eq_tol_1e6'])/len(recs),4)},
 'live_born_state':dict(Counter(r['mk'] for r in recs)),
 'live_born_past_stop':{'n':sum(1 for r in recs if r['breached']),
                        'frac':round(sum(1 for r in recs if r['breached'])/len(recs),6)},
 'displacement_r_market_minus_intended':s([r['disp_r'] for r in recs]),
 'by_stage':{k:{'n':v} for k,v in Counter(r['stage'] for r in recs).items()},
 'by_symbol_disp':{k:s([r['disp_r'] for r in recs if r['sym']==k]) for k,_ in Counter(r['sym'] for r in recs).most_common(12)},
 'nonzero_displacement_rows':[{k:round(v,8) if isinstance(v,float) else v for k,v in r.items()} for r in recs if not r['eq_tol_1e6']][:40],
 'source_proof':'src/components/execution.py:3534 action=1 TRADE_ACTION_DEAL with price=entry_price; TRADE_ACTION_PENDING=5 is defined at src/mt5/mt5_interface.py:63 and referenced ONLY by src/safety/activation_token.py:625 (a classifier) - no request in src/ ever sets action=5',
 'january_pool_comparison':{'born_at_limit_frac':0.5395,'born_resting_frac':0.2876,'born_marketable_frac':0.0458,'born_past_stop_frac':0.1272,
                            'source':'W0CAP2_NOLOOKAHEAD_FULL_V1.json BORN_CENSUS'}}
json.dump(res,open(OUT,'w'),indent=1)
o={k:v for k,v in res.items() if k not in ('nonzero_displacement_rows','by_symbol_disp')}
print(json.dumps(o,indent=1)[:1700])
print('n nonzero-disp rows:',len(res['nonzero_displacement_rows']))
for r in res['nonzero_displacement_rows'][:8]: print(' ',r['sym'],r['side'],r['stage'],'disp_r',round(r['disp_r'],6),'ep',r['ep'],'ref',r['ref'])
