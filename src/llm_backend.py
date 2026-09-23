"""LLM Backend Abstraction — routes AI calls through API or Max subscription.

Two billing modes:
  - "api":          Direct Anthropic Python SDK (pay-per-token). For live trading.
  - "subscription": Claude Code CLI (`claude -p`), billed to Max plan. For bulk backtesting.

CRITICAL SAFETY:
  In subscription mode, ANTHROPIC_API_KEY is stripped from the subprocess
  environment to prevent accidental API billing. This is the #1 safety rule.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

from anthropic import Anthropic

from src.security import get_sanitized_environment, install_runtime_monitoring

logger = logging.getLogger(__name__)

# Keys that MUST be stripped from subprocess env in subscription mode.
# A Max subscriber was billed $1,800 because one of these leaked through.
_API_KEY_ENV_VARS = frozenset([
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_API_KEY",
])


@dataclass
class LLMUsage:
    """Token usage from a single LLM call."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_create_tokens: int = 0


@dataclass
class LLMResponse:
    """Unified response from either backend."""
    text: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    backend_mode: str = "api"


class LLMBackend:
    """Routes LLM calls through API SDK or Claude CLI subscription.

    Parameters
    ----------
    mode : str
        "api" for Anthropic Python SDK, "subscription" for claude -p CLI.
    """

    def __init__(self, mode: str = "api") -> None:
        if mode not in ("api", "subscription"):
            raise ValueError(f"Invalid LLM backend mode: {mode!r}. Use 'api' or 'subscription'.")
        self.mode = mode
        self._api_client = None  # Lazy-init for API mode
        self._claude_bin = "claude"  # Default; overridden by _verify_cli_installed

        if mode == "subscription":
            self._verify_cli_installed()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def call(
        self,
        system_prompt,
        user_message: str,
        model: str,
        max_tokens: int = 1500,
        temperature: float = 0,
        timeout: int = 30,
        effort: Optional[str] = None,
    ) -> LLMResponse:
        """Make an LLM call through the configured backend.

        Parameters
        ----------
        system_prompt : str or list[dict]
            System prompt. In API mode, can be a list of content blocks
            (for prompt caching). In subscription mode, content blocks
            are flattened to plain text.
        user_message : str
            User message content.
        model : str
            Model identifier (e.g. "claude-sonnet-4-6").
        max_tokens : int
            Maximum output tokens.
        temperature : float
            Sampling temperature.
        timeout : int
            Timeout in seconds.
        effort : str, optional
            Extended-thinking effort level — "high" or "max". API mode only;
            ignored in subscription mode. When set, passes
            ``output_config={"effort": effort}`` to the Anthropic SDK.

        Returns
        -------
        LLMResponse
            Unified response with text and usage metadata.
        """
        if self.mode == "api":
            return self._call_api(system_prompt, user_message, model,
                                  max_tokens, temperature, timeout, effort)
        else:
            return self._call_subscription(system_prompt, user_message, model,
                                           max_tokens, timeout)

    def get_api_client(self):
        """Return the Anthropic SDK client (API mode only).

        Raises RuntimeError if called in subscription mode.
        """
        if self.mode != "api":
            raise RuntimeError("API client not available in subscription mode.")
        if self._api_client is None:
            self._api_client = Anthropic()
        return self._api_client

    # ------------------------------------------------------------------
    # API Mode (existing behavior)
    # ------------------------------------------------------------------

    def _call_api(
        self,
        system_prompt,
        user_message: str,
        model: str,
        max_tokens: int,
        temperature: float,
        timeout: int,
        effort: Optional[str] = None,
    ) -> LLMResponse:
        """Call via Anthropic Python SDK — billed to API account."""
        client = self.get_api_client()
        create_kwargs = dict(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            timeout=timeout,
        )
        if effort:
            create_kwargs["output_config"] = {"effort": effort}
        response = client.messages.create(**create_kwargs)
        usage = response.usage
        return LLMResponse(
            text=response.content[0].text,
            usage=LLMUsage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
                cache_create_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            ),
            backend_mode="api",
        )

    # ------------------------------------------------------------------
    # Subscription Mode (claude -p CLI)
    # ------------------------------------------------------------------

    def _call_subscription(
        self,
        system_prompt,
        user_message: str,
        model: str,
        max_tokens: int,
        timeout: int,
    ) -> LLMResponse:
        """Call via claude -p CLI — billed to Max subscription.

        SAFETY: ANTHROPIC_API_KEY is stripped from the subprocess env.
        """
        # Flatten system_prompt if it's a list of content blocks (cache format)
        system_text = self._flatten_system_prompt(system_prompt)

        # ============================================================
        # CRITICAL SAFETY: Build a clean env WITHOUT any API keys.
        # A subscriber was billed $1,800 because the key leaked through.
        # SECURITY: Enhanced with system-wide sanitization (Red Team fix 1.1)
        # ============================================================
        env = get_sanitized_environment()

        # Legacy double-check for backward compatibility
        for key in _API_KEY_ENV_VARS:
            assert key not in env, (
                f"CRITICAL SAFETY FAILURE: {key} still present in subprocess env!"
            )

        # Ensure node/nvm directories are in PATH for the subprocess
        env["PATH"] = self._enriched_path(env.get("PATH", ""))

        # Build combined prompt: system instructions + user message, piped via stdin.
        # NOTE: --system-prompt flag drops content for large prompts when passed
        # via subprocess.run(). Merging into stdin is more reliable.
        # NOTE: --bare is NOT used because it disables OAuth/keychain auth.
        full_prompt = (
            f"[SYSTEM INSTRUCTIONS]\n{system_text}\n[END SYSTEM INSTRUCTIONS]\n\n"
            f"{user_message}"
        )

        cmd = [
            self._claude_bin,
            "-p",                            # Print mode (non-interactive)
            "--model", model,
            "--output-format", "text",       # Raw text output
            "--no-session-persistence",      # Don't save session to disk
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                input=full_prompt,   # Everything via stdin
                timeout=timeout + 90,  # CLI startup + model time
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                # Check for auth errors and provide helpful message
                if "auth" in stderr.lower() or "login" in stderr.lower() or "credential" in stderr.lower():
                    raise RuntimeError(
                        f"Claude CLI auth error. Run:\n"
                        f"  claude logout\n"
                        f"  claude login\n"
                        f"  -> Select 'Claude account with subscription'\n\n"
                        f"Stderr: {stderr}"
                    )
                raise RuntimeError(f"claude -p failed (exit {result.returncode}): {stderr}")

            raw_text = result.stdout.strip()
            logger.debug(
                "CLI returned: exit=%d stdout=%d bytes stderr=%d bytes",
                result.returncode, len(result.stdout), len(result.stderr),
            )
            if not raw_text:
                stderr_hint = result.stderr.strip()[:300] if result.stderr else ""
                logger.warning("CLI empty output. stderr: %s", stderr_hint or "(none)")
                raise RuntimeError(
                    f"claude -p returned empty output"
                    f"{' (stderr: ' + stderr_hint + ')' if stderr_hint else ''}"
                )

            return LLMResponse(
                text=raw_text,
                usage=LLMUsage(),  # Text mode doesn't provide usage metadata
                backend_mode="subscription",
            )

        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"claude -p timed out after {timeout + 90}s. "
                f"The model may be overloaded or the prompt too large."
            )

    # ------------------------------------------------------------------
    # CLI Verification
    # ------------------------------------------------------------------

    def _verify_cli_installed(self) -> None:
        """Find and verify the claude CLI binary.

        Searches PATH, then common nvm/npm/homebrew locations.
        Stores the resolved path in self._claude_bin.
        """
        # 1. Try PATH first
        found = shutil.which("claude")
        if not found:
            # 2. Search common install locations
            home = os.path.expanduser("~")
            candidates = [
                os.path.join(home, ".nvm/versions/node", d, "bin/claude")
                for d in sorted(os.listdir(os.path.join(home, ".nvm/versions/node")), reverse=True)
                if os.path.isdir(os.path.join(home, ".nvm/versions/node", d))
            ] if os.path.isdir(os.path.join(home, ".nvm/versions/node")) else []
            candidates += [
                os.path.join(home, ".npm-global/bin/claude"),
                "/usr/local/bin/claude",
                "/opt/homebrew/bin/claude",
            ]
            for c in candidates:
                if os.path.isfile(c) and os.access(c, os.X_OK):
                    found = c
                    break

        if not found:
            raise RuntimeError(
                "Claude Code CLI not found in PATH or common locations.\n"
                "Install: npm install -g @anthropic-ai/claude-code\n"
                "Login:   claude login -> select 'Claude account with subscription'"
            )

        self._claude_bin = found
        logger.info("Claude CLI found at: %s", found)

    def verify_billing_route(self) -> bool:
        """Run a minimal test call to confirm subscription billing works.

        Returns True if the call succeeded without an API key in the env.
        The user should verify their API console balance didn't change.
        """
        if self.mode != "subscription":
            logger.info("Billing verification skipped (mode=%s)", self.mode)
            return True

        print("=" * 60)
        print("BILLING VERIFICATION TEST")
        print("=" * 60)
        print("Running a minimal test call through claude -p...")
        print("This should bill to your Max subscription, NOT your API account.")
        print()
        print("BEFORE proceeding, note your current API console balance at:")
        print("  https://console.anthropic.com/settings/billing")
        print()

        try:
            response = self._call_subscription(
                system_prompt="You are a test assistant.",
                user_message="Respond with exactly: BILLING_TEST_OK",
                model="claude-sonnet-4-20250514",
                max_tokens=20,
                timeout=30,
            )
            success = "BILLING_TEST_OK" in response.text
            if success:
                print(f"  Test call succeeded. Response: {response.text}")
                print()
                print("NOW CHECK: Did your API console balance change?")
                print("  - If balance is UNCHANGED -> subscription billing confirmed")
                print("  - If balance DECREASED    -> STOP, API key is leaking!")
                print()
            else:
                print(f"  Test call returned unexpected response: {response.text}")
                print("  (This may still be OK — the model just didn't follow instructions exactly)")
                success = True  # Non-empty response means the call worked
            return success
        except Exception as e:
            print(f"  Test call failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _enriched_path(current_path: str) -> str:
        """Ensure node/nvm bin dirs are on PATH for the subprocess."""
        home = os.path.expanduser("~")
        extra_dirs = []
        # Add nvm node bin dirs
        nvm_base = os.path.join(home, ".nvm/versions/node")
        if os.path.isdir(nvm_base):
            for d in sorted(os.listdir(nvm_base), reverse=True):
                bin_dir = os.path.join(nvm_base, d, "bin")
                if os.path.isdir(bin_dir):
                    extra_dirs.append(bin_dir)
                    break  # newest version only
        # Common extras
        for d in [os.path.join(home, ".npm-global/bin"),
                  "/usr/local/bin", "/opt/homebrew/bin"]:
            if os.path.isdir(d):
                extra_dirs.append(d)
        if extra_dirs:
            return ":".join(extra_dirs) + ":" + current_path
        return current_path

    @staticmethod
    def _flatten_system_prompt(system_prompt) -> str:
        """Convert system prompt to plain text.

        API mode uses list[dict] content blocks for prompt caching.
        Subscription mode needs plain text.
        """
        if isinstance(system_prompt, str):
            return system_prompt
        if isinstance(system_prompt, list):
            parts = []
            for block in system_prompt:
                if isinstance(block, dict) and "text" in block:
                    parts.append(block["text"])
                elif isinstance(block, str):
                    parts.append(block)
            return "\n\n".join(parts)
        return str(system_prompt)
