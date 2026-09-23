"""
Q-14 Broad Mutual-Information Edge Discovery
============================================

Three research questions from research_execution_plan_113q.md:

- Q-14.13  Information-theoretic feature discovery (broad MI)
- Q-14.8   Trade flow imbalance from OHLCV (VPIN / BVC / tick rule)
- Q-14.2   Institutional algo footprints in OHLCV (iceberg / TWAP patterns)

All computation is local (no API). Historical data: data/historical_2026/*M15.csv
for 5 symbols (Jan 2 - Apr 10, 2026). Outcome linkage: unified_trades_v2_20260331.json
(2026 subset, n=29).

PRE-REGISTERED HYPOTHESES  (set BEFORE looking at results)
----------------------------------------------------------

H-14.8-1  VPIN_t (BVC-based, bucket=50 M15 candles) carries non-zero MI
          with sign(return_{t+k}) for k in {1,3,6,12} candles.
          Prior: weak signal (tick_volume is not true trade count).

H-14.8-2  At OB-trigger candles, trades initiated during high-VPIN
          windows (top tercile) win more often than low-VPIN.
          Prior: unknown; directionally plausible if toxicity drives mean-reversion.

H-14.2-1  Equal-close frequency (3+ consecutive candles with close within
          0.1 ATR) correlates positively with mean-reversion over k=3..12.
          Prior: weak signal (TWAP imprint).

H-14.2-2  Close-location-in-range asymmetry (|close - mid| / range) at the
          current candle carries MI with sign(return_{t+1}).
          Prior: no signal in random-walk baseline; weak signal in trending tape.

H-14.13-1 At least one of ~25 candle-shape features will clear the
          Bonferroni-corrected 99.83rd-percentile null (alpha=0.05 / 30 tests).
          Prior: at most 1-2 will clear by chance alone; a real edge would
          show multiple related features (e.g., wick asymmetry + body/range
          both for the same horizon).

H-14.13-2 The top-MI feature, if any, will be a volatility-regime variable
          (realized vol / ATR ratio), not a microstructure feature. Regime
          variables routinely show spurious MI with future returns because
          volatility clusters.

HONEST NULL EXPECTATION
-----------------------
On M15 retail-broker OHLCV (no true order flow, no level-II), prior academic
literature (Easley/O'Hara VPIN works on futures; BVC on tick data; algo
footprints need DOB) suggests all three questions will return weak or null
results. That IS the finding we're testing for.

Run: python research/academic_pipeline/scripts/q_14_broad_mi.py
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
DATA_DIR = ROOT / "data" / "historical_2026"
TRADES_FILE = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
OUT_DIR = ROOT / "research" / "academic_pipeline" / "results"
OUT_JSON = OUT_DIR / "Q-14_broad_mi_discovery.json"
OUT_MD = OUT_DIR / "Q-14_broad_mi_discovery.md"

SYMBOLS = {
    "XAUUSD": "XAUUSD_M15.csv",
    "US30": "US30_cash_M15.csv",
    "USDJPY": "USDJPY_M15.csv",
    "GBPJPY": "GBPJPY_M15.csv",
    "GBPUSD": "GBPUSD_M15.csv",
}

HORIZONS = [1, 3, 6, 12]            # M15 candles = 15min, 45min, 1.5h, 3h
VPIN_BUCKET = 50                     # Easley default
N_PERMUTATIONS = 500
SEED = 42
RNG = np.random.default_rng(SEED)


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def load_ohlcv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)
    # Some MT5 exports have 'volume' column holding tick_volume.
    # Check: treat as tick_volume by construction.
    if "volume" not in df.columns:
        raise RuntimeError(f"{path} missing volume column")
    return df


def rolling_std(returns: np.ndarray, window: int = 50) -> np.ndarray:
    """Rolling std with a min_periods=window/4 for early bars."""
    s = pd.Series(returns)
    return s.rolling(window, min_periods=max(5, window // 4)).std().to_numpy()


def norm_cdf(z: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))


# ------------------------------------------------------------------
# Feature engineering (~25 candle-shape + vol features)
# ------------------------------------------------------------------

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer candle-shape, microstructure, and volatility features.

    All features lag-safe: feature at t uses only info <= t.
    Target returns computed separately, then joined.
    """
    f = pd.DataFrame(index=df.index)
    o, h, l, c, v = df["open"].to_numpy(), df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy(), df["volume"].to_numpy()

    rng = h - l
    rng_safe = np.where(rng > 0, rng, np.nan)
    body = np.abs(c - o)
    upper_wick = h - np.maximum(c, o)
    lower_wick = np.minimum(c, o) - l
    mid = (h + l) / 2.0

    # Candle-shape
    f["body_over_range"] = body / rng_safe
    f["upper_wick_ratio"] = upper_wick / rng_safe
    f["lower_wick_ratio"] = lower_wick / rng_safe
    f["wick_asymmetry"] = (upper_wick - lower_wick) / rng_safe  # (+) = upper dominant
    f["close_loc_in_range"] = (c - l) / rng_safe                 # 0 = low, 1 = high
    f["abs_close_off_mid"] = np.abs(c - mid) / rng_safe          # 0.5 = extreme
    f["signed_body"] = (c - o) / rng_safe                        # (+) = bullish
    gap = (o - np.roll(c, 1)) / rng_safe
    gap[0] = np.nan
    f["gap_from_prior_close"] = gap

    # Range / volatility
    f["range"] = rng
    med_rng_20 = pd.Series(rng).rolling(20, min_periods=5).median().to_numpy()
    f["range_compression"] = rng / np.where(med_rng_20 > 0, med_rng_20, np.nan)
    # TR ATR
    prior_close = np.roll(c, 1)
    tr = np.maximum.reduce([h - l, np.abs(h - prior_close), np.abs(l - prior_close)])
    tr[0] = rng[0]
    atr14 = pd.Series(tr).rolling(14, min_periods=3).mean().to_numpy()
    f["atr14"] = atr14
    f["range_over_atr"] = rng / np.where(atr14 > 0, atr14, np.nan)

    # Returns and realized vol
    ret = np.log(c / prior_close)
    ret[0] = 0.0
    f["ret"] = ret
    f["abs_ret"] = np.abs(ret)
    rv20 = pd.Series(ret).rolling(20, min_periods=5).std().to_numpy()
    rv50 = pd.Series(ret).rolling(50, min_periods=10).std().to_numpy()
    f["rv20"] = rv20
    f["rv50"] = rv50
    f["vol_ratio"] = np.where(rv50 > 0, rv20 / rv50, np.nan)

    # Volume
    f["volume"] = v
    vol_med20 = pd.Series(v).rolling(20, min_periods=5).median().to_numpy()
    f["vol_ratio_20"] = v / np.where(vol_med20 > 0, vol_med20, np.nan)

    # -------- Q-14.8 VPIN (BVC) --------
    # buy_frac_t = N(ret_t / sigma_t), sell_frac_t = 1 - buy_frac_t
    sigma_local = rolling_std(ret, window=50)
    z = np.where(sigma_local > 0, ret / sigma_local, 0.0)
    buy_frac = norm_cdf(z)
    sell_frac = 1.0 - buy_frac
    buy_vol = buy_frac * v
    sell_vol = sell_frac * v

    # VPIN = rolling |BV-SV| / TV over bucket of 50 candles
    abs_diff = np.abs(buy_vol - sell_vol)
    total_vol = pd.Series(v).rolling(VPIN_BUCKET, min_periods=10).sum().to_numpy()
    abs_diff_sum = pd.Series(abs_diff).rolling(VPIN_BUCKET, min_periods=10).sum().to_numpy()
    vpin = np.where(total_vol > 0, abs_diff_sum / total_vol, np.nan)
    f["vpin"] = vpin

    # Tick-rule alternative (ignores buy_frac weighting; pure sign)
    tick_sign = np.sign(c - prior_close)
    tick_sign[0] = 0
    tick_imb = pd.Series(tick_sign * v).rolling(VPIN_BUCKET, min_periods=10).sum().to_numpy()
    tick_tot = pd.Series(np.abs(v)).rolling(VPIN_BUCKET, min_periods=10).sum().to_numpy()
    f["tick_imbalance"] = np.where(tick_tot > 0, tick_imb / tick_tot, np.nan)
    f["signed_tick_vol"] = tick_sign * v

    # -------- Q-14.2 Algo footprints --------
    # Equal-close frequency: 3+ consecutive candles with close within 0.1*ATR
    atr_thresh = 0.1 * atr14
    close_diff = np.abs(c - prior_close)
    is_equal = (close_diff < np.where(atr_thresh > 0, atr_thresh, np.inf)).astype(int)
    # rolling sum of 'is_equal' over 5 candles -> 3+ means TWAP-ish
    f["eq_close_5"] = pd.Series(is_equal).rolling(5, min_periods=1).sum().to_numpy()
    # equal-close streak length: count of consecutive 1s up to t
    streak = np.zeros(len(c), dtype=int)
    for i in range(len(c)):
        streak[i] = streak[i - 1] + 1 if (i > 0 and is_equal[i] == 1) else int(is_equal[i])
    f["eq_close_streak"] = streak
    # "Iceberg": hugely high volume but tiny range -> volume/range
    f["vol_per_range"] = v / np.where(rng > 0, rng, np.nan)
    vpr_med20 = pd.Series(f["vol_per_range"]).rolling(20, min_periods=5).median().to_numpy()
    f["vol_per_range_ratio"] = f["vol_per_range"] / np.where(vpr_med20 > 0, vpr_med20, np.nan)

    # Session-of-day one-hot (Asia/London/NY/overlap) -> numeric
    hh = df["time"].dt.hour
    session = np.select(
        [
            (hh >= 0) & (hh < 7),      # Asia
            (hh >= 7) & (hh < 12),     # London
            (hh >= 12) & (hh < 17),    # NY/overlap
        ],
        [0, 1, 2],
        default=3,
    )
    f["session_idx"] = session

    # Replace infinities with nan
    f = f.replace([np.inf, -np.inf], np.nan)
    return f


def build_targets(df: pd.DataFrame, horizons=HORIZONS) -> pd.DataFrame:
    """Future return targets (log-ret from close_t to close_{t+k})."""
    c = df["close"].to_numpy()
    out = pd.DataFrame(index=df.index)
    for k in horizons:
        fut = np.roll(c, -k)
        fut[-k:] = np.nan
        # log-return
        out[f"ret_fwd_{k}"] = np.log(fut / c)
        # signed binary (up vs not-up)
        out[f"dir_fwd_{k}"] = (fut > c).astype(float)
        out.loc[out.index[-k:], f"ret_fwd_{k}"] = np.nan
        out.loc[out.index[-k:], f"dir_fwd_{k}"] = np.nan
    return out


# ------------------------------------------------------------------
# MI estimation with permutation null
# ------------------------------------------------------------------

def mi_with_null(
    x: np.ndarray,
    y: np.ndarray,
    is_binary_y: bool,
    n_permutations: int = N_PERMUTATIONS,
    rng: np.random.Generator = RNG,
    bins: int = 10,
) -> Dict[str, float]:
    """Mutual information with permutation null.

    x: continuous feature (1D)
    y: target (binary or continuous). For continuous y, discretize via deciles.
    """
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    if len(x) < 50:
        return {"mi": np.nan, "null_95": np.nan, "null_99": np.nan, "null_mean": np.nan, "p_emp": np.nan, "n": int(len(x))}

    # Discretize feature x into deciles for robust MI (tree-based sklearn
    # mi_regression handles continuous but is noisy on small-n - we use bins).
    try:
        x_q = pd.qcut(x, q=bins, labels=False, duplicates="drop").astype(int)
    except ValueError:
        return {"mi": np.nan, "null_95": np.nan, "null_99": np.nan, "null_mean": np.nan, "p_emp": np.nan, "n": int(len(x))}

    if is_binary_y:
        y_cls = y.astype(int)
    else:
        try:
            y_cls = pd.qcut(y, q=bins, labels=False, duplicates="drop").astype(int)
        except ValueError:
            return {"mi": np.nan, "null_95": np.nan, "null_99": np.nan, "null_mean": np.nan, "p_emp": np.nan, "n": int(len(x))}

    mi_obs = mutual_info_classif(
        x_q.reshape(-1, 1), y_cls, discrete_features=True, random_state=SEED
    )[0]

    # Permutation null (shuffle y)
    nulls = np.empty(n_permutations, dtype=float)
    y_shuf = y_cls.copy()
    for i in range(n_permutations):
        rng.shuffle(y_shuf)
        nulls[i] = mutual_info_classif(
            x_q.reshape(-1, 1), y_shuf, discrete_features=True, random_state=SEED
        )[0]
    null_95 = float(np.percentile(nulls, 95))
    null_99 = float(np.percentile(nulls, 99))
    null_mean = float(nulls.mean())
    p_emp = float(np.mean(nulls >= mi_obs))
    return {
        "mi": float(mi_obs),
        "null_95": null_95,
        "null_99": null_99,
        "null_mean": null_mean,
        "p_emp": p_emp,
        "n": int(len(x)),
    }


# ------------------------------------------------------------------
# Main analysis
# ------------------------------------------------------------------

def analyze_symbol(symbol: str, csv_name: str, n_perm: int = N_PERMUTATIONS) -> Dict:
    path = DATA_DIR / csv_name
    df = load_ohlcv(path)
    feats = build_features(df)
    targs = build_targets(df)
    combined = pd.concat([df[["time", "close"]], feats, targs], axis=1)
    # Drop early rows where lags/vol are undefined
    combined = combined.iloc[60:-max(HORIZONS)].reset_index(drop=True)

    feat_cols = [c for c in feats.columns if c != "ret"]  # 'ret' is current-bar, keep for reference but not as feature
    results_by_feature: Dict[str, Dict[str, Dict[str, float]]] = {}

    for col in feat_cols:
        x = combined[col].to_numpy()
        per_h: Dict[str, Dict[str, float]] = {}
        for k in HORIZONS:
            # Regression-style (MI vs continuous forward return)
            y = combined[f"ret_fwd_{k}"].to_numpy()
            mi_r = mi_with_null(x, y, is_binary_y=False, n_permutations=n_perm)
            # Classification-style (MI vs direction)
            yb = combined[f"dir_fwd_{k}"].to_numpy()
            mi_c = mi_with_null(x, yb, is_binary_y=True, n_permutations=n_perm)
            per_h[f"k={k}"] = {
                "ret_mi": mi_r["mi"],
                "ret_null_95": mi_r["null_95"],
                "ret_null_99": mi_r["null_99"],
                "ret_p": mi_r["p_emp"],
                "dir_mi": mi_c["mi"],
                "dir_null_95": mi_c["null_95"],
                "dir_null_99": mi_c["null_99"],
                "dir_p": mi_c["p_emp"],
                "n": mi_r["n"],
            }
        results_by_feature[col] = per_h
    return {
        "symbol": symbol,
        "rows": len(combined),
        "first_bar": str(combined["time"].iloc[0]) if len(combined) else None,
        "last_bar": str(combined["time"].iloc[-1]) if len(combined) else None,
        "features": results_by_feature,
    }


# ------------------------------------------------------------------
# Outcome-linkage subgroup test (Q-14.8 H-14.8-2)
# ------------------------------------------------------------------

def load_trades_2026() -> List[Dict]:
    data = json.loads(TRADES_FILE.read_text(encoding="utf-8"))
    return [t for t in data if t.get("date", "").startswith("2026")]


def kz_midpoint(date_str: str, kz: str) -> Optional[datetime]:
    """Approximate entry timestamp: midpoint of kill zone."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    kz = (kz or "").lower()
    # XAUUSD KZs (per CLAUDE.md table; approximate)
    if "london" in kz:
        return d + timedelta(hours=8, minutes=45)   # 07:00 - 10:30 midpoint
    if "ny" in kz:
        return d + timedelta(hours=15, minutes=0)   # 13:00 - 17:00 midpoint
    if "tokyo" in kz or "asia" in kz:
        return d + timedelta(hours=1, minutes=30)
    return None


def vpin_at_entry_subgroup(df_xau: pd.DataFrame, feats: pd.DataFrame, trades: List[Dict]) -> Dict:
    """For each 2026 XAUUSD trade, find nearest M15 bar <= entry time, record VPIN
    at that bar. Test: does high-VPIN (top tercile) predict higher WR than low?
    """
    combined = pd.concat([df_xau[["time"]], feats[["vpin", "tick_imbalance"]]], axis=1)
    combined = combined.set_index("time").sort_index()

    rows = []
    for t in trades:
        ts = kz_midpoint(t["date"], t.get("kill_zone", ""))
        if ts is None:
            continue
        # nearest bar <= ts
        try:
            idx = combined.index.get_indexer([ts], method="pad")[0]
        except KeyError:
            continue
        if idx < 0 or idx >= len(combined):
            continue
        bar = combined.iloc[idx]
        if not np.isfinite(bar["vpin"]):
            continue
        rows.append(
            {
                "date": t["date"],
                "kz": t.get("kill_zone"),
                "vpin": float(bar["vpin"]),
                "tick_imb": float(bar["tick_imbalance"]) if np.isfinite(bar["tick_imbalance"]) else None,
                "r_multiple": float(t.get("r_multiple", 0.0)),
                "win": 1 if float(t.get("r_multiple", 0.0)) > 0 else 0,
            }
        )
    if len(rows) < 12:
        return {"n": len(rows), "note": "insufficient 2026-XAUUSD trade linkage for subgroup test"}

    vpins = np.array([r["vpin"] for r in rows])
    wins = np.array([r["win"] for r in rows])
    t1, t2 = np.percentile(vpins, [33.3, 66.7])
    low_mask = vpins <= t1
    mid_mask = (vpins > t1) & (vpins <= t2)
    high_mask = vpins > t2
    wr = {
        "low": float(wins[low_mask].mean()) if low_mask.any() else None,
        "mid": float(wins[mid_mask].mean()) if mid_mask.any() else None,
        "high": float(wins[high_mask].mean()) if high_mask.any() else None,
        "n_low": int(low_mask.sum()),
        "n_mid": int(mid_mask.sum()),
        "n_high": int(high_mask.sum()),
    }
    # Fisher exact: high vs low
    if low_mask.any() and high_mask.any():
        a = int(wins[high_mask].sum())
        b = int((1 - wins[high_mask]).sum())
        c = int(wins[low_mask].sum())
        d_ = int((1 - wins[low_mask]).sum())
        try:
            odds, pf = stats.fisher_exact([[a, b], [c, d_]])
        except Exception:
            odds, pf = np.nan, np.nan
    else:
        odds, pf = np.nan, np.nan

    return {
        "n": len(rows),
        "t33": float(t1),
        "t66": float(t2),
        "wr_by_vpin_tercile": wr,
        "fisher_high_vs_low_odds": float(odds) if odds == odds else None,
        "fisher_high_vs_low_p": float(pf) if pf == pf else None,
        "rows": rows,
    }


# ------------------------------------------------------------------
# Aggregation + ranking
# ------------------------------------------------------------------

def rank_top_features(all_results: Dict, metric: str = "dir_mi") -> List[Tuple]:
    """Pool (symbol, feature, horizon) triples with MI > null_95 and rank."""
    rows = []
    for sym, r in all_results.items():
        for feat, per_h in r["features"].items():
            for hk, metrics in per_h.items():
                mi = metrics.get(metric)
                null95 = metrics.get(f"{metric.split('_')[0]}_null_95")
                null99 = metrics.get(f"{metric.split('_')[0]}_null_99")
                p = metrics.get(f"{metric.split('_')[0]}_p")
                if mi is None or null95 is None:
                    continue
                sig95 = mi > null95
                sig99 = mi > null99
                rows.append(
                    (sym, feat, hk, mi, null95, null99, p, sig95, sig99)
                )
    rows.sort(key=lambda r: r[3], reverse=True)
    return rows


# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[q_14_broad_mi] starting")
    print(f"  data_dir: {DATA_DIR}")
    print(f"  symbols:  {list(SYMBOLS.keys())}")
    print(f"  n_perm:   {N_PERMUTATIONS}")

    all_results = {}
    for sym, csv in SYMBOLS.items():
        print(f"  -> {sym}")
        try:
            all_results[sym] = analyze_symbol(sym, csv, n_perm=N_PERMUTATIONS)
        except Exception as e:
            all_results[sym] = {"error": repr(e), "symbol": sym}
            print(f"     ERROR: {e}")

    # Subgroup test: XAUUSD VPIN at OB-trigger candles
    print("  -> XAUUSD VPIN subgroup (2026 trades)")
    try:
        xau_df = load_ohlcv(DATA_DIR / SYMBOLS["XAUUSD"])
        xau_feats = build_features(xau_df)
        trades_2026 = load_trades_2026()
        subg = vpin_at_entry_subgroup(xau_df, xau_feats, trades_2026)
    except Exception as e:
        subg = {"error": repr(e)}
        print(f"     ERROR: {e}")

    # Rank pooled (sym, feat, horizon) by dir MI
    ranked_dir = rank_top_features(all_results, metric="dir_mi")
    ranked_ret = rank_top_features(all_results, metric="ret_mi")

    # Save JSON
    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "n_permutations": N_PERMUTATIONS,
        "symbols": list(SYMBOLS.keys()),
        "horizons_m15_candles": HORIZONS,
        "vpin_bucket": VPIN_BUCKET,
        "results_per_symbol": all_results,
        "ranked_top_30_dir_mi": ranked_dir[:30],
        "ranked_top_30_ret_mi": ranked_ret[:30],
        "vpin_subgroup_xauusd_2026": subg,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"[q_14_broad_mi] JSON -> {OUT_JSON}")

    # Minimal md scaffold (full narrative in separate write step)
    lines = []
    lines.append("# Q-14 Broad MI Discovery (skeleton)\n")
    lines.append(f"Generated: {payload['generated_at']}\n")
    lines.append(f"Symbols analyzed: {', '.join(all_results.keys())}\n")
    lines.append(f"Horizons (M15): {HORIZONS}\n")
    lines.append("See narrative markdown for interpretation; raw JSON has full table.\n")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"[q_14_broad_mi] MD  -> {OUT_MD}")
    print("[q_14_broad_mi] done")


if __name__ == "__main__":
    main()
