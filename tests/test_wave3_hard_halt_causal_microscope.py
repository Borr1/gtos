from src.research_infra.wave3_hard_halt_causal_microscope import (
    BOUNDARY_FIELDS,
    blocker_repair_boundary_ledger,
    broker_regression_fixtures,
    fixture_ledger,
    next_owner_prompt_requirement_ledger,
    non_generatable_truth_matrix,
    production_code_disposition_ledger,
)


def _sample_wave2():
    return {
        "trade_rows": [
            {
                "row_id": "trade:1",
                "broker_position_id": 101,
                "symbol": "XAUUSD",
                "side": "SELL",
                "time_window": {"entry": "2026-05-29T00:00:00+00:00"},
                "evidence_class": "broker-real PnL",
                "source_paths": ["broker_truth.json"],
                "causal_surface": ["broker_truth"],
                "metric_fields_used": {
                    "broker_real_pnl_cash": -10.0,
                    "exact_r": None,
                    "proxy_r": -1.0,
                    "failure_tags": ["loss"],
                },
                "missing_fields": ["exact_r"],
                "question_id": ["W2Q_COST_BROKER_NET"],
                "owning_wave3_lane": "hard_halt_causal_microscope_continuation",
            }
        ],
        "candidate_rows": [
            {
                "row_id": "candidate:1",
                "candidate_id": "C1",
                "symbol": "XAUUSD",
                "side": "SELL",
                "evidence_class": "source_bound_candidate_trade_record",
                "metric_fields_used": {"expectancy_r_source_bound": 0.1},
                "missing_fields": ["mfe_r"],
            }
        ],
        "question_rows": [{"question_id": "W2Q_COST_BROKER_NET", "status": "answered"}],
        "blocker_rows": [
            {
                "blocker_id": "B1",
                "source_path": "source.jsonl",
                "downstream_lane": "data_capture_source_repair_final",
                "missing_file_path_field_source": "runtime_intent",
                "owner_access_source_capture_requirement": "capture runtime intent prospectively",
                "evidence_class": "source_gap_or_prospective_capture_requirement",
                "status": "bounded",
            }
        ],
        "allocator_coverage_rows": [
            {
                "source_id": "runtime_decisions",
                "source_path": "runtime.jsonl",
                "remaining_non_generatable_truth": ["original_runtime_candidate_set_id"],
                "coverage_status": "no_exact_allocator_window_ids",
                "v4_requirement_id": "allocator_window_capture",
                "row_count": 12,
            }
        ],
        "path_coverage_rows": [],
        "sltp_rows": [
            {
                "row_id": "sltp:101",
                "broker_position_id": 101,
                "symbol": "XAUUSD",
                "coverage_status": "initial_sltp_present_full_modify_lifecycle_not_captured",
                "evidence_class": "broker_order_initial_sltp_source_coverage",
                "source_path": "orders.json",
                "first_order_ticket": 101,
                "first_order_sl": 4517.39,
                "first_order_tp": 4406.87,
                "unique_sltp_pair_count": 1,
                "non_generatable_or_missing_fields": ["every_sltp_modify_event"],
                "v4_requirement_id": "ticket_bound_sltp_modify_lifecycle_capture",
            }
        ],
        "cost_rows": [
            {
                "row_id": "cost:101",
                "broker_position_id": 101,
                "symbol": "XAUUSD",
                "coverage_status": "broker_deal_cost_truth_joined",
                "evidence_class": "broker_truth_deal_cost_plus_shadow_execution_slippage_join",
                "source_paths": ["deals.json"],
                "broker_deal_source_status": "broker_truth_deal_cost_joined",
                "broker_order_source_status": "broker_truth_orders_joined",
                "commission_swap_source_status": "broker_deal_truth_joined",
                "slippage_source_status": "shadow_slippage_source_gap",
                "pretrade_cost_model_status": "missing_original_runtime_packet",
                "missing_runtime_truth": ["original_pretrade_cost_model"],
                "broker_cost_fields": {"broker_net_cash_from_deals": -10.0},
                "owning_wave3_lane": "cost_swap_slippage_broker_constraint_engine",
                "v4_requirement_id": "runtime_cost_packet_capture",
            }
        ],
        "pending_nofill_summary": {"historical_source_gap_family_counts": {"original_runtime_intent": 3}},
        "production_disposition_rows": [
            {
                "component": "primary_analyzer_prompt_raw_geometry",
                "current_disposition": "legacy_raw_candidate_geometry_surface",
                "production_code_disposition": "research_only",
                "result_use_status": "production_component_disposition_for_v4_design_not_live_activation",
                "source_path": "src/prompts/primary_analyzer_prompt.py",
            }
        ],
    }


def test_fixture_ledger_preserves_broker_candidate_and_question_rows():
    rows = fixture_ledger(_sample_wave2())
    classes = [row["fixture_class"] for row in rows]
    assert classes == [
        "broker_position_regression",
        "candidate_or_live_authority_regression_reference",
        "causal_question_regression_reference",
    ]
    assert rows[0]["result_use_status"] == "regression_fixture_source_not_validation_result"


def test_broker_regression_fixture_carries_cost_lifecycle_and_ftmo_no_copy_assertion():
    rows = broker_regression_fixtures(_sample_wave2())
    assert len(rows) == 1
    fixture = rows[0]
    assert fixture["broker_position_id"] == 101
    assert "original_pretrade_cost_model" in fixture["v4_required_capture_fields"]
    assert "every_sltp_modify_event" in fixture["v4_required_capture_fields"]
    assert "must_not_copy_redacted_account_broker_truth_to_ftmo" in fixture["regression_assertions"]


def test_non_generatable_truth_matrix_turns_gaps_into_capture_requirements():
    rows = non_generatable_truth_matrix(_sample_wave2())
    missing = {row["missing_truth"] for row in rows}
    assert "runtime_intent" in missing
    assert "original_runtime_candidate_set_id" in missing
    assert "every_sltp_modify_event" in missing
    assert "original_pretrade_cost_model" in missing
    assert all(
        row["historical_reconstruction_policy"]
        == "do_not_infer_non_generatable_runtime_truth_from_price_path"
        for row in rows
    )


def test_production_code_disposition_preserves_broker_runtime_boundary():
    rows = production_code_disposition_ledger(_sample_wave2())
    assert any(row["component"] == "same_symbol_vnext_lifecycle_conflict_gate" for row in rows)
    assert all(row.get("broker_runtime_change_status") is False for row in rows)
    assert BOUNDARY_FIELDS["broker_runtime_change_status"] is False


def test_blocker_and_next_owner_prompt_ledgers_are_explicit_boundaries():
    capture_rows = non_generatable_truth_matrix(_sample_wave2())
    blocker_rows = blocker_repair_boundary_ledger(capture_rows)
    assert len(blocker_rows) == len(capture_rows)
    assert all(row["status"] == "exactly_bounded" for row in blocker_rows)

    semantic_rows = [
        {
            "owner_lane": "same_symbol_same_instrument_lifecycle_v4",
            "source_path": "contract.json",
        }
    ]
    prompt_rows = next_owner_prompt_requirement_ledger(semantic_rows)
    assert prompt_rows[0]["must_preserve_no_copy_rule"] is True
    assert prompt_rows[0]["must_preserve_boundary_fields"]["broker_runtime_change_status"] is False
