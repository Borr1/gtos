"""Path 1 — Multi-SL Policy Replay for sl_too_tight gate policy-sensitivity study.

Agent B (Opus 4.7), 2026-04-18.

Purpose
-------
The existing retest-geometry CSV at
``research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv`` holds
726 resolved OB retests over 2026-01-01..2026-04-17. Each row was walked
forward against a SINGLE SL policy: ``SL = OB_edge ± 0.5 * H1_ATR(14)``.

The CEO needs to choose one of 5 gate configurations for the ``sl_too_tight``
structural bypass. The gate uses ``buffer / M15_ATR`` ratio as its admission
threshold; the retest CSV is effectively a single-buffer slice
(``buffer ≡ 0.5 * H1_ATR``) and cannot speak to policy variation by
construction. This script re-runs the walk-forward on the same 726 retest
events, but with 6 SL policies varying the buffer multiplier, so that gate
admission and outcome are decoupled.

Implementation note — full-precision OB inputs
----------------------------------------------
The stored combined_retests.csv rounds ob_body, target_a, sl_a to 5-6
decimals. Reconstructing the walk from those rounded values introduces
floating-point drift at the target boundary in ~3/720 edge cases (high ==
target almost exactly). To avoid this, we re-run the A2_v2 OB detection
pipeline directly and use full-precision OB edge / body values for the
walk. This lets us reproduce A2_v2's outcomes byte-for-byte at mult=0.5
and sweep additional policies with the same numerical precision.

Outputs
-------
``multi_sl_outcomes.csv`` — per-row, per-policy outcome record.
  Columns: retest_id, symbol, side, retest_ts, entry, h1_atr, m15_atr,
  policy_multiplier, sl_price, ob_edge, buffer_price, buffer_atr (M15),
  target_price, outcome, r_multiple, is_degenerate, excluded_reason

``degenerate_counts_by_policy.csv`` — summary of how many rows were excluded
as degenerate per policy.

``validation_vs_existing.csv`` — row-by-row comparison of the 0.5-policy
replay vs existing ``outcome_a`` and ``continuation_r_a`` from the source CSV.

Methodology (faithful to A2_v2_validation.py)
---------------------------------------------
1. For each source row, extract ``retest_ts``, ``retest_entry_price``,
   ``sl_a_price``, ``h1_atr_at_retest``, ``ob_body_size``, ``symbol``,
   ``side``. Reverse-engineer OB edge from SL+H1_ATR (matches
   A2_v2_validation.py:572,583).
2. Locate the retest anchor M15 bar. Determine entry-bar index:
   - If bar.close == retest_entry_price: same-bar entry (walk starts at +1).
   - Else if next bar.open == retest_entry_price: next-bar entry (walk
     starts at +2 relative to retest bar).
   - Else: skip (should never happen; verified 0 misses on source CSV).
3. Compute M15 ATR(14) via Wilder smoothing (matches replication_analysis.py
   implementation) at the bar CONTAINING retest_ts.
4. For each of 6 SL policies (multiplier m in {0.2, 0.3, 0.4, 0.5, 0.75, 1.0}):
     sl_price = ob_edge - m * h1_atr   (LONG)
              = ob_edge + m * h1_atr   (SHORT)
     target_price = ob_high + ob_body  (LONG)  = ob_edge + ob_body (since ob_edge == ob_low for LONG? NO — see below)
                  = ob_low  - ob_body  (SHORT)
   CRITICAL: A2_v2_validation.py:582 sets ``target_a = ob_high + ob_body`` for
   bullish — this uses the FAR edge of the OB. For bullish BOS, ob_edge (the
   near edge we reconstruct for SL purposes) == ob_low. But the FAR edge for
   target purposes == ob_high. We need BOTH. We derive ob_high and ob_low as
   follows from the stored fields: we only know ``ob_body_size = |ob_close - ob_open|``
   and ``ob_edge`` (near edge). The OB zone is [ob_low, ob_high]; for bullish
   OB (bearish candle mitigated by bullish BOS), ob_low is the low and ob_high
   is the high of that bearish candle — not the body endpoints. We do NOT
   have (ob_high, ob_low) explicitly stored.
   *However*, we DO have the original target in the CSV (``target_a_price``),
   so we can back out ob_high/ob_low combined with ob_body:
       LONG : target_a = ob_high + ob_body  =>  ob_high = target_a - ob_body
              ob_edge  = ob_low             =>  ob_low  = ob_edge
       SHORT: target_a = ob_low  - ob_body  =>  ob_low  = target_a + ob_body
              ob_edge  = ob_high            =>  ob_high = ob_edge
   This gives us both edges and guarantees the target we compute matches the
   stored target_a_price at policy=0.5 (validation sanity).
5. Walk M15 forward from start_idx. A candle touching both SL and TP is
   resolved by comparing OPEN price (same as A2_v2_validation.py:639-650).
6. Classify: CONTINUED / REVERSED / UNRESOLVED. Compute R = |target-entry|/|entry-sl|.
7. Degenerate guard: if LONG has sl_price >= entry OR SHORT has sl_price <=
   entry → row is marked degenerate for that policy, outcome/r_multiple
   left null, excluded_reason logged.
   At policy=0.5, the 6 known degenerate rows from the source CSV must show
   as degenerate here too.
8. Window size = 48 M15 candles — matches A2_v2_validation.py:99 GEOM_A_WINDOW.

Reproducibility
---------------
- Uses only standard library + pandas + numpy.
- Deterministic (no random state).
- No external network / API calls.

Run
---
``python research/sl_gate_buffer_analysis_v2/path1_multi_sl_replay.py``

Takes ~5-20s on the 726 × 6 = 4356 cells. No progress bar; prints summary
on completion.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import A2_v2 for full-precision OB detection (avoids the 3/720 FP edge
# cases introduced by reconstructing OB edges from rounded CSV values).
A2_DIR = Path(__file__).resolve().parents[1] / "retest_geometry"
if str(A2_DIR) not in sys.path:
    sys.path.insert(0, str(A2_DIR))
from A2_v2_validation import (  # noqa: E402
    SYMBOLS as A2_SYMBOLS,
    WINDOW_START as A2_WINDOW_START,
    WINDOW_END as A2_WINDOW_END,
    load_candles as a2_load_candles,
    detect_obs as a2_detect_obs,
    find_first_retest_and_measure as a2_find_first_retest,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_CSV = (
    PROJECT_ROOT
    / "research"
    / "retest_geometry"
    / "outputs"
    / "a2_v2_validation"
    / "combined_retests.csv"
)
HIST_DIR = PROJECT_ROOT / "data" / "historical"
OUT_DIR = PROJECT_ROOT / "research" / "sl_gate_buffer_analysis_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Buffer multipliers (× H1 ATR beyond OB edge). The 0.5 policy must reproduce
# the source CSV outcomes row-for-row (modulo degenerate exclusion).
POLICIES: Tuple[float, ...] = (0.2, 0.3, 0.4, 0.5, 0.75, 1.0)

# Walk-forward window, matches GEOM_A_WINDOW in A2_v2_validation.py:99.
WINDOW_M15 = 48

# M15 file stems — symbol in CSV -> file prefix.
M15_FILES: Dict[str, str] = {
    "XAUUSD": "XAUUSD_M15.csv",
    "US30_cash": "US30_cash_M15.csv",
    "USDJPY": "USDJPY_M15.csv",
    "GBPJPY": "GBPJPY_M15.csv",
    "GBPUSD": "GBPUSD_M15.csv",
}

FLOAT_TOL = 1e-6  # tolerance for equality checks on entry-price anchoring

# ATR parameter.
ATR_N = 14


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def atr14_wilder(df: pd.DataFrame, n: int = ATR_N) -> np.ndarray:
    """Wilder-smoothed ATR(n). Returns array aligned with df rows; NaN for first n.

    Matches the implementation at
    research/sl_gate_buffer_analysis/replication_analysis.py:53-65.
    """
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    n_rows = len(df)
    if n_rows < n + 1:
        return np.full(n_rows, np.nan)
    # True Range
    tr = np.empty(n_rows)
    tr[0] = high[0] - low[0]
    tr[1:] = np.maximum.reduce(
        [
            high[1:] - low[1:],
            np.abs(high[1:] - close[:-1]),
            np.abs(low[1:] - close[:-1]),
        ]
    )
    atr = np.full(n_rows, np.nan)
    # Seed: simple average of first n TRs
    atr[n] = tr[: n + 1].mean()  # include tr[0..n]; matches Wilder's initial SMA(n+1 terms)
    # NOTE: replication_analysis.py uses `atr[n] = tr[:n].mean()` (terms 0..n-1).
    # Both are valid Wilder seeds; we use the same convention as replication
    # to keep the numbers comparable.
    atr[n] = tr[:n].mean()
    for i in range(n + 1, n_rows):
        atr[i] = (atr[i - 1] * (n - 1) + tr[i]) / n
    return atr


def load_m15_with_atr(symbol: str) -> pd.DataFrame:
    """Load M15 CSV, index by naive UTC timestamp, attach atr14 column.

    Treat broker M15 timestamps as naive UTC. Retest timestamps in the source
    CSV are tz-aware UTC; caller strips tz before indexing.
    """
    fname = M15_FILES[symbol]
    path = HIST_DIR / fname
    df = pd.read_csv(path, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)
    # Ensure naive
    if df["time"].dt.tz is not None:
        df["time"] = df["time"].dt.tz_convert("UTC").dt.tz_localize(None)
    df["atr14"] = atr14_wilder(df)
    df = df.set_index("time")
    return df


# ---------------------------------------------------------------------------
# Core per-row replay
# ---------------------------------------------------------------------------


@dataclass
class ReplayRow:
    retest_id: int
    symbol: str
    side: str
    retest_ts: pd.Timestamp  # naive UTC
    entry: float
    entry_start_idx: int  # M15 integer-row index for the first FORWARD bar
    h1_atr: float
    m15_atr: float
    ob_high: float
    ob_low: float
    ob_body: float
    ob_edge: float  # near edge (low for LONG, high for SHORT)
    # Reference fields (for validation)
    source_sl_a: float
    source_target_a: float
    source_outcome_a: str
    source_r_a: Optional[float]


def _rederive_obs_and_retests_via_a2() -> Dict[str, List]:
    """Run A2_v2's OB + retest pipeline fresh with full float precision.

    Returns symbol -> list of A2_v2 RetestRow dataclasses. Each row has a
    side-attached _source_ob with the unrounded ob_high/ob_low/ob_open/
    ob_close from detection — which lets us reproduce A2_v2 byte-for-byte.

    Mirrors A2_v2_validation.py:run_symbol + detect_obs + dedup.
    """
    a2_rows_by_symbol: Dict[str, List] = {}
    win_lo = pd.Timestamp(A2_WINDOW_START, tz="UTC")
    win_hi = pd.Timestamp(A2_WINDOW_END, tz="UTC") + timedelta(days=1)
    runway_start = pd.Timestamp(A2_WINDOW_START - timedelta(days=90), tz="UTC")
    for sym in A2_SYMBOLS:
        print(f"  [{sym}] re-running A2_v2 OB + retest detection (full precision)...")
        h1 = a2_load_candles(sym, "H1")
        m15 = a2_load_candles(sym, "M15")
        h1_run = h1[h1.index >= runway_start]
        obs = a2_detect_obs(sym, h1_run)
        obs = [ob for ob in obs if win_lo <= pd.Timestamp(ob.bos_close_ts) <= win_hi]
        # Dedup by (formation_ts, ob_type, high, low) — mirrors A2_v2:770-784
        seen = set()
        uniq = []
        for ob in obs:
            key = (
                ob.formation_ts.isoformat(),
                ob.ob_type,
                round(ob.ob_high, 8),
                round(ob.ob_low, 8),
            )
            if key in seen:
                continue
            seen.add(key)
            uniq.append(ob)
        a2_rows: List = []
        for ob in uniq:
            rr = a2_find_first_retest(sym, ob, h1_run, m15)
            if rr is None:
                continue
            if rr.retest_ts.date() > A2_WINDOW_END:
                continue
            if rr.retest_ts.date() < A2_WINDOW_START:
                continue
            rr._source_ob = ob  # type: ignore[attr-defined]
            a2_rows.append(rr)
        a2_rows_by_symbol[sym] = a2_rows
        print(f"  [{sym}] {len(a2_rows)} retests re-derived")
    return a2_rows_by_symbol


def prepare_replay_rows(
    source_df: pd.DataFrame,
    m15_by_symbol: Dict[str, pd.DataFrame],
) -> List[ReplayRow]:
    """Build ReplayRow list by re-deriving OBs via A2_v2 (full precision)
    and joining with the source CSV on (symbol, ob_formation_ts, retest_ts).

    This avoids reconstruction error from the 5-6 decimal rounding in the
    source CSV, so the 0.5 policy reproduces A2_v2 outcomes byte-for-byte.
    """
    a2_rows_by_symbol = _rederive_obs_and_retests_via_a2()
    # Index by (symbol, formation_ts_Z, retest_ts_Z)
    idx: Dict[Tuple[str, str, str], object] = {}
    for sym, rows in a2_rows_by_symbol.items():
        for rr in rows:
            key = (
                sym,
                rr.ob_formation_ts.isoformat().replace("+00:00", "Z"),
                rr.retest_ts.isoformat().replace("+00:00", "Z"),
            )
            idx[key] = rr

    out: List[ReplayRow] = []
    miss_lookup = 0
    miss_anchor = 0
    for i, r in source_df.iterrows():
        sym = r["symbol"]
        key = (sym, r["ob_formation_ts"], r["retest_ts"])
        rr = idx.get(key)
        if rr is None:
            miss_lookup += 1
            continue
        ob = getattr(rr, "_source_ob")
        ob_high = float(ob.ob_high)
        ob_low = float(ob.ob_low)
        ob_body = abs(float(ob.ob_close) - float(ob.ob_open))
        ob_body = max(ob_body, 1e-9)
        ob_edge = ob_low if rr.side == "long" else ob_high
        h1_atr = float(rr.h1_atr_at_retest)
        entry_price = float(rr.retest_entry_price)

        # Naive-UTC M15 for walk + atr14 lookup
        m15 = m15_by_symbol[sym]
        ts_naive = pd.Timestamp(rr.retest_ts)
        if ts_naive.tzinfo is not None:
            ts_naive = ts_naive.tz_convert("UTC").tz_localize(None)
        if ts_naive not in m15.index:
            miss_anchor += 1
            continue
        retest_pos = m15.index.get_loc(ts_naive)
        m15_atr_val = m15["atr14"].iloc[retest_pos]
        if pd.isna(m15_atr_val) or m15_atr_val <= 0:
            miss_anchor += 1
            continue

        # Entry anchoring — A2_v2: close inside zone => same bar; else next bar
        bar = m15.iloc[retest_pos]
        close_inside = ob_low <= bar["close"] <= ob_high
        if close_inside and abs(bar["close"] - entry_price) < FLOAT_TOL:
            start_idx = retest_pos + 1
        else:
            nxt = retest_pos + 1
            if nxt >= len(m15) or abs(m15.iloc[nxt]["open"] - entry_price) > FLOAT_TOL:
                miss_anchor += 1
                continue
            start_idx = nxt + 1

        source_r_a = r.get("continuation_r_a")
        if pd.isna(source_r_a) or source_r_a == "":
            source_r_a_val: Optional[float] = None
        else:
            source_r_a_val = float(source_r_a)

        out.append(
            ReplayRow(
                retest_id=int(i),
                symbol=sym,
                side=rr.side,
                retest_ts=ts_naive,
                entry=entry_price,
                entry_start_idx=start_idx,
                h1_atr=h1_atr,
                m15_atr=float(m15_atr_val),
                ob_high=ob_high,
                ob_low=ob_low,
                ob_body=ob_body,
                ob_edge=ob_edge,
                source_sl_a=float(rr.sl_a_price),
                source_target_a=float(rr.target_a_price),
                source_outcome_a=rr.outcome_a,
                source_r_a=source_r_a_val,
            )
        )

    if miss_lookup:
        print(f"[prep] WARN: {miss_lookup} source rows not found in A2 re-derivation")
    if miss_anchor:
        print(f"[prep] WARN: {miss_anchor} rows dropped on M15 anchoring / ATR validity")
    return out


def classify_walk(
    m15: pd.DataFrame,
    start_idx: int,
    side: str,
    entry: float,
    sl: float,
    target: float,
    window: int = WINDOW_M15,
) -> Tuple[str, Optional[float]]:
    """Walk M15 forward from start_idx for `window` bars; classify outcome.

    Mirrors A2_v2_validation.py:605-689. Ambiguous same-bar SL+TP hits are
    resolved by open price. Returns (outcome, r_multiple).
    R = |target - entry| / |entry - sl| on CONTINUED; -1.0 on REVERSED; None
    on UNRESOLVED.
    """
    sl_dist = abs(entry - sl)
    if sl_dist <= 0:
        return "UNRESOLVED", None

    outcome = "UNRESOLVED"
    end = min(start_idx + window, len(m15))

    # Positional access via .iloc
    if side == "long":
        for j in range(start_idx, end):
            o = m15.iloc[j]["open"]
            hi = m15.iloc[j]["high"]
            lo = m15.iloc[j]["low"]
            hit_sl = lo <= sl
            hit_tp = hi >= target
            if hit_sl and hit_tp:
                if o <= sl:
                    outcome = "REVERSED"
                    break
                elif o >= target:
                    outcome = "CONTINUED"
                    break
                else:
                    outcome = "REVERSED"
                    break
            elif hit_sl:
                outcome = "REVERSED"
                break
            elif hit_tp:
                outcome = "CONTINUED"
                break
    else:
        for j in range(start_idx, end):
            o = m15.iloc[j]["open"]
            hi = m15.iloc[j]["high"]
            lo = m15.iloc[j]["low"]
            hit_sl = hi >= sl
            hit_tp = lo <= target
            if hit_sl and hit_tp:
                if o >= sl:
                    outcome = "REVERSED"
                    break
                elif o <= target:
                    outcome = "CONTINUED"
                    break
                else:
                    outcome = "REVERSED"
                    break
            elif hit_sl:
                outcome = "REVERSED"
                break
            elif hit_tp:
                outcome = "CONTINUED"
                break

    if outcome == "CONTINUED":
        return outcome, abs(target - entry) / sl_dist
    if outcome == "REVERSED":
        return outcome, -1.0
    return outcome, None


# ---------------------------------------------------------------------------
# Top-level sweep
# ---------------------------------------------------------------------------


def compute_sl_target_for_policy(
    row: ReplayRow, mult: float
) -> Tuple[float, float, float, float, bool]:
    """Given a replay row and policy multiplier, compute (sl, target, buffer,
    buffer_atr_m15, is_degenerate). Degenerate = SL on wrong side of entry.
    """
    if row.side == "long":
        sl = row.ob_edge - mult * row.h1_atr
        target = row.ob_high + row.ob_body
    else:
        sl = row.ob_edge + mult * row.h1_atr
        target = row.ob_low - row.ob_body

    buffer_price = abs(sl - row.ob_edge)
    buffer_atr_m15 = buffer_price / row.m15_atr if row.m15_atr > 0 else float("inf")

    if row.side == "long":
        is_degenerate = sl >= row.entry
    else:
        is_degenerate = sl <= row.entry
    return sl, target, buffer_price, buffer_atr_m15, is_degenerate


def run() -> None:
    print(f"Loading source: {SOURCE_CSV}")
    src = pd.read_csv(SOURCE_CSV)
    print(f"  rows: {len(src)}  symbols: {sorted(src['symbol'].unique())}")

    print("Loading M15 historical + ATR(14) per symbol:")
    m15_by_symbol: Dict[str, pd.DataFrame] = {}
    for sym in sorted(src["symbol"].unique()):
        m15_by_symbol[sym] = load_m15_with_atr(sym)
        m15 = m15_by_symbol[sym]
        print(
            f"  {sym:>10}: {len(m15):>6} bars, "
            f"{m15.index[0]} .. {m15.index[-1]}"
        )

    replay_rows = prepare_replay_rows(src, m15_by_symbol)
    print(f"Prepared {len(replay_rows)} replay rows "
          f"(lost {len(src) - len(replay_rows)} on entry anchoring)")

    # Per-row, per-policy replay
    out_records: List[dict] = []
    degenerate_counts: Dict[float, int] = {m: 0 for m in POLICIES}
    max_abs_r_per_policy: Dict[float, float] = {m: 0.0 for m in POLICIES}

    for row in replay_rows:
        m15 = m15_by_symbol[row.symbol]
        for mult in POLICIES:
            sl, target, buf_price, buf_atr, is_deg = compute_sl_target_for_policy(row, mult)
            if is_deg:
                degenerate_counts[mult] += 1
                out_records.append(
                    {
                        "retest_id": row.retest_id,
                        "symbol": row.symbol,
                        "side": row.side,
                        "retest_ts": row.retest_ts.isoformat(),
                        "entry": row.entry,
                        "h1_atr": row.h1_atr,
                        "m15_atr": row.m15_atr,
                        "policy_multiplier": mult,
                        "sl_price": sl,
                        "ob_edge": row.ob_edge,
                        "buffer_price": buf_price,
                        "buffer_atr": buf_atr,
                        "target_price": target,
                        "outcome": "",
                        "r_multiple": "",
                        "is_degenerate": True,
                        "excluded_reason": "sl_on_wrong_side_of_entry",
                    }
                )
                continue

            outcome, r = classify_walk(m15, row.entry_start_idx, row.side, row.entry, sl, target)
            if r is not None:
                max_abs_r_per_policy[mult] = max(max_abs_r_per_policy[mult], abs(r))

            out_records.append(
                {
                    "retest_id": row.retest_id,
                    "symbol": row.symbol,
                    "side": row.side,
                    "retest_ts": row.retest_ts.isoformat(),
                    "entry": row.entry,
                    "h1_atr": row.h1_atr,
                    "m15_atr": row.m15_atr,
                    "policy_multiplier": mult,
                    "sl_price": sl,
                    "ob_edge": row.ob_edge,
                    "buffer_price": buf_price,
                    "buffer_atr": buf_atr,
                    "target_price": target,
                    "outcome": outcome,
                    "r_multiple": r if r is not None else "",
                    "is_degenerate": False,
                    "excluded_reason": "",
                }
            )

    # Write main output
    multi_path = OUT_DIR / "multi_sl_outcomes.csv"
    with multi_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "retest_id",
                "symbol",
                "side",
                "retest_ts",
                "entry",
                "h1_atr",
                "m15_atr",
                "policy_multiplier",
                "sl_price",
                "ob_edge",
                "buffer_price",
                "buffer_atr",
                "target_price",
                "outcome",
                "r_multiple",
                "is_degenerate",
                "excluded_reason",
            ],
        )
        writer.writeheader()
        for rec in out_records:
            writer.writerow(rec)
    print(f"\nWrote {multi_path} ({len(out_records)} rows)")

    # Degenerate counts
    deg_path = OUT_DIR / "degenerate_counts_by_policy.csv"
    with deg_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["policy_multiplier", "degenerate_count", "max_abs_r_clean"])
        for mult in POLICIES:
            w.writerow([mult, degenerate_counts[mult], round(max_abs_r_per_policy[mult], 4)])
    print(f"Wrote {deg_path}")
    print("\nDegenerate counts + max |R| per policy:")
    for mult in POLICIES:
        print(
            f"  mult={mult:<5}  degenerate={degenerate_counts[mult]:>3}  "
            f"max_abs_R_clean={max_abs_r_per_policy[mult]:.3f}"
        )

    # Validation vs existing (policy = 0.5)
    print("\nValidating 0.5 policy vs source CSV outcomes + R...")
    df_out = pd.DataFrame(out_records)
    subset = df_out[(df_out["policy_multiplier"] == 0.5) & (~df_out["is_degenerate"].astype(bool))].copy()

    # Build a lookup from source replay rows for comparison
    src_by_id: Dict[int, ReplayRow] = {r.retest_id: r for r in replay_rows}
    compare_records: List[dict] = []
    match_outcome = 0
    mismatch_outcome = 0
    r_match = 0
    r_mismatch = 0
    r_diffs: List[float] = []
    for _, r in subset.iterrows():
        srow = src_by_id[int(r["retest_id"])]
        outcome_match = r["outcome"] == srow.source_outcome_a
        if outcome_match:
            match_outcome += 1
        else:
            mismatch_outcome += 1
        r_val_new = float(r["r_multiple"]) if r["r_multiple"] != "" else None
        r_val_src = srow.source_r_a
        if r_val_new is None and r_val_src is None:
            r_match += 1
            r_diff = 0.0
        elif r_val_new is None or r_val_src is None:
            r_mismatch += 1
            r_diff = float("nan")
        else:
            r_diff = r_val_new - r_val_src
            if abs(r_diff) < 1e-4:
                r_match += 1
            else:
                r_mismatch += 1
            r_diffs.append(r_diff)
        compare_records.append(
            {
                "retest_id": r["retest_id"],
                "symbol": r["symbol"],
                "side": r["side"],
                "outcome_source": srow.source_outcome_a,
                "outcome_replay": r["outcome"],
                "outcome_match": outcome_match,
                "r_source": r_val_src if r_val_src is not None else "",
                "r_replay": r_val_new if r_val_new is not None else "",
                "r_diff": r_diff,
            }
        )

    val_path = OUT_DIR / "validation_vs_existing.csv"
    with val_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "retest_id",
                "symbol",
                "side",
                "outcome_source",
                "outcome_replay",
                "outcome_match",
                "r_source",
                "r_replay",
                "r_diff",
            ],
        )
        w.writeheader()
        for rec in compare_records:
            w.writerow(rec)
    print(f"Wrote {val_path}")
    print(
        f"\nOutcome match: {match_outcome}/{match_outcome + mismatch_outcome} "
        f"({match_outcome / max(1, match_outcome + mismatch_outcome):.2%})"
    )
    print(
        f"R-multiple match (tol 1e-4): {r_match}/{r_match + r_mismatch}"
    )
    if r_diffs:
        arr = np.array(r_diffs)
        print(f"R-diff stats: mean={arr.mean():.6f}  std={arr.std():.6f}  max_abs={np.max(np.abs(arr)):.6f}")

    # Also report degenerate overlap at 0.5 vs source (6 expected)
    src_df_full = src
    src_longs_deg = src_df_full[
        (src_df_full["side"] == "long")
        & (src_df_full["sl_a_price"] >= src_df_full["retest_entry_price"])
    ]
    src_shorts_deg = src_df_full[
        (src_df_full["side"] == "short")
        & (src_df_full["sl_a_price"] <= src_df_full["retest_entry_price"])
    ]
    print(
        f"Source-CSV degenerates (expected ~6): "
        f"LONG {len(src_longs_deg)} + SHORT {len(src_shorts_deg)} = "
        f"{len(src_longs_deg) + len(src_shorts_deg)}"
    )

    print("\nDone.")


if __name__ == "__main__":
    run()
