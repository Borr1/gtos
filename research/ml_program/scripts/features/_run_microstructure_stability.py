"""Stability scoring for the K54 v2 Microstructure feature family.

This is a one-shot research helper, not a production tool. It:

1. Loads ``research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl``
2. Filters to records whose ``ob_retest.realized_r`` is populated AND
   whose ``bos.bos_time`` is BEFORE 2026-04-01 (the pre-2026-04 boundary
   for stability scoring per the K54 v1 audit and brief).
3. For each record, computes every microstructure feature at the
   candle-close time corresponding to the BOS event.
4. Joins feature values against ``realized_r`` and computes Spearman
   rank correlation per feature.
5. Emits results to:
     - ``research/ml_program/feature_catalogs/microstructure.csv``
6. The run can also be invoked with ``--sample N`` to limit to N records
   if budget is tight.

Output schema (CSV):
    family, feature_name, source, lookback, computation_summary,
    stability_rho, stability_n, stability_p, expensive_flag

Hard constraints
================
* Data cutoff: ``ts_close < 2026-04-28 23:59 UTC``. Enforced by
  microstructure.compute_microstructure_features.
* Pre-2026-04 boundary: stability scoring only uses BOS events whose
  ``bos_time < 2026-04-01 00:00 UTC``. This guarantees the stability
  ρ values reflect "old data", not the same data K54 v2's holdout will
  cover.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Add the features dir to sys.path so we can import the sibling module
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import microstructure as m


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[4]  # repo root
DATA_DIR = ROOT / "data" / "historical_2026"
TICK_DIR = ROOT / "data" / "ticks"
F11_PATH = ROOT / "research" / "edge_decomposition" / "F11_ob_zone_original_geometry" / "population.jsonl"
OUT_CSV = ROOT / "research" / "ml_program" / "feature_catalogs" / "microstructure.csv"

PRE_2026_04 = datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_bars(symbol: str) -> dict[str, pd.DataFrame]:
    """Load M15 / M1 / H1 / H4 OHLCV CSVs for ``symbol`` from disk.

    Returns dict with empty DataFrames for missing files.
    """
    out: dict[str, pd.DataFrame] = {}
    for tf in ("M15", "M1", "H1", "H4"):
        p = DATA_DIR / f"{symbol}_{tf}.csv"
        if p.exists():
            df = pd.read_csv(p)
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            df = df.dropna(subset=["time"])
            out[tf] = df
        else:
            out[tf] = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
    return out


def _load_f11(*, sample: int | None = None) -> list[dict]:
    """Yield F11 records with ``realized_r`` populated and BOS time
    pre-2026-04. Optionally sample to ``sample`` rows.
    """
    rows = []
    with open(F11_PATH) as f:
        for line in f:
            r = json.loads(line)
            ob = r.get("ob_retest") or {}
            bos = r.get("bos") or {}
            if ob.get("realized_r") is None:
                continue
            ts_iso = bos.get("bos_time")
            if not ts_iso:
                continue
            ts = pd.Timestamp(ts_iso)
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            if ts >= pd.Timestamp(PRE_2026_04):
                continue
            rows.append({
                "symbol": bos["symbol"],
                "bos_time": ts,
                "realized_r": float(ob["realized_r"]),
            })
    rows = sorted(rows, key=lambda r: (r["symbol"], r["bos_time"]))
    if sample is not None and len(rows) > sample:
        # deterministic sample by stride
        stride = max(1, len(rows) // sample)
        rows = rows[::stride][:sample]
    return rows


def _tick_df_for(symbol: str, ts: pd.Timestamp) -> pd.DataFrame | None:
    return m.load_tick_frame_for_date(symbol, ts.strftime("%Y-%m-%d"), root=TICK_DIR)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=None,
                    help="Optional: subsample to this many F11 trades (deterministic stride).")
    ap.add_argument("--out", type=Path, default=OUT_CSV)
    args = ap.parse_args()

    print(f"[microstructure-stability] loading F11 population from {F11_PATH}")
    fills = _load_f11(sample=args.sample)
    print(f"[microstructure-stability] loaded {len(fills)} pre-2026-04 fills")
    print(f"[microstructure-stability] symbols: {sorted({f['symbol'] for f in fills})}")
    if not fills:
        raise RuntimeError("no F11 records survived the pre-2026-04 + realized_r filter")

    # Group fills by symbol so we only load each symbol's bars once.
    by_sym: dict[str, list[dict]] = {}
    for fill in fills:
        by_sym.setdefault(fill["symbol"], []).append(fill)

    feature_rows: list[dict] = []
    realized_rs: list[float] = []
    timestamps: list[pd.Timestamp] = []

    for sym, sym_fills in by_sym.items():
        print(f"[microstructure-stability] processing {sym} ({len(sym_fills)} fills)")
        bars = _load_bars(sym)
        if bars["M15"].empty:
            print(f"  ! no M15 data for {sym}; skipping")
            continue
        # Optional tick frame, by date
        tick_cache: dict[str, pd.DataFrame | None] = {}
        for fill in sym_fills:
            ts = fill["bos_time"]
            date_iso = ts.strftime("%Y-%m-%d")
            if date_iso not in tick_cache:
                tick_cache[date_iso] = m.load_tick_frame_for_date(sym, date_iso, root=TICK_DIR)
            tick_df = tick_cache[date_iso]
            try:
                feats = m.compute_microstructure_features(
                    bars["M15"], bars["M1"], bars["H1"], bars["H4"],
                    ts, symbol=sym, tick_df=tick_df,
                )
            except Exception as e:  # noqa: BLE001
                print(f"  ! compute failed at ts={ts}: {e}")
                continue
            feature_rows.append(feats.iloc[0].to_dict())
            realized_rs.append(fill["realized_r"])
            timestamps.append(ts)

    if not feature_rows:
        raise RuntimeError("no feature rows computed")

    feat_df = pd.DataFrame(feature_rows, index=timestamps)
    rs = pd.Series(realized_rs, index=timestamps)
    print(f"[microstructure-stability] computed {len(feat_df)} feature rows × {feat_df.shape[1]} cols")

    print("[microstructure-stability] computing Spearman stability scores")
    stab = m.compute_stability_for_features(feat_df, rs)

    # Top 5 by |rho|
    top5 = stab.dropna(subset=["stability_rho"]).copy()
    top5["abs_rho"] = top5["stability_rho"].abs()
    top5 = top5.sort_values("abs_rho", ascending=False).head(5)
    print("[microstructure-stability] top 5 features by |rho|:")
    for _, r in top5.iterrows():
        print(f"  {r['feature']:<55s} rho={r['stability_rho']:+.3f} n={int(r['stability_n'])} p={r['stability_p']:.3f}")

    # Emit CSV
    args.out.parent.mkdir(parents=True, exist_ok=True)
    m.emit_catalog_csv(args.out, stability=stab)
    print(f"[microstructure-stability] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
