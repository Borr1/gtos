"""h3-05 -- entry mechanics, part 2: ABSTAIN-on-early-touch, the delay curve in bps, and
the swarm's 60-second CANCEL priced on the cohort it actually lives on.

Three things h3-04 could not answer.

1. h3-04's `cancel<Nmin` arms RE-REST the limit after refusing an early fill, so they buy a
   later, worse fill in a trend. The swarm's rule is not that -- it is CANCEL AND ABSTAIN.
   Here the trade only exists when the FIRST touch is at or after minute N; otherwise the
   opportunity books zero.

2. The delay lever priced in bps over the whole K ladder, so it can be ranked against the
   cost levers on one axis.

3. The 60-second cancel measured on `born_resting` -- the 46 % of the pool that is a passive
   limit at a price away from the market. That is where the swarm measured it, and l10-X3
   established the live engine has no TRADE_ACTION_PENDING entry path, so the number is
   reported with that disqualification attached rather than folded into the live book.
"""
import gzip
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib as H  # noqa: E402
import e_lib        # noqa: E402

U = [0.0, 0.05, 0.10, 0.25, 0.50]
ABST = [1, 2, 3, 5, 10, 15]
C = "TRAIL025"


def load_pas():
    rows = []
    for mm in ("202601", "202602", "202603"):
        for line in gzip.open(os.path.join(D, f"H3_PASSIVE_ROWS_{mm}.jsonl.gz"), "rt"):
            if line.strip():
                rows.append(json.loads(line))
    return rows


rows = load_pas()
N = len(rows)
out = {"lane": "h3", "step": "entry_mechanics_2", "n_opportunities": N, "contract": C}

TOLL_MKT = lambda r: r["real_spread_r"] + r["real_comm_r"] + r["real_slip_r"]   # noqa: E731
TOLL_PAS = lambda r: 0.5 * r["real_spread_r"] + r["real_comm_r"]                # noqa: E731


def score(rows, getter, toll_fn, label, extra=None):
    g, t, n, keep = [], [], [], []
    for r in rows:
        v = getter(r)
        if v is None:
            continue
        gb = v * r["rdp"] * 1e4
        tb = toll_fn(r) * r["rdp"] * 1e4
        g.append(gb); t.append(tb); n.append(gb - tb); keep.append(r)
    opp = {r["day"]: [] for r in rows}
    for r, v in zip(keep, n):
        opp[r["day"]].append(v)
    for r in rows:
        pass
    cnt = {d: 0 for d in opp}
    for r in rows:
        cnt[r["day"]] += 1
    dser = [(sum(opp[d]) / cnt[d]) for d in sorted(opp)]
    if not g:
        return {"label": label, "n": 0}
    d = {"label": label, "n": len(g), "fill_rate": len(g) / len(rows),
         "edge_bps": H.mean(g), "toll_bps": H.mean(t), "net_bps": H.mean(n),
         "edge_over_toll": H.mean(g) / H.mean(t) if H.mean(t) else None,
         "gross_r": H.mean([getter(r) for r in keep]),
         "net_r": H.mean([getter(r) - toll_fn(r) for r in keep]),
         "net_bps_per_opportunity": H.mean(n) * len(g) / len(rows),
         "net_r_per_opportunity": H.mean([getter(r) - toll_fn(r) for r in keep]) * len(g) / len(rows),
         "t_net_trade": H.tstat(n), "t_daily_per_opp": H.tstat(dser),
         "days": len(dser), "days_positive": sum(1 for x in dser if x > 0)}
    for m in sorted(H.MONTHS):
        sub = [r for r in rows if r["month"] == m]
        gg = [getter(r) for r in sub if getter(r) is not None]
        if gg:
            kk = [r for r in sub if getter(r) is not None]
            d["m_" + m] = {"n": len(gg),
                           "edge_bps": H.mean([getter(r) * r["rdp"] * 1e4 for r in kk]),
                           "toll_bps": H.mean([toll_fn(r) * r["rdp"] * 1e4 for r in kk]),
                           "net_bps": H.mean([(getter(r) - toll_fn(r)) * r["rdp"] * 1e4 for r in kk])}
    if extra:
        d.update(extra)
    return d


# ------------------------------------------------- 1. ABSTAIN-on-early-touch arms
arms = [score(rows, lambda r: r.get("MKT0_" + C), TOLL_MKT, "MKT0 at-market baseline"),
        score(rows, lambda r: r.get("MKT5_" + C), TOLL_MKT, "MKT5 at-market +5min HEADLINE")]
for u in U:
    tag = f"u{int(round(u * 100)):03d}"
    arms.append(score(rows, lambda r, k=tag: r.get(f"{k}_j0_{C}"), TOLL_PAS,
                      f"PAS u={u} take first touch", extra={"u_R": u, "abstain_before_min": 0}))
    for a in ABST:
        def get(r, k=tag, a=a):
            j = r.get(f"{k}_j0")
            if j is None or j < a:
                return None
            return r.get(f"{k}_j0_{C}")
        arms.append(score(rows, get, TOLL_PAS,
                          f"PAS u={u} ABSTAIN if touched before min {a}",
                          extra={"u_R": u, "abstain_before_min": a}))
out["abstain_arms"] = arms

# --------------------------------------------- 2. the delay curve, in bps, at-market
atm = H.load_atmkt()
dc = []
for k in H.KS:
    col = f"K{k}_{C}"
    d = H.summarize(atm, col, "cost_true", f"at-market delay {k} min")
    d["delay_min"] = k
    d["by_month"] = {m: H.summarize([r for r in atm if r["month"] == m], col,
                                    "cost_true", m)["edge_bps"] for m in sorted(H.MONTHS)}
    dc.append(d)
out["delay_curve_bps"] = dc
base = [d for d in dc if d["delay_min"] == 0][0]
out["delay_lever_value_bps"] = {"best_k": max(dc, key=lambda d: d["edge_bps"])["delay_min"],
                                "best_edge_bps": max(d["edge_bps"] for d in dc),
                                "k0_edge_bps": base["edge_bps"],
                                "gain_at_k5_bps": [d for d in dc if d["delay_min"] == 5][0]["edge_bps"] - base["edge_bps"],
                                "gain_at_best_bps": max(d["edge_bps"] for d in dc) - base["edge_bps"],
                                "note": "PURE EDGE lever: toll is identical at every k (cost is not delay-dependent)"}

# ------------------------------------ 3. the 60 s cancel on the born_resting cohort
bs = H.load_base()
out["base_born_census"] = {}
for b in sorted({r["born"] for r in bs}):
    sub = [r for r in bs if r["born"] == b]
    out["base_born_census"][b] = {"n": len(sub), "share": len(sub) / len(bs)}
rest = [r for r in bs if r["born"] == "born_resting" and r.get("cost_true") is not None
        and r.get("t_first") is not None]
takeable = [r for r in bs if r["born"] in ("born_resting", "born_at_limit", "born_marketable")
            and r.get("cost_true") is not None]


def sc(rows, valf, tollf, label):
    g = [valf(r) * r["rdp"] * 1e4 for r in rows if valf(r) is not None]
    t = [tollf(r) * r["rdp"] * 1e4 for r in rows if valf(r) is not None]
    n = [a - b for a, b in zip(g, t)]
    if not g:
        return {"label": label, "n": 0}
    return {"label": label, "n": len(g), "edge_bps": H.mean(g), "toll_bps": H.mean(t),
            "net_bps": H.mean(n), "edge_over_toll": H.mean(g) / H.mean(t) if H.mean(t) else None,
            "gross_r": H.mean([valf(r) for r in rows if valf(r) is not None]),
            "t_net": H.tstat(n)}


VR = lambda r: r.get("R_" + C)   # noqa: E731
canc = {"all_resting": sc(rest, VR, TOLL_MKT, "born_resting, all fills"),
        "resting_touch_le_1min": sc([r for r in rest if r["t_first"] is not None and r["t_first"] <= 1],
                                    VR, TOLL_MKT, "touched inside 60 s"),
        "resting_touch_gt_1min": sc([r for r in rest if r["t_first"] is not None and r["t_first"] > 1],
                                    VR, TOLL_MKT, "touched after 60 s (the CANCEL survivors)")}
canc["cancel_edge_gain_bps"] = (canc["resting_touch_gt_1min"]["edge_bps"]
                                - canc["all_resting"]["edge_bps"])
canc["cancel_toll_change_bps"] = (canc["resting_touch_gt_1min"]["toll_bps"]
                                  - canc["all_resting"]["toll_bps"])
canc["keep_rate"] = canc["resting_touch_gt_1min"]["n"] / canc["all_resting"]["n"]
canc["DISQUALIFICATION"] = ("born_resting is a passive limit at a price away from the market. "
                            "l10-X3: 296/296 live entries equal the executable quote exactly and "
                            "the live engine defines TRADE_ACTION_PENDING once and never uses it "
                            "for entry. This cohort is NOT live-placeable; the number is a "
                            "counterfactual, not a lever on the live book.")
out["cancel_on_resting_cohort"] = canc

p = H.dump(out, "H3_ENTRY2_V1.json")
print("%-52s %6s %6s %8s %8s %8s %7s %10s" %
      ("arm", "n", "fill", "edge", "toll", "net", "e/t", "net/opp"))
for a in arms:
    if not a.get("n"):
        continue
    print("%-52s %6d %6.3f %8.4f %8.4f %8.4f %7.3f %10.5f" %
          (a["label"][:52], a["n"], a["fill_rate"], a["edge_bps"], a["toll_bps"],
           a["net_bps"], a["edge_over_toll"] or 0, a["net_bps_per_opportunity"]))
print("\nDELAY CURVE (at-market, toll constant 2.4571 bps):")
for d in dc:
    print("  k=%3d edge=%8.4f bps net=%8.4f e/t=%6.3f  months %s"
          % (d["delay_min"], d["edge_bps"], d["net_bps"], d["edge_over_toll"],
             " ".join("%.3f" % v for v in d["by_month"].values())))
print("\nCANCEL on born_resting:", json.dumps({k: v for k, v in canc.items()
                                               if k != "DISQUALIFICATION"}, indent=1)[:1400])
print("->", p)
