#!/usr/bin/env python3
"""Session FA / February executed-trade walker — step 1: per-trade projection.

Streams the February TRADE ledger (58 rows, ~550 KB/row) line-by-line and
projects each row onto the walker schema (identity, mechanism, direction,
session, times, prices, close_reason, gross/cost/net R, sizing, model scores
at decision, MFE/MAE, first-touch class, best_available_exit_r).

Sources (read-only, wave18 worktree):
  CP_FEBRUARY_TRUE_UTC_S0R0_V1_TRADE_LEDGER.jsonl

Output: TRADES_FEB_TABLE.json in this directory.
"""
import json, os

ROUTE = ('/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/'
         'research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/'
         'attempt_5_typed_sparse/CP_FEBRUARY_TRUE_UTC_S0R0_V1')
TRADE_LEDGER = os.path.join(ROUTE, 'CP_FEBRUARY_TRUE_UTC_S0R0_V1_TRADE_LEDGER.jsonl')
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

FIELDS = [
    # identity
    'candidate_id', 'symbol',
    # mechanism
    'origin_family', 'setup_family', 'route_family', 'bucket_source_family',
    # direction / session
    'direction', 'side', 'session_bucket', 'route_session', 'kill_zone',
    'utc_hour_bucket', 'decision_timeframe',
    # times
    'decision_time_utc', 'entry_time_utc', 'exit_time_utc', 'duration_minutes',
    # prices
    'entry_price', 'stop_loss', 'take_profit_1',
    # outcome
    'close_reason', 'raw_close_reason', 'headline_result_exclusion_reason',
    'gross_r', 'final_r', 'cost_r', 'net_r',
    'spread_r', 'commission_r', 'swap_cost_r', 'expected_slippage_r',
    'total_execution_cost_r',
    # sizing
    'approved_risk_pct', 'risk_cash', 'risk_per_trade_pct',
    # model scores at decision
    'candidate_probability', 'candidate_confidence', 'candidate_ev_r',
    'expectancy_r', 'expected_net_r', 'expected_cost_r', 'fill_probability',
    'policy_target_r', 'raw_target_r',
    # oracle path
    'mfe_r', 'mae_r', 'mfe_time_utc', 'mae_time_utc',
    'entry_first_touch_utc', 'stop_first_touch_utc', 'target_first_touch_utc',
]


def first_touch_class(row):
    """Which terminal boundary was touched first on the ordered path."""
    st = row.get('stop_first_touch_utc')
    tt = row.get('target_first_touch_utc')
    if st and tt:
        return 'target_first' if tt < st else ('stop_first' if st < tt else 'same_bar_ambiguous')
    if tt:
        return 'target_only'
    if st:
        return 'stop_only'
    return 'neither'


def main():
    trades = []
    n = 0
    with open(TRADE_LEDGER) as f:
        for line in f:
            if not line.strip():
                continue
            n += 1
            row = json.loads(line)
            t = {k: row.get(k) for k in FIELDS}
            t['first_touch_class'] = first_touch_class(row)
            # best_available_exit_r: the best exit the ordered M1 path offered.
            # gross basis = mfe_r; net basis subtracts the trade's charged cost_r.
            mfe = t.get('mfe_r')
            cost = t.get('cost_r') or 0.0
            t['best_available_exit_gross_r'] = mfe
            t['best_available_exit_net_r'] = (mfe - cost) if mfe is not None else None
            trades.append(t)

    trades.sort(key=lambda t: (t['decision_time_utc'] or '', t['candidate_id'] or ''))

    tot_net = sum(t['net_r'] for t in trades)
    tot_gross = sum(t['final_r'] for t in trades)
    tot_cost = sum(t['cost_r'] for t in trades)

    out = {
        'schema': 'gtos.session_fa.trades_feb_table.v1',
        'session': 'FA-trades-feb-walker',
        'source_ledger': TRADE_LEDGER,
        'n_trades': n,
        'totals': {
            'sum_net_r': tot_net,
            'sum_gross_r': tot_gross,
            'sum_cost_r': tot_cost,
            'identity_check_gross_minus_cost': tot_gross - tot_cost,
        },
        'field_notes': {
            'gross_r': 'ledger final_r == gross_r on all rows (verified in script 01)',
            'best_available_exit_gross_r': 'mfe_r from the ordered M1 path oracle (120-min horizon of the arm)',
            'best_available_exit_net_r': 'mfe_r - cost_r (charged cost held fixed)',
            'first_touch_class': 'ordering of stop_first_touch_utc vs target_first_touch_utc',
        },
        'trades': trades,
    }
    # verify final_r == gross_r
    mism = [t['candidate_id'] for t in trades if t['gross_r'] is not None and abs((t['final_r'] or 0) - t['gross_r']) > 1e-9]
    out['field_notes']['final_r_vs_gross_r_mismatches'] = mism

    with open(os.path.join(OUT_DIR, 'TRADES_FEB_TABLE.json'), 'w') as f:
        json.dump(out, f, indent=1, default=str)
    print('n_trades', n)
    print('sum_net_r %.8f  sum_gross_r %.8f  sum_cost_r %.8f' % (tot_net, tot_gross, tot_cost))
    print('final_r!=gross_r mismatches:', mism)
    from collections import Counter
    print('close_reason:', Counter(t['close_reason'] for t in trades))
    print('first_touch:', Counter(t['first_touch_class'] for t in trades))
    print('net>0:', sum(1 for t in trades if t['net_r'] > 0), 'gross>0:', sum(1 for t in trades if t['final_r'] > 0))


if __name__ == '__main__':
    main()
