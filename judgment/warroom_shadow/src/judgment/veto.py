"""Hard vetoes for the Jev fluid-gate sidecar.

Jev never places, remints, flattens, moves SL, mints tokens, or writes the
chair inbox. This module also refuses an invented ``NEWS_PROTOCOL`` — that
Project file is not in git (V2 §8) and must not be synthesized here.
"""

from __future__ import annotations

from typing import Iterable

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


class JevPlacePathVeto(RuntimeError):
    """Jev / fluid-gate code tried to reach a place / remint / flatten path."""


class InventedNewsProtocolVeto(RuntimeError):
    """Caller asked this tree to invent NEWS_PROTOCOL contents."""


def is_broker_or_payout_action(action: str) -> bool:
    name = str(action or "").strip().lower()
    if name in BROKER_OR_PAYOUT_ACTIONS:
        return True
    return any(token in name for token in ("place", "order_send", "flatten", "remint"))


def refuse_broker_action(action: str) -> None:
    """Always raise for place / remint / flatten / token mint / inbox write."""

    if is_broker_or_payout_action(action):
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
