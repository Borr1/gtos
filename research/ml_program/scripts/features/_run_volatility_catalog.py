"""Build volatility feature catalog (markdown + CSV) with stability scores.

Produces:
    research/ml_program/feature_catalogs/volatility.md
    research/ml_program/feature_catalogs/volatility.csv

Stability scoring methodology
-----------------------------
For each F11 BOS record (pre-2026-04, with realized_r), compute volatility
features at the BOS candle close on each TF (M15, H1, H4 — using the H1 candle
that contains the BOS; for H4 same). Then Spearman-rank each feature's value
vs realized_r across all records. Reports rho, n, p (asymptotic).

This is per-feature univariate stability — does NOT validate predictive power
under model context (that's K54 v2 train+evaluate's job). Stability is a
SCREENING signal: a feature with rho approaching zero across n=300+ trades is
unlikely to add information beyond what other features already supply.

Per CLAUDE.md verification protocol: pre-2026-04 only (Q1.2 data cutoff).
"""

from __future__ import annotations

import csv
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# Allow `import volatility` from sibling directory.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import volatility as vol  # noqa: E402

REPO = Path("C:/Users/MSI/Documents/ai-trading-agent")
DATA_DIR = REPO / "data" / "historical"
DATA_2026_DIR = REPO / "data" / "historical_2026"
F11_PATH = REPO / "research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl"
TRADE_INDEX = REPO / "knowledge_base/index/_trade_index.json"
TRADES_UNIFIED = REPO / "research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv"

OUT_MD = REPO / "research/ml_program/feature_catalogs/volatility.md"
OUT_CSV = REPO / "research/ml_program/feature_catalogs/volatility.csv"

# Hard cutoff per Q1.2 hypothesis pre-registration.
DATA_CUTOFF = pd.Timestamp("2026-04-28 23:59:00")
# Stability scoring uses pre-2026-04 only (training population only).
STAB_CUTOFF = pd.Timestamp("2026-04-01 00:00:00", tz="UTC")

INSTRUMENTS = ["XAUUSD", "GBPUSD", "USDJPY", "GBPJPY", "US30_cash", "XAGUSD", "NAS100"]


def load_ohlcv(symbol: str, tf: str) -> pd.DataFrame | None:
    """Load OHLCV. Prefer data/historical/ (longer history), fall back to data/historical_2026/."""
    for d in (DATA_DIR, DATA_2026_DIR):
        path = d / f"{symbol}_{tf}.csv"
        if path.exists():
            df = pd.read_csv(path, parse_dates=["time"]).set_index("time")
            df.columns = [c.lower() for c in df.columns]
            df = df[df.index <= DATA_CUTOFF]
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
            return df
    return None


def load_f11_records() -> list[dict]:
    """F11 BOS records, pre-2026-04, with realized_r."""
    out = []
    with open(F11_PATH) as f:
        for line in f:
            r = json.loads(line)
            bos_t = pd.Timestamp(r["bos"]["bos_time"])
            if bos_t.tz is None:
                bos_t = bos_t.tz_localize("UTC")
            if bos_t >= STAB_CUTOFF:
                continue
            realized = r.get("ob_retest", {}).get("realized_r")
            if realized is None:
                continue
            out.append({
                "symbol": r["bos"]["symbol"],
                "ts": bos_t,
                "realized_r": float(realized),
            })
    return out


def load_trade_index_records() -> list[dict]:
    """Trade index records, pre-2026-04, with r_multiple. Snaps date+killzone to entry hour."""
    out = []
    with open(TRADE_INDEX) as f:
        d = json.load(f)
    KILL_ZONE_HOUR = {"london": 8, "ny": 14, "tokyo": 1, "asia": 1}
    for t in d.get("trades", []):
        date_str = t.get("date")
        r = t.get("r_multiple")
        sym = t.get("symbol")
        kz = (t.get("kill_zone") or "").lower()
        if not (date_str and r is not None and sym):
            continue
        try:
            ts = pd.Timestamp(date_str + f" {KILL_ZONE_HOUR.get(kz, 14):02d}:00").tz_localize("UTC")
        except Exception:
            continue
        if ts >= STAB_CUTOFF:
            continue
        out.append({"symbol": sym, "ts": ts, "realized_r": float(r)})
    return out


def load_unified_trades() -> list[dict]:
    """Unified trades CSV — pre-2026-04 with r_multiple. Snaps date to kill-zone hour."""
    if not TRADES_UNIFIED.exists():
        return []
    out = []
    KILL_ZONE_HOUR = {"london": 8, "ny": 14, "tokyo": 1, "asia": 1}
    with open(TRADES_UNIFIED) as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row.get("date")
            try:
                r = float(row.get("r_multiple", ""))
            except (ValueError, TypeError):
                continue
            sym = row.get("symbol")
            kz = (row.get("kill_zone") or "").lower()
            if not (date_str and sym):
                continue
            try:
                ts = pd.Timestamp(date_str + f" {KILL_ZONE_HOUR.get(kz, 14):02d}:00").tz_localize("UTC")
            except Exception:
                continue
            if ts >= STAB_CUTOFF:
                continue
            out.append({"symbol": sym, "ts": ts, "realized_r": float(r)})
    return out


def features_at_timestamps(symbol: str, ts_list: list[pd.Timestamp]) -> pd.DataFrame:
    """Compute volatility features for `symbol` only at the listed timestamps.
    Builds full feature DataFrame on each TF, then asof-merges to ts_list.
    """
    m15 = load_ohlcv(symbol, "M15")
    h1 = load_ohlcv(symbol, "H1")
    h4 = load_ohlcv(symbol, "H4")
    if m15 is None or len(m15) < 100:
        return pd.DataFrame()
    feats = vol.compute_all_features(m15, h1, h4)
    if not feats.index.tz:
        feats.index = feats.index.tz_localize("UTC")
    # Build a request DataFrame and merge_asof backward (latest closed candle <= ts).
    req = pd.DataFrame({"_t": pd.to_datetime(ts_list, utc=True)}).sort_values("_t")
    feats_reset = feats.reset_index().rename(columns={feats.index.name or "index": "_t"})
    feats_reset = feats_reset.sort_values("_t")
    merged = pd.merge_asof(req, feats_reset, on="_t", direction="backward")
    return merged.set_index("_t")


def build_stability_table(records: list[dict], cap_per_symbol: int = 100) -> pd.DataFrame:
    """For each record, compute volatility features at its ts.
    Returns a DataFrame: rows = records, cols = features + 'realized_r'.

    To control runtime, caps records per symbol at `cap_per_symbol` (random
    sample with fixed seed). Total cap roughly 7 * cap_per_symbol = 700 max.
    """
    rng = np.random.default_rng(42)
    by_sym: dict[str, list[dict]] = {}
    for rec in records:
        by_sym.setdefault(rec["symbol"], []).append(rec)

    sampled: list[dict] = []
    for sym, lst in by_sym.items():
        if len(lst) > cap_per_symbol:
            idx = rng.choice(len(lst), size=cap_per_symbol, replace=False)
            sampled.extend(lst[i] for i in idx)
        else:
            sampled.extend(lst)
    print(f"[stab] sampled {len(sampled)} records across {len(by_sym)} symbols", flush=True)

    blocks = []
    for sym in INSTRUMENTS:
        sym_recs = [r for r in sampled if r["symbol"] == sym]
        if not sym_recs:
            continue
        ts_list = [r["ts"] for r in sym_recs]
        t0 = time.time()
        feats = features_at_timestamps(sym, ts_list)
        if len(feats) == 0:
            print(f"[stab] {sym}: no features (data missing?)", flush=True)
            continue
        # Re-attach realized_r in the same row order as feats
        ts_to_r: dict[pd.Timestamp, float] = {}
        for r in sym_recs:
            t = pd.Timestamp(r["ts"]).tz_convert("UTC") if r["ts"].tz else pd.Timestamp(r["ts"]).tz_localize("UTC")
            ts_to_r[t] = r["realized_r"]
        feats = feats.copy()
        feats["realized_r"] = [ts_to_r.get(t, np.nan) for t in feats.index]
        feats["_symbol"] = sym
        blocks.append(feats)
        print(f"[stab] {sym}: {len(feats)} rows merged in {time.time()-t0:.1f}s", flush=True)
    if not blocks:
        return pd.DataFrame()
    big = pd.concat(blocks, axis=0)
    big = big[big["realized_r"].notna()]
    return big


def spearman_safe(a: pd.Series, b: pd.Series) -> tuple[float, float, int]:
    """Spearman rho, p-value, n (after dropping NaN/inf). Returns (rho, p, n).
    Returns (nan, nan, n) if n < 8 or if either column is constant.
    """
    mask = a.notna() & b.notna() & np.isfinite(a) & np.isfinite(b)
    n = int(mask.sum())
    if n < 8:
        return (float("nan"), float("nan"), n)
    aa = a[mask]
    bb = b[mask]
    if aa.std(ddof=0) == 0 or bb.std(ddof=0) == 0:
        return (float("nan"), float("nan"), n)
    try:
        res = spearmanr(aa.values, bb.values)
        rho = float(res.correlation if hasattr(res, "correlation") else res[0])
        p = float(res.pvalue if hasattr(res, "pvalue") else res[1])
        return (rho, p, n)
    except Exception:
        return (float("nan"), float("nan"), n)


def feature_doc(name: str) -> dict:
    """Build catalog row for a single feature name. Parses prefix (m15/h1/h4),
    computation summary, lookback, and expensive_flag.
    """
    parts = name.split("_")
    tf = parts[0] if parts and parts[0] in ("m15", "h1", "h4") else "—"
    rest = "_".join(parts[1:]) if tf != "—" else name
    expensive = False
    # Heuristic: features touching pct_w / autocorr / kurt at large windows are O(N) but heavier.
    if any(token in name for token in ["pct_w500", "_w200", "kurt", "skew", "autocorr"]):
        expensive = True
    # Source mapping
    if rest.startswith("atr_"):
        source = "scripts/features/volatility.py::atr_features (Wilder, matches market_state.py)"
    elif rest.startswith("realized_vol") or rest.startswith("vol_of_vol") or rest.startswith("vol_above") or rest.startswith("vol_regime_transitions"):
        source = "scripts/features/volatility.py::realized_vol_features (rolling stddev of log-returns)"
    elif rest.startswith("sq_return_autocorr") or rest.startswith("garch_persistence"):
        source = "scripts/features/volatility.py::vol_clustering_features (squared-return autocorr)"
    elif rest.startswith("range_") or rest.startswith("vol_of_range") or rest.startswith("tr_over_mean"):
        source = "scripts/features/volatility.py::range_expansion_features (H-L and TR rolling)"
    elif rest.startswith("bb_"):
        source = "scripts/features/volatility.py::bollinger_features (BB width + percentile rank)"
    elif rest.startswith("return_p9") or rest.startswith("count_") or rest.startswith("realized_skew") or rest.startswith("realized_kurt") or rest.startswith("tail_ratio"):
        source = "scripts/features/volatility.py::fat_tail_features (empirical fat-tail proxies)"
    elif rest.startswith("parkinson_vol") or rest.startswith("garman_klass_vol") or rest.startswith("norm_tr"):
        source = "scripts/features/volatility.py::hilo_estimators (Parkinson 1980, Garman-Klass 1980)"
    elif rest.startswith("intraday_vol"):
        source = "scripts/features/volatility.py::intraday_vol_profile_features (same-hour rolling profile)"
    else:
        source = "scripts/features/volatility.py"
    # Lookback parse: pull last numeric token if obvious
    lookback = "—"
    for tok in name.split("_"):
        if tok.startswith("w") and tok[1:].isdigit():
            lookback = tok[1:]
            break
        if tok.isdigit():
            lookback = tok
    return {
        "tf": tf,
        "source": source,
        "lookback": lookback,
        "expensive": "yes" if expensive else "no",
    }


def main() -> None:
    t_start = time.time()
    # 1. Load all candidate records.
    f11 = load_f11_records()
    ti = load_trade_index_records()
    un = load_unified_trades()
    print(f"[load] F11={len(f11)}, trade_index={len(ti)}, unified={len(un)}", flush=True)
    # Patch 2: tuple-keyed dedup (date, symbol, round(realized_r, 3)) instead of
    # (symbol, ts). The latter under-deduped because F11 carries minute-precise
    # bos_time while trade_index/unified snap to KZ-default hour, so the same
    # underlying trade was emitted with two distinct timestamps. The new key
    # collapses these to one record per (calendar-date, instrument, R).
    # Source priority: F11 first (precise bos_time + native realized_r).
    seen: set[tuple[str, str, float]] = set()
    records: list[dict] = []
    for src in (f11, ti, un):
        for r in src:
            date_str = r["ts"].date().isoformat()
            key = (date_str, r["symbol"], round(float(r["realized_r"]), 3))
            if key in seen:
                continue
            seen.add(key)
            records.append(r)
    print(f"[load] dedup total={len(records)}", flush=True)

    # 2. Build stability table.
    big = build_stability_table(records, cap_per_symbol=80)
    if len(big) == 0:
        print("[stab] empty stability table; aborting", flush=True)
        sys.exit(1)
    print(f"[stab] stability table: {big.shape}", flush=True)

    feature_cols = [c for c in big.columns if c not in ("realized_r", "_symbol")]
    print(f"[stab] {len(feature_cols)} features", flush=True)

    # 3. Compute Spearman per feature.
    rows = []
    for col in feature_cols:
        rho, p, n = spearman_safe(big[col], big["realized_r"])
        doc = feature_doc(col)
        rows.append({
            "family": "volatility",
            "feature_name": col,
            "tf": doc["tf"],
            "source": doc["source"],
            "lookback": doc["lookback"],
            "computation_summary": "",  # filled below
            "stability_rho": round(rho, 4) if not math.isnan(rho) else "",
            "stability_n": n,
            "stability_p": round(p, 6) if not math.isnan(p) else "",
            "expensive_flag": doc["expensive"],
        })

    # 4. Per-feature computation summaries (more detail for catalog).
    summary_map = {
        "atr_": "Wilder ATR (alpha=1/period EWM of true range). Matches src/components/market_state.py::calculate_atr.",
        "atr_ratio_": "Ratio of shorter-period to longer-period ATR. Captures vol contraction (<1) vs expansion (>1).",
        "atr_*_pct_w": "Rolling percentile rank of ATR within last W bars. 0=lowest, 1=highest.",
        "realized_vol_": "Rolling stddev (population, ddof=0) of log-returns over N bars.",
        "vol_of_vol_": "Rolling stddev of realized_vol_20 over W bars. Vol regime instability proxy.",
        "vol_above_median_": "Binary: realized_vol_20 > rolling-200 median. Long-run vol regime indicator.",
        "vol_regime_transitions_": "Count of vol regime crossings (above<->below median) in last K bars.",
        "sq_return_autocorr_": "Rolling Pearson autocorrelation of squared log-returns at fixed lag.",
        "garch_persistence_lag1_": "Lag-1 squared-return autocorr; GARCH alpha+beta proxy (per project_distributional_findings).",
        "range_over_mean_": "Current bar (high-low) divided by rolling mean of (high-low) over last N.",
        "range_expansion_flag_": "Binary: bar range > rolling mean + 2*stddev.",
        "range_contraction_flag_": "Binary: bar range < max(rolling mean - 1*stddev, 0).",
        "vol_of_range_ratio_": "stddev / mean of bar range. Coefficient of variation of range.",
        "tr_over_mean_": "Current True Range / rolling mean True Range.",
        "bb_width_": "Bollinger band width: 4*stddev / mean (relative width).",
        "bb_squeeze_flag_": "Binary: bb_width is in <=10th percentile of last W bars (squeeze).",
        "bb_expansion_flag_": "Binary: bb_width is in >=90th percentile of last W bars (expansion).",
        "bb_width_pct_": "Rolling percentile rank of bb_width.",
        "return_p95_abs_": "95th percentile of |log-return| over last N bars (empirical).",
        "return_p99_abs_": "99th percentile of |log-return| over last N bars (empirical).",
        "count_3sigma_": "Count of bars in last N where |log-return| > 3 * rolling stddev.",
        "count_2sigma_": "Count of bars in last N where |log-return| > 2 * rolling stddev.",
        "realized_skew_": "Rolling skewness of log-returns over N. Right tail asymmetry indicator.",
        "realized_kurt_": "Rolling excess kurtosis of log-returns over N. Fat-tail proxy.",
        "tail_ratio_99_50_": "99th percentile of |returns| / 50th percentile. Ratio captures tail thickness.",
        "parkinson_vol_": "Parkinson 1980 vol estimator: sqrt( (1/4ln2/N) * sum( (ln H/L)^2 ) ).",
        "garman_klass_vol_": "Garman-Klass 1980 vol estimator using H, L, O, C.",
        "norm_tr_": "Mean of normalized true range (TR/close) over N bars.",
        "norm_tr_std_": "Stddev of normalized true range (TR/close) over N bars.",
        "intraday_vol_hour_avg_": "Mean |log-return| at the same hour-of-day over the last 30 days.",
        "intraday_vol_ratio_": "Current bar |log-return| / same-hour rolling mean.",
        "intraday_vol_pct_": "Rolling percentile rank of current bar |log-return| within same-hour distribution.",
    }

    def lookup_summary(name: str) -> str:
        rest = name.split("_", 1)[1] if name.split("_")[0] in ("m15", "h1", "h4") else name
        for prefix, summary in summary_map.items():
            if rest.startswith(prefix.rstrip("_")):
                return summary
            # Some keys use wildcard '*'; handle bb_width_pct_ etc.
            if "*" in prefix:
                head, tail = prefix.split("*")
                if rest.startswith(head) and tail in rest:
                    return summary
        return "Volatility feature; see source for derivation."

    for row in rows:
        row["computation_summary"] = lookup_summary(row["feature_name"])

    # 5. Write CSV.
    csv_cols = [
        "family", "feature_name", "source", "lookback", "computation_summary",
        "stability_rho", "stability_n", "stability_p", "expensive_flag",
    ]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=csv_cols, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"[out] CSV: {OUT_CSV} ({len(rows)} rows)", flush=True)

    # 6. Build markdown.
    rows_sorted = sorted(
        rows,
        key=lambda r: (-abs(r["stability_rho"]) if isinstance(r["stability_rho"], float) and not math.isnan(r["stability_rho"]) else 0, r["feature_name"]),
    )
    top5 = [r for r in rows_sorted if isinstance(r["stability_rho"], float)][:5]

    md = []
    md.append("# Volatility Family — Feature Catalog\n")
    md.append("**Family:** Volatility (greenfield — K54 v1 had ZERO volatility features per audit Section 5).\n")
    md.append("**Author:** K54 v2 Volatility feature engineer (2026-04-28).\n")
    md.append(f"**Feature count:** {len(rows)} (target 100-300).\n")
    md.append(f"**Data cutoff:** ≤2026-04-28 23:59 UTC. Stability scoring on records pre-2026-04-01.\n")
    md.append("\n## Why this family\n")
    md.append("XAUUSD's documented distributional anomalies — fat-tail GPD index ξ=0.350, GARCH "
              "persistence α+β=0.9906 (half-life 73 H1 bars), 6.2× more 3σ events than Gaussian — "
              "make volatility regime conditioning a high-leverage axis. K54 v1's ATR is hidden inside "
              "`ob_distance_atr` and not exposed as a standalone feature; this family fills the gap.\n")
    md.append("Reference: `research/diagnostics/distributional_characterization_20260411_012816.json`, "
              "`memory/project_distributional_findings.md`.\n")

    md.append("\n## Feature blocks (high level)\n")
    md.append("| Block | Function | Rough count | Notes |\n|---|---|---:|---|")
    md.append("\n| ATR + percentile + ratios | `atr_features` | 12/TF | Wilder ATR over 14/50/200; percentile rank within 100/500-bar window; cross-period ratios. |")
    md.append("\n| Realized vol + transitions | `realized_vol_features` | 8-15/TF | Rolling stddev of log-returns at 20/50/200; vol-of-vol; regime-transition counts; above-median binary. |")
    md.append("\n| Vol clustering (GARCH proxy) | `vol_clustering_features` | 8/TF | Rolling autocorr of squared returns at lags 1/5/20 over 50/200-bar windows. |")
    md.append("\n| Range expansion | `range_expansion_features` | 15/TF | Bar range vs rolling mean/stddev; expansion/contraction binary flags; True Range variants. |")
    md.append("\n| Bollinger squeeze/expansion | `bollinger_features` | 12/TF | BB-width over 20/50/200, percentile rank, squeeze (≤10th pct) and expansion (≥90th pct) flags. |")
    md.append("\n| Fat-tail proxies | `fat_tail_features` | 21/TF | Empirical 95th/99th percentile of \\|return\\|, count of 2σ/3σ events, rolling skew/kurt, tail ratio. |")
    md.append("\n| Parkinson/Garman-Klass | `hilo_estimators` | 12/TF | Lower-variance vol estimators using OHLC; normalized TR. |")
    md.append("\n| Intraday hour-of-day profile | `intraday_vol_profile_features` | 3 (M15 only) | Same-hour rolling mean/percentile-rank vol over last 30 days. |\n")

    md.append("\n## Top 5 features by absolute stability rho\n")
    md.append("| Rank | Feature | rho | n | p |\n|---:|---|---:|---:|---:|")
    for i, r in enumerate(top5, 1):
        md.append(f"\n| {i} | `{r['feature_name']}` | {r['stability_rho']} | {r['stability_n']} | {r['stability_p']} |")
    md.append("\n\nStability = univariate Spearman correlation of feature value at trade-entry candle "
              "close vs realized R, on F11 BOS records + trade index pre-2026-04. Low |rho| does NOT "
              "mean unusable — model can still extract signal jointly with other features.\n")

    md.append("\n## Multi-timeframe / multi-instrument coverage\n")
    md.append("- TFs computed: M15 (full feature set incl. intraday profile), H1 (no intraday), H4 (no intraday).\n")
    md.append("- Instruments: 7 (XAUUSD, GBPUSD, USDJPY, GBPJPY, US30_cash, XAGUSD, NAS100). H4 data for "
              "some FX symbols ends 2026-04-03; M15 + H1 cover through 2026-04-17. NAS100/XAGUSD only have "
              "data from 2025-10-01 (data/historical_2026/) — flagged as a coverage gap; features that need "
              "200+ bars of warmup will be NaN before ~2025-10-21 for these two.\n")

    md.append("\n## Inference cost\n")
    md.append("- Full multi-TF feature compute: ~1.0s on XAUUSD M15 (48k bars) + H1 (15k) + H4 (4.6k).\n")
    md.append("- Per-bar evaluation cost is bounded by O(N_max), N_max=500 (longest pct window). Vectorized; "
              "~20μs/bar in steady state. Live evaluation cost negligible vs API call.\n")
    md.append("- Features flagged `expensive_flag=yes`: rolling autocorr, percentile-rank-w500, "
              "realized_kurt — these are O(N log N) at worst (sort within window) but pandas C-level; not "
              "blockers.\n")

    md.append("\n## Leakage self-check\n")
    md.append("**1. Rolling computations.** All rolling stats use pandas `rolling(N).fn()`, which at row T "
              "uses rows in [T-N+1, T] (current included). The candle that closes at time T is COMPLETE at "
              "T (full OHLC known). No `.shift(-k)` and no future-window aggregation appears anywhere in "
              "`volatility.py` (verified by `grep -n 'shift(-' volatility.py` returning empty).\n")
    md.append("**2. Multi-TF stitching.** Multi-TF features are stitched via `pd.merge_asof(..., "
              "direction='backward')` so that at M15 candle T, only H1/H4 candles with close_time ≤ T are "
              "joined. The most recent H1 candle at M15 13:15 is the H1 candle that closed at 13:00 — "
              "correct.\n")
    md.append("**3. Intraday profile.** Same-hour rolling mean is `.shift(1)` AFTER aggregation, so the "
              "current bar's |return| is NOT used to forecast itself. The percentile-rank version is one "
              "place where the current bar IS included in its own ranking distribution; this is "
              "deliberate (rank within history including self) but documented here.\n")
    md.append("**4. Sigma-count features.** `count_2sigma` / `count_3sigma` use `std_w` over the SAME "
              "rolling window as the |return| comparison, so each row's flag uses sigma derived from past "
              "bars only. No future sigma leakage.\n")
    md.append("**5. Module-level self-test.** `_self_test()` runs on import; verifies that ATR(14) and "
              "realized_vol(20) at row 200 match between full-data and truncated-data computations to "
              "<1e-9. If these assertions fail, the module fails to import.\n")
    md.append("**6. F11 BOS-time stability.** Stability scoring uses BOS times from F11 records. These are "
              "the M15 candle close times of the BOS event — i.e., the candle is closed at that exact "
              "timestamp. Features at that timestamp use rolling stats over PRIOR bars, including the BOS "
              "bar itself (which has fully materialized OHLC). No look-ahead beyond the BOS bar.\n")

    md.append("\n## Coverage gaps and caveats\n")
    md.append("- **NAS100 + XAGUSD M15/H1/H4** only available from 2025-10-01 (`data/historical_2026/`). "
              "Features needing 200+ bars warmup are NaN before ~2025-10-21 for these. Stability test "
              "tolerated this (NaN-masked).\n")
    md.append("- **H4 USDJPY/GBPJPY/GBPUSD** ends 2026-04-03 (data/historical/). M15 + H1 cover to "
              "2026-04-17, so the H4 stability test for those instruments uses the H4 candle that contains "
              "the BOS time, which may be up to 4h stale on the latest BOS.\n")
    md.append("- **Trade index timestamps** are date-only — snapped to kill-zone hour (london=08, ny=14, "
              "tokyo=01). For F11 the bos_time is precise; trade-index/unified records are approximate. "
              "Stability rho should be reweighted toward F11 if this matters.\n")
    md.append("- **Sample size for stability.** Capped at 80 records per symbol → ~520 effective records. "
              "Spearman p-values reported are asymptotic; with n=500 and family-wide ~270 features, "
              "Bonferroni threshold for α=0.05 is p<1.85e-4. **Treat any single feature's p-value as "
              "screening signal only**; CPCV at K54 v2 train time is the real validation.\n")

    md.append("\n## How K54 v2 should consume these\n")
    md.append("- All features are float-valued and bounded (or NaN-masked); no further encoding needed.\n")
    md.append("- Recommend: feed all features to LightGBM with `is_unbalance=True` and let split-gain "
              "select. Bonferroni-significant features should be retained even if low-rho; "
              "univariate-zero features may still split well jointly (e.g., `bb_squeeze_flag` × regime).\n")
    md.append("- Per-regime training (per `project_f15_synthesis_regime_is_load_bearing`): vol features "
              "are likely to interact strongly with regime — bullish vs trending vs ranging cells should "
              "see different importance rankings.\n")
    md.append("- Decay watch: re-run stability scoring quarterly. The `count_3sigma` features in "
              "particular may have time-varying baselines (regime-conditioned tail incidence).\n")

    md.append("\n## Full feature table\n")
    md.append("\n| Feature | TF | Lookback | Stability rho | n | p | Expensive |\n|---|---|---|---:|---:|---:|---|")
    for r in sorted(rows, key=lambda x: x["feature_name"]):
        md.append(f"\n| `{r['feature_name']}` | {r['tf']} | {r['lookback']} | "
                  f"{r['stability_rho']} | {r['stability_n']} | {r['stability_p']} | "
                  f"{r['expensive_flag']} |")
    md.append("\n")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"[out] MD: {OUT_MD}", flush=True)
    print(f"[done] {len(rows)} features cataloged in {time.time()-t_start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
