#!/usr/bin/env python
"""F27 — Counterfactual NEGATIVE-telemetry probe.

Disambiguation experiment for F27's null verdict. Identical methodology to
F27's treatment run on the same A4 trending_bull XAUUSD n=11 cohort, BUT
with a synthetic negative-telemetry feedback block (8L/2W mean -0.65R,
recent losses dominated by trending_bull LONG ob_retest setups — i.e.
deliberate inverse of the cohort's setup signature).

Two competing hypotheses being disambiguated:
- H_A: feedback channel is dead (AI ignores prompt block regardless of content)
- H_B: channel is alive but signal-direction-dependent (positive on winning
       cohort doesn't move because evidence is reinforcing; contradictory
       telemetry on same cohort SHOULD move decisions)

Verdict thresholds:
- CHANNEL_DEAD: 11/11 still CAND, mean R delta within +/-0.01R
- CHANNEL_ALIVE_DIRECTIONAL: ANY decision flip CAND -> NO_TRADE/WAIT under
  negative telemetry, OR mean R delta <= -0.05R
- CHANNEL_PARTIAL: trade-params shift materially (mean delta > 1 USD on
  entry/SL/TP1) but no decision flip

Production fidelity (model/effort/timeout/cache/temperature/max_tokens) mirrors
F27 treatment exactly. The ONLY semantic difference is the prose-summary content.

Usage:
  python research/f27_prototype_2026-04-28/counterfactual_negative/scripts/f27_replay_negative_telemetry.py \\
      --cohort-csv research/a4_trending_bull_replay_2026-04-28/a4_cohort_manifest.csv \\
      --out-dir research/f27_prototype_2026-04-28/counterfactual_negative \\
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
    # Also try main repo .env when running from worktree
    repo_env = os.environ.get("GTOS_REPO_ROOT")
    if repo_env:
        load_dotenv(Path(repo_env) / ".env")
except Exception:
    pass

try:
    import anthropic  # type: ignore[import-not-found]
    _HAS_ANTHROPIC = True
except Exception:
    _HAS_ANTHROPIC = False

# Make src.* importable. Use GTOS_REPO_ROOT (main repo) so we pick up
# production code + data + .env from main, while writing outputs to worktree.
REPO_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT_ENV = os.environ.get("GTOS_REPO_ROOT")
SRC_ROOT = Path(_REPO_ROOT_ENV) if _REPO_ROOT_ENV else REPO_ROOT
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# ---------------------------------------------------------------------------
# Production-faithful constants (mirror A4 / F27 treatment exactly)
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
# SYNTHETIC NEGATIVE TELEMETRY (the only semantic delta from F27 treatment)
# ---------------------------------------------------------------------------
# Designed to be deliberately INVERSE of F27's positive run:
# - 2W / 8L mean -0.65R (vs F27 positive's 6W/4L +0.31R)
# - Recent losing cluster on SAME (trending_bull / LONG / ob_retest) signature
#   as the A4 cohort, so the "calibration signal" is contradictory rather than
#   reinforcing. Format follows F27's D2 prose-summary style verbatim where
#   possible.

NEGATIVE_TELEMETRY_PROSE = (
    "## Recent trade outcomes (most recent 10 closed; treat as historical signal, not session memory)\n"
    "\n"
    "In your last 10 closed trades on this account: 2W / 8L, mean realized R = -0.65R, sum -6.5R.\n"
    "\n"
    "Recent losing setups (8 of last 10):\n"
    "- 2026-04-14 NY ob_retest LONG XAUUSD trending_bull -> -1.0R (SL hit, similar A+ grade)\n"
    "- 2026-04-14 London ob_retest LONG XAUUSD trending_bull -> -1.0R (SL hit, similar setup signature)\n"
    "- 2026-04-13 NY ob_retest LONG XAUUSD trending_bull -> -1.0R (SL hit, A+ grade)\n"
    "- 2026-04-13 NY ob_retest LONG XAUUSD trending_bull -> -1.0R (SL hit, similar fresh-OB pattern)\n"
    "- 2026-04-12 London ob_retest LONG XAUUSD trending_bull -> -1.0R (SL hit)\n"
    "- 2026-04-12 NY ob_retest LONG XAUUSD trending_bull -> -0.8R (BE-stopped after partial)\n"
    "- 2026-04-11 NY ob_retest LONG XAUUSD chop -> -1.0R (SL hit on counter-trend)\n"
    "- 2026-04-10 London ob_retest LONG XAUUSD trending_bull -> -1.0R (SL hit, displacement faded)\n"
    "\n"
    "Recent winning setups (2 of last 10):\n"
    "- 2026-04-09 NY ob_retest LONG XAUUSD trending_bull -> +1.5R (TP1)\n"
    "- 2026-04-08 NY ob_retest LONG XAUUSD trending_bull -> +1.5R (TP1)\n"
    "\n"
    "Per-regime breakdown of last 10:\n"
    "- trending_bull / LONG / ob_retest / NY: 1W 5L mean -0.81R\n"
    "- trending_bull / LONG / ob_retest / London: 1W 2L mean -0.50R\n"
    "\n"
    "Use this as a calibration signal on your decision-making, not as a substitute for evaluating "
    "this candle's MSO. The outcomes above are HISTORICAL telemetry from previously-closed trades, "
    "NOT the current session's reasoning context.\n"
)


# ---------------------------------------------------------------------------
# Data loading (mirrors F27)
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
    """Rebuild CURRENT production prompt; inject negative-telemetry block."""
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
# API call (mirrors F27 treatment)
# ---------------------------------------------------------------------------

async def _call_one(
    client: "anthropic.AsyncAnthropic",
    sem: asyncio.Semaphore,
    row: CohortRow,
    rec: dict,
    out_dir: Path,
    raw_subdir: str,
    retry_log: Path,
    additional_context: str,
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
    out_dir: Path,
    raw_subdir: str,
    outcomes_filename: str,
    concurrency: int,
    feedback_block: str,
) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outcomes_path = out_dir / outcomes_filename
    retry_log = out_dir / "_retries_negative.jsonl"

    if not _HAS_ANTHROPIC:
        raise RuntimeError("anthropic SDK not installed.")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set.")

    _load_production_builder()

    client = anthropic.AsyncAnthropic(api_key=api_key)
    sem = asyncio.Semaphore(concurrency)

    print(f"NEGATIVE-telemetry mode: feedback_block_chars={len(feedback_block)}",
          file=sys.stderr)
    # Persist the feedback block for inspection
    (out_dir / "feedback_block.txt").write_text(feedback_block, encoding="utf-8")

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

    print(f"Launching {len(rows)} negative-telemetry replays at concurrency {concurrency}…",
          file=sys.stderr)
    t_start = time.monotonic()

    # Cache-friendly fan-out: 1 warmup call to write the cache, then parallel
    # the rest.
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


def write_summary(out_dir: Path, results: list[dict]) -> None:
    summary_path = out_dir / "SUMMARY_negative.md"
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
        f.write(f"# F27 Counterfactual NEGATIVE-Telemetry Replay Summary\n\n")
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
    parser = argparse.ArgumentParser(
        description="F27 — counterfactual NEGATIVE-telemetry probe (channel-alive disambiguation)")
    parser.add_argument("--cohort-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    cohort_csv = Path(args.cohort_csv)
    out_dir = Path(args.out_dir)

    rows = load_cohort(cohort_csv, limit=args.limit)
    print(f"Loaded cohort: {len(rows)} replayable rows", file=sys.stderr)
    if not rows:
        print("No replayable rows — aborting.", file=sys.stderr)
        return 2

    raw_subdir = "raw_responses"
    outcomes_filename = "replay_outcomes.jsonl"

    results = asyncio.run(run(
        rows, out_dir, raw_subdir, outcomes_filename,
        args.concurrency, NEGATIVE_TELEMETRY_PROSE,
    ))
    write_summary(out_dir, results)

    print(f"Wrote {len(results)} outcomes to {out_dir / outcomes_filename}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
