from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from src.research_infra.train_engine import cuts
from src.research_infra.train_engine import decision_semantics as semantics
from src.research_infra.train_engine import repairs
from src.components.probability_debate_v4 import ProbabilityDebateTeamEngineV4
from src.research_infra.v4_timewarp_simulated_live_research_loop import (
    build_probability_context,
)


REPO = Path(__file__).resolve().parents[2]
TRUSTED_COMMISSION_SOURCE = semantics.TRUSTED_COMMISSION_REPAIR_SOURCE
CD_POOL_PATH = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase14/receipts/cd_pool.py"
)
CD_SPEC = importlib.util.spec_from_file_location("session_fd_cd_pool", CD_POOL_PATH)
assert CD_SPEC and CD_SPEC.loader
CD_POOL = importlib.util.module_from_spec(CD_SPEC)
CD_SPEC.loader.exec_module(CD_POOL)


def _scoreable_row(**updates):
    row = {
        "candidate_id": "candidate-a",
        "decision_time_utc": "2026-02-02T00:15:00+00:00",
        "symbol": "XAUUSD",
        "missed_opportunity_non_executable_diagnostic_scoreable": True,
        "missed_opportunity_r_scoreability_status": (
            "diagnostic_opportunity_r_scoreable"
        ),
        "opportunity_net_proxy_r": 1.8,
        "cost_r": 0.2,
        "spread_r": 0.1,
        "commission_r": 0.05,
        "swap_cost_r": 0.03,
        "expected_slippage_r": 0.02,
        "terminal_outcome": "target_reached_before_stop",
    }
    row.update(updates)
    return row


def _authorized_component_row(**updates):
    row = _scoreable_row(
        commission_r_repair_status="applied",
        commission_r_repair_total_redecode_status="complete_component_sum",
        commission_r_source=TRUSTED_COMMISSION_SOURCE,
        commission_r_broker_true_measured=0.05,
    )
    row.update(updates)
    row["cost_component_capture_evidence"] = {
        "spread_r": {
            "value": row.get("spread_r"),
            "source": "historical_ftmo_predecision_tick",
            "source_status": "captured",
        },
        "expected_slippage_r": {
            "value": row.get("expected_slippage_r"),
            "source": "config.selected_cell_default_expected_slippage_r",
            "source_status": "captured",
        },
        "swap_cost_r": {
            "value": row.get("swap_cost_r"),
            "source": "points_mode_time_stop_swap_cost_r_v1",
            "source_status": "captured",
        },
        "commission_r": {
            "value": row.get("commission_r"),
            "source": TRUSTED_COMMISSION_SOURCE,
            "source_status": "captured",
            "included_in_total_cost_r": True,
        },
    }
    return row


def _repair_packet(**component_updates):
    components = {
        "spread_r": 0.0258,
        "expected_slippage_r": 0.02,
        "swap_cost_r": 0.001,
        "commission_r": None,
        "authority_fallback_total_cost_r": 0.12,
    }
    components.update(component_updates)
    return {
        "status": "REFUSED",
        "refusal_reasons": [
            "missing_broker_true_commission_cost_r_conversion:"
            "broker_true_commission_schedule_or_required_entry_price",
            "authority_conservative_broker_default_no_broker_total_cost_r",
        ],
        "commission_model_required": False,
        "commission_cost_model_required": True,
        "commission_cost": {
            "model_version": "broker_true_commission_cash_to_r_v1",
            "source_status": "source_gap",
            "cost_r": None,
            "missing_fields": [
                "broker_true_commission_schedule_or_required_entry_price"
            ],
        },
        "quote_authority": {
            "quote_source": "historical_ftmo_predecision_tick"
        },
        "tick_cost": {
            "spread_r": components.get("spread_r"),
            "source_status": "captured",
        },
        "spread_r": components.get("spread_r"),
        "expected_slippage_r": components.get("expected_slippage_r"),
        "expected_slippage_source": (
            "config.selected_cell_default_expected_slippage_r"
        ),
        "swap_cost": {
            "model_version": "points_mode_time_stop_swap_cost_r_v1",
            "source_status": "captured",
            "cost_r": components.get("swap_cost_r"),
        },
        "total_cost_r": 0.12,
        "old_timewarp_candidate_cost_r_fallback_diagnostic": 0.08,
        "total_cost_components": components,
        "max_spread_r": 0.10,
        "max_total_cost_r": 0.15,
        "cost_limit_tolerance_r": 1e-6,
        "config_requirements": {"packet_required": True},
    }


def test_missed_projection_flattens_cost_packet_and_repair_provenance() -> None:
    row = _scoreable_row(
        pretrade_broker_net_cost_packet={
            "status": "PASSED",
            "model_version": "cost-v3",
            "commission_r_repair_status": "applied",
            "commission_r_regated": True,
            "swap_horizon_repair_status": "applied",
            "swap_horizon_bars_used": 8,
            "quote_authority": {
                "quote_source": "ultimate_book_measured_tick_spread_floor",
                "measured_tick_spread_floor_r": 0.0118,
            },
        }
    )

    projected = cuts.project_missed_pool_row(row)

    assert projected["pretrade_cost_packet_status"] == "PASSED"
    assert projected["commission_r_repair_status"] == "applied"
    assert projected["commission_r_regated"] is True
    assert projected["swap_horizon_repair_status"] == "applied"
    assert projected["swap_horizon_bars_used"] == 8
    assert projected["legacy_cost_quote_source"] == (
        "ultimate_book_measured_tick_spread_floor"
    )
    assert projected["cost_quote_source"] == (
        "ultimate_book_historical_spread_floor_template"
    )
    assert projected["cost_quote_measurement_status"] == (
        "templated_not_decision_measured"
    )


def test_flat_point_twelve_fallback_is_preserved_but_not_authoritative() -> None:
    repaired = semantics.normalize_evidence_row(
        _scoreable_row(
            symbol="GER40",
            cost_r=0.12,
            expected_cost_r=0.12,
            spread_r=0.335891148,
            commission_r=None,
            swap_cost_r=0.002783978,
            miss_reason=(
                "scheduler_materialization_skipped_selector_not_risk_bearing_"
                "cost_missing"
            ),
            broker_pretrade_cost_executable=False,
        )
    )

    assert repaired["recorded_cost_r"] == 0.12
    assert repaired["legacy_emitter_fallback_cost_r"] == 0.12
    assert repaired["authoritative_cost_r"] is None
    assert repaired["cost_capture_contract_status"] == "missing_capture_inputs"
    assert repaired["cost_r_authority_status"] == (
        "legacy_emitter_fallback_non_authoritative"
    )
    assert "broker_true_commission_capture" in repaired[
        "cost_capture_missing_inputs"
    ]


def test_flat_point_twelve_can_be_redecoded_only_with_repair_provenance() -> None:
    legacy = _scoreable_row(
        symbol="GER40",
        cost_r=0.12,
        spread_r=0.335891148,
        commission_r=0.0,
        swap_cost_r=0.002783978,
        broker_pretrade_cost_executable=False,
        miss_reason="scheduler_materialization_cost_missing",
    )
    unbound = semantics.normalize_evidence_row(legacy)
    bound_row = {
        **legacy,
        "commission_r": 0.0,
        "commission_r_broker_true_measured": 0.0,
        "legacy_emitter_fallback_cost_r": 0.12,
        "legacy_emitter_fallback_replaced": True,
    }
    bound = semantics.normalize_evidence_row(
        _authorized_component_row(**bound_row)
    )

    expected = 0.335891148 + 0.02 + 0.002783978
    assert unbound["cost_redecode_candidate_r"] == pytest.approx(expected)
    assert unbound["authoritative_cost_r"] is None
    assert unbound["cost_redecode_authority_status"] == (
        "blocked_incomplete_components"
    )
    assert bound["authoritative_cost_r"] == pytest.approx(expected)
    assert bound["cost_capture_contract_status"] == (
        "complete_components_redecoded"
    )


def test_zero_commission_repair_replaces_emitter_fallback_and_heals_gate() -> None:
    packet = {
        "status": "REFUSED",
        "refusal_reasons": [
            "missing_broker_true_commission_cost_r_conversion:"
            "broker_true_commission_schedule_or_required_entry_price",
            "authority_conservative_broker_default_no_broker_total_cost_r",
        ],
        "commission_model_required": False,
        "commission_cost_model_required": True,
        "commission_cost": {
            "model_version": "broker_true_commission_cash_to_r_v1",
            "source_status": "source_gap",
            "cost_r": None,
            "missing_fields": [
                "broker_true_commission_schedule_or_required_entry_price"
            ],
        },
        "quote_authority": {
            "quote_source": "historical_ftmo_predecision_tick"
        },
        "tick_cost": {"spread_r": 0.0258, "source_status": "captured"},
        "spread_r": 0.0258,
        "expected_slippage_r": 0.02,
        "expected_slippage_source": (
            "config.selected_cell_default_expected_slippage_r"
        ),
        "swap_cost": {
            "model_version": "points_mode_time_stop_swap_cost_r_v1",
            "source_status": "captured",
            "cost_r": 0.001,
        },
        "total_cost_r": 0.12,
        "old_timewarp_candidate_cost_r_fallback_diagnostic": 0.08,
        "total_cost_components": {
            "spread_r": 0.0258,
            "expected_slippage_r": 0.02,
            "swap_cost_r": 0.001,
            "commission_r": None,
            "authority_fallback_total_cost_r": 0.12,
        },
        "max_spread_r": 0.10,
        "max_total_cost_r": 0.15,
        "cost_limit_tolerance_r": 1e-6,
        "config_requirements": {"packet_required": True},
    }

    repaired = repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=0.0,
        charge_r=0.0,
        source=TRUSTED_COMMISSION_SOURCE,
        regate=True,
    )

    assert repaired["commission_cost"]["source_status"] == "captured"
    assert repaired["commission_cost"]["cost_r"] == 0.0
    assert repaired["cost_component_state"] == "complete"
    assert repaired["cost_decision_authorization_status"] == (
        "authorized_complete_component_cost"
    )
    assert repaired["total_cost_r"] == pytest.approx(0.0468)
    assert "authority_fallback_total_cost_r" not in repaired[
        "total_cost_components"
    ]
    assert repaired["legacy_emitter_fallback_cost_r"] == 0.12
    assert repaired["old_proxy_vs_broker_calibrated_delta_r"] == pytest.approx(
        -0.0332
    )
    assert repaired["status"] == "PASSED"
    assert repaired["refusal_reasons"] == []


def test_decision_semantics_capture_patch_is_default_safe_and_unsealed() -> None:
    patch = cuts.make_decision_semantics_projection_patch()

    assert patch.default_on is True
    assert patch.sealed_compatible is False
    assert "decision_semantics_projection" in cuts.TRAIN_SAFE_SET_PATCHES


def test_cost_attribution_capture_carries_repair_status_from_packet() -> None:
    fields = cuts.cost_attribution_provenance_fields(
        {
            "commission_r_repair_status": "applied",
            "commission_r_broker_true_measured": 0.0,
            "commission_r_regated": True,
            "commission_r_repair_total_redecode_status": (
                "complete_component_sum"
            ),
            "scalar_fields": {
                "swap_horizon_repair_status": "applied",
                "swap_horizon_bars_used": 8,
            },
        }
    )
    patch = cuts.make_cost_attribution_provenance_patch()

    assert fields == {
        "commission_r_broker_true_measured": 0.0,
        "commission_r_repair_status": "applied",
        "commission_r_regated": True,
        "swap_horizon_repair_status": "applied",
        "swap_horizon_bars_used": 8,
        "commission_r_repair_total_redecode_status": "complete_component_sum",
    }
    assert patch.default_on is True
    assert patch.sealed_compatible is False
    assert "cost_attribution_provenance" in cuts.TRAIN_SAFE_SET_PATCHES


def test_cost_attribution_runtime_wrapper_emits_provenance() -> None:
    from src.research_infra import v4_timewarp_simulated_live_research_loop as loop

    packets = {
        "pretrade_broker_net_cost_packet": {
            "status": "PASSED",
            "authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "total_cost_r": 0.0468,
            "commission_r": 0.0,
            "commission_r_repair_status": "applied",
            "commission_r_broker_true_measured": 0.0,
            "commission_r_regated": True,
            "commission_r_repair_total_redecode_status": (
                "complete_component_sum"
            ),
            "total_cost_components": {
                "spread_r": 0.0258,
                "expected_slippage_r": 0.02,
                "swap_cost_r": 0.001,
                "commission_r": 0.0,
            },
        }
    }
    assert "commission_r_repair_status" not in loop.pretrade_cost_attribution_fields(
        packets
    )
    patch = cuts.make_cost_attribution_provenance_patch()
    patch.apply()
    try:
        emitted = loop.pretrade_cost_attribution_fields(packets)
    finally:
        patch.revert()

    assert emitted["commission_r_repair_status"] == "applied"
    assert emitted["commission_r_broker_true_measured"] == 0.0
    assert emitted["commission_r_regated"] is True
    assert emitted["commission_r_repair_total_redecode_status"] == (
        "complete_component_sum"
    )


def test_complete_cost_components_explain_geometry_rebase_without_overwrite() -> None:
    repaired = semantics.normalize_evidence_row(
        _authorized_component_row(
            cost_r=0.30,
            spread_r=0.10,
            commission_r=0.05,
            swap_cost_r=0.03,
            expected_slippage_r=0.02,
            marketable_limit_cost_r_rebased_to_effective_fill_geometry=True,
            marketable_limit_original_expected_cost_r=0.20,
            marketable_limit_effective_expected_cost_r=0.30,
            limit_immediate_marketable_cost_r_rebase_multiplier=1.5,
        )
    )

    assert repaired["authoritative_cost_r"] == 0.30
    assert repaired["cost_component_sum_r"] == pytest.approx(0.20)
    assert repaired["cost_component_rebase_delta_r"] == pytest.approx(0.10)
    assert repaired["cost_accounting_status"] == (
        "component_sum_plus_explicit_geometry_rebase"
    )


@pytest.mark.parametrize("missing_field", semantics.COST_COMPONENT_FIELDS)
def test_component_contract_refuses_each_single_absent_component(
    missing_field: str,
) -> None:
    row = _authorized_component_row()
    del row[missing_field]

    repaired = semantics.normalize_evidence_row(row)

    assert repaired["recorded_cost_r"] == 0.2
    assert repaired["authoritative_cost_r"] is None
    assert repaired["cost_component_state"] == "incomplete"
    assert repaired["cost_decision_authorization_status"] == (
        "refused_incomplete_component_cost"
    )
    assert f"absent_component:{missing_field}" in repaired[
        "cost_decision_refusal_reasons"
    ]
    assert "cost_component_sum_r" not in repaired


def test_component_contract_preserves_multiple_missing_components() -> None:
    row = _authorized_component_row()
    del row["spread_r"]
    del row["swap_cost_r"]

    repaired = semantics.normalize_evidence_row(row)

    assert repaired["cost_component_state"] == "incomplete"
    assert repaired["cost_decision_refusal_reasons"] == [
        "absent_component:spread_r",
        "absent_component:swap_cost_r",
    ]
    assert repaired["authoritative_cost_r"] is None


def test_explicit_authorized_zero_is_complete_but_absent_zero_authority_is_not() -> None:
    authorized_zero = _authorized_component_row(
        cost_r=0.10,
        commission_r=0.0,
        commission_r_broker_true_measured=0.0,
        expected_slippage_r=0.0,
        swap_cost_r=0.0,
    )
    absent_zero_authority = dict(authorized_zero)
    del absent_zero_authority["commission_r_broker_true_measured"]

    complete = semantics.normalize_evidence_row(authorized_zero)
    incomplete = semantics.normalize_evidence_row(absent_zero_authority)

    assert complete["cost_component_state"] == "complete"
    assert complete["cost_component_sum_r"] == pytest.approx(0.10)
    assert complete["authoritative_cost_r"] == pytest.approx(0.10)
    assert complete["cost_decision_refusal_reasons"] == []
    assert incomplete["cost_component_state"] == "incomplete"
    assert "missing_authority:commission_r_broker_true_measured" in incomplete[
        "cost_decision_refusal_reasons"
    ]
    assert incomplete["authoritative_cost_r"] is None


@pytest.mark.parametrize("component", semantics.COST_COMPONENT_FIELDS)
@pytest.mark.parametrize("non_finite", [float("nan"), float("inf")])
def test_component_contract_refuses_nan_and_infinity(
    component: str,
    non_finite: float,
) -> None:
    row = _authorized_component_row(**{component: non_finite})

    repaired = semantics.normalize_evidence_row(row)

    assert repaired["cost_component_state"] == "incomplete"
    assert f"non_finite_component:{component}" in repaired["cost_decision_refusal_reasons"]
    assert repaired["authoritative_cost_r"] is None
    assert repaired["cost_decision_authorization_status"] == (
        "refused_incomplete_component_cost"
    )


def test_component_commission_must_match_measured_commission() -> None:
    row = _authorized_component_row(commission_r_broker_true_measured=0.04)

    repaired = semantics.normalize_evidence_row(row)

    assert repaired["cost_component_state"] == "refused"
    assert repaired["cost_component_candidate_sum_r"] == pytest.approx(0.20)
    assert (
        "inconsistent_component:commission_r_vs_"
        "commission_r_broker_true_measured"
    ) in repaired["cost_decision_refusal_reasons"]
    assert repaired["authoritative_cost_r"] is None
    assert "cost_component_sum_r" not in repaired


def test_unexplained_recorded_total_mismatch_is_refused() -> None:
    repaired = semantics.normalize_evidence_row(
        _authorized_component_row(cost_r=0.19)
    )

    assert repaired["cost_component_state"] == "refused"
    assert repaired["recorded_cost_r"] == pytest.approx(0.19)
    assert repaired["cost_component_candidate_sum_r"] == pytest.approx(0.20)
    assert repaired["cost_component_rebase_delta_r"] == pytest.approx(-0.01)
    assert "recorded_total_component_sum_mismatch" in repaired["cost_decision_refusal_reasons"]
    assert repaired["authoritative_cost_r"] is None


def test_fully_complete_component_sum_authorizes_exact_economics() -> None:
    row = _authorized_component_row()

    repaired = semantics.normalize_evidence_row(row)

    assert repaired["decision_semantics_schema"] == (
        "gtos.train_engine.decision_semantics.v2"
    )
    assert repaired["cost_component_state"] == "complete"
    assert repaired["cost_component_sum_r"] == pytest.approx(0.20)
    assert repaired["authoritative_cost_r"] == pytest.approx(0.20)
    assert repaired["cost_decision_authorization_status"] == (
        "authorized_complete_component_cost"
    )
    assert repaired["cost_decision_refusal_reasons"] == []


def test_downstream_cost_authorization_refuses_incomplete_evidence() -> None:
    row = _authorized_component_row(swap_cost_r=None)

    projected = cuts.project_missed_pool_row(row)

    assert projected["recorded_cost_r"] == pytest.approx(0.20)
    assert projected["cost_component_state"] == "incomplete"
    assert "null_component:swap_cost_r" in projected[
        "cost_decision_refusal_reasons"
    ]
    assert projected["cost_decision_authorization_status"] == (
        "refused_incomplete_component_cost"
    )
    assert projected["authoritative_cost_r"] is None
    assert semantics.authoritative_cost_value(row) is None


def test_incomplete_v1_row_cannot_retain_stale_complete_authorization() -> None:
    row = _authorized_component_row(
        swap_cost_r=None,
        decision_semantics_schema="gtos.train_engine.decision_semantics.v1",
        cost_component_state="complete",
        cost_component_sum_r=0.17,
        authoritative_cost_r=0.17,
        cost_decision_authorization_status=(
            "authorized_complete_component_cost"
        ),
    )

    repaired = semantics.normalize_evidence_row(row)

    assert repaired["decision_semantics_schema"] == (
        "gtos.train_engine.decision_semantics.v2"
    )
    assert repaired["cost_component_state"] == "incomplete"
    assert "cost_component_sum_r" not in repaired
    assert repaired["authoritative_cost_r"] is None
    assert repaired["cost_decision_authorization_status"] == (
        "refused_incomplete_component_cost"
    )


@pytest.mark.parametrize(
    "missing_field",
    ["spread_r", "expected_slippage_r", "swap_cost_r"],
)
def test_packet_redecode_never_zero_fills_a_missing_component(
    missing_field: str,
) -> None:
    packet = _repair_packet()
    del packet["total_cost_components"][missing_field]

    repaired = repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=0.0,
        charge_r=0.0,
        source=TRUSTED_COMMISSION_SOURCE,
        regate=False,
    )

    assert repaired["total_cost_r"] == 0.12
    assert repaired["cost_component_state"] == "incomplete"
    assert repaired["commission_r_repair_total_redecode_status"] == (
        "refused_incomplete_component_sum"
    )
    assert repaired["commission_r_repair_total_redecode_missing_fields"] == [
        missing_field
    ]
    assert repaired["total_cost_components"][
        "authority_fallback_total_cost_r"
    ] == 0.12
    assert "cost_component_sum_r" not in repaired


@pytest.mark.parametrize(
    ("component", "non_finite"),
    [
        ("expected_slippage_r", float("nan")),
        ("swap_cost_r", float("inf")),
    ],
)
def test_packet_redecode_refuses_non_finite_components(
    component: str,
    non_finite: float,
) -> None:
    packet = _repair_packet(**{component: non_finite})

    repaired = repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=0.0,
        charge_r=0.0,
        source=TRUSTED_COMMISSION_SOURCE,
        regate=True,
    )

    assert repaired["total_cost_r"] == 0.12
    assert repaired["status"] == "REFUSED"
    assert repaired["cost_component_state"] == "incomplete"
    assert component in repaired[
        "commission_r_repair_total_redecode_missing_fields"
    ]
    assert f"non_finite_component:{component}" in repaired[
        "cost_decision_refusal_reasons"
    ]
    assert "commission_repair_component_sum_incomplete" in repaired[
        "refusal_reasons"
    ]


def test_packet_redecode_refuses_measured_component_commission_mismatch() -> None:
    packet = _repair_packet()

    repaired = repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=0.04,
        charge_r=0.05,
        source=TRUSTED_COMMISSION_SOURCE,
        regate=False,
    )

    assert repaired["total_cost_r"] == 0.12
    assert repaired["cost_component_state"] == "refused"
    assert repaired["commission_r_repair_total_redecode_status"] == (
        "refused_inconsistent_component_sum"
    )
    assert (
        "inconsistent_component:commission_r_vs_"
        "commission_r_broker_true_measured"
    ) in repaired["cost_decision_refusal_reasons"]
    assert repaired["commission_cost"]["included_in_total_cost_r"] is False


def test_fd_complete_row_results_and_economics_remain_identical() -> None:
    reproduction = (
        REPO
        / "research/operations/wave19_sol_repair_2026_08_01/defects/"
        "REPRODUCTION_AND_BIAS.json"
    )
    assert hashlib.sha256(reproduction.read_bytes()).hexdigest() == (
        "c9c8516ffbf084f386c8db9e7a13a00bf13155fa45198284d5722a3a88453f30"
    )
    fd = json.loads(reproduction.read_text())["february"]["missed"][
        "flat_0p12_cost"
    ]
    assert (fd["physical_rows"], fd["scoreable_rows"]) == (17716, 3555)
    assert {
        symbol: (
            values["complete_component_rows"],
            values["redecoded_mean_cost_r"],
            values["scoreable_redecoded_net_r_sum"],
            values["scoreable_sign_flips"],
        )
        for symbol, values in fd["symbols"].items()
    } == {
        "GER40": (13196, 0.333507473, -712.117011599, 18),
        "UKOIL_cash": (2532, 0.067010369, -198.249660512, 36),
        "USOIL_cash": (1988, 0.077987289, -140.81004413, 13),
    }

    historical = semantics.normalize_evidence_row(
        _scoreable_row(
            symbol="GER40",
            cost_r=0.12,
            spread_r=0.335891148,
            commission_r=0.0,
            swap_cost_r=0.002783978,
            expected_slippage_r=0.02,
            broker_pretrade_cost_executable=False,
            commission_r_repair_status="applied",
            commission_r_broker_true_measured=0.0,
        )
    )
    expected = 0.335891148 + 0.02 + 0.002783978
    assert historical["cost_component_state"] == "incomplete"
    assert historical["cost_component_candidate_sum_r"] == expected
    assert historical["authoritative_cost_r"] is None


def test_terminal_outcome_is_not_a_close_mark_source() -> None:
    repaired = semantics.normalize_evidence_row(
        {
            "candidate_id": "candidate-a",
            "decision_time_utc": "2026-01-02T00:15:00+00:00",
            "close_mark_source": "stop_reached_before_target",
            "terminal_outcome": "stop_reached_before_target",
        },
        row_kind="trade",
    )

    assert repaired["terminal_outcome"] == "stop_reached_before_target"
    assert repaired["close_mark_source"] is None
    assert repaired["legacy_close_mark_source"] == "stop_reached_before_target"
    assert repaired["close_mark_source_semantics_status"] == (
        "legacy_terminal_outcome_overload_repaired"
    )


def test_binary_population_definitions_are_explicit_and_not_interchangeable(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "missed.jsonl"
    rows = [
        _scoreable_row(candidate_id="exact-target", opportunity_net_proxy_r=1.8),
        _scoreable_row(
            candidate_id="exact-stop",
            opportunity_net_proxy_r=-1.2,
            terminal_outcome="stop_reached_before_target",
        ),
        _scoreable_row(
            candidate_id="touch-target-not-exact",
            opportunity_net_proxy_r=0.4,
            terminal_outcome="target_reached_before_stop",
        ),
    ]
    ledger.write_text("".join(json.dumps(row) + "\n" for row in rows))

    summary = CD_POOL.summarise(ledger, None)
    exact = summary["gross"]["exact_contract_endpoint_population"]
    first_touch = summary["gross"]["terminal_outcome_first_touch_population"]

    assert (exact["n_target"], exact["n_stop"]) == (1, 1)
    assert (first_touch["n_target"], first_touch["n_stop"]) == (2, 1)
    assert summary["gross"]["binary_population"]["deprecated_alias_of"] == (
        "exact_contract_endpoint_population"
    )
    assert exact["definition"] != first_touch["definition"]


def test_router_reject_reinjection_is_explicitly_replay_only() -> None:
    repaired = semantics.normalize_evidence_row(
        _scoreable_row(
            selector_action="reject",
            selector_reason="admission_quality_dynamic_router_refused_candidate_use",
            effective_selector_action="open-reduced-risk",
            scheduler_materialization_status="scheduler_option_materialized",
        )
    )

    assert repaired["selector_router_reinjection_applied"] is True
    assert repaired["selector_router_reinjection_policy_status"] == (
        "deliberate_replay_softening"
    )
    assert repaired["selector_router_reinjection_authority"] == (
        "selector_reject_open_reduced_materialization_detail"
    )
    assert repaired["selector_router_reinjection_scope"] == (
        "local_replay_only_no_broker_authority"
    )


def test_authority_gate_keeps_intentional_demotion_and_exposes_missing_failures() -> None:
    invalid = semantics.normalize_evidence_row(
        _scoreable_row(
            miss_reason=(
                "scheduler_materialization_skipped_package_positive_reduce_risk_"
                "signed_authority_invalid"
            )
        )
    )
    demoted = semantics.normalize_evidence_row(
        _scoreable_row(
            miss_reason=(
                "scheduler_materialization_skipped_selector_reduce_risk_open_"
                "reduced_not_executable:numeric_disagreement_open_reduced_risk_"
                "disabled_by_config"
            )
        )
    )
    captured = cuts.project_missed_pool_row(
        _scoreable_row(
            miss_reason=(
                "scheduler_materialization_skipped_package_positive_reduce_risk_"
                "signed_authority_invalid"
            ),
            ultimate_candidate_package_reduce_risk_authority={
                "failures": ["immutable_payload_hash_mismatch"]
            },
        )
    )

    assert invalid["package_authority_gate_status"] == "blocked_signature_invalid"
    assert invalid["package_authority_failure_capture_status"] == (
        "missing_failure_payload"
    )
    assert demoted["package_authority_gate_status"] == (
        "intentional_repaired_profile_demotion"
    )
    assert demoted["package_authority_effective_config_value"] is False
    assert captured["package_authority_failures"] == [
        "immutable_payload_hash_mismatch"
    ]
    assert captured["package_authority_failure_capture_status"] == "captured"


def test_unscoreable_terminal_status_and_slippage_template_are_not_outcomes() -> None:
    repaired = semantics.normalize_evidence_row(
        {
            "candidate_id": "candidate-a",
            "decision_time_utc": "2026-01-02T00:15:00+00:00",
            "close_reason": (
                "entry_fill_executable_terminal_r_ordered_tick_sequence_required"
            ),
            "headline_result_exclusion_reason": (
                "entry_fill_executable_terminal_r_ordered_tick_sequence_required"
            ),
            "net_r": 0.0,
            "cost_r": 0.082154,
            "expected_slippage_r": 0.02,
        },
        row_kind="trade",
    )

    assert repaired["close_reason"] is None
    assert repaired["terminal_scoreability_status"] == (
        "entry_fill_executable_terminal_r_ordered_tick_sequence_required"
    )
    assert repaired["trade_headline_scoreable"] is False
    assert repaired["authoritative_net_r"] is None
    assert repaired["recorded_net_r"] == 0.0
    assert repaired["expected_slippage_measurement_status"] == (
        "modeled_constant_not_measured"
    )
    assert repaired["expected_slippage_authority"] == (
        "config.selected_cell_default_expected_slippage_r"
    )


def test_ev_and_template_scores_are_marked_non_authoritative() -> None:
    repaired = semantics.normalize_evidence_row(
        _scoreable_row(
            origin_family="current_fvg_fill",
            candidate_ev_r=0.7,
            expected_net_r=0.5,
            candidate_confidence=0.55,
            confidence_default_applied=True,
            execution_fill_probability=0.92,
            limit_marketable_at_decision=True,
            policy_target_r=2.0,
            selected_policy_for_expected_net_r="momentum_exhaustion",
        )
    )

    assert repaired["ev_cost_context_status"] == (
        "indirect_probability_cost_sensitivity_present_"
        "direct_ev_cost_term_unwired"
    )
    assert repaired["ev_probability_cost_sensitivity_status"] == (
        "cost_affects_base_probability_and_source_weights"
    )
    assert repaired["ev_direct_cost_term_status"] == (
        "probability_context_omits_cost_r_so_debate_cost_r_is_zero"
    )
    assert repaired["ev_geometry_alignment_status"] == (
        "pre_rewrite_1p5r_ev_vs_2p0r_execution_geometry"
    )
    assert repaired["origin_family_hash_authority_status"] == (
        "deterministic_name_hash_heuristic_non_authoritative"
    )
    assert repaired["authoritative_candidate_confidence"] is None
    assert repaired["candidate_confidence_authority_status"] == (
        "missing_confidence_constant_default_non_authoritative"
    )
    assert repaired["authoritative_execution_fill_probability"] is None
    assert repaired["execution_fill_probability_authority_status"] == (
        "marketable_limit_constant_template_non_authoritative"
    )


def test_probability_context_carries_indirect_but_not_direct_cost_semantics() -> None:
    candidate = {
        "candidate_id": "candidate-cost-wiring",
        "symbol": "XAUUSD",
        "side": "LONG",
        "risk_reward_ratio": 2.0,
        "source_window_complete": True,
        "source_fields": {
            "atr14_atr50_ratio": 1.0,
            "lookback50_position": 0.8,
            "trend_state_20": "uptrend",
        },
    }
    low_cost = build_probability_context(
        candidate,
        "2026-02-02T00:15:00+00:00",
        None,
        cost_r=0.02,
    )
    high_cost = build_probability_context(
        candidate,
        "2026-02-02T00:15:00+00:00",
        None,
        cost_r=0.20,
    )

    assert high_cost["base_probability"] < low_cost["base_probability"]
    assert high_cost["sources"][0]["cost_sensitivity"] > low_cost["sources"][0][
        "cost_sensitivity"
    ]
    assert "cost_r" not in high_cost
    assert "estimated_cost_r" not in high_cost

    config = {
        "gtos_vnext_runtime": {
            "probability_debate_team_engine_v4": {
                "enabled": True,
                "apply_to_execution": False,
                "decision_log_enabled": False,
            }
        }
    }
    decision = ProbabilityDebateTeamEngineV4(config).evaluate(high_cost)
    long_thesis = next(
        row for row in decision.to_record()["theses"] if row["action"] == "long"
    )
    assert long_thesis["cost_r"] == 0.0

    direct_cost_context = {**high_cost, "cost_r": 0.20}
    direct_cost_decision = ProbabilityDebateTeamEngineV4(config).evaluate(
        direct_cost_context
    )
    direct_cost_long = next(
        row
        for row in direct_cost_decision.to_record()["theses"]
        if row["action"] == "long"
    )
    assert direct_cost_long["cost_r"] == pytest.approx(0.20)
    assert direct_cost_long["EV"] < long_thesis["EV"]


def test_compact_projection_canonicalizes_key_drift_and_composite_identity() -> None:
    projected = CD_POOL.project(
        _scoreable_row(
            final_blocker_class=None,
            missed_package_replay_order_executable_final_blocker_class=(
                "cost_authority"
            ),
        )
    )

    assert projected["final_blocker_class"] == "cost_authority"
    assert projected["canonical_replay_candidate_instance_key"] == (
        "candidate-a@@2026-02-02T00:15:00+00:00"
    )
    assert projected["candidate_identity_join_contract"] == (
        "candidate_id_plus_decision_time_utc"
    )


# ---------------------------------------------------------------------------
# R-SCHEMA (Session FA Phase C): exit-vocabulary layers and clamp derivation
# ---------------------------------------------------------------------------


def test_exit_vocabulary_layers_get_two_names_and_a_disagreement_bit() -> None:
    # Walk trade 4: the raw path DID reach the stop while the policy overlay
    # had already harvested at the giveback trigger -- two truths, two names.
    trade = semantics.normalize_evidence_row(
        {
            "terminal_outcome": "stop_reached_before_target",
            "close_reason": "selected_policy_replay:giveback_close",
        },
        row_kind="trade",
    )
    assert trade["exit_raw_path_terminal"] == "stop_reached_before_target"
    assert trade["exit_policy_overlay_close"] == (
        "selected_policy_replay:giveback_close"
    )
    assert trade["exit_layers_disagree"] is True
    # The original fields stay byte-identical.
    assert trade["terminal_outcome"] == "stop_reached_before_target"
    assert trade["close_reason"] == "selected_policy_replay:giveback_close"

    # Missed rows carry one merged vocabulary (terminal == opportunity close
    # reason on 8,448/8,448 fence rows): the companions must agree.
    missed = semantics.normalize_evidence_row(
        {
            "terminal_outcome": "time_stop_close_mark_from_m1",
            "opportunity_close_reason": "time_stop_close_mark_from_m1",
        }
    )
    assert missed["exit_raw_path_terminal"] == "time_stop_close_mark_from_m1"
    assert missed["exit_policy_overlay_close"] == "time_stop_close_mark_from_m1"
    assert missed["exit_layers_disagree"] is False

    # An unscoreable-nulled close_reason still surfaces its overlay layer via
    # the legacy copy the terminal repair takes.
    unscoreable = semantics.normalize_evidence_row(
        {
            "terminal_outcome": "stop_reached_before_target",
            "close_reason": "entry_fill_executable_terminal_r_ordered_"
            "tick_sequence_required_unscoreable",
        },
        row_kind="trade",
    )
    assert unscoreable["close_reason"] is None
    assert unscoreable["exit_policy_overlay_close"] == (
        "entry_fill_executable_terminal_r_ordered_tick_sequence_"
        "required_unscoreable"
    )

    # Rows with neither vocabulary stay untouched -- additive only.
    silent = semantics.normalize_evidence_row({"candidate_id": "c"})
    assert "exit_raw_path_terminal" not in silent
    assert "exit_policy_overlay_close" not in silent
    assert "exit_layers_disagree" not in silent


def test_close_mark_clamp_flags_derive_the_frozen_walkers_bound() -> None:
    # Walk trade 1 values: mark +0.2236 against an agreed 2.0R target -- the
    # bound did not bind.
    unclamped = semantics.normalize_evidence_row(
        {
            "terminal_outcome": "filled_time_stop_close_mark",
            "close_mark_r": 0.2236324,
            "target_r": 2.0,
            "policy_target_r": 2.0,
            "raw_target_r": 2.0,
        }
    )
    assert unclamped["close_mark_clamped"] is False
    assert unclamped["close_mark_ambiguity_floor"] is False
    assert unclamped["close_mark_clamp_semantics_status"] == "not_clamped"

    # A mark beyond the agreed target is silently relabeled to the endpoint by
    # `bounded_close_r = max(-1.0, min(mark, target))`; the flag names it.
    ceiling = semantics.normalize_evidence_row(
        {
            "terminal_outcome": "time_stop_close_mark_from_m1",
            "opportunity_close_reason": "time_stop_close_mark_from_m1",
            "counterfactual_order_close_mark_r": 2.7,
            "raw_target_r": 2.0,
            "policy_target_r": 2.0,
        }
    )
    assert ceiling["close_mark_clamped"] is True
    assert ceiling["close_mark_clamp_semantics_status"] == (
        "clamped_at_target_ceiling"
    )

    # A gap beyond -1.0 needs no target to be recognized.
    floor = semantics.normalize_evidence_row(
        {
            "terminal_outcome": "filled_time_stop_close_mark",
            "close_mark_r": -1.4,
        }
    )
    assert floor["close_mark_clamped"] is True
    assert floor["close_mark_clamp_semantics_status"] == "clamped_at_stop_floor"

    # Same-bar ambiguity ASSIGNS -1.0 without any mark; it is a floor, not a
    # clamp of a marked value.
    ambiguity = semantics.normalize_evidence_row(
        {
            "terminal_outcome": "same_bar_ambiguity_conservative_stop_close",
            "opportunity_close_reason": (
                "same_bar_ambiguity_conservative_stop_close"
            ),
        }
    )
    assert ambiguity["close_mark_ambiguity_floor"] is True
    assert ambiguity["close_mark_clamped"] is False
    assert ambiguity["close_mark_clamp_semantics_status"] == (
        "ambiguity_conservative_floor_assigned_no_mark"
    )

    # Honest refusals: a mark-based close without the mark input, and a mark
    # exceeding one of two DISAGREEING targets (raw vs policy re-target) whose
    # pairing cannot be reconstructed from the row.
    absent = semantics.normalize_evidence_row(
        {"terminal_outcome": "filled_time_stop_close_mark"}
    )
    assert absent["close_mark_clamped"] is None
    assert absent["close_mark_clamp_semantics_status"] == (
        "close_mark_input_absent_not_derivable"
    )
    ambiguous_pairing = semantics.normalize_evidence_row(
        {
            "terminal_outcome": "filled_time_stop_close_mark",
            "close_mark_r": 3.0,
            "raw_target_r": 4.529778663,
            "policy_target_r": 2.0,
        }
    )
    assert ambiguous_pairing["close_mark_clamped"] is None
    assert ambiguous_pairing["close_mark_clamp_semantics_status"] == (
        "target_pairing_ambiguous_not_derivable"
    )
    # Walk trade 2/3 shape: targets disagree but the mark sits below both, so
    # every pairing agrees the ceiling did not bind.
    below_all = semantics.normalize_evidence_row(
        {
            "terminal_outcome": "filled_time_stop_close_mark",
            "close_mark_r": 1.22151178,
            "raw_target_r": 2.10713737,
            "policy_target_r": 2.0,
            "target_r": 2.0,
        }
    )
    assert below_all["close_mark_clamped"] is False
    assert below_all["close_mark_clamp_semantics_status"] == "not_clamped"

    # The walker disables the ceiling on a falsy target; mirror it.
    no_target = semantics.normalize_evidence_row(
        {
            "terminal_outcome": "filled_time_stop_close_mark",
            "close_mark_r": 5.0,
            "target_r": 0.0,
        }
    )
    assert no_target["close_mark_clamped"] is False
    assert no_target["close_mark_clamp_semantics_status"] == (
        "not_clamped_no_target_bound"
    )

    # Non-mark closes carry no clamp vocabulary at all -- additive only.
    stop_row = semantics.normalize_evidence_row(
        {"terminal_outcome": "stop_reached_before_target"}
    )
    assert "close_mark_clamped" not in stop_row
    assert "close_mark_ambiguity_floor" not in stop_row


def test_exit_layer_fields_survive_the_missed_keep_set() -> None:
    new_fields = {
        "exit_raw_path_terminal",
        "exit_policy_overlay_close",
        "exit_layers_disagree",
        "close_mark_clamped",
        "close_mark_ambiguity_floor",
        "close_mark_clamp_semantics_status",
    }
    assert new_fields <= semantics.SEMANTIC_FIELDS
    assert new_fields <= cuts._missed_keep_names()

    projected = cuts.project_missed_pool_row(
        {
            "candidate_id": "candidate-a",
            "decision_time_utc": "2026-01-02T08:00:00+00:00",
            "terminal_outcome": "time_stop_close_mark_from_m1",
            "opportunity_close_reason": "time_stop_close_mark_from_m1",
            "counterfactual_order_close_mark_r": 0.50216061,
            "raw_target_r": 2.0,
            "policy_target_r": 2.0,
        }
    )
    assert projected["exit_raw_path_terminal"] == "time_stop_close_mark_from_m1"
    assert projected["exit_layers_disagree"] is False
    assert projected["close_mark_clamped"] is False
    assert projected["close_mark_clamp_semantics_status"] == "not_clamped"
