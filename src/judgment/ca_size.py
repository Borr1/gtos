"""Named CA size wire. The tilt is a fraction of the USD risk the book already sized.

The seven CA labels stay the facts this wire consumes. They are not a
product of planted factors, and they are not a 0-5 level index. The
value the cycle consumes is that fraction. It is not equity, not a
notional, and not a lot count. Empty, tie, and error leave it unset.

No returned fraction is above the size the book already set, and none
is zero. This module does not place and does not refuse the fire. It
does not read a clamp from process_lock.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

WIRE_ID = "ca_cross_asset_size_tilt"
CA_SIZE_SCHEMA = "gtos.judgment.ca_size.v1"
APPLY_ENV = "GTOS_JEV_CA_SIZE_APPLY"
QUESTION_ID = "ca_size_tilt"

CONSUMED_LABELS = (
    "CA-OCC-001",
    "CA-LIQ-001",
    "CA-EVT-001",
    "CA-USD-001",
    "CA-CORR-001",
    "CA-RSK-001",
    "CA-IDX-001",
)

_COMPONENT_NAMES = (
    "occupancy_world",
    "session_liquidity",
    "event_join",
    "usd_proxy",
    "gold_usd_comove",
    "risk_on_funding",
    "gold_index_comove",
)

# One unit: USD risk of the ticket the book already sized. Equity, room,
# notional, lots, and counts are not this unit and are not anchors.
_BOOK_RISK_KEYS = (
    "risk_usd",
    "intended_risk_usd",
    "f5_intended_risk_usd",
    "cash_risk_usd",
)

TILT_UNIT = "fraction of the USD risk the book already sized"

_NESTED = ("account", "account_facts", "equity_frame", "card", "state")

_INSTRUCTIONS = (
    "The score you return is the ca tilt: a fraction of the USD risk the book already sized. "
    "The top level is that whole size. "
    "It is not dollars, not lots, and not a notional. "
    "It may sit between the levels. "
    "An empty score, a tie, or an error leaves the tilt unset. "
    "Do not send. Do not add size. Do not zero the fire."
)


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


def _views(*blobs: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    found: list[Mapping[str, Any]] = []
    pending: list[Mapping[str, Any]] = []
    for blob in blobs:
        if isinstance(blob, Mapping):
            pending.append(blob)
    for blob in pending:
        found.append(blob)
        for key in _NESTED:
            nested = blob.get(key)
            if isinstance(nested, Mapping):
                found.append(nested)
    return found


def _pair_rows(raw: Any) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    seen: list[float] = []
    if isinstance(raw, Mapping):
        items = list(raw.items())
    else:
        try:
            items = list(raw)
        except TypeError:
            return rows
    for item in items:
        label: Any
        number: float | None
        if isinstance(item, Mapping):
            label = item.get("label")
            number = _finite(item.get("value"))
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            label = item[0]
            number = _finite(item[1])
        else:
            continue
        text = "" if label is None else str(label).strip()
        if number is None or not text or number in seen:
            continue
        seen.append(number)
        rows.append((text, number))
    return rows


def _in_tilt_unit(number: float | None) -> float | None:
    """A tilt is a positive fraction of the book's size, through the whole size."""

    if number is None or number <= 0 or number > 1:
        return None
    return number


def _explicit_tilt_anchors(views: list[Mapping[str, Any]]) -> list[tuple[str, float]]:
    """score_anchors already in the tilt unit. A notional or a zero is not one of them."""

    for view in views:
        if "score_anchors" not in view:
            continue
        rows: list[tuple[str, float]] = []
        seen: list[float] = []
        for label, number in _pair_rows(view.get("score_anchors")):
            tilt = _in_tilt_unit(number)
            if tilt is None or tilt in seen:
                continue
            seen.append(tilt)
            rows.append((label, tilt))
        if len(rows) >= 2:
            return rows
    return []


def _first_risk(views: list[Mapping[str, Any]], key: str) -> float | None:
    for view in views:
        if key not in view:
            continue
        number = _finite(view.get(key))
        if number is not None and number > 0:
            return number
    return None


def book_risk_usd(*blobs: Mapping[str, Any] | None) -> float | None:
    """The USD risk the book already sized. Equity and room are not this fact."""

    views = _views(*blobs)
    for key in _BOOK_RISK_KEYS:
        number = _first_risk(views, key)
        if number is not None:
            return number
    return None


def _risk_tilt_anchors(views: list[Mapping[str, Any]]) -> list[tuple[str, float]]:
    """Fractions of one USD-risk figure. A larger figure, a lot, and a count stay out."""

    book = None
    for key in _BOOK_RISK_KEYS:
        number = _first_risk(views, key)
        if number is not None:
            book = number
            break
    if book is None:
        return []
    rows: list[tuple[str, float]] = []
    seen: list[float] = []
    whole = _in_tilt_unit(book / book)
    if whole is not None:
        seen.append(whole)
        rows.append(("the USD risk the book already sized, as a fraction of that risk", whole))
    for key in _BOOK_RISK_KEYS:
        number = _first_risk(views, key)
        if number is None or number > book:
            continue
        tilt = _in_tilt_unit(number / book)
        if tilt is None or tilt in seen:
            continue
        seen.append(tilt)
        rows.append((key + " as a fraction of the USD risk the book already sized", tilt))
    return rows


def size_anchors(
    *blobs: Mapping[str, Any] | None,
) -> list[tuple[str, float]] | None:
    """Tilt levels, all in one unit. Fewer than two is not a Score.

    Named score anchors are kept only when they are already that fraction.
    Otherwise the levels are portions of the ticket's USD risk. Equity,
    floor room, notional, lots, and counts are not mixed in.
    """

    views = _views(*blobs)
    explicit = _explicit_tilt_anchors(views)
    if len(explicit) >= 2:
        return explicit
    rows = _risk_tilt_anchors(views)
    if len(rows) >= 2:
        return rows
    return None


def _score_state(
    state: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if isinstance(state, Mapping):
        return dict(state)
    if isinstance(world, Mapping):
        return dict(world)
    return {}


def _tilt_score(
    card: Mapping[str, Any],
    anchors: list[tuple[str, float]],
    ask: Any,
) -> float | None:
    """One spine score. The return is the anchor value, not the level index."""

    try:
        from .nineteen import score
    except Exception:
        return None
    try:
        got = score(
            _score_state(card, None),
            question_id=QUESTION_ID,
            instructions=_INSTRUCTIONS,
            anchors=anchors,
            ask=ask,
        )
    except Exception:
        return None
    if isinstance(got, bool):
        return None
    tilt = _in_tilt_unit(_finite(got))
    if tilt is None:
        return None
    ceiling = max(value for _label, value in anchors)
    floor = min(value for _label, value in anchors)
    if tilt > ceiling or tilt < floor:
        return None
    return tilt


def ca_size_apply_env() -> bool | None:
    """The launch flag, when it is set. Unset is unset, not a size."""

    raw = os.environ.get(APPLY_ENV)
    if raw is None or str(raw).strip() == "":
        return None
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def ca_size_apply_open(*, ticket: Any = None, house_block: bool = False) -> bool | None:
    """Not a size decision. A house block does not restore a tilt."""

    del ticket, house_block
    return None


def ca_size_components(
    world: Mapping[str, Any] | None,
    *,
    side: Any = None,
    answers: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """The seven labels as facts. A missing component stays unset."""

    del side
    packed = dict(world or {})
    if isinstance(answers, Mapping):
        for key, value in answers.items():
            packed.setdefault(key, value)
    out: dict[str, dict[str, Any]] = {}
    for name in _COMPONENT_NAMES:
        block = packed.get(name)
        assembled = isinstance(block, Mapping) and bool(block.get("decidable"))
        incoming: Any = None
        if isinstance(block, Mapping):
            if "choice" in block:
                incoming = block.get("choice")
            elif "named" in block:
                incoming = block.get("named")
        out[name] = {
            "name": name,
            "input": incoming,
            "tilt": None,
            "assembled": assembled,
            "source": name,
        }
    return out


def ca_cross_asset_size_tilt(
    world: Mapping[str, Any] | None = None,
    *,
    side: Any = None,
    answers: Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
    components: Mapping[str, Any] | None = None,
    ask: Any = None,
) -> float | None:
    """The ca tilt. An empty map leaves it unset.

    ``side`` is not a factor. The return is a fraction of the USD risk
    the book already sized. It is not that risk, and it is not a notional.
    """

    del side
    anchors = size_anchors(state, world, answers, components)
    if not anchors:
        return None
    card = state if isinstance(state, Mapping) else world if isinstance(world, Mapping) else {}
    return _tilt_score(card, anchors, ask)


def score_ca_size(
    world: Mapping[str, Any] | None = None,
    *,
    side: Any = None,
    answers: Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
    components: Mapping[str, Any] | None = None,
    house_block: bool = False,
    ticket: Any = None,
    apply: bool | None = None,
    ask: Any = None,
) -> dict[str, Any]:
    """Record the tilt. Empty stays unset. This call does not place or refuse.

    ``house_block``, ``ticket``, and ``apply`` do not fill a missing score.
    """

    del house_block, ticket, apply
    tilt = ca_cross_asset_size_tilt(
        world,
        side=side,
        answers=answers,
        state=state,
        components=components,
        ask=ask,
    )
    return {
        "schema": CA_SIZE_SCHEMA,
        "wire": WIRE_ID,
        "question_id": QUESTION_ID,
        "unit": "tilt",
        "tilt_unit": TILT_UNIT,
        "book_risk_usd": book_risk_usd(state, world, answers, components),
        "consumes": list(CONSUMED_LABELS),
        "tilt": tilt,
        "live": tilt,
        "shadow": tilt,
        "apply": None,
        "apply_env": APPLY_ENV,
        "order_send": False,
        "agent_order_send": False,
        "never_place": True,
        "this_module_places": False,
        "refused": False,
        "components": ca_size_components(world, side=side, answers=answers),
    }
