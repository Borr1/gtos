#!/usr/bin/env python3
"""Verify the market-expansion broker-authority probe route."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_broker_authority_probe"
EXPECTED_DECISION = "BROKER_AUTHORITY_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED"
EXPECTED_REQ_IDS = {
    "MX-BROKER-AUTH-REQ-001",
    "MX-BROKER-AUTH-REQ-002",
    "MX-BROKER-AUTH-REQ-003",
    "MX-BROKER-AUTH-REQ-004",
    "MX-BROKER-AUTH-REQ-005",
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
    result = load_json("BROKER_AUTHORITY_PROBE_RESULT.json")
    bridge = load_json("BRIDGE_METHOD_SURFACE.json")
    account = load_json("ACCOUNT_TERMINAL_REDACTED_AUDIT.json")
    session = load_json("SESSION_TABLE_REMOTE_PROOF.json")
    deal_rows = load_jsonl("DEAL_HISTORY_COMMISSION_LEDGER.jsonl")
    deal_summary = load_json("DEAL_HISTORY_COMMISSION_SUMMARY.json")
    conversion_rows = load_jsonl("ORDER_CALC_PROFIT_CONVERSION_LEDGER.jsonl")
    conversion_summary = load_json("ORDER_CALC_PROFIT_CONVERSION_SUMMARY.json")
    swap_rows = load_jsonl("SWAP_TO_R_PARTIAL_AUTHORITY_LEDGER.jsonl")
    swap_summary = load_json("SWAP_TO_R_PARTIAL_AUTHORITY_SUMMARY.json")
    requirements = load_jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    blocker_repair = load_jsonl("BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl")
    decisions = load_jsonl("DECISION_LEDGER.jsonl")
    boundary = load_jsonl("PROMOTION_BOUNDARY_LEDGER.jsonl")
    forbidden = load_json("FORBIDDEN_CALL_SCAN.json")
    saturation = load_json("SATURATION_SELF_RED_TEAM_AUDIT.json")
    completion = load_json("COMPLETION_AUDIT.json")

    req_ids = {row["requirement_id"] for row in requirements}
    boundary_status = {row["gate"]: row["status"] for row in boundary}
    conversion_statuses = {row["conversion_status"] for row in conversion_rows}
    swap_status_counts = swap_summary.get("conversion_status_counts", {})
    deal_authority_counts = deal_summary.get("authority_status_counts", {})

    checks = [
        check(
            "result_completion_and_saturation_ok",
            result.get("ok") is True and completion.get("ok") is True and saturation.get("ok") is True,
            {"result_ok": result.get("ok"), "completion_ok": completion.get("ok"), "saturation_ok": saturation.get("ok")},
        ),
        check(
            "decision_is_partial_repair_default_off",
            result.get("decision") == EXPECTED_DECISION
            and result.get("live_authority") is False
            and result.get("deployment_ready") is False
            and result.get("promotion_ready") is False
            and result.get("config_patch_applied") is False
            and result.get("runtime_effect") == "none_market_expansion_default_off_broker_authority_probe_only",
            {
                "decision": result.get("decision"),
                "live_authority": result.get("live_authority"),
                "deployment_ready": result.get("deployment_ready"),
            },
        ),
        check(
            "bridge_and_redacted_account_surface_ok",
            bridge.get("bridge_initialized") is True
            and bridge.get("approved_read_method_available", {}).get("account_info") is True
            and bridge.get("approved_read_method_available", {}).get("history_deals_get") is True
            and bridge.get("approved_read_method_available", {}).get("order_calc_profit") is True
            and account.get("account_info_read") is True
            and account.get("terminal_info_read") is True
            and account.get("raw_account_values_stored") is False
            and account.get("redacted_account", {}).get("currency") == "USD"
            and account.get("redacted_account", {}).get("login_hash")
            and "balance" in account.get("sensitive_fields_excluded", []),
            {
                "bridge_initialized": bridge.get("bridge_initialized"),
                "redaction_policy": account.get("redaction_policy"),
                "currency": account.get("redacted_account", {}).get("currency"),
            },
        ),
        check(
            "session_table_remains_exactly_not_closed",
            session.get("session_table_closed") is False
            and session.get("proof_scope") == "local siliconmetatrader5 client and localhost bridge-host MT5 module, not VPS"
            and session.get("client_symbol_info_session_trade") is False
            and session.get("client_symbol_info_session_quote") is False
            and session.get("bridge_host_symbol_info_session_trade") is False
            and session.get("bridge_host_symbol_info_session_quote") is False
            and session.get("remote_symbol_info_session_trade") is False
            and session.get("remote_symbol_info_session_quote") is False
            and session.get("symbol_info_session_like_key_count") == 0
            and result.get("session_table_closed") is False,
            {
                "proof_scope": session.get("proof_scope"),
                "bridge_host_session_like_names": session.get("bridge_host_session_like_names"),
                "symbol_info_session_like_keys": session.get("symbol_info_session_like_keys"),
            },
        ),
        check(
            "deal_history_commission_partial_authority_is_consistent",
            len(deal_rows) == 14
            and deal_summary.get("symbol_count") == 14
            and result.get("commission_direct_history_symbol_count") == deal_summary.get("direct_history_symbol_count")
            and result.get("commission_nonzero_symbol_count") == deal_summary.get("nonzero_commission_symbol_count")
            and result.get("commission_observed_zero_symbol_count") == deal_summary.get("observed_zero_commission_symbol_count")
            and deal_summary.get("direct_history_symbol_count") == 7
            and deal_summary.get("nonzero_commission_symbol_count") == 2
            and deal_summary.get("observed_zero_commission_symbol_count") == 5
            and deal_summary.get("no_direct_history_symbol_count") == 7
            and deal_summary.get("all_symbols_commission_authority_closed") is False
            and deal_authority_counts.get("direct_observed_nonzero_commission_account_history") == 2
            and deal_authority_counts.get("direct_observed_zero_commission_account_history_not_schedule") == 5
            and deal_authority_counts.get("not_closed_no_direct_deal_rows_for_symbol") == 7,
            {
                "summary": deal_summary,
                "authority_status_counts": deal_authority_counts,
            },
        ),
        check(
            "order_calc_profit_conversion_closed_for_all_symbols",
            len(conversion_rows) == 14
            and conversion_summary.get("symbol_count") == 14
            and conversion_summary.get("closed_symbol_count") == 14
            and conversion_summary.get("all_symbols_closed") is True
            and result.get("profit_conversion_closed_symbol_count") == 14
            and result.get("profit_conversion_all_symbols_closed") is True
            and conversion_statuses == {"closed_order_calc_profit_matches_symbol_info"}
            and float(conversion_summary.get("max_abs_ratio_error_vs_symbol_info", 1.0)) <= 0.005,
            {
                "conversion_statuses": sorted(conversion_statuses),
                "max_abs_ratio_error": conversion_summary.get("max_abs_ratio_error_vs_symbol_info"),
            },
        ),
        check(
            "swap_to_r_is_partial_not_overclaimed",
            len(swap_rows) == 28
            and swap_summary.get("side_row_count") == 28
            and swap_summary.get("symbol_count") == 14
            and swap_summary.get("point_mode_side_rows_computed") == 22
            and swap_summary.get("mode5_or_other_side_rows_not_closed") == 6
            and swap_summary.get("all_swap_to_r_closed") is False
            and result.get("swap_point_mode_side_rows_computed") == 22
            and result.get("swap_mode5_or_other_side_rows_not_closed") == 6
            and result.get("swap_all_symbols_closed") is False
            and swap_status_counts.get("point_mode_cash_to_r_computed") == 22
            and swap_status_counts.get("not_closed_interest_current_mode_formula_required") == 6,
            {"swap_status_counts": swap_status_counts},
        ),
        check(
            "requirements_and_boundaries_keep_promotion_closed",
            req_ids == EXPECTED_REQ_IDS
            and blocker_repair == requirements
            and set(result.get("deployment_not_ready_requirement_ids", [])) == EXPECTED_REQ_IDS
            and len(decisions) >= 5
            and boundary_status.get("session_table_authority") == "not_closed"
            and boundary_status.get("commission_authority") == "partial_not_closed"
            and boundary_status.get("account_currency_profit_conversion") == "closed_for_probe_symbols"
            and boundary_status.get("swap_to_r_authority") == "partial_not_closed"
            and boundary_status.get("fill_slippage_limit_authority") == "not_closed_not_mutated"
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
            and completion.get("forbidden_surfaces_touched") == []
            and completion.get("raw_account_values_stored") is False
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
    write_json("BROKER_AUTHORITY_PROBE_VERIFIER_RESULT.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
