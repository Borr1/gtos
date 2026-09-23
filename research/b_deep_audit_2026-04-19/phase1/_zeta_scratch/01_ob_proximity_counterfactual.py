"""
Zeta counterfactual: were the 542 NAS100 pre-AI ob_proximity rejects hiding winners?

For each reject: we DON'T know the AI would have said CANDIDATE — we simulate what
would have happened IF an AI had picked a LONG or SHORT at the nearest H1 OB boundary
using rough production defaults:
  - entry = nearest H1 OB midpoint (for LONG, below current; for SHORT, above)
  - stop  = OB opposite boundary (below low for LONG)
  - TP    = entry +/- 1.5R
  - forward replay the M15 candles; check if TP hit before SL within 4h or 12h

This is EXPLORATORY. It establishes an upper bound for "edge leaked by the filter".
Real leak would require AI to actually emit CANDIDATEs for these rejects.

Outputs to stdout: ob_proximity_counterfactual.json + a summary table.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
NAS_SLICES = [
    ROOT / "research" / "t3_1_eurusd_nas100_validation_2026-04-19" / f"nas100_slice_{i}" / "NAS100_t7_simulation.json"
    for i in range(1, 6)
]
XAU_SIM = ROOT / "research" / "t7_live_simulation" / "all_results_jan_apr10.json"
EUR_SIM = ROOT / "research" / "t7_live_simulation" / "EURUSD_t7_simulation.json"


def load_results(paths: list[Path]) -> list[dict]:
    results = []
    for p in paths:
        if not p.exists():
            print(f"[WARN] missing: {p}")
            continue
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and "results" in d:
            results += d["results"]
        elif isinstance(d, list):
            results += d
        else:
            print(f"[WARN] unknown shape: {p}")
    return results


def load_csv(path: Path) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["time"] = row["time"].strip()
            row["open"] = float(row["open"])
            row["high"] = float(row["high"])
            row["low"] = float(row["low"])
            row["close"] = float(row["close"])
            rows.append(row)
    return rows


def parse_time(t: str) -> datetime:
    # handle both '2026-01-02T13:15:00Z' and '2026-01-02 13:15:00'
    t = t.strip()
    if t.endswith("Z"):
        t = t[:-1]
    t = t.replace("T", " ")
    return datetime.fromisoformat(t).replace(tzinfo=timezone.utc)


def m15_index_by_time(m15: list[dict]) -> dict[str, int]:
    return {r["time"]: i for i, r in enumerate(m15)}


def forward_replay_outcome(
    m15: list[dict],
    start_time: datetime,
    direction: str,
    entry: float,
    sl: float,
    tp: float,
    horizon_hours: int,
) -> tuple[str, int]:
    """
    Deterministic forward replay.
    Convention: start_time is the ORIGINAL candle close (signal candle); we step
    forward from the NEXT candle and check SL/TP wick hits.

    Returns (outcome, candles_elapsed).
        outcome in {'W', 'L', 'U'} (U = unresolved within horizon)
    """
    # Find start index
    ts = start_time.strftime("%Y-%m-%d %H:%M:%S")
    idx = None
    for i, c in enumerate(m15):
        if c["time"] == ts:
            idx = i
            break
    if idx is None:
        return "U", 0

    horizon_candles = horizon_hours * 4  # M15
    end_idx = min(len(m15), idx + horizon_candles + 1)

    # Assume FILLED instantly at entry for counterfactual (conservative).
    for j in range(idx + 1, end_idx):
        c = m15[j]
        if direction == "LONG":
            # Check if SL hit before TP on THIS candle
            sl_hit = c["low"] <= sl
            tp_hit = c["high"] >= tp
            if sl_hit and tp_hit:
                # Ambiguous — assume SL first (conservative)
                return "L", j - idx
            if sl_hit:
                return "L", j - idx
            if tp_hit:
                return "W", j - idx
        elif direction == "SHORT":
            sl_hit = c["high"] >= sl
            tp_hit = c["low"] <= tp
            if sl_hit and tp_hit:
                return "L", j - idx
            if sl_hit:
                return "L", j - idx
            if tp_hit:
                return "W", j - idx
    return "U", end_idx - idx


def main():
    nas_results = load_results(NAS_SLICES)
    nas_m15 = load_csv(ROOT / "data" / "historical_2026" / "NAS100_M15.csv")
    print(f"NAS100: loaded {len(nas_results)} sim records, {len(nas_m15)} M15 candles")

    # Isolate ob_proximity rejects
    ob_rejects = [
        r for r in nas_results
        if r.get("decision") == "NO_TRADE"
        and (r.get("no_trade_reason") or "").startswith("ob_proximity:")
    ]
    print(f"NAS100 ob_proximity rejects: {len(ob_rejects)}")

    # Sub-breakdown of reasons
    reason_breakdown = Counter()
    for r in ob_rejects:
        rsn = r.get("no_trade_reason", "")
        if "no_unmitigated_obs" in rsn:
            reason_breakdown["no_unmitigated_obs"] += 1
        elif "price_far_from_ob" in rsn:
            # extract pct
            try:
                pct = float(rsn.split("_")[-1].rstrip("pct"))
            except Exception:
                pct = -1.0
            if pct < 1.5:
                reason_breakdown["far_1.0-1.5pct"] += 1
            elif pct < 2.0:
                reason_breakdown["far_1.5-2.0pct"] += 1
            elif pct < 3.0:
                reason_breakdown["far_2.0-3.0pct"] += 1
            else:
                reason_breakdown["far_3.0pct+"] += 1
        else:
            reason_breakdown[rsn[:30]] += 1
    print("NAS100 ob_proximity reason sub-breakdown:")
    for k, v in reason_breakdown.most_common():
        print(f"  {k}: {v}")

    # COUNTERFACTUAL: for each reject, replay assuming the BIAS is AI direction
    # (we don't know AI's choice — use deterministic bias as best proxy)
    # Goal: does forward price from the reject candle hit 1.5R in the bias direction within 4h/12h?
    # Since we don't have OB coords in the JSON record (NO_TRADE has no trade_parameters),
    # we use: ATR-based SL distance (1 ATR) and 1.5R TP.
    # We need M15 ATR - estimate via last 14 candles.

    def atr14(m15: list[dict], idx: int, period: int = 14) -> float:
        if idx < period:
            return 0.0
        tr = []
        for k in range(idx - period, idx):
            h, l = m15[k + 1]["high"], m15[k + 1]["low"]
            pc = m15[k]["close"]
            tr.append(max(h - l, abs(h - pc), abs(l - pc)))
        return sum(tr) / len(tr) if tr else 0.0

    # Use bias_source to infer direction — but NO_TRADE records lack bias_source too
    # Fallback: last H1 structure or explicit bias field on the record
    # Since records don't have bias, we probe BOTH directions and report separately
    # — this is a weak counterfactual but sets an UPPER bound.

    def replay_both(results, m15_csv, label):
        outcomes = {"LONG": Counter(), "SHORT": Counter()}
        r_sums = {"LONG": 0.0, "SHORT": 0.0}
        n_valid = 0
        n_skipped = 0
        m15_idx = {c["time"]: i for i, c in enumerate(m15_csv)}
        for r in results:
            ts = r.get("candle_time", "")
            if ts.endswith("Z"):
                ts = ts[:-1]
            ts = ts.replace("T", " ")
            idx = m15_idx.get(ts)
            if idx is None:
                n_skipped += 1
                continue
            n_valid += 1
            signal_close = m15_csv[idx]["close"]
            atr = atr14(m15_csv, idx)
            if atr <= 0:
                n_skipped += 1
                n_valid -= 1
                continue
            # 4h replay
            for horizon in (4, 12):
                for direction in ("LONG", "SHORT"):
                    if direction == "LONG":
                        entry, sl, tp = signal_close, signal_close - atr, signal_close + 1.5 * atr
                    else:
                        entry, sl, tp = signal_close, signal_close + atr, signal_close - 1.5 * atr
                    start_dt = parse_time(ts + ("Z" if "T" not in ts else ""))
                    out, _ = forward_replay_outcome(
                        m15_csv, start_dt, direction, entry, sl, tp, horizon
                    )
                    outcomes[direction][(horizon, out)] += 1
                    if out == "W":
                        r_sums[direction] += 1.5
                    elif out == "L":
                        r_sums[direction] -= 1.0
        return outcomes, r_sums, n_valid, n_skipped

    print("\n=== NAS100 ob_proximity rejects: both-direction counterfactual ===")
    outcomes, r_sums, n_valid, n_skipped = replay_both(ob_rejects, nas_m15, "NAS100")
    print(f"  valid replays: {n_valid}, skipped (no ts match / no ATR): {n_skipped}")
    for direction in ("LONG", "SHORT"):
        print(f"  -- {direction} --")
        for horizon in (4, 12):
            w = outcomes[direction].get((horizon, "W"), 0)
            l = outcomes[direction].get((horizon, "L"), 0)
            u = outcomes[direction].get((horizon, "U"), 0)
            total = w + l + u
            wr = w / (w + l) if (w + l) > 0 else 0.0
            exp_R = (1.5 * w - 1.0 * l) / total if total > 0 else 0.0
            print(f"     {horizon}h: W={w} L={l} U={u} WR(resolved)={wr:.3f} Exp R/trade={exp_R:+.3f}")

    # Save to JSON
    out = {
        "NAS100_ob_proximity": {
            "n_rejects": len(ob_rejects),
            "reason_breakdown": dict(reason_breakdown),
            "n_valid_replays": n_valid,
            "n_skipped": n_skipped,
            "outcomes": {k: {f"{h}_{o}": v for (h, o), v in d.items()} for k, d in outcomes.items()},
            "r_sums": r_sums,
        }
    }
    out_path = ROOT / "research" / "b_deep_audit_2026-04-19" / "phase1" / "_zeta_scratch" / "01_ob_proximity_counterfactual.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
