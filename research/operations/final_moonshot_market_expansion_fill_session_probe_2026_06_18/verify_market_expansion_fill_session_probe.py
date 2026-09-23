#!/usr/bin/env python3
"""Verify the market-expansion fill/session probe route."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_fill_session_probe"
EXPECTED_DECISION = "FILL_SESSION_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED"
EXPECTED_REQ_IDS = {
    "MX-FILL-SESSION-REQ-001",
    "MX-FILL-SESSION-REQ-002",
    "MX-FILL-SESSION-REQ-003",
    "MX-FILL-SESSION-REQ-004",
    "MX-FILL-SESSION-REQ-005",
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
    result = load_json("FILL_SESSION_PROBE_RESULT.json")
    fill_rows = load_jsonl("HISTORY_ORDER_DEAL_FILL_LEDGER.jsonl")
    fill_summary = load_json("HISTORY_ORDER_DEAL_FILL_SUMMARY.json")
    field_audit = load_json("HISTORY_ORDER_DEAL_FIELD_AUDIT.json")
    session_rows = load_jsonl("OBSERVED_M1_SESSION_AVAILABILITY_LEDGER.jsonl")
    session_summary = load_json("OBSERVED_M1_SESSION_AVAILABILITY_SUMMARY.json")
    requirements = load_jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    blocker_repair = load_jsonl("BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl")
    decisions = load_jsonl("DECISION_LEDGER.jsonl")
    boundary = load_jsonl("PROMOTION_BOUNDARY_LEDGER.jsonl")
    forbidden = load_json("FORBIDDEN_CALL_SCAN.json")
    saturation = load_json("SATURATION_SELF_RED_TEAM_AUDIT.json")
    completion = load_json("COMPLETION_AUDIT.json")

    req_ids = {row["requirement_id"] for row in requirements}
    boundary_status = {row["gate"]: row["status"] for row in boundary}
    fill_status_counts = fill_summary.get("fill_authority_status_counts", {})
    session_status_counts = session_summary.get("observed_session_proxy_status_counts", {})

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
            and result.get("runtime_effect") == "none_market_expansion_default_off_fill_session_probe_only",
            {
                "decision": result.get("decision"),
                "live_authority": result.get("live_authority"),
                "deployment_ready": result.get("deployment_ready"),
            },
        ),
        check(
            "history_fill_rows_are_aggregate_and_partial",
            len(fill_rows) == 14
            and fill_summary.get("symbol_count") == 14
            and fill_summary.get("direct_fill_symbol_count") == 7
            and fill_summary.get("no_direct_fill_symbol_count") == 7
            and fill_summary.get("joined_entry_deal_count_total") == 57
            and fill_summary.get("all_symbols_fill_slippage_closed") is False
            and result.get("direct_fill_symbol_count") == 7
            and result.get("no_direct_fill_symbol_count") == 7
            and result.get("historical_fill_slippage_all_symbols_closed") is False
            and fill_status_counts.get("direct_observed_historical_order_deal_fill_slippage") == 7
            and fill_status_counts.get("not_closed_no_direct_joined_fill_rows") == 7
            and all(row.get("raw_ticket_or_order_ids_stored") is False for row in fill_rows),
            {
                "fill_summary": fill_summary,
                "fill_status_counts": fill_status_counts,
            },
        ),
        check(
            "field_audit_excludes_raw_ids",
            field_audit.get("raw_ticket_or_order_ids_stored") is False
            and "ticket" in field_audit.get("order_field_names", [])
            and "order" in field_audit.get("deal_field_names", [])
            and result.get("joined_entry_deal_count_total") == fill_summary.get("joined_entry_deal_count_total"),
            {
                "raw_ticket_or_order_ids_stored": field_audit.get("raw_ticket_or_order_ids_stored"),
                "order_field_count": len(field_audit.get("order_field_names", [])),
                "deal_field_count": len(field_audit.get("deal_field_names", [])),
            },
        ),
        check(
            "observed_m1_session_proxy_available_but_not_explicit",
            len(session_rows) == 14
            and session_summary.get("symbol_count") == 14
            and session_summary.get("symbols_with_m1_bars") == 14
            and session_summary.get("explicit_session_table_closed") is False
            and result.get("symbols_with_m1_session_proxy") == 14
            and result.get("explicit_session_table_closed") is False
            and all(row.get("m1_bar_count", 0) > 0 for row in session_rows)
            and all(row.get("explicit_session_table_status") == "not_explicit_session_table" for row in session_rows)
            and session_status_counts.get("observed_24_7_like_quote_availability_proxy") == 3
            and session_status_counts.get("observed_weekday_24h_quote_availability_proxy") == 2
            and session_status_counts.get("observed_restricted_weekday_quote_availability_proxy") == 9,
            {
                "session_status_counts": session_status_counts,
                "weekend_quote_symbols": session_summary.get("weekend_quote_symbols"),
            },
        ),
        check(
            "requirements_and_boundaries_keep_promotion_closed",
            req_ids == EXPECTED_REQ_IDS
            and blocker_repair == requirements
            and set(result.get("deployment_not_ready_requirement_ids", [])) == EXPECTED_REQ_IDS
            and len(decisions) >= 4
            and boundary_status.get("historical_fill_slippage") == "partial_not_closed"
            and boundary_status.get("observed_quote_session_proxy") == "proxy_available_not_live_authority"
            and boundary_status.get("explicit_session_table") == "not_closed"
            and boundary_status.get("prospective_limit_queue_fillability") == "not_closed_not_mutated"
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
            and completion.get("raw_ticket_or_order_ids_stored") is False
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
    write_json("FILL_SESSION_PROBE_VERIFIER_RESULT.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
