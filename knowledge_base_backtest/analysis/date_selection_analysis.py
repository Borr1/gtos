#!/usr/bin/env python3
"""
Reverse-Engineer AI Date Selection — Deterministic Edge Extraction
Builds feature matrix, runs exploratory analysis, trains models, validates.
"""

import json
import glob
import sys
import os
import warnings
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

BASE = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = BASE / "knowledge_base_backtest" / "analysis"
DATA_DIR = BASE / "data"

# Add src to path for market_state imports
sys.path.insert(0, str(BASE / "src"))

###############################################################################
# STEP 0: LOAD ALL DATA
###############################################################################

def load_price_data():
    """Load all timeframe price data."""
    dfs = {}
    for tf in ['M15', 'H1', 'H4', 'D1']:
        path = DATA_DIR / f"XAUUSD_{tf}.csv"
        df = pd.read_csv(path, parse_dates=['time'])
        df = df.sort_values('time').reset_index(drop=True)
        dfs[tf] = df
    return dfs

def load_phase0():
    """Load Phase 0 corrected naive baseline data."""
    with open(ANALYSIS_DIR / "phase0_corrected_data_0_1959.json") as f:
        return json.load(f)

def load_phase1_pa_responses():
    """Load all Phase 1 PA responses (all evaluated dates)."""
    pa_files = sorted(glob.glob(str(ANALYSIS_DIR / "phase1_part*_pa_responses_*.jsonl")))
    pa_files += sorted(glob.glob(str(ANALYSIS_DIR / "phase1_rerun_pa_responses_*.jsonl")))
    responses = []
    for pf in pa_files:
        with open(pf) as f:
            for line in f:
                responses.append(json.loads(line.strip()))
    return responses

def load_phase1_trades():
    """Load Phase 1 merged trades."""
    with open(ANALYSIS_DIR / "phase1_all_trades_merged.json") as f:
        return json.load(f)

def load_displacement_db():
    """Load displacement database."""
    with open(ANALYSIS_DIR / "displacement_database_20260403_0030.json") as f:
        return json.load(f)

###############################################################################
# STEP 1: FEATURE COMPUTATION
###############################################################################

def compute_atr(df, period=20):
    """Compute ATR for a dataframe."""
    h = df['high'].values
    l = df['low'].values
    c = df['close'].values
    tr = np.zeros(len(df))
    tr[0] = h[0] - l[0]
    for i in range(1, len(df)):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1]))
    atr = pd.Series(tr).rolling(period).mean().values
    return atr

def compute_adr(d1_df, period=20):
    """Compute Average Daily Range."""
    daily_range = d1_df['high'] - d1_df['low']
    return daily_range.rolling(period).mean()

def get_session_candles(m15_df, date_str, session):
    """Get M15 candles for a specific session on a given date."""
    date = pd.Timestamp(date_str)
    if session == 'asian':
        start = date + pd.Timedelta(hours=0)
        end = date + pd.Timedelta(hours=6, minutes=45)
    elif session == 'london':
        start = date + pd.Timedelta(hours=7)
        end = date + pd.Timedelta(hours=11, minutes=45)
    elif session == 'london_full':
        start = date + pd.Timedelta(hours=7)
        end = date + pd.Timedelta(hours=12, minutes=45)
    elif session == 'ny':
        start = date + pd.Timedelta(hours=13)
        end = date + pd.Timedelta(hours=16, minutes=45)
    elif session == 'pre_london':
        start = date + pd.Timedelta(hours=0)
        end = date + pd.Timedelta(hours=6, minutes=45)
    elif session == 'pre_ny':
        start = date + pd.Timedelta(hours=7)
        end = date + pd.Timedelta(hours=12, minutes=45)
    else:
        return pd.DataFrame()

    mask = (m15_df['time'] >= start) & (m15_df['time'] <= end)
    return m15_df[mask].copy()

def count_displacements_in_session(m15_candles, atr_value):
    """Count 2x+ body displacements in a set of candles."""
    if len(m15_candles) == 0 or atr_value is None or atr_value <= 0:
        return 0
    avg_body = m15_candles.apply(lambda r: abs(r['close'] - r['open']), axis=1).mean()
    if avg_body <= 0:
        return 0
    bodies = m15_candles.apply(lambda r: abs(r['close'] - r['open']), axis=1)
    return int((bodies >= avg_body * 2).sum())

def compute_trend_strength(swings, direction):
    """Count consecutive aligned swing pairs in last 4 swings.
    For bullish: higher highs and higher lows.
    For bearish: lower highs and lower lows.
    """
    if len(swings) < 2:
        return 0
    recent = swings[-4:] if len(swings) >= 4 else swings
    count = 0
    for i in range(1, len(recent)):
        if direction == 'bullish':
            if recent[i] > recent[i-1]:
                count += 1
        elif direction == 'bearish':
            if recent[i] < recent[i-1]:
                count += 1
    return count

def detect_simple_swings(df, lookback=3):
    """Simple swing detection for feature computation."""
    highs = []
    lows = []
    h = df['high'].values
    l = df['low'].values

    for i in range(lookback, len(df) - lookback):
        if all(h[i] >= h[i-j] for j in range(1, lookback+1)) and \
           all(h[i] >= h[i+j] for j in range(1, lookback+1)):
            highs.append((i, h[i]))
        if all(l[i] <= l[i-j] for j in range(1, lookback+1)) and \
           all(l[i] <= l[i+j] for j in range(1, lookback+1)):
            lows.append((i, l[i]))

    return highs, lows

def get_d1_features_for_date(d1_df, date_str):
    """Compute D1-level features for a date (using data BEFORE this date)."""
    date = pd.Timestamp(date_str)
    # Get D1 data up to yesterday
    prior = d1_df[d1_df['time'] < date].copy()
    if len(prior) < 25:
        return {}

    yesterday = prior.iloc[-1]
    d1_range_yesterday = yesterday['high'] - yesterday['low']
    d1_body_yesterday = abs(yesterday['close'] - yesterday['open'])
    d1_body_pct = d1_body_yesterday / d1_range_yesterday if d1_range_yesterday > 0 else 0

    # ADR
    adr_20 = (prior['high'] - prior['low']).tail(20).mean()
    adr_5 = (prior['high'] - prior['low']).tail(5).mean()
    d1_range_vs_adr = d1_range_yesterday / adr_20 if adr_20 > 0 else 1
    daily_adr_expanding = 1 if adr_5 > adr_20 else 0

    # D1 ATR percentile
    atr_vals = compute_atr(prior.tail(120), 20)
    valid_atrs = atr_vals[~np.isnan(atr_vals)]
    if len(valid_atrs) > 10:
        current_atr = valid_atrs[-1]
        d1_atr_pct = (valid_atrs < current_atr).sum() / len(valid_atrs) * 100
    else:
        d1_atr_pct = 50

    # D1 direction from yesterday
    d1_direction = 'bullish' if yesterday['close'] > yesterday['open'] else 'bearish'

    # Trend strength: use last 8 swing highs/lows
    swing_h, swing_l = detect_simple_swings(prior.tail(30), lookback=2)

    # Count higher-highs (bullish) or lower-lows (bearish) in recent swings
    d1_trend_str = 0
    if d1_direction == 'bullish' and len(swing_h) >= 2:
        recent_sh = [s[1] for s in swing_h[-4:]]
        d1_trend_str = sum(1 for i in range(1, len(recent_sh)) if recent_sh[i] > recent_sh[i-1])
    elif d1_direction == 'bearish' and len(swing_l) >= 2:
        recent_sl = [s[1] for s in swing_l[-4:]]
        d1_trend_str = sum(1 for i in range(1, len(recent_sl)) if recent_sl[i] < recent_sl[i-1])

    return {
        'd1_body_pct_yesterday': d1_body_pct,
        'd1_range_vs_adr': d1_range_vs_adr,
        'd1_adr_20': adr_20,
        'd1_atr_percentile': d1_atr_pct,
        'd1_trend_strength': d1_trend_str,
        'd1_direction_bullish': 1 if d1_direction == 'bullish' else 0,
        'daily_adr_expanding': daily_adr_expanding,
    }

def get_htf_features(h4_df, h1_df, date_str, kz, d1_direction):
    """Compute H4 and H1 features before the KZ."""
    date = pd.Timestamp(date_str)

    if kz == 'london':
        cutoff = date + pd.Timedelta(hours=7)
    else:  # ny
        cutoff = date + pd.Timedelta(hours=13)

    h4_prior = h4_df[h4_df['time'] < cutoff].tail(40)
    h1_prior = h1_df[h1_df['time'] < cutoff].tail(60)

    features = {}

    # H4 features
    if len(h4_prior) > 5:
        last_h4 = h4_prior.iloc[-1]
        h4_dir = 'bullish' if last_h4['close'] > last_h4['open'] else 'bearish'
        features['h4_aligned_d1'] = 1 if (h4_dir == 'bullish') == (d1_direction == 'bullish') else 0

        swing_h, swing_l = detect_simple_swings(h4_prior, lookback=2)
        if d1_direction == 'bullish' and len(swing_h) >= 2:
            recent = [s[1] for s in swing_h[-4:]]
            features['h4_trend_strength'] = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])
        elif d1_direction == 'bearish' and len(swing_l) >= 2:
            recent = [s[1] for s in swing_l[-4:]]
            features['h4_trend_strength'] = sum(1 for i in range(1, len(recent)) if recent[i] < recent[i-1])
        else:
            features['h4_trend_strength'] = 0

        # H4 last BOS candles ago (simplified: last candle that broke above/below prior swing)
        features['h4_last_bos_candles_ago'] = 10  # default
        for i in range(len(h4_prior)-1, max(0, len(h4_prior)-20), -1):
            candle = h4_prior.iloc[i]
            if d1_direction == 'bullish' and swing_h:
                if candle['close'] > swing_h[-1][1]:
                    features['h4_last_bos_candles_ago'] = len(h4_prior) - 1 - i
                    break
            elif d1_direction == 'bearish' and swing_l:
                if candle['close'] < swing_l[-1][1]:
                    features['h4_last_bos_candles_ago'] = len(h4_prior) - 1 - i
                    break
    else:
        features['h4_aligned_d1'] = 0
        features['h4_trend_strength'] = 0
        features['h4_last_bos_candles_ago'] = 10

    # H1 features
    if len(h1_prior) > 5:
        last_h1 = h1_prior.iloc[-1]
        h1_dir = 'bullish' if last_h1['close'] > last_h1['open'] else 'bearish'
        features['h1_aligned_d1'] = 1 if (h1_dir == 'bullish') == (d1_direction == 'bullish') else 0

        swing_h, swing_l = detect_simple_swings(h1_prior, lookback=2)
        if d1_direction == 'bullish' and len(swing_h) >= 2:
            recent = [s[1] for s in swing_h[-4:]]
            features['h1_trend_strength'] = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])
        elif d1_direction == 'bearish' and len(swing_l) >= 2:
            recent = [s[1] for s in swing_l[-4:]]
            features['h1_trend_strength'] = sum(1 for i in range(1, len(recent)) if recent[i] < recent[i-1])
        else:
            features['h1_trend_strength'] = 0
    else:
        features['h1_aligned_d1'] = 0
        features['h1_trend_strength'] = 0

    return features

def get_session_features(m15_df, date_str, kz, adr_20):
    """Compute session structure features before the KZ."""
    features = {}

    if kz == 'london':
        # Asian session features
        asian = get_session_candles(m15_df, date_str, 'asian')
        if len(asian) > 3:
            asian_range = asian['high'].max() - asian['low'].min()
            features['pre_kz_range'] = asian_range
            features['pre_kz_range_pct_adr'] = asian_range / adr_20 if adr_20 > 0 else 0
            features['pre_kz_body_avg'] = asian.apply(lambda r: abs(r['close'] - r['open']), axis=1).mean()

            # Count displacements
            avg_body = features['pre_kz_body_avg']
            if avg_body > 0:
                bodies = asian.apply(lambda r: abs(r['close'] - r['open']), axis=1)
                features['pre_kz_num_displacements'] = int((bodies >= avg_body * 2).sum())
            else:
                features['pre_kz_num_displacements'] = 0

            # Trend direction
            net_move = asian.iloc[-1]['close'] - asian.iloc[0]['open']
            features['pre_kz_trend'] = 1 if net_move > 0 else (-1 if net_move < 0 else 0)

            features['asian_high'] = asian['high'].max()
            features['asian_low'] = asian['low'].min()
        else:
            features.update({k: np.nan for k in ['pre_kz_range', 'pre_kz_range_pct_adr',
                'pre_kz_body_avg', 'pre_kz_num_displacements', 'pre_kz_trend',
                'asian_high', 'asian_low']})

    else:  # ny
        # London session features (pre-NY)
        london = get_session_candles(m15_df, date_str, 'pre_ny')
        if len(london) > 3:
            london_range = london['high'].max() - london['low'].min()
            features['pre_kz_range'] = london_range
            features['pre_kz_range_pct_adr'] = london_range / adr_20 if adr_20 > 0 else 0
            features['pre_kz_body_avg'] = london.apply(lambda r: abs(r['close'] - r['open']), axis=1).mean()

            avg_body = features['pre_kz_body_avg']
            if avg_body > 0:
                bodies = london.apply(lambda r: abs(r['close'] - r['open']), axis=1)
                features['pre_kz_num_displacements'] = int((bodies >= avg_body * 2).sum())
            else:
                features['pre_kz_num_displacements'] = 0

            net_move = london.iloc[-1]['close'] - london.iloc[0]['open']
            features['pre_kz_trend'] = 1 if net_move > 0 else (-1 if net_move < 0 else 0)

            features['london_high'] = london['high'].max()
            features['london_low'] = london['low'].min()
        else:
            features.update({k: np.nan for k in ['pre_kz_range', 'pre_kz_range_pct_adr',
                'pre_kz_body_avg', 'pre_kz_num_displacements', 'pre_kz_trend',
                'london_high', 'london_low']})

    return features

def get_volatility_features(m15_df, date_str, kz):
    """Compute volatility features at KZ open."""
    date = pd.Timestamp(date_str)
    if kz == 'london':
        cutoff = date + pd.Timedelta(hours=7)
    else:
        cutoff = date + pd.Timedelta(hours=13)

    prior_m15 = m15_df[m15_df['time'] < cutoff].tail(120)
    features = {}

    if len(prior_m15) > 25:
        atr_vals = compute_atr(prior_m15, 20)
        valid = atr_vals[~np.isnan(atr_vals)]
        if len(valid) > 10:
            current = valid[-1]
            features['m15_atr'] = current
            features['m15_atr_percentile'] = (valid < current).sum() / len(valid) * 100
        else:
            features['m15_atr'] = np.nan
            features['m15_atr_percentile'] = 50

        # Consolidation score: range of last 5 candles / (ATR * 2.5)
        last5 = prior_m15.tail(5)
        r5 = last5['high'].max() - last5['low'].min()
        if features.get('m15_atr', 0) and not np.isnan(features.get('m15_atr', np.nan)):
            features['consolidation_score'] = r5 / (features['m15_atr'] * 2.5) if features['m15_atr'] > 0 else 1
        else:
            features['consolidation_score'] = np.nan
    else:
        features['m15_atr'] = np.nan
        features['m15_atr_percentile'] = 50
        features['consolidation_score'] = np.nan

    return features

def get_liquidity_features(m15_df, d1_df, date_str, kz, d1_direction):
    """Compute liquidity features near KZ open."""
    date = pd.Timestamp(date_str)
    if kz == 'london':
        cutoff = date + pd.Timedelta(hours=7)
    else:
        cutoff = date + pd.Timedelta(hours=13)

    prior_m15 = m15_df[m15_df['time'] < cutoff].tail(100)
    d1_prior = d1_df[d1_df['time'] < date].tail(5)

    features = {}
    if len(prior_m15) < 10:
        features['num_liquidity_levels'] = 0
        features['nearest_level_distance_pct'] = np.nan
        features['sweep_available'] = 0
        return features

    kz_open_price = prior_m15.iloc[-1]['close']

    # Identify liquidity levels: equal highs, equal lows, session levels
    levels = []

    # PDH/PDL
    if len(d1_prior) >= 2:
        pdh = d1_prior.iloc[-1]['high']
        pdl = d1_prior.iloc[-1]['low']
        levels.extend([pdh, pdl])

    # Session high/low (Asian for London, London for NY)
    if kz == 'london':
        session_candles = get_session_candles(m15_df, date_str, 'asian')
    else:
        session_candles = get_session_candles(m15_df, date_str, 'pre_ny')

    if len(session_candles) > 0:
        levels.append(session_candles['high'].max())
        levels.append(session_candles['low'].min())

    # Equal highs/lows from recent M15 (within 0.5$ tolerance)
    highs = prior_m15['high'].values[-40:]
    lows = prior_m15['low'].values[-40:]
    tol = 0.5
    for i in range(len(highs)):
        for j in range(i+2, len(highs)):
            if abs(highs[i] - highs[j]) < tol:
                levels.append((highs[i] + highs[j]) / 2)
    for i in range(len(lows)):
        for j in range(i+2, len(lows)):
            if abs(lows[i] - lows[j]) < tol:
                levels.append((lows[i] + lows[j]) / 2)

    # Count levels within 0.5% of price
    threshold = kz_open_price * 0.005
    nearby = [l for l in levels if abs(l - kz_open_price) < threshold]
    features['num_liquidity_levels'] = len(nearby)

    if nearby:
        distances = [abs(l - kz_open_price) / kz_open_price * 100 for l in nearby]
        features['nearest_level_distance_pct'] = min(distances)
    else:
        features['nearest_level_distance_pct'] = 0.5

    # Sweep available: is there a level on counter-trend side within 0.3%?
    ct_threshold = kz_open_price * 0.003
    if d1_direction == 'bullish':
        # Counter-trend = below price (sweep lows)
        ct_levels = [l for l in levels if l < kz_open_price and (kz_open_price - l) < ct_threshold]
    else:
        ct_levels = [l for l in levels if l > kz_open_price and (l - kz_open_price) < ct_threshold]
    features['sweep_available'] = 1 if ct_levels else 0

    return features

def get_displacement_db_features(disp_db, date_str, kz):
    """Cross-reference displacement database for this date/KZ (forward-looking)."""
    features = {}
    matching = [d for d in disp_db if d['date'] == date_str and
                d.get('kz', False) and
                d.get('session', '') == kz]

    features['kz_displacements'] = len(matching)

    if matching:
        features['kz_max_alignment'] = max(d.get('align', 0) for d in matching)
        features['kz_any_sweep_fvg'] = 1 if any(
            d.get('sweep', False) and d.get('creates_fvg', False) for d in matching) else 0
        features['kz_strongest_body_ratio'] = max(d.get('body_ratio', 0) for d in matching)
        features['kz_max_cont_1h'] = max(d.get('cont_1h', 0) for d in matching)
    else:
        features['kz_max_alignment'] = 0
        features['kz_any_sweep_fvg'] = 0
        features['kz_strongest_body_ratio'] = 0
        features['kz_max_cont_1h'] = 0

    return features

def get_day_features(date_str):
    """Day and timing features."""
    date = pd.Timestamp(date_str)
    dow = date.dayofweek  # 0=Mon, 4=Fri
    return {
        'day_of_week': dow,
        'is_monday': 1 if dow == 0 else 0,
        'is_tuesday': 1 if dow == 1 else 0,
        'is_wednesday': 1 if dow == 2 else 0,
        'is_thursday': 1 if dow == 3 else 0,
        'is_friday': 1 if dow == 4 else 0,
    }

###############################################################################
# STEP 1 MAIN: Build feature matrix
###############################################################################

def build_feature_matrix(p0_data, price_dfs, disp_db, approach='per_kz'):
    """Build the date-level feature matrix.
    approach: 'per_kz' = one row per date-kz combo
              'per_date' = one row per date (ai_traded if EITHER kz traded)
    """
    m15 = price_dfs['M15']
    h1 = price_dfs['H1']
    h4 = price_dfs['H4']
    d1 = price_dfs['D1']

    # Pre-compute D1 ADR
    d1['adr'] = compute_adr(d1, 20)

    rows = []
    skipped = 0

    if approach == 'per_kz':
        items = p0_data  # each item is a date-kz combo
    else:
        # Group by date
        by_date = defaultdict(list)
        for r in p0_data:
            by_date[r['date']].append(r)
        items = []
        for date, records in by_date.items():
            ai_traded = any(r.get('ai_traded', False) for r in records)
            # Use london record as primary
            london = [r for r in records if r['kz'] == 'london']
            ny = [r for r in records if r['kz'] == 'ny']
            primary = london[0] if london else records[0]
            items.append({**primary, 'ai_traded': ai_traded,
                         'ny_also_traded': any(r.get('ai_traded', False) for r in ny)})

    total = len(items)
    for idx, item in enumerate(items):
        if idx % 50 == 0:
            print(f"  Processing {idx}/{total}...")

        date_str = item['date']
        kz = item.get('kz', 'london')
        d1_dir_str = item.get('d1_direction', 'bullish')
        ai_traded = item.get('ai_traded', False)

        # Get entry price for reference
        entry_price = item.get('entry_price', 0)

        # Strategy A outcome at 1.0R TP
        strat_a = item.get('strategy_a', {})
        outcomes = strat_a.get('outcomes', {})
        tp1 = outcomes.get('tp_1.0r', {})
        naive_r = tp1.get('final_r', 0)

        row = {
            'date': date_str,
            'kz': kz,
            'ai_traded': 1 if ai_traded else 0,
            'entry_price': entry_price,
            'naive_r_1r': naive_r,
            'd1_direction': d1_dir_str,
        }

        # D1 features
        d1_feats = get_d1_features_for_date(d1, date_str)
        if not d1_feats:
            skipped += 1
            continue
        row.update(d1_feats)

        adr_20 = d1_feats.get('d1_adr_20', 20)

        # HTF features
        htf_feats = get_htf_features(h4, h1, date_str, kz, d1_dir_str)
        row.update(htf_feats)

        # Session features
        sess_feats = get_session_features(m15, date_str, kz, adr_20)
        row.update(sess_feats)

        # Volatility features
        vol_feats = get_volatility_features(m15, date_str, kz)
        row.update(vol_feats)

        # Liquidity features
        liq_feats = get_liquidity_features(m15, d1, date_str, kz, d1_dir_str)
        row.update(liq_feats)

        # Day features
        day_feats = get_day_features(date_str)
        row.update(day_feats)

        # Displacement DB features (forward-looking / explanatory)
        disp_feats = get_displacement_db_features(disp_db, date_str, kz)
        row.update(disp_feats)

        rows.append(row)

    print(f"  Built {len(rows)} rows, skipped {skipped}")
    return pd.DataFrame(rows)

###############################################################################
# STEP 2-6: Analysis Functions
###############################################################################

def exploratory_analysis(df):
    """Step 3: Feature comparison, correlations, distributions."""
    from scipy import stats

    predictive_features = [
        'pre_kz_range_pct_adr', 'pre_kz_body_avg', 'pre_kz_num_displacements',
        'pre_kz_trend', 'd1_body_pct_yesterday', 'd1_range_vs_adr',
        'd1_atr_percentile', 'd1_trend_strength', 'daily_adr_expanding',
        'h4_aligned_d1', 'h4_trend_strength', 'h4_last_bos_candles_ago',
        'h1_aligned_d1', 'h1_trend_strength',
        'm15_atr', 'm15_atr_percentile', 'consolidation_score',
        'num_liquidity_levels', 'nearest_level_distance_pct', 'sweep_available',
        'is_monday', 'is_tuesday', 'is_wednesday', 'is_thursday', 'is_friday',
        'day_of_week', 'pre_kz_range',
    ]

    explanatory_features = [
        'kz_displacements', 'kz_max_alignment', 'kz_any_sweep_fvg',
        'kz_strongest_body_ratio', 'kz_max_cont_1h',
    ]

    ai_dates = df[df['ai_traded'] == 1]
    non_ai = df[df['ai_traded'] == 0]

    print(f"\n{'='*70}")
    print(f"EXPLORATORY ANALYSIS")
    print(f"{'='*70}")
    print(f"Total rows: {len(df)}, AI traded: {len(ai_dates)} ({len(ai_dates)/len(df)*100:.1f}%)")

    # 3A: Feature comparison
    results = []
    for feat in predictive_features + explanatory_features:
        if feat not in df.columns:
            continue
        ai_vals = pd.to_numeric(ai_dates[feat], errors='coerce').dropna()
        non_vals = pd.to_numeric(non_ai[feat], errors='coerce').dropna()
        if len(ai_vals) < 3 or len(non_vals) < 3:
            continue

        ai_mean = float(ai_vals.mean())
        non_mean = float(non_vals.mean())

        # Cohen's d
        pooled_std = np.sqrt(((len(ai_vals)-1)*ai_vals.std()**2 + (len(non_vals)-1)*non_vals.std()**2) /
                            (len(ai_vals) + len(non_vals) - 2))
        cohens_d = (ai_mean - non_mean) / pooled_std if pooled_std > 0 else 0

        # t-test
        t_stat, p_val = stats.ttest_ind(ai_vals.astype(float), non_vals.astype(float), equal_var=False)

        is_explanatory = feat in explanatory_features
        results.append({
            'feature': feat,
            'ai_mean': ai_mean,
            'non_ai_mean': non_mean,
            'cohens_d': cohens_d,
            'abs_d': abs(cohens_d),
            'p_value': p_val,
            'significant': p_val < 0.05,
            'type': 'EXPLANATORY' if is_explanatory else 'PREDICTIVE',
        })

    results.sort(key=lambda x: x['abs_d'], reverse=True)

    print(f"\n--- Top Features by Effect Size (Cohen's d) ---")
    print(f"{'Feature':<32} {'AI Mean':>10} {'Non-AI':>10} {'Cohen d':>10} {'p-value':>10} {'Type':>12}")
    print(f"{'-'*92}")
    for r in results[:20]:
        sig = '*' if r['significant'] else ' '
        print(f"{r['feature']:<32} {r['ai_mean']:>10.4f} {r['non_ai_mean']:>10.4f} "
              f"{r['cohens_d']:>+10.3f} {r['p_value']:>10.4f}{sig} {r['type']:>12}")

    # 3B: Correlation matrix of top predictive features
    top_pred = [r['feature'] for r in results if r['type'] == 'PREDICTIVE'][:15]
    if len(top_pred) > 3:
        corr = df[top_pred].corr()
        print(f"\n--- High Correlations (>0.5) among top predictive features ---")
        for i in range(len(top_pred)):
            for j in range(i+1, len(top_pred)):
                c = corr.iloc[i, j]
                if abs(c) > 0.5:
                    print(f"  {top_pred[i]} × {top_pred[j]}: {c:.3f}")

    # 3C: Distribution comparison for top 5
    print(f"\n--- Distribution Comparison (Top 5 by effect size) ---")
    for r in results[:5]:
        feat = r['feature']
        ai_vals = ai_dates[feat].dropna()
        non_vals = non_ai[feat].dropna()
        print(f"\n  {feat}:")
        print(f"    AI dates:     min={ai_vals.min():.4f}, P25={ai_vals.quantile(0.25):.4f}, "
              f"median={ai_vals.median():.4f}, P75={ai_vals.quantile(0.75):.4f}, max={ai_vals.max():.4f}")
        print(f"    Non-AI dates: min={non_vals.min():.4f}, P25={non_vals.quantile(0.25):.4f}, "
              f"median={non_vals.median():.4f}, P75={non_vals.quantile(0.75):.4f}, max={non_vals.max():.4f}")
        direction = "HIGHER" if r['cohens_d'] > 0 else "LOWER"
        print(f"    Effect: AI dates have {direction} values (d={r['cohens_d']:+.3f}, p={r['p_value']:.4f})")

    return results, top_pred

def build_models(df, predictive_features):
    """Step 4: Build decision tree and logistic regression models."""
    from sklearn.tree import DecisionTreeClassifier, export_text
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
    from sklearn.preprocessing import StandardScaler

    # Filter to predictive features only
    pred_cols = [f for f in predictive_features if f in df.columns]

    # Drop rows with NaN in features
    model_df = df[['date', 'ai_traded', 'naive_r_1r'] + pred_cols].dropna(subset=pred_cols)
    print(f"\n{'='*70}")
    print(f"MODEL BUILDING")
    print(f"{'='*70}")
    print(f"Rows with complete features: {len(model_df)} (dropped {len(df)-len(model_df)} with NaN)")

    # Chronological split
    model_df = model_df.sort_values('date').reset_index(drop=True)
    split_idx = int(len(model_df) * 0.6)
    train = model_df.iloc[:split_idx]
    test = model_df.iloc[split_idx:]

    print(f"Train: {len(train)} rows ({train['date'].min()} to {train['date'].max()}), "
          f"AI traded: {train['ai_traded'].sum()}")
    print(f"Test:  {len(test)} rows ({test['date'].min()} to {test['date'].max()}), "
          f"AI traded: {test['ai_traded'].sum()}")

    X_train = train[pred_cols].values
    y_train = train['ai_traded'].values
    X_test = test[pred_cols].values
    y_test = test['ai_traded'].values

    # 4A: Decision Tree
    print(f"\n--- Decision Tree (max_depth=4) ---")
    dt = DecisionTreeClassifier(max_depth=4, class_weight='balanced', random_state=42,
                                min_samples_leaf=5)
    dt.fit(X_train, y_train)
    y_pred_dt = dt.predict(X_test)

    print(f"\nTest Set Performance:")
    print(classification_report(y_test, y_pred_dt, target_names=['Not Traded', 'AI Traded'], zero_division=0))

    tree_rules = export_text(dt, feature_names=pred_cols, max_depth=4)
    print(f"\nDecision Tree Rules:\n{tree_rules}")

    # Feature importance
    importances = list(zip(pred_cols, dt.feature_importances_))
    importances.sort(key=lambda x: x[1], reverse=True)
    print(f"\nFeature Importance (Gini):")
    for feat, imp in importances[:15]:
        if imp > 0:
            print(f"  {feat:<35} {imp:.4f}")

    # 4B: Logistic Regression
    print(f"\n--- Logistic Regression ---")
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)

    lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    lr.fit(X_train_sc, y_train)
    y_pred_lr = lr.predict(X_test_sc)

    print(f"\nTest Set Performance:")
    print(classification_report(y_test, y_pred_lr, target_names=['Not Traded', 'AI Traded'], zero_division=0))

    coefs = list(zip(pred_cols, lr.coef_[0]))
    coefs.sort(key=lambda x: abs(x[1]), reverse=True)
    print(f"\nLogistic Regression Coefficients (by magnitude):")
    for feat, coef in coefs[:15]:
        if abs(coef) > 0.01:
            print(f"  {feat:<35} {coef:+.4f}")

    # 4C: Combined feature importance
    dt_rank = {feat: rank for rank, (feat, _) in enumerate(importances)}
    lr_rank = {feat: rank for rank, (feat, _) in enumerate(coefs)}
    combined = []
    for feat in pred_cols:
        dr = dt_rank.get(feat, len(pred_cols))
        lr_ = lr_rank.get(feat, len(pred_cols))
        combined.append((feat, dr + lr_, dr, lr_))
    combined.sort(key=lambda x: x[1])

    print(f"\n--- Combined Feature Importance (DT rank + LR rank) ---")
    for feat, total, dr, lr_ in combined[:10]:
        print(f"  {feat:<35} Combined={total:>4}  (DT={dr}, LR={lr_})")

    return dt, lr, scaler, pred_cols, train, test, importances, coefs

def build_simple_filter(df, dt, pred_cols, importances, train, test):
    """Step 4D: Build and evaluate simple rule-based filter."""
    from sklearn.metrics import precision_score, recall_score

    print(f"\n{'='*70}")
    print(f"SIMPLE RULE-BASED FILTER")
    print(f"{'='*70}")

    # Extract the most important split points from the decision tree
    tree = dt.tree_
    feature_names = pred_cols

    # Get the top features and their thresholds from the tree
    split_features = []
    for node_id in range(tree.node_count):
        if tree.feature[node_id] != -2:  # not a leaf
            feat_idx = tree.feature[node_id]
            threshold = tree.threshold[node_id]
            feat_name = feature_names[feat_idx]
            # Check direction: which side has more AI trades?
            left_ai = tree.value[tree.children_left[node_id]][0][1]
            right_ai = tree.value[tree.children_right[node_id]][0][1]
            left_total = sum(tree.value[tree.children_left[node_id]][0])
            right_total = sum(tree.value[tree.children_right[node_id]][0])
            left_pct = left_ai / left_total if left_total > 0 else 0
            right_pct = right_ai / right_total if right_total > 0 else 0

            split_features.append({
                'feature': feat_name,
                'threshold': threshold,
                'left_ai_pct': left_pct,
                'right_ai_pct': right_pct,
                'depth': 0,  # simplified
                'importance': dict(importances).get(feat_name, 0),
            })

    # Sort by importance
    split_features.sort(key=lambda x: x['importance'], reverse=True)

    print(f"\nTree split points (sorted by importance):")
    for sf in split_features[:8]:
        direction = "<=" if sf['left_ai_pct'] > sf['right_ai_pct'] else ">"
        print(f"  {sf['feature']:<35} {direction} {sf['threshold']:.4f}  "
              f"(left AI: {sf['left_ai_pct']:.1%}, right AI: {sf['right_ai_pct']:.1%})")

    # Build simple scoring function from top splits
    top_splits = split_features[:5]

    def score_date(row):
        score = 0
        for sf in top_splits:
            val = row.get(sf['feature'], np.nan)
            if pd.isna(val):
                continue
            if sf['left_ai_pct'] > sf['right_ai_pct']:
                if val <= sf['threshold']:
                    score += 1
            else:
                if val > sf['threshold']:
                    score += 1
        return score

    # Test different thresholds
    print(f"\n--- Filter Performance at Different Thresholds ---")
    best_f1 = 0
    best_threshold = 3

    full_df = pd.concat([train, test])

    for threshold in range(1, 6):
        train_scores = train.apply(score_date, axis=1)
        test_scores = test.apply(score_date, axis=1)

        train_pred = (train_scores >= threshold).astype(int)
        test_pred = (test_scores >= threshold).astype(int)

        if test_pred.sum() == 0:
            continue

        train_prec = precision_score(train['ai_traded'], train_pred, zero_division=0)
        train_rec = recall_score(train['ai_traded'], train_pred, zero_division=0)
        test_prec = precision_score(test['ai_traded'], test_pred, zero_division=0)
        test_rec = recall_score(test['ai_traded'], test_pred, zero_division=0)
        test_f1 = 2 * test_prec * test_rec / (test_prec + test_rec) if (test_prec + test_rec) > 0 else 0

        # Naive expectancy on flagged dates
        test_flagged = test[test_scores >= threshold]
        test_not_flagged = test[test_scores < threshold]

        flagged_exp = test_flagged['naive_r_1r'].mean() if len(test_flagged) > 0 else 0
        not_flagged_exp = test_not_flagged['naive_r_1r'].mean() if len(test_not_flagged) > 0 else 0

        print(f"  Threshold >= {threshold}: "
              f"Train P={train_prec:.2f}/R={train_rec:.2f} | "
              f"Test P={test_prec:.2f}/R={test_rec:.2f}/F1={test_f1:.2f} | "
              f"Flagged: {test_pred.sum()}/{len(test)} | "
              f"Exp flagged={flagged_exp:+.3f}R vs not={not_flagged_exp:+.3f}R")

        if test_f1 > best_f1:
            best_f1 = test_f1
            best_threshold = threshold

    print(f"\n  Best threshold: >= {best_threshold} (F1={best_f1:.3f})")

    return top_splits, best_threshold, score_date

def validate_phase1(df_p1, score_fn, threshold, top_splits, pred_cols):
    """Step 5: Validate on Phase 1 dates."""
    print(f"\n{'='*70}")
    print(f"PHASE 1 VALIDATION")
    print(f"{'='*70}")

    if len(df_p1) == 0:
        print("  No Phase 1 feature data available for validation.")
        return

    scores = df_p1.apply(score_fn, axis=1)
    flagged = scores >= threshold

    total = len(df_p1)
    ai_traded = df_p1['ai_traded'].sum()
    flagged_count = flagged.sum()

    # How many AI dates flagged?
    ai_rows = df_p1[df_p1['ai_traded'] == 1]
    ai_flagged = flagged[df_p1['ai_traded'] == 1].sum()

    print(f"Total Phase 1 rows: {total}")
    print(f"AI traded: {ai_traded}")
    print(f"Filter flagged: {flagged_count} ({flagged_count/total*100:.1f}%)")
    print(f"AI dates captured: {ai_flagged}/{ai_traded} ({ai_flagged/ai_traded*100:.1f}% recall)" if ai_traded > 0 else "")

    if flagged_count > 0:
        precision = ai_flagged / flagged_count
        print(f"Precision: {precision:.2f}")

        # Expectancy
        flagged_exp = df_p1[flagged]['naive_r_1r'].mean() if 'naive_r_1r' in df_p1.columns else 'N/A'
        not_flagged_exp = df_p1[~flagged]['naive_r_1r'].mean() if 'naive_r_1r' in df_p1.columns and (~flagged).sum() > 0 else 'N/A'
        print(f"Expectancy: flagged={flagged_exp}, not flagged={not_flagged_exp}")

def mechanism_analysis(df):
    """Step 6: Why AI dates are special (using forward-looking features)."""
    from scipy import stats

    print(f"\n{'='*70}")
    print(f"MECHANISM ANALYSIS")
    print(f"{'='*70}")

    ai = df[df['ai_traded'] == 1]
    non_ai = df[df['ai_traded'] == 0]

    explanatory = ['kz_displacements', 'kz_max_alignment', 'kz_any_sweep_fvg',
                   'kz_strongest_body_ratio', 'kz_max_cont_1h']

    print(f"\n--- Forward-Looking Features (What happens DURING the KZ) ---")
    for feat in explanatory:
        if feat not in df.columns:
            continue
        ai_vals = pd.to_numeric(ai[feat], errors='coerce').dropna().astype(float)
        non_vals = pd.to_numeric(non_ai[feat], errors='coerce').dropna().astype(float)
        if len(ai_vals) < 3 or len(non_vals) < 3:
            continue
        t, p = stats.ttest_ind(ai_vals, non_vals, equal_var=False)
        print(f"  {feat:<30} AI={ai_vals.mean():.3f}  Non-AI={non_vals.mean():.3f}  p={p:.4f}")

    # Feature × outcome interaction
    print(f"\n--- Feature × Outcome Interaction (Top 5 predictive) ---")
    top_feats = ['pre_kz_range_pct_adr', 'h4_trend_strength', 'consolidation_score',
                 'd1_range_vs_adr', 'nearest_level_distance_pct']

    for feat in top_feats:
        if feat not in df.columns:
            continue
        median_val = df[feat].median()

        fav = df[df[feat] <= median_val] if feat in ['pre_kz_range_pct_adr', 'd1_range_vs_adr',
                                                       'nearest_level_distance_pct', 'consolidation_score'] \
              else df[df[feat] > median_val]
        unfav = df[~df.index.isin(fav.index)]

        fav_ai = fav[fav['ai_traded'] == 1]['naive_r_1r'].mean() if (fav['ai_traded'] == 1).sum() > 0 else np.nan
        fav_nonai = fav[fav['ai_traded'] == 0]['naive_r_1r'].mean() if (fav['ai_traded'] == 0).sum() > 0 else np.nan
        unfav_ai = unfav[unfav['ai_traded'] == 1]['naive_r_1r'].mean() if (unfav['ai_traded'] == 1).sum() > 0 else np.nan
        unfav_nonai = unfav[unfav['ai_traded'] == 0]['naive_r_1r'].mean() if (unfav['ai_traded'] == 0).sum() > 0 else np.nan

        print(f"\n  {feat} (median={median_val:.4f}):")
        print(f"    Favorable + AI traded:     {fav_ai:+.3f}R  (n={((fav['ai_traded']==1)).sum()})")
        print(f"    Favorable + NOT traded:    {fav_nonai:+.3f}R  (n={((fav['ai_traded']==0)).sum()})")
        print(f"    Unfavorable + AI traded:   {unfav_ai:+.3f}R  (n={((unfav['ai_traded']==1)).sum()})")
        print(f"    Unfavorable + NOT traded:  {unfav_nonai:+.3f}R  (n={((unfav['ai_traded']==0)).sum()})")

###############################################################################
# MAIN
###############################################################################

def main():
    print("="*70)
    print("REVERSE-ENGINEER AI DATE SELECTION")
    print("="*70)

    # Load data
    print("\n[1/7] Loading data...")
    price_dfs = load_price_data()
    p0_data = load_phase0()
    p1_responses = load_phase1_pa_responses()
    p1_trades = load_phase1_trades()
    disp_db = load_displacement_db()

    print(f"  M15: {len(price_dfs['M15'])} rows")
    print(f"  D1: {len(price_dfs['D1'])} rows")
    print(f"  Phase 0: {len(p0_data)} rows")
    print(f"  Phase 1 PA responses: {len(p1_responses)}")
    print(f"  Phase 1 trades: {len(p1_trades)}")
    print(f"  Displacement DB: {len(disp_db)} events")

    # Build feature matrix (per-KZ approach)
    print("\n[2/7] Building feature matrix (per-KZ approach)...")
    df = build_feature_matrix(p0_data, price_dfs, disp_db, approach='per_kz')
    print(f"  Feature matrix: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  AI traded: {df['ai_traded'].sum()} ({df['ai_traded'].mean()*100:.1f}%)")

    # Save feature matrix
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    csv_path = ANALYSIS_DIR / f"date_selection_features_{ts}.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path}")

    # Exploratory analysis
    print("\n[3/7] Exploratory analysis...")
    feat_results, top_pred = exploratory_analysis(df)

    # Predictive features only
    predictive_feats = [r['feature'] for r in feat_results if r['type'] == 'PREDICTIVE']

    # Build models
    print("\n[4/7] Building models...")
    dt, lr, scaler, pred_cols, train, test, dt_imp, lr_coefs = build_models(df, predictive_feats)

    # Simple filter
    print("\n[4D/7] Building simple rule-based filter...")
    top_splits, best_threshold, score_fn = build_simple_filter(df, dt, pred_cols, dt_imp, train, test)

    # Phase 1 validation
    print("\n[5/7] Phase 1 validation...")
    # Build Phase 1 feature matrix
    p1_trade_dates = set(t['date'] for t in p1_trades)
    p1_pa_dates = defaultdict(dict)
    for r in p1_responses:
        date = r['date']
        kz = r.get('kz', 'london')
        traded = r.get('decision', 'NO_TRADE') != 'NO_TRADE'
        p1_pa_dates[(date, kz)] = traded

    # Build p1 equivalent of p0 data for feature computation
    p1_rows = []
    for (date, kz), traded in p1_pa_dates.items():
        # Only include dates NOT in Phase 0 (for true out-of-sample)
        p0_dates = set(r['date'] for r in p0_data)
        if date in p0_dates:
            continue

        # Get approximate D1 direction
        d1_df = price_dfs['D1']
        d1_prior = d1_df[d1_df['time'] < pd.Timestamp(date)].tail(1)
        if len(d1_prior) == 0:
            continue
        d1_dir = 'bullish' if d1_prior.iloc[-1]['close'] > d1_prior.iloc[-1]['open'] else 'bearish'

        # Get entry price (approximate from M15)
        m15 = price_dfs['M15']
        dt_ts = pd.Timestamp(date)
        if kz == 'london':
            kz_start = dt_ts + pd.Timedelta(hours=7)
        else:
            kz_start = dt_ts + pd.Timedelta(hours=13)
        kz_candles = m15[(m15['time'] >= kz_start) & (m15['time'] <= kz_start + pd.Timedelta(hours=1))]
        entry = kz_candles.iloc[0]['open'] if len(kz_candles) > 0 else 0

        p1_rows.append({
            'date': date,
            'kz': kz,
            'd1_direction': d1_dir,
            'trade_direction': 'long' if d1_dir == 'bullish' else 'short',
            'entry_price': entry,
            'ai_traded': traded or (date in p1_trade_dates),
            'strategy_a': {'outcomes': {'tp_1.0r': {'final_r': 0}}},
        })

    if p1_rows:
        print(f"  Building Phase 1 features for {len(p1_rows)} non-overlapping date-KZ combos...")
        df_p1 = build_feature_matrix(p1_rows, price_dfs, disp_db, approach='per_kz')
        validate_phase1(df_p1, score_fn, best_threshold, top_splits, pred_cols)
    else:
        print("  No non-overlapping Phase 1 dates available.")
        df_p1 = pd.DataFrame()

    # Mechanism analysis
    print("\n[6/7] Mechanism analysis...")
    mechanism_analysis(df)

    # Save results
    print("\n[7/7] Saving results...")
    results_data = {
        'feature_comparison': feat_results,
        'dt_feature_importance': [(f, float(i)) for f, i in dt_imp],
        'lr_coefficients': [(f, float(c)) for f, c in lr_coefs],
        'filter_rules': [{'feature': s['feature'], 'threshold': float(s['threshold']),
                          'direction': '<=' if s['left_ai_pct'] > s['right_ai_pct'] else '>',
                          'importance': float(s['importance'])} for s in top_splits],
        'best_threshold': best_threshold,
        'train_dates': {'start': train['date'].min(), 'end': train['date'].max(), 'n': len(train)},
        'test_dates': {'start': test['date'].min(), 'end': test['date'].max(), 'n': len(test)},
    }

    json_path = ANALYSIS_DIR / f"date_selection_model_{ts}.json"
    with open(json_path, 'w') as f:
        json.dump(results_data, f, indent=2, default=str)
    print(f"  Saved: {json_path}")

    return df, dt, lr, feat_results, top_splits, best_threshold, df_p1

if __name__ == '__main__':
    df, dt, lr, feat_results, top_splits, best_threshold, df_p1 = main()
