"""Focused tests for the route-local SCID implementation design package."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent


def load_module(filename: str, name: str):
    path = ROUTE_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module(
    "build_scid_forward_capture_implementation_design_package_2026_05_12.py",
    "scid_impl_design_builder_for_tests",
)
verifier = load_module(
    "verify_scid_forward_capture_implementation_design_package_2026_05_12.py",
    "scid_impl_design_verifier_for_tests",
)


def test_capture_group_contract_is_complete():
    names = {row["capture_group"] for row in builder.CAPTURE_GROUPS}
    assert names == {
        "baseline_control_fields",
        "framework_setup_family",
        "future_orderflow_depth_proxy_requirements",
        "intended_entry_reference",
        "intended_side_direction",
        "intended_stop_reference",
        "intended_target_reference",
        "lifecycle_fill_cancel_expiry_source_status",
        "lower_timeframe_asof_path_availability",
        "poi_type_bounds_source",
    }
    required_keys = {
        "source_contract",
        "source_asof_rule",
        "no_leak_rule",
        "redaction_rule",
        "fail_closed_behavior",
        "duplicate_policy",
        "rollback_plan",
        "test_plan",
        "g12_acceptance_criteria",
        "proposed_patch_artifact",
    }
    for row in builder.CAPTURE_GROUPS:
        assert required_keys <= set(row)
        for key in required_keys:
            assert row[key]


def test_safe_flags_keep_no_live_no_validation_boundary():
    assert builder.SAFE_FLAGS["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    for key in [
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
        "broker_or_account_evidence_opened",
        "ai_api_call_opened",
        "paid_vendor_call_opened",
        "raw_blob_capture_opened",
        "result_scoring_opened",
        "performance_claim_opened",
        "prompt_change_opened",
        "config_change_opened",
        "risk_logic_change_opened",
        "execution_logic_change_opened",
        "canary_or_selector_change_opened",
    ]:
        assert builder.SAFE_FLAGS[key] is False


def test_builder_emits_proposed_only_patch_artifacts():
    builder.build_package()
    patch_dir = ROUTE_DIR / "proposed_patches"
    patches = sorted(patch_dir.glob("*.patch.md"))
    assert len(patches) >= 3
    combined = "\n".join(path.read_text(encoding="utf-8") for path in patches)
    assert "PROPOSED ONLY - DO NOT APPLY IN THIS ROUTE" in combined
    assert "NO_PRODUCTION_EDIT_IN_THIS_ROUTE" in combined
    assert "src/research_infra/forward_capture.py" in combined
    assert "src/components/orchestrator.py" in combined
    assert "src/components/pending_limit_lifecycle_logger.py" in combined
    assert "tests/test_scid_forward_capture_runtime_adapter.py" in combined


def test_redaction_plan_blocks_lifecycle_and_result_leaks():
    payloads = builder.build_payloads()
    redaction = payloads["REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN"]
    forbidden = set(redaction["forbidden_fields"])
    assert {
        "pending_ticket",
        "mt5_order_ticket",
        "trade_state_ticket",
        "actual_r",
        "synthetic_path_r",
        "slippage_price",
        "broker_fill_state",
        "pnl",
        "win_loss",
        "expectancy",
    } <= forbidden


def test_verifier_passes_static_route_checks_after_build():
    builder.build_package()
    result = verifier.verify_package(write_result=False)
    assert result["ok"], result["failures"]
    assert result["candidate_rows_verified"] == 3014
    assert result["capture_groups_verified"] == 10
