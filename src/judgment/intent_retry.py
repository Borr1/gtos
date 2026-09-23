"""Retry sitting status-intent rows into the place loop.

PASS and a missing consume row are appended to this cycle's intents so the
existing asks can reach order_router.place. A HOLD row asks judgment_hold
with the sidecar on the state. An empty answer, a tie, or an error does not
become a send and does not restore a withhold. This module does not send.
"""

from __future__ import annotations

import inspect
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0

_HOLD_CRITERIA = {
    "send_continues": "The send continues. The flow row is not a ban.",
    "hold_stands": "That flow row stands. Do not send this bar.",
}
_HOLD_INSTRUCTIONS = (
    "A flow row on this sleeve and symbol says HOLD. "
    "The sidecar verdict, why_code, and written time are on this state. "
    "Does the send continue, or does that row stand? "
    "Do not close any open ticket. "
    "An empty answer or a tie is not a decision."
)
_DAY_CRITERIA = {
    "reenter": "The row joins this cycle. The place asks still run. This is not a send.",
    "stays_out": "The row stays out of this cycle. Do not send.",
}
_DAY_INSTRUCTIONS = (
    "The slate row day and the cycle day are both on this state. "
    "A different day is a fact. It is not a ban. "
    "reenter joins the cycle. stays_out leaves the row out. "
    "An empty answer or a tie does not send and does not restore a day ban. "
    "Do not close an open ticket."
)
_ACTION_CRITERIA = {
    "reenter": "This consume action joins the cycle. The place asks still run. This is not a send.",
    "stays_out": "This consume action stays out of the cycle. Do not send.",
}
_ACTION_INSTRUCTIONS = (
    "The consume action on this state is not a pass, a missing row, or a hold. "
    "reenter joins the cycle. stays_out leaves the row out. "
    "An empty answer or a tie does not send and does not restore a drop. "
    "Do not close an open ticket."
)


def _now(value: datetime | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _load(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _positive(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number <= 0:
        return None
    return number


def _slate_rows(repo: Path, namespace: str) -> list[dict[str, Any]]:
    pointer = (
        repo
        / "pipeline_state"
        / "ultimate_book"
        / namespace
        / "judgment"
        / "state"
        / "latest_slate.json"
    )
    meta = _load(pointer)
    if not meta:
        return []
    path = Path(str(meta.get("path") or ""))
    slate = _load(path)
    if not slate:
        return []
    rows = []
    for item in slate.get("candidates") or []:
        if isinstance(item, dict) and str(item.get("status") or "") == "intent":
            rows.append(item)
    return rows


def _consume_doc(repo: Path, day: str) -> dict[str, Any]:
    path = repo / "judgment" / f"consume_{day}.json"
    return _load(path) or {}


def _action_of(entry: dict[str, Any]) -> str:
    action = str(entry.get("action") or "").strip().upper()
    verdict = str(entry.get("verdict") or "").strip().lower()
    if action in {"PASS", "HOLD", "APPROVE", "SIZE"}:
        return action
    if verdict in {"hold", "veto"}:
        return "HOLD"
    if verdict in {"pass", "abstain", "absent", "approve"}:
        return "PASS" if verdict != "approve" else "APPROVE"
    return "NONE"


def _join(doc: dict[str, Any], row: dict[str, Any]) -> tuple[str, str | None, dict[str, Any] | None]:
    symbol = str(row.get("symbol") or "")
    sleeve = str(row.get("sleeve") or "")
    day = str(row.get("decision_day") or "")[:10]
    keys = []
    if symbol and sleeve and day:
        keys.append(f"LAUNCHER::{symbol}::{sleeve}::{day}")
    candidate = str(row.get("candidate_id") or "")
    if candidate:
        keys.append(candidate)
    hits: list[tuple[str, dict[str, Any]]] = []
    for key in keys:
        entry = doc.get(key)
        if isinstance(entry, dict):
            hits.append((key, entry))
    if not hits:
        return "NONE", None, None

    def _stamp(item: tuple[str, dict[str, Any]]) -> str:
        entry = item[1]
        return str(entry.get("written_at_utc") or entry.get("ts") or "")

    key, entry = max(hits, key=_stamp)
    return _action_of(entry), key, entry


def judgment_hold_state(intent: Any, decision: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Facts for one judgment_hold ask. The sidecar fields stay on the state."""

    flow = decision if isinstance(decision, dict) else {}
    geometry = None
    reader = getattr(intent, "geometry", None)
    if callable(reader):
        try:
            geometry = reader()
        except Exception:
            geometry = None
    if geometry is None and isinstance(extra, dict):
        geometry = extra.get("geometry")
    state = {
        "symbol": str(getattr(intent, "symbol", "") or (extra or {}).get("symbol") or ""),
        "sleeve": str(getattr(intent, "sleeve", "") or (extra or {}).get("sleeve") or ""),
        "direction": getattr(intent, "direction", None) if intent is not None else (extra or {}).get("direction"),
        "decision_day": str(getattr(intent, "decision_day", "") or (extra or {}).get("decision_day") or "")[:10],
        "candidate_id": flow.get("join_key") or (extra or {}).get("candidate_id"),
        "stop_dist": getattr(intent, "stop_dist", None) if intent is not None else (extra or {}).get("stop_dist"),
        "entry_price": getattr(intent, "entry_price", None) if intent is not None else (extra or {}).get("entry_price"),
        "geometry": geometry,
        "flow_action": str(flow.get("action") or (extra or {}).get("flow_action") or "HOLD"),
        "flow_reason": str(flow.get("reason") or flow.get("why_code") or (extra or {}).get("why_code") or ""),
        "why_code": flow.get("why_code") if flow.get("why_code") is not None else (extra or {}).get("why_code"),
        "verdict": flow.get("verdict") if flow.get("verdict") is not None else (extra or {}).get("verdict"),
        "written_at_utc": flow.get("written_at_utc") or (extra or {}).get("written_at_utc"),
        "namespace": CHALLENGE_NS,
        "login": CHALLENGE_LOGIN,
        "join_key": flow.get("join_key") or (extra or {}).get("consume_key"),
    }
    if extra:
        for key in ("cluster", "consume_key"):
            if extra.get(key) is not None:
                state[key] = extra.get(key)
    return state


def _hold_unanswered(error: Any = None) -> dict[str, Any]:
    """Empty, tie, and error. Not a send, and not the old hold."""

    return {
        "alternative": None,
        "unanswered": True,
        "blocks": False,
        "error": error,
        "send": False,
    }


def _ask_choice(
    spot: str,
    state: dict[str, Any],
    criteria: dict[str, str],
    withhold: str,
    cache_key: str,
    instructions: str,
) -> dict[str, Any]:
    """One choice. The withhold side blocks. Any other returned side is the release.

    Empty, tie, and error stay unanswered. They do not send and they do not
    restore the withhold. This function does not send.
    """

    try:
        from src.judgment.no_fear import fear_withholds
    except Exception as exc:
        return _hold_unanswered(type(exc).__name__)
    try:
        asked = fear_withholds(spot, state, criteria, withhold, cache_key, instructions)
    except Exception as exc:
        return _hold_unanswered(type(exc).__name__)
    if not isinstance(asked, dict):
        return _hold_unanswered("ask_missing")
    alternative = asked.get("alternative")
    if (
        asked.get("unanswered")
        or asked.get("error")
        or asked.get("tie") is True
        or alternative not in set(criteria)
    ):
        return _hold_unanswered(asked.get("error"))
    if alternative == withhold:
        return {
            "alternative": alternative,
            "unanswered": False,
            "blocks": True,
            "error": None,
            "send": False,
        }
    return {
        "alternative": alternative,
        "unanswered": False,
        "blocks": False,
        "error": None,
        "send": False,
    }


def _is_release(asked: dict[str, Any] | None, release: str) -> bool:
    if not isinstance(asked, dict):
        return False
    return (
        asked.get("alternative") == release
        and not asked.get("unanswered")
        and not asked.get("error")
    )


def _together(jobs: list[tuple[Any, Callable[[], dict[str, Any]]]]) -> dict[Any, dict[str, Any]]:
    """Independent asks. One job stays on this thread."""

    if not jobs:
        return {}
    if len(jobs) == 1:
        key, fn = jobs[0]
        try:
            return {key: fn()}
        except Exception as exc:
            return {key: _hold_unanswered(type(exc).__name__)}
    out: dict[Any, dict[str, Any]] = {}

    def _run(key: Any, fn: Callable[[], dict[str, Any]]) -> None:
        try:
            out[key] = fn()
        except Exception as exc:
            out[key] = _hold_unanswered(type(exc).__name__)

    threads = [threading.Thread(target=_run, args=(key, fn)) for key, fn in jobs]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return out


def ask_judgment_hold(state: dict[str, Any]) -> dict[str, Any]:
    """Ask judgment_hold. The return is what the owner loop attaches.

    ``send_continues`` is the only release into the next hop. ``hold_stands``
    withholds. Empty, tie, and error stay unanswered: they do not send and
    they do not restore a withhold. This function does not send.
    """

    why = str(state.get("why_code") or state.get("flow_reason") or "")
    written = str(state.get("written_at_utc") or "")
    cache_key = (
        f"judgment_hold|{state.get('sleeve')}|{state.get('symbol')}|{why}|{written}"
    )
    return _ask_choice(
        "judgment_hold",
        state,
        _HOLD_CRITERIA,
        "hold_stands",
        cache_key,
        _HOLD_INSTRUCTIONS,
    )


def _ask_day(state: dict[str, Any]) -> dict[str, Any]:
    cache_key = (
        f"day_reenter|{state.get('sleeve')}|{state.get('symbol')}|"
        f"{state.get('row_day')}|{state.get('cycle_day')}|{state.get('candidate_id')}"
    )
    return _ask_choice(
        "day_reenter",
        state,
        _DAY_CRITERIA,
        "stays_out",
        cache_key,
        _DAY_INSTRUCTIONS,
    )


def _ask_action(state: dict[str, Any]) -> dict[str, Any]:
    cache_key = (
        f"consume_reenter|{state.get('sleeve')}|{state.get('symbol')}|"
        f"{state.get('consume')}|{state.get('cycle_day')}|{state.get('candidate_id')}"
    )
    return _ask_choice(
        "consume_reenter",
        state,
        _ACTION_CRITERIA,
        "stays_out",
        cache_key,
        _ACTION_INSTRUCTIONS,
    )


def _risk_pct(units: list[dict[str, Any]], balance: float | None, owner: Any, symbol: str, sleeve: str) -> float | None:
    for unit in units:
        if not isinstance(unit, dict) or not unit.get("sized"):
            continue
        pct = _positive(unit.get("risk_pct_per_trade"))
        if pct is not None:
            return pct
    scaler = getattr(owner, "_f5_scaler", None)
    if scaler is None or not balance:
        return None
    usd = None
    unit_for = getattr(scaler, "risk_usd_for", None)
    if callable(unit_for):
        try:
            usd = float(unit_for(symbol, sleeve))
        except Exception:
            usd = None
    if usd is None:
        try:
            usd = float(getattr(scaler, "target_risk_usd"))
        except (TypeError, ValueError):
            usd = None
    if usd is None or usd <= 0:
        return None
    try:
        bal = float(balance)
    except (TypeError, ValueError):
        return None
    if bal <= 0:
        return None
    return usd / bal * 100.0


def _build_intent(row: dict[str, Any]) -> tuple[Any | None, str | None]:
    from src.components.ultimate_book.admission import TradeIntent

    direction_name = str(row.get("direction") or "").upper()
    if direction_name == "LONG":
        direction = 1
    elif direction_name == "SHORT":
        direction = -1
    else:
        return None, "direction_missing"
    geom = row.get("geometry") if isinstance(row.get("geometry"), dict) else {}
    entry = _positive(geom.get("entry"))
    stop = _positive(geom.get("stop"))
    target = _positive(geom.get("target"))
    stop_dist = _positive(row.get("stop_dist"))
    if stop_dist is None and entry is not None and stop is not None:
        stop_dist = abs(entry - stop)
    if stop_dist is None:
        return None, "stop_dist_missing"
    target_dist = None
    if entry is not None and target is not None:
        target_dist = abs(target - entry)
    wanted = {
        "sleeve": str(row.get("sleeve") or ""),
        "symbol": str(row.get("symbol") or ""),
        "direction": direction,
        "decision_day": str(row.get("decision_day") or "")[:10],
        "stop_dist": float(stop_dist),
        "target_dist": target_dist,
        "entry_price": entry,
    }
    params = inspect.signature(TradeIntent).parameters
    kwargs = {key: value for key, value in wanted.items() if key in params}
    missing = [
        name
        for name, param in params.items()
        if name != "self"
        and param.default is inspect.Signature.empty
        and name not in kwargs
    ]
    if missing:
        return None, "intent_fields_missing:" + ",".join(missing)
    try:
        return TradeIntent(**kwargs), None
    except Exception as exc:
        return None, type(exc).__name__


def _present(intents: list[Any]) -> set[tuple[str, str, str]]:
    found = set()
    for intent in intents:
        found.add(
            (
                str(getattr(intent, "sleeve", "") or ""),
                str(getattr(intent, "symbol", "") or ""),
                str(getattr(intent, "decision_day", "") or "")[:10],
            )
        )
    return found


def _sleeve_covered(units: list[dict[str, Any]], sleeve: str) -> bool:
    for unit in units:
        if not isinstance(unit, dict):
            continue
        members = unit.get("sleeve_members") or []
        if sleeve in members:
            return True
    return False


def _write_stamp(repo: Path, row: dict[str, Any]) -> None:
    path = repo / "judgment" / "intent_retry_stamp.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(row, indent=2, default=str) + "\n", encoding="utf-8")
    except OSError:
        return


def attach_sitting_intents(
    owner: Any,
    intents: list[Any],
    units: list[dict[str, Any]],
    now: datetime | None = None,
    *,
    balance: float | None = None,
) -> dict[str, Any]:
    """Append PASS and unanswered-hold-released rows. Never raises. Never sends."""

    moment = _now(now)
    day = moment.date().isoformat()
    repo = Path(str(getattr(owner, "_repo_root", "") or ""))
    report: dict[str, Any] = {
        "schema": "gtos.judgment.intent_retry.v1",
        "at_utc": moment.isoformat(),
        "day": day,
        "namespace": str(getattr(owner, "_namespace", "") or ""),
        "asked": [],
        "retried": [],
        "held": [],
        "unanswered": [],
        "left": [],
        "agent_order_send": False,
    }
    if report["namespace"] != CHALLENGE_NS or not repo.is_dir():
        report["error"] = "not_challenge"
        return report
    try:
        rows = _slate_rows(repo, CHALLENGE_NS)
        consume = _consume_doc(repo, day)
    except Exception as exc:
        report["error"] = type(exc).__name__
        _write_stamp(repo, report)
        return report
    present = _present(intents)
    cards: list[dict[str, Any]] = []
    for row in rows:
        symbol = str(row.get("symbol") or "")
        sleeve = str(row.get("sleeve") or "")
        row_day = str(row.get("decision_day") or "")[:10]
        action, key, entry = _join(consume, row)
        limit_level = (
            _positive((row.get("geometry") or {}).get("entry"))
            if isinstance(row.get("geometry"), dict)
            else None
        )
        hold_state = None
        if action == "HOLD":
            hold_state = judgment_hold_state(
                None,
                {
                    "action": "HOLD",
                    "reason": (entry or {}).get("reason"),
                    "why_code": (entry or {}).get("why_code"),
                    "verdict": (entry or {}).get("verdict") or "hold",
                    "written_at_utc": (entry or {}).get("written_at_utc") or (entry or {}).get("ts"),
                    "join_key": key,
                },
                {
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "direction": row.get("direction"),
                    "decision_day": row_day,
                    "candidate_id": row.get("candidate_id"),
                    "stop_dist": row.get("stop_dist"),
                    "entry_price": limit_level,
                    "geometry": row.get("geometry"),
                    "why_code": (entry or {}).get("why_code"),
                    "verdict": (entry or {}).get("verdict"),
                    "written_at_utc": (entry or {}).get("written_at_utc") or (entry or {}).get("ts"),
                    "consume_key": key,
                    "cluster": row.get("cluster"),
                    "flow_action": "HOLD",
                },
            )
        cards.append(
            {
                "row": row,
                "symbol": symbol,
                "sleeve": sleeve,
                "row_day": row_day,
                "action": action,
                "key": key,
                "limit_level": limit_level,
                "other_day": bool(row_day and row_day != day),
                "duplicate": (sleeve, symbol, row_day) in present,
                "hold_state": hold_state,
                "day_state": {
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "row_day": row_day,
                    "cycle_day": day,
                    "consume": action,
                    "candidate_id": row.get("candidate_id"),
                    "namespace": CHALLENGE_NS,
                    "login": CHALLENGE_LOGIN,
                },
                "action_state": {
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "consume": action,
                    "cycle_day": day,
                    "candidate_id": row.get("candidate_id"),
                    "namespace": CHALLENGE_NS,
                    "login": CHALLENGE_LOGIN,
                },
            }
        )
    jobs: list[tuple[Any, Callable[[], dict[str, Any]]]] = []
    for index, card in enumerate(cards):
        if card["duplicate"]:
            continue
        if card["other_day"]:
            jobs.append((("day", index), lambda c=card: _ask_day(c["day_state"])))
        elif card["action"] == "HOLD":
            jobs.append((("hold", index), lambda c=card: ask_judgment_hold(c["hold_state"])))
        elif card["action"] not in {"PASS", "NONE", "APPROVE", "SIZE"}:
            jobs.append((("action", index), lambda c=card: _ask_action(c["action_state"])))
    answers = _together(jobs)
    wave_two: list[tuple[Any, Callable[[], dict[str, Any]]]] = []
    for index, card in enumerate(cards):
        if card["duplicate"] or not card["other_day"]:
            continue
        if not _is_release(answers.get(("day", index)), "reenter"):
            continue
        if card["action"] == "HOLD":
            wave_two.append((("hold", index), lambda c=card: ask_judgment_hold(c["hold_state"])))
        elif card["action"] not in {"PASS", "NONE", "APPROVE", "SIZE"}:
            wave_two.append((("action", index), lambda c=card: _ask_action(c["action_state"])))
    answers.update(_together(wave_two))
    for index, card in enumerate(cards):
        row = card["row"]
        symbol = card["symbol"]
        sleeve = card["sleeve"]
        row_day = card["row_day"]
        action = card["action"]
        key = card["key"]
        brief = {
            "symbol": symbol,
            "sleeve": sleeve,
            "consume": action,
            "consume_key": key,
            "candidate_id": row.get("candidate_id"),
            "limit_level": card["limit_level"],
            "send": False,
        }
        identity = (sleeve, symbol, row_day)
        if identity in present:
            brief["why"] = "already_in_cycle"
            report["left"].append(brief)
            continue
        if card["other_day"]:
            day_asked = answers.get(("day", index)) or _hold_unanswered("ask_missing")
            report["asked"].append(
                {
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "spot": "day_reenter",
                    "alternative": day_asked.get("alternative"),
                    "unanswered": day_asked.get("unanswered"),
                    "error": day_asked.get("error"),
                    "send": False,
                }
            )
            if day_asked.get("blocks") is True and day_asked.get("alternative") == "stays_out":
                brief["why"] = "stays_out"
                brief["alternative"] = "stays_out"
                report["left"].append(brief)
                continue
            if not _is_release(day_asked, "reenter"):
                brief["why"] = "day_unanswered"
                brief["alternative"] = None
                brief["unanswered"] = True
                brief["error"] = day_asked.get("error")
                report["unanswered"].append(brief)
                continue
        if action == "HOLD":
            asked = answers.get(("hold", index)) or _hold_unanswered("ask_missing")
            brief["alternative"] = asked.get("alternative")
            brief["unanswered"] = asked.get("unanswered")
            brief["error"] = asked.get("error")
            report["asked"].append(
                {
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "spot": "judgment_hold",
                    "alternative": asked.get("alternative"),
                    "unanswered": asked.get("unanswered"),
                    "error": asked.get("error"),
                    "send": False,
                }
            )
            if asked.get("blocks") is True and asked.get("alternative") == "hold_stands":
                brief["why"] = "hold_stands"
                report["held"].append(brief)
                continue
            if not _is_release(asked, "send_continues"):
                brief["why"] = "hold_unanswered"
                brief["alternative"] = None
                brief["unanswered"] = True
                report["unanswered"].append(brief)
                continue
        elif action not in {"PASS", "NONE", "APPROVE", "SIZE"}:
            asked = answers.get(("action", index)) or _hold_unanswered("ask_missing")
            report["asked"].append(
                {
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "spot": "consume_reenter",
                    "consume": action,
                    "alternative": asked.get("alternative"),
                    "unanswered": asked.get("unanswered"),
                    "error": asked.get("error"),
                    "send": False,
                }
            )
            if asked.get("blocks") is True and asked.get("alternative") == "stays_out":
                brief["why"] = "stays_out"
                brief["alternative"] = "stays_out"
                report["left"].append(brief)
                continue
            if not _is_release(asked, "reenter"):
                brief["why"] = "action_unanswered"
                brief["alternative"] = None
                brief["unanswered"] = True
                brief["error"] = asked.get("error")
                report["unanswered"].append(brief)
                continue
        try:
            intent, why = _build_intent(row)
        except Exception as exc:
            brief["why"] = type(exc).__name__
            report["left"].append(brief)
            continue
        if intent is None:
            brief["why"] = why
            report["left"].append(brief)
            continue
        intents.append(intent)
        present.add(identity)
        if not _sleeve_covered(units, sleeve):
            pct = _risk_pct(units, balance, owner, symbol, sleeve)
            units.append(
                {
                    "sleeve_members": [sleeve],
                    "sized": pct is not None,
                    "risk_pct_per_trade": pct,
                    "cluster": row.get("cluster"),
                    "reason": "consume_retry",
                }
            )
        brief["why"] = "retried"
        brief["send"] = False
        report["retried"].append(brief)
    try:
        import os

        report["pid"] = os.getpid()
    except Exception:
        report["pid"] = None
    _write_stamp(repo, report)
    return report
