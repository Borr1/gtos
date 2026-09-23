"""MAGNITUDE PROGRAM — Task 1 kill test, stage 2: economics with broker-true cost.

Produces:
  BREAKOUT_ECONOMICS.csv      every (grid, channel, side, s, k, H, arm) cell
  BREAKOUT_DELTA.csv          BREAKOUT - BLIND, the instrument that isolates the trigger
  HORIZON_COST_CURVE.csv      the fixed-vs-carry cost decomposition against horizon
  CONDITIONING.csv            vol_regime quintile and session conditioning
  STABILITY.csv               per-year / per-symbol / train-test for the surviving cells

Intervals are a CLUSTER BOOTSTRAP over (symbol x calendar quarter), 1000 draws, seed
20260812. Overlapping holds (an 80-day D1 barrier re-entered every few days) make the
naive SE meaningless; the cluster is the smallest unit that is plausibly independent
across both the cross-section and time.
"""
import json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path("/tmp/mag_program/out")
SEED = 20260812
B = 1000
BAR_HOURS = {"D1": 24.0, "H4": 4.0}
TRAIN_END = 2021


def load_grid(grid, slip_mult=1.0):
    import mp_cost as mc
    ev = pd.read_parquet(OUT / f"evcost_{grid}.parquet")
    out = pd.read_parquet(OUT / f"out_{grid}.parquet")
    keep = ["uid", "symbol", "arm", "channel", "side", "atr14", "vol_regime", "year",
            "entry_time", "entry_hour", "broker_hour", "spread_price", "comm_price",
            "slip_price", "slip_fixed_r", "swap_night_price", "rollover_wd",
            "break_ext_atr", "spread_cov", "slip_cov"]
    d = out.merge(ev[keep], on="uid", how="left", copy=False)
    del out, ev
    d["hold_h"] = d["bars_held"].to_numpy(float) * BAR_HOURS[grid]
    # nights are counted per (rollover weekday) group — only two distinct values here
    nights = np.zeros(len(d))
    for rw, g in d.groupby("rollover_wd", observed=True):
        nights[g.index] = mc.rollover_nights_vec(
            g["entry_time"].to_numpy(), g["hold_h"].to_numpy(float), int(rw))
    d["nights"] = nights
    sl = d["s"].to_numpy(float) * d["atr14"].to_numpy(float)
    d["cost_fixed_r"] = ((d["spread_price"] + d["comm_price"]
                          + slip_mult * d["slip_price"]).to_numpy(float) / sl
                         + slip_mult * d["slip_fixed_r"].to_numpy(float))
    d["cost_carry_r"] = nights * d["swap_night_price"].to_numpy(float) / sl
    d["cost_r"] = d["cost_fixed_r"] + d["cost_carry_r"]
    d["net_r"] = d["r_gap"].to_numpy(float) - d["cost_r"].to_numpy(float)
    d["net_r_nogap"] = d["r"].to_numpy(float) - d["cost_r"].to_numpy(float)
    q = pd.PeriodIndex(pd.to_datetime(d["entry_time"], utc=True), freq="Q")
    d["cluster"] = d["symbol"].astype(str) + "|" + q.astype(str)
    d["grid"] = grid
    return d


def _cell_cluster_matrices(v, cellcols, valcol, split=None):
    """(clusters x cells) sums and counts. `split` gives one matrix pair per split level."""
    cidx, cuniq = pd.factorize(v["cluster"], sort=True)
    kidx, kuniq = pd.factorize(pd.MultiIndex.from_frame(v[cellcols]).to_numpy(), sort=False)
    nC, nK = len(cuniq), len(kuniq)
    vals = v[valcol].to_numpy(float)
    if split is None:
        S = np.zeros((nC, nK)); N = np.zeros((nC, nK))
        np.add.at(S, (cidx, kidx), vals)
        np.add.at(N, (cidx, kidx), 1.0)
        return kuniq, nC, {None: (S, N)}
    out = {}
    sv = v[split].to_numpy()
    for lev in pd.unique(sv):
        m = sv == lev
        S = np.zeros((nC, nK)); N = np.zeros((nC, nK))
        np.add.at(S, (cidx[m], kidx[m]), vals[m])
        np.add.at(N, (cidx[m], kidx[m]), 1.0)
        out[lev] = (S, N)
    return kuniq, nC, out


def paired_delta_ci(d, cellcols, valcol="net_r", b=B, seed=SEED, arm="arm",
                    hi="BREAKOUT", lo="BLIND"):
    """POOLED per-trade mean(hi) - mean(lo) per cell, cluster-bootstrapped.

    The estimator is the pooled per-trade difference — what a trader earns per trade —
    NOT an unweighted mean over clusters. Those differ by 0.37 R here, because quarters
    that fire many breakouts are systematically the good ones (corr n vs cell mean 0.49),
    so an unweighted cluster mean silently reweights toward quiet quarters.
    """
    v = d[[*cellcols, "cluster", arm, valcol]].dropna(subset=[valcol])
    kuniq, nC, mats = _cell_cluster_matrices(v, cellcols, valcol, split=arm)
    rng = np.random.default_rng(seed)
    W = rng.multinomial(nC, np.full(nC, 1.0 / nC), size=b).astype(np.float64)
    def pooled(S, N, Wm):
        num, den = Wm @ S, Wm @ N
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(den > 0, num / den, np.nan)
    Sh, Nh = mats[hi]; Sl, Nl = mats[lo]
    boots = pooled(Sh, Nh, W) - pooled(Sl, Nl, W)
    ones = np.ones((1, nC))
    point = (pooled(Sh, Nh, ones) - pooled(Sl, Nl, ones))[0]
    lo_, hi_ = np.nanpercentile(boots, [2.5, 97.5], axis=0)
    res = pd.DataFrame(list(kuniq), columns=cellcols)
    res["n_hi"] = Nh.sum(0).astype(int)
    res["n_lo"] = Nl.sum(0).astype(int)
    res["n_clusters"] = ((Nh > 0) & (Nl > 0)).sum(0).astype(int)
    res[valcol + "_delta"] = point
    res[valcol + "_delta_lo"] = lo_
    res[valcol + "_delta_hi"] = hi_
    res[valcol + "_delta_boot_sd"] = np.nanstd(boots, axis=0)
    return res


def cluster_ci(d, cellcols, valcol="net_r", b=B, seed=SEED):
    """Cluster-bootstrap mean and 95% interval for every cell, in one matmul."""
    v = d[[*cellcols, "cluster", valcol]].dropna(subset=[valcol])
    cell = v.groupby(cellcols, observed=True, sort=True)
    keys = list(cell.groups.keys())
    cidx, cuniq = pd.factorize(v["cluster"], sort=True)
    kidx, kuniq = pd.factorize(pd.MultiIndex.from_frame(v[cellcols]).to_numpy(), sort=False)
    nC, nK = len(cuniq), len(kuniq)
    S = np.zeros((nC, nK)); N = np.zeros((nC, nK))
    np.add.at(S, (cidx, kidx), v[valcol].to_numpy(float))
    np.add.at(N, (cidx, kidx), 1.0)
    rng = np.random.default_rng(seed)
    W = rng.multinomial(nC, np.full(nC, 1.0 / nC), size=b).astype(np.float64)  # b x nC
    num, den = W @ S, W @ N
    with np.errstate(invalid="ignore", divide="ignore"):
        boots = np.where(den > 0, num / den, np.nan)
    lo, hi = np.nanpercentile(boots, [2.5, 97.5], axis=0)
    mean = np.where(N.sum(0) > 0, S.sum(0) / np.maximum(N.sum(0), 1), np.nan)
    res = pd.DataFrame(list(kuniq), columns=cellcols)
    res["n"] = N.sum(0).astype(int)
    res["n_clusters"] = (N > 0).sum(0).astype(int)
    res[valcol + "_mean"] = mean
    res[valcol + "_lo"] = lo
    res[valcol + "_hi"] = hi
    res[valcol + "_boot_sd"] = np.nanstd(boots, axis=0)
    return res


def cell_table(d, cellcols):
    g = d.groupby(cellcols, observed=True)
    t = g.agg(n=("net_r", "size"),
              gross_r=("r_gap", "mean"), gross_nogap=("r", "mean"),
              net_r=("net_r", "mean"),
              cost_r=("cost_r", "mean"), cost_fixed=("cost_fixed_r", "mean"),
              cost_carry=("cost_carry_r", "mean"),
              mfe_atr=("mfe_atr", "mean"), mae_atr=("mae_atr", "mean"),
              hold_h=("hold_h", "median"), nights=("nights", "mean")).reset_index()
    lab = g["label"].value_counts(normalize=True).unstack(fill_value=0.0)
    lab.columns = [{0: "stop_rate", 1: "target_rate", 2: "timeout_rate"}.get(c, str(c))
                   for c in lab.columns]
    return t.merge(lab.reset_index(), on=cellcols, how="left")


def main():
    t0 = time.time()
    frames = []
    for grid in ("D1", "H4"):
        d = load_grid(grid)
        print(json.dumps({"grid": grid, "rows": int(len(d)), "t": round(time.time() - t0, 1)}),
              flush=True)
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    del frames
    CELL = ["grid", "channel", "side", "s", "k", "H", "arm"]

    # ---- A. headline economics ------------------------------------------------------
    tab = cell_table(d, CELL)
    ci = cluster_ci(d, CELL, "net_r")
    tab = tab.merge(ci.drop(columns=["n"]), on=CELL, how="left")
    cig = cluster_ci(d, CELL, "r_gap").rename(columns={c: c.replace("r_gap", "gross")
                                                       for c in ("r_gap_mean", "r_gap_lo",
                                                                 "r_gap_hi", "r_gap_boot_sd")})
    tab = tab.merge(cig[[*CELL, "gross_lo", "gross_hi"]], on=CELL, how="left")
    tab.to_csv(OUT / "BREAKOUT_ECONOMICS.csv", index=False)
    print("A done", round(time.time() - t0, 1), flush=True)

    # ---- B. the trigger's own contribution: BREAKOUT - BLIND, paired by cluster ------
    dcell = ["grid", "channel", "side", "s", "k", "H"]
    dl = paired_delta_ci(d, dcell, "net_r")
    dg = paired_delta_ci(d, dcell, "r_gap")
    dl = dl.merge(dg[[*dcell, "r_gap_delta", "r_gap_delta_lo", "r_gap_delta_hi"]],
                  on=dcell, how="left")
    dl.to_csv(OUT / "BREAKOUT_DELTA.csv", index=False)
    print("B done", round(time.time() - t0, 1), flush=True)

    # ---- C. the horizon cost curve --------------------------------------------------
    bo = d[d.arm == "BREAKOUT"]
    hc = bo.groupby(["grid", "s", "H"], observed=True).agg(
        n=("net_r", "size"), hold_h=("hold_h", "median"), nights=("nights", "mean"),
        cost_fixed=("cost_fixed_r", "mean"), cost_carry=("cost_carry_r", "mean"),
        cost_total=("cost_r", "mean"), gross=("r_gap", "mean"), net=("net_r", "mean"),
        mfe=("mfe_atr", "mean"), mae=("mae_atr", "mean")).reset_index()
    hc["carry_share"] = hc.cost_carry / hc.cost_total
    hc.to_csv(OUT / "HORIZON_COST_CURVE.csv", index=False)

    # per-symbol carry burden at the longest horizon
    sym = bo[bo.H.isin([80, 480])].groupby(["grid", "symbol", "side"], observed=True).agg(
        n=("net_r", "size"), cost_carry=("cost_carry_r", "mean"),
        cost_fixed=("cost_fixed_r", "mean"), gross=("r_gap", "mean"),
        net=("net_r", "mean")).reset_index()
    sym.to_csv(OUT / "SYMBOL_CARRY.csv", index=False)
    print("C done", round(time.time() - t0, 1), flush=True)

    # ---- D. conditioning: vol_regime quintile (within symbol) and session ------------
    bo = bo.copy()
    bo["vq"] = bo.groupby("symbol", observed=True)["vol_regime"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 5, labels=False, duplicates="drop"))
    cond = []
    for var, col in (("vol_quintile", "vq"), ("broker_hour", "broker_hour")):
        cc = ["grid", "s", "k", "H", "side", col]
        t = cell_table(bo, cc).rename(columns={col: "level"})
        t["variable"] = var
        ci2 = cluster_ci(bo, cc, "net_r").rename(columns={col: "level"})
        t = t.merge(ci2.drop(columns=["n"]).rename(columns={col: "level"}),
                    on=["grid", "s", "k", "H", "side", "level"], how="left")
        cond.append(t)
    pd.concat(cond, ignore_index=True).to_csv(OUT / "CONDITIONING.csv", index=False)
    print("D done", round(time.time() - t0, 1), flush=True)

    # ---- E. stability: per-year, per-symbol, train/test ------------------------------
    bo["era"] = np.where(bo.year <= TRAIN_END, "train_2014_2021", "test_2022_2026")
    st_year = cell_table(bo, ["grid", "channel", "side", "s", "k", "H", "year"])
    st_sym = cell_table(bo, ["grid", "channel", "side", "s", "k", "H", "symbol"])
    st_era = cell_table(bo, ["grid", "channel", "side", "s", "k", "H", "era"])
    st_year.to_csv(OUT / "STABILITY_YEAR.csv", index=False)
    st_sym.to_csv(OUT / "STABILITY_SYMBOL.csv", index=False)
    st_era.to_csv(OUT / "STABILITY_ERA.csv", index=False)
    print("DONE", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
