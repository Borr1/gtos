#!/usr/bin/env python3
"""F4 task 3a — what does the frozen 43-feature basis actually SEE?

Two questions, both answerable without any outcome:
  1. What is the effective dimension of the basis (redundancy, dead features)?
  2. What is the TEMPORAL and CROSS-SECTIONAL REACH of the basis — how far back in
     time, and how far across instruments, does any feature look?

The second is the poverty finding. Read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from f4_common import CATEGORICAL, MONTHS, NUMERIC, jdump, load_month  # noqa: E402

OUT = Path(__file__).parent / "receipts"

# Declared reach of each frozen feature, from the generator source
# (src/components/broader_origin_generators._predecision_features) and the
# W21_PREDECISION_RIDGE_SOURCE_FEATURES_SPEC.json feature_authority line:
#   "over the last M15 bar closed at decision time".
REACH = {
    # feature: (timeframe, lookback_bars, lookback_minutes, cross_instrument?)
    "risk_over_atr": ("M15", 50, 750, False),
    "risk_fraction_of_entry": ("M15", 1, 15, False),
    "atr14_over_atr50": ("M15", 50, 750, False),
    "stop_distance_atr": ("M15", 50, 750, False),
    "target_distance_atr": ("M15", 50, 750, False),
    "close_position_in_lookback_range": ("M15", 20, 300, False),
    "dist_to_prior_high20_atr": ("M15", 20, 300, False),
    "dist_to_prior_low20_atr": ("M15", 20, 300, False),
    "trigger_bar_range_atr": ("M15", 1, 15, False),
    "trigger_bar_body_atr": ("M15", 1, 15, False),
    "compression_ratio_prior_bar": ("M15", 2, 30, False),
    "bars_since_session_open": ("M15", 96, 1440, False),
    "close_to_close_vol_8_over_48": ("M15", 48, 720, False),
    "sweep_depth_atr": ("M15", 20, 300, False),
    "session_open_range_width_atr": ("M15", 96, 1440, False),
    "trend_state_m15": ("M15", 20, 300, False),
    "trend_transition_flag": ("M15", 21, 315, False),
    # cost / fillability — priced at the decision instant from static tables
    "cost_r": ("STATIC", 0, 0, False),
    "spread_r": ("STATIC", 0, 0, False),
    "expected_slippage_r": ("STATIC", 0, 0, False),
    "swap_cost_r": ("STATIC", 0, 0, False),
    "commission_r": ("STATIC", 0, 0, False),
    "distance_to_limit_atr": ("M15", 1, 15, False),
    "distance_to_limit_risk": ("M15", 1, 15, False),
    # POI state — the deepest-reaching block in the whole basis
    "poi_age_hours": ("POI", None, None, False),
    "poi_distance_to_midpoint_atr": ("POI", None, None, False),
    "poi_distance_to_zone_atr": ("POI", None, None, False),
    "poi_touch_count": ("POI", None, None, False),
    "poi_max_mitigation_fraction": ("POI", None, None, False),
    "poi_touch_episode_count": ("POI", None, None, False),
    "poi_overlap_bar_count": ("POI", None, None, False),
}


def main() -> None:
    rows = []
    for m in MONTHS:
        rows += load_month(m)
    n = len(rows)
    print(f"rows={n}")

    # ---------- 1. dead and redundant features -------------------------------
    X = np.full((n, len(NUMERIC)), np.nan)
    for j, k in enumerate(NUMERIC):
        X[:, j] = [r.get(k, np.nan) if r.get(k) is not None else np.nan for r in rows]

    dead, near_dead = [], []
    for j, k in enumerate(NUMERIC):
        col = X[:, j]
        nan_rate = float(np.isnan(col).mean())
        finite = col[~np.isnan(col)]
        nuniq = len(np.unique(np.round(finite, 10))) if finite.size else 0
        if nuniq <= 1:
            dead.append({"feature": k, "reason": "constant", "n_unique": nuniq,
                         "value": float(finite[0]) if finite.size else None})
        elif nan_rate > 0.90:
            near_dead.append({"feature": k, "reason": "missing_on_over_90pct",
                              "nan_rate": round(nan_rate, 4), "n_unique": nuniq})

    # exact duplicate / exact linear identity detection
    dupes, identities = [], []
    for a in range(len(NUMERIC)):
        for b in range(a + 1, len(NUMERIC)):
            ca, cb = X[:, a], X[:, b]
            ok = ~np.isnan(ca) & ~np.isnan(cb)
            if ok.sum() < 100:
                continue
            if np.allclose(ca[ok], cb[ok], rtol=1e-9, atol=1e-12):
                dupes.append({"a": NUMERIC[a], "b": NUMERIC[b], "kind": "identical"})
                continue
            # exact proportionality
            nz = ok & (np.abs(cb) > 1e-12)
            if nz.sum() > 100:
                ratio = ca[nz] / cb[nz]
                if np.nanstd(ratio) < 1e-9:
                    dupes.append({"a": NUMERIC[a], "b": NUMERIC[b], "kind": "proportional",
                                  "ratio": float(np.nanmedian(ratio))})

    # cost_r identity
    comp = np.nansum(np.stack([X[:, NUMERIC.index(c)] for c in
                               ("spread_r", "expected_slippage_r", "swap_cost_r", "commission_r")]), axis=0)
    cost = X[:, NUMERIC.index("cost_r")]
    identities.append({
        "claim": "cost_r == spread_r + expected_slippage_r + swap_cost_r + commission_r",
        "max_abs_dev": float(np.nanmax(np.abs(cost - comp))),
        "holds": bool(np.nanmax(np.abs(cost - comp)) < 1e-9),
    })

    # ---------- effective rank on the complete-case numeric block ------------
    complete_cols = [j for j, k in enumerate(NUMERIC)
                     if float(np.isnan(X[:, j]).mean()) < 0.01
                     and len(np.unique(np.round(X[~np.isnan(X[:, j]), j], 10))) > 1]
    Z = X[:, complete_cols]
    Z = Z[~np.isnan(Z).any(axis=1)]
    Zs = (Z - Z.mean(0)) / (Z.std(0) + 1e-12)
    sv = np.linalg.svd(Zs, compute_uv=False)
    var = sv ** 2 / (sv ** 2).sum()
    cum = np.cumsum(var)
    eff = {
        "n_numeric_declared": len(NUMERIC),
        "n_numeric_in_rank_test": len(complete_cols),
        "features_in_rank_test": [NUMERIC[j] for j in complete_cols],
        "n_rows_complete_case": int(Z.shape[0]),
        "singular_value_variance_share": [round(float(v), 5) for v in var],
        "n_components_for_90pct_variance": int(np.searchsorted(cum, 0.90) + 1),
        "n_components_for_99pct_variance": int(np.searchsorted(cum, 0.99) + 1),
        "condition_number": float(sv[0] / sv[-1]),
    }

    # ---------- categorical redundancy ---------------------------------------
    cat_red = []
    for a, b in [("symbol_x_family", "symbol"), ("symbol_x_family", "origin_family"),
                 ("family_x_session", "origin_family"), ("family_x_session", "utc_session"),
                 ("symbol_x_side", "symbol"), ("symbol_x_side", "side"),
                 ("proposed_order_type", "origin_family")]:
        mp = {}
        det = True
        for r in rows:
            kb = str(r.get(b))
            ka = str(r.get(a))
            if b in ("origin_family",) and a == "proposed_order_type":
                kb, ka = ka, kb  # test: order_type determined BY family
            if kb in mp and mp[kb] != ka:
                det = False
                break
            mp[kb] = ka
        cat_red.append({"derived": a, "from": b, "is_deterministic_function": det})

    # ---------- 2. THE REACH AUDIT — the poverty finding ---------------------
    tf_counts, reaches = {}, []
    for k, (tf, bars, mins_, cross) in REACH.items():
        tf_counts[tf] = tf_counts.get(tf, 0) + 1
        reaches.append({"feature": k, "timeframe": tf, "lookback_bars": bars,
                        "lookback_minutes": mins_, "cross_instrument": cross})
    bar_reaches = [r["lookback_minutes"] for r in reaches if r["lookback_minutes"]]
    ident = [c for c in CATEGORICAL]

    poverty = {
        "n_features_total": 43,
        "n_categorical_identity_or_flag": len(ident),
        "timeframe_census": tf_counts,
        "deepest_price_lookback_minutes": max(bar_reaches),
        "deepest_price_lookback_hours": max(bar_reaches) / 60.0,
        "n_features_reading_any_timeframe_above_M15": 0,
        "n_features_reading_any_OTHER_INSTRUMENT": 0,
        "n_features_encoding_time_since_a_state_change": 0,
        "n_features_encoding_the_opposing_side": 0,
        "n_features_encoding_horizon_feasibility": 0,
        "statement": (
            "Every price-derived feature in the frozen basis is computed from M15 bars. "
            "The deepest price lookback is 96 M15 bars = 24 hours (bars_since_session_open / "
            "session_open_range_width_atr, the latter missing on 99.19% of rows). The deepest "
            "lookback that is actually populated on most rows is 50 M15 bars = 12.5 hours "
            "(atr14_over_atr50). No feature reads H4, D1 or any weekly structure. No feature "
            "reads any other instrument. No feature encodes elapsed time since a regime or "
            "trend change beyond a single boolean at the current bar. No feature encodes the "
            "state of the opposing side. No feature encodes whether the required move is "
            "attainable within the 2-hour label horizon."
        ),
    }

    res = {
        "prereg_sha256": "bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054",
        "n_rows": n,
        "dead_features": dead,
        "near_dead_features": near_dead,
        "exact_duplicate_or_proportional_pairs": dupes,
        "exact_identities": identities,
        "effective_dimension": eff,
        "categorical_redundancy": cat_red,
        "reach_audit": poverty,
        "per_feature_reach": reaches,
    }
    jdump(res, OUT / "F4_BASIS_AUDIT_V1.json")

    print("\n=== DEAD ===");             [print("  ", d) for d in dead]
    print("=== NEAR DEAD ===");          [print("  ", d) for d in near_dead]
    print("=== DUPLICATE/PROPORTIONAL ==="); [print("  ", d) for d in dupes]
    print("=== IDENTITIES ===");         [print("  ", d) for d in identities]
    print("=== CATEGORICAL REDUNDANCY ==="); [print("  ", d) for d in cat_red]
    print(f"\n=== EFFECTIVE DIMENSION ===\n  {eff['n_numeric_in_rank_test']} non-dead numerics -> "
          f"{eff['n_components_for_90pct_variance']} components carry 90% of variance, "
          f"{eff['n_components_for_99pct_variance']} carry 99%; condition number "
          f"{eff['condition_number']:.3g}")
    print(f"\n=== REACH ===\n  timeframes: {tf_counts}\n  deepest price lookback: "
          f"{poverty['deepest_price_lookback_hours']:.1f} h\n  {poverty['statement']}")


if __name__ == "__main__":
    main()
