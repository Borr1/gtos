#!/usr/bin/env python3
"""Session FA / wave-19 forensic — per-trade loss attribution + aggregations.

Reads TRADES_JAN_TABLE.json (built by extract_trades_jan.py), the compact
January diagnostic pool (gz, streamed), and the arm SUMMARY for reconciliation.

Outputs: TRADES_JAN_ATTRIBUTION.json
"""
import json, gzip, os, collections

OUT = os.path.dirname(os.path.abspath(__file__))
POOL = ('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/'
        'fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz')
SUMMARY = ('/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/research/operations/'
           'final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/'
           'attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/CJ_RECLOCKED_S0R0_V7_SUMMARY.json')

d = json.load(open(os.path.join(OUT, 'TRADES_JAN_TABLE.json')))
trades = d['trades']

# ---------------- classification ----------------
# Precedence (documented in TRADES_JAN.md):
#  0 unscoreable            gross_r is None (terminal R never scoreable)
#  1 winner_target          net_r > 0 and close reason is a target
#  2 winner_other           net_r > 0 otherwise
#  3 cost_dominated         gross_r >= 0 but net_r < 0 (cost flipped the sign),
#                           or |gross_r| <= cost_r
#  4 exit_geometry          net_r < 0 and mfe_r >= +0.5 (the trade WAS right;
#                           the exit machinery gave it back)
#  5 direction_wrong        net_r < 0 and (stop-class close or mae_r <= -0.9)
#                           and mfe_r < 0.5
#  6 horizon_marked         net_r < 0, closed by path-end / time-stop mark
#  7 other_loss
STOP_REASONS = {'selected_policy_replay:stop_loss', 'stop_reached_before_target'}
TARGET_REASONS = {'selected_policy_replay:final_target', 'target_reached_before_stop'}
MARK_REASONS = {'selected_policy_replay:path_end_mark_to_market', 'time_stop_close_mark_from_m1'}

def classify(t):
    g, n, c = t['gross_r'], t['net_r'], t['cost_r']
    mfe = t['mfe_r'] if isinstance(t['mfe_r'], (int, float)) else None
    mae = t['mae_r'] if isinstance(t['mae_r'], (int, float)) else None
    cr = t['close_reason']
    if g is None or n is None:
        return 'unscoreable'
    if n > 0:
        return 'winner_target' if cr in TARGET_REASONS else 'winner_other'
    if g >= 0 or (c is not None and abs(g) <= c):
        return 'cost_dominated'
    if mfe is not None and mfe >= 0.5:
        return 'exit_geometry'
    if (cr in STOP_REASONS or (mae is not None and mae <= -0.9)) and (mfe is None or mfe < 0.5):
        return 'direction_wrong'
    if cr in MARK_REASONS:
        return 'horizon_marked'
    return 'other_loss'

for t in trades:
    t['loss_class'] = classify(t)

cls = collections.defaultdict(lambda: {'n': 0, 'net_r_sum': 0.0, 'gross_r_sum': 0.0, 'cost_r_sum': 0.0,
                                       'trades': []})
for t in trades:
    e = cls[t['loss_class']]
    e['n'] += 1
    if isinstance(t['net_r'], (int, float)):
        e['net_r_sum'] += t['net_r']; e['gross_r_sum'] += t['gross_r']
    if isinstance(t['cost_r'], (int, float)):
        e['cost_r_sum'] += t['cost_r']
    e['trades'].append(t['candidate_id'])
for e in cls.values():
    for k in ('net_r_sum', 'gross_r_sum', 'cost_r_sum'):
        e[k] = round(e[k], 6)

# ---------------- aggregations ----------------
def agg(key_fn, name):
    a = collections.defaultdict(lambda: {'n': 0, 'net_r_sum': 0.0, 'gross_r_sum': 0.0, 'cost_r_sum': 0.0,
                                         'winners': 0})
    for t in trades:
        k = key_fn(t)
        e = a[k]; e['n'] += 1
        if isinstance(t['net_r'], (int, float)):
            e['net_r_sum'] += t['net_r']; e['gross_r_sum'] += t['gross_r']
            if t['net_r'] > 0: e['winners'] += 1
        if isinstance(t['cost_r'], (int, float)): e['cost_r_sum'] += t['cost_r']
    return {str(k): {kk: (round(v, 6) if isinstance(v, float) else v) for kk, v in e.items()}
            for k, e in sorted(a.items(), key=lambda kv: kv[1]['net_r_sum'])}

aggs = {
    'by_origin_family': agg(lambda t: t['origin_family'], 'origin_family'),
    'by_framework': agg(lambda t: t['framework'], 'framework'),
    'by_direction': agg(lambda t: t['direction'], 'direction'),
    'by_symbol': agg(lambda t: t['symbol'], 'symbol'),
    'by_session': agg(lambda t: t['session_bucket'], 'session'),
    'by_close_reason': agg(lambda t: t['close_reason'], 'close_reason'),
    'by_utc_hour_bucket': agg(lambda t: t['utc_hour_bucket'], 'utc_hour'),
    'by_day': agg(lambda t: t['decision_day'], 'day'),
}

# breaker share of the executed book
breaker = [t for t in trades if 'breaker' in str(t['origin_family']).lower()
           or 'breaker' in str(t['framework']).lower()
           or 'breaker' in str(t['setup_family']).lower()]
breaker_stat = {'n': len(breaker),
                'net_r_sum': round(sum(t['net_r'] for t in breaker if isinstance(t['net_r'], (int, float))), 6),
                'candidate_ids': [t['candidate_id'] for t in breaker]}

# day-level clustering: same day+symbol multiples
day_sym = collections.Counter((t['decision_day'], t['symbol']) for t in trades)
clusters = {f'{d}|{s}': c for (d, s), c in day_sym.items() if c > 1}
day_counts = collections.Counter(t['decision_day'] for t in trades)

# ---------------- pool day-level (what a "negative day" means) -------------
pool_days = collections.defaultdict(lambda: {'rows': 0, 'net_sum': 0.0, 'pos': 0})
pool_rows = 0; pool_net = 0.0
with gzip.open(POOL, 'rt') as f:
    for line in f:
        r = json.loads(line)
        v = r.get('opportunity_net_proxy_r')
        day = (r.get('decision_time_utc') or '')[:10]
        pool_rows += 1
        if isinstance(v, (int, float)):
            pool_net += v
            e = pool_days[day]; e['rows'] += 1; e['net_sum'] += v
            if v > 0: e['pos'] += 1
pool_day_series = {day: {'rows': e['rows'], 'net_sum': round(e['net_sum'], 4), 'pos_rows': e['pos']}
                   for day, e in sorted(pool_days.items())}
neg_days = sum(1 for e in pool_days.values() if e['net_sum'] < 0)

# executed-trade day series
trade_day_series = {}
for day, c in sorted(day_counts.items()):
    net = sum(t['net_r'] for t in trades if t['decision_day'] == day and isinstance(t['net_r'], (int, float)))
    trade_day_series[day] = {'n_trades': c, 'net_r_sum': round(net, 6)}

# ---------------- anomalies ----------------
ids = collections.Counter(t['candidate_id'] for t in trades)
dup_ids = {k: v for k, v in ids.items() if v > 1}
cost_outliers = [{'candidate_id': t['candidate_id'], 'symbol': t['symbol'], 'cost_r': t['cost_r']}
                 for t in trades if isinstance(t['cost_r'], (int, float)) and t['cost_r'] > 1.0]
zero_hold = [{'candidate_id': t['candidate_id'], 'holding_minutes': t['holding_minutes']}
             for t in trades if t['holding_minutes'] is not None and t['holding_minutes'] <= 0]
excl = collections.Counter(t['headline_result_exclusion_reason'] for t in trades)
weird_close = collections.Counter(t['close_reason'] for t in trades
                                  if t['close_reason'] not in STOP_REASONS | TARGET_REASONS | MARK_REASONS
                                  and t['close_reason'] != 'selected_policy_replay:giveback_close')
# price sanity: entry between stop and target for the direction
price_sanity = []
for t in trades:
    ep, sl, tp = t['entry_price'], t['stop_loss'], t['take_profit_1']
    if None in (ep, sl, tp): continue
    if t['direction'] == 'LONG' and not (sl < ep < tp):
        price_sanity.append({'candidate_id': t['candidate_id'], 'dir': 'LONG', 'sl': sl, 'entry': ep, 'tp': tp})
    if t['direction'] == 'SHORT' and not (tp < ep < sl):
        price_sanity.append({'candidate_id': t['candidate_id'], 'dir': 'SHORT', 'sl': sl, 'entry': ep, 'tp': tp})
# mfe/mae availability
mfe_missing = sum(1 for t in trades if not isinstance(t['mfe_r'], (int, float)))

summary = json.load(open(SUMMARY))
sp = summary['split_profile_stats'][0]

scoreable = [t for t in trades if isinstance(t['net_r'], (int, float))]
recon = {
    'sum_net_r_57': round(sum(t['net_r'] for t in scoreable), 8),
    'summary_physical_net_r': sp['physical_net_r'],
    'sum_gross_r': round(sum(t['gross_r'] for t in scoreable), 8),
    'summary_physical_gross_r': sp['physical_gross_r'],
    'sum_cost_r_all57': round(sum(t['cost_r'] for t in trades if isinstance(t['cost_r'], (int, float))), 8),
    'summary_physical_expected_cost_r': sp['physical_expected_cost_r'],
    'sum_cost_r_scoreable55': round(sum(t['cost_r'] for t in scoreable), 8),
    'summary_physical_scoreable_cost_r': sp['physical_scoreable_expected_cost_r'],
    'summary_physical_cash_pnl': sp['physical_cash_pnl'],
    'headline_subset': {'n': 39, 'summary_headline_net_r': sp['headline_net_r'],
                        'recomputed_headline_net_r': round(sum(
                            t['net_r'] for t in trades
                            if t['headline_result_exclusion_reason'] == 'headline_result_eligible'), 8)},
    'trade_count': len(trades), 'order_count': d['order_rows'],
    'order_relationship': d['order_status_counts'],
    'pool_rows_scored': pool_rows, 'pool_net_sum': round(pool_net, 4),
    'pool_negative_days': neg_days, 'pool_scoreable_days': len(pool_days),
}

out = {
    'classification_rule': ('precedence: unscoreable -> winner(target/other) -> cost_dominated '
                            '(gross>=0 but net<0, or |gross|<=cost) -> exit_geometry (loss with '
                            'MFE>=+0.5R) -> direction_wrong (stop-class or MAE<=-0.9 with MFE<0.5) '
                            '-> horizon_marked -> other_loss'),
    'class_totals': dict(cls),
    'aggregations': aggs,
    'breaker_exposure': breaker_stat,
    'sizing': {'approved_risk_pct_all': 0.1, 'risk_cash_all': 100.0,
               'deviations': [t['candidate_id'] for t in trades
                              if t['approved_risk_pct'] != 0.1 or t['risk_cash'] != 100.0]},
    'day_clustering': {'days_with_trades': len(day_counts),
                       'max_trades_one_day': max(day_counts.values()),
                       'same_day_same_symbol_multiples': clusters,
                       'trade_day_series': trade_day_series},
    'pool_day_series': pool_day_series,
    'reconciliation': recon,
    'anomalies': {'duplicate_candidate_ids': dup_ids,
                  'cost_r_gt_1': cost_outliers,
                  'zero_or_negative_holding': zero_hold,
                  'headline_exclusion_counts': dict(excl),
                  'nonstandard_close_reasons': dict(weird_close),
                  'entry_price_outside_stop_target_band': price_sanity,
                  'mfe_mae_missing_count': mfe_missing},
}
with open(os.path.join(OUT, 'TRADES_JAN_ATTRIBUTION.json'), 'w') as f:
    json.dump(out, f, indent=1, default=str)

print(json.dumps({k: {'n': v['n'], 'net': v['net_r_sum']} for k, v in cls.items()}, indent=1))
print('pool days', len(pool_days), 'neg', neg_days, 'pool_net', round(pool_net, 3), 'rows', pool_rows)
print('days with trades', len(day_counts), 'clusters', clusters)
print('recon', json.dumps(recon, indent=1)[:1200])
print('breaker', breaker_stat['n'], breaker_stat['net_r_sum'])
print('anomalies: dup', dup_ids, '| cost>1', len(cost_outliers), '| zerohold', zero_hold, '| price_sanity', len(price_sanity), '| mfe_missing', mfe_missing)
