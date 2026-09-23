from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"


def load_jsonl_sample(name: str, limit: int = 500) -> list[dict]:
    rows = []
    with (ROUTE_DIR / name).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
                if len(rows) >= limit:
                    break
    return rows


def test_stage09_results_are_shadow_only_and_advance_to_stage10() -> None:
    results = json.loads((ROUTE_DIR / f"VNEXT_MOONSHOT_ML_CHALLENGER_RESULTS_{DATE_ID}.json").read_text(encoding="utf-8"))
    state = json.loads((ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json").read_text(encoding="utf-8"))
    assert results["paid_api_or_vendor_calls_made"] == 0
    assert results["fixed_1_5r_used_as_activation_truth"] is False
    assert results["ml_shadow_only_until_sealed_validation_and_owner_approval"] is True
    assert results["feature_ledger_rows"] > 0
    assert state["first_incomplete_invariant"] == "STAGE_10_DEFAULT_OFF_RUNTIME_INTEGRATION"


def test_stage09_feature_ledger_has_all_required_label_families() -> None:
    rows = load_jsonl_sample(f"VNEXT_MOONSHOT_ML_DYNAMIC_FEATURE_LEDGER_{DATE_ID}.jsonl")
    assert rows
    required = {
        "label_dynamic_r_live_current",
        "label_stop_first_risk",
        "label_no_fill_risk",
        "label_candidate_origin_family",
        "label_prop_attempt_success_proxy",
        "label_source_completeness",
        "label_ai_call_need",
        "label_execution_policy_recommendation",
    }
    for row in rows:
        assert required <= set(row)
        assert row["feature_columns"]
        assert row["split_time"] in {"train_pre2025", "test_2025", "holdout_2026", "unknown_time_split"}
        assert row["fixed_1_5r_used_as_activation_truth"] is False


def test_stage09_leakage_audit_excludes_outcome_fields_from_features() -> None:
    audit_rows = load_jsonl_sample(f"VNEXT_MOONSHOT_ML_LEAKAGE_AUDIT_LEDGER_{DATE_ID}.jsonl", limit=200)
    forbidden_scan = next(row for row in audit_rows if row["audit_id"] == "feature_column_forbidden_field_scan")
    assert forbidden_scan["status"] == "pass"
    assert forbidden_scan["forbidden_fields_in_feature_columns"] == []
    assert "legacy_final_r" not in forbidden_scan["feature_columns"]
    assert "policy_results" not in forbidden_scan["feature_columns"]


def test_stage09_challengers_include_dependency_free_and_installed_tool_attempts() -> None:
    results = json.loads((ROUTE_DIR / f"VNEXT_MOONSHOT_ML_CHALLENGER_RESULTS_{DATE_ID}.json").read_text(encoding="utf-8"))
    assert results["dependency_free_baselines"]["classification"]
    assert results["dependency_free_baselines"]["regression"]
    assert "sklearn" in results["installed_local_ml_tools"]
    assert results["sklearn_challengers"]
    assert results["lightgbm_challengers"]
