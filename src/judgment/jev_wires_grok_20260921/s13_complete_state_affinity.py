"""DRAFT SKETCH — session 13_instrument_affinity_sleeves.
Not live. No APPLY. No broker place. Fail-closed if fields missing.

Compose COMPLETE_STATE.alive_menu[].affinity + conflict_set + phi_by_sleeve
for GBPJPY / XAGUSD / NZDUSD / EURUSD / XAUUSD.

Chair land later into judgment/sleeve_select.py + gold_state/symbol_state composer.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

# Envelope: named KEEP tags. Do not port across instruments.
F5_AFFINITY_KEEP_PRIORS: dict[str, tuple[str, ...]] = {
    "EURUSD": ("asian_fade", "sub_mid_dn_re_proxy_eurusd_short_m15_atr"),
    "XAUUSD": (
        "dsp_spring_close_on_20low_through_the_box",
        "dsp_three_fresh_lower_lows",
        "dsp_expanding_up_staircase",
    ),
    "GBPJPY": ("vss_fxcross_london_up_low", "sub_mid_dn_revert"),
    "XAGUSD": ("sub_xvol_pullback", "metals_core", "metal_session_reversion"),
    "NZDUSD": ("sub_mid_dn_re_proxy_nzdusd_short_m15_atr",),
}

# Honest keep_status from Module_ATR packs (not invented).
KEEP_STATUS: dict[tuple[str, str], str] = {
    ("EURUSD", "asian_fade"): "KEEP",
    ("EURUSD", "sub_mid_dn_re_proxy_eurusd_short_m15_atr"): "KEEP",
    ("XAUUSD", "dsp_spring_close_on_20low_through_the_box"): "KEEP",
    ("XAUUSD", "dsp_three_fresh_lower_lows"): "KEEP_research_with_2026_fail_haircut",
    ("XAUUSD", "dsp_expanding_up_staircase"): "KEEP_prior_expanding_lane_p0",
    ("GBPJPY", "vss_fxcross_london_up_low"): "KEEP",
    ("GBPJPY", "sub_mid_dn_revert"): "KEEP",
    ("XAGUSD", "metal_session_reversion"): "KEEP",
    ("XAGUSD", "sub_xvol_pullback"): "NARROW",
    ("XAGUSD", "metals_core"): "NARROW",
    ("NZDUSD", "sub_mid_dn_re_proxy_nzdusd_short_m15_atr"): "KEEP",
}

AFFINITY_LENS: dict[tuple[str, str], str] = {
    ("EURUSD", "asian_fade"): "LIVE_FILE_Module_ATR_trail",
    ("EURUSD", "sub_mid_dn_re_proxy_eurusd_short_m15_atr"): "LIVE_FILE_Module_ATR_PackageB_SHORT",
    ("XAUUSD", "dsp_spring_close_on_20low_through_the_box"): "LIVE_FILE_Module_ATR_0.75_6.0",
    ("XAUUSD", "dsp_three_fresh_lower_lows"): "LIVE_FILE_Module_ATR_0.75_6.0",
    ("XAUUSD", "dsp_expanding_up_staircase"): "EXPANDING_LANE_LOCK_P0",
    ("GBPJPY", "vss_fxcross_london_up_low"): "Module_ATR_affinity_ORB_continuation_proxy",
    ("GBPJPY", "sub_mid_dn_revert"): "Module_ATR_affinity_tape_KEEP_never_PackageB",
    ("XAGUSD", "metal_session_reversion"): "Module_ATR_file_exit_STOP_K_0.8",
    ("XAGUSD", "sub_xvol_pullback"): "Module_ATR_file_exit_H4_NARROW",
    ("XAGUSD", "metals_core"): "Module_ATR_file_exit_H4_NARROW",
    ("NZDUSD", "sub_mid_dn_re_proxy_nzdusd_short_m15_atr"): "Module_ATR_affinity_SHORT_M15",
}

DEFAULT_SIDE: dict[str, int] = {
    "asian_fade": 1,
    "sub_mid_dn_re_proxy_eurusd_short_m15_atr": -1,
    "sub_mid_dn_re_proxy_nzdusd_short_m15_atr": -1,
    "sub_mid_dn_revert": -1,  # GBPJPY tape KEEP SHORT; never EURUSD Package B
    "vss_fxcross_london_up_low": 1,
    "dsp_spring_close_on_20low_through_the_box": 1,
    "dsp_three_fresh_lower_lows": 1,
    "dsp_expanding_up_staircase": 1,
}


def affinity_row(
    symbol: str,
    tag: str,
    *,
    phi: float | None,
    phi_status: str = "ok",
) -> dict[str, Any]:
    sym = str(symbol or "").upper()
    keep_prior = tag in F5_AFFINITY_KEEP_PRIORS.get(sym, ())
    status = KEEP_STATUS.get((sym, tag), "STATE_MISSING")
    lens = AFFINITY_LENS.get((sym, tag), "STATE_MISSING")
    cell = f"{sym}×{tag}"
    return {
        "tag": tag,
        "phi": phi,
        "keep_prior": keep_prior,
        "affinity": {
            "instrument": sym,
            "sleeve": tag,
            "cell": cell,
            "pair": cell,
            "global_rule": False,
            "keep_status": status,
            "lens": lens,
            "side": DEFAULT_SIDE.get(tag),
            "research_only": "three_fresh_like" in tag or tag == "dsp_three_fresh_like",
            "banned_for_aplus": False,
            "proxy_vs_live": (
                "proxy_KEEP_live_NARROW" if tag == "vss_fxcross_london_up_low" else None
            ),
            "phi_status": phi_status if phi is not None else "STATE_MISSING",
            "haircuts": (
                ["chair_2026_fail_capability_haircut_x0.55"]
                if tag == "dsp_three_fresh_lower_lows"
                else []
            ),
            "lane": "expanding_p0" if "expanding" in tag else "affinity",
        },
    }


def compose_alive_menu_affinity(
    symbol: str,
    tags: Sequence[str],
    phi_by_sleeve: Mapping[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Fail-closed: unknown tag → keep_status STATE_MISSING, phi null."""
    phi_by_sleeve = phi_by_sleeve or {}
    menu: list[dict[str, Any]] = []
    for tag in tags:
        if tag == "sub_mid_dn_revert" and tag not in F5_AFFINITY_KEEP_PRIORS.get(str(symbol).upper(), ()):
            continue  # refused_alias_package_b_to_sub_mid_dn_revert
        if tag == "sub_mid_dn_re_proxy_eurusd_short_m15_atr" and str(symbol).upper() != "EURUSD":
            continue
        raw_phi = phi_by_sleeve.get(tag)
        phi_status = "ok" if raw_phi is not None else "STATE_MISSING"
        menu.append(affinity_row(symbol, tag, phi=raw_phi, phi_status=phi_status))
    return menu


def compose_complete_state_affinity_slice(
    symbol: str,
    tags: Sequence[str],
    *,
    phi_by_sleeve: Mapping[str, float] | None = None,
    conflict_set: list[dict[str, Any]] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Slice only. Session 10 composer owns the rest of COMPLETE_STATE."""
    menu = compose_alive_menu_affinity(symbol, tags, phi_by_sleeve)
    return {
        "symbol": str(symbol).upper(),
        "alive_sleeves": [r["tag"] for r in menu],
        "alive_menu": menu,
        "phi_by_sleeve": dict(phi_by_sleeve or {}),
        "conflict_set": list(conflict_set or []),
        "news_join": {"status": "STATE_MISSING"},  # honest; never invent NEWS_PROTOCOL
        "place": False,
        "apply": False,
        "fail_closed": False,
        **dict(extra or {}),
    }
