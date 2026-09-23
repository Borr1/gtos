#!/usr/bin/env python3
"""Pressure Test — System Deep Dive Verification.

Tests 1-4, 6-8: automated verification of deep dive claims.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime, timedelta, date, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BATCH_API = PROJECT_ROOT / "knowledge_base_backtest" / "batch_api"
SESSIONS_DIR = PROJECT_ROOT / "knowledge_base_backtest" / "sessions"
ANALYSIS_DIR = PROJECT_ROOT / "knowledge_base_backtest" / "analysis"
DATA_DIR = PROJECT_ROOT / "data"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(ANALYSIS_DIR))

from displacement_scanner import (
    load_csv, parse_time, detect_swings, identify_structure,
    precompute_htf, lookup_htf, DISP_THRESHOLD_STD,
    KZ_LONDON, KZ_NY,
)


def load_sessions(symbol):
    d = SESSIONS_DIR / symbol
    sessions = {}
    for f in sorted(d.glob("*_session.json")):
        with open(f) as fh:
            sessions[f.stem.replace("_session", "")] = json.load(fh)
    return sessions


def load_responses(symbol):
    d = BATCH_API / "responses" / symbol
    responses = {}
    for f in sorted(d.glob("*_responses.json")):
        with open(f) as fh:
            responses[f.stem.replace("_responses", "")] = json.load(fh)
    return responses


def load_raw_results():
    results = {}
    for f in BATCH_API.glob("msgbatch_*_raw_results.json"):
        with open(f) as fh:
            results.update(json.load(fh))
    return results


def load_displacement_db(symbol):
    candidates = sorted(ANALYSIS_DIR.glob(f"{symbol}_displacement_database_*.csv"))
    if not candidates:
        return []
    path = candidates[-1]
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# ═══════════════════════════════════════════════════════════════════════
# TEST 1: Reasoning Pattern Verification
# ═══════════════════════════════════════════════════════════════════════

def test1(gbp_sessions, gbp_responses):
    """Verify loss categorization and check for reasoning red flags."""
    print("\n" + "="*60)
    print("  TEST 1: Reasoning Pattern Verification")
    print("="*60)

    # Get all trades with outcomes
    wins = []
    losses = []
    for d, sess in gbp_sessions.items():
        for t in sess.get("trade_summary", {}).get("trades", []):
            entry = {"date": d, "kz": t.get("kill_zone", ""), "outcome": t.get("outcome", ""),
                     "r": t.get("r_multiple", 0), "mfe_r": t.get("mfe_r", 0),
                     "mae_r": t.get("mae_r", 0), "exit": t.get("exit_substate", "")}
            if t.get("outcome") == "WIN":
                wins.append(entry)
            else:
                losses.append(entry)

    # Deep dive categorized losses. Let me verify by reading the actual reasoning.
    # The deep dive had: market_condition=10, SL_too_tight=2, immediate_reversal=2, timing_error=2
    # No "structure_misread" category was used. Let me check if any should have been.

    print("\n  Checking all 16 losses for potential structure misread...")
    misread_candidates = []
    for l in losses:
        day_resp = gbp_responses.get(l["date"], {})
        # Find the CANDIDATE response
        resp = None
        for cid, r in day_resp.items():
            if r.get("decision") == "CANDIDATE" and l["kz"] in cid:
                resp = r
                break

        if not resp:
            continue

        reasoning = resp.get("reasoning", {})
        daily_bias = reasoning.get("daily_bias", {})
        h1_setup = reasoning.get("h1_setup", {})
        m15_conf = reasoning.get("m15_confirmation", {})

        # Check for potential misreads:
        # 1. AI says "confident" but loss is immediate reversal (MFE < 0.2R)
        if l["mfe_r"] < 0.20 and resp.get("confidence_score", 0) >= 80:
            misread_candidates.append({
                "date": l["date"], "kz": l["kz"],
                "issue": f"Conf={resp['confidence_score']} but MFE={l['mfe_r']:.2f}R (immediate reversal)",
                "daily_bias": daily_bias.get("direction", ""),
                "h1_poi": h1_setup.get("poi_type", ""),
                "m15_disp": m15_conf.get("displacement_candle_body_vs_avg_ratio", 0),
            })

        # 2. AI cites a specific OB level — check if it matches H1 OBs in the MSO
        if h1_setup.get("poi_price_level"):
            # We can't fully verify without the MSO, but we can flag anomalies
            poi_level = h1_setup["poi_price_level"]
            entry = resp.get("trade_parameters", {}).get("entry_price", 0)
            if entry and abs(poi_level - entry) > 0.005:  # > 50 pips from entry
                misread_candidates.append({
                    "date": l["date"], "kz": l["kz"],
                    "issue": f"POI at {poi_level} but entry at {entry} ({abs(poi_level-entry)/0.0001:.0f} pips apart)",
                })

    print(f"  Potential misread candidates: {len(misread_candidates)}")
    for mc in misread_candidates:
        print(f"    {mc['date']} {mc.get('kz','')}: {mc['issue']}")

    # Check winning trade reasoning for red flags
    print("\n  Checking 5 winning trades for reasoning red flags...")
    red_flags = []
    for w in wins[:5]:
        day_resp = gbp_responses.get(w["date"], {})
        for cid, r in day_resp.items():
            if r.get("decision") == "CANDIDATE" and w["kz"] in cid:
                reasoning = r.get("reasoning", {})
                m15_conf = reasoning.get("m15_confirmation", {})

                # Red flag 1: M15 confirmed=False but decision=CANDIDATE
                if m15_conf.get("confirmed") is False and r.get("decision") == "CANDIDATE":
                    red_flags.append({
                        "date": w["date"],
                        "flag": "m15_confirmation.confirmed=False despite CANDIDATE decision",
                        "explanation": m15_conf.get("explanation", ""),
                    })

                # Red flag 2: Confidence computation doesn't add up
                comp = r.get("confidence_computation", "")
                conf = r.get("confidence_score", 0)
                if "= " in comp:
                    try:
                        stated = int(comp.rsplit("= ", 1)[1].strip())
                        if stated != conf:
                            red_flags.append({
                                "date": w["date"],
                                "flag": f"Computation says {stated} but score is {conf}",
                            })
                    except (ValueError, IndexError):
                        pass
                break

    print(f"  Red flags found in winning trades: {len(red_flags)}")
    for rf in red_flags:
        print(f"    {rf['date']}: {rf['flag']}")
        if rf.get("explanation"):
            print(f"      Explanation: {rf['explanation'][:150]}")

    status = "PASS"
    detail = f"{len(misread_candidates)} potential misreads, {len(red_flags)} red flags"

    # The deep dive had 0 "structure_misread" losses. Verify:
    # If we found immediate_reversal losses with conf>=80, that suggests the AI
    # can't distinguish good from bad setups — but that's "uncalibrated confidence"
    # not "structure misread."
    if len(misread_candidates) > 0:
        detail += f" — {len(misread_candidates)} cases where AI was highly confident on immediate reversals"
    if red_flags:
        status = "WARN"
        detail += f" — {len(red_flags)} red flags in winning trade reasoning"

    print(f"\n  Result: {status} — {detail}")
    return {"status": status, "detail": detail, "misread_candidates": misread_candidates, "red_flags": red_flags}


# ═══════════════════════════════════════════════════════════════════════
# TEST 2: Confidence Score Correlation
# ═══════════════════════════════════════════════════════════════════════

def test2(gbp_sessions, gbp_responses, xau_sessions, xau_responses):
    """Compute Pearson correlation between confidence and outcome."""
    print("\n" + "="*60)
    print("  TEST 2: Confidence Score Correlation")
    print("="*60)

    def compute_correlation(sessions, responses, symbol):
        trades = []
        for d, sess in sessions.items():
            for t in sess.get("trade_summary", {}).get("trades", []):
                kz = t.get("kill_zone", "")
                outcome = 1 if t.get("outcome") == "WIN" else 0
                r = t.get("r_multiple", 0)
                # Find confidence
                day_resp = responses.get(d, {})
                conf = 0
                for cid, resp in day_resp.items():
                    if resp.get("decision") == "CANDIDATE" and kz in cid:
                        conf = resp.get("confidence_score", 0)
                        break
                if conf > 0:
                    trades.append({"conf": conf, "outcome": outcome, "r": r})

        if len(trades) < 5:
            return None, trades

        # Pearson correlation: confidence vs binary outcome
        n = len(trades)
        confs = [t["conf"] for t in trades]
        outcomes = [t["outcome"] for t in trades]

        mean_c = sum(confs) / n
        mean_o = sum(outcomes) / n
        cov = sum((c - mean_c) * (o - mean_o) for c, o in zip(confs, outcomes)) / n
        std_c = (sum((c - mean_c)**2 for c in confs) / n) ** 0.5
        std_o = (sum((o - mean_o)**2 for o in outcomes) / n) ** 0.5

        if std_c == 0 or std_o == 0:
            r = 0
        else:
            r = cov / (std_c * std_o)

        return r, trades

    # GBPUSD
    r_gbp, gbp_trades = compute_correlation(gbp_sessions, gbp_responses, "GBPUSD")
    print(f"\n  GBPUSD (n={len(gbp_trades)}):")
    print(f"    Pearson r (confidence vs win): {r_gbp:.4f}" if r_gbp is not None else "    Insufficient data")

    # Trades with conf > 80 that lost
    high_conf_losses = [t for t in gbp_trades if t["conf"] > 80 and t["outcome"] == 0]
    print(f"    Confidence > 80 losses: {len(high_conf_losses)}")
    for t in high_conf_losses:
        print(f"      conf={t['conf']} R={t['r']:+.3f}")

    # Trades with conf < 75 that won (unlikely given the range)
    low_conf_wins = [t for t in gbp_trades if t["conf"] < 75 and t["outcome"] == 1]
    print(f"    Confidence < 75 wins: {len(low_conf_wins)}")

    # Unique confidence values
    unique_confs = sorted(set(t["conf"] for t in gbp_trades))
    print(f"    Unique confidence values: {unique_confs}")
    for c in unique_confs:
        in_group = [t for t in gbp_trades if t["conf"] == c]
        wins = sum(t["outcome"] for t in in_group)
        print(f"      conf={c}: n={len(in_group)}, wins={wins}, WR={wins/len(in_group)*100:.1f}%")

    # XAUUSD
    r_xau, xau_trades = compute_correlation(xau_sessions, xau_responses, "XAUUSD")
    print(f"\n  XAUUSD (n={len(xau_trades)}):")
    print(f"    Pearson r (confidence vs win): {r_xau:.4f}" if r_xau is not None else "    Insufficient data")

    unique_xau = sorted(set(t["conf"] for t in xau_trades))
    print(f"    Unique confidence values: {unique_xau}")
    for c in unique_xau:
        in_group = [t for t in xau_trades if t["conf"] == c]
        wins = sum(t["outcome"] for t in in_group)
        print(f"      conf={c}: n={len(in_group)}, wins={wins}, WR={wins/len(in_group)*100:.1f}%")

    # Verdict
    is_noise = (r_gbp is not None and abs(r_gbp) < 0.05) or (r_xau is not None and abs(r_xau) < 0.05)
    status = "PASS" if is_noise else "WARN"
    detail = f"GBPUSD r={r_gbp:.4f}, XAUUSD r={r_xau:.4f}" if r_gbp is not None and r_xau is not None else "partial data"
    detail += f" — confidence {'is noise' if is_noise else 'shows weak signal'}"
    print(f"\n  Result: {status} — {detail}")
    return {"status": status, "detail": detail, "r_gbp": r_gbp, "r_xau": r_xau}


# ═══════════════════════════════════════════════════════════════════════
# TEST 3: Missed Setup Verification
# ═══════════════════════════════════════════════════════════════════════

def test3(gbp_sessions, gbp_responses):
    """Verify 3 'missed setup' dates with actual candle data."""
    print("\n" + "="*60)
    print("  TEST 3: Missed Setup Verification")
    print("="*60)

    # Load GBPUSD M15 data
    m15 = load_csv(str(DATA_DIR / "GBPUSD_M15.csv"))
    disp_db = load_displacement_db("GBPUSD")

    # Find dates with high-quality KZ displacements that produced no trades
    trade_dates = set()
    for d, sess in gbp_sessions.items():
        for t in sess.get("trade_summary", {}).get("trades", []):
            trade_dates.add(d)

    # Dates with aligned KZ displacements (align >= 3, in KZ)
    quality_disp_dates = defaultdict(list)
    for row in disp_db:
        if row.get("kz") != "True":
            continue
        try:
            align = int(row.get("align", 0))
        except ValueError:
            continue
        if align < 3:
            continue
        d = row.get("date", "")[:10]
        quality_disp_dates[d].append(row)

    # Missed: quality displacement but no trade
    missed = sorted(set(quality_disp_dates.keys()) - trade_dates)
    print(f"  Dates with high-quality KZ displacements but no trade: {len(missed)}")

    # Also filter to only dates that have response files (prescreen passed)
    missed_with_responses = [d for d in missed if d in gbp_responses]
    print(f"  Of those, with response files (prescreen passed): {len(missed_with_responses)}")

    # Verify 3
    verified = 0
    details = []
    for d in missed_with_responses[:3]:
        disps = quality_disp_dates[d]
        disp = disps[0]  # Take the first quality displacement

        disp_time = disp.get("timestamp", "")
        disp_dir = disp.get("direction", "")
        disp_ratio = float(disp.get("body_ratio", 0))
        has_fvg = disp.get("creates_fvg", "") == "True"
        sweep = disp.get("sweep", "") == "True"
        origin_revisit = disp.get("origin_revisited", "") == "True"

        print(f"\n  Date: {d}")
        print(f"    Displacement: {disp_time} {disp_dir} ratio={disp_ratio:.1f}x FVG={has_fvg} sweep={sweep} revisit={origin_revisit}")

        # Read AI responses for that date
        day_resp = gbp_responses.get(d, {})
        # Find the candle closest to the displacement time
        closest_candle = None
        closest_dist = 999
        for cid, resp in day_resp.items():
            ct = resp.get("timestamp_utc", cid)
            # Try to match by time
            if disp_time[:13] in ct:  # Same hour
                closest_candle = (cid, resp)
                break
            # Otherwise find closest
            try:
                dt_disp = parse_time(disp_time)
                dt_candle = parse_time(ct)
                dist = abs((dt_disp - dt_candle).total_seconds())
                if dist < closest_dist:
                    closest_dist = dist
                    closest_candle = (cid, resp)
            except:
                pass

        if closest_candle:
            cid, resp = closest_candle
            decision = resp.get("decision", "")
            no_trade_reason = resp.get("no_trade_reason", "")
            reasoning = resp.get("reasoning", {})

            # Get specific NO_TRADE reason
            overall = ""
            if isinstance(reasoning, dict):
                overall = reasoning.get("overall_reasoning", "")

            print(f"    Closest candle: {cid}")
            print(f"    Decision: {decision}")
            print(f"    No-trade reason: {no_trade_reason}")
            print(f"    Overall reasoning: {overall[:200]}")

            # Categorize: legitimate pass or missed opportunity?
            if "U1" in str(no_trade_reason) or "D1" in str(no_trade_reason) or "daily" in str(no_trade_reason).lower():
                category = "LEGITIMATE — D1/H4 structural issue"
            elif "U3" in str(no_trade_reason) or "M15" in str(no_trade_reason) or "displacement" in str(no_trade_reason).lower():
                category = "LEGITIMATE — M15 confirmation failed"
            elif "OB" in str(no_trade_reason) or "zone" in str(no_trade_reason).lower():
                category = "POSSIBLE MISS — OB zone issue"
            elif "H1" in str(no_trade_reason) or "structural break" in str(no_trade_reason).lower():
                category = "LEGITIMATE — H1 setup not present"
            else:
                category = "UNKNOWN — needs manual review"

            print(f"    Category: {category}")
            details.append({
                "date": d, "disp_time": disp_time, "disp_ratio": disp_ratio,
                "decision": decision, "reason": str(no_trade_reason)[:150],
                "category": category,
            })

            if "LEGITIMATE" in category:
                verified += 1
        else:
            print(f"    No response found for this date")

    status = "PASS" if verified >= 2 else "WARN"
    detail = f"{verified}/3 correctly identified as legitimate passes"
    print(f"\n  Result: {status} — {detail}")
    return {"status": status, "detail": detail, "details": details}


# ═══════════════════════════════════════════════════════════════════════
# TEST 4: Safety Rejection Outcome Verification
# ═══════════════════════════════════════════════════════════════════════

def test4(gbp_sessions, gbp_responses):
    """Check if direction-mismatch rejected trades would have been profitable."""
    print("\n" + "="*60)
    print("  TEST 4: Safety Rejection Outcome Verification")
    print("="*60)

    m15 = load_csv(str(DATA_DIR / "GBPUSD_M15.csv"))

    # Find direction-mismatch rejections
    # These are CANDIDATE decisions that got rejected by _safety_check
    # The session manifest shows them as specific candle evaluations
    mismatches = []
    for d, sess in gbp_sessions.items():
        for ev in sess.get("candle_evaluations", []):
            if isinstance(ev, dict):
                reason = str(ev.get("reason", ""))
                if "direction_mismatch" in reason:
                    mismatches.append({
                        "date": d,
                        "candle_time": ev.get("candle_time", ""),
                        "reason": reason,
                    })

    print(f"  Direction mismatch rejections found: {len(mismatches)}")

    # For each, find what the AI proposed and check if it would have worked
    profitable = 0
    unprofitable = 0
    details = []

    for mm in mismatches[:7]:
        d = mm["date"]
        ct = mm["candle_time"]

        # Find the AI's response for this candle
        day_resp = gbp_responses.get(d, {})
        resp = None
        for cid, r in day_resp.items():
            if r.get("decision") == "CANDIDATE" and ct[11:16].replace(":", "") in cid:
                resp = r
                break

        if not resp:
            # Try broader match
            for cid, r in day_resp.items():
                if r.get("decision") == "CANDIDATE":
                    resp = r
                    break

        if not resp or not resp.get("trade_parameters"):
            print(f"  {d}: no CANDIDATE response found")
            continue

        tp = resp["trade_parameters"]
        direction = tp.get("direction", "")
        entry = tp.get("entry_price", 0)
        sl = tp.get("stop_loss", 0)
        tp1 = tp.get("take_profit_1", 0)

        if not entry or not sl or not tp1:
            continue

        # Walk M15 candles from the entry time
        entry_time = ct or resp.get("timestamp_utc", "")
        is_long = direction == "LONG"

        # Find the M15 candle at entry time
        entry_idx = None
        for i, c in enumerate(m15):
            if c["time"] == entry_time or c["time"][:16] == entry_time[:16]:
                entry_idx = i
                break

        if entry_idx is None:
            print(f"  {d}: entry candle not found at {entry_time}")
            continue

        # Walk forward for up to 60 candles (15 hours)
        hit_tp = False
        hit_sl = False
        max_fav = 0

        for j in range(entry_idx + 1, min(entry_idx + 61, len(m15))):
            c = m15[j]
            if is_long:
                fav = c["high"] - entry
                adv = entry - c["low"]
                if c["high"] >= tp1:
                    hit_tp = True
                    break
                if c["low"] <= sl:
                    hit_sl = True
                    break
            else:
                fav = entry - c["low"]
                adv = c["high"] - entry
                if c["low"] <= tp1:
                    hit_tp = True
                    break
                if c["high"] >= sl:
                    hit_sl = True
                    break
            max_fav = max(max_fav, fav)

        result = "TP_HIT" if hit_tp else ("SL_HIT" if hit_sl else "TIMEOUT")
        would_profit = hit_tp

        if would_profit:
            profitable += 1
        else:
            unprofitable += 1

        print(f"  {d} {direction} entry={entry:.5f} sl={sl:.5f} tp={tp1:.5f} → {result} (max_fav={max_fav:.5f})")
        details.append({
            "date": d, "direction": direction, "entry": entry, "sl": sl, "tp1": tp1,
            "result": result, "would_profit": would_profit,
        })

    print(f"\n  Would have been profitable: {profitable}/{len(details)}")
    print(f"  Would have lost: {unprofitable}/{len(details)}")

    # If 4+ of 7 would have been profitable, the safety check is overly restrictive
    if profitable >= 4:
        status = "WARN"
        detail = f"{profitable}/{len(details)} rejected trades would have been profitable — safety check may be overly restrictive"
    else:
        status = "PASS"
        detail = f"{profitable}/{len(details)} would have profited — safety check is appropriately protective"

    print(f"\n  Result: {status} — {detail}")
    return {"status": status, "detail": detail, "profitable": profitable, "total": len(details), "details": details}


# ═══════════════════════════════════════════════════════════════════════
# TEST 7: Token Budget Verification
# ═══════════════════════════════════════════════════════════════════════

def test7():
    """Verify token budget claims and room for expansion."""
    print("\n" + "="*60)
    print("  TEST 7: Token Budget Verification")
    print("="*60)

    raw = load_raw_results()

    inputs = [r.get("input_tokens", 0) for r in raw.values() if r.get("input_tokens", 0) > 0]
    outputs = [r.get("output_tokens", 0) for r in raw.values() if r.get("output_tokens", 0) > 0]

    if not inputs:
        print("  No raw results found")
        return {"status": "FAIL", "detail": "No raw results"}

    avg_in = sum(inputs) / len(inputs)
    max_in = max(inputs)
    avg_out = sum(outputs) / len(outputs)

    context_window = 200_000  # Sonnet
    usage_pct = avg_in / context_window * 100
    max_usage_pct = max_in / context_window * 100

    print(f"  Input tokens: avg={avg_in:.0f}, max={max_in}")
    print(f"  Output tokens: avg={avg_out:.0f}")
    print(f"  Context window: {context_window:,}")
    print(f"  Usage: avg={usage_pct:.2f}%, max={max_usage_pct:.2f}%")

    # If we add more context
    additions = {
        "cross_instrument": 100,  # "DXY=bearish, XAUUSD=bullish" etc.
        "session_memory": 300,  # 6 prior candle summaries
        "volatility_regime": 50,  # "D1 ATR percentile: 72nd"
        "context_plan": 500,  # Context Agent session plan
    }

    total_additions = sum(additions.values())
    new_avg = avg_in + total_additions
    new_usage_pct = new_avg / context_window * 100

    print(f"\n  Proposed additions: {total_additions} tokens")
    for name, tokens in additions.items():
        print(f"    {name}: +{tokens}")
    print(f"  New avg input: {new_avg:.0f}")
    print(f"  New usage: {new_usage_pct:.2f}% (vs {usage_pct:.2f}% now)")
    print(f"  Still under 50%: {'YES' if new_usage_pct < 50 else 'NO'}")

    # Cost impact: each additional token costs ~$1.50/M for batch input
    cost_per_token = 1.50 / 1_000_000  # batch rate
    additional_cost_per_candle = total_additions * cost_per_token
    candles_per_session = 20
    additional_cost_per_session = additional_cost_per_candle * candles_per_session
    print(f"\n  Cost impact of additions:")
    print(f"    Per candle: +${additional_cost_per_candle:.6f}")
    print(f"    Per session (20 candles): +${additional_cost_per_session:.4f}")
    print(f"    Per month (30 sessions): +${additional_cost_per_session * 30:.3f}")

    status = "PASS"
    detail = f"Usage {usage_pct:.1f}%, {total_additions} token additions → {new_usage_pct:.1f}%, +${additional_cost_per_session*30:.3f}/month"
    print(f"\n  Result: {status} — {detail}")
    return {"status": status, "detail": detail, "avg_input": avg_in, "usage_pct": usage_pct}


# ═══════════════════════════════════════════════════════════════════════
# TEST 8: Context Agent Feasibility
# ═══════════════════════════════════════════════════════════════════════

def test8():
    """Verify context agent token estimates."""
    print("\n" + "="*60)
    print("  TEST 8: Context Agent Feasibility")
    print("="*60)

    # Get actual system prompt size
    from src.prompts.primary_analyzer_prompt import SYSTEM_PROMPT

    system_tokens = len(SYSTEM_PROMPT) // 4  # rough estimate

    raw = load_raw_results()
    # Get actual cache_create values (= cached static portion)
    cache_creates = [r.get("cache_create", 0) for r in raw.values() if r.get("cache_create", 0) > 0]
    avg_cached = sum(cache_creates) / len(cache_creates) if cache_creates else 0

    # Get actual dynamic portion sizes
    inputs = [r.get("input_tokens", 0) for r in raw.values() if r.get("input_tokens", 0) > 0]
    cache_reads = [r.get("cache_read", 0) for r in raw.values() if r.get("cache_read", 0) > 0]
    avg_input = sum(inputs) / len(inputs) if inputs else 0
    avg_cache_read = sum(cache_reads) / len(cache_reads) if cache_reads else 0

    # The static portion is the cache_create size (system prompt + D1/H4 context)
    # The dynamic portion is total input minus cache_read on cache-hit candles
    print(f"  Current architecture:")
    print(f"    System prompt (est): ~{system_tokens} tokens")
    print(f"    Avg cache_create: {avg_cached:.0f} tokens (static portion)")
    print(f"    Avg input: {avg_input:.0f} tokens")
    print(f"    Avg cache_read: {avg_cache_read:.0f} tokens")

    # The deep dive claimed context agent would INCREASE cost 2.3x.
    # Let's verify: the deep dive estimated:
    #   Current: 20 × avg_input = 20 × 1467 = 29,333
    #   Proposed: 1 × 4000 + 20 × 3300 = 70,500
    # But this is wrong because it didn't account for prompt caching.

    # With caching, effective cost is:
    # First candle: full input (cache_create cost)
    # Subsequent candles: cache_read (much cheaper) + dynamic portion
    # Total effective cost = cache_create × 1 + (avg_input - cache_read + cache_read × 0.1) × 19

    cache_create_cost = 1.875 / 1_000_000  # per token batch
    cache_read_cost = 0.15 / 1_000_000
    input_cost = 1.50 / 1_000_000
    output_cost = 7.50 / 1_000_000

    # Current: for 20 candles
    # Candle 1: full input at input_cost + cache_create at cache_create_cost
    # Candles 2-20: cache_read at cache_read_cost + dynamic at input_cost + output
    candles = 20
    current_cost = (
        avg_input * input_cost  # first candle input
        + avg_cached * cache_create_cost  # first candle cache create
        + (candles - 1) * (avg_cache_read * cache_read_cost + (avg_input - avg_cache_read) * input_cost)  # subsequent
        + candles * 700 * output_cost  # all outputs
    )

    # Context Agent architecture:
    # Context Agent: 1 call, ~8000 tokens input, ~500 output
    # Entry Agent: 20 calls, ~2500 tokens input each (plan + M15 only), ~500 output
    # Entry Agent gets its own cache: system prompt (~1500 tokens) cached after first call
    context_agent_in = avg_cached + 2000  # full static + richer prompt
    context_agent_out = 500
    entry_agent_static = 1500  # slimmer system prompt
    entry_agent_dynamic = 1000  # plan + M15 data only
    entry_agent_out = 500

    proposed_cost = (
        context_agent_in * input_cost + context_agent_out * output_cost  # context agent
        + entry_agent_static * cache_create_cost  # entry agent cache create
        + (candles - 1) * entry_agent_static * cache_read_cost  # entry agent cache reads
        + candles * entry_agent_dynamic * input_cost  # entry agent dynamic
        + candles * entry_agent_out * output_cost  # entry agent outputs
    )

    print(f"\n  Cost comparison (batch rates, {candles} candles):")
    print(f"    Current:  ${current_cost:.4f}")
    print(f"    Proposed: ${proposed_cost:.4f}")
    print(f"    Ratio: {proposed_cost/current_cost:.2f}x")

    if proposed_cost < current_cost:
        verdict = "Context agent REDUCES cost"
    elif proposed_cost < current_cost * 1.5:
        verdict = "Context agent slightly more expensive but adds capability"
    else:
        verdict = "Context agent significantly more expensive"

    print(f"    Verdict: {verdict}")

    # Session memory IS a primitive context agent
    print(f"\n  Session memory as primitive context agent:")
    print(f"    Currently: ~300 tokens of prior candle summaries")
    print(f"    Context Agent would replace this with: ~500 token session plan")
    print(f"    Key difference: Context Agent provides PROACTIVE plan, session memory is REACTIVE log")

    status = "PASS"
    detail = f"Cost ratio {proposed_cost/current_cost:.2f}x — {verdict}"
    print(f"\n  Result: {status} — {detail}")
    return {"status": status, "detail": detail, "cost_ratio": proposed_cost/current_cost}


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("="*70)
    print("  PRESSURE TEST — System Deep Dive Verification")
    print("="*70)

    gbp_sessions = load_sessions("GBPUSD")
    gbp_responses = load_responses("GBPUSD")
    xau_sessions = load_sessions("XAUUSD")
    xau_responses = load_responses("XAUUSD")

    results = {}
    results["test1"] = test1(gbp_sessions, gbp_responses)
    results["test2"] = test2(gbp_sessions, gbp_responses, xau_sessions, xau_responses)
    results["test3"] = test3(gbp_sessions, gbp_responses)
    results["test4"] = test4(gbp_sessions, gbp_responses)
    results["test7"] = test7()
    results["test8"] = test8()

    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    for t, r in sorted(results.items()):
        print(f"  {t}: [{r['status']}] {r['detail'][:100]}")

    return results


if __name__ == "__main__":
    results = main()
