"""Named sleeve features from Challenge-true bars.

``ac60`` is autocorr(M15, 60) at the last closed bar <= as-of — the same
primitive metals.py uses. A8 field numbers come from metals._a8_features
when those bars are present. Missing bars stay None.

The score, the threshold, the loop bound, the parameter, the A8 pass,
the source, whether the features are named, and which component exists
are the System One return for this state. One hop: ``jev_client.evaluate``
with model ``jev-1.13.0`` (POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``). Questions are only a Noul, a Choice, or a Score.
Prior outcomes are attached on that ask and the return is stored for the
next ask. An empty answer, a tie, or an error leaves that return unset.
A floor and a baseline are not a question. This module does not send.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

MODEL = "jev-1.13.0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

_AC_SOURCE = ("challenge_m15", "unassembled")
_A8_SOURCE = ("challenge_m15_metals_a8", "unassembled")
_COMPONENT = ("sleeve_from_tape", "absent")
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
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
_LEVEL_KEYS = (
    "measured_ac60",
    "measured_vol_ratio",
    "measured_htf_slope_norm",
    "measured_mom_20_atr",
    "measured_fvg_freshness_bars",
    "measured_session_hour",
)
_FEATURE_SPEC = (
    ("ac60_source", "choice", "sleeve_ac60_source", _AC_SOURCE),
    ("a8_source", "choice", "sleeve_a8_source", _A8_SOURCE),
    ("a8_pass", "noul", "sleeve_a8_pass", ("true", "false")),
    ("features_named", "noul", "sleeve_named", ("true", "false")),
    ("component", "choice", "sleeve_component", _COMPONENT),
    ("component_present", "noul", "sleeve_component_present", ("true", "false")),
    ("ac60_score", "score", "sleeve_ac60_score", None),
    ("ac60_threshold", "score", "sleeve_ac60_threshold", None),
    ("loop_bound", "score", "sleeve_loop", None),
    ("sleeve_parameter", "score", "sleeve_parameter", None),
)


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _scrub(value: Any) -> Any:
    """Drop floor and baseline keys before an ask."""

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


def _unique(probs: Mapping[str, Any] | None, order: tuple[str, ...] | None) -> str | None:
    """Unique highest probability. A missing probability is not zero.

    An empty map is not a decision. A tie is not a decision.
    """

    if not isinstance(probs, Mapping) or not probs:
        return None
    names = tuple(str(name) for name in order) if order else tuple(str(name) for name in probs)
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
        try:
            p = float(raw)
        except (TypeError, ValueError):
            continue
        if p != p:
            continue
        seen = True
        if best_p is None or p > best_p + 1e-12:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
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
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(probs, order)
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
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The Score that came back. It is not snapped to a level."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        pass
    if "score" in block and block.get("score") is not None:
        return _finite(block.get("score"))
    probs = block.get("probabilities")
    if isinstance(probs, Mapping) and probs:
        name = _unique(probs, None)
        if name is None:
            return None
        return _finite(probs.get(name))
    return None


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
        usable = 0
        for name in menu:
            raw = probs.get(name)
            if raw is None or isinstance(raw, bool):
                continue
            try:
                p = float(raw)
            except (TypeError, ValueError):
                continue
            if p == p:
                usable += 1
        if usable >= 2:
            return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Numbers already on the measured facts. A score may sit between them."""

    found: list[float] = []
    for key in _LEVEL_KEYS:
        if _limit_key(key):
            continue
        number = _finite((facts or {}).get(key))
        if number is not None:
            found.append(number)
    if not found:
        return list(_BETWEEN)
    return [format(number, ".10g") for number in sorted(set(found))]


def _blob(qid: str, spec: Mapping[str, Any]) -> str:
    parts = [str(qid), str(spec.get("instructions") or "")]
    criteria = spec.get("criteria")
    if isinstance(criteria, Mapping):
        for key, value in criteria.items():
            parts.append(str(key))
            parts.append(str(value))
    elif isinstance(criteria, (list, tuple)) and not isinstance(criteria, (str, bytes)):
        parts.extend(str(item) for item in criteria)
    return " ".join(parts)


def _asks_limit(qid: str, spec: Mapping[str, Any]) -> bool:
    """Floor and baseline are not a question. Only Noul, Choice, or Score are asked."""

    if str(spec.get("type") or "") not in {"noul", "choice", "score"}:
        return True
    if _limit_key(qid):
        return True
    blob = _blob(qid, spec).lower()
    if "floor" in blob or "baseline" in blob:
        return True
    compact = blob.replace(",", "").replace("_", "")
    for token in _BANNED_TEXT:
        probe = token.replace(",", "").replace("_", "").lower()
        if probe and probe in compact:
            return True
    return False


def _askable(questions: Mapping[str, Any]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    for qid, spec in questions.items():
        if isinstance(spec, Mapping) and not _asks_limit(str(qid), spec):
            kept = {key: val for key, val in spec.items() if not _limit_key(str(key))}
            pack[str(qid)] = kept
    return pack


def _choice_question(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    body = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): _scrub_text(str(value)) for key, value in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, body["criteria"])
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = dict(block)
            shaped["type"] = "choice"
            shaped["instructions"] = instructions
            shaped["criteria"] = dict(body["criteria"])
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, text: str, levels: Sequence[str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    criteria = [_scrub_text(str(item)) for item in levels] if levels else list(_BETWEEN)
    body = {"type": "score", "instructions": instructions, "criteria": criteria}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = dict(block)
            shaped["type"] = "score"
            shaped["instructions"] = instructions
            shaped["criteria"] = list(criteria)
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _noul_question(qid: str, text: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(text),
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _score_text(noun: str) -> str:
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "Do not send an order."
    )


def _feature_questions(state: Mapping[str, Any]) -> dict[str, Any]:
    """One pack for this book's sleeve features. Types are noul, choice, or score."""

    levels = _levels(state)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "sleeve_ac60_source",
        "Which source names the measured ac60 on this state? "
        "The measured autocorr is a fact on this state. "
        "The option you return is that source. "
        "An empty answer or a tie is not a source. "
        "Do not send an order.",
        {
            "challenge_m15": "The measured ac60 is named from the Challenge M15 bars.",
            "unassembled": "The measured ac60 is not named from those bars.",
        },
    ))
    pack.update(_choice_question(
        "sleeve_a8_source",
        "Which source names the measured A8 fields on this state? "
        "The measured field numbers are facts on this state. "
        "The option you return is that source. "
        "An empty answer or a tie is not a source. "
        "Do not send an order.",
        {
            "challenge_m15_metals_a8": "The measured A8 fields are named from the Challenge M15 metals formulas.",
            "unassembled": "The measured A8 fields are not named.",
        },
    ))
    pack.update(_noul_question(
        "sleeve_a8_pass",
        "Do the named A8 fields pass confluence on this state? "
        "The noul you return is that pass. "
        "An empty answer leaves it unset. "
        "Do not send an order.",
        "The named A8 fields pass confluence.",
        "The named A8 fields do not pass confluence.",
    ))
    pack.update(_noul_question(
        "sleeve_named",
        "Are the measured bars complete enough to name these sleeve features? "
        "An empty answer leaves it unset. "
        "Do not send an order.",
        "The measured bars name these sleeve features.",
        "The measured bars do not name these sleeve features.",
    ))
    pack.update(_choice_question(
        "sleeve_component",
        "Which component exists for these sleeve features on this state? "
        "The option you return is that component. "
        "An empty answer or a tie is not a component. "
        "Do not send an order.",
        {
            "sleeve_from_tape": "The sleeve-from-tape component exists for this state.",
            "absent": "That component is absent for this state.",
        },
    ))
    pack.update(_noul_question(
        "sleeve_component_present",
        "Is the sleeve-from-tape component present for this state? "
        "An empty answer leaves it unset. "
        "Do not send an order.",
        "The sleeve-from-tape component is present.",
        "The sleeve-from-tape component is not present.",
    ))
    pack.update(_score_question(
        "sleeve_ac60_score",
        _score_text("persistence score for the measured ac60"),
        levels,
    ))
    pack.update(_score_question(
        "sleeve_ac60_threshold",
        _score_text("threshold parameter for that persistence score"),
        levels,
    ))
    pack.update(_score_question(
        "sleeve_loop",
        _score_text("loop bound for how many closed bars this naming covers"),
        levels,
    ))
    pack.update(_score_question(
        "sleeve_parameter",
        _score_text("parameter for this sleeve-feature naming"),
        levels,
    ))
    return _askable(pack)


def _score_questions(state: Mapping[str, Any]) -> dict[str, Any]:
    levels = _levels(state)
    pack: dict[str, Any] = {}
    pack.update(_score_question(
        "sleeve_ac60_score",
        _score_text("persistence score for the measured ac60"),
        levels,
    ))
    pack.update(_score_question(
        "sleeve_ac60_threshold",
        _score_text("threshold parameter for that persistence score"),
        levels,
    ))
    return _askable(pack)


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _scrub(dict(state))
    if not isinstance(payload, dict):
        payload = {}
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    pack = _askable(questions)
    if not pack:
        return {"error": "no_questions", "answers": {}, "state": payload, "model": MODEL}
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=pack)
    except Exception:
        loaded = None
    payload["prior_outcomes"] = [] if loaded is None else loaded
    try:
        from .jev_client import evaluate

        receipt = evaluate(
            payload,
            questions=dict(pack),
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


def _remember(state: Mapping[str, Any], rows: Sequence[tuple[str, Any, str | None]]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _run(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    spec: Sequence[tuple[str, str, str, tuple[str, ...] | None]],
) -> dict[str, Any]:
    asked = _ask(state, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    out: dict[str, Any] = {}
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in spec:
        block = answers.get(qid)
        value = _pull(block, kind, order)
        out[field] = value
        rows.append((qid, value, _why(block, value, order, error)))
    _remember(asked.get("state") or {}, rows)
    return out


def _as_of(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iso(moment: datetime | None) -> str | None:
    if not isinstance(moment, datetime):
        return None
    try:
        return _as_of(moment).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def _closed_bars(rows: Sequence[Any] | None, as_of_utc: datetime) -> tuple[list[Any], int] | None:
    if not rows:
        return None
    try:
        from .bars import last_closed_at_or_before

        idx = last_closed_at_or_before(list(rows), _as_of(as_of_utc))
    except Exception:
        return None
    if idx is None:
        return None
    try:
        return [row.bar for row in rows[: idx + 1]], idx
    except Exception:
        return None


def ac60_at(rows: Sequence[Any] | None, as_of_utc: datetime) -> float | None:
    """Measured autocorr at lag 60. A missing bar stays missing."""

    packed = _closed_bars(rows, as_of_utc)
    if packed is None:
        return None
    bars, idx = packed
    try:
        from src.components.ultimate_book.primitives import autocorr

        return _finite(autocorr(bars, idx, 60))
    except Exception:
        return None


def vol_ratio_at(rows: Sequence[Any] | None, as_of_utc: datetime) -> float | None:
    """Measured vol ratio. A missing bar stays missing."""

    packed = _closed_bars(rows, as_of_utc)
    if packed is None:
        return None
    bars, idx = packed
    try:
        from src.components.ultimate_book.primitives import atr14, vol_ratio

        atrs = [atr14(bars, k) for k in range(len(bars))]
        return _finite(vol_ratio(atrs, idx))
    except Exception:
        return None


def _blank_a8() -> dict[str, Any]:
    return {
        "htf_slope_norm": None,
        "mom_20_atr": None,
        "fvg_freshness_bars": None,
        "session_hour": None,
        "bar_index": None,
        "closed_bars": None,
        "bar_utc": None,
    }


def _a8_fields(
    rows: Sequence[Any] | None,
    as_of_utc: datetime,
    vr: float | None,
) -> dict[str, Any]:
    """Name A8 field numbers from the metals formulas. Missing stays None.

    The pass is not decided here.
    """

    found = _blank_a8()
    packed = _closed_bars(rows, as_of_utc)
    if packed is None:
        return found
    bars, idx = packed
    found["bar_index"] = idx
    found["closed_bars"] = len(bars)
    bar_time = None
    if rows is not None and idx < len(rows):
        bar_time = getattr(rows[idx], "utc", None)
        found["bar_utc"] = _iso(bar_time) if isinstance(bar_time, datetime) else None
    if vr is None:
        return found
    try:
        from src.components.ultimate_book.primitives import atr14
        from src.components.ultimate_book.sleeves.metals import _a8_features
    except Exception:
        return found
    try:
        atrs = [atr14(bars, k) for k in range(len(bars))]
        raw = _a8_features(bars, atrs, idx, vr, bar_time)
    except Exception:
        return found
    if not isinstance(raw, Mapping):
        return found
    found["htf_slope_norm"] = raw.get("htf_slope_norm")
    found["mom_20_atr"] = raw.get("mom_20_atr")
    found["fvg_freshness_bars"] = raw.get("fvg_freshness_bars")
    found["session_hour"] = raw.get("session_hour")
    return found


def _identity(as_of_utc: datetime | None) -> dict[str, Any]:
    return {
        "model": MODEL,
        "namespace": CHALLENGE_NS,
        "login": CHALLENGE_LOGIN,
        "as_of_utc": _iso(as_of_utc),
        "identity": {
            "ns": CHALLENGE_NS,
            "login": CHALLENGE_LOGIN,
        },
    }


def _measured_state(
    measured: Mapping[str, Any],
    as_of_utc: datetime | None,
    *,
    tag: str | None = None,
    cluster: str | None = None,
) -> dict[str, Any]:
    state = _identity(as_of_utc)
    state.update(
        {
            "tag": None if tag in (None, "") else str(tag),
            "cluster": None if cluster in (None, "") else str(cluster),
            "component_name": "sleeve_from_tape",
            "measured_ac60": _finite(measured.get("ac60")),
            "measured_vol_ratio": _finite(measured.get("vol_ratio")),
            "measured_htf_slope_norm": _finite(measured.get("htf_slope_norm")),
            "measured_mom_20_atr": _finite(measured.get("mom_20_atr")),
            "measured_fvg_freshness_bars": _finite(measured.get("fvg_freshness_bars")),
            "measured_session_hour": _finite(measured.get("session_hour")),
            "bar_index": measured.get("bar_index"),
            "closed_bars": measured.get("closed_bars"),
            "bar_utc": measured.get("bar_utc"),
        }
    )
    return state


def ac60_score(ac: float | None) -> float | None:
    """Persistence score for this measured ac60. The score is the return.

    An empty answer, a tie, or an error leaves it unset.
    """

    state = _measured_state({"ac60": ac}, None)
    try:
        got = _run(
            state,
            _score_questions(state),
            (
                ("ac60_score", "score", "sleeve_ac60_score", None),
                ("ac60_threshold", "score", "sleeve_ac60_threshold", None),
            ),
        )
    except Exception:
        return None
    return _finite(got.get("ac60_score"))


def _decide_features(
    measured: Mapping[str, Any],
    as_of_utc: datetime,
    *,
    tag: str | None,
    cluster: str | None,
) -> dict[str, Any]:
    state = _measured_state(measured, as_of_utc, tag=tag, cluster=cluster)
    try:
        return _run(state, _feature_questions(state), _FEATURE_SPEC)
    except Exception:
        return {}


def features_from_books(
    books: Mapping[str, Sequence[Any]] | None,
    as_of_utc: datetime,
    *,
    tag: str | None = None,
    cluster: str | None = None,
) -> dict[str, Any]:
    """Fill measured ac60 / vol_ratio / A8 numbers. Decisions are the return.

    A missing measurement stays None. An empty answer, a tie, or an error
    leaves the decision unset.
    """

    m15 = books.get("m15") if isinstance(books, Mapping) else None
    ac = None
    vr = None
    a8 = _blank_a8()
    try:
        ac = ac60_at(m15, as_of_utc)
        vr = vol_ratio_at(m15, as_of_utc)
        a8 = _a8_fields(m15, as_of_utc, vr)
    except Exception:
        ac = None
        vr = None
        a8 = _blank_a8()
    measured = {
        "ac60": ac,
        "vol_ratio": vr,
        "htf_slope_norm": a8.get("htf_slope_norm"),
        "mom_20_atr": a8.get("mom_20_atr"),
        "fvg_freshness_bars": a8.get("fvg_freshness_bars"),
        "session_hour": a8.get("session_hour"),
        "bar_index": a8.get("bar_index"),
        "closed_bars": a8.get("closed_bars"),
        "bar_utc": a8.get("bar_utc"),
    }
    decided = _decide_features(measured, as_of_utc, tag=tag, cluster=cluster)
    return {
        "ac60": ac,
        "vol_ratio": vr,
        "atr_ratio": vr,
        "htf_slope_norm": measured.get("htf_slope_norm"),
        "mom_20_atr": measured.get("mom_20_atr"),
        "fvg_freshness_bars": measured.get("fvg_freshness_bars"),
        "a8_k_of_4_pass": decided.get("a8_pass"),
        "session_hour": measured.get("session_hour"),
        "tag": tag,
        "cluster": cluster,
        "ac60_source": decided.get("ac60_source"),
        "a8_source": decided.get("a8_source"),
        "ac60_score": decided.get("ac60_score"),
        "ac60_threshold": decided.get("ac60_threshold"),
        "loop_bound": decided.get("loop_bound"),
        "sleeve_parameter": decided.get("sleeve_parameter"),
        "features_named": decided.get("features_named"),
        "component": decided.get("component"),
        "component_present": decided.get("component_present"),
    }
