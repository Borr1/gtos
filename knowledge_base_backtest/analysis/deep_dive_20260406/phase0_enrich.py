#!/usr/bin/env python3
"""Phase 0: Data Enrichment — entry times, direction inference, displacement linking."""
import json, csv, os, sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

BASE = Path('/Users/borr/Documents/trading/gold-agent')
KB = BASE / 'knowledge_base_backtest'
KB_LIVE = BASE / 'knowledge_base'
OUT = KB / 'analysis' / 'deep_dive_20260406'

###############################################################################
# 0A: Enrich trade index
###############################################################################
def phase_0a():
    """Extract entry_time, confidence, setup_grade from session files.
    Infer direction from displacement DB or M15 price action."""

    with open(KB_LIVE / 'index' / '_trade_index.json') as f:
        idx = json.load(f)
    trades = idx['trades']

    session_dir = KB / 'sessions'

    enriched = []
    matched = 0
    unmatched = 0

    for t in trades:
        rec = dict(t)
        trade_date = t['date']
        trade_kz = t['kill_zone']
        trade_id_short = t['trade_id']

        # Find matching session file
        session_file = session_dir / f'{trade_date}_session.json'
        entry_time = None
        confidence = None
        setup_grade = None
        ai_reasoning = None

        if session_file.exists():
            with open(session_file) as f:
                sess = json.load(f)

            for ev in sess.get('candle_evaluations', []):
                if ev.get('trade_executed'):
                    # Match by kill_zone if multiple trades on same day
                    ev_kz = ev.get('kill_zone', '')
                    ev_tid = ev.get('trade_id', '')

                    # Check if this evaluation matches our trade
                    if ev_kz == trade_kz or trade_id_short.startswith(ev_tid) or ev_tid in trade_id_short:
                        entry_time = ev.get('candle_time')
                        confidence = ev.get('confidence')
                        setup_grade = ev.get('setup_grade')
                        ai_reasoning = ev.get('reason')
                        matched += 1
                        break
            else:
                # If no break, try looser match - just first trade_executed in matching KZ
                for ev in sess.get('candle_evaluations', []):
                    if ev.get('trade_executed') and ev.get('kill_zone') == trade_kz:
                        entry_time = ev.get('candle_time')
                        confidence = ev.get('confidence')
                        setup_grade = ev.get('setup_grade')
                        ai_reasoning = ev.get('reason')
                        matched += 1
                        break
                else:
                    unmatched += 1
        else:
            unmatched += 1

        rec['entry_time'] = entry_time
        rec['session_confidence'] = confidence
        rec['session_setup_grade'] = setup_grade
        rec['ai_reasoning'] = ai_reasoning if ai_reasoning else None
        rec['direction'] = None  # Will be inferred in 0B

        enriched.append(rec)

    print(f"Phase 0A: {matched}/{len(trades)} trades matched to session files, {unmatched} unmatched")

    # For trades without entry_time, estimate from kill zone
    for rec in enriched:
        if rec['entry_time'] is None:
            date = rec['date']
            kz = rec['kill_zone']
            # Estimate: London opens ~07:00 UTC, NY opens ~13:00 UTC
            if kz == 'london':
                rec['entry_time'] = f"{date}T08:00:00Z"
                rec['entry_time_estimated'] = True
            else:
                rec['entry_time'] = f"{date}T13:30:00Z"
                rec['entry_time_estimated'] = True

    return enriched

###############################################################################
# 0B: Link to displacement DB and infer direction
###############################################################################
def phase_0b(enriched):
    """Link XAUUSD trades to displacement DB. Infer direction from closest displacement."""

    disp_file = KB / 'analysis' / 'XAUUSD_displacement_database_20260403_1003.csv'

    with open(disp_file) as f:
        reader = csv.DictReader(f)
        displacements = list(reader)

    print(f"Displacement DB: {len(displacements)} records")

    # Parse displacement timestamps
    for d in displacements:
        try:
            ts = d['timestamp'].replace('Z', '').replace('+00:00', '')
            d['_ts'] = datetime.fromisoformat(ts)
        except:
            d['_ts'] = None

    # Filter to valid timestamps
    displacements = [d for d in displacements if d['_ts'] is not None]
    print(f"With valid timestamps: {len(displacements)}")

    linked = []
    xau_trades = [t for t in enriched if t['symbol'] == 'XAUUSD']
    link_success = 0
    link_fail = 0
    time_gaps = []

    for t in enriched:
        rec = dict(t)
        rec['displacement_linked'] = False
        rec['displacement_fields'] = {}

        if t['symbol'] != 'XAUUSD':
            linked.append(rec)
            continue

        # Parse entry time
        et_str = t['entry_time']
        try:
            et = datetime.fromisoformat(et_str.replace('Z', '').replace('+00:00', ''))
        except:
            linked.append(rec)
            link_fail += 1
            continue

        trade_date = t['date']
        trade_kz = t['kill_zone']

        # Map kill_zone to session name in displacement DB
        kz_map = {'london': 'london', 'ny': 'ny'}
        target_session = kz_map.get(trade_kz, trade_kz)

        # Filter displacements: same date, same session
        candidates = []
        for d in displacements:
            if d.get('date') == trade_date and d.get('session', '').lower() == target_session:
                # Must be before or near entry time (within 120 min before)
                time_diff = (et - d['_ts']).total_seconds() / 60
                if -10 <= time_diff <= 120:  # Allow 10 min after entry too
                    candidates.append((d, abs(time_diff)))

        if candidates:
            # Take closest
            candidates.sort(key=lambda x: x[1])
            best_disp, gap_min = candidates[0]

            rec['displacement_linked'] = True
            rec['displacement_time_gap_min'] = round(gap_min, 1)

            # Infer direction from displacement
            disp_dir = best_disp.get('direction', '')
            if disp_dir == 'bullish':
                rec['direction'] = 'LONG'
            elif disp_dir == 'bearish':
                rec['direction'] = 'SHORT'

            # Copy all displacement fields
            disp_fields = {k: v for k, v in best_disp.items() if k != '_ts'}
            rec['displacement_fields'] = disp_fields

            link_success += 1
            time_gaps.append(gap_min)
        else:
            link_fail += 1

        linked.append(rec)

    # For GBPUSD trades, try to infer direction from M15 price action
    m15_file = BASE / 'data' / 'historical' / 'XAUUSD_M15.csv'
    # (GBPUSD direction inference would need GBPUSD M15 which only has 701 rows)
    # For GBPUSD trades without direction, leave as None

    # For XAUUSD trades that didn't link, try M15 price action
    m15_data = {}
    with open(m15_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            m15_data[row['time']] = row

    for rec in linked:
        if rec['direction'] is None and rec['symbol'] == 'XAUUSD':
            # Use M15 candle at entry: if close > open, likely LONG
            et_str = rec['entry_time']
            if et_str:
                # Try to match to M15 candle
                et_clean = et_str.replace('Z', '').replace('T', ' ').replace('+00:00', '')
                if et_clean in m15_data:
                    candle = m15_data[et_clean]
                    if float(candle['close']) > float(candle['open']):
                        rec['direction'] = 'LONG'
                        rec['direction_source'] = 'M15_candle'
                    else:
                        rec['direction'] = 'SHORT'
                        rec['direction_source'] = 'M15_candle'

    stats = {
        'total_xauusd_trades': len(xau_trades),
        'linked_to_displacement': link_success,
        'unlinked': link_fail,
        'avg_time_gap_min': round(sum(time_gaps)/len(time_gaps), 1) if time_gaps else None,
        'median_time_gap_min': round(sorted(time_gaps)[len(time_gaps)//2], 1) if time_gaps else None,
        'direction_inferred': sum(1 for t in linked if t['direction'] is not None),
        'direction_null': sum(1 for t in linked if t['direction'] is None),
    }

    print(f"Phase 0B: {link_success}/{len(xau_trades)} XAUUSD trades linked to displacement DB")
    print(f"  Unlinked: {link_fail}")
    if time_gaps:
        print(f"  Avg time gap: {stats['avg_time_gap_min']} min")
    print(f"  Direction inferred: {stats['direction_inferred']}/{len(linked)}")

    return linked, stats

###############################################################################
# 0C: Verify candle data
###############################################################################
def phase_0c():
    """Verify historical candle data coverage."""
    results = {}

    for tf in ['M15', 'H1', 'H4', 'D1']:
        f = BASE / 'data' / 'historical' / f'XAUUSD_{tf}.csv'
        if f.exists():
            with open(f) as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
            dates = [r['time'][:10] for r in rows]
            results[f'XAUUSD_{tf}'] = {
                'rows': len(rows),
                'date_range': f"{min(dates)} to {max(dates)}",
                'unique_dates': len(set(dates))
            }

    for tf in ['M15', 'H1', 'H4', 'D1']:
        f = BASE / 'data' / 'historical' / f'GBPUSD_{tf}.csv'
        if f.exists():
            with open(f) as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
            if rows:
                dates = [r.get('time', r.get('Time', ''))[:10] for r in rows]
                dates = [d for d in dates if d]
                results[f'GBPUSD_{tf}'] = {
                    'rows': len(rows),
                    'date_range': f"{min(dates)} to {max(dates)}" if dates else 'N/A',
                    'unique_dates': len(set(dates))
                }

    return results

###############################################################################
# Main
###############################################################################
if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 0: DATA ENRICHMENT")
    print("=" * 60)

    # 0A
    print("\n--- Phase 0A: Enriching trade index ---")
    enriched = phase_0a()

    # 0B
    print("\n--- Phase 0B: Linking to displacement DB ---")
    linked, link_stats = phase_0b(enriched)

    # 0C
    print("\n--- Phase 0C: Verifying candle data ---")
    candle_stats = phase_0c()
    for k, v in candle_stats.items():
        print(f"  {k}: {v['rows']} rows, {v['date_range']}")

    # Save enriched trade index
    with open(OUT / 'trade_index_enriched.json', 'w') as f:
        json.dump({
            'enrichment_stats': {
                'total_trades': len(linked),
                'with_entry_time_from_session': sum(1 for t in linked if not t.get('entry_time_estimated')),
                'with_estimated_entry_time': sum(1 for t in linked if t.get('entry_time_estimated')),
                'with_direction': sum(1 for t in linked if t['direction'] is not None),
                'without_direction': sum(1 for t in linked if t['direction'] is None),
                'displacement_link_stats': link_stats,
            },
            'candle_data_verification': candle_stats,
            'trades': linked,
        }, f, indent=2, default=str)

    # Save displacement-linked dataset (XAUUSD only, with displacement fields)
    xau_linked = [t for t in linked if t['symbol'] == 'XAUUSD' and t['displacement_linked']]
    with open(OUT / 'trade_displacement_linked.json', 'w') as f:
        json.dump({
            'stats': link_stats,
            'trades': xau_linked,
        }, f, indent=2, default=str)

    print(f"\nSaved: trade_index_enriched.json ({len(linked)} trades)")
    print(f"Saved: trade_displacement_linked.json ({len(xau_linked)} linked trades)")
