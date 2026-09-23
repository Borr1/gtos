"""Backtesting harness — loops over historical sessions, feeds MSOs, logs outcomes.

Usage:
    # Full run with debate (Round 1 only)
    python scripts/backtest_runner.py --start 2025-10-01 --end 2025-12-31 --debate --no-round2

    # Primary Analyzer only (no debate)
    python scripts/backtest_runner.py --start 2025-10-01 --end 2025-12-31 --no-debate

    # Dry-run (mock API responses, test pipeline flow)
    python scripts/backtest_runner.py --start 2025-10-01 --end 2025-10-10 --dry-run

    # Generate report from existing batch data
    python scripts/backtest_runner.py --report

    # Resume a crashed batch (skips already-processed dates)
    python scripts/backtest_runner.py --start 2025-10-01 --end 2025-12-31 --debate --resume
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time as time_mod
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Ensure the project root is importable
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
_LEGACY_LOG_DIR = (
    _PROJECT_ROOT
    / "research"
    / "archive"
    / "root_legacy_artifacts_2026_05_31"
    / "generated"
    / "logs"
)
_LEGACY_LOG_DIR.mkdir(parents=True, exist_ok=True)

from dotenv import load_dotenv

load_dotenv(_PROJECT_ROOT / ".env", override=True)

import yaml

from scripts.historical_data_loader import (
    SESSIONS_DIR,
    replay_london_open,
    parse_tradingview_csv,
)
from src.components.debate import DebateEngine
from src.components.knowledge_base import KnowledgeBase
from src.components.market_state import compute_market_state
from src.components.primary_analyzer import PrimaryAnalyzer
from src.llm_backend import LLMBackend
from src.models.analysis_models import PrimaryAnalysisOutput, TradeParameters
from src.models.debate_models import DebateVerdict
from src.models.trade_models import (
    CandleEvaluation,
    NoTradeRecord,
    NoTradeReasoning,
    PreSession,
    SessionManifest,
    TradeEvent,
    TradeRecord,
    TradeSummary,
)
from src.utils.file_io import atomic_write, load_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_LEGACY_LOG_DIR / "backtest.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BACKTEST_KB_DIR = _PROJECT_ROOT / "knowledge_base_backtest"
BATCH_RESULTS_DIR = BACKTEST_KB_DIR / "batch_results"
DATA_DIR = _PROJECT_ROOT / "data"
HISTORICAL_DIR = DATA_DIR / "historical"

# Sonnet pricing: $3/M input, $15/M output, cache read $0.3/M, cache write $3.75/M
_COST_PER_INPUT_TOKEN = 3.0 / 1_000_000
_COST_PER_OUTPUT_TOKEN = 15.0 / 1_000_000
_COST_PER_CACHE_READ = 0.3 / 1_000_000
_COST_PER_CACHE_WRITE = 3.75 / 1_000_000


# ═══════════════════════════════════════════════════════════════════════
# Dry-run mock responses
# ═══════════════════════════════════════════════════════════════════════

_DRY_RUN_NO_TRADE = json.dumps({
    "timestamp_utc": "2026-01-01T07:15:00Z",
    "model_used": "dry-run",
    "decision": "NO_TRADE",
    "confidence_score": 0,
    "framework": "none",
    "kill_zone": "london",
    "frameworks_evaluated": {
        "session_sweep": {"qualified": False, "reason": "dry_run_mode"},
        "ob_retest": {"qualified": False, "reason": "dry_run_mode"},
    },
    "reasoning": {
        "daily_bias": {"direction": "ranging", "confidence": "low",
                       "protected_swing_level": 0.0, "explanation": "Dry-run"},
        "h4_alignment": {"aligned": False, "explanation": "Dry-run"},
        "h1_setup": {"poi_identified": False, "explanation": "Dry-run"},
        "liquidity_sweep": {"detected": False, "explanation": "Dry-run"},
        "m15_confirmation": {"choch_detected": False, "explanation": "Dry-run"},
        "setup_grade": "C",
        "overall_reasoning": "Dry-run mode — no API call made.",
    },
    "trade_parameters": None,
    "no_trade_reason": "dry_run_mode",
    "wait_reason": None,
})


# ═══════════════════════════════════════════════════════════════════════
# Hypothetical outcome evaluation
# ═══════════════════════════════════════════════════════════════════════

def evaluate_hypothetical_outcome(
    trade_params: TradeParameters,
    future_candles: list[dict],
) -> dict:
    """Walk through future candles and simulate trade outcome.

    Simulates the partial-close logic from Section 2.5:
      - TP1 hit → close 50%, move SL to breakeven
      - TP2 hit → close 25%, trail SL
      - TP3 hit → close runner (remaining 25%)
      - SL/BE hit → close remaining position

    Returns:
        {
            "outcome": "WIN" | "LOSS" | "BREAKEVEN",
            "exit_substate": str,
            "r_multiple": float,
            "hold_time_candles": int,
            "events": list[dict],
        }
    """
    entry = trade_params.entry_price
    sl = trade_params.stop_loss
    tp1 = trade_params.take_profit_1
    tp2 = trade_params.take_profit_2 or 0.0
    tp3 = trade_params.take_profit_3 or 0.0
    direction = trade_params.direction

    risk = abs(entry - sl)
    if risk < 1e-6:
        return {
            "outcome": "LOSS", "exit_substate": "CLOSED_SL",
            "r_multiple": -1.0, "hold_time_candles": 0, "events": [],
            "mfe_r": 0.0, "mae_r": 0.0, "r_path": [],
        }

    is_long = direction == "LONG"

    # State tracking
    remaining_pct = 1.0
    current_sl = sl
    tp1_hit = False
    tp2_hit = False
    total_r = 0.0
    events: list[dict] = []
    max_favorable_r = 0.0
    max_adverse_r = 0.0
    r_path: list[dict] = []  # Enhanced: candle-by-candle R-path

    for i, candle in enumerate(future_candles):
        c_high = candle["high"]
        c_low = candle["low"]
        c_time = candle.get("time", "")

        # Track MFE/MAE before exit checks
        if is_long:
            fav = (c_high - entry) / risk if risk > 0 else 0
            adv = (entry - c_low) / risk if risk > 0 else 0
        else:
            fav = (entry - c_low) / risk if risk > 0 else 0
            adv = (c_high - entry) / risk if risk > 0 else 0
        max_favorable_r = max(max_favorable_r, fav)
        max_adverse_r = max(max_adverse_r, adv)

        # Enhanced: log R at every candle
        if is_long:
            r_close = (candle.get("close", entry) - entry) / risk
            r_high = (c_high - entry) / risk
            r_low = (c_low - entry) / risk
        else:
            r_close = (entry - candle.get("close", entry)) / risk
            r_high = (entry - c_low) / risk
            r_low = (entry - c_high) / risk
        r_path.append({
            "candle_index": i,
            "time": c_time,
            "r_at_close": round(r_close, 4),
            "r_at_high": round(r_high, 4),
            "r_at_low": round(r_low, 4),
        })

        # Check SL first (worst case — hit before TP in same candle)
        sl_hit = (c_low <= current_sl) if is_long else (c_high >= current_sl)
        if sl_hit:
            if tp1_hit and abs(current_sl - entry) < 1e-6:
                # SL was moved to breakeven
                total_r += 0.0 * remaining_pct  # BE on remaining
                events.append({
                    "type": "BE_HIT", "time": c_time,
                    "price": current_sl, "remaining_pct": 0.0,
                })
                exit_sub = "CLOSED_BE"
            elif tp1_hit:
                # Trailing stop
                pnl_per_unit = (current_sl - entry) if is_long else (entry - current_sl)
                total_r += (pnl_per_unit / risk) * remaining_pct
                events.append({
                    "type": "TRAIL_HIT", "time": c_time,
                    "price": current_sl, "remaining_pct": 0.0,
                })
                exit_sub = "CLOSED_TRAIL"
            else:
                # Full stop loss
                total_r = -1.0
                events.append({
                    "type": "SL_HIT", "time": c_time,
                    "price": current_sl, "remaining_pct": 0.0,
                })
                exit_sub = "CLOSED_SL"

            outcome = "WIN" if total_r > 0.05 else ("BREAKEVEN" if total_r > -0.05 else "LOSS")
            return {
                "outcome": outcome, "exit_substate": exit_sub,
                "r_multiple": round(total_r, 2),
                "hold_time_candles": i + 1, "events": events,
                "mfe_r": round(max_favorable_r, 3),
                "mae_r": round(max_adverse_r, 3),
                "r_path": r_path,
            }

        # Check TP1
        if not tp1_hit and tp1 > 0:
            tp1_reached = (c_high >= tp1) if is_long else (c_low <= tp1)
            if tp1_reached:
                tp1_hit = True
                tp1_r = abs(tp1 - entry) / risk
                close_pct = 0.50
                total_r += tp1_r * close_pct
                remaining_pct -= close_pct
                current_sl = entry  # SL to breakeven
                events.append({
                    "type": "PARTIAL_TP1", "time": c_time,
                    "price": tp1, "remaining_pct": remaining_pct,
                })

        # Check TP2
        if tp1_hit and not tp2_hit and tp2 > 0:
            tp2_reached = (c_high >= tp2) if is_long else (c_low <= tp2)
            if tp2_reached:
                tp2_hit = True
                tp2_r = abs(tp2 - entry) / risk
                close_pct = 0.25
                total_r += tp2_r * close_pct
                remaining_pct -= close_pct
                # Trail SL to TP1 level
                current_sl = tp1 if is_long else tp1
                events.append({
                    "type": "PARTIAL_TP2", "time": c_time,
                    "price": tp2, "remaining_pct": remaining_pct,
                })

        # Check TP3 (runner)
        if tp2_hit and tp3 > 0:
            tp3_reached = (c_high >= tp3) if is_long else (c_low <= tp3)
            if tp3_reached:
                tp3_r = abs(tp3 - entry) / risk
                total_r += tp3_r * remaining_pct
                remaining_pct = 0.0
                events.append({
                    "type": "RUNNER_TP3", "time": c_time,
                    "price": tp3, "remaining_pct": 0.0,
                })
                return {
                    "outcome": "WIN", "exit_substate": "CLOSED_TP3_RUNNER",
                    "r_multiple": round(total_r, 2),
                    "hold_time_candles": i + 1, "events": events,
                    "mfe_r": round(max_favorable_r, 3),
                    "mae_r": round(max_adverse_r, 3),
                    "r_path": r_path,
                }

    # Session timeout — close at last candle's close
    last_close = future_candles[-1]["close"] if future_candles else entry
    pnl_per_unit = (last_close - entry) if is_long else (entry - last_close)
    total_r += (pnl_per_unit / risk) * remaining_pct
    events.append({
        "type": "SESSION_TIMEOUT", "time": future_candles[-1].get("time", "") if future_candles else "",
        "price": last_close, "remaining_pct": 0.0,
    })
    outcome = "WIN" if total_r > 0.05 else ("BREAKEVEN" if total_r > -0.05 else "LOSS")
    # Distinguish partial-TP-then-timeout from pure timeout
    if tp1_hit:
        exit_sub = "CLOSED_TP1_THEN_TIMEOUT"
    else:
        exit_sub = "CLOSED_SESSION_TIMEOUT"
    return {
        "outcome": outcome, "exit_substate": exit_sub,
        "r_multiple": round(total_r, 2),
        "hold_time_candles": len(future_candles), "events": events,
        "mfe_r": round(max_favorable_r, 3),
        "mae_r": round(max_adverse_r, 3),
        "r_path": r_path,
    }


# ═══════════════════════════════════════════════════════════════════════
# BacktestRunner
# ═══════════════════════════════════════════════════════════════════════

class BacktestRunner:
    """Orchestrates the full backtesting pipeline."""

    def __init__(
        self,
        config_path: str = "config/agent_config.yaml",
        debate_enabled: bool = True,
        round2_enabled: bool = False,
        dry_run: bool = False,
        delay: float = 1.0,
        budget_limit: float = 5.0,
        billing_mode: str = "api",
    ) -> None:
        with open(_PROJECT_ROOT / config_path) as fh:
            self.config = yaml.safe_load(fh)

        # Override debate settings from CLI
        self.debate_enabled = debate_enabled
        self.config["ai"]["debate_round2_enabled"] = round2_enabled
        self.dry_run = dry_run
        self.delay = delay
        self.billing_mode = billing_mode

        # Create shared LLM backend (api or subscription)
        self.llm_backend = LLMBackend(mode=billing_mode)

        # Point KB at backtest-specific directory
        import src.utils.file_io as fio
        self.kb_dir = BACKTEST_KB_DIR
        fio.KNOWLEDGE_BASE_DIR = self.kb_dir

        self.kb = KnowledgeBase(base_path=str(self.kb_dir))
        self.kb.initialize_rules()

        self.analyzer = PrimaryAnalyzer(self.config, self.kb, llm_backend=self.llm_backend)
        self.debate_engine = DebateEngine(self.config, self.kb, llm_backend=self.llm_backend)

        # Load all historical candle data
        self.all_candles = self._load_historical_candles()

        # Budget and cost tracking
        self.budget_limit = budget_limit
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_usd = 0.0
        self._total_retries = 0

        # Batch state
        self._batch_results: list[dict] = []

    def _load_historical_candles(self) -> dict[str, list[dict]]:
        """Load candle CSVs from data/historical/."""
        symbol = self.config.get("market", {}).get("symbol", "XAUUSD")
        all_candles: dict[str, list[dict]] = {}
        for tf in ("D1", "H4", "H1", "M15"):
            csv_path = HISTORICAL_DIR / f"{symbol}_{tf}.csv"
            if csv_path.exists():
                all_candles[tf] = parse_tradingview_csv(csv_path)
            else:
                logger.warning("No historical CSV for %s at %s", tf, csv_path)
                all_candles[tf] = []
        return all_candles

    # ------------------------------------------------------------------
    # Session runner
    # ------------------------------------------------------------------

    async def run_session(self, date_str: str) -> SessionManifest:
        """Run the full pipeline for one trading day."""
        target_date = date.fromisoformat(date_str)
        day_name = target_date.strftime("%A")

        manifest = SessionManifest(
            date=date_str,
            day_of_week=day_name,
            session_start_utc=f"{date_str}T07:00:00Z",
            session_end_utc=f"{date_str}T09:30:00Z",
        )

        # Reset session-level caches
        self.analyzer.reset_session_cache()

        api_calls = 0
        session_input_tokens = 0
        session_output_tokens = 0
        session_cache_read = 0
        session_cache_create = 0
        session_retries = 0
        trade_taken = False
        kb_context: Optional[dict] = None  # loaded once per session
        best_candidate: Optional[dict] = None  # track best CANDIDATE for outcome eval

        candle_gen = replay_london_open(date_str, self.all_candles)

        for raw_data in candle_gen:
            candle_time = raw_data["timestamp_utc"]

            # If a trade was already taken this session, skip remaining candles
            if trade_taken:
                manifest.candle_evaluations.append(CandleEvaluation(
                    candle_time=candle_time,
                    decision="SKIP",
                    reason="trade_already_taken",
                ))
                continue

            try:
                # ── Component 2: Market State ─────────────────────────
                mso = compute_market_state(raw_data, self.config)

                # ── KB Context (cached per session — loaded once) ─────
                if kb_context is None:
                    try:
                        kb_context = self.kb.assemble_full_context(mso)
                    except Exception:
                        kb_context = {"layer1": {}, "layer2": {}, "layer3": []}

                # ── Component 3A: Primary Analyzer ────────────────────
                if self.dry_run:
                    pa = self._dry_run_primary(candle_time)
                else:
                    pa = await self.analyzer.analyze(mso)
                    api_calls += 1
                    # Collect token usage from PA
                    pa_usage = getattr(self.analyzer, "_last_usage", {})
                    session_input_tokens += pa_usage.get("input_tokens", 0)
                    session_output_tokens += pa_usage.get("output_tokens", 0)
                    session_cache_read += pa_usage.get("cache_read_tokens", 0)
                    session_cache_create += pa_usage.get("cache_create_tokens", 0)
                    if pa.no_trade_reason == "ai_output_malformed":
                        session_retries += 1
                    if self.delay > 0:
                        await asyncio.sleep(self.delay)

                eval_entry = CandleEvaluation(
                    candle_time=candle_time,
                    decision=pa.decision,
                    reason=pa.no_trade_reason or pa.wait_reason,
                    confidence=pa.confidence_score,
                    setup_grade=pa.reasoning.setup_grade if pa.reasoning else None,
                )

                # ── Component 3B: Debate (if CANDIDATE) ───────────────
                if pa.decision == "CANDIDATE":
                    eval_entry.debate_triggered = True

                    if self.debate_enabled and not self.dry_run:
                        # Reset debate usage tracker
                        self.debate_engine._total_usage = {"input_tokens": 0, "output_tokens": 0}
                        verdict = await self.debate_engine.run_debate(
                            mso, pa, kb_context,
                        )
                        # Bull R1 + Bear R1 = 2 calls. Judge = 1. R2 = 2 if enabled.
                        api_calls += 3
                        if self.config["ai"].get("debate_round2_enabled"):
                            api_calls += 2
                        # Collect debate token usage
                        deb_usage = getattr(self.debate_engine, "_total_usage", {})
                        session_input_tokens += deb_usage.get("input_tokens", 0)
                        session_output_tokens += deb_usage.get("output_tokens", 0)
                        if self.delay > 0:
                            await asyncio.sleep(self.delay)

                        eval_entry.debate_verdict = verdict.verdict
                        decision_str = DebateEngine.evaluate_verdict(verdict)

                        if decision_str in ("APPROVED", "APPROVED_MARGINAL"):
                            trade_taken = True
                            best_candidate = {
                                "candle_time": candle_time,
                                "primary_analysis": pa,
                                "verdict": verdict,
                                "decision_str": decision_str,
                            }
                            eval_entry.trade_executed = True
                    elif not self.debate_enabled:
                        # No debate — run deterministic safety checks
                        eval_entry.debate_triggered = False
                        reject_reason = self._safety_check(pa, mso)
                        if reject_reason:
                            eval_entry.debate_verdict = "SAFETY_REJECT"
                            eval_entry.reason = reject_reason
                            logger.info("Safety check rejected: %s", reject_reason)
                        else:
                            eval_entry.debate_verdict = "AUTO_APPROVED"
                            trade_taken = True
                            best_candidate = {
                                "candle_time": candle_time,
                                "primary_analysis": pa,
                                "verdict": None,
                                "decision_str": "APPROVED",
                            }
                            eval_entry.trade_executed = True
                    else:
                        # dry_run with debate
                        eval_entry.debate_verdict = "DRY_RUN_SKIP"

                manifest.candle_evaluations.append(eval_entry)

            except Exception as exc:
                logger.error("Error processing candle %s: %s", candle_time, exc)
                manifest.errors.append(f"{candle_time}: {exc}")
                manifest.candle_evaluations.append(CandleEvaluation(
                    candle_time=candle_time,
                    decision="ERROR",
                    reason=str(exc),
                ))

        # ── Post-session: evaluate hypothetical outcome ───────────────
        # Cache-aware cost: cached reads are 90% cheaper, cache writes 25% more
        # input_tokens from API = non-cached input; cache_read/create are separate
        # In subscription mode, tokens are 0 — cost is covered by Max plan.
        if self.billing_mode == "subscription":
            session_cost = 0.0
        else:
            session_cost = (
                session_input_tokens * _COST_PER_INPUT_TOKEN
                + session_output_tokens * _COST_PER_OUTPUT_TOKEN
                + session_cache_read * _COST_PER_CACHE_READ
                + session_cache_create * _COST_PER_CACHE_WRITE
            )
        manifest.api_calls_count = api_calls
        manifest.api_cost_estimate_usd = round(session_cost, 4)

        # Update running totals
        self._total_input_tokens += session_input_tokens
        self._total_output_tokens += session_output_tokens
        self._total_cost_usd += session_cost
        self._total_retries += session_retries

        if best_candidate and best_candidate["primary_analysis"].trade_parameters:
            pa = best_candidate["primary_analysis"]
            tp = pa.trade_parameters

            # Get future candles (rest of the day after entry)
            future = self._get_future_candles(
                date_str, best_candidate["candle_time"],
            )

            outcome_data = evaluate_hypothetical_outcome(tp, future)

            # Build trade record
            trade_record = TradeRecord(
                trade_id=f"bt_{date_str}_001",
                date=date_str,
                day_of_week=day_name,
                lifecycle_state="CLOSED",
                exit_substate=outcome_data["exit_substate"],
                direction=tp.direction,
                entry_price=tp.entry_price,
                stop_loss=tp.stop_loss,
                take_profit_1=tp.take_profit_1,
                take_profit_2=tp.take_profit_2,
                take_profit_3=tp.take_profit_3,
                risk_reward_ratio=tp.risk_reward_ratio,
                setup_grade=pa.reasoning.setup_grade,
                daily_bias=pa.reasoning.daily_bias.direction,
                h4_aligned=pa.reasoning.h4_alignment.aligned,
                liquidity_swept=pa.reasoning.liquidity_sweep.pool_type,
                displacement_quality=pa.reasoning.m15_confirmation.displacement_quality,
                outcome=outcome_data["outcome"],
                r_multiple=outcome_data["r_multiple"],
                hold_time_minutes=outcome_data["hold_time_candles"] * 15,
            )
            if best_candidate.get("verdict"):
                v = best_candidate["verdict"]
                trade_record.debate_verdict = v.verdict
                trade_record.debate_confidence = v.confidence_score
                trade_record.bull_strength = v.bull_argument_strength
                trade_record.bear_strength = v.bear_argument_strength
                trade_record.debate_key_factor = v.key_factor
                trade_record.debate_round2_enabled = self.config["ai"].get(
                    "debate_round2_enabled", False,
                )

            # Write trade record to KB
            try:
                self.kb.write_trade(trade_record)
                self.kb.update_rolling_stats(trade_record)
            except Exception as exc:
                logger.warning("Failed to write trade record: %s", exc)

            manifest.trade_summary = TradeSummary(
                trade_taken=True,
                trade_id=trade_record.trade_id,
                outcome=outcome_data["outcome"],
                r_multiple=outcome_data["r_multiple"],
            )

            # Find the evaluation entry that triggered the trade and tag it
            for ev in manifest.candle_evaluations:
                if ev.candle_time == best_candidate["candle_time"]:
                    ev.trade_id = trade_record.trade_id
                    break
        else:
            # No trade taken — write no-trade record
            primary_reasons = [
                e.reason for e in manifest.candle_evaluations
                if e.reason and e.decision == "NO_TRADE"
            ]
            dominant_reason = primary_reasons[0] if primary_reasons else "no_candidate"

            nt_record = NoTradeRecord(
                record_id=f"nt_{date_str}_0700",
                date=date_str,
                candle_time=f"{date_str}T07:00:00Z",
                reason=dominant_reason,
                reasoning=NoTradeReasoning(
                    full_explanation=f"Session produced 0 candidates. "
                    f"Primary reasons: {', '.join(set(primary_reasons[:3]))}",
                ),
            )
            try:
                self.kb.write_no_trade(nt_record)
            except Exception as exc:
                logger.warning("Failed to write no-trade record: %s", exc)

        # Write session manifest
        try:
            self.kb.write_session_manifest(manifest)
        except Exception as exc:
            logger.warning("Failed to write session manifest: %s", exc)

        return manifest

    def _dry_run_primary(self, candle_time: str) -> PrimaryAnalysisOutput:
        """Return a mock NO_TRADE response for dry-run mode."""
        data = json.loads(_DRY_RUN_NO_TRADE)
        data["timestamp_utc"] = candle_time
        return PrimaryAnalysisOutput.model_validate(data)

    def _safety_check(self, pa: PrimaryAnalysisOutput, mso) -> Optional[str]:
        """Deterministic safety checks for candidates (no debate needed).

        Returns None if all checks pass, or a rejection reason string.
        """
        # Grade filter — only A and A+ pass
        grade = pa.reasoning.setup_grade if pa.reasoning else "C"
        if grade not in ("A+", "A"):
            return f"below_grade_threshold: {grade}"

        # Must have trade parameters
        tp = pa.trade_parameters
        if not tp:
            return "no_trade_parameters"

        # Direction must match daily bias
        daily_dir = pa.reasoning.daily_bias.direction if pa.reasoning else "ranging"
        if daily_dir == "bullish" and tp.direction == "SHORT":
            return "direction_mismatch: SHORT against bullish daily bias"
        if daily_dir == "bearish" and tp.direction == "LONG":
            return "direction_mismatch: LONG against bearish daily bias"

        # RR check — read threshold from config (default 1.5)
        min_rr = self.config.get("risk", {}).get("min_rr", 1.5)
        if tp.risk_reward_ratio < (min_rr - 0.1):
            return f"rr_too_low: {tp.risk_reward_ratio:.1f} < {min_rr - 0.1:.1f}"

        sl_distance = abs(tp.entry_price - tp.stop_loss)

        # Minimum SL floor — instrument-specific (default $5 for gold)
        sl_floor = self.config.get("risk", {}).get("sl_absolute_min", 5.0)
        if sl_distance < sl_floor:
            return f"sl_below_minimum_floor: SL_dist={sl_distance:.4f} < {sl_floor}"

        # ATR-based SL check — must be >= 1.5x M15 ATR
        m15_tf = mso.timeframes.get("M15") if hasattr(mso, "timeframes") else None
        m15_atr = getattr(m15_tf, "atr_14", 0) or 0 if m15_tf else 0

        if m15_atr > 0 and sl_distance < m15_atr * 1.5:
            return f"sl_too_tight: SL_dist={sl_distance:.2f} < 1.5*ATR={m15_atr * 1.5:.2f}"

        return None  # all checks pass

    def _get_future_candles(
        self, date_str: str, after_time: str,
    ) -> list[dict]:
        """Get M15 candles from after entry to end of that trading day."""
        m15 = self.all_candles.get("M15", [])
        # Include candles from entry time to midnight + next early morning
        end_time = f"{date_str}T23:59:59Z"
        return [
            c for c in m15
            if c["time"] > after_time and c["time"] <= end_time
        ]

    # ------------------------------------------------------------------
    # Batch runner
    # ------------------------------------------------------------------

    async def run_batch(
        self,
        start_date_str: str,
        end_date_str: str,
        resume: bool = False,
    ) -> None:
        """Run sessions for all trading days in the date range."""
        start = date.fromisoformat(start_date_str)
        end = date.fromisoformat(end_date_str)

        BATCH_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        progress_file = BATCH_RESULTS_DIR / "batch_progress.json"

        # Load progress for resume
        completed_dates: set[str] = set()
        if resume and progress_file.exists():
            progress = load_json(progress_file)
            completed_dates = set(progress.get("completed_dates", []))
            self._batch_results = progress.get("results", [])
            logger.info("Resuming: %d sessions already completed", len(completed_dates))

        # Count total weekdays in range
        total_days = 0
        d = start
        while d <= end:
            if d.weekday() < 5:
                total_days += 1
            d += timedelta(days=1)

        # Check we have M15 data
        if not self.all_candles.get("M15"):
            logger.error("No M15 candle data loaded. Run historical_data_loader.py first.")
            return

        session_num = len(completed_dates)
        cumulative_r = 0.0
        wins = sum(1 for r in self._batch_results if r.get("outcome") == "WIN")
        losses = sum(1 for r in self._batch_results if r.get("outcome") == "LOSS")
        trades_taken = wins + losses + sum(
            1 for r in self._batch_results if r.get("outcome") == "BREAKEVEN"
        )

        d = start
        while d <= end:
            if d.weekday() >= 5:
                d += timedelta(days=1)
                continue

            date_str = d.isoformat()

            if date_str in completed_dates:
                d += timedelta(days=1)
                continue

            # Check data availability
            has_data = any(
                c["time"].startswith(date_str)
                for c in self.all_candles["M15"]
            )
            if not has_data:
                logger.info("Skipping %s — no M15 data", date_str)
                d += timedelta(days=1)
                continue

            session_num += 1
            try:
                manifest = await self.run_session(date_str)

                # Extract result summary
                result = {
                    "date": date_str,
                    "trade_taken": manifest.trade_summary.trade_taken,
                    "outcome": manifest.trade_summary.outcome,
                    "r_multiple": manifest.trade_summary.r_multiple,
                    "api_calls": manifest.api_calls_count,
                    "cost_usd": manifest.api_cost_estimate_usd,
                    "errors": len(manifest.errors),
                    "decisions": [e.decision for e in manifest.candle_evaluations],
                }
                self._batch_results.append(result)
                completed_dates.add(date_str)

                # Update cumulative stats
                if result["outcome"]:
                    trades_taken += 1
                    r = result["r_multiple"] or 0.0
                    cumulative_r += r
                    if result["outcome"] == "WIN":
                        wins += 1
                    elif result["outcome"] == "LOSS":
                        losses += 1

                wr = (wins / trades_taken * 100) if trades_taken > 0 else 0
                exp = (cumulative_r / trades_taken) if trades_taken > 0 else 0

                decision = result["outcome"] or "NO_TRADE"
                if self.billing_mode == "subscription":
                    cost_label = "sub"
                else:
                    avg_cost = self._total_cost_usd / session_num if session_num else 0
                    cost_label = f"${self._total_cost_usd:.2f} (${avg_cost:.3f}/sess)"
                logger.info(
                    "Session %3d/%-3d | %s | %-9s | WR: %.0f%% | "
                    "Exp: %.2fR | Cost: %s | Retries: %d",
                    session_num, total_days, date_str, decision,
                    wr, exp, cost_label,
                    self._total_retries,
                )

                # Save intermediate progress
                atomic_write(progress_file, {
                    "completed_dates": sorted(completed_dates),
                    "results": self._batch_results,
                    "total_cost_usd": round(self._total_cost_usd, 4),
                    "total_input_tokens": self._total_input_tokens,
                    "total_output_tokens": self._total_output_tokens,
                    "total_retries": self._total_retries,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                })

                # Budget check (API mode only — subscription has no per-token cost)
                if self.billing_mode != "subscription" and self._total_cost_usd >= self.budget_limit:
                    logger.warning(
                        "BUDGET LIMIT REACHED: $%.2f >= $%.2f. Stopping batch.",
                        self._total_cost_usd, self.budget_limit,
                    )
                    break

            except Exception as exc:
                logger.error("Session %s FAILED: %s", date_str, exc)
                self._batch_results.append({
                    "date": date_str,
                    "trade_taken": False,
                    "outcome": None,
                    "r_multiple": None,
                    "error": str(exc),
                })
                completed_dates.add(date_str)

            d += timedelta(days=1)

        # Final summary
        report = self.generate_batch_report()
        logger.info("\n%s", report)

        report_path = BATCH_RESULTS_DIR / "batch_report.txt"
        report_path.write_text(report)
        logger.info("Report saved to %s", report_path)

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def generate_batch_report(self, *, from_disk: bool = False) -> str:
        """Compile all metrics from Section 9.1 into a formatted report.

        Parameters
        ----------
        from_disk : bool
            If True (used by --report mode), load results from
            batch_progress.json. If False (default, used after a live
            batch), only report on sessions that actually ran.
        """
        results = self._batch_results
        if not results and from_disk:
            # Only load stale results when explicitly asked (--report flag)
            progress_file = BATCH_RESULTS_DIR / "batch_progress.json"
            if progress_file.exists():
                progress = load_json(progress_file)
                results = progress.get("results", [])
                self._batch_results = results

        if not results:
            return (
                "No sessions ran in this batch.\n"
                "All dates may have been skipped due to missing data, "
                "weekends, or resume filtering.\n"
                "Use --report to view results from a previous batch."
            )

        total_sessions = len(results)
        sessions_with_errors = sum(1 for r in results if r.get("errors", 0) > 0 or r.get("error"))

        # Trade outcomes
        trades = [r for r in results if r.get("trade_taken")]
        no_trades = [r for r in results if not r.get("trade_taken")]
        wins = [t for t in trades if t.get("outcome") == "WIN"]
        losses = [t for t in trades if t.get("outcome") == "LOSS"]
        breakevens = [t for t in trades if t.get("outcome") == "BREAKEVEN"]

        num_trades = len(trades)
        win_rate = len(wins) / num_trades if num_trades else 0
        loss_rate = len(losses) / num_trades if num_trades else 0

        # R-multiples
        winner_rs = [t["r_multiple"] for t in wins if t.get("r_multiple") is not None]
        loser_rs = [t["r_multiple"] for t in losses if t.get("r_multiple") is not None]
        all_rs = [t["r_multiple"] for t in trades if t.get("r_multiple") is not None]

        avg_winner_r = sum(winner_rs) / len(winner_rs) if winner_rs else 0
        avg_loser_r = sum(abs(r) for r in loser_rs) / len(loser_rs) if loser_rs else 0
        total_r = sum(all_rs)
        expectancy = total_r / num_trades if num_trades else 0

        profit_factor = (
            sum(winner_rs) / sum(abs(r) for r in loser_rs)
            if loser_rs and sum(abs(r) for r in loser_rs) > 0
            else float("inf") if winner_rs else 0
        )

        # Max consecutive losses
        max_consec_loss = 0
        current_streak = 0
        for t in trades:
            if t.get("outcome") == "LOSS":
                current_streak += 1
                max_consec_loss = max(max_consec_loss, current_streak)
            else:
                current_streak = 0

        # Max drawdown (cumulative R)
        peak_r = 0.0
        running_r = 0.0
        max_dd_r = 0.0
        for t in trades:
            r = t.get("r_multiple", 0) or 0
            running_r += r
            if running_r > peak_r:
                peak_r = running_r
            dd = peak_r - running_r
            if dd > max_dd_r:
                max_dd_r = dd

        # Decisions breakdown
        all_decisions = []
        for r in results:
            all_decisions.extend(r.get("decisions", []))
        candidate_count = sum(1 for d in all_decisions if d == "CANDIDATE")
        no_trade_count = sum(1 for d in all_decisions if d == "NO_TRADE")

        # Section 9.1 metrics
        # False positive rate: CANDIDATE → trade taken → LOSS
        false_positives = len(losses)
        fp_rate = false_positives / num_trades if num_trades else 0

        # Debate metrics (if debate was enabled)
        debate_approvals = [
            t for t in trades
            if t.get("outcome") is not None
        ]
        debate_false_approvals = [t for t in debate_approvals if t["outcome"] == "LOSS"]
        debate_fa_rate = (
            len(debate_false_approvals) / len(debate_approvals)
            if debate_approvals else 0
        )

        # API costs
        total_api_calls = sum(r.get("api_calls", 0) for r in results)
        total_cost = sum(r.get("cost_usd", 0) for r in results)
        is_subscription = self.billing_mode == "subscription"

        # Format report
        lines = [
            "=" * 72,
            "BACKTEST REPORT",
            "=" * 72,
            f"  Billing mode:             {'Max subscription' if is_subscription else 'API (pay-per-token)'}",
            "",
            "── Overview ──────────────────────────────────────────────",
            f"  Total sessions:           {total_sessions}",
            f"  Sessions with errors:     {sessions_with_errors}",
            f"  Trades taken:             {num_trades}",
            f"  No-trade sessions:        {len(no_trades)}",
            f"  Trade frequency:          {num_trades/total_sessions*100:.1f}%" if total_sessions else "",
            "",
            "── Trade Outcomes ────────────────────────────────────────",
            f"  Wins:                     {len(wins)}",
            f"  Losses:                   {len(losses)}",
            f"  Breakeven:                {len(breakevens)}",
            f"  Win rate:                 {win_rate*100:.1f}%",
            "",
            "── R-Multiple Analysis ───────────────────────────────────",
            f"  Total R:                  {total_r:+.2f}R",
            f"  Avg winner:               {avg_winner_r:.2f}R",
            f"  Avg loser:                {avg_loser_r:.2f}R",
            f"  Expectancy:               {expectancy:.2f}R per trade",
            f"  Profit factor:            {profit_factor:.2f}",
            "",
            "── Risk Metrics ──────────────────────────────────────────",
            f"  Max consecutive losses:   {max_consec_loss}",
            f"  Max drawdown (R):         {max_dd_r:.2f}R",
            "",
            "── Section 9.1 Targets ───────────────────────────────────",
            f"  False positive rate:      {fp_rate*100:.1f}%  (target: <30%)",
            f"  Debate false approval:    {debate_fa_rate*100:.1f}%  (target: <20%)",
            f"  Combined expectancy:      {expectancy:.2f}R  (target: >0.5R)",
            f"  False negative rate:      [requires manual review]",
            f"  Debate false rejection:   [requires manual review]",
            "",
            "── Candle Decision Breakdown ─────────────────────────────",
            f"  Total candles evaluated:  {len(all_decisions)}",
            f"  CANDIDATE:                {candidate_count}",
            f"  NO_TRADE:                 {no_trade_count}",
            "",
            "── API Usage ─────────────────────────────────────────────",
            f"  Total LLM calls:          {total_api_calls}",
            *(
                [
                    f"  Estimated cost:           $0.00 (Max subscription)",
                    f"  Token tracking:           N/A (subscription mode)",
                ]
                if is_subscription else
                [
                    f"  Estimated cost:           ${total_cost:.2f}",
                    f"  Avg cost per session:     ${total_cost/total_sessions:.4f}" if total_sessions else "",
                    f"  Input tokens:             {self._total_input_tokens:,}",
                    f"  Output tokens:            {self._total_output_tokens:,}",
                ]
            ),
            f"  Malformed retries:        {self._total_retries}",
            "",
            "=" * 72,
        ]

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backtesting harness for the XAUUSD trading agent.",
    )
    parser.add_argument("--start", type=str, default="2025-10-01")
    parser.add_argument("--end", type=str, default="2026-03-28")

    debate_group = parser.add_mutually_exclusive_group()
    debate_group.add_argument("--debate", action="store_true",
                              help="Enable Bull/Bear debate")
    debate_group.add_argument("--no-debate", action="store_true", default=True,
                              help="Disable debate — PA + safety checks only (default)")

    parser.add_argument("--round2", action="store_true", default=False,
                        help="Enable debate Round 2")
    parser.add_argument("--no-round2", action="store_true", default=True,
                        help="Disable debate Round 2 (default)")

    parser.add_argument("--dry-run", action="store_true",
                        help="Skip API calls, test pipeline flow with mocks")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between API calls in seconds (default: 1.0)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume a crashed batch from saved progress")
    parser.add_argument("--report", action="store_true",
                        help="Generate report from existing batch data")
    parser.add_argument("--budget-limit", type=float, default=5.0,
                        help="Stop batch if total API cost exceeds this (default: $5.00)")
    parser.add_argument("--config", type=str, default="config/agent_config.yaml")
    parser.add_argument("--billing", choices=["api", "subscription", "batch"], default="api",
                        help="Billing mode: 'api' for pay-per-token, "
                             "'subscription' for Max plan via claude -p CLI, "
                             "'batch' for 50%% discount Batch API (use scripts/batch_backtest.py)")

    args = parser.parse_args()

    if args.report:
        runner = BacktestRunner(
            config_path=args.config,
            dry_run=True,
        )
        print(runner.generate_batch_report(from_disk=True))
        return

    debate_enabled = not args.no_debate
    round2_enabled = args.round2 and not args.no_round2

    # --- Batch mode redirect ---
    if args.billing == "batch":
        print()
        print("Batch mode uses a different script optimized for batch processing.")
        print("Run:")
        print(f"  python scripts/batch_backtest.py --start {args.start} --end {args.end} --dry-run")
        print()
        print("The batch script collects all prompts upfront, submits as a single")
        print("batch at 50% discount, and processes results when ready.")
        sys.exit(0)

    # --- Subscription billing verification ---
    if args.billing == "subscription":
        print()
        print("=" * 60)
        print("  SUBSCRIPTION BILLING MODE")
        print("=" * 60)
        print()
        print("  All LLM calls will route through 'claude -p' CLI,")
        print("  billed to your Max subscription (NOT API account).")
        print()
        print("  Prompt caching is NOT available in this mode.")
        print("  Cost per session may differ from API mode estimates.")
        print()

        # Create a temporary backend to run verification
        try:
            test_backend = LLMBackend(mode="subscription")
        except RuntimeError as e:
            print(f"  FATAL: {e}")
            sys.exit(1)

        if not test_backend.verify_billing_route():
            print("  Billing verification FAILED. Aborting.")
            sys.exit(1)

        confirm = input("  Type 'confirmed' to proceed with subscription billing: ").strip()
        if confirm.lower() != "confirmed":
            print("  Aborted by user.")
            sys.exit(0)
        print()

    runner = BacktestRunner(
        config_path=args.config,
        debate_enabled=debate_enabled,
        round2_enabled=round2_enabled,
        dry_run=args.dry_run,
        delay=args.delay,
        budget_limit=args.budget_limit,
        billing_mode=args.billing,
    )

    billing_label = "SUBSCRIPTION (Max plan)" if args.billing == "subscription" else "API (pay-per-token)"
    logger.info(
        "Starting backtest: %s → %s | billing=%s | debate=%s | round2=%s | dry_run=%s | budget=$%.2f",
        args.start, args.end, billing_label, debate_enabled, round2_enabled, args.dry_run,
        args.budget_limit,
    )

    asyncio.run(runner.run_batch(
        args.start, args.end, resume=args.resume,
    ))


if __name__ == "__main__":
    main()
