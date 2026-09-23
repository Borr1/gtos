#!/usr/bin/env python3
"""
Pre-Batch Calibration: Impulse Distribution + Config Verification
Computes impulse candle counts per OB, checks for cliff patterns,
and verifies config readiness for batch tests.
"""

import os
import sys
import json
import time
import warnings
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))
import multi_instrument_screening as m

DATA_DIR = Path(__file__).parent.parent / "exports" / "multi_instrument"
RESULTS_DIR = DATA_DIR / "screening_results"
PROJECT_DIR = Path(__file__).parent.parent

INSTRUMENTS = ['XAUUSD', 'USDJPY', 'GBPUSD', 'US30_cash', 'GBPJPY', 'NZDUSD']

# ─── IMPULSE COUNTING ────────────────────────────────────────────────────────

def process_with_impulse(symbol: str) -> Optional[dict]:
    """Run OB detection and count impulse candles per OB."""
    df = m.load_instrument(symbol, 'H1')
    if df is None:
        return None

    atr = m.compute_atr(df, 14)
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    times = df['dt_utc'].values
    n = len(df)

    # Run the same OB detection as screening
    obs, breaks, swings = m.process_candles(df, atr)
    m.track_retests(df, obs)
    m.measure_continuation(df, obs, atr)

    # Now compute impulse candle count for each OB
    # We need the broken swing index for each OB.
    # The OB stores formation_index (the OB candle) and event_index (the break candle).
    # The impulse leg runs from some earlier point to the break candle.
    # We approximate: impulse_count = event_index - formation_index
    # (the OB candle is typically near the start of the impulse, and the
    # break candle is the end of the impulse)

    ob_data = []
    for ob in obs:
        impulse_count = ob.event_index - ob.formation_index
        if impulse_count < 1:
            impulse_count = 1

        # Check if impulse leg creates an FVG
        creates_fvg = False
        start_i = ob.formation_index
        end_i = ob.event_index
        for k in range(start_i + 1, min(end_i, n - 1)):
            if np.isnan(atr[k]) or atr[k] == 0:
                continue
            min_gap = m.FVG_MIN_GAP_ATR * atr[k]
            if ob.direction == 'bullish':
                gap = lows[k + 1] - highs[k - 1]
                if gap >= min_gap:
                    creates_fvg = True
                    break
            else:
                gap = lows[k - 1] - highs[k + 1]
                if gap >= min_gap:
                    creates_fvg = True
                    break

        ob_data.append({
            'direction': ob.direction,
            'impulse_count': impulse_count,
            'creates_fvg': creates_fvg,
            'retested': ob.retested,
            'continuation': ob.continuation,
            'formation_index': ob.formation_index,
            'event_index': ob.event_index,
        })

    # Compute zone heights for SL estimation
    zone_heights = []
    for ob in obs:
        zh = ob.high - ob.low
        if zh > 0:
            zone_heights.append(zh)

    median_atr = np.nanmedian(atr[14:])

    return {
        'symbol': symbol,
        'n_obs': len(obs),
        'ob_data': ob_data,
        'median_zone_height': float(np.median(zone_heights)) if zone_heights else 0,
        'p25_zone_height': float(np.percentile(zone_heights, 25)) if zone_heights else 0,
        'median_atr': float(median_atr),
    }


def analyze_impulse_distribution(result: dict) -> dict:
    """Analyze impulse candle distribution and find cliff points."""
    ob_data = result['ob_data']
    retested = [ob for ob in ob_data if ob['retested']]

    if not retested:
        return {}

    impulse_counts = [ob['impulse_count'] for ob in retested]
    ic_array = np.array(impulse_counts)

    stats = {
        'min': int(np.min(ic_array)),
        'p25': int(np.percentile(ic_array, 25)),
        'median': int(np.median(ic_array)),
        'p75': int(np.percentile(ic_array, 75)),
        'max': int(np.max(ic_array)),
    }

    # Continuation rate by impulse count bucket
    buckets = {}
    for ob in retested:
        ic = ob['impulse_count']
        if ic not in buckets:
            buckets[ic] = {'n': 0, 'cont': 0}
        buckets[ic]['n'] += 1
        if ob['continuation']:
            buckets[ic]['cont'] += 1

    # Rate per bucket
    bucket_rates = {}
    for ic in sorted(buckets.keys()):
        b = buckets[ic]
        rate = b['cont'] / b['n'] * 100 if b['n'] > 0 else 0
        bucket_rates[ic] = {'n': b['n'], 'rate': round(rate, 1)}

    # Cumulative rates: ≤X and >X for each threshold
    cum_rates = {}
    for threshold in range(2, 20):
        le = [ob for ob in retested if ob['impulse_count'] <= threshold]
        gt = [ob for ob in retested if ob['impulse_count'] > threshold]
        le_rate = sum(1 for ob in le if ob['continuation']) / len(le) * 100 if le else 0
        gt_rate = sum(1 for ob in gt if ob['continuation']) / len(gt) * 100 if gt else 0
        cum_rates[threshold] = {
            'le_n': len(le), 'le_rate': round(le_rate, 1),
            'gt_n': len(gt), 'gt_rate': round(gt_rate, 1),
            'delta': round(le_rate - gt_rate, 1),
        }

    # Find cliff: largest delta between ≤X and >X with both sides having n≥20
    best_cliff = None
    best_delta = 0
    for t, cr in cum_rates.items():
        if cr['le_n'] >= 20 and cr['gt_n'] >= 20 and cr['delta'] > best_delta:
            best_delta = cr['delta']
            best_cliff = t

    # Median split
    med = stats['median']
    le_med = [ob for ob in retested if ob['impulse_count'] <= med]
    gt_med = [ob for ob in retested if ob['impulse_count'] > med]
    cont_le_med = sum(1 for ob in le_med if ob['continuation']) / len(le_med) * 100 if le_med else 0
    cont_gt_med = sum(1 for ob in gt_med if ob['continuation']) / len(gt_med) * 100 if gt_med else 0

    # FVG analysis
    fvg_yes = [ob for ob in retested if ob['creates_fvg']]
    fvg_no = [ob for ob in retested if not ob['creates_fvg']]
    fvg_yes_cont = sum(1 for ob in fvg_yes if ob['continuation']) / len(fvg_yes) * 100 if fvg_yes else 0
    fvg_no_cont = sum(1 for ob in fvg_no if ob['continuation']) / len(fvg_no) * 100 if fvg_no else 0
    fvg_pct = len(fvg_yes) / len(retested) * 100 if retested else 0

    return {
        'stats': stats,
        'bucket_rates': bucket_rates,
        'cum_rates': cum_rates,
        'cliff_threshold': best_cliff,
        'cliff_delta': best_delta,
        'cont_le_median': round(cont_le_med, 1),
        'cont_gt_median': round(cont_gt_med, 1),
        'median_delta': round(cont_le_med - cont_gt_med, 1),
        'fvg_pct': round(fvg_pct, 1),
        'fvg_yes_cont': round(fvg_yes_cont, 1),
        'fvg_no_cont': round(fvg_no_cont, 1),
        'fvg_delta': round(fvg_yes_cont - fvg_no_cont, 1),
        'fvg_yes_n': len(fvg_yes),
        'fvg_no_n': len(fvg_no),
    }


# ─── CONFIG CHECK ────────────────────────────────────────────────────────────

def check_configs() -> dict:
    """Check existing config files for instrument overrides."""
    config_paths = [
        PROJECT_DIR / 'config' / 'agent_config.yaml',
        PROJECT_DIR / 'config' / 'config.yaml',
        PROJECT_DIR / 'config.yaml',
        PROJECT_DIR / 'src' / 'config.py',
    ]

    found_configs = {}
    for p in config_paths:
        if p.exists():
            found_configs[str(p)] = p.read_text()

    # Also check for instrument-specific files
    config_dir = PROJECT_DIR / 'config'
    if config_dir.exists():
        for f in config_dir.iterdir():
            if f.suffix in ('.yaml', '.yml', '.json', '.py'):
                found_configs[str(f)] = f.read_text()

    return found_configs


def get_spread_gates() -> dict:
    """Compute spread gates from extraction_summary.json."""
    with open(DATA_DIR / 'extraction_summary.json') as f:
        summary = json.load(f)

    spread_data = summary.get('spread_samples', {})
    gates = {}

    symbol_map = {
        'USDJPY': 'USDJPY',
        'GBPUSD': 'GBPUSD',
        'US30_cash': 'US30.cash',
        'GBPJPY': 'GBPJPY',
        'NZDUSD': 'NZDUSD',
        'XAUUSD': 'XAUUSD',
    }

    for sym, spread_key in symbol_map.items():
        if spread_key in spread_data:
            s = spread_data[spread_key]
            gates[sym] = {
                'median_spread': s['median_spread'],
                'p90_spread': s.get('p90_spread', 0),
                'max_spread': s.get('max_spread', 0),
                'suggested_gate': round(s.get('p90_spread', 0) * 1.5, 6),
            }

    return gates


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    start_time = time.time()
    print("=" * 70)
    print("PRE-BATCH CALIBRATION: IMPULSE DISTRIBUTION + CONFIG VERIFICATION")
    print("=" * 70)

    all_results = {}
    all_impulse = {}

    # ── PART 1: IMPULSE DISTRIBUTIONS ──

    print("\n" + "=" * 70)
    print("PART 1: IMPULSE CANDLE DISTRIBUTIONS")
    print("=" * 70)

    # XAUUSD first (calibration gate)
    print("\n--- XAUUSD CALIBRATION ---")
    xau = process_with_impulse('XAUUSD')
    if xau is None:
        print("FATAL: Cannot load XAUUSD")
        sys.exit(1)

    xau_imp = analyze_impulse_distribution(xau)
    all_results['XAUUSD'] = xau
    all_impulse['XAUUSD'] = xau_imp

    s = xau_imp['stats']
    print(f"  Distribution: min={s['min']}, p25={s['p25']}, median={s['median']}, "
          f"p75={s['p75']}, max={s['max']}")
    print(f"  ≤ median ({s['median']}): {xau_imp['cont_le_median']}%")
    print(f"  > median ({s['median']}): {xau_imp['cont_gt_median']}%")
    print(f"  Median delta: {xau_imp['median_delta']}pp")

    if xau_imp['cliff_threshold']:
        ct = xau_imp['cliff_threshold']
        cr = xau_imp['cum_rates'][ct]
        print(f"  Cliff at ≤{ct}: {cr['le_rate']}% (n={cr['le_n']}) vs >{ct}: {cr['gt_rate']}% (n={cr['gt_n']}) → {cr['delta']}pp")
    else:
        print(f"  No clear cliff found")

    print(f"  FVG in impulse: {xau_imp['fvg_pct']}% of OBs")
    print(f"  FVG yes: {xau_imp['fvg_yes_cont']}% (n={xau_imp['fvg_yes_n']}), "
          f"FVG no: {xau_imp['fvg_no_cont']}% (n={xau_imp['fvg_no_n']}), "
          f"delta: {xau_imp['fvg_delta']}pp")

    # Print per-count breakdown for gold
    print(f"\n  XAUUSD per-count breakdown:")
    print(f"  {'Count':>5} {'n':>5} {'Cont%':>7} {'Cum≤':>7} {'Cum>':>7} {'Delta':>7}")
    print("  " + "-" * 45)
    for ic in sorted(xau_imp['bucket_rates'].keys()):
        br = xau_imp['bucket_rates'][ic]
        cr = xau_imp['cum_rates'].get(ic, {})
        le_rate = cr.get('le_rate', '-')
        gt_rate = cr.get('gt_rate', '-')
        delta = cr.get('delta', '-')
        print(f"  {ic:>5} {br['n']:>5} {br['rate']:>6.1f}% "
              f"{le_rate if isinstance(le_rate, str) else f'{le_rate:.1f}%':>7} "
              f"{gt_rate if isinstance(gt_rate, str) else f'{gt_rate:.1f}%':>7} "
              f"{delta if isinstance(delta, str) else f'{delta:.1f}':>7}")

    # Run other instruments
    print(f"\n--- OTHER INSTRUMENTS ---")
    for sym in INSTRUMENTS:
        if sym == 'XAUUSD':
            continue
        print(f"\nProcessing {sym}...")
        r = process_with_impulse(sym)
        if r is None:
            print(f"  Skipped — no data")
            continue
        imp = analyze_impulse_distribution(r)
        all_results[sym] = r
        all_impulse[sym] = imp

        s = imp['stats']
        print(f"  Distribution: min={s['min']}, p25={s['p25']}, median={s['median']}, "
              f"p75={s['p75']}, max={s['max']}")
        print(f"  ≤ median: {imp['cont_le_median']}%, > median: {imp['cont_gt_median']}%, "
              f"delta: {imp['median_delta']}pp")
        if imp['cliff_threshold']:
            ct = imp['cliff_threshold']
            cr = imp['cum_rates'][ct]
            print(f"  Cliff at ≤{ct}: {cr['le_rate']}% vs >{ct}: {cr['gt_rate']}% → {cr['delta']}pp")
        else:
            print(f"  No clear cliff")
        print(f"  FVG: {imp['fvg_pct']}% create FVG, delta: {imp['fvg_delta']}pp")

    # Summary table
    print(f"\n{'='*70}")
    print("IMPULSE CANDLE DISTRIBUTION SUMMARY")
    print(f"{'='*70}")
    print(f"\n{'Instrument':<14} {'Min':>4} {'P25':>4} {'Med':>4} {'P75':>4} {'Max':>4} "
          f"{'Cont≤Med':>9} {'Cont>Med':>9} {'Cliff':>7} {'Cliff Δ':>8}")
    print("-" * 85)
    for sym in INSTRUMENTS:
        if sym not in all_impulse:
            continue
        imp = all_impulse[sym]
        s = imp['stats']
        cliff = f"≤{imp['cliff_threshold']}" if imp['cliff_threshold'] else "none"
        cliff_d = f"{imp['cliff_delta']:.1f}pp" if imp['cliff_threshold'] else "-"
        print(f"{sym:<14} {s['min']:>4} {s['p25']:>4} {s['median']:>4} {s['p75']:>4} {s['max']:>4} "
              f"{imp['cont_le_median']:>8.1f}% {imp['cont_gt_median']:>8.1f}% "
              f"{cliff:>7} {cliff_d:>8}")

    # FVG table
    print(f"\n{'Instrument':<14} {'FVG%':>6} {'FVG Yes':>8} {'FVG No':>8} {'FVG Δ':>7}")
    print("-" * 50)
    for sym in INSTRUMENTS:
        if sym not in all_impulse:
            continue
        imp = all_impulse[sym]
        print(f"{sym:<14} {imp['fvg_pct']:>5.1f}% {imp['fvg_yes_cont']:>7.1f}% "
              f"{imp['fvg_no_cont']:>7.1f}% {imp['fvg_delta']:>6.1f}pp")

    # Prompt guidance
    print(f"\n{'='*70}")
    print("PROMPT IMPULSE GUIDANCE")
    print(f"{'='*70}")
    guidance = {}
    for sym in INSTRUMENTS:
        if sym not in all_impulse:
            continue
        imp = all_impulse[sym]
        if imp['cliff_threshold'] and imp['cliff_delta'] >= 5:
            ct = imp['cliff_threshold']
            cr = imp['cum_rates'][ct]
            g = f"≤{ct} candles preferred ({cr['le_rate']}% vs {cr['gt_rate']}% at >{ct}, Δ={cr['delta']}pp)"
            guidance[sym] = {'type': 'cliff', 'threshold': ct, 'text': g}
            print(f"  {sym}: {g}")
        elif imp['median_delta'] >= 5:
            med = imp['stats']['median']
            g = f"≤{med} candles preferred ({imp['cont_le_median']}% vs {imp['cont_gt_median']}%, Δ={imp['median_delta']}pp)"
            guidance[sym] = {'type': 'median', 'threshold': med, 'text': g}
            print(f"  {sym}: {g}")
        else:
            g = "No impulse length preference — not predictive on this instrument"
            guidance[sym] = {'type': 'none', 'threshold': None, 'text': g}
            print(f"  {sym}: {g}")

    # ── PART 2: CONFIG VERIFICATION ──

    print(f"\n{'='*70}")
    print("PART 2: CONFIG VERIFICATION")
    print(f"{'='*70}")

    # Check existing configs
    configs = check_configs()
    print(f"\nConfig files found:")
    for path in configs:
        print(f"  {path}")

    # Check for instrument overrides in configs
    instrument_keywords = ['USDJPY', 'GBPUSD', 'US30', 'GBPJPY', 'NZDUSD',
                          'instrument_overrides', 'per_instrument', 'instruments']
    print(f"\nInstrument override search:")
    config_has_instrument = {}
    for path, content in configs.items():
        for sym in INSTRUMENTS:
            sym_clean = sym.replace('_cash', '')
            if sym_clean in content or sym in content:
                if sym not in config_has_instrument:
                    config_has_instrument[sym] = []
                config_has_instrument[sym].append(path)
                print(f"  {sym} found in {path}")

    for sym in INSTRUMENTS:
        if sym not in config_has_instrument:
            print(f"  {sym}: NOT found in any config")

    # Spread gates
    print(f"\nSpread gates (from extraction_summary.json):")
    spread_gates = get_spread_gates()
    for sym in INSTRUMENTS:
        if sym in spread_gates:
            sg = spread_gates[sym]
            print(f"  {sym}: median={sg['median_spread']}, p90={sg['p90_spread']}, "
                  f"gate={sg['suggested_gate']}")

    # SL minimums from zone heights
    print(f"\nSL minimum estimation (from OB zone heights):")
    sl_estimates = {}
    for sym in INSTRUMENTS:
        if sym in all_results:
            r = all_results[sym]
            mzh = r['median_zone_height']
            p25zh = r['p25_zone_height']
            sl_min = round(p25zh * 0.7, 6)  # 0.7x of P25 zone height
            sl_estimates[sym] = {
                'median_zone_height': mzh,
                'p25_zone_height': p25zh,
                'suggested_sl_min': sl_min,
                'median_atr': r['median_atr'],
            }
            print(f"  {sym}: median_zone={mzh:.5f}, p25_zone={p25zh:.5f}, "
                  f"suggested_SL_min={sl_min:.5f}, ATR={r['median_atr']:.5f}")

    # Config status table
    print(f"\n{'='*70}")
    print("CONFIG STATUS")
    print(f"{'='*70}")

    # Determine recommended KZ windows per instrument
    kz_recommendations = {
        'XAUUSD': 'London+NY',
        'USDJPY': 'Tokyo+London+NY',
        'GBPUSD': 'London+NY',
        'US30_cash': 'London+NY(cash)',
        'GBPJPY': 'Tokyo+London+NY',
        'NZDUSD': 'Tokyo+London',
    }

    print(f"\n{'Instrument':<14} {'Config?':>8} {'SL Min':>12} {'Spread Gate':>12} "
          f"{'KZ Windows':<20} {'Action':<15}")
    print("-" * 85)

    config_status = {}
    for sym in INSTRUMENTS:
        exists = 'Y' if sym in config_has_instrument else 'N'
        sl = sl_estimates.get(sym, {}).get('suggested_sl_min', '?')
        sg = spread_gates.get(sym, {}).get('suggested_gate', '?')
        kz = kz_recommendations.get(sym, '?')
        action = 'verify' if exists == 'Y' else 'CREATE'

        if isinstance(sl, float):
            sl_str = f"{sl:.5f}"
        else:
            sl_str = str(sl)
        if isinstance(sg, float):
            sg_str = f"{sg:.6f}"
        else:
            sg_str = str(sg)

        print(f"{sym:<14} {exists:>8} {sl_str:>12} {sg_str:>12} {kz:<20} {action:<15}")

        config_status[sym] = {
            'config_exists': exists == 'Y',
            'sl_min': sl,
            'spread_gate': sg,
            'kz_windows': kz,
            'action': action,
        }

    # ── PART 3: FINAL CALIBRATION SHEET ──

    print(f"\n{'='*70}")
    print("BATCH TEST CALIBRATION SHEET")
    print(f"{'='*70}")

    print(f"\n{'Instrument':<14} {'Impulse Guidance':<30} {'KZ':<18} "
          f"{'SL Floor':>10} {'Spr Gate':>10} {'FVG Effect':>11} {'Ready':>6}")
    print("-" * 105)

    calibration_sheet = {}
    for sym in INSTRUMENTS:
        if sym not in all_impulse:
            continue
        g = guidance.get(sym, {})
        imp = all_impulse[sym]
        cs = config_status.get(sym, {})

        impulse_text = g.get('text', 'N/A')[:28]
        kz = kz_recommendations.get(sym, '?')
        sl = cs.get('sl_min', '?')
        sg = cs.get('spread_gate', '?')
        fvg_eff = f"+{imp['fvg_delta']:.0f}pp" if abs(imp['fvg_delta']) >= 3 else "null"
        ready = 'Y' if g.get('type') != 'unknown' else 'N'

        sl_str = f"{sl:.5f}" if isinstance(sl, float) else str(sl)
        sg_str = f"{sg:.6f}" if isinstance(sg, float) else str(sg)

        print(f"{sym:<14} {impulse_text:<30} {kz:<18} {sl_str:>10} {sg_str:>10} {fvg_eff:>11} {ready:>6}")

        calibration_sheet[sym] = {
            'impulse_guidance': g,
            'impulse_stats': all_impulse[sym]['stats'],
            'cliff_threshold': all_impulse[sym].get('cliff_threshold'),
            'cliff_delta': all_impulse[sym].get('cliff_delta'),
            'fvg_effect_pp': imp['fvg_delta'],
            'kz_windows': kz,
            'sl_min': sl,
            'spread_gate': sg,
            'median_zone_height': all_results.get(sym, {}).get('median_zone_height'),
            'median_atr': all_results.get(sym, {}).get('median_atr'),
            'config_exists': cs.get('config_exists', False),
            'action_needed': cs.get('action', 'unknown'),
        }

    # Save
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / 'batch_test_calibration.json', 'w') as f:
        json.dump(calibration_sheet, f, indent=2, default=str)

    # Also save detailed impulse data
    with open(RESULTS_DIR / 'impulse_distributions.json', 'w') as f:
        json.dump(all_impulse, f, indent=2, default=str)

    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f}s")
    print(f"Saved to: {RESULTS_DIR / 'batch_test_calibration.json'}")
    print(f"Saved to: {RESULTS_DIR / 'impulse_distributions.json'}")


if __name__ == '__main__':
    main()
