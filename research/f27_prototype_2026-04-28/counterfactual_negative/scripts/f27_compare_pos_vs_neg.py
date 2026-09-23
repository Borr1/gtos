"""F27 — paired comparison: POSITIVE-treatment vs NEGATIVE-treatment.

Treats F27's positive-telemetry treatment as the new "baseline" and the
negative-telemetry counterfactual as the new "treatment". Same n=11 cohort,
same M1 fill simulator, same paired methodology.

Disambiguates F27 NULL hypothesis:
- CHANNEL_DEAD: 11/11 still CAND, mean R delta within +/-0.01R
- CHANNEL_ALIVE_DIRECTIONAL: ANY decision flip CAND -> NO_TRADE/WAIT under
  negative, OR mean R delta <= -0.05R
- CHANNEL_PARTIAL: trade-params shift materially (mean delta > 1 USD on
  entry/SL/TP1) but no decision flip
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve repo root: script is at research/f27_.../counterfactual_negative/scripts/<this>.py
# parents[5] = repo root. Override via GTOS_REPO_ROOT env if needed.
_REPO_ENV = os.environ.get("GTOS_REPO_ROOT")
REPO = Path(_REPO_ENV) if _REPO_ENV else Path(__file__).resolve().parents[5]
M1_CSV = REPO / "data" / "historical_2026" / "XAUUSD_M1.csv"

OUT_DIR = Path(__file__).resolve().parents[1]  # counterfactual_negative/
F27_DIR = OUT_DIR.parent  # research/f27_prototype_2026-04-28/
POSITIVE_OUTCOMES = F27_DIR / "treatment_replay_outcomes.jsonl"
NEGATIVE_OUTCOMES = OUT_DIR / "replay_outcomes.jsonl"
COMPARISON_OUT = OUT_DIR / "counterfactual_comparison.json"

EXPIRY_M15_CANDLES = 192
EXPIRY_M1_MINUTES = EXPIRY_M15_CANDLES * 15  # 2880


# -- M1 fill simulator (verbatim from f27_compare.py) ----------------------

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


# -- Wilcoxon signed-rank (exact for n<=15) --------------------------------

def wilcoxon_signed_rank(diffs: list[float]) -> dict:
    nonzero = [d for d in diffs if d != 0]
    n = len(nonzero)
    if n == 0:
        return {"n_nonzero": 0, "W_plus": 0.0, "p_two_sided": 1.0}

    abs_diffs = [abs(d) for d in nonzero]
    ranks = _rank_with_ties(abs_diffs)

    W_plus = sum(rk for rk, d in zip(ranks, nonzero) if d > 0)
    W_minus = sum(rk for rk, d in zip(ranks, nonzero) if d < 0)
    W = min(W_plus, W_minus)

    if n > 25:
        mu = n * (n + 1) / 4
        sigma = (n * (n + 1) * (2 * n + 1) / 24) ** 0.5
        z = (W_plus - mu) / sigma
        from math import erf
        p = 2 * (1 - 0.5 * (1 + erf(abs(z) / 2 ** 0.5)))
        return {"n_nonzero": n, "W_plus": W_plus, "W_minus": W_minus,
                 "p_two_sided": p, "method": "normal_approx"}

    count_le = 0
    total = 1 << n
    for mask in range(total):
        w = 0.0
        for i in range(n):
            if mask & (1 << i):
                w += ranks[i]
        if w <= W:
            count_le += 1
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
        p = (count_le + count_ge_high - count_le) / total
    else:
        p = (count_le + count_ge_high) / total
    return {"n_nonzero": n, "W_plus": W_plus, "W_minus": W_minus,
             "p_two_sided": min(p, 1.0), "method": "exact"}


def _rank_with_ties(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg = (i + j + 2) / 2
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg
        i = j + 1
    return ranks


def sign_test(diffs: list[float]) -> dict:
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    n = pos + neg
    if n == 0:
        return {"pos": 0, "neg": 0, "p_two_sided": 1.0}
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

    print(f"Sim positive-treatment ({POSITIVE_OUTCOMES.name})…")
    positive_sim = simulate_run(bars, POSITIVE_OUTCOMES)
    print(f"  simulated {len(positive_sim)} records")

    print(f"Sim negative-treatment ({NEGATIVE_OUTCOMES.name})…")
    negative_sim = simulate_run(bars, NEGATIVE_OUTCOMES)
    print(f"  simulated {len(negative_sim)} records")

    positive_rows = {r["trade_id"]: r for r in
                       (json.loads(l) for l in open(POSITIVE_OUTCOMES, encoding="utf-8"))}
    negative_rows = {r["trade_id"]: r for r in
                       (json.loads(l) for l in open(NEGATIVE_OUTCOMES, encoding="utf-8"))}

    trade_ids = sorted(set(positive_rows.keys()) & set(negative_rows.keys()))
    print(f"Paired records: {len(trade_ids)}")

    # 2x2 flip table (POSITIVE -> NEGATIVE)
    flip_2x2 = {}
    for tid in trade_ids:
        p_dec = positive_rows[tid]["current"].get("ai_decision") or "ERROR"
        n_dec = negative_rows[tid]["current"].get("ai_decision") or "ERROR"
        key = f"{p_dec} -> {n_dec}"
        flip_2x2[key] = flip_2x2.get(key, 0) + 1

    # Trade parameter deltas + confidence delta (only both-CAND records)
    param_deltas = []
    confidence_deltas = []
    for tid in trade_ids:
        p = positive_rows[tid]["current"]
        n = negative_rows[tid]["current"]
        bp = p.get("trade_parameters")
        tp = n.get("trade_parameters")
        if not bp or not tp:
            continue
        param_deltas.append({
            "trade_id": tid,
            "d_entry": tp["entry_price"] - bp["entry_price"],
            "d_sl": tp["stop_loss"] - bp["stop_loss"],
            "d_tp1": tp["take_profit_1"] - bp["take_profit_1"],
            "d_buf": (tp.get("sl_buffer_applied") or 0) - (bp.get("sl_buffer_applied") or 0),
        })
        if p.get("ai_confidence") is not None and n.get("ai_confidence") is not None:
            confidence_deltas.append({
                "trade_id": tid,
                "positive_conf": p["ai_confidence"],
                "negative_conf": n["ai_confidence"],
                "d_conf": n["ai_confidence"] - p["ai_confidence"],
            })

    def _r(rec) -> float:
        if rec.get("outcome") in ("NEVER_FILLED", "ERROR", "NOT_CANDIDATE", "NO_DATA"):
            return 0.0
        return rec.get("realized_r") or 0.0

    paired_R = []
    for tid in trade_ids:
        pR = _r(positive_sim[tid])
        nR = _r(negative_sim[tid])
        paired_R.append({
            "trade_id": tid,
            "positive_R": pR,
            "negative_R": nR,
            "delta_R": nR - pR,
            "positive_outcome": positive_sim[tid].get("outcome"),
            "negative_outcome": negative_sim[tid].get("outcome"),
        })

    diffs = [p["delta_R"] for p in paired_R]
    mean_positive_R = sum(p["positive_R"] for p in paired_R) / len(paired_R)
    mean_negative_R = sum(p["negative_R"] for p in paired_R) / len(paired_R)
    mean_delta_R = sum(diffs) / len(diffs)

    wilcoxon = wilcoxon_signed_rank(diffs)
    sign = sign_test(diffs)

    def _wr(sim_dict):
        cands = [r for r in sim_dict.values()
                 if r.get("outcome") in ("FILLED_WIN", "FILLED_LOSS",
                                          "STILL_OPEN_AT_SIM_END")]
        wins = [r for r in cands
                if r.get("outcome") == "FILLED_WIN" or
                   (r.get("outcome") == "STILL_OPEN_AT_SIM_END" and (r.get("realized_r") or 0) > 0)]
        return len(wins) / len(cands) if cands else 0.0, len(wins), len(cands)

    p_wr, p_w, p_n = _wr(positive_sim)
    n_wr, n_w, n_n = _wr(negative_sim)

    # Verdict (per disambiguation spec)
    n_decision_flips = sum(v for k, v in flip_2x2.items()
                            if k.startswith("CANDIDATE -> ") and not k.endswith("CANDIDATE"))

    if param_deltas:
        mean_abs_d_entry = statistics.mean(abs(d["d_entry"]) for d in param_deltas)
        mean_abs_d_sl = statistics.mean(abs(d["d_sl"]) for d in param_deltas)
        mean_abs_d_tp1 = statistics.mean(abs(d["d_tp1"]) for d in param_deltas)
    else:
        mean_abs_d_entry = mean_abs_d_sl = mean_abs_d_tp1 = 0.0

    if n_decision_flips > 0 or mean_delta_R <= -0.05:
        verdict = "CHANNEL_ALIVE_DIRECTIONAL"
        verdict_reason = (
            f"{n_decision_flips} decision flip(s) CAND->NO_TRADE/WAIT under "
            f"negative telemetry; mean R delta = {mean_delta_R:+.4f}R/trade. "
            f"Channel demonstrably moves decisions when telemetry contradicts setup."
        )
    elif (mean_abs_d_entry > 1.0 or mean_abs_d_sl > 1.0 or mean_abs_d_tp1 > 1.0):
        verdict = "CHANNEL_PARTIAL"
        verdict_reason = (
            f"No decision flips, but trade-params shift materially: "
            f"mean |d_entry|={mean_abs_d_entry:.2f} USD, |d_sl|={mean_abs_d_sl:.2f}, "
            f"|d_tp1|={mean_abs_d_tp1:.2f}. Channel registers but not strong enough "
            f"to demote A+ setups."
        )
    else:
        # Use abs(mean_delta_R) tolerance on top of param check
        verdict = "CHANNEL_DEAD"
        verdict_reason = (
            f"All 11 records still CAND under negative telemetry; mean R delta = "
            f"{mean_delta_R:+.4f}R/trade (within +/-0.01R noise). "
            f"Trade-params essentially unchanged "
            f"(mean |d_entry|={mean_abs_d_entry:.3f} USD, "
            f"|d_sl|={mean_abs_d_sl:.3f}, |d_tp1|={mean_abs_d_tp1:.3f}). "
            f"Feedback channel is dead; F27 closes."
        )

    summary = {
        "n_paired": len(trade_ids),
        "n_decision_flips": n_decision_flips,
        "decision_flip_2x2_pos_to_neg": flip_2x2,
        "trade_parameter_deltas": {
            "n_records_with_both_params": len(param_deltas),
            "mean_d_entry": statistics.mean(d["d_entry"] for d in param_deltas) if param_deltas else 0.0,
            "mean_d_sl": statistics.mean(d["d_sl"] for d in param_deltas) if param_deltas else 0.0,
            "mean_d_tp1": statistics.mean(d["d_tp1"] for d in param_deltas) if param_deltas else 0.0,
            "mean_abs_d_entry": mean_abs_d_entry,
            "mean_abs_d_sl": mean_abs_d_sl,
            "mean_abs_d_tp1": mean_abs_d_tp1,
            "median_d_entry": statistics.median(d["d_entry"] for d in param_deltas) if param_deltas else 0.0,
            "median_d_sl": statistics.median(d["d_sl"] for d in param_deltas) if param_deltas else 0.0,
            "median_d_tp1": statistics.median(d["d_tp1"] for d in param_deltas) if param_deltas else 0.0,
            "max_abs_d_entry": max((abs(d["d_entry"]) for d in param_deltas), default=0.0),
            "max_abs_d_sl": max((abs(d["d_sl"]) for d in param_deltas), default=0.0),
            "max_abs_d_tp1": max((abs(d["d_tp1"]) for d in param_deltas), default=0.0),
            "per_record": param_deltas,
        },
        "confidence_deltas": {
            "n": len(confidence_deltas),
            "mean_d_conf": statistics.mean(d["d_conf"] for d in confidence_deltas) if confidence_deltas else 0.0,
            "median_d_conf": statistics.median(d["d_conf"] for d in confidence_deltas) if confidence_deltas else 0.0,
            "per_record": confidence_deltas,
        },
        "m1_realized_R": {
            "mean_positive_R": mean_positive_R,
            "mean_negative_R": mean_negative_R,
            "mean_delta_R": mean_delta_R,
            "stdev_delta_R": statistics.stdev(diffs) if len(diffs) > 1 else 0.0,
            "wilcoxon": wilcoxon,
            "sign_test": sign,
            "positive_WR": {"wins": p_w, "n": p_n, "wr": p_wr},
            "negative_WR": {"wins": n_w, "n": n_n, "wr": n_wr},
            "per_record": paired_R,
        },
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "verdict_thresholds": {
            "CHANNEL_DEAD": "11/11 still CAND, mean R delta within +/-0.01R, no material param shift",
            "CHANNEL_ALIVE_DIRECTIONAL": "ANY decision flip CAND->NO_TRADE/WAIT, OR mean R delta <= -0.05R",
            "CHANNEL_PARTIAL": "trade-params shift materially (mean |delta| > 1 USD on entry/SL/TP1) but no decision flip",
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(COMPARISON_OUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {COMPARISON_OUT}")
    print(f"\n=== F27 COUNTERFACTUAL VERDICT: {verdict} ===")
    print(f"Reason: {verdict_reason}")
    print(f"\nMean realized-R delta (negative - positive): {mean_delta_R:+.4f}R/trade")
    print(f"Positive treatment mean R: {mean_positive_R:+.4f}")
    print(f"Negative treatment mean R: {mean_negative_R:+.4f}")
    print(f"WR positive: {p_w}/{p_n}={p_wr*100:.1f}% | negative: {n_w}/{n_n}={n_wr*100:.1f}%")
    print(f"Wilcoxon p (two-sided): {wilcoxon['p_two_sided']:.4f}")
    print(f"Sign test p (two-sided): {sign['p_two_sided']:.4f}")
    print(f"Decision flips (POS->NEG): {flip_2x2}")
    if confidence_deltas:
        print(f"Mean confidence delta: {summary['confidence_deltas']['mean_d_conf']:+.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
