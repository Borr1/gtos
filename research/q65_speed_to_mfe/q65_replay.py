"""Q-6.5 — Speed-to-MFE vs TP probability (pre-registered).

See ``PRE_REGISTRATION.md`` in the same directory for the committed hypothesis,
metrics, sample/alpha thresholds, and verdict rules.  This script is the
deterministic replay that implements those rules.

Universe construction
---------------------
We build one record per historical batch trade, merging four sources:
  1. ``knowledge_base_backtest/sessions/{SYMBOL}/*_session.json`` — gives the
     final outcome (r_multiple, mfe_r, hold_time_candles, exit_substate) for
     every executed trade, per symbol directory.
  2. ``knowledge_base_backtest/batch_api/*_results.json`` — raw AI responses
     for each candle evaluation.  CANDIDATE responses carry the
     ``trade_parameters`` block (direction / entry_price / stop_loss / TP).
  3. ``knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`` —
     fully hydrated XAUUSD trades with entry/SL already parsed (110 rows).
  4. ``knowledge_base_backtest/analysis/phase1_all_trades_merged.json`` — 18
     XAUUSD trades that carry an r_path (bar-by-bar R log).

Priority for resolving conflicts: phase1 > unified > batch_api/session_join.
Session files are always needed for the outcome (mfe_r, r_multiple,
hold_time_candles, exit_substate) since some batch_api texts are truncated.

Time-to-MFE reconstruction
--------------------------
For trades lacking r_path we read ``data/historical/{SYMBOL}_M15.csv`` and
replay from the entry candle forward.  We count M15 bars from the fill bar
(inclusive of the fill candle itself, to mirror the conventions in
``orchestrator.py``).  The fill bar is the first bar whose [low, high] range
contains the limit ``entry_price``.  If the fill never happens in the first
20 bars after the CANDIDATE candle, we skip the trade (fail-loud, no
fabrication).

Outputs
-------
  q65_trade_speeds.csv  — one row per accepted trade with time-to-+0.5R,
                           time-to-+1.0R, tp_hit flag, direction, source.
  q65_report_2026-04-18.md — human-readable report with pre-registration,
                           methodology, results table, verdict.
  q65_summary.json      — machine-readable aggregate statistics.

Run::
    python research/q65_speed_to_mfe/q65_replay.py
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
HIST_DIR = ROOT / "data" / "historical"
SESS_DIR = ROOT / "knowledge_base_backtest" / "sessions"
BATCH_API_DIR = ROOT / "knowledge_base_backtest" / "batch_api"
UNIFIED_FP = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
PHASE1_FP = ROOT / "knowledge_base_backtest" / "analysis" / "phase1_all_trades_merged.json"


# --- Config (frozen per PRE_REGISTRATION.md) ---------------------------------
SPEED_THRESHOLDS = [3, 5, 10, 20]
MFE_LEVELS = [0.5, 1.0]
MIN_COHORT_N = 30
MIN_OVERALL_N = 100
BONFERRONI_ALPHA = 0.05 / (len(SPEED_THRESHOLDS) * len(MFE_LEVELS))  # 0.00625
TP_HIT_MIN_R = 0.9  # primary TP-hit proxy
WIN_MIN_R = 0.0     # sensitivity proxy: r_multiple > 0


# --- Step 1: load M15 historical CSVs once ----------------------------------
def load_m15(symbol: str) -> list[dict]:
    """Return list of bars: [{time: datetime, o, h, l, c}, ...] sorted ascending."""
    fp = HIST_DIR / f"{symbol}_M15.csv"
    if not fp.exists():
        return []
    bars: list[dict] = []
    with open(fp, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                t = datetime.fromisoformat(row["time"].replace("Z", "").strip())
            except Exception:
                continue
            try:
                bars.append({
                    "time": t,
                    "o": float(row["open"]),
                    "h": float(row["high"]),
                    "l": float(row["low"]),
                    "c": float(row["close"]),
                })
            except Exception:
                continue
    return bars


def build_time_index(bars: list[dict]) -> dict:
    return {b["time"]: i for i, b in enumerate(bars)}


# --- Step 2: load outcome rows from per-symbol session dirs ------------------
SYMBOL_DIRS = {
    "XAUUSD": "XAUUSD",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
    "US30_cash": "US30_cash",
    "USDJPY": "USDJPY",
    # NZDUSD excluded — killed from live universe, not in min=5 symbols.
}


def parse_candidate_text(text: str) -> dict | None:
    """Best-effort extract of trade_parameters JSON from an AI response text."""
    # Strip code fences and whitespace
    t = text.strip()
    if t.startswith("```"):
        # drop leading fence and optional "json"
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        obj = json.loads(t)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def load_batch_api_candidates() -> dict:
    """Return mapping ``eval_key -> parsed_ai_json`` for all CANDIDATE candles.

    eval_key format: e.g. ``2025-10-01_london_0815``.
    """
    out: dict[str, dict] = {}
    paths = sorted(glob.glob(str(BATCH_API_DIR / "*_results.json")))
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            if not isinstance(v, dict):
                continue
            text = v.get("text") or ""
            if '"CANDIDATE"' not in text:
                continue
            parsed = parse_candidate_text(text)
            if not parsed:
                continue
            if parsed.get("decision") != "CANDIDATE":
                continue
            tp = parsed.get("trade_parameters") or {}
            if not tp.get("entry_price") or not tp.get("stop_loss"):
                continue
            out[k] = parsed
    return out


def candle_time_from_evalkey(key: str, session_start: str | None = None) -> datetime | None:
    """Parse ``2025-10-01_ny_1315`` -> datetime(2025,10,1,13,15)."""
    try:
        date_str, _kz, hhmm = key.rsplit("_", 2)
        hh = int(hhmm[:2])
        mm = int(hhmm[2:])
        y, m, d = map(int, date_str.split("-"))
        return datetime(y, m, d, hh, mm)
    except Exception:
        return None


def load_session_trades(symbol_dir: str) -> list[dict]:
    """Return outcome rows from all session files in a symbol directory."""
    out: list[dict] = []
    d = SESS_DIR / symbol_dir
    if not d.is_dir():
        return out
    for fp in sorted(d.glob("*_session.json")):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                sess = json.load(f)
        except Exception:
            continue
        date_str = sess.get("date") or fp.stem.replace("_session", "")
        ce_by_tid: dict[str, dict] = {}
        for ce in sess.get("candle_evaluations", []) or []:
            tid = ce.get("trade_id")
            if tid:
                ce_by_tid[tid] = ce
        for tr in sess.get("trade_summary", {}).get("trades", []) or []:
            if tr.get("outcome") not in ("WIN", "LOSS", "BREAKEVEN"):
                continue
            tid = tr.get("trade_id")
            ce = ce_by_tid.get(tid, {})
            out.append({
                "symbol_dir": symbol_dir,
                "date": date_str,
                "trade_id": tid,
                "kill_zone": tr.get("kill_zone"),
                "outcome": tr.get("outcome"),
                "r_multiple": tr.get("r_multiple"),
                "mfe_r": tr.get("mfe_r"),
                "mae_r": tr.get("mae_r"),
                "hold_time_candles": tr.get("hold_time_candles"),
                "exit_substate": tr.get("exit_substate"),
                "framework": tr.get("framework"),
                "candle_time_str": ce.get("candle_time"),
            })
    return out


# --- Step 3: merge universe --------------------------------------------------
def load_unified() -> dict:
    try:
        with open(UNIFIED_FP, "r", encoding="utf-8") as f:
            arr = json.load(f)
    except Exception:
        return {}
    return {t["trade_id"]: t for t in arr if t.get("trade_id")}


def load_phase1() -> list[dict]:
    try:
        with open(PHASE1_FP, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def build_universe() -> list[dict]:
    """Build the trade universe keyed on (symbol, date, kill_zone, candle_time).

    Each record is a dict with keys used downstream: symbol, date, kill_zone,
    direction, entry_price, stop_loss, r_multiple, mfe_r, hold_time_candles,
    outcome, exit_substate, candle_time (datetime), source, trade_id, r_path.
    """
    # Session-side outcomes per symbol
    session_records_by_sym: dict[str, list[dict]] = {}
    for sym_dir in SYMBOL_DIRS.values():
        session_records_by_sym[sym_dir] = load_session_trades(sym_dir)
    # Also handle top-level legacy sessions/ (XAUUSD before the reseed)
    top_records = []
    for fp in sorted((SESS_DIR).glob("*_session.json")):
        # These legacy files are XAUUSD-coded; they lack the symbol dir
        try:
            with open(fp, "r", encoding="utf-8") as f:
                sess = json.load(f)
        except Exception:
            continue
        date_str = sess.get("date") or fp.stem.replace("_session", "")
        ce_by_tid: dict[str, dict] = {}
        for ce in sess.get("candle_evaluations", []) or []:
            tid = ce.get("trade_id")
            if tid:
                ce_by_tid[tid] = ce
        for tr in sess.get("trade_summary", {}).get("trades", []) or []:
            if tr.get("outcome") not in ("WIN", "LOSS", "BREAKEVEN"):
                continue
            tid = tr.get("trade_id")
            ce = ce_by_tid.get(tid, {})
            top_records.append({
                "symbol_dir": "XAUUSD",
                "date": date_str,
                "trade_id": tid,
                "kill_zone": tr.get("kill_zone"),
                "outcome": tr.get("outcome"),
                "r_multiple": tr.get("r_multiple"),
                "mfe_r": tr.get("mfe_r"),
                "mae_r": tr.get("mae_r"),
                "hold_time_candles": tr.get("hold_time_candles"),
                "exit_substate": tr.get("exit_substate"),
                "framework": tr.get("framework"),
                "candle_time_str": ce.get("candle_time"),
                "_legacy": True,
            })

    # Batch-api AI responses (carry direction, entry_price, stop_loss)
    batch_candidates = load_batch_api_candidates()

    # Unified / phase1 are XAUUSD-only
    unified = load_unified()
    phase1 = load_phase1()

    trades: list[dict] = []

    def _attach_ai(rec: dict) -> dict:
        """Look up the AI-side trade_parameters by (date, kill_zone, candle_time)."""
        ct = rec.get("candle_time_str")
        if not ct:
            return {}
        # Normalise candle_time into eval_key hhmm format
        try:
            # ct like "2024-04-01T13:15:00Z"
            t = datetime.fromisoformat(ct.replace("Z", ""))
        except Exception:
            return {}
        eval_key = f"{t.year:04d}-{t.month:02d}-{t.day:02d}_{rec['kill_zone']}_{t.hour:02d}{t.minute:02d}"
        parsed = batch_candidates.get(eval_key)
        if not parsed:
            return {}
        return parsed.get("trade_parameters") or {}

    # Process per-symbol session records first (gives us every outcome)
    merged_keys: set[tuple] = set()
    for sym_dir, recs in session_records_by_sym.items():
        for r in recs:
            ct = r.get("candle_time_str")
            if not ct:
                continue
            try:
                t = datetime.fromisoformat(ct.replace("Z", ""))
            except Exception:
                continue
            key = (sym_dir, r["date"], r["kill_zone"], t)
            ai = _attach_ai(r)
            entry = ai.get("entry_price")
            sl = ai.get("stop_loss")
            direction = ai.get("direction")
            rec = {
                "symbol": sym_dir,
                "trade_id": r.get("trade_id"),
                "date": r.get("date"),
                "kill_zone": r.get("kill_zone"),
                "candle_time": t,
                "direction": direction,
                "entry_price": entry,
                "stop_loss": sl,
                "r_multiple": r.get("r_multiple"),
                "mfe_r": r.get("mfe_r"),
                "hold_time_candles": r.get("hold_time_candles"),
                "exit_substate": r.get("exit_substate"),
                "outcome": r.get("outcome"),
                "source": "session+batch_api" if ai else "session_only",
                "r_path": None,
            }
            trades.append(rec)
            merged_keys.add(key)

    # Process legacy top-level (XAUUSD only — reseed source)
    for r in top_records:
        ct = r.get("candle_time_str")
        if not ct:
            continue
        try:
            t = datetime.fromisoformat(ct.replace("Z", ""))
        except Exception:
            continue
        key = ("XAUUSD", r["date"], r["kill_zone"], t)
        if key in merged_keys:
            continue  # already present via per-symbol dir
        ai = _attach_ai(r)
        trades.append({
            "symbol": "XAUUSD",
            "trade_id": r.get("trade_id"),
            "date": r.get("date"),
            "kill_zone": r.get("kill_zone"),
            "candle_time": t,
            "direction": ai.get("direction"),
            "entry_price": ai.get("entry_price"),
            "stop_loss": ai.get("stop_loss"),
            "r_multiple": r.get("r_multiple"),
            "mfe_r": r.get("mfe_r"),
            "hold_time_candles": r.get("hold_time_candles"),
            "exit_substate": r.get("exit_substate"),
            "outcome": r.get("outcome"),
            "source": "legacy_top+batch_api" if ai else "legacy_top_only",
            "r_path": None,
        })
        merged_keys.add(key)

    # Patch from unified (XAUUSD, gives entry/SL for any trades missing them)
    for tid, u in unified.items():
        try:
            t = datetime.fromisoformat(u["date"] + "T00:00:00")
        except Exception:
            t = None
        # Identify the trade in our list
        for rec in trades:
            if rec.get("trade_id") == tid:
                for fld in ("direction", "entry_price", "stop_loss"):
                    if not rec.get(fld) and u.get(fld) is not None:
                        rec[fld] = u.get(fld)
                if rec["source"].startswith("session"):
                    rec["source"] = rec["source"] + "+unified"
                break

    # Patch from phase1 (gives r_path)
    for p in phase1:
        # Find matching trade by candle_time + direction + entry_price
        try:
            t = datetime.fromisoformat(p["candle_time"].replace("Z", ""))
        except Exception:
            continue
        match = None
        for rec in trades:
            if rec["candle_time"] == t and rec["kill_zone"] == p.get("kill_zone"):
                ep = rec.get("entry_price")
                if ep and abs(float(ep) - float(p["entry_price"])) < 1e-4:
                    match = rec
                    break
        if match is None:
            # Ingest as new XAUUSD trade (phase1 is XAUUSD-coded)
            trades.append({
                "symbol": "XAUUSD",
                "trade_id": p.get("trade_id") or f"phase1_{p['date']}_{p['kill_zone']}",
                "date": p.get("date"),
                "kill_zone": p.get("kill_zone"),
                "candle_time": t,
                "direction": p.get("direction"),
                "entry_price": p.get("entry_price"),
                "stop_loss": p.get("stop_loss"),
                "r_multiple": p.get("r_multiple"),
                "mfe_r": p.get("mfe_r"),
                "hold_time_candles": p.get("hold_time_candles"),
                "exit_substate": p.get("exit_substate"),
                "outcome": p.get("outcome"),
                "source": "phase1_only",
                "r_path": p.get("r_path"),
            })
        else:
            match["r_path"] = p.get("r_path")
            match["source"] = match["source"] + "+phase1"

    return trades


# --- Step 4: compute time-to-MFE --------------------------------------------
def _time_to_level_from_r_path(r_path: list[dict], level: float) -> int | None:
    """Return bar index at which r_path first reaches the MFE level, else None.

    The r_path convention in phase1 files is: candle_index starts at 0 for the
    first post-entry bar. We mirror that convention and return candle_index
    directly, so the index is 0-based from fill bar.
    """
    if not r_path:
        return None
    for bar in r_path:
        r_high = bar.get("r_at_high")
        r_close = bar.get("r_at_close")
        for r in (r_high, r_close):
            if r is not None and r >= level:
                return int(bar.get("candle_index", 0))
    return None


def _time_to_level_from_bars(
    bars: list[dict],
    time_idx: dict,
    candle_time: datetime,
    entry_price: float,
    stop_loss: float,
    direction: str,
    level: float,
    max_scan: int,
) -> tuple[int | None, str]:
    """Return (bar_index_from_fill_bar, reason) if level reached; else (None, reason).

    Reason is one of: "hit_level_bar_N", "not_reached_within_scan",
    "fill_never_happened", "entry_bar_missing".
    """
    if candle_time not in time_idx:
        return None, "entry_bar_missing"
    ce_idx = time_idx[candle_time]
    # Scan forward for fill: first bar whose [low, high] contains entry_price.
    fill_idx = None
    FILL_SEARCH = 20  # bars
    last_fill_search = min(len(bars), ce_idx + FILL_SEARCH + 1)
    for i in range(ce_idx, last_fill_search):
        b = bars[i]
        if b["l"] <= entry_price <= b["h"]:
            fill_idx = i
            break
    if fill_idx is None:
        return None, "fill_never_happened"
    # Compute R-distance
    if direction == "LONG":
        sl_dist = entry_price - stop_loss
    else:
        sl_dist = stop_loss - entry_price
    if sl_dist <= 0:
        return None, "invalid_sl_distance"
    target = level * sl_dist
    # Scan from fill_idx forward for <= max_scan bars.
    scan_end = min(len(bars), fill_idx + max_scan + 1)
    for i in range(fill_idx, scan_end):
        b = bars[i]
        if direction == "LONG":
            r_at_high = (b["h"] - entry_price) / sl_dist
            if r_at_high >= level:
                return i - fill_idx, f"hit_bar_{i - fill_idx}"
        else:
            r_at_low = (entry_price - b["l"]) / sl_dist
            if r_at_low >= level:
                return i - fill_idx, f"hit_bar_{i - fill_idx}"
    return None, "not_reached_within_scan"


def compute_times(trade: dict, bars_cache: dict) -> dict:
    """Compute time-to-+0.5R, time-to-+1.0R, + reasons."""
    out = {"t_05r": None, "t_10r": None, "reason_05r": "", "reason_10r": "",
           "skipped": None}
    if not trade.get("direction") or trade["direction"] not in ("LONG", "SHORT"):
        out["skipped"] = "missing_direction"
        return out
    if trade.get("entry_price") is None or trade.get("stop_loss") is None:
        out["skipped"] = "missing_entry_or_sl"
        return out
    # Prefer r_path if present
    if trade.get("r_path"):
        out["t_05r"] = _time_to_level_from_r_path(trade["r_path"], 0.5)
        out["t_10r"] = _time_to_level_from_r_path(trade["r_path"], 1.0)
        out["reason_05r"] = "r_path" if out["t_05r"] is not None else "r_path_not_reached"
        out["reason_10r"] = "r_path" if out["t_10r"] is not None else "r_path_not_reached"
        return out
    # Otherwise scan M15 bars.
    sym = trade["symbol"]
    if sym not in bars_cache:
        bars_cache[sym] = (load_m15(sym), None)
        bars, _ = bars_cache[sym]
        bars_cache[sym] = (bars, build_time_index(bars))
    bars, time_idx = bars_cache[sym]
    if not bars:
        out["skipped"] = f"no_historical_m15_{sym}"
        return out
    max_scan = trade.get("hold_time_candles") or 100
    try:
        max_scan = int(max_scan)
    except Exception:
        max_scan = 100
    max_scan = max(max_scan, 1)
    t_05, why_05 = _time_to_level_from_bars(
        bars, time_idx, trade["candle_time"], float(trade["entry_price"]),
        float(trade["stop_loss"]), trade["direction"], 0.5, max_scan,
    )
    if why_05 in {"entry_bar_missing", "fill_never_happened", "invalid_sl_distance"}:
        out["skipped"] = why_05
        return out
    t_10, why_10 = _time_to_level_from_bars(
        bars, time_idx, trade["candle_time"], float(trade["entry_price"]),
        float(trade["stop_loss"]), trade["direction"], 1.0, max_scan,
    )
    out["t_05r"] = t_05
    out["t_10r"] = t_10
    out["reason_05r"] = why_05
    out["reason_10r"] = why_10
    return out


# --- Step 5: statistics ------------------------------------------------------
def _phi(x: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def two_proportion_z(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float, float]:
    """Return (z, two-sided p, effect_size_pp).

    effect_size_pp = (x1/n1 - x2/n2) * 100.
    """
    if n1 == 0 or n2 == 0:
        return float("nan"), float("nan"), float("nan")
    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    denom = math.sqrt(p_pool * (1 - p_pool) * (1.0 / n1 + 1.0 / n2))
    if denom == 0:
        return float("nan"), float("nan"), (p1 - p2) * 100.0
    z = (p1 - p2) / denom
    p = 2.0 * (1.0 - _phi(abs(z)))
    return z, p, (p1 - p2) * 100.0


# --- Step 6: main ------------------------------------------------------------
def main() -> int:
    print("[q65] Building universe...", flush=True)
    trades = build_universe()
    print(f"[q65] Universe size (pre-filter): {len(trades)}", flush=True)

    # Deduplicate on (symbol, candle_time, kill_zone, trade_id) just in case.
    seen = set()
    uniq = []
    for t in trades:
        k = (t["symbol"], t["candle_time"].isoformat(), t["kill_zone"], t["trade_id"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(t)
    trades = uniq
    print(f"[q65] Universe size (dedup): {len(trades)}", flush=True)

    # Compute times
    bars_cache: dict = {}
    accepted = []
    skip_reasons: dict[str, int] = defaultdict(int)
    for tr in trades:
        res = compute_times(tr, bars_cache)
        if res["skipped"]:
            skip_reasons[res["skipped"]] += 1
            continue
        tr["_t_05r"] = res["t_05r"]
        tr["_t_10r"] = res["t_10r"]
        tr["_reason_05r"] = res["reason_05r"]
        tr["_reason_10r"] = res["reason_10r"]
        accepted.append(tr)
    print(f"[q65] Accepted: {len(accepted)}", flush=True)
    print(f"[q65] Skips: {dict(skip_reasons)}", flush=True)

    # Write per-trade CSV
    csv_fp = OUT_DIR / "q65_trade_speeds.csv"
    with open(csv_fp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "symbol", "date", "kill_zone", "trade_id", "candle_time",
            "direction", "entry_price", "stop_loss",
            "r_multiple", "mfe_r", "hold_time_candles", "exit_substate", "outcome",
            "t_to_05R_bars", "t_to_10R_bars",
            "reached_05R", "reached_10R",
            "tp_hit_r09", "win_rpos", "source",
            "reason_05r", "reason_10r",
        ])
        for tr in accepted:
            r = tr.get("r_multiple")
            tp_hit = int(r is not None and float(r) >= TP_HIT_MIN_R)
            win = int(r is not None and float(r) > WIN_MIN_R)
            w.writerow([
                tr["symbol"], tr["date"], tr["kill_zone"], tr["trade_id"],
                tr["candle_time"].isoformat(),
                tr.get("direction"), tr.get("entry_price"), tr.get("stop_loss"),
                r, tr.get("mfe_r"), tr.get("hold_time_candles"),
                tr.get("exit_substate"), tr.get("outcome"),
                tr.get("_t_05r"), tr.get("_t_10r"),
                int(tr.get("_t_05r") is not None), int(tr.get("_t_10r") is not None),
                tp_hit, win, tr.get("source"),
                tr.get("_reason_05r"), tr.get("_reason_10r"),
            ])
    print(f"[q65] Wrote {csv_fp}", flush=True)

    # --- Build cohorts + statistics --------------------------------------
    if len(accepted) < MIN_OVERALL_N:
        print(f"[q65] WARN: overall n={len(accepted)} < {MIN_OVERALL_N}")

    cells = []
    for level, attr in [(0.5, "_t_05r"), (1.0, "_t_10r")]:
        for thr in SPEED_THRESHOLDS:
            fast_x = 0; fast_n = 0
            slow_x = 0; slow_n = 0
            for tr in accepted:
                r = tr.get("r_multiple")
                if r is None:
                    continue
                tp_hit = 1 if float(r) >= TP_HIT_MIN_R else 0
                t = tr.get(attr)
                if t is not None and t <= thr:
                    fast_n += 1
                    fast_x += tp_hit
                else:
                    slow_n += 1
                    slow_x += tp_hit
            z, p, eff = two_proportion_z(fast_x, fast_n, slow_x, slow_n)
            cells.append({
                "mfe_level": level,
                "speed_threshold_bars": thr,
                "fast_n": fast_n, "fast_tp": fast_x,
                "fast_rate": (fast_x / fast_n) if fast_n else float("nan"),
                "slow_n": slow_n, "slow_tp": slow_x,
                "slow_rate": (slow_x / slow_n) if slow_n else float("nan"),
                "effect_pp": eff, "z": z, "p_raw": p,
                "p_bonf": min(1.0, p * 8) if not math.isnan(p) else float("nan"),
                "underpowered": (fast_n < MIN_COHORT_N or slow_n < MIN_COHORT_N),
            })

    # Sensitivity: same grid but using WIN (r > 0) as the outcome
    win_cells = []
    for level, attr in [(0.5, "_t_05r"), (1.0, "_t_10r")]:
        for thr in SPEED_THRESHOLDS:
            fast_x = 0; fast_n = 0
            slow_x = 0; slow_n = 0
            for tr in accepted:
                r = tr.get("r_multiple")
                if r is None:
                    continue
                w = 1 if float(r) > WIN_MIN_R else 0
                t = tr.get(attr)
                if t is not None and t <= thr:
                    fast_n += 1
                    fast_x += w
                else:
                    slow_n += 1
                    slow_x += w
            z, p, eff = two_proportion_z(fast_x, fast_n, slow_x, slow_n)
            win_cells.append({
                "mfe_level": level,
                "speed_threshold_bars": thr,
                "fast_n": fast_n, "fast_win": fast_x,
                "fast_rate": (fast_x / fast_n) if fast_n else float("nan"),
                "slow_n": slow_n, "slow_win": slow_x,
                "slow_rate": (slow_x / slow_n) if slow_n else float("nan"),
                "effect_pp": eff, "z": z, "p_raw": p,
                "p_bonf": min(1.0, p * 8) if not math.isnan(p) else float("nan"),
                "underpowered": (fast_n < MIN_COHORT_N or slow_n < MIN_COHORT_N),
            })

    summary = {
        "pre_registration": "research/q65_speed_to_mfe/PRE_REGISTRATION.md",
        "bonferroni_alpha": BONFERRONI_ALPHA,
        "min_cohort_n": MIN_COHORT_N,
        "min_overall_n": MIN_OVERALL_N,
        "tp_hit_proxy": f"r_multiple >= {TP_HIT_MIN_R}",
        "win_proxy": f"r_multiple > {WIN_MIN_R}",
        "universe_raw": len(trades),
        "accepted": len(accepted),
        "skip_reasons": dict(skip_reasons),
        "cells_tp_hit": cells,
        "cells_win_sensitivity": win_cells,
    }
    with open(OUT_DIR / "q65_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"[q65] Wrote summary", flush=True)

    # Print a terse ASCII table for quick review
    print("\n[q65] TP-hit (r>=0.9) results:")
    print(f"{'MFE':>5} {'Thr':>4} {'fast_n':>7} {'fast':>6} {'slow_n':>7} {'slow':>6} {'eff_pp':>7} {'p_raw':>9} {'p_bonf':>9} {'power':>6}")
    for c in cells:
        power = "OK" if not c["underpowered"] else "LOW"
        pr = f"{c['fast_rate']:.3f}" if c['fast_n'] else "-"
        sr = f"{c['slow_rate']:.3f}" if c['slow_n'] else "-"
        pp = f"{c['effect_pp']:+.1f}" if not math.isnan(c['effect_pp']) else "-"
        p_raw = f"{c['p_raw']:.4f}" if not math.isnan(c['p_raw']) else "-"
        p_bonf = f"{c['p_bonf']:.4f}" if not math.isnan(c['p_bonf']) else "-"
        print(f"{c['mfe_level']:>5.1f} {c['speed_threshold_bars']:>4d} {c['fast_n']:>7d} {pr:>6} {c['slow_n']:>7d} {sr:>6} {pp:>7} {p_raw:>9} {p_bonf:>9} {power:>6}")

    print("\n[q65] WIN (r>0) sensitivity results:")
    print(f"{'MFE':>5} {'Thr':>4} {'fast_n':>7} {'fast':>6} {'slow_n':>7} {'slow':>6} {'eff_pp':>7} {'p_raw':>9} {'p_bonf':>9} {'power':>6}")
    for c in win_cells:
        power = "OK" if not c["underpowered"] else "LOW"
        pr = f"{c['fast_rate']:.3f}" if c['fast_n'] else "-"
        sr = f"{c['slow_rate']:.3f}" if c['slow_n'] else "-"
        pp = f"{c['effect_pp']:+.1f}" if not math.isnan(c['effect_pp']) else "-"
        p_raw = f"{c['p_raw']:.4f}" if not math.isnan(c['p_raw']) else "-"
        p_bonf = f"{c['p_bonf']:.4f}" if not math.isnan(c['p_bonf']) else "-"
        print(f"{c['mfe_level']:>5.1f} {c['speed_threshold_bars']:>4d} {c['fast_n']:>7d} {pr:>6} {c['slow_n']:>7d} {sr:>6} {pp:>7} {p_raw:>9} {p_bonf:>9} {power:>6}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
