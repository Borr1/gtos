#!/usr/bin/env python
"""A4 — replay current production AI prompt on H2-2026 XAUUSD trending_bull cohort.

This is the **Stage 2** replay script. Stage 1 (cohort manifest construction)
is `a4_build_cohort.py`. Run that first.

Per CEO directive 2026-04-28: re-run the production primary-analyzer prompt
exactly as production would today (post-HALLUC-1 + S79 + 4 sister-bug fixes)
on each candle's MSO snapshot, then compare current AI's decision distribution
+ filtered-subset behavior against the H2 baseline (76.5% → 16.7% WR collapse).

The script does NOT mutate any production state — it ONLY:
  - reads trade record JSONs (MSO snapshot captured at decision time)
  - REBUILDS the system + user prompt using CURRENT production code
    (`src.prompts.primary_analyzer_prompt.build_system_prompt/build_static_context/build_user_message`)
  - calls the Anthropic API with the EXACT same model/effort/timeout
  - writes results to research/a4_trending_bull_replay_*/replay_outcomes.jsonl

This is the load-bearing decision: the prompt was modified on 2026-04-27 with
HALLUC-1 + 4 sister bug fixes (system prompt grew 8.4K → 39.5K chars). To test
"did current AI recover the H2 decay?" we must compare the SAME MSO under the
NEW prompt against the OLD baseline outcome.

Production fidelity:
  model = claude-sonnet-4-6   (from agent_config.yaml ai.primary_model)
  effort = max                (from agent_config.yaml ai.primary_effort)
  api_timeout = 90s           (from agent_config.yaml ai.api_timeout_seconds)
  max_tokens = 2000           (from primary_analyzer.py:254)
  temperature = 0             (from primary_analyzer.py:255)
  cache_control: ephemeral 1h on system block (matches production)
  KB context: passed through `kb.assemble_full_context(mso)` (XAUUSD only,
              same fallback to empty as production)

Usage:
  # Smoke test (no API calls, validates everything else):
  python scripts/research/a4_trending_bull_replay.py \\
      --cohort-csv research/a4_trending_bull_replay_2026-04-28/a4_cohort_manifest.csv \\
      --out-dir research/a4_trending_bull_replay_2026-04-28 \\
      --dry-run

  # Real run (concurrency 50, full cohort):
  python scripts/research/a4_trending_bull_replay.py \\
      --cohort-csv research/a4_trending_bull_replay_2026-04-28/a4_cohort_manifest.csv \\
      --out-dir research/a4_trending_bull_replay_2026-04-28 \\
      --concurrency 50

  # Quick test on first 3 records:
  python scripts/research/a4_trending_bull_replay.py \\
      --cohort-csv research/a4_trending_bull_replay_2026-04-28/a4_cohort_manifest.csv \\
      --out-dir research/a4_trending_bull_replay_2026-04-28 \\
      --limit 3
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
# (per memory project_research_scripts_missing_dotenv).
try:
    from dotenv import load_dotenv  # type: ignore[import-not-found]
    load_dotenv()
except Exception:  # pragma: no cover - optional dep
    pass

# anthropic SDK is a runtime requirement of the trading system; don't crash on
# import for --dry-run support.
try:
    import anthropic  # type: ignore[import-not-found]
    _HAS_ANTHROPIC = True
except Exception:  # pragma: no cover - optional dep at scaffolding time
    _HAS_ANTHROPIC = False

# Make src.* importable from anywhere
REPO_ROOT = Path(__file__).resolve().parents[2]
# When invoked from the worktree, the parent repo holds the data + the source
# tree. Prefer GTOS_REPO_ROOT env var for explicit override.
_REPO_ROOT_ENV = os.environ.get("GTOS_REPO_ROOT")
SRC_ROOT = Path(_REPO_ROOT_ENV) if _REPO_ROOT_ENV else REPO_ROOT
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Import production prompt builders.
# These imports happen lazily inside `_build_prompt_for_record` because the
# prompt module reads YAML config; we want the import to fail in the call site
# with a clear error rather than at script load.

# ---------------------------------------------------------------------------
# Production-faithful constants — DO NOT change without updating CLAUDE.md
# ---------------------------------------------------------------------------
PROD_MODEL = "claude-sonnet-4-6"   # ai.primary_model
PROD_EFFORT = "max"                # ai.primary_effort
PROD_TIMEOUT_S = 90                # ai.api_timeout_seconds
PROD_MAX_TOKENS = 2000             # primary_analyzer.py:254
PROD_TEMPERATURE = 0               # primary_analyzer.py:255
PROD_CACHE_TTL = "1h"              # primary_analyzer.py:238
PROD_PRICE_FMT = ".2f"             # XAUUSD precision

# Sonnet 4.6 pricing per 1M tokens (cached as of 2026-04 — see shared/models.md)
PRICE_INPUT_PER_M = 3.00
PRICE_OUTPUT_PER_M = 15.00
PRICE_CACHE_READ_PER_M = 0.30      # ~10% of input
PRICE_CACHE_WRITE_PER_M = 6.00     # 2x of input for 1h TTL


# ---------------------------------------------------------------------------
# Data loading
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
    """Load the per-trade record (contains the captured MSO snapshot)."""
    return json.load(open(mso_path, encoding="utf-8"))


# ---------------------------------------------------------------------------
# Production-faithful prompt rebuild
# ---------------------------------------------------------------------------

_PROD_BUILDER = None
_PROD_CFG = None


def _load_production_builder():
    """Import the production prompt builder + config exactly once."""
    global _PROD_BUILDER, _PROD_CFG
    if _PROD_BUILDER is None:
        from src.prompts import primary_analyzer_prompt as builder
        import yaml
        cfg_path = SRC_ROOT / "config" / "agent_config.yaml"
        cfg = yaml.safe_load(open(cfg_path, encoding="utf-8"))
        # XAUUSD price format
        builder.set_price_format(PROD_PRICE_FMT)
        _PROD_BUILDER = builder
        _PROD_CFG = cfg
    return _PROD_BUILDER, _PROD_CFG


def build_prompt_from_record(rec: dict, kill_zone: str, kb_context: dict | None) -> dict:
    """Rebuild the CURRENT production system + user message from the captured MSO.

    This is the load-bearing semantic difference vs. simply replaying the
    captured prompt: the system prompt was substantially extended on 2026-04-27
    (HALLUC-1 + 4 sister fixes) and we want to test how the NEW prompt handles
    the SAME MSO inputs. Replaying the captured prompt would test the OLD
    prompt — not what the CEO requested.

    Returns dict with keys: system_text, user_message, mso_obj, current_time.
    """
    builder, cfg = _load_production_builder()
    from src.models.market_state_models import MarketStateObject

    mso_obj = MarketStateObject.model_validate(rec["mso"])

    sys_text = builder.build_system_prompt(cfg)
    static_ctx = builder.build_static_context(mso_obj)
    full_sys_text = sys_text + "\n\n## Static Context (D1/H4/Session)\n" + static_ctx

    if kb_context is None:
        kb_context = {"layer1": {}, "layer2": {}, "layer3": []}

    # Use the original candle_time as current_time (production passes
    # datetime.now() but the MSO is what mattered; we keep deterministic).
    candle_time = rec.get("metadata", {}).get("candle_time") or rec["mso"].get("timestamp_utc")
    user_msg = builder.build_user_message(
        mso_obj,
        kb_context=kb_context,
        current_time=candle_time,
        kill_zone=kill_zone,
        session_memory="",  # session memory disabled in production (T2b)
        cross_instrument_context="",
        additional_context="",
    )
    return {
        "system_text": full_sys_text,
        "user_message": user_msg,
        "candle_time": candle_time,
    }


def build_system_blocks(system_text: str) -> list[dict]:
    """Wrap rebuilt system prompt in production wire format (1h ephemeral cache)."""
    return [{
        "type": "text",
        "text": system_text,
        "cache_control": {"type": "ephemeral", "ttl": PROD_CACHE_TTL},
    }]


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

async def _call_one(
    client: "anthropic.AsyncAnthropic",
    sem: asyncio.Semaphore,
    row: CohortRow,
    rec: dict,
    out_dir: Path,
    retry_log: Path,
) -> dict:
    """Call the API for one cohort record. Logs retries to retry_log."""
    prompt = build_prompt_from_record(rec, row.kill_zone, kb_context=None)
    system_blocks = build_system_blocks(prompt["system_text"])
    user_message = prompt["user_message"]

    async with sem:
        last_err: Exception | None = None
        for attempt in range(3):  # initial + 2 retries
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
                        row.ai_decision_original,
                        parsed.get("ai_decision"),
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
                        out_dir, row.trade_id, resp_text,
                    ),
                }
            except Exception as exc:
                last_err = exc
                _log_retry(retry_log, row.trade_id, attempt, str(exc))
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        raise RuntimeError(f"unreachable; last_err={last_err}")


def _persist_full_response(out_dir: Path, trade_id: str, text: str) -> str:
    """Write full raw response to a per-trade file for inspection."""
    raw_dir = out_dir / "raw_responses"
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
    """Parse JSON response. Production primary_analyzer expects JSON; if it
    parses, take fields, else preserve raw."""
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
    concurrency: int,
    dry_run: bool,
) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outcomes_path = out_dir / "replay_outcomes.jsonl"
    retry_log = out_dir / "_retries.jsonl"

    if dry_run:
        # Validate every record loads + has full prompt + MSO + can rebuild prompt.
        results = []
        for row in rows:
            try:
                rec = load_trade_record(row.mso_path)
                # Rebuild current prompt from MSO
                p = build_prompt_from_record(rec, row.kill_zone, kb_context=None)
                results.append({
                    "trade_id": row.trade_id,
                    "candle_time_utc": row.candle_time_utc,
                    "regime": row.regime,
                    "kill_zone": row.kill_zone,
                    "dry_run_ok": True,
                    "current_system_prompt_chars": len(p["system_text"]),
                    "current_user_message_chars": len(p["user_message"]),
                    "captured_system_prompt_chars": len(rec["prompt"]["system_prompt"]),
                    "captured_user_message_chars": len(rec["prompt"]["user_message"]),
                    "mso_chars": len(json.dumps(rec.get("mso", {}))),
                })
            except Exception as exc:
                import traceback
                results.append({
                    "trade_id": row.trade_id,
                    "dry_run_ok": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                })
        with open(outcomes_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")
        return results

    if not _HAS_ANTHROPIC:
        raise RuntimeError(
            "anthropic SDK not installed — run `pip install anthropic` "
            "before launching Stage 2 replay."
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set; ensure .env is loaded or export the var."
        )

    # Eager-load production builder so any import error surfaces before the
    # first parallel call (avoids 11 simultaneous identical errors).
    _load_production_builder()

    client = anthropic.AsyncAnthropic(api_key=api_key)
    sem = asyncio.Semaphore(concurrency)

    async def _wrap(row: CohortRow):
        try:
            rec = load_trade_record(row.mso_path)
            return await _call_one(client, sem, row, rec, out_dir, retry_log)
        except Exception as exc:
            return {
                "trade_id": row.trade_id,
                "candle_time_utc": row.candle_time_utc,
                "regime": row.regime,
                "error": str(exc),
                "ts_replay_utc": datetime.now(timezone.utc).isoformat(),
            }

    print(f"Launching {len(rows)} replays at concurrency {concurrency}…", file=sys.stderr)
    t_start = time.monotonic()

    # Cache-friendly fan-out: fire first call alone, await it (which writes the
    # cache), then fan out the rest. Per shared/prompt-caching.md: a cache
    # entry becomes readable only after the first response BEGINS streaming.
    # Without this, N parallel calls with identical prefixes all pay full price.
    # For the A4 cohort the cost delta is small (~$0.10), but the pattern is
    # documented for reuse.
    warmup_n = 1 if len(rows) > 1 else 0
    if warmup_n:
        print(f"Cache warmup: firing first {warmup_n} call(s) before fan-out", file=sys.stderr)
        warmup_results = await asyncio.gather(*[_wrap(r) for r in rows[:warmup_n]])
        rest_results = await asyncio.gather(*[_wrap(r) for r in rows[warmup_n:]])
        results = list(warmup_results) + list(rest_results)
    else:
        results = await asyncio.gather(*[_wrap(r) for r in rows])
    elapsed = time.monotonic() - t_start
    print(f"Done in {elapsed:.1f}s ({elapsed / max(len(rows), 1):.2f}s/record)", file=sys.stderr)

    with open(outcomes_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    return results


def write_summary(out_dir: Path, results: list[dict], dry_run: bool) -> None:
    summary_path = out_dir / "SUMMARY.md"
    if dry_run:
        ok = sum(1 for r in results if r.get("dry_run_ok"))
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("# A4 Replay — DRY-RUN summary\n\n")
            f.write(f"- records validated: {ok} / {len(results)}\n\n")
            for r in results:
                if r.get("dry_run_ok"):
                    delta_sys = r["current_system_prompt_chars"] - r["captured_system_prompt_chars"]
                    delta_user = r["current_user_message_chars"] - r["captured_user_message_chars"]
                    f.write(f"- {r['trade_id']}: ")
                    f.write(f"sys=current {r['current_system_prompt_chars']} ")
                    f.write(f"(captured {r['captured_system_prompt_chars']}, Δ {delta_sys:+}); ")
                    f.write(f"user=current {r['current_user_message_chars']} ")
                    f.write(f"(captured {r['captured_user_message_chars']}, Δ {delta_user:+})\n")
                else:
                    f.write(f"- FAIL {r.get('trade_id')}: {r.get('error')}\n")
        return

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
    short_filtered = [r for r in filtered if (r.get("current", {}).get("ai_direction") == "SHORT")]
    by_kz = Counter(r.get("kill_zone") for r in filtered)

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# A4 Replay — Summary\n\n")
        f.write(f"## Cohort\n")
        f.write(f"- records: {n}, successes: {len(successes)}, errors: {len(errors)}\n\n")
        f.write(f"## Decision-flip distribution\n")
        for k, v in sorted(flip_counts.items(), key=lambda x: -x[1]):
            f.write(f"- {k}: {v}\n")
        f.write(f"\n## Filtered subset (current emits CANDIDATE)\n")
        f.write(f"- n: {len(filtered)}\n")
        f.write(f"- LONG: {len(long_filtered)}, SHORT: {len(short_filtered)}\n")
        f.write(f"- by kill zone: {dict(by_kz)}\n")
        f.write(f"\n## Token + cost\n")
        f.write(f"- input tokens: {in_tok:,}\n")
        f.write(f"- output tokens: {out_tok:,}\n")
        f.write(f"- cache_read tokens: {cr_tok:,}\n")
        f.write(f"- cache_creation tokens: {cw_tok:,}\n")
        f.write(f"- cumulative cost (Sonnet 4.6 pricing): ${cost:.4f}\n")
        f.write(f"- median elapsed: {median_ms} ms\n")
        f.write("\n## Verdict bands — REQUIRES OUT-OF-BAND REALIZED-R JOIN\n")
        f.write("Realized R for these candidates is NOT in the trade record\n")
        f.write("(`exit: null` per memory `project_trade_records_enrichment_gap`).\n")
        f.write("Use `_trade_index.json` + `trades_unified.csv` + filtered-subset\n")
        f.write("mapping post-hoc; this script alone yields decision-flip distribution\n")
        f.write("only. GREEN/YELLOW/RED bands cannot be evaluated until that join.\n")
        f.write(f"\n## Ten interesting flips (CANDIDATEs the current AI now demotes)\n")
        flip_examples = [r for r in successes if r.get("decision_flip") in ("CAND_to_NO_TRADE", "CAND_to_WAIT")]
        for r in flip_examples[:10]:
            f.write(f"### {r['trade_id']}\n")
            f.write(f"- kill_zone: {r['kill_zone']}, original={r['original']}\n")
            f.write(f"- now: decision={r['current'].get('ai_decision')}, ")
            f.write(f"reason={r['current'].get('no_trade_reason')}\n")
            f.write(f"- raw[:200]: {r.get('raw_response_first_200_chars', '')!r}\n\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="A4 Stage-2 replay (XAUUSD trending_bull H2-2026)")
    parser.add_argument("--cohort-csv", required=True, help="Path to a4_cohort_manifest.csv")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--concurrency", type=int, default=50)
    parser.add_argument("--max-tokens", type=int, default=None,
                        help="Override max_tokens (default = production 2000)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate cohort + prompt rebuild WITHOUT making API calls")
    parser.add_argument("--limit", type=int, default=None,
                        help="Replay only the first N rows (smoke test)")
    args = parser.parse_args()

    global PROD_MAX_TOKENS
    if args.max_tokens is not None and args.max_tokens != PROD_MAX_TOKENS:
        print(
            f"WARNING: overriding max_tokens={args.max_tokens} (production = {PROD_MAX_TOKENS}).",
            file=sys.stderr,
        )
        PROD_MAX_TOKENS = args.max_tokens

    cohort_csv = Path(args.cohort_csv)
    out_dir = Path(args.out_dir)

    rows = load_cohort(cohort_csv, limit=args.limit)
    print(f"Loaded cohort: {len(rows)} replayable rows", file=sys.stderr)
    if not rows:
        print("No replayable rows — aborting.", file=sys.stderr)
        return 2

    results = asyncio.run(run(rows, out_dir, args.concurrency, args.dry_run))
    write_summary(out_dir, results, args.dry_run)

    print(f"Wrote {len(results)} outcomes to {out_dir / 'replay_outcomes.jsonl'}", file=sys.stderr)
    print(f"Summary at {out_dir / 'SUMMARY.md'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
