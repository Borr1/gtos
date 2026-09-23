#!/usr/bin/env python3
"""F4 accuracy lane — shared loader, feature basis, and leak assertions.

Read-only over /private/tmp/w21-puzzle-cache. Touches nothing live.
"""
from __future__ import annotations

import gzip
import json
import pickle
from pathlib import Path

import numpy as np

CACHE = Path("/private/tmp/w21-puzzle-cache")
MONTHS = ["feb", "apr", "may", "jun", "jul"]          # read order
EVAL_FOLDS = ["apr", "may", "jun", "jul"]             # feb is training bootstrap only

# ---- the frozen 43-feature predecision basis (14 categorical + 29 numeric) ----
CATEGORICAL = [
    "symbol", "side", "origin_family", "utc_session", "proposed_order_type",
    "utc_hour", "weekday", "symbol_x_family", "family_x_session", "symbol_x_side",
    "poi_mitigation_status", "limit_marketable_at_decision",
    "trend_state_m15", "trend_transition_flag",
]
NUMERIC = [
    "cost_r", "spread_r", "expected_slippage_r", "swap_cost_r", "commission_r",
    "distance_to_limit_atr", "distance_to_limit_risk", "risk_over_atr",
    "risk_fraction_of_entry", "poi_age_hours", "poi_distance_to_midpoint_atr",
    "poi_distance_to_zone_atr", "poi_touch_count", "poi_max_mitigation_fraction",
    "poi_touch_episode_count", "poi_overlap_bar_count", "atr14_over_atr50",
    "stop_distance_atr", "target_distance_atr", "close_position_in_lookback_range",
    "dist_to_prior_high20_atr", "dist_to_prior_low20_atr", "trigger_bar_range_atr",
    "trigger_bar_body_atr", "compression_ratio_prior_bar", "bars_since_session_open",
    "close_to_close_vol_8_over_48", "sweep_depth_atr", "session_open_range_width_atr",
]
FROZEN_BASIS = CATEGORICAL + NUMERIC
assert len(FROZEN_BASIS) == 43, len(FROZEN_BASIS)

# ---- C3: anything in here may NEVER appear on the feature side ---------------
FORBIDDEN_ON_FEATURE_SIDE = {
    "terminal_net_r", "deductible_cost_r", "lifecycle_label_status",
    "cost_label_status", "pred_month_boundary", "terminal_gross_r",
    "mfe_gross_r", "mae_gross_r", "mfe_r", "mae_r", "time_to_mfe_bars",
    "label_span_end_utc", "expiry_utc", "y", "label",
}

FILLED_STATUSES = {
    "RESOLVED_FILLED_TARGET", "RESOLVED_FILLED_STOP", "RESOLVED_FILLED_TIME_STOP",
}


def assert_no_leak(feature_names) -> None:
    """C3. Raise if any outcome-bearing key reached the feature side."""
    bad = sorted(set(feature_names) & FORBIDDEN_ON_FEATURE_SIDE)
    if bad:
        raise AssertionError(f"C3 LEAK: outcome keys on the feature side: {bad}")
    for n in feature_names:
        low = str(n).lower()
        for tok in ("mfe", "mae", "excursion", "terminal", "outcome", "future", "realis", "realiz"):
            if tok in low and not low.startswith("prior_") and "atr14" not in low:
                raise AssertionError(f"C3 LEAK: feature name looks outcome-bearing: {n}")


def load_month(m: str) -> list:
    with gzip.open(CACHE / f"rows_{m}.pkl.gz", "rb") as f:
        return pickle.load(f)


def load_all() -> list:
    rows = []
    for m in MONTHS:
        rows += load_month(m)
    return rows


def enrich(rows: list) -> list:
    """Add derived OUTCOME columns only. Never touched by the feature builder."""
    for r in rows:
        st = r["lifecycle_label_status"]
        r["is_filled"] = st in FILLED_STATUSES
        net = r.get("terminal_net_r")
        ded = r.get("deductible_cost_r")
        if r["is_filled"] and net is not None and net == net:
            r["terminal_gross_r"] = net + (ded if ded is not None and ded == ded else 0.0)
        else:
            r["terminal_gross_r"] = float("nan")
    return rows


def filled(rows: list) -> list:
    return [r for r in rows if r["is_filled"]]


def dollars(r_value: float, r_per_unit: float = 500.0) -> str:
    """Representative size: 0.5% of a $100,000 account = $500 per 1R."""
    return f"${r_value * r_per_unit:,.0f}"


def jdump(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, default=_default))


def _default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))
