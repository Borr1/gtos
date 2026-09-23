#!/usr/bin/env python3
"""
Phase 2 — Partial Close Investigation
Simulates three exit strategies on gold (candle-by-candle r_path) and GBPUSD (MFE-based).
Includes Monte Carlo risk assessment.
"""

import json
import numpy as np
import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 2A: Gold Phase 1 Simulation (candle-by-candle r_path walk)
# ============================================================

TP1_R = 1.5
SL_R = -1.0
TP2_R = 3.0  # Extended target for runner


def simulate_strategy_a(r_path):
    """100% at TP1 (current system)."""
    for candle in r_path:
        # Check SL hit first (using low)
        if candle["r_at_low"] <= SL_R:
            return {"r": -1.0, "exit": "SL", "candle_idx": candle["candle_index"]}
        # Check TP1 hit (using high)
        if candle["r_at_high"] >= TP1_R:
            return {"r": TP1_R, "exit": "TP1", "candle_idx": candle["candle_index"]}
    # Timeout: use final candle close
    final_r = r_path[-1]["r_at_close"]
    return {"r": final_r, "exit": "TIMEOUT", "candle_idx": r_path[-1]["candle_index"]}


def simulate_strategy_b(r_path):
    """70/30 partial: close 70% at TP1, move SL to BE, hold 30% runner."""
    tp1_hit = False
    banked = 0.0
    tp1_candle = None

    for candle in r_path:
        if not tp1_hit:
            # Phase 1: looking for TP1 or SL
            if candle["r_at_low"] <= SL_R:
                return {"r": -1.0, "exit": "SL", "candle_idx": candle["candle_index"],
                        "tp1_hit": False, "runner_exit": None}
            if candle["r_at_high"] >= TP1_R:
                tp1_hit = True
                banked = TP1_R * 0.7  # +1.05
                tp1_candle = candle["candle_index"]
                # Check if same candle also hits runner targets
                # After TP1 hit, SL is at entry (R=0 for remaining)
                if candle["r_at_high"] >= TP2_R:
                    total = banked + TP2_R * 0.3
                    return {"r": total, "exit": "TP1+TP2", "candle_idx": candle["candle_index"],
                            "tp1_hit": True, "runner_exit": "TP2"}
                # Check if low returns to entry on same candle (after high hit TP1)
                # Only if the low comes after the high — we can't know intra-candle order,
                # so we assume high is hit first, then check low for BE stop
                if candle["r_at_low"] <= 0:
                    total = banked + 0.0  # runner stopped at BE
                    return {"r": total, "exit": "TP1+BE", "candle_idx": candle["candle_index"],
                            "tp1_hit": True, "runner_exit": "BE"}
        else:
            # Phase 2: runner trailing with SL at entry (R=0)
            if candle["r_at_low"] <= 0:
                total = banked + 0.0
                return {"r": total, "exit": "TP1+BE", "candle_idx": candle["candle_index"],
                        "tp1_hit": True, "runner_exit": "BE"}
            if candle["r_at_high"] >= TP2_R:
                total = banked + TP2_R * 0.3
                return {"r": total, "exit": "TP1+TP2", "candle_idx": candle["candle_index"],
                        "tp1_hit": True, "runner_exit": "TP2"}

    # Timeout
    final_r = r_path[-1]["r_at_close"]
    if tp1_hit:
        runner_r = max(final_r, 0) * 0.3  # Can't go below 0 since SL at BE
        total = banked + runner_r
        return {"r": total, "exit": "TP1+TIMEOUT", "candle_idx": r_path[-1]["candle_index"],
                "tp1_hit": True, "runner_exit": "TIMEOUT"}
    else:
        return {"r": final_r, "exit": "TIMEOUT", "candle_idx": r_path[-1]["candle_index"],
                "tp1_hit": False, "runner_exit": None}


def simulate_strategy_c(r_path):
    """50/50 partial: close 50% at TP1, move SL to BE, hold 50% runner."""
    tp1_hit = False
    banked = 0.0
    tp1_candle = None

    for candle in r_path:
        if not tp1_hit:
            if candle["r_at_low"] <= SL_R:
                return {"r": -1.0, "exit": "SL", "candle_idx": candle["candle_index"],
                        "tp1_hit": False, "runner_exit": None}
            if candle["r_at_high"] >= TP1_R:
                tp1_hit = True
                banked = TP1_R * 0.5  # +0.75
                tp1_candle = candle["candle_index"]
                if candle["r_at_high"] >= TP2_R:
                    total = banked + TP2_R * 0.5
                    return {"r": total, "exit": "TP1+TP2", "candle_idx": candle["candle_index"],
                            "tp1_hit": True, "runner_exit": "TP2"}
                if candle["r_at_low"] <= 0:
                    total = banked + 0.0
                    return {"r": total, "exit": "TP1+BE", "candle_idx": candle["candle_index"],
                            "tp1_hit": True, "runner_exit": "BE"}
        else:
            if candle["r_at_low"] <= 0:
                total = banked + 0.0
                return {"r": total, "exit": "TP1+BE", "candle_idx": candle["candle_index"],
                        "tp1_hit": True, "runner_exit": "BE"}
            if candle["r_at_high"] >= TP2_R:
                total = banked + TP2_R * 0.5
                return {"r": total, "exit": "TP1+TP2", "candle_idx": candle["candle_index"],
                        "tp1_hit": True, "runner_exit": "TP2"}

    final_r = r_path[-1]["r_at_close"]
    if tp1_hit:
        runner_r = max(final_r, 0) * 0.5
        total = banked + runner_r
        return {"r": total, "exit": "TP1+TIMEOUT", "candle_idx": r_path[-1]["candle_index"],
                "tp1_hit": True, "runner_exit": "TIMEOUT"}
    else:
        return {"r": final_r, "exit": "TIMEOUT", "candle_idx": r_path[-1]["candle_index"],
                "tp1_hit": False, "runner_exit": None}


def compute_stats(r_values):
    """Compute aggregate statistics for a list of R-multiples."""
    arr = np.array(r_values)
    wins = np.sum(arr > 0)
    losses = np.sum(arr < 0)
    be = np.sum(arr == 0)
    return {
        "n": len(arr),
        "avg_r": round(float(np.mean(arr)), 4),
        "total_r": round(float(np.sum(arr)), 4),
        "median_r": round(float(np.median(arr)), 4),
        "std_r": round(float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0, 4),
        "win_rate": round(float(wins / len(arr) * 100), 1) if len(arr) > 0 else 0,
        "wins": int(wins),
        "losses": int(losses),
        "breakeven": int(be),
        "max_r": round(float(np.max(arr)), 4),
        "min_r": round(float(np.min(arr)), 4),
        "profit_factor": round(float(np.sum(arr[arr > 0]) / abs(np.sum(arr[arr < 0]))) if np.sum(arr[arr < 0]) != 0 else float('inf'), 4),
    }


def run_gold_simulation():
    """Run all three strategies on gold r_path data."""
    with open(os.path.join(BASE_DIR, "phase1_all_trades_merged.json")) as f:
        trades = json.load(f)

    trades_with_rpath = [t for t in trades if t.get("r_path") and len(t["r_path"]) > 0]
    print(f"=== GOLD PARTIAL CLOSE SIMULATION ===")
    print(f"Total trades: {len(trades)}, with r_path: {len(trades_with_rpath)}")
    print()

    results = {"A": [], "B": [], "C": []}
    per_trade = []

    for t in trades_with_rpath:
        rp = t["r_path"]
        res_a = simulate_strategy_a(rp)
        res_b = simulate_strategy_b(rp)
        res_c = simulate_strategy_c(rp)

        results["A"].append(res_a["r"])
        results["B"].append(res_b["r"])
        results["C"].append(res_c["r"])

        per_trade.append({
            "date": t["date"],
            "kill_zone": t.get("kill_zone", ""),
            "direction": t.get("direction", ""),
            "original_r": t.get("r_multiple", None),
            "mfe_r": t.get("mfe_r", None),
            "strategy_a": {"r": round(res_a["r"], 4), "exit": res_a["exit"]},
            "strategy_b": {"r": round(res_b["r"], 4), "exit": res_b["exit"],
                           "tp1_hit": res_b.get("tp1_hit", False),
                           "runner_exit": res_b.get("runner_exit")},
            "strategy_c": {"r": round(res_c["r"], 4), "exit": res_c["exit"],
                           "tp1_hit": res_c.get("tp1_hit", False),
                           "runner_exit": res_c.get("runner_exit")},
        })

    # Print per-trade results
    print(f"{'Date':<12} {'KZ':<8} {'Dir':<6} {'Orig_R':>7} {'MFE':>6} | {'A_R':>7} {'A_Exit':<10} | {'B_R':>7} {'B_Exit':<15} | {'C_R':>7} {'C_Exit':<15}")
    print("-" * 130)
    for pt in per_trade:
        print(f"{pt['date']:<12} {pt['kill_zone']:<8} {pt['direction']:<6} "
              f"{pt['original_r']:>7.2f} {pt['mfe_r']:>6.3f} | "
              f"{pt['strategy_a']['r']:>7.3f} {pt['strategy_a']['exit']:<10} | "
              f"{pt['strategy_b']['r']:>7.3f} {pt['strategy_b']['exit']:<15} | "
              f"{pt['strategy_c']['r']:>7.3f} {pt['strategy_c']['exit']:<15}")

    print()
    # Aggregate stats
    stats = {}
    for strat_name in ["A", "B", "C"]:
        s = compute_stats(results[strat_name])
        stats[strat_name] = s
        label = {"A": "100% at TP1", "B": "70/30 Partial", "C": "50/50 Partial"}[strat_name]
        print(f"Strategy {strat_name} ({label}):")
        print(f"  Avg R: {s['avg_r']:+.4f}  |  Total R: {s['total_r']:+.4f}  |  Win Rate: {s['win_rate']}%")
        print(f"  Std Dev: {s['std_r']:.4f}  |  Profit Factor: {s['profit_factor']:.2f}")
        print(f"  Wins: {s['wins']}  Losses: {s['losses']}  BE: {s['breakeven']}")
        print()

    # Exit distribution
    for strat_name, label in [("A", "Strategy A"), ("B", "Strategy B"), ("C", "Strategy C")]:
        if strat_name == "A":
            exits = [pt[f"strategy_a"]["exit"] for pt in per_trade]
        elif strat_name == "B":
            exits = [pt[f"strategy_b"]["exit"] for pt in per_trade]
        else:
            exits = [pt[f"strategy_c"]["exit"] for pt in per_trade]
        print(f"  {label} exits: {dict(Counter(exits))}")

    return stats, per_trade, results


# ============================================================
# 2B: GBPUSD Comparison (MFE-based simulation)
# ============================================================

def run_gbpusd_simulation():
    """
    GBPUSD has no r_path data, so we simulate using MFE and corrected_r.
    Logic: if mfe_r >= 1.5, TP1 was reachable. For runners, we use batch_r
    as proxy for where price ended up after TP1.
    """
    filepath = os.path.join(BASE_DIR, "gbpusd_batch_deep_analysis_data_20260403.json")
    with open(filepath) as f:
        data = json.load(f)

    trades = data["corrected_trades"]
    print(f"\n=== GBPUSD PARTIAL CLOSE SIMULATION (MFE-based) ===")
    print(f"Total trades: {len(trades)}")
    print()

    results = {"A": [], "B": [], "C": []}

    for t in trades:
        mfe = t.get("mfe_r", 0)
        corrected_r = t.get("corrected_r", 0)
        batch_r = t.get("batch_r", 0)
        batch_exit = t.get("batch_exit", "")
        corrected_exit = t.get("corrected_exit", "")

        # Strategy A: 100% at TP1
        # Already computed as corrected_r in the dataset
        r_a = corrected_r

        # Strategy B: 70/30 partial
        if mfe >= TP1_R:
            # TP1 was hit
            banked = TP1_R * 0.7  # 1.05

            # Runner behavior: use batch_r as proxy for full-path outcome
            # batch_r already incorporates partial close in the original scorer
            # We need to estimate runner outcome from available data
            if batch_exit == "CLOSED_BE":
                # Runner came back to entry
                runner_r = 0.0
            elif batch_exit == "CLOSED_TP1_THEN_TIMEOUT":
                # Runner was still open at timeout; batch_r gives the blended result
                # batch_r = 0.5 * 1.5 + 0.5 * timeout_r (original 50/50)
                # Solve for timeout_r: timeout_r = (batch_r - 0.75) / 0.5
                if t.get("batch_r") is not None:
                    implied_runner_r = (batch_r - 0.75) / 0.5
                    runner_r = max(implied_runner_r, 0)  # SL at BE
                else:
                    runner_r = 0
            elif mfe >= TP2_R:
                # MFE reached 3R, assume runner hit TP2
                runner_r = TP2_R
            else:
                # TP1 hit but unclear runner fate — estimate conservatively
                # Use MFE as upper bound for runner, assume it retraced ~50% of extension
                extension_beyond_tp1 = mfe - TP1_R
                runner_r = max(TP1_R + extension_beyond_tp1 * 0.5, 0)

            r_b = banked + runner_r * 0.3
        else:
            # TP1 not reached — same as corrected_r (loss or timeout)
            if corrected_exit == "CLOSED_SL":
                r_b = -1.0
            else:
                r_b = corrected_r

        # Strategy C: 50/50 partial (same logic, different multipliers)
        if mfe >= TP1_R:
            banked_c = TP1_R * 0.5  # 0.75

            if batch_exit == "CLOSED_BE":
                runner_r_c = 0.0
            elif batch_exit == "CLOSED_TP1_THEN_TIMEOUT":
                if t.get("batch_r") is not None:
                    implied_runner_r = (batch_r - 0.75) / 0.5
                    runner_r_c = max(implied_runner_r, 0)
                else:
                    runner_r_c = 0
            elif mfe >= TP2_R:
                runner_r_c = TP2_R
            else:
                extension_beyond_tp1 = mfe - TP1_R
                runner_r_c = max(TP1_R + extension_beyond_tp1 * 0.5, 0)

            r_c = banked_c + runner_r_c * 0.5
        else:
            if corrected_exit == "CLOSED_SL":
                r_c = -1.0
            else:
                r_c = corrected_r

        results["A"].append(r_a)
        results["B"].append(r_b)
        results["C"].append(r_c)

    stats = {}
    for strat_name in ["A", "B", "C"]:
        s = compute_stats(results[strat_name])
        stats[strat_name] = s
        label = {"A": "100% at TP1", "B": "70/30 Partial", "C": "50/50 Partial"}[strat_name]
        print(f"Strategy {strat_name} ({label}):")
        print(f"  Avg R: {s['avg_r']:+.4f}  |  Total R: {s['total_r']:+.4f}  |  Win Rate: {s['win_rate']}%")
        print(f"  Std Dev: {s['std_r']:.4f}  |  Profit Factor: {s['profit_factor']:.2f}")
        print(f"  Wins: {s['wins']}  Losses: {s['losses']}  BE: {s['breakeven']}")
        print()

    return stats, results


# ============================================================
# 2C: Monte Carlo Risk Assessment
# ============================================================

def monte_carlo_simulation(r_values, n_simulations=10000, n_trades=50, seed=42):
    """
    Bootstrap n_simulations equity curves of n_trades each.
    Returns P5/P25/P50/P75/P95 final equity, max drawdown stats.
    """
    rng = np.random.RandomState(seed)
    r_arr = np.array(r_values)

    final_equities = []
    max_drawdowns = []

    for _ in range(n_simulations):
        sampled = rng.choice(r_arr, size=n_trades, replace=True)
        equity_curve = np.cumsum(sampled)
        final_equities.append(equity_curve[-1])

        # Max drawdown in R terms
        running_max = np.maximum.accumulate(equity_curve)
        drawdowns = equity_curve - running_max
        max_dd = float(np.min(drawdowns))
        max_drawdowns.append(max_dd)

    final_equities = np.array(final_equities)
    max_drawdowns = np.array(max_drawdowns)

    return {
        "final_equity_p5": round(float(np.percentile(final_equities, 5)), 4),
        "final_equity_p25": round(float(np.percentile(final_equities, 25)), 4),
        "final_equity_p50": round(float(np.percentile(final_equities, 50)), 4),
        "final_equity_p75": round(float(np.percentile(final_equities, 75)), 4),
        "final_equity_p95": round(float(np.percentile(final_equities, 95)), 4),
        "final_equity_mean": round(float(np.mean(final_equities)), 4),
        "prob_profitable": round(float(np.mean(final_equities > 0) * 100), 1),
        "prob_above_10r": round(float(np.mean(final_equities > 10) * 100), 1),
        "max_dd_p5": round(float(np.percentile(max_drawdowns, 5)), 4),
        "max_dd_p25": round(float(np.percentile(max_drawdowns, 25)), 4),
        "max_dd_median": round(float(np.percentile(max_drawdowns, 50)), 4),
        "max_dd_p75": round(float(np.percentile(max_drawdowns, 75)), 4),
        "max_dd_p95": round(float(np.percentile(max_drawdowns, 95)), 4),
        "max_dd_mean": round(float(np.mean(max_drawdowns)), 4),
        "max_dd_worst": round(float(np.min(max_drawdowns)), 4),
    }


def run_monte_carlo(gold_results, gbpusd_results):
    """Run Monte Carlo for all strategies on both instruments."""
    print(f"\n=== MONTE CARLO RISK ASSESSMENT ===")
    print(f"10,000 simulations x 50 trades each")
    print()

    mc_results = {}

    for instrument, results in [("gold", gold_results), ("gbpusd", gbpusd_results)]:
        mc_results[instrument] = {}
        print(f"--- {instrument.upper()} ---")
        for strat in ["A", "B", "C"]:
            label = {"A": "100% at TP1", "B": "70/30 Partial", "C": "50/50 Partial"}[strat]
            mc = monte_carlo_simulation(results[strat])
            mc_results[instrument][strat] = mc
            print(f"\n  Strategy {strat} ({label}):")
            print(f"    P5 Equity (50 trades):  {mc['final_equity_p5']:+.2f}R")
            print(f"    P50 Equity (50 trades): {mc['final_equity_p50']:+.2f}R")
            print(f"    P95 Equity (50 trades): {mc['final_equity_p95']:+.2f}R")
            print(f"    Prob Profitable:        {mc['prob_profitable']}%")
            print(f"    Prob >10R:              {mc['prob_above_10r']}%")
            print(f"    Max DD Median:          {mc['max_dd_median']:.2f}R")
            print(f"    Max DD P5 (worst 5%):   {mc['max_dd_p5']:.2f}R")
            print(f"    Max DD Worst Case:      {mc['max_dd_worst']:.2f}R")
        print()

    return mc_results


# ============================================================
# Main
# ============================================================

def main():
    # 2A: Gold simulation
    gold_stats, gold_per_trade, gold_results = run_gold_simulation()

    # 2B: GBPUSD comparison
    gbpusd_stats, gbpusd_results = run_gbpusd_simulation()

    # 2C: Monte Carlo
    mc_results = run_monte_carlo(gold_results, gbpusd_results)

    # Cross-instrument comparison
    print("\n=== CROSS-INSTRUMENT STRATEGY COMPARISON ===")
    print(f"{'Strategy':<20} {'Gold Avg R':>12} {'Gold WR':>10} {'GBP Avg R':>12} {'GBP WR':>10}")
    print("-" * 66)
    for strat in ["A", "B", "C"]:
        label = {"A": "A (100% TP1)", "B": "B (70/30)", "C": "C (50/50)"}[strat]
        print(f"{label:<20} {gold_stats[strat]['avg_r']:>+12.4f} {gold_stats[strat]['win_rate']:>9.1f}% "
              f"{gbpusd_stats[strat]['avg_r']:>+12.4f} {gbpusd_stats[strat]['win_rate']:>9.1f}%")

    # Key insight
    print("\n=== KEY FINDINGS ===")
    best_gold = max(gold_stats.items(), key=lambda x: x[1]["avg_r"])
    best_gbp = max(gbpusd_stats.items(), key=lambda x: x[1]["avg_r"])
    print(f"Gold: Best strategy = {best_gold[0]} (Avg R = {best_gold[1]['avg_r']:+.4f})")
    print(f"GBPUSD: Best strategy = {best_gbp[0]} (Avg R = {best_gbp[1]['avg_r']:+.4f})")

    # Downside protection comparison
    print("\nDownside Protection (Monte Carlo P5 equity over 50 trades):")
    for strat in ["A", "B", "C"]:
        label = {"A": "A (100% TP1)", "B": "B (70/30)", "C": "C (50/50)"}[strat]
        g_p5 = mc_results["gold"][strat]["final_equity_p5"]
        gbp_p5 = mc_results["gbpusd"][strat]["final_equity_p5"]
        print(f"  {label}: Gold P5={g_p5:+.2f}R  |  GBPUSD P5={gbp_p5:+.2f}R")

    # Build output JSON
    output = {
        "gold_by_strategy": {
            "strategy_a_100pct_tp1": gold_stats["A"],
            "strategy_b_70_30_partial": gold_stats["B"],
            "strategy_c_50_50_partial": gold_stats["C"],
            "per_trade_results": gold_per_trade,
        },
        "gbpusd_comparison": {
            "note": "Simulated from MFE data (no candle-by-candle r_path available)",
            "n_trades": len(gbpusd_results["A"]),
            "strategy_a_100pct_tp1": gbpusd_stats["A"],
            "strategy_b_70_30_partial": gbpusd_stats["B"],
            "strategy_c_50_50_partial": gbpusd_stats["C"],
        },
        "monte_carlo_comparison": {
            "parameters": {
                "n_simulations": 10000,
                "n_trades_per_sim": 50,
                "seed": 42,
            },
            "gold": {
                "strategy_a": mc_results["gold"]["A"],
                "strategy_b": mc_results["gold"]["B"],
                "strategy_c": mc_results["gold"]["C"],
            },
            "gbpusd": {
                "strategy_a": mc_results["gbpusd"]["A"],
                "strategy_b": mc_results["gbpusd"]["B"],
                "strategy_c": mc_results["gbpusd"]["C"],
            },
        },
    }

    # Write results JSON
    output_path = os.path.join(BASE_DIR, "partial_close_results_20260403.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {output_path}")


if __name__ == "__main__":
    main()
