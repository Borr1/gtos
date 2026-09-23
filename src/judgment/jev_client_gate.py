"""s19 usage-ramp — evaluate() wrapper for every-gate observe.

Live `jev_client.evaluate` POSTs `https://api.typesafe.ai/v1/systemone` with
`symbol_fanout_questions()` and has no `questions=` / `gate_id` override.
Code default remains `DEFAULT_MAX_CALLS=200`; env `GTOS_JEV_MAX_CALLS`
already claimed 500000 on Challenge. This module:

- one fanout POST per candidate (TypeSafe-correct; not 48 HTTP POSTs)
- optional pack questions override (receipt `gate_id` is NOT sent)
- process-local fanout dedup (`GTOS_JEV_FANOUT_DEDUP` default-on)
- fail-closed helpers if Jev dark
- never places, never invents NEWS_PROTOCOL

Env already live (do not invent a second observe flag):
  GTOS_JEV_A1_OBSERVE_EVERY=1
  GTOS_JEV_A1_LOG / GTOS_JEV_ALIVE_SHADOW
  GTOS_JEV_A1_DEDUPE=1
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from typing import Any, Callable, Mapping

API_URL = "https://api.typesafe.ai/v1/systemone"
PROPOSED_DEFAULT_MAX_CALLS = 500_000  # land into jev_client.DEFAULT_MAX_CALLS
CODE_DEFAULT_MAX_CALLS_NOW = 200
CHALLENGE_LOGIN = 0
NS = "operator"

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off"})

_dedup_lock = threading.Lock()
_DEDUP: dict[str, dict[str, Any]] = {}

EvaluateFn = Callable[..., dict[str, Any]]


def _env_on(name: str, default: str = "") -> bool:
    return os.environ.get(name, default).strip().lower() in _TRUTHY


def _env_off(name: str, default: str = "") -> bool:
    return os.environ.get(name, default).strip().lower() in _FALSY


def observe_every_enabled() -> bool:
    """A1_OBSERVE_EVERY already env. Requires A1_LOG | ALIVE_SHADOW."""
    if not _env_on("GTOS_JEV_A1_OBSERVE_EVERY"):
        return False
    return _env_on("GTOS_JEV_A1_LOG") or _env_on("GTOS_JEV_ALIVE_SHADOW")


def fanout_dedup_enabled() -> bool:
    return not _env_off("GTOS_JEV_FANOUT_DEDUP", "1")


def per_gate_post_enabled() -> bool:
    """Ablation only. Do not enable on Challenge live."""
    return _env_on("GTOS_JEV_PER_GATE_POST")


def fail_closed_dark_enabled() -> bool:
    return _env_on("GTOS_JEV_FAIL_CLOSED_DARK", "1") or _env_on("GTOS_JEV_FAIL_CLOSED_DARK")


def questions_id(questions: Mapping[str, Any] | None) -> str:
    if not questions:
        return "symbol_fanout"
    return ",".join(sorted(str(k) for k in questions.keys()))


def dark(receipt: Mapping[str, Any] | None) -> bool:
    if not receipt:
        return True
    if receipt.get("ok") is True and receipt.get("answers"):
        return False
    return True


def fail_closed_stand(receipt: Mapping[str, Any] | None, *, reason: str) -> dict[str, Any]:
    rec = dict(receipt or {})
    return {
        "ok": False,
        "dark": True,
        "decision": "STAND",
        "refuse_new": True,
        "size_mult": 1.0,
        "place": False,
        "broker_effect": False,
        "news_invent": False,
        "reason": reason or rec.get("skipped") or rec.get("error") or "jev_dark",
        "jev": {k: rec.get(k) for k in ("ok", "skipped", "error", "model", "usage")},
        "never_place_eternal": False,
        "place_policy": "default_off_until_hist_prove",
        "challenge_login": CHALLENGE_LOGIN,
        "ns": NS,
    }


def _dedup_key(state: Mapping[str, Any], questions: Mapping[str, Any] | None) -> str:
    blob = json.dumps(
        {"state": state, "qid": questions_id(questions)},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _live_evaluate(
    state: dict[str, Any],
    *,
    timeout_s: float,
    questions: Mapping[str, Any] | None,
) -> dict[str, Any]:
    from src.judgment.jev_client import (  # noqa: PLC0415
        API_URL as LIVE_URL,
        MODEL,
        _consume_call,
        _skip,
        calls_enabled,
        calls_remaining,
        calls_used,
        key_fingerprint,
        resolve_key,
    )
    from src.judgment.jev_questions import (  # noqa: PLC0415
        symbol_fanout_questions,
        systemone_payload,
    )

    key, source = resolve_key()
    model = MODEL
    q = dict(questions) if questions is not None else symbol_fanout_questions()
    if not key:
        return _skip("TYPESAFE_key_absent", model)
    if not calls_enabled():
        return _skip("GTOS_JEV_A1_CALL_off", model, would_payload_keys=list(q))
    if not _consume_call():
        return _skip("call_budget_exhausted", model)

    if questions is None:
        body_obj = systemone_payload(state, model=model)
    else:
        body_obj = {"state": state, "model": model, "questions": q}
    body = json.dumps(body_obj).encode("utf-8")

    import urllib.error  # noqa: PLC0415
    import urllib.request  # noqa: PLC0415

    req = urllib.request.Request(
        LIVE_URL or API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-judgment/s19-usage-wires",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return {
            "ok": True,
            "skipped": None,
            "model": payload.get("model") or model,
            "answers": payload.get("answers") or {},
            "usage": payload.get("usage") or {},
            "key_source": source,
            "key_fingerprint": key_fingerprint(key),
            "http_status": 200,
            "calls_used": calls_used(),
            "calls_remaining": calls_remaining(),
        }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "skipped": None,
            "error": f"http_{exc.code}",
            "http_status": exc.code,
            "model": model,
            "answers": {},
            "key_source": source,
            "key_fingerprint": key_fingerprint(key),
            "calls_used": calls_used(),
            "calls_remaining": calls_remaining(),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "skipped": None,
            "error": type(exc).__name__,
            "http_status": None,
            "model": model,
            "answers": {},
            "key_source": source,
            "key_fingerprint": key_fingerprint(key),
            "calls_used": calls_used(),
            "calls_remaining": calls_remaining(),
        }


def evaluate_for_gate(
    state: dict[str, Any] | None,
    *,
    timeout_s: float = 8.0,
    questions: Mapping[str, Any] | None = None,
    gate_id: str | None = None,
    evaluate_fn: EvaluateFn | None = None,
) -> dict[str, Any]:
    """POST /v1/systemone. Never raises into a fire path. Never places.

    `gate_id` is stamped on the receipt only — not sent as inference.
    """
    payload_state = dict(state or {})
    payload_state.setdefault("news_join", payload_state.get("news_join") or "STATE_MISSING")
    payload_state.setdefault("place", False)
    try:
        if evaluate_fn is not None:
            rec = dict(evaluate_fn(payload_state) or {})
        else:
            rec = _live_evaluate(payload_state, timeout_s=timeout_s, questions=questions)
    except Exception as exc:  # noqa: BLE001
        rec = {
            "ok": False,
            "skipped": f"evaluate_raised:{type(exc).__name__}",
            "error": type(exc).__name__,
            "answers": {},
        }
    rec.setdefault("answers", rec.get("answers") or {})
    rec["gate_id"] = gate_id
    rec["place"] = False
    rec["broker_effect"] = False
    rec["news_invent"] = False
    rec["challenge_login"] = CHALLENGE_LOGIN
    rec["questions_id"] = questions_id(questions)
    rec["dark"] = dark(rec)
    return rec


def evaluate_dedup(
    state: dict[str, Any] | None,
    *,
    questions: Mapping[str, Any] | None = None,
    gate_id: str | None = None,
    timeout_s: float = 8.0,
    evaluate_fn: EvaluateFn | None = None,
    cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """One fanout POST per identical (state, questions). Bypass if PER_GATE_POST=1."""
    payload_state = dict(state or {})
    if per_gate_post_enabled() or not fanout_dedup_enabled():
        rec = evaluate_for_gate(
            payload_state,
            timeout_s=timeout_s,
            questions=questions,
            gate_id=gate_id,
            evaluate_fn=evaluate_fn,
        )
        rec["deduped"] = False
        return rec

    key = _dedup_key(payload_state, questions)
    store = cache if cache is not None else _DEDUP
    with _dedup_lock:
        hit = store.get(key)
        if hit is not None:
            rec = dict(hit)
            rec["deduped"] = True
            rec["gate_id"] = gate_id
            rec["place"] = False
            rec["broker_effect"] = False
            rec["news_invent"] = False
            return rec
        rec = evaluate_for_gate(
            payload_state,
            timeout_s=timeout_s,
            questions=questions,
            gate_id=gate_id,
            evaluate_fn=evaluate_fn,
        )
        rec["deduped"] = False
        store[key] = dict(rec)
        return rec


def reset_dedup(cache: dict[str, dict[str, Any]] | None = None) -> None:
    store = cache if cache is not None else _DEDUP
    with _dedup_lock:
        store.clear()


def budget_land_note() -> dict[str, Any]:
    return {
        "code_default_now": CODE_DEFAULT_MAX_CALLS_NOW,
        "proposed_default": PROPOSED_DEFAULT_MAX_CALLS,
        "env_override": "GTOS_JEV_MAX_CALLS",
        "file": "src/judgment/jev_client.py",
        "place": False,
        "note": (
            "Chair claimed usage already uncapped via env on Challenge PID. "
            "Box PR41 still DEFAULT_MAX_CALLS=200 — new PIDs without env die at 200. "
            "Land const 500000; env still wins."
        ),
    }
