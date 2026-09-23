"""Update Friday microscope route artifacts after verified code repairs."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.build_vnext_friday_microscope_freeze_inventory as freeze


ROUTE_DIR = freeze.ROUTE_DIR
CODE_VERIFIER = ROUTE_DIR / "FRIDAY_CODE_REPAIR_VERIFIER.py"
CODE_VERIFICATION = ROUTE_DIR / "FRIDAY_CODE_REPAIR_VERIFICATION.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def update_repair_ledger(now: str) -> None:
    existing = read_jsonl(freeze.REPAIR_LEDGER)
    by_id = {row.get("defect_id"): row for row in existing if row.get("defect_id")}
    updates = [
        {
            "schema_version": "friday_microscope_repair_ledger_v1",
            "timestamp_utc": now,
            "defect_id": "FRIDAY_FULL_SELECTED_DENOMINATOR_JOIN_NOT_BUILT_YET",
            "defect_class": "missing_replay_denominator_reconciliation",
            "status": "repaired_initial_friday_denominator_bridge_built",
            "evidence": "FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_LEDGER.jsonl and FRIDAY_RAW_VS_SELECTED_DENOMINATOR_RECONCILIATION.json generated and verified for 328 primary rows",
            "next_action": "broaden row-level Stage04 selected shard scan and quality-selector replay before production-impacting selector decision",
        },
        {
            "schema_version": "friday_microscope_repair_ledger_v1",
            "timestamp_utc": now,
            "defect_id": "FRIDAY_SAME_SYMBOL_VNEXT_LIFECYCLE_SOURCE_FAIL_CLOSED",
            "defect_class": "permissions_same_symbol_lifecycle_guard",
            "status": "repaired_code_and_test_verified",
            "evidence": "src/components/permissions.py fails closed when selected-cell vNext same-symbol position source raises or returns None; FRIDAY_CODE_REPAIR_VERIFICATION.json check same_symbol_vnext_position_source_error_fails_closed",
            "test": "py -3 -m pytest tests/test_concurrent_cap.py::TestGate3Integration::test_vnext_same_symbol_position_source_error_fails_closed -q",
        },
        {
            "schema_version": "friday_microscope_repair_ledger_v1",
            "timestamp_utc": now,
            "defect_id": "FRIDAY_PENDING_LIFECYCLE_AUDIT_STALE_TERMINAL_SELECTION",
            "defect_class": "pending_limit_lifecycle_audit_terminal_selection",
            "status": "repaired_code_and_test_verified",
            "evidence": "src/research_infra/pending_limit_lifecycle_audit.py now orders lifecycle state by fill/created/timestamp before checked candle time; NAS100 2026-05-29 14:15 fill wins over stale 14:29 pending poll",
            "test": "py -3 -m pytest tests/test_pending_limit_lifecycle_audit.py -q",
        },
        {
            "schema_version": "friday_microscope_repair_ledger_v1",
            "timestamp_utc": now,
            "defect_id": "FRIDAY_NET_BROKER_R_ACCOUNTING_FIELDS_ADDED",
            "defect_class": "broker_cost_accounting_net_r_logging",
            "status": "repaired_code_and_test_verified",
            "evidence": "close slippage telemetry and broker_actual_r_audit now emit cash risk, broker profit/commission/swap, broker_net_profit, broker_net_r, broker_net_r_status, and cost_adjustment_r when source fields exist",
            "tests": [
                "py -3 -m pytest tests/test_broker_actual_r_audit.py::test_broker_actual_r_audit_joins_mt5_account_history_export -q",
                "py -3 -m pytest tests/test_slippage_shadow_logger.py::TestCloseSideSlippage::test_long_close_adverse_fill tests/test_slippage_shadow_logger.py::test_close_slippage_wire_carries_source_repair_identity -q",
            ],
        },
    ]
    for row in updates:
        by_id[row["defect_id"]] = row
    rows = [row for row in existing if not row.get("defect_id") or row.get("defect_id") not in by_id]
    rows.extend(by_id.values())
    write_jsonl(freeze.REPAIR_LEDGER, rows)


def update_route_state(now: str) -> None:
    state = load_json(freeze.STATE_PATH, {})
    finished = set(state.get("finished_artifacts") or [])
    finished.update(
        [
            CODE_VERIFIER.relative_to(ROOT).as_posix(),
            CODE_VERIFICATION.relative_to(ROOT).as_posix(),
        ]
    )
    tests = set(state.get("tests_run") or [])
    tests.update(
        [
            "py -3 -m py_compile src/components/permissions.py src/research_infra/pending_limit_lifecycle_audit.py src/components/slippage_shadow_logger.py src/components/execution.py src/research_infra/broker_actual_r_audit.py tests/test_pending_limit_lifecycle_audit.py tests/test_concurrent_cap.py tests/test_broker_actual_r_audit.py tests/test_slippage_shadow_logger.py",
            "py -3 -m pytest tests/test_concurrent_cap.py tests/test_pending_limit_lifecycle_audit.py tests/test_broker_actual_r_audit.py -q",
            "py -3 -m pytest tests/test_slippage_shadow_logger.py -q",
            "python research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31/FRIDAY_CODE_REPAIR_VERIFIER.py --write",
        ]
    )
    state.update(
        {
            "updated_at_utc": now,
            "current_head": git_head(),
            "current_stage": "stage_12_initial_code_repairs_verified",
            "finished_artifacts": sorted(finished),
            "tests_run": sorted(tests),
            "open_defects": [
                {
                    "defect_id": "FRIDAY_QUALITY_SELECTOR_CONTAMINATED_WEEKEND_SOURCE_REQUIRES_CLEAN_REPLAY_DECISION",
                    "status": "open_broad_selected_replay_decision_required_before_execution_selector_change",
                },
                {
                    "defect_id": "FRIDAY_ACCOUNT_EXPOSURE_PROP_DEFERRAL_REPLAY_REQUIRED",
                    "status": "open_stage_10_account_exposure_reconstruction_required",
                },
                {
                    "defect_id": "FRIDAY_MICRO_PRICE_ACTION_ANATOMY_NOT_BUILT",
                    "status": "open_stage_05_required",
                },
                {
                    "defect_id": "FRIDAY_EXECUTION_POLICY_SELECTED_DENOMINATOR_REPLAY_NOT_BUILT",
                    "status": "open_stage_08_required",
                },
            ],
            "repaired_defects": [
                "FRIDAY_FULL_SELECTED_DENOMINATOR_JOIN_NOT_BUILT_YET",
                "FRIDAY_SAME_SYMBOL_VNEXT_LIFECYCLE_SOURCE_FAIL_CLOSED",
                "FRIDAY_PENDING_LIFECYCLE_AUDIT_STALE_TERMINAL_SELECTION",
                "FRIDAY_NET_BROKER_R_ACCOUNTING_FIELDS_ADDED",
            ],
            "exact_next_action": "Build Stage 05 microscopic price-action anatomy and Stage 09 quality-selector broad replay audit; keep account-exposure prop deferral reconstruction open.",
        }
    )
    freeze.write_json(freeze.STATE_PATH, state)


def update_completion_audit(now: str) -> None:
    audit = load_json(freeze.COMPLETION_AUDIT, {})
    completed = set(audit.get("completed_requirements") or [])
    completed.update(
        [
            "Stage 03 canonical event ledger and verifier built",
            "Stage 04 initial full-vNext Friday denominator bridge built",
            "Stage 06 placed-trade autopsy and broker truth ledgers built",
            "Stage 07 initial refusal/stale-blocker and market starvation ledgers built",
            "same-symbol vNext lifecycle source fail-closed repair implemented and verified",
            "pending lifecycle audit stale terminal selection repair implemented and verified",
            "broker gross/net R accounting fields implemented in close telemetry and broker audit helpers",
        ]
    )
    audit.update(
        {
            "generated_at_utc": now,
            "status": "not_complete",
            "completion_decision": "keep_goal_active",
            "completed_requirements": sorted(completed),
        }
    )
    freeze.write_json(freeze.COMPLETION_AUDIT, audit)


def update_manifest() -> None:
    paths = sorted(path for path in ROUTE_DIR.iterdir() if path.is_file())
    freeze.write_json(freeze.OUTPUT_MANIFEST, freeze.output_manifest(paths))


def append_control(now: str) -> None:
    verification = load_json(CODE_VERIFICATION, {})
    freeze.append_jsonl(
        freeze.CONTROL_LEDGER,
        {
            "schema_version": "friday_microscope_control_ledger_v1",
            "timestamp_utc": now,
            "stage": "stage_12_initial_code_repairs_verified",
            "action": "recorded_code_repairs_tests_and_route_verification",
            "git_head": git_head(),
            "verification_ok": verification.get("ok"),
            "verification_issue_count": verification.get("issue_count"),
            "checks": [check.get("name") for check in verification.get("checks", [])],
        },
    )


def main() -> int:
    now = utc_now()
    if not CODE_VERIFICATION.exists():
        raise SystemExit(f"Missing {CODE_VERIFICATION}; run FRIDAY_CODE_REPAIR_VERIFIER.py --write first")
    update_repair_ledger(now)
    update_route_state(now)
    update_completion_audit(now)
    append_control(now)
    update_manifest()
    print(json.dumps({"ok": True, "updated_at_utc": now}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
