"""LANE I Part 1.3 — capture ratio of the actual frozen rule.

The frozen rule's realized figures come from the COMMITTED validation results
(daily prequential refit, market_top_abstain), not from the month-boundary
replica.  The null is matched-count: draw the same number of trades at random
from the same month's eligible / resolved / FILLED / MARKET-order pool -- the
exact pool the market_top_abstain policy draws from (its outcome mixes contain
no NO_FILL rows: every selected trade is STOP / TARGET / TIME_STOP / CENSORED).
"""
import json
from pathlib import Path
import numpy as np, pandas as pd

OUT = Path("/tmp/lane_i")
SEED = 20260811
NDRAW = 20000

# committed frozen-rule realized figures, market_top_abstain
FROZEN = {  # month: (selected, resolved, actual_net_r, worst_case_net_r, source)
 "feb": (106, 105, 14.168399, 13.144092, "FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json::pooled"),
 "apr": (50, 49, -7.742114, -8.815477, "APRIL_MAY_..._RESULT_V1.json::per_month.april_2026"),
 "may": (17, 17, 5.130257, 5.130257, "APRIL_MAY_..._RESULT_V1.json::per_month.may_2026"),
 "jun": (49, 45, 3.963843, -0.116157, "JUNE_JULY_..._RESULT_V1.json::per_month.june_2026"),
 "jul": (68, 66, -14.566020, -16.606020, "JUNE_JULY_..._RESULT_V1.json::per_month.july_2026"),
}

df = pd.read_parquet(OUT / "pop.parquet")
band = json.loads((OUT / "PART1_ORACLE_BAND.json").read_text())
rng = np.random.default_rng(SEED)
rows = {}
for m, (nsel, nres, actual, worst, src) in FROZEN.items():
    d = df[(df.month == m) & df.eligible & df.resolved].copy()
    d = d[d['lifecycle_label_status'].astype(str).str.startswith('RESOLVED_FILLED')]
    pool_all = d['terminal_net_r'].to_numpy(float)
    pool_mkt = d[d['proposed_order_type'].astype(str) == 'MARKET']['terminal_net_r'].to_numpy(float)
    out = {"frozen_selected": nsel, "frozen_resolved": nres,
           "frozen_actual_net_r": actual, "frozen_worst_case_net_r": worst, "source": src}
    for tag, pool in [("market_only", pool_mkt), ("all_filled", pool_all)]:
        draws = rng.choice(pool, size=(NDRAW, nres), replace=True).sum(axis=1)
        out[tag] = {
            "pool_n": int(len(pool)), "pool_mean_r": round(float(pool.mean()), 5),
            "null_mean_sum_r": round(float(draws.mean()), 3),
            "null_sd_sum_r": round(float(draws.std(ddof=1)), 3),
            "null_p05": round(float(np.percentile(draws, 5)), 3),
            "null_p50": round(float(np.percentile(draws, 50)), 3),
            "null_p95": round(float(np.percentile(draws, 95)), 3),
            "frozen_percentile_in_null": round(float((draws < actual).mean()), 4),
            "frozen_z_vs_null": round(float((actual - draws.mean()) / draws.std(ddof=1)), 3),
        }
    b = band['months'][m]['protocol_band']
    out['ceilings'] = {
        "perfect_foresight_frozen_policy_r": b['oracle_best_frozenpol']['net_r'],
        "perfect_foresight_frozen_policy_trades": b['oracle_best_frozenpol']['selected'],
        "perfect_foresight_mixed_r": b['oracle_best_mixed']['net_r'],
        "capture_vs_perfect_foresight_frozen_policy": round(actual / b['oracle_best_frozenpol']['net_r'], 6),
    }
    rows[m] = out
    print(json.dumps({"month": m, "frozen": actual,
                      "null_mean": out['market_only']['null_mean_sum_r'],
                      "null_sd": out['market_only']['null_sd_sum_r'],
                      "z": out['market_only']['frozen_z_vs_null'],
                      "pct": out['market_only']['frozen_percentile_in_null']}), flush=True)

tot_actual = sum(v['frozen_actual_net_r'] for v in rows.values())
tot_worst = sum(v['frozen_worst_case_net_r'] for v in rows.values())
tot_ceiling = sum(v['ceilings']['perfect_foresight_frozen_policy_r'] for v in rows.values())
tot_z = sum(v['market_only']['frozen_actual_net_r'] if False else 0 for v in rows.values())
pooled_null_mean = sum(v['market_only']['null_mean_sum_r'] for v in rows.values())
pooled_null_sd = float(np.sqrt(sum(v['market_only']['null_sd_sum_r'] ** 2 for v in rows.values())))
report = {"schema": "gtos.lane_i.capture_ratio.v1", "seed": SEED, "draws": NDRAW,
          "months": rows,
          "pooled": {"frozen_actual_net_r": round(tot_actual, 4),
                     "frozen_worst_case_net_r": round(tot_worst, 4),
                     "perfect_foresight_frozen_policy_r": round(tot_ceiling, 2),
                     "capture_vs_perfect_foresight": round(tot_actual / tot_ceiling, 6),
                     "matched_count_null_mean_r": round(pooled_null_mean, 3),
                     "matched_count_null_sd_r": round(pooled_null_sd, 3),
                     "frozen_z_vs_matched_null": round((tot_actual - pooled_null_mean) / pooled_null_sd, 3)}}
(OUT / "PART1_CAPTURE_RATIO.json").write_text(json.dumps(report, indent=1, sort_keys=True))
print(json.dumps(report['pooled'], indent=1))
