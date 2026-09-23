#!/usr/bin/env python3
"""B3 shared library -- data, feature blocks, arms, and the walk-forward engine.

Everything here is bound by PREREG_V1.json (payload_sha256
9d53ab7275c2ee475e250a3322afd7fe52fd1d11b1e709421f4c2201730e96ab), which was
frozen before any arm was fitted.  Hyperparameters are constants in this file
and are the ones the prereg names; nothing is searched or tuned.

Memory discipline: source row dicts are never retained.  Features go straight
into a float32 / categorical frame and metadata into a compact per-row dict.
"""
from __future__ import annotations

import gzip
import json
import math
import pickle
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SCRATCH = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/b3")
OUT = SCRATCH / "out"
CACHE = Path("/private/tmp/w21-puzzle-cache")
OA = Path(__file__).resolve().parents[3]   # .../outcome_authority
PREREG_SHA = "9d53ab7275c2ee475e250a3322afd7fe52fd1d11b1e709421f4c2201730e96ab"

MAX_COST_R = 0.20
MIN_EXPECTED_NET_R = 0.10
MONTHS = ("feb", "apr", "may", "jun", "jul")
DEV_MONTHS = ("feb", "apr", "may")
CONF_MONTHS = ("jun", "jul")

CAT0 = [
    "symbol", "side", "origin_family", "utc_session", "proposed_order_type",
    "utc_hour", "weekday", "symbol_x_family", "family_x_session",
    "symbol_x_side", "poi_mitigation_status", "limit_marketable_at_decision",
    "trend_state_m15", "trend_transition_flag",
]
NUM0 = [
    "cost_r", "spread_r", "expected_slippage_r", "swap_cost_r", "commission_r",
    "distance_to_limit_atr", "distance_to_limit_risk", "risk_over_atr",
    "risk_fraction_of_entry", "poi_age_hours", "poi_distance_to_midpoint_atr",
    "poi_distance_to_zone_atr", "poi_touch_count", "poi_max_mitigation_fraction",
    "poi_touch_episode_count", "poi_overlap_bar_count",
    "atr14_over_atr50", "stop_distance_atr", "target_distance_atr",
    "close_position_in_lookback_range", "dist_to_prior_high20_atr",
    "dist_to_prior_low20_atr", "trigger_bar_range_atr",
    "trigger_bar_body_atr", "compression_ratio_prior_bar",
    "bars_since_session_open", "close_to_close_vol_8_over_48",
    "sweep_depth_atr", "session_open_range_width_atr",
]
NUM1 = ["fam_mom5", "fam_mom10", "fam_mom20", "pool_mom10",
        "reg_vol", "reg_ccvol", "reg_comp", "reg_spread", "reg_cost",
        "reg_risk", "reg_trendshare", "reg_upshare"]
CAT1 = ["family_x_volbucket", "family_x_trendbucket"]

COST_FEATURES = {"cost_r", "spread_r", "expected_slippage_r", "swap_cost_r", "commission_r"}
FILLED_ST = {"RESOLVED_FILLED_TARGET", "RESOLVED_FILLED_STOP", "RESOLVED_FILLED_TIME_STOP"}
RESOLVED_ST = FILLED_ST | {"RESOLVED_NO_FILL"}
CLASS5 = ["CENSORED", "NO_FILL", "STOP", "TARGET", "TIME_STOP"]   # sorted, = clf classes_

HGB_KW = dict(max_iter=300, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=100,
              l2_regularization=1.0, early_stopping=False, random_state=0,
              categorical_features="from_dtype")
RIDGE_ALPHA = 10.0


DAYS_REQUIRED = 100


def complete_stages():
    """Stages whose walk-forward covers all 100 scored days."""
    out = []
    for stage in ("W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"):
        ck = OUT / f"ck_{stage}.json"
        pr = OUT / f"preds_{stage}.npz"
        if not (ck.exists() and pr.exists()):
            continue
        import json as _json
        if len(_json.loads(ck.read_text()).get("days_done", [])) >= DAYS_REQUIRED:
            out.append(stage)
    return out


def _f(value):
    try:
        out = float(value)
    except (TypeError, ValueError):
        return np.nan
    return out if math.isfinite(out) else np.nan


def _class5(status):
    if status == "RESOLVED_NO_FILL":
        return "NO_FILL"
    if status == "RESOLVED_FILLED_TARGET":
        return "TARGET"
    if status == "RESOLVED_FILLED_STOP":
        return "STOP"
    if status == "RESOLVED_FILLED_TIME_STOP":
        return "TIME_STOP"
    if status.startswith("CENSORED_"):
        return "CENSORED"
    raise ValueError(status)


def _eligible(row):
    if not row.get("predecision_geometry_valid"):
        return False
    cost = _f(row.get("cost_r"))
    return math.isfinite(cost) and cost <= MAX_COST_R


def day_order():
    prereg = json.loads((OA / "JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1_3.json").read_text())
    tr = prereg["training"]
    val = {w["window_id"]: w["days"] for w in prereg["validation"]["windows"]}
    return [("feb", tr["february_days"]), ("apr", tr["april_days"]), ("may", tr["may_days"]),
            ("jun", val["june_2026"]), ("jul", val["july_2026"])]


# ============================ load ==========================================
def load_dataset():
    """Returns (meta, frame) -- meta is a compact list, frame is F0+F1 columns."""
    cols = {k: [] for k in CAT0 + NUM0}
    meta = []

    def take(src, month, chain_day):
        status = str(src.get("lifecycle_label_status") or "")
        resolved = status in RESOLVED_ST
        for k in CAT0:
            v = src.get(k)
            cols[k].append("MISSING" if v is None else str(v))
        for k in NUM0:
            cols[k].append(_f(src.get(k)))
        meta.append({
            "key": src["candidate_occurrence_key"], "win": src["decision_window_id"],
            "day": src["trading_day"], "cday": chain_day, "month": month,
            "sym": src["symbol"], "ot": src["proposed_order_type"],
            "fam": src["origin_family"], "cost": _f(src.get("cost_r")),
            "net": (float(src.get("terminal_net_r") or 0.0) if resolved else np.nan),
            "dc": _f(src.get("deductible_cost_r")) if src.get("deductible_cost_r") is not None else 0.0,
            "res": resolved, "fil": status in FILLED_ST, "c5": _class5(status),
            "t0": src["label_span_start_utc"],
            "t1": src.get("label_span_end_utc") or src.get("expiry_utc"),
        })

    with (OUT / "bootstrap_rows.pkl").open("rb") as fh:
        boot = pickle.load(fh)
    for src in boot["initial"]:
        if _eligible(src):
            take(src, "boot", "0000-" + str(src["trading_day"]))
    boot["initial"] = None
    for day in boot["jan_runs"]:
        for src in boot["january"][day]:
            if _eligible(src):
                take(src, "jan", "0001-" + day)
        boot["january"][day] = None
    del boot
    n_boot = len(meta)

    for month, days in day_order():
        want = set(days)
        with gzip.open(CACHE / f"rows_{month}.pkl.gz", "rb") as fh:
            month_rows = pickle.load(fh)
        by_day = defaultdict(list)
        for src in month_rows:
            if _eligible(src) and src["trading_day"] in want:
                by_day[src["trading_day"]].append(src)
        del month_rows
        for day in days:
            for src in by_day.get(day, []):
                take(src, month, "0002-" + day)
            by_day[day] = None

    data = {}
    for k in CAT0:
        data[k] = pd.Categorical(cols.pop(k))
    for k in NUM0:
        data[k] = np.asarray(cols.pop(k), dtype=np.float32)
    frame = pd.DataFrame(data)
    return meta, frame, {"n_bootstrap": n_boot, "n_total": len(meta)}


# ============================ F1 regime block ===============================
def add_regime_features(meta, frame):
    """Lane-6 regime x family block.  Strictly prior by construction."""
    cday = np.asarray([m["cday"] for m in meta])
    fam = np.asarray([m["fam"] for m in meta])
    fil = np.asarray([m["fil"] for m in meta])
    net = np.asarray([m["net"] for m in meta], dtype=float)
    days = sorted(set(cday.tolist()))
    dindex = {d: i for i, d in enumerate(days)}

    fam_day = defaultdict(dict)
    for (d, f), grp in pd.DataFrame({"d": cday[fil], "f": fam[fil], "y": net[fil]}).groupby(
            ["d", "f"], observed=True):
        if len(grp) >= 5:
            fam_day[f][d] = float(grp["y"].mean())

    med_keys = {"reg_vol": "atr14_over_atr50", "reg_ccvol": "close_to_close_vol_8_over_48",
                "reg_comp": "compression_ratio_prior_bar", "reg_spread": "spread_r",
                "reg_cost": "cost_r", "reg_risk": "risk_over_atr"}
    day_reg = {}
    tmp = pd.DataFrame({"d": cday})
    for out_key, col in med_keys.items():
        tmp[out_key] = frame[col].to_numpy(dtype=float)
    trend = frame["trend_state_m15"].astype(str).to_numpy()
    tmp["reg_trendshare"] = np.isin(trend, ["strong_up", "strong_down"]).astype(float)
    tmp["reg_upshare"] = np.isin(trend, ["strong_up", "up"]).astype(float)
    agg = tmp.groupby("d", observed=True).agg(
        {**{k: "median" for k in med_keys}, "reg_trendshare": "mean", "reg_upshare": "mean"})
    for d, row in agg.iterrows():
        day_reg[d] = row.to_dict()

    prior_vol, prior_trend, cuts = [], [], {}
    for i, d in enumerate(days):
        cuts[d] = (np.nanpercentile(prior_vol, [33.3, 66.7]).tolist() if len(prior_vol) >= 6 else None,
                   np.nanpercentile(prior_trend, [33.3, 66.7]).tolist() if len(prior_trend) >= 6 else None)
        if i > 0:
            prior_vol.append(day_reg[days[i - 1]]["reg_vol"])
            prior_trend.append(day_reg[days[i - 1]]["reg_trendshare"])

    def bucket(value, cut):
        if cut is None or value is None or not math.isfinite(value):
            return "MISSING"
        return "LO" if value <= cut[0] else ("MID" if value <= cut[1] else "HI")

    per_day = {}
    for i, d in enumerate(days):
        prev = days[i - 1] if i > 0 else None
        reg = dict(day_reg[prev]) if prev is not None else {k: np.nan for k in NUM1[4:]}
        pool = []
        for dd in days[max(0, i - 10):i]:
            vals = [fam_day[f][dd] for f in fam_day if dd in fam_day[f]]
            if vals:
                pool.append(float(np.mean(vals)))
        reg["pool_mom10"] = float(np.mean(pool)) if len(pool) >= 3 else np.nan
        vcut, tcut = cuts[d]
        reg["_vb"] = bucket(reg.get("reg_vol"), vcut)
        reg["_tb"] = bucket(reg.get("reg_trendshare"), tcut)
        per_day[d] = reg

    fam_hist = {}
    for f in fam_day:
        seq = [(d, fam_day[f][d]) for d in days if d in fam_day[f]]
        fam_hist[f] = seq

    fam_mom = {}
    for f, seq in fam_hist.items():
        vals = [v for _d, v in seq]
        seq_days = [d for d, _v in seq]
        for i, d in enumerate(days):
            cut = np.searchsorted(np.asarray([dindex[x] for x in seq_days]), i)
            prior = vals[:cut]
            fam_mom[(f, d)] = tuple(
                float(np.mean(prior[-h:])) if len(prior[-h:]) >= 3 else np.nan for h in (5, 10, 20))

    n = len(meta)
    add = {k: np.full(n, np.nan, dtype=np.float32) for k in NUM1}
    vb = np.empty(n, dtype=object)
    tb = np.empty(n, dtype=object)
    for i in range(n):
        d, f = cday[i], fam[i]
        reg = per_day[d]
        for k in NUM1[4:]:
            add[k][i] = reg.get(k, np.nan)
        add["pool_mom10"][i] = reg["pool_mom10"]
        m5, m10, m20 = fam_mom.get((f, d), (np.nan, np.nan, np.nan))
        add["fam_mom5"][i], add["fam_mom10"][i], add["fam_mom20"][i] = m5, m10, m20
        vb[i] = f + "|" + reg["_vb"]
        tb[i] = f + "|" + reg["_tb"]
    for k in NUM1:
        frame[k] = add[k]
    frame["family_x_volbucket"] = pd.Categorical(vb)
    frame["family_x_trendbucket"] = pd.Categorical(tb)
    return frame


# ============================ models ========================================
def ridge_frame(frame, cats, nums):
    out = frame[cats + nums].copy()
    for key in cats:
        out[key] = out[key].astype(str)
    return out


def make_ridge(cats, nums):
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value=0.0, add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), cats),
                             ("num", numeric, nums)], sparse_threshold=0.3)
    return Pipeline([("pre", pre), ("ridge", Ridge(alpha=RIDGE_ALPHA, solver="lsqr"))])


def make_hgb_reg(columns=None, monotone=False):
    kw = dict(HGB_KW)
    if monotone:
        kw["monotonic_cst"] = [(-1 if c in COST_FEATURES else 0) for c in columns]
    return HistGradientBoostingRegressor(**kw)


def make_hgb_clf():
    return HistGradientBoostingClassifier(**HGB_KW)


def window_weights(meta, idx):
    counts = defaultdict(int)
    for i in idx:
        counts[meta[i]["win"]] += 1
    return np.asarray([1.0 / counts[meta[i]["win"]] for i in idx], dtype=float)


# ============================ funnel / metrics ==============================
def at(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def run_windows(meta, idx, pred, *, occupancy=True, policy="market_top_abstain",
                min_pred=MIN_EXPECTED_NET_R, cap=None):
    """Walk the frozen funnel with an arbitrary ranking statistic.

    `idx` is the candidate index subset to rank (one month, or all five).
    `pred` is a float array aligned with `meta`; NaN means "not scored".
    """
    by_window = defaultdict(list)
    for i in idx:
        value = pred[i]
        if not math.isfinite(value):
            continue
        by_window[meta[i]["win"]].append((float(value), i))
    ordered = sorted(by_window.values(),
                     key=lambda vals: (min(at(meta[i]["t0"]) for _, i in vals),
                                       meta[vals[0][1]]["win"]))
    active, windows, selected = {}, [], []
    for candidates in ordered:
        decision_at = min(at(meta[i]["t0"]) for _, i in candidates)
        active = {s: e for s, e in active.items() if e > decision_at}
        available = [(p, -meta[i]["cost"], meta[i]["key"], i) for p, i in candidates
                     if not (occupancy and meta[i]["sym"] in active)]
        if not available:
            continue
        order = sorted(available, key=lambda item: item[:3], reverse=True)
        top_pred, _neg, _key, ti = order[0]
        top = meta[ti]
        res = [meta[i]["net"] for _p, _n, _k, i in available if meta[i]["res"]]
        record = {
            "month": top["month"], "trading_day": top["day"],
            "decision_window_id": top["win"],
            "n_available": len(available), "n_resolved": len(res),
            "n_positive_available": int(sum(1 for a in res if a > 0)),
            "top_pred": top_pred, "top_order_type": top["ot"],
            "top_family": top["fam"], "top_symbol": top["sym"],
            "pick_actual": (top["net"] if top["res"] else None),
            "pick_wc": (top["net"] if top["res"] else -1.0 - top["dc"]),
            "rank2_actual": (meta[order[1][3]]["net"] if len(order) > 1
                             and meta[order[1][3]]["res"] else None),
            "oracle_max_actual": (max(res) if res else None),
            "oracle_min_actual": (min(res) if res else None),
            "mean_actual": (float(np.mean(res)) if res else None),
            "pick_is_window_best": bool(res and top["res"] and top["net"] >= max(res) - 1e-12),
            "outcome_gate": None,
        }
        windows.append(record)
        if top_pred < min_pred:
            record["outcome_gate"] = "G4_top_below_min_pred"
            continue
        if cap is not None and top_pred > cap:
            record["outcome_gate"] = "G4b_top_above_cap"
            continue
        if policy == "market_top_abstain" and top["ot"] != "MARKET":
            record["outcome_gate"] = "G5_market_top_abstain"
            continue
        record["outcome_gate"] = "TRADED"
        selected.append(ti)
        active[top["sym"]] = at(top["t1"])
    return windows, selected


def book(meta, selected):
    resolved = [i for i in selected if meta[i]["res"]]
    actual = float(sum(meta[i]["net"] for i in resolved))
    worst = actual + float(sum(-1.0 - meta[i]["dc"] for i in selected if not meta[i]["res"]))
    by_day = defaultdict(float)
    for i in resolved:
        by_day[meta[i]["day"]] += meta[i]["net"]
    outcomes = defaultdict(int)
    for i in selected:
        outcomes[meta[i]["c5"]] += 1
    return {"trades": len(selected), "resolved": len(resolved),
            "censored": len(selected) - len(resolved),
            "actual_net_r": round(actual, 6), "worst_case_net_r": round(worst, 6),
            "positive_days": sum(1 for v in by_day.values() if v > 0),
            "negative_days": sum(1 for v in by_day.values() if v < 0),
            "outcomes": dict(sorted(outcomes.items()))}


def boot_day(values, days, nboot=4000, seed=20260812):
    values = list(values)
    if not values:
        return None
    rng = np.random.default_rng(seed)
    grouped = defaultdict(list)
    for v, d in zip(values, days):
        grouped[d].append(v)
    keys = sorted(grouped)
    arrays = [np.asarray(grouped[k], dtype=float) for k in keys]
    n = len(keys)
    draws = np.empty(nboot)
    for i in range(nboot):
        pick = rng.integers(0, n, n)
        draws[i] = np.concatenate([arrays[j] for j in pick]).mean()
    return {"point": float(np.mean(np.asarray(values, dtype=float))),
            "ci95_lo": float(np.percentile(draws, 2.5)),
            "ci95_hi": float(np.percentile(draws, 97.5)),
            "p_two_sided_sign": float(2 * min((draws <= 0).mean(), (draws >= 0).mean())),
            "n": len(values)}


def rank_skill(windows, *, fixed_window=False, nboot=4000):
    pool = [w for w in windows if w["oracle_max_actual"] is not None]
    if not fixed_window:
        pool = [w for w in pool if w["pick_actual"] is not None]
    hit = [1.0 if (w["pick_actual"] or 0) > 0 else 0.0 for w in pool]
    days = [w["trading_day"] for w in pool]
    base = [w["n_positive_available"] / w["n_available"] for w in pool]
    p1 = {"windows": len(pool), "ranker": boot_day(hit, days, nboot),
          "uniform_baseline": float(np.mean(base)) if base else None,
          "ranker_minus_uniform": boot_day([h - b for h, b in zip(hit, base)], days, nboot)}

    best_pool = [w for w in windows if w["oracle_max_actual"] is not None
                 and w["oracle_max_actual"] > 0]
    if not fixed_window:
        best_pool = [w for w in best_pool if w["pick_actual"] is not None]
    bh = [1.0 if w["pick_is_window_best"] else 0.0 for w in best_pool]
    bb = [1.0 / w["n_available"] for w in best_pool]
    bd = [w["trading_day"] for w in best_pool]
    p2 = {"windows": len(best_pool), "ranker": boot_day(bh, bd, nboot),
          "uniform_baseline": float(np.mean(bb)) if bb else None,
          "ranker_minus_uniform": boot_day([a - b for a, b in zip(bh, bb)], bd, nboot)}

    pick = [w["pick_actual"] for w in windows if w["pick_actual"] is not None]
    rnd = [w["mean_actual"] for w in windows if w["mean_actual"] is not None]
    orc = [w["oracle_max_actual"] for w in windows if w["oracle_max_actual"] is not None]
    mp = float(np.mean(pick)) if pick else None
    mr = float(np.mean(rnd)) if rnd else None
    mo = float(np.mean(orc)) if orc else None
    paired = [(w["pick_actual"], w["mean_actual"], w["trading_day"]) for w in windows
              if w["pick_actual"] is not None and w["mean_actual"] is not None]
    p3 = {"windows_scored": len(pick), "mean_pick_r": mp, "mean_random_r": mr,
          "mean_oracle_r": mo,
          "ceiling_capture": ((mp - mr) / (mo - mr)) if None not in (mp, mr, mo) and mo != mr else None,
          "pick_minus_random_paired": boot_day([a - b for a, b, _ in paired],
                                               [d for _, _, d in paired], nboot) if paired else None}
    return {"P1_pick_positive": p1, "P2_pick_best": p2, "P3_r_per_window": p3}
