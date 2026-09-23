"""d1_analyse — is it the SLEEVES?  Signal quality judged on its own terms.

Five questions, eight windows, whole population, no sampling.

  1  per origin family: n / gross / wr / payoff / breakeven / gap, per month and pooled
  2  each family vs a matched RANDOM baseline  (identical rows, identical instants,
     identical geometry, identical fill event, RANDOM side).  The coin flip's
     expectation is a CLOSED FORM here -- (g_long + g_short)/2 -- because the R
     frames are linear in side, so no sampling error enters the control at all.
  3  each family vs a SHUFFLED baseline (direction permuted within instrument-hour):
     separates "the family picks moments" from "the family picks direction"
  4  how much of each family's dispersion is instrument / hour / regime -- a family
     that is really "trade NAS100 at 14:00" is a schedule, not a setup
  5  is ANY family reliably gross-positive across months
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict

import numpy as np

W8 = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")
T = sys.argv[1] if len(sys.argv) > 1 else "2.0"


def load():
    A = defaultdict(list)
    for w in W8:
        z = np.load(f"/tmp/d1/out/D1_{w}.npz", allow_pickle=False)
        n = len(z["sym"])
        A["w"].append(np.array([w] * n))
        for k in ("sym", "fam", "day", "e", "d", "real_long", "is_poi", "filled",
                  "j", "past", "bh", "rv", "costL", "costS", "spreadR", "bad", "nbars"):
            A[k].append(z[k])
        for k in (f"gL_{T}", f"gS_{T}", f"codeL_{T}", f"codeS_{T}"):
            A[k].append(z[k])
        z.close()
    return {k: np.concatenate(v) for k, v in A.items()}


def econ(g, c, label="", nem=None):
    g = np.asarray(g, float)
    c = np.asarray(c, float)
    m = np.isfinite(g)
    g, c = g[m], np.nan_to_num(c[m])
    if g.size == 0:
        return {"label": label, "n": 0}
    win = g[g > 0]
    los = g[g <= 0]
    aw = float(win.mean()) if win.size else 0.0
    al = float(-los.mean()) if los.size else 0.0
    po = aw / al if al else None
    be = 1.0 / (1.0 + po) if po else None
    wr = float((g > 0).mean())
    return {
        "label": label, "n": int(g.size), "n_emissions": int(nem) if nem is not None else None,
        "fill_rate": (float(g.size) / nem) if nem else None,
        "gross": float(g.mean()), "cost": float(c.mean()), "net": float((g - c).mean()),
        "wr": wr, "avg_win": aw, "avg_loss": al, "payoff": po, "breakeven": be,
        "gap": (wr - be) if be else None, "total_gross": float(g.sum()),
    }


def dayboot(v, day, nb=4000, seed=20260806):
    v = np.asarray(v, float)
    m = np.isfinite(v)
    v, day = v[m], np.asarray(day)[m]
    if v.size == 0:
        return None
    s = defaultdict(float)
    c = defaultdict(int)
    for dd, x in zip(day, v):
        s[dd] += x
        c[dd] += 1
    ks = sorted(s)
    S = np.array([s[k] for k in ks])
    C = np.array([c[k] for k in ks], float)
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(ks), size=(nb, len(ks)))
    num = S[ix].sum(axis=1)
    den = C[ix].sum(axis=1)
    den[den == 0] = np.nan
    b = num / den
    b = b[np.isfinite(b)]
    return {"mean": float(S.sum() / C.sum()), "ci95": [float(np.percentile(b, 2.5)),
            float(np.percentile(b, 97.5))], "p_le_0": float((b <= 0).mean()),
            "p_ge_0": float((b >= 0).mean()), "n_days": len(ks)}


def eta2(y, lab):
    """share of variance of y explained by the categorical label"""
    y = np.asarray(y, float)
    m = np.isfinite(y)
    y, lab = y[m], np.asarray(lab)[m]
    if y.size < 3:
        return None
    gm = y.mean()
    sst = float(((y - gm) ** 2).sum())
    if sst <= 0:
        return None
    ssb = 0.0
    for u in np.unique(lab):
        s = lab == u
        ssb += s.sum() * (y[s].mean() - gm) ** 2
    return float(ssb / sst)


def main():
    A = load()
    n = len(A["sym"])
    gL, gS = A[f"gL_{T}"], A[f"gS_{T}"]
    rl = A["real_long"]
    g_real = np.where(rl, gL, gS)
    c_real = np.where(rl, A["costL"], A["costS"])
    g_coin = (gL + gS) / 2.0
    c_coin = (A["costL"] + A["costS"]) / 2.0
    g_anti = np.where(rl, gS, gL)
    v = g_real - g_coin                       # the direction value of THIS row

    dead = A["nbars"] == 0
    live = (~A["bad"]) & (~dead)
    fil = A["filled"] & live & np.isfinite(g_real)
    clean = fil & (~A["past"])                # past-stop rows are un-takeable geometry

    dow = np.array([np.datetime64(d).astype("datetime64[D]").astype(int) % 7 for d in A["day"]])

    # regime tertile within (window, symbol)
    reg = np.full(n, -1, dtype=np.int8)
    for w in W8:
        for s in np.unique(A["sym"]):
            m = (A["w"] == w) & (A["sym"] == s) & np.isfinite(A["rv"])
            if m.sum() < 30:
                continue
            q = np.quantile(A["rv"][m], [1 / 3, 2 / 3])
            reg[m] = np.digitize(A["rv"][m], q)

    rng = np.random.default_rng(20260806)

    def shuffled_long(keys):
        """permute the real side label inside each key group"""
        out = rl.copy()
        idx = defaultdict(list)
        for i in np.nonzero(clean)[0]:
            idx[keys[i]].append(i)
        for _, ii in idx.items():
            ii = np.array(ii)
            out[ii] = rng.permutation(rl[ii])
        return out

    key_sh = np.array([f"{a}|{b}|{c}" for a, b, c in zip(A["w"], A["sym"], A["bh"])])
    key_fsh = np.array([f"{a}|{b}|{c}|{d}" for a, b, c, d in
                        zip(A["w"], A["sym"], A["bh"], A["fam"])])
    sl_sh = shuffled_long(key_sh)
    sl_fsh = shuffled_long(key_fsh)
    g_sh = np.where(sl_sh, gL, gS)
    g_fsh = np.where(sl_fsh, gL, gS)

    R = {"schema": "gtos-d1-signal-quality-v1", "target_r": float(T), "windows": W8,
         "n_rows": int(n), "n_live": int(live.sum()), "n_filled": int(fil.sum()),
         "n_clean": int(clean.sum())}

    # ------------------------------------------------------------ 1. family economics
    fams = sorted(set(A["fam"]))
    tab = {}
    for f in fams:
        mf = (A["fam"] == f) & live
        row = {}
        row["all_fills"] = econ(g_real[mf & fil], c_real[mf & fil], f, nem=int(mf.sum()))
        mc = mf & clean
        row["clean_fills"] = econ(g_real[mc], c_real[mc], f, nem=int(mf.sum()))
        row["born_past_stop_share_of_fills"] = float(A["past"][mf & fil].mean()) if (mf & fil).sum() else None
        row["is_poi"] = f in POI
        row["d_bps_median"] = float(np.median((A["d"] / A["e"] * 1e4)[mf & fil])) if (mf & fil).sum() else None
        # per month
        pm = {}
        for w in W8:
            mm = mc & (A["w"] == w)
            if mm.sum() == 0:
                continue
            pm[w] = econ(g_real[mm], c_real[mm], w)
        row["by_month_clean"] = pm
        row["months_gross_positive"] = int(sum(1 for w in pm if pm[w]["gross"] > 0))
        row["months_net_positive"] = int(sum(1 for w in pm if pm[w]["net"] > 0))
        row["months_measured"] = len(pm)
        tab[f] = row
    R["family"] = tab

    # ------------------------------------------------------------ 2/3. controls
    ctl = {}
    for f in fams + ["__ALL__", "__ATMARKET__", "__POI__"]:
        if f == "__ALL__":
            mc = clean
        elif f == "__ATMARKET__":
            mc = clean & (~A["is_poi"])
        elif f == "__POI__":
            mc = clean & A["is_poi"]
        else:
            mc = clean & (A["fam"] == f)
        if mc.sum() == 0:
            continue
        e_real = econ(g_real[mc], c_real[mc], "real")
        e_coin = econ(g_coin[mc], c_coin[mc], "coin")
        e_anti = econ(g_anti[mc], c_real[mc], "anti")
        e_sh = econ(g_sh[mc], c_real[mc], "shuf_symhour")
        e_fsh = econ(g_fsh[mc], c_real[mc], "shuf_symhourfam")
        ctl[f] = {
            "n": int(mc.sum()),
            "real_gross": e_real["gross"], "coin_gross": e_coin["gross"],
            "anti_gross": e_anti["gross"],
            "shuf_symhour_gross": e_sh["gross"], "shuf_symhourfam_gross": e_fsh["gross"],
            "real_wr": e_real["wr"], "coin_wr": e_coin["wr"],
            "direction_value": dayboot(v[mc], A["day"][mc]),
            "vs_shuf_symhour": dayboot((g_real - g_sh)[mc], A["day"][mc]),
            "vs_shuf_symhourfam": dayboot((g_real - g_fsh)[mc], A["day"][mc]),
            "shuf_symhour_label_change_rate": float((sl_sh != rl)[mc].mean()),
            "shuf_symhourfam_label_change_rate": float((sl_fsh != rl)[mc].mean()),
            "toll": e_real["cost"],
            "direction_value_over_toll": (dayboot(v[mc], A["day"][mc])["mean"] / e_real["cost"])
            if e_real["cost"] else None,
        }
        # per-month direction value sign count
        mo = {}
        for w in W8:
            mm = mc & (A["w"] == w)
            if mm.sum() == 0:
                continue
            mo[w] = float(np.nanmean(v[mm]))
        ctl[f]["direction_value_by_month"] = mo
        ctl[f]["months_direction_value_positive"] = int(sum(1 for w in mo if mo[w] > 0))
    R["controls"] = ctl

    # ------------------------------------------------------------ 4. schedule vs setup
    sch = {}
    cellkey = np.array([f"{a}|{b}|{c}" for a, b, c in zip(A["w"], A["sym"], A["bh"])])
    for f in fams:
        mc = clean & (A["fam"] == f)
        if mc.sum() < 50:
            continue
        y = g_real[mc]
        e2 = {
            "eta2_symbol": eta2(y, A["sym"][mc]),
            "eta2_broker_hour": eta2(y, A["bh"][mc]),
            "eta2_symbol_x_hour": eta2(y, cellkey[mc]),
            "eta2_dow": eta2(y, dow[mc]),
            "eta2_vol_regime": eta2(y, reg[mc]),
            "eta2_direction": eta2(y, rl[mc]),
        }
        # leave-one-family-out ambient cell mean
        amb_sum = defaultdict(float)
        amb_cnt = defaultdict(int)
        for k, x in zip(cellkey[clean], g_real[clean]):
            if np.isfinite(x):
                amb_sum[k] += x
                amb_cnt[k] += 1
        f_sum = defaultdict(float)
        f_cnt = defaultdict(int)
        for k, x in zip(cellkey[mc], y):
            if np.isfinite(x):
                f_sum[k] += x
                f_cnt[k] += 1
        adj = []
        for k, x in zip(cellkey[mc], y):
            c0 = amb_cnt[k] - f_cnt[k]
            if c0 <= 0:
                continue
            amb = (amb_sum[k] - f_sum[k]) / c0
            adj.append(x - amb)
        e2["ambient_adjusted_mean_gross"] = float(np.mean(adj)) if adj else None
        e2["ambient_adjusted_n"] = len(adj)
        e2["raw_mean_gross"] = float(np.nanmean(y))
        # concentration
        tot = np.nansum(np.abs(y))
        by = defaultdict(float)
        for k, x in zip(cellkey[mc], y):
            if np.isfinite(x):
                by[k] += x
        top = sorted(by.items(), key=lambda t: -abs(t[1]))[:3]
        e2["top3_cells_share_of_abs_gross"] = float(sum(abs(t[1]) for t in top) / tot) if tot else None
        e2["top3_cells"] = [[t[0], round(t[1], 3)] for t in top]
        # symbol concentration of the family's rows
        us, cs = np.unique(A["sym"][mc], return_counts=True)
        e2["n_symbols"] = int(len(us))
        e2["top_symbol"] = str(us[np.argmax(cs)])
        e2["top_symbol_row_share"] = float(cs.max() / cs.sum())
        uh, ch = np.unique(A["bh"][mc], return_counts=True)
        e2["n_hours"] = int(len(uh))
        e2["top_hour"] = int(uh[np.argmax(ch)])
        e2["top_hour_row_share"] = float(ch.max() / ch.sum())
        sch[f] = e2
    R["schedule_vs_setup"] = sch

    # ------------------------------------------------------------ family x instrument
    fi = {}
    for f in fams:
        rows = []
        for s in sorted(set(A["sym"])):
            mc = clean & (A["fam"] == f) & (A["sym"] == s)
            if mc.sum() < 30:
                continue
            ee = econ(g_real[mc], c_real[mc], s)
            ee["coin_gross"] = float(np.nanmean(g_coin[mc]))
            ee["dirval"] = float(np.nanmean(v[mc]))
            rows.append(ee)
        fi[f] = sorted(rows, key=lambda r: -r["gross"])
    R["family_by_instrument"] = fi

    # ------------------------------------------------------------ family x side
    fs = {}
    for f in fams:
        o = {}
        for lab, sel in (("L", rl), ("S", ~rl)):
            mc = clean & (A["fam"] == f) & sel
            if mc.sum() < 30:
                continue
            ee = econ(g_real[mc], c_real[mc], lab)
            ee["coin_gross"] = float(np.nanmean(g_coin[mc]))
            o[lab] = ee
        fs[f] = o
    R["family_by_side"] = fs

    # ------------------------------------------------------------ pooled roster
    R["pooled"] = {
        "clean_real": econ(g_real[clean], c_real[clean], "clean_real"),
        "clean_coin": econ(g_coin[clean], c_coin[clean], "clean_coin"),
        "clean_anti": econ(g_anti[clean], c_real[clean], "clean_anti"),
        "all_fills_real": econ(g_real[fil], c_real[fil], "all_fills_real"),
        "all_fills_coin": econ(g_coin[fil], c_coin[fil], "all_fills_coin"),
        "direction_value": dayboot(v[clean], A["day"][clean]),
    }
    with open(f"/tmp/d1/D1_SIGNAL_QUALITY_T{T}.json", "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    print("wrote", f"/tmp/d1/D1_SIGNAL_QUALITY_T{T}.json")


if __name__ == "__main__":
    main()
