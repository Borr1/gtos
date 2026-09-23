"""b2b — the one object that survived both cross-lane checks, measured to the floor.

GER40, entered at market 3 minutes after the decision, plain -1R stop, no target,
NO trailing stop, closed at the 2-hour wall, restricted to instrument-hours whose
hour-true broker round trip is <= 0.60 bps. Five months, Jan-May 2026.

Reports: month by month, hour by hour, day concentration, drop-best-days, bootstrap,
a doubled toll, both sides, and the same cell on the four other cheap instruments.
"""
from __future__ import annotations

import gzip, json, os, sys, time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_lib  # noqa: E402
import b2_verify as V  # noqa: E402


def boot(g, c, days, nboot=4000, seed=20260806):
    rng = np.random.default_rng(seed)
    net = g - c
    ud = np.unique(days)
    idx = {d: np.where(days == d)[0] for d in ud}
    sums = np.array([net[idx[d]].sum() for d in ud])
    cnts = np.array([len(idx[d]) for d in ud])
    nd = len(ud)
    o = np.empty(nboot)
    for b in range(nboot):
        p = rng.integers(0, nd, nd)
        o[b] = sums[p].sum() / cnts[p].sum()
    return {"observed": float(net.mean()), "ci_lo": float(np.quantile(o, 0.025)),
            "ci_hi": float(np.quantile(o, 0.975)), "p_le_0": float((o <= 0).mean()),
            "n_days": int(nd)}


def main():
    t0 = time.time()
    packs = {m: V.load_month(m, p, col="K3_STOPONLY") for m, p in V.MONTHS}
    A = {k: np.concatenate([packs[m][k] for m, _ in V.MONTHS]) for k in
         ("g", "c", "cb", "sym", "day", "mon", "fam", "ses", "side", "bh")}
    out = {}
    GATE = A["cb"] <= 0.60 + 1e-12
    HUNT = np.isin(A["mon"], ["2026-01", "2026-02", "2026-03"])
    OOS = np.isin(A["mon"], ["2026-04", "2026-05"])

    def S(m):
        return V.stats(A["g"][m], A["c"][m], A["day"][m], A["mon"][m])

    G = GATE & (A["sym"] == "GER40")
    out["GER40_cell"] = {"all5": V.rnd(S(G)), "hunt": V.rnd(S(G & HUNT)),
                         "oos": V.rnd(S(G & OOS)),
                         "bootstrap_all5": V.rnd(boot(A["g"][G], A["c"][G], A["day"][G])),
                         "bootstrap_oos": V.rnd(boot(A["g"][G & OOS], A["c"][G & OOS],
                                                     A["day"][G & OOS]))}
    print("GER40 cell (k=3, plain stop, no trail, 2h wall, hour cost<=0.60bps)")
    for lab in ("all5", "hunt", "oos"):
        s = out["GER40_cell"][lab]
        print(f"  {lab:<5} n {s['n']:>5}  net {s['net']:+.5f}  ratio {s['ratio_r']:.3f}"
              f"  t_day {(s.get('t_net_dayclu') or 0):+.2f}  days+ {s['days_pos']}/{s['n_days']}"
              f"  months+ {s['months_pos']}/{s['months_total']}")
    for lab in ("bootstrap_all5", "bootstrap_oos"):
        b = out["GER40_cell"][lab]
        print(f"  {lab:<16} obs {b['observed']:+.5f} CI [{b['ci_lo']:+.5f},{b['ci_hi']:+.5f}]"
              f" P(<=0) {b['p_le_0']:.4f}")

    # month by month
    mm = {}
    for m, _ in V.MONTHS:
        s = S(G & (A["mon"] == m))
        mm[m] = V.rnd(s)
        print(f"  {m}  n {s.get('n',0):>4}  net {s.get('net',0):+.5f} "
              f" ratio {(s.get('ratio_r') or 0):>6.3f}  days+ {s.get('days_pos',0)}/{s.get('n_days',0)}")
    out["GER40_by_month"] = mm

    # which hours the gate admits, and their economics
    hb = {}
    for h in sorted(set(A["bh"][G].tolist())):
        s = S(G & (A["bh"] == h))
        if s.get("n", 0) >= 25:
            hb[str(h)] = V.rnd(s)
    out["GER40_by_broker_hour"] = hb
    print("\n  broker hr  n   net       ratio   (broker hour = UTC+2 Jan-early Mar, UTC+3 after)")
    for h, s in sorted(hb.items(), key=lambda kv: int(kv[0])):
        print(f"   {h:>4}   {s['n']:>5}  {s['net']:+.5f}  {(s['ratio_r'] or 0):>6.3f}")

    # concentration / robustness on the five-month cell
    net = A["g"][G] - A["c"][G]
    days = A["day"][G]
    ud = np.unique(days)
    dsum = np.array([net[days == d].sum() for d in ud])
    order = np.argsort(-dsum)
    tot = dsum.sum()
    rob = {"total_net_R": float(tot),
           "best_day_share": float(dsum[order[0]] / tot) if tot else None,
           "best3_share": float(dsum[order[:3]].sum() / tot) if tot else None}
    for k in (1, 3, 5):
        keep = np.ones(len(ud), bool); keep[order[:k]] = False
        kd = set(ud[keep].tolist())
        m2 = np.array([d in kd for d in days])
        rob[f"drop_best_{k}_days_net"] = float(net[m2].mean())
    rob["toll_x2_net"] = float((A["g"][G] - 2 * A["c"][G]).mean())
    rob["toll_x3_net"] = float((A["g"][G] - 3 * A["c"][G]).mean())
    rob["trimmed_10pct_net"] = float(
        np.mean(np.sort(net)[int(0.05 * len(net)):len(net) - int(0.05 * len(net))]))
    for sd in ("LONG", "SHORT"):
        s = S(G & (A["side"] == sd))
        rob[f"side_{sd}"] = V.rnd(s)
    out["GER40_robustness"] = V.rnd(rob)
    print(f"\n  total {rob['total_net_R']:+.1f} R | best day {rob['best_day_share']:.1%}"
          f" | best3 {rob['best3_share']:.1%} | drop best 3 {rob['drop_best_3_days_net']:+.5f}"
          f" | toll x2 {rob['toll_x2_net']:+.5f} | toll x3 {rob['toll_x3_net']:+.5f}"
          f" | 10% trim {rob['trimmed_10pct_net']:+.5f}")
    print(f"  LONG n {rob['side_LONG']['n']} net {rob['side_LONG']['net']:+.5f} | "
          f"SHORT n {rob['side_SHORT']['n']} net {rob['side_SHORT']['net']:+.5f}")

    # every instrument the gate ever admits, five months
    per = {}
    for s in sorted(set(A["sym"][GATE].tolist())):
        m = GATE & (A["sym"] == s)
        if m.sum() >= 50:
            per[s] = {"all5": V.rnd(S(m)), "hunt": V.rnd(S(m & HUNT)), "oos": V.rnd(S(m & OOS))}
    out["per_symbol_five_months"] = per

    # GER40 with NO cost gate at all, five months (is the gate doing the work?)
    GA = A["sym"] == "GER40"
    out["GER40_no_cost_gate"] = {"all5": V.rnd(S(GA)), "hunt": V.rnd(S(GA & HUNT)),
                                 "oos": V.rnd(S(GA & OOS))}
    s = out["GER40_no_cost_gate"]
    print(f"\n  GER40 ALL hours, no gate: all5 n {s['all5']['n']} net {s['all5']['net']:+.5f}"
          f" r {s['all5']['ratio_r']:.3f} | hunt {s['hunt']['net']:+.5f}"
          f" | oos {s['oos']['net']:+.5f}")

    # and the whole book at the 0.45 cap, which was the only OOS-positive rung
    C45 = A["cb"] <= 0.45 + 1e-12
    out["book_cap_045"] = {"all5": V.rnd(S(C45)), "hunt": V.rnd(S(C45 & HUNT)),
                           "oos": V.rnd(S(C45 & OOS)),
                           "symbols": sorted(set(A["sym"][C45].tolist())),
                           "bootstrap_oos": V.rnd(boot(A["g"][C45 & OOS], A["c"][C45 & OOS],
                                                       A["day"][C45 & OOS]))}
    s = out["book_cap_045"]
    print(f"  cap 0.45 bps: all5 n {s['all5']['n']} net {s['all5']['net']:+.5f}"
          f" r {s['all5']['ratio_r']:.3f} | oos n {s['oos']['n']} net {s['oos']['net']:+.5f}"
          f" r {s['oos']['ratio_r']:.3f} P(<=0) {s['bootstrap_oos']['p_le_0']:.3f}"
          f" | symbols {s['symbols']}")

    out["seconds"] = round(time.time() - t0, 1)
    json.dump(out, open(f"{D}/B2_GER40_V1.json", "w"), indent=1)
    print(f"\nwrote B2_GER40_V1.json ({out['seconds']}s)")


if __name__ == "__main__":
    main()
