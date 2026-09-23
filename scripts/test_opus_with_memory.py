#!/usr/bin/env python3
"""Opus vs Sonnet with FULL session memory — the correct test.

Reconstructs session memory from stored batch results (prior candle Sonnet
responses), injects it into the CANDIDATE candle's prompt, and sends the
complete prompt to Opus via direct API calls.

Usage:
    python scripts/test_opus_with_memory.py --dry-run    # Show what would be sent
    python scripts/test_opus_with_memory.py               # Run all 20 trades
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
OUTPUT_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "test_b"
LEGACY_REPORT_DIR = (
    _PROJECT_ROOT
    / "research"
    / "archive"
    / "root_legacy_artifacts_2026_05_31"
    / "generated"
    / "model_comparison"
)
LEGACY_REPORT_DIR.mkdir(parents=True, exist_ok=True)

SONNET = "claude-sonnet-4-20250514"
OPUS = "claude-opus-4-20250514"

HEDGE_PHRASES = [
    "however", "although", "unclear", "mixed", "choppy",
    "minimal", "weak", "uncertain", "ambiguous", "borderline",
    "marginal", "questionable", "debatable", "possible", "might",
]


# ═══════════════════════════════════════════════════════════════════════
# Load batch data
# ═══════════════════════════════════════════════════════════════════════

def load_all_prompts() -> dict:
    """Load all pre-built prompts indexed by custom_id."""
    index = {}
    for fp in sorted(BATCH_API_DIR.glob("*_full_prompts.json")):
        try:
            for item in json.load(open(fp)):
                index[item["custom_id"]] = item["prompt"]
        except Exception as e:
            logger.warning(f"Failed {fp.name}: {e}")
    return index


def load_all_raw_results() -> dict:
    """Load all raw Sonnet results indexed by custom_id."""
    index = {}
    for fp in sorted(BATCH_API_DIR.glob("*_raw_results.json")):
        try:
            data = json.load(open(fp))
            for cid, result in data.items():
                index[cid] = result
        except Exception as e:
            logger.warning(f"Failed {fp.name}: {e}")
    return index


# ═══════════════════════════════════════════════════════════════════════
# Session memory reconstruction
# ═══════════════════════════════════════════════════════════════════════

def parse_sonnet_response(raw: dict) -> dict | None:
    """Parse a Sonnet response from raw_results into structured data."""
    text = raw.get("text", "")
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def compress_evaluation(parsed: dict) -> str:
    """Compress a PA response into session memory format (matches orchestrator)."""
    decision = parsed.get("decision", "?")
    if decision == "NO_TRADE":
        reason = parsed.get("no_trade_reason", "unknown") or "unknown"
        return f"NO_TRADE — {reason[:100]}"
    elif decision == "WAIT":
        reason = parsed.get("wait_reason", "unknown") or "unknown"
        return f"WAIT — {reason[:100]}"
    elif decision == "CANDIDATE":
        tp = parsed.get("trade_parameters")
        if not tp:
            return "CANDIDATE — null trade_parameters (demoted)"
        r = parsed.get("reasoning", {})
        grade = r.get("setup_grade", "?")
        conf = parsed.get("confidence_score", 0)
        direction = tp.get("direction", "?")
        entry = tp.get("entry_price", 0)
        sl = tp.get("stop_loss", 0)
        tp1 = tp.get("take_profit_1", 0)
        return (f"CANDIDATE ({grade}, conf={conf}) — "
                f"{direction} entry={entry}, SL={sl}, TP1={tp1}")
    return f"{decision}"


def build_session_memory(date: str, kz: str, target_time: str,
                         raw_results: dict) -> str:
    """Reconstruct session memory for a target candle from prior Sonnet responses.

    Finds all candles from the same date+kz that precede the target candle,
    parses their Sonnet responses, and formats as session memory.
    """
    prefix = f"{date}_{kz}_"
    # Find all candles from this session
    session_candles = sorted(
        cid for cid in raw_results.keys()
        if cid.startswith(prefix)
    )

    # Extract target time tag (HHMM)
    target_tag = target_time[11:16].replace(":", "")
    target_cid = f"{date}_{kz}_{target_tag}"

    # Get all prior candles (before the target)
    memory_entries = []
    for cid in session_candles:
        if cid >= target_cid:
            break  # Stop before target candle
        raw = raw_results.get(cid)
        if not raw:
            continue
        parsed = parse_sonnet_response(raw)
        if not parsed:
            continue

        # Extract time from custom_id: date_kz_HHMM -> HH:MM UTC
        time_tag = cid.split("_")[-1]
        time_str = f"{time_tag[:2]}:{time_tag[2:]} UTC"
        summary = compress_evaluation(parsed)
        memory_entries.append(f"- {time_str}: {summary}")

    # Keep last 6 (same as orchestrator)
    memory_entries = memory_entries[-6:]

    if not memory_entries:
        return ""
    return "\n".join(memory_entries)


def inject_session_memory(user_message: str, session_memory: str) -> str:
    """Inject session memory into a user message that doesn't have it."""
    if not session_memory:
        return user_message

    memory_block = (
        "\n## Prior Candle Assessments (this session)\n"
        "The following are your assessments of prior candles in this kill zone.\n"
        "Consider the progression: Is a setup developing across candles? "
        "Did a prior candle show a sweep or displacement that sets up the current candle? "
        "If you said WAIT or noted a developing pattern on a prior candle, "
        "check if the trigger has now occurred.\n\n"
        f"{session_memory}\n"
    )

    # Insert before "## Current Time:" marker
    marker = "## Current Time:"
    idx = user_message.find(marker)
    if idx >= 0:
        return user_message[:idx] + memory_block + "\n" + user_message[idx:]
    else:
        # Append before the final evaluation instruction
        return user_message + "\n" + memory_block


# ═══════════════════════════════════════════════════════════════════════
# Opus API calls
# ═══════════════════════════════════════════════════════════════════════

def call_opus(client: anthropic.Anthropic, system_blocks: list, user_message: str,
              trade_id: str) -> dict:
    """Send a single prompt to Opus via direct API call."""
    try:
        response = client.messages.create(
            model=OPUS,
            max_tokens=2500,
            temperature=0,
            system=system_blocks,
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```\w*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        parsed = json.loads(text)
        return {
            "status": "ok",
            "response": parsed,
            "raw": text,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
    except json.JSONDecodeError:
        return {"status": "parse_error", "raw": text}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def extract_metrics(resp: dict) -> dict:
    if not resp or resp.get("status") != "ok":
        return {"decision": "ERROR", "confidence": 0, "grade": "?",
                "reasoning_words": 0, "price_levels": 0, "hedges": 0,
                "no_trade_reason": "", "risks": ""}

    r = resp["response"]
    reasoning = r.get("reasoning", {})
    overall = reasoning.get("overall_reasoning", "")
    raw = resp.get("raw", "")

    price_pattern = re.findall(r'\d{4}\.\d{1,2}', raw)
    raw_lower = raw.lower()
    hedge_count = sum(raw_lower.count(h) for h in HEDGE_PHRASES)

    risks = []
    for section_name in ["daily_bias", "h4_alignment", "h1_setup", "m15_confirmation"]:
        section = reasoning.get(section_name, {})
        expl = section.get("explanation", "")
        if any(h in expl.lower() for h in ["risk", "concern", "caution", "weak", "unclear", "conflict"]):
            risks.append(f"{section_name}: {expl[:80]}")

    return {
        "decision": r.get("decision", "?"),
        "confidence": r.get("confidence_score", 0),
        "grade": reasoning.get("setup_grade", "?"),
        "framework": r.get("framework", "?"),
        "reasoning_words": len(overall.split()),
        "price_levels": len(set(price_pattern)),
        "hedges": hedge_count,
        "no_trade_reason": r.get("no_trade_reason", "") or "",
        "risks": "; ".join(risks) if risks else "",
        "displacement_quality": reasoning.get("m15_confirmation", {}).get("displacement_quality", "?"),
        "overall_reasoning": overall,
    }


# ═══════════════════════════════════════════════════════════════════════
# Report generation
# ═══════════════════════════════════════════════════════════════════════

def build_report(trades: list[dict], sonnet_data: dict, opus_data: dict,
                 memory_lengths: dict) -> str:
    lines = []
    lines.append("# Opus vs Sonnet — With Full Session Memory")
    lines.append(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Sonnet: {SONNET} (original batch responses)")
    lines.append(f"Opus: {OPUS} (fresh API calls with reconstructed session memory)")
    lines.append(f"Trades: {len(trades)} (10 best winners + 10 worst losers)")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("Session memory was reconstructed from stored batch results: for each")
    lines.append("CANDIDATE candle, the Sonnet responses from all prior candles in the")
    lines.append("same kill zone were compressed into memory entries (matching the")
    lines.append("production orchestrator's format) and injected into the user message.")
    lines.append("Opus received the IDENTICAL system prompt, static context, dynamic")
    lines.append("market data, AND session memory context.")
    lines.append("")

    # Decision table
    lines.append("## Decision Comparison")
    lines.append("")
    lines.append("| # | Date | KZ | Actual | R | Memory | Sonnet | S.Conf | Opus | O.Conf | Match? |")
    lines.append("|---|------|----|--------|-----|--------|--------|--------|------|--------|--------|")

    sonnet_metrics_list = []
    opus_metrics_list = []
    matches = 0

    for i, t in enumerate(trades):
        cid = t["custom_id"]
        sm = sonnet_data.get(cid, {})
        om = opus_data.get(cid, {})
        s_m = extract_metrics(sm)
        o_m = extract_metrics(om)
        sonnet_metrics_list.append(s_m)
        opus_metrics_list.append(o_m)

        match = s_m["decision"] == o_m["decision"]
        if match:
            matches += 1

        mem_len = memory_lengths.get(cid, 0)
        lines.append(f"| {i+1} | {t['date']} | {t['kill_zone']:>3} | {t['outcome']:>5} | "
                     f"{t['r_multiple']:+.2f} | {mem_len} prior | "
                     f"{s_m['decision']:<10} | {s_m['confidence']:>4} | "
                     f"{o_m['decision']:<10} | {o_m['confidence']:>4} | "
                     f"{'YES' if match else '**NO**'} |")

    lines.append("")
    lines.append(f"Decision agreement: {matches}/{len(trades)} ({matches/len(trades):.0%})")

    # Winner/Loser breakdown
    winners = [t for t in trades if t["outcome"] == "WIN"]
    losers = [t for t in trades if t["outcome"] == "LOSS"]

    s_win_cands = sum(1 for i, t in enumerate(trades) if t["outcome"] == "WIN" and sonnet_metrics_list[i]["decision"] == "CANDIDATE")
    s_loss_cands = sum(1 for i, t in enumerate(trades) if t["outcome"] == "LOSS" and sonnet_metrics_list[i]["decision"] == "CANDIDATE")
    o_win_cands = sum(1 for i, t in enumerate(trades) if t["outcome"] == "WIN" and opus_metrics_list[i]["decision"] == "CANDIDATE")
    o_loss_cands = sum(1 for i, t in enumerate(trades) if t["outcome"] == "LOSS" and opus_metrics_list[i]["decision"] == "CANDIDATE")

    s_total = s_win_cands + s_loss_cands
    o_total = o_win_cands + o_loss_cands

    lines.append("")
    lines.append("## Selectivity Comparison")
    lines.append("")
    lines.append("| Metric | Sonnet | Opus |")
    lines.append("|--------|--------|------|")
    lines.append(f"| Total CANDIDATEs | {s_total}/20 | {o_total}/20 |")
    lines.append(f"| Winners caught | {s_win_cands}/10 | {o_win_cands}/10 |")
    lines.append(f"| Losers approved | {s_loss_cands}/10 | {o_loss_cands}/10 |")
    if s_total > 0:
        lines.append(f"| CANDIDATE WR | {s_win_cands}/{s_total} = {s_win_cands/s_total:.0%} | "
                     f"{o_win_cands}/{max(1,o_total)} = {o_win_cands/max(1,o_total):.0%} |")
    lines.append("")

    # R-impact
    lines.append("## R-Impact Analysis")
    lines.append("")
    s_r = 0
    o_r = 0
    for i, t in enumerate(trades):
        sm = sonnet_metrics_list[i]
        om = opus_metrics_list[i]
        if sm["decision"] == "CANDIDATE":
            s_r += t["r_multiple"]
        if om["decision"] == "CANDIDATE":
            o_r += t["r_multiple"]

    lines.append(f"- Sonnet CANDIDATE R-total: {s_r:+.2f}R on {s_total} trades")
    lines.append(f"- Opus CANDIDATE R-total: {o_r:+.2f}R on {o_total} trades")
    lines.append(f"- Delta: {o_r - s_r:+.2f}R")
    lines.append("")

    # Confidence comparison
    lines.append("## Confidence Score Comparison")
    lines.append("")
    s_confs = [m["confidence"] for m in sonnet_metrics_list if m["confidence"] > 0]
    o_confs = [m["confidence"] for m in opus_metrics_list if m["confidence"] > 0]

    if s_confs:
        s_mean = sum(s_confs) / len(s_confs)
        s_std = (sum((c - s_mean)**2 for c in s_confs) / len(s_confs))**0.5
        lines.append(f"Sonnet: n={len(s_confs)}, mean={s_mean:.0f}, std={s_std:.1f}, range=[{min(s_confs)}, {max(s_confs)}]")
    if o_confs:
        o_mean = sum(o_confs) / len(o_confs)
        o_std = (sum((c - o_mean)**2 for c in o_confs) / len(o_confs))**0.5
        lines.append(f"Opus:   n={len(o_confs)}, mean={o_mean:.0f}, std={o_std:.1f}, range=[{min(o_confs)}, {max(o_confs)}]")
    else:
        lines.append("Opus: No CANDIDATE confidence scores to compare")
    lines.append("")

    # Detailed loser analysis
    lines.append("## Loser Analysis — Does Opus Catch What Sonnet Missed?")
    lines.append("")
    for i, t in enumerate(trades):
        if t["outcome"] != "LOSS":
            continue
        sm = sonnet_metrics_list[i]
        om = opus_metrics_list[i]
        lines.append(f"### {t['date']} ({t['kill_zone']}) — LOSS {t['r_multiple']:+.2f}R")
        lines.append(f"- Sonnet: {sm['decision']} (conf={sm['confidence']}, grade={sm['grade']})")
        lines.append(f"- Opus:   {om['decision']} (conf={om['confidence']}, grade={om['grade']})")
        if sm["decision"] == "CANDIDATE" and om["decision"] != "CANDIDATE":
            lines.append(f"  **OPUS CAUGHT IT** — rejected a loser Sonnet approved")
            if om["no_trade_reason"]:
                lines.append(f"  Opus reason: {om['no_trade_reason']}")
        elif sm["decision"] == om["decision"] == "CANDIDATE":
            lines.append(f"  Both approved — same rubber stamp")
        elif sm["decision"] == om["decision"] == "NO_TRADE":
            lines.append(f"  Both rejected (no session memory context may have changed this)")
        lines.append("")

    # Winner analysis
    lines.append("## Winner Analysis — Does Opus Still Catch Winners?")
    lines.append("")
    for i, t in enumerate(trades):
        if t["outcome"] != "WIN":
            continue
        sm = sonnet_metrics_list[i]
        om = opus_metrics_list[i]
        lines.append(f"### {t['date']} ({t['kill_zone']}) — WIN {t['r_multiple']:+.2f}R")
        lines.append(f"- Sonnet: {sm['decision']} (conf={sm['confidence']}, grade={sm['grade']})")
        lines.append(f"- Opus:   {om['decision']} (conf={om['confidence']}, grade={om['grade']})")
        if sm["decision"] == "CANDIDATE" and om["decision"] != "CANDIDATE":
            lines.append(f"  **OPUS MISSED** a +{t['r_multiple']:.2f}R winner")
            if om["no_trade_reason"]:
                lines.append(f"  Opus reason: {om['no_trade_reason']}")
        elif om["decision"] == "CANDIDATE" and sm["decision"] != "CANDIDATE":
            lines.append(f"  **OPUS FOUND** a winner Sonnet missed")
        lines.append("")

    # Reasoning quality
    lines.append("## Reasoning Quality Comparison")
    lines.append("")
    lines.append("| Metric | Sonnet (avg) | Opus (avg) |")
    lines.append("|--------|-------------|-----------|")
    s_words = [m["reasoning_words"] for m in sonnet_metrics_list]
    o_words = [m["reasoning_words"] for m in opus_metrics_list]
    s_prices = [m["price_levels"] for m in sonnet_metrics_list]
    o_prices = [m["price_levels"] for m in opus_metrics_list]
    s_hedges = [m["hedges"] for m in sonnet_metrics_list]
    o_hedges = [m["hedges"] for m in opus_metrics_list]
    lines.append(f"| Reasoning words | {sum(s_words)/len(s_words):.0f} | {sum(o_words)/len(o_words):.0f} |")
    lines.append(f"| Price levels cited | {sum(s_prices)/len(s_prices):.1f} | {sum(o_prices)/len(o_prices):.1f} |")
    lines.append(f"| Hedge phrases | {sum(s_hedges)/len(s_hedges):.1f} | {sum(o_hedges)/len(o_hedges):.1f} |")
    lines.append("")

    # Cost analysis
    lines.append("## Cost-Benefit Analysis")
    lines.append("")
    lines.append("Current Sonnet cost: ~$60/month for 5 instruments")
    lines.append("Opus cost would be: ~$180/month (3x)")
    lines.append("")

    if o_total > 0 and o_win_cands / o_total > s_win_cands / max(1, s_total) + 0.05:
        wr_delta = o_win_cands / o_total - s_win_cands / max(1, s_total)
        lines.append(f"Opus WR improvement: +{wr_delta:.0%}")
        lines.append(f"At 1% risk on $100K ($1,000/trade), each +1pp WR ≈ $10/trade")
        lines.append(f"Break-even at ~{120 / max(0.01, wr_delta * 10 * o_total):.0f} trades/month")
    else:
        lines.append("No clear WR improvement from Opus.")
    lines.append("")

    # Final recommendation
    lines.append("## Recommendation")
    lines.append("")
    if o_total == 0:
        lines.append("**DO NOT SWITCH** — Opus produced zero CANDIDATEs even with session memory.")
    elif o_win_cands >= 7 and o_loss_cands <= 3:
        lines.append(f"**SWITCH TO OPUS** — Opus catches {o_win_cands}/10 winners while rejecting "
                     f"{10 - o_loss_cands}/10 losers. Clear discrimination improvement.")
    elif o_win_cands >= s_win_cands and o_loss_cands < s_loss_cands:
        lines.append(f"**CONSIDER OPUS** — Better selectivity ({o_win_cands}W/{o_loss_cands}L vs "
                     f"{s_win_cands}W/{s_loss_cands}L). Run larger sample to confirm.")
    elif o_total >= s_total * 0.8 and abs(o_win_cands/max(1,o_total) - s_win_cands/max(1,s_total)) < 0.1:
        lines.append("**NO SWITCH** — Same performance, not worth 3x cost.")
    else:
        lines.append("**EVALUATE FURTHER** — Mixed results, need larger sample.")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    trades = json.load(open(OUTPUT_DIR / "opus_retest_trades.json"))
    logger.info(f"Loaded {len(trades)} trades")

    prompt_index = load_all_prompts()
    raw_results = load_all_raw_results()
    logger.info(f"Prompts: {len(prompt_index)}, Raw results: {len(raw_results)}")

    # Reconstruct session memory for each trade and verify
    memory_map = {}
    for t in trades:
        mem = build_session_memory(t["date"], t["kill_zone"], t["candle_time"], raw_results)
        memory_map[t["custom_id"]] = mem
        entry_count = len(mem.split("\n")) if mem else 0
        logger.info(f"  {t['custom_id']}: {entry_count} memory entries")

    # Build enriched prompts
    enriched = {}
    for t in trades:
        cid = t["custom_id"]
        prompt = prompt_index.get(cid)
        if not prompt:
            logger.warning(f"Missing prompt: {cid}")
            continue
        mem = memory_map.get(cid, "")
        user_msg = inject_session_memory(prompt["user_message"], mem)
        enriched[cid] = {
            "system": prompt["system"],
            "user_message": user_msg,
            "memory_entries": len(mem.split("\n")) if mem else 0,
        }

    # Verify session memory is present
    with_memory = sum(1 for v in enriched.values() if v["memory_entries"] > 0)
    logger.info(f"Trades with session memory: {with_memory}/{len(enriched)}")

    # Extract Sonnet responses from raw_results for comparison
    sonnet_data = {}
    for t in trades:
        cid = t["custom_id"]
        raw = raw_results.get(cid)
        if raw:
            parsed = parse_sonnet_response(raw)
            if parsed:
                sonnet_data[cid] = {"status": "ok", "response": parsed, "raw": raw.get("text", "")}
            else:
                sonnet_data[cid] = {"status": "parse_error"}

    # Cost estimate
    # Opus: $15/1M input, $75/1M output, direct (no batch discount)
    avg_input = 5000  # ~5K tokens with session memory
    avg_output = 1500
    cost = 20 * (avg_input * 15 / 1e6 + avg_output * 75 / 1e6)
    logger.info(f"Estimated cost: ${cost:.2f} (20 direct Opus calls)")

    if args.dry_run:
        logger.info("DRY RUN — showing sample enriched prompt")
        sample_cid = trades[0]["custom_id"]
        sample = enriched.get(sample_cid, {})
        umsg = sample.get("user_message", "")
        has_mem = "Prior Candle Assessments" in umsg
        logger.info(f"  Sample: {sample_cid}")
        logger.info(f"  User message length: {len(umsg)} chars")
        logger.info(f"  Has session memory block: {has_mem}")
        if has_mem:
            idx = umsg.find("Prior Candle Assessments")
            end_idx = umsg.find("##", idx + 10)
            if end_idx < 0:
                end_idx = idx + 500
            logger.info(f"  Memory block:\n{umsg[idx:end_idx]}")
        return

    # Run Opus calls
    client = anthropic.Anthropic()
    opus_data = {}
    total_cost = 0

    for i, t in enumerate(trades):
        cid = t["custom_id"]
        e = enriched.get(cid)
        if not e:
            continue

        logger.info(f"[{i+1}/20] Calling Opus for {cid} ({t['outcome']} {t['r_multiple']:+.2f}R)...")
        result = call_opus(client, e["system"], e["user_message"], cid)
        opus_data[cid] = result

        if result["status"] == "ok":
            dec = result["response"].get("decision", "?")
            conf = result["response"].get("confidence_score", 0)
            in_tok = result.get("input_tokens", 0)
            out_tok = result.get("output_tokens", 0)
            call_cost = in_tok * 15 / 1e6 + out_tok * 75 / 1e6
            total_cost += call_cost
            logger.info(f"  → {dec} conf={conf} (${call_cost:.3f})")
        else:
            logger.warning(f"  → {result['status']}: {result.get('error', result.get('raw', '')[:100])}")

        # Small delay to avoid rate limits
        if i < len(trades) - 1:
            time.sleep(1)

    logger.info(f"Total Opus cost: ${total_cost:.2f}")

    # Save raw results
    with open(OUTPUT_DIR / "opus_retest_results.json", "w") as f:
        json.dump({"sonnet": sonnet_data, "opus": opus_data, "cost": total_cost}, f, indent=2)

    # Build report
    memory_lengths = {cid: enriched[cid]["memory_entries"] for cid in enriched}
    report = build_report(trades, sonnet_data, opus_data, memory_lengths)

    out_path = LEGACY_REPORT_DIR / "opus_vs_sonnet_with_memory.md"
    with open(out_path, "w") as f:
        f.write(report)
    logger.info(f"Report saved to {out_path}")
    print("\n" + report)


if __name__ == "__main__":
    main()
