"""Behavioural tests for the broker-truth cost layer (`src.costs`).

These assert what the layer *does*, not what its source says. The most important of them
is `test_reproduces_realized_commission_on_every_w7_fill`, which prices all 175 live W7
fills from symbol + account + stop distance alone and checks the result against what the
broker actually charged.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.costs import (
    BrokerTrueCosts,
    account_for,
    commission_usd_per_lot_for_packet,
    Coverage,
    CostTruthError,
    Measure,
    commission_usd_per_lot,
    component_sum_r,
    cost_r,
    legacy_class_cost_r,
    load_broker_true_costs,
    rollover_nights,
    weakest,
)

REPO = Path(__file__).resolve().parents[1]
W7_ROWS = REPO / "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl"


@pytest.fixture(scope="module")
def truth() -> BrokerTrueCosts:
    return load_broker_true_costs()


# ---------------------------------------------------------------- coverage discipline


def test_measure_refuses_to_exist_without_provenance():
    with pytest.raises(ValueError, match="provenance is required"):
        Measure(value=0.1, coverage=Coverage.MEASURED, provenance="")


def test_measure_refuses_a_non_coverage_class():
    with pytest.raises(TypeError, match="coverage must be a Coverage"):
        Measure(value=0.1, coverage="MEASURED", provenance="x")  # type: ignore[arg-type]


def test_transferred_must_name_its_source():
    with pytest.raises(ValueError, match="transferred_from"):
        Measure(value=0.1, coverage=Coverage.TRANSFERRED, provenance="x")


def test_modelled_must_carry_owner_and_date():
    with pytest.raises(ValueError, match="owner and asof"):
        Measure(value=0.1, coverage=Coverage.MODELLED, provenance="x")


def test_measured_band_is_degenerate_and_non_measured_is_half_to_double():
    m = Measure(value=0.2, coverage=Coverage.MEASURED, provenance="deals")
    assert (m.band_low, m.band_high) == (0.2, 0.2)
    t = Measure(
        value=0.2, coverage=Coverage.TRANSFERRED, provenance="p", transferred_from="XAUUSD"
    )
    assert t.band_low == pytest.approx(0.1)
    assert t.band_high == pytest.approx(0.4)


def test_narrowing_the_band_requires_the_measurement_that_justifies_it():
    with pytest.raises(ValueError, match="band_provenance"):
        Measure(
            value=0.2,
            coverage=Coverage.TRANSFERRED,
            provenance="p",
            transferred_from="XAUUSD",
            band_mult=(0.95, 1.05),
        )
    ok = Measure(
        value=0.2,
        coverage=Coverage.TRANSFERRED,
        provenance="p",
        transferred_from="XAUUSD",
        band_mult=(0.95, 1.05),
        band_provenance="measured class disagreement 0.52%",
    )
    assert ok.band_low == pytest.approx(0.19)


def test_coverage_only_ever_degrades():
    m = Measure(value=1.0, coverage=Coverage.TRANSFERRED, provenance="p", transferred_from="x")
    with pytest.raises(ValueError, match="refusing to strengthen"):
        m.downgraded_to(Coverage.MEASURED, provenance="p")
    weaker = m.downgraded_to(Coverage.MODELLED, provenance="p", owner="o", asof="2026-07-27")
    assert weaker.coverage is Coverage.MODELLED


def test_weakest_picks_the_weakest():
    assert weakest(Coverage.MEASURED, Coverage.MODELLED) is Coverage.MODELLED
    assert weakest(Coverage.MEASURED, Coverage.TRANSFERRED) is Coverage.TRANSFERRED
    assert weakest(Coverage.MEASURED) is Coverage.MEASURED


# ---------------------------------------------------------------- refusals, not zeros


def test_missing_stop_distance_is_refused_rather_than_defaulted(truth):
    with pytest.raises(CostTruthError, match="sl_distance_price must be > 0"):
        cost_r("USDJPY", "FTMO", 1.0, sl_distance_price=0.0, costs=truth)


def test_unknown_symbol_is_unpriced_not_free(truth):
    with pytest.raises(CostTruthError, match="unpriced, not free"):
        cost_r("NOT_A_SYMBOL", "FTMO", 1.0, sl_distance_price=0.01, costs=truth)


def test_unknown_account_is_refused(truth):
    with pytest.raises(CostTruthError, match="no broker truth for account"):
        cost_r("USDJPY", "SomeOtherProp", 1.0, sl_distance_price=0.01, costs=truth)


def test_unknown_commission_schedule_raises_instead_of_charging_zero(truth):
    """The F38 defect in one assertion: an unmeasured commission must never read as 0.0."""
    rec = {
        "commission": {"kind": "unknown", "value": None, "coverage": "MODELLED"},
        "spec": {},
    }
    with pytest.raises(CostTruthError, match="UNKNOWN, not zero"):
        commission_usd_per_lot(rec, entry_price=100.0)


def test_a_measured_zero_is_distinguishable_from_an_unmeasured_one(truth):
    """Index CFDs pay exactly zero -- and the layer says so as a MEASURED zero."""
    b = cost_r("US500.cash", "FTMO", 1.0, sl_distance_price=50.0, costs=truth)
    assert b.commission_r.value == 0.0
    assert b.commission_r.coverage is Coverage.MEASURED
    assert b.commission_r.n and b.commission_r.n > 0


# ---------------------------------------------------------------- the central property


def test_commission_in_r_is_a_function_of_the_stop_not_the_instrument(truth):
    """Halving the stop doubles commission in R. This is why the receipt's per-symbol R
    table is not a rate table."""
    at = datetime(2026, 6, 20, 12, tzinfo=timezone.utc)
    wide = cost_r("USDJPY", "FTMO", 1.0, sl_distance_price=0.20,
                  entry_utc=at, costs=truth)
    tight = cost_r("USDJPY", "FTMO", 1.0, sl_distance_price=0.10,
                   entry_utc=at, costs=truth)
    assert tight.commission_r.value == pytest.approx(2 * wide.commission_r.value, rel=1e-9)


def test_usdjpy_and_gbpjpy_pay_the_identical_per_lot_rate(truth):
    """Their 2.1x gap in GATE_G1B_RECEIPT.md 5.2a is stop distance, not a rate difference."""
    for account in ("FTMO", "redacted_account"):
        usd = commission_usd_per_lot(truth.instrument(account, "USDJPY"), None)[0]
        gbp = commission_usd_per_lot(truth.instrument(account, "GBPJPY"), None)[0]
        assert usd == pytest.approx(gbp, rel=1e-6)
        assert usd == pytest.approx(5.0, abs=0.02)


def test_total_coverage_is_the_weakest_component(truth):
    b = cost_r("USDJPY", "FTMO", 1.0, sl_distance_price=0.05,
               entry_utc=datetime(2026, 6, 20, 12, tzinfo=timezone.utc), costs=truth)
    worst = max(
        (b.commission_r, b.swap_r, b.spread_r, b.slippage_r), key=lambda m: m.coverage.strength
    )
    assert b.total_r.coverage is worst.coverage


def test_total_is_the_sum_of_its_parts(truth):
    b = cost_r("XAUUSD", "redacted_account", 3.0, sl_distance_price=12.0, entry_price=4100.0, costs=truth)
    assert b.total_r.value == component_sum_r(
        b.spread_r.value, b.slippage_r.value, b.swap_r.value, b.commission_r.value
    )


# ---------------------------------------------------------------- swap is rollover-based


def test_swap_is_charged_per_rollover_not_per_hour():
    """Measured in the live rows: swap present on a 2.2 h hold, absent on a 24.3 h hold."""
    # 2.2 h that crosses broker midnight (broker wall = UTC+3, so 21:00 UTC).
    crossing, _ = rollover_nights(
        datetime(2026, 6, 23, 20, 0, tzinfo=timezone.utc),
        2.2,
        server="FTMO-Server3",
        rollover3days_weekday=3,
    )
    # 24.3 h that starts just after a rollover... still crosses one. Use a hold that
    # stays inside one broker day instead: 23 h from 22:00 UTC ends 21:00 UTC next day.
    inside, _ = rollover_nights(
        datetime(2026, 6, 23, 22, 0, tzinfo=timezone.utc),
        22.0,
        server="FTMO-Server3",
        rollover3days_weekday=3,
    )
    assert crossing >= 1.0
    assert inside == 0.0


def test_triple_swap_weekday_counts_three():
    # 2026-06-24 is a Wednesday; MT5 weekday 3 == Wednesday.
    wed, detail = rollover_nights(
        datetime(2026, 6, 23, 20, 0, tzinfo=timezone.utc),
        6.0,
        server="FTMO-Server3",
        rollover3days_weekday=3,
    )
    assert wed == pytest.approx(3.0)
    assert any("2026-06-24" in c for c in detail["crossings"])
    plain, _ = rollover_nights(
        datetime(2026, 6, 23, 20, 0, tzinfo=timezone.utc),
        6.0,
        server="FTMO-Server3",
        rollover3days_weekday=5,
    )
    assert plain == pytest.approx(1.0)


def test_weekend_midnights_are_not_charged_separately():
    """Fri 2026-06-26 23:00 broker -> Sun 15:00 broker crosses Sat and Sun midnights only;
    the weekend is collected on the triple-swap weekday, not charged night by night."""
    nights, detail = rollover_nights(
        datetime(2026, 6, 26, 20, 0, tzinfo=timezone.utc),  # Friday
        40.0,
        server="FTMO-Server3",
        rollover3days_weekday=3,
    )
    assert nights == 0.0
    assert detail["crossings"] == []
    # Extending into Monday does start charging again.
    into_monday, mdetail = rollover_nights(
        datetime(2026, 6, 26, 20, 0, tzinfo=timezone.utc),
        50.0,
        server="FTMO-Server3",
        rollover3days_weekday=3,
    )
    assert into_monday == pytest.approx(1.0)
    assert any("2026-06-29" in c for c in mdetail["crossings"])


def test_swap_degrades_to_modelled_without_an_entry_instant(truth):
    exact = cost_r(
        "XAUUSD",
        "redacted_account",
        30.0,
        sl_distance_price=12.0,
        entry_price=4100.0,
        entry_utc=datetime(2026, 6, 23, 10, 0, tzinfo=timezone.utc),
        costs=truth,
    )
    approx = cost_r(
        "XAUUSD", "redacted_account", 30.0, sl_distance_price=12.0, entry_price=4100.0, costs=truth
    )
    assert exact.swap_r.coverage is Coverage.MEASURED
    assert approx.swap_r.coverage is Coverage.MODELLED
    assert approx.swap_r.band_high > approx.swap_r.band_low


# ---------------------------------------------------------------- spread


def test_p95_spread_costs_more_than_p50(truth):
    p50 = cost_r("XAUUSD", "redacted_account", 1.0, sl_distance_price=12.0, costs=truth)
    p95 = cost_r(
        "XAUUSD", "redacted_account", 1.0, sl_distance_price=12.0, spread_percentile="p95", costs=truth
    )
    assert p95.spread_r.value > p50.spread_r.value


def test_unmeasured_percentile_is_refused(truth):
    with pytest.raises(CostTruthError, match="not measured"):
        cost_r(
            "XAUUSD", "redacted_account", 1.0, sl_distance_price=12.0, spread_percentile="p42", costs=truth
        )


# ---------------------------------------------------------------- F39 comparator


def test_legacy_class_cost_is_modelled_and_banded(truth):
    m = legacy_class_cost_r("USDJPY", "FTMO", costs=truth)
    assert m.coverage is Coverage.MODELLED
    assert m.band_low < m.value < m.band_high
    assert "no generator" in (m.owner or "")


# ---------------------------------------------------------------- broker-truth proof


@pytest.mark.skipif(not W7_ROWS.is_file(), reason="W7 forensics rows not present")
def test_reproduces_realized_commission_on_every_w7_fill(truth):
    """Price 175 live fills from (symbol, account, stop) alone; compare to what the broker
    charged. `cost_r` never sees the realized commission."""
    rows = [json.loads(x) for x in W7_ROWS.read_text("utf-8-sig").splitlines() if x.strip()]
    rows = [r for r in rows if r.get("stack_era") == "w7_book"]
    assert len(rows) == 175, f"expected the 175-fill W7 book, got {len(rows)}"

    account_key = {"ftmo": "FTMO", "redacted_account": "redacted_account"}
    # This test isolates the commission model. Some fills predate an exact-symbol
    # slippage sample; an explicit test double prevents that independent NOT_EVALUABLE
    # term from hiding whether the commission arithmetic reproduces broker history.
    from src.costs.slippage_model import SlippageEstimate
    from src.costs.symbols import canonical_symbol

    class CommissionIsolationSlippage:
        def estimate(self, account, symbol):
            return SlippageEstimate(
                account=account,
                canonical_symbol=canonical_symbol(symbol) or symbol,
                expected_adverse_price=0.0,
                coverage=Coverage.MEASURED,
                n=1,
                provenance="commission isolation test double",
                detail={},
            )

    errors, actuals = [], []
    for r in rows:
        acct = account_key[r["account"]]
        b = cost_r(
            r["broker_symbol"],
            acct,
            holding_hours=float(r.get("holding_seconds") or 0) / 3600.0,
            sl_distance_price=float(r["risk_distance_price"]),
            entry_price=r.get("entry_price"),
            side="SHORT" if str(r.get("side", "")).lower() == "short" else "LONG",
            entry_utc=datetime.fromisoformat(r["entry_time_utc"]),
            slippage_model=CommissionIsolationSlippage(),
            costs=truth,
        )
        actual = -float(r["commission"]) / float(r["risk_at_entry_usd"])
        actuals.append(actual)
        errors.append(abs(b.commission_r.value - actual))

    mean_abs_err = sum(errors) / len(errors)
    pooled_actual = sum(actuals) / len(actuals)
    # Broker truth: pooled commission 0.0591 R/fill (GATE_G1B_RECEIPT.md:759).
    assert pooled_actual == pytest.approx(0.0591, abs=0.001)
    assert mean_abs_err < 0.002, f"mean abs error {mean_abs_err:.6f} R"
    assert max(errors) < 0.01
    # The null control: the shipped model charges zero, so its error IS the cost.
    null_err = sum(abs(a) for a in actuals) / len(actuals)
    assert null_err > 50 * mean_abs_err


# ---------------------------------------------------------------- engine adapter (OD-J1)


def test_account_resolution_fails_closed_on_an_unknown_server():
    assert account_for(server="FTMO-Server3") == "FTMO"
    assert account_for(server="redacted_account-Server 2") == "redacted_account"
    assert account_for(namespace="operator_profile") == "FTMO"
    with pytest.raises(CostTruthError, match="do not fall back"):
        account_for(server="SomeOtherBroker-Live")


def test_adapter_returns_none_rather_than_zero_when_it_cannot_price(truth):
    """None refuses the packet; 0.0 would silently re-create F38."""
    assert commission_usd_per_lot_for_packet(
        "USDJPY", server="FTMO-Server3", costs=truth
    ) == pytest.approx(5.0, abs=0.02)
    assert commission_usd_per_lot_for_packet("USDJPY", server="Nope-Server", costs=truth) is None
    assert commission_usd_per_lot_for_packet(
        "NOT_A_SYMBOL", server="FTMO-Server3", costs=truth
    ) is None


def test_adapter_gives_the_two_accounts_different_crypto_prices(truth):
    ftmo = commission_usd_per_lot_for_packet(
        "BTCUSD", server="FTMO-Server3", entry_price=63000.0, costs=truth
    )
    fn = commission_usd_per_lot_for_packet(
        "BTCUSD", server="redacted_account-Server 2", entry_price=63000.0, costs=truth
    )
    assert ftmo > fn > 0  # FTMO 6.495 bp vs redacted_account 4.000 bp of notional
