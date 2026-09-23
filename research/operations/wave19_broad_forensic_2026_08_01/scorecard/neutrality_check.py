#!/usr/bin/env python3
"""S0 neutrality verification.

Two empirical tests of `neutral_hash_hard_eligible` selection:
 1. SCORE-BLINDNESS: for each executed trade, the percentile of its
    predecision score (expected_net_r, candidate_probability, cost_r) within
    its decision-point choice set (compact pool rows at same
    decision_time_utc). A quality-ranked selector concentrates at 1.0;
    an outcome/score-blind selector is ~uniform.
 2. HASH MECHANISM: recompute neutral_rank_sha256 =
    sha256(seed | decision_window_id | candidate_id@@decision_time) for the
    chosen candidate and every pool competitor; report the chosen hash's
    percentile (lower hash = earlier pick). Chosen should sit LOW among the
    truly hard-eligible; among the full pool (mostly cost-blocked, never in
    the hash draw) it is diagnostic only.
Streams the TRADE ledgers (57/58 rows x ~385 KB) line-by-line.
"""
import gzip, hashlib, json, math
from collections import defaultdict

WT = '/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801'
W16 = '/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731'
W18 = '/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801'
ROUTE = 'research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse'
WINDOWS = {
    'january': {
        'pool': f'{WT}/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz',
        'trade': f'{W16}/{ROUTE}/CJ_RECLOCKED_S0R0_V7/CJ_RECLOCKED_S0R0_V7_TRADE_LEDGER.jsonl',
    },
    'february': {
        'pool': f'{WT}/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz',
        'trade': f'{W18}/{ROUTE}/CP_FEBRUARY_TRUE_UTC_S0R0_V1/CP_FEBRUARY_TRUE_UTC_S0R0_V1_TRADE_LEDGER.jsonl',
    },
}


def fnum(v):
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def pct(value, others, reverse=False):
    if value is None or not others:
        return None
    below = sum(1 for o in others if o < value)
    equal = sum(1 for o in others if o == value)
    p = (below + 0.5 * equal) / len(others)
    return 1.0 - p if reverse else p


def neutral_hash(seed, window_id, candidate_id, decision_time):
    key = f'{candidate_id}@@{decision_time}'
    return hashlib.sha256(f'{seed}|{window_id}|{key}'.encode()).hexdigest()


def main():
    out = {}
    for win, paths in WINDOWS.items():
        groups = defaultdict(list)
        with gzip.open(paths['pool'], 'rt') as f:
            for line in f:
                r = json.loads(line)
                groups[r.get('decision_time_utc')].append({
                    'candidate_id': r.get('candidate_id'),
                    'expected_net_r': fnum(r.get('expected_net_r')),
                    'candidate_probability': fnum(r.get('candidate_probability')),
                    'cost_r': fnum(r.get('cost_r')),
                    'fill_probability': fnum(r.get('fill_probability')),
                    'risk_finalizer_reason': r.get('risk_finalizer_reason'),
                })
        trades = []
        with open(paths['trade']) as f:
            for line in f:
                t = json.loads(line)
                trades.append({
                    'candidate_id': t.get('candidate_id'),
                    'decision_time_utc': t.get('decision_time_utc'),
                    'decision_window_id': t.get('decision_window_id'),
                    'seed': t.get('b7_5_selection_sizing_factorial_neutral_selection_seed_sha256'),
                    'expected_net_r': fnum(t.get('expected_net_r')),
                    'candidate_probability': fnum(t.get('candidate_probability')),
                    'cost_r': fnum(t.get('cost_r')),
                    'fill_probability': fnum(t.get('fill_probability')),
                    'net_r': fnum(t.get('net_r')),
                    'probe_rank': t.get('risk_finalizer_probe_rank'),
                    'probe_selected': t.get('risk_finalizer_probe_selected'),
                })
        detail = []
        for t in trades:
            comp = [c for c in groups.get(t['decision_time_utc'], [])
                    if c['candidate_id'] != t['candidate_id']]
            if not comp:
                continue
            row = {'candidate_id': t['candidate_id'],
                   'decision_time_utc': t['decision_time_utc'],
                   'set_size': len(comp),
                   'probe_rank': t['probe_rank'],
                   'net_r': t['net_r']}
            for k in ('expected_net_r', 'candidate_probability', 'fill_probability'):
                row[f'{k}_percentile'] = pct(t[k], [c[k] for c in comp if c[k] is not None])
            row['cost_r_percentile'] = pct(t['cost_r'], [c['cost_r'] for c in comp if c['cost_r'] is not None])
            # hash percentile: chosen hash vs competitors' hashes (full pool set)
            if t['seed'] and t['decision_window_id']:
                ch = neutral_hash(t['seed'], t['decision_window_id'], t['candidate_id'], t['decision_time_utc'])
                hs = [neutral_hash(t['seed'], t['decision_window_id'], c['candidate_id'], t['decision_time_utc'])
                      for c in comp]
                row['neutral_hash_percentile_full_pool'] = pct(ch, hs)
            detail.append(row)

        def summarize(key):
            vals = [d[key] for d in detail if d.get(key) is not None]
            if not vals:
                return None
            vals_sorted = sorted(vals)
            n = len(vals)
            mean = sum(vals) / n
            # z against uniform(0,1): sd 0.2887
            z = (mean - 0.5) / (0.2886751 / math.sqrt(n))
            return {'n': n, 'mean': mean, 'median': vals_sorted[n // 2],
                    'z_vs_uniform': z,
                    'share_top_decile': sum(1 for v in vals if v >= 0.9) / n,
                    'share_bottom_decile': sum(1 for v in vals if v <= 0.1) / n}

        out[win] = {
            'n_trades': len(trades),
            'n_with_set': len(detail),
            'probe_rank_hist': {},
            'selection_mode_from_code': 'neutral_hash_hard_eligible (v4_timewarp_simulated_live_research_loop.py:36251,:36459-36483; rank key :52318-52323; sort :52345-52350)',
            'percentile_summaries': {
                'expected_net_r': summarize('expected_net_r_percentile'),
                'candidate_probability': summarize('candidate_probability_percentile'),
                'cost_r': summarize('cost_r_percentile'),
                'fill_probability': summarize('fill_probability_percentile'),
                'neutral_hash_full_pool': summarize('neutral_hash_percentile_full_pool'),
            },
            'detail': detail,
        }
        from collections import Counter
        out[win]['probe_rank_hist'] = dict(Counter(str(t['probe_rank']) for t in trades))
        out[win]['probe_selected_all_true'] = all(t['probe_selected'] is True for t in trades)

    with open(f'{WT}/research/operations/wave19_broad_forensic_2026_08_01/scorecard/NEUTRALITY.json', 'w') as f:
        json.dump(out, f, indent=1, default=str)
    for w, r in out.items():
        print(w, r['n_trades'], 'trades; probe_rank_hist', r['probe_rank_hist'])
        for k, s in r['percentile_summaries'].items():
            print('  ', k, s)


if __name__ == '__main__':
    main()
