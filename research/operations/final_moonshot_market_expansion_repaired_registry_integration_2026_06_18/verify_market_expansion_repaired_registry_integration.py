#!/usr/bin/env python3
"""Verify repaired market-expansion metadata registry integration artifacts."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def check(name: str, passed: bool, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail or {}}


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
    result = load_json(ROUTE / "MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATION_RESULT.json")
    active_audit = load_json(ROUTE / "ACTIVE_BEHAVIOR_AUDIT.json")
    count_audit = load_json(ROUTE / "REGISTRY_COUNT_AUDIT.json")
    completion = load_json(ROUTE / "COMPLETION_AUDIT.json")
    saturation = load_json(ROUTE / "SATURATION_AUDIT.json")
    repair = load_json(ROUTE / "REPAIR_LEDGER.json")
    manifest = load_json(ROUTE / "OUTPUT_MANIFEST.json")
    proxy_result = load_json(PROXY_M1_REPAIR_ROUTE / "MARKET_EXPANSION_PROXY_M1_REPAIR_RESULT.json")
    rows = load_jsonl(ROUTE / "REPAIRED_REGISTRY_INTEGRATION_LEDGER.jsonl")
    decisions = load_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    repair_candidates = load_jsonl(PROXY_M1_REPAIR_ROUTE / "EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl")
    interactions = load_jsonl(PROXY_M1_REPAIR_ROUTE / "FULL_BOOK_EXACT_M1_INTERACTION_LEDGER.jsonl")

    specs = candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES
    route_by_tag = {row["tag"]: row for row in rows}
    code_by_tag = {name: code_row(name, spec) for name, spec in specs.items()}
    repair_by_tag = {row["tag"]: row for row in repair_candidates}
    interaction_by_tag = {row["tag"]: row for row in interactions}
    expansion_names = set(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_NAMES)
    active_registry = admission.effective_registry(include_candidate_book=True)
    candidate_runtime = admission.candidate_book_registry()

    status_counts = Counter(row["design_status"] for row in rows)
    family_counts = Counter(row["family"] for row in rows)
    mechanism_counts = Counter(row["mechanism"] for row in rows)
    route_counts = Counter(row["evidence_route"] for row in rows)
    seed_counts = Counter(row["candidate_seed_weight"] for row in rows)
    repair_decision_counts = Counter(row["decision"] for row in repair_candidates)
    transformed_tags = sorted(
        row["tag"]
        for row in rows
        if row["design_status"] == "transformed_context_or_veto_after_exact_m1_repair"
    )
    collision_losers = sorted(row["tag"] for row in rows if not row["symbol_collision_winner"])
    selectable_default_off_tags = sorted(
        row["tag"]
        for row in rows
        if row["design_status"] == "default_off_spec_design_ready" and row["symbol_collision_winner"]
    )
    split_review_tags = sorted(
        repair_row["tag"]
        for repair_row in repair_candidates
        if repair_row["decision"] == "graduate_to_exact_m1_supported_default_off_metadata"
        and repair_row["target2_exact_m1_summary"]["every_populated_split_positive"] is False
    )

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
    for tag, route_row in sorted(route_by_tag.items()):
        code = code_by_tag.get(tag)
        for field in parity_fields:
            if code is None or route_row.get(field) != code.get(field):
                code_mismatches.append(
                    {
                        "tag": tag,
                        "field": field,
                        "route": route_row.get(field),
                        "code": None if code is None else code.get(field),
                    }
                )

    repair_mismatches: list[dict[str, Any]] = []
    for tag, repair_row in sorted(repair_by_tag.items()):
        route_row = route_by_tag.get(tag)
        if route_row is None:
            repair_mismatches.append({"tag": tag, "field": "missing_route_row"})
            continue
        summary = repair_row["target2_exact_m1_summary"]
        expected_status = (
            "default_off_spec_design_ready"
            if repair_row["decision"] == "graduate_to_exact_m1_supported_default_off_metadata"
            else "transformed_context_or_veto_after_exact_m1_repair"
        )
        expected_seed = 0.025 if expected_status == "default_off_spec_design_ready" and route_row["symbol_collision_winner"] else 0.0
        expected_fields = {
            "design_status": expected_status,
            "target2_exact_m1_event_count": repair_row["repaired_exact_m1_event_count"],
            "target2_remaining_path_gap_count": sum(
                int(value)
                for key, value in repair_row["target2_exact_m1_status_counts"].items()
                if key.startswith("no_m1_") or key == "geometry_not_reconstructable"
            ),
            "target2_ordered_mean_r": summary["mean_r"],
            "source_repair_decision": repair_row["decision"],
            "source_repair_exact_m1_mean_r": summary["mean_r"],
            "source_repair_every_populated_split_positive": summary["every_populated_split_positive"],
            "source_repair_new_exact_m1_events_added": repair_row["new_exact_m1_events_added"],
            "source_repair_coverage_ratio": repair_row["repaired_exact_m1_coverage_ratio"],
            "candidate_seed_weight": expected_seed,
        }
        if tag in interaction_by_tag:
            expected_fields["full_book_delta_sharpe"] = interaction_by_tag[tag]["delta_sharpe"]
            expected_fields["source_repair_full_book_delta_sharpe"] = interaction_by_tag[tag]["delta_sharpe"]
        for field, expected in expected_fields.items():
            if route_row.get(field) != expected:
                repair_mismatches.append({"tag": tag, "field": field, "route": route_row.get(field), "expected": expected})

    checks = [
        check(
            "result_completion_and_sources_ok",
            result.get("ok") is True
            and completion.get("ok") is True
            and saturation.get("ok") is True
            and repair.get("ok") is True
            and proxy_result.get("ok") is True,
            {
                "result_ok": result.get("ok"),
                "completion_ok": completion.get("ok"),
                "saturation_ok": saturation.get("ok"),
                "repair_ok": repair.get("ok"),
                "proxy_ok": proxy_result.get("ok"),
            },
        ),
        check(
            "registry_counts_match_repaired_state",
            len(rows) == len(specs) == result.get("metadata_spec_count") == 16
            and status_counts == {
                "default_off_spec_design_ready": 15,
                "transformed_context_or_veto_after_exact_m1_repair": 1,
            }
            and result.get("exact_m1_supported_metadata_count") == 15
            and result.get("proxy_repair_gated_metadata_count") == 0
            and result.get("transformed_context_or_veto_count") == 1,
            {
                "route_rows": len(rows),
                "code_specs": len(specs),
                "status_counts": dict(status_counts),
                "result_counts": {
                    "exact": result.get("exact_m1_supported_metadata_count"),
                    "proxy": result.get("proxy_repair_gated_metadata_count"),
                    "transformed": result.get("transformed_context_or_veto_count"),
                },
            },
        ),
        check(
            "repair_decisions_integrated",
            repair_decision_counts == {
                "graduate_to_exact_m1_supported_default_off_metadata": 9,
                "transform_to_context_or_veto_due_negative_exact_m1": 1,
            }
            and not repair_mismatches,
            {"repair_decision_counts": dict(repair_decision_counts), "sample_mismatches": repair_mismatches[:10]},
        ),
        check(
            "code_route_parity",
            not code_mismatches and set(route_by_tag) == set(code_by_tag),
            {
                "mismatch_count": len(code_mismatches),
                "sample_mismatches": code_mismatches[:10],
                "missing_from_route": sorted(set(code_by_tag) - set(route_by_tag)),
                "missing_from_code": sorted(set(route_by_tag) - set(code_by_tag)),
            },
        ),
        check(
            "candidate_tuples_reflect_repaired_state",
            len(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_M1_SUPPORTED_NAMES) == 15
            and candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_PROXY_REPAIR_REQUIRED_NAMES == ()
            and list(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_TRANSFORMED_NAMES) == transformed_tags
            and len(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES) == 14
            and candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES == (),
            {
                "m1_supported": len(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_M1_SUPPORTED_NAMES),
                "proxy_required": list(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_PROXY_REPAIR_REQUIRED_NAMES),
                "transformed": list(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_TRANSFORMED_NAMES),
                "collision_winners": len(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES),
                "runtime_names": list(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES),
            },
        ),
        check(
            "family_mechanism_seed_and_collision_counts",
            family_counts == {"crypto_alt_or_major": 3, "indices_context": 11, "jpy_fx": 2}
            and mechanism_counts == {
                "d1_atr_mean_reversion": 4,
                "d1_donchian_20_breakout": 4,
                "d1_volume_surge_reversal": 8,
            }
            and seed_counts == {0.025: 14, 0.0: 2}
            and collision_losers == [
                "mx_aus200_cash_d1_atr_mean_reversion",
                "mx_ger40_cash_d1_atr_mean_reversion",
            ]
            and len(selectable_default_off_tags) == 14,
            {
                "family_counts": dict(family_counts),
                "mechanism_counts": dict(mechanism_counts),
                "seed_counts": dict(seed_counts),
                "collision_losers": collision_losers,
                "selectable_default_off_count": len(selectable_default_off_tags),
            },
        ),
        check(
            "split_conflicts_preserved_for_activation_stage",
            split_review_tags == [
                "mx_jp225_cash_d1_volume_surge_reversal",
                "mx_us30_cash_d1_volume_surge_reversal",
            ]
            and result.get("activation_stage_stability_review_tags") == split_review_tags,
            {"split_review_tags": split_review_tags, "result_tags": result.get("activation_stage_stability_review_tags")},
        ),
        check(
            "runtime_and_live_boundaries_closed",
            not (expansion_names & set(active_registry))
            and not (expansion_names & set(candidate_runtime))
            and not set(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES)
            and all(row["activation_weight_now"] == 0.0 for row in rows)
            and active_audit.get("activation_weight_sum") == 0.0
            and result.get("live_authority") is False
            and result.get("orderflow_used") is False
            and result.get("broker_or_order_mutation") is False
            and result.get("account_info_read") is False
            and result.get("config_or_live_activation_changed") is False
            and result.get("vps_process_touched") is False,
            {
                "effective_intersection": sorted(expansion_names & set(active_registry)),
                "candidate_runtime_intersection": sorted(expansion_names & set(candidate_runtime)),
                "runtime_names": list(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES),
                "activation_weight_sum": active_audit.get("activation_weight_sum"),
            },
        ),
        check(
            "count_audit_matches_rows",
            count_audit.get("status_counts") == dict(sorted(status_counts.items()))
            and count_audit.get("family_counts") == dict(sorted(family_counts.items()))
            and count_audit.get("mechanism_counts") == dict(sorted(mechanism_counts.items()))
            and count_audit.get("route_counts") == dict(sorted(route_counts.items()))
            and count_audit.get("repair_decision_counts") == dict(sorted(repair_decision_counts.items())),
            {"count_audit": count_audit},
        ),
        check(
            "manifest_has_core_files",
            {
                "build_market_expansion_repaired_registry_integration.py",
                "verify_market_expansion_repaired_registry_integration.py",
                "MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATION_RESULT.json",
                "REPAIRED_REGISTRY_INTEGRATION_LEDGER.jsonl",
                "ACTIVE_BEHAVIOR_AUDIT.json",
                "REGISTRY_COUNT_AUDIT.json",
                "SATURATION_AUDIT.json",
                "COMPLETION_AUDIT.json",
                "FOCUSED_TEST_RESULT.json",
                "NEXT_PROMPT.md",
                "OUTPUT_MANIFEST.json",
            }
            <= set(manifest.get("files", [])),
            {"files": manifest.get("files", [])},
        ),
        check(
            "decisions_record_no_live_authority_and_split_review",
            any(row["decision"] == result.get("decision") for row in decisions)
            and any(row["decision"] == "PRESERVE_SPLIT_CONFLICT_GRADUATES_AS_DEFAULT_OFF_NOT_LIVE" for row in decisions)
            and any(row["decision"] == "NO_ACTIVE_BEHAVIOR_CHANGE_FROM_REPAIRED_METADATA" for row in decisions),
            {"decisions": [row["decision"] for row in decisions]},
        ),
    ]
    ok = all(item["passed"] for item in checks)
    verifier = {
        "schema": f"{SCHEMA_PREFIX}.verifier_result.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "decision": result.get("decision") if ok else "REPAIR_MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATION",
        "issue_count": sum(1 for item in checks if not item["passed"]),
        "metadata_spec_count": len(rows),
        "exact_m1_supported_metadata_count": status_counts["default_off_spec_design_ready"],
        "proxy_repair_gated_metadata_count": len(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_PROXY_REPAIR_REQUIRED_NAMES),
        "transformed_context_or_veto_count": status_counts["transformed_context_or_veto_after_exact_m1_repair"],
        "selectable_default_off_count": len(selectable_default_off_tags),
        "runtime_effect": "none_metadata_only",
        "live_authority": False,
        "checks": checks,
    }
    write_json(ROUTE / "MARKET_EXPANSION_REPAIRED_REGISTRY_INTEGRATION_VERIFIER_RESULT.json", verifier)
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            **manifest,
            "files": sorted(path.name for path in ROUTE.iterdir() if path.is_file()),
        },
    )
    print(json.dumps({"ok": ok, "issue_count": verifier["issue_count"], "decision": verifier["decision"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
