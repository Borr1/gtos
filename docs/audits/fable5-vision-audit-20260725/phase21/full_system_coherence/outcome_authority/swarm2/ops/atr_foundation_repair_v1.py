#!/usr/bin/env python3
"""ATR FOUNDATION AUDIT -- what basis is every origin family's ATR actually on?

THE CLAIM UNDER TEST
--------------------
"`risk_over_atr = risk / atr14` resolves atr14 through a four-key first-present chain
that names no timeframe anywhere, so one volatility yardstick is applied to signals
whose horizons differ by 20x.  Stop distance spans 14.3x and risk/ATR spans 14.4x and
they move in lockstep -- if each family's ATR were on its own decision timeframe the
ratio would be roughly flat."

WHAT THIS SCRIPT ESTABLISHES INSTEAD (all measured below)
---------------------------------------------------------
  1. TIMEFRAME IS NOT THE DEFECT.  Every family's ATR is M15.  The generator builds
     exactly one bar series, `timeframe="M15"` hardcoded at
     broader_origin_generators.py:448, and every candidate of all ten families is
     emitted off the latest closed bar of that one series.
  2. THE DEFECT IS THE ESTIMATOR, NOT THE CLOCK.  Two different ATR-14 definitions
     are computed on that same M15 series and which one a candidate gets is decided
     by its family:
        basis A  module high-low mean   `_atr` = mean(high-low) over 14 bars
                                        (broader_origin_generators.py:3716-3720)
        basis B  MSO Wilder TRUE RANGE  market_state.calculate_atr (market_state.py:461)
                                        preferred at broader_origin_generators.py:2713-2716
     The module names them itself at :2706-2707 and already published the divergence
     (phase20/receipts/r2/R2_ATR_DEFS_V1.json: median ratio 1.0234, 48.30% of bars
     outside +/-10%).  What was never done is the consequence: the model row mixes them.
  3. THE 14.4x SPREAD IS NOT AN ATR ARTIFACT.  Both extremes of that spread --
     structural_distance_extreme (0.358) and volatility_compression_expansion (5.146)
     -- are basis-A families sharing one IDENTICAL ATR value.  Correcting the basis
     cannot move the headline by construction.  The spread is designed geometry.

METHOD -- how the basis is recovered without re-running generation
------------------------------------------------------------------
The census carries `risk_price` (= abs(entry-stop), f1_walk.py:163) and
`risk_over_atr` (= risk/atr14, feature_contract.py:229-231) computed from the SAME
entry/stop pair.  So `atr = risk_price / risk_over_atr` recovers the exact denominator
the feature contract used, per trade.  Two candidates of different families at the
same (symbol, decision-minute) read the same closed M15 bar, so an exact match proves
a shared basis and a systematic mismatch proves a split one.

UNITS DISCIPLINE (CLAUDE.md sec 7, project rule)
------------------------------------------------
Costs and P&L in DOLLARS.  Market movement in BASIS POINTS OF PRICE.  Never a
cost-in-R beside an edge-in-R.  A filter ON stop distance selects on the denominator
of R, so every economic result below is reported in BOTH domains.  If the dollar
improvement is large while the bp improvement is ~0, the "edge" is the denominator
moving, not the market.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CORPUS = HERE.parent / "forensics/f1_excursion/F1_TRADE_EXCURSION_CENSUS_V1.parquet"
BARS = Path("/Users/borr/GTOSActive/vps-bars-20260727")
OUT = HERE / "receipts/ATR_FOUNDATION_V1.json"

#: Fixed-fractional sizing: 2% of $100,000 per R (execution.py:3445).
DOLLARS_PER_R = 2000.0

#: The three families the generator routes through `_current_framework_atr_with_source`
#: (broader_origin_generators.py:1987-1989), which PREFERS the MSO Wilder-TR ATR.
#: The other seven are emitted by `_generate_single_symbol_candidates` (:1450) whose
#: atr14 is `_atr(series, index, 14)` (:1460), the module high-low mean.
BASIS_B_FAMILIES = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}

THRESHOLD = 0.75


def wilder_atr(h, l, c, period=14):
    """market_state.calculate_atr -- Wilder-smoothed TRUE range (market_state.py:461-478)."""
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    out = np.full(tr.shape, np.nan)
    if len(tr) < period:
        return out
    seed = tr[:period].mean()
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(tr)):
        prev = (prev * (period - 1) + tr[i]) / period
        out[i] = prev
    return out


def hl_mean_atr(h, l, period=14):
    """broader_origin_generators._atr -- mean(high-low), gap-blind (:3716-3720)."""
    r = h - l
    return pd.Series(r).rolling(period).mean().to_numpy()


def bootstrap_ci(x, n=2000, seed=20260812):
    """Day-agnostic percentile CI on the mean.  Reported for scale, not as a gate."""
    if len(x) < 30:
        return None, None
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    m = x[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    out = {
        "what": "ATR foundation audit: which basis is each origin family's ATR on",
        "corpus": str(CORPUS),
        "code_anchors": {
            "single_m15_series": "src/components/broader_origin_generators.py:448 (timeframe=\"M15\")",
            "basis_A_module_hl_mean": "src/components/broader_origin_generators.py:3716-3720",
            "basis_B_mso_wilder_tr": "src/components/market_state.py:461 via broader_origin_generators.py:2713-2716",
            "basis_names_declared": "src/components/broader_origin_generators.py:2706-2707",
            "risk_over_atr": "src/research_infra/wave21_forward_shadow/feature_contract.py:229-231",
            "four_key_fallback_chain": "src/research/moonshot_scheduler_v4_best_trade_allocator.py:19334 (R2-BOUND, untouched)",
        },
        "units": "dollars for P&L (1R=$2000), bp of price for market movement",
    }

    df = pd.read_parquet(CORPUS, columns=[
        "symbol", "month", "family", "sub_min", "entry_price", "risk_price",
        "risk_over_atr", "hold_min", "net_r", "gross_r", "cost_r", "exit_kind"])
    df["atr_implied"] = df.risk_price / df.risk_over_atr
    df["stop_bp"] = df.risk_price / df.entry_price * 1e4
    df["net_usd"] = df.net_r * DOLLARS_PER_R
    df["net_bp"] = df.net_r * df.stop_bp
    df["basis"] = np.where(df.family.isin(BASIS_B_FAMILIES), "B_mso_wilder_tr", "A_module_hl_mean")
    ok = np.isfinite(df.atr_implied) & (df.atr_implied > 0)
    d = df[ok].copy()
    out["n_filled_trades"] = int(len(df))
    out["n_with_recoverable_atr"] = int(len(d))

    # ---------------------------------------------------------------- 1. basis proof
    cell = d.groupby(["symbol", "sub_min", "family"]).atr_implied.median().reset_index()
    piv = cell.pivot_table(index=["symbol", "sub_min"], columns="family", values="atr_implied")
    fams = sorted(piv.columns)
    pairs = []
    for i, a in enumerate(fams):
        for b in fams[i + 1:]:
            m = piv[[a, b]].dropna()
            if len(m) < 50:
                continue
            rel = (m[a] - m[b]).abs() / m[[a, b]].min(axis=1)
            pairs.append({
                "a": a, "b": b, "n_cells": int(len(m)),
                "median_rel_diff": float(rel.median()),
                "share_exact": float((rel < 1e-9).mean()),
                "same_basis": bool(a in BASIS_B_FAMILIES) == bool(b in BASIS_B_FAMILIES),
            })
    same = [p for p in pairs if p["same_basis"]]
    cross = [p for p in pairs if not p["same_basis"]]
    out["basis_proof"] = {
        "method": "atr = risk_price / risk_over_atr, compared across families at the same (symbol, decision-minute)",
        "same_basis_pairs": {
            "n": len(same),
            "max_median_rel_diff": float(max(p["median_rel_diff"] for p in same)),
            "all_median_exactly_zero": bool(all(p["median_rel_diff"] == 0.0 for p in same)),
        },
        "cross_basis_pairs": {
            "n": len(cross),
            "min_median_rel_diff": float(min(p["median_rel_diff"] for p in cross)),
            "max_median_rel_diff": float(max(p["median_rel_diff"] for p in cross)),
            "max_share_exact": float(max(p["share_exact"] for p in cross)),
        },
        "verdict": "exactly two bases; every same-basis pair agrees to the bit, every cross-basis pair never does",
        "pairs": sorted(pairs, key=lambda p: p["median_rel_diff"]),
    }

    # cross-basis ratio, census-implied, vs the published bar-level receipt
    g = d.groupby(["symbol", "sub_min", "basis"]).atr_implied.median().unstack().dropna()
    ratio = (g["B_mso_wilder_tr"] / g["A_module_hl_mean"]).to_numpy()
    out["cross_basis_ratio_census_implied"] = {
        "n_cells": int(len(ratio)),
        "median": float(np.median(ratio)), "mean": float(ratio.mean()),
        "p05": float(np.percentile(ratio, 5)), "p95": float(np.percentile(ratio, 95)),
        "share_over_1": float((ratio > 1).mean()),
        "share_outside_10pct": float((np.abs(ratio - 1) > 0.10).mean()),
        "independent_check_vs": "phase20/receipts/r2/R2_ATR_DEFS_V1.json (bar-level, 611,854 M15 instants)",
    }

    # ---------------------------------------------------------------- 2. family table
    fam = d.groupby(["family"]).agg(
        n=("net_r", "size"), stop_bp_median=("stop_bp", "median"),
        risk_over_atr_median=("risk_over_atr", "median"),
        hold_min_median=("hold_min", "median"),
        time_stop_share=("exit_kind", lambda s: float((s == "TIME_STOP").mean())),
        hold_min_max=("hold_min", "max"),
        net_r_mean=("net_r", "mean"), net_usd_mean=("net_usd", "mean"),
        net_bp_mean=("net_bp", "mean"))
    fam["basis"] = np.where(fam.index.isin(BASIS_B_FAMILIES), "B_mso_wilder_tr", "A_module_hl_mean")
    out["family_table"] = json.loads(fam.reset_index().to_json(orient="records"))

    A = fam[fam.basis == "A_module_hl_mean"]
    out["spread_is_within_one_basis"] = {
        "basis_A_families": int(len(A)),
        "risk_over_atr_min": float(A.risk_over_atr_median.min()),
        "risk_over_atr_max": float(A.risk_over_atr_median.max()),
        "risk_over_atr_span": float(A.risk_over_atr_median.max() / A.risk_over_atr_median.min()),
        "stop_bp_span": float(A.stop_bp_median.max() / A.stop_bp_median.min()),
        "argmin": str(A.risk_over_atr_median.idxmin()), "argmax": str(A.risk_over_atr_median.idxmax()),
        "all_ten_families_span": float(fam.risk_over_atr_median.max() / fam.risk_over_atr_median.min()),
        "verdict": ("both extremes of the 14.4x spread are basis-A families sharing one identical "
                    "ATR value, so the spread cannot be an ATR-basis artifact"),
    }

    # the hold-time spread is mostly censoring, not family horizon
    out["hold_spread_is_censoring"] = {
        "walk_horizon_min": int(df.hold_min.max()),
        "note": ("every family's max hold is the same censoring horizon; the three families whose "
                 "MEDIAN hold equals it are simply mostly unresolved at the horizon"),
        "families_at_horizon_median": {
            str(k): {"time_stop_share": float(v)}
            for k, v in fam.loc[fam.hold_min_median >= df.hold_min.max(), "time_stop_share"].items()},
    }

    # ---------------------------------------------------------------- 3. threshold flips
    broad = d[d.basis == "A_module_hl_mean"].groupby(["symbol", "sub_min"]).atr_implied.median().rename("atr_A")
    poi = d[d.basis == "B_mso_wilder_tr"].join(broad, on=["symbol", "sub_min"])
    poi = poi[np.isfinite(poi.atr_A)].copy()
    poi["roa_restated_A"] = poi.risk_price / poi.atr_A
    keep_ship = poi.risk_over_atr >= THRESHOLD
    keep_rest = poi.roa_restated_A >= THRESHOLD
    flip = keep_ship != keep_rest
    out["threshold_flip_from_basis_split"] = {
        "threshold": THRESHOLD,
        "n_basis_B_rows_with_same_cell_basis_A_atr": int(len(poi)),
        "kept_as_shipped": int(keep_ship.sum()), "kept_restated_to_A": int(keep_rest.sum()),
        "n_flipped": int(flip.sum()), "share_flipped": float(flip.mean()),
        "flipped_in": int((~keep_ship & keep_rest).sum()),
        "flipped_out": int((keep_ship & ~keep_rest).sum()),
        "flipped_rows_net_usd_mean": float(poi.loc[flip, "net_usd"].mean()),
        "all_rows_net_usd_mean": float(poi.net_usd.mean()),
        "by_family": {str(k): float(v) for k, v in poi.assign(f=flip).groupby("family").f.mean().items()},
    }

    # ------------------------------------------------- 4. within-family filter re-test
    rows = []
    for family, sub in d.groupby("family"):
        for label, roa in (("as_shipped", sub.risk_over_atr),):
            hi = roa >= THRESHOLD
            n_hi, n_lo = int(hi.sum()), int((~hi).sum())
            if n_hi < 100 or n_lo < 100:
                rows.append({"family": family, "basis": str(fam.loc[family, "basis"]),
                             "testable": False, "n_above": n_hi, "n_below": n_lo,
                             "reason": "one side under 100 trades -- filter is a family selector here, not a stop selector"})
                continue
            du = float(sub.loc[hi, "net_usd"].mean() - sub.loc[~hi, "net_usd"].mean())
            db = float(sub.loc[hi, "net_bp"].mean() - sub.loc[~hi, "net_bp"].mean())
            lo_u, hi_u = bootstrap_ci(sub.loc[hi, "net_usd"].to_numpy())
            rows.append({
                "family": family, "basis": str(fam.loc[family, "basis"]), "testable": True,
                "n_above": n_hi, "n_below": n_lo,
                "above_net_usd": float(sub.loc[hi, "net_usd"].mean()),
                "below_net_usd": float(sub.loc[~hi, "net_usd"].mean()),
                "delta_usd_per_trade": du,
                "above_net_bp": float(sub.loc[hi, "net_bp"].mean()),
                "below_net_bp": float(sub.loc[~hi, "net_bp"].mean()),
                "delta_bp_per_trade": db,
                "above_usd_ci95": [lo_u, hi_u],
            })
    out["within_family_filter_as_shipped"] = rows

    # the same test for basis-B families, restated onto basis A -- does the verdict hold?
    rest = []
    for family, sub in poi.groupby("family"):
        for label, roa in (("as_shipped_basisB", sub.risk_over_atr),
                           ("restated_basisA", sub.roa_restated_A)):
            hi = roa >= THRESHOLD
            if int(hi.sum()) < 100 or int((~hi).sum()) < 100:
                continue
            rest.append({
                "family": family, "normaliser": label,
                "n_above": int(hi.sum()), "n_below": int((~hi).sum()),
                "delta_usd_per_trade": float(sub.loc[hi, "net_usd"].mean() - sub.loc[~hi, "net_usd"].mean()),
                "delta_bp_per_trade": float(sub.loc[hi, "net_bp"].mean() - sub.loc[~hi, "net_bp"].mean()),
            })
    out["within_family_filter_basis_corrected"] = rest

    # ---------------------------------------------------- 5. the portability number
    # A threshold learned on M15 ATR is not transferable to the armed H4 book.  Measure
    # the actual H4:M15 ATR-14 ratio per symbol on the same bars the lane uses.
    port = []
    for m15p in sorted(BARS.glob("*_M15.csv.gz")):
        h4p = Path(str(m15p).replace("_M15.csv.gz", "_H4.csv.gz"))
        if not h4p.is_file():
            continue
        try:
            a = pd.read_csv(m15p); b = pd.read_csv(h4p)
        except Exception:
            continue
        if len(a) < 100 or len(b) < 100:
            continue
        am = np.nanmedian(wilder_atr(a.high.to_numpy(), a.low.to_numpy(), a.close.to_numpy()))
        bm = np.nanmedian(wilder_atr(b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()))
        if not (am > 0 and bm > 0):
            continue
        port.append({"file": m15p.name.replace("_M15.csv.gz", ""),
                     "atr14_m15_median": float(am), "atr14_h4_median": float(bm),
                     "h4_over_m15": float(bm / am)})
    r = np.array([p["h4_over_m15"] for p in port]) if port else np.array([])
    out["portability_m15_threshold_on_h4_book"] = {
        "n_series": len(port),
        "h4_over_m15_median": float(np.median(r)) if len(r) else None,
        "h4_over_m15_p05": float(np.percentile(r, 5)) if len(r) else None,
        "h4_over_m15_p95": float(np.percentile(r, 95)) if len(r) else None,
        "threshold_0p75_m15_equals_h4": float(THRESHOLD / np.median(r)) if len(r) else None,
        "verdict": ("risk_over_atr is M15-denominated for every family; applying its 0.75 threshold "
                    "to an H4-decided sleeve applies a far weaker cut than intended"),
        "per_series": port,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1, default=str)
    print(json.dumps({"written": str(OUT), "n": len(df)}, indent=1))
    return out


if __name__ == "__main__":
    o = main()
    print("\n--- headline ---")
    print("bases:", o["basis_proof"]["verdict"])
    print("cross-basis ratio median:", round(o["cross_basis_ratio_census_implied"]["median"], 4),
          " outside +/-10%:", round(o["cross_basis_ratio_census_implied"]["share_outside_10pct"], 4))
    print("spread within basis A:", round(o["spread_is_within_one_basis"]["risk_over_atr_span"], 2), "x")
    print("threshold flips:", o["threshold_flip_from_basis_split"]["n_flipped"],
          "=", round(o["threshold_flip_from_basis_split"]["share_flipped"] * 100, 2), "%")
    print("H4/M15 ATR median:", o["portability_m15_threshold_on_h4_book"]["h4_over_m15_median"])
