"""Backfill the v2 structure detector across ``data/historical_2026/`` H4 CSVs.

A3's regime tagging (``src/research_infra/stratification.py``) reads the
production structure-detector divergence log for the H4 window enclosing
each trade's timestamp. Two compounding causes leave most trades
``UNTAGGED``:

1. The live log only records V1↔V2 *divergences* — agreement windows are
   never written. The shadow log only covers windows where the production
   pipeline disagreed with v2; many H4 windows have no row at all.
2. The detector only started running on a given instrument from when the
   shadow logger was wired in; trades older than that fall outside the
   live log's coverage entirely.

This script closes the gap by replaying the v1 + v2 detectors against
the historical H4 OHLCV in ``data/historical_2026/{instrument}_H4.csv``
and emitting one row per H4 boundary in the same JSON shape A3's loader
already understands. Output goes to
``shadow_logs/structure_detector_backfill_2026.jsonl`` (gitignored;
regenerable on demand).

Methodology
-----------
For each H4 candle in the CSV (skipping the first ``--lookback`` candles
so every classification has a full lookback window matching production):

* Take the prior ``--lookback`` H4 candles (default 80, mirroring
  ``data.lookback.H4`` in ``config/agent_config.yaml``) — i.e. the 80
  candles strictly before the current H4 boundary.
* Run ``detect_swings(min_bars=2)`` + ``identify_structure`` (v1) +
  ``identify_structure_v2`` (default ``dead_zone_divisor=8``, matching
  the production v2 promotion).
* Emit a row with::

    ts                       = current H4 boundary (open time, ISO-8601 Z)
    symbol                   = instrument
    timeframe                = "H4"
    v1_direction             = v1_label.direction
    v2_direction             = v2_label.direction
    counts                   = {hh, hl, lh, ll} from v2
    detector_version_config  = "v2"
    mode                     = "backfill"
    production_label         = v2_label.direction (post-promotion semantics)
    v2_score, v2_dead_zone   = derived from v2 counts (mirror live logger)
    source                   = "backfill_v2_regime"

The ``ts`` is the H4 *open* time so it matches A3's ``_floor_h4_utc``
lookup key. A trade at 14:30 UTC (H4 floor = 12:00) maps to the row
emitted for the 12:00 H4 boundary, classifying the regime using the 80
H4 candles ending at 12:00 — i.e. the regime active *at the open* of
the H4 window the trade fell into.

Constraints
-----------
* Read-only on production code. The script imports ``detect_swings``,
  ``identify_structure``, ``identify_structure_v2`` from
  ``src.components.market_state`` but does NOT modify them.
* The production live log is left untouched. Backfill rows go to
  ``shadow_logs/structure_detector_backfill_2026.jsonl`` (a separate
  filename A3's loader recognises as a sibling).
* Pure Python, no MT5, no Anthropic API. CSV reads + detector calls.

Usage
-----

::

    # Default — replay every H4 instrument under data/historical_2026/.
    python scripts/research/backfill_v2_regime.py

    # Filter to specific instruments (8 instruments A3 currently sees).
    python scripts/research/backfill_v2_regime.py \\
        --instruments XAUUSD,USDJPY,XAGUSD

    # Override output path (debug).
    python scripts/research/backfill_v2_regime.py \\
        --output shadow_logs/structure_detector_backfill_test.jsonl

The script is idempotent on a fixed input — a re-run produces the same
JSONL byte-for-byte (with the exception of stable file ordering on the
filesystem). Re-run after a CSV refresh.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


# Locate project root so ``src/`` import works regardless of CWD.
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent
while _PROJECT_ROOT != _PROJECT_ROOT.parent:
    if (_PROJECT_ROOT / "pyproject.toml").exists():
        break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.components.market_state import (  # noqa: E402
    detect_swings,
    identify_structure,
    identify_structure_v2,
)


logger = logging.getLogger(__name__)


# Default 8 instruments A3 sees in the trade index + research slices. US30 is
# absent from data/historical_2026/ as ``US30`` (the file is named
# ``US30_cash_*.csv``); A3's loaders use ``US30_cash`` for that broker convention.
# The default filter intentionally targets the trade-index's instrument codes
# (used by A3's stratify) — the CLI supports overrides.
_DEFAULT_INSTRUMENTS: tuple[str, ...] = (
    "EURUSD",
    "GBPUSD",
    "GBPJPY",
    "GER40",
    "NAS100",
    "UK100",
    "USDJPY",
    "XAGUSD",
    "XAUUSD",
)

# Production lookback for H4 (mirrors ``data.lookback.H4`` in
# ``config/agent_config.yaml``).
_DEFAULT_H4_LOOKBACK: int = 80

# Production swing detector min_bars for H4 (``data.swing_detection_min_bars.H4``).
_DEFAULT_MIN_BARS: int = 2

# Production v2 dead-zone divisor (``identify_structure_v2`` default = 8 +
# ADR-006 promotion). Matches the live detector when ``market_state.detector_version
# == "v2"``.
_DEFAULT_DEAD_ZONE_DIVISOR: int = 8


# ---------------------------------------------------------------------------
# CSV reading
# ---------------------------------------------------------------------------


def _parse_csv_time(s: str) -> Optional[datetime]:
    """Parse the historical CSV's ``time`` column as a UTC datetime.

    The MT5 export emits ``YYYY-MM-DD HH:MM:SS`` without a timezone; the
    project's canonical convention is UTC for all timestamps so we stamp
    the parsed datetime as such.
    """
    s = (s or "").strip()
    if not s:
        return None
    # Accept both ``YYYY-MM-DD HH:MM:SS`` and ``YYYY-MM-DDTHH:MM:SSZ``.
    try:
        if "T" in s:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
        else:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _read_h4_csv(path: Path) -> list[dict]:
    """Read an H4 CSV into the candle-dict shape ``detect_swings`` expects.

    Returned rows have keys:

    * ``time`` — ISO-8601 string with explicit ``Z`` suffix (matches the
      Pydantic ``Swing.time: str`` contract that ``detect_swings``
      eventually serializes into).
    * ``time_dt`` — UTC ``datetime``, used internally by the script for
      ordering and emit-row-ts derivation. Not part of the production
      candle schema; ignored by ``detect_swings``.
    * ``open`` / ``high`` / ``low`` / ``close`` — floats.
    * ``volume`` — int.

    Malformed rows are dropped with a debug log.
    """
    out: list[dict] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = _parse_csv_time(row.get("time", ""))
            if t is None:
                logger.debug("backfill: skipping unparseable time row in %s", path)
                continue
            try:
                o = float(row["open"])
                h = float(row["high"])
                l = float(row["low"])
                c = float(row["close"])
                v = int(float(row.get("volume", 0) or 0))
            except (KeyError, TypeError, ValueError):
                logger.debug("backfill: skipping malformed price row in %s", path)
                continue
            if any(not math.isfinite(x) for x in (o, h, l, c)):
                continue
            time_iso = t.isoformat()
            if time_iso.endswith("+00:00"):
                time_iso = time_iso[:-6] + "Z"
            out.append(
                {
                    "time": time_iso,
                    "time_dt": t,
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "volume": v,
                }
            )
    # Defensive: re-sort ascending by time so the lookback slice is correct
    # even if the CSV was emitted in reverse order.
    out.sort(key=lambda r: r["time_dt"])
    return out


# ---------------------------------------------------------------------------
# Backfill core
# ---------------------------------------------------------------------------


def _h4_label_row(
    *,
    candles: list[dict],
    lookback: int,
    boundary_idx: int,
    symbol: str,
    min_bars: int,
    dead_zone_divisor: int,
) -> Optional[dict[str, Any]]:
    """Build one backfill row for the H4 boundary at ``candles[boundary_idx]``.

    Uses the prior ``lookback`` H4 candles (``candles[boundary_idx -
    lookback : boundary_idx]``) — strictly before the current boundary, so
    the classification mirrors production semantics: "what regime is
    active at the *open* of this H4 window, given the prior 80 H4 of
    history?".

    Returns ``None`` if the lookback window is incomplete (the first
    ``lookback`` candles in the CSV).
    """
    if boundary_idx < lookback:
        return None
    window = candles[boundary_idx - lookback : boundary_idx]
    if len(window) < lookback:
        return None

    # detect_swings consumes the candle's ``time`` field as a string (the
    # Pydantic ``Swing.time: str`` contract). The candle dict carries a
    # parallel ``time_dt`` UTC datetime for ordering / emit-ts derivation,
    # which detect_swings ignores.
    swings = detect_swings(window, min_bars=min_bars)
    v1 = identify_structure(swings)
    v2 = identify_structure_v2(swings, dead_zone_divisor=dead_zone_divisor)

    boundary = candles[boundary_idx]["time_dt"]
    ts_iso = boundary.astimezone(timezone.utc).isoformat()
    if ts_iso.endswith("+00:00"):
        ts_iso = ts_iso[:-6] + "Z"

    # Mirror the live shadow logger's score/dead_zone arithmetic so the
    # backfill row carries the same metadata fields as a production row.
    hh = int(v2.hh_count or 0)
    hl = int(v2.hl_count or 0)
    lh = int(v2.lh_count or 0)
    ll = int(v2.ll_count or 0)
    score = (hh + hl) - (lh + ll)
    high_transitions = hh + lh
    low_transitions = hl + ll
    min_swings = min(high_transitions, low_transitions)
    divisor = dead_zone_divisor if dead_zone_divisor > 0 else 1
    dead_zone = max(2, min_swings // divisor)

    return {
        "ts": ts_iso,
        "logged_at": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "symbol": symbol,
        "timeframe": "H4",
        "v1_direction": v1.direction,
        "v2_direction": v2.direction,
        "counts": {"hh": hh, "hl": hl, "lh": lh, "ll": ll},
        "detector_version_config": "v2",
        "mode": "backfill",
        "production_label": v2.direction,
        "v2_score": score,
        "v2_dead_zone": dead_zone,
        "source": "backfill_v2_regime",
    }


def backfill_instrument(
    *,
    csv_path: Path,
    symbol: str,
    lookback: int = _DEFAULT_H4_LOOKBACK,
    min_bars: int = _DEFAULT_MIN_BARS,
    dead_zone_divisor: int = _DEFAULT_DEAD_ZONE_DIVISOR,
) -> Iterable[dict[str, Any]]:
    """Yield one backfill row per qualifying H4 boundary in ``csv_path``."""
    candles = _read_h4_csv(csv_path)
    if not candles:
        logger.warning("backfill: %s yielded no candles", csv_path)
        return
    if len(candles) <= lookback:
        logger.warning(
            "backfill: %s has %d candles; need > %d for a valid lookback",
            csv_path,
            len(candles),
            lookback,
        )
        return
    for idx in range(lookback, len(candles)):
        row = _h4_label_row(
            candles=candles,
            lookback=lookback,
            boundary_idx=idx,
            symbol=symbol,
            min_bars=min_bars,
            dead_zone_divisor=dead_zone_divisor,
        )
        if row is not None:
            yield row


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _resolve_csv(data_dir: Path, symbol: str) -> Optional[Path]:
    """Return the H4 CSV path for ``symbol`` (handling broker-name aliases).

    A3 uses bare instrument codes (``XAUUSD``, ``US30``, etc.). The
    historical export uses some broker-suffixed names (``US30_cash``,
    ``USOIL_cash``). We try the bare code first, then the ``_cash``
    variant; missing symbols log a warning and produce no rows.
    """
    candidates = [
        data_dir / f"{symbol}_H4.csv",
        data_dir / f"{symbol}_cash_H4.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    logger.warning("backfill: no H4 CSV found for %s under %s", symbol, data_dir)
    return None


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument(
        "--data-dir",
        type=Path,
        default=_PROJECT_ROOT / "data" / "historical_2026",
        help="Directory containing the H4 CSV files (default: data/historical_2026)",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=_PROJECT_ROOT
        / "shadow_logs"
        / "structure_detector_backfill_2026.jsonl",
        help="Output JSONL path (default: shadow_logs/structure_detector_backfill_2026.jsonl)",
    )
    p.add_argument(
        "--instruments",
        type=str,
        default=",".join(_DEFAULT_INSTRUMENTS),
        help="Comma-separated instrument codes (default: A3's 8-instrument fleet)",
    )
    p.add_argument(
        "--lookback",
        type=int,
        default=_DEFAULT_H4_LOOKBACK,
        help=f"H4 lookback window size (default: {_DEFAULT_H4_LOOKBACK})",
    )
    p.add_argument(
        "--min-bars",
        type=int,
        default=_DEFAULT_MIN_BARS,
        help=f"detect_swings min_bars (default: {_DEFAULT_MIN_BARS})",
    )
    p.add_argument(
        "--dead-zone-divisor",
        type=int,
        default=_DEFAULT_DEAD_ZONE_DIVISOR,
        help=(
            "v2 dead_zone_divisor (default: %d, matches production v2 promotion)"
            % _DEFAULT_DEAD_ZONE_DIVISOR
        ),
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    args = _parse_args(argv)
    data_dir: Path = args.data_dir.resolve()
    output: Path = args.output.resolve()
    instruments = [
        s.strip() for s in args.instruments.split(",") if s.strip()
    ]
    if not instruments:
        logger.error("no instruments provided")
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    total_rows = 0
    per_instrument: dict[str, int] = {}
    earliest_ts: Optional[str] = None
    latest_ts: Optional[str] = None

    with output.open("w", encoding="utf-8") as out_f:
        for sym in instruments:
            csv_path = _resolve_csv(data_dir, sym)
            if csv_path is None:
                per_instrument[sym] = 0
                continue
            count = 0
            for row in backfill_instrument(
                csv_path=csv_path,
                symbol=sym,
                lookback=args.lookback,
                min_bars=args.min_bars,
                dead_zone_divisor=args.dead_zone_divisor,
            ):
                out_f.write(json.dumps(row, sort_keys=True) + "\n")
                count += 1
                ts = row["ts"]
                if earliest_ts is None or ts < earliest_ts:
                    earliest_ts = ts
                if latest_ts is None or ts > latest_ts:
                    latest_ts = ts
            per_instrument[sym] = count
            total_rows += count
            logger.info("backfill: %s -> %d rows (%s)", sym, count, csv_path.name)

    logger.info(
        "backfill: wrote %d rows to %s (range %s -> %s)",
        total_rows,
        output,
        earliest_ts,
        latest_ts,
    )
    for sym, n in per_instrument.items():
        logger.info("  %s: %d", sym, n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
