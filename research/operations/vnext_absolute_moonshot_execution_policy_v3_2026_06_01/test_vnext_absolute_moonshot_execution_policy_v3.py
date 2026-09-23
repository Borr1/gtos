from __future__ import annotations

from build_vnext_absolute_moonshot_execution_policy_v3 import (
    BROKER_FIELD_FAMILIES,
    OUTPUTS,
    count_jsonl,
    iter_jsonl,
    policy_family_from_id,
    route_decision_from_dominance,
    verify_outputs,
)


def test_v3_registry_extends_lane11_without_truncating() -> None:
    rows = list(iter_jsonl(OUTPUTS["policy_registry"]))
    assert sum(1 for row in rows if row["inherited_from_lane11"]) >= 890
    assert sum(1 for row in rows if row["inherited_from_lane11"] and row["is_baseline_comparator"]) >= 10
    assert len(rows) > 890
    assert {row["policy_family"] for row in rows} >= {
        "momentum_exhaustion",
        "partial_be_runner",
        "trailing_runner",
        "time_stop",
        "be_after_trigger",
    }


def test_policy_route_decision_separates_proxy_and_exact_r() -> None:
    sample = next(
        row
        for row in iter_jsonl(OUTPUTS["evaluation"])
        if row["result_scope"] == "source_bound_proxy_r"
    )
    assert sample["proxy_r_owned_by_v3"] is True
    assert sample["exact_r_owned_by_v3"] is False
    assert sample["exact_r"] is None
    assert route_decision_from_dominance("PROMOTE_DEFAULT_OFF_PROXY_RESEARCH_BRANCH_REQUIRES_STRICT_TICK", "momentum_exhaustion") == "trade_policy"


def test_broker_tick_lifecycle_requirements_cover_all_required_fields() -> None:
    rows = list(iter_jsonl(OUTPUTS["lifecycle_feasibility"]))
    fields = {row["field"] for row in rows}
    assert fields >= set(BROKER_FIELD_FAMILIES)
    partial_rows = [
        row
        for row in rows
        if row["policy_family"] == "partial_be_runner"
        and row["field"] in {"partial_close_ticket_identity", "residual_ticket_management"}
    ]
    assert len(partial_rows) == 2
    assert all(row["required_by_policy"] for row in partial_rows)


def test_default_off_package_has_no_runtime_effect_and_static_baseline_is_comparator() -> None:
    package = __import__("json").loads(OUTPUTS["routing_package"].read_text(encoding="utf-8"))
    assert package["runtime_effect_now"] is False
    assert package["owner_approval_required_for_live_use"] is True
    assert package["current_production_policy_status"]["fixed_1_5r_j46_j49_status"] == "historical_or_comparator_only"


def test_source_capture_decisions_include_execution_policy_v3_post_lane18_consumption() -> None:
    rows = list(iter_jsonl(OUTPUTS["source_decisions"]))
    assert rows
    dispositions = {row["disposition"] for row in rows}
    assert "read_only_export_required" in dispositions
    assert "forward_capture_required" in dispositions


def test_feasible_evaluation_and_routing_ledgers_preserve_full_material_rows() -> None:
    assert count_jsonl(OUTPUTS["evaluation"]) >= 106_000
    assert count_jsonl(OUTPUTS["routing_ledger"]) >= 7_398
    assert count_jsonl(OUTPUTS["source_gaps"]) >= 6_102
    assert policy_family_from_id("partial_ratio_0_25_trigger_1_0r_be_after_partial_runner_5_0") == "partial_be_runner"


def test_verify_outputs_passes() -> None:
    result = verify_outputs(write=False, count_large=True)
    assert result["ok"], result["issues"]
