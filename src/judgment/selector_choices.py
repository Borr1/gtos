"""Selector V4 decision conditions as Choices. Challenge 0 only.

The two sides of the condition are the alternatives. The unique highest
probability is the decision. Empty, tie, and error return None: the old
boolean is not restored, and nothing is labeled jev_absent. Never raises.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL = "jev-1.13.0"
NS = "operator"
_CACHE: dict[str, dict[str, Any]] = {}
_INFLIGHT: set[str] = set()
_LOCK = threading.Lock()


def on_challenge() -> bool:
    forced = os.environ.get("GTOS_SELECTOR_CHOICE_FORCE")
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


def selector_side(
    spot: str,
    measured: bool,
    true_name: str,
    false_name: str,
    instructions: str,
    *,
    true_text: str,
    false_text: str,
) -> str | None:
    """'true', 'false', or None.

    Off Challenge the measured boolean stands. On Challenge the unique
    highest probability picks the side. Empty, tie, and error are None.
    """

    selector_side.last_side = None
    if true_name == false_name or not true_name or not false_name:
        _remember(spot, {"alternative": None, "unanswered": True, "error": "criteria", "order_send": False})
        return None
    if not on_challenge():
        side = "true" if measured else "false"
        selector_side.last_side = side
        return side
    fact = "true" if measured else "false"
    sent = f"{instructions} The condition measured {fact}."
    digest = hashlib.sha256(sent.encode("utf-8")).hexdigest()[:16]
    cache_key = f"{spot}|{digest}|{fact}"
    with _LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None and cached.get("side") in {"true", "false"}:
            selector_side.last = cached
            selector_side.last_side = cached.get("side")
            return selector_side.last_side
        if cache_key in _INFLIGHT:
            return None
        _INFLIGHT.add(cache_key)
    criteria = {
        false_name: false_text,
        true_name: true_text,
    }

    def run() -> None:
        try:
            _post(spot, criteria, true_name, false_name, sent, cache_key, measured)
        finally:
            with _LOCK:
                _INFLIGHT.discard(cache_key)

    threading.Thread(target=run, name="selector-choice", daemon=True).start()
    return None


selector_side.last = {}
selector_side.last_side = None


def _post(
    spot: str,
    criteria: dict[str, str],
    true_name: str,
    false_name: str,
    instructions: str,
    cache_key: str,
    measured: bool,
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
            "User-Agent": "gtos-selector-choice/1",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
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
    probs = answer.get("probabilities") if isinstance(answer, dict) else None
    if not isinstance(probs, dict) or not probs:
        row["error"] = "probabilities_missing"
        row["key_fingerprint"] = key_fingerprint(key)
        _remember(spot, row)
        return row
    best = None
    best_p = -1.0
    tied = False
    numeric: dict[str, float] = {}
    for name in order:
        try:
            p = float(probs.get(name, 0.0) or 0.0)
        except (TypeError, ValueError):
            p = 0.0
        numeric[name] = p
        if best is None or p > best_p + 1e-12:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    alternative = None if tied or best is None else best
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
            "confidence": answer.get("confidence"),
            "model": body.get("model") or MODEL,
            "key_fingerprint": key_fingerprint(key),
            "key_source": source,
            "error": None if side else "tie",
            "order_send": False,
        }
    )
    if side is not None:
        _CACHE[cache_key] = row
    _remember(spot, row)
    return row


def _remember(spot: str, row: dict[str, Any]) -> None:
    selector_side.last = row
    try:
        path = (
            Path(__file__).resolve().parents[2]
            / "pipeline_state"
            / "ultimate_book"
            / NS
            / "judgment"
            / "selector_choices.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        return


def load_stamp(spots: list[dict[str, Any]], prove: dict[str, Any] | None) -> None:
    try:
        path = (
            Path(__file__).resolve().parents[2]
            / "pipeline_state"
            / "ultimate_book"
            / NS
            / "judgment"
            / "selector_choices_loaded.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema": "gtos.selector_choices.loaded.v0",
                    "model": MODEL,
                    "pid": os.getpid(),
                    "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "namespace": NS,
                    "login": 0,
                    "n_spots": len(spots),
                    "spots": [row.get("spot") for row in spots],
                    "questions": [
                        {"spot": row.get("spot"), "line": row.get("line"), "func": row.get("func"), "question": row.get("question")}
                        for row in spots
                    ],
                    "empty_restores_old_boolean": False,
                    "absent_branch": False,
                    "jev_absent": False,
                    "flatten": False,
                    "order_send": False,
                    "prove": prove,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        return


def prove_one() -> dict[str, Any]:
    """One side-free question. No order send."""

    prior = os.environ.get("GTOS_SELECTOR_CHOICE_FORCE")
    os.environ["GTOS_SELECTOR_CHOICE_FORCE"] = "1"
    try:
        side = selector_side(
            "selector_prove",
            True,
            "label_is_the_decision",
            "measurement_is_a_fact",
            "A selector measurement is on the table. Which side is the decision at this spot?",
            true_text="The label at this spot is the decision.",
            false_text="The measurement is a fact. It does not decide this spot.",
        )
    finally:
        if prior is None:
            os.environ.pop("GTOS_SELECTOR_CHOICE_FORCE", None)
        else:
            os.environ["GTOS_SELECTOR_CHOICE_FORCE"] = prior
    last = dict(selector_side.last or {})
    last["side"] = side
    last["order_send"] = False
    last["flatten"] = False
    return last


def load_selector_choices(spots: list[dict[str, Any]]) -> None:
    """Import-time load. Challenge writer only. One prove. No order send."""

    if not on_challenge():
        return
    prove = None
    try:
        prove = prove_one()
    except Exception:
        prove = {"error": "prove_failed", "order_send": False, "flatten": False}
    load_stamp(spots, prove)
