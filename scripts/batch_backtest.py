"""Batch backtesting via Anthropic Message Batches API.

Submits ALL Primary Analyzer calls as a single batch at 50% discount.
Prompt caching stacks with batch for ~70-75% total savings.

Usage:
    # Dry-run: build prompts, estimate cost, don't submit
    python scripts/batch_backtest.py --start 2025-04-01 --end 2025-09-30 --dry-run

    # Submit batch and wait for results
    python scripts/batch_backtest.py --start 2025-04-01 --end 2025-09-30

    # Resume processing a previously submitted batch
    python scripts/batch_backtest.py --resume-batch msgbatch_XXXXX
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

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

from anthropic import Anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from scripts.historical_data_loader import (
    parse_tradingview_csv,
    replay_london_open,
    replay_ny_open,
    replay_kill_zone,
)
from src.components.knowledge_base import KnowledgeBase
from src.components.market_state import compute_market_state
from src.components.confidence_scorer import score_confidence
from src.components.primary_analyzer import PrimaryAnalyzer, _normalize_pa_fields
from src.prompts.primary_analyzer_prompt import format_cross_instrument_context
from src.utils.cross_instrument import get_xauusd_d1_direction, get_asian_range_pct
from src.models.analysis_models import PrimaryAnalysisOutput, TradeParameters
from src.models.trade_models import (
    CandleEvaluation,
    SessionManifest,
    TradeSummary,
)
from src.utils.file_io import atomic_write, load_json
from src.utils.validation import strip_json_fences

# Re-use outcome evaluation from the sequential runner
from scripts.backtest_runner import (
    evaluate_hypothetical_outcome,
    BACKTEST_KB_DIR,
    BATCH_RESULTS_DIR,
    HISTORICAL_DIR,
    _COST_PER_INPUT_TOKEN,
    _COST_PER_OUTPUT_TOKEN,
    _COST_PER_CACHE_READ,
    _COST_PER_CACHE_WRITE,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_LEGACY_LOG_DIR / "batch_backtest.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# Batch pricing: 50% of standard
_BATCH_INPUT_PER_MTOK = 1.50
_BATCH_OUTPUT_PER_MTOK = 7.50
_BATCH_CACHE_WRITE_PER_MTOK = 1.875
_BATCH_CACHE_READ_PER_MTOK = 0.15

BATCH_STATE_DIR = BACKTEST_KB_DIR / "batch_api"


# ═══════════════════════════════════════════════════════════════════════
# Pre-screen filters (deterministic, zero API cost)
# ═══════════════════════════════════════════════════════════════════════

def prescreen_date(
    date_str: str,
    all_candles: dict[str, list[dict]],
    config: dict,
) -> tuple[bool, str]:
    """Check if a date has enough directional consensus to warrant an API call.

    Uses Component 2 (MSO) data — no API calls.  Builds the MSO once
    from the first London-open candle and inspects D1/H4 structure direction.

    Pass when D1 is clear (H4 must agree), or when D1 is unclear but H4
    is clearly directional (AI uses H4+H1 consensus via U1).
    Skip only when both D1 and H4 lack clear direction.

    Returns (passed, skip_reason).  If ``passed`` is True, *skip_reason*
    is the empty string.
    """
    # Build MSO from the first London candle to read D1/H4 structure
    try:
        candle_gen = replay_london_open(date_str, all_candles)
        first_raw = next(candle_gen)
    except (StopIteration, Exception):
        return False, "no_london_candles"

    mso = compute_market_state(first_raw, config)
    tfs = mso.timeframes if hasattr(mso, "timeframes") else {}

    d1 = tfs.get("D1")
    d1_dir = d1.structure.direction if d1 else "insufficient_data"
    h4 = tfs.get("H4")
    h4_dir = h4.structure.direction if h4 else "insufficient_data"

    d1_clear = d1_dir in ("bullish", "bearish")
    h4_clear = h4_dir in ("bullish", "bearish")

    # Both unclear → no directional consensus possible, skip
    if not d1_clear and not h4_clear:
        return False, f"L1_no_direction_d1_{d1_dir}_h4_{h4_dir}"

    # D1 clear but H4 conflicts → skip
    if d1_clear and h4_clear and h4_dir != d1_dir:
        return False, f"L2_h4_conflict_{h4_dir}_vs_d1_{d1_dir}"

    return True, ""


# ═══════════════════════════════════════════════════════════════════════
# Phase 1: COLLECT — Build all prompts (no API calls)
# ═══════════════════════════════════════════════════════════════════════

def collect_prompts(
    start_str: str,
    end_str: str,
    config: dict,
    all_candles: dict[str, list[dict]],
    prescreen: bool = True,
    vision: bool = False,
    ref_candles: dict[str, list[dict]] | None = None,
    target_dates: list[str] | None = None,
) -> tuple[list[dict], dict]:
    """Build PA prompts for every M15 candle in BOTH kill zones.

    When *prescreen* is True (default), dates where D1 bias is not
    clearly bullish/bearish or H4 conflicts with D1 are skipped entirely.

    When *vision* is True, each request also includes a rendered M15 chart
    as base64 PNG in ``request["chart_b64"]``.

    *ref_candles*: optional dict of reference instrument candle data
    (e.g. ``{"D1": [...]}``) for cross-instrument context.

    *target_dates*: optional list of specific dates (YYYY-MM-DD) to evaluate.
    When provided, *start_str* and *end_str* are ignored and only the
    listed dates are processed.

    Returns ``(requests, prescreen_stats)`` where *prescreen_stats* has
    keys: total_dates, no_data, l1_skip, l2_skip, passed, prescreen_enabled.
    """
    import src.utils.file_io as fio
    fio.KNOWLEDGE_BASE_DIR = BACKTEST_KB_DIR

    kb = KnowledgeBase(base_path=str(BACKTEST_KB_DIR))
    kb.initialize_rules()
    pa = PrimaryAnalyzer(config, kb)

    if target_dates:
        date_list = sorted(set(target_dates))
    else:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        date_list = []
        d = start
        while d <= end:
            if d.weekday() < 5:
                date_list.append(d.isoformat())
            d += timedelta(days=1)

    all_requests: list[dict] = []
    stats = {
        "total_dates": 0,
        "no_data": 0,
        "l1_skip": 0,
        "l2_skip": 0,
        "passed": 0,
        "prescreen_enabled": prescreen,
    }

    for date_str in date_list:
        stats["total_dates"] += 1

        # Check M15 data availability
        has_data = any(
            c["time"].startswith(date_str)
            for c in all_candles.get("M15", [])
        )
        if not has_data:
            stats["no_data"] += 1
            continue

        # ── Pre-screen (deterministic, zero API cost) ─────────────
        if prescreen:
            passed, reason = prescreen_date(date_str, all_candles, config)
            if not passed:
                if reason.startswith("L1_"):
                    stats["l1_skip"] += 1
                elif reason.startswith("L2_"):
                    stats["l2_skip"] += 1
                else:
                    stats["no_data"] += 1
                logger.debug("Pre-screen skip %s: %s", date_str, reason)
                continue

        stats["passed"] += 1

        # ── Chart rendering setup (vision mode) ────────────────────
        _render_chart = None
        if vision:
            try:
                from src.utils.chart_renderer import render_chart_from_mso, chart_to_base64
                _render_chart = render_chart_from_mso
            except ImportError:
                logger.warning("Vision mode requires plotly+kaleido. Falling back to JSON-only.")
                vision = False

        # ── Cross-instrument context (computed once per date) ────
        ci_ctx_text = ""
        ci_cfg = config.get("cross_instrument_context", {})
        if ci_cfg.get("enabled") and ref_candles:
            ref_d1 = ref_candles.get("D1", [])
            xau_dir = get_xauusd_d1_direction(date_str, ref_d1)
            asian_info = get_asian_range_pct(
                date_str, all_candles.get("M15", []), all_candles.get("D1", []),
            )
            ci_ctx_text = format_cross_instrument_context(
                xau_dir, asian_info, config,
            )

        def _build_request(raw_data, candle_time, kz, mso):
            prompt = pa.build_prompt(
                mso, candle_time, kill_zone=kz,
                cross_instrument_context=ci_ctx_text,
            )
            time_tag = candle_time[11:16].replace(":", "")
            custom_id = f"{date_str}_{kz}_{time_tag}"
            req = {
                "custom_id": custom_id,
                "date": date_str,
                "candle_time": candle_time,
                "kill_zone": kz,
                "prompt": prompt,
            }
            if vision and _render_chart:
                try:
                    m15 = all_candles.get("M15", [])
                    window = [c for c in m15 if c["time"] <= candle_time][-40:]
                    chart_bytes = _render_chart(mso, window, kz)
                    req["chart_b64"] = chart_to_base64(chart_bytes)
                except Exception as exc:
                    logger.debug("Chart render failed for %s: %s", custom_id, exc)
            return req

        # ── Replay all configured kill zones ─────────────────────
        kz_cfg = config.get("market", {}).get("kill_zones", {})
        for kz_name, kz_times in kz_cfg.items():
            kz_start = kz_times.get("start_utc", "07:00")
            kz_end = kz_times.get("end_utc", "09:30")
            pa.reset_session_cache()
            try:
                candle_gen = replay_kill_zone(
                    date_str, all_candles,
                    kz_start=kz_start, kz_end=kz_end,
                )
                for raw_data in candle_gen:
                    candle_time = raw_data["timestamp_utc"]
                    mso = compute_market_state(raw_data, config)
                    all_requests.append(_build_request(raw_data, candle_time, kz_name, mso))
            except Exception as exc:
                logger.warning("Failed to build %s prompts for %s: %s", kz_name, date_str, exc)

    kz_counts = {}
    for r in all_requests:
        kz_counts[r["kill_zone"]] = kz_counts.get(r["kill_zone"], 0) + 1
    kz_summary = " + ".join(f"{v} {k.title()}" for k, v in sorted(kz_counts.items()))
    logger.info(
        "Collected %d prompts (%s) from %d sessions "
        "(%d dates skipped — no data, %d L1, %d L2)",
        len(all_requests), kz_summary, stats["passed"],
        stats["no_data"], stats["l1_skip"], stats["l2_skip"],
    )
    return all_requests, stats


# ═══════════════════════════════════════════════════════════════════════
# Phase 2: SUBMIT — Send batch to Anthropic
# ═══════════════════════════════════════════════════════════════════════

_VISION_PREAMBLE = """## Chart Image Provided
An M15 candlestick chart is attached showing the current price action with annotations:
- Green/teal shaded zones: unmitigated bullish H1 order blocks (labeled BOS or CHoCH origin)
- Red/pink shaded zones: unmitigated bearish H1 order blocks
- Dashed horizontal lines: session levels (Asian H/L, PDH/PDL, London H/L)
- Solid horizontal line with label: H1 structure break level (CHoCH or BOS)

USE THE CHART TO VISUALLY ASSESS:
1. Order block quality — clean single-candle impulse OB vs messy multi-candle consolidation
2. Displacement character — was the structural break a clean impulsive move or choppy/overlapping?
3. Price reaction at the OB — sharp rejection with wicks (strong) vs sitting inside with small bodies (weak)
4. Overall price action context — clean trending swings vs choppy overlapping noise
5. Candle body-to-wick ratio near the OB — strong bodies mean conviction, long wicks mean indecision

The JSON data remains your primary source for exact prices and structural analysis. The chart provides visual context that numbers cannot fully capture. If the chart reveals weakness not apparent in the JSON (messy OB, weak rejection, choppy structure), adjust your confidence score and grade downward accordingly.

"""


def build_batch_requests(prompts: list[dict]) -> list[Request]:
    """Convert collected prompts into Batch API request objects.

    If a prompt has ``chart_b64``, the user message becomes multimodal
    (image + text) for vision-enhanced analysis.
    """
    requests = []
    for p in prompts:
        pr = p["prompt"]
        chart_b64 = p.get("chart_b64")

        if chart_b64:
            user_content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": chart_b64,
                    },
                },
                {
                    "type": "text",
                    "text": _VISION_PREAMBLE + pr["user_message"],
                },
            ]
        else:
            user_content = pr["user_message"]

        requests.append(
            Request(
                custom_id=p["custom_id"],
                params=MessageCreateParamsNonStreaming(
                    model=pr["model"],
                    max_tokens=pr["max_tokens"],
                    temperature=pr["temperature"],
                    system=pr["system"],
                    messages=[{"role": "user", "content": user_content}],
                ),
            )
        )
    return requests


def submit_batch(requests: list[Request]) -> str:
    """Submit batch and return batch_id."""
    client = Anthropic()
    logger.info("Submitting batch with %d requests...", len(requests))
    batch = client.messages.batches.create(requests=requests)
    logger.info("Batch submitted: %s (status: %s)", batch.id, batch.processing_status)
    return batch.id


# ═══════════════════════════════════════════════════════════════════════
# Phase 3: WAIT — Poll until completion
# ═══════════════════════════════════════════════════════════════════════

def wait_for_batch(batch_id: str, poll_interval: int = 60) -> dict:
    """Poll batch status until ended. Returns final batch object as dict."""
    client = Anthropic()
    logger.info("Waiting for batch %s ...", batch_id)

    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        total = counts.processing + counts.succeeded + counts.errored + counts.canceled + counts.expired
        done = counts.succeeded + counts.errored + counts.canceled + counts.expired

        logger.info(
            "  Status: %s | %d/%d done (succeeded=%d, errored=%d, expired=%d)",
            batch.processing_status, done, total,
            counts.succeeded, counts.errored, counts.expired,
        )

        if batch.processing_status == "ended":
            return {
                "id": batch.id,
                "status": batch.processing_status,
                "succeeded": counts.succeeded,
                "errored": counts.errored,
                "expired": counts.expired,
                "canceled": counts.canceled,
            }

        time.sleep(poll_interval)


# ═══════════════════════════════════════════════════════════════════════
# Phase 4: PROCESS — Download and process results
# ═══════════════════════════════════════════════════════════════════════

def download_results(batch_id: str) -> dict[str, dict]:
    """Download batch results, save to disk, return {custom_id: result_data}.

    Saves raw results to batch_api/{batch_id}_raw_results.json so they
    can be re-processed without re-downloading from Anthropic.
    """
    # Check for cached download first
    cache_file = BATCH_STATE_DIR / f"{batch_id}_raw_results.json"
    if cache_file.exists():
        logger.info("Loading cached results from %s", cache_file)
        return json.loads(cache_file.read_text())

    client = Anthropic()
    results = {}
    succeeded = 0
    errored = 0

    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        rtype = result.result.type

        if rtype == "succeeded":
            msg = result.result.message
            text = msg.content[0].text if msg.content else ""
            usage = msg.usage
            results[cid] = {
                "text": text,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_read": getattr(usage, "cache_read_input_tokens", 0) or 0,
                "cache_create": getattr(usage, "cache_creation_input_tokens", 0) or 0,
                "status": "succeeded",
            }
            succeeded += 1
        else:
            error_msg = ""
            if rtype == "errored" and hasattr(result.result, "error"):
                error_msg = str(result.result.error)
            results[cid] = {"status": rtype, "error": error_msg}
            errored += 1

    logger.info("Downloaded %d results (%d succeeded, %d failed)", len(results), succeeded, errored)

    # Cache to disk for re-processing
    BATCH_STATE_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write(cache_file, results)
    logger.info("Raw results cached to %s", cache_file)

    return results


def process_results(
    prompts: list[dict],
    results: dict[str, dict],
    config: dict,
    all_candles: dict[str, list[dict]],
    output_dir: Path = BACKTEST_KB_DIR,
) -> list[dict]:
    """Process batch results: parse JSON, apply safety checks, evaluate outcomes.

    Writes per-session manifest files and raw PA responses to disk,
    matching the format used by the sequential runner.

    Returns list of per-session result summaries.
    """
    # Group prompts by date, then by kill_zone within each date
    by_date: dict[str, list[dict]] = {}
    for p in prompts:
        by_date.setdefault(p["date"], []).append(p)

    # Sort candles within each date chronologically
    for dlist in by_date.values():
        dlist.sort(key=lambda x: x["candle_time"])

    # Ensure output directories exist (instrument-scoped to prevent overwrites)
    import src.utils.file_io as fio
    fio.KNOWLEDGE_BASE_DIR = output_dir
    symbol = config.get("market", {}).get("symbol", "XAUUSD")
    sessions_dir = output_dir / "sessions" / symbol
    sessions_dir.mkdir(parents=True, exist_ok=True)
    responses_dir = output_dir / "batch_api" / "responses" / symbol
    responses_dir.mkdir(parents=True, exist_ok=True)

    kb = KnowledgeBase(base_path=str(output_dir))
    kb.initialize_rules()

    batch_results = []
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_create = 0

    for date_str in sorted(by_date.keys()):
        candle_prompts = by_date[date_str]
        target_date = date.fromisoformat(date_str)

        # Group candles by kill zone (generic — supports any number of KZ windows)
        kz_names = list(dict.fromkeys(cp.get("kill_zone", "london") for cp in candle_prompts))
        ordered_prompts = []
        for kz_name in kz_names:
            ordered_prompts.extend(
                cp for cp in candle_prompts if cp.get("kill_zone", "london") == kz_name
            )

        # Per-window state: max ONE trade per window
        trade_taken = set()  # set of kz names where a trade was already taken
        best_candidates = {}  # kill_zone -> {"candle_time": ..., "pa": ...}
        candle_evaluations = []
        session_raw_responses = {}

        for cp in ordered_prompts:
            cid = cp["custom_id"]
            candle_time = cp["candle_time"]
            kz = cp.get("kill_zone", "london")
            r = results.get(cid)

            # Check per-window trade limit
            if kz in trade_taken:
                candle_evaluations.append({
                    "candle_time": candle_time,
                    "kill_zone": kz,
                    "decision": "SKIP",
                    "reason": f"trade_already_taken_{kz}",
                    "confidence": None,
                    "setup_grade": None,
                    "framework": None,
                    "debate_triggered": None,
                    "debate_verdict": None,
                    "trade_executed": None,
                    "trade_id": None,
                })
                continue

            if not r or r.get("status") != "succeeded":
                candle_evaluations.append({
                    "candle_time": candle_time,
                    "kill_zone": kz,
                    "decision": "ERROR",
                    "reason": r.get("error", "batch_request_failed") if r else "no_result",
                    "confidence": None,
                    "setup_grade": None,
                    "framework": None,
                    "debate_triggered": None,
                    "debate_verdict": None,
                    "trade_executed": None,
                    "trade_id": None,
                })
                continue

            raw_text = r["text"]
            total_input += r.get("input_tokens", 0)
            total_output += r.get("output_tokens", 0)
            total_cache_read += r.get("cache_read", 0)
            total_cache_create += r.get("cache_create", 0)

            # Parse PA response
            try:
                cleaned = strip_json_fences(raw_text)
                data = json.loads(cleaned)
                _normalize_pa_fields(data)
                pa = PrimaryAnalysisOutput.model_validate(data)
            except Exception as exc:
                logger.warning("Failed to parse response for %s: %s", cid, exc)
                candle_evaluations.append({
                    "candle_time": candle_time,
                    "kill_zone": kz,
                    "decision": "NO_TRADE",
                    "reason": f"parse_error: {exc}",
                    "confidence": None,
                    "setup_grade": None,
                    "framework": None,
                    "debate_triggered": None,
                    "debate_verdict": None,
                    "trade_executed": None,
                    "trade_id": None,
                })
                continue

            # Save raw PA response
            session_raw_responses[cid] = data

            # Compute empirical confidence metrics
            conf = score_confidence(pa.model_dump())

            eval_entry = {
                "candle_time": candle_time,
                "kill_zone": kz,
                "decision": pa.decision,
                "reason": pa.no_trade_reason or pa.wait_reason,
                "confidence": pa.confidence_score,
                "confidence_grade": conf.confidence_grade,
                "confidence_price_levels": conf.price_level_count,
                "confidence_hesitation": conf.hesitation_score,
                "setup_grade": pa.reasoning.setup_grade if pa.reasoning else None,
                "framework": pa.framework,
                "debate_triggered": None,
                "debate_verdict": None,
                "trade_executed": None,
                "trade_id": None,
            }

            if pa.decision == "CANDIDATE":
                eval_entry["debate_triggered"] = False
                # Reconstruct MSO for safety checks using generic replay_kill_zone
                try:
                    kz_cfg = config.get("market", {}).get("kill_zones", {})
                    kz_times = kz_cfg.get(kz, {})
                    kz_start = kz_times.get("start_utc", "07:00")
                    kz_end = kz_times.get("end_utc", "09:30")
                    raw_data_gen = replay_kill_zone(
                        cp["date"], all_candles,
                        kz_start=kz_start, kz_end=kz_end,
                    )
                    mso = None
                    for rd in raw_data_gen:
                        if rd["timestamp_utc"] == cp["candle_time"]:
                            mso = compute_market_state(rd, config)
                            break
                    if mso is None:
                        eval_entry["decision"] = "NO_TRADE"
                        eval_entry["reason"] = "mso_reconstruction_failed"
                        candle_evaluations.append(eval_entry)
                        continue
                except Exception:
                    eval_entry["decision"] = "NO_TRADE"
                    eval_entry["reason"] = "mso_reconstruction_failed"
                    candle_evaluations.append(eval_entry)
                    continue

                # Safety checks
                reject = _safety_check(pa, mso, config)
                trade_seq = sum(1 for bc in best_candidates.values() if bc is not None)
                trade_id = f"bt_{date_str}_{kz}_{trade_seq + 1:03d}"
                if reject:
                    eval_entry["debate_verdict"] = "SAFETY_REJECT"
                    eval_entry["reason"] = reject
                    logger.info("[%s] Safety rejected: %s", cid, reject)
                else:
                    eval_entry["debate_verdict"] = "AUTO_APPROVED"
                    eval_entry["trade_executed"] = True
                    eval_entry["trade_id"] = trade_id
                    trade_taken.add(kz)
                    best_candidates[kz] = {"candle_time": candle_time, "pa": pa}

            candle_evaluations.append(eval_entry)

        # Evaluate outcomes for ALL trades taken (up to 2 per day)
        trades_summary = []
        for kz, bc in best_candidates.items():
            if bc and bc["pa"].trade_parameters:
                tp = bc["pa"].trade_parameters
                trade_seq = len(trades_summary) + 1
                trade_id = f"bt_{date_str}_{kz}_{trade_seq:03d}"
                m15 = all_candles.get("M15", [])
                future = [
                    c for c in m15
                    if c["time"] > bc["candle_time"]
                    and c["time"].startswith(date_str)
                ]
                # Trade parameter fields (entry/SL/TP/direction)
                sl_dist = abs(tp.entry_price - tp.stop_loss) if tp.entry_price and tp.stop_loss else None
                rr = tp.risk_reward_ratio if hasattr(tp, "risk_reward_ratio") else None
                trade_params = {
                    "entry_price": tp.entry_price,
                    "stop_loss": tp.stop_loss,
                    "take_profit_1": tp.take_profit_1,
                    "direction": tp.direction,
                    "sl_distance": round(sl_dist, 5) if sl_dist is not None else None,
                    "rr_ratio": rr,
                }

                if future:
                    outcome_data = evaluate_hypothetical_outcome(tp, future)
                    trades_summary.append({
                        "trade_id": trade_id,
                        "kill_zone": kz,
                        "outcome": outcome_data["outcome"],
                        "r_multiple": outcome_data["r_multiple"],
                        "framework": bc["pa"].framework,
                        "exit_substate": outcome_data.get("exit_substate"),
                        "mfe_r": outcome_data.get("mfe_r"),
                        "mae_r": outcome_data.get("mae_r"),
                        "hold_time_candles": outcome_data.get("hold_time_candles"),
                        **trade_params,
                    })
                else:
                    trades_summary.append({
                        "trade_id": trade_id,
                        "kill_zone": kz,
                        "outcome": None,
                        "r_multiple": None,
                        "framework": bc["pa"].framework,
                        "exit_substate": None,
                        "mfe_r": None,
                        "mae_r": None,
                        "hold_time_candles": None,
                        **trade_params,
                    })

        any_trade = len(trades_summary) > 0

        # ── Write session manifest (dual kill zone format) ──
        manifest = {
            "date": date_str,
            "day_of_week": target_date.strftime("%A"),
            "session_start_utc": f"{date_str}T{config.get('market', {}).get('kill_zones', {}).get('london', {}).get('start_utc', '07:00')}:00Z",
            "session_end_utc": f"{date_str}T{config.get('market', {}).get('kill_zones', {}).get('ny', {}).get('end_utc', '15:30')}:00Z",
            "pre_session": None,
            "candle_evaluations": candle_evaluations,
            "trade_summary": {
                "trade_taken": any_trade,
                "trades": trades_summary,
                # Backward-compat fields (first trade if any)
                "trade_id": trades_summary[0]["trade_id"] if trades_summary else None,
                "outcome": trades_summary[0]["outcome"] if trades_summary else None,
                "r_multiple": trades_summary[0]["r_multiple"] if trades_summary else None,
            },
            "errors": [],
            "api_calls_count": len([e for e in candle_evaluations if e["decision"] != "SKIP"]),
            "api_cost_estimate_usd": 0,
        }

        session_file = sessions_dir / f"{date_str}_session.json"
        atomic_write(session_file, manifest)

        # ── Write raw PA responses per session ──
        if session_raw_responses:
            resp_file = responses_dir / f"{date_str}_responses.json"
            atomic_write(resp_file, session_raw_responses)

        # Collect decisions list for summary
        decisions = [e["decision"] for e in candle_evaluations]

        batch_results.append({
            "date": date_str,
            "trade_taken": any_trade,
            "trades": trades_summary,
            "outcome": trades_summary[0]["outcome"] if trades_summary else None,
            "r_multiple": trades_summary[0]["r_multiple"] if trades_summary else None,
            "api_calls": manifest["api_calls_count"],
            "cost_usd": 0,
            "errors": sum(1 for d in decisions if d == "ERROR"),
            "decisions": decisions,
        })

    # Calculate batch cost
    batch_cost = (
        total_input * _BATCH_INPUT_PER_MTOK / 1_000_000
        + total_output * _BATCH_OUTPUT_PER_MTOK / 1_000_000
        + total_cache_read * _BATCH_CACHE_READ_PER_MTOK / 1_000_000
        + total_cache_create * _BATCH_CACHE_WRITE_PER_MTOK / 1_000_000
    )

    logger.info(
        "Processed %d sessions | Tokens: %d in / %d out / %d cache_read / %d cache_create | Cost: $%.4f",
        len(batch_results), total_input, total_output, total_cache_read, total_cache_create, batch_cost,
    )
    logger.info("Session files written to %s", sessions_dir)
    logger.info("Raw PA responses written to %s", responses_dir)

    return batch_results, batch_cost


def _safety_check(pa: PrimaryAnalysisOutput, mso, config: dict = None) -> Optional[str]:
    """Deterministic safety checks — mirrors BacktestRunner._safety_check()."""
    if config is None:
        config = {}

    grade = pa.reasoning.setup_grade if pa.reasoning else "C"
    if grade not in ("A+", "A"):
        return f"below_grade_threshold: {grade}"

    tp = pa.trade_parameters
    if not tp:
        return "no_trade_parameters"

    daily_dir = pa.reasoning.daily_bias.direction if pa.reasoning else "ranging"
    if daily_dir == "bullish" and tp.direction == "SHORT":
        return "direction_mismatch: SHORT against bullish daily bias"
    if daily_dir == "bearish" and tp.direction == "LONG":
        return "direction_mismatch: LONG against bearish daily bias"

    # RR check — read threshold from config (default 1.5)
    min_rr = config.get("risk", {}).get("min_rr", 1.5)
    if tp.risk_reward_ratio < (min_rr - 0.1):
        return f"rr_too_low: {tp.risk_reward_ratio:.1f} < {min_rr - 0.1:.1f}"

    sl_distance = abs(tp.entry_price - tp.stop_loss)

    # Minimum SL floor — instrument-specific (default $5 for gold)
    sl_floor = config.get("risk", {}).get("sl_absolute_min", 5.0)
    if sl_distance < sl_floor:
        return f"sl_below_minimum_floor: SL_dist={sl_distance:.4f} < {sl_floor}"

    m15_tf = mso.timeframes.get("M15") if hasattr(mso, "timeframes") else None
    m15_atr = getattr(m15_tf, "atr_14", 0) or 0 if m15_tf else 0
    if m15_atr > 0 and sl_distance < m15_atr * 1.5:
        return f"sl_too_tight: SL_dist={sl_distance:.5f} < 1.5*ATR={m15_atr * 1.5:.5f}"

    return None


# ═══════════════════════════════════════════════════════════════════════
# Phase 5: REPORT
# ═══════════════════════════════════════════════════════════════════════

def generate_report(batch_results: list[dict], batch_cost: float = 0) -> str:
    """Generate batch report (dual kill zone format)."""
    total_sessions = len(batch_results)
    if total_sessions == 0:
        return "No sessions processed."

    # Flatten all individual trades from all sessions
    all_trades = []
    for r in batch_results:
        for t in r.get("trades", []):
            all_trades.append(t)
        # Backward compat: if no "trades" key, use top-level outcome
        if not r.get("trades") and r.get("trade_taken"):
            all_trades.append({
                "outcome": r.get("outcome"),
                "r_multiple": r.get("r_multiple"),
                "kill_zone": "london",
            })

    num_trades = len(all_trades)
    wins = [t for t in all_trades if t.get("outcome") == "WIN"]
    losses = [t for t in all_trades if t.get("outcome") == "LOSS"]
    breakevens = [t for t in all_trades if t.get("outcome") == "BREAKEVEN"]
    win_rate = len(wins) / num_trades if num_trades else 0

    winner_rs = [t["r_multiple"] for t in wins if t.get("r_multiple") is not None]
    loser_rs = [t["r_multiple"] for t in losses if t.get("r_multiple") is not None]
    all_rs = [t["r_multiple"] for t in all_trades if t.get("r_multiple") is not None]

    total_r = sum(all_rs)
    expectancy = total_r / num_trades if num_trades else 0
    avg_winner = sum(winner_rs) / len(winner_rs) if winner_rs else 0
    avg_loser = sum(abs(r) for r in loser_rs) / len(loser_rs) if loser_rs else 0

    # Per-window breakdown
    london_trades = [t for t in all_trades if t.get("kill_zone") == "london"]
    ny_trades = [t for t in all_trades if t.get("kill_zone") == "ny"]

    # Per-framework breakdown
    frameworks: dict[str, list[dict]] = {}
    for t in all_trades:
        fw = t.get("framework", "unknown") or "unknown"
        frameworks.setdefault(fw, []).append(t)

    all_decisions = []
    for r in batch_results:
        all_decisions.extend(r.get("decisions", []))
    cand_count = sum(1 for d in all_decisions if d == "CANDIDATE")
    no_trade_count = sum(1 for d in all_decisions if d == "NO_TRADE")
    total_calls = sum(r.get("api_calls", 0) for r in batch_results)

    sessions_with_trade = sum(1 for r in batch_results if r.get("trade_taken"))

    lines = [
        "=" * 72,
        "BATCH BACKTEST REPORT (DUAL KILL ZONE)",
        "=" * 72,
        f"  Billing mode:             Batch API (50% discount)",
        "",
        "── Overview ──────────────────────────────────────────────",
        f"  Total sessions (days):    {total_sessions}",
        f"  Days with trades:         {sessions_with_trade}",
        f"  Total trades:             {num_trades}  (London: {len(london_trades)}, NY: {len(ny_trades)})",
        f"  Trade frequency:          {num_trades/total_sessions*100:.1f}% (trades/session)",
        "",
        "── Trade Outcomes ────────────────────────────────────────",
        f"  Wins:                     {len(wins)}",
        f"  Losses:                   {len(losses)}",
        f"  Breakeven:                {len(breakevens)}",
        f"  Win rate:                 {win_rate*100:.1f}%",
        "",
        "── R-Multiple Analysis ───────────────────────────────────",
        f"  Total R:                  {total_r:+.2f}R",
        f"  Avg winner:               {avg_winner:.2f}R",
        f"  Avg loser:                {avg_loser:.2f}R",
        f"  Expectancy:               {expectancy:.2f}R per trade",
        "",
        "── Per-Framework Breakdown ───────────────────────────────",
    ]

    for fw, fw_trades in sorted(frameworks.items()):
        fw_wins = [t for t in fw_trades if t.get("outcome") == "WIN"]
        fw_losses = [t for t in fw_trades if t.get("outcome") == "LOSS"]
        fw_rs = [t["r_multiple"] for t in fw_trades if t.get("r_multiple") is not None]
        fw_wr = len(fw_wins) / len(fw_trades) if fw_trades else 0
        fw_exp = sum(fw_rs) / len(fw_trades) if fw_trades else 0
        lines.append(f"  {fw}: {len(fw_trades)} trades, WR={fw_wr*100:.0f}%, "
                     f"W={len(fw_wins)} L={len(fw_losses)}, "
                     f"Exp={fw_exp:.2f}R, Total={sum(fw_rs):.2f}R")

    lines += [
        "",
        "── Candle Decision Breakdown ─────────────────────────────",
        f"  Total candles submitted:  {len(all_decisions)}",
        f"  CANDIDATE:                {cand_count}",
        f"  NO_TRADE:                 {no_trade_count}",
        "",
        "── Batch API Cost ────────────────────────────────────────",
        f"  Total LLM calls:          {total_calls}",
        f"  Batch cost (50% off):     ${batch_cost:.4f}",
        f"  Cost per session:         ${batch_cost/total_sessions:.4f}" if total_sessions else "",
        f"  vs sequential API est:    ~${batch_cost * 2:.4f} (2x batch)",
        "",
        "=" * 72,
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# Cost estimation
# ═══════════════════════════════════════════════════════════════════════

def estimate_cost(prompts: list[dict]) -> dict:
    """Estimate batch cost from prompt lengths.

    Calibrated against May 2025 batch actuals:
    - 1 token ≈ 3.5 chars (system prompt is dense)
    - ~800 output tokens per response (multi-framework evaluation)
    """
    total_input_chars = 0
    total_system_chars = 0
    for p in prompts:
        pr = p["prompt"]
        # System blocks
        sys_text = ""
        for block in pr["system"]:
            if isinstance(block, dict):
                sys_text += block.get("text", "")
        total_system_chars += len(sys_text)
        total_input_chars += len(sys_text) + len(pr["user_message"])

    est_input_tokens = total_input_chars / 3.5
    est_output_tokens = len(prompts) * 800  # ~800 output tokens per response (calibrated May 2025)

    # Assume ~50% cache hit rate for system prompts within same session
    unique_sessions = len(set(p["date"] for p in prompts))
    est_cache_create = unique_sessions * (total_system_chars / len(prompts) / 4) if prompts else 0
    est_cache_read = est_input_tokens * 0.5

    batch_cost = (
        est_input_tokens * 0.5 * _BATCH_INPUT_PER_MTOK / 1_000_000  # non-cached half
        + est_output_tokens * _BATCH_OUTPUT_PER_MTOK / 1_000_000
        + est_cache_create * _BATCH_CACHE_WRITE_PER_MTOK / 1_000_000
        + est_cache_read * _BATCH_CACHE_READ_PER_MTOK / 1_000_000
    )

    sequential_cost = (
        est_input_tokens * _COST_PER_INPUT_TOKEN
        + est_output_tokens * _COST_PER_OUTPUT_TOKEN
    )

    return {
        "total_prompts": len(prompts),
        "unique_sessions": unique_sessions,
        "est_input_tokens": int(est_input_tokens),
        "est_output_tokens": int(est_output_tokens),
        "est_batch_cost": round(batch_cost, 4),
        "est_sequential_cost": round(sequential_cost, 4),
        "savings_pct": round((1 - batch_cost / sequential_cost) * 100, 1) if sequential_cost > 0 else 0,
    }


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch backtesting via Anthropic Message Batches API.",
    )
    parser.add_argument("--start", type=str, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, help="End date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build prompts and estimate cost — don't submit")
    parser.add_argument("--resume-batch", type=str, default=None,
                        help="Resume processing a previously submitted batch ID")
    parser.add_argument("--no-prescreen", action="store_true",
                        help="Disable pre-screening — submit all candles (existing behavior)")
    parser.add_argument("--vision", action="store_true",
                        help="Include rendered M15 chart images in API calls")
    parser.add_argument("--symbol", type=str, default=None,
                        help="Override instrument symbol (loads instrument-specific config)")
    parser.add_argument("--dates", type=str, default=None,
                        help="Comma-separated dates or path to a file with one date per line")
    parser.add_argument("--config", type=str, default="config/agent_config.yaml")
    parser.add_argument("--output-dir", type=str, default="knowledge_base_backtest")

    args = parser.parse_args()

    with open(_PROJECT_ROOT / args.config) as fh:
        config = yaml.safe_load(fh)

    # Apply instrument overrides if --symbol provided
    from src.utils.config import apply_instrument_overrides
    if args.symbol:
        config = apply_instrument_overrides(config, args.symbol)
    else:
        config = apply_instrument_overrides(config)  # strips instruments section

    # Load historical candle data
    symbol = config["market"]["symbol"]
    all_candles: dict[str, list[dict]] = {}
    for tf in ("D1", "H4", "H1", "M15"):
        csv_path = HISTORICAL_DIR / f"{symbol}_{tf}.csv"
        if csv_path.exists():
            all_candles[tf] = parse_tradingview_csv(csv_path)
        else:
            logger.warning("No CSV for %s", tf)
            all_candles[tf] = []

    # Load reference instrument data for cross-instrument context
    ref_candles: dict[str, list[dict]] | None = None
    ci_cfg = config.get("cross_instrument_context", {})
    if ci_cfg.get("enabled"):
        ref_symbol = ci_cfg.get("reference_instrument", "XAUUSD")
        ref_tf = ci_cfg.get("reference_timeframe", "D1")
        ref_csv = HISTORICAL_DIR / f"{ref_symbol}_{ref_tf}.csv"
        if ref_csv.exists():
            ref_candles = {ref_tf: parse_tradingview_csv(ref_csv)}
            logger.info("Loaded %s %s reference data (%d candles) for cross-instrument context",
                        ref_symbol, ref_tf, len(ref_candles[ref_tf]))
        else:
            logger.warning("Cross-instrument enabled but %s not found — skipping", ref_csv)

    BATCH_STATE_DIR.mkdir(parents=True, exist_ok=True)

    # ── Resume mode ──────────────────────────────────────────────────
    if args.resume_batch:
        logger.info("Resuming batch: %s", args.resume_batch)

        # Load saved prompts (prefer full prompts, fall back to metadata)
        full_prompts_file = BATCH_STATE_DIR / f"{args.resume_batch}_full_prompts.json"
        prompts_file = BATCH_STATE_DIR / f"{args.resume_batch}_prompts.json"
        if full_prompts_file.exists():
            prompts = json.loads(full_prompts_file.read_text())
            logger.info("Loaded %d prompts from full prompts file", len(prompts))
        elif prompts_file.exists():
            prompts = json.loads(prompts_file.read_text())
            logger.info("Loaded %d prompts from metadata file", len(prompts))
        else:
            logger.error("No saved prompts for batch %s", args.resume_batch)
            sys.exit(1)

        # Phase 3: Wait (skip if already ended)
        batch_info = wait_for_batch(args.resume_batch)
        logger.info("Batch completed: %s", json.dumps(batch_info))

        # Phase 4: Process
        results = download_results(args.resume_batch)
        batch_results, batch_cost = process_results(prompts, results, config, all_candles)

        # Phase 5: Report
        report = generate_report(batch_results, batch_cost=batch_cost)
        print(report)

        # Save
        out_path = BATCH_STATE_DIR / f"{args.resume_batch}_results.json"
        atomic_write(out_path, batch_results)
        report_path = BATCH_STATE_DIR / f"{args.resume_batch}_report.txt"
        report_path.write_text(report)
        logger.info("Results saved to %s", out_path)
        return

    # ── Parse --dates if provided ─────────────────────────────────────
    target_dates: list[str] | None = None
    if args.dates:
        dates_path = Path(args.dates)
        if dates_path.exists():
            target_dates = [
                line.strip() for line in dates_path.read_text().splitlines()
                if line.strip() and not line.startswith("#")
            ]
            logger.info("Loaded %d dates from %s", len(target_dates), dates_path)
        else:
            target_dates = [d.strip() for d in args.dates.split(",") if d.strip()]
            logger.info("Parsed %d dates from --dates argument", len(target_dates))

    # ── Normal mode — needs start/end or --dates ──────────────────────
    if not target_dates and (not args.start or not args.end):
        parser.error("--start and --end are required (unless using --resume-batch or --dates)")

    # Phase 1: Collect
    do_prescreen = not args.no_prescreen
    use_vision = getattr(args, "vision", False)
    start_label = target_dates[0] if target_dates else args.start
    end_label = target_dates[-1] if target_dates else args.end
    logger.info("Phase 1: Collecting prompts for %s → %s (prescreen=%s, vision=%s, dates=%s) ...",
                start_label, end_label, do_prescreen, use_vision,
                f"{len(target_dates)} specific" if target_dates else "range")
    prompts, ps_stats = collect_prompts(
        args.start or start_label, args.end or end_label, config, all_candles,
        prescreen=do_prescreen, vision=use_vision,
        ref_candles=ref_candles,
        target_dates=target_dates,
    )

    if not prompts:
        logger.error("No prompts collected — no M15 data in date range (or all dates pre-screened out).")
        sys.exit(1)

    # Cost estimate
    cost_est = estimate_cost(prompts)

    london_count = sum(1 for p in prompts if p.get("kill_zone") == "london")
    ny_count = sum(1 for p in prompts if p.get("kill_zone") == "ny")

    total_possible = ps_stats["total_dates"]
    total_without_prescreen = (total_possible - ps_stats["no_data"]) * 20  # ~20 candles/session

    print()
    print("=" * 60)
    print("  BATCH BACKTEST — DRY RUN SUMMARY (DUAL KILL ZONE)")
    print("=" * 60)
    print(f"  Date range:          {start_label} → {end_label}")
    print(f"  Sessions with data:  {cost_est['unique_sessions']}")
    print(f"  Total candles:       {cost_est['total_prompts']}  (London: {london_count}, NY: {ny_count})")
    print(f"  Est. input tokens:   {cost_est['est_input_tokens']:,}")
    print(f"  Est. output tokens:  {cost_est['est_output_tokens']:,}")
    print()
    print(f"  Est. BATCH cost:     ${cost_est['est_batch_cost']:.4f}  (50% off)")
    print(f"  Est. sequential:     ${cost_est['est_sequential_cost']:.4f}  (full price)")
    print(f"  Savings:             {cost_est['savings_pct']:.0f}%")

    if ps_stats["prescreen_enabled"]:
        print()
        print("── Pre-screen Results ────────────────────────────────────")
        print(f"  Total weekdays:                {total_possible}")
        print(f"  No M15 data:                   {ps_stats['no_data']}")
        print(f"  Layer 1 — D1+H4 both unclear:  {ps_stats['l1_skip']} dates skipped")
        print(f"  Layer 2 — H4 conflicts w/ D1:  {ps_stats['l2_skip']} dates skipped")
        print(f"  Passed both layers:            {ps_stats['passed']} dates → {cost_est['total_prompts']} candles")
        if total_without_prescreen > 0:
            saved_pct = (1 - cost_est["total_prompts"] / total_without_prescreen) * 100
            print(f"  vs without pre-screen:         ~{total_without_prescreen} candles")
            print(f"  Estimated savings:             {saved_pct:.0f}%")
    else:
        print()
        print("  Pre-screening: DISABLED (--no-prescreen)")
    print("=" * 60)
    print()

    if args.dry_run:
        # Save prompts summary (not full prompts — those are huge)
        dry_run_path = BATCH_STATE_DIR / "dry_run_summary.json"
        summary = {
            "start": args.start,
            "end": args.end,
            "cost_estimate": cost_est,
            "candle_ids": [p["custom_id"] for p in prompts],
        }
        BATCH_STATE_DIR.mkdir(parents=True, exist_ok=True)
        atomic_write(dry_run_path, summary)

        # Print one example
        example = prompts[0]
        sys_text = ""
        for block in example["prompt"]["system"]:
            if isinstance(block, dict):
                sys_text = block.get("text", "")[:200]
        print(f"  Example request (first candle):")
        print(f"    custom_id: {example['custom_id']}")
        print(f"    model:     {example['prompt']['model']}")
        print(f"    system:    {len(sys_text)}... chars")
        print(f"    user_msg:  {len(example['prompt']['user_message'])} chars")
        print()
        print(f"  Dry-run complete. Review above, then re-run without --dry-run to submit.")
        return

    # Phase 2: Submit
    print("Submitting batch to Anthropic...")
    batch_requests = build_batch_requests(prompts)
    batch_id = submit_batch(batch_requests)

    # Save prompts for resume
    prompts_file = BATCH_STATE_DIR / f"{batch_id}_prompts.json"
    # Save without full system prompt text to avoid huge files
    prompts_meta = [
        {"custom_id": p["custom_id"], "date": p["date"], "candle_time": p["candle_time"]}
        for p in prompts
    ]
    atomic_write(prompts_file, prompts_meta)
    # Also save full prompts for result processing
    full_prompts_file = BATCH_STATE_DIR / f"{batch_id}_full_prompts.json"
    atomic_write(full_prompts_file, prompts)
    logger.info("Batch ID: %s — saved to %s", batch_id, BATCH_STATE_DIR)

    # Phase 3: Wait
    batch_info = wait_for_batch(batch_id)
    logger.info("Batch completed: %s", json.dumps(batch_info))

    # Phase 4: Process
    results = download_results(batch_id)
    batch_results, batch_cost = process_results(prompts, results, config, all_candles)

    # Phase 5: Report
    report = generate_report(batch_results, batch_cost=batch_cost)
    print(report)

    out_path = BATCH_STATE_DIR / f"{batch_id}_results.json"
    atomic_write(out_path, batch_results)
    report_path = BATCH_STATE_DIR / f"{batch_id}_report.txt"
    report_path.write_text(report)
    logger.info("Results saved to %s", out_path)


if __name__ == "__main__":
    main()
