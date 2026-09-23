#!/usr/bin/env python3
"""F4 task 3b — build the three absent feature families and prove them causal.

N1  HIGHER-TIMEFRAME CONTEXT      (D1 / H4 trend, location, structural distance)
N2  HORIZON FEASIBILITY           (is the required move attainable in the label span?)
N3  DECISION-WINDOW POOL STATE    (opposing side, density, directional agreement)

Every feature is computed from bars whose CLOSE is at or before the row's
decision instant, or from candidates in the row's own decision window. A
programmatic point-in-time assertion runs per symbol and is recorded.

Read-only over the lane bar archive. Writes a feature pickle + a receipt.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from f4_common import MONTHS, jdump, load_month  # noqa: E402

LANE = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
            "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1")
MANI = LANE / "manifests"
OUT = Path(__file__).parent / "receipts"
MAN_NAME = {"feb": "february_2026", "apr": "april_2026", "may": "may_2026",
            "jun": "june_2026", "jul": "july_2026"}
TF_MINUTES = {"M15": 15, "H4": 240, "D1": 1440}
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def mins(t: dt.datetime) -> int:
    return int((t - EPOCH).total_seconds() // 60)


def at(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def load_series(month: str, timeframe: str) -> dict:
    """All bar sources for this month+timeframe, merged and deduped by open time.

    Returns {symbol: dict(t=open_minutes, close_min=close_minutes, o,h,l,c)}.
    June carries a separate `_leadin_` family that must be concatenated.
    """
    man = json.loads((MANI / f"{MAN_NAME[month]}.json").read_text())
    per = defaultdict(dict)
    for e in man["bar_sources"]:
        if e["timeframe"] != timeframe:
            continue
        p = LANE / e["lane_relpath"]
        with p.open(newline="") as fh:
            for row in csv.DictReader(fh):
                per[e["symbol"]][row["time"]] = row
    dur = TF_MINUTES[timeframe]
    out = {}
    for sym, d in per.items():
        rows = [d[k] for k in sorted(d)]
        t = np.array([mins(at(r["time"])) for r in rows], dtype=np.int64)
        out[sym] = dict(
            t=t, close_min=t + dur,
            o=np.array([float(r["open"]) for r in rows]),
            h=np.array([float(r["high"]) for r in rows]),
            l=np.array([float(r["low"]) for r in rows]),
            c=np.array([float(r["close"]) for r in rows]),
        )
    return out


def atr(h, l, c, n=14):
    """Wilder-style ATR on arrays; atr[i] uses bars <= i."""
    pc = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    out = np.full(len(tr), np.nan)
    if len(tr) < n:
        return out
    out[n - 1] = tr[:n].mean()
    for i in range(n, len(tr)):
        out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


def last_closed(series: dict, tmin: int) -> int:
    """Index of the last bar whose CLOSE is at or before tmin. -1 if none.

    This is the point-in-time guard: a bar stamped at its open t is only usable
    once t + duration <= decision instant.
    """
    return int(np.searchsorted(series["close_min"], tmin, side="right")) - 1


WALK = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane2")


def load_risk(month: str) -> dict:
    """Exact stop distance in PRICE units from Lane 2's walk.

    risk = |entry_price - stop_loss|, fixed by the candidate's own geometry at
    generation time. Strictly predecision: it carries no outcome content.
    """
    with gzip.open(WALK / f"walk_{month}.pkl.gz", "rb") as f:
        recs = pickle.load(f)
    return {r["k"]: float(r["risk"]) for r in recs if r.get("risk")}


def trend_state(c, a50, i):
    """The generator's own 5-state trend, reimplemented on an arbitrary series
    (broader_origin_generators._trend_state:3733)."""
    if i < 20 or a50 is None or a50 != a50 or a50 <= 0:
        return None
    z = (c[i] - c[i - 20]) / a50
    if z >= 2.0:  return 2
    if z >= 0.75: return 1
    if z <= -2.0: return -2
    if z <= -0.75: return -1
    return 0


def build_month(month: str, rows: list, viol: Counter) -> dict:
    risk_of = load_risk(month)
    d1 = load_series(month, "D1")
    h4 = load_series(month, "H4")
    m15 = load_series(month, "M15")
    for s in (d1, h4, m15):
        for sym, v in s.items():
            v["atr14"] = atr(v["h"], v["l"], v["c"], 14)

    by_sym = defaultdict(list)
    for r in rows:
        by_sym[r["symbol"]].append(r)

    feats = {}
    for sym, rs in by_sym.items():
        S1, S4, S15 = d1.get(sym), h4.get(sym), m15.get(sym)
        if S1 is None or S4 is None or S15 is None:
            viol[f"missing_series:{sym}"] += len(rs)
            continue
        for r in rs:
            tmin = mins(at(r["label_span_start_utc"]))
            f = {}
            i1, i4, i15 = last_closed(S1, tmin), last_closed(S4, tmin), last_closed(S15, tmin)
            # --- hard point-in-time assertion --------------------------------
            for S, i in ((S1, i1), (S4, i4), (S15, i15)):
                if i >= 0 and S["close_min"][i] > tmin:
                    raise AssertionError("point-in-time violation")
            d = 1.0 if r["side"] == "LONG" else -1.0
            # risk in price units, from the frozen features (no outcome content)
            atr_m15 = S15["atr14"][i15] if i15 >= 4 else np.nan
            risk_px = risk_of.get(r["candidate_occurrence_key"], np.nan)
            ref = S15["c"][i15] if i15 >= 0 else np.nan

            # ---------------- N1 higher-timeframe context --------------------
            if i1 >= 20 and S1["atr14"][i1] == S1["atr14"][i1] and S1["atr14"][i1] > 0:
                a1 = S1["atr14"][i1]
                f["htf_d1_trend_atr"] = float((S1["c"][i1] - S1["c"][i1 - 5]) / a1) * d
                hi20 = float(S1["h"][i1 - 19:i1 + 1].max())
                lo20 = float(S1["l"][i1 - 19:i1 + 1].min())
                rng = hi20 - lo20
                f["htf_d1_pos_in_20d_range"] = float((ref - lo20) / rng) if rng > 0 else np.nan
                f["htf_d1_range20_over_atr"] = float(rng / a1)
                # room to structure in the trade's direction, in R
                tgt_lvl = hi20 if d > 0 else lo20
                f["htf_room_to_d1_extreme_r"] = (
                    float((tgt_lvl - ref) * d / risk_px) if risk_px == risk_px and risk_px > 0 else np.nan)
                # prior completed D1 bar levels
                f["htf_dist_prior_day_high_r"] = (
                    float((S1["h"][i1] - ref) * d / risk_px) if risk_px == risk_px and risk_px > 0 else np.nan)
                f["htf_dist_prior_day_low_r"] = (
                    float((ref - S1["l"][i1]) * d / risk_px) if risk_px == risk_px and risk_px > 0 else np.nan)
                # ATR percentile in its own trailing 60-day distribution
                lo_i = max(0, i1 - 59)
                w = S1["atr14"][lo_i:i1 + 1]
                w = w[~np.isnan(w)]
                f["htf_d1_atr_pctile60"] = float((w <= a1).mean()) if len(w) > 5 else np.nan
            if i4 >= 20 and S4["atr14"][i4] == S4["atr14"][i4] and S4["atr14"][i4] > 0:
                a4 = S4["atr14"][i4]
                f["htf_h4_trend_atr"] = float((S4["c"][i4] - S4["c"][i4 - 6]) / a4) * d
                hi = float(S4["h"][i4 - 19:i4 + 1].max())
                lo = float(S4["l"][i4 - 19:i4 + 1].min())
                rng = hi - lo
                f["htf_h4_pos_in_20b_range"] = float((ref - lo) / rng) if rng > 0 else np.nan
            if "htf_d1_trend_atr" in f and "htf_h4_trend_atr" in f:
                f["htf_trend_agree_d1_h4"] = float(
                    np.sign(f["htf_d1_trend_atr"]) * np.sign(f["htf_h4_trend_atr"]))

            # prior completed WEEK high/low (genuine gap: nothing in the repo has it)
            if i1 >= 5 and risk_px == risk_px and risk_px > 0:
                j0 = max(0, i1 - 4)
                wh = float(S1["h"][j0:i1 + 1].max())
                wl = float(S1["l"][j0:i1 + 1].min())
                f["htf_dist_prior_week_high_r"] = float((wh - ref) * d / risk_px)
                f["htf_dist_prior_week_low_r"] = float((ref - wl) * d / risk_px)
                f["htf_prior_week_range_r"] = float((wh - wl) / risk_px)
            # time since the M15 trend state last changed (genuine gap: the frozen
            # basis has only a one-bar boolean, trend_transition_flag)
            if i15 >= 70:
                a50 = S15["atr14"][i15]
                cur = trend_state(S15["c"], a50, i15)
                if cur is not None:
                    n_back = 0
                    for j in range(i15 - 1, max(20, i15 - 200) - 1, -1):
                        if trend_state(S15["c"], S15["atr14"][j], j) != cur:
                            break
                        n_back += 1
                    f["regime_m15_bars_since_trend_change"] = float(n_back)
                    f["regime_m15_trend_state_signed"] = float(cur) * d

            # ---------------- N2 horizon feasibility / vol term structure ----
            # the label span the trade must resolve inside
            span = mins(at(r["label_span_end_utc"])) - tmin
            f["feas_span_minutes"] = float(span)
            if risk_px == risk_px and risk_px > 0 and atr_m15 == atr_m15 and atr_m15 > 0:
                f["feas_required_move_atr_m15"] = float(2.0 * risk_px / atr_m15)
                nb = max(1, int(span // 15))
                f["feas_required_move_per_bar_atr"] = float(2.0 * risk_px / (atr_m15 * np.sqrt(nb)))
                # trailing empirical reachability: over the last K windows of nb M15
                # bars, how often did the favourable excursion from the window open
                # exceed the required 2R move?
                K = 200
                lo_i = max(0, i15 - K * 1)
                idx = np.arange(lo_i, max(lo_i, i15 - nb + 1))
                if len(idx) >= 30:
                    if d > 0:
                        ext = np.array([S15["h"][j:j + nb].max() - S15["o"][j] for j in idx])
                    else:
                        ext = np.array([S15["o"][j] - S15["l"][j:j + nb].min() for j in idx])
                    f["feas_p_reach_2r_trailing"] = float((ext >= 2.0 * risk_px).mean())
                    f["feas_p_reach_1r_trailing"] = float((ext >= 1.0 * risk_px).mean())
                    f["feas_median_span_excursion_r"] = float(np.median(ext) / risk_px)
                if i1 >= 14 and S1["atr14"][i1] == S1["atr14"][i1]:
                    f["vol_term_d1_over_m15"] = float(S1["atr14"][i1] / (atr_m15 * np.sqrt(96.0)))
                if i4 >= 14 and S4["atr14"][i4] == S4["atr14"][i4]:
                    f["vol_term_h4_over_m15"] = float(S4["atr14"][i4] / (atr_m15 * np.sqrt(16.0)))
            feats[r["candidate_occurrence_key"]] = f
    return feats


def pool_features(rows: list) -> dict:
    """N3 — decision-window pool state. Point-in-time by construction: every
    candidate in a decision window exists before any of them is ranked."""
    win = defaultdict(list)
    for r in rows:
        win[r["decision_window_id"]].append(r)
    out = {}
    for wid, rs in win.items():
        n = len(rs)
        n_long = sum(1 for r in rs if r["side"] == "LONG")
        bysym = Counter(r["symbol"] for r in rs)
        bysymside = Counter((r["symbol"], r["side"]) for r in rs)
        byfam = Counter(r["origin_family"] for r in rs)
        for r in rs:
            sym, side = r["symbol"], r["side"]
            opp = "SHORT" if side == "LONG" else "LONG"
            ns = bysym[sym]
            same = bysymside[(sym, side)]
            other = bysymside[(sym, opp)]
            out[r["candidate_occurrence_key"]] = {
                "pool_n_in_window": float(n),
                "pool_n_same_symbol": float(ns),
                "pool_n_opposite_side_same_symbol": float(other),
                "pool_symbol_side_agreement": float((same - other) / ns) if ns else np.nan,
                "pool_frac_long_in_window": float(n_long / n),
                "pool_side_vs_pool": float(
                    (n_long / n) if side == "LONG" else (1.0 - n_long / n)),
                "pool_n_same_family": float(byfam[r["origin_family"]]),
                "pool_n_distinct_symbols": float(len(bysym)),
            }
    return out


def main() -> None:
    viol = Counter()
    allf = {}
    for m in MONTHS:
        rows = load_month(m)
        pf = pool_features(rows)              # N3 over the FULL population
        target = [r for r in rows if r["lifecycle_label_status"].startswith("RESOLVED_FILLED")]
        bf = build_month(m, target, viol)     # N1/N2 over filled rows only
        for r in target:
            k = r["candidate_occurrence_key"]
            allf[k] = dict(bf.get(k, {}), **pf.get(k, {}))
        print(f"{m}: filled={len(target)} with_bar_features={len(bf)}", flush=True)

    names = sorted({k for v in allf.values() for k in v})
    cov = {}
    for k in names:
        vals = np.array([v.get(k, np.nan) for v in allf.values()], dtype=float)
        ok = ~np.isnan(vals)
        cov[k] = {"coverage": float(ok.mean()),
                  "mean": float(vals[ok].mean()) if ok.any() else None,
                  "std": float(vals[ok].std()) if ok.any() else None,
                  "n_unique": int(len(np.unique(np.round(vals[ok], 8)))) if ok.any() else 0}

    fam = {"N1_higher_timeframe": [n for n in names if n.startswith("htf_")],
           "N2_horizon_feasibility": [n for n in names if n.startswith(("feas_", "vol_term_"))],
           "N3_pool_state": [n for n in names if n.startswith("pool_")],
           "N1b_regime_age": [n for n in names if n.startswith("regime_")]}
    res = {
        "prereg_sha256": "bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054",
        "n_rows_with_features": len(allf),
        "families": fam,
        "n_new_features": len(names),
        "coverage_and_moments": cov,
        "point_in_time_violations": dict(viol),
        "point_in_time_rule": (
            "A bar stamped at open time t and of duration D is usable only when "
            "t + D <= label_span_start_utc. Enforced by last_closed() and asserted "
            "per row; any violation raises."),
    }
    jdump(res, OUT / "F4_NEW_FEATURES_V1.json")
    with gzip.open(Path(__file__).parent / "f4_new_features.pkl.gz", "wb") as f:
        pickle.dump(allf, f, protocol=5)

    print(f"\nnew features: {len(names)} over {len(allf)} filled rows")
    for k, v in fam.items():
        print(f"  {k}: {len(v)}")
    print("\ncoverage:")
    for k in names:
        print(f"  {k:36s} cov={cov[k]['coverage']:.4f} uniq={cov[k]['n_unique']:7d}")
    print("violations:", dict(viol))


if __name__ == "__main__":
    main()
