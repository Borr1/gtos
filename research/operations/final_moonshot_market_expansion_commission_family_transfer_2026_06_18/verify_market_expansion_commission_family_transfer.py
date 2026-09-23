#!/usr/bin/env python3
"""Verify market-expansion commission family-transfer artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_commission_family_transfer"
EXPECTED_DECISION = "COMMISSION_FAMILY_TRANSFER_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED"
EXPECTED_REQ_IDS = {
    "MX-COMMISSION-FAMILY-REQ-001",
    "MX-COMMISSION-FAMILY-REQ-002",
    "MX-COMMISSION-FAMILY-REQ-003",
    "MX-COMMISSION-FAMILY-REQ-004",
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(name: str) -> Any:
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(name: str, payload: Any) -> None:
    (ROUTE / name).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def check(name: str, passed: bool, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail or {}}


def main() -> int:
    created_at = utc_now()
    result = load_json("COMMISSION_FAMILY_TRANSFER_RESULT.json")
    account_rows = load_jsonl("ACCOUNT_HISTORY_SYMBOL_COMMISSION_LEDGER.jsonl")
    account_summary = load_json("ACCOUNT_HISTORY_SYMBOL_COMMISSION_SUMMARY.json")
    transfer_rows = load_jsonl("TARGET_COMMISSION_TRANSFER_LEDGER.jsonl")
    transfer_summary = load_json("TARGET_COMMISSION_TRANSFER_SUMMARY.json")
    requirements = load_jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    blocker_repair = load_jsonl("BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl")
    decisions = load_jsonl("DECISION_LEDGER.jsonl")
    boundary = load_jsonl("PROMOTION_BOUNDARY_LEDGER.jsonl")
    forbidden = load_json("FORBIDDEN_CALL_SCAN.json")
    saturation = load_json("SATURATION_SELF_RED_TEAM_AUDIT.json")
    completion = load_json("COMPLETION_AUDIT.json")

    req_ids = {row["requirement_id"] for row in requirements}
    boundary_status = {row["gate"]: row["status"] for row in boundary}
    status_counts = transfer_summary.get("status_counts", {})

    checks = [
        check(
            "result_completion_and_saturation_ok",
            result.get("ok") is True and completion.get("ok") is True and saturation.get("ok") is True,
            {"result_ok": result.get("ok"), "completion_ok": completion.get("ok"), "saturation_ok": saturation.get("ok")},
        ),
        check(
            "decision_is_partial_default_off",
            result.get("decision") == EXPECTED_DECISION
            and result.get("live_authority") is False
            and result.get("deployment_ready") is False
            and result.get("promotion_ready") is False
            and result.get("config_patch_applied") is False
            and result.get("runtime_effect") == "none_market_expansion_default_off_commission_family_transfer_only",
            {
                "decision": result.get("decision"),
                "live_authority": result.get("live_authority"),
                "deployment_ready": result.get("deployment_ready"),
            },
        ),
        check(
            "account_history_symbol_commission_aggregate_clean",
            len(account_rows) == 15
            and account_summary.get("symbol_count") == 15
            and account_summary.get("deal_count_total") == 101
            and account_summary.get("raw_ticket_or_deal_ids_stored") is False
            and account_summary.get("nonzero_commission_symbol_count") == 8
            and account_summary.get("zero_commission_symbol_count") == 7
            and all(row.get("raw_ticket_or_deal_ids_stored") is False for row in account_rows),
            {
                "account_summary": account_summary,
            },
        ),
        check(
            "target_transfer_covers_all_targets_without_schedule_overclaim",
            len(transfer_rows) == 14
            and transfer_summary.get("target_symbol_count") == 14
            and transfer_summary.get("direct_authority_symbol_count") == 7
            and transfer_summary.get("family_proxy_symbol_count") == 7
            and transfer_summary.get("not_closed_symbol_count") == 0
            and transfer_summary.get("direct_or_family_proxy_symbol_count") == 14
            and transfer_summary.get("all_targets_have_direct_or_family_proxy") is True
            and transfer_summary.get("broker_exact_schedule_closed") is False
            and result.get("direct_commission_authority_symbol_count") == 7
            and result.get("family_proxy_commission_symbol_count") == 7
            and result.get("direct_or_family_proxy_symbol_count") == 14
            and result.get("broker_exact_schedule_closed") is False,
            {
                "transfer_summary": transfer_summary,
                "status_counts": status_counts,
            },
        ),
        check(
            "transfer_status_distribution_is_expected",
            status_counts == {
                "direct_observed_nonzero_commission": 2,
                "direct_observed_zero_commission": 5,
                "family_proxy_nonzero_commission": 3,
                "family_proxy_zero_commission": 4,
            }
            and all(row.get("commission_authority_class") != "not_closed" for row in transfer_rows)
            and all(row.get("raw_ticket_or_deal_ids_stored") is False for row in transfer_rows),
            {"status_counts": status_counts},
        ),
        check(
            "requirements_and_boundaries_keep_promotion_closed",
            req_ids == EXPECTED_REQ_IDS
            and blocker_repair == requirements
            and set(result.get("deployment_not_ready_requirement_ids", [])) == EXPECTED_REQ_IDS
            and len(decisions) >= 3
            and boundary_status.get("direct_or_family_commission_evidence") == "closed_as_proxy_not_schedule"
            and boundary_status.get("broker_exact_commission_schedule") == "not_closed"
            and boundary_status.get("owner_vps_action") == "not_executed_by_mac_route",
            {
                "requirement_ids": sorted(req_ids),
                "boundary_status": boundary_status,
            },
        ),
        check(
            "forbidden_scan_and_completion_boundary_clean",
            forbidden.get("ok") is True
            and forbidden.get("matches") == []
            and completion.get("raw_ticket_or_deal_ids_stored") is False
            and completion.get("forbidden_surfaces_touched") == []
            and completion.get("deployment_ready") is False
            and completion.get("promotion_ready") is False,
            {
                "forbidden_matches": forbidden.get("matches"),
                "approved_reads": completion.get("approved_read_surfaces_used"),
            },
        ),
    ]
    ok = all(row["passed"] for row in checks)
    payload = {
        "schema": f"{SCHEMA_PREFIX}.verifier_result.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "issue_count": sum(1 for row in checks if not row["passed"]),
        "checks": checks,
    }
    write_json("COMMISSION_FAMILY_TRANSFER_VERIFIER_RESULT.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
