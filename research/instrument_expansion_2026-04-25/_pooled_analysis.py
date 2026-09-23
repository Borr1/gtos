"""Pooled cross-instrument tests + cluster + regime analysis."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

OUT = Path(__file__).parent
with open(OUT / "02_results.json") as f:
    DATA = json.load(f)


def asset_class(s):
    if s in {"XAUUSD", "XAGUSD"}: return "METALS"
    if s in {"BTCUSD", "ETHUSD"}: return "CRYPTO"
    if s in {"GER40", "JP225", "NAS100", "SPX500", "UK100", "US30_cash"}: return "INDEX"
    if s in {"UKOIL_cash", "USOIL_cash"}: return "ENERGY"
    return "FX"


def jpy_or_not(s):
    return "JPY" if "JPY" in s else "non-JPY"


def usd_pair(s):
    if s in ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD", "USDJPY"):
        if s.startswith("USD"):
            return "USD_base"
        return "USD_quote"
    return "non-FX-USD"


# -------- 1. Cross-instrument pooled H1 vs H2 BOS WR test ---------
rows_pooled = []
for r in DATA:
    h = r["h1h2"].get("h1_bos_retest_wr", {})
    h1n = h.get("h1_n", 0)
    h2n = h.get("h2_n", 0)
    h1wr = h.get("h1_mean", float("nan"))
    h2wr = h.get("h2_mean", float("nan"))
    if h1n < 10 or h2n < 10:
        continue
    h1w = int(round(h1wr * h1n))
    h2w = int(round(h2wr * h2n))
    rows_pooled.append({
        "symbol": r["symbol"],
        "asset_class": asset_class(r["symbol"]),
        "h1_n": h1n, "h1_wins": h1w, "h1_wr": h1wr,
        "h2_n": h2n, "h2_wins": h2w, "h2_wr": h2wr,
        "delta": h2wr - h1wr,
        "data_quality": "FULL" if r["monthly"].get("2026-04", {}).get("m15_candle_count", 0) >= 1500 else "PARTIAL",
    })
df_p = pd.DataFrame(rows_pooled)

# Pooled across all FULL-data instruments
full = df_p[df_p["data_quality"] == "FULL"]
pooled_h1_n = full["h1_n"].sum()
pooled_h1_w = full["h1_wins"].sum()
pooled_h2_n = full["h2_n"].sum()
pooled_h2_w = full["h2_wins"].sum()
p1 = pooled_h1_w / pooled_h1_n
p2 = pooled_h2_w / pooled_h2_n
p_pool = (pooled_h1_w + pooled_h2_w) / (pooled_h1_n + pooled_h2_n)
se = np.sqrt(p_pool * (1 - p_pool) * (1 / pooled_h1_n + 1 / pooled_h2_n))
z = (p1 - p2) / se
p_val = 2 * (1 - stats.norm.cdf(abs(z)))
print(f"=== POOLED CROSS-INSTRUMENT H1 vs H2 BOS retest WR (FULL data only, {len(full)} instruments) ===")
print(f"  H1: {pooled_h1_w}/{pooled_h1_n} = {p1:.4f}")
print(f"  H2: {pooled_h2_w}/{pooled_h2_n} = {p2:.4f}")
print(f"  Delta: {p2 - p1:+.4f} ({(p2-p1)*100:+.2f}pp)")
print(f"  Two-prop z = {z:.3f}, p = {p_val:.4f}")

# Pool by asset class
print("\n=== Per asset class (FULL data) ===")
for ac, g in full.groupby("asset_class"):
    h1n = g["h1_n"].sum(); h1w = g["h1_wins"].sum()
    h2n = g["h2_n"].sum(); h2w = g["h2_wins"].sum()
    p1 = h1w / h1n if h1n else float("nan")
    p2 = h2w / h2n if h2n else float("nan")
    if h1n > 5 and h2n > 5:
        p_pool_ac = (h1w + h2w) / (h1n + h2n)
        se_ac = np.sqrt(p_pool_ac * (1 - p_pool_ac) * (1 / h1n + 1 / h2n))
        z_ac = (p1 - p2) / se_ac if se_ac else float("nan")
        p_val_ac = 2 * (1 - stats.norm.cdf(abs(z_ac))) if np.isfinite(z_ac) else float("nan")
        print(f"  {ac:8s} n={len(g):2d}  H1={p1:.3f} (n={h1n})  H2={p2:.3f} (n={h2n})  delta={p2-p1:+.3f}  p={p_val_ac:.3f}")
    else:
        print(f"  {ac:8s} n={len(g):2d}  insufficient data")

# JPY pairs vs non-JPY
print("\n=== FX: JPY pairs vs non-JPY ===")
for label in ("JPY", "non-JPY"):
    g = df_p[(df_p["asset_class"] == "FX") & df_p["symbol"].apply(jpy_or_not).eq(label) & (df_p["data_quality"] == "FULL")]
    if len(g) == 0: continue
    h1n = g["h1_n"].sum(); h1w = g["h1_wins"].sum()
    h2n = g["h2_n"].sum(); h2w = g["h2_wins"].sum()
    p1 = h1w / h1n; p2 = h2w / h2n
    p_pool_l = (h1w + h2w) / (h1n + h2n)
    se_l = np.sqrt(p_pool_l * (1 - p_pool_l) * (1 / h1n + 1 / h2n))
    z_l = (p1 - p2) / se_l if se_l else float("nan")
    p_val_l = 2 * (1 - stats.norm.cdf(abs(z_l))) if np.isfinite(z_l) else float("nan")
    print(f"  {label:8s} n={len(g):2d}  H1={p1:.3f} (n={h1n})  H2={p2:.3f} (n={h2n})  delta={p2-p1:+.3f}  p={p_val_l:.3f}")

# -------- 2. Bonferroni / FDR correction for per-instrument tests --------
print("\n=== Per-instrument H1 vs H2 BOS WR (Bonferroni N=24) ===")
all_p = []
for r in DATA:
    h = r["h1h2"].get("h1_bos_retest_wr", {})
    p_v = h.get("p_value")
    if p_v is None or not np.isfinite(p_v):
        continue
    all_p.append((r["symbol"], h.get("delta", 0.0), p_v, h.get("h1_n", 0) + h.get("h2_n", 0)))
all_p_sorted = sorted(all_p, key=lambda x: x[2])
N = len(all_p_sorted)
alpha = 0.05
print(f"  Bonferroni threshold: {alpha/N:.4f} (alpha=0.05, N={N} tests)")
for sym, dlt, p, n in all_p_sorted[:8]:
    sig_b = "***" if p < alpha / N else ("*" if p < 0.05 else "")
    print(f"  {sym:12s} delta={dlt:+.3f} (n={n:3d}) p={p:.4f} {sig_b}")

# Benjamini-Hochberg FDR
print("\n  Benjamini-Hochberg FDR (q=0.10):")
qval = 0.10
m = N
for rank, (sym, dlt, p, n) in enumerate(all_p_sorted, 1):
    threshold = (rank / m) * qval
    sig_bh = "<<" if p <= threshold else ""
    if rank <= 6:
        print(f"  rank {rank:2d}  {sym:12s} p={p:.4f}  threshold={threshold:.4f}  {sig_bh}")

# -------- 3. Cross-instrument vol regime / DXY context --------
print("\n=== Volatility regime: ATR-M15 H1->H2 % change ===")
rows_v = []
for r in DATA:
    atr_h = r["h1h2"].get("atr_m15", {})
    h1m = atr_h.get("h1_mean", float("nan"))
    h2m = atr_h.get("h2_mean", float("nan"))
    if not (np.isfinite(h1m) and np.isfinite(h2m) and h1m > 0):
        continue
    rows_v.append({
        "symbol": r["symbol"],
        "asset_class": asset_class(r["symbol"]),
        "atr_h1": h1m, "atr_h2": h2m,
        "atr_pct_change": (h2m - h1m) / h1m,
    })
dfv = pd.DataFrame(rows_v).sort_values("atr_pct_change")
print(dfv.to_string(index=False))
print(f"\n  Median atr % change H1->H2: {dfv['atr_pct_change'].median():+.3f}")
print(f"  Mean   atr % change H1->H2: {dfv['atr_pct_change'].mean():+.3f}")

# -------- 4. Save pooled results ----------
df_p.to_csv(OUT / "02_pooled_h1h2.csv", index=False)
print(f"\n  -> {OUT / '02_pooled_h1h2.csv'}")
