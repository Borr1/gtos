"""Gold entry. One System One ask. Each decision is the return for this state.

The post is ``jev_client.evaluate`` with model ``jev-1.13.0``
(POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
Questions are only Noul, Choice, or Score. Prior outcomes are attached
on the ask, and the return is stored for the next ask. The choice is
the unique highest probability. A score may sit between the levels.
An empty answer, a tie, or an error leaves that return unset.
A floor and a baseline are not a question. This module does not send.
One subtree for this family. The catalog stays hierarchical.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.gold_entry.v1"
CHALLENGE_LOGIN = "0"
ENTRY_ENV = "GTOS_JEV_GOLD_ENTRY"
_TRUTHY_OFF = frozenset({"0", "false", "no", "off"})
_FIRE_ORDER = ("fire", "abstain", "hard_refuse")
_DROP = object()
_LIMIT_PARTS = ("floor", "baseline")
_BANNED = ("90000", "90k", "110000", "110k")
_SECRET_PARTS = ("api_key", "typesafe", "authorization", "password", "secret")

_ENTRY_FAMILIES = (
    "sweep_reclaim",
    "ob_retest",
    "fvg_fill",
    "breaker",
    "displacement_continuation",
    "session_open",
    "news_fade",
)
_CHUNKS = {
    "sweep_reclaim": ("wick", "level", "session"),
    "ob_retest": ("zone", "impulse", "vol"),
    "fvg_fill": ("gap", "freshness", "vol"),
    "breaker": ("zone", "flip"),
    "displacement_continuation": ("range", "body"),
    "session_open": ("open_range", "session"),
    "news_fade": ("calendar", "window"),
}
_EMITTERS = {
    "sweep_reclaim": (
        "liquidity_sweep_reclaim",
        "asia_pdl_fade",
        "liq_asia_up_low_metal",
        "structural_retest_swp",
    ),
    "ob_retest": (
        "current_ob_retest",
        "metals_ob_micro",
        "structural_retest_ob",
        "fb_ob_retest_0p25d_1p5d",
    ),
    "fvg_fill": (
        "current_fvg_fill",
        "metals_core",
        "metals_softband",
        "structural_retest_fvg",
    ),
    "breaker": (
        "current_breaker_re_entry",
        "structural_retest_brk",
        "cq_breaker_inverted_5d_0p25d",
    ),
    "displacement_continuation": (
        "displacement_continuation",
        "structural_retest_disp",
    ),
    "session_open": (
        "session_open_range_break",
        "metal_session_reversion",
    ),
    "news_fade": (),
}
_EMITTER_FAMILY: dict[str, str] = {}
for _fam, _ems in _EMITTERS.items():
    for _em in _ems:
        _EMITTER_FAMILY[_em] = _fam
_EMITTER_FAMILY.update(
    {
        "liquidity_sweep_reclaim": "sweep_reclaim",
        "asia_pdl_fade": "sweep_reclaim",
        "liq_asia_up_low_metal": "sweep_reclaim",
        "current_ob_retest": "ob_retest",
        "metals_ob_micro": "ob_retest",
        "current_fvg_fill": "fvg_fill",
        "metals_core": "fvg_fill",
        "metals_softband": "fvg_fill",
        "current_breaker_re_entry": "breaker",
        "displacement_continuation": "displacement_continuation",
        "session_open_range_break": "session_open",
        "metal_session_reversion": "session_open",
        "ob_retest": "ob_retest",
        "fvg_fill": "fvg_fill",
        "breaker_re_entry": "breaker",
    }
)
_QUALITY_BY_FAMILY = {
    "sweep_reclaim": "sweep_reclaim_quality",
    "ob_retest": "ob_retest_quality",
    "fvg_fill": "fvg_fill_quality",
    "breaker": "breaker_quality",
    "displacement_continuation": "disp_quality",
    "session_open": "session_or_quality",
    "news_fade": "news_fade_quality",
}

# History only when jev_questions cannot be imported. Not a decision.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


def overlay_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Operator gate. Explicit 0/false/off leaves the ask unsent."""
    env = environ if environ is not None else os.environ
    raw = str(env.get(ENTRY_ENV, "")).strip().lower()
    return raw not in _TRUTHY_OFF


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _limit_key(name: str) -> bool:
    low = name.strip().lower()
    return any(part in low for part in _LIMIT_PARTS)


def _secret_key(name: str) -> bool:
    low = name.strip().lower()
    return any(part in low for part in _SECRET_PARTS)


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    parts = compact.replace("/", " ").split()
    banned = set(_BANNED)
    if any(part in banned for part in parts):
        return True
    return compact.replace(" ", "") in banned


def _scrub(value: Any) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name) or _secret_key(name):
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
        if _banned_text(value):
            return _DROP
        return value
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if _banned_text(format(value, ".10g")):
            return _DROP
        return value
    return _DROP


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


def _bad_text(value: str) -> bool:
    low = value.lower()
    return _limit_key(low) or _banned_text(value)


def _family_node(
    *,
    origin_family: str = "",
    sleeve: str = "",
    framework: str = "",
    family: str = "",
) -> str:
    explicit = _norm(family)
    if explicit in _ENTRY_FAMILIES:
        return explicit
    for raw in (origin_family, framework, sleeve):
        key = _norm(raw)
        if key in _ENTRY_FAMILIES:
            return key
        if key in _EMITTER_FAMILY:
            return _EMITTER_FAMILY[key]
        if key.startswith("dsp_"):
            return "other"
    if _norm(sleeve).startswith("dsp_"):
        return "other"
    return "other"


def _used_chunks(family: str) -> tuple[str, ...]:
    return _CHUNKS.get(_norm(family), ())


def _has_emitter(family: str) -> bool:
    return bool(_EMITTERS.get(_norm(family), ()))


def _ignore_if(family: str, state: Mapping[str, Any]) -> str | None:
    fam = _norm(family)
    news = state.get("news") if isinstance(state.get("news"), Mapping) else {}
    levels = state.get("levels") if isinstance(state.get("levels"), Mapping) else {}
    geometry = state.get("geometry") if isinstance(state.get("geometry"), Mapping) else {}
    sessions = state.get("sessions") if isinstance(state.get("sessions"), Mapping) else {}
    if fam == "news_fade":
        if news.get("spine_empty") is True or news.get("source") == "unassembled":
            return "news.spine_empty"
        return None
    if fam in {"sweep_reclaim", "ob_retest", "fvg_fill", "breaker"}:
        if levels.get("source") == "unassembled" and not (
            geometry.get("stop") or geometry.get("stop_dist") or geometry.get("entry")
        ):
            return "levels.source==unassembled and geometry missing"
    if fam == "session_open" and sessions.get("source") == "unassembled":
        return "sessions.source==unassembled"
    if fam == "displacement_continuation" and not (
        geometry.get("trigger_bar_range_atr")
        or geometry.get("stop_atr")
        or geometry.get("stop_dist")
    ):
        return "geometry missing"
    return None


def _route():
    try:
        from .gold_entry import (
            ENTRY_FAMILIES,
            family_has_emitter,
            family_node_for,
            ignore_if,
            used_chunks,
        )
    except Exception:
        return _ENTRY_FAMILIES, _has_emitter, _family_node, _ignore_if, _used_chunks
    return ENTRY_FAMILIES, family_has_emitter, family_node_for, ignore_if, used_chunks


def _identity(state: Mapping[str, Any]) -> dict[str, Any]:
    ident = state.get("identity")
    return dict(ident) if isinstance(ident, Mapping) else {}


def _family_of(state: Mapping[str, Any]) -> str:
    _, _, node_for, _, _ = _route()
    ident = _identity(state)
    return node_for(
        origin_family=str(ident.get("origin_family") or state.get("origin_family") or ""),
        sleeve=str(ident.get("sleeve") or ""),
        framework=str(ident.get("framework") or ident.get("current_framework") or ""),
        family=str(ident.get("entry_family") or ""),
    )


def _labels(state: Mapping[str, Any], family: str) -> dict[str, str]:
    ident = _identity(state)
    clock = state.get("clock") if isinstance(state.get("clock"), Mapping) else {}
    sleeve = str(ident.get("sleeve") or "")
    symbol = str(ident.get("symbol") or "")
    side = str(ident.get("side") or "")
    return {
        "book": CHALLENGE_LOGIN,
        "entry_family": family,
        "sleeve": sleeve,
        "symbol": symbol,
        "side": side,
        "as_of_utc": str(clock.get("as_of_utc") or ""),
        "ticket": str(ident.get("candidate_id") or ident.get("ticket") or ""),
        "subgoal": f"entry:{family}:{sleeve or symbol or 'none'}:{side}",
        "model": MODEL,
    }


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(text) for key, text in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(body["criteria"]))
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = {
        str(key): str(text)
        for key, text in criteria.items()
        if not _bad_text(str(key)) and not _bad_text(str(text))
    }
    return body


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    """A Score for this card. An amount waits for the card. An order keeps its words."""

    words = _ordinal_words(str(qid))
    row = _pending_score(qid, instructions, words)
    if not isinstance(row, dict):
        return None
    return row



def _noul_question(instructions: str, true_text: str, false_text: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {"true": true_text, "false": false_text},
    }


def _question_ok(spec: Mapping[str, Any]) -> bool:
    if spec.get("type") not in {"noul", "choice", "score"}:
        return False
    parts = [str(spec.get("instructions") or "")]
    criteria = spec.get("criteria")
    if isinstance(criteria, Mapping):
        for key, text in criteria.items():
            parts.append(str(key))
            parts.append(str(text))
    elif isinstance(criteria, (list, tuple)):
        parts.extend(str(item) for item in criteria)
    return not _bad_text(" ".join(parts))


def entry_questions(family: str) -> dict[str, dict[str, Any]]:
    """One subtree for this family. The menu names the ask. It does not decide."""

    pack: dict[str, dict[str, Any]] = {
        "entry_state_sufficient": _noul_question(
            (
                "Is this entry state complete enough to judge this fire? "
                "The noul you return is that completeness. "
                "An empty noul leaves completeness unset."
            ),
            "The named blocks are complete enough to judge this fire.",
            "A named block this fire needs is missing.",
        )
    }
    fam = _norm(family)
    families, _, _, _, chunks_for = _route()
    if fam not in families:
        return {key: spec for key, spec in pack.items() if _question_ok(spec)}

    for chunk in chunks_for(fam):
        pack[f"include_{chunk}"] = _score_question(
            f"include_{chunk}",
            (
                f"The score you return is how much of the named {chunk} chunk "
                f"this {fam} entry needs. "
                "It may sit between the levels. "
                "An empty score leaves the depth unset."
            ),
        )
    quality_id = _QUALITY_BY_FAMILY.get(fam)
    if quality_id:
        pack[quality_id] = _score_question(
            quality_id,
            (
                f"The score you return is the quality of this {fam} entry on this state. "
                "It may sit between the levels. "
                "An empty score leaves the quality unset."
            ),
        )
    if fam == "news_fade":
        pack["news_fade_present"] = _noul_question(
            (
                "Is a named high-impact print inside the code window on this state? "
                "The noul you return is that presence. "
                "An empty noul leaves presence unset. "
                "An empty spine is not a named print."
            ),
            "A named high-impact print is inside the code window.",
            "No named high-impact print is inside the code window.",
        )
    pack["entry_fire"] = _choice_question(
        "entry_fire",
        (
            f"Would this {fam} entry still be scored a fire on this state? "
            "The choice is the single highest probability. "
            "An empty answer or a tie leaves the choice unset. "
            "This question does not send."
        ),
        {
            "fire": "Named geometry is present on this state.",
            "abstain": "This state does not name a fire.",
            "hard_refuse": "Named geometry fights the tape.",
        },
    )
    pack["entry_keep"] = _noul_question(
        (
            "Does this entry stay on this state? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "This question does not send."
        ),
        "This entry stays.",
        "This entry does not stay.",
    )
    pack["entry_size_tilt"] = _score_question(
        "entry_size_tilt",
        (
            "The score you return is the size tilt for this entry. "
            "It may sit between the levels. "
            "An empty score leaves the tilt unset. "
            "This question does not send."
        ),
    )
    return {key: spec for key, spec in pack.items() if _question_ok(spec)}


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _finite(value)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie or an empty map is unset."""

    if not probabilities:
        return None
    allowed = [name for name in order if name in probabilities]
    if not allowed:
        return None
    best = max(probabilities[name] for name in allowed)
    winners = [name for name in allowed if probabilities[name] == best]
    if len(winners) != 1:
        return None
    local = winners[0]
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(dict(probabilities), order)
    except Exception:
        agreed = local
    if agreed is None or str(agreed) != local:
        return None
    return local


def _score_value(raw: Any) -> float | None:
    """The returned score. A tie leaves it unset. The number is not snapped."""

    if not isinstance(raw, dict):
        return None
    if raw.get("error"):
        return None
    numeric = _probs(raw)
    if numeric and _unique(numeric, tuple(numeric)) is None:
        return None
    return _finite(raw.get("score"))


def _noul_value(raw: Any) -> bool | float | None:
    """A Noul stays a bool or a probability. Missing stays missing."""

    if not isinstance(raw, dict) or raw.get("error"):
        return None
    if "noul" in raw:
        value = raw.get("noul")
    elif "Noul" in raw:
        value = raw.get("Noul")
    else:
        return None
    if value is True or value is False:
        return value
    return _finite(value)


def _choice_value(raw: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(raw, dict) or raw.get("error"):
        return None
    return _unique(_probs(raw), order)


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _remember(state: Mapping[str, Any], pairs: tuple[tuple[str, Any], ...], error: str | None) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value in pairs:
            _LOCAL_OUTCOMES.append(
                {
                    "spot": key,
                    "value": value,
                    "error": None if value is not None else error,
                }
            )
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value in pairs:
        try:
            append_outcome(key, value, logged, error=None if value is not None else error)
        except Exception:
            return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    ask: Callable[..., Any] | None,
) -> dict[str, Any]:
    call = ask
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    questions = _anchor_questions(questions, state)
    receipt = call(state, questions=dict(questions), merge_sleeve=False, model=MODEL)
    return receipt if isinstance(receipt, dict) else {"error": "evaluate_not_a_dict", "answers": {}}


def _read(family: str, answers: Mapping[str, Any]) -> dict[str, Any]:
    families, _, _, _, chunks_for = _route()
    fam = _norm(family)
    in_tree = fam in families
    completeness = _noul_value(answers.get("entry_state_sufficient"))
    depths: dict[str, float | None] = {}
    quality_id = _QUALITY_BY_FAMILY.get(fam) if in_tree else None
    quality = None
    present = None
    fire = None
    keep = None
    tilt = None
    if in_tree:
        for chunk in chunks_for(fam):
            raw = answers.get(f"include_{chunk}")
            depths[chunk] = _snap_if_ordinal(f"include_{chunk}", raw, _score_value(raw))
        if quality_id:
            raw = answers.get(quality_id)
            quality = _snap_if_ordinal(quality_id, raw, _score_value(raw))
        if fam == "news_fade":
            present = _noul_value(answers.get("news_fade_present"))
        fire = _choice_value(answers.get("entry_fire"), _FIRE_ORDER)
        keep = _noul_value(answers.get("entry_keep"))
        tilt = _score_value(answers.get("entry_size_tilt"))
    return {
        "completeness": completeness,
        "include_depth": depths,
        "quality_id": quality_id,
        "quality": quality,
        "news_fade_present": present,
        "entry_fire": fire,
        "disposition": fire,
        "keep": keep,
        "size_tilt": tilt,
    }


def _pairs(row: Mapping[str, Any], family: str) -> tuple[tuple[str, Any], ...]:
    pairs: list[tuple[str, Any]] = [("entry_state_sufficient", row.get("completeness"))]
    fam = _norm(family)
    families, _, _, _, chunks_for = _route()
    if fam not in families:
        return tuple(pairs)
    depths = row.get("include_depth") if isinstance(row.get("include_depth"), Mapping) else {}
    for chunk in chunks_for(fam):
        pairs.append((f"include_{chunk}", depths.get(chunk)))
    quality_id = row.get("quality_id")
    if quality_id:
        pairs.append((str(quality_id), row.get("quality")))
    if fam == "news_fade":
        pairs.append(("news_fade_present", row.get("news_fade_present")))
    pairs.append(("entry_fire", row.get("entry_fire")))
    pairs.append(("entry_keep", row.get("keep")))
    pairs.append(("entry_size_tilt", row.get("size_tilt")))
    return tuple(pairs)


def _receipt(
    *,
    family: str,
    labels: Mapping[str, str],
    enabled: bool,
    integer_emitted: bool,
    has_emitter: bool,
    skip: str | None,
    missing: bool,
    error: str | None,
    questions: list[str],
    decisions: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row = dict(decisions or {})
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "book": CHALLENGE_LOGIN,
        "labels": dict(labels),
        "entry_family": family,
        "has_emitter": has_emitter,
        "overlay_enabled": enabled,
        "integer_emitted": bool(integer_emitted),
        "missing_jev": missing,
        "extra_pass": False,
        "broker_effect": False,
        "keep": row.get("keep"),
        "size_tilt": row.get("size_tilt"),
        "ignore_if": skip,
        "include_depth": dict(row.get("include_depth") or {}),
        "disposition": row.get("disposition"),
        "quality_id": row.get("quality_id"),
        "quality": row.get("quality"),
        "entry_fire": row.get("entry_fire"),
        "completeness": row.get("completeness"),
        "news_fade_present": row.get("news_fade_present"),
        "questions": list(questions),
        "error": error,
    }


def _prepare(state: Mapping[str, Any] | None, family: str, integer_emitted: bool) -> dict[str, Any]:
    if isinstance(state, Mapping):
        raw = dict(state)
    else:
        raw = {}
        subject = _scrub(state)
        if subject is not _DROP:
            raw["subject"] = subject
    for key in (
        "prior_outcomes",
        "keep",
        "size_tilt",
        "entry_fire",
        "disposition",
        "extra_pass",
        "include_depth",
        "quality",
        "completeness",
    ):
        raw.pop(key, None)
    cleaned = _scrub(raw)
    posted = cleaned if isinstance(cleaned, dict) else {}
    posted["model"] = MODEL
    posted["gate"] = "gold_entry"
    posted["entry_family"] = family
    posted["integer_emitted"] = bool(integer_emitted)
    posted["labels"] = _labels(posted, family)
    posted.pop("prior_outcomes", None)
    return posted


def compose_entry_decision(
    state: Mapping[str, Any],
    answers: Mapping[str, Any] | None = None,
    *,
    integer_emitted: bool = False,
    environ: Mapping[str, str] | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One ask. Completeness, depth, quality, fire, keep, and size tilt are that return.

    A passed ``answers`` map is not a decision. An empty answer, a tie, or an
    error leaves the field unset. This hop does not send.
    """

    del answers
    enabled = overlay_enabled(environ=environ)
    family = _family_of(state if isinstance(state, Mapping) else {})
    _, has_emitter, _, ignore_fn, _ = _route()
    labels = _labels(state if isinstance(state, Mapping) else {}, family)
    skip = None
    if isinstance(state, Mapping):
        try:
            skip = ignore_fn(family, state)
        except Exception:
            skip = None
    emitter = False
    try:
        emitter = bool(has_emitter(family))
    except Exception:
        emitter = False
    if not enabled:
        return _receipt(
            family=family,
            labels=labels,
            enabled=False,
            integer_emitted=integer_emitted,
            has_emitter=emitter,
            skip=skip,
            missing=True,
            error="overlay_off",
            questions=[],
        )

    try:
        questions = entry_questions(family)
    except Exception as exc:
        return _receipt(
            family=family,
            labels=labels,
            enabled=True,
            integer_emitted=integer_emitted,
            has_emitter=emitter,
            skip=skip,
            missing=True,
            error=type(exc).__name__,
            questions=[],
        )
    posted = _prepare(state if isinstance(state, Mapping) else {}, family, integer_emitted)
    _attach_priors(posted, questions)
    try:
        receipt = _post(posted, questions, ask)
    except Exception as exc:
        row = _receipt(
            family=family,
            labels=labels,
            enabled=True,
            integer_emitted=integer_emitted,
            has_emitter=emitter,
            skip=skip,
            missing=True,
            error=type(exc).__name__,
            questions=list(questions),
        )
        _remember(posted, _pairs(row, family), row["error"])
        return row

    payload = receipt.get("answers")
    if not isinstance(payload, dict):
        payload = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not payload and not error:
        error = "empty"
    error_text = None if error in (None, "") else str(error)
    decisions = _read(family, payload)
    filled = any(
        decisions.get(name) is not None
        for name in ("completeness", "entry_fire", "keep", "size_tilt", "quality", "news_fade_present")
    ) or any(
        value is not None
        for value in (decisions.get("include_depth") or {}).values()
    )
    if not payload:
        ask_error = error_text or "empty"
    elif not filled and error_text:
        ask_error = error_text
    else:
        ask_error = None
    row = _receipt(
        family=family,
        labels=labels,
        enabled=True,
        integer_emitted=integer_emitted,
        has_emitter=emitter,
        skip=skip,
        missing=not payload,
        error=ask_error,
        questions=list(questions),
        decisions=decisions,
    )
    row["model"] = MODEL
    _remember(posted, _pairs(row, family), ask_error)
    return row


def maybe_stamp_entry_meta(
    payload: dict[str, Any],
    composed: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach the ask receipt. Does not place and does not send."""

    row = dict(payload)
    row["gold_entry"] = {
        "schema": composed.get("schema"),
        "model": composed.get("model") or MODEL,
        "entry_family": composed.get("entry_family"),
        "disposition": composed.get("disposition"),
        "extra_pass": False,
        "broker_effect": False,
        "keep": composed.get("keep"),
        "size_tilt": composed.get("size_tilt"),
        "include_depth": composed.get("include_depth"),
        "completeness": composed.get("completeness"),
        "ignore_if": composed.get("ignore_if"),
        "labels": composed.get("labels"),
    }
    return row


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
