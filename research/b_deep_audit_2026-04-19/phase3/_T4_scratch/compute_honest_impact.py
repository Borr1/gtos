"""T4 — D1-bias-lag honest per-instrument R impact.

Hypothesis test (H0 vs H1): under per-instrument epsilon + per-day de-correlation,
compute the directional counterfactual R of re-running H4-bias rejects on the
production price stream across 7 instruments.

Inputs:
  - EURUSD: research/t7_live_simulation/EURUSD_t7_simulation.json (804 L2 rejects)
  - NAS100: research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{1..5}
            /NAS100_t7_simulation.json (140 L2 rejects)
  - XAUUSD, US30_cash, USDJPY, GBPJPY, GBPUSD: re-derive L2 rejects from KZ enumeration
    using production `identify_structure` on D1/H4 data (no AI calls needed for prescreen).

Counterfactual:
  - Use H4-bias direction (per zeta's "correct" framing).
  - Entry = signal_candle_close, SL = close -/+ ATR14(M15), TP = close +/- 1.5 * ATR14(M15).
  - Fill check uses per-instrument epsilon from EPSILON_BY_SYMBOL (Tier A fix).
  - Horizon = 16 M15 candles (= 4 hours, matches zeta and reviewer).
  - Per-day de-correlation: at most ONE counterfactual per (symbol, date).
    When multiple L2 rejects fall on the same date, keep the FIRST one chronologically
    (most conservative; mimics operator seeing the first conflict that day).

Bootstrap 95% CI: 5000 resamples of the per-day event list with replacement,
compute R_sum per resample.

Writes results to `results.json` next to this script. The top-level markdown
pulls numbers from this JSON.
"""

from __future__ import annotations

import csv
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, time, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
sys.path.insert(0, str(ROOT))


from src.components.market_state import detect_swings, identify_structure


# ------------------------------------------------------------------
# Per-instrument epsilon (from scripts/simulate_t7_live_period.py:80-89)
# ------------------------------------------------------------------
EPSILON_BY_SYMBOL = {
    "XAUUSD":    0.20,
    "US30":      2.0,
    "US30_cash": 2.0,
    "NAS100":    2.0,
    "USDJPY":    0.02,
    "GBPJPY":    0.02,
    "EURUSD":    0.0002,
    "GBPUSD":    0.0002,
}
DEFAULT_EPSILON = 0.05  # legacy default (for naive replay row)


# ------------------------------------------------------------------
# KZ windows (from simulate_t7_live_period.py:58-67)
# ------------------------------------------------------------------
KZ_WINDOWS = {
    "XAUUSD":    {"london": (time(7, 0), time(10, 30)), "ny": (time(13, 0), time(17, 0))},
    "US30_cash": {"london": (time(8, 0), time(10, 30)), "ny": (time(13, 30), time(16, 0))},
    "US30":      {"london": (time(8, 0), time(10, 30)), "ny": (time(13, 30), time(16, 0))},
    "USDJPY":    {"london": (time(7, 0), time(9, 30)),  "ny": (time(13, 0), time(15, 30)), "tokyo": (time(0, 0), time(3, 0))},
    "GBPJPY":    {"london": (time(7, 0), time(9, 30)),  "ny": (time(13, 0), time(15, 30)), "tokyo": (time(0, 0), time(3, 0))},
    "GBPUSD":    {"london": (time(7, 0), time(12, 0)),  "ny": (time(13, 0), time(15, 30))},
    "EURUSD":    {"london": (time(7, 0), time(12, 0)),  "ny": (time(13, 0), time(15, 30))},
    "NAS100":    {"london": (time(8, 0), time(10, 30)), "ny": (time(13, 30), time(16, 0))},
}


# ------------------------------------------------------------------
# CSV filename resolution (US30_cash data lives in US30_cash_*.csv)
# ------------------------------------------------------------------
def csv_name(symbol: str) -> str:
    return symbol  # data file stem matches symbol as-is


# ------------------------------------------------------------------
# CSV loader (matches scripts/historical_data_loader parse format)
# ------------------------------------------------------------------
def load_csv(symbol: str, tf: str) -> list[dict]:
    p = ROOT / "data" / "historical_2026" / f"{csv_name(symbol)}_{tf}.csv"
    if not p.exists():
        return []
    rows = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = row["time"].strip()
            # normalize to 'YYYY-MM-DD HH:MM:SS'
            if "T" in t:
                t = t.replace("T", " ")
            if t.endswith("Z"):
                t = t[:-1]
            if len(t) == 10:
                t = t + " 00:00:00"
            if len(t) == 16:
                t = t + ":00"
            rows.append({
                "time": t,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            })
    return rows


def dt_of(ts: str) -> datetime:
    # D1 rows may be date-only (e.g. '2026-01-02'), H4/H1/M15 include time.
    t = ts.strip()
    if len(t) == 10:
        t = t + " 00:00:00"
    return datetime.strptime(t, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def in_kz(symbol: str, dt: datetime) -> bool:
    kz = KZ_WINDOWS.get(symbol, KZ_WINDOWS["XAUUSD"])
    t = dt.time()
    for _, (start, end) in kz.items():
        if start <= t < end:
            return True
    return False


# ------------------------------------------------------------------
# ATR14 at M15 idx
# ------------------------------------------------------------------
def atr14(m15: list[dict], idx: int, period: int = 14) -> float:
    if idx < period:
        return 0.0
    tr = []
    for k in range(idx - period, idx):
        h = m15[k + 1]["high"]
        l = m15[k + 1]["low"]
        pc = m15[k]["close"]
        tr.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(tr) / len(tr) if tr else 0.0


# ------------------------------------------------------------------
# Counterfactual replay matching compute_outcome() semantics
# scripts/simulate_t7_live_period.py:491-570
# ------------------------------------------------------------------
def replay(
    m15: list[dict],
    idx: int,
    direction: str,
    entry: float,
    sl: float,
    tp: float,
    epsilon: float,
    horizon: int = 16,
) -> tuple[str, float]:
    """Returns (outcome, r_multiple). outcome in {W, L, U}."""
    candle_close = m15[idx]["close"]
    # Fill check: if entry within epsilon of close, treat as at-market fill.
    entry_filled = abs(entry - candle_close) <= epsilon

    sl_dist = abs(entry - sl)
    if sl_dist == 0:
        return "U", 0.0
    tp_r = abs(tp - entry) / sl_dist  # should be ~1.5

    end = min(len(m15), idx + horizon + 1)
    for j in range(idx + 1, end):
        c = m15[j]
        h, l = c["high"], c["low"]

        if not entry_filled:
            if direction == "LONG":
                if entry < candle_close and l <= entry:
                    entry_filled = True
                elif entry > candle_close and h >= entry:
                    entry_filled = True
            else:  # SHORT
                if entry > candle_close and h >= entry:
                    entry_filled = True
                elif entry < candle_close and l <= entry:
                    entry_filled = True
            if not entry_filled:
                continue

        # Post-fill: check TP/SL. Conservative: if both hit same candle, SL first.
        if direction == "LONG":
            if l <= sl:
                return "L", -1.0
            if h >= tp:
                return "W", tp_r
        else:
            if h >= sl:
                return "L", -1.0
            if l <= tp:
                return "W", tp_r

    return "U", 0.0  # unresolved / UNFILLED / OPEN


# ------------------------------------------------------------------
# Load simulation-sourced L2 rejects (EURUSD, NAS100)
# ------------------------------------------------------------------
_L2_RE = re.compile(r"prescreen:L2_h4_conflict_(\w+)_vs_d1_(\w+)")


def parse_l2(reason: str) -> dict | None:
    m = _L2_RE.match(reason)
    if not m:
        return None
    return {"h4": m.group(1), "d1": m.group(2)}


def l2_from_sim(results: list[dict]) -> list[dict]:
    out = []
    for r in results:
        if r.get("decision") != "NO_TRADE":
            continue
        reason = str(r.get("no_trade_reason", ""))
        parsed = parse_l2(reason)
        if parsed is None:
            continue
        out.append({
            "candle_time": r["candle_time"],
            "h4": parsed["h4"],
            "d1": parsed["d1"],
        })
    return out


def load_eurusd_l2() -> list[dict]:
    p = ROOT / "research" / "t7_live_simulation" / "EURUSD_t7_simulation.json"
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    return l2_from_sim(d["results"])


def load_nas100_l2() -> list[dict]:
    out = []
    base = ROOT / "research" / "t3_1_eurusd_nas100_validation_2026-04-19"
    for i in range(1, 6):
        p = base / f"nas100_slice_{i}" / "NAS100_t7_simulation.json"
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        out += l2_from_sim(d["results"])
    return out


# ------------------------------------------------------------------
# Re-derive L2 rejects for instruments without simulation data
# ------------------------------------------------------------------
def derive_l2_rejects(
    symbol: str,
    m15: list[dict],
    d1: list[dict],
    h4: list[dict],
    start: date = date(2026, 1, 2),
    end: date = date(2026, 4, 10),
) -> list[dict]:
    """Enumerate KZ candles, compute D1/H4 structure directions, flag h4!=d1 conflicts.

    Matches `prescreen_mso` in orchestrator.py:2984-3014:
      - h4_dir != d1_dir where both are in {bullish, bearish} → L2 conflict.
    """
    # Build D1/H4 time indices: D1 uses last N days before candle_time, H4 last N H4 bars
    d1_times = [r["time"] for r in d1]
    h4_times = [r["time"] for r in h4]

    rejects = []
    rejected_at: set[str] = set()

    # Lookbacks: D1=30, H4=80 (production values, data_ingestion.py:38)
    D1_LOOKBACK = 30
    H4_LOOKBACK = 80

    for c in m15:
        dt = dt_of(c["time"])
        d = dt.date()
        if d < start or d > end:
            continue
        if dt.weekday() >= 5:
            continue
        if not in_kz(symbol, dt):
            continue

        # D1 window = all D1 candles strictly before candle_time, last 30
        d1_idx = 0
        for k, r in enumerate(d1):
            if dt_of(r["time"]) >= dt:
                break
            d1_idx = k + 1
        d1_win = d1[max(0, d1_idx - D1_LOOKBACK):d1_idx]
        if len(d1_win) < 4:
            continue
        d1_swings = detect_swings(d1_win, min_bars=2)
        d1_struct = identify_structure(d1_swings)
        d1_dir = d1_struct.direction

        h4_idx = 0
        for k, r in enumerate(h4):
            if dt_of(r["time"]) >= dt:
                break
            h4_idx = k + 1
        h4_win = h4[max(0, h4_idx - H4_LOOKBACK):h4_idx]
        if len(h4_win) < 4:
            continue
        h4_swings = detect_swings(h4_win, min_bars=2)
        h4_struct = identify_structure(h4_swings)
        h4_dir = h4_struct.direction

        d1_clear = d1_dir in ("bullish", "bearish")
        h4_clear = h4_dir in ("bullish", "bearish")
        if d1_clear and h4_clear and h4_dir != d1_dir:
            ts = c["time"]
            if ts in rejected_at:
                continue
            rejected_at.add(ts)
            rejects.append({
                "candle_time": ts.replace(" ", "T") + "Z",
                "h4": h4_dir,
                "d1": d1_dir,
            })
    return rejects


# ------------------------------------------------------------------
# Run counterfactual for one instrument
# ------------------------------------------------------------------
def run_counterfactual(
    symbol: str,
    rejects: list[dict],
    m15: list[dict],
    epsilon: float,
) -> dict:
    """Replay each reject and return stats. `dir_source` is always H4 per zeta."""
    # Build m15 index by normalized candle_time
    idx_by_ts = {c["time"]: i for i, c in enumerate(m15)}

    events = []  # list of (date, candle_time, R_h4, outcome_h4, R_d1, outcome_d1)
    unresolved = 0
    missing_idx = 0
    missing_atr = 0

    for r in rejects:
        ts_raw = r["candle_time"]
        # Normalize to 'YYYY-MM-DD HH:MM:SS'
        t = ts_raw.replace("T", " ").rstrip("Z")
        if len(t) == 16:
            t = t + ":00"
        # Also try without trailing offset for tolerance
        idx = idx_by_ts.get(t)
        if idx is None:
            missing_idx += 1
            continue
        atr = atr14(m15, idx)
        if atr <= 0:
            missing_atr += 1
            continue
        close = m15[idx]["close"]

        # H4-direction counterfactual
        h4_dir = "LONG" if r["h4"] == "bullish" else "SHORT"
        if h4_dir == "LONG":
            entry, sl, tp = close, close - atr, close + 1.5 * atr
        else:
            entry, sl, tp = close, close + atr, close - 1.5 * atr
        out_h4, R_h4 = replay(m15, idx, h4_dir, entry, sl, tp, epsilon)

        # D1-direction counterfactual
        d1_dir = "LONG" if r["d1"] == "bullish" else "SHORT"
        if d1_dir == "LONG":
            entry2, sl2, tp2 = close, close - atr, close + 1.5 * atr
        else:
            entry2, sl2, tp2 = close, close + atr, close - 1.5 * atr
        out_d1, R_d1 = replay(m15, idx, d1_dir, entry2, sl2, tp2, epsilon)

        events.append({
            "date": t[:10],
            "candle_time": t,
            "h4_dir": r["h4"],
            "d1_dir": r["d1"],
            "R_h4": R_h4,
            "out_h4": out_h4,
            "R_d1": R_d1,
            "out_d1": out_d1,
        })

    # All-sample stats (H4 replay)
    R_sum_all = sum(e["R_h4"] for e in events)
    w_all = sum(1 for e in events if e["out_h4"] == "W")
    l_all = sum(1 for e in events if e["out_h4"] == "L")
    u_all = sum(1 for e in events if e["out_h4"] == "U")

    # Per-day de-correlation (keep first reject per date)
    by_day: dict[str, dict] = {}
    for e in events:
        if e["date"] not in by_day:
            by_day[e["date"]] = e
    per_day_events = list(by_day.values())
    R_sum_day = sum(e["R_h4"] for e in per_day_events)
    w_day = sum(1 for e in per_day_events if e["out_h4"] == "W")
    l_day = sum(1 for e in per_day_events if e["out_h4"] == "L")
    u_day = sum(1 for e in per_day_events if e["out_h4"] == "U")

    # Bootstrap 95% CI on per-day R_sum
    def boot_ci(sample: list[float], n_boot: int = 5000, seed: int = 42) -> tuple[float, float]:
        if not sample:
            return 0.0, 0.0
        rng = random.Random(seed)
        n = len(sample)
        sums = []
        for _ in range(n_boot):
            s = 0.0
            for _ in range(n):
                s += sample[rng.randrange(n)]
            sums.append(s)
        sums.sort()
        return sums[int(0.025 * n_boot)], sums[int(0.975 * n_boot)]

    per_day_rs = [e["R_h4"] for e in per_day_events]
    ci_lo, ci_hi = boot_ci(per_day_rs)

    return {
        "symbol": symbol,
        "n_rejects_raw": len(rejects),
        "n_replayed": len(events),
        "missing_idx": missing_idx,
        "missing_atr": missing_atr,
        "distinct_days": len(by_day),
        # Full-sample H4 replay
        "all_W": w_all, "all_L": l_all, "all_U": u_all,
        "R_sum_all": R_sum_all,
        # Per-day H4 replay
        "day_W": w_day, "day_L": l_day, "day_U": u_day,
        "R_sum_day": R_sum_day,
        "day_ci95_lo": ci_lo, "day_ci95_hi": ci_hi,
        # Events list (optional; can be large)
        "per_day_events": per_day_events,
    }


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    configs = {
        "EURUSD": {"load_l2": load_eurusd_l2},
        "NAS100": {"load_l2": load_nas100_l2},
        "XAUUSD": {"load_l2": None},
        "US30_cash": {"load_l2": None},
        "USDJPY": {"load_l2": None},
        "GBPJPY": {"load_l2": None},
        "GBPUSD": {"load_l2": None},
    }

    all_results = {}

    for symbol, cfg in configs.items():
        print(f"\n=== {symbol} ===", flush=True)
        m15 = load_csv(symbol, "M15")
        if not m15:
            print(f"  No M15 data for {symbol}")
            continue
        d1 = load_csv(symbol, "D1")
        h4 = load_csv(symbol, "H4")

        if cfg["load_l2"] is not None:
            rejects = cfg["load_l2"]()
            source = "simulation_json"
        else:
            rejects = derive_l2_rejects(symbol, m15, d1, h4)
            source = "re_derived"
        print(f"  L2 rejects ({source}): n={len(rejects)}")

        epsilon = EPSILON_BY_SYMBOL.get(symbol, DEFAULT_EPSILON)
        # Full honest (per-instrument epsilon)
        res_honest = run_counterfactual(symbol, rejects, m15, epsilon)
        # Naive (default eps=0.05, matches zeta's original)
        res_naive = run_counterfactual(symbol, rejects, m15, DEFAULT_EPSILON)

        combined = {
            "source": source,
            "epsilon_honest": epsilon,
            "epsilon_naive": DEFAULT_EPSILON,
            "n_rejects_raw": res_honest["n_rejects_raw"],
            "n_replayed": res_honest["n_replayed"],
            "missing_idx": res_honest["missing_idx"],
            "missing_atr": res_honest["missing_atr"],
            "distinct_days": res_honest["distinct_days"],
            # Naive (eps=0.05, full-sample)
            "R_sum_naive_all": res_naive["R_sum_all"],
            "R_sum_naive_day": res_naive["R_sum_day"],
            "naive_all_W": res_naive["all_W"], "naive_all_L": res_naive["all_L"], "naive_all_U": res_naive["all_U"],
            "naive_day_W": res_naive["day_W"], "naive_day_L": res_naive["day_L"], "naive_day_U": res_naive["day_U"],
            # Honest full-sample
            "R_sum_honest_all": res_honest["R_sum_all"],
            "honest_all_W": res_honest["all_W"], "honest_all_L": res_honest["all_L"], "honest_all_U": res_honest["all_U"],
            # Honest per-day de-correlated (primary)
            "R_sum_honest_day": res_honest["R_sum_day"],
            "honest_day_W": res_honest["day_W"],
            "honest_day_L": res_honest["day_L"],
            "honest_day_U": res_honest["day_U"],
            "honest_day_ci95_lo": res_honest["day_ci95_lo"],
            "honest_day_ci95_hi": res_honest["day_ci95_hi"],
        }
        all_results[symbol] = combined

        print(f"  epsilon honest={epsilon} naive={DEFAULT_EPSILON}")
        print(f"  n_replayed={combined['n_replayed']} distinct_days={combined['distinct_days']}")
        print(f"  naive eps=0.05 full: W={combined['naive_all_W']} L={combined['naive_all_L']} U={combined['naive_all_U']} R={combined['R_sum_naive_all']:+.2f}")
        print(f"  honest eps full:     W={combined['honest_all_W']} L={combined['honest_all_L']} U={combined['honest_all_U']} R={combined['R_sum_honest_all']:+.2f}")
        print(f"  honest per-day:      W={combined['honest_day_W']} L={combined['honest_day_L']} U={combined['honest_day_U']} R={combined['R_sum_honest_day']:+.2f} "
              f"CI95=[{combined['honest_day_ci95_lo']:+.2f}, {combined['honest_day_ci95_hi']:+.2f}]")

    out_path = Path(__file__).parent / "results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
