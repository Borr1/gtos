"""b2 — the two cross-lane checks nobody ran, before writing the owner report.

PART A. Every lane's headline cell is scored on the SAME contract the swarm published
        (k=5, TRAIL025). h6-F8 measured that that contract's gross carries +0.084014
        R/trade of bar-resolution premium: e_lib.walk arms the trail off a bar's HIGH
        and only TESTS the tightened stop from the NEXT bar. The estate has already
        ratified the conservative bound (B613 / AD 95.8% intrabar). Nobody re-priced
        h1/h2/h3/h5's cells under it. This does, at hour-true broker cost.

PART B. h6's paying cell is `k=3, plain -1R stop, no target, NO trail, close at 120min`
        gated on hour-true round-trip cost <= 0.60 bps. That is EXACTLY the shipped
        `K3_STOPONLY` column. h5 built April and May at-market cohorts (13,837 + 11,888)
        that no lane ever scored on a no-trail contract. This reads h6's cell on them.
        The cell carries NO trail, so the honest-bound premium is 0.000000 by
        construction and the OOS read needs no correction.

No sealed replay. No VPS. No broker script. Nothing committed.
"""
from __future__ import annotations

import gzip, json, os, sys, time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_lib                      # noqa: E402
import h6_lib as H                # noqa: E402
import h6_16_trailbound as TB     # noqa: E402

TICK = json.load(open(f"{D}/L10X_TICK_SPREAD_V1.json"))
NY = ZoneInfo("America/New_York")
BERLIN = ZoneInfo("Europe/Berlin")
LONDON = ZoneInfo("Europe/London")


def broker_hour_true(dt_iso, plus_min=0):
    t = datetime.fromisoformat(dt_iso)
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    t = t + timedelta(minutes=plus_min)
    return (t.astimezone(NY) + timedelta(hours=7)).hour


def in_cash_session(sym, dt_iso):
    """h2's ex-ante rule: each instrument only while its own exchange's cash market
    is open, written in the exchange's OWN local wall clock (DST-correct)."""
    t = datetime.fromisoformat(dt_iso)
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    if sym == "GER40":
        lt = t.astimezone(BERLIN); mins = lt.hour * 60 + lt.minute
        return 9 * 60 <= mins < 17 * 60 + 30
    if sym == "UK100":
        lt = t.astimezone(LONDON); mins = lt.hour * 60 + lt.minute
        return 8 * 60 <= mins < 16 * 60 + 30
    if sym in ("NAS100", "SPX500", "US30_cash"):
        lt = t.astimezone(NY); mins = lt.hour * 60 + lt.minute
        return 9 * 60 + 30 <= mins < 16 * 60
    return False


def stats(g, c, days, months=None):
    n = len(g)
    if n < 2:
        return {"n": n}
    net = g - c
    o = {"n": int(n), "gross": float(g.mean()), "cost": float(c.mean()),
         "net": float(net.mean()),
         "t_net": float(net.mean() / (net.std(ddof=1) / np.sqrt(n))),
         "t_gross": float(g.mean() / (g.std(ddof=1) / np.sqrt(n))),
         "ratio_r": float(g.mean() / c.mean()) if c.mean() else None,
         "total_net_R": float(net.sum())}
    ud = np.unique(days)
    dm = np.array([net[days == d].mean() for d in ud])
    o["n_days"] = int(len(ud))
    o["days_pos"] = int((dm > 0).sum())
    # day-clustered t (blocks = trading days)
    o["t_net_dayclu"] = float(dm.mean() / (dm.std(ddof=1) / np.sqrt(len(ud)))) if len(ud) > 2 else None
    if months is not None:
        mm = {}
        for m in np.unique(months):
            s = months == m
            mm[str(m)] = {"n": int(s.sum()), "net": float(net[s].mean()),
                          "ratio_r": float(g[s].mean() / c[s].mean()) if c[s].mean() else None}
        o["by_month"] = mm
        o["months_pos"] = int(sum(1 for v in mm.values() if v["net"] > 0))
        o["months_total"] = len(mm)
    return o


def rnd(o, p=6):
    if isinstance(o, dict):
        return {k: rnd(v, p) for k, v in o.items()}
    if isinstance(o, list):
        return [rnd(v, p) for v in o]
    if isinstance(o, float):
        return round(o, p)
    return o


# ===================================================================== PART A
def part_a():
    P, M = H.load()
    cost_hour = np.load(f"{D}/h6_cost_hour.npy")
    bh = np.load(f"{D}/h6_broker_hour.npy")
    bpsfac = M["bpsfac"]
    cost_hour_bps = cost_hour * bpsfac
    rows = [json.loads(x) for x in gzip.open(f"{D}/h6_ATMKT_META.jsonl.gz", "rt") if x.strip()]
    cash = np.array([in_cash_session(r["symbol"], r["dt"]) for r in rows])
    utc_hour = M["hour"]

    SW = dict(k=5, target=None, stop=-1.0, trail=0.25, maxbars=None)
    r_opt, _rs, trd_o = TB.walk_trail_mode(P, same_bar=False, **SW)
    r_hon, _rs2, trd_h = TB.walk_trail_mode(P, same_bar=True, **SW)
    base = trd_o & trd_h & np.isfinite(cost_hour)

    # the one no-trail form, for contrast (premium 0 by construction)
    NT = dict(k=3, target=None, stop=-1.0, trail=None, maxbars=None)
    r_nt, _r3, trd_nt = TB.walk_trail_mode(P, same_bar=False, **NT)
    r_nt2, _r4, _t4 = TB.walk_trail_mode(P, same_bar=True, **NT)
    base_nt = trd_nt & np.isfinite(cost_hour)

    S, F, SE = M["symbol"], M["family"], M["session"]
    CELLS = [
        ("BOOK — whole live-expressible book", "swarm", base),
        ("h1 · cost<=0.50bps AND broker hour 08-20", "h1",
         base & (cost_hour_bps <= 0.50 + 1e-12) & (bh >= 8) & (bh <= 20)),
        ("h1 · NAS100 AND cost<=0.50bps", "h1",
         base & (S == "NAS100") & (cost_hour_bps <= 0.50 + 1e-12)),
        ("h1 · GER40+NAS100 AND cost<=0.50bps", "h1",
         base & np.isin(S, ["GER40", "NAS100"]) & (cost_hour_bps <= 0.50 + 1e-12)),
        ("h1/h2/h5 · GER40 | london session", "h1,h2,h5", base & (S == "GER40") & (SE == "london")),
        ("h2 · GER40+NAS100 inside own cash session", "h2",
         base & np.isin(S, ["GER40", "NAS100"]) & cash),
        ("h2 · GER40 inside own cash session", "h2", base & (S == "GER40") & cash),
        ("h2 · NAS100 inside own cash session", "h2", base & (S == "NAS100") & cash),
        ("h3/h1/h2 · regime_transition_break (family)", "h3",
         base & (F == "regime_transition_break")),
        ("h5 · GER40 | UTC hour 14", "h5", base & (S == "GER40") & (utc_hour == 14)),
        ("h5 · GER40 | UTC hour 08", "h5", base & (S == "GER40") & (utc_hour == 8)),
        ("h5 · US30_cash | cost decile 0", "h5", base & (S == "US30_cash")
         & (cost_hour_bps <= np.nanquantile(cost_hour_bps[base], 0.10))),
        ("h1 · GER40 | broker hours 16-19", "h1",
         base & (S == "GER40") & (bh >= 16) & (bh <= 19)),
        ("h1 · US30_cash | london session", "h1", base & (S == "US30_cash") & (SE == "london")),
    ]
    out = {}
    print(f"{'cell':<46}{'n':>6}{'gr_opt':>10}{'gr_HON':>10}{'prem':>9}"
          f"{'cost':>9}{'net_opt':>10}{'net_HON':>10}{'r_opt':>8}{'r_HON':>8}")
    for lab, owner, sel in CELLS:
        if sel.sum() < 30:
            continue
        g_o, g_h, c = r_opt[sel], r_hon[sel], cost_hour[sel]
        a = stats(g_o, c, M["day"][sel], M["month"][sel])
        b = stats(g_h, c, M["day"][sel], M["month"][sel])
        out[lab] = {"lane": owner, "optimistic": rnd(a), "honest_trail_bound": rnd(b),
                    "trail_bar_premium_gross": round(float(g_o.mean() - g_h.mean()), 6),
                    "survives_honest_bound": bool(b["net"] > 0)}
        print(f"{lab:<46}{a['n']:>6}{a['gross']:>+10.5f}{b['gross']:>+10.5f}"
              f"{g_o.mean()-g_h.mean():>+9.5f}{a['cost']:>9.5f}{a['net']:>+10.5f}"
              f"{b['net']:>+10.5f}{(a['ratio_r'] or 0):>8.3f}{(b['ratio_r'] or 0):>8.3f}")

    # the no-trail cell — premium is zero by construction
    for lab, sel in (("h6 · NO-TRAIL k=3 | hour cost<=0.60bps", base_nt
                      & (cost_hour_bps <= 0.60 + 1e-12)),
                     ("h6 · NO-TRAIL k=3 | ungated", base_nt)):
        g_o, g_h, c = r_nt[sel], r_nt2[sel], cost_hour[sel]
        a = stats(g_o, c, M["day"][sel], M["month"][sel])
        b = stats(g_h, c, M["day"][sel], M["month"][sel])
        out[lab] = {"lane": "h6", "optimistic": rnd(a), "honest_trail_bound": rnd(b),
                    "trail_bar_premium_gross": round(float(g_o.mean() - g_h.mean()), 6),
                    "survives_honest_bound": bool(b["net"] > 0),
                    "symbols": sorted(set(S[sel].tolist()))}
        print(f"{lab:<46}{a['n']:>6}{a['gross']:>+10.5f}{b['gross']:>+10.5f}"
              f"{g_o.mean()-g_h.mean():>+9.5f}{a['cost']:>9.5f}{a['net']:>+10.5f}"
              f"{b['net']:>+10.5f}{(a['ratio_r'] or 0):>8.3f}{(b['ratio_r'] or 0):>8.3f}")
    return out


# ===================================================================== PART B
MONTHS = [("2026-01", "e_JAN_ATMKT_V1.jsonl.gz"), ("2026-02", "e_FEB_ATMKT_V1.jsonl.gz"),
          ("2026-03", "e_MAR_ATMKT_V1.jsonl.gz"), ("2026-04", "e_APR_ATMKT_V1.jsonl.gz"),
          ("2026-05", "e_MAY_ATMKT_V1.jsonl.gz")]


def load_month(mk, path, col="K3_STOPONLY"):
    g, c, cb, sym, day, mon, fam, ses, side, hr = [], [], [], [], [], [], [], [], [], []
    nmiss = 0
    for x in gzip.open(f"{D}/{path}", "rt"):
        if not x.strip():
            continue
        r = json.loads(x)
        v = r.get(col)
        if v is None or r.get("real_spread_r") is None:
            nmiss += 1
            continue
        tk = TICK.get("ftmo:" + e_lib.TMAP.get(r["symbol"], r["symbol"]))
        if not tk:
            nmiss += 1
            continue
        b_h = broker_hour_true(r["dt"])
        sp_bps = (tk.get("spread_bps_median_by_broker_hour") or {}).get(str(b_h))
        if sp_bps is None:
            sp_bps = tk["spread_bps_median"]
        sp_r = sp_bps * r["entry_price"] / 1e4 / r["risk_distance"]
        ch = sp_r + r["real_comm_r"] + r["real_slip_r"]
        bf = r["risk_distance"] / r["entry_price"] * 1e4
        g.append(v); c.append(ch); cb.append(ch * bf)
        sym.append(r["symbol"]); day.append(r["day"]); mon.append(mk)
        fam.append(r.get("family") or ""); ses.append(r.get("session") or "")
        side.append(r.get("side") or ""); hr.append(b_h)
    return dict(g=np.array(g), c=np.array(c), cb=np.array(cb), sym=np.array(sym),
                day=np.array(day), mon=np.array(mon), fam=np.array(fam),
                ses=np.array(ses), side=np.array(side), bh=np.array(hr), nmiss=nmiss)


def part_b():
    t0 = time.time()
    packs = {}
    for mk, p in MONTHS:
        packs[mk] = load_month(mk, p)
        print(f"  {mk}: n={len(packs[mk]['g']):,} (dropped {packs[mk]['nmiss']})", flush=True)
    A = {k: np.concatenate([packs[m][k] for m, _ in MONTHS]) for k in
         ("g", "c", "cb", "sym", "day", "mon", "fam", "ses", "side", "bh")}
    HUNT = np.isin(A["mon"], ["2026-01", "2026-02", "2026-03"])
    OOS = np.isin(A["mon"], ["2026-04", "2026-05"])
    out = {"n_total": int(len(A["g"])),
           "n_hunt": int(HUNT.sum()), "n_oos": int(OOS.sum()),
           "per_month_n": {m: int((A["mon"] == m).sum()) for m, _ in MONTHS}}

    def sc(mask, label=None):
        return stats(A["g"][mask], A["c"][mask], A["day"][mask], A["mon"][mask])

    GATE = A["cb"] <= 0.60 + 1e-12
    out["headline_cell_k3_STOPONLY_hourcost_le_060"] = {
        "HUNT_jan_feb_mar": rnd(sc(HUNT & GATE)),
        "OOS_apr_may": rnd(sc(OOS & GATE)),
        "ALL_FIVE_MONTHS": rnd(sc(GATE)),
        "symbols_hunt": sorted(set(A["sym"][HUNT & GATE].tolist())),
        "symbols_oos": sorted(set(A["sym"][OOS & GATE].tolist()))}
    out["book_k3_STOPONLY_ungated"] = {
        "HUNT_jan_feb_mar": rnd(sc(HUNT)), "OOS_apr_may": rnd(sc(OOS)),
        "ALL_FIVE_MONTHS": rnd(sc(np.ones(len(A["g"]), bool)))}

    # gate ladder, out of sample
    lad = []
    for cap in (None, 2.0, 1.5, 1.0, 0.8, 0.7, 0.6, 0.5, 0.45, 0.4):
        m = np.ones(len(A["g"]), bool) if cap is None else (A["cb"] <= cap + 1e-12)
        if (m & OOS).sum() < 50:
            continue
        lad.append({"cap_bps": cap, "hunt": rnd(sc(m & HUNT)), "oos": rnd(sc(m & OOS)),
                    "all5": rnd(sc(m))})
    out["gate_ladder"] = lad
    print("\n  cap    HUNT n   HUNT net   HUNT r |    OOS n    OOS net    OOS r |  ALL5 net  ALL5 r")
    for L in lad:
        print(f"  {str(L['cap_bps']):>4} {L['hunt']['n']:>8,} {L['hunt']['net']:>+10.5f}"
              f" {(L['hunt']['ratio_r'] or 0):>7.3f} | {L['oos']['n']:>8,}"
              f" {L['oos']['net']:>+10.5f} {(L['oos']['ratio_r'] or 0):>7.3f} |"
              f" {L['all5']['net']:>+9.5f} {(L['all5']['ratio_r'] or 0):>6.3f}")

    # per instrument inside the gate
    per = {}
    for s in sorted(set(A["sym"][GATE].tolist())):
        m = GATE & (A["sym"] == s)
        per[s] = {"hunt": rnd(sc(m & HUNT)), "oos": rnd(sc(m & OOS)), "all5": rnd(sc(m))}
    out["per_symbol_in_gate"] = per
    print("\n  symbol        HUNT n  HUNT net   HUNT r |  OOS n   OOS net    OOS r | ALL5 n  ALL5 net  ALL5 r")
    for s, v in sorted(per.items(), key=lambda kv: -(kv[1]["all5"].get("net") or -9)):
        if v["all5"].get("n", 0) < 50:
            continue
        print(f"  {s:<12} {v['hunt'].get('n',0):>7,} {v['hunt'].get('net',0):>+9.5f}"
              f" {(v['hunt'].get('ratio_r') or 0):>7.3f} | {v['oos'].get('n',0):>6,}"
              f" {v['oos'].get('net',0):>+9.5f} {(v['oos'].get('ratio_r') or 0):>7.3f} |"
              f" {v['all5'].get('n',0):>6,} {v['all5'].get('net',0):>+8.5f}"
              f" {(v['all5'].get('ratio_r') or 0):>6.3f}")

    # delay ladder on the gated cell, five months (is k=3 a spike?)
    dl = {}
    for k in (0, 1, 2, 3, 5, 10, 15, 20, 30):
        pk = {}
        for mk, p in MONTHS:
            pk[mk] = load_month(mk, p, col=f"K{k}_STOPONLY")
        B = {kk: np.concatenate([pk[m][kk] for m, _ in MONTHS]) for kk in
             ("g", "c", "cb", "mon", "day")}
        gm = B["cb"] <= 0.60 + 1e-12
        hm = gm & np.isin(B["mon"], ["2026-01", "2026-02", "2026-03"])
        om = gm & np.isin(B["mon"], ["2026-04", "2026-05"])
        dl[str(k)] = {"hunt": rnd(stats(B["g"][hm], B["c"][hm], B["day"][hm], B["mon"][hm])),
                      "oos": rnd(stats(B["g"][om], B["c"][om], B["day"][om], B["mon"][om])),
                      "all5": rnd(stats(B["g"][gm], B["c"][gm], B["day"][gm], B["mon"][gm]))}
        print(f"  k={k:<3} HUNT net {dl[str(k)]['hunt']['net']:+.5f} r "
              f"{(dl[str(k)]['hunt']['ratio_r'] or 0):.3f} | OOS net "
              f"{dl[str(k)]['oos']['net']:+.5f} r {(dl[str(k)]['oos']['ratio_r'] or 0):.3f}"
              f" | ALL5 net {dl[str(k)]['all5']['net']:+.5f}", flush=True)
    out["delay_ladder_in_gate"] = dl

    # contract ladder on the gated cell (is STOPONLY special?)
    cl = {}
    for cname in ("STOPONLY", "INC", "TRAIL025", "TS90S1", "TS60S1", "T3S1"):
        pk = {m: load_month(m, p, col=f"K3_{cname}") for m, p in MONTHS}
        B = {kk: np.concatenate([pk[m][kk] for m, _ in MONTHS]) for kk in
             ("g", "c", "cb", "mon", "day")}
        gm = B["cb"] <= 0.60 + 1e-12
        hm = gm & np.isin(B["mon"], ["2026-01", "2026-02", "2026-03"])
        om = gm & np.isin(B["mon"], ["2026-04", "2026-05"])
        cl[cname] = {"hunt": rnd(stats(B["g"][hm], B["c"][hm], B["day"][hm], B["mon"][hm])),
                     "oos": rnd(stats(B["g"][om], B["c"][om], B["day"][om], B["mon"][om])),
                     "all5": rnd(stats(B["g"][gm], B["c"][gm], B["day"][gm], B["mon"][gm]))}
        print(f"  {cname:<10} HUNT {cl[cname]['hunt']['net']:+.5f} | OOS "
              f"{cl[cname]['oos']['net']:+.5f} | ALL5 {cl[cname]['all5']['net']:+.5f}"
              f" (r {(cl[cname]['all5']['ratio_r'] or 0):.3f})", flush=True)
    out["contract_ladder_in_gate_k3"] = cl

    # h5's five-month leads, on the NO-TRAIL contract this time
    lead = {}
    for lab, m in (("GER40|utc14", (A["sym"] == "GER40") & (np.array(
                        [int(d) for d in [0] * 0]) if False else np.zeros(len(A["g"]), bool))),):
        pass
    out["seconds"] = round(time.time() - t0, 1)
    return out


def main():
    t0 = time.time()
    print("=" * 118)
    print("PART A — every lane's headline cell under the ratified HONEST-TRAIL bound, "
          "at hour-true broker cost (Jan-Mar)")
    print("=" * 118)
    a = part_a()
    print("\n" + "=" * 118)
    print("PART B — h6's NO-TRAIL paying cell read on APRIL + MAY 2026 "
          "(never scored on a no-trail contract by any lane)")
    print("=" * 118)
    b = part_b()
    json.dump({"part_a_honest_trail_bound": a, "part_b_out_of_sample": b,
               "seconds": round(time.time() - t0, 1)},
              open(f"{D}/B2_VERIFY_V1.json", "w"), indent=1)
    print(f"\nwrote B2_VERIFY_V1.json  ({round(time.time()-t0,1)}s)")


if __name__ == "__main__":
    main()
