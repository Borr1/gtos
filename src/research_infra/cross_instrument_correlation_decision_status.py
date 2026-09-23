"""Status helper for cross-instrument correlation decision capture."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any


SCHEMA_VERSION = "cross_instrument_correlation_decision_status_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def _stable_hash(*parts: Any) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _risk_config(config: dict[str, Any]) -> dict[str, Any]:
    return (config.get("risk") or {}) if isinstance(config, dict) else {}


def _logger_config(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        return {}
    return ((config.get("shadow_loggers") or {}).get("cross_instrument_correlation_decisions_logger") or {})


def _timestamp_values(rows: list[dict[str, Any]]) -> list[str]:
    values = [normalized(row.get("timestamp_utc")) for row in rows]
    return [value for value in values if value]


def summarize_cross_instrument_correlation_decisions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize decision rows without changing gate behavior."""
    timestamps = _timestamp_values(rows)
    action_counts = Counter(normalized(row.get("gate_action")) or "UNKNOWN" for row in rows)
    context_counts = Counter(normalized(row.get("evaluation_context")) or "UNKNOWN" for row in rows)
    symbol_counts = Counter(normalized(row.get("candidate_symbol")) or "UNKNOWN" for row in rows)
    return {
        "decision_rows": len(rows),
        "gate_action_counts": dict(sorted(action_counts.items())),
        "evaluation_context_counts": dict(sorted(context_counts.items())),
        "candidate_symbol_counts": dict(sorted(symbol_counts.items())),
        "none_action_rows": int(action_counts.get("NONE") or 0),
        "risk_reduce_half_rows": int(action_counts.get("RISK_REDUCE_HALF") or 0),
        "reject_rows": int(action_counts.get("REJECT") or 0),
        "first_decision_timestamp_utc": min(timestamps) if timestamps else "",
        "latest_decision_timestamp_utc": max(timestamps) if timestamps else "",
    }


def build_cross_instrument_correlation_decision_status(
    *,
    config: dict[str, Any],
    decision_rows: list[dict[str, Any]],
    decision_log_path: str,
    decision_log_exists: bool,
    runtime_halt_active: bool,
    generated_at_utc: str,
) -> dict[str, Any]:
    """Build one idempotent status row for the correlation decision logger."""
    risk_cfg = _risk_config(config)
    logger_cfg = _logger_config(config)
    gate_enabled = bool(risk_cfg.get("cross_instrument_correlation_enabled", False))
    logger_enabled = bool(logger_cfg.get("enabled", False))
    summary = summarize_cross_instrument_correlation_decisions(decision_rows)

    action_required_codes: list[str] = []
    documented_limitation_codes: list[str] = []
    if gate_enabled and not logger_enabled:
        status = "ACTION_REQUIRED_CROSS_INSTRUMENT_CORRELATION_DECISION_LOGGER_DISABLED"
        action_required_codes.append("CROSS_INSTRUMENT_CORRELATION_DECISION_LOGGER_DISABLED")
    elif not gate_enabled:
        status = "DISABLED_CROSS_INSTRUMENT_CORRELATION_GATE_CONFIG"
        documented_limitation_codes.append("CROSS_INSTRUMENT_CORRELATION_GATE_DISABLED_BY_CONFIG")
    elif summary["decision_rows"] > 0:
        status = "OK_CROSS_INSTRUMENT_CORRELATION_DECISION_ROWS_PRESENT"
    elif runtime_halt_active:
        status = "OK_NO_CROSS_INSTRUMENT_CORRELATION_ROWS_RUNTIME_HALTED"
        documented_limitation_codes.append("NO_DECISION_ROWS_EXPECTED_WHILE_RESEARCH_RUNTIME_HALTED")
    else:
        status = "OK_NO_CROSS_INSTRUMENT_CORRELATION_ROWS_YET"
        documented_limitation_codes.append("NO_DECISION_ROWS_OBSERVED_YET")

    source_dependency_signature = _stable_hash(
        gate_enabled,
        logger_enabled,
        runtime_halt_active,
        decision_log_exists,
        summary,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "promotion_verdict": PROMOTION_VERDICT,
        "generated_at_utc": generated_at_utc,
        "status": status,
        "decision_log_path": decision_log_path,
        "decision_log_exists": decision_log_exists,
        "runtime_halt_active": runtime_halt_active,
        "cross_instrument_correlation_gate_enabled": gate_enabled,
        "cross_instrument_correlation_decisions_logger_enabled": logger_enabled,
        "config_threshold": risk_cfg.get("cross_instrument_correlation_threshold"),
        "config_min_positions": risk_cfg.get("cross_instrument_correlation_min_positions"),
        **summary,
        "action_required_codes": action_required_codes,
        "documented_limitation_codes": documented_limitation_codes,
        "source_dependency_signature": source_dependency_signature,
        "row_key": _stable_hash("cross_instrument_correlation_decision_status", source_dependency_signature),
        "claim_boundary": (
            "Status row documents cross-instrument correlation decision capture only. "
            "It does not change correlation thresholds, sizing, permissions, execution, or orders."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def build_cross_instrument_correlation_decision_report(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "cross_instrument_correlation_decision_status_report_v1",
        "generated_at_utc": row.get("generated_at_utc"),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if row.get("action_required_codes") else "OK_CROSS_CORR_DECISION_STATUS_DOCUMENTED",
        "status_row": row,
        "counts": {
            "decision_rows": row.get("decision_rows"),
            "none_action_rows": row.get("none_action_rows"),
            "risk_reduce_half_rows": row.get("risk_reduce_half_rows"),
            "reject_rows": row.get("reject_rows"),
            "action_required": len(row.get("action_required_codes") or []),
        },
        "claim_boundary": row.get("claim_boundary"),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }
