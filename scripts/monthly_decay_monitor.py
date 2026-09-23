#!/usr/bin/env python3
"""Monthly-Decay Shadow Monitor — fast edge-decay alarm.

Purpose
-------
CLAUDE.md records a quarterly-decay trend (73% -> 59% over Q1-Q4 2025) and
session-39 comprehensive extraction surfaced a WITHIN-2026 XAUUSD WR drop
(Jan 45.5% n=11 / Feb 75.0% n=20 / Mar 33.3% n=15 / Apr 10.0% n=10; H1 vs
H2 chi-square p=0.006). CEO's #1 concern is edge decay. This shadow monitor
catches it at month/week granularity instead of quarterly.

Scope
-----
Infrastructure + observability only. No trading-logic change. Log-only —
the monitor writes a markdown report; raising the alarm is a human step
done by the CEO after reviewing the report.

Data sources (unioned + deduped on (instrument, candle_time_iso))
-----------------------------------------------------------------
Priority 1 (live, ground truth once populated):
  knowledge_base/trade_records/{SYMBOL}/*.json  — A3 v1.1 schema (capture_version
  1.0 + 1.1). Trade outcome comes from the ``exit`` block.

Priority 2 (simulator history, fills the pre-live period):
  research/a1_adr005_backtest/slices/**/all_results.json
  research/f3_backtest_2026-04-24/**/all_results.json
  research/t7_live_simulation/all_results_*.json
  research/q65_speed_to_mfe/*.json  (opportunistic — skipped if absent)

Live records override simulator rows on the same (symbol, candle_time) key.

Alert thresholds
----------------
WR decay:       current-month WR drops > 15pp below 3-month rolling baseline
                AND n_current >= 10.
Expectancy:     current-month Exp R drops > 0.25R below 3-month baseline
                AND n_current >= 10.
Consecutive:    3 consecutive weeks with WR < instrument breakeven
                AND n_week >= 5 each.
Insufficient:   n_current < 10 -> "insufficient sample" INFO marker
                (not an alarm — just shows why we are not firing one).

Statistical methods
-------------------
WR:         Wilson 95% CI for the binomial proportion.
Expectancy: bootstrap 95% CI with >=1000 resamples (percentile method).
R clipping: [-5R, +5R] per trade before aggregation to prevent outlier
            domination of expectancy (fat-tail discipline, per memory
            project_distributional_findings.md).

Usage
-----
    python scripts/monthly_decay_monitor.py \
        --output research/monthly_decay_monitor/2026-04_report.md

    # Custom data roots (tests/dev):
    python scripts/monthly_decay_monitor.py \
        --trade-records-dir tmp/knowledge_base/trade_records \
        --simulator-root tmp/research \
        --output tmp/report.md

    # Baseline month explicitly (default = "now"):
    python scripts/monthly_decay_monitor.py --as-of 2026-04-30 --output ...

The script is stdlib-only (plus optional numpy if present for bootstrap)
so it can run on any environment without extra deps.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import random
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

logger = logging.getLogger("monthly_decay_monitor")


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

# Per-instrument breakeven WR from CLAUDE.md §Quick Reference Card.
BREAKEVEN_WR: dict[str, float] = {
    "AUDJPY": 0.40,
    "AUDUSD": 0.40,
    "BTCUSD": 0.40,
    "CHFJPY": 0.40,
    "ETHUSD": 0.40,
    "EURGBP": 0.40,
    "EURJPY": 0.40,
    "EURUSD": 0.40,
    "GBPJPY": 0.417,
    "GBPUSD": 0.375,      # estimated until batch stats land
    "GER40": 0.40,
    "JP225": 0.40,
    "NAS100": 0.40,
    "NZDUSD": 0.40,
    "SPX500": 0.40,
    "UK100": 0.40,
    "UKOIL_cash": 0.40,
    "US30_cash": 0.345,   # broker symbol alias used in live records
    "USDCAD": 0.40,
    "USDCHF": 0.40,
    "USDJPY": 0.400,
    "USOIL_cash": 0.40,
    "XAGUSD": 0.40,
    "XAUUSD": 0.357,
    "US30": 0.345,
}

# Default breakeven when an unlisted instrument appears (conservative).
DEFAULT_BREAKEVEN_WR = 0.40

# Canonical instrument list for report ordering + empty-instrument placeholders.
DEFAULT_INSTRUMENTS: tuple[str, ...] = (
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
)

# R-value clip bounds for fat-tail discipline.
R_CLIP_LOW: float = -5.0
R_CLIP_HIGH: float = 5.0

# Alert thresholds (spec).
WR_DROP_THRESHOLD_PP: float = 0.15       # 15 percentage-point drop
EXP_DROP_THRESHOLD: float = 0.25         # 0.25 R drop
INSUFFICIENT_N: int = 10                 # gate for WR/Exp alarms
CONSECUTIVE_WEEK_N: int = 3              # 3 consecutive weeks
WEEK_MIN_N: int = 5                      # min trades per week for weakness check
BASELINE_WINDOW_MONTHS: int = 3          # rolling baseline = 3 months

# Bootstrap resamples (>=1000 per spec).
BOOTSTRAP_ITERS: int = 1000

# Number of weekly rows to include in report (last N weeks).
WEEKLY_ROWS: int = 12

# Instrument aliases — records can use either "US30" or "US30_cash".
INSTRUMENT_ALIAS: dict[str, str] = {
    "GER30": "GER40",
    "NDX100": "NAS100",
    "UKOUSD": "UKOIL_cash",
    "US30": "US30_cash",
    "US30_cash": "US30_cash",
    "USOUSD": "USOIL_cash",
}


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class TradeOutcome:
    """Canonical trade outcome usable by the monitor."""
    instrument: str                  # canonical symbol ("XAUUSD", "US30", ...)
    candle_time: datetime             # UTC
    outcome: str                     # "WIN" | "LOSS" | "BE"
    r_multiple: float                # clipped to [R_CLIP_LOW, R_CLIP_HIGH]
    source: str                      # "live" | "a1" | "f3" | "t7" | ...
    exit_reason: Optional[str] = None
    raw_candle_time: Optional[str] = None  # original string, for dedup key


@dataclass
class InstrumentAggregate:
    instrument: str
    monthly: list["BucketStats"] = field(default_factory=list)
    weekly: list["BucketStats"] = field(default_factory=list)


@dataclass
class BucketStats:
    label: str                       # "2026-04" or "2026-W17"
    n: int
    wins: int
    losses: int
    be: int
    wr: float                        # wins / n, 0.0 if n==0
    wr_ci_lo: float
    wr_ci_hi: float
    exp_r: float                     # mean realized R over the bucket
    exp_ci_lo: float
    exp_ci_hi: float
    total_r: float                   # sum realized R (informational)

    @classmethod
    def empty(cls, label: str) -> "BucketStats":
        return cls(
            label=label, n=0, wins=0, losses=0, be=0,
            wr=0.0, wr_ci_lo=0.0, wr_ci_hi=0.0,
            exp_r=0.0, exp_ci_lo=0.0, exp_ci_hi=0.0, total_r=0.0,
        )


# ----------------------------------------------------------------------------
# Statistical helpers
# ----------------------------------------------------------------------------

def wilson_ci(wins: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Returns (lo, hi) both in [0, 1]. (0.0, 0.0) when total == 0.
    Matches scripts/live_monitor.py:99 implementation.
    """
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
    """Percentile bootstrap 95% CI for the sample mean.

    Stdlib-only so the monitor has no numpy requirement. Seed is configurable
    for deterministic tests.
    """
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    if n == 1:
        return (float(values[0]), float(values[0]))
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(iters):
        # Resample with replacement by drawing n indices.
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = int((alpha / 2.0) * iters)
    hi_idx = int((1.0 - alpha / 2.0) * iters) - 1
    hi_idx = max(hi_idx, 0)
    lo_idx = min(lo_idx, iters - 1)
    return (means[lo_idx], means[hi_idx])


def chi_square_2x2(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    """2x2 chi-square with Yates correction. Returns (chi2, p-value).

    Used by test-suite to reproduce A1 H1-vs-H2 XAUUSD decay p ~ 0.006.
    Stdlib-only — computes the p-value via a series approximation for the
    chi-square-1 survival function.
    """
    # Contingency:
    #   group1: a wins, b losses
    #   group2: c wins, d losses
    n = a + b + c + d
    if n <= 0:
        return (0.0, 1.0)
    row1, row2 = a + b, c + d
    col1, col2 = a + c, b + d
    if row1 == 0 or row2 == 0 or col1 == 0 or col2 == 0:
        return (0.0, 1.0)
    # Expected counts.
    e_a = row1 * col1 / n
    e_b = row1 * col2 / n
    e_c = row2 * col1 / n
    e_d = row2 * col2 / n
    chi2 = 0.0
    for obs, exp in ((a, e_a), (b, e_b), (c, e_c), (d, e_d)):
        # Yates continuity correction: subtract 0.5 from |obs-exp|.
        diff = abs(obs - exp) - 0.5
        if diff < 0:
            diff = 0.0
        chi2 += (diff * diff) / exp if exp > 0 else 0.0
    # p-value = P(X > chi2) where X ~ chi-square with df=1 = erfc(sqrt(chi2/2)).
    # Use math.erfc directly since df=1.
    p = math.erfc(math.sqrt(chi2 / 2.0))
    return (chi2, p)


# ----------------------------------------------------------------------------
# Normalization helpers
# ----------------------------------------------------------------------------

def _canonical_instrument(raw: Any) -> Optional[str]:
    """Map raw symbol to canonical. None if missing/malformed."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    s = raw.strip()
    return INSTRUMENT_ALIAS.get(s, s)


def _parse_candle_time(raw: Any) -> Optional[datetime]:
    """Parse ISO timestamp (with or without ``Z`` suffix) to UTC datetime."""
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
    """Coerce + clip an R value. Return None if unparseable."""
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
    """Return 'WIN'/'LOSS'/'BE' from a numeric R value."""
    if r > 0:
        return "WIN"
    if r < 0:
        return "LOSS"
    return "BE"


# ----------------------------------------------------------------------------
# Data loaders
# ----------------------------------------------------------------------------

def _load_live_trade_record(path: Path) -> Optional[TradeOutcome]:
    """Load a single trade record JSON (A3 v1.1 or v1.0 schema).

    Returns None if:
      - file is non-JSON / unreadable
      - no exit block present (trade unfilled / still open)
      - exit block lacks a numeric R
      - candle_time is missing / malformed
      - symbol is missing / malformed
    """
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.debug("skip live record %s: %s", path, exc)
        return None

    if not isinstance(data, dict):
        return None

    meta = data.get("metadata") or {}
    instrument = _canonical_instrument(meta.get("symbol"))
    if not instrument:
        return None

    ct = _parse_candle_time(meta.get("candle_time"))
    if ct is None:
        return None

    exit_block = data.get("exit")
    if not isinstance(exit_block, dict) or not exit_block:
        # No fill yet — pending / rejected / limit-placed.
        return None

    # Try A3 v1.1 aliases first, fall back to v1.0 native names.
    r_raw = (
        exit_block.get("realized_R")
        if exit_block.get("realized_R") is not None
        else exit_block.get("actual_r")
    )
    # Also check instrumentation block as a secondary alias (v1.1 duplicates here).
    if r_raw is None:
        instrumentation = data.get("instrumentation")
        if isinstance(instrumentation, dict):
            r_raw = instrumentation.get("realized_R")

    r_clipped = _clip_r(r_raw)
    if r_clipped is None:
        return None

    exit_reason = exit_block.get("exit_reason") or exit_block.get("exit_type") or None

    return TradeOutcome(
        instrument=instrument,
        candle_time=ct,
        outcome=_classify_r(r_clipped),
        r_multiple=r_clipped,
        source="live",
        exit_reason=exit_reason,
        raw_candle_time=meta.get("candle_time"),
    )


def _iter_live_trade_records(base: Path) -> Iterable[Path]:
    """Yield trade record JSONs under base_dir/{SYMBOL}/*.json.

    Skips index + pending-records housekeeping files.
    """
    if not base.exists():
        return
    for sym_dir in base.iterdir():
        if not sym_dir.is_dir():
            continue
        for fp in sym_dir.glob("*.json"):
            if "_pending" in fp.name or fp.name.startswith("_"):
                continue
            yield fp


def load_live_trade_outcomes(base: Path) -> list[TradeOutcome]:
    """Load every well-formed trade outcome under the live trade_records dir."""
    out: list[TradeOutcome] = []
    for fp in _iter_live_trade_records(base):
        rec = _load_live_trade_record(fp)
        if rec is not None:
            out.append(rec)
    return out


def _load_simulator_slice(path: Path, source: str) -> list[TradeOutcome]:
    """Load all CANDIDATE rows with a resolved outcome from a simulator slice.

    Simulator slice schema (observed):
        {"results": [{"candle_time": "...", "decision": "CANDIDATE",
                      "symbol": "...", "outcome": "WIN|LOSS|UNFILLED|...",
                      "r_multiple": <num|null>, ...}, ...]}
    """
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.debug("skip simulator slice %s: %s", path, exc)
        return []

    results = data.get("results") if isinstance(data, dict) else None
    if not isinstance(results, list):
        return []

    out: list[TradeOutcome] = []
    for row in results:
        if not isinstance(row, dict):
            continue
        if row.get("decision") != "CANDIDATE":
            continue
        outcome_raw = row.get("outcome")
        if not isinstance(outcome_raw, str):
            continue
        outcome_uc = outcome_raw.upper()
        if outcome_uc not in {"WIN", "LOSS", "BE"}:
            # UNFILLED / PENDING / null -> not a trade.
            continue
        r_clipped = _clip_r(row.get("r_multiple"))
        if r_clipped is None:
            # If outcome is WIN/LOSS without an R, synthesize a minimal R.
            # WIN defaults to +1.5R (system min_rr=1.5), LOSS defaults to -1R.
            # BE defaults to 0. This is a rare branch — most simulator rows
            # have explicit r_multiple.
            if outcome_uc == "WIN":
                r_clipped = 1.5
            elif outcome_uc == "LOSS":
                r_clipped = -1.0
            else:
                r_clipped = 0.0

        instrument = _canonical_instrument(row.get("symbol"))
        if not instrument:
            continue
        ct = _parse_candle_time(row.get("candle_time"))
        if ct is None:
            continue
        out.append(TradeOutcome(
            instrument=instrument,
            candle_time=ct,
            outcome=outcome_uc,
            r_multiple=r_clipped,
            source=source,
            exit_reason=None,
            raw_candle_time=row.get("candle_time"),
        ))
    return out


def load_simulator_outcomes(research_root: Path) -> list[TradeOutcome]:
    """Load simulator outcomes from all known research sources.

    Sources explored:
      - research/a1_adr005_backtest/slices/**/all_results.json
      - research/f3_backtest_2026-04-24/**/all_results.json
      - research/t7_live_simulation/all_results*.json
    """
    outcomes: list[TradeOutcome] = []

    # A1 slices.
    a1_dir = research_root / "a1_adr005_backtest" / "slices"
    if a1_dir.is_dir():
        for slice_dir in sorted(a1_dir.iterdir()):
            fp = slice_dir / "all_results.json"
            if fp.is_file():
                outcomes.extend(_load_simulator_slice(fp, source="a1"))

    # F3 slices.
    f3_dir = research_root / "f3_backtest_2026-04-24"
    if f3_dir.is_dir():
        for slice_dir in sorted(f3_dir.iterdir()):
            if not slice_dir.is_dir():
                continue
            fp = slice_dir / "all_results.json"
            if fp.is_file():
                outcomes.extend(_load_simulator_slice(fp, source="f3"))

    # T7 top-level files.
    t7_dir = research_root / "t7_live_simulation"
    if t7_dir.is_dir():
        for fp in sorted(t7_dir.glob("all_results*.json")):
            outcomes.extend(_load_simulator_slice(fp, source="t7"))

    return outcomes


def union_and_dedup(
    live: list[TradeOutcome],
    simulator: list[TradeOutcome],
) -> list[TradeOutcome]:
    """Union live + simulator outcomes.

    Dedup key is (instrument, candle_time_iso). Live wins on key conflict
    (simulator rows at the same timestamp are dropped because the live
    outcome IS the ground truth).
    """
    seen: dict[tuple[str, str], TradeOutcome] = {}

    # Load live first — claims its keys.
    for rec in live:
        key = (rec.instrument, rec.candle_time.isoformat())
        if key not in seen:
            seen[key] = rec

    # Simulator rows backfill keys live did not claim.
    for rec in simulator:
        key = (rec.instrument, rec.candle_time.isoformat())
        if key not in seen:
            seen[key] = rec

    # Return chronologically sorted.
    return sorted(seen.values(), key=lambda r: (r.instrument, r.candle_time))


# ----------------------------------------------------------------------------
# Bucketing + aggregation
# ----------------------------------------------------------------------------

def _month_label(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def _week_label(dt: datetime) -> str:
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year:04d}-W{iso_week:02d}"


def _bucketize(records: list[TradeOutcome], key_fn) -> dict[str, list[TradeOutcome]]:
    buckets: dict[str, list[TradeOutcome]] = {}
    for rec in records:
        key = key_fn(rec.candle_time)
        buckets.setdefault(key, []).append(rec)
    return buckets


def _bucket_stats(label: str, records: list[TradeOutcome], seed: Optional[int] = None) -> BucketStats:
    n = len(records)
    if n == 0:
        return BucketStats.empty(label)
    wins = sum(1 for r in records if r.outcome == "WIN")
    losses = sum(1 for r in records if r.outcome == "LOSS")
    be = sum(1 for r in records if r.outcome == "BE")
    rs = [r.r_multiple for r in records]
    exp = sum(rs) / n
    wr_lo, wr_hi = wilson_ci(wins, n)
    exp_lo, exp_hi = bootstrap_mean_ci(rs, seed=seed)
    return BucketStats(
        label=label, n=n, wins=wins, losses=losses, be=be,
        wr=wins / n if n else 0.0,
        wr_ci_lo=wr_lo, wr_ci_hi=wr_hi,
        exp_r=exp, exp_ci_lo=exp_lo, exp_ci_hi=exp_hi,
        total_r=sum(rs),
    )


def aggregate_by_instrument(
    records: list[TradeOutcome],
    as_of: datetime,
    seed: Optional[int] = None,
) -> dict[str, InstrumentAggregate]:
    """Return per-instrument monthly + weekly buckets, chronologically sorted."""
    per_inst: dict[str, list[TradeOutcome]] = {}
    for r in records:
        per_inst.setdefault(r.instrument, []).append(r)

    result: dict[str, InstrumentAggregate] = {}
    # Ensure all default instruments appear even if empty (for placeholder tables).
    for inst in list(per_inst.keys()) + list(DEFAULT_INSTRUMENTS):
        if inst in result:
            continue
        inst_records = per_inst.get(inst, [])
        month_buckets = _bucketize(inst_records, _month_label)
        week_buckets = _bucketize(inst_records, _week_label)
        monthly = [
            _bucket_stats(label, month_buckets[label], seed=seed)
            for label in sorted(month_buckets.keys())
        ]
        weekly_all = [
            _bucket_stats(label, week_buckets[label], seed=seed)
            for label in sorted(week_buckets.keys())
        ]
        result[inst] = InstrumentAggregate(
            instrument=inst,
            monthly=monthly,
            weekly=weekly_all,
        )
    return result


# ----------------------------------------------------------------------------
# Alert detection
# ----------------------------------------------------------------------------

@dataclass
class Alert:
    severity: str                    # "HIGH" | "INFO"
    instrument: str
    kind: str                        # "WR_DECAY" | "EXP_DECAY" | "CONSECUTIVE_WEAKNESS" | "INSUFFICIENT_SAMPLE"
    message: str
    evidence: dict[str, Any]


def _prev_n_buckets(buckets: list[BucketStats], current_label: str, n: int) -> list[BucketStats]:
    """Return up to n buckets immediately preceding current_label (chronological order)."""
    try:
        idx = next(i for i, b in enumerate(buckets) if b.label == current_label)
    except StopIteration:
        return []
    start = max(0, idx - n)
    return buckets[start:idx]


def _weighted_baseline(buckets: list[BucketStats]) -> tuple[float, float, int]:
    """Pool buckets into a (wr, exp_r, n_total) weighted baseline."""
    total_n = sum(b.n for b in buckets)
    if total_n == 0:
        return (0.0, 0.0, 0)
    total_wins = sum(b.wins for b in buckets)
    total_r = sum(b.total_r for b in buckets)
    return (total_wins / total_n, total_r / total_n, total_n)


def detect_alerts(
    aggregates: dict[str, InstrumentAggregate],
    as_of: datetime,
    breakeven_wr: dict[str, float] = BREAKEVEN_WR,
) -> list[Alert]:
    alerts: list[Alert] = []
    current_month = _month_label(as_of)

    for instrument in sorted(aggregates.keys()):
        agg = aggregates[instrument]

        # Identify the current-month bucket (or explicit empty one if missing).
        current_bucket = next(
            (b for b in agg.monthly if b.label == current_month),
            None,
        )
        prev_months = _prev_n_buckets(
            agg.monthly,
            current_label=current_month,
            n=BASELINE_WINDOW_MONTHS,
        ) if current_bucket is not None else []
        # If current month has no bucket, use most-recent month AS current
        # + the 3 months before that.
        if current_bucket is None and agg.monthly:
            current_bucket = agg.monthly[-1]
            prev_months = agg.monthly[-1 - BASELINE_WINDOW_MONTHS:-1]

        if current_bucket is None:
            # No data at all for this instrument — skip silently unless you
            # want a LOW-severity "no data" info. We keep it quiet for now.
            continue

        n_curr = current_bucket.n

        if n_curr < INSUFFICIENT_N:
            alerts.append(Alert(
                severity="INFO",
                instrument=instrument,
                kind="INSUFFICIENT_SAMPLE",
                message=(
                    f"n={n_curr} < {INSUFFICIENT_N} — WR / Exp alarms gated. "
                    f"Current WR {current_bucket.wr * 100:.1f}% (Wilson CI "
                    f"[{current_bucket.wr_ci_lo * 100:.1f}, {current_bucket.wr_ci_hi * 100:.1f}])."
                ),
                evidence={
                    "current_month": current_bucket.label,
                    "n_current": n_curr,
                    "wr_current": current_bucket.wr,
                    "required_n": INSUFFICIENT_N,
                },
            ))
        else:
            # WR decay check.
            baseline_wr, baseline_exp, baseline_n = _weighted_baseline(prev_months)
            if baseline_n > 0:
                wr_drop = baseline_wr - current_bucket.wr
                if wr_drop > WR_DROP_THRESHOLD_PP:
                    alerts.append(Alert(
                        severity="HIGH",
                        instrument=instrument,
                        kind="WR_DECAY",
                        message=(
                            f"WR dropped {wr_drop * 100:.1f}pp "
                            f"(threshold {WR_DROP_THRESHOLD_PP * 100:.0f}pp): "
                            f"current {current_bucket.wr * 100:.1f}% (n={n_curr}) vs "
                            f"{BASELINE_WINDOW_MONTHS}-month baseline "
                            f"{baseline_wr * 100:.1f}% (n={baseline_n})."
                        ),
                        evidence={
                            "current_month": current_bucket.label,
                            "n_current": n_curr,
                            "wr_current": current_bucket.wr,
                            "wr_current_ci": [current_bucket.wr_ci_lo, current_bucket.wr_ci_hi],
                            "wr_baseline": baseline_wr,
                            "n_baseline": baseline_n,
                            "baseline_months": [b.label for b in prev_months],
                            "drop_pp": wr_drop,
                            "threshold_pp": WR_DROP_THRESHOLD_PP,
                        },
                    ))

                exp_drop = baseline_exp - current_bucket.exp_r
                if exp_drop > EXP_DROP_THRESHOLD:
                    alerts.append(Alert(
                        severity="HIGH",
                        instrument=instrument,
                        kind="EXP_DECAY",
                        message=(
                            f"Expectancy dropped {exp_drop:.2f}R "
                            f"(threshold {EXP_DROP_THRESHOLD:.2f}R): "
                            f"current {current_bucket.exp_r:+.2f}R (n={n_curr}) vs "
                            f"{BASELINE_WINDOW_MONTHS}-month baseline {baseline_exp:+.2f}R (n={baseline_n})."
                        ),
                        evidence={
                            "current_month": current_bucket.label,
                            "n_current": n_curr,
                            "exp_current": current_bucket.exp_r,
                            "exp_current_ci": [current_bucket.exp_ci_lo, current_bucket.exp_ci_hi],
                            "exp_baseline": baseline_exp,
                            "n_baseline": baseline_n,
                            "baseline_months": [b.label for b in prev_months],
                            "drop_r": exp_drop,
                            "threshold_r": EXP_DROP_THRESHOLD,
                        },
                    ))

        # Consecutive-weakness check — last CONSECUTIVE_WEEK_N weeks below breakeven.
        breakeven = breakeven_wr.get(instrument, DEFAULT_BREAKEVEN_WR)
        recent_weeks = agg.weekly[-CONSECUTIVE_WEEK_N:] if len(agg.weekly) >= CONSECUTIVE_WEEK_N else []
        if recent_weeks and all(
            w.n >= WEEK_MIN_N and w.wr < breakeven for w in recent_weeks
        ):
            alerts.append(Alert(
                severity="HIGH",
                instrument=instrument,
                kind="CONSECUTIVE_WEAKNESS",
                message=(
                    f"{CONSECUTIVE_WEEK_N} consecutive weeks with WR < "
                    f"{breakeven * 100:.1f}% breakeven: "
                    + ", ".join(f"{w.label} WR={w.wr * 100:.1f}% (n={w.n})" for w in recent_weeks)
                ),
                evidence={
                    "weeks": [
                        {"label": w.label, "n": w.n, "wr": w.wr}
                        for w in recent_weeks
                    ],
                    "breakeven_wr": breakeven,
                },
            ))

    return alerts


# ----------------------------------------------------------------------------
# Forecast
# ----------------------------------------------------------------------------

def forecast_next_30_days(
    aggregates: dict[str, InstrumentAggregate],
    as_of: datetime,
) -> dict[str, dict[str, Any]]:
    """Project trade count + WR for the next 30 days per-instrument.

    Uses current-month run-rate (trades / elapsed days in current month).
    No attempt at multi-month trend fitting — premature.
    """
    current_month = _month_label(as_of)
    # Days elapsed this month (1..today.day); clamp to >=1 to avoid div/0.
    elapsed = max(1, as_of.day)
    out: dict[str, dict[str, Any]] = {}

    for instrument in sorted(aggregates.keys()):
        agg = aggregates[instrument]
        current = next((b for b in agg.monthly if b.label == current_month), None)
        if current is None or current.n == 0:
            out[instrument] = {
                "projected_trades_30d": 0,
                "wr_point_estimate": 0.0,
                "note": "no current-month data",
            }
            continue
        rate_per_day = current.n / elapsed
        projected = int(round(rate_per_day * 30))
        out[instrument] = {
            "projected_trades_30d": projected,
            "wr_point_estimate": current.wr,
            "note": f"rate {rate_per_day:.2f} trades/day from current-month n={current.n} over {elapsed} days",
        }
    return out


# ----------------------------------------------------------------------------
# Report renderer
# ----------------------------------------------------------------------------

def _trend_bar(values: list[tuple[str, float, int]], width: int = 30) -> list[str]:
    """Render a simple ASCII bar chart for (label, ratio, n) triples."""
    if not values:
        return ["(no data)"]
    rows = []
    for label, val, n in values:
        bars = int(round(val * width))
        rows.append(f"  {label}  {'#' * bars}{'.' * (width - bars)}  {val * 100:5.1f}%  (n={n})")
    return rows


def _source_mix(records: list[TradeOutcome]) -> dict[str, int]:
    mix: dict[str, int] = {}
    for r in records:
        mix[r.source] = mix.get(r.source, 0) + 1
    return mix


def render_report(
    aggregates: dict[str, InstrumentAggregate],
    alerts: list[Alert],
    records: list[TradeOutcome],
    as_of: datetime,
    generated_at: Optional[datetime] = None,
    forecasts: Optional[dict[str, dict[str, Any]]] = None,
) -> str:
    if generated_at is None:
        generated_at = datetime.now(timezone.utc)
    if forecasts is None:
        forecasts = forecast_next_30_days(aggregates, as_of)

    lines: list[str] = []
    lines.append(f"# Monthly-Decay Shadow Monitor — {_month_label(as_of)}")
    lines.append("")
    lines.append(f"**Generated (UTC):** {generated_at.isoformat(timespec='seconds')}")
    lines.append(f"**As-of (UTC):** {as_of.isoformat(timespec='seconds')}")
    lines.append("")

    # Coverage.
    if records:
        first = min(r.candle_time for r in records)
        last = max(r.candle_time for r in records)
        lines.append(f"**Coverage:** {first.date()} → {last.date()} "
                     f"({len(records)} total trades across {len(set(r.instrument for r in records))} instruments)")
    else:
        lines.append("**Coverage:** _no trade outcomes ingested — monitor has nothing to report._")
    mix = _source_mix(records)
    if mix:
        lines.append(f"**Source mix:** " + ", ".join(
            f"{src}={n}" for src, n in sorted(mix.items(), key=lambda kv: -kv[1])
        ))
    lines.append("")

    # Alerts section first — the most important content.
    lines.append("## Alerts")
    lines.append("")
    high_alerts = [a for a in alerts if a.severity == "HIGH"]
    info_alerts = [a for a in alerts if a.severity != "HIGH"]
    if not high_alerts and not info_alerts:
        lines.append("- _no alerts fired_")
    if high_alerts:
        lines.append("### HIGH")
        for a in high_alerts:
            lines.append(f"- **{a.instrument} / {a.kind}** — {a.message}")
    if info_alerts:
        lines.append("")
        lines.append("### INFO")
        for a in info_alerts:
            lines.append(f"- **{a.instrument} / {a.kind}** — {a.message}")
    lines.append("")

    # Per-instrument monthly table.
    lines.append("## Per-instrument monthly (Wilson 95% CI / bootstrap 95% CI)")
    lines.append("")
    for inst in sorted(aggregates.keys()):
        agg = aggregates[inst]
        lines.append(f"### {inst}")
        if not agg.monthly:
            lines.append("_(no data)_")
            lines.append("")
            continue
        lines.append("")
        lines.append("| Month | n | WR | WR 95% CI | Exp R | Exp 95% CI | Total R |")
        lines.append("|---|---:|---:|---|---:|---|---:|")
        for b in agg.monthly:
            lines.append(
                f"| {b.label} | {b.n} | {b.wr * 100:.1f}% | "
                f"[{b.wr_ci_lo * 100:.1f}%, {b.wr_ci_hi * 100:.1f}%] | "
                f"{b.exp_r:+.2f}R | "
                f"[{b.exp_ci_lo:+.2f}, {b.exp_ci_hi:+.2f}] | "
                f"{b.total_r:+.2f}R |"
            )
        lines.append("")

    # Per-instrument weekly table (last 12 weeks).
    lines.append("## Per-instrument weekly (last 12 weeks)")
    lines.append("")
    for inst in sorted(aggregates.keys()):
        agg = aggregates[inst]
        lines.append(f"### {inst}")
        recent = agg.weekly[-WEEKLY_ROWS:]
        if not recent:
            lines.append("_(no data)_")
            lines.append("")
            continue
        lines.append("")
        lines.append("| Week | n | WR | Exp R |")
        lines.append("|---|---:|---:|---:|")
        for b in recent:
            lines.append(f"| {b.label} | {b.n} | {b.wr * 100:.1f}% | {b.exp_r:+.2f}R |")
        lines.append("")

    # ASCII trend — monthly WR per instrument.
    lines.append("## Monthly WR trend (ASCII)")
    lines.append("")
    for inst in sorted(aggregates.keys()):
        agg = aggregates[inst]
        if not agg.monthly:
            continue
        lines.append(f"### {inst}")
        lines.append("```")
        rows = _trend_bar([(b.label, b.wr, b.n) for b in agg.monthly])
        lines.extend(rows)
        lines.append("```")
        lines.append("")

    # Forecast.
    lines.append("## Forecast")
    lines.append("")
    lines.append("Projects next 30 days at current-month run-rate. Not a prediction — "
                 "a sanity check on whether the monitor will have enough samples to "
                 "trigger the n>=10 gate again next month.")
    lines.append("")
    lines.append("| Instrument | Projected trades (30d) | WR (point estimate) | Note |")
    lines.append("|---|---:|---:|---|")
    for inst in sorted(aggregates.keys()):
        f = forecasts.get(inst, {})
        trades = f.get("projected_trades_30d", 0)
        wr = f.get("wr_point_estimate", 0.0) or 0.0
        note = f.get("note", "")
        lines.append(f"| {inst} | {trades} | {wr * 100:.1f}% | {note} |")
    lines.append("")

    # Footer.
    lines.append("---")
    lines.append("")
    lines.append("_Generated by `scripts/monthly_decay_monitor.py`. This is an "
                 "observation-only shadow monitor — alerts are signals for CEO "
                 "review, NOT automatic trading-state changes._")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def _parse_as_of(raw: Optional[str]) -> datetime:
    if raw is None:
        return datetime.now(timezone.utc)
    # Accept both YYYY-MM-DD and ISO 8601 forms.
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        # YYYY-MM-DD only fallback.
        dt = datetime.strptime(raw, "%Y-%m-%d")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _default_output_path(as_of: datetime) -> Path:
    return Path("research") / "monthly_decay_monitor" / f"{_month_label(as_of)}_report.md"


def run_monitor(
    trade_records_dir: Path,
    simulator_root: Path,
    output: Path,
    as_of: datetime,
    seed: Optional[int] = None,
) -> dict[str, Any]:
    """Full pipeline: load, dedupe, aggregate, alert, render, write.

    Returns a result dict suitable for programmatic callers and tests.
    """
    live = load_live_trade_outcomes(trade_records_dir)
    sim = load_simulator_outcomes(simulator_root)
    records = union_and_dedup(live, sim)

    aggregates = aggregate_by_instrument(records, as_of, seed=seed)
    alerts = detect_alerts(aggregates, as_of)
    forecasts = forecast_next_30_days(aggregates, as_of)

    md = render_report(aggregates, alerts, records, as_of, forecasts=forecasts)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(md, encoding="utf-8")

    return {
        "output_path": str(output),
        "n_records": len(records),
        "n_live": len(live),
        "n_simulator": len(sim),
        "aggregates": aggregates,
        "alerts": alerts,
        "forecasts": forecasts,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Monthly-decay shadow monitor")
    parser.add_argument(
        "--trade-records-dir",
        type=Path,
        default=Path("knowledge_base/trade_records"),
        help="Root of live trade records (A3 v1.1 schema). Default: knowledge_base/trade_records",
    )
    parser.add_argument(
        "--simulator-root",
        type=Path,
        default=Path("research"),
        help="Root under which a1/f3/t7 simulator results live. Default: research/",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Markdown output path. Default: research/monthly_decay_monitor/YYYY-MM_report.md",
    )
    parser.add_argument(
        "--as-of",
        type=str,
        default=None,
        help="UTC date/time to anchor the 'current month' (YYYY-MM-DD or ISO 8601). Default: now().",
    )
    parser.add_argument(
        "--bootstrap-seed",
        type=int,
        default=None,
        help="Seed for bootstrap resampling (deterministic tests).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    as_of = _parse_as_of(args.as_of)
    output = args.output or _default_output_path(as_of)

    result = run_monitor(
        trade_records_dir=args.trade_records_dir,
        simulator_root=args.simulator_root,
        output=output,
        as_of=as_of,
        seed=args.bootstrap_seed,
    )

    high_count = sum(1 for a in result["alerts"] if a.severity == "HIGH")
    info_count = sum(1 for a in result["alerts"] if a.severity != "HIGH")
    logger.info(
        "monitor complete: %d records (%d live + %d simulator) -> %s "
        "with %d HIGH / %d INFO alerts",
        result["n_records"],
        result["n_live"],
        result["n_simulator"],
        result["output_path"],
        high_count,
        info_count,
    )
    # Exit codes (watchdog contract):
    #   0  = OK (report written, no HIGH alerts)
    #   1  = ALARM (report written, >=1 HIGH alert fired — CEO review required)
    #   2+ = transient failure (never reached under normal operation; script
    #        will raise on IO errors and the caller's exception handler wins)
    return 1 if high_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
