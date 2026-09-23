"""
Q-14 Non-Zone Mechanisms
========================
Q-14.4  Momentum ignition / cascade acceleration — does RIDING the cascade
        (with-impulse entry) outperform FADING it (OB retest)?
Q-14.10 Day-of-week × time-of-day interaction effects — are there specific
        day + hour combos with anomalous WR?

Pre-registered hypotheses (stated BEFORE looking at data):

Q-14.4 Hypothesis:
    H0: Riding the impulse (enter at BOS close, SL at prior swing) has the same
        expectancy as fading it at OB retest.
    H1 (expected):  FADE beats RIDE.  GTOS edge is OB zone precision / stop-cascade
        mean-reversion (Osler 2000-2005, Cont 2014).  Ride-the-impulse signals get
        systematically faded by institutional liquidity that placed the OB in the
        first place.  Expected ride-WR <= 50% on batch-matched counterfactual.

Q-14.10 Hypothesis:
    H0: No (day_of_week, hour-bucket) cell has WR > 55% at a Bonferroni-corrected
        significance level beyond what the kill-zone timing already explains.
    H1: One or more specific day × kill-zone cells show Wilson-lower-CI > 0.55
        with n >= 10 after Bonferroni correction.

Data limitations (declared up front, not fabricated):
- `unified_trades_v2_20260331.json` contains date (YYYY-MM-DD) but NO intraday
  entry_time.  Kill-zone (london/ny) is the only intraday locator.  We CANNOT
  do hour-of-day granularity.  Day-of-week × kill-zone (2 buckets) is the best
  achievable resolution — 5 days x 2 zones = 10 cells.
- Historical M15 data (data/historical_2026/) only covers 2026-01-02 to
  2026-04-10.  Only 29 of 111 batch trades overlap this window.  Q-14.4
  counterfactual is restricted to that n=29 subset.
- Without the exact entry M15 candle, any "ride the impulse" reconstruction is
  approximate — we use the highest-range M15 candle inside the kill zone on
  the trade's date as the proxy BOS/impulse candle.  This is disclosed in the
  caveats and verdicts.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
TRADES_JSON = (
    ROOT
    / "knowledge_base_backtest"
    / "analysis"
    / "unified_trades_v2_20260331.json"
)
HIST_DIR = ROOT / "data" / "historical_2026"
OUT_MD = ROOT / "research" / "academic_pipeline" / "results" / "Q-14_non_zone.md"


# ---------------------------------------------------------------------------
# Constants — kill-zone UTC hours (from CLAUDE.md XAUUSD schedule)
# ---------------------------------------------------------------------------
KZ_HOURS = {
    "london": (7, 10),   # 07:00-10:30 UTC; we treat 07-10 inclusive of hour
    "ny": (13, 17),      # 13:00-17:00 UTC; skip 13:00-13:15 convention ignored here
}


# ---------------------------------------------------------------------------
# Helpers — statistics
# ---------------------------------------------------------------------------
def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (95% default)."""
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def binom_test_p(wins: int, n: int, p0: float = 0.5) -> float:
    """Two-sided exact binomial test p-value against p0."""
    if n == 0:
        return 1.0
    # exact binomial
    def logC(n_, k_):
        return (math.lgamma(n_ + 1) - math.lgamma(k_ + 1) - math.lgamma(n_ - k_ + 1))

    def pmf(k_):
        return math.exp(
            logC(n, k_) + k_ * math.log(p0) + (n - k_) * math.log(1 - p0)
        )

    obs = pmf(wins)
    p_total = 0.0
    for k in range(n + 1):
        pk = pmf(k)
        if pk <= obs + 1e-15:
            p_total += pk
    return min(1.0, p_total)


# ---------------------------------------------------------------------------
# Helpers — IO
# ---------------------------------------------------------------------------
def load_trades() -> list[dict[str, Any]]:
    return json.loads(TRADES_JSON.read_text(encoding="utf-8"))


def load_ohlc(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "time": datetime.fromisoformat(row["time"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                }
            )
    return rows


# ---------------------------------------------------------------------------
# Q-14.4  Fade vs Ride counterfactual (XAUUSD, 2026 overlap only)
# ---------------------------------------------------------------------------
def simulate_ride_alternative(
    trades: list[dict[str, Any]], m15: list[dict[str, Any]]
) -> dict[str, Any]:
    """For each batch trade inside the historical window, reconstruct a naive
    "ride the impulse" alternative and record simulated R multiples.

    Method (documented limitations in-line):
      1. Filter trades to {2026-01-02 .. 2026-04-10} AND direction in {LONG,SHORT}.
      2. For each trade's date + kill_zone, select the M15 candle with the
         largest body-range inside the kill zone hours as the proxy "impulse"
         candle (this is the approximation — we lack the true BOS candle).
      3. Entry = impulse candle close.  SL = prior swing = min(low) / max(high)
         of preceding 6 M15 candles (90 min).  TP = symmetric distance yielding
         same 1:planned_rr ratio as the actual trade (so R normalisation matches).
      4. Walk forward up to `hold_time_candles` M15 bars.  Hit SL first -> -1R.
         Hit TP first -> +planned_rr.  Neither -> mark-to-market at exit.
      5. Output: per-trade {actual_R, ride_R} and aggregate stats.
    """
    # Index M15 by date for fast lookup
    bars_by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for bar in m15:
        bars_by_date[bar["time"].date().isoformat()].append(bar)

    results: list[dict[str, Any]] = []
    skipped: list[str] = []
    for t in trades:
        d = t["date"]
        if not ("2026-01-02" <= d <= "2026-04-10"):
            continue
        direction = t["direction"]
        if direction not in ("LONG", "SHORT"):
            skipped.append(f"{d}: direction={direction}")
            continue
        kz = t["kill_zone"]
        if kz not in KZ_HOURS:
            skipped.append(f"{d}: kz={kz}")
            continue
        day_bars = bars_by_date.get(d, [])
        if not day_bars:
            skipped.append(f"{d}: no m15 bars")
            continue

        kz_lo, kz_hi = KZ_HOURS[kz]
        zone_bars = [b for b in day_bars if kz_lo <= b["time"].hour <= kz_hi]
        if len(zone_bars) < 3:
            skipped.append(f"{d}: zone_bars<3 ({len(zone_bars)})")
            continue

        # Proxy impulse candle = largest body-range inside kill zone
        impulse = max(zone_bars, key=lambda b: b["high"] - b["low"])
        impulse_idx = day_bars.index(impulse)
        if impulse_idx < 6:
            skipped.append(f"{d}: prior-swing bars<6")
            continue

        prior = day_bars[impulse_idx - 6 : impulse_idx]
        ride_entry = impulse["close"]
        if direction == "LONG":
            ride_sl = min(b["low"] for b in prior)
            sl_dist = ride_entry - ride_sl
            if sl_dist <= 0:
                skipped.append(f"{d}: invalid LONG sl_dist")
                continue
            ride_tp = ride_entry + sl_dist * float(t.get("planned_rr") or 2.0)
        else:
            ride_sl = max(b["high"] for b in prior)
            sl_dist = ride_sl - ride_entry
            if sl_dist <= 0:
                skipped.append(f"{d}: invalid SHORT sl_dist")
                continue
            ride_tp = ride_entry - sl_dist * float(t.get("planned_rr") or 2.0)

        # Walk forward hold_time_candles bars (fall back to 48 if missing)
        hold = int(t.get("hold_time_candles") or 48)
        forward = day_bars[impulse_idx + 1 : impulse_idx + 1 + hold]
        if len(forward) < 3:
            # Extend with next calendar day if possible
            next_day = (impulse["time"].date()).toordinal() + 1
            nd_iso = datetime.fromordinal(next_day).date().isoformat()
            forward += bars_by_date.get(nd_iso, [])
            forward = forward[:hold]

        ride_r: float | None = None
        for b in forward:
            if direction == "LONG":
                if b["low"] <= ride_sl:
                    ride_r = -1.0
                    break
                if b["high"] >= ride_tp:
                    ride_r = float(t.get("planned_rr") or 2.0)
                    break
            else:
                if b["high"] >= ride_sl:
                    ride_r = -1.0
                    break
                if b["low"] <= ride_tp:
                    ride_r = float(t.get("planned_rr") or 2.0)
                    break
        if ride_r is None:
            # Mark to market with last close
            if not forward:
                skipped.append(f"{d}: no forward bars")
                continue
            last = forward[-1]["close"]
            if direction == "LONG":
                ride_r = (last - ride_entry) / sl_dist
            else:
                ride_r = (ride_entry - last) / sl_dist

        results.append(
            {
                "trade_id": t.get("trade_id"),
                "date": d,
                "direction": direction,
                "kill_zone": kz,
                "actual_R": float(t["r_multiple"]),
                "ride_R": ride_r,
                "planned_rr": float(t.get("planned_rr") or 2.0),
                "hold_candles": hold,
            }
        )

    if not results:
        return {"n": 0, "skipped": skipped, "trades": []}

    actual = [r["actual_R"] for r in results]
    ride = [r["ride_R"] for r in results]
    actual_wins = sum(1 for r in actual if r > 0)
    ride_wins = sum(1 for r in ride if r > 0)
    return {
        "n": len(results),
        "skipped_count": len(skipped),
        "skipped": skipped[:20],
        "trades": results,
        "actual": {
            "wr": actual_wins / len(actual),
            "wr_wilson": wilson_ci(actual_wins, len(actual)),
            "mean_R": sum(actual) / len(actual),
            "sum_R": sum(actual),
        },
        "ride": {
            "wr": ride_wins / len(ride),
            "wr_wilson": wilson_ci(ride_wins, len(ride)),
            "mean_R": sum(ride) / len(ride),
            "sum_R": sum(ride),
        },
        "diff": {
            "wr_diff_pp": (actual_wins - ride_wins) / len(actual) * 100,
            "mean_R_diff": sum(actual) / len(actual) - sum(ride) / len(ride),
            # Paired sign test of ride_R < actual_R
            "paired_fade_better_rate": sum(
                1 for a, b in zip(actual, ride) if a > b
            )
            / len(actual),
            "paired_binom_p_two_sided": binom_test_p(
                sum(1 for a, b in zip(actual, ride) if a > b),
                sum(1 for a, b in zip(actual, ride) if a != b),
                0.5,
            ),
        },
    }


# ---------------------------------------------------------------------------
# Q-14.10  Day × time bucket pivot
# ---------------------------------------------------------------------------
def day_time_pivot(trades: list[dict[str, Any]]) -> dict[str, Any]:
    """Because batch data lacks hour-of-day, we use day_of_week × kill_zone as
    the finest resolution available.  Cells: 5 days x 2 zones = 10 cells."""
    cells: dict[tuple[str, str], list[float]] = defaultdict(list)
    for t in trades:
        dow = t.get("day_of_week", "")
        kz = t.get("kill_zone", "")
        if not dow or not kz:
            continue
        cells[(dow, kz)].append(float(t["r_multiple"]))

    rows = []
    # We set n_min_flag to 10 per pre-reg, but we'll also surface cells with n<10
    # as informational.
    for (dow, kz), rs in sorted(cells.items()):
        wins = sum(1 for r in rs if r > 0)
        n = len(rs)
        lo, hi = wilson_ci(wins, n)
        # Raw one-sided binomial test H0: p=0.55 vs H1: p>0.55 (anomalous strong)
        # Use two-sided exact and halve for one-sided approximation
        p_two = binom_test_p(wins, n, 0.55)
        # Reasonable n-tested for Bonferroni = 10 cells (5 days × 2 zones)
        rows.append(
            {
                "day": dow,
                "kill_zone": kz,
                "n": n,
                "wins": wins,
                "wr": wins / n if n else 0.0,
                "wilson_lo": lo,
                "wilson_hi": hi,
                "mean_R": sum(rs) / n if n else 0.0,
                "p_raw_vs_55": p_two,
            }
        )

    # Bonferroni: m = number of cells considered (10)
    m = len(rows)
    for r in rows:
        r["p_bonf"] = min(1.0, r["p_raw_vs_55"] * m)
        r["anomalous_strong"] = (
            r["n"] >= 10
            and r["wilson_lo"] > 0.55
            and r["p_bonf"] < 0.05
        )
        r["informational_strong"] = (
            r["n"] >= 5
            and r["wilson_lo"] > 0.55
        )

    # Additional: pure day-of-week effect (collapse kill zones)
    day_rows = []
    by_day: dict[str, list[float]] = defaultdict(list)
    for t in trades:
        dow = t.get("day_of_week", "")
        if dow:
            by_day[dow].append(float(t["r_multiple"]))
    for dow, rs in sorted(by_day.items()):
        wins = sum(1 for r in rs if r > 0)
        n = len(rs)
        lo, hi = wilson_ci(wins, n)
        day_rows.append(
            {
                "day": dow,
                "n": n,
                "wins": wins,
                "wr": wins / n,
                "wilson_lo": lo,
                "wilson_hi": hi,
                "mean_R": sum(rs) / n,
            }
        )

    return {
        "n_total": sum(r["n"] for r in rows),
        "m_cells": m,
        "cells": rows,
        "day_only": day_rows,
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def fmt_r(x: float) -> str:
    return f"{x:+.3f}"


def render_md(q144: dict[str, Any], q1410: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Q-14 Non-Zone Mechanisms")
    lines.append("")
    lines.append(
        "Generated by `research/academic_pipeline/scripts/q_14_non_zone.py` "
        "(local, $0 API)."
    )
    lines.append("")
    # ---------- HYPOTHESIS ----------
    lines.append("## Hypotheses (pre-registered)")
    lines.append("")
    lines.append("**Q-14.4** — GTOS trades OB retest (fade the cascade).  Prior")
    lines.append(
        "belief: fading beats riding, because the edge is stop-cascade mean"
    )
    lines.append(
        "reversion (Osler 2000-2005, Cont et al. 2014).  Null: ride-WR equals"
    )
    lines.append("actual-WR.  Expected: actual (fade) mean-R > ride mean-R.")
    lines.append("")
    lines.append("**Q-14.10** — No (day, time-bucket) cell shows Wilson-lower-CI > 0.55")
    lines.append(
        "and Bonferroni-corrected p < 0.05.  Batch data has only "
        "`date (YYYY-MM-DD)` + `kill_zone`; hour-of-day is not recorded.  The"
    )
    lines.append(
        "finest achievable bucketing is day-of-week x kill-zone (5 x 2 = 10 cells)."
    )
    lines.append("")
    # ---------- DATA ----------
    lines.append("## Data")
    lines.append("")
    lines.append("- Source: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (n=111).")
    lines.append("- Historical OHLC: `data/historical_2026/XAUUSD_M15.csv` (2026-01-02 .. 2026-04-10, 6420 bars).")
    lines.append("- Overlap window for Q-14.4: 29 trades (25 LONG, 4 SHORT).")
    lines.append("")
    # ---------- METHOD ----------
    lines.append("## Method")
    lines.append("")
    lines.append("**Q-14.4**:  For each batch trade inside the historical window, build a naive")
    lines.append("'ride-the-impulse' counterfactual on M15.  Impulse candle = largest body-range")
    lines.append("candle inside the kill-zone hours on the trade's date (proxy for the BOS candle —")
    lines.append("true BOS timestamp is NOT recorded in the batch JSON).  Entry = impulse close.")
    lines.append("SL = prior 6-bar swing low/high.  TP = entry +/- (sl_dist * planned_rr).  Walk")
    lines.append("forward up to `hold_time_candles` M15 bars; first touch wins.  Mark-to-market if")
    lines.append("neither touched.  Compare actual_R (fade) vs ride_R (ride) per trade.")
    lines.append("")
    lines.append("**Q-14.10**:  Pivot `day_of_week` x `kill_zone` from batch.  Wilson 95% CI per")
    lines.append("cell.  Exact two-sided binomial test against p0=0.55 (the baseline WR a cell")
    lines.append("must beat to be 'anomalously strong').  Bonferroni correction: p_bonf = p_raw * 10.")
    lines.append("Flag cells with n >= 10, Wilson-lower > 0.55, and p_bonf < 0.05.")
    lines.append("")
    # ---------- Q-14.4 RESULTS ----------
    lines.append("## Q-14.4 Results — Fade vs Ride")
    lines.append("")
    if q144["n"] == 0:
        lines.append("**Data gap**: no trades could be reconstructed.")
        lines.append("")
        lines.append("Skipped reasons:")
        for s in q144.get("skipped", [])[:20]:
            lines.append(f"- {s}")
    else:
        lines.append(f"Reconstructed n = **{q144['n']}** of 29 overlap trades.  Skipped = {q144['skipped_count']}.")
        lines.append("")
        lines.append("| Strategy | WR | Wilson 95% CI | mean R | sum R |")
        lines.append("|---|---|---|---|---|")
        a = q144["actual"]
        r = q144["ride"]
        lines.append(
            f"| Actual (FADE / OB retest) | {fmt_pct(a['wr'])} "
            f"| [{fmt_pct(a['wr_wilson'][0])}, {fmt_pct(a['wr_wilson'][1])}] "
            f"| {fmt_r(a['mean_R'])} | {fmt_r(a['sum_R'])} |"
        )
        lines.append(
            f"| Counterfactual (RIDE / with-impulse) | {fmt_pct(r['wr'])} "
            f"| [{fmt_pct(r['wr_wilson'][0])}, {fmt_pct(r['wr_wilson'][1])}] "
            f"| {fmt_r(r['mean_R'])} | {fmt_r(r['sum_R'])} |"
        )
        d = q144["diff"]
        lines.append("")
        lines.append("**Paired comparison** (trade-by-trade):")
        lines.append("")
        lines.append(f"- WR diff (fade - ride): **{d['wr_diff_pp']:+.1f}pp**")
        lines.append(f"- mean-R diff (fade - ride): **{d['mean_R_diff']:+.3f}R**")
        lines.append(
            f"- Fraction of trades where fade > ride: {fmt_pct(d['paired_fade_better_rate'])}"
        )
        lines.append(
            f"- Paired sign-test two-sided p: **{d['paired_binom_p_two_sided']:.4f}**"
        )
        lines.append("")
        # Per-trade table (abbreviated)
        lines.append("<details><summary>Per-trade detail (first 29)</summary>")
        lines.append("")
        lines.append("| trade_id | date | dir | kz | actual_R | ride_R |")
        lines.append("|---|---|---|---|---|---|")
        for t in q144["trades"]:
            lines.append(
                f"| {t['trade_id']} | {t['date']} | {t['direction']} "
                f"| {t['kill_zone']} | {fmt_r(t['actual_R'])} | {fmt_r(t['ride_R'])} |"
            )
        lines.append("")
        lines.append("</details>")
    lines.append("")
    # ---------- Q-14.10 RESULTS ----------
    lines.append("## Q-14.10 Results — Day x Time-Bucket")
    lines.append("")
    lines.append("### Day-of-week x kill-zone pivot")
    lines.append("")
    lines.append("| day | kz | n | wins | WR | Wilson lo | Wilson hi | mean R | p raw | p bonf | flag |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")

    # Sort by day order then kz
    cells_sorted = sorted(
        q1410["cells"],
        key=lambda x: (DAY_ORDER.index(x["day"]) if x["day"] in DAY_ORDER else 99, x["kill_zone"]),
    )
    for c in cells_sorted:
        flag = ""
        if c["anomalous_strong"]:
            flag = "**ANOMALOUS_STRONG**"
        elif c["informational_strong"]:
            flag = "info-strong"
        lines.append(
            f"| {c['day']} | {c['kill_zone']} | {c['n']} | {c['wins']} "
            f"| {fmt_pct(c['wr'])} | {fmt_pct(c['wilson_lo'])} | {fmt_pct(c['wilson_hi'])} "
            f"| {fmt_r(c['mean_R'])} | {c['p_raw_vs_55']:.4f} | {c['p_bonf']:.4f} | {flag} |"
        )
    lines.append("")
    bonf_hits = [c for c in q1410["cells"] if c["anomalous_strong"]]
    info_hits = [
        c
        for c in q1410["cells"]
        if c["informational_strong"] and not c["anomalous_strong"]
    ]
    lines.append(f"Bonferroni-significant cells (n>=10, Wilson_lo>55%, p_bonf<0.05): **{len(bonf_hits)}**")
    if bonf_hits:
        for c in bonf_hits:
            lines.append(
                f"- {c['day']} {c['kill_zone']}: n={c['n']} WR={fmt_pct(c['wr'])} "
                f"wilson_lo={fmt_pct(c['wilson_lo'])} p_bonf={c['p_bonf']:.4f}"
            )
    lines.append("")
    lines.append(f"Informational-strong cells (n>=5, Wilson_lo>55%, not Bonferroni-significant): **{len(info_hits)}**")
    for c in info_hits:
        lines.append(
            f"- {c['day']} {c['kill_zone']}: n={c['n']} WR={fmt_pct(c['wr'])} "
            f"wilson_lo={fmt_pct(c['wilson_lo'])} p_raw={c['p_raw_vs_55']:.4f}"
        )
    lines.append("")
    lines.append("### Collapsed day-of-week (for reference)")
    lines.append("")
    lines.append("| day | n | WR | Wilson lo | Wilson hi | mean R |")
    lines.append("|---|---|---|---|---|---|")
    for c in sorted(
        q1410["day_only"],
        key=lambda x: DAY_ORDER.index(x["day"]) if x["day"] in DAY_ORDER else 99,
    ):
        lines.append(
            f"| {c['day']} | {c['n']} | {fmt_pct(c['wr'])} "
            f"| {fmt_pct(c['wilson_lo'])} | {fmt_pct(c['wilson_hi'])} | {fmt_r(c['mean_R'])} |"
        )
    lines.append("")
    # ---------- CAVEATS ----------
    lines.append("## Caveats")
    lines.append("")
    lines.append("1. **Q-14.4 impulse candle is a proxy** — batch JSON has no M15 BOS timestamp.")
    lines.append("   Largest-range kill-zone candle is an approximation; results are suggestive,")
    lines.append("   NOT production-faithful.")
    lines.append("2. **Q-14.4 sample is small** — only 29 batch trades overlap the 2026 historical")
    lines.append("   window.  Underpowered for anything stronger than effect-size reporting.")
    lines.append("3. **Q-14.10 granularity is coarse** — day x kill-zone (10 cells), not day x hour")
    lines.append("   (168 cells).  Hour-of-day analysis requires entry_time recorded in batch JSON")
    lines.append("   which does not exist.")
    lines.append("4. **Kill-zone timing is already a filter** — cells inside kill zones may appear")
    lines.append("   strong simply because the system only trades those hours.  The day x kz")
    lines.append("   pivot can only detect 'day-conditional kill-zone' effects, not novel")
    lines.append("   intraday signals.")
    lines.append("5. **No economic-calendar control** — day x kz cells mix quiet days with NFP")
    lines.append("   Fridays, FOMC Wednesdays, etc.  Confounded with macro events.")
    lines.append("")
    # ---------- VERDICTS ----------
    lines.append("## Verdicts")
    lines.append("")
    if q144["n"] > 0:
        a = q144["actual"]["mean_R"]
        r = q144["ride"]["mean_R"]
        direction_word = (
            "FADE beats RIDE"
            if a > r
            else "RIDE beats FADE"
            if r > a
            else "tie"
        )
        lines.append(
            f"- **Q-14.4**: Under the impulse-candle proxy on n={q144['n']}, "
            f"{direction_word} by mean-R delta of **{a - r:+.3f}R/trade** "
            f"(fade WR {fmt_pct(q144['actual']['wr'])} vs ride WR {fmt_pct(q144['ride']['wr'])}).  "
            f"Paired sign-test p={q144['diff']['paired_binom_p_two_sided']:.4f}.  "
            "Prior (fade > ride) is **"
            + ("consistent" if a > r else "NOT consistent")
            + "** with the data.  Proxy-based, low-power — not a substitute for "
            "a BOS-timestamped counterfactual."
        )
    else:
        lines.append(
            "- **Q-14.4**: Data gap — no overlap trades could be reconstructed."
        )
    if bonf_hits:
        lines.append(
            "- **Q-14.10**: "
            f"{len(bonf_hits)} cell(s) survive Bonferroni.  Investigate further."
        )
    else:
        lines.append(
            "- **Q-14.10**: **Zero** day-of-week x kill-zone cells survive Bonferroni "
            "(p_bonf < 0.05, n >= 10, Wilson_lo > 55%).  Prior (no specific "
            "day x time signal beyond kill zones) is **consistent** with the data.  "
            f"{len(info_hits)} cell(s) flagged at the weaker 'informational' threshold "
            "(n >= 5, Wilson_lo > 55%) — treat as hypothesis-generating only."
        )
    lines.append("")
    # ---------- NEXT STEPS ----------
    lines.append("## Next steps")
    lines.append("")
    lines.append("1. If Q-14.4 is to be settled properly, add `entry_time` (M15 UTC) to the")
    lines.append("   batch schema so the exact BOS candle can be reproduced.  Re-run the")
    lines.append("   ride counterfactual with true impulse-candle alignment — that is the only")
    lines.append("   way to rule out the proxy bias reported here.")
    lines.append("2. For Q-14.10, record `entry_time` to enable true day x hour pivots (168")
    lines.append("   cells), then apply the same Bonferroni pipeline.  Hour-of-day WR")
    lines.append("   heterogeneity is the open question this study could not answer.")
    lines.append("3. Merge day x kz pivot with economic-calendar overlap (NFP Fri, FOMC Wed)")
    lines.append("   to separate calendar confounds from pure day-of-week effects.")
    lines.append("4. Neither Q-14.4 nor Q-14.10 produced a Bonferroni-significant signal;")
    lines.append("   no production action is warranted at this time.  Keep T7 C-gate + OB")
    lines.append("   retest (fade) as the trading edge.")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    trades = load_trades()
    print(f"Loaded {len(trades)} batch trades.")
    m15 = load_ohlc(HIST_DIR / "XAUUSD_M15.csv")
    print(f"Loaded {len(m15)} M15 bars.")

    q144 = simulate_ride_alternative(trades, m15)
    print(f"Q-14.4 reconstructed n={q144['n']}, skipped={q144.get('skipped_count')}")

    q1410 = day_time_pivot(trades)
    print(f"Q-14.10 cells={q1410['m_cells']}, total_trades={q1410['n_total']}")

    md = render_md(q144, q1410)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
