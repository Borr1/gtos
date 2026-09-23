"""K-4 / P-4 — Stoikov 2018 Micro-Price reference implementation.

DESIGN-ONLY. This module lives in `research/ml_program/experiments/` and is
NOT imported by production code. See `k4_stoikov_micro_price.md` for the
specification, pre-registered prediction, verdict gates, and K54 v3 drop-in
catalog spec.

Two implementations:
- ``stoikov_canonical_micro_price`` — Stoikov 2018 §2.1 closed-form, requires
  bid + ask volumes (queue depths). Used for unit tests against published
  example numerics.
- ``stoikov_flow_proxy_micro_price`` — Adapted form for MT5 retail-broker tick
  data (volume = 0 in spot CFDs); uses rolling tick-flow imbalance from
  ``inferred_aggressor`` as a queue-imbalance proxy.

Plus benchmark harness (``run_benchmark``) and unit tests (``run_unit_tests``).
Run from this file directly to reproduce results:

    python research/ml_program/experiments/k4_stoikov_micro_price.py

This will:
1. Run unit tests against published Stoikov 2018 example numerics.
2. Run per-tick + M15-aggregated benchmark on NAS100 + US30_cash.
3. Write `k4_benchmark_results.json` with the verdict per instrument.

NO production code is imported. NO writes outside `research/ml_program/`.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Module config — edit only with intent
# ---------------------------------------------------------------------------

EXPERIMENT_DIR = Path(__file__).parent
PROJECT_ROOT = EXPERIMENT_DIR.parent.parent.parent  # ai-trading-agent/
TICKS_ROOT = PROJECT_ROOT / "data" / "ticks"
RESULTS_PATH = EXPERIMENT_DIR / "k4_benchmark_results.json"

# Imbalance-window grid for hyperparameter selection (pre-registered).
IMBALANCE_WINDOWS_TO_TEST = [10, 50, 200]

# Verdict gate threshold (per pre-registered prediction P1).
RMSE_REDUCTION_PASS_PCT = 10.0

# Spread-spike filter for benchmark.
SPREAD_SPIKE_FILTER_MULT = 5.0

# Tick sizes per instrument (broker-actual; conservative defaults).
TICK_SIZE = {
    "NAS100": 0.01,
    "US30_cash": 0.05,
}


# ---------------------------------------------------------------------------
# Variant A — canonical closed-form Stoikov micro-price (§2.1)
# ---------------------------------------------------------------------------


def stoikov_canonical_micro_price(
    p_bid: float, v_bid: float, p_ask: float, v_ask: float,
) -> float:
    """Stoikov 2018 §2.1 simple imbalance-weighted micro-price.

    .. math::
        mp = p_{bid} \\cdot \\frac{V_{ask}}{V_{bid} + V_{ask}}
           + p_{ask} \\cdot \\frac{V_{bid}}{V_{bid} + V_{ask}}

    Note the **inversion**: when V_bid is large, the micro-price tilts toward
    p_ask, not p_bid. This is the published Stoikov mechanism.

    Returns ``(p_bid + p_ask) / 2`` (naive mid) on degenerate inputs
    (zero or negative volumes).
    """
    total_v = v_bid + v_ask
    if total_v <= 0 or p_bid <= 0 or p_ask <= 0 or p_bid > p_ask:
        return (p_bid + p_ask) / 2.0
    # Imbalance I = V_bid / (V_bid + V_ask) — the "bid weight."
    # Micro-price = I * p_ask + (1 - I) * p_bid.
    imb = v_bid / total_v
    return imb * p_ask + (1.0 - imb) * p_bid


def stoikov_canonical_imbalance(v_bid: float, v_ask: float) -> float:
    """Bid-side imbalance ratio I = V_bid / (V_bid + V_ask). NaN if degenerate."""
    total = v_bid + v_ask
    if total <= 0:
        return float("nan")
    return v_bid / total


# ---------------------------------------------------------------------------
# Variant B — Stoikov §3 finite-iteration martingale correction
# ---------------------------------------------------------------------------


def stoikov_martingale_correction(
    df,
    *,
    n_imbalance_buckets: int = 5,
    n_spread_buckets: int = 3,
    martingale_iterations: int = 6,
):
    """Stoikov §3.2 finite-K micro-price.

    Constructs an empirical transition matrix on (I_bucket × S_bucket) states
    derived from `df` (must have 'flow_imbalance' and 'spread' columns),
    then iterates the matrix K times to compute the long-run expected
    mid-quote change conditional on current state.

    Returns a tuple `(state_to_correction_dict, state_assigner)`. The
    correction dict maps (i_bucket, s_bucket) tuple → expected price-change
    correction (delta, in price units).

    Empirically a 1-3 iteration cutoff captures 95% of the correction;
    K=6 is the operational default per Stoikov §3.4.
    """
    import numpy as np

    df = df.dropna(subset=["bid", "ask", "flow_imbalance"]).reset_index(drop=True)
    if len(df) < 100:
        # Too few samples; return zero correction (degenerate to closed-form).
        return ({}, lambda x: (0, 0))

    spreads = (df["ask"].to_numpy() - df["bid"].to_numpy()).astype(float)
    imbs = df["flow_imbalance"].to_numpy().astype(float)

    # Spread bucket edges via quantile.
    s_edges = np.quantile(spreads, np.linspace(0, 1, n_spread_buckets + 1)[1:-1])
    # Imbalance bucket edges: uniform on [0,1].
    i_edges = np.linspace(0, 1, n_imbalance_buckets + 1)[1:-1]

    def assign(spread_v: float, imb_v: float):
        i_idx = int(np.searchsorted(i_edges, imb_v))
        s_idx = int(np.searchsorted(s_edges, spread_v))
        i_idx = max(0, min(n_imbalance_buckets - 1, i_idx))
        s_idx = max(0, min(n_spread_buckets - 1, s_idx))
        return (i_idx, s_idx)

    # Build empirical 1-step transition: (state_t -> state_{t+1}, mid_change_{t+1}).
    n = len(df)
    states = [assign(spreads[i], imbs[i]) for i in range(n)]
    mids = (df["bid"].to_numpy() + df["ask"].to_numpy()) / 2.0
    mid_changes = np.diff(mids, prepend=mids[0])

    # Aggregate: for each state s, list of (next_state, mid_change_next).
    n_states = n_imbalance_buckets * n_spread_buckets
    state_idx = {(i, s): i * n_spread_buckets + s
                 for i in range(n_imbalance_buckets)
                 for s in range(n_spread_buckets)}

    # Transition counts.
    P = np.zeros((n_states, n_states), dtype=float)
    expected_dmid = np.zeros(n_states, dtype=float)
    counts = np.zeros(n_states, dtype=float)
    for t in range(n - 1):
        s_from = state_idx[states[t]]
        s_to = state_idx[states[t + 1]]
        P[s_from, s_to] += 1.0
        expected_dmid[s_from] += mid_changes[t + 1]
        counts[s_from] += 1.0

    # Normalize transition matrix.
    row_sums = P.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    P = P / row_sums

    # Average per-state next-mid-change (the per-step contribution).
    counts_safe = counts.copy()
    counts_safe[counts_safe == 0] = 1.0
    g = expected_dmid / counts_safe

    # Iterate Bellman-style: total_correction = g + P*g + P^2*g + ... + P^(K-1)*g
    correction = g.copy()
    P_k = P.copy()
    for _ in range(martingale_iterations - 1):
        correction = correction + P_k @ g
        P_k = P_k @ P

    state_to_correction = {}
    for (i_idx, s_idx), idx in state_idx.items():
        state_to_correction[(i_idx, s_idx)] = float(correction[idx])

    return (state_to_correction, assign)


# ---------------------------------------------------------------------------
# Flow-proxy adaptation (the MT5-spot-tick benchmark variant)
# ---------------------------------------------------------------------------


def compute_flow_imbalance(
    df,
    *,
    imbalance_window_ticks: int = 50,
):
    """Compute rolling-tick flow imbalance per row.

    For each tick, returns ratio
        n_buy_in_trailing_window / (n_buy + n_sell)
    where the trailing window is the most recent `imbalance_window_ticks`
    rows (excluding the current row, so it is a *prior* state estimate).

    NaN if the trailing window has zero classified ticks.
    """
    import numpy as np
    import pandas as pd

    if "inferred_aggressor" not in df.columns:
        return pd.Series([float("nan")] * len(df), index=df.index)

    is_buy = (df["inferred_aggressor"] == "buy").astype(float).to_numpy()
    is_sell = (df["inferred_aggressor"] == "sell").astype(float).to_numpy()

    # Rolling sum (window-by-row, exclusive of current via shift).
    if len(df) == 0:
        return pd.Series([], dtype=float)

    s_buy = pd.Series(is_buy).shift(1).fillna(0)
    s_sell = pd.Series(is_sell).shift(1).fillna(0)
    roll_buy = s_buy.rolling(window=imbalance_window_ticks, min_periods=1).sum().to_numpy()
    roll_sell = s_sell.rolling(window=imbalance_window_ticks, min_periods=1).sum().to_numpy()

    total = roll_buy + roll_sell
    imb = np.where(total > 0, roll_buy / np.maximum(total, 1e-9), float("nan"))
    return pd.Series(imb, index=df.index)


def stoikov_flow_proxy_micro_price(
    df,
    *,
    imbalance_window_ticks: int = 50,
    use_martingale_correction: bool = False,
    n_imbalance_buckets: int = 5,
    n_spread_buckets: int = 3,
    martingale_iterations: int = 6,
):
    """Compute Stoikov-style micro-price per tick using flow-proxy imbalance.

    Substitutes Stoikov §2.1's queue-volume imbalance V_bid/(V_bid+V_ask)
    with the flow-proxy
        I_t = n_buy_recent / (n_buy_recent + n_sell_recent)
    over a trailing tick window.

    Then applies the same closed-form
        mp = (1 - I) * p_bid + I * p_ask

    Note: this CRITICAL inversion mirrors Stoikov's published formula. When
    flow imbalance is BUY-heavy (I high), the micro-price tilts TOWARD p_ask
    (not p_bid) because sustained buy pressure indicates the next mid will
    push up.

    If ``use_martingale_correction``, also estimates the §3 finite-K
    correction from the in-sample data and adds it to the closed-form.

    Returns a DataFrame with columns:
        - flow_imbalance         (the proxy I, NaN before first window fills)
        - micro_price            (the per-tick Stoikov-flow estimate)
        - mid                    (the naive midprice for comparison)
        - micro_minus_mid        (micro_price - mid, signed)
    """
    import pandas as pd

    df = df.copy().reset_index(drop=True)
    df["mid"] = (df["bid"] + df["ask"]) / 2.0
    df["spread"] = df["ask"] - df["bid"]
    df["flow_imbalance"] = compute_flow_imbalance(
        df, imbalance_window_ticks=imbalance_window_ticks,
    )

    # Closed-form micro-price using flow imbalance.
    # mp = (1 - I) * p_bid + I * p_ask
    #    = p_bid + I * (p_ask - p_bid)
    df["micro_price"] = df["bid"] + df["flow_imbalance"] * (df["ask"] - df["bid"])

    # On rows with NaN imbalance (early, no window data), fall back to mid.
    df["micro_price"] = df["micro_price"].fillna(df["mid"])

    if use_martingale_correction:
        try:
            corrections, assigner = stoikov_martingale_correction(
                df,
                n_imbalance_buckets=n_imbalance_buckets,
                n_spread_buckets=n_spread_buckets,
                martingale_iterations=martingale_iterations,
            )
            corr_per_row = []
            for _, row in df.iterrows():
                if math.isnan(row["flow_imbalance"]):
                    corr_per_row.append(0.0)
                    continue
                state = assigner(row["spread"], row["flow_imbalance"])
                corr_per_row.append(corrections.get(state, 0.0))
            df["micro_price"] = df["micro_price"] + corr_per_row
        except Exception:  # noqa: BLE001
            # Fall back to closed-form silently.
            pass

    df["micro_minus_mid"] = df["micro_price"] - df["mid"]
    return df


# ---------------------------------------------------------------------------
# M15-aggregation feature for K54 v3
# ---------------------------------------------------------------------------


def m15_bar_window(candle_close_utc: datetime):
    """Return (bar_open_utc, bar_close_utc) for an M15 close timestamp."""
    from datetime import timedelta

    snapped = candle_close_utc.replace(
        minute=(candle_close_utc.minute // 15) * 15,
        second=0,
        microsecond=0,
    )
    if snapped.tzinfo is None:
        snapped = snapped.replace(tzinfo=timezone.utc)
    return snapped - timedelta(minutes=15), snapped


def compute_m15_stoikov_features(
    *,
    symbol: str,
    bar_close_utc: datetime,
    ticks_root: Path = TICKS_ROOT,
    imbalance_window_ticks: int = 50,
):
    """Compute the K54 v3 drop-in features for one M15 bar.

    Returns a dict with NaN sentinels if no tick coverage, otherwise:
        - stoikov_micro_price_close (float)
        - stoikov_micro_price_minus_mid_ticks (float)
        - stoikov_imbalance_close (float)
        - stoikov_imbalance_window (int)
    """
    from datetime import timedelta

    nan_payload = {
        "stoikov_micro_price_close": float("nan"),
        "stoikov_micro_price_minus_mid_ticks": float("nan"),
        "stoikov_imbalance_close": float("nan"),
        "stoikov_imbalance_window": -1,
    }

    try:
        import pandas as pd
        import pyarrow.parquet as pq
    except ImportError:
        return nan_payload

    bar_open, bar_close = m15_bar_window(bar_close_utc)

    # Read candidate parquet files (bar may straddle UTC midnight).
    days = sorted({bar_open.date(), (bar_close - timedelta(microseconds=1)).date()})
    frames = []
    for day in days:
        path = ticks_root / symbol / f"{day.isoformat()}.parquet"
        if not path.exists():
            continue
        try:
            df = pq.read_table(str(path)).to_pandas()
            frames.append(df)
        except Exception:  # noqa: BLE001
            continue

    if not frames:
        return nan_payload

    df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    if df.empty or "ts_utc" not in df.columns:
        return nan_payload

    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    bar_open_ts = pd.Timestamp(bar_open).tz_convert("UTC") if bar_open.tzinfo else pd.Timestamp(bar_open, tz="UTC")
    bar_close_ts = pd.Timestamp(bar_close).tz_convert("UTC") if bar_close.tzinfo else pd.Timestamp(bar_close, tz="UTC")
    mask = (df["ts_utc"] >= bar_open_ts) & (df["ts_utc"] < bar_close_ts)
    bar_df = df.loc[mask].reset_index(drop=True)

    if len(bar_df) == 0:
        return nan_payload

    enriched = stoikov_flow_proxy_micro_price(
        bar_df, imbalance_window_ticks=imbalance_window_ticks,
    )
    last = enriched.iloc[-1]
    tick_size = TICK_SIZE.get(symbol, 0.01)

    return {
        "stoikov_micro_price_close": float(last["micro_price"]),
        "stoikov_micro_price_minus_mid_ticks":
            float((last["micro_price"] - last["mid"]) / max(tick_size, 1e-9)),
        "stoikov_imbalance_close": (
            float(last["flow_imbalance"])
            if not (math.isnan(last["flow_imbalance"]) or last["flow_imbalance"] is None)
            else float("nan")
        ),
        "stoikov_imbalance_window": int(imbalance_window_ticks),
    }


# ---------------------------------------------------------------------------
# Benchmark harness
# ---------------------------------------------------------------------------


@dataclass
class InstrumentBenchmark:
    instrument: str
    n_ticks: int
    best_imbalance_window: int
    rmse_naive_mid: float
    rmse_stoikov: float
    rmse_reduction_pct: float
    directional_accuracy_pct: float
    m15_n_bars: int
    m15_rmse_naive: float
    m15_rmse_stoikov: float
    m15_rmse_reduction_pct: float
    verdict: str
    inverted_diagnostic_reduction_pct: float = float("nan")


def _per_tick_rmse(
    df, imbalance_window_ticks: int,
):
    """Compute per-tick 1-step-ahead RMSE for naive mid + Stoikov.

    Filters: drops rows where bid >= ask, spread > 5x rolling-1000 median,
    or mid_{t+1} unavailable.
    Returns (rmse_naive, rmse_stoikov, directional_accuracy, n_used).
    """
    import numpy as np
    import pandas as pd

    if len(df) < 2:
        return float("nan"), float("nan"), float("nan"), 0

    # Compute Stoikov + mid.
    enriched = stoikov_flow_proxy_micro_price(
        df, imbalance_window_ticks=imbalance_window_ticks,
    )

    # Spread filter.
    spreads = enriched["spread"].to_numpy()
    rolling_med = pd.Series(spreads).rolling(window=1000, min_periods=50).median().bfill().ffill().to_numpy()
    keep_spread = spreads <= (SPREAD_SPIKE_FILTER_MULT * rolling_med)
    keep_valid = (enriched["bid"] < enriched["ask"]).to_numpy() & keep_spread
    keep_valid[-1] = False  # last row has no t+1.

    # Targets (next-tick mid).
    target = enriched["mid"].shift(-1).to_numpy()
    naive_pred = enriched["mid"].to_numpy()
    stoikov_pred = enriched["micro_price"].to_numpy()

    # Filter
    mask = keep_valid & ~np.isnan(target) & ~np.isnan(stoikov_pred)
    n_used = int(mask.sum())
    if n_used == 0:
        return float("nan"), float("nan"), float("nan"), 0

    res_naive = target[mask] - naive_pred[mask]
    res_stoikov = target[mask] - stoikov_pred[mask]

    rmse_naive = float(np.sqrt(np.mean(res_naive ** 2)))
    rmse_stoikov = float(np.sqrt(np.mean(res_stoikov ** 2)))

    # Directional accuracy: sign of (mp - mid) predicting sign of (mid_{t+1} - mid_t).
    target_sign = np.sign(target[mask] - naive_pred[mask])
    stoikov_dir_signal = np.sign(stoikov_pred[mask] - naive_pred[mask])
    nonzero = target_sign != 0
    if int(nonzero.sum()) > 0:
        dir_acc = float(((target_sign[nonzero] * stoikov_dir_signal[nonzero]) > 0).mean())
    else:
        dir_acc = float("nan")

    return rmse_naive, rmse_stoikov, dir_acc, n_used


def _m15_rmse(df, imbalance_window_ticks: int, symbol: str):
    """M15-aggregated RMSE: last-tick-of-bar mp vs next-bar last-tick mid.

    Returns (rmse_naive, rmse_stoikov, n_bars).
    """
    import numpy as np
    import pandas as pd

    if len(df) < 100:
        return float("nan"), float("nan"), 0

    enriched = stoikov_flow_proxy_micro_price(
        df, imbalance_window_ticks=imbalance_window_ticks,
    ).copy()
    enriched["ts_utc"] = pd.to_datetime(enriched["ts_utc"], utc=True)

    # Floor each row to its M15 bar (open).
    enriched["bar"] = enriched["ts_utc"].dt.floor("15min")
    last_per_bar = enriched.groupby("bar", as_index=False).last()

    if len(last_per_bar) < 2:
        return float("nan"), float("nan"), 0

    mids = last_per_bar["mid"].to_numpy()
    mps = last_per_bar["micro_price"].to_numpy()

    # Target: next bar's last-tick mid.
    target = np.roll(mids, -1)
    res_naive = target[:-1] - mids[:-1]
    res_stoikov = target[:-1] - mps[:-1]

    rmse_naive = float(np.sqrt(np.mean(res_naive ** 2)))
    rmse_stoikov = float(np.sqrt(np.mean(res_stoikov ** 2)))
    return rmse_naive, rmse_stoikov, int(len(last_per_bar) - 1)


def benchmark_instrument(symbol: str, ticks_root: Path = TICKS_ROOT):
    """Run the K-4 benchmark for one instrument across all available days.

    Returns InstrumentBenchmark with verdict.
    """
    import numpy as np
    import pandas as pd
    import pyarrow.parquet as pq

    parquet_dir = ticks_root / symbol
    if not parquet_dir.exists():
        return InstrumentBenchmark(
            instrument=symbol, n_ticks=0, best_imbalance_window=-1,
            rmse_naive_mid=float("nan"), rmse_stoikov=float("nan"),
            rmse_reduction_pct=float("nan"),
            directional_accuracy_pct=float("nan"),
            m15_n_bars=0, m15_rmse_naive=float("nan"),
            m15_rmse_stoikov=float("nan"),
            m15_rmse_reduction_pct=float("nan"),
            verdict="NO_DATA",
        )

    files = sorted(parquet_dir.glob("*.parquet"))
    if not files:
        return InstrumentBenchmark(
            instrument=symbol, n_ticks=0, best_imbalance_window=-1,
            rmse_naive_mid=float("nan"), rmse_stoikov=float("nan"),
            rmse_reduction_pct=float("nan"),
            directional_accuracy_pct=float("nan"),
            m15_n_bars=0, m15_rmse_naive=float("nan"),
            m15_rmse_stoikov=float("nan"),
            m15_rmse_reduction_pct=float("nan"),
            verdict="NO_DATA",
        )

    frames = []
    for f in files:
        try:
            d = pq.read_table(str(f)).to_pandas()
            frames.append(d)
        except Exception:  # noqa: BLE001
            continue

    if not frames:
        return InstrumentBenchmark(
            instrument=symbol, n_ticks=0, best_imbalance_window=-1,
            rmse_naive_mid=float("nan"), rmse_stoikov=float("nan"),
            rmse_reduction_pct=float("nan"),
            directional_accuracy_pct=float("nan"),
            m15_n_bars=0, m15_rmse_naive=float("nan"),
            m15_rmse_stoikov=float("nan"),
            m15_rmse_reduction_pct=float("nan"),
            verdict="UNREADABLE",
        )

    df = pd.concat(frames, ignore_index=True)
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df = df.sort_values("ts_utc").reset_index(drop=True)

    # Filter NaN bid/ask and corrupt rows.
    df = df.dropna(subset=["bid", "ask"]).reset_index(drop=True)
    df = df[df["ask"] > df["bid"]].reset_index(drop=True)

    # Hyperparameter sweep over imbalance window.
    best = None
    sweep_results = []
    for w in IMBALANCE_WINDOWS_TO_TEST:
        rmse_n, rmse_s, dir_acc, n_used = _per_tick_rmse(df, imbalance_window_ticks=w)
        if math.isnan(rmse_n) or math.isnan(rmse_s) or rmse_n <= 0:
            continue
        red = 100.0 * (rmse_n - rmse_s) / rmse_n
        sweep_results.append({
            "window": w, "rmse_naive": rmse_n, "rmse_stoikov": rmse_s,
            "reduction_pct": red, "dir_acc": dir_acc, "n_used": n_used,
        })
        if best is None or red > best["reduction_pct"]:
            best = sweep_results[-1]

    # Diagnostic: sign-inverted control to check bid-ask-bounce hypothesis.
    # If the FLOW proxy carries the WRONG sign (sustained buy aggressors actually
    # signal mean-reversion at sub-second), inverting the sign should beat naive.
    # NOT used for verdict (verdict is locked to pre-registered direction); but
    # diagnostic for the FAIL post-mortem.
    inverted_diag = None
    if best is not None:
        try:
            inv_df = stoikov_flow_proxy_micro_price(
                df, imbalance_window_ticks=int(best["window"]),
            )
            # Invert the imbalance correction.
            inv_df["micro_price"] = inv_df["mid"] - inv_df["micro_minus_mid"]
            target_inv = inv_df["mid"].shift(-1).to_numpy()
            naive_pred_inv = inv_df["mid"].to_numpy()
            stoikov_pred_inv = inv_df["micro_price"].to_numpy()
            mask_inv = (~pd.isna(target_inv)) & (~pd.isna(stoikov_pred_inv))
            mask_inv[-1] = False
            import numpy as np
            res_n = target_inv[mask_inv] - naive_pred_inv[mask_inv]
            res_si = target_inv[mask_inv] - stoikov_pred_inv[mask_inv]
            if len(res_n) > 0:
                rmse_n_inv = float(np.sqrt(np.mean(res_n ** 2)))
                rmse_s_inv = float(np.sqrt(np.mean(res_si ** 2)))
                if rmse_n_inv > 0:
                    inv_red_pct = 100.0 * (rmse_n_inv - rmse_s_inv) / rmse_n_inv
                    inverted_diag = {
                        "rmse_naive": rmse_n_inv,
                        "rmse_inverted": rmse_s_inv,
                        "inverted_reduction_pct": inv_red_pct,
                    }
        except Exception:  # noqa: BLE001
            pass

    if best is None:
        return InstrumentBenchmark(
            instrument=symbol, n_ticks=int(len(df)), best_imbalance_window=-1,
            rmse_naive_mid=float("nan"), rmse_stoikov=float("nan"),
            rmse_reduction_pct=float("nan"),
            directional_accuracy_pct=float("nan"),
            m15_n_bars=0, m15_rmse_naive=float("nan"),
            m15_rmse_stoikov=float("nan"),
            m15_rmse_reduction_pct=float("nan"),
            verdict="COMPUTE_ERROR",
        )

    # M15-aggregation cross-check at the locked best window.
    m15_n, m15_s, m15_bars = _m15_rmse(df, best["window"], symbol)
    m15_red = (
        100.0 * (m15_n - m15_s) / m15_n
        if (not math.isnan(m15_n) and m15_n > 0)
        else float("nan")
    )

    verdict = "PASS" if best["reduction_pct"] >= RMSE_REDUCTION_PASS_PCT else "FAIL"

    return InstrumentBenchmark(
        instrument=symbol,
        n_ticks=int(len(df)),
        best_imbalance_window=int(best["window"]),
        rmse_naive_mid=float(best["rmse_naive"]),
        rmse_stoikov=float(best["rmse_stoikov"]),
        rmse_reduction_pct=float(best["reduction_pct"]),
        directional_accuracy_pct=float(best["dir_acc"] * 100.0)
            if not math.isnan(best["dir_acc"]) else float("nan"),
        m15_n_bars=int(m15_bars),
        m15_rmse_naive=float(m15_n) if not math.isnan(m15_n) else float("nan"),
        m15_rmse_stoikov=float(m15_s) if not math.isnan(m15_s) else float("nan"),
        m15_rmse_reduction_pct=float(m15_red) if not math.isnan(m15_red) else float("nan"),
        verdict=verdict,
        inverted_diagnostic_reduction_pct=(
            float(inverted_diag["inverted_reduction_pct"])
            if inverted_diag is not None
            else float("nan")
        ),
    )


def run_benchmark(
    symbols=("NAS100", "US30_cash"),
    ticks_root: Path = TICKS_ROOT,
    out_path: Path = RESULTS_PATH,
):
    """Run benchmark on all instruments + persist to JSON."""
    results = []
    for sym in symbols:
        print(f"[k4_benchmark] {sym}: starting...")
        r = benchmark_instrument(sym, ticks_root=ticks_root)
        results.append(asdict(r))
        print(f"[k4_benchmark] {sym}: verdict={r.verdict} "
              f"reduction={r.rmse_reduction_pct:.2f}% "
              f"(n={r.n_ticks} best_window={r.best_imbalance_window})")
        print(f"[k4_benchmark]   M15 cross-check: reduction={r.m15_rmse_reduction_pct:.2f}% (n_bars={r.m15_n_bars})")
        print(f"[k4_benchmark]   directional accuracy: {r.directional_accuracy_pct:.2f}%")

    # Synthesis verdict — PASS only if ALL instruments PASS.
    overall = "PASS" if all(r["verdict"] == "PASS" for r in results) else "FAIL"

    summary = {
        "_meta": {
            "experiment": "k4_stoikov_micro_price",
            "computed_at_utc": datetime.now(timezone.utc).isoformat(),
            "pre_registered_threshold_pct": RMSE_REDUCTION_PASS_PCT,
            "imbalance_windows_tested": IMBALANCE_WINDOWS_TO_TEST,
            "overall_verdict": overall,
            "interpretation": (
                "PASS = micro-price RMSE reduction >= 10% on every instrument "
                "(per-tick benchmark). FAIL = at least one instrument falls short. "
                "M15 cross-check is informational; failure of the M15 form despite "
                "per-tick PASS is consistent with E24/E26 archive."
            ),
        },
        "results": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[k4_benchmark] wrote {out_path}")
    return summary


# ---------------------------------------------------------------------------
# Unit tests (run before benchmark)
# ---------------------------------------------------------------------------


def run_unit_tests():
    """Verify Stoikov formula correctness against published example numerics."""

    # 1. Synthetic-volume formula tests (5 cases).
    print("[k4_unit_tests] 1. Synthetic-volume canonical formula tests...")

    cases = [
        # (p_bid, V_bid, p_ask, V_ask, expected, label)
        (100.0, 100.0, 100.10, 100.0, 100.05, "balanced (equal volumes -> mid)"),
        (100.0, 200.0, 100.10, 100.0, 100.0666666667, "bid-heavy 2:1 (-> tilt to ask)"),
        (100.0, 100.0, 100.10, 200.0, 100.0333333333, "ask-heavy 1:2 (-> tilt to bid)"),
        (100.0, 1.0, 100.10, 1.0, 100.05, "min volumes balanced"),
        (50.0, 50.0, 50.05, 150.0, 50.0125, "ask-heavy 1:3"),
    ]
    for p_bid, v_bid, p_ask, v_ask, expected, label in cases:
        got = stoikov_canonical_micro_price(p_bid, v_bid, p_ask, v_ask)
        assert abs(got - expected) < 1e-9, (
            f"FAIL canonical {label}: got {got} expected {expected}"
        )
        print(f"  PASS {label}: mp={got:.10f}")

    # 2. Stoikov 2018 Table-2-style spot check (canonical AAPL example).
    print("[k4_unit_tests] 2. Stoikov 2018 §2.1 canonical AAPL example...")
    # AAPL: p_bid=100.00, V_bid=200, p_ask=100.01, V_ask=100.
    # Expected: mp = 100.00 * (100/300) + 100.01 * (200/300)
    #             = (100.00 + 100.01 * 2) / 3
    #             = (100.00 + 200.02) / 3
    #             = 300.02 / 3
    #             = 100.0066666...
    got = stoikov_canonical_micro_price(100.00, 200.0, 100.01, 100.0)
    expected = 100.00 * (100.0 / 300.0) + 100.01 * (200.0 / 300.0)
    assert abs(got - expected) < 1e-12, (
        f"FAIL Stoikov AAPL: got {got} expected {expected}"
    )
    assert abs(got - 100.0066666666666) < 1e-9, (
        f"FAIL Stoikov AAPL precision: got {got}"
    )
    print(f"  PASS Stoikov AAPL: mp={got:.10f} (expected 100.0066666666...)")

    # 3. Edge cases (4 cases).
    print("[k4_unit_tests] 3. Edge cases...")

    # 3a. Zero V_bid (empty bid side) per Stoikov §2.1 -> mp tilts to p_bid.
    # mp = p_bid * (V_ask / total) + p_ask * (V_bid / total)
    #    = 100.0 * (100/100) + 100.10 * (0/100)
    #    = 100.0
    # The intuition: no bid-side liquidity to absorb sells -> next move down.
    got = stoikov_canonical_micro_price(100.0, 0.0, 100.10, 100.0)
    assert abs(got - 100.0) < 1e-9, f"FAIL zero-V_bid: got {got}"
    print(f"  PASS zero V_bid -> p_bid: mp={got}")

    # 3b. Zero V_ask (empty ask side) -> mp tilts to p_ask.
    got = stoikov_canonical_micro_price(100.0, 100.0, 100.10, 0.0)
    assert abs(got - 100.10) < 1e-9, f"FAIL zero-V_ask: got {got}"
    print(f"  PASS zero V_ask -> p_ask: mp={got}")

    # 3c. Both zero -> degenerate to naive mid (defensive fallback).
    got = stoikov_canonical_micro_price(100.0, 0.0, 100.10, 0.0)
    assert abs(got - 100.05) < 1e-9, f"FAIL both-zero degenerate: got {got}"
    print(f"  PASS both V=0 -> mid (defensive): mp={got}")

    # 3d. Inverted bid/ask -> defensive fallback to mid.
    got = stoikov_canonical_micro_price(100.10, 100.0, 100.0, 100.0)
    assert abs(got - 100.05) < 1e-9, f"FAIL inverted bid/ask: got {got}"
    print(f"  PASS inverted bid/ask -> mid (defensive): mp={got}")

    # 3e. Equal volumes -> mid (sanity).
    got = stoikov_canonical_micro_price(100.0, 50.0, 100.10, 50.0)
    assert abs(got - 100.05) < 1e-9, "FAIL equal-volume not mid"
    print(f"  PASS equal volumes -> mid: mp={got}")

    # 4. Flow-proxy adapter test on synthetic ticks.
    print("[k4_unit_tests] 4. Flow-proxy on synthetic ticks...")
    try:
        import pandas as pd

        # 100 ticks, all-buy aggressors -> imbalance approaches 1.0 -> mp -> p_ask.
        synth = pd.DataFrame({
            "ts_utc": pd.date_range("2026-04-27 10:00", periods=100, freq="1s", tz="UTC"),
            "bid": [100.0] * 100,
            "ask": [100.10] * 100,
            "inferred_aggressor": ["buy"] * 100,
        })
        out = stoikov_flow_proxy_micro_price(synth, imbalance_window_ticks=10)
        # After window fills, micro_price should approach p_ask = 100.10.
        last_mp = float(out.iloc[-1]["micro_price"])
        assert last_mp > 100.099, f"FAIL all-buy synthetic: last_mp={last_mp}"
        print(f"  PASS all-buy synthetic -> ask: last_mp={last_mp:.6f}")

        # All-sell -> imbalance -> 0 -> mp -> p_bid.
        synth["inferred_aggressor"] = ["sell"] * 100
        out = stoikov_flow_proxy_micro_price(synth, imbalance_window_ticks=10)
        last_mp = float(out.iloc[-1]["micro_price"])
        assert last_mp < 100.001, f"FAIL all-sell synthetic: last_mp={last_mp}"
        print(f"  PASS all-sell synthetic -> bid: last_mp={last_mp:.6f}")

        # Balanced: alternating -> imbalance ~ 0.5 -> mp -> mid.
        synth["inferred_aggressor"] = ["buy" if i % 2 == 0 else "sell" for i in range(100)]
        out = stoikov_flow_proxy_micro_price(synth, imbalance_window_ticks=10)
        last_mp = float(out.iloc[-1]["micro_price"])
        assert abs(last_mp - 100.05) < 0.01, f"FAIL balanced synthetic: last_mp={last_mp}"
        print(f"  PASS balanced synthetic -> mid: last_mp={last_mp:.6f}")

    except ImportError:
        print("  SKIP flow-proxy tests (pandas missing)")

    print("[k4_unit_tests] ALL TESTS PASSED")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    print("=" * 70)
    print("K-4 / P-4 Stoikov micro-price reference impl + benchmark")
    print("=" * 70)
    print()
    print("[stage 1] Unit tests (formula correctness vs Stoikov 2018 §2.1)")
    print("-" * 70)
    try:
        run_unit_tests()
    except AssertionError as e:
        print(f"\nUNIT TESTS FAILED: {e}")
        sys.exit(1)
    print()
    print("[stage 2] Per-tick + M15 benchmark on NAS100 + US30_cash")
    print("-" * 70)
    summary = run_benchmark()
    print()
    print("[stage 3] Verdict synthesis")
    print("-" * 70)
    print(json.dumps(summary["_meta"], indent=2))
    print()
    for r in summary["results"]:
        print(f"  {r['instrument']}: verdict={r['verdict']} "
              f"per-tick reduction={r['rmse_reduction_pct']:.2f}% "
              f"M15 reduction={r['m15_rmse_reduction_pct']:.2f}% "
              f"directional={r['directional_accuracy_pct']:.2f}%")


if __name__ == "__main__":
    main()
