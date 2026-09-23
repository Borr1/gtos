#!/usr/bin/env python3
"""Lightweight secondary-account execution follower.

Consumes canonical trade intents emitted by the primary vNext live system and
executes them through the target account's own MT5 terminal, profile, risk
rules, symbol aliases, current tick, and broker geometry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.data_ingestion import TF_MAP  # noqa: E402
from src.components.dual_broker_intent_bus import (  # noqa: E402
    INTENT_LOG_ENV_VAR,
    MARKET_ENTRY,
    PENDING_LIMIT,
    _execution_is_filled_entry_source,
    _pending_is_open_entry_source,
    _record_has_terminal_exit,
    intent_to_trade_params,
    read_intents_from_offset,
    resolve_intent_log_path,
    source_target_boundary_violations,
    validate_intent,
)
from src.components.execution import (  # noqa: E402
    ExecutionEngine,
    PENDING_INTENT_DIR,
    TradeState,
)
from src.components.mt5_daemon_runtime import (  # noqa: E402
    acquire_single_instance_lock,
    install_signal_handlers,
    release_single_instance_lock,
    write_daemon_heartbeat,
)
from src.mt5 import create_mt5  # noqa: E402
from src.safety.runtime_halt import (  # noqa: E402
    RuntimeHaltError,
    enforce_runtime_not_halted,
)
from src.utils.broker_profile import (  # noqa: E402
    assert_mt5_account_matches_profile,
    broker_account_namespace,
    namespaced_file_path,
    resolve_mt5_portable_mode,
    resolve_mt5_terminal_path,
)
from src.utils.config import (  # noqa: E402
    apply_instrument_overrides,
    apply_profile_overrides,
    resolve_profile,
)

LOGGER = logging.getLogger(__name__)
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "agent_config.yaml"
DEFAULT_PROFILE = "operator_profile"
DEFAULT_SOURCE_NAMESPACE = "redacted_account_live_bee34003"
DEFAULT_TARGET_NAMESPACE = "operator_profile"
DEFAULT_TERMINAL_PATH = r"C:\MT5\FTMO\terminal64.exe"
TARGET_TICK_MAX_AGE_SECONDS = 600.0
MARKET_INTENT_MAX_TARGET_TICK_WAIT_SECONDS = 120.0
DEFAULT_LIVE_RECOVERY_WINDOW_SECONDS = 1800.0
TARGET_TICK_DEFERRAL_LOG_SECONDS = 30.0
TARGET_RISK_BUDGET_EPSILON = 1e-6
DEFAULT_DAILY_RESET_OFFSET_HOURS = 3.0
TERMINAL_INTENT_EVENTS = {
    "dry_run_intent_ready",
    "market_intent_processed",
    "pending_limit_intent_processed",
    "risk_guard_rejected",
    "skip_source_is_target",
    "skip_unexpected_source_namespace",
    "intent_source_target_boundary_violation",
    "skip_unmapped_symbol",
    "unsupported_intent_type",
    "market_intent_missing_target_execution_context",
    "pending_limit_missing_target_execution_context",
    "market_intent_expired_target_tick_unavailable",
    "market_intent_expired_no_target_order",
    "market_intent_skipped_outside_live_recovery_window",
    "market_intent_target_position_detected_before_retry",
    "market_intent_target_position_detected_after_none",
    "market_intent_reprocess_failed_retry_skipped_source_not_open",
    "market_intent_reprocess_failed_retry_skipped_outside_live_recovery_window",
}
REPROCESSABLE_FAILED_INTENT_EVENTS = {
    "market_intent_missing_target_execution_context",
    "pending_limit_missing_target_execution_context",
    "market_intent_expired_target_tick_unavailable",
    "market_intent_expired_no_target_order",
}
INTENT_OUTCOME_CATEGORY_BY_EVENT = {
    "dry_run_intent_ready": "dry_run_ready",
    "pending_limit_intent_processed": "pending_limit_processed",
    "risk_guard_rejected": "risk_blocked",
    "skip_source_is_target": "skipped_non_applicable",
    "skip_unexpected_source_namespace": "skipped_non_applicable",
    "intent_source_target_boundary_violation": "boundary_rejected",
    "skip_unmapped_symbol": "skipped_non_applicable",
    "unsupported_intent_type": "skipped_non_applicable",
    "market_intent_missing_target_execution_context": "failed_retryable",
    "pending_limit_missing_target_execution_context": "failed_retryable",
    "market_intent_expired_target_tick_unavailable": "failed_retryable",
    "market_intent_expired_no_target_order": "failed_retryable",
    "market_intent_skipped_outside_live_recovery_window": "stale_skipped",
    "market_intent_target_position_detected_before_retry": "target_position_detected",
    "market_intent_target_position_detected_after_none": "target_position_detected",
    "market_intent_reprocess_failed_retry_skipped_source_not_open": "failed_source_terminal",
    "market_intent_reprocess_failed_retry_skipped_outside_live_recovery_window": "stale_skipped",
    "market_intent_deferred_target_tick_unavailable": "deferred_retryable",
    "market_intent_deferred_no_target_order": "deferred_retryable",
    "market_intent_reprocess_failed_retry_started": "retry_started",
}
VNEXT_TARGET_REQUIRED_CONTEXT_KEYS = (
    "gtos_vnext_production_execution_path",
    "gtos_vnext_dynamic_policy_selected",
    "gtos_vnext_execution_policy_id",
    "gtos_vnext_dynamic_policy_applied",
    "gtos_vnext_dynamic_policy_replaced_policy",
    "gtos_vnext_selected_cell_risk_pct",
    "gtos_vnext_selected_cell_risk_cell_id",
    "gtos_vnext_selected_cell_risk_selected_policy",
    "gtos_vnext_selected_cell_risk_policy_identity_status",
    "gtos_vnext_commission_model_status",
)
VNEXT_VERIFIED_COMMISSION_STATUS = (
    "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP"
)
VNEXT_NON_FATAL_CONTEXT_UNRESOLVED_REASONS = {
    "condition_challenger_cell_join_missing_for_broader_origin_allowlist_entry",
}

_STOP = False


def _request_stop() -> None:
    global _STOP
    _STOP = True


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "__dict__"):
        return _jsonable(
            {k: v for k, v in vars(value).items() if not str(k).startswith("_")}
        )
    return str(value)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(row)
    payload.setdefault("recorded_at_utc", _utcnow_iso())
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_jsonable(payload), ensure_ascii=True, sort_keys=True) + "\n")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _source_record_path_from_intent(intent: dict[str, Any]) -> Path | None:
    primary_order = (
        intent.get("primary_order")
        if isinstance(intent.get("primary_order"), dict)
        else {}
    )
    record_path = str(primary_order.get("record_path") or "").strip()
    if not record_path:
        return None
    path = Path(record_path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _source_record_retry_state(intent: dict[str, Any]) -> dict[str, Any]:
    """Return whether stale failed-intent replay is still safe.

    Old failed copies are dangerous unless the primary record still proves an
    unclosed source lifecycle. This deliberately fails closed when the source
    record is missing, terminal, or internally ambiguous.
    """
    path = _source_record_path_from_intent(intent)
    if path is None:
        return {
            "allow_retry": False,
            "status": "source_record_path_missing",
        }
    state: dict[str, Any] = {
        "record_path": str(path),
        "allow_retry": False,
    }
    if not path.exists():
        state["status"] = "source_record_missing"
        return state
    record = _read_json(path)
    if not record:
        state["status"] = "source_record_unreadable_or_empty"
        return state
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    pending = (
        record.get("limit_intent")
        if isinstance(record.get("limit_intent"), dict)
        else record.get("pending_limit")
        if isinstance(record.get("pending_limit"), dict)
        else {}
    )
    terminal_markers = {
        "record_exit_block": _record_has_terminal_exit(record),
        "execution_terminal_exit_type": execution.get("terminal_exit_type"),
        "execution_terminal_exit_time_utc": execution.get("terminal_exit_time_utc"),
        "execution_last_lifecycle_result": execution.get("last_lifecycle_result"),
        "execution_active_lifecycle_capture_status": execution.get(
            "active_lifecycle_capture_status"
        ),
    }
    lifecycle_text = " ".join(
        str(value or "").strip().lower() for value in terminal_markers.values()
    )
    if terminal_markers["record_exit_block"] or "terminal_exit" in lifecycle_text:
        state.update(
            {
                "status": "source_record_terminal",
                "terminal_markers": terminal_markers,
            }
        )
        return state

    execution_current_volume = _safe_float(execution.get("current_volume"))
    if execution_current_volume is not None and execution_current_volume <= 0:
        state.update(
            {
                "status": "source_record_zero_current_volume",
                "current_volume": execution_current_volume,
            }
        )
        return state

    execution_filled = bool(execution) and _execution_is_filled_entry_source(execution)
    pending_open = bool(pending) and _pending_is_open_entry_source(pending)
    if execution_filled or pending_open:
        state.update(
            {
                "allow_retry": True,
                "status": (
                    "source_record_unclosed_filled_entry"
                    if execution_filled
                    else "source_record_unclosed_pending_entry"
                ),
                "ticket": execution.get("ticket") or execution.get("position_ticket"),
                "entry_order_ticket": execution.get("entry_order_ticket"),
                "pending_order_ticket": pending.get("ticket") or pending.get("order_ticket"),
                "current_volume": execution_current_volume,
            }
        )
        return state

    state["status"] = "source_record_liveness_unproven"
    return state


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    data = json.dumps(_jsonable(payload), indent=2, sort_keys=True)
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            tmp.write_text(data, encoding="utf-8")
            os.replace(str(tmp), str(path))
            return
        except PermissionError as exc:
            if attempt >= max_attempts:
                LOGGER.error(
                    "json persistence skipped after transient file-lock retries: "
                    "path=%s tmp=%s error=%s",
                    path,
                    tmp,
                    exc,
                )
                return
            LOGGER.warning(
                "json persistence retry after file-lock: path=%s tmp=%s "
                "attempt=%s/%s error=%s",
                path,
                tmp,
                attempt,
                max_attempts,
                exc,
            )
            time.sleep(0.05 * attempt)
        except OSError as exc:
            LOGGER.error(
                "json persistence skipped after filesystem error: path=%s tmp=%s "
                "error=%s",
                path,
                tmp,
                exc,
            )
            return


def _processed_intent_ids_from_action_log(
    path: Path,
    *,
    reprocess_failed_intents: bool = False,
) -> set[str]:
    processed, _failed = _intent_recovery_state_from_action_log(
        path,
        reprocess_failed_intents=reprocess_failed_intents,
    )
    return processed


def _intent_recovery_state_from_action_log(
    path: Path,
    *,
    reprocess_failed_intents: bool = False,
) -> tuple[set[str], set[str]]:
    processed: set[str] = set()
    reprocessable_failed: set[str] = set()
    if not path.exists():
        return processed, reprocessable_failed
    try:
        fh = path.open(encoding="utf-8")
    except OSError as exc:
        LOGGER.warning("could not read follower action log for processed intents: %s", exc)
        return processed, reprocessable_failed
    with fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            event = str(row.get("event") or "")
            intent_id = str(row.get("intent_id") or "").strip()
            if not intent_id or event not in TERMINAL_INTENT_EVENTS:
                continue
            retryable_failure = event in REPROCESSABLE_FAILED_INTENT_EVENTS or (
                event == "market_intent_processed" and row.get("result") is None
            )
            if reprocess_failed_intents and retryable_failure:
                processed.discard(intent_id)
                reprocessable_failed.add(intent_id)
                continue
            if (
                reprocess_failed_intents
                and event == "market_intent_skipped_outside_live_recovery_window"
                and intent_id in reprocessable_failed
            ):
                processed.discard(intent_id)
                continue
            processed.add(intent_id)
            reprocessable_failed.discard(intent_id)
    return processed, reprocessable_failed


def _intent_outcome_category(row: dict[str, Any]) -> str:
    event = str(row.get("event") or "")
    if event == "market_intent_processed":
        result = row.get("result")
        if isinstance(result, dict) and result.get("ticket") not in (None, "", 0, "0"):
            return "copied"
        return "failed_retryable"
    return INTENT_OUTCOME_CATEGORY_BY_EVENT.get(event, "other")


def _action_log_intent_outcome_summary(path: Path) -> dict[str, Any]:
    latest_by_intent: dict[str, dict[str, Any]] = {}
    event_counts: Counter[str] = Counter()
    malformed_rows = 0
    if not path.exists():
        return {
            "intent_count": 0,
            "outcome_counts": {},
            "event_counts": {},
            "malformed_rows": 0,
            "latest_intents": {},
        }
    try:
        fh = path.open(encoding="utf-8")
    except OSError as exc:
        LOGGER.warning("could not read follower action log for outcome summary: %s", exc)
        return {
            "intent_count": 0,
            "outcome_counts": {},
            "event_counts": {},
            "malformed_rows": 0,
            "read_error": str(exc),
            "latest_intents": {},
        }
    with fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                malformed_rows += 1
                continue
            event = str(row.get("event") or "")
            intent_id = str(row.get("intent_id") or "").strip()
            if not intent_id or not event:
                continue
            event_counts[event] += 1
            latest_by_intent[intent_id] = {
                "intent_id": intent_id,
                "event": event,
                "outcome_category": _intent_outcome_category(row),
                "line_no": line_no,
                "recorded_at_utc": row.get("recorded_at_utc"),
                "reason": row.get("reason"),
            }
    outcome_counts = Counter(
        row["outcome_category"] for row in latest_by_intent.values()
    )
    return {
        "intent_count": len(latest_by_intent),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "event_counts": dict(sorted(event_counts.items())),
        "malformed_rows": malformed_rows,
        "latest_intents": dict(sorted(latest_by_intent.items())),
    }


_TRADE_STATE_FIELDS = {field.name for field in fields(TradeState)}


def _trade_state_payload(trade: TradeState) -> dict[str, Any]:
    return {key: _jsonable(value) for key, value in asdict(trade).items()}


def _trade_state_from_payload(payload: dict[str, Any]) -> TradeState | None:
    if not isinstance(payload, dict):
        return None
    kwargs = {key: payload.get(key) for key in _TRADE_STATE_FIELDS if key in payload}
    required = (
        "ticket",
        "direction",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "take_profit_2",
        "take_profit_3",
        "initial_volume",
        "current_volume",
        "sl_distance",
    )
    if any(kwargs.get(key) in (None, "") for key in required):
        return None
    try:
        return TradeState(**kwargs)
    except TypeError as exc:
        LOGGER.warning("target trade-state payload restore failed: %s", exc)
        return None


def _ticket_key(value: Any) -> str | None:
    numeric = _safe_float(value)
    if numeric is None:
        return None
    ticket = int(numeric)
    return str(ticket) if ticket else None


def _parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _intent_age_seconds(intent: dict[str, Any]) -> float:
    recorded_at = _parse_utc(intent.get("recorded_at_utc"))
    if recorded_at is None:
        return 0.0
    return (datetime.now(timezone.utc) - recorded_at).total_seconds()


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def _nonempty_reasons(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def target_execution_context_errors(params: dict[str, Any]) -> list[str]:
    """Return non-retryable vNext intent-schema errors for the target account."""
    has_vnext_risk_context = bool(
        params.get("gtos_vnext_selected_cell_risk_cell_id")
        or params.get("gtos_vnext_selected_cell_risk_pct") is not None
        or params.get("gtos_vnext_production_execution_path")
    )
    if not has_vnext_risk_context:
        return []

    errors = [
        f"missing:{key}"
        for key in VNEXT_TARGET_REQUIRED_CONTEXT_KEYS
        if not _present(params.get(key))
    ]
    if not _truthy(params.get("gtos_vnext_dynamic_policy_applied")):
        errors.append("gtos_vnext_dynamic_policy_not_applied")
    selected_policy = str(params.get("gtos_vnext_dynamic_policy_selected") or "").strip().lower()
    risk_policy = str(
        params.get("gtos_vnext_selected_cell_risk_selected_policy") or ""
    ).strip().lower()
    if selected_policy and risk_policy and selected_policy != risk_policy:
        errors.append(
            "selected_policy_risk_identity_mismatch:"
            f"selected={selected_policy} risk={risk_policy}"
        )
    unresolved = _nonempty_reasons(
        params.get("gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons")
    )
    if not unresolved:
        unresolved = _nonempty_reasons(
            params.get("gtos_vnext_selected_cell_risk_unresolved_reasons")
        )
    unresolved = [
        reason
        for reason in unresolved
        if reason not in VNEXT_NON_FATAL_CONTEXT_UNRESOLVED_REASONS
    ]
    if unresolved:
        errors.append("selected_cell_unresolved:" + ",".join(sorted(unresolved)))
    if (
        str(params.get("gtos_vnext_commission_model_status") or "")
        != VNEXT_VERIFIED_COMMISSION_STATUS
    ):
        errors.append("selected_cell_commission_status_not_verified")
    return errors


def execution_engine_none_reason(params: dict[str, Any]) -> str:
    pretrade_cost_model = params.get("gtos_vnext_pretrade_cost_model")
    if isinstance(pretrade_cost_model, dict):
        status = str(pretrade_cost_model.get("status") or "").strip().upper()
        refusal_reason = str(pretrade_cost_model.get("refusal_reason") or "").strip()
        if status == "REFUSED":
            if refusal_reason:
                return f"gtos_vnext_pretrade_cost_model_refused:{refusal_reason}"
            return "gtos_vnext_pretrade_cost_model_refused"
    return "execution_engine_returned_none"


def execution_engine_none_context(params: dict[str, Any]) -> dict[str, Any]:
    pretrade_cost_model = params.get("gtos_vnext_pretrade_cost_model")
    if not isinstance(pretrade_cost_model, dict):
        return {}
    return {
        "pretrade_cost_model_status": pretrade_cost_model.get("status"),
        "pretrade_cost_model_refusal_reason": pretrade_cost_model.get("refusal_reason"),
        "pretrade_cost_model": pretrade_cost_model,
    }


def target_execution_failure_context(
    engine: ExecutionEngine,
    *,
    mt5: Any,
    broker_symbol: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    context = execution_engine_none_context(params)
    snapshot: dict[str, Any] = {
        "broker_symbol": broker_symbol,
        "engine_symbol": getattr(engine, "symbol", None),
    }
    for method_name, target_key in (
        ("_symbol_info_snapshot", "symbol_info"),
        ("_tick_snapshot", "tick"),
        ("_positions_snapshot", "positions"),
    ):
        method = getattr(engine, method_name, None)
        if not callable(method):
            continue
        try:
            snapshot[target_key] = method()
        except Exception as exc:  # noqa: BLE001
            snapshot[target_key] = {"available": False, "error": str(exc)}
    last_order = getattr(engine, "_last_order_send_diagnostic", None)
    if last_order is not None:
        snapshot["last_order_send_diagnostic"] = last_order
    last_sltp = getattr(engine, "_last_sltp_modify_diagnostic", None)
    if last_sltp is not None:
        snapshot["last_sltp_modify_diagnostic"] = last_sltp
    raw_mt5 = getattr(mt5, "_mt5", None)
    last_error = getattr(raw_mt5, "last_error", None)
    if callable(last_error):
        try:
            snapshot["mt5_last_error"] = last_error()
        except Exception as exc:  # noqa: BLE001
            snapshot["mt5_last_error"] = f"last_error_failed:{exc}"
    context["target_execution_failure_snapshot"] = snapshot
    return context


def target_tick_quality(mt5: Any, broker_symbol: str) -> tuple[bool, str, Any | None]:
    tick = mt5.get_tick(broker_symbol)
    if tick is None:
        return False, "target_tick_unavailable", None
    bid = _safe_float(getattr(tick, "bid", None))
    ask = _safe_float(getattr(tick, "ask", None))
    if bid is None or ask is None or bid <= 0 or ask <= 0:
        return False, "target_tick_nonpositive_bid_ask", tick
    if ask < bid:
        return False, "target_tick_inverted_bid_ask", tick
    tick_time = getattr(tick, "time", None)
    if isinstance(tick_time, datetime):
        if tick_time.tzinfo is None:
            tick_time = tick_time.replace(tzinfo=timezone.utc)
        age_seconds = abs(
            (datetime.now(timezone.utc) - tick_time.astimezone(timezone.utc)).total_seconds()
        )
        if age_seconds > TARGET_TICK_MAX_AGE_SECONDS:
            return False, f"target_tick_stale:{age_seconds:.1f}s", tick
    return True, "passed", tick


def read_intents_with_offsets(path: str | Path, offset: int = 0) -> tuple[list[tuple[dict[str, Any], int]], int]:
    target = Path(path)
    if not target.exists():
        return [], 0
    size = target.stat().st_size
    if offset < 0 or offset > size:
        offset = 0
    rows: list[tuple[dict[str, Any], int]] = []
    with target.open("rb") as fh:
        fh.seek(offset)
        while True:
            raw_line = fh.readline()
            if not raw_line:
                break
            row_end = fh.tell()
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                LOGGER.warning("dual broker follower skipped malformed intent row")
                continue
            rows.append((row, row_end))
        end_offset = fh.tell()
    return rows, end_offset


def load_target_base_config(config_path: Path, profile: str | None) -> dict[str, Any]:
    with config_path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    resolved_profile = resolve_profile(profile)
    return apply_profile_overrides(raw, resolved_profile)


def load_target_symbol_config(base_config: dict[str, Any], symbol: str) -> dict[str, Any]:
    return apply_instrument_overrides(base_config, symbol)


def target_risk_cap_pct(
    intent: dict[str, Any],
    target_config: dict[str, Any],
) -> float | None:
    risk_cfg = target_config.get("risk") if isinstance(target_config.get("risk"), dict) else {}
    configured = risk_cfg.get("risk_per_trade_pct", target_config.get("risk_per_trade_pct"))
    cap = intent.get("risk") if isinstance(intent.get("risk"), dict) else {}
    source_cap = cap.get("effective_risk_pct_cap")
    try:
        source_numeric = float(source_cap)
    except (TypeError, ValueError):
        return None
    if source_numeric <= 0:
        return None

    try:
        configured_numeric = float(configured)
    except (TypeError, ValueError):
        configured_numeric = None
    if configured_numeric is not None and configured_numeric > 0:
        return min(configured_numeric, source_numeric)
    return source_numeric


def intent_source_namespace(intent: dict[str, Any]) -> str:
    source = intent.get("source") if isinstance(intent.get("source"), dict) else {}
    return str(source.get("runtime_namespace") or "").strip().lower()


def intent_symbol(intent: dict[str, Any]) -> str:
    source = intent.get("source") if isinstance(intent.get("source"), dict) else {}
    return str(source.get("symbol") or "").strip()


def _open_position_count(mt5, symbol_map: dict[str, str]) -> int:
    tickets: set[int] = set()
    for broker_symbol in symbol_map.values():
        try:
            for pos in _positions_for_broker_symbol(mt5, broker_symbol):
                tickets.add(int(pos.ticket))
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("position count probe failed for %s: %s", broker_symbol, exc)
    return len(tickets)


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return numeric


def _nested_dict(root: dict[str, Any], key: str) -> dict[str, Any]:
    value = root.get(key)
    return value if isinstance(value, dict) else {}


def _runtime_config(config: dict[str, Any]) -> dict[str, Any]:
    return _nested_dict(config, "gtos_vnext_runtime")


def _risk_config(config: dict[str, Any]) -> dict[str, Any]:
    return _nested_dict(config, "risk")


def _ftmo_rules(config: dict[str, Any]) -> dict[str, Any]:
    return _nested_dict(config, "ftmo_rules")


def _config_float(
    root: dict[str, Any],
    section: str,
    key: str,
    default: float | None = None,
) -> float | None:
    return _safe_float(_nested_dict(root, section).get(key), default)


def _initial_balance_for_budget(config: dict[str, Any], current_balance: float) -> float:
    for value in (
        _runtime_config(config).get("prop_safe_selector_initial_balance"),
        _ftmo_rules(config).get("account_balance_initial_inferred_usd"),
        config.get("initial_balance"),
        current_balance,
    ):
        numeric = _safe_float(value)
        if numeric is not None and numeric > 0:
            return numeric
    return current_balance


def _daily_loss_limit_pct(config: dict[str, Any]) -> float:
    for value in (
        _runtime_config(config).get("prop_safe_selector_external_daily_loss_limit_pct"),
        _ftmo_rules(config).get("maximum_daily_loss_pct"),
        _risk_config(config).get("external_daily_loss_limit_pct"),
        5.0,
    ):
        numeric = _safe_float(value)
        if numeric is not None and numeric > 0:
            return numeric
    return 5.0


def _overall_loss_limit_pct(config: dict[str, Any]) -> float:
    for value in (
        _runtime_config(config).get("prop_safe_selector_external_overall_max_loss_pct"),
        _ftmo_rules(config).get("maximum_loss_pct"),
        _risk_config(config).get("external_overall_loss_limit_pct"),
        10.0,
    ):
        numeric = _safe_float(value)
        if numeric is not None and numeric > 0:
            return numeric
    return 10.0


def _internal_daily_limit_pct(config: dict[str, Any]) -> float | None:
    runtime = _runtime_config(config)
    apply_internal = _truthy(
        runtime.get("prop_safe_selector_apply_internal_daily_overlay", True)
    )
    if not apply_internal:
        return None
    for value in (
        runtime.get("prop_safe_selector_internal_daily_loss_limit_pct"),
        _risk_config(config).get("max_daily_loss_pct"),
    ):
        numeric = _safe_float(value)
        if numeric is not None and numeric > 0:
            return numeric
    return None


def _overall_remaining_cushion_pct(config: dict[str, Any]) -> float:
    for value in (
        _runtime_config(config).get("prop_safe_selector_overall_remaining_cushion_pct"),
        _risk_config(config).get("overall_remaining_cushion_pct"),
        0.0,
    ):
        numeric = _safe_float(value)
        if numeric is not None and numeric >= 0:
            return numeric
    return 0.0


def _min_reduced_risk_pct(config: dict[str, Any], requested_risk_pct: float) -> float:
    for value in (
        _runtime_config(config).get("prop_safe_selector_min_reduced_risk_pct"),
        _risk_config(config).get("min_reduced_risk_pct"),
        requested_risk_pct,
    ):
        numeric = _safe_float(value)
        if numeric is not None and numeric > 0:
            return min(numeric, requested_risk_pct)
    return requested_risk_pct


def _target_risk_buffer_amount(config: dict[str, Any], initial_balance: float) -> float:
    runtime = _runtime_config(config)
    for key in (
        "prop_safe_selector_spread_slippage_commission_buffer_amount",
        "prop_safe_selector_default_spread_slippage_commission_buffer_amount",
    ):
        numeric = _safe_float(runtime.get(key))
        if numeric is not None and numeric >= 0:
            return numeric
    pct = _safe_float(
        runtime.get("prop_safe_selector_default_spread_slippage_commission_buffer_pct"),
        0.10,
    )
    if pct is None or pct < 0:
        pct = 0.10
    return max(0.0, initial_balance * pct / 100.0)


def _daily_reset_start_utc(
    config: dict[str, Any],
    now_utc: datetime | None = None,
) -> datetime:
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    runtime = _runtime_config(config)
    tz_name = str(runtime.get("prop_safe_selector_daily_reset_timezone") or "").strip()
    if not tz_name and "CE(S)T" in str(_ftmo_rules(config).get("daily_reset_time") or ""):
        tz_name = "Europe/Prague"
    if tz_name:
        try:
            tz = ZoneInfo(tz_name)
            local_now = now.astimezone(tz)
            local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
            return local_start.astimezone(timezone.utc)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("daily reset timezone %s unavailable: %s", tz_name, exc)

    offset_hours = _safe_float(
        runtime.get("prop_safe_selector_daily_reset_timezone_offset_hours"),
        DEFAULT_DAILY_RESET_OFFSET_HOURS,
    )
    if offset_hours is None:
        offset_hours = DEFAULT_DAILY_RESET_OFFSET_HOURS
    offset = timedelta(hours=offset_hours)
    shifted = now + offset
    shifted_start = shifted.replace(hour=0, minute=0, second=0, microsecond=0)
    return shifted_start - offset


def _history_realized_pnl_since_reset(
    mt5: Any,
    symbol_map: dict[str, str],
    reset_start_utc: datetime,
    now_utc: datetime,
) -> tuple[float, int, str | None]:
    get_history_deals = getattr(mt5, "get_history_deals", None)
    if not callable(get_history_deals):
        return 0.0, 0, "history_deals_unavailable"
    realized = 0.0
    deal_count = 0
    seen: set[str] = set()
    for broker_symbol in sorted(set(symbol_map.values())):
        try:
            deals = get_history_deals(reset_start_utc, now_utc, broker_symbol)
        except Exception as exc:  # noqa: BLE001
            return realized, deal_count, f"history_deals_probe_failed:{broker_symbol}:{exc}"
        if deals is None:
            # C6. `get_history_deals` returns None for a FAILED broker fetch and
            # [] for "no deals today"; the previous `or []` collapsed them, so an
            # unreadable history silently reset the reconstructed day-start
            # balance to the CURRENT (already drawn-down) balance and re-opened
            # the whole daily-loss budget. Report the failure instead.
            return realized, deal_count, f"history_deals_unreadable:{broker_symbol}"
        for deal in deals:
            if not isinstance(deal, dict):
                continue
            key = str(
                deal.get("ticket")
                or deal.get("deal")
                or deal.get("order")
                or deal.get("position_id")
                or f"{broker_symbol}:{deal.get('time')}:{deal.get('profit')}"
            )
            if key in seen:
                continue
            seen.add(key)
            amount = 0.0
            for field in ("profit", "commission", "swap", "fee"):
                amount += _safe_float(deal.get(field), 0.0) or 0.0
            realized += amount
            deal_count += 1
    return realized, deal_count, None


def _day_start_baseline_for_budget(
    mt5: Any,
    config: dict[str, Any],
    symbol_map: dict[str, str],
    current_balance: float,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    reset_start = _daily_reset_start_utc(config, now)
    realized, deal_count, history_error = _history_realized_pnl_since_reset(
        mt5,
        symbol_map,
        reset_start,
        now,
    )
    day_start_balance = current_balance - realized
    return {
        "baseline": day_start_balance,
        "day_start_balance": day_start_balance,
        "realized_pnl_since_reset": realized,
        "history_deal_count": deal_count,
        "history_error": history_error,
        "reset_start_utc": reset_start.isoformat(),
        "reset_reference_utc": now.isoformat(),
    }


def _symbol_config_for_broker_symbol(
    base_config: dict[str, Any],
    symbol_map: dict[str, str],
    broker_symbol: str,
) -> dict[str, Any]:
    for source_symbol, mapped_broker_symbol in symbol_map.items():
        if mapped_broker_symbol == broker_symbol:
            return load_target_symbol_config(base_config, source_symbol)
    return base_config


def _market_float(market: dict[str, Any], *keys: str, default: float | None = None) -> float | None:
    for key in keys:
        numeric = _safe_float(market.get(key))
        if numeric is not None and numeric > 0:
            return numeric
    return default


def _position_profit_at_price_with_source(
    mt5: Any,
    position: Any,
    target_price: float,
    symbol_config: dict[str, Any],
    *,
    allow_tick_metadata_fallback: bool = True,
) -> tuple[float | None, str]:
    broker_symbol = str(getattr(position, "symbol", "") or "")
    volume = _safe_float(getattr(position, "volume", None))
    price_open = _safe_float(getattr(position, "price_open", None))
    position_type = int(_safe_float(getattr(position, "type", 0), 0) or 0)
    if not broker_symbol or volume is None or volume <= 0 or price_open is None:
        return None, "position_geometry_unresolved"
    raw_mt5 = getattr(mt5, "_mt5", None)
    order_calc_profit = getattr(raw_mt5, "order_calc_profit", None)
    if callable(order_calc_profit):
        try:
            calculated = order_calc_profit(
                position_type,
                broker_symbol,
                volume,
                price_open,
                target_price,
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("order_calc_profit failed for %s: %s", broker_symbol, exc)
        else:
            numeric = _safe_float(calculated)
            if numeric is not None:
                return numeric, "broker_order_calc_profit"

    if not allow_tick_metadata_fallback:
        return None, "broker_order_calc_profit_required_unavailable"

    market = _nested_dict(symbol_config, "market")
    tick_size = _market_float(market, "trade_tick_size", "tick_size", "point")
    tick_value = _market_float(
        market,
        "trade_tick_value_loss",
        "trade_tick_value",
        "tick_value",
    )
    if tick_size is None or tick_size <= 0 or tick_value is None or tick_value <= 0:
        return None, "symbol_tick_metadata_unresolved"
    price_delta = (
        target_price - price_open if position_type == 0 else price_open - target_price
    )
    return (
        price_delta / tick_size
    ) * tick_value * volume, "symbol_tick_metadata_fallback"


def _position_profit_at_price(
    mt5: Any,
    position: Any,
    target_price: float,
    symbol_config: dict[str, Any],
) -> float | None:
    profit_at_price, _source = _position_profit_at_price_with_source(
        mt5,
        position,
        target_price,
        symbol_config,
    )
    return profit_at_price


def _target_open_position_sl_risk_amount(
    mt5: Any,
    base_config: dict[str, Any],
    symbol_map: dict[str, str],
    *,
    require_broker_profit_model: bool = True,
) -> tuple[float, list[dict[str, Any]], list[str]]:
    total = 0.0
    details: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_tickets: set[int] = set()
    for broker_symbol in sorted(set(symbol_map.values())):
        try:
            positions = _positions_for_broker_symbol(mt5, broker_symbol)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"position_probe_failed:{broker_symbol}:{exc}")
            continue
        for position in positions:
            ticket = int(_safe_float(getattr(position, "ticket", 0), 0) or 0)
            if ticket and ticket in seen_tickets:
                continue
            if ticket:
                seen_tickets.add(ticket)
            position_symbol = str(getattr(position, "symbol", broker_symbol) or broker_symbol)
            symbol_config = _symbol_config_for_broker_symbol(
                base_config,
                symbol_map,
                position_symbol,
            )
            sl = _safe_float(getattr(position, "sl", None))
            if sl is None or sl <= 0:
                errors.append(f"open_position_missing_stop_loss:{ticket or position_symbol}")
                details.append(
                    {
                        "ticket": ticket,
                        "broker_symbol": position_symbol,
                        "status": "missing_stop_loss",
                    }
                )
                continue
            current_profit = _safe_float(getattr(position, "profit", 0.0), 0.0) or 0.0
            profit_at_sl, profit_model = _position_profit_at_price_with_source(
                mt5,
                position,
                sl,
                symbol_config,
                allow_tick_metadata_fallback=not require_broker_profit_model,
            )
            if profit_at_sl is None:
                errors.append(
                    "open_position_sl_risk_unresolved:"
                    f"{ticket or position_symbol}:{profit_model}"
                )
                details.append(
                    {
                        "ticket": ticket,
                        "broker_symbol": position_symbol,
                        "status": "profit_at_stop_unresolved",
                        "stop_loss": sl,
                        "profit_model": profit_model,
                    }
                )
                continue
            if require_broker_profit_model and profit_model != "broker_order_calc_profit":
                errors.append(
                    "open_position_sl_risk_unverified_profit_model:"
                    f"{ticket or position_symbol}:{profit_model}"
                )
                details.append(
                    {
                        "ticket": ticket,
                        "broker_symbol": position_symbol,
                        "status": "unverified_profit_model",
                        "stop_loss": sl,
                        "profit_at_stop_loss": profit_at_sl,
                        "profit_model": profit_model,
                    }
                )
                continue
            additional_risk = max(0.0, current_profit - profit_at_sl)
            total += additional_risk
            details.append(
                {
                    "ticket": ticket,
                    "broker_symbol": position_symbol,
                    "type": int(_safe_float(getattr(position, "type", 0), 0) or 0),
                    "volume": _safe_float(getattr(position, "volume", None)),
                    "price_open": _safe_float(getattr(position, "price_open", None)),
                    "stop_loss": sl,
                    "current_profit": current_profit,
                    "profit_at_stop_loss": profit_at_sl,
                    "profit_model": profit_model,
                    "additional_risk_to_stop_loss": additional_risk,
                }
            )
    return total, details, errors


def _pending_engine_risk_amount(engines: dict[str, ExecutionEngine]) -> float:
    total = 0.0
    for engine in engines.values():
        intent = getattr(engine, "pending_intent", None)
        if intent is None:
            continue
        account_balance = _safe_float(getattr(intent, "account_balance", None))
        risk_pct = _safe_float(getattr(intent, "risk_pct", None))
        if account_balance is None or risk_pct is None:
            continue
        total += max(0.0, account_balance * risk_pct / 100.0)
    return total


def _target_account_budget_projection(
    *,
    mt5: Any,
    base_config: dict[str, Any],
    symbol_map: dict[str, str],
    engines: dict[str, ExecutionEngine],
    requested_risk_pct: float,
    source_symbol: str,
) -> dict[str, Any]:
    balance = _safe_float(getattr(mt5, "get_account_balance")(), None)
    equity = _safe_float(getattr(mt5, "get_account_equity")(), None)
    if balance is None or balance <= 0 or equity is None or equity <= 0:
        return {
            "action": "BLOCK",
            "reason": "target_account_state_unavailable",
            "requested_risk_pct": requested_risk_pct,
            "after_risk_pct": None,
        }

    cfg = load_target_symbol_config(base_config, source_symbol)
    initial_balance = _initial_balance_for_budget(cfg, balance)
    day_state = _day_start_baseline_for_budget(
        mt5,
        cfg,
        symbol_map,
        balance,
    )
    daily_pct = _daily_loss_limit_pct(cfg)
    overall_pct = _overall_loss_limit_pct(cfg)
    internal_daily_pct = _internal_daily_limit_pct(cfg)
    overall_cushion_pct = _overall_remaining_cushion_pct(cfg)
    buffer_amount = _target_risk_buffer_amount(cfg, initial_balance)
    open_risk_amount, open_risk_details, open_risk_errors = (
        _target_open_position_sl_risk_amount(mt5, base_config, symbol_map)
    )
    pending_risk_amount = _pending_engine_risk_amount(engines)
    if open_risk_errors:
        return {
            "action": "BLOCK",
            "reason": "target_open_position_sl_risk_unavailable",
            "requested_risk_pct": requested_risk_pct,
            "after_risk_pct": None,
            "account": {
                "balance": balance,
                "equity": equity,
                "initial_balance": initial_balance,
                "day_start": day_state,
            },
            "open_position_risk_amount": open_risk_amount,
            "open_position_risk_errors": open_risk_errors,
            "open_position_risk_details": open_risk_details,
            "open_position_profit_model_requirement": "broker_order_calc_profit",
        }

    risk_base_amount = balance
    requested_risk_amount = max(0.0, risk_base_amount * requested_risk_pct / 100.0)
    min_reduced_pct = _min_reduced_risk_pct(cfg, requested_risk_pct)
    min_reduced_amount = risk_base_amount * min_reduced_pct / 100.0
    existing_and_buffer = open_risk_amount + pending_risk_amount + buffer_amount
    day_start_baseline = _safe_float(day_state.get("baseline"), balance) or balance
    budget_limits: list[dict[str, Any]] = [
        {
            "name": "external_daily_drawdown",
            "floor": day_start_baseline - (initial_balance * daily_pct / 100.0),
            "limit_pct": daily_pct,
            "reset_start_utc": day_state.get("reset_start_utc"),
        },
        {
            "name": "external_overall_drawdown_with_cushion"
            if overall_cushion_pct > 0
            else "external_overall_drawdown",
            "floor": initial_balance
            * (1.0 - ((overall_pct - overall_cushion_pct) / 100.0)),
            "limit_pct": overall_pct,
            "cushion_pct": overall_cushion_pct,
        },
    ]
    if internal_daily_pct is not None and internal_daily_pct > 0:
        budget_limits.append(
            {
                "name": "internal_daily_drawdown_overlay",
                "floor": day_start_baseline
                - (initial_balance * internal_daily_pct / 100.0),
                "limit_pct": internal_daily_pct,
                "reset_start_utc": day_state.get("reset_start_utc"),
            }
        )

    remaining_limits: list[dict[str, Any]] = []
    for limit in budget_limits:
        floor = float(limit["floor"])
        remaining = equity - floor - existing_and_buffer
        projected_remaining = remaining - requested_risk_amount
        remaining_limits.append(
            {
                **limit,
                "remaining_after_existing_risk_amount": remaining,
                "projected_remaining_after_requested_risk_amount": projected_remaining,
            }
        )
    binding = min(
        remaining_limits,
        key=lambda row: row["remaining_after_existing_risk_amount"],
    )
    available_for_new_risk = float(binding["remaining_after_existing_risk_amount"])

    action = "ALLOW"
    after_risk_pct = requested_risk_pct
    reason = "target_account_drawdown_budget_allows_full_risk"
    if available_for_new_risk + TARGET_RISK_BUDGET_EPSILON < requested_risk_amount:
        if available_for_new_risk + TARGET_RISK_BUDGET_EPSILON >= min_reduced_amount:
            action = "REDUCE_RISK"
            after_risk_pct = max(0.0, available_for_new_risk / risk_base_amount * 100.0)
            after_risk_pct = min(after_risk_pct, requested_risk_pct)
            reason = f"target_account_drawdown_budget_reduced_by:{binding['name']}"
        else:
            action = "BLOCK"
            after_risk_pct = None
            reason = f"target_account_drawdown_budget_blocked_by:{binding['name']}"

    return {
        "action": action,
        "reason": reason,
        "requested_risk_pct": requested_risk_pct,
        "after_risk_pct": after_risk_pct,
        "account": {
            "balance": balance,
            "equity": equity,
            "initial_balance": initial_balance,
            "day_start": day_state,
        },
        "budget_limits": remaining_limits,
        "binding_budget": binding["name"],
        "risk_base_amount": risk_base_amount,
        "requested_risk_amount": requested_risk_amount,
        "min_reduced_risk_pct": min_reduced_pct,
        "min_reduced_risk_amount": min_reduced_amount,
        "open_position_risk_amount": open_risk_amount,
        "pending_order_risk_amount": pending_risk_amount,
        "buffer_amount": buffer_amount,
        "available_for_new_risk_amount": available_for_new_risk,
        "open_position_risk_details": open_risk_details,
        "open_position_profit_model_requirement": "broker_order_calc_profit",
    }


def _positions_for_broker_symbol(mt5: Any, broker_symbol: str) -> list[Any]:
    positions = mt5.get_positions(broker_symbol) or []
    filtered: list[Any] = []
    for position in positions:
        position_symbol = str(getattr(position, "symbol", broker_symbol) or "").strip()
        if not position_symbol or position_symbol == broker_symbol:
            filtered.append(position)
    return filtered


def _latest_closed_m15(mt5, broker_symbol: str) -> dict[str, Any] | None:
    candles = mt5.get_candles(broker_symbol, TF_MAP["M15"], 4) or []
    if not candles:
        return None
    if len(candles) >= 2:
        return candles[-2]
    return candles[-1]


def _install_notification_suppression() -> None:
    os.environ["GTOS_NOTIFICATIONS_DISABLED"] = "1"
    os.environ["GTOS_NOTIFICATION_QUEUE_DISABLED"] = "1"
    try:
        import src.notifications as notifications
    except Exception:  # noqa: BLE001
        return

    def _noop(*args, **kwargs):  # noqa: ANN001, ARG001
        return None

    for name in dir(notifications):
        if name.startswith("notify_"):
            setattr(notifications, name, _noop)


@dataclass
class FollowerRuntime:
    mt5: Any
    base_config: dict[str, Any]
    target_namespace: str
    source_namespace: str
    order_enabled: bool
    action_log: Path
    symbol_map: dict[str, str]
    target_trade_state_path: Path | None = None
    max_live_recovery_intent_age_seconds: float | None = DEFAULT_LIVE_RECOVERY_WINDOW_SECONDS
    engines: dict[str, ExecutionEngine] = field(default_factory=dict)
    processed_intent_ids: set[str] = field(default_factory=set)
    reprocessable_failed_intent_ids: set[str] = field(default_factory=set)
    latest_checked_candle: dict[str, str] = field(default_factory=dict)
    deferred_intent_log_monotonic: dict[str, float] = field(default_factory=dict)
    deferred_no_target_position_counts: dict[str, int] = field(default_factory=dict)
    last_risk_budget_projection: dict[str, dict[str, Any]] = field(default_factory=dict)
    active_trade_intent_ids: dict[str, str] = field(default_factory=dict)
    _last_trade_state_store_hash: str | None = None

    def _trade_state_path(self) -> Path:
        if self.target_trade_state_path is not None:
            return Path(self.target_trade_state_path)
        return _default_target_trade_state_path(self.target_namespace)

    def _read_trade_state_store(self) -> dict[str, Any]:
        return _read_json(self._trade_state_path())

    def _active_trade_snapshot(
        self,
        *,
        symbol: str,
        broker_symbol: str,
        trade: TradeState,
        source: str,
        intent_id: str | None = None,
    ) -> dict[str, Any]:
        ticket_key = _ticket_key(getattr(trade, "ticket", None))
        resolved_intent_id = intent_id
        if not resolved_intent_id and ticket_key:
            resolved_intent_id = self.active_trade_intent_ids.get(ticket_key)
        return {
            "schema_version": 1,
            "updated_at_utc": _utcnow_iso(),
            "target_namespace": self.target_namespace,
            "symbol": symbol,
            "broker_symbol": broker_symbol,
            "ticket": trade.ticket,
            "intent_id": resolved_intent_id,
            "source": source,
            "trade_state": _trade_state_payload(trade),
        }

    def _remember_active_trade_intent(
        self,
        trade: TradeState | None,
        intent_id: Any,
    ) -> None:
        resolved_intent_id = str(intent_id or "").strip()
        ticket_key = _ticket_key(getattr(trade, "ticket", None))
        if resolved_intent_id and ticket_key:
            self.active_trade_intent_ids[ticket_key] = resolved_intent_id

    def _action_log_trade_snapshots_by_ticket(self) -> dict[str, dict[str, Any]]:
        """Recover target trade state from prior follower action-log rows.

        This is a startup-only fallback for deployments that already had live
        FTMO positions before the compact target-state store existed.
        """
        snapshots: dict[str, dict[str, Any]] = {}
        if not self.action_log.exists():
            return snapshots
        try:
            fh = self.action_log.open(encoding="utf-8")
        except OSError as exc:
            LOGGER.warning("target action-log state recovery read failed: %s", exc)
            return snapshots
        with fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                result = row.get("result")
                if not isinstance(result, dict):
                    continue
                ticket_key = _ticket_key(result.get("ticket"))
                if not ticket_key:
                    continue
                symbol = str(row.get("symbol") or result.get("symbol") or "").strip()
                if not symbol:
                    continue
                snapshots[ticket_key] = {
                    "schema_version": 1,
                    "updated_at_utc": row.get("recorded_at_utc") or _utcnow_iso(),
                    "target_namespace": self.target_namespace,
                    "symbol": symbol,
                    "broker_symbol": self.symbol_map.get(symbol, symbol),
                    "ticket": int(ticket_key),
                    "intent_id": row.get("intent_id"),
                    "source": "dual_broker_execution_follower_action_log",
                    "trade_state": result,
                }
        return snapshots

    def _trade_snapshots_by_ticket(self) -> dict[str, dict[str, Any]]:
        snapshots = self._action_log_trade_snapshots_by_ticket()
        store = self._read_trade_state_store()
        persisted = store.get("active_trades_by_ticket")
        if isinstance(persisted, dict):
            for ticket_key, snapshot in persisted.items():
                if isinstance(snapshot, dict):
                    ticket_key_text = str(ticket_key)
                    action_snapshot = snapshots.get(ticket_key_text) or {}
                    merged_snapshot = dict(snapshot)
                    if not str(merged_snapshot.get("intent_id") or "").strip():
                        action_intent_id = str(
                            action_snapshot.get("intent_id") or ""
                        ).strip()
                        if action_intent_id:
                            merged_snapshot["intent_id"] = action_intent_id
                            merged_snapshot[
                                "intent_id_source"
                            ] = "dual_broker_execution_follower_action_log"
                    snapshots[ticket_key_text] = merged_snapshot
        return snapshots

    @staticmethod
    def _sync_restored_trade_with_position(trade: TradeState, position: Any) -> TradeState:
        trade.ticket = int(getattr(position, "ticket", trade.ticket))
        trade.current_volume = float(getattr(position, "volume", trade.current_volume) or 0.0)
        broker_sl = _safe_float(getattr(position, "sl", None))
        if broker_sl is not None and broker_sl > 0:
            trade.stop_loss = broker_sl
            if trade.direction == "LONG":
                trade.sl_at_breakeven = broker_sl >= float(trade.entry_price or 0.0)
            else:
                trade.sl_at_breakeven = broker_sl <= float(trade.entry_price or 0.0)
        broker_tp = _safe_float(getattr(position, "tp", None))
        if broker_tp is not None and broker_tp > 0 and not trade.take_profit_2:
            trade.take_profit_2 = broker_tp
        selected_policy = str(
            trade.gtos_vnext_dynamic_policy_selected or ""
        ).strip().lower()
        residual_volume = (
            float(trade.initial_volume or 0.0) > 0
            and trade.current_volume < float(trade.initial_volume or 0.0) - 1e-9
        )
        if (
            selected_policy in {"partial_be_runner", "trailing_runner", "momentum_exhaustion"}
            and (residual_volume or trade.sl_at_breakeven)
        ):
            trade.tp1_hit = True
            trade.gtos_vnext_dynamic_mfe_r = max(
                float(trade.gtos_vnext_dynamic_mfe_r or 0.0),
                float(trade.gtos_vnext_dynamic_be_trigger_r or 0.0),
            )
            if not any(
                str(event.get("type") or "").startswith(
                    "TARGET_STATE_RECOVERED_BROKER_RESIDUAL"
                )
                for event in trade.partial_close_events
                if isinstance(event, dict)
            ):
                trade.partial_close_events.append(
                    {
                        "type": "TARGET_STATE_RECOVERED_BROKER_RESIDUAL",
                        "time": _utcnow_iso(),
                        "broker_ticket": trade.ticket,
                        "broker_volume": trade.current_volume,
                        "initial_volume": trade.initial_volume,
                        "broker_sl": broker_sl,
                        "broker_tp": broker_tp,
                        "selected_policy": selected_policy,
                        "tp1_hit_inferred": True,
                        "reason": "broker_residual_volume_or_breakeven_sl_on_restore",
                    }
                )
        trade.position_confirmed = True
        return trade

    def _annotate_restored_cash_risk_metadata(
        self,
        *,
        symbol: str,
        broker_symbol: str,
        trade: TradeState,
        position: Any | None,
    ) -> str | None:
        source_blank = not str(
            getattr(trade, "cash_risk_amount_source", "") or ""
        ).strip()
        status_blank = not str(
            getattr(trade, "cash_risk_amount_status", "") or ""
        ).strip()
        existing_source = str(getattr(trade, "cash_risk_amount_source", "") or "")
        existing_status = str(getattr(trade, "cash_risk_amount_status", "") or "")
        weak_existing = any(
            marker in existing_source.upper() or marker in existing_status.upper()
            for marker in (
                "UNVERIFIED",
                "UNRESOLVED",
                "POSITION_MISSING",
                "MISSING_STOP",
                "TICK_METADATA",
            )
        )
        if (
            not source_blank
            and not status_blank
            and not (position is not None and weak_existing)
        ):
            return None

        diagnostic = dict(trade.broker_lot_sizing_diagnostic or {})
        restore_diag: dict[str, Any] = {
            "recorded_at_utc": _utcnow_iso(),
            "symbol": symbol,
            "broker_symbol": broker_symbol,
            "ticket": getattr(trade, "ticket", None),
            "cash_risk_amount": getattr(trade, "cash_risk_amount", None),
            "reason": "target_trade_state_restored_without_cash_risk_provenance",
        }

        if position is None:
            source = "legacy_target_state_amount_unverified_position_missing"
            status = "LEGACY_TARGET_STATE_CASH_RISK_PROVENANCE_POSITION_MISSING"
            restore_diag["status"] = status
        else:
            stop_loss = _safe_float(getattr(position, "sl", None))
            restore_diag.update(
                {
                    "position_volume": _safe_float(getattr(position, "volume", None)),
                    "position_entry": _safe_float(getattr(position, "price_open", None)),
                    "position_stop_loss": stop_loss,
                }
            )
            if stop_loss is None or stop_loss <= 0:
                source = "legacy_target_state_amount_unverified_no_current_stop"
                status = "LEGACY_TARGET_STATE_CASH_RISK_PROVENANCE_MISSING_STOP_LOSS"
                restore_diag["status"] = status
            else:
                symbol_config = load_target_symbol_config(self.base_config, symbol)
                profit_at_stop, profit_model = _position_profit_at_price_with_source(
                    self.mt5,
                    position,
                    stop_loss,
                    symbol_config,
                )
                if (
                    not source_blank
                    and not status_blank
                    and weak_existing
                    and profit_model != "broker_order_calc_profit"
                ):
                    return None
                restore_diag.update(
                    {
                        "profit_model": profit_model,
                        "profit_at_current_stop": profit_at_stop,
                    }
                )
                if profit_at_stop is None:
                    source = "legacy_target_state_amount_unverified_profit_model_unresolved"
                    status = "LEGACY_TARGET_STATE_CASH_RISK_PROVENANCE_UNRESOLVED"
                    restore_diag["status"] = status
                elif profit_at_stop >= 0:
                    source = (
                        f"legacy_target_state_amount_current_sl_{profit_model}"
                        "_zero_risk_checked"
                    )
                    status = (
                        "LEGACY_AMOUNT_CURRENT_SL_ZERO_RISK_VERIFIED"
                        if profit_model == "broker_order_calc_profit"
                        else "LEGACY_AMOUNT_CURRENT_SL_ZERO_RISK_TICK_METADATA_CHECKED"
                    )
                    trade.broker_cash_risk_per_lot = 0.0
                    restore_diag["current_stop_cash_risk_amount"] = 0.0
                    restore_diag["status"] = status
                else:
                    current_stop_risk = abs(float(profit_at_stop))
                    position_volume = _safe_float(getattr(position, "volume", None))
                    source = (
                        f"legacy_target_state_amount_current_sl_{profit_model}"
                        "_checked"
                    )
                    status = (
                        "LEGACY_AMOUNT_CURRENT_SL_RISK_VERIFIED"
                        if profit_model == "broker_order_calc_profit"
                        else "LEGACY_AMOUNT_CURRENT_SL_RISK_TICK_METADATA_CHECKED"
                    )
                    if position_volume and position_volume > 0:
                        trade.broker_cash_risk_per_lot = (
                            current_stop_risk / position_volume
                        )
                    restore_diag.update(
                        {
                            "current_stop_cash_risk_amount": current_stop_risk,
                            "broker_cash_risk_per_lot": trade.broker_cash_risk_per_lot,
                            "status": status,
                        }
                    )

        if source_blank:
            trade.cash_risk_amount_source = source
        if status_blank:
            trade.cash_risk_amount_status = status
        diagnostic["target_state_restore_cash_risk_provenance"] = restore_diag
        trade.broker_lot_sizing_diagnostic = diagnostic
        return trade.cash_risk_amount_status

    def _restore_engine_trade_state_from_snapshot(
        self,
        *,
        symbol: str,
        broker_symbol: str,
        engine: ExecutionEngine,
        positions: list[Any],
        snapshots_by_ticket: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        trade = engine.active_trade
        if trade is None:
            return None
        ticket_key = _ticket_key(getattr(trade, "ticket", None))
        if not ticket_key:
            return None
        snapshot = snapshots_by_ticket.get(ticket_key)
        if not snapshot:
            return {
                "symbol": symbol,
                "broker_symbol": broker_symbol,
                "ticket": getattr(trade, "ticket", None),
                "status": "generic_orphan_without_persisted_target_trade_state",
            }
        restored = _trade_state_from_payload(snapshot.get("trade_state") or {})
        if restored is None:
            return {
                "symbol": symbol,
                "broker_symbol": broker_symbol,
                "ticket": getattr(trade, "ticket", None),
                "status": "persisted_target_trade_state_unusable",
                "source": snapshot.get("source"),
            }
        position = next(
            (
                item
                for item in positions
                if _ticket_key(getattr(item, "ticket", None)) == ticket_key
            ),
            None,
        )
        if position is not None:
            restored = self._sync_restored_trade_with_position(restored, position)
        cash_risk_restore_status = self._annotate_restored_cash_risk_metadata(
            symbol=symbol,
            broker_symbol=broker_symbol,
            trade=restored,
            position=position,
        )
        self._remember_active_trade_intent(restored, snapshot.get("intent_id"))
        engine.active_trade = restored
        return {
            "symbol": symbol,
            "broker_symbol": broker_symbol,
            "ticket": restored.ticket,
            "status": "target_trade_state_restored",
            "source": snapshot.get("source"),
            "intent_id": snapshot.get("intent_id"),
            "cash_risk_amount_status": restored.cash_risk_amount_status,
            "cash_risk_restore_status": cash_risk_restore_status,
            "dynamic_policy_selected": restored.gtos_vnext_dynamic_policy_selected,
            "dynamic_policy_applied": restored.gtos_vnext_dynamic_policy_applied,
            "tp1_hit": restored.tp1_hit,
            "sl_at_breakeven": restored.sl_at_breakeven,
        }

    def persist_target_trade_state(self, *, reason: str) -> dict[str, Any]:
        active_by_ticket: dict[str, dict[str, Any]] = {}
        active_by_symbol: dict[str, str] = {}
        position_cache: dict[str, list[Any]] = {}

        def position_for_trade(broker_symbol: str, ticket_key: str) -> Any | None:
            if broker_symbol not in position_cache:
                try:
                    position_cache[broker_symbol] = _positions_for_broker_symbol(
                        self.mt5,
                        broker_symbol,
                    )
                except Exception as exc:  # noqa: BLE001
                    LOGGER.warning(
                        "target trade-state broker position refresh failed for %s: %s",
                        broker_symbol,
                        exc,
                    )
                    position_cache[broker_symbol] = []
            for position in position_cache[broker_symbol]:
                if _ticket_key(getattr(position, "ticket", None)) == ticket_key:
                    return position
            return None

        for symbol, engine in sorted(self.engines.items()):
            trade = engine.active_trade
            if trade is None:
                continue
            ticket_key = _ticket_key(getattr(trade, "ticket", None))
            if not ticket_key:
                continue
            broker_symbol = self.symbol_map.get(symbol, symbol)
            position = position_for_trade(broker_symbol, ticket_key)
            if position is not None:
                self._sync_restored_trade_with_position(trade, position)
                self._annotate_restored_cash_risk_metadata(
                    symbol=symbol,
                    broker_symbol=broker_symbol,
                    trade=trade,
                    position=position,
                )
            snapshot = self._active_trade_snapshot(
                symbol=symbol,
                broker_symbol=broker_symbol,
                trade=trade,
                source=reason,
            )
            active_by_ticket[ticket_key] = snapshot
            active_by_symbol[symbol] = ticket_key
        store = {
            "schema_version": 1,
            "updated_at_utc": _utcnow_iso(),
            "target_namespace": self.target_namespace,
            "reason": reason,
            "active_trades_by_ticket": active_by_ticket,
            "active_trades_by_symbol": active_by_symbol,
            "active_trade_count": len(active_by_ticket),
        }
        stable_store = {
            "schema_version": store["schema_version"],
            "target_namespace": store["target_namespace"],
            "active_trades_by_ticket": active_by_ticket,
            "active_trades_by_symbol": active_by_symbol,
            "active_trade_count": len(active_by_ticket),
        }
        store_hash = hashlib.sha256(
            json.dumps(_jsonable(stable_store), sort_keys=True).encode("utf-8")
        ).hexdigest()
        if store_hash != self._last_trade_state_store_hash:
            _write_json(self._trade_state_path(), store)
            self._last_trade_state_store_hash = store_hash
        return store

    def engine_for(self, symbol: str) -> ExecutionEngine:
        existing = self.engines.get(symbol)
        if existing is not None:
            return existing
        cfg = load_target_symbol_config(self.base_config, symbol)
        engine = ExecutionEngine(self.mt5, cfg)
        actions = engine.reconcile_on_startup()
        if actions:
            _append_jsonl(
                self.action_log,
                {
                    "event": "startup_reconcile",
                    "symbol": symbol,
                    "actions": actions,
                    "target_namespace": self.target_namespace,
                },
            )
        self.engines[symbol] = engine
        return engine

    def _pending_intent_file_for_symbol(self, symbol: str) -> Path:
        cfg = load_target_symbol_config(self.base_config, symbol)
        market = cfg.get("market") if isinstance(cfg.get("market"), dict) else {}
        persist_symbol = str(market.get("symbol") or symbol)
        return namespaced_file_path(
            Path(PENDING_INTENT_DIR) / f"pending_intent_{persist_symbol}.pkl",
            self.target_namespace,
        )

    def recover_target_state_on_startup(self) -> dict[str, Any]:
        """Instantiate only target symbols that already need lifecycle management."""
        symbols_with_positions: list[str] = []
        symbols_with_pending_intents: list[str] = []
        recovered_actions: list[dict[str, Any]] = []
        snapshots_by_ticket = self._trade_snapshots_by_ticket()

        for symbol, broker_symbol in sorted(self.symbol_map.items()):
            try:
                positions = _positions_for_broker_symbol(self.mt5, broker_symbol)
            except Exception as exc:  # noqa: BLE001
                recovered_actions.append(
                    {
                        "symbol": symbol,
                        "broker_symbol": broker_symbol,
                        "status": "position_probe_failed",
                        "error": str(exc),
                    }
                )
                continue
            pending_path = self._pending_intent_file_for_symbol(symbol)
            has_positions = bool(positions)
            has_pending = pending_path.exists()
            if not has_positions and not has_pending:
                continue
            if has_positions:
                symbols_with_positions.append(symbol)
            if has_pending:
                symbols_with_pending_intents.append(symbol)
            engine = self.engine_for(symbol)
            restored_state = self._restore_engine_trade_state_from_snapshot(
                symbol=symbol,
                broker_symbol=broker_symbol,
                engine=engine,
                positions=positions,
                snapshots_by_ticket=snapshots_by_ticket,
            )
            recovered_actions.append(
                {
                    "symbol": symbol,
                    "broker_symbol": broker_symbol,
                    "status": "engine_recovered",
                    "position_tickets": [
                        getattr(position, "ticket", None) for position in positions
                    ],
                    "pending_intent_file": str(pending_path) if has_pending else None,
                    "active_trade_ticket": (
                        getattr(engine.active_trade, "ticket", None)
                        if engine.active_trade is not None
                        else None
                    ),
                    "pending_intent_loaded": engine.pending_intent is not None,
                    "target_trade_state_restore": restored_state,
                }
            )

        summary = {
            "event": "target_startup_state_recovery",
            "target_namespace": self.target_namespace,
            "symbols_with_positions": symbols_with_positions,
            "symbols_with_pending_intents": symbols_with_pending_intents,
            "engine_symbols": sorted(self.engines),
            "recovered_actions": recovered_actions,
        }
        _append_jsonl(self.action_log, summary)
        self.persist_target_trade_state(reason="startup_recovery")
        return summary

    def _risk_guard(self, intent: dict[str, Any], symbol: str) -> tuple[bool, str, float | None]:
        cfg = load_target_symbol_config(self.base_config, symbol)
        risk_pct = target_risk_cap_pct(intent, cfg)
        if risk_pct is None or risk_pct <= 0:
            return False, "target_risk_pct_unresolved", None
        projection = _target_account_budget_projection(
            mt5=self.mt5,
            base_config=self.base_config,
            symbol_map=self.symbol_map,
            engines=self.engines,
            requested_risk_pct=risk_pct,
            source_symbol=symbol,
        )
        intent_id = str(intent.get("intent_id") or "")
        if intent_id:
            self.last_risk_budget_projection[intent_id] = projection
        action = projection.get("action")
        reason = str(projection.get("reason") or "target_account_drawdown_budget_unresolved")
        if action in {"ALLOW", "REDUCE_RISK"}:
            final_risk = _safe_float(projection.get("after_risk_pct"))
            if final_risk is None or final_risk <= 0:
                return False, "target_account_drawdown_budget_final_risk_unresolved", None
            return True, reason, final_risk
        return False, reason, None

    def _log_target_tick_deferral(
        self,
        *,
        intent_id: str,
        symbol: str,
        broker_symbol: str,
        reason: str,
        tick: Any | None,
        event: str = "market_intent_deferred_target_tick_unavailable",
    ) -> None:
        key = f"{intent_id}:{reason}"
        now = time.monotonic()
        last = self.deferred_intent_log_monotonic.get(key, 0.0)
        if now - last < TARGET_TICK_DEFERRAL_LOG_SECONDS:
            return
        self.deferred_intent_log_monotonic[key] = now
        _append_jsonl(
            self.action_log,
            {
                "event": event,
                "intent_id": intent_id,
                "symbol": symbol,
                "broker_symbol": broker_symbol,
                "reason": reason,
                "target_tick": _jsonable(tick),
                "target_namespace": self.target_namespace,
            },
        )

    def process_intent(self, intent: dict[str, Any]) -> bool:
        """Process one intent.

        Returns True when the bus offset may advance. Returns False for a
        retryable target-side deferral so the intent is not lost.
        """
        intent_id = str(intent.get("intent_id") or "")
        if intent_id and intent_id in self.processed_intent_ids:
            return True
        validate_intent(intent)
        age_seconds = _intent_age_seconds(intent)
        is_reprocessable_failed_retry = (
            bool(intent_id) and intent_id in self.reprocessable_failed_intent_ids
        )
        is_stale_market_recovery = (
            intent.get("intent_type") == MARKET_ENTRY
            and self.max_live_recovery_intent_age_seconds is not None
            and age_seconds > float(self.max_live_recovery_intent_age_seconds)
        )
        if (
            is_stale_market_recovery
            and not is_reprocessable_failed_retry
        ):
            _append_jsonl(
                self.action_log,
                {
                    "event": "market_intent_skipped_outside_live_recovery_window",
                    "intent_id": intent_id,
                    "symbol": intent_symbol(intent),
                    "intent_age_seconds": round(age_seconds, 3),
                    "max_live_recovery_intent_age_seconds": (
                        self.max_live_recovery_intent_age_seconds
                    ),
                    "target_namespace": self.target_namespace,
                },
            )
            self.processed_intent_ids.add(intent_id)
            return True
        if is_reprocessable_failed_retry:
            source_record_retry_state = (
                _source_record_retry_state(intent) if is_stale_market_recovery else {}
            )
            if is_stale_market_recovery:
                source_still_unclosed = bool(source_record_retry_state.get("allow_retry"))
                event_name = (
                    "market_intent_reprocess_failed_retry_skipped_outside_live_recovery_window"
                    if source_still_unclosed
                    else "market_intent_reprocess_failed_retry_skipped_source_not_open"
                )
                reason = (
                    "stale_market_entry_not_opened_late_even_with_unclosed_source_record"
                    if source_still_unclosed
                    else "source_record_not_open_or_liveness_unproven"
                )
                _append_jsonl(
                    self.action_log,
                    {
                        "event": event_name,
                        "intent_id": intent_id,
                        "symbol": intent_symbol(intent),
                        "reason": reason,
                        "intent_age_seconds": round(age_seconds, 3),
                        "max_live_recovery_intent_age_seconds": (
                            self.max_live_recovery_intent_age_seconds
                        ),
                        "source_record_retry_state": source_record_retry_state,
                        "target_namespace": self.target_namespace,
                    },
                )
                self.reprocessable_failed_intent_ids.discard(intent_id)
                self.processed_intent_ids.add(intent_id)
                return True
            _append_jsonl(
                self.action_log,
                {
                    "event": "market_intent_reprocess_failed_retry_started",
                    "intent_id": intent_id,
                    "symbol": intent_symbol(intent),
                    "intent_age_seconds": round(age_seconds, 3),
                    "max_live_recovery_intent_age_seconds": (
                        self.max_live_recovery_intent_age_seconds
                    ),
                    "source_record_retry_state": source_record_retry_state,
                    "target_namespace": self.target_namespace,
                },
            )
            self.reprocessable_failed_intent_ids.discard(intent_id)
        source_namespace = intent_source_namespace(intent)
        if source_namespace == self.target_namespace.lower():
            _append_jsonl(
                self.action_log,
                {
                    "event": "skip_source_is_target",
                    "intent_id": intent_id,
                    "source_namespace": source_namespace,
                    "target_namespace": self.target_namespace,
                },
            )
            self.processed_intent_ids.add(intent_id)
            return True
        if self.source_namespace and source_namespace != self.source_namespace.lower():
            _append_jsonl(
                self.action_log,
                {
                    "event": "skip_unexpected_source_namespace",
                    "intent_id": intent_id,
                    "source_namespace": source_namespace,
                    "expected_source_namespace": self.source_namespace,
                },
            )
            self.processed_intent_ids.add(intent_id)
            return True

        boundary_violations = source_target_boundary_violations(intent)
        if boundary_violations:
            _append_jsonl(
                self.action_log,
                {
                    "event": "intent_source_target_boundary_violation",
                    "intent_id": intent_id,
                    "source_namespace": source_namespace,
                    "target_namespace": self.target_namespace,
                    "boundary_violations": boundary_violations,
                    "reason": "source_broker_truth_not_allowed_in_target_execution_payload",
                },
            )
            self.processed_intent_ids.add(intent_id)
            return True

        symbol = intent_symbol(intent)
        if symbol not in self.symbol_map:
            _append_jsonl(
                self.action_log,
                {
                    "event": "skip_unmapped_symbol",
                    "intent_id": intent_id,
                    "symbol": symbol,
                    "target_namespace": self.target_namespace,
                },
            )
            self.processed_intent_ids.add(intent_id)
            return True

        broker_symbol = self.symbol_map[symbol]
        if intent.get("intent_type") == MARKET_ENTRY:
            tick_ok, tick_reason, target_tick = target_tick_quality(self.mt5, broker_symbol)
            if not tick_ok:
                age_seconds = _intent_age_seconds(intent)
                if age_seconds > MARKET_INTENT_MAX_TARGET_TICK_WAIT_SECONDS:
                    _append_jsonl(
                        self.action_log,
                        {
                            "event": "market_intent_expired_target_tick_unavailable",
                            "intent_id": intent_id,
                            "symbol": symbol,
                            "broker_symbol": broker_symbol,
                            "reason": tick_reason,
                            "intent_age_seconds": round(age_seconds, 3),
                            "target_tick": _jsonable(target_tick),
                            "target_namespace": self.target_namespace,
                        },
                    )
                    self.processed_intent_ids.add(intent_id)
                    return True
                self._log_target_tick_deferral(
                    intent_id=intent_id,
                    symbol=symbol,
                    broker_symbol=broker_symbol,
                    reason=tick_reason,
                    tick=target_tick,
                )
                return False

        ok, reason, risk_pct = self._risk_guard(intent, symbol)
        if not ok:
            _append_jsonl(
                self.action_log,
                {
                    "event": "risk_guard_rejected",
                    "intent_id": intent_id,
                    "symbol": symbol,
                    "reason": reason,
                    "target_risk_budget": self.last_risk_budget_projection.get(intent_id),
                    "target_namespace": self.target_namespace,
                },
            )
            self.processed_intent_ids.add(intent_id)
            return True

        params = intent_to_trade_params(intent)
        context_errors = target_execution_context_errors(params)
        if context_errors:
            _append_jsonl(
                self.action_log,
                {
                    "event": "market_intent_missing_target_execution_context"
                    if intent.get("intent_type") == MARKET_ENTRY
                    else "pending_limit_missing_target_execution_context",
                    "intent_id": intent_id,
                    "symbol": symbol,
                    "broker_symbol": broker_symbol,
                    "reason": "missing_or_unverified_vnext_execution_context",
                    "context_errors": context_errors,
                    "dynamic_context_keys": sorted(
                        (intent.get("dynamic_context") or {}).keys()
                    )
                    if isinstance(intent.get("dynamic_context"), dict)
                    else [],
                    "target_namespace": self.target_namespace,
                },
            )
            self.processed_intent_ids.add(intent_id)
            return True

        engine = self.engine_for(symbol)
        if not self.order_enabled:
            tick = self.mt5.get_tick(broker_symbol)
            _append_jsonl(
                self.action_log,
                {
                    "event": "dry_run_intent_ready",
                    "intent_id": intent_id,
                    "intent_type": intent.get("intent_type"),
                    "symbol": symbol,
                    "broker_symbol": broker_symbol,
                    "risk_pct": risk_pct,
                    "target_risk_budget": self.last_risk_budget_projection.get(intent_id),
                    "target_tick": _jsonable(tick),
                    "target_namespace": self.target_namespace,
                },
            )
            self.processed_intent_ids.add(intent_id)
            return True

        account_balance = float(self.mt5.get_account_balance() or 0.0)
        if intent.get("intent_type") == MARKET_ENTRY:
            deferred_baseline = self.deferred_no_target_position_counts.get(intent_id)
            if deferred_baseline is not None:
                current_positions = len(_positions_for_broker_symbol(self.mt5, broker_symbol))
                if current_positions > deferred_baseline:
                    _append_jsonl(
                        self.action_log,
                        {
                            "event": "market_intent_target_position_detected_before_retry",
                            "intent_id": intent_id,
                            "symbol": symbol,
                            "broker_symbol": broker_symbol,
                            "reason": "target_position_count_increased_after_prior_no_order_return",
                            "baseline_positions": deferred_baseline,
                            "current_positions": current_positions,
                            "target_namespace": self.target_namespace,
                        },
                    )
                    self.deferred_no_target_position_counts.pop(intent_id, None)
                    self.processed_intent_ids.add(intent_id)
                    return True
            target_positions_before = len(_positions_for_broker_symbol(self.mt5, broker_symbol))
            # H6: this script RE-TRANSMITS historical intents to a live broker
            # account and carried no halt check of its own. `engine.open_trade`
            # has one, but it is config-armed and BOTH of its defaults are False
            # (runtime_halt.py:91 and :247), so a follower launched with a config
            # that never mentions runtime_control was unbraked. Check here with
            # the guard armed, so halt coverage is a property of this script
            # rather than of whether a config key was remembered.
            try:
                enforce_runtime_not_halted(
                    action="dual_broker_follower_open_trade",
                    config=self.base_config,
                    context={
                        "intent_id": intent_id,
                        "symbol": symbol,
                        "target_namespace": self.target_namespace,
                        "order_enabled": bool(self.order_enabled),
                    },
                    enabled_default=True,
                )
            except RuntimeHaltError as halt_error:
                _append_jsonl(
                    self.action_log,
                    {
                        "event": "intent_refused_runtime_halt",
                        "intent_id": intent_id,
                        "symbol": symbol,
                        "reason": str(halt_error),
                        "target_namespace": self.target_namespace,
                    },
                )
                return False
            trade_state = engine.open_trade(
                params,
                account_balance=account_balance,
                risk_pct_override=risk_pct,
                kill_zone=(intent.get("context") or {}).get("kill_zone")
                if isinstance(intent.get("context"), dict)
                else None,
                trigger="dual_broker_follower_market",
            )
            if trade_state is None:
                execution_none_reason = execution_engine_none_reason(params)
                execution_none_context = target_execution_failure_context(
                    engine,
                    mt5=self.mt5,
                    broker_symbol=broker_symbol,
                    params=params,
                )
                try:
                    target_positions_after = len(
                        _positions_for_broker_symbol(self.mt5, broker_symbol)
                    )
                except Exception as exc:  # noqa: BLE001
                    target_positions_after = f"probe_failed:{exc}"
                age_seconds = _intent_age_seconds(intent)
                target_position_detected = (
                    isinstance(target_positions_after, int) and target_positions_after > 0
                )
                if (
                    not target_position_detected
                    and age_seconds <= MARKET_INTENT_MAX_TARGET_TICK_WAIT_SECONDS
                ):
                    _append_jsonl(
                        self.action_log,
                        {
                            "event": "market_intent_deferred_no_target_order",
                            "intent_id": intent_id,
                            "symbol": symbol,
                            "broker_symbol": broker_symbol,
                            "reason": execution_none_reason,
                            "intent_age_seconds": round(age_seconds, 3),
                            "max_wait_seconds": MARKET_INTENT_MAX_TARGET_TICK_WAIT_SECONDS,
                            "target_positions_before_symbol": target_positions_before,
                            "target_positions_after_symbol": target_positions_after,
                            "target_risk_budget": self.last_risk_budget_projection.get(intent_id),
                            "target_namespace": self.target_namespace,
                            **execution_none_context,
                        },
                    )
                    self.deferred_no_target_position_counts[intent_id] = min(
                        target_positions_before,
                        self.deferred_no_target_position_counts.get(
                            intent_id, target_positions_before
                        ),
                    )
                    return False
                event_name = (
                    "market_intent_target_position_detected_after_none"
                    if target_position_detected
                    else "market_intent_expired_no_target_order"
                )
                _append_jsonl(
                    self.action_log,
                    {
                        "event": event_name,
                        "intent_id": intent_id,
                        "symbol": symbol,
                        "broker_symbol": broker_symbol,
                        "reason": execution_none_reason,
                        "intent_age_seconds": round(age_seconds, 3),
                        "max_wait_seconds": MARKET_INTENT_MAX_TARGET_TICK_WAIT_SECONDS,
                        "target_positions_before_symbol": target_positions_before,
                        "target_positions_after_symbol": target_positions_after,
                        "target_risk_budget": self.last_risk_budget_projection.get(intent_id),
                        "target_namespace": self.target_namespace,
                        **execution_none_context,
                    },
                )
            else:
                self._remember_active_trade_intent(trade_state, intent_id)
            _append_jsonl(
                self.action_log,
                {
                    "event": "market_intent_processed",
                    "intent_id": intent_id,
                    "symbol": symbol,
                    "order_enabled": True,
                    "risk_pct": risk_pct,
                    "target_risk_budget": self.last_risk_budget_projection.get(intent_id),
                    "result": _jsonable(trade_state),
                    "target_namespace": self.target_namespace,
                },
            )
            self.deferred_no_target_position_counts.pop(intent_id, None)
            self.processed_intent_ids.add(intent_id)
            return True

        if intent.get("intent_type") == PENDING_LIMIT:
            pending = engine.set_limit_intent(
                params,
                account_balance=account_balance,
                risk_pct_override=risk_pct,
                telemetry_context={
                    "source_branch": "dual_broker_execution_follower",
                    "source_intent_id": intent_id,
                    **(intent.get("dynamic_context") or {}),
                },
            )
            if pending is None:
                _append_jsonl(
                    self.action_log,
                    {
                        "event": "pending_limit_intent_not_staged",
                        "intent_id": intent_id,
                        "symbol": symbol,
                        "broker_symbol": broker_symbol,
                        "reason": "execution_engine_returned_none",
                        "target_namespace": self.target_namespace,
                    },
                )
            _append_jsonl(
                self.action_log,
                {
                    "event": "pending_limit_intent_processed",
                    "intent_id": intent_id,
                    "symbol": symbol,
                    "order_enabled": True,
                    "risk_pct": risk_pct,
                    "target_risk_budget": self.last_risk_budget_projection.get(intent_id),
                    "result": _jsonable(pending),
                    "target_namespace": self.target_namespace,
                },
            )
            self.processed_intent_ids.add(intent_id)
            return True

        _append_jsonl(
            self.action_log,
            {
                "event": "unsupported_intent_type",
                "intent_id": intent_id,
                "intent_type": intent.get("intent_type"),
                "target_namespace": self.target_namespace,
            },
        )
        self.processed_intent_ids.add(intent_id)
        return True

    def manage_live_state(self) -> None:
        if not self.order_enabled:
            return
        for symbol, engine in list(self.engines.items()):
            if engine.active_trade is not None:
                status = engine.check_and_manage_trade({})
                if status and status != "monitoring":
                    _append_jsonl(
                        self.action_log,
                        {
                            "event": "active_trade_management",
                            "symbol": symbol,
                            "status": status,
                            "target_namespace": self.target_namespace,
                        },
                    )
            if engine.pending_intent is None:
                continue
            broker_symbol = self.symbol_map.get(symbol, symbol)
            candle = _latest_closed_m15(self.mt5, broker_symbol)
            if not candle:
                continue
            candle_time = str(candle.get("time") or "")
            if candle_time == self.latest_checked_candle.get(symbol):
                continue
            self.latest_checked_candle[symbol] = candle_time
            tick_ok, tick_reason, target_tick = target_tick_quality(self.mt5, broker_symbol)
            if not tick_ok:
                self._log_target_tick_deferral(
                    intent_id=f"pending:{symbol}:{candle_time}",
                    symbol=symbol,
                    broker_symbol=broker_symbol,
                    reason=tick_reason,
                    tick=target_tick,
                    event="pending_limit_deferred_target_tick_unavailable",
                )
                continue
            trade_state = engine.check_limit_fill(
                candle,
                telemetry_context={
                    "source_branch": "dual_broker_execution_follower",
                    "check_context": "target_broker_m15_close",
                    "elapsed_candle_increment": 1,
                    "latest_m15_time_utc": candle_time,
                },
            )
            _append_jsonl(
                self.action_log,
                {
                    "event": "pending_limit_target_candle_check",
                    "symbol": symbol,
                    "broker_symbol": broker_symbol,
                    "candle_time": candle_time,
                    "filled": bool(trade_state),
                    "result": _jsonable(trade_state),
                    "target_namespace": self.target_namespace,
                },
            )


def build_symbol_map(base_config: dict[str, Any]) -> dict[str, str]:
    instruments = base_config.get("instruments")
    if not isinstance(instruments, dict):
        return {}
    mapping: dict[str, str] = {}
    for symbol in sorted(str(item) for item in instruments):
        try:
            cfg = apply_instrument_overrides(base_config, symbol)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("symbol config resolve failed for %s: %s", symbol, exc)
            continue
        market = cfg.get("market") if isinstance(cfg.get("market"), dict) else {}
        mapping[symbol] = str(market.get("mt5_symbol") or symbol)
    return mapping


def dual_broker_architecture_contract(
    base_config: dict[str, Any],
    *,
    target_namespace: str,
    source_namespace: str,
    order_enabled: bool,
) -> dict[str, Any]:
    dual_cfg = (
        base_config.get("dual_broker")
        if isinstance(base_config.get("dual_broker"), dict)
        else {}
    )
    if not dual_cfg:
        return {
            "configured": False,
            "status": "not_configured",
            "errors": [],
        }

    target_authority = (
        dual_cfg.get("target_authority")
        if isinstance(dual_cfg.get("target_authority"), dict)
        else {}
    )
    role = str(dual_cfg.get("role") or "").strip()
    configured_target = str(dual_cfg.get("target_runtime_namespace") or "").strip()
    configured_source = str(dual_cfg.get("source_runtime_namespace") or "").strip()
    runtime_model = str(dual_cfg.get("runtime_model") or "").strip()
    errors: list[str] = []

    if role != "follower_projector_only":
        errors.append(f"dual_broker.role_not_follower_projector_only:{role or 'missing'}")
    if not runtime_model:
        errors.append("dual_broker.runtime_model_missing")
    if configured_target and configured_target != target_namespace:
        errors.append(
            "dual_broker.target_namespace_mismatch:"
            f"configured={configured_target}:runtime={target_namespace}"
        )
    if configured_source and configured_source.lower() != source_namespace.lower():
        errors.append(
            "dual_broker.source_namespace_mismatch:"
            f"configured={configured_source}:runtime={source_namespace}"
        )
    if str(target_authority.get("order_source") or "") != "canonical_trade_intents_only":
        errors.append("dual_broker.target_order_source_not_canonical_intents_only")
    if str(target_authority.get("full_run_agent_fleet") or "") != "forbidden":
        errors.append("dual_broker.target_full_run_agent_fleet_not_forbidden")
    for forbidden_key in (
        "primary_lot_copy",
        "primary_fill_price_copy",
        "primary_cash_pnl_copy",
        "primary_cost_swap_fee_copy",
        "primary_symbol_spec_session_copy",
        "primary_order_deal_position_lifecycle_copy",
    ):
        if str(target_authority.get(forbidden_key) or "") != "forbidden":
            errors.append(f"dual_broker.{forbidden_key}_not_forbidden")
    for required_key in (
        "broker_local_risk_gate",
        "broker_local_lifecycle_management",
        "broker_local_crash_recovery",
    ):
        if str(target_authority.get(required_key) or "") != "required":
            errors.append(f"dual_broker.{required_key}_not_required")
    if order_enabled and not _truthy(dual_cfg.get("intent_bus_enabled")):
        errors.append("dual_broker.intent_bus_disabled_for_order_enabled_follower")

    return {
        "configured": True,
        "status": "passed" if not errors else "failed",
        "architecture_id": dual_cfg.get("architecture_id"),
        "runtime_model": runtime_model,
        "role": role,
        "source_runtime_namespace": configured_source,
        "target_runtime_namespace": configured_target,
        "intent_log_path": dual_cfg.get("intent_log_path"),
        "target_state_path": dual_cfg.get("target_state_path"),
        "action_log_path": dual_cfg.get("action_log_path"),
        "order_enabled": bool(order_enabled),
        "target_authority": target_authority,
        "errors": errors,
    }


def _default_checkpoint_path(namespace: str) -> Path:
    return PROJECT_ROOT / "pipeline_state" / namespace / "dual_broker_execution_follower_checkpoint.json"


def _default_action_log(namespace: str) -> Path:
    return PROJECT_ROOT / "pipeline_state" / namespace / "dual_broker_execution_follower_actions.jsonl"


def _default_target_trade_state_path(namespace: str) -> Path:
    return PROJECT_ROOT / "pipeline_state" / namespace / "dual_broker_target_trade_state.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GTOS dual-broker execution follower")
    parser.add_argument("--mode", choices=["mock", "demo", "live"], default="live")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--runtime-namespace", default=DEFAULT_TARGET_NAMESPACE)
    parser.add_argument("--source-runtime-namespace", default=DEFAULT_SOURCE_NAMESPACE)
    parser.add_argument("--terminal-path", default=DEFAULT_TERMINAL_PATH)
    parser.add_argument("--portable-terminal", action="store_true")
    parser.add_argument("--intent-log", default=None)
    parser.add_argument("--checkpoint-path", default=None)
    parser.add_argument("--action-log", default=None)
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--replay-existing", action="store_true")
    parser.add_argument(
        "--reprocess-failed-intents",
        action="store_true",
        help=(
            "When replaying, allow recent non-filled failures such as stale "
            "target context/tick/no-order outcomes to be re-evaluated. "
            "Successful copies and risk rejections remain terminal."
        ),
    )
    parser.add_argument(
        "--live-recovery-window-seconds",
        type=float,
        default=DEFAULT_LIVE_RECOVERY_WINDOW_SECONDS,
        help=(
            "Maximum age for market-entry intents replayed after a follower "
            "restart. Older market intents are recorded as intentionally "
            "skipped rather than opened late."
        ),
    )
    parser.add_argument("--order-enabled", action="store_true")
    parser.add_argument("--enable-notifications", action="store_true")
    parser.add_argument("--once", action="store_true")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    if not args.enable_notifications:
        _install_notification_suppression()

    os.environ["GTOS_PROFILE"] = args.profile
    os.environ["GTOS_RUNTIME_NAMESPACE"] = args.runtime_namespace
    if args.terminal_path:
        os.environ["GTOS_MT5_TERMINAL_PATH"] = args.terminal_path

    target_namespace = broker_account_namespace({}, args.runtime_namespace) or args.runtime_namespace
    lock_name = f"dual_broker_execution_follower_{target_namespace}"
    acquired, conflict = acquire_single_instance_lock(
        lock_name,
        argv_marker="dual_broker_execution_follower.py",
    )
    if not acquired:
        LOGGER.error("another dual-broker follower is alive at PID %s", conflict)
        return 2

    checkpoint_path = (
        Path(args.checkpoint_path)
        if args.checkpoint_path
        else _default_checkpoint_path(target_namespace)
    )
    action_log = Path(args.action_log) if args.action_log else _default_action_log(target_namespace)

    mt5 = None
    try:
        config_path = Path(args.config)
        profile = resolve_profile(args.profile)
        base_config = load_target_base_config(config_path, profile)
        terminal_path = resolve_mt5_terminal_path(base_config, args.terminal_path)
        terminal_portable = resolve_mt5_portable_mode(
            base_config,
            True if args.portable_terminal else None,
        )
        architecture_contract = dual_broker_architecture_contract(
            base_config,
            target_namespace=target_namespace,
            source_namespace=str(args.source_runtime_namespace or "").strip().lower(),
            order_enabled=bool(args.order_enabled),
        )
        if architecture_contract.get("errors"):
            raise RuntimeError(
                "Dual-broker follower architecture contract failed: "
                f"{architecture_contract['errors']}"
            )
        intent_log = (
            Path(args.intent_log)
            if args.intent_log
            else resolve_intent_log_path(base_config, os.environ.get(INTENT_LOG_ENV_VAR))
        )

        mt5_kwargs = {}
        if args.mode != "mock" and terminal_path:
            mt5_kwargs["terminal_path"] = terminal_path
        if args.mode != "mock" and terminal_portable:
            mt5_kwargs["portable"] = True
        mt5 = create_mt5(args.mode, **mt5_kwargs)
        if not mt5.connect():
            raise RuntimeError("MT5 connect failed")
        account_check = {"status": "skipped_mock_mode"}
        if args.mode != "mock":
            account_check = assert_mt5_account_matches_profile(mt5, base_config)

        symbol_map = build_symbol_map(base_config)
        runtime = FollowerRuntime(
            mt5=mt5,
            base_config=base_config,
            target_namespace=target_namespace,
            source_namespace=str(args.source_runtime_namespace or "").strip().lower(),
            order_enabled=bool(args.order_enabled),
            action_log=action_log,
            symbol_map=symbol_map,
            max_live_recovery_intent_age_seconds=(
                None
                if float(args.live_recovery_window_seconds) <= 0
                else float(args.live_recovery_window_seconds)
            ),
        )
        processed_intent_ids, reprocessable_failed_intent_ids = (
            _intent_recovery_state_from_action_log(
                action_log,
                reprocess_failed_intents=bool(args.reprocess_failed_intents),
            )
        )
        runtime.processed_intent_ids.update(processed_intent_ids)
        runtime.reprocessable_failed_intent_ids.update(reprocessable_failed_intent_ids)
        startup_recovery = runtime.recover_target_state_on_startup()
        checkpoint = _read_json(checkpoint_path)
        offset = int(checkpoint.get("offset") or 0)
        if args.replay_existing:
            offset = 0
        elif not checkpoint and intent_log.exists():
            offset = 0
        if (
            checkpoint
            and args.reprocess_failed_intents
            and args.replay_existing
        ):
            offset = 0
        if (
            not checkpoint
            and not args.replay_existing
            and not args.reprocess_failed_intents
            and intent_log.exists()
        ):
            # Kept only for explicit legacy dry-start behavior. The live
            # watchdog launches with replay/recovery enabled.
            offset = intent_log.stat().st_size

        _append_jsonl(
            action_log,
            {
                "event": "follower_started",
                "mode": args.mode,
                "profile": profile,
                "target_namespace": target_namespace,
                "source_namespace": runtime.source_namespace,
                "terminal_path": terminal_path,
                "terminal_portable": terminal_portable,
                "intent_log": str(intent_log),
                "order_enabled": bool(args.order_enabled),
                "notifications_enabled": bool(args.enable_notifications),
                "account_check": account_check,
                "offset": offset,
                "replay_existing": bool(args.replay_existing),
                "reprocess_failed_intents": bool(args.reprocess_failed_intents),
                "live_recovery_window_seconds": args.live_recovery_window_seconds,
                "dual_broker_architecture_contract": architecture_contract,
                "processed_intent_count_from_action_log": len(runtime.processed_intent_ids),
                "reprocessable_failed_intent_count_from_action_log": len(
                    runtime.reprocessable_failed_intent_ids
                ),
                "intent_outcome_summary_from_action_log": _action_log_intent_outcome_summary(
                    action_log
                ),
                "symbol_count": len(symbol_map),
                "startup_recovery": startup_recovery,
            },
        )

        last_progress = datetime.now(timezone.utc)
        while not _STOP:
            rows, end_offset = read_intents_with_offsets(intent_log, offset)
            if rows:
                last_progress = datetime.now(timezone.utc)
            advanced_offset = offset
            for row, row_end in rows:
                try:
                    consumed = runtime.process_intent(row)
                except Exception as exc:  # noqa: BLE001
                    _append_jsonl(
                        action_log,
                        {
                            "event": "intent_processing_error",
                            "intent_id": row.get("intent_id"),
                            "error": str(exc),
                            "target_namespace": target_namespace,
                        },
                    )
                    consumed = True
                if consumed:
                    advanced_offset = row_end
                    continue
                break
            offset = advanced_offset if rows else end_offset
            runtime.manage_live_state()
            target_trade_state = runtime.persist_target_trade_state(
                reason="live_loop"
            )
            intent_outcome_summary = _action_log_intent_outcome_summary(action_log)
            _write_json(
                checkpoint_path,
                {
                    "offset": offset,
                    "updated_at_utc": _utcnow_iso(),
                    "intent_log": str(intent_log),
                    "target_namespace": target_namespace,
                    "source_namespace": runtime.source_namespace,
                    "order_enabled": bool(args.order_enabled),
                    "processed_intent_count": len(runtime.processed_intent_ids),
                    "intent_outcome_summary": intent_outcome_summary,
                    "engine_symbols": sorted(runtime.engines),
                    "target_trade_state_path": str(runtime._trade_state_path()),
                    "target_active_trade_count": target_trade_state.get(
                        "active_trade_count"
                    ),
                },
            )
            write_daemon_heartbeat(
                lock_name,
                last_progress_at=last_progress,
                extra={
                    "intent_log": str(intent_log),
                    "checkpoint_path": str(checkpoint_path),
                    "action_log": str(action_log),
                    "order_enabled": bool(args.order_enabled),
                    "target_namespace": target_namespace,
                    "source_namespace": runtime.source_namespace,
                },
            )
            if args.once:
                break
            time.sleep(max(0.25, float(args.poll_seconds)))
        return 0
    finally:
        if mt5 is not None:
            try:
                mt5.disconnect()
            except Exception:  # noqa: BLE001
                pass
        release_single_instance_lock(lock_name)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    install_signal_handlers(_request_stop)
    args = parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
