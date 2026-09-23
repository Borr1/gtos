"""Previous-system-candidate Jev probe (archive ask t2016u).

One System One POST per state. Model ``jev-1.13.0``.
POST https://api.typesafe.ai/v1/systemone via ``jev_client.evaluate``
(``merge_sleeve=False``). Questions are only Noul, Choice, or Score.

Every decision, including every parameter, is the return for that state.
Prior outcomes are attached on the ask, and the return is stored for the
next ask. An empty answer, a tie, or an error leaves that field unset.
A floor and a baseline are not questions.

This probe does not send, does not flatten, and does not print the key.
Judge code stays unable to send.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

SCHEMA = "gtos.judgment.jev_history_probe.v1"
SEAT = "admission"
ARCHIVE_ASK = "t2016u"
MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
_BOOK_LOGIN = 0
_BOOK_MAGIC = 0
_BOOK_NS = "operator"

DEFAULT_JSONL = (
    Path(__file__).resolve().parents[2]
    / "judgment"
    / "astra"
    / "lab"
    / "challenge_replay_20260917"
    / "challenge_replay_rows.jsonl"
)
DEFAULT_OUT = (
    Path(__file__).resolve().parents[2]
    / "judgment"
    / "astra"
    / "lab"
    / "wires"
    / "JEV_HISTORY_PROBE.json"
)
V2_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "judgment"
    / "astra"
    / "schemas"
    / "jev_admit_v2.json"
)

V1_ADMIT_KEYS = ("admit", "surface_ok", "toxic_family", "geometry_quality", "confidence_gate")
V1_CLOSE_KEYS = ("exit_class", "toxic_remint", "geometry_quality")
V2_ANSWER_KEYS = frozenset(
    {
        "state_sufficient",
        "admit",
        "fast_stop_hazard",
        "side_formula_tension",
        "cluster_same_dir",
        "event_proximity",
        "house_consistency",
    }
)
ADMIT_ORDER = ("admit", "abstain", "hard_refuse")
ADMIT_CHOICES = frozenset(ADMIT_ORDER)
DISPOSITION_ORDER = ("log_only", "abstain")
HARD_OFF_FAMILIES = ("bleed", "orb_crypto", "idxrev", "xa_huge", "mx_us30")
KEEP_FAMILIES = ("spring", "vss")
FAMILY_LABELS = frozenset(
    {
        "house_keep",
        "house_hard_off",
        "study",
        "starve_watch",
        "other_tagged",
        "unknown",
    }
)
ADMISSION_IDS = (
    "state_sufficient",
    "flow_alignment",
    "persistence",
    "a8_quality",
    "a8_agrees",
    "geometry_vs_tape",
    "level_respect",
    "cost_hurtful",
    "admit",
)
DETERMINISM_TICKETS = (291794419, 291113462)

# Archive shape of the 2026-09-17 log. Not a live decision.
V1_QTYPE = {
    "admit": "choice",
    "surface_ok": "noul",
    "toxic_family": "noul",
    "geometry_quality": "score",
    "confidence_gate": "score",
    "exit_class": "choice",
    "toxic_remint": "noul",
}

PRICE_KEYS = frozenset(
    {
        "entry",
        "stop",
        "target",
        "open_price",
        "sl",
        "tp",
        "exit_price",
        "last_close",
        "open",
        "high",
        "low",
        "close",
        "prior_day_high",
        "prior_day_low",
        "prior_week_high",
        "prior_week_low",
        "broker_net",
        "profit",
        "realized_pnl",
        "mfe",
        "mae",
        "R",
        "stop_dist",
        "target_dist",
        "atr14",
        "volume",
        "risk",
    }
)
KEEP_RELATIVE = frozenset(
    {
        "plan_r",
        "stop_atr",
        "target_atr",
        "vol_ratio",
        "ac60",
        "htf_slope_norm",
        "mom_20_atr",
        "trigger_bar_range_atr",
        "trigger_bar_body_atr",
        "spread_r",
        "spread_r_of_stop",
        "cost_r",
    }
)
DATE_KEYS = frozenset(
    {
        "as_of_utc",
        "decision_day",
        "decision_bar_iso",
        "open_time",
        "close_time",
        "logged_at_utc",
        "first_seen_utc",
        "last_seen_utc",
        "built_at_utc",
        "weekday",
        "weekday_name",
        "is_friday",
        "as_of",
        "day",
    }
)
_DATE_RE = re.compile(
    r"^\d{4}[-.]\d{2}[-.]\d{2}([ T]\d{2}:\d{2}(:\d{2})?(Z|[+-]\d{2}:?\d{2})?)?$"
)
_LIMIT_PARTS = ("floor", "baseline", "pass_target", "pass_line", "to_pass")
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
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_STRUCTURAL_NEVER = (
    "shadow_log_only",
    "never_place",
    "never_remint",
    "never_flatten",
    "never_move_sl",
    "never_write_chair_inbox",
)

# qid, kind, field
_PACK: tuple[tuple[str, str, str], ...] = (
    ("state_sufficient", "noul", "state_sufficient"),
    ("a8_agrees", "noul", "a8_agrees"),
    ("cost_hurtful", "noul", "cost_hurtful"),
    ("probe_noul_every_tick", "noul", "noul_every_tick"),
    ("probe_one_post", "noul", "one_post"),
    ("probe_isolated_reentry", "noul", "isolated_reentry"),
    ("probe_two_stop_exhausted", "noul", "two_stop_exhausted"),
    ("probe_us30_off", "noul", "us30_off"),
    ("probe_hard_off", "noul", "hard_off"),
    ("probe_keep", "noul", "keep"),
    ("probe_component_exists", "noul", "component_exists"),
    ("admit", "choice", "admit"),
    ("probe_component", "choice", "component"),
    ("probe_disposition", "choice", "disposition"),
    ("flow_alignment", "score", "flow_alignment"),
    ("persistence", "score", "persistence"),
    ("a8_quality", "score", "a8_quality"),
    ("geometry_vs_tape", "score", "geometry_vs_tape"),
    ("level_respect", "score", "level_respect"),
    ("probe_threshold", "score", "threshold"),
    ("probe_planned_calls", "score", "planned_calls"),
    ("probe_determinism_repeats", "score", "determinism_repeats"),
    ("probe_timeout_s", "score", "timeout_s"),
    ("probe_loop_bound", "score", "loop_bound"),
    ("probe_parameter", "score", "parameter"),
)
_FIELDS = tuple(field for _qid, _kind, field in _PACK)
_CHOICE_ORDER = {
    "admit": ADMIT_ORDER,
    "probe_component": ADMISSION_IDS,
    "probe_disposition": DISPOSITION_ORDER,
}
_NOUL_TEXT = {
    "state_sufficient": "Is this open state sufficient for the admission seat?",
    "a8_agrees": "Does a8 agree with this open state?",
    "cost_hurtful": "Is the cost hurtful on this open state?",
    "probe_noul_every_tick": "Does this state ask a separate noul on every tick?",
    "probe_one_post": "Does this state stay one post for this candidate?",
    "probe_isolated_reentry": "Is isolated re-entry legal on this open state?",
    "probe_two_stop_exhausted": "Is the two-stop circuit exhausted on this open state?",
    "probe_us30_off": "Is US30 off for this open state?",
    "probe_hard_off": "Is this sleeve a hard-off family on this open state?",
    "probe_keep": "Is this sleeve a keep family on this open state?",
    "probe_component_exists": "Does the named component exist on this open state?",
}
_SCORE_TEXT = {
    "flow_alignment": "flow alignment",
    "persistence": "persistence weight",
    "a8_quality": "a8 quality",
    "geometry_vs_tape": "geometry versus the tape",
    "level_respect": "level respect",
    "probe_threshold": "threshold",
    "probe_planned_calls": "how many candidate posts this state allows",
    "probe_determinism_repeats": "how many repeats this state allows",
    "probe_timeout_s": "wait for this state, in seconds",
    "probe_loop_bound": "loop bound",
    "probe_parameter": "parameter",
}
_CHOICE_TEXT = {
    "admit": "Admission for this open state.",
    "probe_component": "Which component is the one this state is scoring?",
    "probe_disposition": "What is the shadow disposition of this state?",
}
_ADMIT_CRITERIA = {
    "admit": "Admit this candidate.",
    "abstain": "Abstain on this candidate.",
    "hard_refuse": "Refuse this candidate.",
}
_DISPOSITION_CRITERIA = {
    "log_only": "Log this state and leave the book unchanged.",
    "abstain": "No disposition for this state.",
}

# History only when jev_questions cannot be imported. A miss is not copied back.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []
_LAST: dict[str, Any] = {field: None for field in _FIELDS}


def _book() -> tuple[Any, Any, str]:
    """Challenge identity facts. A missing challenge module keeps the known book."""

    try:
        from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS

        return CHALLENGE_LOGIN, CHALLENGE_MAGIC, str(CHALLENGE_NS)
    except Exception:
        return _BOOK_LOGIN, _BOOK_MAGIC, _BOOK_NS


def _client() -> Any | None:
    try:
        from . import jev_client
    except Exception:
        return None
    return jev_client


def _limit_key(name: str) -> bool:
    low = str(name).lower()
    return any(part in low for part in _LIMIT_PARTS)


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    return any(token.replace(",", "").replace("_", "").lower() in compact for token in _BANNED_TEXT)


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


_DROP = object()


def _scrub(value: Any) -> Any:
    """Drop floor and baseline keys before an ask. They are not a question."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            cleaned = _scrub(item)
            if cleaned is _DROP:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        kept = []
        for item in value:
            cleaned = _scrub(item)
            if cleaned is not _DROP:
                kept.append(cleaned)
        return kept
    if isinstance(value, str):
        if _banned_text(value) or _limit_key(value):
            return _DROP
        return value
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if _banned_text(format(value, ".10g")):
            return _DROP
        return value
    return str(value)


def _blank() -> dict[str, Any]:
    return {field: None for field in _FIELDS}


def _store(parsed: Mapping[str, Any]) -> None:
    """The latest ask replaces every field. An omitted field stays unset."""

    for field in _FIELDS:
        _LAST[field] = parsed.get(field)


def persist_weight() -> float | None:
    """Persistence score from the latest ask. A miss stays unset."""

    return _finite(_LAST.get("persistence"))


def planned_call_budget() -> float | None:
    """Candidate-post score from the latest ask. A miss stays unset."""

    return _finite(_LAST.get("planned_calls"))


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        if _limit_key(key):
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(str(child_key), child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            for item in value:
                walk(key, item)
            return
        number = _finite(value)
        if number is None:
            return
        text = format(number, ".10g")
        if _banned_text(text):
            return
        found.append(number)

    for key, value in dict(facts or {}).items():
        walk(str(key), value)
    levels = [format(number, ".10g") for number in sorted(set(found))]
    return levels if levels else list(_BETWEEN)


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    block: dict[str, Any] = {}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(criteria))
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        block = {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    block["type"] = "choice"
    block["instructions"] = instructions
    block["criteria"] = {str(key): str(text) for key, text in criteria.items() if not _limit_key(str(key))}
    return block


def _score_question(qid: str, instructions: str, criteria: list[str]) -> dict[str, Any]:
    block: dict[str, Any] = {}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        block = {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    block["type"] = "score"
    block["instructions"] = instructions
    kept = [str(item) for item in criteria if not _limit_key(str(item)) and not _banned_text(str(item))]
    block["criteria"] = kept if kept else list(_BETWEEN)
    return block


def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {
            "true": "Yes for this state.",
            "false": "No for this state.",
        },
    }


def _criteria(qid: str) -> dict[str, str]:
    if qid == "admit":
        return dict(_ADMIT_CRITERIA)
    if qid == "probe_disposition":
        return dict(_DISPOSITION_CRITERIA)
    if qid == "probe_component":
        return {name: f"This state is scoring {name}." for name in ADMISSION_IDS}
    return {}


def probe_questions(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One pack. Types stay Noul, Choice, or Score."""

    scale = _levels(state if isinstance(state, Mapping) else {})
    pack: dict[str, Any] = {}
    for qid, kind, _field in _PACK:
        if kind == "noul":
            text = (
                f"{_NOUL_TEXT[qid]} "
                "An empty answer leaves this unset. "
                "Do not send an order."
            )
            block = _noul_question(qid, text)
        elif kind == "choice":
            text = (
                f"{_CHOICE_TEXT[qid]} "
                "The unique highest probability is the decision. "
                "An empty answer or a tie leaves this unset. "
                "Do not send an order."
            )
            block = _choice_question(qid, text, _criteria(qid))
        else:
            text = (
                f"The score you return is the {_SCORE_TEXT[qid]} for this state. "
                "It may sit between the levels on this state. "
                "An empty score leaves it unset. "
                "Do not send an order."
            )
            block = _score_question(qid, text, scale)
        blob = json.dumps(block, default=str).lower()
        if _limit_key(qid) or "floor" in blob or "baseline" in blob or _banned_text(blob):
            continue
        if str(block.get("type") or "") not in {"noul", "choice", "score"}:
            continue
        pack[qid] = block
    return pack


def gold_admission_qtypes() -> dict[str, str]:
    return {qid: kind for qid, kind, _field in _PACK}


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
        if name not in allowed or _limit_key(name):
            continue
        number = _finite(val)
        if number is None:
            continue
        numeric[name] = number
    return numeric


def _local_unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in order:
        if name not in numeric:
            continue
        prob = numeric[name]
        seen = True
        if best_p is None or prob > best_p + 1e-12:
            best = name
            best_p = prob
            tied = False
        elif abs(prob - best_p) <= 1e-12:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice_of(block: Any, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A bare label, a tie, or an empty block is unset."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "choice":
        return None
    numeric = _probabilities(block, order)
    if not numeric:
        return None
    local = _local_unique(numeric, order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(numeric, order)
    except Exception:
        picked = local
    if local is None or picked is None or str(picked) != local or str(picked) not in order:
        return None
    return str(picked)


def _noul_of(block: Any) -> bool | float | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "noul":
        return None
    if "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is None:
        return None
    if raw is True or raw is False:
        return raw
    return _finite(raw)


def _score_of(block: Any) -> float | None:
    """The returned score. It may sit between levels. A missing score stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "score":
        return None
    raw = None
    if "score" in block and block.get("score") is not None:
        raw = block.get("score")
    elif "value" in block and block.get("value") is not None:
        raw = block.get("value")
    number = _finite(raw)
    try:
        from .jev_questions import returned_number

        parsed = _finite(returned_number(block))
    except Exception:
        parsed = number
    if number is None or parsed is None or parsed != number:
        return None
    return number


def _parse(answers: Mapping[str, Any] | None) -> dict[str, Any]:
    raw = answers if isinstance(answers, Mapping) else {}
    parsed = _blank()
    for qid, kind, field in _PACK:
        block = raw.get(qid)
        if kind == "choice":
            parsed[field] = _choice_of(block, _CHOICE_ORDER[qid])
        elif kind == "noul":
            parsed[field] = _noul_of(block)
        else:
            parsed[field] = _score_of(block)
    return parsed


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
        state["prior_outcomes"] = [] if loaded is None else loaded
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]


def _remember(state: Mapping[str, Any], parsed: Mapping[str, Any], error: str | None) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        append_outcome = None
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for qid, _kind, field in _PACK:
        value = parsed.get(field)
        miss = None if value is not None else (error or "unset")
        if append_outcome is None:
            _LOCAL_OUTCOMES.append({"key": qid, "value": value, "error": miss})
            continue
        stored = value if isinstance(value, (str, int, float, bool)) or value is None else None
        try:
            append_outcome(qid, stored, logged, error=miss)
        except Exception:
            _LOCAL_OUTCOMES.append({"key": qid, "value": value, "error": miss})


def _ask(
    state: Mapping[str, Any] | None,
    *,
    timeout_s: float | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One post. Empty, tie, and error leave every field unset."""

    cleaned = _scrub(dict(state or {}))
    asked = cleaned if isinstance(cleaned, dict) else {}
    login, magic, ns = _book()
    asked["model"] = MODEL
    asked["login"] = login
    asked["ns"] = ns
    asked["magic"] = magic
    asked.pop("prior_outcomes", None)
    questions = probe_questions(asked)
    if not questions:
        parsed = _blank()
        _store(parsed)
        _remember(asked, parsed, "question_rejected")
        return {
            "ok": False,
            "skipped": None,
            "error": "question_rejected",
            "http_status": None,
            "model": MODEL,
            "answers": {},
            "decisions": parsed,
            "question_ids": [],
            "calls_used": None,
            "calls_remaining": None,
            "key_source": None,
            "key_fingerprint": None,
        }
    _attach_priors(asked, questions)
    wait = _finite(timeout_s)
    if wait is not None and wait <= 0:
        wait = None
    try:
        call = evaluate_fn
        if call is None:
            client = _client()
            if client is None:
                raise ModuleNotFoundError("jev_client")
            call = client.evaluate
        receipt = call(
            asked,
            timeout_s=wait,
            model=MODEL,
            questions=questions,
            merge_sleeve=False,
        )
    except Exception as exc:
        parsed = _blank()
        _store(parsed)
        _remember(asked, parsed, type(exc).__name__)
        return {
            "ok": False,
            "skipped": None,
            "error": type(exc).__name__,
            "http_status": None,
            "model": MODEL,
            "answers": {},
            "decisions": parsed,
            "question_ids": list(questions),
            "calls_used": None,
            "calls_remaining": None,
            "key_source": None,
            "key_fingerprint": None,
        }
    if not isinstance(receipt, dict):
        parsed = _blank()
        _store(parsed)
        _remember(asked, parsed, "evaluate_not_a_dict")
        return {
            "ok": False,
            "skipped": None,
            "error": "evaluate_not_a_dict",
            "http_status": None,
            "model": MODEL,
            "answers": {},
            "decisions": parsed,
            "question_ids": list(questions),
            "calls_used": None,
            "calls_remaining": None,
            "key_source": None,
            "key_fingerprint": None,
        }
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    parsed = _parse(answers)
    error = None
    if receipt.get("ok") is False or not answers:
        error = str(receipt.get("error") or receipt.get("skipped") or "empty")
    elif all(value is None for value in parsed.values()):
        error = "empty"
    _store(parsed)
    _remember(asked, parsed, error)
    key = None
    client = _client()
    if client is not None:
        try:
            key = client.api_key()
        except Exception:
            key = None
    dumped = json.dumps(receipt, default=str)
    if key and key in dumped:
        raise RuntimeError("key leaked into receipt")
    return {
        "ok": bool(receipt.get("ok")) and error is None,
        "skipped": receipt.get("skipped"),
        "error": error,
        "http_status": receipt.get("http_status"),
        "model": receipt.get("model") or MODEL,
        "answers": answers,
        "decisions": parsed,
        "question_ids": list(questions),
        "calls_used": receipt.get("calls_used"),
        "calls_remaining": receipt.get("calls_remaining"),
        "key_source": receipt.get("key_source"),
        "key_fingerprint": receipt.get("key_fingerprint"),
    }


def load_replay_rows(path: Path | None = None) -> list[dict[str, Any]]:
    src = path or DEFAULT_JSONL
    rows: list[dict[str, Any]] = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def parse_open_clock(raw: str) -> datetime:
    text = (raw or "").strip()
    for fmt in (
        "%Y.%m.%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ):
        try:
            dt = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    raise ValueError(f"unparsed open_time {raw!r}")


def _side(raw: str) -> str:
    text = (raw or "").strip().lower()
    if text in {"buy", "long"}:
        return "long"
    if text in {"sell", "short"}:
        return "short"
    raise ValueError(f"unmapped side {raw!r}")


def _side_or_none(raw: Any) -> str | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return _side(str(raw))
    except ValueError:
        return None


def _plan_r(entry: float | None, stop: float | None, target: float | None) -> float | None:
    if entry is None or stop is None or target is None:
        return None
    width = abs(float(entry) - float(stop))
    if width <= 0:
        return None
    return abs(float(target) - float(entry)) / width


def _num(value: Any) -> float | None:
    return _finite(value)


def row_input(row: Mapping[str, Any]) -> dict[str, Any]:
    return dict(row.get("input") or {})


def ticket_of(row: Mapping[str, Any]) -> int:
    return int(row_input(row)["ticket"])


def _ticket_or_zero(row: Mapping[str, Any]) -> int:
    try:
        return ticket_of(row)
    except (KeyError, TypeError, ValueError):
        return 0


def _family_label(sleeve: str, symbol: str) -> str | None:
    try:
        from .family import family_class_for
    except Exception:
        return None
    try:
        label = family_class_for(sleeve, symbol=symbol, origin="f5_challenge")
    except Exception:
        return None
    if label is None:
        return None
    text = str(label)
    if text not in FAMILY_LABELS and text not in KEEP_FAMILIES and text not in HARD_OFF_FAMILIES:
        return None
    return text


def _reject_expost(state: Mapping[str, Any], clock: str) -> list[Any]:
    try:
        from .gold_state import reject_expost
    except Exception:
        return []
    try:
        leaked = reject_expost(state, clock)
    except Exception:
        return []
    if not leaked:
        return []
    return list(leaked)


def assemble_as_of_open(
    row: Mapping[str, Any],
    *,
    as_of_clock: str = "as_of_open_study",
) -> dict[str, Any]:
    """Open facts from the replay row. Decision fields stay off this state."""

    inp = row_input(row)
    sleeve = str(inp.get("sleeve") or inp.get("tag") or "")
    raw_symbol = inp.get("symbol")
    symbol = str(raw_symbol).strip() if raw_symbol not in (None, "") else None
    side = _side(str(inp.get("side") or ""))
    entry = _num(inp.get("open_price"))
    stop = _num(inp.get("sl"))
    target = _num(inp.get("tp"))
    plan_r = _plan_r(entry, stop, target)
    stop_dist = None if entry is None or stop is None else abs(entry - stop)
    opened = parse_open_clock(str(inp.get("open_time") or ""))
    login, magic, ns = _book()
    geometry = {
        key: value
        for key, value in (
            ("entry", entry),
            ("stop", stop),
            ("target", target),
            ("stop_dist", stop_dist),
            ("plan_r", plan_r),
        )
        if value is not None
    }
    order_type = inp.get("order_type")
    if isinstance(order_type, str) and order_type.strip():
        geometry["order_type"] = order_type.strip()
    occupancy: dict[str, Any] = {
        "ticket": inp.get("ticket"),
        "occupancy_source": "challenge_replay_open",
    }
    if inp.get("remint_of") is not None:
        occupancy["remint_of"] = inp.get("remint_of")
    identity: dict[str, Any] = {
        "candidate_id": str(inp.get("ticket")),
        "side": side,
        "origin_organism": "f5_challenge",
    }
    if sleeve:
        identity["sleeve"] = sleeve
    if symbol:
        identity["symbol"] = symbol
    family = _family_label(sleeve, symbol or "")
    if family is not None:
        identity["family_class"] = family
    state = {
        "schema": "gold_state.v0",
        "as_of_clock": as_of_clock,
        "identity": identity,
        "clock": {"as_of_utc": opened.strftime("%Y-%m-%dT%H:%M:%SZ")},
        "geometry": geometry,
        "occupancy": occupancy,
        "world": {
            "source": "unassembled",
            "assembled": False,
        },
        "labels": {
            "ticket": inp.get("ticket"),
            "side": side,
            "subgoal": "history_probe",
            **({"sleeve": sleeve} if sleeve else {}),
            **({"symbol": symbol} if symbol else {}),
        },
        "login": login,
        "ns": ns,
        "magic": magic,
        "model": MODEL,
        "seat": SEAT,
    }
    leaked = _reject_expost(state, as_of_clock)
    for key in leaked:
        if isinstance(key, str):
            state.pop(key, None)
    return state


def mask_absolute_dates_and_prices(state: Mapping[str, Any] | None) -> dict[str, Any]:
    """Ablation: strip dates and absolute prices. Keep relative ATR, session, side, family, plan_r."""

    def walk(obj: Any, key: str | None = None) -> Any:
        if key in KEEP_RELATIVE:
            return deepcopy(obj)
        if key in DATE_KEYS or key in PRICE_KEYS or (key is not None and _limit_key(key)):
            return None
        if isinstance(obj, str) and key not in {"named", "side", "sleeve", "family_class", "symbol", "family_node"}:
            if _DATE_RE.match(obj.strip()) or _banned_text(obj):
                return None
        if isinstance(obj, Mapping):
            return {str(k): walk(v, str(k)) for k, v in obj.items() if not _limit_key(str(k))}
        if isinstance(obj, list):
            return [walk(v, key) for v in obj]
        return deepcopy(obj)

    out = walk(state) or {}
    if not isinstance(out, dict):
        out = {}
    ident = dict(out.get("identity") or {})
    ticket = ident.get("candidate_id")
    if ticket is not None:
        ident["candidate_id"] = str(ticket)
        ident["decision_day"] = None
        ident["decision_bar_iso"] = None
        out["identity"] = ident
    clock = dict(out.get("clock") or {})
    clock["as_of_utc"] = None
    clock["weekday"] = None
    clock["weekday_name"] = None
    clock["is_friday"] = None
    out["clock"] = clock
    labels = dict(out.get("labels") or {})
    if labels:
        labels["as_of"] = None
        labels["day"] = None
        out["labels"] = labels
    leaked = _reject_expost(out, str(out.get("as_of_clock") or "as_of_open_study"))
    for key in leaked:
        if isinstance(key, str):
            out.pop(key, None)
    scrubbed = _scrub(out)
    return scrubbed if isinstance(scrubbed, dict) else {}


def admission_payload(state: Mapping[str, Any], *, masked: bool) -> dict[str, Any]:
    body = dict(state)
    if masked:
        body = mask_absolute_dates_and_prices(body)
    scrubbed = _scrub(body)
    if not isinstance(scrubbed, dict):
        scrubbed = {}
    questions = probe_questions(scrubbed)
    return {
        "state": scrubbed,
        "model": MODEL,
        "questions": questions,
        "masked": masked,
        "seat": SEAT,
        "ask_together": True,
    }


def typesafe_shape_ok(answers: Mapping[str, Any] | None, qtypes: Mapping[str, str]) -> dict[str, Any]:
    """TypeSafe answer shape for the questions actually asked. A meter, not a filled parameter."""

    raw = dict(answers or {})
    n_choice = n_noul = n_score = 0
    choice_in_prob = 0
    maps_ok = 0
    maps_n = 0
    range_ok = 0
    range_n = 0
    for qid, spec in qtypes.items():
        ans = raw.get(qid)
        if not isinstance(ans, Mapping):
            continue
        if spec == "choice":
            n_choice += 1
            choice = ans.get("choice")
            probs = ans.get("probabilities") or {}
            if choice in probs:
                choice_in_prob += 1
            if isinstance(probs, Mapping) and probs:
                maps_n += 1
                total = sum(float(v) for v in probs.values() if _finite(v) is not None)
                if abs(total - 1.0) <= 0.02:
                    maps_ok += 1
            conf = ans.get("confidence")
            if conf is not None:
                range_n += 1
                if _finite(conf) is not None and 0.0 <= float(conf) <= 1.0:
                    range_ok += 1
        elif spec == "noul":
            n_noul += 1
            val = ans.get("noul")
            if val is not None:
                range_n += 1
                if val is True or val is False or _finite(val) is not None:
                    range_ok += 1
        elif spec == "score":
            n_score += 1
            score = ans.get("score")
            conf = ans.get("confidence")
            if score is not None:
                range_n += 1
                if _finite(score) is not None:
                    range_ok += 1
            if conf is not None:
                range_n += 1
                if _finite(conf) is not None and 0.0 <= float(conf) <= 1.0:
                    range_ok += 1
            probs = ans.get("probabilities")
            if isinstance(probs, Mapping) and probs:
                maps_n += 1
                total = sum(float(v) for v in probs.values() if _finite(v) is not None)
                if abs(total - 1.0) <= 0.02:
                    maps_ok += 1
    asked = sum(1 for qid in qtypes if qid in raw)
    ok = (
        asked == len(qtypes)
        and (n_choice == 0 or choice_in_prob == n_choice)
        and (maps_n == 0 or maps_ok == maps_n)
        and (range_n == 0 or range_ok == range_n)
    )
    return {
        "ok": ok,
        "asked": asked,
        "want": len(qtypes),
        "choice_in_probabilities": f"{choice_in_prob}/{n_choice}" if n_choice else "0/0",
        "prob_maps_sum_1": f"{maps_ok}/{maps_n}" if maps_n else "0/0",
        "range_ok": f"{range_ok}/{range_n}" if range_n else "0/0",
        "n_choice": n_choice,
        "n_noul": n_noul,
        "n_score": n_score,
    }


def answers_are_v2_shape(answers: Mapping[str, Any] | None) -> bool:
    """True iff answers contain a valid v2 admit Choice and no illegal extra keys."""

    raw = dict(answers or {})
    extra = set(raw) - V2_ANSWER_KEYS
    if extra:
        return False
    admit = raw.get("admit")
    if not isinstance(admit, Mapping):
        return False
    if _choice_of(admit, ADMIT_ORDER) is None:
        return False
    conf = admit.get("confidence")
    probs = admit.get("probabilities")
    if not isinstance(probs, Mapping):
        return False
    if conf is None or _finite(conf) is None or not (0.0 <= float(conf) <= 1.0):
        return False
    total = sum(float(v) for v in probs.values() if _finite(v) is not None)
    if abs(total - 1.0) > 0.02:
        return False
    ss = raw.get("state_sufficient")
    if ss is not None:
        if _noul_of(ss) is None and not (isinstance(ss, Mapping) and ss.get("noul") is not None):
            return False
        noul = ss.get("noul") if isinstance(ss, Mapping) else None
        if noul is not None and noul is not True and noul is not False:
            if _finite(noul) is None:
                return False
    return True


def v2_sidecar_from_admission(
    *,
    state: Mapping[str, Any],
    answers: Mapping[str, Any],
    ticket: int,
    decisions: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Study sidecar. Shadow-log only. House fields are the return or unset."""

    decided = dict(decisions or {})
    ident = dict(state.get("identity") or {})
    sleeve = str(ident.get("sleeve") or "")
    symbol = str(ident.get("symbol") or "")
    family = ident.get("family_class")
    if family is not None and str(family) not in FAMILY_LABELS:
        family = None
    geo = dict(state.get("geometry") or {})
    login, magic, ns = _book()
    slim_answers = {k: deepcopy(v) for k, v in answers.items() if k in V2_ANSWER_KEYS}
    threshold = _finite(decided.get("threshold"))
    return {
        "schema": "jev_admit_v2",
        "mode": "shadow_log_only",
        "shadow_log_only": True,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_move_sl": True,
        "never_write_chair_inbox": True,
        "namespace": "gtos.astra.jev_trial.v2",
        "account_surface": {
            "login": login,
            "magic": magic,
            "ns": ns,
            "role": "challenge_calibration",
            "verification_login_quarantined": "0",
        },
        "admit_clock": "as_of_open_study",
        "house_law": {
            "us30_off": decided.get("us30_off"),
            "hard_off_hit": decided.get("hard_off"),
            "keep_family": decided.get("keep"),
            "two_stop_exhausted": decided.get("two_stop_exhausted"),
            "house_block": decided.get("hard_off"),
        },
        "state": {
            "candidate": {
                "candidate_id": str(ticket),
                "symbol": symbol,
                "sleeve": sleeve,
                "family_class": family,
                "direction": ident.get("side"),
                "geometry": {
                    k: geo[k]
                    for k in ("plan_r", "stop_atr", "target_atr")
                    if geo.get(k) is not None
                },
            },
            "surface": {
                "hard_off_families": list(HARD_OFF_FAMILIES),
                "keep_families": list(KEEP_FAMILIES),
                "circuit": "2-stop",
            },
            "writer": {
                "token_namespace": ns,
            },
        },
        "answers": slim_answers,
        "disposition": decided.get("disposition"),
        "threshold": threshold,
        "persistence": _finite(decided.get("persistence")),
        "parameter": _finite(decided.get("parameter")),
    }


def v2_sidecar_ok(sidecar: Mapping[str, Any] | None) -> bool:
    row = dict(sidecar or {})
    if row.get("schema") != "jev_admit_v2":
        return False
    if row.get("mode") != "shadow_log_only":
        return False
    for flag in _STRUCTURAL_NEVER:
        if row.get(flag) is not True:
            return False
    surface = row.get("account_surface") or {}
    login, _magic, _ns = _book()
    if str(surface.get("login")) != str(login):
        return False
    if row.get("admit_clock") not in {"live_intent", "as_of_open_study", "as_of_close_illegal_for_live"}:
        return False
    state = row.get("state") or {}
    if not isinstance(state.get("candidate"), Mapping):
        return False
    if not isinstance(state.get("surface"), Mapping):
        return False
    if not isinstance(state.get("writer"), Mapping):
        return False
    if _reject_expost(state.get("candidate") or {}, str(row.get("admit_clock"))):
        return False
    surface_account = row.get("account_surface") or {}
    if any(_limit_key(str(key)) for key in surface_account):
        return False
    return answers_are_v2_shape(row.get("answers"))


def archived_call_blocks(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    blocks = []
    for name, keys, qtypes in (
        ("admit_then", V1_ADMIT_KEYS, {k: V1_QTYPE[k] for k in V1_ADMIT_KEYS}),
        ("admit_now", V1_ADMIT_KEYS, {k: V1_QTYPE[k] for k in V1_ADMIT_KEYS}),
        ("close_label", V1_CLOSE_KEYS, {k: V1_QTYPE[k] for k in V1_CLOSE_KEYS}),
    ):
        blob = dict(row.get(name) or {})
        answers = dict(blob.get("answers") or {})
        blocks.append(
            {
                "seat": name,
                "ticket": ticket_of(row),
                "model": blob.get("model"),
                "keys": tuple(sorted(answers)),
                "answers": answers,
                "qtypes": qtypes,
                "v1_keys": keys,
            }
        )
    return blocks


def score_archived_pack(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Measure the stored 2026-09-17 answers. This read does not decide a live parameter."""

    n_calls = 0
    n_v2_raw = 0
    n_typesafe = 0
    n_v2_sidecar = 0
    n_v1_keyset = 0
    models = set()
    for row in rows:
        for block in archived_call_blocks(row):
            n_calls += 1
            models.add(block.get("model"))
            want = tuple(sorted(block["v1_keys"]))
            if tuple(sorted(block["keys"])) == want:
                n_v1_keyset += 1
            shape = typesafe_shape_ok(block["answers"], block["qtypes"])
            if shape["ok"]:
                n_typesafe += 1
            if answers_are_v2_shape(block["answers"]):
                n_v2_raw += 1
            slim = {k: v for k, v in block["answers"].items() if k in V2_ANSWER_KEYS}
            inp = row_input(row)
            sleeve = str(inp.get("sleeve") or "")
            symbol = str(inp.get("symbol") or "")
            fake_state = {
                "identity": {
                    "sleeve": sleeve,
                    "symbol": symbol,
                    "side": _side_or_none(inp.get("side")),
                    "family_class": _family_label(sleeve, symbol),
                },
                "geometry": {},
            }
            sidecar = v2_sidecar_from_admission(
                state=fake_state,
                answers=slim,
                ticket=block["ticket"],
            )
            if v2_sidecar_ok(sidecar):
                n_v2_sidecar += 1
    return {
        "n_rows": len(rows),
        "n_calls": n_calls,
        "models": sorted(str(m) for m in models if m),
        "v1_keyset": f"{n_v1_keyset}/{n_calls}",
        "typesafe_shape": f"{n_typesafe}/{n_calls}",
        "typesafe_shape_n": n_typesafe,
        "v2_raw_answers": f"{n_v2_raw}/{n_calls}",
        "v2_raw_answers_n": n_v2_raw,
        "v2_stripped_sidecar": f"{n_v2_sidecar}/{n_calls}",
        "v2_stripped_sidecar_n": n_v2_sidecar,
        "v1_keys_admit": list(V1_ADMIT_KEYS),
        "v1_keys_close": list(V1_CLOSE_KEYS),
        "note": (
            "09-17 replay stored v1 keys. Raw answers are measured as stored. "
            "A stripped sidecar keeps only v2 answer keys. Close rows have no admit Choice."
        ),
    }


def unauthenticated_post(*, timeout_s: float | None = None) -> dict[str, Any]:
    """POST without Authorization. Does not decide a parameter. Never sends a key."""

    wait = _finite(timeout_s)
    if wait is None or wait <= 0:
        return {
            "ok": False,
            "skipped": "timeout_unset",
            "http_status": None,
            "error": "timeout_unset",
            "authorization_header_sent": False,
        }
    url = API_URL
    client = _client()
    if client is not None:
        url = str(getattr(client, "API_URL", API_URL))
    body = json.dumps({"model": MODEL, "state": {"probe": "unauth"}}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "gtos-judgment/history-probe"},
    )
    try:
        with urllib.request.urlopen(req, timeout=wait) as resp:
            return {
                "ok": True,
                "http_status": int(resp.status),
                "error": None,
                "authorization_header_sent": False,
            }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "http_status": int(exc.code),
            "error": f"http_{exc.code}",
            "authorization_header_sent": False,
        }
    except Exception as exc:  # noqa: BLE001 — probe must never raise
        return {
            "ok": False,
            "http_status": None,
            "error": type(exc).__name__,
            "authorization_header_sent": False,
        }


def post_admission(
    state: Mapping[str, Any],
    *,
    masked: bool,
    timeout_s: float | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    payload = admission_payload(state, masked=masked)
    posted = _ask(payload["state"], timeout_s=timeout_s, evaluate_fn=evaluate_fn)
    answers = dict(posted.get("answers") or {})
    decisions = dict(posted.get("decisions") or _blank())
    qtypes = gold_admission_qtypes()
    shape = typesafe_shape_ok(answers, qtypes) if answers else {"ok": False, "asked": 0}
    sidecar = None
    sidecar_ok = False
    if answers and posted.get("ok"):
        ticket_raw = (payload["state"].get("labels") or {}).get("ticket")
        try:
            ticket = int(ticket_raw)
        except (TypeError, ValueError):
            ticket = 0
        sidecar = v2_sidecar_from_admission(
            state=payload["state"],
            answers=answers,
            ticket=ticket,
            decisions=decisions,
        )
        sidecar_ok = v2_sidecar_ok(sidecar)
    return {
        "ok": bool(posted.get("ok")),
        "skipped": posted.get("skipped"),
        "error": posted.get("error"),
        "http_status": posted.get("http_status"),
        "model": posted.get("model") or MODEL,
        "masked": masked,
        "seat": SEAT,
        "payload_question_ids": list(posted.get("question_ids") or []),
        "answers": answers,
        "decisions": decisions,
        "typesafe_shape_ok": bool(shape.get("ok")),
        "v2_raw_answers_ok": answers_are_v2_shape(answers) if answers else False,
        "v2_sidecar_ok": sidecar_ok,
        "calls_used": posted.get("calls_used"),
        "calls_remaining": posted.get("calls_remaining"),
        "key_source": posted.get("key_source"),
        "key_fingerprint": posted.get("key_fingerprint"),
        "persist_weight": decisions.get("persistence"),
        "noul_every_tick": decisions.get("noul_every_tick"),
        "one_post": decisions.get("one_post"),
        "broker_effect": False,
        "never_order_send": True,
    }


def _safe_summary_row(posted: Mapping[str, Any], ticket: int) -> dict[str, Any]:
    decisions = dict(posted.get("decisions") or {})
    return {
        "ticket": ticket,
        "masked": posted.get("masked"),
        "ok": posted.get("ok"),
        "skipped": posted.get("skipped"),
        "http_status": posted.get("http_status"),
        "admit_choice": decisions.get("admit"),
        "persistence": decisions.get("persistence"),
        "threshold": decisions.get("threshold"),
        "parameter": decisions.get("parameter"),
        "disposition": decisions.get("disposition"),
        "typesafe_shape_ok": posted.get("typesafe_shape_ok"),
        "v2_raw_answers_ok": posted.get("v2_raw_answers_ok"),
        "v2_sidecar_ok": posted.get("v2_sidecar_ok"),
    }


def _key_meta() -> tuple[bool, str | None, str | None]:
    client = _client()
    if client is None:
        return False, None, None
    try:
        present = client.api_key() is not None
    except Exception:
        present = False
    try:
        source = client.key_source()
    except Exception:
        source = None
    try:
        finger = client.key_fingerprint()
    except Exception:
        finger = None
    return bool(present), source, finger


def _cap(max_posts: int | None, planned: Any) -> float | None:
    bounds: list[float] = []
    if max_posts is not None:
        number = _finite(max_posts)
        if number is not None:
            bounds.append(number)
    score = _finite(planned)
    if score is not None:
        bounds.append(score)
    if not bounds:
        return None
    return min(bounds)


def _under(posted: int, cap: float | None) -> bool:
    if cap is None:
        return False
    return posted < cap


def _repeat_count(decisions: Mapping[str, Any]) -> float:
    """Extra posts of the same state. Unset or one-post leaves the count at zero."""

    if decisions.get("one_post") is not False:
        return 0.0
    repeats = _finite(decisions.get("determinism_repeats"))
    if repeats is None or repeats <= 0:
        return 0.0
    return repeats


def run_probe(
    *,
    jsonl: Path | None = None,
    out: Path | None = None,
    timeout_s: float | None = None,
    max_posts: int | None = None,
    skip_unauth: bool = False,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    login, magic, ns = _book()
    pin: dict[str, Any] | None
    try:
        from .gold_priors import assert_gold_pin

        raw_pin = assert_gold_pin()
        pin = dict(raw_pin) if isinstance(raw_pin, Mapping) else {"ok": False, "error": "pin_unreadable"}
    except Exception as exc:
        pin = {"ok": False, "error": type(exc).__name__}
    if isinstance(pin, dict):
        pin = _scrub(pin)
        if not isinstance(pin, dict):
            pin = {"ok": False, "error": "pin_scrubbed"}

    rows = load_replay_rows(jsonl)
    archived = score_archived_pack(rows)
    present, source, finger = _key_meta()
    client = _client()
    if client is None:
        blocker = "jev_client_import_failed"
    elif not present:
        blocker = "TYPESAFE_API_KEY_absent"
    else:
        blocker = None
    if client is not None and evaluate_fn is None:
        try:
            client.reset_call_budget()
        except Exception:
            pass

    run_state = {
        "schema": SCHEMA,
        "archive_ask": ARCHIVE_ASK,
        "seat": SEAT,
        "n_rows": len(rows),
        "login": login,
        "ns": ns,
        "magic": magic,
        "model": MODEL,
        "labels": {"subgoal": "history_probe", "archive_ask": ARCHIVE_ASK},
    }
    run_posted = _ask(run_state, timeout_s=timeout_s, evaluate_fn=evaluate_fn)
    run_decisions = dict(run_posted.get("decisions") or _blank())
    wait = _finite(timeout_s)
    if wait is None or wait <= 0:
        returned_wait = _finite(run_decisions.get("timeout_s"))
        wait = returned_wait if returned_wait is not None and returned_wait > 0 else None
    cap = _cap(max_posts, run_decisions.get("planned_calls"))

    if skip_unauth:
        unauth: dict[str, Any] = {"skipped": "skip_unauth"}
    else:
        unauth = unauthenticated_post(timeout_s=wait)

    posts_unmasked: list[dict[str, Any]] = []
    posts_masked: list[dict[str, Any]] = []
    determinism: dict[str, Any] = {}
    assembled: list[dict[str, Any]] = []
    for row in rows:
        try:
            state = assemble_as_of_open(row)
        except (ValueError, KeyError, TypeError) as exc:
            assembled.append({"ticket": None, "error": type(exc).__name__})
            continue
        leaked = _reject_expost(state, "as_of_open_study")
        identity = state.get("identity") or {}
        assembled.append(
            {
                "ticket": identity.get("candidate_id"),
                "symbol": identity.get("symbol"),
                "sleeve": identity.get("sleeve"),
                "side": identity.get("side"),
                "family_class": identity.get("family_class"),
                "plan_r": (state.get("geometry") or {}).get("plan_r"),
                "expost_rejected": leaked,
                "state_sufficient_for_live": None,
            }
        )

    n_posted = 0
    live = evaluate_fn is not None or present

    def _note(posted: Mapping[str, Any]) -> None:
        nonlocal n_posted
        del posted
        n_posted += 1

    if live and _under(n_posted, cap):
        open_rows = []
        for row in rows:
            try:
                open_rows.append((row, assemble_as_of_open(row)))
            except (ValueError, KeyError, TypeError):
                continue
        for row, state in open_rows:
            if not _under(n_posted, cap):
                break
            posted = post_admission(state, masked=False, timeout_s=wait, evaluate_fn=evaluate_fn)
            _note(posted)
            posts_unmasked.append(_safe_summary_row(posted, _ticket_or_zero(row)))
        for row, state in open_rows:
            if not _under(n_posted, cap):
                break
            posted = post_admission(state, masked=True, timeout_s=wait, evaluate_fn=evaluate_fn)
            _note(posted)
            posts_masked.append(_safe_summary_row(posted, _ticket_or_zero(row)))
        repeats = _repeat_count(run_decisions)
        by_ticket = {}
        for row in rows:
            try:
                by_ticket[ticket_of(row)] = row
            except (KeyError, TypeError, ValueError):
                continue
        for ticket in DETERMINISM_TICKETS:
            if ticket not in by_ticket:
                determinism[str(ticket)] = {"ok": False, "reason": "ticket_absent", "n": 0}
                continue
            answers_seq: list[Any] = []
            while len(answers_seq) < repeats and _under(n_posted, cap):
                state = assemble_as_of_open(by_ticket[ticket])
                posted = post_admission(state, masked=False, timeout_s=wait, evaluate_fn=evaluate_fn)
                _note(posted)
                answers_seq.append(posted.get("answers") or {})
            identical = bool(answers_seq) and all(item == answers_seq[0] for item in answers_seq)
            determinism[str(ticket)] = {
                "n": len(answers_seq),
                "identical": identical if answers_seq else None,
                "skipped": (all(not item for item in answers_seq) if answers_seq else None),
            }
    elif rows:
        sample = None
        for row in rows:
            try:
                sample = assemble_as_of_open(row)
                break
            except (ValueError, KeyError, TypeError):
                continue
        if sample is not None:
            _ = admission_payload(sample, masked=False)
            _ = admission_payload(sample, masked=True)

    calls_used = run_posted.get("calls_used")
    calls_remaining = run_posted.get("calls_remaining")
    if client is not None:
        try:
            calls_used = client.calls_used()
        except Exception:
            pass
        try:
            calls_remaining = client.calls_remaining()
        except Exception:
            pass
    v2_rel = None
    try:
        v2_rel = str(V2_SCHEMA_PATH.relative_to(Path(__file__).resolve().parents[2]))
    except ValueError:
        v2_rel = str(V2_SCHEMA_PATH)
    receipt = {
        "schema": SCHEMA,
        "archive_ask": ARCHIVE_ASK,
        "probed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "book": login,
        "ns": ns,
        "magic": magic,
        "model": MODEL,
        "api_url": API_URL,
        "seat": SEAT,
        "admission_ids": list(ADMISSION_IDS),
        "question_ids": list(run_posted.get("question_ids") or []),
        "probe_parameters": run_decisions,
        "persist_weight": run_decisions.get("persistence"),
        "noul_every_tick": run_decisions.get("noul_every_tick"),
        "one_post": run_decisions.get("one_post"),
        "planned_calls": run_decisions.get("planned_calls"),
        "determinism_repeats": run_decisions.get("determinism_repeats"),
        "timeout_s": run_decisions.get("timeout_s"),
        "loop_bound": run_decisions.get("loop_bound"),
        "threshold": run_decisions.get("threshold"),
        "parameter": run_decisions.get("parameter"),
        "ac60_wall": False,
        "never_place": True,
        "never_flatten": True,
        "never_bounce_writer": True,
        "never_leftover_ship_onto_main": True,
        "never_print_key": True,
        "never_order_send": True,
        "broker_effect": False,
        "pin": pin,
        "cap": cap,
        "key_present": present,
        "key_source": source,
        "key_fingerprint": finger,
        "blocker": blocker,
        "unauthenticated_post": unauth,
        "archived_20260917": archived,
        "assembled_open": assembled,
        "posts_unmasked": posts_unmasked,
        "posts_masked": posts_masked,
        "masked_vs_unmasked": _masked_vs_unmasked(posts_unmasked, posts_masked),
        "determinism": determinism,
        "n_posted": n_posted if live else 0,
        "calls_used": calls_used,
        "calls_remaining": calls_remaining,
        "v2_schema_path": v2_rel,
    }
    leaked_key = None
    if client is not None:
        try:
            leaked_key = client.api_key()
        except Exception:
            leaked_key = None
    encoded = json.dumps(receipt, indent=2, sort_keys=True, default=str)
    if leaked_key and leaked_key in encoded:
        raise RuntimeError("key leaked into receipt")
    dest = out or DEFAULT_OUT
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(encoded + "\n", encoding="utf-8")
    receipt["out"] = str(dest)
    return receipt


def _masked_vs_unmasked(
    unmasked: list[Mapping[str, Any]],
    masked: list[Mapping[str, Any]],
) -> dict[str, Any]:
    if not unmasked or not masked:
        return {
            "n_paired": 0,
            "admit_choice_agree": None,
            "ran": False,
            "reason": "no_posts",
        }
    by_m = {int(row["ticket"]): row for row in masked}
    paired = []
    agree = 0
    for row in unmasked:
        other = by_m.get(int(row["ticket"]))
        if not other:
            continue
        same = row.get("admit_choice") == other.get("admit_choice")
        if same:
            agree += 1
        paired.append(
            {
                "ticket": row["ticket"],
                "unmasked": row.get("admit_choice"),
                "masked": other.get("admit_choice"),
                "agree": same,
            }
        )
    n = len(paired)
    return {
        "n_paired": n,
        "admit_choice_agree": f"{agree}/{n}" if n else None,
        "admit_choice_agree_n": agree,
        "ran": True,
        "pairs": paired,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--max-posts", type=int, default=None)
    parser.add_argument("--skip-unauth", action="store_true")
    args = parser.parse_args(argv)
    receipt = run_probe(
        jsonl=args.jsonl,
        out=args.out,
        timeout_s=args.timeout,
        max_posts=args.max_posts,
        skip_unauth=args.skip_unauth,
    )
    public = {
        "schema": receipt["schema"],
        "archive_ask": receipt["archive_ask"],
        "book": receipt["book"],
        "model": receipt["model"],
        "seat": receipt["seat"],
        "persist_weight": receipt["persist_weight"],
        "noul_every_tick": receipt["noul_every_tick"],
        "one_post": receipt["one_post"],
        "planned_calls": receipt["planned_calls"],
        "key_present": receipt["key_present"],
        "key_source": receipt["key_source"],
        "key_fingerprint": receipt["key_fingerprint"],
        "blocker": receipt["blocker"],
        "unauthenticated_http": (receipt.get("unauthenticated_post") or {}).get("http_status"),
        "archived": receipt["archived_20260917"],
        "n_posted": receipt["n_posted"],
        "masked_vs_unmasked": {
            k: v
            for k, v in (receipt.get("masked_vs_unmasked") or {}).items()
            if k != "pairs"
        },
        "determinism_tickets": list((receipt.get("determinism") or {}).keys()),
        "out": receipt.get("out"),
    }
    print(json.dumps(public, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
