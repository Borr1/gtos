#!/usr/bin/env python3
"""Session FA / wave-19 forensic — January executed-trade walker.

Streams the CJ_RECLOCKED_S0R0_V7 TRADE / ORDER / ORDERED_PATH_ORACLE ledgers
(read-only, in place, line by line) and projects the per-trade table.

Outputs: TRADES_JAN_TABLE.json in the same directory as this script.
"""
import json, os, datetime

ROUTE = ('/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/'
         'research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/'
         'attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/')
OUT = os.path.dirname(os.path.abspath(__file__))
LANE = ('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/'
        'fable5-vision-audit-20260725/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl')

def parse_ts(s):
    if not s: return None
    return datetime.datetime.fromisoformat(s)

def minutes(a, b):
    ta, tb = parse_ts(a), parse_ts(b)
    if ta is None or tb is None: return None
    return round((tb - ta).total_seconds() / 60.0, 4)

TRADE_FIELDS = [
    'candidate_id','origin_family','framework','setup_family','symbol','direction','side',
    'session_bucket','utc_hour_bucket','kill_zone','route_session',
    'decision_time_utc','entry_time_utc','exit_time_utc',
    'entry_price','stop_loss','take_profit_1','close_mark_price','close_mark_quote_side',
    'close_reason','gross_r','cost_r','spread_r','commission_r','swap_cost_r','expected_slippage_r',
    'net_r','final_r','final_r_authority','approved_risk_pct','risk_cash',
    'candidate_probability','candidate_ev_r','expected_net_r','candidate_confidence',
    'headline_result_exclusion_reason','fill_realism_class','fill_realism_executable',
    'mfe_r','mae_r','mfe_time_utc','mae_time_utc',
    'target_first_touch_utc','stop_first_touch_utc','entry_first_touch_utc',
    'policy_target_r','raw_target_r',
    'limit_first_full_horizon_gross_r','limit_first_full_horizon_close_reason','limit_first_full_horizon_target_r',
    'guarded_market_fallback_extra_cost_r','fallback_execution_surcharge_r',
    'candidate_lifecycle_action','effective_order_type','order_execution_path',
    'exit_composition_selected_policy_gross_r','exit_composition_raw_fixed_target_gross_r',
    'exit_composition_terminal_gross_r','path_source_timeframe','path_row_count',
    'ordered_tick_truth_oracle_satisfied','total_cost_components',
    'dynamic_geometry_policy','risk_finalizer_reason','risk_finalizer_rank',
]

trades = []
with open(ROUTE + 'CJ_RECLOCKED_S0R0_V7_TRADE_LEDGER.jsonl') as f:
    for line in f:
        r = json.loads(line)
        t = {k: r.get(k) for k in TRADE_FIELDS}
        t['holding_minutes'] = minutes(t['entry_time_utc'], t['exit_time_utc'])
        # first-touch within tick horizon (from the trade's own ordered-tick path replay)
        tt, st = t['target_first_touch_utc'], t['stop_first_touch_utc']
        if tt and st:
            t['first_touch_within_horizon'] = 'target' if tt < st else 'stop'
        elif tt:
            t['first_touch_within_horizon'] = 'target'
        elif st:
            t['first_touch_within_horizon'] = 'stop'
        else:
            t['first_touch_within_horizon'] = 'neither'
        mfe = t['mfe_r']; cost = t['cost_r']
        t['best_available_exit_r_net'] = (round(mfe - cost, 8)
                                          if isinstance(mfe, (int, float)) and isinstance(cost, (int, float))
                                          else None)
        t['R_if_held_to_horizon_gross'] = t['limit_first_full_horizon_gross_r']
        t['decision_day'] = (t['decision_time_utc'] or '')[:10]
        trades.append(t)

assert len(trades) == 57, len(trades)

# ---- ORACLE ledger: join mfe/mae as independent cross-check --------------
oracle = {}
with open(ROUTE + 'CJ_RECLOCKED_S0R0_V7_ORDERED_PATH_ORACLE_LEDGER.jsonl') as f:
    for line in f:
        r = json.loads(line)
        oracle[(r.get('candidate_id'), r.get('asof_utc'))] = {
            'mfe_r': r.get('mfe_r'), 'mae_r': r.get('mae_r'),
            'path_row_count': r.get('path_row_count'),
            'path_source_timeframe': r.get('path_source_timeframe'),
            'adverse_before_profit_flag': r.get('adverse_before_profit_flag'),
            'close_mark_price': r.get('close_mark_price'),
        }
oracle_matched = 0
for t in trades:
    o = oracle.get((t['candidate_id'], t['decision_time_utc']))
    if o:
        oracle_matched += 1
        t['oracle_mfe_r'] = o['mfe_r']; t['oracle_mae_r'] = o['mae_r']
        t['oracle_adverse_before_profit'] = o['adverse_before_profit_flag']
        t['oracle_mfe_matches_trade'] = (o['mfe_r'] == t['mfe_r'])
    else:
        t['oracle_mfe_r'] = None; t['oracle_mae_r'] = None
        t['oracle_adverse_before_profit'] = None; t['oracle_mfe_matches_trade'] = None
trade_keys = {(t['candidate_id'], t['decision_time_utc']) for t in trades}
oracle_only = [k for k in oracle if k not in trade_keys]

# ---- ORDER ledger: lifecycle accounting ----------------------------------
import collections
order_status = collections.Counter()
terminal_status = collections.Counter()
orders_by_cand = collections.defaultdict(list)
n_orders = 0
with open(ROUTE + 'CJ_RECLOCKED_S0R0_V7_ORDER_LEDGER.jsonl') as f:
    for line in f:
        r = json.loads(line)
        n_orders += 1
        order_status[r.get('order_status')] += 1
        terminal_status[r.get('terminal_resolution_status')] += 1
        orders_by_cand[(r.get('candidate_id'), r.get('candidate_instance_time_utc'))].append(
            {'order_status': r.get('order_status'),
             'terminal_resolution_status': r.get('terminal_resolution_status'),
             'symbol': r.get('symbol')})
# orders per executed trade / orders with no trade
cands_with_trade = trade_keys
orders_for_trades = sum(len(v) for k, v in orders_by_cand.items() if k in cands_with_trade)
orders_no_trade = sum(len(v) for k, v in orders_by_cand.items() if k not in cands_with_trade)
no_trade_status = collections.Counter()
for k, v in orders_by_cand.items():
    if k not in cands_with_trade:
        for o in v: no_trade_status[(o['order_status'], o['terminal_resolution_status'])] += 1
with_trade_status = collections.Counter()
for k, v in orders_by_cand.items():
    if k in cands_with_trade:
        for o in v: with_trade_status[(o['order_status'], o['terminal_resolution_status'])] += 1

# ---- lane trade table cross-check -----------------------------------------
lane_rows = []
with open(LANE) as f:
    meta = json.loads(f.readline())
    for line in f:
        lane_rows.append(json.loads(line))
lane_by_key = {(r['candidate_id'], r['decision_time_utc']): r for r in lane_rows}
lane_mismatch = []
for t in trades:
    lr = lane_by_key.get((t['candidate_id'], t['decision_time_utc']))
    if lr is None:
        lane_mismatch.append({'key': [t['candidate_id'], t['decision_time_utc']], 'why': 'missing_in_lane'})
        continue
    for fld in ('net_r', 'final_r', 'cost_r', 'close_reason', 'risk_cash', 'approved_risk_pct'):
        if lr.get(fld) != t.get(fld):
            lane_mismatch.append({'key': [t['candidate_id'], t['decision_time_utc']],
                                  'field': fld, 'lane': lr.get(fld), 'trade': t.get(fld)})

result = {
    'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_trade_ledger': ROUTE + 'CJ_RECLOCKED_S0R0_V7_TRADE_LEDGER.jsonl',
    'n_trades': len(trades),
    'oracle_rows': len(oracle),
    'oracle_matched_to_trades': oracle_matched,
    'oracle_rows_without_trade': oracle_only,
    'order_rows': n_orders,
    'order_status_counts': dict(order_status),
    'terminal_resolution_counts': dict(terminal_status),
    'orders_attached_to_executed_trades': orders_for_trades,
    'orders_without_executed_trade': orders_no_trade,
    'orders_without_trade_status_breakdown': {f'{a}|{b}': c for (a, b), c in no_trade_status.items()},
    'orders_with_trade_status_breakdown': {f'{a}|{b}': c for (a, b), c in with_trade_status.items()},
    'lane_table_rows': len(lane_rows),
    'lane_identity_mismatches': lane_mismatch,
    'trades': trades,
}
with open(os.path.join(OUT, 'TRADES_JAN_TABLE.json'), 'w') as f:
    json.dump(result, f, indent=1, default=str)
print('trades', len(trades), '| oracle matched', oracle_matched, '| oracle-only', len(oracle_only))
print('order_status', dict(order_status))
print('terminal', dict(terminal_status))
print('orders for trades', orders_for_trades, '| orders no trade', orders_no_trade)
print('lane mismatches', len(lane_mismatch))
print('sum net_r', round(sum(t['net_r'] for t in trades if isinstance(t['net_r'], (int, float))), 8))
print('sum final_r', round(sum(t['final_r'] for t in trades if isinstance(t['final_r'], (int, float))), 8))
print('sum gross_r', round(sum(t['gross_r'] for t in trades if isinstance(t['gross_r'], (int, float))), 8))
print('sum cost_r', round(sum(t['cost_r'] for t in trades if isinstance(t['cost_r'], (int, float))), 8))
