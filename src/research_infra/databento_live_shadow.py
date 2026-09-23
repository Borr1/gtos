"""Databento Live shadow-row helpers.

The live collector is intentionally separate from the trading orchestrator. It
may use network and a paid data subscription, so production trade decisions only
read the append-only shadow log if it exists.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "databento_live_confluence_v1"
BUDGET_LEDGER_SCHEMA_VERSION = "databento_live_budget_ledger_v1"
POLICY_VERSION = "databento_live_trigger_policy_v1"
POLICY_ID = "lto010_databento_live_confluence_policy_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DEFAULT_LOG_PATH = Path("shadow_logs/databento_live_confluence.jsonl")
DEFAULT_BUDGET_LOG_PATH = Path("shadow_logs/databento_live_budget_ledger.jsonl")

ENABLE_ENV_VAR = "GTOS_DATABENTO_LIVE_SHADOW_ENABLED"
OWNER_APPROVAL_ENV_VAR = "GTOS_DATABENTO_LIVE_OWNER_APPROVED"
TRIGGER_CAP_ENV_VAR = "GTOS_DATABENTO_LIVE_TRIGGER_CAP_USD"
DAILY_CAP_ENV_VAR = "GTOS_DATABENTO_LIVE_DAILY_CAP_USD"
API_KEY_ENV_VAR = "DATABENTO_API_KEY"
OWNER_APPROVAL_STATUS = "OWNER_APPROVED_BY_CEO_2026-05-05_VALUE_MAX_FORWARD_COLLECTION"

NO_DECISION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}

REGISTERED_SYMBOL_SCHEMAS = {
    # Direct CME futures proxies that can add forward orderflow/depth context
    # around GTOS live candidates. GBPJPY remains a source-transfer problem
    # because it needs an explicit 6B/6J cross-proxy convention before use.
    "NAS100": ("trades", "mbp-10", "mbo"),
    "US30": ("trades", "mbp-10", "mbo"),
    "XAUUSD": ("trades", "mbp-10", "mbo"),
    "XAGUSD": ("trades", "mbp-10", "mbo"),
    "USDJPY": ("trades", "mbp-10"),
    "GBPUSD": ("trades", "mbp-10"),
}

SCHEMA_FEATURE_CLASSES = {
    "trades": "TRADES_ONLY",
    "tbbo": "TRADES_ONLY",
    "mbp-1": "MBP_DEPTH",
    "mbp-10": "MBP_DEPTH",
    "mbo": "MBO_ORDER_FLOW",
    "depth-heatmap": "DEPTH_HEATMAP",
}

MAX_COST_PER_TRIGGER_USD = 2.50
DAILY_SPEND_CAP_USD = 25.00
COOLDOWN_SECONDS = 60
MAX_TIMEOUT_SECONDS = 600.0
MAX_RECORDS_PER_TRIGGER = 50000

GTOS_TO_DATABENTO = {
    "NAS100": {"raw_symbol": "NQ.FUT", "stype_in": "parent"},
    "US30": {"raw_symbol": "YM.FUT", "stype_in": "parent"},
    "US30_cash": {"raw_symbol": "YM.FUT", "stype_in": "parent"},
    "XAUUSD": {"raw_symbol": "GC.FUT", "stype_in": "parent"},
    "XAGUSD": {"raw_symbol": "SI.FUT", "stype_in": "parent"},
    "USDJPY": {"raw_symbol": "6J.FUT", "stype_in": "parent"},
    "GBPUSD": {"raw_symbol": "6B.FUT", "stype_in": "parent"},
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_key(schema: str, *parts: Any) -> str:
    payload = "|".join(str(part) for part in (schema, *parts))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except Exception:
        return None


def _float_env(env: Mapping[str, str], name: str) -> float | None:
    try:
        value = env.get(name)
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def schema_feature_class(schema: str | None) -> str:
    return SCHEMA_FEATURE_CLASSES.get(str(schema or "").lower(), "UNKNOWN_SCHEMA_FEATURE_CLASS")


def registered_policy_summary() -> dict[str, Any]:
    return {
        "schema_version": POLICY_VERSION,
        "policy_id": POLICY_ID,
        "registered_symbol_schemas": REGISTERED_SYMBOL_SCHEMAS,
        "schema_feature_classes": SCHEMA_FEATURE_CLASSES,
        "max_cost_per_trigger_usd": MAX_COST_PER_TRIGGER_USD,
        "daily_spend_cap_usd": DAILY_SPEND_CAP_USD,
        "cooldown_seconds": COOLDOWN_SECONDS,
        "max_timeout_seconds": MAX_TIMEOUT_SECONDS,
        "max_records_per_trigger": MAX_RECORDS_PER_TRIGGER,
        "required_env": {
            "enabled": ENABLE_ENV_VAR,
            "api_key": API_KEY_ENV_VAR,
            "trigger_cap_usd_override": TRIGGER_CAP_ENV_VAR,
            "daily_cap_usd_override": DAILY_CAP_ENV_VAR,
        },
        "owner_approval_status": OWNER_APPROVAL_STATUS,
        "activation_policy": (
            "Live paid collection is owner-approved for value-max forward collection. "
            "A live pull still requires a registered trigger_id, non-empty reason, "
            "allowed symbol/schema, cooldown pass, cost-cap pass, API key, and enabled env. "
            "Dry-run/status rows never connect."
        ),
        "promotion_verdict": PROMOTION_VERDICT,
    }


def load_budget_rows(path: Path | str = DEFAULT_BUDGET_LOG_PATH) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows


def _budget_day(value: datetime) -> str:
    return value.astimezone(timezone.utc).date().isoformat()


def _reserved_or_charged(row: dict[str, Any]) -> bool:
    return str(row.get("budget_status") or "") in {
        "BUDGET_RESERVED",
        "BUDGET_CHARGED",
        "LIVE_SESSION_CLOSED_ACTUAL_COST_UNKNOWN",
    }


def _daily_reserved_usd(rows: list[dict[str, Any]], day_utc: str) -> float:
    total = 0.0
    for row in rows:
        if row.get("budget_day_utc") != day_utc or not _reserved_or_charged(row):
            continue
        value = row.get("actual_cost_usd")
        if value is None:
            value = row.get("estimated_cost_usd")
        try:
            total += float(value or 0.0)
        except (TypeError, ValueError):
            continue
    return total


def _cooldown_remaining_seconds(
    rows: list[dict[str, Any]],
    *,
    symbols: list[str],
    now: datetime,
) -> int:
    newest: datetime | None = None
    symbol_set = set(symbols)
    for row in rows:
        if not _reserved_or_charged(row):
            continue
        row_symbols = set(row.get("symbols") or [])
        if not row_symbols.intersection(symbol_set):
            continue
        ts = _parse_utc(row.get("created_at_utc"))
        if ts is None:
            continue
        if newest is None or ts > newest:
            newest = ts
    if newest is None:
        return 0
    elapsed = (now - newest).total_seconds()
    return max(0, int(COOLDOWN_SECONDS - elapsed))


def evaluate_live_trigger_policy(
    *,
    symbols: list[str],
    schemas: list[str],
    trigger_id: str | None,
    reason: str | None,
    estimated_cost_usd: float | None,
    timeout_seconds: float | None,
    max_records: int | None,
    env: Mapping[str, str],
    budget_rows: list[dict[str, Any]] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now = now_utc or datetime.now(timezone.utc)
    budget_rows = budget_rows or []
    normalized_symbols = [item.strip() for item in symbols if item.strip()]
    normalized_schemas = [item.strip().lower() for item in schemas if item.strip()]
    day_utc = _budget_day(now)
    env_trigger_cap = _float_env(env, TRIGGER_CAP_ENV_VAR)
    env_daily_cap = _float_env(env, DAILY_CAP_ENV_VAR)
    effective_trigger_cap = min(MAX_COST_PER_TRIGGER_USD, env_trigger_cap) if env_trigger_cap is not None else MAX_COST_PER_TRIGGER_USD
    effective_daily_cap = min(DAILY_SPEND_CAP_USD, env_daily_cap) if env_daily_cap is not None else DAILY_SPEND_CAP_USD

    block_reasons: list[str] = []
    if not trigger_id:
        block_reasons.append("MISSING_TRIGGER_ID")
    if not reason or len(reason.strip()) < 12:
        block_reasons.append("MISSING_REQUIRED_REASON")
    if not normalized_symbols:
        block_reasons.append("NO_SYMBOLS_REQUESTED")
    if not normalized_schemas:
        block_reasons.append("NO_SCHEMAS_REQUESTED")

    symbol_schema_status: dict[str, Any] = {}
    for symbol in normalized_symbols:
        allowed = REGISTERED_SYMBOL_SCHEMAS.get(symbol)
        if not allowed:
            block_reasons.append(f"SYMBOL_NOT_REGISTERED:{symbol}")
            symbol_schema_status[symbol] = {"status": "SYMBOL_NOT_REGISTERED", "allowed_schemas": []}
            continue
        bad_schemas = [schema for schema in normalized_schemas if schema not in allowed]
        if bad_schemas:
            block_reasons.append(f"SCHEMA_NOT_ALLOWED:{symbol}:{','.join(bad_schemas)}")
        symbol_schema_status[symbol] = {
            "status": "OK" if not bad_schemas else "SCHEMA_NOT_ALLOWED",
            "allowed_schemas": list(allowed),
            "requested_schemas": normalized_schemas,
        }

    if estimated_cost_usd is None:
        block_reasons.append("MISSING_ESTIMATED_COST_USD")
    elif estimated_cost_usd < 0:
        block_reasons.append("NEGATIVE_ESTIMATED_COST_USD")
    timeout_value = float(timeout_seconds or 0.0)
    if timeout_value <= 0:
        block_reasons.append("MISSING_TIMEOUT_SECONDS")
    elif timeout_value > MAX_TIMEOUT_SECONDS:
        block_reasons.append("TIMEOUT_EXCEEDS_POLICY")
    if max_records is None or max_records <= 0:
        block_reasons.append("MISSING_MAX_RECORDS")
    elif max_records > MAX_RECORDS_PER_TRIGGER:
        block_reasons.append("MAX_RECORDS_EXCEEDS_POLICY")

    if env.get(ENABLE_ENV_VAR) != "1":
        block_reasons.append("DISABLED_BY_ENV")
    if not env.get(API_KEY_ENV_VAR):
        block_reasons.append("DATABENTO_API_KEY_MISSING")

    estimated = float(estimated_cost_usd or 0.0)
    if estimated_cost_usd is not None and estimated > effective_trigger_cap:
        block_reasons.append("TRIGGER_COST_CAP_EXCEEDED")
    daily_reserved = _daily_reserved_usd(budget_rows, day_utc)
    if daily_reserved + estimated > effective_daily_cap:
        block_reasons.append("DAILY_COST_CAP_EXCEEDED")
    cooldown_remaining = _cooldown_remaining_seconds(
        budget_rows,
        symbols=normalized_symbols,
        now=now,
    )
    if cooldown_remaining > 0:
        block_reasons.append("COOLDOWN_ACTIVE")

    live_fetch_allowed = not block_reasons
    trigger_status = "TRIGGER_APPROVED_FOR_LIVE_FETCH" if live_fetch_allowed else block_reasons[0]
    decision = "ALLOW_LIVE_FETCH" if live_fetch_allowed else "DO_NOT_FETCH"
    feature_classes = sorted({schema_feature_class(schema) for schema in normalized_schemas})

    return {
        "schema_version": "databento_live_trigger_policy_decision_v1",
        "policy": registered_policy_summary(),
        "policy_id": POLICY_ID,
        "created_at_utc": now.isoformat(),
        "trigger_id": trigger_id,
        "trigger_status": trigger_status,
        "decision": decision,
        "live_fetch_allowed": live_fetch_allowed,
        "block_reasons": block_reasons,
        "symbols": normalized_symbols,
        "schemas": normalized_schemas,
        "feature_classes": feature_classes,
        "symbol_schema_status": symbol_schema_status,
        "reason": reason,
        "estimated_cost_usd": estimated_cost_usd,
        "budget_day_utc": day_utc,
        "daily_reserved_usd_before_trigger": round(daily_reserved, 6),
        "max_cost_per_trigger_usd": MAX_COST_PER_TRIGGER_USD,
        "daily_spend_cap_usd": DAILY_SPEND_CAP_USD,
        "effective_trigger_cap_usd": effective_trigger_cap,
        "effective_daily_cap_usd": effective_daily_cap,
        "cooldown_seconds": COOLDOWN_SECONDS,
        "cooldown_remaining_seconds": cooldown_remaining,
        "timeout_seconds": timeout_seconds,
        "max_records": max_records,
        "env_status": {
            "enabled": env.get(ENABLE_ENV_VAR) == "1",
            "owner_approved": True,
            "owner_approval_status": OWNER_APPROVAL_STATUS,
            "owner_approval_env_present": env.get(OWNER_APPROVAL_ENV_VAR) == "1",
            "api_key_present": bool(env.get(API_KEY_ENV_VAR)),
            "trigger_cap_usd_override_present": env_trigger_cap is not None,
            "daily_cap_usd_override_present": env_daily_cap is not None,
        },
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
        "databento_calls": 0,
        **NO_DECISION_COUNTERS,
        "promotion_verdict": PROMOTION_VERDICT,
    }


def build_live_status_row(
    *,
    status: str,
    gtos_symbol: str | None = None,
    raw_symbol: str | None = None,
    schema: str | None = None,
    dataset: str = "GLBX.MDP3",
    message: str | None = None,
    features: dict[str, Any] | None = None,
    trigger_id: str | None = None,
    policy_decision: dict[str, Any] | None = None,
    feature_class: str | None = None,
    source_candidate_id: str | None = None,
    source_opportunity_id: str | None = None,
    asof_cutoff_utc: str | None = None,
    window_start_utc: str | None = None,
    window_end_utc: str | None = None,
    signal_use_case: str | None = None,
    paid_fetch_attempted: bool = False,
    paid_data_calls: int = 0,
    databento_calls: int = 0,
) -> dict[str, Any]:
    created = utc_now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _row_key(
            SCHEMA_VERSION,
            created,
            status,
            trigger_id,
            gtos_symbol,
            raw_symbol,
            schema,
        ),
        "created_at_utc": created,
        "promotion_verdict": PROMOTION_VERDICT,
        "evidence_class": "FUTURES_PROXY_TRANSFER",
        "status": status,
        "trigger_id": trigger_id,
        "candidate_id": source_candidate_id,
        "source_candidate_id": source_candidate_id,
        "source_opportunity_id": source_opportunity_id,
        "gtos_symbol": gtos_symbol,
        "symbol": gtos_symbol,
        "raw_symbol": raw_symbol,
        "dataset": dataset,
        "schema": schema,
        "feature_class": feature_class or schema_feature_class(schema),
        "asof_cutoff_utc": asof_cutoff_utc,
        "window_start_utc": window_start_utc,
        "window_end_utc": window_end_utc,
        "signal_use_case": signal_use_case,
        "message": message,
        "features": features or {},
        "policy_id": POLICY_ID,
        "policy_decision": policy_decision or {},
        "cost_policy": {
            "max_cost_per_trigger_usd": MAX_COST_PER_TRIGGER_USD,
            "daily_spend_cap_usd": DAILY_SPEND_CAP_USD,
            "cooldown_seconds": COOLDOWN_SECONDS,
        },
        "paid_fetch_attempted": paid_fetch_attempted,
        "paid_data_calls": paid_data_calls,
        "databento_calls": databento_calls,
        **NO_DECISION_COUNTERS,
        "no_leak_status": "LIVE_STREAM_RECORD_ASOF_EVENT_TIME",
    }


def append_live_row(row: dict[str, Any], path: Path | str = DEFAULT_LOG_PATH) -> None:
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Databento live shadow append failed: %s", exc)


def build_budget_ledger_row(
    *,
    budget_status: str,
    policy_decision: dict[str, Any],
    actual_cost_usd: float | None = None,
) -> dict[str, Any]:
    created = utc_now_iso()
    trigger_id = policy_decision.get("trigger_id")
    symbols = list(policy_decision.get("symbols") or [])
    schemas = list(policy_decision.get("schemas") or [])
    estimated_cost = policy_decision.get("estimated_cost_usd")
    attempted_statuses = {
        "BUDGET_RESERVED",
        "BUDGET_CHARGED",
        "LIVE_SESSION_CLOSED_ACTUAL_COST_UNKNOWN",
        "LIVE_SESSION_FAILED_NO_LICENSE",
        "LIVE_SESSION_FAILED_API_ERROR",
    }
    paid_data_statuses = {
        "BUDGET_CHARGED",
        "LIVE_SESSION_CLOSED_ACTUAL_COST_UNKNOWN",
    }
    return {
        "schema_version": BUDGET_LEDGER_SCHEMA_VERSION,
        "row_key": _row_key(BUDGET_LEDGER_SCHEMA_VERSION, created, trigger_id, budget_status, symbols, schemas),
        "created_at_utc": created,
        "promotion_verdict": PROMOTION_VERDICT,
        "evidence_class": "FUTURES_PROXY_TRANSFER",
        "policy_id": POLICY_ID,
        "trigger_id": trigger_id,
        "budget_status": budget_status,
        "budget_day_utc": policy_decision.get("budget_day_utc"),
        "symbols": symbols,
        "schemas": schemas,
        "feature_classes": list(policy_decision.get("feature_classes") or []),
        "estimated_cost_usd": estimated_cost,
        "actual_cost_usd": actual_cost_usd,
        "daily_reserved_usd_before_trigger": policy_decision.get("daily_reserved_usd_before_trigger"),
        "max_cost_per_trigger_usd": policy_decision.get("max_cost_per_trigger_usd"),
        "daily_spend_cap_usd": policy_decision.get("daily_spend_cap_usd"),
        "effective_trigger_cap_usd": policy_decision.get("effective_trigger_cap_usd"),
        "effective_daily_cap_usd": policy_decision.get("effective_daily_cap_usd"),
        "cooldown_seconds": policy_decision.get("cooldown_seconds"),
        "cooldown_remaining_seconds": policy_decision.get("cooldown_remaining_seconds"),
        "decision": policy_decision.get("decision"),
        "trigger_status": policy_decision.get("trigger_status"),
        "paid_fetch_attempted": budget_status in attempted_statuses,
        "paid_data_calls": 1 if budget_status in paid_data_statuses else 0,
        "databento_calls": 1 if budget_status in attempted_statuses else 0,
        **NO_DECISION_COUNTERS,
        "no_leak_status": "BUDGET_LEDGER_NOT_A_DECISION_FEATURE",
    }


def append_budget_row(row: dict[str, Any], path: Path | str = DEFAULT_BUDGET_LOG_PATH) -> None:
    append_live_row(row, path)


def normalize_record(record: Any) -> dict[str, Any]:
    """Best-effort conversion of a Databento record to JSON-safe fields."""
    if hasattr(record, "to_dict"):
        try:
            return dict(record.to_dict())
        except Exception:
            pass
    out: dict[str, Any] = {}
    for name in (
        "ts_event",
        "ts_recv",
        "instrument_id",
        "price",
        "size",
        "side",
        "action",
        "levels",
        "bid_px_00",
        "ask_px_00",
        "bid_sz_00",
        "ask_sz_00",
    ):
        try:
            value = getattr(record, name)
        except Exception:
            continue
        out[name] = value
    if not out:
        out["repr"] = repr(record)
    return out
