#!/usr/bin/env python3
"""Regular Opus (NO thinking) on all 86 XAUUSD trades with session memory.

Direct API calls, checkpoint every 2 trades, live interim analysis.

Usage:
    python scripts/opus_regular_full_86.py
    python scripts/opus_regular_full_86.py --resume
"""

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
CHECKPOINT = OUTPUT_DIR / "opus_regular_86_checkpoint.json"

OPUS = "claude-opus-4-20250514"


def load_all_prompts():
    idx = {}
    for fp in sorted(BATCH_API_DIR.glob("*_full_prompts.json")):
        for item in json.load(open(fp)):
            idx[item["custom_id"]] = item["prompt"]
    return idx


def load_all_raw_results():
    idx = {}
    for fp in sorted(BATCH_API_DIR.glob("*_raw_results.json")):
        idx.update(json.load(open(fp)))
    return idx


def load_all_trades():
    trades = []
    for f in sorted(SESSIONS_DIR.glob("*.json")):
        d = json.load(open(f))
        ts = d.get("trade_summary", {})
        if not (isinstance(ts, dict) and ts.get("trade_taken")):
            continue
        evals = d.get("candle_evaluations", [])
        cand = next((e for e in evals if e.get("decision") == "CANDIDATE" and e.get("trade_executed")), None)
        if not cand:
            continue
        ct = cand["candle_time"]
        kz = cand.get("kill_zone", "london")
        date_str = d["date"]
        tt = ct[11:16].replace(":", "")
        trades.append({
            "date": date_str, "candle_time": ct, "kill_zone": kz,
            "custom_id": f"{date_str}_{kz}_{tt}",
            "outcome": ts["outcome"], "r_multiple": ts.get("r_multiple", 0),
        })
    return trades


def parse_raw(raw):
    text = raw.get("text", "") if isinstance(raw, dict) else raw
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except:
        return None


def compress(parsed):
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


def build_memory(date, kz, candle_time, raw_results):
    prefix = f"{date}_{kz}_"
    tag = candle_time[11:16].replace(":", "")
    target = f"{date}_{kz}_{tag}"
    entries = []
    for cid in sorted(k for k in raw_results if k.startswith(prefix)):
        if cid >= target:
            break
        p = parse_raw(raw_results[cid])
        if not p:
            continue
        tt = cid.split("_")[-1]
        entries.append(f"- {tt[:2]}:{tt[2:]} UTC: {compress(p)}")
    return "\n".join(entries[-6:])


def inject_memory(user_msg, mem):
    if not mem:
        return user_msg
    block = (
        "\n## Prior Candle Assessments (this session)\n"
        "The following are your assessments of prior candles in this kill zone.\n"
        "Consider the progression: Is a setup developing across candles? "
        "Did a prior candle show a sweep or displacement that sets up the current candle? "
        "If you said WAIT or noted a developing pattern on a prior candle, "
        "check if the trigger has now occurred.\n\n"
        f"{mem}\n"
    )
    marker = "## Current Time:"
    idx = user_msg.find(marker)
    if idx >= 0:
        return user_msg[:idx] + block + "\n" + user_msg[idx:]
    return user_msg + "\n" + block


def call_opus(client, system_blocks, user_message):
    """Regular Opus — NO thinking, NO streaming needed."""
    try:
        resp = client.messages.create(
            model=OPUS,
            max_tokens=4096,
            temperature=0,
            system=system_blocks,
            messages=[{"role": "user", "content": user_message}],
        )
        text = resp.content[0].text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```\w*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        parsed = json.loads(text)
        return {
            "status": "ok", "response": parsed, "raw": text,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        }
    except json.JSONDecodeError:
        return {"status": "parse_error", "raw": text[:300]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def interim_analysis(trades_done, results):
    """Print live stats after each batch of completions."""
    if not trades_done:
        return
    w_total = sum(1 for t in trades_done if t["outcome"] == "WIN")
    l_total = sum(1 for t in trades_done if t["outcome"] == "LOSS")

    opus_cands = [(t, results[t["custom_id"]]) for t in trades_done
                  if results.get(t["custom_id"], {}).get("status") == "ok"
                  and results[t["custom_id"]]["response"].get("decision") == "CANDIDATE"]

    opus_w = sum(1 for t, _ in opus_cands if t["outcome"] == "WIN")
    opus_l = sum(1 for t, _ in opus_cands if t["outcome"] == "LOSS")
    n = len(opus_cands)

    # Veto rates
    winners = [t for t in trades_done if t["outcome"] == "WIN"]
    losers = [t for t in trades_done if t["outcome"] == "LOSS"]
    w_vetoed = sum(1 for t in winners
                   if results.get(t["custom_id"], {}).get("status") == "ok"
                   and results[t["custom_id"]]["response"].get("decision") != "CANDIDATE")
    l_vetoed = sum(1 for t in losers
                   if results.get(t["custom_id"], {}).get("status") == "ok"
                   and results[t["custom_id"]]["response"].get("decision") != "CANDIDATE")

    wr = opus_w / n if n > 0 else 0
    r_total = sum(t["r_multiple"] for t, _ in opus_cands)

    logger.info(
        f"  ── INTERIM {len(trades_done)}/86 ({w_total}W {l_total}L) ── "
        f"Opus: {n} CAND ({opus_w}W {opus_l}L) WR={wr:.0%} R={r_total:+.1f} | "
        f"Winner veto: {w_vetoed}/{len(winners)} ({w_vetoed/max(1,len(winners)):.0%}) | "
        f"Loser veto: {l_vetoed}/{len(losers)} ({l_vetoed/max(1,len(losers)):.0%})"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    trades = load_all_trades()
    logger.info(f"Loaded {len(trades)} trades")

    prompts = load_all_prompts()
    raw_results = load_all_raw_results()
    logger.info(f"Prompts: {len(prompts)}, Raw results: {len(raw_results)}")

    # Build enriched prompts
    enriched = {}
    for t in trades:
        cid = t["custom_id"]
        p = prompts.get(cid)
        if not p:
            continue
        mem = build_memory(t["date"], t["kill_zone"], t["candle_time"], raw_results)
        enriched[cid] = {"system": p["system"], "user_message": inject_memory(p["user_message"], mem)}

    with_mem = sum(1 for cid in enriched
                   if "Prior Candle Assessments" in enriched[cid]["user_message"])
    logger.info(f"Enriched: {len(enriched)}, with session memory: {with_mem}")

    # Checkpoint
    if args.resume and CHECKPOINT.exists():
        cp = json.load(open(CHECKPOINT))
        results = cp.get("results", {})
        logger.info(f"Resuming from checkpoint: {len(results)} done")
    else:
        results = {}

    client = anthropic.Anthropic()
    total_cost = 0

    for i, t in enumerate(trades):
        cid = t["custom_id"]
        if cid in results:
            continue
        e = enriched.get(cid)
        if not e:
            continue

        logger.info(f"[{i+1}/86] {cid} ({t['outcome']} {t['r_multiple']:+.2f}R)...")

        for attempt in range(3):
            result = call_opus(client, e["system"], e["user_message"])
            if result["status"] == "ok":
                break
            if attempt < 2:
                logger.warning(f"  Retry {attempt+1}: {result.get('error','')[:80]}")
                time.sleep(5)

        results[cid] = result

        if result["status"] == "ok":
            dec = result["response"].get("decision", "?")
            conf = result["response"].get("confidence_score", 0)
            cost = result.get("input_tokens", 0) * 15 / 1e6 + result.get("output_tokens", 0) * 75 / 1e6
            total_cost += cost
            logger.info(f"  → {dec} conf={conf} (${cost:.3f})")
        else:
            logger.warning(f"  → {result['status']}: {result.get('error','')[:80]}")

        # Checkpoint every 2
        if (i + 1) % 2 == 0:
            json.dump({"results": results, "cost": total_cost},
                      open(CHECKPOINT, "w"), indent=2)

        # Interim analysis every 10
        completed = [t2 for t2 in trades[:i+1] if t2["custom_id"] in results]
        if len(completed) % 10 == 0 and len(completed) > 0:
            interim_analysis(completed, results)

        time.sleep(0.5)

    # Final checkpoint
    json.dump({"results": results, "cost": total_cost}, open(CHECKPOINT, "w"), indent=2)
    logger.info(f"Done. Total cost: ${total_cost:.2f}")

    # Final analysis
    completed = [t for t in trades if t["custom_id"] in results]
    interim_analysis(completed, results)

    # Save results file
    json.dump({"results": results, "cost": total_cost, "trades": trades},
              open(OUTPUT_DIR / "opus_regular_86_results.json", "w"), indent=2)
    logger.info(f"Results saved to {OUTPUT_DIR / 'opus_regular_86_results.json'}")


if __name__ == "__main__":
    main()
