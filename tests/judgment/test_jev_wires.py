"""Hist-first close_grok jev_wires land — APPLY_CANDIDATE vs KILL fence."""

from __future__ import annotations

import src.judgment as judgment
from src.judgment.compose import compose_shadow
from src.judgment.fluid_pipeline import may_auto_apply
from src.judgment.jev_wires import (
    APPLY_CANDIDATE,
    HARD_BLOCKER_GATES,
    KILL_WIRES,
    LIVE_IMPORT_MODULES,
    PACK1B_BEATEN,
    RESEARCH_ONLY_GATES,
    UNINTEGRATED_MODULES,
    assert_pack_closed,
    classify_module,
    hist_rollup,
    is_kill_wire,
    live_import_stamp,
    refuse_kill_apply,
)
from src.judgment.process_lock import APPLIED_WIRES, wire_apply_open
from src.judgment.veto import InventedNewsProtocolVeto, JevPlacePathVeto


def test_every_unintegrated_module_is_apply_or_kill():
    closed = assert_pack_closed()
    assert closed["ok"] is True
    assert closed["n_unintegrated"] == 46
    assert closed["n_apply_candidate"] + closed["n_kill"] == 46
    assert closed["missing"] == []
    assert closed["extra"] == []
    assert closed["overlap"] == []
    assert closed["resting_shadow_modules"] == []
    for name in UNINTEGRATED_MODULES:
        assert classify_module(name) in {"APPLY_CANDIDATE", "KILL"}


def test_no_resting_shadow_and_pack1b_still_false():
    assert PACK1B_BEATEN is False
    assert judgment.PACK1B_BEATEN is False
    stamp = live_import_stamp()
    assert stamp["pack1b_beaten"] is False
    assert stamp["no_resting_shadow"] is True
    assert stamp["never_place"] is True
    assert stamp["never_order_send"] is True
    assert stamp["no_news_invent"] is True
    assert stamp["login"] == 0
    assert stamp["ns"] == "operator"
    assert stamp["magic"] == 0
    assert stamp["vps_draft_folder_present"] is False
    assert stamp["box_receipt_present"] is False
    assert stamp["closed"] is True
    assert set(stamp["hard_blocker_gates"]) == set(HARD_BLOCKER_GATES)
    assert set(APPLIED_WIRES) <= set(stamp["applied_named_wires"])


def test_apply_wires_live_import_path():
    for name in (
        "compose_shadow",
        "flow_alignment_size_tilt",
        "cost_hurtful_size_tilt",
        "haircut_challenge_unit",
        "maybe_haircut_unit",
        "physical_apply_allowed",
        "score_ca_size",
        "attach_fluid",
        "may_auto_apply",
        "pipeline_snapshot",
        "gold_fanout_questions",
        "vps_land_plan",
        "prove_dual",
        "host_occupancy_governor",
        "hist_prove_allows_label_apply",
        "closed_doc_from_deals",
        "refuse_kill_apply",
        "classify_module",
    ):
        assert name in judgment.__all__
        assert hasattr(judgment, name)
    for module in LIVE_IMPORT_MODULES:
        if module == "jev_wires":
            continue
        assert classify_module(module) == "APPLY_CANDIDATE"


def test_kill_modules_not_exported_and_cannot_apply():
    for name in KILL_WIRES:
        assert name not in judgment.__all__
        assert classify_module(name) == "KILL"
        assert is_kill_wire(name) is True
        assert wire_apply_open(name) is False
        try:
            refuse_kill_apply(name)
        except JevPlacePathVeto as exc:
            assert "kill_fenced" in str(exc)
        else:
            raise AssertionError(f"expected fence for {name}")


def test_hard_blocker_and_research_only_cannot_auto_apply():
    for gate_id in HARD_BLOCKER_GATES:
        assert may_auto_apply(gate_id) is False
        assert may_auto_apply(gate_id, prove_ledger={gate_id: "PROVED_SHADOW"}) is False
        assert wire_apply_open(gate_id) is False
        try:
            refuse_kill_apply(gate_id)
        except JevPlacePathVeto as exc:
            assert "hard_blocker_no_apply" in str(exc)
        else:
            raise AssertionError(f"expected HARD_BLOCKER fence for {gate_id}")
    for gate_id in RESEARCH_ONLY_GATES:
        assert may_auto_apply(gate_id) is False
        assert wire_apply_open(gate_id) is False


def test_news_protocol_still_vetoed():
    try:
        refuse_kill_apply("NEWS_PROTOCOL")
    except InventedNewsProtocolVeto:
        pass
    else:
        raise AssertionError("NEWS_PROTOCOL must stay a veto")
    try:
        refuse_kill_apply("news_calendar_sync")
    except JevPlacePathVeto:
        pass
    else:
        raise AssertionError("news_calendar_sync APPLY must stay fenced")


def test_dig_e_s16_family_is_kill():
    for name in ("s16_flags", "s16_guard", "s16_fixtures", "s16_heuristics"):
        assert classify_module(name) == "KILL"
        assert is_kill_wire(name) is True
    assert is_kill_wire("DIG_MULTI_STAGE_GUARD") is True
    assert is_kill_wire("GTOS_DIG_MULTI_STAGE_GUARD_APPLY") is True
    assert wire_apply_open("DIG_MULTI_STAGE_GUARD") is False


def test_named_apply_wires_still_open_and_compose_stamps_registry():
    assert wire_apply_open("f5_xau_flow_alignment_size_tilt") is True
    assert wire_apply_open("F5-JEV-004") is True
    assert wire_apply_open("ca_cross_asset_size_tilt") is True
    state = {
        "identity": {"side": "short", "family_class": "study", "symbol": "XAUUSD"},
        "completeness": {"state_sufficient_for_live": True},
        "news": {"spine_empty": False},
        "cost": {},
        "timeframes": {"h4": {"trend": 1}},
    }
    row = compose_shadow(state)
    assert row["apply_this_row"] is True
    assert row["jev_wires"]["pack1b_beaten"] is False
    assert row["jev_wires"]["closed"] is True
    assert row["jev_wires"]["n_apply_candidate"] == len(APPLY_CANDIDATE)
    assert row["jev_wires"]["n_kill"] == len(KILL_WIRES)


def test_hist_rollup_matches_sealed_fluid_counts():
    rollup = hist_rollup()
    assert rollup["pack1b_beaten"] is False
    assert rollup["never_place"] is True
    assert rollup["fluid_pipeline"]["n_fluid"] == 48
    assert rollup["fluid_pipeline"]["n_applied"] >= 44
    assert rollup["fluid_pipeline"]["n_shadow"] == 3
    assert may_auto_apply("SEL-V4-002") is False
    assert may_auto_apply("ENV-KILL") is False
