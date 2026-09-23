"""F2-SWEEP — dead-zone-divisor sensitivity sweep for ``identify_structure_v2``.

Zero-API-cost historical sweep to pick the best ``dead_zone_divisor`` before
committing $30-50 to the F3 backtest. See ADR-004 + F2.2 cold review for the
motivation (v2 at divisor=4 on 168-bar H1 production windows produces dead
zone ~20, which absorbs most observed score magnitudes → near-100%
transitional, OB supply collapses).

Procedure per instrument × 168-bar rolling H1 window (step=24) × divisor d in
``{2, 4, 6, 8, 12}``:

    swings        = detect_swings(candles)
    structure_v1  = identify_structure(swings)
    structure_v2  = identify_structure_v2(swings, dead_zone_divisor=d)
    events_v1/v2  = detect_structure_breaks(candles, swings, structure_X)
    obs_v1/v2     = identify_order_blocks(candles, events_X)

Then reports:

  * Label distribution per (instrument, divisor) — bullish/bearish/transitional/
    insufficient_data counts + percentages.
  * OB supply: total, bullish, bearish, under v1 and under v2 at each
    divisor. Ratio v2/v1 exposes the F2.2-flagged 47% USDJPY worst-case.
  * Fleet-wide aggregate + a 4-criterion acceptance scoreboard.

Usage::

    python scripts/f2_dead_zone_sweep.py
                                         [--start 2026-01-02] [--end 2026-04-13]

No external dependencies beyond project imports. Runs purely on CSV data from
``data/historical_2026/{SYMBOL}_H1.csv``.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.components.market_state import (
    detect_structure_breaks,
    detect_swings,
    identify_order_blocks,
    identify_structure,
    identify_structure_v2,
)


SYMBOLS: tuple[str, ...] = ("XAUUSD", "USDJPY", "GBPJPY", "US30_cash", "GBPUSD")
DIVISORS: tuple[int, ...] = (2, 4, 6, 8, 12)
WINDOW_BARS = 168
STEP_BARS = 24
DATA_DIR = _REPO / "data" / "historical_2026"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_iso(ts: str) -> datetime | None:
    """Best-effort ISO parser. Accepts Z and ``+HH:MM`` suffixes."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_h1(symbol: str, start: datetime | None, end: datetime | None) -> list[dict]:
    """Load H1 CSV bars between ``[start, end]`` inclusive.

    CSV schema: ``time,open,high,low,close,volume``. Rows with unparseable
    timestamps or numeric fields are skipped silently (counted via the
    printed summary only when the caller wants it).
    """
    fp = DATA_DIR / f"{symbol}_H1.csv"
    if not fp.exists():
        return []
    out: list[dict] = []
    with fp.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = row.get("time") or ""
            dt = _parse_iso(ts)
            if dt is None:
                continue
            # Normalize to UTC-aware for filter comparison.
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if start is not None and dt < start:
                continue
            if end is not None and dt > end:
                continue
            try:
                out.append({
                    "time": ts,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0) or 0),
                })
            except (ValueError, KeyError):
                continue
    return out


def rolling(bars: list[dict], window: int, step: int):
    """Yield non-overlapping step-spaced rolling windows."""
    if len(bars) < window:
        return
    for i in range(window, len(bars) + 1, step):
        yield bars[i - window : i]


# ---------------------------------------------------------------------------
# Aggregators
# ---------------------------------------------------------------------------


@dataclass
class WindowStats:
    """One instrument × one divisor: label distribution + OB supply."""

    labels: Counter = field(default_factory=Counter)
    total_obs: int = 0
    bull_obs: int = 0
    bear_obs: int = 0
    windows: int = 0


@dataclass
class V1Stats:
    """Baseline v1 stats for an instrument (no divisor dimension)."""

    labels: Counter = field(default_factory=Counter)
    total_obs: int = 0
    bull_obs: int = 0
    bear_obs: int = 0
    windows: int = 0


# ---------------------------------------------------------------------------
# Core sweep
# ---------------------------------------------------------------------------


def sweep_instrument(
    symbol: str,
    bars: list[dict],
    divisors: tuple[int, ...],
) -> tuple[V1Stats, dict[int, WindowStats]]:
    """Compute v1 baseline + v2-per-divisor stats on one instrument."""
    v1 = V1Stats()
    v2_by_d: dict[int, WindowStats] = {d: WindowStats() for d in divisors}

    for window in rolling(bars, WINDOW_BARS, STEP_BARS):
        swings = detect_swings(window)
        structure_v1 = identify_structure(swings)
        events_v1 = detect_structure_breaks(window, swings, structure_v1)
        obs_v1 = identify_order_blocks(window, events_v1)

        v1.labels[structure_v1.direction] += 1
        v1.total_obs += len(obs_v1)
        v1.bull_obs += sum(1 for ob in obs_v1 if ob.type == "bullish")
        v1.bear_obs += sum(1 for ob in obs_v1 if ob.type == "bearish")
        v1.windows += 1

        for d in divisors:
            structure_v2 = identify_structure_v2(swings, dead_zone_divisor=d)
            events_v2 = detect_structure_breaks(window, swings, structure_v2)
            obs_v2 = identify_order_blocks(window, events_v2)
            s = v2_by_d[d]
            s.labels[structure_v2.direction] += 1
            s.total_obs += len(obs_v2)
            s.bull_obs += sum(1 for ob in obs_v2 if ob.type == "bullish")
            s.bear_obs += sum(1 for ob in obs_v2 if ob.type == "bearish")
            s.windows += 1

    return v1, v2_by_d


# ---------------------------------------------------------------------------
# Acceptance criteria
# ---------------------------------------------------------------------------


def _pct(num: int, denom: int) -> float:
    return (100.0 * num / denom) if denom else 0.0


def _label_pct(s: WindowStats | V1Stats, label: str) -> float:
    total = sum(s.labels.values())
    return _pct(s.labels.get(label, 0), total)


def acceptance_row(
    divisor: int,
    v2_by_sym: dict[str, WindowStats],
    v1_by_sym: dict[str, V1Stats],
) -> dict:
    """Compute the 4 acceptance criteria for one divisor.

    1. Symmetry: |agg_bullish% - agg_bearish%| < 10pp.
    2. Transitional rate in [10, 30]% aggregate AND per-instrument.
    3. OB preservation: v2_total / v1_total > 70% per instrument.
    4. Directional balance: max(bullish%, bearish%) < 60% per instrument.
    """
    agg_labels: Counter = Counter()
    for s in v2_by_sym.values():
        agg_labels.update(s.labels)
    agg_total = sum(agg_labels.values())
    agg_bull_pct = _pct(agg_labels.get("bullish", 0), agg_total)
    agg_bear_pct = _pct(agg_labels.get("bearish", 0), agg_total)
    agg_trans_pct = _pct(agg_labels.get("transitional", 0), agg_total)
    agg_insuf_pct = _pct(agg_labels.get("insufficient_data", 0), agg_total)

    # (1) Symmetry
    symmetry_gap = abs(agg_bull_pct - agg_bear_pct)
    symmetry_pass = symmetry_gap < 10.0

    # (2) Transitional rate (aggregate + per-instrument in [10, 30])
    trans_ok_agg = 10.0 <= agg_trans_pct <= 30.0
    trans_per_sym: dict[str, float] = {
        sym: _label_pct(s, "transitional") for sym, s in v2_by_sym.items()
    }
    trans_ok_per_sym = {
        sym: 10.0 <= pct <= 30.0 for sym, pct in trans_per_sym.items()
    }
    trans_pass = trans_ok_agg and all(trans_ok_per_sym.values())

    # (3) OB preservation per instrument
    ob_ratio_per_sym: dict[str, float] = {}
    ob_preserve_per_sym: dict[str, bool] = {}
    for sym, s in v2_by_sym.items():
        v1 = v1_by_sym[sym]
        ratio = (s.total_obs / v1.total_obs) if v1.total_obs else 0.0
        ob_ratio_per_sym[sym] = ratio
        ob_preserve_per_sym[sym] = ratio > 0.70
    ob_pass = all(ob_preserve_per_sym.values())

    # (4) Directional balance per instrument
    max_dir_per_sym: dict[str, float] = {}
    dir_bal_per_sym: dict[str, bool] = {}
    for sym, s in v2_by_sym.items():
        max_dir = max(_label_pct(s, "bullish"), _label_pct(s, "bearish"))
        max_dir_per_sym[sym] = max_dir
        dir_bal_per_sym[sym] = max_dir < 60.0
    dir_pass = all(dir_bal_per_sym.values())

    criteria_pass = int(symmetry_pass) + int(trans_pass) + int(ob_pass) + int(dir_pass)

    return {
        "divisor": divisor,
        "agg_bull_pct": agg_bull_pct,
        "agg_bear_pct": agg_bear_pct,
        "agg_trans_pct": agg_trans_pct,
        "agg_insuf_pct": agg_insuf_pct,
        "symmetry_gap": symmetry_gap,
        "symmetry_pass": symmetry_pass,
        "trans_ok_agg": trans_ok_agg,
        "trans_per_sym": trans_per_sym,
        "trans_ok_per_sym": trans_ok_per_sym,
        "trans_pass": trans_pass,
        "ob_ratio_per_sym": ob_ratio_per_sym,
        "ob_preserve_per_sym": ob_preserve_per_sym,
        "ob_pass": ob_pass,
        "max_dir_per_sym": max_dir_per_sym,
        "dir_bal_per_sym": dir_bal_per_sym,
        "dir_pass": dir_pass,
        "criteria_pass_count": criteria_pass,
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def fmt_pct(x: float) -> str:
    return f"{x:.1f}%"


def fmt_ratio(x: float) -> str:
    return f"{x:.2f}"


def build_report(
    v1_by_sym: dict[str, V1Stats],
    v2_by_sym_by_d: dict[int, dict[str, WindowStats]],
    divisors: tuple[int, ...],
    symbols: tuple[str, ...],
    start: datetime | None,
    end: datetime | None,
    bar_counts: dict[str, int],
    window_counts: dict[str, int],
) -> str:
    """Render the full markdown report."""
    lines: list[str] = []
    add = lines.append

    add("# WAVE2 — F2-SWEEP Dead-Zone Divisor Report")
    add("")
    add(
        "Offline zero-cost sensitivity sweep over ``dead_zone_divisor`` in "
        "``identify_structure_v2``. See the task brief and ADR-004 for "
        "motivation."
    )
    add("")

    # --- Methodology ---
    add("## 1. Methodology")
    add("")
    start_s = start.date().isoformat() if start else "min(data)"
    end_s = end.date().isoformat() if end else "max(data)"
    add(
        f"- **Instruments:** {', '.join(symbols)}"
    )
    add(
        f"- **Timeframe:** H1 candles from ``data/historical_2026/{{SYMBOL}}_H1.csv``"
    )
    add(
        f"- **Date range filter:** ``{start_s} → {end_s}`` (inclusive)"
    )
    add(
        f"- **Rolling window:** {WINDOW_BARS} bars (~1 week) with step {STEP_BARS} "
        f"(~1 day)"
    )
    add(
        f"- **Divisors probed:** {list(divisors)}"
    )
    add("- **No API calls.** Pure offline detect_swings + identify_structure_v2 + "
        "detect_structure_breaks + identify_order_blocks replay.")
    add("")
    add("Per window: compute v1 baseline once, then v2 at each divisor. v1 and "
        "v2 share the same swings (so ``detect_swings`` output is identical); "
        "OB supply differs only because ``detect_structure_breaks`` branches "
        "on ``structure.direction``. Windows labeled ``transitional`` by v2 "
        "(with ``protected_swing=None``, the only form v2 emits for transitional) "
        "produce zero BOS and zero CHoCH — the CHoCH block in "
        "``detect_structure_breaks`` requires a protected swing and the BOS "
        "block branches only on ``bullish``/``bearish``. Zero structure events "
        "in turn yield zero OBs from ``identify_order_blocks``. This is the "
        "dominant mechanism behind the OB-supply drop the sweep quantifies.")
    add("")
    add("### Data provenance")
    add("")
    add("| Symbol | Bars loaded | Windows evaluated |")
    add("|--------|-------------|-------------------|")
    for sym in symbols:
        add(f"| {sym} | {bar_counts.get(sym, 0):,} | {window_counts.get(sym, 0):,} |")
    add("")

    # --- Per-instrument × per-divisor label distribution ---
    add("## 2. Label distribution per (instrument, divisor)")
    add("")
    add("Rows are (instrument, divisor). v1 baseline shown once per symbol. "
        "Percentages computed over all evaluated windows including "
        "``insufficient_data``.")
    add("")
    add("| Instrument | Divisor | Windows | Bullish | Bearish | Transitional | Insufficient |")
    add("|------------|---------|---------|---------|---------|--------------|--------------|")
    for sym in symbols:
        v1 = v1_by_sym[sym]
        total_v1 = sum(v1.labels.values())
        add(
            f"| {sym} | v1 (baseline) | {total_v1} | "
            f"{fmt_pct(_label_pct(v1, 'bullish'))} | "
            f"{fmt_pct(_label_pct(v1, 'bearish'))} | "
            f"{fmt_pct(_label_pct(v1, 'transitional'))} | "
            f"{fmt_pct(_label_pct(v1, 'insufficient_data'))} |"
        )
        for d in divisors:
            s = v2_by_sym_by_d[d][sym]
            total = sum(s.labels.values())
            add(
                f"| {sym} | {d} | {total} | "
                f"{fmt_pct(_label_pct(s, 'bullish'))} | "
                f"{fmt_pct(_label_pct(s, 'bearish'))} | "
                f"{fmt_pct(_label_pct(s, 'transitional'))} | "
                f"{fmt_pct(_label_pct(s, 'insufficient_data'))} |"
            )
    add("")

    # --- OB supply ---
    add("## 3. OB supply per (instrument, divisor)")
    add("")
    add("Total OBs, split by bullish/bearish type. ``v2 / v1`` column is the "
        "preservation ratio the F2.2 cold review flagged at 47% on USDJPY. "
        "Target: > 70%.")
    add("")
    add("| Instrument | Divisor | Total OBs | Bullish OBs | Bearish OBs | v2/v1 |")
    add("|------------|---------|-----------|-------------|-------------|-------|")
    for sym in symbols:
        v1 = v1_by_sym[sym]
        add(
            f"| {sym} | v1 (baseline) | {v1.total_obs} | "
            f"{v1.bull_obs} | {v1.bear_obs} | 1.00 |"
        )
        for d in divisors:
            s = v2_by_sym_by_d[d][sym]
            ratio = (s.total_obs / v1.total_obs) if v1.total_obs else 0.0
            add(
                f"| {sym} | {d} | {s.total_obs} | "
                f"{s.bull_obs} | {s.bear_obs} | {fmt_ratio(ratio)} |"
            )
    add("")

    # --- Acceptance scoreboard ---
    add("## 4. Acceptance scoreboard")
    add("")
    add("Per-divisor pass/fail on the 4 acceptance criteria:")
    add("")
    add("1. **Symmetry** — aggregate ``|bullish% - bearish%| < 10pp``.")
    add("2. **Transitional rate** — aggregate AND per-instrument in [10, 30]%.")
    add("3. **OB preservation** — ``v2_total_OBs / v1_total_OBs > 70%`` per instrument.")
    add("4. **Directional balance** — ``max(bullish%, bearish%) < 60%`` per instrument.")
    add("")
    add("| Divisor | Bull% | Bear% | Trans% | Symm (1) | Trans (2) | OB (3) | Dir (4) | Pass count |")
    add("|---------|-------|-------|--------|----------|-----------|--------|---------|------------|")

    rows = []
    for d in divisors:
        row = acceptance_row(d, v2_by_sym_by_d[d], v1_by_sym)
        rows.append(row)
        add(
            f"| {d} | {fmt_pct(row['agg_bull_pct'])} | "
            f"{fmt_pct(row['agg_bear_pct'])} | "
            f"{fmt_pct(row['agg_trans_pct'])} | "
            f"{'PASS' if row['symmetry_pass'] else 'FAIL'} ({fmt_pct(row['symmetry_gap'])}) | "
            f"{'PASS' if row['trans_pass'] else 'FAIL'} | "
            f"{'PASS' if row['ob_pass'] else 'FAIL'} | "
            f"{'PASS' if row['dir_pass'] else 'FAIL'} | "
            f"{row['criteria_pass_count']}/4 |"
        )
    add("")

    # --- Per-instrument detail on failure modes ---
    add("### 4.1 Per-instrument failure-mode breakdown")
    add("")
    add("For each divisor, shows the instruments that individually fail each "
        "non-aggregate criterion. Empty cells = all instruments pass.")
    add("")
    add("| Divisor | Trans fails (sym: %) | OB ratio fails (sym: ratio) | Dir fails (sym: max%) |")
    add("|---------|----------------------|-----------------------------|-----------------------|")
    for row in rows:
        d = row["divisor"]
        trans_fails = [
            f"{sym}: {fmt_pct(row['trans_per_sym'][sym])}"
            for sym, ok in row["trans_ok_per_sym"].items() if not ok
        ]
        ob_fails = [
            f"{sym}: {fmt_ratio(row['ob_ratio_per_sym'][sym])}"
            for sym, ok in row["ob_preserve_per_sym"].items() if not ok
        ]
        dir_fails = [
            f"{sym}: {fmt_pct(row['max_dir_per_sym'][sym])}"
            for sym, ok in row["dir_bal_per_sym"].items() if not ok
        ]
        add(
            f"| {d} | "
            f"{', '.join(trans_fails) if trans_fails else '(none)'} | "
            f"{', '.join(ob_fails) if ob_fails else '(none)'} | "
            f"{', '.join(dir_fails) if dir_fails else '(none)'} |"
        )
    add("")

    # --- Recommendation ---
    add("## 5. Recommendation")
    add("")

    # Severity-aware tie-break among rows with the max pass count.
    # For each row compute a "miss magnitude" on each criterion:
    #   symm: max(0, symmetry_gap - 10)
    #   trans: count of instruments outside [10,30] + agg excess above 30
    #   ob: count of instruments with ratio <= 0.70 + magnitude below 0.70
    #   dir: count of instruments with max-dir >= 60 + magnitude above 60
    # Lower aggregated miss = closer to passing.
    def _miss_severity(row: dict) -> float:
        sev = 0.0
        if not row["symmetry_pass"]:
            sev += max(0.0, row["symmetry_gap"] - 10.0)
        if not row["trans_pass"]:
            sev += sum(
                max(0.0, pct - 30.0) + max(0.0, 10.0 - pct)
                for pct in row["trans_per_sym"].values()
            )
            if row["agg_trans_pct"] > 30:
                sev += (row["agg_trans_pct"] - 30.0) * 0.5
            if row["agg_trans_pct"] < 10:
                sev += (10.0 - row["agg_trans_pct"]) * 0.5
        if not row["ob_pass"]:
            sev += sum(
                max(0.0, 0.70 - r) * 100.0
                for r in row["ob_ratio_per_sym"].values()
            )
        if not row["dir_pass"]:
            sev += sum(
                max(0.0, pct - 60.0)
                for pct in row["max_dir_per_sym"].values()
            )
        return sev

    max_pass = max(r["criteria_pass_count"] for r in rows)
    top_rows = [r for r in rows if r["criteria_pass_count"] == max_pass]
    # Prefer lowest total miss severity; tie-break on lowest divisor (smaller
    # change from current default).
    best = min(
        top_rows,
        key=lambda r: (_miss_severity(r), r["divisor"]),
    )
    winner = best["divisor"]
    all_pass_rows = [r for r in rows if r["criteria_pass_count"] == 4]
    if all_pass_rows:
        tie_break = min(
            all_pass_rows,
            key=lambda r: (abs(r["agg_trans_pct"] - 20.0), r["divisor"]),
        )
        winner = tie_break["divisor"]
        add(
            f"**Recommended divisor: {winner}** — clears all 4 acceptance "
            f"criteria. Tie-break: transitional rate closest to the midpoint "
            f"of the ADR §6.4 [10, 30]% target band (20%)."
        )
    else:
        add(
            f"**No divisor clears all 4 criteria cleanly. Closest-to-passing: "
            f"{winner}** — {best['criteria_pass_count']}/4 criteria, "
            f"transitional rate {fmt_pct(best['agg_trans_pct'])}. Selection "
            f"minimises total miss magnitude across failed criteria (per-instrument "
            f"severity, not just binary pass/fail). See §4.1 for details."
        )
        # Also report the miss severities for transparency.
        add("")
        add("Per-divisor miss severity ranking (lower = closer to passing):")
        add("")
        add("| Divisor | Pass count | Miss severity |")
        add("|---------|------------|---------------|")
        ranked = sorted(rows, key=lambda r: (-r["criteria_pass_count"], _miss_severity(r)))
        for r in ranked:
            add(f"| {r['divisor']} | {r['criteria_pass_count']}/4 | {_miss_severity(r):.2f} |")
    add("")

    # Recommendation summary
    add("### 5.1 Winning-divisor metrics")
    add("")
    win_row = next(r for r in rows if r["divisor"] == winner)
    add(f"- **Aggregate bullish / bearish / transitional:** "
        f"{fmt_pct(win_row['agg_bull_pct'])} / "
        f"{fmt_pct(win_row['agg_bear_pct'])} / "
        f"{fmt_pct(win_row['agg_trans_pct'])} "
        f"(symmetry gap {fmt_pct(win_row['symmetry_gap'])})")
    add("- **Per-instrument OB preservation ratio:**")
    for sym in symbols:
        ratio = win_row["ob_ratio_per_sym"][sym]
        flag = "" if ratio > 0.70 else " **(below 70%)**"
        add(f"  - {sym}: {fmt_ratio(ratio)}{flag}")
    add("- **Per-instrument transitional rate:**")
    for sym in symbols:
        t = win_row["trans_per_sym"][sym]
        flag = "" if 10.0 <= t <= 30.0 else " **(outside [10,30]%)**"
        add(f"  - {sym}: {fmt_pct(t)}{flag}")
    add("- **Per-instrument max(bullish%, bearish%):**")
    for sym in symbols:
        m = win_row["max_dir_per_sym"][sym]
        flag = "" if m < 60.0 else " **(>= 60%)**"
        add(f"  - {sym}: {fmt_pct(m)}{flag}")
    add("")

    # --- Pathologies section ---
    add("### 5.2 Per-instrument pathologies and caveats")
    add("")
    for sym in symbols:
        v1 = v1_by_sym[sym]
        # How does this instrument behave across all divisors?
        notes = []
        v1_bull = _label_pct(v1, "bullish")
        v1_bear = _label_pct(v1, "bearish")
        notes.append(
            f"v1: bull {fmt_pct(v1_bull)} / bear {fmt_pct(v1_bear)} "
            f"(v1 known 100%-bullish bug surface)."
        )
        # v2 behaviour across divisors
        v2_range_trans = []
        v2_range_bull = []
        v2_range_bear = []
        v2_range_ratio = []
        for d in divisors:
            s = v2_by_sym_by_d[d][sym]
            v2_range_trans.append(_label_pct(s, "transitional"))
            v2_range_bull.append(_label_pct(s, "bullish"))
            v2_range_bear.append(_label_pct(s, "bearish"))
            v1_tot = v1.total_obs or 1
            v2_range_ratio.append(s.total_obs / v1_tot)
        notes.append(
            f"v2 across divisors {list(divisors)}: "
            f"trans {[f'{x:.0f}%' for x in v2_range_trans]}; "
            f"bull {[f'{x:.0f}%' for x in v2_range_bull]}; "
            f"bear {[f'{x:.0f}%' for x in v2_range_bear]}; "
            f"OB ratio {[f'{r:.2f}' for r in v2_range_ratio]}."
        )
        worst_ratio = min(v2_range_ratio)
        if worst_ratio < 0.70:
            notes.append(
                f"**OB supply preservation worst case {fmt_ratio(worst_ratio)} "
                f"at divisor {divisors[v2_range_ratio.index(worst_ratio)]} — "
                f"below 70% target.**"
            )
        add(f"- **{sym}**: " + " ".join(notes))
    add("")

    # --- Proposed code change ---
    add("## 6. Proposed code change")
    add("")
    add(
        f"If CEO approves promotion of divisor ``{winner}``, the one-line "
        f"change in ``src/components/market_state.py`` is:"
    )
    add("")
    add("```python")
    add(f"def identify_structure_v2(")
    add(f"    swings: list[Swing],")
    add(f"    dead_zone_divisor: int = {winner},   # <-- change default from 4 to {winner}")
    add(f") -> StructureAnalysis:")
    add("```")
    add("")
    add(
        f"All existing callers (unit tests, F2.3 shadow logger, F3 backtest) "
        f"remain unchanged — they pass no divisor argument so the new default "
        f"(``{winner}``) takes effect at the function boundary. The F2.3 "
        f"shadow logger then starts accumulating evidence under the tighter "
        f"dead zone before any production cutover."
    )
    add("")
    if not all_pass_rows:
        add(
            f"**Caveat:** recommended divisor {winner} does NOT clear all 4 "
            f"criteria. See §4.1 for which instruments fail which criterion. "
            f"Before committing the default-change, consider whether a "
            f"per-instrument ``dead_zone_divisor`` map is warranted."
        )
        add("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        default="research/archive/root_legacy_artifacts_2026_05_31/generated/wave2_f2/WAVE2_F2_SWEEP_REPORT.md",
        help="Output markdown path (default: legacy archive generated report)",
    )
    p.add_argument("--start", default="2026-01-02",
                   help="Start date YYYY-MM-DD (default 2026-01-02)")
    p.add_argument("--end", default="2026-04-13",
                   help="End date YYYY-MM-DD (default 2026-04-13)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc) if args.start else None
    end = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc) if args.end else None
    # Inclusive end: shift to 23:59:59 of chosen date so the final H1 bar lands inside.
    if end is not None:
        end = end.replace(hour=23, minute=59, second=59)

    v1_by_sym: dict[str, V1Stats] = {}
    v2_by_sym_by_d: dict[int, dict[str, WindowStats]] = {d: {} for d in DIVISORS}
    bar_counts: dict[str, int] = {}
    window_counts: dict[str, int] = {}

    for sym in SYMBOLS:
        bars = load_h1(sym, start, end)
        bar_counts[sym] = len(bars)
        if not bars:
            print(f"[sweep] {sym}: no bars in range — skipping", file=sys.stderr)
            v1_by_sym[sym] = V1Stats()
            for d in DIVISORS:
                v2_by_sym_by_d[d][sym] = WindowStats()
            window_counts[sym] = 0
            continue

        print(f"[sweep] {sym}: {len(bars):,} bars loaded", file=sys.stderr)
        v1, v2_map = sweep_instrument(sym, bars, DIVISORS)
        v1_by_sym[sym] = v1
        for d in DIVISORS:
            v2_by_sym_by_d[d][sym] = v2_map[d]
        window_counts[sym] = v1.windows
        print(
            f"[sweep] {sym}: {v1.windows} windows evaluated; "
            f"v1 labels {dict(v1.labels)}; v1 OBs {v1.total_obs}",
            file=sys.stderr,
        )

    report = build_report(
        v1_by_sym=v1_by_sym,
        v2_by_sym_by_d=v2_by_sym_by_d,
        divisors=DIVISORS,
        symbols=SYMBOLS,
        start=start,
        end=end,
        bar_counts=bar_counts,
        window_counts=window_counts,
    )

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = _REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"[sweep] wrote report to {out_path}", file=sys.stderr)

    # Also emit a terse scoreboard to stdout for quick reading.
    print("\nAcceptance scoreboard:")
    for d in DIVISORS:
        row = acceptance_row(d, v2_by_sym_by_d[d], v1_by_sym)
        print(
            f"  divisor={d}: bull {row['agg_bull_pct']:.1f}% / "
            f"bear {row['agg_bear_pct']:.1f}% / "
            f"trans {row['agg_trans_pct']:.1f}% -- "
            f"symm {'PASS' if row['symmetry_pass'] else 'FAIL'} "
            f"trans {'PASS' if row['trans_pass'] else 'FAIL'} "
            f"ob {'PASS' if row['ob_pass'] else 'FAIL'} "
            f"dir {'PASS' if row['dir_pass'] else 'FAIL'} "
            f"= {row['criteria_pass_count']}/4"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
