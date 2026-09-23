#!/usr/bin/env python3
"""
Agent Beta — independent LIRA A/B forensic.

Reads RAW data from:
  - LIRA: research/lira_ab_backtest/slices/{slice}/all_results.json
  - V3 A2: research/a2_v2_active_backtest/slices/{slice}/all_results.json
  - F3: research/f3_backtest_2026-04-24/{slice}/all_results.json

Computes:
  Q1 per-slice stats (recompute from raw)
  Q2 decision-divergence audit
  Q3 USDJPY LONG over-permissiveness feature analysis
  Q4 SL-placement deltas
  Q5 stratum dominance
  Q6 regime-sliced
  Q7 confidence_tier discrimination
  Plus: F3-LIRA cross-check, parse-error distribution, UNFILLED rates,
        token/latency comparison.
"""
from __future__ import annotations
import json
import os
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

LIRA_ROOT = Path(r'C:\Users\MSI\Documents\ai-trading-agent\research\lira_ab_backtest\slices')
A2_ROOT = Path(r'C:\Users\MSI\Documents\ai-trading-agent\research\a2_v2_active_backtest\slices')
F3_ROOT = Path(r'C:\Users\MSI\Documents\ai-trading-agent\research\f3_backtest_2026-04-24')
OUT_ROOT = Path(r'C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a871462b6595168f1\research\lira_ab_deep_forensic')

SLICES = [
    'xauusd_s1', 'xauusd_s2', 'xauusd_s3', 'xauusd_s4',
    'xauusd_s5', 'xauusd_s6', 'xauusd_s7', 'xauusd_s8',
    'usdjpy_s1', 'usdjpy_s2', 'usdjpy_s3', 'usdjpy_s4',
]

def load_results(root: Path, slice_id: str) -> list[dict]:
    p = root / slice_id / 'all_results.json'
    if not p.exists():
        return []
    with open(p, encoding='utf-8') as f:
        return json.load(f)['results']

def filter_candidates(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get('decision') == 'CANDIDATE']

def filter_filled(rows: list[dict]) -> list[dict]:
    """Filled = CANDIDATE with outcome WIN or LOSS (not UNFILLED/null)."""
    out = []
    for r in rows:
        if r.get('decision') != 'CANDIDATE':
            continue
        o = r.get('outcome')
        if o in ('WIN', 'LOSS'):
            out.append(r)
    return out

def wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = wins / n
    denom = 1 + z*z/n
    center = (p + z*z/(2*n)) / denom
    halfwidth = (z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / denom
    return (max(0.0, center - halfwidth), min(1.0, center + halfwidth))

def compute_stats(filled: list[dict]) -> dict:
    """Compute WR / ExpR / total R / maxdd over a filled set."""
    n = len(filled)
    wins = sum(1 for r in filled if r['outcome'] == 'WIN')
    losses = sum(1 for r in filled if r['outcome'] == 'LOSS')
    rs = [r['r_multiple'] for r in filled]
    total_r = sum(rs)
    wr = wins / n if n else 0.0
    exp_r = total_r / n if n else 0.0
    # MaxDD: walk through chronologically, peak-to-trough
    sorted_filled = sorted(filled, key=lambda r: r['candle_time'])
    cum = 0
    peak = 0
    maxdd = 0
    for r in sorted_filled:
        cum += r['r_multiple']
        peak = max(peak, cum)
        maxdd = max(maxdd, peak - cum)
    return {
        'n': n,
        'wins': wins,
        'losses': losses,
        'wr': wr,
        'wr_ci': wilson_ci(wins, n),
        'exp_r': exp_r,
        'total_r': total_r,
        'maxdd': maxdd,
    }

def main():
    OUT_ROOT.mkdir(exist_ok=True)
    out: dict[str, Any] = {}

    # Q1: Per-slice stats for both LIRA and A2
    print('=== Q1 Per-slice stats ===')
    per_slice = {}
    fleet = {'LIRA': [], 'A2': []}
    for s in SLICES:
        lira_rows = load_results(LIRA_ROOT, s)
        a2_rows = load_results(A2_ROOT, s)
        lira_cands = filter_candidates(lira_rows)
        a2_cands = filter_candidates(a2_rows)
        lira_filled = filter_filled(lira_rows)
        a2_filled = filter_filled(a2_rows)
        lira_unfilled = [r for r in lira_cands if r.get('outcome') not in ('WIN', 'LOSS')]
        a2_unfilled = [r for r in a2_cands if r.get('outcome') not in ('WIN', 'LOSS')]
        # parse_errors: rows where decision is NO_TRADE and no_trade_reason starts with "parse_error"
        lira_parse_err = sum(
            1 for r in lira_rows
            if r.get('decision') == 'NO_TRADE'
            and (r.get('no_trade_reason') or '').lower().startswith('parse_error')
        )
        a2_parse_err = sum(
            1 for r in a2_rows
            if r.get('decision') == 'NO_TRADE'
            and (r.get('no_trade_reason') or '').lower().startswith('parse_error')
        )
        per_slice[s] = {
            'lira_evaluations': len(lira_rows),
            'a2_evaluations': len(a2_rows),
            'lira_cands': len(lira_cands),
            'a2_cands': len(a2_cands),
            'lira_filled': len(lira_filled),
            'a2_filled': len(a2_filled),
            'lira_unfilled': len(lira_unfilled),
            'a2_unfilled': len(a2_unfilled),
            'lira_parse_err': lira_parse_err,
            'a2_parse_err': a2_parse_err,
            'lira_stats': compute_stats(lira_filled),
            'a2_stats': compute_stats(a2_filled),
        }
        fleet['LIRA'].extend(lira_filled)
        fleet['A2'].extend(a2_filled)
        ls = per_slice[s]['lira_stats']
        a_s = per_slice[s]['a2_stats']
        print(f'  {s:12s} | LIRA: filled={ls["n"]:2d}/cands={len(lira_cands):2d} R={ls["total_r"]:+5.1f} WR={ls["wr"]*100:4.1f}%  | A2: filled={a_s["n"]:2d}/cands={len(a2_cands):2d} R={a_s["total_r"]:+5.1f} WR={a_s["wr"]*100:4.1f}%')

    out['q1_per_slice'] = per_slice
    out['q1_fleet_LIRA'] = compute_stats(fleet['LIRA'])
    out['q1_fleet_A2'] = compute_stats(fleet['A2'])
    print()
    print(f'FLEET LIRA: {out["q1_fleet_LIRA"]}')
    print(f'FLEET A2:   {out["q1_fleet_A2"]}')

    # Q2: Decision-divergence audit
    print()
    print('=== Q2 Decision divergence ===')
    common = []  # (slice, candle_time, dir) where both produced CAND
    lira_only = []
    a2_only = []
    for s in SLICES:
        lira_rows = load_results(LIRA_ROOT, s)
        a2_rows = load_results(A2_ROOT, s)
        lira_cands = filter_candidates(lira_rows)
        a2_cands = filter_candidates(a2_rows)
        lira_keys = {(r['candle_time'], r['direction']): r for r in lira_cands}
        a2_keys = {(r['candle_time'], r['direction']): r for r in a2_cands}
        for k in lira_keys:
            if k in a2_keys:
                common.append((s, k, lira_keys[k], a2_keys[k]))
            else:
                lira_only.append((s, k, lira_keys[k]))
        for k in a2_keys:
            if k not in lira_keys:
                a2_only.append((s, k, a2_keys[k]))
    # Also count direction-only matches (even if direction disagrees)
    cand_overlap_no_dir = 0
    cand_dir_disagree = 0
    for s in SLICES:
        lira_rows = load_results(LIRA_ROOT, s)
        a2_rows = load_results(A2_ROOT, s)
        lira_cands = filter_candidates(lira_rows)
        a2_cands = filter_candidates(a2_rows)
        lira_times = {r['candle_time']: r for r in lira_cands}
        a2_times = {r['candle_time']: r for r in a2_cands}
        for t in lira_times:
            if t in a2_times:
                cand_overlap_no_dir += 1
                if lira_times[t]['direction'] != a2_times[t]['direction']:
                    cand_dir_disagree += 1
    print(f'  Common (slice, time, dir): {len(common)}')
    print(f'  LIRA-only: {len(lira_only)}')
    print(f'  A2-only: {len(a2_only)}')
    print(f'  Same time, dir-disagree: {cand_dir_disagree}')
    print(f'  Same time overlap: {cand_overlap_no_dir}')

    out['q2_overlap'] = {
        'common_count': len(common),
        'lira_only_count': len(lira_only),
        'a2_only_count': len(a2_only),
        'same_time_overlap': cand_overlap_no_dir,
        'dir_disagree_count': cand_dir_disagree,
    }
    out['q2_lira_only_records'] = [(s, k[0], k[1], r.get('outcome'), r.get('r_multiple')) for s, k, r in lira_only]
    out['q2_a2_only_records'] = [(s, k[0], k[1], r.get('outcome'), r.get('r_multiple')) for s, k, r in a2_only]

    # Q3: USDJPY LONG analysis on raw_response
    print()
    print('=== Q3 USDJPY LONG over-permissiveness ===')
    usdjpy_lira = []
    usdjpy_a2 = []
    for s in [x for x in SLICES if x.startswith('usdjpy_')]:
        usdjpy_lira.extend([(s, r) for r in filter_candidates(load_results(LIRA_ROOT, s))])
        usdjpy_a2.extend([(s, r) for r in filter_candidates(load_results(A2_ROOT, s))])
    # All LIRA USDJPY LONGs
    usdjpy_lira_long = [(s, r) for s, r in usdjpy_lira if r['direction'] == 'LONG']
    usdjpy_a2_long = [(s, r) for s, r in usdjpy_a2 if r['direction'] == 'LONG']
    print(f'  USDJPY LIRA LONGs (raw CAND): {len(usdjpy_lira_long)}')
    print(f'  USDJPY A2 LONGs   (raw CAND): {len(usdjpy_a2_long)}')

    # Confidence_tier extraction from raw_response
    def extract_tier(r):
        rr = r.get('raw_response', '')
        m = re.search(r'"confidence_tier"\s*:\s*"([^"]+)"', rr)
        return m.group(1) if m else None

    def extract_setup_grade(r):
        return r.get('setup_grade')

    def extract_gates_passed(r):
        rr = r.get('raw_response', '')
        m = re.search(r'"gates_passed"\s*:\s*\[([^\]]*)\]', rr)
        if not m:
            return []
        return re.findall(r'"([^"]+)"', m.group(1))

    # Tier distribution for LIRA USDJPY LONGs
    lira_long_tier = Counter(extract_tier(r) for s, r in usdjpy_lira_long)
    a2_long_tier = Counter(extract_tier(r) for s, r in usdjpy_a2_long)
    print(f'  LIRA tier distribution: {dict(lira_long_tier)}')
    print(f'  A2   tier distribution: {dict(a2_long_tier)}')

    # WR per tier (filled only)
    def filled(r): return r.get('outcome') in ('WIN', 'LOSS')
    lira_long_filled = [(s, r) for s, r in usdjpy_lira_long if filled(r)]
    a2_long_filled = [(s, r) for s, r in usdjpy_a2_long if filled(r)]
    tier_stats = {'LIRA': defaultdict(lambda: {'n': 0, 'wins': 0, 'rs': []}),
                  'A2': defaultdict(lambda: {'n': 0, 'wins': 0, 'rs': []})}
    for s, r in lira_long_filled:
        t = extract_tier(r) or 'unknown'
        tier_stats['LIRA'][t]['n'] += 1
        if r['outcome'] == 'WIN':
            tier_stats['LIRA'][t]['wins'] += 1
        tier_stats['LIRA'][t]['rs'].append(r['r_multiple'])
    for s, r in a2_long_filled:
        t = extract_tier(r) or 'unknown'
        tier_stats['A2'][t]['n'] += 1
        if r['outcome'] == 'WIN':
            tier_stats['A2'][t]['wins'] += 1
        tier_stats['A2'][t]['rs'].append(r['r_multiple'])

    print('  Per-tier WR (USDJPY LONG filled):')
    for variant in ('LIRA', 'A2'):
        for tier, st in tier_stats[variant].items():
            wr = st['wins'] / st['n'] if st['n'] else 0
            ci = wilson_ci(st['wins'], st['n'])
            er = sum(st['rs']) / st['n'] if st['n'] else 0
            print(f'    {variant} {tier:18s}: n={st["n"]:3d} WR={wr*100:5.1f}% [{ci[0]*100:.1f}, {ci[1]*100:.1f}] ExpR={er:+.3f}')

    # Q3 follow-on: for LIRA-only USDJPY LONGs, what tier and WR
    lira_only_usdjpy_long = []
    a2_keys_usdjpy = set()
    for s in [x for x in SLICES if x.startswith('usdjpy_')]:
        for r in filter_candidates(load_results(A2_ROOT, s)):
            a2_keys_usdjpy.add((s, r['candle_time'], r['direction']))
    for s, r in usdjpy_lira_long:
        key = (s, r['candle_time'], 'LONG')
        if key not in a2_keys_usdjpy:
            lira_only_usdjpy_long.append((s, r))
    print(f'  LIRA-only USDJPY LONGs (not produced by A2): {len(lira_only_usdjpy_long)}')
    lo_filled = [(s, r) for s, r in lira_only_usdjpy_long if filled(r)]
    lo_wins = sum(1 for s, r in lo_filled if r['outcome'] == 'WIN')
    lo_total_r = sum(r['r_multiple'] for s, r in lo_filled)
    print(f'    Filled: {len(lo_filled)}, WR: {lo_wins/len(lo_filled)*100 if lo_filled else 0:.1f}%, ExpR: {lo_total_r/len(lo_filled) if lo_filled else 0:+.3f}, Total R: {lo_total_r:+.1f}')
    lo_tier = Counter(extract_tier(r) for s, r in lira_only_usdjpy_long)
    print(f'    Tier dist of LIRA-only: {dict(lo_tier)}')

    out['q3_usdjpy_long'] = {
        'lira_long_n': len(usdjpy_lira_long),
        'a2_long_n': len(usdjpy_a2_long),
        'lira_long_tier': dict(lira_long_tier),
        'a2_long_tier': dict(a2_long_tier),
        'tier_stats': {
            v: {t: {'n': s['n'], 'wins': s['wins'], 'wr': s['wins']/s['n'] if s['n'] else 0, 'exp_r': sum(s['rs'])/s['n'] if s['n'] else 0}
                for t, s in tier_stats[v].items()}
            for v in ('LIRA', 'A2')
        },
        'lira_only_usdjpy_long_n': len(lira_only_usdjpy_long),
        'lira_only_usdjpy_long_filled': len(lo_filled),
        'lira_only_usdjpy_long_wr': lo_wins/len(lo_filled) if lo_filled else 0,
        'lira_only_usdjpy_long_exp_r': lo_total_r/len(lo_filled) if lo_filled else 0,
        'lira_only_usdjpy_long_total_r': lo_total_r,
        'lira_only_usdjpy_long_tier': dict(lo_tier),
    }

    # Q4: SL-placement delta
    print()
    print('=== Q4 SL placement delta ===')
    deltas = []
    for s, k, lira_r, a2_r in common:
        if lira_r.get('stop_loss') is None or a2_r.get('stop_loss') is None:
            continue
        if lira_r.get('entry_price') in (None, 0):
            continue
        sl_lira = float(lira_r['stop_loss'])
        sl_a2 = float(a2_r['stop_loss'])
        entry = float(lira_r['entry_price'])
        # tighter = closer to entry; for LONG: SL_lira > SL_a2 means LIRA tighter
        # for SHORT: SL_lira < SL_a2 means LIRA tighter
        d_abs = abs(sl_lira - sl_a2)
        d_pct = d_abs / entry * 100
        direction = lira_r['direction']
        if direction == 'LONG':
            lira_tighter = sl_lira > sl_a2
        else:
            lira_tighter = sl_lira < sl_a2
        # Also compute SL distance from entry for each variant
        lira_sl_dist = abs(entry - sl_lira)
        a2_sl_dist = abs(entry - sl_a2)
        lira_sl_pct = lira_sl_dist / entry * 100
        a2_sl_pct = a2_sl_dist / entry * 100
        deltas.append({
            'slice': s, 'candle_time': k[0], 'dir': k[1],
            'entry': entry, 'sl_lira': sl_lira, 'sl_a2': sl_a2,
            'd_abs': d_abs, 'd_pct': d_pct,
            'lira_tighter': lira_tighter,
            'lira_sl_pct': lira_sl_pct,
            'a2_sl_pct': a2_sl_pct,
            'lira_outcome': lira_r.get('outcome'),
            'a2_outcome': a2_r.get('outcome'),
            'lira_r': lira_r.get('r_multiple'),
            'a2_r': a2_r.get('r_multiple'),
        })
    n_d = len(deltas)
    n_tighter = sum(1 for d in deltas if d['lira_tighter'])
    n_looser = sum(1 for d in deltas if not d['lira_tighter'])
    median_d_pct = statistics.median([d['d_pct'] for d in deltas]) if deltas else 0
    mean_d_pct = statistics.mean([d['d_pct'] for d in deltas]) if deltas else 0
    print(f'  Common pairs with SL data: {n_d}')
    print(f'  LIRA tighter: {n_tighter} ({n_tighter/n_d*100 if n_d else 0:.1f}%)')
    print(f'  LIRA looser:  {n_looser} ({n_looser/n_d*100 if n_d else 0:.1f}%)')
    print(f'  Median |delta|: {median_d_pct:.3f}% of entry')
    print(f'  Mean   |delta|: {mean_d_pct:.3f}% of entry')

    # SL distance from entry, signed: LIRA - A2 in pct
    sl_dist_signed = [d['lira_sl_pct'] - d['a2_sl_pct'] for d in deltas]
    median_signed = statistics.median(sl_dist_signed) if deltas else 0
    mean_signed = statistics.mean(sl_dist_signed) if deltas else 0
    print(f'  Signed SL_distance delta (LIRA% - A2%): mean={mean_signed:+.3f}pp median={median_signed:+.3f}pp')

    # Outcome divergence
    win_to_loss = sum(1 for d in deltas if d['a2_outcome'] == 'WIN' and d['lira_outcome'] == 'LOSS')
    loss_to_win = sum(1 for d in deltas if d['a2_outcome'] == 'LOSS' and d['lira_outcome'] == 'WIN')
    win_to_unfilled = sum(1 for d in deltas if d['a2_outcome'] == 'WIN' and d['lira_outcome'] not in ('WIN', 'LOSS'))
    unfilled_to_win = sum(1 for d in deltas if d['a2_outcome'] not in ('WIN', 'LOSS') and d['lira_outcome'] == 'WIN')
    print(f'  Outcome WIN->LOSS (A2->LIRA): {win_to_loss}')
    print(f'  Outcome LOSS->WIN (A2->LIRA): {loss_to_win}')
    print(f'  Outcome WIN->UNFILLED: {win_to_unfilled}')
    print(f'  Outcome UNFILLED->WIN: {unfilled_to_win}')

    out['q4_sl_delta'] = {
        'n_pairs': n_d,
        'lira_tighter_n': n_tighter,
        'lira_looser_n': n_looser,
        'median_abs_d_pct': median_d_pct,
        'mean_abs_d_pct': mean_d_pct,
        'median_signed_d_pct': median_signed,
        'mean_signed_d_pct': mean_signed,
        'win_to_loss': win_to_loss,
        'loss_to_win': loss_to_win,
        'win_to_unfilled': win_to_unfilled,
        'unfilled_to_win': unfilled_to_win,
        'rows': deltas,
    }

    # Q5: Stratum dominance
    print()
    print('=== Q5 Stratum dominance ===')
    # Stratify by symbol, direction, kill_zone
    def strat(r):
        return (r['symbol'], r['direction'], r['kill_zone'])

    lira_strat = defaultdict(lambda: {'n': 0, 'wins': 0, 'rs': []})
    a2_strat = defaultdict(lambda: {'n': 0, 'wins': 0, 'rs': []})
    for r in fleet['LIRA']:
        k = strat(r)
        lira_strat[k]['n'] += 1
        if r['outcome'] == 'WIN':
            lira_strat[k]['wins'] += 1
        lira_strat[k]['rs'].append(r['r_multiple'])
    for r in fleet['A2']:
        k = strat(r)
        a2_strat[k]['n'] += 1
        if r['outcome'] == 'WIN':
            a2_strat[k]['wins'] += 1
        a2_strat[k]['rs'].append(r['r_multiple'])

    print('  (symbol, dir, kz) | LIRA n/WR/ExpR | A2 n/WR/ExpR | Delta ExpR')
    all_keys = sorted(set(list(lira_strat.keys()) + list(a2_strat.keys())))
    strat_results = []
    for k in all_keys:
        L = lira_strat[k]
        A = a2_strat[k]
        l_er = sum(L['rs'])/L['n'] if L['n'] else 0
        a_er = sum(A['rs'])/A['n'] if A['n'] else 0
        l_wr = L['wins']/L['n'] if L['n'] else 0
        a_wr = A['wins']/A['n'] if A['n'] else 0
        delta = l_er - a_er
        strat_results.append({'key': k, 'lira_n': L['n'], 'a2_n': A['n'], 'lira_wr': l_wr, 'a2_wr': a_wr, 'lira_exp': l_er, 'a2_exp': a_er, 'delta_exp': delta})
        print(f'  {str(k):40s} | n={L["n"]:2d} WR={l_wr*100:4.1f}% E={l_er:+.3f} | n={A["n"]:2d} WR={a_wr*100:4.1f}% E={a_er:+.3f} | dE={delta:+.3f}')

    # Where LIRA is strongest (positive ExpR delta vs A2)
    out['q5_strat'] = strat_results

    # Q6 regime-sliced: per-month per-symbol
    print()
    print('=== Q6 Per-month aggregation ===')
    def month(r): return r['candle_time'][:7]
    def per_month_agg(rows, label):
        m_stats = defaultdict(lambda: {'n': 0, 'wins': 0, 'rs': []})
        for r in rows:
            m = month(r)
            m_stats[m]['n'] += 1
            if r['outcome'] == 'WIN':
                m_stats[m]['wins'] += 1
            m_stats[m]['rs'].append(r['r_multiple'])
        return m_stats
    lira_month = per_month_agg(fleet['LIRA'], 'LIRA')
    a2_month = per_month_agg(fleet['A2'], 'A2')
    months = sorted(set(list(lira_month.keys()) + list(a2_month.keys())))
    print('  month | LIRA n/WR/ExpR | A2 n/WR/ExpR | Delta')
    out['q6_per_month'] = []
    for m in months:
        L = lira_month[m]
        A = a2_month[m]
        l_er = sum(L['rs'])/L['n'] if L['n'] else 0
        a_er = sum(A['rs'])/A['n'] if A['n'] else 0
        l_wr = L['wins']/L['n'] if L['n'] else 0
        a_wr = A['wins']/A['n'] if A['n'] else 0
        print(f'  {m} | n={L["n"]:2d} WR={l_wr*100:4.1f}% E={l_er:+.3f} | n={A["n"]:2d} WR={a_wr*100:4.1f}% E={a_er:+.3f} | dE={l_er-a_er:+.3f}')
        out['q6_per_month'].append({'month': m, 'lira_n': L['n'], 'a2_n': A['n'], 'lira_wr': l_wr, 'a2_wr': a_wr, 'lira_exp': l_er, 'a2_exp': a_er})

    # Q7 confidence_tier discrimination — fleet level
    print()
    print('=== Q7 Confidence tier discrimination (LIRA fleet) ===')
    lira_tier_full = defaultdict(lambda: {'n': 0, 'wins': 0, 'rs': []})
    for r in fleet['LIRA']:
        t = extract_tier(r) or 'unknown'
        lira_tier_full[t]['n'] += 1
        if r['outcome'] == 'WIN':
            lira_tier_full[t]['wins'] += 1
        lira_tier_full[t]['rs'].append(r['r_multiple'])
    out['q7_lira_tier'] = {}
    for t, st in lira_tier_full.items():
        wr = st['wins']/st['n'] if st['n'] else 0
        ci = wilson_ci(st['wins'], st['n'])
        er = sum(st['rs'])/st['n'] if st['n'] else 0
        print(f'  LIRA {t:18s}: n={st["n"]:3d} WR={wr*100:5.1f}% [{ci[0]*100:.1f}, {ci[1]*100:.1f}] ExpR={er:+.3f}')
        out['q7_lira_tier'][t] = {'n': st['n'], 'wins': st['wins'], 'wr': wr, 'wr_ci': ci, 'exp_r': er}
    a2_tier_full = defaultdict(lambda: {'n': 0, 'wins': 0, 'rs': []})
    for r in fleet['A2']:
        t = extract_tier(r) or 'unknown'
        a2_tier_full[t]['n'] += 1
        if r['outcome'] == 'WIN':
            a2_tier_full[t]['wins'] += 1
        a2_tier_full[t]['rs'].append(r['r_multiple'])
    out['q7_a2_tier'] = {}
    print('  --- A2 tier ---')
    for t, st in a2_tier_full.items():
        wr = st['wins']/st['n'] if st['n'] else 0
        ci = wilson_ci(st['wins'], st['n'])
        er = sum(st['rs'])/st['n'] if st['n'] else 0
        print(f'  A2   {t:18s}: n={st["n"]:3d} WR={wr*100:5.1f}% [{ci[0]*100:.1f}, {ci[1]*100:.1f}] ExpR={er:+.3f}')
        out['q7_a2_tier'][t] = {'n': st['n'], 'wins': st['wins'], 'wr': wr, 'wr_ci': ci, 'exp_r': er}

    # Token / cost per CANDIDATE comparison
    print()
    print('=== Tokens & cost per CANDIDATE ===')
    def token_stats(rows):
        cands = filter_candidates(rows)
        in_t = [r.get('input_tokens', 0) for r in cands if r.get('input_tokens')]
        out_t = [r.get('output_tokens', 0) for r in cands if r.get('output_tokens')]
        cost = [r.get('cost', 0) for r in cands if r.get('cost') is not None]
        return {
            'n': len(cands),
            'mean_in': statistics.mean(in_t) if in_t else 0,
            'mean_out': statistics.mean(out_t) if out_t else 0,
            'median_out': statistics.median(out_t) if out_t else 0,
            'mean_cost': statistics.mean(cost) if cost else 0,
        }
    lira_tokens = []
    a2_tokens = []
    for s in SLICES:
        lira_tokens.extend(filter_candidates(load_results(LIRA_ROOT, s)))
        a2_tokens.extend(filter_candidates(load_results(A2_ROOT, s)))
    lira_in = [r.get('input_tokens', 0) for r in lira_tokens if r.get('input_tokens')]
    lira_out = [r.get('output_tokens', 0) for r in lira_tokens if r.get('output_tokens')]
    a2_in = [r.get('input_tokens', 0) for r in a2_tokens if r.get('input_tokens')]
    a2_out = [r.get('output_tokens', 0) for r in a2_tokens if r.get('output_tokens')]
    print(f'  LIRA: n={len(lira_tokens)} mean_in={statistics.mean(lira_in):.0f} mean_out={statistics.mean(lira_out):.0f} median_out={statistics.median(lira_out):.0f}')
    print(f'  A2:   n={len(a2_tokens)} mean_in={statistics.mean(a2_in):.0f} mean_out={statistics.mean(a2_out):.0f} median_out={statistics.median(a2_out):.0f}')
    out['q_tokens'] = {
        'lira': {'n': len(lira_tokens), 'mean_in': statistics.mean(lira_in), 'mean_out': statistics.mean(lira_out), 'median_out': statistics.median(lira_out)},
        'a2':   {'n': len(a2_tokens),   'mean_in': statistics.mean(a2_in),   'mean_out': statistics.mean(a2_out),   'median_out': statistics.median(a2_out)},
    }

    # NO_TRADE reason categorization (LIRA vs A2)
    print()
    print('=== NO_TRADE reason distribution ===')
    def categorize_reason(reason):
        if not reason:
            return 'empty'
        r = reason.lower()
        if r.startswith('prescreen:'):
            return 'prescreen'
        if r.startswith('parse_error'):
            return 'parse_error'
        if r.startswith('p2a_'):
            return 'p2a_filter'
        return 'other'
    lira_no_trade = []
    a2_no_trade = []
    for s in SLICES:
        for r in load_results(LIRA_ROOT, s):
            if r['decision'] == 'NO_TRADE':
                lira_no_trade.append(r)
        for r in load_results(A2_ROOT, s):
            if r['decision'] == 'NO_TRADE':
                a2_no_trade.append(r)
    lira_cats = Counter(categorize_reason(r.get('no_trade_reason')) for r in lira_no_trade)
    a2_cats = Counter(categorize_reason(r.get('no_trade_reason')) for r in a2_no_trade)
    print(f'  LIRA NO_TRADE: {len(lira_no_trade)} -> {dict(lira_cats)}')
    print(f'  A2   NO_TRADE: {len(a2_no_trade)} -> {dict(a2_cats)}')

    # Save full output
    print()
    out_path = OUT_ROOT / 'beta_analysis.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, default=str)
    print(f'Saved analysis -> {out_path}')

if __name__ == '__main__':
    main()
