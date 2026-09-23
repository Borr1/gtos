#!/usr/bin/env python3
"""LANE 3 shared library: the instrumented funnel.

Reproduces, gate for gate, the frozen selection path:
  * eligibility  : w21_predecision_ridge.py:249-255  (eligible)
                   -> predecision_geometry_valid AND finite(cost_r) AND cost_r <= MAX_COST_R
                   MAX_COST_R = 0.20   candidate_funnel_analysis.py:52
  * selection    : w21_score_feb_market_top_r2.py:226-261  (select)
                   MIN_EXPECTED_NET_R = 0.10  candidate_funnel_analysis.py:53
  * order type   : candidate_funnel_analysis.py:80-81  (_order_type)
                   LIMIT iff origin_family in {current_fvg_fill, current_ob_retest,
                                               current_breaker_re_entry}
  * resolution   : probability_truth_analysis.py:177-183  (_state)

Every candidate is stamped with the FIRST gate it fails.
"""
from __future__ import annotations

import gzip
import math
import pickle
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

CACHE = Path("/private/tmp/w21-puzzle-cache")
MONTHS = ("feb", "apr", "may", "jun", "jul")
MAX_COST_R = 0.20
MIN_EXPECTED_NET_R = 0.10
LIMIT_FAMILIES = frozenset(
    {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
)
RESOLVED_STATUS_TO_STATE = {
    "RESOLVED_NO_FILL": "NO_FILL",
    "RESOLVED_FILLED_TARGET": "TARGET",
    "RESOLVED_FILLED_STOP": "STOP",
    "RESOLVED_FILLED_TIME_STOP": "TIME_STOP",
}

KEEP = (
    "candidate_occurrence_key", "candidate_id", "decision_window_id", "trading_day",
    "label_span_start_utc", "label_span_end_utc", "expiry_utc",
    "symbol", "side", "origin_family", "utc_session", "utc_hour", "weekday",
    "proposed_order_type", "cost_r", "deductible_cost_r", "spread_r",
    "expected_slippage_r", "swap_cost_r", "commission_r",
    "terminal_net_r", "lifecycle_label_status", "cost_label_status",
    "predecision_geometry_valid", "pred_month_boundary", "month",
    "distance_to_limit_atr", "distance_to_limit_risk",
    "limit_marketable_at_decision", "risk_over_atr", "stop_distance_atr",
    "target_distance_atr",
)

GATES = (
    "G0_geometry_invalid",
    "G1_cost_gt_0p20",
    "G2_symbol_occupied",
    "G3_lost_rank",
    "G4_top_below_min_pred",
    "G5_market_top_abstain",
)
TERMINAL = "TRADED"


def at(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def state_of(row):
    status = str(row.get("lifecycle_label_status") or "")
    if status in RESOLVED_STATUS_TO_STATE:
        return RESOLVED_STATUS_TO_STATE[status]
    if status.startswith("CENSORED_"):
        return None
    raise ValueError(f"unknown lifecycle status: {status!r}")


def load_month(month):
    """Compact load: only the fields the audit reads."""
    with gzip.open(CACHE / f"rows_{month}.pkl.gz", "rb") as fh:
        raw = pickle.load(fh)
    out = []
    for src in raw:
        row = {k: src.get(k) for k in KEEP}
        row["state"] = state_of(src)
        row["resolved"] = row["state"] is not None
        out.append(row)
    del raw
    return out


def net_actual(row):
    """Realized net R for a resolved row; None if censored."""
    if not row["resolved"]:
        return None
    return float(row.get("terminal_net_r") or 0.0)


def net_wc(row):
    """Worst-case convention used by every frozen gate (s2.summary:264-274):
    resolved -> terminal_net_r ; censored -> -1 - deductible_cost_r."""
    if row["resolved"]:
        return float(row.get("terminal_net_r") or 0.0)
    dc = row.get("deductible_cost_r")
    try:
        dc = float(dc)
    except (TypeError, ValueError):
        dc = 0.0
    return -1.0 - dc


def is_eligible(row):
    if not row["predecision_geometry_valid"]:
        return False, "G0_geometry_invalid"
    cost = row.get("cost_r")
    try:
        cost = float(cost)
    except (TypeError, ValueError):
        return False, "G1_cost_gt_0p20"
    if not math.isfinite(cost) or cost > MAX_COST_R:
        return False, "G1_cost_gt_0p20"
    return True, None


def run_funnel(rows, *, policy="market_top_abstain", pred_key="pred_month_boundary",
               keep=None, min_pred=MIN_EXPECTED_NET_R, max_cost=MAX_COST_R,
               diagnose=False):
    """Instrumented reproduction of s2.select.

    Returns (selected, dispositions, death) where death maps
    candidate_occurrence_key -> gate name (or 'TRADED').
    `keep` is an optional candidate-level overlay applied where pm_analysis
    applies it (before ranking), used for the scoped-family object.
    With diagnose=True a fourth element is returned: one record per decision
    window carrying the ranker's pick and the within-window realized ceiling.
    """
    death = {}
    eligible = []
    windows = []
    for row in rows:
        if max_cost == MAX_COST_R:
            ok, gate = is_eligible(row)
        else:
            # swept cost ceiling: same predicate, different constant.
            # NOTE loosening above 0.20 cannot be evaluated from this cache -
            # rows above the shipped ceiling carry no prediction (they were
            # never in r.eligible), so they are dropped and the sweep is only
            # informative DOWNWARD.
            ok, gate = True, None
            if not row["predecision_geometry_valid"]:
                ok, gate = False, "G0_geometry_invalid"
            else:
                try:
                    c = float(row.get("cost_r"))
                except (TypeError, ValueError):
                    c = float("nan")
                if not math.isfinite(c) or c > max_cost:
                    ok, gate = False, "G1_cost_gt_0p20"
        if not ok:
            death[row["candidate_occurrence_key"]] = gate
            continue
        if row.get(pred_key) is None:
            # eligible rows always carry a prediction in the cache; guard anyway
            death[row["candidate_occurrence_key"]] = "G1_cost_gt_0p20"
            continue
        eligible.append(row)

    by_window = defaultdict(list)
    for row in eligible:
        by_window[row["decision_window_id"]].append((float(row[pred_key]), row))
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
        active = {sym: end for sym, end in active.items() if end > decision_at}
        available, blocked = [], []
        for prediction, row in candidates:
            if row["symbol"] in active:
                blocked.append(row)
                continue
            if policy == "market_rerank" and row["proposed_order_type"] != "MARKET":
                blocked.append(row)
                continue
            if keep is not None and not keep(row):
                blocked.append(row)
                continue
            available.append(
                (prediction, -float(row["cost_r"]), row["candidate_occurrence_key"], row)
            )
        for row in blocked:
            death[row["candidate_occurrence_key"]] = "G2_symbol_occupied"
        if not available:
            dispositions["no_available_candidate"] += 1
            continue
        prediction, _neg, _key, top = max(available, key=lambda item: item[:3])
        for _p, _n, _k, row in available:
            if row is not top:
                death[row["candidate_occurrence_key"]] = "G3_lost_rank"
        if diagnose:
            windows.append(_window_record(available, top, prediction))
        if prediction < min_pred:
            dispositions["top_below_0p10"] += 1
            death[top["candidate_occurrence_key"]] = "G4_top_below_min_pred"
            if diagnose:
                windows[-1]["outcome_gate"] = "G4_top_below_min_pred"
            continue
        if policy == "market_top_abstain" and top["proposed_order_type"] != "MARKET":
            dispositions["top_limit_abstain"] += 1
            death[top["candidate_occurrence_key"]] = "G5_market_top_abstain"
            if diagnose:
                windows[-1]["outcome_gate"] = "G5_market_top_abstain"
            continue
        dispositions["trade"] += 1
        death[top["candidate_occurrence_key"]] = TERMINAL
        if diagnose:
            windows[-1]["outcome_gate"] = TERMINAL
        selected.append(dict(top, predicted_net_r=prediction))
        active[top["symbol"]] = at(top["label_span_end_utc"] or top["expiry_utc"])
    if diagnose:
        return selected, dict(sorted(dispositions.items())), death, windows
    return selected, dict(sorted(dispositions.items())), death


def _window_record(available, top, prediction):
    """Per-window ceiling diagnostics over the AVAILABLE set (post-occupancy)."""
    rows = [item[3] for item in available]
    preds = [item[0] for item in available]
    act = [net_actual(r) for r in rows]
    wc = [net_wc(r) for r in rows]
    res = [a for a in act if a is not None]
    order = sorted(range(len(rows)), key=lambda i: (preds[i], -float(rows[i]["cost_r"]),
                                                    rows[i]["candidate_occurrence_key"]),
                   reverse=True)
    market_idx = [i for i in range(len(rows)) if rows[i]["proposed_order_type"] == "MARKET"]
    cheap = min(range(len(rows)), key=lambda i: float(rows[i]["cost_r"]))
    return {
        "trading_day": top["trading_day"],
        "decision_window_id": top["decision_window_id"],
        "n_available": len(rows),
        "n_resolved": len(res),
        "top_pred": prediction,
        "top_order_type": top["proposed_order_type"],
        "top_family": top["origin_family"],
        "top_symbol": top["symbol"],
        "pick_actual": net_actual(top),
        "pick_wc": net_wc(top),
        "rank2_actual": net_actual(rows[order[1]]) if len(order) > 1 else None,
        "rank2_wc": net_wc(rows[order[1]]) if len(order) > 1 else None,
        "oracle_max_actual": max(res) if res else None,
        "oracle_min_actual": min(res) if res else None,
        "oracle_max_wc": max(wc) if wc else None,
        "mean_actual": (sum(res) / len(res)) if res else None,
        "mean_wc": (sum(wc) / len(wc)) if wc else None,
        "mincost_actual": net_actual(rows[cheap]),
        "mincost_wc": net_wc(rows[cheap]),
        "market_argmax_actual": (
            net_actual(rows[max(market_idx, key=lambda i: (preds[i], -float(rows[i]["cost_r"])))])
            if market_idx else None),
        "market_argmax_wc": (
            net_wc(rows[max(market_idx, key=lambda i: (preds[i], -float(rows[i]["cost_r"])))])
            if market_idx else None),
        "n_positive_available": sum(1 for a in res if a > 0),
        "pick_is_window_best": bool(res and net_actual(top) is not None
                                    and net_actual(top) >= max(res) - 1e-12),
        "outcome_gate": None,
    }


def portfolio(selected):
    resolved = [row for row in selected if row["resolved"]]
    censored = [row for row in selected if not row["resolved"]]
    actual = sum(float(row.get("terminal_net_r") or 0.0) for row in resolved)
    worst = actual + sum(-1.0 - float(row["deductible_cost_r"]) for row in censored)
    by_day = defaultdict(float)
    for row in resolved:
        by_day[row["trading_day"]] += float(row.get("terminal_net_r") or 0.0)
    return {
        "selected": len(selected),
        "resolved": len(resolved),
        "censored": len(censored),
        "actual_net_r": round(actual, 6),
        "worst_case_net_r": round(worst, 6),
        "outcomes": dict(sorted(Counter(row["state"] or "CENSORED" for row in selected).items())),
        "families": dict(sorted(Counter(row["origin_family"] for row in selected).items())),
        "net_by_family": {
            name: round(sum(float(r.get("terminal_net_r") or 0.0)
                            for r in resolved if r["origin_family"] == name), 6)
            for name in sorted({r["origin_family"] for r in selected})
        },
        "positive_days": sum(1 for v in by_day.values() if v > 0),
        "negative_days": sum(1 for v in by_day.values() if v < 0),
    }
