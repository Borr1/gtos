import json, statistics as st
from collections import Counter, defaultdict
SRC='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
rows=[json.loads(l) for l in open(SRC)]
recs=[]
for r in rows:
    if r.get('stage')!='entry_fill_reconciled': continue
    oso=r.get('order_send_observation') or {}
    req=oso.get('request') or {}; resu=oso.get('result') or {}
    dcr=r.get('deal_cost_reconciliation') or {}
    ident=r.get('identity') or {}
    fill=dcr.get('broker_entry_price'); reqp=req.get('price'); sl=req.get('sl')
    rec=dict(candidate_id=ident.get('candidate_id'), symbol=ident.get('broker_symbol') or req.get('symbol'),
             decision_time_utc=ident.get('decision_time_utc'),
             action=req.get('action'), otype=req.get('type'), type_filling=req.get('type_filling'),
             type_time=req.get('type_time'), deviation=req.get('deviation'), volume=req.get('volume'),
             req_price=reqp, req_sl=sl, req_tp=req.get('tp'),
             fill_price=fill, commission=dcr.get('commission'), swap=dcr.get('swap'),
             deal_ticket=dcr.get('deal_ticket'), order_ticket=resu.get('order_ticket'),
             retcode=resu.get('retcode'), success=resu.get('success'),
             res_volume=resu.get('volume'), res_price=resu.get('price'),
             send_utc=oso.get('order_send_time_utc'), result_utc=oso.get('order_result_time_utc'),
             broker_fill_time_utc=dcr.get('broker_fill_time_utc'),
             lookup_status=dcr.get('account_history_lookup_status'))
    # pretrade cost model captured spread
    pcm=r.get('pretrade_cost_model') or {}
    for k in ('decision_spread','spread','spread_value','decision_spread_value','expected_slippage_r','expected_cost_r','spread_r','total_cost_r'):
        if k in pcm: rec['pcm_'+k]=pcm[k]
    rec['pcm_keys']=sorted(pcm.keys())
    recs.append(rec)
print('entry_fill_reconciled rows:', len(recs))
print('with fill+req price:', sum(1 for x in recs if x['fill_price'] and x['req_price']))
print('actions', Counter(x['action'] for x in recs))
print('otypes', Counter(x['otype'] for x in recs))
print('filling', Counter(x['type_filling'] for x in recs))
print('retcodes', Counter(x['retcode'] for x in recs))
print('res_price nonzero', sum(1 for x in recs if x['res_price']))
print('lookup', Counter(x['lookup_status'] for x in recs))
print('PCM KEYS SAMPLE', recs[0]['pcm_keys'][:40])
json.dump(recs, open(OUTD+'/L10_ENTRY_FILLS_RAW_V1.json','w'), indent=0)
