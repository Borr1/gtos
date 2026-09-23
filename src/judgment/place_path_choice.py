"""Place-path decisions that used to be booleans in front of a send.

Each question is the two sides of one condition. The unique highest
probability is the decision. An empty answer or a tie is not a decision
and does not restore the old boolean. This module does not send.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

_MODEL = "jev-1.13.0"
_NS = "operator"
_OPEN_TICKET = 294215389
_CACHE: dict[tuple, dict[str, Any]] = {}

_SPOTS = {
    "event_registry_high_window": {
        "instructions": (
            "Active exclusions for this symbol are on the state. "
            "Does an exclusion stop this send, or is the registry only a fact? "
            "Do not close an open ticket."
        ),
        "criteria": {
            "high_window_blocks": "An active exclusion covers this symbol. Do not send.",
            "no_blocking_exclusion": "No active exclusion stops this send.",
        },
        "continue_side": "no_blocking_exclusion",
    },
    "event_snapshot_drift": {
        "instructions": (
            "Whether the registry hash or version differs from the prior request is on the state. "
            "Does that difference stop this send? Do not close an open ticket."
        ),
        "criteria": {
            "snapshot_drift_blocks": "The registry moved against the prior request. Do not send.",
            "snapshot_still_the_request": "The registry does not stop this send.",
        },
        "continue_side": "snapshot_still_the_request",
    },
    "news_t60_market_chase": {
        "instructions": (
            "A native-limit requirement and whether this request is a native limit are on the state. "
            "Is this a market chase, or a send that can continue? Do not close an open ticket."
        ),
        "criteria": {
            "market_chase_forbidden": (
                "This request chases with a market order while a native limit is required. Do not send."
            ),
            "limit_or_not_required": "This request is a native limit, or a native limit is not required.",
        },
        "continue_side": "limit_or_not_required",
    },
}


def _unique(probabilities: dict[str, Any] | None, order: tuple[str, ...]) -> str | None:
    """Unique highest. A missing probability is not a vote and is not zero."""
    try:
        from src.judgment.jev_questions import unique_highest
    except Exception:
        return None
    try:
        return unique_highest(probabilities, order)
    except Exception:
        return None


def _receipt(row: dict[str, Any]) -> None:
    try:
        from pathlib import Path

        path = (
            Path(__file__).resolve().parents[2]
            / "pipeline_state"
            / "ultimate_book"
            / _NS
            / "judgment"
            / "place_path_choices.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        return


def decide_place_path(
    *,
    symbol: Any = None,
    exclusions_present: bool = False,
    exclusion_count: int = 0,
    snapshot_drift: bool = False,
    registry_read_error: bool = False,
    require_native_limit: bool = False,
    native_limit: bool = False,
    include_chase: bool = False,
) -> dict[str, Any]:
    """Ask the place-path spots. ``continues`` is true only when every spot's continue side is the unique highest.

    Does not send. Does not restore a boolean when a spot is unanswered.
    """
    ids = ["event_registry_high_window", "event_snapshot_drift"]
    if include_chase:
        ids.append("news_t60_market_chase")
    state = {
        "symbol": str(symbol or ""),
        "exclusions_present": bool(exclusions_present),
        "exclusion_count": int(exclusion_count or 0),
        "snapshot_drift": bool(snapshot_drift),
        "registry_read_error": bool(registry_read_error),
        "require_native_limit": bool(require_native_limit),
        "native_limit": bool(native_limit),
        "open_ticket_do_not_close": _OPEN_TICKET,
    }
    fact_key = tuple(state.items())
    sides: dict[str, str | None] = {}
    probabilities: dict[str, dict[str, float]] = {}
    pending = []
    for spot in ids:
        cached = _CACHE.get((spot, fact_key))
        if isinstance(cached, dict) and "side" in cached:
            sides[spot] = cached.get("side")
            probabilities[spot] = dict(cached.get("probabilities") or {})
        else:
            pending.append(spot)

    error = None
    model = _MODEL
    if pending:
        posted = _post(state, pending)
        error = posted.get("error")
        model = posted.get("model") or _MODEL
        for spot in pending:
            order = tuple(_SPOTS[spot]["criteria"])
            probs = posted.get("probabilities", {}).get(spot) or {}
            side = _unique(probs, order)
            sides[spot] = side
            probabilities[spot] = probs
            _CACHE[(spot, fact_key)] = {"side": side, "probabilities": probs}

    reason = None
    continues = True
    for spot in ids:
        side = sides.get(spot)
        if side is None:
            continues = False
            reason = reason or ("no_decision:" + spot)
        elif side != _SPOTS[spot]["continue_side"]:
            continues = False
            reason = reason or side
    row = {
        "sides": sides,
        "probabilities": probabilities,
        "continues": continues,
        "reason": None if continues else reason,
        "model": model,
        "error": error,
        "send": False,
        "flatten": False,
        "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _receipt(row)
    return row


def _post(state: dict[str, Any], spots: list[str]) -> dict[str, Any]:
    """One post for every pending spot. No planted wait. An empty answer is not a side."""
    out: dict[str, Any] = {"probabilities": {}, "model": _MODEL, "error": None}
    questions = {}
    for spot in spots:
        spec = _SPOTS[spot]
        questions[spot] = {
            "type": "choice",
            "instructions": spec["instructions"],
            "criteria": dict(spec["criteria"]),
        }
    try:
        from src.judgment.jev_client import evaluate
    except Exception as exc:  # noqa: BLE001
        out["error"] = type(exc).__name__
        return out
    try:
        receipt = evaluate(state, questions=questions, merge_sleeve=False, model=_MODEL)
    except Exception as exc:  # noqa: BLE001
        out["error"] = type(exc).__name__
        return out
    if not isinstance(receipt, dict):
        out["error"] = "evaluate_not_a_dict"
        return out
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or not answers:
        out["error"] = str(receipt.get("error") or receipt.get("skipped") or "probabilities_missing")
        return out
    parsed: dict[str, dict[str, float]] = {}
    for spot in spots:
        answer = answers.get(spot) if isinstance(answers.get(spot), dict) else {}
        probs = answer.get("probabilities") if isinstance(answer, dict) else None
        numeric: dict[str, float] = {}
        if isinstance(probs, dict):
            for name, val in probs.items():
                if isinstance(val, bool) or val is None:
                    continue
                try:
                    number = float(val)
                except (TypeError, ValueError):
                    continue
                if number == number:
                    numeric[str(name)] = number
        parsed[spot] = numeric
        if not numeric:
            out["error"] = out["error"] or "probabilities_missing"
    out["probabilities"] = parsed
    reported = receipt.get("model")
    out["model"] = reported if isinstance(reported, str) and reported.strip() else _MODEL
    if receipt.get("ok") is False and not out["error"]:
        out["error"] = str(receipt.get("error") or receipt.get("skipped") or "post_failed")
    return out
