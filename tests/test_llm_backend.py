"""Tests for LLM Backend — API key safety, mode routing, CLI verification."""

from __future__ import annotations

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.llm_backend import LLMBackend, LLMResponse, LLMUsage, _API_KEY_ENV_VARS


def _make_subscription_backend():
    """Create a subscription backend with mocked CLI verification."""
    with patch.object(LLMBackend, "_verify_cli_installed") as mock_verify:
        backend = LLMBackend(mode="subscription")
        backend._claude_bin = "/usr/local/bin/claude"
    return backend


# ══════════════════════════════════════════════════════════════════════
# Construction / mode validation
# ══════════════════════════════════════════════════════════════════════


class TestLLMBackendInit:
    def test_api_mode_creates_backend(self):
        backend = LLMBackend(mode="api")
        assert backend.mode == "api"

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Invalid LLM backend mode"):
            LLMBackend(mode="invalid")

    @patch("shutil.which", return_value="/usr/local/bin/claude")
    def test_subscription_mode_with_cli(self, mock_which):
        backend = LLMBackend(mode="subscription")
        assert backend.mode == "subscription"
        assert backend._claude_bin == "/usr/local/bin/claude"

    @patch("shutil.which", return_value=None)
    @patch("os.path.isdir", return_value=False)  # No nvm dir
    def test_subscription_mode_without_cli_raises(self, mock_isdir, mock_which):
        with pytest.raises(RuntimeError, match="Claude Code CLI not found"):
            LLMBackend(mode="subscription")


# ══════════════════════════════════════════════════════════════════════
# CRITICAL: API key stripping tests
# ══════════════════════════════════════════════════════════════════════


class TestAPIKeySafety:
    """These are the MOST IMPORTANT tests in this file.

    A Max subscriber was billed $1,800 because ANTHROPIC_API_KEY leaked
    into the subprocess environment. These tests ensure that can never happen.
    """

    @patch("subprocess.run")
    def test_subscription_mode_strips_anthropic_api_key(self, mock_run):
        """CRITICAL: ANTHROPIC_API_KEY must NEVER be in subprocess env."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test response", stderr="")
        backend = _make_subscription_backend()

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "redacted"}):
            backend._call_subscription("system", "user", "claude-sonnet-4-20250514", 100, 30)

        call_kwargs = mock_run.call_args
        passed_env = call_kwargs.kwargs.get("env")
        assert passed_env is not None, "subprocess.run must receive explicit env"
        assert "ANTHROPIC_API_KEY" not in passed_env, \
            "CRITICAL SAFETY FAILURE: ANTHROPIC_API_KEY was passed to subscription subprocess!"

    @patch("subprocess.run")
    def test_subscription_mode_strips_anthropic_auth_token(self, mock_run):
        """CRITICAL: ANTHROPIC_AUTH_TOKEN must NEVER be in subprocess env."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test response", stderr="")
        backend = _make_subscription_backend()

        with patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN": "token-fake-12345"}):
            backend._call_subscription("system", "user", "claude-sonnet-4-20250514", 100, 30)

        passed_env = mock_run.call_args.kwargs.get("env")
        assert "ANTHROPIC_AUTH_TOKEN" not in passed_env, \
            "CRITICAL SAFETY FAILURE: ANTHROPIC_AUTH_TOKEN was passed to subscription subprocess!"

    @patch("subprocess.run")
    def test_subscription_mode_strips_claude_api_key(self, mock_run):
        """CRITICAL: CLAUDE_API_KEY must NEVER be in subprocess env."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test response", stderr="")
        backend = _make_subscription_backend()

        with patch.dict(os.environ, {"CLAUDE_API_KEY": "claude-fake-key-12345"}):
            backend._call_subscription("system", "user", "claude-sonnet-4-20250514", 100, 30)

        passed_env = mock_run.call_args.kwargs.get("env")
        assert "CLAUDE_API_KEY" not in passed_env, \
            "CRITICAL SAFETY FAILURE: CLAUDE_API_KEY was passed to subscription subprocess!"

    @patch("subprocess.run")
    def test_subscription_mode_strips_all_keys_simultaneously(self, mock_run):
        """CRITICAL: ALL API key variants must be stripped at once."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test response", stderr="")
        backend = _make_subscription_backend()

        fake_keys = {
            "ANTHROPIC_API_KEY": "sk-ant-fake",
            "ANTHROPIC_AUTH_TOKEN": "token-fake",
            "CLAUDE_API_KEY": "claude-fake",
        }
        with patch.dict(os.environ, fake_keys):
            backend._call_subscription("system", "user", "claude-sonnet-4-20250514", 100, 30)

        passed_env = mock_run.call_args.kwargs.get("env")
        for key in _API_KEY_ENV_VARS:
            assert key not in passed_env, \
                f"CRITICAL SAFETY FAILURE: {key} was passed to subscription subprocess!"

    @patch("subprocess.run")
    def test_subscription_mode_does_not_modify_global_env(self, mock_run):
        """Subprocess env stripping must NOT affect os.environ."""
        mock_run.return_value = MagicMock(returncode=0, stdout="test", stderr="")
        backend = _make_subscription_backend()

        original_key = "redacted"
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": original_key}):
            backend._call_subscription("system", "user", "claude-sonnet-4-20250514", 100, 30)
            # os.environ must still have the key
            assert os.environ.get("ANTHROPIC_API_KEY") == original_key, \
                "Global os.environ was modified! Only subprocess env should be changed."


# ══════════════════════════════════════════════════════════════════════
# Subscription mode: CLI invocation
# ══════════════════════════════════════════════════════════════════════


class TestSubscriptionCLIInvocation:
    @patch("subprocess.run")
    def test_user_message_piped_via_stdin(self, mock_run):
        """User message must go through stdin."""
        mock_run.return_value = MagicMock(returncode=0, stdout="response text", stderr="")
        backend = _make_subscription_backend()

        backend._call_subscription("my system prompt", "my user input",
                                   "claude-sonnet-4-20250514", 1500, 30)

        call_kwargs = mock_run.call_args.kwargs
        assert "input" in call_kwargs, "User message must be piped via stdin"
        assert "my user input" in call_kwargs["input"]

    @patch("subprocess.run")
    def test_system_prompt_merged_into_stdin(self, mock_run):
        """System prompt should be merged into stdin input."""
        mock_run.return_value = MagicMock(returncode=0, stdout="response text", stderr="")
        backend = _make_subscription_backend()

        backend._call_subscription("my system prompt", "my user input",
                                   "claude-sonnet-4-20250514", 1500, 30)

        call_kwargs = mock_run.call_args.kwargs
        stdin_text = call_kwargs["input"]
        assert "SYSTEM INSTRUCTIONS" in stdin_text
        assert "my system prompt" in stdin_text
        assert "my user input" in stdin_text

    @patch("subprocess.run")
    def test_uses_no_session_persistence(self, mock_run):
        """--no-session-persistence should be present to avoid saving history."""
        mock_run.return_value = MagicMock(returncode=0, stdout="response", stderr="")
        backend = _make_subscription_backend()

        backend._call_subscription("sys", "usr", "claude-sonnet-4-20250514", 100, 30)

        cmd = mock_run.call_args.args[0]
        assert "--no-session-persistence" in cmd

    @patch("subprocess.run")
    def test_uses_correct_model_flag(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="response", stderr="")
        backend = _make_subscription_backend()

        backend._call_subscription("sys", "usr", "claude-sonnet-4-20250514", 100, 30)

        cmd = mock_run.call_args.args[0]
        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "claude-sonnet-4-20250514"

    @patch("subprocess.run")
    def test_cli_nonzero_exit_raises(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="some error")
        backend = _make_subscription_backend()

        with pytest.raises(RuntimeError, match="claude -p failed"):
            backend._call_subscription("sys", "usr", "claude-sonnet-4-20250514", 100, 30)

    @patch("subprocess.run")
    def test_cli_auth_error_gives_login_instructions(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="auth error: not logged in")
        backend = _make_subscription_backend()

        with pytest.raises(RuntimeError, match="claude login"):
            backend._call_subscription("sys", "usr", "claude-sonnet-4-20250514", 100, 30)

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=60))
    def test_cli_timeout_raises(self, mock_run):
        backend = _make_subscription_backend()

        with pytest.raises(RuntimeError, match="timed out"):
            backend._call_subscription("sys", "usr", "claude-sonnet-4-20250514", 100, 30)

    @patch("subprocess.run")
    def test_cli_empty_response_raises(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        backend = _make_subscription_backend()

        with pytest.raises(RuntimeError, match="empty output"):
            backend._call_subscription("sys", "usr", "claude-sonnet-4-20250514", 100, 30)


# ══════════════════════════════════════════════════════════════════════
# System prompt flattening
# ══════════════════════════════════════════════════════════════════════


class TestSystemPromptFlattening:
    def test_string_passthrough(self):
        assert LLMBackend._flatten_system_prompt("hello") == "hello"

    def test_list_of_content_blocks(self):
        blocks = [
            {"type": "text", "text": "Part one", "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": "Part two"},
        ]
        result = LLMBackend._flatten_system_prompt(blocks)
        assert "Part one" in result
        assert "Part two" in result
        assert "cache_control" not in result  # Metadata stripped

    def test_empty_list(self):
        assert LLMBackend._flatten_system_prompt([]) == ""


# ══════════════════════════════════════════════════════════════════════
# API mode: delegates to SDK
# ══════════════════════════════════════════════════════════════════════


class TestAPIMode:
    @patch("src.llm_backend.Anthropic")
    def test_api_mode_calls_sdk(self, mock_anthropic_cls):
        """API mode should call client.messages.create()."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 50
        mock_usage.cache_read_input_tokens = 0
        mock_usage.cache_creation_input_tokens = 0

        mock_content = MagicMock()
        mock_content.text = '{"decision": "NO_TRADE"}'

        mock_response = MagicMock()
        mock_response.usage = mock_usage
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        backend = LLMBackend(mode="api")
        result = backend.call("system", "user", "claude-sonnet-4-20250514")

        assert result.text == '{"decision": "NO_TRADE"}'
        assert result.usage.input_tokens == 100
        assert result.usage.output_tokens == 50
        assert result.backend_mode == "api"
        mock_client.messages.create.assert_called_once()


# ══════════════════════════════════════════════════════════════════════
# Billing verification
# ══════════════════════════════════════════════════════════════════════


class TestBillingVerification:
    def test_api_mode_skips_verification(self):
        backend = LLMBackend(mode="api")
        assert backend.verify_billing_route() is True

    @patch("subprocess.run")
    def test_subscription_verification_passes(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="BILLING_TEST_OK", stderr="")
        backend = _make_subscription_backend()
        assert backend.verify_billing_route() is True

    @patch("subprocess.run", side_effect=RuntimeError("connection failed"))
    def test_subscription_verification_fails_on_error(self, mock_run):
        backend = _make_subscription_backend()
        assert backend.verify_billing_route() is False
