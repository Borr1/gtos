"""DRAFT — compose COMPLETE_STATE for Policy C. NOT live-landed.

Honest PENDING / STATE_MISSING. Never invent NEWS, ATR, regime, or EXPOST.
Session 10 owns the shared composer; this is the Policy C consumer shape.
"""
from __future__ import annotations

from typing import Any, Mapping

SCHEMA = "gtos.jev.complete_state.v0"

PENDING = ("PENDING", "PENDING_SHADOW", "")


def _incomplete(v: Any) -> bool:
    return v is None or v in PENDING


def policy_c_complete_state(raw: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build typed COMPLETE_STATE. Missing news_join → STATE_MISSING (honest)."""
    src = dict(raw or {})
    news = src.get("news_join", src.get("news"))
    if news is None or news is False or news == "STATE_MISSING":
        news_join: Any = "STATE_MISSING"
    else:
        news_join = news

    identity = src.get("identity") if isinstance(src.get("identity"), Mapping) else {}
    cost = src.get("cost") if isinstance(src.get("cost"), Mapping) else {}
    occupancy = src.get("occupancy") if isinstance(src.get("occupancy"), Mapping) else {}
    account = src.get("account") if isinstance(src.get("account"), Mapping) else {}
    remint = src.get("remint") if isinstance(src.get("remint"), Mapping) else {}
    place = src.get("place_context") if isinstance(src.get("place_context"), Mapping) else {}

    voters = [
        src.get("alive", src.get("alive_sleeves")),
        src.get("regime_tag"),
        src.get("conf_band"),
        src.get("session_fit"),
    ]
    n_incomplete = int(src.get("n_incomplete") or sum(1 for v in voters if _incomplete(v)))
    full_dark = bool(src.get("full_state_dark")) or n_incomplete >= 4

    state = {
        "schema": SCHEMA,
        "symbol": src.get("symbol") or identity.get("symbol"),
        "broker_symbol": src.get("broker_symbol") or identity.get("broker_symbol"),
        "session_day": src.get("session_day") or identity.get("decision_day"),
        "decision_bar_iso": src.get("decision_bar_iso") or identity.get("decision_bar_iso"),
        "session_bucket": src.get("session_bucket") or src.get("session_fit") or "PENDING",
        "alive_sleeves": src.get("alive_sleeves") or src.get("alive") or "PENDING",
        "alive_menu": src.get("alive_menu") or [],
        "selected_sleeve_candidate": src.get("selected_sleeve_candidate") or identity.get("sleeve"),
        "conflict_set": src.get("conflict_set") or [],
        "regime_tag": src.get("regime_tag") if src.get("regime_tag") is not None else "PENDING",
        "conf_band": src.get("conf_band") or "PENDING",
        "session_fit": src.get("session_fit") or "PENDING",
        "phi": src.get("phi"),
        "phi_by_sleeve": src.get("phi_by_sleeve") or {},
        "cost": {
            "spread_r": cost.get("spread_r") or cost.get("spread_r_of_stop"),
            "total_cost_r": cost.get("total_cost_r"),
            "commission_r": cost.get("commission_r"),
            "max_total_cost_r": cost.get("max_total_cost_r"),
        },
        "occupancy": {
            "sleeve_holds_symbol": occupancy.get("sleeve_holds_symbol"),
            "broker_open_symbols": occupancy.get("broker_open_symbols"),
            "same_cycle_placed": occupancy.get("same_cycle_placed"),
            "n_open_book": occupancy.get("n_open_book") or occupancy.get("n_clusters_open"),
        },
        "account": {
            "login": account.get("login") or 0,
            "ns": account.get("ns") or "operator",
            "equity_r": account.get("equity_r"),
            "dd_wall_r": account.get("dd_wall_r"),
            "soft_daily_stop": account.get("soft_daily_stop"),
        },
        "hard_off_hit": src.get("hard_off_hit"),
        "remint": {
            "orig_stops_today": remint.get("orig_stops_today"),
            "last_exit_class": remint.get("last_exit_class"),
            "minutes_since_exit": remint.get("minutes_since_exit"),
            "two_stop_armed": remint.get("two_stop_armed"),
        },
        "news_join": news_join,
        "full_state_dark": full_dark,
        "n_incomplete": n_incomplete,
        "place_context": {
            "writer_ready": place.get("writer_ready"),
            "authority": place.get("authority"),
            "last_refusal_class": place.get("last_refusal_class"),
            "ticket_draft_fp": place.get("ticket_draft_fp"),
        },
        "identity": dict(identity),
        "clock": src.get("clock") or {},
        "sessions": src.get("sessions") or {},
        "completeness": src.get("completeness") or {
            "n_incomplete": n_incomplete,
            "full_state_dark": full_dark,
        },
        "geometry": src.get("geometry") or {},
        "timeframes": src.get("timeframes") or {},
        "news_invent": False,
        "place": False,
    }
    # Strip EXPOST if someone leaked them onto live_intent.
    for k in ("R", "mfe", "mae", "miss", "year_le0", "year_le0_geometry_proxy", "profit", "realized_pnl"):
        state.pop(k, None)
        if isinstance(state.get("identity"), dict):
            state["identity"].pop(k, None)
    return state
