# GTOS research infrastructure (Phase 1)
"""Tests for ``src.research_infra.model_router``.

Coverage matrix
---------------
* Default table routes every TaskType correctly
* ``trading_decision`` always lands on Sonnet 4.6 effort=max
* Override of ``trading_decision`` raises RouterMisconfigurationError
* Custom routing tables that swap *only* non-trading entries are accepted
* Dry-run mode returns the intended routing AND logs a [DRY-RUN] warning
* Unknown TaskType raises UnknownTaskTypeError (no silent default)
* Empty / None routing_table falls back to the default table

The router never makes API calls; these tests therefore stay fully
offline + deterministic.
"""

from __future__ import annotations

import logging
from typing import Mapping

import pytest

from src.research_infra.model_router import (
    DEFAULT_ROUTING_TABLE,
    MODEL_HAIKU_4_5,
    MODEL_SONNET_4_6,
    ModelRouter,
    RouterMisconfigurationError,
    RoutingDecision,
    TaskType,
    UnknownTaskTypeError,
    VALID_TASK_TYPES,
)


# ---------------------------------------------------------------------------
# Default table behaviour
# ---------------------------------------------------------------------------


class TestDefaultTable:
    def test_default_table_covers_all_task_types(self) -> None:
        """DEFAULT_ROUTING_TABLE must have one entry per VALID_TASK_TYPES."""
        assert set(DEFAULT_ROUTING_TABLE.keys()) == set(VALID_TASK_TYPES)

    def test_trading_decision_routes_to_sonnet_max(self) -> None:
        router = ModelRouter()
        model, effort = router.route("trading_decision")
        assert model == MODEL_SONNET_4_6
        assert effort == "max"

    def test_regime_classification_routes_to_haiku_high(self) -> None:
        router = ModelRouter()
        model, effort = router.route("regime_classification")
        assert model == MODEL_HAIKU_4_5
        assert effort == "high"

    def test_metadata_extraction_routes_to_haiku_medium(self) -> None:
        router = ModelRouter()
        model, effort = router.route("metadata_extraction")
        assert model == MODEL_HAIKU_4_5
        assert effort == "medium"

    def test_decay_analysis_routes_to_haiku_high(self) -> None:
        router = ModelRouter()
        model, effort = router.route("decay_analysis")
        assert model == MODEL_HAIKU_4_5
        assert effort == "high"

    def test_summary_aggregation_routes_to_haiku_medium(self) -> None:
        router = ModelRouter()
        model, effort = router.route("summary_aggregation")
        assert model == MODEL_HAIKU_4_5
        assert effort == "medium"

    def test_other_falls_back_to_sonnet_high(self) -> None:
        """The conservative escape hatch — Sonnet 4.6 effort=high."""
        router = ModelRouter()
        model, effort = router.route("other")
        assert model == MODEL_SONNET_4_6
        assert effort == "high"

    @pytest.mark.parametrize("task_type", list(VALID_TASK_TYPES))
    def test_route_returns_tuple_of_strings(self, task_type: TaskType) -> None:
        router = ModelRouter()
        result = router.route(task_type)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(x, str) for x in result)


# ---------------------------------------------------------------------------
# Trading-decision immutability
# ---------------------------------------------------------------------------


class TestTradingDecisionImmutable:
    def test_override_to_haiku_rejected(self) -> None:
        bad_table = dict(DEFAULT_ROUTING_TABLE)
        bad_table["trading_decision"] = RoutingDecision(
            MODEL_HAIKU_4_5, "max"
        )
        with pytest.raises(RouterMisconfigurationError, match="IMMUTABLE"):
            ModelRouter(routing_table=bad_table)

    def test_override_to_lower_effort_rejected(self) -> None:
        bad_table = dict(DEFAULT_ROUTING_TABLE)
        bad_table["trading_decision"] = RoutingDecision(
            MODEL_SONNET_4_6, "high"
        )
        with pytest.raises(RouterMisconfigurationError, match="IMMUTABLE"):
            ModelRouter(routing_table=bad_table)

    def test_override_with_dated_snapshot_rejected(self) -> None:
        """Even a dated Sonnet snapshot ID is rejected — pinning is the
        model_pin layer's job, not the router's."""
        bad_table = dict(DEFAULT_ROUTING_TABLE)
        bad_table["trading_decision"] = RoutingDecision(
            "claude-sonnet-4-6-20250101", "max"
        )
        with pytest.raises(RouterMisconfigurationError, match="IMMUTABLE"):
            ModelRouter(routing_table=bad_table)

    def test_missing_trading_decision_rejected(self) -> None:
        bad_table: dict[TaskType, RoutingDecision] = {
            k: v for k, v in DEFAULT_ROUTING_TABLE.items() if k != "trading_decision"
        }
        with pytest.raises(RouterMisconfigurationError, match="trading_decision"):
            ModelRouter(routing_table=bad_table)

    def test_trading_decision_must_be_routing_decision(self) -> None:
        bad_table = dict(DEFAULT_ROUTING_TABLE)
        # Use a tuple instead of a RoutingDecision — common mistake
        bad_table["trading_decision"] = (MODEL_SONNET_4_6, "max")  # type: ignore[assignment]
        with pytest.raises(RouterMisconfigurationError, match="RoutingDecision"):
            ModelRouter(routing_table=bad_table)


# ---------------------------------------------------------------------------
# Custom routing tables (allowed when trading_decision preserved)
# ---------------------------------------------------------------------------


class TestCustomRoutingTables:
    def test_swap_haiku_for_sonnet_on_regime(self) -> None:
        """A research script that wants Sonnet for regime classification
        (e.g. quality-controlled run) is allowed."""
        custom = dict(DEFAULT_ROUTING_TABLE)
        custom["regime_classification"] = RoutingDecision(
            MODEL_SONNET_4_6, "high"
        )
        router = ModelRouter(routing_table=custom)
        assert router.route("regime_classification") == (
            MODEL_SONNET_4_6,
            "high",
        )
        # Trading decision still pinned
        assert router.route("trading_decision") == (MODEL_SONNET_4_6, "max")

    def test_change_effort_on_summary_aggregation(self) -> None:
        custom = dict(DEFAULT_ROUTING_TABLE)
        custom["summary_aggregation"] = RoutingDecision(
            MODEL_HAIKU_4_5, "low"
        )
        router = ModelRouter(routing_table=custom)
        assert router.route("summary_aggregation") == (
            MODEL_HAIKU_4_5,
            "low",
        )

    def test_table_with_unknown_key_rejected(self) -> None:
        bad_table: dict[str, RoutingDecision] = dict(DEFAULT_ROUTING_TABLE)
        bad_table["bogus_task_type"] = RoutingDecision(MODEL_HAIKU_4_5, "low")
        with pytest.raises(RouterMisconfigurationError, match="unknown"):
            ModelRouter(routing_table=bad_table)  # type: ignore[arg-type]

    def test_table_missing_non_trading_key_rejected(self) -> None:
        bad_table: dict[TaskType, RoutingDecision] = {
            k: v
            for k, v in DEFAULT_ROUTING_TABLE.items()
            if k != "summary_aggregation"
        }
        with pytest.raises(RouterMisconfigurationError, match="missing"):
            ModelRouter(routing_table=bad_table)

    def test_non_routing_decision_value_rejected(self) -> None:
        bad_table = dict(DEFAULT_ROUTING_TABLE)
        bad_table["regime_classification"] = "claude-haiku-4-5"  # type: ignore[assignment]
        with pytest.raises(RouterMisconfigurationError, match="RoutingDecision"):
            ModelRouter(routing_table=bad_table)

    def test_non_mapping_argument_rejected(self) -> None:
        with pytest.raises(RouterMisconfigurationError, match="Mapping"):
            ModelRouter(routing_table=[("trading_decision", RoutingDecision(MODEL_SONNET_4_6, "max"))])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Dry-run mode
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_returns_intended_routing(self) -> None:
        router = ModelRouter(dry_run=True)
        assert router.route("regime_classification") == (
            MODEL_HAIKU_4_5,
            "high",
        )
        assert router.route("trading_decision") == (MODEL_SONNET_4_6, "max")

    def test_dry_run_emits_warning_log(self, caplog: pytest.LogCaptureFixture) -> None:
        router = ModelRouter(dry_run=True)
        with caplog.at_level(logging.WARNING, logger="src.research_infra.model_router"):
            router.route("regime_classification")
        assert any(
            "[DRY-RUN]" in r.message and "regime_classification" in r.message
            for r in caplog.records
        )

    def test_non_dry_run_emits_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        router = ModelRouter(dry_run=False)
        with caplog.at_level(logging.WARNING, logger="src.research_infra.model_router"):
            router.route("regime_classification")
        assert not any("[DRY-RUN]" in r.message for r in caplog.records)

    def test_dry_run_property_exposed(self) -> None:
        assert ModelRouter(dry_run=True).dry_run is True
        assert ModelRouter(dry_run=False).dry_run is False
        # Default is False
        assert ModelRouter().dry_run is False


# ---------------------------------------------------------------------------
# Unknown task types
# ---------------------------------------------------------------------------


class TestUnknownTaskType:
    def test_unknown_task_type_raises(self) -> None:
        router = ModelRouter()
        with pytest.raises(UnknownTaskTypeError, match="Unknown task_type"):
            router.route("classification")  # type: ignore[arg-type]

    def test_empty_string_rejected(self) -> None:
        router = ModelRouter()
        with pytest.raises(UnknownTaskTypeError):
            router.route("")  # type: ignore[arg-type]

    def test_none_rejected(self) -> None:
        router = ModelRouter()
        with pytest.raises(UnknownTaskTypeError):
            router.route(None)  # type: ignore[arg-type]

    def test_unknown_error_message_lists_valid_values(self) -> None:
        router = ModelRouter()
        with pytest.raises(UnknownTaskTypeError) as excinfo:
            router.route("not_a_task")  # type: ignore[arg-type]
        msg = str(excinfo.value)
        for valid in VALID_TASK_TYPES:
            assert valid in msg


# ---------------------------------------------------------------------------
# Empty / None routing-table fallback
# ---------------------------------------------------------------------------


class TestEmptyAndNoneFallback:
    def test_none_uses_default(self) -> None:
        router = ModelRouter(routing_table=None)
        for task_type in VALID_TASK_TYPES:
            expected = DEFAULT_ROUTING_TABLE[task_type]
            assert router.route(task_type) == (expected.model_id, expected.effort)

    def test_empty_dict_uses_default(self) -> None:
        router = ModelRouter(routing_table={})
        for task_type in VALID_TASK_TYPES:
            expected = DEFAULT_ROUTING_TABLE[task_type]
            assert router.route(task_type) == (expected.model_id, expected.effort)

    def test_default_router_construction_no_error(self) -> None:
        """Bare ``ModelRouter()`` must not raise."""
        ModelRouter()


# ---------------------------------------------------------------------------
# validate_table standalone
# ---------------------------------------------------------------------------


class TestValidateTableStandalone:
    def test_default_table_passes(self) -> None:
        # Should not raise
        ModelRouter.validate_table(DEFAULT_ROUTING_TABLE)

    def test_validate_table_can_be_called_without_router(self) -> None:
        good_table = dict(DEFAULT_ROUTING_TABLE)
        good_table["regime_classification"] = RoutingDecision(
            MODEL_HAIKU_4_5, "low"
        )
        ModelRouter.validate_table(good_table)  # no raise

    def test_validate_table_raises_on_tampered(self) -> None:
        bad = dict(DEFAULT_ROUTING_TABLE)
        bad["trading_decision"] = RoutingDecision(MODEL_HAIKU_4_5, "max")
        with pytest.raises(RouterMisconfigurationError):
            ModelRouter.validate_table(bad)


# ---------------------------------------------------------------------------
# Defensive contract: DEFAULT_ROUTING_TABLE pin
# ---------------------------------------------------------------------------


class TestDefaultTablePin:
    """Pin the exact default routing decisions so accidental edits to
    ``DEFAULT_ROUTING_TABLE`` flag in CI."""

    def test_default_table_pinned_values(self) -> None:
        expected: Mapping[TaskType, RoutingDecision] = {
            "trading_decision": RoutingDecision(MODEL_SONNET_4_6, "max"),
            "regime_classification": RoutingDecision(MODEL_HAIKU_4_5, "high"),
            "metadata_extraction": RoutingDecision(MODEL_HAIKU_4_5, "medium"),
            "decay_analysis": RoutingDecision(MODEL_HAIKU_4_5, "high"),
            "summary_aggregation": RoutingDecision(MODEL_HAIKU_4_5, "medium"),
            "other": RoutingDecision(MODEL_SONNET_4_6, "high"),
        }
        assert dict(DEFAULT_ROUTING_TABLE) == dict(expected)
