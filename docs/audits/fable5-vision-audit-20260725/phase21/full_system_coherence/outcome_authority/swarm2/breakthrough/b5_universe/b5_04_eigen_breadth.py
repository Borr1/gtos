"""B5 step (b2) — effective breadth by eigenvalue participation ratio.

Why a second instrument.  Lane 4's day-portfolio variance ratio assumes EQUICORRELATION
within the group (its own §8 flags this: "real correlation is clustered ... a single rhobar
understates diversification in the tails and overstates it in the clusters").  On a
166-symbol universe with a 9-symbol crypto cluster and a 43-symbol FX bloc that assumption
is materially wrong, and the demeaned/dollar-neutral version of the variance-ratio estimator
is DEGENERATE — cross-sectional demeaning forces the day-sum to exactly zero, so it returns
N_eff = Kbar mechanically and measures nothing.

The participation ratio of the correlation matrix has neither problem:
    N_eff = (sum lambda_i)^2 / sum lambda_i^2 = K^2 / ||C||_F^2
It is exact for any correlation structure, needs no equicorrelation assumption, and equals K
for the identity matrix and 1 for a perfectly correlated block.  Reported three ways:
    ALL_FACTORS      the raw universe as a directional book sees it
    EX_MARKET        after projecting out the first principal component (what a dollar-neutral
                     long/short book harvests)
    EX_TOP3          after projecting out the first three (market + two bloc factors)

Complete-case only, on a per-universe window where coverage is dense, so the matrix is PSD
by construction.  Writes <OUT>/B5_EIGEN_BREADTH_V1.json.  Runtime ~20 s.
"""
import json, math, os, pickle
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "b5_receipts")
SCRATCH = "/Users/borr/.claude/jobs/adb9e69b/tmp/b5"
VOL_N = 60
LIVE24 = ["AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY", "EURUSD",
          "GBPJPY", "GBPUSD", "GER40_cash", "JP225_cash", "US100_cash", "NZDUSD", "US500_cash",
          "UK100_cash", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF", "USDJPY", "USOIL_cash",
          "XAGUSD", "XAUUSD"]


def build_z():
    d = pickle.load(open(os.path.join(SCRATCH, "panel_d1.pkl"), "rb"))
    panel, dates = d["panel"], d["dates"]
    syms = sorted({s for dt in dates for s in panel[dt]})
    S = {s: i for i, s in enumerate(syms)}
    T, N = len(dates), len(syms)
    LC = np.full((T, N), np.nan)
    for ti, dt in enumerate(dates):
        for s, v in panel[dt].items():
            LC[ti, S[s]] = math.log(v[3])
    Z = np.full((T, N), np.nan)
    for s in syms:
        j = S[s]; ts = np.where(~np.isnan(LC[:, j]))[0]; lc = LC[ts, j]
        if len(lc) < VOL_N + 2:
            continue
        r = np.diff(lc); n = VOL_N
        cs = np.cumsum(np.insert(r, 0, 0.0)); cs2 = np.cumsum(np.insert(r * r, 0, 0.0))
        m = (cs[n:] - cs[:-n]) / n; m2 = (cs2[n:] - cs2[:-n]) / n
        sd = np.sqrt(np.maximum(m2 - m * m, 0.0) * n / (n - 1))
        for k in range(n + 1, len(ts)):
            s_ = sd[k - n - 1]
            if s_ > 0:
                Z[ts[k], j] = r[k - 1] / s_
    return dates, syms, S, Z, d["cls"]


def participation(C):
    """N_eff = (sum lam)^2 / sum lam^2 for a correlation matrix; equals K^2/||C||_F^2."""
    lam = np.linalg.eigvalsh(C)
    lam = np.clip(lam, 0.0, None)
    return float(lam.sum() ** 2 / max((lam ** 2).sum(), 1e-12)), lam


def strip_top(C, k):
    """Project out the k leading eigenvectors, renormalise the residual to a correlation matrix."""
    lam, V = np.linalg.eigh(C)
    order = np.argsort(lam)[::-1]
    lam, V = lam[order], V[:, order]
    lam2 = lam.copy(); lam2[:k] = 0.0
    R = V @ np.diag(lam2) @ V.T
    dg = np.sqrt(np.clip(np.diag(R), 1e-12, None))
    return R / np.outer(dg, dg), float(lam[:k].sum() / lam.sum())


def run(Z, dates, cols, min_obs=250, cov_floor=0.90):
    """Complete-case window: keep dates where >= cov_floor of the subset is present."""
    sub = Z[:, cols]
    present = ~np.isnan(sub)
    keep = present.mean(axis=1) >= cov_floor
    rows = np.where(keep)[0]
    if len(rows) < min_obs:
        # relax to the densest contiguous tail
        cov = present.mean(axis=1)
        thr = np.quantile(cov[cov > 0], 0.5)
        rows = np.where(cov >= thr)[0]
        if len(rows) < min_obs:
            return None
    X = sub[rows]
    good = ~np.isnan(X).any(axis=1)
    X = X[good]
    if len(X) < min_obs:
        # drop the sparsest symbols until complete-case survives
        colcov = (~np.isnan(sub[rows])).mean(axis=0)
        keepc = np.argsort(colcov)[::-1]
        for cut in range(len(cols), 1, -1):
            cc = np.sort(keepc[:cut])
            X2 = sub[np.ix_(rows, cc)]
            X2 = X2[~np.isnan(X2).any(axis=1)]
            if len(X2) >= min_obs:
                X = X2; cols = [cols[i] for i in cc]
                break
        else:
            return None
    K = X.shape[1]
    C = np.corrcoef(X, rowvar=False)
    C = np.nan_to_num(C, nan=0.0)
    np.fill_diagonal(C, 1.0)
    n_all, lam = participation(C)
    C1, share1 = strip_top(C, 1)
    n_ex1, _ = participation(C1)
    C3, share3 = strip_top(C, 3)
    n_ex3, _ = participation(C3)
    iu = np.triu_indices(K, 1)
    pw = C[iu]
    return {
        "n_symbols_used": K, "n_complete_days": int(len(X)),
        "window": [dates[int(rows[0])][:10], dates[int(rows[-1])][:10]],
        "mean_pairwise_corr": float(pw.mean()), "median_pairwise_corr": float(np.median(pw)),
        "p95_pairwise_corr": float(np.percentile(pw, 95)),
        "frac_pairs_abs_gt_0.2": float((np.abs(pw) > 0.2).mean()),
        "top_eigenvalue_share": float(lam.max() / lam.sum()),
        "N_eff_ALL_FACTORS": n_all,
        "N_eff_EX_MARKET": n_ex1, "variance_share_market": share1,
        "N_eff_EX_TOP3": n_ex3, "variance_share_top3": share3,
    }


def main():
    dates, syms, S, Z, cls = build_z()
    trade = json.load(open(os.path.join(OUT, "B5_TRADEABILITY_V1.json")))["symbols"]

    def cols_for(pred):
        return [S[s] for s in syms if pred(s)]

    U = {
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
    res = {"config": {"instrument": "eigenvalue participation ratio of the z correlation matrix",
                      "bet_unit": "vol-normalised daily log return (60-obs strictly-past SD)",
                      "complete_case": True, "coverage_floor": 0.90, "min_days": 250},
           "universes": {}}
    for name, cols in U.items():
        r = run(Z, dates, cols)
        res["universes"][name] = r
        if r:
            print(f"{name:28s} K={r['n_symbols_used']:3d} days={r['n_complete_days']:5d} "
                  f"mean_rho={r['mean_pairwise_corr']:+.4f} pc1={r['top_eigenvalue_share']:.3f} "
                  f"Neff_all={r['N_eff_ALL_FACTORS']:6.2f} exMkt={r['N_eff_EX_MARKET']:6.2f} exTop3={r['N_eff_EX_TOP3']:6.2f} "
                  f"{r['window'][0]}..{r['window'][1]}")
        else:
            print(f"{name:28s} INSUFFICIENT complete-case coverage")
    json.dump(res, open(os.path.join(OUT, "B5_EIGEN_BREADTH_V1.json"), "w"), indent=1)
    print("written")


if __name__ == "__main__":
    main()
