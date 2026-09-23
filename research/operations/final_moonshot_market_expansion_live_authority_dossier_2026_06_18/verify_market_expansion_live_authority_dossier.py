#!/usr/bin/env python3
"""Verify the market-expansion live-authority dossier route."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_live_authority_dossier"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def check(name: str, passed: bool, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail or {}}


def main() -> int:
    created_at = utc_now()
    result = load_json(ROUTE / "MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_RESULT.json")
    source_events = load_jsonl(ROUTE / "SOURCE_EVENT_COST_LEDGER.jsonl")
    cost_rows = load_jsonl(ROUTE / "SOURCE_SESSION_SPEC_COST_FILL_LEDGER.jsonl")
    replay_rows = load_jsonl(ROUTE / "PORTFOLIO_REPLAY_LEDGER.jsonl")
    daily_replay_rows = load_jsonl(ROUTE / "PORTFOLIO_DAILY_REPLAY_LEDGER.jsonl")
    material_rows = load_jsonl(ROUTE / "ALL_MATERIAL_ROW_LEDGER.jsonl")
    decisions = load_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    bridge = load_json(ROUTE / "BROKER_SPEC_ENHANCED_CAPTURE.json")
    session = load_json(ROUTE / "SESSION_TABLE_UNAVAILABLE_PROOF.json")
    fill = load_json(ROUTE / "FILL_POLICY_DECISION.json")
    zero = load_json(ROUTE / "ZERO_ACTIVE_BEHAVIOR_AUDIT.json")
    forbidden_scan = load_json(ROUTE / "FORBIDDEN_CALL_SCAN.json")
    saturation = load_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json")
    completion = load_json(ROUTE / "COMPLETION_AUDIT.json")

    source_tags = {row["tag"] for row in source_events}
    cost_tags = {row["tag"] for row in cost_rows}
    material_tags = {row["tag"] for row in material_rows}
    replay_names = {row["scenario"] for row in replay_rows}
    source_join_statuses = {row["source_join_status"] for row in source_events}
    scenario = next(
        (row for row in replay_rows if row["scenario"] == "candidate_plus_expansion_seed_0p025_cost3"),
        None,
    )

    checks = [
        check(
            "result_completion_saturation_ok",
            result.get("ok") is True and completion.get("ok") is True and saturation.get("ok") is True,
            {
                "result_ok": result.get("ok"),
                "completion_ok": completion.get("ok"),
                "saturation_ok": saturation.get("ok"),
            },
        ),
        check(
            "all_14_material_rows_and_cost_rows_present",
            result.get("selectable_activation_candidate_count") == 14
            and len(cost_rows) == 14
            and len(material_rows) == 14
            and len(cost_tags) == len(material_tags) == len(source_tags) == 14
            and cost_tags == material_tags == source_tags,
            {
                "cost_rows": len(cost_rows),
                "material_rows": len(material_rows),
                "source_tags": len(source_tags),
            },
        ),
        check(
            "source_event_cost_join_complete",
            result.get("source_event_cost_row_count") == 2596
            and len(source_events) == 2596
            and source_join_statuses == {"joined_generator_parity_risk"}
            and all(row.get("risk_abs") is not None for row in source_events),
            {
                "source_event_cost_row_count": result.get("source_event_cost_row_count"),
                "source_join_statuses": sorted(source_join_statuses),
            },
        ),
        check(
            "portfolio_replay_scenarios_complete",
            len(replay_rows) == 8
            and len(daily_replay_rows) == result.get("portfolio_daily_replay_row_count") == 1679
            and result.get("portfolio_proxy_replay_complete") is True
            and scenario is not None
            and scenario.get("source_value_key") == "proxy_r_cost3"
            and scenario.get("expansion_weight_per_tag") == 0.025
            and {
                "active_core8_a8_baseline_no_candidates",
                "candidate_all_on_active_a8_reference",
                "candidate_plus_expansion_seed_0p025_cost1",
                "candidate_plus_expansion_seed_0p025_cost2",
                "candidate_plus_expansion_seed_0p025_cost3",
                "candidate_plus_expansion_micro_0p0125_cost3",
                "candidate_plus_expansion_ceiling_0p05_cost3",
                "active_a8_plus_expansion_seed_0p025_cost3_no_candidate_book",
            }
            <= replay_names,
            {"replay_names": sorted(replay_names), "daily_replay_rows": len(daily_replay_rows)},
        ),
        check(
            "portfolio_daily_replay_has_aligned_interaction_columns",
            bool(daily_replay_rows)
            and {
                "date",
                "active_a8_r",
                "candidate_all_on_active_a8_r",
                "candidate_overlay_r",
                "candidate_plus_expansion_seed_0p025_cost3_r",
                "candidate_plus_expansion_seed_0p025_cost3_expansion_overlay_r",
                "active_a8_plus_expansion_seed_0p025_cost3_no_candidate_book_r",
            }
            <= set(daily_replay_rows[0])
            and all(row["split"] in {"train", "oos", "sealed"} for row in daily_replay_rows),
            {"first_row_keys": sorted(daily_replay_rows[0]) if daily_replay_rows else []},
        ),
        check(
            "broker_capture_boundary",
            bridge.get("symbol_count") == 14
            and bridge.get("account_info_read") is False
            and bridge.get("symbol_select_called") is False
            and bridge.get("broker_or_order_mutation") is False
            and bridge.get("orderflow_used") is False
            and bridge.get("symbol_info_captured_count") == 14
            and bridge.get("stop_freeze_present_count") == 14,
            {
                "bridge_reachable": bridge.get("bridge_reachable"),
                "symbol_info_captured_count": bridge.get("symbol_info_captured_count"),
                "symbol_info_tick_captured_count": bridge.get("symbol_info_tick_captured_count"),
                "stop_freeze_present_count": bridge.get("stop_freeze_present_count"),
            },
        ),
        check(
            "static_forbidden_call_scan_clean",
            forbidden_scan.get("ok") is True
            and forbidden_scan.get("matches") == [],
            {"matches": forbidden_scan.get("matches")},
        ),
        check(
            "session_table_gap_is_exact_or_captured",
            (
                bridge.get("explicit_session_table_present_count", 0) > 0
                or (
                    session.get("session_trade_method_available") is False
                    and session.get("session_quote_method_available") is False
                    and session.get("explicit_session_table_present_count") == 0
                )
            ),
            {
                "session_trade_method_available": session.get("session_trade_method_available"),
                "session_quote_method_available": session.get("session_quote_method_available"),
                "explicit_session_table_present_count": session.get("explicit_session_table_present_count"),
            },
        ),
        check(
            "cost_and_fill_statuses_preserve_boundaries",
            all(row.get("commission_to_r_status") == "not_available_in_symbol_info_or_activation_artifacts" for row in cost_rows)
            and all(row.get("slippage_to_r_status") == "stress_proxy_cost2_cost3_only_not_broker_exact" for row in cost_rows)
            and all(row.get("fill_policy_status") == "limit_first_or_guarded_open_market_policy_draft_not_live_order_logic" for row in cost_rows)
            and fill.get("live_order_logic_changed") is False,
            {"fill_policy_decision": fill.get("decision")},
        ),
        check(
            "zero_active_and_no_live_authority",
            zero.get("zero_active_behavior_ok") is True
            and result.get("activation_weight_now") == 0.0
            and result.get("live_authority") is False
            and result.get("deployment_ready") is False
            and result.get("promotion_ready") is False
            and result.get("config_or_live_activation_changed") is False
            and result.get("vps_process_touched") is False,
            {
                "zero_active_behavior_ok": zero.get("zero_active_behavior_ok"),
                "deployment_not_ready_reasons": result.get("deployment_not_ready_reasons"),
            },
        ),
        check(
            "decision_and_completion_boundaries",
            result.get("decision") == "MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_BUILT_DEFAULT_OFF_NOT_PROMOTED"
            and len(decisions) >= 5
            and completion.get("forbidden_surfaces_touched") == []
            and completion.get("runtime_effect_boundary") == "none_default_off_dossier_only"
            and saturation.get("no_arbitrary_top_n") is True,
            {
                "decision": result.get("decision"),
                "decision_rows": len(decisions),
                "runtime_effect_boundary": completion.get("runtime_effect_boundary"),
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
    write_json(ROUTE / "MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_VERIFIER_RESULT.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
