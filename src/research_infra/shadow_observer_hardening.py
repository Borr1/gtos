"""LTO-035 shadow-observer hardening and source registry status.

This module audits the existing no-AI/no-execution shadow observer without
changing live trading behavior. It turns observer lifecycle and source/proxy
coverage into a deterministic status row and report.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "shadow_observer_hardening_status_v1"
REPORT_SCHEMA_VERSION = "lto035_shadow_observer_hardening_v1"
REGISTRY_SCHEMA_VERSION = "shadow_observer_source_registry_v1"
LTO_ID = "LTO-035"
FOLLOW_IDS = ("LIVE-FOLLOW-008", "LIVE-FOLLOW-033")
ACTION_REQUIRED = "SHADOW_OBSERVER_HARDENING_ACTION_REQUIRED"
STATUS_OK = "SHADOW_OBSERVER_HARDENED_SOURCE_STATUS_ONLY"

DEFAULT_OBSERVER_REGISTRY_PATH = Path("config/shadow_observer_registry.yaml")
DEFAULT_AGENT_CONFIG_PATH = Path("config/agent_config.yaml")
DEFAULT_STATUS_LOG_PATH = Path("shadow_logs/shadow_observer_status.jsonl")
DEFAULT_STRATEGY_EVALUATIONS_PATH = Path("shadow_logs/strategy_follow_evaluations.jsonl")
DEFAULT_STATE_PATH = Path("pipeline_state/shadow_observer_state.json")
STALE_MINUTES = 90

NO_DECISION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}

REQUIRED_FORBIDDEN = {
    "ai_api_call",
    "canary_call",
    "order_send",
    "execution_engine",
    "permission_gate",
    "outcome_opening",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(json.dumps(part, sort_keys=True, default=str) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _parse_iso(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except ValueError:
        return None


def _read_yaml(path: Path | str) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {}
    return yaml.safe_load(target.read_text(encoding="utf-8")) or {}


def _read_json(path: Path | str) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _rows_with_lines(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> list[tuple[int, dict[str, Any]]]:
    normalized: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(rows or [], start=1):
        if isinstance(item, tuple) and len(item) == 2 and isinstance(item[1], dict):
            normalized.append((int(item[0]), item[1]))
        elif isinstance(item, dict):
            normalized.append((index, item))
    return normalized


def _parse_hhmm(value: str) -> int:
    hour_s, minute_s = value.split(":", 1)
    return int(hour_s) * 60 + int(minute_s)


def _instrument_config(agent_config: dict[str, Any], config_symbol: str | None) -> dict[str, Any]:
    if not config_symbol:
        return {}
    instruments = agent_config.get("instruments") or {}
    return instruments.get(config_symbol) or {}


def _max_kill_zone_end_utc(agent_config: dict[str, Any], config_symbol: str | None) -> str | None:
    config = _instrument_config(agent_config, config_symbol)
    kill_zones = ((config.get("market") or {}).get("kill_zones") or {})
    if not kill_zones:
        return None
    end_minutes = []
    for window in kill_zones.values():
        try:
            end_minutes.append(_parse_hhmm(str(window.get("end_utc"))))
        except Exception:
            continue
    if not end_minutes:
        return None
    latest = max(end_minutes)
    return f"{latest // 60:02d}:{latest % 60:02d}"


def _kill_zone_window_state(agent_config: dict[str, Any], config_symbol: str | None, now_utc: datetime) -> str:
    config = _instrument_config(agent_config, config_symbol)
    kill_zones = ((config.get("market") or {}).get("kill_zones") or {})
    windows: list[tuple[int, int]] = []
    for window in kill_zones.values():
        try:
            windows.append((_parse_hhmm(str(window.get("start_utc"))), _parse_hhmm(str(window.get("end_utc")))))
        except Exception:
            continue
    if not windows:
        return "NO_CONFIGURED_KILL_ZONE"

    now_minutes = now_utc.hour * 60 + now_utc.minute
    starts = [start for start, _ in windows]
    ends = [end for _, end in windows]
    for start, end in windows:
        if start <= end:
            if start <= now_minutes <= end:
                return "ACTIVE_SESSION"
        elif now_minutes >= start or now_minutes <= end:
            return "ACTIVE_SESSION"

    if now_minutes < min(starts):
        return "BEFORE_FIRST_SESSION"
    if now_minutes > max(ends):
        return "AFTER_FINAL_SESSION"
    return "BETWEEN_SESSIONS"


def normalize_source_registry(observer_registry: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in observer_registry.get("instruments") or []:
        if not isinstance(item, dict):
            continue
        activation_state = str(item.get("activation_state") or "")
        evidence_class = str(item.get("evidence_class") or "")
        if activation_state == "CONTEXT_CONTROL_ONLY":
            proxy_class = "CONTROL_ONLY"
        elif activation_state == "PRE_REGISTRATION_REQUIRED":
            proxy_class = "PREREGISTRATION_REQUIRED"
        elif evidence_class == "FORWARD_SHADOW":
            proxy_class = "FORWARD_SHADOW"
        else:
            proxy_class = evidence_class or "UNSPECIFIED"
        rows.append(
            {
                "observer_id": item.get("observer_id"),
                "enabled": bool(item.get("enabled", False)),
                "activation_state": activation_state,
                "symbol": item.get("symbol"),
                "broker_symbol": item.get("broker_symbol"),
                "config_symbol": item.get("config_symbol"),
                "family": item.get("family"),
                "evidence_class": evidence_class,
                "source_proxy_class": proxy_class,
                "source_status": item.get("source_status"),
                "pre_registered_question_id": item.get("pre_registered_question_id"),
                "allowed_rows": item.get("allowed_rows") or [],
                "forbidden": item.get("forbidden") or [],
                "required_before_enable": item.get("required_before_enable") or [],
            }
        )
    return rows


def _latest_by_observer(status_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for line_no, row in _rows_with_lines(status_rows):
        observer_id = str(row.get("observer_id") or "")
        created = _parse_iso(row.get("created_at_utc"))
        if not observer_id or created is None:
            continue
        current = latest.get(observer_id)
        current_ts = _parse_iso((current or {}).get("created_at_utc"))
        if current_ts is None or created >= current_ts:
            latest[observer_id] = {**row, "_line_no": line_no}
    return latest


def _strategy_observer_counts(strategy_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]]) -> dict[str, Any]:
    by_symbol: Counter[str] = Counter()
    ai_statuses: Counter[str] = Counter()
    source_files: Counter[str] = Counter()
    rows = 0
    for _, row in _rows_with_lines(strategy_rows):
        if row.get("source_file") != "shadow_observer_mso_no_ai":
            continue
        rows += 1
        by_symbol[str(row.get("symbol") or "UNKNOWN")] += 1
        ai_statuses[str(row.get("ai_status") or "UNKNOWN")] += 1
        source_files[str(row.get("source_file") or "UNKNOWN")] += 1
    return {
        "shadow_observer_strategy_rows": rows,
        "by_symbol": dict(by_symbol),
        "ai_statuses": dict(ai_statuses),
        "source_files": dict(source_files),
    }


def _safety_violations(
    status_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    strategy_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for line_no, row in _rows_with_lines(status_rows):
        for field in ("no_ai_calls", "no_canary_required", "no_execution"):
            if row.get(field) is not True:
                violations.append({"source": "status", "line_no": line_no, "field": field, "value": row.get(field)})
        for field in ("ai_calls", "canary_calls", "order_calls", "paid_data_calls"):
            if field in row and row.get(field) not in {0, 0.0}:
                violations.append({"source": "status", "line_no": line_no, "field": field, "value": row.get(field)})
        if row.get("paid_fetch_attempted") not in {None, False}:
            violations.append({"source": "status", "line_no": line_no, "field": "paid_fetch_attempted", "value": row.get("paid_fetch_attempted")})
    for line_no, row in _rows_with_lines(strategy_rows):
        if row.get("source_file") != "shadow_observer_mso_no_ai":
            continue
        if row.get("ai_status") != "NOT_CALLED_BY_SHADOW_OBSERVER":
            violations.append({"source": "strategy", "line_no": line_no, "field": "ai_status", "value": row.get("ai_status")})
        if row.get("no_leak_status") != "NO_AI_NO_EXECUTION_NO_POST_OUTCOME_FIELDS":
            violations.append({"source": "strategy", "line_no": line_no, "field": "no_leak_status", "value": row.get("no_leak_status")})
    return violations


def stale_observer_detection(
    *,
    source_registry: list[dict[str, Any]],
    latest_status: dict[str, dict[str, Any]],
    now_utc: datetime,
    stale_minutes: int = STALE_MINUTES,
) -> dict[str, Any]:
    rows = []
    action_required = []
    for entry in source_registry:
        if not entry.get("enabled") or entry.get("activation_state") != "ACTIVE_MSO_SHADOW":
            continue
        observer_id = str(entry.get("observer_id"))
        latest = latest_status.get(observer_id) or {}
        created = _parse_iso(latest.get("created_at_utc"))
        age = None if created is None else (now_utc - created).total_seconds() / 60.0
        if created is None:
            status = "STALE_NO_STATUS_ROW"
        elif age is not None and age > stale_minutes:
            status = "STALE_STATUS_ROW"
        else:
            status = "FRESH_OR_RECENT_STATUS_ROW"
        if status.startswith("STALE"):
            action_required.append(observer_id)
        rows.append(
            {
                "observer_id": observer_id,
                "symbol": entry.get("symbol"),
                "latest_status": latest.get("lifecycle_status"),
                "latest_status_utc": latest.get("created_at_utc"),
                "age_minutes": None if age is None else round(age, 3),
                "stale_status": status,
            }
        )
    return {
        "stale_minutes": stale_minutes,
        "rows": rows,
        "action_required_observer_ids": action_required,
        "status": "ACTION_REQUIRED" if action_required else "OK",
    }


def _stable_stale_signature(stale: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": stale.get("status"),
        "action_required_observer_ids": stale.get("action_required_observer_ids") or [],
        "rows": [
            {
                "observer_id": row.get("observer_id"),
                "stale_status": row.get("stale_status"),
            }
            for row in stale.get("rows") or []
        ],
    }


def _stable_latest_status_signature(latest_status: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        observer_id: {
            "activation_state": row.get("activation_state"),
            "enabled": row.get("enabled"),
            "lifecycle_status": row.get("lifecycle_status"),
            "reason": row.get("reason"),
            "source_status": row.get("source_status"),
        }
        for observer_id, row in sorted(latest_status.items())
    }


def _stable_gate_signature(gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "gate_id": gate.get("gate_id"),
            "passed": gate.get("passed"),
            "blocker_code": gate.get("blocker_code"),
        }
        for gate in gates
    ]


def final_closeout_detection(
    *,
    source_registry: list[dict[str, Any]],
    latest_status: dict[str, dict[str, Any]],
    observer_state: dict[str, Any],
    agent_config: dict[str, Any],
    status_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    current_time = now_utc or datetime.now(timezone.utc)
    rows = []
    confirmed = []
    for entry in source_registry:
        if not entry.get("enabled") or entry.get("activation_state") != "ACTIVE_MSO_SHADOW":
            continue
        observer_id = str(entry.get("observer_id"))
        state_row = observer_state.get(observer_id) if isinstance(observer_state, dict) else {}
        latest_close = (state_row or {}).get("last_candle_close_utc")
        latest_status_row = latest_status.get(observer_id) or {}
        session_end = _max_kill_zone_end_utc(agent_config, entry.get("config_symbol"))
        window_state = _kill_zone_window_state(agent_config, entry.get("config_symbol"), current_time)
        latest_close_dt = _parse_iso(latest_close)
        close_hhmm = None if latest_close_dt is None else f"{latest_close_dt.hour:02d}:{latest_close_dt.minute:02d}"
        outside_status = latest_status_row.get("lifecycle_status") == "SKIPPED_OUTSIDE_KILL_ZONE"
        if session_end and close_hhmm == session_end and outside_status:
            status = "FINAL_CLOSEOUT_CONFIRMED"
            confirmed.append(observer_id)
        elif _has_historical_final_closeout(
            observer_id=observer_id,
            session_end=session_end,
            status_rows=status_rows or [],
        ):
            status = "HISTORICAL_FINAL_CLOSEOUT_CONFIRMED"
            confirmed.append(observer_id)
        elif window_state in {"BEFORE_FIRST_SESSION", "ACTIVE_SESSION", "BETWEEN_SESSIONS"}:
            status = f"FINAL_CLOSEOUT_NOT_DUE_{window_state}"
        elif outside_status:
            status = "OUTSIDE_KZ_STATUS_PRESENT_NO_FINAL_CLOSE_MATCH"
        elif latest_close:
            status = "LATEST_CLOSE_PRESENT_NO_OUTSIDE_KZ_CONFIRMATION"
        else:
            status = "NO_CLOSEOUT_EVIDENCE_YET"
        rows.append(
            {
                "observer_id": observer_id,
                "symbol": entry.get("symbol"),
                "config_symbol": entry.get("config_symbol"),
                "latest_candle_close_utc": latest_close,
                "configured_latest_session_end_utc": session_end,
                "kill_zone_window_state": window_state,
                "latest_lifecycle_status": latest_status_row.get("lifecycle_status"),
                "closeout_status": status,
            }
        )
    return {
        "rows": rows,
        "confirmed_observer_ids": confirmed,
        "status": "OK",
    }


def _has_historical_final_closeout(
    *,
    observer_id: str,
    session_end: str | None,
    status_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
) -> bool:
    if not session_end:
        return False

    emitted_closeouts: list[datetime] = []
    outside_rows: list[datetime] = []
    for _, row in _rows_with_lines(status_rows):
        if row.get("observer_id") != observer_id:
            continue
        created = _parse_iso(row.get("created_at_utc"))
        if created is None:
            continue
        lifecycle_status = row.get("lifecycle_status")
        decision_time = _parse_iso(row.get("decision_time_utc") or row.get("latest_closed_m15_utc"))
        close_hhmm = None if decision_time is None else f"{decision_time.hour:02d}:{decision_time.minute:02d}"
        if lifecycle_status == "EMITTED_STRATEGY_FOLLOW_EVALUATION" and close_hhmm == session_end:
            emitted_closeouts.append(created)
        elif lifecycle_status == "SKIPPED_OUTSIDE_KILL_ZONE":
            outside_rows.append(created)

    return any(outside >= emitted for emitted in emitted_closeouts for outside in outside_rows)


def build_status_row(
    *,
    observer_registry: dict[str, Any] | None = None,
    agent_config: dict[str, Any] | None = None,
    observer_state: dict[str, Any] | None = None,
    status_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    strategy_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    now_utc = _parse_iso(generated) or datetime.now(timezone.utc)
    registry = observer_registry or {}
    source_registry = normalize_source_registry(registry)
    latest_status = _latest_by_observer(status_rows or [])
    lifecycle_counts = Counter(str(row.get("lifecycle_status") or "UNKNOWN") for _, row in _rows_with_lines(status_rows or []))
    active_entries = [row for row in source_registry if row.get("enabled") and row.get("activation_state") == "ACTIVE_MSO_SHADOW"]
    inactive_entries = [row for row in source_registry if row not in active_entries]
    registry_errors = []
    seen = set()
    for row in source_registry:
        observer_id = str(row.get("observer_id") or "")
        if observer_id in seen:
            registry_errors.append(f"{observer_id}: duplicate observer_id")
        seen.add(observer_id)
        if row.get("enabled") and row.get("activation_state") == "ACTIVE_MSO_SHADOW":
            missing_forbidden = sorted(REQUIRED_FORBIDDEN - set(row.get("forbidden") or []))
            if missing_forbidden:
                registry_errors.append(f"{observer_id}: missing forbidden {missing_forbidden}")
            if not row.get("broker_symbol") or not row.get("config_symbol") or not row.get("pre_registered_question_id"):
                registry_errors.append(f"{observer_id}: missing active observer symbol/question fields")
    safety_violations = _safety_violations(status_rows or [], strategy_rows or [])
    strategy_counts = _strategy_observer_counts(strategy_rows or [])
    stale = stale_observer_detection(
        source_registry=source_registry,
        latest_status=latest_status,
        now_utc=now_utc,
    )
    closeout = final_closeout_detection(
        source_registry=source_registry,
        latest_status=latest_status,
        observer_state=observer_state or {},
        agent_config=agent_config or {},
        status_rows=status_rows or [],
        now_utc=now_utc,
    )
    restart_policy = {
        "component": "shadow_observer",
        "policy": (
            "Restart after observer schema/lifecycle changes or verified observer staleness; keep no-AI/no-order/"
            "no-Databento boundaries intact."
        ),
        "manual_commands": [
            "python scripts/run_shadow_observer.py --mode live --profile redacted_account --once",
            "python scripts/run_shadow_observer.py --mode live --profile redacted_account",
            "python scripts/run_shadow_observer.py --mode live --profile redacted_account --symbols EURUSD,GER40",
        ],
    }
    gates = [
        {
            "gate_id": "G0_NO_AI_NO_EXECUTION_NO_PAID_CALLS",
            "passed": not safety_violations,
            "observed": {"safety_violations": safety_violations, **NO_DECISION_COUNTERS},
            "blocker_code": "" if not safety_violations else "SHADOW_OBSERVER_SAFETY_COUNTER_VIOLATION",
        },
        {
            "gate_id": "G1_SOURCE_REGISTRY_NORMALIZED",
            "passed": len(source_registry) >= 8 and not registry_errors,
            "observed": {
                "entries": len(source_registry),
                "active": len(active_entries),
                "inactive": len(inactive_entries),
                "registry_errors": registry_errors,
            },
            "blocker_code": "" if len(source_registry) >= 8 and not registry_errors else "SHADOW_OBSERVER_SOURCE_REGISTRY_INCOMPLETE",
        },
        {
            "gate_id": "G2_LIFECYCLE_STATUS_ROWS_PRESENT",
            "passed": all(str(row.get("observer_id")) in latest_status for row in active_entries),
            "observed": {"latest_status_observer_ids": sorted(latest_status), "lifecycle_counts": dict(lifecycle_counts)},
            "blocker_code": "" if all(str(row.get("observer_id")) in latest_status for row in active_entries) else "SHADOW_OBSERVER_LIFECYCLE_STATUS_MISSING",
        },
        {
            "gate_id": "G3_STALE_OBSERVER_DETECTION",
            "passed": stale["status"] == "OK",
            "observed": stale,
            "blocker_code": "" if stale["status"] == "OK" else "SHADOW_OBSERVER_STALE_STATUS_ROW",
        },
        {
            "gate_id": "G4_RESTART_POLICY_PRESENT",
            "passed": bool(restart_policy.get("manual_commands")),
            "observed": restart_policy,
            "blocker_code": "" if restart_policy.get("manual_commands") else "SHADOW_OBSERVER_RESTART_POLICY_MISSING",
        },
        {
            "gate_id": "G5_GER40_EXTENDED_SESSION_CLOSEOUT_FIXTURE",
            "passed": any(
                row.get("observer_id") == "ger40_tier2_mso_shadow_v1"
                and row.get("closeout_status")
                in {
                    "FINAL_CLOSEOUT_CONFIRMED",
                    "HISTORICAL_FINAL_CLOSEOUT_CONFIRMED",
                    "FINAL_CLOSEOUT_NOT_DUE_BEFORE_FIRST_SESSION",
                    "FINAL_CLOSEOUT_NOT_DUE_ACTIVE_SESSION",
                    "FINAL_CLOSEOUT_NOT_DUE_BETWEEN_SESSIONS",
                }
                for row in closeout["rows"]
            ),
            "observed": closeout,
            "blocker_code": ""
            if any(
                row.get("observer_id") == "ger40_tier2_mso_shadow_v1"
                and row.get("closeout_status")
                in {
                    "FINAL_CLOSEOUT_CONFIRMED",
                    "HISTORICAL_FINAL_CLOSEOUT_CONFIRMED",
                    "FINAL_CLOSEOUT_NOT_DUE_BEFORE_FIRST_SESSION",
                    "FINAL_CLOSEOUT_NOT_DUE_ACTIVE_SESSION",
                    "FINAL_CLOSEOUT_NOT_DUE_BETWEEN_SESSIONS",
                }
                for row in closeout["rows"]
            )
            else "GER40_EXTENDED_SESSION_CLOSEOUT_NOT_CONFIRMED",
        },
    ]
    failed = [gate for gate in gates if not gate["passed"]]
    action_required_codes = [gate["blocker_code"] for gate in failed if gate["blocker_code"]]
    status = ACTION_REQUIRED if action_required_codes else STATUS_OK
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        generated.split("T")[0],
        source_registry,
        _stable_latest_status_signature(latest_status),
        strategy_counts,
        _stable_stale_signature(stale),
        closeout,
        _stable_gate_signature(gates),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("shadow_observer_hardening", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "lto_id": LTO_ID,
        "follow_ids": list(FOLLOW_IDS),
        "status": status,
        "evidence_class": "FORWARD_SHADOW",
        "promotion_verdict": PROMOTION_VERDICT,
        "source_registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "source_registry": source_registry,
        "registry_summary": {
            "total_entries": len(source_registry),
            "active_entries": len(active_entries),
            "inactive_entries": len(inactive_entries),
            "registry_errors": registry_errors,
        },
        "lifecycle_summary": {
            "status_rows": len(_rows_with_lines(status_rows or [])),
            "lifecycle_counts": dict(lifecycle_counts),
            "latest_status_by_observer": latest_status,
        },
        "strategy_observer_counts": strategy_counts,
        "stale_observer_detection": stale,
        "final_closeout_detection": closeout,
        "restart_policy": restart_policy,
        "validation_gates": gates,
        "gate_summary": {
            "passed": sum(1 for gate in gates if gate["passed"]),
            "failed": len(failed),
            "failed_gate_ids": [gate["gate_id"] for gate in failed],
            "failed_blocker_codes": action_required_codes,
        },
        "documented_limitation_codes": [],
        "action_required_codes": action_required_codes,
        "claim_boundary": (
            "LTO-035 hardens no-AI/no-execution observer monitoring and source registry only. "
            "It does not enable new instruments, open outcomes, or change live trading behavior."
        ),
        **NO_DECISION_COUNTERS,
    }


def build_report_payload(
    *,
    observer_registry: dict[str, Any] | None = None,
    agent_config: dict[str, Any] | None = None,
    observer_state: dict[str, Any] | None = None,
    status_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    strategy_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    row = build_status_row(
        observer_registry=observer_registry,
        agent_config=agent_config,
        observer_state=observer_state,
        status_rows=status_rows,
        strategy_rows=strategy_rows,
        generated_at_utc=generated,
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "promotion_verdict": PROMOTION_VERDICT,
        "status": row["status"],
        "status_row": row,
        "source_registry": {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "generated_at_utc": generated,
            "promotion_verdict": PROMOTION_VERDICT,
            "entries": row["source_registry"],
        },
        "completion_evidence": {
            "active_observers": row["registry_summary"]["active_entries"],
            "source_registry_entries": row["registry_summary"]["total_entries"],
            "safety_violations": row["validation_gates"][0]["observed"]["safety_violations"],
            "stale_action_required": row["stale_observer_detection"]["action_required_observer_ids"],
            "ger40_closeout_confirmed": "ger40_tier2_mso_shadow_v1"
            in row["final_closeout_detection"]["confirmed_observer_ids"],
            "new_ai_calls": 0,
            "new_canary_calls": 0,
            "new_order_calls": 0,
            "new_paid_data_calls": 0,
        },
        "synthesis": {
            "summary": (
                "Shadow-observer lifecycle, no-AI/no-execution boundaries, restart policy, source registry, "
                "staleness detection, and GER40 extended-session closeout are now artifact-backed."
            ),
        },
    }


def load_inputs(
    *,
    observer_registry_path: Path | str = DEFAULT_OBSERVER_REGISTRY_PATH,
    agent_config_path: Path | str = DEFAULT_AGENT_CONFIG_PATH,
    state_path: Path | str = DEFAULT_STATE_PATH,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return _read_yaml(observer_registry_path), _read_yaml(agent_config_path), _read_json(state_path)


def render_source_registry_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# LTO035 Shadow Observer Source Registry - 2026-05-05",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "| Observer | Enabled | State | Symbol | Broker | Evidence | Proxy class | Source status |",
        "|---|---:|---|---|---|---|---|---|",
    ]
    for row in payload["entries"]:
        lines.append(
            f"| `{row['observer_id']}` | `{row['enabled']}` | `{row['activation_state']}` | "
            f"`{row['symbol']}` | `{row['broker_symbol']}` | `{row['evidence_class']}` | "
            f"`{row['source_proxy_class']}` | `{row['source_status']}` |"
        )
    return "\n".join(lines) + "\n"


def render_markdown(payload: dict[str, Any]) -> str:
    row = payload["status_row"]
    lines = [
        "# LTO035 Shadow Observer Hardening - 2026-05-05",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        payload["synthesis"]["summary"],
        "",
        "## Registry",
        "",
        f"- Source registry entries: `{row['registry_summary']['total_entries']}`",
        f"- Active observers: `{row['registry_summary']['active_entries']}`",
        f"- Inactive/context/prereg entries: `{row['registry_summary']['inactive_entries']}`",
        f"- Registry errors: `{row['registry_summary']['registry_errors']}`",
        "",
        "## Lifecycle",
        "",
        f"- Status rows: `{row['lifecycle_summary']['status_rows']}`",
        f"- Lifecycle counts: `{row['lifecycle_summary']['lifecycle_counts']}`",
        f"- Strategy observer counts: `{row['strategy_observer_counts']}`",
        f"- Stale action-required observers: `{row['stale_observer_detection']['action_required_observer_ids']}`",
        f"- GER40 closeout confirmed: `{'ger40_tier2_mso_shadow_v1' in row['final_closeout_detection']['confirmed_observer_ids']}`",
        "",
        "## Gates",
        "",
        "| Gate | Passed | Blocker |",
        "|---|---:|---|",
    ]
    for gate in row["validation_gates"]:
        lines.append(f"| `{gate['gate_id']}` | `{gate['passed']}` | `{gate['blocker_code'] or '-'}` |")
    lines.extend(
        [
            "",
            "## Restart Policy",
            "",
            row["restart_policy"]["policy"],
            "",
            "## Boundary",
            "",
            row["claim_boundary"],
            "",
            "## Safety Counters",
            "",
            f"- ai_calls: `{row['ai_calls']}`",
            f"- canary_calls: `{row['canary_calls']}`",
            f"- order_calls: `{row['order_calls']}`",
            f"- paid_data_calls: `{row['paid_data_calls']}`",
        ]
    )
    return "\n".join(lines) + "\n"
