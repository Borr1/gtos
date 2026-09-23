#!/usr/bin/env python3
"""Full 86-trade model comparison: Sonnet+Thinking vs Opus+Thinking.

Runs all 86 XAUUSD batch trades through both models with extended thinking
and reconstructed session memory. Produces the definitive comparison.

Usage:
    python scripts/full_86_model_comparison.py --dry-run
    python scripts/full_86_model_comparison.py
    python scripts/full_86_model_comparison.py --resume  # Resume from checkpoint
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env", override=True)

import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_API_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "batch_api"
SESSIONS_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "sessions"
OUTPUT_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "test_b"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LEGACY_REPORT_DIR = (
    _PROJECT_ROOT
    / "research"
    / "archive"
    / "root_legacy_artifacts_2026_05_31"
    / "generated"
    / "model_comparison"
)
LEGACY_REPORT_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_FILE = OUTPUT_DIR / "full_86_checkpoint.json"

SONNET = "claude-sonnet-4-20250514"
OPUS = "claude-opus-4-20250514"

HEDGE_PHRASES = [
    "however", "although", "unclear", "mixed", "choppy",
    "minimal", "weak", "uncertain", "ambiguous", "borderline",
    "marginal", "questionable", "debatable", "possible", "might",
]


# ═══════════════════════════════════════════════════════════════════════
# Data loading (cached)
# ═══════════════════════════════════════════════════════════════════════

_prompt_cache = None
_raw_cache = None


def load_all_prompts() -> dict:
    global _prompt_cache
    if _prompt_cache is not None:
        return _prompt_cache
    index = {}
    for fp in sorted(BATCH_API_DIR.glob("*_full_prompts.json")):
        try:
            for item in json.load(open(fp)):
                index[item["custom_id"]] = item["prompt"]
        except Exception as e:
            logger.warning(f"Failed {fp.name}: {e}")
    _prompt_cache = index
    return index


def load_all_raw_results() -> dict:
    global _raw_cache
    if _raw_cache is not None:
        return _raw_cache
    index = {}
    for fp in sorted(BATCH_API_DIR.glob("*_raw_results.json")):
        try:
            index.update(json.load(open(fp)))
        except Exception as e:
            logger.warning(f"Failed {fp.name}: {e}")
    _raw_cache = index
    return index


# ═══════════════════════════════════════════════════════════════════════
# Trade selection — ALL 86
# ═══════════════════════════════════════════════════════════════════════

def load_all_86_trades() -> list[dict]:
    trades = []
    for f in sorted(SESSIONS_DIR.glob("*.json")):
        d = json.load(open(f))
        ts = d.get("trade_summary", {})
        if not (isinstance(ts, dict) and ts.get("trade_taken")):
            continue
        evals = d.get("candle_evaluations", [])
        candidate = None
        for e in evals:
            if e.get("decision") == "CANDIDATE" and e.get("trade_executed"):
                candidate = e
                break
        if not candidate:
            continue
        ct = candidate["candle_time"]
        kz = candidate.get("kill_zone", "london")
        date_str = d["date"]
        time_part = ct[11:16].replace(":", "")
        custom_id = f"{date_str}_{kz}_{time_part}"
        trades.append({
            "date": date_str, "candle_time": ct, "kill_zone": kz,
            "custom_id": custom_id, "outcome": ts["outcome"],
            "r_multiple": ts.get("r_multiple", 0),
        })
    return trades


# ═══════════════════════════════════════════════════════════════════════
# Session memory reconstruction
# ═══════════════════════════════════════════════════════════════════════

def parse_response_text(raw) -> dict | None:
    text = raw.get("text", "") if isinstance(raw, dict) else raw
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except:
        return None


def compress_eval(parsed: dict) -> str:
    d = parsed.get("decision", "?")
    if d == "NO_TRADE":
        return f"NO_TRADE — {(parsed.get('no_trade_reason','') or '')[:100]}"
    elif d == "CANDIDATE":
        tp = parsed.get("trade_parameters", {}) or {}
        r = parsed.get("reasoning", {})
        return (f"CANDIDATE ({r.get('setup_grade','?')}, conf={parsed.get('confidence_score',0)}) — "
                f"{tp.get('direction','?')} entry={tp.get('entry_price',0)}")
    elif d == "WAIT":
        return f"WAIT — {(parsed.get('wait_reason','') or '')[:100]}"
    return d


def build_session_memory(date: str, kz: str, candle_time: str, raw_results: dict) -> str:
    prefix = f"{date}_{kz}_"
    target_tag = candle_time[11:16].replace(":", "")
    target_cid = f"{date}_{kz}_{target_tag}"
    entries = []
    for cid in sorted(k for k in raw_results if k.startswith(prefix)):
        if cid >= target_cid:
            break
        parsed = parse_response_text(raw_results[cid])
        if not parsed:
            continue
        tt = cid.split("_")[-1]
        entries.append(f"- {tt[:2]}:{tt[2:]} UTC: {compress_eval(parsed)}")
    return "\n".join(entries[-6:])


def inject_memory(user_message: str, session_memory: str) -> str:
    if not session_memory:
        return user_message
    block = (
        "\n## Prior Candle Assessments (this session)\n"
        "The following are your assessments of prior candles in this kill zone.\n"
        "Consider the progression: Is a setup developing across candles? "
        "Did a prior candle show a sweep or displacement that sets up the current candle? "
        "If you said WAIT or noted a developing pattern on a prior candle, "
        "check if the trigger has now occurred.\n\n"
        f"{session_memory}\n"
    )
    marker = "## Current Time:"
    idx = user_message.find(marker)
    if idx >= 0:
        return user_message[:idx] + block + "\n" + user_message[idx:]
    return user_message + "\n" + block


# ═══════════════════════════════════════════════════════════════════════
# API calls with thinking
# ═══════════════════════════════════════════════════════════════════════

def call_with_thinking(client: anthropic.Anthropic, model: str,
                       system_blocks: list, user_message: str,
                       retries: int = 2) -> dict:
    """Call a model with extended thinking. Uses streaming for both models."""
    for attempt in range(retries + 1):
        try:
            with client.messages.stream(
                model=model,
                max_tokens=16000,
                thinking={"type": "enabled", "budget_tokens": 10000},
                system=system_blocks,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                response = stream.get_final_message()

            thinking_text = ""
            response_text = ""
            for block in response.content:
                if block.type == "thinking":
                    thinking_text = block.thinking
                elif block.type == "text":
                    response_text = block.text

            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```\w*\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)
            parsed = json.loads(cleaned)

            return {
                "status": "ok",
                "response": parsed,
                "raw": cleaned,
                "thinking": thinking_text,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        except json.JSONDecodeError:
            return {"status": "parse_error", "raw": response_text[:500] if 'response_text' in dir() else ""}
        except Exception as e:
            if attempt < retries:
                logger.warning(f"  Attempt {attempt+1} failed ({e}), retrying in 5s...")
                time.sleep(5)
                continue
            return {"status": "error", "error": str(e)}


def extract_metrics(resp: dict) -> dict:
    if not resp or resp.get("status") != "ok":
        return {"decision": "ERROR", "confidence": 0, "grade": "?",
                "reasoning_words": 0, "price_levels": 0, "hedges": 0,
                "no_trade_reason": ""}
    r = resp["response"]
    reasoning = r.get("reasoning", {})
    overall = reasoning.get("overall_reasoning", "")
    raw = resp.get("raw", "")
    prices = re.findall(r'\d{4}\.\d{1,2}', raw)
    hedge_count = sum(raw.lower().count(h) for h in HEDGE_PHRASES)
    return {
        "decision": r.get("decision", "?"),
        "confidence": r.get("confidence_score", 0),
        "grade": reasoning.get("setup_grade", "?"),
        "framework": r.get("framework", "?"),
        "reasoning_words": len(overall.split()),
        "price_levels": len(set(prices)),
        "hedges": hedge_count,
        "no_trade_reason": r.get("no_trade_reason", "") or "",
    }


# ═══════════════════════════════════════════════════════════════════════
# Checkpoint management
# ═══════════════════════════════════════════════════════════════════════

def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        return json.load(open(CHECKPOINT_FILE))
    return {"sonnet_results": {}, "opus_results": {}, "completed": []}


def save_checkpoint(checkpoint: dict):
    # Strip thinking text from checkpoint to keep file small
    for key in ["sonnet_results", "opus_results"]:
        for cid, r in checkpoint.get(key, {}).items():
            if "thinking" in r:
                r["thinking_len"] = len(r["thinking"])
                del r["thinking"]
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════
# Report generation
# ═══════════════════════════════════════════════════════════════════════

def build_report(trades: list[dict], sonnet_orig: dict,
                 sonnet_think: dict, opus_think: dict) -> str:
    lines = []
    lines.append("# Full 86-Trade Model Comparison: Sonnet+Thinking vs Opus+Thinking")
    lines.append(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Population: ALL {len(trades)} XAUUSD batch trades")
    lines.append(f"Sonnet+Thinking: {SONNET} with 10K thinking budget")
    lines.append(f"Opus+Thinking: {OPUS} with 10K thinking budget")
    lines.append(f"Baseline: Original Sonnet (no thinking) from batch results")
    lines.append("")

    # ── Decision table ──
    lines.append("## Decision Table")
    lines.append("")
    lines.append("| # | Date | KZ | Actual | R | Orig Sonnet | Sonnet+Think | Opus+Think |")
    lines.append("|---|------|----|--------|-----|-------------|-------------|-----------|")

    orig_metrics = []
    st_metrics = []
    ot_metrics = []

    for i, t in enumerate(trades):
        cid = t["custom_id"]
        om = extract_metrics(sonnet_orig.get(cid, {}))
        sm = extract_metrics(sonnet_think.get(cid, {}))
        opm = extract_metrics(opus_think.get(cid, {}))
        orig_metrics.append(om)
        st_metrics.append(sm)
        ot_metrics.append(opm)

        lines.append(f"| {i+1} | {t['date']} | {t['kill_zone'][:2]} | {t['outcome']:>4} | "
                     f"{t['r_multiple']:+.2f} | {om['decision']:<11} | "
                     f"{sm['decision']:<11} | {opm['decision']:<9} |")

    # ── Aggregate stats ──
    def agg(metrics, trades_list):
        cands = [(m, t) for m, t in zip(metrics, trades_list) if m["decision"] == "CANDIDATE"]
        n = len(cands)
        w = sum(1 for m, t in cands if t["outcome"] == "WIN")
        l = n - w
        confs = [m["confidence"] for m in metrics if m["confidence"] > 0]
        return {
            "total_cand": n, "wins": w, "losses": l,
            "wr": w / n if n > 0 else 0,
            "confs": confs,
            "conf_mean": sum(confs) / len(confs) if confs else 0,
            "conf_std": (sum((c - sum(confs)/len(confs))**2 for c in confs) / len(confs))**0.5 if len(confs) > 1 else 0,
            "conf_min": min(confs) if confs else 0,
            "conf_max": max(confs) if confs else 0,
        }

    o_agg = agg(orig_metrics, trades)
    s_agg = agg(st_metrics, trades)
    op_agg = agg(ot_metrics, trades)

    lines.append("")
    lines.append("## Selectivity Summary")
    lines.append("")
    lines.append("| Metric | Orig Sonnet | Sonnet+Thinking | Opus+Thinking |")
    lines.append("|--------|-------------|-----------------|---------------|")
    lines.append(f"| CANDIDATEs | {o_agg['total_cand']}/{len(trades)} | "
                 f"{s_agg['total_cand']}/{len(trades)} | {op_agg['total_cand']}/{len(trades)} |")
    lines.append(f"| Winners caught | {o_agg['wins']} | {s_agg['wins']} | {op_agg['wins']} |")
    lines.append(f"| Losers approved | {o_agg['losses']} | {s_agg['losses']} | {op_agg['losses']} |")
    lines.append(f"| **CANDIDATE WR** | **{o_agg['wr']:.0%}** | **{s_agg['wr']:.0%}** | **{op_agg['wr']:.0%}** |")
    lines.append(f"| Trade rate | {o_agg['total_cand']/len(trades):.0%} | "
                 f"{s_agg['total_cand']/len(trades):.0%} | {op_agg['total_cand']/len(trades):.0%} |")

    # ── Confidence comparison ──
    lines.append("")
    lines.append("## Confidence Score Distribution")
    lines.append("")
    for label, a in [("Orig Sonnet", o_agg), ("Sonnet+Thinking", s_agg), ("Opus+Thinking", op_agg)]:
        if a["confs"]:
            lines.append(f"- {label}: n={len(a['confs'])}, mean={a['conf_mean']:.0f}, "
                        f"std={a['conf_std']:.1f}, range=[{a['conf_min']}, {a['conf_max']}]")
        else:
            lines.append(f"- {label}: No CANDIDATE confidence scores")

    # ── R-impact ──
    lines.append("")
    lines.append("## R-Impact Analysis")
    lines.append("")

    for label, metrics in [("Orig Sonnet", orig_metrics), ("Sonnet+Thinking", st_metrics), ("Opus+Thinking", ot_metrics)]:
        r_total = 0
        for m, t in zip(metrics, trades):
            if m["decision"] == "CANDIDATE":
                r_total += t["r_multiple"]
        a = agg(metrics, trades)
        lines.append(f"- **{label}**: {r_total:+.2f}R on {a['total_cand']} trades "
                     f"({a['wins']}W {a['losses']}L)")

    # ── Winner catch rate ──
    lines.append("")
    lines.append("## Winner Catch Rate (trades that were actual winners)")
    lines.append("")
    winner_trades = [(i, t) for i, t in enumerate(trades) if t["outcome"] == "WIN"]
    loser_trades = [(i, t) for i, t in enumerate(trades) if t["outcome"] == "LOSS"]

    for label, metrics in [("Orig Sonnet", orig_metrics), ("Sonnet+Thinking", st_metrics), ("Opus+Thinking", ot_metrics)]:
        caught = sum(1 for i, t in winner_trades if metrics[i]["decision"] == "CANDIDATE")
        lines.append(f"- {label}: {caught}/{len(winner_trades)} winners caught ({caught/len(winner_trades):.0%})")

    # ── Loser veto rate ──
    lines.append("")
    lines.append("## Loser Veto Rate (trades that were actual losers)")
    lines.append("")
    for label, metrics in [("Orig Sonnet", orig_metrics), ("Sonnet+Thinking", st_metrics), ("Opus+Thinking", ot_metrics)]:
        approved = sum(1 for i, t in loser_trades if metrics[i]["decision"] == "CANDIDATE")
        vetoed = len(loser_trades) - approved
        lines.append(f"- {label}: {vetoed}/{len(loser_trades)} losers vetoed ({vetoed/len(loser_trades):.0%})")

    # ── Flip analysis: Sonnet+Thinking vs Original ──
    lines.append("")
    lines.append("## Flips: Sonnet+Thinking vs Original Sonnet")
    lines.append("")
    good_flips_st = 0
    bad_flips_st = 0
    for i, t in enumerate(trades):
        om = orig_metrics[i]
        sm = st_metrics[i]
        if om["decision"] == sm["decision"]:
            continue
        if t["outcome"] == "LOSS" and om["decision"] == "CANDIDATE" and sm["decision"] != "CANDIDATE":
            good_flips_st += 1
            lines.append(f"  GOOD: {t['date']} — Thinking vetoed LOSS ({t['r_multiple']:+.2f}R)")
        elif t["outcome"] == "WIN" and om["decision"] == "CANDIDATE" and sm["decision"] != "CANDIDATE":
            bad_flips_st += 1
            lines.append(f"  BAD:  {t['date']} — Thinking missed WIN ({t['r_multiple']:+.2f}R)")
        elif t["outcome"] == "WIN" and om["decision"] != "CANDIDATE" and sm["decision"] == "CANDIDATE":
            good_flips_st += 1
            lines.append(f"  GOOD: {t['date']} — Thinking found WIN ({t['r_multiple']:+.2f}R)")
        elif t["outcome"] == "LOSS" and om["decision"] != "CANDIDATE" and sm["decision"] == "CANDIDATE":
            bad_flips_st += 1
            lines.append(f"  BAD:  {t['date']} — Thinking approved LOSS ({t['r_multiple']:+.2f}R)")

    lines.append(f"\nGood flips: {good_flips_st}, Bad flips: {bad_flips_st}")

    # ── Flip analysis: Opus+Thinking vs Original ──
    lines.append("")
    lines.append("## Flips: Opus+Thinking vs Original Sonnet")
    lines.append("")
    good_flips_op = 0
    bad_flips_op = 0
    for i, t in enumerate(trades):
        om = orig_metrics[i]
        opm = ot_metrics[i]
        if om["decision"] == opm["decision"]:
            continue
        if t["outcome"] == "LOSS" and om["decision"] == "CANDIDATE" and opm["decision"] != "CANDIDATE":
            good_flips_op += 1
            lines.append(f"  GOOD: {t['date']} — Opus vetoed LOSS ({t['r_multiple']:+.2f}R)")
        elif t["outcome"] == "WIN" and om["decision"] == "CANDIDATE" and opm["decision"] != "CANDIDATE":
            bad_flips_op += 1
            lines.append(f"  BAD:  {t['date']} — Opus missed WIN ({t['r_multiple']:+.2f}R)")
        elif t["outcome"] == "WIN" and om["decision"] != "CANDIDATE" and opm["decision"] == "CANDIDATE":
            good_flips_op += 1
            lines.append(f"  GOOD: {t['date']} — Opus found WIN ({t['r_multiple']:+.2f}R)")
        elif t["outcome"] == "LOSS" and om["decision"] != "CANDIDATE" and opm["decision"] == "CANDIDATE":
            bad_flips_op += 1
            lines.append(f"  BAD:  {t['date']} — Opus approved LOSS ({t['r_multiple']:+.2f}R)")

    lines.append(f"\nGood flips: {good_flips_op}, Bad flips: {bad_flips_op}")

    # ── Head-to-head: Sonnet+Thinking vs Opus+Thinking ──
    lines.append("")
    lines.append("## Head-to-Head: Sonnet+Thinking vs Opus+Thinking")
    lines.append("")
    h2h_agree = sum(1 for i in range(len(trades)) if st_metrics[i]["decision"] == ot_metrics[i]["decision"])
    lines.append(f"Agreement: {h2h_agree}/{len(trades)} ({h2h_agree/len(trades):.0%})")
    lines.append("")
    for i, t in enumerate(trades):
        sm = st_metrics[i]
        opm = ot_metrics[i]
        if sm["decision"] != opm["decision"]:
            lines.append(f"  {t['date']} {t['outcome']:>4} {t['r_multiple']:+.2f}R — "
                        f"Sonnet+T: {sm['decision']}, Opus+T: {opm['decision']}")

    # ── Cost analysis ──
    lines.append("")
    lines.append("## Cost Analysis")
    lines.append("")
    lines.append("Per-call costs (direct API, not batch):")
    lines.append("- Sonnet+Thinking: ~$0.04/call → ~$120/month at 100 calls/day")
    lines.append("- Opus+Thinking: ~$0.15/call → ~$450/month at 100 calls/day")
    lines.append("- Current Sonnet (no thinking): ~$0.01/call → ~$30/month")
    lines.append("")
    lines.append("With batch API (50% discount):")
    lines.append("- Sonnet+Thinking: ~$0.02/call → ~$60/month")
    lines.append("- Opus+Thinking: ~$0.075/call → ~$225/month")
    lines.append("")

    # ── FINAL VERDICT ──
    lines.append("## FINAL VERDICT")
    lines.append("")

    # Compute the key decision metrics
    best_wr = max(s_agg["wr"], op_agg["wr"])
    best_label = "Sonnet+Thinking" if s_agg["wr"] >= op_agg["wr"] else "Opus+Thinking"
    worst_label = "Opus+Thinking" if best_label == "Sonnet+Thinking" else "Sonnet+Thinking"

    # R-totals
    s_r = sum(t["r_multiple"] for i, t in enumerate(trades) if st_metrics[i]["decision"] == "CANDIDATE")
    o_r = sum(t["r_multiple"] for i, t in enumerate(trades) if ot_metrics[i]["decision"] == "CANDIDATE")
    orig_r = sum(t["r_multiple"] for i, t in enumerate(trades) if orig_metrics[i]["decision"] == "CANDIDATE")

    lines.append("| Model | CANDIDATEs | WR | R-Total | Cost/month |")
    lines.append("|-------|-----------|-----|---------|-----------|")
    lines.append(f"| Orig Sonnet | {o_agg['total_cand']} | {o_agg['wr']:.0%} | {orig_r:+.2f}R | ~$60 (batch) |")
    lines.append(f"| Sonnet+Thinking | {s_agg['total_cand']} | {s_agg['wr']:.0%} | {s_r:+.2f}R | ~$60 (batch) |")
    lines.append(f"| Opus+Thinking | {op_agg['total_cand']} | {op_agg['wr']:.0%} | {o_r:+.2f}R | ~$225 (batch) |")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# Main execution
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    args = parser.parse_args()

    trades = load_all_86_trades()
    logger.info(f"Total trades: {len(trades)}")
    wins = sum(1 for t in trades if t["outcome"] == "WIN")
    losses = sum(1 for t in trades if t["outcome"] == "LOSS")
    logger.info(f"  {wins}W {losses}L")

    prompt_index = load_all_prompts()
    raw_results = load_all_raw_results()
    logger.info(f"Prompts: {len(prompt_index)}, Raw results: {len(raw_results)}")

    # Build enriched prompts with session memory
    enriched = {}
    mem_counts = {}
    for t in trades:
        cid = t["custom_id"]
        prompt = prompt_index.get(cid)
        if not prompt:
            logger.warning(f"Missing prompt: {cid}")
            continue
        mem = build_session_memory(t["date"], t["kill_zone"], t["candle_time"], raw_results)
        user_msg = inject_memory(prompt["user_message"], mem)
        enriched[cid] = {"system": prompt["system"], "user_message": user_msg}
        mem_counts[cid] = len(mem.split("\n")) if mem else 0

    with_mem = sum(1 for v in mem_counts.values() if v > 0)
    logger.info(f"Enriched: {len(enriched)}, with session memory: {with_mem}")

    # Load original Sonnet results for baseline
    sonnet_orig = {}
    for t in trades:
        cid = t["custom_id"]
        raw = raw_results.get(cid)
        if raw:
            parsed = parse_response_text(raw)
            if parsed:
                sonnet_orig[cid] = {"status": "ok", "response": parsed, "raw": raw.get("text", "")}

    # Cost estimate
    # Sonnet+thinking: ~$0.04/call, Opus+thinking: ~$0.15/call
    est_sonnet = len(enriched) * 0.04
    est_opus = len(enriched) * 0.15
    logger.info(f"Cost estimate: Sonnet+T ${est_sonnet:.2f} + Opus+T ${est_opus:.2f} = ${est_sonnet + est_opus:.2f}")

    if args.dry_run:
        logger.info("DRY RUN complete.")
        return

    # Load checkpoint if resuming
    if args.resume:
        checkpoint = load_checkpoint()
        logger.info(f"Resuming: {len(checkpoint.get('sonnet_results', {}))} Sonnet, "
                     f"{len(checkpoint.get('opus_results', {}))} Opus completed")
    else:
        checkpoint = {"sonnet_results": {}, "opus_results": {}, "completed": []}

    client = anthropic.Anthropic()
    sonnet_results = checkpoint.get("sonnet_results", {})
    opus_results = checkpoint.get("opus_results", {})

    total = len(enriched)
    total_cost = 0

    # Run both models for each trade (interleaved for progress visibility)
    for i, t in enumerate(trades):
        cid = t["custom_id"]
        e = enriched.get(cid)
        if not e:
            continue

        # Sonnet+Thinking
        if cid not in sonnet_results:
            logger.info(f"[{i+1}/{total}] Sonnet+T: {cid} ({t['outcome']} {t['r_multiple']:+.2f}R)...")
            result = call_with_thinking(client, SONNET, e["system"], e["user_message"])
            # Store without thinking text for checkpoint size
            store = {k: v for k, v in result.items() if k != "thinking"}
            sonnet_results[cid] = store
            if result["status"] == "ok":
                cost = result.get("input_tokens", 0) * 3 / 1e6 + result.get("output_tokens", 0) * 15 / 1e6
                total_cost += cost
                dec = result["response"].get("decision", "?")
                conf = result["response"].get("confidence_score", 0)
                logger.info(f"  Sonnet+T → {dec} conf={conf} (${cost:.3f})")
            else:
                logger.warning(f"  Sonnet+T → {result['status']}")
            time.sleep(0.5)

        # Opus+Thinking
        if cid not in opus_results:
            logger.info(f"[{i+1}/{total}] Opus+T:   {cid} ({t['outcome']} {t['r_multiple']:+.2f}R)...")
            result = call_with_thinking(client, OPUS, e["system"], e["user_message"])
            store = {k: v for k, v in result.items() if k != "thinking"}
            opus_results[cid] = store
            if result["status"] == "ok":
                cost = result.get("input_tokens", 0) * 15 / 1e6 + result.get("output_tokens", 0) * 75 / 1e6
                total_cost += cost
                dec = result["response"].get("decision", "?")
                conf = result["response"].get("confidence_score", 0)
                logger.info(f"  Opus+T  → {dec} conf={conf} (${cost:.3f})")
            else:
                logger.warning(f"  Opus+T  → {result['status']}")
            time.sleep(0.5)

        # Checkpoint every 2 trades
        if (i + 1) % 2 == 0:
            checkpoint["sonnet_results"] = sonnet_results
            checkpoint["opus_results"] = opus_results
            save_checkpoint(checkpoint)
            logger.info(f"  Checkpoint saved ({i+1}/{total})")

    # Final save
    checkpoint["sonnet_results"] = sonnet_results
    checkpoint["opus_results"] = opus_results
    save_checkpoint(checkpoint)

    logger.info(f"Total cost: ${total_cost:.2f}")
    logger.info(f"Sonnet+T: {sum(1 for v in sonnet_results.values() if v.get('status')=='ok')}/{total} OK")
    logger.info(f"Opus+T:   {sum(1 for v in opus_results.values() if v.get('status')=='ok')}/{total} OK")

    # Build report
    report = build_report(trades, sonnet_orig, sonnet_results, opus_results)

    out_path = LEGACY_REPORT_DIR / "opus_full_86_comparison.md"
    with open(out_path, "w") as f:
        f.write(report)
    # Also save to test_b dir
    with open(OUTPUT_DIR / "opus_full_86_comparison.md", "w") as f:
        f.write(report)

    logger.info(f"Report saved to {out_path}")
    print("\n" + report)


if __name__ == "__main__":
    main()
