#!/usr/bin/env python3
"""Phase 6: Per-Record Analyses — retracement, impulse, overlap, FVG deep dive, calendar."""
import json, csv, os, sys, math, warnings
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from scipy import stats as scipy_stats

warnings.filterwarnings('ignore')

BASE = Path('/Users/borr/Documents/trading/gold-agent')
KB = BASE / 'knowledge_base_backtest'
OUT = KB / 'analysis' / 'deep_dive_20260406'
PR = KB / 'analysis' / 'per_record_20260406'

###############################################################################
# Check prerequisites
###############################################################################
ob_xau_file = PR / 'ob_per_record_xauusd.json'
fvg_xau_file = PR / 'fvg_per_record_xauusd.json'
overlap_file = PR / 'framework_date_overlap.json'

print("Prerequisite check:")
for f in [ob_xau_file, fvg_xau_file, overlap_file]:
    print(f"  {f.name}: {'EXISTS' if f.exists() else 'MISSING'}")

# Load per-record data
with open(ob_xau_file) as f:
    ob_records = json.load(f)
print(f"\nOB records: {len(ob_records)}")

with open(fvg_xau_file) as f:
    fvg_records = json.load(f)
print(f"FVG records: {len(fvg_records)}")

with open(overlap_file) as f:
    overlap_data = json.load(f)

# Check calendar
calendar_file = None
for path in [BASE / 'data' / 'economic_calendar.csv',
             BASE / 'data' / 'economic_calendar_export.csv',
             BASE / 'exports' / 'candle_redownload' / 'economic_calendar_export.csv']:
    if path.exists():
        calendar_file = path
        break
print(f"Calendar: {'FOUND at ' + str(calendar_file) if calendar_file else 'NOT FOUND'}")

# Check GBPUSD per-record
gb_ob_file = PR / 'ob_per_record_gbpusd.json'
gb_fvg_file = PR / 'fvg_per_record_gbpusd.json'
print(f"GBPUSD OB: {'EXISTS' if gb_ob_file.exists() else 'MISSING'}")
print(f"GBPUSD FVG: {'EXISTS' if gb_fvg_file.exists() else 'MISSING'}")

###############################################################################
# 6A: Continuous Retracement Depth Curve
###############################################################################
def retracement_curve():
    """Analyze retracement depth vs continuation for OBs."""
    # Filter to retested OBs
    retested = [r for r in ob_records if r.get('retested') in (True, 'true', 'True', 1)]

    if len(retested) < 30:
        return {'insufficient': True, 'n_retested': len(retested)}

    # Get retracement_pct (stored as ratio 0-1, multiply by 100)
    data = []
    for r in retested:
        ret_pct = r.get('retracement_pct')
        if ret_pct is None:
            continue
        ret_pct = float(ret_pct) * 100  # Convert to percentage

        cont = r.get('continuation')  # OB field name confirmed
        if cont is None:
            continue

        cont_val = 1 if cont in (True, 'true', 'True', 1, '1') else 0
        data.append({'ret_pct': ret_pct, 'cont': cont_val, 'set': r.get('period', '')})

    if len(data) < 30:
        return {'insufficient': True, 'n_with_retracement': len(data)}

    # Narrow bins (data compressed to 52-98%)
    bins_def = [(50, 70), (70, 80), (80, 85), (85, 90), (90, 95), (95, 100)]
    bin_results = {}
    for lo, hi in bins_def:
        bin_data = [d for d in data if lo <= d['ret_pct'] < hi]
        if bin_data:
            n = len(bin_data)
            cr = sum(d['cont'] for d in bin_data) / n
            bin_results[f'{lo}-{hi}%'] = {'n': n, 'cont_rate': round(cr, 4)}

    # Median split (91.4%)
    median_split = 91.4
    below = [d for d in data if d['ret_pct'] < median_split]
    above = [d for d in data if d['ret_pct'] >= median_split]

    median_result = {}
    if below and above:
        below_cr = sum(d['cont'] for d in below) / len(below)
        above_cr = sum(d['cont'] for d in above) / len(above)
        median_result = {
            'below_median': {'n': len(below), 'cont_rate': round(below_cr, 4)},
            'above_median': {'n': len(above), 'cont_rate': round(above_cr, 4)},
            'difference': round(above_cr - below_cr, 4),
        }

        # Fisher exact
        a = sum(d['cont'] for d in below)
        b = len(below) - a
        c = sum(d['cont'] for d in above)
        d_val = len(above) - c
        _, p = scipy_stats.fisher_exact([[a, b], [c, d_val]])
        median_result['fisher_p'] = round(p, 4)

    # Chi-squared across bins
    bin_groups = []
    for lo, hi in bins_def:
        bd = [d for d in data if lo <= d['ret_pct'] < hi]
        if len(bd) >= 5:
            bin_groups.append([sum(d_['cont'] for d_ in bd), len(bd) - sum(d_['cont'] for d_ in bd)])

    chi_p = None
    if len(bin_groups) >= 2:
        try:
            chi2, p, _, _ = scipy_stats.chi2_contingency(bin_groups)
            chi_p = round(p, 4)
        except:
            chi_p = None

    # Discovery vs validation
    disc_data = [d for d in data if d['set'] == 'disc']
    val_data = [d for d in data if d['set'] == 'val']

    disc_val = {}
    for label, subset in [('discovery', disc_data), ('validation', val_data)]:
        if subset:
            disc_val[label] = {
                'n': len(subset),
                'cont_rate': round(sum(d['cont'] for d in subset) / len(subset), 4),
                'mean_ret_pct': round(np.mean([d['ret_pct'] for d in subset]), 1),
            }

    return {
        'n_retested': len(retested),
        'n_with_data': len(data),
        'overall_cont_rate': round(sum(d['cont'] for d in data) / len(data), 4),
        'mean_retracement_pct': round(np.mean([d['ret_pct'] for d in data]), 1),
        'median_retracement_pct': round(float(np.median([d['ret_pct'] for d in data])), 1),
        'bin_results': bin_results,
        'median_split': median_result,
        'chi_squared_across_bins': chi_p,
        'disc_val': disc_val,
    }

###############################################################################
# 6B: Impulse Leg Character
###############################################################################
def impulse_character():
    """Check if impulse fields exist and analyze."""
    impulse_fields = ['impulse_candle_count', 'impulse_atr_multiple',
                      'impulse_body_ratio_avg', 'impulse_created_fvg']

    # Check which fields exist
    sample = ob_records[0] if ob_records else {}
    available = [f for f in impulse_fields if f in sample]

    if not available:
        return {'status': 'Impulse data not available — OB extraction did not include impulse reconstruction.',
                'checked_fields': impulse_fields,
                'available_fields': list(sample.keys())[:30]}

    results = {}
    for field in available:
        data = [(r[field], r.get('continuation', r.get('cont', r.get('continued'))))
                for r in ob_records if r.get(field) is not None]
        if len(data) < 30:
            results[field] = {'insufficient': True, 'n': len(data)}
            continue

        # Parse continuation
        parsed = []
        for v, c in data:
            if c is None:
                continue
            c_val = 1 if (isinstance(c, bool) and c) or str(c).lower() in ('true', 'win', '1') else 0
            parsed.append((v, c_val))

        if len(parsed) < 30:
            results[field] = {'insufficient': True, 'n': len(parsed)}
            continue

        # Analyze based on type
        unique = set(v for v, _ in parsed)
        if len(unique) <= 5:
            groups = defaultdict(list)
            for v, t in parsed:
                groups[str(v)].append(t)
            rates = {k: {'n': len(v), 'cont_rate': round(sum(v)/len(v), 4)} for k, v in groups.items()}
            results[field] = {'type': 'categorical', 'rates': rates}
        else:
            x = np.array([float(v) for v, _ in parsed])
            y = np.array([t for _, t in parsed])
            r_pb, p = scipy_stats.pointbiserialr(y, x)
            results[field] = {'type': 'continuous', 'correlation': round(float(r_pb), 4), 'p_value': round(float(p), 6)}

    return results

###############################################################################
# 6C: FVG/OB Date Overlap
###############################################################################
def framework_overlap():
    """Interpret the pre-computed overlap data."""
    result = {
        'raw_overlap': overlap_data,
    }

    # Extract key numbers from actual structure
    date_ovl = overlap_data.get('date_overlap', {})
    n_fvg = date_ovl.get('fvg_fill_only_kz', 0)
    n_ob = date_ovl.get('ob_retest_only_kz', 0)
    n_both = date_ovl.get('both_ob_retest_and_fvg_fill_kz', 0)
    n_neither = date_ovl.get('neither', 0)
    total = date_ovl.get('total_trading_dates', n_fvg + n_ob + n_both + n_neither)
    fvg_additive_pct = date_ovl.get('fvg_additive_pct', 0)

    result['summary'] = {
        'fvg_only_dates': n_fvg,
        'ob_only_dates': n_ob,
        'both_dates': n_both,
        'neither_dates': n_neither,
        'total_dates': total,
    }

    # Frequency multiplier
    if n_ob > 0:
        additional_pct = n_fvg / (n_ob + n_both) * 100 if (n_ob + n_both) > 0 else 0
        result['frequency_analysis'] = {
            'ob_dates': n_ob + n_both,
            'fvg_additional_dates': n_fvg,
            'frequency_increase_pct': round(additional_pct, 1),
            'increases_monthly_trades_gt_30pct': additional_pct > 30,
        }

        # Monthly frequency estimate (total dates / months)
        total_trading_months = total / 21  # ~21 trading days/month
        ob_monthly = (n_ob + n_both) / total_trading_months if total_trading_months > 0 else 0
        fvg_additional_monthly = n_fvg / total_trading_months if total_trading_months > 0 else 0

        result['frequency_analysis']['ob_trades_per_month_est'] = round(ob_monthly, 1)
        result['frequency_analysis']['fvg_additional_per_month_est'] = round(fvg_additional_monthly, 1)

    return result

###############################################################################
# 6D: FVG Per-Record Deep Dive
###############################################################################
def fvg_deep_dive():
    """Analyze FVG per-record data in detail."""
    if not fvg_records:
        return {'error': 'No FVG records'}

    # Check available fields
    sample = fvg_records[0]
    print(f"  FVG record keys: {list(sample.keys())[:20]}")

    # Parse continuation — FVG uses 'continuation_3h' field
    data = []
    for r in fvg_records:
        cont = r.get('continuation_3h')
        if cont is None:
            continue
        c_val = 1 if cont in (True, 'true', 'True', 1, '1') else 0

        data.append({
            'cont': c_val,
            'fill_pct': r.get('fill_percentage'),
            'max_fill': r.get('max_fill_depth'),
            'fvg_size': r.get('fvg_size'),
            'candles_to_fill': None,  # fill_time is a timestamp, not a count
            'set': r.get('period', ''),
        })

    overall_cr = sum(d['cont'] for d in data) / len(data) if data else 0
    print(f"  Overall FVG cont rate: {overall_cr:.3f}")

    result = {
        'n_records': len(data),
        'overall_cont_rate': round(overall_cr, 4),
    }

    # Fill depth as continuous variable
    fill_data = [(float(d['fill_pct']), d['cont']) for d in data
                 if d['fill_pct'] is not None]
    if fill_data:
        # Bins: 0-10, 10-20, ..., 90-100, 100+
        bins_def = [(0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5),
                    (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 1.0), (1.0, 2.01)]
        fill_bins = {}
        for lo, hi in bins_def:
            bd = [(f, c) for f, c in fill_data if lo <= f < hi]
            if bd:
                fill_bins[f'{int(lo*100)}-{int(hi*100)}%'] = {
                    'n': len(bd),
                    'cont_rate': round(sum(c for _, c in bd) / len(bd), 4),
                }
        result['fill_depth_bins'] = fill_bins

    # FVG size analysis
    size_data = [(float(d['fvg_size']), d['cont']) for d in data
                 if d.get('fvg_size') is not None]
    if len(size_data) > 30:
        x = np.array([s for s, _ in size_data])
        y = np.array([c for _, c in size_data])
        quints = np.percentile(x, [20, 40, 60, 80])
        bins = np.digitize(x, quints)
        size_quintiles = {}
        for q in range(5):
            mask = bins == q
            if sum(mask) > 0:
                size_quintiles[f'Q{q+1}'] = {
                    'n': int(sum(mask)),
                    'cont_rate': round(float(y[mask].mean()), 4),
                    'size_range': f"{x[mask].min():.2f} to {x[mask].max():.2f}",
                }
        result['fvg_size_quintiles'] = size_quintiles

        r_pb, p = scipy_stats.pointbiserialr(y, x)
        result['fvg_size_correlation'] = round(float(r_pb), 4)
        result['fvg_size_p_value'] = round(float(p), 6)

    # Time-to-fill
    fill_time_data = [(float(d['candles_to_fill']), d['cont']) for d in data
                      if d.get('candles_to_fill') is not None]
    if len(fill_time_data) > 30:
        x = np.array([t for t, _ in fill_time_data])
        y = np.array([c for _, c in fill_time_data])
        r_pb, p = scipy_stats.pointbiserialr(y, x)
        result['time_to_fill'] = {
            'correlation': round(float(r_pb), 4),
            'p_value': round(float(p), 6),
            'mean_candles': round(float(np.mean(x)), 1),
            'median_candles': round(float(np.median(x)), 1),
        }

    # Disc/val split
    disc = [d for d in data if d['set'] == 'disc']
    val = [d for d in data if d['set'] == 'val']
    if disc and val:
        result['disc_val'] = {
            'discovery': {'n': len(disc), 'cont_rate': round(sum(d['cont'] for d in disc)/len(disc), 4)},
            'validation': {'n': len(val), 'cont_rate': round(sum(d['cont'] for d in val)/len(val), 4)},
        }

    return result

###############################################################################
# 6E: Economic Calendar
###############################################################################
def calendar_analysis():
    """Tag trades with high-impact economic events."""
    if calendar_file is None:
        return {'status': 'Calendar data not available — requires MQL5 export from Windows.'}

    # Load calendar
    with open(calendar_file) as f:
        reader = csv.DictReader(f)
        cal_fields = reader.fieldnames
        cal_events = list(reader)

    print(f"  Calendar: {len(cal_events)} events, fields: {cal_fields[:10]}")

    # Filter high impact
    high_impact = []
    for e in cal_events:
        impact = e.get('impact', e.get('importance', e.get('Impact', ''))).lower()
        if 'high' in impact or impact == '3':
            currency = e.get('currency', e.get('Currency', ''))
            if currency.upper() in ('USD', 'GBP'):
                high_impact.append(e)

    if not high_impact:
        return {'status': f'No high-impact USD/GBP events found in calendar ({len(cal_events)} total events)',
                'fields': cal_fields}

    # Load enriched trades
    with open(OUT / 'trade_index_enriched.json') as f:
        trades_data = json.load(f)
    trades = trades_data['trades']

    # Tag trades
    event_trades = 0
    no_event_trades = 0
    event_wins = 0
    no_event_wins = 0
    event_r = []
    no_event_r = []

    for t in trades:
        entry = t.get('entry_time', '')
        if not entry:
            continue

        try:
            et = datetime.fromisoformat(entry.replace('Z', '').replace('+00:00', ''))
        except:
            continue

        near_event = False
        for e in high_impact:
            # Parse event time — format is date + time_utc (HH:MM)
            event_date = e.get('date', '')
            event_time_str = e.get('time_utc', '')
            if not event_date or not event_time_str:
                continue
            try:
                evt = datetime.fromisoformat(f"{event_date}T{event_time_str}:00")
            except:
                continue

            # Within 4 hours before or 2 hours after
            diff_min = (et - evt).total_seconds() / 60
            if -240 <= diff_min <= 120:
                near_event = True
                break

        is_win = t['outcome'] == 'WIN'
        if near_event:
            event_trades += 1
            if is_win: event_wins += 1
            event_r.append(t['r_multiple'])
        else:
            no_event_trades += 1
            if is_win: no_event_wins += 1
            no_event_r.append(t['r_multiple'])

    result = {
        'n_high_impact_events': len(high_impact),
        'trades_near_events': event_trades,
        'trades_no_events': no_event_trades,
    }

    if event_trades > 0 and no_event_trades > 0:
        event_wr = event_wins / event_trades
        no_event_wr = no_event_wins / no_event_trades

        table = [[event_wins, event_trades - event_wins],
                 [no_event_wins, no_event_trades - no_event_wins]]
        _, p = scipy_stats.fisher_exact(table)

        result['event_near'] = {
            'n': event_trades,
            'win_rate': round(event_wr, 4),
            'mean_r': round(np.mean(event_r), 4),
        }
        result['no_event'] = {
            'n': no_event_trades,
            'win_rate': round(no_event_wr, 4),
            'mean_r': round(np.mean(no_event_r), 4),
        }
        result['fisher_p'] = round(p, 4)

    return result

###############################################################################
# 6F: GBPUSD Per-Record
###############################################################################
def gbpusd_analysis():
    """Analyze GBPUSD per-record data if available."""
    if not gb_fvg_file.exists():
        return {'status': 'GBPUSD per-record data exists but GBPUSD M15 only has 700 rows (2026 only) — insufficient for historical analysis'}

    with open(gb_fvg_file) as f:
        gb_fvg = json.load(f)

    # Compare XAUUSD vs GBPUSD FVG characteristics
    xau_cont = sum(1 for r in fvg_records if r.get('continuation_3h') in (True, 'true', 'True', 1)) / len(fvg_records) if fvg_records else 0
    gb_cont = sum(1 for r in gb_fvg if r.get('continuation_3h') in (True, 'true', 'True', 1)) / len(gb_fvg) if gb_fvg else 0

    return {
        'xauusd_fvg_n': len(fvg_records),
        'xauusd_fvg_cont_rate': round(xau_cont, 4),
        'gbpusd_fvg_n': len(gb_fvg),
        'gbpusd_fvg_cont_rate': round(gb_cont, 4),
        'difference_pp': round((xau_cont - gb_cont) * 100, 1),
    }

###############################################################################
# Main
###############################################################################
if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 6: PER-RECORD ANALYSES")
    print("=" * 60)

    # 6A
    print("\n--- 6A: Retracement Depth Curve ---")
    ret = retracement_curve()
    print(f"  n={ret.get('n_with_data', 'N/A')}, overall cont={ret.get('overall_cont_rate', 'N/A')}")
    if 'bin_results' in ret:
        for k, v in ret['bin_results'].items():
            print(f"    {k}: n={v['n']}, rate={v['cont_rate']}")
    if 'median_split' in ret:
        ms = ret['median_split']
        print(f"  Median split p: {ms.get('fisher_p')}")
    print(f"  Chi-squared bins p: {ret.get('chi_squared_across_bins')}")

    # 6B
    print("\n--- 6B: Impulse Character ---")
    imp = impulse_character()
    print(f"  {imp.get('status', 'Fields found: ' + str(list(imp.keys())))}")

    # 6C
    print("\n--- 6C: Framework Overlap ---")
    ovlp = framework_overlap()
    if 'summary' in ovlp:
        s = ovlp['summary']
        print(f"  FVG-only: {s['fvg_only_dates']}, OB-only: {s['ob_only_dates']}, Both: {s['both_dates']}, Neither: {s['neither_dates']}")
    if 'frequency_analysis' in ovlp:
        fa = ovlp['frequency_analysis']
        print(f"  FVG adds {fa['frequency_increase_pct']}% more trading dates")
        print(f"  >30% increase: {'YES' if fa['increases_monthly_trades_gt_30pct'] else 'NO'}")

    # 6D
    print("\n--- 6D: FVG Deep Dive ---")
    fvg_dd = fvg_deep_dive()
    print(f"  n={fvg_dd.get('n_records')}, cont={fvg_dd.get('overall_cont_rate')}")
    if 'fill_depth_bins' in fvg_dd:
        for k, v in fvg_dd['fill_depth_bins'].items():
            print(f"    Fill {k}: n={v['n']}, rate={v['cont_rate']}")
    if 'fvg_size_p_value' in fvg_dd:
        print(f"  FVG size p: {fvg_dd['fvg_size_p_value']}")
    if 'time_to_fill' in fvg_dd:
        print(f"  Time-to-fill: corr={fvg_dd['time_to_fill']['correlation']}, p={fvg_dd['time_to_fill']['p_value']}")

    # 6E
    print("\n--- 6E: Calendar Analysis ---")
    cal = calendar_analysis()
    if 'event_near' in cal:
        print(f"  Near event: n={cal['event_near']['n']}, WR={cal['event_near']['win_rate']}")
        print(f"  No event: n={cal['no_event']['n']}, WR={cal['no_event']['win_rate']}")
        print(f"  Fisher p: {cal['fisher_p']}")
    else:
        print(f"  {cal.get('status', 'No data')}")

    # 6F
    print("\n--- 6F: GBPUSD ---")
    gb = gbpusd_analysis()
    if 'xauusd_fvg_cont_rate' in gb:
        print(f"  XAUUSD FVG: {gb['xauusd_fvg_cont_rate']:.1%} (n={gb['xauusd_fvg_n']})")
        print(f"  GBPUSD FVG: {gb['gbpusd_fvg_cont_rate']:.1%} (n={gb['gbpusd_fvg_n']})")
        print(f"  Gap: {gb['difference_pp']}pp")
    else:
        print(f"  {gb.get('status', 'N/A')}")

    # Save all
    all_results = {
        'retracement_curve': ret,
        'impulse_character': imp,
        'framework_overlap': ovlp,
        'fvg_deep_dive': fvg_dd,
        'calendar_analysis': cal,
        'gbpusd_analysis': gb,
    }

    with open(OUT / 'phase6_per_record_20260406.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    # Individual outputs
    with open(OUT / 'impulse_character_20260406.json', 'w') as f:
        json.dump(imp, f, indent=2, default=str)
    with open(OUT / 'framework_overlap_20260406.json', 'w') as f:
        json.dump(ovlp, f, indent=2, default=str)
    with open(OUT / 'fvg_deep_dive_20260406.json', 'w') as f:
        json.dump(fvg_dd, f, indent=2, default=str)
    with open(OUT / 'calendar_analysis_20260406.json', 'w') as f:
        json.dump(cal, f, indent=2, default=str)
    with open(OUT / 'gbpusd_analysis_20260406.json', 'w') as f:
        json.dump(gb, f, indent=2, default=str)

    # Markdown reports
    md = f"""# Phase 6: Per-Record Analyses — {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 6A: Retracement Depth Curve
- N retested: {ret.get('n_retested')} | N with data: {ret.get('n_with_data')}
- Overall continuation rate: {ret.get('overall_cont_rate')}
- Mean retracement: {ret.get('mean_retracement_pct')}% | Median: {ret.get('median_retracement_pct')}%

### Bin Results
| Bin | N | Cont Rate |
|-----|---|-----------|
"""
    if 'bin_results' in ret:
        for k, v in ret['bin_results'].items():
            md += f"| {k} | {v['n']} | {v['cont_rate']} |\n"

    md += f"""
Chi-squared across bins: p={ret.get('chi_squared_across_bins')}
Median split Fisher p: {ret.get('median_split', {}).get('fisher_p')}

## 6B: Impulse Character
{json.dumps(imp, indent=2, default=str)[:500]}

## 6C: Framework Overlap
"""
    if 'summary' in ovlp:
        s = ovlp['summary']
        md += f"- FVG-only dates: {s['fvg_only_dates']}\n- OB-only dates: {s['ob_only_dates']}\n- Both: {s['both_dates']}\n- Neither: {s['neither_dates']}\n"
    if 'frequency_analysis' in ovlp:
        fa = ovlp['frequency_analysis']
        md += f"- FVG increases trading frequency by {fa['frequency_increase_pct']}%\n"
        md += f"- >30% increase: {'YES — strong recommendation to implement' if fa['increases_monthly_trades_gt_30pct'] else 'NO'}\n"

    md += f"""
## 6D: FVG Deep Dive
- Records: {fvg_dd.get('n_records')} | Overall cont: {fvg_dd.get('overall_cont_rate')}
"""
    if 'fill_depth_bins' in fvg_dd:
        md += "\n### Fill Depth Bins\n| Bin | N | Cont Rate |\n|-----|---|----------|\n"
        for k, v in fvg_dd['fill_depth_bins'].items():
            md += f"| {k} | {v['n']} | {v['cont_rate']} |\n"

    if 'fvg_size_quintiles' in fvg_dd:
        md += "\n### FVG Size Quintiles\n| Q | N | Cont Rate | Size Range |\n|---|---|-----------|------------|\n"
        for k, v in fvg_dd['fvg_size_quintiles'].items():
            md += f"| {k} | {v['n']} | {v['cont_rate']} | {v.get('size_range', '')} |\n"

    md += f"""
## 6E: Calendar Analysis
"""
    if 'event_near' in cal:
        md += f"- Near high-impact event: n={cal['event_near']['n']}, WR={cal['event_near']['win_rate']:.1%}, mean R={cal['event_near']['mean_r']}\n"
        md += f"- No event nearby: n={cal['no_event']['n']}, WR={cal['no_event']['win_rate']:.1%}, mean R={cal['no_event']['mean_r']}\n"
        md += f"- Fisher exact p: {cal['fisher_p']}\n"
    else:
        md += f"Status: {cal.get('status', 'N/A')}\n"

    md += f"""
## 6F: GBPUSD Analysis
"""
    if 'xauusd_fvg_cont_rate' in gb:
        md += f"- XAUUSD FVG cont: {gb['xauusd_fvg_cont_rate']:.1%} (n={gb['xauusd_fvg_n']})\n"
        md += f"- GBPUSD FVG cont: {gb['gbpusd_fvg_cont_rate']:.1%} (n={gb['gbpusd_fvg_n']})\n"
        md += f"- Gap: {gb['difference_pp']}pp\n"

    with open(OUT / 'impulse_character_20260406.md', 'w') as f:
        f.write(md)
    with open(OUT / 'framework_overlap_20260406.md', 'w') as f:
        f.write(md)
    with open(OUT / 'fvg_deep_dive_20260406.md', 'w') as f:
        f.write(md)

    print("\nPhase 6 complete.")
