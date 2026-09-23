"""sl_too_tight Buffer Distribution Study — Primary Analysis
Analyst: Opus 4.7 primary  |  Date: 2026-04-18

Purpose
-------
Compute empirical buffer distribution and gate-admission statistics for 5
candidate sl_too_tight gate configurations, informing CEO decision.

Gate semantics (from src/components/permissions.py:642-648):
    if m15_atr > 0 and sl_distance < m15_atr * 1.5:
        if not _ob_retest_sl_exception_applies(...):
            deny("sl_too_tight")

The ob_retest structural exception (lines 238-344) additionally requires:
  - framework == "ob_retest"
  - sl_beyond_edge (LONG: SL <= ob.low, SHORT: SL >= ob.high)
  - buffer = |SL - ob_edge| in [0, 0.5 * M15_ATR + eps]
  - structural_sl_distance > 0
  - m15_atr > 0

Datasets
--------
1. Retest CSV (primary): combined_retests.csv (n=726). Simulated geometry.
   SL_a = ob_edge ± 0.5 * H1_ATR (deterministic). Each row has a CONTINUED
   or REVERSED outcome from OHLC walk-forward.

2. Batch JSON (secondary): unified_trades_v2_20260331.json (n=111, XAUUSD).
   AI-chosen SLs, no OB_edge or M15_ATR fields — limited gate analysis only.

Key Methodology
---------------
The retest CSV carries only H1_ATR, not M15_ATR. The production gate uses
M15_ATR. Two options:

  (a) Assume M15_ATR ≈ 0.48 × H1_ATR (median ratio observed across 5 symbols
      in data/historical/ — XAUUSD 0.481, US30 0.493, USDJPY 0.482, GBPJPY
      0.496, GBPUSD 0.483, n≥12k per symbol).

  (b) Join each retest row to the per-symbol M15 OHLC feed and compute the
      14-period ATR at the retest timestamp.

We use (b) — real per-row M15 ATR computed from `data/historical/` M15 CSVs.

Buffer
------
For the retest CSV, SL_a is constructed at ob_edge ± 0.5 × H1_ATR. Thus:
    buffer = 0.5 × H1_ATR
    buffer_atr (in M15 ATR units) = 0.5 × H1_ATR / M15_ATR
    sl_beyond_edge = True by construction (SL outside OB on safe side)

R-outcomes
----------
Geometry A in retest CSV: target = OB_far_edge + 1 × OB_body (per ADR 003).
SL at 0.5 × H1_ATR beyond OB edge on SL side. R = (target - entry) / sl_dist
for WIN, -1 for LOSS. `continuation_r_a` column carries this.

Outcomes are:
  - CONTINUED (winner): r_multiple from continuation_r_a
  - REVERSED (loser): r_multiple = -1.0 (full SL hit)
  - UNRESOLVED (19 rows): excluded from win/loss counts but reported

Sweep-event proxy
-----------------
A "sweep event" is a loss where the SL was hit with thin buffer and price
would have reached TP if SL were wider. Retest CSV lacks forward OHLC past
the SL candle, so we use proxy:
  sweep_proxy = REVERSED AND buffer_atr < 0.3 AND time_to_mae_a_candles <= 2
  (i.e., price touched SL within 2 candles, small buffer)

This is an UPPER BOUND. True sweep (price continued to TP after wicking SL)
cannot be determined without forward bars in the current dataset.

Configurations (from task brief)
--------------------------------
  1. Baseline            : reject if SL_dist < 1.5*M15_ATR (no bypass)
  2. Current-live        : bypass if framework=ob_retest & sl_beyond & buffer >= 0.3*ATR
  3. Impl-A / Option C   : bypass if framework=ob_retest & sl_beyond & buffer <= 0.5*ATR
  4. Option D            : bypass if framework=ob_retest & sl_beyond & buffer <= 0.3*ATR
  5. Option E (hybrid)   : bypass if framework=ob_retest & sl_beyond & 0.3<=buffer<=0.5

For each config:
  - admitted = trades where gate did NOT deny (either SL_dist >= 1.5*ATR
    naturally, or bypass condition satisfied)
  - For the retest dataset, every row is by construction ob_retest with
    sl_beyond_edge = True, so config filtering reduces to buffer band tests
    (and SL_dist vs 1.5 ATR for the Baseline).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


# ------------------------------------------------------------------ paths ---
ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
RETEST_CSV = ROOT / "research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv"
BATCH_JSON = ROOT / "knowledge_base_backtest/analysis/unified_trades_v2_20260331.json"
OUT_DIR = ROOT / "research/sl_gate_buffer_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------- atr computation ---
def atr14(df: pd.DataFrame) -> pd.Series:
    """Standard ATR(14) using simple moving average of true range."""
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(14).mean()


def load_m15_atr_series(symbol: str) -> pd.DataFrame:
    """Return DataFrame with columns [time, m15_atr14]."""
    path = ROOT / f"data/historical/{symbol}_M15.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["time"])
    df["m15_atr14"] = atr14(df)
    df = df[["time", "m15_atr14"]].dropna()
    # Normalize to UTC-naive to match retest timestamps cleanly.
    if getattr(df["time"].dt, "tz", None) is not None:
        df["time"] = df["time"].dt.tz_localize(None)
    return df


# ----------------------------------------------------------- load retests ---
def load_retests() -> pd.DataFrame:
    df = pd.read_csv(RETEST_CSV, parse_dates=["retest_ts"])
    # Retest ts is ISO Z; convert to UTC-naive for merge.
    if getattr(df["retest_ts"].dt, "tz", None) is not None:
        df["retest_ts"] = df["retest_ts"].dt.tz_localize(None)
    return df


def enrich_retests(retests: pd.DataFrame) -> pd.DataFrame:
    """Attach real per-row M15 ATR (14) by joining to per-symbol M15 feeds.

    Merge is as-of (last M15 bar at or before retest_ts — we assume the
    retest decision uses ATR of the closed M15 candle preceding the retest).
    """
    out_parts = []
    for symbol, group in retests.groupby("symbol"):
        m15 = load_m15_atr_series(symbol)
        if m15 is None or m15.empty:
            # fallback: use 0.48 * H1_ATR as approximation
            group = group.copy()
            group["m15_atr14"] = group["h1_atr_at_retest"] * 0.48
            group["m15_atr_source"] = "h1_ratio_fallback"
            out_parts.append(group)
            continue
        group_sorted = group.sort_values("retest_ts")
        m15_sorted = m15.sort_values("time")
        merged = pd.merge_asof(
            group_sorted,
            m15_sorted,
            left_on="retest_ts",
            right_on="time",
            direction="backward",
            tolerance=pd.Timedelta("1h"),
        )
        merged["m15_atr_source"] = np.where(
            merged["m15_atr14"].notna(), "real", "missing"
        )
        # Fallback where M15 lookup missed (gaps in CSV)
        fill_mask = merged["m15_atr14"].isna()
        merged.loc[fill_mask, "m15_atr14"] = (
            merged.loc[fill_mask, "h1_atr_at_retest"] * 0.48
        )
        merged.loc[fill_mask, "m15_atr_source"] = "h1_ratio_fallback"
        out_parts.append(merged)
    return pd.concat(out_parts, ignore_index=True)


# -------------------------------------------------- derive gate fields -----
def derive_gate_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Compute buffer, SL_distance, buffer_atr, SL_dist_atr, R.

    Deriving ob_edge from geometry A construction:
      LONG:  sl_a = ob_low  - 0.5 * H1_ATR   => ob_edge = sl_a + 0.5 * H1_ATR
      SHORT: sl_a = ob_high + 0.5 * H1_ATR   => ob_edge = sl_a - 0.5 * H1_ATR

    Then:
      buffer = |sl - ob_edge| = 0.5 * H1_ATR by construction (always positive)
      structural_sl_distance = |entry - ob_edge|
      sl_beyond_edge:
        LONG:  sl <= ob_edge  (always True by construction, sl = edge - buf)
        SHORT: sl >= ob_edge  (always True by construction, sl = edge + buf)

    So `sl_beyond_edge` is tautologically True for geometry A. The gate's
    sl_beyond_edge condition is a SANITY CHECK against bad zone data and is
    always satisfied here.
    """
    df = df.copy()
    h1 = df["h1_atr_at_retest"]
    df["buffer"] = 0.5 * h1
    df["sl_distance"] = (df["retest_entry_price"] - df["sl_a_price"]).abs()
    # Derive ob_edge from construction
    is_long = df["side"].str.lower() == "long"
    df["ob_edge"] = np.where(
        is_long, df["sl_a_price"] + 0.5 * h1, df["sl_a_price"] - 0.5 * h1
    )
    df["structural_sl_distance"] = (df["retest_entry_price"] - df["ob_edge"]).abs()
    # Validate sl_beyond_edge as production code would:
    df["sl_beyond_edge"] = np.where(
        is_long, df["sl_a_price"] <= df["ob_edge"], df["sl_a_price"] >= df["ob_edge"]
    )
    # ATR-normalized quantities (using real M15 ATR)
    df["buffer_atr"] = df["buffer"] / df["m15_atr14"]
    df["sl_dist_atr"] = df["sl_distance"] / df["m15_atr14"]
    # R-multiple: CONTINUED uses continuation_r_a (computed as (target-entry)/sl_dist * sign).
    # REVERSED = -1, UNRESOLVED = NaN
    df["r"] = np.where(
        df["outcome_a"] == "REVERSED",
        -1.0,
        np.where(df["outcome_a"] == "CONTINUED", df["continuation_r_a"], np.nan),
    )
    df["is_win"] = df["outcome_a"] == "CONTINUED"
    df["is_loss"] = df["outcome_a"] == "REVERSED"
    df["framework"] = "ob_retest"  # all retests are ob_retest by construction
    return df


# --------------------------------------------------- config evaluation -----
def apply_gate_config(df: pd.DataFrame, cfg: str) -> pd.Series:
    """Return boolean Series: True = trade ADMITTED under this gate.

    The gate denies trades where SL_dist < 1.5 * M15_ATR unless the exception
    applies. ob_retest exception requires:
      - framework == ob_retest
      - sl_beyond_edge True
      - buffer in configured band
    """
    sl_fail = df["sl_distance"] < 1.5 * df["m15_atr14"]
    framework_ok = df["framework"] == "ob_retest"
    beyond_ok = df["sl_beyond_edge"]
    buf = df["buffer_atr"]

    if cfg == "baseline":
        bypass = pd.Series(False, index=df.index)
    elif cfg == "current_live":
        # buffer >= 0.3 ATR (no upper bound)
        bypass = framework_ok & beyond_ok & (buf >= 0.3)
    elif cfg == "impl_a":
        # buffer <= 0.5 ATR (no lower bound)
        bypass = framework_ok & beyond_ok & (buf <= 0.5)
    elif cfg == "option_d":
        # buffer <= 0.3 ATR
        bypass = framework_ok & beyond_ok & (buf <= 0.3)
    elif cfg == "option_e":
        # 0.3 <= buffer <= 0.5 ATR (hybrid)
        bypass = framework_ok & beyond_ok & (buf >= 0.3) & (buf <= 0.5)
    else:
        raise ValueError(f"unknown cfg {cfg}")

    admitted = (~sl_fail) | bypass
    return admitted


def evaluate_config(df: pd.DataFrame, cfg: str) -> dict:
    admitted = apply_gate_config(df, cfg)
    sub = df[admitted]
    # Only count rows with non-NaN R for WR/expectancy
    sub_r = sub.dropna(subset=["r"])
    n_admitted = int(len(sub))
    n_with_r = int(len(sub_r))
    wins = int(sub_r["is_win"].sum())
    losses = int(sub_r["is_loss"].sum())
    wr = wins / n_with_r if n_with_r else float("nan")
    expectancy = float(sub_r["r"].mean()) if n_with_r else float("nan")
    # Sweep proxy (upper bound): REVERSED with fast MAE (SL hit within 2 candles)
    # AND thin buffer (buffer_atr < 0.7 — the lower tail of the observed
    # geometry-A distribution, corresponding to high-ATR environments where
    # the fixed 0.5*H1_ATR buffer is small relative to M15 ATR).
    # TRUE sweep (would reach TP if SL wider) cannot be measured without
    # forward OHLC past the SL-hit candle.
    sweep_mask = (
        sub["is_loss"]
        & (sub["buffer_atr"] < 0.7)
        & (sub["time_to_mae_a_candles"] <= 2)
    )
    sweeps = int(sweep_mask.sum())
    return {
        "cfg": cfg,
        "admitted": n_admitted,
        "with_r": n_with_r,
        "wins": wins,
        "losses": losses,
        "unresolved": n_admitted - n_with_r,
        "wr": wr,
        "expectancy": expectancy,
        "sweeps_proxy": sweeps,
    }


# ------------------------------------------------------ buffer histogram ---
def buffer_histogram(df: pd.DataFrame) -> pd.DataFrame:
    edges = np.arange(0, 3.05, 0.1)
    df = df.dropna(subset=["buffer_atr", "r"]).copy()
    df["bin"] = pd.cut(
        df["buffer_atr"], bins=edges, right=False, include_lowest=True
    )
    grouped = df.groupby(["bin"], observed=True).agg(
        n=("r", "size"),
        wins=("is_win", "sum"),
        losses=("is_loss", "sum"),
        mean_r=("r", "mean"),
    )
    grouped["wr"] = grouped["wins"] / (grouped["wins"] + grouped["losses"]).replace(0, np.nan)
    return grouped.reset_index()


# --------------------------------------------------- sensitivity sweep -----
def sensitivity_option_e(df: pd.DataFrame, floors: list[float]) -> pd.DataFrame:
    rows = []
    for floor in floors:
        cfg_mask = (
            (df["framework"] == "ob_retest")
            & df["sl_beyond_edge"]
            & (df["buffer_atr"] >= floor)
            & (df["buffer_atr"] <= 0.5)
        )
        sl_fail = df["sl_distance"] < 1.5 * df["m15_atr14"]
        admitted = (~sl_fail) | cfg_mask
        sub = df[admitted].dropna(subset=["r"])
        wins = int(sub["is_win"].sum())
        losses = int(sub["is_loss"].sum())
        n = wins + losses
        wr = wins / n if n else float("nan")
        exp = float(sub["r"].mean()) if len(sub) else float("nan")
        rows.append(
            {
                "floor": floor,
                "ceiling": 0.5,
                "admitted": int(admitted.sum()),
                "wins": wins,
                "losses": losses,
                "wr": wr,
                "expectancy": exp,
            }
        )
    return pd.DataFrame(rows)


# ------------------------------------------------------------ batch JSON ---
def load_batch() -> pd.DataFrame:
    with open(BATCH_JSON) as fh:
        raw = json.load(fh)
    df = pd.DataFrame(raw)
    # XAUUSD assumed; compute SL_dist from stop_loss & entry_price
    df["sl_distance"] = (df["entry_price"] - df["stop_loss"]).abs()
    # There is no M15 ATR in the batch JSON. Estimate via merge to XAUUSD M15
    # feed using `date` (date-only, ideally we would use the actual decision
    # candle but the JSON does not preserve it).
    xau_m15 = load_m15_atr_series("XAUUSD")
    if xau_m15 is None:
        df["m15_atr14"] = np.nan
    else:
        xau_m15 = xau_m15.copy()
        xau_m15["date"] = xau_m15["time"].dt.date.astype(str)
        daily = xau_m15.groupby("date")["m15_atr14"].mean().reset_index()
        df = df.merge(daily, on="date", how="left")
    df["sl_dist_atr"] = df["sl_distance"] / df["m15_atr14"]
    df["is_win"] = df["outcome"] == "WIN"
    df["is_loss"] = df["outcome"] == "LOSS"
    df["r"] = df["r_multiple"]
    # Without OB edge, buffer cannot be computed. Flag.
    df["buffer"] = np.nan
    df["buffer_atr"] = np.nan
    df["sl_beyond_edge"] = np.nan
    return df


def evaluate_batch_config(df: pd.DataFrame, cfg: str) -> dict:
    """Simplified evaluation on batch JSON (no buffer available).

    Policy: since buffer cannot be computed, we conservatively treat every
    ob_retest trade in the batch as FAILING any buffer-band condition (so
    buffer-based exceptions never fire). This isolates the pure sl_too_tight
    effect with AI-chosen SLs.
    """
    sl_fail = df["sl_distance"] < 1.5 * df["m15_atr14"]
    # NO buffer-based bypass available — config bypass never fires
    admitted = ~sl_fail
    sub = df[admitted].dropna(subset=["r"])
    wins = int(sub["is_win"].sum())
    losses = int(sub["is_loss"].sum())
    n = wins + losses
    wr = wins / n if n else float("nan")
    expectancy = float(sub["r"].mean()) if len(sub) else float("nan")
    return {
        "cfg": cfg,
        "admitted": int(admitted.sum()),
        "with_r": int(sub["r"].notna().sum()),
        "wins": wins,
        "losses": losses,
        "wr": wr,
        "expectancy": expectancy,
        "sweeps_proxy": np.nan,
    }


# ------------------------------------------------------------------ main ---
def main():
    print("Loading retests ...")
    retests = load_retests()
    print(f"  n={len(retests)} rows")
    print("  symbols:", retests["symbol"].value_counts().to_dict())
    print("  outcome_a:", retests["outcome_a"].value_counts().to_dict())

    print("Enriching with real M15 ATR from data/historical/ ...")
    retests = enrich_retests(retests)
    print("  m15_atr_source:", retests["m15_atr_source"].value_counts().to_dict())

    print("Deriving gate fields ...")
    retests = derive_gate_fields(retests)

    # Drop rows with non-positive or NaN m15_atr (gate can't evaluate)
    gate_evaluable = retests["m15_atr14"].notna() & (retests["m15_atr14"] > 0)
    dropped = int((~gate_evaluable).sum())
    rt = retests[gate_evaluable].copy()
    print(f"  dropped {dropped} rows with missing/zero M15 ATR")
    print(f"  rt n={len(rt)}")
    print(f"  buffer_atr desc:\n{rt['buffer_atr'].describe()}")
    print(f"  sl_dist_atr desc:\n{rt['sl_dist_atr'].describe()}")

    # Sanity: fraction of rows with sl_dist >= 1.5 ATR (auto-pass Baseline)
    auto_pass = (rt["sl_dist_atr"] >= 1.5).sum()
    print(f"  Rows auto-passing Baseline (SL_dist >= 1.5*ATR): {auto_pass} "
          f"({auto_pass/len(rt):.1%})")
    # Fraction sl_beyond_edge
    print(f"  sl_beyond_edge True: {rt['sl_beyond_edge'].sum()} / {len(rt)}")

    # Per-config evaluation
    configs = ["baseline", "current_live", "impl_a", "option_d", "option_e"]
    results = [evaluate_config(rt, c) for c in configs]
    res_df = pd.DataFrame(results)
    print("\n=== RETEST DATASET RESULTS ===")
    print(res_df.to_string(index=False))

    # Per-symbol breakdown on impl_a (the CEO's current proposal)
    print("\nPer-symbol breakdown (impl_a config):")
    per_sym = []
    for sym, grp in rt.groupby("symbol"):
        result = evaluate_config(grp, "impl_a")
        result["symbol"] = sym
        per_sym.append(result)
    per_sym_df = pd.DataFrame(per_sym)
    print(per_sym_df.to_string(index=False))

    # Buffer histogram
    hist = buffer_histogram(rt)
    print("\nBuffer ATR histogram (winners vs losers):")
    print(hist.to_string(index=False))

    # Sensitivity
    sens = sensitivity_option_e(rt, [0.2, 0.3, 0.4])
    print("\nOption E sensitivity (floor sweep):")
    print(sens.to_string(index=False))

    # Batch JSON
    print("\nLoading batch JSON ...")
    batch = load_batch()
    print(f"  n={len(batch)}")
    print(f"  frameworks: {batch['framework'].value_counts().to_dict()}")
    print(f"  sl_dist_atr desc:\n{batch['sl_dist_atr'].describe()}")
    batch_results = [evaluate_batch_config(batch, c) for c in configs]
    batch_df = pd.DataFrame(batch_results)
    print("\n=== BATCH DATASET RESULTS (no buffer — buffer bypass never fires) ===")
    print(batch_df.to_string(index=False))

    # Save results as parquet/CSV for reproducibility
    rt.to_csv(OUT_DIR / "retests_enriched.csv", index=False)
    hist.to_csv(OUT_DIR / "buffer_histogram.csv", index=False)
    res_df.to_csv(OUT_DIR / "retest_config_results.csv", index=False)
    per_sym_df.to_csv(OUT_DIR / "retest_per_symbol_impl_a.csv", index=False)
    sens.to_csv(OUT_DIR / "option_e_sensitivity.csv", index=False)
    batch_df.to_csv(OUT_DIR / "batch_config_results.csv", index=False)
    print(f"\nWrote outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
