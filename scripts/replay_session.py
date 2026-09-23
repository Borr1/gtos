"""Historical Session Replay — Tests the live pipeline on historical data.

Usage:
    python scripts/replay_session.py --dates 2025-10-20 2025-10-24 2026-01-08
    python scripts/replay_session.py --date-file productive_dates.txt
    python scripts/replay_session.py --start 2025-10-01 --end 2025-10-31
    python scripts/replay_session.py --dry-run --dates 2025-10-20

Runs each date through the full live pipeline with:
- Sequential candle processing (not batch)
- Session memory (prior candle context injected into next evaluation)
- MockMT5 (no real orders)
- Full pipeline: data ingestion → MSO → pre-screen → PA → permissions → mock execution

Outputs comparison against batch backtest results.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
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
    parse_tradingview_csv,
    replay_london_open,
    replay_ny_open,
)
from scripts.backtest_runner import evaluate_hypothetical_outcome
from src.components.confidence_scorer import score_confidence
from src.components.market_state import compute_market_state
from src.components.permissions import check_permissions
from src.components.primary_analyzer import PrimaryAnalyzer, guard_candidate_null_params
from src.components.knowledge_base import KnowledgeBase
from src.llm_backend import LLMBackend
from src.models.analysis_models import TradeParameters
from src.mt5.mt5_mock import MockMT5
from src.components.execution import ExecutionEngine
from src.components.orchestrator import prescreen_mso
from src.utils.file_io import atomic_write
from src.utils.file_versioning import get_versioned_path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_LEGACY_LOG_DIR / "replay.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HISTORICAL_DIR = _PROJECT_ROOT / "data" / "historical"
BACKTEST_KB_DIR = _PROJECT_ROOT / "knowledge_base_backtest"
OUTPUT_DIR = BACKTEST_KB_DIR / "analysis" / "replay"

# Sonnet pricing: $3/M input, $15/M output, cache read $0.3/M, cache write $3.75/M
_COST_PER_INPUT_TOKEN = 3.0 / 1_000_000
_COST_PER_OUTPUT_TOKEN = 15.0 / 1_000_000
_COST_PER_CACHE_READ = 0.3 / 1_000_000
_COST_PER_CACHE_WRITE = 3.75 / 1_000_000


# ═══════════════════════════════════════════════════════════════════════
# Session memory management (mirrors orchestrator logic)
# ═══════════════════════════════════════════════════════════════════════

class SessionMemory:
    """Tracks candle evaluations within a kill zone (max 6 entries)."""

    def __init__(self):
        self.entries: list[dict] = []

    def update(self, candle_time: str, kill_zone: str, analysis) -> None:
        summary = self._compress(analysis)
        # Extract just the time portion for display
        t = candle_time.split("T")[1].replace("Z", "").replace(":00", "") if "T" in candle_time else candle_time
        self.entries.append({
            "time": f"{t} UTC",
            "kill_zone": kill_zone,
            "decision": analysis.decision,
            "summary": summary,
        })
        # Sliding window: keep last 6 per KZ
        kz_entries = [e for e in self.entries if e["kill_zone"] == kill_zone]
        if len(kz_entries) > 6:
            for i, e in enumerate(self.entries):
                if e["kill_zone"] == kill_zone:
                    self.entries.pop(i)
                    break

    def update_prescreen(self, candle_time: str, kill_zone: str, reason: str) -> None:
        t = candle_time.split("T")[1].replace("Z", "").replace(":00", "") if "T" in candle_time else candle_time
        self.entries.append({
            "time": f"{t} UTC",
            "kill_zone": kill_zone,
            "decision": "NO_TRADE",
            "summary": f"NO_TRADE — pre_screen: {reason}",
        })
        kz_entries = [e for e in self.entries if e["kill_zone"] == kill_zone]
        if len(kz_entries) > 6:
            for i, e in enumerate(self.entries):
                if e["kill_zone"] == kill_zone:
                    self.entries.pop(i)
                    break

    def format(self) -> str:
        if not self.entries:
            return ""
        lines = ["## Prior Candle Evaluations (This Session)"]
        for entry in self.entries[-6:]:
            lines.append(f"- {entry['time']}: {entry['summary']}")
        return "\n".join(lines)

    def snapshot(self) -> list[dict]:
        return copy.deepcopy(self.entries)

    def reset(self) -> None:
        self.entries = []

    @staticmethod
    def _compress(analysis) -> str:
        decision = analysis.decision
        if decision == "NO_TRADE":
            reason = analysis.no_trade_reason or "unknown"
            return f"NO_TRADE — {reason[:100]}"
        elif decision == "WAIT":
            reason = getattr(analysis, "wait_reason", "unknown") or "unknown"
            return f"WAIT — {reason[:100]}"
        elif decision == "CANDIDATE":
            tp = analysis.trade_parameters
            if tp is None:
                return "CANDIDATE — null trade_parameters (demoted)"
            r = analysis.reasoning
            grade = r.setup_grade if r else "?"
            conf = analysis.confidence_score
            return (f"CANDIDATE ({grade}, conf={conf}) — "
                    f"{tp.direction} entry={tp.entry_price}, "
                    f"SL={tp.stop_loss}, TP1={tp.take_profit_1}")
        return f"{decision}"


# ═══════════════════════════════════════════════════════════════════════
# Replay engine
# ═══════════════════════════════════════════════════════════════════════

class ReplayEngine:
    """Replays historical sessions through the live pipeline."""

    def __init__(self, config: dict, all_candles: dict, dry_run: bool = False):
        self.config = config
        self.all_candles = all_candles
        self.dry_run = dry_run

        # Pipeline components
        self.mt5 = MockMT5(balance=100_000.0)
        self.mt5.connect()
        self.execution = ExecutionEngine(self.mt5, config)

        # Analyzer (lazy init unless dry-run)
        self.analyzer: Optional[PrimaryAnalyzer] = None
        if not dry_run:
            billing_mode = config.get("ai", {}).get("billing_mode", "api")
            kb = KnowledgeBase()
            backend = LLMBackend(mode=billing_mode)
            self.analyzer = PrimaryAnalyzer(config, kb=kb, llm_backend=backend)

        # Tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_read = 0
        self.total_cache_create = 0
        self.total_cost = 0.0
        self.total_api_calls = 0

        # Results
        self.trade_results: list[dict] = []
        self.candle_log: list[dict] = []
        self.pa_responses: list[dict] = []  # Enhanced: full PA response for every evaluation
        self.session_memories: dict[str, dict] = {}  # date → {london: [...], ny: [...]}

    async def replay_date(self, date_str: str) -> dict:
        """Replay both kill zones for a single date."""
        logger.info(f"{'[DRY-RUN] ' if self.dry_run else ''}Replaying {date_str}")

        date_result = {
            "date": date_str,
            "london": {"trades": [], "candle_evals": 0, "api_calls": 0},
            "ny": {"trades": [], "candle_evals": 0, "api_calls": 0},
        }

        memory = SessionMemory()
        self.session_memories[date_str] = {"london": [], "ny": []}

        # Reset mock MT5 state for fresh session
        self.mt5 = MockMT5(balance=100_000.0)
        self.mt5.connect()
        self.execution = ExecutionEngine(self.mt5, self.config)

        # Session state (mirrors orchestrator)
        session_state = {
            "date": date_str,
            "trades_today": 0,
            "trades_london": 0,
            "trades_ny": 0,
            "daily_pnl_pct": 0.0,
            "current_kill_zone": None,
            "losses_today": 0,
        }

        # Reset analyzer session cache
        if self.analyzer:
            self.analyzer.reset_session_cache()

        # London Open
        london_result = await self._replay_kill_zone(
            date_str, "london", memory, session_state,
        )
        date_result["london"] = london_result

        # Reset memory between kill zones (matches orchestrator)
        memory.reset()

        # NY Open
        ny_result = await self._replay_kill_zone(
            date_str, "ny", memory, session_state,
        )
        date_result["ny"] = ny_result

        # Save session memory progression
        self.session_memories[date_str] = {
            "london": london_result.get("memory_progression", []),
            "ny": ny_result.get("memory_progression", []),
        }

        return date_result

    async def _replay_kill_zone(
        self,
        date_str: str,
        kill_zone: str,
        memory: SessionMemory,
        session_state: dict,
    ) -> dict:
        """Replay a single kill zone sequentially."""
        if kill_zone == "london":
            candle_gen = replay_london_open(date_str, self.all_candles)
        else:
            candle_gen = replay_ny_open(date_str, self.all_candles)

        kz_result = {
            "trades": [],
            "candle_evals": 0,
            "api_calls": 0,
            "memory_progression": [],
        }

        trade_executed = False
        session_state["current_kill_zone"] = kill_zone

        for raw_data in candle_gen:
            candle_time = raw_data["timestamp_utc"]
            kz_result["candle_evals"] += 1

            # Skip if already traded in this KZ
            kz_key = f"trades_{kill_zone}"
            if session_state.get(kz_key, 0) >= 1:
                logger.debug(f"  Already traded in {kill_zone} — skipping {candle_time}")
                break

            # 1. Compute MSO
            mso = compute_market_state(raw_data, self.config)

            # 2. Pre-screen
            passed, reason = prescreen_mso(mso)
            if not passed:
                memory.update_prescreen(candle_time, kill_zone, reason)
                self._log_candle(date_str, candle_time, kill_zone, "NO_TRADE",
                                 f"pre_screen: {reason}", memory.snapshot())
                continue

            # 3. Dry-run: just count, don't call API
            if self.dry_run:
                kz_result["api_calls"] += 1
                self.total_api_calls += 1
                self._log_candle(date_str, candle_time, kill_zone, "DRY_RUN",
                                 "would_call_api", memory.snapshot())
                continue

            # 4. Run Primary Analyzer WITH session memory
            memory_block = memory.format()
            try:
                analysis = await self.analyzer.analyze(
                    market_state=mso,
                    kill_zone=kill_zone,
                    session_memory=memory_block,
                )
            except Exception as e:
                logger.error(f"  Analyzer error on {candle_time}: {e}")
                self._log_candle(date_str, candle_time, kill_zone, "ERROR",
                                 str(e), memory.snapshot())
                continue

            # Track API usage
            usage = getattr(self.analyzer, "_last_usage", {})
            inp = usage.get("input_tokens", 0)
            out = usage.get("output_tokens", 0)
            cache_r = usage.get("cache_read_tokens", 0)
            cache_w = usage.get("cache_create_tokens", 0)
            self.total_input_tokens += inp
            self.total_output_tokens += out
            self.total_cache_read += cache_r
            self.total_cache_create += cache_w
            call_cost = (inp * _COST_PER_INPUT_TOKEN +
                         out * _COST_PER_OUTPUT_TOKEN +
                         cache_r * _COST_PER_CACHE_READ +
                         cache_w * _COST_PER_CACHE_WRITE)
            self.total_cost += call_cost
            self.total_api_calls += 1
            kz_result["api_calls"] += 1

            # 5. Update session memory
            memory.update(candle_time, kill_zone, analysis)
            kz_result["memory_progression"].append(memory.snapshot())

            # 5b. Enhanced: Log full PA response for every evaluation
            reasoning_text = ""
            if analysis.reasoning:
                reasoning_text = analysis.reasoning.overall_reasoning or ""
            no_trade_reason = analysis.no_trade_reason if analysis.decision == "NO_TRADE" else None
            self.pa_responses.append({
                "date": date_str,
                "kz": kill_zone,
                "candle_time": candle_time,
                "decision": analysis.decision,
                "reasoning_text": reasoning_text[:500],  # Cap at 500 chars
                "no_trade_reason": no_trade_reason,
                "grade": analysis.reasoning.setup_grade if analysis.reasoning else None,
                "confidence": analysis.confidence_score,
                "framework": getattr(analysis, "framework", None),
                "memory_depth": len(memory.snapshot()),
                "candle_index_in_kz": kz_result["candle_evals"],
            })

            # 6. Log candle
            detail = ""
            if analysis.decision == "NO_TRADE":
                detail = analysis.no_trade_reason or ""
            elif analysis.decision == "WAIT":
                detail = getattr(analysis, "wait_reason", "") or ""
            elif analysis.decision == "CANDIDATE":
                tp = analysis.trade_parameters
                detail = (f"{tp.direction} entry={tp.entry_price} "
                          f"SL={tp.stop_loss} TP1={tp.take_profit_1}")

            self._log_candle(date_str, candle_time, kill_zone, analysis.decision,
                             detail, memory.snapshot(),
                             confidence=analysis.confidence_score,
                             framework=getattr(analysis, "framework", None),
                             grade=analysis.reasoning.setup_grade if analysis.reasoning else None)

            if analysis.decision != "CANDIDATE":
                continue

            # 7. Permission check
            # Set mock tick to entry price for spread check
            entry_price = analysis.trade_parameters.entry_price
            self.mt5.set_tick(entry_price - 0.10, entry_price + 0.10)

            symbol = self.config.get("market", {}).get("symbol", "XAUUSD")
            denial = check_permissions(analysis, mso, session_state, self.mt5,
                                        config=self.config, symbol=symbol)
            if denial:
                self._log_candle(date_str, candle_time, kill_zone, "REJECTED",
                                 f"{denial.gate}: {denial.reason}", memory.snapshot())
                logger.info(f"  REJECTED: {denial.gate} — {denial.reason}")
                continue

            # 8. Mock execute
            balance = self.mt5.get_account_balance()
            tp = analysis.trade_parameters
            trade_state = self.execution.open_trade(
                trade_params={
                    "direction": tp.direction,
                    "entry_price": tp.entry_price,
                    "stop_loss": tp.stop_loss,
                    "take_profit_1": tp.take_profit_1,
                    "take_profit_2": tp.take_profit_2,
                    "take_profit_3": tp.take_profit_3,
                    "risk_reward_ratio": tp.risk_reward_ratio,
                },
                account_balance=balance,
            )

            if trade_state:
                session_state["trades_today"] += 1
                session_state[kz_key] = session_state.get(kz_key, 0) + 1
                trade_executed = True
                logger.info(f"  EXECUTED: {tp.direction} @ {tp.entry_price} "
                            f"(grade={analysis.reasoning.setup_grade}, "
                            f"conf={analysis.confidence_score})")

                # Evaluate hypothetical outcome
                future = self._get_future_candles(date_str, candle_time)
                outcome = evaluate_hypothetical_outcome(tp, future)

                trade_record = {
                    "date": date_str,
                    "kill_zone": kill_zone,
                    "candle_time": candle_time,
                    "framework": analysis.framework if hasattr(analysis, "framework") else
                                 (analysis.reasoning.overall_reasoning[:50] if analysis.reasoning else "unknown"),
                    "direction": tp.direction,
                    "entry_price": tp.entry_price,
                    "stop_loss": tp.stop_loss,
                    "take_profit_1": tp.take_profit_1,
                    "take_profit_2": tp.take_profit_2,
                    "take_profit_3": tp.take_profit_3,
                    "risk_reward_ratio": tp.risk_reward_ratio,
                    "setup_grade": analysis.reasoning.setup_grade if analysis.reasoning else "?",
                    "confidence_score": analysis.confidence_score,
                    "confidence_metrics": score_confidence(analysis.model_dump()).model_dump(),
                    "outcome": outcome["outcome"],
                    "r_multiple": outcome["r_multiple"],
                    "exit_substate": outcome.get("exit_substate"),
                    "mfe_r": outcome.get("mfe_r"),
                    "mae_r": outcome.get("mae_r"),
                    "hold_time_candles": outcome.get("hold_time_candles"),
                    "r_path": outcome.get("r_path", []),  # Enhanced: full candle-by-candle R-path
                    "session_memory_at_entry": memory.snapshot(),
                    "session_memory_formatted": memory_block,
                    "candles_evaluated_before_entry": kz_result["candle_evals"],
                    "candle_index_in_kz": kz_result["candle_evals"],  # Enhanced: which candle in KZ triggered entry
                    "source": "replay",
                }
                kz_result["trades"].append(trade_record)
                self.trade_results.append(trade_record)

                # Max 1 trade per KZ — break
                break
            else:
                logger.warning(f"  EXECUTION_FAILED on {candle_time}")

        return kz_result

    def _get_future_candles(self, date_str: str, after_time: str) -> list[dict]:
        """Get M15 candles from after entry to end of trading day."""
        m15 = self.all_candles.get("M15", [])
        end_time = f"{date_str}T23:59:59Z"
        return [c for c in m15 if c["time"] > after_time and c["time"] <= end_time]

    def _log_candle(self, date_str, candle_time, kill_zone, decision, detail,
                    memory_state, confidence=None, framework=None, grade=None,
                    candle_index_in_kz=None):
        entry = {
            "date": date_str,
            "candle_time": candle_time,
            "kill_zone": kill_zone,
            "decision": decision,
            "detail": detail,
            "memory_entries": len(memory_state),
            "memory_depth": len(memory_state),  # Enhanced: explicit depth
            "candle_index_in_kz": candle_index_in_kz,  # Enhanced: position in KZ
            "confidence": confidence,
            "framework": framework,
            "grade": grade,
        }
        self.candle_log.append(entry)


# ═══════════════════════════════════════════════════════════════════════
# Comparison report
# ═══════════════════════════════════════════════════════════════════════

def load_batch_trades() -> list[dict]:
    """Load batch backtest results for comparison."""
    path = BACKTEST_KB_DIR / "analysis" / "unified_trades_v2.json"
    if not path.exists():
        path = BACKTEST_KB_DIR / "analysis" / "unified_trades.json"
    if not path.exists():
        logger.warning("No batch backtest results found for comparison")
        return []
    with open(path) as f:
        return json.load(f)


def generate_comparison_report(
    replay_trades: list[dict],
    candle_log: list[dict],
    total_cost: float,
    total_api_calls: int,
    dates_replayed: list[str],
    dry_run: bool = False,
) -> str:
    """Generate markdown comparison report."""
    batch_trades = load_batch_trades()

    # Index batch by (date, kill_zone)
    batch_by_date_kz: dict[tuple, dict] = {}
    for t in batch_trades:
        key = (t["date"], t.get("kill_zone", "london"))
        batch_by_date_kz[key] = t

    # Index replay by (date, kill_zone)
    replay_by_date_kz: dict[tuple, dict] = {}
    for t in replay_trades:
        key = (t["date"], t["kill_zone"])
        replay_by_date_kz[key] = t

    lines = []
    lines.append("# REPLAY vs BATCH COMPARISON")
    lines.append("=" * 50)
    lines.append("")

    if dry_run:
        lines.append("**MODE: DRY-RUN (no API calls made)**")
        lines.append("")
        lines.append(f"Dates to replay: {len(dates_replayed)}")
        total_candles = len(candle_log)
        api_calls = sum(1 for c in candle_log if c["decision"] == "DRY_RUN")
        lines.append(f"Total candles: {total_candles}")
        lines.append(f"API calls needed: {api_calls}")
        est_cost = api_calls * 0.02  # ~$0.02 per Sonnet call
        lines.append(f"Estimated cost: ${est_cost:.2f}")
        return "\n".join(lines)

    lines.append(f"Dates replayed: {len(dates_replayed)}")
    lines.append(f"Candles evaluated: {len(candle_log)} (with session memory)")
    lines.append(f"API calls: {total_api_calls}")
    lines.append(f"API cost: ${total_cost:.2f}")
    lines.append("")

    # Overall stats
    def compute_stats(trades):
        if not trades:
            return {"count": 0, "wr": 0, "total_r": 0, "exp": 0}
        wins = sum(1 for t in trades if t.get("outcome") == "WIN")
        count = len(trades)
        wr = (wins / count * 100) if count else 0
        total_r = sum(t.get("r_multiple", 0) for t in trades)
        exp = total_r / count if count else 0
        return {"count": count, "wr": round(wr, 1), "total_r": round(total_r, 2),
                "exp": round(exp, 2)}

    # Filter batch to only dates we replayed
    replay_dates = set(dates_replayed)
    batch_on_dates = [t for t in batch_trades if t["date"] in replay_dates]

    b_stats = compute_stats(batch_on_dates)
    r_stats = compute_stats(replay_trades)

    lines.append("## OVERALL")
    lines.append(f"  Batch:  {b_stats['count']} trades, {b_stats['wr']}% WR, "
                 f"+{b_stats['total_r']}R total, {b_stats['exp']}R exp")
    lines.append(f"  Replay: {r_stats['count']} trades, {r_stats['wr']}% WR, "
                 f"+{r_stats['total_r']}R total, {r_stats['exp']}R exp")
    lines.append("")

    # Trade-by-trade diff
    all_keys = set(list(batch_by_date_kz.keys()) + list(replay_by_date_kz.keys()))
    both_same_outcome = 0
    both_diff_outcome = 0
    batch_only = 0
    replay_only = 0
    diff_candle = 0
    diff_details = []

    for key in sorted(all_keys):
        if key[0] not in replay_dates:
            continue
        b = batch_by_date_kz.get(key)
        r = replay_by_date_kz.get(key)

        if b and r:
            if b.get("outcome") == r.get("outcome"):
                both_same_outcome += 1
            else:
                both_diff_outcome += 1
                diff_details.append(
                    f"  {key[0]} {key[1]}: batch={b.get('outcome')} "
                    f"({b.get('r_multiple',0):+.2f}R) → replay={r.get('outcome')} "
                    f"({r.get('r_multiple',0):+.2f}R)")
        elif b and not r:
            batch_only += 1
            diff_details.append(
                f"  {key[0]} {key[1]}: batch traded ({b.get('outcome')}), "
                f"replay DID NOT trade")
        elif r and not b:
            replay_only += 1
            diff_details.append(
                f"  {key[0]} {key[1]}: replay traded ({r.get('outcome')}), "
                f"batch DID NOT trade")

    lines.append("## TRADE-BY-TRADE DIFF (same dates)")
    lines.append(f"  Both took same trade, same outcome: {both_same_outcome}")
    lines.append(f"  Both took same trade, different outcome: {both_diff_outcome}")
    lines.append(f"  Batch traded, replay didn't: {batch_only} (session memory caused skip?)")
    lines.append(f"  Replay traded, batch didn't: {replay_only} (session memory found opportunity?)")
    lines.append("")

    if diff_details:
        lines.append("### Differences:")
        lines.extend(diff_details)
        lines.append("")

    # Session memory analysis
    with_memory = [t for t in replay_trades if t.get("session_memory_at_entry")]
    mem_counts = [len(t["session_memory_at_entry"]) for t in with_memory]
    avg_mem = sum(mem_counts) / len(mem_counts) if mem_counts else 0

    lines.append("## SESSION MEMORY ANALYSIS")
    lines.append(f"  Trades where session memory had context: {len(with_memory)}")
    lines.append(f"  Average memory entries at CANDIDATE time: {avg_mem:.1f}")
    lines.append("")

    # Confidence comparison
    b_confs = [t.get("confidence_score", 0) for t in batch_on_dates if t.get("confidence_score")]
    r_confs = [t.get("confidence_score", 0) for t in replay_trades if t.get("confidence_score")]
    b_avg_conf = sum(b_confs) / len(b_confs) if b_confs else 0
    r_avg_conf = sum(r_confs) / len(r_confs) if r_confs else 0

    lines.append("## CONFIDENCE SCORE COMPARISON")
    lines.append(f"  Batch avg confidence: {b_avg_conf:.1f}")
    lines.append(f"  Replay avg confidence: {r_avg_conf:.1f}")
    if r_confs:
        import statistics
        lines.append(f"  Replay confidence std dev: {statistics.stdev(r_confs):.1f}" if len(r_confs) > 1 else "")
    lines.append("")

    # Framework breakdown
    r_frameworks = {}
    for t in replay_trades:
        fw = t.get("framework", "unknown")
        r_frameworks.setdefault(fw, []).append(t)

    if r_frameworks:
        lines.append("## FRAMEWORK BREAKDOWN (Replay)")
        for fw, trades in sorted(r_frameworks.items()):
            s = compute_stats(trades)
            lines.append(f"  {fw}: {s['count']} trades, {s['wr']}% WR, {s['exp']}R exp")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# Date selection helpers
# ═══════════════════════════════════════════════════════════════════════

def get_ob_retest_dates() -> list[str]:
    """Get dates where batch took ob_retest trades (Tier 1)."""
    batch = load_batch_trades()
    return sorted(set(t["date"] for t in batch if t.get("framework") == "ob_retest"))


def parse_dates(args) -> list[str]:
    """Parse date arguments into a sorted list of date strings."""
    dates: list[str] = []

    if args.dates:
        dates = args.dates

    elif args.date_file:
        with open(args.date_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    dates.append(line)

    elif args.start and args.end:
        d = date.fromisoformat(args.start)
        end = date.fromisoformat(args.end)
        while d <= end:
            if d.weekday() < 5:  # Skip weekends
                dates.append(d.isoformat())
            d += timedelta(days=1)

    elif args.tier1:
        dates = get_ob_retest_dates()
        if args.limit:
            dates = dates[:args.limit]

    if not dates:
        logger.error("No dates specified. Use --dates, --date-file, --start/--end, or --tier1")
        sys.exit(1)

    return sorted(set(dates))


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def load_candles() -> dict[str, list[dict]]:
    """Load historical candle CSVs."""
    all_candles: dict[str, list[dict]] = {}
    for tf in ("D1", "H4", "H1", "M15"):
        csv_path = HISTORICAL_DIR / f"XAUUSD_{tf}.csv"
        if csv_path.exists():
            all_candles[tf] = parse_tradingview_csv(csv_path)
            logger.info(f"Loaded {tf}: {len(all_candles[tf])} candles")
        else:
            logger.warning(f"No CSV for {tf} at {csv_path}")
            all_candles[tf] = []
    return all_candles


async def main():
    parser = argparse.ArgumentParser(description="Historical Session Replay")

    # Date selection
    date_group = parser.add_argument_group("Date selection")
    date_group.add_argument("--dates", nargs="+", help="Specific dates (YYYY-MM-DD)")
    date_group.add_argument("--date-file", help="File with one date per line")
    date_group.add_argument("--start", help="Start date (YYYY-MM-DD)")
    date_group.add_argument("--end", help="End date (YYYY-MM-DD)")
    date_group.add_argument("--tier1", action="store_true",
                            help="Use Tier 1 dates (ob_retest batch trades)")
    date_group.add_argument("--limit", type=int, help="Max dates to replay (with --tier1)")

    # Options
    parser.add_argument("--dry-run", action="store_true",
                        help="Count API calls without making them")
    parser.add_argument("--billing", default="api", choices=["api", "subscription"],
                        help="LLM billing mode (default: api)")
    parser.add_argument("--config", default="config/agent_config.yaml",
                        help="Path to config file")
    parser.add_argument("--output-prefix", default=None,
                        help="Output prefix (e.g. 'supplementary'). Saves to versioned files instead of overwriting defaults.")

    args = parser.parse_args()
    dates = parse_dates(args)

    logger.info(f"Dates to replay: {len(dates)}")
    if len(dates) <= 10:
        logger.info(f"Dates: {dates}")

    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)

    # Override billing mode from CLI
    config.setdefault("ai", {})["billing_mode"] = args.billing

    # Load candles
    all_candles = load_candles()
    if not all_candles.get("M15"):
        logger.error("No M15 data. Run historical_data_loader.py first.")
        sys.exit(1)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Run replay
    engine = ReplayEngine(config, all_candles, dry_run=args.dry_run)

    start_time = time_mod.time()
    all_date_results = []

    for i, date_str in enumerate(dates, 1):
        logger.info(f"[{i}/{len(dates)}] Replaying {date_str}")
        try:
            result = await engine.replay_date(date_str)
            all_date_results.append(result)
        except Exception as e:
            logger.error(f"Failed to replay {date_str}: {e}", exc_info=True)
            all_date_results.append({"date": date_str, "error": str(e)})

        # Progress update every 5 dates
        if i % 5 == 0:
            elapsed = time_mod.time() - start_time
            logger.info(f"Progress: {i}/{len(dates)} dates, "
                        f"{engine.total_api_calls} API calls, "
                        f"${engine.total_cost:.2f} cost, "
                        f"{elapsed:.0f}s elapsed")

    elapsed = time_mod.time() - start_time
    logger.info(f"Replay complete: {len(dates)} dates in {elapsed:.0f}s")
    logger.info(f"Total API calls: {engine.total_api_calls}")
    logger.info(f"Total cost: ${engine.total_cost:.2f}")
    logger.info(f"Trades found: {len(engine.trade_results)}")

    # Save results
    prefix = args.output_prefix
    if prefix:
        # Versioned supplementary output — saves to analysis/ not replay/
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        analysis_dir = BACKTEST_KB_DIR / "analysis"

        # 1. Trade results (with r_path)
        results_path = analysis_dir / f"{prefix}_replay_{ts}.json"
        atomic_write(str(results_path), engine.trade_results)
        logger.info(f"Saved trade results: {results_path}")

        # 1b. PA responses (JSONL for streaming)
        pa_path = analysis_dir / f"{prefix}_pa_responses_{ts}.jsonl"
        with open(pa_path, "w") as f:
            for resp in engine.pa_responses:
                f.write(json.dumps(resp) + "\n")
        logger.info(f"Saved PA responses: {pa_path} ({len(engine.pa_responses)} entries)")

        # 2. Candle log
        candle_log_path = analysis_dir / f"{prefix}_candle_log_{ts}.json"
        atomic_write(str(candle_log_path), engine.candle_log)
        logger.info(f"Saved candle log: {candle_log_path}")
    else:
        # Default: overwrite main replay files
        # 1. Trade results
        results_path = OUTPUT_DIR / "replay_results.json"
        atomic_write(str(results_path), engine.trade_results)
        logger.info(f"Saved trade results: {results_path}")

        # 1b. PA responses (JSONL)
        pa_path = OUTPUT_DIR / "replay_pa_responses.jsonl"
        with open(pa_path, "w") as f:
            for resp in engine.pa_responses:
                f.write(json.dumps(resp) + "\n")
        logger.info(f"Saved PA responses: {pa_path} ({len(engine.pa_responses)} entries)")

        # 2. Candle log
        candle_log_path = OUTPUT_DIR / "replay_candle_log.json"
        atomic_write(str(candle_log_path), engine.candle_log)
        logger.info(f"Saved candle log: {candle_log_path}")

    # 3. Session memories
    memories_dir = OUTPUT_DIR / "replay_session_memories"
    memories_dir.mkdir(parents=True, exist_ok=True)
    for date_str, mem_data in engine.session_memories.items():
        mem_path = memories_dir / f"{date_str}.json"
        atomic_write(str(mem_path), mem_data)

    # 4. Comparison report
    report = generate_comparison_report(
        engine.trade_results,
        engine.candle_log,
        engine.total_cost,
        engine.total_api_calls,
        dates,
        dry_run=args.dry_run,
    )
    report_path = get_versioned_path(OUTPUT_DIR, "replay_comparison", ".md")
    with open(report_path, "w") as f:
        f.write(report)
    logger.info(f"Saved comparison report: {report_path}")

    # Print summary to stdout
    print("\n" + report)


if __name__ == "__main__":
    asyncio.run(main())
