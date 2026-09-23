"""The book-lane rerate producer: what it admits, what it refuses, and whether its R is right.

The admission tests exist because of a specific, expensive precedent — Session P published 71,969
still-open positions as completed holds, a 2.49x overstatement of the one number OD-3 turns on.
Every refusal path here is a named, counted reason rather than a silent drop.
"""
import json
from pathlib import Path

import pytest

from src.components.ultimate_book.live_evidence import (
    _survives,
    build_sleeve_evidence,
    collect_realized_fills,
    price_closed_position,
)

REPO = Path(__file__).resolve().parents[2]
CALIBRATION = REPO / "research/operations/learning_lane_2026_07_29/LIVE_EVIDENCE_CALIBRATION_V1.json"


def _packet(**over) -> dict:
    """A closed SHORT with exact, hand-checkable geometry.

    fill 100.0, stop 102.0 -> risk 2.0 price units
    exit 97.0             -> travel 3.0 price units in the trade's favour
    gross profit 30.0 cash -> 10.0 cash per price unit -> risk_cash 20.0
    charges -1.0 commission, -0.5 swap -> realized 28.5 -> net R = 28.5/20.0 = 1.425
    """
    o = {
        "sleeve": "crypto",
        "namespace": "operator_profile",
        "symbol": "BTCUSD",
        "broker_symbol": "BTCUSD",
        "direction": "SHORT",
        "trade_lifecycle_status": "closed",
        "broker_exit_time_utc": "2026-07-02T16:03:00+00:00",
        "broker_fill_time_utc": "2026-07-01T16:03:00+00:00",
        "broker_position_fill_price": 100.0,
        "broker_position_fill_adjusted_stop_loss": 102.0,
        "broker_exit_price": 97.0,
        "broker_position_aggregate_profit": 30.0,
        "broker_position_aggregate_commission": -1.0,
        "broker_position_aggregate_swap": -0.5,
        "broker_position_aggregate_fee": 0.0,
        "broker_realized_pnl": 28.5,
        "broker_position_accounting_coverage_status": "entry_and_exit_deals_present",
    }
    o.update(over)
    return {"event_type": "position_closed", "namespace": o["namespace"], "sleeve": o["sleeve"], "outcome": o}


# --------------------------------------------------------------------- the R derivation

def test_realized_r_is_derived_exactly_without_needing_volume():
    fill, reason = price_closed_position(_packet())
    assert reason is None and fill is not None
    assert fill.risk_px == pytest.approx(2.0)
    assert fill.risk_cash == pytest.approx(20.0)
    assert fill.gross_r == pytest.approx(1.5)          # 30.0 / 20.0
    assert fill.realized_net_r == pytest.approx(1.425)  # 28.5 / 20.0
    assert fill.realized_cost_r == pytest.approx(0.075)  # (1.0 + 0.5) / 20.0, positive drag
    assert fill.cost_coverage == "MEASURED"
    assert fill.hold_hours == pytest.approx(24.0)


def test_long_and_short_are_symmetric():
    short = price_closed_position(_packet())[0]
    long_ = price_closed_position(_packet(
        direction="LONG", broker_position_fill_price=100.0,
        broker_position_fill_adjusted_stop_loss=98.0, broker_exit_price=103.0))[0]
    assert long_.realized_net_r == pytest.approx(short.realized_net_r)


def test_cost_is_a_positive_drag_and_net_is_below_gross():
    fill = price_closed_position(_packet())[0]
    assert fill.realized_cost_r > 0
    assert fill.realized_net_r < fill.gross_r


def test_costs_are_never_silently_zero_when_the_broker_charged_them():
    """F38 in one assertion: a charged cost must appear in the R that feeds the learning rule."""
    charged = price_closed_position(_packet())[0]
    free = price_closed_position(_packet(
        broker_position_aggregate_commission=0.0, broker_position_aggregate_swap=0.0,
        broker_realized_pnl=30.0))[0]
    assert charged.realized_net_r < free.realized_net_r
    assert free.realized_cost_r == pytest.approx(0.0)


# --------------------------------------------------------------------- admission and refusal

def test_position_without_a_broker_exit_deal_is_refused():
    """No broker exit deal => no realized cost or price, so it cannot be priced at broker truth.

    Named for what it is. These rows ARE completed holds (`trade_lifecycle_status == "closed"` on
    61/61 in the live export); what they lack is the deal-record join.
    """
    fill, reason = price_closed_position(_packet(broker_exit_time_utc=None))
    assert fill is None
    assert reason == "no_broker_exit_deal_record_join"


def test_non_closed_lifecycle_is_refused():
    fill, reason = price_closed_position(_packet(trade_lifecycle_status="managing"))
    assert fill is None and reason == "not_lifecycle_closed"


def test_zero_price_travel_is_refused_not_infinite():
    """A scratch close makes the cash bridge undefined; it must refuse, not divide by ~0."""
    fill, reason = price_closed_position(_packet(broker_exit_price=100.0))
    assert fill is None and reason == "zero_price_travel_cash_bridge_undefined"


def test_zero_stop_distance_is_refused():
    fill, reason = price_closed_position(_packet(broker_position_fill_adjusted_stop_loss=100.0))
    assert fill is None and reason == "zero_stop_distance"


def test_profit_disagreeing_with_price_travel_is_refused():
    fill, reason = price_closed_position(_packet(broker_position_aggregate_profit=-30.0))
    assert fill is None and reason == "inconsistent_profit_vs_price_travel"


def test_unmapped_namespace_is_refused_not_defaulted():
    fill, reason = price_closed_position(_packet(namespace="some_other_account"))
    assert fill is None and reason.startswith("unmapped_namespace")


def test_missing_direction_is_refused():
    fill, reason = price_closed_position(_packet(direction=None))
    assert fill is None and reason == "missing_direction"


def test_refusals_are_counted_and_published_not_dropped():
    packets = [_packet(), _packet(broker_exit_time_utc=None), _packet(broker_exit_price=100.0)]
    rep = collect_realized_fills(packets)
    assert rep.closed_rows == 3
    assert len(rep.fills) == 1
    assert sum(rep.rejected.values()) == 2
    assert set(rep.rejected) == {
        "no_broker_exit_deal_record_join",
        "zero_price_travel_cash_bridge_undefined",
    }
    assert rep.rejected_examples  # each refusal keeps an identifying example


def test_non_closed_event_types_are_not_counted_as_closed():
    rep = collect_realized_fills([{"event_type": "position_managed", "outcome": {}}, _packet()])
    assert rep.total_rows == 2 and rep.closed_rows == 1 and len(rep.fills) == 1


# --------------------------------------------------------------------- evidence assembly

def test_silent_sleeves_are_emitted_explicitly_with_live_n_zero():
    """'No evidence' must be visible in the output, not an absence a reader has to notice."""
    cal = {"accounts": {"FTMO": {
        "crypto": {"calibrated": True, "survivor_tier": "UNCONDITIONAL",
                   "thresholds_down_r": {"1": -9.0}, "thresholds_kill_r": {"1": -19.0}},
        "energy_agri": {"calibrated": True, "survivor_tier": "UNCONDITIONAL",
                        "thresholds_down_r": {}, "thresholds_kill_r": {}},
    }}}
    ev = build_sleeve_evidence([], account="FTMO", calibration=cal)
    assert set(ev) == {"crypto", "energy_agri"}
    assert all(e.live_n == 0 and e.live_meanR is None for e in ev.values())


def test_thresholds_are_selected_at_the_observed_n():
    cal = {"accounts": {"FTMO": {"crypto": {
        "calibrated": True, "survivor_tier": "UNCONDITIONAL",
        "thresholds_down_r": {"1": -1.0, "2": -2.0}, "thresholds_kill_r": {"1": -5.0, "2": -6.0},
    }}}}
    ev = build_sleeve_evidence([price_closed_position(_packet())[0]] * 2,
                               account="FTMO", calibration=cal)
    assert ev["crypto"].live_n == 2
    assert ev["crypto"].live_gate_threshold_r == -2.0
    assert ev["crypto"].live_kill_threshold_r == -6.0


def test_uncalibrated_sleeve_gets_no_thresholds_rather_than_a_guess():
    cal = {"accounts": {"FTMO": {"crypto": {"calibrated": False, "reason": "no stream"}}}}
    ev = build_sleeve_evidence([price_closed_position(_packet())[0]],
                               account="FTMO", calibration=cal)
    assert ev["crypto"].live_gate_threshold_r is None
    assert ev["crypto"].live_kill_threshold_r is None


def test_fills_are_partitioned_by_account():
    fn = price_closed_position(_packet(namespace="redacted_account_live_bee34003"))[0]
    ftmo = price_closed_position(_packet())[0]
    cal = {"accounts": {"FTMO": {}, "redacted_account": {}}}
    assert build_sleeve_evidence([fn, ftmo], account="FTMO", calibration=cal)["crypto"].live_n == 1
    assert build_sleeve_evidence([fn, ftmo], account="redacted_account", calibration=cal)["crypto"].live_n == 1


# --------------------------------------------------------------------- the survivor tier mapping

@pytest.mark.parametrize("tier,expected", [
    ("UNCONDITIONAL", True),
    ("MEASURED_LIVE_CARRY", True),
    ("CARRY_CONDITIONAL_LIVE_SUPPORTED", True),
    ("CARRY_CONDITIONAL", False),
    ("DEAD_BEFORE_COST", False),
    (None, None),
])
def test_survivor_tier_mapping(tier, expected):
    """CARRY_CONDITIONAL is not a survivor: it turns on a holding time no cache records."""
    assert _survives(tier) is expected


@pytest.mark.skipif(not CALIBRATION.is_file(), reason="calibration artifact not built")
def test_every_tier_in_the_shipped_calibration_is_a_known_tier():
    doc = json.loads(CALIBRATION.read_text())
    for sleeves in doc["accounts"].values():
        for name, cal in sleeves.items():
            if not cal.get("calibrated"):
                continue
            assert _survives(cal["survivor_tier"]) is not None, (
                f"{name}: unknown survivor tier {cal['survivor_tier']!r} would silently skip the veto"
            )
