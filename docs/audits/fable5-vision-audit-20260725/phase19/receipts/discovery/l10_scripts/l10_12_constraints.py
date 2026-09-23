import json, datetime as dt
from collections import Counter, defaultdict
SL='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs'
API='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
RET={10004:'REQUOTE',10006:'REJECT',10007:'CANCEL',10008:'PLACED',10009:'DONE',10010:'DONE_PARTIAL',10011:'ERROR',10012:'TIMEOUT',10013:'INVALID',10014:'INVALID_VOLUME',10015:'INVALID_PRICE',10016:'INVALID_STOPS',10017:'TRADE_DISABLED',10018:'MARKET_CLOSED',10019:'NO_MONEY',10020:'PRICE_CHANGED',10021:'PRICE_OFF',10022:'INVALID_EXPIRATION',10023:'ORDER_CHANGED',10024:'TOO_MANY_REQUESTS',10025:'NO_CHANGES',10026:'SERVER_DISABLES_AT',10027:'CLIENT_DISABLES_AT',10028:'LOCKED',10029:'FROZEN',10030:'INVALID_FILL',10031:'CONNECTION',10032:'ONLY_REAL',10033:'LIMIT_ORDERS',10034:'LIMIT_VOLUME'}
rows=[json.loads(l) for l in open(f'{SL}/broker_order_lifecycle_capture_v4.jsonl')]
out={}
# retcodes by stage
rc=defaultdict(Counter)
for r in rows:
    st=r.get('stage'); res=r.get('result') if isinstance(r.get('result'),dict) else ((r.get('order_send_observation') or {}).get('result') or {})
    if res and res.get('retcode') is not None:
        rc[st][RET.get(res['retcode'],res['retcode'])]+=1
out['retcode_by_stage']={k:dict(v) for k,v in rc.items()}
# comment census
cm=Counter()
for r in rows:
    res=r.get('result') if isinstance(r.get('result'),dict) else ((r.get('order_send_observation') or {}).get('result') or {})
    if res and res.get('comment'): cm[res['comment']]+=1
out['result_comments']=dict(cm.most_common(15))
# broker symbol constraints from the traded-spec exports (both accounts)
spec={}
for a in ['ftmo','redacted_account']:
    d=json.load(open(f'{API}/{a}_symbol_specs_traded.json'))
    for s,v in d.items():
        f=v.get('fields',v)
        spec[f'{a}:{s}']={k:f.get(k) for k in ('point','trade_stops_level','trade_freeze_level','volume_min','volume_step','volume_max','trade_contract_size','trade_tick_size','trade_tick_value','swap_mode','swap_long','swap_short','swap_rollover3days','spread','spread_float','filling_mode','trade_mode','digits')}
out['symbol_constraints']=spec
nz=[(k,v['trade_stops_level']) for k,v in spec.items() if v.get('trade_stops_level')]
out['nonzero_stops_level']=dict(nz)
out['n_symbols_with_stops_level']=len(nz); out['n_symbols']=len(spec)
fz=[(k,v['trade_freeze_level']) for k,v in spec.items() if v.get('trade_freeze_level')]
out['nonzero_freeze_level']=dict(fz)
# swap modes
out['swap_modes']=dict(Counter(v.get('swap_mode') for v in spec.values()))
out['swap_rollover3days']=dict(Counter(v.get('swap_rollover3days') for v in spec.values()))
# MARKET_CLOSED timing
mc=[]
for r in rows:
    res=r.get('result') if isinstance(r.get('result'),dict) else ((r.get('order_send_observation') or {}).get('result') or {})
    if res and res.get('retcode')==10018:
        mc.append(dict(t=r.get('generated_at_utc'), sym=r.get('symbol') or (r.get('identity') or {}).get('broker_symbol'), stage=r.get('stage')))
out['market_closed_events']=mc
json.dump(out,open(OUTD+'/L10_CONSTRAINTS_V1.json','w'),indent=1)
print('RETCODE BY STAGE:'); 
for k,v in out['retcode_by_stage'].items(): print('  ',k,v)
print('COMMENTS:',out['result_comments'])
print('symbols',out['n_symbols'],'with nonzero stops_level',out['n_symbols_with_stops_level'],out['nonzero_stops_level'])
print('freeze',out['nonzero_freeze_level'])
print('swap_modes',out['swap_modes'],'rollover3days',out['swap_rollover3days'])
print('MARKET_CLOSED n',len(mc)); 
for m in mc[:8]: print('   ',m)
