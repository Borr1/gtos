"""Component 3A — Primary Analyzer (AI Reasoning Engine).

Evaluates the Market State Object against Model A criteria
using contextual SMC reasoning via Claude API.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.components.knowledge_base import KnowledgeBase
from src.components.ai_decision_trace_logger import record_ai_decision_trace
from src.components.ai_call_policy import (
    evaluate_ai_call_policy,
    record_ai_call_policy_decision,
)
from src.components.ai_supervisor import repair_ai_response_format_preserving_semantics
from src.components.ai_reliability_contract import (
    build_deterministic_baseline_contract,
    build_fallback_behavior_contract,
    stable_sha256,
)
from src.components import model_pin as _model_pin
from src.components.precision import (
    _decimals_from_format as _decimals_from_format,
    _snap_to_precision as _snap_to_precision,
)
from src.models.analysis_models import (
    DailyBiasAnalysis,
    H1SetupAnalysis,
    H4AlignmentAnalysis,
    LiquiditySweepAnalysis,
    M15ConfirmationAnalysis,
    PrimaryAnalysisOutput,
    PrimaryAnalysisReasoning,
)
from src.models.market_state_models import MarketStateObject
from src.prompts import primary_analyzer_prompt
from src.utils.file_io import write_pipeline
from src.utils.validation import strip_json_fences

from anthropic import (
    Anthropic,
    APITimeoutError as AnthropicTimeoutError,
    RateLimitError as AnthropicRateLimitError,
    InternalServerError as AnthropicServerError,
)

from src.llm_backend import LLMBackend, LLMResponse

logger = logging.getLogger(__name__)

# Format-correction message appended on retry (Section 5.7 #6)
_FORMAT_CORRECTION = (
    "Your previous response was not valid JSON. "
    "Please respond with ONLY a valid JSON object. "
    "No text before or after the JSON."
)


_MALFORMED_LOG = Path("shadow_logs/malformed_responses.jsonl")


def _normalize_ai_guard_text(value: object) -> str:
    return str(value or "").strip().lower()


def _enforce_primary_candidate_rate_model_guard(ai_cfg: dict) -> None:
    """Reject primary-analyzer model/effort combos that evidence killed."""
    if not bool(ai_cfg.get("candidate_rate_model_guard_enabled", False)):
        return
    model = _normalize_ai_guard_text(ai_cfg.get("primary_model"))
    effort = _normalize_ai_guard_text(ai_cfg.get("primary_effort"))
    blocked = ai_cfg.get("candidate_rate_blocked_model_efforts", []) or []
    if not isinstance(blocked, list):
        return
    for rule in blocked:
        if not isinstance(rule, dict):
            continue
        rule_model = _normalize_ai_guard_text(rule.get("model"))
        prefixes = [
            _normalize_ai_guard_text(item)
            for item in (rule.get("model_prefixes", []) or [])
            if _normalize_ai_guard_text(item)
        ]
        if rule_model and rule_model != model:
            continue
        if not rule_model and prefixes and not any(model.startswith(prefix) for prefix in prefixes):
            continue
        efforts = rule.get("efforts", []) or []
        effort_set = {_normalize_ai_guard_text(item) for item in efforts}
        if effort not in effort_set:
            continue
        reason = rule.get("reason") or "primary_model_effort_blocked_by_candidate_rate_evidence"
        source_path = rule.get("source_path")
        raise ValueError(
            "PrimaryAnalyzer blocked configured model/effort: "
            f"model={ai_cfg.get('primary_model')!r} effort={ai_cfg.get('primary_effort')!r} "
            f"reason={reason!r} source_path={source_path!r}"
        )


def _log_malformed_response(
    raw_text: str,
    error_msg: str,
    attempt: int = 1,
    *,
    symbol: str | None = None,
    candle_time: str | None = None,
    kill_zone: str | None = None,
    model: str | None = None,
) -> None:
    """Save raw AI response when parsing fails — diagnostic only."""
    try:
        _MALFORMED_LOG.parent.mkdir(parents=True, exist_ok=True)
        raw_text = raw_text or ""
        entry = {
            "schema_version": "ai_malformed_response_v2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempt": attempt,
            "symbol": symbol,
            "candle_time": candle_time,
            "kill_zone": kill_zone,
            "model": model,
            "error": error_msg,
            "raw_response_sha256": stable_sha256(raw_text),
            "raw_response_length": len(raw_text),
            "raw_response": raw_text[:2000],
            "ai_reliability_contract": {
                "deterministic_baseline_contract": build_deterministic_baseline_contract(
                    reason="malformed_response_parse_failure"
                ),
                "fallback_behavior_contract": build_fallback_behavior_contract(
                    reason="ai_output_malformed",
                    response_status="malformed_demoted",
                    parse_attempts=attempt,
                ),
            },
        }
        with open(_MALFORMED_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Never let diagnostic logging crash the pipeline


def _make_no_trade(reason: str, model: str, error: Optional[str] = None) -> PrimaryAnalysisOutput:
    """Build a NO_TRADE output for error/fallback paths."""
    return PrimaryAnalysisOutput(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        model_used=model,
        decision="NO_TRADE",
        confidence_score=0,
        confidence_computation=f"deterministic_fallback:{reason}",
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction="ranging", confidence="low"),
            h4_alignment=H4AlignmentAnalysis(aligned=False),
            h1_setup=H1SetupAnalysis(poi_identified=False),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(choch_detected=False),
        ),
        no_trade_reason=reason,
    )


class PrimaryAnalyzer:
    """AI-powered market analysis using Claude API."""

    def __init__(self, config: dict, kb: KnowledgeBase,
                 llm_backend: Optional[LLMBackend] = None) -> None:
        self.config = config
        self.kb = kb

        ai_cfg = config.get("ai", {})
        self.model = ai_cfg.get("primary_model", "claude-sonnet-4-6")
        self.effort = ai_cfg.get("primary_effort")  # None, "high", or "max"
        _enforce_primary_candidate_rate_model_guard(ai_cfg)
        self.timeout = ai_cfg.get("api_timeout_seconds", 60)
        self.max_retries = ai_cfg.get("max_api_retries", 1)
        # 2026-04-27: gate timeout-retry behind a config flag. During fleet
        # stalls each retry is a fresh cold-cache full-prompt rewrite (~$2-3
        # per request) and the next M15 candle will re-evaluate anyway.
        # Default false; set ai.timeout_retry_enabled=true to restore legacy
        # behavior. Server errors + rate limits retain their retry paths.
        self.timeout_retry_enabled = ai_cfg.get("timeout_retry_enabled", False)

        # LLM backend: injected or default to API mode
        self.backend = llm_backend or LLMBackend(mode="api")
        # Keep direct client reference for API mode backward compat
        self.client = self.backend.get_api_client() if self.backend.mode == "api" else None

    def reset_session_cache(self) -> None:
        """Call at the start of each trading session to reset cached prompts."""
        self._cached_system_blocks = None
        self._cached_directions = None
        self._cached_frameworks_key = None

    @staticmethod
    def _extract_directions(mso) -> tuple:
        """Extract D1/H4 directions for cache invalidation."""
        tfs = getattr(mso, "timeframes", {}) or {}
        dirs = []
        for tf_name in ("D1", "H4"):
            tf = tfs.get(tf_name)
            structure = getattr(tf, "structure", None) if tf else None
            dirs.append(getattr(structure, "direction", "unavailable") if structure else "unavailable")
        return tuple(dirs)

    @property
    def last_system_prompt(self):
        """Return the system prompt blocks from the last analyze() call."""
        return getattr(self, "_last_system_blocks", None)

    @property
    def last_user_message(self) -> str:
        """Return the user message from the last analyze() call."""
        return getattr(self, "_last_user_message", "")

    def _record_ai_decision_trace(
        self,
        *,
        system_prompt,
        user_message: str,
        raw_response: str | None,
        result: PrimaryAnalysisOutput,
        symbol: str | None,
        candle_time: str | None,
        kill_zone: str | None,
        model: str | None,
        response_status: str,
        parse_attempts: int,
    ) -> None:
        record_ai_decision_trace(
            config=self.config,
            system_prompt=system_prompt,
            user_message=user_message,
            raw_response=raw_response,
            result=result,
            usage=getattr(self, "_last_usage", {}),
            symbol=symbol,
            candle_time=candle_time,
            kill_zone=kill_zone,
            model=model or self.model,
            backend_mode=getattr(self.backend, "mode", None),
            response_status=response_status,
            parse_attempts=parse_attempts,
        )

    # ------------------------------------------------------------------
    # Prompt assembly (shared by analyze and batch mode)
    # ------------------------------------------------------------------

    def build_prompt(
        self,
        market_state: MarketStateObject,
        current_time: str,
        kb_context: Optional[dict] = None,
        kill_zone: str = "london",
        session_memory: str = "",
        cross_instrument_context: str = "",
        additional_context: str = "",
        frameworks_override: Optional[list[str]] = None,
    ) -> dict:
        """Build the system prompt and user message WITHOUT making an API call.

        Used by batch mode to pre-compute all prompts before submission.
        Also used internally by analyze().

        *kill_zone*: ``"london"`` or ``"ny"`` — passed through to user message.
        *session_memory*: prior candle evaluations from the current session.
        *cross_instrument_context*: pre-formatted cross-instrument block.
        *additional_context*: pre-formatted extra context (align score, etc.).

        Returns a dict with keys: system, user_message, model, max_tokens, temperature
        """
        effective_config = self.config
        if frameworks_override is not None:
            effective_config = dict(self.config)
            model_a = dict(effective_config.get("model_a", {}) or {})
            model_a["enabled_frameworks"] = [str(item) for item in frameworks_override if str(item)]
            effective_config["model_a"] = model_a

        symbol = effective_config.get("market", {}).get("symbol", "XAUUSD")

        # Belt-and-suspenders: force-empty cross-instrument context for symbols
        # in the strip list. Primary enforcement lives in the orchestrator which
        # skips the fetch entirely; this guards the prompt assembly layer against
        # batch/test/future callers that bypass the orchestrator path.
        disabled_for = effective_config.get("cross_instrument_context_disabled_for", []) or []
        if symbol in disabled_for and cross_instrument_context:
            logger.warning(
                "Stripping cross_instrument_context for %s (disabled by config) — "
                "%d chars discarded", symbol, len(cross_instrument_context),
            )
            cross_instrument_context = ""

        if kb_context is None:
            if symbol == "XAUUSD":
                try:
                    kb_context = self.kb.assemble_full_context(
                        market_state,
                        config=effective_config,
                    )
                except Exception:
                    kb_context = {"layer1": {}, "layer2": {}, "layer3": []}
            else:
                # Non-gold instruments have no instrument-specific KB history yet.
                # Batch tests proved 57-80% WR without KB context.
                kb_context = {"layer1": {}, "layer2": {}, "layer3": []}

        # Static context cached per session — invalidate on D1/H4 direction change
        current_dirs = self._extract_directions(market_state)
        cached_dirs = getattr(self, "_cached_directions", None)
        frameworks_key = tuple(effective_config.get("model_a", {}).get("enabled_frameworks") or ())
        cached_frameworks_key = getattr(self, "_cached_frameworks_key", None)
        if (not hasattr(self, "_cached_system_blocks")
                or self._cached_system_blocks is None
                or cached_dirs != current_dirs
                or cached_frameworks_key != frameworks_key):
            # Set price format for this instrument before building context
            price_fmt = effective_config.get("prompt", {}).get("price_format", ".2f")
            primary_analyzer_prompt.set_price_format(price_fmt)

            static_ctx = primary_analyzer_prompt.build_static_context(market_state)
            system_text = primary_analyzer_prompt.build_system_prompt(effective_config)

            # Gate frameworks based on config.
            # Legacy: strip the "## BREAKER BLOCK RETEST" section from V1/V2
            # prompt formats when neither breaker variant is enabled. V3+ no
            # longer ships that section in the base template, so the strip is
            # a no-op for current production. The ``breaker_re_entry``
            # injection (additive 2026-04-25) is handled inside
            # ``build_system_prompt(config)`` based on the same flag list, so
            # the only remaining responsibility here is the legacy strip.
            enabled_fw = effective_config.get("model_a", {}).get("enabled_frameworks")
            breaker_enabled = bool(enabled_fw) and (
                "breaker_retest" in enabled_fw or "breaker_re_entry" in enabled_fw
            )
            if enabled_fw and not breaker_enabled:
                system_text = _strip_breaker_sections(system_text)

            self._cached_system_blocks = [
                {
                    "type": "text",
                    "text": system_text + "\n\n## Static Context (D1/H4/Session)\n" + static_ctx,
                    # 1h TTL (vs 5m default) protects against fleet stalls on
                    # Windows OS pause/sleep events: a 5+ minute stall expires the
                    # 5m cache and forces 7 cold-cache rewrites on resume (~$15-18
                    # per stall observed 2026-04-27 NY+London KZ open). 1h costs
                    # 2× cache_write (vs 1.25× for 5m) but pays back after 5 reads;
                    # at our M15 cadence and ~7 instruments the writes amortize
                    # within a single KZ. Wire format matches
                    # ``cache_helper.build_cache_control(ttl="1h")``.
                    "cache_control": {"type": "ephemeral", "ttl": "1h"},
                },
            ]
            self._cached_directions = current_dirs
            self._cached_frameworks_key = frameworks_key

        user_msg = primary_analyzer_prompt.build_user_message(
            market_state, kb_context, current_time, kill_zone=kill_zone,
            session_memory=session_memory,
            cross_instrument_context=cross_instrument_context,
            additional_context=additional_context,
        )

        return {
            "system": self._cached_system_blocks,
            "user_message": user_msg,
            "model": self.model,
            "max_tokens": 2000,
            "temperature": 0,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(
        self,
        market_state: MarketStateObject,
        kill_zone: str = "london",
        session_memory: str = "",
        cross_instrument_context: str = "",
        additional_context: str = "",
        frameworks_override: Optional[list[str]] = None,
        ai_call_context: Optional[dict] = None,
    ) -> PrimaryAnalysisOutput:
        """Run the full primary analysis pipeline.

        1. Assemble KB context (three layers).
        2. Build prompts.
        3. Call Claude API.
        4. Parse / validate → retry on malformed.
        5. Write to pipeline state.
        6. Return ``PrimaryAnalysisOutput``.

        *kill_zone*: ``"london"`` or ``"ny"`` — active kill zone window.
        *session_memory*: prior candle evaluations from the current session.
        *cross_instrument_context*: pre-formatted cross-instrument block.
        """
        current_time = datetime.now(timezone.utc).isoformat()
        self._last_usage = {"input_tokens": 0, "output_tokens": 0,
                            "cache_read_tokens": 0, "cache_create_tokens": 0, "_fresh": False}
        policy_decision = evaluate_ai_call_policy(
            config=self.config,
            context=ai_call_context,
            symbol=self.config.get("market", {}).get("symbol"),
            kill_zone=kill_zone,
            candle_time_utc=getattr(market_state, "timestamp_utc", None),
            model=self.model,
        )
        self._last_ai_call_policy_decision = policy_decision
        record_ai_call_policy_decision(
            decision=policy_decision,
            config=self.config,
            phase="primary_analyzer_pre_call",
        )
        if not policy_decision.allowed:
            result = _make_no_trade(f"ai_call_policy:{policy_decision.reason}", self.model)
            self._last_system_blocks = []
            self._last_user_message = ""
            self._write_output(result)
            return result

        # 1+2. Build prompts (shared with batch mode)
        prompt = self.build_prompt(market_state, current_time,
                                   kill_zone=kill_zone, session_memory=session_memory,
                                   cross_instrument_context=cross_instrument_context,
                                   additional_context=additional_context,
                                   frameworks_override=frameworks_override)
        system_blocks = prompt["system"]
        user_msg = prompt["user_message"]

        # Capture for trade_capture
        self._last_system_blocks = system_blocks
        self._last_user_message = user_msg
        malformed_log_context = {
            "symbol": self.config.get("market", {}).get("symbol"),
            "candle_time": getattr(market_state, "timestamp_utc", None),
            "kill_zone": kill_zone,
            "model": self.model,
        }

        # 3+4. Call + parse (with one retry on malformed)
        try:
            raw = await asyncio.get_running_loop().run_in_executor(
                None, self._call_claude, system_blocks, user_msg,
            )
        except _APITimeoutError:
            result = _make_no_trade("api_timeout", self.model)
            self._record_ai_decision_trace(
                system_prompt=system_blocks,
                user_message=user_msg,
                raw_response=None,
                result=result,
                response_status="api_timeout",
                parse_attempts=0,
                **malformed_log_context,
            )
            self._write_output(result)
            return result
        except _APIServerError:
            result = _make_no_trade("api_server_error", self.model)
            self._record_ai_decision_trace(
                system_prompt=system_blocks,
                user_message=user_msg,
                raw_response=None,
                result=result,
                response_status="api_server_error",
                parse_attempts=0,
                **malformed_log_context,
            )
            self._write_output(result)
            return result
        except _APIRateLimitError:
            result = _make_no_trade("api_rate_limit", self.model)
            self._record_ai_decision_trace(
                system_prompt=system_blocks,
                user_message=user_msg,
                raw_response=None,
                result=result,
                response_status="api_rate_limit",
                parse_attempts=0,
                **malformed_log_context,
            )
            self._write_output(result)
            return result
        except Exception as exc:
            result = _make_no_trade(f"unexpected_error: {exc}", self.model)
            self._record_ai_decision_trace(
                system_prompt=system_blocks,
                user_message=user_msg,
                raw_response=None,
                result=result,
                response_status="unexpected_error",
                parse_attempts=0,
                **malformed_log_context,
            )
            self._write_output(result)
            return result

        response_status = "parsed_first_attempt"
        final_raw_response = raw
        parse_attempts = 1
        try:
            result = self._parse_and_validate(raw)
        except Exception as first_err:
            # Retry with format correction
            logger.info("Malformed response — retrying with format correction")
            _log_malformed_response(raw, str(first_err), attempt=1, **malformed_log_context)
            retry_msg = user_msg + "\n\n" + _FORMAT_CORRECTION
            raw2 = ""
            try:
                raw2 = await asyncio.get_running_loop().run_in_executor(
                    None, self._call_claude, system_blocks, retry_msg,
                )
                result = self._parse_and_validate(raw2)
                response_status = "parsed_retry"
                final_raw_response = raw2
                parse_attempts = 2
            except Exception as retry_err:
                _log_malformed_response(raw2, str(retry_err), attempt=2, **malformed_log_context)
                result = _make_no_trade("ai_output_malformed", self.model)
                response_status = "malformed_demoted"
                final_raw_response = raw2
                parse_attempts = 2

        # Guard against CANDIDATE with null trade_parameters
        result = guard_candidate_null_params(result)
        # Guard against FX-precision-bug degeneracy (entry==SL or entry==TP1)
        result = guard_candidate_degenerate_params(result)
        # Guard against wrong-side SL (LONG with SL>entry, SHORT with SL<entry) —
        # PROMPT V2 backstop for self-check failure; addresses the 63.6% GBPUSD
        # L2-reject rate documented in fa3_t7_rerun_report.md §2 D1 + handoff 36.
        # Runs BEFORE inconsistent_pois so the distinct wrong_side_sl reason code
        # is preserved (per V8 review recommendation).
        result = guard_candidate_wrong_side_sl(result)
        # Guard against AI citing different OBs for POI / entry / SL
        # (Thursday 2026-04-23 US30 NY 16:00 class of bug). Runs AFTER the
        # wrong_side_sl + degenerate guards so non-zero fields + correct
        # geometry are assumed here.
        # Precision-aware (HALLUC-1 fix 2026-04-27): pass price_format so the
        # guard snaps OB bounds to the same display precision the AI was
        # shown. Without this, instruments with .1f precision (NAS100) and
        # OB.high underlying floats whose 2nd decimal is >=5 trigger a 100%
        # deterministic demotion (NAS100 2026-04-27 93% rate).
        price_format = self.config.get("prompt", {}).get("price_format", ".2f")
        result = guard_candidate_inconsistent_pois(
            result, market_state, price_format=price_format,
        )

        self._record_ai_decision_trace(
            system_prompt=system_blocks,
            user_message=user_msg,
            raw_response=final_raw_response,
            result=result,
            response_status=response_status,
            parse_attempts=parse_attempts,
            **malformed_log_context,
        )
        self._write_output(result)
        return result

    # ------------------------------------------------------------------
    # Claude API call
    # ------------------------------------------------------------------

    def _call_claude(self, system_prompt, user_message: str) -> str:
        """Call the LLM with retry logic.

        Routes through API SDK or CLI subscription based on self.backend.mode.

        *system_prompt* can be a string or a list of content blocks (for caching).

        Raises:
            _APITimeoutError: on timeout after retry.
            _APIServerError: on 500 after retry.
            _APIRateLimitError: on rate limit after retry.
        """
        # --- Subscription mode: use LLMBackend (no SDK retry logic) ---
        if self.backend.mode == "subscription":
            return self._call_claude_subscription(system_prompt, user_message)

        # --- API mode: existing SDK behavior with retry logic ---
        for attempt in range(1 + self.max_retries):
            try:
                create_kwargs = dict(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                    timeout=self.timeout,
                )
                if self.effort:
                    create_kwargs["output_config"] = {"effort": self.effort}
                response = self.client.messages.create(**create_kwargs)
                # Track ALL token usage (accumulate across retries)
                usage = response.usage
                cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
                cache_create = getattr(usage, "cache_creation_input_tokens", 0) or 0
                if not hasattr(self, "_last_usage") or self._last_usage.get("_fresh", True):
                    self._last_usage = {"input_tokens": 0, "output_tokens": 0,
                                        "cache_read_tokens": 0, "cache_create_tokens": 0, "_fresh": False}
                self._last_usage["input_tokens"] += usage.input_tokens
                self._last_usage["output_tokens"] += usage.output_tokens
                self._last_usage["cache_read_tokens"] += cache_read
                self._last_usage["cache_create_tokens"] += cache_create

                # T1.4 — model-id pinning + drift alert. Additive monitoring,
                # wrapped so any failure here cannot break the trading path.
                try:
                    served_model = getattr(response, "model", None)
                    response_id = getattr(response, "id", None)
                    _model_pin.record_served_model(self.model, served_model, response_id)
                except Exception as exc:
                    logger.warning("model_pin record failed (ignored): %s", exc)

                return response.content[0].text

            except AnthropicTimeoutError:
                # 2026-04-27: timeout retries gated by ai.timeout_retry_enabled
                # (default false). During fleet stalls each retry is a cold-cache
                # full-prompt rewrite — fail-soft and let the next M15 candle pick
                # up. Server errors + rate limits keep retrying as before.
                if self.timeout_retry_enabled and attempt < self.max_retries:
                    logger.warning("API timeout — retrying (attempt %d)", attempt + 1)
                    continue
                raise _APITimeoutError("API timeout (retry gated by ai.timeout_retry_enabled)")

            except AnthropicRateLimitError as exc:
                retry_after = getattr(exc, "retry_after", None) or 5
                if attempt < self.max_retries:
                    logger.warning("Rate limited — waiting %ss", retry_after)
                    time.sleep(float(retry_after))
                    continue
                raise _APIRateLimitError("Rate limit after retries")

            except AnthropicServerError:
                if attempt < self.max_retries:
                    logger.warning("API 500 — retrying after 5s")
                    time.sleep(5)
                    continue
                raise _APIServerError("API 500 after retries")

        raise _APIServerError("Exhausted retries")

    def _call_claude_subscription(self, system_prompt, user_message: str) -> str:
        """Route through LLMBackend subscription mode with retry.

        Subscription mode uses higher retry count and longer backoff
        because the CLI has more latency than the SDK and Max plan
        usage limits can cause intermittent empty responses.
        """
        # Subscription gets more retries — CLI is less reliable than SDK
        max_retries = max(self.max_retries, 2)
        for attempt in range(1 + max_retries):
            try:
                llm_resp = self.backend.call(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    model=self.model,
                    max_tokens=1500,
                    temperature=0,
                    timeout=self.timeout,
                )
                # Track usage (subscription mode won't have real token counts)
                if not hasattr(self, "_last_usage") or self._last_usage.get("_fresh", True):
                    self._last_usage = {"input_tokens": 0, "output_tokens": 0,
                                        "cache_read_tokens": 0, "cache_create_tokens": 0, "_fresh": False}
                self._last_usage["input_tokens"] += llm_resp.usage.input_tokens
                self._last_usage["output_tokens"] += llm_resp.usage.output_tokens
                return llm_resp.text

            except RuntimeError as exc:
                err_msg = str(exc)
                if "timed out" in err_msg:
                    if attempt < max_retries:
                        logger.warning("CLI timeout — retrying (attempt %d)", attempt + 1)
                        time.sleep(5)
                        continue
                    raise _APITimeoutError(f"CLI timeout after retries: {err_msg}")
                if attempt < max_retries:
                    wait = 5 * (attempt + 1)  # Progressive backoff: 5s, 10s, 15s
                    logger.warning("CLI error — retrying in %ds: %s", wait, err_msg)
                    time.sleep(wait)
                    continue
                raise _APIServerError(f"CLI error after retries: {err_msg}")

        raise _APIServerError("Exhausted retries (subscription)")

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_and_validate(self, raw_response: str) -> PrimaryAnalysisOutput:
        """Strip fences, parse JSON, normalize known variants, validate."""
        supervisor_cfg = ((getattr(self, "config", {}) or {}).get("ai_supervisor", {}) or {})
        if bool(supervisor_cfg.get("format_repair_enabled", True)):
            repair = repair_ai_response_format_preserving_semantics(raw_response)
            cleaned = repair.repaired_text if repair.repaired else strip_json_fences(raw_response)
        else:
            cleaned = strip_json_fences(raw_response)
        data = json.loads(cleaned)
        _normalize_pa_fields(data)
        data["model_used"] = self.model  # Override AI-reported model name with config value
        result = PrimaryAnalysisOutput.model_validate(data)
        _warn_tp1_placement(result)
        return result

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _write_output(self, result: PrimaryAnalysisOutput) -> None:
        write_pipeline(
            "03a_primary_analysis.json",
            result.model_dump(mode="json"),
        )


def _normalize_pa_fields(data: dict) -> None:
    """Fix common AI field-value mismatches before Pydantic validation."""
    r = data.get("reasoning", {})
    if not r:
        return

    # pool_type normalization (case-insensitive + common AI variants)
    _VALID_POOLS = {
        "asian_high", "asian_low", "pdh", "pdl",
        "equal_highs", "equal_lows",
        "session_high", "session_low",
        "london_high", "london_low",
        "none",
    }
    _POOL_MAP = {
        "equal_high": "equal_highs", "equal_low": "equal_lows",
        "session_high": "session_high", "session_low": "session_low",
        "pdh run": "pdh", "pdl run": "pdl",
        "previous day high": "pdh", "previous day low": "pdl",
        "prev day high": "pdh", "prev day low": "pdl",
        "asian high": "asian_high", "asian low": "asian_low",
        "london high": "london_high", "london low": "london_low",
    }
    sweep = r.get("liquidity_sweep", {})
    if sweep:
        pt = sweep.get("pool_type", "")
        pt_lower = pt.lower().strip()
        if pt_lower in _VALID_POOLS:
            # Simple lowercase match ("PDH" → "pdh", "Session_High" → "session_high")
            sweep["pool_type"] = pt_lower
        elif pt_lower in _POOL_MAP:
            # Verbose variant ("previous day high" → "pdh", "asian high" → "asian_high")
            sweep["pool_type"] = _POOL_MAP[pt_lower]
        elif pt:
            # Compound values ("session_high / equal_highs", "PDL and session_high", "PDH sweep")
            tokens = [t.strip() for t in pt_lower.replace("+", "/").replace(" and ", "/").split("/")]
            resolved = None
            for tok in tokens:
                tok_clean = tok.split()[0] if tok.split() else tok  # strip trailing noise words
                if tok_clean in _VALID_POOLS:
                    resolved = tok_clean
                    break
                if tok_clean in _POOL_MAP:
                    resolved = _POOL_MAP[tok_clean]
                    break
            sweep["pool_type"] = resolved if resolved else "none"
        else:
            sweep["pool_type"] = "none"

    # poi_type normalization
    h1 = r.get("h1_setup", {})
    if h1:
        pt = h1.get("poi_type", "")
        _POI_MAP = {
            "order_block": "OB", "ob": "OB",
            "fair_value_gap": "FVG", "fvg": "FVG",
            "liquidity": "liquidity_zone",
            "breaker": "breaker_block", "breaker_block": "breaker_block",
        }
        if pt.lower() in _POI_MAP:
            h1["poi_type"] = _POI_MAP[pt.lower()]

    # causing_event_type normalization
    if h1:
        cet = h1.get("causing_event_type", "unknown")
        _CET_MAP = {
            "bos": "BOS", "choch": "CHoCH", "CHoCH": "CHoCH", "BOS": "BOS",
            "price_action": "price_action", "mitigation": "price_action",
        }
        if cet in _CET_MAP:
            h1["causing_event_type"] = _CET_MAP[cet]
        elif cet not in ("BOS", "CHoCH", "price_action", "unknown"):
            h1["causing_event_type"] = "unknown"

    # setup_grade normalization — clamp to valid values
    grade = r.get("setup_grade", "C")
    if grade not in ("A+", "A", "B+", "B", "C"):
        _GRADE_MAP = {"A-": "B+", "B-": "C", "D": "C", "F": "C"}
        r["setup_grade"] = _GRADE_MAP.get(grade, "C")

    # framework normalization
    fw = data.get("framework", "none")
    _FW_MAP = {
        "session_liquidity_sweep": "session_sweep",
        "liquidity_sweep": "session_sweep",
        "ob_retest_bos": "ob_retest",
        "order_block_retest": "ob_retest",
        # Common AI aliases for the active breaker route must normalize to
        # the production-facing framework. The exact legacy literal
        # ``breaker_retest`` remains valid below for historical records, but
        # alias text should not bypass the active breaker_re_entry L2 check.
        "breaker_block_retest": "breaker_re_entry",
        "breaker_block": "breaker_re_entry",
        "breaker": "breaker_re_entry",
        "equal_highs_lows": "equal_sweep",
        "equal_hl_sweep": "equal_sweep",
        "fvg_fill_pd": "fvg_fill",
        "fvg": "fvg_fill",
    }
    _VALID_FRAMEWORKS = {
        "session_sweep", "ob_retest", "breaker_retest",
        # ``breaker_re_entry`` is the explicit-naming variant used by config
        # ``model_a.enabled_frameworks`` from 2026-04-25 onwards (FTMO challenge
        # activation). The legacy ``breaker_retest`` exact label remains valid
        # for historical fixtures.
        "breaker_re_entry",
        "equal_sweep", "fvg_fill", "none",
    }
    if fw:
        fw_key = str(fw).strip().lower()
    else:
        fw_key = ""
    if fw_key in _FW_MAP:
        data["framework"] = _FW_MAP[fw_key]
    elif fw not in _VALID_FRAMEWORKS:
        data["framework"] = "none"

    frameworks_evaluated = data.get("frameworks_evaluated")
    if isinstance(frameworks_evaluated, dict):
        normalized_evals = {}
        for raw_name, raw_eval in frameworks_evaluated.items():
            raw_key = str(raw_name).strip().lower()
            canonical_name = _FW_MAP.get(raw_key, raw_name)
            if canonical_name not in _VALID_FRAMEWORKS:
                canonical_name = "none"
            if canonical_name in normalized_evals:
                prior = normalized_evals[canonical_name]
                prior_qualified = False
                if isinstance(prior, dict):
                    prior_qualified = bool(prior.get("qualified"))
                raw_qualified = False
                if isinstance(raw_eval, dict):
                    raw_qualified = bool(raw_eval.get("qualified"))
                if isinstance(prior, dict) and isinstance(raw_eval, dict):
                    prior["qualified"] = prior_qualified or raw_qualified
                    prior_reason = str(prior.get("reason") or "")
                    raw_reason = str(raw_eval.get("reason") or "")
                    if raw_reason and raw_reason not in prior_reason:
                        prior["reason"] = (
                            f"{prior_reason}; {raw_reason}"
                            if prior_reason else raw_reason
                        )
                continue
            normalized_evals[canonical_name] = raw_eval
        data["frameworks_evaluated"] = normalized_evals

    # kill_zone normalization
    kz_raw = data.get("kill_zone", "london")
    kz = str(kz_raw).strip().lower().replace("-", "_").replace(" ", "_")
    _KZ_MAP = {
        "ldn": "london",
        "london_core": "london",
        "new_york": "ny",
        "new_york_core": "ny",
        "ny_core": "ny",
        "tokyo_kz": "tokyo",
        "asia": "tokyo",
        "asian": "tokyo",
        "asian_session": "tokyo",
    }
    data["kill_zone"] = _KZ_MAP.get(kz, kz if kz in ("london", "ny", "tokyo") else "london")

    # (london_high / london_low now handled by _VALID_POOLS above)


def _strip_breaker_sections(prompt: str) -> str:
    """Remove breaker block framework sections from the PA prompt.

    Works with the Phase 2A v1 scored prompt format.
    """
    import re
    # Remove the breaker block section (Phase 2A v1 format)
    prompt = re.sub(
        r'## BREAKER BLOCK RETEST \(alternative framework\).*?(?=## TARGETS)',
        '',
        prompt,
        flags=re.DOTALL,
    )
    # Also handle legacy format (pre-Phase 2A)
    prompt = re.sub(
        r'---\s*\n\s*## H1 BREAKER BLOCK RETEST.*?(?=---\s*\n\s*## (?:SETUP GRADING|QUALITY SIGNALS))',
        '',
        prompt,
        flags=re.DOTALL,
    )
    return prompt


def _warn_tp1_placement(result: PrimaryAnalysisOutput) -> None:
    """Log a warning if CANDIDATE has TP1 outside the 1.3R–2.0R accepted band."""
    if result.decision != "CANDIDATE" or result.trade_parameters is None:
        return
    tp = result.trade_parameters
    sl_dist = abs(tp.entry_price - tp.stop_loss)
    if sl_dist < 1e-6:
        return
    tp1_dist = abs(tp.take_profit_1 - tp.entry_price)
    tp1_r = tp1_dist / sl_dist
    if tp1_r < 1.3:
        logger.warning(
            "TP1 placement warning: TP1 at %.2fR is below 1.3R minimum — "
            "will be rejected by tp1_too_close gate. (entry=%.5f, SL=%.5f, TP1=%.5f)",
            tp1_r, tp.entry_price, tp.stop_loss, tp.take_profit_1,
        )
    elif tp1_r > 2.0:
        logger.warning(
            "TP1 placement warning: TP1 at %.2fR exceeds 2.0R maximum — "
            "will be rejected by tp1_too_far gate. (entry=%.5f, SL=%.5f, TP1=%.5f)",
            tp1_r, tp.entry_price, tp.stop_loss, tp.take_profit_1,
        )
    # TP1 on wrong side of entry
    if tp.direction == "LONG" and tp.take_profit_1 <= tp.entry_price:
        logger.error("TP1 BELOW ENTRY for LONG: TP1=%.5f, entry=%.5f", tp.take_profit_1, tp.entry_price)
    elif tp.direction == "SHORT" and tp.take_profit_1 >= tp.entry_price:
        logger.error("TP1 ABOVE ENTRY for SHORT: TP1=%.5f, entry=%.5f", tp.take_profit_1, tp.entry_price)


# ── Precision-aware snapping helpers ───────────────────────────────────
# Promoted to ``src/components/precision.py`` (sister-bug branch
# 2026-04-27) so verification.py + m5_refinement.py can share the same
# helpers introduced by HALLUC-1. They are re-imported above and re-
# exported as module-level names so the existing
# ``tests/test_precision_aware_guards.py`` import surface is unchanged
# (``from src.components.primary_analyzer import _decimals_from_format,
# _snap_to_precision``).


def guard_candidate_null_params(result: PrimaryAnalysisOutput) -> PrimaryAnalysisOutput:
    """Demote CANDIDATE to NO_TRADE if trade_parameters is None.

    Call this after parsing to prevent crashes downstream.
    """
    if result.decision == "CANDIDATE" and result.trade_parameters is None:
        logger.warning("CANDIDATE returned with null trade_parameters — demoting to NO_TRADE")
        result.decision = "NO_TRADE"
        if result.reasoning:
            result.reasoning.overall_reasoning += " [SYSTEM: Demoted from CANDIDATE — null trade_parameters]"
        result.no_trade_reason = "ai_output_malformed"
    return result


def guard_candidate_degenerate_params(result: PrimaryAnalysisOutput) -> PrimaryAnalysisOutput:
    """Demote CANDIDATE to NO_TRADE if entry==SL or entry==TP1 bit-exactly.

    Catches the FX precision bug documented in Phase 4 Chairman Synthesis
    Change 2: AI renders FX prices at 2-dp on 4-5-dp instruments, collapsing
    entry/SL/TP1 to the same rounded value. β Finding 1 quantified 59.67%
    of EURUSD CANDIDATEs as bit-exactly degenerate.
    """
    if result.decision != "CANDIDATE" or result.trade_parameters is None:
        return result
    tp = result.trade_parameters
    reasons = []
    if math.isclose(tp.entry_price, tp.stop_loss, abs_tol=1e-9):
        reasons.append(f"entry_price==stop_loss ({tp.entry_price})")
    if math.isclose(tp.entry_price, tp.take_profit_1, abs_tol=1e-9):
        reasons.append(f"entry_price==take_profit_1 ({tp.entry_price})")
    if reasons:
        logger.error(
            "CANDIDATE has degenerate trade_parameters: %s — demoting to NO_TRADE",
            "; ".join(reasons),
        )
        result.decision = "NO_TRADE"
        if result.reasoning:
            result.reasoning.overall_reasoning += (
                f" [SYSTEM: Demoted from CANDIDATE — degenerate_trade_parameters: {'; '.join(reasons)}]"
            )
        result.no_trade_reason = "degenerate_trade_parameters"
    return result


def guard_candidate_wrong_side_sl(result: PrimaryAnalysisOutput) -> PrimaryAnalysisOutput:
    """Demote CANDIDATE to NO_TRADE if SL is on the geometrically wrong side of entry.

    PROMPT V2 backstop — complements the prompt-level self-check. Catches the
    case observed in GBPUSD Thursday 2026-04-23: 63.6% of L2 rejects had
    `sl_beyond_ob` FAIL because Sonnet-4-6 emitted SL > entry for LONG (a
    protective stop is geometrically impossible on the wrong side of entry).

    Rules:
      - LONG: stop_loss must be STRICTLY below entry_price.
      - SHORT: stop_loss must be STRICTLY above entry_price.
      - Equality (SL == entry) is already caught by
        `guard_candidate_degenerate_params`; this guard targets the
        wrong-side case specifically.

    Evidence:
      - fa3_t7_rerun_report.md §2 D1 (EURUSD 59% degeneracy, 63.6% GBPUSD L2 fail)
      - Thursday 2026-04-23 GBPUSD audit (referenced in handoff 36 §"Known gaps #4")
    """
    if result.decision != "CANDIDATE" or result.trade_parameters is None:
        return result
    tp = result.trade_parameters
    # Degenerate equality is handled by guard_candidate_degenerate_params;
    # this guard only fires on STRICT wrong-side violations.
    if math.isclose(tp.entry_price, tp.stop_loss, abs_tol=1e-9):
        return result
    reason = None
    if tp.direction == "LONG" and tp.stop_loss > tp.entry_price:
        reason = (
            f"LONG with stop_loss={tp.stop_loss} > entry_price={tp.entry_price} "
            f"(SL must be strictly below entry for LONG)"
        )
    elif tp.direction == "SHORT" and tp.stop_loss < tp.entry_price:
        reason = (
            f"SHORT with stop_loss={tp.stop_loss} < entry_price={tp.entry_price} "
            f"(SL must be strictly above entry for SHORT)"
        )
    if reason:
        logger.error(
            "CANDIDATE has wrong-side stop_loss: %s — demoting to NO_TRADE",
            reason,
        )
        result.decision = "NO_TRADE"
        if result.reasoning:
            result.reasoning.overall_reasoning += (
                f" [SYSTEM: Demoted from CANDIDATE — wrong_side_sl: {reason}]"
            )
        result.no_trade_reason = "wrong_side_sl"
    return result


def guard_candidate_inconsistent_pois(
    result: PrimaryAnalysisOutput,
    mso: MarketStateObject,
    price_format: Optional[str] = None,
) -> PrimaryAnalysisOutput:
    """Demote CANDIDATE when poi_price_level and entry_price do not reference
    the SAME H1 order block (precision-aware against the AI's display view).

    Catches a class of AI-output bug observed on Thursday 2026-04-23 US30 NY
    16:00: the AI cited one OB via ``poi_price_level`` (touches=4 OB
    midpoint), another OB via ``entry_price`` (touches=2 OB high). The
    inconsistency manifested when the AI mentally bound to a different OB
    than the POI it cited.

    PRECISION-AWARE (HALLUC-1 fix, 2026-04-27):
      The MSO renders OB.high / OB.low at the instrument's
      ``prompt.price_format`` (e.g. ".1f" for NAS100). The AI emits
      ``entry_price`` at that same precision. Comparisons against the
      underlying floats must snap the floats to the AI's display view
      first — otherwise a sub-tick rounding delta (e.g. underlying
      27262.16 → rendered 27262.2 → AI emits 27262.2 → 27262.2 <= 27262.16
      is False) forces a deterministic violation. Sister bug class to
      ``project_eurusd_sl_root_cause``.

      *price_format* defaults to ``None`` (back-compat) which selects
      ``.2f`` (XAUUSD-style 2-dp). Production callers pass the value
      from ``config.prompt.price_format``.

    Logic:
      1) Locate the H1 OB whose RENDERED bounds contain ``poi_price_level``.
         If no OB matches, defer to L2 ``h1_poi_exists`` / pre-AI gate.
      2) If multiple H1 OBs match (rendered bounds overlap), pick the one
         whose nearest rendered edge is closest to ``entry_price``.
      3) Require ``entry_price`` to lie inside ``[rendered_low, rendered_high]``.
      4) Defensive TP1 direction check (overlaps with prompt self-check;
         AI-emitted vs AI-emitted comparison so no precision-snap needed):
           LONG  → ``take_profit_1 > entry_price``
           SHORT → ``take_profit_1 < entry_price``

    SL-vs-OB-edge check REMOVED (HALLUC-1 P1 fix): the prompt instructs SL
    placement beyond the H1/M15 swing low (LONG) or swing high (SHORT), not
    beyond the OB's far edge. Two-thirds of the NAS100 2026-04-27 demotion
    rate were this prompt-vs-guard contradiction. The existing tolerance-
    tier ``sl_beyond_ob`` L2 gate (verification.py:127-145) is the correct
    enforcement layer; it is config-driven via
    ``verification.sl_beyond_ob_tick_floor``.

    Runs AFTER ``guard_candidate_wrong_side_sl`` and
    ``guard_candidate_degenerate_params`` — assumes non-degenerate
    entry/SL/TP1 fields and correct SL-side-of-entry.
    """
    if result.decision != "CANDIDATE" or result.trade_parameters is None:
        return result

    tp = result.trade_parameters
    h1_setup = result.reasoning.h1_setup if result.reasoning else None
    poi_level = getattr(h1_setup, "poi_price_level", 0.0) if h1_setup else 0.0

    # Pydantic default is 0.0 (not None); treat 0.0 as "not reported" and defer.
    if poi_level == 0.0:
        return result

    # Locate H1 timeframe — conservative passthrough if missing.
    h1_tf = mso.timeframes.get("H1") if mso and mso.timeframes else None
    if h1_tf is None:
        return result

    # Resolve display precision the AI was shown. Fall back to ".2f"
    # (XAUUSD legacy default in build_prompt) for back-compat with callers
    # that don't supply it (e.g. unit tests built around XAUUSD numbers).
    fmt = price_format if price_format else ".2f"
    decimals = _decimals_from_format(fmt)
    if decimals is None:
        # Unrecognized format — bail out conservatively (do not demote).
        # We'd rather under-block than mis-block on a misconfigured profile.
        decimals = 2

    def _rlow(ob) -> float:
        return _snap_to_precision(ob.low, decimals)

    def _rhigh(ob) -> float:
        return _snap_to_precision(ob.high, decimals)

    # Match POI to OBs using the rendered bounds — the AI only ever saw
    # the rendered values, so use the same precision plane the AI used.
    matching_obs = [
        ob for ob in h1_tf.order_blocks
        if _rlow(ob) <= poi_level <= _rhigh(ob)
    ]

    # POI level not inside any H1 OB — separate issue handled by L2
    # ``h1_poi_exists`` or the pre-AI availability gate. Do not demote here.
    if not matching_obs:
        return result

    if len(matching_obs) > 1:
        # Ambiguous overlap — pick the OB whose nearest rendered edge is
        # closest to the AI-reported entry_price (tightest fit, on the
        # same precision plane).
        matching_ob = min(
            matching_obs,
            key=lambda ob: min(
                abs(_rlow(ob) - tp.entry_price),
                abs(_rhigh(ob) - tp.entry_price),
            ),
        )
    else:
        matching_ob = matching_obs[0]

    matched_low = _rlow(matching_ob)
    matched_high = _rhigh(matching_ob)

    reasons: list[str] = []

    # Entry must lie inside the matched OB AS THE AI SAW IT (rendered bounds).
    if not (matched_low <= tp.entry_price <= matched_high):
        reasons.append(
            f"entry_price {tp.entry_price} outside matched OB "
            f"[{matched_low}, {matched_high}]"
        )

    # Defensive TP1 direction check (AI-vs-AI; no precision snapping needed).
    if tp.direction == "LONG":
        if not tp.take_profit_1 > tp.entry_price:
            reasons.append(
                f"take_profit_1 {tp.take_profit_1} <= entry_price "
                f"{tp.entry_price} for LONG"
            )
    else:  # SHORT
        if not tp.take_profit_1 < tp.entry_price:
            reasons.append(
                f"take_profit_1 {tp.take_profit_1} >= entry_price "
                f"{tp.entry_price} for SHORT"
            )

    if reasons:
        touches = getattr(matching_ob, "touch_count", "?")
        detail = (
            f"poi_price_level {poi_level} maps to OB "
            f"[{matched_low}, {matched_high}] "
            f"(touches={touches}, fmt={fmt}), but: {'; '.join(reasons)}"
        )
        logger.error(
            "CANDIDATE has inconsistent POI references — demoting to NO_TRADE: %s",
            detail,
        )
        result.decision = "NO_TRADE"
        if result.reasoning:
            result.reasoning.overall_reasoning += (
                f" [SYSTEM: Demoted from CANDIDATE — ai_output_inconsistent_pois: {detail}]"
            )
        result.no_trade_reason = "ai_output_inconsistent_pois"
    return result


# ── Internal exception hierarchy (not exposed) ───────────────────────

class _APITimeoutError(Exception):
    pass


class _APIServerError(Exception):
    pass


class _APIRateLimitError(Exception):
    pass
