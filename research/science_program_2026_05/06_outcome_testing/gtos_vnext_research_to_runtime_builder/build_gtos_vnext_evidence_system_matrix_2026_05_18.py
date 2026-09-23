from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "GTOS_VNEXT_RESEARCH_TO_RUNTIME_BUILDER"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
MOONSHOT = Path("C:/tmp/")

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.gtos_vnext_evidence_system import (  # noqa: E402
    DEFAULT_SOURCE_SPECS,
    SCHEMA_VERSION,
    SURFACE,
    build_evidence_matrix,
    build_instruction_coverage_rows,
    build_runtime_architecture_ledger,
    find_safety_issues,
    rows_for_target,
    sha256_path,
    summarize_exact_proxy_expectancy,
    summarize_matrix,
    write_json,
    write_jsonl,
)


MATRIX = ROUTE_DIR / f"GTOS_VNEXT_EVIDENCE_TO_SYSTEM_BUILD_MATRIX_{DATE}.jsonl"
SOURCE_INVENTORY = ROUTE_DIR / f"GTOS_VNEXT_SOURCE_INVENTORY_{DATE}.jsonl"
RUNTIME_ARCHITECTURE = ROUTE_DIR / f"GTOS_VNEXT_RUNTIME_ARCHITECTURE_DECISION_LEDGER_{DATE}.jsonl"
SCORER_FILTER_ROUTER = ROUTE_DIR / f"GTOS_VNEXT_SCORER_FILTER_ROUTER_IMPLEMENTATION_LEDGER_{DATE}.jsonl"
AI_DECISION = ROUTE_DIR / f"GTOS_VNEXT_AI_DECISION_ARCHITECTURE_LEDGER_{DATE}.jsonl"
GATE_RISK_EXIT = ROUTE_DIR / f"GTOS_VNEXT_GATE_FILTER_SELECTOR_RISK_EXIT_LEDGER_{DATE}.jsonl"
MARKET_TIMEFRAME = ROUTE_DIR / f"GTOS_VNEXT_MARKET_TIMEFRAME_EXPANSION_LEDGER_{DATE}.jsonl"
LEGACY_MERGER = ROUTE_DIR / f"GTOS_VNEXT_LEGACY_RESEARCH_MERGER_LEDGER_{DATE}.jsonl"
EXACT_PROXY_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_EXACT_PROXY_R_EXPECTANCY_SUMMARY_{DATE}.json"
INSTRUCTION_COVERAGE = ROUTE_DIR / f"GTOS_VNEXT_INSTRUCTION_COVERAGE_LEDGER_{DATE}.jsonl"
COMPLETION_AUDIT = ROUTE_DIR / f"GTOS_VNEXT_CHECKPOINT_COMPLETION_AUDIT_{DATE}.json"
SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_BUILD_MATRIX_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"GTOS_VNEXT_OUTPUT_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def run_git(cwd: Path, *args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "cwd": str(cwd).replace("\\", "/"),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def run_git_safe(cwd: Path, *args: str) -> dict[str, Any]:
    return run_git(cwd, "-c", f"safe.directory={str(cwd).replace('\\', '/')}", *args)


def moonshot_snapshot() -> dict[str, Any]:
    if not MOONSHOT.exists():
        return {"path": str(MOONSHOT).replace("\\", "/"), "exists": False}
    return {
        "path": str(MOONSHOT).replace("\\", "/"),
        "exists": True,
        "head": run_git_safe(MOONSHOT, "rev-parse", "HEAD"),
        "branch": run_git_safe(MOONSHOT, "branch", "--show-current"),
        "status_short": run_git_safe(MOONSHOT, "status", "--short", "--branch"),
        "consumption_mode": "READ_ONLY_SOURCE_SNAPSHOT",
    }


def output_surface(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "lines": count_lines(path),
        "sha256": sha256_path(path),
    }


def code_surface(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "lines": count_lines(path) if path.exists() else 0,
        "sha256": sha256_path(path) if path.exists() else "",
    }


def build_completion_audit(summary: dict[str, Any], safety_issues: list[str]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": summary["generated_utc"],
        "checkpoint_status": "CHECKPOINT_NOT_FINAL_72H_OBJECTIVE_REMAINS_ACTIVE",
        "can_mark_goal_complete": False,
        "early_finish_allowed": False,
        "matrix_rows": summary["matrix_rows"],
        "all_source_rows_preserved": summary["all_source_rows_preserved"],
        "safety_issue_count": len(safety_issues),
        "safety_issues": safety_issues[:25],
        "runtime_enablement": "NONE_DEFAULT_OFF_ONLY",
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "next_required_action": (
            "Promote strongest default-off matrix surfaces into callable scorer/filter/router registries, "
            "then run replay/verifier surfaces without enabling runtime."
        ),
    }


def build() -> dict[str, Any]:
    generated = utc_now()
    matrix_rows, inventory_rows = build_evidence_matrix(REPO, DEFAULT_SOURCE_SPECS)
    runtime_architecture_rows = build_runtime_architecture_ledger(matrix_rows, inventory_rows)
    scorer_rows = rows_for_target(matrix_rows, "scorer_filter_router")
    ai_rows = rows_for_target(matrix_rows, "ai_decision_architecture")
    gate_rows = rows_for_target(matrix_rows, "gate_filter_selector_risk_exit")
    market_rows = rows_for_target(matrix_rows, "market_timeframe_expansion")
    legacy_rows = rows_for_target(matrix_rows, "legacy_research_merger")
    exact_proxy_summary = summarize_exact_proxy_expectancy(rows_for_target(matrix_rows, "exact_proxy_r"))
    instruction_rows = build_instruction_coverage_rows(matrix_rows, inventory_rows)
    safety_issues = find_safety_issues(matrix_rows)

    write_jsonl(MATRIX, matrix_rows)
    write_jsonl(SOURCE_INVENTORY, inventory_rows)
    write_jsonl(RUNTIME_ARCHITECTURE, runtime_architecture_rows)
    write_jsonl(SCORER_FILTER_ROUTER, scorer_rows)
    write_jsonl(AI_DECISION, ai_rows)
    write_jsonl(GATE_RISK_EXIT, gate_rows)
    write_jsonl(MARKET_TIMEFRAME, market_rows)
    write_jsonl(LEGACY_MERGER, legacy_rows)
    write_json(EXACT_PROXY_SUMMARY, exact_proxy_summary)
    write_jsonl(INSTRUCTION_COVERAGE, instruction_rows)

    matrix_summary = summarize_matrix(matrix_rows, inventory_rows)
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "main_repo_head_at_build": run_git(REPO, "rev-parse", "HEAD"),
        "main_repo_status_short_at_build": run_git(REPO, "status", "--short", "--branch"),
        "moonshot_snapshot": moonshot_snapshot(),
        "source_spec_count": len(DEFAULT_SOURCE_SPECS),
        "source_specs": [
            {
                "source_name": spec.source_name,
                "evidence_family": spec.evidence_family,
                "source_role": spec.source_role,
                "path": str(spec.path).replace("\\", "/"),
                "ledger_targets": list(spec.ledger_targets),
            }
            for spec in DEFAULT_SOURCE_SPECS
        ],
        "output_row_counts": {
            "matrix": len(matrix_rows),
            "source_inventory": len(inventory_rows),
            "runtime_architecture": len(runtime_architecture_rows),
            "scorer_filter_router": len(scorer_rows),
            "ai_decision_architecture": len(ai_rows),
            "gate_filter_selector_risk_exit": len(gate_rows),
            "market_timeframe_expansion": len(market_rows),
            "legacy_research_merger": len(legacy_rows),
            "instruction_coverage": len(instruction_rows),
        },
        "code_surfaces": [
            code_surface(REPO / SURFACE),
            code_surface(REPO / "tests/research_infra/test_gtos_vnext_evidence_system.py"),
            code_surface(Path(__file__)),
        ],
        **matrix_summary,
    }
    write_json(SUMMARY, summary)
    write_json(COMPLETION_AUDIT, build_completion_audit(summary, safety_issues))

    outputs = [
        MATRIX,
        SOURCE_INVENTORY,
        RUNTIME_ARCHITECTURE,
        SCORER_FILTER_ROUTER,
        AI_DECISION,
        GATE_RISK_EXIT,
        MARKET_TIMEFRAME,
        LEGACY_MERGER,
        EXACT_PROXY_SUMMARY,
        INSTRUCTION_COVERAGE,
        COMPLETION_AUDIT,
        SUMMARY,
    ]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "outputs": [output_surface(path) for path in outputs],
        "source_inventory_sha256": sha256_path(SOURCE_INVENTORY),
        "matrix_sha256": sha256_path(MATRIX),
        "completion_audit_sha256": sha256_path(COMPLETION_AUDIT),
        "builder": display_path(Path(__file__)),
    }
    write_json(MANIFEST, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
