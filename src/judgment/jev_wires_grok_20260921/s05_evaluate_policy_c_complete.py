"""DRAFT orchestrator — integer envelope + optional Jev POST. NOT live-landed.

Fail-closed if Jev dark. place=False default-until-prove. No order_send.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

CHOICE_STAND = "A_STAND_DOWN"
CHOICE_TRIM = "C_SIZE_TRIM"
CHOICE_FULL = "D_FULL"
SKIP_STATE_MISSING = "STATE_MISSING"
_VOTER_KEYS = ("alive", "regime_tag", "conf_band", "session_fit")
SIZE_MAP = {CHOICE_STAND: 0.0, CHOICE_TRIM: 0.75, CHOICE_FULL: 1.0}


def _env_on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def policy_c_apply_env() -> bool:
    return _env_on("GTOS_JEV_POLICY_C_APPLY")


def _incomplete(v: Any) -> bool:
    return v is None or v in ("PENDING", "PENDING_SHADOW", "")


def evaluate_policy_c_integer(state: Mapping[str, Any] | None) -> dict[str, Any]:
    """Current live 4-voter integer (STARVED). Keep as fail-closed fallback."""
    if not state or not isinstance(state, Mapping):
        return {
            "Choice": None,
            "reason": SKIP_STATE_MISSING,
            "skip": True,
            "refuse": False,
            "size_mult": None,
            "apply": False,
            "place": False,
            "news_invent": False,
            "composer": "integer",
        }
    if state.get("policy_c_skip_reason") == SKIP_STATE_MISSING or state.get("state_missing") is True:
        return {
            "Choice": None,
            "reason": SKIP_STATE_MISSING,
            "skip": True,
            "refuse": False,
            "size_mult": None,
            "apply": False,
            "place": False,
            "news_invent": False,
            "composer": "integer",
        }
    full_dark = bool(state.get("full_state_dark"))
    voters = [state.get(k) for k in _VOTER_KEYS]
    n_incomplete = sum(1 for v in voters if _incomplete(v))
    if full_dark:
        choice, reason, mult = CHOICE_STAND, "full_state_dark", 0.0
    elif n_incomplete >= 3:
        choice, reason, mult = CHOICE_TRIM, "incomplete_state", 0.75
    else:
        choice, reason, mult = CHOICE_FULL, "state_sufficient", 1.0
    refuse = bool(policy_c_apply_env() and choice == CHOICE_STAND)
    return {
        "Choice": choice,
        "reason": reason,
        "skip": False,
        "refuse": refuse,
        "size_mult": mult,
        "n_incomplete": n_incomplete,
        "full_state_dark": full_dark,
        "apply": policy_c_apply_env(),
        "place": False,
        "news_invent": False,
        "composer": "integer",
    }


def _choice_from_answers(answers: Mapping[str, Any]) -> tuple[str | None, float | None]:
    block = answers.get("policy_c_choice")
    if not isinstance(block, Mapping):
        return None, None
    choice = block.get("choice")
    conf = block.get("confidence")
    if choice not in {CHOICE_STAND, CHOICE_TRIM, CHOICE_FULL}:
        return None, None
    try:
        c = float(conf) if conf is not None else None
    except (TypeError, ValueError):
        c = None
    return str(choice), c


def _score(answers: Mapping[str, Any], key: str) -> float | None:
    block = answers.get(key)
    if isinstance(block, Mapping) and block.get("score") is not None:
        try:
            return float(block["score"])
        except (TypeError, ValueError):
            return None
    return None


def _noul(answers: Mapping[str, Any], key: str) -> float | None:
    block = answers.get(key)
    if isinstance(block, Mapping) and block.get("noul") is not None:
        try:
            return float(block["noul"])
        except (TypeError, ValueError):
            return None
    return None


def evaluate_policy_c(state: Mapping[str, Any] | None) -> dict[str, Any]:
    """Envelope skip + integer fallback + optional Jev over COMPLETE_STATE."""
    integer = evaluate_policy_c_integer(state)
    if integer.get("skip"):
        return integer
    if not _env_on("GTOS_JEV_POLICY_C_JEV_EVAL"):
        integer["jev_eval"] = False
        return integer

    # Local drafts; live land would import from src.judgment.*
    from policy_c_complete_state import policy_c_complete_state  # type: ignore
    from policy_c_questions import policy_c_questions  # type: ignore

    complete = policy_c_complete_state(state)
    ablation = os.environ.get("GTOS_JEV_POLICY_C_ABLATION", "core_speculative")
    include_place = _env_on("GTOS_JEV_POLICY_C_PLACE_CHOICE")
    questions = policy_c_questions(ablation=ablation, include_place=include_place)

    try:
        from src.judgment.jev_client import evaluate  # live path

        jev = evaluate(complete, questions=questions)  # requires jev_client patch
    except TypeError:
        # Unpatched client ignores questions= — FAIL-CLOSED, do not silently use 49q
        integer.update(
            {
                "reason": "jev_client_questions_kwarg_missing",
                "jev_eval": False,
                "fail_closed": True,
            }
        )
        return integer
    except Exception as exc:  # noqa: BLE001
        integer.update(
            {
                "reason": f"jev_dark_{type(exc).__name__}",
                "jev_eval": False,
                "fail_closed": True,
            }
        )
        return integer

    if not jev.get("ok"):
        integer.update(
            {
                "reason": f"jev_dark_{jev.get('skipped') or jev.get('error') or 'not_ok'}",
                "jev_eval": False,
                "fail_closed": True,
                "jev_receipt": {k: jev.get(k) for k in ("ok", "skipped", "error", "http_status", "calls_used")},
            }
        )
        return integer

    answers = jev.get("answers") or {}
    choice, conf = _choice_from_answers(answers)
    sev = _score(answers, "incomplete_severity")
    sufficient = _noul(answers, "state_sufficient")
    fail_closed = _env_on("GTOS_JEV_POLICY_C_FAIL_CLOSED") or os.environ.get(
        "GTOS_JEV_POLICY_C_FAIL_CLOSED", "1"
    ).strip() != "0"

    if choice is None:
        integer.update({"reason": "jev_dark_choice_unreadable", "fail_closed": True, "jev_eval": True})
        return integer
    if fail_closed and conf is not None and conf < 0.50 and choice == CHOICE_FULL:
        # low-confidence full → do not fail-open
        choice = CHOICE_TRIM if (sev is None or sev < 1.5) else integer["Choice"]
        reason = "low_confidence_no_fail_open"
    else:
        reason = "jev_policy_c_choice"

    if sufficient is not None and sufficient < 0.35 and choice == CHOICE_FULL:
        choice = CHOICE_TRIM
        reason = "state_sufficient_noul_blocks_full"

    size_mult = SIZE_MAP[choice]
    if choice == CHOICE_TRIM and not _env_on("GTOS_JEV_POLICY_C_TRIM_APPLY"):
        # label trim; do not haircut lots until hist-prove
        applied_mult = 1.0
    else:
        applied_mult = size_mult

    refuse = bool(policy_c_apply_env() and choice == CHOICE_STAND)
    out = {
        "Choice": choice,
        "reason": reason,
        "skip": False,
        "refuse": refuse,
        "size_mult": applied_mult,
        "size_mult_label": size_mult,
        "n_incomplete": complete.get("n_incomplete"),
        "full_state_dark": complete.get("full_state_dark"),
        "apply": policy_c_apply_env(),
        "place": False,  # default-until-prove; PLACE_CHOICE may stamp advisory only
        "news_invent": False,
        "composer": "jev_complete_state",
        "jev_eval": True,
        "confidence": conf,
        "incomplete_severity": sev,
        "state_sufficient_noul": sufficient,
        "integer_fallback_choice": integer.get("Choice"),
        "ablation": ablation,
    }
    if include_place:
        blk = answers.get("place_stand_delay")
        if isinstance(blk, Mapping):
            out["place_choice_advisory"] = blk.get("choice")
            out["place"] = False  # still no send from this helper
    return out
