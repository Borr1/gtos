#!/usr/bin/env python3
"""Session FA / wave-19 forensic — extras: cost components, first-touch,
headline-vs-physical split, holding stats. Amends TRADES_JAN_ATTRIBUTION.json
under key 'extras'."""
import json, os, collections, statistics

OUT = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(OUT, 'TRADES_JAN_TABLE.json')))
ts = d['trades']
a = json.load(open(os.path.join(OUT, 'TRADES_JAN_ATTRIBUTION.json')))

def s(key, sub=None):
    tot = 0.0
    for t in ts:
        v = t.get(key)
        if sub and isinstance(v, dict):
            v = v.get(sub)
        if isinstance(v, (int, float)):
            tot += v
    return round(tot, 6)

cost_components = {
    'spread_r_sum': s('spread_r'),
    'commission_r_sum': s('commission_r'),
    'swap_cost_r_sum': s('swap_cost_r'),
    'expected_slippage_r_sum': s('expected_slippage_r'),
    'cost_r_sum': s('cost_r'),
    'guarded_market_fallback_extra_cost_r_sum': s('guarded_market_fallback_extra_cost_r'),
    'fallback_execution_surcharge_r_sum': s('fallback_execution_surcharge_r'),
}

ft = collections.Counter(t['first_touch_within_horizon'] for t in ts)
holds = [t['holding_minutes'] for t in ts if isinstance(t['holding_minutes'], (int, float))]
hold_stats = {'n': len(holds), 'min': min(holds), 'median': statistics.median(holds),
              'mean': round(statistics.mean(holds), 2), 'max': max(holds)}

headline = [t for t in ts if t['headline_result_exclusion_reason'] == 'headline_result_eligible']
proxy = [t for t in ts if t['headline_result_exclusion_reason'] != 'headline_result_eligible'
         and isinstance(t['net_r'], (int, float))]
split = {
    'headline_39_net_r': round(sum(t['net_r'] for t in headline), 8),
    'diagnostic_only_18_scoreable_net_r': round(sum(t['net_r'] for t in proxy), 8),
    'unscoreable_2_cost_r_charged_outside_net': round(sum(
        t['cost_r'] for t in ts if not isinstance(t['net_r'], (int, float))), 8),
}

mfes = [t['mfe_r'] for t in ts if isinstance(t['mfe_r'], (int, float))]
maes = [t['mae_r'] for t in ts if isinstance(t['mae_r'], (int, float))]
path_stats = {
    'mfe_median': round(statistics.median(mfes), 4), 'mfe_mean': round(statistics.mean(mfes), 4),
    'mae_median': round(statistics.median(maes), 4), 'mae_mean': round(statistics.mean(maes), 4),
    'n_mfe_ge_0p5': sum(1 for m in mfes if m >= 0.5),
    'n_mfe_ge_1': sum(1 for m in mfes if m >= 1.0),
    'sum_best_available_exit_r_net': round(sum(
        t['best_available_exit_r_net'] for t in ts
        if isinstance(t.get('best_available_exit_r_net'), (int, float))), 4),
    'giveback_mfe_to_gross_on_exit_geometry_class': round(sum(
        t['mfe_r'] - t['gross_r'] for t in ts
        if isinstance(t['net_r'], (int, float)) and t['net_r'] < 0
        and isinstance(t['mfe_r'], (int, float)) and t['mfe_r'] >= 0.5), 4),
}

a['extras'] = {
    'cost_components': cost_components,
    'first_touch_within_horizon_counts': dict(ft),
    'holding_minutes_stats': hold_stats,
    'headline_vs_physical_split': split,
    'path_stats': path_stats,
}
with open(os.path.join(OUT, 'TRADES_JAN_ATTRIBUTION.json'), 'w') as f:
    json.dump(a, f, indent=1, default=str)
print(json.dumps(a['extras'], indent=1))
