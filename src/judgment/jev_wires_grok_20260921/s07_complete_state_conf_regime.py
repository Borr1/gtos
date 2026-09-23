"""DRAFT ONLY — not landed. Stamp regime_tag + conf_band onto COMPLETE_STATE.

PENDING if Jev dark or missing. Never invent ATR / NEWS / regime.
Policy C consumes these voters; this helper does not refuse admit itself.
place=false. No order_send.
"""

from __future__ import annotations

from typing import Any, Mapping

PENDING = "PENDING"
CONF_ADMIT = ("YES", "NO", "UNSURE")
CONF_BANDS = (
    "STRICT",
    "SESSION",
    "EVENT",
    "REVIEW",
    "KEEP",
    "ALLOW",
    "PENDING",
    "CONF_GATE_STRICT",
    "CONF_GATE_SESSION",
    "CONF_GATE_EVENT",
    "CONF_GATE_REVIEW",
    "CONF_GATE_KEEP",
    "CONF_GATE_ALLOW",
)
REGIME_TAGS = ("trend_up", "trend_down", "range", "chop", "unclear", PENDING)


def _incomplete(value: Any) -> bool:
    return value is None or value in ("", PENDING, "PENDING_SHADOW")


def atr_source_of(gold: Mapping[str, Any] | None) -> str:
    """Honesty: lab constants must not look like Module_ATR / live ATR."""
    if not gold:
        return "STATE_MISSING"
    geo = gold.get("geometry") if isinstance(gold.get("geometry"), Mapping) else {}
    atr14 = geo.get("atr14") if isinstance(geo, Mapping) else None
    atr50 = geo.get("atr50") if isinstance(geo, Mapping) else None
    note = str((gold.get("completeness") or {}).get("atr_source") or "")
    if note:
        return note
    if atr14 is None and atr50 is None:
        return "omitted"
    # S14 lab helper used 1.2 / 1.0 — if a row carries only those and no bars, tag it.
    try:
        if float(atr14) == 1.2 and float(atr50) == 1.0 and gold.get("as_of_clock") == "as_of_open_study":
            return "lab_constant_suspect"
    except (TypeError, ValueError):
        pass
    return "gold_state_geometry"


def stamp_conf_regime_into_complete_state(
    state: Mapping[str, Any] | None,
    *,
    regime_type: str | None,
    conf_admit: str | None,
    conf_band_label: str | None,
    jev_dark: bool,
    atr_omitted: bool = False,
) -> dict[str, Any]:
    out = dict(state or {})
    if jev_dark:
        out["regime_tag"] = PENDING
        out["conf_band"] = PENDING
        out["conf_admit"] = None
    else:
        tag = str(regime_type) if regime_type else PENDING
        out["regime_tag"] = tag if tag in REGIME_TAGS else PENDING
        band = str(conf_band_label) if conf_band_label else PENDING
        out["conf_band"] = band if band in CONF_BANDS else PENDING
        admit = str(conf_admit) if conf_admit else None
        out["conf_admit"] = admit if admit in CONF_ADMIT else None
    voters = [out.get(k) for k in ("alive", "regime_tag", "conf_band", "session_fit")]
    out["n_incomplete"] = sum(1 for v in voters if _incomplete(v))
    out["full_state_dark"] = bool(out.get("full_state_dark")) or jev_dark
    out["place"] = False
    out["news_invent"] = False
    if atr_omitted:
        missing = list(out.get("completeness", {}).get("missing_fields") or []) if isinstance(out.get("completeness"), dict) else []
        if "atr_expansion" not in missing:
            missing.append("atr_expansion")
        completeness = dict(out.get("completeness") or {})
        completeness["missing_fields"] = missing
        completeness["atr_source"] = completeness.get("atr_source") or "omitted"
        out["completeness"] = completeness
    return out
