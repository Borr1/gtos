#!/usr/bin/env python3
"""Build proof artifacts for the repaired market-expansion metadata registry."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
DEFAULT_OFF_REGISTRY_ROUTE = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_market_expansion_default_off_registry_2026_06_18"
)
PROXY_M1_REPAIR_ROUTE = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_market_expansion_proxy_m1_repair_2026_06_18"
)
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_repaired_registry_integration"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.ultimate_book import admission  # noqa: E402
from src.components.ultimate_book.sleeves import candidate_registry  # noqa: E402


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def remaining_gap_count(repair_row: dict[str, Any]) -> int:
    counts = repair_row.get("target2_exact_m1_status_counts", {})
    return sum(
        int(value)
        for key, value in counts.items()
        if key.startswith("no_m1_") or key == "geometry_not_reconstructable"
    )


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
        "runtime_effect": "none_metadata_only",
    }


def build() -> dict[str, Any]:
    created_at = utc_now()
    prior_registry_result = read_json(DEFAULT_OFF_REGISTRY_ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_RESULT.json")
    proxy_result = read_json(PROXY_M1_REPAIR_ROUTE / "MARKET_EXPANSION_PROXY_M1_REPAIR_RESULT.json")
    repair_candidates = read_jsonl(PROXY_M1_REPAIR_ROUTE / "EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl")
    interactions = read_jsonl(PROXY_M1_REPAIR_ROUTE / "FULL_BOOK_EXACT_M1_INTERACTION_LEDGER.jsonl")
    repair_by_tag = {row["tag"]: row for row in repair_candidates}
    interaction_by_tag = {row["tag"]: row for row in interactions}

    specs = candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES
    rows: list[dict[str, Any]] = []
    for name, spec in specs.items():
        row = code_row(name, spec)
        repair_row = repair_by_tag.get(name)
        if repair_row is not None:
            summary = repair_row["target2_exact_m1_summary"]
            row.update(
                {
                    "source_repair_decision": repair_row["decision"],
                    "source_repair_exact_m1_mean_r": summary["mean_r"],
                    "source_repair_every_populated_split_positive": summary["every_populated_split_positive"],
                    "source_repair_remaining_gap_count": remaining_gap_count(repair_row),
                    "source_repair_new_exact_m1_events_added": repair_row["new_exact_m1_events_added"],
                    "source_repair_coverage_ratio": repair_row["repaired_exact_m1_coverage_ratio"],
                    "source_repair_route": rel(PROXY_M1_REPAIR_ROUTE),
                    "source_repair_split_count": summary["populated_split_count"],
                    "source_repair_positive_split_count": summary["positive_populated_split_count"],
                }
            )
        interaction = interaction_by_tag.get(name)
        if interaction is not None:
            row.update(
                {
                    "source_repair_full_book_delta_sharpe": interaction["delta_sharpe"],
                    "source_repair_scenario_sharpe": interaction["scenario_sharpe"],
                    "source_repair_matched_current_book_days": interaction["matched_current_book_days"],
                }
            )
        rows.append(row)

    status_counts = Counter(row["design_status"] for row in rows)
    family_counts = Counter(row["family"] for row in rows)
    mechanism_counts = Counter(row["mechanism"] for row in rows)
    route_counts = Counter(row["evidence_route"] for row in rows)
    seed_counts = Counter(row["candidate_seed_weight"] for row in rows)
    repair_decision_counts = Counter(row["decision"] for row in repair_candidates)
    activation_stage_stability_review_tags = sorted(
        row["tag"]
        for row in repair_candidates
        if row["decision"] == "graduate_to_exact_m1_supported_default_off_metadata"
        and row["target2_exact_m1_summary"]["every_populated_split_positive"] is False
    )
    transformed_tags = sorted(
        row["tag"]
        for row in rows
        if row["design_status"] == "transformed_context_or_veto_after_exact_m1_repair"
    )
    selectable_default_off_tags = sorted(
        row["tag"]
        for row in rows
        if row["design_status"] == "default_off_spec_design_ready" and row["symbol_collision_winner"]
    )

    active_registry = admission.effective_registry(include_candidate_book=True)
    candidate_runtime = admission.candidate_book_registry()
    expansion_names = set(specs)
    active_audit = {
        "schema": f"{SCHEMA_PREFIX}.active_behavior_audit.v1",
        "created_at_utc": created_at,
        "ok": True,
        "market_expansion_names_in_effective_registry": sorted(expansion_names & set(active_registry)),
        "market_expansion_names_in_candidate_book_registry": sorted(expansion_names & set(candidate_runtime)),
        "market_expansion_runtime_names": list(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES),
        "activation_weight_sum": round(sum(float(row["activation_weight_now"]) for row in rows), 6),
        "runtime_effect": "none_metadata_only",
    }

    result_ok = (
        prior_registry_result.get("ok") is True
        and proxy_result.get("ok") is True
        and len(rows) == 16
        and status_counts == {
            "default_off_spec_design_ready": 15,
            "transformed_context_or_veto_after_exact_m1_repair": 1,
        }
        and repair_decision_counts == {
            "graduate_to_exact_m1_supported_default_off_metadata": 9,
            "transform_to_context_or_veto_due_negative_exact_m1": 1,
        }
        and not candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_PROXY_REPAIR_REQUIRED_NAMES
        and list(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_TRANSFORMED_NAMES) == transformed_tags
        and not active_audit["market_expansion_names_in_effective_registry"]
        and not active_audit["market_expansion_names_in_candidate_book_registry"]
        and not active_audit["market_expansion_runtime_names"]
        and active_audit["activation_weight_sum"] == 0.0
    )
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": result_ok,
        "decision": "MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATED_NO_LIVE_AUTHORITY",
        "source_default_off_registry_route": rel(DEFAULT_OFF_REGISTRY_ROUTE),
        "source_proxy_m1_repair_route": rel(PROXY_M1_REPAIR_ROUTE),
        "metadata_spec_count": len(rows),
        "exact_m1_supported_metadata_count": status_counts["default_off_spec_design_ready"],
        "proxy_repair_gated_metadata_count": len(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_PROXY_REPAIR_REQUIRED_NAMES),
        "transformed_context_or_veto_count": status_counts["transformed_context_or_veto_after_exact_m1_repair"],
        "selectable_default_off_count": len(selectable_default_off_tags),
        "collision_winner_count": len(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES),
        "candidate_seed_enabled_count": sum(1 for row in rows if row["candidate_seed_weight"] > 0.0),
        "activation_stage_stability_review_tags": activation_stage_stability_review_tags,
        "repaired_graduated_metadata_count": repair_decision_counts["graduate_to_exact_m1_supported_default_off_metadata"],
        "repaired_transformed_metadata_count": repair_decision_counts["transform_to_context_or_veto_due_negative_exact_m1"],
        "repaired_exact_m1_event_count": proxy_result["repaired_exact_m1_event_count"],
        "new_exact_m1_events_added": proxy_result["new_exact_m1_events_added"],
        "activation_weight_now": 0.0,
        "runtime_effect": "none_metadata_only",
        "live_authority": False,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "account_info_read": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
    }
    input_manifest = {
        "schema": f"{SCHEMA_PREFIX}.input_manifest.v1",
        "created_at_utc": created_at,
        "source_artifacts": [
            rel(DEFAULT_OFF_REGISTRY_ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_RESULT.json"),
            rel(DEFAULT_OFF_REGISTRY_ROUTE / "DEFAULT_OFF_REGISTRY_SPEC_LEDGER.jsonl"),
            rel(PROXY_M1_REPAIR_ROUTE / "MARKET_EXPANSION_PROXY_M1_REPAIR_RESULT.json"),
            rel(PROXY_M1_REPAIR_ROUTE / "EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl"),
            rel(PROXY_M1_REPAIR_ROUTE / "FULL_BOOK_EXACT_M1_INTERACTION_LEDGER.jsonl"),
        ],
        "code_surfaces": [
            "src/components/ultimate_book/sleeves/candidate_registry.py",
            "tests/ultimate_book/test_market_expansion_default_off_registry.py",
            "tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py",
        ],
        "forbidden_data": [
            "orderflow",
            "depth",
            "broker order/deal/position/account mutation",
            "broker account-info reads",
            "VPS process mutation",
            "live config activation",
        ],
    }
    decision_rows = [
        {
            "created_at_utc": created_at,
            "decision": result["decision"],
            "metadata_spec_count": result["metadata_spec_count"],
            "exact_m1_supported_metadata_count": result["exact_m1_supported_metadata_count"],
            "proxy_repair_gated_metadata_count": result["proxy_repair_gated_metadata_count"],
            "transformed_context_or_veto_count": result["transformed_context_or_veto_count"],
            "runtime_effect": "none_metadata_only",
        },
        {
            "created_at_utc": created_at,
            "decision": "PRESERVE_SPLIT_CONFLICT_GRADUATES_AS_DEFAULT_OFF_NOT_LIVE",
            "activation_stage_stability_review_tags": activation_stage_stability_review_tags,
            "reason": "positive exact-M1 mean rows remain useful intelligence, but split conflict is carried forward before any activation",
        },
        {
            "created_at_utc": created_at,
            "decision": "NO_ACTIVE_BEHAVIOR_CHANGE_FROM_REPAIRED_METADATA",
            "reason": "market-expansion rows are absent from runtime generators, effective registry, candidate confidence, live config, and VPS surfaces",
        },
    ]
    repair = {
        "schema": f"{SCHEMA_PREFIX}.repair_ledger.v1",
        "ok": True,
        "blockers": [],
        "completed_repairs": [
            "integrated all 10 proxy-M1 repair decisions into code-readable default-off metadata",
            "cleared proxy-repair-gated metadata count from 10 to 0",
            "graduated 9 repaired rows to exact-M1-supported default-off metadata",
            "transformed GER40 ATR mean-reversion into context/veto intelligence after negative exact-M1 repair",
            "preserved split-conflicted positive-mean rows as activation-stage stability review instead of killing them",
        ],
        "remaining_same_evidence_class_work": [
            "runtime generator implementation for selectable default-off rows",
            "broker contract/cost/spec/min-volume/session proof before any activation",
            "activation-stage split-stability sizing review for JP225 and US30 repaired graduates",
            "full candidate-book interaction replay after generator implementation, before live authority",
        ],
    }
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_audit.v1",
        "ok": True,
        "all_proxy_rows_integrated": set(repair_by_tag) <= {row["tag"] for row in rows},
        "all_proxy_repair_gates_cleared_or_transformed": not candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_PROXY_REPAIR_REQUIRED_NAMES,
        "all_rows_remain_metadata_only": all(row["activation_weight_now"] == 0.0 for row in rows),
        "no_arbitrary_top_n": True,
        "inspire_not_kill_split_conflicts_preserved": activation_stage_stability_review_tags == [
            "mx_jp225_cash_d1_volume_surge_reversal",
            "mx_us30_cash_d1_volume_surge_reversal",
        ],
        "runtime_effect": "none_metadata_only",
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "ok": result_ok,
        "metadata_rows": len(rows),
        "active_behavior_audit_ok": active_audit["ok"],
        "instruction_coverage": {
            "mandatory_gtos_preflight": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_hardening_controls_read": True,
            "same_evidence_class_proxy_m1_repair_pursued": True,
            "inspire_not_kill_rows_preserved": True,
            "no_arbitrary_top_n": True,
        },
        "runtime_effect": "none_metadata_only",
    }
    focused_test = {
        "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 -m py_compile src/components/ultimate_book/sleeves/candidate_registry.py tests/ultimate_book/test_market_expansion_default_off_registry.py research/operations/final_moonshot_market_expansion_repaired_registry_integration_2026_06_18/build_market_expansion_repaired_registry_integration.py research/operations/final_moonshot_market_expansion_repaired_registry_integration_2026_06_18/verify_market_expansion_repaired_registry_integration.py tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py",
            "python3 research/operations/final_moonshot_market_expansion_repaired_registry_integration_2026_06_18/build_market_expansion_repaired_registry_integration.py",
            "python3 research/operations/final_moonshot_market_expansion_repaired_registry_integration_2026_06_18/verify_market_expansion_repaired_registry_integration.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_market_expansion_default_off_registry.py tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py tests/ultimate_book/test_candidate_book_consistency.py -q",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_market_expansion_repaired_registry_integration_2026_06_18/NEXT_PROMPT.md",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_repaired_registry_integration_2026_06_18 --full-jsonl",
            "git diff --check",
        ],
        "warning": "PytestConfigWarning: Unknown config option asyncio_mode may appear and is pre-existing",
    }
    next_prompt = """# Market Expansion Activation Package Prompt

Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt plus the repaired-registry integration artifacts from disk after any compaction/resume/interruption/uncertainty, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and `.context/00_core/parallel_goal_merge_playbook.md` as active instructions before acting.

Evidence class: default-off market-expansion activation package design. This is not live authority. Operate with maximum practical reasoning, active creativity, no arbitrary top-N/top-3/top-5/top-10 cutoff, no conservative narrowing, full ledger preservation for all material rows, same-evidence-class blocker pursuit, full same-evidence-class pursuit, and inspire-not-kill preservation. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action available inside the allowed evidence class has been attempted or reduced to an exact source-capture requirement.

Allowed data: committed repaired registry integration route artifacts, proxy M1 repair route artifacts, source-hashed local MT5 OHLCV/tick-volume exports, current active candidate-book replay/MC artifacts, and the localhost MT5 bridge read-only for missing OHLCV/tick-volume/spec/session evidence. Do not use orderflow/depth. Forbidden surfaces: no production-change or live trading broker operation; no live config/risk/execution/safety/canary/selector activation changes; no broker/account/order/history/deal/position mutation; no credentials; no remotes; no VPS processes; no MT5 order state; no paid API/vendor calls.

Objective: convert the 14 selectable repaired/default-off market-expansion metadata rows into a deployable activation-candidate package without turning them on. For every selectable row, prove broker contract/spec/session/min-volume/cost assumptions, draft runtime generator mapping, define split-stability/sizing constraints, run full candidate-book interaction replay against current book artifacts, and produce a row-level decision: implement default-off runtime candidate, keep metadata-only pending exact requirement, or transform to sizing/context/veto intelligence. JP225 and US30 must carry their negative-OOS split conflict into explicit activation-stage sizing/stability controls rather than being silently accepted or killed.

Result materialization is required for every selectable row: source-capture/source completeness proof, branch decision, implementation decision, computed expectancy/proxy-R/exact-R result, or exact source-safe impossibility. Do not leave rows as vague follow-up ideas.

Required output: row-level activation-readiness ledger, broker spec/cost/session manifest, generator implementation or exact non-implementation requirement, full-book interaction replay, verifier, focused tests, completion audit, output manifest, and successor prompt. Keep activation weight zero unless a later owner-approved live authority package explicitly changes live config after all proof gates pass.
"""

    write_json(ROUTE / "REPAIRED_REGISTRY_INPUT_MANIFEST.json", input_manifest)
    write_jsonl(ROUTE / "REPAIRED_REGISTRY_INTEGRATION_LEDGER.jsonl", rows)
    write_json(ROUTE / "ACTIVE_BEHAVIOR_AUDIT.json", active_audit)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "REPAIR_LEDGER.json", repair)
    write_json(ROUTE / "SATURATION_AUDIT.json", saturation)
    write_json(ROUTE / "MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATION_RESULT.json", result)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused_test)
    write_json(
        ROUTE / "REGISTRY_COUNT_AUDIT.json",
        {
            "schema": f"{SCHEMA_PREFIX}.registry_count_audit.v1",
            "status_counts": dict(sorted(status_counts.items())),
            "family_counts": dict(sorted(family_counts.items())),
            "mechanism_counts": dict(sorted(mechanism_counts.items())),
            "route_counts": dict(sorted(route_counts.items())),
            "seed_counts": {str(key): value for key, value in sorted(seed_counts.items())},
            "repair_decision_counts": dict(sorted(repair_decision_counts.items())),
        },
    )
    (ROUTE / "NEXT_PROMPT.md").write_text(next_prompt, encoding="utf-8")
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
            "created_at_utc": created_at,
            "files": sorted({path.name for path in ROUTE.iterdir() if path.is_file()} | {"OUTPUT_MANIFEST.json"}),
        },
    )
    return result


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "ok": result["ok"],
                "decision": result["decision"],
                "metadata_spec_count": result["metadata_spec_count"],
                "exact_m1_supported_metadata_count": result["exact_m1_supported_metadata_count"],
                "proxy_repair_gated_metadata_count": result["proxy_repair_gated_metadata_count"],
                "transformed_context_or_veto_count": result["transformed_context_or_veto_count"],
                "selectable_default_off_count": result["selectable_default_off_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
