"""L-6 reference impl — HALLUC-2 token-usage logger (call-grain).

DESIGN-ONLY MODULE. Lives under research/ for review, NOT under src/. Main
thread copies the relevant pieces into src/components/ after CEO approval per
the design doc at research/ml_program/experiments/l6_l7_logger_design.md.

Records ONE jsonl row per Anthropic API call — distinct from the
``evaluation_logger.log_evaluation(usage=...)`` path which writes one row per
M15 evaluation (1-3 API calls fold into a single eval row, hiding retry
waste). This logger gives call-grain telemetry: cost in USD, latency,
prompt-hash for cache-debug, role tag for retry-vs-first-call separation,
call_id correlation key.

Reuses pricing math from ``src/research_infra/cost_tracker.compute_cost`` to
keep a single source of truth for the pricing table.

Fail-open: any exception inside the logger is caught and downgraded to a
WARNING; trading flow MUST NEVER block on a shadow-log write. Mirrors the
canonical pattern in ``src/components/slippage_shadow_logger.py``.

Tests at the bottom of this file run standalone:
    python -m pytest research/ml_program/experiments/l6_token_usage_logger.py
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default sink. Tests redirect via ``log_path`` keyword on log_call APIs OR
# by monkey-patching this module attribute.
SHADOW_LOG_PATH = "shadow_logs/token_usage.jsonl"


# Canonical role tags. Free-form strings are accepted (logger never rejects
# unknown roles) but these are the documented values consumers can rely on.
ROLE_PRIMARY = "primary"
ROLE_PRIMARY_RETRY_FORMAT = "primary_retry_format"
ROLE_PRIMARY_RETRY_TIMEOUT = "primary_retry_timeout"
ROLE_PRIMARY_RETRY_RATE_LIMIT = "primary_retry_rate_limit"
ROLE_PRIMARY_RETRY_500 = "primary_retry_500"
ROLE_BATCH = "batch"
ROLE_CANARY = "canary"


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        return int(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _hash_prompt(system_blocks: Any) -> Optional[str]:
    """SHA-256 (16-hex truncated) of system prompt content for cache-debug.

    Accepts the str-or-list-of-content-blocks shape the SDK uses. Returns None
    on any error (logger fail-open contract).
    """
    try:
        if system_blocks is None:
            return None
        if isinstance(system_blocks, str):
            payload = system_blocks
        elif isinstance(system_blocks, list):
            # List of content blocks — concat each block's "text" field.
            chunks = []
            for blk in system_blocks:
                if isinstance(blk, dict) and "text" in blk:
                    chunks.append(str(blk["text"]))
                else:
                    chunks.append(str(blk))
            payload = "\n".join(chunks)
        else:
            payload = str(system_blocks)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return None


def _compute_cost_safe(
    *, model: str, usage: dict, is_batch: bool, cache_ttl: str
) -> tuple[Optional[dict], Optional[float]]:
    """Compute cost via cost_tracker if importable; fail-open to (None, None).

    The reference impl does NOT hard-import ``src.research_infra.cost_tracker``
    so this module is unit-testable in isolation. Production wiring imports
    it directly; the try/except below is the test-isolation hatch.
    """
    try:
        # Local import keeps test isolation; main-thread integration may
        # promote this to a top-level import.
        from src.research_infra.cost_tracker import compute_cost  # type: ignore
    except Exception:
        return None, None
    try:
        breakdown, total, _norm = compute_cost(
            model=model,
            usage=usage,
            is_batch=is_batch,
            cache_ttl=cache_ttl,
        )
        return breakdown, total
    except Exception as exc:
        logger.debug("cost compute failed (non-blocking): %s", exc)
        return None, None


class TokenUsageLogger:
    """Stateful helper for the call-start / call-end pattern.

    The PrimaryAnalyzer wires one instance at __init__ time; each
    ``client.messages.create(...)`` site brackets the call with
    ``start_call`` and ``log_success``/``log_failure``. The logger stores
    only per-call state (start time, call_id) keyed by call_id so multiple
    in-flight calls (future tool_use roundtrips) cannot collide.
    """

    def __init__(self, log_path: Optional[str] = None) -> None:
        # Path resolution at write time (not init) so tests can monkey-patch
        # ``SHADOW_LOG_PATH`` after construction.
        self._explicit_log_path = log_path
        self._inflight: dict[str, dict] = {}

    @property
    def log_path(self) -> str:
        """Re-read on every write so monkey-patching ``SHADOW_LOG_PATH`` works."""
        return self._explicit_log_path or SHADOW_LOG_PATH

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_call(
        self,
        *,
        symbol: Optional[str] = None,
        kill_zone: Optional[str] = None,
        candle_time: Optional[str] = None,
        model: str,
        primary_effort: Optional[str] = None,
        role: str = ROLE_PRIMARY,
        attempt: int = 1,
        backend_mode: str = "api",
        system_blocks: Any = None,
        is_batch: bool = False,
        cache_ttl: str = "1h",
    ) -> str:
        """Record call start. Returns a fresh call_id to pass back to log_*."""
        call_id = uuid.uuid4().hex  # 32 chars; collision probability is fine
        try:
            self._inflight[call_id] = {
                "t0_ns": time.perf_counter_ns(),
                "symbol": symbol,
                "kill_zone": kill_zone,
                "candle_time": candle_time,
                "model": model,
                "primary_effort": primary_effort,
                "role": role,
                "attempt": int(attempt),
                "backend_mode": backend_mode,
                "prompt_hash": _hash_prompt(system_blocks),
                "is_batch": bool(is_batch),
                "cache_ttl": cache_ttl,
            }
        except Exception as exc:
            # Even the start-call bookkeeping is fail-open. If we fail here,
            # log_success / log_failure simply skip writing — caller never
            # learns. Acceptable for a shadow logger.
            logger.warning("token_usage_logger start_call failed: %s", exc)
        return call_id

    def log_success(
        self,
        call_id: str,
        response: Any,
        *,
        cache_ttl: Optional[str] = None,
    ) -> None:
        """Write the success row for ``call_id`` from an SDK response object.

        ``response`` must expose ``response.usage.input_tokens / output_tokens
        / cache_read_input_tokens / cache_creation_input_tokens`` and
        optionally ``response.id`` + ``response.model``. Pulled defensively
        with getattr — missing fields default to 0/null.
        """
        meta = self._inflight.pop(call_id, None)
        if meta is None:
            logger.debug("token_usage_logger log_success: unknown call_id=%s", call_id)
            return
        try:
            latency_ms = (time.perf_counter_ns() - int(meta.get("t0_ns") or 0)) // 1_000_000
            usage = getattr(response, "usage", None)
            input_tokens = _safe_int(getattr(usage, "input_tokens", 0))
            output_tokens = _safe_int(getattr(usage, "output_tokens", 0))
            cache_read = _safe_int(getattr(usage, "cache_read_input_tokens", 0))
            cache_create = _safe_int(getattr(usage, "cache_creation_input_tokens", 0))
            served_model_id = getattr(response, "model", None)
            response_id = getattr(response, "id", None)

            effective_ttl = cache_ttl or meta.get("cache_ttl") or "none"
            usage_dict = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_create,
            }

            cost_breakdown: Optional[dict] = None
            total_cost_usd: Optional[float] = None
            notes: Optional[str] = None
            if meta.get("backend_mode") == "subscription":
                # Subscription mode does not bill against the $50/mo cap.
                # See memory feedback_billing_tracks_distinction.
                cost_breakdown = {
                    "input": 0.0, "output": 0.0,
                    "cache_write": 0.0, "cache_read": 0.0,
                }
                total_cost_usd = 0.0
            else:
                cost_breakdown, total_cost_usd = _compute_cost_safe(
                    model=meta["model"],
                    usage=usage_dict,
                    is_batch=bool(meta.get("is_batch")),
                    cache_ttl=effective_ttl,
                )
                if cost_breakdown is None:
                    notes = f"unknown_model_or_pricing_error:{meta.get('model')}"

            self._write_row(
                meta=meta,
                latency_ms=int(latency_ms),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read=cache_read,
                cache_create=cache_create,
                effective_ttl=effective_ttl,
                cost_breakdown=cost_breakdown,
                total_cost_usd=total_cost_usd,
                served_model_id=served_model_id,
                response_id=response_id,
                call_id=call_id,
                outcome="success",
                exception_class=None,
                notes=notes,
            )
        except Exception as exc:
            logger.warning(
                "token_usage_logger log_success failed (non-blocking): %s "
                "[call_id=%s]", exc, call_id,
            )

    def log_failure(
        self, call_id: str, exception_class: str = "Unknown",
    ) -> None:
        """Write the failure row for ``call_id`` (timeout / 500 / rate-limit / etc).

        ``exception_class`` should be ``type(exc).__name__`` from the caller —
        ``"AnthropicTimeoutError"`` etc. Recorded so analysts can compute
        retry-rate per exception class.
        """
        meta = self._inflight.pop(call_id, None)
        if meta is None:
            logger.debug("token_usage_logger log_failure: unknown call_id=%s", call_id)
            return
        try:
            latency_ms = (time.perf_counter_ns() - int(meta.get("t0_ns") or 0)) // 1_000_000
            self._write_row(
                meta=meta,
                latency_ms=int(latency_ms),
                input_tokens=0,
                output_tokens=0,
                cache_read=0,
                cache_create=0,
                effective_ttl=meta.get("cache_ttl", "none"),
                cost_breakdown={
                    "input": 0.0, "output": 0.0,
                    "cache_write": 0.0, "cache_read": 0.0,
                },
                total_cost_usd=0.0,
                served_model_id=None,
                response_id=None,
                call_id=call_id,
                outcome="failure",
                exception_class=exception_class,
                notes=None,
            )
        except Exception as exc:
            logger.warning(
                "token_usage_logger log_failure failed (non-blocking): %s "
                "[call_id=%s]", exc, call_id,
            )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _write_row(
        self,
        *,
        meta: dict,
        latency_ms: int,
        input_tokens: int,
        output_tokens: int,
        cache_read: int,
        cache_create: int,
        effective_ttl: str,
        cost_breakdown: Optional[dict],
        total_cost_usd: Optional[float],
        served_model_id: Optional[str],
        response_id: Optional[str],
        call_id: str,
        outcome: str,
        exception_class: Optional[str],
        notes: Optional[str],
    ) -> None:
        """Append one jsonl row. Single source of truth for the schema."""
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "call_id": call_id,
            "symbol": meta.get("symbol"),
            "kill_zone": meta.get("kill_zone"),
            "candle_time": meta.get("candle_time"),
            "model": meta.get("model"),
            "primary_effort": meta.get("primary_effort"),
            "role": meta.get("role"),
            "attempt": int(meta.get("attempt") or 1),
            "input_tokens": input_tokens,
            "cache_read_tokens": cache_read,
            "cache_creation_tokens": cache_create,
            "output_tokens": output_tokens,
            "cache_ttl": effective_ttl,
            "is_batch": bool(meta.get("is_batch")),
            "cost_usd_breakdown": cost_breakdown,
            "total_cost_usd": total_cost_usd,
            "latency_ms": int(latency_ms),
            "prompt_hash": meta.get("prompt_hash"),
            "served_model_id": served_model_id,
            "response_id": response_id,
            "backend_mode": meta.get("backend_mode", "api"),
            "outcome": outcome,
            "exception_class": exception_class,
            "notes": notes,
        }
        path = Path(self.log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


# ============================================================================
# Tests
# ============================================================================
# Self-contained pytest tests — run with:
#     python -m pytest research/ml_program/experiments/l6_token_usage_logger.py


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class _FakeUsage:
    """Mimics the Anthropic SDK's response.usage shape."""

    def __init__(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_input_tokens: int = 0,
        cache_creation_input_tokens: int = 0,
    ):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_read_input_tokens = cache_read_input_tokens
        self.cache_creation_input_tokens = cache_creation_input_tokens


class _FakeResponse:
    """Mimics the Anthropic SDK's response object."""

    def __init__(self, usage: _FakeUsage, *, id: str = "msg_test", model: str = "claude-sonnet-4-6-20260201"):
        self.usage = usage
        self.id = id
        self.model = model
        self.content = [type("Block", (), {"text": "ok"})()]


def test_log_success_writes_canonical_schema(tmp_path):
    log = TokenUsageLogger(log_path=str(tmp_path / "tu.jsonl"))
    cid = log.start_call(
        symbol="XAUUSD", kill_zone="london",
        candle_time="2026-04-29T08:00:00+00:00",
        model="claude-sonnet-4-6", primary_effort="max",
        role=ROLE_PRIMARY, attempt=1,
        system_blocks=[{"type": "text", "text": "hello"}],
        cache_ttl="1h",
    )
    response = _FakeResponse(_FakeUsage(150, 800, 12000, 0))
    log.log_success(cid, response)

    rows = _read_rows(Path(log.log_path))
    assert len(rows) == 1
    r = rows[0]
    canonical_keys = {
        "timestamp", "call_id", "symbol", "kill_zone", "candle_time",
        "model", "primary_effort", "role", "attempt",
        "input_tokens", "cache_read_tokens", "cache_creation_tokens",
        "output_tokens", "cache_ttl", "is_batch",
        "cost_usd_breakdown", "total_cost_usd", "latency_ms",
        "prompt_hash", "served_model_id", "response_id",
        "backend_mode", "outcome", "exception_class", "notes",
    }
    assert canonical_keys == set(r.keys()), f"missing or extra keys: {canonical_keys ^ set(r.keys())}"
    assert r["symbol"] == "XAUUSD"
    assert r["model"] == "claude-sonnet-4-6"
    assert r["input_tokens"] == 150
    assert r["cache_read_tokens"] == 12000
    assert r["output_tokens"] == 800
    assert r["outcome"] == "success"
    assert r["prompt_hash"] is not None and len(r["prompt_hash"]) == 16


def test_log_success_handles_cache_hit(tmp_path):
    log = TokenUsageLogger(log_path=str(tmp_path / "tu.jsonl"))
    cid = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY, cache_ttl="1h")
    log.log_success(cid, _FakeResponse(_FakeUsage(150, 800, 12000, 0)))
    rows = _read_rows(Path(log.log_path))
    assert rows[0]["cache_read_tokens"] == 12000
    assert rows[0]["cache_creation_tokens"] == 0
    if rows[0]["total_cost_usd"] is not None:
        # If cost_tracker is importable, verify magnitude.
        assert rows[0]["total_cost_usd"] > 0
        assert rows[0]["cost_usd_breakdown"]["cache_read"] > 0


def test_log_success_handles_cache_miss(tmp_path):
    log = TokenUsageLogger(log_path=str(tmp_path / "tu.jsonl"))
    cid = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY, cache_ttl="1h")
    log.log_success(cid, _FakeResponse(_FakeUsage(150, 800, 0, 12000)))
    rows = _read_rows(Path(log.log_path))
    assert rows[0]["cache_read_tokens"] == 0
    assert rows[0]["cache_creation_tokens"] == 12000


def test_log_failure_writes_zero_cost(tmp_path):
    log = TokenUsageLogger(log_path=str(tmp_path / "tu.jsonl"))
    cid = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY)
    log.log_failure(cid, exception_class="AnthropicTimeoutError")
    rows = _read_rows(Path(log.log_path))
    assert rows[0]["total_cost_usd"] == 0.0
    assert rows[0]["outcome"] == "failure"
    assert rows[0]["exception_class"] == "AnthropicTimeoutError"
    assert rows[0]["input_tokens"] == 0


def test_log_subscription_mode_writes_zero_cost(tmp_path):
    log = TokenUsageLogger(log_path=str(tmp_path / "tu.jsonl"))
    cid = log.start_call(model="claude-sonnet-4-6", backend_mode="subscription", role=ROLE_PRIMARY)
    log.log_success(cid, _FakeResponse(_FakeUsage(150, 800, 0, 0)))
    rows = _read_rows(Path(log.log_path))
    assert rows[0]["total_cost_usd"] == 0.0
    assert rows[0]["backend_mode"] == "subscription"


def test_log_unknown_model_does_not_raise(tmp_path):
    log = TokenUsageLogger(log_path=str(tmp_path / "tu.jsonl"))
    cid = log.start_call(model="claude-foo-9-9", role=ROLE_PRIMARY)
    log.log_success(cid, _FakeResponse(_FakeUsage(150, 800, 0, 0)))
    rows = _read_rows(Path(log.log_path))
    assert len(rows) == 1
    # When cost_tracker is reachable but model is unknown, total_cost_usd
    # is None and notes carries the error tag. When cost_tracker is NOT
    # reachable from the test env, total_cost_usd is also None.
    assert rows[0]["total_cost_usd"] is None
    # In subscription mode this would be 0.0, but we used api mode here.


def test_call_id_unique_across_retries(tmp_path):
    log = TokenUsageLogger(log_path=str(tmp_path / "tu.jsonl"))
    ids = []
    for attempt in (1, 2, 3):
        cid = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY, attempt=attempt)
        ids.append(cid)
        log.log_success(cid, _FakeResponse(_FakeUsage(1, 1, 0, 0)))
    rows = _read_rows(Path(log.log_path))
    assert len(rows) == 3
    assert len(set(r["call_id"] for r in rows)) == 3
    assert [r["attempt"] for r in rows] == [1, 2, 3]


def test_prompt_hash_stable_for_same_prompt(tmp_path):
    log = TokenUsageLogger(log_path=str(tmp_path / "tu.jsonl"))
    blocks = [{"type": "text", "text": "static system prompt"}]
    h1 = []
    for _ in range(2):
        cid = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY,
                             system_blocks=blocks, cache_ttl="1h")
        log.log_success(cid, _FakeResponse(_FakeUsage(1, 1, 0, 0)))
    rows = _read_rows(Path(log.log_path))
    assert len(rows) == 2
    assert rows[0]["prompt_hash"] == rows[1]["prompt_hash"]
    # Different prompt → different hash.
    cid = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY,
                         system_blocks=[{"type": "text", "text": "different"}])
    log.log_success(cid, _FakeResponse(_FakeUsage(1, 1, 0, 0)))
    rows = _read_rows(Path(log.log_path))
    assert rows[2]["prompt_hash"] != rows[0]["prompt_hash"]


def test_log_path_override_for_isolation(tmp_path):
    custom = tmp_path / "custom.jsonl"
    log = TokenUsageLogger(log_path=str(custom))
    cid = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY)
    log.log_success(cid, _FakeResponse(_FakeUsage(1, 1, 0, 0)))
    assert custom.exists()
    # Default sink untouched.
    assert not (tmp_path / "shadow_logs").exists()


def test_role_tags_distinguish_first_vs_retry(tmp_path):
    log = TokenUsageLogger(log_path=str(tmp_path / "tu.jsonl"))
    cid1 = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY, attempt=1)
    log.log_success(cid1, _FakeResponse(_FakeUsage(1, 1, 0, 0)))
    cid2 = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY_RETRY_FORMAT, attempt=2)
    log.log_success(cid2, _FakeResponse(_FakeUsage(1, 1, 0, 0)))
    rows = _read_rows(Path(log.log_path))
    assert rows[0]["role"] == ROLE_PRIMARY
    assert rows[1]["role"] == ROLE_PRIMARY_RETRY_FORMAT


def test_jsonl_lines_parse_individually(tmp_path):
    log = TokenUsageLogger(log_path=str(tmp_path / "tu.jsonl"))
    for _ in range(5):
        cid = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY)
        log.log_success(cid, _FakeResponse(_FakeUsage(1, 1, 0, 0)))
    text = (tmp_path / "tu.jsonl").read_text(encoding="utf-8")
    for line in text.splitlines():
        assert json.loads(line)  # each line independently parseable


def test_failure_open_on_disk_error(tmp_path, monkeypatch):
    """Logger MUST swallow disk errors; trade flow must not depend on log success."""
    log = TokenUsageLogger(log_path=str(tmp_path / "no_dir" / "child" / "tu.jsonl"))

    def _explode(*a, **k):
        raise PermissionError("simulated")
    monkeypatch.setattr("builtins.open", _explode)

    cid = log.start_call(model="claude-sonnet-4-6", role=ROLE_PRIMARY)
    # Must not raise:
    log.log_success(cid, _FakeResponse(_FakeUsage(1, 1, 0, 0)))


if __name__ == "__main__":
    # Allow `python l6_token_usage_logger.py` to drive the tests when pytest
    # is unavailable. Imports lazily so the module stays useful as a library.
    try:
        import pytest  # type: ignore
        sys.exit(pytest.main([__file__, "-v"]))
    except ImportError:
        print("pytest not installed; skipping test run", file=sys.stderr)
        sys.exit(2)
