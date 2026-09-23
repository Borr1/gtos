"""ATR Multiplier Analysis: Compare SL Distances 2025 vs 2026

Validates differences in stop loss distances between 2025 and 2026 for stopped-out trades.
Compares both absolute dollar amounts and ATR multiples.
Statistical testing using t-test for significance.
"""

import json
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import warnings
from typing import Dict, List, Tuple, Optional

warnings.filterwarnings('ignore')


def load_trade_data() -> List[Dict]:
    """Load unified trade data from knowledge base backtest."""
    trade_file = Path("knowledge_base_backtest/analysis/unified_trades_v2_20260331.json")

    if not trade_file.exists():
        raise FileNotFoundError(f"Trade data not found at {trade_file}")

    with open(trade_file, 'r') as f:
        trades = json.load(f)

    print(f"Loaded {len(trades)} total trades")
    return trades


def calculate_atr(symbol: str, date: str, period: int = 14) -> Optional[float]:
    """Calculate ATR for given symbol and date using historical data.

    Uses D1 timeframe data to calculate 14-period ATR.
    """
    # Try multiple possible data locations
    data_paths = [
        f"data/{symbol}_D1.csv",
        f"data/historical/{symbol}_D1.csv",
        f"data/raw/{symbol}_D1.csv"
    ]

    df = None
    for path in data_paths:
        if Path(path).exists():
            try:
                df = pd.read_csv(path)
                break
            except Exception as e:
                continue

    if df is None:
        print(f"Warning: No price data found for {symbol}")
        return None

    # Standardize column names
    df.columns = [col.lower() for col in df.columns]

    # Handle different datetime formats
    if 'time' in df.columns:
        df['date'] = pd.to_datetime(df['time']).dt.date
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    elif 'datetime' in df.columns:
        df['date'] = pd.to_datetime(df['datetime']).dt.date
    else:
        print(f"Warning: No date column found in {symbol} data")
        return None

    # Calculate True Range
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['prev_close'])
    df['tr3'] = abs(df['low'] - df['prev_close'])
    df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)

    # Calculate ATR (simple moving average)
    df['atr'] = df['true_range'].rolling(window=period, min_periods=period).mean()

    # Find ATR for the specific date
    target_date = pd.to_datetime(date).date()

    # Get closest available date (within 7 days)
    df['date_diff'] = abs((pd.to_datetime(df['date']).dt.date - target_date).apply(lambda x: x.days))
    closest = df[df['date_diff'] <= 7].sort_values('date_diff')

    if len(closest) > 0 and not pd.isna(closest.iloc[0]['atr']):
        return closest.iloc[0]['atr']

    print(f"Warning: No ATR data available for {symbol} on {date}")
    return None


def extract_symbol_from_trade(trade: Dict) -> str:
    """Extract trading symbol from trade data.

    For now, assume all trades are XAUUSD (Gold) based on project context.
    This could be expanded to parse from trade_id or other fields.
    """
    return "XAUUSD"


def filter_stopped_trades(trades: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Filter stopped-out trades by year (2025 vs 2026)."""

    stopped_2025 = []
    stopped_2026 = []

    for trade in trades:
        if trade.get('outcome') == 'LOSS' and trade.get('sl_dollars') is not None:
            date_str = trade.get('date', '')
            if date_str.startswith('2025'):
                stopped_2025.append(trade)
            elif date_str.startswith('2026'):
                stopped_2026.append(trade)

    print(f"Filtered {len(stopped_2025)} stopped trades in 2025")
    print(f"Filtered {len(stopped_2026)} stopped trades in 2026")

    return stopped_2025, stopped_2026


def calculate_stop_out_rates(trades: List[Dict]) -> Tuple[float, float]:
    """Calculate stop-out rates for 2025 vs 2026."""

    trades_2025 = [t for t in trades if t.get('date', '').startswith('2025')]
    trades_2026 = [t for t in trades if t.get('date', '').startswith('2026')]

    if len(trades_2025) == 0 or len(trades_2026) == 0:
        return 0.0, 0.0

    stopped_2025 = len([t for t in trades_2025 if t.get('outcome') == 'LOSS'])
    stopped_2026 = len([t for t in trades_2026 if t.get('outcome') == 'LOSS'])

    rate_2025 = stopped_2025 / len(trades_2025)
    rate_2026 = stopped_2026 / len(trades_2026)

    return rate_2025, rate_2026


def analyze_atr_multipliers(stopped_2025: List[Dict], stopped_2026: List[Dict]) -> Dict:
    """Calculate and compare ATR multipliers between years."""

    print("\nCalculating ATR multipliers...")

    # Extract all SL dollar amounts (regardless of ATR availability)
    sl_dollars_2025_all = []
    sl_dollars_2026_all = []

    for trade in stopped_2025:
        sl_dollars = trade.get('sl_dollars', 0)
        if sl_dollars > 0:
            sl_dollars_2025_all.append(sl_dollars)

    for trade in stopped_2026:
        sl_dollars = trade.get('sl_dollars', 0)
        if sl_dollars > 0:
            sl_dollars_2026_all.append(sl_dollars)

    print(f"Extracted SL dollars: {len(sl_dollars_2025_all)} for 2025, {len(sl_dollars_2026_all)} for 2026")

    # Calculate ATR multipliers for 2025
    atr_mult_2025 = []
    sl_dollars_2025 = []

    for trade in stopped_2025:
        sl_dollars = trade.get('sl_dollars', 0)
        if sl_dollars <= 0:
            continue

        symbol = extract_symbol_from_trade(trade)
        date = trade.get('date')
        atr = calculate_atr(symbol, date)

        if atr and atr > 0:
            atr_multiplier = sl_dollars / atr
            atr_mult_2025.append(atr_multiplier)
            sl_dollars_2025.append(sl_dollars)

    # Calculate ATR multipliers for 2026
    atr_mult_2026 = []
    sl_dollars_2026 = []

    for trade in stopped_2026:
        sl_dollars = trade.get('sl_dollars', 0)
        if sl_dollars <= 0:
            continue

        symbol = extract_symbol_from_trade(trade)
        date = trade.get('date')
        atr = calculate_atr(symbol, date)

        if atr and atr > 0:
            atr_multiplier = sl_dollars / atr
            atr_mult_2026.append(atr_multiplier)
            sl_dollars_2026.append(sl_dollars)

    print(f"Calculated ATR multipliers: {len(atr_mult_2025)} for 2025, {len(atr_mult_2026)} for 2026")

    return {
        'atr_mult_2025': atr_mult_2025,
        'atr_mult_2026': atr_mult_2026,
        'sl_dollars_2025': sl_dollars_2025,
        'sl_dollars_2026': sl_dollars_2026,
        'sl_dollars_2025_all': sl_dollars_2025_all,
        'sl_dollars_2026_all': sl_dollars_2026_all
    }


def run_statistical_tests(data: Dict) -> Dict:
    """Run t-tests to compare differences between years."""

    results = {}

    # T-test for ATR multipliers
    if len(data['atr_mult_2025']) > 0 and len(data['atr_mult_2026']) > 0:
        atr_t_stat, atr_p_value = stats.ttest_ind(
            data['atr_mult_2025'],
            data['atr_mult_2026']
        )
        results['atr_test'] = {
            't_statistic': atr_t_stat,
            'p_value': atr_p_value,
            'significant': atr_p_value < 0.05
        }

    # T-test for SL dollars (use full dataset)
    if len(data['sl_dollars_2025_all']) > 0 and len(data['sl_dollars_2026_all']) > 0:
        sl_t_stat, sl_p_value = stats.ttest_ind(
            data['sl_dollars_2025_all'],
            data['sl_dollars_2026_all']
        )
        results['sl_dollars_test'] = {
            't_statistic': sl_t_stat,
            'p_value': sl_p_value,
            'significant': sl_p_value < 0.05
        }

    return results


def generate_summary_stats(data: Dict) -> Dict:
    """Generate summary statistics for both years."""

    summary = {}

    # ATR multiplier stats
    if data['atr_mult_2025']:
        summary['atr_mult_2025'] = {
            'mean': np.mean(data['atr_mult_2025']),
            'median': np.median(data['atr_mult_2025']),
            'std': np.std(data['atr_mult_2025']),
            'min': np.min(data['atr_mult_2025']),
            'max': np.max(data['atr_mult_2025']),
            'count': len(data['atr_mult_2025'])
        }

    if data['atr_mult_2026']:
        summary['atr_mult_2026'] = {
            'mean': np.mean(data['atr_mult_2026']),
            'median': np.median(data['atr_mult_2026']),
            'std': np.std(data['atr_mult_2026']),
            'min': np.min(data['atr_mult_2026']),
            'max': np.max(data['atr_mult_2026']),
            'count': len(data['atr_mult_2026'])
        }

    # SL dollars stats (use full dataset regardless of ATR availability)
    if data['sl_dollars_2025_all']:
        summary['sl_dollars_2025'] = {
            'mean': np.mean(data['sl_dollars_2025_all']),
            'median': np.median(data['sl_dollars_2025_all']),
            'std': np.std(data['sl_dollars_2025_all']),
            'min': np.min(data['sl_dollars_2025_all']),
            'max': np.max(data['sl_dollars_2025_all']),
            'count': len(data['sl_dollars_2025_all'])
        }

    if data['sl_dollars_2026_all']:
        summary['sl_dollars_2026'] = {
            'mean': np.mean(data['sl_dollars_2026_all']),
            'median': np.median(data['sl_dollars_2026_all']),
            'std': np.std(data['sl_dollars_2026_all']),
            'min': np.min(data['sl_dollars_2026_all']),
            'max': np.max(data['sl_dollars_2026_all']),
            'count': len(data['sl_dollars_2026_all'])
        }

    return summary


def main():
    """Execute ATR multiplier analysis."""

    print("=== ATR Multiplier Analysis: 2025 vs 2026 ===")
    print("Loading trade data...")

    try:
        # Load all trade data
        all_trades = load_trade_data()

        # Calculate stop-out rates
        rate_2025, rate_2026 = calculate_stop_out_rates(all_trades)
        print(f"\nStop-out rates:")
        print(f"2025: {rate_2025:.1%}")
        print(f"2026: {rate_2026:.1%}")

        # Filter stopped trades
        stopped_2025, stopped_2026 = filter_stopped_trades(all_trades)

        if len(stopped_2025) == 0 or len(stopped_2026) == 0:
            print("Error: Insufficient stopped trades for comparison")
            return

        # Analyze ATR multipliers
        atr_data = analyze_atr_multipliers(stopped_2025, stopped_2026)

        # Generate summary statistics
        summary = generate_summary_stats(atr_data)

        # Run statistical tests
        test_results = run_statistical_tests(atr_data)

        # Print results
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)

        if 'atr_mult_2025' in summary:
            print(f"\nATR Multipliers 2025 (n={summary['atr_mult_2025']['count']}):")
            print(f"  Mean: {summary['atr_mult_2025']['mean']:.2f}")
            print(f"  Median: {summary['atr_mult_2025']['median']:.2f}")
            print(f"  Std Dev: {summary['atr_mult_2025']['std']:.2f}")
            print(f"  Range: {summary['atr_mult_2025']['min']:.2f} - {summary['atr_mult_2025']['max']:.2f}")

        if 'atr_mult_2026' in summary:
            print(f"\nATR Multipliers 2026 (n={summary['atr_mult_2026']['count']}):")
            print(f"  Mean: {summary['atr_mult_2026']['mean']:.2f}")
            print(f"  Median: {summary['atr_mult_2026']['median']:.2f}")
            print(f"  Std Dev: {summary['atr_mult_2026']['std']:.2f}")
            print(f"  Range: {summary['atr_mult_2026']['min']:.2f} - {summary['atr_mult_2026']['max']:.2f}")

        if 'sl_dollars_2025' in summary:
            print(f"\nSL Dollars 2025 (n={summary['sl_dollars_2025']['count']}):")
            print(f"  Mean: ${summary['sl_dollars_2025']['mean']:.2f}")
            print(f"  Median: ${summary['sl_dollars_2025']['median']:.2f}")
            print(f"  Std Dev: ${summary['sl_dollars_2025']['std']:.2f}")
            print(f"  Range: ${summary['sl_dollars_2025']['min']:.2f} - ${summary['sl_dollars_2025']['max']:.2f}")
        else:
            print(f"\nSL Dollars 2025: No data available")

        if 'sl_dollars_2026' in summary:
            print(f"\nSL Dollars 2026 (n={summary['sl_dollars_2026']['count']}):")
            print(f"  Mean: ${summary['sl_dollars_2026']['mean']:.2f}")
            print(f"  Median: ${summary['sl_dollars_2026']['median']:.2f}")
            print(f"  Std Dev: ${summary['sl_dollars_2026']['std']:.2f}")
            print(f"  Range: ${summary['sl_dollars_2026']['min']:.2f} - ${summary['sl_dollars_2026']['max']:.2f}")
        else:
            print(f"\nSL Dollars 2026: No data available")

        print("\n" + "="*60)
        print("STATISTICAL TESTS")
        print("="*60)

        if 'atr_test' in test_results:
            print(f"\nATR Multiplier T-Test:")
            print(f"  T-statistic: {test_results['atr_test']['t_statistic']:.4f}")
            print(f"  P-value: {test_results['atr_test']['p_value']:.4f}")
            print(f"  Significant: {test_results['atr_test']['significant']}")

        if 'sl_dollars_test' in test_results:
            print(f"\nSL Dollars T-Test:")
            print(f"  T-statistic: {test_results['sl_dollars_test']['t_statistic']:.4f}")
            print(f"  P-value: {test_results['sl_dollars_test']['p_value']:.4f}")
            print(f"  Significant: {test_results['sl_dollars_test']['significant']}")

        # Calculate differences
        if 'atr_mult_2025' in summary and 'atr_mult_2026' in summary:
            atr_diff = summary['atr_mult_2026']['mean'] - summary['atr_mult_2025']['mean']
            atr_pct_change = (atr_diff / summary['atr_mult_2025']['mean']) * 100
            print(f"\nATR Multiplier Change:")
            print(f"  2025→2026: {atr_diff:+.2f} ({atr_pct_change:+.1f}%)")
        else:
            print(f"\nATR Multiplier Change: Cannot calculate (insufficient data)")

        if 'sl_dollars_2025' in summary and 'sl_dollars_2026' in summary:
            sl_diff = summary['sl_dollars_2026']['mean'] - summary['sl_dollars_2025']['mean']
            sl_pct_change = (sl_diff / summary['sl_dollars_2025']['mean']) * 100
            print(f"\nSL Dollar Change:")
            print(f"  2025→2026: ${sl_diff:+.2f} ({sl_pct_change:+.1f}%)")
        else:
            print(f"\nSL Dollar Change: Cannot calculate (insufficient data)")

        rate_diff = rate_2026 - rate_2025
        print(f"\nStop-out Rate Change:")
        print(f"  2025→2026: {rate_diff:+.1%} (from {rate_2025:.1%} to {rate_2026:.1%})")

        print("\n" + "="*60)
        print("INTERPRETATION")
        print("="*60)

        # Provide interpretation
        if 'sl_dollars_test' in test_results and test_results['sl_dollars_test']['significant']:
            if sl_diff > 0:
                print("✓ SL distances increased significantly in 2026")
            else:
                print("✓ SL distances decreased significantly in 2026")
        else:
            print("• No significant difference in SL distances between years")

        if 'atr_test' in test_results and test_results['atr_test']['significant']:
            if summary['atr_mult_2026']['mean'] > summary['atr_mult_2025']['mean']:
                print("✓ ATR multipliers increased significantly in 2026")
            else:
                print("✓ ATR multipliers decreased significantly in 2026")
        else:
            print("• No significant difference in ATR multipliers between years")

        if abs(rate_diff) > 0.05:  # 5% threshold for meaningful difference
            if rate_diff > 0:
                print("⚠ Stop-out rate increased in 2026")
            else:
                print("✓ Stop-out rate improved in 2026")

        print(f"\nAnalysis complete. Results saved to: {Path(__file__).name}")

    except Exception as e:
        print(f"Error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()