"""h3-01 -- reproduce the synthesis headline, then decompose the 2.457 bps toll.

Nothing downstream is trusted until the anchor reproduces to the published decimals.
"""
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib as H  # noqa: E402

rows = H.load_atmkt(require_cost=False)
with_cost = [r for r in rows if r.get("cost_true") is not None]
out = {"lane": "h3", "step": "anchor",
       "n_loaded": len(rows), "n_with_broker_true_cost": len(with_cost),
       "n_dropped_no_tick_truth": len(rows) - len(with_cost),
       "dropped_symbols": sorted({r["symbol"] for r in rows if r.get("cost_true") is None}),
       "by_month": {}}
for m in sorted(H.MONTHS):
    out["by_month"][m] = sum(1 for r in rows if r["month"] == m)

# ---- the published headline: K5_TRAIL025, broker-true cost, all 24 instruments
head = H.summarize(with_cost, "K5_TRAIL025", label="published headline K5_TRAIL025")
out["headline"] = head
out["published"] = {"n": 43755, "cost_r": 0.18183, "gross_r": 0.03834, "net_r": -0.14349,
                    "edge_bps": 0.231, "toll_bps": 2.457, "t_gross": 12.35,
                    "days_gross_positive": 53, "days": 63}
out["anchor_check"] = {
    "n_match": head["n"] == 43755,
    "gross_r_absdiff": abs(head["gross_r"] - 0.03834),
    "cost_r_absdiff": abs(head["cost_r"] - 0.18183),
    "edge_bps_absdiff": abs(head["edge_bps"] - 0.231),
    "toll_bps_absdiff": abs(head["toll_bps"] - 2.457),
}

# ---- toll decomposition, in R and in bps, per trade
comp = {}
for k, f in (("spread", "real_spread_r"), ("commission", "real_comm_r"),
             ("slippage", "real_slip_r")):
    r_vals = [r[f] for r in with_cost]
    b_vals = [r[f] * r["rdp"] * 1e4 for r in with_cost]
    comp[k] = {"mean_r": H.mean(r_vals), "mean_bps": H.mean(b_vals),
               "share_of_toll_bps": None, "n_nonzero": sum(1 for x in r_vals if x > 1e-12)}
tot = sum(comp[k]["mean_bps"] for k in comp)
for k in comp:
    comp[k]["share_of_toll_bps"] = comp[k]["mean_bps"] / tot
out["toll_decomposition"] = comp
out["toll_decomposition"]["TOTAL_bps"] = tot

# ---- frozen model, for contrast (what the engine actually charges today)
fr = [r["cost_frozen"] for r in with_cost if r.get("cost_frozen") is not None]
frb = [r["cost_frozen"] * r["rdp"] * 1e4 for r in with_cost if r.get("cost_frozen") is not None]
sw = [r.get("swap_r") or 0.0 for r in with_cost]
out["frozen_model"] = {"n": len(fr), "mean_cost_r": H.mean(fr), "mean_cost_bps": H.mean(frb),
                       "overcharge_x_r": H.mean(fr) / H.mean([r["cost_true"] for r in with_cost]),
                       "frozen_swap_r_mean": H.mean(sw),
                       "frozen_swap_bps_mean": H.mean([(r.get("swap_r") or 0.0) * r["rdp"] * 1e4
                                                       for r in with_cost])}

# ---- per-symbol table at the headline contract
per = {}
for r in with_cost:
    per.setdefault(r["symbol"], []).append(r)
tab = []
for s, rs in per.items():
    d = H.summarize(rs, "K5_TRAIL025", label=s)
    d["symbol"] = s
    d["mean_rdp_bps"] = H.mean([x["rdp_bps"] for x in rs])
    d["spread_bps_flat"] = H.mean([x["real_spread_r"] * x["rdp"] * 1e4 for x in rs])
    d["comm_bps_flat"] = H.mean([x["real_comm_r"] * x["rdp"] * 1e4 for x in rs])
    d["slip_bps_flat"] = H.mean([x["real_slip_r"] * x["rdp"] * 1e4 for x in rs])
    tab.append(d)
tab.sort(key=lambda x: x["toll_bps"])
out["per_symbol"] = tab
out["n_symbols"] = len(tab)
out["n_symbols_edge_over_toll_ge_1"] = sum(1 for x in tab if x["edge_over_toll"] and x["edge_over_toll"] >= 1)

p = H.dump(out, "H3_ANCHOR_V1.json")
print(json.dumps({k: out[k] for k in ("n_loaded", "n_with_broker_true_cost",
                                      "n_dropped_no_tick_truth", "dropped_symbols",
                                      "anchor_check", "n_symbols",
                                      "n_symbols_edge_over_toll_ge_1")}, indent=1))
print("HEADLINE", json.dumps(head, indent=1))
print("TOLL", json.dumps(out["toll_decomposition"], indent=1))
print("FROZEN", json.dumps(out["frozen_model"], indent=1))
print("->", p)
