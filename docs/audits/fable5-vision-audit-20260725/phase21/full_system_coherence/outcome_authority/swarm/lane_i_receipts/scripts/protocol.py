"""LANE I: the frozen selection protocol, reimplemented verbatim from
w21_score_feb_market_top_r2.py::select (lines 236-262) with a parameterised score.

Verbatim reference (the frozen rule, market_top_abstain):
  - group by decision_window_id
  - order windows by (min label_span_start_utc, decision_window_id)
  - drop active symbols whose label span has ended
  - available = candidates whose symbol is not active (+ policy order-type filter)
  - key = max by (score, -cost_r, occurrence_key)
  - abstain if score < MIN_EXPECTED_NET_R (0.10)
  - abstain if policy==market_top_abstain and top pick is not MARKET
  - active[symbol] = label_span_end_utc or expiry_utc
"""
from collections import defaultdict
import numpy as np

MIN_EXPECTED_NET_R = 0.10
NEG = -1e18


def build_windows(df):
    """Pre-group eligible rows into the frozen window ordering. Returns list of
    (decision_at, [row_index,...]) in the frozen order."""
    by_window = defaultdict(list)
    wid = df['decision_window_id'].to_numpy()
    start = df['label_span_start_utc'].to_numpy()
    for i in range(len(df)):
        by_window[wid[i]].append(i)
    ordered = sorted(by_window.items(), key=lambda kv: (min(start[i] for i in kv[1]), kv[0]))
    return [(min(start[i] for i in idx), idx) for _key, idx in ordered]


def run(windows, arrays, score, *, policy="market_top_abstain", threshold=MIN_EXPECTED_NET_R,
        available_mask=None):
    """Run the protocol. `score` is a float array aligned to arrays['symbol'].
    `available_mask` (bool array) can remove rows from availability entirely
    (e.g. the oracle may not pick a censored row, whose outcome does not exist).
    Returns dict with selected indices and dispositions."""
    sym = arrays['symbol']; end = arrays['end']; cost = arrays['cost_r']
    key = arrays['key']; otype = arrays['is_market']
    active_sym = {}
    selected = []
    disp = defaultdict(int)
    for decision_at, idx in windows:
        for s in [s for s, e in active_sym.items() if e <= decision_at]:
            del active_sym[s]
        best = None
        for i in idx:
            if sym[i] in active_sym:
                continue
            if available_mask is not None and not available_mask[i]:
                continue
            if policy == "market_rerank" and not otype[i]:
                continue
            cand = (score[i], -cost[i], key[i], i)
            if best is None or cand[:3] > best[:3]:
                best = cand
        if best is None:
            disp['no_available_candidate'] += 1
            continue
        if best[0] < threshold:
            disp['top_below_threshold'] += 1
            continue
        if policy == "market_top_abstain" and not otype[best[3]]:
            disp['top_limit_abstain'] += 1
            continue
        disp['trade'] += 1
        i = best[3]
        selected.append(i)
        active_sym[sym[i]] = end[i]
    return {"selected": np.asarray(selected, dtype=np.int64), "dispositions": dict(sorted(disp.items()))}


def score_book(sel, arrays):
    """Portfolio arithmetic in the frozen rule's own accounting."""
    if len(sel) == 0:
        return {"selected": 0, "resolved": 0, "censored": 0, "net_r": 0.0,
                "worst_case_net_r": 0.0, "mean_resolved_net_r": None}
    res = arrays['resolved'][sel]
    net = arrays['net_r'][sel]
    dcost = arrays['deductible_cost_r'][sel]
    actual = float(np.nansum(np.where(res, net, 0.0)))
    worst = actual + float(np.sum(np.where(~res, -1.0 - dcost, 0.0)))
    nres = int(res.sum())
    return {"selected": int(len(sel)), "resolved": nres, "censored": int((~res).sum()),
            "net_r": round(actual, 4), "worst_case_net_r": round(worst, 4),
            "mean_resolved_net_r": round(actual / nres, 6) if nres else None}
