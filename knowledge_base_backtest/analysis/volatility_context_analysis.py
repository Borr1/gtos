"""
Phase 4: Cross-Instrument and Volatility Context Analysis
==========================================================
Computes volatility metrics (ATR percentile, Asian range width, pre-KZ range)
for each trade and checks if they predict trade outcome.
Also checks cross-instrument direction alignment for GBPUSD vs XAUUSD.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path("/Users/borr/Documents/trading/gold-agent")
DATA = BASE / "data"
ANALYSIS = BASE / "knowledge_base_backtest" / "analysis"

# ──────────────────────────────────────────────────────────────────────
# 1. Load all data
# ──────────────────────────────────────────────────────────────────────

with open(ANALYSIS / "phase1_all_trades_merged.json") as f:
    gold_trades_raw = json.load(f)

with open(ANALYSIS / "system_deep_dive_data_20260403.json") as f:
    deep_dive = json.load(f)

with open(ANALYSIS / "gbpusd_batch_deep_analysis_data_20260403.json") as f:
    gbpusd_data = json.load(f)

gbpusd_trades_raw = gbpusd_data["corrected_trades"]

# Load market data
xau_d1 = pd.read_csv(DATA / "XAUUSD_D1.csv", parse_dates=["time"])
xau_m15 = pd.read_csv(DATA / "XAUUSD_M15.csv", parse_dates=["time"])
gbp_d1 = pd.read_csv(DATA / "GBPUSD_D1.csv", parse_dates=["time"])
gbp_m15 = pd.read_csv(DATA / "GBPUSD_M15.csv", parse_dates=["time"])

# Create date columns for easy lookup
xau_d1["date"] = xau_d1["time"].dt.date
gbp_d1["date"] = gbp_d1["time"].dt.date
xau_m15["date"] = xau_m15["time"].dt.date
gbp_m15["date"] = gbp_m15["time"].dt.date

# ──────────────────────────────────────────────────────────────────────
# 2. Compute D1 ATR for each day (14-period ATR)
# ──────────────────────────────────────────────────────────────────────

def compute_atr(df_d1, period=14):
    """Compute ATR and return dataframe with date, atr, atr_percentile."""
    df = df_d1.copy().sort_values("time").reset_index(drop=True)
    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            abs(df["high"] - df["close"].shift(1)),
            abs(df["low"] - df["close"].shift(1))
        )
    )
    df["atr"] = df["tr"].rolling(period).mean()
    # Rolling percentile: where is today's ATR relative to last 60 days
    df["atr_pct"] = df["atr"].rolling(60).apply(
        lambda x: (x.iloc[-1] <= x).sum() / len(x) * 100 if len(x) == 60 else np.nan,
        raw=False
    )
    return df[["date", "atr", "atr_pct", "high", "low", "open", "close"]].dropna()

xau_atr = compute_atr(xau_d1)
gbp_atr = compute_atr(gbp_d1)

# Also compute 20-day ADR (Average Daily Range)
def compute_adr(df_d1, period=20):
    df = df_d1.copy().sort_values("time").reset_index(drop=True)
    df["daily_range"] = df["high"] - df["low"]
    df["adr"] = df["daily_range"].rolling(period).mean()
    return df[["date", "adr", "daily_range"]].dropna()

xau_adr = compute_adr(xau_d1)
gbp_adr = compute_adr(gbp_d1)

# ──────────────────────────────────────────────────────────────────────
# 3. Compute Asian range for each day
# ──────────────────────────────────────────────────────────────────────
# Asian session: roughly 00:00-08:00 UTC (Tokyo/Sydney overlap)

def compute_asian_range(df_m15):
    """Get Asian session (00:00-08:00 UTC) high/low per day."""
    df = df_m15.copy()
    df["hour"] = df["time"].dt.hour
    asian = df[(df["hour"] >= 0) & (df["hour"] < 8)].copy()
    asian_range = asian.groupby("date").agg(
        asian_high=("high", "max"),
        asian_low=("low", "min")
    ).reset_index()
    asian_range["asian_width"] = asian_range["asian_high"] - asian_range["asian_low"]
    return asian_range

xau_asian = compute_asian_range(xau_m15)
gbp_asian = compute_asian_range(gbp_m15)

# ──────────────────────────────────────────────────────────────────────
# 4. Compute pre-KZ range (from day open to KZ start)
# ──────────────────────────────────────────────────────────────────────
# London KZ: 07:00-10:00 UTC -> pre-KZ = 00:00-07:00
# NY KZ: 12:00-15:00 UTC -> pre-KZ = 00:00-12:00

def compute_pre_kz_range(df_m15, kz_start_hour):
    """Get price range from day open (00:00) to KZ start."""
    df = df_m15.copy()
    df["hour"] = df["time"].dt.hour
    pre_kz = df[(df["hour"] >= 0) & (df["hour"] < kz_start_hour)].copy()
    pre_kz_range = pre_kz.groupby("date").agg(
        pre_kz_high=("high", "max"),
        pre_kz_low=("low", "min"),
        day_open=("open", "first")
    ).reset_index()
    pre_kz_range["pre_kz_width"] = pre_kz_range["pre_kz_high"] - pre_kz_range["pre_kz_low"]
    return pre_kz_range

# We'll compute both and pick based on KZ
xau_pre_kz_london = compute_pre_kz_range(xau_m15, 7)
xau_pre_kz_ny = compute_pre_kz_range(xau_m15, 12)
gbp_pre_kz_london = compute_pre_kz_range(gbp_m15, 7)
gbp_pre_kz_ny = compute_pre_kz_range(gbp_m15, 12)

# ──────────────────────────────────────────────────────────────────────
# 5. D1 direction for cross-instrument analysis
# ──────────────────────────────────────────────────────────────────────

def compute_d1_direction(df_d1):
    """Simple D1 direction: bullish if close > prev close, bearish otherwise.
    Also check structure: higher high + higher low = bullish."""
    df = df_d1.copy().sort_values("time").reset_index(drop=True)
    df["prev_close"] = df["close"].shift(1)
    df["prev_high"] = df["high"].shift(1)
    df["prev_low"] = df["low"].shift(1)
    df["d1_dir_simple"] = np.where(df["close"] > df["prev_close"], "bullish", "bearish")
    # Structure-based: 3-day trend
    df["hh"] = df["high"] > df["prev_high"]
    df["hl"] = df["low"] > df["prev_low"]
    df["d1_structure"] = np.where(
        df["hh"] & df["hl"], "bullish",
        np.where(~df["hh"] & ~df["hl"], "bearish", "mixed")
    )
    return df[["date", "d1_dir_simple", "d1_structure", "close", "high", "low"]].dropna()

xau_d1_dir = compute_d1_direction(xau_d1)
gbp_d1_dir = compute_d1_direction(gbp_d1)

# ──────────────────────────────────────────────────────────────────────
# 6. Build unified trade table with volatility metrics
# ──────────────────────────────────────────────────────────────────────

def normalize_trade(trade, instrument):
    """Normalize trade dict to common format."""
    from datetime import date as dt_date
    if instrument == "XAUUSD":
        d = pd.to_datetime(trade["date"]).date()
        kz = trade.get("kill_zone", "ny").lower()
        outcome = trade.get("outcome", "")
        r = trade.get("r_multiple", 0)
        direction = trade.get("direction", "")
        return {
            "date": d,
            "kill_zone": kz,
            "instrument": instrument,
            "direction": direction,
            "outcome": outcome,
            "r_multiple": r,
            "is_win": outcome == "WIN",
            "entry_price": trade.get("entry_price"),
            "stop_loss": trade.get("stop_loss"),
        }
    else:  # GBPUSD
        d = pd.to_datetime(trade["date"]).date()
        kz = trade.get("kill_zone", "ny").lower()
        corrected_exit = trade.get("corrected_exit", "")
        corrected_r = trade.get("corrected_r", 0)
        is_win = corrected_exit == "CLOSED_TP1"
        r = corrected_r if is_win else (-1.0 if corrected_exit == "CLOSED_SL" else trade.get("batch_r", 0))
        direction = trade.get("direction", "")
        return {
            "date": d,
            "kill_zone": kz,
            "instrument": instrument,
            "direction": direction,
            "outcome": "WIN" if is_win else ("LOSS" if corrected_exit == "CLOSED_SL" else "TIMEOUT"),
            "r_multiple": r,
            "is_win": is_win,
            "entry_price": trade.get("entry_price"),
            "stop_loss": trade.get("stop_loss"),
        }

all_trades = []
for t in gold_trades_raw:
    all_trades.append(normalize_trade(t, "XAUUSD"))
for t in gbpusd_trades_raw:
    all_trades.append(normalize_trade(t, "GBPUSD"))

trades_df = pd.DataFrame(all_trades)
trades_df["date"] = pd.to_datetime(trades_df["date"]).dt.date

print(f"Total trades: {len(trades_df)} (XAUUSD: {len([t for t in all_trades if t['instrument']=='XAUUSD'])}, GBPUSD: {len([t for t in all_trades if t['instrument']=='GBPUSD'])})")

# ──────────────────────────────────────────────────────────────────────
# 7. Merge volatility metrics onto trades
# ──────────────────────────────────────────────────────────────────────

def merge_metrics(trades_df, atr_df, adr_df, asian_df, pre_kz_london_df, pre_kz_ny_df, instrument):
    """Merge volatility metrics for one instrument."""
    mask = trades_df["instrument"] == instrument
    sub = trades_df[mask].copy()

    # Convert date columns for merge
    for df in [atr_df, adr_df, asian_df, pre_kz_london_df, pre_kz_ny_df]:
        df["date"] = pd.to_datetime(df["date"]).dt.date if hasattr(df["date"].iloc[0], 'year') else df["date"]

    # Merge ATR
    sub = sub.merge(atr_df[["date", "atr", "atr_pct"]], on="date", how="left")
    # Merge ADR
    sub = sub.merge(adr_df[["date", "adr"]], on="date", how="left")
    # Merge Asian range
    sub = sub.merge(asian_df[["date", "asian_width"]], on="date", how="left")

    # Asian range normalized by ADR
    sub["asian_range_pct_adr"] = sub["asian_width"] / sub["adr"] * 100

    # Merge pre-KZ range based on kill zone
    london_merge = sub[sub["kill_zone"] == "london"].merge(
        pre_kz_london_df[["date", "pre_kz_width"]], on="date", how="left"
    )
    ny_merge = sub[sub["kill_zone"] == "ny"].merge(
        pre_kz_ny_df[["date", "pre_kz_width"]], on="date", how="left"
    )
    sub = pd.concat([london_merge, ny_merge], ignore_index=True)

    # pre-KZ range normalized by ADR
    sub["pre_kz_pct_adr"] = sub["pre_kz_width"] / sub["adr"] * 100

    return sub

xau_trades = merge_metrics(trades_df, xau_atr, xau_adr, xau_asian,
                           xau_pre_kz_london, xau_pre_kz_ny, "XAUUSD")
gbp_trades = merge_metrics(trades_df, gbp_atr, gbp_adr, gbp_asian,
                           gbp_pre_kz_london, gbp_pre_kz_ny, "GBPUSD")

enriched = pd.concat([xau_trades, gbp_trades], ignore_index=True)

print(f"\nEnriched trades: {len(enriched)}")
print(f"ATR available: {enriched['atr_pct'].notna().sum()}")
print(f"Asian range available: {enriched['asian_range_pct_adr'].notna().sum()}")
print(f"Pre-KZ range available: {enriched['pre_kz_pct_adr'].notna().sum()}")

# ──────────────────────────────────────────────────────────────────────
# 8. Quartile analysis: ATR percentile vs outcome
# ──────────────────────────────────────────────────────────────────────

def quartile_analysis(df, metric_col, metric_name, quartile_labels=None):
    """Bin a metric into quartiles and compute win rate / avg R per quartile."""
    valid = df[df[metric_col].notna()].copy()
    if len(valid) < 4:
        return {"status": "insufficient_data", "n": len(valid), "metric": metric_name}

    # Use fixed quartile boundaries
    if quartile_labels is None:
        quartile_labels = ["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"]

    try:
        valid["quartile"] = pd.qcut(valid[metric_col], 4, labels=quartile_labels, duplicates="drop")
    except ValueError:
        # Not enough unique values for 4 bins; try 2
        try:
            quartile_labels_2 = ["Low", "High"]
            valid["quartile"] = pd.qcut(valid[metric_col], 2, labels=quartile_labels_2, duplicates="drop")
        except ValueError:
            return {"status": "insufficient_unique_values", "n": len(valid), "metric": metric_name}

    results = {}
    for q in valid["quartile"].unique():
        qdata = valid[valid["quartile"] == q]
        n = len(qdata)
        wins = qdata["is_win"].sum()
        wr = wins / n * 100 if n > 0 else 0
        avg_r = qdata["r_multiple"].mean()
        results[str(q)] = {
            "n": int(n),
            "wins": int(wins),
            "win_rate": round(wr, 1),
            "avg_r": round(float(avg_r), 3),
            "metric_range": f"{qdata[metric_col].min():.1f} - {qdata[metric_col].max():.1f}"
        }

    # Compute spread
    wrs = [v["win_rate"] for v in results.values() if v["n"] >= 2]
    wr_spread = max(wrs) - min(wrs) if len(wrs) >= 2 else 0

    return {
        "status": "ok",
        "metric": metric_name,
        "total_trades": len(valid),
        "quartiles": results,
        "wr_spread": round(wr_spread, 1),
        "actionable": wr_spread > 10
    }

# ──────────────────────────────────────────────────────────────────────
# 8a. Combined analysis (all instruments)
# ──────────────────────────────────────────────────────────────────────

atr_result = quartile_analysis(enriched, "atr_pct", "ATR Percentile (60-day rolling)")
asian_result = quartile_analysis(enriched, "asian_range_pct_adr", "Asian Range Width (% of ADR)")
pre_kz_result = quartile_analysis(enriched, "pre_kz_pct_adr", "Pre-KZ Range (% of ADR)")

# ──────────────────────────────────────────────────────────────────────
# 8b. Per-instrument analysis
# ──────────────────────────────────────────────────────────────────────

per_instrument = {}
for inst in ["XAUUSD", "GBPUSD"]:
    sub = enriched[enriched["instrument"] == inst]
    per_instrument[inst] = {
        "atr": quartile_analysis(sub, "atr_pct", f"{inst} ATR Percentile"),
        "asian_range": quartile_analysis(sub, "asian_range_pct_adr", f"{inst} Asian Range"),
        "pre_kz": quartile_analysis(sub, "pre_kz_pct_adr", f"{inst} Pre-KZ Range"),
    }

# ──────────────────────────────────────────────────────────────────────
# 9. Cross-instrument direction alignment (GBPUSD trades vs XAUUSD D1)
# ──────────────────────────────────────────────────────────────────────

# For each GBPUSD trade date, check XAUUSD D1 direction
xau_dir_map = {row.date: row.d1_dir_simple for row in xau_d1_dir.itertuples()}
gbp_dir_map = {row.date: row.d1_dir_simple for row in gbp_d1_dir.itertuples()}

cross_instrument = []
for _, trade in gbp_trades.iterrows():
    d = trade["date"]
    xau_dir = xau_dir_map.get(d, None)
    trade_dir = "bullish" if trade["direction"] == "LONG" else "bearish"
    gbp_d1_direction = gbp_dir_map.get(d, None)

    if xau_dir is not None:
        aligned = (trade_dir == xau_dir)
        cross_instrument.append({
            "date": str(d),
            "trade_direction": trade_dir,
            "xau_d1_direction": xau_dir,
            "gbp_d1_direction": gbp_d1_direction,
            "aligned_with_xau": aligned,
            "is_win": trade["is_win"],
            "r_multiple": trade["r_multiple"],
        })

cross_df = pd.DataFrame(cross_instrument)
cross_result = {"status": "insufficient_data", "n": 0}

if len(cross_df) > 0:
    aligned = cross_df[cross_df["aligned_with_xau"] == True]
    not_aligned = cross_df[cross_df["aligned_with_xau"] == False]

    aligned_wr = aligned["is_win"].mean() * 100 if len(aligned) > 0 else 0
    not_aligned_wr = not_aligned["is_win"].mean() * 100 if len(not_aligned) > 0 else 0
    aligned_r = aligned["r_multiple"].mean() if len(aligned) > 0 else 0
    not_aligned_r = not_aligned["r_multiple"].mean() if len(not_aligned) > 0 else 0

    wr_diff = aligned_wr - not_aligned_wr

    cross_result = {
        "status": "ok",
        "description": "GBPUSD trade direction aligned with XAUUSD D1 direction",
        "total_trades": len(cross_df),
        "aligned": {
            "n": int(len(aligned)),
            "win_rate": round(aligned_wr, 1),
            "avg_r": round(float(aligned_r), 3),
        },
        "not_aligned": {
            "n": int(len(not_aligned)),
            "win_rate": round(not_aligned_wr, 1),
            "avg_r": round(float(not_aligned_r), 3),
        },
        "wr_difference": round(wr_diff, 1),
        "actionable": abs(wr_diff) > 10,
        "trade_details": cross_instrument[:10]  # sample
    }

# Also check XAUUSD trades vs GBPUSD D1 direction
cross_xau_instrument = []
for _, trade in xau_trades.iterrows():
    d = trade["date"]
    gbp_dir = gbp_dir_map.get(d, None)
    trade_dir = "bullish" if trade["direction"] == "LONG" else "bearish"

    if gbp_dir is not None:
        aligned = (trade_dir == gbp_dir)
        cross_xau_instrument.append({
            "date": str(d),
            "trade_direction": trade_dir,
            "gbp_d1_direction": gbp_dir,
            "aligned_with_gbp": aligned,
            "is_win": trade["is_win"],
            "r_multiple": trade["r_multiple"],
        })

cross_xau_df = pd.DataFrame(cross_xau_instrument)
cross_xau_result = {"status": "insufficient_data", "n": 0}

if len(cross_xau_df) > 0:
    aligned_x = cross_xau_df[cross_xau_df["aligned_with_gbp"] == True]
    not_aligned_x = cross_xau_df[cross_xau_df["aligned_with_gbp"] == False]

    aligned_wr_x = aligned_x["is_win"].mean() * 100 if len(aligned_x) > 0 else 0
    not_aligned_wr_x = not_aligned_x["is_win"].mean() * 100 if len(not_aligned_x) > 0 else 0
    aligned_r_x = aligned_x["r_multiple"].mean() if len(aligned_x) > 0 else 0
    not_aligned_r_x = not_aligned_x["r_multiple"].mean() if len(not_aligned_x) > 0 else 0

    wr_diff_x = aligned_wr_x - not_aligned_wr_x

    cross_xau_result = {
        "status": "ok",
        "description": "XAUUSD trade direction aligned with GBPUSD D1 direction",
        "total_trades": len(cross_xau_df),
        "aligned": {
            "n": int(len(aligned_x)),
            "win_rate": round(aligned_wr_x, 1),
            "avg_r": round(float(aligned_r_x), 3),
        },
        "not_aligned": {
            "n": int(len(not_aligned_x)),
            "win_rate": round(not_aligned_wr_x, 1),
            "avg_r": round(float(not_aligned_r_x), 3),
        },
        "wr_difference": round(wr_diff_x, 1),
        "actionable": abs(wr_diff_x) > 10,
    }

# ──────────────────────────────────────────────────────────────────────
# 10. Implementation decision
# ──────────────────────────────────────────────────────────────────────

actionable_signals = []
for name, result in [("atr_vs_outcome", atr_result),
                     ("asian_range_vs_outcome", asian_result),
                     ("pre_kz_range_vs_outcome", pre_kz_result)]:
    if isinstance(result, dict) and result.get("actionable"):
        actionable_signals.append(name)

if cross_result.get("actionable"):
    actionable_signals.append("cross_instrument_gbpusd_vs_xauusd")
if cross_xau_result.get("actionable"):
    actionable_signals.append("cross_instrument_xauusd_vs_gbpusd")

for inst, metrics in per_instrument.items():
    for metric_name, metric_result in metrics.items():
        if isinstance(metric_result, dict) and metric_result.get("actionable"):
            actionable_signals.append(f"{inst}_{metric_name}")

implementation_rec = "implement" if len(actionable_signals) > 0 else "null_result"

# ──────────────────────────────────────────────────────────────────────
# 11. Build output
# ──────────────────────────────────────────────────────────────────────

output = {
    "analysis_date": "2026-04-03",
    "data_sources": {
        "gold_trades": len(gold_trades_raw),
        "gbpusd_trades": len(gbpusd_trades_raw),
        "total_enriched_trades": len(enriched),
        "xauusd_d1_bars": len(xau_d1),
        "gbpusd_d1_bars": len(gbp_d1),
    },
    "atr_vs_outcome": {
        "combined": atr_result,
        "per_instrument": {k: v["atr"] for k, v in per_instrument.items()},
    },
    "asian_range_vs_outcome": {
        "combined": asian_result,
        "per_instrument": {k: v["asian_range"] for k, v in per_instrument.items()},
    },
    "pre_kz_range_vs_outcome": {
        "combined": pre_kz_result,
        "per_instrument": {k: v["pre_kz"] for k, v in per_instrument.items()},
    },
    "cross_instrument_vs_outcome": {
        "gbpusd_trades_vs_xauusd_d1": cross_result,
        "xauusd_trades_vs_gbpusd_d1": cross_xau_result,
    },
    "actionable_signals": actionable_signals,
    "implementation_recommendation": implementation_rec,
    "methodology": {
        "atr": "14-period ATR, percentile rank over 60-day rolling window",
        "asian_range": "Asian session (00:00-08:00 UTC) high-low, normalized by 20-day ADR",
        "pre_kz_range": "Range from day open to KZ start (07:00 for London, 12:00 for NY), normalized by 20-day ADR",
        "cross_instrument": "D1 close vs previous close direction; aligned = trade direction matches cross-instrument D1 direction",
        "actionable_threshold": ">10% win rate difference between best and worst quartile/group",
    },
}

# ──────────────────────────────────────────────────────────────────────
# 12. Print summary
# ──────────────────────────────────────────────────────────────────────

print("\n" + "="*70)
print("PHASE 4: VOLATILITY & CROSS-INSTRUMENT CONTEXT RESULTS")
print("="*70)

print(f"\nTrades analyzed: {len(enriched)} ({len(xau_trades)} XAUUSD, {len(gbp_trades)} GBPUSD)")

print("\n--- ATR PERCENTILE VS OUTCOME (COMBINED) ---")
if atr_result.get("status") == "ok":
    for q, v in atr_result["quartiles"].items():
        print(f"  {q:20s}  n={v['n']:3d}  WR={v['win_rate']:5.1f}%  Avg R={v['avg_r']:+.3f}  [{v['metric_range']}]")
    print(f"  WR spread: {atr_result['wr_spread']}%  {'** ACTIONABLE **' if atr_result['actionable'] else '(not actionable)'}")
else:
    print(f"  {atr_result}")

print("\n--- ASIAN RANGE VS OUTCOME (COMBINED) ---")
if asian_result.get("status") == "ok":
    for q, v in asian_result["quartiles"].items():
        print(f"  {q:20s}  n={v['n']:3d}  WR={v['win_rate']:5.1f}%  Avg R={v['avg_r']:+.3f}  [{v['metric_range']}]")
    print(f"  WR spread: {asian_result['wr_spread']}%  {'** ACTIONABLE **' if asian_result['actionable'] else '(not actionable)'}")
else:
    print(f"  {asian_result}")

print("\n--- PRE-KZ RANGE VS OUTCOME (COMBINED) ---")
if pre_kz_result.get("status") == "ok":
    for q, v in pre_kz_result["quartiles"].items():
        print(f"  {q:20s}  n={v['n']:3d}  WR={v['win_rate']:5.1f}%  Avg R={v['avg_r']:+.3f}  [{v['metric_range']}]")
    print(f"  WR spread: {pre_kz_result['wr_spread']}%  {'** ACTIONABLE **' if pre_kz_result['actionable'] else '(not actionable)'}")
else:
    print(f"  {pre_kz_result}")

print("\n--- CROSS-INSTRUMENT: GBPUSD vs XAUUSD D1 ---")
if cross_result.get("status") == "ok":
    a = cross_result["aligned"]
    na = cross_result["not_aligned"]
    print(f"  Aligned:      n={a['n']:3d}  WR={a['win_rate']:5.1f}%  Avg R={a['avg_r']:+.3f}")
    print(f"  Not aligned:  n={na['n']:3d}  WR={na['win_rate']:5.1f}%  Avg R={na['avg_r']:+.3f}")
    print(f"  WR diff: {cross_result['wr_difference']}%  {'** ACTIONABLE **' if cross_result['actionable'] else '(not actionable)'}")
else:
    print(f"  {cross_result}")

print("\n--- CROSS-INSTRUMENT: XAUUSD vs GBPUSD D1 ---")
if cross_xau_result.get("status") == "ok":
    a = cross_xau_result["aligned"]
    na = cross_xau_result["not_aligned"]
    print(f"  Aligned:      n={a['n']:3d}  WR={a['win_rate']:5.1f}%  Avg R={a['avg_r']:+.3f}")
    print(f"  Not aligned:  n={na['n']:3d}  WR={na['win_rate']:5.1f}%  Avg R={na['avg_r']:+.3f}")
    print(f"  WR diff: {cross_xau_result['wr_difference']}%  {'** ACTIONABLE **' if cross_xau_result['actionable'] else '(not actionable)'}")
else:
    print(f"  {cross_xau_result}")

# Per-instrument detail
for inst in ["XAUUSD", "GBPUSD"]:
    print(f"\n--- {inst} PER-INSTRUMENT DETAIL ---")
    for metric_name, result in per_instrument[inst].items():
        if result.get("status") == "ok":
            print(f"  {result['metric']}:")
            for q, v in result["quartiles"].items():
                print(f"    {q:20s}  n={v['n']:3d}  WR={v['win_rate']:5.1f}%  Avg R={v['avg_r']:+.3f}")
            print(f"    WR spread: {result['wr_spread']}%  {'** ACTIONABLE **' if result['actionable'] else ''}")
        else:
            print(f"  {metric_name}: {result.get('status', 'error')} (n={result.get('n', 0)})")

print(f"\n{'='*70}")
print(f"IMPLEMENTATION RECOMMENDATION: {implementation_rec.upper()}")
if actionable_signals:
    print(f"Actionable signals found: {actionable_signals}")
else:
    print("No metric showed >10% WR difference between best and worst group.")
print(f"{'='*70}")

# Save results
output_path = ANALYSIS / "volatility_context_results_20260403.json"
with open(output_path, "w") as f:
    json.dump(output, f, indent=2, default=str)
print(f"\nResults saved to: {output_path}")
