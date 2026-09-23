#!/usr/bin/env python3
"""Opus + extended thinking on the same 4 diagnostic losers."""

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

TRADES = [
    {"custom_id": "2024-06-05_ny_1445", "outcome": "LOSS", "r": -1.0},
    {"custom_id": "2024-09-27_ny_1400", "outcome": "LOSS", "r": -1.0},
    {"custom_id": "2025-03-14_london_0745", "outcome": "LOSS", "r": -1.0},
    {"custom_id": "2025-02-12_london_0800", "outcome": "LOSS", "r": -1.0},
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
        index.update(json.load(open(fp)))
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
    d = parsed.get("decision", "?")
    if d == "NO_TRADE":
        return f"NO_TRADE — {(parsed.get('no_trade_reason','') or '')[:100]}"
    elif d == "CANDIDATE":
        tp = parsed.get("trade_parameters", {}) or {}
        r = parsed.get("reasoning", {})
        return (f"CANDIDATE ({r.get('setup_grade','?')}, conf={parsed.get('confidence_score',0)}) — "
                f"{tp.get('direction','?')} entry={tp.get('entry_price',0)}")
    return d


def build_session_memory(date, kz, candle_time, raw_results):
    prefix = f"{date}_{kz}_"
    target_tag = candle_time[11:16].replace(":", "")
    target_cid = f"{date}_{kz}_{target_tag}"
    entries = []
    for cid in sorted(k for k in raw_results if k.startswith(prefix)):
        if cid >= target_cid:
            break
        parsed = parse_response(raw_results[cid])
        if not parsed:
            continue
        tt = cid.split("_")[-1]
        entries.append(f"- {tt[:2]}:{tt[2:]} UTC: {compress_eval(parsed)}")
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

    results = []
    for t in TRADES:
        cid = t["custom_id"]
        parts = cid.split("_")
        date, kz, time_tag = parts[0], parts[1], parts[2]
        candle_time = f"{date}T{time_tag[:2]}:{time_tag[2:]}:00Z"

        prompt = prompt_index.get(cid)
        if not prompt:
            print(f"MISSING: {cid}")
            continue

        mem = build_session_memory(date, kz, candle_time, raw_results)
        user_msg = inject_memory(prompt["user_message"], mem)

        logger.info(f"Calling Opus+thinking for {cid}...")
        try:
            # Opus+thinking requires streaming for long requests
            thinking_text = ""
            response_text = ""
            input_tokens = 0
            output_tokens = 0

            with client.messages.stream(
                model="claude-opus-4-20250514",
                max_tokens=16000,
                thinking={"type": "enabled", "budget_tokens": 10000},
                system=prompt["system"],
                messages=[{"role": "user", "content": user_msg}],
            ) as stream:
                response = stream.get_final_message()

            for block in response.content:
                if block.type == "thinking":
                    thinking_text = block.thinking
                elif block.type == "text":
                    response_text = block.text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```\w*\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)
            parsed = json.loads(cleaned)

            decision = parsed.get("decision", "?")
            conf = parsed.get("confidence_score", 0)
            grade = parsed.get("reasoning", {}).get("setup_grade", "?")
            no_trade_reason = parsed.get("no_trade_reason", "")
            cost = response.usage.input_tokens * 15 / 1e6 + response.usage.output_tokens * 75 / 1e6

            print(f"\n{cid}: {decision} conf={conf} grade={grade}")
            if no_trade_reason:
                print(f"  Reason: {no_trade_reason}")
            print(f"  Thinking: {len(thinking_text)} chars, Cost: ${cost:.3f}")

            # Key risk lines from thinking
            for line in thinking_text.split("\n"):
                if any(m in line.lower() for m in ["risk", "violation", "conflict", "fail", "not at", "missing", "u3", "u4"]):
                    print(f"  > {line.strip()[:120]}")

            results.append({
                "cid": cid, "decision": decision, "confidence": conf,
                "grade": grade, "no_trade_reason": no_trade_reason,
                "thinking_length": len(thinking_text), "cost": cost,
            })

        except Exception as e:
            print(f"ERROR {cid}: {e}")
            results.append({"cid": cid, "decision": "ERROR", "error": str(e)})

        time.sleep(1)

    # Save results
    with open(_PROJECT_ROOT / "knowledge_base_backtest" / "test_b" / "opus_thinking_4_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n\nSummary:")
    for r in results:
        print(f"  {r['cid']}: {r.get('decision','?')} conf={r.get('confidence',0)}")


if __name__ == "__main__":
    main()
