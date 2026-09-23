"""Chair G1–G8 ENFORCE surface for S14 admit/size labels.

Every decision on this surface, including every parameter, is the System
One return for that state. One call: ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False``. That call POSTs
https://api.typesafe.ai/v1/systemone. Questions are only Noul, Choice, or
Score. Prior outcomes are attached on the ask, and the return is stored
for the next ask.

An empty answer, a tie, or an error leaves that return unset. Floor and
baseline are not a question. Marker lists, the chair file, and occupancy
are facts on the state. Membership in a marker list is not a verdict.
This module does not send. Judge code cannot send.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0

CHAIR_ENFORCE_PATH = (
    Path(__file__).resolve().parents[2] / "judgment" / "astra" / "chair_enforce_g1_g8.json"
)

INDEX_SLEEVE_MARKERS = ("idxrev",)
INDEX_SYMBOL_PREFIXES = ("US30",)
_NAMED_HARD_OFF = ("orb_",)
_NAMED_KEEP = ("dsp_spring", "vss_fxcross")
REASON_MARKERS = ("idxrev", "xa_huge", "orb_crypto", "orb_", "bleed", "mx_us30")

try:
    from .challenge import (
        CHALLENGE_HARD_OFF_FAMILIES as _HARD_FAMILIES,
        CHALLENGE_KEEP_FAMILIES as _KEEP_FAMILIES,
    )
except Exception:
    _HARD_FAMILIES = ()
    _KEEP_FAMILIES = ()


def _name_tuple(raw: Any) -> tuple[str, ...]:
    if raw is None or isinstance(raw, (str, bytes)):
        return ()
    try:
        return tuple(str(item) for item in raw)
    except TypeError:
        return ()


CHALLENGE_HARD_OFF_FAMILIES = _name_tuple(_HARD_FAMILIES)
CHALLENGE_KEEP_FAMILIES = _name_tuple(_KEEP_FAMILIES)
HARD_OFF_MARKERS = tuple(dict.fromkeys(CHALLENGE_HARD_OFF_FAMILIES + _NAMED_HARD_OFF))
KEEP_MARKERS = tuple(dict.fromkeys(CHALLENGE_KEEP_FAMILIES + _NAMED_KEEP))

G6_CUT_SESSIONS = frozenset({"London", "NY", "London_NY_overlap", "Asia", "london", "ny", "asia"})
G6_LEAVE_ALONE = frozenset({"Asia_London_pre", "Off_hours", "asia_london_pre", "off_hours"})

FLUID_STAMPS_OBSERVE = (
    "FLUID-ADM-002",
    "FLUID-ADM-007",
    "FLUID-PLC-001",
    "f5_xau_flow_alignment_size_tilt",
    "FLUID-SIZ-008",
)

_GATES = ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8")
_ENFORCE_ORDER = ("ENFORCE", "NOT_APPLICABLE")
_G5_ORDER = ("SHADOW", "NOT_APPLICABLE")
_G4_ORDER = ("KEEP_EXEMPT", "APPLY_CUT_0_5", "NOT_APPLICABLE")
_G6_ORDER = ("LEAVE_ALONE", "KEEP_EXEMPT", "APPLY_CUT_0_75", "NOT_APPLICABLE")
_G7_ORDER = ("ALLOW_NO_BOOST", "NOT_APPLICABLE")
_G8_ORDER = ("BLOCK_REENTRY", "ALLOW_REENTRY", "NOT_APPLICABLE")
_REASON_ORDER = (
    "chair_g_index_hard_off",
    "chair_xa_huge_hard_off",
    "chair_orb_crypto_hard_off",
    "chair_bleed_hard_off",
    "chair_mx_us30_hard_off",
    "chair_hard_off_family",
    "none",
)
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)

_HARD_OFF_ID = "chair_enforce_hard_off"
_HARD_OFF_SLEEVE_ID = "chair_enforce_hard_off_sleeve"
_INDEX_ID = "chair_enforce_index_hard_off"
_KEEP_ID = "chair_enforce_keep_family"
_NO_BOOST_ID = "chair_enforce_keep_no_boost"
_G8_BLOCK_ID = "chair_enforce_g8_block"
_G8_NOUL_ID = "chair_enforce_g8_noul"
_PRESENT_ID = "chair_enforce_present"
_REASON_ID = "chair_enforce_reason"
_G4_CEILING_ID = "chair_enforce_g4_ceiling"
_G6_CEILING_ID = "chair_enforce_g6_ceiling"
_G7_CEILING_ID = "chair_enforce_g7_ceiling"
_SIZE_CEILING_ID = "chair_enforce_size_ceiling"
_THRESHOLD_ID = "chair_enforce_threshold"
_LOOP_ID = "chair_enforce_loop"
_PARAMETER_ID = "chair_enforce_parameter"

_LIMIT_KEYS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "flatten_floor_usd",
    "daily_loss_pct",
    "floor_room",
    "to_pass",
})
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
_SKIP_PARTS = ("floor", "baseline")

# History only when jev_questions cannot be imported. Never copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []
_DROP = object()


def _gate_id(gate: str) -> str:
    return f"chair_enforce_{gate.lower()}"


@dataclass(frozen=True)
class ChairEnforceStamp:
    """Constraints read from one ask. Never a broker send."""

    hard_off: bool | float | None
    hard_off_reason: str | None
    keep_family: bool | float | None
    keep_no_boost: bool | float | None
    g4_size_ceiling: float | None
    g6_size_ceiling: float | None
    g7_size_ceiling: float | None
    g8_block_reentry: bool | float | None
    size_ceiling: float | None
    decisions: dict[str, str | None]
    notes: tuple[str, ...]
    g4_soft_label: str | None = None
    g6_soft_label: str | None = None
    g8_block_noul: bool | float | None = None
    hard_off_sleeve: bool | float | None = None
    index_hard_off: bool | float | None = None
    present: bool | float | None = None
    threshold: float | None = None
    loop_bound: float | None = None
    parameter: float | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "hard_off": self.hard_off,
            "hard_off_reason": self.hard_off_reason,
            "hard_off_sleeve": self.hard_off_sleeve,
            "index_hard_off": self.index_hard_off,
            "keep_family": self.keep_family,
            "keep_no_boost": self.keep_no_boost,
            "g4_size_ceiling": self.g4_size_ceiling,
            "g6_size_ceiling": self.g6_size_ceiling,
            "g7_size_ceiling": self.g7_size_ceiling,
            "g8_block_reentry": self.g8_block_reentry,
            "size_ceiling": self.size_ceiling,
            "g4_soft_label": self.g4_soft_label,
            "g6_soft_label": self.g6_soft_label,
            "g8_block_noul": self.g8_block_noul,
            "present": self.present,
            "threshold": self.threshold,
            "loop_bound": self.loop_bound,
            "parameter": self.parameter,
            "decisions": dict(self.decisions),
            "notes": list(self.notes),
            "fluid_stamps_observe": list(FLUID_STAMPS_OBSERVE),
            "soft_labels_shadow_never_apply_ceiling": True,
            "place": False,
            "broker_effect": False,
            "login": CHALLENGE_LOGIN,
            "namespace": CHALLENGE_NS,
            "magic": CHALLENGE_MAGIC,
            "model": MODEL,
        }


def load_chair_enforce(path: Path | None = None) -> dict[str, Any]:
    """Read the chair file. A missing file is an empty fact, not a verdict."""

    target = path if path is not None else CHAIR_ENFORCE_PATH
    if target.is_file():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            loaded = None
        if isinstance(loaded, dict):
            return loaded
    return {
        "schema": "gtos.chair.enforce.v1",
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "decisions": {},
        "file_present": False,
    }


def _contains_marker(name: str, markers: tuple[str, ...]) -> bool:
    """Name-menu membership. A fact for the ask, not the verdict."""

    raw = str(name or "").strip().lower()
    if not raw:
        return False
    for marker in markers:
        token = str(marker).lower()
        if raw == token or raw.startswith(token) or f"_{token}" in raw or raw.startswith(f"{token}_"):
            return True
    return False


def _symbol_index(symbol: str) -> bool:
    sym = str(symbol or "").strip().upper()
    if not sym:
        return False
    return any(sym == prefix or sym.startswith(prefix) for prefix in INDEX_SYMBOL_PREFIXES)


def _in_set(name: str, catalog: frozenset[str]) -> bool:
    if not name:
        return False
    folded = {item.lower() for item in catalog}
    return name in catalog or name.lower() in folded


def _file_status(doc: Mapping[str, Any]) -> dict[str, str]:
    raw = doc.get("decisions") if isinstance(doc.get("decisions"), Mapping) else {}
    out: dict[str, str] = {}
    for key in _GATES:
        block = raw.get(key)
        status: Any = None
        if isinstance(block, Mapping):
            status = block.get("status")
        elif isinstance(block, str):
            status = block
        if status in (None, ""):
            continue
        out[key] = str(status)
    return out


def _limit_key(name: str) -> bool:
    token = str(name).strip().lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    return any(token.replace(",", "").replace("_", "").lower() in compact for token in _BANNED_TEXT)


def _scrub_text(value: str) -> str | None:
    if _banned_text(value) or any(part in value.lower() for part in _SKIP_PARTS):
        return None
    return value


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before the ask."""

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
        cleaned = _scrub_text(value)
        if cleaned is None:
            return _DROP
        return cleaned
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if _banned_text(format(value, ".10g")):
            return _DROP
        return value
    return str(value)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        number = _number(val)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision. A miss is not zero."""

    allowed = [name for name in order if name in probabilities]
    if not allowed:
        return None
    best = max(probabilities[name] for name in allowed)
    winners = [name for name in allowed if abs(probabilities[name] - best) <= 1e-12]
    if len(winners) != 1:
        return None
    return winners[0]


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    """The choice is the unique highest probability. A bare label is not a choice."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    probabilities = _probabilities(block)
    kept = {name: probabilities[name] for name in order if name in probabilities}
    local = _unique(kept, order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(kept or None, order)
    except Exception:
        picked = local
    if local is None or picked is None or str(picked) != local or str(picked) not in order:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if block is True or block is False:
        return block
    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        value = block.get("noul") if "noul" in block else block.get("Noul")
        if value is None:
            return None
        if value is True or value is False:
            return value
        return _number(value)
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The parameter is the returned score. A missing score stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _number(returned_number(block))
    except Exception:
        raw = block.get("score")
        if raw is None:
            raw = block.get("value")
        return _number(raw)


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions) or ""
    cleaned = {
        str(key): str(val)
        for key, val in criteria.items()
        if _scrub_text(str(key)) is not None and _scrub_text(str(val)) is not None
    }
    block: dict[str, Any] = {}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, cleaned)
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        block = {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    block["type"] = "choice"
    block["instructions"] = text
    block["criteria"] = cleaned
    return {qid: block}


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    text = _scrub_text(instructions) or ""
    block: dict[str, Any] = {}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, text)
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        block = {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    criteria = block.get("criteria")
    kept: list[str] = []
    if isinstance(criteria, list):
        for item in criteria:
            token = str(item)
            if _scrub_text(token) is None or _limit_key(token):
                continue
            kept.append(token)
    if not kept:
        kept = list(_BETWEEN)
    block["type"] = "score"
    block["instructions"] = text
    block["criteria"] = kept
    return {qid: block}


def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(instructions) or "",
            "criteria": {
                "true": _scrub_text(yes) or "",
                "false": _scrub_text(no) or "",
            },
        }
    }


def _questions() -> dict[str, Any]:
    """One pack. Types are noul, choice, or score."""

    pack: dict[str, Any] = {}
    pack.update(_noul_question(
        _HARD_OFF_ID,
        "Is this sleeve and symbol a hard-off on this state? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "This sleeve and symbol are a hard-off.",
        "This sleeve and symbol are not a hard-off.",
    ))
    pack.update(_noul_question(
        _HARD_OFF_SLEEVE_ID,
        "Is this sleeve a hard-off sleeve on this state? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "This sleeve is a hard-off sleeve.",
        "This sleeve is not a hard-off sleeve.",
    ))
    pack.update(_noul_question(
        _INDEX_ID,
        "Is this an index hard-off on this state? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "This is an index hard-off.",
        "This is not an index hard-off.",
    ))
    pack.update(_noul_question(
        _KEEP_ID,
        "Is this sleeve a keep family on this state? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "This sleeve is a keep family.",
        "This sleeve is not a keep family.",
    ))
    pack.update(_noul_question(
        _NO_BOOST_ID,
        "Does this state allow the keep surface only with no boost? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "The keep surface allows no boost.",
        "The keep surface does not allow no boost.",
    ))
    pack.update(_noul_question(
        _G8_BLOCK_ID,
        "Does this state block same-sleeve reentry? "
        "Occupancy on this state is a fact. "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "Same-sleeve reentry is blocked.",
        "Same-sleeve reentry is not blocked.",
    ))
    pack.update(_noul_question(
        _G8_NOUL_ID,
        "What noul applies to blocking same-sleeve reentry on this state? "
        "A probability is kept as returned. "
        "Occupancy on this state is a fact. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "Reentry block is present.",
        "Reentry block is not present.",
    ))
    pack.update(_noul_question(
        _PRESENT_ID,
        "Does the chair enforce component exist for this state? "
        "The noul you return is that existence. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "The chair enforce component exists for this state.",
        "The chair enforce component does not exist for this state.",
    ))
    pack.update(_choice_question(
        _REASON_ID,
        "Which hard-off reason is this state? "
        "The option with the single highest probability is the reason. "
        "An empty answer or a tie leaves the reason unset. "
        "This question does not send.",
        {
            "chair_g_index_hard_off": "Index sleeve or US30 symbol hard-off.",
            "chair_xa_huge_hard_off": "xa_huge hard-off.",
            "chair_orb_crypto_hard_off": "orb crypto hard-off.",
            "chair_bleed_hard_off": "bleed hard-off.",
            "chair_mx_us30_hard_off": "mx_us30 hard-off.",
            "chair_hard_off_family": "Another hard-off family.",
            "none": "No hard-off reason.",
        },
    ))
    for gate, order, noun in (
        ("G1", _ENFORCE_ORDER, "G1"),
        ("G2", _ENFORCE_ORDER, "G2"),
        ("G3", _ENFORCE_ORDER, "G3"),
        ("G5", _G5_ORDER, "G5"),
        ("G7", _G7_ORDER, "G7"),
        ("G8", _G8_ORDER, "G8"),
    ):
        criteria = {name: f"{noun} label {name} on this state." for name in order}
        pack.update(_choice_question(
            _gate_id(gate),
            f"Which {noun} label applies on this state? "
            "The chair file status is a fact, not this label. "
            "The option with the single highest probability is the label. "
            "An empty answer or a tie leaves the label unset. "
            "This question does not send.",
            criteria,
        ))
    pack.update(_choice_question(
        _gate_id("G4"),
        "Which G4 label applies on this state? "
        "The option with the single highest probability is the label. "
        "An empty answer or a tie leaves the label unset. "
        "This question does not send.",
        {
            "KEEP_EXEMPT": "Keep exempts G4 on this state.",
            "APPLY_CUT_0_5": "G4 applies a cut on this state.",
            "NOT_APPLICABLE": "G4 does not apply on this state.",
        },
    ))
    pack.update(_choice_question(
        _gate_id("G6"),
        "Which G6 label applies on this state? "
        "The session name is a fact. "
        "The option with the single highest probability is the label. "
        "An empty answer or a tie leaves the label unset. "
        "This question does not send.",
        {
            "LEAVE_ALONE": "This session is left alone.",
            "KEEP_EXEMPT": "Keep exempts G6 on this state.",
            "APPLY_CUT_0_75": "G6 applies a cut on this state.",
            "NOT_APPLICABLE": "G6 does not apply on this state.",
        },
    ))
    pack.update(_score_question(
        _G4_CEILING_ID,
        "The score you return is the G4 size ceiling for this state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the ceiling unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _G6_CEILING_ID,
        "The score you return is the G6 size ceiling for this state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the ceiling unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _G7_CEILING_ID,
        "The score you return is the G7 size ceiling for this state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the ceiling unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _SIZE_CEILING_ID,
        "The score you return is the enforce size ceiling for this state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the ceiling unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _THRESHOLD_ID,
        "The score you return is the threshold for this enforce state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the threshold unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _LOOP_ID,
        "The score you return is the loop bound for this enforce state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the loop bound unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _PARAMETER_ID,
        "The score you return is the parameter for this enforce state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the parameter unset. "
        "This question does not send.",
    ))
    return pack


def _pack_ok(questions: Mapping[str, Any]) -> bool:
    allowed = {"noul", "choice", "score"}
    if not questions:
        return False
    for qid, block in questions.items():
        if _limit_key(str(qid)):
            return False
        if not isinstance(block, dict) or str(block.get("type") or "") not in allowed:
            return False
        try:
            text = json.dumps(block, default=str).lower()
        except Exception:
            return False
        if any(part in text for part in _SKIP_PARTS) or _banned_text(text):
            return False
    return True


def _occupancy_facts(occupancy: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(occupancy, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, value in occupancy.items():
        if _limit_key(str(key)):
            continue
        out[str(key)] = value
    return out


def _state(
    *,
    sleeve: str | None = None,
    symbol: str | None = None,
    session_named: str | None = None,
    occupancy: Mapping[str, Any] | None = None,
    chair_doc: Mapping[str, Any] | None = None,
    g4_applies: bool | None = None,
    keep_named: bool | None = None,
) -> dict[str, Any]:
    if chair_doc is not None:
        doc: Mapping[str, Any] = chair_doc
        file_present = True
    else:
        doc = load_chair_enforce()
        if "file_present" in doc:
            file_present = bool(doc.get("file_present"))
        else:
            file_present = True
    sleeve_text = None if sleeve is None else str(sleeve)
    symbol_text = None if symbol is None else str(symbol)
    session_text = str(session_named or "").strip()
    raw_keep = str(sleeve_text or "").strip().lower()
    keep_names = {item.lower() for item in CHALLENGE_KEEP_FAMILIES}
    body: dict[str, Any] = {
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "sleeve": sleeve_text,
        "symbol": symbol_text,
        "session_named": session_text or None,
        "g4_applies": g4_applies,
        "keep_named": keep_named,
        "occupancy": _occupancy_facts(occupancy),
        "file_present": file_present,
        "file_gate_status": _file_status(doc),
        "hard_off_markers": list(HARD_OFF_MARKERS),
        "keep_markers": list(KEEP_MARKERS),
        "reason_markers": list(REASON_MARKERS),
        "index_sleeve_markers": list(INDEX_SLEEVE_MARKERS),
        "index_symbol_prefixes": list(INDEX_SYMBOL_PREFIXES),
        "g6_cut_sessions": sorted(G6_CUT_SESSIONS),
        "g6_leave_alone": sorted(G6_LEAVE_ALONE),
        "fluid_stamps_observe": list(FLUID_STAMPS_OBSERVE),
        "sleeve_matches_hard_off_marker": _contains_marker(sleeve_text or "", HARD_OFF_MARKERS),
        "sleeve_matches_keep_marker": _contains_marker(sleeve_text or "", KEEP_MARKERS),
        "sleeve_in_keep_families": bool(raw_keep) and raw_keep in keep_names,
        "sleeve_matches_index_marker": _contains_marker(sleeve_text or "", INDEX_SLEEVE_MARKERS),
        "symbol_matches_index_prefix": _symbol_index(symbol_text or ""),
        "session_in_cut_catalog": _in_set(session_text, G6_CUT_SESSIONS),
        "session_in_leave_catalog": _in_set(session_text, G6_LEAVE_ALONE),
        "identity": {
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "magic": CHALLENGE_MAGIC,
        },
    }
    cleaned = _scrub(body)
    state = cleaned if isinstance(cleaned, dict) else {}
    state["model"] = MODEL
    state["login"] = CHALLENGE_LOGIN
    state["namespace"] = CHALLENGE_NS
    state["ns"] = CHALLENGE_NS
    state["magic"] = CHALLENGE_MAGIC
    return state


def _local_priors() -> list[dict[str, Any]]:
    return [dict(item) for item in _LOCAL_OUTCOMES]


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = _local_priors()
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    error = row.get("error")
    err = None if error in (None, "") else str(error)
    pairs = (
        (_HARD_OFF_ID, row.get("hard_off")),
        (_HARD_OFF_SLEEVE_ID, row.get("hard_off_sleeve")),
        (_INDEX_ID, row.get("index_hard_off")),
        (_KEEP_ID, row.get("keep_family")),
        (_NO_BOOST_ID, row.get("keep_no_boost")),
        (_G8_BLOCK_ID, row.get("g8_block_reentry")),
        (_G8_NOUL_ID, row.get("g8_block_noul")),
        (_PRESENT_ID, row.get("present")),
        (_REASON_ID, row.get("hard_off_reason")),
        (_gate_id("G1"), row.get("g1")),
        (_gate_id("G2"), row.get("g2")),
        (_gate_id("G3"), row.get("g3")),
        (_gate_id("G4"), row.get("g4")),
        (_gate_id("G5"), row.get("g5")),
        (_gate_id("G6"), row.get("g6")),
        (_gate_id("G7"), row.get("g7")),
        (_gate_id("G8"), row.get("g8")),
        (_G4_CEILING_ID, row.get("g4_size_ceiling")),
        (_G6_CEILING_ID, row.get("g6_size_ceiling")),
        (_G7_CEILING_ID, row.get("g7_size_ceiling")),
        (_SIZE_CEILING_ID, row.get("size_ceiling")),
        (_THRESHOLD_ID, row.get("threshold")),
        (_LOOP_ID, row.get("loop_bound")),
        (_PARAMETER_ID, row.get("parameter")),
    )
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value in pairs:
            _LOCAL_OUTCOMES.append({
                "spot": key,
                "value": value,
                "error": None if value is not None else (err or "unset"),
            })
        return
    for key, value in pairs:
        try:
            append_outcome(key, value, logged, error=None if value is not None else (err or "unset"))
        except Exception:
            return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> dict[str, Any]:
    call = evaluate_fn
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    receipt = call(state, questions=dict(questions), merge_sleeve=False, model=MODEL)
    return receipt if isinstance(receipt, dict) else {"error": "evaluate_not_a_dict", "answers": {}}


def _blank_row(error: str | None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "hard_off": None,
        "hard_off_sleeve": None,
        "index_hard_off": None,
        "keep_family": None,
        "keep_no_boost": None,
        "g8_block_reentry": None,
        "g8_block_noul": None,
        "present": None,
        "hard_off_reason": None,
        "g1": None,
        "g2": None,
        "g3": None,
        "g4": None,
        "g5": None,
        "g6": None,
        "g7": None,
        "g8": None,
        "g4_size_ceiling": None,
        "g6_size_ceiling": None,
        "g7_size_ceiling": None,
        "size_ceiling": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "error": error,
        "model": MODEL,
    }
    return row


def _read(answers: Mapping[str, Any], error: str | None) -> dict[str, Any]:
    row = _blank_row(error)
    row["hard_off"] = _noul(answers.get(_HARD_OFF_ID))
    row["hard_off_sleeve"] = _noul(answers.get(_HARD_OFF_SLEEVE_ID))
    row["index_hard_off"] = _noul(answers.get(_INDEX_ID))
    row["keep_family"] = _noul(answers.get(_KEEP_ID))
    row["keep_no_boost"] = _noul(answers.get(_NO_BOOST_ID))
    row["g8_block_reentry"] = _noul(answers.get(_G8_BLOCK_ID))
    row["g8_block_noul"] = _noul(answers.get(_G8_NOUL_ID))
    row["present"] = _noul(answers.get(_PRESENT_ID))
    row["hard_off_reason"] = _choice(answers.get(_REASON_ID), _REASON_ORDER)
    row["g1"] = _choice(answers.get(_gate_id("G1")), _ENFORCE_ORDER)
    row["g2"] = _choice(answers.get(_gate_id("G2")), _ENFORCE_ORDER)
    row["g3"] = _choice(answers.get(_gate_id("G3")), _ENFORCE_ORDER)
    row["g4"] = _choice(answers.get(_gate_id("G4")), _G4_ORDER)
    row["g5"] = _choice(answers.get(_gate_id("G5")), _G5_ORDER)
    row["g6"] = _choice(answers.get(_gate_id("G6")), _G6_ORDER)
    row["g7"] = _choice(answers.get(_gate_id("G7")), _G7_ORDER)
    row["g8"] = _choice(answers.get(_gate_id("G8")), _G8_ORDER)
    row["g4_size_ceiling"] = _score(answers.get(_G4_CEILING_ID))
    row["g6_size_ceiling"] = _score(answers.get(_G6_CEILING_ID))
    row["g7_size_ceiling"] = _score(answers.get(_G7_CEILING_ID))
    row["size_ceiling"] = _score(answers.get(_SIZE_CEILING_ID))
    row["threshold"] = _score(answers.get(_THRESHOLD_ID))
    row["loop_bound"] = _score(answers.get(_LOOP_ID))
    row["parameter"] = _score(answers.get(_PARAMETER_ID))
    return row


def _evaluate(
    state: dict[str, Any],
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One ask for this state. A miss stays unset. Never sends."""

    try:
        questions = _questions()
    except Exception as exc:
        row = _blank_row(type(exc).__name__)
        _remember(state, row)
        return row
    if not _pack_ok(questions):
        row = _blank_row("question_rejected")
        _remember(state, row)
        return row
    _attach_priors(state, questions)
    priors = _scrub(state.get("prior_outcomes"))
    state["prior_outcomes"] = [] if priors is _DROP or priors is None else priors
    try:
        receipt = _post(state, questions, evaluate_fn)
    except Exception as exc:
        row = _blank_row(type(exc).__name__)
        _remember(state, row)
        return row
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    if not answers:
        row = _blank_row(None if error in (None, "") else str(error))
        if receipt.get("model"):
            row["model"] = receipt.get("model")
        _remember(state, row)
        return row
    row = _read(answers, None if error in (None, "") else str(error))
    if receipt.get("model"):
        row["model"] = receipt.get("model")
    _remember(state, row)
    return row


def _stamp_from_row(row: Mapping[str, Any]) -> ChairEnforceStamp:
    decisions = {gate: row.get(gate.lower()) for gate in _GATES}
    notes = ["labels_only_no_send"]
    if row.get("error") not in (None, ""):
        notes.append(str(row.get("error")))
    return ChairEnforceStamp(
        hard_off=row.get("hard_off"),
        hard_off_reason=row.get("hard_off_reason") if isinstance(row.get("hard_off_reason"), str) else None,
        keep_family=row.get("keep_family"),
        keep_no_boost=row.get("keep_no_boost"),
        g4_size_ceiling=row.get("g4_size_ceiling"),
        g6_size_ceiling=row.get("g6_size_ceiling"),
        g7_size_ceiling=row.get("g7_size_ceiling"),
        g8_block_reentry=row.get("g8_block_reentry"),
        size_ceiling=row.get("size_ceiling"),
        decisions=decisions,
        notes=tuple(notes),
        g4_soft_label=row.get("g4") if isinstance(row.get("g4"), str) else None,
        g6_soft_label=row.get("g6") if isinstance(row.get("g6"), str) else None,
        g8_block_noul=row.get("g8_block_noul"),
        hard_off_sleeve=row.get("hard_off_sleeve"),
        index_hard_off=row.get("index_hard_off"),
        present=row.get("present"),
        threshold=row.get("threshold"),
        loop_bound=row.get("loop_bound"),
        parameter=row.get("parameter"),
    )


def is_hard_off_sleeve(
    sleeve: str | None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> bool | float | None:
    """Hard-off sleeve noul for this state. A miss stays unset."""

    state = _state(sleeve=sleeve)
    return _evaluate(state, evaluate_fn).get("hard_off_sleeve")


def is_index_hard_off(
    *,
    sleeve: str | None,
    symbol: str | None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> bool | float | None:
    """Index hard-off noul for this state. A miss stays unset."""

    state = _state(sleeve=sleeve, symbol=symbol)
    return _evaluate(state, evaluate_fn).get("index_hard_off")


def is_keep_family(
    sleeve: str | None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> bool | float | None:
    """Keep-family noul for this state. A miss stays unset."""

    state = _state(sleeve=sleeve)
    return _evaluate(state, evaluate_fn).get("keep_family")


def hard_off_reason(
    *,
    sleeve: str | None,
    symbol: str | None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> str | None:
    """Hard-off reason for this state. The unique highest probability, or unset."""

    state = _state(sleeve=sleeve, symbol=symbol)
    reason = _evaluate(state, evaluate_fn).get("hard_off_reason")
    if reason in _REASON_ORDER:
        return str(reason)
    return None


def soft_g4_choice(
    *,
    g4_applies: bool,
    keep: bool,
    evaluate_fn: Callable[..., Any] | None = None,
) -> str | None:
    """G4 label for this state. A miss stays unset. The ceiling is a separate score."""

    state = _state(g4_applies=g4_applies, keep_named=keep)
    label = _evaluate(state, evaluate_fn).get("g4")
    if label in _G4_ORDER:
        return str(label)
    return None


def soft_g6_choice(
    *,
    session_named: str | None,
    keep: bool,
    evaluate_fn: Callable[..., Any] | None = None,
) -> str | None:
    """G6 label for this state. A miss stays unset. The ceiling is a separate score."""

    state = _state(session_named=session_named, keep_named=keep)
    label = _evaluate(state, evaluate_fn).get("g6")
    if label in _G6_ORDER:
        return str(label)
    return None


def soft_g8_noul(
    occupancy: Mapping[str, Any] | None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> bool | float | None:
    """Reentry-block noul for this occupancy. A miss stays unset."""

    state = _state(occupancy=occupancy)
    return _evaluate(state, evaluate_fn).get("g8_block_noul")


def stamp_chair_enforce(
    *,
    sleeve: str | None,
    symbol: str | None,
    session_named: str | None = None,
    occupancy: Mapping[str, Any] | None = None,
    chair_doc: Mapping[str, Any] | None = None,
    g4_applies: bool = False,
    evaluate_fn: Callable[..., Any] | None = None,
) -> ChairEnforceStamp:
    """One ask. Labels and ceilings are that return. A miss stays unset. Never sends."""

    state = _state(
        sleeve=sleeve,
        symbol=symbol,
        session_named=session_named,
        occupancy=occupancy,
        chair_doc=chair_doc,
        g4_applies=g4_applies,
    )
    try:
        row = _evaluate(state, evaluate_fn)
    except Exception as exc:
        row = _blank_row(type(exc).__name__)
    return _stamp_from_row(row)


__all__ = [
    "CHAIR_ENFORCE_PATH",
    "CHALLENGE_HARD_OFF_FAMILIES",
    "CHALLENGE_KEEP_FAMILIES",
    "CHALLENGE_LOGIN",
    "CHALLENGE_MAGIC",
    "CHALLENGE_NS",
    "FLUID_STAMPS_OBSERVE",
    "G6_CUT_SESSIONS",
    "G6_LEAVE_ALONE",
    "HARD_OFF_MARKERS",
    "INDEX_SLEEVE_MARKERS",
    "INDEX_SYMBOL_PREFIXES",
    "KEEP_MARKERS",
    "MODEL",
    "REASON_MARKERS",
    "ChairEnforceStamp",
    "hard_off_reason",
    "is_hard_off_sleeve",
    "is_index_hard_off",
    "is_keep_family",
    "load_chair_enforce",
    "soft_g4_choice",
    "soft_g6_choice",
    "soft_g8_noul",
    "stamp_chair_enforce",
]
