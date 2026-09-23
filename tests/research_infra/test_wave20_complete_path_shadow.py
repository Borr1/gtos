from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest


REPO = Path(__file__).resolve().parents[2]
ADAPTER_PATH = REPO / "src/research_infra/wave20_complete_path_shadow.py"
DECISION_US = 1_000_000_000
MINUTE_US = 60_000_000


@pytest.fixture(scope="module")
def adapter() -> ModuleType:
    spec = importlib.util.spec_from_file_location("wave20_complete_path_shadow_under_test", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _permission_inputs() -> dict:
    return {
        "session_state": {
            "asof_utc": "2026-01-02T13:15:00Z",
            "session_open": True,
            "daily_loss_blocked": False,
        },
        "account_headroom": {
            "snapshot_status": "VALID",
            "daily_headroom_pct": 2.0,
            "overall_headroom_pct": 4.0,
        },
        "symbol_state": {
            "symbol": "XAUUSD",
            "trade_mode": "ENABLED",
            "position_conflict": False,
        },
        "mt5_interface_response": {
            "interface_status": "INERT_OK",
            "symbol_visible": True,
        },
    }


def _candidate(candidate_id: str = "broadorigin_original") -> dict:
    return {
        "candidate_id": candidate_id,
        "origin_family": "current_breaker_re_entry",
        "symbol": "XAUUSD",
        "side": "LONG",
        "direction": "LONG",
        "decision_time_utc": "2026-01-02T13:15:00Z",
        "entry_price": 100.0,
        "stop_loss": 98.0,
        "take_profit_1": 103.0,
        "risk_reward_ratio": 1.5,
        "predecision_features": {
            "stop_distance_atr": 2.0,
            "target_distance_atr": 3.0,
        },
        "source_fields": {"uses_outcome_fields": False},
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 98.0,
            "take_profit_1": 103.0,
            "risk_reward_ratio": 1.5,
        },
    }


def _account_snapshot(account_scope: str) -> dict:
    return {
        "account_scope": account_scope,
        "profile_id": account_scope,
        "profile_snapshot_sha256": "a" * 64,
        "symbol_snapshot_sha256": "b" * 64,
        "broker_symbol": "XAUUSD",
        "deviation_points": 12,
        "magic": 20260725,
        "comment": "P1_SYNTHETIC",
        "filling_mode": "ORDER_FILLING_IOC",
    }


def _capture_evidence(
    *,
    spread_r: object = 0.10,
    expected_slippage_r: object = 0.02,
    swap_cost_r: object = 0.03,
    commission_r: object = 0.05,
) -> dict:
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
            "source": "broker_true_BROKER_TRUE_COSTS_V1_round_turn_over_stop_distance",
            "source_status": "captured",
            "included_in_total_cost_r": True,
        },
    }


def _complete_cost_row() -> dict:
    return {
        "spread_r": 0.10,
        "expected_slippage_r": 0.02,
        "swap_cost_r": 0.03,
        "commission_r": 0.05,
        "cost_r": 0.20,
        "cost_component_capture_evidence": _capture_evidence(),
        "cost_quote_source": "historical_ftmo_predecision_tick",
        "expected_slippage_source": "config.selected_cell_default_expected_slippage_r",
        "commission_r_broker_true_measured": 0.05,
        "commission_r_repair_status": "applied",
        "commission_r_repair_total_redecode_status": "complete_component_sum",
        "commission_r_source": (
            "broker_true_BROKER_TRUE_COSTS_V1_round_turn_over_stop_distance"
        ),
    }


def _hdf_input() -> dict:
    return {
        "cell": {"id": "V00", "kind": "identity"},
        "decision_time_us": DECISION_US,
        "cost_r": 999.0,
        "source_mode": "SYNTHETIC_TICK",
        "points": [
            {
                "time_us": DECISION_US + MINUTE_US,
                "signed_r": 0.4,
                "deadline_eligible": True,
                "source_index": 1,
            },
            {
                "time_us": DECISION_US + 2 * MINUTE_US,
                "signed_r": 1.2,
                "deadline_eligible": True,
                "source_index": 2,
            },
            {
                "time_us": DECISION_US + 3 * MINUTE_US,
                "signed_r": 0.7,
                "deadline_eligible": True,
                "source_index": 3,
            },
        ],
    }


def _source(
    *,
    source_id: str = "src-1",
    account_scope: str = "operator_profile",
    order_kind: str = "market",
    fill_status: str = "FILLED",
) -> dict:
    candidate_id = f"candidate-{source_id}"
    return {
        "source_window_id": "january_2026",
        "source_opportunity_id": source_id,
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-01-02T13:15:00Z",
        "account_scope": account_scope,
        "synthetic_candidate": _candidate(candidate_id),
        "permission_inputs": _permission_inputs(),
        "order_kind": order_kind,
        "account_snapshot": _account_snapshot(account_scope),
        "synthetic_fill": {
            "status": fill_status,
            "reason": "synthetic_known_answer_fill" if fill_status == "FILLED" else "synthetic_known_answer_no_touch",
        },
        "hde_cost_input": _complete_cost_row(),
        "hdf_exit_input": _hdf_input(),
    }


def _dependencies(adapter: ModuleType):
    return adapter.ShadowDependencies(
        generate_candidate=adapter.source_bound_candidate_generator,
        dynamic_router=adapter.inert_admit_unchanged_router,
        scheduler_capture=adapter.inert_scheduler_capture,
        fill_or_no_fill=adapter.source_bound_fill_projection,
    )


def test_default_off_does_not_iterate_or_call_dependencies(adapter: ModuleType) -> None:
    touched: list[str] = []

    def source_generator():
        touched.append("iterated")
        yield _source()

    result = adapter.run_complete_path_shadow(source_generator())

    assert result["status"] == "DEFAULT_OFF"
    assert result["stage_ledger"] == result["missed_opportunity_ledger"] == []
    assert result["execution_authority"] is False
    assert result["activation_authority"] is False
    assert result["result_bearing_science_executed"] is False
    assert touched == []


def test_static_import_and_broker_write_surface_are_refused(adapter: ModuleType) -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {
        "MetaTrader5",
        "src.mt5.mt5_real",
        "src.components.execution",
        "src.components.orchestrator",
    }
    forbidden_operation = "order" + "_send"

    assert imported.isdisjoint(forbidden)
    assert forbidden_operation not in source
    assert not any(
        isinstance(node, ast.Attribute) and node.attr == forbidden_operation
        for node in ast.walk(tree)
    )
    with pytest.raises(adapter.ShadowRefusal, match="forbidden_external_operation"):
        adapter.refuse_external_operation(forbidden_operation)


def test_fixed_b0_identity_and_geometry_are_unchanged(adapter: ModuleType) -> None:
    repaired = adapter.apply_current_breaker_re_entry_repair(_candidate(), enabled=True)

    assert adapter.FIXED_BREAKER_MEMBER == (
        "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"
    )
    assert adapter.FIXED_BREAKER_MEMBER_CANONICAL_SHA256 == (
        "0de66ebe5b67e7b3352d98624acb50c69ab116b1c46d58c422b887e5583a650f"
    )
    assert adapter.FIXED_BREAKER_MEMBER_RECORD["name"] == adapter.FIXED_BREAKER_MEMBER
    assert adapter.canonical_sha256(adapter.FIXED_BREAKER_MEMBER_RECORD) == (
        adapter.FIXED_BREAKER_MEMBER_CANONICAL_SHA256
    )
    assert repaired["side"] == repaired["direction"] == "SHORT"
    assert repaired["entry_price"] == 100.0
    assert repaired["stop_loss"] == pytest.approx(100.5)
    assert repaired["take_profit_1"] == pytest.approx(90.0)
    assert repaired["risk_reward_ratio"] == pytest.approx(20.0)
    assert repaired["candidate_transform_id"] == adapter.BREAKER_TRANSFORM_ID


def test_denominator_and_composite_identity_are_preserved(adapter: ModuleType) -> None:
    sources = [
        _source(source_id="ftmo", order_kind="market"),
        _source(
            source_id="redacted_account",
            account_scope="redacted_account",
            order_kind="limit",
            fill_status="NO_FILL",
        ),
    ]
    result = adapter.run_complete_path_shadow(
        sources,
        enabled=True,
        dependencies=_dependencies(adapter),
    )

    assert result["status"] == "COMPLETE_SYNTHETIC_NO_MISSES"
    assert result["source_opportunity_count"] == 2
    assert result["stage_row_count"] == 2 * len(adapter.STAGES) == 22
    assert result["missed_opportunity_ledger"] == []
    for source in sources:
        identity = {field: source[field] for field in adapter.IDENTITY_FIELDS}
        rows = [row for row in result["stage_ledger"] if row["composite_identity"] == identity]
        assert [row["stage"] for row in rows] == list(adapter.STAGES)
        assert len(rows) == len(adapter.STAGES)
        assert rows[-1]["reason"] == adapter.FROZEN_GATE_DISPOSITION


def test_first_exact_miss_is_ledgered_once_and_later_rows_do_not_disappear(
    adapter: ModuleType,
) -> None:
    source = _source()
    del source["permission_inputs"]["mt5_interface_response"]["symbol_visible"]
    result = adapter.run_complete_path_shadow(
        [source],
        enabled=True,
        dependencies=_dependencies(adapter),
    )

    expected = "permission_missing_required_field:mt5_interface_response.symbol_visible"
    assert result["status"] == "COMPLETE_SYNTHETIC_WITH_EXPLICIT_MISSES"
    assert result["stage_row_count"] == len(adapter.STAGES)
    assert result["missed_opportunity_ledger"] == [
        {
            **result["missed_opportunity_ledger"][0],
            "first_missing_stage": "permission",
            "reason": expected,
        }
    ]
    rows = {row["stage"]: row for row in result["stage_ledger"]}
    assert rows["permission"]["reason"] == expected
    assert rows["dynamic_router"]["disposition"] == "NOT_REACHED_PRIOR_STAGE_MISS"
    assert rows["unchanged_frozen_gate_disposition"]["disposition"] == "UNCHANGED"


def test_unbound_candidate_generator_fails_closed(adapter: ModuleType) -> None:
    source = _source()
    deps = _dependencies(adapter)
    deps = adapter.ShadowDependencies(
        generate_candidate=lambda row: [],
        dynamic_router=deps.dynamic_router,
        scheduler_capture=deps.scheduler_capture,
        fill_or_no_fill=deps.fill_or_no_fill,
    )

    result = adapter.run_complete_path_shadow([source], enabled=True, dependencies=deps)

    assert result["missed_opportunity_ledger"][0]["first_missing_stage"] == (
        "candidate_generation"
    )
    assert result["missed_opportunity_ledger"][0]["reason"] == (
        "candidate_generator_dependency_not_bound"
    )


def test_market_order_preimage_matches_reference_fields(adapter: ModuleType) -> None:
    result = adapter.project_order_preimage(
        _candidate(),
        order_kind="market",
        account_snapshot=_account_snapshot("operator_profile"),
        account_scope="operator_profile",
    )

    assert result["executable"] is False
    assert result["action"] == "TRADE_ACTION_DEAL"
    assert result["type"] == "ORDER_TYPE_BUY"
    assert (result["symbol"], result["price"], result["sl"], result["tp"]) == (
        "XAUUSD",
        100.0,
        98.0,
        103.0,
    )
    assert result["deviation"] == 12
    assert result["type_time"] == "ORDER_TIME_GTC"
    assert result["type_filling"] == "ORDER_FILLING_IOC"


def test_limit_preimage_is_an_internal_intent_not_a_broker_pending_order(
    adapter: ModuleType,
) -> None:
    result = adapter.project_order_preimage(
        _candidate(),
        order_kind="limit",
        account_snapshot=_account_snapshot("redacted_account"),
        account_scope="redacted_account",
    )

    assert result["executable"] is False
    assert result["action"] == "STORE_INTERNAL_PENDING_LIMIT_INTENT"
    assert result["direction"] == "LONG"
    assert (result["limit_price"], result["stop_loss"], result["take_profit_1"]) == (
        100.0,
        98.0,
        103.0,
    )
    assert result["pending_order_mode"] == "internal_software_limit"
    assert result["broker_pending_order_created"] is False
    assert result["native_pending_order_type"] is None


def test_permission_missing_field_fails_closed(adapter: ModuleType) -> None:
    inputs = _permission_inputs()
    del inputs["account_headroom"]["daily_headroom_pct"]

    result = adapter.evaluate_inert_permission(inputs)

    assert result["status"] == "REFUSED"
    assert result["reason"] == (
        "permission_missing_required_field:account_headroom.daily_headroom_pct"
    )


def test_permission_invalid_numeric_fails_closed(adapter: ModuleType) -> None:
    inputs = _permission_inputs()
    inputs["account_headroom"]["daily_headroom_pct"] = "2.0"

    result = adapter.evaluate_inert_permission(inputs)

    assert result["status"] == "REFUSED"
    assert result["reason"] == (
        "permission_invalid_numeric:account_headroom.daily_headroom_pct"
    )


def test_scheduler_is_capture_only_and_cannot_change_disposition(adapter: ModuleType) -> None:
    result = adapter.scheduler_capture_only(
        {
            "requested_disposition": "DROP",
            "selected_candidate_id": "other",
            "rank": 1,
            "risk_pct": 99,
        },
        incoming_disposition="ADMIT",
    )

    assert result["mode"] == "CAPTURE_ONLY"
    assert result["effect"] == "NONE"
    assert result["input_disposition"] == result["output_disposition"] == "ADMIT"
    assert result["selection_authority"] is False
    assert result["ranking_authority"] is False
    assert result["suppression_authority"] is False
    assert result["sizing_authority"] is False


def test_learned_probability_path_stops_as_k1_stale(adapter: ModuleType) -> None:
    source = _source()
    source["synthetic_candidate"]["candidate_probability"] = 0.9

    with pytest.raises(adapter.K1StaleRefusal, match="k1_learned_authority_forbidden"):
        adapter.run_complete_path_shadow(
            [source],
            enabled=True,
            dependencies=_dependencies(adapter),
        )


def test_learned_scheduler_path_stops_as_k1_stale(adapter: ModuleType) -> None:
    with pytest.raises(adapter.K1StaleRefusal, match="k1_learned_authority_forbidden"):
        adapter.scheduler_capture_only(
            {"learned_probability": 0.9}, incoming_disposition="ADMIT"
        )


def test_bound_router_preserves_candidate_geometry(adapter: ModuleType) -> None:
    candidate = _candidate()
    before = adapter.canonical_sha256(candidate)
    routed = adapter.inert_admit_unchanged_router(candidate, _source())

    assert routed["disposition"] == "ADMIT"
    assert adapter.canonical_sha256(routed["candidate"]) == before


def test_unbound_router_cannot_enter_geometry_path(adapter: ModuleType) -> None:
    source = _source()
    deps = _dependencies(adapter)

    def mutate(candidate, row):
        candidate["entry_price"] = float(candidate["entry_price"]) + 1.0
        return {
            "candidate": candidate,
            "disposition": "ADMIT",
            "reason": "malicious_geometry_change",
        }

    deps = adapter.ShadowDependencies(
        generate_candidate=deps.generate_candidate,
        dynamic_router=mutate,
        scheduler_capture=deps.scheduler_capture,
        fill_or_no_fill=deps.fill_or_no_fill,
    )
    result = adapter.run_complete_path_shadow([source], enabled=True, dependencies=deps)

    assert result["missed_opportunity_ledger"][0]["first_missing_stage"] == "dynamic_router"
    assert result["missed_opportunity_ledger"][0]["reason"] == "dynamic_router_dependency_not_bound"


def test_unbound_scheduler_and_fill_dependencies_fail_closed(adapter: ModuleType) -> None:
    source = _source()
    deps = _dependencies(adapter)
    unbound_scheduler = adapter.ShadowDependencies(
        generate_candidate=deps.generate_candidate,
        dynamic_router=deps.dynamic_router,
        scheduler_capture=lambda candidate, row: {},
        fill_or_no_fill=deps.fill_or_no_fill,
    )
    scheduler_result = adapter.run_complete_path_shadow(
        [source], enabled=True, dependencies=unbound_scheduler
    )
    assert scheduler_result["missed_opportunity_ledger"][0]["reason"] == (
        "scheduler_capture_dependency_not_bound"
    )

    unbound_fill = adapter.ShadowDependencies(
        generate_candidate=deps.generate_candidate,
        dynamic_router=deps.dynamic_router,
        scheduler_capture=deps.scheduler_capture,
        fill_or_no_fill=lambda preimage, row: row["synthetic_fill"],
    )
    fill_result = adapter.run_complete_path_shadow(
        [source], enabled=True, dependencies=unbound_fill
    )
    assert fill_result["missed_opportunity_ledger"][0]["reason"] == (
        "fill_projection_dependency_not_bound"
    )


def test_hde_complete_arithmetic_is_authoritative(adapter: ModuleType) -> None:
    result = adapter.project_hde_cost(_complete_cost_row())

    assert result["state"] == "complete"
    assert result["candidate_sum_r"] == pytest.approx(0.20)
    assert result["authoritative_cost_r"] == pytest.approx(0.20)
    assert result["tolerance_r"] == 1e-8


def test_hde_incomplete_arithmetic_is_not_authoritative(adapter: ModuleType) -> None:
    row = _complete_cost_row()
    del row["cost_component_capture_evidence"]["swap_cost_r"]

    result = adapter.project_hde_cost(row)

    assert result["state"] == "incomplete"
    assert result["authoritative_cost_r"] is None
    assert any("swap_cost_r" in reason for reason in result["refusal_reasons"])


def test_hde_contradictory_evidence_is_refused(adapter: ModuleType) -> None:
    row = _complete_cost_row()
    row["cost_component_capture_evidence"]["spread_r"]["value"] = 0.11

    result = adapter.project_hde_cost(row)

    assert result["state"] == "refused"
    assert result["authoritative_cost_r"] is None
    assert any("spread_r" in reason for reason in result["refusal_reasons"])


def test_hdf_deadline_collision_belongs_to_timebox(adapter: ModuleType) -> None:
    result = adapter.project_hdf_exit(
        {
            "cell": {"id": "TB", "kind": "time_box", "minutes": 30},
            "decision_time_us": DECISION_US,
            "cost_r": 0.0,
            "source_mode": "SYNTHETIC_TICK",
            "points": [
                {
                    "time_us": DECISION_US + 30 * MINUTE_US,
                    "signed_r": 2.0,
                    "deadline_eligible": True,
                    "source_index": 30,
                }
            ],
        }
    )

    assert result["exit_reason"] == "time_box"
    assert result["gross_r"] == pytest.approx(2.0)


def test_hdf_uses_first_deadline_eligible_observation(adapter: ModuleType) -> None:
    result = adapter.project_hdf_exit(
        {
            "cell": {"id": "TB", "kind": "time_box", "minutes": 30},
            "decision_time_us": DECISION_US,
            "cost_r": 0.0,
            "source_mode": "SYNTHETIC_TICK",
            "points": [
                {
                    "time_us": DECISION_US + 30 * MINUTE_US,
                    "signed_r": 0.4,
                    "deadline_eligible": False,
                    "source_index": 1,
                },
                {
                    "time_us": DECISION_US + 30 * MINUTE_US,
                    "signed_r": 0.3,
                    "deadline_eligible": True,
                    "source_index": 2,
                },
            ],
        }
    )

    assert result["exit_reason"] == "time_box"
    assert result["gross_r"] == pytest.approx(0.3)


def test_hdf_partial_uses_original_fraction_and_charges_cost_once(adapter: ModuleType) -> None:
    result = adapter.project_hdf_exit(
        {
            "cell": {
                "id": "PH",
                "kind": "partial_harvest",
                "trigger_r": 0.5,
                "fraction": 0.5,
            },
            "decision_time_us": DECISION_US,
            "cost_r": 0.2,
            "source_mode": "SYNTHETIC_TICK",
            "points": [
                {
                    "time_us": DECISION_US + MINUTE_US,
                    "signed_r": 0.6,
                    "deadline_eligible": True,
                    "source_index": 1,
                },
                {
                    "time_us": DECISION_US + 2 * MINUTE_US,
                    "signed_r": 2.1,
                    "deadline_eligible": True,
                    "source_index": 2,
                },
            ],
        }
    )

    assert result["partial_realized_r"] == pytest.approx(0.25)
    assert result["remaining_fraction"] == pytest.approx(0.5)
    assert result["gross_r"] == pytest.approx(1.25)
    assert result["net_r"] == pytest.approx(1.05)


def test_hdf_terminal_observation_closes_final_state(adapter: ModuleType) -> None:
    payload = _hdf_input()
    payload["points"] = [
        {
            "time_us": DECISION_US + MINUTE_US,
            "signed_r": 0.2,
            "deadline_eligible": True,
            "source_index": 1,
        },
        {
            "time_us": DECISION_US + 2 * MINUTE_US,
            "signed_r": 0.3,
            "deadline_eligible": True,
            "source_index": 2,
        },
    ]
    payload["cost_r"] = 0.1

    result = adapter.project_hdf_exit(payload)

    assert result["exit_reason"] == "horizon_terminal_mark"
    assert result["gross_r"] == pytest.approx(0.3)
    assert result["net_r"] == pytest.approx(0.2)


def test_hdf_m1_collision_selects_lower_net_ordering(adapter: ModuleType) -> None:
    result = adapter.project_hdf_m1_exit(
        {
            "cell": {"id": "TB", "kind": "time_box", "minutes": 30},
            "decision_time_us": DECISION_US,
            "cost_r": 0.0,
            "bars": [
                {
                    "time_us": DECISION_US + MINUTE_US,
                    "open_r": 0.0,
                    "high_r": 2.1,
                    "low_r": -1.1,
                    "close_r": 0.2,
                    "source_index": 0,
                }
            ],
        }
    )

    assert result["open_high_low_close"]["gross_r"] == pytest.approx(2.0)
    assert result["open_low_high_close"]["gross_r"] == pytest.approx(-1.0)
    assert result["selected"]["gross_r"] == pytest.approx(-1.0)
    assert result["outcomes_differ"] is True


def test_ftmo_is_future_economic_scope_and_redacted_account_is_mechanical_only(
    adapter: ModuleType,
) -> None:
    ftmo = adapter.account_claim_scope("operator_profile")
    redacted_account = adapter.account_claim_scope("redacted_account")

    assert ftmo["scope"] == "SOLE_FUTURE_ECONOMIC_SCOPE"
    assert ftmo["economic_verdict_emitted"] is False
    assert redacted_account["scope"] == "MECHANICAL_ONLY"
    assert redacted_account["economic_gate_allowed"] is False
    assert redacted_account["promotion_or_veto_allowed"] is False
    assert redacted_account["economic_verdict_emitted"] is False


def test_owner_risk_volume_is_never_defaulted(adapter: ModuleType) -> None:
    candidate = _candidate()
    candidate["volume"] = 99.0
    candidate["risk_per_trade_pct"] = 2.0

    result = adapter.project_order_preimage(
        candidate,
        order_kind="market",
        account_snapshot=_account_snapshot("operator_profile"),
        account_scope="operator_profile",
    )

    assert result["volume"] is None
    assert result["volume_status"] == "NOT_EVALUABLE_OWNER_INPUT_REQUIRED"


def test_injected_account_authority_requires_sha256_shape(adapter: ModuleType) -> None:
    snapshot = _account_snapshot("operator_profile")
    snapshot["profile_snapshot_sha256"] = "not-a-hash"

    result = adapter.project_order_preimage(
        _candidate(),
        order_kind="market",
        account_snapshot=snapshot,
        account_scope="operator_profile",
    )

    assert result["account_authority_status"] == (
        "NOT_EVALUABLE_INERT_SNAPSHOT_AUTHORITY_REQUIRED"
    )
    assert result["missing_account_authority"] == [
        "invalid_sha256:profile_snapshot_sha256"
    ]


def test_runner_refuses_non_admitted_window_before_dependency_call(adapter: ModuleType) -> None:
    source = _source()
    source["source_window_id"] = "march_2026"
    calls: list[str] = []
    deps = _dependencies(adapter)
    deps = adapter.ShadowDependencies(
        generate_candidate=lambda row: calls.append("generate") or [row["synthetic_candidate"]],
        dynamic_router=deps.dynamic_router,
        scheduler_capture=deps.scheduler_capture,
        fill_or_no_fill=deps.fill_or_no_fill,
    )

    with pytest.raises(adapter.ShadowRefusal, match="source_window_not_admitted:march_2026"):
        adapter.run_complete_path_shadow([source], enabled=True, dependencies=deps)
    assert calls == []


@pytest.mark.parametrize(
    ("path", "window_id", "purpose", "reason"),
    [
        (
            "february/result.json",
            "february_2026",
            "economic_selection",
            "february_economics_or_selection_forbidden",
        ),
        (
            "march/path.jsonl.gz",
            "march_2026",
            "metadata",
            "march_2026_read_forbidden",
        ),
        (
            "live-forward/outcome.jsonl",
            "live_forward",
            "metadata",
            "live_forward_read_forbidden",
        ),
        (
            "january/pool.jsonl.gz",
            "january_2026",
            "candidate_breadth",
            "candidate_breadth_forbidden",
        ),
        (
            "january/pool.jsonl.gz",
            "january_2026",
            "post_hoc_drop",
            "post_hoc_drop_forbidden",
        ),
    ],
)
def test_forbidden_scopes_refuse_before_reader_call(
    adapter: ModuleType,
    path: str,
    window_id: str,
    purpose: str,
    reason: str,
) -> None:
    calls: list[str] = []

    def reader(value: str):
        calls.append(value)
        return {"unexpected": True}

    with pytest.raises(adapter.ShadowRefusal, match=reason):
        adapter.guarded_source_read(
            path,
            window_id=window_id,
            purpose=purpose,
            reader=reader,
        )
    assert calls == []
