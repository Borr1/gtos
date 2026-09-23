"""Remint/flatten/deal_close LABEL consume — 60-seat APPLY vs KILL board."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.judgment.challenge import CHALLENGE_LOGIN, CHALLENGE_NS
from src.judgment.place_seat_trust import PLACE_APPLY, PLACE_ENSEMBLE, canonical_sha256
from src.judgment.process_lock import PREAUTH_EFFECTS
from src.judgment.remint_flatten_consume import (
    BOARD_SIZE,
    DEAL_CLOSE_TAPE_TICKETS,
    DIG_B_REMINT_FLATTEN_DRAFTS,
    DRAFT_ID,
    consume_board,
    consume_seats,
    observe_book_owner_consume,
    receipt_payload,
    remint_flatten_choice,
    write_consume_receipt,
)
from src.judgment.veto import JevPlacePathVeto


REPO = Path(__file__).resolve().parents[2]


def test_board_is_sixty_and_draft_id_matches():
    seats = consume_board()
    assert len(seats) == BOARD_SIZE
    assert len(DEAL_CLOSE_TAPE_TICKETS) == 46
    assert len(DIG_B_REMINT_FLATTEN_DRAFTS) == 14
    assert DRAFT_ID == "BOOK_OWNER_REMINT_FLATTEN_CONSUME_DRAFT"
    assert "label" in PREAUTH_EFFECTS


def test_choice_applies_keep_tickets_with_complete_hash_as_label():
    seat = {
        "seat_id": "remint:291794419",
        "kind": "remint",
        "ticket": "291794419",
        "sleeve": "dsp_spring_cl",
        "symbol": "XAUUSD",
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "sha256": canonical_sha256({"ticket": "291794419"}),
    }
    # Use the board's own complete hash so Choice and trust share one digest.
    board = {s["seat_id"]: s for s in consume_board()}
    decision = remint_flatten_choice(board["remint:291794419"])
    assert decision.verdict == "APPLY"
    assert decision.apply is True
    assert decision.chair_verb == "LABEL"
    assert decision.keep_ticket is True
    assert decision.hash_complete is True
    assert decision.as_dict()["broker_effect"] is False


def test_choice_refuses_incomplete_hash_even_on_keep_ticket():
    decision = remint_flatten_choice(
        {
            "seat_id": "remint:incomplete_hash",
            "kind": "remint",
            "ticket": "291794419",
            "sleeve": "dsp_spring_cl",
            "symbol": "XAUUSD",
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "sha256": "deadbeef",
        }
    )
    assert decision.verdict == "KILL"
    assert decision.apply is False
    assert decision.reason == "incomplete_sha256"
    assert decision.hash_complete is False


def test_choice_kills_fn_leave_orig_hard_off_pack1b_news():
    board = {s["seat_id"]: s for s in consume_board()}
    assert remint_flatten_choice(board["remint:redacted_account"]).reason == "redacted_account_forbidden"
    assert remint_flatten_choice(board["remint:293332188"]).reason == "leave_orig_no_remint"
    assert remint_flatten_choice(board["flatten:verification"]).reason == "verification_quarantined"
    assert remint_flatten_choice(board["remint:291076386"]).reason.startswith("hard_off")
    assert remint_flatten_choice(board["flatten:291113462"]).reason.startswith("hard_off")
    assert remint_flatten_choice(board["flatten:pack1b_beaten"]).reason == "pack1b_beaten_must_stay_false"
    news = remint_flatten_choice(board["remint:news_invent"])
    assert news.verdict == "KILL"
    assert news.reason == "news_protocol_invent_veto"


def test_choice_vetoes_place_path():
    with pytest.raises(JevPlacePathVeto):
        remint_flatten_choice(
            {
                "kind": "place",
                "ticket": "291794419",
                "sha256": canonical_sha256({"k": 1}),
            }
        )


def test_receipt_lists_apply_vs_kill_and_never_sends():
    payload = receipt_payload()
    assert payload["board_size"] == BOARD_SIZE
    assert payload["n_apply"] + payload["n_kill"] == BOARD_SIZE
    assert payload["place_apply"] == PLACE_APPLY
    assert payload["place_ensemble"] == PLACE_ENSEMBLE
    assert payload["pack1b_beaten"] is False
    assert payload["never_broker_send"] is True
    assert payload["broker_effect"] is False
    assert payload["apply_is_label_only"] is True

    apply_ids = set(payload["apply_seat_ids"])
    kill_ids = set(payload["kill_seat_ids"])
    assert apply_ids.isdisjoint(kill_ids)
    expected_apply = {
        "deal_close:291087142",
        "deal_close:291794419",
        "deal_close:291816474",
        "remint:291794419",
        "remint:291816474",
        "remint:293540988",
        "flatten:291794419",
        "flatten:291816474",
        "flatten:293540988",
    }
    assert apply_ids == expected_apply
    assert payload["n_apply"] == 9
    assert payload["n_kill"] == 51
    assert "remint:incomplete_hash" in kill_ids
    assert "remint:293332188" in kill_ids
    assert "remint:redacted_account" in kill_ids
    assert "flatten:verification" in kill_ids
    assert "deal_close:293128383" in kill_ids
    assert "deal_close:291072108" in kill_ids


def test_write_receipt_round_trip(tmp_path):
    path = write_consume_receipt(tmp_path / "REMINT_FLATTEN_CONSUME_RECEIPT.json")
    import json

    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["draft_id"] == DRAFT_ID
    assert doc["n_apply"] == 9
    assert len(doc["apply_seats"]) == 9
    assert len(doc["kill_seats"]) == 51


def test_book_owner_observe_is_challenge_only_and_never_mutates():
    fn = observe_book_owner_consume(namespace="redacted_account", live_broker_authority=True)
    assert fn["reason"] in {"not_f5", "redacted_account_forbidden"}
    assert fn["broker_effect"] is False

    w7 = observe_book_owner_consume(namespace="operator_profile")
    assert w7["reason"] == "not_f5"
    assert w7["broker_effect"] is False

    row = observe_book_owner_consume(
        namespace=CHALLENGE_NS,
        live_broker_authority=False,
    )
    assert row["namespace"] == CHALLENGE_NS
    assert row["action"] == "OBSERVE"
    assert row["broker_effect"] is False
    assert row["broker_mutation_allowed"] is False
    assert row["h8_observe_only"] is True
    assert row["n_apply"] == 9
    assert row["pack1b_beaten"] is False
    assert "order_send" not in row
    assert row["never_broker_send"] is True


def test_book_owner_observe_hook_skips_non_challenge_and_never_raises():
    from src.components.ultimate_book.book_owner import UltimateBookOwner

    class _Stub:
        _namespace = "redacted_account"

        def _live_broker_authority(self):
            raise AssertionError("FN must not touch authority")

    summary = {}
    UltimateBookOwner._f5_observe_remint_flatten_consume(_Stub(), summary, None)
    assert summary == {}

    class _Challenge:
        _namespace = CHALLENGE_NS

        def _live_broker_authority(self):
            return False

    summary = {}
    UltimateBookOwner._f5_observe_remint_flatten_consume(_Challenge(), summary, None)
    assert summary["remint_flatten_consume"]["n_apply"] == 9
    assert summary["remint_flatten_consume"]["broker_mutation_allowed"] is False


def test_committed_receipt_matches_apply_kill_ids():
    path = REPO / "judgment" / "astra" / "lab" / "wires" / "REMINT_FLATTEN_CONSUME_RECEIPT.json"
    if not path.is_file():
        pytest.skip("receipt not written yet")
    import json

    doc = json.loads(path.read_text(encoding="utf-8"))
    live = receipt_payload()
    assert set(doc["apply_seat_ids"]) == set(live["apply_seat_ids"])
    assert set(doc["kill_seat_ids"]) == set(live["kill_seat_ids"])
    assert doc["pack1b_beaten"] is False
    assert consume_seats()  # board still 60
