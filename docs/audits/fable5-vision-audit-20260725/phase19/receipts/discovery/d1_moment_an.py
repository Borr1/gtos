"""d1_moment_an — decompose each family into MOMENT value and DIRECTION value."""
from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

W8 = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")


def dayboot(v, day, nb=4000, seed=20260806):
    v = np.asarray(v, float)
    m = np.isfinite(v)
    v, day = v[m], np.asarray(day)[m]
    if v.size == 0:
        return None
    s, c = defaultdict(float), defaultdict(int)
    for dd, x in zip(day, v):
        s[dd] += x
        c[dd] += 1
    ks = sorted(s)
    S = np.array([s[k] for k in ks])
    C = np.array([c[k] for k in ks], float)
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(ks), size=(nb, len(ks)))
    num, den = S[ix].sum(axis=1), C[ix].sum(axis=1)
    den[den == 0] = np.nan
    b = num / den
    b = b[np.isfinite(b)]
    return {"mean": float(S.sum() / C.sum()),
            "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
            "p_le_0": float((b <= 0).mean()), "n_days": len(ks)}


def main():
    real_g, coin_g, mom_g, mom_c, fam, day, w, cost = [], [], [], [], [], [], [], []
    for win in W8:
        z = np.load(f"/tmp/d1/out/D1_{win}.npz", allow_pickle=False)
        m = np.load(f"/tmp/d1/out/MOM_{win}.npz", allow_pickle=False)
        sel = m["sel"]
        gL, gS = z["gL_2.0"][sel], z["gS_2.0"][sel]
        rl = z["real_long"][sel]
        real_g.append(np.where(rl, gL, gS))
        coin_g.append((gL + gS) / 2.0)
        cost.append(np.where(rl, z["costL"][sel], z["costS"][sel]))
        mom_g.append(np.nanmean(m["g"], axis=0))
        mom_c.append(np.nanmean(m["c"], axis=0))
        fam.append(m["fam"])
        day.append(m["day"])
        w.append(np.array([win] * len(sel)))
        z.close()
        m.close()
    real_g = np.concatenate(real_g)
    coin_g = np.concatenate(coin_g)
    mom_g = np.concatenate(mom_g)
    mom_c = np.concatenate(mom_c)
    cost = np.concatenate(cost)
    fam = np.concatenate(fam)
    day = np.concatenate(day)
    w = np.concatenate(w)

    ok = np.isfinite(mom_g) & np.isfinite(real_g) & np.isfinite(coin_g)
    out = {"schema": "gtos-d1-moment-decomp-v1", "n_rows": int(ok.sum()),
           "n_rows_total": int(len(real_g)),
           "moment_placebo_coverage": float(ok.mean()), "n_draws_per_row": 3}
    rows = {}
    fams = sorted(set(fam))
    for f in fams + ["__ALL__", "__ATMARKET__", "__POI__"]:
        if f == "__ALL__":
            s = ok
        elif f == "__ATMARKET__":
            s = ok & ~np.isin(fam, POI)
        elif f == "__POI__":
            s = ok & np.isin(fam, POI)
        else:
            s = ok & (fam == f)
        if s.sum() < 50:
            continue
        momv = coin_g[s] - mom_g[s]           # value of choosing THIS moment
        dirv = real_g[s] - coin_g[s]          # value of choosing THIS direction
        tot = real_g[s] - mom_g[s]            # total value over an arbitrary moment+side
        mb = dayboot(momv, day[s])
        db = dayboot(dirv, day[s])
        tb = dayboot(tot, day[s])
        mo_m, mo_d = {}, {}
        for win in W8:
            ss = s & (w == win)
            if ss.sum() == 0:
                continue
            mo_m[win] = float(np.nanmean(coin_g[ss] - mom_g[ss]))
            mo_d[win] = float(np.nanmean(real_g[ss] - coin_g[ss]))
        rows[f] = {
            "n": int(s.sum()),
            "real_gross": float(np.nanmean(real_g[s])),
            "coin_gross": float(np.nanmean(coin_g[s])),
            "random_moment_coin_gross": float(np.nanmean(mom_g[s])),
            "toll_real": float(np.nanmean(cost[s])),
            "toll_random_moment": float(np.nanmean(mom_c[s])),
            "moment_value": mb, "direction_value": db, "total_value": tb,
            "moment_value_by_month": mo_m, "direction_value_by_month": mo_d,
            "months_moment_positive": int(sum(1 for x in mo_m.values() if x > 0)),
            "months_direction_positive": int(sum(1 for x in mo_d.values() if x > 0)),
            "moment_value_over_toll": float(mb["mean"] / np.nanmean(cost[s])),
            "total_value_over_toll": float(tb["mean"] / np.nanmean(cost[s])),
        }
    out["decomposition"] = rows
    with open("/tmp/d1/D1_MOMENT_V1.json", "w") as fh:
        json.dump(out, fh, indent=1, default=float)
    print("wrote /tmp/d1/D1_MOMENT_V1.json  n=", int(ok.sum()))


if __name__ == "__main__":
    main()
