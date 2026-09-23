#!/usr/bin/env python3
"""Session FA funnel_feb — Task 1 + 5: full physical census of the February
CJ_RECLOCKED_S0R0_V7 MISSED_OPPORTUNITY ledger (129,165 rows, 1.21 GB), streamed
line-by-line. Produces FUNNEL_CENSUS.json and NONSCOREABLE_CENSUS.json.

Full-ledger key names differ from the compact pool:
  final_blocker_class          -> missed_package_replay_order_executable_final_blocker_class
(verified by direct read of row 1 of the ledger.)
"""
import json, collections, sys

LEDGER = ('/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/research/operations/'
          'final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/'
          'attempt_5_typed_sparse/CP_FEBRUARY_TRUE_UTC_S0R0_V1/CP_FEBRUARY_TRUE_UTC_S0R0_V1_MISSED_OPPORTUNITY_LEDGER.jsonl')
OUT = '/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/research/operations/wave19_broad_forensic_2026_08_01/funnel_feb/'

FBC = 'missed_package_replay_order_executable_final_blocker_class'

single_fields = ['selector_action', 'selector_reason', 'effective_selector_action',
                 'effective_selector_reason', 'scheduler_materialization_status',
                 'scheduler_selection_disposition', 'risk_finalizer_rank',
                 'risk_finalizer_reason', 'miss_reason', FBC,
                 'candidate_lifecycle_action', 'pretrade_cost_packet_status',
                 'broker_pretrade_cost_executable',
                 'missed_opportunity_r_scoreability_status']

joints = [
    ('selector_action', 'selector_reason'),
    ('selector_action', 'scheduler_materialization_status'),
    ('selector_action', 'pretrade_cost_packet_status'),
    ('selector_reason', 'pretrade_cost_packet_status'),
    ('scheduler_materialization_status', 'scheduler_selection_disposition'),
    ('scheduler_selection_disposition', 'risk_finalizer_reason'),
    ('scheduler_selection_disposition', FBC),
    ('selector_action', FBC),
    ('risk_finalizer_reason', FBC),
    ('missed_opportunity_r_scoreability_status', 'miss_reason'),
    ('missed_opportunity_r_scoreability_status', 'selector_action'),
    ('missed_opportunity_r_scoreability_status', FBC),
    ('missed_opportunity_r_scoreability_status', 'scheduler_materialization_status'),
]

singles = {f: collections.Counter() for f in single_fields}
joint_counts = {f'{a}|X|{b}': collections.Counter() for a, b in joints}
# risk_finalizer_rank per reason: n, min, max
rank_by_reason = {}
# proxy availability by scoreability status
proxy_nonnull = collections.Counter()
proxy_null = collections.Counter()

n = 0
with open(LEDGER, 'r') as f:
    for line in f:
        d = json.loads(line)
        n += 1
        for fl in single_fields:
            singles[fl][str(d.get(fl))] += 1
        for a, b in joints:
            joint_counts[f'{a}|X|{b}'][f'{d.get(a)} || {d.get(b)}'] += 1
        rr = str(d.get('risk_finalizer_reason'))
        rk = d.get('risk_finalizer_rank')
        e = rank_by_reason.setdefault(rr, {'n': 0, 'min': None, 'max': None})
        e['n'] += 1
        if isinstance(rk, (int, float)):
            e['min'] = rk if e['min'] is None else min(e['min'], rk)
            e['max'] = rk if e['max'] is None else max(e['max'], rk)
        st = str(d.get('missed_opportunity_r_scoreability_status'))
        if d.get('opportunity_net_proxy_r') is None:
            proxy_null[st] += 1
        else:
            proxy_nonnull[st] += 1
        if n % 20000 == 0:
            print(f'  {n} rows', file=sys.stderr)

out = {
    'schema': 'gtos.session_fa.funnel_feb.full_census.v1',
    'ledger': LEDGER,
    'total_physical_rows': n,
    'single_field_distributions': {f: dict(c.most_common()) for f, c in singles.items()},
    'joint_distributions': {k: dict(c.most_common()) for k, c in joint_counts.items()},
    'risk_finalizer_rank_by_reason': rank_by_reason,
}
with open(OUT + 'FUNNEL_CENSUS.json', 'w') as f:
    json.dump(out, f, indent=1)

ns = {
    'schema': 'gtos.session_fa.funnel_feb.nonscoreable_census.v1',
    'ledger': LEDGER,
    'total_physical_rows': n,
    'scoreability_status_counts': dict(singles['missed_opportunity_r_scoreability_status'].most_common()),
    'proxy_field_nonnull_by_status': dict(proxy_nonnull),
    'proxy_field_null_by_status': dict(proxy_null),
    'status_x_miss_reason': dict(joint_counts['missed_opportunity_r_scoreability_status|X|miss_reason'].most_common()),
    'status_x_selector_action': dict(joint_counts['missed_opportunity_r_scoreability_status|X|selector_action'].most_common()),
    'status_x_final_blocker_class': dict(joint_counts[f'missed_opportunity_r_scoreability_status|X|{FBC}'].most_common()),
    'status_x_scheduler_materialization': dict(joint_counts['missed_opportunity_r_scoreability_status|X|scheduler_materialization_status'].most_common()),
}
with open(OUT + 'NONSCOREABLE_CENSUS.json', 'w') as f:
    json.dump(ns, f, indent=1)
print('DONE', n)
