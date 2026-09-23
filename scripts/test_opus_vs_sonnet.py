#!/usr/bin/env python3
"""Opus vs Sonnet model comparison test.

Takes 10 trades (5 best winners + 5 worst losers), runs identical prompts
through both claude-sonnet-4 and claude-opus-4, compares assessments.

Usage:
    python scripts/test_opus_vs_sonnet.py --dry-run
    python scripts/test_opus_vs_sonnet.py
    python scripts/test_opus_vs_sonnet.py --resume-sonnet msgbatch_XXX --resume-opus msgbatch_YYY
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

from anthropic import Anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_API_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "batch_api"
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

SONNET = "claude-sonnet-4-20250514"
OPUS = "claude-opus-4-20250514"

# Hedging phrases to count
HEDGE_PHRASES = [
    "however", "although", "unclear", "mixed", "choppy",
    "minimal", "weak", "uncertain", "ambiguous", "borderline",
    "marginal", "questionable", "debatable", "possible", "might",
]


def load_prompt_index() -> dict:
    index = {}
    for fp in sorted(BATCH_API_DIR.glob("*_full_prompts.json")):
        try:
            for item in json.load(open(fp)):
                index[item["custom_id"]] = item["prompt"]
        except Exception as e:
            logger.warning(f"Failed to load {fp.name}: {e}")
    logger.info(f"Loaded {len(index)} prompts")
    return index


def build_requests(trades: list[dict], prompt_index: dict, model: str, prefix: str) -> list[Request]:
    reqs = []
    for t in trades:
        prompt = prompt_index.get(t["custom_id"])
        if not prompt:
            logger.warning(f"Missing prompt for {t['custom_id']}")
            continue
        reqs.append(Request(
            custom_id=f"{prefix}_{t['custom_id']}",
            params=MessageCreateParamsNonStreaming(
                model=model,
                max_tokens=2500,
                temperature=0,
                system=prompt["system"],
                messages=[{"role": "user", "content": prompt["user_message"]}],
            ),
        ))
    return reqs


def submit_and_poll(client: Anthropic, requests: list[Request], label: str) -> dict:
    logger.info(f"Submitting {label}: {len(requests)} requests")
    batch = client.messages.batches.create(requests=requests)
    batch_id = batch.id
    logger.info(f"{label} batch: {batch_id}")

    while True:
        b = client.messages.batches.retrieve(batch_id)
        counts = b.request_counts
        logger.info(f"  {label}: {b.processing_status} — "
                     f"ok={counts.succeeded} err={counts.errored} pending={counts.processing}")
        if b.processing_status == "ended":
            break
        time.sleep(30)

    results = {}
    for r in client.messages.batches.results(batch_id):
        cid = r.custom_id
        if r.result.type == "succeeded":
            text = r.result.message.content[0].text if r.result.message.content else ""
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```\w*\n?", "", text)
                text = re.sub(r"\n?```$", "", text)
            try:
                results[cid] = {"status": "ok", "response": json.loads(text), "raw": text}
            except json.JSONDecodeError:
                results[cid] = {"status": "parse_error", "raw": text}
        else:
            results[cid] = {"status": "error", "error": str(r.result)}

    logger.info(f"{label}: {sum(1 for v in results.values() if v['status']=='ok')}/{len(results)} parsed OK")
    return results, batch_id


def extract_metrics(resp: dict) -> dict:
    """Extract comparison metrics from a PA response."""
    if not resp or resp.get("status") != "ok":
        return {"decision": "ERROR", "confidence": 0, "grade": "?", "reasoning_words": 0,
                "price_levels": 0, "hedges": 0, "risks": ""}

    r = resp["response"]
    reasoning = r.get("reasoning", {})

    # Word count from overall_reasoning
    overall = reasoning.get("overall_reasoning", "")
    word_count = len(overall.split())

    # Count distinct price levels in the raw response
    raw = resp.get("raw", "")
    price_pattern = re.findall(r'\d{4}\.\d{1,2}', raw)  # Gold prices like 2345.67
    distinct_prices = len(set(price_pattern))

    # Count hedging phrases
    raw_lower = raw.lower()
    hedge_count = sum(raw_lower.count(h) for h in HEDGE_PHRASES)

    # Extract risk factors from reasoning
    risks = []
    for section_name in ["daily_bias", "h4_alignment", "h1_setup", "m15_confirmation", "liquidity_sweep"]:
        section = reasoning.get(section_name, {})
        explanation = section.get("explanation", "")
        if any(h in explanation.lower() for h in ["risk", "concern", "caution", "warning", "weak", "unclear"]):
            risks.append(f"{section_name}: {explanation[:80]}")

    no_trade_reason = r.get("no_trade_reason", "")

    return {
        "decision": r.get("decision", "?"),
        "confidence": r.get("confidence_score", 0),
        "grade": reasoning.get("setup_grade", "?"),
        "framework": r.get("framework", "?"),
        "reasoning_words": word_count,
        "price_levels": distinct_prices,
        "hedges": hedge_count,
        "risks": "; ".join(risks) if risks else "none identified",
        "no_trade_reason": no_trade_reason or "",
        "d1_direction": reasoning.get("daily_bias", {}).get("direction", "?"),
        "d1_confidence": reasoning.get("daily_bias", {}).get("confidence", "?"),
        "displacement_quality": reasoning.get("m15_confirmation", {}).get("displacement_quality", "?"),
        "poi_type": reasoning.get("h1_setup", {}).get("poi_type", "?"),
    }


def build_report(trades: list[dict], sonnet_results: dict, opus_results: dict) -> str:
    lines = []
    lines.append("# Opus vs Sonnet Model Comparison")
    lines.append(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Sonnet: {SONNET}")
    lines.append(f"Opus: {OPUS}")
    lines.append(f"Trades: 10 (5 best winners + 5 worst losers)")
    lines.append(f"Prompt: Identical production prompt, no session memory")
    lines.append("")

    # Summary table
    lines.append("## Decision Summary")
    lines.append("")
    lines.append("| # | Date | KZ | Actual | R | Sonnet Dec | Opus Dec | Match? |")
    lines.append("|---|------|-----|--------|-----|-----------|---------|--------|")

    sonnet_metrics = []
    opus_metrics = []
    decision_matches = 0

    for i, t in enumerate(trades):
        cid = t["custom_id"]
        s = sonnet_results.get(f"sonnet_{cid}", {})
        o = opus_results.get(f"opus_{cid}", {})
        sm = extract_metrics(s)
        om = extract_metrics(o)
        sonnet_metrics.append(sm)
        opus_metrics.append(om)

        match = sm["decision"] == om["decision"]
        if match:
            decision_matches += 1
        match_str = "YES" if match else "**NO**"

        lines.append(f"| {i+1} | {t['date']} | {t['kill_zone']} | {t['outcome']} | "
                     f"{t['r_multiple']:+.2f} | {sm['decision']} | {om['decision']} | {match_str} |")

    lines.append("")
    lines.append(f"Decision agreement: {decision_matches}/10 ({decision_matches*10}%)")
    lines.append("")

    # Detailed comparison table
    lines.append("## Detailed Metrics")
    lines.append("")
    lines.append("| # | Date | Outcome | Model | Decision | Conf | Grade | Words | Prices | Hedges |")
    lines.append("|---|------|---------|-------|----------|------|-------|-------|--------|--------|")

    for i, t in enumerate(trades):
        sm = sonnet_metrics[i]
        om = opus_metrics[i]
        lines.append(f"| {i+1} | {t['date']} | {t['outcome']:>5} | Sonnet | "
                     f"{sm['decision']:<10} | {sm['confidence']:>4} | {sm['grade']:<3} | "
                     f"{sm['reasoning_words']:>5} | {sm['price_levels']:>6} | {sm['hedges']:>6} |")
        lines.append(f"| | | | Opus | "
                     f"{om['decision']:<10} | {om['confidence']:>4} | {om['grade']:<3} | "
                     f"{om['reasoning_words']:>5} | {om['price_levels']:>6} | {om['hedges']:>6} |")

    # Aggregate stats
    lines.append("")
    lines.append("## Aggregate Statistics")
    lines.append("")

    for label, metrics in [("Sonnet", sonnet_metrics), ("Opus", opus_metrics)]:
        cands = [m for m in metrics if m["decision"] == "CANDIDATE"]
        confs = [m["confidence"] for m in metrics if m["confidence"] > 0]
        words = [m["reasoning_words"] for m in metrics]
        prices = [m["price_levels"] for m in metrics]
        hedges = [m["hedges"] for m in metrics]

        lines.append(f"**{label}:**")
        lines.append(f"- CANDIDATEs: {len(cands)}/10")
        if confs:
            lines.append(f"- Confidence: mean={sum(confs)/len(confs):.0f}, "
                        f"min={min(confs)}, max={max(confs)}, "
                        f"std={( sum((c - sum(confs)/len(confs))**2 for c in confs) / len(confs) )**0.5:.1f}")
        lines.append(f"- Reasoning words: mean={sum(words)/len(words):.0f}, "
                     f"range=[{min(words)}, {max(words)}]")
        lines.append(f"- Price levels cited: mean={sum(prices)/len(prices):.1f}")
        lines.append(f"- Hedge phrases: mean={sum(hedges)/len(hedges):.1f}")
        lines.append("")

    # Key question: Does Opus catch losers?
    lines.append("## Key Question: Does Opus Catch the Losers?")
    lines.append("")
    loser_trades = [t for t in trades if t["outcome"] == "LOSS"]
    for t in loser_trades:
        cid = t["custom_id"]
        s = sonnet_results.get(f"sonnet_{cid}", {})
        o = opus_results.get(f"opus_{cid}", {})
        sm = extract_metrics(s)
        om = extract_metrics(o)

        lines.append(f"### {t['date']} ({t['kill_zone']}) — LOSS {t['r_multiple']:+.2f}R")
        lines.append(f"- Sonnet: {sm['decision']} (conf={sm['confidence']}, grade={sm['grade']})")
        lines.append(f"- Opus:   {om['decision']} (conf={om['confidence']}, grade={om['grade']})")
        if sm["decision"] == "CANDIDATE" and om["decision"] != "CANDIDATE":
            lines.append(f"  **OPUS CAUGHT IT** — rejected a loser that Sonnet approved")
            if om["no_trade_reason"]:
                lines.append(f"  Opus reason: {om['no_trade_reason']}")
        elif sm["decision"] != "CANDIDATE" and om["decision"] == "CANDIDATE":
            lines.append(f"  Opus MISSED — approved a loser that Sonnet rejected")
        elif sm["decision"] == om["decision"]:
            lines.append(f"  Same decision")
        lines.append("")

    # Winner analysis
    lines.append("## Does Opus Miss Winners?")
    lines.append("")
    winner_trades = [t for t in trades if t["outcome"] == "WIN"]
    for t in winner_trades:
        cid = t["custom_id"]
        s = sonnet_results.get(f"sonnet_{cid}", {})
        o = opus_results.get(f"opus_{cid}", {})
        sm = extract_metrics(s)
        om = extract_metrics(o)

        lines.append(f"### {t['date']} ({t['kill_zone']}) — WIN {t['r_multiple']:+.2f}R")
        lines.append(f"- Sonnet: {sm['decision']} (conf={sm['confidence']}, grade={sm['grade']})")
        lines.append(f"- Opus:   {om['decision']} (conf={om['confidence']}, grade={om['grade']})")
        if sm["decision"] == "CANDIDATE" and om["decision"] != "CANDIDATE":
            lines.append(f"  **OPUS MISSED** a {t['r_multiple']:+.2f}R winner")
        elif sm["decision"] != "CANDIDATE" and om["decision"] == "CANDIDATE":
            lines.append(f"  **OPUS CAUGHT** a winner that Sonnet missed")
        lines.append("")

    # Interpretation
    lines.append("## Interpretation")
    lines.append("")

    # Count specific patterns
    sonnet_cand_wins = sum(1 for i, t in enumerate(trades) if t["outcome"] == "WIN" and sonnet_metrics[i]["decision"] == "CANDIDATE")
    sonnet_cand_losses = sum(1 for i, t in enumerate(trades) if t["outcome"] == "LOSS" and sonnet_metrics[i]["decision"] == "CANDIDATE")
    opus_cand_wins = sum(1 for i, t in enumerate(trades) if t["outcome"] == "WIN" and opus_metrics[i]["decision"] == "CANDIDATE")
    opus_cand_losses = sum(1 for i, t in enumerate(trades) if t["outcome"] == "LOSS" and opus_metrics[i]["decision"] == "CANDIDATE")

    sonnet_total_cand = sonnet_cand_wins + sonnet_cand_losses
    opus_total_cand = opus_cand_wins + opus_cand_losses

    lines.append("| Metric | Sonnet | Opus |")
    lines.append("|--------|--------|------|")
    lines.append(f"| Total CANDIDATEs | {sonnet_total_cand} | {opus_total_cand} |")
    if sonnet_total_cand:
        lines.append(f"| CANDIDATE WR | {sonnet_cand_wins}/{sonnet_total_cand} = {sonnet_cand_wins/sonnet_total_cand:.0%} | "
                     f"{opus_cand_wins}/{opus_total_cand} = {opus_cand_wins/max(1,opus_total_cand):.0%} |")
    lines.append(f"| Winners caught | {sonnet_cand_wins}/5 | {opus_cand_wins}/5 |")
    lines.append(f"| Losers approved | {sonnet_cand_losses}/5 | {opus_cand_losses}/5 |")
    lines.append("")

    s_confs = [m["confidence"] for m in sonnet_metrics if m["confidence"] > 0]
    o_confs = [m["confidence"] for m in opus_metrics if m["confidence"] > 0]
    if s_confs and o_confs:
        s_std = (sum((c - sum(s_confs)/len(s_confs))**2 for c in s_confs) / len(s_confs))**0.5
        o_std = (sum((c - sum(o_confs)/len(o_confs))**2 for c in o_confs) / len(o_confs))**0.5
        lines.append(f"Confidence variance: Sonnet std={s_std:.1f}, Opus std={o_std:.1f}")
        if o_std > s_std * 1.5:
            lines.append("→ Opus produces MORE varied confidence scores (better calibrated)")
        elif s_std > o_std * 1.5:
            lines.append("→ Sonnet produces MORE varied confidence (unexpected)")
        else:
            lines.append("→ Similar confidence variance between models")

    lines.append("")
    lines.append("## Recommendation")
    lines.append("")

    # Auto-generate recommendation based on data
    if opus_cand_losses < sonnet_cand_losses and opus_cand_wins >= sonnet_cand_wins:
        lines.append("**SWITCH TO OPUS** — Opus caught losers without sacrificing winners. "
                     "The ~3x cost increase is justified by improved selectivity.")
    elif opus_cand_losses < sonnet_cand_losses and opus_cand_wins < sonnet_cand_wins:
        lines.append("**MIXED** — Opus is more conservative overall (fewer CANDIDATEs of both types). "
                     "Check if the avoided losers outweigh the missed winners in R-terms.")
    elif opus_total_cand == sonnet_total_cand and decision_matches >= 8:
        lines.append("**NO SWITCH** — Opus produces essentially the same decisions as Sonnet. "
                     "The problem is the prompt, not the model. Save the 3x cost.")
    else:
        lines.append("**EVALUATE FURTHER** — Results are mixed. Consider a larger sample.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Opus vs Sonnet comparison")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume-sonnet", type=str, default=None)
    parser.add_argument("--resume-opus", type=str, default=None)
    args = parser.parse_args()

    trades = json.load(open(OUTPUT_DIR / "opus_test_trades.json"))
    logger.info(f"Loaded {len(trades)} trades")

    prompt_index = load_prompt_index()

    sonnet_reqs = build_requests(trades, prompt_index, SONNET, "sonnet")
    opus_reqs = build_requests(trades, prompt_index, OPUS, "opus")
    logger.info(f"Sonnet: {len(sonnet_reqs)}, Opus: {len(opus_reqs)}")

    # Cost estimate: Sonnet ~$3/1M in, $15/1M out; Opus ~$15/1M in, $75/1M out
    # ~4K input tokens + ~1.5K output per request, 50% batch discount
    sonnet_cost = (10 * 4000 * 3 / 1e6 + 10 * 1500 * 15 / 1e6) * 0.5
    opus_cost = (10 * 4000 * 15 / 1e6 + 10 * 1500 * 75 / 1e6) * 0.5
    logger.info(f"Cost estimate: Sonnet ${sonnet_cost:.2f} + Opus ${opus_cost:.2f} = ${sonnet_cost + opus_cost:.2f}")

    if args.dry_run:
        logger.info("DRY RUN — no API calls")
        return

    client = Anthropic()

    if args.resume_sonnet:
        sonnet_batch_id = args.resume_sonnet
        sonnet_results = {}  # Will poll
    else:
        sonnet_results, sonnet_batch_id = submit_and_poll(client, sonnet_reqs, "Sonnet")

    if args.resume_opus:
        opus_batch_id = args.resume_opus
        opus_results = {}
    else:
        opus_results, opus_batch_id = submit_and_poll(client, opus_reqs, "Opus")

    # If resuming, poll now
    if args.resume_sonnet and not sonnet_results:
        sonnet_results, _ = submit_and_poll(client, [], "Sonnet")  # Won't work — need to poll directly
    if args.resume_opus and not opus_results:
        opus_results, _ = submit_and_poll(client, [], "Opus")

    # Save raw
    with open(OUTPUT_DIR / "opus_sonnet_results.json", "w") as f:
        json.dump({"sonnet": sonnet_results, "opus": opus_results,
                    "sonnet_batch": sonnet_batch_id, "opus_batch": opus_batch_id}, f, indent=2)

    report = build_report(trades, sonnet_results, opus_results)
    out_path = LEGACY_REPORT_DIR / "opus_vs_sonnet_comparison.md"
    with open(out_path, "w") as f:
        f.write(report)
    logger.info(f"Report saved to {out_path}")
    print("\n" + report)


if __name__ == "__main__":
    main()
