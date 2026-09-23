#!/usr/bin/env python3
"""Regime-Outcome Correlation Analyzer (post-shadow-period evaluation).

Purpose
-------
Read the shadow log produced by
``src/components/regime_shadow_logger.py`` and join it against trade
outcomes from ``knowledge_base/trade_records/`` to compute per-regime
WR / Exp R / count for each instrument. Output is a CSV + a markdown
summary so the CEO can make the V1 -> live promotion call.

Run AFTER 14+ days of shadow data has accumulated.

Usage
-----
    python scripts/regime_outcome_correlation.py \\
        --shadow-log shadow_logs/regime_classifications.jsonl \\
        --trade-records-dir knowledge_base/trade_records \\
        --output-csv research/regime_classifier/correlation_report.csv \\
        --output-md research/regime_classifier/correlation_report.md

    # As-of date for filtering (default = "today"):
    python scripts/regime_outcome_correlation.py --as-of 2026-05-09 ...

Methodology
-----------
* For each trade record with an exit block, extract:
    - canonical symbol (alias normalised — US30_cash -> US30)
    - candle_time (UTC datetime)
    - realized R (clipped to [-5, +5] per fat-tail discipline; see
      memory project_distributional_findings.md)
    - direction (LONG / SHORT)
* For each shadow log row, extract:
    - symbol, ts (candle close UTC), regime label, classifier_version
* Join: for each trade, find the shadow log row whose ``ts`` is the
  closest match within ``--match-window-minutes`` of the trade's
  candle_time on the same symbol. If no match found the trade is
  reported in an "unmatched" bucket (not silently dropped).
* Aggregate per (symbol, regime): WR (Wilson 95% CI), Exp R
  (bootstrap 95% CI), count.

Statistical methods
-------------------
Match those used in ``scripts/monthly_decay_monitor.py`` for
consistency:

* WR:        Wilson 95% CI for binomial proportion.
* Exp R:     percentile bootstrap 95% CI on the sample mean.
* R clip:    [-5R, +5R] before aggregation.

Stdlib-only (plus optional ``csv`` and ``random``) so the analyzer
runs anywhere.

Status
------
This is a post-shadow-period analysis tool. It does NOT promote V1 to
live; CEO does that explicitly after reviewing the report. No part of
this script imports anything from ``permissions.py`` or
``primary_analyzer.py``.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

logger = logging.getLogger("regime_outcome_correlation")


# ---------------------------------------------------------------------------
# Constants — kept in sync with monthly_decay_monitor.py
# ---------------------------------------------------------------------------

R_CLIP_LOW: float = -5.0
R_CLIP_HIGH: float = 5.0

INSTRUMENT_ALIAS: dict[str, str] = {
    "US30_cash": "US30",
    "US30": "US30",
}

DEFAULT_MATCH_WINDOW_MINUTES: int = 30
"""Maximum minutes between trade candle_time and shadow row ts to call
it a match. Trades fire on the M15 close that produced the CANDIDATE,
so a within-window match is a same-candle match. We allow 30 minutes
to absorb any clock skew or instrumentation lag."""

BOOTSTRAP_ITERS: int = 1000


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TradeOutcome:
    instrument: str
    candle_time: datetime
    direction: str          # "LONG" | "SHORT"
    outcome: str            # "WIN" | "LOSS" | "BE"
    r_multiple: float       # clipped to [R_CLIP_LOW, R_CLIP_HIGH]
    raw_candle_time: Optional[str] = None


@dataclass(frozen=True)
class RegimeRow:
    symbol: str
    ts: datetime
    regime: str
    classifier_version: str


@dataclass
class RegimeBucket:
    instrument: str
    regime: str
    n: int = 0
    wins: int = 0
    losses: int = 0
    be: int = 0
    rs: list[float] = field(default_factory=list)


@dataclass
class BucketStats:
    instrument: str
    regime: str
    n: int
    wins: int
    losses: int
    be: int
    wr: float
    wr_ci_lo: float
    wr_ci_hi: float
    exp_r: float
    exp_ci_lo: float
    exp_ci_hi: float
    total_r: float


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

def wilson_ci(wins: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    p = wins / total
    denom = 1.0 + (z * z) / total
    center = (p + (z * z) / (2 * total)) / denom
    spread = z * math.sqrt((p * (1 - p) + (z * z) / (4 * total)) / total) / denom
    return (max(0.0, center - spread), min(1.0, center + spread))


def bootstrap_mean_ci(
    values: list[float],
    iters: int = BOOTSTRAP_ITERS,
    alpha: float = 0.05,
    seed: Optional[int] = None,
) -> tuple[float, float]:
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    if n == 1:
        return (float(values[0]), float(values[0]))
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(iters):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = int((alpha / 2.0) * iters)
    hi_idx = int((1.0 - alpha / 2.0) * iters) - 1
    hi_idx = max(hi_idx, 0)
    lo_idx = min(lo_idx, iters - 1)
    return (means[lo_idx], means[hi_idx])


# ---------------------------------------------------------------------------
# Coercion helpers
# ---------------------------------------------------------------------------

def _canonical_instrument(raw: Any) -> Optional[str]:
    if not isinstance(raw, str) or not raw.strip():
        return None
    s = raw.strip()
    return INSTRUMENT_ALIAS.get(s, s)


def _parse_datetime(raw: Any) -> Optional[datetime]:
    if not isinstance(raw, str) or not raw.strip():
        return None
    s = raw.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _clip_r(r: Any) -> Optional[float]:
    if r is None:
        return None
    try:
        rf = float(r)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(rf):
        return None
    return max(R_CLIP_LOW, min(R_CLIP_HIGH, rf))


def _classify_r(r: float) -> str:
    if r > 0:
        return "WIN"
    if r < 0:
        return "LOSS"
    return "BE"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_shadow_log(path: Path) -> list[RegimeRow]:
    """Load all rows from the regime shadow log (JSONL).

    Drops rows with missing/malformed symbol or ts. Preserves order.
    """
    rows: list[RegimeRow] = []
    if not path.is_file():
        logger.warning("shadow log not found: %s", path)
        return rows
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(d, dict):
                continue
            symbol = _canonical_instrument(d.get("symbol"))
            ts = _parse_datetime(d.get("ts"))
            regime = d.get("regime")
            if not symbol or ts is None or not isinstance(regime, str):
                continue
            rows.append(RegimeRow(
                symbol=symbol,
                ts=ts,
                regime=regime,
                classifier_version=str(d.get("classifier_version", "")),
            ))
    return rows


def load_trade_outcomes(base: Path) -> list[TradeOutcome]:
    """Load every closed-with-exit trade record under base."""
    out: list[TradeOutcome] = []
    if not base.is_dir():
        logger.warning("trade_records dir not found: %s", base)
        return out
    for fp in base.rglob("*.json"):
        if "_pending" in fp.name or fp.name.startswith("_"):
            continue
        try:
            with fp.open("r", encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(d, dict):
            continue
        meta = d.get("metadata") or {}
        symbol = _canonical_instrument(meta.get("symbol"))
        ct = _parse_datetime(meta.get("candle_time"))
        if not symbol or ct is None:
            continue
        exit_block = d.get("exit")
        if not isinstance(exit_block, dict) or not exit_block:
            continue
        # A3 v1.1: realized_R; v1.0: actual_r; v1.1 also surfaces in instrumentation.
        r_raw = exit_block.get("realized_R")
        if r_raw is None:
            r_raw = exit_block.get("actual_r")
        if r_raw is None:
            instrumentation = d.get("instrumentation")
            if isinstance(instrumentation, dict):
                r_raw = instrumentation.get("realized_R")
        r = _clip_r(r_raw)
        if r is None:
            continue
        # Direction comes from trade_parameters.
        params = d.get("trade_parameters") or {}
        direction_raw = params.get("direction") or ""
        direction = "LONG" if str(direction_raw).upper() == "LONG" else "SHORT"
        out.append(TradeOutcome(
            instrument=symbol,
            candle_time=ct,
            direction=direction,
            outcome=_classify_r(r),
            r_multiple=r,
            raw_candle_time=meta.get("candle_time"),
        ))
    return out


# ---------------------------------------------------------------------------
# Joining + aggregation
# ---------------------------------------------------------------------------

def find_nearest_regime(
    trade: TradeOutcome,
    shadow_rows: list[RegimeRow],
    window_minutes: int,
) -> Optional[RegimeRow]:
    """Return the shadow row closest to the trade's candle_time on the
    same symbol within window_minutes; None if no match.

    Linear scan — the shadow log is bounded by candle frequency (~96
    M15 candles/instrument/day) so this is fine for any realistic
    horizon.
    """
    window = timedelta(minutes=window_minutes)
    best: Optional[RegimeRow] = None
    best_dt: Optional[timedelta] = None
    for row in shadow_rows:
        if row.symbol != trade.instrument:
            continue
        delta = abs(row.ts - trade.candle_time)
        if delta > window:
            continue
        if best_dt is None or delta < best_dt:
            best = row
            best_dt = delta
    return best


def aggregate_buckets(
    trades: list[TradeOutcome],
    shadow_rows: list[RegimeRow],
    window_minutes: int,
) -> tuple[dict[tuple[str, str], RegimeBucket], list[TradeOutcome]]:
    """Return (buckets, unmatched_trades).

    buckets is keyed by (instrument, regime). Trades with no shadow
    match within window_minutes go to unmatched_trades (NOT silently
    dropped).
    """
    buckets: dict[tuple[str, str], RegimeBucket] = {}
    unmatched: list[TradeOutcome] = []
    for trade in trades:
        match = find_nearest_regime(trade, shadow_rows, window_minutes)
        if match is None:
            unmatched.append(trade)
            continue
        key = (trade.instrument, match.regime)
        bucket = buckets.get(key)
        if bucket is None:
            bucket = RegimeBucket(instrument=trade.instrument, regime=match.regime)
            buckets[key] = bucket
        bucket.n += 1
        bucket.rs.append(trade.r_multiple)
        if trade.outcome == "WIN":
            bucket.wins += 1
        elif trade.outcome == "LOSS":
            bucket.losses += 1
        else:
            bucket.be += 1
    return buckets, unmatched


def compute_stats(buckets: dict[tuple[str, str], RegimeBucket]) -> list[BucketStats]:
    """Materialise BucketStats with WR / Exp R + 95% CIs."""
    out: list[BucketStats] = []
    for (sym, regime), b in sorted(buckets.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        wr = b.wins / b.n if b.n else 0.0
        wr_lo, wr_hi = wilson_ci(b.wins, b.n)
        exp_r = sum(b.rs) / b.n if b.n else 0.0
        exp_lo, exp_hi = bootstrap_mean_ci(b.rs, seed=42)
        out.append(BucketStats(
            instrument=b.instrument,
            regime=b.regime,
            n=b.n,
            wins=b.wins,
            losses=b.losses,
            be=b.be,
            wr=wr,
            wr_ci_lo=wr_lo,
            wr_ci_hi=wr_hi,
            exp_r=exp_r,
            exp_ci_lo=exp_lo,
            exp_ci_hi=exp_hi,
            total_r=sum(b.rs),
        ))
    return out


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

CSV_HEADER = [
    "instrument", "regime", "n", "wins", "losses", "be",
    "wr", "wr_ci_lo", "wr_ci_hi",
    "exp_r", "exp_ci_lo", "exp_ci_hi",
    "total_r",
]


def write_csv(stats: list[BucketStats], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(CSV_HEADER)
        for s in stats:
            w.writerow([
                s.instrument, s.regime, s.n, s.wins, s.losses, s.be,
                f"{s.wr:.4f}", f"{s.wr_ci_lo:.4f}", f"{s.wr_ci_hi:.4f}",
                f"{s.exp_r:.4f}", f"{s.exp_ci_lo:.4f}", f"{s.exp_ci_hi:.4f}",
                f"{s.total_r:.4f}",
            ])


def write_markdown(
    stats: list[BucketStats],
    unmatched_count: int,
    shadow_count: int,
    trade_count: int,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Regime-Outcome Correlation Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"* Shadow rows loaded: {shadow_count}")
    lines.append(f"* Trade outcomes loaded: {trade_count}")
    lines.append(f"* Unmatched trades (no shadow row in window): {unmatched_count}")
    lines.append("")
    lines.append("## Per-instrument per-regime statistics")
    lines.append("")
    lines.append(
        "| Instrument | Regime | n | WR | WR 95% CI | Exp R | Exp R 95% CI | Total R |"
    )
    lines.append(
        "| --- | --- | ---: | ---: | --- | ---: | --- | ---: |"
    )
    if not stats:
        lines.append("| (no joined data) | | | | | | | |")
    else:
        for s in stats:
            wr_ci = f"[{s.wr_ci_lo:.3f}, {s.wr_ci_hi:.3f}]"
            exp_ci = f"[{s.exp_ci_lo:+.3f}, {s.exp_ci_hi:+.3f}]"
            lines.append(
                f"| {s.instrument} | {s.regime} | {s.n} | "
                f"{s.wr:.3f} | {wr_ci} | "
                f"{s.exp_r:+.3f} | {exp_ci} | "
                f"{s.total_r:+.2f} |"
            )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "* WR CIs are Wilson 95%. Exp R CIs are percentile bootstrap "
        "95% (seed=42, 1000 iters)."
    )
    lines.append(
        "* R values are clipped to [-5, +5] before aggregation per fat-tail "
        "discipline."
    )
    lines.append(
        "* `unclear` is a valid regime — it will appear in the table when the "
        "classifier could not resolve. Track its rate over time."
    )
    lines.append(
        "* This is observation-only. Use this report to *propose* a "
        "regime-aware filter or prompt hint. CEO approval required to ship."
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Compute per-regime WR / Exp R / count from shadow log + trade records.",
    )
    p.add_argument(
        "--shadow-log",
        type=Path,
        default=Path("shadow_logs/regime_classifications.jsonl"),
        help="JSONL produced by regime_shadow_logger (default: %(default)s)",
    )
    p.add_argument(
        "--trade-records-dir",
        type=Path,
        default=Path("knowledge_base/trade_records"),
        help="Directory of A3-format trade record JSONs (default: %(default)s)",
    )
    p.add_argument(
        "--output-csv",
        type=Path,
        default=Path("research/regime_classifier/correlation_report.csv"),
        help="CSV output path (default: %(default)s)",
    )
    p.add_argument(
        "--output-md",
        type=Path,
        default=Path("research/regime_classifier/correlation_report.md"),
        help="Markdown summary output path (default: %(default)s)",
    )
    p.add_argument(
        "--match-window-minutes",
        type=int,
        default=DEFAULT_MATCH_WINDOW_MINUTES,
        help=(
            "Max minutes between trade candle_time and nearest shadow row "
            "to count as a match (default: %(default)s)"
        ),
    )
    p.add_argument(
        "--as-of",
        type=str,
        default=None,
        help="Ignore trades with candle_time after this date (YYYY-MM-DD).",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)

    shadow_rows = load_shadow_log(args.shadow_log)
    trades = load_trade_outcomes(args.trade_records_dir)

    if args.as_of:
        try:
            cutoff = datetime.fromisoformat(args.as_of).replace(tzinfo=timezone.utc)
            trades = [t for t in trades if t.candle_time <= cutoff]
        except ValueError:
            logger.error("could not parse --as-of=%s", args.as_of)
            return 2

    logger.info("loaded %d shadow rows + %d trades", len(shadow_rows), len(trades))

    buckets, unmatched = aggregate_buckets(
        trades, shadow_rows, window_minutes=args.match_window_minutes
    )
    stats = compute_stats(buckets)

    write_csv(stats, args.output_csv)
    write_markdown(
        stats,
        unmatched_count=len(unmatched),
        shadow_count=len(shadow_rows),
        trade_count=len(trades),
        path=args.output_md,
    )

    logger.info("wrote %s + %s", args.output_csv, args.output_md)
    if unmatched:
        logger.info("unmatched trades: %d (no shadow row within window)", len(unmatched))
    return 0


if __name__ == "__main__":
    sys.exit(main())
