"""Structured per-evaluation logging for WF-1 data collection.

Writes one JSONL record per AI evaluation (CANDIDATE, NO_TRADE, WAIT).
Full reasoning text is saved for CANDIDATEs and sampled NO_TRADEs.

HALLUC-2 (2026-04-27) extends the schema with an optional ``usage`` block
that captures Anthropic SDK token counts per evaluation. When the caller
does not pass usage data the field is omitted from the JSONL row, which
preserves backward-compatibility for existing readers and historical
records (`knowledge_base/live_evaluations/` had ZERO ``usage`` fields
prior to this change). Closes the observability gap surfaced in
``research/audit_2026_04_26/21_anthropic_telegram.md`` and in the
HALLUC-2 token-correlation research (commit ``fde8ca7``).
"""

import json
import os
import random
import re
from datetime import datetime, timezone
from typing import Optional


# Canonical key set for the persisted ``usage`` block. Locked here so test
# suites can pin the contract; downstream cost / decay analysis joins on
# these names. Add new keys at the END of the tuple to keep diff hygiene.
USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
    "cache_creation_5m_tokens",
    "cache_creation_1h_tokens",
)


class EvaluationLogger:
    """Append-only JSONL logger for every candle evaluation."""

    def __init__(self, base_dir: str = "knowledge_base/live_evaluations"):
        self.base_dir = base_dir
        self._prev_decision: Optional[str] = None
        self._candle_index_in_kz: int = 0
        self._current_kz: Optional[str] = None

    def reset_session(self):
        """Call at the start of each kill zone window."""
        self._prev_decision = None
        self._candle_index_in_kz = 0
        self._current_kz = None

    def log_evaluation(
        self,
        symbol: str,
        candle_time: str,
        kill_zone: str,
        analysis_dict: dict,
        session_memory_count: int,
        align_score: Optional[int],
        spread: Optional[float],
        usage: Optional[dict] = None,
    ):
        """Log structured data from every AI evaluation.

        *analysis_dict* should be ``analysis.model_dump(mode="json")``.
        *usage* is the optional Anthropic SDK token-usage block. The
        logger accepts EITHER the SDK's native field names
        (``cache_read_input_tokens`` / ``cache_creation_input_tokens``)
        OR the simplified shape stored on
        ``PrimaryAnalyzer._last_usage`` (``cache_read_tokens`` /
        ``cache_create_tokens``); both are normalised to the canonical
        keys in :data:`USAGE_FIELDS`. When ``usage`` is ``None`` the
        field is OMITTED from the JSONL row to preserve byte-for-byte
        backward compatibility with pre-HALLUC-2 records.
        """
        if kill_zone != self._current_kz:
            self._current_kz = kill_zone
            self._candle_index_in_kz = 0
        else:
            self._candle_index_in_kz += 1

        reasoning = analysis_dict.get("reasoning") or {}
        decision = analysis_dict.get("decision", "UNKNOWN")

        save_full = self._should_save_full_reasoning(decision)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candle_time": candle_time,
            "symbol": symbol,
            "kill_zone": kill_zone,
            "decision": decision,

            # Per-step outputs
            "daily_bias_direction": _deep(reasoning, "daily_bias", "direction"),
            "daily_bias_confidence": _deep(reasoning, "daily_bias", "confidence"),
            "h4_aligned": _deep(reasoning, "h4_alignment", "aligned"),
            "h1_poi_identified": _deep(reasoning, "h1_setup", "poi_identified"),
            "h1_poi_type": _deep(reasoning, "h1_setup", "poi_type"),
            "h1_zone": _deep(reasoning, "h1_setup", "zone"),
            "h1_fib_pct": _deep(reasoning, "h1_setup", "fib_retracement_pct"),
            "h1_causing_event": _deep(reasoning, "h1_setup", "causing_event_type"),
            "sweep_detected": _deep(reasoning, "liquidity_sweep", "detected"),
            "sweep_type": _deep(reasoning, "liquidity_sweep", "pool_type"),
            "sweep_quality": _deep(reasoning, "liquidity_sweep", "sweep_quality"),
            "m15_choch": _deep(reasoning, "m15_confirmation", "choch_detected"),
            "m15_displacement_quality": _deep(reasoning, "m15_confirmation", "displacement_quality"),
            "m15_displacement_ratio": _deep(reasoning, "m15_confirmation", "displacement_candle_body_vs_avg_ratio"),
            "setup_grade": reasoning.get("setup_grade"),
            "confidence_score": analysis_dict.get("confidence_score"),
            "framework": analysis_dict.get("framework"),

            # Context state
            "session_memory_count": session_memory_count,
            "align_score": align_score,
            "spread": spread,
            "candle_index_in_kz": self._candle_index_in_kz,

            # NO_TRADE / WAIT reason
            "no_trade_reason": analysis_dict.get("no_trade_reason"),
            "wait_reason": analysis_dict.get("wait_reason"),

            # Reasoning text metrics (always computed)
            "reasoning_word_count": _word_count(reasoning.get("overall_reasoning", "")),
            "reasoning_price_count": _count_prices(reasoning.get("overall_reasoning", "")),
        }

        # Token usage — additive, optional, omitted on None for byte-level
        # backward compatibility with pre-HALLUC-2 records.
        if usage is not None:
            normalised = _normalise_usage(usage)
            if normalised is not None:
                record["usage"] = normalised

        # Full reasoning text — only for CANDIDATE and sampled NO_TRADEs
        if save_full:
            record["overall_reasoning"] = reasoning.get("overall_reasoning", "")

        self._prev_decision = decision
        self._write(symbol, candle_time, record)

    def _should_save_full_reasoning(self, decision: str) -> bool:
        if decision != "NO_TRADE":
            return True
        if self._candle_index_in_kz == 0:
            return True
        if self._prev_decision and self._prev_decision != "NO_TRADE":
            return True
        return random.random() < 0.2

    def _write(self, symbol: str, candle_time: str, record: dict):
        dir_path = os.path.join(self.base_dir, symbol)
        os.makedirs(dir_path, exist_ok=True)

        date_str = candle_time[:10] if candle_time else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        file_path = os.path.join(dir_path, f"{date_str}.jsonl")

        with open(file_path, "a") as f:
            f.write(json.dumps(record, default=str) + "\n")


def _deep(d: dict, *keys):
    """Safe nested dict access."""
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _word_count(text: str) -> int:
    return len(text.split()) if text else 0


def _count_prices(text: str) -> int:
    if not text:
        return 0
    return len(set(re.findall(r"\d{3,5}\.\d{1,2}", text)))


def _coerce_int(val) -> int:
    """Coerce a value to int; non-numeric / None becomes 0.

    Mirrors ``research_infra.cost_tracker._normalize_usage`` semantics so
    the two paths agree on how SDK fields map to integers.
    """
    try:
        return int(val) if val is not None else 0
    except (TypeError, ValueError):
        return 0


def _normalise_usage(usage) -> Optional[dict]:
    """Project an SDK or analyzer usage dict to the canonical log schema.

    Accepts:
      * Anthropic SDK ``response.usage`` shape (input_tokens,
        output_tokens, cache_read_input_tokens,
        cache_creation_input_tokens, cache_creation.ephemeral_5m_input_tokens,
        cache_creation.ephemeral_1h_input_tokens) — exposed either as
        attributes on the SDK object or as keys on a dict.
      * ``PrimaryAnalyzer._last_usage`` simplified shape
        (cache_read_tokens / cache_create_tokens). The simplified shape
        does not split 5m vs 1h ephemeral; those fields default to 0.

    Returns the canonical dict (keys :data:`USAGE_FIELDS`) or ``None``
    when the input is unusable. ``None`` is propagated by the caller so
    the JSONL row simply omits the ``usage`` field — preserving the
    byte-level historical schema for records lacking usage data.
    """
    if usage is None:
        return None

    # Accept either dicts or duck-typed SDK objects. Prefer dict-style
    # access, fall back to attribute access. Strip the analyzer's
    # private ``_fresh`` sentinel — it's an implementation detail of the
    # multi-call accumulator, not part of the persisted contract.
    def _get(name, default=None):
        if isinstance(usage, dict):
            return usage.get(name, default)
        return getattr(usage, name, default)

    # Native SDK exposes ephemeral 5m/1h via a nested ``cache_creation``
    # object (Anthropic SDK ≥0.40). Fall back to flat
    # ``cache_creation_*_tokens`` for callers that already pre-flattened.
    cache_creation_obj = _get("cache_creation")
    five_m = _get("cache_creation_5m_tokens")
    one_h = _get("cache_creation_1h_tokens")
    if cache_creation_obj is not None:
        if isinstance(cache_creation_obj, dict):
            five_m = cache_creation_obj.get("ephemeral_5m_input_tokens", five_m)
            one_h = cache_creation_obj.get("ephemeral_1h_input_tokens", one_h)
        else:
            five_m = getattr(cache_creation_obj, "ephemeral_5m_input_tokens", five_m)
            one_h = getattr(cache_creation_obj, "ephemeral_1h_input_tokens", one_h)

    # Bridge the analyzer's simplified key names to canonical SDK names.
    cache_read = _get("cache_read_input_tokens")
    if cache_read is None:
        cache_read = _get("cache_read_tokens")
    cache_create = _get("cache_creation_input_tokens")
    if cache_create is None:
        cache_create = _get("cache_create_tokens")

    return {
        "input_tokens": _coerce_int(_get("input_tokens")),
        "output_tokens": _coerce_int(_get("output_tokens")),
        "cache_read_input_tokens": _coerce_int(cache_read),
        "cache_creation_input_tokens": _coerce_int(cache_create),
        "cache_creation_5m_tokens": _coerce_int(five_m),
        "cache_creation_1h_tokens": _coerce_int(one_h),
    }
