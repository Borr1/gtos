from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name("verify_vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26.py")
SPEC = importlib.util.spec_from_file_location("stage11_semantic_verifier", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verifier
SPEC.loader.exec_module(verifier)


DATE = "2026-05-26"


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _build_minimal_route(tmp_path: Path) -> Path:
    route = tmp_path
    _write_json(
        route / f"VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_{DATE}.json",
        {
            "row_level_evidence": {"router_replay_rows": 2},
            "router_replay_summary": {
                "decision_status_counts": {"refuse_live_use_until_source_or_scope_repaired": 1}
            },
        },
    )
    _write_json(
        route / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_{DATE}.json",
        {
            "stage_id": "STAGE_11_SEMANTIC_VERIFIER_HARDENING",
            "row_replay_rows": 2,
            "refusal_repair_split_rows": 1,
            "condition_challenge_rows": 2,
            "prop_aware_comparison_rows": 2,
            "forbidden_boundaries_crossed": False,
            "no_live_trading_or_broker_mutation": True,
            "no_paid_api_or_vendor_call": True,
            "prop_aware_terminal_decision": {
                "prop_default_retained": True,
                "terminal_classification": (
                    "condition_router_beats_global_row_expectancy_but_is_rejected_as_primary_prop_default_from_local_prop_replay"
                ),
            },
        },
    )
    _write_json(
        route / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE}.json",
        {
            "first_incomplete_invariant": "STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION",
            "completion_gate_status": "not_complete_first_incomplete_stage12",
        },
    )
    _write_jsonl(
        route / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_ROW_REPLAY_LEDGER_{DATE}.jsonl",
        [
            {
                "schema_version": "vnext_moonshot_stage11_condition_router_row_replay_v1",
                "framework": "fvg_fill",
                "condition_selected_policy": "trailing_runner",
                "condition_selected_policy_final_r": 2.0,
                "global_be_after_trigger_final_r": 1.0,
                "live_current_j46_j49_final_r": -1.0,
                "fixed_1_5r_final_r": 0.5,
                "selector_uses_only_asof_feature_columns": True,
                "selector_excludes_expost_same_bar_outcome": True,
            },
            {
                "schema_version": "vnext_moonshot_stage11_condition_router_row_replay_v1",
                "framework": "fvg_fill",
                "condition_selected_policy": "be_after_trigger",
                "condition_selected_policy_final_r": 1.2,
                "global_be_after_trigger_final_r": 1.1,
                "live_current_j46_j49_final_r": 0.0,
                "fixed_1_5r_final_r": 0.7,
                "selector_uses_only_asof_feature_columns": True,
                "selector_excludes_expost_same_bar_outcome": True,
            },
        ],
    )
    _write_jsonl(
        route / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_CHALLENGE_LEDGER_{DATE}.jsonl",
        [
            {"row_type": "full_row_asof_condition_router_all_candidates"},
            {
                "row_type": "chrono_oof_condition_router_challenge",
                "row_count": 2,
                "condition_vs_global_be_delta_r": 0.5,
                "selector_excludes_expost_same_bar_outcome": True,
            },
        ],
    )
    _write_jsonl(
        route / f"VNEXT_MOONSHOT_STAGE11_REFUSAL_REPAIR_SPLIT_LEDGER_{DATE}.jsonl",
        [
            {
                "terminal_repair_class": "activation_excluded_secondary_branch_pending_prop_default_not_source_repair",
                "repair_class_tags": [
                    "activation_excluded_secondary_branch_scope",
                    "ordered_ltf_or_tick_required",
                    "forward_capture_required",
                ],
                "locally_repairable_now": False,
            }
        ],
    )
    _write_jsonl(
        route / f"VNEXT_MOONSHOT_STAGE11_PROP_AWARE_ROUTER_COMPARISON_{DATE}.jsonl",
        [
            {
                "policy_name": "be_after_trigger_prop_pass_default",
                "reference_ev_per_terminal_day_usd_fee599_payout8000": 10.0,
                "allowed_trades": 20,
            },
            {
                "policy_name": "condition_asof_displacement_v1_account_restart",
                "reference_ev_per_terminal_day_usd_fee599_payout8000": 8.0,
                "allowed_trades": 10,
            },
        ],
    )
    _write_jsonl(
        route / f"VNEXT_MOONSHOT_ROUTE_CONTROL_NUDGE_LEDGER_{DATE}.jsonl",
        [
            {
                "steer_id": "stage11_semantic_verifier_hardening_active_challenge_steer_2026_05_26",
                "classification": "applied_now",
            }
        ],
    )
    return route


def test_semantic_verifier_accepts_minimal_contract(tmp_path: Path) -> None:
    route = _build_minimal_route(tmp_path)

    result = verifier.verify_semantic_contract(route_dir=route, repo_root=tmp_path, write_result=False, check_config=False)

    assert result["ok"] is True
    assert result["condition_vs_global_be_delta_r"] > 0


def test_semantic_verifier_rejects_missing_oof_challenge(tmp_path: Path) -> None:
    route = _build_minimal_route(tmp_path)
    _write_jsonl(
        route / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_CHALLENGE_LEDGER_{DATE}.jsonl",
        [{"row_type": "full_row_asof_condition_router_all_candidates"}],
    )
    stage11 = json.loads((route / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_{DATE}.json").read_text())
    stage11["condition_challenge_rows"] = 1
    _write_json(route / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_{DATE}.json", stage11)

    with pytest.raises(verifier.SemanticVerificationError, match="missing chrono out-of-fold"):
        verifier.verify_semantic_contract(route_dir=route, repo_root=tmp_path, write_result=False, check_config=False)


def test_semantic_verifier_rejects_unresolved_local_repairable_row(tmp_path: Path) -> None:
    route = _build_minimal_route(tmp_path)
    _write_jsonl(
        route / f"VNEXT_MOONSHOT_STAGE11_REFUSAL_REPAIR_SPLIT_LEDGER_{DATE}.jsonl",
        [
            {
                "terminal_repair_class": "activation_excluded_secondary_branch_pending_prop_default_not_source_repair",
                "repair_class_tags": [
                    "activation_excluded_secondary_branch_scope",
                    "ordered_ltf_or_tick_required",
                    "forward_capture_required",
                ],
                "locally_repairable_now": True,
                "action_taken": "classified_only",
            }
        ],
    )

    with pytest.raises(verifier.SemanticVerificationError, match="locally repairable row not repaired"):
        verifier.verify_semantic_contract(route_dir=route, repo_root=tmp_path, write_result=False, check_config=False)


def test_semantic_verifier_rejects_missing_prop_adjudication(tmp_path: Path) -> None:
    route = _build_minimal_route(tmp_path)
    _write_jsonl(
        route / f"VNEXT_MOONSHOT_STAGE11_PROP_AWARE_ROUTER_COMPARISON_{DATE}.jsonl",
        [
            {
                "policy_name": "be_after_trigger_prop_pass_default",
                "reference_ev_per_terminal_day_usd_fee599_payout8000": 7.0,
                "allowed_trades": 9,
            },
            {
                "policy_name": "condition_asof_displacement_v1_account_restart",
                "reference_ev_per_terminal_day_usd_fee599_payout8000": 8.0,
                "allowed_trades": 10,
            },
        ],
    )

    with pytest.raises(verifier.SemanticVerificationError, match="condition router row-level improvement"):
        verifier.verify_semantic_contract(route_dir=route, repo_root=tmp_path, write_result=False, check_config=False)
