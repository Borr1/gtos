"""Hash-only AI decision trace logger.

Observation-only JSONL capture for PrimaryAnalyzer calls. The logger records
prompt/response fingerprints, model/candle context, final decision, and token
usage without storing full prompt or response text.

Output: ``shadow_logs/ai_decision_trace.jsonl``.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.components.ai_reliability_contract import (
    AI_RELIABILITY_CONTRACT_SCHEMA_VERSION,
    build_cache_identity,
    build_deterministic_baseline_contract,
    build_disagreement_calibration_contract,
    build_fallback_behavior_contract,
    build_model_version_contract,
    build_semantic_ownership_handoff,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "ai_decision_trace_v1"
SHADOW_LOG_PATH = "shadow_logs/ai_decision_trace.jsonl"


def _logger_config(config: Optional[dict[str, Any]]) -> dict[str, Any]:
    if not config:
        return {}
    try:
        logger_cfg = (config.get("shadow_loggers", {}) or {}).get(
            "ai_decision_trace_logger", {}
        ) or {}
        return logger_cfg if isinstance(logger_cfg, dict) else {}
    except Exception:
        return {}


def _logger_enabled(config: Optional[dict[str, Any]]) -> bool:
    return bool(_logger_config(config).get("enabled", False))


def _stable_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_len(value: str | None) -> int:
    return len(value or "")


def _result_value(result: Any, field: str, default: Any = None) -> Any:
    return getattr(result, field, default) if result is not None else default


def _trade_direction(result: Any) -> str | None:
    params = _result_value(result, "trade_parameters")
    if params is None:
        return None
    direction = getattr(params, "direction", None)
    return str(direction) if direction is not None else None


def _result_payload(result: Any) -> dict[str, Any]:
    if result is None:
        return {}
    try:
        return result.model_dump(mode="json")
    except Exception:
        return {"repr": repr(result)}


def _usage_payload(usage: Optional[dict[str, Any]]) -> dict[str, int]:
    usage = usage or {}
    return {
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "cache_read_tokens": int(usage.get("cache_read_tokens") or 0),
        "cache_create_tokens": int(usage.get("cache_create_tokens") or 0),
    }


def build_ai_decision_trace_row(
    *,
    system_prompt: Any,
    user_message: str,
    raw_response: str | None,
    result: Any,
    usage: Optional[dict[str, Any]],
    symbol: str | None,
    candle_time: str | None,
    kill_zone: str | None,
    model: str | None,
    backend_mode: str | None,
    response_status: str,
    parse_attempts: int,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a hash-only AI trace row without touching disk."""
    system_text = _stable_text(system_prompt)
    user_text = user_message or ""
    response_text = raw_response or ""
    result_payload = _result_payload(result)
    result_text = _stable_text(result_payload)
    prompt_bundle = _stable_text(
        {
            "model": model,
            "system_prompt_sha256": _sha256_text(system_text),
            "user_message_sha256": _sha256_text(user_text),
        }
    )
    prompt_bundle_sha = _sha256_text(prompt_bundle)
    user_message_sha = _sha256_text(user_text)
    source_context = {
        "symbol": symbol,
        "candle_time": candle_time,
        "kill_zone": kill_zone,
        "backend_mode": backend_mode,
    }
    cache_identity = build_cache_identity(
        model=model,
        prompt_bundle_sha256=prompt_bundle_sha,
        user_message_sha256=user_message_sha,
        config=config,
        source_context=source_context,
    )
    no_trade_reason = _result_value(result, "no_trade_reason")
    fallback_behavior = build_fallback_behavior_contract(
        reason=no_trade_reason,
        response_status=response_status,
        parse_attempts=parse_attempts,
    )
    row_key = _sha256_text(
        _stable_text(
            {
                "symbol": symbol,
                "candle_time": candle_time,
                "kill_zone": kill_zone,
                "model": model,
                "response_status": response_status,
                "parse_attempts": parse_attempts,
                "prompt_bundle_sha256": prompt_bundle_sha,
                "response_sha256": _sha256_text(response_text) if response_text else None,
                "result_sha256": _sha256_text(result_text),
                "cache_key": cache_identity.get("content_addressed_cache_key"),
            }
        )
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "row_key": row_key,
        "symbol": symbol,
        "candle_time": candle_time,
        "kill_zone": kill_zone,
        "model": model,
        "backend_mode": backend_mode,
        "response_status": response_status,
        "parse_attempts": parse_attempts,
        "decision": _result_value(result, "decision"),
        "no_trade_reason": _result_value(result, "no_trade_reason"),
        "framework": _result_value(result, "framework"),
        "trade_direction": _trade_direction(result),
        "prompt_fingerprint": {
            "system_prompt_sha256": _sha256_text(system_text),
            "user_message_sha256": user_message_sha,
            "prompt_bundle_sha256": prompt_bundle_sha,
            "system_prompt_length": _safe_len(system_text),
            "user_message_length": _safe_len(user_text),
        },
        "content_addressed_cache_identity": cache_identity,
        "ai_reliability_contract": {
            "schema_version": AI_RELIABILITY_CONTRACT_SCHEMA_VERSION,
            "model_version_contract": build_model_version_contract(
                requested_model=model
            ),
            "deterministic_baseline_contract": build_deterministic_baseline_contract(
                reason=no_trade_reason or "trace_observation_no_fallback"
            ),
            "fallback_behavior_contract": fallback_behavior,
            "disagreement_calibration_contract": build_disagreement_calibration_contract(),
            "semantic_ownership_handoff": build_semantic_ownership_handoff(),
        },
        "raw_response_sha256": _sha256_text(response_text) if response_text else None,
        "raw_response_length": _safe_len(response_text),
        "result_sha256": _sha256_text(result_text),
        "usage": _usage_payload(usage),
        "research_boundary": {
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call_added_by_logger": False,
            "runtime_candidate_use_permitted": False,
            "stores_full_prompt_or_response_text": False,
        },
    }


def record_ai_decision_trace(
    *,
    config: Optional[dict[str, Any]],
    system_prompt: Any,
    user_message: str,
    raw_response: str | None,
    result: Any,
    usage: Optional[dict[str, Any]],
    symbol: str | None,
    candle_time: str | None,
    kill_zone: str | None,
    model: str | None,
    backend_mode: str | None,
    response_status: str,
    parse_attempts: int,
    log_path: str | None = None,
) -> dict[str, Any] | None:
    """Append one AI decision trace row.

    This function must never raise into the trading path.
    """
    try:
        if not _logger_enabled(config):
            return None
        logger_cfg = _logger_config(config)
        path = Path(log_path or logger_cfg.get("path") or SHADOW_LOG_PATH)
        row = build_ai_decision_trace_row(
            system_prompt=system_prompt,
            user_message=user_message,
            raw_response=raw_response,
            result=result,
            usage=usage,
            symbol=symbol,
            candle_time=candle_time,
            kill_zone=kill_zone,
            model=model,
            backend_mode=backend_mode,
            response_status=response_status,
            parse_attempts=parse_attempts,
            config=config,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        return row
    except Exception as exc:  # noqa: BLE001 - diagnostic logging cannot affect trading
        logger.warning("ai_decision_trace_logger failed: %s", exc, exc_info=True)
        return None


__all__ = [
    "SCHEMA_VERSION",
    "SHADOW_LOG_PATH",
    "build_ai_decision_trace_row",
    "record_ai_decision_trace",
]
