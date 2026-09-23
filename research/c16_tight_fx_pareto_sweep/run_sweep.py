"""C16 v3 — Per-instrument tight-FX override Pareto sweep.

Sweeps (atr_multiplier, min_ticks) for SL buffer on EURUSD/GBPUSD/USDJPY
trade-record cohorts. Targets the realized-R impact of widening the AI's
proposed SL via prompt-side knobs.

DATA AVAILABILITY (verified 2026-04-27):
  EURUSD: 0 trade records (no live evaluations dir, no trade_records dir)
          → reported as NO_DATA per stop-condition.
  GBPUSD: 28 CANDIDATE records (2026-04-13 → 2026-04-22)
  USDJPY: 44 CANDIDATE records (2026-04-07 → 2026-04-17)
  GBPJPY: NOT in tight-FX scope; excluded.

METHODOLOGY:
  1. Load every CANDIDATE trade-record per symbol.
  2. Extract: direction, entry, AI-proposed SL/TP, AI's anchored OB
     (closest unmitigated bullish/bearish OB on correct side of entry to
     AI's chosen SL), gate-matched OB (from L2 detail), H1 ATR_14, candle_time.
  3. For each (atr_mult, min_ticks) cell:
        new_buffer = max(atr_mult * H1_ATR, min_ticks * tick_size)
        new_sl     = ai_ob_low - new_buffer  (LONG)
                     ai_ob_high + new_buffer (SHORT)
        l2_pass    = new_sl <= ai_ob_low - sl_beyond_ob_tick_floor*tick (LONG)
        new_rr     = |tp1 - entry| / |entry - new_sl|
        accepted   = l2_pass AND new_rr >= 1.5
  4. For ACCEPTED cells, walk M15 OHLCV forward (max 200 bars ≈ 50 hours)
     using first-touch resolution; conservative: SL+TP same bar → SL hit.
  5. Per-cell aggregates: acceptance_rate, mean_r, win_rate, Wilson CI on WR,
     bootstrap 95% CI on mean_r (1000 resamples).
  6. Pareto frontier per instrument: maximize (acceptance_rate, mean_r).
     Cells with n_resolved < 5 → marked NO_DATA per task stop-condition.
  7. Cross-instrument synthesis: rank cells by mean (acceptance × mean_R) per
     symbol, then min EV across symbols → robust shared-config candidate.

NO PANDAS — pandas import is ~3min on this Windows host. CSV via stdlib.
READ-ONLY. NO PRODUCTION CONFIG CHANGES. NO MERGE. ZERO API.
"""

import csv
import datetime as dt
import glob
import json
import os
import random
import sys
from bisect import bisect_left
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
TRADE_RECORDS = REPO / "knowledge_base" / "trade_records"
OHLCV_DIR = REPO / "data" / "historical_2026"
OUT_DIR = REPO / "research" / "c16_tight_fx_pareto_sweep"
OUT_DIR.mkdir(parents=True, exist_ok=True)

INSTRUMENTS = ["EURUSD", "GBPUSD", "USDJPY"]

TICK_SIZE = {
    "EURUSD": 0.00001,
    "GBPUSD": 0.00001,
    "USDJPY": 0.001,
}

# L2 gate floor (post-FA-2 / ADR-006 default: 1 tick)
SL_BEYOND_OB_TICK_FLOOR = 1
MIN_RR = 1.5
WALK_WINDOW_BARS = 480       # ~5 days on M15 (extended to capture pullback fills)
MIN_RESOLVED_PER_CELL = 5    # task stop-condition: NO_DATA below this
BOOTSTRAP_N = 1000

# Sweep grid
ATR_MULTS = [0.25, 0.30, 0.40, 0.50, 0.60]
MIN_TICKS = [3, 5, 8, 12]

random.seed(42)

# ---------------------------------------------------------------------------
# OHLCV loader (stdlib only)
# ---------------------------------------------------------------------------

_ohlcv_cache: dict = {}

def _parse_iso(ts: str) -> dt.datetime:
    """Naive UTC parser. Strips tz if present."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    if "+" in ts and "T" in ts:
        # ISO 8601 with offset
        try:
            d = dt.datetime.fromisoformat(ts)
            if d.tzinfo is not None:
                d = d.astimezone(dt.timezone.utc).replace(tzinfo=None)
            return d
        except Exception:
            pass
    if "T" in ts:
        try:
            return dt.datetime.fromisoformat(ts)
        except Exception:
            pass
    return dt.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


def load_ohlcv(symbol: str, tf: str = "M15"):
    """Return (times, opens, highs, lows, closes) parallel lists."""
    key = (symbol, tf)
    if key in _ohlcv_cache:
        return _ohlcv_cache[key]
    fp = OHLCV_DIR / f"{symbol}_{tf}.csv"
    if not fp.exists():
        _ohlcv_cache[key] = None
        return None
    times, opens, highs, lows, closes = [], [], [], [], []
    with open(fp, encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            try:
                t = _parse_iso(row["time"])
                lo = float(row["low"]); hi = float(row["high"])
                op = float(row["open"]); cl = float(row["close"])
                times.append(t); opens.append(op); highs.append(hi)
                lows.append(lo); closes.append(cl)
            except Exception:
                continue
    _ohlcv_cache[key] = (times, opens, highs, lows, closes)
    return _ohlcv_cache[key]


def walk_forward(symbol: str, candle_time: str, direction: str,
                 entry: float, sl: float, tp: float,
                 max_bars: int = WALK_WINDOW_BARS) -> tuple[Optional[float], str]:
    """First-touch walk on M15. Returns (realized R or None, status code).

    status codes:
      "tp"          : TP1 first → +R_if_tp
      "sl"          : SL first → -1R
      "no_fill"     : entry never reached within window
      "no_resolve"  : entry filled but no SL/TP within window
      "no_data"     : OHLCV missing or invalid
      "no_risk"     : risk <= 0 (degenerate)
      "before_ts"   : candle_time after end of OHLCV

    Conservative: same-bar SL+TP touch -> assume SL hit.
    Risk model: R = (tp - entry)/(entry - sl) for LONG; SL hit = -1R.
    Limit-fill: entry filled when bar range covers entry price.
    """
    bars = load_ohlcv(symbol, "M15")
    if bars is None:
        return (None, "no_data")
    times, opens, highs, lows, closes = bars
    try:
        ts = _parse_iso(candle_time)
    except Exception:
        return (None, "no_data")

    start = bisect_left(times, ts)
    if start >= len(times):
        return (None, "before_ts")
    end = min(start + max_bars, len(times) - 1)
    risk = abs(entry - sl)
    if risk <= 0:
        return (None, "no_risk")
    target = abs(tp - entry)
    R_if_tp = target / risk

    filled = False
    for i in range(start, end + 1):
        lo = lows[i]; hi = highs[i]
        if not filled:
            if lo <= entry <= hi:
                filled = True
                if direction == "LONG":
                    sl_hit = lo <= sl; tp_hit = hi >= tp
                else:
                    sl_hit = hi >= sl; tp_hit = lo <= tp
                if sl_hit and tp_hit:
                    return (-1.0, "sl")
                if sl_hit:
                    return (-1.0, "sl")
                if tp_hit:
                    return (R_if_tp, "tp")
            continue
        if direction == "LONG":
            sl_hit = lo <= sl; tp_hit = hi >= tp
        else:
            sl_hit = hi >= sl; tp_hit = lo <= tp
        if sl_hit and tp_hit:
            return (-1.0, "sl")
        if sl_hit:
            return (-1.0, "sl")
        if tp_hit:
            return (R_if_tp, "tp")
    return (None, "no_fill" if not filled else "no_resolve")


# ---------------------------------------------------------------------------
# Record extraction
# ---------------------------------------------------------------------------

def extract_records(symbol: str) -> list[dict]:
    """Pull CANDIDATE records with full geometric context."""
    sym_dir = TRADE_RECORDS / symbol
    if not sym_dir.exists():
        return []
    results = []
    paths = sorted(glob.glob(str(sym_dir / "*.json")))
    for fp in paths:
        try:
            with open(fp, encoding="utf-8") as f:
                r = json.load(f)
        except Exception:
            continue
        ai = r.get("ai_response", {}) or {}
        if not isinstance(ai, dict) or ai.get("decision") != "CANDIDATE":
            continue
        tp = r.get("trade_parameters", {}) or {}
        entry = tp.get("entry_price")
        ai_sl = tp.get("stop_loss")
        tp1 = tp.get("take_profit_1")
        direction = tp.get("direction")
        if not (entry and ai_sl and tp1 and direction):
            continue

        mso = r.get("mso", {}) or {}
        h1 = mso.get("timeframes", {}).get("H1", {}) if isinstance(mso, dict) else {}
        h1_atr = h1.get("atr_14")
        if not h1_atr or h1_atr <= 0:
            continue
        meta = r.get("metadata", {}) or {}
        candle_time = meta.get("candle_time") or meta.get("timestamp_utc")
        if not candle_time:
            continue

        # Gate-matched OB
        dp = r.get("decision_pipeline", {}) or {}
        l2 = dp.get("level2_verification", {}) or {}
        gate_ob_low = gate_ob_high = None
        ob_match_status = None
        for c in l2.get("checks", []) or []:
            name = c.get("name")
            mso_val = c.get("mso_value")
            if name == "h1_poi_exists" and isinstance(mso_val, str) and "-" in mso_val:
                try:
                    a, b = mso_val.split("-")
                    a, b = float(a), float(b)
                    gate_ob_low, gate_ob_high = min(a, b), max(a, b)
                except Exception:
                    pass
            if name == "sl_beyond_ob":
                ob_match_status = c.get("status")

        # AI-anchored OB: structurally valid (correct side of entry),
        # closest anchored boundary to AI's chosen SL.
        obs = h1.get("order_blocks", []) or []
        need_type = "bullish" if direction == "LONG" else "bearish"
        cand_obs = [o for o in obs
                    if o.get("type") == need_type and not o.get("mitigated", False)]
        if direction == "LONG":
            cand_obs = [o for o in cand_obs if o["high"] <= entry]
            anchor_field = "low"
        else:
            cand_obs = [o for o in cand_obs if o["low"] >= entry]
            anchor_field = "high"

        ai_ob_low = ai_ob_high = None
        if cand_obs:
            anchor_price = float(ai_sl)
            tol = abs(entry) * 0.01
            within = [o for o in cand_obs
                      if abs(o[anchor_field] - anchor_price) <= tol]
            if within:
                pick = min(within,
                           key=lambda o: abs(o[anchor_field] - anchor_price))
            else:
                pick = min(cand_obs,
                           key=lambda o: abs((o["low"] + o["high"]) / 2 - entry))
            ai_ob_low, ai_ob_high = float(pick["low"]), float(pick["high"])

        # Fallbacks
        if gate_ob_low is None and ai_ob_low is None:
            continue
        if gate_ob_low is None:
            gate_ob_low, gate_ob_high = ai_ob_low, ai_ob_high
        if ai_ob_low is None:
            ai_ob_low, ai_ob_high = gate_ob_low, gate_ob_high

        results.append({
            "file": os.path.basename(fp),
            "candle_time": candle_time,
            "direction": direction,
            "entry": float(entry),
            "ai_sl": float(ai_sl),
            "tp1": float(tp1),
            "ai_ob_low": float(ai_ob_low),
            "ai_ob_high": float(ai_ob_high),
            "gate_ob_low": float(gate_ob_low),
            "gate_ob_high": float(gate_ob_high),
            "h1_atr": float(h1_atr),
            "ai_sl_buffer_applied": float(tp.get("sl_buffer_applied") or 0.0),
            "ob_match_status": ob_match_status,
            "ob_match_mismatch": (
                ai_ob_low is not None
                and gate_ob_low is not None
                and abs(ai_ob_low - gate_ob_low) > 1e-6
            ),
        })
    return results


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------

def sweep_record(rec: dict, symbol: str) -> list[dict]:
    """Score every (atr_mult, min_ticks) cell against this record.

    L2 acceptance computed against AI's anchored OB.
    Gate-matched OB acceptance also reported as `gate_legacy_pass`.
    """
    tick = TICK_SIZE[symbol]
    floor = SL_BEYOND_OB_TICK_FLOOR * tick
    out = []
    for atr_mult in ATR_MULTS:
        for mt in MIN_TICKS:
            new_buffer = max(atr_mult * rec["h1_atr"], mt * tick)
            if rec["direction"] == "LONG":
                new_sl = rec["ai_ob_low"] - new_buffer
                l2_pass = new_sl <= rec["ai_ob_low"] - floor
                gate_legacy_pass = new_sl <= rec["gate_ob_low"] - floor
            else:
                new_sl = rec["ai_ob_high"] + new_buffer
                l2_pass = new_sl >= rec["ai_ob_high"] + floor
                gate_legacy_pass = new_sl >= rec["gate_ob_high"] + floor

            risk = abs(rec["entry"] - new_sl)
            target = abs(rec["tp1"] - rec["entry"])
            new_rr = target / risk if risk > 0 else 0.0
            rr_pass = new_rr >= MIN_RR
            accepted = l2_pass and rr_pass
            realized_r = None
            walk_status = "skipped"
            if accepted:
                realized_r, walk_status = walk_forward(
                    symbol, rec["candle_time"], rec["direction"],
                    rec["entry"], new_sl, rec["tp1"],
                )
            out.append({
                "file": rec["file"],
                "symbol": symbol,
                "candle_time": rec["candle_time"],
                "atr_mult": atr_mult,
                "min_ticks": mt,
                "new_buffer": new_buffer,
                "new_sl": new_sl,
                "new_rr": new_rr,
                "l2_pass": l2_pass,
                "gate_legacy_pass": gate_legacy_pass,
                "rr_pass": rr_pass,
                "accepted": accepted,
                "realized_r": realized_r,
                "walk_status": walk_status,
                "h1_atr": rec["h1_atr"],
                "direction": rec["direction"],
                "entry": rec["entry"],
                "tp1": rec["tp1"],
                "ai_ob_low": rec["ai_ob_low"],
                "ai_ob_high": rec["ai_ob_high"],
                "gate_ob_low": rec["gate_ob_low"],
                "gate_ob_high": rec["gate_ob_high"],
                "ai_sl": rec["ai_sl"],
                "ob_match_mismatch": rec["ob_match_mismatch"],
            })
    return out


# ---------------------------------------------------------------------------
# Stats helpers (stdlib)
# ---------------------------------------------------------------------------

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z / denom) * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (max(0.0, center - half), min(1.0, center + half))


def bootstrap_mean_ci(values: list[float], n_resample: int = BOOTSTRAP_N,
                      alpha: float = 0.05) -> tuple[float, float]:
    if not values:
        return (float("nan"), float("nan"))
    n = len(values)
    rng = random.Random(42)
    means = []
    for _ in range(n_resample):
        sample = [values[rng.randrange(n)] for __ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = int(n_resample * (alpha / 2))
    hi_idx = int(n_resample * (1 - alpha / 2)) - 1
    return (means[lo_idx], means[hi_idx])


def aggregate_per_cell(rows: list[dict]) -> list[dict]:
    by_cell = defaultdict(list)
    for r in rows:
        by_cell[(r["atr_mult"], r["min_ticks"])].append(r)
    out = []
    for (atr_mult, mt), recs in sorted(by_cell.items()):
        n_total = len(recs)
        accepted = [r for r in recs if r["accepted"]]
        n_accepted = len(accepted)
        resolved = [r for r in accepted if r["realized_r"] is not None]
        n_resolved = len(resolved)
        # walk-status histogram (across accepted)
        walk_hist = defaultdict(int)
        for r in accepted:
            walk_hist[r.get("walk_status", "unknown")] += 1
        if n_resolved >= MIN_RESOLVED_PER_CELL:
            rs = [r["realized_r"] for r in resolved]
            mean_r = mean(rs)
            wins = sum(1 for r in rs if r > 0)
            win_rate = wins / n_resolved
            wr_lo, wr_hi = wilson_ci(wins, n_resolved)
            r_lo, r_hi = bootstrap_mean_ci(rs)
            std_r = stdev(rs) if n_resolved > 1 else 0.0
            insufficient = False
        else:
            mean_r = win_rate = wr_lo = wr_hi = r_lo = r_hi = std_r = None
            insufficient = True
        out.append({
            "atr_mult": atr_mult,
            "min_ticks": mt,
            "n_total": n_total,
            "n_accepted": n_accepted,
            "acceptance_rate": (n_accepted / n_total) if n_total else 0.0,
            "n_resolved": n_resolved,
            "n_unresolved": n_accepted - n_resolved,
            "mean_r": mean_r,
            "boot_ci_low_r": r_lo,
            "boot_ci_high_r": r_hi,
            "win_rate": win_rate,
            "wilson_ci_low_wr": wr_lo,
            "wilson_ci_high_wr": wr_hi,
            "std_r": std_r,
            "insufficient_data": insufficient,
            "walk_tp": walk_hist.get("tp", 0),
            "walk_sl": walk_hist.get("sl", 0),
            "walk_no_fill": walk_hist.get("no_fill", 0),
            "walk_no_resolve": walk_hist.get("no_resolve", 0),
        })
    return out


# ---------------------------------------------------------------------------
# Pareto frontier
# ---------------------------------------------------------------------------

def find_pareto(cells: list[dict],
                dims=("acceptance_rate", "mean_r")) -> list[dict]:
    a_dim, b_dim = dims
    candidates = [c for c in cells if c[a_dim] is not None and c[b_dim] is not None]
    pareto = []
    for c in candidates:
        ca, cb = c[a_dim], c[b_dim]
        dominated = False
        for o in candidates:
            if o is c:
                continue
            oa, ob = o[a_dim], o[b_dim]
            if (oa >= ca and ob >= cb) and (oa > ca or ob > cb):
                dominated = True
                break
        if not dominated:
            pareto.append(c)
    return pareto


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _flush_print(*args, **kwargs):
    print(*args, **kwargs, flush=True)


def main():
    # Force unbuffered, UTF-8 output (Windows cp1252 default rejects '->')
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
        except Exception:
            sys.stdout.reconfigure(line_buffering=True)
    _flush_print(f"C16 v3 sweep -- {dt.datetime.utcnow().isoformat()}Z\n")

    summary = {}
    all_per_record_rows = []
    pareto_rows = []
    cells_per_instr = {}

    for sym in INSTRUMENTS:
        _flush_print(f"=== {sym} ===")
        recs = extract_records(sym)
        _flush_print(f"  Records (CANDIDATE): {len(recs)}")
        if not recs:
            summary[sym] = {
                "status": "NO_DATA",
                "n_records": 0,
                "reason": "No trade_records dir or zero CANDIDATE rows",
            }
            _flush_print(f"  -> NO_DATA (zero records)")
            continue

        all_rows = []
        for r in recs:
            all_rows.extend(sweep_record(r, sym))
        all_per_record_rows.extend(all_rows)
        cells = aggregate_per_cell(all_rows)
        cells_per_instr[sym] = cells
        n_pareto = len(find_pareto(cells))
        n_with_data = sum(1 for c in cells if not c["insufficient_data"])
        _flush_print(f"  Cells: {len(cells)} ({n_with_data} with n_resolved >= {MIN_RESOLVED_PER_CELL}); "
              f"Pareto-optimal: {n_pareto}")

        for p in find_pareto(cells):
            pareto_rows.append({"symbol": sym, **p})
            _flush_print(f"    PARETO: atr={p['atr_mult']}, mt={p['min_ticks']}, "
                  f"accept={p['acceptance_rate']:.1%}, "
                  f"meanR={p['mean_r']:.3f}, WR={p['win_rate']:.1%} (n={p['n_resolved']})")

        cur_cfg = {
            "EURUSD": {"atr_mult": 0.50, "min_ticks": 8},
            "GBPUSD": {"atr_mult": 0.50, "min_ticks": 8},
            "USDJPY": {"atr_mult": 0.30, "min_ticks": 5},
        }[sym]
        cur_cell = None
        for c in cells:
            if abs(c["atr_mult"] - cur_cfg["atr_mult"]) < 1e-9 and c["min_ticks"] == cur_cfg["min_ticks"]:
                cur_cell = c
                break
        summary[sym] = {
            "status": "OK",
            "n_records": len(recs),
            "n_cells_total": len(cells),
            "n_cells_with_data": n_with_data,
            "n_pareto_cells": n_pareto,
            "current_config": cur_cfg,
            "current_cell_metrics": cur_cell,
        }

    # Cross-instrument synthesis
    cross = {}
    for sym, cells in cells_per_instr.items():
        for c in cells:
            key = (c["atr_mult"], c["min_ticks"])
            cross.setdefault(key, {})
            cross[key][sym] = c

    cross_summary = []
    for key, by_sym in sorted(cross.items()):
        atr_mult, mt = key
        ev_per_sym = {}
        for sym, c in by_sym.items():
            if c["mean_r"] is not None:
                ev_per_sym[sym] = c["acceptance_rate"] * c["mean_r"]
            else:
                ev_per_sym[sym] = None
        valid_evs = [v for v in ev_per_sym.values() if v is not None]
        avg_ev = sum(valid_evs) / len(valid_evs) if valid_evs else None
        min_ev = min(valid_evs) if valid_evs else None
        cross_summary.append({
            "atr_mult": atr_mult,
            "min_ticks": mt,
            "n_syms_with_data": len(valid_evs),
            "ev_per_sym": ev_per_sym,
            "avg_ev": avg_ev,
            "min_ev": min_ev,
        })

    summary_full = {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "task": "C16 — Per-instrument tight-FX override Pareto sweep",
        "branch": "feat/research-c16-tight-fx-pareto-sweep-v3",
        "atr_mult_grid": ATR_MULTS,
        "min_ticks_grid": MIN_TICKS,
        "instruments_targeted": INSTRUMENTS,
        "min_rr": MIN_RR,
        "sl_beyond_ob_tick_floor": SL_BEYOND_OB_TICK_FLOOR,
        "walk_window_bars": WALK_WINDOW_BARS,
        "min_resolved_per_cell": MIN_RESOLVED_PER_CELL,
        "bootstrap_n": BOOTSTRAP_N,
        "per_instrument": summary,
        "per_instrument_cells": cells_per_instr,
        "cross_instrument_summary": cross_summary,
    }

    out_json = OUT_DIR / "results.json"
    with open(out_json, "w") as f:
        json.dump(summary_full, f, indent=2, default=str)
    _flush_print(f"\nWrote {out_json}")

    pareto_csv = OUT_DIR / "pareto_per_instrument.csv"
    with open(pareto_csv, "w", newline="") as f:
        if pareto_rows:
            writer = csv.DictWriter(f, fieldnames=list(pareto_rows[0].keys()))
            writer.writeheader()
            writer.writerows(pareto_rows)
        else:
            f.write("symbol,atr_mult,min_ticks,acceptance_rate,mean_r,win_rate,n_resolved\n")
    _flush_print(f"Wrote {pareto_csv}")

    cells_csv = OUT_DIR / "cells_per_instrument.csv"
    with open(cells_csv, "w", newline="") as f:
        rows = []
        for sym, cells in cells_per_instr.items():
            for c in cells:
                rows.append({"symbol": sym, **c})
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    _flush_print(f"Wrote {cells_csv}")

    rec_csv = OUT_DIR / "per_record_sweep.csv"
    with open(rec_csv, "w", newline="") as f:
        if all_per_record_rows:
            writer = csv.DictWriter(f, fieldnames=list(all_per_record_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_per_record_rows)
    _flush_print(f"Wrote {rec_csv}")

    cross_csv = OUT_DIR / "cross_instrument_summary.csv"
    with open(cross_csv, "w", newline="") as f:
        rows = []
        for c in cross_summary:
            row = {
                "atr_mult": c["atr_mult"],
                "min_ticks": c["min_ticks"],
                "n_syms_with_data": c["n_syms_with_data"],
                "avg_ev": c["avg_ev"],
                "min_ev": c["min_ev"],
            }
            for sym in INSTRUMENTS:
                row[f"ev_{sym}"] = c["ev_per_sym"].get(sym)
            rows.append(row)
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    _flush_print(f"Wrote {cross_csv}")

    return summary_full


if __name__ == "__main__":
    main()
