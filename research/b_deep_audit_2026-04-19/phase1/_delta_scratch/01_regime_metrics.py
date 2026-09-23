"""
Compute per-quarter regime metrics from D1/H1 CSVs for all 7 instruments.

Metrics:
  1. ADR  — Average Daily Range (H-L on D1), median + mean
  2. ATR_ratio — ATR(14) vs 52-week rolling mean
  3. Hurst exponent (rolling 90-day on D1 close-to-close)
  4. Kaufman AMA trend strength proxy — abs(Price_change) / sum(abs(daily_moves))
  5. Autocorrelation lag-1 and lag-5 on D1 returns
  6. Realized vol — std of H1 log returns, annualized (sanity)
  7. Skew + kurt of D1 returns

Outputs: regime_metrics.csv  (symbol, quarter, metric, value)
"""
import csv
import math
import os
import statistics
from collections import defaultdict
from datetime import datetime

ROOT = 'C:/Users/MSI/Documents/ai-trading-agent'
SCRATCH = f'{ROOT}/research/b_deep_audit_2026-04-19/phase1/_delta_scratch'

# Paths: data/historical/ has 2023-earliest; data/ root has 2024; data/historical_2026/ has 2026 only
# We want longest possible history, so prefer data/historical/ then fallback to data/
HIST_DIRS = [
    f'{ROOT}/data/historical',
    f'{ROOT}/data',  # for NAS100, EURUSD, XAGUSD
]

SYMBOLS_TO_LOAD = ['XAUUSD', 'USDJPY', 'GBPUSD', 'GBPJPY', 'NZDUSD', 'US30_cash',
                   'EURUSD', 'NAS100', 'XAGUSD']


def quarter_of(dt_str):
    y, m = dt_str[:4], int(dt_str[5:7])
    q = (m - 1) // 3 + 1
    return f'{y}-Q{q}'


def load_csv(sym, tf):
    """Return list of dicts sorted by time. Handles multiple header layouts."""
    for d in HIST_DIRS:
        p = f'{d}/{sym}_{tf}.csv'
        if not os.path.exists(p):
            continue
        rows = []
        with open(p) as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                try:
                    rows.append({
                        'time': r.get('time') or r.get('date') or r.get('datetime'),
                        'open': float(r['open']),
                        'high': float(r['high']),
                        'low': float(r['low']),
                        'close': float(r['close']),
                    })
                except (ValueError, KeyError):
                    continue
        rows.sort(key=lambda x: x['time'])
        return rows, p
    return None, None


def atr(rows, period=14, i=None):
    """ATR at index i (default: last index)."""
    if i is None:
        i = len(rows) - 1
    if i < period:
        return None
    trs = []
    for j in range(max(1, i - period + 1), i + 1):
        h = rows[j]['high']
        l = rows[j]['low']
        pc = rows[j-1]['close']
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    return statistics.mean(trs)


def rolling_returns(rows):
    out = []
    for i in range(1, len(rows)):
        try:
            r = math.log(rows[i]['close'] / rows[i-1]['close'])
        except (ValueError, ZeroDivisionError):
            r = 0
        out.append(r)
    return out


def hurst(series, max_lag=None):
    """Compute Hurst exponent via rescaled-range method (approximate).

    Uses log-log regression of R/S over varying chunk sizes.
    Returns None if series is too short.
    """
    n = len(series)
    if n < 20:
        return None
    if max_lag is None:
        max_lag = min(n // 2, 50)

    lags = list(range(2, max_lag + 1))
    log_rs = []
    log_n = []

    for lag in lags:
        if lag > n // 2:
            break
        # Partition into chunks of `lag` length
        n_chunks = n // lag
        rs_vals = []
        for ci in range(n_chunks):
            chunk = series[ci*lag:(ci+1)*lag]
            mu = statistics.mean(chunk)
            devs = [x - mu for x in chunk]
            # Cumulative deviations
            cum = [0]
            for d in devs:
                cum.append(cum[-1] + d)
            R = max(cum) - min(cum)
            S = statistics.stdev(chunk) if len(chunk) > 1 else 0
            if S > 0:
                rs_vals.append(R / S)
        if rs_vals:
            log_rs.append(math.log(statistics.mean(rs_vals)))
            log_n.append(math.log(lag))

    if len(log_rs) < 3:
        return None
    # Linear regression: slope of log(R/S) vs log(n)
    n_pts = len(log_rs)
    mean_x = statistics.mean(log_n)
    mean_y = statistics.mean(log_rs)
    num = sum((log_n[i] - mean_x) * (log_rs[i] - mean_y) for i in range(n_pts))
    den = sum((log_n[i] - mean_x)**2 for i in range(n_pts))
    if den == 0:
        return None
    return num / den


def autocorr(series, lag):
    """Pearson autocorrelation at given lag."""
    n = len(series)
    if n <= lag + 1:
        return None
    x1 = series[:n-lag]
    x2 = series[lag:]
    m1 = statistics.mean(x1)
    m2 = statistics.mean(x2)
    num = sum((x1[i] - m1) * (x2[i] - m2) for i in range(len(x1)))
    d1 = math.sqrt(sum((x - m1)**2 for x in x1))
    d2 = math.sqrt(sum((x - m2)**2 for x in x2))
    if d1 == 0 or d2 == 0:
        return None
    return num / (d1 * d2)


def kaufman_efficiency(rows, period=10):
    """Kaufman's Efficiency Ratio over last `period` bars:
    |close[end] - close[end-period]| / sum(|close[i] - close[i-1]|)
    Returns 0..1; higher = stronger trend.
    """
    if len(rows) < period + 1:
        return None
    net = abs(rows[-1]['close'] - rows[-1-period]['close'])
    vol = sum(abs(rows[i]['close'] - rows[i-1]['close'])
              for i in range(len(rows) - period, len(rows)))
    if vol == 0:
        return None
    return net / vol


def skew(series):
    if len(series) < 3:
        return None
    mu = statistics.mean(series)
    sd = statistics.stdev(series)
    if sd == 0:
        return None
    n = len(series)
    return sum(((x - mu) / sd)**3 for x in series) / n


def kurt(series):
    if len(series) < 4:
        return None
    mu = statistics.mean(series)
    sd = statistics.stdev(series)
    if sd == 0:
        return None
    n = len(series)
    # Excess kurtosis
    return sum(((x - mu) / sd)**4 for x in series) / n - 3


def analyze_instrument(sym):
    d1, path_d1 = load_csv(sym, 'D1')
    h1, path_h1 = load_csv(sym, 'H1')
    if not d1:
        print(f'  {sym}: NO D1 DATA')
        return []

    # Partition D1 into quarters
    d1_by_q = defaultdict(list)
    for row in d1:
        q = quarter_of(row['time'])
        d1_by_q[q].append(row)

    h1_by_q = defaultdict(list)
    if h1:
        for row in h1:
            q = quarter_of(row['time'])
            h1_by_q[q].append(row)

    # Rolling: compute 52-week (252-day) rolling ATR_14 baseline to normalize
    # For each quarter, we compute ATR14 over the quarter and 252-day rolling baseline
    # For simplicity: compute ATR14 per-day through the full series; then quarterly mean.
    atr_series = []  # (time_str, atr14)
    for i in range(14, len(d1)):
        trs = []
        for j in range(i - 14 + 1, i + 1):
            h = d1[j]['high']
            l = d1[j]['low']
            pc = d1[j-1]['close']
            tr = max(h - l, abs(h - pc), abs(l - pc))
            trs.append(tr)
        atr_series.append((d1[i]['time'], statistics.mean(trs)))

    # 252-day rolling mean of ATR
    atr_long_mean = []
    for i in range(len(atr_series)):
        start = max(0, i - 251)
        chunk = [a[1] for a in atr_series[start:i+1]]
        atr_long_mean.append(statistics.mean(chunk))

    # D1 log-returns full series
    returns = rolling_returns(d1)
    dates = [d1[i+1]['time'] for i in range(len(returns))]  # returns[i] corresponds to d1[i+1]

    # Aggregate metrics per quarter
    out_rows = []
    quarters = sorted(d1_by_q.keys())
    for q in quarters:
        q_days = d1_by_q[q]
        if len(q_days) < 5:
            continue

        # ADR (average daily range)
        adrs = [row['high'] - row['low'] for row in q_days]
        adr_mean = statistics.mean(adrs)
        adr_median = statistics.median(adrs)
        adr_pct_mean = statistics.mean((row['high'] - row['low']) / row['close'] for row in q_days) * 100

        # ATR ratio: mean ATR14 during Q vs mean(ATR14 rolling-252 within Q)
        q_atrs = [a[1] for a in atr_series if quarter_of(a[0]) == q]
        q_atr_long = [atr_long_mean[i] for i, a in enumerate(atr_series) if quarter_of(a[0]) == q]
        if q_atrs and q_atr_long:
            atr_ratio = statistics.mean(q_atrs) / statistics.mean(q_atr_long)
        else:
            atr_ratio = None

        # Hurst on quarter-confined log returns
        q_returns = [returns[i] for i in range(len(returns)) if quarter_of(dates[i]) == q]
        h_q = hurst(q_returns) if len(q_returns) >= 20 else None

        # Autocorr lag-1, lag-5
        ac1 = autocorr(q_returns, 1)
        ac5 = autocorr(q_returns, 5)

        # Kaufman efficiency (end-of-quarter, looking back over 10 days)
        # Also average over all rolling windows in quarter
        kefs = []
        for i in range(10, len(q_days)):
            kef = kaufman_efficiency(q_days[:i+1], 10)
            if kef is not None:
                kefs.append(kef)
        kef_mean = statistics.mean(kefs) if kefs else None

        # Realized vol (std of log returns, annualized)
        if len(q_returns) > 1:
            rv = statistics.stdev(q_returns) * math.sqrt(252)
        else:
            rv = None

        # Skew, kurt
        sk = skew(q_returns)
        ku = kurt(q_returns)

        # Trend direction: (close_end - close_start) / close_start  %
        trend_pct = (q_days[-1]['close'] - q_days[0]['close']) / q_days[0]['close'] * 100

        out_rows.append({
            'symbol': sym,
            'quarter': q,
            'n_days': len(q_days),
            'adr_mean': adr_mean,
            'adr_median': adr_median,
            'adr_pct_mean': adr_pct_mean,
            'atr14_to_252d_ratio': atr_ratio,
            'hurst': h_q,
            'autocorr_lag1': ac1,
            'autocorr_lag5': ac5,
            'kaufman_er_10d_mean': kef_mean,
            'realized_vol_ann': rv,
            'skew': sk,
            'kurt': ku,
            'trend_pct_of_q': trend_pct,
        })

    return out_rows


def main():
    all_rows = []
    for sym in SYMBOLS_TO_LOAD:
        print(f'Analyzing {sym}...')
        rows = analyze_instrument(sym)
        all_rows.extend(rows)
        if rows:
            # Print summary for this instrument
            print(f'  {len(rows)} quarters from {rows[0]["quarter"]} to {rows[-1]["quarter"]}')

    out_csv = f'{SCRATCH}/regime_metrics.csv'
    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        headers = [
            'symbol', 'quarter', 'n_days',
            'adr_mean', 'adr_median', 'adr_pct_mean',
            'atr14_to_252d_ratio', 'hurst', 'autocorr_lag1', 'autocorr_lag5',
            'kaufman_er_10d_mean', 'realized_vol_ann', 'skew', 'kurt',
            'trend_pct_of_q',
        ]
        w.writerow(headers)
        for r in all_rows:
            w.writerow([r.get(h) for h in headers])
    print(f'\nWrote {out_csv}  ({len(all_rows)} rows)')


if __name__ == '__main__':
    main()
