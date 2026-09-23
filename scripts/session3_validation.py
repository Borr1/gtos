#!/usr/bin/env python3
"""Session 3: Validation batch comparison + MFE/MAE analysis."""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, date
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = PROJECT_ROOT / "knowledge_base_backtest"
ANALYSIS_DIR = KB_DIR / "analysis"
BATCH_DIR = KB_DIR / "batch_api"
RESPONSES_DIR = BATCH_DIR / "responses"
SESSIONS_DIR = KB_DIR / "sessions"


def wilson_ci(wins, total, z=1.96):
    if total == 0:
        return (0, 0)
    p = wins / total
    d = 1 + z**2 / total
    c = (p + z**2 / (2 * total)) / d
    s = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / d
    return (max(0, c - s), min(1, c + s))


def bootstrap_ci(data, n_boot=10000, ci=0.95):
    if len(data) < 2:
        return (data[0] if data else 0, data[0] if data else 0)
    np.random.seed(42)
    arr = np.array(data)
    means = [np.mean(np.random.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    alpha = (1 - ci) / 2
    return (np.percentile(means, alpha * 100), np.percentile(means, (1 - alpha) * 100))


def flag(n, thresh=15):
    return " ⚠️ LOW" if n < thresh else ""


# ═══════════════════════════════════════════════════════════════════════
# Find and load the NEW batch
# ═══════════════════════════════════════════════════════════════════════

def find_latest_batch():
    """Find the most recent batch result file."""
    result_files = sorted(BATCH_DIR.glob("msgbatch_*_results.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not result_files:
        raise FileNotFoundError("No batch results found")
    latest = result_files[0]
    batch_id = latest.stem.replace("_results", "")
    return batch_id, latest


def load_new_trades(batch_id: str, results_path: Path):
    """Load trades from the new batch, enriching with response-level detail."""
    results = json.loads(results_path.read_text())
    trades = []

    for result in results:
        date_str = result["date"]
        if not result.get("trade_taken"):
            continue

        # Load response file for detailed reasoning
        resp_path = RESPONSES_DIR / f"{date_str}_responses.json"
        responses = json.loads(resp_path.read_text()) if resp_path.exists() else {}

        for trade_info in result.get("trades", []):
            trade = {
                "date": date_str,
                "trade_id": trade_info.get("trade_id", ""),
                "kill_zone": trade_info.get("kill_zone", "unknown"),
                "framework": trade_info.get("framework", "unknown"),
                "outcome": trade_info.get("outcome", "unknown"),
                "r_multiple": trade_info.get("r_multiple", 0.0),
                "exit_substate": trade_info.get("exit_substate"),
                "mfe_r": trade_info.get("mfe_r"),
                "mae_r": trade_info.get("mae_r"),
                "hold_time_candles": trade_info.get("hold_time_candles"),
            }

            # Parse date info
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                trade["day_of_week"] = dt.strftime("%A")
                trade["month"] = dt.strftime("%Y-%m")
            except:
                trade["day_of_week"] = "Unknown"
                trade["month"] = "Unknown"

            # Find CANDIDATE in response for detailed fields
            for key, resp in responses.items():
                if resp.get("decision") == "CANDIDATE" and resp.get("kill_zone") == trade["kill_zone"]:
                    trade["confidence_score"] = resp.get("confidence_score")
                    trade["confidence_computation"] = resp.get("confidence_computation")
                    trade["setup_grade"] = resp.get("reasoning", {}).get("setup_grade", "unknown")

                    tp = resp.get("trade_parameters", {}) or {}
                    trade["direction"] = tp.get("direction", "unknown")
                    trade["entry_price"] = tp.get("entry_price")
                    trade["stop_loss"] = tp.get("stop_loss")
                    trade["take_profit_1"] = tp.get("take_profit_1")
                    trade["take_profit_2"] = tp.get("take_profit_2")
                    trade["take_profit_3"] = tp.get("take_profit_3")
                    trade["planned_rr"] = tp.get("risk_reward_ratio")
                    if trade.get("entry_price") and trade.get("stop_loss"):
                        trade["sl_dollars"] = abs(trade["entry_price"] - trade["stop_loss"])

                    reasoning = resp.get("reasoning", {})
                    trade["daily_bias"] = reasoning.get("daily_bias", {}).get("direction", "unknown")
                    trade["liquidity_pool_type"] = reasoning.get("liquidity_sweep", {}).get("pool_type", "unknown")
                    trade["sweep_quality"] = reasoning.get("liquidity_sweep", {}).get("sweep_quality", "unknown")
                    trade["displacement_quality"] = reasoning.get("m15_confirmation", {}).get("displacement_quality", "unknown")

                    # Check H1 order block info for causing_event_type
                    fe = resp.get("frameworks_evaluated", {})
                    ob_eval = fe.get("ob_retest", {})
                    trade["ob_eval_reason"] = ob_eval.get("reason", "") if isinstance(ob_eval, dict) else ""

                    break

            # Defaults
            trade.setdefault("direction", "unknown")
            trade.setdefault("setup_grade", "unknown")
            trade.setdefault("confidence_score", None)
            trade.setdefault("sl_dollars", None)
            trade.setdefault("planned_rr", None)

            trades.append(trade)

    return trades, results


def stats_block(group, label=""):
    """Return multiline stats for a group of trades."""
    n = len(group)
    if n == 0:
        return f"{label}: 0 trades\n"
    wins = [t for t in group if t["outcome"] == "WIN"]
    losses = [t for t in group if t["outcome"] == "LOSS"]
    rs = [t["r_multiple"] for t in group]
    tr = sum(rs)
    wr = len(wins) / n
    exp = tr / n

    win_rs = [t["r_multiple"] for t in wins]
    loss_rs = [abs(t["r_multiple"]) for t in losses]

    lines = [f"### {label}" if label else ""]
    lines.append(f"  Trades: {n}  |  {len(wins)}W / {len(losses)}L")
    ci = wilson_ci(len(wins), n)
    lines.append(f"  Win rate: {wr*100:.1f}% (95% CI: [{ci[0]*100:.1f}%, {ci[1]*100:.1f}%])")
    lines.append(f"  Total R: {tr:+.2f}R")

    exp_ci = bootstrap_ci(rs) if n >= 3 else (exp, exp)
    lines.append(f"  Expectancy: {exp:+.3f}R (95% CI: [{exp_ci[0]:+.3f}R, {exp_ci[1]:+.3f}R])")

    if win_rs:
        lines.append(f"  Avg winner: {statistics.mean(win_rs):.3f}R  |  Median: {statistics.median(win_rs):.3f}R")
    if loss_rs:
        lines.append(f"  Avg loser: {statistics.mean(loss_rs):.3f}R  |  Median: {statistics.median(loss_rs):.3f}R")

    if win_rs and loss_rs:
        pf = sum(win_rs) / sum(loss_rs)
        lines.append(f"  Profit factor: {pf:.3f}  |  Payoff: {statistics.mean(win_rs)/statistics.mean(loss_rs):.3f}")

    return "\n".join(lines)


def main():
    report = []
    report.append("=" * 72)
    report.append("SESSION 3: VALIDATION BATCH — COMPARATIVE ANALYSIS")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 72)

    # Load OLD trades
    old_trades = json.loads((ANALYSIS_DIR / "unified_trades.json").read_text())
    report.append(f"\nOLD system: {len(old_trades)} trades loaded")

    # Load NEW batch
    batch_id, results_path = find_latest_batch()
    report.append(f"NEW batch: {batch_id}")
    new_trades, new_results = load_new_trades(batch_id, results_path)
    report.append(f"NEW system: {len(new_trades)} trades extracted")

    # ═══ PART 2: COMPARISON ═══════════════════════════════════════════

    report.append("\n" + "=" * 72)
    report.append("PART 2: NEW SYSTEM OVERVIEW")
    report.append("=" * 72)

    total_sessions = len(new_results)
    trade_sessions = sum(1 for r in new_results if r.get("trade_taken"))
    report.append(f"\nTotal sessions: {total_sessions}")
    report.append(f"Sessions with trades: {trade_sessions}")
    report.append(f"Trade frequency: {len(new_trades)/total_sessions*100:.1f}% trades/session")

    report.append("\n" + stats_block(new_trades, "NEW System Combined"))

    # 2.3 Framework breakdown
    report.append("\n## 2.3 FRAMEWORK BREAKDOWN\n")
    for fw in sorted(set(t["framework"] for t in new_trades)):
        g = [t for t in new_trades if t["framework"] == fw]
        report.append(stats_block(g, fw))

    # Check for ob_retest BOS vs CHoCH distinction
    # The new system's responses should have causing_event_type info if we can read it
    # from the H1 order_blocks in the MSO. Since we can't directly, check the AI reasoning.
    ob_trades = [t for t in new_trades if t["framework"] == "ob_retest"]
    if ob_trades:
        report.append("\n### ob_retest detail (BOS vs CHoCH):")
        for t in sorted(ob_trades, key=lambda x: x["date"]):
            reason = t.get("ob_eval_reason", "")
            # Try to infer from reasoning whether BOS or CHoCH was used
            bos_hint = "BOS" if "BOS" in reason.upper() else ("CHoCH" if "CHoCH" in reason.upper() or "choch" in reason.lower() else "unknown")
            report.append(f"  {t['date']} {t['kill_zone']:>7} {t['direction']:<5} {t['outcome']} {t['r_multiple']:+.2f}R "
                          f"grade={t.get('setup_grade','?')} conf={t.get('confidence_score','?')} "
                          f"break_type={bos_hint}")

    # 2.4 Framework × Kill Zone
    report.append("\n## 2.4 FRAMEWORK × KILL ZONE\n")
    report.append(f"| {'Framework':<15} | {'KZ':<7} | {'N':>4} | {'W':>3} | {'L':>3} | {'WR':>6} | {'Exp':>8} | {'Total R':>8} |")
    report.append(f"|{'-'*15}--|{'-'*7}--|{'-'*4}--|{'-'*3}--|{'-'*3}--|{'-'*6}--|{'-'*8}--|{'-'*8}--|")

    for fw in sorted(set(t["framework"] for t in new_trades)):
        for kz in ["london", "ny"]:
            g = [t for t in new_trades if t["framework"] == fw and t["kill_zone"] == kz]
            n = len(g)
            if n == 0:
                report.append(f"| {fw:<15} | {kz:<7} | {0:>4} |   - |   - |    --% |      --R |      --R |")
            else:
                w = sum(1 for t in g if t["outcome"] == "WIN")
                tr = sum(t["r_multiple"] for t in g)
                report.append(f"| {fw:<15} | {kz:<7} | {n:>4} | {w:>3} | {n-w:>3} | {w/n*100:>5.1f}% | {tr/n:>+7.3f}R | {tr:>+7.2f}R |{flag(n)}")

    ss_london = [t for t in new_trades if t["framework"] == "session_sweep" and t["kill_zone"] == "london"]
    if len(ss_london) == 0:
        report.append("\n✓ session_sweep + London = 0 trades (kill zone gate working)")
    else:
        report.append(f"\n⚠️ session_sweep + London = {len(ss_london)} trades (gate NOT working!)")

    # 2.5 Side-by-side comparison
    report.append("\n## 2.5 SIDE-BY-SIDE COMPARISON\n")
    old_n = len(old_trades)
    new_n = len(new_trades)
    old_wr = sum(1 for t in old_trades if t["outcome"] == "WIN") / old_n if old_n else 0
    new_wr = sum(1 for t in new_trades if t["outcome"] == "WIN") / new_n if new_n else 0
    old_exp = sum(t["r_multiple"] for t in old_trades) / old_n if old_n else 0
    new_exp = sum(t["r_multiple"] for t in new_trades) / new_n if new_n else 0
    old_tr = sum(t["r_multiple"] for t in old_trades)
    new_tr = sum(t["r_multiple"] for t in new_trades)
    old_ob = [t for t in old_trades if t["framework"] == "ob_retest"]
    new_ob = [t for t in new_trades if t["framework"] == "ob_retest"]
    old_ss = [t for t in old_trades if t["framework"] == "session_sweep"]
    new_ss = [t for t in new_trades if t["framework"] == "session_sweep"]
    old_ss_lon = [t for t in old_trades if t["framework"] == "session_sweep" and t["kill_zone"] == "london"]

    report.append(f"| {'Metric':<25} | {'OLD':>10} | {'NEW':>10} | {'Change':>10} |")
    report.append(f"|{'-'*25}--|{'-'*10}--|{'-'*10}--|{'-'*10}--|")
    report.append(f"| {'Total trades':<25} | {old_n:>10} | {new_n:>10} | {new_n - old_n:>+10} |")
    report.append(f"| {'ob_retest trades':<25} | {len(old_ob):>10} | {len(new_ob):>10} | {len(new_ob)-len(old_ob):>+10} |")
    report.append(f"| {'session_sweep trades':<25} | {len(old_ss):>10} | {len(new_ss):>10} | {len(new_ss)-len(old_ss):>+10} |")
    report.append(f"| {'Win rate':<25} | {old_wr*100:>9.1f}% | {new_wr*100:>9.1f}% | {(new_wr-old_wr)*100:>+9.1f}% |")
    report.append(f"| {'Expectancy':<25} | {old_exp:>+9.3f}R | {new_exp:>+9.3f}R | {new_exp-old_exp:>+9.3f}R |")
    report.append(f"| {'Total R':<25} | {old_tr:>+9.2f}R | {new_tr:>+9.2f}R | {new_tr-old_tr:>+9.2f}R |")

    old_ob_wr = sum(1 for t in old_ob if t["outcome"]=="WIN")/len(old_ob) if old_ob else 0
    new_ob_wr = sum(1 for t in new_ob if t["outcome"]=="WIN")/len(new_ob) if new_ob else 0
    old_ob_exp = sum(t["r_multiple"] for t in old_ob)/len(old_ob) if old_ob else 0
    new_ob_exp = sum(t["r_multiple"] for t in new_ob)/len(new_ob) if new_ob else 0
    report.append(f"| {'ob_retest WR':<25} | {old_ob_wr*100:>9.1f}% | {new_ob_wr*100:>9.1f}% | {(new_ob_wr-old_ob_wr)*100:>+9.1f}% |")
    report.append(f"| {'ob_retest exp':<25} | {old_ob_exp:>+9.3f}R | {new_ob_exp:>+9.3f}R | {new_ob_exp-old_ob_exp:>+9.3f}R |")
    report.append(f"| {'SS London trades':<25} | {len(old_ss_lon):>10} | {len(ss_london):>10} | {len(ss_london)-len(old_ss_lon):>+10} |")
    report.append(f"| {'SS London R':<25} | {sum(t['r_multiple'] for t in old_ss_lon):>+9.2f}R | {sum(t['r_multiple'] for t in ss_london):>+9.2f}R | {'KILLED':>10} |")

    # 2.6 Confidence score distribution
    report.append("\n## 2.6 CONFIDENCE SCORE DISTRIBUTION\n")
    confs = [t.get("confidence_score") for t in new_trades if t.get("confidence_score") is not None]
    if confs:
        report.append(f"  Count: {len(confs)}")
        report.append(f"  Distribution: {Counter(confs).most_common(10)}")
        report.append(f"  Min: {min(confs)}  25th: {np.percentile(confs, 25):.0f}  Median: {np.percentile(confs, 50):.0f}  75th: {np.percentile(confs, 75):.0f}  Max: {max(confs)}")
        report.append(f"  Std dev: {statistics.stdev(confs):.1f}" if len(set(confs)) > 1 else "  Std dev: 0.0 (CONSTANT)")
        report.append(f"  Variance adequate (std > 5)? {'YES' if len(set(confs)) > 1 and statistics.stdev(confs) > 5 else 'NO'}")

        if len(set(confs)) > 1:
            rs = [t["r_multiple"] for t in new_trades if t.get("confidence_score") is not None]
            rho, pval = sp_stats.spearmanr(confs, rs)
            report.append(f"  Spearman ρ(confidence, R): {rho:.3f} (p={pval:.4f})")
        else:
            report.append(f"  Confidence still constant — rubric not working")

        # Show a few confidence_computation examples
        comps = [t.get("confidence_computation") for t in new_trades if t.get("confidence_computation")]
        if comps:
            report.append(f"\n  Sample computations:")
            for c in comps[:5]:
                report.append(f"    {c}")
    else:
        report.append("  No confidence data")

    # 2.7 Grade breakdown
    report.append("\n## 2.7 GRADE BREAKDOWN\n")
    for grade in sorted(set(t.get("setup_grade", "?") for t in new_trades)):
        g = [t for t in new_trades if t.get("setup_grade") == grade]
        report.append(stats_block(g, f"Grade {grade}"))

    # 2.8 Kill zone
    report.append("\n## 2.8 KILL ZONE BREAKDOWN\n")
    for kz in ["london", "ny"]:
        g = [t for t in new_trades if t["kill_zone"] == kz]
        report.append(stats_block(g, kz.upper()))

    # 2.9 Day of week
    report.append("\n## 2.9 DAY OF WEEK\n")
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        g = [t for t in new_trades if t["day_of_week"] == day]
        n = len(g)
        if n == 0:
            continue
        w = sum(1 for t in g if t["outcome"] == "WIN")
        tr = sum(t["r_multiple"] for t in g)
        ci = wilson_ci(w, n)
        report.append(f"  {day:<10}: {n:>3} trades, {w}W/{n-w}L, WR {w/n*100:.1f}% [{ci[0]*100:.0f}%-{ci[1]*100:.0f}%], Exp {tr/n:+.3f}R, Total {tr:+.2f}R")

    # 2.10 Monthly
    report.append("\n## 2.10 MONTHLY PERFORMANCE\n")
    monthly = defaultdict(list)
    for t in new_trades:
        monthly[t["month"]].append(t)
    cum = 0
    for m in sorted(monthly.keys()):
        g = monthly[m]
        w = sum(1 for t in g if t["outcome"] == "WIN")
        tr = sum(t["r_multiple"] for t in g)
        cum += tr
        report.append(f"  {m}: {len(g):>2} trades ({w}W/{len(g)-w}L), {tr:+.2f}R, Cumulative: {cum:+.2f}R")

    # 2.11 Temporal stability
    report.append("\n## 2.11 TEMPORAL STABILITY\n")
    sorted_new = sorted(new_trades, key=lambda t: t["date"])
    nt = len(sorted_new)
    third = nt // 3
    for i, label in enumerate(["First third", "Second third", "Final third"]):
        if i < 2:
            g = sorted_new[i*third:(i+1)*third]
        else:
            g = sorted_new[i*third:]
        if not g:
            continue
        n = len(g)
        w = sum(1 for t in g if t["outcome"] == "WIN")
        tr = sum(t["r_multiple"] for t in g)
        report.append(f"  {label} ({n} trades, {g[0]['date']} to {g[-1]['date']}): WR {w/n*100:.1f}%, Exp {tr/n:+.3f}R, Total {tr:+.2f}R")

    # ═══ PART 3: MFE/MAE ANALYSIS ═══════════════════════════════════

    report.append("\n" + "=" * 72)
    report.append("PART 3: MFE/MAE ANALYSIS")
    report.append("=" * 72)

    trades_with_mfe = [t for t in new_trades if t.get("mfe_r") is not None]
    report.append(f"\nTrades with MFE data: {len(trades_with_mfe)}/{len(new_trades)}")

    if trades_with_mfe:
        winners_mfe = [t for t in trades_with_mfe if t["outcome"] == "WIN"]
        losers_mfe = [t for t in trades_with_mfe if t["outcome"] == "LOSS"]

        report.append("\n## 3.1 MFE Distribution\n")
        for label, group in [("ALL", trades_with_mfe), ("Winners", winners_mfe), ("Losers", losers_mfe)]:
            mfes = [t["mfe_r"] for t in group]
            if mfes:
                report.append(f"  {label} ({len(group)} trades): min={min(mfes):.2f}R 25th={np.percentile(mfes,25):.2f}R "
                              f"median={np.percentile(mfes,50):.2f}R 75th={np.percentile(mfes,75):.2f}R max={max(mfes):.2f}R")

        if losers_mfe:
            mfes = [t["mfe_r"] for t in losers_mfe]
            report.append(f"\n  Losers with MFE > 0.5R: {sum(1 for m in mfes if m > 0.5)} / {len(mfes)}")
            report.append(f"  Losers with MFE > 1.0R: {sum(1 for m in mfes if m > 1.0)} / {len(mfes)}")
            report.append(f"  Losers with MFE > 1.5R: {sum(1 for m in mfes if m > 1.5)} / {len(mfes)}")

        # 3.2 By framework
        report.append("\n## 3.2 MFE by Framework\n")
        for fw in sorted(set(t["framework"] for t in trades_with_mfe)):
            for outcome_label, outcome_val in [("winners", "WIN"), ("losers", "LOSS")]:
                g = [t for t in trades_with_mfe if t["framework"] == fw and t["outcome"] == outcome_val]
                if g:
                    mfes = [t["mfe_r"] for t in g]
                    report.append(f"  {fw} {outcome_label} ({len(g)}): median MFE={np.percentile(mfes,50):.2f}R, avg={statistics.mean(mfes):.2f}R")

        # 3.3 OPTIMAL TP1
        report.append("\n## 3.3 OPTIMAL TP1 CALCULATION\n")

        def compute_tp_curve(group, label):
            n = len(group)
            if n == 0:
                return
            mfes = [t["mfe_r"] for t in group]
            report.append(f"\n### {label} ({n} trades)")
            report.append(f"| {'TP1':>5} | {'Hit':>4} | {'Miss':>4} | {'WR':>6} | {'Exp':>8} |")
            report.append(f"|{'-'*5}--|{'-'*4}--|{'-'*4}--|{'-'*6}--|{'-'*8}--|")

            best_exp = -999
            best_tp = 0
            for tp_level_x10 in range(5, 31):
                tp = tp_level_x10 / 10.0
                hits = sum(1 for m in mfes if m >= tp)
                misses = n - hits
                wr = hits / n
                exp = wr * tp - (1 - wr) * 1.0
                if exp > best_exp:
                    best_exp = exp
                    best_tp = tp
                report.append(f"| {tp:>4.1f}R | {hits:>4} | {misses:>4} | {wr*100:>5.1f}% | {exp:>+7.3f}R |")

            report.append(f"\n  ★ OPTIMAL TP1 = {best_tp:.1f}R → expectancy {best_exp:+.3f}R")

        compute_tp_curve(trades_with_mfe, "All trades")
        ob_mfe = [t for t in trades_with_mfe if t["framework"] == "ob_retest"]
        if ob_mfe:
            compute_tp_curve(ob_mfe, "ob_retest only")
        ss_mfe = [t for t in trades_with_mfe if t["framework"] == "session_sweep"]
        if ss_mfe:
            compute_tp_curve(ss_mfe, "session_sweep only")
        ny_mfe = [t for t in trades_with_mfe if t["kill_zone"] == "ny"]
        if ny_mfe:
            compute_tp_curve(ny_mfe, "NY only")

        # 3.4 MAE
        report.append("\n## 3.4 MAE Analysis\n")
        for label, group in [("Winners", winners_mfe), ("Losers", losers_mfe)]:
            maes = [t["mae_r"] for t in group if t.get("mae_r") is not None]
            if maes:
                report.append(f"  {label}: avg MAE={statistics.mean(maes):.2f}R, median={statistics.median(maes):.2f}R, max={max(maes):.2f}R")

        # 3.5 Exit type
        report.append("\n## 3.5 EXIT TYPE ANALYSIS\n")
        exit_types = Counter(t.get("exit_substate", "unknown") for t in new_trades)
        for et, count in exit_types.most_common():
            g = [t for t in new_trades if t.get("exit_substate") == et]
            avg_r = statistics.mean([t["r_multiple"] for t in g]) if g else 0
            report.append(f"  {et:<25}: {count:>3} trades ({count/len(new_trades)*100:.1f}%), avg R={avg_r:+.2f}")

    # ═══ PART 4: STATISTICAL TESTS ═══════════════════════════════════

    report.append("\n" + "=" * 72)
    report.append("PART 4: STATISTICAL TESTS")
    report.append("=" * 72)

    def run_stats(group, label):
        rs = [t["r_multiple"] for t in group]
        n = len(rs)
        if n < 3:
            report.append(f"\n### {label}: Too few trades ({n}) for statistical testing")
            return
        exp = statistics.mean(rs)
        t_stat, p_val = sp_stats.ttest_1samp(rs, 0)
        ci = bootstrap_ci(rs)
        report.append(f"\n### {label} (n={n})")
        report.append(f"  Expectancy: {exp:+.3f}R")
        report.append(f"  t-stat: {t_stat:.3f}, p-value: {p_val:.4f}")
        report.append(f"  Bootstrap 95% CI: [{ci[0]:+.3f}R, {ci[1]:+.3f}R]")
        if p_val < 0.05:
            report.append(f"  → REJECT H0 at p < 0.05 ✓✓")
        elif p_val < 0.10:
            report.append(f"  → REJECT H0 at p < 0.10 ✓")
        else:
            report.append(f"  → FAIL TO REJECT H0")
        if ci[0] > 0:
            report.append(f"  → CI excludes zero ✓")

    run_stats(new_trades, "Full System")
    run_stats([t for t in new_trades if t["framework"] == "ob_retest"], "ob_retest Only")
    run_stats([t for t in new_trades if t["kill_zone"] == "ny"], "NY Only")

    # Best filter
    filters = {
        "ALL": lambda t: True,
        "NY only": lambda t: t["kill_zone"] == "ny",
        "ob_retest": lambda t: t["framework"] == "ob_retest",
        "ob_retest NY": lambda t: t["framework"] == "ob_retest" and t["kill_zone"] == "ny",
        "A+ only": lambda t: t.get("setup_grade") == "A+",
        "NOT Wednesday": lambda t: t["day_of_week"] != "Wednesday",
        "NY + NOT Wed": lambda t: t["kill_zone"] == "ny" and t["day_of_week"] != "Wednesday",
    }

    report.append("\n### Best Filter Search")
    best_exp_15 = -999
    best_label = ""
    for label, fn in filters.items():
        g = [t for t in new_trades if fn(t)]
        n = len(g)
        if n == 0:
            continue
        tr = sum(t["r_multiple"] for t in g)
        exp = tr / n
        if n >= 15 and exp > best_exp_15:
            best_exp_15 = exp
            best_label = label
        report.append(f"  {label:<20}: {n:>3} trades, Exp {exp:+.3f}R{flag(n)}")

    if best_label:
        report.append(f"\n  ★ Best filter (≥15): {best_label} with {best_exp_15:+.3f}R")
        best_group = [t for t in new_trades if filters[best_label](t)]
        run_stats(best_group, f"Best Filter: {best_label}")

    # Monte Carlo
    report.append("\n## 4.4 MONTE CARLO SIMULATION\n")
    np.random.seed(42)

    def run_mc(group, label, n_trades=100, n_sims=10000):
        rs = np.array([t["r_multiple"] for t in group])
        if len(rs) < 3:
            report.append(f"  {label}: Too few trades for MC")
            return
        finals = []
        max_dds = []
        for _ in range(n_sims):
            samples = np.random.choice(rs, size=n_trades, replace=True)
            cum = np.cumsum(samples)
            finals.append(cum[-1])
            peak = np.maximum.accumulate(cum)
            max_dds.append(np.max(peak - cum))
        finals = np.array(finals)
        max_dds = np.array(max_dds)

        p50_finals = np.cumsum(np.random.choice(rs, size=(n_sims, 50), replace=True), axis=1)[:, -1]

        report.append(f"  {label} ({len(rs)} trades → {n_trades} simulated):")
        report.append(f"    Median final R: {np.median(finals):+.2f}R")
        report.append(f"    5th/95th pct: [{np.percentile(finals,5):+.2f}R, {np.percentile(finals,95):+.2f}R]")
        report.append(f"    P(profit after 50): {np.mean(p50_finals > 0)*100:.1f}%")
        report.append(f"    P(profit after 100): {np.mean(finals > 0)*100:.1f}%")
        report.append(f"    Max DD — median: {np.median(max_dds):.2f}R, 95th: {np.percentile(max_dds,95):.2f}R")
        report.append(f"    P(DD > 10R in 50 trades): {np.mean(np.max(np.maximum.accumulate(np.cumsum(np.random.choice(rs, size=(n_sims,50), replace=True), axis=1), axis=1) - np.cumsum(np.random.choice(rs, size=(n_sims,50), replace=True), axis=1), axis=1) > 10)*100:.1f}%")

    run_mc(new_trades, "All trades")
    run_mc([t for t in new_trades if t["framework"] == "ob_retest"], "ob_retest")
    if best_label:
        run_mc([t for t in new_trades if filters[best_label](t)], f"Best filter: {best_label}")

    # ═══ PART 5: VERDICT ═════════════════════════════════════════════

    report.append("\n" + "=" * 72)
    report.append("PART 5: VERDICT")
    report.append("=" * 72)

    report.append("\n## 5.1 DID THE RESTRUCTURE WORK?\n")
    report.append(f"  ob_retest frequency: {len(old_ob)} → {len(new_ob)} trades ({'✓ INCREASED' if len(new_ob) > len(old_ob) else '✗ NOT INCREASED'})")
    report.append(f"  SS London eliminated: {'✓ YES' if len(ss_london) == 0 else '✗ NO'} (was 55 trades, now {len(ss_london)})")

    confs_unique = len(set(confs)) if confs else 0
    report.append(f"  Confidence variance: {'✓ VARIED' if confs_unique > 3 else '✗ STILL CONSTANT'} ({confs_unique} unique values)")
    report.append(f"  Expectancy: {old_exp:+.3f}R → {new_exp:+.3f}R ({'✓ IMPROVED' if new_exp > old_exp else '✗ WORSENED'})")

    report.append("\n## 5.2 IS THERE A CONFIRMED EDGE?\n")
    rs_all = [t["r_multiple"] for t in new_trades]
    if len(rs_all) >= 3:
        _, p_all = sp_stats.ttest_1samp(rs_all, 0)
        ci_all = bootstrap_ci(rs_all)
        report.append(f"  Full system: p={p_all:.4f}, CI=[{ci_all[0]:+.3f}, {ci_all[1]:+.3f}]")
        if ci_all[0] > 0:
            report.append(f"  → YES: Edge confirmed (CI excludes zero)")
        elif p_all < 0.10:
            report.append(f"  → MARGINAL: Suggestive but CI includes zero")
        else:
            report.append(f"  → NO: Cannot confirm edge statistically")

    report.append("\n## 5.5 NEXT STEPS\n")
    report.append("  1. Based on MFE data: adjust TP1 to optimal level identified in 3.3")
    report.append("  2. Re-run batch with optimized TP to validate improvement")
    report.append("  3. If edge confirmed: begin demo trading with conservative sizing")

    # ═══ SAVE OUTPUTS ════════════════════════════════════════════════

    full_report = "\n".join(report)
    print(full_report)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    (ANALYSIS_DIR / "session3_validation_report.md").write_text(full_report)
    print(f"\nSaved: {ANALYSIS_DIR / 'session3_validation_report.md'}")

    # Save new unified trades
    trades_clean = [{k: v for k, v in t.items()} for t in new_trades]
    (ANALYSIS_DIR / "unified_trades_v2.json").write_text(json.dumps(trades_clean, indent=2, default=str))
    print(f"Saved: {ANALYSIS_DIR / 'unified_trades_v2.json'}")

    # Save TP optimization data
    if trades_with_mfe:
        tp_data = {
            "trades_analyzed": len(trades_with_mfe),
            "mfe_distribution": {
                "all": {"min": min(t["mfe_r"] for t in trades_with_mfe),
                        "median": float(np.percentile([t["mfe_r"] for t in trades_with_mfe], 50)),
                        "max": max(t["mfe_r"] for t in trades_with_mfe)},
            },
        }
        (ANALYSIS_DIR / "tp_optimization.json").write_text(json.dumps(tp_data, indent=2))
        print(f"Saved: {ANALYSIS_DIR / 'tp_optimization.json'}")


if __name__ == "__main__":
    main()
