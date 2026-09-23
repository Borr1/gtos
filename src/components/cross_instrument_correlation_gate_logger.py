"""Cross-instrument correlation gate decision logger.

Observation-only JSONL capture for the additive cross-instrument correlation
gate. The logger is deliberately failure-isolated: if row construction or disk
I/O fails, the gate result returned by ``cross_instrument_correlation_gate`` is
unchanged.

Output: ``shadow_logs/cross_instrument_correlation_decisions.jsonl``.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/cross_instrument_correlation_decisions.jsonl"


def _logger_enabled(config: Optional[dict[str, Any]]) -> bool:
    if not config:
        return False
    try:
        logger_cfg = (config.get("shadow_loggers", {}) or {}).get(
            "cross_instrument_correlation_decisions_logger", {}
        ) or {}
        return bool(logger_cfg.get("enabled", False))
    except Exception:
        return False


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_positions(positions: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(positions, list):
        return out
    for pos in positions:
        if not isinstance(pos, dict):
            continue
        out.append(
            {
                "symbol": str(pos.get("symbol") or ""),
                "direction": str(pos.get("direction") or ""),
                "correlation": _safe_float(pos.get("correlation")),
            }
        )
    return out


def log_cross_instrument_correlation_decision(
    *,
    candidate_symbol: str,
    candidate_direction: str,
    result: Any,
    config: Optional[dict[str, Any]],
    evaluation_context: str | None = None,
    log_path: str | None = None,
) -> None:
    """Append one cross-instrument correlation decision row.

    This function must never raise into the gate path.
    """
    try:
        if not _logger_enabled(config):
            return

        correlated_positions = _safe_positions(getattr(result, "correlated_positions", []))
        row = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "candidate_symbol": candidate_symbol,
            "candidate_direction": candidate_direction,
            "evaluation_context": evaluation_context,
            "gate_action": str(getattr(result, "action", "")),
            "risk_multiplier": _safe_float(getattr(result, "risk_multiplier", None)),
            "cluster_size": len(correlated_positions),
            "correlated_positions": correlated_positions,
            "threshold": _safe_float(getattr(result, "threshold", None)),
            "min_positions": _safe_int(getattr(result, "min_positions", None)),
            "reason": str(getattr(result, "reason", "")),
        }
        path = Path(log_path or SHADOW_LOG_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:  # noqa: BLE001 - must never affect gate behavior
        logger.warning(
            "cross_instrument_correlation_gate_logger failed: %s",
            exc,
            exc_info=True,
        )


__all__ = [
    "SHADOW_LOG_PATH",
    "log_cross_instrument_correlation_decision",
]
