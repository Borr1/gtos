"""LANE I Part 1.1 — the perfect-foresight oracle band."""
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/lane_i")
import protocol as P

OUT = Path("/tmp/lane_i")
df = pd.read_parquet(OUT / "pop.parquet")
MONTHS = ["feb", "apr", "may", "jun", "jul"]
rng = np.random.default_rng(20260811)
report = {"schema": "gtos.lane_i.oracle_band.v1", "months": {}}
t0 = time.time()

for m in MONTHS:
    d = df[(df.month == m) & df.eligible].reset_index(drop=True)
    arrays = {
        'symbol': d['symbol'].astype(str).to_numpy(),
        'end': d['label_span_end_utc'].fillna(d['expiry_utc']).to_numpy(),
        'cost_r': d['cost_r'].to_numpy(float),
        'key': d['candidate_occurrence_key'].astype(str).to_numpy(),
        'is_market': (d['proposed_order_type'].astype(str) == 'MARKET').to_numpy(),
        'resolved': d['resolved'].to_numpy(bool),
        # frozen rule scores a null terminal_net_r as exactly 0.0
        # (w21_score_feb_market_top_r2.py:268 `float(row.get("terminal_net_r") or 0.0)`);
        # RESOLVED_NO_FILL is a real, resolved, zero-value outcome.
        'net_r': np.nan_to_num(d['terminal_net_r'].to_numpy(float), nan=0.0),
        'filled': d['lifecycle_label_status'].astype(str).str.startswith('RESOLVED_FILLED').to_numpy(),
        'deductible_cost_r': d['deductible_cost_r'].to_numpy(float),
    }
    windows = P.build_windows(d)
    res = arrays['resolved']; fil = arrays['filled']
    net = np.where(res, arrays['net_r'], np.nan)

    # ---- pool dispersion over FILLED rows (the AW / JANUARY_BANK framing) --
    rn = arrays['net_r'][fil]
    pool = {"resolved_rows": int(res.sum()), "filled_rows": int(fil.sum()),
            "no_fill_rows": int((res & ~fil).sum()), "censored_rows": int((~res).sum()),
            "positive_rows": int((rn > 0).sum()), "negative_rows": int((rn < 0).sum()),
            "zero_rows": int((rn == 0).sum()),
            "positive_sum_r": round(float(rn[rn > 0].sum()), 2),
            "negative_sum_r": round(float(rn[rn < 0].sum()), 2),
            "abs_dispersion_r": round(float(np.abs(rn).sum()), 2),
            "pool_mean_r_per_fill": round(float(rn.mean()), 6),
            "pool_net_sum_r": round(float(rn.sum()), 2)}

    # ---- per-window ceiling, ignoring the concurrency constraint ----------
    wid = d['decision_window_id'].astype(str).to_numpy()
    g = pd.DataFrame({"w": wid, "net": net}).dropna().groupby("w")["net"]
    wmax, wmin, wmean = g.max(), g.min(), g.mean()
    unconstrained = {
        "windows_with_resolved_candidate": int(len(wmax)),
        "sum_of_window_max_r": round(float(wmax.sum()), 2),
        "sum_of_window_max_positive_only_r": round(float(wmax[wmax > 0].sum()), 2),
        "windows_with_a_positive_candidate": int((wmax > 0).sum()),
        "sum_of_window_min_r": round(float(wmin.sum()), 2),
        "sum_of_window_mean_r": round(float(wmean.sum()), 2),
    }

    # ---- protocol-constrained oracle band --------------------------------
    band = {}
    for name, sc, thr, mask, pol in [
        ("oracle_best_mixed",     np.where(res, arrays['net_r'], P.NEG), 0.0,  res, "mixed"),
        ("oracle_best_market",    np.where(res, arrays['net_r'], P.NEG), 0.0,  res, "market_rerank"),
        ("oracle_best_frozenpol", np.where(res, arrays['net_r'], P.NEG), 0.0,  res, "market_top_abstain"),
        ("oracle_worst_mixed",    np.where(res, -arrays['net_r'], P.NEG), 0.0, res, "mixed"),
        ("oracle_must_trade_mixed", np.where(res, arrays['net_r'], P.NEG), -1e17, res, "mixed"),
        ("oracle_best_filled_only", np.where(fil, arrays['net_r'], P.NEG), 0.0, fil, "mixed"),
        ("oracle_worst_filled_only", np.where(fil, -arrays['net_r'], P.NEG), 0.0, fil, "mixed"),
    ]:
        out = P.run(windows, arrays, sc, policy=pol, threshold=thr, available_mask=mask)
        book = P.score_book(out['selected'], arrays)
        band[name] = {**book, "dispositions": out['dispositions']}

    # ---- random-selection null (same protocol, must trade) ---------------
    draws = []
    for b in range(200):
        sc = np.where(res, rng.random(len(d)), P.NEG)
        out = P.run(windows, arrays, sc, policy="mixed", threshold=-1e17, available_mask=res)
        draws.append(P.score_book(out['selected'], arrays)['net_r'])
    draws = np.asarray(draws)
    band['random_mixed_must_trade'] = {
        "draws": 200, "mean_net_r": round(float(draws.mean()), 3),
        "sd_net_r": round(float(draws.std(ddof=1)), 3),
        "p05_net_r": round(float(np.percentile(draws, 5)), 3),
        "p95_net_r": round(float(np.percentile(draws, 95)), 3)}

    # ---- frozen-rule replica on the month-boundary ridge ----------------
    pred = d['pred_month_boundary'].to_numpy(float)
    for name, pol in [("frozen_replica_market_top_abstain", "market_top_abstain"),
                      ("frozen_replica_mixed", "mixed"),
                      ("frozen_replica_market_rerank", "market_rerank")]:
        out = P.run(windows, arrays, pred, policy=pol, threshold=P.MIN_EXPECTED_NET_R)
        band[name] = {**P.score_book(out['selected'], arrays), "dispositions": out['dispositions']}

    report["months"][m] = {"eligible_rows": int(len(d)), "windows": len(windows),
                           "pool": pool, "unconstrained_window_ceiling": unconstrained,
                           "protocol_band": band}
    print(json.dumps({"month": m, "t": round(time.time()-t0, 1),
                      "oracle_mixed": band['oracle_best_mixed']['net_r'],
                      "oracle_worst": band['oracle_worst_mixed']['net_r'],
                      "random": band['random_mixed_must_trade']['mean_net_r'],
                      "frozen": band['frozen_replica_market_top_abstain']['worst_case_net_r']}), flush=True)

(OUT / "PART1_ORACLE_BAND.json").write_text(json.dumps(report, indent=1, sort_keys=True))
print("DONE", round(time.time()-t0, 1))
