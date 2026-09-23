#!/usr/bin/env python3
"""Verify the market-expansion activation-candidate package artifacts."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_activation_candidate_package"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.ultimate_book import admission  # noqa: E402
from src.components.ultimate_book.sleeves import candidate_registry, registry  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def check(name: str, passed: bool, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail or {}}


def selected_specs() -> dict[str, candidate_registry.MarketExpansionDefaultOffSpec]:
    return {
        name: spec
        for name, spec in candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES.items()
        if spec.design_status == "default_off_spec_design_ready" and spec.symbol_collision_winner
    }


def code_row(name: str, spec: candidate_registry.MarketExpansionDefaultOffSpec) -> dict[str, Any]:
    return {
        "tag": name,
        "file_symbol": spec.file_symbol,
        "broker_symbol": spec.broker_symbol,
        "family": spec.family,
        "mechanism": spec.mechanism,
        "design_status": spec.design_status,
        "candidate_seed_weight": spec.candidate_seed_weight,
        "candidate_weight_ceiling": spec.candidate_weight_ceiling,
        "activation_weight_now": spec.activation_weight_now,
        "symbol_collision_winner": spec.symbol_collision_winner,
        "target2_exact_m1_event_count": spec.target2_exact_m1_event_count,
        "target2_remaining_path_gap_count": spec.target2_m15_proxy_event_count,
        "target2_ordered_mean_r": spec.target2_ordered_mean_r,
        "full_book_delta_sharpe": spec.full_book_delta_sharpe,
        "evidence_route": spec.evidence_route,
        "note": spec.note,
    }


def main() -> int:
    created_at = datetime.now(UTC).isoformat()
    result = load_json(ROUTE / "MARKET_EXPANSION_ACTIVATION_CANDIDATE_PACKAGE_RESULT.json")
    input_manifest = load_json(ROUTE / "ACTIVATION_INPUT_MANIFEST.json")
    spec_manifest = load_json(ROUTE / "BROKER_SPEC_COST_SESSION_MANIFEST.json")
    active_audit = load_json(ROUTE / "ACTIVE_BEHAVIOR_AUDIT.json")
    repair = load_json(ROUTE / "REPAIR_LEDGER.json")
    saturation = load_json(ROUTE / "SATURATION_AUDIT.json")
    completion = load_json(ROUTE / "COMPLETION_AUDIT.json")
    focused = load_json(ROUTE / "FOCUSED_TEST_RESULT.json")
    output_manifest = load_json(ROUTE / "OUTPUT_MANIFEST.json")
    rows = load_jsonl(ROUTE / "ACTIVATION_CANDIDATE_ROW_LEDGER.jsonl")
    generator_rows = load_jsonl(ROUTE / "GENERATOR_IMPLEMENTATION_DECISION_LEDGER.jsonl")
    sizing_rows = load_jsonl(ROUTE / "SPLIT_STABILITY_SIZING_LEDGER.jsonl")
    interaction_rows = load_jsonl(ROUTE / "FULL_BOOK_INTERACTION_REPLAY_LEDGER.jsonl")
    decision_rows = load_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    subagent_rows = load_jsonl(ROUTE / "SUBAGENT_REVIEW_INTEGRATION_LEDGER.jsonl")

    specs = selected_specs()
    by_tag = {row["tag"]: row for row in rows}
    code_by_tag = {name: code_row(name, spec) for name, spec in specs.items()}
    generator_by_tag = {row["tag"]: row for row in generator_rows}
    sizing_by_tag = {row["tag"]: row for row in sizing_rows}
    interaction_by_tag = {row["tag"]: row for row in interaction_rows}
    expansion_names = set(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_NAMES)
    active_registry = admission.effective_registry(include_candidate_book=True)
    candidate_runtime = admission.candidate_book_registry()

    parity_fields = (
        "file_symbol",
        "broker_symbol",
        "family",
        "mechanism",
        "design_status",
        "candidate_seed_weight",
        "candidate_weight_ceiling",
        "activation_weight_now",
        "symbol_collision_winner",
        "target2_exact_m1_event_count",
        "target2_remaining_path_gap_count",
        "target2_ordered_mean_r",
        "full_book_delta_sharpe",
        "evidence_route",
        "note",
    )
    code_mismatches: list[dict[str, Any]] = []
    for tag, code in sorted(code_by_tag.items()):
        row = by_tag.get(tag)
        if row is None:
            code_mismatches.append({"tag": tag, "field": "missing_route_row"})
            continue
        for field in parity_fields:
            if row.get(field) != code.get(field):
                code_mismatches.append({"tag": tag, "field": field, "route": row.get(field), "code": code.get(field)})

    cost3_split_pass_tags = sorted(
        row["tag"]
        for row in rows
        if (row.get("cost_stress", {}).get("cost3") or {}).get("every_populated_split_positive") is True
    )
    exact_split_pass_tags = sorted(
        row["tag"] for row in rows if row.get("target2_split_every_populated_positive") is True
    )
    split_conflict_tags = sorted(
        row["tag"] for row in rows if row.get("target2_split_every_populated_positive") is False
    )
    cost3_control_tags = sorted(
        row["tag"]
        for row in rows
        if (row.get("cost_stress", {}).get("cost3") or {}).get("every_populated_split_positive") is not True
    )
    live_spec_complete_tags = sorted(
        row["tag"] for row in rows if row.get("broker_execution_spec_complete_for_live_authority") is True
    )
    generator_missing_contracts = [
        row["tag"]
        for row in generator_rows
        if row.get("current_generator_code_status") != "not_implemented_in_runtime"
        or "D1 next-open" not in row.get("non_implementation_requirement", "")
        or "ultimate_book_include_market_expansion_book" not in " ".join(row.get("required_runtime_safety_design") or [])
    ]
    missing_required_live_fields = [
        row["tag"]
        for row in rows
        if not {
            "trade_stops_level",
            "trade_freeze_level",
            "explicit_broker_trading_session_table",
            "exact_live_D1_M1_server_timezone_rule",
            "commission_slippage_to_R_conversion",
            "limit_fill_or_market_fill_policy",
            "runtime_generator_parity",
            "full_generator_book_replay",
        }.issubset(set(row.get("broker_execution_spec_missing_fields") or []))
    ]
    missing_source_artifacts = [
        row for row in input_manifest.get("source_artifacts", []) if not row.get("exists") or not row.get("sha256")
    ]
    manifest_artifacts = {Path(row["path"]).name for row in output_manifest.get("artifacts", [])}

    checks = [
        check(
            "result_and_completion_ok",
            result.get("ok") is True
            and completion.get("ok") is True
            and saturation.get("ok") is True
            and repair.get("ok") is True
            and focused.get("ok") is True,
            {
                "result_ok": result.get("ok"),
                "completion_ok": completion.get("ok"),
                "saturation_ok": saturation.get("ok"),
                "repair_ok": repair.get("ok"),
                "focused_ok": focused.get("ok"),
            },
        ),
        check(
            "selectable_row_counts_and_code_parity",
            len(rows) == len(specs) == result.get("selectable_activation_candidate_count") == 14
            and set(by_tag) == set(code_by_tag)
            and not code_mismatches,
            {
                "route_rows": len(rows),
                "code_specs": len(specs),
                "mismatch_count": len(code_mismatches),
                "sample_mismatches": code_mismatches[:10],
            },
        ),
        check(
            "broker_contract_and_live_spec_boundary",
            result.get("broker_spec_ready_count") == 14
            and result.get("broker_contract_min_volume_ready_count") == 14
            and result.get("broker_execution_spec_live_complete_count") == 0
            and spec_manifest.get("broker_spec_ready_count") == 14
            and not live_spec_complete_tags
            and not missing_required_live_fields,
            {
                "broker_spec_ready_count": result.get("broker_spec_ready_count"),
                "broker_execution_spec_live_complete_count": result.get("broker_execution_spec_live_complete_count"),
                "live_spec_complete_tags": live_spec_complete_tags,
                "missing_required_live_fields": missing_required_live_fields,
            },
        ),
        check(
            "cost_split_and_path_split_counts",
            result.get("positive_cost3_mean_count") == 14
            and result.get("cost1_split_pass_count") == 13
            and result.get("cost2_split_pass_count") == 10
            and result.get("cost3_split_pass_count") == len(cost3_split_pass_tags) == 9
            and result.get("exact_or_ordered_split_pass_count") == len(exact_split_pass_tags) == 12
            and split_conflict_tags == [
                "mx_jp225_cash_d1_volume_surge_reversal",
                "mx_us30_cash_d1_volume_surge_reversal",
            ]
            and cost3_control_tags
            == [
                "mx_aus200_cash_d1_volume_surge_reversal",
                "mx_avausd_d1_donchian_20_breakout",
                "mx_jp225_cash_d1_volume_surge_reversal",
                "mx_nzdjpy_d1_donchian_20_breakout",
                "mx_spn35_cash_d1_volume_surge_reversal",
            ],
            {
                "cost3_split_pass_tags": cost3_split_pass_tags,
                "exact_split_pass_tags": exact_split_pass_tags,
                "split_conflict_tags": split_conflict_tags,
                "cost3_control_tags": cost3_control_tags,
            },
        ),
        check(
            "generator_mapping_and_nonimplementation_contract",
            len(generator_rows) == len(generator_by_tag) == 14
            and set(generator_by_tag) == set(by_tag)
            and result.get("runtime_generator_implemented_count") == 0
            and result.get("runtime_generator_not_implemented_count") == 14
            and not generator_missing_contracts,
            {
                "generator_row_count": len(generator_rows),
                "generator_missing_contracts": generator_missing_contracts,
            },
        ),
        check(
            "sizing_controls_preserve_caveat_rows",
            set(sizing_by_tag) == set(by_tag)
            and "negative_path_split_requires_holdout_or_sizing_gate_before_activation"
            in sizing_by_tag["mx_jp225_cash_d1_volume_surge_reversal"]["activation_stage_controls"]
            and "negative_path_split_requires_holdout_or_sizing_gate_before_activation"
            in sizing_by_tag["mx_us30_cash_d1_volume_surge_reversal"]["activation_stage_controls"]
            and "cost3_split_stress_not_all_positive_requires_initial_weight_cap_or_limit_order_model"
            in sizing_by_tag["mx_spn35_cash_d1_volume_surge_reversal"]["activation_stage_controls"],
            {
                "jp225_controls": sizing_by_tag["mx_jp225_cash_d1_volume_surge_reversal"]["activation_stage_controls"],
                "us30_controls": sizing_by_tag["mx_us30_cash_d1_volume_surge_reversal"]["activation_stage_controls"],
                "spn35_controls": sizing_by_tag["mx_spn35_cash_d1_volume_surge_reversal"]["activation_stage_controls"],
            },
        ),
        check(
            "interaction_rows_are_sensitivity_not_generator_replay",
            set(interaction_by_tag) == set(by_tag)
            and all(row.get("runtime_generator_replay_status") == "not_run_current_generator_not_implemented" for row in interaction_rows)
            and all(row.get("delta_sharpe") is not None for row in interaction_rows),
            {"interaction_count": len(interaction_rows)},
        ),
        check(
            "active_runtime_boundary_closed",
            result.get("deployment_ready") is False
            and result.get("activation_weight_now") == 0.0
            and result.get("live_authority") is False
            and active_audit.get("activation_weight_sum") == 0.0
            and not active_audit.get("market_expansion_names_in_effective_registry")
            and not active_audit.get("market_expansion_names_in_candidate_book_registry")
            and not active_audit.get("market_expansion_names_in_candidate_built")
            and not active_audit.get("market_expansion_names_in_candidate_registry_candidates")
            and not active_audit.get("market_expansion_runtime_names")
            and not (expansion_names & set(active_registry))
            and not (expansion_names & set(candidate_runtime))
            and not (expansion_names & set(registry.CANDIDATE_BUILT))
            and not (expansion_names & set(candidate_registry.CANDIDATES)),
            {
                "deployment_ready": result.get("deployment_ready"),
                "activation_weight_sum": active_audit.get("activation_weight_sum"),
                "effective_intersection": sorted(expansion_names & set(active_registry)),
            },
        ),
        check(
            "input_and_output_manifests_complete",
            not missing_source_artifacts
            and {
                "MARKET_EXPANSION_ACTIVATION_CANDIDATE_PACKAGE_RESULT.json",
                "ACTIVATION_CANDIDATE_ROW_LEDGER.jsonl",
                "BROKER_SPEC_COST_SESSION_MANIFEST.json",
                "GENERATOR_IMPLEMENTATION_DECISION_LEDGER.jsonl",
                "SPLIT_STABILITY_SIZING_LEDGER.jsonl",
                "FULL_BOOK_INTERACTION_REPLAY_LEDGER.jsonl",
                "SUBAGENT_REVIEW_INTEGRATION_LEDGER.jsonl",
                "NEXT_PROMPT.md",
            }.issubset(manifest_artifacts),
            {
                "missing_source_artifacts": missing_source_artifacts,
                "manifest_artifacts": sorted(manifest_artifacts),
            },
        ),
        check(
            "subagent_reviews_integrated",
            {row.get("subagent") for row in subagent_rows} == {"Franklin", "Lovelace"}
            and len(decision_rows) >= 15
            and any(row.get("decision") == "DO_NOT_KILL_COST_OR_SPLIT_CAVEAT_ROWS_TRANSLATE_TO_CONTROLS" for row in decision_rows),
            {
                "subagent_rows": subagent_rows,
                "decision_count": len(decision_rows),
            },
        ),
        check(
            "forbidden_surfaces_closed",
            result.get("orderflow_used") is False
            and result.get("broker_or_order_mutation") is False
            and result.get("account_info_read") is False
            and result.get("config_or_live_activation_changed") is False
            and result.get("vps_process_touched") is False
            and completion.get("forbidden_surfaces_touched") == [],
            {
                "orderflow_used": result.get("orderflow_used"),
                "broker_or_order_mutation": result.get("broker_or_order_mutation"),
                "account_info_read": result.get("account_info_read"),
                "config_or_live_activation_changed": result.get("config_or_live_activation_changed"),
                "vps_process_touched": result.get("vps_process_touched"),
            },
        ),
    ]
    issue_rows = [item for item in checks if not item["passed"]]
    verification = {
        "schema": f"{SCHEMA_PREFIX}.verifier_result.v1",
        "created_at_utc": created_at,
        "ok": not issue_rows,
        "issue_count": len(issue_rows),
        "checks": checks,
        "summary": {
            "row_count": len(rows),
            "family_counts": dict(sorted(Counter(row["family"] for row in rows).items())),
            "mechanism_counts": dict(sorted(Counter(row["mechanism"] for row in rows).items())),
            "decision_counts": dict(sorted(Counter(row["row_level_decision"] for row in rows).items())),
        },
    }
    write_json(ROUTE / "MARKET_EXPANSION_ACTIVATION_CANDIDATE_PACKAGE_VERIFIER_RESULT.json", verification)
    print(json.dumps({"ok": verification["ok"], "issue_count": len(issue_rows)}, sort_keys=True))
    return 0 if verification["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
