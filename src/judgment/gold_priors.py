"""Gold-only hierarchical Jev priors pinned from G-FULL M15 tape.

Unique question files live under ``src/judgment/gold_questions/``. This
module dumps a ``QUESTION_TREE`` subtree (gate / admission / size / close)
into one System One POST per candidate. It does not Noul every tick, does
not dump the 49-ID ``gold_fanout_questions`` catalog, and does not mutate
that catalog (48-fluid inventory tests stay on the catalog).

Every decision here, including each include-depth and each composite
weight, is the value System One returns for that state. The post is
``jev_client.evaluate`` with model ``jev-1.13.0``
(POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
Questions on that post are only Noul, Choice, or Score. Prior outcomes
are attached on the ask. An empty answer, a tie, a missing score, or an
error leaves that return unset and does not copy the recorded pin back in.

Include-depth is a Choice of hide / short / long / full, not a linear
Noul keep/drop. The seat stays one piece. Close is a second object after
an exit exists. This module does not send an order.

Book: Challenge 0 / ns operator / magic 0.
Model pin: jev-1.13.0. Missing Jev → no extra PASS.
"""

from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS
from .jev_questions import MODEL

QUESTIONS_DIR = Path(__file__).resolve().parent / "gold_questions"

PIN_WINDOW = "G-FULL"
TEST_WINDOW = "G-2M"
DO_NOT_HUNT = "G-2W"

GOLD_QUESTION_IDS: tuple[str, ...] = (
    "state_sufficient",
    "flow_stance",
    "flow_alignment",
    "session_fitness",
    "geometry_vs_tape",
    "level_respect",
    "persistence",
    "a8_quality",
    "a8_agrees",
    "signal_presence",
    "tape_fresh",
    "event_proximity",
    "calendar_honest",
    "cost_hurtful",
    "admit",
    "isolated_reentry_is_new",
    "conviction_vs_tape",
    "chase_toxicity",
    "exit_class",
)

# ac60_size is a size-seat alias of persistence — same unique file, no duplicate.
QUESTION_ALIASES: dict[str, str] = {"ac60_size": "persistence"}

# Live POST dumps the seat subtree, not the catalog. Gate extra IDs are the
# compose consumers that sit on the same one POST (JEV_EVERYWHERE §3).
QUESTION_TREE: dict[str, tuple[str, ...]] = {
    "gate": (
        "state_sufficient",
        "flow_stance",
        "flow_alignment",
        "session_fitness",
        "geometry_vs_tape",
        "level_respect",
        "persistence",
        "signal_presence",
        "tape_fresh",
        "event_proximity",
        "calendar_honest",
        "cost_hurtful",
        "admit",
        "isolated_reentry_is_new",
        "chase_toxicity",
    ),
    "admission": (
        "state_sufficient",
        "flow_alignment",
        "persistence",
        "a8_quality",
        "a8_agrees",
        "geometry_vs_tape",
        "level_respect",
        "cost_hurtful",
        "admit",
    ),
    "size": (
        "persistence",
        "geometry_vs_tape",
        "session_fitness",
        "cost_hurtful",
        "conviction_vs_tape",
        "event_proximity",
    ),
    "close": ("exit_class",),
}

# Recorded G-FULL pin for the unique-file drift check. These numbers are not
# the live weights. persistence stays on the pin with flow_stance. Do not
# retune this pin on G-2W. The live weight is the Score on this ask.
GATE_COMPOSITE_WEIGHTS: dict[str, float] = {
    "geometry_vs_tape": 0.43,
    "session_fitness": 0.35,
    "level_respect": 0.12,
    "flow_alignment": 0.10,
    "persistence": 0.00,
}

# Chunks one post may include. The depth of each chunk is the Choice.
INCLUDE_PATHS: tuple[str, ...] = (
    "identity",
    "clock",
    "geometry",
    "sessions",
    "timeframes.m15",
    "timeframes.h4",
    "timeframes.d1",
    "sleeve_features.ac60",
    "sleeve_features.vol_ratio",
    "levels.prior_day_high",
    "levels.prior_day_low",
    "levels.fvg",
    "news",
    "cost",
    "sleeve_features.a8",
    "occupancy",
)

_VALID_DEPTH = frozenset({"hide", "short", "long", "full"})
_DEPTH_ORDER = ("hide", "short", "long", "full")
_DEPTH_CRITERIA = {
    "hide": "This chunk is not part of this ask.",
    "short": "A short summary of this chunk is part of this ask.",
    "long": "A longer summary of this chunk is part of this ask.",
    "full": "The whole named chunk is part of this ask.",
}
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


def noul_every_tick() -> bool:
    """Founder: linear Noul on every field/tick is the anti-pattern."""
    return False


def one_post_per_candidate() -> bool:
    return True


def gold_only() -> bool:
    return False


@lru_cache(maxsize=1)
def _compose_meta() -> dict[str, Any]:
    path = QUESTIONS_DIR / "compose.json"
    return json.loads(path.read_text(encoding="utf-8"))


def compose_meta() -> dict[str, Any]:
    return dict(_compose_meta())


def resolve_question_id(question_id: str) -> str:
    return QUESTION_ALIASES.get(question_id, question_id)


@lru_cache(maxsize=64)
def load_gold_question(question_id: str) -> dict[str, Any]:
    qid = resolve_question_id(question_id)
    if qid not in GOLD_QUESTION_IDS:
        raise KeyError(f"not a gold unique-file id: {question_id}")
    path = QUESTIONS_DIR / f"{qid}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("id") != qid:
        raise ValueError(f"{path} id {payload.get('id')!r} != {qid}")
    return payload


def gold_questions() -> dict[str, dict[str, Any]]:
    """Nineteen gold IDs only. Not the 49-key catalog."""
    out: dict[str, dict[str, Any]] = {}
    for qid in GOLD_QUESTION_IDS:
        spec = load_gold_question(qid)
        out[qid] = {
            "type": spec["type"],
            "instructions": spec["instructions"],
            "criteria": spec["criteria"],
        }
    return out


def question_subtree(seat: str) -> dict[str, dict[str, Any]]:
    """Hierarchical function-calling: dump the named seat, not the catalog."""
    if seat not in QUESTION_TREE:
        raise KeyError(f"unknown seat {seat!r}; want gate|admission|size|close")
    pack = gold_questions()
    return {qid: pack[qid] for qid in QUESTION_TREE[seat]}


def include_depth_for_seat(
    seat: str | None = None,
    returned: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Include-depth Choices for this seat.

    Only a returned hide / short / long / full is a depth. ``seat`` was
    named on the ask. A missing Choice is absent here.
    """
    _ = seat
    out: dict[str, str] = {}
    if not isinstance(returned, Mapping):
        return out
    for path, level in returned.items():
        name = str(level).strip() if isinstance(level, str) else ""
        if name in _VALID_DEPTH:
            out[str(path)] = name
    return out


def _get_path(state: Mapping[str, Any], dotted: str) -> Any:
    cur: Any = state
    for part in dotted.split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _set_path(out: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur: dict[str, Any] = out
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _short_summary(value: Any) -> Any:
    if value is None:
        return {"assembled": False, "value": None}
    if isinstance(value, Mapping):
        source = value.get("source")
        missing = value.get("missing_fields") or value.get("spine_empty")
        return {
            "assembled": source not in (None, "unassembled"),
            "source": source,
            "keys": sorted(str(k) for k in value.keys()),
            "empty_or_missing": bool(missing) if missing is not None else False,
        }
    if isinstance(value, (list, tuple)):
        return {"n": len(value), "assembled": bool(value)}
    return {"assembled": True, "kind": type(value).__name__}


def _long_summary(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Mapping):
        keep = {
            "source",
            "named",
            "trend",
            "last_close",
            "atr14",
            "spine_empty",
            "spread_r",
            "spread_r_of_stop",
            "ac60",
            "vol_ratio",
            "htf_slope_norm",
            "a8_k_of_4_pass",
            "isolated_reentry_legal",
            "symbol_open",
            "minutes_since_flat",
            "plan_r",
            "stop_atr",
            "target_atr",
        }
        slim = {k: value[k] for k in value.keys() if k in keep or k.endswith("_empty")}
        if not slim:
            slim = {k: value[k] for k in value.keys()}
        return slim
    return value


def _delete_path(out: dict[str, Any], dotted: str) -> None:
    parts = dotted.split(".")
    cur: Any = out
    for part in parts[:-1]:
        if not isinstance(cur, dict):
            return
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            return
        cur = nxt
    if isinstance(cur, dict):
        cur.pop(parts[-1], None)


def schema_at_depth(
    state: Mapping[str, Any] | None,
    *,
    seat: str | None = None,
    include_depth: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Apply returned include-depth. A missing Choice leaves that path as it stands."""
    depth = include_depth_for_seat(seat, include_depth)
    src = dict(state or {})
    if not depth:
        return dict(src)
    out: dict[str, Any] = deepcopy(src)
    for path, level in depth.items():
        if level == "hide":
            _delete_path(out, path)
            continue
        value = _get_path(src, path)
        if level == "full":
            if path in src and "." not in path:
                out[path] = deepcopy(src[path])
            elif value is not None:
                _set_path(out, path, deepcopy(value))
        elif level == "long":
            _set_path(out, path, _long_summary(value))
        else:
            _set_path(out, path, _short_summary(value))
    return out


def hierarchical_labels(
    state: Mapping[str, Any] | None,
    *,
    seat: str | None = None,
) -> dict[str, Any]:
    """Nested labels for log(n) tree search. Not a linear message scan."""
    ident = (state or {}).get("identity") or {}
    clock = (state or {}).get("clock") or {}
    occ = (state or {}).get("occupancy") or {}
    return {
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "origin": ident.get("origin_organism"),
        "family_node": ident.get("family_class"),
        "sleeve": ident.get("sleeve"),
        "symbol": ident.get("symbol") or "",
        "side": ident.get("side"),
        "as_of": clock.get("as_of_utc"),
        "day": ident.get("decision_day"),
        "ticket": ident.get("candidate_id") or occ.get("ticket"),
        "seat": seat,
        "subgoal": "gold_close" if seat == "close" else "gold_place",
        "pin_window": PIN_WINDOW,
        "test_window": TEST_WINDOW,
        "noul_every_tick": False,
    }


def _mentions_limit(text: str) -> bool:
    low = str(text).lower()
    if any(part in low for part in _LIMIT_PARTS):
        return True
    for token in _BANNED_TEXT:
        if token.lower() in low:
            return True
    return False


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


def _limit_key(name: str) -> bool:
    key = str(name).strip().lower()
    return any(part in key for part in _LIMIT_PARTS)


def _scrub(value: Any) -> Any:
    """Drop limit keys before an ask. They are not a question."""
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _limit_key(str(key)):
                continue
            out[str(key)] = _scrub(item)
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


def _depth_qid(path: str) -> str:
    return "include_depth__" + path.replace(".", "__")


def _weight_qid(qid: str) -> str:
    return "weight__" + qid


def _take_loaded(pack: Mapping[str, Any]) -> dict[str, Any]:
    """Keep loaded seat questions whose type is Noul, Choice, or Score."""
    out: dict[str, Any] = {}
    for qid, spec in pack.items():
        if not isinstance(spec, Mapping):
            continue
        kind = str(spec.get("type") or "").strip().lower()
        if kind not in {"noul", "choice", "score"}:
            continue
        instructions = str(spec.get("instructions") or "")
        if _mentions_limit(instructions) or _mentions_limit(str(qid)):
            continue
        block: dict[str, Any] = {
            "type": kind,
            "instructions": instructions.strip(),
        }
        if "criteria" in spec:
            block["criteria"] = spec["criteria"]
        out[str(qid)] = block
    return out


def _seat_pack(seat: str | None) -> dict[str, Any]:
    """The seat subtree. A missing file stays out of the post."""
    try:
        loaded = question_subtree(seat) if seat else gold_questions()
    except Exception:
        return {}
    if not isinstance(loaded, Mapping):
        return {}
    return _take_loaded(loaded)


def _depth_question(path: str, seat: str | None) -> dict[str, Any]:
    qid = _depth_qid(path)
    where = f"the {seat} seat" if seat else "this gold post"
    text = (
        f"What include-depth does `{path}` have on this state for {where}? "
        "Pick one of hide, short, long, or full. "
        "The unique highest probability is that depth. "
        "An empty answer or a tie leaves the depth unset. "
        "This is not a yes/no keep of each field."
    )
    criteria = dict(_DEPTH_CRITERIA)
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, criteria)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict) and str(block.get("type") or "") == "choice":
            copied = dict(block)
            copied["type"] = "choice"
            copied["instructions"] = text
            copied["criteria"] = criteria
            return {qid: copied}
    except Exception:
        pass
    return {qid: {"type": "choice", "instructions": text, "criteria": criteria}}


def _weight_question(qid: str) -> dict[str, Any]:
    """A weight is the amount on this card. Fewer than two weights does not post."""

    spot = _weight_qid(qid)
    text = (
        f"What weight does the returned {qid} score carry when the gate scores "
        "on this state are combined? The score you return is that weight. "
        "It may sit between levels. An empty score leaves the weight unset."
    )
    row = _pending_score(spot, text, None)
    if not isinstance(row, dict):
        return {}
    return {spot: row}



def _decision_questions(seat: str | None) -> dict[str, Any]:
    """One pack: the seat subtree, the depth Choices, the weight Scores."""
    questions = _seat_pack(seat)
    for path in INCLUDE_PATHS:
        questions.update(_depth_question(path, seat))
    for qid in GATE_COMPOSITE_WEIGHTS:
        questions.update(_weight_question(qid))
    return questions


def gold_systemone_payload(
    state: Mapping[str, Any] | None,
    *,
    seat: str | None = None,
    model: str = MODEL,
    include_depth: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """One System One body. Seat dumps the subtree plus the parameter questions.

    Close is a second object (``seat='close'``) after the exit exists — not a
    second Noul per field, and not every tick. Include-depth on the body is
    the returned Choice map. A miss does not fill a depth.
    """
    questions = _anchor_questions(_decision_questions(seat), state or {})
    base = _scrub(dict(state or {}))
    labeled = schema_at_depth(base, seat=seat, include_depth=include_depth)
    labeled["labels"] = hierarchical_labels(state, seat=seat)
    return {
        "state": labeled,
        "model": model,
        "questions": questions,
        "ask_together": True,
        "one_post": True,
        "gold_only": False,
        "noul_every_tick": False,
        "seat": seat,
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "include_depth": include_depth_for_seat(seat, include_depth),
    }


# The live persist weight is the Score returned for this state, or the weight
# note_persist_choice recorded from that return. A miss stays unset.
_CHOSEN_PERSIST: float | None = None


def note_persist_choice(weight: float | None) -> None:
    """Record the persist Score. None means this spot was not decided."""
    global _CHOSEN_PERSIST
    if weight is None:
        _CHOSEN_PERSIST = None
        return
    number = _finite(weight)
    _CHOSEN_PERSIST = number


def applied_persistence_weight() -> float | None:
    """The returned persist weight, or None when this spot has no answer."""
    return _CHOSEN_PERSIST


def diagnostic_composite(
    scores: Mapping[str, Any] | None,
    weights: Mapping[str, Any] | None = None,
) -> float | None:
    """Diagnostic weighted sum of returned scores. Not a place cliff.

    Each weight is a returned Score. A missing Score omits that term. The
    recorded pin is not copied in. No returned term leaves the sum unset.
    """
    raw = scores or {}
    explicit = isinstance(weights, Mapping)
    returned = dict(weights) if explicit else {}
    total = 0.0
    used = False
    for qid in GATE_COMPOSITE_WEIGHTS:
        if explicit:
            use = returned.get(qid)
        elif qid == "persistence":
            use = applied_persistence_weight()
        else:
            use = None
        number = _finite(use)
        if number is None:
            continue
        value = _finite(raw.get(qid))
        if value is None:
            continue
        total += number * value
        used = True
    if not used:
        return None
    return total


def _local_unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    for name in order:
        if name not in numeric:
            continue
        prob = numeric[name]
        if best_p is None or prob > best_p:
            best = name
            best_p = prob
            tied = False
        elif prob == best_p:
            tied = True
    if tied or best is None:
        return None
    return best


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return None
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
    if not numeric:
        return None
    picked: Any = None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(numeric, order)
    except Exception:
        picked = _local_unique(numeric, order)
    if picked is None or str(picked) not in allowed:
        return None
    return str(picked)


def _score_value(block: Any) -> float | None:
    """The Score on this block. A missing score stays missing."""
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "score" not in block or block.get("score") is None:
        return None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = block.get("score")
    return _finite(number if number is not None else block.get("score"))


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
        state["prior_outcomes"] = _scrub(loaded if loaded is not None else [])
    except Exception:
        state["prior_outcomes"] = []


def _remember(state: Mapping[str, Any], spot: str, value: Any, error: str | None) -> None:
    try:
        from .jev_questions import append_outcome

        append_outcome(spot, value, state, error=error)
    except Exception:
        return


def _blank_depths() -> dict[str, str | None]:
    return {path: None for path in INCLUDE_PATHS}


def _blank_weights() -> dict[str, float | None]:
    return {qid: None for qid in GATE_COMPOSITE_WEIGHTS}


def _read_decisions(
    answers: Mapping[str, Any],
    *,
    error: str | None,
) -> tuple[dict[str, str | None], dict[str, float | None]]:
    depths = _blank_depths()
    weights = _blank_weights()
    if error:
        return depths, weights
    for path in INCLUDE_PATHS:
        depths[path] = _choice(answers.get(_depth_qid(path)), _DEPTH_ORDER)
    for qid in GATE_COMPOSITE_WEIGHTS:
        weights[qid] = _score_value(answers.get(_weight_qid(qid)))
    return depths, weights


def evaluate_gold_priors(
    state: Mapping[str, Any] | None = None,
    *,
    seat: str | None = None,
) -> dict[str, Any]:
    """One System One post. Depths and weights are that return.

    An empty answer, a tie, a missing score, or an error leaves that field
    unset. This does not send an order.
    """
    questions = _anchor_questions(_decision_questions(seat), state or {})
    asked = _scrub(dict(state or {}))
    asked["labels"] = hierarchical_labels(state, seat=seat)
    asked["model"] = MODEL
    asked["seat"] = seat
    _attach_priors(asked, questions)
    receipt: dict[str, Any] = {}
    error: str | None = None
    try:
        from .jev_client import evaluate
    except Exception:
        evaluate = None  # type: ignore[assignment]
        error = "import_failed"
    if error is None and evaluate is not None:
        try:
            questions = _anchor_questions(questions, asked)
            got = evaluate(
                asked,
                model=MODEL,
                questions=dict(questions),
                merge_sleeve=False,
            )
            receipt = got if isinstance(got, dict) else {}
        except Exception as exc:  # noqa: BLE001 — a miss stays unset
            receipt = {}
            error = type(exc).__name__
    answers: dict[str, Any] = {}
    if error is None:
        if not receipt.get("ok"):
            error = str(receipt.get("error") or receipt.get("skipped") or "error")
        else:
            raw = receipt.get("answers")
            if not isinstance(raw, dict) or not raw:
                error = str(receipt.get("error") or receipt.get("skipped") or "empty")
            else:
                answers = raw
    depths, weights = _read_decisions(answers, error=error)
    for path, level in depths.items():
        miss = None if level is not None else (error or "tie_or_empty")
        _remember(asked, _depth_qid(path), level, miss)
    for qid, number in weights.items():
        miss = None if number is not None else (error or "score_missing")
        _remember(asked, _weight_qid(qid), number, miss)
    note_persist_choice(weights.get("persistence"))
    score_map = {
        qid: None if error else _score_value(answers.get(qid))
        for qid in GATE_COMPOSITE_WEIGHTS
    }
    return {
        "model": str(receipt.get("model") or MODEL) if receipt else MODEL,
        "seat": seat,
        "one_post": True,
        "depths": depths,
        "weights": weights,
        "include_depth": include_depth_for_seat(seat, depths),
        "persistence": weights.get("persistence"),
        "composite": diagnostic_composite(score_map, weights),
        "error": error,
        "answers": answers,
        "broker_effect": False,
    }


def assert_gold_pin() -> dict[str, Any]:
    """Fail closed if unique files drift from the pin contract."""
    meta = compose_meta()
    weights = meta.get("gate_composite_weights") or {}
    if dict(weights) != GATE_COMPOSITE_WEIGHTS:
        raise ValueError("compose.json weights drifted from GATE_COMPOSITE_WEIGHTS")
    if abs(sum(GATE_COMPOSITE_WEIGHTS.values()) - 1.0) > 1e-12:
        raise ValueError("weights must sum to 1.00")
    if meta.get("noul_every_tick") is not False:
        raise ValueError("noul_every_tick must be false")
    if meta.get("one_systemone_post_per_candidate") is not True:
        raise ValueError("one POST per candidate")
    if meta.get("book") != CHALLENGE_LOGIN:
        raise ValueError("gold priors bind Challenge 0 only")
    missing = [qid for qid in GOLD_QUESTION_IDS if not (QUESTIONS_DIR / f"{qid}.json").is_file()]
    if missing:
        raise FileNotFoundError(f"missing unique gold files: {missing}")
    extra = sorted(
        p.stem
        for p in QUESTIONS_DIR.glob("*.json")
        if p.stem not in set(GOLD_QUESTION_IDS) | {"compose"}
    )
    if extra:
        raise ValueError(f"non-gold json in gold_questions/: {extra}")
    return {
        "ok": True,
        "n_gold_ids": len(GOLD_QUESTION_IDS),
        "weights": dict(GATE_COMPOSITE_WEIGHTS),
        "pin_window": PIN_WINDOW,
        "test_window": TEST_WINDOW,
        "do_not_hunt": DO_NOT_HUNT,
        "book": CHALLENGE_LOGIN,
    }


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
