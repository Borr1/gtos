#!/usr/bin/env python3
"""Comprehensive backtest analysis for XAUUSD AI Trading Agent.

Reads all batch results, session files, and response files to produce
a unified trade dataset and exhaustive statistical report.
"""

from __future__ import annotations

import json
import math
import os
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
from scipy import stats as sp_stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = PROJECT_ROOT / "knowledge_base_backtest"
BATCH_DIR = KB_DIR / "batch_api"
SESSIONS_DIR = KB_DIR / "sessions"
RESPONSES_DIR = BATCH_DIR / "responses"
ANALYSIS_DIR = KB_DIR / "analysis"

# Batch ID -> label mapping (determined from data inspection)
BATCH_MAP = {
    "01M9NW1bUnhF4Zf6g3VrNR8g": {"label": "Batch3", "desc": "Oct 2024 – Mar 2025"},
    "01PeezeEy1M3LiNHbKwfaj6o": {"label": "Batch4A", "desc": "Apr 2025 – Mar 2026"},
    "01HJEdo4gP2s5nd9hrgtJUHK": {"label": "Batch4B", "desc": "Apr 2024 – Sep 2024"},
    "0195ug8PMEQvUM2pgrZGdkbB": {"label": "Batch_0195", "desc": "May 2025 (overlap)"},
    "01BNRwLoPRLjDs8XyAXx25XU": {"label": "Batch_BNR", "desc": "Apr-Sep 2025 (0 trades)"},
}

# Only include batches that are the "canonical" runs (Batch3, 4A, 4B)
CANONICAL_BATCHES = ["01M9NW1bUnhF4Zf6g3VrNR8g", "01PeezeEy1M3LiNHbKwfaj6o", "01HJEdo4gP2s5nd9hrgtJUHK"]


def load_all_results():
    """Load results from all canonical batch result files."""
    all_results = []
    for bid in CANONICAL_BATCHES:
        path = BATCH_DIR / f"msgbatch_{bid}_results.json"
        if path.exists():
            results = json.loads(path.read_text())
            label = BATCH_MAP[bid]["label"]
            for r in results:
                r["_batch_id"] = bid
                r["_batch_label"] = label
            all_results.extend(results)
    return all_results


def load_response_file(date_str: str) -> dict | None:
    """Load detailed per-candle responses for a date."""
    path = RESPONSES_DIR / f"{date_str}_responses.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def load_session_file(date_str: str) -> dict | None:
    """Load session manifest for a date."""
    path = SESSIONS_DIR / f"{date_str}_session.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def extract_trades(all_results: list[dict]) -> list[dict]:
    """Extract all trades into flat dicts with every available field."""
    trades = []

    for result in all_results:
        date_str = result["date"]
        batch_label = result["_batch_label"]

        if not result.get("trade_taken"):
            continue

        # Load detailed response data
        responses = load_response_file(date_str)
        session = load_session_file(date_str)

        for trade_info in result.get("trades", []):
            trade = {
                "date": date_str,
                "batch": batch_label,
                "trade_id": trade_info.get("trade_id", ""),
                "kill_zone": trade_info.get("kill_zone", "unknown"),
                "framework": trade_info.get("framework", "unknown"),
                "outcome": trade_info.get("outcome", "unknown"),
                "r_multiple": trade_info.get("r_multiple", 0.0),
            }

            # Parse date info
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                trade["day_of_week"] = dt.strftime("%A")
                trade["month"] = dt.strftime("%Y-%m")
                trade["year_month_num"] = dt.year * 100 + dt.month
            except:
                trade["day_of_week"] = "Unknown"
                trade["month"] = "Unknown"

            # Find the CANDIDATE candle in session data for grade/confidence
            if session:
                for ce in session.get("candle_evaluations", []):
                    if ce.get("decision") == "CANDIDATE" and ce.get("trade_id") == trade["trade_id"]:
                        trade["setup_grade"] = ce.get("setup_grade", "unknown")
                        trade["confidence_score"] = ce.get("confidence", None)
                        break
                    elif ce.get("decision") == "CANDIDATE" and ce.get("kill_zone") == trade["kill_zone"]:
                        trade["setup_grade"] = ce.get("setup_grade", "unknown")
                        trade["confidence_score"] = ce.get("confidence", None)
                        break

            # Find detailed reasoning from response file
            if responses:
                for key, resp in responses.items():
                    if resp.get("decision") == "CANDIDATE" and resp.get("kill_zone") == trade["kill_zone"]:
                        # Trade parameters
                        tp = resp.get("trade_parameters", {}) or {}
                        trade["direction"] = tp.get("direction", "unknown")
                        trade["entry_price"] = tp.get("entry_price")
                        trade["stop_loss"] = tp.get("stop_loss")
                        trade["take_profit_1"] = tp.get("take_profit_1")
                        trade["take_profit_2"] = tp.get("take_profit_2")
                        trade["take_profit_3"] = tp.get("take_profit_3")
                        trade["planned_rr"] = tp.get("risk_reward_ratio")

                        # Calculate SL dollars
                        if trade.get("entry_price") and trade.get("stop_loss"):
                            trade["sl_dollars"] = abs(trade["entry_price"] - trade["stop_loss"])

                        # Confidence & grade from response
                        if "confidence_score" not in trade or trade.get("confidence_score") is None:
                            trade["confidence_score"] = resp.get("confidence_score")
                        if "setup_grade" not in trade or trade.get("setup_grade") == "unknown":
                            trade["setup_grade"] = resp.get("reasoning", {}).get("setup_grade", "unknown")

                        # Reasoning details
                        reasoning = resp.get("reasoning", {})
                        trade["daily_bias"] = reasoning.get("daily_bias", {}).get("direction", "unknown")
                        trade["h4_aligned"] = reasoning.get("h4_alignment", {}).get("aligned")

                        liq = reasoning.get("liquidity_sweep", {})
                        trade["liquidity_pool_type"] = liq.get("pool_type", "unknown")
                        trade["sweep_quality"] = liq.get("sweep_quality", "unknown")

                        m15 = reasoning.get("m15_confirmation", {})
                        trade["displacement_quality"] = m15.get("displacement_quality", "unknown")

                        # Frameworks evaluated
                        fe = resp.get("frameworks_evaluated", {})
                        trade["frameworks_evaluated"] = fe

                        break

            # Fill defaults for missing fields
            trade.setdefault("direction", "unknown")
            trade.setdefault("setup_grade", "unknown")
            trade.setdefault("confidence_score", None)
            trade.setdefault("entry_price", None)
            trade.setdefault("stop_loss", None)
            trade.setdefault("sl_dollars", None)
            trade.setdefault("take_profit_1", None)
            trade.setdefault("take_profit_2", None)
            trade.setdefault("take_profit_3", None)
            trade.setdefault("planned_rr", None)
            trade.setdefault("daily_bias", "unknown")
            trade.setdefault("h4_aligned", None)
            trade.setdefault("liquidity_pool_type", "unknown")
            trade.setdefault("sweep_quality", "unknown")
            trade.setdefault("displacement_quality", "unknown")

            trades.append(trade)

    return trades


def extract_all_candle_decisions(all_results: list[dict]) -> list[dict]:
    """Extract ALL candle decisions (CANDIDATE, NO_TRADE, SKIP) for safety check analysis."""
    candidates = []
    no_trades = []

    for result in all_results:
        date_str = result["date"]
        batch_label = result["_batch_label"]
        responses = load_response_file(date_str)

        if not responses:
            continue

        for key, resp in responses.items():
            decision = resp.get("decision")
            if decision == "CANDIDATE":
                candidates.append({
                    "date": date_str,
                    "batch": batch_label,
                    "key": key,
                    "kill_zone": resp.get("kill_zone"),
                    "framework": resp.get("framework"),
                    "confidence": resp.get("confidence_score"),
                    "grade": resp.get("reasoning", {}).get("setup_grade"),
                    "trade_params": resp.get("trade_parameters"),
                })
            elif decision == "NO_TRADE":
                no_trades.append({
                    "date": date_str,
                    "batch": batch_label,
                    "key": key,
                    "kill_zone": resp.get("kill_zone"),
                    "framework": resp.get("framework", "none"),
                    "reason": resp.get("no_trade_reason", ""),
                    "frameworks_evaluated": resp.get("frameworks_evaluated", {}),
                })

    return candidates, no_trades


def wilson_ci(wins, total, z=1.96):
    """Wilson score interval for binomial proportion."""
    if total == 0:
        return (0, 0)
    p_hat = wins / total
    denom = 1 + z**2 / total
    center = (p_hat + z**2 / (2 * total)) / denom
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * total)) / total) / denom
    return (max(0, center - spread), min(1, center + spread))


def bootstrap_ci(data, n_boot=10000, ci=0.95):
    """Bootstrap confidence interval for mean."""
    if len(data) < 2:
        return (data[0] if data else 0, data[0] if data else 0)

    np.random.seed(42)
    boot_means = []
    arr = np.array(data)
    for _ in range(n_boot):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        boot_means.append(np.mean(sample))

    alpha = (1 - ci) / 2
    lower = np.percentile(boot_means, alpha * 100)
    upper = np.percentile(boot_means, (1 - alpha) * 100)
    return (lower, upper)


def low_sample_flag(n, threshold=15):
    return " ⚠️ LOW SAMPLE" if n < threshold else ""


# ═══════════════════════════════════════════════════════════════════════════
# REPORT SECTIONS
# ═══════════════════════════════════════════════════════════════════════════

def section_data_integrity(all_results, trades):
    lines = []
    lines.append("## 3.1 DATA INTEGRITY REPORT\n")

    # Count sessions per batch
    batch_counts = Counter(r["_batch_label"] for r in all_results)
    for label in ["Batch3", "Batch4A", "Batch4B"]:
        sessions = [r for r in all_results if r["_batch_label"] == label]
        trade_sessions = [r for r in sessions if r.get("trade_taken")]
        dates = sorted(r["date"] for r in sessions)
        lines.append(f"**{label}** ({BATCH_MAP[[k for k,v in BATCH_MAP.items() if v['label']==label][0]]['desc']})")
        lines.append(f"  Sessions evaluated: {len(sessions)}")
        lines.append(f"  Sessions with trades: {len(trade_sessions)}")
        lines.append(f"  Date range: {dates[0]} to {dates[-1]}")

        # Calculate total possible dates (weekdays) in range
        start = datetime.strptime(dates[0], "%Y-%m-%d").date()
        end = datetime.strptime(dates[-1], "%Y-%m-%d").date()
        total_weekdays = sum(1 for d in (start + timedelta(days=i) for i in range((end - start).days + 1)) if d.weekday() < 5)
        pre_screened_out = total_weekdays - len(sessions)
        lines.append(f"  Total weekdays in range: {total_weekdays}")
        lines.append(f"  Pre-screened out (estimated): {pre_screened_out}")
        lines.append(f"  Pre-screen pass rate: {len(sessions)/total_weekdays*100:.1f}%" if total_weekdays > 0 else "")
        lines.append("")

    # Total trade count
    total_trades = len(trades)
    dates_traded = sorted(set(t["date"] for t in trades))
    lines.append(f"**Combined Totals**")
    lines.append(f"  Total sessions: {len(all_results)}")
    lines.append(f"  Total trades: {total_trades}")
    lines.append(f"  Earliest trade: {dates_traded[0] if dates_traded else 'N/A'}")
    lines.append(f"  Latest trade: {dates_traded[-1] if dates_traded else 'N/A'}")

    # Check for duplicate dates across batches
    date_batch_pairs = [(r["date"], r["_batch_label"]) for r in all_results]
    date_counts = Counter(r["date"] for r in all_results)
    dups = {d: c for d, c in date_counts.items() if c > 1}
    if dups:
        lines.append(f"\n  ⚠️ DUPLICATE DATES across batches: {len(dups)}")
        for d, c in sorted(dups.items())[:10]:
            batches_for_date = [r["_batch_label"] for r in all_results if r["date"] == d]
            lines.append(f"    {d}: appears in {batches_for_date}")
    else:
        lines.append(f"  No duplicate dates across canonical batches")

    # Batch 4B anomaly investigation
    lines.append(f"\n**Batch 4B Anomaly Investigation (expected ~95 sessions, got 24):**")
    b4b_results = [r for r in all_results if r["_batch_label"] == "Batch4B"]
    b4b_dates = sorted(r["date"] for r in b4b_results)
    lines.append(f"  Actual dates processed: {len(b4b_dates)}")
    lines.append(f"  Date range: {b4b_dates[0]} to {b4b_dates[-1]}")

    # Check gaps
    if b4b_dates:
        date_objs = [datetime.strptime(d, "%Y-%m-%d").date() for d in b4b_dates]
        # Monthly distribution
        month_counts = Counter(d.strftime("%Y-%m") for d in date_objs)
        lines.append(f"  Monthly distribution: {dict(sorted(month_counts.items()))}")
        lines.append(f"  Note: This batch covers Apr-Sep 2024 but only has 24 sessions")
        lines.append(f"  ~126 weekdays in that range → pre-screen pass rate: {24/126*100:.1f}%")
        lines.append(f"  This suggests heavy pre-screening OR limited M15 data availability")

    lines.append("")
    return "\n".join(lines)


def section_combined_overview(trades):
    lines = []
    lines.append("## 3.2 COMBINED OVERVIEW\n")

    n = len(trades)
    wins = [t for t in trades if t["outcome"] == "WIN"]
    losses = [t for t in trades if t["outcome"] == "LOSS"]
    n_win = len(wins)
    n_loss = len(losses)
    n_be = n - n_win - n_loss

    r_multiples = [t["r_multiple"] for t in trades]
    total_r = sum(r_multiples)

    win_rs = [t["r_multiple"] for t in wins]
    loss_rs = [abs(t["r_multiple"]) for t in losses]

    wr = n_win / n if n > 0 else 0
    wr_ci = wilson_ci(n_win, n)

    expectancy = total_r / n if n > 0 else 0
    exp_ci = bootstrap_ci(r_multiples) if n >= 2 else (0, 0)

    avg_win = statistics.mean(win_rs) if win_rs else 0
    avg_loss = statistics.mean(loss_rs) if loss_rs else 0
    med_win = statistics.median(win_rs) if win_rs else 0
    med_loss = statistics.median(loss_rs) if loss_rs else 0

    gross_wins = sum(win_rs)
    gross_losses = sum(loss_rs)
    profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')

    max_win = max(win_rs) if win_rs else 0
    max_loss = max(loss_rs) if loss_rs else 0

    stdev_r = statistics.stdev(r_multiples) if len(r_multiples) >= 2 else 0
    payoff = avg_win / avg_loss if avg_loss > 0 else float('inf')

    # Trade frequency
    all_dates = sorted(set(t["date"] for t in trades))
    months_active = len(set(t["month"] for t in trades))
    trades_per_month = n / months_active if months_active > 0 else 0

    lines.append(f"Total trades: {n}")
    lines.append(f"  Wins: {n_win}  |  Losses: {n_loss}  |  Breakeven: {n_be}")
    lines.append(f"  Win rate: {wr*100:.1f}%  (95% CI: [{wr_ci[0]*100:.1f}%, {wr_ci[1]*100:.1f}%])")
    lines.append(f"  Total R: {total_r:+.2f}R")
    lines.append(f"  Expectancy: {expectancy:+.3f}R per trade  (95% CI: [{exp_ci[0]:+.3f}R, {exp_ci[1]:+.3f}R])")
    lines.append(f"  Avg winner: {avg_win:.3f}R  |  Avg loser: {avg_loss:.3f}R")
    lines.append(f"  Median winner: {med_win:.3f}R  |  Median loser: {med_loss:.3f}R")
    lines.append(f"  Profit factor: {profit_factor:.3f}")
    lines.append(f"  Max single win: +{max_win:.2f}R  |  Max single loss: -{max_loss:.2f}R")
    lines.append(f"  Std dev of R: {stdev_r:.3f}")
    lines.append(f"  Payoff ratio: {payoff:.3f}")
    lines.append(f"  Active months: {months_active}  |  Trades/month: {trades_per_month:.1f}")
    lines.append("")
    return "\n".join(lines)


def section_breakdown(trades, field, title, section_num):
    lines = []
    lines.append(f"## {section_num} {title}\n")

    groups = defaultdict(list)
    for t in trades:
        key = t.get(field, "unknown")
        groups[key].append(t)

    for key in sorted(groups.keys()):
        group = groups[key]
        n = len(group)
        wins = sum(1 for t in group if t["outcome"] == "WIN")
        rs = [t["r_multiple"] for t in group]
        total_r = sum(rs)
        wr = wins / n if n > 0 else 0
        exp = total_r / n if n > 0 else 0

        win_rs = [t["r_multiple"] for t in group if t["outcome"] == "WIN"]
        loss_rs = [abs(t["r_multiple"]) for t in group if t["outcome"] == "LOSS"]
        avg_w = statistics.mean(win_rs) if win_rs else 0
        avg_l = statistics.mean(loss_rs) if loss_rs else 0

        flag = low_sample_flag(n)
        lines.append(f"**{key}**: {n} trades, {wins}W/{n-wins}L, WR {wr*100:.1f}%, "
                      f"Total {total_r:+.2f}R, Exp {exp:+.3f}R, "
                      f"Avg W {avg_w:.2f}R, Avg L {avg_l:.2f}R{flag}")

    lines.append("")
    return "\n".join(lines)


def section_kill_zone_detail(trades):
    lines = []
    lines.append("## 3.4 KILL ZONE BREAKDOWN (DETAILED)\n")

    for kz in ["london", "ny"]:
        group = [t for t in trades if t["kill_zone"] == kz]
        n = len(group)
        wins = sum(1 for t in group if t["outcome"] == "WIN")
        losses = n - wins
        rs = [t["r_multiple"] for t in group]
        total_r = sum(rs)
        wr = wins / n if n > 0 else 0
        exp = total_r / n if n > 0 else 0

        win_rs = [t["r_multiple"] for t in group if t["outcome"] == "WIN"]
        loss_rs = [abs(t["r_multiple"]) for t in group if t["outcome"] == "LOSS"]
        avg_w = statistics.mean(win_rs) if win_rs else 0
        avg_l = statistics.mean(loss_rs) if loss_rs else 0
        best = max(rs) if rs else 0
        worst = min(rs) if rs else 0

        flag = low_sample_flag(n)
        lines.append(f"**{kz.upper()}**: {n} trades ({wins}W/{losses}L), WR {wr*100:.1f}%, "
                      f"Total {total_r:+.2f}R, Exp {exp:+.3f}R{flag}")
        lines.append(f"  Avg winner: {avg_w:.2f}R  |  Avg loser: {avg_l:.2f}R")
        lines.append(f"  Best: {best:+.2f}R  |  Worst: {worst:+.2f}R")

        # Monthly distribution
        months = Counter(t["month"] for t in group)
        lines.append(f"  Monthly dist: {dict(sorted(months.items()))}")
        lines.append("")

    # Statistical difference test (Mann-Whitney U)
    london_rs = [t["r_multiple"] for t in trades if t["kill_zone"] == "london"]
    ny_rs = [t["r_multiple"] for t in trades if t["kill_zone"] == "ny"]

    if len(london_rs) >= 5 and len(ny_rs) >= 5:
        u_stat, p_val = sp_stats.mannwhitneyu(london_rs, ny_rs, alternative='two-sided')
        lines.append(f"**London vs NY difference test (Mann-Whitney U):**")
        lines.append(f"  U-statistic: {u_stat:.1f}, p-value: {p_val:.4f}")
        if p_val < 0.05:
            lines.append(f"  → Statistically significant at p<0.05")
        elif p_val < 0.10:
            lines.append(f"  → Marginally significant at p<0.10")
        else:
            lines.append(f"  → NOT statistically significant (p={p_val:.3f})")
    else:
        lines.append("**London vs NY difference test: Insufficient data**")

    lines.append("")
    return "\n".join(lines)


def section_cross_tab(trades, field1, field2, title, section_num):
    """Cross-tabulate two fields."""
    lines = []
    lines.append(f"### {title}\n")

    combos = defaultdict(list)
    for t in trades:
        k = f"{t.get(field1, 'unk')} + {t.get(field2, 'unk')}"
        combos[k].append(t)

    for key in sorted(combos.keys()):
        group = combos[key]
        n = len(group)
        wins = sum(1 for t in group if t["outcome"] == "WIN")
        rs = [t["r_multiple"] for t in group]
        total_r = sum(rs)
        exp = total_r / n if n > 0 else 0
        flag = low_sample_flag(n)
        lines.append(f"  {key}: {n} trades, WR {wins/n*100:.1f}%, Exp {exp:+.3f}R, Total {total_r:+.2f}R{flag}")

    lines.append("")
    return "\n".join(lines)


def section_monthly_performance(trades):
    lines = []
    lines.append("## 3.8 MONTHLY PERFORMANCE\n")

    monthly = defaultdict(list)
    for t in trades:
        monthly[t["month"]].append(t)

    cumulative_r = 0
    months_data = []
    for month in sorted(monthly.keys()):
        group = monthly[month]
        n = len(group)
        wins = sum(1 for t in group if t["outcome"] == "WIN")
        rs = [t["r_multiple"] for t in group]
        total_r = sum(rs)
        cumulative_r += total_r
        months_data.append((month, total_r))
        lines.append(f"  {month}: {n} trades ({wins}W/{n-wins}L), "
                      f"{total_r:+.2f}R, Cumulative: {cumulative_r:+.2f}R")

    # Simple linear regression on monthly R
    if len(months_data) >= 3:
        y = [m[1] for m in months_data]
        x = list(range(len(y)))
        slope, intercept, r_val, p_val, std_err = sp_stats.linregress(x, y)
        lines.append(f"\n  Linear trend: slope={slope:+.3f}R/month, R²={r_val**2:.3f}, p={p_val:.3f}")
        if slope > 0:
            lines.append(f"  → Improving trend")
        else:
            lines.append(f"  → Degrading trend")

    lines.append("")
    return "\n".join(lines)


def section_temporal_stability(trades):
    lines = []
    lines.append("## 3.9 TEMPORAL STABILITY\n")

    sorted_trades = sorted(trades, key=lambda t: t["date"])
    n = len(sorted_trades)
    third = n // 3

    for i, label in enumerate(["First third", "Second third", "Final third"]):
        if i < 2:
            group = sorted_trades[i * third:(i + 1) * third]
        else:
            group = sorted_trades[i * third:]

        ng = len(group)
        wins = sum(1 for t in group if t["outcome"] == "WIN")
        rs = [t["r_multiple"] for t in group]
        total_r = sum(rs)
        wr = wins / ng if ng > 0 else 0
        exp = total_r / ng if ng > 0 else 0

        win_rs = [t["r_multiple"] for t in group if t["outcome"] == "WIN"]
        loss_rs = [abs(t["r_multiple"]) for t in group if t["outcome"] == "LOSS"]
        avg_w = statistics.mean(win_rs) if win_rs else 0
        avg_l = statistics.mean(loss_rs) if loss_rs else 0

        date_range = f"{group[0]['date']} to {group[-1]['date']}" if group else "N/A"
        flag = low_sample_flag(ng)
        lines.append(f"**{label}** ({ng} trades, {date_range}):{flag}")
        lines.append(f"  WR {wr*100:.1f}%, Exp {exp:+.3f}R, Avg W {avg_w:.2f}R, Avg L {avg_l:.2f}R, Total {total_r:+.2f}R")

    lines.append("")
    return "\n".join(lines)


def section_safety_check(all_results, candidates, no_trades):
    lines = []
    lines.append("## 3.10 SAFETY CHECK ANALYSIS\n")

    total_candle_decisions = sum(len(r.get("decisions", [])) for r in all_results)
    n_candidates = len(candidates)

    # Count trades (candidates that became trades)
    trade_dates_kz = set()
    for r in all_results:
        if r.get("trade_taken"):
            for t in r.get("trades", []):
                trade_dates_kz.add((r["date"], t.get("kill_zone")))

    passed = len(trade_dates_kz)
    rejected = n_candidates - passed  # candidates that were generated but some may have been safety-rejected

    lines.append(f"Total candle evaluations: {total_candle_decisions}")
    lines.append(f"CANDIDATE signals generated: {n_candidates}")
    lines.append(f"Trades executed: {passed}")
    lines.append(f"Note: In batch backtest, CANDIDATE → trade is near-automatic (debate auto-approved)")
    lines.append(f"      Safety checks are embedded in the PA prompt, not a separate step")

    # Analyze NO_TRADE reasons
    reason_counts = Counter()
    for nt in no_trades:
        reason = nt.get("reason", "unknown")
        # Categorize
        reason_lower = reason.lower() if reason else ""
        if "choch" in reason_lower or "confirmation" in reason_lower:
            reason_counts["No M15 CHoCH/confirmation"] += 1
        elif "displacement" in reason_lower:
            reason_counts["No displacement"] += 1
        elif "bias" in reason_lower or "conflict" in reason_lower:
            reason_counts["Bias conflict"] += 1
        elif "sweep" in reason_lower:
            reason_counts["No liquidity sweep"] += 1
        elif "structure" in reason_lower:
            reason_counts["Structure unclear"] += 1
        elif "poi" in reason_lower or "ob" in reason_lower or "fvg" in reason_lower:
            reason_counts["No POI interaction"] += 1
        else:
            reason_counts["Other"] += 1

    lines.append(f"\nNO_TRADE reason categories (from {len(no_trades)} candle evaluations):")
    for reason, count in reason_counts.most_common(10):
        pct = count / len(no_trades) * 100 if no_trades else 0
        lines.append(f"  {reason}: {count} ({pct:.1f}%)")

    lines.append("")
    return "\n".join(lines)


def section_framework_investigation(no_trades):
    lines = []
    lines.append("## 3.25 FRAMEWORK 2-4 INVESTIGATION\n")

    # Check frameworks_evaluated in NO_TRADE responses
    framework_mentions = defaultdict(lambda: {"qualified": 0, "not_qualified": 0, "reasons": Counter()})

    for nt in no_trades:
        fe = nt.get("frameworks_evaluated", {})
        for fw_name, fw_data in fe.items():
            if isinstance(fw_data, dict):
                if fw_data.get("qualified"):
                    framework_mentions[fw_name]["qualified"] += 1
                else:
                    framework_mentions[fw_name]["not_qualified"] += 1
                    reason = fw_data.get("reason", "unknown")
                    # Shorten reason
                    if len(reason) > 80:
                        reason = reason[:77] + "..."
                    framework_mentions[fw_name]["reasons"][reason] += 1

    for fw_name in ["session_sweep", "ob_retest", "equal_sweep", "fvg_fill"]:
        data = framework_mentions.get(fw_name, {"qualified": 0, "not_qualified": 0, "reasons": Counter()})
        total = data["qualified"] + data["not_qualified"]
        lines.append(f"**{fw_name}**:")
        lines.append(f"  Evaluated: {total} times")
        lines.append(f"  Qualified: {data['qualified']} ({data['qualified']/total*100:.1f}% of evaluations)" if total > 0 else "  Qualified: 0")
        lines.append(f"  Not qualified: {data['not_qualified']}")
        if data["reasons"]:
            lines.append(f"  Top rejection reasons:")
            for reason, count in data["reasons"].most_common(3):
                lines.append(f"    - {reason}: {count}")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


def section_streaks(trades):
    lines = []
    lines.append("## 3.18 WIN/LOSS STREAK ANALYSIS\n")

    sorted_trades = sorted(trades, key=lambda t: t["date"])

    # Calculate streaks
    max_win_streak = 0
    max_loss_streak = 0
    current_win = 0
    current_loss = 0
    win_streaks = []
    loss_streaks = []

    for t in sorted_trades:
        if t["outcome"] == "WIN":
            current_win += 1
            if current_loss > 0:
                loss_streaks.append(current_loss)
            current_loss = 0
        else:
            current_loss += 1
            if current_win > 0:
                win_streaks.append(current_win)
            current_win = 0

    if current_win > 0:
        win_streaks.append(current_win)
    if current_loss > 0:
        loss_streaks.append(current_loss)

    max_win_streak = max(win_streaks) if win_streaks else 0
    max_loss_streak = max(loss_streaks) if loss_streaks else 0
    avg_win_streak = statistics.mean(win_streaks) if win_streaks else 0
    avg_loss_streak = statistics.mean(loss_streaks) if loss_streaks else 0

    lines.append(f"Max consecutive wins: {max_win_streak}")
    lines.append(f"Max consecutive losses: {max_loss_streak}")
    lines.append(f"Avg win streak: {avg_win_streak:.1f}")
    lines.append(f"Avg loss streak: {avg_loss_streak:.1f}")

    # Max drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in sorted_trades:
        cumulative += t["r_multiple"]
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    lines.append(f"Max drawdown: {max_dd:.2f}R (peak to trough)")
    lines.append("")
    return "\n".join(lines)


def section_cross_filter(trades):
    lines = []
    lines.append("## 3.19 CROSS-FILTER ANALYSIS\n")

    def calc_stats(group):
        n = len(group)
        if n == 0:
            return {"n": 0, "wr": 0, "exp": 0, "total_r": 0}
        wins = sum(1 for t in group if t["outcome"] == "WIN")
        rs = [t["r_multiple"] for t in group]
        return {"n": n, "wr": wins / n, "exp": sum(rs) / n, "total_r": sum(rs)}

    filters = {
        "ALL trades": lambda t: True,
        "NY only": lambda t: t["kill_zone"] == "ny",
        "London only": lambda t: t["kill_zone"] == "london",
        "A+ only": lambda t: t.get("setup_grade") == "A+",
        "A only": lambda t: t.get("setup_grade") == "A",
        "NY + A+": lambda t: t["kill_zone"] == "ny" and t.get("setup_grade") == "A+",
        "NY + A": lambda t: t["kill_zone"] == "ny" and t.get("setup_grade") == "A",
        "London + A+": lambda t: t["kill_zone"] == "london" and t.get("setup_grade") == "A+",
        "London + A": lambda t: t["kill_zone"] == "london" and t.get("setup_grade") == "A",
        "LONG only": lambda t: t.get("direction") == "LONG",
        "SHORT only": lambda t: t.get("direction") == "SHORT",
        "Confidence >= 75": lambda t: (t.get("confidence_score") or 0) >= 75,
        "Confidence >= 80": lambda t: (t.get("confidence_score") or 0) >= 80,
        "Confidence >= 85": lambda t: (t.get("confidence_score") or 0) >= 85,
        "NY + Confidence >= 75": lambda t: t["kill_zone"] == "ny" and (t.get("confidence_score") or 0) >= 75,
        "SL <= $8": lambda t: t.get("sl_dollars") is not None and t["sl_dollars"] <= 8,
        "SL > $8": lambda t: t.get("sl_dollars") is not None and t["sl_dollars"] > 8,
        "session_sweep only": lambda t: t.get("framework") == "session_sweep",
        "Batch3": lambda t: t.get("batch") == "Batch3",
        "Batch4A": lambda t: t.get("batch") == "Batch4A",
        "Batch4B": lambda t: t.get("batch") == "Batch4B",
    }

    lines.append(f"| {'Filter':<30} | {'Trades':>6} | {'Win Rate':>8} | {'Expectancy':>10} | {'Total R':>8} |")
    lines.append(f"|{'-'*30}--|{'-'*6}--|{'-'*8}--|{'-'*10}--|{'-'*8}--|")

    best_exp = -999
    best_filter = ""

    for label, fn in filters.items():
        group = [t for t in trades if fn(t)]
        s = calc_stats(group)
        flag = " ⚠️" if s["n"] < 15 else ""
        lines.append(f"| {label:<30} | {s['n']:>6} | {s['wr']*100:>7.1f}% | {s['exp']:>+9.3f}R | {s['total_r']:>+7.2f}R |{flag}")

        if s["n"] >= 20 and s["exp"] > best_exp:
            best_exp = s["exp"]
            best_filter = label

    lines.append("")
    if best_filter:
        lines.append(f"**Best filter (≥20 trades): {best_filter} with expectancy {best_exp:+.3f}R**")

    lines.append("")
    return "\n".join(lines), best_filter


def section_statistical_significance(trades, best_filter_trades=None, best_filter_label=""):
    lines = []
    lines.append("## 3.20 STATISTICAL SIGNIFICANCE\n")

    rs = [t["r_multiple"] for t in trades]
    n = len(rs)

    # One-sample t-test: H0: mean = 0
    t_stat, p_val = sp_stats.ttest_1samp(rs, 0)
    lines.append(f"**All trades (n={n})**")
    lines.append(f"  H0: true expectancy = 0")
    lines.append(f"  t-statistic: {t_stat:.3f}")
    lines.append(f"  p-value: {p_val:.4f}")

    if p_val < 0.05:
        lines.append(f"  → REJECT H0 at p < 0.05 ✓")
    elif p_val < 0.10:
        lines.append(f"  → REJECT H0 at p < 0.10 (marginal)")
    else:
        lines.append(f"  → FAIL TO REJECT H0 (p = {p_val:.3f})")

    # Bootstrap CI
    ci = bootstrap_ci(rs)
    lines.append(f"  Bootstrap 95% CI on expectancy: [{ci[0]:+.3f}R, {ci[1]:+.3f}R]")
    if ci[0] > 0:
        lines.append(f"  → CI entirely above zero — edge is statistically supported")
    elif ci[1] < 0:
        lines.append(f"  → CI entirely below zero — system is losing")
    else:
        lines.append(f"  → CI spans zero — cannot confirm edge")

    # Sample size needed for 95% confidence
    if n >= 2:
        mean_r = statistics.mean(rs)
        std_r = statistics.stdev(rs)
        if mean_r > 0 and std_r > 0:
            # n needed: (z * std / margin)^2 where margin = mean_r (we want CI to exclude 0)
            n_needed = math.ceil((1.96 * std_r / mean_r) ** 2)
            lines.append(f"  Sample size needed for 95% CI to exclude zero: ~{n_needed} trades")
        else:
            lines.append(f"  Cannot estimate needed sample size (mean={mean_r:.3f}, std={std_r:.3f})")

    # Best filter subset
    if best_filter_trades and len(best_filter_trades) >= 5:
        rs_bf = [t["r_multiple"] for t in best_filter_trades]
        t_stat_bf, p_val_bf = sp_stats.ttest_1samp(rs_bf, 0)
        ci_bf = bootstrap_ci(rs_bf)
        lines.append(f"\n**Best filter subset: {best_filter_label} (n={len(rs_bf)})**")
        lines.append(f"  t-stat: {t_stat_bf:.3f}, p-value: {p_val_bf:.4f}")
        lines.append(f"  Bootstrap 95% CI: [{ci_bf[0]:+.3f}R, {ci_bf[1]:+.3f}R]")

    lines.append("")
    return "\n".join(lines)


def section_monte_carlo(trades, best_filter_trades=None, best_filter_label=""):
    lines = []
    lines.append("## 3.21 MONTE CARLO EQUITY SIMULATION\n")

    np.random.seed(42)

    def run_sim(rs, label, n_trades=100, n_sims=10000):
        arr = np.array(rs)
        results = []
        max_dds = []
        for _ in range(n_sims):
            samples = np.random.choice(arr, size=n_trades, replace=True)
            cum = np.cumsum(samples)
            results.append(cum[-1])
            # Max drawdown
            peak = np.maximum.accumulate(cum)
            dd = peak - cum
            max_dds.append(np.max(dd))

        results = np.array(results)
        max_dds = np.array(max_dds)

        lines.append(f"**{label} ({len(rs)} actual trades, simulated to {n_trades}):**")
        lines.append(f"  Median final R after {n_trades} trades: {np.median(results):+.2f}R")
        lines.append(f"  5th percentile (worst case): {np.percentile(results, 5):+.2f}R")
        lines.append(f"  95th percentile (best case): {np.percentile(results, 95):+.2f}R")

        # Probability of profit
        prob_50 = np.mean(np.cumsum(np.random.choice(arr, size=(n_sims, 50), replace=True), axis=1)[:, -1] > 0)
        prob_100 = np.mean(results > 0)
        lines.append(f"  P(profitable after 50 trades): {prob_50*100:.1f}%")
        lines.append(f"  P(profitable after {n_trades} trades): {prob_100*100:.1f}%")

        lines.append(f"  Max drawdown — median: {np.median(max_dds):.2f}R, "
                      f"5th pct: {np.percentile(max_dds, 5):.2f}R, "
                      f"95th pct: {np.percentile(max_dds, 95):.2f}R")
        lines.append("")

    rs = [t["r_multiple"] for t in trades]
    run_sim(rs, "All trades")

    if best_filter_trades and len(best_filter_trades) >= 10:
        rs_bf = [t["r_multiple"] for t in best_filter_trades]
        run_sim(rs_bf, f"Best filter: {best_filter_label}")

    return "\n".join(lines)


def section_kelly(trades):
    lines = []
    lines.append("## 3.22 KELLY CRITERION\n")

    n = len(trades)
    wins = [t for t in trades if t["outcome"] == "WIN"]
    losses = [t for t in trades if t["outcome"] == "LOSS"]

    W = len(wins) / n if n > 0 else 0
    L = 1 - W

    avg_win = statistics.mean([t["r_multiple"] for t in wins]) if wins else 0
    avg_loss = statistics.mean([abs(t["r_multiple"]) for t in losses]) if losses else 1

    # Kelly: f* = W/L_avg - L/W_avg  (simplified for R-multiples where loss = 1R)
    # More standard: f* = (p * b - q) / b where b = avg_win/avg_loss, p = win_rate, q = 1-p
    b = avg_win / avg_loss if avg_loss > 0 else 0
    kelly = (W * b - L) / b if b > 0 else 0

    lines.append(f"Win rate (W): {W*100:.1f}%")
    lines.append(f"Avg winner: {avg_win:.3f}R  |  Avg loser: {avg_loss:.3f}R")
    lines.append(f"Payoff ratio (b): {b:.3f}")
    lines.append(f"Full Kelly: {kelly*100:.2f}% of capital per trade")
    lines.append(f"Half Kelly: {kelly/2*100:.2f}%")
    lines.append(f"Quarter Kelly: {kelly/4*100:.2f}%")
    lines.append(f"Current system: 1.00% per trade")

    if kelly > 0:
        if 0.01 < kelly / 4:
            lines.append(f"→ 1% is BELOW quarter Kelly — conservative")
        elif 0.01 < kelly / 2:
            lines.append(f"→ 1% is between quarter and half Kelly — appropriate")
        elif 0.01 < kelly:
            lines.append(f"→ 1% is between half and full Kelly — moderate")
        else:
            lines.append(f"→ 1% EXCEEDS full Kelly — too aggressive!")
    else:
        lines.append(f"→ Kelly is NEGATIVE — system has no edge by this measure")

    lines.append("")
    return "\n".join(lines)


def section_sl_sizing(trades):
    lines = []
    lines.append("## 3.14 SL SIZING ANALYSIS\n")

    trades_with_sl = [t for t in trades if t.get("sl_dollars") is not None]

    if not trades_with_sl:
        lines.append("No SL dollar data available.")
        lines.append("")
        return "\n".join(lines)

    sls = [t["sl_dollars"] for t in trades_with_sl]
    lines.append(f"Trades with SL data: {len(trades_with_sl)}/{len(trades)}")
    lines.append(f"SL distribution: min ${min(sls):.2f}, median ${statistics.median(sls):.2f}, "
                  f"mean ${statistics.mean(sls):.2f}, max ${max(sls):.2f}")

    # Bucket analysis
    buckets = {
        "<$5": lambda s: s < 5,
        "$5-$8": lambda s: 5 <= s < 8,
        "$8-$12": lambda s: 8 <= s < 12,
        "$12-$18": lambda s: 12 <= s < 18,
        "$18+": lambda s: s >= 18,
    }

    for label, fn in buckets.items():
        group = [t for t in trades_with_sl if fn(t["sl_dollars"])]
        n = len(group)
        if n == 0:
            lines.append(f"  {label}: 0 trades")
            continue
        wins = sum(1 for t in group if t["outcome"] == "WIN")
        rs = [t["r_multiple"] for t in group]
        exp = sum(rs) / n
        flag = low_sample_flag(n)
        lines.append(f"  {label}: {n} trades, WR {wins/n*100:.1f}%, Exp {exp:+.3f}R{flag}")

    lines.append("")
    return "\n".join(lines)


def section_confidence_score(trades):
    lines = []
    lines.append("## 3.15 CONFIDENCE SCORE VS OUTCOME\n")

    trades_with_conf = [t for t in trades if t.get("confidence_score") is not None]

    if not trades_with_conf:
        lines.append("No confidence score data available.")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"Trades with confidence data: {len(trades_with_conf)}/{len(trades)}")

    confs = [t["confidence_score"] for t in trades_with_conf]
    lines.append(f"Confidence distribution: min {min(confs)}, median {statistics.median(confs)}, "
                  f"mean {statistics.mean(confs):.1f}, max {max(confs)}")

    # Bucket analysis
    buckets = [
        ("<70", lambda c: c < 70),
        ("70-79", lambda c: 70 <= c < 80),
        ("80-84", lambda c: 80 <= c < 85),
        ("85", lambda c: c == 85),
        ("86-90", lambda c: 86 <= c < 91),
        ("90+", lambda c: c >= 91),
    ]

    for label, fn in buckets:
        group = [t for t in trades_with_conf if fn(t["confidence_score"])]
        n = len(group)
        if n == 0:
            continue
        wins = sum(1 for t in group if t["outcome"] == "WIN")
        rs = [t["r_multiple"] for t in group]
        exp = sum(rs) / n
        flag = low_sample_flag(n)
        lines.append(f"  Confidence {label}: {n} trades, WR {wins/n*100:.1f}%, Exp {exp:+.3f}R{flag}")

    # Spearman correlation
    rs_vals = [t["r_multiple"] for t in trades_with_conf]
    conf_vals = [t["confidence_score"] for t in trades_with_conf]
    if len(set(conf_vals)) > 1:
        rho, p_val = sp_stats.spearmanr(conf_vals, rs_vals)
        lines.append(f"\n  Spearman correlation (confidence vs R): ρ={rho:.3f}, p={p_val:.4f}")
        if p_val < 0.05:
            lines.append(f"  → Confidence IS predictive")
        else:
            lines.append(f"  → Confidence is NOT predictive")
    else:
        lines.append(f"\n  All confidence scores identical ({conf_vals[0]}) — cannot compute correlation")

    lines.append("")
    return "\n".join(lines)


def section_planned_rr(trades):
    lines = []
    lines.append("## 3.13 TP HIT RATE / PLANNED RR ANALYSIS\n")

    trades_with_rr = [t for t in trades if t.get("planned_rr") is not None]

    if not trades_with_rr:
        lines.append("No planned RR data available.")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"Trades with planned RR: {len(trades_with_rr)}/{len(trades)}")
    rrs = [t["planned_rr"] for t in trades_with_rr]
    lines.append(f"Planned RR distribution: min {min(rrs):.2f}, median {statistics.median(rrs):.2f}, "
                  f"mean {statistics.mean(rrs):.2f}, max {max(rrs):.2f}")

    # Winners: actual R vs planned RR
    winners_with_rr = [t for t in trades_with_rr if t["outcome"] == "WIN"]
    losers_with_rr = [t for t in trades_with_rr if t["outcome"] == "LOSS"]

    if winners_with_rr:
        lines.append(f"\nWinners ({len(winners_with_rr)}):")
        for w in sorted(winners_with_rr, key=lambda x: x["date"]):
            lines.append(f"  {w['date']} {w['kill_zone']:>7} {w['framework']:>15}: "
                          f"Planned RR {w['planned_rr']:.2f}, Actual {w['r_multiple']:+.2f}R")

    if losers_with_rr:
        lines.append(f"\nLosers ({len(losers_with_rr)}):")
        for l in sorted(losers_with_rr, key=lambda x: x["date"]):
            lines.append(f"  {l['date']} {l['kill_zone']:>7} {l['framework']:>15}: "
                          f"Planned RR {l['planned_rr']:.2f}, Actual {l['r_multiple']:+.2f}R")

    lines.append("")
    return "\n".join(lines)


def section_pre_screening(all_results):
    lines = []
    lines.append("## 3.24 PRE-SCREENING EFFICIENCY\n")

    for label in ["Batch3", "Batch4A", "Batch4B"]:
        sessions = [r for r in all_results if r["_batch_label"] == label]
        if not sessions:
            continue

        dates = sorted(r["date"] for r in sessions)
        start = datetime.strptime(dates[0], "%Y-%m-%d").date()
        end = datetime.strptime(dates[-1], "%Y-%m-%d").date()
        total_weekdays = sum(1 for d in (start + timedelta(days=i) for i in range((end - start).days + 1)) if d.weekday() < 5)

        n_sessions = len(sessions)
        n_trades = sum(1 for r in sessions if r.get("trade_taken"))
        n_wins = sum(1 for r in sessions if r.get("outcome") == "WIN")

        pre_screened_out = total_weekdays - n_sessions

        lines.append(f"**{label}:**")
        lines.append(f"  Total weekdays in range: {total_weekdays}")
        lines.append(f"  Sessions that passed pre-screening: {n_sessions} ({n_sessions/total_weekdays*100:.1f}%)")
        lines.append(f"  Pre-screened out: ~{pre_screened_out} ({pre_screened_out/total_weekdays*100:.1f}%)")
        lines.append(f"  Sessions → trades: {n_trades}/{n_sessions} ({n_trades/n_sessions*100:.1f}%)")
        lines.append(f"  Sessions → winning trades: {n_wins}/{n_sessions} ({n_wins/n_sessions*100:.1f}%)")

        # Monthly breakdown
        monthly = defaultdict(int)
        for r in sessions:
            m = r["date"][:7]
            monthly[m] += 1
        lines.append(f"  Monthly session counts: {dict(sorted(monthly.items()))}")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


def section_recommendations(trades, all_results):
    lines = []
    lines.append("## STEP 4: SUMMARY RECOMMENDATIONS\n")

    n = len(trades)
    total_r = sum(t["r_multiple"] for t in trades)
    exp = total_r / n if n > 0 else 0

    # 1. Kill/Keep decisions
    lines.append("### 1. KILL/KEEP DECISIONS\n")

    london = [t for t in trades if t["kill_zone"] == "london"]
    ny = [t for t in trades if t["kill_zone"] == "ny"]

    london_exp = sum(t["r_multiple"] for t in london) / len(london) if london else 0
    ny_exp = sum(t["r_multiple"] for t in ny) / len(ny) if ny else 0
    london_wr = sum(1 for t in london if t["outcome"] == "WIN") / len(london) if london else 0
    ny_wr = sum(1 for t in ny if t["outcome"] == "WIN") / len(ny) if ny else 0

    lines.append(f"London: {len(london)} trades, WR {london_wr*100:.1f}%, Exp {london_exp:+.3f}R")
    lines.append(f"NY:     {len(ny)} trades, WR {ny_wr*100:.1f}%, Exp {ny_exp:+.3f}R")

    if london_exp < 0 and ny_exp > 0:
        lines.append("→ CONSIDER dropping London (negative expectancy) but sample sizes are small")
    elif ny_exp < 0 and london_exp > 0:
        lines.append("→ CONSIDER dropping NY")
    else:
        lines.append("→ Keep both kill zones — neither is conclusively negative")

    # Grade analysis
    grades = defaultdict(list)
    for t in trades:
        grades[t.get("setup_grade", "unknown")].append(t)

    lines.append("")
    for g in sorted(grades.keys()):
        group = grades[g]
        ge = sum(t["r_multiple"] for t in group) / len(group) if group else 0
        gw = sum(1 for t in group if t["outcome"] == "WIN") / len(group) if group else 0
        lines.append(f"Grade {g}: {len(group)} trades, WR {gw*100:.1f}%, Exp {ge:+.3f}R")

    # 2. TP optimization
    lines.append("\n### 2. TP OPTIMIZATION\n")

    winners = [t for t in trades if t["outcome"] == "WIN"]
    losers = [t for t in trades if t["outcome"] == "LOSS"]
    avg_winner_r = statistics.mean([t["r_multiple"] for t in winners]) if winners else 0

    lines.append(f"Average winner achieves: {avg_winner_r:.2f}R")
    lines.append(f"Note: MFE data not available in batch results — cannot do precise TP optimization")
    lines.append(f"Recommendation: Track MFE in live/demo to enable this analysis")

    # 3. Framework pruning
    lines.append("\n### 3. FRAMEWORK PRUNING\n")

    fw_counts = Counter(t["framework"] for t in trades)
    for fw, count in fw_counts.most_common():
        group = [t for t in trades if t["framework"] == fw]
        ge = sum(t["r_multiple"] for t in group) / len(group) if group else 0
        lines.append(f"{fw}: {count} trades, Exp {ge:+.3f}R")

    if fw_counts.get("session_sweep", 0) > 0.8 * n:
        lines.append("→ session_sweep dominates. Other frameworks rarely trigger.")
        lines.append("→ Consider: either fix framework 2-4 triggers or simplify to session_sweep only")

    # 4. Filter recommendations
    lines.append("\n### 4. FILTER RECOMMENDATIONS\n")
    lines.append("See cross-filter table (3.19) for the optimal filter combination.")

    # 5. Statistical verdict
    lines.append("\n### 5. STATISTICAL VERDICT\n")

    rs = [t["r_multiple"] for t in trades]
    t_stat, p_val = sp_stats.ttest_1samp(rs, 0)
    ci = bootstrap_ci(rs)

    lines.append(f"Overall expectancy: {exp:+.3f}R per trade")
    lines.append(f"t-test p-value: {p_val:.4f}")
    lines.append(f"Bootstrap 95% CI: [{ci[0]:+.3f}R, {ci[1]:+.3f}R]")

    if ci[0] > 0:
        lines.append("→ EDGE CONFIRMED: 95% CI entirely above zero")
    elif p_val < 0.10:
        lines.append("→ MARGINAL EDGE: suggestive but not conclusive")
    else:
        lines.append("→ NO CONFIRMED EDGE: Cannot reject null hypothesis")

    # 6. Kelly sizing
    lines.append("\n### 6. KELLY SIZING VERDICT\n")
    W = sum(1 for t in trades if t["outcome"] == "WIN") / n if n > 0 else 0
    avg_w = statistics.mean([t["r_multiple"] for t in winners]) if winners else 0
    avg_l = statistics.mean([abs(t["r_multiple"]) for t in losers]) if losers else 1
    b = avg_w / avg_l if avg_l > 0 else 0
    kelly = (W * b - (1 - W)) / b if b > 0 else 0

    if kelly > 0:
        lines.append(f"Full Kelly: {kelly*100:.2f}%")
        lines.append(f"Quarter Kelly: {kelly/4*100:.2f}%")
        if kelly / 4 > 0.01:
            lines.append("→ 1% risk is conservative (below quarter Kelly) — appropriate for unproven system")
        else:
            lines.append("→ 1% risk is near or above quarter Kelly — appropriate")
    else:
        lines.append(f"Kelly is negative ({kelly*100:.2f}%) — suggests no mathematical edge to size")
        lines.append("→ 1% risk is fine for demo testing but system needs improvement for live")

    # 7. Go/no-go
    lines.append("\n### 7. GO/NO-GO FOR DEMO TRADING\n")

    if exp > 0 and ci[0] > -0.1:
        lines.append("VERDICT: CAUTIOUS GO for demo trading")
        lines.append("Rationale:")
        lines.append(f"  - Positive expectancy ({exp:+.3f}R) across {n} trades")
        lines.append(f"  - System is not catastrophically losing")
        lines.append(f"  - Demo testing will provide MFE data for TP optimization")
        lines.append(f"  - Demo testing will validate real-time execution")
        lines.append("Conditions:")
        lines.append(f"  - Use 1% risk (conservative)")
        lines.append(f"  - Run minimum 50 demo trades before any live consideration")
        lines.append(f"  - Track MFE/MAE for every trade")
        lines.append(f"  - Stop and re-evaluate if drawdown exceeds 8R")
    else:
        lines.append("VERDICT: NOT READY for demo trading")
        lines.append("Rationale:")
        lines.append(f"  - Expectancy {exp:+.3f}R is insufficient")
        lines.append(f"  - Bootstrap CI includes zero")
        lines.append("Required before demo:")
        lines.append("  - Identify and fix the losing filter combinations")
        lines.append("  - Add MFE tracking to optimize TP placement")
        lines.append("  - Re-run backtest on new date ranges for validation")

    lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("Loading data...")
    all_results = load_all_results()
    print(f"  Loaded {len(all_results)} session results from {len(CANONICAL_BATCHES)} batches")

    print("Extracting trades...")
    trades = extract_trades(all_results)
    print(f"  Extracted {len(trades)} trades")

    print("Extracting candle decisions...")
    candidates, no_trades = extract_all_candle_decisions(all_results)
    print(f"  {len(candidates)} candidates, {len(no_trades)} no-trade decisions")

    # Save unified trades
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    trades_path = ANALYSIS_DIR / "unified_trades.json"
    # Remove non-serializable fields
    trades_clean = []
    for t in trades:
        tc = {k: v for k, v in t.items() if k != "frameworks_evaluated"}
        trades_clean.append(tc)
    trades_path.write_text(json.dumps(trades_clean, indent=2, default=str))
    print(f"  Saved unified trades to {trades_path}")

    # Build report
    report = []
    report.append("# COMPREHENSIVE BACKTEST ANALYSIS — XAUUSD AI TRADING AGENT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total sessions: {len(all_results)} | Total trades: {len(trades)}")
    report.append("=" * 70)
    report.append("")

    report.append(section_data_integrity(all_results, trades))
    report.append(section_combined_overview(trades))
    report.append(section_breakdown(trades, "framework", "FRAMEWORK BREAKDOWN", "3.3"))
    report.append(section_kill_zone_detail(trades))
    report.append(section_breakdown(trades, "setup_grade", "GRADE BREAKDOWN", "3.5"))
    report.append(section_cross_tab(trades, "setup_grade", "kill_zone", "Grade × Kill Zone", "3.5b"))
    report.append(section_breakdown(trades, "direction", "DIRECTION BREAKDOWN", "3.6"))
    report.append(section_cross_tab(trades, "direction", "kill_zone", "Direction × Kill Zone", "3.6b"))
    report.append(section_breakdown(trades, "day_of_week", "DAY OF WEEK", "3.7"))
    report.append(section_monthly_performance(trades))
    report.append(section_temporal_stability(trades))
    report.append(section_safety_check(all_results, candidates, no_trades))

    # 3.12 MFE/MAE — not available in batch data
    report.append("## 3.11-3.12 MFE/MAE ANALYSIS\n")
    report.append("MFE (Max Favorable Excursion) and MAE (Max Adverse Excursion) data is NOT")
    report.append("tracked in the batch backtest results. Only final outcome (WIN/LOSS at -1R/+XR)")
    report.append("is recorded. To enable TP optimization and near-miss analysis, MFE tracking")
    report.append("must be added to the outcome evaluation logic.")
    report.append("**This is the single most important missing data point for system improvement.**\n")

    report.append(section_planned_rr(trades))
    report.append(section_sl_sizing(trades))
    report.append(section_confidence_score(trades))

    # 3.16 Displacement quality
    report.append(section_breakdown(trades, "displacement_quality", "DISPLACEMENT QUALITY VS OUTCOME", "3.16"))

    # 3.17 Liquidity pool type
    report.append(section_breakdown(trades, "liquidity_pool_type", "LIQUIDITY POOL TYPE VS OUTCOME", "3.17"))

    # 3.17b Sweep quality
    report.append(section_breakdown(trades, "sweep_quality", "SWEEP QUALITY VS OUTCOME", "3.17b"))

    report.append(section_streaks(trades))

    # Cross-filter analysis
    cf_text, best_filter = section_cross_filter(trades)
    report.append(cf_text)

    # Get best filter trades for significance testing
    filter_fns = {
        "ALL trades": lambda t: True,
        "NY only": lambda t: t["kill_zone"] == "ny",
        "London only": lambda t: t["kill_zone"] == "london",
        "A+ only": lambda t: t.get("setup_grade") == "A+",
        "session_sweep only": lambda t: t.get("framework") == "session_sweep",
        "Batch3": lambda t: t.get("batch") == "Batch3",
        "Batch4A": lambda t: t.get("batch") == "Batch4A",
        "Batch4B": lambda t: t.get("batch") == "Batch4B",
    }
    best_filter_trades = None
    if best_filter and best_filter in filter_fns:
        best_filter_trades = [t for t in trades if filter_fns[best_filter](t)]

    report.append(section_statistical_significance(trades, best_filter_trades, best_filter))
    report.append(section_monte_carlo(trades, best_filter_trades, best_filter))
    report.append(section_kelly(trades))

    # 3.23 Optimal TP — can't do without MFE
    report.append("## 3.23 OPTIMAL TP PLACEMENT MODEL\n")
    report.append("Cannot perform this analysis without MFE data. See 3.11-3.12 note above.\n")

    report.append(section_pre_screening(all_results))
    report.append(section_framework_investigation(no_trades))
    report.append(section_recommendations(trades, all_results))

    # Print full report
    full_report = "\n".join(report)
    print(full_report)

    # Save report
    report_path = ANALYSIS_DIR / "full_analysis_report.md"
    report_path.write_text(full_report)
    print(f"\n{'='*70}")
    print(f"Report saved to: {report_path}")
    print(f"Unified trades saved to: {trades_path}")


if __name__ == "__main__":
    main()
