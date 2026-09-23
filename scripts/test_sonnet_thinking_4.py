#!/usr/bin/env python3
"""Quick 4-trade test: Sonnet with extended thinking vs Opus on diagnostic losers.

Tests whether Sonnet+thinking catches the same criteria violations that Opus found.
"""

import json
import logging
import re
import sys
import time
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

# The 4 diagnostic trades
TRADES = [
    {"custom_id": "2024-06-05_ny_1445", "outcome": "LOSS", "r": -1.0,
     "opus_reason": "Price not at required H1 point of interest for setup qualification"},
    {"custom_id": "2024-09-27_ny_1400", "outcome": "LOSS", "r": -1.0,
     "opus_reason": "No qualifying setup - H1 OBs too far below in discount, no liquidity sweep detected"},
    {"custom_id": "2025-03-14_london_0745", "outcome": "LOSS", "r": -1.0,
     "opus_reason": "M15 bearish structure conflicts with bullish daily bias - violates U4"},
    {"custom_id": "2025-02-12_london_0800", "outcome": "LOSS", "r": -1.0,
     "opus_reason": "Both Sonnet and Opus approved this one (rubber stamp)"},
]


def load_all_prompts():
    index = {}
    for fp in sorted(BATCH_API_DIR.glob("*_full_prompts.json")):
        for item in json.load(open(fp)):
            index[item["custom_id"]] = item["prompt"]
    return index


def load_all_raw_results():
    index = {}
    for fp in sorted(BATCH_API_DIR.glob("*_raw_results.json")):
        data = json.load(open(fp))
        index.update(data)
    return index


def parse_response(raw):
    text = raw.get("text", "") if isinstance(raw, dict) else raw
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except:
        return None


def compress_eval(parsed):
    decision = parsed.get("decision", "?")
    if decision == "NO_TRADE":
        return f"NO_TRADE — {(parsed.get('no_trade_reason','') or '')[:100]}"
    elif decision == "CANDIDATE":
        tp = parsed.get("trade_parameters", {}) or {}
        r = parsed.get("reasoning", {})
        return (f"CANDIDATE ({r.get('setup_grade','?')}, conf={parsed.get('confidence_score',0)}) — "
                f"{tp.get('direction','?')} entry={tp.get('entry_price',0)}")
    return f"{decision}"


def build_session_memory(date, kz, target_time, raw_results):
    prefix = f"{date}_{kz}_"
    target_tag = target_time[11:16].replace(":", "") if "T" in target_time else target_time
    target_cid = f"{date}_{kz}_{target_tag}"

    entries = []
    for cid in sorted(k for k in raw_results if k.startswith(prefix)):
        if cid >= target_cid:
            break
        parsed = parse_response(raw_results[cid])
        if not parsed:
            continue
        time_tag = cid.split("_")[-1]
        time_str = f"{time_tag[:2]}:{time_tag[2:]} UTC"
        entries.append(f"- {time_str}: {compress_eval(parsed)}")

    return "\n".join(entries[-6:])


def inject_memory(user_message, session_memory):
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


def main():
    prompt_index = load_all_prompts()
    raw_results = load_all_raw_results()
    client = anthropic.Anthropic()

    print("=" * 80)
    print("Sonnet + Extended Thinking vs Opus — 4 Diagnostic Losers")
    print("=" * 80)

    for t in TRADES:
        cid = t["custom_id"]
        parts = cid.split("_")
        date = parts[0]
        kz = parts[1]
        time_tag = parts[2]
        candle_time = f"{date}T{time_tag[:2]}:{time_tag[2:]}:00Z"

        prompt = prompt_index.get(cid)
        if not prompt:
            print(f"\n{cid}: MISSING PROMPT")
            continue

        mem = build_session_memory(date, kz, candle_time, raw_results)
        user_msg = inject_memory(prompt["user_message"], mem)

        print(f"\n{'='*80}")
        print(f"{cid} — {t['outcome']} {t['r']}R")
        print(f"Session memory: {len(mem.split(chr(10))) if mem else 0} entries")
        print(f"Opus verdict: {t['opus_reason']}")
        print(f"{'='*80}")

        # Call Sonnet with extended thinking
        logger.info(f"Calling Sonnet+thinking for {cid}...")
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16000,
                thinking={
                    "type": "enabled",
                    "budget_tokens": 10000,
                },
                system=prompt["system"],
                messages=[{"role": "user", "content": user_msg}],
            )

            # Extract thinking and response
            thinking_text = ""
            response_text = ""
            for block in response.content:
                if block.type == "thinking":
                    thinking_text = block.thinking
                elif block.type == "text":
                    response_text = block.text

            # Parse the JSON response
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```\w*\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)
            parsed = json.loads(cleaned)

            decision = parsed.get("decision", "?")
            conf = parsed.get("confidence_score", 0)
            grade = parsed.get("reasoning", {}).get("setup_grade", "?")
            no_trade_reason = parsed.get("no_trade_reason", "")

            print(f"\nSonnet+Thinking Decision: {decision} (conf={conf}, grade={grade})")
            if no_trade_reason:
                print(f"No-trade reason: {no_trade_reason}")

            # Check if thinking identified the same issues as Opus
            print(f"\n--- Thinking excerpt (looking for risk identification) ---")
            # Find relevant risk-related passages in thinking
            thinking_lower = thinking_text.lower()
            risk_markers = ["risk", "concern", "violation", "conflict", "fail",
                           "not at", "too far", "no sweep", "no choch", "u3", "u4",
                           "doesn't meet", "not present", "missing"]
            relevant_lines = []
            for line in thinking_text.split("\n"):
                if any(m in line.lower() for m in risk_markers):
                    relevant_lines.append(line.strip())

            if relevant_lines:
                for line in relevant_lines[:8]:
                    print(f"  > {line[:120]}")
            else:
                print("  (no risk-related passages found in thinking)")

            print(f"\nThinking length: {len(thinking_text)} chars")
            cost = response.usage.input_tokens * 3 / 1e6 + response.usage.output_tokens * 15 / 1e6
            print(f"Cost: ${cost:.3f} (in={response.usage.input_tokens}, out={response.usage.output_tokens})")

            # Verdict comparison
            opus_rejected = t["custom_id"] != "2025-02-12_london_0800"  # Opus rejected all except this one
            thinking_rejected = decision != "CANDIDATE"

            if opus_rejected and thinking_rejected:
                print(f"\n✓ MATCH — Both Opus and Sonnet+thinking rejected this loser")
            elif opus_rejected and not thinking_rejected:
                print(f"\n✗ MISMATCH — Opus rejected but Sonnet+thinking still approved")
            elif not opus_rejected and thinking_rejected:
                print(f"\n! SURPRISE — Sonnet+thinking rejected but Opus approved")
            else:
                print(f"\n= BOTH APPROVED this trade (the rubber stamp case)")

        except Exception as e:
            print(f"ERROR: {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()
