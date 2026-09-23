"""h3-07 -- the cells. Where is edge/toll already above 1?

Three families of arm, all scored on the same 43,755 live-expressible opportunities:

A. NO-RETRACE MARKET ENTRY -- fully implementable with the engine that exists today.
   At minute k, ask one question that is knowable at minute k: has price traded back
   THROUGH the decision price at any time since the decision? If it has not, buy at market
   at the close of minute k. If it has, stand down. Toll is the FULL market toll -- no
   passive fill is assumed anywhere in this family.

B. PASSIVE NO-RETRACE -- the same filter, but the entry is a resting limit at the decision
   price, so the entry half-spread is not paid. Requires an order type l10-X3 measured the
   live engine has never placed. Reported at BOTH tolls so the two are never confused.

C. CELLS -- arm A crossed with instrument, NY hour and session, so the cross-section can be
   read directly. Every cell carries n, per-month split and both tolls.

No multiplicity correction is applied and none is claimed. Cells are reported with their n.
"""
import gzip
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib as H  # noqa: E402

C = "TRAIL025"
KS = H.KS
CONDS = [0, 1, 2, 3, 5, 10, 15, 20, 30]

pas = []
for mm in ("202601", "202602", "202603"):
    for line in gzip.open(os.path.join(D, f"H3_PASSIVE_ROWS_{mm}.jsonl.gz"), "rt"):
        if line.strip():
            pas.append(json.loads(line))
atm = {(r["cid"], r["dt"]): r for r in H.load_atmkt()}
H.add_hour_cost(list(atm.values()))
rows = []
for r in pas:
    a = atm.get((r["cid"], r["dt"]))
    if a is None:
        continue
    m = dict(a)
    m["j0"] = r.get("u000_j0")
    m["j1"] = r.get("u000_j1")
    for k in ("u000_j0_" + C, "u005_j0_" + C, "u010_j0_" + C, "u025_j0_" + C, "u050_j0_" + C):
        m[k] = r.get(k)
    m["u000_j0_bar"] = r.get("u000_j0")
    rows.append(m)
N = len(rows)

TOLL_MKT = lambda r: r["cost_true"]                                             # noqa: E731
TOLL_MKT_H = lambda r: r["cost_true_hour"]                                      # noqa: E731
TOLL_PAS = lambda r: 0.5 * r["real_spread_r"] + r["real_comm_r"]                # noqa: E731

out = {"lane": "h3", "step": "cells", "n_opportunities": N, "contract": C,
       "conds_minutes": CONDS, "delays_minutes": KS}


def score(sub, valkey, tollf, ntot, label, extra=None):
    g, t, n, keep = [], [], [], []
    for r in sub:
        v = r.get(valkey)
        if v is None:
            continue
        gb = v * r["rdp"] * 1e4
        tb = tollf(r) * r["rdp"] * 1e4
        g.append(gb); t.append(tb); n.append(gb - tb); keep.append(r)
    if len(g) < 10:
        return None
    d = {"label": label, "n": len(g), "keep_rate": len(g) / ntot,
         "edge_bps": H.mean(g), "toll_bps": H.mean(t), "net_bps": H.mean(n),
         "edge_over_toll": H.mean(g) / H.mean(t) if H.mean(t) else None,
         "gross_r": H.mean([r[valkey] for r in keep]),
         "net_r": H.mean([r[valkey] - tollf(r) for r in keep]),
         "net_bps_per_opportunity": H.mean(n) * len(g) / ntot,
         "net_r_per_opportunity": H.mean([r[valkey] - tollf(r) for r in keep]) * len(g) / ntot,
         "t_gross_trade": H.tstat(g), "t_net_trade": H.tstat(n)}
    dd = {}
    for m in sorted(H.MONTHS):
        s2 = [r for r in keep if r["month"] == m]
        if len(s2) >= 5:
            gg = [r[valkey] * r["rdp"] * 1e4 for r in s2]
            tt = [tollf(r) * r["rdp"] * 1e4 for r in s2]
            dd[m] = {"n": len(s2), "edge_bps": H.mean(gg), "toll_bps": H.mean(tt),
                     "net_bps": H.mean(gg) - H.mean(tt),
                     "edge_over_toll": H.mean(gg) / H.mean(tt) if H.mean(tt) else None}
    d["by_month"] = dd
    d["months_edge_over_toll_ge_1"] = sum(1 for v in dd.values()
                                          if v["edge_over_toll"] and v["edge_over_toll"] >= 1)
    d["months_measured"] = len(dd)
    dser = {}
    for r, v in zip(keep, n):
        dser.setdefault(r["day"], []).append(v)
    ds = [sum(x) / len(x) for x in dser.values()]
    d["days_traded"] = len(ds)
    d["days_net_positive"] = sum(1 for x in ds if x > 0)
    d["t_net_daily"] = H.tstat(ds)
    if extra:
        d.update(extra)
    return d


# ---------------------------------------------------- A. no-retrace market entry grid
A = []
for k in KS:
    for c in CONDS:
        if c > k:
            continue                     # the test must be answerable by the entry minute
        sub = [r for r in rows if r["j0"] is None or r["j0"] >= c]
        d = score(sub, f"K{k}_{C}", TOLL_MKT, N,
                  f"NO-RETRACE(>={c} min) + market entry at minute {k}",
                  extra={"delay_min": k, "cond_min": c, "family": "A_market_no_retrace"})
        if d:
            A.append(d)
out["A_no_retrace_market"] = A
out["A_best_by_ratio"] = sorted([d for d in A if d["n"] >= 500],
                                key=lambda d: -d["edge_over_toll"])[:15]
out["A_best_by_net_per_opportunity"] = sorted(A, key=lambda d: -d["net_bps_per_opportunity"])[:15]

# unconditional baselines for the same delays
out["A_baseline_unconditional"] = [
    score(rows, f"K{k}_{C}", TOLL_MKT, N, f"unconditional market entry at minute {k}",
          extra={"delay_min": k, "cond_min": None}) for k in KS]

# ---------------------------------------------------- B. passive no-retrace, both tolls
B = []
for c in CONDS:
    sub = [r for r in rows if r["j0"] is not None and r["j0"] >= c]
    for tk, tf in (("passive_toll", TOLL_PAS), ("market_toll", TOLL_MKT)):
        d = score(sub, "u000_j0_" + C, tf, N,
                  f"PASSIVE limit at decision price, abstain if touched before min {c} [{tk}]",
                  extra={"cond_min": c, "toll_basis": tk, "family": "B_passive_no_retrace"})
        if d:
            B.append(d)
out["B_passive_no_retrace"] = B

# ---------------------------------------------------- C. cells
def cells(axis, keyf, family, valkey, tollf, cond, delay):
    acc = {}
    base = [r for r in rows if r["j0"] is None or r["j0"] >= cond]
    for r in base:
        acc.setdefault(keyf(r), []).append(r)
    res = []
    for k, rs in acc.items():
        d = score(rs, valkey, tollf, len([r for r in rows if keyf(r) == k]),
                  f"{axis}={k}", extra={"axis": axis, "cell": k, "family": family,
                                        "cond_min": cond, "delay_min": delay})
        if d:
            res.append(d)
    res.sort(key=lambda d: -(d["edge_over_toll"] or -9))
    return res


BEST_K, BEST_C = 20, 10
out["best_arm_used_for_cells"] = {"delay_min": BEST_K, "cond_min": BEST_C}
for axis, kf in (("symbol", lambda r: r["symbol"]),
                 ("ny_hour", lambda r: r["ny_hour"]),
                 ("session", lambda r: r.get("session") or "none"),
                 ("family", lambda r: r.get("family") or "none"),
                 ("side", lambda r: r["side"])):
    out[f"C_cells_{axis}_unconditional"] = cells(axis, kf, "C_cells", f"K5_{C}", TOLL_MKT, 0, 5)
    out[f"C_cells_{axis}_noretrace"] = cells(axis, kf, "C_cells", f"K{BEST_K}_{C}",
                                             TOLL_MKT, BEST_C, BEST_K)

# ---- symbol x no-retrace, the joint cell that matters most
joint = []
for s in sorted({r["symbol"] for r in rows}):
    for c in (0, 5, 10, 15):
        for k in (5, 10, 20, 30):
            if c > k:
                continue
            sub = [r for r in rows if r["symbol"] == s and (r["j0"] is None or r["j0"] >= c)]
            tot = len([r for r in rows if r["symbol"] == s])
            d = score(sub, f"K{k}_{C}", TOLL_MKT, tot, f"{s} noretrace>={c} delay={k}",
                      extra={"symbol": s, "cond_min": c, "delay_min": k})
            if d:
                joint.append(d)
out["C_symbol_x_noretrace"] = joint
out["C_symbol_x_noretrace_best"] = sorted([d for d in joint if d["n"] >= 200],
                                          key=lambda d: -d["edge_over_toll"])[:25]

p = H.dump(out, "H3_CELLS_V1.json")
print("A -- no-retrace MARKET entry, top 15 by edge:toll (n>=500), FULL market toll")
print("%-46s %6s %6s %8s %8s %8s %7s %10s %4s" %
      ("arm", "n", "keep", "edge", "toll", "net", "e/t", "net/opp", "m>=1"))
for d in out["A_best_by_ratio"]:
    print("%-46s %6d %6.3f %8.4f %8.4f %8.4f %7.3f %10.5f %2d/%d" %
          (d["label"][:46], d["n"], d["keep_rate"], d["edge_bps"], d["toll_bps"],
           d["net_bps"], d["edge_over_toll"], d["net_bps_per_opportunity"],
           d["months_edge_over_toll_ge_1"], d["months_measured"]))
print("\nA -- top 15 by net bps per OPPORTUNITY")
for d in out["A_best_by_net_per_opportunity"]:
    print("%-46s %6d %6.3f %8.4f %8.4f %8.4f %7.3f %10.5f" %
          (d["label"][:46], d["n"], d["keep_rate"], d["edge_bps"], d["toll_bps"],
           d["net_bps"], d["edge_over_toll"], d["net_bps_per_opportunity"]))
print("\nB -- passive no-retrace at both tolls")
for d in B:
    print("%-72s n=%6d e/t=%6.3f net=%8.4f net/opp=%9.5f" %
          (d["label"][:72], d["n"], d["edge_over_toll"], d["net_bps"],
           d["net_bps_per_opportunity"]))
print("->", p)
