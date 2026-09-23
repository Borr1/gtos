"""Spot-exact Choices for sleeve conditions.

Each spot is one Choice. The alternatives are the two sides of that exact
condition: condition_true and condition_false. The unique highest probability
is the decision. Empty, tie, HTTP, missing key, and calls-off leave the spot
as None. None is not condition_true, does not restore the measured boolean,
and is never labeled with an absent-mode string.

One ask() is one POST for every spot on that candidate. Decisive answers are
cached by sleeve, symbol, bar, and measured fact. This module does not consume
the shared process call budget.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

MODEL = "jev-1.13.0"
NAMESPACE = "operator"
LOGIN = 0
DO_NOT_CLOSE_TICKET = 294215389
PERSIST = 0.0
UNIT_USD = 150
_TIMEOUT_S = 4.0
_TIE = 1e-12
_SIDES = ("condition_true", "condition_false")
_MAX_DISK = 2000

_LOCK = threading.Lock()
_CACHE: dict[str, dict[str, str | None]] = {}
_DISK_LOADED = False


def unique_highest(probabilities: Mapping[str, Any]) -> str | None:
    """Unique argmax over the two sides. A tie or an empty map is None."""
    best: str | None = None
    best_p = -1.0
    tied = False
    seen = False
    for name in _SIDES:
        if name not in probabilities:
            continue
        seen = True
        try:
            p = float(probabilities.get(name, 0.0) or 0.0)
        except (TypeError, ValueError):
            p = 0.0
        if best is None or p > best_p + _TIE:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= _TIE:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def all_false(sides: Mapping[str, str | None]) -> bool:
    """True only when every spot's unique highest is condition_false.

    None is not condition_false, so an unanswered spot does not pass and does
    not restore the measured boolean.
    """
    if not sides:
        return False
    return all(side == "condition_false" for side in sides.values())


def bar_id(decision_day, n, bar_time=None, bar_times=None) -> str:
    stamp = bar_time
    if stamp is None and bar_times:
        try:
            stamp = bar_times[-1]
        except Exception:
            stamp = None
    return f"{decision_day}|{n}|{stamp}"


def _repo_root() -> Path:
    # sleeves -> ultimate_book -> components -> src -> repo
    return Path(__file__).resolve().parents[4]


def _receipt_dir() -> Path:
    return (
        _repo_root()
        / "pipeline_state"
        / "ultimate_book"
        / NAMESPACE
        / "judgment"
    )


def _client():
    for name in ("src.judgment.jev_client", "judgment.jev_client"):
        try:
            return importlib.import_module(name)
        except ImportError:
            continue
    repo = str(_repo_root())
    if repo not in sys.path:
        sys.path.insert(0, repo)
    return importlib.import_module("src.judgment.jev_client")


def _clean(raw: str | None) -> str | None:
    if not raw:
        return None
    return str(raw).replace("jev_absent", "unanswered")


def _cache_token(sleeve: str, symbol: str, bar: str, spots: Mapping[str, Mapping[str, Any]]) -> str:
    payload = {
        "sleeve": sleeve,
        "symbol": symbol,
        "bar": bar,
        "spots": [
            [name, str(spots[name].get("condition", "")), bool(spots[name].get("measured"))]
            for name in spots
        ],
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_disk() -> None:
    global _DISK_LOADED
    if _DISK_LOADED:
        return
    _DISK_LOADED = True
    path = _receipt_dir() / "sleeve_spot_cache.json"
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(blob, dict):
        return
    for key, sides in blob.items():
        if isinstance(sides, dict) and sides and all(v in _SIDES for v in sides.values()):
            _CACHE[str(key)] = {str(k): str(v) for k, v in sides.items()}


def _store_disk(token: str, sides: dict[str, str | None]) -> None:
    if any(v not in _SIDES for v in sides.values()):
        return
    path = _receipt_dir() / "sleeve_spot_cache.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            blob = {}
        if not isinstance(blob, dict):
            blob = {}
        blob[token] = sides
        if len(blob) > _MAX_DISK:
            for old in list(blob)[: len(blob) - _MAX_DISK]:
                blob.pop(old, None)
        path.write_text(json.dumps(blob, sort_keys=True), encoding="utf-8")
    except Exception:
        return


def _append_receipt(row: dict[str, Any]) -> None:
    try:
        path = _receipt_dir() / "sleeve_spot_choices.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        return


def _questions(spots: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, spec in spots.items():
        condition = str(spec.get("condition", "")).strip()
        measured = bool(spec.get("measured"))
        out[name] = {
            "type": "choice",
            "instructions": (
                f"Condition: {condition}. "
                f"Measured fact for this condition is {measured}. "
                "The alternatives are the two sides of this exact condition. "
                "condition_true means the condition holds. "
                "condition_false means the condition does not hold."
            ),
            "criteria": {
                "condition_true": f"The condition holds. {condition}",
                "condition_false": f"The condition does not hold. {condition}",
            },
        }
    return out


def _post(state: dict[str, Any], spots: Mapping[str, Mapping[str, Any]]) -> dict[str, str | None]:
    client = _client()
    sides: dict[str, str | None] = {name: None for name in spots}
    if not client.calls_enabled():
        _append_receipt({
            "sleeve": state.get("sleeve"),
            "symbol": state.get("symbol"),
            "bar": state.get("bar"),
            "error": "calls_off",
            "sides": sides,
            "model": MODEL,
        })
        return sides
    key, source = client.resolve_key()
    if not key:
        _append_receipt({
            "sleeve": state.get("sleeve"),
            "symbol": state.get("symbol"),
            "bar": state.get("bar"),
            "error": "key_missing",
            "sides": sides,
            "model": MODEL,
        })
        return sides
    payload = {"state": state, "model": MODEL, "questions": _questions(spots)}
    req = urllib.request.Request(
        client.API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-sleeve-spot/1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        error = None
        answers = body.get("answers") if isinstance(body, dict) else None
        if not isinstance(answers, dict):
            answers = {}
            error = "probabilities_missing"
        probs_out: dict[str, Any] = {}
        for name in spots:
            answer = answers.get(name) if isinstance(answers.get(name), dict) else {}
            probs = answer.get("probabilities") if isinstance(answer, dict) else None
            if not isinstance(probs, dict) or not probs:
                sides[name] = None
                continue
            choice = unique_highest(probs)
            sides[name] = choice
            probs_out[name] = {str(k): float(v) for k, v in probs.items() if k in _SIDES}
        if any(v is None for v in sides.values()) and error is None:
            error = "unanswered"
        _append_receipt({
            "sleeve": state.get("sleeve"),
            "symbol": state.get("symbol"),
            "bar": state.get("bar"),
            "sides": sides,
            "probabilities": probs_out,
            "error": error,
            "model": (body.get("model") if isinstance(body, dict) else None) or MODEL,
            "key_fingerprint": client.key_fingerprint(key),
            "key_source": source,
        })
        return sides
    except urllib.error.HTTPError as exc:
        _append_receipt({
            "sleeve": state.get("sleeve"),
            "symbol": state.get("symbol"),
            "bar": state.get("bar"),
            "error": _clean(f"http_{exc.code}"),
            "sides": sides,
            "model": MODEL,
            "key_fingerprint": client.key_fingerprint(key),
            "key_source": source,
        })
        return sides
    except Exception as exc:  # noqa: BLE001 — a sleeve must not raise into the book
        _append_receipt({
            "sleeve": state.get("sleeve"),
            "symbol": state.get("symbol"),
            "bar": state.get("bar"),
            "error": _clean(type(exc).__name__),
            "sides": sides,
            "model": MODEL,
            "key_fingerprint": client.key_fingerprint(key),
            "key_source": source,
        })
        return sides


def ask(*, sleeve: str, symbol: str, bar_id: str, spots: Mapping[str, Mapping[str, Any]]) -> dict[str, str | None]:
    """One POST. Returns spot -> condition_true | condition_false | None."""
    if not spots:
        return {}
    token = _cache_token(sleeve, symbol, str(bar_id), spots)
    with _LOCK:
        _load_disk()
        cached = _CACHE.get(token)
    if cached is not None and set(cached) == set(spots):
        return dict(cached)
    state = {
        "sleeve": sleeve,
        "symbol": symbol,
        "namespace": NAMESPACE,
        "login": LOGIN,
        "bar": str(bar_id),
        "measured": {name: bool(spec.get("measured")) for name, spec in spots.items()},
        "flatten": False,
        "do_not_close_ticket": DO_NOT_CLOSE_TICKET,
        "persist": PERSIST,
        "unit_usd": UNIT_USD,
    }
    sides = _post(state, spots)
    if sides and all(v in _SIDES for v in sides.values()):
        with _LOCK:
            _CACHE[token] = dict(sides)
            _store_disk(token, dict(sides))
    return sides
