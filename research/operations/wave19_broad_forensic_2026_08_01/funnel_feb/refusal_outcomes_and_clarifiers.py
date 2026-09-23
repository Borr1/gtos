#!/usr/bin/env python3
"""Session FA funnel_feb — REFUSAL_OUTCOMES.json + CLARIFIERS.json for February,
mirroring funnel_jan's schemas exactly (see ../funnel_jan/pool_analysis.py and
clarifiers.py). Source: the February compact scoreable pool (24,239 rows).
FEBRUARY ATTRIBUTION EVIDENCE ONLY — owner mandate 2026-08-01."""
import json, gzip, collections

POOL = ('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/'
        'fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz')
OUT = ('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/research/operations/'
       'wave19_broad_forensic_2026_08_01/funnel_feb/')

rows = []
with gzip.open(POOL, 'rt') as f:
    for line in f:
        rows.append(json.loads(line))

def group_stats(sub):
    n = len(sub)
    if n == 0:
        return {'n': 0}
    nets = [r['opportunity_net_proxy_r'] for r in sub]
    costs = [r['cost_r'] for r in sub]
    gross = [nt + c for nt, c in zip(nets, costs)]
    pos = [x for x in nets if x > 0]
    return {'n': n,
            'sum_net_r': round(sum(nets), 4), 'mean_net_r': round(sum(nets) / n, 5),
            'mean_gross_r': round(sum(gross) / n, 5), 'sum_gross_r': round(sum(gross), 4),
            'mean_cost_r': round(sum(costs) / n, 5),
            'positive_share': round(len(pos) / n, 5), 'n_positive': len(pos),
            'sum_positive_net_r': round(sum(pos), 4),
            'sum_negative_net_r': round(sum(x for x in nets if x < 0), 4)}

def by(field):
    g = collections.defaultdict(list)
    for r in rows:
        g[str(r.get(field))].append(r)
    out = {}
    for k, sub in sorted(g.items(), key=lambda kv: -len(kv[1])):
        s = group_stats(sub)
        s['refusal_economically_correct_on_average'] = s['mean_net_r'] < 0
        out[k] = s
    return out

pool_total = group_stats(rows)
refusal = {
    'schema': 'gtos.session_fa.funnel_feb.refusal_outcomes.v1',
    'evidence_class': 'FEBRUARY ATTRIBUTION EVIDENCE ONLY - owner mandate 2026-08-01; never a selection surface',
    'pool_rows': len(rows),
    'pool_total': pool_total,
    'by_selector_reason': by('selector_reason'),
    'by_final_blocker_class': by('final_blocker_class'),
    'by_scheduler_selection_disposition': by('scheduler_selection_disposition'),
    'by_risk_finalizer_reason': by('risk_finalizer_reason'),
    'by_selector_action': by('selector_action'),
    'note': 'gross = net + cost_r. A gate is scored "economically correct on average" when the mean net proxy of the rows it refused is negative. Schema mirrors funnel_jan/REFUSAL_OUTCOMES.json for month-over-month comparison.',
}
json.dump(refusal, open(OUT + 'REFUSAL_OUTCOMES.json', 'w'), indent=1)

# ------------------- CLARIFIERS (mirror of funnel_jan/clarifiers.py) -------------------
PASS = {'trade', 'open-reduced-risk', 'reduce-risk'}

def st(sub):
    n = len(sub)
    nets = [r['opportunity_net_proxy_r'] for r in sub]
    return {'n': n, 'mean_net_r': round(sum(nets) / n, 5) if n else None,
            'sum_net_r': round(sum(nets), 3),
            'positive_share': round(sum(1 for x in nets if x > 0) / n, 4) if n else None}

rej_mat = [r for r in rows if r['selector_action'] == 'reject'
           and r['scheduler_materialization_status'] == 'scheduler_option_materialized']
anb = [r for r in rows if r['broker_pretrade_cost_executable'] is True
       and r['selector_action'] in PASS
       and r['scheduler_materialization_status'] != 'scheduler_option_materialized']
B = [r for r in rows if r['scheduler_materialization_status'] == 'scheduler_option_materialized']

def bucket(rk):
    if rk is None: return 'none'
    if rk <= 1: return '1'
    if rk <= 3: return '2-3'
    if rk <= 10: return '4-10'
    return '11+'

rankb = collections.defaultdict(list)
for r in B:
    rankb[bucket(r.get('risk_finalizer_rank'))].append(r)

eb = sorted([r for r in B if isinstance(r.get('expected_net_r'), (int, float))],
            key=lambda r: r['expected_net_r'])
n = len(eb); q = n // 4
ev_quartiles = {}
for i, name in enumerate(['Q1_lowest_expected_net', 'Q2', 'Q3', 'Q4_highest_expected_net']):
    seg = eb[i * q:(i + 1) * q if i < 3 else n]
    ev_quartiles[name] = {**st(seg),
                          'mean_expected_net_r': round(sum(r['expected_net_r'] for r in seg) / len(seg), 4)}

days = collections.defaultdict(float)
for r in rows:
    days[r['decision_time_utc'][:10]] += r['opportunity_net_proxy_r']

trade_rows = [r for r in rows if r['selector_action'] == 'trade']

clar = {
    'schema': 'gtos.session_fa.funnel_feb.clarifiers.v1',
    'evidence_class': 'FEBRUARY ATTRIBUTION EVIDENCE ONLY - owner mandate 2026-08-01; never a selection surface',
    'selector_reject_but_scheduler_materialized': {
        **st(rej_mat),
        'selector_reason': dict(collections.Counter(r['selector_reason'] for r in rej_mat)),
        'effective_selector_action': dict(collections.Counter(r['effective_selector_action'] for r in rej_mat)),
    },
    'A_not_B_cost_and_selector_passed_never_ranked': {
        **st(anb),
        'miss_reason_top': dict(collections.Counter(r['miss_reason'] for r in anb).most_common(8)),
    },
    'rank_vs_outcome_within_ranked_set': {k: st(v) for k, v in sorted(rankb.items())},
    'expected_net_quartiles_within_ranked_set': ev_quartiles,
    'scoreable_days': {'n_days': len(days), 'n_negative_days': sum(1 for v in days.values() if v < 0),
                       'daily_net_r': {k: round(v, 3) for k, v in sorted(days.items())}},
    'selector_trade_action_rows': {
        **st(trade_rows),
        'scheduler_selection_disposition': dict(collections.Counter(r['scheduler_selection_disposition'] for r in trade_rows)),
        'miss_reason': dict(collections.Counter(r['miss_reason'] for r in trade_rows)),
        'final_blocker_class': dict(collections.Counter(r['final_blocker_class'] for r in trade_rows)),
    },
}
json.dump(clar, open(OUT + 'CLARIFIERS.json', 'w'), indent=1)

print('pool_total', pool_total)
print('rej_mat', st(rej_mat))
print('anb', st(anb), list(clar['A_not_B_cost_and_selector_passed_never_ranked']['miss_reason_top'].items())[:3])
print('rank_vs_outcome', {k: st(v) for k, v in sorted(rankb.items())})
print('ev_quartiles', {k: (v['n'], v['mean_net_r'], v['mean_expected_net_r']) for k, v in ev_quartiles.items()})
print('days', clar['scoreable_days']['n_days'], 'neg', clar['scoreable_days']['n_negative_days'])
print('trade rows', st(trade_rows))
