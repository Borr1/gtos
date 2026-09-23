"""DRAFT ONLY — 17_residual_static_admission_governor.

Not on the live import path. Chair copies after Challenge hist-prove.
place=false. APPLY default-off. Never order_send.
"""
from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

_TRUTHY = {"1", "true", "yes", "on"}
_OUT = Path(__file__).resolve().parents[1]
_DEFAULT_LOG = _OUT / "shadow_logs" / "admission_jev.jsonl"

NEVER_PLACE = True
APPLY_DEFAULT = False
FAIL_CLOSED_DEFAULT = True

# Envelope constants copied as documentation — live values stay in admission.py
FTMO_DAILY = 0.05
JOINT_BUFFER = 0.005
OVERLAY_SIZEUP_MAX = 1.75
STRESS_DERISK_MIN_MULT = 0.60
LEARNING_RERATE_MAX = 1.25
DERISK_SCORE_MIN = 0.25  # Score haircut floor; 0.0 is envelope BLOCK only


def _env_on(name: str, default: bool = False) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in _TRUTHY


def shadow_enabled() -> bool:
    return _env_on("GTOS_JEV_ADMISSION_SHADOW") or _env_on("GTOS_JEV_ALIVE_SHADOW")


def apply_enabled() -> bool:
    # Hard default-off. Hist-prove receipt still required by caller.
    if not _env_on("GTOS_JEV_ADMISSION_APPLY", APPLY_DEFAULT):
        return False
    return False  # this session never opens APPLY even if env is set


def fail_closed() -> bool:
    return _env_on("GTOS_JEV_ADMISSION_FAIL_CLOSED", FAIL_CLOSED_DEFAULT)


def admission_governor_questions() -> dict[str, Any]:
    """Typed Choice/Score/Noul for the account governor. Not the sleeve-fire admit Choice."""
    return {
        "governor_room_honest": {
            "type": "noul",
            "instructions": (
                "Are named governor.equity, realized_today_pct, open_risk_pct, dd_frac "
                "finite, and is remaining room under hard daily 5% and static maxDD 10% "
                "still positive? Use only named fields. Missing => false."
            ),
            "criteria": {
                "true": "Named governor fields are finite and room remains",
                "false": "A named field is missing/contradictory or room is exhausted",
            },
        },
        "maxdd_derisk_size_mult": {
            "type": "score",
            "instructions": (
                "How hard should NEW-entry size shrink given named governor.dd_frac "
                "and governor.derisk_mode? 0 = at/past entry buffer (code already BLOCKs); "
                "mid = moderate haircut; top = below derisk_start, full static size. "
                "You may only recommend a haircut versus the static cap_mult. "
                "Do not flip derisk_mode. Do not place."
            ),
            "criteria": [
                "At or past the entry buffer — zero new risk",
                "Deep band — heavy haircut",
                "Mid band — moderate haircut",
                "Early band — light haircut",
                "Below derisk_start — full static size",
            ],
        },
        "profit_target_lock_size_mult": {
            "type": "score",
            "instructions": (
                "If named gain_vs_initial >= profit_target_pct, how small should NEW size "
                "be to lock the pass? Cannot exceed static profit_target_derisk_mult. "
                "If target logic is off (pct=0), abstain at mid."
            ),
            "criteria": [
                "Lock pass at quarter size or less",
                "Lock pass at half",
                "Still hunt near full static",
            ],
        },
        "daily_room_size_mult": {
            "type": "score",
            "instructions": (
                "Given named realized_today_pct versus soft_daily_stop_pct and the "
                "joint remaining room to hard daily 5% minus 0.5pp, how much NEW size? "
                "Cannot recommend size that would let realized+open+new graze the hard wall."
            ),
            "criteria": [
                "Near the hard daily wall — haircut hard",
                "Ordinary intraday room",
                "Green day — full static",
            ],
        },
        "soft_daily_action": {
            "type": "choice",
            "instructions": (
                "Named reason is or would be soft_daily_stop_reached (-3% buffer; hard is -5%). "
                "House integer today BLOCKs new entries. Prefer BLOCK_KEEP unless named "
                "joint_daily_room clearly remains. STAND if state is thin. "
                "Never reopen circuit_breaker_open or max_dd_limit_reached. Never place."
            ),
            "criteria": {
                "BLOCK_KEEP": "Keep the integer BLOCK of new entries",
                "DERISK_TRIM": "Remaining joint room exists; shrink new size instead of block",
                "STAND": "State thin or mixed; do not steer",
            },
        },
        "unit_keep_under_gross_cap": {
            "type": "score",
            "instructions": (
                "If gross cap binds, should this named unit be kept under remaining "
                "available_gross_risk_pct? Affinity: XAU/GBPJPY keep is allowed as a "
                "preference, not a global sleeve-select APPLY. Sum of kept unit_risk "
                "must not exceed remaining headroom."
            ),
            "criteria": [
                "Shed this unit",
                "Borderline fit",
                "Keep this unit",
            ],
        },
        "metals_a8_action": {
            "type": "choice",
            "instructions": (
                "Named A8 K-of-4 on metals_core/metals_softband. Use only named "
                "htf_slope_norm, mom_20_atr, fvg_freshness_bars, atr_ratio, session_hour. "
                "atr_ratio is a decision-bar fact — not Module_ATR blotter R, not an invented regime. "
                "Featureless => ABSTAIN (code admits-as-today). Gate ON + fail K => default DROP."
            ),
            "criteria": {
                "DROP": "Named features fail K=3-of-4 — keep the integer drop",
                "ADMIT_TRIM": "Named features mixed; admit at reduced size",
                "ABSTAIN": "Features missing or not a metals A8 sleeve",
            },
        },
    }


def _f(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        x = float(v)
        if x != x or x in (float("inf"), float("-inf")):
            return None
        return x
    except (TypeError, ValueError):
        return None


def admission_complete_state(
    *,
    gov: Any,
    gs: Any,
    limits: Any,
    intents: Sequence[Any] = (),
    profile: str = "",
    account: str = "A",
    stress_state: Any = None,
    n_active: int | None = None,
    occupancy: Mapping[str, Any] | None = None,
    gold: Mapping[str, Any] | None = None,
    news_join: Any = "STATE_MISSING",
) -> dict[str, Any]:
    """COMPLETE_STATE for governor wires. Honest missing. No Module_ATR invention."""
    def gget(obj: Any, *names: str, default: Any = None) -> Any:
        if obj is None:
            return default
        if isinstance(obj, Mapping):
            for n in names:
                if n in obj and obj[n] is not None:
                    return obj[n]
            return default
        for n in names:
            if hasattr(obj, n):
                val = getattr(obj, n)
                if val is not None:
                    return val
        return default

    equity = _f(gget(gs, "equity"))
    dd_ref = _f(gget(gs, "max_dd_reference_equity", "high_water")) or 0.0
    dd_frac = None
    if equity is not None and dd_ref and dd_ref > 0:
        dd_frac = (dd_ref - equity) / dd_ref
    gain = None
    if equity is not None and dd_ref and dd_ref > 0:
        gain = (equity - dd_ref) / dd_ref

    first = intents[0] if intents else None
    atr_ratio = gget(first, "atr_ratio")
    vr = gget(first, "vr")
    atr_basis = "missing"
    if vr is not None or atr_ratio is not None:
        atr_basis = "intent_price"
    elif gold and (gold.get("geometry") or {}).get("atr14") is not None:
        atr_basis = "wave21_atr"

    missing: list[str] = []
    if equity is None:
        missing.append("governor.equity")
    if news_join == "STATE_MISSING" or news_join is None:
        missing.append("news_join")
    if atr_basis == "missing":
        missing.append("atr")

    return {
        "schema": "gtos.complete_state.admission_governor.v0",
        "never_place": True,
        "apply": False,
        "identity": {
            "symbol": gget(first, "symbol"),
            "sleeve": gget(first, "sleeve"),
            "side": gget(first, "direction"),
            "decision_day": gget(first, "decision_day"),
        },
        "account": {
            "login": 0,
            "ns": "operator",
            "equity": equity,
            "dd_wall_r": 0.10,
            "soft_daily_stop": gget(limits, "soft_daily_stop_pct", default=0.03),
        },
        "governor": {
            "allow_new": gget(gov, "allow_new_entries", "allow_new"),
            "cap_mult": gget(gov, "size_cap_multiplier", "cap_mult"),
            "reason": gget(gov, "reason"),
            "realized_today_pct": gget(gs, "realized_today_pct"),
            "open_risk_pct": gget(gs, "open_risk_pct"),
            "dd_frac": dd_frac,
            "dd_ref": dd_ref,
            "derisk_mode": gget(limits, "derisk_mode"),
            "derisk_start_dd_pct": gget(limits, "derisk_start_dd_pct"),
            "max_dd_limit_pct": gget(limits, "max_dd_limit_pct", default=0.10),
            "entry_block_pct": gget(limits, "max_dd_entry_block_pct"),
            "profit_target_pct": gget(limits, "profit_target_pct"),
            "profit_target_derisk_mult": gget(limits, "profit_target_derisk_mult"),
            "profit_target_gain": gain,
            "gross_cap": gget(limits, "gross_open_risk_cap_pct"),
            "available_gross": gget(gov, "available_gross_risk_pct"),
            "circuit_breaker": gget(gs, "operator_circuit_breaker"),
            "profile": profile,
            "account_side": account,
            "hard_daily_limit_pct": FTMO_DAILY,
            "joint_buffer": JOINT_BUFFER,
        },
        "stress": {
            "consecutive_loss_days": gget(stress_state, "consecutive_loss_days", default=0),
            "trailing_neg_frac": gget(stress_state, "trailing_neg_frac", default=0.0),
        },
        "kelly": {"n_active_sleeves_today": n_active, "conservative": True},
        "occupancy": dict(occupancy or {}),
        "news_join": news_join if news_join is not None else "STATE_MISSING",
        "atr": {
            "atr_ratio": atr_ratio,
            "vr": vr,
            "atr_basis": atr_basis,
            "module_atr_invented": False,
        },
        "hard_off_hit": None,
        "full_state_dark": bool(missing),
        "n_incomplete": len(missing),
        "missing_fields": missing,
        "place_context": {"writer_ready": None, "authority": None, "ticket_draft_fp": None},
        "as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def score_to_size_mult(score: float | None, *, lo: float = DERISK_SCORE_MIN, hi: float = 1.0) -> float:
    """Map 0–N Score onto [lo, hi]. Missing => 1.0 (no steer). Never >1.0 here (shrink family)."""
    if score is None:
        return 1.0
    try:
        v = float(score)
    except (TypeError, ValueError):
        return 1.0
    # Fanout Scores are 0–2; admission maxdd score is 0–4. Normalize by assuming 0..max(2,v).
    span = 4.0 if v > 2.5 else 2.0
    v = max(0.0, min(span, v))
    return round(lo + (v / span) * (hi - lo), 6)


def joint_room_ok(gs: Any, limits: Any, new_open_risk_pct: float) -> bool:
    realized = _f(getattr(gs, "realized_today_pct", None) if not isinstance(gs, Mapping)
                  else gs.get("realized_today_pct")) or 0.0
    open_r = _f(getattr(gs, "open_risk_pct", None) if not isinstance(gs, Mapping)
                else gs.get("open_risk_pct")) or 0.0
    hard = FTMO_DAILY
    worst = max(0.0, -realized) + max(0.0, open_r) + max(0.0, new_open_risk_pct)
    return worst <= (hard - JOINT_BUFFER) + 1e-12


def maybe_score_governor(gov: Any, gs: Any, limits: Any, intents: Sequence[Any] = (), **ctx: Any) -> Any:
    """SHADOW-or-identity. APPLY is hard-off in this draft. Dark => gov unchanged."""
    if not shadow_enabled() and not apply_enabled():
        return gov
    state = admission_complete_state(gov=gov, gs=gs, limits=limits, intents=intents, **ctx)
    rec: dict[str, Any] = {
        "ok": False,
        "dark": True,
        "skipped": "draft_no_live_post",
        "size_mult": 1.0,
        "soft_action": "STAND",
        "never_place": True,
        "apply": False,
    }
    # Live land would call jev_client.evaluate(state) here.
    _log(state, rec, gov)
    if fail_closed() or not apply_enabled() or rec.get("dark"):
        return gov
    return gov


def _log(state: dict[str, Any], rec: dict[str, Any], gov: Any) -> None:
    path = Path(os.environ.get("GTOS_JEV_ADMISSION_LOG") or _DEFAULT_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "schema": "gtos.admission_jev.shadow.v0",
        "never_place": True,
        "apply": False,
        "governor_reason": getattr(gov, "reason", None) if not isinstance(gov, Mapping)
        else gov.get("reason"),
        "state_n_incomplete": state.get("n_incomplete"),
        "rec": rec,
        "ts_utc": datetime.now(timezone.utc).isoformat(),
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


# Silence unused import in draft (replace used at live land).
_ = replace
