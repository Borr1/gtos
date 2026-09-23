"""No-AI, no-execution live shadow observer for non-orchestrator symbols.

This module is intentionally separate from the live orchestrator. It reads MT5
market data, computes an as-of MSO snapshot, and appends research-only forward
rows. It must never import the AI analyzer, permissions, or execution engine.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from src.components.data_ingestion import DataIncompleteError, ingest_live_data
from src.components.market_state import compute_market_state
from src.research_infra.forward_capture import (
    PROMOTION_VERDICT,
    mso_summary_snapshot,
    record_strategy_follow_evaluation,
)
from src.utils.config import apply_instrument_overrides, apply_profile_overrides, resolve_profile

logger = logging.getLogger(__name__)

ACTIVE_MSO_SHADOW = "ACTIVE_MSO_SHADOW"
STATUS_PATH_DEFAULT = Path("shadow_logs/shadow_observer_status.jsonl")
STATE_PATH_DEFAULT = Path("pipeline_state/shadow_observer_state.json")
OUTPUT_PATH_DEFAULT = Path("shadow_logs/strategy_follow_evaluations.jsonl")


@dataclass(frozen=True)
class ShadowObserverEntry:
    observer_id: str
    symbol: str
    broker_symbol: str | None
    config_symbol: str | None
    activation_state: str
    enabled: bool
    family: str
    evidence_class: str
    source_status: str
    pre_registered_question_id: str | None = None
    allowed_rows: tuple[str, ...] = field(default_factory=tuple)
    forbidden: tuple[str, ...] = field(default_factory=tuple)
    required_before_enable: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""

    @property
    def can_emit_strategy_rows(self) -> bool:
        return self.enabled and self.activation_state == ACTIVE_MSO_SHADOW


@dataclass(frozen=True)
class ShadowObserverRegistry:
    schema_version: str
    defaults: dict[str, Any]
    instruments: tuple[ShadowObserverEntry, ...]

    @property
    def active_entries(self) -> tuple[ShadowObserverEntry, ...]:
        return tuple(item for item in self.instruments if item.can_emit_strategy_rows)


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def load_registry(path: str | Path = "config/shadow_observer_registry.yaml") -> ShadowObserverRegistry:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    entries: list[ShadowObserverEntry] = []
    for item in raw.get("instruments") or []:
        entries.append(
            ShadowObserverEntry(
                observer_id=str(item["observer_id"]),
                symbol=str(item["symbol"]),
                broker_symbol=(
                    None if item.get("broker_symbol") is None else str(item.get("broker_symbol"))
                ),
                config_symbol=(
                    None if item.get("config_symbol") is None else str(item.get("config_symbol"))
                ),
                activation_state=str(item.get("activation_state") or ""),
                enabled=bool(item.get("enabled", False)),
                family=str(item.get("family") or ""),
                evidence_class=str(item.get("evidence_class") or "FORWARD_SHADOW"),
                source_status=str(item.get("source_status") or ""),
                pre_registered_question_id=(
                    None
                    if item.get("pre_registered_question_id") is None
                    else str(item.get("pre_registered_question_id"))
                ),
                allowed_rows=_tuple(item.get("allowed_rows")),
                forbidden=_tuple(item.get("forbidden")),
                required_before_enable=_tuple(item.get("required_before_enable")),
                notes=str(item.get("notes") or ""),
            )
        )
    return ShadowObserverRegistry(
        schema_version=str(raw.get("schema_version") or "shadow_observer_registry_v1"),
        defaults=dict(raw.get("defaults") or {}),
        instruments=tuple(entries),
    )


def validate_registry(registry: ShadowObserverRegistry) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for item in registry.instruments:
        if item.observer_id in seen:
            errors.append(f"{item.observer_id}: duplicate observer_id")
        seen.add(item.observer_id)
        if item.can_emit_strategy_rows:
            if not item.broker_symbol:
                errors.append(f"{item.observer_id}: active observer requires broker_symbol")
            if not item.config_symbol:
                errors.append(f"{item.observer_id}: active observer requires config_symbol")
            if not item.pre_registered_question_id:
                errors.append(f"{item.observer_id}: active observer requires pre_registered_question_id")
            if "strategy_follow_evaluation_v1" not in item.allowed_rows:
                errors.append(f"{item.observer_id}: active observer must allow strategy_follow_evaluation_v1")
            forbidden = set(item.forbidden)
            for required_forbidden in (
                "ai_api_call",
                "canary_call",
                "order_send",
                "execution_engine",
                "permission_gate",
                "outcome_opening",
            ):
                if required_forbidden not in forbidden:
                    errors.append(f"{item.observer_id}: missing forbidden={required_forbidden}")
    return errors


def append_jsonl(path: str | Path, row: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def status_row(
    entry: ShadowObserverEntry,
    *,
    lifecycle_status: str,
    observer_run_id: str | None = None,
    reason: str | None = None,
    decision_time_utc: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    detail_values = details or {}
    rows_written = detail_values.get("rows_written")
    if rows_written is None:
        rows_written = 1 if lifecycle_status == "EMITTED_STRATEGY_FOLLOW_EVALUATION" else 0
    return {
        "schema_version": "shadow_observer_status_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "observer_id": entry.observer_id,
        "symbol": entry.symbol,
        "broker_symbol": entry.broker_symbol,
        "config_symbol": entry.config_symbol,
        "family": entry.family,
        "activation_state": entry.activation_state,
        "enabled": entry.enabled,
        "source_status": entry.source_status,
        "pre_registered_question_id": entry.pre_registered_question_id,
        "observer_run_id": observer_run_id,
        "status": lifecycle_status,
        "lifecycle_status": lifecycle_status,
        "reason": reason,
        "decision_time_utc": decision_time_utc,
        "latest_closed_m15_utc": decision_time_utc,
        "rows_written": rows_written,
        "ai_calls": 0,
        "databento_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
        "no_ai_calls": True,
        "no_execution": True,
        "no_canary_required": True,
        "promotion_verdict": PROMOTION_VERDICT,
        "details": detail_values,
    }


def _parse_iso_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except Exception:
        return None


def status_throttle_seconds(row: dict[str, Any]) -> int:
    lifecycle = str(row.get("lifecycle_status") or "")
    if lifecycle in {
        "SKIPPED_OUTSIDE_KILL_ZONE",
        "SKIPPED_DUPLICATE_CANDLE",
        "SKIPPED_NOT_ACTIVE_MSO_SHADOW",
    }:
        return 10 * 60
    if lifecycle in {"BLOCKED_SYMBOL_NOT_READY", "BLOCKED_NO_CLOSED_M15"}:
        return 2 * 60
    return 0


def append_status(
    path: str | Path,
    row: dict[str, Any],
    *,
    state: dict[str, Any] | None = None,
) -> bool:
    throttle = status_throttle_seconds(row)
    if state is not None and throttle > 0:
        throttle_state = state.setdefault("_status_throttle", {})
        key = "|".join(
            str(row.get(name) or "")
            for name in ("observer_id", "lifecycle_status", "reason", "decision_time_utc")
        )
        now = _parse_iso_utc(row.get("created_at_utc")) or datetime.now(timezone.utc)
        last = _parse_iso_utc(throttle_state.get(key))
        if last is not None and (now - last).total_seconds() < throttle:
            return False
        throttle_state[key] = now.isoformat()
    append_jsonl(path, row)
    return True


def load_json(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("shadow observer state unreadable; starting fresh: %s", target)
        return {}


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(target)


def active_kill_zone(config: dict[str, Any], now: datetime | None = None) -> str | None:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)
    minute = current.hour * 60 + current.minute
    for name, window in ((config.get("market") or {}).get("kill_zones") or {}).items():
        start = _parse_hhmm(str(window.get("start_utc", "00:00")))
        end = _parse_hhmm(str(window.get("end_utc", "00:00")))
        if end <= start:
            if minute >= start or minute < end:
                return str(name)
        elif start <= minute < end:
            return str(name)
    return None


def _parse_hhmm(value: str) -> int:
    hour_s, minute_s = value.split(":", 1)
    return int(hour_s) * 60 + int(minute_s)


def load_observer_config(
    *,
    base_config_path: str | Path,
    profile: str | None,
    entry: ShadowObserverEntry,
) -> dict[str, Any]:
    raw = yaml.safe_load(Path(base_config_path).read_text(encoding="utf-8")) or {}
    resolved_profile = resolve_profile(profile)
    config = apply_profile_overrides(raw, resolved_profile)
    config = apply_instrument_overrides(config, entry.config_symbol)
    config.setdefault("market", {})
    config["market"]["symbol"] = entry.symbol
    if entry.broker_symbol:
        config["market"]["mt5_symbol"] = entry.broker_symbol
    config["trading_enabled"] = False
    config["shadow_observer"] = {
        "observer_id": entry.observer_id,
        "source_status": entry.source_status,
        "pre_registered_question_id": entry.pre_registered_question_id,
        "no_ai_calls": True,
        "no_execution": True,
    }
    return config


def _ensure_symbol_selected(mt5: Any, broker_symbol: str | None) -> tuple[bool, str]:
    if not broker_symbol:
        return False, "missing_broker_symbol"
    raw = getattr(mt5, "_mt5", None)
    if raw is None or not hasattr(raw, "symbol_select"):
        return True, "symbol_select_unavailable_assumed_ready"
    try:
        ok = bool(raw.symbol_select(broker_symbol, True))
    except Exception as exc:  # noqa: BLE001
        return False, f"symbol_select_exception:{type(exc).__name__}:{exc}"
    return (ok, "symbol_select_ok" if ok else "symbol_select_false")


def _candle_close(raw_data: dict[str, Any]) -> str | None:
    value = raw_data.get("candle_close_utc")
    return None if value is None else str(value)


def observe_entry_once(
    *,
    entry: ShadowObserverEntry,
    mt5: Any,
    base_config_path: str | Path = "config/agent_config.yaml",
    profile: str | None = None,
    output_path: str | Path = OUTPUT_PATH_DEFAULT,
    status_path: str | Path = STATUS_PATH_DEFAULT,
    state: dict[str, Any] | None = None,
    now: datetime | None = None,
    observer_run_id: str | None = None,
) -> bool:
    """Observe one registry entry once.

    Returns True when a strategy evaluation row was emitted.
    """
    if not entry.can_emit_strategy_rows:
        append_status(
            status_path,
            status_row(
                entry,
                lifecycle_status="SKIPPED_NOT_ACTIVE_MSO_SHADOW",
                observer_run_id=observer_run_id,
                reason=entry.activation_state,
            ),
            state=state,
        )
        return False

    selected_ok, selected_reason = _ensure_symbol_selected(mt5, entry.broker_symbol)
    if not selected_ok:
        append_status(
            status_path,
            status_row(
                entry,
                lifecycle_status="BLOCKED_SYMBOL_NOT_READY",
                observer_run_id=observer_run_id,
                reason=selected_reason,
            ),
            state=state,
        )
        return False

    config = load_observer_config(
        base_config_path=base_config_path,
        profile=profile,
        entry=entry,
    )
    kill_zone = active_kill_zone(config, now=now)
    if kill_zone is None:
        append_status(
            status_path,
            status_row(
                entry,
                lifecycle_status="SKIPPED_OUTSIDE_KILL_ZONE",
                observer_run_id=observer_run_id,
                reason="outside_configured_kill_zones",
                details={"symbol_select": selected_reason},
            ),
            state=state,
        )
        return False

    try:
        raw_data = ingest_live_data(mt5, config)
        decision_time = _candle_close(raw_data)
        if not decision_time:
            append_status(
                status_path,
                status_row(
                    entry,
                    lifecycle_status="BLOCKED_NO_CLOSED_M15",
                    observer_run_id=observer_run_id,
                    reason=str(raw_data.get("candle_timestamp_source") or "missing_candle_close_utc"),
                    details={"symbol_select": selected_reason},
                ),
                state=state,
            )
            return False
        state = state if state is not None else {}
        per_symbol = state.setdefault(entry.observer_id, {})
        if per_symbol.get("last_candle_close_utc") == decision_time:
            append_status(
                status_path,
                status_row(
                    entry,
                    lifecycle_status="SKIPPED_DUPLICATE_CANDLE",
                    observer_run_id=observer_run_id,
                    reason="already_emitted_for_candle",
                    decision_time_utc=decision_time,
                ),
                state=state,
            )
            return False

        mso = compute_market_state(raw_data, config)
        record_strategy_follow_evaluation(
            {
                "symbol": entry.symbol,
                "broker_symbol": entry.broker_symbol,
                "source_symbol": entry.family,
                "session": kill_zone,
                "kill_zone": kill_zone,
                "candidate_id": f"{entry.symbol}_{decision_time}_shadow_observer",
                "trade_id": None,
                "evidence_class": entry.evidence_class,
                "decision_time_utc": decision_time,
                "asof_cutoff_utc": decision_time,
                "source_file": "shadow_observer_mso_no_ai",
                "source_hash": entry.pre_registered_question_id,
                "source_run_id": observer_run_id,
                "dedupe_key": f"{entry.observer_id}|{decision_time}|SHADOW_OBSERVER_MSO_NO_AI",
                "no_leak_status": "NO_AI_NO_EXECUTION_NO_POST_OUTCOME_FIELDS",
                "evaluation_stage": "SHADOW_OBSERVER_MSO_NO_AI",
                "ai_dependency": "NO_AI_REQUIRED_FOR_ROW",
                "ai_status": "NOT_CALLED_BY_SHADOW_OBSERVER",
                "prescreen_status": "NOT_RUN_NO_AI_OBSERVER",
                "deterministic_bias": None,
                "mso_summary": mso_summary_snapshot(mso),
                "external_confluence_policy": {
                    "sierra": "ATTACH_ONLY_IF_REGISTERED_PROXY_AND_LOCAL_FILE_PRESENT",
                    "databento": "NO_DATABENTO_CALL_FROM_SHADOW_OBSERVER",
                    "no_paid_fetch_from_this_pre_ai_row": True,
                },
                "observer_metadata": {
                    "observer_id": entry.observer_id,
                    "observer_run_id": observer_run_id,
                    "family": entry.family,
                    "activation_state": entry.activation_state,
                    "source_status": entry.source_status,
                    "pre_registered_question_id": entry.pre_registered_question_id,
                    "no_execution": True,
                    "no_ai_calls": True,
                    "no_canary_required": True,
                    "symbol_select": selected_reason,
                },
            },
            log_path=output_path,
        )
        per_symbol["last_candle_close_utc"] = decision_time
        per_symbol["last_emit_utc"] = datetime.now(timezone.utc).isoformat()
        append_status(
            status_path,
            status_row(
                entry,
                lifecycle_status="EMITTED_STRATEGY_FOLLOW_EVALUATION",
                observer_run_id=observer_run_id,
                decision_time_utc=decision_time,
                details={"kill_zone": kill_zone, "symbol_select": selected_reason},
            ),
            state=state,
        )
        return True
    except DataIncompleteError as exc:
        append_status(
            status_path,
            status_row(
                entry,
                lifecycle_status="BLOCKED_DATA_INCOMPLETE",
                observer_run_id=observer_run_id,
                reason=str(exc),
                details={"symbol_select": selected_reason},
            ),
            state=state,
        )
        return False
    except Exception as exc:  # noqa: BLE001
        append_status(
            status_path,
            status_row(
                entry,
                lifecycle_status="ERROR_FAIL_OPEN",
                observer_run_id=observer_run_id,
                reason=f"{type(exc).__name__}: {exc}",
                details={"symbol_select": selected_reason},
            ),
            state=state,
        )
        logger.warning("shadow observer failed for %s: %s", entry.symbol, exc)
        return False


def observe_cycle(
    *,
    registry: ShadowObserverRegistry,
    mt5: Any,
    symbols: Iterable[str] | None = None,
    include_inactive: bool = False,
    base_config_path: str | Path = "config/agent_config.yaml",
    profile: str | None = None,
    output_path: str | Path | None = None,
    status_path: str | Path | None = None,
    state_path: str | Path | None = None,
    now: datetime | None = None,
    observer_run_id: str | None = None,
) -> dict[str, Any]:
    wanted = {s.upper() for s in symbols or []}
    output = Path(output_path or registry.defaults.get("output_path") or OUTPUT_PATH_DEFAULT)
    status = Path(status_path or registry.defaults.get("status_path") or STATUS_PATH_DEFAULT)
    state_target = Path(state_path or registry.defaults.get("state_path") or STATE_PATH_DEFAULT)
    state = load_json(state_target)
    emitted = 0
    checked = 0
    skipped_by_filter = 0
    entries = registry.instruments if include_inactive else registry.active_entries
    for entry in entries:
        if wanted and entry.symbol.upper() not in wanted and entry.observer_id.upper() not in wanted:
            skipped_by_filter += 1
            continue
        checked += 1
        if observe_entry_once(
            entry=entry,
            mt5=mt5,
            base_config_path=base_config_path,
            profile=profile,
            output_path=output,
            status_path=status,
            state=state,
            now=now,
            observer_run_id=observer_run_id,
        ):
            emitted += 1
    write_json(state_target, state)
    return {
        "schema_version": "shadow_observer_cycle_result_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "checked": checked,
        "emitted": emitted,
        "skipped_by_filter": skipped_by_filter,
        "output_path": str(output),
        "status_path": str(status),
        "state_path": str(state_target),
        "observer_run_id": observer_run_id,
    }
