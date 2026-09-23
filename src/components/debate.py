"""Component 3B — Bull/Bear Debate.

Subjects CANDIDATE trades to adversarial debate.
Confirmation bias prevention mechanism using Bull agent,
Bear agent, and Judge.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from anthropic import (
    Anthropic,
    APITimeoutError as AnthropicTimeoutError,
    InternalServerError as AnthropicServerError,
    RateLimitError as AnthropicRateLimitError,
)

from src.llm_backend import LLMBackend

from src.models.analysis_models import PrimaryAnalysisOutput
from src.models.debate_models import (
    BearArgument,
    BullArgument,
    BullKeyPoint,
    DebateRound2,
    DebateVerdict,
    Rebuttal,
)
from src.models.market_state_models import MarketStateObject
from src.prompts import (
    bear_agent_prompt,
    bull_agent_prompt,
    judge_prompt,
)
from src.utils.file_io import write_pipeline
from src.utils.validation import strip_json_fences

logger = logging.getLogger(__name__)

_FORMAT_CORRECTION = (
    "Your previous response was not valid JSON. "
    "Please respond with ONLY a valid JSON object. "
    "No text before or after the JSON."
)


def _make_rejection_verdict(reason: str, model: str) -> DebateVerdict:
    """Build a REJECT verdict for error / fallback paths."""
    return DebateVerdict(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        model_used=model,
        verdict="REJECT",
        winning_perspective="BEAR",
        confidence_score=0,
        bull_argument_strength=0,
        bear_argument_strength=0,
        key_factor=reason,
        summary=f"Debate could not complete: {reason}",
    )


class DebateEngine:
    """Adversarial Bull/Bear debate for CANDIDATE trades."""

    def __init__(self, config: dict, kb: "KnowledgeBase",  # noqa: F821
                 llm_backend: Optional[LLMBackend] = None) -> None:
        ai_cfg = config.get("ai", {})
        self.model = ai_cfg.get("debate_model", "claude-sonnet-4-20250514")
        self.timeout = ai_cfg.get("api_timeout_seconds", 30)
        self.max_retries = ai_cfg.get("max_api_retries", 1)
        self.round2_enabled = ai_cfg.get("debate_round2_enabled", True)
        self.kb = kb
        # LLM backend: injected or default to API mode
        self.backend = llm_backend or LLMBackend(mode="api")
        self.client = self.backend.get_api_client() if self.backend.mode == "api" else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_debate(
        self,
        market_state: MarketStateObject,
        primary_analysis: PrimaryAnalysisOutput,
        kb_context: dict,
    ) -> DebateVerdict:
        """Run the full debate: R1 (parallel) → R2 (optional) → Judge."""

        # ── Round 1 — concurrent ──────────────────────────────────────
        bull_r1, bear_r1 = await self._run_round1(
            market_state, primary_analysis, kb_context,
        )

        # Both failed → cannot debate
        if bull_r1 is None and bear_r1 is None:
            v = _make_rejection_verdict("both_agents_failed", self.model)
            self._write_verdict(v)
            return v

        # One failed → provide note to Judge, proceed
        missing_note: Optional[str] = None
        if bull_r1 is None:
            v = _make_rejection_verdict("bull_agent_api_failure", self.model)
            self._write_verdict(v)
            return v
        if bear_r1 is None:
            v = _make_rejection_verdict("bear_agent_api_failure", self.model)
            self._write_verdict(v)
            return v

        # Write Round 1
        write_pipeline("03b_debate_round1.json", {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "bull_argument": bull_r1.model_dump(mode="json"),
            "bear_argument": bear_r1.model_dump(mode="json"),
        })

        # ── Round 2 — sequential (if enabled) ─────────────────────────
        round2: Optional[DebateRound2] = None
        if self.round2_enabled:
            round2 = await self._run_round2(bull_r1, bear_r1)
            if round2 is not None:
                write_pipeline("03b_debate_round2.json",
                               round2.model_dump(mode="json"))
            else:
                logger.warning("Round 2 failed — proceeding with Round 1 only")

        # ── Judge ─────────────────────────────────────────────────────
        verdict = await self._run_judge(
            primary_analysis, bull_r1, bear_r1, round2,
        )
        if verdict is None:
            verdict = _make_rejection_verdict("judge_api_failure", self.model)

        self._write_verdict(verdict)
        return verdict

    # ------------------------------------------------------------------
    # Verdict evaluation (deterministic, no AI)
    # ------------------------------------------------------------------

    @staticmethod
    def evaluate_verdict(verdict: DebateVerdict) -> str:
        """Map a DebateVerdict to a lifecycle decision string.

        Returns one of: ``"APPROVED"``, ``"APPROVED_MARGINAL"``, ``"REJECTED"``.
        """
        if verdict.verdict == "REJECT":
            return "REJECTED"

        if verdict.verdict == "APPROVE":
            if verdict.confidence_score >= 70:
                return "APPROVED"
            elif verdict.confidence_score >= 50:
                return "APPROVED_MARGINAL"
            else:
                return "REJECTED"

        return "REJECTED"  # any ambiguity → reject

    # ------------------------------------------------------------------
    # Individual agent runners
    # ------------------------------------------------------------------

    async def _run_round1(
        self,
        market_state: MarketStateObject,
        primary_analysis: PrimaryAnalysisOutput,
        kb_context: dict,
    ) -> tuple[Optional[BullArgument], Optional[BearArgument]]:
        # Run sequentially to ensure deterministic ordering.
        # (Bull and bear each take ~1-2s; parallel saves <2s but
        #  causes non-deterministic executor scheduling on Python 3.13+.)
        try:
            bull = await self._run_bull(market_state, primary_analysis, kb_context)
        except Exception:
            bull = None
        try:
            bear = await self._run_bear(market_state, primary_analysis, kb_context)
        except Exception:
            bear = None
        return bull, bear

    async def _run_bull(
        self,
        market_state: MarketStateObject,
        primary_analysis: PrimaryAnalysisOutput,
        kb_context: dict,
    ) -> BullArgument:
        system = bull_agent_prompt.SYSTEM_PROMPT
        user_msg = bull_agent_prompt.build_user_message(
            market_state, primary_analysis, kb_context,
        )
        raw = await self._call_agent(system, user_msg, "bull")
        return self._parse(raw, BullArgument)

    async def _run_bear(
        self,
        market_state: MarketStateObject,
        primary_analysis: PrimaryAnalysisOutput,
        kb_context: dict,
    ) -> BearArgument:
        system = bear_agent_prompt.SYSTEM_PROMPT
        user_msg = bear_agent_prompt.build_user_message(
            market_state, primary_analysis, kb_context,
        )
        raw = await self._call_agent(system, user_msg, "bear")
        return self._parse(raw, BearArgument)

    async def _run_round2(
        self,
        bull_r1: BullArgument,
        bear_r1: BearArgument,
    ) -> Optional[DebateRound2]:
        try:
            bull_reb = await self._run_bull_rebuttal(bull_r1, bear_r1)
            bear_reb = await self._run_bear_rebuttal(bear_r1, bull_r1)
            return DebateRound2(
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                bull_rebuttal=bull_reb,
                bear_rebuttal=bear_reb,
            )
        except Exception as exc:
            logger.warning("Round 2 failed: %s", exc)
            return None

    async def _run_bull_rebuttal(
        self, bull_r1: BullArgument, bear_r1: BearArgument,
    ) -> Rebuttal:
        system = judge_prompt.BULL_REBUTTAL_SYSTEM_PROMPT
        user_msg = judge_prompt.build_rebuttal_message(
            bull_r1, bear_r1, "bull",
        )
        raw = await self._call_agent(system, user_msg, "bull_rebuttal")
        return self._parse(raw, Rebuttal)

    async def _run_bear_rebuttal(
        self, bear_r1: BearArgument, bull_r1: BullArgument,
    ) -> Rebuttal:
        system = judge_prompt.BEAR_REBUTTAL_SYSTEM_PROMPT
        user_msg = judge_prompt.build_rebuttal_message(
            bear_r1, bull_r1, "bear",
        )
        raw = await self._call_agent(system, user_msg, "bear_rebuttal")
        return self._parse(raw, Rebuttal)

    async def _run_judge(
        self,
        primary_analysis: PrimaryAnalysisOutput,
        bull_r1: BullArgument,
        bear_r1: BearArgument,
        round2: Optional[DebateRound2],
    ) -> Optional[DebateVerdict]:
        system = judge_prompt.SYSTEM_PROMPT
        user_msg = judge_prompt.build_user_message(
            primary_analysis, bull_r1, bear_r1, round2,
        )
        try:
            raw = await self._call_agent(system, user_msg, "judge")
            return self._parse(raw, DebateVerdict)
        except Exception as exc:
            logger.error("Judge failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # API call + retry
    # ------------------------------------------------------------------

    async def _call_agent(
        self, system_prompt: str, user_message: str, agent_name: str,
    ) -> str:
        """Call Claude with retry logic.  Returns raw text.

        On persistent failure, raises so the caller can handle it.
        """
        loop = asyncio.get_running_loop()

        for attempt in range(1 + self.max_retries):
            try:
                raw = await loop.run_in_executor(
                    None, self._sync_call, system_prompt, user_message, agent_name,
                )
                return raw
            except AnthropicTimeoutError:
                if attempt < self.max_retries:
                    logger.warning("%s timeout — retry %d", agent_name, attempt + 1)
                    continue
                raise
            except AnthropicRateLimitError as exc:
                wait = getattr(exc, "retry_after", None) or 5
                if attempt < self.max_retries:
                    logger.warning("%s rate limited — wait %ss", agent_name, wait)
                    await asyncio.sleep(float(wait))
                    continue
                raise
            except AnthropicServerError:
                if attempt < self.max_retries:
                    logger.warning("%s 500 — retry after 5s", agent_name)
                    await asyncio.sleep(5)
                    continue
                raise

        raise RuntimeError(f"{agent_name}: exhausted retries")

    # max_tokens per agent role
    _MAX_TOKENS = {"bull": 1000, "bear": 1000, "judge": 800, "bull_rebuttal": 800, "bear_rebuttal": 800}

    def _sync_call(self, system_prompt: str, user_message: str, agent_name: str = "bull") -> str:
        max_tok = self._MAX_TOKENS.get(agent_name, 1000)

        # --- Subscription mode: route through LLMBackend ---
        if self.backend.mode == "subscription":
            llm_resp = self.backend.call(
                system_prompt=system_prompt,
                user_message=user_message,
                model=self.model,
                max_tokens=max_tok,
                temperature=0,
                timeout=self.timeout,
            )
            if not hasattr(self, "_total_usage"):
                self._total_usage = {"input_tokens": 0, "output_tokens": 0}
            self._total_usage["input_tokens"] += llm_resp.usage.input_tokens
            self._total_usage["output_tokens"] += llm_resp.usage.output_tokens
            return llm_resp.text

        # --- API mode: existing SDK behavior ---
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tok,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            timeout=self.timeout,
        )
        # Track token usage
        usage = resp.usage
        if not hasattr(self, "_total_usage"):
            self._total_usage = {"input_tokens": 0, "output_tokens": 0}
        self._total_usage["input_tokens"] += usage.input_tokens
        self._total_usage["output_tokens"] += usage.output_tokens
        return resp.content[0].text

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse(self, raw: str, model_cls):
        """Strip fences, parse JSON, validate with pydantic model."""
        cleaned = strip_json_fences(raw)
        data = json.loads(cleaned)
        # Inject metadata fields the AI doesn't produce
        if "timestamp_utc" not in data:
            data["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        if "model_used" not in data:
            data["model_used"] = self.model
        return model_cls.model_validate(data)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _write_verdict(self, verdict: DebateVerdict) -> None:
        write_pipeline("03b_verdict.json", verdict.model_dump(mode="json"))
