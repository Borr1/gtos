"""Challenge admission KEEP/KILL. The live row is the score.

Never order_send. Never invent NEWS_PROTOCOL. An empty score stays unset.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.judgment.admission import (
    APPLY_ENV,
    CEILING_REASON,
    CHOICE_ENV,
    KEEP,
    KEEP_CHOICE_ANSWERS,
    KEEP_NAMES,
    KILL,
    KILL_NAMES,
    PACK1B_BEATEN,
    admission_apply_int,
    admission_apply_open,
    admit_and_size,
    candidate_block_stands,
    choice_path_open,
    env_flag_contract,
    evaluate_candidate,
    overlay_sizeup_allowed_on_challenge,
    receipt_payload,
    refuse_dig_broker_send,
    refuse_news_invent,
    stamp_admission,
    verdict_for,
    write_receipt,
)
from src.judgment.apply_size import CHALLENGE_LOGIN, CHALLENGE_NS
from src.judgment.challenge import VERIFICATION_QUARANTINED
from src.judgment.flags import apply_enabled
from src.judgment.host_occupancy import host_occupancy_governor
from src.judgment.process_lock import ENVELOPE_WALL_IDS
from src.judgment.veto import InventedNewsProtocolVeto, JevPlacePathVeto

SRC = Path(__file__).resolve().parents[2] / "src" / "judgment" / "admission.py"


def _challenge(**kwargs):
    kwargs.setdefault("login", CHALLENGE_LOGIN)
    kwargs.setdefault("ns", CHALLENGE_NS)
    return kwargs


def test_hist_table_is_four_keep_two_kill():
    assert verdict_for("circuit_breaker_open") == KEEP
    assert verdict_for("derisking_into_maxdd_wall") == KEEP
    assert verdict_for(CEILING_REASON) == KEEP
    assert verdict_for("soft_daily_stop_reached") == KEEP
    assert verdict_for("profit_target_protect_derisk") == KILL
    assert verdict_for("leader_impulse_veto") == KILL
    assert KEEP_NAMES == {
        "circuit_breaker_open",
        "derisking_into_maxdd_wall",
        CEILING_REASON,
        "soft_daily_stop_reached",
    }
    assert KILL_NAMES == {
        "profit_target_protect_derisk",
        "leader_impulse_veto",
    }
    assert CEILING_REASON == "ceiling_profile_requires_smooth_ddefense"
    assert PACK1B_BEATEN is False


def test_choice_only_on_keep_challenge():
    for name in KEEP_NAMES:
        assert choice_path_open(name, **_challenge()) is True
        row = evaluate_candidate(name, **_challenge())
        assert row["choice_wired"] is True
        assert row["choice"]["choice"] == "KEEP_INTEGER"
        assert row["choice"]["apply"] is None
        assert tuple(row["choice"]["allowed"]) == KEEP_CHOICE_ANSWERS
        assert row["shadow"] is False
        assert row["status"] == KEEP
        assert row["apply"] is None
        assert row["apply_open"] is None
        assert row["integer_stays_fail_closed"] is True
    for name in KILL_NAMES:
        assert choice_path_open(name, **_challenge()) is False
        row = evaluate_candidate(name, **_challenge())
        assert row["choice"] is None
        assert row["choice_wired"] is False
        assert row["shadow"] is False
        assert row["status"] == KILL
        assert row["dead_soft_path"] is True
        assert "SHADOW" not in str(row["status"])


def test_empty_score_stays_unset_and_keep_kill_are_the_row(monkeypatch):
    monkeypatch.setenv(APPLY_ENV, "1")
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    monkeypatch.setenv("GTOS_JEV_FLUID_GATES_APPLY", "1")
    assert apply_enabled() is True
    assert admission_apply_open(**_challenge()) is None
    assert admission_apply_int(**_challenge()) is None
    assert admission_apply_open(score=None, environ={APPLY_ENV: "1"}) is None
    assert admission_apply_open(score="") is None
    assert admission_apply_open(score="KEEP") == KEEP
    assert admission_apply_int(score="KILL") == KILL
    assert admission_apply_open(row={"verdict": "KEEP"}) == KEEP
    assert admission_apply_open(row={"choice": True, "verdict": "KEEP", "apply": 0}) is None
    row = evaluate_candidate("circuit_breaker_open", **_challenge())
    assert row["apply"] is None
    assert row["apply_open"] is None
    kept = evaluate_candidate("circuit_breaker_open", score="KEEP", **_challenge())
    assert kept["apply"] == KEEP
    killed = evaluate_candidate("circuit_breaker_open", score="KILL", **_challenge())
    assert killed["apply"] == KILL
    stamped = stamp_admission({"reason": "circuit_breaker_open"}, **_challenge())
    assert stamped["apply"] is None
    assert stamped["apply_open"] is None
    assert stamped["n_shadow"] == 0
    assert candidate_block_stands() is None
    assert candidate_block_stands(score=None) is None
    assert candidate_block_stands(score="") is None
    assert candidate_block_stands(score=True) is None
    assert candidate_block_stands(score=0) is None
    assert candidate_block_stands(score="KILL") is False
    assert candidate_block_stands(score="KEEP") is True


def test_w7_and_verification_are_not_challenge():
    w7 = evaluate_candidate(
        "circuit_breaker_open",
        login=0,
        ns="operator_profile",
    )
    assert w7["challenge"] is False
    assert w7["choice_wired"] is False
    assert w7["refuse"] == "not_challenge"
    assert choice_path_open("circuit_breaker_open", ns="operator_profile") is False
    quarantined = evaluate_candidate(
        "circuit_breaker_open",
        login=VERIFICATION_QUARANTINED,
        ns=CHALLENGE_NS,
    )
    assert quarantined["challenge"] is False
    assert quarantined["choice_wired"] is False


def test_unknown_reason_is_not_shadow():
    row = evaluate_candidate("ok", **_challenge())
    assert row["in_hist_table"] is False
    assert row["verdict"] is None
    assert row["shadow"] is False
    assert row["status"] == "NOT_CANDIDATE"
    assert row["choice"] is None


def test_envelope_walls_stay_integers_no_choice():
    for wall in ("ENV-DD", "ENV-KILL", "$KILL", "ENV-H8"):
        assert wall in ENVELOPE_WALL_IDS or wall == "ENV-DD"
        row = evaluate_candidate(wall, **_challenge())
        assert row["choice_wired"] is False
        assert row["envelope_walls_stay_integers"] is True
        assert choice_path_open(wall, **_challenge()) is False
    soft = evaluate_candidate("soft_daily_stop_reached", **_challenge())
    assert soft["envelope_untouched"] == "ENV-DD"
    assert soft["verdict"] == KEEP
    assert soft["choice_wired"] is True
    assert soft["apply"] is None
    assert soft["integer_stays_fail_closed"] is True


def test_leader_impulse_veto_kills_overlay_sizeup():
    assert overlay_sizeup_allowed_on_challenge("leader_impulse_veto") is False
    assert overlay_sizeup_allowed_on_challenge("session_active_stack") is False
    row = evaluate_candidate("leader_impulse_veto", **_challenge())
    assert row["overlay_sizeup_allowed"] is False
    stamped = stamp_admission(
        {"reason": "ok"},
        overlay="leader_impulse_veto",
        **_challenge(),
    )
    assert stamped["n_kill"] == 1
    assert stamped["n_choice_wired"] == 0
    assert stamped["rows"][0]["sid"] == "S33"


def test_choice_flag_off_keeps_integer_without_shadow(monkeypatch):
    monkeypatch.setenv(CHOICE_ENV, "0")
    row = evaluate_candidate("circuit_breaker_open", **_challenge())
    assert row["verdict"] == KEEP
    assert row["choice_wired"] is False
    assert row["status"] == KEEP
    assert row["shadow"] is False
    assert row["integer_stays_fail_closed"] is True


def test_host_occupancy_stamps_keep_and_kill():
    class _Dec:
        governor = {
            "allow_new_entries": False,
            "size_cap_multiplier": 0.0,
            "reason": "circuit_breaker_open",
        }

    pack = host_occupancy_governor(
        symbol="XAUUSD",
        as_of="2026-09-17T10:00:00Z",
        ticket="slate-xau",
        decision=_Dec(),
        opens=[],
        closed_doc={"closed": []},
        namespace=CHALLENGE_NS,
        login=CHALLENGE_LOGIN,
    )
    assert pack["never_place"] is True
    assert pack["admission"]["apply"] == 0
    assert pack["admission"]["n_keep"] == 1
    assert pack["admission"]["n_shadow"] == 0
    assert pack["admission"]["rows"][0]["choice_wired"] is True

    class _Soft:
        governor = {
            "allow_new_entries": False,
            "size_cap_multiplier": 0.0,
            "reason": "soft_daily_stop_reached",
        }

    kept = host_occupancy_governor(
        symbol="XAUUSD",
        as_of="2026-09-17T10:00:00Z",
        decision=_Soft(),
        opens=[],
        closed_doc={"closed": []},
        namespace=CHALLENGE_NS,
        login=CHALLENGE_LOGIN,
    )
    assert kept["admission"]["n_keep"] == 1
    assert kept["admission"]["n_kill"] == 0
    assert kept["admission"]["n_choice_wired"] == 1
    assert kept["admission"]["apply"] == 0
    assert kept["admission"]["rows"][0]["status"] == KEEP
    assert kept["admission"]["rows"][0]["sid"] == "S29"


def test_receipt_has_no_shadow_and_documents_flags(tmp_path):
    receipt = write_receipt(
        dest=tmp_path / "ADMISSION_KEEP_INTEGERS_S28_S33.json",
        md_dest=tmp_path / "ADMISSION_KEEP_INTEGERS_S28_S33.md",
        env_dest=tmp_path / "ADMISSION_KEEP_INTEGERS.md",
    )
    assert receipt["n_keep"] == 4
    assert receipt["n_kill"] == 2
    assert receipt["n_shadow"] == 0
    assert receipt["n_choice_wired"] == 4
    assert receipt["pack1b_beaten"] is False
    assert receipt["admission_apply"] is None
    assert receipt["apply_open"] is None
    assert receipt["consume_stale"] is True
    flags = env_flag_contract()
    assert flags[APPLY_ENV]["can_open_apply"] is False
    env_text = (tmp_path / "ADMISSION_KEEP_INTEGERS.md").read_text(encoding="utf-8")
    assert "GTOS_JEV_ADMISSION_APPLY" in env_text
    assert "GTOS_JEV_ADMISSION_CHOICE" in env_text
    assert "GTOS_JEV_ADMISSION_KEEP" in env_text
    assert "GTOS_JEV_APPLY_LIVE" in env_text
    assert "GTOS_JEV_FLUID_GATES_APPLY" in env_text


def test_payload_matches_chair_consume_stale_table():
    payload = receipt_payload()
    by_sid = {row["sid"]: row for row in payload["rows"]}
    assert by_sid["S28"]["hist"] == "APPLY_CANDIDATE_KEEP"
    assert by_sid["S29"]["hist"] == "APPLY_CANDIDATE_KEEP"
    assert by_sid["S30"]["hist"] == "APPLY_CANDIDATE_KEEP"
    assert by_sid["S32"]["hist"] == "APPLY_CANDIDATE_KEEP"
    assert by_sid["S31"]["hist"] == KILL
    assert by_sid["S33"]["hist"] == KILL
    assert payload["s29_superseded_from"] == "KILL"
    assert payload["s29_evidence"] == "Challenge soft_2pct n=1"
    assert payload["hist_source"] == "DIG_B_STATIC_REMAINING"
    assert by_sid["S32"]["name"] == CEILING_REASON


def test_no_news_invent_and_no_broker_send():
    with pytest.raises(InventedNewsProtocolVeto):
        refuse_news_invent(("NEWS_PROTOCOL",))
    with pytest.raises(InventedNewsProtocolVeto):
        evaluate_candidate("NEWS_PROTOCOL", **_challenge())
    with pytest.raises(JevPlacePathVeto):
        refuse_dig_broker_send("order_send")
    with pytest.raises(RuntimeError, match="ultimate_book"):
        admit_and_size([])


def test_admission_module_ast_never_broker_sends():
    tree = ast.parse(SRC.read_text(encoding="utf-8"), filename=str(SRC))
    banned = {"order_send", "open_trade", "run_book"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "attr", None) or getattr(func, "id", None)
            assert name not in banned
        if isinstance(node, ast.Name):
            assert node.id not in {"order_send", "open_trade"}
    text = SRC.read_text(encoding="utf-8")
    assert "order_send" in text  # named as forbidden
    assert "NEWS_PROTOCOL" not in text or "invent" in text.lower()
    assert "mt5.order" not in text
    assert "RealMT5" not in text
