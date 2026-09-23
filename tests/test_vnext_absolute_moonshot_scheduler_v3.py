from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = (
    ROOT
    / "research"
    / "operations"
    / "vnext_absolute_moonshot_scheduler_v3_2026_06_01"
)
sys.path.insert(0, str(ROUTE_DIR))

SPEC = importlib.util.spec_from_file_location(
    "scheduler_v3_default_off", ROUTE_DIR / "scheduler_v3_default_off.py"
)
scheduler_v3 = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = scheduler_v3
SPEC.loader.exec_module(scheduler_v3)

BUILDER_SPEC = importlib.util.spec_from_file_location(
    "scheduler_v3_builder", ROUTE_DIR / "build_vnext_absolute_moonshot_scheduler_v3.py"
)
builder = importlib.util.module_from_spec(BUILDER_SPEC)
assert BUILDER_SPEC and BUILDER_SPEC.loader
sys.modules[BUILDER_SPEC.name] = builder
BUILDER_SPEC.loader.exec_module(builder)


def base_row(**overrides):
    row = {
        "scheduler_decision": "REJECTED",
        "scheduler_reason": "same_symbol_exposure_conflict_active_until_lifecycle_close",
        "same_symbol_state": "same_symbol_same_side_active",
        "same_symbol_release_state": "same_symbol_all_risk_released_lifecycle_active",
        "cluster_state": "cluster_active_under_ceiling",
        "requested_risk_pct": 1.0,
        "approved_risk_pct": 0.0,
        "result_r": 1.2,
        "max_money_risk_allowed_pct": 1.0,
        "max_safe_risk_with_cluster_pct": 1.0,
        "total_risk_pct_before": 1.0,
        "correlated_cluster_risk_pct_before": 1.0,
        "cost_buffer_pct": 0.1,
        "day_start_baseline": 100000.0,
        "current_equity": 100500.0,
        "realized_proxy_pnl": 500.0,
    }
    row.update(overrides)
    return row


def test_same_side_released_positive_row_queues_without_live_activation():
    action = scheduler_v3.classify_scheduler_v3_action(base_row())

    assert action.decision == "QUEUE"
    assert action.action_class == "queue"
    assert action.runtime_effect_now is False
    assert action.owner_approval_required_for_live_use is True


def test_high_expectancy_same_side_released_row_gets_replace_contract():
    action = scheduler_v3.classify_scheduler_v3_action(base_row(result_r=2.5))

    assert action.decision == "REPLACE"
    assert action.action_class == "replace"
    assert "ticket" in action.action


def test_opposite_side_same_symbol_is_conflict_net_reject():
    action = scheduler_v3.classify_scheduler_v3_action(
        base_row(
            same_symbol_state="same_symbol_opposite_side_active",
            same_symbol_release_state="same_symbol_open_worst_case_risk_active",
            result_r=3.0,
        )
    )

    assert action.decision == "REJECTED"
    assert action.action_class == "conflict_net"
    assert "hedge" in action.reason


def test_missing_risk_requires_source_not_count_cap():
    action = scheduler_v3.classify_scheduler_v3_action(
        base_row(
            scheduler_reason="selected_cell_or_effective_risk_missing_nonpositive_stale_source_repair_required",
            requested_risk_pct=0.0,
        )
    )

    assert action.decision == "REQUIRE_SOURCE"
    assert action.action_class == "require_source"
    assert "count" not in action.reason


def test_money_risk_exposure_has_required_fields():
    exposure = scheduler_v3.build_money_risk_exposure(base_row())

    for field in scheduler_v3.REQUIRED_MONEY_RISK_FIELDS:
        assert field in exposure
    assert exposure["open_worst_case_sl_risk_pct"] is not None
    assert exposure["portfolio_ceiling_pct"] is not None


def test_written_scheduler_v3_outputs_verify_when_present():
    if not builder.DEFAULT_OFF_PACKAGE.exists():
        return

    result = builder.verify_outputs(write=False)

    assert result["ok"] is True
    assert result["ledger_counts"]["full_evidence_rows"] == builder.EXPECTED_ROWS
    assert result["action_class_counts"]["admit"] > 0
    assert result["action_class_counts"]["require_source"] > 0
