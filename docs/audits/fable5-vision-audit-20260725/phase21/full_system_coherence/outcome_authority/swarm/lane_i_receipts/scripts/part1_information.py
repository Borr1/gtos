"""LANE I Part 1.2 — the feature-set information test.

Decisive question: do the 43 recorded predecision features contain information
about terminal_net_r that survives out of sample?

Capacity ladder, all on the identical row set and the identical frozen
selection protocol (proved equivalent in PART1_PROTOCOL_EQUIVALENCE.json):

  oracle_best / oracle_worst   perfect foresight        (ceiling / floor)
  gbm_is                       high-capacity, in-sample (feature-set ceiling)
  gbm_is_shuffled              same capacity, labels shuffled (capacity control)
  ridge_is                     frozen model class, in-sample
  gbm_cv_day                   same month, unseen day   (5-fold GroupKFold)
  gbm_oos                      prior months -> this month
  ridge_oos_frozen             the frozen rule's own prediction (pred_month_boundary)
  random                       no information at all    (null)

Primary instrument: MUST-TRADE, mixed policy. Every arm faces the identical
window set, so the only difference between arms is WHICH candidate is picked.
"""
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
sys.path.insert(0, "/tmp/lane_i")
import protocol as P

CAT = ['symbol','side','origin_family','utc_session','proposed_order_type','utc_hour','weekday',
       'symbol_x_family','family_x_session','symbol_x_side','poi_mitigation_status',
       'limit_marketable_at_decision','trend_state_m15','trend_transition_flag']
NUM = ['cost_r','spread_r','expected_slippage_r','swap_cost_r','commission_r','distance_to_limit_atr',
       'distance_to_limit_risk','risk_over_atr','risk_fraction_of_entry','poi_age_hours',
       'poi_distance_to_midpoint_atr','poi_distance_to_zone_atr','poi_touch_count',
       'poi_max_mitigation_fraction','poi_touch_episode_count','poi_overlap_bar_count',
       'atr14_over_atr50','stop_distance_atr','target_distance_atr','close_position_in_lookback_range',
       'dist_to_prior_high20_atr','dist_to_prior_low20_atr','trigger_bar_range_atr','trigger_bar_body_atr',
       'compression_ratio_prior_bar','bars_since_session_open','close_to_close_vol_8_over_48',
       'sweep_depth_atr','session_open_range_width_atr']
MONTHS = ["feb", "apr", "may", "jun", "jul"]
OUT = Path("/tmp/lane_i")
SEED = 20260811

df = pd.read_parquet(OUT / "pop.parquet")
df = df[df.eligible].reset_index(drop=True)
# global integer codes for the categoricals (HistGB native categorical support)
codes = {}
for c in CAT:
    cc = df[c].astype(str).astype("category")
    codes[c] = dict(enumerate(cc.cat.categories))
    df[c + "__code"] = cc.cat.codes.astype(np.int32)
XCOLS = [c + "__code" for c in CAT] + NUM
CATMASK = np.array([True] * len(CAT) + [False] * len(NUM))
X_ALL = df[XCOLS].to_numpy(dtype=np.float64)
Y_ALL = np.nan_to_num(df['terminal_net_r'].to_numpy(float), nan=0.0)   # frozen: `or 0.0`
RES = df['resolved'].to_numpy(bool)
FIL = df['lifecycle_label_status'].astype(str).str.startswith('RESOLVED_FILLED').to_numpy()
MONTH = df['month'].astype(str).to_numpy()
DAY = df['trading_day'].astype(str).to_numpy()
WID = df['decision_window_id'].astype(str).to_numpy()
W_ALL = pd.Series(WID).map(pd.Series(WID).value_counts()).rpow(1).to_numpy()
W_ALL = 1.0 / W_ALL  # 1/window-count, the frozen sample weight


def gbm(**kw):
    p = dict(loss="squared_error", max_iter=400, learning_rate=0.06, max_leaf_nodes=31,
             min_samples_leaf=20, l2_regularization=1.0, max_bins=255,
             categorical_features=CATMASK, early_stopping=False, random_state=SEED)
    p.update(kw)
    return HistGradientBoostingRegressor(**p)


def ridge_pipe():
    numeric = Pipeline([('impute', SimpleImputer(strategy='constant', fill_value=0.0, add_indicator=True)),
                        ('scale', StandardScaler())])
    return Pipeline([('pre', ColumnTransformer(
        [('cat', OneHotEncoder(handle_unknown='ignore'), list(range(len(CAT)))),
         ('num', numeric, list(range(len(CAT), len(XCOLS))))], sparse_threshold=0.3)),
        ('ridge', Ridge(alpha=10.0, solver='lsqr'))])


def fit_predict(kind, tr, te, y=None):
    yy = Y_ALL if y is None else y
    if kind.startswith("gbm"):
        cfg = {"is": dict(max_iter=800, max_leaf_nodes=63, min_samples_leaf=5, l2_regularization=0.0,
                          learning_rate=0.10),
               "reg": dict()}["is" if kind == "gbm_is" else "reg"]
        mdl = gbm(**cfg)
        mdl.fit(X_ALL[tr], yy[tr], sample_weight=W_ALL[tr])
        return mdl.predict(X_ALL[te])
    mdl = ridge_pipe()
    mdl.fit(X_ALL[tr], yy[tr], ridge__sample_weight=W_ALL[tr])
    return mdl.predict(X_ALL[te])


def skill(pred, idx):
    """Ranking skill on the FILLED rows of idx (where the economics are)."""
    sub = idx[FIL[idx]]
    p, y = pred[np.isin(idx, sub)], Y_ALL[sub]
    if len(sub) < 100:
        return {}
    rho = float(spearmanr(p, y).statistic)
    order = np.argsort(-p)
    n = len(sub)
    out = {"n_filled": int(n), "spearman_filled": round(rho, 5),
           "pop_mean_r": round(float(y.mean()), 5)}
    for frac, tag in [(0.01, "top1pct"), (0.05, "top5pct"), (0.10, "top10pct")]:
        k = max(20, int(n * frac))
        out[tag + "_mean_r"] = round(float(y[order[:k]].mean()), 5)
        out[tag + "_lift_r"] = round(float(y[order[:k]].mean() - y.mean()), 5)
    k = max(20, int(n * 0.10))
    out["bottom10pct_mean_r"] = round(float(y[order[-k:]].mean()), 5)
    out["decile_spread_r"] = round(out["top10pct_mean_r"] - out["bottom10pct_mean_r"], 5)
    return out


report = {"schema": "gtos.lane_i.feature_information_test.v1", "seed": SEED,
          "features": {"categorical": CAT, "numeric": NUM, "count": len(CAT) + len(NUM)},
          "months": {}}
rng = np.random.default_rng(SEED)
t0 = time.time()

for m in MONTHS:
    te = np.flatnonzero(MONTH == m)
    d = df.iloc[te].reset_index(drop=True)
    end = d['label_span_end_utc'].fillna(d['expiry_utc'])
    arrays = {'symbol': d['symbol'].astype(str).to_numpy(), 'end': end.to_numpy(),
              'cost_r': d['cost_r'].to_numpy(float),
              'key': d['candidate_occurrence_key'].astype(str).to_numpy(),
              'is_market': (d['proposed_order_type'].astype(str) == 'MARKET').to_numpy(),
              'resolved': RES[te], 'filled': FIL[te],
              'net_r': Y_ALL[te], 'deductible_cost_r': d['deductible_cost_r'].to_numpy(float)}
    windows = P.build_windows(d)
    res_local, fil_local = arrays['resolved'], arrays['filled']

    tr_month = te[RES[te]]                                   # in-sample training rows
    prior = np.flatnonzero(np.isin(MONTH, MONTHS[:MONTHS.index(m)]) & RES)

    preds = {}
    preds['ridge_oos_frozen'] = d['pred_month_boundary'].to_numpy(float)
    preds['gbm_is'] = fit_predict("gbm_is", tr_month, te)
    y_shuf = Y_ALL.copy(); perm = rng.permutation(tr_month); y_shuf[tr_month] = Y_ALL[perm]
    preds['gbm_is_shuffled'] = fit_predict("gbm_is", tr_month, te, y=y_shuf)
    preds['ridge_is'] = fit_predict("ridge", tr_month, te)
    # 5-fold GroupKFold by trading day, out-of-fold predictions for every row of the month
    days = np.unique(DAY[te]); folds = np.array_split(days, 5)
    oof = np.full(len(te), np.nan)
    for f in folds:
        hold = np.isin(DAY[te], f)
        trf = te[(~hold) & RES[te]]
        oof[hold] = fit_predict("gbm_reg", trf, te[hold])
    preds['gbm_cv_day'] = oof
    if len(prior):
        preds['gbm_oos'] = fit_predict("gbm_reg", prior, te)
        preds['ridge_oos'] = fit_predict("ridge", prior, te)

    arms = {}
    for name, pr in preds.items():
        entry = {"skill": skill(pr, te)}
        for pol, thr, tag in [("mixed", -1e17, "must_trade_mixed"),
                              ("market_top_abstain", P.MIN_EXPECTED_NET_R, "frozen_policy_0p10")]:
            out = P.run(windows, arrays, np.where(res_local, pr, P.NEG), policy=pol,
                        threshold=thr, available_mask=res_local)
            entry[tag] = P.score_book(out['selected'], arrays)
        arms[name] = entry

    # ceilings / floors / null on the SAME instrument
    for name, sc, sgn in [("oracle_best", arrays['net_r'], 1), ("oracle_worst", -arrays['net_r'], 1)]:
        out = P.run(windows, arrays, np.where(res_local, sc, P.NEG), policy="mixed",
                    threshold=-1e17, available_mask=res_local)
        arms[name] = {"must_trade_mixed": P.score_book(out['selected'], arrays)}
    draws = []
    for b in range(200):
        out = P.run(windows, arrays, np.where(res_local, rng.random(len(d)), P.NEG),
                    policy="mixed", threshold=-1e17, available_mask=res_local)
        draws.append(P.score_book(out['selected'], arrays)['net_r'])
    draws = np.asarray(draws)
    arms['random'] = {"must_trade_mixed": {"net_r": round(float(draws.mean()), 4),
                                           "sd": round(float(draws.std(ddof=1)), 4),
                                           "p05": round(float(np.percentile(draws, 5)), 4),
                                           "p95": round(float(np.percentile(draws, 95)), 4),
                                           "draws": 200}}

    ceil = arms['oracle_best']['must_trade_mixed']['net_r']
    floor_ = arms['random']['must_trade_mixed']['net_r']
    span = ceil - floor_
    for name in arms:
        v = arms[name].get('must_trade_mixed', {})
        if 'net_r' in v and span > 0:
            v['capture_ratio_vs_random_floor'] = round((v['net_r'] - floor_) / span, 5)

    report["months"][m] = {"eligible_rows": int(len(te)), "windows": len(windows),
                           "filled_rows": int(fil_local.sum()), "arms": arms}
    print(json.dumps({"month": m, "t": round(time.time() - t0, 1), **{
        k: arms[k]['must_trade_mixed']['net_r'] for k in
        ['oracle_best', 'gbm_is', 'gbm_is_shuffled', 'gbm_cv_day', 'ridge_oos_frozen', 'random', 'oracle_worst']
        if k in arms}}), flush=True)

(OUT / "PART1_FEATURE_INFORMATION.json").write_text(json.dumps(report, indent=1, sort_keys=True))
print("DONE", round(time.time() - t0, 1))
