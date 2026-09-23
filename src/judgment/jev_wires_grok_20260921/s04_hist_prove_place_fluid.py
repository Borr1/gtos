"""SKETCH — Challenge file-exit hist-prove for place_action.

Does not APPLY. Does not order_send. Does not invent fills, ATR, or NEWS.
Module_ATR blotter is a tagged secondary lens; never merge Dig_3R / Edge_ATR R.
"""

from __future__ import annotations

# Frozen before read (Challenge_file_exit PASS)
BARS = {
    "min_decidable": 20,
    "min_jev_ok": 20,
    "n_invented_high": 0,
    "n_invented_atr": 0,
    "n_refused_cost_skip": 0,
    "sumR_delta_gt": 0.0,
    "fire_rate_max_mult": 1.15,
    "keep_win_tickets": ("291816474", "293540988", "291794419"),
}

LENS_CHALLENGE = "Challenge_file_exit"
LENS_MODULE_ATR = "Module_ATR"

# fill_model on Module_ATR rows — geometry proxy, not broker
MODULE_ATR_FILL = "geometry_proxy_ohlc_touch_module_ATR_exit_NOT_broker_NOT_module_exact"


def atr_named(state: dict) -> float | None:
    geo = state.get("geometry") or {}
    m15 = ((state.get("timeframes") or {}).get("m15") or {})
    for raw in (geo.get("atr14"), m15.get("atr14")):
        try:
            if raw is None or raw == "":
                continue
            val = float(raw)
        except (TypeError, ValueError):
            continue
        if val > 0:
            return val
    return None  # do not invent


def invented_high(state: dict) -> bool:
    news = state.get("news") or {}
    return bool(news.get("spine_empty") and news.get("high_in_f5_window") is True)
