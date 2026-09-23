"""Metals-sleeve decision conditions as Choices. Challenge 0 only.

The two sides of the condition are the alternatives. The unique highest
probability is the decision. Empty, tie, and error return None: the old
boolean is not restored, and there is no absent-mode label. Never raises.
Does not flatten. Does not send.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL = "jev-1.13.0"
NS = "operator"
_CACHE: dict[str, dict[str, Any]] = {}


def on_challenge() -> bool:
    forced = os.environ.get("GTOS_METALS_CHOICE_FORCE")
    if forced == "1":
        return True
    if forced == "0":
        return False
    argv = sys.argv
    for index, arg in enumerate(argv):
        if arg == NS:
            return True
        if arg == f"--namespace={NS}":
            return True
        if arg == "--namespace" and index + 1 < len(argv) and argv[index + 1] == NS:
            return True
    return False


def ask(
    spot: str,
    measured: bool,
    true_name: str,
    false_name: str,
    true_text: str,
    false_text: str,
    **facts: Any,
) -> str | None:
    """Two sides of one condition. None when there is no unique highest."""

    return metals_side(
        spot,
        bool(measured),
        true_name,
        false_name,
        f"Condition: {true_text} Which side of this condition is the decision?",
        true_text=true_text,
        false_text=false_text,
        facts=facts or None,
    )


def decision_stops(side: str | None) -> bool:
    """True unless the false side is the unique highest.

    Unanswered is not the false side, so the measured boolean is not applied.
    """

    return side != "false"


def metals_side(
    spot: str,
    measured: bool,
    true_name: str,
    false_name: str,
    instructions: str,
    *,
    true_text: str,
    false_text: str,
    facts: dict | None = None,
) -> str | None:
    """'true', 'false', or None.

    Off Challenge the measured boolean stands. On Challenge the unique
    highest probability picks the side. Empty, tie, and error are None.
    """

    metals_side.last_side = None
    if true_name == false_name or not true_name or not false_name:
        _remember(spot, {"alternative": None, "unanswered": True, "error": "criteria", "order_send": False, "flatten": False})
        return None
    clean = _jsonable(facts)
    if not on_challenge():
        side = "true" if measured else "false"
        metals_side.last_side = side
        return side
    fact = "true" if measured else "false"
    sent = f"{instructions} The condition measured {fact}."
    blob = sent + "\n" + json.dumps(clean, sort_keys=True, default=str)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    cache_key = f"{spot}|{digest}|{fact}"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        metals_side.last = cached
        side = cached.get("side")
        metals_side.last_side = side if side in {"true", "false"} else None
        return metals_side.last_side
    criteria = {
        false_name: false_text,
        true_name: true_text,
    }
    row = _post(spot, criteria, true_name, false_name, sent, cache_key, measured, clean)
    side = row.get("side")
    metals_side.last_side = side if side in {"true", "false"} else None
    return metals_side.last_side


metals_side.last = {}
metals_side.last_side = None


def _jsonable(facts: dict | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in (facts or {}).items():
        if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
            out[str(key)] = value
        elif isinstance(value, float):
            out[str(key)] = value if value == value and value not in (float("inf"), float("-inf")) else None
        else:
            try:
                out[str(key)] = float(value)
            except (TypeError, ValueError):
                out[str(key)] = str(value)
    return out


def _socket_wait(facts: dict | None) -> float | None:
    """Seconds until this bar prints, when that fact is already on the card.

    No expiry means no timeout.
    """

    if not isinstance(facts, dict):
        return None
    for key in ("seconds_until_print", "seconds_from_clock", "bar_deadline_s", "timeout_s"):
        raw = facts.get(key)
        if isinstance(raw, bool) or raw is None:
            continue
        try:
            number = float(raw)
        except (TypeError, ValueError):
            continue
        if number == number and number not in (float("inf"), float("-inf")) and number > 0:
            return number
    return None


def _returned_score(answer: Any) -> float | None:
    """A number the hop returned. A miss stays absent. It is not zero."""

    if not isinstance(answer, dict):
        return None
    for key in ("score", "value", "confidence"):
        if key not in answer or answer.get(key) is None or isinstance(answer.get(key), bool):
            continue
        try:
            number = float(answer.get(key))
        except (TypeError, ValueError):
            continue
        if number == number and number not in (float("inf"), float("-inf")):
            return number
    return None


def _post(
    spot: str,
    criteria: dict[str, str],
    true_name: str,
    false_name: str,
    instructions: str,
    cache_key: str,
    measured: bool,
    facts: dict[str, Any],
) -> dict[str, Any]:
    order = tuple(criteria)
    row: dict[str, Any] = {
        "question": spot,
        "alternative": None,
        "side": None,
        "unanswered": True,
        "probabilities": {},
        "flatten": False,
        "model": MODEL,
        "order_send": False,
        "measured": bool(measured),
        "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        from src.judgment.jev_client import (
            API_URL,
            _consume_call,
            calls_enabled,
            key_fingerprint,
            resolve_key,
        )
    except Exception as exc:
        row["error"] = type(exc).__name__
        _remember(spot, row)
        return row
    if not calls_enabled():
        row["error"] = "calls_off"
        _remember(spot, row)
        return row
    key, source = resolve_key()
    if not key:
        row["error"] = "key_missing"
        _remember(spot, row)
        return row
    if not _consume_call():
        row["error"] = "call_budget_exhausted"
        _remember(spot, row)
        return row
    payload = {
        "state": {
            "spot": spot,
            "namespace": NS,
            "login": 0,
            "measured": bool(measured),
            "facts": facts,
        },
        "model": MODEL,
        "questions": {
            spot: {
                "type": "choice",
                "instructions": instructions,
                "criteria": criteria,
            }
        },
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-metals-choice/1",
        },
    )
    wait = _socket_wait(facts)
    try:
        opened = urllib.request.urlopen(req, timeout=wait) if wait is not None else urllib.request.urlopen(req)
        with opened as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        row["error"] = f"http_{exc.code}"
        row["key_fingerprint"] = key_fingerprint(key)
        _remember(spot, row)
        return row
    except Exception as exc:
        row["error"] = type(exc).__name__
        row["key_fingerprint"] = key_fingerprint(key)
        _remember(spot, row)
        return row
    answer = (body.get("answers") or {}).get(spot) or {}
    if not isinstance(answer, dict):
        answer = {}
    returned = _returned_score(answer)
    probs = answer.get("probabilities") if isinstance(answer.get("probabilities"), dict) else None
    if not isinstance(probs, dict) or not probs:
        row["error"] = None if returned is not None else "probabilities_missing"
        if returned is not None:
            row["score"] = returned
        row["key_fingerprint"] = key_fingerprint(key)
        row["key_source"] = source
        _remember(spot, row)
        return row
    numeric: dict[str, float] = {}
    for name in order:
        if name not in probs or probs.get(name) is None or isinstance(probs.get(name), bool):
            continue
        try:
            p = float(probs.get(name))
        except (TypeError, ValueError):
            continue
        if p != p or p in (float("inf"), float("-inf")):
            continue
        numeric[name] = p
    try:
        from src.judgment.jev_questions import unique_highest

        alternative = unique_highest(numeric, order)
    except Exception:
        alternative = None
    side = None
    if alternative == true_name:
        side = "true"
    elif alternative == false_name:
        side = "false"
    row.update(
        {
            "alternative": alternative,
            "side": side,
            "unanswered": side is None,
            "probabilities": numeric,
            "probability": None if alternative is None else numeric.get(alternative),
            "model": body.get("model") or MODEL,
            "key_fingerprint": key_fingerprint(key),
            "key_source": source,
            "error": None if side else ("tie" if len(numeric) >= 2 else "empty"),
            "order_send": False,
            "flatten": False,
        }
    )
    if returned is not None:
        row["score"] = returned
    if side is not None:
        _CACHE[cache_key] = row
    _remember(spot, row)
    return row


def _repo() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "src" / "judgment").is_dir():
            return parent
    return here.parents[-1]


def _remember(spot: str, row: dict[str, Any]) -> None:
    metals_side.last = row
    try:
        path = (
            _repo()
            / "pipeline_state"
            / "ultimate_book"
            / NS
            / "judgment"
            / "metals_choices.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        return
