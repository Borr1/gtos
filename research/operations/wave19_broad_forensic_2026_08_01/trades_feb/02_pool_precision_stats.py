#!/usr/bin/env python3
"""Session FA / February walker — step 2: pool-level precision statistics.

Streams the February compact scoreable pool (gz JSONL) line-by-line and
computes: net-basis precision inputs (cross-check against
CP_FEBRUARY_POOL_S0R0_V1.json), zero-cost (gross) counterfactual precision/
breakeven/net, cost by outcome sign, and W/L asymmetry decomposition inputs.
Nothing is loaded whole into memory.
"""
import gzip, json, os

POOL = ('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/'
        'docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/'
        'CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz')
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def acc():
    return {'n': 0, 'sum': 0.0}


def add(a, v):
    a['n'] += 1
    a['sum'] += v


def mean(a):
    return a['sum'] / a['n'] if a['n'] else None


def main():
    n = 0
    n_scoreable = 0
    net_pos, net_neg, net_flat = acc(), acc(), acc()
    gross_pos, gross_neg, gross_flat = acc(), acc(), acc()
    net_all, gross_all, cost_all = acc(), acc(), acc()
    cost_by_net_sign = {'pos': acc(), 'neg': acc()}
    gross_by_net_sign = {'pos': acc(), 'neg': acc()}
    # rows where cost flips a gross-positive row negative
    flipped = acc()          # gross>0 and net<=0
    flipped_gross = acc()
    close_reason_by_sign = {}
    identity_bad = 0

    with gzip.open(POOL, 'rt') as f:
        for line in f:
            if not line.strip():
                continue
            n += 1
            r = json.loads(line)
            if not r.get('missed_opportunity_non_executable_diagnostic_scoreable'):
                continue
            n_scoreable += 1
            net = r['opportunity_net_proxy_r']
            cost = r['cost_r']
            gross = r.get('opportunity_gross_r')
            if gross is None:
                gross = net + cost
            elif abs((net + cost) - gross) > 1e-6:
                identity_bad += 1
            add(net_all, net); add(gross_all, gross); add(cost_all, cost)
            (net_pos if net > 0 else (net_neg if net < 0 else net_flat)) and None
            if net > 0:
                add(net_pos, net); sign = 'pos'
            elif net < 0:
                add(net_neg, net); sign = 'neg'
            else:
                add(net_flat, net); sign = 'neg'
            if gross > 0:
                add(gross_pos, gross)
            elif gross < 0:
                add(gross_neg, gross)
            else:
                add(gross_flat, gross)
            add(cost_by_net_sign[sign], cost)
            add(gross_by_net_sign[sign], gross)
            if gross > 0 and net <= 0:
                add(flipped, net); add(flipped_gross, gross)
            cr = r.get('opportunity_close_reason') or 'none'
            d = close_reason_by_sign.setdefault(cr, {'pos': acc(), 'neg': acc()})
            add(d[sign], net)

    def be(w_mean, l_mean):
        # breakeven precision p*: p*W + (1-p*)L = 0  ->  p* = |L| / (W + |L|)
        if w_mean is None or l_mean is None:
            return None
        return abs(l_mean) / (w_mean + abs(l_mean))

    net_w, net_l = mean(net_pos), mean(net_neg)
    gr_w, gr_l = mean(gross_pos), mean(gross_neg)

    out = {
        'schema': 'gtos.session_fa.feb_pool_precision_stats.v1',
        'source_pool': POOL,
        'rows_in_compact_pool': n,
        'diagnostic_scoreable_rows': n_scoreable,
        'gross_eq_net_plus_cost_violations': identity_bad,
        'net_basis': {
            'positive_rows': net_pos['n'], 'negative_rows': net_neg['n'], 'flat_rows': net_flat['n'],
            'base_rate_positive': net_pos['n'] / n_scoreable,
            'mean_r_per_row': mean(net_all),
            'net_r_sum': net_all['sum'],
            'mean_winner_r': net_w, 'mean_loser_r': net_l,
            'breakeven_precision': be(net_w, net_l),
        },
        'zero_cost_counterfactual_gross_basis': {
            'positive_rows': gross_pos['n'], 'negative_rows': gross_neg['n'], 'flat_rows': gross_flat['n'],
            'base_rate_positive': gross_pos['n'] / n_scoreable,
            'mean_gross_r_per_row': mean(gross_all),
            'gross_r_sum': gross_all['sum'],
            'mean_winner_r': gr_w, 'mean_loser_r': gr_l,
            'breakeven_precision': be(gr_w, gr_l),
            'headroom': gross_pos['n'] / n_scoreable - be(gr_w, gr_l),
        },
        'cost': {
            'mean_cost_r': mean(cost_all), 'sum_cost_r': cost_all['sum'],
            'mean_cost_r_net_winners': mean(cost_by_net_sign['pos']),
            'mean_cost_r_net_losers': mean(cost_by_net_sign['neg']),
            'mean_gross_r_net_winners': mean(gross_by_net_sign['pos']),
            'mean_gross_r_net_losers': mean(gross_by_net_sign['neg']),
            'rows_gross_pos_flipped_negative_by_cost': flipped['n'],
            'net_r_sum_in_flipped_rows': flipped['sum'],
            'gross_r_sum_in_flipped_rows': flipped_gross['sum'],
        },
        'close_reason_by_net_sign': {
            cr: {'pos_n': d['pos']['n'], 'pos_sum': d['pos']['sum'],
                 'neg_n': d['neg']['n'], 'neg_sum': d['neg']['sum']}
            for cr, d in sorted(close_reason_by_sign.items())
        },
    }
    with open(os.path.join(OUT_DIR, 'FEB_POOL_PRECISION_STATS.json'), 'w') as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in ('rows_in_compact_pool', 'diagnostic_scoreable_rows',
                                          'net_basis', 'zero_cost_counterfactual_gross_basis', 'cost')}, indent=1))


if __name__ == '__main__':
    main()
