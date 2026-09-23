from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_candidate_repair_stage09_decision_dossier_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("stage09_repair_builder", MODULE_PATH)
stage09 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage09
spec.loader.exec_module(stage09)


def _summary_fixture() -> dict:
    return {
        "candidate_universe_rows": 253234,
        "executable_stream_rows": 79320,
        "paid_api_or_vendor_calls_made": 0,
        "no_paid_call_replay_diagnostic_only": True,
        "broker_facing_activation_change": False,
        "required_metric_coverage": {"selected_rows": True, "total_r": True},
        "off_kz_treatment": {"off_kz_rows_in_repaired_selected_stream": 0},
        "best_policy_reference_fee_599_payout_8000": {
            "policy": "ACCOUNT_ABANDON_OR_RESTART",
            "reference_expected_value_per_attempt_usd": 1000.0,
            "reference_ev_per_terminal_day_usd_fee599_payout8000": 500.0,
        },
        "policy_metrics": {
            "ACCOUNT_ABANDON_OR_RESTART": {
                "allowed_trades": 80,
                "accepted_winners": 50,
                "accepted_losers": 30,
                "expectancy_r": 0.2,
                "total_r": 16.0,
                "risk_adjusted_r": 15.0,
                "profit_factor": 1.4,
                "pass_rate": 0.5,
                "account_loss_rate": 0.4,
                "paid_api_or_vendor_calls_made": 0,
                "ai_calls_required_after_prop_accept": 80,
                "ai_calls_saved_by_prop_block_or_defer": 20,
            }
        },
    }


def _ablation_fixture() -> dict:
    return {
        "layers": [
            {"layer": "baseline_current_shadow", "selected_count": 100},
            {
                "layer": "stage05_avoid_pre_ai_demotion",
                "recovered_rows": 42,
                "recovered_r": 9.5,
            },
        ]
    }


def _state_fixture() -> dict:
    return {
        "stage_status_table": {"STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY": "complete"},
        "verification_status": {"stage08_verifier_ok": True},
    }


def test_classify_decision_accepts_viable_repaired_candidate():
    decision = stage09.classify_decision(
        _summary_fixture(), _ablation_fixture(), _state_fixture()
    )

    assert decision["final_state"] == "production_candidate_viable_after_repair"
    assert decision["hard_failures"] == []
    assert decision["selected_to_baseline_ratio"] == 0.8


def test_classify_decision_rejects_negative_or_collapsed_candidate():
    summary = _summary_fixture()
    bad = copy.deepcopy(summary)
    best = bad["policy_metrics"]["ACCOUNT_ABANDON_OR_RESTART"]
    best["allowed_trades"] = 5
    best["accepted_winners"] = 0
    best["accepted_losers"] = 5
    best["expectancy_r"] = -1.0
    best["total_r"] = -5.0
    best["risk_adjusted_r"] = -5.0
    best["profit_factor"] = 0.0

    decision = stage09.classify_decision(bad, _ablation_fixture(), _state_fixture())

    assert decision["final_state"] == "production_candidate_failed_with_full_failure_anatomy"
    assert "negative_or_zero_expectancy" in decision["hard_failures"]
    assert "selected_count_collapsed_below_25pct_of_baseline" in decision["hard_failures"]


def test_completion_audit_records_required_instruction_coverage():
    audit = stage09.build_completion_audit(
        stage08_summary=_summary_fixture(),
        ablation=_ablation_fixture(),
        state={
            **_state_fixture(),
            "stage_status_table": {
                "STAGE_00_INPUT_FREEZE_AND_FAILED_ROUTE_INVALIDATION": "complete",
                "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER": "complete",
                "STAGE_02_ACCEPTANCE_GATE_REPAIR": "complete",
                "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR": "complete",
                "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR": "complete",
                "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR": "complete",
                "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR": "complete",
                "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR": "complete",
                "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY": "complete",
            },
            "tests_and_verifiers_run": [],
            "forbidden_boundary_actions_not_taken": [],
            "row_count_hash_coverage": {
                "stage08_repaired_replay_decision_rows": 555240,
                "stage08_repaired_prop_attempt_rows": 1119,
            },
        },
        decision=stage09.classify_decision(
            _summary_fixture(), _ablation_fixture(), _state_fixture()
        ),
        changed_files=["fixture.py"],
    )

    assert audit["completion_checks"]["prop_replay_uses_segmented_attempts"] is True
    assert "controlling_prompt_operationalized" in audit["instruction_coverage"]
    assert audit["final_state"] == "production_candidate_viable_after_repair"
