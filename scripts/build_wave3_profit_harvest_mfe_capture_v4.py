#!/usr/bin/env python3
"""Build Wave3 profit-harvest/MFE-capture V4 route artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path("research/operations/wave3_profit_harvest_mfe_capture_v4_2026_06_04")
WAVE2_DIR = Path("research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04")
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "wave3_final_moonshot_after_hard_halt_2026_06_04/"
    "WAVE3_11_PROFIT_HARVEST_MFE_CAPTURE_V4_GOAL_PROMPT_2026-06-04.md"
)
STARTER_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "wave3_final_moonshot_after_hard_halt_2026_06_04/"
    "WAVE3_11_PROFIT_HARVEST_MFE_CAPTURE_V4_STARTER_2026-06-04.txt"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True).strip()
    except Exception as exc:  # noqa: BLE001
        return f"unavailable:{exc}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_actions(row: dict[str, Any]) -> list[str]:
    actions = []
    tick_mfe = row.get("tick_mfe_r")
    if isinstance(tick_mfe, (int, float)):
        if tick_mfe >= 0.25:
            actions.append("trail_or_be_protect_after_min_mfe")
        if tick_mfe >= 0.50:
            actions.append("micro_partial_design_fixture")
    if row.get("first_giveback_0_5r_minutes_after_mfe") is not None:
        actions.append("close_or_reduce_on_giveback_design_fixture")
    if row.get("near_mfe_within_0_10r_span_minutes"):
        actions.append("stale_or_consolidation_near_mfe_design_fixture")
    if not actions:
        actions.append("no_harvest_action_source_bound_below_threshold")
    return actions


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()

    filled_rows = read_jsonl(WAVE2_DIR / "WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl")
    loser_mfe_rows = read_jsonl(WAVE2_DIR / "WAVE2_MFE_HARVEST_FAILURE_LEDGER.jsonl")
    stale_rows = read_jsonl(WAVE2_DIR / "WAVE2_OVERNIGHT_NEXT_DAY_STALE_THESIS_LEDGER.jsonl")
    ownership = read_json(WAVE2_DIR / "WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json")
    causal_model = read_json(WAVE2_DIR / "WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json")

    stale_by_trade = {
        (row.get("trade_id"), row.get("symbol"), row.get("side")): row
        for row in stale_rows
    }

    source_coverage_rows: list[dict[str, Any]] = []
    for row in filled_rows:
        is_loser_positive = (
            isinstance(row.get("actual_r"), (int, float))
            and row["actual_r"] < 0
            and isinstance(row.get("mfe_r"), (int, float))
            and row["mfe_r"] > 0
        )
        source_coverage_rows.append(
            {
                "row_id": f"wave3_source_coverage:{row.get('row_id')}",
                "upstream_row_id": row.get("row_id"),
                "trade_id": row.get("trade_id"),
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "actual_r": row.get("actual_r"),
                "mfe_r": row.get("mfe_r"),
                "mae_r": row.get("mae_r"),
                "giveback_r": row.get("giveback_r"),
                "partial_close_count": row.get("partial_close_count"),
                "selected_policy": row.get("selected_policy"),
                "execution_policy_id": row.get("execution_policy_id"),
                "source_path": row.get("source_path"),
                "source_read_status": row.get("source_read_status"),
                "route_disposition": (
                    "loser_positive_mfe_fixture_materialized"
                    if is_loser_positive
                    else "source_coverage_not_loser_positive_mfe_fixture"
                ),
                "result_use_status": "source_coverage_not_counterfactual_pnl",
                "broker_runtime_change_status": False,
            }
        )

    fixture_rows: list[dict[str, Any]] = []
    for row in loser_mfe_rows:
        stale = stale_by_trade.get((row.get("trade_id"), row.get("symbol"), row.get("side")), {})
        fixture_rows.append(
            {
                "row_id": f"wave3_loser_mfe_fixture:{row.get('row_id')}",
                "upstream_row_id": row.get("row_id"),
                "source_tick_repair_row_id": row.get("source_tick_repair_row_id"),
                "trade_id": row.get("trade_id"),
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "actual_r": row.get("actual_r"),
                "tick_mfe_r": row.get("tick_mfe_r"),
                "tick_mae_r": row.get("tick_mae_r"),
                "terminal_tick_r": row.get("terminal_tick_r"),
                "mfe_to_terminal_giveback_r": row.get("mfe_to_terminal_giveback_r"),
                "mfe_to_worst_after_mfe_reversal_r": row.get(
                    "mfe_to_worst_after_mfe_reversal_r"
                ),
                "first_giveback_0_25r_minutes_after_mfe": row.get(
                    "first_giveback_0_25r_minutes_after_mfe"
                ),
                "first_giveback_0_5r_minutes_after_mfe": row.get(
                    "first_giveback_0_5r_minutes_after_mfe"
                ),
                "first_giveback_1_0r_minutes_after_mfe": row.get(
                    "first_giveback_1_0r_minutes_after_mfe"
                ),
                "near_mfe_within_0_10r_span_minutes": row.get(
                    "near_mfe_within_0_10r_span_minutes"
                ),
                "harvest_failure_status": row.get("harvest_failure_status"),
                "stale_thesis_status": stale.get("stale_thesis_status"),
                "hold_minutes_repaired": stale.get("hold_minutes_repaired"),
                "path_source_status": row.get("path_source_status"),
                "tick_repair_status": row.get("tick_repair_status"),
                "full_tick_window_covered": row.get("full_tick_window_covered"),
                "evidence_class": row.get("evidence_class"),
                "source_path": row.get("source_path"),
                "source_paths": row.get("source_paths"),
                "v4_requirement_id": row.get("v4_requirement_id"),
                "v4_actions_supported": fixture_actions(row),
                "result_use_status": "source_bound_path_fixture_not_counterfactual_pnl",
                "broker_runtime_change_status": False,
                "ftmo_copy_status": "not_copied_to_ftmo_truth",
            }
        )

    trigger_contract = {
        "artifact": "WAVE3_PROFIT_HARVEST_MFE_TRIGGER_CONTRACT",
        "generated_at_utc": generated_at,
        "lane": "profit_harvest_mfe_capture_v4",
        "evidence_class": "production_code_integration_plus_source_bound_replay_design_fixture",
        "runtime_boundary": {
            "broker_runtime_change_status": False,
            "live_deployment_status": "not_deployed",
            "config_default": "profit_harvest_mfe_capture_v4_enabled=false",
            "forbidden_surfaces": [
                "live trading deployment",
                "broker account/order/history/deal/position mutation",
                "credential mutation or disclosure",
                "paid API/vendor calls",
                "active VPS process changes",
                "remote push",
            ],
        },
        "source_rows": {
            "filled_trade_coverage_rows": len(source_coverage_rows),
            "loser_mfe_fixture_rows": len(fixture_rows),
            "wave2_filled_trade_source": str(
                WAVE2_DIR / "WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl"
            ),
            "wave2_loser_mfe_source": str(
                WAVE2_DIR / "WAVE2_MFE_HARVEST_FAILURE_LEDGER.jsonl"
            ),
        },
        "production_overlay": {
            "integration_file": "src/components/execution.py",
            "enabled_key": "gtos_vnext_runtime.profit_harvest_mfe_capture_v4_enabled",
            "default_disposition": "staged_default_off",
            "ticket_bound_state": True,
            "actions": [
                {
                    "action": "trail_or_be_protect_after_min_mfe",
                    "trigger": "mfe_r >= min_mfe_r before primary dynamic trigger",
                    "default_min_mfe_r": 0.25,
                    "default_trail_gap_r": 0.35,
                    "default_protect_floor_r": 0.0,
                },
                {
                    "action": "close_on_giveback",
                    "trigger": "mfe_r - current_progress_r >= close_on_giveback_r",
                    "default_close_on_giveback_r": 0.50,
                },
                {
                    "action": "stale_thesis_close",
                    "trigger": (
                        "age_minutes >= stale_minutes and mfe_r >= stale_min_mfe_r "
                        "and current_progress_r <= stale_close_below_r"
                    ),
                    "default_stale_minutes": 360,
                    "default_stale_min_mfe_r": 0.25,
                    "default_stale_close_below_r": 0.0,
                },
            ],
            "handoffs": [
                "micro-partial live sizing and partial residual policy remain owned by partial_be_trailing_stale_thesis_exit_policy_v4",
                "open trade versus new candidate competition remains owned by same_symbol_same_instrument_lifecycle_v4",
                "probability and EV selection remain owned by probability_debate_team_engine_v4",
            ],
        },
        "source_replay_policy": {
            "integration_file": "src/research/dynamic_execution_policy.py",
            "policy_name": "profit_harvest_mfe_capture_v4",
            "source_bound_actions": [
                "micro_partial_design_fixture",
                "be_or_trail_replay",
                "giveback_close_replay",
                "stale_thesis_close_replay",
            ],
            "counterfactual_boundary": "no_broker_real_counterfactual_pnl_claim",
        },
    }

    decision_rows = [
        {
            "row_id": "decision:execution_overlay_default_off",
            "decision": "implement_profit_harvest_mfe_capture_v4_execution_overlay",
            "status": "staged_default_off",
            "code_paths": ["src/components/execution.py", "config/agent_config.yaml"],
            "reason": "Wave2 loser-positive-MFE rows showed sub-1R harvest failure before old fixed trigger.",
            "broker_runtime_change_status": False,
        },
        {
            "row_id": "decision:source_replay_policy",
            "decision": "implement_source_bound_profit_harvest_replay_policy",
            "status": "active_research_replay_policy",
            "code_paths": ["src/research/dynamic_execution_policy.py"],
            "reason": "Partial, trail, giveback, and stale-thesis harvest logic needs design fixtures without broker-real counterfactual PnL claims.",
            "broker_runtime_change_status": False,
        },
        {
            "row_id": "decision:fixture_all_loser_mfe_rows",
            "decision": "materialize_all_loser_mfe_rows",
            "status": "complete",
            "row_count": len(fixture_rows),
            "reason": "No arbitrary top-N; all Wave2 source-bound loser MFE rows are preserved.",
            "broker_runtime_change_status": False,
        },
        {
            "row_id": "decision:partial_live_handoff",
            "decision": "handoff_live_micro_partial_volume_policy",
            "status": "bounded_to_first_class_exit_policy_owner",
            "owner_lane": "partial_be_trailing_stale_thesis_exit_policy_v4",
            "reason": "This lane materializes source-bound partial fixtures and execution close/trail overlay; partial residual live sizing requires first-class exit-policy ownership.",
            "broker_runtime_change_status": False,
        },
    ]

    disposition_rows = [
        {
            "component": "src/components/execution.py",
            "disposition": "staged_default_off",
            "reason": "Default-off V4 overlay with explicit config key and ticket-bound state.",
        },
        {
            "component": "config/agent_config.yaml",
            "disposition": "staged_default_off",
            "reason": "profit_harvest_mfe_capture_v4_enabled=false; parameters and contract path are declared.",
        },
        {
            "component": "src/research/dynamic_execution_policy.py",
            "disposition": "active_research_replay_policy",
            "reason": "Pure source-bound replay policy for partial/trail/giveback/stale fixtures.",
        },
        {
            "component": "tests/test_limit_order_flow.py",
            "disposition": "focused_test",
            "reason": "Pins default-off and explicit-on execution behavior.",
        },
        {
            "component": "tests/test_dynamic_execution_policy.py",
            "disposition": "focused_test",
            "reason": "Pins source-bound policy fixture behavior.",
        },
    ]

    semantic_rows = [
        {
            "owner_lane": "same_symbol_same_instrument_lifecycle_v4",
            "dependency_status": "handoff_contract_materialized",
            "contract": "open trade versus new candidate competition, duplicate exposure, and same-instrument risk remain first-class lifecycle decisions.",
        },
        {
            "owner_lane": "partial_be_trailing_stale_thesis_exit_policy_v4",
            "dependency_status": "handoff_contract_materialized",
            "contract": "live micro-partial sizing, residual ticket mapping, BE/trailing/stale-thesis policy promotion remain first-class exit-policy decisions.",
        },
        {
            "owner_lane": "probability_debate_team_engine_v4",
            "dependency_status": "handoff_contract_materialized",
            "contract": "numeric close/reduce/hold/no-trade/scale/reverse theses and EV selection remain first-class probability/debate decisions.",
        },
        {
            "owner_lane": "follow_avoid_mixed_numeric_confluence_v4",
            "dependency_status": "handoff_contract_materialized",
            "contract": "FOLLOW/AVOID/MIXED is numeric evidence only and never automatic trade permission.",
        },
        {
            "owner_lane": "wave4_wave5_ml_feature_label_store_contract",
            "dependency_status": "prospective_capture_contract_materialized",
            "contract": "MFE, MAE, giveback, stale thesis, harvest failure, and stop/target efficiency are label-store fields with no-leak/as-of source hashes.",
        },
    ]

    source_gap_rows = [
        {
            "row_id": "source_gap:broker_counterfactual_pnl_forbidden",
            "status": "bounded_by_evidence_class",
            "gap": "broker-real counterfactual PnL for alternate exits is not claimed",
            "repair_or_next_requirement": "sealed replay/validation owner can test rules without broker-real counterfactual PnL language",
        },
        {
            "row_id": "source_gap:partial_live_sizing_handoff",
            "status": "bounded_to_first_class_owner",
            "gap": "micro-partial live volume and residual-ticket policy is not activated by this lane",
            "repair_or_next_requirement": "partial_be_trailing_stale_thesis_exit_policy_v4 must own live residual volume policy and promotion gate",
        },
        {
            "row_id": "source_gap:filled_trade_tick_gap",
            "status": "exact_source_gap_preserved",
            "gap": "one filled-trade stale-thesis source row had no tick rows in Wave2 stale-thesis ledger",
            "affected_rows": sum(
                1 for row in stale_rows if row.get("status") == "source_gap_no_tick_rows"
            ),
            "repair_or_next_requirement": "data capture/source repair owner must hydrate or prospectively capture exact tick path",
        },
    ]

    instruction_coverage = {
        "goal_session_research_discipline_read_after_preflight": True,
        "research_operating_doctrine_read_after_preflight": True,
        "builder_integration_posture": "production_code_integration_plus_source_bound_repair_replay_design_fixtures",
        "anti_boxing_questions_pursued": [
            "sub_1r_positive_mfe_harvest_before_old_trigger",
            "giveback_after_mfe",
            "stale_thesis_after_positive_mfe",
            "ticket_bound_runtime_state",
            "ML label capture handoff",
        ],
        "no_arbitrary_top_n": True,
        "all_material_rows_before_ranking": {
            "filled_trade_source_coverage_rows": len(source_coverage_rows),
            "loser_mfe_fixture_rows": len(fixture_rows),
        },
        "forbidden_surfaces_untouched": True,
        "validation_result_status": False,
        "outcome_result_rows_status": False,
        "broker_runtime_change_status": False,
    }

    searched_rows = [
        {
            "root": str(PROMPT_PATH),
            "status": "read",
            "material_use": "controlling lane requirements",
        },
        {
            "root": str(STARTER_PATH),
            "status": "read",
            "material_use": "resume and completion constraints",
        },
        {
            "root": str(WAVE2_DIR),
            "status": "searched_and_consumed",
            "material_use": "Wave2 source rows, ownership contracts, and causal model",
        },
        {
            "root": "src/components/execution.py",
            "status": "read_and_modified",
            "material_use": "production execution management overlay",
        },
        {
            "root": "src/research/dynamic_execution_policy.py",
            "status": "read_and_modified",
            "material_use": "source-bound replay policy",
        },
        {
            "root": "config/agent_config.yaml",
            "status": "read_and_modified",
            "material_use": "default-off config authority",
        },
        {
            "root": "tests/test_limit_order_flow.py and tests/test_dynamic_execution_policy.py",
            "status": "read_and_modified",
            "material_use": "focused tests",
        },
        {
            "root": "shadow_logs",
            "status": "bounded_by_live_state_lfs_pointer_status",
            "material_use": "not used for row-level claims in this sparse worktree",
        },
    ]

    context_anchor = {
        "generated_at_utc": generated_at,
        "lane": "profit_harvest_mfe_capture_v4",
        "branch": git_value("branch", "--show-current"),
        "head": git_value("rev-parse", "HEAD"),
        "main": git_value("rev-parse", "main"),
        "origin_main": git_value("rev-parse", "origin/main"),
        "prompt_path": str(PROMPT_PATH),
        "starter_path": str(STARTER_PATH),
        "route_dir": str(ROUTE_DIR),
        "wave2_status": causal_model.get("status"),
        "wave2_primary_failure_model": causal_model.get("primary_failure_model"),
        "ownership_wave3_lanes": ownership.get("wave3_lanes"),
        "active_boundaries": {
            "validation_result_status": False,
            "outcome_result_rows_status": False,
            "broker_runtime_change_status": False,
        },
    }

    write_json(ROUTE_DIR / "WAVE3_CONTEXT_ANCHOR.json", context_anchor)
    write_json(ROUTE_DIR / "WAVE3_PROFIT_HARVEST_MFE_TRIGGER_CONTRACT.json", trigger_contract)
    write_jsonl(ROUTE_DIR / "WAVE3_PROFIT_HARVEST_FILLED_TRADE_SOURCE_COVERAGE.jsonl", source_coverage_rows)
    write_jsonl(ROUTE_DIR / "WAVE3_PROFIT_HARVEST_LOSER_MFE_FIXTURES.jsonl", fixture_rows)
    write_jsonl(ROUTE_DIR / "WAVE3_DECISION_LEDGER.jsonl", decision_rows)
    write_jsonl(ROUTE_DIR / "WAVE3_PRODUCTION_CODE_DISPOSITION_LEDGER.jsonl", disposition_rows)
    write_jsonl(ROUTE_DIR / "WAVE3_SEMANTIC_OWNERSHIP_HANDOFF_LEDGER.jsonl", semantic_rows)
    write_jsonl(ROUTE_DIR / "WAVE3_SOURCE_GAP_AND_REPAIR_LEDGER.jsonl", source_gap_rows)
    write_jsonl(ROUTE_DIR / "WAVE3_SEARCHED_ROOT_LEDGER.jsonl", searched_rows)
    write_json(ROUTE_DIR / "WAVE3_INSTRUCTION_COVERAGE_CHECKLIST.json", instruction_coverage)

    fixture_status_counts = Counter(row["harvest_failure_status"] for row in fixture_rows)
    write_json(
        ROUTE_DIR / "WAVE3_PROFIT_HARVEST_FIXTURE_SUMMARY.json",
        {
            "generated_at_utc": generated_at,
            "filled_trade_source_coverage_rows": len(source_coverage_rows),
            "loser_mfe_fixture_rows": len(fixture_rows),
            "harvest_failure_status_counts": dict(sorted(fixture_status_counts.items())),
            "source_boundary": "no_broker_real_counterfactual_pnl_claim",
            "broker_runtime_change_status": False,
        },
    )

    saturation = f"""# Wave3 Profit Harvest MFE Capture V4 Saturation Self Red Team

Generated: {generated_at}

## Same-Class Gaps Pursued

- All Wave2 filled-trade profit-harvest rows were materialized: `{len(source_coverage_rows)}`.
- All Wave2 loser-positive-MFE harvest rows were materialized as fixtures: `{len(fixture_rows)}`.
- The production execution surface was read and patched as a default-off overlay rather than only producing a ledger.
- The pure replay surface was patched so partial, BE/trail, giveback close, and stale-thesis close are source-bound design fixtures.

## Evidence-Class Guards

- Broker-real counterfactual PnL is not claimed.
- redacted_account row evidence is not copied into FTMO broker truth.
- Live deployment, broker/account/order/deal/position mutation, credentials, paid/vendor calls, active VPS process changes, and remote push remain untouched.

## Red-Team Outcomes

- A stale close without ticket-bound state would be unsafe; execution integration requires `gtos_vnext_dynamic_policy_applied`.
- A micro-partial live rule without first-class residual sizing would be under-owned; the source-bound replay fixture is materialized and live residual policy is handed to `partial_be_trailing_stale_thesis_exit_policy_v4`.
- A sampled fixture set would lose small loser-positive-MFE cases; the fixture ledger preserves all Wave2 rows before summaries.
"""
    (ROUTE_DIR / "WAVE3_SATURATION_SELF_RED_TEAM.md").write_text(saturation, encoding="utf-8")

    files = sorted(path for path in ROUTE_DIR.iterdir() if path.is_file())
    manifest = {
        "generated_at_utc": generated_at,
        "lane": "profit_harvest_mfe_capture_v4",
        "route_dir": str(ROUTE_DIR),
        "artifact_count": len(files) + 1,
        "required_output_floor": {
            "profit_harvest_policy_code": [
                "src/components/execution.py",
                "src/research/dynamic_execution_policy.py",
            ],
            "mfe_giveback_trigger_contract": "WAVE3_PROFIT_HARVEST_MFE_TRIGGER_CONTRACT.json",
            "loser_mfe_fixture_set": "WAVE3_PROFIT_HARVEST_LOSER_MFE_FIXTURES.jsonl",
            "focused_harvest_tests": [
                "tests/test_limit_order_flow.py",
                "tests/test_dynamic_execution_policy.py",
            ],
            "verifier": "scripts/verify_wave3_profit_harvest_mfe_capture_v4.py",
        },
        "artifacts": [
            {
                "path": path.relative_to(ROUTE_DIR).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
        "boundary_fields": {
            "validation_result_status": False,
            "outcome_result_rows_status": False,
            "broker_runtime_change_status": False,
        },
    }
    write_json(ROUTE_DIR / "WAVE3_OUTPUT_MANIFEST.json", manifest)
    print(json.dumps({"route_dir": str(ROUTE_DIR), "artifacts": manifest["artifact_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
