#!/usr/bin/env python3
"""F1 excursion census: build the per-trade artifact and every aggregate."""
import gzip, json, pickle, sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
MONTHS = ["feb", "apr", "may", "jun", "jul"]
TARGETS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
LEVELS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 1.8, 1.9, 2.0]
R_USD = 2000.0          # 2.00% nominal dial on the $100,000 account (agent_config.yaml:23, :1363)
R_USD_EFF = 1730.0      # half-Kelly effective ~1.73% (agent_config.yaml:1316-1322)
tag = lambda v: ("%g" % v).replace(".", "p")


def load():
    frames = []
    for m in MONTHS:
        recs = pickle.load(gzip.open(HERE / f"f1walk_{m}.pkl.gz", "rb"))
        frames.append(pd.DataFrame.from_records(recs))
    df = pd.concat(frames, ignore_index=True)
    # Two frames, and they are NOT the same. Excursion is measured in R from the
    # actual FILL (what you could have banked). The estate's contract levels
    # (-1R stop, +2R target) are denominated from the DECLARED ENTRY. They differ
    # by the fill slippage: R_from_entry = R_from_fill - entry_slip_r.
    df["mfe_entry_r"] = df["mfe_r"] - df["entry_slip_r"]
    df["mfe_pre_exit_entry_r"] = df["mfe_pre_exit_r"] - df["entry_slip_r"]
    df["mae_entry_r"] = df["mae_r"] - df["entry_slip_r"]
    df["mfe_full_entry_r"] = df["mfe_full_r"] - df["entry_slip_r"]
    for lv in LEVELS:
        t = "l" + tag(lv)
        df["reachE_" + t] = df["mfe_entry_r"] >= lv
        df["reachpreE_" + t] = df["mfe_pre_exit_entry_r"] >= lv
    df["is_win"] = df["exit_kind"] == "TARGET"
    df["is_stop"] = df["exit_kind"] == "STOP"
    df["is_time"] = df["exit_kind"] == "TIME_STOP"
    df["net_usd"] = df["net_r"] * R_USD
    df["gross_usd"] = df["gross_r"] * R_USD
    df["cost_usd"] = df["cost_r"] * R_USD
    return df


def q(a, ps=(5, 10, 25, 50, 75, 90, 95, 99)):
    a = np.asarray(a, dtype=float); a = a[np.isfinite(a)]
    if not len(a):
        return {}
    out = {"n": int(len(a)), "mean": float(a.mean()), "sd": float(a.std(ddof=1)) if len(a) > 1 else 0.0}
    for p in ps:
        out["p%g" % p] = float(np.percentile(a, p))
    return out


def boot_ci(a, n=2000, seed=20260812):
    a = np.asarray(a, dtype=float); a = a[np.isfinite(a)]
    if len(a) < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(n, len(a)))
    ms = a[idx].mean(axis=1)
    return float(np.percentile(ms, 2.5)), float(np.percentile(ms, 97.5))


def main():
    df = load()
    out = {}

    # ---------------------------------------------------------------- 0. population
    out["population"] = {
        "n_trades": int(len(df)),
        "by_month": df.groupby("month").size().to_dict(),
        "by_exit_kind": df["exit_kind"].value_counts().to_dict(),
        "by_order_type": df["order_type"].value_counts().to_dict(),
        "n_symbols": int(df["symbol"].nunique()),
        "n_families": int(df["family"].nunique()),
        "n_trading_days": int(df["trading_day"].nunique()),
        "hit_rate_all_fills": float(df["is_win"].mean()),
        "hit_rate_barrier_resolved": float(df["is_win"].sum() / (df["is_win"].sum() + df["is_stop"].sum())),
        "mean_net_r": float(df["net_r"].mean()),
        "mean_gross_r": float(df["gross_r"].mean()),
        "mean_cost_r": float(df["cost_r"].mean()),
        "total_net_r": float(df["net_r"].sum()),
        "mean_net_usd_at_2pct": float(df["net_r"].mean() * R_USD),
        "median_hold_min": float(df["hold_min"].median()),
        "mean_hold_min": float(df["hold_min"].mean()),
        "cost_components_mean_r": {
            "spread": float(df["spread_r"].mean()), "slippage": float(df["slippage_r"].mean()),
            "swap": float(df["swap_r"].mean()), "commission": float(df["commission_r"].mean()),
            "deductible_total": float(df["cost_r"].mean())},
    }

    # ---------------------------------------------------------------- 1. NEAR MISS
    near = {}
    for name, sub in [("stop_losers", df[df.is_stop]), ("all_negative", df[df.net_r < 0]),
                      ("time_stop_negative", df[df.is_time & (df.net_r < 0)]),
                      ("time_stop_all", df[df.is_time]), ("all_fills", df)]:
        d = {"n": int(len(sub))}
        for lv in LEVELS:
            # FILL frame: R actually bankable from the price we got (economic)
            d["reached_%s_inclusive" % tag(lv)] = float(sub["reach_" + "l" + tag(lv)].mean())
            d["reached_%s_preexit" % tag(lv)] = float(sub["reachpre_" + "l" + tag(lv)].mean())
            # DECLARED-ENTRY frame: the frame the -1R/+2R contract is written in
            d["entryframe_%s_inclusive" % tag(lv)] = float(sub["reachE_" + "l" + tag(lv)].mean())
            d["entryframe_%s_preexit" % tag(lv)] = float(sub["reachpreE_" + "l" + tag(lv)].mean())
        d["mfe_r"] = q(sub["mfe_r"]); d["mfe_pre_exit_r"] = q(sub["mfe_pre_exit_r"])
        d["mfe_entry_frame_r"] = q(sub["mfe_entry_r"])
        d["entry_slip_r"] = q(sub["entry_slip_r"])
        d["mfe_full_r_barrier_free"] = q(sub["mfe_full_r"])
        d["t_mfe_min"] = q(sub["t_mfe_min"])
        near[name] = d
    out["near_miss"] = near

    # ---------------------------------------------------------------- 2. MAE / fragility
    frag = {}
    for name, sub in [("winners", df[df.is_win]), ("stop_losers", df[df.is_stop]),
                      ("time_stops", df[df.is_time]), ("all_fills", df)]:
        d = {"n": int(len(sub)), "mae_r": q(sub["mae_r"]), "t_mae_min": q(sub["t_mae_min"]),
             "mae_headroom_r": q(sub["mae_headroom_r"]),
             "mae_full_r_barrier_free": q(sub["mae_full_r"]),
             "mae_before_mfe_share": float(sub["mae_before_mfe"].mean())}
        for thr in (0.02, 0.05, 0.10, 0.20, 0.30, 0.50):
            d["within_%gR_of_stop" % thr] = float((sub["mae_headroom_r"] <= thr).mean())
        near_stop = sub["mae_r"] / sub["stop_r"].abs()
        d["mae_as_frac_of_stop"] = q(near_stop.abs())
        frag[name] = d
    out["fragility"] = frag

    # ---------------------------------------------------------------- 3. give-back
    gb = {}
    for thr in (0.5, 1.0, 1.5, 1.8):
        sub = df[df.mfe_r >= thr]
        if not len(sub):
            continue
        gb["mfe_ge_%s" % tag(thr)] = {
            "n": int(len(sub)), "share_of_all_fills": float(len(sub) / len(df)),
            "giveback_r": q(sub["giveback_r"]),
            "outcome_mix": sub["exit_kind"].value_counts(normalize=True).to_dict(),
            "mean_net_r": float(sub["net_r"].mean()),
            "mean_net_usd": float(sub["net_r"].mean() * R_USD),
            "total_giveback_r": float(sub["giveback_r"].sum()),
            "total_giveback_usd": float(sub["giveback_r"].sum() * R_USD),
        }
    out["giveback"] = gb

    # ---------------------------------------------------------------- 4. path shape
    dec = ["p%d" % (q_ * 10) for q_ in range(1, 11)]
    shape = {}
    for name, sub in [("all", df), ("TARGET", df[df.is_win]), ("STOP", df[df.is_stop]),
                      ("TIME_STOP", df[df.is_time])]:
        shape[name] = {"n": int(len(sub)),
                       "mean_R_at_decile": {c: float(sub[c].mean()) for c in dec},
                       "median_R_at_decile": {c: float(sub[c].median()) for c in dec},
                       "mae_before_mfe_share": float(sub["mae_before_mfe"].mean()),
                       "t_mfe_min": q(sub["t_mfe_min"]), "t_mae_min": q(sub["t_mae_min"]),
                       "hold_min": q(sub["hold_min"])}
    out["path_shape"] = shape

    # ------------------------------------------------- 5. MFE conditional on outcome
    cond = {}
    for name, sub in [("TARGET", df[df.is_win]), ("STOP", df[df.is_stop]), ("TIME_STOP", df[df.is_time])]:
        cond[name] = {"n": int(len(sub)),
                      "mfe_full_r": q(sub["mfe_full_r"]), "mae_full_r": q(sub["mae_full_r"]),
                      "close_full_r": q(sub["close_full_r"]),
                      "mfe15_r": q(sub["mfe15_r"]), "mfe30_r": q(sub["mfe30_r"]),
                      "mae15_r": q(sub["mae15_r"]), "mae30_r": q(sub["mae30_r"])}
    # non-circular directional edge: barrier-free mark at the sealed horizon
    cf = df["close_full_r"].to_numpy(dtype=float)
    lo, hi = boot_ci(cf)
    cond["_barrier_free_directional_edge"] = {
        "n": int(np.isfinite(cf).sum()), "mean_close_full_r": float(np.nanmean(cf)),
        "ci95": [lo, hi], "t": float(np.nanmean(cf) / (np.nanstd(cf, ddof=1) / np.sqrt(np.isfinite(cf).sum()))),
        "mean_cost_r": float(df["cost_r"].mean()),
        "note": "barrier-free mark at the sealed 120-min horizon; exit-rule-free measure of direction",
    }
    # overlap of early MFE between eventual winners and eventual stop-losers (AUC)
    for col in ("mfe15_r", "mfe30_r", "mfe_full_r"):
        a = df.loc[df.is_win, col].to_numpy(dtype=float)
        b = df.loc[df.is_stop, col].to_numpy(dtype=float)
        allv = np.concatenate([a, b]); ranks = pd.Series(allv).rank().to_numpy()
        auc = (ranks[:len(a)].sum() - len(a) * (len(a) + 1) / 2) / (len(a) * len(b))
        cond.setdefault("_auc_winner_vs_stop", {})[col] = float(auc)
    out["mfe_conditional_on_outcome"] = cond

    # ---------------------------------------------------- 6. ACHIEVABLE HIT RATE
    def ladder(sub, suffix, arm):
        """arm: 'sealed'   -- same-bar both-barriers-touched is CENSORED (sealed convention)
                'pess'     -- same-bar ambiguity resolved as STOP  (worst case)
                'opt'      -- same-bar ambiguity resolved as TARGET (best case)
        The bracket matters: censoring rises as the target falls, so the sealed arm's
        n shrinks non-randomly at low T and would flatter a tight target if read alone."""
        rows = []
        for T in TARGETS:
            k = sub["t%s_kind%s" % (tag(T), suffix)]
            g = sub["t%s_gross%s" % (tag(T), suffix)].astype(float)
            h = sub["t%s_hold%s" % (tag(T), suffix)].astype(float)
            have = k.notna()
            cen = have & (k == "CENSOR")
            if arm == "sealed":
                ok = have & g.notna()
                gg = g.where(~cen)
            else:
                ok = have
                # the ambiguous bar touched BOTH: assign it wholly one way
                fill_v = sub["stop_r"] if arm == "pess" else (
                    T + sub["entry_slip_r"])          # target level on the fill basis
                gg = g.where(~cen, fill_v)
            n = int(ok.sum())
            if not n:
                continue
            kk = k.where(~cen, "STOP" if arm == "pess" else "TARGET") if arm != "sealed" else k
            win = ok & (kk == "TARGET"); stp = ok & (kk == "STOP")
            tim = ok & (kk == "TIME_STOP"); cn = ok & (kk == "CENSOR")
            net = gg[ok] - sub.loc[ok, "cost_r"]
            p_T = float(win.sum() / n); p_S = float(stp.sum() / n)
            p_TS = float(tim.sum() / n); p_C = float(cn.sum() / n)
            m_ts = float(gg[tim].mean()) if tim.sum() else 0.0
            c = float(sub.loc[ok, "cost_r"].mean())
            f = p_T + p_S
            # break-even hit rate: move mass between TARGET and STOP holding the
            # time-stop share and its mean mark fixed
            be_all = (f + c - p_TS * m_ts) / (T + 1.0) if f else float("nan")
            lo, hi = boot_ci(net.to_numpy())
            rows.append({
                "target_R": T, "arm": arm, "n": n,
                "hit_rate_all_fills": p_T,
                "hit_rate_barrier_resolved": float(p_T / f) if f else float("nan"),
                "stop_rate": p_S, "time_stop_rate": p_TS, "censor_rate": p_C,
                "mean_gross_r": float(gg[ok].mean()), "mean_net_r": float(net.mean()),
                "net_ci95": [lo, hi], "total_net_r": float(net.sum()),
                "mean_net_usd": float(net.mean() * R_USD), "total_net_usd": float(net.sum() * R_USD),
                "mean_hold_min": float(h[ok].mean()), "median_hold_min": float(h[ok].median()),
                "breakeven_hit_rate_all_fills": float(be_all),
                "breakeven_hit_rate_barrier_resolved": float(be_all / f) if f else float("nan"),
                "hit_rate_minus_breakeven_pp": float((p_T - be_all) * 100.0),
                "mean_cost_r": c,
            })
        return rows
    for arm in ("sealed", "pess", "opt"):
        out.setdefault("achievable_hit_rate_sealed_120min", {})[arm] = ladder(df, "", arm)
        out.setdefault("achievable_hit_rate_24h", {})[arm] = ladder(df, "E", arm)
    # per-family ladder at the sealed clock, sealed arm
    out["ladder_by_family"] = {}
    for fam, sub in df.groupby("family"):
        if len(sub) < 500:
            continue
        out["ladder_by_family"][str(fam)] = ladder(sub, "", "sealed")

    # ---------------------------------------------------------------- 7. cross-tabs
    def xt(key, minn=200):
        g = df.groupby(key)
        rows = []
        for name, sub in g:
            if len(sub) < minn:
                continue
            rows.append({
                str(key): str(name), "n": int(len(sub)),
                "hit_rate_all_fills": float(sub["is_win"].mean()),
                "hit_rate_barrier_resolved": float(sub["is_win"].sum() / max(1, (sub["is_win"].sum() + sub["is_stop"].sum()))),
                "stop_rate": float(sub["is_stop"].mean()), "time_stop_rate": float(sub["is_time"].mean()),
                "mean_net_r": float(sub["net_r"].mean()), "total_net_r": float(sub["net_r"].sum()),
                "total_net_usd": float(sub["net_r"].sum() * R_USD),
                "mean_cost_r": float(sub["cost_r"].mean()),
                "mean_mfe_r": float(sub["mfe_r"].mean()), "mean_mae_r": float(sub["mae_r"].mean()),
                "mean_mfe_full_r": float(sub["mfe_full_r"].mean()),
                "mean_close_full_r": float(sub["close_full_r"].mean()),
                "median_hold_min": float(sub["hold_min"].median()),
                "loser_reached_1R_preexit": float(sub.loc[sub.is_stop, "reachpre_l1"].mean()) if sub.is_stop.any() else None,
                "loser_reached_1p8R_preexit": float(sub.loc[sub.is_stop, "reachpre_l1p8"].mean()) if sub.is_stop.any() else None,
                "winner_within_0p1R_of_stop": float((sub.loc[sub.is_win, "mae_headroom_r"] <= 0.1).mean()) if sub.is_win.any() else None,
            })
        return sorted(rows, key=lambda r: -r["n"])
    for key in ("family", "symbol", "session", "side", "month", "order_type", "utc_hour", "weekday"):
        out.setdefault("cross_tabs", {})[key] = xt(key)

    # volatility regime tertiles
    for col in ("atr14_over_atr50", "vol_8_over_48", "risk_over_atr"):
        v = df[col]
        try:
            df["_rg"] = pd.qcut(v, 3, labels=["low", "mid", "high"])
        except Exception:
            continue
        out["cross_tabs"]["regime_" + col] = xt("_rg", minn=100)
        df.drop(columns=["_rg"], inplace=True)

    # ---------------------------------------------------------------- 8. dollars
    out["dollars"] = {
        "basis": "1 R = 2.00% of a $100,000 account = $2,000 (config/agent_config.yaml:23 "
                 "risk_per_trade_pct, :1363 governor_static_initial_balance)",
        "r_usd_nominal": R_USD, "r_usd_half_kelly_effective": R_USD_EFF,
        "mean_net_usd_per_trade": float(df["net_r"].mean() * R_USD),
        "mean_cost_usd_per_trade": float(df["cost_r"].mean() * R_USD),
        "total_net_usd_all_fills": float(df["net_r"].sum() * R_USD),
        "per_trade_by_outcome_usd": {
            k: float(df.loc[df.exit_kind == k, "net_r"].mean() * R_USD)
            for k in ("TARGET", "STOP", "TIME_STOP")},
        "total_giveback_usd_mfe_ge_1R": float(df.loc[df.mfe_r >= 1.0, "giveback_r"].sum() * R_USD),
    }

    json.dump(out, open(HERE / "F1_CENSUS.json", "w"), indent=1, default=str)
    print(json.dumps({"written": "F1_CENSUS.json", "n": len(df)}))
    return df


if __name__ == "__main__":
    main()
