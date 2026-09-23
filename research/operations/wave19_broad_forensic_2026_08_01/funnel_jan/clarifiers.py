#!/usr/bin/env python3
"""Session FA funnel_jan — clarifier pass over the January compact pool.
Answers: (a) why selector-reject rows were scheduler-materialized, (b) what killed
the A\\B rows (cost-pass + selector-pass but never ranked), (c) whether scheduler
rank / the model's own expected_net_r carried outcome signal within the ranked set,
(d) day count, (e) dispositions of the 21 selector-action='trade' rows.
Writes CLARIFIERS.json.
"""
import json, gzip, collections

POOL = ('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/'
        'fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz')
OUT = ('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/research/operations/'
       'wave19_broad_forensic_2026_08_01/funnel_jan/CLARIFIERS.json')

rows = []
with gzip.open(POOL, 'rt') as f:
    for line in f:
        rows.append(json.loads(line))

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

out = {
    'schema': 'gtos.session_fa.funnel_jan.clarifiers.v1',
    'selector_reject_but_scheduler_materialized': {
        **st(rej_mat),
        'selector_reason': dict(collections.Counter(r['selector_reason'] for r in rej_mat)),
        'effective_selector_action': dict(collections.Counter(r['effective_selector_action'] for r in rej_mat)),
        'reading': 'router-refused candidates softened to effective open-reduced-risk and materialized for replay; this is the B\\A membership (207 rows).',
    },
    'A_not_B_cost_and_selector_passed_never_ranked': {
        **st(anb),
        'miss_reason_top': dict(collections.Counter(r['miss_reason'] for r in anb).most_common(8)),
        'reading': 'killed by signed-authority/config gates between selector and scheduler; best economics of any refused group (58.5% positive) but still negative mean.',
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
json.dump(out, open(OUT, 'w'), indent=1)
print(json.dumps(out['selector_trade_action_rows'], indent=1))
print('days', out['scoreable_days']['n_days'], 'neg', out['scoreable_days']['n_negative_days'])
