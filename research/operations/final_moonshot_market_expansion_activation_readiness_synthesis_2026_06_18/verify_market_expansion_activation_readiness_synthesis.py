#!/usr/bin/env python3
"""Verify market-expansion activation-readiness synthesis artifacts."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_activation_readiness_synthesis"
EXPECTED_DECISION = "MARKET_EXPANSION_ACTIVATION_READINESS_SYNTHESIS_READY_DEFAULT_OFF_NOT_PROMOTED"
EXPECTED_REQ_IDS = {
    "MX-READINESS-REQ-001",
    "MX-READINESS-REQ-002",
    "MX-READINESS-REQ-003",
    "MX-READINESS-REQ-004",
    "MX-READINESS-REQ-005",
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> int:
    created_at = utc_now()
    result = read_json(ROUTE / "MARKET_EXPANSION_ACTIVATION_READINESS_RESULT.json")
    summary = read_json(ROUTE / "CANDIDATE_AUTHORITY_SUMMARY.json")
    matrix = read_jsonl(ROUTE / "CANDIDATE_AUTHORITY_MATRIX.jsonl")
    requirements = read_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    boundary = read_jsonl(ROUTE / "PROMOTION_BOUNDARY_LEDGER.jsonl")
    local_repair = read_jsonl(ROUTE / "LOCAL_REPAIR_EXHAUSTION_LEDGER.jsonl")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    saturation = read_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json")
    forbidden = read_json(ROUTE / "FORBIDDEN_CALL_SCAN.json")

    req_ids = {row["requirement_id"] for row in requirements}
    boundary_status = {row["gate"]: row["status"] for row in boundary}
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check(
        "result_and_completion_ok",
        result["ok"] is True and completion["ok"] is True and saturation["ok"] is True,
        {"decision": result.get("decision"), "completion_ok": completion.get("ok"), "saturation_ok": saturation.get("ok")},
    )
    check(
        "decision_is_default_off_not_promoted",
        result["decision"] == EXPECTED_DECISION
        and result["live_authority"] is False
        and result["deployment_ready"] is False
        and result["promotion_ready"] is False
        and result["config_patch_applied"] is False,
        {
            "live_authority": result.get("live_authority"),
            "deployment_ready": result.get("deployment_ready"),
            "promotion_ready": result.get("promotion_ready"),
            "config_patch_applied": result.get("config_patch_applied"),
        },
    )
    check(
        "matrix_counts_expected",
        len(matrix) == 14
        and summary["candidate_count"] == 14
        and summary["default_off_code_package_ready_count"] == 14
        and summary["live_authority_ready_count"] == 0
        and summary["deployment_ready_count"] == 0
        and summary["promotion_ready_count"] == 0,
        summary,
    )
    check(
        "authority_subcounts_expected",
        summary["runtime_generator_parity_closed_count"] == 14
        and summary["broker_spec_snapshot_closed_count"] == 14
        and summary["profit_conversion_closed_count"] == 14
        and summary["source_cost_join_closed_count"] == 14
        and summary["explicit_session_table_closed_count"] == 0
        and summary["observed_m1_session_proxy_closed_count"] == 14,
        summary,
    )
    check(
        "fill_commission_swap_counts_expected",
        summary["direct_fill_slippage_closed_count"] == 7
        and summary["no_direct_fill_slippage_symbol_count"] == 7
        and summary["commission_direct_or_family_proxy_closed_count"] == 14
        and summary["direct_commission_authority_count"] == 7
        and summary["family_proxy_commission_authority_count"] == 7
        and summary["swap_point_mode_symbol_count"] == 11
        and summary["swap_mode5_formula_required_symbol_count"] == 3,
        summary,
    )
    check(
        "no_row_overclaims_live_authority",
        all(
            row["live_authority_ready"] is False
            and row["deployment_ready"] is False
            and row["promotion_ready"] is False
            and row["config_patch_applied"] is False
            for row in matrix
        ),
        {
            "live_authority_rows": sum(1 for row in matrix if row["live_authority_ready"]),
            "deployment_ready_rows": sum(1 for row in matrix if row["deployment_ready"]),
        },
    )
    check(
        "requirements_and_boundaries_preserved",
        req_ids == EXPECTED_REQ_IDS
        and boundary_status.get("default_off_code_package") == "ready_14_of_14"
        and boundary_status.get("live_authority") == "not_closed_0_of_14"
        and boundary_status.get("config_patch") == "not_applied"
        and boundary_status.get("owner_vps_action") == "required_not_executed_by_mac_route",
        {"req_ids": sorted(req_ids), "boundary_status": boundary_status},
    )
    check(
        "local_repair_paths_are_not_empty",
        len(local_repair) >= 7
        and {row["repair_family"] for row in local_repair}
        >= {
            "runtime_generator_parity",
            "observed_m1_session_proxy",
            "commission_family_transfer",
            "historical_fill_slippage",
            "swap_to_r",
            "explicit_session_table",
        },
        {"repair_count": len(local_repair), "families": sorted(row["repair_family"] for row in local_repair)},
    )
    check(
        "forbidden_scan_clean",
        forbidden["ok"] is True and forbidden["matches"] == [] and completion["forbidden_surfaces_touched"] == [],
        forbidden,
    )

    verifier = {
        "schema": f"{SCHEMA_PREFIX}.verifier_result.v1",
        "created_at_utc": created_at,
        "ok": all(row["passed"] for row in checks),
        "issue_count": sum(1 for row in checks if not row["passed"]),
        "checks": checks,
    }
    write_json(ROUTE / "MARKET_EXPANSION_ACTIVATION_READINESS_VERIFIER_RESULT.json", verifier)
    print(json.dumps(verifier, indent=2, sort_keys=True))
    return 0 if verifier["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
