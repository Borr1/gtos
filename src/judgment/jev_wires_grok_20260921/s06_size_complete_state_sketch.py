"""OUT-only sketch. Do not import from live writer. Never places.

Chair may copy into src/judgment/ after hist-prove. Defaults keep
physical combined = flow × cost × ca (PR41). Overlay APPLY flags stay 0.
"""

from __future__ import annotations

from typing import Any, Mapping

SCHEMA = "gtos.judgment.size_complete_state.v0"
WIRE_SIZE_MULT = "jev_size_mult_complete_state"
WIRE_CA_JEV = "ca_size_mult_jev"

FLOW_LO, FLOW_HI = 0.70, 1.15
VETO_LO, VETO_HI = 0.70, 1.00

SIZE_POSTURE = ("SIZE_FULL", "SIZE_TRIM", "SIZE_HOLD", "STAND")


def _f(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, lo: float, hi: float) -> float:
    return round(min(hi, max(lo, float(value))), 4)


def score_to_flow_tilt(score: float | None) -> float:
    if score is None:
        return 1.0
    mapped = FLOW_LO + (max(0.0, min(2.0, float(score))) / 2.0) * (FLOW_HI - FLOW_LO)
    return round(mapped, 4)


def score_to_veto_tilt(score: float | None) -> float:
    if score is None:
        return 1.0
    mapped = VETO_HI - (max(0.0, min(2.0, float(score))) / 2.0) * (VETO_HI - VETO_LO)
    return round(mapped, 4)


def assemble_size_complete_state(
    state: Mapping[str, Any] | None,
    *,
    compose_row: Mapping[str, Any] | None = None,
    unit: Mapping[str, Any] | None = None,
    already_admitted: bool = True,
) -> dict[str, Any]:
    """Size overlay. Missing ATR/news stay named — never invented."""
    st = dict(state or {})
    ident = dict(st.get("identity") or {})
    geo = dict(st.get("geometry") or {})
    news = dict(st.get("news") or {})
    row = dict(compose_row or {})
    unit_d = dict(unit or {}) if isinstance(unit, Mapping) else {}
    stop_atr = geo.get("stop_atr")
    target_atr = geo.get("target_atr")
    atr_block: Any
    if stop_atr is None and target_atr is None:
        atr_block = "STATE_MISSING"
    else:
        atr_block = {"stop_atr": stop_atr, "target_atr": target_atr, "source": "named_geometry"}
    news_join = st.get("news_join")
    if news_join is None:
        news_join = "STATE_MISSING" if news.get("spine_empty") else news
    return {
        "schema": SCHEMA,
        "already_admitted": bool(already_admitted),
        "named_apply_symbol": row.get("named_apply_symbol"),
        "leave_orig": bool(row.get("leave_orig")),
        "symbol": ident.get("symbol"),
        "sleeve": ident.get("sleeve"),
        "side": ident.get("side"),
        "family_class": ident.get("family_class"),
        "f5_intended_risk_usd": unit_d.get("f5_intended_risk_usd") or 150.0,
        "risk_pct_per_trade": unit_d.get("risk_pct_per_trade"),
        "local_live_size_tilt": row.get("live_size_tilt", 1.0),
        "local_live_cost_tilt": row.get("live_cost_tilt", 1.0),
        "local_live_ca_size_tilt": row.get("live_ca_size_tilt", 1.0),
        "local_combined_live_tilt": row.get("combined_live_tilt", 1.0),
        "geometry_atr": atr_block,
        "news_join": news_join,
        "spine_empty": bool(news.get("spine_empty")),
        "invented_atr": False,
        "invented_news_protocol": False,
        "never_place": True,
        "default_until_prove_place": True,
    }


def overlay_combined(
    local_flow: float,
    local_cost: float,
    local_ca: float,
    answers: Mapping[str, Any] | None,
    *,
    size_mult_apply: bool,
    ca_jev_apply: bool,
) -> dict[str, Any]:
    """Fail-closed: flags off or missing Jev → local product. Cannot refuse."""
    packed = dict(answers or {})
    posture = ((packed.get("size_posture") or {}) or {}).get("choice")
    size_score = _f(((packed.get("size_mult") or {}) or {}).get("score"))
    ca_score = _f(((packed.get("ca_size_mult") or {}) or {}).get("score"))

    flow, cost, ca = float(local_flow), float(local_cost), float(local_ca)
    source = "local_product"

    if posture in {"SIZE_HOLD", "STAND"}:
        flow, cost, ca = 1.0, 1.0, 1.0
        source = "size_posture_hold"
    elif size_mult_apply and posture == "SIZE_TRIM" and size_score is not None:
        flow = score_to_flow_tilt(size_score)
        source = "jev_size_mult"
    elif size_mult_apply and posture == "SIZE_FULL":
        flow = 1.0
        source = "jev_size_full_flow"

    if ca_jev_apply and ca_score is not None:
        ca = score_to_veto_tilt(ca_score)
        source = source + "+jev_ca"

    flow = _clamp(flow, FLOW_LO, FLOW_HI)
    cost = _clamp(min(cost, VETO_HI), VETO_LO, VETO_HI)
    ca = _clamp(min(ca, VETO_HI), VETO_LO, VETO_HI)
    combined = round(flow * cost * ca, 4)
    return {
        "flow": flow,
        "cost": cost,
        "ca": ca,
        "combined": combined,
        "source": source,
        "size_posture": posture,
        "cannot_refuse": True,
        "cannot_zero_fire": True,
        "apply_claimed": 0,
        "never_place": True,
    }
