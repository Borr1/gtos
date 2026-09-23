"""The identity tuple is the acceptance instrument. These tests try to fool it.

The failure this file exists to prevent is the one AX shipped into his own
comparator and caught by luck: an aggregate that silently skipped every row and
reported a clean zero on both sides. A comparator that can be fooled by absence
is worse than no comparator, because it produces a green receipt.
"""

from __future__ import annotations

import pytest

from src.research_infra.train_engine import identity


def _trade(**overrides: object) -> dict[str, object]:
    row = {
        "candidate_id": "broadorigin_a47895e43883d1a0c1059541",
        "decision_time_utc": "2026-01-02T07:15:00+00:00",
        "symbol": "XAUUSD",
        "direction": "SHORT",
        "entry_time_utc": "2026-01-02T07:15:00+00:00",
        "entry_price": 4377.82,
        "exit_time_utc": "2026-01-02T07:54:24.605000+00:00",
        "close_reason": "selected_policy_replay:stop_loss",
        "final_r": -1.0,
        "cost_r": 0.09544224,
        "net_r": -1.09544224,
        "risk_cash": 250.0,
        "approved_risk_pct": 0.25,
        "headline_result_exclusion_reason": "headline_result_eligible",
    }
    row.update(overrides)
    return row


def _economics(trades, orders=(), counts=None, pool=None) -> dict[str, object]:
    return {
        "trades": list(trades),
        "orders": list(orders),
        "counts": counts or {"trade": len(list(trades)), "order": 0, "scorecard": 0, "missed": 0},
        "missed_digest": pool or {},
    }


# --------------------------------------------------------------------------
# absence must be loud
# --------------------------------------------------------------------------


def test_a_row_missing_an_identity_field_raises_rather_than_defaulting() -> None:
    row = _trade()
    del row["net_r"]
    with pytest.raises(identity.IdentityExtractionError) as excinfo:
        identity.trade_tuples([row])
    assert "net_r" in str(excinfo.value)


def test_two_rows_missing_the_same_field_do_not_compare_equal_they_raise() -> None:
    """The AX failure mode: both sides absent, both default to None, verdict green."""

    row = _trade()
    del row["cost_r"]
    with pytest.raises(identity.IdentityExtractionError):
        identity.compare_economics(_economics([row]), _economics([dict(row)]))


def test_a_non_mapping_row_raises() -> None:
    with pytest.raises(identity.IdentityExtractionError):
        identity.trade_tuples(["not a row"])  # type: ignore[list-item]


def test_a_baseline_pool_that_scored_nothing_fails_acceptance() -> None:
    """8,807 rows and zero scoreable is the silent-skip signature, not a result."""

    pool = {"rows": 8807, "diagnostic_scoreable_rows": 0, "positive_net_r": 0.0}
    verdict = identity.compare_economics(
        _economics([_trade()], pool=pool), _economics([_trade()], pool=pool)
    )
    assert verdict["verdict"] == "OUTCOME_DIVERGED"
    assert "missed_opportunity_pool_baseline_scored_nothing" in verdict["failures"]


# --------------------------------------------------------------------------
# the gate itself
# --------------------------------------------------------------------------


def test_identical_runs_are_outcome_identical() -> None:
    pool = {"rows": 8807, "diagnostic_scoreable_rows": 1539, "positive_net_r": 335.8}
    verdict = identity.compare_economics(
        _economics([_trade()], pool=pool), _economics([_trade()], pool=pool)
    )
    assert verdict["verdict"] == "OUTCOME_IDENTICAL"
    assert verdict["failures"] == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("entry_price", 4377.83),
        ("net_r", -1.09544225),
        ("close_reason", "selected_policy_replay:time_stop"),
        ("risk_cash", 250.01),
        ("approved_risk_pct", 0.5),
        ("exit_time_utc", "2026-01-02T07:54:24.606000+00:00"),
        ("headline_result_exclusion_reason", "excluded_thin_sample"),
        ("direction", "LONG"),
    ],
)
def test_any_moved_identity_field_diverges(field: str, value: object) -> None:
    pool = {"rows": 1, "diagnostic_scoreable_rows": 1}
    verdict = identity.compare_economics(
        _economics([_trade()], pool=pool),
        _economics([_trade(**{field: value})], pool=pool),
    )
    assert verdict["verdict"] == "OUTCOME_DIVERGED"
    assert "trade_identity_set_differs" in verdict["failures"]
    assert field in verdict["trade_field_divergence"]["fields_moved"]


def test_zero_tolerance_means_the_last_float_bit_counts() -> None:
    pool = {"rows": 1, "diagnostic_scoreable_rows": 1}
    verdict = identity.compare_economics(
        _economics([_trade(entry_price=4377.82)], pool=pool),
        _economics([_trade(entry_price=4377.820000000001)], pool=pool),
    )
    assert verdict["verdict"] == "OUTCOME_DIVERGED"
    assert identity.FLOAT_TOLERANCE == 0.0


def test_duplicate_trades_are_a_multiset_not_a_set() -> None:
    """Two identical trades is a different arm from one. A set would hide it."""

    pool = {"rows": 1, "diagnostic_scoreable_rows": 1}
    verdict = identity.compare_economics(
        _economics([_trade()], pool=pool),
        _economics([_trade(), _trade()], pool=pool),
    )
    assert verdict["verdict"] == "OUTCOME_DIVERGED"
    assert verdict["trades"]["only_in_candidate_count"] == 1


def test_a_dropped_order_diverges_even_when_the_trade_set_is_unchanged() -> None:
    """An order that never filled leaves no trade. Orders are gated separately
    precisely so a cut that stopped placing one is still caught."""

    order = {
        "candidate_id": "c1",
        "decision_time_utc": "2026-01-02T07:15:00+00:00",
        "symbol": "EURUSD",
        "direction": "LONG",
        "risk_cash": 100.0,
        "approved_risk_pct": 0.1,
    }
    pool = {"rows": 1, "diagnostic_scoreable_rows": 1}
    verdict = identity.compare_economics(
        _economics([_trade()], orders=[order], pool=pool),
        _economics([_trade()], orders=[], pool=pool),
    )
    assert verdict["verdict"] == "OUTCOME_DIVERGED"
    assert "order_identity_set_differs" in verdict["failures"]


def test_row_counts_are_gated_so_a_suppressed_ledger_cannot_pass() -> None:
    pool = {"rows": 1, "diagnostic_scoreable_rows": 1}
    verdict = identity.compare_economics(
        _economics([_trade()], counts={"trade": 1, "missed": 8807}, pool=pool),
        _economics([_trade()], counts={"trade": 1, "missed": 0}, pool=pool),
    )
    assert verdict["verdict"] == "OUTCOME_DIVERGED"
    assert "ledger_row_counts_differ" in verdict["failures"]


def test_the_missed_opportunity_pool_is_gated_because_it_is_the_training_substrate() -> None:
    verdict = identity.compare_economics(
        _economics([_trade()], pool={"rows": 8807, "diagnostic_scoreable_rows": 1539, "positive_net_r": 335.8}),
        _economics([_trade()], pool={"rows": 8807, "diagnostic_scoreable_rows": 1539, "positive_net_r": 331.0}),
    )
    assert verdict["verdict"] == "OUTCOME_DIVERGED"
    assert "missed_opportunity_pool_differs" in verdict["failures"]


# --------------------------------------------------------------------------
# canonicalisation corners
# --------------------------------------------------------------------------


def test_bool_and_int_do_not_collide() -> None:
    """`True == 1` in Python. A tuple that folded them would compare equal."""

    assert identity._canonical(True) != identity._canonical(1)
    assert identity._canonical(False) != identity._canonical(0)


def test_nan_folds_so_two_nans_compare_equal() -> None:
    assert identity._canonical(float("nan")) == identity._canonical(float("nan"))


def test_the_tuple_version_is_recorded_in_every_verdict() -> None:
    verdict = identity.compare_economics(
        _economics([_trade()], pool={"rows": 1, "diagnostic_scoreable_rows": 1}),
        _economics([_trade()], pool={"rows": 1, "diagnostic_scoreable_rows": 1}),
    )
    assert verdict["tuple_version"] == identity.TUPLE_VERSION
    assert verdict["trade_identity_fields"] == list(identity.TRADE_IDENTITY_FIELDS)


def test_the_tuple_contains_the_fields_the_result_doc_claims() -> None:
    """A silent field removal would loosen every acceptance claim ever made
    against this version. Changing the tuple must mean bumping the version."""

    assert identity.TUPLE_VERSION == "gtos.train_engine.trade_identity.v1"
    assert identity.TRADE_IDENTITY_FIELDS == (
        "candidate_id",
        "decision_time_utc",
        "symbol",
        "direction",
        "entry_time_utc",
        "entry_price",
        "exit_time_utc",
        "close_reason",
        "final_r",
        "cost_r",
        "net_r",
        "risk_cash",
        "approved_risk_pct",
        "headline_result_exclusion_reason",
    )
