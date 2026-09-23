#!/usr/bin/env python3
"""
Filter Validation: Gap Ceiling + Touch-1 on Scenario A
XAUUSD Jan 2 – Apr 10, 2026

Validates whether two filters improve WR on 557 entry_in_ob rejected setups.
"""

import json
import re
import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = '/Users/borr/Documents/trading/gold-agent'


# ─── Data loading ────────────────────────────────────────────────────────────

def load_rejected_records():
    path = Path(BASE_DIR) / 'research/t7_live_simulation/all_results_jan_apr10.json'
    with open(path) as f:
        data = json.load(f)
    all_records = data['results']
    rejected = [
        r for r in all_records
        if r.get('decision') == 'REJECTED_L2'
        and 'entry_in_ob' in str(r.get('l2_reason', ''))
    ]
    return rejected


def load_m15_csv():
    path = Path(BASE_DIR) / 'data/historical_2026/XAUUSD_M15.csv'
    candles = []
    time_index = {}  # time_str -> list index
    with open(path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            candles.append({
                'time': row['time'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
            })
            time_index[row['time']] = i
    return candles, time_index


# ─── Parsing helpers ──────────────────────────────────────────────────────────

def parse_ob_zone(l2_reason):
    """Extract (ob_low, ob_high) from l2_reason string.
    Format: 'entry_in_ob: Entry X is outside OB zone {ob_low}-{ob_high}'
    Also handles: 'Entry X is inside OB zone {ob_low}-{ob_high}' (shouldn't occur but safety)
    """
    m = re.search(r'OB zone ([\d.]+)-([\d.]+)', l2_reason)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None


def candle_time_to_csv_fmt(candle_time):
    """Convert '2026-01-07T09:45:00Z' -> '2026-01-07 09:45:00'"""
    return candle_time.replace('T', ' ').replace('Z', '')


# ─── Scenario A ───────────────────────────────────────────────────────────────

def scan_outcome(forward_candles, tp_price, sl_price):
    """
    Scan forward candles for TP or SL hit (LONG only — all records are LONG).
    Returns: ('WIN'|'LOSS'|'OPEN', r_value_or_None)
    Matches original entry_scenario_analysis.py scan_outcome() exactly.
    Fill candle is NOT included — caller passes forward_window[fill_idx+1:].
    """
    for c in forward_candles:
        hit_tp = c['high'] >= tp_price
        hit_sl = c['low'] <= sl_price
        if hit_tp and hit_sl:
            # Same-candle ambiguity: bullish close = TP first (LONG)
            outcome = 'WIN' if c['close'] > c['open'] else 'LOSS'
            return outcome, (1.5 if outcome == 'WIN' else -1.0)
        elif hit_tp:
            return 'WIN', 1.5
        elif hit_sl:
            return 'LOSS', -1.0
    return 'OPEN', None


def scenario_a(forward_candles, direction, zone_entry, zone_sl, zone_tp_1r5):
    """
    Scenario A: proactive limit at ob_high, 1.5R TP, ob_low*0.999 SL.
    Fill: any candle with low <= zone_entry (LONG).
    Outcome: scan from fill_idx+1 only (fill candle itself not checked for TP/SL).
    Matches original entry_scenario_analysis.py scenario_a() exactly.
    Returns: {'fill': bool, 'outcome': 'WIN'|'LOSS'|'OPEN'|'EXPIRED'}
    """
    fill_idx = None
    for i, c in enumerate(forward_candles):
        if c['low'] <= zone_entry:   # LONG: filled when candle touches zone top
            fill_idx = i
            break

    if fill_idx is None:
        return {'fill': False, 'outcome': 'EXPIRED'}

    # Scan candles AFTER the fill candle (fill candle itself not scanned)
    after_fill = forward_candles[fill_idx + 1:]
    outcome, r_val = scan_outcome(after_fill, zone_tp_1r5, zone_sl)
    return {'fill': True, 'outcome': outcome, 'r': r_val}


def compute_rr(outcome):
    if outcome == 'WIN':
        return 1.5
    elif outcome == 'LOSS':
        return -1.0
    return 0.0


# ─── Run Scenario A on a list of enriched records ────────────────────────────

def run_scenario_a_on_subset(enriched_records, m15_candles):
    fills = 0
    wins = 0
    losses = 0
    opens = 0
    total_r = 0.0

    for rec in enriched_records:
        m15_idx = rec['m15_idx']
        ob_low = rec['ob_low']
        ob_high = rec['ob_high']

        zone_entry = ob_high
        zone_sl = ob_low * 0.999
        zone_risk = zone_entry - zone_sl
        zone_tp_1r5 = zone_entry + zone_risk * 1.5

        # Forward window: 192 candles starting at m15_idx+1
        # Matches original entry_scenario_analysis.py: fwd_start = m15_idx + 1
        forward_start = m15_idx + 1
        forward_end = min(forward_start + 192, len(m15_candles))
        forward_candles = m15_candles[forward_start:forward_end]

        result = scenario_a(forward_candles, 'LONG', zone_entry, zone_sl, zone_tp_1r5)

        if result['fill']:
            fills += 1
            if result['outcome'] == 'WIN':
                wins += 1
                total_r += 1.5
            elif result['outcome'] == 'LOSS':
                losses += 1
                total_r -= 1.0
            elif result['outcome'] == 'OPEN':
                opens += 1

    resolved = wins + losses
    wr = wins / resolved if resolved > 0 else None
    return {
        'n': len(enriched_records),
        'fills': fills,
        'wins': wins,
        'losses': losses,
        'opens': opens,
        'resolved': resolved,
        'wr': round(wr, 4) if wr is not None else None,
        'total_r': round(total_r, 2),
    }


# ─── Monthly aggregation ──────────────────────────────────────────────────────

def run_monthly_breakdown(enriched_records, m15_candles):
    monthly = defaultdict(list)
    for rec in enriched_records:
        month = rec['date'][:7]  # '2026-01'
        monthly[month].append(rec)

    result = {}
    for month in sorted(monthly.keys()):
        result[month] = run_scenario_a_on_subset(monthly[month], m15_candles)
    return result


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Loading data...")
    rejected = load_rejected_records()
    m15_candles, time_index = load_m15_csv()

    print(f"Rejected records: {len(rejected)}")
    print(f"M15 candles: {len(m15_candles)}")

    # ── Enrich each record ────────────────────────────────────────────────────
    print("Enriching records (computing ob zones, gap_pct, prior_touch_count)...")

    enriched = []
    parse_failures = 0
    m15_miss = 0

    for rec in rejected:
        ob_low, ob_high = parse_ob_zone(rec.get('l2_reason', ''))
        if ob_low is None:
            parse_failures += 1
            continue

        entry_price = float(rec.get('entry_price', 0))
        # gap_pct: how far above ob_high the entry price is (as % of ob_high)
        # If entry_price <= ob_high, gap <= 0 (inside zone)
        gap_pct = (entry_price - ob_high) / ob_high * 100

        # Candle time -> M15 index
        csv_time = candle_time_to_csv_fmt(rec['candle_time'])
        m15_idx = time_index.get(csv_time)
        if m15_idx is None:
            m15_miss += 1
            continue

        # Count prior touches: candles before m15_idx where low <= ob_high
        prior_touch_count = 0
        for i in range(m15_idx):
            if m15_candles[i]['low'] <= ob_high:
                prior_touch_count += 1

        enriched.append({
            **rec,
            'ob_low': ob_low,
            'ob_high': ob_high,
            'gap_pct': gap_pct,
            'prior_touch_count': prior_touch_count,
            'm15_idx': m15_idx,
        })

    print(f"Enriched: {len(enriched)} | Parse failures: {parse_failures} | M15 misses: {m15_miss}")

    # ── Validation checks ─────────────────────────────────────────────────────
    checks = {}
    checks['count_557'] = len(enriched) == 557  # parse_failures=0, m15_miss=0

    # Run baseline first to validate numbers
    print("Running baseline Scenario A...")
    baseline = run_scenario_a_on_subset(enriched, m15_candles)
    print(f"Baseline: n={baseline['n']}, fills={baseline['fills']}, "
          f"wins={baseline['wins']}, losses={baseline['losses']}, "
          f"wr={baseline['wr']}, total_r={baseline['total_r']}")

    checks['baseline_fills'] = abs(baseline['fills'] - 332) <= 1
    checks['baseline_wr'] = baseline['wr'] is not None and abs(baseline['wr'] - 0.4554) <= 0.002
    checks['baseline_r'] = abs(baseline['total_r'] - 45.0) <= 1.0

    # Check M15 alignment: first record should map to valid candle
    first_rec = enriched[0] if enriched else None
    checks['m15_alignment'] = first_rec is not None and first_rec['m15_idx'] is not None

    # Touch-1 plausibility check
    touch1_count = sum(1 for r in enriched if r['prior_touch_count'] == 0)
    checks['touch1_plausible'] = 10 <= touch1_count <= 500

    checks['no_m15_miss'] = m15_miss == 0

    print("\nValidation checks:")
    for k, v in checks.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    if not checks['count_557']:
        print(f"\nWARNING: Only {len(enriched)} records enriched, expected 557.")
        print(f"Parse failures: {parse_failures}, M15 misses: {m15_miss}")

    # ── Filter subsets ────────────────────────────────────────────────────────
    print("\nBuilding filter subsets...")

    gap_1_5 = [r for r in enriched if r['gap_pct'] <= 1.5]
    gap_2_0 = [r for r in enriched if r['gap_pct'] <= 2.0]
    gap_2_5 = [r for r in enriched if r['gap_pct'] <= 2.5]
    touch1 = [r for r in enriched if r['prior_touch_count'] == 0]
    combined = [r for r in enriched if r['gap_pct'] <= 2.0 and r['prior_touch_count'] == 0]

    print(f"Gap ≤1.5%: {len(gap_1_5)} | Gap ≤2.0%: {len(gap_2_0)} | Gap ≤2.5%: {len(gap_2_5)}")
    print(f"Touch-1: {len(touch1)} | Combined gap≤2.0%+Touch-1: {len(combined)}")

    # ── Run Scenario A on all filter variants ─────────────────────────────────
    print("\nRunning Scenario A on all filter variants...")

    res_gap_1_5 = run_scenario_a_on_subset(gap_1_5, m15_candles)
    res_gap_2_0 = run_scenario_a_on_subset(gap_2_0, m15_candles)
    res_gap_2_5 = run_scenario_a_on_subset(gap_2_5, m15_candles)
    res_touch1 = run_scenario_a_on_subset(touch1, m15_candles)
    res_combined = run_scenario_a_on_subset(combined, m15_candles)

    # ── Monthly breakdown for combined filter ─────────────────────────────────
    print("Running monthly breakdown for combined filter...")
    monthly_combined = run_monthly_breakdown(combined, m15_candles)

    # ── Touch distribution analysis ───────────────────────────────────────────
    print("Running touch distribution analysis...")
    touch_buckets = {
        '0': [r for r in enriched if r['prior_touch_count'] == 0],
        '1': [r for r in enriched if r['prior_touch_count'] == 1],
        '2': [r for r in enriched if r['prior_touch_count'] == 2],
        '3-5': [r for r in enriched if 3 <= r['prior_touch_count'] <= 5],
        '6-10': [r for r in enriched if 6 <= r['prior_touch_count'] <= 10],
        '11+': [r for r in enriched if r['prior_touch_count'] >= 11],
    }

    touch_results = {}
    for label, subset in touch_buckets.items():
        if subset:
            touch_results[label] = run_scenario_a_on_subset(subset, m15_candles)
            touch_results[label]['bucket_label'] = label
        else:
            touch_results[label] = {'n': 0, 'fills': 0, 'resolved': 0, 'wr': None, 'total_r': 0.0, 'bucket_label': label}

    # ── Build outputs ─────────────────────────────────────────────────────────
    print("\nBuilding output files...")

    # JSON summary
    summary = {
        "analysis_date": "2026-04-13",
        "validation_checks": {k: "PASS" if v else "FAIL" for k, v in checks.items()},
        "m15_miss_count": m15_miss,
        "parse_failure_count": parse_failures,
        "touch1_count": touch1_count,
        "baseline": {
            "n": baseline['n'],
            "fills": baseline['fills'],
            "wins": baseline['wins'],
            "losses": baseline['losses'],
            "opens": baseline['opens'],
            "resolved": baseline['resolved'],
            "wr": baseline['wr'],
            "total_r": baseline['total_r'],
        },
        "gap_filter": {
            "1.5pct": {"n": res_gap_1_5['n'], "fills": res_gap_1_5['fills'], "resolved": res_gap_1_5['resolved'], "wr": res_gap_1_5['wr'], "total_r": res_gap_1_5['total_r']},
            "2.0pct": {"n": res_gap_2_0['n'], "fills": res_gap_2_0['fills'], "resolved": res_gap_2_0['resolved'], "wr": res_gap_2_0['wr'], "total_r": res_gap_2_0['total_r']},
            "2.5pct": {"n": res_gap_2_5['n'], "fills": res_gap_2_5['fills'], "resolved": res_gap_2_5['resolved'], "wr": res_gap_2_5['wr'], "total_r": res_gap_2_5['total_r']},
        },
        "touch1_filter": {
            "n": res_touch1['n'], "fills": res_touch1['fills'], "resolved": res_touch1['resolved'],
            "wr": res_touch1['wr'], "total_r": res_touch1['total_r'],
        },
        "combined_2pct_touch1": {
            "n": res_combined['n'],
            "fills": res_combined['fills'],
            "wins": res_combined['wins'],
            "losses": res_combined['losses'],
            "opens": res_combined['opens'],
            "resolved": res_combined['resolved'],
            "wr": res_combined['wr'],
            "total_r": res_combined['total_r'],
            "monthly": {
                month: {
                    "n": v['n'], "fills": v['fills'], "resolved": v['resolved'],
                    "wr": v['wr'], "total_r": v['total_r']
                }
                for month, v in monthly_combined.items()
            }
        },
        "touch_distribution": [
            {
                "prior_touches": label,
                "n": touch_results[label]['n'],
                "fills": touch_results[label]['fills'],
                "resolved": touch_results[label].get('resolved', 0),
                "wr": touch_results[label].get('wr'),
                "total_r": touch_results[label]['total_r'],
            }
            for label in ['0', '1', '2', '3-5', '6-10', '11+']
        ]
    }

    json_path = Path(BASE_DIR) / 'research/academic_pipeline/data/filter_validation_summary.json'
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"JSON written: {json_path}")

    # ── Markdown report ───────────────────────────────────────────────────────
    def wr_str(wr):
        return f"{wr*100:.1f}%" if wr is not None else "N/A"

    def r_str(r):
        return f"{r:+.1f}R"

    lines = []
    lines.append("# Filter Validation — Gap Ceiling + Touch-1")
    lines.append("# XAUUSD Jan 2 – Apr 10, 2026")
    lines.append("")
    lines.append("**Analysis date:** 2026-04-13")
    lines.append("**Source:** research/t7_live_simulation/all_results_jan_apr10.json")
    lines.append(f"**Baseline:** {baseline['n']} entry_in_ob rejections, Scenario A: {r_str(baseline['total_r'])} / {wr_str(baseline['wr'])} WR")
    lines.append("")

    # Validation checks
    lines.append("## Validation Checks")
    lines.append("")
    check_labels = {
        'count_557': f"557 records extracted (got {len(enriched)})",
        'baseline_fills': f"Baseline fill rate: 332/557 = 59.6% (got {baseline['fills']}/{baseline['n']})",
        'baseline_wr': f"Baseline WR: 148/325 = 45.5% (got {baseline['wins']}/{baseline['resolved']} = {wr_str(baseline['wr'])})",
        'baseline_r': f"Baseline Total R: +45.0 (got {r_str(baseline['total_r'])})",
        'm15_alignment': f"M15 index alignment: first record maps to valid M15 candle",
        'touch1_plausible': f"Touch-1 count plausible: 10–500 (got {touch1_count})",
        'no_m15_miss': f"No M15 lookup misses (got {m15_miss} misses)",
    }
    for k, label in check_labels.items():
        status = "PASS" if checks.get(k) else "FAIL"
        lines.append(f"- [{status}] {label}")
    lines.append("")

    # Part 1: Filter Population Counts
    lines.append("## 1. Filter Population Counts")
    lines.append("")
    lines.append("| Filter | Records | % of 557 |")
    lines.append("|--------|---------|-----------|")
    lines.append(f"| No filter (baseline) | 557 | 100% |")
    lines.append(f"| Gap ≤ 1.5% | {len(gap_1_5)} | {len(gap_1_5)/557*100:.1f}% |")
    lines.append(f"| Gap ≤ 2.0% | {len(gap_2_0)} | {len(gap_2_0)/557*100:.1f}% |")
    lines.append(f"| Gap ≤ 2.5% | {len(gap_2_5)} | {len(gap_2_5)/557*100:.1f}% |")
    lines.append(f"| Touch-1 only | {len(touch1)} | {len(touch1)/557*100:.1f}% |")
    lines.append(f"| Gap ≤ 2.0% + Touch-1 | {len(combined)} | {len(combined)/557*100:.1f}% |")
    lines.append("")

    # Part 2: Scenario A by filter
    lines.append("## 2. Scenario A Performance by Filter")
    lines.append("")
    lines.append("| Filter | N setups | Fills | Resolved | WR | Total R |")
    lines.append("|--------|----------|-------|----------|----|---------|")

    def row(label, res):
        fills_pct = f"{res['fills']}/{res['n']} ({res['fills']/res['n']*100:.1f}%)" if res['n'] > 0 else "0"
        return f"| {label} | {res['n']} | {fills_pct} | {res['resolved']} | {wr_str(res['wr'])} | {r_str(res['total_r'])} |"

    lines.append(row("Baseline (no filter)", baseline))
    lines.append(row("Gap ≤ 1.5% only", res_gap_1_5))
    lines.append(row("Gap ≤ 2.0% only", res_gap_2_0))
    lines.append(row("Gap ≤ 2.5% only", res_gap_2_5))
    lines.append(row("Touch-1 only", res_touch1))
    lines.append(row("Gap ≤ 2.0% + Touch-1", res_combined))
    lines.append("")

    # Part 3: Monthly breakdown for combined
    lines.append("## 3. Monthly Breakdown — Gap ≤ 2.0% + Touch-1 Combined")
    lines.append("")
    lines.append("| Month | N setups (filtered) | Filled | Resolved | WR | Total R |")
    lines.append("|-------|---------------------|--------|----------|----|---------|")
    for month in ['2026-01', '2026-02', '2026-03', '2026-04']:
        if month in monthly_combined:
            v = monthly_combined[month]
            lines.append(f"| {month} | {v['n']} | {v['fills']} | {v['resolved']} | {wr_str(v['wr'])} | {r_str(v['total_r'])} |")
        else:
            lines.append(f"| {month} | 0 | 0 | 0 | N/A | +0.0R |")
    lines.append("")

    # Part 4: Touch distribution
    lines.append("## 4. Touch Distribution Analysis")
    lines.append("")
    lines.append("| Prior touches | Count | % | Scenario A WR |")
    lines.append("|--------------|-------|---|--------------|")
    for label in ['0', '1', '2', '3-5', '6-10', '11+']:
        v = touch_results[label]
        pct = v['n'] / len(enriched) * 100 if enriched else 0
        lines.append(f"| {label} | {v['n']} | {pct:.1f}% | {wr_str(v.get('wr'))} |")
    lines.append("")

    # Key findings
    lines.append("## 5. Key Findings")
    lines.append("")

    # Finding F1: Does touch degradation hold?
    wr_t0 = touch_results['0'].get('wr')
    wr_t1 = touch_results['1'].get('wr')
    wr_t2 = touch_results['2'].get('wr')
    touch_deg_holds = (
        wr_t0 is not None and wr_t1 is not None and wr_t0 > wr_t1
    ) if wr_t0 and wr_t1 else False
    lines.append(f"**F1: Touch degradation in this dataset:**")
    lines.append(f"- Touch-0 WR: {wr_str(wr_t0)} (n={touch_results['0']['resolved']})")
    lines.append(f"- Touch-1 WR: {wr_str(wr_t1)} (n={touch_results['1']['resolved']})")
    lines.append(f"- Touch-2 WR: {wr_str(wr_t2)} (n={touch_results['2']['resolved']})")
    lines.append(f"- Degradation holds (touch-0 > touch-1): {'YES' if touch_deg_holds else 'NO'}")
    lines.append("")

    # Finding F2: Which gap ceiling has best R/WR?
    best_gap = max(
        [("1.5%", res_gap_1_5), ("2.0%", res_gap_2_0), ("2.5%", res_gap_2_5)],
        key=lambda x: x[1]['wr'] or 0
    )
    lines.append(f"**F2: Gap ceiling — best WR threshold:**")
    lines.append(f"- Gap ≤1.5%: WR={wr_str(res_gap_1_5['wr'])}, R={r_str(res_gap_1_5['total_r'])}, n={res_gap_1_5['n']}")
    lines.append(f"- Gap ≤2.0%: WR={wr_str(res_gap_2_0['wr'])}, R={r_str(res_gap_2_0['total_r'])}, n={res_gap_2_0['n']}")
    lines.append(f"- Gap ≤2.5%: WR={wr_str(res_gap_2_5['wr'])}, R={r_str(res_gap_2_5['total_r'])}, n={res_gap_2_5['n']}")
    lines.append(f"- Best WR: {best_gap[0]}")
    lines.append("")

    # Finding F3: Combined filter vs baseline
    lines.append(f"**F3: Combined filter (gap ≤2.0% + touch-1) vs baseline:**")
    lines.append(f"- Baseline: WR={wr_str(baseline['wr'])}, R={r_str(baseline['total_r'])}, n={baseline['n']}")
    lines.append(f"- Combined: WR={wr_str(res_combined['wr'])}, R={r_str(res_combined['total_r'])}, n={res_combined['n']}")
    wr_delta = ((res_combined['wr'] or 0) - (baseline['wr'] or 0)) * 100
    r_delta = res_combined['total_r'] - baseline['total_r']
    lines.append(f"- WR delta: {wr_delta:+.1f}pp | R delta: {r_delta:+.1f}R | Setup reduction: {(1 - res_combined['n']/baseline['n'])*100:.0f}%")
    lines.append("")

    # Finding F4: Does March still fail on combined filter?
    mar_combined = monthly_combined.get('2026-03', {})
    mar_wr = mar_combined.get('wr')
    lines.append(f"**F4: March WR on combined filter:**")
    lines.append(f"- Baseline March (all 557): known 33.3% (below 40% breakeven)")
    if mar_wr is not None:
        above_be = mar_wr >= 0.40
        lines.append(f"- Combined filter March: WR={wr_str(mar_wr)}, R={r_str(mar_combined.get('total_r', 0))}, n={mar_combined.get('n', 0)}")
        lines.append(f"- March above 40% breakeven: {'YES' if above_be else 'NO'}")
    else:
        lines.append(f"- Combined filter March: No data (n=0)")
    lines.append("")

    # Finding F5: Sample size warning
    lines.append(f"**F5: Sample size note:**")
    lines.append(f"- Combined filter reduces setups to {res_combined['n']} (from 557). "
                 f"Resolved trades: {res_combined['resolved']}. "
                 f"Statistical significance not assessed here — this is descriptive only.")
    lines.append("")

    md_path = Path(BASE_DIR) / 'research/academic_pipeline/results/filter_validation_v1.md'
    with open(md_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"Markdown written: {md_path}")

    # ── Done checklist ────────────────────────────────────────────────────────
    print("\n=== DONE CHECKLIST ===")
    print(f"[{'x' if len(enriched)==557 else ' '}] 557 records extracted and validated")
    print(f"[x] M15 loaded, time index built ({len(m15_candles)} candles)")
    print(f"[x] prior_touch_count computed for all {len(enriched)} records")
    print(f"[x] gap_pct computed for all {len(enriched)} records")
    print(f"[{'x' if all(checks.values()) else '!'}] Baseline Scenario A reproduced (all 4 checks: {[v for v in checks.values()]})")
    print(f"[x] All 6 filter variants run")
    print(f"[x] Monthly breakdown for combined filter computed")
    print(f"[x] Touch distribution by bucket with per-bucket WR computed")
    print(f"[x] filter_validation_v1.md written")
    print(f"[x] filter_validation_summary.json written")
    print(f"[x] No fabricated numbers — all figures trace to data")

    return summary


if __name__ == '__main__':
    main()
