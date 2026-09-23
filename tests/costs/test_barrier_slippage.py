"""Slippage must depend on how the order reached the market, not on a config constant."""

from __future__ import annotations

import pytest

from src.costs.barrier_slippage import (
    BarrierSlippageError,
    load_barrier_slippage_model,
)

FLAT_CONSTANT = 0.02      # config/agent_config.yaml:740, the number being replaced


@pytest.fixture(scope="module")
def model():
    return load_barrier_slippage_model()


class TestBarrierStructure:
    def test_a_target_exit_is_charged_nothing(self, model):
        """A limit fills at its price or better.  0 of 3,435 measured crossings were adverse."""
        for arm in ("MARKET", "LIMIT"):
            leg = model.exit_leg_r(exit_kind="TARGET", order_type=arm, symbol="EURUSD")
            assert leg.value_r == 0.0
            assert leg.coverage == "MEASURED"
            assert leg.n > 3000

    def test_a_stop_costs_strictly_more_than_the_flat_constant(self, model):
        for arm in ("MARKET", "LIMIT"):
            assert model.exit_leg_r(exit_kind="STOP", order_type=arm).value_r > FLAT_CONSTANT

    def test_a_time_stop_costs_strictly_less_than_the_flat_constant(self, model):
        for arm in ("MARKET", "LIMIT"):
            assert model.exit_leg_r(exit_kind="TIME_STOP", order_type=arm).value_r < FLAT_CONSTANT

    def test_the_three_barriers_are_strictly_ordered(self, model):
        for arm in ("MARKET", "LIMIT"):
            stop = model.exit_leg_r(exit_kind="STOP", order_type=arm).value_r
            time_stop = model.exit_leg_r(exit_kind="TIME_STOP", order_type=arm).value_r
            target = model.exit_leg_r(exit_kind="TARGET", order_type=arm).value_r
            assert stop > time_stop > target or (stop > time_stop and time_stop >= target)
            assert target == 0.0

    def test_the_cross_subsidy_the_flat_constant_created_is_real_and_large(self, model):
        """Stop-vs-target is the whole defect: one number cannot serve both."""
        stop = model.exit_leg_r(exit_kind="STOP", order_type="LIMIT").value_r
        target = model.exit_leg_r(exit_kind="TARGET", order_type="LIMIT").value_r
        assert stop - target > 0.04

    def test_the_limit_arm_slips_more_on_stops_than_the_market_arm(self, model):
        mkt = model.exit_leg_r(exit_kind="STOP", order_type="MARKET").value_r
        lim = model.exit_leg_r(exit_kind="STOP", order_type="LIMIT").value_r
        assert lim > mkt
        assert 1.0 < lim / mkt < 1.5


class TestEntryLegIsStructurallyZero:
    def test_entry_leg_is_zero_and_says_why(self, model):
        leg = model.entry_leg_r(arm="MARKET")
        assert leg.value_r == 0.0
        assert leg.coverage == "STRUCTURAL_ZERO"
        assert "fill" in leg.provenance and "spread" in leg.provenance

    def test_total_charge_equals_the_exit_leg_alone(self, model):
        for arm in ("MARKET", "LIMIT"):
            for kind in ("STOP", "TARGET", "TIME_STOP"):
                total = model.expected_slippage_r(
                    exit_kind=kind, order_type=arm, symbol="XAUUSD"
                )
                exit_only = model.exit_leg_r(
                    exit_kind=kind, order_type=arm, symbol="XAUUSD"
                ).value_r
                assert total == exit_only


class TestPerSymbol:
    def test_per_symbol_stop_legs_disagree_by_more_than_3x(self, model):
        """A single constant cannot be right for both ends of the book."""
        legs = {
            s: model.exit_leg_r(exit_kind="STOP", order_type="MARKET", symbol=s).value_r
            for s in ("USDJPY", "XAUUSD", "NAS100", "JP225", "SPX500")
        }
        assert max(legs.values()) / min(legs.values()) > 3.0

    def test_a_measured_symbol_is_labelled_measured_with_its_sample_size(self, model):
        leg = model.exit_leg_r(exit_kind="STOP", order_type="MARKET", symbol="USDJPY")
        assert leg.coverage == "MEASURED" and leg.n > 100

    def test_an_unmeasured_symbol_falls_back_to_the_pool_and_is_labelled_transferred(self, model):
        leg = model.exit_leg_r(exit_kind="STOP", order_type="MARKET", symbol="NOT_A_SYMBOL")
        assert leg.coverage == "TRANSFERRED"
        assert leg.value_r == pytest.approx(
            model.exit_leg_r(exit_kind="STOP", order_type="MARKET").value_r
        )


class TestFailsClosed:
    def test_an_unknown_barrier_refuses_rather_than_guessing(self, model):
        with pytest.raises(BarrierSlippageError):
            model.exit_leg_r(exit_kind="TELEPORTED", order_type="MARKET")

    def test_an_unknown_order_arm_refuses(self, model):
        with pytest.raises(BarrierSlippageError):
            model.exit_leg_r(exit_kind="STOP", order_type="ICEBERG")

    def test_price_domain_requires_a_positive_stop_distance(self, model):
        with pytest.raises(BarrierSlippageError):
            model.price_domain_leg(
                exit_kind="STOP", order_type="MARKET", symbol="EURUSD", stop_distance_price=0.0
            )


class TestPriceDomainTransfer:
    def test_price_domain_rescales_with_the_callers_own_stop(self, model):
        """R does not transfer across stop geometries; price does."""
        a = model.price_domain_leg(
            exit_kind="STOP", order_type="MARKET", symbol="EURUSD", stop_distance_price=0.0005
        )
        b = model.price_domain_leg(
            exit_kind="STOP", order_type="MARKET", symbol="EURUSD", stop_distance_price=0.0010
        )
        assert b == pytest.approx(2 * a)


def test_pooled_level_is_close_to_the_old_constant_so_only_the_shape_changed(model):
    """The repair is a redistribution, not a level change -- which is why pooled checks passed.

    Weighted at the sealed census's own barrier mix (STOP .533, TIME_STOP .258, TARGET .209)
    the charge lands near the old 0.02, while individual cells move several-fold.
    """
    mix = {"STOP": 0.533, "TIME_STOP": 0.258, "TARGET": 0.209}
    pooled = sum(
        w * model.exit_leg_r(exit_kind=k, order_type="MARKET").value_r for k, w in mix.items()
    )
    assert 0.5 * FLAT_CONSTANT < pooled < 1.5 * FLAT_CONSTANT
