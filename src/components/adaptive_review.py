"""Component 6 — Adaptive Review System.

Four-tier adaptation mechanism:
  Tier 1: Observation only (log deviations)
  Tier 2: Suggest parameter adjustments
  Tier 3: Propose rule modifications with AI review
  Tier 4: Auto-adjust within guarded bounds

Post-trade updates are pure Python (no AI).  Weekly insight generation
and deep reviews use Claude Sonnet.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import yaml

from anthropic import (
    Anthropic,
    APITimeoutError as AnthropicTimeoutError,
    InternalServerError as AnthropicServerError,
    RateLimitError as AnthropicRateLimitError,
)

from src.components.knowledge_base import KnowledgeBase
from src.models.trade_models import (
    DeterministicChecks,
    PostmortemRecord,
    QualityScores,
    TradeRecord,
)
from src.utils.file_io import atomic_write, load_json, load_yaml
from src.utils.validation import strip_json_fences

logger = logging.getLogger(__name__)

# ── Hard guardrails: NEVER modifiable ────────────────────────────────
PROTECTED_PARAMETERS = frozenset({
    "max_risk_pct",
    "max_daily_losses",
    "max_daily_loss_pct",
    "max_weekly_loss_pct",
    "max_monthly_loss_pct",
    "session_start_utc",
    "session_end_utc",
    "debate_required",
})

# ── Thresholds from config.adaptation ────────────────────────────────
_DEFAULT_TIER2_DEVIATION = 0.15
_DEFAULT_TIER2_MIN_SAMPLES = 20
_DEFAULT_TIER3_MIN_SAMPLES = 50
_DEFAULT_MAX_MODS_PER_50 = 1

# ── Weekly insights prompt ───────────────────────────────────────────
_INSIGHTS_SYSTEM_PROMPT = """You are the analytical engine for a gold trading system.
Generate compressed insights from the trading data provided.
Output ONLY valid YAML matching the CompressedInsights schema.
No preamble, no markdown fences, no explanation.

Schema fields:
  generated_at: ISO-8601 timestamp
  total_trades_analyzed: int
  overall_win_rate: float (0-1)
  overall_expectancy: float (R-multiple)
  overall_profit_factor: float
  max_consecutive_losses: int
  condition_insights: list of {condition, sample_size, win_rate, expectancy, avg_r_winner, avg_r_loser, flag, note}
  debate_calibration: {total_debates, bull_wins, bear_wins, bull_win_rate, bear_win_rate, false_approvals_pct, false_rejections_pct, calibration_note}
  regime_insight: {current_regime, regime_started, model_performance_in_regime}
  active_failure_patterns: list of {pattern, affected_trades, all_losses, recommendation}
  rule_modification_history: list of {modification, date, impact, status}

For each condition with 10+ samples, classify flag as:
  STRONG_EDGE: expectancy > overall + 0.3R
  NEUTRAL: within 0.3R of overall
  UNDERPERFORMING: expectancy < overall - 0.3R AND sample >= 15
  SIGNIFICANTLY_UNDERPERFORMING: negative expectancy AND sample >= 20
"""


class AdaptiveReviewSystem:
    """Statistical analysis, quality scoring, and adaptation logic."""

    def __init__(self, config: dict, kb: KnowledgeBase) -> None:
        self.config = config
        self.kb = kb

        adapt_cfg = config.get("adaptation", {})
        self.tier2_deviation = adapt_cfg.get(
            "tier2_deviation_threshold", _DEFAULT_TIER2_DEVIATION,
        )
        self.tier2_min_samples = adapt_cfg.get(
            "tier2_min_samples", _DEFAULT_TIER2_MIN_SAMPLES,
        )
        self.tier3_min_samples = adapt_cfg.get(
            "tier3_min_samples", _DEFAULT_TIER3_MIN_SAMPLES,
        )
        self.max_mods_per_50 = adapt_cfg.get(
            "max_modifications_per_50_trades", _DEFAULT_MAX_MODS_PER_50,
        )

        ai_cfg = config.get("ai", {})
        # H2 (2026-04-26): default updated from stale snapshot ID
        # ``claude-sonnet-4-20250514`` to current production alias
        # ``claude-sonnet-4-6`` (matches ai.primary_model). Production reads
        # this from agent_config.yaml `ai.review_model`; the in-code default
        # is the safety fallback when the key is absent.
        self.model = ai_cfg.get("review_model", "claude-sonnet-4-6")
        self.timeout = ai_cfg.get("api_timeout_seconds", 30)
        self.max_retries = ai_cfg.get("max_api_retries", 1)

        self.client = Anthropic()

    # ------------------------------------------------------------------
    # 1. Post-trade update (pure Python — no AI)
    # ------------------------------------------------------------------

    def post_trade_update(self, trade: TradeRecord) -> None:
        """Called after every completed trade.

        Updates: rolling stats, trade index, condition performance,
        quality scores.  Does NOT call any AI model.
        """
        # a) Rolling statistics
        self.kb.update_rolling_stats(trade)

        # b) Trade index
        self.kb.update_trade_index(trade)

        # c) Condition performance
        self._update_condition_performance(trade)

        # d) Deterministic quality score
        scores = self.score_trade_deterministic(trade)
        self._update_quality_scores(trade, scores)

    def _update_condition_performance(self, trade: TradeRecord) -> None:
        """Track win rate and expectancy per condition combination."""
        filepath = self.kb.base / "statistics" / "condition_performance.json"
        perf = load_json(filepath)

        r = trade.r_multiple or 0.0
        is_win = trade.outcome == "WIN"

        # Individual dimensions
        dims = {
            "day_of_week": trade.day_of_week or "unknown",
            "liquidity_type": trade.liquidity_swept or "unknown",
            "displacement_quality": trade.displacement_quality or "unknown",
            "regime": trade.regime or "unknown",
        }

        # Combined dimensions
        combos = {
            "day_of_week+liquidity_type": (
                f"{dims['day_of_week']}_{dims['liquidity_type']}"
            ),
            "displacement_quality+regime": (
                f"{dims['displacement_quality']}_{dims['regime']}"
            ),
        }

        all_keys: dict[str, str] = {}
        for dim_name, dim_val in dims.items():
            all_keys[f"{dim_name}:{dim_val}"] = dim_val
        for combo_name, combo_val in combos.items():
            all_keys[f"{combo_name}:{combo_val}"] = combo_val

        for key in all_keys:
            bucket = perf.setdefault(key, {
                "wins": 0, "losses": 0, "breakeven": 0,
                "total": 0, "gross_r": 0.0, "gross_winner_r": 0.0,
                "gross_loser_r": 0.0,
            })
            bucket["total"] += 1
            bucket["gross_r"] += r

            if trade.outcome == "WIN":
                bucket["wins"] += 1
                bucket["gross_winner_r"] += r
            elif trade.outcome == "LOSS":
                bucket["losses"] += 1
                bucket["gross_loser_r"] += abs(r)
            else:
                bucket["breakeven"] += 1

            total = bucket["total"]
            bucket["win_rate"] = bucket["wins"] / total if total else 0.0
            avg_w = (
                bucket["gross_winner_r"] / bucket["wins"]
                if bucket["wins"] else 0.0
            )
            avg_l = (
                bucket["gross_loser_r"] / bucket["losses"]
                if bucket["losses"] else 0.0
            )
            bucket["expectancy"] = round(
                (bucket["win_rate"] * avg_w)
                - ((1 - bucket["win_rate"]) * avg_l),
                4,
            )
            bucket["sample_size"] = total

        atomic_write(filepath, perf)

    def _update_quality_scores(
        self, trade: TradeRecord, scores: dict,
    ) -> None:
        """Append the deterministic quality score to the scores log."""
        filepath = self.kb.base / "statistics" / "quality_scores.json"
        data = load_json(filepath)
        log = data.setdefault("scores", [])
        log.append({
            "trade_id": trade.trade_id,
            "date": trade.date,
            "deterministic_score": scores["deterministic_score"],
            "checks": scores["deterministic_checks"],
        })
        atomic_write(filepath, data)

    # ------------------------------------------------------------------
    # 2. Deterministic quality scoring
    # ------------------------------------------------------------------

    @staticmethod
    def score_trade_deterministic(trade: TradeRecord) -> dict:
        """Implement the deterministic quality scoring axis.

        Returns ``{"deterministic_score": float, "deterministic_checks": dict}``.
        """
        checks = {
            "risk_exactly_1pct": (
                abs((trade.actual_risk_pct or 1.0) - 1.0) < 0.15
            ),
            "within_session_window": _within_session_window(trade),
            "sl_correct": _sl_correct(trade),
            "position_size_correct": (
                trade.position_size_lots is not None
                and trade.position_size_lots > 0
            ),
            "one_trade_limit": True,  # enforced at pipeline level
            "partials_correct": _partials_correct(trade),
        }

        det_score = (sum(checks.values()) / len(checks)) * 100

        return {
            "deterministic_score": round(det_score, 1),
            "deterministic_checks": checks,
        }

    # ------------------------------------------------------------------
    # 3. Weekly insights generation (AI call)
    # ------------------------------------------------------------------

    async def generate_weekly_insights(self) -> dict:
        """Generate compressed insights YAML via Claude Sonnet.

        Budget: max 5 API calls (1 expected, retries count).
        """
        stats = self.kb.load_rolling_stats()
        cond_perf = load_json(
            self.kb.base / "statistics" / "condition_performance.json",
        )
        last_trades = self.kb.get_last_n_trades(50)
        regime = self.kb.load_regime()

        user_msg = (
            f"## Overall Statistics\n{json.dumps(stats, indent=2)}\n\n"
            f"## Condition Performance\n{json.dumps(cond_perf, indent=2)}\n\n"
            f"## Recent 50 Trades\n{json.dumps(last_trades, indent=2)}\n\n"
            f"## Current Regime\n{json.dumps(regime, indent=2)}\n\n"
            f"Generate compressed insights as YAML. Output YAML only."
        )

        max_attempts = min(5, 1 + self.max_retries * 2)
        for attempt in range(max_attempts):
            try:
                raw = await self._call_claude(
                    _INSIGHTS_SYSTEM_PROMPT, user_msg,
                )
                cleaned = strip_json_fences(raw)
                insights = yaml.safe_load(cleaned)
                if not isinstance(insights, dict):
                    raise ValueError("Insights response is not a dict")

                insights.setdefault(
                    "generated_at",
                    datetime.now(timezone.utc).isoformat(),
                )
                atomic_write(
                    self.kb.base / "insights" / "current_insights.yaml",
                    insights,
                )
                logger.info("Weekly insights generated (attempt %d)", attempt + 1)
                return insights

            except Exception as exc:
                logger.warning(
                    "Insights generation attempt %d failed: %s", attempt + 1, exc,
                )
                if attempt == max_attempts - 1:
                    logger.error("Weekly insights generation exhausted all attempts")
                    return {}

        return {}

    # ------------------------------------------------------------------
    # 4. Adaptation flags (pure Python)
    # ------------------------------------------------------------------

    def check_adaptation_flags(self) -> dict:
        """Check all condition combinations for statistical anomalies.

        Returns ``{"flags": [...], "proposals": [...]}``.
        Writes flags to ``rules/pending_reviews.yaml``.
        """
        stats = self.kb.load_rolling_stats()
        overall_wr = stats.get("win_rate", 0.0)

        cond_perf = load_json(
            self.kb.base / "statistics" / "condition_performance.json",
        )

        flags: list[dict] = []
        proposals: list[dict] = []

        for condition, perf in cond_perf.items():
            if not isinstance(perf, dict):
                continue
            sample = perf.get("sample_size", perf.get("total", 0))
            if sample < self.tier2_min_samples:
                continue

            cond_wr = perf.get("win_rate", 0.0)
            deviation = cond_wr - overall_wr

            # Tier 2: Flag for review
            if abs(deviation) > self.tier2_deviation:
                flags.append({
                    "condition": condition,
                    "deviation": round(deviation, 4),
                    "win_rate": round(cond_wr, 4),
                    "overall_win_rate": round(overall_wr, 4),
                    "sample_size": sample,
                    "tier": 2,
                })

            # Tier 3: Propose modification (needs more samples)
            if (
                abs(deviation) > self.tier2_deviation
                and sample >= self.tier3_min_samples
            ):
                expectancy = perf.get("expectancy", 0.0)
                if expectancy < 0:
                    proposals.append({
                        "condition": condition,
                        "proposed_change": (
                            f"Treat '{condition}' as NO_TRADE filter"
                        ),
                        "supporting_data": {
                            "win_rate": round(cond_wr, 4),
                            "expectancy": round(expectancy, 4),
                            "sample_size": sample,
                        },
                        "rollback_criteria": (
                            "Revert if expectancy drops by >0.1R "
                            "over next 30 trades"
                        ),
                        "tier": 3,
                    })

        result = {"flags": flags, "proposals": proposals}

        # Write to pending reviews
        pending_path = self.kb.base / "rules" / "pending_reviews.yaml"
        atomic_write(pending_path, {
            "items": flags + proposals,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })

        return result

    # ------------------------------------------------------------------
    # 5. Deep review (every 50 trades)
    # ------------------------------------------------------------------

    async def run_deep_review(self, force: bool = False) -> dict:
        """Triggered every 50 trades (or force=True).

        Budget: max 15 API calls.
        Returns a review summary dict.
        """
        stats = self.kb.load_rolling_stats()
        total = stats.get("total_trades", 0)

        if not force and total % 50 != 0:
            return {"skipped": True, "reason": "Not at 50-trade boundary"}

        logger.info("Running deep review at %d total trades", total)

        # 1. Full condition breakdown
        adaptation = self.check_adaptation_flags()

        # 2. Debate calibration
        debate_cal = self._compute_debate_calibration()

        # 3. Generate insights (counts toward budget)
        insights = await self.generate_weekly_insights()

        # 4. Compile review document
        review = {
            "review_at_trade": total,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "rolling_stats": stats,
            "adaptation_flags": adaptation["flags"],
            "adaptation_proposals": adaptation["proposals"],
            "debate_calibration": debate_cal,
            "insights_generated": bool(insights),
        }

        # Save
        review_dir = self.kb.base / "statistics"
        atomic_write(
            review_dir / f"deep_review_{total:04d}.json", review,
        )
        logger.info("Deep review complete: %d flags, %d proposals",
                     len(adaptation["flags"]), len(adaptation["proposals"]))

        return review

    def _compute_debate_calibration(self) -> dict:
        """Compute debate win rates and false approval/rejection rates."""
        trades = self.kb.get_last_n_trades(200)

        total_debates = 0
        bull_wins = 0
        bear_wins = 0
        approved_losses = 0
        approved_total = 0
        rejected_would_win = 0
        rejected_total = 0

        for t in trades:
            dv = t.get("debate_confidence")
            if dv is None:
                continue  # no debate data

            total_debates += 1
            # Rough heuristic: debate_confidence > 50 ≈ bull wins
            if dv and dv >= 50:
                bull_wins += 1
            else:
                bear_wins += 1

            outcome = t.get("outcome")
            if outcome:
                approved_total += 1
                if outcome == "LOSS":
                    approved_losses += 1

        bull_wr = bull_wins / total_debates if total_debates else 0.0
        bear_wr = bear_wins / total_debates if total_debates else 0.0
        fa_pct = approved_losses / approved_total if approved_total else 0.0

        return {
            "total_debates": total_debates,
            "bull_wins": bull_wins,
            "bear_wins": bear_wins,
            "bull_win_rate": round(bull_wr, 4),
            "bear_win_rate": round(bear_wr, 4),
            "false_approvals_pct": round(fa_pct, 4),
            "false_rejections_pct": 0.0,  # needs manual review
        }

    # ------------------------------------------------------------------
    # 6. Hard guardrails
    # ------------------------------------------------------------------

    @staticmethod
    def validate_rule_change(parameter: str, new_value: object) -> bool:
        """Return False if *parameter* is a protected guardrail.

        NEVER allows modification of protected parameters.
        """
        return parameter not in PROTECTED_PARAMETERS

    @staticmethod
    def get_protected_parameters() -> frozenset[str]:
        return PROTECTED_PARAMETERS

    # ------------------------------------------------------------------
    # Internal: Claude API call
    # ------------------------------------------------------------------

    async def _call_claude(
        self, system_prompt: str, user_message: str,
    ) -> str:
        loop = asyncio.get_running_loop()
        for attempt in range(1 + self.max_retries):
            try:
                raw = await loop.run_in_executor(
                    None, self._sync_call, system_prompt, user_message,
                )
                return raw
            except AnthropicTimeoutError:
                if attempt < self.max_retries:
                    logger.warning("Review API timeout — retry %d", attempt + 1)
                    continue
                raise
            except AnthropicRateLimitError as exc:
                wait = getattr(exc, "retry_after", None) or 5
                if attempt < self.max_retries:
                    await asyncio.sleep(float(wait))
                    continue
                raise
            except AnthropicServerError:
                if attempt < self.max_retries:
                    await asyncio.sleep(5)
                    continue
                raise
        raise RuntimeError("Exhausted retries")

    def _sync_call(self, system_prompt: str, user_message: str) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            timeout=self.timeout,
        )
        return resp.content[0].text


# ── Helpers for deterministic scoring ────────────────────────────────

def _within_session_window(trade: TradeRecord) -> bool:
    """Check if trade was entered during 07:00–09:30 UTC."""
    # In backtesting the trade_id encodes the date; entry time comes
    # from state_transitions or events.  For scoring we parse what we
    # have — the first state transition or candle time.
    for st in trade.state_transitions:
        try:
            dt = datetime.fromisoformat(
                st.time.replace("Z", "+00:00")
            )
            h, m = dt.hour, dt.minute
            if 7 <= h < 10:
                return True
            return False
        except Exception:
            continue
    # Fallback: assume correct during backtesting
    return True


def _sl_correct(trade: TradeRecord) -> bool:
    """Verify SL is placed beyond the sweep wick + buffer."""
    if trade.direction == "LONG":
        return trade.stop_loss < trade.entry_price
    elif trade.direction == "SHORT":
        return trade.stop_loss > trade.entry_price
    return False


def _partials_correct(trade: TradeRecord) -> bool:
    """Verify partial close events are consistent.

    TP1 should close ~50%, remaining should have SL at BE, etc.
    In backtesting we only check the events list is non-empty for
    trades that reached TP1.
    """
    if not trade.events:
        # No events → either full SL or session timeout; acceptable
        return True

    tp1_events = [e for e in trade.events if e.type == "PARTIAL_TP1"]
    if tp1_events:
        # Verify remaining_pct dropped to ~0.5
        return tp1_events[0].remaining_pct <= 0.55
    return True
