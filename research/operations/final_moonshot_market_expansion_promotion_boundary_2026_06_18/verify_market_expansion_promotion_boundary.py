#!/usr/bin/env python3
"""Verify the market-expansion promotion-boundary route."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_promotion_boundary"
EXPECTED_DECISION = "MARKET_EXPANSION_PROMOTION_BOUNDARY_READY_NOT_PROMOTED"
EXPECTED_REQ_IDS = {
    "MX-PROMO-REQ-001",
    "MX-PROMO-REQ-002",
    "MX-PROMO-REQ-003",
    "MX-PROMO-REQ-004",
    "MX-PROMO-REQ-005",
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
    result = load_json("MARKET_EXPANSION_PROMOTION_BOUNDARY_RESULT.json")
    pretrade = load_jsonl("PRETRADE_COST_PACKET_LEDGER.jsonl")
    pretrade_summary = load_json("PRETRADE_COST_PACKET_SUMMARY.json")
    root_refusal = load_json("ROOT_CONFIG_PRETRADE_REFUSAL_AUDIT.json")
    bridge = load_json("BRIDGE_SURFACE_NEGATIVE_PROOF.json")
    zero = load_json("ZERO_ACTIVE_BEHAVIOR_AUDIT.json")
    config_patch = load_json("CONFIG_PATCH_PROPOSAL.json")
    requirements = load_jsonl("UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    blocker_repair = load_jsonl("BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl")
    decisions = load_jsonl("DECISION_LEDGER.jsonl")
    boundary = load_jsonl("PROMOTION_BOUNDARY_LEDGER.jsonl")
    forbidden = load_json("FORBIDDEN_CALL_SCAN.json")
    saturation = load_json("SATURATION_SELF_RED_TEAM_AUDIT.json")
    completion = load_json("COMPLETION_AUDIT.json")

    activation = config_patch["activation_patch_yaml"]["gtos_vnext_runtime"]
    rollback = config_patch["rollback_patch_yaml"]["gtos_vnext_runtime"]
    requirement_ids = {row["requirement_id"] for row in requirements}
    packet_statuses = {row["packet"]["status"] for row in pretrade}
    packet_refusals = [row["refusal_reason"] for row in pretrade if row["refusal_reason"]]
    boundary_by_gate = {row["gate"]: row for row in boundary}

    checks = [
        check(
            "result_completion_saturation_ok",
            result.get("ok") is True and completion.get("ok") is True and saturation.get("ok") is True,
            {"result_ok": result.get("ok"), "completion_ok": completion.get("ok"), "saturation_ok": saturation.get("ok")},
        ),
        check(
            "terminal_decision_is_ready_boundary_not_promotion",
            result.get("decision") == EXPECTED_DECISION
            and result.get("live_authority") is False
            and result.get("deployment_ready") is False
            and result.get("promotion_ready") is False
            and result.get("runtime_effect") == "none_market_expansion_default_off_promotion_boundary_only"
            and result.get("config_patch_applied") is False,
            {
                "decision": result.get("decision"),
                "live_authority": result.get("live_authority"),
                "deployment_ready": result.get("deployment_ready"),
                "promotion_ready": result.get("promotion_ready"),
            },
        ),
        check(
            "profile_merged_pretrade_packets_pass",
            len(pretrade) == 28
            and pretrade_summary.get("row_count") == 28
            and pretrade_summary.get("status_counts") == {"PASSED": 28}
            and result.get("profile_merged_pretrade_packet_row_count") == 28
            and result.get("profile_merged_pretrade_packet_pass_count") == 28
            and packet_statuses == {"PASSED"}
            and packet_refusals == []
            and pretrade_summary.get("swap_captured_count") == 28
            and all((row["packet"].get("swap") or {}).get("source_status") == "captured" for row in pretrade),
            {
                "row_count": len(pretrade),
                "status_counts": pretrade_summary.get("status_counts"),
                "swap_captured_count": pretrade_summary.get("swap_captured_count"),
                "packet_refusals": packet_refusals[:3],
            },
        ),
        check(
            "raw_root_config_fails_only_profile_namespace",
            root_refusal.get("status") == "REFUSED"
            and root_refusal.get("refusal_reason") == "missing_broker_account_profile_namespace",
            {"status": root_refusal.get("status"), "refusal_reason": root_refusal.get("refusal_reason")},
        ),
        check(
            "bridge_surface_cannot_close_session_or_commission",
            bridge.get("installed_client_imported") is True
            and bridge.get("has_symbol_info") is True
            and bridge.get("has_symbol_info_tick") is True
            and bridge.get("has_symbol_info_session_trade") is False
            and bridge.get("has_symbol_info_session_quote") is False
            and bridge.get("commission_like_symbol_info_keys") == []
            and result.get("bridge_session_trade_method_available") is False
            and result.get("bridge_session_quote_method_available") is False
            and result.get("bridge_commission_like_symbol_info_key_count") == 0,
            {
                "installed_client_imported": bridge.get("installed_client_imported"),
                "has_symbol_info_session_trade": bridge.get("has_symbol_info_session_trade"),
                "has_symbol_info_session_quote": bridge.get("has_symbol_info_session_quote"),
                "commission_like_symbol_info_keys": bridge.get("commission_like_symbol_info_keys"),
            },
        ),
        check(
            "zero_active_and_fail_closed_defaults",
            zero.get("zero_active_behavior_ok") is True
            and zero.get("active_config_include_market_expansion_book") is False
            and zero.get("active_config_market_expansion_sleeves") == []
            and zero.get("bridge_default_include_market_expansion_book") is False
            and zero.get("bridge_default_market_expansion_sleeves") == []
            and zero.get("explicit_allowlist_market_expansion_count") == 14
            and zero.get("empty_allowlist_decision_status") == "fail_closed_market_expansion_requires_explicit_sleeves",
            {
                "zero_active_behavior_ok": zero.get("zero_active_behavior_ok"),
                "empty_allowlist_decision_status": zero.get("empty_allowlist_decision_status"),
                "explicit_allowlist_market_expansion_count": zero.get("explicit_allowlist_market_expansion_count"),
            },
        ),
        check(
            "non_applied_config_patch_is_exact_and_rollback_scoped",
            config_patch.get("status") == "not_applied_owner_action_only"
            and activation.get("ultimate_book_include_market_expansion_book") is True
            and activation.get("ultimate_book_market_expansion_profile") == "default_off_market_expansion_d1_target2_v1"
            and len(activation.get("ultimate_book_market_expansion_sleeves", [])) == 14
            and rollback == {
                "ultimate_book_include_market_expansion_book": False,
                "ultimate_book_market_expansion_sleeves": [],
            },
            {
                "activation_sleeve_count": len(activation.get("ultimate_book_market_expansion_sleeves", [])),
                "rollback": rollback,
            },
        ),
        check(
            "unresolved_requirements_are_exact_and_material",
            requirement_ids == EXPECTED_REQ_IDS
            and blocker_repair == requirements
            and set(result.get("deployment_not_ready_requirement_ids", [])) == EXPECTED_REQ_IDS
            and set(result.get("deployment_not_ready_reasons", [])) == {row["requirement"] for row in requirements}
            and all(row["status"] == "not_closed_by_current_allowed_evidence" for row in requirements),
            {
                "requirement_ids": sorted(requirement_ids),
                "blocker_repair_row_count": len(blocker_repair),
                "deployment_not_ready_requirement_ids": result.get("deployment_not_ready_requirement_ids"),
                "deployment_not_ready_reasons": result.get("deployment_not_ready_reasons"),
            },
        ),
        check(
            "promotion_boundary_preserves_not_closed_gates",
            len(decisions) >= 3
            and boundary_by_gate.get("session_commission_slippage_swap_fill_authority", {}).get("status") == "not_closed"
            and boundary_by_gate.get("owner_vps_action", {}).get("status") == "not_executed_by_mac_route"
            and boundary_by_gate.get("pretrade_cost_packet_shape", {}).get("status") == "diagnostic_pass_not_live_authority",
            {"boundary_gates": sorted(boundary_by_gate)},
        ),
        check(
            "forbidden_scan_and_completion_boundary_clean",
            forbidden.get("ok") is True
            and forbidden.get("matches") == []
            and completion.get("forbidden_surfaces_touched") == []
            and completion.get("config_patch_applied") is False
            and completion.get("deployment_ready") is False
            and completion.get("promotion_ready") is False,
            {"forbidden_matches": forbidden.get("matches"), "completion_boundary": completion.get("runtime_effect_boundary")},
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
    write_json("MARKET_EXPANSION_PROMOTION_BOUNDARY_VERIFIER_RESULT.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
