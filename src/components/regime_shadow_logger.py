"""Regime Shadow Logger — observation-only.

For every M15 close, classify the current regime per-instrument via
:func:`src.components.regime_classifier.classify_regime` and append a
single JSONL row to ``shadow_logs/regime_classifications.jsonl``.

NO DECISION IMPACT. The classifier output is never consulted by
``permissions.py``, the AI prompt, the execution path, or any other
trade-relevant code path. This logger is a pure side-channel that
collects ground truth so the companion analysis script
``scripts/regime_outcome_correlation.py`` can later answer:

  - WR / Exp R / count per regime label
  - whether regime correlates with realized R
  - whether AI selectivity differs across regimes

Promotion gating — NOT enforced here, this module only produces the data:

    * >= 14-30 days of shadow data
    * cross-reference with knowledge_base/trade_records/ outcomes
    * CEO greenlight
    * promotion likely lands first as a PROMPT hint to the AI before
      any hard gate in ``permissions.py``.

Design references
-----------------
* Pattern: ``proximity_shadow_logger.py``, ``be_shadow_logger.py``,
  ``structure_detector_shadow_logger.py``. Common contract:
    - JSONL append-only log under ``shadow_logs/``.
    - ``log_path`` parameterised so tests can redirect to ``tmp_path``.
    - Every IO wrapped in try/except — a logger crash MUST NOT break
      the production pipeline (this is the "additive logger" rule
      from CLAUDE.md §What is unresolved item 4 + the Apr 16 silent
      crash incident).
    - No mutation of the MSO or any other shared state.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.components.regime_classifier import (
    DEFAULT_LOOKBACK_H4,
    classify_regime,
)
from src.models.market_state_models import MarketStateObject

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/regime_classifications.jsonl"


# ---------------------------------------------------------------------------
# Row builder
# ---------------------------------------------------------------------------

def build_regime_row(
    *,
    symbol: str,
    candle_time: str,
    regime: str,
    classifier_version: str,
    lookback: int,
    raw_features: dict,
    reason: str = "",
    logged_at: Optional[str] = None,
) -> dict[str, Any]:
    """Assemble the JSONL row for one regime classification.

    Schema (intentionally flat for easy ``jq`` / pandas ingestion)::

        {
          "ts": "2026-04-25T14:15:00Z",        # candle close (UTC)
          "logged_at": "2026-04-25T14:15:02Z", # write timestamp
          "symbol": "XAUUSD",
          "regime": "trending_bull",
          "classifier_version": "v1.0-option-a-h4-swing",
          "lookback": 20,
          "reason": "H4 net score=8 > dead_zone=2; HH+HL dominant.",
          "raw_features": {...}                # pass-through
        }

    Both candle_time and logged_at are kept — candle_time is what an
    analyst joins on (it matches the M15 close stamped into other
    shadow logs + trade records); logged_at is an audit trail for
    write latency / clock-skew debugging.
    """
    if logged_at is None:
        logged_at = datetime.now(timezone.utc).isoformat()
    return {
        "ts": candle_time,
        "logged_at": logged_at,
        "symbol": symbol,
        "regime": regime,
        "classifier_version": classifier_version,
        "lookback": int(lookback),
        "reason": reason,
        "raw_features": raw_features,
    }


# ---------------------------------------------------------------------------
# Main entry point — used by orchestrator
# ---------------------------------------------------------------------------

def log_classification(
    mso: Optional[MarketStateObject],
    *,
    symbol: str,
    candle_time: Optional[str] = None,
    lookback_h4_candles: int = DEFAULT_LOOKBACK_H4,
    log_path: str = SHADOW_LOG_PATH,
) -> Optional[str]:
    """Classify and persist regime for one M15 close.

    Returns the regime label written (string) on success, or ``None``
    if the IO failed. The caller (orchestrator) must NOT branch on
    this — it's only useful for tests + debugging.

    All exceptions are swallowed and logged at WARNING. The
    "additive logger never breaks the pipeline" rule applies here as
    in every other shadow logger in this repo.

    Parameters
    ----------
    mso:
        :class:`MarketStateObject` or ``None``. Forwarded to
        ``classify_regime`` (which itself handles the None branch).
    symbol:
        Canonical instrument symbol (XAUUSD, US30, etc.) — copied
        verbatim into the row for downstream filtering.
    candle_time:
        UTC candle close timestamp. Falls back to
        ``mso.timestamp_utc`` and then ``datetime.now(utc)`` when not
        supplied. Tests pin this to make assertions deterministic.
    lookback_h4_candles:
        Forwarded to ``classify_regime``.
    log_path:
        Defaults to the production path. Tests pass ``tmp_path``
        strings to isolate writes.
    """
    try:
        classification = classify_regime(
            mso, lookback_h4_candles=lookback_h4_candles
        )

        # Resolve candle_time with sensible fallbacks.
        ts = candle_time
        if not ts and mso is not None:
            ts = getattr(mso, "timestamp_utc", "") or ""
        if not ts:
            ts = datetime.now(timezone.utc).isoformat()

        row = build_regime_row(
            symbol=symbol,
            candle_time=ts,
            regime=classification.regime,
            classifier_version=classification.classifier_version,
            lookback=classification.lookback_h4_candles,
            raw_features=classification.raw_features,
            reason=classification.reason,
        )

        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(row) + "\n")

        logger.info(
            "REGIME_SHADOW: symbol=%s regime=%s ts=%s",
            symbol,
            classification.regime,
            ts,
        )
        return classification.regime

    except Exception as e:  # pragma: no cover — defensive; unit-tested
        # Never allow a logger failure to break the production pipeline.
        logger.warning(
            "REGIME_SHADOW: failed to log classification (non-blocking): %s",
            e,
        )
        return None


__all__ = [
    "SHADOW_LOG_PATH",
    "build_regime_row",
    "log_classification",
]
