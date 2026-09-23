"""B5 step (b) — EFFECTIVE breadth of the expanded universe, on Lane 4's instrument.

Lane 4's estimator, reproduced exactly (lane4_receipts/b_breadth.py):
    Var(sum of K same-day bets) / (K * sigma^2) = 1 + (Kbar-1)*rhobar
    N_eff = Kbar / (1 + (Kbar-1)*rhobar),  bootstrap CI over day-groups, 400 resamples.

A "bet" here is one symbol's vol-normalised daily log return  z = r_t / sigma_{t-1},
sigma being a strictly-past 60-observation own-sequence SD. That is the unit a
risk-parity cross-sectional book actually deploys, and it is dimensionless like Lane 4's
terminal_net_r, so the two N_eff numbers are on the same scale.

Two populations, because they answer different questions:
    RAW      z as-is                       -> breadth available to a directional book
    NEUTRAL  z cross-sectionally demeaned  -> breadth available to a dollar-neutral book
                                              (the market factor removed, which is what a
                                               long/short XS book does by construction)

Writes <OUT>/B5_EFFECTIVE_BREADTH_V1.json.  Runtime ~30 s.  No new bulk data.
"""
import json, math, os, pickle
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "b5_receipts")
SCRATCH = "/Users/borr/.claude/jobs/adb9e69b/tmp/b5"
rng = np.random.default_rng(20260812)   # Lane 4's seed, so bootstraps are comparable

LIVE24 = ["AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY", "EURUSD",
          "GBPJPY", "GBPUSD", "GER40_cash", "JP225_cash", "US100_cash", "NZDUSD", "US500_cash",
          "UK100_cash", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF", "USDJPY", "USOIL_cash",
          "XAGUSD", "XAUUSD"]   # GTOS_24_SYMBOL_SURFACE, mapped to archive naming
VOL_N = 60


def build():
    d = pickle.load(open(os.path.join(SCRATCH, "panel_d1.pkl"), "rb"))
    panel, dates = d["panel"], d["dates"]
    syms = sorted({s for dt in dates for s in panel[dt]})
    S = {s: i for i, s in enumerate(syms)}
    T, N = len(dates), len(syms)
    LC = np.full((T, N), np.nan)
    for ti, dt in enumerate(dates):
        for s, v in panel[dt].items():
            LC[ti, S[s]] = math.log(v[3])
    OWN = {s: np.where(~np.isnan(LC[:, S[s]]))[0] for s in syms}
    Z = np.full((T, N), np.nan)            # vol-normalised daily return, strictly past vol
    for s in syms:
        j = S[s]; ts = OWN[s]; lc = LC[ts, j]
        if len(lc) < VOL_N + 2:
            continue
        r = np.diff(lc)                     # r[i] = return realised at own-obs i+1
        cs = np.cumsum(np.insert(r, 0, 0.0)); cs2 = np.cumsum(np.insert(r * r, 0, 0.0))
        n = VOL_N
        m = (cs[n:] - cs[:-n]) / n; m2 = (cs2[n:] - cs2[:-n]) / n
        sd = np.sqrt(np.maximum(m2 - m * m, 0.0) * n / (n - 1))   # sd of r[i-n..i-1] at obs i
        ok = sd > 0
        idx = ts[n + 1:][ok[: len(ts) - n - 1]] if len(ts) > n + 1 else np.array([], int)
        # align: at own-obs i (i>=n+1) the realised return is r[i-1], the past-vol is sd[i-n-1]
        for k in range(n + 1, len(ts)):
            s_ = sd[k - n - 1]
            if s_ > 0:
                Z[ts[k], j] = r[k - 1] / s_
    return dates, syms, S, Z, d["cls"]


def var_ratio(Z, dates, cols, neutral=False, nboot=400, min_k=2):
    """Lane 4's day-portfolio variance ratio over a column subset."""
    sub = Z[:, cols]
    rows = []
    for t in range(len(dates)):
        v = sub[t]
        v = v[~np.isnan(v)]
        if len(v) >= min_k:
            rows.append(v)
    if len(rows) < 30:
        return None
    if neutral:
        rows = [v - v.mean() for v in rows]
    allv = np.concatenate(rows)
    sig2 = float(allv.var(ddof=1)); mu = float(allv.mean())
    K = np.array([len(v) for v in rows], float)
    Ssum = np.array([v.sum() for v in rows], float)
    resid = Ssum - K * mu
    varS = float(np.sum(resid ** 2) / (len(resid) - 1))
    Kbar = float(K.mean()); Kmean2 = float((K ** 2).mean())
    rho = (varS / sig2 - Kbar) / max(Kmean2 - Kbar, 1e-12)
    neff = Kbar / (1.0 + (Kbar - 1.0) * max(rho, 0.0)) if Kbar > 1 else Kbar
    idx = np.arange(len(K)); rb = []
    for _ in range(nboot):
        b = rng.choice(idx, size=len(idx), replace=True)
        Kb, Rb = K[b], resid[b]
        vb = float(np.sum(Rb ** 2) / (len(Rb) - 1))
        kb = float(Kb.mean()); k2 = float((Kb ** 2).mean())
        rb.append((vb / sig2 - kb) / max(k2 - kb, 1e-12))
    rb = np.array(rb)
    lo, hi = float(np.percentile(rb, 2.5)), float(np.percentile(rb, 97.5))
    return {
        "n_day_groups": len(rows), "n_bets": int(K.sum()),
        "Kbar_raw_bets_per_day": Kbar,
        "per_bet_sd": math.sqrt(sig2),
        "variance_inflation": varS / (Kbar * sig2),
        "rhobar": rho, "rhobar_ci95": [lo, hi],
        "N_eff_per_day": neff,
        "N_eff_per_day_ci95": [Kbar / (1 + (Kbar - 1) * max(hi, 0.0)),
                               Kbar / (1 + (Kbar - 1) * max(lo, 0.0))],
        "direct_portfolio_check": None,
    }


def direct_check(Z, dates, cols, neutral=False):
    """Independent route: per-bet SD vs equal-weight day-portfolio SD.  ratio^2 ~= N_eff."""
    per, port = [], []
    for t in range(len(dates)):
        v = Z[t, cols]; v = v[~np.isnan(v)]
        if len(v) < 2:
            continue
        if neutral:
            v = v - v.mean()
        per.append(v); port.append(v.mean())
    if len(port) < 30:
        return None
    a = np.concatenate(per)
    sd_bet = float(a.std(ddof=1)); sd_port = float(np.std(port, ddof=1))
    return {"per_bet_sd": sd_bet, "equal_weight_day_portfolio_sd": sd_port,
            "sd_ratio": sd_bet / sd_port, "implied_N_eff": (sd_bet / sd_port) ** 2}


def main():
    dates, syms, S, Z, cls = build()
    trade = json.load(open(os.path.join(OUT, "B5_TRADEABILITY_V1.json")))["symbols"]

    def cols_for(pred):
        return [S[s] for s in syms if pred(s)]

    universes = {
        "live24_decision_surface": cols_for(lambda s: s in set(LIVE24)),
        "gtos_configured_41": cols_for(lambda s: trade[s]["ftmo_instrument_config"] or trade[s]["redacted_account_instrument_config"]),
        "both_brokers_61": cols_for(lambda s: trade[s]["ftmo_listed"] and trade[s]["redacted_account_listed"]),
        "ftmo_tradeable_166": cols_for(lambda s: trade[s]["ftmo_listed"]),
        "class_fx_43": cols_for(lambda s: cls.get(s) == "fx"),
        "class_equity_58": cols_for(lambda s: cls.get(s) == "equity"),
        "class_crypto_31": cols_for(lambda s: cls.get(s) == "crypto"),
        "class_commodity_20": cols_for(lambda s: cls.get(s) == "commodity"),
        "class_index_14": cols_for(lambda s: cls.get(s) == "index"),
        "fx_on_both_brokers_36": cols_for(lambda s: cls.get(s) == "fx" and trade[s]["ftmo_listed"] and trade[s]["redacted_account_listed"]),
    }
    res = {"config": {"vol_lookback_obs": VOL_N, "estimator": "Lane 4 day-portfolio variance ratio",
                      "seed": 20260812, "bootstrap": 400,
                      "bet_unit": "vol-normalised daily log return, strictly-past 60-obs SD",
                      "panel_dates": len(dates), "panel_first": dates[0], "panel_last": dates[-1]},
           "universes": {}}
    for name, cols in universes.items():
        if len(cols) < 2:
            continue
        raw = var_ratio(Z, dates, cols, neutral=False)
        neu = var_ratio(Z, dates, cols, neutral=True)
        if raw:
            raw["direct_portfolio_check"] = direct_check(Z, dates, cols, False)
        if neu:
            neu["direct_portfolio_check"] = direct_check(Z, dates, cols, True)
        res["universes"][name] = {"n_symbols": len(cols), "RAW": raw, "NEUTRAL": neu}
        if raw:
            print(f"{name:28s} n={len(cols):3d} Kbar={raw['Kbar_raw_bets_per_day']:6.1f} "
                  f"rho={raw['rhobar']:+.4f} Neff_raw={raw['N_eff_per_day']:7.2f} "
                  f"| neutral rho={neu['rhobar']:+.4f} Neff={neu['N_eff_per_day']:7.2f}")
    json.dump(res, open(os.path.join(OUT, "B5_EFFECTIVE_BREADTH_V1.json"), "w"), indent=1)
    print("written")


if __name__ == "__main__":
    main()
