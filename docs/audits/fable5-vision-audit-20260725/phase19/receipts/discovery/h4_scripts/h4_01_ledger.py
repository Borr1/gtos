import json, collections, datetime as dt
SRC='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl'
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
rows=[json.loads(l) for l in open(SRC)]
stages=collections.Counter(r.get('stage') for r in rows)
print('STAGES',stages)
L=[]
for r in rows:
    if r.get('stage')!='entry_fill_reconciled': continue
    oso=r.get('order_send_observation') or {}; req=oso.get('request') or {}; resu=oso.get('result') or {}
    dcr=r.get('deal_cost_reconciliation') or {}; pcm=r.get('pretrade_cost_model') or {}
    ident=r.get('identity') or {}
    spec=(pcm.get('symbol_spec') or {}).get('fields') or {}
    tick=pcm.get('tick_cost') or {}
    prof=(pcm.get('profile') or {})
    L.append(dict(
      cid=ident.get('candidate_id'), sym=ident.get('symbol'), bsym=ident.get('broker_symbol') or req.get('symbol'),
      t=ident.get('decision_time_utc'), broker=prof.get('broker'), ns=prof.get('runtime_profile_namespace'),
      side=('LONG' if req.get('type')==0 else 'SHORT' if req.get('type')==1 else None),
      vol=req.get('volume'), dev=req.get('deviation'), req=req.get('price'), sl=req.get('sl'), tp=req.get('tp'),
      fill=dcr.get('broker_entry_price'), comm=dcr.get('commission'), swap=dcr.get('swap'),
      deal=dcr.get('deal_ticket'), retcode=resu.get('retcode'), res_vol=resu.get('volume'), res_px=resu.get('price'),
      send=oso.get('order_send_time_utc'), res=oso.get('order_result_time_utc'),
      bfill_t=dcr.get('broker_fill_time_utc'),
      m_spread_px=pcm.get('spread_price'), m_spread_r=pcm.get('spread_r'), m_slip_r=pcm.get('expected_slippage_r'),
      m_total_r=pcm.get('total_cost_r'), m_sl_dist=pcm.get('sl_distance'), m_entry=pcm.get('entry_price'),
      ask=tick.get('ask'), bid=tick.get('bid'), tick_t=tick.get('time_utc'),
      csize=spec.get('trade_contract_size'), tickval=spec.get('trade_tick_value'), ticksize=spec.get('trade_tick_size'),
      point=spec.get('point'), swap_long=spec.get('swap_long'), swap_short=spec.get('swap_short'),
      swap_mode=spec.get('swap_mode'), roll3=spec.get('swap_rollover3days'),
      m_swap_costr=(pcm.get('swap_cost') or {}).get('cost_r'),
    ))
print('entry_fill_reconciled', len(L))
print('with fill&req', sum(1 for x in L if x['fill'] and x['req']))
print('brokers', collections.Counter(x['broker'] for x in L))
print('syms', len(set(x['bsym'] for x in L)))
print('date range', min(x['t'] for x in L), max(x['t'] for x in L))
print('csize present', sum(1 for x in L if x['csize']))
print('ask/bid present', sum(1 for x in L if x['ask'] and x['bid']))
json.dump(L, open(D+'/h4_FILL_LEDGER_RAW.json','w'), indent=0)
