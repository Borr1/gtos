"""
Load and unify all available trade-outcome datasets for delta regime-decay analysis.

Output files (written to _delta_scratch/):
  - trades_unified.csv  — all trades with outcome, r_multiple, instrument, date, framework, kz
  - sessions_derived.csv — per-session CANDIDATE counts by quarter/instrument
"""

import json
import os
import csv
from collections import defaultdict, Counter
from datetime import datetime, timezone

ROOT = 'C:/Users/MSI/Documents/ai-trading-agent'
SCRATCH = f'{ROOT}/research/b_deep_audit_2026-04-19/phase1/_delta_scratch'


def quarter_of(date_str):
    """Convert date string to 'YYYY-QN'."""
    if not date_str:
        return None
    y, m = date_str[:4], int(date_str[5:7])
    q = (m - 1) // 3 + 1
    return f'{y}-Q{q}'


def load_unified_trades():
    """Load the canonical per-trade outcome dataset."""
    p = f'{ROOT}/knowledge_base_backtest/analysis/unified_trades_v2_20260331.json'
    with open(p) as f:
        return json.load(f)


def load_batch_api_results():
    """Load all msgbatch_*_results.json files and merge."""
    import glob
    batches = sorted(glob.glob(f'{ROOT}/knowledge_base_backtest/batch_api/msgbatch_*_results.json'))
    all_rows = []
    for p in batches:
        with open(p) as f:
            d = json.load(f)
        if isinstance(d, list):
            all_rows.extend(d)
    return all_rows


def load_trade_index():
    p = f'{ROOT}/knowledge_base/index/_trade_index.json'
    with open(p) as f:
        return json.load(f).get('trades', [])


def load_sessions_unified():
    """Walk all session JSONs and build a unified candle-evaluation table."""
    sessions_dir = f'{ROOT}/knowledge_base_backtest/sessions'
    all_evals = []
    for symbol in os.listdir(sessions_dir):
        sp = os.path.join(sessions_dir, symbol)
        if not os.path.isdir(sp):
            continue
        for f in sorted(os.listdir(sp)):
            if not f.endswith('.json'):
                continue
            try:
                with open(os.path.join(sp, f)) as fh:
                    d = json.load(fh)
                date_str = d.get('date')
                evs = d.get('candle_evaluations', [])
                for e in evs:
                    all_evals.append({
                        'symbol': symbol,
                        'date': date_str,
                        'candle_time': e.get('candle_time'),
                        'kill_zone': e.get('kill_zone'),
                        'decision': e.get('decision'),
                        'framework': e.get('framework'),
                        'setup_grade': e.get('setup_grade'),
                        'confidence': e.get('confidence'),
                        'trade_id': e.get('trade_id'),
                        'trade_executed': e.get('trade_executed'),
                    })
            except Exception as ex:
                print(f'Warn: {f}: {ex}')
    return all_evals


def main():
    # Unified trades (v2) are the primary per-trade outcomes
    unified = load_unified_trades()
    # Trade index (live-format, 129 rows GBPUSD+XAUUSD — superset of unified)
    idx_trades = load_trade_index()
    # Sessions: full candle evaluations (no outcomes, but CANDIDATE counts)
    sessions = load_sessions_unified()

    print(f'unified_trades_v2:  {len(unified)} trades')
    print(f'_trade_index.json:  {len(idx_trades)} trades')
    print(f'session evals:      {len(sessions)} evaluations')

    # Build per-trade table matching all three
    # Key: date + candle_time + symbol
    # unified_trades has: date, trade_id, kill_zone, framework, outcome, r_multiple, mfe_r, mae_r, direction, entry_price, ...
    # No symbol in unified though — note first rec
    # Build lookup: either tid or tid+symbol_suffix
    idx_by_tid = {}
    for idx in idx_trades:
        tid = idx.get('trade_id')
        if tid:
            idx_by_tid[tid] = idx.get('symbol')

    def resolve_symbol(tid):
        if not tid:
            return 'UNKNOWN'
        # Direct match
        if tid in idx_by_tid:
            return idx_by_tid[tid]
        # Try with _<symbol> suffix
        for suf_sym in [('_xauusd', 'XAUUSD'), ('_gbpusd', 'GBPUSD'),
                        ('_usdjpy', 'USDJPY'), ('_gbpjpy', 'GBPJPY'),
                        ('_us30', 'US30_cash'), ('_nzdusd', 'NZDUSD')]:
            k = f'{tid}{suf_sym[0]}'
            if k in idx_by_tid:
                return idx_by_tid[k]
        # Fall back: unified_trades_v2 is XAUUSD-only (per session 31 confirmation)
        # since its naming uses trailing NUM without symbol suffix
        return 'XAUUSD'

    syms_unified = Counter()
    for t in unified:
        sym = resolve_symbol(t.get('trade_id'))
        syms_unified[sym] += 1

    print(f'\nunified symbols: {syms_unified}')

    # Write the unified trades CSV enriched with symbol
    out_csv = f'{SCRATCH}/trades_unified.csv'
    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([
            'trade_id', 'symbol', 'date', 'quarter', 'kill_zone', 'framework',
            'direction', 'outcome', 'r_multiple', 'setup_grade', 'exit_substate',
            'mfe_r', 'mae_r', 'hold_time_candles', 'daily_bias',
            'liquidity_pool_type', 'sweep_quality', 'displacement_quality',
            'entry_price', 'stop_loss', 'take_profit_1', 'planned_rr',
        ])
        for t in unified:
            tid = t.get('trade_id', '')
            sym = resolve_symbol(tid)
            w.writerow([
                tid, sym, t.get('date'), quarter_of(t.get('date')),
                t.get('kill_zone'), t.get('framework'),
                t.get('direction'), t.get('outcome'), t.get('r_multiple'),
                t.get('setup_grade'), t.get('exit_substate'),
                t.get('mfe_r'), t.get('mae_r'), t.get('hold_time_candles'),
                t.get('daily_bias'),
                t.get('liquidity_pool_type'), t.get('sweep_quality'), t.get('displacement_quality'),
                t.get('entry_price'), t.get('stop_loss'), t.get('take_profit_1'), t.get('planned_rr'),
            ])
    print(f'\nWrote {out_csv}')

    # Also add extra trades from the index file that unified may have missed
    # (particularly for other symbols). Dedupe by trade_id OR by
    # trade_id minus _symbol_suffix.
    unified_ids = set()
    for t in unified:
        tid = t.get('trade_id')
        if tid:
            unified_ids.add(tid)
            # also register what our resolver would have matched to
            for suf in ['_xauusd', '_gbpusd', '_usdjpy', '_gbpjpy', '_us30', '_nzdusd']:
                unified_ids.add(f'{tid}{suf}')
    extra = [idx for idx in idx_trades if idx.get('trade_id') and idx.get('trade_id') not in unified_ids]
    if extra:
        print(f'\n_trade_index has {len(extra)} trades NOT in unified')
        with open(out_csv, 'a', newline='') as f:
            w = csv.writer(f)
            for idx in extra:
                w.writerow([
                    idx.get('trade_id'), idx.get('symbol'), idx.get('date'),
                    quarter_of(idx.get('date')),
                    idx.get('kill_zone'), idx.get('framework'),
                    idx.get('direction'), idx.get('outcome'), idx.get('r_multiple'),
                    idx.get('setup_grade'), idx.get('exit_type'),
                    idx.get('mfe_r'), idx.get('mae_r'), idx.get('hold_time_candles'),
                    None, None, None, None, None, None, None, None,
                ])
        print(f'Appended {len(extra)} to {out_csv}')

    # Sessions CSV: CANDIDATE count / trade count by symbol+quarter
    out_sess = f'{SCRATCH}/sessions_per_quarter.csv'
    per_q = defaultdict(lambda: defaultdict(int))  # (sym, q) -> {candidates, trades, evals}
    for e in sessions:
        date = e.get('date') or (e.get('candle_time') or '')[:10]
        q = quarter_of(date)
        if not q:
            continue
        key = (e['symbol'], q)
        per_q[key]['evals'] += 1
        if e.get('decision') == 'CANDIDATE':
            per_q[key]['candidates'] += 1
        if e.get('decision') == 'CANDIDATE' and e.get('trade_executed'):
            per_q[key]['trades'] += 1
    with open(out_sess, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['symbol', 'quarter', 'evals', 'candidates', 'trades', 'candidate_rate_pct'])
        for (sym, q), v in sorted(per_q.items()):
            rate = v['candidates'] / v['evals'] * 100 if v['evals'] else 0
            w.writerow([sym, q, v['evals'], v['candidates'], v['trades'], f'{rate:.2f}'])
    print(f'Wrote {out_sess}')


if __name__ == '__main__':
    main()
