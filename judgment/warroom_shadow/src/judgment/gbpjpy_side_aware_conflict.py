"""GBPJPY side-aware conflict — scoped LABEL for admission (Chair land).
Do NOT flip GTOS_JEV_SLEEVE_SELECT_APPLY=1.
Source: JEV_SLEEVE_SELECT_choice_rule_v4 patch 20260920.
"""
from __future__ import annotations
from typing import Any, Mapping

# NOTE: depends on is_vss / is_sub_mid / is_package_b from choice_rule host module.
def gbpjpy_side_aware_conflict(
    state: dict,
    keep_cands: list[str],
    prior: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Chair hist KEEP conflict (GROK_KEEP_HIST_PROVE_20260920).

    GBPJPY only — affinity instrument×sleeve. Like XAU three_fresh STAND:
      opp-side (vss LONG vs sub_mid SHORT): prefer vss LONG; STAND/drop sub_mid fade
      same SHORT (vss SHORT × sub_mid SHORT): prefer sub_mid; drop vss SHORT
    Does NOT flip GTOS_JEV_SLEEVE_SELECT_APPLY. LABEL for admission until Chair lands.
    Never places. Cost never kill. Never invent NEWS.
    """
    symbol = (state.get("symbol") or state.get("instrument") or "").upper()
    if symbol != "GBPJPY":
        return None
    vss = [c for c in keep_cands if is_vss(c)]
    sub = [c for c in keep_cands if is_sub_mid(c) and not is_package_b(c)]
    if not vss or not sub:
        return None

    # Resolve sides from state (intents / candidate sides). Default: vss LONG analog, sub_mid SHORT.
    def _side(tag: str) -> int | None:
        key = (tag or "").lower()
        sides = state.get("sleeve_sides") or state.get("candidate_sides") or {}
        if key in sides:
            try:
                return int(sides[key])
            except Exception:
                pass
        for item in state.get("sleeve_candidates_detail") or []:
            if isinstance(item, dict) and (item.get("tag") or item.get("sleeve") or "").lower() == key:
                d = item.get("direction") or item.get("side")
                if d is not None:
                    try:
                        return int(d)
                    except Exception:
                        if str(d).upper() in ("LONG", "BUY"):
                            return 1
                        if str(d).upper() in ("SHORT", "SELL"):
                            return -1
        if "up_low" in key or "uplow" in key or "long" in key:
            return 1
        if is_sub_mid(tag):
            return -1  # tape KEEP SHORT on GBPJPY Module_ATR proxy
        if is_vss(tag) and "short" in key:
            return -1
        if is_vss(tag):
            return int(state.get("vss_direction") or state.get("vss_side") or 1)
        return None

    vss_tag = vss[0]
    sub_tag = sub[0]
    vss_side = _side(vss_tag)
    sub_side = _side(sub_tag)
    if vss_side is None or sub_side is None:
        return {
            "kind": "GBPJPY_CONFLICT_LABEL",
            "effective": keep_cands,
            "dropped": [],
            "label": "GBPJPY_CONFLICT_SIDES_UNRESOLVED_LABEL_FOR_CHAIR",
            "rule": "gbpjpy_side_aware_v1",
            "apply_global": False,
        }

    # opp-side: prefer vss LONG, STAND sub_mid fade
    if vss_side > 0 and sub_side < 0:
        return {
            "kind": "TRUE_CONFLICT",
            "effective": [vss_tag],
            "dropped": [sub_tag],
            "pick": vss_tag,
            "stand": sub_tag,
            "reason": "gbpjpy_opp_side_prefer_vss_LONG_stand_sub_mid_fade",
            "rule": "gbpjpy_side_aware_v1",
            "apply_global": False,
            "scoped_apply_recommended": True,
            "scoped_scope": "GBPJPY_conflict_vss_LONG_x_sub_mid_SHORT",
        }
    # same SHORT: prefer sub_mid, drop vss SHORT
    if vss_side < 0 and sub_side < 0:
        return {
            "kind": "TRUE_CONFLICT",
            "effective": [sub_tag],
            "dropped": [vss_tag],
            "pick": sub_tag,
            "stand": vss_tag,
            "reason": "gbpjpy_same_SHORT_prefer_sub_mid_drop_vss_SHORT",
            "rule": "gbpjpy_side_aware_v1",
            "apply_global": False,
            "scoped_apply_recommended": True,
            "scoped_scope": "GBPJPY_conflict_vss_SHORT_x_sub_mid_SHORT",
        }
    # same LONG or residual: LABEL only
    return {
        "kind": "GBPJPY_CONFLICT_LABEL",
        "effective": keep_cands,
        "dropped": [],
        "label": "GBPJPY_CONFLICT_RESIDUAL_LABEL",
        "vss_side": vss_side,
        "sub_side": sub_side,
        "rule": "gbpjpy_side_aware_v1",
        "apply_global": False,
    }



