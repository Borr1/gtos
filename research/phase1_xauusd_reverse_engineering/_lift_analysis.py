"""
Compute expected-R/month lift if skip candidates implemented.

Reads bucket_stats_60min.csv. Since n<20 makes recommendations impossible in
most cells, this module also shows the "worst 20% by E[R]" contribution —
purely descriptive, not a recommendation.

Math:
  * For each bucket, contribution_R = n * E[R]  (total R delivered by bucket)
  * Rank by E[R] ascending; cumulative sum from the bottom gives the "loss
    you avoid" by dropping the worst k buckets.
  * Convert to expected R/month by dividing by months spanned in dataset.

Also presents high-quality-frequency ranking (n * WR * avg_R) for EMPHASIS
candidates (note: none at n>=20 in current dataset).
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(__file__)
INP = os.path.join(HERE, 'bucket_stats_60min.csv')
INP_TRADES = os.path.join(HERE, 'unified_trades.csv')
OUT = os.path.join(HERE, 'lift_analysis.md')


def months_spanned(trades):
    dates = sorted(t['date'] for t in trades)
    d0 = datetime.fromisoformat(dates[0])
    d1 = datetime.fromisoformat(dates[-1])
    delta_days = (d1 - d0).days
    return max(delta_days / 30.0, 1.0)


def main():
    trades = list(csv.DictReader(open(INP_TRADES)))
    for t in trades:
        t['r_multiple'] = float(t['r_multiple'])
    months = months_spanned(trades)

    rows = list(csv.DictReader(open(INP)))
    for r in rows:
        r['n'] = int(r['n'])
        r['wr'] = float(r['wr'])
        r['mean_r'] = float(r['mean_r'])
        r['hqf_score'] = float(r['hqf_score'])
        r['wr_lo95'] = float(r['wr_lo95']) if r['wr_lo95'] else None
        r['wr_hi95'] = float(r['wr_hi95']) if r['wr_hi95'] else None
        r['mean_r_lo95'] = float(r['mean_r_lo95']) if r['mean_r_lo95'] else None
        r['mean_r_hi95'] = float(r['mean_r_hi95']) if r['mean_r_hi95'] else None

    lines = []
    lines.append('# Lift Analysis — Expected R/Month Impact of Bucket Trimming')
    lines.append('')
    lines.append(f'Dataset spans **{months:.1f} months** ({len(trades)} trades). ')
    lines.append('All values are simulator-derived (q65_sim / F3 backtest / T7 live sim).')
    lines.append('')
    lines.append('## Per-instrument 60-min bucket ranking by E[R] (worst → best)')
    lines.append('')

    per_sym = defaultdict(list)
    for r in rows:
        per_sym[r['symbol']].append(r)

    for sym, brs in sorted(per_sym.items()):
        lines.append(f'### {sym}')
        lines.append('')
        lines.append('| KZ | Bucket | n | WR | WR CI | E[R] | E[R] CI | Total R | Rec |')
        lines.append('|---|---|---|---|---|---|---|---|---|')
        ordered = sorted(brs, key=lambda r: (r['mean_r'], r['n']))
        for r in ordered:
            n = r['n']
            wr = r['wr']
            er = r['mean_r']
            total_r = n * er
            wr_ci = f"[{r['wr_lo95']:.2f}, {r['wr_hi95']:.2f}]" if r['wr_lo95'] is not None else '-'
            er_ci = f"[{r['mean_r_lo95']:+.2f}, {r['mean_r_hi95']:+.2f}]" if r['mean_r_lo95'] is not None else '-'
            lines.append(f"| {r['kill_zone']} | {r['bucket_start']}-{r['bucket_end']} | {n} | {wr:.3f} | {wr_ci} | {er:+.3f} | {er_ci} | {total_r:+.2f}R | {r['recommendation']} |")
        lines.append('')

    # Worst 20% lift for XAUUSD at n>=20 subset
    lines.append('## XAUUSD: hypothetical trimming of worst buckets (n>=20 only)')
    lines.append('')
    lines.append('*Caveat: the only XAUUSD bucket with negative E[R] and n>=20 is NY 13:00 (n=29, E[R]=-0.088R, WR 48.3%). Its WR upper-CI (65.5%) is well above breakeven (35.7%), so it does NOT pass the SKIP rule. This section is descriptive only.*')
    lines.append('')
    xau = [r for r in per_sym.get('XAUUSD', []) if r['n'] >= 20]
    if xau:
        # Rank bottom-first
        xau_ranked = sorted(xau, key=lambda r: r['mean_r'])
        total_n_xau = sum(r['n'] for r in xau)
        total_r_xau = sum(r['n'] * r['mean_r'] for r in xau)
        lines.append(f'All XAUUSD n>=20 buckets: N={total_n_xau}, total R delivered={total_r_xau:+.2f}R over {months:.1f} months = **{total_r_xau/months:+.2f}R/month**')
        lines.append('')
        cum_n = 0
        cum_r = 0.0
        lines.append('| Dropped buckets | Cumulative freq lost | Cumulative R avoided | New E[R]/month (after drop) | Pct N lost |')
        lines.append('|---|---|---|---|---|')
        for k in range(0, len(xau_ranked) + 1):
            dropped = xau_ranked[:k]
            dn = sum(r['n'] for r in dropped)
            dr = sum(r['n'] * r['mean_r'] for r in dropped)
            remaining_r = total_r_xau - dr
            remaining_per_month = remaining_r / months
            pct = 100 * dn / total_n_xau if total_n_xau else 0
            label = ', '.join(f"{r['kill_zone']} {r['bucket_start']}" for r in dropped) or 'none'
            lines.append(f'| {label} | {dn} trades ({pct:.1f}%) | {-dr:+.2f}R | {remaining_per_month:+.3f}R/mo | {pct:.1f}% |')
        lines.append('')

    # High-quality-frequency ranking (emphasis lens): for candidates that WOULD
    # reach emphasis if n>=20
    lines.append('## High-quality-frequency ranking (freq x mean R) — all buckets')
    lines.append('')
    lines.append('Ranked descending by total R delivered (n * E[R]). Useful for spotting where the edge actually lives empirically.')
    lines.append('')
    lines.append('| Symbol | KZ | Bucket | n | WR | E[R] | Total R | Rec |')
    lines.append('|---|---|---|---|---|---|---|---|')
    all_rows = sorted(rows, key=lambda r: r['n'] * r['mean_r'], reverse=True)
    for r in all_rows[:25]:
        n = r['n']
        total_r = n * r['mean_r']
        lines.append(f"| {r['symbol']} | {r['kill_zone']} | {r['bucket_start']}-{r['bucket_end']} | {n} | {r['wr']:.3f} | {r['mean_r']:+.3f} | {total_r:+.2f}R | {r['recommendation']} |")
    lines.append('')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('WROTE', OUT)
    print(f'\n--- {months:.1f} months of data ---')


if __name__ == '__main__':
    main()
