#!/usr/bin/env python3
"""Verify the market-expansion default-off registry metadata lane."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
DESIGN_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_default_off_design_2026_06_18"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_default_off_registry"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.ultimate_book import admission  # noqa: E402
from src.components.ultimate_book.sleeves import candidate_registry  # noqa: E402


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _check(name: str, passed: bool, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail or {}}


def main() -> int:
    created_at = datetime.now(UTC).isoformat()
    result = _load_json(ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_RESULT.json")
    active_audit = _load_json(ROUTE / "ACTIVE_BEHAVIOR_AUDIT.json")
    count_audit = _load_json(ROUTE / "REGISTRY_COUNT_AUDIT.json")
    completion = _load_json(ROUTE / "COMPLETION_AUDIT.json")
    manifest = _load_json(ROUTE / "OUTPUT_MANIFEST.json")
    design_result = _load_json(DESIGN_ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_DESIGN_RESULT.json")
    route_rows = _load_jsonl(ROUTE / "DEFAULT_OFF_REGISTRY_SPEC_LEDGER.jsonl")
    design_rows = _load_jsonl(DESIGN_ROUTE / "DEFAULT_OFF_IMPLEMENTATION_SPEC_LEDGER.jsonl")

    specs = candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES
    route_by_tag = {row["tag"]: row for row in route_rows}
    design_by_tag = {f"mx_{row['file_symbol'].lower()}_{row['mechanism']}": row for row in design_rows}
    expansion_names = set(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_NAMES)
    effective_with_candidates = admission.effective_registry(include_candidate_book=True)
    candidate_runtime = admission.candidate_book_registry()

    code_rows = [
        {
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
            "target2_m15_proxy_event_count": spec.target2_m15_proxy_event_count,
            "target2_ordered_mean_r": spec.target2_ordered_mean_r,
            "full_book_delta_sharpe": spec.full_book_delta_sharpe,
            "evidence_route": spec.evidence_route,
        }
        for name, spec in specs.items()
    ]
    code_by_tag = {row["tag"]: row for row in code_rows}
    status_counts = Counter(row["design_status"] for row in route_rows)
    family_counts = Counter(row["family"] for row in route_rows)
    mechanism_counts = Counter(row["mechanism"] for row in route_rows)
    seed_weight_by_status = {
        status: sorted({row["candidate_seed_weight"] for row in route_rows if row["design_status"] == status})
        for status in status_counts
    }
    collision_losers = sorted(row["tag"] for row in route_rows if not row["symbol_collision_winner"])

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
        "target2_m15_proxy_event_count",
        "target2_ordered_mean_r",
        "full_book_delta_sharpe",
    )
    mismatches: list[dict[str, Any]] = []
    for tag, route_row in sorted(route_by_tag.items()):
        design_row = design_by_tag.get(tag)
        code_row = code_by_tag.get(tag)
        for field in parity_fields:
            if design_row is not None and route_row.get(field) != design_row.get(field):
                mismatches.append({"tag": tag, "source": "design", "field": field, "route": route_row.get(field), "expected": design_row.get(field)})
            if code_row is not None and route_row.get(field) != code_row.get(field):
                mismatches.append({"tag": tag, "source": "code", "field": field, "route": route_row.get(field), "expected": code_row.get(field)})

    checks = [
        _check(
            "result_and_design_route_ok",
            result.get("ok") is True and design_result.get("ok") is True,
            {"result_ok": result.get("ok"), "design_ok": design_result.get("ok")},
        ),
        _check(
            "all_sixteen_design_rows_installed",
            len(route_rows) == len(specs) == result.get("metadata_spec_count") == design_result.get("accepted_default_off_count") == 16,
            {
                "route_rows": len(route_rows),
                "code_specs": len(specs),
                "result_count": result.get("metadata_spec_count"),
                "design_count": design_result.get("accepted_default_off_count"),
            },
        ),
        _check(
            "status_counts_match_design",
            status_counts == {"default_off_spec_design_ready": 6, "repair_gated_default_off_spec_only": 10},
            {"status_counts": dict(status_counts)},
        ),
        _check(
            "family_and_mechanism_counts_match_g12_design",
            family_counts == {"crypto_alt_or_major": 3, "indices_context": 11, "jpy_fx": 2}
            and mechanism_counts == {"d1_atr_mean_reversion": 4, "d1_donchian_20_breakout": 4, "d1_volume_surge_reversal": 8},
            {"family_counts": dict(family_counts), "mechanism_counts": dict(mechanism_counts)},
        ),
        _check(
            "code_route_design_parity",
            not mismatches and set(route_by_tag) == set(design_by_tag) == set(code_by_tag),
            {
                "mismatch_count": len(mismatches),
                "sample_mismatches": mismatches[:10],
                "missing_from_route": sorted((set(design_by_tag) | set(code_by_tag)) - set(route_by_tag)),
                "missing_from_design": sorted(set(route_by_tag) - set(design_by_tag)),
                "missing_from_code": sorted(set(route_by_tag) - set(code_by_tag)),
            },
        ),
        _check(
            "metadata_is_inert_to_runtime_admission",
            not (expansion_names & set(effective_with_candidates))
            and not (expansion_names & set(candidate_runtime))
            and not set(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES),
            {
                "effective_intersection": sorted(expansion_names & set(effective_with_candidates)),
                "candidate_runtime_intersection": sorted(expansion_names & set(candidate_runtime)),
                "runtime_names": list(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES),
            },
        ),
        _check(
            "zero_activation_and_seed_gate_policy",
            all(row["activation_weight_now"] == 0.0 for row in route_rows)
            and seed_weight_by_status == {
                "default_off_spec_design_ready": [0.025],
                "repair_gated_default_off_spec_only": [0.0],
            },
            {
                "activation_weight_sum": sum(row["activation_weight_now"] for row in route_rows),
                "seed_weight_by_status": seed_weight_by_status,
            },
        ),
        _check(
            "collision_policy_preserved",
            collision_losers == [
                "mx_aus200_cash_d1_volume_surge_reversal",
                "mx_ger40_cash_d1_volume_surge_reversal",
            ],
            {"collision_losers": collision_losers},
        ),
        _check(
            "boundary_audits_close_live_surfaces",
            result.get("live_authority") is False
            and result.get("orderflow_used") is False
            and result.get("broker_or_order_mutation") is False
            and result.get("config_or_live_activation_changed") is False
            and result.get("vps_process_touched") is False
            and active_audit.get("runtime_effect") == "none_metadata_only"
            and completion.get("runtime_effect") == "none_metadata_only",
            {
                "live_authority": result.get("live_authority"),
                "orderflow_used": result.get("orderflow_used"),
                "broker_or_order_mutation": result.get("broker_or_order_mutation"),
                "config_or_live_activation_changed": result.get("config_or_live_activation_changed"),
                "vps_process_touched": result.get("vps_process_touched"),
                "active_runtime_effect": active_audit.get("runtime_effect"),
                "completion_runtime_effect": completion.get("runtime_effect"),
            },
        ),
        _check(
            "manifest_has_core_route_files",
            {
                "build_market_expansion_default_off_registry.py",
                "verify_market_expansion_default_off_registry.py",
                "DEFAULT_OFF_REGISTRY_SPEC_LEDGER.jsonl",
                "MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_RESULT.json",
                "ACTIVE_BEHAVIOR_AUDIT.json",
                "COMPLETION_AUDIT.json",
                "OUTPUT_MANIFEST.json",
                "NEXT_PROMPT.md",
            }
            <= set(manifest.get("files", [])),
            {"files": manifest.get("files", [])},
        ),
        _check(
            "count_audit_matches_route_rows",
            count_audit.get("status_counts") == dict(sorted(status_counts.items()))
            and count_audit.get("family_counts") == dict(sorted(family_counts.items()))
            and count_audit.get("mechanism_counts") == dict(sorted(mechanism_counts.items())),
            {"count_audit": count_audit},
        ),
    ]
    ok = all(check["passed"] for check in checks)
    verifier_result = {
        "schema": f"{SCHEMA_PREFIX}.verifier_result.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "decision": result.get("decision") if ok else "REPAIR_MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_METADATA",
        "issue_count": sum(1 for check in checks if not check["passed"]),
        "metadata_spec_count": len(route_rows),
        "m1_supported_metadata_count": status_counts["default_off_spec_design_ready"],
        "proxy_repair_gated_metadata_count": status_counts["repair_gated_default_off_spec_only"],
        "runtime_effect": "none_metadata_only",
        "live_authority": False,
        "checks": checks,
    }
    (ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_VERIFIER_RESULT.json").write_text(
        json.dumps(verifier_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": ok, "issue_count": verifier_result["issue_count"], "decision": verifier_result["decision"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
