"""Anthropic Message Batches API wrapper for offline research workloads.

Phase 1 research infrastructure (T0.1). This is an ADDITIVE wrapper for the
async Message Batches endpoint — it does NOT touch the production sync path
(``src/llm_backend.py``) used by ``primary_analyzer.py``.

When to use this wrapper
------------------------
Use the batch API for any research workload where:
  * Results are not needed within seconds (24h SLA, typically <1h).
  * Cost matters: 50% discount on input + output tokens vs the sync API.
  * The job is large enough to amortize the polling overhead.

Do NOT use the batch API for:
  * Live trading-decision calls (those go through ``src/llm_backend.py``).
  * Any path where latency under a few minutes matters.

Design notes
------------
* Model-agnostic. Documented use is offline research (Haiku 4.5 for cheap
  scans, Sonnet 4.6 for high-fidelity backtests). The Sonnet 4.6 trading-gate
  decision lives in production code; do NOT route trading-decision calls
  through this wrapper.
* Cache-control passthrough. ``cache_control: {"type": "ephemeral"}`` blocks
  inside ``system``/``messages`` are forwarded verbatim to the SDK; both 5m
  default and 1h ttl are supported. The ``cache_ttl`` field on
  ``BatchRequest`` is INFORMATIONAL (audit/observability) — the actual cache
  contract is whatever the caller embeds inside the content blocks.
* Effort passthrough. ``output_config={"effort": "max"}`` is forwarded as the
  ``params.output_config`` block in the per-request payload.
* Idempotent retries. Network-class transients (5xx, connection errors,
  overload) trigger up to 3 retries with exponential backoff (1s/2s/4s
  base + jitter). 4xx (validation, auth, rate-limit policy) and 408/429-as-
  retry-after fall straight through to the caller.
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

CacheTTL = Literal["5m", "1h", "none"]
BatchStatus = Literal["in_progress", "ended", "canceled", "expired", "errored"]

# Anthropic limits (https://docs.claude.com/en/api/creating-message-batches)
MAX_REQUESTS_PER_BATCH: int = 100_000
DEFAULT_POLL_INTERVAL_SECONDS: int = 60
DEFAULT_MAX_WAIT_SECONDS: int = 24 * 60 * 60  # 24h SLA


@dataclass
class BatchRequest:
    """Single request inside a batch submission.

    Mirrors the ``BatchCreateParams.Request`` shape (``custom_id`` + ``params``)
    but flattened so callers do not need to import SDK types. Conversion to the
    SDK shape happens in ``BatchClient._to_sdk_request``.
    """

    custom_id: str
    """Unique-within-batch identifier. Used to match results back to inputs."""

    model: str
    """Model identifier (e.g. ``claude-haiku-4-5-20251001``)."""

    messages: list[dict]
    """User/assistant turn list, same shape as ``client.messages.create``."""

    max_tokens: int = 1024
    """Maximum output tokens for this request."""

    system: Any = None
    """Optional system prompt. Either a plain string or a list of content
    blocks (the prompt-caching shape, e.g.
    ``[{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}]``).
    Forwarded verbatim to the SDK."""

    output_config: Optional[dict] = None
    """Optional ``output_config`` block, e.g. ``{"effort": "max"}`` for
    extended-thinking. Forwarded verbatim to the SDK as
    ``params.output_config``."""

    cache_ttl: CacheTTL = "none"
    """Audit-only annotation of which cache TTL the caller intends. Does NOT
    by itself add cache_control — that lives inside ``system``/``messages``
    content blocks. Recorded so cost/observability tooling (T0.2) can join
    against it."""

    temperature: float = 0.0
    """Sampling temperature. Default 0 matches the production gate."""

    extra_params: Optional[dict] = None
    """Escape hatch for additional ``params.*`` fields not modelled above
    (e.g. ``stop_sequences``, ``metadata``). Merged last."""


@dataclass
class BatchResult:
    """Result for a single request inside a batch.

    On success, ``content_text`` is the concatenated text of all ``text``
    blocks in the message (matching ``LLMResponse.text`` semantics in
    ``src/llm_backend.py``). ``error`` is populated for ``errored`` /
    ``canceled`` / ``expired`` results — exactly one of ``content_text``
    (success) or ``error`` (failure) will be non-None.
    """

    custom_id: str
    content_text: Optional[str] = None
    stop_reason: Optional[str] = None
    usage: dict = field(default_factory=dict)
    """Raw usage block from the API. Keys include ``input_tokens``,
    ``output_tokens``, ``cache_creation_input_tokens``,
    ``cache_read_input_tokens``."""
    error: Optional[dict] = None
    """``{"type": "errored"|"canceled"|"expired", "detail": <api error or None>}``
    when the request did not succeed."""


# ---------------------------------------------------------------------------
# BatchClient
# ---------------------------------------------------------------------------


class BatchClient:
    """Wrapper around ``client.messages.batches.*`` with retries and polling.

    Parameters
    ----------
    api_key
        Optional Anthropic API key. If None, the SDK falls back to
        ``ANTHROPIC_API_KEY`` from the environment (matching the live wrapper
        in ``src/llm_backend.py``).
    polling_interval_seconds
        Sleep between status polls in :meth:`wait_and_fetch`. Defaults to 60s
        (the SDK's recommended cadence for a 24h job).
    max_wait_seconds
        Hard ceiling on :meth:`wait_and_fetch`. Defaults to 24h (the API's
        own expiry).
    sdk_client
        Dependency-injection seam for tests. If supplied, the wrapper uses it
        directly and ignores ``api_key``. In production code, leave None and
        the wrapper will lazy-init an :class:`anthropic.Anthropic` client.
    """

    # Status values the API may return on the ``processing_status`` field of
    # MessageBatch. ``request_counts`` is consulted for the terminal subdivision
    # (ended into succeeded/errored/canceled/expired counts).
    _PROCESSING_STATUS_TERMINAL = "ended"

    def __init__(
        self,
        api_key: Optional[str] = None,
        polling_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS,
        max_wait_seconds: int = DEFAULT_MAX_WAIT_SECONDS,
        sdk_client: Any = None,
    ) -> None:
        if polling_interval_seconds <= 0:
            raise ValueError("polling_interval_seconds must be > 0")
        if max_wait_seconds <= 0:
            raise ValueError("max_wait_seconds must be > 0")
        self._api_key = api_key
        self.polling_interval_seconds = polling_interval_seconds
        self.max_wait_seconds = max_wait_seconds
        self._sdk_client = sdk_client

    # ------------------------------------------------------------------
    # Lazy SDK client init
    # ------------------------------------------------------------------

    def _get_sdk_client(self) -> Any:
        if self._sdk_client is None:
            # Imported lazily so tests that inject ``sdk_client`` need no
            # ANTHROPIC_API_KEY in the environment and we don't pay the
            # import cost when the wrapper is unused.
            from anthropic import Anthropic

            kwargs: dict = {}
            if self._api_key is not None:
                kwargs["api_key"] = self._api_key
            elif not os.environ.get("ANTHROPIC_API_KEY"):
                raise RuntimeError(
                    "BatchClient requires either api_key= or ANTHROPIC_API_KEY env var"
                )
            self._sdk_client = Anthropic(**kwargs)
        return self._sdk_client

    # ------------------------------------------------------------------
    # Public API: submit / poll / fetch
    # ------------------------------------------------------------------

    def submit_batch(self, requests: list[BatchRequest]) -> str:
        """Submit a batch of requests and return the batch id.

        Validates non-empty / size-bound / dedup before any network call.
        """
        if not requests:
            raise ValueError("submit_batch requires a non-empty list of requests")
        if len(requests) > MAX_REQUESTS_PER_BATCH:
            raise ValueError(
                f"Batch size {len(requests)} exceeds API limit of "
                f"{MAX_REQUESTS_PER_BATCH} requests"
            )

        seen: set[str] = set()
        for r in requests:
            if not r.custom_id:
                raise ValueError("BatchRequest.custom_id must be a non-empty string")
            if r.custom_id in seen:
                raise ValueError(
                    f"Duplicate custom_id in batch: {r.custom_id!r} "
                    "(custom_id must be unique within a batch)"
                )
            seen.add(r.custom_id)

        sdk_requests = [self._to_sdk_request(r) for r in requests]

        def _do_create():
            client = self._get_sdk_client()
            return client.messages.batches.create(requests=sdk_requests)

        batch = self._with_retries("submit_batch", _do_create)
        batch_id = getattr(batch, "id", None) or batch["id"]  # SDK obj or dict
        logger.info(
            "Submitted batch %s with %d requests (cache_ttls=%s)",
            batch_id,
            len(requests),
            sorted({r.cache_ttl for r in requests}),
        )
        return batch_id

    def poll_status(self, batch_id: str) -> BatchStatus:
        """Return the high-level status of a batch.

        Maps the SDK's ``processing_status`` (``in_progress`` /
        ``canceling`` / ``ended``) plus ``request_counts`` into the terminal
        states the caller cares about. ``canceling`` is reported as
        ``in_progress`` until it actually ends.
        """

        def _do_retrieve():
            client = self._get_sdk_client()
            return client.messages.batches.retrieve(batch_id)

        batch = self._with_retries("poll_status", _do_retrieve)
        return self._derive_status(batch)

    def fetch_results(self, batch_id: str) -> dict[str, BatchResult]:
        """Fetch all results for a batch. Raises if the batch is not ended.

        Returns a dict keyed by ``custom_id``. Order is not guaranteed by the
        API (per the docs); callers must reconcile via custom_id.
        """
        status = self.poll_status(batch_id)
        if status != "ended":
            raise BatchNotEndedError(
                f"Cannot fetch results for batch {batch_id}: status={status!r}"
            )

        def _do_results():
            client = self._get_sdk_client()
            return client.messages.batches.results(batch_id)

        decoder = self._with_retries("fetch_results", _do_results)
        results: dict[str, BatchResult] = {}
        for line in decoder:
            parsed = self._parse_individual_response(line)
            results[parsed.custom_id] = parsed
        return results

    def wait_and_fetch(
        self,
        batch_id: str,
        progress_callback: Optional[Callable[[BatchStatus, dict], None]] = None,
    ) -> dict[str, BatchResult]:
        """Poll ``batch_id`` until terminal then return parsed results.

        Honors ``self.max_wait_seconds``. Calls ``progress_callback(status,
        request_counts_dict)`` on every poll if supplied — useful for cost
        / cache observability hooks (T0.2).
        """

        def _do_retrieve():
            client = self._get_sdk_client()
            return client.messages.batches.retrieve(batch_id)

        deadline = time.monotonic() + self.max_wait_seconds
        while True:
            batch = self._with_retries("poll_status", _do_retrieve)
            status = self._derive_status(batch)
            counts = self._extract_request_counts(batch)
            if progress_callback is not None:
                try:
                    progress_callback(status, counts)
                except Exception:  # noqa: BLE001 — observer must not break polling
                    logger.exception("progress_callback raised; ignoring")
            if status != "in_progress":
                break
            if time.monotonic() >= deadline:
                raise BatchTimeoutError(
                    f"Batch {batch_id} did not reach a terminal state within "
                    f"{self.max_wait_seconds}s (last status={status!r}, "
                    f"counts={counts})"
                )
            time.sleep(self.polling_interval_seconds)

        if status != "ended":
            raise BatchTerminalError(
                f"Batch {batch_id} ended in non-success terminal state: {status!r}"
            )
        return self.fetch_results(batch_id)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _to_sdk_request(self, r: BatchRequest) -> dict:
        """Convert a ``BatchRequest`` to the SDK's request shape.

        Produces ``{"custom_id": ..., "params": {...}}``. ``cache_ttl`` is
        intentionally NOT injected into params (the actual cache_control
        lives inside the system/messages content blocks). It survives only
        as an attribute on the originating BatchRequest for audit.
        """
        params: dict = {
            "model": r.model,
            "max_tokens": r.max_tokens,
            "messages": r.messages,
            "temperature": r.temperature,
        }
        if r.system is not None:
            params["system"] = r.system
        if r.output_config is not None:
            params["output_config"] = r.output_config
        if r.extra_params:
            for k, v in r.extra_params.items():
                params[k] = v
        return {"custom_id": r.custom_id, "params": params}

    @staticmethod
    def _derive_status(batch: Any) -> BatchStatus:
        """Map a MessageBatch (or dict) into our public ``BatchStatus``.

        Rules:
          * processing_status == "ended" AND request_counts.errored > 0 AND
            no other terminal counts → ``"errored"`` (whole batch
            errored). Otherwise ``"ended"`` (mixed results — fetch and
            inspect per-request).
          * processing_status == "ended" AND counts indicate every request
            ``canceled`` → ``"canceled"``.
          * processing_status == "ended" AND counts indicate every request
            ``expired`` → ``"expired"``.
          * processing_status in {"in_progress", "canceling"} → ``"in_progress"``.
        """
        proc = _get_attr(batch, "processing_status", default="in_progress")
        if proc != BatchClient._PROCESSING_STATUS_TERMINAL:
            return "in_progress"

        counts = BatchClient._extract_request_counts(batch)
        succeeded = int(counts.get("succeeded", 0) or 0)
        errored = int(counts.get("errored", 0) or 0)
        canceled = int(counts.get("canceled", 0) or 0)
        expired = int(counts.get("expired", 0) or 0)
        total = succeeded + errored + canceled + expired

        if total > 0 and canceled == total:
            return "canceled"
        if total > 0 and expired == total:
            return "expired"
        if total > 0 and errored == total and succeeded == 0:
            return "errored"
        return "ended"

    @staticmethod
    def _extract_request_counts(batch: Any) -> dict:
        rc = _get_attr(batch, "request_counts", default=None)
        if rc is None:
            return {}
        if isinstance(rc, dict):
            return rc
        # SDK BaseModel — try .model_dump(), else fall back to attr enumeration.
        if hasattr(rc, "model_dump"):
            try:
                return rc.model_dump()
            except Exception:  # noqa: BLE001
                pass
        out: dict = {}
        for k in ("processing", "succeeded", "errored", "canceled", "expired"):
            v = getattr(rc, k, None)
            if v is not None:
                out[k] = v
        return out

    @staticmethod
    def _parse_individual_response(line: Any) -> BatchResult:
        """Decode one ``MessageBatchIndividualResponse`` into a ``BatchResult``."""
        # Accept either an SDK BaseModel (has .custom_id / .result) or a dict
        # (test fixtures often use dicts directly).
        custom_id = _get_attr(line, "custom_id", default=None)
        result = _get_attr(line, "result", default=None)
        if custom_id is None or result is None:
            # As a last resort, treat the whole thing as a json-loadable string.
            if isinstance(line, (str, bytes, bytearray)):
                obj = json.loads(line)
                custom_id = obj.get("custom_id")
                result = obj.get("result")

        if custom_id is None:
            raise ValueError(f"Missing custom_id in batch result line: {line!r}")
        if result is None:
            raise ValueError(f"Missing result block in batch result line: {line!r}")

        result_type = _get_attr(result, "type", default=None)
        if result_type == "succeeded":
            message = _get_attr(result, "message", default=None)
            content_blocks = _get_attr(message, "content", default=[]) or []
            text_parts: list[str] = []
            for block in content_blocks:
                btype = _get_attr(block, "type", default=None)
                btext = _get_attr(block, "text", default=None)
                if btype == "text" and btext is not None:
                    text_parts.append(btext)
            content_text = "".join(text_parts) if text_parts else ""
            stop_reason = _get_attr(message, "stop_reason", default=None)
            usage_obj = _get_attr(message, "usage", default=None)
            usage = _normalize_usage(usage_obj)
            return BatchResult(
                custom_id=custom_id,
                content_text=content_text,
                stop_reason=stop_reason,
                usage=usage,
                error=None,
            )

        # Failure paths (errored / canceled / expired). All carry a non-None
        # error envelope so callers can branch on `.error is not None`.
        error_payload: dict = {"type": result_type or "unknown"}
        err = _get_attr(result, "error", default=None)
        if err is not None:
            if hasattr(err, "model_dump"):
                try:
                    error_payload["detail"] = err.model_dump()
                except Exception:  # noqa: BLE001
                    error_payload["detail"] = repr(err)
            elif isinstance(err, dict):
                error_payload["detail"] = err
            else:
                error_payload["detail"] = repr(err)
        else:
            error_payload["detail"] = None
        return BatchResult(custom_id=custom_id, error=error_payload)

    # ------------------------------------------------------------------
    # Retry helper
    # ------------------------------------------------------------------

    _RETRY_BASE_DELAYS = (1.0, 2.0, 4.0)

    def _with_retries(self, label: str, fn: Callable[[], Any]) -> Any:
        """Invoke ``fn`` with exponential backoff on retryable transients.

        Retryable: APIConnectionError, APITimeoutError, InternalServerError,
        and any APIStatusError with ``status_code >= 500`` (covers
        ServiceUnavailableError / OverloadedError / DeadlineExceededError —
        these are not part of the public ``anthropic`` namespace in
        SDK 0.87.0 but inherit from APIStatusError with 5xx codes).

        Non-retryable: 4xx (including RateLimitError 429 — caller must back
        off itself), anything outside the SDK exception tree.
        """
        # Imported lazily so tests can run without anthropic in the path
        # of every helper call. By the time we hit a retry, the SDK is
        # already imported.
        try:
            from anthropic import (
                APIConnectionError,
                APIStatusError,
                APITimeoutError,
                InternalServerError,
            )
        except ImportError:  # pragma: no cover — anthropic is a hard dep
            APIConnectionError = APITimeoutError = APIStatusError = ()
            InternalServerError = ()

        retryable_exact = tuple(
            x
            for x in (
                APIConnectionError,
                APITimeoutError,
                InternalServerError,
            )
            if x
        )

        last_exc: Optional[Exception] = None
        for attempt in range(len(self._RETRY_BASE_DELAYS) + 1):
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001 — classify below
                last_exc = exc
                is_retryable = False
                if retryable_exact and isinstance(exc, retryable_exact):
                    is_retryable = True
                elif APIStatusError and isinstance(exc, APIStatusError):
                    status = getattr(exc, "status_code", None)
                    if isinstance(status, int) and status >= 500:
                        is_retryable = True
                if not is_retryable or attempt >= len(self._RETRY_BASE_DELAYS):
                    raise
                base = self._RETRY_BASE_DELAYS[attempt]
                jitter = random.uniform(0, base * 0.25)
                delay = base + jitter
                logger.warning(
                    "%s attempt %d/%d failed with %s; retrying in %.2fs",
                    label,
                    attempt + 1,
                    len(self._RETRY_BASE_DELAYS) + 1,
                    type(exc).__name__,
                    delay,
                )
                time.sleep(delay)
        # Should be unreachable — the loop either returns or re-raises.
        raise RuntimeError(
            f"_with_retries({label}) exhausted without raising; last={last_exc!r}"
        )


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class BatchClientError(RuntimeError):
    """Base class for batch-client-specific errors."""


class BatchNotEndedError(BatchClientError):
    """Raised when ``fetch_results`` is called before the batch is terminal."""


class BatchTimeoutError(BatchClientError):
    """Raised when ``wait_and_fetch`` exceeds ``max_wait_seconds``."""


class BatchTerminalError(BatchClientError):
    """Raised when a batch ended in canceled/expired/errored (whole-batch)."""


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    """Read ``name`` from either a dict-like or attribute-bearing object."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _normalize_usage(usage_obj: Any) -> dict:
    """Coerce a ``Usage`` SDK model (or dict) into a plain dict.

    Always returns a dict; missing fields default to 0 so downstream cost
    accounting (T0.2) sees a stable shape.
    """
    out = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    if usage_obj is None:
        return out
    if isinstance(usage_obj, dict):
        for k in out:
            if k in usage_obj and usage_obj[k] is not None:
                out[k] = usage_obj[k]
        return out
    for k in out:
        v = getattr(usage_obj, k, None)
        if v is not None:
            out[k] = v
    return out
