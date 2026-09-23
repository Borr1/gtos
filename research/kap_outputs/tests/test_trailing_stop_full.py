#!/usr/bin/env python3
"""
Comprehensive Trailing Stop Test
Test Trail 0.5R after 1.5R MFE only
Split by 2025 vs 2026 AND by symbol
Analysis of all trades in knowledge_base_backtest/sessions
"""

import json
import os
import pandas as pd
from datetime import datetime
from collections import defaultdict
from pathlib import Path

def extract_symbol_from_trade_id(trade_id):
    """Extract symbol from trade_id format like bt_2024-01-25_london_001"""
    # For now, return "XAUUSD" as default since most trades are gold
    # This might need refinement based on actual data patterns
    if "xau" in trade_id.lower() or "gold" in trade_id.lower():
        return "XAUUSD"
    elif "us30" in trade_id.lower() or "dow" in trade_id.lower():
        return "US30_cash"
    elif "usdjpy" in trade_id.lower():
        return "USDJPY"
    elif "gbpjpy" in trade_id.lower():
        return "GBPJPY"
    elif "gbpusd" in trade_id.lower():
        return "GBPUSD"
    elif "nzdusd" in trade_id.lower():
        return "NZDUSD"
    else:
        return "XAUUSD"  # Default assumption

def apply_trailing_stop(mfe_r, original_r, mae_r=None):
    """
    Apply trailing stop logic: 0.5R trail after 1.5R MFE

    Args:
        mfe_r: Maximum Favorable Excursion in R
        original_r: Original trade outcome in R
        mae_r: Maximum Adverse Excursion in R (optional)

    Returns:
        dict with trailing stop results
    """
    if mfe_r < 1.5:
        # No trailing stop applied - trade didn't reach 1.5R MFE
        return {
            'trail_applied': False,
            'trail_trigger_r': None,
            'trail_exit_r': original_r,
            'improvement_r': 0,
            'trail_reason': 'MFE_BELOW_THRESHOLD'
        }

    # Trail activated at 1.5R MFE
    trail_trigger_r = 1.5

    # Trail exit is 0.5R below peak MFE, but at minimum the trail trigger
    trail_exit_r = max(mfe_r - 0.5, trail_trigger_r)

    improvement_r = trail_exit_r - original_r

    return {
        'trail_applied': True,
        'trail_trigger_r': trail_trigger_r,
        'trail_exit_r': trail_exit_r,
        'improvement_r': improvement_r,
        'trail_reason': 'TRAIL_EXECUTED'
    }

def load_all_trades():
    """Load all trades from session files"""
    sessions_dir = Path("knowledge_base_backtest/sessions")
    all_trades = []

    if not sessions_dir.exists():
        print(f"ERROR: Directory {sessions_dir} not found!")
        return []

    session_files = list(sessions_dir.glob("*.json"))
    print(f"Loading trades from {len(session_files)} session files...")

    for session_file in session_files:
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)

            session_date = session_data.get('date', '')
            year = int(session_date.split('-')[0]) if session_date else 0

            if session_data.get('trade_summary', {}).get('trade_taken', False):
                trades = session_data['trade_summary'].get('trades', [])

                for trade in trades:
                    trade_record = {
                        'session_date': session_date,
                        'year': year,
                        'trade_id': trade.get('trade_id', ''),
                        'symbol': extract_symbol_from_trade_id(trade.get('trade_id', '')),
                        'outcome': trade.get('outcome', ''),
                        'original_r': trade.get('r_multiple', 0),
                        'mfe_r': trade.get('mfe_r', 0),
                        'mae_r': trade.get('mae_r', 0),
                        'framework': trade.get('framework', ''),
                        'exit_substate': trade.get('exit_substate', ''),
                        'hold_time_candles': trade.get('hold_time_candles', 0),
                        'kill_zone': trade.get('kill_zone', '')
                    }
                    all_trades.append(trade_record)

        except Exception as e:
            print(f"Error loading {session_file}: {e}")

    print(f"Loaded {len(all_trades)} total trades")
    return all_trades

def analyze_trailing_stop(trades):
    """Analyze trailing stop performance"""

    results = []

    for trade in trades:
        trail_result = apply_trailing_stop(
            trade['mfe_r'],
            trade['original_r'],
            trade['mae_r']
        )

        analysis = {
            **trade,
            **trail_result
        }

        results.append(analysis)

    return results

def generate_summary_stats(results):
    """Generate comprehensive summary statistics"""

    df = pd.DataFrame(results)

    # Filter for trades where trail was applied
    trailed_trades = df[df['trail_applied'] == True]

    print("\n" + "="*80)
    print("COMPREHENSIVE TRAILING STOP ANALYSIS")
    print("="*80)

    print(f"\nOVERALL SUMMARY:")
    print(f"Total trades analyzed: {len(df)}")
    print(f"Trades with MFE >= 1.5R (trail eligible): {len(trailed_trades)}")
    print(f"Trail eligibility rate: {len(trailed_trades)/len(df)*100:.1f}%")

    if len(trailed_trades) > 0:
        avg_improvement = trailed_trades['improvement_r'].mean()
        total_improvement = trailed_trades['improvement_r'].sum()

        print(f"\nTRAILING STOP IMPACT:")
        print(f"Average R improvement per trailed trade: {avg_improvement:.3f}R")
        print(f"Total R improvement across all trailed trades: {total_improvement:.3f}R")

        # Win rate analysis
        original_wins = (df['original_r'] > 0).sum()
        trailed_wins = (df['trail_exit_r'] > 0).sum()

        print(f"\nWIN RATE COMPARISON:")
        print(f"Original win rate: {original_wins/len(df)*100:.1f}% ({original_wins}/{len(df)})")
        print(f"With trailing stops: {trailed_wins/len(df)*100:.1f}% ({trailed_wins}/{len(df)})")

        # R-multiple analysis
        original_avg_r = df['original_r'].mean()
        trailed_avg_r = df['trail_exit_r'].mean()

        print(f"\nR-MULTIPLE ANALYSIS:")
        print(f"Original average R: {original_avg_r:.3f}")
        print(f"With trailing stops: {trailed_avg_r:.3f}")
        print(f"Overall improvement: {trailed_avg_r - original_avg_r:.3f}R")

    # Year breakdown
    print(f"\n" + "-"*60)
    print("YEAR BREAKDOWN:")
    print("-"*60)

    for year in sorted(df['year'].unique()):
        if year == 0:
            continue

        year_df = df[df['year'] == year]
        year_trailed = year_df[year_df['trail_applied'] == True]

        print(f"\n{year}:")
        print(f"  Total trades: {len(year_df)}")
        print(f"  Trail eligible: {len(year_trailed)} ({len(year_trailed)/len(year_df)*100:.1f}%)")

        if len(year_trailed) > 0:
            avg_improvement = year_trailed['improvement_r'].mean()
            total_improvement = year_trailed['improvement_r'].sum()
            print(f"  Average improvement: {avg_improvement:.3f}R")
            print(f"  Total improvement: {total_improvement:.3f}R")

            original_avg = year_df['original_r'].mean()
            trailed_avg = year_df['trail_exit_r'].mean()
            print(f"  Original avg R: {original_avg:.3f}")
            print(f"  Trailed avg R: {trailed_avg:.3f}")
            print(f"  Net improvement: {trailed_avg - original_avg:.3f}R")

    # Symbol breakdown
    print(f"\n" + "-"*60)
    print("SYMBOL BREAKDOWN:")
    print("-"*60)

    for symbol in sorted(df['symbol'].unique()):
        symbol_df = df[df['symbol'] == symbol]
        symbol_trailed = symbol_df[symbol_df['trail_applied'] == True]

        print(f"\n{symbol}:")
        print(f"  Total trades: {len(symbol_df)}")
        print(f"  Trail eligible: {len(symbol_trailed)} ({len(symbol_trailed)/len(symbol_df)*100:.1f}%)")

        if len(symbol_trailed) > 0:
            avg_improvement = symbol_trailed['improvement_r'].mean()
            total_improvement = symbol_trailed['improvement_r'].sum()
            print(f"  Average improvement: {avg_improvement:.3f}R")
            print(f"  Total improvement: {total_improvement:.3f}R")

            original_avg = symbol_df['original_r'].mean()
            trailed_avg = symbol_df['trail_exit_r'].mean()
            print(f"  Original avg R: {original_avg:.3f}")
            print(f"  Trailed avg R: {trailed_avg:.3f}")
            print(f"  Net improvement: {trailed_avg - original_avg:.3f}R")

    # Year × Symbol breakdown
    print(f"\n" + "-"*60)
    print("YEAR × SYMBOL BREAKDOWN:")
    print("-"*60)

    for year in sorted(df['year'].unique()):
        if year == 0:
            continue

        print(f"\n{year}:")
        year_df = df[df['year'] == year]

        for symbol in sorted(year_df['symbol'].unique()):
            year_symbol_df = year_df[year_df['symbol'] == symbol]
            year_symbol_trailed = year_symbol_df[year_symbol_df['trail_applied'] == True]

            if len(year_symbol_df) > 0:
                print(f"  {symbol}: {len(year_symbol_df)} trades, {len(year_symbol_trailed)} trailed", end="")

                if len(year_symbol_trailed) > 0:
                    avg_improvement = year_symbol_trailed['improvement_r'].mean()
                    original_avg = year_symbol_df['original_r'].mean()
                    trailed_avg = year_symbol_df['trail_exit_r'].mean()
                    print(f" → {original_avg:.3f}R to {trailed_avg:.3f}R ({avg_improvement:+.3f}R)")
                else:
                    print(" → No trails applied")

    return df

def save_detailed_results(results):
    """Save detailed results to CSV files"""

    df = pd.DataFrame(results)

    # Overall results
    overall_file = "research/kap_outputs/tests/trailing_stop_details_overall.csv"
    df.to_csv(overall_file, index=False)
    print(f"\nDetailed results saved to: {overall_file}")

    # Split by year
    for year in sorted(df['year'].unique()):
        if year == 0:
            continue

        year_df = df[df['year'] == year]
        year_file = f"research/kap_outputs/tests/trailing_stop_details_year_{year}.csv"
        year_df.to_csv(year_file, index=False)
        print(f"Year {year} results saved to: {year_file}")

    # Split by symbol and year
    for symbol in sorted(df['symbol'].unique()):
        for year in sorted(df['year'].unique()):
            if year == 0:
                continue

            symbol_year_df = df[(df['symbol'] == symbol) & (df['year'] == year)]

            if len(symbol_year_df) > 0:
                symbol_year_file = f"research/kap_outputs/tests/trailing_stop_details_{symbol}_{year}.csv"
                symbol_year_df.to_csv(symbol_year_file, index=False)
                print(f"{symbol} {year} results saved to: {symbol_year_file}")

    # Summary statistics
    summary_stats = []

    for year in sorted(df['year'].unique()):
        if year == 0:
            continue

        for symbol in sorted(df['symbol'].unique()):
            subset = df[(df['year'] == year) & (df['symbol'] == symbol)]

            if len(subset) > 0:
                trailed_subset = subset[subset['trail_applied'] == True]

                summary_stats.append({
                    'year': year,
                    'symbol': symbol,
                    'total_trades': len(subset),
                    'trail_eligible': len(trailed_subset),
                    'trail_eligible_pct': len(trailed_subset) / len(subset) * 100,
                    'original_avg_r': subset['original_r'].mean(),
                    'trailed_avg_r': subset['trail_exit_r'].mean(),
                    'improvement_r': subset['trail_exit_r'].mean() - subset['original_r'].mean(),
                    'original_win_rate': (subset['original_r'] > 0).mean() * 100,
                    'trailed_win_rate': (subset['trail_exit_r'] > 0).mean() * 100,
                    'total_r_improvement': subset['improvement_r'].sum()
                })

    summary_df = pd.DataFrame(summary_stats)
    summary_file = "research/kap_outputs/tests/trailing_stop_summary.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"Summary statistics saved to: {summary_file}")

def main():
    """Main execution function"""

    print("TRAILING STOP TEST - COMPREHENSIVE ANALYSIS")
    print("=" * 60)
    print("Testing: Trail 0.5R after 1.5R MFE")
    print("Split: 2025 vs 2026 AND by symbol")
    print("=" * 60)

    # Load all trades
    trades = load_all_trades()

    if not trades:
        print("ERROR: No trades found!")
        return

    # Analyze with trailing stops
    results = analyze_trailing_stop(trades)

    # Generate comprehensive statistics
    generate_summary_stats(results)

    # Save detailed results
    save_detailed_results(results)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()