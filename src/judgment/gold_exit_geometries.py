"""Geometry-bound gold exits — one System One ask.

Challenge **0** / ``operator`` / magic **0**.

This pack enumerates every way an open XAU ticket can leave. It is **not**
PR #67 ``size_exit.py``. One hop is ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False`` (POST
https://api.typesafe.ai/v1/systemone). The return is a Noul, a Choice, or
a Score. Each write, label, and parameter is that return. A Score may sit
between levels. Prior outcomes are attached on the ask, and the return is
appended for the next ask.

An empty answer, a tie, a missing score, or an error leaves that field
unset and does not restore a constant. A dollar line is not a question.
This module does not send an order and does not flatten the book.

Digest, stop count, named surface, prop wall, weekend flag, and operator
flag stay facts when they are on the card. The write is the return.

Founder shape (TypeSafe memo, Appendix 3): one completeness Noul on *this*
open object; the include-depth Score on that same ask; nested labels +
subtree dump. Not linear keep/drop of the catalog. Do not Noul every tick.
Do not compact the Challenge session. Do not invent ``NEWS_PROTOCOL`` rows.

The close-label is a question on this same ask. It does not authorize a write.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS

SCHEMA = "gtos.judgment.gold_exit_geometries.v0"
STEAL = "GOLD_EXIT"
MODEL = "jev-1.13.0"
LEAVE_ORIG = "leave_orig"
INCLUDE_DEPTH = ("hide", "short", "long", "full")
OVERLAY_ENV = "GTOS_JEV_GOLD_EXIT"

GEOMETRIES: tuple[str, ...] = (
    "target",
    "stop",
    "time_stop",
    "trail",
    "scale",
    "opposite_displacement",
    "session_death",
    "news",
)

WRITE_KEYS: tuple[str, ...] = (
    "take_target",
    "time_stop",
    "move_sl",
    "scale_out",
    "opposite_displacement",
    "session_death",
    "news_exit",
)

EXIT_CLASS_CRITERIA = {
    "orig_stop": "Broker original stop fill on this ticket.",
    "broker_tp": "Broker target fill on this ticket.",
    "time_stop": "Writer horizon close on this ticket.",
    "breach_flatten": "Governor flatten named on this ticket. An operator flag is a different fact.",
    "other": "Unassembled close label.",
}

# Directional snippets so the model knows an action *could* exist without
# dumping the full schema (founder two-layer catalog).
SNIPPETS: dict[str, str] = {
    "target": "Broker TP or a named take-target write before TP.",
    "stop": "Broker original stop on this open ticket.",
    "time_stop": "Writer horizon close of this open ticket.",
    "trail": "Stop modify on this open ticket.",
    "scale": "Partial volume cut (TP1/TP2 / partial_be_runner).",
    "opposite_displacement": "Thesis displacement reversed against identity.side.",
    "session_death": "Named session died on an open ticket (not the entry clock hold).",
    "news": "Named HIGH on an occupied ticket.",
    "exit_state_sufficient": "One completeness Noul on this open object.",
    "exit_class": "Close label after the exit exists.",
    "take_target": "Named take-target write, or leave_orig (broker TP stays).",
    "honor_orig_stop": "Orig stop still the thesis stop. Broker-side.",
    "move_sl": "BE / trail SL modify, or leave_orig.",
    "scale_out": "Named partial, or leave_orig.",
    "news_exit": "Named HIGH flatten of this ticket, or leave_orig.",
    "event_proximity": "Named HIGH on this as-of?",
    "geometry_vs_tape": "Does this open stop/target still fit named tape?",
    "include_depth": "How deep this open object's schema is included.",
    "exit_threshold": "Threshold on this open gold exit.",
    "take_target_parameter": "Parameter of the take-target write.",
    "time_stop_parameter": "Parameter of the time-stop write.",
    "move_sl_parameter": "Parameter of the stop modify.",
    "scale_out_parameter": "Parameter of the partial.",
    "opposite_displacement_parameter": "Parameter of the opposite-displacement write.",
    "session_death_parameter": "Parameter of the session-death write.",
    "news_exit_parameter": "Parameter of the news write.",
}


def _choice_block(instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    return {
        "type": "choice",
        "instructions": instructions,
        "criteria": dict(criteria),
    }


def _noul_block(instructions: str, *, true: str, false: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {"true": true, "false": false},
    }


def _score_block(instructions: str, levels: list[str]) -> dict[str, Any]:
    return {
        "type": "score",
        "instructions": instructions,
        "criteria": list(levels),
    }


LEAVE_ORIG_CRITERIA = {
    LEAVE_ORIG: (
        "Original broker protection, size, and occupancy. "
        "This option counts only when it is the unique highest probability."
    ),
}

GOLD_EXIT_QUESTIONS: dict[str, dict[str, Any]] = {
    "exit_state_sufficient": _noul_block(
        (
            "Is this OPEN gold object complete enough to name a write as-of "
            "clock.as_of_utc? Need identity.side, geometry.stop, geometry.target "
            "or orig_sl/orig_tp, occupancy, sessions.named. Nulls stay null. "
            "The noul you return is that completeness. An empty noul leaves it unset. "
            "This question does not send."
        ),
        true="Named open object is complete enough to judge a write",
        false="Assemble / escalate — other answers are not a fire",
    ),
    "exit_class": _choice_block(
        (
            "Name the live write class on this open ticket. "
            "The option with the single highest probability is the label. "
            "An empty answer or a tie leaves the label unset. "
            "This question does not send."
        ),
        EXIT_CLASS_CRITERIA,
    ),
    "take_target": _choice_block(
        (
            "Should the writer close toward the named target before broker TP fills? "
            "leave_orig keeps the broker TP when that option is the unique highest. "
            "The parameter is the score on take_target_parameter. "
            "An empty answer or a tie leaves the choice unset. This question does not send."
        ),
        {
            **LEAVE_ORIG_CRITERIA,
            "take_target": "Writer prints a full close as a named take-target.",
        },
    ),
    "honor_orig_stop": _noul_block(
        (
            "Is the named orig stop still the thesis stop on this card? "
            "A widen is the never_widen noul on this same ask. A pull is move_sl. "
            "The noul you return is that match. An empty noul leaves it unset. "
            "This question does not send."
        ),
        true="Named orig stop still matches the thesis stop",
        false="The named orig stop does not match the thesis stop",
    ),
    "time_stop": _choice_block(
        (
            "Should the writer time-stop this open gold ticket? "
            "Naming time_stop is that close when the option is the unique highest. "
            "The parameter is the score on time_stop_parameter. "
            "An empty answer or a tie leaves the choice unset. This question does not send."
        ),
        {
            **LEAVE_ORIG_CRITERIA,
            "time_stop": "Close now as time_stop. Writer prints the close.",
        },
    ),
    "move_sl": _choice_block(
        (
            "Should the writer move the stop on this open gold ticket? "
            "The stop parameter is the score on move_sl_parameter. "
            "The option with the single highest probability is the decision. "
            "An empty answer or a tie leaves it unset. This question does not send."
        ),
        {
            **LEAVE_ORIG_CRITERIA,
            "move_be": "Move SL to break-even. Writer prints the SL modify.",
            "trail": "Trail the stop. Writer prints the SL modify.",
        },
    ),
    "scale_out": _choice_block(
        (
            "Should the writer scale out of this open gold ticket? "
            "The fraction is the score on scale_out_parameter. "
            "The option with the single highest probability is the decision. "
            "An empty answer or a tie leaves it unset. This question does not send."
        ),
        {
            **LEAVE_ORIG_CRITERIA,
            "scale_out": "Take the named partial. Writer prints the volume cut.",
        },
    ),
    "opposite_displacement": _choice_block(
        (
            "Did named displacement reverse against identity.side on this open ticket? "
            "The facts on the card are the displacement. "
            "The parameter is the score on opposite_displacement_parameter. "
            "The option with the single highest probability is the decision. "
            "An empty answer or a tie leaves it unset. This question does not send."
        ),
        {
            **LEAVE_ORIG_CRITERIA,
            "flatten_opposite": (
                "Named opposite displacement. Writer prints flatten of THIS ticket."
            ),
        },
    ),
    "session_death": _choice_block(
        (
            "Did the named session die on this occupied gold ticket? "
            "Clock facts on the card stay facts. "
            "The parameter is the score on session_death_parameter. "
            "The option with the single highest probability is the decision. "
            "An empty answer or a tie leaves it unset. This question does not send."
        ),
        {
            **LEAVE_ORIG_CRITERIA,
            "flatten_session": "Named session-death flatten of THIS ticket.",
        },
    ),
    "news_exit": _choice_block(
        (
            "Should the writer name flatten_news for a named HIGH on this occupied ticket? "
            "The news facts on the card are the minutes and the events. "
            "An empty spine is a fact, not a filled answer. "
            "The parameter is the score on news_exit_parameter. "
            "The option with the single highest probability is the decision. "
            "An empty answer or a tie leaves it unset. This question does not send."
        ),
        {
            **LEAVE_ORIG_CRITERIA,
            "flatten_news": "Named HIGH flatten of THIS ticket. Writer prints.",
        },
    ),
    "event_proximity": _noul_block(
        (
            "Is a named HIGH in news.events on this as-of? "
            "The minutes on the card are a fact. An empty spine still gets this question. "
            "The noul you return is that proximity. An empty noul leaves it unset. "
            "This question does not send."
        ),
        true="A named HIGH is on this as-of",
        false="No named HIGH is on this as-of",
    ),
    "geometry_vs_tape": _score_block(
        (
            "The score you return is whether this open stop and target still fit the named tape. "
            "It may sit between the levels. An empty score leaves it unset. "
            "This question does not send."
        ),
        [
            "Named vol/tape will not pay the plan_r (hi/xhi missing displacement)",
            "Ordinary",
            "Stop/target fit named quiet tape",
        ],
    ),
    "include_depth": _score_block(
        (
            "The score you return is how deep this open gold object's schema is included. "
            "It may sit between the levels. An empty score leaves the depth unset. "
            "This question does not send."
        ),
        ["hide", "short", "long", "full"],
    ),
    "exit_threshold": _score_block(
        (
            "The score you return is the threshold on this open gold exit. "
            "It may sit between the levels. An empty score leaves the threshold unset. "
            "This question does not send."
        ),
        ["none", "trace", "small", "modest", "notable", "heavy"],
    ),
    "take_target_parameter": _score_block(
        (
            "The score you return is the parameter of take_target on this open gold ticket. "
            "It may sit between the levels. An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        ["none", "trace", "small", "modest", "notable", "heavy"],
    ),
    "time_stop_parameter": _score_block(
        (
            "The score you return is the parameter of time_stop on this open gold ticket. "
            "It may sit between the levels. An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        ["none", "trace", "small", "modest", "notable", "heavy"],
    ),
    "move_sl_parameter": _score_block(
        (
            "The score you return is the parameter of move_sl on this open gold ticket. "
            "It may sit between the levels. An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        ["none", "trace", "small", "modest", "notable", "heavy"],
    ),
    "scale_out_parameter": _score_block(
        (
            "The score you return is the parameter of scale_out on this open gold ticket. "
            "It may sit between the levels. An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        ["none", "trace", "small", "modest", "notable", "heavy"],
    ),
    "opposite_displacement_parameter": _score_block(
        (
            "The score you return is the parameter of opposite_displacement on this open gold ticket. "
            "It may sit between the levels. An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        ["none", "trace", "small", "modest", "notable", "heavy"],
    ),
    "session_death_parameter": _score_block(
        (
            "The score you return is the parameter of session_death on this open gold ticket. "
            "It may sit between the levels. An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        ["none", "trace", "small", "modest", "notable", "heavy"],
    ),
    "news_exit_parameter": _score_block(
        (
            "The score you return is the parameter of news_exit on this open gold ticket. "
            "It may sit between the levels. An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        ["none", "trace", "small", "modest", "notable", "heavy"],
    ),
    "broker_effect": _noul_block(
        (
            "Is a broker effect open on this gold exit? "
            "The noul you return is that answer. An empty noul leaves it unset. "
            "This question does not send."
        ),
        true="A broker effect is open on this state.",
        false="A broker effect is not open on this state.",
    ),
    "never_widen": _noul_block(
        (
            "Is a widen of this stop closed on this state? "
            "The noul you return is that answer. An empty noul leaves it unset. "
            "This question does not send."
        ),
        true="A widen is closed on this state.",
        false="A widen is not closed on this state.",
    ),
}

# Nested seats. Code picks a node, then dumps that schema.
GOLD_EXIT_TREE: dict[str, Any] = {
    "object": {
        "ids": (
            "exit_state_sufficient",
            "geometry_vs_tape",
            "include_depth",
            "exit_threshold",
            "broker_effect",
            "never_widen",
        )
    },
    "label": {"ids": ("exit_class",)},
    "writes": {
        "target": {"ids": ("take_target", "take_target_parameter")},
        "stop": {"ids": ("honor_orig_stop",)},
        "time_stop": {"ids": ("time_stop", "time_stop_parameter")},
        "trail": {"ids": ("move_sl", "move_sl_parameter")},
        "scale": {"ids": ("scale_out", "scale_out_parameter")},
        "opposite_displacement": {
            "ids": ("opposite_displacement", "opposite_displacement_parameter")
        },
        "session_death": {"ids": ("session_death", "session_death_parameter")},
        "news": {"ids": ("news_exit", "event_proximity", "news_exit_parameter")},
    },
}

# Facts stay on the card. Nothing here skips an ask.
QUESTION_IGNORE_IF: dict[str, str] = {}


def overlay_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """The env token is a fact. It does not skip the ask."""

    del environ
    return True


def gold_exit_labels(
    *,
    symbol: Any = "XAUUSD",
    sleeve: Any = None,
    side: Any = None,
    ticket: Any = None,
    as_of: Any = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Nested labels so later tree-search can find this object. Not a transcript."""
    labels = {
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "symbol": symbol,
        "sleeve": sleeve,
        "side": side,
        "ticket": ticket,
        "as_of": as_of,
        "subgoal": "gold_exit",
    }
    if extra:
        labels.update(dict(extra))
    return labels


def _ids_under(node: Any) -> tuple[str, ...]:
    if isinstance(node, dict):
        if "ids" in node:
            return tuple(str(x) for x in node["ids"])
        out: list[str] = []
        seen: set[str] = set()
        for child in node.values():
            for qid in _ids_under(child):
                if qid not in seen:
                    seen.add(qid)
                    out.append(qid)
        return tuple(out)
    return ()


def dump_gold_exit_subtree(*path: str, depth: str = "full") -> dict[str, dict[str, Any]]:
    """Hierarchical schema dump. ``path`` walks GOLD_EXIT_TREE. Not keep/drop.

    ``depth`` is the schema view the caller named. The live include depth is
    the score returned on ``include_depth``.
    """
    if depth not in INCLUDE_DEPTH:
        raise ValueError(f"include_depth must be one of {INCLUDE_DEPTH}, got {depth!r}")
    if depth == "hide":
        return {}
    node: Any = GOLD_EXIT_TREE
    for part in path:
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"unknown gold-exit subtree {path!r}")
        node = node[part]
    ids = _ids_under(node)
    if not path:
        ids = _ids_under(GOLD_EXIT_TREE)
    if depth == "short":
        return {qid: {"type": GOLD_EXIT_QUESTIONS[qid]["type"], "snippet": SNIPPETS.get(qid) or GOLD_EXIT_QUESTIONS[qid]["instructions"][:80]} for qid in ids}
    if depth == "long":
        return {
            qid: {
                "type": GOLD_EXIT_QUESTIONS[qid]["type"],
                "instructions": GOLD_EXIT_QUESTIONS[qid]["instructions"],
            }
            for qid in ids
        }
    return {qid: dict(GOLD_EXIT_QUESTIONS[qid]) for qid in ids}


def gold_exit_live_pack(*, include_depth: str = "full") -> dict[str, dict[str, Any]]:
    """One live manage dump: object + writes. Label pack is the second object."""
    if include_depth == "hide":
        return {}
    packed: dict[str, dict[str, Any]] = {}
    packed.update(dump_gold_exit_subtree("object", depth=include_depth))
    packed.update(dump_gold_exit_subtree("writes", depth=include_depth))
    return packed


def gold_exit_label_pack(*, include_depth: str = "full") -> dict[str, dict[str, Any]]:
    return dump_gold_exit_subtree("label", depth=include_depth)


def gold_exit_state(
    *,
    symbol: Any = "XAUUSD",
    sleeve: Any = None,
    side: Any = None,
    ticket: Any = None,
    occupancy: Mapping[str, Any] | None = None,
    geometry: Mapping[str, Any] | None = None,
    sessions: Mapping[str, Any] | None = None,
    news: Mapping[str, Any] | None = None,
    record: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Explicit open-ticket state. Nulls stay null. No invented news."""
    trade: dict[str, Any] = {}
    if isinstance(record, Mapping):
        for key in (
            "ticket",
            "symbol",
            "sleeve",
            "side",
            "entry_price",
            "stop_loss",
            "take_profit",
            "orig_sl",
            "orig_tp",
            "fav_r",
            "bars_held",
        ):
            if record.get(key) is not None:
                trade[key] = record.get(key)
    news_obj = dict(news) if isinstance(news, Mapping) else {"events": []}
    state = {
        "schema": SCHEMA,
        "identity": {
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "magic": CHALLENGE_MAGIC,
            "symbol": symbol,
            "sleeve": sleeve,
            "side": side,
            "ticket": ticket,
        },
        "occupancy": dict(occupancy or {}),
        "geometry": dict(geometry or {}),
        "sessions": dict(sessions or {}),
        "news": news_obj,
        "trade": trade,
        "geometries": list(GEOMETRIES),
    }
    state["labels"] = gold_exit_labels(
        symbol=symbol,
        sleeve=sleeve,
        side=side,
        ticket=ticket,
        extra={"subgoal": "gold_exit"},
    )
    if extra:
        state["extra"] = dict(extra)
    return state


CHOICE_IDS: tuple[str, ...] = tuple(
    qid for qid, block in GOLD_EXIT_QUESTIONS.items() if block.get("type") == "choice"
)
NOUL_IDS: tuple[str, ...] = tuple(
    qid for qid, block in GOLD_EXIT_QUESTIONS.items() if block.get("type") == "noul"
)
SCORE_IDS: tuple[str, ...] = tuple(
    qid for qid, block in GOLD_EXIT_QUESTIONS.items() if block.get("type") == "score"
)

_LIMIT_PARTS = ("floor", "baseline")
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
# History only when jev_questions cannot be imported. A miss is not copied back.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


def _limit_key(name: str) -> bool:
    low = str(name).lower()
    return any(part in low for part in _LIMIT_PARTS)


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    for word in ("floor", "baseline", "Floor", "Baseline", "FLOOR", "BASELINE"):
        cleaned = cleaned.replace(word, "")
    return " ".join(cleaned.split())


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)):
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


def _criteria_order(qid: str) -> tuple[str, ...]:
    block = GOLD_EXIT_QUESTIONS.get(qid) or {}
    criteria = block.get("criteria")
    if isinstance(criteria, Mapping):
        return tuple(str(name) for name in criteria if not _limit_key(str(name)))
    return ()


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _finite(val)
        if number is None:
            continue
        numeric[name] = number
    return numeric


def _local_unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest among probabilities that were returned. A tie is unset."""

    best: str | None = None
    best_p: float | None = None
    tied = False
    for name in order:
        if name not in numeric:
            continue
        prob = numeric[name]
        if best_p is None or prob > best_p + 1e-12:
            best = name
            best_p = prob
            tied = False
        elif abs(prob - best_p) <= 1e-12:
            tied = True
    if tied or best is None:
        return None
    return best


def _choice(answers: Mapping[str, Any] | None, key: str) -> str | None:
    """Unique highest probability. A bare label, a tie, or an empty block is unset."""

    if not isinstance(answers, Mapping):
        return None
    order = _criteria_order(key)
    if not order:
        return None
    numeric = _probabilities(answers.get(key), order)
    if not numeric:
        return None
    local = _local_unique(numeric, order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(numeric, order)
    except Exception:
        picked = local
    if picked is None or local is None or str(picked) != local or str(picked) not in order:
        return None
    return str(picked)


def _noul_value(block: Any) -> bool | float | None:
    """A Noul stays a bool or a probability. Missing stays missing."""

    if not isinstance(block, dict) or "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _finite(raw)


def _score_value(block: Any) -> float | None:
    """The returned score. It may sit between levels. Missing stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    parsed: float | None = None
    try:
        from .jev_questions import returned_number

        parsed = _finite(returned_number(block))
    except Exception:
        parsed = None
    if parsed is not None:
        return parsed
    for key in ("score", "value"):
        if key in block:
            parsed = _finite(block.get(key))
            if parsed is not None:
                return parsed
    return None


def _ask_pack() -> dict[str, dict[str, Any]]:
    """One hierarchical pack. Types stay Noul, Choice, or Score."""

    pack: dict[str, dict[str, Any]] = {}
    for qid, block in GOLD_EXIT_QUESTIONS.items():
        kind = str(block.get("type") or "")
        if kind not in {"noul", "choice", "score"}:
            continue
        instructions = _scrub_text(str(block.get("instructions") or ""))
        criteria = block.get("criteria")
        row: dict[str, Any] | None = None
        try:
            if kind == "choice" and isinstance(criteria, Mapping):
                from .jev_questions import spot_question

                built = spot_question(
                    qid,
                    instructions,
                    {str(key): str(text) for key, text in criteria.items() if not _limit_key(str(key))},
                )
                got = built.get(qid) if isinstance(built, dict) else None
                if isinstance(got, dict):
                    row = dict(got)
            elif kind == "score" and qid != "geometry_vs_tape":
                from .jev_questions import parameter_question

                built = parameter_question(qid, instructions)
                got = built.get(qid) if isinstance(built, dict) else None
                if isinstance(got, dict):
                    row = dict(got)
        except Exception:
            row = None
        if row is None:
            row = {"type": kind, "instructions": instructions}
            if isinstance(criteria, Mapping):
                row["criteria"] = {
                    str(key): _scrub_text(str(text))
                    for key, text in criteria.items()
                    if not _limit_key(str(key))
                }
            elif isinstance(criteria, list):
                row["criteria"] = [str(item) for item in criteria if not _limit_key(str(item))]
        row["type"] = kind
        row["instructions"] = instructions
        if kind == "choice" and isinstance(criteria, Mapping):
            row["criteria"] = {
                str(key): _scrub_text(str(text))
                for key, text in criteria.items()
                if not _limit_key(str(key))
            }
        elif kind == "noul" and isinstance(criteria, Mapping):
            row["criteria"] = {
                str(key): _scrub_text(str(text)) for key, text in criteria.items()
            }
        elif kind == "score":
            levels = row.get("criteria")
            if isinstance(levels, list):
                kept = [_scrub_text(str(item)) for item in levels if not _limit_key(str(item))]
                kept = [item for item in kept if item]
                if kept:
                    row["criteria"] = kept
                else:
                    row.pop("criteria", None)
            elif qid == "geometry_vs_tape" and isinstance(criteria, list):
                row["criteria"] = [str(item) for item in criteria if not _limit_key(str(item))]
        pack[qid] = row
    return pack


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _remember(state: Mapping[str, Any], qid: str, value: Any, error: str | None) -> None:
    """The return just asked is history for the next ask. A miss stays a miss."""

    try:
        from .jev_questions import append_outcome

        append_outcome(qid, value, state, error=error)
    except Exception:
        _LOCAL_OUTCOMES.append({"key": qid, "value": value, "error": error})


def _evaluate_gold_exit(
    state: Mapping[str, Any],
    ask: Callable[..., Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """One System One post. Empty and error leave the answers unset."""

    questions = _ask_pack()
    asked = _scrub(dict(state))
    if not isinstance(asked, dict):
        asked = {}
    asked.pop("prior_outcomes", None)
    asked["model"] = MODEL
    if "labels" not in asked:
        try:
            from .jev_questions import hierarchical_labels

            asked["labels"] = hierarchical_labels(asked, extra={"subgoal": "gold_exit"})
        except Exception:
            asked["labels"] = gold_exit_labels()
    _attach_priors(asked, questions)
    call = ask
    if call is None:
        try:
            from .jev_client import evaluate
        except Exception:
            return {}, {"ok": False, "error": "import_failed", "model": MODEL, "answers": {}}
        call = evaluate
    try:
        receipt = call(asked, questions=questions, merge_sleeve=False, model=MODEL)
    except Exception as exc:  # noqa: BLE001 — a dark ask must not raise into the writer
        return {}, {"ok": False, "error": type(exc).__name__, "model": MODEL, "answers": {}}
    if not isinstance(receipt, dict):
        return {}, {"ok": False, "error": "evaluate_not_a_dict", "model": MODEL, "answers": {}}
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or not answers:
        err = receipt.get("error") or receipt.get("skipped") or "empty"
        return {}, {**receipt, "ok": False, "error": str(err), "model": receipt.get("model") or MODEL, "answers": {}}
    return answers, receipt


def _parsed(answers: Mapping[str, Any]) -> tuple[dict[str, str | None], dict[str, bool | float | None], dict[str, float | None]]:
    choices = {qid: _choice(answers, qid) for qid in CHOICE_IDS}
    nouls = {qid: _noul_value(answers.get(qid)) for qid in NOUL_IDS}
    scores = {qid: _score_value(answers.get(qid)) for qid in SCORE_IDS}
    return choices, nouls, scores


def _remember_parsed(
    state: Mapping[str, Any],
    choices: Mapping[str, Any],
    nouls: Mapping[str, Any],
    scores: Mapping[str, Any],
    error: str | None,
) -> None:
    pairs: list[tuple[str, Any]] = []
    pairs.extend(choices.items())
    pairs.extend(nouls.items())
    pairs.extend(scores.items())
    for qid, value in pairs:
        miss = None
        if value is None:
            if qid in SCORE_IDS:
                miss = error or "score_missing"
            elif qid in NOUL_IDS:
                miss = error or "noul_missing"
            else:
                miss = error or "tie_or_empty"
        _remember(state, qid, value, miss)


@dataclass(frozen=True)
class GoldExitDecision:
    take_target: str | None = None
    time_stop: str | None = None
    move_sl: str | None = None
    scale_out: str | None = None
    opposite_displacement: str | None = None
    session_death: str | None = None
    news_exit: str | None = None
    exit_class: str | None = None
    sufficient: bool | float | None = None
    honor_orig_stop: bool | float | None = None
    event_proximity: bool | float | None = None
    geometry_vs_tape: float | None = None
    include_depth: float | None = None
    threshold: float | None = None
    broker_effect: bool | float | None = None
    never_widen: bool | float | None = None
    source: str = "unset"
    skipped: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def named_any(self) -> bool:
        return any((
            self.take_target == "take_target",
            self.time_stop == "time_stop",
            self.move_sl in {"move_be", "trail"},
            self.scale_out == "scale_out",
            self.opposite_displacement == "flatten_opposite",
            self.session_death == "flatten_session",
            self.news_exit == "flatten_news",
        ))

    @property
    def allow_time_stop(self) -> bool:
        return self.time_stop == "time_stop"

    @property
    def allow_take_target(self) -> bool:
        return self.take_target == "take_target"

    @property
    def allow_scale_out(self) -> bool:
        return self.scale_out == "scale_out"

    @property
    def allow_trail(self) -> bool:
        return self.move_sl in {"trail", "move_be"}

    @property
    def allow_flatten_named(self) -> bool:
        return any(
            v in {"flatten_opposite", "flatten_session", "flatten_news"}
            for v in (
                self.opposite_displacement,
                self.session_death,
                self.news_exit,
            )
        )

    def as_allow(self) -> dict[str, bool]:
        """True only when that Choice authorizes the act. A miss is not an allow."""
        return {
            "take_target": self.allow_take_target,
            "time_stop": self.allow_time_stop,
            "move_be": self.move_sl == "move_be",
            "trail": self.move_sl == "trail",
            "scale_out": self.allow_scale_out,
            "flatten_opposite": self.opposite_displacement == "flatten_opposite",
            "flatten_session": self.session_death == "flatten_session",
            "flatten_news": self.news_exit == "flatten_news",
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "steal": STEAL,
            "model": MODEL,
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "take_target": self.take_target,
            "time_stop": self.time_stop,
            "move_sl": self.move_sl,
            "scale_out": self.scale_out,
            "opposite_displacement": self.opposite_displacement,
            "session_death": self.session_death,
            "news_exit": self.news_exit,
            "exit_class": self.exit_class,
            "sufficient": self.sufficient,
            "honor_orig_stop": self.honor_orig_stop,
            "event_proximity": self.event_proximity,
            "geometry_vs_tape": self.geometry_vs_tape,
            "include_depth": self.include_depth,
            "threshold": self.threshold,
            "broker_effect": self.broker_effect,
            "never_widen": self.never_widen,
            "parameters": dict(self.parameters),
            "named_any": self.named_any,
            "source": self.source,
            "skipped": self.skipped,
            "allow": self.as_allow(),
        }


def _decision_from_answers(
    answers: Mapping[str, Any] | None,
    receipt: Mapping[str, Any],
    *,
    skipped: str | None,
    state: Mapping[str, Any],
) -> GoldExitDecision:
    payload = answers if isinstance(answers, Mapping) else {}
    choices, nouls, scores = _parsed(payload)
    any_return = any(value is not None for value in (*choices.values(), *nouls.values(), *scores.values()))
    error = None
    if receipt.get("ok") is False:
        error = str(receipt.get("error") or receipt.get("skipped") or "empty")
    _remember_parsed(state, choices, nouls, scores, None if any_return else error)
    if any_return:
        source = str(receipt.get("model") or MODEL)
    else:
        source = "unset"
    if receipt.get("ok") is False:
        skipped_out = skipped or error
    else:
        skipped_out = skipped
    return GoldExitDecision(
        take_target=choices.get("take_target"),
        time_stop=choices.get("time_stop"),
        move_sl=choices.get("move_sl"),
        scale_out=choices.get("scale_out"),
        opposite_displacement=choices.get("opposite_displacement"),
        session_death=choices.get("session_death"),
        news_exit=choices.get("news_exit"),
        exit_class=choices.get("exit_class"),
        sufficient=nouls.get("exit_state_sufficient"),
        honor_orig_stop=nouls.get("honor_orig_stop"),
        event_proximity=nouls.get("event_proximity"),
        geometry_vs_tape=scores.get("geometry_vs_tape"),
        include_depth=scores.get("include_depth"),
        threshold=scores.get("exit_threshold"),
        broker_effect=nouls.get("broker_effect"),
        never_widen=nouls.get("never_widen"),
        source=source,
        skipped=skipped_out,
        parameters=dict(scores),
    )


def decide_gold_exit(
    answers: Mapping[str, Any] | None = None,
    *,
    state: Mapping[str, Any] | None = None,
    skipped: str | None = None,
    environ: Mapping[str, str] | None = None,
    evaluate_jev: bool = True,
    ask: Callable[..., Any] | None = None,
) -> GoldExitDecision:
    """Each write, label, noul, and parameter is the System One return.

    An empty answer, a tie, a missing score, or an error leaves that field
    unset. This does not send.
    """

    if answers is None:
        if not evaluate_jev:
            return GoldExitDecision(source="not_asked", skipped=skipped)
        built = gold_exit_state() if state is None else dict(state)
        env = environ if environ is not None else os.environ
        raw = str(env.get(OVERLAY_ENV, "")).strip().lower()
        built["overlay_env"] = raw or None
        packed, receipt = _evaluate_gold_exit(built, ask)
        return _decision_from_answers(packed, receipt, skipped=skipped, state=built)
    return _decision_from_answers(
        answers,
        {"ok": True, "model": MODEL, "source": "answers_injected"},
        skipped=skipped,
        state=dict(state or {}),
    )


def exit_class_lists_time_stop(pack: Mapping[str, Any] | None = None) -> bool:
    block = (pack or GOLD_EXIT_QUESTIONS).get("exit_class") or {}
    criteria = block.get("criteria") or {}
    return "time_stop" in criteria and "manual_other" not in criteria
