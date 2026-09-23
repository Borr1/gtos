"""Tick Capture Daemon — per-symbol MT5 tick streaming with Lee-Ready aggressor classification.

Built per ``research/vision_program_2026-04-25/04_DATA_LAYER_ROADMAP.md`` §B
(Layer 1 — MT5 Tick Stream). Captures every bid/ask change with millisecond
timestamp, classifies each tick as buy/sell/neutral aggressor (Lee & Ready 1991),
and writes per-day Parquet files under ``data/ticks/{SYMBOL}/{YYYY-MM-DD}.parquet``.

Design intent
-------------
- One process per symbol (NOT threads — MT5 maintains a single connection per
  process, so concurrency must be process-level).
- Polls ``mt5.copy_ticks_from(symbol, last_seen_msc, count, COPY_TICKS_ALL)``
  every 1-5s; deduplicates by ``time_msc`` (broker-time millisecond
  timestamp). Stored ``ts_utc`` is converted to true UTC when the broker
  clock is offset.
- Crash-resilient: transient MT5 errors trigger exponential backoff; the daemon
  never aborts on a single failed poll.
- Storage budget per CEO target: ~25 GB/yr fleet; chunked by UTC day,
  pyarrow Parquet with snappy compression (3-5x reduction vs raw).

Lee-Ready aggressor classification (Lee & Ready 1991, JoF 46(2):733-746)
-----------------------------------------------------------------------
For each tick:
1. **Quote rule (primary).** If trade price equals the ask, classify as BUY
   (ask-side aggression). If equal to bid, classify as SELL (bid-side aggression).
   ``last`` for spot CFDs is often zero (broker doesn't populate trade price);
   we substitute ``mid + tick_size_threshold`` heuristic — see below.
2. **Tick test (secondary).** When the trade price is at the mid (or ``last``
   is unavailable / zero), compare to the previous classifiable price:
   higher than prior = BUY, lower than prior = SELL. If equal, inherit the
   prior classification.
3. **Broker BUY/SELL flags (override).** When ``TICK_FLAG_BUY`` (32) or
   ``TICK_FLAG_SELL`` (64) is set, trust the broker classification — these
   are deterministic where present and dominate the quote/tick test.

Lee & Ready report ~85% agreement with true trade direction on NYSE TAQ; for
spot-FX/gold CFDs the accuracy is **broker-dependent and lower** because BUY/SELL
flags are heuristic on non-centralized markets. Treat ``inferred_aggressor`` as
an OBSERVATIONAL feature for ≥30 days before any gating decision.

Broker flag caveat (verified empirically 2026-04-25 against this account)
-------------------------------------------------------------------------
For spot gold and FX CFDs:
- ``TICK_FLAG_BID``/``TICK_FLAG_ASK`` are reliable (deterministic from quote
  changes) — used by every broker.
- ``TICK_FLAG_BUY``/``TICK_FLAG_SELL`` exist in the MT5 SDK but **are NOT
  populated by this broker** for any of XAUUSD / US30.cash / USDJPY / GBPJPY /
  GBPUSD. Empirical probe over 13,140 ticks across 5 symbols on 2026-04-24
  Friday NY session: 0/13,140 had either flag set. **Operating implication**:
  the broker-flag override path in ``classify_aggressor`` is dead code on this
  account — every tick falls through to the quote rule + tick test. The
  ``classify_aggressor`` keeps the broker-flag override as a future-proofing
  measure for the day we move to a futures-enabled broker (Layer 6 in the
  roadmap, Databento-backed CME GC).
- ``volume_real`` and ``volume`` are uniformly **zero** on this broker for
  spot CFDs. ``last`` is also uniformly zero. The tick stream is therefore
  bid/ask only.
- The ``volume`` accumulator in this module substitutes 1.0 per tick when the
  raw volume is 0, so cumulative_delta degrades gracefully into a count delta
  (buy_count − sell_count). This matches Lee-Ready intent for FX where tick
  volume is a count proxy in any case.

**Honest accuracy expectation.** With BUY/SELL flags absent and last==0, the
classifier reduces to the tick test alone (uptick → buy, downtick → sell,
flat → inherit). On synthetic Brownian motion that achieves ≥85% accuracy
relative to ground truth (see ``test_tick_test_synthetic_geometric_brownian``).
On real broker quote dynamics — where bid/ask updates are heuristic and the
broker may push quotes for inventory reasons unrelated to flow direction —
accuracy is **broker-dependent and likely 60-80%**. Treat ``inferred_aggressor``
as observational for ≥30 days before any gating decision.

Output schema (Parquet)
-----------------------
Per-tick row:

================  =========  ==========================================
Column            dtype      Description
================  =========  ==========================================
ts_utc            datetime64 UTC timestamp (millisecond precision)
ts_msc            int64      MT5 time_msc (raw, used for dedup)
bid               float64    Bid price at tick
ask               float64    Ask price at tick
last              float64    Last trade price (often 0 for spot CFDs)
volume            float64    Tick volume (real for futures, tick-count for spot)
flags             int32      MT5 TICK_FLAG_* OR-encoded
inferred_aggressor object    "buy" / "sell" / "neutral" (Lee-Ready)
================  =========  ==========================================

Files: ``data/ticks/{SYMBOL}/{YYYY-MM-DD}.parquet``. Daily files appended in
batches; last_msc state in ``data/ticks/{SYMBOL}/.state.json``.

CLI usage
---------
::

    python -m src.components.tick_capture --symbol XAUUSD --mt5-symbol XAUUSD
    python -m src.components.tick_capture --symbol US30_cash --mt5-symbol US30.cash
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from src.safety.runtime_halt import append_runtime_halt_audit, read_runtime_halt_state

logger = logging.getLogger(__name__)

TICK_CORRUPT_QUARANTINE_DIRNAME = "_corrupt_quarantine"

# Default poll interval (seconds). 1-5s recommended; 2s is a good default.
DEFAULT_POLL_INTERVAL_SEC = 2.0

# How many ticks to fetch on each poll (cap).
DEFAULT_FETCH_COUNT = 10000

# Backoff on transient MT5 errors.
INITIAL_BACKOFF_SEC = 1.0
MAX_BACKOFF_SEC = 60.0

# Stale-tick warning window (seconds during market hours).
DEFAULT_STALE_TICK_WARN_SEC = 30.0

# Buffer flush threshold (rows). Avoids per-tick disk I/O.
DEFAULT_FLUSH_BATCH = 500

# Maximum time to keep a non-empty buffer in memory before flushing. This
# keeps lower-volume symbols observable and reduces crash-loss of sparse ticks.
DEFAULT_FLUSH_INTERVAL_SEC = 60.0

# Storage root.
TICKS_ROOT = Path("data/ticks")

# MT5 tick-flag bit values (per MT5 Python docs / mql5.com forum).
TICK_FLAG_BID = 2
TICK_FLAG_ASK = 4
TICK_FLAG_LAST = 8
TICK_FLAG_VOLUME = 16
TICK_FLAG_BUY = 32
TICK_FLAG_SELL = 64


# ---------------------------------------------------------------------------
# Lee-Ready aggressor classification
# ---------------------------------------------------------------------------


def classify_aggressor(
    bid: float,
    ask: float,
    last: float,
    flags: int,
    prev_price: Optional[float],
    prev_aggressor: Optional[str],
    *,
    mid_tolerance: float = 1e-9,
) -> str:
    """Classify a single tick as ``buy`` / ``sell`` / ``neutral`` per Lee-Ready 1991.

    The function applies three rules in priority order:

    1. **Broker flags override.** If ``TICK_FLAG_BUY`` is set, return ``"buy"``.
       If ``TICK_FLAG_SELL`` is set, return ``"sell"``. These are
       broker-classified flags — authoritative when populated.
    2. **Quote rule.** When ``last`` is available (>0) and within the
       bid-ask spread:

       - ``last == ask`` (within tolerance) → BUY
       - ``last == bid`` (within tolerance) → SELL
       - ``last`` strictly between bid and ask → check tick test (rule 3).

       When ``last`` is 0 (typical for spot CFDs) we use the **mid-as-trade**
       proxy: a quote update that PUSHED the bid (TICK_FLAG_BID) is treated
       like a sell-side print at bid; pushing the ask (TICK_FLAG_ASK) is
       treated like a buy-side print at ask. When BOTH flags are set, defer
       to the tick test.
    3. **Tick test.** Compare the current effective price (``last`` if >0, else
       ``mid = (bid+ask)/2``) to ``prev_price``. Higher → BUY, lower → SELL,
       equal → inherit ``prev_aggressor`` (or ``"neutral"`` on first tick).

    Parameters
    ----------
    bid, ask, last : float
        Quote and trade prices. ``last`` is typically 0 on spot CFDs.
    flags : int
        MT5 tick flags (OR of TICK_FLAG_* constants).
    prev_price : float, optional
        Previous classifiable price (mid or last). ``None`` on first tick.
    prev_aggressor : str, optional
        Previous aggressor classification. Used for the tick-test tie case.
    mid_tolerance : float
        Floating-point tolerance for "at the bid/ask" comparison.

    Returns
    -------
    str
        One of ``"buy"``, ``"sell"``, ``"neutral"``.

    Notes
    -----
    Lee & Ready (1991) reported ~85% accuracy on NYSE TAQ. On spot-FX/gold
    CFDs accuracy is broker-dependent and lower because:

    - Broker BUY/SELL flags are heuristically set, not exchange-authoritative.
    - ``last`` is rarely populated, forcing fallback to the mid-as-proxy
      heuristic which is noisier than true trade direction.
    """
    # Rule 1: broker-flag override.
    has_buy = bool(flags & TICK_FLAG_BUY)
    has_sell = bool(flags & TICK_FLAG_SELL)
    if has_buy and not has_sell:
        return "buy"
    if has_sell and not has_buy:
        return "sell"

    # Rule 2: quote rule when last is populated.
    if last and last > 0:
        if abs(last - ask) <= mid_tolerance:
            return "buy"
        if abs(last - bid) <= mid_tolerance:
            return "sell"
        # last strictly inside the spread → fall through to tick test
        effective_price = last
    else:
        # Spot CFD path: use bid/ask flag direction as proxy.
        bid_changed = bool(flags & TICK_FLAG_BID)
        ask_changed = bool(flags & TICK_FLAG_ASK)
        if bid_changed and not ask_changed:
            # Bid moved but ask unchanged → seller pressure on the bid side.
            # If the bid moved UP, that's actually buying pressure pushing the
            # bid higher; if it moved DOWN, that's selling pressure. We need
            # prev_price to disambiguate — fall to tick test.
            pass
        if ask_changed and not bid_changed:
            pass
        # Use mid as effective trade-proxy price for the tick test.
        if bid > 0 and ask > 0:
            effective_price = (bid + ask) / 2.0
        elif bid > 0:
            effective_price = bid
        elif ask > 0:
            effective_price = ask
        else:
            return "neutral"  # malformed tick

    # Rule 3: tick test.
    if prev_price is None:
        return "neutral"
    if effective_price > prev_price + mid_tolerance:
        return "buy"
    if effective_price < prev_price - mid_tolerance:
        return "sell"
    # Equal → inherit prior classification.
    return prev_aggressor or "neutral"


def classify_aggressor_series(ticks: Iterable[dict]) -> list[str]:
    """Apply ``classify_aggressor`` to a sequence of tick dicts in time order.

    Each input dict must have keys: ``bid``, ``ask``, ``last``, ``flags``.
    Order matters — the tick test is path-dependent on prior price.

    Returns a list of strings (one per tick) aligned with input order.
    """
    out: list[str] = []
    prev_price: Optional[float] = None
    prev_aggressor: Optional[str] = None
    for t in ticks:
        bid = float(t.get("bid", 0.0) or 0.0)
        ask = float(t.get("ask", 0.0) or 0.0)
        last = float(t.get("last", 0.0) or 0.0)
        flags = int(t.get("flags", 0) or 0)
        agg = classify_aggressor(
            bid, ask, last, flags, prev_price, prev_aggressor
        )
        out.append(agg)
        # Update prev_price using the same logic as classify_aggressor.
        if last and last > 0:
            prev_price = last
        elif bid > 0 and ask > 0:
            prev_price = (bid + ask) / 2.0
        elif bid > 0:
            prev_price = bid
        elif ask > 0:
            prev_price = ask
        prev_aggressor = agg
    return out


# ---------------------------------------------------------------------------
# Tick batch normalization
# ---------------------------------------------------------------------------


def normalize_tick(raw_tick) -> dict:
    """Normalize a single MT5 tick (numpy void / dict / namedtuple) to a dict.

    Handles all three shapes that ``mt5.copy_ticks_from`` and the test mock
    can produce. Returns a dict with stable string keys.
    """
    # numpy void / structured-array record path.
    if hasattr(raw_tick, "dtype") and hasattr(raw_tick, "__getitem__"):
        try:
            return {
                "time": int(raw_tick["time"]),
                "ts_msc": int(raw_tick["time_msc"]),
                "bid": float(raw_tick["bid"]),
                "ask": float(raw_tick["ask"]),
                "last": float(raw_tick["last"]),
                "volume": float(raw_tick["volume"]),
                "flags": int(raw_tick["flags"]),
            }
        except (ValueError, KeyError, IndexError):
            pass

    # Dict path (mock / replay).
    if isinstance(raw_tick, dict):
        return {
            "time": int(raw_tick.get("time", 0)),
            "ts_msc": int(
                raw_tick.get("time_msc", raw_tick.get("ts_msc", 0))
            ),
            "bid": float(raw_tick.get("bid", 0.0) or 0.0),
            "ask": float(raw_tick.get("ask", 0.0) or 0.0),
            "last": float(raw_tick.get("last", 0.0) or 0.0),
            "volume": float(raw_tick.get("volume", 0.0) or 0.0),
            "flags": int(raw_tick.get("flags", 0) or 0),
        }

    # Namedtuple-ish path.
    return {
        "time": int(getattr(raw_tick, "time", 0)),
        "ts_msc": int(getattr(raw_tick, "time_msc", 0)),
        "bid": float(getattr(raw_tick, "bid", 0.0) or 0.0),
        "ask": float(getattr(raw_tick, "ask", 0.0) or 0.0),
        "last": float(getattr(raw_tick, "last", 0.0) or 0.0),
        "volume": float(getattr(raw_tick, "volume", 0.0) or 0.0),
        "flags": int(getattr(raw_tick, "flags", 0) or 0),
    }


def annotate_aggressor(ticks: list[dict],
                        prev_price: Optional[float] = None,
                        prev_aggressor: Optional[str] = None,
                        broker_offset_seconds: int = 0) -> tuple[list[dict], Optional[float], Optional[str]]:
    """Add ``inferred_aggressor`` and ``ts_utc`` fields to each tick dict in-place.

    Returns (annotated_list, last_price, last_aggressor) so callers can carry
    state across batches without re-classifying old ticks.

    Broker-offset convention (Issue #16, 2026-04-28)
    ------------------------------------------------
    The MT5 SDK reports ``tick.time_msc`` in **broker server time**, not UTC
    (per the same audit that produced commit 5c66ee8). On a +3 broker
    (redacted_account-Server 2) a tick captured at 14:30:00 UTC arrives with
    ``time_msc`` corresponding to 17:30:00. Pre-fix, ``ts_utc`` was simply
    ``datetime.fromtimestamp(ts_msc/1000, tz=timezone.utc)`` which mis-
    labelled broker-localized seconds as UTC. Downstream lookups in
    ``tick_features._read_ticks_for_bar`` then computed
    ``(df['ts_utc'] >= bar_open_ts) & (df['ts_utc'] < bar_close_ts)``
    in true UTC and missed every row by exactly ``broker_offset_seconds``.

    Fix: subtract ``broker_offset_seconds`` from the broker-time epoch
    BEFORE constructing the timezone-aware datetime. The ``ts_msc`` column
    is preserved as-is (broker time, dedup key — production tests assert
    on that), but ``ts_utc`` is now genuine UTC.

    Backward-compat: ``broker_offset_seconds=0`` (the default) reproduces
    the legacy behavior bit-exactly. Existing tests that pass tick batches
    without an offset get the same datetime values they always did.
    """
    if not ticks:
        return ticks, prev_price, prev_aggressor
    aggressors: list[str] = []
    p = prev_price
    a = prev_aggressor
    for t in ticks:
        bid = float(t.get("bid", 0.0) or 0.0)
        ask = float(t.get("ask", 0.0) or 0.0)
        last = float(t.get("last", 0.0) or 0.0)
        flags = int(t.get("flags", 0) or 0)
        agg = classify_aggressor(bid, ask, last, flags, p, a)
        aggressors.append(agg)
        if last and last > 0:
            p = last
        elif bid > 0 and ask > 0:
            p = (bid + ask) / 2.0
        elif bid > 0:
            p = bid
        elif ask > 0:
            p = ask
        a = agg
    offset_int = int(broker_offset_seconds or 0)
    for t, agg in zip(ticks, aggressors):
        t["inferred_aggressor"] = agg
        # ts_utc: derive from ts_msc (millisecond) for sub-second precision.
        # Subtract broker offset so the UTC datetime is TRUE UTC and bar-
        # window lookups in tick_features find the rows.
        ts_msc = int(t.get("ts_msc", 0) or 0)
        if ts_msc > 0:
            true_utc_seconds = (ts_msc / 1000.0) - offset_int
            # Guard against pre-epoch values from a misconfigured offset:
            # fromtimestamp with a negative epoch is platform-dependent on
            # Windows. Clamp at 0 (1970-01-01) — the lookup will simply
            # miss, which is the correct fail-open behavior.
            if true_utc_seconds < 0:
                true_utc_seconds = 0.0
            t["ts_utc"] = datetime.fromtimestamp(true_utc_seconds, tz=timezone.utc)
        else:
            raw_seconds = int(t.get("time", 0) or 0) - offset_int
            if raw_seconds < 0:
                raw_seconds = 0
            t["ts_utc"] = datetime.fromtimestamp(raw_seconds, tz=timezone.utc)
    return ticks, p, a


# ---------------------------------------------------------------------------
# Parquet storage
# ---------------------------------------------------------------------------


def parquet_path_for(symbol: str, day: date, root: Path = TICKS_ROOT) -> Path:
    """Return the canonical Parquet path for a (symbol, date) pair."""
    return root / symbol / f"{day.isoformat()}.parquet"


def state_path_for(symbol: str, root: Path = TICKS_ROOT) -> Path:
    """Return the per-symbol state file path (last_msc + last classifier state)."""
    return root / symbol / ".state.json"


def _quarantine_corrupt_parquet(out_path: Path, reason: Exception) -> Path | None:
    if not out_path.exists():
        return None
    quarantine_dir = out_path.parent / TICK_CORRUPT_QUARANTINE_DIRNAME
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    quarantine_path = quarantine_dir / f"{out_path.stem}.{stamp}.corrupt{out_path.suffix}"
    shutil.move(str(out_path), str(quarantine_path))
    quarantine_path.with_suffix(quarantine_path.suffix + ".json").write_text(
        json.dumps(
            {
                "schema_version": "gtos_tick_corrupt_parquet_quarantine_v1",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "original_path": str(out_path),
                "quarantine_path": str(quarantine_path),
                "reason": str(reason),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return quarantine_path


def write_ticks_parquet(ticks: list[dict], out_path: Path,
                        compression: str = "snappy") -> int:
    """Write/append a batch of annotated tick dicts to a daily Parquet file.

    If the file exists, the new rows are concatenated with the existing rows
    (read → concat → write). For our daily volumes (~80-150k rows for XAU,
    ~25-40 MB raw), a full read-write round-trip per flush is fast enough
    (<200ms typical) and avoids the operational complexity of Parquet's
    incremental row-group APIs. For higher-frequency symbols a row-group
    streaming writer would be preferred.

    Returns the row count actually written.
    """
    if not ticks:
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Lazy import to keep test paths runnable without pyarrow installed.
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    # Build DataFrame with explicit dtypes.
    df = pd.DataFrame([
        {
            "ts_utc": t["ts_utc"],
            "ts_msc": int(t.get("ts_msc", 0) or 0),
            "bid": float(t.get("bid", 0.0) or 0.0),
            "ask": float(t.get("ask", 0.0) or 0.0),
            "last": float(t.get("last", 0.0) or 0.0),
            "volume": float(t.get("volume", 0.0) or 0.0),
            "flags": int(t.get("flags", 0) or 0),
            "inferred_aggressor": str(t.get("inferred_aggressor", "neutral")),
        }
        for t in ticks
    ])
    # Ensure timezone-aware datetime column.
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)

    if out_path.exists():
        try:
            existing = pq.read_table(str(out_path)).to_pandas()
            df = pd.concat([existing, df], ignore_index=True)
            # De-dup by ts_msc (defensive — caller should have done this).
            df = df.drop_duplicates(subset=["ts_msc"], keep="last").reset_index(drop=True)
        except Exception as e:
            # Preserve corrupt evidence before starting a fresh canonical file.
            quarantine_path = _quarantine_corrupt_parquet(out_path, e)
            logger.error(
                "Existing Parquet at %s is corrupt (%s); quarantined to %s "
                "before starting a fresh segment",
                out_path,
                e,
                quarantine_path,
            )

    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, str(out_path), compression=compression)
    return len(ticks)


# ---------------------------------------------------------------------------
# Stateful capture daemon
# ---------------------------------------------------------------------------


@dataclass
class CaptureState:
    """In-memory state for a single-symbol tick capture session."""

    symbol: str
    last_msc: int = 0
    last_price: Optional[float] = None
    last_aggressor: Optional[str] = None
    last_tick_at: float = 0.0  # monotonic time of most recent tick fetched
    buffer: list[dict] = field(default_factory=list)
    total_ticks_written: int = 0
    heartbeat_name: Optional[str] = None


def load_state(symbol: str, root: Path = TICKS_ROOT) -> CaptureState:
    """Load saved state for ``symbol`` (or fresh state if absent/corrupt)."""
    state = CaptureState(symbol=symbol)
    p = state_path_for(symbol, root=root)
    if not p.exists():
        return state
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        state.last_msc = int(data.get("last_msc", 0) or 0)
        lp = data.get("last_price")
        state.last_price = float(lp) if lp is not None else None
        state.last_aggressor = data.get("last_aggressor")
        state.total_ticks_written = int(data.get("total_ticks_written", 0) or 0)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        logger.warning("Could not load tick state for %s (%s); starting fresh", symbol, e)
    return state


def save_state(state: CaptureState, root: Path = TICKS_ROOT) -> None:
    """Persist state to disk atomically (write-then-rename)."""
    p = state_path_for(state.symbol, root=root)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + f".tmp{os.getpid()}")
    payload = {
        "symbol": state.symbol,
        "last_msc": state.last_msc,
        "last_price": state.last_price,
        "last_aggressor": state.last_aggressor,
        "total_ticks_written": state.total_ticks_written,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f)
    os.replace(str(tmp), str(p))


def fetch_new_ticks(mt5_module, symbol: str, last_msc: int,
                    count: int = DEFAULT_FETCH_COUNT) -> list[dict]:
    """Fetch ticks since ``last_msc`` for ``symbol``.

    Uses ``mt5.copy_ticks_from(symbol, datetime, count, COPY_TICKS_ALL)``.
    The MT5 SDK takes a ``datetime`` (truncates to seconds), so we fetch
    from ``floor(last_msc/1000)`` and filter by ``time_msc > last_msc``.

    ``last_msc`` is persisted exactly as MT5 reports it: broker server time.
    On redacted_account/MT5, ``copy_ticks_from`` must be queried in the same
    broker-time epoch space as the returned ``time_msc`` values. Do not
    subtract ``broker_offset_seconds`` here; offset correction belongs only in
    the stored ``ts_utc`` column.

    Returns a list of normalized tick dicts (see ``normalize_tick``).
    Raises any underlying MT5 exception (caller handles backoff).
    """
    if last_msc <= 0:
        # Cold start: fetch the last few seconds of ticks to seed state.
        from_dt = datetime.now(tz=timezone.utc).replace(microsecond=0)
    else:
        # Subtract 1 second of safety margin so we don't miss ticks at the boundary.
        from_dt = datetime.fromtimestamp(max(0, (last_msc // 1000) - 1), tz=timezone.utc)

    raw = mt5_module.copy_ticks_from(symbol, from_dt, count, mt5_module.COPY_TICKS_ALL)
    if raw is None:
        # MT5 returned None — could be transient or no-data. Caller decides.
        return []

    out: list[dict] = []
    for r in raw:
        d = normalize_tick(r)
        if d["ts_msc"] > last_msc:
            out.append(d)
    return out


def run_capture_loop(
    mt5_module,
    symbol: str,
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SEC,
    flush_batch: int = DEFAULT_FLUSH_BATCH,
    flush_interval_sec: float = DEFAULT_FLUSH_INTERVAL_SEC,
    stale_warn_sec: float = DEFAULT_STALE_TICK_WARN_SEC,
    root: Path = TICKS_ROOT,
    stop_predicate=None,
    broker_offset_seconds: int = 0,
    heartbeat_name: str | None = None,
) -> CaptureState:
    """Run the capture daemon for ``symbol`` until ``stop_predicate`` returns True.

    ``stop_predicate`` is a zero-arg callable. Pass ``lambda: SHUTDOWN`` to make
    the loop exit on a signal handler. If ``None``, the loop runs forever.

    ``broker_offset_seconds`` is the broker server-time offset relative to UTC
    (e.g. +10800 for redacted_account-Server 2's UTC+3). It is forwarded to
    ``annotate_aggressor`` so the parquet ``ts_utc`` column lands in true
    UTC instead of broker time. The default ``0`` reproduces legacy
    behavior (used by tests + UTC-broker hosts).

    Returns the final CaptureState (caller can persist).

    Errors
    ------
    Transient MT5 errors trigger exponential backoff (1s → 60s cap). The loop
    NEVER aborts — it logs and retries. Hard exit only on stop_predicate.
    """
    state = load_state(symbol, root=root)
    state.heartbeat_name = heartbeat_name
    backoff = INITIAL_BACKOFF_SEC
    state.last_tick_at = time.monotonic()
    last_flush_at = time.monotonic()
    last_data_progress_at: datetime | None = None

    # Open the daily output path lazily — symbol dir created on first flush.
    while True:
        if stop_predicate is not None and stop_predicate():
            break
        loop_started = time.monotonic()
        try:
            new_ticks = fetch_new_ticks(mt5_module, symbol, state.last_msc)
        except Exception as e:  # noqa: BLE001 — daemon must survive any error
            logger.error("[%s] tick fetch error: %s — backing off %.1fs",
                          symbol, e, backoff)
            _sleep_or_exit(backoff, stop_predicate)
            backoff = min(MAX_BACKOFF_SEC, backoff * 2.0)
            continue

        backoff = INITIAL_BACKOFF_SEC  # reset on any successful poll

        if new_ticks:
            # Annotate aggressor with carry-over state.
            new_ticks, state.last_price, state.last_aggressor = annotate_aggressor(
                new_ticks, state.last_price, state.last_aggressor,
                broker_offset_seconds=broker_offset_seconds,
            )
            state.buffer.extend(new_ticks)
            state.last_msc = max(state.last_msc,
                                  max(t["ts_msc"] for t in new_ticks))
            state.last_tick_at = time.monotonic()
            last_data_progress_at = datetime.now(tz=timezone.utc)

        # Stale-tick warning.
        elapsed_since_tick = time.monotonic() - state.last_tick_at
        if elapsed_since_tick > stale_warn_sec:
            logger.warning("[%s] no ticks for %.1fs — possible market closed or feed stalled",
                            symbol, elapsed_since_tick)

        try:
            from src.components import mt5_daemon_runtime as _runtime
            _runtime.write_daemon_heartbeat(
                state.heartbeat_name or f"tick_capture_{state.symbol}",
                last_progress_at=last_data_progress_at,
                extra={
                    "symbol": state.symbol,
                    "total_ticks_written": state.total_ticks_written,
                    "last_msc": state.last_msc,
                    "liveness_utc": datetime.now(tz=timezone.utc).isoformat(),
                    "last_poll_status": "ok",
                    "last_poll_new_tick_count": len(new_ticks),
                    "last_progress_source": (
                        "current_poll_new_ticks"
                        if new_ticks
                        else "no_new_ticks_valid_liveness_only"
                    ),
                },
            )
        except Exception:  # noqa: BLE001
            pass

        # Flush buffer when threshold reached, on UTC-day boundary, or after a
        # bounded interval so sparse tick streams still persist progress.
        if state.buffer and (
            len(state.buffer) >= flush_batch
            or _crosses_utc_day(state.buffer)
            or (time.monotonic() - last_flush_at) >= flush_interval_sec
        ):
            flushed = _flush_buffer(state, root=root)
            if flushed > 0:
                last_flush_at = time.monotonic()

        # Sleep till next poll.
        sleep_for = max(0.0, poll_interval - (time.monotonic() - loop_started))
        _sleep_or_exit(sleep_for, stop_predicate)

    # Final flush on shutdown.
    if state.buffer:
        _flush_buffer(state, root=root)
    save_state(state, root=root)
    return state


def _crosses_utc_day(ticks: list[dict]) -> bool:
    """Return True if the buffer contains ticks from more than one UTC day."""
    if len(ticks) < 2:
        return False
    first_day = ticks[0]["ts_utc"].date()
    last_day = ticks[-1]["ts_utc"].date()
    return first_day != last_day


def _flush_buffer(state: CaptureState, root: Path = TICKS_ROOT) -> int:
    """Group buffered ticks by UTC day and write each group to its day file.

    Returns total rows flushed. Updates ``state.total_ticks_written``.
    Empties ``state.buffer`` on success; on partial failure, retains the
    failed rows for retry on the next flush.
    """
    if not state.buffer:
        return 0

    by_day: dict[date, list[dict]] = {}
    for t in state.buffer:
        d = t["ts_utc"].date()
        by_day.setdefault(d, []).append(t)

    flushed = 0
    failed_rows: list[dict] = []
    for day, group in by_day.items():
        out = parquet_path_for(state.symbol, day, root=root)
        try:
            write_ticks_parquet(group, out)
            flushed += len(group)
        except Exception as e:  # noqa: BLE001
            logger.error("[%s] parquet write failed for %s: %s — retaining for retry",
                          state.symbol, day, e)
            failed_rows.extend(group)

    state.total_ticks_written += flushed
    state.buffer = failed_rows
    save_state(state, root=root)
    if flushed > 0:
        logger.info("[%s] flushed %d ticks (total=%d)", state.symbol, flushed,
                     state.total_ticks_written)
        # Update daemon heartbeat on every successful flush so an out-of-band
        # monitor can distinguish "PID alive AND producing data" from "PID
        # alive but feed silent". Best-effort -- never raises into the loop.
        try:
            from src.components import mt5_daemon_runtime as _runtime
            heartbeat_now = datetime.now(tz=timezone.utc)
            _runtime.write_daemon_heartbeat(
                state.heartbeat_name or f"tick_capture_{state.symbol}",
                last_progress_at=heartbeat_now,
                extra={
                    "symbol": state.symbol,
                    "total_ticks_written": state.total_ticks_written,
                    "last_msc": state.last_msc,
                    "liveness_utc": heartbeat_now.isoformat(),
                    "last_poll_status": "flush_success",
                    "last_poll_new_tick_count": flushed,
                    "last_progress_source": "flush_buffer_new_ticks",
                },
            )
        except Exception:  # noqa: BLE001
            # Heartbeat failure must never affect tick capture itself.
            pass
    return flushed


def _sleep_or_exit(seconds: float, stop_predicate) -> None:
    """Sleep in small chunks so stop_predicate can interrupt promptly."""
    if seconds <= 0:
        return
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if stop_predicate is not None and stop_predicate():
            return
        time.sleep(min(0.25, end - time.monotonic()))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


_SHUTDOWN = False


def _signal_handler(signum, frame):  # noqa: ARG001
    global _SHUTDOWN  # noqa: PLW0603
    logger.warning("Received signal %s — shutting down tick capture", signum)
    _SHUTDOWN = True


def _set_shutdown() -> None:
    """Module-level setter usable as a callback (e.g. signal handlers).

    Extracted so ``mt5_daemon_runtime.install_signal_handlers`` can flip
    the same flag the legacy ``_signal_handler`` uses.
    """
    global _SHUTDOWN  # noqa: PLW0603
    _SHUTDOWN = True


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry. Connects to MT5 and runs the capture loop until SIGINT/SIGTERM.

    Architectural notes (2026-04-28 sibling-daemon-stability fix)
    ------------------------------------------------------------
    Three failure modes from the old version are now handled via
    ``src.components.mt5_daemon_runtime``:

    1. **Single-instance enforcement.** Multiple python tick_capture
       processes for the same symbol used to accumulate when the watchdog
       launched via ``cmd.exe /c`` -- the lock file held the cmd.exe PID,
       which separated from the python child on Windows. Now the python
       daemon claims a per-symbol lock with own-PID at startup, exits
       cleanly if another live python with matching ``--symbol`` argv is
       already holding it.
    2. **Symbol subscription verification.** ``ensure_mt5_symbol_ready``
       always calls ``symbol_select(sym, True)`` and verifies a fresh
       tick arrives, with backoff-and-retry. The previous code only
       re-selected when ``info.visible`` was False -- which empirically
       mis-reported True for FX/metals on redacted_account after reconnects,
       leading to 32+ hours of "no ticks" warnings on a daemon that
       never got a real subscription.
    3. **Alive-but-stalled detection.** Each successful flush updates
       ``pipeline_state/daemon_heartbeat_tick_capture_{SYMBOL}.json`` with
       a ``last_progress_utc`` field. An out-of-band monitor (or future
       watchdog upgrade) can detect "PID alive but no progress in N
       minutes" -- the failure mode the old PID-only check missed.

    The capture loop remains observation-only; it writes tick data and daemon
    heartbeats but never places or manages orders.
    """
    parser = argparse.ArgumentParser(description="GTOS MT5 Tick Capture Daemon")
    parser.add_argument("--symbol", required=True,
                         help="Canonical GTOS symbol (e.g., XAUUSD, US30_cash)")
    parser.add_argument("--mt5-symbol", default=None,
                         help="Broker MT5 symbol if different (e.g., US30.cash)")
    parser.add_argument("--poll", type=float, default=DEFAULT_POLL_INTERVAL_SEC,
                         help="Poll interval seconds (default 2.0)")
    parser.add_argument("--flush-batch", type=int, default=DEFAULT_FLUSH_BATCH,
                         help="Flush buffer to disk every N ticks (default 500)")
    parser.add_argument("--flush-interval-sec", type=float, default=DEFAULT_FLUSH_INTERVAL_SEC,
                         help="Flush a non-empty buffer after N seconds (default 60)")
    parser.add_argument("--stale-warn-sec", type=float, default=DEFAULT_STALE_TICK_WARN_SEC,
                         help="Warn if no tick for N seconds (default 30)")
    parser.add_argument("--ticks-root", default=str(TICKS_ROOT),
                         help="Storage root directory (default data/ticks)")
    parser.add_argument("--terminal-path", default=None,
                         help="Optional MT5 terminal64.exe path. Overrides "
                              "GTOS_MT5_TERMINAL_PATH.")
    parser.add_argument("--runtime-namespace", default=None,
                         help="Optional broker/account namespace for lock, "
                              "heartbeat, and default tick data root.")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--skip-tick-freshness-check", action="store_true",
                         help="Allow startup with a stale tick (e.g., weekend testing); "
                              "default behavior fails fast if MT5 returns stale ticks "
                              "during market hours.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    halt_config = {
        "runtime_control": {
            "enabled": True,
            "audit_log_path": "pipeline_state/runtime_control_atomic_halt_audit.jsonl",
        }
    }
    halt_snapshot = read_runtime_halt_state(halt_config)
    if halt_snapshot.active:
        append_runtime_halt_audit(
            action="tick_capture_start",
            snapshot=halt_snapshot,
            context={
                "component": "tick_capture",
                "symbol": args.symbol,
                "mt5_symbol": args.mt5_symbol or args.symbol,
            },
            config=halt_config,
        )
        logger.info(
            "%s active; tick capture exiting before lock/MT5 interaction.",
            halt_snapshot.status,
        )
        return 0

    from src.utils.broker_profile import (
        namespaced_daemon_name,
        namespaced_directory_path,
        resolve_mt5_terminal_path,
        sanitize_namespace,
    )

    canonical_symbol = args.symbol
    mt5_symbol = args.mt5_symbol or canonical_symbol
    namespace = sanitize_namespace(
        args.runtime_namespace or os.environ.get("GTOS_RUNTIME_NAMESPACE", "")
    )

    # Single-instance guard. The argv marker is the canonical symbol with
    # the option flag prefix so a sibling daemon for a DIFFERENT symbol does
    # not match. Failure to acquire is a clean non-fatal exit -- the
    # already-running python will continue operating.
    from src.components import mt5_daemon_runtime as _runtime

    lock_name = namespaced_daemon_name(f"tick_capture_{canonical_symbol}", namespace)
    argv_marker = f"-m src.components.tick_capture --symbol {canonical_symbol}"
    acquired, conflicting = _runtime.acquire_single_instance_lock(
        lock_name, argv_marker=argv_marker,
    )
    if not acquired:
        logger.warning(
            "[%s] another tick_capture is already running (pid=%s) -- exiting cleanly",
            canonical_symbol, conflicting,
        )
        return 0  # exit 0 so the watchdog does not "restart" us in a loop

    try:
        import MetaTrader5 as mt5_module
    except ImportError:
        logger.error("MetaTrader5 package not installed — daemon cannot run")
        _runtime.release_single_instance_lock(lock_name)
        return 2

    terminal_path = resolve_mt5_terminal_path(explicit=args.terminal_path)
    init_kwargs = {"path": terminal_path} if terminal_path else {}
    if not mt5_module.initialize(**init_kwargs):
        logger.error("MT5 initialize failed: %s", mt5_module.last_error())
        _runtime.release_single_instance_lock(lock_name)
        return 3

    # Detect broker offset ONCE on startup. Brokers run UTC+0/+2/+3
    # depending on the firm; redacted_account-Server 2 is +3 (verified live
    # 2026-04-28). With offset=0 against a +3 broker, `_tick_is_fresh`
    # rejects every live tick as 3h future-dated and the daemon fails its
    # readiness check forever -- the failure mode this fix removes.
    broker_offset_seconds = _runtime.detect_broker_offset_seconds(
        mt5_module,
        symbols=(mt5_symbol,) + _runtime.DEFAULT_OFFSET_PROBE_SYMBOLS,
    )
    if broker_offset_seconds:
        logger.info(
            "[%s] detected broker offset = %+ds (%+.1fh ahead of UTC)",
            canonical_symbol, broker_offset_seconds,
            broker_offset_seconds / 3600.0,
        )

    try:
        ready, reason = _runtime.ensure_mt5_symbol_ready(
            mt5_module, mt5_symbol,
            require_fresh_tick=not args.skip_tick_freshness_check,
            broker_offset_seconds=broker_offset_seconds,
        )
        if not ready:
            logger.error(
                "[%s] subscription readiness check failed: %s -- exiting so "
                "watchdog can re-launch with a fresh MT5 connection",
                mt5_symbol, reason,
            )
            return 4

        # Install signal handlers via the shared helper (covers SIGINT +
        # SIGTERM uniformly across daemons).
        _runtime.install_signal_handlers(_set_shutdown)
        # Keep the legacy direct-handler binding for backward-compat with
        # tests that patch ``signal.signal`` differently.
        signal.signal(signal.SIGINT, _signal_handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _signal_handler)

        logger.info("Tick capture starting for %s (mt5_symbol=%s, poll=%.1fs)",
                    canonical_symbol, mt5_symbol, args.poll)
        # Initial heartbeat with last_progress=now so an "alive but never
        # produced" daemon is still observable on the first cycle.
        _runtime.write_daemon_heartbeat(
            lock_name,
            last_progress_at=datetime.now(tz=timezone.utc),
            extra={
                "symbol": canonical_symbol,
                "mt5_symbol": mt5_symbol,
                "broker_offset_seconds": broker_offset_seconds,
                "liveness_utc": datetime.now(tz=timezone.utc).isoformat(),
                "last_poll_status": "startup_ready",
                "last_poll_new_tick_count": 0,
                "last_progress_source": "startup_readiness_check",
            },
        )

        # We use the canonical_symbol for the storage path so files are
        # broker-agnostic (US30_cash directory regardless of broker rename).
        # But fetch_new_ticks needs the broker MT5 symbol — pass through the
        # mt5_module wrapper.
        class _SymbolAlias:
            def __init__(self, real_mt5, mt5_sym):
                self._real = real_mt5
                self._mt5_sym = mt5_sym
                self.COPY_TICKS_ALL = real_mt5.COPY_TICKS_ALL

            def copy_ticks_from(self, symbol, dt, count, flags):  # noqa: ARG002
                # Always re-route to the broker MT5 symbol.
                return self._real.copy_ticks_from(self._mt5_sym, dt, count, flags)

        wrapper = _SymbolAlias(mt5_module, mt5_symbol)

        default_ticks_root = Path(args.ticks_root)
        ticks_root = (
            default_ticks_root
            if args.ticks_root != str(TICKS_ROOT)
            else namespaced_directory_path(default_ticks_root, namespace)
        )
        run_capture_loop(
            wrapper,
            canonical_symbol,
            poll_interval=args.poll,
            flush_batch=args.flush_batch,
            flush_interval_sec=args.flush_interval_sec,
            stale_warn_sec=args.stale_warn_sec,
            root=ticks_root,
            stop_predicate=lambda: _SHUTDOWN,
            broker_offset_seconds=broker_offset_seconds,
            heartbeat_name=lock_name,
        )
    finally:
        try:
            mt5_module.shutdown()
        except Exception:  # noqa: BLE001
            pass
        # Always release the single-instance lock on shutdown so a
        # subsequent restart can claim it cleanly.
        _runtime.release_single_instance_lock(lock_name)

    return 0


if __name__ == "__main__":
    sys.exit(main())
