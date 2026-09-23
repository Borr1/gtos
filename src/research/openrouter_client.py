"""OpenRouter API client for research/batch dispatch.

Standalone module — does NOT import anthropic SDK.
Enforces hard safety assertions: ANTHROPIC_API_KEY value never appears
in any HTTP header, URL, body, or log line.

Usage:
    from src.research.openrouter_client import OpenRouterClient

    client = OpenRouterClient()
    result = client.call(
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=100,
    )
    print(result["response_text"])
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Per-call jsonl log directory (one file per UTC day)
_LOG_DIR = Path("shadow_logs/elephant_raw")

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Retry config
_RETRY_STATUS_CODES = {429, 502, 503, 504}
_RETRY_ATTEMPTS = 3
_RETRY_BASE_SLEEP = 2.0  # seconds; doubles each attempt: 2, 4, 8


def _sha256(data: Any) -> str:
    """SHA-256 hash of the JSON-serialised data."""
    serialised = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialised.encode()).hexdigest()


class OpenRouterClient:
    """Thin wrapper around OpenRouter's OpenAI-compatible chat completions API.

    Safety guarantee: ANTHROPIC_API_KEY value will never appear in any HTTP
    header, URL, request body, or log line. Enforced by runtime assertions
    before every HTTP call.
    """

    def __init__(
        self,
        model: str = "openrouter/elephant-alpha",
        timeout: int = 60,
    ) -> None:
        self.model = model
        self.timeout = timeout

        # Load key at construction — fail fast if missing
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set or is empty. "
                "Set it in your .env file or environment before using OpenRouterClient."
            )
        self._api_key = api_key

        # Rate-limit tracker: rolling 60s and 3600s windows
        # Each entry is a float timestamp
        self._call_times: deque[float] = deque()
        self.last_429_at: float | None = None

        # Per-instance state (no class-level shared state)
        self._total_calls: int = 0

    # ------------------------------------------------------------------
    # Rate-limit properties
    # ------------------------------------------------------------------

    def _prune_call_times(self) -> None:
        """Remove timestamps older than 3600s from the rolling window."""
        now = time.monotonic()
        cutoff_3600 = now - 3600.0
        while self._call_times and self._call_times[0] < cutoff_3600:
            self._call_times.popleft()

    @property
    def current_rpm(self) -> int:
        """Calls made in the last 60 seconds."""
        self._prune_call_times()
        now = time.monotonic()
        cutoff_60 = now - 60.0
        return sum(1 for t in self._call_times if t >= cutoff_60)

    @property
    def current_rph(self) -> int:
        """Calls made in the last 3600 seconds."""
        self._prune_call_times()
        return len(self._call_times)

    # ------------------------------------------------------------------
    # Safety assertion helpers
    # ------------------------------------------------------------------

    def _assert_no_anthropic_key_leak(
        self,
        headers: dict[str, str],
        url: str,
        body_str: str,
    ) -> None:
        """Assert ANTHROPIC_API_KEY value does not appear anywhere in the call."""
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not anthropic_key:
            return  # Nothing to leak

        # Check every header value
        for header_name, header_val in headers.items():
            assert anthropic_key not in header_val, (
                f"SAFETY VIOLATION: ANTHROPIC_API_KEY value found in header '{header_name}'. "
                "This must never happen."
            )

        # Check URL
        assert anthropic_key not in url, (
            "SAFETY VIOLATION: ANTHROPIC_API_KEY value found in request URL."
        )

        # Check request body
        assert anthropic_key not in body_str, (
            "SAFETY VIOLATION: ANTHROPIC_API_KEY value found in request body."
        )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_call(
        self,
        prompt_hash: str,
        latency_ms: float,
        status: str,
        prompt_tokens: int,
        completion_tokens: int,
        error: str | None = None,
    ) -> None:
        """Append a jsonl record to shadow_logs/elephant_raw/{YYYY-MM-DD}.jsonl.

        SAFETY: openrouter key value is never written to the log.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = _LOG_DIR / f"{today}.jsonl"
        _LOG_DIR.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.model,
            "prompt_hash": prompt_hash,
            "latency_ms": round(latency_ms, 1),
            "status": status,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        if error:
            record["error"] = error[:500]

        # Paranoia: verify neither key appears in the serialised record
        openrouter_key = self._api_key
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        record_str = json.dumps(record)
        assert openrouter_key not in record_str, (
            "SAFETY VIOLATION: OPENROUTER_API_KEY appeared in log record."
        )
        if anthropic_key:
            assert anthropic_key not in record_str, (
                "SAFETY VIOLATION: ANTHROPIC_API_KEY appeared in log record."
            )

        try:
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(record_str + "\n")
        except Exception as exc:
            logger.warning("Failed to write elephant_raw log: %s", exc)

    # ------------------------------------------------------------------
    # Core call method
    # ------------------------------------------------------------------

    def call(
        self,
        messages: list[dict],
        max_tokens: int,
        temperature: float = 0.0,
    ) -> dict:
        """Call the OpenRouter API and return a structured response dict.

        Args:
            messages: OpenAI-compatible messages list (role/content dicts).
            max_tokens: Maximum tokens in the completion.
            temperature: Sampling temperature (0.0 = deterministic).

        Returns:
            dict with keys:
                response_text (str): The model's text output.
                usage (dict): prompt_tokens, completion_tokens, total_tokens.
                latency_ms (float): Round-trip time in milliseconds.
                model (str): Model identifier as reported by the API.
                raw (dict): Full parsed API response.
                status (str): "success" or "error".

        Raises:
            RuntimeError: On non-retryable HTTP errors (4xx except 429).
            RuntimeError: After exhausting retries on 429/5xx.
        """
        prompt_hash = _sha256(messages)
        t_start = time.monotonic()

        # Build headers using ONLY the OpenRouter key
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/gtos/ai-trading-agent",
            "X-Title": "GTOS Elephant Alpha Harness",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        body_str = json.dumps(payload)

        # Hard safety assertion before every call
        self._assert_no_anthropic_key_leak(headers, _OPENROUTER_BASE_URL, body_str)

        last_error: Exception | None = None
        last_status_code: int | None = None

        for attempt in range(_RETRY_ATTEMPTS):
            try:
                response = requests.post(
                    _OPENROUTER_BASE_URL,
                    headers=headers,
                    data=body_str,
                    timeout=self.timeout,
                )
                last_status_code = response.status_code

                if response.status_code == 200:
                    break  # Success

                if response.status_code in _RETRY_STATUS_CODES:
                    # 429: rate-limited; 502/503/504: transient server errors
                    if response.status_code == 429:
                        self.last_429_at = time.monotonic()
                    sleep_s = _RETRY_BASE_SLEEP * (2 ** attempt)
                    logger.warning(
                        "OpenRouter %d (attempt %d/%d) — sleeping %.1fs",
                        response.status_code, attempt + 1, _RETRY_ATTEMPTS, sleep_s,
                    )
                    time.sleep(sleep_s)
                    last_error = RuntimeError(
                        f"HTTP {response.status_code} after {attempt + 1} attempts"
                    )
                    continue  # retry

                # Any other 4xx: fail fast
                latency_ms = (time.monotonic() - t_start) * 1000
                error_text = response.text[:500]
                self._log_call(
                    prompt_hash, latency_ms, f"http_{response.status_code}",
                    0, 0, error=error_text,
                )
                raise RuntimeError(
                    f"OpenRouter HTTP {response.status_code} (non-retryable): {error_text}"
                )

            except requests.Timeout as exc:
                sleep_s = _RETRY_BASE_SLEEP * (2 ** attempt)
                logger.warning(
                    "OpenRouter request timed out (attempt %d/%d) — sleeping %.1fs",
                    attempt + 1, _RETRY_ATTEMPTS, sleep_s,
                )
                time.sleep(sleep_s)
                last_error = exc
                continue

            except requests.RequestException as exc:
                # Network-level error — retry
                sleep_s = _RETRY_BASE_SLEEP * (2 ** attempt)
                logger.warning(
                    "OpenRouter network error (attempt %d/%d): %s — sleeping %.1fs",
                    attempt + 1, _RETRY_ATTEMPTS, exc, sleep_s,
                )
                time.sleep(sleep_s)
                last_error = exc
                continue

        else:
            # All retries exhausted
            latency_ms = (time.monotonic() - t_start) * 1000
            error_msg = str(last_error) if last_error else f"HTTP {last_status_code}"
            self._log_call(
                prompt_hash, latency_ms, "exhausted_retries", 0, 0, error=error_msg
            )
            raise RuntimeError(
                f"OpenRouter call failed after {_RETRY_ATTEMPTS} attempts: {error_msg}"
            )

        # Parse successful response
        latency_ms = (time.monotonic() - t_start) * 1000
        try:
            data = response.json()
        except Exception as exc:
            self._log_call(
                prompt_hash, latency_ms, "json_parse_error", 0, 0, error=str(exc)
            )
            raise RuntimeError(f"OpenRouter returned non-JSON response: {exc}") from exc

        # Extract text from OpenAI-compatible schema
        try:
            response_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            self._log_call(
                prompt_hash, latency_ms, "schema_error", 0, 0, error=str(exc)
            )
            raise RuntimeError(
                f"Unexpected OpenRouter response schema (choices[0].message.content missing): {exc}"
            ) from exc

        # Extract usage
        usage_raw = data.get("usage", {})
        prompt_tokens = usage_raw.get("prompt_tokens", 0)
        completion_tokens = usage_raw.get("completion_tokens", 0)
        total_tokens = usage_raw.get("total_tokens", prompt_tokens + completion_tokens)

        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

        # Record call time for rate-limit tracker
        self._call_times.append(time.monotonic())
        self._total_calls += 1

        # Log the successful call
        self._log_call(
            prompt_hash, latency_ms, "success",
            prompt_tokens, completion_tokens,
        )

        reported_model = data.get("model", self.model)
        logger.debug(
            "OpenRouter call OK: model=%s latency=%.0fms tokens=%d+%d",
            reported_model, latency_ms, prompt_tokens, completion_tokens,
        )

        return {
            "response_text": response_text,
            "usage": usage,
            "latency_ms": latency_ms,
            "model": reported_model,
            "raw": data,
            "status": "success",
        }
