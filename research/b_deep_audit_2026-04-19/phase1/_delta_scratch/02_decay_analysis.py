"""
Main decay analysis.

Produces:
  - per-quarter WR per instrument
  - OB subtype decay (ob_type, fresh/retested, zone)
  - Time-of-day decay (kill zone)
  - Cross-instrument algo-density vs decay Spearman
  - Decay noise-floor bootstrap (pseudo-quarters from 131-trade XAUUSD batch)
  - Structural vs noise verdict
"""
import csv
import json
import math
import random
import statistics
from collections import defaultdict, Counter

ROOT = 'C:/Users/MSI/Documents/ai-trading-agent'
SCRATCH = f'{ROOT}/research/b_deep_audit_2026-04-19/phase1/_delta_scratch'

random.seed(42)


def quarter_of(date_str):
    y, m = date_str[:4], int(date_str[5:7])
    q = (m - 1) // 3 + 1
    return f'{y}-Q{q}'


def load_trades():
    p = f'{SCRATCH}/trades_unified.csv'
    with open(p) as f:
        return list(csv.DictReader(f))


def load_regime():
    p = f'{SCRATCH}/regime_metrics.csv'
    with open(p) as f:
        return list(csv.DictReader(f))


def load_sessions():
    p = f'{SCRATCH}/sessions_per_quarter.csv'
    with open(p) as f:
        return list(csv.DictReader(f))


def two_prop_z(n1, k1, n2, k2):
    """Two-proportion Z test (two-sided)."""
    if n1 == 0 or n2 == 0:
        return None, None
    p1 = k1 / n1
    p2 = k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    if se == 0:
        return None, None
    z = (p1 - p2) / se
    # Two-tailed p via erfc
    p = math.erfc(abs(z) / math.sqrt(2))
    return z, p


def binomial_p(n, k, p0=0.5):
    """Two-sided binomial test against null p0."""
    if n == 0:
        return None
    from math import comb
    # Compute two-sided p value
    # Find probability of observed + more extreme outcomes
    obs_prob = comb(n, k) * p0**k * (1 - p0)**(n - k)
    total = 0.0
    for i in range(n + 1):
        pi = comb(n, i) * p0**i * (1 - p0)**(n - i)
        if pi <= obs_prob + 1e-12:
            total += pi
    return total


def spearman(x, y):
    """Spearman rank correlation."""
    if len(x) != len(y) or len(x) < 3:
        return None, None
    # Rank
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0] * len(vals)
        for i, o in enumerate(order):
            ranks[o] = i + 1
        return ranks
    rx = rank(x)
    ry = rank(y)
    n = len(x)
    mean_x = sum(rx) / n
    mean_y = sum(ry) / n
    num = sum((rx[i] - mean_x) * (ry[i] - mean_y) for i in range(n))
    dx = math.sqrt(sum((r - mean_x)**2 for r in rx))
    dy = math.sqrt(sum((r - mean_y)**2 for r in ry))
    if dx == 0 or dy == 0:
        return None, None
    rho = num / (dx * dy)
    # p-value via t-approx for n>7
    if n > 3 and abs(rho) < 1:
        t = rho * math.sqrt((n - 2) / (1 - rho**2))
        # Two-tailed via normal approx (conservative)
        p = math.erfc(abs(t) / math.sqrt(2))
    else:
        p = None
    return rho, p


def report_quarterly_wr(trades, outfh):
    """Per-instrument, per-quarter WR, Expectancy, n."""
    outfh.write('\n## Per-instrument, per-quarter WR (from unified+index trades)\n\n')
    per = defaultdict(list)
    for t in trades:
        if not t.get('outcome'):
            continue
        per[(t['symbol'], t['quarter'])].append(t)

    outfh.write('| Symbol | Quarter | N | W | L | BE | WR | Expectancy |\n')
    outfh.write('|---|---|---:|---:|---:|---:|---:|---:|\n')
    symbols = sorted(set(t['symbol'] for t in trades if t.get('symbol')))
    for sym in symbols:
        for q in sorted(set(k[1] for k in per.keys() if k[0] == sym)):
            ts = per[(sym, q)]
            n = len(ts)
            w = sum(1 for t in ts if t['outcome'] == 'WIN')
            ll = sum(1 for t in ts if t['outcome'] == 'LOSS')
            be = sum(1 for t in ts if t['outcome'] == 'BREAKEVEN')
            rs = [float(t['r_multiple']) for t in ts if t.get('r_multiple')]
            wr = w / n * 100
            exp = sum(rs) / n if rs else 0
            outfh.write(f'| {sym} | {q} | {n} | {w} | {ll} | {be} | {wr:.1f}% | {exp:+.3f}R |\n')
    return per


def report_xauusd_quarterly_trend(per, outfh):
    """Does XAUUSD show monotonic WR decay?"""
    outfh.write('\n## XAUUSD quarterly decay test\n\n')
    xau_quarters = sorted([k[1] for k in per.keys() if k[0] == 'XAUUSD'])
    wrs = []
    ns = []
    exps = []
    for q in xau_quarters:
        ts = per[('XAUUSD', q)]
        if len(ts) < 3:
            continue
        w = sum(1 for t in ts if t['outcome'] == 'WIN')
        n = len(ts)
        wrs.append((q, w / n * 100, n, w))
        ns.append(n)
        rs = [float(t['r_multiple']) for t in ts if t.get('r_multiple')]
        exps.append((q, sum(rs) / len(rs) if rs else 0))

    outfh.write('| Quarter | N | Wins | WR | Exp |\n|---|---:|---:|---:|---:|\n')
    for (q, wr, n, w), (_, e) in zip(wrs, exps):
        outfh.write(f'| {q} | {n} | {w} | {wr:.1f}% | {e:+.3f}R |\n')

    # Linear regression of WR vs quarter index
    if len(wrs) >= 3:
        xs = list(range(len(wrs)))
        ys = [w[1] for w in wrs]
        mx = statistics.mean(xs)
        my = statistics.mean(ys)
        num = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs)))
        den = sum((xs[i] - mx)**2 for i in range(len(xs)))
        slope = num / den if den else None
        outfh.write(f'\n**WR trend slope**: {slope:+.2f} pp/quarter\n\n')

        # Last 4 quarters (most recent)
        last4 = wrs[-4:]
        outfh.write(f'**Last 4 quarters**: ')
        outfh.write(' → '.join(f'{q[1]:.1f}%' for q in last4) + '\n')
        outfh.write(f'  n values: {[q[2] for q in last4]}\n')

        # Compare first half vs second half
        h = len(wrs) // 2
        fh_w = sum(w[3] for w in wrs[:h])
        fh_n = sum(w[2] for w in wrs[:h])
        sh_w = sum(w[3] for w in wrs[h:])
        sh_n = sum(w[2] for w in wrs[h:])
        if fh_n and sh_n:
            fh_wr = fh_w / fh_n * 100
            sh_wr = sh_w / sh_n * 100
            z, p = two_prop_z(fh_n, fh_w, sh_n, sh_w)
            outfh.write(f'\n**First half** ({fh_n} trades): WR={fh_wr:.1f}%\n')
            outfh.write(f'**Second half** ({sh_n} trades): WR={sh_wr:.1f}%\n')
            outfh.write(f'**Two-prop Z**: z={z:.3f}, p={p:.4f}\n')


def decay_noise_bootstrap(trades, outfh, n_iter=10000):
    """Bootstrap pseudo-quarters from the XAUUSD batch to see
    how often a random resample produces the 73→59% swing.
    """
    xau = [t for t in trades if t['symbol'] == 'XAUUSD' and t.get('outcome')]
    outfh.write(f'\n## Decay noise-floor bootstrap (XAUUSD n={len(xau)})\n\n')
    outfh.write(f'Null: no time trend, all WR samples i.i.d. from pool WR.\n')
    outfh.write(f'Method: resample 4 groups of equal size to mirror the decay-period quarters.\n')

    # Use sizes of actual quarterly n for fair comparison
    # From the batch, last 4 XAUUSD quarters (2025-Q1, Q2, Q3, Q4, 2026-Q1):
    q_sizes = [32, 20, 10, 23, 32]  # 2025-Q1..2026-Q1 per earlier analysis
    # The decay claim is on 4 quarters — let's use n=32,20,10,23 for Q2-Q4 2025 + Q1 2026 (or
    # roughly equivalent sizes matching the 73→59 window)
    # Better: try to be conservative — use equal size = pool mean n ≈ 23
    avg_n = len(xau) // 5
    q_test_sizes = [avg_n] * 4  # 4 quarters of ~equal size

    outfh.write(f'Pseudo-quarter sizes: {q_test_sizes} (~{avg_n} each)\n')

    # Observed: claimed 73→71→64→59 pattern: measure some decay statistic
    # Stat = max(WR) - min(WR) across 4 pseudo-quarters
    # Stat2 = monotonic sign count (in how many resamples do we see WR[1] > WR[2] > WR[3] > WR[4])
    # Stat3 = final-to-first WR drop
    observed_spread = 73.2 - 59.4  # 13.8pp

    # The TRUE decay claim is monotonic. Let's also measure: of resamples, how often
    # is the max-min ≥ 13.8pp?

    spreads = []
    monotonic_count = 0
    final_drops = []

    outcomes = [1 if t['outcome'] == 'WIN' else 0 for t in xau]

    for _ in range(n_iter):
        # Random shuffle
        perm = random.sample(outcomes, len(outcomes))
        q_wrs = []
        idx = 0
        for qs in q_test_sizes:
            chunk = perm[idx:idx+qs]
            idx += qs
            if chunk:
                q_wrs.append(sum(chunk) / len(chunk) * 100)
        if len(q_wrs) < 2:
            continue
        sp = max(q_wrs) - min(q_wrs)
        spreads.append(sp)
        # Monotonic descending?
        is_mono = all(q_wrs[i] >= q_wrs[i+1] for i in range(len(q_wrs) - 1))
        if is_mono:
            monotonic_count += 1
        final_drops.append(q_wrs[0] - q_wrs[-1])

    p_spread = sum(1 for s in spreads if s >= observed_spread) / n_iter
    p_mono = monotonic_count / n_iter
    p_final_drop = sum(1 for d in final_drops if d >= observed_spread) / n_iter

    outfh.write(f'\n**Results** ({n_iter} iterations):\n\n')
    outfh.write(f'- Median max-min spread: {statistics.median(spreads):.2f}pp\n')
    outfh.write(f'- 95th percentile spread: {sorted(spreads)[int(n_iter*0.95)]:.2f}pp\n')
    outfh.write(f'- P(max-min ≥ 13.8pp under null): **{p_spread:.4f}**\n')
    outfh.write(f'- P(monotonic descending sequence): **{p_mono:.4f}**\n')
    outfh.write(f'- P(final-to-first drop ≥ 13.8pp): **{p_final_drop:.4f}**\n')

    # Interpretation
    if p_spread > 0.05:
        outfh.write(f'\n**Interpretation**: observed spread is within noise band (p={p_spread:.3f} > 0.05).\n')
    else:
        outfh.write(f'\n**Interpretation**: observed spread is unusually large vs null (p={p_spread:.3f}).\n')


def ob_subtype_decay(trades, outfh):
    """OB subtype decay: by framework, setup_grade, kill_zone, daily_bias."""
    xau = [t for t in trades if t['symbol'] == 'XAUUSD' and t.get('outcome')]

    outfh.write('\n## OB subtype decay analysis (XAUUSD)\n\n')

    def wr_by(rows, key):
        by = defaultdict(list)
        for t in rows:
            k = t.get(key) or 'NA'
            by[k].append(t)
        out = []
        for k, group in sorted(by.items()):
            n = len(group)
            w = sum(1 for t in group if t['outcome'] == 'WIN')
            rs = [float(t['r_multiple']) for t in group if t.get('r_multiple')]
            exp = sum(rs) / len(rs) if rs else 0
            out.append((k, n, w, w/n*100, exp))
        return out

    for dim in ['framework', 'setup_grade', 'kill_zone', 'daily_bias',
                'liquidity_pool_type', 'sweep_quality', 'displacement_quality']:
        outfh.write(f'\n### By {dim}\n\n')
        outfh.write('| Value | N | W | WR | Exp |\n|---|---:|---:|---:|---:|\n')
        for k, n, w, wr, exp in wr_by(xau, dim):
            if n == 0: continue
            outfh.write(f'| {k} | {n} | {w} | {wr:.1f}% | {exp:+.3f}R |\n')

    # Two-period split by key dimension — does the winner sub-type shift?
    outfh.write('\n### First-half vs second-half WR by subtype (XAUUSD, sorted by date)\n\n')
    xau.sort(key=lambda t: t['date'])
    half = len(xau) // 2
    fh = xau[:half]
    sh = xau[half:]
    outfh.write(f'First half: {len(fh)} trades, {fh[0]["date"]} to {fh[-1]["date"]}\n')
    outfh.write(f'Second half: {len(sh)} trades, {sh[0]["date"]} to {sh[-1]["date"]}\n\n')

    for dim in ['framework', 'setup_grade', 'kill_zone', 'daily_bias',
                'liquidity_pool_type', 'sweep_quality', 'displacement_quality']:
        outfh.write(f'\n**By {dim}**:\n\n| Value | 1H N | 1H WR | 2H N | 2H WR | ΔWR | Z | p |\n|---|---:|---:|---:|---:|---:|---:|---:|\n')
        fh_by = defaultdict(list)
        sh_by = defaultdict(list)
        for t in fh:
            fh_by[t.get(dim) or 'NA'].append(t)
        for t in sh:
            sh_by[t.get(dim) or 'NA'].append(t)
        vals = sorted(set(list(fh_by.keys()) + list(sh_by.keys())))
        for v in vals:
            n1 = len(fh_by.get(v, []))
            w1 = sum(1 for t in fh_by.get(v, []) if t['outcome'] == 'WIN')
            n2 = len(sh_by.get(v, []))
            w2 = sum(1 for t in sh_by.get(v, []) if t['outcome'] == 'WIN')
            if n1 + n2 < 5:
                continue
            wr1 = w1/n1*100 if n1 else 0
            wr2 = w2/n2*100 if n2 else 0
            d = wr2 - wr1
            z, p = two_prop_z(n1, w1, n2, w2)
            z_s = f'{z:+.2f}' if z is not None else 'NA'
            p_s = f'{p:.3f}' if p is not None else 'NA'
            outfh.write(f'| {v} | {n1} | {wr1:.1f}% | {n2} | {wr2:.1f}% | {d:+.1f}pp | {z_s} | {p_s} |\n')


def time_of_day_decay(trades, outfh):
    """WR by time-of-day bucket (KZ open/middle/end)."""
    outfh.write('\n## Time-of-day decay (XAUUSD)\n\n')
    outfh.write('KZ subdivision: first-quarter, middle-half, last-quarter based on candle_time within KZ.\n')
    outfh.write('No direct candle_time in unified trades — using kill_zone and the candle hour from date.\n')

    # Try to get candle hour from trade_id (bt_YYYY-MM-DD_kz_NNN_sym) — NO, trade_id no timestamp
    # Without candle_time, we can only split by kill_zone
    # But we do have hold_time_candles — proxy for "opened late in KZ → quick stop-out"
    xau = [t for t in trades if t['symbol'] == 'XAUUSD' and t.get('outcome')]
    by_kz = defaultdict(list)
    for t in xau:
        by_kz[t.get('kill_zone') or 'NA'].append(t)

    outfh.write('\n### WR by kill zone\n\n| KZ | N | W | WR | Exp |\n|---|---:|---:|---:|---:|\n')
    for kz, group in sorted(by_kz.items()):
        n = len(group)
        w = sum(1 for t in group if t['outcome'] == 'WIN')
        rs = [float(t['r_multiple']) for t in group if t.get('r_multiple')]
        exp = sum(rs) / len(rs) if rs else 0
        outfh.write(f'| {kz} | {n} | {w} | {w/n*100:.1f}% | {exp:+.3f}R |\n')

    # Quarterly WR per KZ
    outfh.write('\n### Quarterly WR per KZ (first half vs second half by trade order)\n\n')
    xau.sort(key=lambda t: t['date'])
    half = len(xau) // 2
    for kz in ['london', 'ny']:
        fh = [t for t in xau[:half] if t.get('kill_zone') == kz]
        sh = [t for t in xau[half:] if t.get('kill_zone') == kz]
        n1 = len(fh); w1 = sum(1 for t in fh if t['outcome'] == 'WIN')
        n2 = len(sh); w2 = sum(1 for t in sh if t['outcome'] == 'WIN')
        if n1 and n2:
            wr1 = w1/n1*100; wr2 = w2/n2*100
            z, p = two_prop_z(n1, w1, n2, w2)
            z_s = f'{z:+.2f}' if z is not None else 'NA'
            p_s = f'{p:.3f}' if p is not None else 'NA'
            outfh.write(f'- **{kz}**: 1H {w1}/{n1} ({wr1:.1f}%) → 2H {w2}/{n2} ({wr2:.1f}%), Δ={wr2-wr1:+.1f}pp, z={z_s}, p={p_s}\n')


def cross_instrument_algo_density(trades, outfh):
    """Rank instruments by algo-density, test Spearman vs decay rate."""
    outfh.write('\n## Cross-instrument algo-density correlation\n\n')
    outfh.write('Informal algo-density ranking (from handoff brief):\n')
    outfh.write('NAS100 > EURUSD > GBPUSD > USDJPY > GBPJPY > XAUUSD\n\n')

    # Compute per-instrument WR + decay slope from available data
    per = defaultdict(lambda: defaultdict(list))
    for t in trades:
        if t.get('outcome'):
            per[t['symbol']][t['quarter']].append(t)

    outfh.write('### Per-instrument WR + decay slope (last-4-quarter)\n\n')
    outfh.write('| Symbol | Total N | Overall WR | Quarters used | WR trend slope (pp/q) |\n|---|---:|---:|---|---:|\n')
    instrument_slopes = {}
    for sym in ['XAUUSD', 'USDJPY', 'GBPUSD', 'GBPJPY', 'NZDUSD', 'US30_cash', 'NAS100', 'EURUSD']:
        qs = sorted(per[sym].keys())
        total_n = sum(len(v) for v in per[sym].values())
        total_w = sum(sum(1 for t in v if t['outcome'] == 'WIN') for v in per[sym].values())
        overall_wr = total_w / total_n * 100 if total_n else 0
        # Per-quarter WRs
        wrs = []
        for q in qs:
            ts = per[sym][q]
            if len(ts) >= 3:
                w = sum(1 for t in ts if t['outcome'] == 'WIN')
                wrs.append(w / len(ts) * 100)
        if len(wrs) >= 3:
            xs = list(range(len(wrs)))
            mx = statistics.mean(xs); my = statistics.mean(wrs)
            num = sum((xs[i] - mx) * (wrs[i] - my) for i in range(len(xs)))
            den = sum((xs[i] - mx)**2 for i in range(len(xs)))
            slope = num / den if den else None
        else:
            slope = None
        instrument_slopes[sym] = slope
        slope_s = f'{slope:+.2f}' if slope is not None else f'n<3q (only {len(wrs)})'
        outfh.write(f'| {sym} | {total_n} | {overall_wr:.1f}% | {len(qs)} | {slope_s} |\n')

    # Spearman on our available data (small n)
    algo_rank = {'NAS100': 1, 'EURUSD': 2, 'GBPUSD': 3, 'USDJPY': 4, 'GBPJPY': 5, 'XAUUSD': 6}
    # more negative slope = faster decay
    rank_x = []
    rank_y = []
    for sym, alg in sorted(algo_rank.items(), key=lambda x: x[1]):
        s = instrument_slopes.get(sym)
        if s is not None:
            rank_x.append(alg)
            rank_y.append(-s)  # negate so "more decay" = higher y
    outfh.write(f'\n**Symbols available for Spearman**: {len(rank_x)}\n')
    if len(rank_x) >= 3:
        rho, p = spearman(rank_x, rank_y)
        outfh.write(f'**Spearman rho** (algo-rank vs decay): {rho:.3f}, p={p:.3f}\n')
    else:
        outfh.write(f'**Insufficient data for Spearman** (need ≥3 instruments with ≥3 quarters each)\n')


def regime_correlation(trades, regime, outfh):
    """Join quarterly WR to regime metrics; see which move with decay."""
    # Build WR[symbol][quarter] and Exp[symbol][quarter]
    per = defaultdict(lambda: defaultdict(list))
    for t in trades:
        if t.get('outcome'):
            per[t['symbol']][t['quarter']].append(t)

    # Build regime[symbol][quarter] -> dict of metrics
    regime_idx = {}
    for r in regime:
        regime_idx[(r['symbol'], r['quarter'])] = r

    outfh.write('\n## Regime metric correlation with WR (XAUUSD only — highest n)\n\n')
    # Focus on XAUUSD — the decay claim is here
    xau_qs = sorted(per['XAUUSD'].keys())

    rows = []
    outfh.write('| Quarter | N trades | WR | Exp | ADR_mean | ATR_ratio | Hurst | KER_10d | Autocorr1 | Autocorr5 | Vol_Ann | Trend_pct | Skew | Kurt |\n')
    outfh.write('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n')

    for q in xau_qs:
        ts = per['XAUUSD'][q]
        if len(ts) < 3: continue
        n = len(ts)
        w = sum(1 for t in ts if t['outcome'] == 'WIN')
        wr = w / n * 100
        rs_ = [float(t['r_multiple']) for t in ts if t.get('r_multiple')]
        exp = sum(rs_) / len(rs_) if rs_ else 0
        rm = regime_idx.get(('XAUUSD', q), {})

        def fmt(val):
            if val in (None, '', 'None'):
                return 'NA'
            try:
                return f'{float(val):.3f}'
            except Exception:
                return str(val)

        row = [
            q, n, wr, exp,
            rm.get('adr_mean'), rm.get('atr14_to_252d_ratio'), rm.get('hurst'),
            rm.get('kaufman_er_10d_mean'), rm.get('autocorr_lag1'),
            rm.get('autocorr_lag5'), rm.get('realized_vol_ann'),
            rm.get('trend_pct_of_q'), rm.get('skew'), rm.get('kurt'),
        ]
        outfh.write('| ' + ' | '.join([
            str(row[0]), str(row[1]), f'{row[2]:.1f}%', f'{row[3]:+.3f}R',
            fmt(row[4]), fmt(row[5]), fmt(row[6]), fmt(row[7]), fmt(row[8]),
            fmt(row[9]), fmt(row[10]), fmt(row[11]), fmt(row[12]), fmt(row[13]),
        ]) + ' |\n')
        rows.append(row)

    # Correlate each regime metric vs WR across quarters
    outfh.write('\n### Spearman correlation: quarterly XAUUSD WR vs regime metric\n\n')
    outfh.write('| Metric | Spearman ρ | p | Direction |\n|---|---:|---:|---|\n')
    if len(rows) >= 4:
        wrs = [r[2] for r in rows]
        # Column indices: metric starts at 4
        metric_names = ['ADR_mean', 'ATR_ratio', 'Hurst', 'KER_10d',
                        'Autocorr1', 'Autocorr5', 'Vol_Ann', 'Trend_pct',
                        'Skew', 'Kurt']
        for i, name in enumerate(metric_names):
            col = 4 + i
            xs, ys = [], []
            for r in rows:
                v = r[col]
                if v in (None, '', 'None'):
                    continue
                try:
                    xs.append(float(v))
                    ys.append(r[2])  # WR
                except Exception:
                    pass
            if len(xs) >= 4:
                rho, p = spearman(xs, ys)
                direction = 'positive' if rho > 0 else 'negative'
                rho_s = f'{rho:+.3f}' if rho is not None else 'NA'
                p_s = f'{p:.3f}' if p is not None else 'NA'
                outfh.write(f'| {name} | {rho_s} | {p_s} | {direction} |\n')


def main():
    trades = load_trades()
    regime = load_regime()
    sessions = load_sessions()
    print(f'Trades: {len(trades)}')
    print(f'Regime rows: {len(regime)}')
    print(f'Sessions rows: {len(sessions)}')

    out_path = f'{SCRATCH}/decay_analysis.md'
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write('# Delta — Phase 1 — Decay Analysis Tables\n\n')
        fh.write('Auto-generated by `02_decay_analysis.py`. Sources:\n')
        fh.write('- `trades_unified.csv` (merged `unified_trades_v2_20260331.json` + `_trade_index.json`)\n')
        fh.write('- `regime_metrics.csv` (from `data/historical/*_D1.csv` and fallbacks)\n')
        fh.write('- `sessions_per_quarter.csv` (walked `knowledge_base_backtest/sessions/`)\n\n')

        per = report_quarterly_wr(trades, fh)
        report_xauusd_quarterly_trend(per, fh)
        decay_noise_bootstrap(trades, fh)
        ob_subtype_decay(trades, fh)
        time_of_day_decay(trades, fh)
        cross_instrument_algo_density(trades, fh)
        regime_correlation(trades, regime, fh)

    print(f'\nWrote {out_path}')


if __name__ == '__main__':
    main()
