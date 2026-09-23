from __future__ import annotations

import copy

import pytest

from src.research_infra.train_engine import cuts
from src.research_infra.train_engine import decision_semantics as semantics
from src.research_infra.train_engine import repairs


TRUSTED_COMMISSION_SOURCE = (
    "broker_true_BROKER_TRUE_COSTS_V1_round_turn_over_stop_distance"
)


def _capture_evidence(
    *,
    spread_r: object = 0.10,
    expected_slippage_r: object = 0.02,
    swap_cost_r: object = 0.03,
    commission_r: object = 0.05,
) -> dict[str, dict[str, object]]:
    return {
        "spread_r": {
            "value": spread_r,
            "source": "historical_ftmo_predecision_tick",
            "source_status": "captured",
        },
        "expected_slippage_r": {
            "value": expected_slippage_r,
            "source": "config.selected_cell_default_expected_slippage_r",
            "source_status": "captured",
        },
        "swap_cost_r": {
            "value": swap_cost_r,
            "source": "points_mode_time_stop_swap_cost_r_v1",
            "source_status": "captured",
        },
        "commission_r": {
            "value": commission_r,
            "source": TRUSTED_COMMISSION_SOURCE,
            "source_status": "captured",
            "included_in_total_cost_r": True,
        },
    }


def _flat_row(*, recorded: bool = True, **updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "spread_r": 0.10,
        "expected_slippage_r": 0.02,
        "swap_cost_r": 0.03,
        "commission_r": 0.05,
        "cost_component_capture_evidence": _capture_evidence(),
        "cost_quote_source": "historical_ftmo_predecision_tick",
        "expected_slippage_source": (
            "config.selected_cell_default_expected_slippage_r"
        ),
        "commission_r_broker_true_measured": 0.05,
        "commission_r_repair_status": "applied",
        "commission_r_repair_total_redecode_status": "complete_component_sum",
        "commission_r_source": TRUSTED_COMMISSION_SOURCE,
    }
    if recorded:
        row["cost_r"] = 0.20
    row.update(updates)
    return row


def _packet() -> dict[str, object]:
    return {
        "status": "PASSED",
        "model_version": "vnext_selected_cell_pretrade_cost_model_v3",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "quote_authority": {
            "quote_source": "historical_ftmo_predecision_tick",
            "historical_tick_time_utc": "2026-02-02T00:14:59+00:00",
        },
        "tick_cost": {
            "spread_r": 0.10,
            "source_status": "captured",
        },
        "spread_r": 0.10,
        "expected_slippage_r": 0.02,
        "expected_slippage_source": (
            "config.selected_cell_default_expected_slippage_r"
        ),
        "swap_cost": {
            "model_version": "points_mode_time_stop_swap_cost_r_v1",
            "source_status": "captured",
            "cost_r": 0.03,
            "favorable_swap_credit_applied": False,
        },
        "commission_r": 0.05,
        "commission_r_broker_true_measured": 0.05,
        "commission_r_repair_status": "applied",
        "commission_r_repair_total_redecode_status": "complete_component_sum",
        "commission_r_source": TRUSTED_COMMISSION_SOURCE,
        "commission_cost": {
            "model_version": "broker_true_commission_cash_to_r_v1",
            "source_status": "captured",
            "cost_r": 0.05,
            "broker_true_measured_cost_r": 0.05,
            "included_in_total_cost_r": True,
            "repair_source": TRUSTED_COMMISSION_SOURCE,
            "artifact": "BROKER_TRUE_COSTS_V1.json",
        },
        "total_cost_r": 0.20,
        "total_cost_components": {
            "spread_r": 0.10,
            "expected_slippage_r": 0.02,
            "swap_cost_r": 0.03,
            "commission_r": 0.05,
        },
        "refusal_reasons": [],
        "config_requirements": {"packet_required": True},
    }


def _nested_row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "cost_r": 0.20,
        "pretrade_broker_net_cost_packet": _packet(),
    }
    row.update(updates)
    return row


def _assert_not_authoritative(
    row: dict[str, object], state: str, reason: str | None = None
) -> None:
    assert row["cost_component_state"] == state
    assert row["authoritative_cost_r"] is None
    if reason is not None:
        assert reason in row["cost_decision_refusal_reasons"]


@pytest.mark.parametrize("field", semantics.COST_COMPONENT_FIELDS)
@pytest.mark.parametrize(
    "bad",
    [True, False, "0", "0.1", " 0.1 "],
    ids=["true", "false", "zero-string", "numeric-string", "padded-string"],
)
def test_bool_and_numeric_strings_never_create_component_authority(
    field: str,
    bad: object,
) -> None:
    row = _flat_row(recorded=False)
    row[field] = bad
    row["cost_component_capture_evidence"][field]["value"] = bad  # type: ignore[index]

    normalized = semantics.normalize_evidence_row(row)

    _assert_not_authoritative(normalized, "incomplete", f"invalid_component:{field}")


@pytest.mark.parametrize("field", semantics.COST_COMPONENT_FIELDS)
@pytest.mark.parametrize("blank", [None, "", "   "], ids=["none", "empty", "whitespace"])
def test_null_and_blank_components_stay_incomplete(
    field: str,
    blank: object,
) -> None:
    row = _flat_row(recorded=False)
    row[field] = blank
    row["cost_component_capture_evidence"][field]["value"] = blank  # type: ignore[index]

    normalized = semantics.normalize_evidence_row(row)

    _assert_not_authoritative(normalized, "incomplete", f"null_component:{field}")


@pytest.mark.parametrize("field", semantics.COST_COMPONENT_FIELDS)
@pytest.mark.parametrize(
    "bad",
    [float("nan"), float("inf"), float("-inf")],
    ids=["nan", "positive-infinity", "negative-infinity"],
)
def test_all_non_finite_components_stay_incomplete(
    field: str,
    bad: float,
) -> None:
    row = _flat_row(recorded=False)
    row[field] = bad
    row["cost_component_capture_evidence"][field]["value"] = bad  # type: ignore[index]

    normalized = semantics.normalize_evidence_row(row)

    _assert_not_authoritative(
        normalized, "incomplete", f"non_finite_component:{field}"
    )


@pytest.mark.parametrize("field", semantics.COST_COMPONENT_FIELDS)
@pytest.mark.parametrize("bad", [[], {}, [0.1]], ids=["list", "map", "list-scalar"])
def test_non_scalar_components_stay_incomplete(field: str, bad: object) -> None:
    row = _flat_row(recorded=False)
    row[field] = bad
    row["cost_component_capture_evidence"][field]["value"] = bad  # type: ignore[index]

    normalized = semantics.normalize_evidence_row(row)

    _assert_not_authoritative(normalized, "incomplete", f"invalid_component:{field}")


@pytest.mark.parametrize("field", semantics.COST_COMPONENT_FIELDS)
def test_negative_cost_components_are_domain_invalid(field: str) -> None:
    row = _flat_row(recorded=False)
    row[field] = -0.01
    row["cost_component_capture_evidence"][field]["value"] = -0.01  # type: ignore[index]

    normalized = semantics.normalize_evidence_row(row)

    _assert_not_authoritative(
        normalized, "incomplete", f"negative_component:{field}"
    )


@pytest.mark.parametrize(
    "bad",
    [True, False, "0.05", " 0.05 ", -0.05],
    ids=["true", "false", "numeric-string", "padded-string", "negative"],
)
def test_invalid_measured_commission_cannot_bind_matching_component(
    bad: object,
) -> None:
    row = _flat_row(recorded=False, commission_r=bad)
    row["commission_r_broker_true_measured"] = bad
    row["cost_component_capture_evidence"]["commission_r"]["value"] = bad  # type: ignore[index]

    normalized = semantics.normalize_evidence_row(row)

    _assert_not_authoritative(normalized, "incomplete")


@pytest.mark.parametrize("field", semantics.COST_COMPONENT_FIELDS)
def test_every_component_requires_independent_capture_evidence(field: str) -> None:
    row = _flat_row()
    del row["cost_component_capture_evidence"][field]  # type: ignore[index]

    normalized = semantics.normalize_evidence_row(row)

    _assert_not_authoritative(
        normalized,
        "incomplete",
        f"missing_authority:{field}_capture_authority",
    )


def test_stale_applied_label_without_capture_evidence_is_not_authority() -> None:
    row = _flat_row()
    del row["cost_component_capture_evidence"]

    normalized = semantics.normalize_evidence_row(row)

    _assert_not_authoritative(normalized, "incomplete")


def test_legitimate_captured_zeroes_remain_authoritative() -> None:
    row = _flat_row(
        cost_r=0.10,
        expected_slippage_r=0.0,
        swap_cost_r=0.0,
        commission_r=0.0,
        commission_r_broker_true_measured=0.0,
        cost_component_capture_evidence=_capture_evidence(
            expected_slippage_r=0.0,
            swap_cost_r=0.0,
            commission_r=0.0,
        ),
    )

    normalized = semantics.normalize_evidence_row(row)

    assert normalized["cost_component_state"] == "complete"
    assert normalized["cost_component_sum_r"] == 0.10
    assert normalized["authoritative_cost_r"] == 0.10


def test_nested_packet_with_all_source_evidence_is_authoritative() -> None:
    normalized = semantics.normalize_evidence_row(_nested_row())

    assert normalized["cost_component_state"] == "complete"
    assert normalized["authoritative_cost_r"] == 0.20
    assert set(normalized["cost_component_capture_evidence"]) == set(
        semantics.COST_COMPONENT_FIELDS
    )


@pytest.mark.parametrize(
    ("packet_path", "replacement"),
    [
        (("tick_cost",), {"spread_r": 0.10, "source_status": "source_gap"}),
        (("expected_slippage_source",), None),
        (
            ("swap_cost",),
            {
                "model_version": "points_mode_time_stop_swap_cost_r_v1",
                "source_status": "source_gap",
                "cost_r": 0.03,
            },
        ),
        (("commission_cost",), {"source_status": "source_gap", "cost_r": 0.05}),
    ],
    ids=["spread", "slippage", "swap", "commission"],
)
def test_nested_totals_do_not_replace_missing_component_authority(
    packet_path: tuple[str, ...],
    replacement: object,
) -> None:
    packet = _packet()
    packet[packet_path[0]] = replacement

    normalized = semantics.normalize_evidence_row(
        {"cost_r": 0.20, "pretrade_broker_net_cost_packet": packet}
    )

    _assert_not_authoritative(normalized, "incomplete")


def test_top_level_and_nested_component_conflict_refuses_both() -> None:
    normalized = semantics.normalize_evidence_row(
        _nested_row(spread_r=0.20, cost_r=0.30)
    )

    _assert_not_authoritative(
        normalized,
        "refused",
        "inconsistent_component:spread_r_top_level_vs_packet",
    )


def test_flat_component_and_capture_value_conflict_refuses_both() -> None:
    row = _flat_row(spread_r=0.11, cost_r=0.21)

    normalized = semantics.normalize_evidence_row(row)

    _assert_not_authoritative(
        normalized,
        "refused",
        "inconsistent_component:spread_r_vs_capture_evidence",
    )


def test_top_level_and_nested_measured_commission_conflict_refuses() -> None:
    normalized = semantics.normalize_evidence_row(
        _nested_row(
            commission_r_broker_true_measured=0.05,
            commission_r=0.05,
        )
    )
    packet = _packet()
    packet["commission_r_broker_true_measured"] = 0.04
    packet["commission_cost"]["broker_true_measured_cost_r"] = 0.04  # type: ignore[index]
    conflicted = semantics.normalize_evidence_row(
        {
            "cost_r": 0.20,
            "commission_r_broker_true_measured": 0.05,
            "pretrade_broker_net_cost_packet": packet,
        }
    )

    assert normalized["cost_component_state"] == "complete"
    _assert_not_authoritative(conflicted, "refused")


@pytest.mark.parametrize(
    ("field", "malformed"),
    [
        ("total_cost_components", "not-a-map"),
        ("tick_cost", [0.10]),
        ("swap_cost", [0.03]),
        ("commission_cost", [0.05]),
    ],
)
def test_malformed_nested_maps_fail_closed_without_top_level_rescue(
    field: str,
    malformed: object,
) -> None:
    packet = _packet()
    packet[field] = malformed
    row = _flat_row(pretrade_broker_net_cost_packet=packet)

    normalized = semantics.normalize_evidence_row(row)

    assert normalized["cost_component_state"] != "complete"
    assert normalized["authoritative_cost_r"] is None


def test_malformed_packet_container_cannot_fall_back_to_flat_authority() -> None:
    normalized = semantics.normalize_evidence_row(
        _flat_row(pretrade_broker_net_cost_packet="not-a-map")
    )

    _assert_not_authoritative(
        normalized,
        "refused",
        "inconsistent_component:cost_packet_container_invalid",
    )


def test_conflicting_packet_aliases_refuse_instead_of_selecting_first() -> None:
    first = _packet()
    second = copy.deepcopy(first)
    second["total_cost_components"]["spread_r"] = 0.11  # type: ignore[index]
    normalized = semantics.normalize_evidence_row(
        {
            "cost_r": 0.20,
            "pretrade_broker_net_cost_packet": first,
            "pretrade_cost_packet": second,
        }
    )

    _assert_not_authoritative(
        normalized,
        "refused",
        "inconsistent_component:conflicting_cost_packet_aliases",
    )


def test_conflicting_recorded_total_aliases_refuse() -> None:
    normalized = semantics.normalize_evidence_row(
        _flat_row(cost_r=0.20, expected_cost_r=0.21)
    )

    _assert_not_authoritative(
        normalized,
        "refused",
        "inconsistent_component:cost_r_vs_expected_cost_r",
    )


@pytest.mark.parametrize(
    "bad",
    [True, False, "0.20", " 0.20 ", float("nan"), float("inf"), float("-inf"), -0.20],
    ids=[
        "true",
        "false",
        "numeric-string",
        "padded-string",
        "nan",
        "positive-infinity",
        "negative-infinity",
        "negative",
    ],
)
def test_invalid_recorded_total_never_falls_through_to_component_sum(
    bad: object,
) -> None:
    normalized = semantics.normalize_evidence_row(_flat_row(cost_r=bad))

    _assert_not_authoritative(normalized, "refused")


def test_unnamed_point_twelve_mismatch_is_not_a_legacy_fallback() -> None:
    normalized = semantics.normalize_evidence_row(
        _flat_row(
            cost_r=0.12,
            spread_r=0.10,
            expected_slippage_r=0.02,
            swap_cost_r=0.03,
            commission_r=0.0,
            commission_r_broker_true_measured=0.0,
            broker_pretrade_cost_executable=False,
            cost_component_capture_evidence=_capture_evidence(commission_r=0.0),
        )
    )

    _assert_not_authoritative(normalized, "refused")
    assert "legacy_emitter_fallback_cost_r" not in normalized


def test_named_point_twelve_fallback_requires_current_capture_binding() -> None:
    row = _flat_row(
        cost_r=0.12,
        spread_r=0.10,
        expected_slippage_r=0.02,
        swap_cost_r=0.03,
        commission_r=0.0,
        commission_r_broker_true_measured=0.0,
        miss_reason="scheduler_cost_missing",
        cost_component_capture_evidence=_capture_evidence(commission_r=0.0),
    )
    del row["commission_r_source"]
    del row["commission_r_repair_total_redecode_status"]
    row["commission_r_repair_status"] = "applied"

    normalized = semantics.normalize_evidence_row(row)

    assert normalized["legacy_emitter_fallback_cost_r"] == 0.12
    _assert_not_authoritative(normalized, "incomplete")


def test_explicit_repaired_fallback_redecodes_in_historical_order() -> None:
    row = _flat_row(
        cost_r=0.12,
        spread_r=0.335891148,
        expected_slippage_r=0.02,
        swap_cost_r=0.002783978,
        commission_r=0.0,
        commission_r_broker_true_measured=0.0,
        legacy_emitter_fallback_cost_r=0.12,
        legacy_emitter_fallback_replaced=True,
        cost_component_capture_evidence=_capture_evidence(
            spread_r=0.335891148,
            expected_slippage_r=0.02,
            swap_cost_r=0.002783978,
            commission_r=0.0,
        ),
    )

    normalized = semantics.normalize_evidence_row(row)

    expected = 0.335891148 + 0.02 + 0.002783978 + 0.0
    assert normalized["cost_component_sum_r"] == expected
    assert normalized["authoritative_cost_r"] == expected
    assert normalized["cost_accounting_status"] == (
        "legacy_fallback_replaced_by_complete_component_sum"
    )


def test_valid_geometry_rebase_binds_original_and_effective_costs() -> None:
    normalized = semantics.normalize_evidence_row(
        _flat_row(
            cost_r=0.30,
            marketable_limit_cost_r_rebased_to_effective_fill_geometry=True,
            marketable_limit_original_expected_cost_r=0.20,
            marketable_limit_effective_expected_cost_r=0.30,
            limit_immediate_marketable_cost_r_rebase_multiplier=1.5,
        )
    )

    assert normalized["cost_component_state"] == "complete"
    assert normalized["authoritative_cost_r"] == 0.30
    assert normalized["cost_accounting_status"] == (
        "component_sum_plus_explicit_geometry_rebase"
    )


@pytest.mark.parametrize(
    "updates",
    [
        {"marketable_limit_cost_r_rebased_to_effective_fill_geometry": True},
        {"marketable_limit_cost_r_rebased_to_effective_fill_geometry": "true"},
        {"marketable_limit_effective_expected_cost_r": 0.30},
        {
            "marketable_limit_cost_r_rebased_to_effective_fill_geometry": True,
            "marketable_limit_original_expected_cost_r": 0.20,
            "marketable_limit_effective_expected_cost_r": "0.30",
        },
        {
            "marketable_limit_cost_r_rebased_to_effective_fill_geometry": True,
            "marketable_limit_original_expected_cost_r": 0.21,
            "marketable_limit_effective_expected_cost_r": 0.30,
        },
        {
            "marketable_limit_cost_r_rebased_to_effective_fill_geometry": True,
            "marketable_limit_original_expected_cost_r": 0.20,
            "marketable_limit_effective_expected_cost_r": 0.29,
        },
        {
            "marketable_limit_cost_r_rebased_to_effective_fill_geometry": True,
            "marketable_limit_original_expected_cost_r": 0.20,
            "marketable_limit_effective_expected_cost_r": 0.30,
            "limit_immediate_marketable_cost_r_rebase_multiplier": False,
        },
        {
            "marketable_limit_cost_r_rebased_to_effective_fill_geometry": True,
            "marketable_limit_original_expected_cost_r": 0.20,
            "marketable_limit_effective_expected_cost_r": 0.30,
            "limit_immediate_marketable_cost_r_rebase_multiplier": 1.4,
        },
    ],
    ids=[
        "marker-only",
        "string-marker",
        "effective-only",
        "string-effective",
        "wrong-original",
        "wrong-effective",
        "bool-multiplier",
        "wrong-multiplier",
    ],
)
def test_incomplete_or_contradictory_rebase_evidence_refuses(
    updates: dict[str, object],
) -> None:
    normalized = semantics.normalize_evidence_row(_flat_row(cost_r=0.30, **updates))

    _assert_not_authoritative(normalized, "refused")


def test_component_and_total_tolerance_edges_are_fail_closed() -> None:
    inside = semantics.normalize_evidence_row(
        _flat_row(cost_r=0.20 + semantics.COST_COMPONENT_TOLERANCE_R / 2)
    )
    outside = semantics.normalize_evidence_row(
        _flat_row(cost_r=0.20 + semantics.COST_COMPONENT_TOLERANCE_R * 2)
    )
    commission_inside = semantics.normalize_evidence_row(
        _flat_row(
            commission_r_broker_true_measured=(
                0.05 + semantics.COST_COMPONENT_TOLERANCE_R / 2
            )
        )
    )
    commission_outside = semantics.normalize_evidence_row(
        _flat_row(
            commission_r_broker_true_measured=(
                0.05 + semantics.COST_COMPONENT_TOLERANCE_R * 2
            )
        )
    )

    assert inside["cost_component_state"] == "complete"
    assert outside["cost_component_state"] == "refused"
    assert commission_inside["cost_component_state"] == "complete"
    assert commission_outside["cost_component_state"] == "refused"


def test_nested_and_flattened_forms_are_deterministic_and_idempotent() -> None:
    once = semantics.normalize_evidence_row(_nested_row())
    twice = semantics.normalize_evidence_row(once)
    flattened = dict(once)
    flattened.pop("pretrade_broker_net_cost_packet")
    flattened_again = semantics.normalize_evidence_row(flattened)

    assert twice == once
    assert flattened_again["cost_component_state"] == "complete"
    assert flattened_again["authoritative_cost_r"] == 0.20
    assert flattened_again["cost_component_capture_evidence"] == once[
        "cost_component_capture_evidence"
    ]


def test_stale_v2_complete_fields_cannot_override_lost_capture() -> None:
    row = semantics.normalize_evidence_row(_flat_row())
    del row["cost_component_capture_evidence"]["swap_cost_r"]
    row.update(
        {
            "cost_component_state": "complete",
            "cost_component_sum_r": 0.20,
            "authoritative_cost_r": 0.20,
            "cost_component_invalid_fields": [],
            "cost_component_refusal_reasons": [],
            "cost_decision_authorization_status": (
                "authorized_complete_component_cost"
            ),
        }
    )

    normalized = semantics.normalize_evidence_row(row)

    _assert_not_authoritative(normalized, "incomplete")
    assert "cost_component_invalid_fields" not in normalized
    assert "cost_component_refusal_reasons" not in normalized


def test_downstream_projection_and_accessor_refuse_incomplete_capture() -> None:
    row = _flat_row()
    del row["cost_component_capture_evidence"]["spread_r"]

    projected = cuts.project_missed_pool_row(row)

    _assert_not_authoritative(projected, "incomplete")
    assert semantics.authoritative_cost_value(row) is None


@pytest.mark.parametrize(
    ("measured", "charge", "source"),
    [
        (True, True, TRUSTED_COMMISSION_SOURCE),
        ("0.05", "0.05", TRUSTED_COMMISSION_SOURCE),
        (-0.05, -0.05, TRUSTED_COMMISSION_SOURCE),
        (0.04, 0.05, TRUSTED_COMMISSION_SOURCE),
        (0.05, 0.05, "   "),
        (0.05, 0.05, "stale-test-label"),
    ],
    ids=[
        "bool",
        "numeric-string",
        "negative",
        "measured-charge-conflict",
        "blank-source",
        "untrusted-source",
    ],
)
def test_packet_commission_repair_rejects_invalid_or_untrusted_capture(
    measured: object,
    charge: object,
    source: str,
) -> None:
    packet = _packet()
    before_total = packet["total_cost_r"]

    repaired = repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=measured,  # type: ignore[arg-type]
        charge_r=charge,  # type: ignore[arg-type]
        source=source,
        regate=False,
    )

    assert repaired["commission_r_repair_status"].startswith("refused_")
    assert repaired["cost_component_state"] != "complete"
    assert repaired["total_cost_r"] == before_total


@pytest.mark.parametrize("malformed", [None, "bad", 1, [0.10]])
def test_packet_commission_repair_handles_malformed_component_map(
    malformed: object,
) -> None:
    packet = _packet()
    packet["total_cost_components"] = malformed

    repaired = repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=0.05,
        charge_r=0.05,
        source=TRUSTED_COMMISSION_SOURCE,
        regate=False,
    )

    assert repaired["cost_component_state"] == "incomplete"
    assert repaired["total_cost_r"] == 0.20


def test_packet_repair_refuses_unexplained_existing_total() -> None:
    packet = _packet()
    packet["total_cost_r"] = 0.19

    repaired = repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=0.05,
        charge_r=0.05,
        source=TRUSTED_COMMISSION_SOURCE,
        regate=False,
    )

    assert repaired["cost_component_state"] == "refused"
    assert repaired["total_cost_r"] == 0.19


def test_stale_fallback_field_cannot_waive_complete_component_conflict() -> None:
    packet = _packet()
    packet["total_cost_r"] = 0.12
    packet["total_cost_components"]["authority_fallback_total_cost_r"] = 0.12  # type: ignore[index]

    repaired = repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=0.05,
        charge_r=0.05,
        source=TRUSTED_COMMISSION_SOURCE,
        regate=False,
    )

    assert repaired["cost_component_state"] == "refused"
    assert repaired["total_cost_r"] == 0.12
    assert "legacy_emitter_fallback_replaced" not in repaired


def test_packet_repair_preserves_exact_order_and_legitimate_fallback() -> None:
    packet = _packet()
    packet["total_cost_r"] = 0.12
    packet["total_cost_components"] = {
        "spread_r": 0.335891148,
        "expected_slippage_r": 0.02,
        "swap_cost_r": 0.002783978,
        "commission_r": None,
        "authority_fallback_total_cost_r": 0.12,
    }
    packet["tick_cost"]["spread_r"] = 0.335891148  # type: ignore[index]
    packet["spread_r"] = 0.335891148
    packet["swap_cost"]["cost_r"] = 0.002783978  # type: ignore[index]
    packet["commission_cost"] = {
        "model_version": "broker_true_commission_cash_to_r_v1",
        "source_status": "source_gap",
        "cost_r": None,
        "missing_fields": ["broker_true_commission_schedule"],
    }

    repaired = repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=0.0,
        charge_r=0.0,
        source=TRUSTED_COMMISSION_SOURCE,
        regate=False,
    )

    expected = 0.335891148 + 0.02 + 0.002783978 + 0.0
    assert repaired["cost_component_state"] == "complete"
    assert repaired["total_cost_r"] == expected
    assert repaired["legacy_emitter_fallback_cost_r"] == 0.12
    assert repaired["legacy_emitter_fallback_replaced"] is True


def test_packet_repair_is_idempotent_after_complete_redecode() -> None:
    packet = _packet()
    packet["total_cost_r"] = 0.12
    packet["total_cost_components"]["commission_r"] = None  # type: ignore[index]
    packet["total_cost_components"]["authority_fallback_total_cost_r"] = 0.12  # type: ignore[index]
    packet["commission_cost"] = {
        "model_version": "broker_true_commission_cash_to_r_v1",
        "source_status": "source_gap",
        "cost_r": None,
    }
    packet["commission_r_repair_total_redecode_invalid_fields"] = ["stale"]

    repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=0.05,
        charge_r=0.05,
        source=TRUSTED_COMMISSION_SOURCE,
        regate=True,
    )
    once = copy.deepcopy(packet)
    assert "commission_r_repair_total_redecode_invalid_fields" not in once
    repairs._apply_broker_true_commission_capture(
        packet,
        measured_commission_r=0.05,
        charge_r=0.05,
        source=TRUSTED_COMMISSION_SOURCE,
        regate=True,
    )

    assert packet == once
