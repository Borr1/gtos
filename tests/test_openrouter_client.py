"""Tests for src/research/openrouter_client.py.

All tests use mocked HTTP — no real API calls are made.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ok_response(
    content: str = '{"decision": "NO_TRADE"}',
    model: str = "openrouter/elephant-alpha",
    prompt_tokens: int = 100,
    completion_tokens: int = 50,
) -> MagicMock:
    """Build a mock requests.Response for a successful API call."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "choices": [{"message": {"content": content}}],
        "model": model,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
    return resp


def _make_error_response(status_code: int, body: str = "error") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = body
    resp.json.return_value = {}
    return resp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_OR_KEY = "redacted"
FAKE_ANTHROPIC_KEY = "redacted"
MESSAGES = [{"role": "user", "content": "Hello"}]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    """Ensure a clean, predictable env + redirect log files to tmp_path."""
    monkeypatch.setenv("OPENROUTER_API_KEY", FAKE_OR_KEY)
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_ANTHROPIC_KEY)
    # Redirect shadow log dir to tmp_path so tests don't write to real dirs
    monkeypatch.setattr(
        "src.research.openrouter_client._LOG_DIR",
        tmp_path / "elephant_raw",
    )
    yield


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_raises_on_missing_openrouter_key(self, monkeypatch):
        """Unset OPENROUTER_API_KEY -> RuntimeError with clear message."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        # Also force reload so dotenv doesn't resurrect the key
        from src.research import openrouter_client as _mod
        monkeypatch.setattr(_mod.os.environ, "get",
                            lambda k, default="": "" if k == "OPENROUTER_API_KEY" else os.environ.get(k, default))
        from src.research.openrouter_client import OpenRouterClient
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            OpenRouterClient()

    def test_construction_succeeds_with_key(self):
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        assert client.model == "openrouter/elephant-alpha"


class TestHeaderSafety:
    def test_authorization_uses_openrouter_key(self, tmp_path):
        """Authorization header must be 'Bearer <OPENROUTER_API_KEY>'."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        with patch("requests.post", return_value=_make_ok_response()) as mock_post:
            client.call(MESSAGES, max_tokens=50)
        _, kwargs = mock_post.call_args
        # requests.post(url, headers=..., data=..., timeout=...)
        headers = mock_post.call_args[1].get("headers") or mock_post.call_args[0][1]
        # Accept both positional and keyword
        call_kwargs = mock_post.call_args
        # Inspect keyword args
        headers = call_kwargs.kwargs.get("headers", {})
        if not headers:
            # Fall back: second positional
            try:
                headers = call_kwargs.args[1]
            except IndexError:
                headers = {}
        assert headers.get("Authorization") == f"Bearer {FAKE_OR_KEY}"

    def test_anthropic_key_never_in_headers(self):
        """ANTHROPIC_API_KEY value must not appear in any header value."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        captured_headers: dict = {}

        def fake_post(url, *, headers=None, data=None, timeout=None, **kwargs):
            captured_headers.update(headers or {})
            return _make_ok_response()

        with patch("requests.post", side_effect=fake_post):
            client.call(MESSAGES, max_tokens=50)

        for header_name, header_val in captured_headers.items():
            assert FAKE_ANTHROPIC_KEY not in header_val, (
                f"ANTHROPIC_API_KEY found in header '{header_name}'"
            )

    def test_anthropic_key_never_in_body(self):
        """ANTHROPIC_API_KEY must not appear in the request body."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        captured_body: list[str] = []

        def fake_post(url, *, headers=None, data=None, timeout=None, **kwargs):
            captured_body.append(data or "")
            return _make_ok_response()

        with patch("requests.post", side_effect=fake_post):
            client.call(MESSAGES, max_tokens=50)

        full_body = "".join(captured_body)
        assert FAKE_ANTHROPIC_KEY not in full_body, (
            "ANTHROPIC_API_KEY value appeared in request body"
        )


class TestKeySecrecyInLogs:
    def test_anthropic_key_never_in_logs(self, tmp_path):
        """Neither the anthropic nor openrouter key should appear in the jsonl log."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        with patch("requests.post", return_value=_make_ok_response()):
            client.call(MESSAGES, max_tokens=50)

        log_dir = tmp_path / "elephant_raw"
        log_files = list(log_dir.glob("*.jsonl"))
        assert log_files, "No log file was written"

        full_log = log_files[0].read_text(encoding="utf-8")
        assert FAKE_ANTHROPIC_KEY not in full_log, (
            "ANTHROPIC_API_KEY appeared in log file"
        )
        assert FAKE_OR_KEY not in full_log, (
            "OPENROUTER_API_KEY appeared in log file"
        )


class TestRetryLogic:
    def test_retry_on_429(self):
        """429 -> 200 sequence: two calls made, final response returned."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        side_effects = [_make_error_response(429), _make_ok_response()]
        with patch("requests.post", side_effect=side_effects) as mock_post, \
             patch("time.sleep"):
            result = client.call(MESSAGES, max_tokens=50)
        assert mock_post.call_count == 2
        assert result["status"] == "success"

    def test_retry_on_503(self):
        """503 -> 200: retries and succeeds."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        side_effects = [_make_error_response(503), _make_ok_response()]
        with patch("requests.post", side_effect=side_effects) as mock_post, \
             patch("time.sleep"):
            result = client.call(MESSAGES, max_tokens=50)
        assert mock_post.call_count == 2
        assert result["status"] == "success"

    def test_no_retry_on_400(self):
        """400 -> RuntimeError immediately, exactly 1 call made."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        with patch("requests.post", return_value=_make_error_response(400)) as mock_post:
            with pytest.raises(RuntimeError, match="400"):
                client.call(MESSAGES, max_tokens=50)
        assert mock_post.call_count == 1

    def test_respects_timeout(self):
        """requests.Timeout causes retries then RuntimeError after all attempts."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        with patch("requests.post", side_effect=requests.Timeout("timed out")) as mock_post, \
             patch("time.sleep"):
            with pytest.raises(RuntimeError):
                client.call(MESSAGES, max_tokens=50)
        # All 3 attempts should have been tried
        assert mock_post.call_count == 3

    def test_backoff_timing(self):
        """Verify sleep called with increasing delays: 2s, 4s, 8s."""
        from src.research.openrouter_client import OpenRouterClient
        from src.research.openrouter_client import _RETRY_BASE_SLEEP
        client = OpenRouterClient()
        always_429 = [_make_error_response(429)] * 3
        sleep_calls: list[float] = []

        with patch("requests.post", side_effect=always_429), \
             patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
            with pytest.raises(RuntimeError):
                client.call(MESSAGES, max_tokens=50)

        # Should have been called twice (after attempt 0 and attempt 1;
        # attempt 2 exhausts retries without sleeping again)
        assert len(sleep_calls) >= 2
        # First sleep: base * 2^0 = 2.0; second: base * 2^1 = 4.0
        assert sleep_calls[0] == pytest.approx(_RETRY_BASE_SLEEP * 1, rel=0.01)
        assert sleep_calls[1] == pytest.approx(_RETRY_BASE_SLEEP * 2, rel=0.01)


class TestLogging:
    def test_jsonl_log_format(self, tmp_path):
        """Successful call writes a jsonl line with required fields + correct hash."""
        from src.research.openrouter_client import OpenRouterClient, _sha256
        client = OpenRouterClient()
        with patch("requests.post", return_value=_make_ok_response(prompt_tokens=200, completion_tokens=80)):
            client.call(MESSAGES, max_tokens=100)

        log_dir = tmp_path / "elephant_raw"
        log_files = list(log_dir.glob("*.jsonl"))
        assert log_files

        line = json.loads(log_files[0].read_text().strip().splitlines()[-1])
        assert "timestamp" in line
        assert line["model"] == "openrouter/elephant-alpha"
        assert line["prompt_hash"] == _sha256(MESSAGES)
        assert line["latency_ms"] >= 0
        assert line["status"] == "success"
        assert line["prompt_tokens"] == 200
        assert line["completion_tokens"] == 80


class TestRateLimitTracker:
    def test_rate_limit_tracker_rpm(self):
        """10 calls in < 60s -> current_rpm == 10."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        with patch("requests.post", return_value=_make_ok_response()):
            for _ in range(10):
                client.call(MESSAGES, max_tokens=10)
        assert client.current_rpm == 10

    def test_rate_limit_tracker_rph(self):
        """10 calls -> current_rph == 10."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        with patch("requests.post", return_value=_make_ok_response()):
            for _ in range(10):
                client.call(MESSAGES, max_tokens=10)
        assert client.current_rph == 10


class TestResponseParsing:
    def test_response_text_extraction(self):
        """choices[0].message.content is returned as response_text."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        expected = '{"decision": "CANDIDATE", "confidence": 85}'
        with patch("requests.post", return_value=_make_ok_response(content=expected)):
            result = client.call(MESSAGES, max_tokens=50)
        assert result["response_text"] == expected

    def test_usage_extraction(self):
        """Token counts from usage object extracted correctly."""
        from src.research.openrouter_client import OpenRouterClient
        client = OpenRouterClient()
        with patch("requests.post", return_value=_make_ok_response(prompt_tokens=300, completion_tokens=120)):
            result = client.call(MESSAGES, max_tokens=200)
        assert result["usage"]["prompt_tokens"] == 300
        assert result["usage"]["completion_tokens"] == 120
        assert result["usage"]["total_tokens"] == 420


class TestIsolation:
    def test_multiple_instances_share_no_state(self):
        """Two OpenRouterClient instances must not share rate-tracker state."""
        from src.research.openrouter_client import OpenRouterClient
        client_a = OpenRouterClient()
        client_b = OpenRouterClient()

        with patch("requests.post", return_value=_make_ok_response()):
            for _ in range(5):
                client_a.call(MESSAGES, max_tokens=10)

        # client_b has made zero calls
        assert client_b.current_rpm == 0
        assert client_b.current_rph == 0
        # client_a has 5
        assert client_a.current_rpm == 5
