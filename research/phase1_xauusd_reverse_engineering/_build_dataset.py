"""
Build unified per-trade dataset for sub-session bucket analysis.

Data provenance (all simulator-based; live post-April-7 trades have no exit data
due to FTMO free-trial EA-excluded issue — see CLAUDE.md and log 'AutoTrading
disabled by client' errors):

  * q65_speed_to_mfe/q65_trade_speeds.csv  (session_simulator, 233 trades with
    candle_time, April 2024 - March 2026, all 5 instruments)
  * f3_backtest_2026-04-24/<slice>/all_results.json  (12 T7 slices, Jan-Apr 2026
    XAUUSD + USDJPY, production-faithful simulation)
  * t7_live_simulation/all_results_jan_apr10.json  (XAUUSD T7 Jan 2 - Apr 10, 2026)

Dedupes on (symbol, candle_time). UNFILLED rows dropped.
Writes: unified_trades.csv  (source CSV for bucket analysis)
"""
from __future__ import annotations
import csv
import glob
import json
import os
from collections import Counter

OUT = os.path.join(os.path.dirname(__file__), 'unified_trades.csv')
ROOT = 'C:/Users/MSI/Documents/ai-trading-agent'


def load_q65():
    p = f'{ROOT}/research/q65_speed_to_mfe/q65_trade_speeds.csv'
    with open(p) as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            try:
                rm = float(r['r_multiple'])
            except Exception:
                continue
            if r['outcome'] not in ('WIN', 'LOSS', 'BREAKEVEN'):
                continue
            yield {
                'source': 'q65_sim',
                'trade_id': r['trade_id'],
                'symbol': r['symbol'],
                'date': r['date'],
                'candle_time': r['candle_time'],
                'kill_zone': r['kill_zone'],
                'outcome': r['outcome'],
                'r_multiple': rm,
                'direction': (r.get('direction') or '').upper(),
            }


def load_f3_slices():
    for sdir in sorted(glob.glob(f'{ROOT}/research/f3_backtest_2026-04-24/*/')):
        if sdir.endswith('.log/'):
            continue
        slice_name = sdir.rstrip('/').rstrip('\\').split('/')[-1]
        p = os.path.join(sdir, 'all_results.json')
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding='utf-8') as f:
                d = json.load(f)
        except Exception:
            continue
        sym_guess = 'XAUUSD' if 'xauusd' in slice_name.lower() else (
            'USDJPY' if 'usdjpy' in slice_name.lower() else None)
        for r in d.get('results', []):
            if r.get('decision') != 'CANDIDATE':
                continue
            sym = r.get('symbol') or sym_guess
            if sym is None:
                continue
            rm_raw = r.get('r_multiple')
            if rm_raw in (None, '', 'N/A'):
                continue
            try:
                rm = float(rm_raw)
            except Exception:
                continue
            out = r.get('outcome')
            if out in ('UNFILLED', None, ''):
                continue
            if out not in ('WIN', 'LOSS', 'BREAKEVEN'):
                continue
            yield {
                'source': f'f3_{slice_name}',
                'trade_id': f"{slice_name}_{r.get('candle_time', '?')}",
                'symbol': sym,
                'date': (r.get('date') or (r.get('candle_time') or '')[:10]),
                'candle_time': r.get('candle_time', ''),
                'kill_zone': r.get('kill_zone'),
                'outcome': out,
                'r_multiple': rm,
                'direction': (r.get('direction') or '').upper(),
            }


def load_t7():
    p = f'{ROOT}/research/t7_live_simulation/all_results_jan_apr10.json'
    with open(p, encoding='utf-8') as f:
        d = json.load(f)
    sym = d.get('symbol')
    for r in d.get('results', []):
        if r.get('decision') != 'CANDIDATE':
            continue
        rm_raw = r.get('r_multiple')
        if rm_raw in (None, '', 'N/A'):
            continue
        try:
            rm = float(rm_raw)
        except Exception:
            continue
        out = r.get('outcome')
        if out in ('UNFILLED', None, ''):
            continue
        if out not in ('WIN', 'LOSS', 'BREAKEVEN'):
            continue
        yield {
            'source': 't7_live_sim_jan_apr10',
            'trade_id': f"t7_{r.get('candle_time')}",
            'symbol': sym,
            'date': r.get('date') or r.get('candle_time', '')[:10],
            'candle_time': r.get('candle_time', ''),
            'kill_zone': r.get('kill_zone'),
            'outcome': out,
            'r_multiple': rm,
            'direction': (r.get('direction') or '').upper(),
        }


def main():
    all_trades = list(load_q65()) + list(load_f3_slices()) + list(load_t7())
    print('RAW:', len(all_trades))

    # Dedup on (symbol, candle_time)
    seen = set()
    dedup = []
    for t in all_trades:
        key = (t['symbol'], t['candle_time'])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(t)
    print('DEDUP:', len(dedup))
    print('BY SOURCE:', Counter(t['source'].split('_')[0] for t in dedup))
    print('BY SYMBOL:', Counter(t['symbol'] for t in dedup))
    if dedup:
        dates = sorted([t['date'] for t in dedup])
        print('DATE RANGE:', dates[0], '->', dates[-1])

    fieldnames = [
        'source', 'trade_id', 'symbol', 'date', 'candle_time',
        'kill_zone', 'outcome', 'r_multiple', 'direction',
    ]
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for t in dedup:
            w.writerow(t)
    print('WROTE:', OUT)


if __name__ == '__main__':
    main()
