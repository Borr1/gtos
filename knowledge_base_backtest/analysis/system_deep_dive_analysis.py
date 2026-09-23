#!/usr/bin/env python3
"""System Deep Dive — Complete Understanding Analysis.

Reads actual AI outputs, analyzes reasoning patterns, measures token usage,
and identifies failure modes.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime, date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BATCH_API = PROJECT_ROOT / "knowledge_base_backtest" / "batch_api"
SESSIONS_DIR = PROJECT_ROOT / "knowledge_base_backtest" / "sessions"
ANALYSIS_DIR = PROJECT_ROOT / "knowledge_base_backtest" / "analysis"
OUT_DIR = ANALYSIS_DIR

sys.path.insert(0, str(PROJECT_ROOT))


def load_gbpusd_sessions():
    """Load all GBPUSD session manifests."""
    d = SESSIONS_DIR / "GBPUSD"
    sessions = {}
    for f in sorted(d.glob("*_session.json")):
        with open(f) as fh:
            sessions[f.stem.replace("_session", "")] = json.load(fh)
    return sessions


def load_gbpusd_responses():
    """Load all GBPUSD parsed responses."""
    d = BATCH_API / "responses" / "GBPUSD"
    responses = {}
    for f in sorted(d.glob("*_responses.json")):
        with open(f) as fh:
            day_data = json.load(fh)
            date_str = f.stem.replace("_responses", "")
            responses[date_str] = day_data
    return responses


def load_xauusd_sessions():
    d = SESSIONS_DIR / "XAUUSD"
    sessions = {}
    for f in sorted(d.glob("*_session.json")):
        with open(f) as fh:
            sessions[f.stem.replace("_session", "")] = json.load(fh)
    return sessions


def load_xauusd_responses():
    d = BATCH_API / "responses" / "XAUUSD"
    responses = {}
    for f in sorted(d.glob("*_responses.json")):
        with open(f) as fh:
            responses[f.stem.replace("_responses", "")] = json.load(fh)
    return responses


def load_raw_batch_results():
    """Load raw batch results to get token counts."""
    results = {}
    for f in BATCH_API.glob("msgbatch_*_raw_results.json"):
        with open(f) as fh:
            data = json.load(fh)
            results.update(data)
    return results


def load_displacement_db(symbol):
    """Load latest displacement database CSV."""
    pattern = f"{symbol}_displacement_database_20260403_1003.csv"
    path = ANALYSIS_DIR / pattern
    if not path.exists():
        # Try other timestamps
        candidates = sorted(ANALYSIS_DIR.glob(f"{symbol}_displacement_database_*.csv"))
        if candidates:
            path = candidates[-1]
        else:
            return []

    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def get_trade_dates(sessions):
    """Get dates with trades and their outcomes."""
    wins = []
    losses = []
    for date_str, sess in sessions.items():
        ts = sess.get("trade_summary", {})
        for t in ts.get("trades", []):
            entry = {
                "date": date_str,
                "kz": t.get("kill_zone", ""),
                "outcome": t.get("outcome", ""),
                "r": t.get("r_multiple", 0),
                "mfe_r": t.get("mfe_r", 0),
                "mae_r": t.get("mae_r", 0),
                "hold": t.get("hold_time_candles", 0),
                "exit": t.get("exit_substate", ""),
                "framework": t.get("framework", ""),
                "trade_id": t.get("trade_id", ""),
            }
            if t.get("outcome") == "WIN":
                wins.append(entry)
            else:
                losses.append(entry)
    return wins, losses


def extract_candidate_response(responses, date_str, kz):
    """Find the CANDIDATE response for a given date/kz."""
    day_resp = responses.get(date_str, {})
    for cid, resp in day_resp.items():
        if resp.get("decision") == "CANDIDATE" and resp.get("kill_zone") == kz:
            return cid, resp
    # If not found by kz field, try matching from custom_id
    for cid, resp in day_resp.items():
        if resp.get("decision") == "CANDIDATE" and kz in cid:
            return cid, resp
    return None, None


def extract_reasoning(resp):
    """Extract all reasoning fields from a response."""
    r = resp.get("reasoning", {})
    if isinstance(r, str):
        return {"raw_text": r}

    result = {}

    # Daily bias
    db = r.get("daily_bias", {})
    if isinstance(db, dict):
        result["daily_bias"] = {
            "direction": db.get("direction", ""),
            "confidence": db.get("confidence", ""),
            "explanation": db.get("explanation", ""),
        }

    # H4 alignment
    h4 = r.get("h4_alignment", {})
    if isinstance(h4, dict):
        result["h4_alignment"] = {
            "aligned": h4.get("aligned", False),
            "explanation": h4.get("explanation", ""),
        }

    # H1 setup
    h1 = r.get("h1_setup", {})
    if isinstance(h1, dict):
        result["h1_setup"] = {
            "poi_identified": h1.get("poi_identified", False),
            "poi_type": h1.get("poi_type", ""),
            "explanation": h1.get("explanation", ""),
        }

    # M15 confirmation
    m15 = r.get("m15_confirmation", {})
    if isinstance(m15, dict):
        result["m15_confirmation"] = {
            "confirmed": m15.get("confirmed", False),
            "explanation": m15.get("explanation", ""),
        }

    # Liquidity
    liq = r.get("liquidity", {})
    if isinstance(liq, dict):
        result["liquidity"] = {
            "swept": liq.get("swept", False),
            "level": liq.get("level", ""),
            "explanation": liq.get("explanation", ""),
        }

    # Overall
    result["setup_grade"] = r.get("setup_grade", resp.get("setup_grade", ""))
    result["overall_reasoning"] = r.get("overall_reasoning", "")

    return result


# ═══════════════════════════════════════════════════════════════════════
# PART A: How the AI Thinks
# ═══════════════════════════════════════════════════════════════════════

def part_a(gbp_sessions, gbp_responses, xau_sessions, xau_responses):
    """Read actual AI outputs — winning, losing, no-trade, confidence."""
    print("\n" + "="*70)
    print("  PART A: How the AI Thinks")
    print("="*70)

    wins, losses = get_trade_dates(gbp_sessions)

    # A1: 5 winning trade responses
    print("\n--- A1: Winning Trade Responses ---")
    win_details = []
    for w in wins[:5]:
        cid, resp = extract_candidate_response(gbp_responses, w["date"], w["kz"])
        if resp:
            reasoning = extract_reasoning(resp)
            tp = resp.get("trade_parameters", {})
            detail = {
                "date_kz": f"{w['date']} {w['kz']}",
                "decision": resp.get("decision"),
                "grade": resp.get("setup_grade", reasoning.get("setup_grade", "")),
                "confidence": resp.get("confidence_score", 0),
                "confidence_computation": resp.get("confidence_computation", ""),
                "overall_reasoning": reasoning.get("overall_reasoning", ""),
                "daily_bias": reasoning.get("daily_bias", {}),
                "h4_alignment": reasoning.get("h4_alignment", {}),
                "h1_setup": reasoning.get("h1_setup", {}),
                "m15_confirmation": reasoning.get("m15_confirmation", {}),
                "liquidity": reasoning.get("liquidity", {}),
                "entry": tp.get("entry_price", 0) if isinstance(tp, dict) else 0,
                "sl": tp.get("stop_loss", 0) if isinstance(tp, dict) else 0,
                "tp1": tp.get("take_profit_1", 0) if isinstance(tp, dict) else 0,
                "outcome": f"{w['outcome']}, R={w['r']:+.3f}",
                "mfe_r": w["mfe_r"],
                "mae_r": w["mae_r"],
            }
            win_details.append(detail)
            print(f"\n  WIN: {w['date']} {w['kz']} R={w['r']:+.3f}")
            print(f"    Grade: {detail['grade']}, Confidence: {detail['confidence']}")
            print(f"    Conf computation: {detail['confidence_computation'][:120]}...")
            print(f"    Overall reasoning: {detail['overall_reasoning'][:200]}...")
            db = detail.get("daily_bias", {})
            print(f"    Daily bias: {db.get('direction','')} ({db.get('confidence','')}) — {db.get('explanation','')[:120]}")
            h1 = detail.get("h1_setup", {})
            print(f"    H1 setup: poi={h1.get('poi_type','')} — {h1.get('explanation','')[:120]}")
            m15 = detail.get("m15_confirmation", {})
            print(f"    M15 confirm: {m15.get('confirmed','')} — {m15.get('explanation','')[:120]}")
        else:
            print(f"  WIN: {w['date']} {w['kz']} — NO RESPONSE FOUND")

    # A2: 5 losing trade responses
    print("\n\n--- A2: Losing Trade Responses ---")
    loss_details = []
    for l in losses[:5]:
        cid, resp = extract_candidate_response(gbp_responses, l["date"], l["kz"])
        if resp:
            reasoning = extract_reasoning(resp)
            tp = resp.get("trade_parameters", {})
            detail = {
                "date_kz": f"{l['date']} {l['kz']}",
                "decision": resp.get("decision"),
                "grade": resp.get("setup_grade", reasoning.get("setup_grade", "")),
                "confidence": resp.get("confidence_score", 0),
                "confidence_computation": resp.get("confidence_computation", ""),
                "overall_reasoning": reasoning.get("overall_reasoning", ""),
                "daily_bias": reasoning.get("daily_bias", {}),
                "h4_alignment": reasoning.get("h4_alignment", {}),
                "h1_setup": reasoning.get("h1_setup", {}),
                "m15_confirmation": reasoning.get("m15_confirmation", {}),
                "liquidity": reasoning.get("liquidity", {}),
                "entry": tp.get("entry_price", 0) if isinstance(tp, dict) else 0,
                "sl": tp.get("stop_loss", 0) if isinstance(tp, dict) else 0,
                "tp1": tp.get("take_profit_1", 0) if isinstance(tp, dict) else 0,
                "outcome": f"{l['outcome']}, R={l['r']:+.3f}",
                "mfe_r": l["mfe_r"],
                "mae_r": l["mae_r"],
            }
            loss_details.append(detail)
            print(f"\n  LOSS: {l['date']} {l['kz']} R={l['r']:+.3f} (MFE={l['mfe_r']:.2f}R)")
            print(f"    Grade: {detail['grade']}, Confidence: {detail['confidence']}")
            print(f"    Conf computation: {detail['confidence_computation'][:120]}...")
            print(f"    Overall reasoning: {detail['overall_reasoning'][:200]}...")
            db = detail.get("daily_bias", {})
            print(f"    Daily bias: {db.get('direction','')} ({db.get('confidence','')}) — {db.get('explanation','')[:120]}")
        else:
            print(f"  LOSS: {l['date']} {l['kz']} — NO RESPONSE FOUND")

    # A3: NO_TRADE on active days
    print("\n\n--- A3: NO_TRADE on Active Days ---")
    disp_db = load_displacement_db("GBPUSD")

    # Find dates with KZ displacements that had aligned direction
    disp_dates = set()
    for row in disp_db:
        if row.get("kz") == "True" and row.get("align", "0") != "0":
            try:
                al = int(row["align"])
            except (ValueError, KeyError):
                al = 0
            if al >= 2:
                disp_dates.add(row.get("date", "")[:10])

    trade_dates = set(w["date"] for w in wins) | set(l["date"] for l in losses)
    no_trade_active = sorted(disp_dates - trade_dates)[:5]

    no_trade_details = []
    for d in no_trade_active:
        day_resp = gbp_responses.get(d, {})
        if not day_resp:
            continue

        # Find the candle closest to a displacement
        reasons = []
        for cid, resp in day_resp.items():
            reasons.append({
                "candle": cid,
                "decision": resp.get("decision", ""),
                "reason": resp.get("no_trade_reason", "") or resp.get("wait_reason", ""),
                "confidence": resp.get("confidence_score", 0),
            })

        detail = {"date": d, "candle_count": len(reasons), "decisions": reasons}
        no_trade_details.append(detail)

        print(f"\n  ACTIVE DATE (no trade): {d}")
        for r in reasons[:3]:
            print(f"    {r['candle']}: {r['decision']} — {str(r['reason'])[:120]}")
        if len(reasons) > 3:
            print(f"    ... ({len(reasons) - 3} more candles)")

    # A5: Confidence score analysis
    print("\n\n--- A5: Confidence Score Analysis ---")

    # Collect all CANDIDATE confidences with outcomes
    candidate_confidences = []
    for d, day_resp in gbp_responses.items():
        for cid, resp in day_resp.items():
            if resp.get("decision") == "CANDIDATE":
                conf = resp.get("confidence_score", 0)
                comp = resp.get("confidence_computation", "")
                # Find outcome
                kz = resp.get("kill_zone", "london" if "london" in cid else "ny")
                outcome = None
                sess = gbp_sessions.get(d, {})
                for t in sess.get("trade_summary", {}).get("trades", []):
                    if t.get("kill_zone") == kz:
                        outcome = t.get("outcome")
                        r = t.get("r_multiple", 0)
                        break
                candidate_confidences.append({
                    "date": d, "kz": kz, "confidence": conf,
                    "computation": comp, "outcome": outcome, "r": r if outcome else 0,
                })

    if candidate_confidences:
        confs = [c["confidence"] for c in candidate_confidences]
        print(f"  GBPUSD CANDIDATE confidence: n={len(confs)}")
        print(f"    Min: {min(confs)}, Max: {max(confs)}, Mean: {sum(confs)/len(confs):.1f}")
        confs_sorted = sorted(confs)
        print(f"    Median: {confs_sorted[len(confs_sorted)//2]}")

        # Win rate by confidence bin
        bins = [(50, 65), (65, 75), (75, 85), (85, 95)]
        for lo, hi in bins:
            in_bin = [c for c in candidate_confidences if lo <= c["confidence"] < hi]
            if in_bin:
                wins_in_bin = sum(1 for c in in_bin if c["outcome"] == "WIN")
                print(f"    Confidence {lo}-{hi}: n={len(in_bin)}, wins={wins_in_bin}, WR={wins_in_bin/len(in_bin)*100:.1f}%")

        # Confidence computation breakdown
        comp_adjustments = Counter()
        for c in candidate_confidences:
            comp = c.get("computation", "")
            if isinstance(comp, str):
                # Count each +/- adjustment mentioned
                for segment in comp.split(","):
                    segment = segment.strip()
                    if "+" in segment or "-" in segment:
                        comp_adjustments[segment[:50]] += 1

        print(f"\n    Most common adjustments:")
        for adj, count in comp_adjustments.most_common(10):
            print(f"      {count:3d}x: {adj}")

    # Same for XAUUSD
    xau_wins, xau_losses = get_trade_dates(xau_sessions)
    xau_confs = []
    for d, day_resp in xau_responses.items():
        for cid, resp in day_resp.items():
            if resp.get("decision") == "CANDIDATE":
                conf = resp.get("confidence_score", 0)
                kz = resp.get("kill_zone", "london" if "london" in cid else "ny")
                outcome = None
                r = 0
                sess = xau_sessions.get(d, {})
                for t in sess.get("trade_summary", {}).get("trades", []):
                    if t.get("kill_zone") == kz:
                        outcome = t.get("outcome")
                        r = t.get("r_multiple", 0)
                        break
                xau_confs.append({"confidence": conf, "outcome": outcome, "r": r})

    if xau_confs:
        confs = [c["confidence"] for c in xau_confs]
        print(f"\n  XAUUSD CANDIDATE confidence: n={len(confs)}")
        print(f"    Min: {min(confs)}, Max: {max(confs)}, Mean: {sum(confs)/len(confs):.1f}")

        for lo, hi in bins:
            in_bin = [c for c in xau_confs if lo <= c["confidence"] < hi]
            if in_bin:
                wins_in_bin = sum(1 for c in in_bin if c["outcome"] == "WIN")
                print(f"    Confidence {lo}-{hi}: n={len(in_bin)}, wins={wins_in_bin}, WR={wins_in_bin/len(in_bin)*100:.1f}%")

    return {
        "winning_trades_reasoning": win_details,
        "losing_trades_reasoning": loss_details,
        "no_trade_on_active_days": no_trade_details,
        "candidate_confidences_gbpusd": candidate_confidences,
        "candidate_confidences_xauusd": [{"confidence": c["confidence"], "outcome": c["outcome"]} for c in xau_confs],
    }


# ═══════════════════════════════════════════════════════════════════════
# PART B: What the AI Sees
# ═══════════════════════════════════════════════════════════════════════

def part_b():
    """Full input analysis — prompt, MSO, token budget."""
    print("\n" + "="*70)
    print("  PART B: What the AI Sees")
    print("="*70)

    # B1: Full gold PA prompt
    from src.prompts.primary_analyzer_prompt import SYSTEM_PROMPT, build_system_prompt

    prompt_len = len(SYSTEM_PROMPT)
    # Rough token estimate: ~4 chars per token for English text
    prompt_tokens_est = prompt_len // 4

    print(f"\n--- B1: Gold System Prompt ---")
    print(f"  Character count: {prompt_len}")
    print(f"  Estimated tokens: ~{prompt_tokens_est}")
    print(f"  First 200 chars: {SYSTEM_PROMPT[:200]}...")
    print(f"  Last 200 chars: ...{SYSTEM_PROMPT[-200:]}")

    # Sections in the prompt
    sections = []
    for line in SYSTEM_PROMPT.split("\n"):
        if line.startswith("##") and not line.startswith("###"):
            sections.append(line.strip())
    print(f"  Sections ({len(sections)}):")
    for s in sections:
        print(f"    {s}")

    # B3: Token budget from raw batch results
    print(f"\n--- B3: Token Budget Analysis ---")
    raw = load_raw_batch_results()

    # Sample 10 random candle evaluations
    import random
    random.seed(42)
    keys = list(raw.keys())
    sample_keys = random.sample(keys, min(10, len(keys)))

    token_data = []
    for k in sample_keys:
        r = raw[k]
        token_data.append({
            "candle": k,
            "input_tokens": r.get("input_tokens", 0),
            "output_tokens": r.get("output_tokens", 0),
            "cache_read": r.get("cache_read", 0),
            "cache_create": r.get("cache_create", 0),
        })

    if token_data:
        inp = [t["input_tokens"] for t in token_data]
        out = [t["output_tokens"] for t in token_data]
        cache_r = [t["cache_read"] for t in token_data]
        cache_c = [t["cache_create"] for t in token_data]

        print(f"  Sample of {len(token_data)} candle evaluations:")
        print(f"    Input tokens:  min={min(inp)}, max={max(inp)}, avg={sum(inp)/len(inp):.0f}")
        print(f"    Output tokens: min={min(out)}, max={max(out)}, avg={sum(out)/len(out):.0f}")
        print(f"    Cache read:    min={min(cache_r)}, max={max(cache_r)}, avg={sum(cache_r)/len(cache_r):.0f}")
        print(f"    Cache create:  min={min(cache_c)}, max={max(cache_c)}, avg={sum(cache_c)/len(cache_c):.0f}")
        print(f"    Total input:   avg={sum(inp)/len(inp):.0f} (context window: 200K)")
        print(f"    % of context:  {sum(inp)/len(inp)/200000*100:.1f}%")

        # Check for truncation
        truncated = sum(1 for t in token_data if t["output_tokens"] >= 1900)
        print(f"    Potentially truncated (>=1900 output tokens): {truncated}/{len(token_data)}")

    # Compute total tokens for one session (10-20 candles)
    # Find all candles for one date
    date_groups = defaultdict(list)
    for k, r in raw.items():
        date_str = k[:10]
        date_groups[date_str].append(r)

    session_tokens = []
    for d, candles in list(date_groups.items())[:20]:
        total_in = sum(c.get("input_tokens", 0) for c in candles)
        total_out = sum(c.get("output_tokens", 0) for c in candles)
        session_tokens.append({"date": d, "candles": len(candles), "input": total_in, "output": total_out})

    if session_tokens:
        print(f"\n  Per-session token usage (first 20 dates):")
        print(f"    {'Date':12s} | {'Candles':>7} | {'Input':>8} | {'Output':>7} | {'Total':>8}")
        for s in session_tokens[:10]:
            print(f"    {s['date']:12s} | {s['candles']:7d} | {s['input']:8d} | {s['output']:7d} | {s['input']+s['output']:8d}")

    return {
        "system_prompt_chars": prompt_len,
        "system_prompt_tokens_est": prompt_tokens_est,
        "system_prompt_sections": sections,
        "token_analysis": token_data,
        "session_token_usage": session_tokens[:20],
    }


# ═══════════════════════════════════════════════════════════════════════
# PART C: Where the AI Fails
# ═══════════════════════════════════════════════════════════════════════

def part_c(gbp_sessions, gbp_responses):
    """Systematic failure analysis."""
    print("\n" + "="*70)
    print("  PART C: Where the AI Fails")
    print("="*70)

    wins, losses = get_trade_dates(gbp_sessions)

    # C1: Losing trade forensics
    print("\n--- C1: Losing Trade Forensics ---")
    loss_analysis = []
    for l in losses:
        cid, resp = extract_candidate_response(gbp_responses, l["date"], l["kz"])

        category = "unknown"
        if l["exit"] == "CLOSED_SL":
            if l["mfe_r"] >= 1.0:
                category = "SL_too_tight"  # Had 1R+ MFE but still hit SL
            elif l["mfe_r"] < 0.3:
                category = "immediate_reversal"  # Never went in direction
            else:
                category = "market_condition"  # Normal loss
        elif l["exit"] == "CLOSED_SESSION_TIMEOUT":
            if l["r"] > -0.5:
                category = "timing_error"  # Slightly underwater at timeout
            else:
                category = "market_condition"

        reasoning = ""
        conf = 0
        if resp:
            r = extract_reasoning(resp)
            reasoning = r.get("overall_reasoning", "")[:200]
            conf = resp.get("confidence_score", 0)

        entry = {
            "date": l["date"], "kz": l["kz"], "r": l["r"],
            "mfe_r": l["mfe_r"], "mae_r": l["mae_r"],
            "exit": l["exit"], "category": category,
            "confidence": conf, "reasoning": reasoning,
        }
        loss_analysis.append(entry)
        print(f"  {l['date']} {l['kz']:8s} R={l['r']:+.3f} MFE={l['mfe_r']:.2f}R exit={l['exit']:25s} → {category}")

    # Category counts
    cats = Counter(l["category"] for l in loss_analysis)
    print(f"\n  Loss categories:")
    for cat, count in cats.most_common():
        print(f"    {cat:25s}: {count}")

    # C2: Safety-rejected trades
    print("\n\n--- C2: Safety-Rejected Trades ---")
    safety_rejects = []
    for d, day_resp in gbp_responses.items():
        sess = gbp_sessions.get(d, {})
        for cid, resp in day_resp.items():
            # Look for safety rejection markers
            evals = sess.get("candle_evaluations", [])
            for ev in evals:
                if isinstance(ev, dict) and ev.get("candle_time", "").replace(":", "").replace("-", "").replace("T", "").replace("Z", "") in cid.replace("_", ""):
                    reason = ev.get("reason", "")
                    if "direction_mismatch" in str(reason) or "below_grade" in str(reason) or "rr_too_low" in str(reason) or "sl_too" in str(reason).lower():
                        safety_rejects.append({
                            "date": d, "candle": cid,
                            "reason": str(reason)[:100],
                        })

    # Simpler: count from session manifests
    reject_counts = Counter()
    for d, sess in gbp_sessions.items():
        for ev in sess.get("candle_evaluations", []):
            if isinstance(ev, dict):
                reason = str(ev.get("reason", ""))
                if "direction_mismatch" in reason:
                    reject_counts["direction_mismatch"] += 1
                elif "below_grade" in reason:
                    reject_counts["below_grade"] += 1
                elif "rr_too_low" in reason:
                    reject_counts["rr_too_low"] += 1
                elif "sl_too" in reason.lower() or "atr" in reason.lower():
                    reject_counts["sl_too_tight"] += 1

    print(f"  Safety rejection counts:")
    for reason, count in reject_counts.most_common():
        print(f"    {reason:25s}: {count}")

    # C4: Multi-candle decision patterns
    print("\n\n--- C4: Multi-Candle Decision Patterns ---")
    candidate_timing = []
    session_patterns = defaultdict(list)

    for d, sess in gbp_sessions.items():
        evals = sess.get("candle_evaluations", [])
        for i, ev in enumerate(evals):
            if isinstance(ev, dict):
                kz = ev.get("kill_zone", "")
                decision = ev.get("decision", "")
                session_patterns[f"{d}_{kz}"].append(decision)
                if decision == "CANDIDATE":
                    candidate_timing.append({"date": d, "kz": kz, "candle_num": i + 1})

    if candidate_timing:
        positions = [c["candle_num"] for c in candidate_timing]
        print(f"  CANDIDATE fires on candle # (1-indexed):")
        pos_counts = Counter(positions)
        for pos in sorted(pos_counts.keys()):
            bar = "█" * pos_counts[pos]
            print(f"    Candle {pos:2d}: {pos_counts[pos]:3d} {bar}")
        print(f"    Mean position: {sum(positions)/len(positions):.1f}")

    # Pattern analysis: do non-trading sessions show "warming up"?
    no_trade_sessions = 0
    immediate_notrade = 0
    warmup_then_notrade = 0
    for key, decisions in session_patterns.items():
        if "CANDIDATE" not in decisions:
            no_trade_sessions += 1
            if all(d == "NO_TRADE" for d in decisions):
                immediate_notrade += 1
            elif "WAIT" in decisions:
                warmup_then_notrade += 1

    print(f"\n  Non-trading sessions: {no_trade_sessions}")
    print(f"    All NO_TRADE (immediate reject): {immediate_notrade} ({immediate_notrade/max(1,no_trade_sessions)*100:.0f}%)")
    print(f"    Had WAIT then NO_TRADE (warmup):  {warmup_then_notrade} ({warmup_then_notrade/max(1,no_trade_sessions)*100:.0f}%)")

    return {
        "loss_categorization": {cat: count for cat, count in cats.items()},
        "loss_analysis": loss_analysis,
        "safety_rejection_counts": dict(reject_counts),
        "candidate_timing": candidate_timing,
        "decision_patterns": {
            "no_trade_sessions": no_trade_sessions,
            "immediate_notrade": immediate_notrade,
            "warmup_then_notrade": warmup_then_notrade,
        },
    }


# ═══════════════════════════════════════════════════════════════════════
# PART E: Architecture Deep Dive
# ═══════════════════════════════════════════════════════════════════════

def part_e():
    """Architecture analysis — token flow, caching, context budget."""
    print("\n" + "="*70)
    print("  PART E: Architecture Deep Dive")
    print("="*70)

    raw = load_raw_batch_results()

    # E3: Token flow for one session
    print("\n--- E3: Token Flow Diagram ---")

    # Find a date with a full 20-candle session (GBPUSD extended)
    date_candles = defaultdict(list)
    for k, r in raw.items():
        date_str = k[:10]
        date_candles[date_str].append((k, r))

    # Pick a date with many candles
    best_date = max(date_candles.keys(), key=lambda d: len(date_candles[d]))
    candles = sorted(date_candles[best_date], key=lambda x: x[0])

    print(f"\n  Session: {best_date} ({len(candles)} candles)")
    total_in = 0
    total_out = 0
    total_cache_read = 0
    total_cache_create = 0

    for cid, r in candles[:20]:
        inp = r.get("input_tokens", 0)
        out = r.get("output_tokens", 0)
        cr = r.get("cache_read", 0)
        cc = r.get("cache_create", 0)
        total_in += inp
        total_out += out
        total_cache_read += cr
        total_cache_create += cc

        cache_pct = cr / max(1, inp) * 100
        print(f"    {cid:35s} in={inp:5d} out={out:4d} cache_read={cr:5d} ({cache_pct:.0f}%)")

    print(f"\n  Session totals:")
    print(f"    Total input: {total_in:,}")
    print(f"    Total output: {total_out:,}")
    print(f"    Total cache read: {total_cache_read:,}")
    print(f"    Total cache create: {total_cache_create:,}")
    print(f"    Cache hit rate: {total_cache_read / max(1, total_in) * 100:.1f}%")

    # Estimate cached vs dynamic portions
    if candles:
        first_in = candles[0][1].get("input_tokens", 0)
        first_cache = candles[0][1].get("cache_create", 0)
        second_cache_read = candles[1][1].get("cache_read", 0) if len(candles) > 1 else 0
        second_in = candles[1][1].get("input_tokens", 0) if len(candles) > 1 else 0

        print(f"\n  Cache analysis:")
        print(f"    First candle: {first_in} input, {first_cache} cache_create")
        print(f"    Second candle: {second_in} input, {second_cache_read} cache_read")
        print(f"    Estimated cached (system prompt): ~{first_cache} tokens")
        print(f"    Estimated dynamic (MSO per candle): ~{second_in - second_cache_read} tokens")

    return {
        "session_example": {
            "date": best_date,
            "candle_count": len(candles),
            "total_input": total_in,
            "total_output": total_out,
            "cache_hit_rate": round(total_cache_read / max(1, total_in) * 100, 1),
        },
    }


# ═══════════════════════════════════════════════════════════════════════
# PART F: Opportunity Identification
# ═══════════════════════════════════════════════════════════════════════

def part_f():
    """What information exists but isn't used."""
    print("\n" + "="*70)
    print("  PART F: Opportunity Identification")
    print("="*70)

    # F1: MSO fields computed but not in prompt
    print("\n--- F1: Computed but Unused MSO Fields ---")

    # Read market_state.py to find all computed fields
    from src.models.market_state_models import TimeframeState, MarketStateObject

    tf_fields = [f for f in TimeframeState.model_fields.keys()]
    mso_fields = [f for f in MarketStateObject.model_fields.keys()]

    print(f"  TimeframeState fields: {tf_fields}")
    print(f"  MarketStateObject fields: {mso_fields}")

    # Check what the prompt builder actually uses
    # The prompt builder serializes the MSO via model_dump() — so ALL fields go to the AI
    # But some fields might be empty/useless

    # Read the prompt builder to see what's injected
    from src.components.primary_analyzer import PrimaryAnalyzer
    import inspect
    source = inspect.getsource(PrimaryAnalyzer.build_prompt)

    # Check for specific fields referenced
    fields_in_prompt = []
    for field in tf_fields + mso_fields:
        if field in source:
            fields_in_prompt.append(field)

    print(f"\n  Fields referenced in build_prompt: {fields_in_prompt}")
    print(f"  Fields computed but not directly referenced: {set(tf_fields + mso_fields) - set(fields_in_prompt)}")

    # F3: Context Agent feasibility
    print("\n\n--- F3: Context Agent Feasibility ---")

    raw = load_raw_batch_results()
    # Get input token stats
    inputs = [r.get("input_tokens", 0) for r in raw.values()]
    cache_creates = [r.get("cache_create", 0) for r in raw.values()]
    cache_reads = [r.get("cache_read", 0) for r in raw.values()]

    avg_input = sum(inputs) / max(1, len(inputs))
    avg_cached = sum(cache_creates) / max(1, len(cache_creates))
    avg_dynamic = avg_input - sum(cache_reads) / max(1, len(cache_reads))

    print(f"  Current per-candle cost:")
    print(f"    Avg input tokens: {avg_input:.0f}")
    print(f"    Avg cached (system prompt): {avg_cached:.0f}")
    print(f"    Avg dynamic (MSO): {avg_dynamic:.0f}")
    print(f"    Avg output tokens: {sum(r.get('output_tokens', 0) for r in raw.values()) / max(1, len(raw)):.0f}")

    # Context Agent estimate
    # Context Agent input = full D1+H4+H1 data (~3000 tokens) + system prompt (~1000 tokens)
    # Context Agent output = session plan (~500 tokens)
    # Entry Agent input = plan (~500 tokens) + M15 data (~800 tokens) + system prompt (~2000 tokens)
    # Entry Agent output = trade decision (~500 tokens)

    candles_per_session = 20  # Extended average
    current_total = avg_input * candles_per_session

    context_agent_in = 4000  # estimate
    context_agent_out = 500
    entry_agent_in = 3300  # estimate: smaller prompt + plan + M15 only
    entry_agent_out = 500
    proposed_total = context_agent_in + context_agent_out + (entry_agent_in + entry_agent_out) * candles_per_session

    print(f"\n  Context Agent feasibility:")
    print(f"    Current: {candles_per_session} × {avg_input:.0f} = {current_total:.0f} input tokens/session")
    print(f"    Proposed: 1 × {context_agent_in} + {candles_per_session} × {entry_agent_in} = {proposed_total:.0f} tokens/session")
    print(f"    Savings: {(1 - proposed_total/current_total)*100:.0f}%")

    return {
        "context_agent_estimate": {
            "current_per_session": round(current_total),
            "proposed_per_session": proposed_total,
            "savings_pct": round((1 - proposed_total/current_total)*100),
            "context_agent_input": context_agent_in,
            "context_agent_output": context_agent_out,
            "entry_agent_input": entry_agent_in,
            "entry_agent_output": entry_agent_out,
        },
    }


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("="*70)
    print("  SYSTEM DEEP DIVE — Complete Understanding")
    print("="*70)

    # Load data
    print("\nLoading data...")
    gbp_sessions = load_gbpusd_sessions()
    gbp_responses = load_gbpusd_responses()
    xau_sessions = load_xauusd_sessions()
    xau_responses = load_xauusd_responses()
    print(f"  GBPUSD: {len(gbp_sessions)} sessions, {len(gbp_responses)} response files")
    print(f"  XAUUSD: {len(xau_sessions)} sessions, {len(xau_responses)} response files")

    all_results = {}

    # Part A
    all_results["part_a"] = part_a(gbp_sessions, gbp_responses, xau_sessions, xau_responses)

    # Part B
    all_results["part_b"] = part_b()

    # Part C
    all_results["part_c"] = part_c(gbp_sessions, gbp_responses)

    # Part E
    all_results["part_e"] = part_e()

    # Part F
    all_results["part_f"] = part_f()

    # Save JSON
    json_path = OUT_DIR / "system_deep_dive_data_20260403.json"

    def clean(obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return obj

    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2, default=clean)
    print(f"\n\nData saved: {json_path}")


if __name__ == "__main__":
    main()
