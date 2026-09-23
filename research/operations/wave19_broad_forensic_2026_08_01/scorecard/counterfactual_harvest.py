#!/usr/bin/env python3
"""Counterfactual per-decision-point harvest over the compact pools.

For each decision point (decision_time_utc) compute the proxy outcome of:
  - oracle best (max opportunity_net_proxy_r)          [ex-post, unknowable]
  - argmax expected_net_r                              [knowable ex-ante]
  - argmax candidate_probability                       [knowable ex-ante]
  - argmin cost_r                                      [knowable ex-ante]
  - random expectation (set mean)                      [the S0 reference]
  - executable-only variants (broker_pretrade_cost_executable == True)
NOTE: pool rows are non-executed misses; the proxy is diagnostic, and most
rows were cost-refused, so 'knowable' selections here ignore the fact that
the arm was FORBIDDEN from trading most of these rows. This bounds what a
selection layer could harvest from the same choice sets, it does not assert
the trades were placeable.
"""
import gzip, json, math
from collections import defaultdict

WT = '/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801'
POOLS = {
    'january': f'{WT}/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz',
    'february': f'{WT}/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz',
}


def fnum(v):
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def main():
    out = {}
    for win, path in POOLS.items():
        groups = defaultdict(list)
        with gzip.open(path, 'rt') as f:
            for line in f:
                r = json.loads(line)
                o = fnum(r.get('opportunity_net_proxy_r'))
                if o is None:
                    continue
                groups[r.get('decision_time_utc')].append((
                    o, fnum(r.get('expected_net_r')), fnum(r.get('candidate_probability')),
                    fnum(r.get('cost_r')), bool(r.get('broker_pretrade_cost_executable'))))
        res = {}
        strategies = {
            'oracle_best': lambda rows: max(rows, key=lambda t: t[0])[0],
            'argmax_expected_net_r': lambda rows: max(rows, key=lambda t: (t[1] is not None, t[1]))[0],
            'argmax_probability': lambda rows: max(rows, key=lambda t: (t[2] is not None, t[2]))[0],
            'argmin_cost': lambda rows: min(rows, key=lambda t: (t[3] is None, t[3]))[0],
            'set_mean_random': lambda rows: sum(t[0] for t in rows) / len(rows),
        }
        for name, fn in strategies.items():
            tot = n = pos = 0
            for rows in groups.values():
                v = fn(rows)
                tot += v; n += 1; pos += (v > 0)
            res[name] = {'n_decision_points': n, 'sum_r': round(tot, 2),
                         'mean_r_per_dp': round(tot / n, 4), 'share_positive': round(pos / n, 4)}
            # executable-only variant
            tot = n = pos = 0
            for rows in groups.values():
                er = [t for t in rows if t[4]]
                if not er:
                    continue
                v = fn(er)
                tot += v; n += 1; pos += (v > 0)
            res[name + '_executable_only'] = {'n_decision_points': n, 'sum_r': round(tot, 2),
                                              'mean_r_per_dp': round(tot / n, 4) if n else None,
                                              'share_positive': round(pos / n, 4) if n else None}
        out[win] = res
    with open(f'{WT}/research/operations/wave19_broad_forensic_2026_08_01/scorecard/COUNTERFACTUAL_HARVEST.json', 'w') as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
