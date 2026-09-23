"""Behavioural tests for PLACE_CHOICE hash stamps (Dig F consume).

No broker, no order_send, Challenge 0 only.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.judgment.alive_menu import rebuild_choice_criteria
from src.judgment.challenge import CHALLENGE_LOGIN, PayoutWriterError, VERIFICATION_QUARANTINED
from src.judgment.inventory import collect_live_inventory
from src.judgment.place_choice import (
    HASH_KEYS,
    IncompletePlaceChoiceHashes,
    assert_place_choice_hashes,
    is_complete_hash,
    jev_repeatability_probe,
    stamp_place_choice,
)
from src.judgment.place_consume_flags import (
    NEW_BROKER_FLAGS,
    PACK1B_BEATEN,
    PLACE_APPLY,
    already_live_consume,
)
from src.judgment.veto import InventedNewsProtocolVeto


def _inventory(**kwargs):
    return collect_live_inventory(
        sleeves=kwargs.get("sleeves", ("spring", "vss")),
        workers=kwargs.get("workers", ("challenge:0",)),
        handlers=kwargs.get("handlers", ("shadow_log", "label_draft")),
        include_w7_armed=False,
        include_launcher_workers=False,
        include_research_armed=False,
    )


def _menu():
    return rebuild_choice_criteria(_inventory())


def test_complete_hashes_stamp_and_never_broker() -> None:
    menu = _menu()
    stamp = stamp_place_choice(menu=menu, option_order=menu.option_ids, state=None)
    assert stamp.complete is True
    assert stamp.missing == ()
    assert stamp.broker_effect is False
    assert stamp.never_place is True
    assert stamp.pack1b_beaten is False
    assert stamp.place_apply is PLACE_APPLY
    assert stamp.login == CHALLENGE_LOGIN
    for key in HASH_KEYS:
        assert is_complete_hash(getattr(stamp, key))
    assert "option_order_sensitivity" in stamp.consumes
    assert "state_evidence_sufficiency" in stamp.consumes
    assert "jev_repeatability_probe" in stamp.consumes


def test_incomplete_menu_hash_refuses() -> None:
    menu = _menu()
    with pytest.raises(IncompletePlaceChoiceHashes, match="menu_hash"):
        stamp_place_choice(menu=menu, menu_hash="abc")
    with pytest.raises(IncompletePlaceChoiceHashes, match="menu_hash"):
        assert_place_choice_hashes(
            menu_hash="",
            option_order_hash="a" * 64,
            state_hash="b" * 64,
        )


def test_incomplete_option_order_hash_refuses() -> None:
    menu = _menu()
    with pytest.raises(IncompletePlaceChoiceHashes, match="option_order_hash"):
        stamp_place_choice(menu=menu, option_order_hash="deadbeef")
    with pytest.raises(IncompletePlaceChoiceHashes, match="option_order_hash"):
        stamp_place_choice(menu=menu, option_order_hash="0" * 64)


def test_incomplete_state_hash_refuses() -> None:
    menu = _menu()
    with pytest.raises(IncompletePlaceChoiceHashes, match="state_hash"):
        stamp_place_choice(menu=menu, state_hash="not-a-hash")
    with pytest.raises(IncompletePlaceChoiceHashes, match="state_hash"):
        assert_place_choice_hashes(
            menu_hash="a" * 64,
            option_order_hash="b" * 64,
            state_hash=None,
        )


def test_option_order_sensitivity_changes_hash() -> None:
    menu = _menu()
    forward = stamp_place_choice(menu=menu, option_order=menu.option_ids)
    reversed_order = tuple(reversed(menu.option_ids))
    backward = stamp_place_choice(menu=menu, option_order=reversed_order)
    assert forward.option_order_hash != backward.option_order_hash
    assert forward.menu_hash == backward.menu_hash


def test_state_evidence_sufficiency_changes_hash() -> None:
    menu = _menu()
    empty = stamp_place_choice(menu=menu, state=None)
    sufficient = stamp_place_choice(
        menu=menu,
        state={
            "identity": {"login": CHALLENGE_LOGIN, "symbol": "XAUUSD", "sleeve": "spring"},
            "completeness": {"state_sufficient_for_live": True},
        },
    )
    assert empty.state_hash != sufficient.state_hash
    assert empty.state_sufficient is False
    assert sufficient.state_sufficient is True
    assert is_complete_hash(empty.state_hash)


def test_jev_repeatability_probe_same_inputs() -> None:
    menu = _menu()
    state = {"completeness": {"state_sufficient_for_live": False}}
    probe = jev_repeatability_probe(menu=menu, option_order=menu.option_ids, state=state)
    assert probe["repeatable"] is True
    assert probe["broker_effect"] is False
    assert probe["never_place"] is True
    assert probe["pack1b_beaten"] is False
    for key in HASH_KEYS:
        assert is_complete_hash(probe["hashes"][key])


def test_place_choice_challenge_only() -> None:
    menu = _menu()
    with pytest.raises(PayoutWriterError):
        stamp_place_choice(menu=menu, login="ftmo_w7")
    from src.judgment.challenge import QuarantinedAccountError

    with pytest.raises(QuarantinedAccountError):
        stamp_place_choice(menu=menu, login=VERIFICATION_QUARANTINED)


def test_place_choice_refuses_invented_news() -> None:
    menu = _menu()
    with pytest.raises(InventedNewsProtocolVeto):
        stamp_place_choice(menu=menu, invented_files=("NEWS_PROTOCOL",))


def test_already_live_consume_has_no_new_broker_flags() -> None:
    block = already_live_consume()
    assert block["already_live"]["CONF_ORDER_CONSUME"] is True
    assert block["already_live"]["PLACE_APPLY"] is True
    assert block["already_live"]["PLACE_ENSEMBLE"] is True
    assert block["new_broker_flags"] == []
    assert NEW_BROKER_FLAGS == ()
    assert block["pack1b_beaten"] is PACK1B_BEATEN
    assert PACK1B_BEATEN is False
    assert block["dig_never_broker_send"] is True
    assert block["news_invent"] is False


def test_place_choice_module_has_no_order_send() -> None:
    src = Path(__file__).resolve().parents[2] / "src" / "judgment" / "place_choice.py"
    tree = ast.parse(src.read_text(encoding="utf-8"), filename=str(src))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            assert name not in {"order_send", "open_trade"}
        if isinstance(node, ast.ImportFrom):
            assert "mt5" not in (node.module or "").lower()
