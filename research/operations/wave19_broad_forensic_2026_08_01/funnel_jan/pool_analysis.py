#!/usr/bin/env python3
"""Session FA funnel_jan — Tasks 2, 3, 4, 6 over the January compact scoreable pool
(27,658 rows). Produces REFUSAL_OUTCOMES.json, RESIDUAL_CHOICE_SET.json,
COST_BAND_CROSS.json, DECLINED_WINNERS.json.

Definitions:
- net  = opportunity_net_proxy_r (the pool's cost-true diagnostic outcome proxy)
- gross = net + cost_r
- winner = net > 0
- residual choice set def A ("survived every pre-scheduler gate"):
    broker_pretrade_cost_executable == True AND selector_action in
    {trade, open-reduced-risk, reduce-risk} (source-required is a hold, not a pass)
- residual choice set def B (what the scheduler literally ranked):
    scheduler_materialization_status == 'scheduler_option_materialized'
"""
import json, gzip, collections, math

POOL = ('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/'
        'fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz')
LANE = ('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/'
        'fable5-vision-audit-20260725/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl')
OUT = ('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/research/operations/'
       'wave19_broad_forensic_2026_08_01/funnel_jan/')

KEEP = ['selector_action', 'selector_reason', 'scheduler_materialization_status',
        'scheduler_selection_disposition', 'risk_finalizer_reason', 'final_blocker_class',
        'miss_reason', 'broker_pretrade_cost_executable', 'opportunity_net_proxy_r',
        'cost_r', 'spread_r', 'commission_r', 'swap_cost_r', 'expected_slippage_r',
        'origin_family', 'direction', 'route_session', 'session_bucket', 'symbol',
        'decision_time_utc', 'candidate_id', 'expected_net_r', 'candidate_ev_r',
        'candidate_probability', 'risk_finalizer_rank']
rows = []
with gzip.open(POOL, 'rt') as f:
    for line in f:
        d = json.loads(line)
        rows.append({k: d.get(k) for k in KEEP})

N = len(rows)


def stats(sub):
    n = len(sub)
    if n == 0:
        return {'n': 0}
    nets = [r['opportunity_net_proxy_r'] for r in sub]
    costs = [r['cost_r'] for r in sub]
    grosses = [a + b for a, b in zip(nets, costs)]
    pos = sum(1 for x in nets if x > 0)
    return {
        'n': n,
        'sum_net_r': round(sum(nets), 4),
        'mean_net_r': round(sum(nets) / n, 5),
        'mean_gross_r': round(sum(grosses) / n, 5),
        'sum_gross_r': round(sum(grosses), 4),
        'mean_cost_r': round(sum(costs) / n, 5),
        'positive_share': round(pos / n, 5),
        'n_positive': pos,
        'sum_positive_net_r': round(sum(x for x in nets if x > 0), 4),
        'sum_negative_net_r': round(sum(x for x in nets if x < 0), 4),
    }


def group_stats(sub, key):
    g = collections.defaultdict(list)
    for r in sub:
        g[str(r[key])].append(r)
    out = {k: stats(v) for k, v in g.items()}
    return dict(sorted(out.items(), key=lambda kv: -kv[1]['n']))


# ---------------- Task 2: refusal vs outcome ----------------
refusal = {
    'schema': 'gtos.session_fa.funnel_jan.refusal_outcomes.v1',
    'pool_rows': N,
    'pool_total': stats(rows),
    'by_selector_reason': group_stats(rows, 'selector_reason'),
    'by_final_blocker_class': group_stats(rows, 'final_blocker_class'),
    'by_scheduler_selection_disposition': group_stats(rows, 'scheduler_selection_disposition'),
    'by_risk_finalizer_reason': group_stats(rows, 'risk_finalizer_reason'),
    'by_selector_action': group_stats(rows, 'selector_action'),
    'note': ("'economically correct refusal' first pass = mean_net_r < 0 for the refused class; "
             "net is the pool's cost-true 2R-policy proxy (opportunity_net_proxy_r)."),
}
for section in ['by_selector_reason', 'by_final_blocker_class',
                'by_scheduler_selection_disposition', 'by_risk_finalizer_reason']:
    for k, v in refusal[section].items():
        if v['n']:
            v['refusal_economically_correct_on_average'] = bool(v['mean_net_r'] < 0)
json.dump(refusal, open(OUT + 'REFUSAL_OUTCOMES.json', 'w'), indent=1)

# ---------------- Task 3: residual choice set ----------------
PASS_ACTIONS = {'trade', 'open-reduced-risk', 'reduce-risk'}
resA = [r for r in rows if r['broker_pretrade_cost_executable'] is True
        and r['selector_action'] in PASS_ACTIONS]
resB = [r for r in rows if r['scheduler_materialization_status'] == 'scheduler_option_materialized']

# lane executed trades (the SELECTED side of the choice)
lane = [json.loads(l) for l in open(LANE)]
lane_meta, lane_trades = lane[0], lane[1:]
lt_nets = [t['net_r'] for t in lane_trades if t.get('net_r') is not None]
executed = {
    'n_trades': len(lane_trades),
    'n_with_net': len(lt_nets),
    'sum_net_r': round(sum(lt_nets), 4),
    'mean_net_r': round(sum(lt_nets) / len(lt_nets), 5),
    'n_positive': sum(1 for x in lt_nets if x > 0),
    'positive_share': round(sum(1 for x in lt_nets if x > 0) / len(lt_nets), 5),
    'max_cost_r': max((t.get('cost_r') or 0) for t in lane_trades),
    'n_cost_gt_1': sum(1 for t in lane_trades if (t.get('cost_r') or 0) > 1.0),
}


def composition(sub):
    tri = collections.Counter()
    for r in sub:
        tri[f"{r['origin_family']} || {r['direction']} || {r['route_session']}"] += 1
    return {
        'by_family': group_stats(sub, 'origin_family'),
        'by_direction': group_stats(sub, 'direction'),
        'by_route_session': group_stats(sub, 'route_session'),
        'by_symbol': group_stats(sub, 'symbol'),
        'family_x_direction_x_session_counts': dict(tri.most_common()),
    }


residual = {
    'schema': 'gtos.session_fa.funnel_jan.residual_choice_set.v1',
    'definitions': {
        'A': 'broker_pretrade_cost_executable==True AND selector_action in {trade, open-reduced-risk, reduce-risk}',
        'B': "scheduler_materialization_status == 'scheduler_option_materialized'",
    },
    'A': {
        'total': stats(resA),
        'composition': composition(resA),
        'by_scheduler_materialization': group_stats(resA, 'scheduler_materialization_status'),
        'by_scheduler_disposition': group_stats(resA, 'scheduler_selection_disposition'),
        'by_final_blocker_class': group_stats(resA, 'final_blocker_class'),
        'by_selector_action': group_stats(resA, 'selector_action'),
    },
    'B': {
        'total': stats(resB),
        'composition': composition(resB),
        'by_scheduler_disposition': group_stats(resB, 'scheduler_selection_disposition'),
        'by_final_blocker_class': group_stats(resB, 'final_blocker_class'),
        'by_risk_finalizer_reason': group_stats(resB, 'risk_finalizer_reason'),
    },
    'overlap': {
        'A_and_B': len([r for r in resA if r['scheduler_materialization_status'] == 'scheduler_option_materialized']),
        'A_not_B': len([r for r in resA if r['scheduler_materialization_status'] != 'scheduler_option_materialized']),
        'B_not_A': len([r for r in resB if not (r['broker_pretrade_cost_executable'] is True and r['selector_action'] in PASS_ACTIONS)]),
    },
    'selected_by_scheduler_and_executed': executed,
    'note': ('The missed pool contains only DECLINED rows; the SELECTED side of the choice set is the '
             '57 executed trades in the lane trade table. B\\A rows exist when the scheduler ranked a '
             'candidate whose selector action or cost flag was not a clean pass.'),
}
json.dump(residual, open(OUT + 'RESIDUAL_CHOICE_SET.json', 'w'), indent=1)

# ---------------- Task 4: cost band cross ----------------
band = [r for r in rows if r['cost_r'] is not None and r['cost_r'] > 1.0]
band_in_A = [r for r in band if r['broker_pretrade_cost_executable'] is True and r['selector_action'] in PASS_ACTIONS]
band_in_B = [r for r in band if r['scheduler_materialization_status'] == 'scheduler_option_materialized']
cost_cross = {
    'schema': 'gtos.session_fa.funnel_jan.cost_band_cross.v1',
    'band_definition': 'cost_r > 1.0 (round-trip cost exceeds 1R: stop narrower than cost)',
    'band_total': stats(band),
    'share_of_pool_net_loss': round(sum(r['opportunity_net_proxy_r'] for r in band) /
                                    sum(r['opportunity_net_proxy_r'] for r in rows), 5),
    'by_final_blocker_class': group_stats(band, 'final_blocker_class'),
    'by_selector_reason': group_stats(band, 'selector_reason'),
    'by_broker_pretrade_cost_executable': group_stats(band, 'broker_pretrade_cost_executable'),
    'leaked_into_residual_A': stats(band_in_A),
    'leaked_into_residual_A_detail': {
        'by_selector_reason': group_stats(band_in_A, 'selector_reason'),
        'by_final_blocker_class': group_stats(band_in_A, 'final_blocker_class'),
        'by_symbol': group_stats(band_in_A, 'symbol'),
    },
    'leaked_into_scheduler_ranked_B': stats(band_in_B),
    'executed_trades_from_band': {
        'n_cost_gt_1': executed['n_cost_gt_1'],
        'max_executed_cost_r': executed['max_cost_r'],
        'verdict': 'no executed trade came from the cost>1R band' if executed['n_cost_gt_1'] == 0 else 'LEAK',
    },
}
json.dump(cost_cross, open(OUT + 'COST_BAND_CROSS.json', 'w'), indent=1)

# ---------------- Task 6: declined winners ----------------
winners = [r for r in rows if r['opportunity_net_proxy_r'] > 0]
winners_sorted = sorted(rows, key=lambda r: -r['opportunity_net_proxy_r'])
top_decile = winners_sorted[: N // 10]

NY_METALS_LONG = [r for r in rows if r['symbol'] in ('XAUUSD', 'XAGUSD')
                  and r['direction'] == 'LONG' and (r['route_session'] == 'ny' or r['session_bucket'] == 'ny')]
LSR_LONG = [r for r in rows if r['origin_family'] == 'liquidity_sweep_reclaim' and r['direction'] == 'LONG']


def funnel_of(sub):
    return {
        'total': stats(sub),
        'by_final_blocker_class': group_stats(sub, 'final_blocker_class'),
        'by_selector_reason': group_stats(sub, 'selector_reason'),
        'by_selector_action': group_stats(sub, 'selector_action'),
        'by_scheduler_disposition': group_stats(sub, 'scheduler_selection_disposition'),
        'by_risk_finalizer_reason': group_stats(sub, 'risk_finalizer_reason'),
        'reached_residual_A': stats([r for r in sub if r['broker_pretrade_cost_executable'] is True
                                     and r['selector_action'] in PASS_ACTIONS]),
        'reached_scheduler_ranked_B': stats([r for r in sub if r['scheduler_materialization_status']
                                             == 'scheduler_option_materialized']),
    }


dw = {
    'schema': 'gtos.session_fa.funnel_jan.declined_winners.v1',
    'winner_definition': 'scoreable row with opportunity_net_proxy_r > 0',
    'all_winners': funnel_of(winners),
    'top_decile_by_net_proxy': {
        'n': len(top_decile),
        'min_net_r_in_decile': round(top_decile[-1]['opportunity_net_proxy_r'], 5),
        **funnel_of(top_decile),
    },
    'class_a_ny_metals_long': {
        'definition': "symbol in {XAUUSD, XAGUSD} AND direction LONG AND (route_session=='ny' OR session_bucket=='ny')",
        **funnel_of(NY_METALS_LONG),
        'winners_within': funnel_of([r for r in NY_METALS_LONG if r['opportunity_net_proxy_r'] > 0]),
    },
    'class_b_liquidity_sweep_reclaim_long': {
        'definition': "origin_family=='liquidity_sweep_reclaim' AND direction LONG",
        **funnel_of(LSR_LONG),
        'winners_within': funnel_of([r for r in LSR_LONG if r['opportunity_net_proxy_r'] > 0]),
    },
}
json.dump(dw, open(OUT + 'DECLINED_WINNERS.json', 'w'), indent=1)

# ---------------- cross-checks ----------------
xc = {
    'pool_rows': N, 'expect': 27658,
    'sum_net': round(sum(r['opportunity_net_proxy_r'] for r in rows), 4), 'expect_sum_net': -24357.199,
    'mean_net': round(sum(r['opportunity_net_proxy_r'] for r in rows) / N, 6), 'expect_mean_net': -0.88066,
    'mean_gross': round(sum(r['opportunity_net_proxy_r'] + r['cost_r'] for r in rows) / N, 6), 'expect_mean_gross': -0.21750,
    'mean_cost': round(sum(r['cost_r'] for r in rows) / N, 6), 'expect_mean_cost': 0.66316,
    'n_positive': sum(1 for r in rows if r['opportunity_net_proxy_r'] > 0), 'expect_positive': 7706,
    'cost_gt1_rows': len(band), 'expect_band_rows': 4908,
    'exec_true': sum(1 for r in rows if r['broker_pretrade_cost_executable'] is True), 'expect_true': 7210,
    'lane_trades': len(lane_trades), 'expect_trades': 57,
    'lane_sum_net': round(sum(lt_nets), 4), 'expect_lane_net': -5.506,
}
print(json.dumps(xc, indent=1))
