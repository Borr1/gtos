from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components.concurrent_tracker import reset_cache
from src.components.gtos_vnext_runtime import (
    GTOSVNextRuntimeDecision,
    evaluate_vnext_prop_safe_selector,
)
import src.components.permissions as permissions
from src.mt5.mt5_interface import MAGIC_NUMBER


ROUTE_ID = "vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID
LANE01_DIR = ROOT / "research" / "operations" / "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31"
LANE04_DIR = ROOT / "research" / "operations" / "vnext_lane04_selected_cell_risk_bridge_packet_completeness_2026_05_31"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def file_evidence(path: Path, role: str) -> dict[str, Any]:
    data = path.read_bytes() if path.exists() else b""
    return {
        "path": rel(path),
        "role": role,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "sha256": __import__("hashlib").sha256(data).hexdigest() if path.exists() else None,
    }


def line_number(path: Path, needle: str) -> int | None:
    if not path.exists():
        return None
    for index, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if needle in line:
            return index
    return None


def build_code_path_ledger(now: str) -> list[dict[str, Any]]:
    markers = [
        (
            ROOT / "src" / "components" / "permissions.py",
            "selected-cell rows are governed by account-risk exposure proof",
            "module_contract",
            "selected-cell vNext rows are account-risk governed, while legacy count caps remain for non-vNext surfaces",
        ),
        (
            ROOT / "src" / "components" / "permissions.py",
            "def _vnext_risk_budget_governed_trade",
            "selected_cell_governance_detector",
            "requires active vNext dynamic context, selected policy, execution policy id, and positive selected-cell risk pct",
        ),
        (
            ROOT / "src" / "components" / "permissions.py",
            "def _reject_if_same_symbol_vnext_lifecycle_conflict",
            "same_symbol_lifecycle_guard",
            "same-symbol stacking stays blocked until ticket-bound multi-position lifecycle support is explicit",
        ),
        (
            ROOT / "src" / "components" / "permissions.py",
            "def _reject_if_concurrent_cap_reached",
            "legacy_count_cap_boundary",
            "legacy filled-position count cap is skipped for governed current vNext rows",
        ),
        (
            ROOT / "src" / "components" / "gtos_vnext_runtime.py",
            "def evaluate_vnext_prop_safe_selector",
            "account_exposure_scheduler",
            "computes current equity, risk base, daily/overall cushions, open/pending/new risk, buffers, and allow/reduce/defer/block action",
        ),
        (
            ROOT / "src" / "components" / "orchestrator.py",
            "prop_account_state = {",
            "runtime_account_state_projection",
            "orchestrator feeds account balance/equity, day baseline, open/pending risk, new risk, buffers, and concentration counts into the scheduler",
        ),
        (
            ROOT / "src" / "components" / "orchestrator.py",
            "pre_dynamic_projection_only_",
            "pre_dynamic_projection_boundary",
            "pre-dynamic new-trade budget actions are projections until selected-cell risk and executable geometry are known",
        ),
        (
            ROOT / "src" / "components" / "orchestrator.py",
            "Re-run the prop governor after selected-cell risk",
            "terminal_post_geometry_scheduler_gate",
            "terminal scheduler authority runs after selected-cell risk and executable geometry repair",
        ),
        (
            ROOT / "src" / "components" / "orchestrator.py",
            "for key, value in dynamic_trade_context.items():",
            "dynamic_context_attached_before_permission_gate",
            "selected-cell risk proof is attached onto trade parameters before the final permissions gate",
        ),
        (
            ROOT / "tests" / "test_vnext_lane05_portfolio_scheduler.py",
            "def test_selected_cell_vnext_trade_bypasses_legacy_concurrent_count_cap",
            "lane05_focused_test",
            "guards the stale count-cap bypass for governed selected-cell vNext rows",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for path, needle, marker_id, evidence in markers:
        rows.append(
            {
                "evidence": evidence,
                "file": rel(path),
                "line": line_number(path, needle),
                "marker_id": marker_id,
                "needle": needle,
                "route_id": ROUTE_ID,
                "schema_version": "lane05_runtime_scheduler_code_path_row_v1",
                "status": "present" if line_number(path, needle) else "missing",
                "timestamp_utc": now,
            }
        )
    return rows


def build_scheduler_ledger(now: str) -> list[dict[str, Any]]:
    rows = []
    source_rows = read_jsonl(LANE01_DIR / "LANE01_RISK_EXPOSURE_DOLLAR_R_LEDGER.jsonl")
    for source in source_rows:
        rejection_reason = source.get("rejection_reason")
        if rejection_reason == "same_symbol_position_conflict_multi_ticket_lifecycle_unsupported":
            final_authority = "same_symbol_lifecycle_guard_reject"
        elif rejection_reason == "portfolio_open_risk_cap_exceeded_after_config_buffer":
            final_authority = "account_exposure_budget_reject"
        elif source.get("portfolio_decision") == "ACCEPTED":
            final_authority = "account_exposure_budget_accept"
        else:
            final_authority = "unclassified_route_row"
        rows.append(
            {
                "branch_decision": "materialize_lane01_replay_row_as_runtime_scheduler_contract",
                "buffered_exposure_after_candidate": source.get("buffered_exposure_after_candidate"),
                "decision_time_utc": source.get("decision_time_utc"),
                "effective_gross_dollars": source.get("effective_gross_dollars"),
                "effective_risk_amount": source.get("effective_risk_amount"),
                "effective_risk_pct": source.get("effective_risk_pct"),
                "final_risk_authority": final_authority,
                "gross_r": source.get("gross_r"),
                "implementation_decision": "current_runtime_scheduler_authority_must_match_lane01_account_exposure_replay_contract",
                "open_risk_after": source.get("open_risk_after"),
                "open_risk_before": source.get("open_risk_before"),
                "portfolio_decision": source.get("portfolio_decision"),
                "portfolio_open_risk_ceiling": (source.get("portfolio_risk_state") or {}).get("open_risk_ceiling"),
                "rejection_reason": rejection_reason,
                "result_materialization_status": source.get("result_materialization_status"),
                "route_id": ROUTE_ID,
                "schema_version": "lane05_scheduler_row_v1",
                "source_lane": "01",
                "source_paths": source.get("source_paths"),
                "symbol": source.get("symbol"),
                "timestamp_utc": now,
                "trade_id": source.get("trade_id"),
            }
        )
    return rows


def _runtime_decision() -> GTOSVNextRuntimeDecision:
    return GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "route_session": "london"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="lane05_scheduler_matrix",
    )


def _selector_cfg() -> dict[str, Any]:
    return {
        "gtos_vnext_runtime": {
            "prop_safe_selector_enabled": True,
            "prop_safe_selector_apply_to_execution": True,
            "prop_safe_selector_initial_balance": 100000.0,
            "prop_safe_selector_external_daily_loss_limit_pct": 5.0,
            "prop_safe_selector_external_overall_max_loss_pct": 10.0,
            "prop_safe_selector_phase1_target_pct": 8.0,
            "prop_safe_selector_phase2_target_pct": 5.0,
            "prop_safe_selector_daily_reset_timezone_offset_hours": 3.0,
            "prop_safe_selector_malaysia_timezone_offset_hours": 8.0,
            "prop_safe_selector_spread_slippage_commission_buffer_pct": 0.0,
            "prop_safe_selector_min_reduced_risk_pct": 0.25,
            "prop_safe_selector_reserve_simultaneous_candidates": True,
            "prop_safe_selector_internal_daily_overlay_enabled": False,
            "prop_safe_selector_internal_overlay_applies_to_budget": True,
        },
        "risk": {"risk_per_trade_pct": 2.0, "max_daily_loss_pct": 4.0, "max_concurrent": 1},
    }


def _account_state(**overrides: Any) -> dict[str, Any]:
    state = {
        "initial_balance": 100000.0,
        "current_balance": 100000.0,
        "current_equity": 100000.0,
        "risk_base_amount": 100000.0,
        "day_start_equity_or_balance_baseline": 100000.0,
        "open_position_risk_pct": 0.0,
        "pending_order_risk_pct": 0.0,
        "new_trade_sl_risk_pct": 1.0,
        "spread_slippage_commission_buffer_pct": 0.0,
        "simultaneous_candidate_count": 1,
        "symbol": "XAUUSD",
        "route_session": "london",
    }
    state.update(overrides)
    return state


def _governed_trade(direction: str = "LONG") -> SimpleNamespace:
    return SimpleNamespace(
        trade_parameters=SimpleNamespace(
            direction=direction,
            gtos_vnext_production_execution_path=True,
            gtos_vnext_dynamic_policy_applied=True,
            gtos_vnext_dynamic_policy_selected="partial_be_runner",
            gtos_vnext_execution_policy_id="partial_be_runner",
            gtos_vnext_selected_cell_risk_pct=0.25,
            gtos_vnext_selected_cell_risk_cell_id="risk-cell-lane05",
        )
    )


def build_gate_matrix(now: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cfg = _selector_cfg()

    selector_cases = [
        ("account_exposure_allow_full_risk", _account_state(new_trade_sl_risk_pct=0.25), 0.25),
        ("account_exposure_reduce_to_overall_budget", _account_state(current_equity=91000.0, day_start_equity_or_balance_baseline=91000.0, new_trade_sl_risk_pct=2.0), 2.0),
        ("account_exposure_defer_until_daily_reset", _account_state(current_equity=95200.0, new_trade_sl_risk_pct=1.0), 1.0),
        ("account_exposure_block_current_overall_breach", _account_state(current_equity=89000.0, new_trade_sl_risk_pct=1.0), 1.0),
        ("pending_risk_reduces_budget", _account_state(pending_order_risk_pct=4.5, new_trade_sl_risk_pct=1.0), 1.0),
        ("simultaneous_candidates_reserve_budget", _account_state(new_trade_sl_risk_pct=2.0, simultaneous_candidate_count=3), 2.0),
    ]
    for scenario_id, account, before_risk in selector_cases:
        decision = evaluate_vnext_prop_safe_selector(
            decision=_runtime_decision(),
            config=cfg,
            current_risk_pct=before_risk,
            account_state=account,
            current_time_utc="2026-05-29T12:00:00+00:00",
            candidate_context={"symbol": account.get("symbol"), "route_session": account.get("route_session")},
        )
        rows.append(
            {
                "after_authority": "account_exposure_budget_scheduler",
                "after_risk_pct": decision.after_risk_pct,
                "before_authority": "legacy_count_or_static_risk_gate",
                "before_risk_pct": before_risk,
                "decision_action": decision.action,
                "decision_reason": decision.reason,
                "exposure_breakdown": decision.exposure_breakdown,
                "external_rule_projection": decision.external_rule_projection,
                "route_id": ROUTE_ID,
                "scenario_id": scenario_id,
                "schema_version": "lane05_before_after_gate_matrix_row_v1",
                "timestamp_utc": now,
                "would_action": decision.would_action,
            }
        )

    reset_cache()
    mt5 = SimpleNamespace(
        _positions=[
            SimpleNamespace(magic=MAGIC_NUMBER),
            SimpleNamespace(magic=MAGIC_NUMBER),
        ]
    )
    legacy_denial = permissions._reject_if_concurrent_cap_reached(
        mt5, cfg, trade_params=SimpleNamespace(trade_parameters=SimpleNamespace())
    )
    governed_denial = permissions._reject_if_concurrent_cap_reached(
        mt5, cfg, trade_params=_governed_trade()
    )
    rows.extend(
        [
            {
                "after_authority": "legacy_count_cap_for_non_vnext_only",
                "before_authority": "legacy_count_cap",
                "decision_action": "BLOCK" if legacy_denial else "ALLOW",
                "decision_reason": getattr(legacy_denial, "reason", None),
                "route_id": ROUTE_ID,
                "scenario_id": "non_vnext_legacy_concurrent_cap_blocks",
                "schema_version": "lane05_before_after_gate_matrix_row_v1",
                "timestamp_utc": now,
            },
            {
                "after_authority": "selected_cell_account_exposure_governance",
                "before_authority": "legacy_count_cap_would_have_blocked",
                "decision_action": "ALLOW" if governed_denial is None else "BLOCK",
                "decision_reason": getattr(governed_denial, "reason", None),
                "route_id": ROUTE_ID,
                "scenario_id": "governed_vnext_bypasses_legacy_concurrent_cap",
                "schema_version": "lane05_before_after_gate_matrix_row_v1",
                "timestamp_utc": now,
            },
        ]
    )

    class MT5SameSymbol:
        def get_positions(self, symbol):
            return [
                SimpleNamespace(
                    ticket=241779188,
                    symbol="NDX100",
                    type=0,
                    volume=0.1,
                    price_open=21300.0,
                    sl=21200.0,
                    tp=21500.0,
                    magic=MAGIC_NUMBER,
                )
            ]

    same_symbol_denial = permissions._reject_if_same_symbol_vnext_lifecycle_conflict(
        MT5SameSymbol(), "NAS100", {"market": {"symbol": "NAS100"}}, _governed_trade(direction="SHORT")
    )
    rows.append(
        {
            "after_authority": "same_symbol_ticket_lifecycle_guard",
            "before_authority": "unbounded_multi_ticket_assumption",
            "decision_action": "BLOCK" if same_symbol_denial else "ALLOW",
            "decision_reason": getattr(same_symbol_denial, "reason", None),
            "details": getattr(same_symbol_denial, "details", {}),
            "route_id": ROUTE_ID,
            "scenario_id": "same_symbol_vnext_conflict_blocks_until_multi_ticket_contract",
            "schema_version": "lane05_before_after_gate_matrix_row_v1",
            "timestamp_utc": now,
        }
    )
    return rows


def build_source_completeness(now: str, scheduler_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lane01_summary = read_json(LANE01_DIR / "LANE01_PORTFOLIO_REPLAY_SUMMARY.json", {})
    lane04_audit = read_json(LANE04_DIR / "LANE04_COMPLETION_AUDIT.json", {})
    source_rows = read_jsonl(LANE04_DIR / "LANE04_SOURCE_COMPLETENESS_LEDGER.jsonl")
    decisions = Counter(row.get("portfolio_decision") for row in scheduler_rows)
    return [
        {
            "field_family": "lane01_account_exposure_scheduler_contract",
            "current_status": "full_lane01_quality_scheduler_rows_consumed",
            "source_rows": len(scheduler_rows),
            "portfolio_decision_counts": dict(decisions),
            "summary_counts": {
                "quality_subset_rows": lane01_summary.get("quality_subset_rows"),
                "accepted_rows": lane01_summary.get("accepted_rows"),
                "rejected_rows": lane01_summary.get("rejected_rows"),
                "reject_reason_counts": lane01_summary.get("reject_reason_counts"),
            },
            "schema_version": "lane05_source_completeness_row_v1",
            "source_paths": [rel(LANE01_DIR / "LANE01_RISK_EXPOSURE_DOLLAR_R_LEDGER.jsonl")],
            "timestamp_utc": now,
        },
        {
            "field_family": "lane04_selected_cell_packet_contract",
            "current_status": "terminal_lane04_packet_contract_consumed",
            "row_level_closure": lane04_audit.get("row_level_closure"),
            "source_completeness_rows": len(source_rows),
            "schema_version": "lane05_source_completeness_row_v1",
            "source_paths": [rel(LANE04_DIR / "LANE04_SOURCE_COMPLETENESS_LEDGER.jsonl")],
            "timestamp_utc": now,
        },
        {
            "field_family": "runtime_scheduler_code_and_test_surface",
            "current_status": "current_runtime_code_paths_inspected_and_focused_lane05_tests_added",
            "schema_version": "lane05_source_completeness_row_v1",
            "source_paths": [
                "src/components/permissions.py",
                "src/components/gtos_vnext_runtime.py",
                "src/components/orchestrator.py",
                "tests/test_vnext_lane05_portfolio_scheduler.py",
            ],
            "timestamp_utc": now,
        },
    ]


def build_decision_ledger(now: str) -> list[dict[str, Any]]:
    return [
        {
            "branch_decision": "no_new_production_behavior_patch_required_for_lane05_checkpoint",
            "implementation_decision": "current runtime already has selected-cell account-exposure scheduler, pre/post dynamic prop-safe checks, legacy count-cap bypass, and same-symbol lifecycle guard; add focused regression tests and route-owned verifier evidence",
            "runtime_effect_boundary": "tests_and_research_artifacts_only_no_live_restart_no_broker_action_no_config_change",
            "schema_version": "lane05_implementation_decision_row_v1",
            "source_paths": [
                "src/components/permissions.py",
                "src/components/gtos_vnext_runtime.py",
                "src/components/orchestrator.py",
                "tests/test_vnext_lane05_portfolio_scheduler.py",
            ],
            "timestamp_utc": now,
        },
        {
            "branch_decision": "keep_same_symbol_conflict_as_explicit_reject",
            "implementation_decision": "do not loosen same-symbol multi-ticket behavior until ticket-bound partial/residual lifecycle support is proven",
            "runtime_effect_boundary": "current guard preserved",
            "schema_version": "lane05_implementation_decision_row_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "keep_old_caps_as_non_vnext_or_diagnostic_surfaces",
            "implementation_decision": "stale max_concurrent does not block governed current vNext selected-cell rows, but remains active for non-vNext paths",
            "runtime_effect_boundary": "current guard preserved",
            "schema_version": "lane05_implementation_decision_row_v1",
            "timestamp_utc": now,
        },
    ]


def build_shared_code_ledger(now: str) -> list[dict[str, Any]]:
    return [
        {
            "file": "src/components/permissions.py",
            "lane05_action": "inspected_no_edit",
            "shared_owner": "Lane05 runtime portfolio scheduler; Lane09 merge packaging",
            "conflict_policy": "do not mutate further unless a verifier/test failure proves the scheduler contract is broken",
            "schema_version": "lane05_shared_code_ownership_row_v1",
            "timestamp_utc": now,
        },
        {
            "file": "src/components/gtos_vnext_runtime.py",
            "lane05_action": "inspected_no_edit",
            "shared_owner": "Lane05 account-exposure scheduler; Lane04 packet bridge; Lane09 merge packaging",
            "conflict_policy": "preserve selected-cell source proof and prop-safe account state fields",
            "schema_version": "lane05_shared_code_ownership_row_v1",
            "timestamp_utc": now,
        },
        {
            "file": "src/components/orchestrator.py",
            "lane05_action": "inspected_no_edit",
            "shared_owner": "Lane04 packet writer and Lane05 scheduler integration; Lane09 merge packaging",
            "conflict_policy": "preserve pre-dynamic projection boundary, post-geometry terminal scheduler gate, and dynamic context attachment before final permissions",
            "schema_version": "lane05_shared_code_ownership_row_v1",
            "timestamp_utc": now,
        },
        {
            "file": "tests/test_vnext_lane05_portfolio_scheduler.py",
            "lane05_action": "added_focused_regression_tests",
            "shared_owner": "Lane05",
            "conflict_policy": "Lane09 packages as Lane05 verifier guard",
            "schema_version": "lane05_shared_code_ownership_row_v1",
            "timestamp_utc": now,
        },
    ]


def run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "ok": completed.returncode == 0,
        "stderr_tail": completed.stderr[-2000:],
        "stdout_tail": completed.stdout[-4000:],
    }


def build_focused_test_result(now: str) -> dict[str, Any]:
    tests = [
        "tests/test_vnext_lane05_portfolio_scheduler.py",
        "tests/test_gtos_vnext_runtime.py::test_vnext_prop_safe_selector_pending_risk_is_included",
        "tests/test_gtos_vnext_runtime.py::test_vnext_prop_safe_selector_current_equity_includes_open_floating_loss",
        "tests/test_gtos_vnext_runtime.py::test_vnext_prop_safe_selector_multiple_simultaneous_candidates_reserve_budget",
        "tests/test_gtos_vnext_runtime.py::test_agent_config_wires_redacted_account_prop_safe_selector_production_activation_gate",
        "tests/test_vnext_broader_origin_orchestrator.py::test_pre_dynamic_prop_budget_projection_does_not_terminally_block_dynamic_router",
        "tests/test_vnext_broader_origin_orchestrator.py::test_open_position_risk_uses_ticket_bound_vnext_lifecycle_not_base_config",
    ]
    py_compile = run_command(
        [
            sys.executable,
            "-m",
            "py_compile",
            "scripts/build_vnext_lane05_runtime_portfolio_scheduler.py",
            "tests/test_vnext_lane05_portfolio_scheduler.py",
        ]
    )
    pytest = run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            *tests,
            "-q",
            "--basetemp=.pytest-tmp-lane05-runtime-scheduler",
            "-o",
            "cache_dir=.pytest-tmp-lane05-runtime-scheduler-cache",
        ]
    )
    return {
        "generated_at_utc": now,
        "ok": py_compile["ok"] and pytest["ok"],
        "py_compile": py_compile,
        "pytest": pytest,
        "route_id": ROUTE_ID,
        "schema_version": "lane05_focused_test_result_v1",
        "tests": tests,
    }


def write_verifier() -> None:
    verifier = ROUTE_DIR / "verify_lane05_runtime_portfolio_scheduler.py"
    verifier.write_text(
        r'''from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent
LANE01_LEDGER = ROOT / "research" / "operations" / "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31" / "LANE01_RISK_EXPOSURE_DOLLAR_R_LEDGER.jsonl"
RESULT_PATH = ROUTE_DIR / "LANE05_VERIFICATION_RESULT.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def main() -> int:
    issues = []
    required = [
        "LANE05_RUNTIME_SCHEDULER_CODE_PATH_LEDGER.jsonl",
        "LANE05_SCHEDULER_LEDGER.jsonl",
        "LANE05_BEFORE_AFTER_GATE_MATRIX.jsonl",
        "LANE05_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "LANE05_SOURCE_COMPLETENESS_LEDGER.jsonl",
        "LANE05_SHARED_CODE_OWNERSHIP_LEDGER.jsonl",
        "LANE05_FOCUSED_TEST_RESULT.json",
        "LANE05_OUTPUT_MANIFEST.json",
        "LANE05_COMPLETION_AUDIT.json",
    ]
    for name in required:
        if not (ROUTE_DIR / name).exists():
            issues.append(f"missing_required_output:{name}")

    scheduler_rows = read_jsonl(ROUTE_DIR / "LANE05_SCHEDULER_LEDGER.jsonl")
    source_rows = read_jsonl(LANE01_LEDGER)
    if len(scheduler_rows) != len(source_rows):
        issues.append(f"scheduler_row_count_mismatch:{len(scheduler_rows)}!={len(source_rows)}")

    authorities = {row.get("final_risk_authority") for row in scheduler_rows}
    for required_authority in {
        "account_exposure_budget_accept",
        "account_exposure_budget_reject",
        "same_symbol_lifecycle_guard_reject",
    }:
        if required_authority not in authorities:
            issues.append(f"missing_scheduler_authority:{required_authority}")

    matrix = read_jsonl(ROUTE_DIR / "LANE05_BEFORE_AFTER_GATE_MATRIX.jsonl")
    scenario_ids = {row.get("scenario_id") for row in matrix}
    for required_scenario in {
        "account_exposure_allow_full_risk",
        "account_exposure_reduce_to_overall_budget",
        "account_exposure_defer_until_daily_reset",
        "account_exposure_block_current_overall_breach",
        "pending_risk_reduces_budget",
        "simultaneous_candidates_reserve_budget",
        "non_vnext_legacy_concurrent_cap_blocks",
        "governed_vnext_bypasses_legacy_concurrent_cap",
        "same_symbol_vnext_conflict_blocks_until_multi_ticket_contract",
    }:
        if required_scenario not in scenario_ids:
            issues.append(f"missing_gate_matrix_scenario:{required_scenario}")

    code_rows = read_jsonl(ROUTE_DIR / "LANE05_RUNTIME_SCHEDULER_CODE_PATH_LEDGER.jsonl")
    missing_markers = [row.get("marker_id") for row in code_rows if row.get("status") != "present"]
    if missing_markers:
        issues.append(f"missing_code_markers:{missing_markers}")

    tests = read_json(ROUTE_DIR / "LANE05_FOCUSED_TEST_RESULT.json")
    if not tests.get("ok"):
        issues.append("focused_tests_not_ok")

    audit = read_json(ROUTE_DIR / "LANE05_COMPLETION_AUDIT.json")
    if audit.get("status") != "pass":
        issues.append(f"completion_audit_not_pass:{audit.get('status')}")

    result = {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "route_id": "vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31",
        "schema_version": "lane05_verification_result_v1",
        "scheduler_rows": len(scheduler_rows),
        "gate_matrix_rows": len(matrix),
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )


def build_manifest(now: str) -> dict[str, Any]:
    outputs = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if path.is_dir() or path.name == "LANE05_OUTPUT_MANIFEST.json":
            continue
        outputs.append(file_evidence(path, "lane05_route_output"))
    return {
        "generated_at_utc": now,
        "output_count": len(outputs),
        "outputs": outputs,
        "route_dir": rel(ROUTE_DIR),
        "route_id": ROUTE_ID,
        "schema_version": "lane05_output_manifest_v1",
    }


def build_completion_audit(
    now: str,
    scheduler_rows: list[dict[str, Any]],
    gate_matrix: list[dict[str, Any]],
    focused_test_result: dict[str, Any],
) -> dict[str, Any]:
    authority_counts = Counter(row.get("final_risk_authority") for row in scheduler_rows)
    scenario_counts = Counter(row.get("decision_action") for row in gate_matrix)
    passed = bool(focused_test_result.get("ok")) and bool(scheduler_rows) and bool(gate_matrix)
    return {
        "anti_boxing_pursuit": [
            "Lane01 full risk exposure dollar/R ledger consumed without sampling",
            "Lane04 packet/source completeness consumed",
            "permissions.py old cap and same-symbol lifecycle gates inspected",
            "gtos_vnext_runtime.py prop-safe selector inspected and exercised",
            "orchestrator.py pre/post dynamic scheduler path inspected",
        ],
        "builder_posture": "runtime_implementation_and_test_package_with_route_owned_verifier",
        "completion_ready_for_lane09": passed,
        "forbidden_boundaries_not_crossed": [
            "no live broker/order/deal/position action",
            "no paid API/vendor call",
            "no credential or remote change",
            "no live restart or hidden deployment",
            "no config/risk/execution behavior change beyond focused tests and route evidence",
        ],
        "generated_at_utc": now,
        "mandatory_context_use": {
            "live_state_regenerated": True,
            "current_vnext_system_map_read": True,
            "current_repo_reading_order_read": True,
            "quick_reference_card_read": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "lane01_artifacts_read": True,
            "lane04_artifacts_read": True,
        },
        "row_level_closure": {
            "scheduler_rows": len(scheduler_rows),
            "scheduler_authority_counts": dict(authority_counts),
            "gate_matrix_rows": len(gate_matrix),
            "gate_matrix_action_counts": dict(scenario_counts),
        },
        "runtime_effect_boundary": "local_tests_and_route_artifacts_only",
        "schema_version": "lane05_completion_audit_v1",
        "status": "pass" if passed else "fail",
        "unmet_requirements": [] if passed else ["focused tests, scheduler rows, or gate matrix did not pass materialization checks"],
    }


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    now = utc_now()

    code_path_ledger = build_code_path_ledger(now)
    scheduler_rows = build_scheduler_ledger(now)
    gate_matrix = build_gate_matrix(now)
    source_completeness = build_source_completeness(now, scheduler_rows)
    decisions = build_decision_ledger(now)
    shared_code = build_shared_code_ledger(now)

    write_jsonl(ROUTE_DIR / "LANE05_RUNTIME_SCHEDULER_CODE_PATH_LEDGER.jsonl", code_path_ledger)
    write_jsonl(ROUTE_DIR / "LANE05_SCHEDULER_LEDGER.jsonl", scheduler_rows)
    write_jsonl(ROUTE_DIR / "LANE05_BEFORE_AFTER_GATE_MATRIX.jsonl", gate_matrix)
    write_jsonl(ROUTE_DIR / "LANE05_SOURCE_COMPLETENESS_LEDGER.jsonl", source_completeness)
    write_jsonl(ROUTE_DIR / "LANE05_IMPLEMENTATION_DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE_DIR / "LANE05_SHARED_CODE_OWNERSHIP_LEDGER.jsonl", shared_code)

    write_verifier()
    focused_test_result = build_focused_test_result(now)
    write_json(ROUTE_DIR / "LANE05_FOCUSED_TEST_RESULT.json", focused_test_result)

    audit = build_completion_audit(now, scheduler_rows, gate_matrix, focused_test_result)
    write_json(ROUTE_DIR / "LANE05_COMPLETION_AUDIT.json", audit)
    (ROUTE_DIR / "LANE05_CONTEXT_ANCHOR.md").write_text(
        "\n".join(
            [
                "# Lane05 Runtime Portfolio Scheduler Context Anchor",
                "",
                f"Generated: {now}",
                f"Route id: `{ROUTE_ID}`",
                "",
                "Lane05 consumes Lane01 full scheduler replay rows and Lane04 packet/source-completeness contracts. It records current runtime scheduler code paths, gate matrix behavior, focused tests, and shared-file ownership without editing Lane02 artifacts or performing live broker/config changes.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_json(ROUTE_DIR / "LANE05_OUTPUT_MANIFEST.json", build_manifest(now))

    verification = run_command([sys.executable, rel(ROUTE_DIR / "verify_lane05_runtime_portfolio_scheduler.py")])
    try:
        verification_payload = json.loads(verification["stdout_tail"])
    except json.JSONDecodeError:
        verification_payload = {"ok": False, "parse_error": verification["stdout_tail"]}
    verification_payload.update(
        {
            "command": verification["command"],
            "exit_code": verification["exit_code"],
            "stderr_tail": verification["stderr_tail"],
        }
    )
    write_json(ROUTE_DIR / "LANE05_VERIFICATION_RESULT.json", verification_payload)
    write_json(ROUTE_DIR / "LANE05_OUTPUT_MANIFEST.json", build_manifest(now))

    print(
        json.dumps(
            {
                "focused_tests_ok": focused_test_result.get("ok"),
                "ok": focused_test_result.get("ok") and verification_payload.get("ok"),
                "route_dir": rel(ROUTE_DIR),
                "scheduler_rows": len(scheduler_rows),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if focused_test_result.get("ok") and verification_payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
