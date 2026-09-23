"""Learning Choice for one friend copy of a Challenge fill.

The decision is the unique highest probability. A tie is not a decision.
A bare label is not a decision. This module does not call order_send.
Close is legal only when ``close`` is that unique highest. Leaving the
copy open is not a flatten.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
PERSIST = "0.00"
SCHEMA = "gtos.judgment.friend_choice.v0"
QUESTION_ID = "manage_close"
OPTIONS = ("leave_orig", "move_sl", "move_tp", "close", "hold")
AUTHORIZES_CLOSE = "close"
FRIEND_BOOKS = {
    "sh": {"login": 0, "ns": "friend_a_f5_minimal"},
    "redacted_account": {"login": 0, "ns": "ftmo_redacted_account_f5_minimal"},
    "redacted_account": {"login": 1514684855, "ns": "ftmo_redacted_account_f5_minimal"},
}
CRITERIA = {
    "leave_orig": "Leave the original broker SL and TP. Do not send this manage.",
    "move_sl": "Move the stop to the proposed SL. This is the SL-modify send.",
    "move_tp": "Move the target to the proposed TP. This is the TP-modify send.",
    "close": "Close this friend copy. This is the close send for this ticket only.",
    "hold": "Hold. Do not send a modify or a close on this copy.",
}

REPO = Path(r"host-local\redacted_host\repo")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo() -> Path:
    if (REPO / "src" / "judgment").is_dir():
        return REPO
    return Path(__file__).resolve().parents[2]


def _read_key_file(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" not in line:
            return line
    return None


def _key_from_env_file(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    found: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip("'").strip('"')
        if name in {"TYPESAFE_API_KEY", "TYPESAFE_KEY"} and value:
            found[name] = value
    return found.get("TYPESAFE_API_KEY") or found.get("TYPESAFE_KEY")


def resolve_key() -> tuple[str | None, str | None]:
    """Return (key, source_label). Never include the key in receipts."""

    env_api = (os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if env_api:
        return env_api, "env:TYPESAFE_API_KEY"
    env_key = (os.environ.get("TYPESAFE_KEY") or "").strip()
    if env_key:
        return env_key, "env:TYPESAFE_KEY"
    override = (os.environ.get("TYPESAFE_KEY_FILE") or "").strip()
    if override:
        path = Path(override)
        got = _key_from_env_file(path) or _read_key_file(path)
        if got:
            return got, "file:TYPESAFE_KEY_FILE"
    home = Path.home() / ".config" / "typesafe" / "api_key"
    got = _read_key_file(home)
    if got:
        return got, "file:~/.config/typesafe/api_key"
    root = _repo()
    for path, label in (
        (Path("/run/secrets/TYPESAFE_API_KEY"), "file:/run/secrets/TYPESAFE_API_KEY"),
        (Path("/run/secrets/TYPESAFE_KEY"), "file:/run/secrets/TYPESAFE_KEY"),
        (root / "secrets" / "TYPESAFE_API_KEY.txt", "file:secrets/TYPESAFE_API_KEY.txt"),
        (root / "secrets" / "TYPESAFE_KEY.txt", "file:secrets/TYPESAFE_KEY.txt"),
    ):
        got = _read_key_file(path)
        if got:
            return got, label
    got = _key_from_env_file(root / ".env.typesafe")
    if got:
        return got, "file:.env.typesafe"
    return None, None


def _as_float(value: Any) -> float | None:
    try:
        if value is None or isinstance(value, bool):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def probabilities(answer: Any) -> tuple[dict[str, float], str]:
    """Numeric option map only. A bare label is not a decision."""

    names = set(OPTIONS)
    if not isinstance(answer, dict):
        return {}, "unreadable"
    for key in ("distribution", "probabilities", "probs"):
        raw = answer.get(key)
        if isinstance(raw, dict) and raw:
            out: dict[str, float] = {}
            for name, val in raw.items():
                if str(name) in names:
                    number = _as_float(val)
                    if number is not None:
                        out[str(name)] = number
            if out:
                return out, key
    options = answer.get("options") or answer.get("choices")
    if isinstance(options, list):
        out = {}
        for opt in options:
            if not isinstance(opt, dict):
                continue
            name = opt.get("value") if opt.get("value") is not None else opt.get("name")
            number = _as_float(opt.get("probability", opt.get("prob", opt.get("p"))))
            if name is not None and str(name) in names and number is not None:
                out[str(name)] = number
        if out:
            return out, "options"
    return {}, "unreadable"


def unique_highest(probs: Mapping[str, float]) -> str | None:
    """The single highest probability. A tie is not a decision."""

    if not probs:
        return None
    top = max(probs.values())
    winners = [name for name, prob in probs.items() if prob == top]
    if len(winners) != 1:
        return None
    return winners[0]


def close_authorized(choice: str | None, *, decision_emitted: bool) -> bool:
    return bool(decision_emitted) and choice == AUTHORIZES_CLOSE


def measure_copied_fills(deals: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Count friend copies on deal history. Does not send."""

    entries: list[dict[str, Any]] = []
    exits: list[dict[str, Any]] = []
    for deal in deals:
        comment = str(deal.get("comment") or "")
        entry = deal.get("entry")
        try:
            entry_i = int(entry)
        except (TypeError, ValueError):
            entry_i = -1
        if comment.startswith("fleet:") and entry_i == 0:
            entries.append(
                {
                    "deal": deal.get("deal"),
                    "position_id": deal.get("position_id"),
                    "comment": comment,
                    "symbol": deal.get("symbol"),
                    "volume": deal.get("volume"),
                    "price": deal.get("price"),
                }
            )
        elif entry_i == 1 and deal.get("position_id") is not None:
            exits.append(deal)
    entry_ids = {row["position_id"] for row in entries}
    copy_exits = [deal for deal in exits if deal.get("position_id") in entry_ids]
    open_ids = entry_ids - {deal.get("position_id") for deal in copy_exits}
    return {
        "copy_entries": len(entries),
        "copy_exits": len(copy_exits),
        "copy_open_on_history": len(open_ids),
        "source_294215389_entries": sum(
            1 for row in entries if str(row["comment"]) == "fleet:294215389"
        ),
    }


def _ask(state: Mapping[str, Any], instructions: str) -> dict[str, Any]:
    base: dict[str, Any] = {
        "asked": True,
        "ok": False,
        "question_id": QUESTION_ID,
        "model": MODEL,
        "choice": None,
        "probability": None,
        "probabilities": {},
        "probability_source": None,
        "decision_emitted": False,
        "order_send": False,
        "send": False,
        "http_status": None,
        "error": None,
        "key_source": None,
        "persist": PERSIST,
    }
    key, source = resolve_key()
    base["key_source"] = source
    if not key:
        base["error"] = "key_unreadable"
        return base
    payload = {
        "model": MODEL,
        "state": state,
        "questions": {
            QUESTION_ID: {
                "type": "choice",
                "instructions": instructions,
                "criteria": dict(CRITERIA),
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
            "User-Agent": "gtos-judgment/0.1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            status = getattr(resp, "status", 200)
    except urllib.error.HTTPError as exc:
        base["http_status"] = exc.code
        base["error"] = f"http_{exc.code}"
        return base
    except Exception as exc:  # noqa: BLE001 — Choice must not raise into a close
        base["error"] = type(exc).__name__
        return base
    base["http_status"] = status
    answers = body.get("answers") if isinstance(body, dict) else None
    answer = answers.get(QUESTION_ID) if isinstance(answers, dict) else None
    probs, source_name = probabilities(answer)
    winner = unique_highest(probs)
    base["probabilities"] = probs
    base["probability_source"] = source_name
    base["model"] = (body.get("model") if isinstance(body, dict) else None) or MODEL
    if winner is None:
        base["error"] = "no_unique_highest" if probs else "no_probabilities"
        return base
    base["ok"] = True
    base["choice"] = winner
    base["probability"] = probs[winner]
    base["decision_emitted"] = True
    base["send"] = close_authorized(winner, decision_emitted=True)
    base["error"] = None
    return base


def manage_open_copy(
    *,
    book: str,
    login: int,
    friend_ticket: int,
    source_ticket: int,
    symbol: str,
    volume: float,
    side: str,
    price_open: float | None,
    sl: float | None,
    tp: float | None,
    profit: float | None,
    comment: str,
    magic: int | None,
    printer_close: Mapping[str, Any] | None = None,
    record: bool = True,
) -> dict[str, Any]:
    """Ask the manage Choice for this open copy. ``send`` is close-only."""

    named = (
        f"{book} ticket {friend_ticket} {symbol} {side} lots {volume} "
        f"stop {sl} target {tp} comment {comment}"
    )
    instructions = (
        f"Friend copy manage for this exact ticket only: {named}. "
        f"Challenge source {source_ticket} is already closed. "
        "Pick one option. The close send happens only if close has the "
        "single highest probability. leave_orig and hold keep this copy open. "
        "Do not flatten a copy as a gesture. Do not close a different ticket."
    )
    state = {
        "book": book,
        "login": int(login),
        "namespace": FRIEND_BOOKS.get(book, {}).get("ns"),
        "friend_ticket": int(friend_ticket),
        "source_ticket": int(source_ticket),
        "symbol": symbol,
        "side": side,
        "volume": volume,
        "price_open": price_open,
        "sl": sl,
        "tp": tp,
        "profit": profit,
        "comment": comment,
        "magic": magic,
        "printer_close": dict(printer_close or {}),
        "persist": PERSIST,
        "gesture_flatten": False,
    }
    hop = _ask(state, instructions)
    row = {
        "schema": SCHEMA,
        "as_of_utc": _now(),
        "book": book,
        "login": int(login),
        "namespace": state["namespace"],
        "friend_ticket": int(friend_ticket),
        "source_ticket": int(source_ticket),
        "symbol": symbol,
        "side": side,
        "volume": volume,
        "price_open": price_open,
        "sl": sl,
        "tp": tp,
        "profit": profit,
        "comment": comment,
        "magic": magic,
        "question_id": QUESTION_ID,
        "model": hop.get("model"),
        "http_status": hop.get("http_status"),
        "choice": hop.get("choice"),
        "probability": hop.get("probability"),
        "probabilities": hop.get("probabilities") or {},
        "probability_source": hop.get("probability_source"),
        "decision_emitted": bool(hop.get("decision_emitted")),
        "send": bool(hop.get("send")),
        "order_send": False,
        "gesture_flatten": False,
        "persist": PERSIST,
        "key_source": hop.get("key_source"),
        "error": hop.get("error"),
    }
    if record:
        _append(row)
    return row


def record_path(book: str) -> Path:
    ns = FRIEND_BOOKS.get(book, {}).get("ns") or book
    return (
        _repo()
        / "pipeline_state"
        / "ultimate_book"
        / ns
        / "judgment"
        / "friend_choice.jsonl"
    )


def _append(row: Mapping[str, Any]) -> None:
    path = record_path(str(row.get("book") or ""))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=str) + "\n")
