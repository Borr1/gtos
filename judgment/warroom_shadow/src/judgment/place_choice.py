"""Owner-unlocked Jev place Choice — Challenge APPLY only.

Owner WORD 2026-09-21: "yes unlock, no reason to be afraid. God is with us."
Chair ENFORCE: Jev may PLACE / STAND / DELAY / REMINT / FLATTEN_CANDIDATE
when GTOS_JEV_PLACE_APPLY=1 on Challenge ns/login. Printer still prints.
ENV-* integers unchanged. Never invent NEWS_PROTOCOL.
SHADOW proves continue in parallel — this module is the live place gate.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Mapping

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_CHALLENGE_NS = frozenset({"operator"})
_CHALLENGE_LOGIN = frozenset({"0", 0})

PLACE_CRITERIA = {
    "PLACE": "Fire now — state discriminating; identity/sleeve/side ready; writer may order_send",
    "STAND": "Do not place this cycle — refuse admit / skip fire",
    "DELAY": "Wait — incomplete or ambiguous; retry next cycle",
    "REMINT": "Prefer remint sibling / re-entry path over fresh place",
    "FLATTEN_CANDIDATE": "Prefer flatten/derisk over new risk (writer decides envelope)",
}


def place_apply_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get("GTOS_JEV_PLACE_APPLY", "")).strip().lower() in _TRUTHY


def _challenge_ok(intent: Any, *, login: Any = None, namespace: str | None = None) -> bool:
    ns = str(namespace or os.environ.get("GTOS_NAMESPACE") or os.environ.get("GTOS_BOOK_NAMESPACE") or "").strip()
    details = getattr(intent, "details", None) if intent is not None else None
    if isinstance(details, dict):
        ns = ns or str(details.get("namespace") or "")
    if ns and ns not in _CHALLENGE_NS and "ftmo_f5" not in ns.lower():
        # also allow when login matches even if ns blank
        if login is None or str(login) not in {str(x) for x in _CHALLENGE_LOGIN}:
            return ns in _CHALLENGE_NS or ns == ""
    if login is not None and str(login) not in {str(x) for x in _CHALLENGE_LOGIN}:
        # if login known and not challenge, block
        if str(login).isdigit() and str(login) not in {"0"}:
            return False
    return True


def _intent_fields(intent: Any) -> dict[str, Any]:
    symbol = str(getattr(intent, "symbol", None) or getattr(intent, "instrument", None) or "")
    sleeve = str(getattr(intent, "sleeve", None) or getattr(intent, "tag", None) or "")
    side = str(getattr(intent, "side", None) or getattr(intent, "direction", None) or "")
    details = getattr(intent, "details", None)
    if isinstance(details, dict):
        symbol = symbol or str(details.get("symbol") or "")
        sleeve = sleeve or str(details.get("sleeve") or details.get("tag") or "")
        side = side or str(details.get("side") or "")
    return {"symbol": symbol, "sleeve": sleeve, "side": side, "tag": sleeve}


def _state_hash(state: dict[str, Any]) -> str:
    blob = json.dumps(state, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def _menu_hashes(criteria: dict[str, str]) -> tuple[str, str]:
    keys = list(criteria.keys())
    menu = hashlib.sha256("|".join(keys).encode()).hexdigest()[:16]
    order = hashlib.sha256(">".join(keys).encode()).hexdigest()[:16]
    return menu, order


def build_place_state(intent: Any, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    fields = _intent_fields(intent)
    state = {
        "gate": "jev_place_choice",
        "identity": fields,
        "symbol": fields["symbol"],
        "sleeve": fields["sleeve"],
        "side": fields["side"],
        "place_context": {
            "writer_ready": True,
            "owner_unlock_20260921": True,
            "apply_flag": place_apply_enabled(),
        },
        "clock": {"as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
    }
    if extra:
        state.update(extra)
    state["state_hash"] = _state_hash(state)
    return state


def evaluate_place_choice(
    intent: Any,
    *,
    environ: Mapping[str, str] | None = None,
    login: Any = None,
    namespace: str | None = None,
    extra_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return {action, refuse_place, source, stamps, ...}. Fail-open to PLACE when dark if APPLY off; fail-closed STAND when APPLY on and API dark? Owner: unlock — fail-open DELAY when dark under APPLY."""
    if not place_apply_enabled(environ):
        return {
            "action": "SKIP_APPLY_OFF",
            "refuse_place": False,
            "source": "apply_off",
            "never_place": False,  # unlock doctrine; gate simply off
            "owner_unlock": True,
        }
    if not _challenge_ok(intent, login=login, namespace=namespace):
        return {
            "action": "SKIP_NOT_CHALLENGE",
            "refuse_place": False,
            "source": "ns_login_gate",
            "owner_unlock": True,
        }

    state = build_place_state(intent, extra=extra_state)
    menu_hash, option_order_hash = _menu_hashes(PLACE_CRITERIA)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stamps = {
        "menu_hash": menu_hash,
        "option_order_hash": option_order_hash,
        "state_hash": state.get("state_hash"),
        "model_id": "jev-1.13.0",
        "run_id": run_id,
        "owner_unlock": True,
    }

    try:
        from .jev_client import evaluate
    except Exception as exc:
        return {
            "action": "DELAY",
            "refuse_place": True,
            "source": "jev_client_import_fail",
            "error": type(exc).__name__,
            "stamps": stamps,
        }

    # System One uses symbol_fanout; also stamp place intent into state for model
    state["place_menu"] = list(PLACE_CRITERIA.keys())
    state["place_instructions"] = (
        "Owner unlocked Jev place on Challenge. Choose PLACE only when state "
        "is discriminating and fire is ready. Prefer STAND or DELAY when "
        "ambiguous. REMINT/FLATTEN_CANDIDATE only when clearer than new risk. "
        "Never invent news. Pre-entry only."
    )

    try:
        ts = evaluate(state)
    except Exception as exc:
        return {
            "action": "DELAY",
            "refuse_place": True,
            "source": "evaluate_raise",
            "error": type(exc).__name__,
            "stamps": stamps,
        }

    if not isinstance(ts, dict) or ts.get("ok") is not True:
        return {
            "action": "DELAY",
            "refuse_place": True,
            "source": "typesafe_dark",
            "typesafe": {k: ts.get(k) for k in ("skipped", "error", "http_status") } if isinstance(ts, dict) else {},
            "stamps": stamps,
        }

    answers = ts.get("answers") or {}
    # Prefer explicit place_choice if present; else map from flow_stance / state_sufficient
    pick = None
    if isinstance(answers, dict):
        raw = answers.get("place_choice") or answers.get("jev_place")
        if isinstance(raw, dict):
            pick = raw.get("id") or raw.get("label") or raw.get("answer") or raw.get("choice")
        elif raw:
            pick = raw
        if not pick:
            ss = answers.get("state_sufficient")
            if isinstance(ss, dict):
                ss_v = ss.get("answer", ss.get("noul", ss.get("value")))
            else:
                ss_v = ss
            flow = answers.get("flow_stance")
            if isinstance(flow, dict):
                flow = flow.get("answer") or flow.get("choice") or flow.get("id")
            if ss_v is False or str(ss_v).lower() in {"false", "no", "0"}:
                pick = "STAND"
            elif str(flow).lower() in {"against_flow"}:
                pick = "DELAY"
            else:
                pick = "PLACE"

    action = str(pick or "DELAY").upper()
    if action not in PLACE_CRITERIA:
        # fuzzy
        for k in PLACE_CRITERIA:
            if k in action:
                action = k
                break
        else:
            action = "DELAY"

    refuse = action in {"STAND", "DELAY"}
    return {
        "action": action,
        "refuse_place": refuse,
        "source": "typesafe_systemone",
        "stamps": stamps,
        "calls_used": ts.get("calls_used"),
        "usage": ts.get("usage"),
        "owner_unlock": True,
        "never_place": False,
        "broker_effect": action in {"PLACE", "REMINT", "FLATTEN_CANDIDATE"},
    }
