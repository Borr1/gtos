"""Spot-exact Choice for one DSP sleeve condition.

Each question has the two sides of that condition. The unique highest
probability is the decision. An empty answer, a tie, and a transport
error are not a decision: the old boolean is not restored. This module
never labels an unanswered hop, never places, and never flattens.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

_MODEL = "jev-1.13.0"
_CACHE: dict[str, bool] = {}


def unique_highest(
    probabilities: Mapping[str, Any] | None,
    order: tuple[str, ...] | list[str],
) -> str | None:
    """The decision is the unique highest probability.

    An empty map is not a decision. A tie is not a decision. A bare label
    is not a probability. The first name is not a default.
    """
    if not isinstance(probabilities, Mapping) or not probabilities:
        return None
    best: str | None = None
    best_p = -1.0
    tied = False
    for name in order:
        raw = probabilities.get(name, 0.0)
        try:
            p = float(raw or 0.0)
        except (TypeError, ValueError):
            p = 0.0
        if best is None or p > best_p + 1e-12:
            best = str(name)
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    if tied or best is None:
        return None
    return best


def _probs(block: Any) -> dict[str, float] | None:
    if not isinstance(block, dict):
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, dict) or not raw:
        return None
    out: dict[str, float] = {}
    for key, value in raw.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return out or None


def spot_winners(
    answers: Mapping[str, Any] | None,
    spots: list[dict[str, str]],
) -> dict[str, str | None]:
    """One winner per spot. None means that spot is not a decision."""
    answers = answers if isinstance(answers, Mapping) else {}
    winners: dict[str, str | None] = {}
    for spot in spots:
        order = (spot["emit"], spot["other"])
        block = answers.get(spot["id"])
        winners[spot["id"]] = unique_highest(_probs(block), order)
    return winners


def _decided_emit(winners: Mapping[str, str | None], spots: list[dict[str, str]]) -> bool | None:
    """True when every spot's unique highest is its emit side.

    None when any spot has no unique highest. False when a unique highest
    is the other side. Never fills a miss from a measured boolean.
    """
    if not spots:
        return None
    for spot in spots:
        winner = winners.get(spot["id"])
        if winner is None:
            return None
        if winner != spot["emit"]:
            return False
    return True


def _questions(spots: list[dict[str, str]]) -> dict[str, Any]:
    questions: dict[str, Any] = {}
    for spot in spots:
        emit = spot["emit"]
        other = spot["other"]
        if emit == other:
            raise ValueError("spot sides must differ")
        questions[spot["id"]] = {
            "type": "choice",
            "instructions": spot["instructions"],
            "criteria": {
                emit: spot["emit_text"],
                other: spot["other_text"],
            },
        }
    return questions


def _receipt(row: dict[str, Any]) -> None:
    try:
        from pathlib import Path

        path = (
            Path(__file__).resolve().parents[4]
            / "pipeline_state"
            / "ultimate_book"
            / "operator"
            / "judgment"
            / "dsp_spot_choice.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        return


def _post(facts: Mapping[str, Any], spots: list[dict[str, str]]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "model": _MODEL,
        "winners": {},
        "emit": False,
        "decided": False,
        "error": None,
        "flatten": False,
    }
    try:
        from src.judgment.jev_client import (
            API_URL,
            _consume_call,
            calls_enabled,
            resolve_key,
        )
    except Exception as exc:
        row["error"] = type(exc).__name__
        return row
    if not calls_enabled():
        row["error"] = "calls_off"
        return row
    key, _source = resolve_key()
    if not key:
        row["error"] = "key_missing"
        return row
    if not _consume_call():
        row["error"] = "call_budget_exhausted"
        return row
    payload = {
        "state": dict(facts),
        "model": _MODEL,
        "questions": _questions(spots),
    }
    body = json.dumps(payload, default=str).encode("utf-8")
    req_headers = {
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "User-Agent": "gtos-dsp-spot/1",
    }
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers=req_headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        row["error"] = f"http_{exc.code}"
        return row
    except Exception as exc:
        row["error"] = type(exc).__name__
        return row
    answers = parsed.get("answers") if isinstance(parsed, dict) else None
    winners = spot_winners(answers if isinstance(answers, Mapping) else None, spots)
    decided = _decided_emit(winners, spots)
    row["model"] = (parsed.get("model") if isinstance(parsed, dict) else None) or _MODEL
    row["winners"] = winners
    row["decided"] = decided is not None
    row["emit"] = decided is True
    if decided is None:
        row["error"] = "no_unique_highest"
    return row


def spots_allow_emit(
    facts: Mapping[str, Any],
    spots: list[dict[str, str]],
    cache_key: str,
    answers: Mapping[str, Any] | None = None,
) -> bool:
    """Emit only when every spot's unique highest is that spot's emit side.

    A passed ``answers`` map is the same card, already in hand. It is not
    the old boolean. Missing, tied, and failed cards do not emit.
    """
    if answers is not None:
        decided = _decided_emit(spot_winners(answers, spots), spots)
        return decided is True
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    row = _post(facts, spots)
    _receipt({
        "cache_key": cache_key,
        "sleeve": facts.get("sleeve"),
        "symbol": facts.get("symbol"),
        "model": row.get("model"),
        "winners": row.get("winners"),
        "emit": row.get("emit"),
        "decided": row.get("decided"),
        "error": row.get("error"),
        "flatten": False,
    })
    if row.get("decided") is True:
        _CACHE[cache_key] = bool(row.get("emit"))
        return bool(row.get("emit"))
    return False
