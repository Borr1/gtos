"""Incremental tick-microstructure pipeline (North-Star C2 capability — "used-when-needed-then-DELETED").

Cycle 13 reduced tick-C2 to an exact source requirement: multi-YEAR tick across regimes (billions of
ticks, infeasible to store at once). This module is the capability that unblocks it WITHOUT ever storing
the full tick: process ONE bounded window at a time — export tick from the bridge -> derive compact
per-bar microstructure FEATURES (delta / absorption / aggression / sweep) -> APPEND the small feature rows
to a persistent store -> DELETE the raw tick -> next window. Across many windows this accumulates a
multi-year microstructure FEATURE dataset (kilobytes/bar, not billions of raw ticks), which a future
session mines + certifies through the edge factory (with the cycle-14 NULL-MECHANISM PLACEBO guard, since
microstructure R is a non-standard definition).

Disk discipline: the raw tick for a window is held only in-memory / a temp file and deleted before the next
window. Only the compact feature rows persist. This is the literal "export -> mine -> delete -> free disk
-> next" mandate.

Bridge: siliconmetatrader5 (host localhost:8001). No paid APIs. OHLC/tick are MT5-native (in evidence class).
"""
from __future__ import annotations

import json
import os
import statistics as st
from typing import Dict, List, Optional, Tuple


def derive_bar_features(ticks: List[dict], bar_key_len: int = 13) -> Dict[str, dict]:
    """Aggregate a window of bid/ask ticks into per-bar microstructure features (default H1 = first 13
    chars of ISO time 'YYYY-MM-DDTHH'). Each tick: {'time': iso, 'bid': float, 'ask': float}.

    Per-bar features (the MT5 order-flow PROXY — no paid order-flow needed):
      o/h/l/c (mid), n_ticks, up/down (mid-uptick/downtick counts),
      delta = up - down (signed flow proxy), spread_mean (execution cost proxy),
      absorption = n_ticks / (range_in_bps + eps) (high activity, low progress = absorption),
      aggression = |delta| / n_ticks (directional conviction of flow).
    """
    bars: Dict[str, dict] = {}
    prev_mid: Optional[float] = None
    for t in ticks:
        try:
            bid = float(t["bid"]); ask = float(t["ask"]); ts = str(t["time"])[:bar_key_len]
        except (KeyError, TypeError, ValueError):
            continue
        mid = (bid + ask) / 2.0
        b = bars.get(ts)
        if b is None:
            b = bars[ts] = {"o": mid, "h": mid, "l": mid, "c": mid, "n": 0, "up": 0, "down": 0,
                            "spread_sum": 0.0}
        b["c"] = mid; b["h"] = max(b["h"], mid); b["l"] = min(b["l"], mid)
        b["n"] += 1; b["spread_sum"] += (ask - bid)
        if prev_mid is not None:
            if mid > prev_mid:
                b["up"] += 1
            elif mid < prev_mid:
                b["down"] += 1
        prev_mid = mid
    out: Dict[str, dict] = {}
    for ts, b in bars.items():
        rng_bps = (b["h"] - b["l"]) / b["o"] * 1e4 if b["o"] else 0.0
        delta = b["up"] - b["down"]
        out[ts] = {"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "n_ticks": b["n"],
                   "delta": delta, "spread_mean": b["spread_sum"] / b["n"] if b["n"] else 0.0,
                   "absorption": b["n"] / (rng_bps + 1e-6), "aggression": abs(delta) / b["n"] if b["n"] else 0.0,
                   "range_bps": rng_bps}
    return out


def append_features(features: Dict[str, dict], symbol: str, store_path: str) -> int:
    """Append per-bar feature rows (compact) to the persistent JSONL store. Returns rows written."""
    os.makedirs(os.path.dirname(store_path), exist_ok=True)
    n = 0
    with open(store_path, "a") as f:
        for ts, feat in sorted(features.items()):
            f.write(json.dumps({"symbol": symbol, "bar": ts, **{k: round(v, 6) if isinstance(v, float) else v
                                                                 for k, v in feat.items()}}) + "\n")
            n += 1
    return n


def process_window(symbol: str, start, end, store_path: str, *, bridge_host: str = "localhost",
                   bridge_port: int = 8001, bar_key_len: int = 13) -> dict:
    """Export one window's tick from the bridge -> derive features -> append to store -> DELETE raw tick.
    Returns a summary dict. The raw tick is never persisted (held in-memory, dropped on return)."""
    from siliconmetatrader5 import MetaTrader5  # noqa: PLC0415
    c = MetaTrader5(host=bridge_host, port=bridge_port, keepalive=True)
    if not c.initialize():
        raise RuntimeError(f"bridge init failed: {c.last_error()}")
    try:
        c.symbol_select(symbol, True)
        raw = c.copy_ticks_range(symbol, start, end, c.COPY_TICKS_ALL)
        n_raw = len(raw) if raw is not None else 0
        # normalize to dicts (bridge returns structured rows: [time_s, bid, ask, last, vol, time_msc, flags, vol_real])
        ticks = []
        if raw is not None:
            from datetime import datetime, timezone
            for r in raw:
                t = r["time_msc"] if hasattr(r, "keys") and "time_msc" in r else (r[5] if not hasattr(r, "keys") else None)
                bid = r["bid"] if hasattr(r, "keys") else r[1]
                ask = r["ask"] if hasattr(r, "keys") else r[2]
                iso = datetime.fromtimestamp(int(t) / 1000.0, tz=timezone.utc).isoformat()
                ticks.append({"time": iso, "bid": bid, "ask": ask})
        feats = derive_bar_features(ticks, bar_key_len=bar_key_len)
        rows = append_features(feats, symbol, store_path)
        del raw, ticks  # DELETE raw tick from memory before the next window
        return {"symbol": symbol, "n_raw_ticks": n_raw, "n_bars": len(feats), "rows_written": rows,
                "store": store_path, "raw_deleted": True}
    finally:
        try:
            c.close()
        except Exception:
            pass


def process_windows(symbol: str, windows: List[Tuple], store_path: str, **kw) -> dict:
    """Run process_window across many bounded windows (the multi-year accumulation loop)."""
    summ = []
    for (s, e) in windows:
        summ.append(process_window(symbol, s, e, store_path, **kw))
    return {"symbol": symbol, "n_windows": len(windows), "total_bars": sum(x["n_bars"] for x in summ),
            "total_raw_ticks_processed": sum(x["n_raw_ticks"] for x in summ), "per_window": summ}
