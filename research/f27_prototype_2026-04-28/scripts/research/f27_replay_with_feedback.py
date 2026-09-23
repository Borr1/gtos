#!/usr/bin/env python
"""F27 — Backward outcome injection prototype.

A/B replay:
- BASELINE: current production prompt (post-HALLUC-1 + S79 + 4 sister fixes).
- TREATMENT: identical, but with a "## Recent trade outcomes" prose-summary
  block (last 10 closed trades from `trades_unified.csv`) injected via the
  existing `additional_context` parameter of `build_user_message()`.

Cohort: A4 trending_bull XAUUSD (n=11) — see F27_PROTOTYPE_DESIGN.md.

Production fidelity (model/effort/timeout/cache/temperature/max_tokens) mirrors
A4's `a4_trending_bull_replay.py` exactly. The ONLY semantic difference between
baseline and treatment is the `additional_context` block.

Usage:
  # Baseline
  python scripts/research/f27_replay_with_feedback.py \\
      --cohort-csv research/a4_trending_bull_replay_2026-04-28/a4_cohort_manifest.csv \\
      --past-trades-csv research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv \\
      --out-dir research/f27_prototype_2026-04-28 \\
      --mode baseline \\
      --concurrency 10

  # Treatment
  python scripts/research/f27_replay_with_feedback.py \\
      --cohort-csv research/a4_trending_bull_replay_2026-04-28/a4_cohort_manifest.csv \\
      --past-trades-csv research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv \\
      --out-dir research/f27_prototype_2026-04-28 \\
      --mode treatment \\
      --concurrency 10
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Optional dotenv — research scripts don't auto-load .env
try:
    from dotenv import load_dotenv  # type: ignore[import-not-found]
    load_dotenv()
except Exception:
    pass

try:
    import anthropic  # type: ignore[import-not-found]
    _HAS_ANTHROPIC = True
except Exception:
    _HAS_ANTHROPIC = False

# Make src.* importable. The worktree's `src/` is what we want — production code is
# identical between worktree (since the worktree was created off main HEAD).
# Script is at research/f27_.../scripts/research/<this>.py — parents[4] = repo root.
REPO_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT_ENV = os.environ.get("GTOS_REPO_ROOT")
SRC_ROOT = Path(_REPO_ROOT_ENV) if _REPO_ROOT_ENV else REPO_ROOT
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# ---------------------------------------------------------------------------
# Production-faithful constants (mirror A4 exactly)
# ---------------------------------------------------------------------------
PROD_MODEL = "claude-sonnet-4-6"
PROD_EFFORT = "max"
PROD_TIMEOUT_S = 90
PROD_MAX_TOKENS = 2000
PROD_TEMPERATURE = 0
PROD_CACHE_TTL = "1h"
PROD_PRICE_FMT = ".2f"

PRICE_INPUT_PER_M = 3.00
PRICE_OUTPUT_PER_M = 15.00
PRICE_CACHE_READ_PER_M = 0.30
PRICE_CACHE_WRITE_PER_M = 6.00


# ---------------------------------------------------------------------------
# Past-outcome telemetry (D2 prose-summary feedback block)
# ---------------------------------------------------------------------------

def load_past_trades(past_csv: Path) -> list[dict]:
    """Load enriched closed-trade history."""
    rows = []
    with open(past_csv, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "trade_id": r.get("trade_id", ""),
                "date": r["date"],
                "symbol": r["symbol"],
                "kill_zone": r.get("kill_zone", ""),
                "framework": r.get("framework", ""),
                "direction": r.get("direction", ""),
                "outcome": r.get("outcome", ""),
                "r_multiple": float(r["r_multiple"]) if r.get("r_multiple") else 0.0,
                "daily_bias": r.get("daily_bias", ""),
            })
    return rows


def select_last_n_before(past: list[dict], cutoff_iso: str, n: int = 10,
                          symbol: str | None = None) -> list[dict]:
    """Return last N closed trades with date < cutoff date.

    Filters by symbol if provided; otherwise returns ALL instruments (production
    AI sees a portfolio-wide signal, which is what F27 hypothesizes).
    """
    cutoff = datetime.fromisoformat(cutoff_iso.replace("Z", "+00:00")).date()
    eligible = [r for r in past
                if datetime.fromisoformat(r["date"]).date() < cutoff
                and (symbol is None or r["symbol"] == symbol)]
    eligible.sort(key=lambda r: r["date"])
    return eligible[-n:]


def format_d2_prose(past_trades: list[dict]) -> str:
    """Render the D2 prose-summary feedback block for the prompt.

    Format:
      ## Recent trade outcomes (most recent N closed; treat as historical signal,
      not session memory)
      In your last N closed trades, the system recorded W wins and L losses
      for a mean of +X.XXR per trade.
      - Recent wins: <enumeration>
      - Recent losses: <enumeration>
      Use this as a calibration signal on your decision-making, not as a
      substitute for evaluating this candle's MSO. The outcomes above are
      HISTORICAL telemetry from previously-closed trades, NOT the current
      session's reasoning context.
    """
    if not past_trades:
        return ""
    n = len(past_trades)
    wins = [t for t in past_trades if t["outcome"] == "WIN"]
    losses = [t for t in past_trades if t["outcome"] == "LOSS"]
    bes = [t for t in past_trades if t["outcome"] == "BREAKEVEN"]
    mean_r = sum(t["r_multiple"] for t in past_trades) / n

    def _fmt_one(t: dict) -> str:
        # e.g. "LONG ob_retest XAUUSD on 2026-03-09 (NY, bullish bias, R +0.23)"
        return (
            f"{t['direction']} {t['framework']} {t['symbol']} on {t['date']} "
            f"({t['kill_zone']}, {t['daily_bias']} bias, R "
            f"{t['r_multiple']:+.2f})"
        )

    win_lines = "; ".join(_fmt_one(t) for t in wins) or "none"
    loss_lines = "; ".join(_fmt_one(t) for t in losses) or "none"
    be_clause = f" and {len(bes)} breakeven" if bes else ""

    block = (
        f"## Recent trade outcomes (most recent {n} closed; treat as historical "
        f"signal, not session memory)\n"
        f"\n"
        f"In your last {n} closed trades, the system recorded {len(wins)} wins, "
        f"{len(losses)} losses{be_clause} for a mean of {mean_r:+.2f}R per trade.\n"
        f"- Recent wins: {win_lines}.\n"
        f"- Recent losses: {loss_lines}.\n"
        f"\n"
        f"Use this as a calibration signal on your decision-making, not as a "
        f"substitute for evaluating this candle's MSO. The outcomes above are "
        f"HISTORICAL telemetry from previously-closed trades, NOT the current "
        f"session's reasoning context.\n"
    )
    return block


# ---------------------------------------------------------------------------
# Data loading (mirrors A4)
# ---------------------------------------------------------------------------

@dataclass
class CohortRow:
    trade_id: str
    candle_time_utc: str
    kill_zone: str
    regime: str
    daily_bias_direction: str
    setup_grade: str
    framework: str
    ai_decision_original: str
    ai_direction_original: str
    mso_path: str


def load_cohort(cohort_csv: Path, limit: int | None) -> list[CohortRow]:
    rows = []
    with open(cohort_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("has_full_mso", "").lower() != "true":
                continue
            rows.append(CohortRow(
                trade_id=r["trade_id"],
                candle_time_utc=r["candle_time_utc"],
                kill_zone=r["kill_zone"],
                regime=r["regime"],
                daily_bias_direction=r.get("daily_bias_direction", ""),
                setup_grade=r.get("setup_grade", ""),
                framework=r.get("framework", ""),
                ai_decision_original=r.get("ai_decision_original", ""),
                ai_direction_original=r.get("ai_direction_original", ""),
                mso_path=r["mso_path"],
            ))
    if limit:
        rows = rows[:limit]
    return rows


def load_trade_record(mso_path: str) -> dict:
    return json.load(open(mso_path, encoding="utf-8"))


# ---------------------------------------------------------------------------
# Production-faithful prompt rebuild
# ---------------------------------------------------------------------------

_PROD_BUILDER = None
_PROD_CFG = None


def _load_production_builder():
    global _PROD_BUILDER, _PROD_CFG
    if _PROD_BUILDER is None:
        from src.prompts import primary_analyzer_prompt as builder
        import yaml
        cfg_path = SRC_ROOT / "config" / "agent_config.yaml"
        cfg = yaml.safe_load(open(cfg_path, encoding="utf-8"))
        builder.set_price_format(PROD_PRICE_FMT)
        _PROD_BUILDER = builder
        _PROD_CFG = cfg
    return _PROD_BUILDER, _PROD_CFG


def build_prompt_from_record(rec: dict, kill_zone: str, kb_context: dict | None,
                              additional_context: str = "") -> dict:
    """Rebuild the CURRENT production prompt; optionally inject F27 feedback.

    The F27 feedback block is passed via `additional_context`, which the
    production `build_user_message()` already supports (used in production
    for cross-instrument context blocks).
    """
    builder, cfg = _load_production_builder()
    from src.models.market_state_models import MarketStateObject

    mso_obj = MarketStateObject.model_validate(rec["mso"])

    sys_text = builder.build_system_prompt(cfg)
    static_ctx = builder.build_static_context(mso_obj)
    full_sys_text = sys_text + "\n\n## Static Context (D1/H4/Session)\n" + static_ctx

    if kb_context is None:
        kb_context = {"layer1": {}, "layer2": {}, "layer3": []}

    candle_time = rec.get("metadata", {}).get("candle_time") or rec["mso"].get("timestamp_utc")
    user_msg = builder.build_user_message(
        mso_obj,
        kb_context=kb_context,
        current_time=candle_time,
        kill_zone=kill_zone,
        session_memory="",
        cross_instrument_context="",
        additional_context=additional_context,
    )
    return {
        "system_text": full_sys_text,
        "user_message": user_msg,
        "candle_time": candle_time,
    }


def build_system_blocks(system_text: str) -> list[dict]:
    return [{
        "type": "text",
        "text": system_text,
        "cache_control": {"type": "ephemeral", "ttl": PROD_CACHE_TTL},
    }]


# ---------------------------------------------------------------------------
# API call (mirrors A4)
# ---------------------------------------------------------------------------

async def _call_one(
    client: "anthropic.AsyncAnthropic",
    sem: asyncio.Semaphore,
    row: CohortRow,
    rec: dict,
    out_dir: Path,
    raw_subdir: str,
    retry_log: Path,
    additional_context: str = "",
) -> dict:
    prompt = build_prompt_from_record(rec, row.kill_zone, kb_context=None,
                                       additional_context=additional_context)
    system_blocks = build_system_blocks(prompt["system_text"])
    user_message = prompt["user_message"]

    async with sem:
        last_err: Exception | None = None
        for attempt in range(3):
            t_start = time.monotonic()
            try:
                resp = await client.messages.create(
                    model=PROD_MODEL,
                    max_tokens=PROD_MAX_TOKENS,
                    temperature=PROD_TEMPERATURE,
                    system=system_blocks,
                    messages=[{"role": "user", "content": user_message}],
                    output_config={"effort": PROD_EFFORT},
                    timeout=PROD_TIMEOUT_S,
                )
                elapsed_ms = int((time.monotonic() - t_start) * 1000)
                resp_text = ""
                for block in resp.content:
                    if getattr(block, "type", None) == "text":
                        resp_text = block.text
                        break
                parsed = _extract_decision_fields(resp_text)
                u = resp.usage
                return {
                    "trade_id": row.trade_id,
                    "candle_time_utc": row.candle_time_utc,
                    "regime": row.regime,
                    "kill_zone": row.kill_zone,
                    "original": {
                        "ai_decision": row.ai_decision_original,
                        "ai_direction": row.ai_direction_original,
                        "ai_grade": row.setup_grade,
                        "ai_framework": row.framework,
                    },
                    "current": parsed,
                    "decision_flip": _classify_flip(
                        row.ai_decision_original, parsed.get("ai_decision"),
                    ),
                    "input_tokens": getattr(u, "input_tokens", 0),
                    "output_tokens": getattr(u, "output_tokens", 0),
                    "cache_read_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
                    "cache_creation_tokens": getattr(u, "cache_creation_input_tokens", 0) or 0,
                    "elapsed_ms": elapsed_ms,
                    "model": PROD_MODEL,
                    "effort": PROD_EFFORT,
                    "ts_replay_utc": datetime.now(timezone.utc).isoformat(),
                    "retries": attempt,
                    "raw_response_first_200_chars": resp_text[:200],
                    "raw_response_full_path": _persist_full_response(
                        out_dir, raw_subdir, row.trade_id, resp_text,
                    ),
                    "feedback_block_chars": len(additional_context),
                }
            except Exception as exc:
                last_err = exc
                _log_retry(retry_log, row.trade_id, attempt, str(exc))
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        raise RuntimeError(f"unreachable; last_err={last_err}")


def _persist_full_response(out_dir: Path, raw_subdir: str, trade_id: str, text: str) -> str:
    raw_dir = out_dir / raw_subdir
    raw_dir.mkdir(parents=True, exist_ok=True)
    p = raw_dir / f"{trade_id}.json"
    p.write_text(text, encoding="utf-8")
    return str(p.relative_to(out_dir))


def _classify_flip(orig: str | None, current: str | None) -> str:
    if not current:
        return f"{orig or 'unknown'}_to_NULL"
    if orig == "CANDIDATE":
        if current == "CANDIDATE":
            return "CAND_to_CAND"
        if current == "NO_TRADE":
            return "CAND_to_NO_TRADE"
        if current == "WAIT":
            return "CAND_to_WAIT"
    return f"{orig or 'unknown'}_to_{current}"


def _extract_decision_fields(text: str) -> dict:
    out: dict = {
        "ai_decision": None,
        "ai_direction": None,
        "ai_grade": None,
        "ai_framework": None,
        "ai_confidence": None,
        "trade_parameters": None,
        "no_trade_reason": None,
    }
    text_stripped = text.strip()
    if text_stripped.startswith("```"):
        lines = text_stripped.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text_stripped = "\n".join(lines)
    try:
        d = json.loads(text_stripped)
        out["ai_decision"] = d.get("decision")
        out["ai_grade"] = d.get("setup_grade") or d.get("confidence_grade")
        out["ai_framework"] = d.get("framework")
        out["ai_confidence"] = d.get("confidence_score")
        out["trade_parameters"] = d.get("trade_parameters")
        out["no_trade_reason"] = d.get("no_trade_reason")
        if d.get("trade_parameters"):
            out["ai_direction"] = d["trade_parameters"].get("direction")
    except Exception:
        pass
    return out


def _log_retry(retry_log: Path, trade_id: str, attempt: int, err: str) -> None:
    retry_log.parent.mkdir(parents=True, exist_ok=True)
    with open(retry_log, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "trade_id": trade_id,
            "attempt": attempt,
            "error": err,
        }) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(
    rows: list[CohortRow],
    past_trades: list[dict],
    out_dir: Path,
    raw_subdir: str,
    outcomes_filename: str,
    concurrency: int,
    mode: str,
    feedback_n: int,
    feedback_symbol_filter: str | None,
) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outcomes_path = out_dir / outcomes_filename
    retry_log = out_dir / f"_retries_{mode}.jsonl"

    if not _HAS_ANTHROPIC:
        raise RuntimeError("anthropic SDK not installed.")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set.")

    _load_production_builder()

    client = anthropic.AsyncAnthropic(api_key=api_key)
    sem = asyncio.Semaphore(concurrency)

    # Generate the F27 feedback block ONCE per record (cohort spans 3 days; if
    # we picked feedback per-day the block is mostly identical anyway).
    if mode == "treatment":
        # Use the cohort's earliest candle date as the cutoff for "most recent N before
        # cohort start". This is conservative — we don't peek forward inside the cohort.
        sorted_rows = sorted(rows, key=lambda r: r.candle_time_utc)
        cutoff_iso = sorted_rows[0].candle_time_utc
        last_n = select_last_n_before(past_trades, cutoff_iso,
                                       n=feedback_n, symbol=feedback_symbol_filter)
        feedback_block = format_d2_prose(last_n)
        print(f"Treatment mode: feedback_block_chars={len(feedback_block)}, "
              f"based on {len(last_n)} past trades before {cutoff_iso}",
              file=sys.stderr)
        # Persist the feedback block for inspection
        (out_dir / "feedback_block.txt").write_text(feedback_block, encoding="utf-8")
        (out_dir / "feedback_past_trades.json").write_text(
            json.dumps(last_n, indent=2), encoding="utf-8")
    else:
        feedback_block = ""

    async def _wrap(row: CohortRow):
        try:
            rec = load_trade_record(row.mso_path)
            return await _call_one(client, sem, row, rec, out_dir, raw_subdir,
                                    retry_log, additional_context=feedback_block)
        except Exception as exc:
            return {
                "trade_id": row.trade_id,
                "candle_time_utc": row.candle_time_utc,
                "regime": row.regime,
                "error": str(exc),
                "ts_replay_utc": datetime.now(timezone.utc).isoformat(),
            }

    print(f"Launching {len(rows)} {mode} replays at concurrency {concurrency}…",
          file=sys.stderr)
    t_start = time.monotonic()

    # Cache-friendly fan-out: 1 warmup call to write the cache, then parallel
    # the rest. This is critical because the system prompt is ~40K chars.
    warmup_n = 1 if len(rows) > 1 else 0
    if warmup_n:
        warmup_results = await asyncio.gather(*[_wrap(r) for r in rows[:warmup_n]])
        rest_results = await asyncio.gather(*[_wrap(r) for r in rows[warmup_n:]])
        results = list(warmup_results) + list(rest_results)
    else:
        results = await asyncio.gather(*[_wrap(r) for r in rows])
    elapsed = time.monotonic() - t_start
    print(f"Done in {elapsed:.1f}s ({elapsed / max(len(rows), 1):.2f}s/record)",
          file=sys.stderr)

    with open(outcomes_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    return results


def write_summary(out_dir: Path, results: list[dict], mode: str) -> None:
    summary_path = out_dir / f"SUMMARY_{mode}.md"
    n = len(results)
    errors = [r for r in results if r.get("error")]
    successes = [r for r in results if not r.get("error")]
    flips = [r.get("decision_flip") for r in successes]
    from collections import Counter
    flip_counts = Counter(flips)

    in_tok = sum(r.get("input_tokens", 0) for r in successes)
    out_tok = sum(r.get("output_tokens", 0) for r in successes)
    cr_tok = sum(r.get("cache_read_tokens", 0) for r in successes)
    cw_tok = sum(r.get("cache_creation_tokens", 0) for r in successes)
    cost = (
        in_tok * PRICE_INPUT_PER_M / 1e6
        + out_tok * PRICE_OUTPUT_PER_M / 1e6
        + cr_tok * PRICE_CACHE_READ_PER_M / 1e6
        + cw_tok * PRICE_CACHE_WRITE_PER_M / 1e6
    )
    elapsed_ms = [r.get("elapsed_ms", 0) for r in successes]
    median_ms = statistics.median(elapsed_ms) if elapsed_ms else 0

    filtered = [r for r in successes if r.get("current", {}).get("ai_decision") == "CANDIDATE"]
    long_filtered = [r for r in filtered if (r.get("current", {}).get("ai_direction") == "LONG")]

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# F27 Replay — {mode.upper()} Summary\n\n")
        f.write(f"## Cohort\n")
        f.write(f"- records: {n}, successes: {len(successes)}, errors: {len(errors)}\n\n")
        f.write(f"## Decision-flip distribution\n")
        for k, v in sorted(flip_counts.items(), key=lambda x: -x[1]):
            f.write(f"- {k}: {v}\n")
        f.write(f"\n## Filtered subset (current emits CANDIDATE)\n")
        f.write(f"- n: {len(filtered)}\n")
        f.write(f"- LONG: {len(long_filtered)}\n")
        f.write(f"\n## Token + cost\n")
        f.write(f"- input tokens: {in_tok:,}\n")
        f.write(f"- output tokens: {out_tok:,}\n")
        f.write(f"- cache_read tokens: {cr_tok:,}\n")
        f.write(f"- cache_creation tokens: {cw_tok:,}\n")
        f.write(f"- cumulative cost (Sonnet 4.6): ${cost:.4f}\n")
        f.write(f"- median elapsed: {median_ms} ms\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="F27 — backward-outcome injection replay")
    parser.add_argument("--cohort-csv", required=True)
    parser.add_argument("--past-trades-csv", required=True,
                        help="trades_unified.csv (enriched closed-trade history)")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--mode", choices=["baseline", "treatment"], required=True)
    parser.add_argument("--feedback-n", type=int, default=10,
                        help="N most-recent past trades to include in feedback block")
    parser.add_argument("--feedback-symbol", type=str, default=None,
                        help="Filter past trades by symbol (default: all instruments)")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    cohort_csv = Path(args.cohort_csv)
    out_dir = Path(args.out_dir)
    past_csv = Path(args.past_trades_csv)

    rows = load_cohort(cohort_csv, limit=args.limit)
    print(f"Loaded cohort: {len(rows)} replayable rows", file=sys.stderr)
    if not rows:
        print("No replayable rows — aborting.", file=sys.stderr)
        return 2

    past_trades = load_past_trades(past_csv)
    print(f"Loaded past-trades: {len(past_trades)} closed records", file=sys.stderr)

    raw_subdir = f"raw_responses_{args.mode}"
    outcomes_filename = f"{args.mode}_replay_outcomes.jsonl"

    results = asyncio.run(run(
        rows, past_trades, out_dir, raw_subdir, outcomes_filename,
        args.concurrency, args.mode, args.feedback_n, args.feedback_symbol,
    ))
    write_summary(out_dir, results, args.mode)

    print(f"Wrote {len(results)} outcomes to {out_dir / outcomes_filename}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
