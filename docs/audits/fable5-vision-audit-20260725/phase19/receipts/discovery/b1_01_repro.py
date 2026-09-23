"""b1 step 1 — reproduce every cell this lane is going to build from, on ONE substrate.

If the five-month substrate does not reproduce h1/h2/h3/h5/h6's published cells, nothing
downstream is trustworthy. Every target below is quoted from the lane's own receipt.
"""
import json
import os
import sys
import time

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import b1_lib as B  # noqa: E402

M3 = B.HUNT_MONTHS


def main():
    t0 = time.time()
    rows = B.load(M3)
    out = {"substrate": {"file": "h5_SUBSTRATE_5M.jsonl.gz",
                         "n_3month": len(rows),
                         "n_all": len(B.load())}}

    # ---------------------------------------------------------------- swarm headline
    sw = B.score(rows, "K5_TRAIL025", "cost_true")
    out["A_swarm_headline_flatcost"] = B.slim(sw)
    sw_h = B.score(rows, "K5_TRAIL025", "cost_true_hour")
    out["A_swarm_headline_hourcost"] = B.slim(sw_h)

    # ---------------------------------------------------------------- h6 cell B
    # k=3, stop -1R, no target, NO TRAIL, close at 120 min (= path end), hour cost <= 0.60 bps
    selB = [r for r in rows
            if r["K3_STOPONLY"] is not None and r["cost_bps"] is not None
            and r["cost_bps"] <= 0.60 + 1e-12]
    b = B.score(selB, "K3_STOPONLY", "cost_true_hour")
    out["B_h6_hourcap060_k3"] = B.slim(b)
    out["B_h6_target"] = {"n": 3807, "gross_R": 0.114982, "cost_R": 0.046457,
                          "net_R": 0.068525, "ratio_R": 2.475, "ratio_bps": 2.036,
                          "t_net": 2.069}
    out["B_h6_symbols"] = sorted({r["symbol"] for r in selB})

    # ---------------------------------------------------------------- h1 money gate
    def bh(r):
        return (r["ny_hour"] + 7) % 24
    selM = [r for r in rows if r["cost_bps_flat"] is not None
            and r["cost_bps_flat"] <= 0.50 + 1e-12]
    out["C_h1_money_gate_050_flat_swarmcontract"] = B.slim(
        B.score(selM, "K5_TRAIL025", "cost_true"))
    selMh = [r for r in selM if 8 <= bh(r) <= 20]
    out["C_h1_money_gate_050_bh0820"] = B.slim(
        B.score(selMh, "K5_TRAIL025", "cost_true"))
    out["C_h1_target"] = {"gate050": {"n": 3191, "net_R": 0.00956, "ratio_R": 1.212},
                          "composed": {"n": 2759, "net_R": 0.01701, "ratio_R": 1.428}}

    # ---------------------------------------------------------------- h5 whole book
    allm = B.load()
    out["D_h5_five_month_book"] = B.slim(B.score(allm, "K5_TRAIL025", "cost_true_hour"))
    out["D_h5_target"] = {"n": 69480, "gross": 0.03831, "toll": 0.23020,
                          "net": -0.19188, "ratio": 0.1664}

    # ---------------------------------------------------------------- h3 family cell
    selF = [r for r in rows if r["family"] == "regime_transition_break"]
    out["E_h3_regime_transition_break_k5"] = B.slim(
        B.score(selF, "K5_TRAIL025", "cost_true"))
    out["E_h3_target"] = {"n": 828, "edge_bps": 3.6099, "toll_bps": 2.6255,
                          "ratio_bps": 1.375, "net_R": 0.01526}

    # ---------------------------------------------------------------- h2 GER40+NAS100
    out["F_h2_ger40_nas100_all_hours_hourcost"] = B.slim(
        B.score([r for r in rows if r["symbol"] in ("GER40", "NAS100")],
                "K5_TRAIL025", "cost_true_hour"))

    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_REPRO_V1.json", "w") as f:
        json.dump(out, f, indent=1, default=str)

    for k in ("A_swarm_headline_flatcost", "B_h6_hourcap060_k3",
              "C_h1_money_gate_050_bh0820", "D_h5_five_month_book",
              "E_h3_regime_transition_break_k5"):
        s = out[k]
        print(f"{k:42s} n={s['n']:6d} gross={s['gross_R']:+.6f} cost={s['cost_R']:.6f} "
              f"net={s['net_R']:+.6f} ratio={s['ratio_R']}")
    print("B symbols:", out["B_h6_symbols"])
    print("elapsed", out["elapsed_s"])


if __name__ == "__main__":
    main()
