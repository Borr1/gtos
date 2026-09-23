"""A book question names a ticket only when the live read returned one."""

from __future__ import annotations

from types import SimpleNamespace

from src.components.ultimate_book.open_tickets import question_with_open_tickets


def test_flat_book_question_carries_no_ticket_text():
    raw = SimpleNamespace(positions_get=lambda: ())
    text, card = question_with_open_tickets(
        "The two sides of closing the book after daily-loss or the risk floor.",
        raw,
    )
    assert card == {"open_tickets": "none"}
    assert "ticket" not in text.lower()


def test_one_live_position_names_that_ticket():
    raw = SimpleNamespace(positions_get=lambda: [SimpleNamespace(ticket=881122)])
    text, card = question_with_open_tickets(
        "The two sides of closing the book after daily-loss or the risk floor.",
        raw,
    )
    assert card == {"open_tickets": [881122]}
    assert text.endswith("Open ticket 881122.")
    assert "294215389" not in text


def test_failed_read_does_not_name_a_ticket():
    raw = SimpleNamespace(positions_get=lambda: None)
    text, card = question_with_open_tickets(
        "The two sides of closing the book after daily-loss or the risk floor.",
        raw,
    )
    assert card == {"open_tickets": "unread"}
    assert "ticket" not in text.lower()


def test_gold_sleeve_card_names_only_a_live_ticket():
    from src.judgment.gold_sleeve_ifs import OPEN_GOLD_SLEEVE, gold_subtree_questions

    flat = SimpleNamespace(positions_get=lambda: ())
    pack = gold_subtree_questions(OPEN_GOLD_SLEEVE, symbol="XAUUSD", raw=flat)
    text = pack["questions"]["gold_vs_sibling"]["instructions"]
    assert pack["open_ticket_card"] == {"open_tickets": "none"}
    assert "294215389" not in text
    assert "ticket" not in text.lower()

    live = SimpleNamespace(positions_get=lambda: [SimpleNamespace(ticket=881122)])
    pack = gold_subtree_questions(OPEN_GOLD_SLEEVE, symbol="XAUUSD", raw=live)
    text = pack["questions"]["gold_vs_sibling"]["instructions"]
    assert pack["open_ticket_card"] == {"open_tickets": [881122]}
    assert text.endswith("Open ticket 881122.")
    assert "294215389" not in text


def test_hop_open_gold_sleeve_comes_from_the_live_gold_comment():
    from src.judgment.gold_sleeve_ifs import OPEN_GOLD_SLEEVE, _hop_state

    flat = SimpleNamespace(positions_get=lambda: ())
    state = _hop_state(sleeve="dsp_x", symbol="XAUUSD", raw=flat)
    assert "open_gold_sleeve" not in state

    gold = SimpleNamespace(
        positions_get=lambda: [
            SimpleNamespace(ticket=881122, symbol="XAUUSD", comment="live_gold_comment"),
        ]
    )
    state = _hop_state(
        sleeve="dsp_x",
        symbol="XAUUSD",
        extra={"open_gold_sleeve": OPEN_GOLD_SLEEVE},
        raw=gold,
    )
    assert state["open_gold_sleeve"] == "live_gold_comment"

    other = SimpleNamespace(
        positions_get=lambda: [
            SimpleNamespace(ticket=770011, symbol="EURUSD", comment=OPEN_GOLD_SLEEVE),
        ]
    )
    state = _hop_state(sleeve="dsp_x", symbol="XAUUSD", raw=other)
    assert "open_gold_sleeve" not in state


def test_open_gold_facts_use_only_the_live_gold_position():
    from pathlib import Path

    from src.judgment.learning_choices import _open_gold_facts

    root = Path("/tmp")
    flat = SimpleNamespace(positions_get=lambda: ())
    facts = _open_gold_facts(root, raw=flat)
    assert facts["present"] is False
    assert facts["symbol"] is None
    assert facts["sleeve"] is None
    assert facts["open_tickets"] == "none"

    gold = SimpleNamespace(
        positions_get=lambda: [
            SimpleNamespace(ticket=881122, symbol="XAUUSD", comment="live_gold_comment"),
        ]
    )
    facts = _open_gold_facts(root, raw=gold)
    assert facts["present"] is True
    assert facts["symbol"] == "XAUUSD"
    assert facts["sleeve"] == "live_gold_comment"
    assert facts["open_tickets"] == [881122]

    other = SimpleNamespace(
        positions_get=lambda: [
            SimpleNamespace(ticket=770011, symbol="EURUSD", comment="dsp_descending_lows_accepted"),
        ]
    )
    facts = _open_gold_facts(root, raw=other)
    assert facts["present"] is False
    assert facts["symbol"] is None
    assert facts["sleeve"] is None
    assert facts["open_tickets"] == "none"
    assert facts["open_tickets"] != [770011]
