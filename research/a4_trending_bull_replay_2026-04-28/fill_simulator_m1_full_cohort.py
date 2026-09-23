"""A4 Stage 2.5+ — Full-cohort M1 fill simulator using CURRENT (post-FA-2) AI emissions.

Extends fill_simulator_m1.py from the n=4 historically-filled subset to the full
n=11 cohort. Uses the *current* trade_parameters from replay_outcomes.jsonl
(post-FA-2 prompt, non-zero buffers), not the historical zero-buffer values.

Methodology (mirrors fill_simulator_m1.py exactly):
- Treat AI emission as a LIMIT order at entry_price placed at candle_time_utc.
- Walk M1 bars forward from candle_time_utc.
  - LONG: filled when bar.low <= entry_price; thereafter check SL (bar.low<=SL) and TP1 (bar.high>=TP1).
  - SHORT: mirror logic.
- Fill bar itself can also trigger SL/TP within the same bar.
- Same-bar SL+TP collision -> SL first (adverse-first).
- Forward-walk horizon: 192 M15 candles -> 192*15 = 2880 M1 bars (~48h).

Outcomes:
- FILLED_WIN -> realized_r = (tp1 - fill) / risk for LONG (positive)
- FILLED_LOSS -> realized_r = -1.0
- NEVER_FILLED -> realized_r = None
- FILLED_TIME_EXPIRY -> realized_r = MTM at last bar / risk

Output: research/a4_trending_bull_replay_2026-04-28/a4_before_framework_fix_full_cohort_R.json
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
M1_CSV = REPO / "data" / "historical_2026" / "XAUUSD_M1.csv"
RESEARCH_DIR = Path(__file__).parent
REPLAY_OUTCOMES = RESEARCH_DIR / "replay_outcomes.jsonl"
STAGE_2_5_RESULTS = RESEARCH_DIR / "fill_simulation_m1_results.json"
OUT_PATH = RESEARCH_DIR / "a4_before_framework_fix_full_cohort_R.json"
OUT_SUMMARY = RESEARCH_DIR / "a4_before_framework_fix_full_cohort_R_SUMMARY.md"

EXPIRY_M15_CANDLES = 192
EXPIRY_M1_MINUTES = EXPIRY_M15_CANDLES * 15  # 2880


def load_m1():
    """Load M1 candles into a list of dicts (sorted by time, UTC-aware)."""
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
    """First bar with bar.time > t. Returns -1 if none. Linear scan (fine for n=11)."""
    for i, b in enumerate(bars):
        if b["time"] > t:
            return i
    return -1


def simulate_limit(bars, candle_time: datetime, direction: str,
                    limit: float, sl: float, tp1: float,
                    expiry_minutes: int = EXPIRY_M1_MINUTES) -> dict:
    """Simulate forward fill + exit on M1 bars. Mirrors fill_simulator_m1.py semantics."""
    next_idx = find_first_bar_after(bars, candle_time)
    if next_idx == -1:
        return {"outcome": "NO_DATA", "exit_reason": "candle_time after data range"}

    end_scan = min(next_idx + expiry_minutes, len(bars))

    # Fill scan
    fill_idx = -1
    fill_price = None
    for i in range(next_idx, end_scan):
        b = bars[i]
        if direction == "LONG":
            if b["low"] <= limit:
                fill_idx = i
                fill_price = limit
                break
        else:  # SHORT
            if b["high"] >= limit:
                fill_idx = i
                fill_price = limit
                break

    if fill_idx == -1:
        return {
            "outcome": "NEVER_FILLED",
            "realized_r": None,
            "exit_reason": "never_filled",
            "expiry_time": bars[end_scan - 1]["time"].isoformat() if end_scan > 0 else None,
        }

    risk = abs(fill_price - sl)

    # Exit scan from the fill bar onward (volatile bar may also hit SL/TP).
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
            # Same-bar collision: adverse-first (SL wins)
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


def detect_bar_gaps(bars, start_idx: int, end_idx: int, max_gap_minutes: int = 240) -> list:
    """Flag UNEXPECTED M1 bar-time gaps within [start_idx, end_idx).

    Filters out routine session breaks:
    - Daily ~1h break (23:59 -> 01:00 next trading day, ~61min)
    - Weekend gap (Fri close -> Sun/Mon open, ~2880min)
    - Daily ~3.5h break around US session close (21:30 -> 01:00, ~210min)

    Only flags gaps > max_gap_minutes that don't match a known break pattern,
    OR mid-session gaps > 5min within the same trading day.
    """
    gaps = []
    for i in range(start_idx + 1, min(end_idx, len(bars))):
        prev_t = bars[i - 1]["time"]
        cur_t = bars[i]["time"]
        delta = (cur_t - prev_t).total_seconds() / 60.0
        if delta <= 5:  # Normal contiguous bars
            continue

        is_weekend = (prev_t.weekday() == 4 and cur_t.weekday() in (0, 6)) or \
                     (prev_t.weekday() == 5)
        # Daily session break: prev hour late (>=21) or 23:59 -> next day 01:00ish
        is_daily_break = (
            prev_t.hour >= 21 and cur_t.hour <= 2 and
            (cur_t.date() - prev_t.date()).days == 1
        )

        if is_weekend or is_daily_break:
            continue

        if delta > max_gap_minutes or (delta > 5 and not is_daily_break and not is_weekend):
            gaps.append({
                "after_bar": prev_t.isoformat(),
                "before_bar": cur_t.isoformat(),
                "gap_minutes": delta,
            })
    return gaps


def main():
    t_start = time.time()

    # Resolve git HEAD
    head_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO), text=True
    ).strip()

    print(f"Loading M1 from {M1_CSV}")
    bars = load_m1()
    print(f"  loaded {len(bars)} bars, range {bars[0]['time']} -> {bars[-1]['time']}\n")

    # Load Stage 2.5 reference outcomes for sanity-check
    stage_2_5 = {}
    if STAGE_2_5_RESULTS.exists():
        with open(STAGE_2_5_RESULTS, encoding="utf-8") as fh:
            stage_2_5 = json.load(fh)

    # Load all 11 replay outcomes
    replay_rows = []
    with open(REPLAY_OUTCOMES, encoding="utf-8") as fh:
        for line in fh:
            replay_rows.append(json.loads(line))

    per_record = {}
    for row in replay_rows:
        tid = row["trade_id"]
        candle_time = datetime.fromisoformat(row["candle_time_utc"])
        if candle_time.tzinfo is None:
            candle_time = candle_time.replace(tzinfo=timezone.utc)

        tp = row["current"]["trade_parameters"]
        direction = tp["direction"]
        entry = tp["entry_price"]
        sl = tp["stop_loss"]
        tp1 = tp["take_profit_1"]
        sl_buffer = tp.get("sl_buffer_applied", 0.0)

        sl_distance = abs(entry - sl)
        tp1_distance = abs(tp1 - entry)
        tp1_distance_r = tp1_distance / sl_distance if sl_distance > 0 else 0.0

        result = simulate_limit(bars, candle_time, direction, entry, sl, tp1,
                                  expiry_minutes=EXPIRY_M1_MINUTES)

        # Detect bar gaps in the simulation window for caveats (anomalous only)
        next_idx = find_first_bar_after(bars, candle_time)
        caveats = []
        if next_idx != -1:
            # Bound gap-scan window to the actual sim path (entry to exit, or end-of-horizon)
            end_scan = min(next_idx + EXPIRY_M1_MINUTES, len(bars))
            gaps = detect_bar_gaps(bars, next_idx, end_scan, max_gap_minutes=240)
            if gaps:
                gap_summary = ", ".join(
                    f"{g['after_bar']}->{g['before_bar']} ({g['gap_minutes']:.0f}min)"
                    for g in gaps[:3]
                )
                more = f" +{len(gaps)-3} more" if len(gaps) > 3 else ""
                caveats.append(
                    f"Anomalous M1 gap(s) within sim window: {gap_summary}{more}"
                )

        # Stage 2.5 match check (only for the 4 originally-simulated records)
        stage_2_5_match = None
        stage_2_5_outcome = None
        if tid in stage_2_5:
            stage_2_5_outcome = stage_2_5[tid].get("outcome")
            # Match on outcome category (FILLED_WIN/FILLED_LOSS/NEVER_FILLED/STILL_OPEN)
            stage_2_5_match = (result.get("outcome") == stage_2_5_outcome)

        rec = {
            "candle_time_utc": candle_time.isoformat(),
            "direction": direction,
            "entry": entry,
            "sl": sl,
            "tp1": tp1,
            "tp1_distance_r": tp1_distance_r,
            "sl_buffer_applied": sl_buffer,
            "outcome": result.get("outcome"),
            "fill_time": result.get("fill_time"),
            "exit_time": result.get("exit_time"),
            "fill_price": result.get("fill_price"),
            "exit_price": result.get("exit_price"),
            "exit_reason": result.get("exit_reason"),
            "realized_r": result.get("realized_r"),
            "intra_m1_ambiguity": result.get("intra_m1_ambiguity", False),
        }
        if tid in stage_2_5:
            rec["stage_2_5_match"] = stage_2_5_match
            rec["stage_2_5_outcome"] = stage_2_5_outcome
            rec["stage_2_5_realized_r"] = stage_2_5[tid].get("realized_r")
        if caveats:
            rec["caveats"] = caveats

        per_record[tid] = rec

        print(f"{tid}:")
        print(f"  candle_time={candle_time}")
        print(f"  dir={direction} entry={entry} SL={sl} TP1={tp1} buf={sl_buffer} tp1_R={tp1_distance_r:.3f}")
        print(f"  -> outcome={rec['outcome']}  realized_r={rec['realized_r']}")
        if rec.get("fill_time"):
            print(f"  -> fill_time={rec['fill_time']}@{rec['fill_price']}  exit_time={rec.get('exit_time')}@{rec.get('exit_price')}  reason={rec.get('exit_reason')}")
        if tid in stage_2_5:
            print(f"  -> stage_2_5_outcome={stage_2_5_outcome}  match={stage_2_5_match}")
        print()

    # Aggregate
    n = len(per_record)
    n_wins = sum(1 for r in per_record.values() if r["outcome"] == "FILLED_WIN")
    n_losses = sum(1 for r in per_record.values() if r["outcome"] == "FILLED_LOSS")
    n_never = sum(1 for r in per_record.values() if r["outcome"] == "NEVER_FILLED")
    n_open = sum(1 for r in per_record.values() if r["outcome"] == "STILL_OPEN_AT_SIM_END")
    n_filled = n_wins + n_losses + n_open

    realized_filled = [r["realized_r"] for r in per_record.values()
                       if r["outcome"] in ("FILLED_WIN", "FILLED_LOSS", "STILL_OPEN_AT_SIM_END")
                       and r["realized_r"] is not None]
    sum_r_filled = sum(realized_filled)
    mean_r_filled = sum_r_filled / len(realized_filled) if realized_filled else 0.0
    wr_filled = n_wins / n_filled if n_filled > 0 else 0.0

    # n=11 with NEVER_FILLED treated as 0R or -0.5R
    realized_n11_zero = realized_filled + [0.0] * n_never
    realized_n11_minus_half = realized_filled + [-0.5] * n_never
    mean_r_n11_zero = sum(realized_n11_zero) / n if n > 0 else 0.0
    mean_r_n11_minus_half = sum(realized_n11_minus_half) / n if n > 0 else 0.0
    sum_r = sum_r_filled  # never-filled contribute zero PnL

    # Verdict band
    # GREEN: filtered mean R >= +0.30 AND filtered WR >= 50%
    # YELLOW: >= +0.10R but below 50% WR
    # RED: <= +0.05R
    if mean_r_filled >= 0.30 and wr_filled >= 0.50:
        verdict = "GREEN"
    elif mean_r_filled >= 0.10 and wr_filled < 0.50:
        verdict = "YELLOW"
    elif mean_r_filled <= 0.05:
        verdict = "RED"
    else:
        # Fallback: between bands (e.g. mean >= 0.10 and WR >= 50% but mean < 0.30,
        # or mean between 0.05 and 0.10) -> YELLOW
        verdict = "YELLOW"

    aggregate = {
        "n": n,
        "n_filled": n_filled,
        "n_wins": n_wins,
        "n_losses": n_losses,
        "n_open_at_horizon": n_open,
        "n_never_filled": n_never,
        "wr_filled_only": wr_filled,
        "mean_r_filled_only": mean_r_filled,
        "mean_r_n11_with_neverfilled_as_zero": mean_r_n11_zero,
        "mean_r_n11_with_neverfilled_as_minus_half_r": mean_r_n11_minus_half,
        "sum_r": sum_r,
    }

    caveats_global = [
        "M1 same-bar SL+TP collision resolved adverse-first (SL wins).",
        "Forward-walk horizon = 192 M15 candles = 2880 M1 bars (~48h, matches pending-intent expiry).",
        "Uses current (post-FA-2) AI emissions from replay_outcomes.jsonl, NOT historical zero-buffer params.",
        "All 11 records are LONG (cohort=trending_bull, all CANDIDATEs).",
        "STILL_OPEN_AT_SIM_END outcomes use MTM realized R (close at horizon / risk).",
        "Multi-framework dispatch fix is NOT applied (separate branch). This sim represents 'A4 cohort with sl_beyond_ob fix only'.",
    ]

    sim_walltime = time.time() - t_start

    output = {
        "methodology": "M1 fill sim using current (post-FA-2) AI emissions from replay_outcomes.jsonl",
        "main_head_at_sim": head_sha,
        "sim_walltime_s": sim_walltime,
        "sim_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "expiry_m15_candles": EXPIRY_M15_CANDLES,
        "expiry_m1_minutes": EXPIRY_M1_MINUTES,
        "per_record": per_record,
        "aggregate": aggregate,
        "verdict_band": verdict,
        "verdict_reasoning": {
            "mean_r_filled_only": mean_r_filled,
            "wr_filled_only": wr_filled,
            "thresholds": {
                "GREEN": "mean_r_filled >= +0.30R AND wr_filled >= 50%",
                "YELLOW": "mean_r_filled >= +0.10R but wr_filled < 50% (or mid-band)",
                "RED": "mean_r_filled <= +0.05R",
            },
        },
        "caveats": caveats_global,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, default=str)
    print(f"\nWrote {OUT_PATH}")
    print(f"Aggregate: n={n} filled={n_filled} wins={n_wins} losses={n_losses} never_filled={n_never} open={n_open}")
    print(f"  WR (filled only) = {wr_filled:.1%}")
    print(f"  mean R (filled only) = {mean_r_filled:+.3f}")
    print(f"  mean R (n=11, neverfilled=0) = {mean_r_n11_zero:+.3f}")
    print(f"  mean R (n=11, neverfilled=-0.5) = {mean_r_n11_minus_half:+.3f}")
    print(f"  Verdict: {verdict}")
    print(f"  Walltime: {sim_walltime:.2f}s")


if __name__ == "__main__":
    main()
