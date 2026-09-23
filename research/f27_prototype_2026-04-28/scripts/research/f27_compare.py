"""F27 — pair baseline + treatment via M1 fill sim, compute paired stats.

Mirrors fill_simulator_m1_full_cohort.py methodology, but runs over BOTH
runs and computes paired comparison: per-record realized R delta, decision
flip table, trade-parameter deltas, and Wilcoxon signed-rank.
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Resolve repo root: script is at research/f27_.../scripts/research/<this>.py
# parents[4] = repo root. Override via GTOS_REPO_ROOT env if needed.
import os as _os
_REPO_ENV = _os.environ.get("GTOS_REPO_ROOT")
REPO = Path(_REPO_ENV) if _REPO_ENV else Path(__file__).resolve().parents[4]
M1_CSV = REPO / "data" / "historical_2026" / "XAUUSD_M1.csv"
OUT_DIR = Path(__file__).resolve().parents[2]  # research/f27_prototype_2026-04-28/
BASELINE_OUTCOMES = OUT_DIR / "baseline_replay_outcomes.jsonl"
TREATMENT_OUTCOMES = OUT_DIR / "treatment_replay_outcomes.jsonl"
COMPARISON_OUT = OUT_DIR / "f27_comparison.json"

EXPIRY_M15_CANDLES = 192
EXPIRY_M1_MINUTES = EXPIRY_M15_CANDLES * 15  # 2880


# -- M1 fill simulator (copied verbatim from
# fill_simulator_m1_full_cohort.py:simulate_limit) -------------------------

def load_m1():
    bars = []
    with open(M1_CSV, encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        for row in rdr:
            t = datetime.fromisoformat(row["time"]).replace(tzinfo=timezone.utc)
            bars.append({
                "time": t,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            })
    bars.sort(key=lambda b: b["time"])
    return bars


def find_first_bar_after(bars, t: datetime) -> int:
    for i, b in enumerate(bars):
        if b["time"] > t:
            return i
    return -1


def simulate_limit(bars, candle_time: datetime, direction: str,
                    limit: float, sl: float, tp1: float,
                    expiry_minutes: int = EXPIRY_M1_MINUTES) -> dict:
    next_idx = find_first_bar_after(bars, candle_time)
    if next_idx == -1:
        return {"outcome": "NO_DATA", "exit_reason": "candle_time after data range"}

    end_scan = min(next_idx + expiry_minutes, len(bars))

    fill_idx = -1
    fill_price = None
    for i in range(next_idx, end_scan):
        b = bars[i]
        if direction == "LONG":
            if b["low"] <= limit:
                fill_idx = i
                fill_price = limit
                break
        else:
            if b["high"] >= limit:
                fill_idx = i
                fill_price = limit
                break

    if fill_idx == -1:
        return {
            "outcome": "NEVER_FILLED",
            "realized_r": None,
            "exit_reason": "never_filled",
        }

    risk = abs(fill_price - sl)
    exit_end = min(fill_idx + expiry_minutes, len(bars))
    for i in range(fill_idx, exit_end):
        b = bars[i]
        if direction == "LONG":
            sl_hit = b["low"] <= sl
            tp_hit = b["high"] >= tp1
        else:
            sl_hit = b["high"] >= sl
            tp_hit = b["low"] <= tp1

        if sl_hit and tp_hit:
            return {
                "outcome": "FILLED_LOSS",
                "realized_r": -1.0,
                "fill_time": bars[fill_idx]["time"].isoformat(),
                "fill_price": fill_price,
                "exit_time": b["time"].isoformat(),
                "exit_price": sl,
                "exit_reason": "sl_hit (M1 ambiguous bar -- SL assumed first)",
                "intra_m1_ambiguity": True,
            }
        if sl_hit:
            return {
                "outcome": "FILLED_LOSS",
                "realized_r": -1.0,
                "fill_time": bars[fill_idx]["time"].isoformat(),
                "fill_price": fill_price,
                "exit_time": b["time"].isoformat(),
                "exit_price": sl,
                "exit_reason": "sl_hit",
            }
        if tp_hit:
            r = abs(tp1 - fill_price) / risk if risk > 0 else 0.0
            return {
                "outcome": "FILLED_WIN",
                "realized_r": r,
                "fill_time": bars[fill_idx]["time"].isoformat(),
                "fill_price": fill_price,
                "exit_time": b["time"].isoformat(),
                "exit_price": tp1,
                "exit_reason": "tp1_hit",
            }

    last_bar = bars[exit_end - 1]
    final_close = last_bar["close"]
    pnl = (final_close - fill_price) if direction == "LONG" else (fill_price - final_close)
    r = pnl / risk if risk > 0 else 0.0
    return {
        "outcome": "STILL_OPEN_AT_SIM_END",
        "realized_r": r,
        "fill_time": bars[fill_idx]["time"].isoformat(),
        "fill_price": fill_price,
        "exit_time": last_bar["time"].isoformat(),
        "exit_price": final_close,
        "exit_reason": f"sim_horizon_end_at_{expiry_minutes}_minutes",
    }


def simulate_run(bars, replay_path: Path) -> dict:
    """Run M1 fill sim across all records of a replay file."""
    rows = [json.loads(l) for l in open(replay_path, encoding="utf-8")]
    out = {}
    for row in rows:
        if row.get("error"):
            out[row["trade_id"]] = {"outcome": "ERROR", "error": row["error"]}
            continue
        cur = row["current"]
        if cur.get("ai_decision") != "CANDIDATE" or not cur.get("trade_parameters"):
            out[row["trade_id"]] = {"outcome": "NOT_CANDIDATE",
                                      "ai_decision": cur.get("ai_decision")}
            continue
        candle_time = datetime.fromisoformat(row["candle_time_utc"])
        if candle_time.tzinfo is None:
            candle_time = candle_time.replace(tzinfo=timezone.utc)
        tp = cur["trade_parameters"]
        result = simulate_limit(bars, candle_time, tp["direction"],
                                  tp["entry_price"], tp["stop_loss"],
                                  tp["take_profit_1"])
        result["entry"] = tp["entry_price"]
        result["sl"] = tp["stop_loss"]
        result["tp1"] = tp["take_profit_1"]
        result["sl_buffer"] = tp.get("sl_buffer_applied", 0.0)
        result["direction"] = tp["direction"]
        out[row["trade_id"]] = result
    return out


# -- Wilcoxon signed-rank (one-sample, two-sided, exact for n<=15) ---------

def wilcoxon_signed_rank(diffs: list[float]) -> dict:
    """Compute exact two-sided p-value for Wilcoxon signed-rank.

    For small n (<=15) we compute the exact null distribution by enumeration.
    """
    nonzero = [d for d in diffs if d != 0]
    n = len(nonzero)
    if n == 0:
        return {"n_nonzero": 0, "W_plus": 0.0, "p_two_sided": 1.0}

    abs_diffs = [abs(d) for d in nonzero]
    ranks = _rank_with_ties(abs_diffs)

    W_plus = sum(rk for rk, d in zip(ranks, nonzero) if d > 0)
    W_minus = sum(rk for rk, d in zip(ranks, nonzero) if d < 0)
    W = min(W_plus, W_minus)

    # Exact: enumerate all 2^n sign assignments
    if n > 25:
        # Approximate normal (we won't hit this in pilot but kept for safety)
        mu = n * (n + 1) / 4
        sigma = (n * (n + 1) * (2 * n + 1) / 24) ** 0.5
        z = (W_plus - mu) / sigma
        # Two-sided
        from math import erf
        p = 2 * (1 - 0.5 * (1 + erf(abs(z) / 2 ** 0.5)))
        return {"n_nonzero": n, "W_plus": W_plus, "W_minus": W_minus,
                 "p_two_sided": p, "method": "normal_approx"}

    # Exact enumeration
    count_le = 0
    total = 1 << n
    for mask in range(total):
        w = 0.0
        for i in range(n):
            if mask & (1 << i):
                w += ranks[i]
        if w <= W:
            count_le += 1
    # Two-sided: P(W_plus <= W or W_plus >= total_rank_sum - W)
    rank_sum = sum(ranks)
    count_ge_high = 0
    high = rank_sum - W
    for mask in range(total):
        w = 0.0
        for i in range(n):
            if mask & (1 << i):
                w += ranks[i]
        if w >= high:
            count_ge_high += 1
    if W == high:
        # Avoid double-counting the exact tail when W == E[W] and is symmetric
        p = (count_le + count_ge_high - count_le) / total
    else:
        p = (count_le + count_ge_high) / total
    return {"n_nonzero": n, "W_plus": W_plus, "W_minus": W_minus,
             "p_two_sided": min(p, 1.0), "method": "exact"}


def _rank_with_ties(values: list[float]) -> list[float]:
    """Average rank for ties."""
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg = (i + j + 2) / 2  # ranks are 1-indexed
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg
        i = j + 1
    return ranks


# -- Sign test (binomial two-sided) ----------------------------------------

def sign_test(diffs: list[float]) -> dict:
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    n = pos + neg
    if n == 0:
        return {"pos": 0, "neg": 0, "p_two_sided": 1.0}
    # Exact two-sided binomial p-value: P(X <= min(pos,neg) | p=0.5) * 2
    from math import comb
    k = min(pos, neg)
    cdf = sum(comb(n, i) * (0.5 ** n) for i in range(k + 1))
    p = min(2 * cdf, 1.0)
    return {"pos": pos, "neg": neg, "p_two_sided": p}


# -- Main ------------------------------------------------------------------

def main():
    print(f"Loading M1 from {M1_CSV}")
    bars = load_m1()
    print(f"  loaded {len(bars)} bars\n")

    print(f"Sim baseline ({BASELINE_OUTCOMES.name})…")
    baseline_sim = simulate_run(bars, BASELINE_OUTCOMES)
    print(f"  simulated {len(baseline_sim)} records")

    print(f"Sim treatment ({TREATMENT_OUTCOMES.name})…")
    treatment_sim = simulate_run(bars, TREATMENT_OUTCOMES)
    print(f"  simulated {len(treatment_sim)} records")

    # Load decisions for flip table
    baseline_rows = {r["trade_id"]: r for r in
                       (json.loads(l) for l in open(BASELINE_OUTCOMES, encoding="utf-8"))}
    treatment_rows = {r["trade_id"]: r for r in
                       (json.loads(l) for l in open(TREATMENT_OUTCOMES, encoding="utf-8"))}

    trade_ids = sorted(set(baseline_rows.keys()) & set(treatment_rows.keys()))
    print(f"Paired records: {len(trade_ids)}")

    # 2x2 flip table
    flip_2x2 = {}
    for tid in trade_ids:
        b_dec = baseline_rows[tid]["current"].get("ai_decision") or "ERROR"
        t_dec = treatment_rows[tid]["current"].get("ai_decision") or "ERROR"
        key = f"{b_dec} -> {t_dec}"
        flip_2x2[key] = flip_2x2.get(key, 0) + 1

    # Trade parameter deltas (only for both-CAND records)
    param_deltas = []
    for tid in trade_ids:
        b = baseline_rows[tid]["current"]
        t = treatment_rows[tid]["current"]
        bp = b.get("trade_parameters")
        tp = t.get("trade_parameters")
        if not bp or not tp:
            continue
        param_deltas.append({
            "trade_id": tid,
            "d_entry": tp["entry_price"] - bp["entry_price"],
            "d_sl": tp["stop_loss"] - bp["stop_loss"],
            "d_tp1": tp["take_profit_1"] - bp["take_profit_1"],
            "d_buf": (tp.get("sl_buffer_applied") or 0) - (bp.get("sl_buffer_applied") or 0),
        })

    # Realized-R deltas (treat NEVER_FILLED as 0)
    def _r(rec) -> float:
        if rec.get("outcome") in ("NEVER_FILLED", "ERROR", "NOT_CANDIDATE", "NO_DATA"):
            return 0.0
        return rec.get("realized_r") or 0.0

    paired_R = []
    for tid in trade_ids:
        bR = _r(baseline_sim[tid])
        tR = _r(treatment_sim[tid])
        paired_R.append({
            "trade_id": tid,
            "baseline_R": bR,
            "treatment_R": tR,
            "delta_R": tR - bR,
            "baseline_outcome": baseline_sim[tid].get("outcome"),
            "treatment_outcome": treatment_sim[tid].get("outcome"),
        })

    diffs = [p["delta_R"] for p in paired_R]
    mean_baseline_R = sum(p["baseline_R"] for p in paired_R) / len(paired_R)
    mean_treatment_R = sum(p["treatment_R"] for p in paired_R) / len(paired_R)
    mean_delta_R = sum(diffs) / len(diffs)

    wilcoxon = wilcoxon_signed_rank(diffs)
    sign = sign_test(diffs)

    # WR computation
    def _wr(sim_dict):
        cands = [r for r in sim_dict.values()
                 if r.get("outcome") in ("FILLED_WIN", "FILLED_LOSS",
                                          "STILL_OPEN_AT_SIM_END")]
        wins = [r for r in cands
                if r.get("outcome") == "FILLED_WIN" or
                   (r.get("outcome") == "STILL_OPEN_AT_SIM_END" and (r.get("realized_r") or 0) > 0)]
        return len(wins) / len(cands) if cands else 0.0, len(wins), len(cands)

    b_wr, b_w, b_n = _wr(baseline_sim)
    t_wr, t_w, t_n = _wr(treatment_sim)

    # Verdict
    if mean_delta_R >= 0.10:
        verdict = "GO"
        verdict_reason = (f"Mean realized-R delta = {mean_delta_R:+.3f}R/trade meets "
                           f"threshold (>= +0.10R/trade).")
    elif mean_delta_R <= -0.05:
        verdict = "NO_GO"
        verdict_reason = (f"Mean realized-R delta = {mean_delta_R:+.3f}R/trade falls "
                           f"below kill threshold (<= -0.05R/trade).")
    else:
        verdict = "INCONCLUSIVE"
        verdict_reason = (f"Mean realized-R delta = {mean_delta_R:+.3f}R/trade is in "
                           f"the kill-fast band (-0.05R to +0.10R). Pilot null.")

    summary = {
        "n_paired": len(trade_ids),
        "decision_flip_2x2": flip_2x2,
        "trade_parameter_deltas": {
            "n_records_with_both_params": len(param_deltas),
            "mean_d_entry": statistics.mean(d["d_entry"] for d in param_deltas) if param_deltas else 0.0,
            "mean_d_sl": statistics.mean(d["d_sl"] for d in param_deltas) if param_deltas else 0.0,
            "mean_d_tp1": statistics.mean(d["d_tp1"] for d in param_deltas) if param_deltas else 0.0,
            "median_d_entry": statistics.median(d["d_entry"] for d in param_deltas) if param_deltas else 0.0,
            "median_d_sl": statistics.median(d["d_sl"] for d in param_deltas) if param_deltas else 0.0,
            "median_d_tp1": statistics.median(d["d_tp1"] for d in param_deltas) if param_deltas else 0.0,
            "max_abs_d_entry": max((abs(d["d_entry"]) for d in param_deltas), default=0.0),
            "max_abs_d_sl": max((abs(d["d_sl"]) for d in param_deltas), default=0.0),
            "max_abs_d_tp1": max((abs(d["d_tp1"]) for d in param_deltas), default=0.0),
            "per_record": param_deltas,
        },
        "m1_realized_R": {
            "mean_baseline_R": mean_baseline_R,
            "mean_treatment_R": mean_treatment_R,
            "mean_delta_R": mean_delta_R,
            "stdev_delta_R": statistics.stdev(diffs) if len(diffs) > 1 else 0.0,
            "wilcoxon": wilcoxon,
            "sign_test": sign,
            "baseline_WR": {"wins": b_w, "n": b_n, "wr": b_wr},
            "treatment_WR": {"wins": t_w, "n": t_n, "wr": t_wr},
            "per_record": paired_R,
        },
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "threshold": "+0.10R/trade lift OR -0.05R kill",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(COMPARISON_OUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {COMPARISON_OUT}")
    print(f"\n=== F27 PROTOTYPE VERDICT: {verdict} ===")
    print(f"Mean realized-R delta: {mean_delta_R:+.4f}R/trade")
    print(f"Baseline mean R: {mean_baseline_R:+.4f}, Treatment mean R: {mean_treatment_R:+.4f}")
    print(f"WR baseline: {b_w}/{b_n}={b_wr*100:.1f}% | treatment: {t_w}/{t_n}={t_wr*100:.1f}%")
    print(f"Wilcoxon p (two-sided): {wilcoxon['p_two_sided']:.4f}")
    print(f"Sign test p (two-sided): {sign['p_two_sided']:.4f}")
    print(f"Decision flips: {flip_2x2}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
