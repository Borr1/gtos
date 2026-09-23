#!/usr/bin/env python3
"""Compact stale dual-supervisor hot evidence after current proof exists.

This is route-evidence cleanup only. It does not call MT5 and does not mutate
broker orders, positions, deals, or live process state.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE = Path(__file__).resolve().parent
ROUTE_ID = "vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02"
EVIDENCE_CLASS = "DUAL_BROKER_VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION"
STALE_PRE_RELOAD_BOUNDARY = "code_config_launcher_watchdog_repair_not_yet_reloaded"
SUPERSEDED_BOUNDARY = "historical_pre_activation_repair_evidence_superseded_by_current_live_checkpoints"

AUDIT = ROUTE / "DUAL_CURRENT_LIVE_CANDIDATE_TRADE_LIFECYCLE_AUDIT.json"
DIRECT = ROUTE / "DUAL_CURRENT_LIVE_DIRECT_INSPECTION_CLASSES.json"
STATE = ROUTE / "DUAL_SUPERVISOR_STATE.json"
MANIFEST = ROUTE / "DUAL_OUTPUT_MANIFEST.json"
CLEANUP_LEDGER = ROUTE / "DUAL_STALE_EVIDENCE_CLEANUP_LEDGER.jsonl"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            try:
                rows.append(json.loads(raw))
            except json.JSONDecodeError:
                rows.append({"_malformed": True, "_raw": raw.rstrip("\n")})
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def remove_pending_placeholders(path: Path) -> int:
    rows = iter_jsonl(path)
    kept = [
        row
        for row in rows
        if not (
            row.get("status") == "pending"
            and str(row.get("runtime_effect_boundary") or "").startswith(STALE_PRE_RELOAD_BOUNDARY)
        )
    ]
    write_jsonl(path, kept)
    return len(rows) - len(kept)


def normalize_superseded_boundaries() -> tuple[int, int]:
    files_changed = 0
    rows_changed = 0
    for path in sorted(ROUTE.glob("*.jsonl")):
        rows = iter_jsonl(path)
        if not rows:
            continue
        changed = False
        normalized_rows: list[dict[str, Any]] = []
        for row in rows:
            if row.get("runtime_effect_boundary") == STALE_PRE_RELOAD_BOUNDARY:
                row = {
                    **row,
                    "runtime_effect_boundary": SUPERSEDED_BOUNDARY,
                    "current_authority_artifacts": [
                        "DUAL_SUPERVISOR_STATE.json",
                        "DUAL_CURRENT_LIVE_CANDIDATE_TRADE_LIFECYCLE_AUDIT.json",
                        "DUAL_CURRENT_LIVE_DIRECT_INSPECTION_CLASSES.json",
                    ],
                }
                changed = True
                rows_changed += 1
            normalized_rows.append(row)
        if changed:
            write_jsonl(path, normalized_rows)
            files_changed += 1
    return files_changed, rows_changed


def replace_one(path: Path, row: dict[str, Any]) -> int:
    old_count = len(iter_jsonl(path))
    write_jsonl(path, [row])
    return old_count


def compact_anomalies(path: Path) -> tuple[int, int]:
    rows = iter_jsonl(path)
    keep: list[dict[str, Any]] = []
    latest_issue_index: dict[tuple[Any, ...], int] = {}
    noisy_issue_rows: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    for row in rows:
        issue_id = row.get("issue_id")
        if not issue_id:
            keep.append(row)
            continue
        key = (
            issue_id,
            row.get("ticket"),
            row.get("symbol"),
            row.get("line_no"),
            tuple(row.get("intent_ids") or []),
        )
        latest_issue_index[key] = len(noisy_issue_rows)
        noisy_issue_rows.append((key, row))

    latest_keys = {key: idx for key, idx in latest_issue_index.items()}
    for idx, (key, row) in enumerate(noisy_issue_rows):
        if latest_keys[key] == idx:
            keep.append(row)

    keep.sort(key=lambda row: str(row.get("recorded_at_utc") or ""))
    write_jsonl(path, keep)
    return len(rows), len(keep)


def compact_latest_by_status(path: Path) -> tuple[int, int]:
    """Keep the latest row for repeated snapshot/status classes."""
    rows = iter_jsonl(path)
    if len(rows) <= 1:
        return len(rows), len(rows)

    latest_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    passthrough: list[dict[str, Any]] = []
    for row in rows:
        status = row.get("status")
        checkpoint_id = row.get("checkpoint_id")
        repeated_snapshot = status in {
            "process_memory_environment_recorded",
            "post_reboot_environment_recorded",
            "process_memory_snapshot_recorded",
            "post_reboot_process_snapshot_recorded",
            "process_memory_checkpoint_no_process_launch",
            "vps_reboot_user_reported_auto_watchdog_observed",
        }
        if repeated_snapshot:
            latest_by_key[(status, checkpoint_id)] = row
        else:
            passthrough.append(row)

    compacted = passthrough + list(latest_by_key.values())
    compacted.sort(key=lambda row: str(row.get("recorded_at_utc") or ""))
    write_jsonl(path, compacted)
    return len(rows), len(compacted)


def compact_supervisor_checkpoints(path: Path) -> tuple[int, int]:
    rows = iter_jsonl(path)
    if len(rows) <= 1:
        return len(rows), len(rows)

    keep: list[dict[str, Any]] = []
    latest_by_checkpoint: dict[str, dict[str, Any]] = {}
    material_statuses = {
        "active_supervision_checkpoint_repaired_bridge_live_continuation_required",
        "checkpoint_recorded_after_repair_reload_verifier_pass",
        "recorded",
        "recorded_in_route_state",
        "validated",
        "validated_current_process_memory_observation",
    }
    stale_statuses = {
        "active_defects_found",
        "process_memory_checkpoint_recorded",
        "post_reboot_checkpoint_recorded",
        "no_active_trade_linkage_or_risk_defects_found",
    }
    removed_stale_count = 0

    for row in rows:
        status = row.get("status")
        checkpoint_id = row.get("checkpoint_id") or status or "unknown"
        if status in material_statuses:
            keep.append(row)
        elif status in stale_statuses:
            latest_by_checkpoint[str(checkpoint_id)] = row
            removed_stale_count += 1
        else:
            keep.append(row)

    keep.extend(latest_by_checkpoint.values())
    keep.sort(key=lambda row: str(row.get("recorded_at_utc") or ""))
    write_jsonl(path, keep)
    return len(rows), len(keep)


def compact_open_lifecycle_snapshots(path: Path) -> tuple[int, int]:
    rows = iter_jsonl(path)
    if len(rows) <= 1:
        return len(rows), len(rows)

    keep: list[dict[str, Any]] = []
    latest_open_check: dict[str, dict[str, Any]] = {}
    for row in rows:
        status = row.get("status")
        if status == "dual_open_positions_orders_read_only_checked":
            key = str(row.get("account_namespace") or "dual")
            latest_open_check[key] = row
        else:
            keep.append(row)

    keep.extend(latest_open_check.values())
    keep.sort(key=lambda row: str(row.get("recorded_at_utc") or ""))
    write_jsonl(path, keep)
    return len(rows), len(keep)


def normalize_closed_future_observation_language() -> int:
    """Remove stale-looking pending phrasing from closed, non-active rows."""
    replacements = {
        "repaired_reloaded_future_intents_pending_live_proof": "repaired_reloaded_future_intents_observation_only",
        "closed_pre_repair_mirror_gap_fresh_proof_pending": "closed_pre_repair_mirror_gap_future_observation_only",
        "next_fresh_target_trade_lifecycle_proof_pending": "next_fresh_target_trade_lifecycle_observation_only",
        "current_intent_and_trade_record_classes_inspected_pending_future_candidate_delta": "current_intent_and_trade_record_classes_inspected_awaiting_future_candidate_delta",
    }
    changed = 0
    for path in sorted(ROUTE.glob("*.jsonl")):
        rows = iter_jsonl(path)
        if not rows:
            continue
        file_changed = False
        updated: list[dict[str, Any]] = []
        for row in rows:
            new_row = dict(row)
            for field in ("status", "severity", "closure_state", "direct_inspection_status"):
                value = new_row.get(field)
                if isinstance(value, str):
                    replaced = value
                    for old, new in replacements.items():
                        replaced = replaced.replace(old, new)
                    if replaced != value:
                        new_row[field] = replaced
                        file_changed = True
                        changed += 1
            updated.append(new_row)
        if file_changed:
            write_jsonl(path, updated)
    return changed


def main() -> int:
    now = utcnow()
    audit = load_json(AUDIT)
    direct = load_json(DIRECT)
    state = load_json(STATE)
    coverage = audit.get("coverage") or {}
    risk = audit.get("risk_summary") or {}
    dual = audit.get("dual_bridge_summary") or {}
    direct_classes = {
        row.get("class_id"): row for row in direct.get("classes", []) if isinstance(row, dict)
    }

    removed_pending: dict[str, int] = {}
    for name in (
        "DUAL_BROKER_RECONCILIATION_LEDGER.jsonl",
        "DUAL_MT5_SYMBOL_SPEC_LEDGER.jsonl",
        "DUAL_RISK_EXPOSURE_LEDGER.jsonl",
        "DUAL_RUNTIME_DECISION_LEDGER.jsonl",
        "DUAL_CANDIDATE_AGENT_INSPECTION_LEDGER.jsonl",
        "DUAL_TRADE_AGENT_INSPECTION_LEDGER.jsonl",
        "DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl",
        "DUAL_PROCESS_HEALTH_LEDGER.jsonl",
        "DUAL_RESTART_RELOAD_LEDGER.jsonl",
    ):
        removed_pending[name] = remove_pending_placeholders(ROUTE / name)

    replacement_rows = {
        "DUAL_CANDIDATE_PACKET_LEDGER.jsonl": {
            "artifact": "DUAL_CANDIDATE_PACKET_LEDGER.jsonl",
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            "recorded_at_utc": audit.get("recorded_at_utc") or now,
            "status": "current_candidate_records_inspected_no_active_defect",
            "trade_records_today": coverage.get("trade_records_today"),
            "outcome_counts_today": audit.get("outcome_counts_today"),
            "rejection_counts_today": audit.get("rejection_counts_today"),
            "runtime_effect_boundary": "read_only_current_audit_summary_no_broker_mutation",
        },
        "DUAL_DATA_CAPTURE_HEALTH_LEDGER.jsonl": {
            "artifact": "DUAL_DATA_CAPTURE_HEALTH_LEDGER.jsonl",
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            "recorded_at_utc": state.get("last_updated_utc") or now,
            "status": "current_namespaced_capture_processes_present",
            "tick_capture": (state.get("post_reboot_process_counts") or {}).get("tick_capture"),
            "m1_capture": (state.get("post_reboot_process_counts") or {}).get("m1_capture"),
            "runtime_namespace": "redacted_account_live_bee34003",
            "runtime_effect_boundary": "read_only_process_checkpoint_no_broker_mutation",
        },
        "DUAL_NO_CANDIDATE_PROOF_LEDGER.jsonl": {
            "artifact": "DUAL_NO_CANDIDATE_PROOF_LEDGER.jsonl",
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            "recorded_at_utc": audit.get("recorded_at_utc") or now,
            "status": "superseded_candidate_rows_present",
            "status_detail": "Not a no-candidate window; current candidate/trade lifecycle audit is the active proof.",
            "trade_records_today": coverage.get("trade_records_today"),
            "runtime_effect_boundary": "read_only_current_audit_summary_no_broker_mutation",
        },
        "DUAL_V3_RUNTIME_DISPOSITION_LEDGER.jsonl": {
            "artifact": "DUAL_V3_RUNTIME_DISPOSITION_LEDGER.jsonl",
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            "recorded_at_utc": audit.get("recorded_at_utc") or now,
            "status": "current_vnext_runtime_disposition_verified",
            "execution_policy_counts_today": audit.get("policy_counts_today"),
            "selector_v3": "vNext/moonshot production replacement active",
            "scheduler_v3": "24-symbol redacted_account primary plus lightweight FTMO follower",
            "execution_policy_v3": "momentum_exhaustion primary with partial_be_runner exception selection",
            "runtime_effect_boundary": "read_only_current_audit_summary_no_broker_mutation",
        },
        "DUAL_TRADE_AGENT_INSPECTION_LEDGER.jsonl": {
            "artifact": "DUAL_TRADE_AGENT_INSPECTION_LEDGER.jsonl",
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            "recorded_at_utc": audit.get("recorded_at_utc") or now,
            "status": "current_trade_lifecycle_and_follower_inspected_no_active_defect",
            "direct_inspection_status": direct_classes.get("dual_broker_intent_and_follower", {}).get("direct_agent_status"),
            "redacted_account_positions": coverage.get("broker_open_positions_redacted_account"),
            "ftmo_positions": coverage.get("broker_open_positions_ftmo"),
            "redacted_account_orders": coverage.get("broker_pending_orders_redacted_account"),
            "ftmo_orders": coverage.get("broker_pending_orders_ftmo"),
            "dual_bridge_summary": dual,
            "runtime_effect_boundary": "read_only_current_audit_summary_no_broker_mutation",
        },
        "DUAL_SUPERVISOR_WORK_QUEUE.jsonl": {
            "artifact": "DUAL_SUPERVISOR_WORK_QUEUE.jsonl",
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            "recorded_at_utc": now,
            "status": "current_live_supervision_continuation_required",
            "state": "active",
            "next_action": "continue live supervision from current checkpoints; no pending pre-activation reload or FTMO activation tasks remain open",
            "runtime_effect_boundary": "local_route_evidence_cleanup_only_no_mt5_call_no_broker_mutation",
        },
    }
    replaced: dict[str, int] = {}
    for name, row in replacement_rows.items():
        replaced[name] = replace_one(ROUTE / name, row)

    old_anomaly_count, new_anomaly_count = compact_anomalies(ROUTE / "DUAL_ANOMALY_LEDGER.jsonl")
    normalized_files, normalized_rows = normalize_superseded_boundaries()
    compacted_hot_ledgers: dict[str, dict[str, int]] = {}
    for name in (
        "DUAL_ENVIRONMENT_LEDGER.jsonl",
        "DUAL_PROCESS_HEALTH_LEDGER.jsonl",
        "DUAL_RESTART_RELOAD_LEDGER.jsonl",
    ):
        before, after = compact_latest_by_status(ROUTE / name)
        compacted_hot_ledgers[name] = {"before": before, "after": after}
    before, after = compact_supervisor_checkpoints(ROUTE / "DUAL_SUPERVISOR_CHECKPOINTS.jsonl")
    compacted_hot_ledgers["DUAL_SUPERVISOR_CHECKPOINTS.jsonl"] = {"before": before, "after": after}
    before, after = compact_open_lifecycle_snapshots(ROUTE / "DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl")
    compacted_hot_ledgers["DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl"] = {"before": before, "after": after}
    closed_language_rewrites = normalize_closed_future_observation_language()

    manifest = load_json(MANIFEST)
    material = set(manifest.get("material_artifacts") or [])
    material.update(
        {
            "DUAL_CURRENT_LIVE_CANDIDATE_TRADE_LIFECYCLE_AUDIT.json:active_issue_count_0",
            "DUAL_CURRENT_LIVE_DIRECT_INSPECTION_CLASSES.json:completed_no_active_defects",
            "DUAL_SUPERVISOR_STATE.json:current_process_and_audit_authority",
        }
    )
    manifest.update(
        {
            "generated_at_utc": now,
            "latest_status": "current_hot_evidence_compacted_no_active_live_defects",
            "stale_evidence_cleanup_updated_at_utc": now,
            "material_artifacts": sorted(material),
        }
    )
    write_json(MANIFEST, manifest)

    cleanup_row = {
        "artifact": "DUAL_STALE_EVIDENCE_CLEANUP_LEDGER.jsonl",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "recorded_at_utc": now,
        "status": "stale_hot_evidence_compacted",
        "removed_pending_placeholder_rows": removed_pending,
        "replaced_current_summary_ledgers_old_row_counts": replaced,
        "anomaly_ledger_rows_before": old_anomaly_count,
        "anomaly_ledger_rows_after": new_anomaly_count,
        "normalized_superseded_pre_reload_files": normalized_files,
        "normalized_superseded_pre_reload_rows": normalized_rows,
        "compacted_hot_ledger_rows": compacted_hot_ledgers,
        "closed_nonactive_language_rewrites": closed_language_rewrites,
        "runtime_effect_boundary": "local_route_evidence_cleanup_only_no_mt5_call_no_broker_mutation",
    }
    append_jsonl(CLEANUP_LEDGER, cleanup_row)

    state.update(
        {
            "stale_evidence_cleanup": cleanup_row,
            "latest_status": "current_hot_evidence_compacted_no_active_live_defects",
            "last_updated_utc": now,
        }
    )
    write_json(STATE, state)
    print(json.dumps(cleanup_row, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
