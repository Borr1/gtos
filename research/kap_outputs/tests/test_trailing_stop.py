#!/usr/bin/env python3
"""
Trailing stop test on ALL historical trades.
Tests whether a trailing stop improves net R across the full population.
"""
import json, glob, os, sys
import numpy as np

sessions_dir = 'knowledge_base_backtest/sessions'
if not os.path.isdir(sessions_dir):
    print("ERROR: No sessions directory found")
    sys.exit(1)

# Load ALL trades with MFE data
trades = []
for f in sorted(glob.glob(os.path.join(sessions_dir, '*.json'))):
    try:
        d = json.load(open(f))
        ts = d.get('trade_summary', {})
        if not (isinstance(ts, dict) and ts.get('trade_taken')):
            continue

        trades_list = ts.get('trades', [])
        if not trades_list:
            trades_list = [ts]

        for t in trades_list:
            mfe = t.get('mfe_r', t.get('mfe'))
            mae = t.get('mae_r', t.get('mae', 0))
            r_multiple = t.get('r_multiple', 0)
            outcome = t.get('outcome', '')
            exit_sub = t.get('exit_substate', '')

            if mfe is not None:
                trades.append({
                    'date': d.get('date', os.path.basename(f)[:10]),
                    'r_multiple': r_multiple,
                    'mfe': mfe,
                    'mae': mae or 0,
                    'outcome': outcome,
                    'exit_substate': exit_sub,
                    'symbol': d.get('symbol', 'XAUUSD'),
                })
    except Exception:
        continue

print(f"Loaded {len(trades)} trades with MFE data")
timeouts = [t for t in trades if 'TIMEOUT' in t['exit_substate']]
print(f"Timeouts: {len(timeouts)} (avg MFE={np.mean([t['mfe'] for t in timeouts]):.2f}R, avg final={np.mean([t['r_multiple'] for t in timeouts]):.2f}R)")
print(f"Current total R: {sum(t['r_multiple'] for t in trades):.1f}")
print()

# Baseline
baseline_R = sum(t['r_multiple'] for t in trades)
baseline_WR = np.mean([1 if t['outcome'] == 'WIN' else 0 for t in trades])

print(f"=== BASELINE ===")
print(f"Total R: {baseline_R:.1f}")
print(f"WR: {baseline_WR:.1%}")
print(f"Avg R: {np.mean([t['r_multiple'] for t in trades]):.3f}")
print()

# Test multiple trailing stop configurations
configs = [
    {"name": "Trail 0.5R after 0.5R MFE", "activation": 0.5, "trail": 0.5},
    {"name": "Trail 0.5R after 1.0R MFE", "activation": 1.0, "trail": 0.5},
    {"name": "Trail 0.5R after 1.5R MFE", "activation": 1.5, "trail": 0.5},
    {"name": "Trail 0.75R after 1.0R MFE", "activation": 1.0, "trail": 0.75},
    {"name": "Trail 1.0R after 1.0R MFE", "activation": 1.0, "trail": 1.0},
    {"name": "Trail 1.0R after 1.5R MFE", "activation": 1.5, "trail": 1.0},
    {"name": "Trail 1.0R after 2.0R MFE", "activation": 2.0, "trail": 1.0},
    {"name": "Trail 1.5R after 2.0R MFE", "activation": 2.0, "trail": 1.5},
    {"name": "Fixed TP 1.5R", "fixed_tp": 1.5},
    {"name": "Fixed TP 2.0R", "fixed_tp": 2.0},
    {"name": "Fixed TP 2.5R", "fixed_tp": 2.5},
    {"name": "Fixed TP 3.0R", "fixed_tp": 3.0},
]

print(f"{'Config':<35s} {'Total R':>8s} {'vs Base':>8s} {'WR':>6s} {'Avg R':>7s} {'Helped':>7s} {'Hurt':>6s}")
print("-" * 85)

best_config = None
best_R = baseline_R
all_results = []

for cfg in configs:
    new_results = []
    helped = 0
    hurt = 0

    for t in trades:
        mfe = t['mfe']
        original_r = t['r_multiple']

        if 'fixed_tp' in cfg:
            tp = cfg['fixed_tp']
            if mfe >= tp:
                new_r = tp
            else:
                new_r = original_r
        else:
            activation = cfg['activation']
            trail = cfg['trail']

            if mfe >= activation:
                trailed_r = mfe - trail
                new_r = max(trailed_r, -1.0)
            else:
                new_r = original_r

        if new_r > original_r + 0.01:
            helped += 1
        elif new_r < original_r - 0.01:
            hurt += 1

        new_results.append(new_r)

    total_R = sum(new_results)
    avg_R = np.mean(new_results)
    wr = np.mean([1 if r > 0 else 0 for r in new_results])
    diff = total_R - baseline_R

    print(f"{cfg['name']:<35s} {total_R:>8.1f} {diff:>+8.1f} {wr:>6.1%} {avg_R:>7.3f} {helped:>7d} {hurt:>6d}")

    all_results.append({
        "config": cfg['name'],
        "total_R": round(total_R, 1),
        "diff": round(diff, 1),
        "wr": round(wr, 3),
        "avg_R": round(avg_R, 3),
        "helped": helped,
        "hurt": hurt,
    })

    if total_R > best_R:
        best_R = total_R
        best_config = cfg['name']

print()
if best_config:
    print(f"=== BEST CONFIG: {best_config} ({best_R:.1f}R, {best_R - baseline_R:+.1f} vs baseline) ===")
else:
    print(f"=== NO CONFIG BEAT BASELINE ({baseline_R:.1f}R) ===")

# Breakdown by exit reason
print()
print("=== BREAKDOWN: Timeout trades vs non-timeout ===")
non_timeouts = [t for t in trades if 'TIMEOUT' not in t['exit_substate']]

print(f"Timeout trades:     n={len(timeouts)}, avg MFE={np.mean([t['mfe'] for t in timeouts]):.2f}R, avg final R={np.mean([t['r_multiple'] for t in timeouts]):.2f}R, total R={sum(t['r_multiple'] for t in timeouts):.1f}")
print(f"Non-timeout trades: n={len(non_timeouts)}, avg MFE={np.mean([t['mfe'] for t in non_timeouts]):.2f}R, avg final R={np.mean([t['r_multiple'] for t in non_timeouts]):.2f}R, total R={sum(t['r_multiple'] for t in non_timeouts):.1f}")

# Exit substate breakdown
print()
print("=== EXIT SUBSTATE BREAKDOWN ===")
from collections import Counter
for es, cnt in Counter(t['exit_substate'] for t in trades).most_common():
    subset = [t for t in trades if t['exit_substate'] == es]
    print(f"  {es:<30s} n={cnt:>3d}  avg MFE={np.mean([t['mfe'] for t in subset]):.2f}R  avg final={np.mean([t['r_multiple'] for t in subset]):.2f}R")

# Period comparison
print()
print("=== BASELINE BY PERIOD ===")
for label, filt in [
    ("2024-2025", lambda t: t['date'][:4] in ('2024', '2025')),
    ("2026", lambda t: t['date'][:4] == '2026'),
]:
    subset = [t for t in trades if t['date'] and filt(t)]
    if subset:
        orig = sum(t['r_multiple'] for t in subset)
        print(f"  {label}: {len(subset)} trades, {orig:.1f}R total, avg MFE={np.mean([t['mfe'] for t in subset]):.2f}R")

# Save results
results_file = 'research/kap_outputs/test_results.json'
existing = json.load(open(results_file)) if os.path.exists(results_file) else []
result = {
    "test": "trailing_stop_optimization",
    "date": "2026-04-07",
    "trades": len(trades),
    "baseline_R": round(baseline_R, 1),
    "best_config": best_config or "NONE (baseline wins)",
    "best_R": round(best_R, 1),
    "improvement": round(best_R - baseline_R, 1),
    "configs_tested": len(configs),
    "all_configs": all_results,
}
existing.append(result)
with open(results_file, 'w') as f:
    json.dump(existing, f, indent=2)

print(f"\nResults saved to {results_file}")
