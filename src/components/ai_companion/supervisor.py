"""Always-on AI companion supervisor.

The supervisor reads runtime evidence and emits deterministic companion state:
cycle digest, proposals, heartbeat, and bounded control_state.json. The live
runtime applies only controls accepted by control_state.AICompanionRuntimeGate.
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from src.components.ultimate_book.runtime_learning_packet import validate_runtime_learning_packet

from .control_state import (
    AI_COMPANION_CONTROL_SCHEMA,
    DEFAULT_CONTROL_STATE_PATH,
    DEFAULT_DECISION_LOG_PATH,
    RUNTIME_EFFECT_BOUNDARY,
    build_empty_control_state,
    config_value,
    iso_utc,
    load_control_state,
    parse_utc,
    utc_now,
    write_control_state_atomic,
)


DEFAULT_DIGEST_PATH = "pipeline_state/ai_companion/cycle_digest.json"
DEFAULT_PROPOSAL_LOG_PATH = "pipeline_state/ai_companion/proposals.jsonl"
DEFAULT_HEARTBEAT_PATH = "pipeline_state/ai_companion/heartbeat.json"
DEFAULT_PACKET_LOG_PATH = "shadow_logs/ultimate_book_runtime_learning_packets.jsonl"
DEFAULT_LAUNCHER_LOG_PATH = "shadow_logs/ultimate_book_launcher.jsonl"
DEFAULT_EXECUTION_MANAGER_LOG_PATH = "shadow_logs/execution_manager_v4_decisions.jsonl"
DEFAULT_BOOK_HEARTBEAT_ROOT = "pipeline_state/ultimate_book"
DEFAULT_BOOK_HEARTBEAT_STALE_SECONDS = 180.0
DEFAULT_CLEAR_RESOLVED_CONTROL_REASONS = {
    "ai_companion_book_link_unhealthy",
    "ai_companion_runtime_integrity_issue",
}
DEFAULT_JSONL_TAIL_MAX_BYTES = 16 * 1024 * 1024


def _is_launcher_execution_manager_block(reason: str) -> bool:
    return (
        reason.startswith("exec_mgr_v4:")
        or ";exec_mgr_v4:" in reason
    )


def _is_launcher_pretrade_cost_block(reason: str) -> bool:
    return reason.startswith("pretrade_cost:")


def _read_jsonl_tail(path: Path, max_rows: int = 500) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not path.exists():
        return [], []
    try:
        max_rows = max(1, int(max_rows))
        size = path.stat().st_size
        chunks: list[bytes] = []
        newline_count = 0
        read_bytes = 0
        chunk_size = 1024 * 1024
        with path.open("rb") as handle:
            position = size
            while position > 0 and newline_count <= max_rows and read_bytes < DEFAULT_JSONL_TAIL_MAX_BYTES:
                take = min(chunk_size, position, DEFAULT_JSONL_TAIL_MAX_BYTES - read_bytes)
                position -= take
                handle.seek(position)
                chunk = handle.read(take)
                chunks.append(chunk)
                read_bytes += len(chunk)
                newline_count += chunk.count(b"\n")
        if not chunks:
            return [], []
        text = b"".join(reversed(chunks)).decode("utf-8-sig", errors="ignore")
        lines = text.splitlines()
    except Exception as exc:
        return [], [{"line": None, "error": repr(exc)}]
    tail = lines[-max_rows:]
    # The EOF tail intentionally avoids a full-file scan, so physical line numbers
    # are local to the bounded tail window rather than whole-file absolute values.
    base_line = 0
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for offset, line in enumerate(tail, start=1):
        text = line.strip()
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            # A concurrently written final line can be transient. Ignore only the latest physical line.
            if base_line + offset == len(lines):
                continue
            errors.append({"line": base_line + offset, "error": str(exc)})
            continue
        if isinstance(parsed, dict):
            parsed["_line_no"] = base_line + offset
            rows.append(parsed)
        else:
            errors.append({"line": base_line + offset, "error": "non_object_json"})
    return rows, errors


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def _proposal_signature(row: Mapping[str, Any]) -> str:
    control = row.get("control") if isinstance(row.get("control"), Mapping) else {}
    event = row.get("event") if isinstance(row.get("event"), Mapping) else {}
    status = row.get("status")
    control_lifecycle_epoch = None
    if status == "accepted":
        control_lifecycle_epoch = control.get("generated_at_utc") or row.get("ts")
    elif status == "cleared_after_condition_resolved":
        control_lifecycle_epoch = control.get("cleared_at_utc") or row.get("ts")
    material = {
        "proposal_type": row.get("proposal_type"),
        "status": status,
        "reason": row.get("reason"),
        "control_id": control.get("control_id"),
        "control_type": control.get("type"),
        "control_lifecycle_epoch": control_lifecycle_epoch,
        "namespace": control.get("namespace") or row.get("namespace") or event.get("namespace"),
        "symbol": control.get("symbol") or row.get("symbol") or event.get("symbol"),
        "sleeve": control.get("sleeve") or row.get("sleeve") or event.get("sleeve"),
        "decision_bar_iso": event.get("decision_bar_iso"),
        "event_ts": event.get("generated_at_utc") or event.get("ts"),
        "event_candidate_id": event.get("candidate_id"),
        "event_cost_refusal_reasons": event.get("cost_refusal_reasons"),
        "event_fatal_reasons": event.get("fatal_reasons"),
    }
    return json.dumps(material, sort_keys=True, default=str, separators=(",", ":"))


def _write_json_atomic(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(row, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(path))


def _row_event_dt(row: Mapping[str, Any]) -> datetime | None:
    return parse_utc(
        row.get("created_at_utc")
        or row.get("generated_at_utc")
        or row.get("ts")
        or row.get("observed_at_utc")
    )


def _fresh_rows(rows: Iterable[Mapping[str, Any]], now: datetime, window_minutes: int) -> list[Mapping[str, Any]]:
    cutoff = now - timedelta(minutes=max(1, int(window_minutes)))
    out: list[tuple[datetime, int, Mapping[str, Any]]] = []
    for row in rows:
        dt = _row_event_dt(row)
        if dt is not None and dt >= cutoff:
            out.append((dt, _int_or_none(row.get("_line_no")) or 0, row))
    out.sort(key=lambda item: (item[0], item[1]))
    return [row for _dt, _line, row in out]


def _row_value(row: Mapping[str, Any], key: str) -> Any:
    if key in row:
        return row.get(key)
    outcome = row.get("outcome") if isinstance(row.get("outcome"), Mapping) else {}
    return outcome.get(key)


def _int_or_none(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _is_targetless_time_stop_management(row: Mapping[str, Any]) -> bool:
    if row.get("event_type") not in {
        "position_adopted",
        "position_managed",
        "position_closed",
        "position_management_error",
        "breach_flatten",
    }:
        return False
    policy = str(_row_value(row, "gtos_vnext_dynamic_policy_selected") or "").strip().lower()
    if policy != "time_stop":
        return False
    no_tp = _row_value(row, "gtos_vnext_dynamic_no_broker_take_profit") is True
    broker_tp_mode = str(_row_value(row, "gtos_vnext_dynamic_broker_take_profit_mode") or "").strip().lower()
    return bool(no_tp or broker_tp_mode == "none")


def _policy_clock_anomalies(
    rows: Iterable[Mapping[str, Any]],
    *,
    grace_minutes: int,
) -> list[dict[str, Any]]:
    grace_bars = max(0, int(grace_minutes or 0) // 15)
    anomalies: list[dict[str, Any]] = []
    bad_statuses = {
        "missing_time_stop_bars",
        "missing_entry_time",
        "invalid_entry_time",
        "elapsed_unavailable",
        "exception",
        "close_failed",
        "hydrate_returned_false",
    }
    for row in rows:
        if not _is_targetless_time_stop_management(row):
            continue
        status = str(_row_value(row, "policy_clock_status") or "").strip().lower()
        rehydration_status = str(_row_value(row, "rehydration_status") or "").strip().lower()
        reason = None
        if not status:
            reason = "missing_policy_clock_status"
        elif status in bad_statuses:
            reason = f"policy_clock_{status}"
        elif rehydration_status in {"hydrate_returned_false", "exception"}:
            reason = f"rehydration_{rehydration_status}"
        overdue_bars = _int_or_none(_row_value(row, "policy_clock_overdue_bars"))
        if reason is None and overdue_bars is not None and overdue_bars > grace_bars:
            reason = "targetless_time_stop_overdue"
        if reason is None:
            continue
        anomalies.append({
            "line": row.get("_line_no"),
            "created_at_utc": row.get("created_at_utc"),
            "namespace": row.get("namespace"),
            "event_type": row.get("event_type"),
            "symbol": row.get("symbol"),
            "sleeve": row.get("sleeve"),
            "candidate_id": row.get("candidate_id"),
            "ticket_hash_sha256": row.get("ticket_hash_sha256"),
            "management_action": row.get("management_action"),
            "policy_clock_status": status or None,
            "policy_clock_checked_at_utc": _row_value(row, "policy_clock_checked_at_utc"),
            "policy_clock_entry_time_utc": _row_value(row, "policy_clock_entry_time_utc"),
            "policy_clock_time_stop_bars": _row_value(row, "policy_clock_time_stop_bars"),
            "policy_clock_elapsed_m15_bars": _row_value(row, "policy_clock_elapsed_m15_bars"),
            "policy_clock_bars_until_due": _row_value(row, "policy_clock_bars_until_due"),
            "policy_clock_overdue_bars": overdue_bars,
            "policy_clock_source": _row_value(row, "policy_clock_source"),
            "rehydration_status": rehydration_status or None,
            "reason": reason,
        })
    return anomalies


def _control_id(*parts: Any) -> str:
    return ":".join(str(part).replace(" ", "_") for part in parts if part not in (None, ""))


def _config_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "n", "off", "disabled"}:
        return False
    return bool(default)


def _config_string_set(value: Any, default: set[str]) -> set[str]:
    if value in (None, ""):
        return set(default)
    if isinstance(value, str):
        return {part.strip() for part in value.split(",") if part.strip()}
    if isinstance(value, Iterable):
        return {str(part).strip() for part in value if str(part).strip()}
    return set(default)


class AICompanionSupervisor:
    def __init__(self, config: Mapping[str, Any] | None, *, repo_root: str | Path = "."):
        self.config = config or {}
        self.repo_root = Path(repo_root)
        self.enabled = _config_bool(config_value(config, "enabled", False), False)
        self.authority_level = str(config_value(config, "authority_level", "observe") or "observe")
        self.control_state_path = str(config_value(config, "control_state_path", DEFAULT_CONTROL_STATE_PATH))
        self.decision_log_path = str(config_value(config, "decision_log_path", DEFAULT_DECISION_LOG_PATH))
        self.digest_path = str(config_value(
            config,
            "digest_path",
            config_value(config, "cycle_digest_path", DEFAULT_DIGEST_PATH),
        ))
        self.proposal_log_path = str(config_value(config, "proposal_log_path", DEFAULT_PROPOSAL_LOG_PATH))
        self.heartbeat_path = str(config_value(config, "heartbeat_path", DEFAULT_HEARTBEAT_PATH))
        self.packet_log_path = str(config_value(config, "packet_log_path", DEFAULT_PACKET_LOG_PATH))
        self.launcher_log_path = str(config_value(config, "launcher_log_path", DEFAULT_LAUNCHER_LOG_PATH))
        self.execution_manager_log_path = str(config_value(
            config,
            "execution_manager_log_path",
            DEFAULT_EXECUTION_MANAGER_LOG_PATH,
        ))
        self.book_heartbeat_root = str(config_value(config, "book_heartbeat_root", DEFAULT_BOOK_HEARTBEAT_ROOT))
        self.book_heartbeat_stale_seconds = float(config_value(
            config,
            "book_heartbeat_stale_seconds",
            DEFAULT_BOOK_HEARTBEAT_STALE_SECONDS,
        ) or DEFAULT_BOOK_HEARTBEAT_STALE_SECONDS)
        self.namespaces = list(config_value(
            config,
            "namespaces",
            ["operator_profile", "redacted_account_live_bee34003"],
        ) or [])
        self.window_minutes = int(config_value(config, "window_minutes", 20) or 20)
        self.control_ttl_minutes = int(config_value(config, "control_ttl_minutes", 30) or 30)
        self.integrity_pause_minutes = int(config_value(config, "integrity_pause_minutes", 30) or 30)
        self.link_pause_minutes = int(config_value(config, "link_pause_minutes", 15) or 15)
        self.loop_seconds = float(config_value(config, "loop_seconds", 60.0) or 60.0)
        self.persist_controls_until_expiry = _config_bool(
            config_value(config, "persist_controls_until_expiry", True),
            True,
        )
        self.clear_resolved_control_reasons = _config_string_set(
            config_value(config, "clear_resolved_control_reasons", None),
            DEFAULT_CLEAR_RESOLVED_CONTROL_REASONS,
        )
        self.targetless_time_stop_overdue_grace_minutes = int(config_value(
            config,
            "targetless_time_stop_overdue_grace_minutes",
            30,
        ) or 30)
        self.targetless_time_stop_pause_new_entries_enabled = _config_bool(
            config_value(config, "targetless_time_stop_pause_new_entries_enabled", True),
            True,
        )

    def _carried_forward_controls(
        self,
        now: datetime,
        new_control_ids: set[str],
        digest: Mapping[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not self.persist_controls_until_expiry:
            return [], []
        previous = load_control_state(self.repo_root, self.control_state_path)
        if not isinstance(previous, Mapping):
            return [], []
        controls = previous.get("controls")
        if not isinstance(controls, list):
            return [], []
        carried: list[dict[str, Any]] = []
        cleared: list[dict[str, Any]] = []
        for control in controls:
            if not isinstance(control, Mapping):
                continue
            control_id = str(control.get("control_id") or "")
            if not control_id or control_id in new_control_ids:
                continue
            expires = parse_utc(control.get("expires_at_utc"))
            if expires is None or expires <= now:
                continue
            reason = str(control.get("reason") or "")
            if reason in self.clear_resolved_control_reasons:
                cleared_control = dict(control)
                cleared_control["control_lifecycle_status"] = "cleared_after_condition_resolved"
                cleared_control["latest_digest_condition_active"] = False
                cleared_control["cleared_at_utc"] = iso_utc(now)
                cleared_control["cleared_reason"] = "resolved_non_sticky_condition"
                cleared_control["clear_evidence"] = self._clear_evidence_for_control(control, digest)
                cleared.append(cleared_control)
                continue
            carried_control = dict(control)
            carried_control["control_lifecycle_status"] = "carried_forward_until_expiry"
            carried_control["latest_digest_condition_active"] = False
            carried_control["carried_forward_at_utc"] = iso_utc(now)
            carried_control["carried_forward_reason"] = "previously_accepted_control_unexpired"
            carried.append(carried_control)
        return carried, cleared

    def _clear_evidence_for_control(
        self,
        control: Mapping[str, Any],
        digest: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        reason = str(control.get("reason") or "")
        issue_counts = digest.get("issue_counts") if isinstance(digest.get("issue_counts"), Mapping) else {}
        generated_at = digest.get("generated_at_utc")
        base: dict[str, Any] = {
            "path": self.digest_path,
            "digest_generated_at_utc": generated_at,
            "digest_ok": bool(digest.get("ok")),
        }
        if reason == "ai_companion_runtime_integrity_issue":
            codes = [
                "launcher_parse_errors",
                "launcher_error_rows",
                "packet_parse_errors",
                "packet_validation_issues",
                "launcher_runtime_learning_write_errors",
            ]
            base["issue_counts"] = {code: issue_counts.get(code, 0) for code in codes}
            base["clear_condition"] = "runtime_integrity_issue_counts_zero"
            return [base]
        if reason == "ai_companion_book_link_unhealthy":
            namespace = str(control.get("namespace") or "")
            heartbeats = digest.get("book_heartbeats") if isinstance(digest.get("book_heartbeats"), Mapping) else {}
            heartbeat = heartbeats.get(namespace) if namespace else None
            if isinstance(heartbeat, Mapping):
                base["heartbeat"] = dict(heartbeat)
            base["clear_condition"] = "book_link_healthy_or_no_link_issue"
            return [base]
        base["clear_condition"] = "resolved_non_sticky_condition"
        return [base]

    def _previous_active_control_ids(self, now: datetime) -> set[str]:
        previous = load_control_state(self.repo_root, self.control_state_path)
        if not isinstance(previous, Mapping):
            return set()
        controls = previous.get("controls")
        if not isinstance(controls, list):
            return set()
        out: set[str] = set()
        for control in controls:
            if not isinstance(control, Mapping):
                continue
            control_id = str(control.get("control_id") or "")
            if not control_id:
                continue
            expires = parse_utc(control.get("expires_at_utc"))
            if expires is not None and expires <= now:
                continue
            out.add(control_id)
        return out

    def _book_heartbeats(self, now: datetime) -> dict[str, Any]:
        root = self.repo_root / self.book_heartbeat_root
        by_namespace: dict[str, Any] = {}
        for namespace in self.namespaces:
            path = root / namespace / "heartbeat.json"
            rec: dict[str, Any] = {"path": str(path.relative_to(self.repo_root)), "present": path.exists()}
            if path.exists():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8-sig"))
                    if isinstance(loaded, dict):
                        rec.update(loaded)
                except Exception as exc:
                    rec["parse_error"] = repr(exc)
            dt = parse_utc(rec.get("ts"))
            rec["age_seconds"] = None if dt is None else round((now - dt).total_seconds(), 3)
            by_namespace[namespace] = rec
        return by_namespace

    def _heartbeat_link_issue_reason(self, heartbeat: Mapping[str, Any]) -> str | None:
        if heartbeat.get("present") is False:
            return "missing_heartbeat"
        if heartbeat.get("parse_error"):
            return "heartbeat_parse_error"
        if heartbeat.get("healthy") is False:
            return "heartbeat_unhealthy"
        age_seconds = heartbeat.get("age_seconds")
        try:
            age = float(age_seconds)
        except (TypeError, ValueError):
            return "missing_heartbeat_timestamp"
        if age > self.book_heartbeat_stale_seconds:
            return "stale_heartbeat"
        return None

    def build_digest(self, now: datetime | None = None) -> dict[str, Any]:
        ts = now or utc_now()
        launcher_rows, launcher_errors = _read_jsonl_tail(self.repo_root / self.launcher_log_path, max_rows=800)
        packet_rows, packet_errors = _read_jsonl_tail(self.repo_root / self.packet_log_path, max_rows=1200)
        execution_rows, execution_errors = _read_jsonl_tail(
            self.repo_root / self.execution_manager_log_path,
            max_rows=800,
        )
        recent_launcher = _fresh_rows(launcher_rows, ts, self.window_minutes)
        recent_packets = _fresh_rows(packet_rows, ts, self.window_minutes)
        recent_execution = _fresh_rows(execution_rows, ts, self.window_minutes)
        packet_validation_issues: list[dict[str, Any]] = []
        for row in recent_packets:
            validation_row = dict(row)
            validation_row.pop("_line_no", None)
            ok, issues = validate_runtime_learning_packet(validation_row)
            if not ok:
                packet_validation_issues.append(
                    {"line": row.get("_line_no"), "namespace": row.get("namespace"), "issues": issues[:6]}
                )
        action_counts = Counter(str(row.get("action") or "missing") for row in recent_launcher)
        launcher_error_rows = [row for row in recent_launcher if row.get("action") == "error"]
        skipped_reason_counts: Counter[str] = Counter()
        placed_counts: Counter[str] = Counter()
        governor_reasons: Counter[str] = Counter()
        profile_missing: Counter[str] = Counter()
        cost_screens: list[dict[str, Any]] = []
        pretrade_cost_blocks: list[dict[str, Any]] = []
        execution_manager_blocks: list[dict[str, Any]] = []
        duplicate_skips: list[dict[str, Any]] = []
        runtime_learning_write_errors: list[dict[str, Any]] = []
        for row in recent_launcher:
            namespace = str(row.get("namespace") or "missing")
            runtime_learning = row.get("runtime_learning") if isinstance(row.get("runtime_learning"), Mapping) else {}
            write_error = runtime_learning.get("error")
            write_error_count = _int_or_none(runtime_learning.get("packet_write_error_count")) or 0
            if write_error or write_error_count > 0:
                placed_examples = []
                for placed in row.get("placed") or []:
                    if not isinstance(placed, Mapping):
                        continue
                    placed_examples.append({
                        "symbol": placed.get("symbol"),
                        "sleeve": placed.get("sleeve"),
                        "decision_bar_iso": placed.get("decision_bar_iso"),
                        "candidate_id": placed.get("candidate_id"),
                        "ticket_hash_sha256": placed.get("ticket_hash_sha256"),
                        "placement_source_completeness_status": placed.get(
                            "placement_source_completeness_status"
                        ),
                        "placement_source_missing_fields": placed.get("placement_source_missing_fields"),
                    })
                runtime_learning_write_errors.append({
                    "ts": row.get("ts"),
                    "namespace": namespace,
                    "action": row.get("action"),
                    "runtime_learning_error": write_error,
                    "packet_write_error_count": write_error_count,
                    "packet_write_errors": runtime_learning.get("packet_write_errors") or [],
                    "placed_count": len(row.get("placed") or []),
                    "placed_examples": placed_examples[:5],
                })
            for placed in row.get("placed") or []:
                if isinstance(placed, dict):
                    placed_counts[f"{namespace}:{placed.get('symbol')}:{placed.get('sleeve')}"] += 1
            bridge = row.get("bridge") if isinstance(row.get("bridge"), dict) else {}
            gov = bridge.get("governor") if isinstance(bridge.get("governor"), dict) else {}
            if gov.get("reason"):
                governor_reasons[str(gov.get("reason"))] += 1
            for item in row.get("skipped") or []:
                if not isinstance(item, dict):
                    continue
                reason = str(item.get("reason") or "missing")
                skipped_reason_counts[reason] += 1
                if reason == "profile_missing_instrument_config":
                    profile_missing[str(item.get("symbol") or "missing")] += 1
                elif reason.startswith("cost_screen_"):
                    cost_screens.append({
                        "ts": row.get("ts"),
                        "namespace": namespace,
                        "symbol": item.get("symbol"),
                        "sleeve": item.get("sleeve"),
                        "decision_bar_iso": item.get("decision_bar_iso"),
                        "reason": reason,
                    })
                elif _is_launcher_execution_manager_block(reason):
                    execution_manager_blocks.append({
                        "ts": row.get("ts"),
                        "namespace": namespace,
                        "symbol": item.get("symbol"),
                        "sleeve": item.get("sleeve"),
                        "decision_bar_iso": item.get("decision_bar_iso"),
                        "reason": reason,
                    })
                elif _is_launcher_pretrade_cost_block(reason):
                    pretrade_cost_blocks.append({
                        "ts": row.get("ts"),
                        "namespace": namespace,
                        "symbol": item.get("symbol"),
                        "sleeve": item.get("sleeve"),
                        "decision_bar_iso": item.get("decision_bar_iso"),
                        "reason": reason,
                    })
                elif reason == "already_placed_today":
                    duplicate_skips.append({
                        "ts": row.get("ts"),
                        "namespace": namespace,
                        "symbol": item.get("symbol"),
                        "sleeve": item.get("sleeve"),
                        "decision_bar_iso": item.get("decision_bar_iso"),
                        "reason": reason,
                    })
        packet_event_counts = Counter(str(row.get("event_type") or "missing") for row in recent_packets)
        packet_joinability_counts = Counter(str(row.get("joinability_status") or "missing") for row in recent_packets)
        policy_clock_anomalies = _policy_clock_anomalies(
            recent_packets,
            grace_minutes=self.targetless_time_stop_overdue_grace_minutes,
        )
        execution_action_counts = Counter(str(row.get("action") or "missing") for row in recent_execution)
        execution_fatal_counts: Counter[str] = Counter()
        execution_cost_refusal_counts: Counter[str] = Counter()
        execution_blocked_events: list[dict[str, Any]] = []
        for row in recent_execution:
            fatal_reasons = [str(item) for item in (row.get("fatal_reasons") or []) if item]
            for reason in fatal_reasons:
                execution_fatal_counts[reason] += 1
            if row.get("action") != "block" and row.get("should_block") is not True:
                continue
            identity = row.get("identity") if isinstance(row.get("identity"), Mapping) else {}
            cost_context = row.get("cost_context") if isinstance(row.get("cost_context"), Mapping) else {}
            lifecycle = (
                row.get("broker_order_lifecycle_capture_v4")
                if isinstance(row.get("broker_order_lifecycle_capture_v4"), Mapping)
                else {}
            )
            pretrade_raw = lifecycle.get("pretrade_cost_model")
            pretrade = pretrade_raw if isinstance(pretrade_raw, Mapping) else {}
            cost_refusals = [str(item) for item in (pretrade.get("refusal_reasons") or []) if item]
            for reason in cost_refusals:
                execution_cost_refusal_counts[reason] += 1
            execution_blocked_events.append({
                "generated_at_utc": row.get("generated_at_utc"),
                "symbol": identity.get("symbol"),
                "broker_symbol": identity.get("broker_symbol"),
                "candidate_id": identity.get("candidate_id"),
                "action": row.get("action"),
                "fatal_reasons": fatal_reasons,
                "cost_status": cost_context.get("pretrade_cost_model_status"),
                "cost_context_status": cost_context.get("status"),
                "spread_r": cost_context.get("spread_r"),
                "max_spread_r": cost_context.get("max_spread_r"),
                "commission_model_status": cost_context.get("commission_model_status"),
                "cost_refusal_reasons": cost_refusals,
            })
        heartbeat_by_namespace = self._book_heartbeats(ts)
        heartbeat_link_issues: dict[str, Any] = {}
        for ns, hb in heartbeat_by_namespace.items():
            if not isinstance(hb, Mapping):
                continue
            reason = self._heartbeat_link_issue_reason(hb)
            if reason:
                enriched = dict(hb)
                enriched["link_issue_reason"] = reason
                heartbeat_link_issues[ns] = enriched
        stale_heartbeats = {
            ns: hb for ns, hb in heartbeat_by_namespace.items()
            if hb.get("age_seconds") is not None
            and float(hb.get("age_seconds") or 0.0) > self.book_heartbeat_stale_seconds
        }
        missing_heartbeats = {
            ns: hb for ns, hb in heartbeat_by_namespace.items()
            if hb.get("present") is False
        }
        digest = {
            "schema": "gtos.ai_companion.runtime_digest.v1",
            "generated_at_utc": iso_utc(ts),
            "enabled": self.enabled,
            "authority_level": self.authority_level,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "window_minutes": self.window_minutes,
            "source_paths": {
                "launcher_log": self.launcher_log_path,
                "packet_log": self.packet_log_path,
                "execution_manager_log": self.execution_manager_log_path,
                "book_heartbeat_root": self.book_heartbeat_root,
            },
            "launcher": {
                "window_row_count": len(recent_launcher),
                "parse_error_count": len(launcher_errors),
                "action_counts": dict(sorted(action_counts.items())),
                "error_rows": launcher_error_rows[-10:],
                "placed_counts": dict(sorted(placed_counts.items())),
                "skipped_reason_counts": dict(sorted(skipped_reason_counts.items())),
                "cost_screen_events": cost_screens[-20:],
                "pretrade_cost_block_events": pretrade_cost_blocks[-20:],
                "execution_manager_block_events": execution_manager_blocks[-20:],
                "duplicate_protection_events": duplicate_skips[-20:],
                "runtime_learning_write_error_count": len(runtime_learning_write_errors),
                "runtime_learning_write_errors": runtime_learning_write_errors[-20:],
                "profile_missing_symbol_counts": dict(sorted(profile_missing.items())),
                "governor_reason_counts": dict(sorted(governor_reasons.items())),
            },
            "runtime_packets": {
                "window_row_count": len(recent_packets),
                "parse_error_count": len(packet_errors),
                "validation_issue_count": len(packet_validation_issues),
                "validation_issues": packet_validation_issues[-20:],
                "event_counts": dict(sorted(packet_event_counts.items())),
                "joinability_counts": dict(sorted(packet_joinability_counts.items())),
                "targetless_time_stop_policy_clock_anomaly_count": len(policy_clock_anomalies),
                "targetless_time_stop_policy_clock_anomalies": policy_clock_anomalies[-20:],
            },
            "execution_manager": {
                "window_row_count": len(recent_execution),
                "parse_error_count": len(execution_errors),
                "action_counts": dict(sorted(execution_action_counts.items())),
                "fatal_reason_counts": dict(sorted(execution_fatal_counts.items())),
                "cost_refusal_reason_counts": dict(sorted(execution_cost_refusal_counts.items())),
                "blocked_events": execution_blocked_events[-20:],
            },
            "book_heartbeats": heartbeat_by_namespace,
            "book_link_issues": heartbeat_link_issues,
            "issue_counts": {
                "launcher_parse_errors": len(launcher_errors),
                "launcher_error_rows": len(launcher_error_rows),
                "packet_parse_errors": len(packet_errors),
                "packet_validation_issues": len(packet_validation_issues),
                "launcher_runtime_learning_write_errors": len(runtime_learning_write_errors),
                "targetless_time_stop_policy_clock_anomalies": len(policy_clock_anomalies),
                "link_unhealthy_namespaces": len(heartbeat_link_issues),
                "missing_book_heartbeats": len(missing_heartbeats),
                "stale_book_heartbeats": len(stale_heartbeats),
            },
        }
        digest["ok"] = all(int(v or 0) == 0 for v in digest["issue_counts"].values())
        return digest

    def build_controls(self, digest: Mapping[str, Any], now: datetime | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        ts = now or utc_now()
        proposals: list[dict[str, Any]] = []
        controls: list[dict[str, Any]] = []
        previous_active_control_ids = self._previous_active_control_ids(ts)

        def _add_control_proposal(control: dict[str, Any]) -> None:
            control_id = str(control.get("control_id") or "")
            if control_id in previous_active_control_ids:
                return
            proposals.append({"proposal_type": "control", "status": "accepted", "control": control})

        expires_integrity = iso_utc(ts + timedelta(minutes=self.integrity_pause_minutes))
        expires_link = iso_utc(ts + timedelta(minutes=self.link_pause_minutes))
        issue_counts = digest.get("issue_counts") if isinstance(digest.get("issue_counts"), Mapping) else {}
        integrity_issue_codes = [
            "launcher_parse_errors",
            "launcher_error_rows",
            "packet_parse_errors",
            "packet_validation_issues",
            "launcher_runtime_learning_write_errors",
        ]
        if any(int(issue_counts.get(code) or 0) > 0 for code in integrity_issue_codes):
            control = {
                "type": "pause_new_entries",
                "control_id": _control_id("pause", "runtime_integrity"),
                "namespace": "*",
                "reason": "ai_companion_runtime_integrity_issue",
                "generated_at_utc": iso_utc(ts),
                "expires_at_utc": expires_integrity,
                "evidence": [
                    {
                        "path": self.digest_path,
                        "issue_counts": {code: issue_counts.get(code) for code in integrity_issue_codes},
                    }
                ],
            }
            controls.append(control)
            _add_control_proposal(control)
        runtime_packets = (
            digest.get("runtime_packets")
            if isinstance(digest.get("runtime_packets"), Mapping)
            else {}
        )
        policy_clock_anomalies = [
            event for event in (runtime_packets.get("targetless_time_stop_policy_clock_anomalies") or [])
            if isinstance(event, Mapping)
        ]
        for event in policy_clock_anomalies:
            proposals.append({
                "proposal_type": "advisory",
                "status": "observed",
                "reason": "targetless_time_stop_policy_clock_issue",
                "event": dict(event),
            })
        if (
            self.targetless_time_stop_pause_new_entries_enabled
            and int(issue_counts.get("targetless_time_stop_policy_clock_anomalies") or 0) > 0
        ):
            namespaces = sorted({
                str(event.get("namespace") or "*")
                for event in policy_clock_anomalies
            } or {"*"})
            for namespace in namespaces:
                examples = [
                    dict(event)
                    for event in policy_clock_anomalies
                    if str(event.get("namespace") or "*") == namespace
                ][:5]
                control = {
                    "type": "pause_new_entries",
                    "control_id": _control_id("pause", namespace, "targetless_time_stop_clock"),
                    "namespace": namespace,
                    "reason": "ai_companion_targetless_time_stop_policy_clock_issue",
                    "generated_at_utc": iso_utc(ts),
                    "expires_at_utc": expires_integrity,
                    "evidence": [
                        {
                            "path": self.digest_path,
                            "issue_counts": {
                                "targetless_time_stop_policy_clock_anomalies": issue_counts.get(
                                    "targetless_time_stop_policy_clock_anomalies"
                                ),
                            },
                            "examples": examples,
                        }
                    ],
                }
                controls.append(control)
                _add_control_proposal(control)
        link_issues = digest.get("book_link_issues") if isinstance(digest.get("book_link_issues"), Mapping) else {}
        heartbeats = digest.get("book_heartbeats") if isinstance(digest.get("book_heartbeats"), Mapping) else {}
        if not link_issues:
            link_issues = {
                namespace: hb
                for namespace, hb in heartbeats.items()
                if isinstance(hb, Mapping) and self._heartbeat_link_issue_reason(hb)
            }
        for namespace, hb in link_issues.items():
            if not isinstance(hb, Mapping):
                continue
            control = {
                "type": "pause_new_entries",
                "control_id": _control_id("pause", namespace, "book_link_unhealthy"),
                "namespace": namespace,
                "reason": "ai_companion_book_link_unhealthy",
                "generated_at_utc": iso_utc(ts),
                "expires_at_utc": expires_link,
                "evidence": [{"path": hb.get("path"), "heartbeat": dict(hb)}],
            }
            controls.append(control)
            _add_control_proposal(control)
        launcher = digest.get("launcher") if isinstance(digest.get("launcher"), Mapping) else {}
        for event in launcher.get("cost_screen_events") or []:
            proposals.append({
                "proposal_type": "advisory",
                "status": "observed",
                "reason": "cost_screen_review_only_do_not_override_execution_manager",
                "event": event,
            })
        for event in launcher.get("pretrade_cost_block_events") or []:
            proposals.append({
                "proposal_type": "advisory",
                "status": "observed",
                "reason": "pretrade_cost_block_review_only_runtime_already_fail_closed",
                "event": event,
            })
        for event in launcher.get("execution_manager_block_events") or []:
            proposals.append({
                "proposal_type": "advisory",
                "status": "observed",
                "reason": "execution_manager_block_review_only_runtime_already_fail_closed",
                "event": event,
            })
        execution_manager = (
            digest.get("execution_manager")
            if isinstance(digest.get("execution_manager"), Mapping)
            else {}
        )
        for event in execution_manager.get("blocked_events") or []:
            proposals.append({
                "proposal_type": "advisory",
                "status": "observed",
                "reason": "execution_manager_block_detail_runtime_already_fail_closed",
                "event": event,
            })
        for symbol, count in (launcher.get("profile_missing_symbol_counts") or {}).items():
            proposals.append({
                "proposal_type": "advisory",
                "status": "observed",
                "reason": "broker_profile_hygiene_queue_runtime_already_fail_closed",
                "symbol": symbol,
                "count": count,
            })
        for event in launcher.get("duplicate_protection_events") or []:
            proposals.append({
                "proposal_type": "advisory",
                "status": "observed",
                "reason": "duplicate_protection_confirmed_runtime_already_fail_closed",
                "event": event,
            })
        new_control_ids = {str(control.get("control_id")) for control in controls if control.get("control_id")}
        carried_controls, cleared_controls = self._carried_forward_controls(ts, new_control_ids, digest)
        for carried_control in carried_controls:
            controls.append(carried_control)
            proposals.append({
                "proposal_type": "control",
                "status": "carried_forward_until_expiry",
                "control": carried_control,
            })
        for cleared_control in cleared_controls:
            proposals.append({
                "proposal_type": "control",
                "status": "cleared_after_condition_resolved",
                "control": cleared_control,
            })
        state = build_empty_control_state(
            authority_level=self.authority_level,
            now=ts,
            ttl_minutes=max(1, self.control_ttl_minutes),
            source="ai_companion_supervisor",
        )
        state["controls"] = controls
        state["summary"] = {
            "active_control_count": len(controls),
            "pause_new_entries": any(c.get("type") == "pause_new_entries" for c in controls),
            "symbol_sleeve_cooldown_count": sum(1 for c in controls if c.get("type") == "symbol_sleeve_cooldown"),
            "risk_multiplier_count": sum(1 for c in controls if c.get("type") == "risk_multiplier"),
            "proposal_count": len(proposals),
        }
        state["source_digest_path"] = self.digest_path
        return state, proposals

    def run_once(self, now: datetime | None = None) -> dict[str, Any]:
        ts = now or utc_now()
        _write_json_atomic(self.repo_root / self.heartbeat_path, {
            "schema": "gtos.ai_companion.heartbeat.v1",
            "ts": iso_utc(ts),
            "pid": os.getpid(),
            "enabled": self.enabled,
            "authority_level": self.authority_level,
            "ok": None,
            "cycle_status": "running",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        })
        digest = self.build_digest(ts)
        digest_path = self.repo_root / self.digest_path
        _write_json_atomic(digest_path, digest)
        state, proposals = self.build_controls(digest, ts)
        state_path = write_control_state_atomic(self.repo_root, state, self.control_state_path)
        proposal_path = self.repo_root / self.proposal_log_path
        prior_proposals, _proposal_read_errors = _read_jsonl_tail(proposal_path, max_rows=2000)
        seen_proposal_signatures = {
            str(row.get("proposal_dedupe_key") or _proposal_signature(row))
            for row in prior_proposals
        }
        appended_proposal_count = 0
        suppressed_proposal_count = 0
        decision = {
            "schema": "gtos.ai_companion.supervisor_decision.v1",
            "ts": iso_utc(ts),
            "enabled": self.enabled,
            "authority_level": self.authority_level,
            "ok": bool(digest.get("ok")),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "digest_path": str(digest_path.relative_to(self.repo_root)),
            "control_state_path": str(state_path.relative_to(self.repo_root)),
            "issue_counts": digest.get("issue_counts"),
            "control_count": len(state.get("controls") or []),
            "proposal_count": len(proposals),
            "proposal_append_policy": "dedupe_by_reason_control_identity_and_event_identity",
        }
        _append_jsonl(self.repo_root / self.decision_log_path, decision)
        for proposal in proposals:
            proposal_row = {
                "schema": "gtos.ai_companion.proposal.v1",
                "ts": iso_utc(ts),
                **proposal,
            }
            proposal_signature = _proposal_signature(proposal_row)
            proposal_row["proposal_dedupe_key"] = proposal_signature
            if proposal_signature in seen_proposal_signatures:
                suppressed_proposal_count += 1
                continue
            seen_proposal_signatures.add(proposal_signature)
            _append_jsonl(proposal_path, proposal_row)
            appended_proposal_count += 1
        if appended_proposal_count or suppressed_proposal_count:
            decision["proposal_appended_count"] = appended_proposal_count
            decision["proposal_suppressed_duplicate_count"] = suppressed_proposal_count
            _append_jsonl(self.repo_root / self.decision_log_path, {
                "schema": "gtos.ai_companion.supervisor_proposal_append_summary.v1",
                "ts": iso_utc(ts),
                "proposal_appended_count": appended_proposal_count,
                "proposal_suppressed_duplicate_count": suppressed_proposal_count,
                "proposal_append_policy": decision["proposal_append_policy"],
            })
        heartbeat = {
            "schema": "gtos.ai_companion.heartbeat.v1",
            "ts": iso_utc(ts),
            "pid": os.getpid(),
            "enabled": self.enabled,
            "authority_level": self.authority_level,
            "ok": bool(digest.get("ok")),
            "cycle_status": "completed",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "control_count": len(state.get("controls") or []),
            "digest_path": str(digest_path.relative_to(self.repo_root)),
            "control_state_path": str(state_path.relative_to(self.repo_root)),
        }
        _write_json_atomic(self.repo_root / self.heartbeat_path, heartbeat)
        return decision

    def run_forever(self) -> None:
        while True:
            try:
                self.run_once()
            except Exception as exc:  # noqa: BLE001 - supervisor must keep running.
                err = {
                    "schema": "gtos.ai_companion.supervisor_error.v1",
                    "ts": iso_utc(),
                    "pid": os.getpid(),
                    "error": repr(exc),
                    "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
                }
                _append_jsonl(self.repo_root / self.decision_log_path, err)
            time.sleep(self.loop_seconds)


__all__ = [
    "AICompanionSupervisor",
    "DEFAULT_DIGEST_PATH",
    "DEFAULT_PROPOSAL_LOG_PATH",
    "DEFAULT_HEARTBEAT_PATH",
]
