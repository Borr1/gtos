"""DRAFT ONLY — chair_enforce hard-off exception Choice.

Not live. Not imported by writer. place=false. APPLY=false until Chair+hist.
Fail-closed KEEP_OFF if Jev dark / no prove / scoped miss / low confidence.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

# Draft env names. Live flags.py would grow these; do not flip sleeve_select APPLY.
SHADOW_ENV = "GTOS_JEV_HARD_OFF_EXCEPTION_SHADOW"
APPLY_ENV = "GTOS_JEV_HARD_OFF_EXCEPTION_APPLY"
SCOPED_ENV = "GTOS_JEV_HARD_OFF_EXCEPTION_SCOPED"
CONF_FLOOR_ENV = "GTOS_JEV_HARD_OFF_EXCEPTION_CONF_FLOOR"
PROVE_DIR_ENV = "GTOS_JEV_HARD_OFF_EXCEPTION_PROVE_DIR"

NAMED_REASONS = (
    "chair_g_index_hard_off",
    "chair_xa_huge_hard_off",
    "chair_orb_crypto_hard_off",
    "chair_bleed_hard_off",
    "chair_mx_us30_hard_off",
    "chair_hard_off_family",
)

REASON_TO_FAMILY = {
    "chair_g_index_hard_off": "idxrev",
    "chair_xa_huge_hard_off": "xa_huge",
    "chair_orb_crypto_hard_off": "orb_crypto",
    "chair_bleed_hard_off": "bleed",
    "chair_mx_us30_hard_off": "mx_us30",
    "chair_hard_off_family": "hard_off_family",
}

_TRUTHY = frozenset({"1", "true", "yes", "on"})
STATE_MISSING = "STATE_MISSING"


def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY


def shadow_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    return _env_on(SHADOW_ENV, environ)


def apply_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    return _env_on(APPLY_ENV, environ)


def conf_floor(environ: Mapping[str, str] | None = None) -> float:
    env = environ if environ is not None else os.environ
    raw = str(env.get(CONF_FLOOR_ENV, "") or "0.80").strip()
    try:
        return float(raw)
    except ValueError:
        return 0.80


def hard_off_exception_questions() -> dict[str, Any]:
    return {
        "hard_off_exception": {
            "type": "choice",
            "instructions": {
                "question": (
                    "Given named hard_off_reason, challenge_hist_cell, "
                    "module_atr_cell, surface.us30_off, affinity, and occupancy, "
                    "should the chair_enforce wall KEEP_OFF or grant a "
                    "SCOPED_EXCEPTION for scoped_key only?"
                ),
                "focus": (
                    "Default is KEEP_OFF. SCOPED_EXCEPTION is a narrow skip of "
                    "stand_down for this candidate. ENV-US30, ENV-KILL, G8, and "
                    "2-stop COUNT still bind. Do not discover a new hard-off family. "
                    "Do not treat Module_ATR KEEP on a different sleeve as proof. "
                    "module_atr_cell=STATE_MISSING means no ATR proof."
                ),
            },
            "criteria": {
                "KEEP_OFF": (
                    "Named house hard-off wall stays. Candidate must stand_down."
                ),
                "SCOPED_EXCEPTION": (
                    "Named wall may be skipped for THIS scoped_key only. "
                    "Not a family delete, not a place, not an ENV-US30 lift."
                ),
            },
        },
        "house_toxic_named": {
            "type": "noul",
            "instructions": (
                "Is identity.family_class house_hard_off or hard_off_reason one of "
                "the six named chair_*_hard_off reasons? Confirm the named class. "
                "Do not invent a new family."
            ),
            "criteria": {
                "true": "Named house hard-off class is present on this row",
                "false": "Named class is absent or STATE_MISSING",
            },
        },
    }


def scoped_key(family: str, symbol: str, session_bucket: str) -> str:
    fam = str(family or "unknown").strip().lower()
    sym = str(symbol or "unknown").strip().upper().replace(".", "_")
    sess = str(session_bucket or "unknown").strip().lower()
    return f"{fam}:{sym}:{sess}"


def scoped_allowlisted(key: str, allow_csv: str) -> bool:
    if not allow_csv or not str(allow_csv).strip():
        return False
    key_l = key.lower()
    for raw in str(allow_csv).split(","):
        token = raw.strip().lower()
        if not token:
            continue
        if key_l == token or key_l.startswith(token + ":"):
            return True
        # token family or family:SYMBOL matches prefix of key
        if key_l.startswith(token):
            return True
    return False


def exception_authorized(
    *,
    choice: str | None,
    confidence: float | None,
    reason: str | None,
    key: str,
    us30_off: bool,
    index_symbol_hit: bool,
    full_state_dark: bool,
    shadow: bool,
    apply: bool,
    allow_csv: str,
    receipt_proven: bool,
    receipt_may_not_lift_env_us30: bool = True,
    floor: float = 0.80,
) -> bool:
    """False unless every gate passes. Never place."""
    del shadow  # shadow never authorizes
    if not apply:
        return False
    if full_state_dark:
        return False
    if reason not in NAMED_REASONS:
        return False
    if choice != "SCOPED_EXCEPTION":
        return False
    if confidence is None or float(confidence) < floor:
        return False
    if not receipt_proven:
        return False
    if not scoped_allowlisted(key, allow_csv):
        return False
    if (us30_off or index_symbol_hit) and receipt_may_not_lift_env_us30:
        return False
    return True


def fail_closed_stamp(*, reason: str | None, skipped: str) -> dict[str, Any]:
    return {
        "hard_off": True,
        "hard_off_reason": reason,
        "exception_choice": "KEEP_OFF",
        "exception_confidence": None,
        "exception_applied": False,
        "jev_skipped": skipped,
        "broker_effect": False,
        "place": False,
        "new_hard_off": False,
    }


def consume_jev_row(
    row: Mapping[str, Any] | None,
    *,
    reason: str | None,
    key: str,
    us30_off: bool,
    index_symbol_hit: bool,
    full_state_dark: bool,
    environ: Mapping[str, str] | None = None,
    receipt_proven: bool = False,
    receipt_may_not_lift_env_us30: bool = True,
) -> dict[str, Any]:
    """Map jev_client.evaluate receipt → stamp fields. Never raises."""
    env = environ if environ is not None else os.environ
    shadow = shadow_enabled(environ=env)
    apply = apply_enabled(environ=env)
    if not shadow and not apply:
        return fail_closed_stamp(reason=reason, skipped="flags_off")
    if not row or not row.get("ok"):
        skipped = str((row or {}).get("skipped") or (row or {}).get("error") or "jev_dark")
        return fail_closed_stamp(reason=reason, skipped=skipped)
    answers = row.get("answers") or {}
    ho = answers.get("hard_off_exception") or {}
    choice = ho.get("choice")
    conf = ho.get("confidence")
    try:
        conf_f = float(conf) if conf is not None else None
    except (TypeError, ValueError):
        conf_f = None
    authorized = exception_authorized(
        choice=str(choice) if choice else None,
        confidence=conf_f,
        reason=reason,
        key=key,
        us30_off=us30_off,
        index_symbol_hit=index_symbol_hit,
        full_state_dark=full_state_dark,
        shadow=shadow,
        apply=apply,
        allow_csv=str(env.get(SCOPED_ENV, "") or ""),
        receipt_proven=receipt_proven,
        receipt_may_not_lift_env_us30=receipt_may_not_lift_env_us30,
        floor=conf_floor(env),
    )
    out_choice = str(choice) if choice in {"KEEP_OFF", "SCOPED_EXCEPTION"} else "KEEP_OFF"
    return {
        "hard_off": True,
        "hard_off_reason": reason,
        "exception_choice": out_choice,
        "exception_confidence": conf_f,
        "exception_applied": bool(authorized),
        "jev_skipped": None,
        "broker_effect": False,
        "place": False,
        "new_hard_off": False,
        "scoped_key": key,
        "house_toxic_named": (answers.get("house_toxic_named") or {}).get("noul"),
    }
