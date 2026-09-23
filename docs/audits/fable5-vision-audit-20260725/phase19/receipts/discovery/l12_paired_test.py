#!/usr/bin/env python3
"""l12 step 6: paired window-level test of the score ablations, + fill-multiplier isolation.

Every arm picks from the SAME 1,969 windows, so the difference is paired: compute the
per-window delta and its t. Also adds arms that strip the fill probability from every
place it appears, and a permutation test on the winning delta.
"""
import gzip
import json
import math
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
W_EV, W_P, W_CONF, W_COMP, W_FILL, W_XFER, W_COST = 0.55, 1.20, 0.20, 0.15, 0.10, 6.00, 0.80


def arms(r):
    ev, p, c = r.get("candidate_ev_r"), r.get("candidate_probability"), r.get("cost_r")
    f, k, conf = r.get("execution_fill_probability"), r.get("source_completeness"), \
        r.get("candidate_confidence")
    if None in (ev, p, c, k, conf):
        return None
    f = 0.0 if f is None else f
    k = max(0.0, min(1.0, float(k)))
    pm, fm = max(0.0, min(1.0, p)), max(0.0, min(1.0, f))
    net = ev - c
    base = W_EV * ev + W_P * (p - .5) + W_CONF * conf + W_COMP * k + W_FILL * f
    base_nofill = W_EV * ev + W_P * (p - .5) + W_CONF * conf + W_COMP * k
    return {
        "A_as_is": base + W_XFER * max(0., net) * pm * fm * k - W_COST * c,
        "D_drop_fill_multiplier": base + W_XFER * max(0., net) * pm * k - W_COST * c,
        "N_drop_fill_everywhere": base_nofill + W_XFER * max(0., net) * pm * k - W_COST * c,
        "P_drop_fill_and_double_cost": base_nofill + W_XFER * max(0., net) * pm * k,
        "Q_drop_all_dead_constants": (W_EV * ev + W_P * (p - .5)
                                      + W_XFER * max(0., net) * pm - W_COST * c),
        "R_unfloored_net": base_nofill + W_XFER * net * pm * k,
        "H_plain_probability": p,
        "G_plain_ev": ev,
        "F_plain_expected_net": net,
    }


def summ(v):
    n = len(v)
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / max(1, n - 1)) ** .5
    return {"n": n, "mean": round(m, 6), "t": round(m / (sd / math.sqrt(n)), 3) if sd else None}


def main():
    rows = w0_ws.load()
    by = {(r["candidate_id"], r["decision_time_utc"]): r for r in rows}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if line.strip():
                a = json.loads(line)
                t = by.get((a.get("candidate_id"), a.get("decision_time_utc")))
                if t is not None:
                    t["_mkt_r"] = a.get("mkt_r_prev_close")

    out = {}
    for popname in ("ALL", "CLEAN"):
        usable = []
        for r in rows:
            if popname == "CLEAN" and not (r.get("_mkt_r") is not None
                                           and r["_mkt_r"] > -1.0):
                continue
            s = arms(r)
            if s is None:
                continue
            r["_s"] = s
            usable.append(r)
        wins = defaultdict(list)
        for r in usable:
            wins[r["decision_time_utc"]].append(r)
        keys = list(usable[0]["_s"].keys())
        picks = {k: {} for k in keys}
        for wid, cands in wins.items():
            for k in keys:
                picks[k][wid] = max(cands, key=lambda r: r["_s"][k])
        res = {"n_windows": len(wins), "levels": {}, "paired_vs_A": {}}
        for y in ("gross_r", "fill_honest_walk_r", "plain_walk_r"):
            res["levels"][y] = {}
            for k in keys:
                v = [picks[k][w].get(y) for w in wins if picks[k][w].get(y) is not None]
                res["levels"][y][k] = summ(v)
            res["paired_vs_A"][y] = {}
            for k in keys:
                if k == "A_as_is":
                    continue
                d = []
                for w in wins:
                    a, b = picks["A_as_is"][w].get(y), picks[k][w].get(y)
                    if a is not None and b is not None:
                        d.append(b - a)
                s = summ(d)
                s["frac_positive"] = round(
                    sum(1 for x in d if x > 0) / len(d), 5)
                s["frac_identical"] = round(
                    sum(1 for x in d if abs(x) < 1e-12) / len(d), 5)
                res["paired_vs_A"][y][k] = s
        out[popname] = res

    # permutation test on the headline delta (CLEAN, fill_honest, N vs A)
    rng = random.Random(4242)
    d = []
    popname = "CLEAN"
    usable = [r for r in rows if r.get("_mkt_r") is not None and r["_mkt_r"] > -1.0
              and arms(r) is not None]
    for r in usable:
        r["_s"] = arms(r)
    wins = defaultdict(list)
    for r in usable:
        wins[r["decision_time_utc"]].append(r)
    for wid, cands in wins.items():
        a = max(cands, key=lambda r: r["_s"]["A_as_is"])
        b = max(cands, key=lambda r: r["_s"]["N_drop_fill_everywhere"])
        if a.get("fill_honest_walk_r") is not None and b.get("fill_honest_walk_r") is not None:
            d.append(b["fill_honest_walk_r"] - a["fill_honest_walk_r"])
    obs = sum(d) / len(d)
    cnt = 0
    for _ in range(2000):
        s = sum(x if rng.random() < .5 else -x for x in d) / len(d)
        if abs(s) >= abs(obs):
            cnt += 1
    out["permutation_CLEAN_honest_N_vs_A"] = {
        "n_paired_windows": len(d), "observed_delta": round(obs, 6),
        "sign_flip_p": round((cnt + 1) / 2001, 5)}

    dest = os.path.join(HERE, "L12_PAIRED_TEST_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)

    for popname in ("ALL", "CLEAN"):
        r = out[popname]
        print("== %s n_windows=%d" % (popname, r["n_windows"]))
        print("   %-30s %10s %8s | %10s %8s | %9s %9s" % (
            "arm", "gross", "t", "honest", "t", "d_honest", "t(paired)"))
        for k in r["levels"]["gross_r"]:
            g = r["levels"]["gross_r"][k]
            h = r["levels"]["fill_honest_walk_r"][k]
            pv = r["paired_vs_A"]["fill_honest_walk_r"].get(k)
            print("   %-30s %10.4f %8s | %10.4f %8s | %9s %9s" % (
                k, g["mean"], g["t"], h["mean"], h["t"],
                ("%.4f" % pv["mean"]) if pv else "-",
                (str(pv["t"])) if pv else "-"))
    print("PERM:", out["permutation_CLEAN_honest_N_vs_A"])
    print("WROTE", dest)


if __name__ == "__main__":
    main()
