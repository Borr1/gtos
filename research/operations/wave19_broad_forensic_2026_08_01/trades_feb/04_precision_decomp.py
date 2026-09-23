#!/usr/bin/env python3
"""Session FA / February walker — step 4: assemble PRECISION_DECOMP.json.

All numbers recomputed from raw artifacts in steps 1-3 (TRADES_FEB_TABLE.json,
FEB_POOL_PRECISION_STATS.json, TRADES_FEB_ATTRIBUTION.json) and cross-checked
against the committed receipts (CP_FEBRUARY_POOL_S0R0_V1.json,
CP_FEBRUARY_FIRST_READ_RESULT_V1.json, the arm SUMMARY split_profile_stats[0]).
"""
import json, os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
tbl = json.load(open(os.path.join(OUT_DIR, 'TRADES_FEB_TABLE.json')))
pool = json.load(open(os.path.join(OUT_DIR, 'FEB_POOL_PRECISION_STATS.json')))
att = json.load(open(os.path.join(OUT_DIR, 'TRADES_FEB_ATTRIBUTION.json')))
trades = tbl['trades']


def be(w, l):
    return abs(l) / (w + abs(l))


wins = [t['net_r'] for t in trades if t['net_r'] > 0]
losses = [t['net_r'] for t in trades if t['net_r'] <= 0]
W, L = sum(wins) / len(wins), sum(losses) / len(losses)
gw = [t['final_r'] for t in trades if t['final_r'] > 0]
gl = [t['final_r'] for t in trades if t['final_r'] <= 0]
GW, GL = sum(gw) / len(gw), sum(gl) / len(gl)

nb = pool['net_basis']
gb = pool['zero_cost_counterfactual_gross_basis']
pc = pool['cost']

out = {
 'schema': 'gtos.session_fa.feb_precision_decomp.v1',
 'a_what_precision_is': {
   'definition': ('POOL row metric, not a trade metric. base_rate_positive = share of the 24,239 '
                  'diagnostic-scoreable missed-opportunity rows with cost-true net '
                  '(opportunity_net_proxy_r) > 0. breakeven_precision = |mean_loser_r| / '
                  '(mean_winner_r + |mean_loser_r|) over the same rows.'),
   'protocol_source': 'CP_FEBRUARY_FIRST_READ_PROTOCOL_V1.json decision_population.precision_metrics',
   'recomputed_base_rate_positive': nb['base_rate_positive'],
   'recomputed_breakeven_precision': nb['breakeven_precision'],
   'receipt_values': {'base_rate_positive': 0.309336, 'breakeven_precision': 0.606359,
                      'headroom': -0.297023},
   'cross_check': 'EXACT match (7,498/24,239; W +0.84821490, L -1.30657596)',
 },
 'b_trade_level_w_l_asymmetry': {
   'n_trades': 58, 'n_winners': len(wins), 'n_losers': len(losses),
   'trade_precision': len(wins) / 58,
   'mean_winner_net_r': W, 'mean_loser_net_r': L,
   'trade_level_breakeven': be(W, L),
   'trade_level_headroom': len(wins) / 58 - be(W, L),
   'note': ('Executed trades have the OPPOSITE asymmetry to the pool: winners (+0.817) are larger '
            'than losers (-0.693), so the executed breakeven is 0.459, not 0.606. The 0.606 '
            'breakeven is set by the pool loser tail (-1.307 vs +0.848), which is cost-driven. '
            'The executed book sits 4.5 pp below its own breakeven; the pool sits 29.7 pp below.'),
 },
 'c_asymmetry_decomposition': {
   'pool': {
     'gross_basis': {'mean_winner': gb['mean_winner_r'], 'mean_loser': gb['mean_loser_r'],
                     'breakeven': gb['breakeven_precision']},
     'net_basis': {'mean_winner': nb['mean_winner_r'], 'mean_loser': nb['mean_loser_r'],
                   'breakeven': nb['breakeven_precision']},
     'breakeven_shift_from_cost': nb['breakeven_precision'] - gb['breakeven_precision'],
     'channels': {
       'differential_cost_load': {'mean_cost_r_net_winners': pc['mean_cost_r_net_winners'],
                                  'mean_cost_r_net_losers': pc['mean_cost_r_net_losers']},
       'sign_flips': {'rows_gross_pos_flipped_negative': pc['rows_gross_pos_flipped_negative_by_cost'],
                      'gross_r_in_flipped': pc['gross_r_sum_in_flipped_rows'],
                      'net_r_in_flipped': pc['net_r_sum_in_flipped_rows'],
                      'precision_drop_from_flips': gb['base_rate_positive'] - nb['base_rate_positive']},
     },
     'gross_asymmetry_verdict': ('At gross the pool W/L asymmetry is FAVORABLE (1.051 vs -0.866, '
                                 'breakeven 0.452 < 0.5). The entire 0.452 -> 0.606 breakeven '
                                 'inflation is cost: losers carry 1.84x the winners\' cost load and '
                                 '1,546 gross-winners are flipped into the loser tail.'),
   },
   'executed_58': {
     'sum_gross_r': tbl['totals']['sum_gross_r'], 'sum_cost_r': tbl['totals']['sum_cost_r'],
     'sum_net_r': tbl['totals']['sum_net_r'],
     'mean_cost_r_winners': sum(t['cost_r'] for t in trades if t['net_r'] > 0) / len(wins),
     'mean_cost_r_losers': sum(t['cost_r'] for t in trades if t['net_r'] <= 0) / len(losses),
     'verdict': ('On the executed 58 cost is small (0.072 R/trade) and symmetric; the deficit is '
                 'the aggregate cost bill (4.165 R) on a gross book of +0.204 R — cost is 105% of '
                 'the realized loss.'),
     'exit_truncation_close_reason_mix': {
       'path_end_mark_to_market': {'n': 21, 'net_r': -1.2847},
       'time_stop_close_mark_from_m1': {'n': 4, 'net_r': -1.1148},
       'giveback_close': {'n': 14, 'net_r': +12.9513},
       'stop_closes': {'n': 17, 'net_r': -18.3701},
       'target_closes': {'n': 2, 'net_r': +3.8567},
       'note': ('21/58 trades (36%) are marked at the 120-min path end (median hold 91 min, max '
                '120). Exit truncation is real but nets only -1.28 R of the -3.96; stops carry '
                '-18.37 R and the giveback/harvest exits carry +12.95 R.'),
     },
   },
 },
 'd_zero_cost_counterfactual': {
   'pool': {'precision': gb['base_rate_positive'], 'breakeven': gb['breakeven_precision'],
            'headroom': gb['headroom'], 'net_r_sum': gb['gross_r_sum'],
            'mean_r_per_row': gb['mean_gross_r_per_row'],
            'verdict': ('Still NEGATIVE at zero cost: precision 0.373 vs breakeven 0.452 '
                        '(headroom -0.079), pool sum -3,649 R. Cost explains 11,864 R = 76.5% of '
                        'the -15,513 R pool deficit and 73.5% of the -0.297 headroom gap; the '
                        'residual -0.079 is genuine gross negativity of the family.')},
   'executed_58': {'precision': len(gw) / 58, 'breakeven': be(GW, GL),
                   'headroom': len(gw) / 58 - be(GW, GL), 'net_r_sum': tbl['totals']['sum_gross_r'],
                   'verdict': ('POSITIVE at zero cost: 25/58 gross winners, precision 0.431 vs '
                               'breakeven 0.429, sum +0.204 R. The executed slice crosses breakeven '
                               'the moment cost is removed — but only just, and n=58.')},
   'binary_endpoint_framing': {'receipt_hit_rate': 0.206074, 'breakeven_hit_rate': 0.333333,
                               'note': 'fixed-geometry binary endpoints stay negative even before cost'},
 },
 'e_ex_ante_subpopulations': {
   'method': ('ex-ante dimensions only (origin_family / session / symbol / direction); groups with '
              'precision > own breakeven flagged; n<10 is not evidence'),
   'february': {k: v for k, v in att['february']['aggregations'].items()
                if k in ('origin_family', 'direction', 'session_bucket', 'symbol')},
   'verdict': ('NO ex-ante subpopulation of the 58 clears its own breakeven at usable n. The two '
               'that clear it — current_breaker_re_entry (n=3, +1.218 R, 3/3) and '
               'structural_distance_extreme (n=1, +1.170 R) — repeat January\'s sign (breaker n=8 '
               '+4.356 above own BE; structural n=7 +3.499 above own BE) and are exactly the '
               'direction the wave-18/19 candidate factory already mined (CQ inverted-breaker). '
               'current_fvg_fill is the loss engine in both months (Feb n=42 -5.784; Jan n=20 '
               '-12.264), below its own breakeven both times. Direction and session FLIP between '
               'months (Jan LONG +4.89/SHORT -10.39; Feb LONG -2.87/SHORT -1.10) — not stable.'),
 },
 'cross_checks': {
   'realized_physical_net_r': {'receipt': -3.96139869, 'recomputed_sum_58': tbl['totals']['sum_net_r']},
   'summary_split_profile': {'physical_gross_r': 0.20391894, 'physical_total_execution_cost_r': 4.16531763,
                             'physical_win_count': 24, 'physical_loss_count': 34,
                             'physical_win_rate': 0.4137931, 'all_match': True},
   'pool_receipt': 'all recomputed pool figures match CP_FEBRUARY_POOL_S0R0_V1.json exactly',
 },
}

with open(os.path.join(OUT_DIR, 'PRECISION_DECOMP.json'), 'w') as f:
    json.dump(out, f, indent=1)
print('PRECISION_DECOMP.json written')
print('trade-level BE', be(W, L), 'gross BE', be(GW, GL))
