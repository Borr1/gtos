from __future__ import annotations

from pathlib import Path

from scripts import build_lto031_lto032_source_contract_registry as script
from scripts import build_lto031_lto032_source_unblocking_plan as plan
from src.research_infra import lto_source_contract_registry as mod


def test_registry_rows_cover_all_source_contracts_with_required_fields():
    payload = mod.build_registry_payload(plan.build_source_contracts(), generated_at_utc="2026-05-06T00:00:00+00:00")
    rows = payload["registry_rows"]

    assert payload["status"] == mod.STATUS_READY
    assert payload["promotion_verdict"] == mod.PROMOTION_VERDICT
    assert payload["source_contract_count"] == 11
    assert payload["source_contract_counts_by_lto"] == {"LTO-031": 7, "LTO-032": 4}
    assert payload["validation_safe_counts"] == {"false": 11}
    assert payload["validation_issues"] == []
    assert all(mod.REQUIRED_ROW_FIELDS <= set(row) for row in rows)
    assert all(row["promotion_verdict"] == mod.PROMOTION_VERDICT for row in rows)


def test_blocked_or_incomplete_source_cannot_be_marked_validation_safe():
    rows = [
        mod.normalize_contract(row)
        for row in plan.build_source_contracts()
        if row["source_key"] in {"official_or_historical_aggregate_gex", "kmw_fx_fix"}
    ]
    rows[0]["validation_safe"] = True
    rows[1]["validation_safe"] = True

    issues = mod.validate_registry_rows(rows)

    assert "official_or_historical_aggregate_gex:BLOCKED_SOURCE_MARKED_VALIDATION_SAFE" in issues
    assert "official_or_historical_aggregate_gex:VALIDATION_SAFE_WITH_BLOCKERS" in issues
    assert "kmw_fx_fix:BLOCKED_SOURCE_MARKED_VALIDATION_SAFE" in issues


def test_flashalpha_basic_is_forward_context_only_not_historical_gamma_validation():
    payload = mod.build_registry_payload(plan.build_source_contracts(), generated_at_utc="2026-05-06T00:00:00+00:00")
    rows = {row["source_key"]: row for row in payload["registry_rows"]}
    flashalpha = rows["flashalpha_basic_gex_forward_proxy"]

    assert flashalpha["forward_context_allowed"] is True
    assert flashalpha["historical_validation_allowed"] is False
    assert flashalpha["validation_safe"] is False
    assert flashalpha["allowed_feature_role"] == "FORWARD_CONTEXT_ONLY"
    assert "FORWARD_PROXY_ONLY_NO_HISTORICAL_GAMMA_RECONSTRUCTION" in flashalpha["validation_safe_blockers"]


def test_databento_credit_row_requires_manifest_estimate_and_caps_before_fetch():
    payload = mod.build_registry_payload(plan.build_source_contracts(), generated_at_utc="2026-05-06T00:00:00+00:00")
    rows = {row["source_key"]: row for row in payload["registry_rows"]}
    databento = rows["pre_2024_tick_lob"]

    assert databento["cost_policy"] == "EXISTING_DATABENTO_CREDITS_ONLY_MANIFEST_AND_ESTIMATE_BEFORE_FETCH"
    assert databento["validation_safe"] is False
    assert "DATABENTO_REQUEST_MANIFEST_AND_COST_ESTIMATE_NOT_BUILT" in databento["validation_safe_blockers"]
    assert databento["databento_use"] == "PRIMARY_HISTORICAL_COUNTERFACTUAL_REPLAY_SOURCE"


def test_registry_payload_preserves_no_action_boundary():
    payload = mod.build_registry_payload(plan.build_source_contracts(), generated_at_utc="2026-05-06T00:00:00+00:00")

    assert payload["ai_calls"] == 0
    assert payload["canary_calls"] == 0
    assert payload["order_calls"] == 0
    assert payload["paid_data_calls"] == 0
    assert payload["paid_fetch_attempted"] is False
    assert payload["no_ai_calls"] is True
    assert payload["no_execution"] is True


def test_script_writes_registry_markdown_json_and_operations_summary(tmp_path: Path):
    out_json = tmp_path / "registry.json"
    out_md = tmp_path / "registry.md"
    ops_md = tmp_path / "ops.md"

    assert script.main(
        [
            "--output-json",
            str(out_json),
            "--output-md",
            str(out_md),
            "--operations-md",
            str(ops_md),
            "--generated-at-utc",
            "2026-05-06T00:00:00+00:00",
        ]
    ) == 0

    assert out_json.exists()
    assert out_md.exists()
    assert ops_md.exists()
    markdown = out_md.read_text(encoding="utf-8")
    ops = ops_md.read_text(encoding="utf-8")
    assert "NO_PROMOTION_VERDICT" in markdown
    assert "Validation-safe rows: `{'false': 11}`" in markdown
    assert "No source is marked validation-safe" in ops
