from src.judgment.compose import compose_shadow
from src.judgment.fluid_gates import is_envelope, lookup
from src.judgment.fluid_local import local_answers
from src.judgment.fluid_pipeline import may_auto_apply
from src.judgment.fluid_prove import prove_gate, prove_remaining
from src.judgment.process_lock import WIRE_COST, WIRE_FLOW


def _xau_state(**news):
    return {
        "identity": {"symbol": "XAUUSD", "side": "short", "family_class": "study", "sleeve": "dsp_two_bar_t"},
        "completeness": {"state_sufficient_for_live": True, "cost": True},
        "news": {"spine_empty": False, "high_in_f5_window": False, "events": [{"event": "CPI", "minutes_from_as_of": 40}], **news},
        "cost": {"spread_r_of_stop": 0.08},
        "timeframes": {"h4": {"trend": 1}, "m15": {"atr14": 4.0}},
        "geometry": {"entry": 4331.0, "stop_dist": 5.45, "atr14": 4.0},
        "levels": {"prior_day_high": 4340.0, "prior_day_low": 4300.0, "source": "wave21"},
        "sessions": {"named": "london", "utc_hour": 8},
        "clock": {"is_friday": False},
        "occupancy": {},
        "sleeve_features": {},
    }


def test_local_answers_do_not_invent_high_on_empty_spine():
    state = _xau_state()
    state["news"] = {"spine_empty": True, "high_in_f5_window": None, "events": []}
    answers = local_answers(state, extra={"kind": "slate"}, ticket="1")
    assert answers["high_in_f5_window"]["decidable"] is False
    assert answers["event_size"]["score"] == 1.0
    assert answers["spine_empty_honesty"]["noul"] is True


def test_compose_stamps_48_fluid_and_leave_orig_stays_one():
    row = compose_shadow(_xau_state(), ticket="292667008")
    assert row["fluid"]["n"] == 48
    assert row["fluid"]["gates"][WIRE_FLOW]["decidable"] is True
    held = compose_shadow(_xau_state(), ticket="293332188")
    assert held["leave_orig"] is True
    assert held["live_size_tilt"] == 1.0
    assert held["fluid"]["gates"][WIRE_FLOW]["live"] == 1.0
    assert held["fluid"]["gates"][WIRE_FLOW]["apply"] is False


def test_prove_rejects_invented_high():
    rows = []
    for i in range(20):
        state = _xau_state()
        state["news"] = {"spine_empty": True, "high_in_f5_window": True, "events": []}
        composed = compose_shadow(state, ticket=str(1000 + i))
        rows.append({"kind": "slate", "compose": composed, "state": state})
    gate = lookup("FLUID-NWS-002")
    rec = prove_gate(rows, gate)
    assert rec["verdict"] == "NOT_PROVED"
    assert any("invented_high" in r for r in rec["reasons"])


def test_prove_session_size_when_bars_met():
    rows = []
    for i in range(24):
        state = _xau_state()
        state["sessions"] = {"named": "london" if i < 12 else "asia", "utc_hour": 8 if i < 12 else 3}
        composed = compose_shadow(state, ticket=str(2000 + i))
        rows.append({"kind": "slate", "compose": composed, "state": state})
    rec = prove_gate(rows, lookup("FLUID-SIZ-003"))
    assert rec["verdict"] == "PROVED_SHADOW"
    assert rec["ready_to_apply"] is True
    assert may_auto_apply("FLUID-SIZ-003", prove_ledger={"FLUID-SIZ-003": "PROVED_SHADOW"}) is True


def test_sel_v4_002_cannot_apply_even_if_proved():
    assert lookup("SEL-V4-002")["research_only"] is True
    assert may_auto_apply("SEL-V4-002", prove_ledger={"SEL-V4-002": "PROVED_SHADOW"}) is False


def test_occupancy_noul_proves_when_true_and_false_present():
    rows = []
    for i in range(24):
        state = _xau_state()
        state["occupancy"] = {"symbol_open": i < 8, "isolated_reentry_legal": i >= 8}
        composed = compose_shadow(state, ticket=str(3000 + i))
        rows.append({"kind": "slate", "compose": composed, "state": state})
    rec = prove_gate(rows, lookup("FLUID-PLC-004"))
    assert rec["verdict"] == "PROVED_SHADOW"
    assert rec["n_distinct"] >= 2


def test_geometry_mid_band_counts_as_moved_label():
    rows = []
    for i in range(24):
        state = _xau_state()
        # 1.0/4=0.25 → 0; 5.45/4=1.36 → 1 mid-band (must count as moved)
        state["geometry"] = dict(state["geometry"])
        state["geometry"]["stop_dist"] = 1.0 if i < 8 else 5.45
        composed = compose_shadow(state, ticket=str(4000 + i))
        rows.append({"kind": "slate", "compose": composed, "state": state})
    rec = prove_gate(rows, lookup("FLUID-ADM-005"))
    assert rec["verdict"] == "PROVED_SHADOW"
    assert rec["n_moved"] >= 20
    assert rec["n_distinct"] >= 2


def test_ac60_size_scores_named_band():
    rows = []
    for i in range(24):
        state = _xau_state()
        state["sleeve_features"] = {"ac60": -0.05 if i < 12 else 0.16}
        composed = compose_shadow(state, ticket=str(5000 + i))
        rows.append({"kind": "slate", "compose": composed, "state": state})
    rec = prove_gate(rows, lookup("FLUID-SIZ-007"))
    assert rec["verdict"] == "PROVED_SHADOW"
    assert rec["n_distinct"] >= 2


def test_hold_too_late_only_on_closes():
    answers = local_answers(_xau_state(), extra={"kind": "slate"}, ticket="1")
    assert answers["hold_too_late"]["decidable"] is False
    closed = local_answers(
        _xau_state(),
        extra={"kind": "deal_close", "close_reason": "EXPERT|close_vnext_time_stop"},
        ticket="2",
    )
    assert closed["hold_too_late"]["decidable"] is True
    assert closed["hold_too_late"]["noul"] is True


def test_envelope_not_in_remaining_prove():
    assert is_envelope("ENV-H8")
    receipt = prove_remaining([])
    assert "ENV-H8" not in receipt["gates"]
    assert WIRE_FLOW in receipt["gates"]
    assert receipt["gates"][WIRE_FLOW]["verdict"] == "APPLIED_NAMED"
