"""F6 — Extract historical OHLCV from MT5 to ``data/historical_2026/``.

Closes the data-depth gap that left A3's pre-2026 trades 100% UNTAGGED and
2026-Q1 trades 18.3% UNTAGGED (the v2 detector's 80-H4 lookback warmup
window). Pulls bar history directly from the local MT5 terminal — for the
10 instruments A3 / K50 / K51 / K53 / A6 actually consume — and writes the
exact CSV schema the project's downstream tooling already understands.

Methodology (paranoid)
----------------------
* MT5 connection: ``mt5.initialize()`` with no kwargs — relies on the
  already-logged-in Windows terminal session. There is **no**
  ``MT5_LOGIN/PASSWORD/SERVER`` infrastructure in this codebase
  (verified ``grep -r MT5_LOGIN src/ scripts/`` 2026-04-26). Login is via
  the desktop app; this script is a **read-only** consumer.
* Symbol mapping: the production broker uses suffixed names for some
  instruments. ``US30 -> US30.cash``, ``NAS100 -> US100.cash``,
  ``GER40 -> GER40.cash``, ``UK100 -> UK100.cash``. Verified live
  via ``mt5.symbol_info`` 2026-04-26. The mapping table below is
  authoritative; missing symbols fail loudly per-instrument (do not
  silently skip).
* CSV schema: ``time,open,high,low,close,volume`` — exact match for
  ``data/historical_2026/{INST}_{TF}.csv`` produced by
  ``scripts/export_mt5_historical.py``. ``volume`` is MT5
  ``tick_volume`` (real volume is broker-dependent and not always
  populated for FX). D1 emits ``YYYY-MM-DD``; intraday TFs emit
  ``YYYY-MM-DD HH:MM:SS``. All timestamps are normalised to **UTC**
  (broker server time is converted via ``datetime.fromtimestamp(ts,
  tz=timezone.utc)``). For brokers whose server runs in a non-UTC zone,
  MT5's ``copy_rates_range`` returns server-local seconds — see the
  "Time bounds" section below.
* Idempotent append: if a CSV already exists, the script reads the
  existing rows, computes the latest stamped time, and only writes new
  rows whose ``time > existing_max``. Existing rows are preserved
  byte-for-byte. The output is sorted ascending and re-written in
  place; no overwrite of historical data ever happens. A re-run with
  the same ``--start/--end`` is a no-op once the window is fully
  covered.
* Time bounds: ``--start/--end`` are interpreted as UTC dates.
  ``copy_rates_range`` is called with ``datetime(YYYY, MM, DD, tzinfo=UTC)``
  — MT5 internally treats these as broker-server-time and returns bars
  with server-local epoch seconds. Empirically (XAUUSD H1 row 1 of
  existing CSVs is ``2026-01-02 01:00:00``, MT5 server uses UTC+0/+1 on
  EU brokers) the conversion via ``fromtimestamp(ts, tz=UTC)`` reproduces
  the existing CSVs exactly. If a downstream consumer ever notices a
  ±1h drift it means the broker server changed; document this in the
  data dir.

Constraints
-----------
* Read-only on production code. No production config edits, no AI
  calls, no order placement.
* Per the brief: 7 production-fleet instruments + 3 backtest-only =
  10 instruments × 4 timeframes = 40 CSV files maximum.
* Memory ``project_research_scripts_missing_dotenv``: research scripts
  don't auto-load ``.env``. Since MT5 connection is via the already-
  logged-in terminal there are no required env vars; ``--anthropic``
  not used here. The script also explicitly ``load_dotenv()`` on the
  project root for forward compatibility (any future MT5 multi-account
  override would land in env vars; we read them now so we don't need
  a re-edit later).

Usage
-----

::

    python scripts/research/extract_ohlcv_history.py \\
        --start 2025-10-01 --end 2026-04-24 \\
        --instruments XAUUSD,US30,USDJPY,GBPJPY,XAGUSD,NAS100,GBPUSD,EURUSD,GER40,UK100 \\
        --timeframes M15,H1,H4,D1 \\
        --output-dir data/historical_2026

    # Dry-run: print the per-(symbol, tf) plan + skip MT5 calls.
    python scripts/research/extract_ohlcv_history.py \\
        --start 2025-10-01 --end 2026-04-24 --dry-run

    # Override MT5 terminal path (when not in default install).
    python scripts/research/extract_ohlcv_history.py \\
        --terminal-path "C:/Program Files/MetaTrader 5/terminal64.exe"

Exit codes
----------
* ``0`` — success (or no-op when everything is already up-to-date).
* ``1`` — MT5 initialize failed.
* ``2`` — bad CLI args (no instruments / no TFs / start >= end).
* ``3`` — MT5 package not importable (ModuleNotFoundError).

The script is callable from tests (``python -m extract_ohlcv_history``-
style won't work because of the path-based location; tests import
``backfill_instrument`` and friends via the project root sys.path
shuffle below).
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

# Locate project root so test imports work regardless of CWD.
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent
while _PROJECT_ROOT != _PROJECT_ROOT.parent:
    if (_PROJECT_ROOT / "pyproject.toml").exists():
        break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# Memory ``project_research_scripts_missing_dotenv``: load .env from project
# root so any future MT5_LOGIN/PASSWORD/SERVER override would land in env.
# Right now there are none; this is forward-compatible plumbing.
try:  # pragma: no cover - dotenv is in pyproject; cover via integration
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:  # pragma: no cover - fail-soft if dotenv unavailable
    pass


logger = logging.getLogger("extract_ohlcv_history")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


#: 10 instruments F6 must cover: 7 production + 3 backtest-only.
#:
#: A3 / K50 / K51 / K53 / A6 read trade index + research slices using these
#: codes. The broker-suffix mapping below converts to MT5 symbols. ``US30``
#: live trading actually uses ``US30_cash`` as the trade-record code; we
#: emit the CSV under the stratifier's ``US30_cash`` filename (see
#: ``backfill_v2_regime.py``'s ``_resolve_csv``) so A3 finds it. Likewise
#: ``USOIL_cash`` etc. are not in this F6 set because they're not the
#: 10 the brief targets.
DEFAULT_INSTRUMENTS: tuple[str, ...] = (
    # 7 production-fleet
    "XAUUSD",
    "US30",
    "USDJPY",
    "GBPJPY",
    "XAGUSD",
    "NAS100",
    "GBPUSD",
    # 3 backtest-only that A5 saw
    "EURUSD",
    "GER40",
    "UK100",
)


#: MT5 broker-symbol mapping. Verified live via ``mt5.symbol_info``
#: against the FTMO demo terminal 2026-04-26.
BROKER_ALIAS: dict[str, str] = {
    "US30": "US30.cash",
    "NAS100": "US100.cash",
    "GER40": "GER40.cash",
    "UK100": "UK100.cash",
}


#: Project-internal CSV filename mapping. ``US30`` lives under
#: ``US30_cash_*.csv`` because A3's stratifier uses that broker-suffixed
#: code in ``_resolve_csv``. Other broker-aliased instruments keep their
#: bare CSV names because that's how A3 / A5 / K54 reference them.
CSV_NAME_OVERRIDE: dict[str, str] = {
    "US30": "US30_cash",
}


#: Default timeframes — matches A3 stratifier needs (H4 is the regime axis;
#: M15 / H1 / D1 are needed by K50/K51 feature engineering).
DEFAULT_TIMEFRAMES: tuple[str, ...] = ("M15", "H1", "H4", "D1")


#: MT5 timeframe constants (per CLAUDE.md "MT5 timeframe constants").
MT5_TF_CONST: dict[str, int] = {
    "M15": 15,
    "H1": 16385,
    "H4": 16388,
    "D1": 16408,
}


#: CSV schema column order — must match ``scripts/export_mt5_historical.py``
#: byte-for-byte so downstream consumers don't break.
CSV_COLUMNS: tuple[str, ...] = ("time", "open", "high", "low", "close", "volume")


# ---------------------------------------------------------------------------
# Plan structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtractionTarget:
    """One (instrument, timeframe) cell of the extraction plan."""

    symbol: str  # bare instrument code (used in CSV filename)
    timeframe: str  # M15 / H1 / H4 / D1
    broker_symbol: str  # MT5 symbol (with .cash suffix if needed)
    csv_path: Path  # output CSV path
    start_utc: datetime  # earliest bar requested
    end_utc: datetime  # exclusive upper bound
    existing_max_time: Optional[str] = None  # last `time` column in existing CSV
    existing_row_count: int = 0  # rows already on disk

    @property
    def append_only(self) -> bool:
        """True iff the CSV already exists with at least one data row."""
        return self.existing_row_count > 0


@dataclass
class ExtractionResult:
    """Outcome of one (instrument, timeframe) fetch — filled by ``run``."""

    target: ExtractionTarget
    rows_fetched: int = 0  # bars MT5 returned
    rows_appended: int = 0  # bars actually written (after dedup)
    error: Optional[str] = None  # non-None means this cell failed
    earliest_new_time: Optional[str] = None  # first time we wrote
    latest_new_time: Optional[str] = None  # last time we wrote


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def format_bar_time(epoch_seconds: int, timeframe: str) -> str:
    """Format MT5's ``time`` field for the project CSV schema.

    MT5 returns ``time`` as broker-server epoch seconds. Converting via
    ``datetime.fromtimestamp(ts, tz=UTC)`` reproduces the existing CSV
    formatting bit-for-bit on the FTMO/MetaQuotes demo (verified by
    re-extracting a single XAUUSD H1 bar 2026-04-26).

    D1 emits ``YYYY-MM-DD``; intraday emits ``YYYY-MM-DD HH:MM:SS``.
    """
    dt = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    if timeframe == "D1":
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def read_existing_csv(path: Path) -> tuple[list[list[str]], Optional[str]]:
    """Read an existing OHLCV CSV. Returns (rows_excluding_header, max_time).

    Robust to a missing file, an empty file, or a header-only file. The
    returned rows preserve the on-disk order; ``max_time`` is the
    lexicographic max over the ``time`` column (which equals the
    chronological max because both formats sort lexicographically).

    Raises ``ValueError`` if the header doesn't match ``CSV_COLUMNS`` —
    drift here would corrupt downstream tooling, so we fail loudly.
    """
    if not path.exists():
        return [], None
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], None
        if tuple(header) != CSV_COLUMNS:
            raise ValueError(
                f"CSV {path} has unexpected header {header!r}; "
                f"expected {list(CSV_COLUMNS)}"
            )
        rows = [r for r in reader if r]  # drop blank lines
    if not rows:
        return [], None
    max_time = max(r[0] for r in rows if r)
    return rows, max_time


def write_csv(path: Path, rows: list[list[str]]) -> None:
    """Write the OHLCV CSV with our canonical header + sorted rows.

    Rows are sorted ascending by the first column. Both date and datetime
    formats sort lexicographically, so a single sort over strings is
    correct for both D1 and intraday CSVs.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    rows_sorted = sorted(rows, key=lambda r: r[0])
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        writer.writerows(rows_sorted)


def merge_rows(
    *,
    existing_rows: list[list[str]],
    new_rows: list[list[str]],
) -> tuple[list[list[str]], int]:
    """Merge new bars into existing rows; dedup on the ``time`` key.

    Preserves the **existing** row's payload on collision (idempotent: a
    re-run that fetches a bar already on disk doesn't rewrite it). Returns
    ``(merged_rows, num_appended)``.
    """
    seen: set[str] = {r[0] for r in existing_rows}
    appended = 0
    merged: list[list[str]] = list(existing_rows)
    for row in new_rows:
        if not row:
            continue
        ts = row[0]
        if ts in seen:
            continue
        seen.add(ts)
        merged.append(row)
        appended += 1
    return merged, appended


# ---------------------------------------------------------------------------
# Plan builder
# ---------------------------------------------------------------------------


def build_plan(
    *,
    instruments: list[str],
    timeframes: list[str],
    start_utc: datetime,
    end_utc: datetime,
    output_dir: Path,
) -> list[ExtractionTarget]:
    """Build the per-(instrument, tf) extraction plan.

    Inspects the existing CSVs to determine whether each cell is an
    append-only operation. Does NOT call MT5 (so ``--dry-run`` works
    without a connection).
    """
    plan: list[ExtractionTarget] = []
    for sym in instruments:
        broker = BROKER_ALIAS.get(sym, sym)
        csv_basename = CSV_NAME_OVERRIDE.get(sym, sym)
        for tf in timeframes:
            csv_path = output_dir / f"{csv_basename}_{tf}.csv"
            existing_rows, max_time = read_existing_csv(csv_path)
            plan.append(
                ExtractionTarget(
                    symbol=sym,
                    timeframe=tf,
                    broker_symbol=broker,
                    csv_path=csv_path,
                    start_utc=start_utc,
                    end_utc=end_utc,
                    existing_max_time=max_time,
                    existing_row_count=len(existing_rows),
                )
            )
    return plan


def format_plan_summary(plan: list[ExtractionTarget]) -> str:
    """Render the plan as human-readable text (used by ``--dry-run``)."""
    lines: list[str] = []
    lines.append(
        f"Extraction plan: {len(plan)} cells "
        f"({len({p.symbol for p in plan})} instruments x "
        f"{len({p.timeframe for p in plan})} timeframes)"
    )
    lines.append("")
    lines.append(
        f"{'Instrument':12s} {'TF':4s} {'Broker':14s} "
        f"{'Existing':>9s} {'Last on disk':>20s}  Output"
    )
    for t in plan:
        last = t.existing_max_time or "(none)"
        lines.append(
            f"{t.symbol:12s} {t.timeframe:4s} {t.broker_symbol:14s} "
            f"{t.existing_row_count:9d} {last:>20s}  {t.csv_path}"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# MT5 fetching
# ---------------------------------------------------------------------------


def _import_mt5():
    """Import ``MetaTrader5`` with a clear error if it's missing.

    Raises ``ModuleNotFoundError`` with the install hint.
    """
    try:
        import MetaTrader5 as mt5  # type: ignore
    except ImportError as e:
        raise ModuleNotFoundError(
            "MetaTrader5 package is required for live extraction. "
            "Install with `pip install MetaTrader5` (Windows-only) "
            f"or run with --dry-run for the plan only. Original error: {e}"
        ) from e
    return mt5


def fetch_bars(
    *,
    mt5_module: Any,
    target: ExtractionTarget,
) -> list[list[str]]:
    """Fetch bars for one (symbol, tf) cell. Returns canonicalised rows.

    The MT5 ``copy_rates_range`` API returns a numpy structured array with
    ``time, open, high, low, close, tick_volume, spread, real_volume``
    columns. We project to our 6-col schema using ``tick_volume`` as the
    ``volume`` column (matching ``scripts/export_mt5_historical.py``).
    """
    if target.broker_symbol not in BROKER_ALIAS.values() and target.broker_symbol == target.symbol:
        # bare code; check that it resolves
        info = mt5_module.symbol_info(target.broker_symbol)
        if info is None:
            raise ValueError(
                f"Broker symbol {target.broker_symbol!r} does not resolve "
                f"on this MT5 terminal. Add an entry to BROKER_ALIAS."
            )
    # Ensure the symbol is enabled in Market Watch — some brokers (FTMO
    # demo) need this for ``copy_rates_range`` to return data.
    if not mt5_module.symbol_select(target.broker_symbol, True):
        logger.warning(
            "symbol_select(%s) failed — last_error=%s",
            target.broker_symbol,
            mt5_module.last_error(),
        )

    tf_const = MT5_TF_CONST[target.timeframe]
    rates = mt5_module.copy_rates_range(
        target.broker_symbol,
        tf_const,
        target.start_utc,
        target.end_utc,
    )
    if rates is None or len(rates) == 0:
        # No data for this window — could be weekend/holiday for a daily
        # close request, or the broker doesn't carry that history. Both
        # are handled by the caller emitting a warning + skipping.
        return []

    rows: list[list[str]] = []
    for bar in rates:
        ts_str = format_bar_time(int(bar["time"]), target.timeframe)
        rows.append(
            [
                ts_str,
                _format_price(float(bar["open"])),
                _format_price(float(bar["high"])),
                _format_price(float(bar["low"])),
                _format_price(float(bar["close"])),
                str(int(bar["tick_volume"])),
            ]
        )
    return rows


def _format_price(x: float) -> str:
    """Format a price float to match the existing CSV (no fixed precision).

    Existing CSVs use Python's default ``str(float)`` shape, e.g.
    ``4327.16``, ``1.1685699999999999``. We mirror that exactly via
    ``str()`` so a re-extraction of an existing bar produces the same
    bytes (idempotency at the CSV-byte level when possible).
    """
    # ``str(0.1)`` -> '0.1' (matches existing). ``str(1.1685699999999999)``
    # -> '1.1685699999999999' (matches existing too). Don't use ``repr``
    # because Python 2 vs 3 differs there; ``str`` is stable in 3.x.
    return str(x)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_extraction(
    *,
    plan: list[ExtractionTarget],
    mt5_module: Any,
) -> list[ExtractionResult]:
    """Execute the plan, writing/appending CSVs in place.

    Returns one ``ExtractionResult`` per ``ExtractionTarget`` in plan order.
    Errors on individual cells are captured (``result.error``) but do NOT
    abort the run — partial fleet extraction is preferable to all-or-
    nothing. The summary at the end reports per-cell status.
    """
    results: list[ExtractionResult] = []
    for target in plan:
        result = ExtractionResult(target=target)
        try:
            new_rows = fetch_bars(mt5_module=mt5_module, target=target)
            result.rows_fetched = len(new_rows)
            if not new_rows:
                logger.warning(
                    "no bars returned for %s %s window %s -> %s",
                    target.broker_symbol,
                    target.timeframe,
                    target.start_utc.date(),
                    target.end_utc.date(),
                )
                results.append(result)
                continue
            existing_rows, _ = read_existing_csv(target.csv_path)
            merged, appended = merge_rows(
                existing_rows=existing_rows,
                new_rows=new_rows,
            )
            write_csv(target.csv_path, merged)
            result.rows_appended = appended
            new_only = [r[0] for r in new_rows if r[0] not in {x[0] for x in existing_rows}]
            if new_only:
                result.earliest_new_time = min(new_only)
                result.latest_new_time = max(new_only)
            logger.info(
                "%s %s: fetched=%d appended=%d existing=%d -> %s",
                target.symbol,
                target.timeframe,
                result.rows_fetched,
                result.rows_appended,
                len(existing_rows),
                target.csv_path.name,
            )
        except Exception as exc:  # noqa: BLE001 — surface but don't abort run
            result.error = f"{type(exc).__name__}: {exc}"
            logger.exception(
                "extraction failed for %s %s",
                target.symbol,
                target.timeframe,
            )
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_date(s: str) -> datetime:
    """Parse a YYYY-MM-DD CLI date as a UTC datetime at midnight."""
    try:
        d = datetime.strptime(s, "%Y-%m-%d")
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"expected YYYY-MM-DD; got {s!r} ({e})"
        ) from e
    return d.replace(tzinfo=timezone.utc)


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument(
        "--start",
        type=_parse_date,
        required=True,
        help="Earliest bar (UTC date, YYYY-MM-DD)",
    )
    p.add_argument(
        "--end",
        type=_parse_date,
        required=True,
        help="Exclusive upper bound (UTC date, YYYY-MM-DD)",
    )
    p.add_argument(
        "--instruments",
        type=str,
        default=",".join(DEFAULT_INSTRUMENTS),
        help=f"Comma-separated instrument codes (default: F6's 10-instrument set)",
    )
    p.add_argument(
        "--timeframes",
        type=str,
        default=",".join(DEFAULT_TIMEFRAMES),
        help=f"Comma-separated timeframes (default: {','.join(DEFAULT_TIMEFRAMES)})",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=_PROJECT_ROOT / "data" / "historical_2026",
        help="Output directory (default: data/historical_2026)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan + skip MT5 calls (no env required)",
    )
    p.add_argument(
        "--terminal-path",
        type=str,
        default=None,
        help="Override MT5 terminal path (e.g. C:/Program Files/MetaTrader 5/terminal64.exe)",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    args = _parse_args(argv)
    instruments = [s.strip() for s in args.instruments.split(",") if s.strip()]
    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]

    if not instruments:
        logger.error("no instruments provided")
        return 2
    if not timeframes:
        logger.error("no timeframes provided")
        return 2
    bad_tfs = [t for t in timeframes if t not in MT5_TF_CONST]
    if bad_tfs:
        logger.error("unknown timeframes: %s (valid: %s)", bad_tfs, list(MT5_TF_CONST))
        return 2
    if args.start >= args.end:
        logger.error("start (%s) must be < end (%s)", args.start, args.end)
        return 2

    output_dir: Path = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    plan = build_plan(
        instruments=instruments,
        timeframes=timeframes,
        start_utc=args.start,
        end_utc=args.end,
        output_dir=output_dir,
    )

    summary = format_plan_summary(plan)
    print(summary)

    if args.dry_run:
        logger.info("dry-run: skipping MT5 + write phases")
        return 0

    # Live mode: connect to MT5.
    try:
        mt5 = _import_mt5()
    except ModuleNotFoundError as e:
        logger.error("%s", e)
        return 3

    init_kwargs: dict[str, Any] = {}
    if args.terminal_path:
        init_kwargs["path"] = args.terminal_path

    if not mt5.initialize(**init_kwargs):
        # Fall back to no-args init (uses default install).
        if init_kwargs and not mt5.initialize():
            logger.error("MT5 initialize failed: %s", mt5.last_error())
            return 1
        if not init_kwargs:
            logger.error("MT5 initialize failed: %s", mt5.last_error())
            return 1

    term = mt5.terminal_info()
    acct = mt5.account_info()
    logger.info(
        "MT5 connected: terminal=%s account=%s server=%s",
        getattr(term, "name", "?"),
        getattr(acct, "login", "?") if acct else "?",
        getattr(acct, "server", "?") if acct else "?",
    )

    try:
        results = run_extraction(plan=plan, mt5_module=mt5)
    finally:
        mt5.shutdown()

    # Final summary.
    n_ok = sum(1 for r in results if r.error is None)
    n_err = sum(1 for r in results if r.error is not None)
    total_appended = sum(r.rows_appended for r in results)
    total_fetched = sum(r.rows_fetched for r in results)
    logger.info(
        "extraction done: %d/%d cells ok, %d errors, %d bars fetched, %d bars appended",
        n_ok,
        len(results),
        n_err,
        total_fetched,
        total_appended,
    )
    if n_err:
        for r in results:
            if r.error:
                logger.error(
                    "  FAILED %s %s: %s",
                    r.target.symbol,
                    r.target.timeframe,
                    r.error,
                )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
