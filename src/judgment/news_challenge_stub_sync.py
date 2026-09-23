"""Sync the Challenge stub FROM the 20260920 WATCH HIGH spine.

Does not invent events. Does not overwrite June ``data/news_calendar.json``.
Host stub ``news_calendar.json`` on VPS was last synced 20260918T221900Z and
still carries summer ECB Oct29 12:15Z/12:45Z. Live spine
``f5_high_calendar`` updated 20260920T222007Z corrected those clocks to
winter CET 13:15Z/13:45Z. This module writes a lab snapshot only.

Every decision, including each parameter, is the System One return for this
state. One call: ``jev_client.evaluate`` with model ``jev-1.13.0``,
``merge_sleeve=False``, POST https://api.typesafe.ai/v1/systemone.
Questions are only Noul, Choice, or Score. Prior outcomes are attached on
that ask, and the return is stored for the next ask.

The spine Choice, the write Noul, the news-protocol Noul, the
challenge-stub-sync Noul, and the apply-persist Score are that return.
An empty answer, a tie, or an error leaves that field unset and does not
restore a constant. A floor and a baseline are not a question. This module
does not send. Judge code stays unable to send.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .news_calendar_sync import JuneWeekOfRecordError, refuse_june_overwrite, sync_from_spine

MODEL = "jev-1.13.0"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPINE = REPO_ROOT / "data" / "news" / "f5_high_calendar_host_20260920.json"
DEFAULT_OUT = REPO_ROOT / "data" / "news" / "news_calendar_f5_synced_from_spine_20260920.json"
FALLBACK_SPINE = REPO_ROOT / "data" / "news" / "f5_high_calendar_host_20260916.json"

_SPINE_ORDER = ("spine_20260920", "spine_20260916", "caller_spine")
_SPINE_PATHS = {
    "spine_20260920": DEFAULT_SPINE,
    "spine_20260916": FALLBACK_SPINE,
}
_SPINE_CRITERIA = {
    "spine_20260920": "Sync from the 20260920 WATCH HIGH spine named on this state.",
    "spine_20260916": "Sync from the 20260916 host spine named on this state.",
    "caller_spine": "Sync from the caller spine path named on this state.",
}
_NOUL_ORDER = ("true", "false")
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LIMIT_KEYS = frozenset(
    {
        "floor",
        "baseline",
        "day_start_baseline",
        "static_floor",
        "pass_line",
        "flatten_floor_usd",
        "daily_loss_pct",
        "floor_room",
    }
)
_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "90K",
    "110000",
    "110,000",
    "110_000",
    "110k",
    "110K",
)
_LOCAL_OUTCOMES: list[dict[str, Any]] = []
_SPEC: tuple[tuple[str, str, str, tuple[str, ...] | None], ...] = (
    ("stub_spine", "choice", "stub_spine", _SPINE_ORDER),
    ("stub_write", "noul", "stub_write", _NOUL_ORDER),
    ("news_protocol_applied", "noul", "news_protocol_applied", _NOUL_ORDER),
    ("challenge_stub_sync", "noul", "challenge_stub_sync", _NOUL_ORDER),
    ("apply_persist", "score", "apply_persist", None),
)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    lowered = cleaned.lower()
    kept: list[str] = []
    index = 0
    while index < len(cleaned):
        if lowered.startswith("baseline", index):
            index += len("baseline")
            continue
        if lowered.startswith("floor", index):
            index += len("floor")
            continue
        kept.append(cleaned[index])
        index += 1
    return "".join(kept)


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before the ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _unique(probs: Mapping[str, Any] | None, order: tuple[str, ...] | None) -> str | None:
    """Unique highest probability. A missing probability is not zero. A tie is unset."""

    if not isinstance(probs, Mapping) or not probs:
        return None
    names = tuple(order) if order else tuple(str(name) for name in probs)
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in names:
        if name not in probs:
            continue
        raw = probs.get(name)
        if raw is None or isinstance(raw, bool):
            continue
        number = _finite(raw)
        if number is None:
            continue
        seen = True
        if best_p is None or number > best_p:
            best = str(name)
            best_p = number
            tied = False
        elif number == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, Mapping):
        return None
    picked: str | None = None
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probs, order)
        if agreed in order:
            picked = str(agreed)
    except Exception:
        picked = None
    if picked not in order:
        picked = _unique(probs, order)
    if picked not in order:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _choice(block, _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The score that came back. A missing score is not a constant and not a probability."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "score" not in block or block.get("score") is None:
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        return _finite(block.get("score"))


def _pull(block: Any, kind: str, order: tuple[str, ...] | None) -> Any:
    if kind == "noul":
        return _noul(block)
    if kind == "choice":
        return _choice(block, order or ())
    return _score(block)


def _why(block: Any, value: Any, order: tuple[str, ...] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probs = block.get("probabilities") if isinstance(block, Mapping) else None
    menu = order or (tuple(str(name) for name in probs) if isinstance(probs, Mapping) else ())
    if isinstance(probs, Mapping) and probs and _unique(probs, menu or None) is None:
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _choice_question(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    cleaned = {str(key): _scrub_text(str(value)) for key, value in criteria.items()}
    body: dict[str, Any] = {"type": "choice", "instructions": instructions, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, cleaned)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "choice"
            shaped["instructions"] = instructions
            shaped["criteria"] = cleaned
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, text: str) -> dict[str, Any]:
    """A Score for this card. An amount waits for the card. An order keeps its words."""

    words = _ordinal_words(str(qid))
    row = _pending_score(qid, text, words)
    if not isinstance(row, dict):
        return {}
    return {str(qid): row}



def _noul_question(qid: str, text: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(text),
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _questions() -> dict[str, Any]:
    """One pack. Types are noul, choice, or score."""

    unset = "An empty answer leaves it unset. This ask does not transmit an order."
    pack: dict[str, Any] = {}
    pack.update(
        _choice_question(
            "stub_spine",
            "Which named spine does this challenge stub sync from? "
            "The option you return is the unique highest probability. "
            "A tie or an empty answer leaves the spine unset. "
            "File presence on this state is a fact. "
            "This ask does not transmit an order.",
            _SPINE_CRITERIA,
        )
    )
    pack.update(
        _noul_question(
            "stub_write",
            "Does this state write the lab snapshot? "
            "The noul you return is that answer. " + unset,
            "Write the lab snapshot for this state.",
            "Leave the lab snapshot unwritten for this state.",
        )
    )
    pack.update(
        _noul_question(
            "news_protocol_applied",
            "Is the news protocol applied on this challenge stub sync? "
            "The noul you return is that answer. " + unset,
            "The news protocol is applied on this sync.",
            "The news protocol is not applied on this sync.",
        )
    )
    pack.update(
        _noul_question(
            "challenge_stub_sync",
            "Is this state the challenge stub sync? "
            "The noul you return is that answer. " + unset,
            "This state is the challenge stub sync.",
            "This state is not the challenge stub sync.",
        )
    )
    pack.update(
        _score_question(
            "apply_persist",
            "The score you return is the apply-persist parameter for this state. "
            "It may sit between the levels. "
            "An empty score leaves it unset. "
            "This ask does not transmit an order.",
        )
    )
    return pack


def _ecb_clocks(events: Any) -> list[str] | None:
    if not isinstance(events, list):
        return None
    clocks: list[str] = []
    for row in events:
        if not isinstance(row, dict):
            continue
        scheduled = str(row.get("scheduled_utc") or "")
        name = str(row.get("event") or row.get("name") or "")
        if "ECB" in name and scheduled.startswith("2026-10-29"):
            clocks.append(scheduled)
    return clocks


def _spine_fact(path: Path) -> dict[str, Any]:
    """Path, presence, and clocks are facts. They are not the spine choice."""

    fact: dict[str, Any] = {
        "path": _rel(path),
        "present": path.is_file(),
        "updated_utc": None,
        "n_events": None,
        "ecb_oct29": None,
    }
    if not path.is_file():
        return fact
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        fact["present"] = False
        return fact
    if not isinstance(payload, dict):
        return fact
    updated = payload.get("updated_utc")
    fact["updated_utc"] = updated if isinstance(updated, str) else None
    rows = payload.get("events")
    if isinstance(rows, list):
        kept = [row for row in rows if isinstance(row, dict)]
        fact["n_events"] = len(kept)
        fact["ecb_oct29"] = _ecb_clocks(kept)
    return fact


def _state(
    *,
    caller_spine: Path | None,
    caller_stub: Path | None,
    dest: Path,
    proposed_write: bool | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": MODEL,
        "namespace": CHALLENGE_NS,
        "login": CHALLENGE_LOGIN,
        "magic": CHALLENGE_MAGIC,
        "caller_spine": None if caller_spine is None else _rel(caller_spine),
        "caller_stub": None if caller_stub is None else _rel(caller_stub),
        "caller_out": _rel(dest),
        "proposed_write": proposed_write,
        "spine_20260920": _spine_fact(DEFAULT_SPINE),
        "spine_20260916": _spine_fact(FALLBACK_SPINE),
        "lab_out": _rel(DEFAULT_OUT),
        "identity": {
            "ns": CHALLENGE_NS,
            "login": CHALLENGE_LOGIN,
            "magic": CHALLENGE_MAGIC,
        },
    }
    scrubbed = _scrub(body)
    return scrubbed if isinstance(scrubbed, dict) else body


def _attach_priors(payload: dict[str, Any], questions: Mapping[str, Any]) -> None:
    payload.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
    except Exception:
        loaded = [dict(item) for item in _LOCAL_OUTCOMES]
    if loaded is None:
        loaded = []
    payload["prior_outcomes"] = loaded


def _remember(state: Mapping[str, Any], rows: Sequence[tuple[str, Any, str | None]]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in rows:
            _LOCAL_OUTCOMES.append({"spot": key, "value": value, "error": error})
        return
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            _LOCAL_OUTCOMES.append({"spot": key, "value": value, "error": error})


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = dict(state)
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    payload["endpoint"] = ENDPOINT
    _attach_priors(payload, questions)
    try:
        from .jev_client import API_URL, evaluate

        payload["endpoint"] = str(API_URL)
        questions = _anchor_questions(questions, payload)
        receipt = evaluate(
            payload,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {"error": type(exc).__name__, "answers": {}, "state": payload, "model": MODEL}
    if not isinstance(receipt, dict):
        return {"error": "evaluate_not_a_dict", "answers": {}, "state": payload, "model": MODEL}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "error": error,
        "answers": answers,
        "state": payload,
        "model": receipt.get("model") or MODEL,
    }


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, Mapping):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, float] = {}
    for name in _SPINE_ORDER:
        number = _finite(raw.get(name))
        if number is not None:
            out[name] = number
    return out


def _decisions(asked: Mapping[str, Any]) -> dict[str, Any]:
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    out: dict[str, Any] = {"stub_spine_probabilities": _probabilities(answers.get("stub_spine"))}
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in _SPEC:
        block = answers.get(qid)
        value = _pull(block, kind, order)
        out[field] = value
        rows.append((qid, value, _why(block, value, order, error)))
    posted = asked.get("state") if isinstance(asked.get("state"), Mapping) else {}
    _remember(posted, rows)
    out["stub_sync_error"] = error if not answers else None
    return out


def _spine_path(choice: str | None, caller_spine: Path | None) -> Path | None:
    """The returned spine. An unset choice does not pick a file that exists."""

    if choice == "caller_spine":
        return caller_spine
    named = _SPINE_PATHS.get(str(choice or ""))
    if named is None:
        return None
    return named


def _blank(error: str | None = None) -> dict[str, Any]:
    return {
        "invented": False,
        "june_week_of_record_untouched": True,
        "events": None,
        "stub_spine": None,
        "stub_spine_probabilities": {},
        "stub_write": None,
        "NEWS_PROTOCOL_APPLIED": None,
        "challenge_stub_sync": None,
        "apply_persist": None,
        "ecb_oct29_clocks": None,
        "stub_sync_error": error,
        "model": MODEL,
    }


def _overlay(snap: dict[str, Any], decisions: Mapping[str, Any]) -> dict[str, Any]:
    snap["stub_spine"] = decisions.get("stub_spine")
    snap["stub_spine_probabilities"] = decisions.get("stub_spine_probabilities") or {}
    snap["stub_write"] = decisions.get("stub_write")
    snap["NEWS_PROTOCOL_APPLIED"] = decisions.get("news_protocol_applied")
    snap["challenge_stub_sync"] = decisions.get("challenge_stub_sync")
    snap["apply_persist"] = decisions.get("apply_persist")
    snap["ecb_oct29_clocks"] = _ecb_clocks(snap.get("events"))
    snap["invented"] = False
    error = decisions.get("stub_sync_error")
    if error not in (None, ""):
        snap["stub_sync_error"] = error
    elif "stub_sync_error" not in snap:
        snap["stub_sync_error"] = None
    snap["model"] = MODEL
    return snap


def _sync_chosen(
    spine: Path | None,
    *,
    caller_stub: Path | None,
    dest: Path,
    write_noul: Any,
) -> dict[str, Any]:
    if spine is None:
        return _blank()
    if not spine.is_file():
        card = _blank("spine_absent")
        card["spine_file"] = _rel(spine)
        card["spine_file_present"] = False
        return card
    try:
        snap = sync_from_spine(
            spine_path=spine,
            stub_path=caller_stub,
            out_path=dest,
            write=write_noul is True,
        )
    except JuneWeekOfRecordError:
        raise
    except Exception as exc:  # noqa: BLE001 — a failed read does not switch spines
        card = _blank(type(exc).__name__)
        card["spine_file"] = _rel(spine)
        card["spine_file_present"] = True
        return card
    if not isinstance(snap, dict):
        card = _blank("sync_not_a_dict")
        card["spine_file"] = _rel(spine)
        card["spine_file_present"] = True
        return card
    snap["spine_file"] = _rel(spine)
    snap["spine_file_present"] = True
    snap["june_week_of_record_untouched"] = True
    return snap


def sync_challenge_stub(
    *,
    spine_path: Path | None = None,
    stub_path: Path | None = None,
    out_path: Path | None = None,
    write: bool | None = None,
) -> dict[str, Any]:
    """Lab snapshot for this state. The spine, write, and parameters are the return.

    A caller path or write flag is a fact on the ask. An empty answer, a tie,
    or an error leaves that field unset. Does not invent events. Does not send.
    """

    caller_spine = None if spine_path is None else Path(spine_path)
    caller_stub = None if stub_path is None else Path(stub_path)
    dest = Path(out_path) if out_path is not None else DEFAULT_OUT
    refuse_june_overwrite(dest)
    proposed = write if isinstance(write, bool) else None
    try:
        questions = _questions()
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return _blank(type(exc).__name__)
    allowed = {"noul", "choice", "score"}
    if not questions or any(
        not isinstance(block, dict) or block.get("type") not in allowed for block in questions.values()
    ):
        return _blank("question_pack_fail")
    asked = _ask(
        _state(
            caller_spine=caller_spine,
            caller_stub=caller_stub,
            dest=dest,
            proposed_write=proposed,
        ),
        questions,
    )
    decisions = _decisions(asked)
    snap = _sync_chosen(
        _spine_path(decisions.get("stub_spine") if isinstance(decisions.get("stub_spine"), str) else None, caller_spine),
        caller_stub=caller_stub,
        dest=dest,
        write_noul=decisions.get("stub_write"),
    )
    return _overlay(snap, decisions)


_BOUND_CARD = None

_SKIP_FACT_KEYS = frozenset({
    "login",
    "magic",
    "model",
    "prior_outcomes",
    "reason_ids",
    "scoped_xau_names",
    "windows",
    "order_send",
    "flatten",
    "namespace",
    "ns",
    "api_url",
    "schema",
    "questions",
    "answers",
    "criteria",
    "instructions",
})
_PRICE_KEYS = frozenset({
    "entry",
    "stop",
    "target",
    "entry_price",
    "stop_loss",
    "take_profit",
    "take_profit_1",
    "bid",
    "ask",
    "price",
    "sl",
    "tp",
    "deal_final",
    "event_stop_now",
    "inv_entry",
    "inv_stop",
})
_PRICE_QIDS = frozenset({
    "inv_entry",
    "inv_stop",
    "entry_stop_parameter",
    "entry_target_parameter",
    "host_named_sl",
})
_WEIGHT_QIDS = frozenset({
    "geometry_vs_tape",
    "session_fitness",
    "level_respect",
    "flow_alignment",
    "persistence",
})
_UNIX_QIDS = frozenset({"gfull_start", "gfull_end", "cutoff_unix"})
_COUNT_LISTS = frozenset({
    "events",
    "rows",
    "candidates",
    "peers",
    "sites",
    "stubs",
    "recipe_rows",
    "recipes",
})
_ORDINAL_EXACT = frozenset({
    "wall_pressure",
    "fill_realism",
    "paper_live_parity",
    "protection_still_earns",
    "session_liquidity",
})


def _bind_card(card):
    global _BOUND_CARD
    if isinstance(card, Mapping):
        _BOUND_CARD = card


def _finite_fact(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _ordinal_words(qid):
    name = str(qid)
    if name == "session_liquidity":
        return ("thin liquidity", "ordinary liquidity", "deep liquidity")
    if name == "include_depth" or name.startswith("include_"):
        return ("hide", "short", "long", "full")
    if name in _ORDINAL_EXACT or name.endswith("_quality"):
        return ("poor", "ordinary", "clean")
    return None


def _qid_unit(qid):
    name = str(qid).lower()
    if _ordinal_words(name):
        return ""
    if "minute" in name:
        return "minutes"
    if name.endswith("_sl") or name in _PRICE_QIDS:
        return "price"
    if name.endswith("_s") or "second" in name or "prefer_s" in name:
        return "seconds"
    if "_pct" in name or "percent" in name:
        return "pct"
    if name.endswith("_r") or "spread_r" in name:
        return "r"
    if name in _WEIGHT_QIDS or "weight" in name or "persist" in name:
        return "weight"
    if (
        name.endswith("_mult")
        or name.endswith("_multiple")
        or "multiplier" in name
        or "_tilt" in name
        or name.endswith("_tilt")
    ):
        return "mult"
    if name in _UNIX_QIDS or name.endswith("_unix"):
        return "unix"
    if "dist" in name or name.endswith("_eps") or "epsilon" in name:
        return "distance"
    if name.endswith("_hour") or name == "utc_hour":
        return "hour"
    if "horizon" in name or name.endswith("_days"):
        return "days"
    if name.endswith("_rate"):
        return "rate"
    if name.endswith("_net"):
        return "money"
    if "line" in name:
        return "lines"
    if (
        name.endswith("_n")
        or "_n_" in name
        or name.endswith("_count")
        or "loop" in name
        or name.endswith("_bars")
        or name.endswith("_cap")
        or name.endswith("_k")
        or name.startswith("n_")
        or "nth" in name
        or "candidate" in name
        or "occupancy" in name
        or "corr_window" in name
        or name.endswith("_shadow")
        or "shadow" in name
    ):
        return "count"
    return ""


def _key_unit(key):
    name = str(key).lower()
    if name in _SKIP_FACT_KEYS or name.startswith("_"):
        return ""
    if "minute" in name:
        return "minutes"
    if name.endswith("_sl") or name in _PRICE_KEYS:
        return "price"
    if name.endswith("_seconds") or name.endswith("_s") or "delta_s" in name or "prefer_s" in name:
        return "seconds"
    if "_pct" in name or name.endswith("_percent") or "percent" in name:
        return "pct"
    if name.endswith("_r") or name in {"spread_r", "locked_r"}:
        return "r"
    if "weight" in name or "persist" in name:
        return "weight"
    if (
        name.endswith("_mult")
        or name.endswith("_multiple")
        or "multiplier" in name
        or name.endswith("_tilt")
        or name in {"tilt", "shadow_tilt"}
    ):
        return "mult"
    if name.endswith("_unix") or name in {"gfull_start", "gfull_end", "cutoff_unix"}:
        return "unix"
    if "dist" in name or name.endswith("_eps") or "epsilon" in name:
        return "distance"
    if name.endswith("_hour") or name == "utc_hour":
        return "hour"
    if "horizon" in name or name.endswith("_days"):
        return "days"
    if name.endswith("_rate"):
        return "rate"
    if name.endswith("_net") or name in {"equity", "balance", "profit", "pnl", "open_pnl", "net"}:
        return "money"
    if "line" in name:
        return "lines"
    if (
        name.endswith("_n")
        or "_n_" in name
        or name.endswith("_count")
        or "loop" in name
        or name.endswith("_bars")
        or name.endswith("_cap")
        or name.endswith("_k")
        or name.startswith("n_")
        or name.endswith("_hits")
        or name.endswith("_anchors")
        or "candidate" in name
        or "nth" in name
        or name == "occupancy_world"
    ):
        return "count"
    return ""


def _fact_label(key, used):
    text = "the " + str(key) + " named on this card"
    if text not in used:
        used.add(text)
        return text
    index = 2
    while True:
        alt = "another " + str(key) + " named on this card (" + str(index) + ")"
        if alt not in used:
            used.add(alt)
            return alt
        index += 1


def _walk_facts(value, key, unit, pairs, labels, seen):
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return
        seen.add(ident)
        for child_key, child in value.items():
            if not isinstance(child_key, str) or child_key.lower() in _SKIP_FACT_KEYS:
                continue
            _walk_facts(child, child_key, unit, pairs, labels, seen)
        return
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return
        seen.add(ident)
        if unit == "count" and str(key).lower() in _COUNT_LISTS:
            pairs.append((_fact_label("count of " + str(key), labels), float(len(value))))
        for item in value:
            if isinstance(item, Mapping):
                _walk_facts(item, key, unit, pairs, labels, seen)
        return
    if _key_unit(key) != unit:
        return
    number = _finite_fact(value)
    if number is None:
        return
    pairs.append((_fact_label(key, labels), number))


def _distance_gap(card, pairs, labels):
    left = None
    right = None

    def walk(node, seen):
        nonlocal left, right
        if not isinstance(node, Mapping):
            return
        ident = id(node)
        if ident in seen:
            return
        seen.add(ident)
        if left is None:
            left = _finite_fact(node.get("left"))
        if right is None:
            right = _finite_fact(node.get("right"))
        for child in node.values():
            if isinstance(child, Mapping):
                walk(child, seen)

    if isinstance(card, Mapping):
        walk(card, set())
    if left is None or right is None:
        return
    pairs.append((_fact_label("stop gap", labels), abs(left - right)))


def _anchors_for(unit, card):
    if not unit or not isinstance(card, Mapping):
        return []
    pairs = []
    labels = set()
    if unit == "weight":
        try:
            from .jev_questions import weight_anchors

            for label, number in weight_anchors(card):
                pairs.append((str(label), number))
                labels.add(str(label))
        except Exception:
            pairs = []
            labels = set()
    _walk_facts(card, "", unit, pairs, labels, set())
    if unit == "distance":
        _distance_gap(card, pairs, labels)
    return pairs


def _pending_score(qid, instructions, words=None):
    text = "" if instructions is None else str(instructions)
    scrub = globals().get("_scrub_text")
    if callable(scrub):
        try:
            cleaned = scrub(text)
        except Exception:
            return None
        if cleaned is None:
            return None
        if isinstance(cleaned, str):
            text = cleaned
    text = text.strip()
    if not text:
        return None
    for guard_name in ("_limit_key", "_skip_key", "_blocked", "_blocked_text", "_bad_text"):
        guard = globals().get(guard_name)
        if not callable(guard):
            continue
        try:
            if guard(str(qid)) or guard(text):
                return None
        except Exception:
            return None
    row = {"type": "score", "instructions": text}
    if words:
        kept = [str(item).strip() for item in words if str(item).strip()]
        if len(kept) >= 2:
            row["_words"] = kept
    return row


def _anchor_questions(questions, card):
    """Rebuild each Score from this card. Fewer than two levels drops that Score."""

    if not isinstance(questions, Mapping):
        return questions
    _bind_card(card)
    out = {}
    for key, block in questions.items():
        if not isinstance(block, dict) or str(block.get("type") or "") != "score":
            out[key] = block
            continue
        name = str(key)
        words = block.get("_words")
        if not isinstance(words, (list, tuple)):
            words = _ordinal_words(name)
        try:
            if words:
                from .jev_questions import ordinal_question

                built = ordinal_question(name, str(block.get("instructions") or ""), words)
            else:
                from .jev_questions import amount_question

                built = amount_question(
                    name,
                    str(block.get("instructions") or ""),
                    _anchors_for(_qid_unit(name), card),
                )
        except Exception:
            continue
        row = built.get(name) if isinstance(built, dict) else None
        if not isinstance(row, dict) or not row.get("criteria"):
            continue
        if block.get("ignore_if"):
            row = dict(row)
            row["ignore_if"] = block.get("ignore_if")
        out[key] = row
    return out


def _snap_ordinal(block, n_levels):
    try:
        count = int(n_levels)
    except (TypeError, ValueError):
        return None
    if count < 2:
        return None
    try:
        from .jev_questions import ordinal_index

        return ordinal_index(block, count)
    except Exception:
        return None


def _snap_if_ordinal(qid, block, fallback):
    words = _ordinal_words(qid)
    if not words:
        return fallback
    return _snap_ordinal(block, len(words))
