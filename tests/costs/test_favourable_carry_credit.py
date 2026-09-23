"""B9 -- the favourable-carry clamp: default bit-identity, and the credit when asked for.

`broker_net_cost_engine.py:465-468` and `costs/model.py:1033` book a swap the broker PAYS as a
cost of exactly 0.00. Both now MEASURE the discarded credit and neither changes any decision
unless explicitly told to.

Every assertion here is behavioural -- it calls the engine and reads the numbers it returns. No
test greps the source, because a source-string test passes against a wrong implementation
(CLAUDE.md 6).

The instrument in the fixtures is FTMO `USOIL_cash` as the 2026-06-01 profile records it
(`swap_long: +36.56`, `swap_mode: 1`, `point: 0.001`) -- the ARMED `energy_agri` sleeve's own
symbol, chosen so a regression here fails on the trade that motivated the change.
"""
from __future__ import annotations

import pytest

from src.components.broker_net_cost_engine import (
    LEGACY_ZERO_COMMISSION_COMPARATOR_MODE,
    _swap_cost_packet,
    build_pretrade_cost_packet,
    pretrade_cost_refusal_reasons,
)
from src.costs.model import CostTruthError, swap_price_drag_per_night

# ------------------------------------------------------------------ fixtures

USOIL_SPEC = {"fields": {"swap_mode": 1.0, "point": 0.001, "swap_rollover3days": 3}}
SERVER = "FTMO-Server3"
ENTRY = "2026-07-01T10:00:00+00:00"          # Wednesday; one broker midnight inside 24 h
SL = 0.938                                    # a real energy_agri stop distance, price units
SWAP_LONG_USOIL_20260601 = 36.56
SWAP_LONG_USOIL_20260725 = 4.06
SWAP_SHORT_USOIL_20260601 = -168.09


def _packet(swap, *, credit_authority=None, sl=SL, spec=None, server=SERVER, entry=ENTRY):
    cfg = {"selected_cell_swap_cost_default_hold_days": 1.0}
    if credit_authority is not None:
        cfg["selected_cell_swap_credit_favourable_carry"] = credit_authority
    return _swap_cost_packet(
        runtime_cfg=cfg,
        trade_params={},
        spec=spec or USOIL_SPEC,
        swap_value=swap,
        entry_price=76.0,
        sl_distance=sl,
        entry_utc=entry,
        server=server,
    )


# ------------------------------------------------------------------ default bit-identity


def test_default_favourable_swap_still_costs_exactly_zero():
    """The clamp is unchanged by default. This is the regression guard for armed money."""
    p = _packet(SWAP_LONG_USOIL_20260601)
    assert p["cost_r"] == 0.0
    assert p["daily_cost_r"] == 0.0
    assert p["adverse_swap_points"] == 0.0
    assert p["source_status"] == "captured"
    assert p["favorable_swap_credit_applied"] is False
    assert p["carry_credit_authority"] is False


def test_default_adverse_swap_is_untouched():
    p = _packet(SWAP_SHORT_USOIL_20260601)
    # 168.09 points * 0.001 / 0.938 per night, over the charged nights
    assert p["cost_r"] > 0
    assert p["adverse_swap_points"] == pytest.approx(168.09)
    assert p["daily_price_drag"] == pytest.approx(168.09 * 0.001)
    assert p["credit_r_foregone"] is None
    assert p["credit_source_status"] == "not_applicable_adverse_or_absent_swap"


def test_explicit_false_is_the_same_as_absent():
    absent = _packet(SWAP_LONG_USOIL_20260601)
    explicit = _packet(SWAP_LONG_USOIL_20260601, credit_authority=False)
    for key in ("cost_r", "daily_cost_r", "daily_price_drag", "adverse_swap_points", "source_status"):
        assert absent[key] == explicit[key], key


# ------------------------------------------------------------------ the credit is measured anyway


def test_credit_is_measured_even_with_no_authority():
    p = _packet(SWAP_LONG_USOIL_20260601)
    nights = p["swap_charge_units"]
    assert nights and nights > 0
    expected = -SWAP_LONG_USOIL_20260601 * 0.001 / SL * nights
    assert p["cost_r_carry_credited"] == pytest.approx(expected)
    assert p["cost_r_carry_credited"] < 0                      # negative = the broker pays
    assert p["credit_r_foregone"] == pytest.approx(-expected)  # what the clamp discards
    assert p["credit_source_status"] == "captured"
    assert p["cost_r"] == 0.0                                  # ...and the decision is unchanged


def test_credit_shrinks_with_the_broker_table():
    """The 2026-06-01 and 2026-07-25 FTMO reads disagree 9x on this symbol; the engine follows."""
    old = _packet(SWAP_LONG_USOIL_20260601)["credit_r_foregone"]
    new = _packet(SWAP_LONG_USOIL_20260725)["credit_r_foregone"]
    assert old > new > 0
    assert old / new == pytest.approx(SWAP_LONG_USOIL_20260601 / SWAP_LONG_USOIL_20260725, rel=1e-9)


def test_credit_scales_inversely_with_the_stop():
    wide = _packet(SWAP_LONG_USOIL_20260601, sl=2 * SL)["credit_r_foregone"]
    tight = _packet(SWAP_LONG_USOIL_20260601, sl=SL)["credit_r_foregone"]
    assert tight == pytest.approx(2 * wide)


# ------------------------------------------------------------------ authority on


def test_authority_moves_the_credit_into_cost_r():
    on = _packet(SWAP_LONG_USOIL_20260601, credit_authority=True)
    off = _packet(SWAP_LONG_USOIL_20260601, credit_authority=False)
    assert on["cost_r"] < 0
    assert on["cost_r"] == pytest.approx(off["cost_r_carry_credited"])
    assert on["favorable_swap_credit_applied"] is True
    assert on["daily_price_drag"] == pytest.approx(-SWAP_LONG_USOIL_20260601 * 0.001)


def test_authority_does_not_touch_the_adverse_side():
    on = _packet(SWAP_SHORT_USOIL_20260601, credit_authority=True)
    off = _packet(SWAP_SHORT_USOIL_20260601, credit_authority=False)
    assert on["cost_r"] == off["cost_r"] > 0
    assert on["favorable_swap_credit_applied"] is False


# ------------------------------------------------------------------ the favourable-side source gap


def test_favourable_side_source_gap_is_now_visible_and_still_costs_zero():
    """Before B9 the favourable branch skipped every validation and reported `captured`.

    It still returns 0.0 -- unchanged -- but a missing `point` no longer hides behind that zero.
    """
    p = _packet(SWAP_LONG_USOIL_20260601, spec={"fields": {"swap_mode": 1.0, "swap_rollover3days": 3}})
    assert p["cost_r"] == 0.0
    assert p["source_status"] == "captured"          # unchanged
    assert p["credit_source_status"] == "source_gap"  # ...and now inspectable
    assert "point" in p["credit_missing_fields"]
    assert p["cost_r_carry_credited"] is None


def test_unresolvable_broker_clock_is_a_credit_source_gap_not_a_crash():
    p = _packet(SWAP_LONG_USOIL_20260601, server="NOT-A-REGISTERED-SERVER")
    assert p["cost_r"] == 0.0
    assert p["credit_source_status"] == "source_gap"
    assert "swap_charge_units" in p["credit_missing_fields"]


def test_swap_mode_5_credit_uses_the_annual_interest_conversion():
    spec = {"fields": {"swap_mode": 5.0, "point": 0.01, "swap_rollover3days": 3}}
    p = _packet(2.4, spec=spec)
    nights = p["swap_charge_units"]
    assert p["cost_r_carry_credited"] == pytest.approx(-76.0 * (2.4 / 100.0) / 360.0 / SL * nights)


# ------------------------------------------------------------------ the live gate


def _live_cfg(**over):
    # `broker_profile.server` is what lets the swap term count real broker-wall midnights
    # (`_profile_packet:298-312` -> `rollover_nights`). Without it the swap packet degrades to
    # `source_gap_broker_server_missing` -- which is exactly what the live profiles supply, so
    # the fixture supplies it too.
    cfg = {
        "broker_profile": {"server": SERVER, "broker": "FTMO"},
        "runtime": {"profile_namespace": "operator_profile"},
        "gtos_vnext_runtime": {
            "enabled": True,
            "mode": "production_replacement_vnext_moonshot",
            "apply_to_execution": True,
            "selected_cell_pretrade_cost_model_required": True,
            "selected_cell_pretrade_max_total_cost_r": 0.15,
            "selected_cell_pretrade_max_spread_r": 0.10,
            "selected_cell_swap_cost_default_hold_days": 1.0,
            "selected_cell_default_expected_slippage_r": 0.02,
            "selected_cell_commission_model_required": False,
            **over,
        }
    }
    return cfg


class _Tick:
    bid = 75.90
    ask = 76.10
    time = 1782000000


def _live_packet(**over):
    return build_pretrade_cost_packet(
        config=_live_cfg(**over),
        trade_params={
            "gtos_vnext_production_execution_path": True,
            "direction": "BUY",
            "entry_price": 76.0,
            "stop_loss": 76.0 - SL,
        },
        tick=_Tick(),
        symbol="USOIL_cash",
        broker_symbol="USOIL.cash",
        entry_price=76.0,
        stop_loss=76.0 - SL,
        sl_distance=SL,
        risk_pct=0.5,
        symbol_info={
            "swap_mode": 1,
            "swap_long": SWAP_LONG_USOIL_20260601,
            "swap_short": SWAP_SHORT_USOIL_20260601,
            "point": 0.001,
            "swap_rollover3days": 3,
            "trade_mode": 4,
        },
        asof_utc=ENTRY,
        commission_mode=LEGACY_ZERO_COMMISSION_COMPARATOR_MODE,
    )


def test_live_packet_reports_the_credited_total_without_gating_on_it():
    p = _live_packet()
    assert p["total_cost_r"] is not None
    assert p["total_cost_r_carry_credited"] is not None
    assert p["total_cost_r_carry_credited"] < p["total_cost_r"]
    assert p["carry_credit_r_foregone"] > 0
    assert p["carry_credit_authority"] is False
    # the number the gate reads is still the clamped one
    assert p["total_cost_components"]["swap_cost_r"] == 0.0


def test_live_refusal_is_computed_from_the_clamped_total_by_default():
    """A candidate whose clamped cost is over the ceiling is refused even when its true
    all-in cost, credit included, is under it. That is the conservative half of the defect."""
    p = _live_packet(selected_cell_pretrade_max_total_cost_r=0.0)
    reasons = pretrade_cost_refusal_reasons(p)
    assert any(r.startswith("total_cost_r_exceeds_limit") for r in reasons)
    assert p["status"] == "REFUSED"


def test_live_authority_lowers_the_gated_total():
    off = _live_packet()
    on = _live_packet(selected_cell_swap_credit_favourable_carry=True)
    assert on["total_cost_r"] < off["total_cost_r"]
    assert on["total_cost_r"] == pytest.approx(off["total_cost_r_carry_credited"])
    assert on["swap_cost"]["favorable_swap_credit_applied"] is True


# ------------------------------------------------------------------ costs/model.py


def _rec(swap_long, swap_short=-168.09, mode=1, point=0.001):
    return {
        "spec": {"swap_long": swap_long, "swap_short": swap_short, "swap_mode": mode,
                 "point": point, "swap_rollover3days": 3},
        "spread_price": {"mid_price_median": 76.0},
        "swap": {"coverage": "MEASURED"},
    }


def test_model_default_returns_zero_for_favourable_and_reports_the_credit():
    drag, detail = swap_price_drag_per_night(_rec(SWAP_LONG_USOIL_20260601), "LONG", 76.0)
    assert drag == 0.0
    assert detail["credit_price_per_night"] == pytest.approx(SWAP_LONG_USOIL_20260601 * 0.001)


def test_model_credit_opt_in_returns_the_signed_value():
    drag, _ = swap_price_drag_per_night(
        _rec(SWAP_LONG_USOIL_20260601), "LONG", 76.0, credit_favourable=True
    )
    assert drag == pytest.approx(-SWAP_LONG_USOIL_20260601 * 0.001)


def test_model_adverse_side_unchanged_and_credit_zero():
    drag, detail = swap_price_drag_per_night(_rec(SWAP_LONG_USOIL_20260601), "SHORT", 76.0)
    assert drag == pytest.approx(168.09 * 0.001)
    assert detail["credit_price_per_night"] == 0.0


def test_model_favourable_with_missing_point_does_not_raise_by_default():
    rec = _rec(SWAP_LONG_USOIL_20260601, point=None)
    drag, detail = swap_price_drag_per_night(rec, "LONG", 76.0)
    assert drag == 0.0
    assert detail["credit_price_per_night"] is None
    assert "credit_source_gap" in detail
    with pytest.raises(CostTruthError):
        swap_price_drag_per_night(rec, "LONG", 76.0, credit_favourable=True)


def test_model_adverse_with_missing_point_still_raises():
    with pytest.raises(CostTruthError):
        swap_price_drag_per_night(_rec(SWAP_LONG_USOIL_20260601, point=None), "SHORT", 76.0)
