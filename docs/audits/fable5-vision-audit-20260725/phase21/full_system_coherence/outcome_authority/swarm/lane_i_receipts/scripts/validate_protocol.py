"""LANE I receipt: prove protocol.run is byte-equivalent to the frozen select().

The reference below is copied VERBATIM from
w21_score_feb_market_top_r2.py::select (the committed February r2 scorer, which
r3b/r4d load byte-identically), with only `r.m.MIN_EXPECTED_NET_R` inlined as
the literal 0.10 it resolves to (candidate_funnel_analysis.py:53).
"""
import json, sys
from collections import defaultdict, Counter
from datetime import datetime
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/lane_i")
import protocol as P

MIN_EXPECTED_NET_R = 0.10


def at(value):
    return value  # already numpy datetime64 in this harness; ordering identical


def select_reference(rows, predictions, *, policy):
    by_window = defaultdict(list)
    for row, prediction in zip(rows, predictions):
        by_window[row["decision_window_id"]].append((float(prediction), row))
    ordered = sorted(
        by_window.values(),
        key=lambda values: (
            min(at(row["label_span_start_utc"]) for _, row in values),
            values[0][1]["decision_window_id"],
        ),
    )
    active, selected, dispositions = {}, [], Counter()
    for candidates in ordered:
        decision_at = min(at(row["label_span_start_utc"]) for _, row in candidates)
        active = {symbol: end for symbol, end in active.items() if end > decision_at}
        available = [
            (prediction, -float(row["cost_r"]), row["candidate_occurrence_key"], row)
            for prediction, row in candidates
            if row["symbol"] not in active
            and (policy != "market_rerank" or row["proposed_order_type"] == "MARKET")
        ]
        if not available:
            dispositions["no_available_candidate"] += 1
            continue
        prediction, _neg_cost, _key, row = max(available, key=lambda item: item[:3])
        if prediction < MIN_EXPECTED_NET_R:
            dispositions["top_below_0p10"] += 1
            continue
        if policy == "market_top_abstain" and row["proposed_order_type"] != "MARKET":
            dispositions["top_limit_abstain"] += 1
            continue
        dispositions["trade"] += 1
        selected.append(row["_i"])
        active[row["symbol"]] = at(row["label_span_end_utc"] or row["expiry_utc"])
    return selected, dict(sorted(dispositions.items()))


df = pd.read_parquet("/tmp/lane_i/pop.parquet")
out = {}
for m in ["feb", "apr", "may", "jun", "jul"]:
    d = df[(df.month == m) & df.eligible].reset_index(drop=True)
    end = d['label_span_end_utc'].fillna(d['expiry_utc'])
    rows = [{"_i": i,
             "decision_window_id": w, "label_span_start_utc": s, "label_span_end_utc": e,
             "expiry_utc": x, "symbol": sy, "cost_r": c,
             "candidate_occurrence_key": k, "proposed_order_type": o}
            for i, (w, s, e, x, sy, c, k, o) in enumerate(zip(
                d['decision_window_id'].astype(str), d['label_span_start_utc'],
                end, d['expiry_utc'], d['symbol'].astype(str), d['cost_r'].astype(float),
                d['candidate_occurrence_key'].astype(str), d['proposed_order_type'].astype(str)))]
    arrays = {'symbol': d['symbol'].astype(str).to_numpy(), 'end': end.to_numpy(),
              'cost_r': d['cost_r'].to_numpy(float),
              'key': d['candidate_occurrence_key'].astype(str).to_numpy(),
              'is_market': (d['proposed_order_type'].astype(str) == 'MARKET').to_numpy()}
    windows = P.build_windows(d)
    pred = d['pred_month_boundary'].to_numpy(float)
    month_out = {}
    for policy in ("market_top_abstain", "mixed", "market_rerank"):
        ref_sel, ref_disp = select_reference(rows, pred, policy=policy)
        mine = P.run(windows, arrays, pred, policy=policy, threshold=MIN_EXPECTED_NET_R)
        same = list(mine['selected']) == list(ref_sel)
        month_out[policy] = {"identical_selection": bool(same),
                             "n_reference": len(ref_sel), "n_reimplementation": int(len(mine['selected'])),
                             "reference_dispositions": ref_disp,
                             "reimplementation_dispositions": mine['dispositions']}
    out[m] = month_out
    print(json.dumps({"month": m, **{p: month_out[p]["identical_selection"] for p in month_out}}), flush=True)

ok = all(v[p]["identical_selection"] for v in out.values() for p in v)
report = {"schema": "gtos.lane_i.protocol_equivalence.v1",
          "reference": "w21_score_feb_market_top_r2.py::select (verbatim)",
          "all_identical": ok, "months": out}
open("/tmp/lane_i/PART1_PROTOCOL_EQUIVALENCE.json", "w").write(json.dumps(report, indent=1, sort_keys=True))
print("ALL_IDENTICAL", ok)
