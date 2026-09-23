"""PLACE_APPLY owner unlock vs Challenge envelope.

A: cage lifts on PLACE_APPLY=1 + hist-prove + Challenge identity.
B: envelope (identity, kill, Jev dark, redacted_account, NEWS invent, leave-orig)
   stays fail-closed even when PLACE_APPLY=1.
"""

from __future__ import annotations

import pytest

from src.judgment.flags import ProveReceipt, apply_authorized
from src.judgment.place_apply import (
    PLACE_APPLY_ENV,
    cage_stamp,
    evaluate_place_apply,
    place_authorized,
)
from src.judgment.process_lock import stamp_lock
from src.judgment.veto import JevPlacePathVeto, refuse_broker_action


def test_default_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PLACE_APPLY_ENV, raising=False)
    monkeypatch.delenv("GTOS_JEV_PLACE_APPLY", raising=False)
    decision = evaluate_place_apply()
    assert decision.allowed is False
    assert decision.reason == "place_apply_off"
    stamp = stamp_lock()
    assert stamp["never_place"] is True
    assert stamp["never_remint"] is True
    assert stamp["never_flatten"] is True
    assert stamp["place_apply"] is False
    with pytest.raises(JevPlacePathVeto):
        refuse_broker_action("place")
    with pytest.raises(JevPlacePathVeto):
        refuse_broker_action("mint_token")


def test_place_apply_lifts_challenge_cages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLACE_APPLY_ENV, "1")
    monkeypatch.delenv("GTOS_JEV_DARK", raising=False)
    monkeypatch.delenv("GTOS_JEV_A1_CALL", raising=False)
    monkeypatch.delenv("GTOS_JEV_KILL", raising=False)
    decision = evaluate_place_apply()
    assert decision.allowed is True
    assert decision.reason == "place_apply_authorized"
    stamp = stamp_lock()
    assert stamp["never_place"] is False
    assert stamp["never_remint"] is False
    assert stamp["never_flatten"] is False
    assert stamp["envelope_walls_stay_integers"] is True
    refuse_broker_action("place")
    refuse_broker_action("remint")
    refuse_broker_action("flatten")
    with pytest.raises(JevPlacePathVeto):
        refuse_broker_action("mint_token")
    with pytest.raises(JevPlacePathVeto):
        refuse_broker_action("write_verdict")


def test_envelope_kill_flag_stays_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLACE_APPLY_ENV, "1")
    monkeypatch.setenv("GTOS_JEV_KILL", "1")
    assert place_authorized() is False
    assert evaluate_place_apply().reason.startswith("kill_flag")
    assert cage_stamp()["never_place"] is True
    with pytest.raises(JevPlacePathVeto):
        refuse_broker_action("place")


def test_envelope_jev_dark_stays_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLACE_APPLY_ENV, "1")
    monkeypatch.setenv("GTOS_JEV_DARK", "1")
    assert evaluate_place_apply().reason == "jev_dark"
    assert cage_stamp()["never_place"] is True


def test_a1_call_off_is_not_organism_dark(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLACE_APPLY_ENV, "1")
    monkeypatch.setenv("GTOS_JEV_A1_CALL", "0")
    monkeypatch.delenv("GTOS_JEV_DARK", raising=False)
    assert evaluate_place_apply().reason == "place_apply_authorized"


def test_envelope_redacted_account_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLACE_APPLY_ENV, "1")
    decision = evaluate_place_apply(ns="redacted_account")
    assert decision.allowed is False
    assert decision.reason == "redacted_account_forbidden"


def test_envelope_wrong_login_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLACE_APPLY_ENV, "1")
    decision = evaluate_place_apply(login="0")
    assert decision.allowed is False
    assert decision.reason == "identity_not_challenge"


def test_envelope_news_invent_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLACE_APPLY_ENV, "1")
    decision = evaluate_place_apply(invented_files=("NEWS_PROTOCOL",))
    assert decision.allowed is False
    assert decision.reason == "news_invent"


def test_envelope_leave_orig_stays_locked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLACE_APPLY_ENV, "1")
    decision = evaluate_place_apply(ticket="293332188")
    assert decision.allowed is False
    assert decision.reason == "leave_orig"


def test_hist_prove_missing_blocks_unlock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PLACE_APPLY_ENV, "1")
    decision = evaluate_place_apply(hist_prove={"allowed": False, "reason": "hist_prove_receipt_missing"})
    assert decision.allowed is False
    assert decision.reason == "hist_prove_receipt_missing"


def test_apply_authorized_place_respects_unlock(monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = ProveReceipt("UB-AUTH-010", "A1", True, "chair")
    monkeypatch.delenv(PLACE_APPLY_ENV, raising=False)
    monkeypatch.delenv("GTOS_JEV_PLACE_APPLY", raising=False)
    denied = apply_authorized(
        stake="place", apply_flag=True, receipt=receipt, band="HIGH", required_band="VETO"
    )
    assert denied.apply is False
    assert denied.mode == "veto"
    monkeypatch.setenv(PLACE_APPLY_ENV, "1")
    monkeypatch.delenv("GTOS_JEV_DARK", raising=False)
    monkeypatch.delenv("GTOS_JEV_A1_CALL", raising=False)
    opened = apply_authorized(
        stake="place", apply_flag=True, receipt=receipt, band="HIGH", required_band="VETO"
    )
    assert opened.apply is True
    assert opened.reason == "place_apply_authorized"
    assert opened.mode == "place"
