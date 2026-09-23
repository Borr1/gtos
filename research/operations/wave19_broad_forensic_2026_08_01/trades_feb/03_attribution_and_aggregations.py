#!/usr/bin/env python3
"""Session FA / February walker — step 3: per-trade loss attribution + aggregations
+ January executed-book comparison under the SAME deterministic class rules.

Class rules (priority order, first match wins), documented for receipt use:
  target_hit      : net_r > 0 and close_reason is a target close
  (winners with a non-target close land in `other` with subclass
   `winner_non_target_exit` so every trade carries a class and class net_r
   totals sum exactly to the realized month figure)
  cost_dominated  : gross_r >= 0 and net_r <= 0  (cost flipped the sign)
  direction_wrong : mfe_r < 0.25  (path never offered >= 0.25R favorable excursion)
  exit_geometry   : mfe_r - cost_r > 0  (a net-profitable exit existed on the
                    ordered path; the exit policy failed to capture it)
  stop_hit        : close_reason is a stop close
  horizon_marked  : close_reason is a path-end mark-to-market / time stop
  other           : remainder

January comparison streams the January TRADE ledger (57 rows) from the wave16
worktree read-only and applies identical rules.
"""
import json, os
from collections import defaultdict

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FEB_TABLE = os.path.join(OUT_DIR, 'TRADES_FEB_TABLE.json')
JAN_TRADE_LEDGER = ('/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/'
                    'research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/'
                    'attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/CJ_RECLOCKED_S0R0_V7_TRADE_LEDGER.jsonl')

TARGET_REASONS = ('final_target', 'target_reached_before_stop')
STOP_REASONS = ('stop_loss', 'stop_reached_before_target')
HORIZON_REASONS = ('path_end_mark_to_market', 'time_stop')


def reason_kind(cr):
    cr = (cr or '').split(':')[-1]
    if any(t in cr for t in TARGET_REASONS):
        return 'target'
    if any(s in cr for s in STOP_REASONS):
        return 'stop'
    if any(h in cr for h in HORIZON_REASONS):
        return 'horizon'
    if 'giveback' in cr:
        return 'giveback'
    return 'other'


def classify(t):
    net, gross = t['net_r'], t['final_r']
    if net is None or gross is None:
        # January carries 2 terminal_r_unscoreable executed rows (ordered-tick
        # sequence required); they are outside the realized sum by construction.
        return 'unscoreable', t.get('headline_result_exclusion_reason')
    mfe = t.get('mfe_r')
    cost = t.get('cost_r') or 0.0
    kind = reason_kind(t.get('close_reason'))
    if net > 0:
        if kind == 'target':
            return 'target_hit', None
        return 'other', 'winner_non_target_exit'
    if gross >= 0 and net <= 0:
        return 'cost_dominated', None
    if mfe is not None and mfe < 0.25:
        return 'direction_wrong', None
    if mfe is not None and (mfe - cost) > 0:
        return 'exit_geometry', None
    if kind == 'stop':
        return 'stop_hit', None
    if kind in ('horizon', 'giveback'):
        return 'horizon_marked', None
    return 'other', None


def class_totals(trades):
    out = defaultdict(lambda: {'n': 0, 'net_r': 0.0, 'gross_r': 0.0, 'cost_r': 0.0,
                               'mfe_sum': 0.0, 'mae_sum': 0.0, 'candidate_ids': []})
    for t in trades:
        c = out[t['loss_class']]
        c['n'] += 1
        c['net_r'] += t['net_r'] or 0.0
        c['gross_r'] += t['final_r'] or 0.0
        c['cost_r'] += t['cost_r'] or 0.0
        c['mfe_sum'] += t.get('mfe_r') or 0.0
        c['mae_sum'] += t.get('mae_r') or 0.0
        c['candidate_ids'].append(t['candidate_id'])
    for c in out.values():
        c['mean_mfe_r'] = c['mfe_sum'] / c['n']
        c['mean_mae_r'] = c['mae_sum'] / c['n']
        del c['mfe_sum'], c['mae_sum']
    return dict(out)


def group_stats(trades, key_fn):
    g = defaultdict(list)
    for t in trades:
        if t['net_r'] is None:
            continue
        g[key_fn(t)].append(t)
    out = {}
    for k, ts in sorted(g.items(), key=lambda kv: str(kv[0])):
        wins = [t['net_r'] for t in ts if t['net_r'] > 0]
        losses = [t['net_r'] for t in ts if t['net_r'] <= 0]
        w = sum(wins) / len(wins) if wins else None
        l = sum(losses) / len(losses) if losses else None
        prec = len(wins) / len(ts)
        be = abs(l) / (w + abs(l)) if (w is not None and l is not None and (w + abs(l)) > 0) else (0.0 if w else None)
        out[str(k)] = {
            'n': len(ts), 'net_r_sum': sum(t['net_r'] for t in ts),
            'gross_r_sum': sum(t['final_r'] for t in ts),
            'cost_r_sum': sum(t['cost_r'] for t in ts),
            'precision': prec, 'mean_winner_r': w, 'mean_loser_r': l,
            'own_breakeven': be,
            'above_own_breakeven': (be is not None and prec > be),
            'net_positive': sum(t['net_r'] for t in ts) > 0,
        }
    return out


def jan_first_touch(row):
    st, tt = row.get('stop_first_touch_utc'), row.get('target_first_touch_utc')
    if st and tt:
        return 'target_first' if tt < st else ('stop_first' if st < tt else 'same_bar_ambiguous')
    return 'target_only' if tt else ('stop_only' if st else 'neither')


JAN_FIELDS = ['candidate_id', 'symbol', 'origin_family', 'setup_family', 'direction',
              'session_bucket', 'decision_time_utc', 'close_reason', 'final_r', 'gross_r',
              'cost_r', 'net_r', 'mfe_r', 'mae_r', 'stop_first_touch_utc',
              'target_first_touch_utc', 'duration_minutes']


def load_jan():
    trades = []
    with open(JAN_TRADE_LEDGER) as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            t = {k: row.get(k) for k in JAN_FIELDS}
            t['first_touch_class'] = jan_first_touch(row)
            trades.append(t)
    return trades


def main():
    feb = json.load(open(FEB_TABLE))['trades']
    for t in feb:
        t['loss_class'], t['loss_subclass'] = classify(t)

    jan = load_jan()
    for t in jan:
        t['loss_class'], t['loss_subclass'] = classify(t)

    feb_classes = class_totals(feb)
    jan_classes = class_totals(jan)
    for cls in jan_classes.values():
        del cls['candidate_ids']  # keep January light; ids are the Jan walker's job

    aggs = {
        'origin_family': group_stats(feb, lambda t: t['origin_family']),
        'direction': group_stats(feb, lambda t: t['direction']),
        'symbol': group_stats(feb, lambda t: t['symbol']),
        'session_bucket': group_stats(feb, lambda t: t['session_bucket']),
        'close_reason': group_stats(feb, lambda t: t['close_reason']),
        'first_touch_class': group_stats(feb, lambda t: t['first_touch_class']),
    }
    jan_aggs = {
        'origin_family': group_stats(jan, lambda t: t['origin_family']),
        'direction': group_stats(jan, lambda t: t['direction']),
        'symbol': group_stats(jan, lambda t: t['symbol']),
        'session_bucket': group_stats(jan, lambda t: t['session_bucket']),
        'close_reason': group_stats(jan, lambda t: t['close_reason']),
        'first_touch_class': group_stats(jan, lambda t: t['first_touch_class']),
    }

    out = {
        'schema': 'gtos.session_fa.trades_feb_attribution.v1',
        'class_rules_priority': [
            'target_hit: net_r>0 and target close',
            "other/winner_non_target_exit: net_r>0, non-target close",
            'cost_dominated: gross_r>=0 and net_r<=0',
            'direction_wrong: mfe_r<0.25',
            'exit_geometry: (mfe_r - cost_r)>0',
            'stop_hit: stop close', 'horizon_marked: path-end mark / time stop / giveback',
            'other: remainder'],
        'february': {
            'n_trades': len(feb),
            'sum_net_r': sum(t['net_r'] for t in feb),
            'class_totals': feb_classes,
            'aggregations': aggs,
        },
        'january_same_rules': {
            'source': JAN_TRADE_LEDGER,
            'n_trades': len(jan),
            'sum_net_r': sum(t['net_r'] or 0.0 for t in jan),
            'class_totals': jan_classes,
            'aggregations': jan_aggs,
        },
        'per_trade_classes': [
            {'candidate_id': t['candidate_id'], 'symbol': t['symbol'],
             'decision_time_utc': t['decision_time_utc'], 'net_r': t['net_r'],
             'loss_class': t['loss_class'], 'loss_subclass': t['loss_subclass']}
            for t in feb],
    }
    with open(os.path.join(OUT_DIR, 'TRADES_FEB_ATTRIBUTION.json'), 'w') as f:
        json.dump(out, f, indent=1, default=str)

    # also re-write the trade table with classes attached
    tbl = json.load(open(FEB_TABLE))
    tbl['trades'] = feb
    with open(FEB_TABLE, 'w') as f:
        json.dump(tbl, f, indent=1, default=str)

    print('FEB classes:')
    for k, v in sorted(feb_classes.items()):
        print(f"  {k:18s} n={v['n']:3d} net={v['net_r']:+9.4f} gross={v['gross_r']:+9.4f} cost={v['cost_r']:8.4f} mfe~{v['mean_mfe_r']:+.3f} mae~{v['mean_mae_r']:+.3f}")
    print('  sum check', sum(v['net_r'] for v in feb_classes.values()))
    print('JAN classes (same rules, n=%d, sum=%.4f):' % (len(jan), sum(t['net_r'] or 0.0 for t in jan)))
    for k, v in sorted(jan_classes.items()):
        print(f"  {k:18s} n={v['n']:3d} net={v['net_r']:+9.4f} gross={v['gross_r']:+9.4f} cost={v['cost_r']:8.4f}")
    print('\nFEB families:')
    for k, v in aggs['origin_family'].items():
        print(f"  {k:40s} n={v['n']:3d} net={v['net_r_sum']:+9.4f} prec={v['precision']:.3f} be={v['own_breakeven']}")
    print('JAN families:')
    for k, v in jan_aggs['origin_family'].items():
        print(f"  {k:40s} n={v['n']:3d} net={v['net_r_sum']:+9.4f} prec={v['precision']:.3f} be={v['own_breakeven']}")


if __name__ == '__main__':
    main()
