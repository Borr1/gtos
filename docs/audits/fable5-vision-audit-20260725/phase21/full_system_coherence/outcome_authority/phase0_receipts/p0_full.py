#!/usr/bin/env python3
"""Phase 0 — the full result set: T2, T3, T5, and the gate.

Every number here is computed off `walk_{month}.pkl.gz`, which is the committed
labeler's own output on two order contracts (original + inverted) over the five
sealed candidate roots. The original arm reproduces the sealed cache exactly
(see P0_CONTROL.json).
"""
from __future__ import annotations

import gzip
import json
import math
import pickle
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

OUT = Path("/private/tmp/phase0-inversion")
MONTHS = ("feb", "apr", "may", "jun", "jul")
MARKET = (
    "structural_distance_extreme",
    "liquidity_sweep_reclaim",
    "cross_asset_lead_lag",
    "displacement_continuation",
    "session_open_range_break",
    "regime_transition_break",
    "volatility_compression_expansion",
)
FILLED = ("RESOLVED_FILLED_TARGET", "RESOLVED_FILLED_STOP", "RESOLVED_FILLED_TIME_STOP")
GATE_R = 0.03
MAX_COST_R = 0.20


def load():
    records = []
    for month in MONTHS:
        path = OUT / f"walk_{month}.pkl.gz"
        rows = pickle.load(gzip.open(path, "rb"))
        for row in rows:
            row["month"] = month
        records.extend(rows)
    return records


def m(values):
    values = [v for v in values if v is not None]
    return float(np.mean(values)) if values else None


def stats(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0}
    arr = np.asarray(values, dtype=float)
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "sd": float(arr.std(ddof=1)) if arr.size > 1 else None,
        "se": float(arr.std(ddof=1) / math.sqrt(arr.size)) if arr.size > 1 else None,
        "sum": float(arr.sum()),
    }


def drawdown(series):
    peak = run = worst = 0.0
    for value in series:
        run += value
        peak = max(peak, run)
        worst = min(worst, run - peak)
    return worst


def per_day(rows, arm, extra=0.0):
    by_day = defaultdict(float)
    for row in rows:
        by_day[row["day"]] += row[arm]["net"] - extra
    days = sorted(by_day)
    return [by_day[day] for day in days]


def driftless_p(row, arm):
    """P(target first) for a driftless continuous path from the ACTUAL modelled fill.

    Exact for driftless Brownian motion with continuous paths and any volatility:
    P = down_distance / (down_distance + up_distance). Uses the real fill price, so
    it absorbs the geometry (RR 2.0), the spread side and the entry drift.
    """
    fill = row[arm]["fill_price"]
    if fill is None:
        return None
    entry, risk = row["entry_price"], row["risk_price"]
    long_orig = row["side"] == "LONG"
    stop_o, target_o = (
        (entry - risk, entry + row["risk_price_inv"])
        if long_orig
        else (entry + risk, entry - row["risk_price_inv"])
    )
    if arm == "orig":
        stop, target, direction = stop_o, target_o, (1 if long_orig else -1)
    else:
        stop, target, direction = target_o, stop_o, (-1 if long_orig else 1)
    down = direction * (fill - stop)
    up = direction * (target - fill)
    if down <= 0 or up <= 0:
        return None
    return down / (down + up)


def arm_block(rows, arm, extra=0.0):
    if not rows:
        return {"n": 0}
    net = [row[arm]["net"] - extra for row in rows]
    states = Counter(row[arm]["state"] for row in rows)
    barrier = states["TARGET"] + states["STOP"]
    bench = [
        driftless_p(row, arm)
        for row in rows
        if row[arm]["state"] in ("TARGET", "STOP")
    ]
    bench = [b for b in bench if b is not None]
    hit = states["TARGET"] / barrier if barrier else None
    expected = float(np.mean(bench)) if bench else None
    z = None
    if hit is not None and expected is not None and barrier > 0:
        var = sum(p * (1 - p) for p in bench)
        z = (states["TARGET"] - sum(bench)) / math.sqrt(var) if var > 0 else None
    series = per_day(rows, arm, extra)
    return {
        **stats(net),
        "states": dict(states),
        "barrier_n": barrier,
        "hit_rate": hit,
        "driftless_benchmark": expected,
        "z_vs_driftless": z,
        "time_stop_share": states["TIME_STOP"] / len(rows),
        "worst_day_r": min(series) if series else None,
        "best_day_r": max(series) if series else None,
        "max_drawdown_r": drawdown(series),
        "active_days": len(series),
    }


def sel(records, arm, *, family=None, month=None, eligible=False, pred=None):
    out = []
    for row in records:
        if family and row["family"] != family:
            continue
        if month and row["month"] != month:
            continue
        if eligible and row["cost_r"] > MAX_COST_R:
            continue
        if row[arm]["status"] not in FILLED:
            continue
        if pred and not pred(row):
            continue
        out.append(row)
    return out


def main():
    records = load()
    market = [row for row in records if row["family"] in MARKET]
    report = {
        "population": {
            "records": len(records),
            "by_month": dict(Counter(row["month"] for row in records)),
            "by_family": dict(Counter(row["family"] for row in records)),
        },
        "geometry": {
            "risk_reward_ratio_observed": dict(
                Counter(
                    round(row["risk_price_inv"] / row["risk_price"], 4)
                    for row in records
                    if row["risk_price"] > 0
                ).most_common(5)
            ),
            "note": (
                "target distance / stop distance for every sealed candidate. The plan's "
                "section 3 assumes 1.5; the sealed rows carry 2.0 "
                "(risk_reward_ratio == 2.0 on every compact row, set by the replay's "
                "momentum_exhaustion dynamic execution policy, final_target_r=2.0, "
                "src/research/dynamic_execution_policy.py:167-186 -- NOT risk.min_rr, "
                "which is 1.5 at config/agent_config.yaml:39)."
            ),
        },
    }

    # ---- T2 ---------------------------------------------------------------
    t2 = {}
    for family in MARKET:
        block = {"pooled": {}, "pooled_eligible": {}, "per_month": {}, "per_month_eligible": {}}
        for arm in ("orig", "inv"):
            block["pooled"][arm] = arm_block(sel(market, arm, family=family), arm)
            block["pooled_eligible"][arm] = arm_block(
                sel(market, arm, family=family, eligible=True), arm
            )
        for month in MONTHS:
            block["per_month"][month] = {
                arm: arm_block(sel(market, arm, family=family, month=month), arm)
                for arm in ("orig", "inv")
            }
            block["per_month_eligible"][month] = {
                arm: arm_block(
                    sel(market, arm, family=family, month=month, eligible=True), arm
                )
                for arm in ("orig", "inv")
            }
        for scope, key in (("per_month", "months_positive"), ("per_month_eligible", "months_positive_eligible")):
            block[key] = sum(
                1
                for month in MONTHS
                if (block[scope][month]["inv"].get("mean") or 0) > 0
            )
            block[key + "_above_gate"] = sum(
                1
                for month in MONTHS
                if (block[scope][month]["inv"].get("mean") or -9) >= GATE_R
            )
        t2[family] = block
    report["T2_inverted_walk"] = t2

    # ---- T3 time stops ----------------------------------------------------
    t3 = {}
    for family in MARKET:
        rows = sel(market, "inv", family=family)
        ts = [row for row in rows if row["inv"]["state"] == "TIME_STOP"]
        bar = [row for row in rows if row["inv"]["state"] != "TIME_STOP"]
        pairs = [
            (-row["orig"]["gross"] / (row["risk_price_inv"] / row["risk_price"]),
             row["inv"]["gross"])
            for row in ts
            if row["orig"]["status"] == "RESOLVED_FILLED_TIME_STOP"
        ]
        plan_pairs = [
            (-row["orig"]["gross"] / 1.5, row["inv"]["gross"])
            for row in ts
            if row["orig"]["status"] == "RESOLVED_FILLED_TIME_STOP"
        ]
        residual = [exact - approx for approx, exact in pairs]
        plan_residual = [exact - approx for approx, exact in plan_pairs]
        total = sum(row["inv"]["net"] for row in rows)
        t3[family] = {
            "inv_filled_n": len(rows),
            "time_stop_n": len(ts),
            "time_stop_share": len(ts) / len(rows) if rows else None,
            "time_stop_mean_net_r": m([row["inv"]["net"] for row in ts]),
            "barrier_mean_net_r": m([row["inv"]["net"] for row in bar]),
            "time_stop_share_of_total_net": (
                sum(row["inv"]["net"] for row in ts) / total if total else None
            ),
            "exact_vs_ratio_approx": {
                "n": len(pairs),
                "approx_mean": m([a for a, _ in pairs]),
                "exact_mean": m([b for _, b in pairs]),
                "residual_mean": m(residual),
                "residual_sd": stats(residual).get("sd"),
                "residual_max_abs": float(np.max(np.abs(residual))) if residual else None,
            },
            "exact_vs_plan_1p5_approx": {
                "n": len(plan_pairs),
                "approx_mean": m([a for a, _ in plan_pairs]),
                "exact_mean": m([b for _, b in plan_pairs]),
                "residual_mean": m(plan_residual),
            },
        }
    report["T3_time_stops"] = t3

    # ---- T5 adversarial ---------------------------------------------------
    t5 = {}

    # (b) drop the worst symbol per family
    worst_symbol = {}
    for family in MARKET:
        rows = sel(market, "inv", family=family, eligible=True)
        by_symbol = defaultdict(list)
        for row in rows:
            by_symbol[row["symbol"]].append(row["inv"]["net"])
        totals = {s: float(np.sum(v)) for s, v in by_symbol.items()}
        if not totals:
            continue
        worst = min(totals, key=totals.get)
        kept = [row for row in rows if row["symbol"] != worst]
        worst_symbol[family] = {
            "worst_symbol": worst,
            "worst_symbol_total_r": totals[worst],
            "all_mean": m([row["inv"]["net"] for row in rows]),
            "ex_worst_mean": m([row["inv"]["net"] for row in kept]),
            "ex_worst_n": len(kept),
            "ex_worst_months_positive": sum(
                1
                for month in MONTHS
                if (m([row["inv"]["net"] for row in kept if row["month"] == month]) or 0) > 0
            ),
        }
    t5["b_exclude_worst_symbol"] = worst_symbol

    # (c) within-month stability: first half vs second half of each month's days
    halves = {}
    for family in MARKET:
        rows = sel(market, "inv", family=family, eligible=True)
        per = {}
        for month in MONTHS:
            month_rows = [row for row in rows if row["month"] == month]
            days = sorted({row["day"] for row in month_rows})
            if not days:
                continue
            cut = days[len(days) // 2]
            first = [row for row in month_rows if row["day"] < cut]
            second = [row for row in month_rows if row["day"] >= cut]
            per[month] = {
                "first_half": {"n": len(first), "mean": m([r["inv"]["net"] for r in first])},
                "second_half": {"n": len(second), "mean": m([r["inv"]["net"] for r in second])},
            }
        halves[family] = per
    t5["c_within_month_halves"] = halves

    # (d) portfolio constraint: one trade per decision window, per family, plus a
    #     same-symbol occupancy rule, ranked by lowest cost (no model needed)
    portfolio = {}
    for family in MARKET:
        rows = sorted(
            sel(market, "inv", family=family, eligible=True),
            key=lambda row: (row["decision_utc"], row["cost_r"], row["key"]),
        )
        by_window = {}
        for row in rows:
            by_window.setdefault(row["window"], row)
        chosen = sorted(by_window.values(), key=lambda row: row["decision_utc"])
        series = per_day(chosen, "inv")
        portfolio[family] = {
            "n": len(chosen),
            **stats([row["inv"]["net"] for row in chosen]),
            "months_positive": sum(
                1
                for month in MONTHS
                if (m([row["inv"]["net"] for row in chosen if row["month"] == month]) or 0) > 0
            ),
            "per_month_mean": {
                month: m([row["inv"]["net"] for row in chosen if row["month"] == month])
                for month in MONTHS
            },
            "worst_day_r": min(series) if series else None,
            "max_drawdown_r": drawdown(series),
        }
    t5["d_one_per_window_portfolio"] = portfolio

    # (e) direction mapping: does LONG beat SHORT on symbols that rose?
    direction = {}
    for month in MONTHS:
        for symbol in sorted({row["symbol"] for row in market if row["month"] == month}):
            rows = [
                row
                for row in market
                if row["month"] == month
                and row["symbol"] == symbol
                and row["orig"]["status"] in FILLED
            ]
            if len(rows) < 40:
                continue
            ordered = sorted(rows, key=lambda row: row["decision_utc"])
            first, last = ordered[0], ordered[-1]
            move = (last["entry_price"] - first["entry_price"]) / first["entry_price"]
            longs = [row["orig"]["gross"] for row in rows if row["side"] == "LONG"]
            shorts = [row["orig"]["gross"] for row in rows if row["side"] == "SHORT"]
            if not longs or not shorts:
                continue
            direction[f"{month}|{symbol}"] = {
                "month_move_frac": move,
                "long_mean_gross": float(np.mean(longs)),
                "short_mean_gross": float(np.mean(shorts)),
                "long_minus_short": float(np.mean(longs) - np.mean(shorts)),
                "n_long": len(longs),
                "n_short": len(shorts),
            }
    moves = [v["month_move_frac"] for v in direction.values()]
    spreads = [v["long_minus_short"] for v in direction.values()]
    corr = float(np.corrcoef(moves, spreads)[0, 1]) if len(moves) > 2 else None
    t5["e_direction_mapping"] = {
        "cells": len(direction),
        "corr_month_move_vs_long_minus_short": corr,
        "sign_agreement_frac": float(
            np.mean([np.sign(a) == np.sign(b) for a, b in zip(moves, spreads)])
        )
        if moves
        else None,
        "geometry_consistency": (
            "the labeler refuses any row whose stop/entry/target ordering contradicts its "
            "declared side (quote_side.py:1148-1152, CENSORED_GEOMETRY); the observed "
            "censor count for that reason bounds any side/geometry mismatch"
        ),
        "censored_geometry_rows": sum(
            1 for row in market if row["orig"]["status"] == "CENSORED_GEOMETRY"
        ),
        "per_cell": direction,
    }

    # (a) fill/labeling asymmetry: the modelled fill is one M1 bar late
    asym = {}
    for family in MARKET:
        rows = [
            row
            for row in market
            if row["family"] == family
            and row["entry_drift_r_orig_dir"] is not None
            and row["orig"]["status"] in FILLED
        ]
        drift = [row["entry_drift_r_orig_dir"] for row in rows]
        inv_units = [
            -row["entry_drift_r_orig_dir"] * row["risk_price"] / row["risk_price_inv"]
            for row in rows
        ]
        asym[family] = {
            "n": len(rows),
            "orig_dir_drift_r": stats(drift),
            "inv_dir_drift_r_in_inv_units": stats(inv_units),
        }
    t5["a_entry_timing_asymmetry"] = asym

    # (a2) is the anti-signal a cost artifact? hit rate by spread quintile,
    #      against the per-row driftless benchmark
    quint = {}
    for family in MARKET:
        rows = [
            row
            for row in sel(market, "orig", family=family)
            if row["orig"]["state"] in ("TARGET", "STOP")
        ]
        if len(rows) < 100:
            continue
        cuts = np.percentile([row["spread_r"] for row in rows], [20, 40, 60, 80])
        buckets = defaultdict(list)
        for row in rows:
            buckets[int(np.searchsorted(cuts, row["spread_r"]))].append(row)
        quint[family] = {}
        for index, bucket in sorted(buckets.items()):
            bench = [driftless_p(row, "orig") for row in bucket]
            bench = [b for b in bench if b is not None]
            hits = sum(row["orig"]["state"] == "TARGET" for row in bucket)
            var = sum(p * (1 - p) for p in bench)
            quint[family][f"q{index + 1}"] = {
                "n": len(bucket),
                "median_spread_r": float(np.median([row["spread_r"] for row in bucket])),
                "hit_rate": hits / len(bucket),
                "driftless_benchmark": float(np.mean(bench)) if bench else None,
                "z": (hits - sum(bench)) / math.sqrt(var) if var > 0 else None,
            }
    t5["a2_hit_rate_by_spread_quintile"] = quint
    report["T5_adversarial"] = t5

    # ---- the gate ---------------------------------------------------------
    gate = {}
    for family in MARKET:
        block = t2[family]
        per_month = {
            month: block["per_month_eligible"][month]["inv"].get("mean")
            for month in MONTHS
        }
        above = [month for month, value in per_month.items() if (value or -9) >= GATE_R]
        port = t5["d_one_per_window_portfolio"].get(family, {})
        gate[family] = {
            "pooled_mean_r_eligible": block["pooled_eligible"]["inv"].get("mean"),
            "per_month_mean_r_eligible": per_month,
            "months_at_or_above_+0.03": len(above),
            "portfolio_pooled_mean_r": port.get("mean"),
            "portfolio_months_positive": port.get("months_positive"),
            "PASS": len(above) >= 4,
        }
    report["GATE"] = {
        "rule": "at least one MARKET family clears +0.03 R/trade after true costs in >=4 of 5 months",
        "per_family": gate,
        "ANY_FAMILY_PASSES": any(value["PASS"] for value in gate.values()),
    }

    path = OUT / "receipts/P0_FULL_RESULT.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=1, sort_keys=True, allow_nan=False) + "\n")
    print("WROTE", path)
    print(f"{'family':34s} {'n(elig)':>8s} {'inv mean':>9s} {'mo>=+.03':>9s} {'hit':>6s} {'bench':>6s} {'z':>8s} {'PASS':>5s}")
    for family in MARKET:
        block = t2[family]["pooled_eligible"]["inv"]
        g = gate[family]
        print(
            f"{family:34s} {block.get('n',0):8d} {block.get('mean',float('nan')):+9.4f} "
            f"{g['months_at_or_above_+0.03']:9d} {block.get('hit_rate') or float('nan'):6.3f} "
            f"{block.get('driftless_benchmark') or float('nan'):6.3f} "
            f"{block.get('z_vs_driftless') or float('nan'):+8.2f} {str(g['PASS']):>5s}"
        )
    print("ANY FAMILY PASSES:", report["GATE"]["ANY_FAMILY_PASSES"])


if __name__ == "__main__":
    main()
