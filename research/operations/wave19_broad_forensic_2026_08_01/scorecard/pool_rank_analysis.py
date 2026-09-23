#!/usr/bin/env python3
"""Rank-vs-outcome + rank-driver + neutrality analysis over the compact pools.

Streams the January/February compact scoreable pools, groups rows by decision
point (decision_time_utc), and measures:
  (a) within-set Spearman of risk_finalizer_rank vs opportunity_net_proxy_r
  (b) chosen-candidate outcome percentile within its choice set (lane trades)
  (c) rank-1 vs rank-last mean realized proxy outcome
  (d) which score component actually drives the rank ordering
Everything is stdlib-only and line-streamed.
"""
import gzip, json, math, sys
from collections import defaultdict

WT = '/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801'
WINDOWS = {
    'january': {
        'pool': f'{WT}/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz',
        'lane': f'{WT}/docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl',
    },
    'february': {
        'pool': f'{WT}/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz',
        'lane': f'{WT}/docs/audits/fable5-vision-audit-20260725/phase18/receipts/CP_FEBRUARY_TRUE_UTC_S0R0_V1_LANE/LANE_TRADE_TABLE.jsonl',
    },
}

SCORE_FIELDS = ['expected_net_r', 'candidate_probability', 'cost_r',
                'candidate_confidence', 'fill_probability', 'candidate_ev_r',
                'spread_r', 'expectancy_r', 'expected_cost_r']


def fnum(v):
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def rankdata(xs):
    """Average ranks (1-based) with ties."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(x, y):
    n = len(x)
    if n < 2:
        return None
    rx, ry = rankdata(x), rankdata(y)
    mx = sum(rx) / n
    my = sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def pooled_within_set_spearman(groups, xkey, ykey):
    """Spearman computed per set (>=2 valid pairs, x has variation), then
    n-weighted mean; plus a pooled Spearman over within-set percentiles."""
    per_set = []
    all_px, all_py = [], []
    for rows in groups.values():
        xs, ys = [], []
        for r in rows:
            x, y = r.get(xkey), r.get(ykey)
            if x is not None and y is not None:
                xs.append(x); ys.append(y)
        if len(xs) < 2 or len(set(xs)) < 2 or len(set(ys)) < 2:
            continue
        s = spearman(xs, ys)
        if s is not None:
            per_set.append((len(xs), s))
        rx, ry = rankdata(xs), rankdata(ys)
        n = len(xs)
        for a, b in zip(rx, ry):
            all_px.append((a - 1) / (n - 1))
            all_py.append((b - 1) / (n - 1))
    if not per_set:
        return {'n_sets': 0}
    wsum = sum(n for n, _ in per_set)
    return {
        'n_sets': len(per_set),
        'n_pairs': wsum,
        'weighted_mean_spearman': sum(n * s for n, s in per_set) / wsum,
        'unweighted_mean_spearman': sum(s for _, s in per_set) / len(per_set),
        'pooled_percentile_spearman': spearman(all_px, all_py),
        'share_sets_positive': sum(1 for _, s in per_set if s > 0) / len(per_set),
    }


def main():
    out = {}
    for win, paths in WINDOWS.items():
        groups = defaultdict(list)   # decision_time_utc -> list of dicts
        n_rows = 0
        rank_missing = 0
        net_sum = 0.0
        pos = 0
        field_missing = defaultdict(int)
        with gzip.open(paths['pool'], 'rt') as f:
            for line in f:
                r = json.loads(line)
                n_rows += 1
                keep = {'candidate_id': r.get('candidate_id'),
                        'symbol': r.get('symbol'),
                        'rank': fnum(r.get('risk_finalizer_rank')),
                        'outcome': fnum(r.get('opportunity_net_proxy_r')),
                        'risk_finalizer_reason': r.get('risk_finalizer_reason'),
                        'scheduler_selection_disposition': r.get('scheduler_selection_disposition')}
                for k in SCORE_FIELDS:
                    keep[k] = fnum(r.get(k))
                    if keep[k] is None:
                        field_missing[k] += 1
                if keep['rank'] is None:
                    rank_missing += 1
                if keep['outcome'] is not None:
                    net_sum += keep['outcome']
                    if keep['outcome'] > 0:
                        pos += 1
                groups[r.get('decision_time_utc')].append(keep)
        res = {'pool_rows': n_rows,
               'decision_points': len(groups),
               'rank_missing_rows': rank_missing,
               'pool_net_sum_cross_check': round(net_sum, 3),
               'pool_positive_rows_cross_check': pos,
               'score_field_missing_counts': dict(field_missing)}

        # set size distribution
        sizes = sorted(len(v) for v in groups.values())
        res['set_size'] = {'min': sizes[0], 'p50': sizes[len(sizes)//2],
                           'max': sizes[-1],
                           'mean': sum(sizes)/len(sizes),
                           'sets_ge2': sum(1 for s in sizes if s >= 2)}

        # (a) rank vs outcome
        res['rank_vs_outcome'] = pooled_within_set_spearman(groups, 'rank', 'outcome')

        # (c) rank-1 vs rank-last realized proxy outcome (sets >=2, ranks present)
        r1, rlast, rbest_by_rank = [], [], []
        for rows in groups.values():
            rr = [r for r in rows if r['rank'] is not None and r['outcome'] is not None]
            if len(rr) < 2:
                continue
            rr.sort(key=lambda r: r['rank'])
            if rr[0]['rank'] == rr[-1]['rank']:
                continue
            r1.append(rr[0]['outcome'])
            rlast.append(rr[-1]['outcome'])
        res['rank1_vs_ranklast'] = {
            'n_sets': len(r1),
            'mean_outcome_rank1': (sum(r1)/len(r1)) if r1 else None,
            'mean_outcome_ranklast': (sum(rlast)/len(rlast)) if rlast else None,
        }

        # (d) rank drivers
        res['rank_drivers'] = {k: pooled_within_set_spearman(groups, 'rank', k)
                               for k in SCORE_FIELDS}
        # driver-vs-outcome for reference: does expected_net_r predict outcome?
        res['score_vs_outcome'] = {k: pooled_within_set_spearman(groups, k, 'outcome')
                                   for k in ['expected_net_r', 'candidate_probability',
                                             'cost_r', 'expectancy_r']}

        # (b) chosen-candidate percentile within choice set
        trades = []
        with open(paths['lane']) as f:
            meta = json.loads(f.readline())
            for line in f:
                t = json.loads(line)
                if t.get('row_kind') == 'trade':
                    trades.append(t)
        chosen = []
        matched = 0
        for t in trades:
            dt = t.get('decision_time_utc')
            net = fnum(t.get('net_r'))
            rows = groups.get(dt, [])
            outs = [r['outcome'] for r in rows if r['outcome'] is not None
                    and r['candidate_id'] != t.get('candidate_id')]
            if net is None or not outs:
                continue
            matched += 1
            below = sum(1 for o in outs if o < net)
            equal = sum(1 for o in outs if o == net)
            pct = (below + 0.5 * equal) / len(outs)
            chosen.append({'candidate_id': t.get('candidate_id'), 'symbol': t.get('symbol'),
                           'decision_time_utc': dt, 'net_r': net,
                           'set_size_excl_chosen': len(outs),
                           'outcome_percentile': pct,
                           'set_max_outcome': max(outs), 'set_mean_outcome': sum(outs)/len(outs),
                           'n_set_positive': sum(1 for o in outs if o > 0)})
        pcts = [c['outcome_percentile'] for c in chosen]
        res['chosen_percentile'] = {
            'n_trades_lane': len(trades),
            'n_trades_with_pool_set': matched,
            'mean_percentile': (sum(pcts)/len(pcts)) if pcts else None,
            'median_percentile': sorted(pcts)[len(pcts)//2] if pcts else None,
            'share_below_set_mean': (sum(1 for c in chosen if c['net_r'] < c['set_mean_outcome'])/len(chosen)) if chosen else None,
            'share_set_had_positive_option': (sum(1 for c in chosen if c['n_set_positive'] > 0)/len(chosen)) if chosen else None,
            'mean_chosen_net_r': (sum(c['net_r'] for c in chosen)/len(chosen)) if chosen else None,
            'mean_set_mean_outcome': (sum(c['set_mean_outcome'] for c in chosen)/len(chosen)) if chosen else None,
            'mean_set_max_outcome': (sum(c['set_max_outcome'] for c in chosen)/len(chosen)) if chosen else None,
            'detail': chosen,
        }

        # positive-option census: decision points with >=1 positive proxy
        dp_pos = sum(1 for rows in groups.values()
                     if any(r['outcome'] is not None and r['outcome'] > 0 for r in rows))
        res['decision_points_with_positive_option'] = dp_pos

        # rank distribution + reason mix at rank 1
        from collections import Counter
        rank_counter = Counter()
        for rows in groups.values():
            for r in rows:
                if r['rank'] is not None:
                    rank_counter[int(r['rank'])] += 1
        res['risk_finalizer_rank_hist_top'] = dict(sorted(rank_counter.items())[:12])
        res['scheduler_selection_disposition_counts'] = dict(Counter(
            r['scheduler_selection_disposition'] for rows in groups.values() for r in rows).most_common(15))
        res['risk_finalizer_reason_counts'] = dict(Counter(
            r['risk_finalizer_reason'] for rows in groups.values() for r in rows).most_common(15))
        out[win] = res
        print(f'{win}: rows={n_rows} dps={len(groups)} done', file=sys.stderr)

    with open(f'{WT}/research/operations/wave19_broad_forensic_2026_08_01/scorecard/RANK_OUTCOME.json', 'w') as f:
        json.dump({w: {k: v for k, v in r.items() if k not in ('rank_drivers', 'score_vs_outcome')}
                   for w, r in out.items()}, f, indent=1, default=str)
    with open(f'{WT}/research/operations/wave19_broad_forensic_2026_08_01/scorecard/RANK_DRIVERS.json', 'w') as f:
        json.dump({w: {'rank_drivers': r['rank_drivers'], 'score_vs_outcome': r['score_vs_outcome'],
                       'score_field_missing_counts': r['score_field_missing_counts']}
                   for w, r in out.items()}, f, indent=1, default=str)
    print(json.dumps({w: {'rank_vs_outcome': r['rank_vs_outcome'],
                          'rank1_vs_ranklast': r['rank1_vs_ranklast'],
                          'chosen': {k: v for k, v in r['chosen_percentile'].items() if k != 'detail'},
                          'dp_with_pos': r['decision_points_with_positive_option'],
                          'set_size': r['set_size']} for w, r in out.items()}, indent=1, default=str))


if __name__ == '__main__':
    main()
