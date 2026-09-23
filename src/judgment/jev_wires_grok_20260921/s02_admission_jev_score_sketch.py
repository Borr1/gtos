"""DRAFT ONLY — 02_admission_circuit_score.

Not imported by live GTOS. Chair may copy into src/judgment/admission_jev.py
after hist-prove. Never places. Never order_send.

Fail-closed: missing Jev / low confidence / envelope reason → keep integer
governor (evaluate_governor output). Soft Score may TRIM size; it cannot
clear circuit_breaker / max_dd / fail_closed / ceiling interlock.
"""
from __future__ import annotations

from typing import Any, Mapping

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"  # jev_client.evaluate owns the POST

ENVELOPE_BLOCK_REASONS = frozenset(
    {
        "circuit_breaker_open",
        "fail_closed:nan_state",
        "fail_closed:nonpositive_equity",
        "fail_closed:high_water_below_equity",
        "fail_closed:negative_open_risk",
        "max_dd_limit_reached",
        "max_dd_entry_buffer_reached",
        "gross_risk_cap_exhausted",
        "ceiling_profile_requires_smooth_ddefense",
        "unknown_profile",
    }
)

SOFT_DAILY_CLAMP = (0.0, 0.50)
TARGET_PROTECT_CLAMP = (0.10, 0.50)
STRESS_FLOOR = 0.60
OVERLAY_SIZEUP_MAX = 1.75
MIN_CONFIDENCE = 0.45  # tune on Challenge hist; not a cookbook constant


def admission_governor_questions() -> dict[str, Any]:
    """Typed Score/Noul set for the governor hook. IDs are for code."""
    return {
        "admission_soft_daily_size": {
            "type": "score",
            "instructions": (
                "Given named governor.realized_today_pct, open_risk_pct, "
                "joint_daily_gross_cap_pct, occupancy, phi, and session_bucket — "
                "how much NEW-entry size remains inside the -5% hard daily wall? "
                "House integers already decided the -3% soft stop. You do not place. "
                "You do not clear the -5% wall. Empty news spine is not 'no HIGH'."
            ),
            "criteria": [
                "Named realized is at/through the soft stop and remaining session + open_risk would threaten the -5% hard daily wall — keep integer BLOCK",
                "Named daily loss is real but occupancy/phi/session argue a trimmed new unit still fits the joint daily cap",
                "Named realized is near the soft stop but COMPLETE_STATE shows headroom vs the -5% wall and a clean sleeve hour — never full size after the soft stop",
            ],
        },
        "admission_dd_derisk_size": {
            "type": "score",
            "instructions": (
                "How should NEW-entry size_cap_multiplier sit versus named "
                "governor.cap_mult_static (band or smooth formula)? Prop walls "
                "max_dd_limit and max_dd_entry_buffer are code. You may not admit "
                "when dd_frac >= entry buffer. You do not flip derisk_mode. You do not place."
            ),
            "criteria": [
                "Named dd_frac is in the derisk band and remaining intelligence says DEEP_DERISK — at or below static cap_mult",
                "Named dd_frac matches the static formula — keep cap_mult_static",
                "Named static formula over-derisks given phi/session/occupancy/n_active — restore toward 1.0 but never above 1.0",
            ],
        },
        "admission_target_protect_size": {
            "type": "score",
            "instructions": (
                "Named gain vs static initial-balance already meets profit_target_pct. "
                "How hard should NEW-entry size lock in the pass? You keep trading. "
                "You never return full size after target. You do not place."
            ),
            "criteria": [
                "Lock-in hard — named remaining risk or occupancy argues ~0.10–0.25",
                "Keep the integer protect multiplier (named profit_target_derisk_mult, default 0.25)",
                "Milder lock-in up to 0.50 because named DD is healthy and occupancy is light — never 1.0",
            ],
        },
        "leader_impulse_named": {
            "type": "noul",
            "instructions": (
                "Is governor.ll_impulse assembled as the named tag 'none' (no relevant "
                "leader >=1.5 sigma) on a sub_xvol_pullback intent? Unassembled is false. "
                "Do not invent a leader z-score or ATR."
            ),
            "criteria": {
                "true": "Named ll_impulse is the 'none' tag",
                "false": "Unassembled, opposed, or a firing-leg string — not the none tag",
            },
        },
        "admission_leader_impulse_sizeup": {
            "type": "score",
            "instructions": (
                "If leader_impulse_named is true on sub_xvol_pullback with overlays_enabled, "
                "how much confluence size-up is justified? Cap is OVERLAY_SIZEUP_MAX 1.75. "
                "You do not BLOCK. You do not place. Unassembled leader → no size-up."
            ),
            "criteria": [
                "Leader opposed or unassembled — no size-up (1.0)",
                "Mixed / not the none tag — ordinary size (1.0)",
                "Named none tag on sub_xvol_pullback — size-up toward 1.5x",
            ],
        },
        "admission_session_active_sizeup": {
            "type": "score",
            "instructions": (
                "Size-up from named decision_hour / session_bucket only. "
                "Writer clock stays integer. Do not invent overlap volume. Friday cutoff is 0."
            ),
            "criteria": [
                "Dead window, Friday cutoff, or unassembled hour — no size-up",
                "Ordinary session not in the London-open..NY set — 1.0",
                "Named decision_hour in {8,12,16} on an overlay base sleeve — size-up toward 1.15x",
            ],
        },
        "admission_stress_ladder_size": {
            "type": "score",
            "instructions": (
                "Named consecutive_loss_days already computed leak-free from prior days. "
                "Integer ladder is x0.80 then x0.60. You may reshape inside [0.60, 1.0]. "
                "You never widen above 1.0. You do not place."
            ),
            "criteria": [
                "Streak >= 2 — keep or deeper than x0.60, still >= 0.60",
                "Streak == 1 — keep x0.80",
                "Streak exists but today n_active/session/phi argue the integer over-derisks — restore toward 1.0",
            ],
        },
        "admission_coloss_size": {
            "type": "score",
            "instructions": (
                "Named trailing_neg_frac vs 0.57 coloss trigger. Integer trip is x0.60. "
                "Reshape inside [0.60, 1.0] only. You do not place."
            ),
            "criteria": [
                "Named frac >= 0.57 — keep/deeper than x0.60",
                "Named frac near the trigger — keep integer trip",
                "Named frac trips but independent sleeves today argue a milder shrink still >= 0.60",
            ],
        },
        "operator_circuit_named": {
            "type": "noul",
            "instructions": "Is governor.operator_circuit_breaker true? LABEL only. You cannot clear it.",
            "criteria": {
                "true": "Named operator circuit is open — integer BLOCK",
                "false": "Named circuit is closed or unassembled",
            },
        },
        "ceiling_smooth_pairing_named": {
            "type": "noul",
            "instructions": (
                "Is named profile base_risk >= 0.02 paired with derisk_mode smooth? "
                "LABEL only. Uncertified band pairing is already integer-refused."
            ),
            "criteria": {
                "true": "Certified ceiling + smooth pairing",
                "false": "Missing or uncertified pairing",
            },
        },
    }


def _score(answers: Mapping[str, Any], key: str) -> tuple[float | None, float | None]:
    block = answers.get(key)
    if not isinstance(block, dict):
        return None, None
    try:
        s = float(block["score"]) if block.get("score") is not None else None
    except (TypeError, ValueError):
        s = None
    try:
        c = float(block["confidence"]) if block.get("confidence") is not None else None
    except (TypeError, ValueError):
        c = None
    return s, c


def _noul(answers: Mapping[str, Any], key: str) -> bool | float | None:
    block = answers.get(key)
    if not isinstance(block, dict):
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _usable(score: float | None, conf: float | None) -> bool:
    if score is None:
        return False
    if conf is None:
        return False
    return conf >= MIN_CONFIDENCE


def map_soft_daily(score: float) -> float:
    lo, hi = SOFT_DAILY_CLAMP
    t = max(0.0, min(2.0, score)) / 2.0
    return round(lo + t * (hi - lo), 6)


def map_dd_haircut_only(score: float, static_cap: float) -> float:
    """APPLY v1: never exceed static cap_mult."""
    t = max(0.0, min(2.0, score)) / 2.0
    deep = min(static_cap, 0.25)
    proposed = deep + t * (static_cap - deep)
    return round(min(static_cap, max(0.0, proposed)), 6)


def map_target_protect(score: float, static_mult: float) -> float:
    lo, hi = TARGET_PROTECT_CLAMP
    t = max(0.0, min(2.0, score)) / 2.0
    proposed = lo + t * (hi - lo)
    # cannot disable protect: also cannot exceed 0.50; keep static if score~1
    return round(min(hi, max(lo, proposed if abs(score - 1.0) > 0.25 else static_mult)), 6)


def map_leader_sizeup(score: float, named: bool) -> float:
    if not named:
        return 1.0
    t = max(0.0, min(2.0, score)) / 2.0
    return round(min(OVERLAY_SIZEUP_MAX, 1.0 + t * 0.5), 6)


def compose_admission(
    gov: Mapping[str, Any],
    answers: Mapping[str, Any] | None,
    *,
    apply_soft_daily: bool = False,
    apply_dd: bool = False,
    apply_target: bool = False,
    apply_leader: bool = False,
    apply_stress: bool = False,
    overlays_enabled: bool = False,
    ll_impulse: str | None = None,
    sleeve: str | None = None,
    consecutive_loss_days: int = 0,
    trailing_neg_frac: float = 0.0,
    static_stress_mult: float = 1.0,
) -> dict[str, Any]:
    """Return a compose receipt. never_place=True. Mutates no broker state.

    `gov` is asdict(GovernorDecision) plus static cap/reason.
    """
    reason = str(gov.get("reason") or "")
    cap = float(gov.get("size_cap_multiplier") or 0.0)
    allow = bool(gov.get("allow_new_entries"))
    receipt: dict[str, Any] = {
        "ok": True,
        "place": False,
        "never_broker_place": True,
        "reason_static": reason,
        "cap_mult_static": cap,
        "allow_static": allow,
        "applied": [],
        "skipped": None,
        "cap_mult_out": cap,
        "allow_out": allow,
    }
    if reason in ENVELOPE_BLOCK_REASONS or reason.startswith("fail_closed:"):
        receipt["skipped"] = "envelope_keep"
        receipt["allow_out"] = False
        receipt["cap_mult_out"] = 0.0
        return receipt
    answers = answers or {}
    if not answers:
        receipt["skipped"] = "jev_dark_keep_integer"
        return receipt

    if reason == "soft_daily_stop_reached":
        s, c = _score(answers, "admission_soft_daily_size")
        if apply_soft_daily and _usable(s, c):
            cap = map_soft_daily(float(s))
            allow = cap > 0.0
            receipt["applied"].append("soft_daily")
        else:
            cap, allow = 0.0, False
            receipt["skipped"] = receipt["skipped"] or "soft_daily_fail_closed_block"

    if reason in {"ok", "derisking_into_maxdd_wall"} and apply_dd:
        s, c = _score(answers, "admission_dd_derisk_size")
        if _usable(s, c):
            cap = map_dd_haircut_only(float(s), cap)
            receipt["applied"].append("dd_derisk_v1_haircut_only")

    if reason == "profit_target_protect_derisk" and apply_target:
        s, c = _score(answers, "admission_target_protect_size")
        static_m = float(gov.get("profit_target_derisk_mult") or 0.25)
        if _usable(s, c):
            cap = min(cap, map_target_protect(float(s), static_m))
            receipt["applied"].append("target_protect")

    if apply_leader and overlays_enabled and sleeve == "sub_xvol_pullback":
        named = _noul(answers, "leader_impulse_named")
        named_ok = named is True or (isinstance(named, float) and named >= 0.7)
        named_ok = named_ok and (ll_impulse == "none")
        s, c = _score(answers, "admission_leader_impulse_sizeup")
        if named_ok and _usable(s, c):
            receipt["leader_sizeup"] = map_leader_sizeup(float(s), True)
            receipt["applied"].append("leader_impulse")
        else:
            receipt["leader_sizeup"] = 1.0

    if apply_stress and (consecutive_loss_days > 0 or trailing_neg_frac >= 0.57):
        # reshape inside [STRESS_FLOOR, 1.0]; default keep integer product
        stress = max(STRESS_FLOOR, min(1.0, float(static_stress_mult)))
        receipt["stress_mult_out"] = stress
        receipt["applied"].append("stress_floor_envelope")

    if cap <= 0.0:
        allow = False
    receipt["cap_mult_out"] = cap
    receipt["allow_out"] = allow
    return receipt


def joint_daily_clamp(
    cap: float,
    *,
    realized_today_pct: float,
    proposed_unit_risk_pct: float,
    hard_daily_limit_pct: float = 0.05,
    buffer: float = 0.005,
) -> float:
    """Integer envelope: Jev cannot open a -5% daily path."""
    realized_loss = max(0.0, -float(realized_today_pct or 0.0))
    room = max(0.0, float(hard_daily_limit_pct) - realized_loss - float(buffer))
    if proposed_unit_risk_pct <= 0:
        return cap
    max_cap = room / float(proposed_unit_risk_pct)
    return round(max(0.0, min(cap, max_cap)), 6)
