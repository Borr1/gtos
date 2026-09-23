"""PLACE_CHOICE — hash stamps on the Challenge place/conf path.

Dig F APPLY_CANDIDATE consume:

* ``option_order_sensitivity`` — option *order* is part of the stamp
* ``state_evidence_sufficiency`` — state hash is required and complete
* ``jev_repeatability_probe`` — same inputs must restamp identically

Incomplete ``menu_hash`` / ``option_order_hash`` / ``state_hash`` refuse.
Never broker-send from the stamp helpers. Challenge 0 only.
``pack1b_beaten`` is false. ``evaluate_place_choice`` is the live APPLY gate.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .alive_menu import AliveMenu
from .challenge import CHALLENGE_LOGIN, assert_challenge_payout_writer
from .jev_questions import hierarchical_labels, spot_question, unique_highest
from .place_consume_flags import (
    APPLY_CANDIDATES,
    PACK1B_BEATEN,
    PLACE_APPLY,
    already_live_consume,
)
from .veto import refuse_invented_news_protocol

SCHEMA = "gtos.judgment.place_choice.v1"
HASH_KEYS = ("menu_hash", "option_order_hash", "state_hash")
SHA256_HEX_LEN = 64
_HEX = frozenset("009abcdef")


class IncompletePlaceChoiceHashes(ValueError):
    """Menu / option_order / state hash missing, short, or not sha256 hex."""


def canonical_sha256(payload: object) -> str:
    """Stable sha256 of a JSON-canonical payload."""

    blob = json.dumps(
        _canonicalize(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _canonicalize(payload: object) -> object:
    if payload is None:
        return None
    if isinstance(payload, Mapping):
        return {str(k): _canonicalize(v) for k, v in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [_canonicalize(v) for v in payload]
    if isinstance(payload, bool):
        return payload
    if isinstance(payload, (int, float)):
        return payload
    return str(payload)


def is_complete_hash(value: object) -> bool:
    """True only for a full 64-char sha256 hex digest."""

    if not isinstance(value, str):
        return False
    digest = value.strip().lower()
    if len(digest) != SHA256_HEX_LEN:
        return False
    if digest == "0" * SHA256_HEX_LEN:
        return False
    return all(ch in _HEX for ch in digest)


def missing_hash_keys(
    *,
    menu_hash: object,
    option_order_hash: object,
    state_hash: object,
) -> tuple[str, ...]:
    pairs = (
        ("menu_hash", menu_hash),
        ("option_order_hash", option_order_hash),
        ("state_hash", state_hash),
    )
    return tuple(name for name, value in pairs if not is_complete_hash(value))


def assert_place_choice_hashes(
    *,
    menu_hash: object,
    option_order_hash: object,
    state_hash: object,
) -> None:
    """Refuse a stamp whose menu / option_order / state hashes are incomplete."""

    missing = missing_hash_keys(
        menu_hash=menu_hash,
        option_order_hash=option_order_hash,
        state_hash=state_hash,
    )
    if missing:
        raise IncompletePlaceChoiceHashes(
            "PLACE_CHOICE refuses incomplete hashes: " + ", ".join(missing)
        )


def menu_hash_payload(menu: AliveMenu) -> dict[str, object]:
    return {
        "cycle_id": menu.cycle_id,
        "inventory_fingerprint": menu.inventory_fingerprint,
        "option_ids": list(menu.option_ids),
        "criteria": [c.as_dict() for c in menu.criteria],
    }


def option_order_hash_payload(option_order: Sequence[str]) -> dict[str, object]:
    """Order is load-bearing (option_order_sensitivity)."""

    return {"option_order": [str(x) for x in option_order]}


def _sufficient_flag(completeness: object) -> bool | None:
    """A present bool is that bool. A missing flag stays missing."""

    if not isinstance(completeness, Mapping):
        return None
    if "state_sufficient_for_live" not in completeness:
        return None
    raw = completeness.get("state_sufficient_for_live")
    if raw is True or raw is False:
        return raw
    return None


def state_hash_payload(state: Mapping[str, Any] | None) -> dict[str, object]:
    """Canonical state for state_evidence_sufficiency.

    Absent state is hashed as an honest insufficient payload — that is a
    *complete* hash, not an incomplete one. Incomplete means a missing or
    malformed digest, not missing books. A missing sufficiency flag is not
    recorded as false.
    """

    if state is None:
        return {
            "state_absent": True,
            "completeness": {"state_sufficient_for_live": None},
        }
    completeness = state.get("completeness") if isinstance(state.get("completeness"), Mapping) else {}
    identity = state.get("identity") if isinstance(state.get("identity"), Mapping) else {}
    return {
        "state_absent": False,
        "completeness": dict(completeness) if completeness else {},
        "identity": {
            "login": identity.get("login"),
            "symbol": identity.get("symbol"),
            "sleeve": identity.get("sleeve"),
            "candidate_id": identity.get("candidate_id"),
        },
        "state_sufficient_for_live": _sufficient_flag(completeness),
    }


@dataclass(frozen=True)
class PlaceChoiceStamp:
    """One place/conf hash stamp. ``broker_effect`` is always False."""

    menu_hash: str
    option_order_hash: str
    state_hash: str
    option_order: tuple[str, ...]
    state_sufficient: bool | None
    complete: bool
    missing: tuple[str, ...]
    consumes: tuple[str, ...]
    pack1b_beaten: bool
    login: str
    place_apply: bool
    never_place: bool = True
    broker_effect: bool = False

    def refuse_if_incomplete(self) -> None:
        if not self.complete:
            raise IncompletePlaceChoiceHashes(
                "PLACE_CHOICE refuses incomplete hashes: " + ", ".join(self.missing)
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "menu_hash": self.menu_hash,
            "option_order_hash": self.option_order_hash,
            "state_hash": self.state_hash,
            "option_order": list(self.option_order),
            "state_sufficient": self.state_sufficient,
            "complete": self.complete,
            "missing": list(self.missing),
            "consumes": list(self.consumes),
            "pack1b_beaten": self.pack1b_beaten,
            "login": self.login,
            "place_apply": self.place_apply,
            "already_live": already_live_consume(),
            "never_place": True,
            "never_remint": True,
            "never_flatten": True,
            "broker_effect": False,
            "dig_never_broker_send": True,
        }


def stamp_place_choice(
    *,
    menu: AliveMenu,
    option_order: Sequence[str] | None = None,
    state: Mapping[str, Any] | None = None,
    menu_hash: str | None = None,
    option_order_hash: str | None = None,
    state_hash: str | None = None,
    login: str = CHALLENGE_LOGIN,
    refuse_incomplete: bool = True,
    invented_files: tuple[str, ...] = (),
) -> PlaceChoiceStamp:
    """Stamp menu / option_order / state hashes. Refuse incompletes.

    Injected hash strings (tests / host) are accepted only when complete.
    """

    assert_challenge_payout_writer(login)
    refuse_invented_news_protocol(invented_files)

    order = tuple(str(x) for x in (option_order if option_order is not None else menu.option_ids))
    computed_menu = canonical_sha256(menu_hash_payload(menu))
    computed_order = canonical_sha256(option_order_hash_payload(order))
    state_payload = state_hash_payload(state)
    computed_state = canonical_sha256(state_payload)

    resolved_menu = menu_hash if menu_hash is not None else computed_menu
    resolved_order = option_order_hash if option_order_hash is not None else computed_order
    resolved_state = state_hash if state_hash is not None else computed_state

    missing = missing_hash_keys(
        menu_hash=resolved_menu,
        option_order_hash=resolved_order,
        state_hash=resolved_state,
    )
    stamp = PlaceChoiceStamp(
        menu_hash=str(resolved_menu),
        option_order_hash=str(resolved_order),
        state_hash=str(resolved_state),
        option_order=order,
        state_sufficient=_sufficient_flag(
            {"state_sufficient_for_live": state_payload.get("state_sufficient_for_live")}
            if "state_sufficient_for_live" in state_payload
            else {}
        ),
        complete=not missing,
        missing=missing,
        consumes=(
            "option_order_sensitivity",
            "state_evidence_sufficiency",
            "jev_repeatability_probe",
        ),
        pack1b_beaten=PACK1B_BEATEN,
        login=login,
        place_apply=PLACE_APPLY,
    )
    if refuse_incomplete:
        stamp.refuse_if_incomplete()
    return stamp


def jev_repeatability_probe(
    *,
    menu: AliveMenu,
    option_order: Sequence[str] | None = None,
    state: Mapping[str, Any] | None = None,
    login: str = CHALLENGE_LOGIN,
    repeats: int | None = None,
) -> dict[str, object]:
    """APPLY_CANDIDATE consume: restamp must be identical.

    Dig never broker-sends. Repeatability is hash identity, not a live fill.
    The repeat count is the returned loop bound. ``repeats`` is not that bound.
    """

    del repeats
    asked = _ask_place({} if state is None else dict(state))
    card = _bounds_for(asked.get("answers") or {})
    bound = card.get("loop_bound")
    stamps: list[PlaceChoiceStamp] = []
    if isinstance(bound, (int, float)) and not isinstance(bound, bool):
        while len(stamps) < bound:
            stamps.append(
                stamp_place_choice(
                    menu=menu,
                    option_order=option_order,
                    state=state,
                    login=login,
                    refuse_incomplete=True,
                )
            )
    keys = [
        (row.menu_hash, row.option_order_hash, row.state_hash) for row in stamps
    ]
    if not keys or not keys[1:]:
        repeatable = None
    else:
        repeatable = all(item == keys[0] for item in keys[1:])
    _remember_bounds(asked.get("state") or {}, card, error=asked.get("error"))
    hashes = {
        "menu_hash": stamps[0].menu_hash,
        "option_order_hash": stamps[0].option_order_hash,
        "state_hash": stamps[0].state_hash,
    } if stamps else {
        "menu_hash": None,
        "option_order_hash": None,
        "state_hash": None,
    }
    return {
        "schema": "gtos.judgment.jev_repeatability_probe.v1",
        "consume": "jev_repeatability_probe",
        "repeatable": repeatable,
        "repeats": None if bound is None else len(stamps),
        "loop_bound": bound,
        "hashes": hashes,
        "pack1b_beaten": PACK1B_BEATEN,
        "never_place": True,
        "broker_effect": False,
        "apply_candidates": list(APPLY_CANDIDATES),
    }


# --- live APPLY gate (Owner unlock 2026-09-21). Stamp helpers above stay. ---

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_CHALLENGE_NS = frozenset({"operator"})
_CHALLENGE_LOGIN_IDS = frozenset({"0", 0})

PLACE_CRITERIA = {
    "PLACE": "This candidate is the order on this bar.",
    "STAND": "This candidate is not the order on this bar.",
    "DELAY": "This bar is not the bar for this candidate.",
    "REMINT": "A re-entry of an existing ticket fits this candidate.",
    "FLATTEN_CANDIDATE": "This candidate is a reduction of open risk.",
}
PLACE_ORDER = tuple(PLACE_CRITERIA)
PLACE_OVERLAY = spot_question(
    "place",
    "This candidate on this bar. symbol, sleeve, and side are on the state. Is this candidate the order?",
    PLACE_CRITERIA,
)
PLACE_HOP_PACK = dict(PLACE_OVERLAY)
PLACE_CHOICE_QUESTION = PLACE_HOP_PACK
_FUNCTION_ORDER = ("returned_score", "last_outcome", "withhold")
_BRANCH_ORDER = ("take", "skip")


def place_questions() -> dict[str, Any]:
    """Place card. Same names the size card uses, so the seats answer each other.

    The place spot stays the order question. Function, branch, loop bound,
    splice bound, and digest width are the other returns on that same ask.
    """

    from .jev_questions import parameter_question

    pack: dict[str, Any] = dict(PLACE_OVERLAY)
    pack.update(spot_question(
        "place_function",
        "Which function returns the loop bound and the parameter on this state? "
        "The name you return is the function that runs. "
        "Do not name a number.",
        {
            "returned_score": "The function is the score hop. Its return is the loop bound and the parameter.",
            "last_outcome": "The function reads the previous returned loop bound and parameter and returns those.",
            "withhold": "The function returns no loop bound and no parameter.",
        },
    ))
    pack.update(spot_question(
        "place_if",
        "Does this state take the place branch? "
        "The name you return is the branch.",
        {
            "take": "Take the branch. The named function returns the loop bound and the parameter.",
            "skip": "Do not take the branch. The loop bound and the parameter stay unset.",
        },
    ))
    pack.update(parameter_question(
        "place_loop",
        "Given the facts and prior_outcomes on this state, how far does the same stamp repeat? "
        "The score you return is that bound. "
        "A pass line and a floor do not limit it.",
    ))
    pack.update(parameter_question(
        "place_splice",
        "Given the facts and prior_outcomes on this state, how many posted answers may sit "
        "before the catalog is leftover? "
        "The score you return is that bound. "
        "A pass line and a floor do not limit it.",
    ))
    pack.update(parameter_question(
        "place_width",
        "Given the facts and prior_outcomes on this state, how wide is the digest prefix "
        "on this place stamp? "
        "The score you return is that width. "
        "A pass line and a floor do not limit it.",
    ))
    pack["state_sufficient"] = {
        "type": "noul",
        "instructions": "Is this state complete enough for the place on this bar?",
        "criteria": {
            "true": "The fields needed to judge this place are present.",
            "false": "The fields needed to judge this place are missing.",
        },
    }
    return pack


def _place_posted_ids() -> list[str]:
    """Ids on this ask. Not a gate catalog."""
    return list(place_questions())


def place_apply_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get("GTOS_JEV_PLACE_APPLY", "")).strip().lower() in _TRUTHY


def _challenge_ok(intent: Any, *, login: Any = None, namespace: str | None = None) -> bool:
    ns = str(
        namespace
        or os.environ.get("GTOS_NAMESPACE")
        or os.environ.get("GTOS_BOOK_NAMESPACE")
        or ""
    ).strip()
    details = getattr(intent, "details", None) if intent is not None else None
    if isinstance(details, dict):
        ns = ns or str(details.get("namespace") or "")
    if ns and ns not in _CHALLENGE_NS and "ftmo_f5" not in ns.lower():
        if login is None or str(login) not in {str(x) for x in _CHALLENGE_LOGIN_IDS}:
            return ns in _CHALLENGE_NS or ns == ""
    if login is not None and str(login) not in {str(x) for x in _CHALLENGE_LOGIN_IDS}:
        if str(login).isdigit() and str(login) not in {"0"}:
            return False
    return True


def _intent_fields(intent: Any) -> dict[str, Any]:
    symbol = str(getattr(intent, "symbol", None) or getattr(intent, "instrument", None) or "")
    sleeve = str(getattr(intent, "sleeve", None) or getattr(intent, "tag", None) or "")
    side = str(getattr(intent, "side", None) or getattr(intent, "direction", None) or "")
    details = getattr(intent, "details", None)
    if isinstance(details, dict):
        symbol = symbol or str(details.get("symbol") or "")
        sleeve = sleeve or str(details.get("sleeve") or details.get("tag") or "")
        side = side or str(details.get("side") or "")
    return {"symbol": symbol, "sleeve": sleeve, "side": side, "tag": sleeve}


def _number(value: Any) -> float | None:
    """A returned number. Booleans, blanks, and non-finite values stay empty."""

    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _prefix(digest: str, width: float | None) -> str:
    """Keep the digest out to the returned width. A missing width keeps the digest."""

    if width is None:
        return digest
    kept: list[str] = []
    while len(kept) < width and len(kept) < len(digest):
        kept.append(digest[len(kept)])
    return "".join(kept)


def _choice_state_hash(state: dict[str, Any], width: float | None = None) -> str:
    blob = json.dumps(state, sort_keys=True, default=str).encode("utf-8")
    return _prefix(hashlib.sha256(blob).hexdigest(), width)


def _menu_hashes(criteria: dict[str, str], width: float | None = None) -> tuple[str, str]:
    keys = list(criteria.keys())
    menu = _prefix(hashlib.sha256("|".join(keys).encode()).hexdigest(), width)
    order = _prefix(hashlib.sha256(">".join(keys).encode()).hexdigest(), width)
    return menu, order


def build_place_state(intent: Any, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    fields = _intent_fields(intent)
    state = {
        "gate": "place_choice",
        "identity": fields,
        "symbol": fields["symbol"],
        "sleeve": fields["sleeve"],
        "side": fields["side"],
        "place_context": {
            "writer_ready": True,
            "owner_unlock_20260921": True,
            "apply_flag": place_apply_enabled(),
        },
        "clock": {"as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
    }
    if extra:
        state.update(extra)
    try:
        from .equity_frame import attach_account

        state = attach_account(state)
    except Exception:
        pass
    try:
        state["labels"] = hierarchical_labels(state, extra={"subgoal": "place"})
    except Exception:
        pass
    try:
        _attach_priors(state, place_questions())
    except Exception:
        state.setdefault("prior_outcomes", [])
    state.pop("state_hash", None)
    state["state_hash"] = _choice_state_hash(state)
    return state


def _unique_observe_slim(namespace: str | None) -> dict[str, Any] | None:
    """Attach LABEL unique fire. Does not change the place Choice."""
    try:
        from .unique_loader import observe_unique_apply

        row = observe_unique_apply(namespace=namespace, origin="evaluate_place_choice")
        rungs = row.get("rungs") if isinstance(row, dict) else None
        return {
            "n_loaded": row.get("n_loaded"),
            "n_failed": row.get("n_failed"),
            "persist": row.get("persist"),
            "reason": row.get("reason"),
            "rung_ok": row.get("rung_ok"),
            "rung_names": list(rungs.keys()) if isinstance(rungs, dict) else [],
            "news_protocol_applied": (row.get("news") or {}).get("NEWS_PROTOCOL_APPLIED"),
            "mill_url": (row.get("news") or {}).get("mill_url"),
        }
    except Exception:
        return None


def _probabilities(raw: Any) -> dict[str, float]:
    block = raw if isinstance(raw, dict) else {}
    probs_in = block.get("probabilities") if isinstance(block.get("probabilities"), dict) else None
    numeric: dict[str, float] = {}
    if isinstance(probs_in, dict):
        for key, val in probs_in.items():
            number = _number(val)
            if number is not None:
                numeric[str(key)] = number
    return numeric


def _unique_highest(raw: Any, order: Sequence[str] = PLACE_ORDER) -> dict[str, Any]:
    """The decision is the unique highest probability. A label without probabilities is not a decision."""
    numeric = _probabilities(raw)
    choice = unique_highest(numeric or None, order)
    if choice is None or str(choice) not in set(order):
        return {
            "choice": None,
            "probabilities": numeric,
            "unique_highest": False,
            "probability": None,
        }
    name = str(choice)
    if order is PLACE_ORDER and name.upper() in PLACE_CRITERIA:
        name = name.upper()
    return {
        "choice": name,
        "probabilities": numeric,
        "unique_highest": True,
        "probability": numeric.get(name) if name in numeric else numeric.get(str(choice)),
    }


def _score_block(raw: Any) -> float | None:
    """The numeric score. A missing score stays empty. A level label is not a number."""

    block = raw if isinstance(raw, dict) else {}
    for key in ("score", "value"):
        number = _number(block.get(key))
        if number is not None:
            return number
    return None


def _noul_value(raw: Any) -> bool | float | None:
    """A noul stays a bool or a probability. It is not coerced to a threshold."""
    block = raw if isinstance(raw, dict) else {}
    value = block.get("noul")
    if value is True or value is False:
        return value
    return _number(value)


def _last_logged(key: str) -> float | None:
    try:
        from .jev_questions import last_logged_value
    except Exception:
        return None
    try:
        return _number(last_logged_value(key))
    except Exception:
        return None


def _applied_bounds(answers: Mapping[str, Any] | None) -> dict[str, Any]:
    """Run the function and the branch. A skip, a tie, or a missing score leaves the numbers unset."""
    payload = answers if isinstance(answers, Mapping) else {}
    function_name = _unique_highest(payload.get("place_function"), _FUNCTION_ORDER)["choice"]
    branch = _unique_highest(payload.get("place_if"), _BRANCH_ORDER)["choice"]
    loop_score = _score_block(payload.get("place_loop"))
    splice_score = _score_block(payload.get("place_splice"))
    width_score = _score_block(payload.get("place_width"))
    loop_bound = None
    splice_bound = None
    width = None
    if function_name == "returned_score" and branch == "take":
        loop_bound = loop_score
        splice_bound = splice_score
        width = width_score
    elif function_name == "last_outcome" and branch == "take":
        loop_bound = _last_logged("place_loop")
        splice_bound = _last_logged("place_splice")
        width = _last_logged("place_width")
    return {
        "place_function": function_name,
        "place_if": branch,
        "loop_bound": loop_bound,
        "splice_bound": splice_bound,
        "width": width,
    }


def _bounds_for(answers: Mapping[str, Any] | None) -> dict[str, Any]:
    """Apply the splice score. A missing splice score does not become a stand-in cap."""
    payload = answers if isinstance(answers, Mapping) else {}
    card = _applied_bounds(payload)
    splice = card.get("splice_bound")
    blocked = splice is not None and len(payload) >= splice
    if blocked:
        card = {**card, "loop_bound": None, "width": None}
    card["blocked"] = blocked
    return card


def _remember_bounds(
    state: Mapping[str, Any],
    card: Mapping[str, Any],
    error: Any = None,
) -> None:
    """The returns just run are the next ask's history. A miss is stored as empty."""
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    rows = (
        ("place_loop", card.get("loop_bound")),
        ("place_splice", card.get("splice_bound")),
        ("place_width", card.get("width")),
    )
    for key, value in rows:
        try:
            append_outcome(
                key,
                value,
                state,
                error=None if value is not None else error,
            )
        except Exception:
            continue


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    from .jev_questions import prior_outcomes

    state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)


def _remember_choice(
    state: Mapping[str, Any],
    choice: Any,
    noul: Any,
    error: Any = None,
) -> None:
    """The place Choice and the sufficiency noul are the next ask's history."""

    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    rows = (
        ("place", choice),
        ("state_sufficient", noul),
    )
    for key, value in rows:
        try:
            append_outcome(
                key,
                value,
                state,
                error=None if value is not None else error,
            )
        except Exception:
            continue


def _ask_place(state: dict[str, Any]) -> dict[str, Any]:
    """One existing evaluate() call. Priors go in on this ask. No second client."""
    try:
        questions = place_questions()
    except Exception as exc:
        return {
            "ok": False,
            "source": "question_pack_fail",
            "error": type(exc).__name__,
            "answers": {},
            "state": state,
            "questions": {},
            "receipt": {},
        }
    try:
        _attach_priors(state, questions)
    except Exception:
        state.setdefault("prior_outcomes", [])
    state.pop("state_hash", None)
    state["state_hash"] = _choice_state_hash(state)
    try:
        from .jev_client import evaluate
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "source": "jev_client_import_fail",
            "error": type(exc).__name__,
            "answers": {},
            "state": state,
            "questions": questions,
            "receipt": {},
        }
    try:
        receipt = evaluate(
            state,
            questions=questions,
            merge_sleeve=False,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "source": "evaluate_raise",
            "error": type(exc).__name__,
            "answers": {},
            "state": state,
            "questions": questions,
            "receipt": {},
        }
    if not isinstance(receipt, dict):
        receipt = {}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "ok": bool(answers),
        "source": "place_hop",
        "error": error,
        "answers": answers,
        "state": state,
        "questions": questions,
        "receipt": receipt,
    }


def evaluate_place_choice(
    intent: Any,
    *,
    environ: Mapping[str, str] | None = None,
    login: Any = None,
    namespace: str | None = None,
    extra_state: dict[str, Any] | None = None,
    observe: bool = False,
) -> dict[str, Any]:
    """Place decision for this candidate, this bar.

    The order is the place return. The loop bound, the splice bound, and the
    digest width are the scores on that same ask. A miss stays empty.
    This hop does not send.
    """
    del environ
    if not _challenge_ok(intent, login=login, namespace=namespace):
        return {
            "action": None,
            "source": "not_challenge",
            "hop": "place",
            "seat": "place",
            "broker_effect": False,
        }

    unique_observe = _unique_observe_slim(namespace) if observe else None

    def _out(payload: dict[str, Any]) -> dict[str, Any]:
        if unique_observe is not None:
            payload["unique_observe"] = unique_observe
        payload["broker_effect"] = False
        return payload

    try:
        state = build_place_state(intent, extra=extra_state)
        asked = _ask_place(state)
    except Exception as exc:  # noqa: BLE001
        return _out({
            "action": None,
            "source": "evaluate_raise",
            "error": type(exc).__name__,
            "seat": "place",
            "hop": "place",
            "loop_bound": None,
            "splice_bound": None,
            "width": None,
            "state_sufficient": None,
        })

    state = asked.get("state") if isinstance(asked.get("state"), dict) else state
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    receipt = asked.get("receipt") if isinstance(asked.get("receipt"), dict) else {}
    questions = asked.get("questions") if isinstance(asked.get("questions"), dict) else {}
    posted_ids = list(questions) if questions else []
    card = _bounds_for(answers)
    blocked = bool(card.get("blocked"))
    width = card.get("width")
    menu_hash, option_order_hash = _menu_hashes(
        PLACE_CRITERIA,
        width if isinstance(width, (int, float)) and not isinstance(width, bool) else None,
    )
    state_hash = state.get("state_hash")
    if isinstance(width, (int, float)) and not isinstance(width, bool) and isinstance(state_hash, str):
        state_hash = _prefix(state_hash, width)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stamps = {
        "menu_hash": menu_hash,
        "option_order_hash": option_order_hash,
        "state_hash": state_hash,
        "model_id": "jev-1.13.0",
        "run_id": run_id,
        "owner_unlock": True,
        "hop": "place",
        "seat": "place",
        "posted_ids": posted_ids,
        "n_posted": len(answers) if answers else len(posted_ids),
    }
    if not asked.get("ok") and not answers:
        _remember_bounds(state, card, error=asked.get("error"))
        _remember_choice(state, None, None, error=asked.get("error"))
        return _out({
            "action": None,
            "source": asked.get("source") or "evaluate_raise",
            "error": asked.get("error"),
            "stamps": stamps,
            "seat": "place",
            "posted_ids": posted_ids,
            "n_posted": len(posted_ids),
            "hop": "place",
            "place_function": card.get("place_function"),
            "place_if": card.get("place_if"),
            "loop_bound": None,
            "splice_bound": None,
            "width": None,
            "state_sufficient": None,
        })

    raw_picked = _unique_highest(answers.get("place") or answers.get("place_choice") or {})
    if blocked:
        picked = {
            "choice": None,
            "probabilities": raw_picked["probabilities"],
            "unique_highest": False,
            "probability": None,
        }
    else:
        picked = raw_picked
    _remember_bounds(
        state,
        card,
        error="leftover_catalog_splice" if blocked else asked.get("error"),
    )
    noul = _noul_value(answers.get("state_sufficient"))
    _remember_choice(
        state,
        None if blocked else picked["choice"],
        noul,
        error="leftover_catalog_splice" if blocked else asked.get("error"),
    )
    payload = {
        "action": picked["choice"],
        "choice": picked["choice"],
        "probabilities": picked["probabilities"],
        "unique_highest": picked["unique_highest"],
        "probability": picked["probability"],
        "source": "place_hop",
        "seat": "place",
        "posted_ids": list(answers.keys()) or posted_ids,
        "n_posted": len(answers) if answers else len(posted_ids),
        "stamps": stamps,
        "calls_used": receipt.get("calls_used"),
        "usage": receipt.get("usage"),
        "owner_unlock": True,
        "model": receipt.get("model") or "jev-1.13.0",
        "hop": "place",
        "place_function": card.get("place_function"),
        "place_if": card.get("place_if"),
        "loop_bound": card.get("loop_bound"),
        "splice_bound": card.get("splice_bound"),
        "width": card.get("width"),
        "state_sufficient": noul,
    }
    if blocked:
        payload["error"] = "leftover_catalog_splice"
    elif asked.get("error"):
        payload["error"] = asked.get("error")
    return _out(payload)
