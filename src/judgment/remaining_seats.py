"""Remaining Challenge decision walls — TypeSafe packs, not linear keep/drop.

Seats PR #67 (size+close), #68 (admission/place), and #69 (gate admit) do
not own: already_placed_today / cluster later-bar, restart-chase
``_entry_too_late``, hydrate TP remint, activation mint, sleeve ``ac60``
cliffs, A8 K=3-of-4 as a drop.

Every decision in this module, and every parameter of that decision, is
the System One return for that state. Model ``jev-1.13.0``. The post is
``jev_client.evaluate`` (POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``). Questions are only Noul, Choice, or Score.
A Choice is the unique highest probability. A Score is the returned
number and may sit between levels. A Noul is a bool or a probability.
Prior outcomes are attached on every ask, and the return is appended
for the next ask. An empty answer, a tie, or an error leaves that
return unset and does not restore a constant. Floor and baseline are
not a question. This pack stays hierarchical. It does not flatten into
a linear keep/drop.

Founder shape (Diogo memo, not an API primer): Noul per **context chunk**,
Score include-depth hide/short/long/full, many TypeSafe calls from one
intent, explicit reads vs writes, hierarchical labels + log(n) tree
search. Do not Noul every tick because it is cheap. Do not compact a
Challenge session as if every future turn wanted one shared state. Do not
implement Tamara-style linear binary keep/drop.

Code owns workflow. TypeSafe owns the semantic call. Missing Jev → no
extra PASS. Integers still compute facts (keep-one occupied, already_placed
*this bar*, 2-stop COUNT, named surface, prop wall, FLATTEN.flag,
weekend-flat, token digest). Writer still prints. W7 ns bit-identical.

Default-on for Challenge ``operator`` / login 0.
``GTOS_JEV_REMAINING=0`` restores the old ifs. ``GTOS_JEV_REMINT=0``
restores ungated ``cmd_mint``. This module never remints a VPS and never
sends an order.

Folded onto the 69/68/67/70 tip: ``evaluate_pack`` dumps hierarchical
packs through stacked ``evaluate(questions=..., merge_sleeve=False)``.
Two reads from one intent (include-depth, then the decision pack). Not a
private HTTP hop and not a keep/drop wall.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .apply_size import CHALLENGE_LOGIN, CHALLENGE_NS, is_challenge_account
from .jev_questions import MODEL

REMAINING_ENV = "GTOS_JEV_REMAINING"
REMINT_ENV = "GTOS_JEV_REMINT"
BOOK_LOGIN = int(CHALLENGE_LOGIN) if str(CHALLENGE_LOGIN).isdigit() else 0
MAGIC = 0

INCLUDE_HIDE = 0
INCLUDE_SHORT = 1
INCLUDE_LONG = 2
INCLUDE_FULL = 3
INCLUDE_NAMES = ("hide", "short", "long", "full")

KIND_READ = "read"
KIND_WRITE = "write"

SUBGOAL_PLACE_WALL = "place_wall"
SUBGOAL_RESTART = "restart_chase"
SUBGOAL_REMINT = "remint_authorize"
SUBGOAL_SLEEVE = "sleeve_emit"
SUBGOAL_A8 = "a8_move_k"

_FALSY = frozenset({"0", "false", "no", "off"})
_tls = threading.local()
_cache_lock = threading.Lock()
_include_cache: dict[str, dict[str, float | None]] = {}
_CACHE_CAP = 256
_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "110000",
    "110,000",
    "110_000",
    "110k",
    "floor",
    "baseline",
)
_QUESTION_TYPES = frozenset({"noul", "choice", "score"})

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRINT = REPO_ROOT / "judgment" / "astra" / "lab" / "a1" / "remaining_seats_print.jsonl"

_INCLUDE_CRITERIA = [
    "hide — this chunk is not needed for this subgoal",
    "short — flags and counts only",
    "long — named fields, no raw bars or full event lists",
    "full — the whole chunk",
]


def remaining_seats_env_on(*, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    raw = str(env.get(REMAINING_ENV, "1")).strip().lower()
    return raw not in _FALSY


def remint_env_on(*, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    raw = str(env.get(REMINT_ENV, "1")).strip().lower()
    return raw not in _FALSY


def bind_namespace(ns: Any) -> None:
    """Process/thread label so generators can see Challenge ns without a config byte."""
    _tls.namespace = None if ns in (None, "") else str(ns).strip()


def bound_namespace() -> str | None:
    got = getattr(_tls, "namespace", None)
    return str(got) if got else None


def challenge_bound(*, login: Any = None, ns: Any = None) -> bool:
    namespace = ns if ns not in (None, "") else bound_namespace()
    if login is None and namespace:
        return is_challenge_account(ns=namespace)
    return is_challenge_account(login=login, ns=namespace)


def challenge_remaining_on(
    *,
    login: Any = None,
    ns: Any = None,
    environ: Mapping[str, str] | None = None,
) -> bool:
    if not remaining_seats_env_on(environ=environ):
        return False
    return challenge_bound(login=login, ns=ns)


def resolve_owner_login(owner: Any) -> Any:
    """Best-effort MT5 / config login. Never raises."""
    try:
        mt5 = getattr(owner, "_mt5", None)
        if mt5 is not None:
            fn = getattr(mt5, "get_account_login", None)
            if callable(fn):
                try:
                    got = fn()
                    if got is not None:
                        return got
                except Exception:
                    pass
            info = getattr(mt5, "account_info", None)
            if callable(info):
                try:
                    got = getattr(info(), "login", None)
                    if got is not None:
                        return got
                except Exception:
                    pass
        base = getattr(owner, "base_config", None) or {}
        return (base.get("deployment") or {}).get("mt5_login")
    except Exception:
        return None


LABEL_PATH = (
    "book",
    "ns",
    "sleeve",
    "symbol",
    "side",
    "decision_day",
    "ticket",
    "subgoal",
)


def label_path(labels: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Nested path for log(n) lookup. Not a linear scan of messages."""
    labels = labels or {}
    return tuple(str(labels.get(key) if labels.get(key) not in (None, "") else "_") for key in LABEL_PATH)


class LabelIndex:
    """Hierarchical label tree. Lookup walks depth, not a transcript."""

    def __init__(self) -> None:
        self._root: dict[str, Any] = {}

    def insert(self, labels: Mapping[str, Any], payload: Any) -> None:
        node = self._root
        for part in label_path(labels):
            node = node.setdefault(part, {})
        node["_payload"] = payload

    def lookup(self, labels: Mapping[str, Any]) -> Any:
        node: Any = self._root
        for part in label_path(labels):
            if not isinstance(node, dict):
                return None
            node = node.get(part)
            if node is None:
                return None
        if isinstance(node, dict):
            return node.get("_payload")
        return None

    def prefix(self, **want: Any) -> list[Any]:
        """Walk only the named prefix. Does not scan a message list."""
        node: Any = self._root
        for key in LABEL_PATH:
            if key not in want:
                break
            raw = want[key]
            part = str(raw) if raw not in (None, "") else "_"
            if not isinstance(node, dict):
                return []
            node = node.get(part)
            if node is None:
                return []
        found: list[Any] = []
        stack = [node]
        while stack:
            cur = stack.pop()
            if not isinstance(cur, dict):
                continue
            if "_payload" in cur:
                found.append(cur["_payload"])
            stack.extend(v for k, v in cur.items() if k != "_payload")
        return found


def label_tree(
    *,
    sleeve: Any = None,
    symbol: Any = None,
    side: Any = None,
    as_of_utc: Any = None,
    decision_day: Any = None,
    ticket: Any = None,
    subgoal: str,
    candidate_id: Any = None,
    cluster: Any = None,
    ns: Any = None,
) -> dict[str, Any]:
    """Nested labels so a later tree-search can find this fire. Not a transcript."""
    day = str(decision_day or "")[:10] or None
    as_of = _stamp(as_of_utc)
    return {
        "book": BOOK_LOGIN,
        "ns": str(ns or bound_namespace() or CHALLENGE_NS),
        "magic": MAGIC,
        "sleeve": None if sleeve in (None, "") else str(sleeve),
        "symbol": None if symbol in (None, "") else str(symbol),
        "side": None if side in (None, "") else str(side),
        "as_of_utc": as_of,
        "decision_day": day or (as_of[:10] if as_of else None),
        "ticket": None if ticket in (None, "") else str(ticket),
        "candidate_id": None if candidate_id in (None, "") else str(candidate_id),
        "cluster": None if cluster in (None, "") else str(cluster),
        "subgoal": subgoal,
    }


def _stamp(raw: Any) -> str | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, datetime):
        dt = raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = str(raw).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return str(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _include_question(chunk: str) -> dict[str, Any]:
    return {
        "type": "score",
        "instructions": (
            f"For this subgoal only, the score is how much of chunks.{chunk} belongs in context. "
            "The scale is hide, short, long, full. The score may sit between those levels. "
            "An empty score leaves the depth unset. "
            "Query-aware include-depth — not a yes/no keep/drop on every field, "
            "and not a session compaction. An empty news spine is not a 'no HIGH' answer."
        ),
        "criteria": list(_INCLUDE_CRITERIA),
    }


INCLUDE_DEPTH_PACK: dict[str, dict[str, Any]] = {
    "include_occupancy": _include_question("occupancy"),
    "include_tape": _include_question("tape"),
    "include_a8": _include_question("a8"),
    "include_news": _include_question("news"),
    "include_remint": _include_question("remint"),
}

PLACE_WALL_PACK: dict[str, dict[str, Any]] = {
    "state_sufficient": {
        "type": "noul",
        "instructions": (
            "Is the labeled occupancy chunk complete enough to judge this place-wall "
            "as-of labels.as_of_utc? Missing isolated_reentry_legal is incomplete. "
            "Do not treat empty news as 'no HIGH'."
        ),
        "criteria": {
            "true": "Named occupancy is present enough to judge a new isolated fire",
            "false": "A required occupancy integer is missing or unknown",
        },
    },
    "isolated_reentry_is_new": {
        "type": "noul",
        "instructions": (
            "Do writer integers say this is a new named fire on a FLAT symbol "
            "(isolated ≥15m), not the spent ticket? Challenge XAU: 291096187 remint-of "
            "291072108 (dsp_walked_hi), both orig_stop. Occupancy KEEP-one is dead as a "
            "judgment; it stays an integer. This Noul is how re-entry stays a decision. "
            "2-stop COUNT stays an integer. Do not invent a remint. Do not re-encode "
            "leftover H4/USDJPY lists as cliffs."
        ),
        "criteria": {
            "true": "Named isolated re-entry is a new fire on a flat symbol",
            "false": "Spent ticket / not isolated / unknown",
        },
    },
    "place_wall": {
        "type": "choice",
        "instructions": (
            "Given the named occupancy on this state, does this place-wall yield or skip? "
            "The option you return is that decision. "
            "An empty answer or a tie is not a decision. "
            "Keep-one occupied, already placed this bar, and the 2-stop count stay integers on the state. "
            "You do not send."
        ),
        "criteria": {
            "yield": "This named fire yields through the place-wall",
            "skip": "This place-wall does not yield",
        },
    },
    "cluster_same_day": {
        "type": "noul",
        "instructions": (
            "LABEL only: named same-day cluster on this sleeve/symbol? "
            "Not a refuse. Occupancy KEEP-one stays the integer."
        ),
        "criteria": {
            "true": "Named cluster already placed another bar today",
            "false": "No named cluster, or unknown",
        },
    },
}

RESTART_PACK: dict[str, dict[str, Any]] = {
    "state_sufficient": {
        "type": "noul",
        "instructions": (
            "Is the labeled tape chunk complete enough to judge restart-chase "
            "(bar iso, timeframe minutes, lateness frac, now)?"
        ),
        "criteria": {
            "true": "Named tape is present enough to judge a chase",
            "false": "Bar or timeframe is missing",
        },
    },
    "chase_toxicity": {
        "type": "score",
        "instructions": (
            "The score is how toxic this restart chase is on the named tape. "
            "It may sit between the levels. An empty score leaves the parameter unset. "
            "Read bars since decision, pending age, sessions.named, tape.late_frac. "
            "Do not call a legal isolated reprint a remint."
        ),
        "criteria": [
            "Restart chase / aged pending on a dead or wrong hour",
            "Ordinary continuation of the same named setup",
            "Fresh named setup, not a chase",
        ],
    },
    "restart_chase": {
        "type": "choice",
        "instructions": (
            "Given the named tape, should this late-after-restart signal skip, "
            "shadow, or still send? The option you return is that decision. "
            "An empty answer or a tie is not a decision. "
            "A send is a write the caller owns. You do not send."
        ),
        "criteria": {
            "skip": "Too late / chase — do not send",
            "place_shadow": "Record the fire, do not send",
            "send": "Named tape says this is still the setup, not a chase",
        },
    },
}

REMINT_PACK: dict[str, dict[str, Any]] = {
    "state_sufficient": {
        "type": "noul",
        "instructions": (
            "Is the remint chunk complete enough to authorize a mutating command "
            "(ticket, hydrator present, proposed TP modify, live_broker_authority)?"
        ),
        "criteria": {
            "true": "Named remint object is complete enough to judge",
            "false": "Ticket/hydrator/authority missing",
        },
    },
    "remint_authorize": {
        "type": "choice",
        "instructions": (
            "Permission Noul analog: should this mutating remint run? "
            "The option you return is that decision. "
            "An empty answer or a tie is not a decision. "
            "authorize means the caller may modify broker TP or write an activation token. "
            "leave_orig means hydrate without modifying TP. "
            "refuse means do not mint and do not modify. "
            "You do not write the broker. "
            "Challenge tokens and broker payloads are the don't-yoink class — do not "
            "route this chunk to a cheap vendor."
        ),
        "criteria": {
            "refuse": "Do not mint and do not modify broker TP",
            "leave_orig": "Hydrate locally; do not modify broker TP; do not mint",
            "authorize": "Named state supports the mutating remint the caller proposed",
        },
    },
}

SLEEVE_PACK: dict[str, dict[str, Any]] = {
    "state_sufficient": {
        "type": "noul",
        "instructions": (
            "Is ac60 named (not warmup None) so persistence can be scored as a range?"
        ),
        "criteria": {
            "true": "ac60 is named",
            "false": "ac60 null — warmup, integer cliff stays",
        },
    },
    "persistence": {
        "type": "score",
        "instructions": (
            "Is persistence with named gold flow a range on this bar, or a coin? "
            "The score you return is that parameter. It may sit between the levels. "
            "An empty score leaves the parameter unset. "
            "Do not re-encode an ac60 cliff."
        ),
        "criteria": [
            "Fighting / mean-reverting versus the side",
            "Random / coin",
            "Persistent with the named side",
        ],
    },
    "a8_quality": {
        "type": "score",
        "instructions": (
            "The score is A8 confluence on this bar. It may sit between the levels. "
            "An empty score leaves the parameter unset. "
            "Integer K=3-of-4 still computes as a fact. Ignore when not metals."
        ),
        "criteria": [
            "0–1 of the named A8 fields",
            "2-of-4",
            "3–4-of-4 and news/levels do not contradict",
        ],
    },
    "a8_agrees": {
        "type": "noul",
        "instructions": (
            "Does a8_k_of_4_pass agree with the named A8 fields? Consistency only, "
            "not a re-vote of the integer gate. Ignore when not a metals sleeve."
        ),
        "criteria": {
            "true": "Named A8 fields agree with the integer pass bit",
            "false": "Named A8 fields disagree or are missing",
        },
    },
    "sleeve_emit": {
        "type": "choice",
        "instructions": (
            "Given persistence as a range and named A8, should this generator emit, "
            "hold, or drop? The option you return is that decision. "
            "An empty answer or a tie is not a decision. "
            "The ac60 cliff stays an integer fact on this state. You do not place."
        ),
        "criteria": {
            "emit": "Named persistence/A8 support emitting this sleeve's intent",
            "hold": "Mixed — do not emit, do not invent a second cliff",
            "drop": "Named tape argues against emitting",
        },
    },
    "a8_keep": {
        "type": "choice",
        "instructions": (
            "Integer K failed on this bar. Do the named A8 fields keep it or release it? "
            "The option you return is that decision. "
            "An empty answer or a tie is not a decision. You do not place."
        ),
        "criteria": {
            "keep": "Named A8 fields keep this failed-K bar",
            "release": "Named A8 fields release this failed-K bar",
        },
    },
}

CHUNKS_FOR_SUBGOAL: dict[str, tuple[str, ...]] = {
    SUBGOAL_PLACE_WALL: ("occupancy", "news"),
    SUBGOAL_RESTART: ("tape", "occupancy"),
    SUBGOAL_REMINT: ("remint", "occupancy"),
    SUBGOAL_SLEEVE: ("a8", "tape"),
    SUBGOAL_A8: ("a8", "news"),
}

DECISION_PACKS: dict[str, dict[str, dict[str, Any]]] = {
    SUBGOAL_PLACE_WALL: PLACE_WALL_PACK,
    SUBGOAL_RESTART: RESTART_PACK,
    SUBGOAL_REMINT: REMINT_PACK,
    SUBGOAL_SLEEVE: SLEEVE_PACK,
    SUBGOAL_A8: SLEEVE_PACK,
}


def assemble_remaining_state(
    *,
    subgoal: str,
    sleeve: Any = None,
    symbol: Any = None,
    side: Any = None,
    as_of_utc: Any = None,
    decision_day: Any = None,
    ticket: Any = None,
    candidate_id: Any = None,
    cluster: Any = None,
    ns: Any = None,
    occupancy: Mapping[str, Any] | None = None,
    tape: Mapping[str, Any] | None = None,
    a8: Mapping[str, Any] | None = None,
    news: Mapping[str, Any] | None = None,
    remint: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Explicit state object for this fire. Nulls stay null. Not a chat log."""
    labels = label_tree(
        sleeve=sleeve,
        symbol=symbol,
        side=side,
        as_of_utc=as_of_utc,
        decision_day=decision_day,
        ticket=ticket,
        subgoal=subgoal,
        candidate_id=candidate_id,
        cluster=cluster,
        ns=ns,
    )
    chunks = {
        "occupancy": dict(occupancy or {}),
        "tape": dict(tape or {}),
        "a8": dict(a8 or {}),
        "news": dict(news or {}),
        "remint": dict(remint or {}),
    }
    return {
        "schema": "gtos.judgment.remaining_seats.v0",
        "kind": KIND_READ,
        "labels": labels,
        "chunks": chunks,
        "identity": {
            "sleeve": labels["sleeve"],
            "symbol": labels["symbol"],
            "side": labels["side"],
            "ticket": labels["ticket"],
            "candidate_id": labels["candidate_id"],
            "family_class": (extra or {}).get("family_class"),
        },
        "clock": {"as_of_utc": labels["as_of_utc"]},
        "extra": dict(extra or {}),
    }


def chunks_for(subgoal: str, state: Mapping[str, Any]) -> tuple[str, ...]:
    """Query-aware chunk set. Ignore-if is compression: empty news is not scored as 'no HIGH'."""
    wanted = list(CHUNKS_FOR_SUBGOAL.get(subgoal, ()))
    chunks = state.get("chunks") or {}
    news = chunks.get("news") or {}
    if "news" in wanted and (news.get("spine_empty") is True or not news.get("events")):
        wanted = [name for name in wanted if name != "news"]
    a8 = chunks.get("a8") or {}
    sleeve = str((state.get("labels") or {}).get("sleeve") or "")
    metals = sleeve.startswith("metals_")
    if "a8" in wanted and not metals and a8.get("source") in (None, "unassembled"):
        wanted = [name for name in wanted if name != "a8"]
    return tuple(wanted)


def include_depth_pack_for(subgoal: str, state: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    names = chunks_for(subgoal, state)
    return {f"include_{name}": INCLUDE_DEPTH_PACK[f"include_{name}"] for name in names}


def _number(value: Any) -> float | None:
    """A returned number. Booleans and non-finite values stay empty."""

    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _returned_score(block: Any) -> float | None:
    """The score this hop returned. It is not snapped to a level."""

    number = None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = None
    parsed = _number(number)
    if parsed is not None:
        return parsed
    if not isinstance(block, dict):
        return None
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _number(raw)


def _noul_value(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A float is not cut to a line."""

    if not isinstance(block, dict):
        return None
    if "noul" in block:
        raw = block.get("noul")
    elif "Noul" in block:
        raw = block.get("Noul")
    else:
        return None
    if raw is True or raw is False:
        return raw
    return _number(raw)


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict):
        return {}
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _number(value)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _unique_local(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest among the options. A tie or an empty map is not a decision."""

    if not probabilities or not order:
        return None
    best: str | None = None
    best_p = -1.0
    tied = False
    for name in order:
        try:
            p = float(probabilities.get(name, 0.0) or 0.0)
        except (TypeError, ValueError):
            p = 0.0
        if best is None or p > best_p + 1e-12:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    if tied or best is None:
        return None
    return best


def _unique_choice(block: Any, order: tuple[str, ...]) -> str | None:
    """The choice is the unique highest probability. A bare label is not a decision."""

    numeric = _probabilities(block)
    if not numeric or not order:
        return None
    picked: str | None = None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(numeric, order)
    except Exception:
        picked = _unique_local(numeric, order)
    if picked not in order:
        return None
    return str(picked)


def _choice_at(answers: Mapping[str, Any] | None, key: str, order: tuple[str, ...]) -> str | None:
    if not isinstance(answers, Mapping):
        return None
    return _unique_choice(answers.get(key), order)


def _include_level(score: float | None) -> int | None:
    """An exact scale point. A score between hide, short, long, and full stays between."""

    if score is None:
        return None
    for level in (INCLUDE_HIDE, INCLUDE_SHORT, INCLUDE_LONG, INCLUDE_FULL):
        if abs(score - float(level)) <= 1e-9:
            return level
    return None


def _limit_key(name: Any) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    for token in _BANNED_TEXT:
        probe = token.replace(",", "").replace("_", "").lower()
        if probe and probe in compact:
            return True
    return False


def _scrub_limits(value: Any) -> Any:
    """Floor and baseline are not a question. Drop them before the ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _limit_key(key):
                continue
            out[str(key)] = _scrub_limits(item)
        return out
    if isinstance(value, list):
        return [_scrub_limits(item) for item in value]
    if isinstance(value, tuple):
        return [_scrub_limits(item) for item in value]
    if isinstance(value, str) and _banned_text(value):
        return ""
    return value


def _scrub_question_text(text: str) -> str:
    kept: list[str] = []
    for sentence in str(text).split(". "):
        if _banned_text(sentence):
            continue
        kept.append(sentence)
    return ". ".join(kept).strip()


def _pack_questions(questions: Mapping[str, Any]) -> dict[str, Any]:
    """Noul, Choice, and Score only. Floor and baseline are not asked."""

    clean: dict[str, Any] = {}
    for key, block in dict(questions).items():
        if _limit_key(key) or not isinstance(block, dict):
            continue
        qtype = str(block.get("type") or "").strip().lower()
        if qtype not in _QUESTION_TYPES:
            continue
        row = dict(block)
        row["type"] = qtype
        text = row.get("instructions")
        if isinstance(text, str):
            row["instructions"] = _scrub_question_text(text)
        criteria = row.get("criteria")
        if isinstance(criteria, Mapping):
            row["criteria"] = {
                str(name): value
                for name, value in criteria.items()
                if not _limit_key(name) and not (isinstance(value, str) and _banned_text(value))
            }
        elif isinstance(criteria, list):
            row["criteria"] = [
                item for item in criteria if not (isinstance(item, str) and _banned_text(item))
            ]
        clean[str(key)] = row
    return clean


def depths_from_answers(
    answers: Mapping[str, Any] | None,
    chunks: tuple[str, ...],
) -> dict[str, float | None]:
    """Include-depth scores. A missing score stays unset."""

    answers = answers or {}
    out: dict[str, float | None] = {}
    for name in chunks:
        out[name] = _returned_score(answers.get(f"include_{name}"))
    return out


def project_state(state: Mapping[str, Any], depths: Mapping[str, Any]) -> dict[str, Any]:
    """Query-shaped context. An exact hide/short/long/full score shapes the chunk.

    A missing score stays unset. A score between those levels stays the number
    and does not snap to a neighbor.
    """

    projected = json.loads(json.dumps(state, default=str))
    chunks = dict(projected.get("chunks") or {})
    include: dict[str, Any] = {}
    asked = depths if isinstance(depths, Mapping) else {}
    for name, chunk in chunks.items():
        if name not in asked:
            include[name] = None
            chunks[name] = {"included": None}
            continue
        score = _number(asked.get(name))
        level = _include_level(score)
        body = dict(chunk) if isinstance(chunk, Mapping) else {"value": chunk}
        if score is None or level is None:
            include[name] = score
            body["included"] = score
            chunks[name] = body
            continue
        include[name] = INCLUDE_NAMES[level]
        if level <= INCLUDE_HIDE:
            chunks[name] = {"included": "hide"}
        elif level == INCLUDE_SHORT:
            chunks[name] = _short_chunk(name, body)
        elif level == INCLUDE_LONG:
            chunks[name] = _long_chunk(name, body)
        else:
            body["included"] = "full"
            chunks[name] = body
    projected["chunks"] = chunks
    projected["include_depth"] = include
    projected["kind"] = KIND_READ
    return projected


def _short_chunk(name: str, chunk: Mapping[str, Any]) -> dict[str, Any]:
    if name == "occupancy":
        keys = (
            "symbol_open",
            "already_placed_today",
            "cluster_placed_today",
            "isolated_reentry_legal",
            "minutes_since_flat",
            "keep_one_symbol",
        )
    elif name == "tape":
        keys = ("late", "late_frac", "tf_minutes", "sessions_named", "bars_since_decision")
    elif name == "a8":
        keys = ("ac60", "a8_k_of_4_pass", "k_pass", "sleeve")
    elif name == "news":
        keys = ("spine_empty", "n_events")
    elif name == "remint":
        keys = ("ticket", "proposed_modify_tp", "live_broker_authority", "command")
    else:
        keys = tuple(chunk.keys())[:6]
    out = {k: chunk.get(k) for k in keys}
    out["included"] = "short"
    return out


def _long_chunk(name: str, chunk: Mapping[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in chunk.items() if k not in {"bars", "events", "raw", "bytes"}}
    if name == "news" and "events" in chunk:
        events = chunk.get("events") or []
        out["n_events"] = len(events) if isinstance(events, list) else None
    out["included"] = "long"
    return out


def _cache_key(state: Mapping[str, Any], chunks: tuple[str, ...]) -> str:
    labels = state.get("labels") or {}
    payload = {
        "subgoal": labels.get("subgoal"),
        "book": labels.get("book"),
        "sleeve": labels.get("sleeve"),
        "symbol": labels.get("symbol"),
        "day": labels.get("decision_day"),
        "ticket": labels.get("ticket"),
        "chunks": {name: (state.get("chunks") or {}).get(name) for name in chunks},
    }
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def cached_include_depths(key: str) -> dict[str, float | None] | None:
    with _cache_lock:
        got = _include_cache.get(key)
        return dict(got) if got else None


def store_include_depths(key: str, depths: Mapping[str, float | None]) -> None:
    with _cache_lock:
        if len(_include_cache) >= _CACHE_CAP:
            _include_cache.pop(next(iter(_include_cache)))
        _include_cache[key] = dict(depths)


def reset_include_cache() -> None:
    with _cache_lock:
        _include_cache.clear()


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    """Prior outcomes on this ask. A miss does not invent a history."""

    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        return
    if loaded is not None:
        state["prior_outcomes"] = loaded


def _remember_pack(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    answers: Mapping[str, Any],
    error: str | None,
) -> None:
    """The return is the next ask's history. A miss is stored as a miss."""

    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, spec in questions.items():
        if not isinstance(spec, dict):
            continue
        qtype = str(spec.get("type") or "")
        block = answers.get(key) if isinstance(answers, Mapping) else None
        value: Any = None
        if qtype == "choice":
            criteria = spec.get("criteria") or {}
            order = tuple(str(name) for name in criteria) if isinstance(criteria, Mapping) else ()
            value = _unique_choice(block, order)
        elif qtype == "score":
            value = _returned_score(block)
        elif qtype == "noul":
            value = _noul_value(block)
        else:
            continue
        miss = error if value is None else None
        if value is None and not miss:
            miss = "empty"
        try:
            append_outcome(str(key), value, logged, error=miss)
        except Exception:
            continue


def evaluate_pack(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    *,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Dump THIS hierarchical pack through one ``evaluate(questions=)``.

    Include-depth and the decision pack stay two reads from one intent, not a
    flattened keep/drop and not a second HTTP client. ``merge_sleeve`` stays
    False so occupancy and remint packs are that subtree only. Model
    ``jev-1.13.0``. Prior outcomes ride on the ask. Never raises into a fire path.
    """
    pack = _pack_questions(questions)
    posted = _scrub_limits(dict(state))
    if not isinstance(posted, dict):
        posted = {}
    posted.pop("prior_outcomes", None)
    posted["model"] = MODEL
    if not pack:
        return {
            "ok": False,
            "skipped": "empty_pack",
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
        }
    _attach_priors(posted, pack)
    try:
        from .jev_client import evaluate as _evaluate

        receipt = _evaluate(
            posted,
            questions=pack,
            timeout_s=timeout_s,
            model=MODEL,
            merge_sleeve=False,
        )
    except Exception as exc:  # noqa: BLE001 — fire-path must never raise
        receipt = {
            "ok": False,
            "skipped": type(exc).__name__,
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
        }
    out = dict(receipt) if isinstance(receipt, Mapping) else {"ok": False, "answers": {}}
    answers = out.get("answers")
    if not isinstance(answers, dict):
        answers = {}
        out["answers"] = answers
    error = None
    if out.get("ok") is not True:
        error = str(out.get("skipped") or out.get("error") or "empty")
    elif not answers:
        error = "empty"
    _remember_pack(posted, pack, answers, error)
    out.setdefault("kind", KIND_READ)
    out["model"] = out.get("model") or MODEL
    return out


def fanout_remaining(
    state: dict[str, Any],
    *,
    subgoal: str,
    evaluate_jev: bool = True,
    include_answers: Mapping[str, Any] | None = None,
    decision_answers: Mapping[str, Any] | None = None,
    skipped: str | None = None,
) -> dict[str, Any]:
    """Two TypeSafe calls from one intent: include-depth, then the decision pack.

    Not Noul-every-field. Not a session summary. Include-depth may reuse a
    same-fire cache (cost-aware); decisions are not compacted across turns.
    """
    names = chunks_for(subgoal, state)
    include_pack = include_depth_pack_for(subgoal, state)
    cache_key = _cache_key(state, names)
    depths: dict[str, float | None] | None = None
    include_receipt: dict[str, Any] = {"ok": True, "skipped": None, "answers": {}, "cached": False}
    if include_answers is not None:
        depths = depths_from_answers(include_answers, names)
        include_receipt = {"ok": True, "skipped": None, "answers": dict(include_answers), "cached": False}
    elif decision_answers is not None:
        depths = {name: None for name in names}
    else:
        cached = cached_include_depths(cache_key)
        if cached is not None:
            depths = cached
            include_receipt = {"ok": True, "skipped": None, "answers": {}, "cached": True}
        elif evaluate_jev and include_pack:
            include_receipt = evaluate_pack(dict(state), include_pack)
            if include_receipt.get("ok") is not True:
                return {
                    "ok": False,
                    "skipped": include_receipt.get("skipped")
                    or include_receipt.get("error")
                    or "include_depth_not_ok",
                    "depths": {name: None for name in names},
                    "projected": dict(state),
                    "answers": {},
                    "include_receipt": {**include_receipt, "cached": False},
                    "decision_receipt": {},
                    "n_calls": 1,
                    "kind": KIND_READ,
                }
            depths = depths_from_answers(include_receipt.get("answers") or {}, names)
            if names and all(_number(depths.get(name)) is not None for name in names):
                store_include_depths(cache_key, depths)
            include_receipt = {**include_receipt, "cached": False}
        else:
            depths = {name: None for name in names}
    if depths is None:
        depths = {name: None for name in names}
    projected = project_state(state, depths)
    decision_pack = DECISION_PACKS.get(subgoal) or {}
    decision_receipt: dict[str, Any]
    asked_include = bool(
        include_pack
        and include_answers is None
        and decision_answers is None
        and evaluate_jev
        and not include_receipt.get("cached")
    )
    n_calls = 1 if asked_include else 0
    if decision_answers is not None:
        decision_receipt = {"ok": True, "skipped": skipped, "answers": dict(decision_answers)}
    elif not evaluate_jev:
        return {
            "ok": False,
            "skipped": skipped or "evaluate_jev_false",
            "depths": depths,
            "projected": projected,
            "answers": {},
            "include_receipt": include_receipt,
            "decision_receipt": {
                "ok": False,
                "skipped": skipped or "evaluate_jev_false",
                "answers": {},
            },
            "n_calls": n_calls,
            "kind": KIND_READ,
        }
    else:
        decision_receipt = evaluate_pack(projected, decision_pack)
        n_calls += 1
        if decision_receipt.get("ok") is not True:
            return {
                "ok": False,
                "skipped": decision_receipt.get("skipped")
                or decision_receipt.get("error")
                or skipped
                or "decision_not_ok",
                "depths": depths,
                "projected": projected,
                "answers": decision_receipt.get("answers") or {},
                "include_receipt": include_receipt,
                "decision_receipt": decision_receipt,
                "n_calls": n_calls,
                "kind": KIND_READ,
            }
    answers = dict(decision_receipt.get("answers") or {})
    return {
        "ok": True,
        "skipped": skipped or decision_receipt.get("skipped"),
        "depths": depths,
        "projected": projected,
        "answers": answers,
        "include_receipt": include_receipt,
        "decision_receipt": decision_receipt,
        "n_calls": n_calls,
        "kind": KIND_READ,
    }


@dataclass
class RemainingDecision:
    action: str
    reason: str
    skipped: str | None = None
    answers: dict[str, Any] = field(default_factory=dict)
    depths: dict[str, Any] = field(default_factory=dict)
    n_calls: int = 0
    kind: str = KIND_READ
    write: bool = False
    state: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "reason": self.reason,
            "skipped": self.skipped,
            "depths": self.depths,
            "n_calls": self.n_calls,
            "kind": KIND_WRITE if self.write else KIND_READ,
            "write": self.write,
        }


def _no_decision(reason: str, *, skipped: str | None = None, **extra: Any) -> RemainingDecision:
    return RemainingDecision(
        action="jev_no_decision",
        reason=reason,
        skipped=skipped,
        kind=KIND_READ,
        write=False,
        **{k: v for k, v in extra.items() if k in RemainingDecision.__dataclass_fields__},
    )


_PLACE_ORDER = ("yield", "skip")
_RESTART_ORDER = ("skip", "place_shadow", "send")
_REMINT_ORDER = ("refuse", "leave_orig", "authorize")
_SLEEVE_ORDER = ("emit", "hold", "drop")
_A8_KEEP_ORDER = ("keep", "release")


def _from_choice(
    state: dict[str, Any],
    fan: Mapping[str, Any],
    key: str,
    order: tuple[str, ...],
    *,
    write_on: str | None = None,
) -> RemainingDecision:
    """The action is the unique choice. A miss, a tie, or an error stays unset."""

    common = {
        "answers": fan.get("answers") or {},
        "depths": fan.get("depths") or {},
        "n_calls": int(fan.get("n_calls") or 0),
        "state": state,
    }
    if not fan.get("ok"):
        return _no_decision(
            "jev_no_decision",
            skipped=str(fan.get("skipped") or "jev_not_ok"),
            **common,
        )
    named = _choice_at(common["answers"], key, order)
    if named is None:
        return _no_decision(
            "jev_no_decision",
            skipped=f"{key}_unset",
            **common,
        )
    write = write_on is not None and named == write_on
    return RemainingDecision(
        action=named,
        reason=f"{key}_{named}",
        kind=KIND_WRITE if write else KIND_READ,
        write=write,
        **common,
    )


def decide_place_wall(
    *,
    occupancy: Mapping[str, Any] | None = None,
    news: Mapping[str, Any] | None = None,
    sleeve: Any = None,
    symbol: Any = None,
    side: Any = None,
    as_of_utc: Any = None,
    decision_day: Any = None,
    ticket: Any = None,
    cluster: Any = None,
    wall: str = "already_placed_today",
    login: Any = None,
    ns: Any = None,
    evaluate_jev: bool = True,
    answers: Mapping[str, Any] | None = None,
    include_answers: Mapping[str, Any] | None = None,
    skipped: str | None = None,
) -> RemainingDecision:
    """Yield or skip is the place_wall choice. Occupancy integers stay facts on the state."""
    if not challenge_remaining_on(login=login, ns=ns):
        return RemainingDecision(action="integer_path", reason="not_challenge_integer_path")
    occ = dict(occupancy or {})
    state = assemble_remaining_state(
        subgoal=SUBGOAL_PLACE_WALL,
        sleeve=sleeve,
        symbol=symbol,
        side=side,
        as_of_utc=as_of_utc,
        decision_day=decision_day,
        ticket=ticket,
        cluster=cluster,
        ns=ns,
        occupancy={**occ, "wall": wall},
        news=news,
    )
    fan = fanout_remaining(
        state,
        subgoal=SUBGOAL_PLACE_WALL,
        evaluate_jev=evaluate_jev,
        include_answers=include_answers,
        decision_answers=answers,
        skipped=skipped,
    )
    return _from_choice(state, fan, "place_wall", _PLACE_ORDER)


def decide_restart_chase(
    *,
    tape: Mapping[str, Any] | None = None,
    occupancy: Mapping[str, Any] | None = None,
    sleeve: Any = None,
    symbol: Any = None,
    side: Any = None,
    as_of_utc: Any = None,
    decision_day: Any = None,
    ticket: Any = None,
    login: Any = None,
    ns: Any = None,
    evaluate_jev: bool = True,
    answers: Mapping[str, Any] | None = None,
    include_answers: Mapping[str, Any] | None = None,
    skipped: str | None = None,
) -> RemainingDecision:
    """Skip, shadow, or send is the restart_chase choice. The caller owns a send."""
    if not challenge_remaining_on(login=login, ns=ns):
        return RemainingDecision(action="integer_path", reason="not_challenge_integer_path")
    state = assemble_remaining_state(
        subgoal=SUBGOAL_RESTART,
        sleeve=sleeve,
        symbol=symbol,
        side=side,
        as_of_utc=as_of_utc,
        decision_day=decision_day,
        ticket=ticket,
        ns=ns,
        tape=tape,
        occupancy=occupancy,
    )
    fan = fanout_remaining(
        state,
        subgoal=SUBGOAL_RESTART,
        evaluate_jev=evaluate_jev,
        include_answers=include_answers,
        decision_answers=answers,
        skipped=skipped,
    )
    return _from_choice(state, fan, "restart_chase", _RESTART_ORDER, write_on="send")


def decide_remint(
    *,
    remint: Mapping[str, Any] | None = None,
    occupancy: Mapping[str, Any] | None = None,
    sleeve: Any = None,
    symbol: Any = None,
    ticket: Any = None,
    as_of_utc: Any = None,
    login: Any = None,
    ns: Any = None,
    evaluate_jev: bool = True,
    answers: Mapping[str, Any] | None = None,
    include_answers: Mapping[str, Any] | None = None,
    skipped: str | None = None,
) -> RemainingDecision:
    """Refuse, leave_orig, or authorize is the remint_authorize choice. This module does not mint."""
    if not challenge_remaining_on(login=login, ns=ns):
        return RemainingDecision(action="integer_path", reason="not_challenge_integer_path")
    state = assemble_remaining_state(
        subgoal=SUBGOAL_REMINT,
        sleeve=sleeve,
        symbol=symbol,
        ticket=ticket,
        as_of_utc=as_of_utc,
        ns=ns,
        remint=remint,
        occupancy=occupancy,
    )
    fan = fanout_remaining(
        state,
        subgoal=SUBGOAL_REMINT,
        evaluate_jev=evaluate_jev,
        include_answers=include_answers,
        decision_answers=answers,
        skipped=skipped,
    )
    return _from_choice(state, fan, "remint_authorize", _REMINT_ORDER, write_on="authorize")


def remint_cli_allows(
    *,
    namespace: Any = None,
    profile: Any = None,
    login: Any = None,
    evaluate_jev: bool = True,
    answers: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> tuple[bool | None, str]:
    """Wrap ``cmd_mint``. W7 profiles pass. Only an authorize choice allows a Challenge mint."""
    if not remint_env_on(environ=environ):
        return True, "GTOS_JEV_REMINT_off"
    ns = namespace
    if ns in (None, "") and str(profile or "").strip() == CHALLENGE_NS:
        ns = CHALLENGE_NS
    if not challenge_remaining_on(login=login, ns=ns, environ=environ):
        return True, "not_challenge_integer_path"
    decision = decide_remint(
        remint={
            "command": "activation_token_mint",
            "proposed_modify_tp": False,
            "live_broker_authority": False,
            "profile": profile,
            "namespace": ns,
        },
        ns=ns,
        login=login,
        evaluate_jev=evaluate_jev,
        answers=answers,
    )
    if decision.action == "authorize":
        return True, decision.reason
    if decision.action == "jev_no_decision":
        return None, decision.skipped or "jev_no_decision"
    return False, decision.reason


def decide_sleeve_emit(
    *,
    a8: Mapping[str, Any] | None = None,
    tape: Mapping[str, Any] | None = None,
    sleeve: Any = None,
    symbol: Any = None,
    side: Any = None,
    as_of_utc: Any = None,
    decision_day: Any = None,
    login: Any = None,
    ns: Any = None,
    evaluate_jev: bool = True,
    answers: Mapping[str, Any] | None = None,
    include_answers: Mapping[str, Any] | None = None,
    skipped: str | None = None,
) -> RemainingDecision:
    """Emit, hold, or drop is the sleeve_emit choice. A missing choice stays unset."""
    if not challenge_remaining_on(login=login, ns=ns):
        return RemainingDecision(action="integer_path", reason="not_challenge_integer_path")
    feats = dict(a8 or {})
    state = assemble_remaining_state(
        subgoal=SUBGOAL_SLEEVE,
        sleeve=sleeve,
        symbol=symbol,
        side=side,
        as_of_utc=as_of_utc,
        decision_day=decision_day,
        ns=ns,
        a8=feats,
        tape=tape,
    )
    fan = fanout_remaining(
        state,
        subgoal=SUBGOAL_SLEEVE,
        evaluate_jev=evaluate_jev,
        include_answers=include_answers,
        decision_answers=answers,
        skipped=skipped,
    )
    return _from_choice(state, fan, "sleeve_emit", _SLEEVE_ORDER)


def challenge_sleeve_may_emit(
    *,
    sleeve: str,
    ac60: float | None,
    symbol: Any = None,
    side: Any = None,
    decision_day: Any = None,
    a8_k_of_4_pass: Any = None,
    feats: Mapping[str, Any] | None = None,
    answers: Mapping[str, Any] | None = None,
    include_answers: Mapping[str, Any] | None = None,
    evaluate_jev: bool = True,
) -> bool | None:
    """None → integer cliff. True/False → Jev named emit/drop-or-hold."""
    if not challenge_remaining_on():
        return None
    a8 = dict(feats or {})
    a8["ac60"] = ac60
    a8["a8_k_of_4_pass"] = a8_k_of_4_pass
    a8["sleeve"] = sleeve
    decision = decide_sleeve_emit(
        a8=a8,
        sleeve=sleeve,
        symbol=symbol,
        side=side,
        decision_day=decision_day,
        evaluate_jev=evaluate_jev,
        answers=answers,
        include_answers=include_answers,
    )
    if decision.action == "emit":
        return True
    if decision.action in {"hold", "drop"}:
        return False
    return None


def a8_may_keep_failed_k(
    intent: Any,
    *,
    answers: Mapping[str, Any] | None = None,
    include_answers: Mapping[str, Any] | None = None,
    evaluate_jev: bool = True,
) -> bool | None:
    """Keep or release is the a8_keep choice. A missing choice stays unset."""
    if not challenge_remaining_on():
        return None
    sleeve = str(getattr(intent, "sleeve", "") or "")
    feats = {
        "ac60": getattr(intent, "ac60", None),
        "htf_slope_norm": getattr(intent, "htf_slope_norm", None),
        "mom_20_atr": getattr(intent, "mom_20_atr", None),
        "fvg_freshness_bars": getattr(intent, "fvg_freshness_bars", None),
        "atr_ratio": getattr(intent, "atr_ratio", None),
        "session_hour": getattr(intent, "session_hour", None),
        "a8_k_of_4_pass": False,
        "k_pass": False,
        "sleeve": sleeve,
        "source": "intent",
    }
    decision = decide_sleeve_emit(
        a8=feats,
        sleeve=sleeve,
        symbol=getattr(intent, "symbol", None),
        side="long" if int(getattr(intent, "direction", 1) or 1) > 0 else "short",
        decision_day=getattr(intent, "decision_day", None),
        evaluate_jev=evaluate_jev,
        answers=answers,
        include_answers=include_answers,
    )
    if decision.action == "jev_no_decision" and decision.skipped != "sleeve_emit_unset":
        return None
    choice = _choice_at(decision.answers, "a8_keep", _A8_KEEP_ORDER)
    if choice == "keep":
        return True
    if choice == "release":
        return False
    return None


def wall_occupancy_from_owner(
    owner: Any,
    intent: Any,
    *,
    wall: str,
    as_of: datetime | None = None,
    account_state: Any = None,
    decision: Any = None,
    dday: Any = None,
    cluster: Any = None,
) -> dict[str, Any]:
    """Read-only occupancy for a place wall. Keep-one is the broker integer."""
    occ: dict[str, Any] = {
        "already_placed_today": wall == "already_placed_today",
        "cluster_placed_today": wall == "cluster_later_bar",
        "wall": wall,
        "decision_day": str(dday or "")[:10] or None,
        "cluster": cluster,
        "occupancy_source": "place_wall",
    }
    symbol = getattr(intent, "symbol", None)
    sleeve = getattr(intent, "sleeve", None)
    try:
        occ["symbol_open"] = bool(owner._broker_holds(symbol, sleeve))
    except Exception:
        occ["symbol_open"] = None
    try:
        from .host_occupancy import host_occupancy_governor

        pack = host_occupancy_governor(
            symbol=symbol,
            as_of=as_of or datetime.now(timezone.utc),
            sleeve=sleeve,
            account_state=account_state,
            decision=decision,
            namespace=getattr(owner, "_namespace", None),
        )
        live = pack.get("occupancy") if isinstance(pack, dict) else None
        if isinstance(live, dict):
            for key in (
                "isolated_reentry_legal",
                "minutes_since_flat",
                "symbol_open",
                "already_placed_today",
                "cluster_placed_today",
                "keep_one_symbol",
            ):
                if live.get(key) is not None:
                    occ[key] = live.get(key)
            occ["occupancy_source"] = live.get("occupancy_source") or "host_tape"
    except Exception:
        pass
    return occ


def write_remaining_print(row: Mapping[str, Any]) -> None:
    override = (os.environ.get("GTOS_JEV_REMAINING_PRINT") or "").strip()
    path = Path(override) if override else DEFAULT_PRINT
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(dict(row), default=str) + "\n")
    except Exception:
        return
