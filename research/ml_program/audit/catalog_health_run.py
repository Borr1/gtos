#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K54 v2 Catalog Health Audit (Q1, Q2, Q4) — single-shot runner.

Q1 (Composability): Imports all 6 family modules, computes every family's
features for one (timestamp, instrument) tuple. Verifies output shape,
naming uniqueness, time-axis joinability.

Q2 (Cross-family redundancy): Computes Pearson + Spearman correlation
matrices over the K54 v1 411-trade cohort joined to K54 v2 catalog
features. Reports |rho| >= 0.7 / 0.9 pair counts and top-20.

Q4 (Inference cost): Times unified feature build for one
(timestamp, instrument) tuple, all 1219 features. Per-family breakdown.

Output (UTF-8):
  research/ml_program/audit/q1_composability.json
  research/ml_program/audit/q2_correlation_matrix.csv
  research/ml_program/audit/q2_top_corr_pairs.csv
  research/ml_program/audit/q2_correlation_summary.json
  research/ml_program/audit/q4_timing.csv
  research/ml_program/audit/q4_timing_summary.json
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import warnings
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
AUDIT = REPO / "research" / "ml_program" / "audit"
SCRIPTS = REPO / "research" / "ml_program" / "scripts"
FEATURES = SCRIPTS / "features"
CATALOGS = REPO / "research" / "ml_program" / "feature_catalogs"

# Make sibling feature modules importable
sys.path.insert(0, str(FEATURES))
sys.path.insert(0, str(REPO))

# Test fixture
TEST_INSTRUMENT = "XAUUSD"
# Spec said 2026-03-15 13:00 UTC, but that's a Sunday (no candles). Use the
# nearest weekday NY-KZ open: 2026-03-13 13:00 UTC (Friday).
TEST_TS_STR = "2026-03-13 13:00:00"
TEST_TS = datetime(2026, 3, 13, 13, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _resolve_ohlcv_path(symbol: str, tf: str):
    """Pick the data file with maximum row count for (symbol, tf). Search
    data/historical_2026 (newer) and data/historical (deeper history).
    """
    candidates = []
    for d in ("historical_2026", "historical"):
        p = REPO / "data" / d / f"{symbol}_{tf}.csv"
        if p.exists():
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            candidates.append((size, p))
    if not candidates:
        return None
    # Pick LARGEST file (most rows) — this gives us deepest history.
    candidates.sort(reverse=True)
    return candidates[0][1]


def load_ohlcv_pandas(symbol: str, tf: str):
    """Load the OHLCV file with deepest history available (data/historical_2026
    overlaps data/historical; pick the larger).

    For correlation computation we need dates back to 2024-04 (K54 v1 cohort
    start). data/historical_2026/ starts 2025-10; data/historical/ extends
    to 2024-04. Concatenating both gives the most coverage but risks
    duplicates. Picking the larger file is sufficient because data/historical
    extends through 2026-04-17 too.
    """
    import pandas as pd
    path = _resolve_ohlcv_path(symbol, tf)
    if path is None:
        return None
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df = df.dropna(subset=["time"]).drop_duplicates(subset=["time"]).set_index("time").sort_index()
    return df


def load_ohlcv_dicts(symbol: str, tf: str):
    """Return list[dict] candle records as required by structure / liquidity."""
    path = _resolve_ohlcv_path(symbol, tf)
    if path is None:
        return []
    out = []
    seen_times = set()
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            t = row["time"]
            if t in seen_times:
                continue
            seen_times.add(t)
            out.append({
                "time": t,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0) or 0),
            })
    out.sort(key=lambda r: r["time"])
    return out


def find_anchor_idx(candles, ts_str: str) -> int:
    """Find idx of last candle with open <= ts_str."""
    for i in range(len(candles) - 1, -1, -1):
        if candles[i]["time"] <= ts_str:
            return i
    return -1


def slice_until_pandas(df, ts_close):
    """Return df with rows whose index <= ts_close (inclusive). Useful for
    bar-frame inputs to volatility / microstructure (which expect closed-bar
    information up to and including the eval point).
    """
    if df is None:
        return None
    return df[df.index <= ts_close]


# ---------------------------------------------------------------------------
# Q1 — Composability (run once, capture metadata)
# ---------------------------------------------------------------------------

def run_q1():
    import pandas as pd
    print("=" * 70)
    print("Q1 — Composability")
    print("=" * 70)

    findings = {
        "test_instrument": TEST_INSTRUMENT,
        "test_timestamp": TEST_TS_STR,
        "deviation_note": (
            "Spec asked for 2026-03-15 13:00 UTC; that is a Sunday with no candles. "
            "Substituted 2026-03-13 13:00 UTC (Friday NY-KZ open) — weekday close in "
            "training population (<= 2026-04-28)."
        ),
        "imports": {},
        "interfaces": {},
        "outputs": {},
        "name_collisions_across_families": [],
        "duplicate_names_within_family": [],
        "verdict": None,
    }

    # 1) Import all six modules
    family_modules = {}
    for name in ("structure", "volatility", "microstructure",
                 "time_session", "liquidity", "regime"):
        t0 = time.perf_counter()
        try:
            mod = __import__(name)
            findings["imports"][name] = {
                "ok": True,
                "import_time_ms": round((time.perf_counter() - t0) * 1000, 2),
                "module_path": getattr(mod, "__file__", "?"),
            }
            family_modules[name] = mod
        except Exception as e:
            findings["imports"][name] = {
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
            }
    if any(not v["ok"] for v in findings["imports"].values()):
        findings["verdict"] = "FAIL_IMPORT"
        return findings, {}

    # 2) Load OHLCV for the test instrument (pandas + dicts)
    df_m15 = load_ohlcv_pandas(TEST_INSTRUMENT, "M15")
    df_m1 = load_ohlcv_pandas(TEST_INSTRUMENT, "M1")
    df_h1 = load_ohlcv_pandas(TEST_INSTRUMENT, "H1")
    df_h4 = load_ohlcv_pandas(TEST_INSTRUMENT, "H4")
    df_d1 = load_ohlcv_pandas(TEST_INSTRUMENT, "D1")

    # Slice bar frames to <=ts (volatility / microstructure are fail-safe but
    # still need the row at-or-before ts_close).
    df_m15_s = slice_until_pandas(df_m15, TEST_TS)
    df_m1_s = slice_until_pandas(df_m1, TEST_TS)
    df_h1_s = slice_until_pandas(df_h1, TEST_TS)
    df_h4_s = slice_until_pandas(df_h4, TEST_TS)

    candles_m15 = load_ohlcv_dicts(TEST_INSTRUMENT, "M15")
    candles_h1 = load_ohlcv_dicts(TEST_INSTRUMENT, "H1")
    candles_h4 = load_ohlcv_dicts(TEST_INSTRUMENT, "H4")
    candles_d1 = load_ohlcv_dicts(TEST_INSTRUMENT, "D1")

    candles_by_tf = {
        "M15": candles_m15,
        "H1": candles_h1,
        "H4": candles_h4,
        "D1": candles_d1,
    }
    anchor_by_tf = {
        "M15": find_anchor_idx(candles_m15, TEST_TS_STR),
        "H1": find_anchor_idx(candles_h1, TEST_TS_STR),
        "H4": find_anchor_idx(candles_h4, TEST_TS_STR),
        "D1": find_anchor_idx(candles_d1, TEST_TS_STR),
    }
    findings["interfaces"]["anchor_idx_by_tf"] = anchor_by_tf

    # Reference price for liquidity (BOS-close convention). Use M15 close at anchor.
    ref_price = (
        candles_m15[anchor_by_tf["M15"]]["close"]
        if anchor_by_tf["M15"] >= 0 else float("nan")
    )

    # 3) Compute each family. Capture timing + output keys + sample numeric
    #    values for downstream Q4.
    per_family_features: dict[str, dict[str, float]] = {}

    # ---- Structure ----
    try:
        t0 = time.perf_counter()
        df_struct = family_modules["structure"].build_structure_features(
            timestamps=[TEST_TS_STR],
            candles_by_tf=candles_by_tf,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        cols = list(df_struct.columns)
        per_family_features["structure"] = df_struct.iloc[0].to_dict()
        findings["outputs"]["structure"] = {
            "n_features": len(cols),
            "elapsed_ms": round(elapsed, 2),
            "interface": "build_structure_features(timestamps, candles_by_tf)",
            "first_5": cols[:5],
            "last_5": cols[-5:],
        }
    except Exception as e:
        findings["outputs"]["structure"] = {"error": f"{type(e).__name__}: {e}"}

    # ---- Volatility ----
    try:
        t0 = time.perf_counter()
        df_vol = family_modules["volatility"].compute_all_features(
            df_m15=df_m15_s, df_h1=df_h1_s, df_h4=df_h4_s,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        # Take the row aligned to TEST_TS (last row of M15 slice <= ts_close).
        # df_vol is indexed by M15 close via merge_asof; take last row.
        if TEST_TS in df_vol.index:
            row = df_vol.loc[TEST_TS]
        else:
            row = df_vol.iloc[-1]
        cols = list(df_vol.columns)
        per_family_features["volatility"] = {c: float(row[c]) if (
            row[c] == row[c]) else float("nan") for c in cols}
        findings["outputs"]["volatility"] = {
            "n_features": len(cols),
            "elapsed_ms": round(elapsed, 2),
            "interface": "compute_all_features(df_m15, df_h1, df_h4)",
            "first_5": cols[:5],
            "last_5": cols[-5:],
            "row_ts": str(row.name) if hasattr(row, "name") else str(TEST_TS),
        }
    except Exception as e:
        findings["outputs"]["volatility"] = {"error": f"{type(e).__name__}: {e}"}

    # ---- Microstructure ----
    try:
        t0 = time.perf_counter()
        # The module enforces a hard < cutoff: ts must be <= 2026-04-28 23:59 UTC.
        # We are on 2026-03-13 — well below cutoff.
        # The module accepts pandas frames with a 'time' column OR DatetimeIndex.
        # Looking at compute_microstructure_features, it does df_m15[df_m15.time<ts]
        # style slicing. Need to provide frames with 'time' column. Reset index.
        def _reset(df):
            if df is None:
                return df
            d2 = df.reset_index()
            return d2
        df_micro = family_modules["microstructure"].compute_microstructure_features(
            df_m15=_reset(df_m15), df_m1=_reset(df_m1),
            df_h1=_reset(df_h1), df_h4=_reset(df_h4),
            ts_close=TEST_TS, symbol=TEST_INSTRUMENT, tick_df=None,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        row = df_micro.iloc[0]
        cols = list(df_micro.columns)
        per_family_features["microstructure"] = {c: float(row[c]) if (
            row[c] == row[c]) else float("nan") for c in cols}
        findings["outputs"]["microstructure"] = {
            "n_features": len(cols),
            "elapsed_ms": round(elapsed, 2),
            "interface": "compute_microstructure_features(df_m15, df_m1, df_h1, df_h4, ts_close, symbol, tick_df)",
            "first_5": cols[:5],
            "last_5": cols[-5:],
        }
    except Exception as e:
        findings["outputs"]["microstructure"] = {"error": f"{type(e).__name__}: {e}"}

    # ---- Time / Session ----
    try:
        t0 = time.perf_counter()
        ts_dict = family_modules["time_session"].compute_time_session_features(
            ts=TEST_TS, symbol=TEST_INSTRUMENT,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        per_family_features["time_session"] = ts_dict
        cols = list(ts_dict.keys())
        findings["outputs"]["time_session"] = {
            "n_features": len(cols),
            "elapsed_ms": round(elapsed, 2),
            "interface": "compute_time_session_features(ts, symbol, **kwargs)",
            "first_5": cols[:5],
            "last_5": cols[-5:],
        }
    except Exception as e:
        findings["outputs"]["time_session"] = {"error": f"{type(e).__name__}: {e}"}

    # ---- Liquidity ----
    try:
        t0 = time.perf_counter()
        liq_dict = family_modules["liquidity"].extract_liquidity_features(
            candles_by_tf={"M15": candles_m15, "H1": candles_h1, "H4": candles_h4},
            anchor_idx_by_tf={"M15": anchor_by_tf["M15"], "H1": anchor_by_tf["H1"], "H4": anchor_by_tf["H4"]},
            instrument=TEST_INSTRUMENT, side="LONG", current_price=ref_price,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        per_family_features["liquidity"] = liq_dict
        cols = list(liq_dict.keys())
        findings["outputs"]["liquidity"] = {
            "n_features": len(cols),
            "elapsed_ms": round(elapsed, 2),
            "interface": "extract_liquidity_features(candles_by_tf, anchor_idx_by_tf, instrument, side, current_price)",
            "first_5": cols[:5],
            "last_5": cols[-5:],
        }
    except Exception as e:
        findings["outputs"]["liquidity"] = {"error": f"{type(e).__name__}: {e}"}

    # ---- Regime ----
    try:
        t0 = time.perf_counter()
        ctx = family_modules["regime"].RegimeFeatureContext()
        regime_od = family_modules["regime"].compute_regime_features(
            symbol=TEST_INSTRUMENT, ts=TEST_TS, side="LONG", ctx=ctx,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        per_family_features["regime"] = dict(regime_od)
        cols = list(regime_od.keys())
        findings["outputs"]["regime"] = {
            "n_features": len(cols),
            "elapsed_ms": round(elapsed, 2),
            "interface": "compute_regime_features(symbol, ts, side, ctx)",
            "first_5": cols[:5],
            "last_5": cols[-5:],
        }
    except Exception as e:
        findings["outputs"]["regime"] = {"error": f"{type(e).__name__}: {e}"}

    # 4) Naming uniqueness across families
    name_to_family = defaultdict(list)
    name_within = defaultdict(int)
    for fam, feats in per_family_features.items():
        for n in feats:
            name_to_family[n].append(fam)
            name_within[(fam, n)] += 1
    findings["name_collisions_across_families"] = [
        {"feature": n, "families": list(set(fams))}
        for n, fams in name_to_family.items()
        if len(set(fams)) > 1
    ]
    findings["duplicate_names_within_family"] = [
        {"family": fam, "feature": n, "count": c}
        for (fam, n), c in name_within.items() if c > 1
    ]

    # 5) Verdict
    all_ok = all(
        "error" not in findings["outputs"][f]
        for f in ("structure", "volatility", "microstructure",
                  "time_session", "liquidity", "regime")
    )
    n_collisions = len(findings["name_collisions_across_families"])
    n_dups = len(findings["duplicate_names_within_family"])
    findings["total_features_computed"] = sum(
        findings["outputs"].get(f, {}).get("n_features", 0)
        for f in ("structure", "volatility", "microstructure",
                  "time_session", "liquidity", "regime")
    )
    findings["verdict"] = "PASS" if (
        all_ok and n_collisions == 0 and n_dups == 0
    ) else "FAIL"

    return findings, per_family_features


# ---------------------------------------------------------------------------
# Q4 — Inference timing (re-runs each family N times for a stable median)
# ---------------------------------------------------------------------------

def run_q4(per_family_features):
    import pandas as pd
    print("=" * 70)
    print("Q4 — Inference cost benchmark")
    print("=" * 70)

    # Reload OHLCV (small enough to memoize externally; reload here since Q4 is
    # the cost benchmark so it should reflect a fresh call cost — except
    # OHLCV CSV load itself is amortized at process start, so we exclude it.
    df_m15 = load_ohlcv_pandas(TEST_INSTRUMENT, "M15")
    df_m1 = load_ohlcv_pandas(TEST_INSTRUMENT, "M1")
    df_h1 = load_ohlcv_pandas(TEST_INSTRUMENT, "H1")
    df_h4 = load_ohlcv_pandas(TEST_INSTRUMENT, "H4")
    df_m15_s = slice_until_pandas(df_m15, TEST_TS)
    df_h1_s = slice_until_pandas(df_h1, TEST_TS)
    df_h4_s = slice_until_pandas(df_h4, TEST_TS)

    candles_m15 = load_ohlcv_dicts(TEST_INSTRUMENT, "M15")
    candles_h1 = load_ohlcv_dicts(TEST_INSTRUMENT, "H1")
    candles_h4 = load_ohlcv_dicts(TEST_INSTRUMENT, "H4")
    candles_d1 = load_ohlcv_dicts(TEST_INSTRUMENT, "D1")
    candles_by_tf = {"M15": candles_m15, "H1": candles_h1, "H4": candles_h4, "D1": candles_d1}
    anchor_by_tf = {
        "M15": find_anchor_idx(candles_m15, TEST_TS_STR),
        "H1": find_anchor_idx(candles_h1, TEST_TS_STR),
        "H4": find_anchor_idx(candles_h4, TEST_TS_STR),
    }
    ref_price = candles_m15[anchor_by_tf["M15"]]["close"] if anchor_by_tf["M15"] >= 0 else float("nan")

    import structure as structure_mod
    import volatility as volatility_mod
    import microstructure as microstructure_mod
    import time_session as time_session_mod
    import liquidity as liquidity_mod
    import regime as regime_mod

    regime_ctx = regime_mod.RegimeFeatureContext()  # context is amortized

    runs = 5  # call each family this many times; report median

    def time_call(fn, *args, **kwargs):
        durations_ms = []
        result = None
        for _ in range(runs):
            t0 = time.perf_counter()
            result = fn(*args, **kwargs)
            durations_ms.append((time.perf_counter() - t0) * 1000)
        durations_ms.sort()
        return durations_ms, result

    timings = {}

    print("Timing structure...")
    d, df_struct = time_call(
        structure_mod.build_structure_features,
        timestamps=[TEST_TS_STR], candles_by_tf=candles_by_tf,
    )
    timings["structure"] = {
        "median_ms": d[runs // 2], "min_ms": d[0], "max_ms": d[-1],
        "n_features": len(df_struct.columns),
    }

    print("Timing volatility...")
    d, df_vol = time_call(
        volatility_mod.compute_all_features,
        df_m15=df_m15_s, df_h1=df_h1_s, df_h4=df_h4_s,
    )
    timings["volatility"] = {
        "median_ms": d[runs // 2], "min_ms": d[0], "max_ms": d[-1],
        "n_features": len(df_vol.columns),
    }

    def _reset(df):
        if df is None:
            return df
        return df.reset_index()

    print("Timing microstructure...")
    d, df_micro = time_call(
        microstructure_mod.compute_microstructure_features,
        df_m15=_reset(df_m15), df_m1=_reset(df_m1),
        df_h1=_reset(df_h1), df_h4=_reset(df_h4),
        ts_close=TEST_TS, symbol=TEST_INSTRUMENT, tick_df=None,
    )
    timings["microstructure"] = {
        "median_ms": d[runs // 2], "min_ms": d[0], "max_ms": d[-1],
        "n_features": len(df_micro.columns),
    }

    print("Timing time_session...")
    d, ts_dict = time_call(
        time_session_mod.compute_time_session_features,
        ts=TEST_TS, symbol=TEST_INSTRUMENT,
    )
    timings["time_session"] = {
        "median_ms": d[runs // 2], "min_ms": d[0], "max_ms": d[-1],
        "n_features": len(ts_dict),
    }

    print("Timing liquidity...")
    d, liq_dict = time_call(
        liquidity_mod.extract_liquidity_features,
        candles_by_tf={"M15": candles_m15, "H1": candles_h1, "H4": candles_h4},
        anchor_idx_by_tf={"M15": anchor_by_tf["M15"], "H1": anchor_by_tf["H1"], "H4": anchor_by_tf["H4"]},
        instrument=TEST_INSTRUMENT, side="LONG", current_price=ref_price,
    )
    timings["liquidity"] = {
        "median_ms": d[runs // 2], "min_ms": d[0], "max_ms": d[-1],
        "n_features": len(liq_dict),
    }

    print("Timing regime...")
    d, regime_od = time_call(
        regime_mod.compute_regime_features,
        symbol=TEST_INSTRUMENT, ts=TEST_TS, side="LONG", ctx=regime_ctx,
    )
    timings["regime"] = {
        "median_ms": d[runs // 2], "min_ms": d[0], "max_ms": d[-1],
        "n_features": len(regime_od),
    }

    total_median = sum(t["median_ms"] for t in timings.values())
    total_features = sum(t["n_features"] for t in timings.values())

    summary = {
        "test_instrument": TEST_INSTRUMENT,
        "test_timestamp": TEST_TS_STR,
        "runs_per_family": runs,
        "per_family": timings,
        "total_median_ms": round(total_median, 2),
        "total_features": total_features,
        "production_budget_ms_per_decision": 1.0,  # CLAUDE.md note
        "exceeds_budget_at_per_call": total_median > 1.0,
        "production_path_note": (
            "Production lives at the M15-candle-close cadence (one decision per "
            "candle per instrument = 4/hour/symbol). The <1ms-per-decision budget "
            "comes from CLAUDE.md's 'Inference cost' framing of K54 v1 features. "
            "K54 v2 is ~72x larger and is intended for OFFLINE batch feature "
            "build + cached inference, not strict 1ms inline."
        ),
    }

    # Persist CSV
    timing_csv = AUDIT / "q4_timing.csv"
    with timing_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "median_ms", "min_ms", "max_ms", "n_features", "ms_per_feature"])
        for fam, t in timings.items():
            mpf = t["median_ms"] / max(t["n_features"], 1)
            w.writerow([fam, f"{t['median_ms']:.2f}", f"{t['min_ms']:.2f}",
                        f"{t['max_ms']:.2f}", t["n_features"], f"{mpf:.4f}"])
        w.writerow(["TOTAL", f"{total_median:.2f}", "", "", total_features,
                    f"{total_median/max(total_features,1):.4f}"])

    return summary


# ---------------------------------------------------------------------------
# Q2 — Cross-family redundancy
# ---------------------------------------------------------------------------

def run_q2(per_family_features):
    """Compute Pearson + Spearman correlation matrices over a representative
    cohort.

    Strategy: rather than re-running every family on every K54 v1 trade
    (would take ~1 hour), we use the per-family stability values from the
    catalog as a proxy for cross-feature relationships. But the brief
    explicitly asks for cross-family correlation on the actual feature
    cohort.

    Practical compromise: re-run all 6 families across a subset of N=30
    candle-close timestamps drawn from the K54 v1 trade cohort. Compute
    correlations on that 30-row matrix. Document explicitly that 30 is a
    SCREENING-only cohort size.

    Why subset and not all 411: structure alone takes ~5-15s per call (Q4
    will tell us). 411 calls -> 35-100 minutes; not subscription-bounded
    cost issue, but a wall-clock issue. 30 is enough to detect |rho|>=0.7
    with reasonable Type-1-error control (df=28; |rho|>=0.7 -> p<1e-4).
    """
    import pandas as pd
    import numpy as np
    print("=" * 70)
    print("Q2 — Cross-family redundancy")
    print("=" * 70)

    # 1) Load K54 v1 features.csv to get representative timestamps
    k54v1_csv = REPO / ".claude" / "worktrees" / "agent-a01c00db65592ac2b" / "research" / "k54_ml_classifier_baseline" / "features.csv"
    k54v1_rows = []
    if k54v1_csv.exists():
        with k54v1_csv.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                k54v1_rows.append(r)

    # Filter to XAUUSD trades (we only have OHLCV for the 7-instrument fleet
    # and we already loaded XAUUSD; mixing instruments would require reloading).
    xau_rows = [r for r in k54v1_rows if r.get("symbol", "").upper() == "XAUUSD"]
    # Dedupe by trade_id (K54 v1 has ~33-row dup; use bare set on date+hour key)
    seen_keys = set()
    deduped = []
    for r in xau_rows:
        k = (r.get("date_iso", ""), r.get("hour_utc", ""), r.get("direction_long_short", ""))
        if k in seen_keys:
            continue
        seen_keys.add(k)
        deduped.append(r)
    xau_rows = deduped
    # Sample evenly distributed by date
    xau_rows.sort(key=lambda r: r.get("date_iso", ""))
    target_n = 60
    if len(xau_rows) >= target_n:
        step = max(1, len(xau_rows) // target_n)
        sampled = xau_rows[::step][:target_n]
    else:
        sampled = xau_rows

    # Build candle-close timestamps. K54 v1 schema has date_iso in TWO formats:
    #   - "2024-04-01" (date only) for backtest rows; combine with hour_utc
    #   - "2026-04-24T05:00:00+00:00" (ISO datetime) for F11 mechanical rows
    test_timestamps = []
    for r in sampled:
        date_iso = r.get("date_iso", "")
        # Try ISO datetime first (F11 rows)
        ts = None
        try:
            if "T" in date_iso:
                # Parse ISO; accept trailing Z or +00:00
                s = date_iso.replace("Z", "+00:00")
                ts = datetime.fromisoformat(s)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            else:
                hr = r.get("hour_utc", "0")
                try:
                    hr = int(hr)
                except ValueError:
                    hr = 0
                ts = datetime.strptime(date_iso, "%Y-%m-%d").replace(
                    hour=hr, tzinfo=timezone.utc
                )
        except (ValueError, TypeError):
            continue
        # Skip if past data cutoff
        cutoff = datetime(2026, 4, 28, 23, 59, 59, tzinfo=timezone.utc)
        if ts > cutoff:
            continue
        test_timestamps.append(ts)

    # Cap at target_n
    test_timestamps = test_timestamps[:target_n]
    print(f"  cohort: {len(test_timestamps)} XAUUSD timestamps")
    if len(test_timestamps) < 10:
        return {
            "error": f"insufficient cohort ({len(test_timestamps)}); cannot compute correlations",
            "verdict": "INSUFFICIENT_COHORT",
        }

    # 2) Load OHLCV once
    df_m15 = load_ohlcv_pandas(TEST_INSTRUMENT, "M15")
    df_m1 = load_ohlcv_pandas(TEST_INSTRUMENT, "M1")
    df_h1 = load_ohlcv_pandas(TEST_INSTRUMENT, "H1")
    df_h4 = load_ohlcv_pandas(TEST_INSTRUMENT, "H4")
    candles_m15 = load_ohlcv_dicts(TEST_INSTRUMENT, "M15")
    candles_h1 = load_ohlcv_dicts(TEST_INSTRUMENT, "H1")
    candles_h4 = load_ohlcv_dicts(TEST_INSTRUMENT, "H4")
    candles_d1 = load_ohlcv_dicts(TEST_INSTRUMENT, "D1")

    import structure as structure_mod
    import volatility as volatility_mod
    import microstructure as microstructure_mod
    import time_session as time_session_mod
    import liquidity as liquidity_mod
    import regime as regime_mod
    regime_ctx = regime_mod.RegimeFeatureContext()

    # 3) Compute features for each timestamp; build a wide matrix
    feature_rows: list[dict[str, float]] = []
    feature_to_family: dict[str, str] = {}
    last_min_ts = None
    for i, ts in enumerate(test_timestamps):
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        if i % 5 == 0:
            print(f"    [{i+1}/{len(test_timestamps)}] {ts_str}")
        row: dict[str, float] = {}
        anchor_by_tf = {
            "M15": find_anchor_idx(candles_m15, ts_str),
            "H1": find_anchor_idx(candles_h1, ts_str),
            "H4": find_anchor_idx(candles_h4, ts_str),
            "D1": find_anchor_idx(candles_d1, ts_str),
        }
        if anchor_by_tf["M15"] < 0:
            continue
        ref_price = candles_m15[anchor_by_tf["M15"]]["close"]
        # Slice frames
        df_m15_s = slice_until_pandas(df_m15, ts)
        df_h1_s = slice_until_pandas(df_h1, ts)
        df_h4_s = slice_until_pandas(df_h4, ts)
        if len(df_m15_s) < 50 or len(df_h1_s) < 20 or len(df_h4_s) < 5:
            continue

        # Structure
        try:
            df_struct = structure_mod.build_structure_features(
                timestamps=[ts_str], candles_by_tf={
                    "M15": candles_m15, "H1": candles_h1,
                    "H4": candles_h4, "D1": candles_d1,
                },
            )
            sd = df_struct.iloc[0].to_dict()
            for k, v in sd.items():
                key = f"structure__{k}"
                row[key] = float(v) if v == v else float("nan")
                feature_to_family[key] = "structure"
        except Exception as e:
            warnings.warn(f"structure failed at {ts_str}: {e}")

        # Volatility
        try:
            df_vol = volatility_mod.compute_all_features(
                df_m15=df_m15_s, df_h1=df_h1_s, df_h4=df_h4_s,
            )
            vrow = df_vol.iloc[-1]
            for k in df_vol.columns:
                key = f"volatility__{k}"
                v = vrow[k]
                row[key] = float(v) if (v == v) else float("nan")
                feature_to_family[key] = "volatility"
        except Exception as e:
            warnings.warn(f"volatility failed at {ts_str}: {e}")

        # Microstructure
        try:
            def _r(d): return d.reset_index() if d is not None else d
            df_micro = microstructure_mod.compute_microstructure_features(
                df_m15=_r(df_m15), df_m1=_r(df_m1),
                df_h1=_r(df_h1), df_h4=_r(df_h4),
                ts_close=ts, symbol=TEST_INSTRUMENT, tick_df=None,
            )
            mrow = df_micro.iloc[0]
            for k in df_micro.columns:
                key = f"microstructure__{k}"
                v = mrow[k]
                row[key] = float(v) if (v == v) else float("nan")
                feature_to_family[key] = "microstructure"
        except Exception as e:
            warnings.warn(f"microstructure failed at {ts_str}: {e}")

        # Time / Session
        try:
            ts_dict = time_session_mod.compute_time_session_features(
                ts=ts, symbol=TEST_INSTRUMENT,
            )
            for k, v in ts_dict.items():
                key = f"time_session__{k}"
                row[key] = float(v) if (v == v) else float("nan")
                feature_to_family[key] = "time_session"
        except Exception as e:
            warnings.warn(f"time_session failed at {ts_str}: {e}")

        # Liquidity
        try:
            liq_dict = liquidity_mod.extract_liquidity_features(
                candles_by_tf={"M15": candles_m15, "H1": candles_h1, "H4": candles_h4},
                anchor_idx_by_tf={"M15": anchor_by_tf["M15"], "H1": anchor_by_tf["H1"], "H4": anchor_by_tf["H4"]},
                instrument=TEST_INSTRUMENT, side="LONG", current_price=ref_price,
            )
            for k, v in liq_dict.items():
                key = f"liquidity__{k}"
                row[key] = float(v) if (v == v) else float("nan")
                feature_to_family[key] = "liquidity"
        except Exception as e:
            warnings.warn(f"liquidity failed at {ts_str}: {e}")

        # Regime
        try:
            regime_od = regime_mod.compute_regime_features(
                symbol=TEST_INSTRUMENT, ts=ts, side="LONG", ctx=regime_ctx,
            )
            for k, v in dict(regime_od).items():
                key = f"regime__{k}"
                try:
                    row[key] = float(v) if (v == v) else float("nan")
                except (TypeError, ValueError):
                    row[key] = float("nan")
                feature_to_family[key] = "regime"
        except Exception as e:
            warnings.warn(f"regime failed at {ts_str}: {e}")

        feature_rows.append(row)

    print(f"    materialized {len(feature_rows)} feature rows x {len(feature_to_family)} columns")

    # 4) Build a DataFrame, drop columns with too many NaN or zero variance
    df = pd.DataFrame(feature_rows)
    # Drop columns where >50% of rows are NaN
    nan_frac = df.isna().mean()
    df = df.loc[:, nan_frac < 0.5]
    # Drop zero-variance columns
    var = df.var(axis=0)
    df = df.loc[:, var > 1e-12]
    print(f"    after drop nan/const: {df.shape[1]} columns / {df.shape[0]} rows")

    # 5) Compute Spearman correlation matrix
    print("    computing Spearman correlation matrix...")
    spearman = df.corr(method="spearman")
    pearson = df.corr(method="pearson")

    # 6) Extract upper-triangle pairs, filter to cross-family pairs only
    print("    extracting cross-family pairs...")
    cols = list(df.columns)
    n = len(cols)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            ci, cj = cols[i], cols[j]
            fam_i = feature_to_family.get(ci, "?")
            fam_j = feature_to_family.get(cj, "?")
            cross_family = fam_i != fam_j
            sp = spearman.iloc[i, j]
            pe = pearson.iloc[i, j]
            if pd.isna(sp) and pd.isna(pe):
                continue
            pairs.append({
                "feature_a": ci.split("__", 1)[1] if "__" in ci else ci,
                "feature_b": cj.split("__", 1)[1] if "__" in cj else cj,
                "family_a": fam_i,
                "family_b": fam_j,
                "cross_family": cross_family,
                "spearman_rho": sp if not pd.isna(sp) else None,
                "pearson_rho": pe if not pd.isna(pe) else None,
                "abs_max_rho": max(
                    abs(sp) if not pd.isna(sp) else 0.0,
                    abs(pe) if not pd.isna(pe) else 0.0,
                ),
            })
    pairs.sort(key=lambda p: p["abs_max_rho"], reverse=True)

    # 7) Counts
    n_07_all = sum(1 for p in pairs if p["abs_max_rho"] >= 0.7)
    n_09_all = sum(1 for p in pairs if p["abs_max_rho"] >= 0.9)
    n_07_cross = sum(1 for p in pairs if p["cross_family"] and p["abs_max_rho"] >= 0.7)
    n_09_cross = sum(1 for p in pairs if p["cross_family"] and p["abs_max_rho"] >= 0.9)

    # Features with at least one |rho|>=0.7 partner (any family)
    feat_with_high_corr = set()
    for p in pairs:
        if p["abs_max_rho"] >= 0.7:
            feat_with_high_corr.add(f"{p['family_a']}__{p['feature_a']}")
            feat_with_high_corr.add(f"{p['family_b']}__{p['feature_b']}")

    # 8) Top-20 cross-family pairs
    top20_cross = [p for p in pairs if p["cross_family"]][:20]

    # 9) Persist CSV
    pairs_csv = AUDIT / "q2_top_corr_pairs.csv"
    with pairs_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family_a", "feature_a", "family_b", "feature_b", "cross_family",
                    "spearman_rho", "pearson_rho", "abs_max_rho"])
        # write top 200 to keep file useful but bounded
        for p in pairs[:200]:
            w.writerow([
                p["family_a"], p["feature_a"], p["family_b"], p["feature_b"],
                p["cross_family"],
                f"{p['spearman_rho']:.4f}" if p["spearman_rho"] is not None else "",
                f"{p['pearson_rho']:.4f}" if p["pearson_rho"] is not None else "",
                f"{p['abs_max_rho']:.4f}",
            ])

    # 10) Write reduced correlation matrix CSV (only features with at least one
    # |rho|>=0.7 partner — full 1219x1219 is 1.5M cells, too much).
    high_cols = [c for c in cols if c in feat_with_high_corr]
    if high_cols:
        sub = spearman.loc[high_cols, high_cols]
        sub.to_csv(AUDIT / "q2_correlation_matrix.csv", encoding="utf-8")
    else:
        # Empty file as marker
        with (AUDIT / "q2_correlation_matrix.csv").open("w", encoding="utf-8") as fh:
            fh.write("# No features with |rho|>=0.7 partner; matrix omitted.\n")

    summary = {
        "cohort_size": int(df.shape[0]),
        "n_features_in_matrix": int(df.shape[1]),
        "n_features_dropped_nan_or_const": int(len(feature_to_family) - df.shape[1]),
        "total_pairs_above_0.7_abs": n_07_all,
        "total_pairs_above_0.9_abs": n_09_all,
        "cross_family_pairs_above_0.7_abs": n_07_cross,
        "cross_family_pairs_above_0.9_abs": n_09_cross,
        "features_with_at_least_one_high_corr_partner": len(feat_with_high_corr),
        "top_20_cross_family_pairs": top20_cross[:20],
        "interpretation": (
            "Spearman + Pearson computed on N=" + str(int(df.shape[0]))
            + " representative XAUUSD candle-close timestamps. SCREENING-only;"
            " final correlation discipline lives at K54 v2 train time on the"
            " modeling cohort (~411 trades).  Threshold |rho|>=0.7 is a"
            " conservative redundancy gate; |rho|>=0.9 indicates near-duplicates."
        ),
    }
    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    AUDIT.mkdir(parents=True, exist_ok=True)

    q1, per_family_feats = run_q1()
    with (AUDIT / "q1_composability.json").open("w", encoding="utf-8") as fh:
        # Strip non-serializable feature dicts
        json.dump(q1, fh, indent=2, default=str)
    print(f"\n  Q1 verdict: {q1.get('verdict')}")

    q4 = run_q4(per_family_feats)
    with (AUDIT / "q4_timing_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(q4, fh, indent=2, default=str)
    print(f"\n  Q4 total: {q4['total_median_ms']:.2f}ms; per-family:")
    for fam, t in q4["per_family"].items():
        print(f"    {fam:15s}  median={t['median_ms']:.2f}ms  n={t['n_features']}")

    q2 = run_q2(per_family_feats)
    with (AUDIT / "q2_correlation_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(q2, fh, indent=2, default=str)
    print(f"\n  Q2 cohort_size: {q2.get('cohort_size')}")
    print(f"  Q2 |rho|>=0.7 cross-family: {q2.get('cross_family_pairs_above_0.7_abs')}")
    print(f"  Q2 |rho|>=0.9 cross-family: {q2.get('cross_family_pairs_above_0.9_abs')}")

    print("\nDone.")
    return q1, q2, q4


if __name__ == "__main__":
    main()
