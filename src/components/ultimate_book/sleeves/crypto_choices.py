"""Spot-exact Choices for crypto sleeve decision ifs.

The two sides of one condition are the alternatives. The unique highest
probability wins. Empty, tie, and error return None: the measured boolean
is not restored, and nothing is labeled unanswered as an absent mode.
Arithmetic warmup, on-surface membership, and the clock stay integers.
Does not close a position.
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
LOGIN = 0
_CACHE: dict[str, dict[str, Any]] = {}


def on_challenge() -> bool:
    forced = os.environ.get("GTOS_CRYPTO_CHOICE_FORCE")
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


def crypto_side(
    spot: str,
    measured: bool,
    true_name: str,
    false_name: str,
    instructions: str,
    *,
    true_text: str,
    false_text: str,
    facts: dict[str, Any] | None = None,
) -> str | None:
    """'true', 'false', or None.

    Off Challenge the measured boolean stands. On Challenge the unique
    highest probability picks the side. Empty, tie, and error are None.
    None does not restore the measured boolean.
    """

    crypto_side.last_side = None
    if true_name == false_name or not true_name or not false_name:
        _remember(
            spot,
            {
                "alternative": None,
                "unanswered": True,
                "error": "criteria",
                "order_send": False,
                "flatten": False,
            },
        )
        return None
    if not on_challenge():
        side = "true" if measured else "false"
        crypto_side.last_side = side
        crypto_side.last = {
            "question": spot,
            "side": side,
            "measured": bool(measured),
            "off_challenge": True,
            "order_send": False,
            "flatten": False,
        }
        return side
    fact = "true" if measured else "false"
    sent = f"{instructions} The condition measured {fact}."
    fact_text = json.dumps(facts or {}, sort_keys=True, default=str)
    digest = hashlib.sha256(f"{sent}|{fact_text}".encode("utf-8")).hexdigest()
    cache_key = f"{spot}|{digest}|{fact}"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        crypto_side.last = cached
        side = cached.get("side")
        crypto_side.last_side = side if side in {"true", "false"} else None
        return crypto_side.last_side
    criteria = {false_name: false_text, true_name: true_text}
    row = _post(spot, criteria, true_name, false_name, sent, cache_key, measured, facts or {})
    side = row.get("side")
    crypto_side.last_side = side if side in {"true", "false"} else None
    return crypto_side.last_side


crypto_side.last = {}
crypto_side.last_side = None


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
        "login": LOGIN,
        "ns": NS,
        "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
    safe_facts = {}
    for name, value in facts.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe_facts[str(name)] = value
        else:
            safe_facts[str(name)] = str(value)
    payload = {
        "state": {
            "spot": spot,
            "namespace": NS,
            "login": LOGIN,
            "measured": bool(measured),
            "facts": safe_facts,
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
            "User-Agent": "gtos-crypto-choice/1",
        },
    )
    wait = None
    for key_name in ("seconds_from_clock", "seconds_until_cycle", "cycle_wait"):
        raw_wait = safe_facts.get(key_name)
        try:
            number = float(raw_wait)
        except (TypeError, ValueError):
            continue
        if number == number and number > 0 and number not in (float("inf"), float("-inf")):
            wait = number if wait is None else min(wait, number)
    try:
        if wait is not None:
            handle = urllib.request.urlopen(req, timeout=wait)
        else:
            handle = urllib.request.urlopen(req)
        with handle as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        row["error"] = f"http_{exc.code}"
        row["key_source"] = source
        _remember(spot, row)
        return row
    except Exception as exc:
        row["error"] = type(exc).__name__
        row["key_source"] = source
        _remember(spot, row)
        return row
    answer = (body.get("answers") or {}).get(spot) or {}
    probs = answer.get("probabilities") if isinstance(answer, dict) else None
    if not isinstance(probs, dict) or not probs:
        row["error"] = "probabilities_missing"
        row["key_source"] = source
        _remember(spot, row)
        return row
    best = None
    best_p = None
    tied = False
    seen = False
    numeric: dict[str, float] = {}
    for name in order:
        if name not in probs or probs.get(name) is None:
            continue
        try:
            p = float(probs.get(name))
        except (TypeError, ValueError):
            continue
        if p != p:
            continue
        numeric[name] = p
        seen = True
        if best_p is None or p > best_p + 1e-12:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    alternative = None if (not seen) or tied or best is None else best
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
            "confidence": answer.get("confidence") if isinstance(answer, dict) else None,
            "model": body.get("model") or MODEL,
            "key_source": source,
            "error": None if side else "tie",
            "order_send": False,
            "flatten": False,
        }
    )
    if side is not None:
        _CACHE[cache_key] = row
    _remember(spot, row)
    return row


def _remember(spot: str, row: dict[str, Any]) -> None:
    crypto_side.last = row
    try:
        path = (
            Path(__file__).resolve().parents[4]
            / "pipeline_state"
            / "ultimate_book"
            / NS
            / "judgment"
            / "crypto_sleeve_choices.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        return
