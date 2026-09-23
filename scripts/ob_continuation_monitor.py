#!/usr/bin/env python3
"""OB continuation rolling-50 monitor — primary edge-decay sentinel.

Purpose
-------
The system's edge is **H1 OB zone precision** (stop-cascade mean-reversion to
pre-cascade equilibrium). Baseline continuation rate is ~70% mechanically
across 13 instruments (+19pp above shuffled baseline). Per ``CLAUDE.md``, this
rate is the **#1 primary decay metric** — ahead of SPRT, CUSUM, and the
emergency stops. If continuation drops below 60% over a rolling-50 window,
the edge is degrading and trading should be reviewed.

This script computes that rolling-50 rate **once per UTC day**, per-instrument
and portfolio-wide, by replaying the same methodology used by
``scripts/ob_retest_comprehensive.py`` against the historical M15 data under
``data/historical/``. It is cron-runnable, observation-only, and does
not touch live trading state. Alarms are CRITICAL-logged and (best-effort)
Telegram-pushed via ``src.notifications.notify_alert``.

Methodology source (exact line references)
------------------------------------------
Retest + classification logic mirrors ``scripts/ob_retest_comprehensive.py``:

* **OB detection** — ``identify_order_blocks`` in
  ``src/components/market_state.py`` (lines 380-461). Only fresh (unmitigated)
  OBs are candidates; mitigated OBs are skipped (``ob_retest_comprehensive.py``
  lines 234-236).

* **Retest trigger** — first M15 candle in which the zone is entered
  chronologically forward from formation:
    * bullish OB: ``candle.low <= ob.high``
    * bearish OB: ``candle.high >= ob.low``
  (``ob_retest_comprehensive.py`` lines 413, 448). A 192-candle (48h) scan
  window is applied (line 407).

* **Entry price** — candle.close if inside/above the zone, else next
  candle.open (lines 422-429 bullish, 453-460 bearish).

* **SL buffer** — configured symbols use the same per-symbol absolute
  ``config/agent_config.yaml`` ``symbols.*.risk.sl_buffer_dollars`` values as
  the current vNext surface. Unknown symbols fall back to the older reference
  percent-style formula so they still get a non-zero buffer.

* **Classification** — walk forward ``range(1, 13)`` = 12 M15 candles (3h).
  ``target_distance = 1.5 * sl_distance`` (line 531). Outcomes:
    * CONTINUED iff favorable side hit ``entry ± target_distance`` BEFORE SL
      is hit (lines 537-593, ``hit_target_3h=True``).
    * REVERSED iff SL hit without target first, OR 12-candle horizon expires
      with neither side hit (``hit_target_3h=False``).
    * UNRESOLVED — our extension only: fewer than 12 forward candles
      available (dataset end). These are skipped entirely from the rolling
      window (they are neither wins nor losses, just undetermined).

Cross-check: ``scripts/ob_retest_pressure_test.py`` does NOT redefine the
rule — it imports ``detect_retests`` from ``ob_retest_comprehensive``
directly (line 47 of that file). The rule is canonical.

Output schema (``shadow_logs/ob_continuation_daily.csv``)
---------------------------------------------------------

    date_utc, scope, window_size, window_start_date, window_end_date,
    continuation_count, total_count, rate_pct, alarm_fired,
    insufficient_sample

One row per (date_utc, scope) — re-runs on the same UTC day dedupe: the most
recent row wins (read-existing + dedupe + rewrite, atomic via os.replace).
Scopes: every configured Stage08 broker-native vNext symbol + ``PORTFOLIO``
(chronologically merged).

Runtime behavior
----------------
Per-symbol: load M15 CSV → detect OBs (on the full M15 series, using the
same market_state primitives the live pipeline uses) → detect first retest
per OB → resolve outcome → build chronological ResolvedRetest list.
Portfolio = merge-sort all ResolvedRetests across symbols by retest time,
then take most-recent 50.

Cold-start: CSV is created with header on first write. Missing symbol CSV:
logged, emits a ``total_count=0`` row for that symbol, continues.

Exit codes
----------
    0 — all scopes green (every rate >= ALARM_THRESHOLD_PCT, or insufficient
         data on that scope)
    1 — one or more alarms fired
    2 — unrecoverable load/processing failure (e.g. market_state primitives
         failed to import, or every symbol CSV failed to load)

Design notes (staleness, portfolio mix, idempotence)
----------------------------------------------------

* **Staleness**: the rolling window is the **most recent 50 retests** by
  retest time, regardless of absolute age. A quiet instrument could have a
  window that ends weeks ago — that IS the observation window. We log a
  warning when the newest retest in a scope's window is > 30 days old, but
  do not change behavior. Staleness alarming is deliberately out of scope
  for v1.

* **Portfolio blending**: chronological merge across configured vNext symbols. If one
  symbol is chatty, it dominates the portfolio window. That is the intended
  semantics — "most recent 50 genuine retests across all instruments".

* **Idempotence**: running twice on the same UTC day produces one row per
  (date, scope). We read the existing CSV, drop rows matching today's date
  for the scopes we're about to write, and rewrite atomically.

* **Shape of missing data**: missing M15 CSV → warning + emit a row with
  ``total_count=0``, ``rate_pct=0.0``, ``alarm_fired=false``. The zero-total
  row is informational; alarm is only fired when ``total_count >= WINDOW_SIZE``
  and ``rate_pct < ALARM_THRESHOLD_PCT``.

CLI
---
    python scripts/ob_continuation_monitor.py                # default run
    python scripts/ob_continuation_monitor.py --dry-run      # no CSV, no alerts
    python scripts/ob_continuation_monitor.py --date 2026-04-17 --window-size 50

Test-isolation discipline
-------------------------
All filesystem paths are module-level constants so tests monkeypatch via
``from scripts import ob_continuation_monitor as _mod`` +
``monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "test.csv")``. Writes
under the real ``shadow_logs/`` in a pytest process would trigger the
``ProductionWriteError`` guard in ``tests/conftest.py``.
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Literal, Optional

# ---------------------------------------------------------------------------
# Project-root importability (script is runnable as ``python scripts/...``)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(_PROJECT_ROOT / ".env", override=True)

# Lazy-ish imports — the monkeypatchable I/O layer below may override data
# loaders in tests, but these core imports must succeed or we exit(2).
try:
    from scripts.historical_data_loader import parse_tradingview_csv
    from src.components.market_state import (
        detect_structure_breaks,
        detect_swings,
        identify_order_blocks,
        identify_structure,
    )
except Exception as exc:  # pragma: no cover — import failure handled in run_monitor
    parse_tradingview_csv = None  # type: ignore[assignment]
    detect_swings = None  # type: ignore[assignment]
    identify_structure = None  # type: ignore[assignment]
    detect_structure_breaks = None  # type: ignore[assignment]
    identify_order_blocks = None  # type: ignore[assignment]
    _IMPORT_ERROR: Optional[Exception] = exc
else:
    _IMPORT_ERROR = None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-level constants — tests MUST monkeypatch these on the module object.
# ---------------------------------------------------------------------------

DATA_DIR: Path = _PROJECT_ROOT / "data" / "historical"
OUTPUT_CSV: Path = _PROJECT_ROOT / "shadow_logs" / "ob_continuation_daily.csv"

WINDOW_SIZE: int = 50
ALARM_THRESHOLD_PCT: float = 60.0

SYMBOLS: list[str] = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

# Forward-scan horizon for outcome classification (12 M15 candles = 3h).
# Mirrors ``ob_retest_comprehensive.py`` line 537: ``for j in range(1, 13)``.
RESOLUTION_HORIZON_CANDLES: int = 12

# Retest search window after OB formation (192 M15 candles = 48h).
# Mirrors line 407: ``end_m15_idx = min(start_m15_idx + 192, len(m15_candles))``.
RETEST_SCAN_WINDOW_CANDLES: int = 192

# Target = 1.5 * SL distance (line 531: ``target_distance = 1.5 * sl_distance``).
TARGET_RR: float = 1.5

# Per-symbol SL buffer. Values mirror live ``config/agent_config.yaml``
# ``symbols.*.risk.sl_buffer_dollars`` for the current 24-symbol vNext surface.
# Falls back to the ob_retest_comprehensive percent-style reference default if
# a symbol is missing.
_SL_BUFFER_CONFIG: dict[str, dict] = {
    "AUDJPY": {"mode": "abs", "value": 0.010},
    "AUDUSD": {"mode": "abs", "value": 0.00008},
    "BTCUSD": {"mode": "abs", "value": 50.0},
    "CHFJPY": {"mode": "abs", "value": 0.012},
    "ETHUSD": {"mode": "abs", "value": 5.0},
    "EURGBP": {"mode": "abs", "value": 0.00008},
    "EURJPY": {"mode": "abs", "value": 0.012},
    "EURUSD": {"mode": "abs", "value": 0.00010},
    "GBPJPY": {"mode": "abs", "value": 0.014},
    "GBPUSD": {"mode": "abs", "value": 0.00015},
    "GER40": {"mode": "abs", "value": 1.30},
    "JP225": {"mode": "abs", "value": 50.0},
    "NAS100": {"mode": "abs", "value": 15.0},
    "NZDUSD": {"mode": "abs", "value": 0.00005},
    "SPX500": {"mode": "abs", "value": 2.0},
    "UK100": {"mode": "abs", "value": 1.30},
    "UKOIL_cash": {"mode": "abs", "value": 0.10},
    "US30_cash": {"mode": "abs", "value": 3.75},
    "USDCAD": {"mode": "abs", "value": 0.00010},
    "USDCHF": {"mode": "abs", "value": 0.00010},
    "USDJPY": {"mode": "abs", "value": 0.012},
    "USOIL_cash": {"mode": "abs", "value": 0.10},
    "XAGUSD": {"mode": "abs", "value": 0.03},
    "XAUUSD": {"mode": "abs", "value": 1.20},
}

# Staleness warning threshold — warn if newest retest in window is older.
_STALENESS_WARN_DAYS: int = 30


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


RetestOutcome = Literal["CONTINUED", "REVERSED", "UNRESOLVED"]


@dataclass(frozen=True)
class ResolvedRetest:
    """A single OB retest with a resolved outcome."""
    symbol: str
    ob_type: Literal["bullish", "bearish"]
    ob_formation_time: str          # ISO-8601 UTC
    ob_high: float
    ob_low: float
    retest_time: str                # ISO-8601 UTC of the M15 candle that retested
    entry_price: float
    sl_price: float
    sl_distance: float
    outcome: RetestOutcome


# ---------------------------------------------------------------------------
# Pure helpers (no I/O, no module-state)
# ---------------------------------------------------------------------------


def _parse_candle_time(t: str) -> datetime:
    """Parse candle timestamp string to UTC datetime. Supports the formats
    ``parse_tradingview_csv`` emits (ISO with Z) plus legacy ``YYYY-MM-DD``
    / ``YYYY-MM-DD HH:MM:SS`` just in case.
    """
    # historical_data_loader normalizes to "%Y-%m-%dT%H:%M:%SZ".
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse candle time: {t!r}")


def _sl_buffer_for(symbol: str, ob_edge_price: float) -> float:
    """Return the absolute SL buffer (price units) to apply for *symbol*.

    Configured symbols use fixed absolute buffers (e.g., 1.20 for XAUUSD and
    1.5 pips for GBPUSD). If a symbol has no explicit config, fall back to
    ``0.001 * ob_edge_price`` so unknown symbols still get a non-zero buffer.
    """
    cfg = _SL_BUFFER_CONFIG.get(symbol)
    if cfg is None:
        # Defensive fallback — mirrors XAUUSD-style scaling.
        return 0.001 * ob_edge_price
    if cfg["mode"] == "pct":
        return float(cfg["value"]) * ob_edge_price
    # Absolute buffer — independent of price magnitude.
    return float(cfg["value"])


def classify_retest(
    ob: dict,
    post_retest_candles: list[dict],
) -> RetestOutcome:
    """Classify a retest outcome given forward candles starting from the
    entry candle (inclusive).

    Rule (mirrors ``ob_retest_comprehensive.py`` lines 530-593):

    * ``target_distance = 1.5 * sl_distance``.
    * Walk ``range(1, RESOLUTION_HORIZON_CANDLES + 1)`` = 12 candles AFTER
      the entry candle.
    * bullish OB: SL hit when ``c.low <= sl_price``; target hit when
      ``c.high >= entry + target_distance``. If both in same candle, inspect
      open: open <= sl → SL first, open >= target → target first, else
      conservative = SL.
    * bearish OB: mirrored.
    * CONTINUED if target hit first. REVERSED if SL hit first OR horizon
      expires with neither. UNRESOLVED if fewer than 12 forward candles
      available (dataset truncation).

    ``ob`` must have ``ob_type`` (str), ``entry_price`` (float), ``sl_price``
    (float), ``sl_distance`` (float). ``post_retest_candles`` starts at the
    entry candle (index 0 is the entry candle; we iterate from index 1).
    """
    ob_type = ob["ob_type"]
    entry_price = float(ob["entry_price"])
    sl_price = float(ob["sl_price"])
    sl_distance = float(ob["sl_distance"])
    if sl_distance <= 0:
        return "UNRESOLVED"

    target_distance = TARGET_RR * sl_distance

    # We need 12 candles AFTER entry (indices 1..12). If we don't have them,
    # UNRESOLVED.
    if len(post_retest_candles) < RESOLUTION_HORIZON_CANDLES + 1:
        return "UNRESOLVED"

    for j in range(1, RESOLUTION_HORIZON_CANDLES + 1):
        c = post_retest_candles[j]
        if ob_type == "bullish":
            sl_hit = c["low"] <= sl_price
            tp_hit = c["high"] >= entry_price + target_distance
            if sl_hit and tp_hit:
                # Ambiguous — resolve by open.
                if c["open"] <= sl_price:
                    return "REVERSED"
                if c["open"] >= entry_price + target_distance:
                    return "CONTINUED"
                # Open between SL and TP — conservative = SL.
                return "REVERSED"
            if sl_hit:
                return "REVERSED"
            if tp_hit:
                return "CONTINUED"
        else:  # bearish
            sl_hit = c["high"] >= sl_price
            tp_hit = c["low"] <= entry_price - target_distance
            if sl_hit and tp_hit:
                if c["open"] >= sl_price:
                    return "REVERSED"
                if c["open"] <= entry_price - target_distance:
                    return "CONTINUED"
                return "REVERSED"
            if sl_hit:
                return "REVERSED"
            if tp_hit:
                return "CONTINUED"

    # Horizon expired with neither side hit — in the reference script this is
    # treated as ``hit_target_3h=False`` (i.e., not a continuation). We match
    # that behavior: REVERSED. The decay-monitor's alarm triggers on low
    # continuation rate, so "timed out" must be on the non-win side or the
    # metric would drift upward as OBs consolidate sideways.
    return "REVERSED"


def build_retest_history(
    obs: list,
    m15_candles: list[dict],
    symbol: str,
) -> list[ResolvedRetest]:
    """Walk each OB forward on M15; detect first retest; resolve outcome.

    Mirrors ``ob_retest_comprehensive.detect_retests`` behavior. Unmitigated
    OBs only. 192-candle forward scan cap. First-retest semantics (only the
    initial retest per OB is counted toward the continuation metric —
    subsequent retests are explicitly de-prioritized in the codebase because
    touch-1 WR is 72.7% vs touch-2+ 31.5%).

    Returns the list sorted ascending by retest time.
    """
    if not obs or not m15_candles:
        return []

    # Index M15 candle times → indices for fast formation-time lookup.
    # We scan forward per-OB so no need for a map; just linear scan.

    results: list[ResolvedRetest] = []

    for ob in obs:
        if getattr(ob, "mitigated", False):
            continue

        try:
            ob_time = _parse_candle_time(ob.formation_time)
        except (AttributeError, ValueError):
            continue

        ob_high = float(ob.high)
        ob_low = float(ob.low)
        ob_type = ob.type

        # Find first M15 candle strictly AFTER OB formation time.
        start_idx: Optional[int] = None
        for i, c in enumerate(m15_candles):
            try:
                if _parse_candle_time(c["time"]) > ob_time:
                    start_idx = i
                    break
            except ValueError:
                continue
        if start_idx is None:
            continue

        end_idx = min(start_idx + RETEST_SCAN_WINDOW_CANDLES, len(m15_candles))

        retest_info: Optional[dict] = None
        in_zone = False
        for i in range(start_idx, end_idx):
            c = m15_candles[i]

            if ob_type == "bullish":
                enters = c["low"] <= ob_high
            else:
                enters = c["high"] >= ob_low

            if enters and not in_zone:
                in_zone = True
                # First retest only — build it and break.
                if ob_type == "bullish":
                    if c["close"] >= ob_low:
                        entry_price = float(c["close"])
                        entry_idx = i
                    elif i + 1 < len(m15_candles):
                        entry_price = float(m15_candles[i + 1]["open"])
                        entry_idx = i + 1
                    else:
                        continue
                    buf = _sl_buffer_for(symbol, ob_low)
                    sl_price = ob_low - buf
                else:  # bearish
                    if c["close"] <= ob_high:
                        entry_price = float(c["close"])
                        entry_idx = i
                    elif i + 1 < len(m15_candles):
                        entry_price = float(m15_candles[i + 1]["open"])
                        entry_idx = i + 1
                    else:
                        continue
                    buf = _sl_buffer_for(symbol, ob_high)
                    sl_price = ob_high + buf

                sl_distance = abs(entry_price - sl_price)
                retest_info = {
                    "ob_type": ob_type,
                    "retest_time": c["time"],
                    "entry_price": entry_price,
                    "entry_idx": entry_idx,
                    "sl_price": sl_price,
                    "sl_distance": sl_distance,
                }
                break
            if not enters:
                in_zone = False

        if retest_info is None:
            continue

        # Extract forward window starting at the entry candle (inclusive).
        entry_idx = retest_info["entry_idx"]
        post = m15_candles[entry_idx : entry_idx + RESOLUTION_HORIZON_CANDLES + 1]

        outcome = classify_retest(retest_info, post)

        results.append(ResolvedRetest(
            symbol=symbol,
            ob_type=ob_type,
            ob_formation_time=ob.formation_time,
            ob_high=ob_high,
            ob_low=ob_low,
            retest_time=retest_info["retest_time"],
            entry_price=retest_info["entry_price"],
            sl_price=retest_info["sl_price"],
            sl_distance=retest_info["sl_distance"],
            outcome=outcome,
        ))

    # Chronological sort by retest time.
    results.sort(key=lambda r: r.retest_time)
    return results


def rolling_window(
    resolved: list[ResolvedRetest],
    size: int,
) -> list[ResolvedRetest]:
    """Return the most recent ``size`` retests by retest_time. If fewer than
    ``size`` are available, return all of them. The input is assumed already
    sorted ascending by retest_time (build_retest_history returns sorted).
    """
    if size <= 0:
        return []
    if len(resolved) <= size:
        return list(resolved)
    return resolved[-size:]


def compute_rate(window: list[ResolvedRetest]) -> tuple[int, int, float]:
    """Return (continuation_count, total_count, rate_pct).

    Only CONTINUED / REVERSED are counted. UNRESOLVED are excluded — they
    have no outcome. Zero-total is safe: returns (0, 0, 0.0), no crash.

    ``rate_pct`` is 0.0 for zero-total (the monitor's alarm path must also
    skip zero-total scopes; see ``_should_alarm``).
    """
    counted = [r for r in window if r.outcome in ("CONTINUED", "REVERSED")]
    total = len(counted)
    if total == 0:
        return 0, 0, 0.0
    cont = sum(1 for r in counted if r.outcome == "CONTINUED")
    rate_pct = (cont / total) * 100.0
    return cont, total, rate_pct


def _should_alarm(
    total: int,
    rate_pct: float,
    threshold_pct: float,
    window_size: int = WINDOW_SIZE,
) -> bool:
    """Alarm iff the window is FULL (``total >= window_size``) AND the rate
    is strictly below the threshold. A partially-filled (``total < window_size``)
    or zero-total scope never alarms — a rolling-N trend needs N observations
    to be meaningful, otherwise a single bad sequence on a thin symbol (e.g.
    GBPUSD) would produce a spurious alarm.
    """
    if total <= 0:
        return False
    if total < window_size:
        return False
    return rate_pct < threshold_pct


def merge_for_portfolio(
    per_symbol: dict[str, list[ResolvedRetest]],
) -> list[ResolvedRetest]:
    """Chronologically merge all per-symbol resolved retests. Each input list
    is already sorted — we concatenate and sort rather than a proper merge
    because N is small (thousands, not millions).
    """
    merged: list[ResolvedRetest] = []
    for lst in per_symbol.values():
        merged.extend(lst)
    merged.sort(key=lambda r: r.retest_time)
    return merged


def _path_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _csv_data_roots() -> list[Path]:
    roots = [DATA_DIR]
    parent = DATA_DIR.parent
    if parent != DATA_DIR:
        roots.append(parent)
    return roots


def _resolve_csv_pointer(path: Path) -> Path:
    """Resolve small repo-local CSV pointer stubs such as '../GBPUSD_M15.csv'."""
    try:
        if not path.is_file() or path.stat().st_size > 512:
            return path
        raw = path.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return path

    if not raw or "\n" in raw or "\r" in raw or "," in raw:
        return path
    target = Path(raw)
    if target.suffix.lower() != ".csv":
        return path
    if not target.is_absolute():
        target = path.parent / target
    try:
        target = target.resolve()
    except OSError:
        return path
    if not target.exists():
        return path
    if not any(_path_is_under(target, root) for root in _csv_data_roots()):
        logger.warning("CSV pointer for %s resolves outside data roots: %s", path, target)
        return path
    logger.info("Resolved CSV pointer %s -> %s", path, target)
    return target


def _resolve_csv_input_path(path: Path) -> Path:
    """Resolve valid CSV source aliases without hiding genuinely missing data."""
    if path.exists():
        return _resolve_csv_pointer(path)

    if path.parent.name.lower() == "historical":
        sibling = path.parent.parent / path.name
        if sibling.exists() and any(_path_is_under(sibling, root) for root in _csv_data_roots()):
            logger.info("Using sibling CSV fallback %s for missing %s", sibling, path)
            return sibling
    return path


# ---------------------------------------------------------------------------
# I/O — thin, monkeypatchable
# ---------------------------------------------------------------------------


def load_m15_for_symbol(symbol: str) -> list[dict]:
    """Load M15 candles for *symbol* from ``DATA_DIR``. Returns [] if missing.

    Tests monkeypatch this function directly (not the underlying parser) to
    inject synthetic candle sequences without touching the real filesystem.
    """
    if parse_tradingview_csv is None:
        raise RuntimeError(
            f"parse_tradingview_csv unavailable ({_IMPORT_ERROR}); cannot load CSV"
        )
    requested_path = DATA_DIR / f"{symbol}_M15.csv"
    path = _resolve_csv_input_path(requested_path)
    if not path.exists():
        logger.warning("M15 CSV missing for %s at %s — scope will be empty", symbol, path)
        return []
    try:
        return parse_tradingview_csv(path)
    except Exception as exc:
        logger.warning("Failed to parse M15 CSV for %s: %s", symbol, exc)
        return []


def build_resolved_retests_for_symbol(symbol: str) -> list[ResolvedRetest]:
    """Full per-symbol pipeline: load M15 → detect OBs → detect retests →
    classify → return chronological list. Returns [] on any failure or
    missing data.
    """
    if detect_swings is None:  # primitives failed to import
        logger.error("market_state primitives unavailable — cannot process %s", symbol)
        return []

    m15 = load_m15_for_symbol(symbol)
    if not m15:
        return []

    # The production pipeline runs OB detection on the H1 timeframe for the
    # OB/retest edge. We mirror that here, detecting OBs on the H1 series
    # derived from the same data/historical corpus.
    requested_h1_path = DATA_DIR / f"{symbol}_H1.csv"
    h1_path = _resolve_csv_input_path(requested_h1_path)
    if not h1_path.exists():
        logger.warning(
            "H1 CSV missing for %s at %s — falling back to M15 for OB detection "
            "(less reliable; edge is H1-native)",
            symbol, h1_path,
        )
        h1 = m15
    else:
        try:
            h1 = parse_tradingview_csv(h1_path)
        except Exception as exc:
            logger.warning("Failed to parse H1 CSV for %s: %s; falling back to M15", symbol, exc)
            h1 = m15

    if len(h1) < 20:
        logger.warning("Too few H1 candles for %s (%d) — skipping", symbol, len(h1))
        return []

    # Detect structure + OBs on H1 (mirrors primary_analyzer pipeline).
    try:
        swings = detect_swings(h1)
        structure = identify_structure(swings)
        events = detect_structure_breaks(h1, swings, structure)
        obs = identify_order_blocks(h1, events)
    except Exception as exc:
        logger.error("OB detection failed for %s: %s", symbol, exc)
        return []

    if not obs:
        logger.info("No OBs detected for %s", symbol)
        return []

    logger.info("%s: %d H1 OBs detected, resolving retests on M15 (%d candles)",
                symbol, len(obs), len(m15))

    return build_retest_history(obs, m15, symbol)


# ---------------------------------------------------------------------------
# CSV append with dedupe
# ---------------------------------------------------------------------------


_CSV_FIELDS = [
    "date_utc",
    "scope",
    "window_size",
    "window_start_date",
    "window_end_date",
    "continuation_count",
    "total_count",
    "rate_pct",
    "alarm_fired",
    "insufficient_sample",
]


def _read_existing_rows(path: Path) -> list[dict]:
    """Return existing CSV rows, or [] if the file is missing / empty /
    has a different header. Rows are returned as ordinary dicts; invalid
    rows are silently skipped.
    """
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                return []
            # Accept any header superset/subset — we'll write the canonical
            # header on rewrite.
            rows = [dict(r) for r in reader]
            return rows
    except Exception as exc:
        logger.warning("Failed to read existing %s: %s — treating as empty", path, exc)
        return []


def append_daily_snapshot_row(
    date_utc: str,
    scope: str,
    window_size: int,
    window_start_date: str,
    window_end_date: str,
    continuation_count: int,
    total_count: int,
    rate_pct: float,
    alarm_fired: bool,
    insufficient_sample: bool = False,
) -> None:
    """Append (or replace, by (date, scope)) a row in the daily snapshot CSV.

    Read-dedupe-rewrite semantics so running twice on the same UTC day is
    idempotent. Atomic via os.replace on the whole file (small: one row per
    configured scope plus PORTFOLIO).
    """
    path = Path(OUTPUT_CSV)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = _read_existing_rows(path)

    # Drop existing (date, scope) pair — new row wins.
    kept = [
        r for r in existing
        if not (r.get("date_utc") == date_utc and r.get("scope") == scope)
    ]

    new_row = {
        "date_utc": date_utc,
        "scope": scope,
        "window_size": str(window_size),
        "window_start_date": window_start_date,
        "window_end_date": window_end_date,
        "continuation_count": str(continuation_count),
        "total_count": str(total_count),
        "rate_pct": f"{rate_pct:.4f}",
        "alarm_fired": "true" if alarm_fired else "false",
        "insufficient_sample": "true" if insufficient_sample else "false",
    }
    kept.append(new_row)

    # Atomic rewrite via a tmp file + os.replace.
    tmp_path = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS)
            writer.writeheader()
            for r in kept:
                # Only write known fields to avoid propagating legacy columns.
                writer.writerow({k: r.get(k, "") for k in _CSV_FIELDS})
        os.replace(tmp_path, path)
    finally:
        # Best-effort cleanup if replace failed (wrapped: ignore errors).
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Alert transport (best-effort)
# ---------------------------------------------------------------------------


def send_telegram_alert(msg: str) -> None:
    """Fire a Telegram alert via ``src.notifications.notify_alert`` if available.

    Never raises — any import or network failure is swallowed (logged at WARN).
    The live Telegram bot runs in a separate codebase per CLAUDE.md, so the
    fallback (import fails or env vars missing) is effectively a no-op with
    an INFO log so operators can see alarms in the log stream regardless.
    """
    try:
        from src.notifications import notify_alert
        notify_alert(msg)
        return
    except Exception as exc:
        logger.warning("Telegram alert delivery failed (%s); logging only: %s", exc, msg)
        return


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _window_date_range(window: list[ResolvedRetest]) -> tuple[str, str]:
    """Return (earliest_date, latest_date) as ``YYYY-MM-DD`` strings, or
    (``"-"``, ``"-"``) for an empty window.
    """
    if not window:
        return "-", "-"
    try:
        first = _parse_candle_time(window[0].retest_time).date().isoformat()
        last = _parse_candle_time(window[-1].retest_time).date().isoformat()
        return first, last
    except Exception:
        return "-", "-"


def _check_staleness(
    scope: str,
    window: list[ResolvedRetest],
    now_utc: datetime,
) -> None:
    """Log a warning if the newest retest in ``window`` is older than
    ``_STALENESS_WARN_DAYS``. Informational only — does not change outcome.
    """
    if not window:
        return
    try:
        newest = _parse_candle_time(window[-1].retest_time)
    except ValueError:
        return
    age = now_utc - newest
    if age > timedelta(days=_STALENESS_WARN_DAYS):
        logger.warning(
            "[%s] Newest retest in window is %d days old (retest_time=%s) — "
            "continuation rate reflects a stale observation window.",
            scope, age.days, window[-1].retest_time,
        )


def run_monitor(
    target_date: Optional[date] = None,
    window_size: int = WINDOW_SIZE,
    alarm_threshold_pct: float = ALARM_THRESHOLD_PCT,
    dry_run: bool = False,
    symbols: Optional[list[str]] = None,
) -> int:
    """Core monitor entrypoint. Returns the exit code.

    Dry-run: builds and logs everything but writes no CSV and sends no alerts.
    """
    if _IMPORT_ERROR is not None:
        logger.error(
            "Core imports failed at module load (%s) — cannot run monitor",
            _IMPORT_ERROR,
        )
        return 2

    target_date = target_date or datetime.now(timezone.utc).date()
    date_str = target_date.isoformat()
    now_utc = datetime.now(timezone.utc)
    symbols = symbols if symbols is not None else list(SYMBOLS)

    # ---------------------------------------------------------------
    # Phase 1: build per-symbol resolved retests.
    # ---------------------------------------------------------------
    per_symbol: dict[str, list[ResolvedRetest]] = {}
    total_loaded = 0
    load_failures = 0
    for sym in symbols:
        try:
            resolved = build_resolved_retests_for_symbol(sym)
        except Exception as exc:
            logger.exception("Unhandled error building retests for %s: %s", sym, exc)
            resolved = []
            load_failures += 1
        per_symbol[sym] = resolved
        if resolved:
            total_loaded += 1
        logger.info("%s: %d resolved retests", sym, len(resolved))

    if total_loaded == 0:
        logger.error(
            "No resolved retests built for ANY symbol (%d load failures / %d attempted)",
            load_failures, len(symbols),
        )
        return 2

    # ---------------------------------------------------------------
    # Phase 2: compute rolling-50 per scope (configured symbols + PORTFOLIO).
    # ---------------------------------------------------------------
    any_alarm = False
    scopes: list[tuple[str, list[ResolvedRetest]]] = [
        (sym, per_symbol[sym]) for sym in symbols
    ]
    scopes.append(("PORTFOLIO", merge_for_portfolio(per_symbol)))

    for scope, resolved_list in scopes:
        window = rolling_window(resolved_list, window_size)
        cont, total, rate_pct = compute_rate(window)
        insufficient_sample = total < window_size
        alarm = _should_alarm(total, rate_pct, alarm_threshold_pct, window_size)

        _check_staleness(scope, window, now_utc)
        start_date, end_date = _window_date_range(window)

        level = logging.CRITICAL if alarm else logging.INFO
        status_suffix = ""
        if alarm:
            status_suffix = " ALARM"
        elif insufficient_sample:
            status_suffix = f" INSUFFICIENT_SAMPLE (n={total}<{window_size})"
        logger.log(
            level,
            "[%s] %s rolling-%d: %d/%d = %.2f%% (threshold %.1f%%)%s",
            date_str, scope, window_size, cont, total, rate_pct, alarm_threshold_pct,
            status_suffix,
        )

        if alarm:
            any_alarm = True
            if not dry_run:
                send_telegram_alert(
                    f"OB continuation ALARM [{scope}] {rate_pct:.2f}% "
                    f"({cont}/{total}) < {alarm_threshold_pct:.1f}% — "
                    f"window {start_date}..{end_date}"
                )

        if not dry_run:
            try:
                append_daily_snapshot_row(
                    date_utc=date_str,
                    scope=scope,
                    window_size=window_size,
                    window_start_date=start_date,
                    window_end_date=end_date,
                    continuation_count=cont,
                    total_count=total,
                    rate_pct=rate_pct,
                    alarm_fired=alarm,
                    insufficient_sample=insufficient_sample,
                )
            except Exception as exc:
                logger.exception("CSV append failed for scope %s: %s", scope, exc)
                # Don't fail the whole monitor — CSV write issues are reported
                # but shouldn't mask real alarms. If we can't write AND nothing
                # alarmed, we're still effectively green.

    return 1 if any_alarm else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="OB continuation rolling-50 monitor — primary edge-decay sentinel.",
    )
    p.add_argument(
        "--date", type=str, default=None,
        help="UTC date to stamp the output row (YYYY-MM-DD). Default: today UTC.",
    )
    p.add_argument(
        "--window-size", type=int, default=WINDOW_SIZE,
        help=f"Rolling window size (default: {WINDOW_SIZE}).",
    )
    p.add_argument(
        "--alarm-threshold", type=float, default=ALARM_THRESHOLD_PCT,
        help=f"Alarm threshold in percent (default: {ALARM_THRESHOLD_PCT}).",
    )
    p.add_argument(
        "--data-dir", type=str, default=None,
        help="Historical data directory (default: data/historical).",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Compute but do not write CSV and do not send Telegram alerts.",
    )
    p.add_argument(
        "--symbols", type=str, default=None,
        help="Comma-separated symbol list (default: all configured vNext symbols).",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    # Operator notification delivery is default-deny per process (F30 / Q7).
    # This monitor calls heartbeat_monitor.send_telegram_alert directly, so it
    # takes the grant at its entrypoint.
    from src.safety.notification_authorization import authorize_operator_delivery
    authorize_operator_delivery(reason="scripts/ob_continuation_monitor.py cron entrypoint")

    # CLI data-dir override acts via module constant (so tests share the
    # same path hook).
    global DATA_DIR
    if args.data_dir:
        DATA_DIR = Path(args.data_dir).resolve()
        logger.info("DATA_DIR overridden → %s", DATA_DIR)

    target_date: Optional[date] = None
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            logger.error("Invalid --date (expected YYYY-MM-DD): %r", args.date)
            return 2

    symbols: Optional[list[str]] = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    return run_monitor(
        target_date=target_date,
        window_size=args.window_size,
        alarm_threshold_pct=args.alarm_threshold,
        dry_run=args.dry_run,
        symbols=symbols,
    )


if __name__ == "__main__":
    sys.exit(main())
