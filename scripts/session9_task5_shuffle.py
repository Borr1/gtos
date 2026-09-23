#!/usr/bin/env python3
"""
Session 9 — Task 5: Shuffle Test Replication
Validates whether OB continuation rate delta (~19pp) is structural or random.
"""
from pathlib import Path
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUTPUT_DIR = Path("research/archive/root_legacy_artifacts_2026_05_29/generated/session9")

np.random.seed(42)

print("=" * 80)
print("TASK 5: SHUFFLE TEST REPLICATION")
print("=" * 80)

def generate_trending_series(n_candles=5000, trend_prob=0.6, volatility=1.0):
    """Generate synthetic H1 candles with momentum (trending behavior)."""
    closes = [100.0]
    opens = [100.0]
    highs = [100.0]
    lows = [100.0]

    direction = 1  # 1 = up, -1 = down
    for i in range(1, n_candles):
        # Momentum: same direction as previous with trend_prob
        if np.random.random() < trend_prob:
            pass  # keep direction
        else:
            direction *= -1

        body = abs(np.random.normal(0.5, 0.3)) * volatility * direction
        o = closes[-1]
        c = o + body
        wick_up = abs(np.random.normal(0.1, 0.1)) * volatility
        wick_down = abs(np.random.normal(0.1, 0.1)) * volatility
        h = max(o, c) + wick_up
        l = min(o, c) - wick_down

        opens.append(o)
        closes.append(c)
        highs.append(h)
        lows.append(l)

    return np.array(opens), np.array(highs), np.array(lows), np.array(closes)


def detect_structure_and_obs(opens, highs, lows, closes, lookback=5):
    """
    Simplified OB detection:
    1. Find impulse moves (3+ consecutive candles in same direction with acceleration)
    2. The last opposing candle before impulse is the OB
    3. Check if price returns to OB zone and continues in impulse direction
    """
    n = len(closes)
    ob_events = []

    for i in range(lookback, n - 20):
        # Detect impulse: 3 consecutive candles in same direction with increasing body
        bodies = closes[i-2:i+1] - opens[i-2:i+1]
        if all(b > 0 for b in bodies):  # Bullish impulse
            impulse_dir = 1
        elif all(b < 0 for b in bodies):  # Bearish impulse
            impulse_dir = -1
        else:
            continue

        # Total impulse size
        impulse_size = abs(closes[i] - opens[i-2])
        avg_body = np.mean(np.abs(bodies))

        # Need meaningful impulse (> 1.5x average body of surrounding candles)
        surrounding_bodies = np.abs(closes[max(0,i-10):i-2] - opens[max(0,i-10):i-2])
        if len(surrounding_bodies) < 3:
            continue
        avg_surrounding = np.mean(surrounding_bodies)
        if impulse_size < 1.5 * avg_surrounding * 3:
            continue

        # OB is the last opposing candle before impulse
        ob_candle_idx = i - 3
        if ob_candle_idx < 0:
            continue

        ob_body = closes[ob_candle_idx] - opens[ob_candle_idx]
        # OB should be opposing the impulse
        if impulse_dir == 1 and ob_body >= 0:
            continue
        if impulse_dir == -1 and ob_body <= 0:
            continue

        # OB zone
        if impulse_dir == 1:
            ob_top = opens[ob_candle_idx]  # Top of bearish OB
            ob_bottom = closes[ob_candle_idx]
        else:
            ob_top = closes[ob_candle_idx]  # Top of bullish OB
            ob_bottom = opens[ob_candle_idx]

        # Check retest: does price come back to OB zone within next 15 candles?
        retested = False
        continuation = False
        for j in range(i+1, min(i+16, n)):
            if lows[j] <= ob_top and highs[j] >= ob_bottom:
                retested = True
                # Check continuation: does price move in impulse direction after retest?
                for k in range(j+1, min(j+10, n)):
                    if impulse_dir == 1 and closes[k] > closes[i]:
                        continuation = True
                        break
                    elif impulse_dir == -1 and closes[k] < closes[i]:
                        continuation = True
                        break
                break

        if retested:
            ob_events.append({
                'idx': i,
                'dir': impulse_dir,
                'continuation': continuation
            })

    return ob_events


def run_test(n_candles=5000, n_shuffles=1000, trend_prob=0.6):
    """Run structured vs shuffled comparison."""
    print(f"\nGenerating {n_candles} synthetic H1 candles (trend_prob={trend_prob})...")

    opens, highs, lows, closes = generate_trending_series(n_candles, trend_prob)

    # Detect OBs on structured series
    events = detect_structure_and_obs(opens, highs, lows, closes)
    n_obs = len(events)
    if n_obs == 0:
        print("No OB events detected in structured series")
        return None

    n_cont = sum(1 for e in events if e['continuation'])
    structured_rate = n_cont / n_obs

    print(f"Structured series: {n_cont}/{n_obs} continuations = {structured_rate*100:.1f}%")

    # Shuffle test
    print(f"Running {n_shuffles} shuffle iterations...")
    shuffle_rates = []

    for s in range(n_shuffles):
        # Shuffle the candle RETURNS (not absolute prices)
        returns = closes[1:] - closes[:-1]
        np.random.shuffle(returns)

        # Reconstruct prices from shuffled returns
        shuffled_closes = np.concatenate([[closes[0]], closes[0] + np.cumsum(returns)])

        # Need to reconstruct OHLC from shuffled closes
        body_ratios = (closes[1:] - opens[1:]) / (np.abs(closes[1:] - opens[1:]) + 0.001)
        orig_bodies = np.abs(closes[1:] - opens[1:])
        np.random.shuffle(orig_bodies)

        shuffled_opens = shuffled_closes.copy()
        shuffled_highs = shuffled_closes.copy()
        shuffled_lows = shuffled_closes.copy()

        for i in range(1, len(shuffled_closes)):
            body = orig_bodies[min(i-1, len(orig_bodies)-1)] * (1 if shuffled_closes[i] > shuffled_closes[i-1] else -1)
            shuffled_opens[i] = shuffled_closes[i] - body
            wick = abs(np.random.normal(0.1, 0.1))
            shuffled_highs[i] = max(shuffled_opens[i], shuffled_closes[i]) + wick
            shuffled_lows[i] = min(shuffled_opens[i], shuffled_closes[i]) - wick

        events_s = detect_structure_and_obs(shuffled_opens, shuffled_highs, shuffled_lows, shuffled_closes)
        if len(events_s) >= 5:  # Need enough events
            rate = sum(1 for e in events_s if e['continuation']) / len(events_s)
            shuffle_rates.append(rate)

    if not shuffle_rates:
        print("No valid shuffle iterations")
        return None

    shuffle_mean = np.mean(shuffle_rates)
    shuffle_std = np.std(shuffle_rates)

    print(f"\nResults:")
    print(f"  Structured OB continuation: {structured_rate*100:.1f}% (n={n_obs})")
    print(f"  Shuffled OB continuation:   {shuffle_mean*100:.1f}% ± {shuffle_std*100:.1f}%")
    print(f"  Delta:                      {(structured_rate - shuffle_mean)*100:+.1f}pp")
    print(f"  Z-score:                    {(structured_rate - shuffle_mean) / shuffle_std:.2f}")

    # Empirical p-value
    p_value = np.mean(np.array(shuffle_rates) >= structured_rate)
    print(f"  Empirical p-value:          {p_value:.4f}")

    return structured_rate, shuffle_mean, shuffle_std, shuffle_rates, n_obs


# Run with different momentum parameters
results = {}
for tp in [0.55, 0.60, 0.65]:
    print(f"\n{'='*60}")
    print(f"TREND PROBABILITY = {tp}")
    print(f"{'='*60}")
    r = run_test(n_candles=5000, n_shuffles=500, trend_prob=tp)
    if r:
        results[tp] = r

# Chart
if results:
    fig, axes = plt.subplots(1, len(results), figsize=(5*len(results), 5))
    if len(results) == 1:
        axes = [axes]

    for idx, (tp, (sr, sm, ss, shuffle_rates, n)) in enumerate(results.items()):
        axes[idx].hist(shuffle_rates, bins=30, alpha=0.7, color='steelblue', edgecolor='white')
        axes[idx].axvline(x=sr, color='red', linewidth=2, label=f'Structured: {sr*100:.1f}%')
        axes[idx].axvline(x=sm, color='black', linewidth=1, linestyle='--', label=f'Shuffle mean: {sm*100:.1f}%')
        axes[idx].set_title(f'Trend prob={tp}, n={n} OBs')
        axes[idx].set_xlabel('Continuation Rate')
        axes[idx].legend(fontsize=8)

    plt.tight_layout()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outpath = OUTPUT_DIR / 'session9_shuffle_test.png'
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    print(f"\nChart saved: {outpath}")

print("\n" + "=" * 80)
print("TASK 5 COMPLETE")
print("=" * 80)
