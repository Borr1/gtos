"""Canonical dual-broker intent bus.

The primary live system emits broker-neutral trade intents. Secondary accounts
consume those intents and run their own broker/profile execution checks instead
of copying primary broker fills, lots, or terminal assumptions.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
DEFAULT_INTENT_LOG_PATH = Path("pipeline_state/dual_broker/canonical_trade_intents.jsonl")
INTENT_LOG_ENV_VAR = "GTOS_DUAL_BROKER_INTENT_LOG"
INTENT_ENABLED_ENV_VAR = "GTOS_DUAL_BROKER_INTENT_ENABLED"

MARKET_ENTRY = "market_entry"
PENDING_LIMIT = "pending_limit"
SUPPORTED_INTENT_TYPES = {MARKET_ENTRY, PENDING_LIMIT}

_TRADE_PARAM_KEYS = (
    "direction",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "take_profit_2",
    "take_profit_3",
    "risk_reward_ratio",
)

_CONTEXT_KEY_PREFIXES = ("gtos_vnext_",)
_CONTEXT_KEYS = {
    "decision_spread_value_source_safe",
    "decision_spread_unit",
    "pending_created_time_utc",
    "pending_candles_elapsed",
    "candidate_id",
    "origin_family",
    "route_session",
    "utc_hour_bucket",
    "source_window_complete",
    "source_path_feature_status",
    "live_generation_status",
}

_MISSING = object()

_SELECTED_CELL_VERIFIED_COMMISSION_STATUS = (
    "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP"
)
_SELECTED_CELL_GAP_COMMISSION_STATUS = (
    "SELECTED_CELL_RISK_LEDGER_HAS_UNRESOLVED_COST_OR_GEOMETRY_GAP"
)
_NON_FATAL_PROJECTION_UNRESOLVED_REASONS = {
    "condition_challenger_cell_join_missing_for_broader_origin_allowlist_entry",
}

_VNEXT_RISK_CONTEXT_KEYS = (
    "gtos_vnext_selected_cell_risk_pct",
    "gtos_vnext_selected_cell_risk_cell_id",
    "gtos_vnext_selected_cell_risk_decision_basis",
    "gtos_vnext_selected_cell_risk_unresolved_reasons",
    "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons",
    "gtos_vnext_selected_cell_risk_selected_policy",
    "gtos_vnext_selected_cell_risk_source_policy",
    "gtos_vnext_selected_cell_risk_policy_identity_status",
)

_VNEXT_PROJECTION_REQUIRED_KEYS = (
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

PRIMARY_ORDER_SOURCE_REFERENCE_ALLOWED_KEYS = frozenset({"record_path"})

PRIMARY_ORDER_TARGET_FORBIDDEN_KEYS = frozenset(
    {
        "broker_cash_risk_per_lot",
        "broker_pending_order_created",
        "cash_pnl",
        "commission",
        "contract_size",
        "cost",
        "deal_ticket",
        "entry_deal_ticket",
        "entry_order_retcode",
        "entry_order_ticket",
        "entry_price",
        "executed_entry_price",
        "fee",
        "fill_price",
        "initial_volume",
        "lifecycle",
        "lot",
        "lots",
        "margin",
        "mt5_order_ticket",
        "native_pending_order_type",
        "order_ticket",
        "pending_order_mode",
        "pnl",
        "position_ticket",
        "profit",
        "session",
        "spec",
        "spread",
        "swap",
        "ticket",
        "tick_size",
        "tick_value",
        "volume",
    }
)

PRIMARY_ORDER_TARGET_FORBIDDEN_SUBSTRINGS = (
    "cash",
    "commission",
    "contract",
    "cost",
    "deal",
    "fee",
    "fill",
    "lifecycle",
    "lot",
    "margin",
    "order",
    "pnl",
    "position",
    "profit",
    "session",
    "spec",
    "spread",
    "swap",
    "ticket",
    "volume",
)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _present(value: Any, *, allow_empty: bool = False) -> bool:
    if value is _MISSING or value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if not allow_empty and isinstance(value, (list, tuple, set, dict)) and not value:
        return False
    return True


def _put_if_present(
    context: dict[str, Any],
    key: str,
    value: Any,
    *,
    allow_empty: bool = False,
) -> None:
    if _present(value, allow_empty=allow_empty):
        context[key] = _jsonable(value)


def _get_nested(payload: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return _MISSING
        if key not in current:
            return _MISSING
        current = current[key]
    return current


def _nested_dict(payload: dict[str, Any], path: tuple[str, ...]) -> dict[str, Any] | None:
    value = _get_nested(payload, path)
    return value if isinstance(value, dict) else None


def _dicts_from_paths(
    payload: dict[str, Any],
    paths: tuple[tuple[str, ...], ...],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        row = _nested_dict(payload, path)
        if row is not None:
            rows.append(row)
    return rows


def _first_from_dicts(
    rows: list[dict[str, Any]],
    *keys: str,
    allow_empty: bool = False,
) -> Any:
    for row in rows:
        for key in keys:
            if key in row and _present(row.get(key), allow_empty=allow_empty):
                return row.get(key)
    return _MISSING


def _normalized_reasons(value: Any) -> list[str]:
    if value is _MISSING or value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def sanitize_primary_order_for_target_contract(
    primary_order: dict[str, Any] | None,
) -> dict[str, Any]:
    """Keep only source-reference fields safe for target-broker consumption.

    The canonical intent bus may reference a source trade-record path so the
    follower can fail closed on stale retry attempts. It must not transport
    redacted_account fills, lots, cash/cost fields, broker specs, or lifecycle truth
    into the FTMO target namespace.
    """
    if not isinstance(primary_order, dict):
        return {}
    sanitized: dict[str, Any] = {}
    for key in sorted(PRIMARY_ORDER_SOURCE_REFERENCE_ALLOWED_KEYS):
        value = primary_order.get(key)
        if _present(value):
            sanitized[key] = _jsonable(value)
    if sanitized:
        sanitized["source_reference_policy"] = (
            "source_path_reference_only_no_target_broker_truth"
        )
    return sanitized


def source_target_boundary_violations(intent: dict[str, Any]) -> list[str]:
    """Return source-to-target no-copy violations visible in an intent row."""
    violations: list[str] = []
    primary_order = intent.get("primary_order")
    if isinstance(primary_order, dict):
        for key in sorted(primary_order):
            normalized = str(key).strip().lower()
            if normalized in PRIMARY_ORDER_SOURCE_REFERENCE_ALLOWED_KEYS:
                continue
            if normalized == "source_reference_policy":
                continue
            if normalized in PRIMARY_ORDER_TARGET_FORBIDDEN_KEYS or any(
                token in normalized
                for token in PRIMARY_ORDER_TARGET_FORBIDDEN_SUBSTRINGS
            ):
                violations.append(f"primary_order_forbidden_source_field:{key}")
            else:
                violations.append(f"primary_order_unapproved_source_field:{key}")
    elif primary_order not in (None, ""):
        violations.append("primary_order_not_object")

    risk = intent.get("risk") if isinstance(intent.get("risk"), dict) else {}
    if str(risk.get("risk_instruction") or "") != (
        "target_account_recompute_from_profile_and_current_broker_geometry"
    ):
        violations.append("risk_instruction_not_target_recompute")

    contract = (
        intent.get("target_execution_contract")
        if isinstance(intent.get("target_execution_contract"), dict)
        else {}
    )
    required_contract = {
        "market_entry": "use_target_current_tick_not_source_fill",
        "pending_limit": (
            "target_account_polls_target_broker_candles_then_uses_target_tick_on_touch"
        ),
        "lot_sizing": "target_account_recomputes_lots_from_target_contract_geometry",
    }
    for key, expected in required_contract.items():
        if contract.get(key) != expected:
            violations.append(f"target_execution_contract_mismatch:{key}")
    return violations


def _copy_flat_vnext_context(context: dict[str, Any], *rows: dict[str, Any]) -> None:
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key, value in row.items():
            key_text = str(key)
            if key_text.startswith(_CONTEXT_KEY_PREFIXES):
                _put_if_present(context, key_text, value, allow_empty=True)


def _extract_vnext_projection_context(
    record: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    """Recover execution-critical vNext context from a full trade record.

    Filled trade records can write MT5 fill details before the final vNext
    production proof sections settle. The dual-broker bridge must project the
    complete primary intent, not just the fill telemetry object.
    """
    context: dict[str, Any] = {}
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    limit_intent = (
        record.get("limit_intent")
        if isinstance(record.get("limit_intent"), dict)
        else {}
    )
    pending_limit = (
        record.get("pending_limit")
        if isinstance(record.get("pending_limit"), dict)
        else {}
    )
    instrumentation = (
        record.get("instrumentation")
        if isinstance(record.get("instrumentation"), dict)
        else {}
    )
    _copy_flat_vnext_context(
        context,
        metadata,
        instrumentation,
        execution,
        limit_intent,
        pending_limit,
        source,
    )

    dynamic_packets = _dicts_from_paths(
        record,
        (
            ("decision_pipeline", "gtos_vnext_moonshot_dynamic_execution"),
            ("execution", "gtos_vnext_moonshot_dynamic_execution"),
            ("limit_intent", "gtos_vnext_moonshot_dynamic_execution"),
            ("pending_limit", "gtos_vnext_moonshot_dynamic_execution"),
            ("gtos_vnext_moonshot_dynamic_execution",),
        ),
    )
    source_events = _dicts_from_paths(
        record,
        (
            ("decision_pipeline", "gtos_vnext_moonshot_dynamic_execution", "source_event"),
            ("execution", "gtos_vnext_moonshot_dynamic_execution", "source_event"),
            ("limit_intent", "gtos_vnext_moonshot_dynamic_execution", "source_event"),
            ("pending_limit", "gtos_vnext_moonshot_dynamic_execution", "source_event"),
            ("gtos_vnext_moonshot_dynamic_execution", "source_event"),
        ),
    )
    risk_packets = [
        *source_events,
        *_dicts_from_paths(
            record,
            (
                ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "selected_cell_risk_proof"),
                ("decision_pipeline", "gtos_vnext_replacement_monitoring", "source_capture_completeness", "selected_cell_risk"),
                ("decision_pipeline", "gtos_vnext_executable_geometry_repair", "selected_cell_risk_check"),
                ("execution", "gtos_vnext_candidate_intelligence_packet", "selected_cell_risk_proof"),
                ("limit_intent", "gtos_vnext_candidate_intelligence_packet", "selected_cell_risk_proof"),
            ),
        ),
    ]

    dynamic_key_map = {
        "gtos_vnext_dynamic_policy_selected": ("selected_policy",),
        "gtos_vnext_execution_policy_id": (
            "execution_policy_id",
            "selected_cell_risk_execution_policy_id",
        ),
        "gtos_vnext_dynamic_policy_applied": ("applied",),
        "gtos_vnext_dynamic_policy_replaced_policy": ("replaced_policy",),
        "gtos_vnext_dynamic_policy_candidate_action": ("candidate_action",),
        "gtos_vnext_dynamic_policy_decision_status": ("decision_status",),
        "gtos_vnext_dynamic_policy_source_quality_action": ("source_quality_action",),
        "gtos_vnext_dynamic_policy_exit_management_action": ("exit_management_action",),
        "gtos_vnext_dynamic_policy_prop_action": ("prop_action",),
        "gtos_vnext_dynamic_policy_fixed_target_role": ("fixed_target_role",),
    }
    for target_key, source_keys in dynamic_key_map.items():
        _put_if_present(context, target_key, _first_from_dicts(dynamic_packets, *source_keys))

    risk_key_map = {
        "gtos_vnext_selected_cell_risk_pct": ("selected_cell_risk_pct", "risk_pct"),
        "gtos_vnext_selected_cell_risk_cell_id": ("selected_cell_risk_cell_id", "cell_id"),
        "gtos_vnext_selected_cell_risk_decision_basis": (
            "selected_cell_risk_decision_basis",
            "decision_basis",
        ),
        "gtos_vnext_selected_cell_risk_status": ("selected_cell_risk_status", "status"),
        "gtos_vnext_selected_cell_risk_selected_policy": (
            "selected_cell_risk_selected_policy",
            "selected_policy",
        ),
        "gtos_vnext_selected_cell_risk_source_policy": (
            "selected_cell_risk_source_policy",
            "source_policy",
        ),
        "gtos_vnext_selected_cell_risk_policy_identity_status": (
            "selected_cell_risk_policy_identity_status",
            "policy_identity_status",
        ),
        "gtos_vnext_selected_cell_risk_unresolved_reasons": (
            "selected_cell_risk_unresolved_reasons",
            "unresolved_reasons",
        ),
        "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons": (
            "selected_cell_risk_execution_critical_unresolved_reasons",
        ),
    }
    for target_key, source_keys in risk_key_map.items():
        allow_empty = target_key.endswith("_unresolved_reasons")
        _put_if_present(
            context,
            target_key,
            _first_from_dicts(risk_packets, *source_keys, allow_empty=allow_empty),
            allow_empty=allow_empty,
        )

    if "gtos_vnext_execution_policy_id" not in context:
        _put_if_present(
            context,
            "gtos_vnext_execution_policy_id",
            _first_from_dicts(risk_packets, "selected_cell_risk_execution_policy_id"),
        )
    if "gtos_vnext_selector_row_id" not in context:
        _put_if_present(
            context,
            "gtos_vnext_selector_row_id",
            context.get("gtos_vnext_selected_cell_risk_cell_id"),
        )

    selected_allowed = _first_from_dicts(
        risk_packets,
        "selected_cell_risk_allowed",
        "risk_allowed",
    )
    critical_reasons = _normalized_reasons(
        context.get("gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons")
    )
    if "gtos_vnext_commission_model_status" not in context and selected_allowed is not _MISSING:
        context["gtos_vnext_commission_model_status"] = (
            _SELECTED_CELL_VERIFIED_COMMISSION_STATUS
            if selected_allowed is True and not critical_reasons
            else _SELECTED_CELL_GAP_COMMISSION_STATUS
        )
    if (
        "gtos_vnext_production_execution_path" not in context
        and (
            selected_allowed is True
            or (
                context.get("gtos_vnext_selected_cell_risk_cell_id")
                and context.get("gtos_vnext_selected_cell_risk_pct") is not None
            )
        )
    ):
        context["gtos_vnext_production_execution_path"] = True

    trigger_packets = _dicts_from_paths(
        record,
        (
            ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "dynamic_policy", "dynamic_trigger_final_pullback"),
            ("decision_pipeline", "gtos_vnext_candidate_intelligence_packet", "dynamic_trigger_final_pullback"),
            ("decision_pipeline", "gtos_vnext_moonshot_dynamic_execution", "router_record", "dynamic_trigger_final_pullback"),
            ("execution", "gtos_vnext_moonshot_dynamic_execution", "router_record", "dynamic_trigger_final_pullback"),
            ("limit_intent", "gtos_vnext_moonshot_dynamic_execution", "router_record", "dynamic_trigger_final_pullback"),
            ("pending_limit", "gtos_vnext_moonshot_dynamic_execution", "router_record", "dynamic_trigger_final_pullback"),
        ),
    )
    selected_policy = str(
        context.get("gtos_vnext_dynamic_policy_selected")
        or _first_from_dicts(trigger_packets, "selected_policy")
        or ""
    ).strip().lower()
    if selected_policy == "be_after_trigger":
        _put_if_present(
            context,
            "gtos_vnext_dynamic_be_trigger_r",
            _first_from_dicts(trigger_packets, "be_trigger_r"),
        )
        _put_if_present(
            context,
            "gtos_vnext_dynamic_final_target_r",
            _first_from_dicts(
                trigger_packets,
                "be_final_target_r",
                "final_target_r",
                "repaired_dynamic_final_target_r",
            ),
        )
    elif selected_policy == "partial_be_runner":
        _put_if_present(
            context,
            "gtos_vnext_dynamic_be_trigger_r",
            _first_from_dicts(trigger_packets, "partial_trigger_r"),
        )
        _put_if_present(
            context,
            "gtos_vnext_dynamic_final_target_r",
            _first_from_dicts(
                trigger_packets,
                "partial_final_target_r",
                "repaired_dynamic_final_target_r",
            ),
        )
        _put_if_present(
            context,
            "gtos_vnext_dynamic_partial_close_ratio",
            _first_from_dicts(trigger_packets, "partial_close_ratio"),
        )
    elif selected_policy == "trailing_runner":
        _put_if_present(
            context,
            "gtos_vnext_dynamic_be_trigger_r",
            _first_from_dicts(trigger_packets, "trailing_trigger_r"),
        )
        _put_if_present(
            context,
            "gtos_vnext_dynamic_final_target_r",
            _first_from_dicts(
                trigger_packets,
                "trailing_final_target_r",
                "repaired_dynamic_final_target_r",
            ),
        )
        _put_if_present(
            context,
            "gtos_vnext_dynamic_trail_gap_r",
            _first_from_dicts(trigger_packets, "trailing_gap_r"),
        )
    elif selected_policy == "momentum_exhaustion":
        _put_if_present(
            context,
            "gtos_vnext_dynamic_be_trigger_r",
            _first_from_dicts(trigger_packets, "momentum_trigger_r"),
        )
        _put_if_present(
            context,
            "gtos_vnext_dynamic_final_target_r",
            _first_from_dicts(
                trigger_packets,
                "momentum_final_target_r",
                "repaired_dynamic_final_target_r",
            ),
        )
        _put_if_present(
            context,
            "gtos_vnext_dynamic_momentum_pullback_r",
            _first_from_dicts(trigger_packets, "momentum_pullback_r"),
        )
    elif selected_policy == "time_stop":
        _put_if_present(
            context,
            "gtos_vnext_dynamic_final_target_r",
            _first_from_dicts(
                trigger_packets,
                "time_stop_target_r",
                "target_r",
                "repaired_dynamic_final_target_r",
            ),
        )
        _put_if_present(
            context,
            "gtos_vnext_dynamic_time_stop_bars",
            _first_from_dicts(trigger_packets, "time_stop_bars"),
        )

    return context


def vnext_projection_context_errors(context: dict[str, Any]) -> list[str]:
    if not any(key in context for key in _VNEXT_RISK_CONTEXT_KEYS) and not context.get(
        "gtos_vnext_dynamic_policy_selected"
    ):
        return []
    missing = [
        key
        for key in _VNEXT_PROJECTION_REQUIRED_KEYS
        if not _present(context.get(key), allow_empty=True)
    ]
    if missing:
        return [f"missing:{key}" for key in missing]
    if not _truthy(context.get("gtos_vnext_dynamic_policy_applied")):
        return ["gtos_vnext_dynamic_policy_not_applied"]
    unresolved = _normalized_reasons(
        context.get("gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons")
    )
    if not unresolved:
        unresolved = _normalized_reasons(
            context.get("gtos_vnext_selected_cell_risk_unresolved_reasons")
        )
    unresolved = [
        reason
        for reason in unresolved
        if reason not in _NON_FATAL_PROJECTION_UNRESOLVED_REASONS
    ]
    if unresolved:
        return [f"selected_cell_unresolved:{','.join(sorted(unresolved))}"]
    if (
        str(context.get("gtos_vnext_commission_model_status") or "")
        != _SELECTED_CELL_VERIFIED_COMMISSION_STATUS
    ):
        return ["selected_cell_commission_status_not_verified"]
    return []


def trade_record_projection_skip_reasons(record: dict[str, Any]) -> list[str]:
    """Explain why a trade record cannot be projected into an intent."""

    if _record_has_terminal_exit(record):
        return ["terminal_exit_record"]

    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    pending = (
        record.get("limit_intent")
        if isinstance(record.get("limit_intent"), dict)
        else record.get("pending_limit")
        if isinstance(record.get("pending_limit"), dict)
        else {}
    )
    execution_filled = bool(execution) and _execution_is_filled_entry_source(execution)
    pending_open = bool(pending) and _pending_is_open_entry_source(pending)
    source = execution if execution_filled else pending if pending_open else {}
    if not source:
        return ["no_filled_execution_or_open_pending_source"]

    symbol = str(
        metadata.get("symbol")
        or record.get("symbol")
        or source.get("symbol")
        or ""
    ).strip()
    trade_id = str(
        source.get("trade_id")
        or metadata.get("trade_id")
        or record.get("trade_id")
        or ""
    ).strip()
    direction = source.get("direction") or record.get("direction") or metadata.get("side")
    entry_price = (
        source.get("requested_limit_price")
        or source.get("entry_price")
        or source.get("executed_entry_price")
        or source.get("limit_price")
        or record.get("entry_price")
    )
    stop_loss = source.get("stop_loss") or record.get("stop_loss")
    take_profit_1 = source.get("take_profit_1") or record.get("take_profit_1")
    missing = [
        name
        for name, value in (
            ("symbol", symbol),
            ("trade_id", trade_id),
            ("direction", direction),
            ("entry_price", entry_price),
            ("stop_loss", stop_loss),
            ("take_profit_1", take_profit_1),
        )
        if not _present(value)
    ]
    if missing:
        return [f"missing_source_fields:{','.join(missing)}"]

    telemetry_context = dict(source)
    telemetry_context.update(_extract_vnext_projection_context(record, source))
    return vnext_projection_context_errors(telemetry_context)


def intent_bus_enabled(config: dict[str, Any] | None = None) -> bool:
    env_value = os.environ.get(INTENT_ENABLED_ENV_VAR)
    if env_value is not None:
        return _truthy(env_value)
    cfg = config or {}
    dual_cfg = cfg.get("dual_broker") if isinstance(cfg.get("dual_broker"), dict) else {}
    return _truthy(dual_cfg.get("intent_bus_enabled", False))


def resolve_intent_log_path(
    config: dict[str, Any] | None = None,
    explicit: str | Path | None = None,
) -> Path:
    if explicit:
        return Path(explicit)
    env_path = os.environ.get(INTENT_LOG_ENV_VAR, "").strip()
    if env_path:
        return Path(env_path)
    cfg = config or {}
    dual_cfg = cfg.get("dual_broker") if isinstance(cfg.get("dual_broker"), dict) else {}
    configured = dual_cfg.get("intent_log_path") if isinstance(dual_cfg, dict) else None
    if configured:
        return Path(str(configured))
    return DEFAULT_INTENT_LOG_PATH


def _canonical_identity_payload(intent: dict[str, Any]) -> dict[str, Any]:
    trade = intent.get("trade") if isinstance(intent.get("trade"), dict) else {}
    source = intent.get("source") if isinstance(intent.get("source"), dict) else {}
    dynamic = intent.get("dynamic_context") if isinstance(intent.get("dynamic_context"), dict) else {}
    return {
        "schema_version": intent.get("schema_version"),
        "intent_type": intent.get("intent_type"),
        "source_namespace": source.get("runtime_namespace"),
        "source_symbol": source.get("symbol"),
        "source_trade_id": source.get("trade_id"),
        "source_candidate_id": source.get("candidate_id"),
        "direction": trade.get("direction"),
        "dynamic_policy": dynamic.get("gtos_vnext_dynamic_policy_selected"),
        "execution_policy_id": dynamic.get("gtos_vnext_execution_policy_id"),
    }


def canonical_intent_id(intent: dict[str, Any]) -> str:
    payload = _jsonable(_canonical_identity_payload(intent))
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _normalized_source_trade_id(value: Any) -> str:
    text = str(value or "").strip()
    if text.startswith("lim_filled_"):
        return f"lim_{text[len('lim_filled_'):]}"
    return text


def _source_lifecycle_key(intent: dict[str, Any]) -> tuple[Any, ...] | None:
    source = intent.get("source") if isinstance(intent.get("source"), dict) else {}
    trade = intent.get("trade") if isinstance(intent.get("trade"), dict) else {}
    primary_order = (
        intent.get("primary_order")
        if isinstance(intent.get("primary_order"), dict)
        else {}
    )
    record_path = str(primary_order.get("record_path") or "").strip().lower()
    if record_path:
        return (
            "record_path",
            source.get("runtime_namespace"),
            record_path,
            trade.get("direction"),
        )
    source_trade_id = _normalized_source_trade_id(source.get("trade_id"))
    candidate_or_trade = source.get("candidate_id") or source_trade_id
    if not (
        source.get("runtime_namespace")
        and source.get("symbol")
        and candidate_or_trade
        and trade.get("direction")
    ):
        return None
    return (
        "source_lifecycle",
        source.get("runtime_namespace"),
        source.get("symbol"),
        candidate_or_trade,
        trade.get("direction"),
    )


def _intent_dedupe_keys(intent: dict[str, Any]) -> set[str]:
    # repair/replay cannot duplicate the same source trade
    keys: set[str] = set()
    intent_id = intent.get("intent_id")
    if intent_id:
        keys.add(f"intent_id:{intent_id}")
    try:
        keys.add(f"canonical_id:{canonical_intent_id(intent)}")
    except Exception:  # noqa: BLE001 - malformed historical rows are ignored
        pass
    lifecycle_key = _source_lifecycle_key(intent)
    if lifecycle_key is not None:
        encoded = json.dumps(_jsonable(lifecycle_key), sort_keys=True, ensure_ascii=True)
        keys.add(f"source_lifecycle:{encoded}")
    return keys


@contextlib.contextmanager
def _file_lock(lock_path: Path, timeout_seconds: float = 5.0) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+b") as fh:
        if fh.tell() == 0:
            fh.write(b"\0")
            fh.flush()
        fh.seek(0)
        if os.name == "nt":
            import msvcrt

            deadline = time.monotonic() + timeout_seconds
            while True:
                try:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Timed out acquiring {lock_path}")
                    time.sleep(0.05)
            try:
                yield
            finally:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            return

        try:
            import fcntl  # type: ignore[import-not-found]
        except ImportError:
            yield
            return

        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out acquiring {lock_path}")
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _existing_intent_dedupe_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            seen.update(_intent_dedupe_keys(row))
    return seen


def append_intent(
    intent: dict[str, Any],
    path: str | Path | None = None,
    *,
    dedupe: bool = True,
) -> dict[str, Any]:
    target = Path(path) if path is not None else DEFAULT_INTENT_LOG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _jsonable(dict(intent))
    payload["primary_order"] = sanitize_primary_order_for_target_contract(
        payload.get("primary_order") if isinstance(payload.get("primary_order"), dict) else None
    )
    payload.setdefault("schema_version", SCHEMA_VERSION)
    payload.setdefault("recorded_at_utc", _utcnow_iso())
    payload.setdefault("intent_id", canonical_intent_id(payload))
    lock_path = target.with_suffix(target.suffix + ".lock")

    with _file_lock(lock_path):
        if dedupe and _intent_dedupe_keys(payload) & _existing_intent_dedupe_keys(target):
            return {
                "status": "duplicate",
                "intent_id": payload["intent_id"],
                "path": str(target),
            }
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")

    return {
        "status": "appended",
        "intent_id": payload["intent_id"],
        "path": str(target),
    }


def read_intents_from_offset(
    path: str | Path,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    target = Path(path)
    if not target.exists():
        return [], 0
    size = target.stat().st_size
    if offset < 0 or offset > size:
        offset = 0
    rows: list[dict[str, Any]] = []
    with target.open("rb") as fh:
        fh.seek(offset)
        for raw_line in fh:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("dual broker intent bus: malformed row skipped")
                continue
            rows.append(row)
        end_offset = fh.tell()
    return rows, end_offset


def _dynamic_context(
    trade_params: dict[str, Any],
    telemetry_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context: dict[str, Any] = {}
    merged = {}
    merged.update(telemetry_context or {})
    merged.update(trade_params or {})
    for key, value in merged.items():
        key_text = str(key)
        if key_text in _CONTEXT_KEYS or key_text.startswith(_CONTEXT_KEY_PREFIXES):
            context[key_text] = _jsonable(value)
    return context


def _trade_payload(trade_params: dict[str, Any]) -> dict[str, Any]:
    payload = {key: _jsonable(trade_params.get(key)) for key in _TRADE_PARAM_KEYS}
    for key in ("entry_price", "stop_loss", "take_profit_1", "take_profit_2", "take_profit_3", "risk_reward_ratio"):
        numeric = _safe_float(payload.get(key))
        if numeric is not None:
            payload[key] = numeric
    return payload


def validate_intent(intent: dict[str, Any]) -> None:
    if intent.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported dual-broker intent schema_version")
    if intent.get("intent_type") not in SUPPORTED_INTENT_TYPES:
        raise ValueError(f"Unsupported dual-broker intent_type={intent.get('intent_type')!r}")
    source = intent.get("source")
    trade = intent.get("trade")
    if not isinstance(source, dict) or not isinstance(trade, dict):
        raise ValueError("Dual-broker intent requires source and trade objects")
    for key in ("runtime_namespace", "symbol", "trade_id"):
        if not source.get(key):
            raise ValueError(f"Dual-broker intent source missing {key}")
    for key in ("direction", "entry_price", "stop_loss", "take_profit_1"):
        if trade.get(key) in (None, ""):
            raise ValueError(f"Dual-broker intent trade missing {key}")
    if str(trade.get("direction")).upper() not in {"LONG", "SHORT"}:
        raise ValueError("Dual-broker intent direction must be LONG or SHORT")


def build_intent_from_execution_inputs(
    *,
    intent_type: str,
    source_profile: str | None,
    source_runtime_namespace: str | None,
    source_symbol: str,
    source_mt5_symbol: str | None,
    trade_params: dict[str, Any],
    source_trade_id: str,
    candidate_id: str | None = None,
    effective_risk_pct: float | None = None,
    kill_zone: str | None = None,
    trigger: str | None = None,
    telemetry_context: dict[str, Any] | None = None,
    primary_order: dict[str, Any] | None = None,
) -> dict[str, Any]:
    intent = {
        "schema_version": SCHEMA_VERSION,
        "intent_type": intent_type,
        "recorded_at_utc": _utcnow_iso(),
        "source": {
            "profile": source_profile,
            "runtime_namespace": source_runtime_namespace,
            "symbol": source_symbol,
            "mt5_symbol": source_mt5_symbol or source_symbol,
            "trade_id": source_trade_id,
            "candidate_id": candidate_id,
        },
        "trade": _trade_payload(trade_params),
        "risk": {
            "effective_risk_pct_cap": effective_risk_pct,
            "risk_instruction": "target_account_recompute_from_profile_and_current_broker_geometry",
        },
        "context": {
            "kill_zone": kill_zone,
            "trigger": trigger,
        },
        "dynamic_context": _dynamic_context(trade_params, telemetry_context),
        "primary_order": sanitize_primary_order_for_target_contract(primary_order),
        "target_execution_contract": {
            "market_entry": "use_target_current_tick_not_source_fill",
            "pending_limit": "target_account_polls_target_broker_candles_then_uses_target_tick_on_touch",
            "lot_sizing": "target_account_recomputes_lots_from_target_contract_geometry",
            "notifications": "secondary_follower_suppressed_by_default",
        },
    }
    intent["intent_id"] = canonical_intent_id(intent)
    validate_intent(intent)
    return intent


def intent_to_trade_params(intent: dict[str, Any]) -> dict[str, Any]:
    validate_intent(intent)
    trade = intent["trade"]
    dynamic_context = intent.get("dynamic_context")
    params = {
        "direction": trade["direction"],
        "entry_price": float(trade["entry_price"]),
        "stop_loss": float(trade["stop_loss"]),
        "take_profit_1": float(trade["take_profit_1"]),
        "take_profit_2": float(trade.get("take_profit_2") or 0.0),
        "take_profit_3": float(trade.get("take_profit_3") or 0.0),
        "risk_reward_ratio": float(trade.get("risk_reward_ratio") or 1.5),
    }
    if isinstance(dynamic_context, dict):
        params.update(dynamic_context)
    return params


def _record_has_terminal_exit(record: dict[str, Any]) -> bool:
    exit_data = record.get("exit") if isinstance(record.get("exit"), dict) else {}
    if not exit_data:
        return False
    terminal_keys = {
        "exit_reason",
        "exit_type",
        "close_time",
        "close_time_utc",
        "closed_at_utc",
        "realized_R",
        "actual_r",
        "broker_close_state",
        "close_deal_ticket",
    }
    return any(exit_data.get(key) not in (None, "") for key in terminal_keys)


def _execution_is_filled_entry_source(execution: dict[str, Any]) -> bool:
    fill_state = str(
        execution.get("broker_fill_state") or execution.get("fill_state") or ""
    ).strip().lower()
    if fill_state not in {"filled", "order_filled", "done"}:
        return False
    fill_evidence = (
        execution.get("fill_time_utc"),
        execution.get("entry_deal_ticket"),
        execution.get("entry_order_ticket"),
        execution.get("position_ticket"),
        execution.get("ticket"),
    )
    return any(value not in (None, "", 0, "0") for value in fill_evidence)


def _pending_is_open_entry_source(pending: dict[str, Any]) -> bool:
    terminal_fields = (
        pending.get("terminal_state"),
        pending.get("terminal_reason"),
        pending.get("terminal_outcome"),
    )
    if any(value not in (None, "") for value in terminal_fields):
        return False
    broker_fill_state = str(pending.get("broker_fill_state") or "").strip().lower()
    if broker_fill_state and broker_fill_state not in {"pending", "active", "placed"}:
        return False
    return True


def build_intent_from_trade_record(
    record: dict[str, Any],
    *,
    record_path: str | Path,
    source_profile: str | None,
    source_runtime_namespace: str | None,
) -> dict[str, Any] | None:
    """Best-effort projection from a saved trade record.

    This is intentionally conservative. If the record does not expose a clear
    primary execution or pending intent, return None instead of guessing.
    """
    if _record_has_terminal_exit(record):
        return None

    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    pending = (
        record.get("limit_intent")
        if isinstance(record.get("limit_intent"), dict)
        else record.get("pending_limit")
        if isinstance(record.get("pending_limit"), dict)
        else {}
    )
    execution_filled = bool(execution) and _execution_is_filled_entry_source(execution)
    pending_open = bool(pending) and _pending_is_open_entry_source(pending)
    source = execution if execution_filled else pending if pending_open else {}
    if not source:
        return None

    symbol = str(
        metadata.get("symbol")
        or record.get("symbol")
        or source.get("symbol")
        or ""
    ).strip()
    trade_id = str(
        source.get("trade_id")
        or metadata.get("trade_id")
        or record.get("trade_id")
        or ""
    ).strip()
    direction = source.get("direction") or record.get("direction") or metadata.get("side")
    entry_price = (
        source.get("requested_limit_price")
        or source.get("entry_price")
        or source.get("executed_entry_price")
        or source.get("limit_price")
        or record.get("entry_price")
    )
    stop_loss = source.get("stop_loss") or record.get("stop_loss")
    take_profit_1 = source.get("take_profit_1") or record.get("take_profit_1")
    if not all((symbol, trade_id, direction, entry_price, stop_loss, take_profit_1)):
        return None

    intent_type = MARKET_ENTRY if execution_filled else PENDING_LIMIT
    trade_params = {
        "direction": direction,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit_1": take_profit_1,
        "take_profit_2": source.get("take_profit_2"),
        "take_profit_3": source.get("take_profit_3"),
        "risk_reward_ratio": source.get("risk_reward_ratio") or 1.5,
    }
    telemetry_context = dict(source)
    telemetry_context.update(_extract_vnext_projection_context(record, source))
    if vnext_projection_context_errors(telemetry_context):
        return None
    return build_intent_from_execution_inputs(
        intent_type=intent_type,
        source_profile=source_profile,
        source_runtime_namespace=source_runtime_namespace,
        source_symbol=symbol,
        source_mt5_symbol=source.get("broker_symbol") or source.get("mt5_symbol") or symbol,
        trade_params=trade_params,
        source_trade_id=trade_id,
        candidate_id=metadata.get("candidate_id") or record.get("candidate_id"),
        effective_risk_pct=_safe_float(source.get("risk_pct") or record.get("risk_pct")),
        kill_zone=metadata.get("kill_zone") or record.get("kill_zone"),
        trigger=f"trade_record_projection:{record_path}",
        telemetry_context=telemetry_context,
        primary_order={
            "record_path": str(record_path),
            "ticket": source.get("ticket") or source.get("position_ticket"),
            "entry_order_ticket": source.get("entry_order_ticket"),
            "entry_deal_ticket": source.get("entry_deal_ticket"),
            "pending_order_mode": source.get("pending_order_mode"),
            "broker_pending_order_created": source.get("broker_pending_order_created"),
        },
    )


def publish_intent_if_enabled(
    config: dict[str, Any] | None,
    intent: dict[str, Any],
    *,
    path: str | Path | None = None,
) -> dict[str, Any]:
    if not intent_bus_enabled(config):
        return {"status": "disabled"}
    target = Path(path) if path is not None else resolve_intent_log_path(config)
    try:
        return append_intent(intent, target, dedupe=True)
    except Exception as exc:  # noqa: BLE001 - primary live path must not block
        logger.warning("dual broker intent publish failed open: %s", exc)
        return {"status": "error", "error": str(exc), "path": str(target)}
