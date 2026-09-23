from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_vnext_live_replay_gate_stack_audit import (
    LEDGER_PATH,
    REQUIRED_GATE_IDS,
    SUMMARY_PATH,
    build,
)


VERIFY_PATH = (
    REPO_ROOT
    / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/"
    "LIVE_REPLAY_GATE_STACK_VERIFICATION.json"
)

LIVE_GATE_COVERAGE_PATTERNS = {
    "gate1_grade_direction_touch_inverted_liquidity_cluster": [
        ("src/components/permissions.py", "_reject_if_touch_count_too_high"),
        ("src/components/permissions.py", "_reject_if_sl_behind_liquidity_cluster"),
        ("src/components/permissions.py", "inverted_tp_sl_blocked_negative_expectancy"),
    ],
    "orchestrator_pre_candle_halt_sprt_kz_trade_cap": [
        ("src/components/orchestrator.py", "_check_sprt_class_halt_gate"),
        ("src/components/orchestrator.py", "_check_kill_zone_trade_cap"),
        ("src/components/orchestrator.py", "_check_and_trigger_daily_loss_stop"),
    ],
    "execution_order_send_retcode_volume_margin": [
        ("src/components/execution.py", "_calculate_lots"),
        ("src/components/execution.py", "_normalize_volume"),
        ("src/components/execution.py", "order_send"),
    ],
    "candidate_intelligence_packet_null_zero_guard": [
        ("src/components/orchestrator.py", "_refresh_vnext_candidate_intelligence_packet"),
        ("src/components/orchestrator.py", "missing_reason"),
        ("tests/test_vnext_broader_origin_orchestrator.py", "test_broader_origin_dynamic_refusal_record_has_complete_candidate_packet"),
    ],
    "heartbeat_flatten_orphan_reconciliation": [
        ("src/safety/heartbeat_monitor.py", "flatten_enabled"),
        ("scripts/watchdog.ps1", "orphan"),
        ("scripts/verify_shadow_log_integrity.py", "account_truth_reconciliation_status"),
    ],
}


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    value = json.loads(line)
                    if isinstance(value, dict):
                        rows.append(value)
    except (OSError, json.JSONDecodeError):
        return rows
    return rows


def verify() -> dict[str, Any]:
    expected_rows, expected_summary = build()
    current_rows = _read_jsonl(LEDGER_PATH)
    current_summary = _read_json(SUMMARY_PATH, {})
    issues: list[dict[str, Any]] = []

    if len(current_rows) != len(expected_rows):
        issues.append({
            "code": "ledger_row_count_mismatch",
            "current": len(current_rows),
            "expected": len(expected_rows),
        })
    current_gate_ids = {row.get("gate_id") for row in current_rows}
    missing = sorted(set(REQUIRED_GATE_IDS) - current_gate_ids)
    if missing:
        issues.append({"code": "missing_required_gate_ids", "gate_ids": missing})

    rows_by_gate = {row.get("gate_id"): row for row in current_rows}
    for gate_id, patterns in LIVE_GATE_COVERAGE_PATTERNS.items():
        row = rows_by_gate.get(gate_id)
        if not row:
            continue
        row_sources = "\n".join(str(item) for item in row.get("code_config_source") or [])
        row_proof = "\n".join(str(item) for item in row.get("proof") or [])
        for rel_path, pattern in patterns:
            path = REPO_ROOT / rel_path
            if not path.exists():
                issues.append({
                    "code": "coverage_source_missing",
                    "gate_id": gate_id,
                    "path": rel_path,
                })
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                issues.append({
                    "code": "coverage_source_unreadable",
                    "gate_id": gate_id,
                    "path": rel_path,
                    "error": str(exc),
                })
                continue
            if pattern not in text:
                issues.append({
                    "code": "coverage_pattern_missing_from_source",
                    "gate_id": gate_id,
                    "path": rel_path,
                    "pattern": pattern,
                })
            if rel_path not in row_sources and rel_path not in row_proof:
                issues.append({
                    "code": "coverage_pattern_not_referenced_by_ledger_row",
                    "gate_id": gate_id,
                    "path": rel_path,
                    "pattern": pattern,
                })

    comparable_expected = dict(expected_summary)
    comparable_expected.pop("generated_at_utc", None)
    comparable_current = dict(current_summary or {})
    comparable_current.pop("generated_at_utc", None)
    if comparable_current != comparable_expected:
        issues.append({"code": "summary_not_current"})

    required_fields = {
        "gate_id",
        "gate_name",
        "code_config_source",
        "runs_live",
        "ran_in_vnext_replay",
        "classification",
        "affected_symbols",
        "affected_origin_families",
        "affected_sessions",
        "affected_policies",
        "counts",
        "r_frequency_impact",
        "repair_decision",
        "proof",
    }
    for idx, row in enumerate(current_rows):
        missing_fields = sorted(required_fields - set(row))
        if missing_fields:
            issues.append({
                "code": "ledger_row_missing_fields",
                "row_index": idx,
                "gate_id": row.get("gate_id"),
                "missing_fields": missing_fields,
            })
        if row.get("runs_live") is True and row.get("classification") == "stale-old-system":
            issues.append({
                "code": "stale_old_system_gate_still_live_authoritative",
                "gate_id": row.get("gate_id"),
            })
        if row.get("runs_live") is True and not row.get("repair_decision"):
            issues.append({
                "code": "live_gate_missing_repair_decision",
                "gate_id": row.get("gate_id"),
            })
        if row.get("runs_live") is True and not row.get("proof"):
            issues.append({
                "code": "live_gate_missing_proof",
                "gate_id": row.get("gate_id"),
            })

    summary_assertions = (current_summary or {}).get("repair_assertions", {})
    for key in (
        "raw_broader_origin_gate1_terminal_authority_removed",
        "final_gate1_runs_after_vnext_repair",
        "dynamic_target_gate1_static_2r_ceiling_removed_for_vnext",
        "selected_cell_and_prop_rechecked_before_order",
    ):
        if summary_assertions.get(key) is not True:
            issues.append({"code": "missing_true_repair_assertion", "assertion": key})
    if summary_assertions.get("old_fixed_15r_j46_j49_live_default_allowed") is not False:
        issues.append({"code": "old_fixed_15r_j46_j49_default_not_blocked"})

    selected_projection = (current_summary or {}).get("selected_trade_projection", {})
    if isinstance(selected_projection, dict) and "selected_policy_counts" in selected_projection:
        issues.append({
            "code": "stale_stage04_selected_policy_counts_label_present",
            "reason": "Stage04 be_after_trigger projection must be scoped as historical input, not current production policy",
        })
    current_policy_distribution = (current_summary or {}).get(
        "current_production_dynamic_policy_distribution",
        {},
    )
    if not isinstance(current_policy_distribution, dict) or not current_policy_distribution:
        issues.append({"code": "missing_current_production_policy_distribution"})
    else:
        if "momentum_exhaustion" not in current_policy_distribution:
            issues.append({"code": "current_policy_distribution_missing_momentum_exhaustion"})
        if "partial_be_runner" not in current_policy_distribution:
            issues.append({"code": "current_policy_distribution_missing_partial_be_runner"})
        if set(current_policy_distribution) == {"be_after_trigger"}:
            issues.append({"code": "current_policy_distribution_stale_be_only"})

    broker_ready = (current_summary or {}).get(
        "broker_placement_ready_selected_rows_after_replay_included_live_gates"
    )
    replay_rows = (current_summary or {}).get("replay_selected_rows")
    if not isinstance(broker_ready, int) or broker_ready <= 0:
        issues.append({"code": "missing_broker_placement_ready_selected_rows"})
    if isinstance(broker_ready, int) and isinstance(replay_rows, int) and broker_ready > replay_rows:
        issues.append({
            "code": "broker_ready_rows_exceed_selected_rows",
            "broker_ready": broker_ready,
            "selected": replay_rows,
        })

    return {
        "schema_version": "vnext_live_replay_gate_stack_verification_v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "ledger_rows": len(current_rows),
        "required_gate_count": len(REQUIRED_GATE_IDS),
        "broker_placement_ready_selected_rows_after_replay_included_live_gates": broker_ready,
        "replay_selected_rows": replay_rows,
        "ledger_path": str(LEDGER_PATH.relative_to(REPO_ROOT)),
        "summary_path": str(SUMMARY_PATH.relative_to(REPO_ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = verify()
    if not args.check:
        VERIFY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
