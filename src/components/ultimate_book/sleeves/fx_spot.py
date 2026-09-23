"""Two-sided spot Choice for one FX sleeve condition.

Each question has two criteria: the two sides of that condition. The unique
highest probability is the decision. A tie, an empty distribution, or a
failed read is not a decision. The caller does not put the old condition
back in charge, and this module does not name an unanswered read.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Mapping

MODEL = "jev-1.13.0"
_CACHE: dict[str, dict[str, str | None]] = {}


def book_state(sleeve: str, symbol: str, **facts: Any) -> dict[str, Any]:
    """Named facts for one FX spot. The open gold ticket stays a fact."""
    state: dict[str, Any] = {
        "book": "challenge",
        "namespace": "operator",
        "sleeve": sleeve,
        "symbol": symbol,
        "open_gold": 294215389,
    }
    state.update(facts)
    return state


def q(side_a: str, text_a: str, side_b: str, text_b: str, instructions: str) -> dict[str, str]:
    return {
        "a": side_a,
        "a_text": text_a,
        "b": side_b,
        "b_text": text_b,
        "instructions": instructions,
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return None
        return float(value)
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return _jsonable(item())
        except Exception:
            return str(value)
    return str(value)


def _unique(probs: Any, names: tuple[str, str]) -> str | None:
    if not isinstance(probs, dict) or not probs:
        return None
    best: str | None = None
    best_p = -1.0
    tied = False
    for name in names:
        try:
            prob = float(probs.get(name, 0.0) or 0.0)
        except (TypeError, ValueError):
            prob = 0.0
        if best is None or prob > best_p + 1e-12:
            best = name
            best_p = prob
            tied = False
        elif abs(prob - best_p) <= 1e-12:
            tied = True
    if tied or best is None:
        return None
    return best


def continues(picks: Mapping[str, str | None], questions: Mapping[str, Mapping[str, str]]) -> bool:
    """True only when every question's continue side is the unique highest."""
    for qid, spec in questions.items():
        if picks.get(qid) != spec["a"]:
            return False
    return bool(questions)


def unique_sides(
    questions: Mapping[str, Mapping[str, str]],
    state: Mapping[str, Any],
    cache_key: str,
) -> dict[str, str | None]:
    """Ask each spot. Return the unique highest side, or None when it is not unique.

    ``spec['a']`` is the continue side. ``spec['b']`` is the other side.
    """
    cached = _CACHE.get(cache_key)
    if cached is not None:
        unique_sides.receipt = {
            "cached": True,
            "picks": dict(cached),
            "probabilities": {},
            "error": None,
            "model": MODEL,
        }
        return dict(cached)

    picks: dict[str, str | None] = {qid: None for qid in questions}
    receipt: dict[str, Any] = {
        "cached": False,
        "picks": picks,
        "probabilities": {},
        "error": None,
        "model": MODEL,
        "http_status": None,
    }
    unique_sides.receipt = receipt
    order: dict[str, tuple[str, str]] = {}
    payload_questions: dict[str, Any] = {}
    for qid, spec in questions.items():
        side_a = spec["a"]
        side_b = spec["b"]
        order[qid] = (side_a, side_b)
        payload_questions[qid] = {
            "type": "choice",
            "instructions": spec["instructions"],
            "criteria": {side_a: spec["a_text"], side_b: spec["b_text"]},
        }
    try:
        from src.judgment.jev_client import (  # type: ignore
            API_URL,
            _consume_call,
            calls_enabled,
            resolve_key,
        )
    except Exception as exc:
        receipt["error"] = type(exc).__name__
        return picks
    if not calls_enabled():
        receipt["error"] = "calls_off"
        return picks
    if not _consume_call():
        receipt["error"] = "call_budget_exhausted"
        return picks
    key, source = resolve_key()
    receipt["key_source"] = source
    if not key:
        receipt["error"] = "key_missing"
        return picks
    payload = {
        "state": _jsonable(dict(state)),
        "model": MODEL,
        "questions": payload_questions,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-fx-spot/1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            receipt["http_status"] = getattr(resp, "status", 200)
    except urllib.error.HTTPError as exc:
        receipt["error"] = f"http_{exc.code}"
        receipt["http_status"] = exc.code
        return picks
    except Exception as exc:
        receipt["error"] = type(exc).__name__
        return picks
    receipt["model"] = body.get("model") or MODEL
    answers = body.get("answers") or {}
    probs_out: dict[str, Any] = {}
    decided = True
    for qid, names in order.items():
        answer = answers.get(qid) or {}
        probs = answer.get("probabilities") if isinstance(answer, dict) else None
        winner = _unique(probs, names)
        picks[qid] = winner
        if isinstance(probs, dict):
            probs_out[qid] = {str(name): probs.get(name) for name in names}
        if winner is None:
            decided = False
    receipt["probabilities"] = probs_out
    receipt["picks"] = dict(picks)
    if not decided:
        receipt["error"] = receipt["error"] or "no_unique_highest"
        return picks
    _CACHE[cache_key] = dict(picks)
    return picks


unique_sides.receipt = {}
