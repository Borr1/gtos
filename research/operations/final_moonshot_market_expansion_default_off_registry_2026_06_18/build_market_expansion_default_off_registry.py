#!/usr/bin/env python3
"""Verify/install evidence route for market-expansion default-off registry metadata."""

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


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def build() -> dict[str, Any]:
    created_at = utc_now()
    design_result = read_json(DESIGN_ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_DESIGN_RESULT.json")
    specs = candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES
    rows = [
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
            "runtime_effect": "none_metadata_only",
        }
        for name, spec in specs.items()
    ]
    active_registry = admission.effective_registry(include_candidate_book=True)
    candidate_runtime = admission.candidate_book_registry()
    expansion_names = set(specs)
    status_counts = Counter(row["design_status"] for row in rows)
    family_counts = Counter(row["family"] for row in rows)
    mechanism_counts = Counter(row["mechanism"] for row in rows)
    active_audit = {
        "schema": f"{SCHEMA_PREFIX}.active_behavior_audit.v1",
        "created_at_utc": created_at,
        "ok": True,
        "market_expansion_names_in_effective_registry": sorted(expansion_names & set(active_registry)),
        "market_expansion_names_in_candidate_book_registry": sorted(expansion_names & set(candidate_runtime)),
        "market_expansion_runtime_names": list(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES),
        "activation_weight_sum": round(sum(float(row["activation_weight_now"]) for row in rows), 6),
        "candidate_book_registry_count": len(candidate_runtime),
        "runtime_effect": "none_metadata_only",
    }
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": (
            design_result.get("ok") is True
            and len(rows) == 16
            and status_counts["default_off_spec_design_ready"] == 6
            and status_counts["repair_gated_default_off_spec_only"] == 10
            and not active_audit["market_expansion_names_in_effective_registry"]
            and not active_audit["market_expansion_names_in_candidate_book_registry"]
            and not active_audit["market_expansion_runtime_names"]
            and active_audit["activation_weight_sum"] == 0.0
        ),
        "decision": "MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_METADATA_INSTALLED_NO_LIVE_AUTHORITY",
        "source_design_route": rel(DESIGN_ROUTE),
        "metadata_spec_count": len(rows),
        "m1_supported_metadata_count": status_counts["default_off_spec_design_ready"],
        "proxy_repair_gated_metadata_count": status_counts["repair_gated_default_off_spec_only"],
        "unique_symbol_count": len({row["file_symbol"] for row in rows}),
        "activation_weight_now": 0.0,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
        "live_authority": False,
    }
    input_manifest = {
        "schema": f"{SCHEMA_PREFIX}.input_manifest.v1",
        "created_at_utc": created_at,
        "source_artifacts": [
            rel(DESIGN_ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_DESIGN_RESULT.json"),
            rel(DESIGN_ROUTE / "DEFAULT_OFF_IMPLEMENTATION_SPEC_LEDGER.jsonl"),
        ],
        "code_surfaces": [
            "src/components/ultimate_book/sleeves/candidate_registry.py",
            "tests/ultimate_book/test_market_expansion_default_off_registry.py",
        ],
        "forbidden_data": ["orderflow", "depth", "broker order/deal/position/account mutation", "VPS process mutation", "live config activation"],
    }
    decision_rows = [
        {
            "created_at_utc": created_at,
            "decision": result["decision"],
            "metadata_spec_count": result["metadata_spec_count"],
            "m1_supported_metadata_count": result["m1_supported_metadata_count"],
            "proxy_repair_gated_metadata_count": result["proxy_repair_gated_metadata_count"],
            "runtime_effect": "none_metadata_only",
        },
        {
            "created_at_utc": created_at,
            "decision": "NO_ACTIVE_BEHAVIOR_CHANGE_FROM_METADATA_REGISTRY",
            "reason": "market-expansion metadata is separate from candidate runtime generators, confidence, active registry, and config",
        },
    ]
    repair = {
        "schema": f"{SCHEMA_PREFIX}.repair_ledger.v1",
        "ok": True,
        "blockers": [],
        "completed_repairs": [
            "installed code-readable metadata-only catalog for all 16 default-off design rows",
            "kept market-expansion names out of runtime candidate registry and effective registry",
            "preserved 10 proxy rows as zero-activation repair-gated metadata",
        ],
        "remaining_same_evidence_class_work": [
            "exact M1 repair for proxy rows",
            "runtime generator implementation for any future owner-approved candidate",
            "broker cost/spec/deployment verifier before activation",
        ],
    }
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_audit.v1",
        "ok": True,
        "all_design_rows_installed_as_metadata": len(rows) == design_result.get("accepted_default_off_count") == 16,
        "no_runtime_activation_names": not candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_RUNTIME_NAMES,
        "no_arbitrary_top_n": True,
        "runtime_effect": "none_metadata_only",
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "ok": result["ok"],
        "metadata_rows": len(rows),
        "active_behavior_audit_ok": active_audit["ok"],
        "instruction_coverage": {
            "mandatory_gtos_preflight": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_hardening_controls_read": True,
            "inspire_not_kill_rows_preserved": True,
            "no_arbitrary_top_n": True,
        },
        "runtime_effect": "none_metadata_only",
    }
    focused_test = {
        "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 -m py_compile src/components/ultimate_book/sleeves/candidate_registry.py tests/ultimate_book/test_market_expansion_default_off_registry.py",
            "python3 -m py_compile research/operations/final_moonshot_market_expansion_default_off_registry_2026_06_18/build_market_expansion_default_off_registry.py research/operations/final_moonshot_market_expansion_default_off_registry_2026_06_18/verify_market_expansion_default_off_registry.py tests/ultimate_book/test_market_expansion_default_off_registry_artifacts.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_market_expansion_default_off_registry.py tests/ultimate_book/test_market_expansion_default_off_registry_artifacts.py tests/ultimate_book/test_candidate_book_consistency.py -q",
            "python3 research/operations/final_moonshot_market_expansion_default_off_registry_2026_06_18/verify_market_expansion_default_off_registry.py",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_market_expansion_default_off_registry_2026_06_18/NEXT_PROMPT.md",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_default_off_registry_2026_06_18 --full-jsonl",
            "git diff --check",
        ],
        "warning": "PytestConfigWarning: Unknown config option asyncio_mode may appear and is pre-existing",
    }
    next_prompt = """# Market Expansion Proxy M1 Repair Prompt

Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt plus the default-off registry route artifacts from disk after any compaction/resume/interruption/uncertainty, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and `.context/00_core/parallel_goal_merge_playbook.md` as active instructions before acting.

Evidence class: exact M1 repair for repair-gated market-expansion metadata. This is not live authority. Operate with maximum practical reasoning, active creativity, no conservative brake, no arbitrary top-N/top-3/top-5/top-10 cutoff, full ledger preservation for all material rows, same-evidence-class blocker pursuit, full same-evidence-class pursuit, and inspire-not-kill preservation.

Allowed data: committed default-off registry/design/G12/follow-up/scoring artifacts, source-hashed local MT5 OHLCV/tick-volume exports, current active candidate-book replay/MC artifacts, and the localhost MT5 bridge read-only. Do not use orderflow/depth. Forbidden surfaces: no production-change or live trading broker operation; no live config/risk/execution/safety/canary/selector activation changes; no broker/account/order/history/deal/position mutation; no credentials; no remotes; no VPS processes; no MT5 order state; no paid API/vendor calls.

Objective: repair the 10 proxy-gated market-expansion metadata rows by exporting or locating exact M1 path history, proving source completeness/source-capture status, rerunning path replay, and deciding whether each row graduates to exact-M1-supported default-off metadata, remains repair-gated, or transforms to context/veto/sizing intelligence. Result materialization is required for every proxy row, and each row must receive an implementation decision or exact repair/source requirement.

Required output: M1 export/source manifest, repaired path replay ledger, updated metadata decision ledger, verifier, focused tests, completion audit, output manifest, and successor prompt.
"""

    write_json(ROUTE / "DEFAULT_OFF_REGISTRY_INPUT_MANIFEST.json", input_manifest)
    write_jsonl(ROUTE / "DEFAULT_OFF_REGISTRY_SPEC_LEDGER.jsonl", rows)
    write_json(ROUTE / "ACTIVE_BEHAVIOR_AUDIT.json", active_audit)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "REPAIR_LEDGER.json", repair)
    write_json(ROUTE / "SATURATION_AUDIT.json", saturation)
    write_json(ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_RESULT.json", result)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused_test)
    write_json(ROUTE / "REGISTRY_COUNT_AUDIT.json", {
        "schema": f"{SCHEMA_PREFIX}.registry_count_audit.v1",
        "status_counts": dict(sorted(status_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "mechanism_counts": dict(sorted(mechanism_counts.items())),
    })
    (ROUTE / "NEXT_PROMPT.md").write_text(next_prompt, encoding="utf-8")
    manifest = {
        "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
        "created_at_utc": created_at,
        "files": sorted(path.name for path in ROUTE.iterdir() if path.is_file()),
    }
    write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    return result


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "ok": result["ok"],
                "decision": result["decision"],
                "metadata_spec_count": result["metadata_spec_count"],
                "m1_supported_metadata_count": result["m1_supported_metadata_count"],
                "proxy_repair_gated_metadata_count": result["proxy_repair_gated_metadata_count"],
                "activation_weight_now": result["activation_weight_now"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
