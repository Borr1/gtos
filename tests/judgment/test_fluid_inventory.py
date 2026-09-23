from src.judgment.a1_log import observe_fluid_inventory
from src.judgment.fluid_gates import (
    EXPECTED_ENVELOPE,
    EXPECTED_FLUID,
    assert_inventory_shape,
    auto_apply_eligible,
    fluid_gate_ids,
    is_envelope,
    lookup,
)
from src.judgment.fluid_pipeline import may_auto_apply, pipeline_snapshot
from src.judgment.jev_questions import gold_fanout_questions
from src.judgment.process_lock import APPLIED_WIRES, WIRE_CA_SIZE, WIRE_COST, WIRE_FLOW


def test_inventory_is_48_fluid_and_8_envelope():
    shape = assert_inventory_shape()
    assert shape["ok"] is True
    assert shape["n_fluid"] == EXPECTED_FLUID == 48
    assert shape["n_envelope"] == EXPECTED_ENVELOPE == 8
    assert not shape["duplicate_ids"]
    ids = fluid_gate_ids()
    assert WIRE_FLOW in ids
    assert WIRE_COST in ids
    assert "SEL-V4-002" in ids
    assert lookup("SEL-V4-002")["research_only"] is True
    assert is_envelope("ENV-KILL")
    assert is_envelope("$KILL")
    assert is_envelope("ENV-TWO-STOP")
    assert is_envelope("ENV-H8")
    assert lookup("ENV-KILL")["class"] == "envelope"


def test_applied_wires_and_preauth_pipeline():
    assert lookup(WIRE_FLOW)["status"] == "APPLIED_NAMED"
    assert lookup(WIRE_COST)["status"] == "APPLIED_NAMED"
    assert lookup(WIRE_COST)["cannot_refuse"] is True
    snap = pipeline_snapshot()
    assert snap["n_fluid"] == 48
    assert snap["n_applied"] >= 2
    assert may_auto_apply(WIRE_FLOW) is True
    assert may_auto_apply("ENV-H8") is False
    assert may_auto_apply("SEL-V4-002") is False
    later = lookup("FLUID-SIZ-003")
    assert auto_apply_eligible(later) is True
    if later.get("status") == "SHADOW":
        assert may_auto_apply("FLUID-SIZ-003") is False
    assert may_auto_apply("FLUID-SIZ-003", prove_ledger={"FLUID-SIZ-003": "PROVED_SHADOW"}) is True
    assert set(APPLIED_WIRES) == {WIRE_FLOW, WIRE_COST, WIRE_CA_SIZE}
    assert WIRE_CA_SIZE not in fluid_gate_ids()  # named fire, not a 49th fluid


def test_fanout_covers_inventory_questions():
    questions = gold_fanout_questions()
    for gate in (
        "state_sufficient",
        "flow_alignment",
        "cost_hurtful",
        "level_respect",
        "calendar_honest",
        "close_label",
        "isolated_reentry",
        "two_stop_would_be_third",
        "spine_empty_honesty",
        "leave_orig_293332188",
    ):
        assert gate in questions


def test_observe_fluid_inventory_off_stamps_48():
    row = observe_fluid_inventory(None)
    assert row["skipped"] == "GTOS_JEV_A1_LOG_off"
    assert row["n_fluid"] == 48
    assert row["never_place"] is True
    assert len(row["fluid_ids"]) == 48
