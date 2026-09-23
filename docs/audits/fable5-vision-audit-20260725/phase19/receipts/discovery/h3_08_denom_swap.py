"""h3-08 -- STOP WIDTH (item 4) and HOLDING TIME / SWAP (item 5).

Item 4. `cost_r = cost_price / risk_distance` is an identity, so every R-denominated cost
number in this estate is a quotient of a real quantity by a policy choice. This measures how
much of the R-space cost dispersion is the numerator (real money) and how much is the
denominator (the stop the generator happened to emit). The sign invariance is ESTABLISHED
(l2-F2, e5-F3) and is not re-derived here -- only the denomination is quantified.

    ln cost_r = ln cost_bps - ln rdp_bps
    Var(ln cost_r) = Var(ln cost_bps) + Var(ln rdp_bps) - 2 Cov(.,.)

Item 5. Every path in this substrate is capped at 120 M1 bars = 2 h, so no trade can reach a
swap boundary unless it is opened within 2 h of one. That is measurable exactly, and so is
what the FROZEN model charges for carry that cannot be incurred. The live lever that DOES
exist on this axis is not swap -- it is that a round-trip toll is a FIXED charge, so the
longer a position is held the more gross move it amortises the toll over. That is measured
as toll per hour held, per exit contract.
"""
import gzip
import json
import math
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib as H  # noqa: E402
import e_lib        # noqa: E402

COL = "K5_TRAIL025"
rows = H.load_atmkt()
out = {"lane": "h3", "step": "denomination_and_holding", "n": len(rows), "contract": COL}


# ------------------------------------------------------------- 4. denomination
def var(v):
    m = H.mean(v)
    return sum((x - m) ** 2 for x in v) / (len(v) - 1)


def cov(a, b):
    ma, mb = H.mean(a), H.mean(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (len(a) - 1)


lc_r = [math.log(r["cost_true"]) for r in rows if r["cost_true"] > 0]
sub = [r for r in rows if r["cost_true"] > 0]
lc_b = [math.log(r["cost_true"] * r["rdp"] * 1e4) for r in sub]
l_rdp = [math.log(r["rdp_bps"]) for r in sub]
out["log_variance_decomposition"] = {
    "n": len(sub),
    "var_ln_cost_r": var(lc_r), "var_ln_cost_bps": var(lc_b), "var_ln_rdp_bps": var(l_rdp),
    "cov_lncostbps_lnrdp": cov(lc_b, l_rdp),
    "identity_residual": var(lc_r) - (var(lc_b) + var(l_rdp) - 2 * cov(lc_b, l_rdp)),
    "share_of_var_ln_cost_r_from_stop_width": var(l_rdp) / var(lc_r),
    "share_of_var_ln_cost_r_from_real_money": var(lc_b) / var(lc_r),
}


def spear(pairs):
    a = sorted(range(len(pairs)), key=lambda i: pairs[i][0])
    b = sorted(range(len(pairs)), key=lambda i: pairs[i][1])
    ra = {v: i for i, v in enumerate(a)}
    rb = {v: i for i, v in enumerate(b)}
    n = len(pairs)
    return 1 - 6 * sum((ra[i] - rb[i]) ** 2 for i in range(n)) / (n * (n * n - 1))


out["spearman_cost_r_vs_inverse_stop"] = spear([(r["cost_true"], 1.0 / r["rdp"]) for r in rows])
out["spearman_cost_r_vs_cost_bps"] = spear([(r["cost_true"], r["cost_true"] * r["rdp"] * 1e4)
                                            for r in rows])

# family dispersion in both spaces -- the 12.1x claim, re-expressed
fam = {}
for r in rows:
    fam.setdefault(r.get("family") or "none", []).append(r)
ft = []
for f, rs in fam.items():
    ft.append({"family": f, "n": len(rs),
               "cost_r": H.mean([r["cost_true"] for r in rs]),
               "cost_bps": H.mean([r["cost_true"] * r["rdp"] * 1e4 for r in rs]),
               "rdp_bps": H.mean([r["rdp_bps"] for r in rs]),
               "edge_bps": H.mean([r[COL] * r["rdp"] * 1e4 for r in rs]),
               "edge_over_toll": (H.mean([r[COL] * r["rdp"] * 1e4 for r in rs])
                                  / H.mean([r["cost_true"] * r["rdp"] * 1e4 for r in rs]))})
ft.sort(key=lambda d: d["cost_r"])
out["family_dispersion"] = {
    "cells": ft,
    "cost_r_spread_x": max(d["cost_r"] for d in ft) / min(d["cost_r"] for d in ft),
    "cost_bps_spread_x": max(d["cost_bps"] for d in ft) / min(d["cost_bps"] for d in ft),
    "rdp_bps_spread_x": max(d["rdp_bps"] for d in ft) / min(d["rdp_bps"] for d in ft),
}
sy = {}
for r in rows:
    sy.setdefault(r["symbol"], []).append(r)
st = [{"symbol": s, "n": len(rs), "cost_r": H.mean([r["cost_true"] for r in rs]),
       "cost_bps": H.mean([r["cost_true"] * r["rdp"] * 1e4 for r in rs]),
       "rdp_bps": H.mean([r["rdp_bps"] for r in rs])} for s, rs in sy.items()]
out["symbol_dispersion"] = {
    "cells": sorted(st, key=lambda d: d["cost_r"]),
    "cost_r_spread_x": max(d["cost_r"] for d in st) / min(d["cost_r"] for d in st),
    "cost_bps_spread_x": max(d["cost_bps"] for d in st) / min(d["cost_bps"] for d in st),
    "rdp_bps_spread_x": max(d["rdp_bps"] for d in st) / min(d["rdp_bps"] for d in st)}

# the mechanical statement, verified numerically on the real rows
w = {}
for f in (1.0, 1.5, 2.0, 3.0, 5.0):
    cr = [r["cost_true"] / f for r in rows]
    cb = [(r["cost_true"] / f) * (r["rdp"] * f) * 1e4 for r in rows]
    w[f"widen_x{f}"] = {"mean_cost_r": H.mean(cr), "mean_cost_bps": H.mean(cb),
                        "cost_r_vs_base": H.mean(cr) / H.mean([r["cost_true"] for r in rows]),
                        "cost_bps_vs_base": H.mean(cb) / H.mean([r["cost_true"] * r["rdp"] * 1e4
                                                                 for r in rows])}
out["stop_widen_identity"] = w

# rdp decile x affordability
ds = sorted(rows, key=lambda r: r["rdp_bps"])
dec = []
for i in range(10):
    lo, hi = i * len(ds) // 10, (i + 1) * len(ds) // 10
    rs = ds[lo:hi]
    g, t, n, keep = H.scored(rs, COL, "cost_true")
    dec.append({"decile": i + 1, "n": len(rs),
                "rdp_bps_lo": rs[0]["rdp_bps"], "rdp_bps_hi": rs[-1]["rdp_bps"],
                "cost_r": H.mean([r["cost_true"] for r in rs]),
                "edge_bps": H.mean(g), "toll_bps": H.mean(t), "net_bps": H.mean(n),
                "edge_over_toll": H.mean(g) / H.mean(t),
                "net_r": H.mean([r[COL] - r["cost_true"] for r in keep])})
out["rdp_deciles"] = dec

# ------------------------------------------------------ 5. holding time and swap
pas = []
for mm in ("202601", "202602", "202603"):
    for line in gzip.open(os.path.join(D, f"H3_PASSIVE_ROWS_{mm}.jsonl.gz"), "rt"):
        if line.strip():
            pas.append(json.loads(line))

# broker rollover = broker midnight = NY 17:00 (validated in h3-03 by the spread peak)
cross = 0
for r in pas:
    b = r.get("MKT5_TRAIL025_b") or r["path_bars"]
    h = r["ny_hour"]
    mins = int(r["dt"][14:16])
    # minutes from decision until the next NY 17:00
    to_roll = ((17 - h) % 24) * 60 - mins
    if to_roll <= 0:
        to_roll += 1440
    if b + 5 >= to_roll:
        cross += 1
out["swap"] = {
    "n": len(pas),
    "trades_whose_holding_window_reaches_a_rollover": cross,
    "share": cross / len(pas),
    "rollover_definition": "broker midnight = NY 17:00, validated by the spread peak in h3-03",
    "broker_true_swap_charged_bps": 0.0,
    "frozen_model_swap_r_mean": H.mean([r.get("swap_r") or 0.0 for r in rows]),
    "frozen_model_swap_bps_mean": H.mean([(r.get("swap_r") or 0.0) * r["rdp"] * 1e4 for r in rows]),
    "frozen_model_total_bps": H.mean([r["cost_frozen"] * r["rdp"] * 1e4 for r in rows
                                      if r.get("cost_frozen") is not None]),
}
out["swap"]["frozen_swap_share_of_frozen_toll"] = (
    out["swap"]["frozen_model_swap_bps_mean"] / out["swap"]["frozen_model_total_bps"])

# holding time: toll amortisation per contract
hold = []
for c in ("INC", "TRAIL025"):
    bars = [r.get("MKT5_" + c + "_b") for r in pas if r.get("MKT5_" + c + "_b")]
    g = [r["MKT5_" + c] * r["rdp"] * 1e4 for r in pas if r.get("MKT5_" + c) is not None]
    t = [r["cost_true"] * r["rdp"] * 1e4 for r in pas if r.get("MKT5_" + c) is not None]
    hold.append({"contract": c, "n": len(g), "mean_hold_min": H.mean(bars),
                 "median_hold_min": H.q(bars, 0.5) if hasattr(H, "q") else None,
                 "edge_bps": H.mean(g), "toll_bps": H.mean(t),
                 "edge_over_toll": H.mean(g) / H.mean(t),
                 "toll_bps_per_hour_held": H.mean(t) / (H.mean(bars) / 60.0),
                 "edge_bps_per_hour_held": H.mean(g) / (H.mean(bars) / 60.0)})
out["holding_time_amortisation"] = hold

# edge and toll by realised holding bucket, headline contract
buck = {}
for r in pas:
    b = r.get("MKT5_TRAIL025_b")
    if b is None or r.get("MKT5_TRAIL025") is None:
        continue
    k = ("le5" if b <= 5 else "6_15" if b <= 15 else "16_30" if b <= 30 else
         "31_60" if b <= 60 else "61_115" if b <= 115 else "116_120_horizon")
    buck.setdefault(k, []).append(r)
out["by_realised_hold"] = {
    k: {"n": len(v), "share": len(v) / len(pas),
        "mean_hold_min": H.mean([r["MKT5_TRAIL025_b"] for r in v]),
        "edge_bps": H.mean([r["MKT5_TRAIL025"] * r["rdp"] * 1e4 for r in v]),
        "toll_bps": H.mean([r["cost_true"] * r["rdp"] * 1e4 for r in v]),
        "net_bps": H.mean([(r["MKT5_TRAIL025"] - r["cost_true"]) * r["rdp"] * 1e4 for r in v])}
    for k, v in sorted(buck.items())}

# what a longer horizon would do: contracts with different time stops, at k=5
alt = []
for c in ("TS90S1", "TS60S1", "INC", "T3S1", "STOPONLY", "TRAIL025"):
    col = "K5_" + c
    if not any(r.get(col) is not None for r in rows):
        continue
    d = H.summarize(rows, col, "cost_true", c)
    d["contract"] = c
    alt.append(d)
out["contract_menu_at_k5"] = sorted(alt, key=lambda d: -(d["edge_over_toll"] or -9))

p = H.dump(out, "H3_DENOM_SWAP_V1.json")
print("VAR DECOMP", json.dumps(out["log_variance_decomposition"], indent=1))
print("spearman(cost_r, 1/rdp) = %.4f   spearman(cost_r, cost_bps) = %.4f"
      % (out["spearman_cost_r_vs_inverse_stop"], out["spearman_cost_r_vs_cost_bps"]))
print("family dispersion: cost_r %.2fx  cost_bps %.2fx  rdp %.2fx"
      % (out["family_dispersion"]["cost_r_spread_x"],
         out["family_dispersion"]["cost_bps_spread_x"],
         out["family_dispersion"]["rdp_bps_spread_x"]))
print("symbol dispersion: cost_r %.2fx  cost_bps %.2fx  rdp %.2fx"
      % (out["symbol_dispersion"]["cost_r_spread_x"],
         out["symbol_dispersion"]["cost_bps_spread_x"],
         out["symbol_dispersion"]["rdp_bps_spread_x"]))
print("\nrdp deciles:")
for d in dec:
    print("  d%2d n=%5d rdp=%8.2f-%8.2f bps cost_r=%.4f edge=%7.4f toll=%7.4f e/t=%6.3f net_r=%+.5f"
          % (d["decile"], d["n"], d["rdp_bps_lo"], d["rdp_bps_hi"], d["cost_r"],
             d["edge_bps"], d["toll_bps"], d["edge_over_toll"], d["net_r"]))
print("\nSWAP", json.dumps(out["swap"], indent=1))
print("\nHOLDING", json.dumps(out["holding_time_amortisation"], indent=1))
print("\nby realised hold:")
for k, v in out["by_realised_hold"].items():
    print("  %-18s n=%6d share=%.3f hold=%6.1f edge=%8.4f toll=%7.4f net=%8.4f"
          % (k, v["n"], v["share"], v["mean_hold_min"], v["edge_bps"], v["toll_bps"], v["net_bps"]))
print("\ncontract menu at k=5:")
for d in out["contract_menu_at_k5"]:
    print("  %-10s n=%5d edge=%8.4f toll=%7.4f net=%8.4f e/t=%6.3f"
          % (d["contract"], d["n"], d["edge_bps"], d["toll_bps"], d["net_bps"], d["edge_over_toll"]))
print("->", p)
