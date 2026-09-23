"""Hard vetoes for the Jev fluid-gate sidecar.

Jev place / remint / flatten stay vetoed unless owner ``PLACE_APPLY=1``
clears the Challenge envelope. Token mint, inbox write, and invented
``NEWS_PROTOCOL`` stay vetoed. That Project file is not in git (V2 §8)
and must not be synthesized here.
"""

from __future__ import annotations

from typing import Iterable, Mapping

from .place_apply import action_unlockable, place_authorized

#: Actions that must never be taken from a Jev answer or fluid-gate APPLY.
BROKER_OR_PAYOUT_ACTIONS = frozenset(
    {
        "place",
        "remint",
        "flatten",
        "move_sl",
        "order_send",
        "mint_token",
        "write_verdict",
        "open_trade",
        "broker",
        "order",
    }
)

INVENTED_NEWS_PROTOCOL = "NEWS_PROTOCOL"

#: Keys that must never appear in the Jev-visible S14 state object.
FORBIDDEN_JEV_STATE_KEYS = frozenset(
    {
        "raw_ohlcv",
        "raw_ticks",
        "ohlcv",
        "ticks",
        "tick_dump",
        "broker_net",
        "profit",
        "R",
        "mfe",
        "mae",
        "expost_on_live_intent",
        "invented_news_events",
        INVENTED_NEWS_PROTOCOL,
    }
)


class JevPlacePathVeto(RuntimeError):
    """Jev / fluid-gate code tried to reach a place / remint / flatten path."""


class InventedNewsProtocolVeto(RuntimeError):
    """Caller asked this tree to invent NEWS_PROTOCOL contents."""


class RawTickDumpVeto(RuntimeError):
    """S14 state tried to send raw OHLCV / ticks / expost to Jev."""


def is_broker_or_payout_action(action: str) -> bool:
    name = str(action or "").strip().lower()
    if name in BROKER_OR_PAYOUT_ACTIONS:
        return True
    return any(token in name for token in ("place", "order_send", "flatten", "remint"))


def refuse_broker_action(action: str) -> None:
    """Raise for broker/payout actions unless PLACE_APPLY unlocks this one."""

    if not is_broker_or_payout_action(action):
        return
    if action_unlockable(action) and place_authorized():
        return
    raise JevPlacePathVeto(
        f"VETO PLACE_PATH: Jev never {action}; intelligence proposes, "
        "printer prints, Chair verbs"
    )


def refuse_invented_news_protocol(names: Iterable[str] | None = None) -> None:
    """Fail closed if a caller asks this tree to invent NEWS_PROTOCOL."""

    requested = {str(n).strip() for n in (names or ())}
    if INVENTED_NEWS_PROTOCOL in requested:
        raise InventedNewsProtocolVeto(
            "VETO NEWS_PROTOCOL: do not invent this Project file from Codila, "
            "TypeSafe, or LangChain sources; event Noul abstains when the spine "
            "is empty"
        )


def assert_answers_have_no_place_path(answers: dict | None) -> None:
    """Refuse a payload whose *selected* choice is place / remint / flatten.

    Probability mass on a forbidden key (lab corr-HOLD often returns
    ``flatten: 0.0``) is not a selected action.
    """

    if not answers:
        return
    for payload in answers.values():
        if not isinstance(payload, dict):
            continue
        refuse_broker_action(str(payload.get("choice") or ""))


def _walk_forbidden_keys(payload: object, *, found: set[str]) -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            name = str(key)
            if name in FORBIDDEN_JEV_STATE_KEYS:
                found.add(name)
            _walk_forbidden_keys(value, found=found)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _walk_forbidden_keys(item, found=found)


def forbidden_jev_keys_in(state: Mapping[str, object] | None) -> set[str]:
    """Return forbidden *keys* present in ``state`` (not substring hits).

    ``"R" in "EURUSD"`` is not a hit — only an actual key named ``R`` is.
    """

    found: set[str] = set()
    if not state:
        return found
    _walk_forbidden_keys(state, found=found)
    return found


def refuse_raw_tick_dump_to_jev(state: Mapping[str, object] | None) -> None:
    """VETO ``no_raw_tick_dump_to_jev`` — buckets only, never ticks/OHLCV/expost."""

    found = forbidden_jev_keys_in(state)
    if found:
        raise RawTickDumpVeto(
            "VETO no_raw_tick_dump_to_jev: forbidden keys in Jev state: "
            + ", ".join(sorted(found))
        )
