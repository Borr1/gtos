"""d1 (re-run) — final analyser.  Population: PB's reproduced close-only ROSTER,
8 open windows, 1,118,694 emissions, whole population, nothing sampled.

THE SIDE CONTROL, and why it had to be rebuilt.
  The estate's standard direction control mirrors the geometry about the entry price
  and re-walks (f2 PLACEBO-SIDE; d1 pass 1 COIN).  That is exact and valid wherever the
  FILL is side-independent -- the seven at-market families.  On the three POI families
  it is not: a resting BUY limit at a level BELOW the market mirrors into a SELL at the
  same level, which is not a limit order at all (it is marketable at once, at a price
  the book cannot get, with a stop that is already breached).  Measured, that arm fills
  99.66 % of the time and books about -0.955 R/trade.  It is an artifact, and this lane
  publishes it as one.
  The control used for every direction claim here is therefore the ANTI-AT-THE-FILL arm:
  at the instant price reaches the level and the real order fills, take the OPPOSITE side
  from that same price with the mirrored stop.  Same price, same trigger, opposite side,
  and it is an order the broker accepts (a stop order instead of a limit).
"""
from __future__ import annotations
import sys, os, json
import numpy as np
from collections import defaultdict

ROWS = "/tmp/d1/rows3"
OUT = "/tmp/d1/D1B_SIGNAL_QUALITY_V1.json"
WINDOWS = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
ATMARKET = {"cross_asset_lead_lag", "displacement_continuation", "liquidity_sweep_reclaim",
            "regime_transition_break", "session_open_range_break",
            "structural_distance_extreme", "volatility_compression_expansion"}
POI = ["current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"]


def blockboot(vals, blocks, nboot=4000, seed=11):
    vals = np.asarray(vals, float)
    if vals.size < 2:
        return (float("nan"), float("nan"), float("nan"))
    o = np.argsort(blocks, kind="stable")
    v = vals[o]; b = np.asarray(blocks)[o]
    ub = np.unique(b)
    st = np.searchsorted(b, ub, "left"); en = np.searchsorted(b, ub, "right")
    sums = np.add.reduceat(v, st); cnts = (en - st).astype(float)
    rs = np.random.default_rng(seed)
    idx = rs.integers(0, sums.size, size=(nboot, sums.size))
    ms = sums[idx].sum(1) / cnts[idx].sum(1)
    lo, hi = np.percentile(ms, [2.5, 97.5])
    return float(lo), float(hi), float((ms <= 0).mean())


def eta2(y, g):
    y = np.asarray(y, float)
    tot = ((y - y.mean()) ** 2).sum()
    if tot <= 0 or y.size < 2:
        return 0.0
    _, inv = np.unique(np.asarray(g), return_inverse=True)
    c = np.bincount(inv).astype(float)
    mu = np.bincount(inv, weights=y) / c
    return float((c * (mu - y.mean()) ** 2).sum() / tot)


def econ(g, c, nom):
    g = np.asarray(g, float); c = np.asarray(c, float); net = g - c
    if g.size == 0:
        return {}
    w = g[g > 0]; l = g[g <= 0]
    aw = float(w.mean()) if w.size else 0.0
    al = float(-l.mean()) if l.size else 0.0
    pay = (aw / al) if al else None
    be = (1 / (1 + pay)) if pay else None
    wr = float((g > 0).mean())
    return dict(n=int(g.size), gross=float(g.mean()), toll=float(c.mean()), net=float(net.mean()),
                win_rate=wr, avg_win=aw, avg_loss=al, payoff_realised=pay,
                breakeven_wr_realised=be, gap_realised=(wr - be) if be else None,
                breakeven_wr_nominal=1.0 / (1.0 + nom),
                gross_over_toll=(float(g.mean()) / float(c.mean())) if c.mean() else None,
                win_rate_needed_for_toll=(be + float(c.mean()) / (aw + al)) if (be and (aw + al)) else None,
                total_gross_R=float(g.sum()), total_net_R=float(net.sum()))


def load():
    P = defaultdict(list); leg = None
    for wi, w in enumerate(WINDOWS):
        d = dict(np.load(f"{ROWS}/D1_{w}.npz"))
        lg = json.load(open(f"{ROWS}/D1_{w}.legend.json")); leg = leg or lg
        n = len(d["day"])
        P["win"].append(np.full(n, wi, np.int32))
        P["blk"].append(wi * 100 + d["day"].astype(np.int32))
        for k in ("hour", "bhour", "sym", "fam", "side", "vol", "trend", "rfil", "ffil",
                  "rpast", "mfil", "mffil", "atm", "afil", "rtouch", "rrs20", "afs20"):
            P[k].append(d[k].astype(np.int32))
        for k in ("d_bps", "rr15", "rr20", "fg15", "fg20", "rcost", "fcost",
                  "mr15", "mr20", "mf15", "mf20", "af15", "af20"):
            P[k].append(d[k].astype(np.float64))
    T = {k: np.concatenate(v) for k, v in P.items()}
    T["fams"] = leg["fams"]; T["syms"] = leg["syms"]
    return T


def main():
    T = load()
    fams = [f for f in T["fams"] if f != "__other__"]
    syms = T["syms"]; N = T["win"].size
    fidx = {f: i for i, f in enumerate(T["fams"])}
    fc = T["fam"]; atm = T["atm"] == 1
    breaker = fc == fidx["current_breaker_re_entry"]
    # PASS-1 CLEAN: drop only rows born already past their stop (keeps every family)
    clean = T["rpast"] == 0
    # THE FILL EVENT under the live order type: a market order for the 7 at-market
    # families (always fills), a resting limit for the 3 POI families (may never fill).
    rf = np.where(atm, T["mfil"] == 1, T["rfil"] == 1)
    # REAL gross per fill under the live order type
    Rg = {t: np.where(atm, T["mr" + t], T["rr" + t]) for t in ("15", "20")}
    # THE SIDE CONTROL, paired arm by arm with the real one:
    #   at-market -> the mirrored market order at the same instant
    #   POI       -> the opposite side taken from the same price at the real fill instant
    Ag = {t: np.where(atm, T["mf" + t], T["af" + t]) for t in ("15", "20")}
    ok = np.where(atm, (T["mfil"] == 1) & (T["mffil"] == 1),
                  (T["rfil"] == 1) & (T["afil"] == 1))    # both arms exist

    res = {"schema": "gtos-d1b-signal-quality-v1",
           "lane": "d1 (independent re-run)",
           "population": "Session PB reproduced close-only candidate ROSTER, 8 open windows",
           "n_emissions": int(N), "n_fills": int(rf.sum()),
           "n_clean_fills": int((rf & clean).sum()), "windows": WINDOWS,
           "contract": {
               "fill_at_market_families": "market fill at the generator's emitted entry; path = stamps i+1..i+120",
               "fill_poi_families": "honest resting limit at the emitted entry, scanned i..i+119; never touched -> no trade",
               "targets": {"1.5": "the generator's OWN emitted take_profit_1 (risk.min_rr = 1.5)",
                           "2.0": "the downstream geometry f1/f2 priced"},
               "stop": "-1R", "tie_rule": "stop wins inside one M1 bar",
               "toll": "h1 four-term broker-true price-unit cost / this row's risk distance",
               "side_control": "ANTI AT THE FILL: opposite side from the same price at the same instant, mirrored stop"}}

    # ---------- harness validation against the two committed wave-19 artifacts ----------
    lf = T["rfil"] == 1
    f1clean = (~breaker) & (T["rpast"] == 0)
    res["harness_validation"] = {
        "f1_roster_all_emissions_t20_limit_contract": econ(
            np.where(lf, T["rr20"], 0.0), np.where(lf, T["rcost"], 0.0), 2.0),
        "f1_roster_filled_t20_limit_contract": econ(T["rr20"][lf], T["rcost"][lf], 2.0),
        "f1_roster_filled_clean_t20_limit_contract": econ(
            T["rr20"][lf & f1clean], T["rcost"][lf & f1clean], 2.0),
        "f1_published": {"all_emissions": {"n": 1118694, "gross": -0.024400982646910315,
                                           "cost": 0.08317939718668416},
                         "filled": {"n": 331548, "gross": -0.08233267243718162,
                                    "cost": 0.28066009312787427},
                         "filled_clean": {"n": 298537, "gross": -0.013268637647644799}}}

    groups = [(f, fc == fidx[f]) for f in fams if (fc == fidx[f]).any()]
    groups += [("__ALL__", np.ones(N, bool)),
               ("__ATMARKET__", atm), ("__POI__", ~atm),
               ("__CLEAN_NO_BREAKER__", ~breaker)]

    # ---------- (1) family economics ----------
    tbl = {}
    for name, m0 in groups:
        m = m0 & clean & rf
        if m.sum() < 30:
            continue
        rec = {"n_emissions": int((m0 & clean).sum()), "n_fills": int(m.sum()),
               "fill_rate": float(rf[m0 & clean].mean()),
               "at_market": bool(name in ATMARKET),
               "d_bps_median": float(np.median(T["d_bps"][m])),
               "long_share": float((T["side"][m] == 1).mean()),
               "past_stop_share_of_all_fills": float(T["rpast"][m0 & rf].mean())}
        for t, nom in (("15", 1.5), ("20", 2.0)):
            e = econ(Rg[t][m], T["rcost"][m], nom)
            lo, hi, p = blockboot(Rg[t][m], T["blk"][m])
            e["blockboot_ci95"] = [lo, hi]; e["p_le_0"] = p; e["p_ge_0"] = 1.0 - p
            rec["t" + t] = e
            pw, pos = {}, 0
            for wi, w in enumerate(WINDOWS):
                mm = m & (T["win"] == wi)
                if mm.sum() == 0:
                    continue
                v = float(Rg[t][mm].mean()); pw[w] = {"n": int(mm.sum()), "gross": v,
                                                      "net": float((Rg[t][mm] - T["rcost"][mm]).mean())}
                pos += 1 if v > 0 else 0
            rec["by_window_t" + t] = pw
            rec["months_gross_positive_t" + t] = pos
            rec["n_windows"] = len(pw)
        tbl[name] = rec
    res["family_economics"] = tbl

    # ---------- (2) the fill-convention correction to f1's roster table ----------
    conv = {}
    for name, m0 in [(f, fc == fidx[f]) for f in fams if f in ATMARKET] + [("__ATMARKET__", atm)]:
        m = m0 & clean
        if m.sum() < 30:
            continue
        lim = m & (T["rfil"] == 1)
        conv[name] = {"n_emissions": int(m.sum()),
                      "limit_contract_fill_rate": float((T["rfil"][m] == 1).mean()),
                      "gross_t20_limit_contract": float(T["rr20"][lim].mean()),
                      "gross_t20_market_contract": float(T["mr20"][m & (T["mfil"] == 1)].mean()),
                      "delta": float(T["mr20"][m & (T["mfil"] == 1)].mean() - T["rr20"][lim].mean())}
        d = np.where(T["mfil"][m] == 1, T["mr20"][m], 0.0) - np.where(T["rfil"][m] == 1, T["rr20"][m], 0.0)
        lo, hi, p = blockboot(d, T["blk"][m])
        conv[name]["delta_ci95"] = [lo, hi]; conv[name]["delta_p_le_0"] = p
    res["fill_convention_correction"] = conv

    # ---------- (3) direction controls ----------
    cell = (T["win"].astype(np.int64) * 100000 + T["sym"].astype(np.int64) * 100
            + T["bhour"].astype(np.int64))
    ctl = {}
    for t in ("15", "20"):
        R = Rg[t]; A = Ag[t]
        COIN = 0.5 * (R + A)
        isL = T["side"] == 1
        Lo_ = np.where(isL, R, A); So_ = np.where(isL, A, R)
        rows = {}
        for name, m0 in groups:
            m = m0 & clean & ok
            if m.sum() < 100:
                continue
            # cell shares computed on THIS subset so the shuffle preserves its own mix
            for lbl, key in (("cell", cell[m]), ("cell_family", cell[m] * 20 + fc[m])):
                pass
            u, inv = np.unique(cell[m], return_inverse=True)
            cnt = np.bincount(inv).astype(float)
            pl = (np.bincount(inv, weights=isL[m].astype(float)) / cnt)[inv]
            SH = pl * Lo_[m] + (1 - pl) * So_[m]
            cf = cell[m] * 20 + fc[m]
            u2, inv2 = np.unique(cf, return_inverse=True)
            cnt2 = np.bincount(inv2).astype(float)
            pl2 = (np.bincount(inv2, weights=isL[m].astype(float)) / cnt2)[inv2]
            SHF = pl2 * Lo_[m] + (1 - pl2) * So_[m]
            dC = R[m] - COIN[m]; dS = R[m] - SH; dSF = R[m] - SHF; dL = SH - COIN[m]
            l1, h1, p1 = blockboot(dC, T["blk"][m])
            l2, h2, p2 = blockboot(dS, T["blk"][m])
            l3, h3, p3 = blockboot(dSF, T["blk"][m])
            l4, h4, p4 = blockboot(dL, T["blk"][m])
            pos = sum(1 for wi in range(8)
                      if (m & (T["win"] == wi)).sum() and
                      (R[m & (T["win"] == wi)] - COIN[m & (T["win"] == wi)]).mean() > 0)
            rows[name] = {"n": int(m.sum()), "real": float(R[m].mean()),
                          "anti_at_fill": float(A[m].mean()), "coinflip": float(COIN[m].mean()),
                          "shuffle_cell": float(SH.mean()), "shuffle_cell_family": float(SHF.mean()),
                          "toll": float(T["rcost"][m].mean()),
                          "direction_value": float(dC.mean()), "direction_ci95": [l1, h1],
                          "direction_p_le_0": p1, "direction_p_ge_0": 1.0 - p1,
                          "vs_shuffle_cell": float(dS.mean()), "shuffle_cell_ci95": [l2, h2],
                          "shuffle_cell_p_le_0": p2,
                          "vs_shuffle_cell_family": float(dSF.mean()),
                          "shuffle_cell_family_ci95": [l3, h3], "shuffle_cell_family_p_le_0": p3,
                          "lean_component": float(dL.mean()), "lean_ci95": [l4, h4], "lean_p_le_0": p4,
                          "months_direction_positive": pos,
                          "real_win_rate": float((R[m] > 0).mean()),
                          "coin_win_rate": float(((R[m] > 0).astype(float).mean()
                                                  + (A[m] > 0).astype(float).mean()) / 2),
                          "direction_over_toll": float(dC.mean() / T["rcost"][m].mean())}
        ctl["t" + t] = rows
    res["direction_controls"] = ctl

    # ---------- (4) the mirrored-limit ARTIFACT, published as one ----------
    art = {}
    for name, m0 in [(f, fc == fidx[f]) for f in POI] + [("__POI__", ~atm), ("__ATMARKET__", atm)]:
        m = m0 & clean
        if m.sum() < 100:
            continue
        art[name] = {"n_emissions": int(m.sum()),
                     "real_limit_fill_rate": float((T["rfil"][m] == 1).mean()),
                     "MIRRORED_limit_fill_rate": float((T["ffil"][m] == 1).mean()),
                     "mirrored_limit_gross_per_fill_t20": float(T["fg20"][m & (T["ffil"] == 1)].mean()),
                     "anti_at_fill_gross_t20": float(T["af20"][m & ok].mean()),
                     "note": "a mirrored resting limit at the same price is marketable at once; on POI levels it books a near-mechanical -1R"}
    res["mirrored_limit_artifact"] = art

    # ---------- (5) spec layer: family x side ----------
    spec = {}
    for f in fams:
        for sd, sn in ((1, "LONG"), (0, "SHORT")):
            m = (fc == fidx[f]) & (T["side"] == sd) & clean & rf
            if m.sum() < 100:
                continue
            rec = {"n_fills": int(m.sum())}
            for t, nom in (("15", 1.5), ("20", 2.0)):
                e = econ(Rg[t][m], T["rcost"][m], nom)
                lo, hi, p = blockboot(Rg[t][m], T["blk"][m])
                e["blockboot_ci95"] = [lo, hi]; e["p_le_0"] = p
                pos = sum(1 for wi in range(8) if (m & (T["win"] == wi)).sum()
                          and Rg[t][m & (T["win"] == wi)].mean() > 0)
                e["months_gross_positive"] = pos
                e["n_windows"] = sum(1 for wi in range(8) if (m & (T["win"] == wi)).sum() > 0)
                rec["t" + t] = e
            mo = m & ok
            rec["direction_value_t20"] = float((Rg["20"][mo] - 0.5 * (Rg["20"][mo] + Ag["20"][mo])).mean())
            spec[f"{f}|{sn}"] = rec
    res["spec_family_side"] = spec

    # ---------- (6) schedule vs setup ----------
    ve = {}
    symhour = T["sym"].astype(np.int64) * 100 + T["bhour"].astype(np.int64)
    rs = np.random.default_rng(3)
    for name, m0 in groups:
        m = m0 & clean & rf
        if m.sum() < 500:
            continue
        y = Rg["20"][m]
        rec = {"n_fills": int(m.sum())}
        for lbl, g in (("symbol", T["sym"][m]), ("broker_hour", T["bhour"][m]),
                       ("symbol_x_hour", symhour[m]), ("vol_tercile", T["vol"][m]),
                       ("trend_sign", T["trend"][m]), ("side", T["side"][m]),
                       ("day", T["blk"][m])):
            obs = eta2(y, g)
            null = float(np.mean([eta2(rs.permutation(y), g) for _ in range(40)]))
            rec["eta2_" + lbl] = obs
            rec["eta2_" + lbl + "_excess_over_permutation_null"] = obs - null
        s = T["sym"][m]
        tots = {syms[si]: float(y[s == si].sum()) for si in np.unique(s)}
        gt = sum(abs(v) for v in tots.values()) or 1.0
        rec["top3_symbols"] = [{"symbol": k, "total_gross_R": v, "share_of_abs": abs(v) / gt}
                               for k, v in sorted(tots.items(), key=lambda kv: -abs(kv[1]))[:3]]
        rec["n_symbols_gross_positive"] = int(sum(1 for si in np.unique(s) if y[s == si].mean() > 0))
        rec["n_symbols"] = int(np.unique(s).size)
        hb = np.bincount(T["bhour"][m], minlength=24).astype(float)
        rec["top_broker_hour"] = int(np.argmax(hb)); rec["top_broker_hour_share"] = float(hb.max() / hb.sum())
        ve[name] = rec
    res["schedule_vs_setup"] = ve

    # ---------- (7) chronological hold-out ----------
    ho = {}
    for name, m0 in groups:
        m = m0 & clean & rf
        if m.sum() < 500:
            continue
        y = Rg["20"][m]; wm = T["win"][m]; bk = T["blk"][m]

        def sub(sel):
            if sel.sum() < 50:
                return None
            lo, hi, p = blockboot(y[sel], bk[sel])
            return {"n": int(sel.sum()), "gross": float(y[sel].mean()), "ci95": [lo, hi], "p_le_0": p}
        ho[name] = {"first4_2025_10_to_2026_01": sub(wm <= 3),
                    "last4_2026_02_to_2026_05": sub(wm >= 4),
                    "first6": sub(wm <= 5), "last2_2026_04_05": sub(wm >= 6)}
    res["chronological_holdout_t20"] = ho

    # ---------- (8) the breaker inversion, priced ----------
    m = breaker & clean & ok
    inv_ = {}
    for t, nom in (("15", 1.5), ("20", 2.0)):
        e_r = econ(Rg[t][m], T["rcost"][m], nom)
        e_a = econ(Ag[t][m], T["rcost"][m], nom)
        lo, hi, p = blockboot(Ag[t][m] - T["rcost"][m], T["blk"][m])
        inv_["t" + t] = {"real": e_r, "inverted": e_a,
                         "inverted_net_ci95": [lo, hi], "inverted_net_p_le_0": p,
                         "inverted_months_gross_positive": sum(
                             1 for wi in range(8) if (m & (T["win"] == wi)).sum()
                             and Ag[t][m & (T["win"] == wi)].mean() > 0)}
    mall = breaker & ok
    inv_["all_rows_including_born_past_stop_t20"] = {
        "n": int(mall.sum()), "real_gross": float(Rg["20"][mall].mean()),
        "inverted_gross": float(Ag["20"][mall].mean()),
        "inverted_net": float((Ag["20"][mall] - T["rcost"][mall]).mean()),
        "born_past_stop_share": float(T["rpast"][mall].mean())}
    res["breaker_inversion_priced"] = inv_

    json.dump(res, open(OUT, "w"), indent=1)
    print("wrote", OUT, "N", N)


if __name__ == "__main__":
    main()
