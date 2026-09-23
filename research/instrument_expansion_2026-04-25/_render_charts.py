"""Render M15 + H1 charts with structure markers for top candidates.

For each of the top ~15 candidates in 01_ranked_candidates.csv, save
a 2-panel chart (H1 above, M15 below) with:
  - Candle prices (matplotlib OHLC)
  - Identified swings (markers)
  - Order blocks (rectangles)
  - FVGs (rectangles, lighter color)
  - Structure events (vertical lines for BOS/CHoCH)

Save to research/instrument_expansion_2026-04-25/charts/{symbol}.png
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.historical_data_loader import parse_tradingview_csv
from src.components.market_state import (
    detect_swings,
    identify_structure,
    detect_structure_breaks,
    identify_order_blocks,
    identify_fvgs,
    calculate_atr,
)

OUT_DIR = PROJECT_ROOT / "research" / "instrument_expansion_2026-04-25"
DATA_DIR = PROJECT_ROOT / "data" / "historical_2026"
CHARTS_DIR = OUT_DIR / "charts"


def parse_iso(t: str) -> datetime:
    return datetime.fromisoformat(t.rstrip("Z"))


def render_chart(symbol: str, n_top: int) -> bool:
    """Render H1 + M15 chart with structure annotations."""
    try:
        candles_h1 = parse_tradingview_csv(DATA_DIR / f"{symbol}_H1.csv")
        candles_m15 = parse_tradingview_csv(DATA_DIR / f"{symbol}_M15.csv")
    except FileNotFoundError as e:
        print(f"[{symbol}] missing CSV: {e}", flush=True)
        return False

    if not candles_h1 or not candles_m15:
        return False

    # H1 series: take last ~600 candles for readability (~25 days)
    n_h1 = min(600, len(candles_h1))
    h1 = candles_h1[-n_h1:]
    h1_swings = detect_swings(h1, min_bars=2)
    h1_structure = identify_structure(h1_swings)
    h1_events = detect_structure_breaks(h1, h1_swings, h1_structure)
    h1_obs = identify_order_blocks(h1, h1_events)

    atr_h1 = calculate_atr(h1, 14)

    # M15 series: last ~480 candles (~5 days)
    n_m15 = min(480, len(candles_m15))
    m15 = candles_m15[-n_m15:]
    atr_m15 = calculate_atr(m15, 14)
    m15_swings = detect_swings(m15, min_bars=2)
    m15_fvgs = identify_fvgs(m15, min_gap_size=max(0.1 * atr_m15, 1e-6))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={"height_ratios": [3, 2]})

    # ── H1 panel ────────────────────────────────────────────────
    h1_times = [parse_iso(c["time"]) for c in h1]
    h1_x = mdates.date2num(h1_times)

    for i, c in enumerate(h1):
        color = "#2ecc71" if c["close"] >= c["open"] else "#e74c3c"
        ax1.plot([h1_x[i], h1_x[i]], [c["low"], c["high"]], color=color, linewidth=0.6, zorder=2)
        body_low = min(c["open"], c["close"])
        body_high = max(c["open"], c["close"])
        ax1.add_patch(mpatches.Rectangle(
            (h1_x[i] - 0.018, body_low),
            0.036, max(body_high - body_low, 1e-9),
            facecolor=color, edgecolor=color, alpha=0.85, zorder=3,
        ))

    # H1 swings
    for s in h1_swings[-30:]:
        if s.index >= len(h1):
            continue
        ts = parse_iso(h1[s.index]["time"])
        x = mdates.date2num(ts)
        marker = "v" if s.type == "high" else "^"
        color = "#c0392b" if s.type == "high" else "#27ae60"
        ax1.plot(x, s.price, marker=marker, color=color, markersize=8,
                 markeredgecolor="black", markeredgewidth=0.5, zorder=5)

    # H1 OBs (last 8)
    for ob in h1_obs[-8:]:
        if ob.formation_index >= len(h1):
            continue
        x_start = mdates.date2num(parse_iso(h1[ob.formation_index]["time"]))
        x_end = mdates.date2num(parse_iso(h1[-1]["time"]))
        color = "#3498db" if ob.type == "bullish" else "#e67e22"
        alpha = 0.15 if ob.mitigated else 0.30
        ax1.add_patch(mpatches.Rectangle(
            (x_start, ob.low), x_end - x_start, ob.high - ob.low,
            facecolor=color, alpha=alpha, edgecolor=color, linewidth=1, zorder=1,
        ))

    # H1 BOS/CHoCH
    for ev in h1_events[-15:]:
        if ev.candle_index >= len(h1):
            continue
        ts = parse_iso(h1[ev.candle_index]["time"])
        x = mdates.date2num(ts)
        color = "purple" if ev.type == "CHoCH" else "blue"
        linestyle = "--" if ev.type == "CHoCH" else ":"
        ax1.axvline(x, color=color, linestyle=linestyle, linewidth=0.8, alpha=0.7, zorder=2)

    ax1.set_title(f"{symbol} — H1 (last {n_h1} candles, ~{n_h1//24}d) | rank={n_top} | structure={h1_structure.direction}",
                  fontsize=13, fontweight="bold")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax1.grid(True, alpha=0.3)
    ax1.set_ylabel("Price")

    # Legend
    legend_h1 = [
        mpatches.Patch(color="#3498db", alpha=0.30, label="Unmitigated bullish OB"),
        mpatches.Patch(color="#e67e22", alpha=0.30, label="Unmitigated bearish OB"),
        mpatches.Patch(color="#3498db", alpha=0.15, label="Mitigated bullish OB"),
        plt.Line2D([0], [0], color="blue", linestyle=":", label="BOS"),
        plt.Line2D([0], [0], color="purple", linestyle="--", label="CHoCH"),
        plt.Line2D([0], [0], marker="v", color="#c0392b", linestyle="", label="Swing High"),
        plt.Line2D([0], [0], marker="^", color="#27ae60", linestyle="", label="Swing Low"),
    ]
    ax1.legend(handles=legend_h1, loc="upper left", fontsize=8, framealpha=0.85)

    # ── M15 panel ───────────────────────────────────────────────
    m15_times = [parse_iso(c["time"]) for c in m15]
    m15_x = mdates.date2num(m15_times)

    for i, c in enumerate(m15):
        color = "#2ecc71" if c["close"] >= c["open"] else "#e74c3c"
        ax2.plot([m15_x[i], m15_x[i]], [c["low"], c["high"]], color=color, linewidth=0.4, zorder=2)
        body_low = min(c["open"], c["close"])
        body_high = max(c["open"], c["close"])
        ax2.add_patch(mpatches.Rectangle(
            (m15_x[i] - 0.005, body_low),
            0.01, max(body_high - body_low, 1e-9),
            facecolor=color, edgecolor=color, alpha=0.85, zorder=3,
        ))

    # M15 unfilled FVGs (last 20)
    unfilled = [f for f in m15_fvgs if not f.filled][-20:]
    for fvg in unfilled:
        idx = max(fvg.candle_indices)
        if idx >= len(m15):
            continue
        x_start = mdates.date2num(parse_iso(m15[idx]["time"]))
        x_end = mdates.date2num(parse_iso(m15[-1]["time"]))
        color = "#9b59b6" if fvg.type == "bullish" else "#f39c12"
        ax2.add_patch(mpatches.Rectangle(
            (x_start, fvg.bottom), x_end - x_start, fvg.top - fvg.bottom,
            facecolor=color, alpha=0.18, edgecolor=color, linewidth=0.5, zorder=1,
        ))

    # M15 last 30 swings
    for s in m15_swings[-30:]:
        if s.index >= len(m15):
            continue
        ts = parse_iso(m15[s.index]["time"])
        x = mdates.date2num(ts)
        marker = "v" if s.type == "high" else "^"
        color = "#c0392b" if s.type == "high" else "#27ae60"
        ax2.plot(x, s.price, marker=marker, color=color, markersize=5,
                 markeredgecolor="black", markeredgewidth=0.3, zorder=5)

    ax2.set_title(f"{symbol} — M15 (last {n_m15} candles, ~{n_m15//(96)}d) | unfilled FVGs shown",
                  fontsize=11)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax2.grid(True, alpha=0.3)
    ax2.set_ylabel("Price")

    legend_m15 = [
        mpatches.Patch(color="#9b59b6", alpha=0.18, label="Unfilled bullish FVG"),
        mpatches.Patch(color="#f39c12", alpha=0.18, label="Unfilled bearish FVG"),
    ]
    ax2.legend(handles=legend_m15, loc="upper left", fontsize=8, framealpha=0.85)

    plt.tight_layout()
    out_path = CHARTS_DIR / f"{symbol}.png"
    plt.savefig(out_path, dpi=85, bbox_inches="tight")
    plt.close(fig)
    print(f"[{symbol}] chart saved -> {out_path.name}", flush=True)
    return True


def main():
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    # Read ranked candidates
    with open(OUT_DIR / "01_ranked_candidates.csv", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        ranked = list(rdr)

    # Top 15 + always include all 5 LIVE instruments
    LIVE = {"XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"}
    top15 = [r["symbol"] for r in ranked[:15]]
    chart_targets = list(top15)
    for live in LIVE:
        if live not in chart_targets:
            chart_targets.append(live)

    print(f"Rendering charts for {len(chart_targets)} symbols: {chart_targets}", flush=True)
    success = 0
    for i, sym in enumerate(chart_targets, 1):
        try:
            if render_chart(sym, i):
                success += 1
        except Exception as e:
            import traceback
            print(f"[{sym}] FAIL: {e}\n{traceback.format_exc()}", flush=True)

    print(f"\nDONE. {success}/{len(chart_targets)} charts saved to {CHARTS_DIR}", flush=True)


if __name__ == "__main__":
    main()
