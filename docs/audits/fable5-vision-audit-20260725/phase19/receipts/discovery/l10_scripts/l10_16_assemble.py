import json, os
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
def L(n):
    p=os.path.join(D,n)
    return json.load(open(p)) if os.path.isfile(p) else None
out={}
out['lane']='l10-broker-truth'
out['scope']='EXECUTION MECHANICS ONLY. No live-forward P&L computed, tabulated or reported.'
census=L('L10_MT5_CENSUS_V1.json')
out['evidence_inventory']=dict(
  primary_broker_records={
    'ftmo_history_orders_get.jsonl':dict(n=census['ftmo']['n_orders'],window=census['ftmo']['orders_window_utc']),
    'ftmo_history_deals_get.jsonl':dict(n=census['ftmo']['n_deals'],window=census['ftmo']['deals_window_utc']),
    'redacted_account_history_orders_get.jsonl':dict(n=census['redacted_account']['n_orders'],window=census['redacted_account']['orders_window_utc']),
    'redacted_account_history_deals_get.jsonl':dict(n=census['redacted_account']['n_deals'],window=census['redacted_account']['deals_window_utc'])},
  root='/Users/borr/GTOSActive/vps-export-20260725/extracted/',
  runtime_capture=dict(path='05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl', rows=594,
     stages=dict(sltp_modify_result=271, entry_fill_reconciled=149, pre_send=147, sltp_modify_deferred=15, close_position_result=10, sltp_modify_blocked=2),
     reconciled_fills_with_request_and_broker_fill_price=140),
  other_execution_logs={'slippage.jsonl':192,'slippage_runtime.jsonl':165,'nofill_forward_source_capture.jsonl':446,
     'execution_manager_v4_decisions.jsonl_bytes':6090235,'broker_actual_r_audit.jsonl':285,'time_in_trade.jsonl':51},
  POST_ARMING_COVERAGE='ABSENT. The newest broker export on this machine is 2026-07-25/26 (vps-export-20260725, mt5 pull stamped 2026-07-26T06:28Z). FTMO armed 2026-07-29 12:55Z and redacted_account 2026-07-30 05:18Z, so ZERO post-arming live-forward broker records exist locally. Every number in this receipt is from the pre-arming live window (redacted_account 2026-04-27..2026-07-02, FTMO 2026-06-02..2026-07-03). Searched: /Users/borr/GTOSActive (all trees), ~/Documents, ~/.gtos, /Volumes.',
  newest_vps_pull='vps-bars-20260727 (bars), vps-ticks-20260726 (ticks 2026-06-18..07-24), vps-export-20260725 (full host export)')
out['F1_order_type_census']=dict(
  claim='The live engine has never placed a strategy limit order. 631 of 633 orders are market (TRADE_ACTION_DEAL); the only 2 pending orders in either account are preflight test artifacts.',
  ftmo=dict(orders=267, market=266, close_by=1, pending=0, types=census['ftmo']['order_type_counts'], states=census['ftmo']['order_state_counts'],
            filling=census['ftmo']['type_filling_counts'], time=census['ftmo']['type_time_counts']),
  redacted_account=dict(orders=366, market=364, pending=2, types=census['redacted_account']['order_type_counts'], states=census['redacted_account']['order_state_counts'],
            filling=census['redacted_account']['type_filling_counts'], time=census['redacted_account']['type_time_counts']),
  the_two_pending=[dict(ticket=234901868,symbol='XAUUSD',type='BUY_LIMIT',state='CANCELED',magic=99999999,comment='preflight_test',utc='2026-05-01T02:49:30Z',sit_seconds=0),
                   dict(ticket=241520122,symbol='XAUUSD',type='BUY_LIMIT',state='CANCELED',magic=99999999,comment='preflight_test',utc='2026-05-28T15:57:45Z',sit_seconds=0)],
  strategy_magic=20260401,
  source_proof='src/components/execution.py:3534 hardcodes {"action": 1,  # TRADE_ACTION_DEAL} on the only entry order_send. rg over src/ + run_book.py finds TRADE_ACTION_PENDING only at src/mt5/mt5_interface.py:63 (constant) and src/safety/activation_token.py:70,625 (classifier). There is no code path in the live engine that can create a pending order.',
  lifecycle_corroboration=dict(entry_fill_reconciled_rows=149, action_1_TRADE_ACTION_DEAL=149, type_filling_IOC=149, retcode_10009=149))
fr=L('L10_FILLRATE_V1.json')
out['F2_fill_rate']=dict(
  claim='Real market-order acceptance is 0.99524 pooled, not the modelled 0.92 / 0.805.',
  ftmo=dict(n_market=266, filled=266, rate=1.0, rejected=0),
  redacted_account=dict(n_market=364, filled=361, rate=0.99176, rejected=3, strategy_rate=fr['redacted_account']['strategy_fill_rate']),
  pooled=dict(n=630, filled=627, rate=round(627/630,5)),
  rejections=fr['redacted_account']['rejected_detail'],
  per_session_utc=dict(ftmo=fr['ftmo']['fill_rate_per_session_utc'], redacted_account=fr['redacted_account']['fill_rate_per_session_utc']),
  per_symbol=dict(ftmo=fr['ftmo']['fill_rate_per_symbol'], redacted_account=fr['redacted_account']['fill_rate_per_symbol']),
  limit_orders=dict(n=2, filled=0, rate=0.0, note='both are preflight_test artifacts, canceled in the same second'),
  modelled_values=dict(execution_fill_probability_marketable_branch=0.92, pool_mean=0.805058, pool_min=0.0401331,
     source='src/components/poi_execution_lifecycle.py:174-176 (0.92 branch), :178-181 (distance-scaled else-branch)'),
  empirical_replacement=dict(market_order_acceptance_ftmo=1.0, market_order_acceptance_redacted_account=0.99176,
     market_order_acceptance_pooled=0.99524,
     limit_order_fill_probability='UNMEASURED - no strategy limit order has ever been placed at either broker'))
sb=L('L10_SLIP_BREAKDOWN_V1.json'); ss=L('L10_SPEC_SPREAD_V1.json')
out['F3_entry_slippage']=dict(
  claim='Real entry slippage on 140 reconciled market fills is +0.013232 R mean / +0.000398 R median against a flat modelled allowance of 0.02 R. The flat constant is wrong in BOTH directions: it overcharges indices 16.9x and undercharges FX majors up to 2.1x.',
  n=140, mean_r=0.013232, median_r=0.000398, p25_r=-0.0, p75_r=0.017998, p90_r=0.050233, min_r=-0.061404, max_r=0.171569,
  zero_slippage_fills=37, adverse=78, favourable=25,
  modelled_flat=0.02, modelled_source='config/agent_config.yaml:740 selected_cell_default_expected_slippage_r; expected_slippage_source=config.selected_cell_default_expected_slippage_r on 140/140',
  frac_fills_model_overcharges=0.7714, n_model_over=108, n_model_under=32,
  by_class={c:dict(n=v['n'],mean_r=v['slip_r']['mean'],median_r=v['slip_r']['median'],zero=v['zero']) for c,v in sb['per_class'].items()},
  empirical_replacement_r=dict(fx=0.030625, crypto=0.004424, metals=0.002782, index=0.001184, pooled=0.013232),
  by_side=sb['per_side'], by_symbol={k:dict(n=v['n'],mean=v['slip_r']['mean'],median=v['slip_r']['median'],zero=v['zero'],adverse=v['adverse'],fav=v['fav']) for k,v in sb['per_symbol'].items()},
  request_side_convention=ss['summary']['request_side_convention'],
  displacement_note='requested price EQUALS the strategy intended entry_price on 140/140 fills (frac 1.0). The W7 book names no resting level; its entry IS the market. Total displacement between intent and fill therefore equals the slippage above.')
out['F4_latency']=dict(
  claim='FTMO fills in a tight 130-193 ms band with zero outliers. redacted_account entry latency is 3.4x slower (median 488 ms) with a 14.0 s worst entry and a 148.1 s worst close.',
  ftmo=dict(all=census['ftmo']['market_order_latency_ms'], entry=fr['ftmo']['latency_open_ms'], close=fr['ftmo']['latency_close_ms']),
  redacted_account=dict(all=census['redacted_account']['market_order_latency_ms'], entry=fr['redacted_account']['latency_open_ms'], close=fr['redacted_account']['latency_close_ms']),
  buckets=dict(ftmo=dict(lt50=0,ms50_250=266,ms250_1000=0,ge1000=0,ge10000=0),
               redacted_account=dict(lt50=121,ms50_250=5,ms250_1000=197,ge1000=36,ge10000=5)),
  bimodality_explained='redacted_account CLOSE orders execute server-side near-instantly (median 7 ms, 62.05% under 50 ms) while OPEN orders take median 488 ms. FTMO is uniform (~145 ms) for both. Not a symbol or era effect: fast and slow cohorts share the same symbols, dates, filling mode and magic.',
  worst_entries_redacted_account_ms=[12617,14019],
  worst_close_redacted_account_ms=148112)
json.dump(out,open(D+'/L10_PART1.json','w'),indent=1)
print('part1 keys',list(out.keys()))
print('ok')
