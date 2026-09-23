"""h3-04 -- ENTRY MECHANICS priced in bps: at-market, delayed, resting limit, cancel.

THE TOLL IDENTITY THIS LANE USES, stated once.

    round-trip toll  =  quoted_spread          (crossed once: half in, half out)
                     +  commission             (charged both legs, already round-trip)
                     +  slippage               (market orders only)

So the entry half of the spread is 0.5 x quoted_spread of the toll and it is REMOVABLE in
principle by resting a limit instead of taking the market. Whether it is removable in
practice is a question about fills and adverse selection, and that is what this measures.

ARMS (all on the same 43,755 opportunities; the denominator never changes):
    MKT0   at-market at the decision instant                toll = spread + comm + slip
    MKT5   at-market at the close of minute 5 (headline)    toll = spread + comm + slip
    PAS(u, cancel)  limit resting u R better than the decision price, `cancel` = refuse a
                    fill that arrives before minute `cancel`;                toll = 0.5*spread + comm
    PAS_SLIP        same but keeping the slippage term, as a conservative arm.

For every arm the receipt carries BOTH per-trade and per-OPPORTUNITY figures. An arm that
does not fill books exactly zero, which is the honest accounting for abstention.
"""
import gzip
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib as H  # noqa: E402

U = [0.0, 0.02, 0.05, 0.10, 0.15, 0.25, 0.50]
CANCEL = [0, 1, 5]
WINDOWS = [1, 2, 5, 15, 60, 120]
C = "TRAIL025"


def load():
    rows = []
    for mm in ("202601", "202602", "202603"):
        for line in gzip.open(os.path.join(D, f"H3_PASSIVE_ROWS_{mm}.jsonl.gz"), "rt"):
            if line.strip():
                rows.append(json.loads(line))
    return rows


rows = load()
out = {"lane": "h3", "step": "entry_mechanics", "n_opportunities": len(rows),
       "contract": C, "u_ladder_R": U, "cancel_minutes": CANCEL, "windows_bars": WINDOWS}

# ---------------------------------------------------------------- 0. validation
atm = {H.key if False else (r["cid"], r["dt"]): r for r in H.load_atmkt(require_cost=False)}
dif0, dif5, nmatch = [], [], 0
for r in rows:
    a = atm.get((r["cid"], r["dt"]))
    if not a:
        continue
    nmatch += 1
    if a.get("K0_" + C) is not None and r.get("MKT0_" + C) is not None:
        dif0.append(abs(a["K0_" + C] - r["MKT0_" + C]))
    if a.get("K5_" + C) is not None and r.get("MKT5_" + C) is not None:
        dif5.append(abs(a["K5_" + C] - r["MKT5_" + C]))
out["validation_vs_e_build_atmkt"] = {
    "matched": nmatch, "n_K0": len(dif0), "max_abs_diff_K0": max(dif0) if dif0 else None,
    "exact_frac_K0": sum(1 for x in dif0 if x < 1e-9) / len(dif0) if dif0 else None,
    "n_K5": len(dif5), "max_abs_diff_K5": max(dif5) if dif5 else None,
    "exact_frac_K5": sum(1 for x in dif5 if x < 1e-9) / len(dif5) if dif5 else None}


# ---------------------------------------------------------------- scoring helper
def score(rows, getter, toll_fn, label, extra=None):
    """getter(row) -> gross R or None (no trade). toll_fn(row) -> toll R."""
    g, t, n, keep = [], [], [], []
    for r in rows:
        v = getter(r)
        if v is None:
            continue
        gb = v * r["rdp"] * 1e4
        tb = toll_fn(r) * r["rdp"] * 1e4
        g.append(gb); t.append(tb); n.append(gb - tb); keep.append(r)
    if not g:
        return {"label": label, "n": 0, "fill_rate": 0.0}
    dm = {}
    for r, v in zip(keep, n):
        dm.setdefault(r["day"], []).append(v)
    # per-opportunity daily series: non-fills contribute 0 on their own day
    opp = {}
    for r in rows:
        opp.setdefault(r["day"], []).append(0.0)
    idx = {d: 0 for d in opp}
    for r, v in zip(keep, n):
        opp[r["day"]].append(v)
    dser = [sum(x) / len(x) for x in opp.values()]
    d = {"label": label, "n": len(g), "fill_rate": len(g) / len(rows),
         "edge_bps": H.mean(g), "toll_bps": H.mean(t), "net_bps": H.mean(n),
         "edge_over_toll": H.mean(g) / H.mean(t) if H.mean(t) else None,
         "gross_r": H.mean([getter(r) for r in keep]),
         "toll_r": H.mean([toll_fn(r) for r in keep]),
         "net_r": H.mean([getter(r) - toll_fn(r) for r in keep]),
         "net_bps_per_opportunity": H.mean(n) * len(g) / len(rows),
         "net_r_per_opportunity": H.mean([getter(r) - toll_fn(r) for r in keep]) * len(g) / len(rows),
         "t_net_trade": H.tstat(n),
         "t_net_daily_per_opportunity": H.tstat(dser),
         "days": len(dser),
         "days_positive_per_opportunity": sum(1 for x in dser if x > 0)}
    if extra:
        d.update(extra)
    return d


TOLL_MKT = lambda r: r["real_spread_r"] + r["real_comm_r"] + r["real_slip_r"]      # noqa: E731
TOLL_PAS = lambda r: 0.5 * r["real_spread_r"] + r["real_comm_r"]                   # noqa: E731
TOLL_PAS_SLIP = lambda r: 0.5 * r["real_spread_r"] + r["real_comm_r"] + r["real_slip_r"]  # noqa: E731

arms = []
arms.append(score(rows, lambda r: r.get("MKT0_" + C), TOLL_MKT, "MKT0 at-market, no delay"))
arms.append(score(rows, lambda r: r.get("MKT5_" + C), TOLL_MKT, "MKT5 at-market, +5 min (HEADLINE)"))

# ---- passive ladder x cancel x acceptance window
grid = []
for u in U:
    tag = f"u{int(round(u * 100)):03d}"
    for cc in CANCEL:
        jk = f"{tag}_j{cc}"
        rk = f"{tag}_j{cc}_{C}"
        for w in WINDOWS:
            def get(r, jk=jk, rk=rk, w=w):
                j = r.get(jk)
                if j is None or j >= w:
                    return None
                return r.get(rk)
            d = score(rows, get, TOLL_PAS,
                      f"PAS u={u} cancel<{cc}min window<={w}min",
                      extra={"u_R": u, "cancel_min": cc, "window_min": w})
            d["u_bps_mean"] = H.mean([u * r["rdp"] * 1e4 for r in rows])
            grid.append(d)
out["passive_grid"] = grid

# ---- the headline passive arms, unwindowed (limit works the full 2 h)
for u in U:
    tag = f"u{int(round(u * 100)):03d}"
    for cc in CANCEL:
        arms.append(score(rows, lambda r, k=f"{tag}_j{cc}_{C}": r.get(k), TOLL_PAS,
                          f"PAS u={u} cancel<{cc}min, works 2h",
                          extra={"u_R": u, "cancel_min": cc}))
arms.append(score(rows, lambda r: r.get("u000_j0_" + C), TOLL_PAS_SLIP,
                  "PAS u=0 cancel<0, KEEPING slippage (conservative)"))
out["arms"] = arms

# ---------------------------------------------------- adverse selection by fill bar
adv = {}
for r in rows:
    j = r.get("u000_j0")
    if j is None or r.get("u000_j0_" + C) is None:
        continue
    b = ("bar0_first_60s" if j == 0 else "bar1_2" if j <= 2 else
         "bar3_5" if j <= 5 else "bar6_15" if j <= 15 else "bar16_60" if j <= 60 else "bar61_120")
    adv.setdefault(b, []).append(r)
out["passive_u0_by_fill_bar"] = {
    k: {"n": len(v), "share": len(v) / len(rows),
        "gross_r": H.mean([x["u000_j0_" + C] for x in v]),
        "edge_bps": H.mean([x["u000_j0_" + C] * x["rdp"] * 1e4 for x in v]),
        "toll_bps": H.mean([TOLL_PAS(x) * x["rdp"] * 1e4 for x in v]),
        "net_bps": H.mean([(x["u000_j0_" + C] - TOLL_PAS(x)) * x["rdp"] * 1e4 for x in v])}
    for k, v in sorted(adv.items())}

# ---------------------------------------------------- exit side: what can rest?
exi = {}
for c in ("TRAIL025", "INC"):
    acc = {}
    for r in rows:
        x = r.get("MKT5_" + c + "_x")
        if x is None:
            continue
        acc.setdefault(x, []).append(r)
    tot = sum(len(v) for v in acc.values())
    exi[c] = {k: {"n": len(v), "share": len(v) / tot,
                  "gross_r": H.mean([r["MKT5_" + c] for r in v]),
                  "mean_exit_bar": H.mean([r["MKT5_" + c + "_b"] for r in v if r["MKT5_" + c + "_b"]])}
              for k, v in sorted(acc.items())}
    lim = sum(v["n"] for k, v in exi[c].items() if k == "target")
    exi[c]["_limitable_exit_share"] = lim / tot
    exi[c]["_exit_half_spread_saving_bps"] = (
        lim / tot) * H.mean([0.5 * r["real_spread_r"] * r["rdp"] * 1e4 for r in rows])
out["exit_side"] = exi

# ---------------------------------------------------- theoretical toll ceiling
sp = H.mean([r["real_spread_r"] * r["rdp"] * 1e4 for r in rows])
cm = H.mean([r["real_comm_r"] * r["rdp"] * 1e4 for r in rows])
sl = H.mean([r["real_slip_r"] * r["rdp"] * 1e4 for r in rows])
out["toll_ceiling"] = {
    "toll_bps": sp + cm + sl,
    "spread_bps": sp, "commission_bps": cm, "slippage_bps": sl,
    "entry_half_spread_bps": 0.5 * sp, "exit_half_spread_bps": 0.5 * sp,
    "removable_by_passive_entry_bps": 0.5 * sp + sl,
    "removable_by_passive_entry_pct": (0.5 * sp + sl) / (sp + cm + sl),
    "irreducible_commission_bps": cm,
    "irreducible_pct": cm / (sp + cm + sl),
    "floor_if_both_legs_passive_bps": cm,
}

p = H.dump(out, "H3_ENTRY_MECHANICS_V1.json")
print("validation:", json.dumps(out["validation_vs_e_build_atmkt"]))
print("\nTOLL CEILING", json.dumps(out["toll_ceiling"], indent=1))
print("\n%-46s %6s %6s %8s %8s %8s %7s %10s" %
      ("arm", "n", "fill", "edge", "toll", "net", "e/t", "net/opp"))
for a in arms:
    if a["n"] == 0:
        continue
    print("%-46s %6d %6.3f %8.4f %8.4f %8.4f %7.3f %10.5f" %
          (a["label"][:46], a["n"], a["fill_rate"], a["edge_bps"], a["toll_bps"],
           a["net_bps"], a["edge_over_toll"] or 0, a["net_bps_per_opportunity"]))
print("\nadverse selection by passive fill bar (u=0):")
for k, v in out["passive_u0_by_fill_bar"].items():
    print("  %-16s n=%6d share=%.3f edge=%8.4f toll=%7.4f net=%8.4f" %
          (k, v["n"], v["share"], v["edge_bps"], v["toll_bps"], v["net_bps"]))
print("->", p)
