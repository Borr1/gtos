"""d1_analyse2 — significance, permutation nulls, and the affordability question."""
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


def eta2_with_null(y, lab, nperm=200, seed=7):
    y = np.asarray(y, float)
    m = np.isfinite(y)
    y, lab = y[m], np.asarray(lab)[m]
    if y.size < 30:
        return None
    codes, inv = np.unique(lab, return_inverse=True)
    k = len(codes)
    gm = y.mean()
    sst = float(((y - gm) ** 2).sum())
    if sst <= 0:
        return None

    def one(iv):
        s = np.bincount(iv, weights=y, minlength=k)
        c = np.bincount(iv, minlength=k).astype(float)
        c[c == 0] = np.nan
        mu = s / c
        return float(np.nansum(c * (mu - gm) ** 2) / sst)

    obs = one(inv)
    rng = np.random.default_rng(seed)
    nul = np.array([one(rng.permutation(inv)) for _ in range(nperm)])
    return {"eta2": obs, "eta2_null_mean": float(nul.mean()),
            "eta2_null_p95": float(np.percentile(nul, 95)),
            "excess": float(obs - nul.mean()), "k_levels": int(k),
            "p_ge_obs": float((nul >= obs).mean())}


def main():
    A = load()
    gL, gS = A[f"gL_{T}"], A[f"gS_{T}"]
    rl = A["real_long"]
    g = np.where(rl, gL, gS)
    c = np.where(rl, A["costL"], A["costS"])
    gc = (gL + gS) / 2.0
    v = g - gc
    live = (~A["bad"]) & (A["nbars"] > 0)
    clean = A["filled"] & live & np.isfinite(g) & (~A["past"])
    dbps = A["d"] / A["e"] * 1e4
    fams = sorted(set(A["fam"]))
    R = {"schema": "gtos-d1-signal-quality-sig-v1", "target_r": float(T)}

    # --- per-family significance on GROSS and NET, monthly sign test
    sig = {}
    from math import comb
    for f in fams + ["__ALL__", "__ATMARKET__", "__POI__"]:
        if f == "__ALL__":
            m = clean
        elif f == "__ATMARKET__":
            m = clean & ~A["is_poi"]
        elif f == "__POI__":
            m = clean & A["is_poi"]
        else:
            m = clean & (A["fam"] == f)
        if m.sum() < 30:
            continue
        gb = dayboot(g[m], A["day"][m])
        nb = dayboot((g - c)[m], A["day"][m])
        mg = [float(np.nanmean(g[m & (A["w"] == w)])) for w in W8 if (m & (A["w"] == w)).sum() > 0]
        kpos = sum(1 for x in mg if x > 0)
        n_m = len(mg)
        p_sign = sum(comb(n_m, i) for i in range(kpos, n_m + 1)) / 2 ** n_m
        sig[f] = {"n": int(m.sum()), "gross": gb, "net": nb,
                  "months_positive": kpos, "months": n_m, "sign_test_p_one_sided": p_sign,
                  "toll": float(np.nanmean(c[m])),
                  "gross_over_toll": float(gb["mean"] / np.nanmean(c[m])),
                  "dirval_over_toll": float(np.nanmean(v[m]) / np.nanmean(c[m])),
                  "d_bps_median": float(np.median(dbps[m])),
                  "monthly_gross": mg}
    R["significance"] = sig

    # --- permutation-null eta2 for the schedule question
    sch = {}
    cellkey = np.array([f"{a}|{b}|{c2}" for a, b, c2 in zip(A["w"], A["sym"], A["bh"])])
    dow = np.array([np.datetime64(d).astype("datetime64[D]").astype(int) % 7 for d in A["day"]])
    reg = np.full(len(g), -1, dtype=np.int8)
    for w in W8:
        for s in np.unique(A["sym"]):
            mm = (A["w"] == w) & (A["sym"] == s) & np.isfinite(A["rv"])
            if mm.sum() < 30:
                continue
            q = np.quantile(A["rv"][mm], [1 / 3, 2 / 3])
            reg[mm] = np.digitize(A["rv"][mm], q)
    for f in fams:
        m = clean & (A["fam"] == f)
        if m.sum() < 200:
            continue
        y = g[m]
        sch[f] = {
            "symbol": eta2_with_null(y, A["sym"][m]),
            "broker_hour": eta2_with_null(y, A["bh"][m]),
            "symbol_x_hour": eta2_with_null(y, cellkey[m]),
            "dow": eta2_with_null(y, dow[m]),
            "vol_regime": eta2_with_null(y, reg[m]),
            "side": eta2_with_null(y, rl[m]),
        }
    R["schedule_perm"] = sch

    # --- realizable sampled coin flip (win rate + payoff are NOT linear, so sample)
    rng = np.random.default_rng(11)
    draws = []
    for _ in range(200):
        pick = rng.random(len(g)) < 0.5
        gg = np.where(pick, gL, gS)[clean]
        gg = gg[np.isfinite(gg)]
        w_ = gg > 0
        aw = gg[w_].mean() if w_.any() else 0.0
        al = -gg[~w_].mean() if (~w_).any() else 0.0
        draws.append((gg.mean(), w_.mean(), aw / al if al else np.nan))
    d_ = np.array(draws)
    R["sampled_coin_flip"] = {
        "gross_mean": float(d_[:, 0].mean()), "gross_ci95": [float(np.percentile(d_[:, 0], 2.5)),
                                                             float(np.percentile(d_[:, 0], 97.5))],
        "win_rate_mean": float(d_[:, 1].mean()),
        "payoff_mean": float(d_[:, 2].mean()),
        "breakeven_mean": float((1 / (1 + d_[:, 2])).mean()),
        "n_draws": 200,
        "closed_form_gross": float(np.nanmean(gc[clean])),
    }

    # --- affordability: can ANY risk-distance slice of the best families pay its toll?
    aff = {}
    for f in ["structural_distance_extreme", "cross_asset_lead_lag", "liquidity_sweep_reclaim",
              "displacement_continuation", "session_open_range_break", "__ATMARKET__", "__ALL__"]:
        if f == "__ATMARKET__":
            m = clean & ~A["is_poi"]
        elif f == "__ALL__":
            m = clean
        else:
            m = clean & (A["fam"] == f)
        if m.sum() < 100:
            continue
        d2, g2, c2 = dbps[m], g[m], c[m]
        q = np.quantile(d2, np.linspace(0, 1, 11))
        rows = []
        for i in range(10):
            s = (d2 >= q[i]) & (d2 <= q[i + 1]) if i == 9 else (d2 >= q[i]) & (d2 < q[i + 1])
            if s.sum() == 0:
                continue
            rows.append({"decile": i + 1, "d_lo": float(q[i]), "d_hi": float(q[i + 1]),
                         "n": int(s.sum()), "gross": float(np.nanmean(g2[s])),
                         "cost": float(np.nanmean(c2[s])), "net": float(np.nanmean((g2 - c2)[s]))})
        aff[f] = rows
    R["affordability_deciles"] = aff

    with open(f"/tmp/d1/D1_SIG_T{T}.json", "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    print("wrote", f"/tmp/d1/D1_SIG_T{T}.json")


if __name__ == "__main__":
    main()
