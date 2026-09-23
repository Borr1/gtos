"""b1 step 2 — join h1's four-term broker-true cost onto the substrate (3 hunt months).

h5's cost_true_hour = hour-aware tick spread + commission + measured slippage.
h1's total_r        = the same THREE terms with a corrected BTCUSD/ETHUSD commission
                      (e_lib normalises a live-window price-unit measurement by a
                      January price; h1/h4 both measured the error at 1.47-1.81x)
                      PLUS swap charged per rollover crossing.

Emits b1_COST_JOIN_V1.jsonl.gz: cid|dt -> {cost_h1_r, cost_h1_flat_r, cost_h1_era_r,
swap_r, broker_hour, kill_zone, instrument_class}. Also reports the join coverage and
the three bases side by side, so every downstream number can be quoted at any of them.
"""
import gzip
import json
import os
import sys
import time

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import b1_lib as B  # noqa: E402


def main():
    t0 = time.time()
    h1 = {}
    for ln in gzip.open(f"{D}/h1_COST_ROWS_V1.jsonl.gz", "rt"):
        r = json.loads(ln)
        h1[(r["cid"], r["dt"])] = r

    rows = B.load(B.HUNT_MONTHS)
    hit = miss = 0
    out = []
    for r in rows:
        k = (r["cid"], r["dt"])
        h = h1.get(k)
        if h is None:
            miss += 1
            continue
        hit += 1
        out.append({"cid": r["cid"], "dt": r["dt"],
                    "cost_h1_r": h["total_r"], "cost_h1_flat_r": h["total_r_flat"],
                    "cost_h1_era_r": h["total_r_era"], "cost_h1_noswap_r": h["total_r_noswap"],
                    "swap_r": h["swap_r"], "comm_r_h1": h["comm_r"],
                    "spread_r_h1": h["spread_r"],
                    "broker_hour": h["broker_hour"], "broker_dow": h["broker_dow"],
                    "kill_zone": h["kill_zone"],
                    "instrument_class": h["instrument_class"],
                    "era_ratio": h["era_ratio"], "era_class": h["era_class"]})

    with gzip.open(f"{D}/b1_COST_JOIN_V1.jsonl.gz", "wt") as f:
        for o in out:
            f.write(json.dumps(o) + "\n")

    # side-by-side of the three bases on the joined population
    idx = {(o["cid"], o["dt"]): o for o in out}
    js = [r for r in rows if (r["cid"], r["dt"]) in idx]
    for r in js:
        o = idx[(r["cid"], r["dt"])]
        r["cost_h1_r"] = o["cost_h1_r"]
        r["cost_h1_noswap_r"] = o["cost_h1_noswap_r"]

    def mm(key):
        v = [r[key] for r in js]
        vb = [r[key] * r["rdp"] * 1e4 for r in js]
        return {"mean_R": sum(v) / len(v), "mean_bps": sum(vb) / len(vb)}

    rec = {"n_substrate_3m": len(rows), "n_h1_rows": len(h1),
           "joined": hit, "missed": miss,
           "bases": {"swarm_flat_cost_true": mm("cost_true"),
                     "b1_headline_cost_true_hour": mm("cost_true_hour"),
                     "h1_broker_true_4term": mm("cost_h1_r"),
                     "h1_broker_true_noswap": mm("cost_h1_noswap_r")},
           "elapsed_s": round(time.time() - t0, 1)}
    with open(f"{D}/B1_COSTJOIN_V1.json", "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
