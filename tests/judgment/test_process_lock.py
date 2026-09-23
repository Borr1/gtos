import os

from src.judgment.compose import compose_shadow, cost_hurtful_size_tilt, flow_alignment_size_tilt
from tests.judgment.cages import assert_live_cages
from src.judgment.process_lock import (
    APPLIED_WIRES,
    LOCK_ID,
    WIRE_CANDIDATE,
    WIRE_CANDIDATES,
    WIRE_COST,
    WIRE_FLOW,
    leave_orig_ticket,
    live_multiplier,
    owner_has_named,
    ready_to_name,
    stamp_lock,
    wire_apply_open,
)
from src.judgment.wire_prove import prove_dual, prove_shadow


def test_lock_stamp_apply_era_and_leave_orig():
    stamp = stamp_lock()
    assert stamp["process_lock"] == LOCK_ID
    assert stamp["same_pass_blind_live_forbidden"] is True
    assert stamp["eternal_shadow_forbidden"] is True
    assert stamp["wire_apply"] is True
    assert stamp["owner_named"] is True
    assert stamp["owner_named_spoken"] == "apply everything yes"
    assert stamp["leave_orig_293332188"] is True
    assert_live_cages(stamp)
    assert stamp["envelope_walls_stay_integers"] is True
    assert stamp["alive_organism"] is True
    assert set(stamp["applied_wires"]) == set(APPLIED_WIRES)
    assert stamp["wire_candidate"] == WIRE_CANDIDATE
    assert stamp["shadow_both"] is True
    assert set(stamp["wire_candidates"]) == set(WIRE_CANDIDATES)


def test_env_cannot_open_envelope_or_leave_orig(monkeypatch):
    monkeypatch.setenv("GTOS_JEV_W_NAMED", WIRE_CANDIDATE)
    monkeypatch.setenv("GTOS_JEV_APPLY_LIVE", "1")
    assert wire_apply_open("$KILL") is False
    assert wire_apply_open("ENV-H8") is False
    assert wire_apply_open("two_stop_count") is False
    assert wire_apply_open(WIRE_FLOW, ticket="293332188") is False
    assert live_multiplier(0.70, ticket="293332188") == 1.0
    assert leave_orig_ticket("293332188") is True
    assert wire_apply_open(WIRE_FLOW) is True
    assert live_multiplier(0.70, wire_id=WIRE_FLOW) == 0.70
    assert owner_has_named(
        prove={"process_lock": LOCK_ID, "verdict": "PROVED_SHADOW", "wire_candidate": WIRE_CANDIDATE}
    )


def test_compose_live_tilt_moves_except_leave_orig():
    state = {
        "identity": {"side": "short", "family_class": "study"},
        "completeness": {"state_sufficient_for_live": True},
        "news": {"spine_empty": False},
        "cost": {},
        "timeframes": {"h4": {"trend": 1}},  # short vs up = against → shadow 0.70
    }
    row = compose_shadow(state)
    assert row["shadow_size_tilt"] == flow_alignment_size_tilt(0.0)
    assert row["live_size_tilt"] == flow_alignment_size_tilt(0.0)
    assert row["size_tilt"] == row["live_size_tilt"]
    assert row["disposition"] == "named_apply"
    assert row["process_lock"] == LOCK_ID
    assert row["wire_apply"] is True
    assert row["apply_this_row"] is True
    assert row["wires"][WIRE_FLOW]["apply"] is True
    assert row["wires"][WIRE_COST]["cannot_refuse"] is True
    held = compose_shadow(state, ticket="293332188")
    assert held["leave_orig"] is True
    assert held["live_size_tilt"] == 1.0
    assert held["live_cost_tilt"] == 1.0
    assert held["apply_this_row"] is False
    assert held["disposition"] == "log_only"
    assert held["wires"][WIRE_FLOW]["apply"] is False


def test_prove_not_proved_on_empty_tape_rows():
    receipt = prove_shadow(
        [
            {
                "kind": "open",
                "ticket": 293332188,
                "house": {"family_class": "study"},
                "compose": {
                    "shadow_size_tilt": 1.0,
                    "live_size_tilt": 1.0,
                    "wire_apply": False,
                    "disposition": "log_only",
                },
                "state": {
                    "identity": {"symbol": "XAUUSD"},
                    "completeness": {"state_sufficient_for_live": False},
                    "news": {"spine_empty": False, "high_in_f5_window": False},
                },
            }
        ]
    )
    assert receipt["verdict"] == "NOT_PROVED"
    assert receipt["ready_to_name"] is False
    assert any("xau_sufficient" in r for r in receipt["reasons"])


def test_prove_shadow_when_bars_met():
    rows = []
    for i in range(20):
        rows.append(
            {
                "kind": "slate",
                "house": {"family_class": "study"},
                "compose": {
                    "shadow_size_tilt": 0.70 if i < 8 else 1.15,
                    "live_size_tilt": 1.0,
                    "wire_apply": False,
                    "disposition": "log_only",
                },
                "state": {
                    "identity": {"symbol": "XAUUSD"},
                    "completeness": {"state_sufficient_for_live": True},
                    "news": {"spine_empty": False, "high_in_f5_window": False},
                },
            }
        )
    receipt = prove_shadow(rows)
    assert receipt["verdict"] == "PROVED_SHADOW"
    assert receipt["ready_to_name"] is True
    assert receipt["era"] == "shadow_prove"
    assert ready_to_name(prove=receipt) is True
    applied = prove_shadow(rows, era="applied")
    assert applied["verdict"] == "APPLIED_NAMED"


def test_prove_rejects_invented_high_and_live_tilt_in_shadow_era():
    bad = prove_shadow(
        [
            {
                "kind": "open",
                "house": {"family_class": "study"},
                "compose": {"shadow_size_tilt": 0.7, "live_size_tilt": 0.7, "wire_apply": False},
                "state": {
                    "identity": {"symbol": "XAUUSD"},
                    "completeness": {"state_sufficient_for_live": True},
                    "news": {"spine_empty": True, "high_in_f5_window": True},
                },
            }
        ]
        * 20
    )
    assert bad["verdict"] == "NOT_PROVED"
    assert any("invented_high" in r for r in bad["reasons"])
    assert any("live_size_tilt" in r for r in bad["reasons"])
    applied_era = prove_shadow(
        [
            {
                "kind": "slate",
                "house": {"family_class": "study"},
                "compose": {
                    "shadow_size_tilt": 0.7,
                    "live_size_tilt": 0.7,
                    "apply_this_row": True,
                    "disposition": "named_apply",
                },
                "state": {
                    "identity": {"symbol": "XAUUSD"},
                    "completeness": {"state_sufficient_for_live": True},
                    "news": {"spine_empty": False, "high_in_f5_window": False},
                },
            }
        ]
        * 20,
        era="applied",
    )
    assert applied_era["verdict"] == "APPLIED_NAMED"
    assert not any("live_size_tilt" in r for r in applied_era["reasons"])


def test_cost_tilt_cannot_refuse_or_zero():
    assert cost_hurtful_size_tilt(None) == 1.0
    assert cost_hurtful_size_tilt(0.0) == 1.0
    assert cost_hurtful_size_tilt(0.10) == 0.70
    assert cost_hurtful_size_tilt(0.50) == 0.70
    assert cost_hurtful_size_tilt(0.080734) == 0.7578
    assert cost_hurtful_size_tilt(0.20, jev_noul=False) == 1.0
    assert cost_hurtful_size_tilt(0.01, jev_noul=True) == 0.70
    assert cost_hurtful_size_tilt(None, jev_noul=0.5) == 0.85


def test_cost_wire_moves_live_except_leave_orig():
    state = {
        "identity": {"side": "short", "family_class": "study", "symbol": "XAUUSD"},
        "completeness": {"state_sufficient_for_live": False, "cost": True},
        "news": {"spine_empty": False},
        "cost": {"spread_r_of_stop": 0.080734, "cost_screen_would_refuse": False},
        "timeframes": {},
    }
    row = compose_shadow(state)
    assert row["state_sufficient"] is False
    assert row["shadow_size_tilt"] == 1.0  # tape missing — flow stays 1.0
    assert row["shadow_cost_tilt"] == 0.7578
    assert row["live_cost_tilt"] == 0.7578
    assert row["live_cost_tilt"] <= 1.0
    assert row["live_size_tilt"] == 1.0
    assert row["wires"][WIRE_COST]["apply"] is True
    held = compose_shadow(state, ticket="293332188")
    assert held["live_cost_tilt"] == 1.0
    assert held["shadow_cost_tilt"] == 0.7578


def test_prove_cost_on_cost_complete_rows():
    rows = []
    for i in range(20):
        rows.append(
            {
                "kind": "open",
                "house": {"family_class": "study"},
                "compose": {
                    "shadow_size_tilt": 1.0,
                    "live_size_tilt": 1.0,
                    "shadow_cost_tilt": 0.70 if i < 8 else 1.0,
                    "live_cost_tilt": 1.0,
                    "wire_apply": False,
                    "disposition": "log_only",
                },
                "state": {
                    "identity": {"symbol": "XAUUSD"},
                    "completeness": {"state_sufficient_for_live": False, "cost": True},
                    "news": {"spine_empty": False, "high_in_f5_window": False},
                    "cost": {"spread_r_of_stop": 0.12},
                },
            }
        )
    receipt = prove_shadow(rows, wire_id=WIRE_COST)
    assert receipt["verdict"] == "PROVED_SHADOW"
    assert receipt["n_xau_cost_complete"] == 20
    dual = prove_dual(rows)
    assert dual["apply_either"] is True
    assert dual["candidates"][WIRE_COST]["verdict"] == "PROVED_SHADOW"
    assert dual["candidates"][WIRE_FLOW]["verdict"] == "NOT_PROVED"
    assert dual["clears_first_hint"] == WIRE_COST


def test_a1_off_still_stamps_lock():
    os.environ.pop("GTOS_JEV_A1_LOG", None)
    os.environ.pop("GTOS_JEV_ALIVE_SHADOW", None)
    from src.judgment.a1_log import observe

    row = observe("UB-AUTH-010", None)
    assert row["process_lock"] == LOCK_ID
    assert row["wire_apply"] is True
    assert row["leave_orig_293332188"] is True
