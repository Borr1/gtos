#!/usr/bin/env python3
"""Phase 3: Enriched Trade Analysis + Phase 4: Cross-Analysis."""
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

# Load enriched trades
with open(OUT / 'trade_index_enriched.json') as f:
    enrich_data = json.load(f)
trades = enrich_data['trades']
xau_trades = [t for t in trades if t['symbol'] == 'XAUUSD']

# Load M15 data
m15_data = {}
with open(BASE / 'data' / 'historical' / 'XAUUSD_M15.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        m15_data[row['time']] = row

# Load displacement DB
with open(KB / 'analysis' / 'XAUUSD_displacement_database_20260403_1003.csv') as f:
    reader = csv.DictReader(f)
    displacements = list(reader)

###############################################################################
# 3A: MFE Time-Profile (Candle Walk)
###############################################################################
def mfe_time_profile():
    """Walk forward 12 M15 candles from entry for each trade."""
    results = []
    winners = []
    losers = []

    m15_times = sorted(m15_data.keys())

    for t in xau_trades:
        entry_time = t.get('entry_time', '')
        direction = t.get('direction')
        if not entry_time or not direction:
            continue

        # Clean entry time
        et = entry_time.replace('Z', '').replace('T', ' ').replace('+00:00', '')

        # Find the M15 candle at or just before entry
        if et in m15_data:
            entry_candle = m15_data[et]
        else:
            # Find closest M15 candle before entry
            entry_dt = datetime.fromisoformat(et)
            closest = None
            for mt in m15_times:
                mt_dt = datetime.fromisoformat(mt)
                if mt_dt <= entry_dt:
                    closest = mt
                else:
                    break
            if closest is None:
                continue
            entry_candle = m15_data[closest]
            et = closest

        entry_price = float(entry_candle['close'])
        entry_idx = m15_times.index(et)

        # Get next 12 candles
        if entry_idx + 12 >= len(m15_times):
            continue

        candles = []
        for i in range(1, 13):
            c = m15_data[m15_times[entry_idx + i]]
            candles.append(c)

        # Compute MFE/MAE at each candle
        mfe_profile = []
        mae_profile = []
        is_winner = t['outcome'] == 'WIN'

        for n in range(1, 13):
            subset = candles[:n]
            highs = [float(c['high']) for c in subset]
            lows = [float(c['low']) for c in subset]

            if direction == 'LONG':
                mfe = max(highs) - entry_price
                mae = entry_price - min(lows)
            else:  # SHORT
                mfe = entry_price - min(lows)
                mae = max(highs) - entry_price

            mfe_profile.append(mfe)
            mae_profile.append(mae)

        # Convert to R-multiples using mfe_r from trade index
        mfe_r = t.get('mfe_r', 0)
        if mfe_r and mfe_r > 0 and mfe_profile[-1] > 0:
            # SL distance = actual_max_mfe_price / mfe_r
            sl_dist = max(mfe_profile) / mfe_r if mfe_r > 0 else None
        else:
            sl_dist = None

        rec = {
            'trade_id': t['trade_id'],
            'direction': direction,
            'outcome': t['outcome'],
            'r_multiple': t['r_multiple'],
            'entry_price': entry_price,
            'sl_dist_estimate': sl_dist,
            'mfe_price_profile': [round(m, 2) for m in mfe_profile],
            'mae_price_profile': [round(m, 2) for m in mae_profile],
        }

        if sl_dist and sl_dist > 0:
            rec['mfe_r_profile'] = [round(m / sl_dist, 4) for m in mfe_profile]
            rec['mae_r_profile'] = [round(m / sl_dist, 4) for m in mae_profile]
        else:
            rec['mfe_r_profile'] = None
            rec['mae_r_profile'] = None

        results.append(rec)
        if is_winner:
            winners.append(rec)
        else:
            losers.append(rec)

    # Compute average profiles
    def avg_profile(recs, key):
        profiles = [r[key] for r in recs if r[key] is not None]
        if not profiles:
            return None
        return [round(np.mean([p[i] for p in profiles if i < len(p)]), 4) for i in range(12)]

    avg_mfe_w = avg_profile(winners, 'mfe_r_profile')
    avg_mae_w = avg_profile(winners, 'mae_r_profile')
    avg_mfe_l = avg_profile(losers, 'mfe_r_profile')
    avg_mae_l = avg_profile(losers, 'mae_r_profile')

    # Key questions
    peak_mfe_candle_w = None
    if avg_mfe_w:
        peak_mfe_candle_w = avg_mfe_w.index(max(avg_mfe_w)) + 1

    mae_05r_candle_l = None
    if avg_mae_l:
        for i, m in enumerate(avg_mae_l):
            if m >= 0.5:
                mae_05r_candle_l = i + 1
                break

    # BE Stop Optimization
    be_results = {}
    all_with_profiles = [r for r in results if r['mfe_r_profile'] is not None]

    for trigger in [0.5, 0.75, 1.0, 1.25, 1.5]:
        winners_stopped_be = 0
        losers_saved = 0
        total_effect = 0

        for r in all_with_profiles:
            mfe_p = r['mfe_r_profile']
            mae_p = r['mae_r_profile']
            original_r = r['r_multiple']
            is_winner = r['outcome'] == 'WIN'

            # Did MFE hit trigger?
            hit_trigger = any(m >= trigger for m in mfe_p)
            if not hit_trigger:
                continue

            # Find candle where trigger was hit
            trigger_candle = None
            for i, m in enumerate(mfe_p):
                if m >= trigger:
                    trigger_candle = i
                    break

            # After hitting trigger, did price retrace to entry (0R)?
            # Check MAE after trigger candle
            if trigger_candle is not None and trigger_candle < 11:
                post_trigger_mae = max(mae_p[trigger_candle:])
                post_trigger_mfe = max(mfe_p[trigger_candle:])

                # If MAE after trigger exceeds MFE at trigger, it retraced to entry
                retraced = post_trigger_mae >= mfe_p[trigger_candle]

                if retraced:
                    if is_winner:
                        winners_stopped_be += 1
                        total_effect += (0 - original_r)  # Lost the win, got 0 instead
                    else:
                        losers_saved += 1
                        total_effect += (0 - original_r)  # Saved from loss, got 0 instead of negative

        n_triggered = sum(1 for r in all_with_profiles if any(m >= trigger for m in r['mfe_r_profile']))

        be_results[trigger] = {
            'trigger_r': trigger,
            'trades_hitting_trigger': n_triggered,
            'winners_stopped_at_be': winners_stopped_be,
            'losers_saved': losers_saved,
            'net_r_effect': round(total_effect, 4),
            'effect_per_trade': round(total_effect / len(all_with_profiles), 4) if all_with_profiles else 0,
        }

    return {
        'n_trades_analyzed': len(results),
        'n_winners': len(winners),
        'n_losers': len(losers),
        'avg_mfe_r_winners': avg_mfe_w,
        'avg_mae_r_winners': avg_mae_w,
        'avg_mfe_r_losers': avg_mfe_l,
        'avg_mae_r_losers': avg_mae_l,
        'peak_mfe_candle_winners': peak_mfe_candle_w,
        'loser_mae_05r_candle': mae_05r_candle_l,
        'mfe_at_candle_4_winners': avg_mfe_w[3] if avg_mfe_w and len(avg_mfe_w) > 3 else None,
        'mfe_at_candle_4_losers': avg_mfe_l[3] if avg_mfe_l and len(avg_mfe_l) > 3 else None,
        'be_stop_optimization': be_results,
    }

###############################################################################
# 3B: First-Candle Momentum
###############################################################################
def first_candle_momentum():
    """Analyze first M15 candle after entry."""
    results = []
    m15_times = sorted(m15_data.keys())

    for t in xau_trades:
        entry_time = t.get('entry_time', '')
        direction = t.get('direction')
        if not entry_time or not direction:
            continue

        et = entry_time.replace('Z', '').replace('T', ' ').replace('+00:00', '')

        if et in m15_data:
            entry_idx = m15_times.index(et)
        else:
            entry_dt = datetime.fromisoformat(et)
            closest = None
            for mt in m15_times:
                if datetime.fromisoformat(mt) <= entry_dt:
                    closest = mt
            if closest is None:
                continue
            entry_idx = m15_times.index(closest)

        if entry_idx + 1 >= len(m15_times):
            continue

        entry_price = float(m15_data[m15_times[entry_idx]]['close'])
        next_candle = m15_data[m15_times[entry_idx + 1]]

        if direction == 'LONG':
            first_move = float(next_candle['close']) - entry_price
        else:
            first_move = entry_price - float(next_candle['close'])

        # Estimate SL distance (same as 3A approach)
        mfe_r = t.get('mfe_r', 0)
        # Use a rough SL estimate based on typical gold SL (3-5 dollars)
        sl_dist = 4.0  # Default rough estimate for gold

        first_r = first_move / sl_dist if sl_dist > 0 else 0

        results.append({
            'trade_id': t['trade_id'],
            'outcome': t['outcome'],
            'direction': direction,
            'first_candle_r_move': round(first_r, 4),
            'first_candle_price_move': round(first_move, 2),
            'is_winner': t['outcome'] == 'WIN',
        })

    winners = [r for r in results if r['is_winner']]
    losers = [r for r in results if not r['is_winner']]

    w_moves = [r['first_candle_r_move'] for r in winners]
    l_moves = [r['first_candle_r_move'] for r in losers]

    # Adverse first candle analysis
    adverse_trades = [r for r in results if r['first_candle_r_move'] < -0.1]
    if adverse_trades:
        adverse_wr = sum(1 for r in adverse_trades if r['is_winner']) / len(adverse_trades)
    else:
        adverse_wr = None

    return {
        'n_analyzed': len(results),
        'winner_first_candle_r': {
            'mean': round(np.mean(w_moves), 4) if w_moves else None,
            'median': round(float(np.median(w_moves)), 4) if w_moves else None,
            'pct_favorable_gt_02r': round(sum(1 for m in w_moves if m > 0.2) / len(w_moves), 4) if w_moves else None,
        },
        'loser_first_candle_r': {
            'mean': round(np.mean(l_moves), 4) if l_moves else None,
            'median': round(float(np.median(l_moves)), 4) if l_moves else None,
            'pct_adverse_gt_02r': round(sum(1 for m in l_moves if m < -0.2) / len(l_moves), 4) if l_moves else None,
        },
        'adverse_first_candle_analysis': {
            'threshold': -0.1,
            'n_adverse': len(adverse_trades),
            'win_rate_if_adverse': round(adverse_wr, 4) if adverse_wr is not None else None,
        }
    }

###############################################################################
# 3C: Lasso Logistic Regression
###############################################################################
def feature_redundancy():
    """Lasso logistic regression on trade-displacement linked data."""
    linked_file = OUT / 'trade_displacement_linked.json'
    with open(linked_file) as f:
        linked_data = json.load(f)
    linked_trades = linked_data['trades']

    if len(linked_trades) < 30:
        return {'insufficient_data': True, 'n': len(linked_trades)}

    # Define outcome fields to exclude
    outcome_fields = {
        'cont_1h', 'cont_3h', 'cont_session',
        'mfe_1h', 'mfe_3h', 'mfe_sess',
        'mae_1h', 'mae_3h', 'mae_sess',
        'net_1h', 'net_3h', 'net_sess',
        'mfe_1h_bm', 'mfe_3h_bm',
        'revisit_continued', 'revisit_mfe', 'revisit_candles', 'revisit_depth',
        'nc_body_ratio', 'nc_cont_pct', 'nc_dir', 'nc_rej_wick',
        'origin_revisited',
    }
    metadata_fields = {
        'date', 'timestamp', 'symbol', 'set', 'open', 'high', 'low', 'close', 'volume',
        '_ts', '_cont_3h',
    }

    # Build feature matrix from displacement fields
    feature_names = []
    feature_matrix = []
    outcomes = []

    for t in linked_trades:
        disp = t.get('displacement_fields', {})
        if not disp:
            continue
        outcomes.append(1 if t['outcome'] == 'WIN' else 0)
        row = {}
        for k, v in disp.items():
            if k in outcome_fields or k in metadata_fields:
                continue
            if v is None or v == '' or v == 'None':
                row[k] = None
            else:
                try:
                    row[k] = float(v)
                except:
                    row[k] = v
        feature_matrix.append(row)

    if len(feature_matrix) < 30:
        return {'insufficient_data': True, 'n': len(feature_matrix)}

    # Find features with >80% non-null and >1 unique value
    all_keys = set()
    for row in feature_matrix:
        all_keys.update(row.keys())

    valid_features = []
    for k in all_keys:
        vals = [row.get(k) for row in feature_matrix]
        non_null = [v for v in vals if v is not None]
        if len(non_null) / len(vals) < 0.8:
            continue
        # Check if numeric
        nums = [v for v in non_null if isinstance(v, (int, float))]
        if len(nums) == len(non_null) and len(set(nums)) > 1:
            valid_features.append(k)
        elif len(set(non_null)) <= 10 and len(set(non_null)) > 1:
            # Categorical — will need encoding
            valid_features.append(k)

    # Build numpy arrays
    X_data = []
    y_data = []
    used_features = []

    for i, row in enumerate(feature_matrix):
        x_row = []
        skip = False
        for feat in valid_features:
            v = row.get(feat)
            if v is None:
                skip = True
                break
            if isinstance(v, (int, float)):
                x_row.append(float(v))
            elif isinstance(v, bool):
                x_row.append(1.0 if v else 0.0)
            elif isinstance(v, str):
                # Simple binary encode for True/False
                if v.lower() in ('true', 'yes'):
                    x_row.append(1.0)
                elif v.lower() in ('false', 'no'):
                    x_row.append(0.0)
                else:
                    skip = True
                    break
            else:
                skip = True
                break
        if not skip:
            X_data.append(x_row)
            y_data.append(outcomes[i])

    if len(X_data) < 30:
        return {'insufficient_data': True, 'n': len(X_data), 'features': len(valid_features)}

    X = np.array(X_data)
    y = np.array(y_data)

    # Standardize
    means = X.mean(axis=0)
    stds = X.std(axis=0)
    stds[stds == 0] = 1
    X_std = (X - means) / stds

    # Simple L1 logistic regression using coordinate descent
    # (avoiding sklearn dependency)
    from scipy.optimize import minimize

    def lasso_loss(w, X, y, lam):
        z = X @ w[:-1] + w[-1]
        z = np.clip(z, -500, 500)
        p = 1 / (1 + np.exp(-z))
        p = np.clip(p, 1e-10, 1-1e-10)
        nll = -np.mean(y * np.log(p) + (1-y) * np.log(1-p))
        l1 = lam * np.sum(np.abs(w[:-1]))
        return nll + l1

    n_features = X_std.shape[1]
    best_lam = 0.1  # Strong regularization given small n

    w0 = np.zeros(n_features + 1)
    result = minimize(lasso_loss, w0, args=(X_std, y, best_lam), method='L-BFGS-B')
    w = result.x

    # Non-zero coefficients
    coefs = w[:-1]
    non_zero = [(valid_features[i], round(float(coefs[i]), 4)) for i in range(n_features) if abs(coefs[i]) > 0.01]
    non_zero.sort(key=lambda x: abs(x[1]), reverse=True)
    zeroed = [valid_features[i] for i in range(n_features) if abs(coefs[i]) <= 0.01]

    # Cross-validation accuracy (simple 5-fold)
    from numpy.random import RandomState
    rs = RandomState(42)
    indices = rs.permutation(len(X_std))
    fold_size = len(X_std) // 5
    cv_accs = []

    for fold in range(5):
        test_idx = indices[fold*fold_size:(fold+1)*fold_size]
        train_idx = np.concatenate([indices[:fold*fold_size], indices[(fold+1)*fold_size:]])

        X_train, X_test = X_std[train_idx], X_std[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        w0 = np.zeros(n_features + 1)
        result = minimize(lasso_loss, w0, args=(X_train, y_train, best_lam), method='L-BFGS-B')
        w_cv = result.x

        z = X_test @ w_cv[:-1] + w_cv[-1]
        preds = (1 / (1 + np.exp(-np.clip(z, -500, 500)))) >= 0.5
        acc = np.mean(preds == y_test)
        cv_accs.append(acc)

    cv_acc = np.mean(cv_accs)

    # In-sample accuracy
    z = X_std @ w[:-1] + w[-1]
    preds = (1 / (1 + np.exp(-np.clip(z, -500, 500)))) >= 0.5
    in_sample_acc = np.mean(preds == y)

    return {
        'n_trades': len(X_data),
        'n_features_tested': n_features,
        'lambda': best_lam,
        'non_zero_coefficients': non_zero,
        'zeroed_out_features': zeroed,
        'n_non_zero': len(non_zero),
        'n_zeroed': len(zeroed),
        'cv_accuracy_5fold': round(float(cv_acc), 4),
        'in_sample_accuracy': round(float(in_sample_acc), 4),
        'cv_better_than_55pct': cv_acc > 0.55,
        'WARNING': 'n=59 with 20+ features is overfit-prone. CV accuracy is the real test.' if len(X_data) < 100 else None,
    }

###############################################################################
# 3D: Regime Classification
###############################################################################
def regime_analysis():
    """Classify market regimes from D1 data and tag trades."""
    d1_file = BASE / 'data' / 'historical' / 'XAUUSD_D1.csv'
    if not d1_file.exists():
        return {'error': 'D1 file not found'}

    with open(d1_file) as f:
        reader = csv.DictReader(f)
        d1_data = list(reader)

    # Compute ATR and regime for each day
    d1_by_date = {}
    ranges = []
    for i, row in enumerate(d1_data):
        h = float(row['high'])
        l = float(row['low'])
        c_prev = float(d1_data[i-1]['close']) if i > 0 else float(row['open'])
        tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
        ranges.append(tr)

        date = row['time'][:10]
        d1_by_date[date] = {
            'range': tr,
            'close': float(row['close']),
            'open': float(row['open']),
        }

    # Rolling 20-day ATR
    atr_20 = {}
    for i in range(19, len(d1_data)):
        date = d1_data[i]['time'][:10]
        atr = np.mean(ranges[i-19:i+1])
        atr_20[date] = atr

    # Classify regimes
    all_atrs = list(atr_20.values())
    atr_median = np.median(all_atrs) if all_atrs else 0

    regimes = {}
    for date, atr in atr_20.items():
        vol_regime = 'high_vol' if atr > atr_median else 'low_vol'

        # Trend: rolling 20-day close change / ATR
        idx = next((i for i, r in enumerate(d1_data) if r['time'][:10] == date), None)
        if idx is not None and idx >= 20:
            trend_move = float(d1_data[idx]['close']) - float(d1_data[idx-20]['close'])
            trend_ratio = abs(trend_move) / atr if atr > 0 else 0
            trend_regime = 'trending' if trend_ratio > 1.5 else 'ranging'
        else:
            trend_regime = 'unknown'

        # Range regime
        if date in d1_by_date:
            day_range = d1_by_date[date]['range']
            avg_range = np.mean(ranges[max(0, idx-19):idx+1]) if idx else day_range
            range_regime = 'wide' if day_range > avg_range * 1.2 else 'normal'
        else:
            range_regime = 'unknown'

        regimes[date] = {
            'volatility': vol_regime,
            'trend': trend_regime,
            'range': range_regime,
        }

    # Tag trades with regimes
    regime_trades = defaultdict(lambda: {'n': 0, 'wins': 0, 'total_r': 0})

    for t in xau_trades:
        date = t['date']
        if date in regimes:
            for regime_type in ['volatility', 'trend', 'range']:
                bucket = regimes[date][regime_type]
                key = f"{regime_type}_{bucket}"
                regime_trades[key]['n'] += 1
                if t['outcome'] == 'WIN':
                    regime_trades[key]['wins'] += 1
                regime_trades[key]['total_r'] += t['r_multiple']

    # Compute stats and tests
    results = {}
    for key, v in regime_trades.items():
        if v['n'] > 0:
            results[key] = {
                'n': v['n'],
                'win_rate': round(v['wins'] / v['n'], 4),
                'mean_r': round(v['total_r'] / v['n'], 4),
                'total_r': round(v['total_r'], 4),
            }

    # Fisher exact for each regime pair
    tests = {}
    for regime_type in ['volatility', 'trend', 'range']:
        keys = [k for k in results if k.startswith(regime_type)]
        if len(keys) == 2:
            a_key, b_key = keys
            a = results[a_key]
            b = results[b_key]
            table = [[a['n'] * a['win_rate'], a['n'] - a['n'] * a['win_rate']],
                     [b['n'] * b['win_rate'], b['n'] - b['n'] * b['win_rate']]]
            table = [[int(round(x)) for x in row] for row in table]
            try:
                _, p = scipy_stats.fisher_exact(table)
                tests[regime_type] = {
                    'groups': keys,
                    'p_value': round(p, 4),
                    'significant_bonferroni': p < 0.05 / 3,
                }
            except:
                tests[regime_type] = {'groups': keys, 'p_value': 1.0}

    return {
        'regime_performance': results,
        'regime_tests': tests,
        'n_trades_tagged': sum(1 for t in xau_trades if t['date'] in regimes),
    }

###############################################################################
# 4A: h16-h17 Displacement Quality
###############################################################################
def h16_h17_analysis():
    """Check displacement quality by hour."""
    hour_buckets = defaultdict(lambda: {'n': 0, 'cont': 0, 'mfe_sum': 0})

    for d in displacements:
        ts = d.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '').replace('+00:00', ''))
            hour = dt.hour
        except:
            continue

        cont = 1 if str(d.get('cont_3h', '')).lower() in ('true', '1') else 0
        mfe = float(d.get('mfe_3h', 0) or 0)

        hour_buckets[hour]['n'] += 1
        hour_buckets[hour]['cont'] += cont
        hour_buckets[hour]['mfe_sum'] += mfe

    results = {}
    for h in sorted(hour_buckets.keys()):
        v = hour_buckets[h]
        results[f'h{h:02d}'] = {
            'n': v['n'],
            'cont_rate': round(v['cont'] / v['n'], 4) if v['n'] > 0 else 0,
            'avg_mfe': round(v['mfe_sum'] / v['n'], 4) if v['n'] > 0 else 0,
        }

    # Compare h13-h15 vs h16-h17
    ny_kz = {'cont': 0, 'n': 0, 'mfe': 0}
    post_kz = {'cont': 0, 'n': 0, 'mfe': 0}

    for h in [13, 14, 15]:
        b = hour_buckets.get(h, {'n': 0, 'cont': 0, 'mfe_sum': 0})
        ny_kz['n'] += b['n']
        ny_kz['cont'] += b['cont']
        ny_kz['mfe'] += b['mfe_sum']

    for h in [16, 17]:
        b = hour_buckets.get(h, {'n': 0, 'cont': 0, 'mfe_sum': 0})
        post_kz['n'] += b['n']
        post_kz['cont'] += b['cont']
        post_kz['mfe'] += b['mfe_sum']

    comparison = {
        'h13_h15': {
            'n': ny_kz['n'],
            'cont_rate': round(ny_kz['cont'] / ny_kz['n'], 4) if ny_kz['n'] > 0 else 0,
            'avg_mfe': round(ny_kz['mfe'] / ny_kz['n'], 4) if ny_kz['n'] > 0 else 0,
        },
        'h16_h17': {
            'n': post_kz['n'],
            'cont_rate': round(post_kz['cont'] / post_kz['n'], 4) if post_kz['n'] > 0 else 0,
            'avg_mfe': round(post_kz['mfe'] / post_kz['n'], 4) if post_kz['n'] > 0 else 0,
        }
    }

    # Fisher exact
    if ny_kz['n'] > 0 and post_kz['n'] > 0:
        table = [[ny_kz['cont'], ny_kz['n'] - ny_kz['cont']],
                 [post_kz['cont'], post_kz['n'] - post_kz['cont']]]
        _, p = scipy_stats.fisher_exact(table)
        comparison['fisher_p'] = round(p, 4)
        comparison['recommend_extension'] = p < 0.05 and comparison['h16_h17']['cont_rate'] >= comparison['h13_h15']['cont_rate']

    return {
        'hourly_breakdown': results,
        'ny_kz_vs_post_kz': comparison,
    }

###############################################################################
# 4B+4C: Quick cross-analyses
###############################################################################
def ob_feature_ranking():
    """Phase 4C: Extract OB comprehensive feature ranking."""
    ob_comp = KB / 'analysis' / 'ob_comprehensive_analysis_20260403.json'
    if not ob_comp.exists():
        # Try other names
        candidates = list((KB / 'analysis').glob('ob_comprehensive*.json'))
        if candidates:
            ob_comp = candidates[0]
        else:
            return {'error': 'OB comprehensive file not found'}

    with open(ob_comp) as f:
        ob_data = json.load(f)

    # Extract feature rankings
    if 'feature_analysis' in ob_data:
        return ob_data['feature_analysis']
    elif 'chi_squared_results' in ob_data:
        return ob_data['chi_squared_results']
    else:
        return {'keys': list(ob_data.keys())[:20]}

###############################################################################
# Main
###############################################################################
if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 3+4: ENRICHED TRADE + CROSS ANALYSIS")
    print("=" * 60)

    # 3A
    print("\n--- 3A: MFE Time-Profile ---")
    mfe = mfe_time_profile()
    print(f"  Trades analyzed: {mfe['n_trades_analyzed']} ({mfe['n_winners']}W / {mfe['n_losers']}L)")
    print(f"  Peak MFE candle (winners): {mfe['peak_mfe_candle_winners']}")
    print(f"  MFE at candle 4 (1hr): W={mfe['mfe_at_candle_4_winners']}, L={mfe['mfe_at_candle_4_losers']}")
    if mfe['be_stop_optimization']:
        print("  BE Stop Optimization:")
        for trig, r in mfe['be_stop_optimization'].items():
            print(f"    Trigger {trig}R: saved {r['losers_saved']}L, stopped {r['winners_stopped_at_be']}W, net R/trade={r['effect_per_trade']}")
    with open(OUT / 'mfe_time_profile_20260406.json', 'w') as f:
        json.dump(mfe, f, indent=2, default=str)

    # 3B
    print("\n--- 3B: First-Candle Momentum ---")
    fc = first_candle_momentum()
    print(f"  Winners first candle mean R: {fc['winner_first_candle_r']['mean']}")
    print(f"  Losers first candle mean R: {fc['loser_first_candle_r']['mean']}")
    print(f"  Adverse first candle WR: {fc['adverse_first_candle_analysis']['win_rate_if_adverse']}")
    with open(OUT / 'first_candle_momentum_20260406.json', 'w') as f:
        json.dump(fc, f, indent=2, default=str)

    # 3C
    print("\n--- 3C: Feature Redundancy (Lasso) ---")
    fr = feature_redundancy()
    print(f"  n={fr.get('n_trades')}, features={fr.get('n_features_tested')}")
    print(f"  CV accuracy: {fr.get('cv_accuracy_5fold')}")
    print(f"  Non-zero coefs: {fr.get('n_non_zero')}")
    if fr.get('non_zero_coefficients'):
        for name, coef in fr['non_zero_coefficients'][:5]:
            print(f"    {name}: {coef}")
    with open(OUT / 'feature_redundancy_20260406.json', 'w') as f:
        json.dump(fr, f, indent=2, default=str)

    # 3D
    print("\n--- 3D: Regime Analysis ---")
    reg = regime_analysis()
    for k, v in sorted(reg.get('regime_performance', {}).items()):
        print(f"  {k}: n={v['n']}, WR={v['win_rate']}, mean_R={v['mean_r']}")
    for k, v in reg.get('regime_tests', {}).items():
        print(f"  {k} test: p={v['p_value']}")
    with open(OUT / 'regime_analysis_20260406.json', 'w') as f:
        json.dump(reg, f, indent=2, default=str)

    # 4A
    print("\n--- 4A: h16-h17 Quality ---")
    h16 = h16_h17_analysis()
    comp = h16.get('ny_kz_vs_post_kz', {})
    if comp:
        print(f"  h13-h15: n={comp.get('h13_h15',{}).get('n')}, cont={comp.get('h13_h15',{}).get('cont_rate')}")
        print(f"  h16-h17: n={comp.get('h16_h17',{}).get('n')}, cont={comp.get('h16_h17',{}).get('cont_rate')}")
        print(f"  Fisher p: {comp.get('fisher_p')}")
    with open(OUT / 'h16_h17_analysis_20260406.json', 'w') as f:
        json.dump(h16, f, indent=2, default=str)

    # 4C
    print("\n--- 4C: OB Feature Ranking ---")
    ob_rank = ob_feature_ranking()
    with open(OUT / 'ob_feature_ranking_20260406.json', 'w') as f:
        json.dump(ob_rank, f, indent=2, default=str)
    if isinstance(ob_rank, dict) and 'error' not in ob_rank:
        print(f"  Extracted OB feature data")
    else:
        print(f"  {ob_rank}")

    # Write MFE markdown
    md = f"""# Phase 3: MFE Time-Profile — {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 3A: MFE Time-Profile
- Trades analyzed: {mfe['n_trades_analyzed']} ({mfe['n_winners']}W / {mfe['n_losers']}L)
- Peak MFE candle (winners): candle {mfe['peak_mfe_candle_winners']}
- MFE at candle 4 (1hr): Winners={mfe['mfe_at_candle_4_winners']}, Losers={mfe['mfe_at_candle_4_losers']}

### Average MFE/MAE Profile (R-multiples)
| Candle | Winner MFE | Winner MAE | Loser MFE | Loser MAE |
|--------|-----------|-----------|----------|----------|
"""
    if mfe['avg_mfe_r_winners']:
        for i in range(12):
            md += f"| {i+1} | {mfe['avg_mfe_r_winners'][i] if i < len(mfe['avg_mfe_r_winners']) else 'N/A'} | {mfe['avg_mae_r_winners'][i] if mfe['avg_mae_r_winners'] and i < len(mfe['avg_mae_r_winners']) else 'N/A'} | {mfe['avg_mfe_r_losers'][i] if mfe['avg_mfe_r_losers'] and i < len(mfe['avg_mfe_r_losers']) else 'N/A'} | {mfe['avg_mae_r_losers'][i] if mfe['avg_mae_r_losers'] and i < len(mfe['avg_mae_r_losers']) else 'N/A'} |\n"

    md += "\n### BE Stop Optimization\n| Trigger | Trades Hit | Winners Stopped | Losers Saved | Net R/Trade |\n|---------|-----------|----------------|-------------|------------|\n"
    for trig, r in mfe['be_stop_optimization'].items():
        md += f"| {trig}R | {r['trades_hitting_trigger']} | {r['winners_stopped_at_be']} | {r['losers_saved']} | {r['effect_per_trade']} |\n"

    md += f"""
## 3C: Feature Redundancy (Lasso)
- n={fr.get('n_trades')}, features={fr.get('n_features_tested')}
- CV accuracy (5-fold): {fr.get('cv_accuracy_5fold')}
- {'⚠️ CV accuracy < 55%: model is noise' if not fr.get('cv_better_than_55pct') else 'CV accuracy > 55%'}

## 3D: Regime Analysis
"""
    for k, v in sorted(reg.get('regime_performance', {}).items()):
        md += f"- {k}: n={v['n']}, WR={v['win_rate']:.1%}, mean_R={v['mean_r']}\n"

    with open(OUT / 'mfe_time_profile_20260406.md', 'w') as f:
        f.write(md)

    # Feature redundancy md
    with open(OUT / 'feature_redundancy_20260406.md', 'w') as f:
        f.write(md)  # Combined report

    # Regime md
    with open(OUT / 'regime_analysis_20260406.md', 'w') as f:
        f.write(md)

    print("\nPhases 3+4 complete.")
