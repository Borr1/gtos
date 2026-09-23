"""e5 step 4 — L2-F6's own limit case, taken seriously.

If widening the stop always helps and the limit (no stop at all) is the best stop rule,
then the binding contract is not the stop -- it is the HOLDING TIME. This measures the
fill-honest mark-to-market at every minute t = 1..120 after the decision, for three
exit contracts, per month and per cohort:

  C0  no stop, no target        -> pure holding-time value of the signal
  C1  stop -1R, no target       -> what the shipped stop costs, minute by minute
  C2  stop -1R, target +2R      -> the shipped contract with a time exit at t (t=120 = as shipped)

Unfilled candidates contribute 0.0 (no position), which is the honest portfolio view.
Writes E5_TIME_CURVE_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)

OUT = os.path.join(D, "E5_TIME_CURVE_V1.json")
MONTHS = ["january", "february", "march"]
H = 120


def curves(sub):
    """returns dict contract -> [mean R at t=1..H]"""
    n = len(sub)
    acc = {"C0": [0.0] * H, "C1": [0.0] * H, "C2": [0.0] * H}
    for e in sub:
        fav, adv, cls, tgt = e["fav"], e["adv"], e["cls"], e["tgt"]
        L = len(fav)
        fb = e["fb"]
        if fb is None:
            continue
        # C0: no stop no target -> value at t is cls[min(t,L-1)] once filled
        # C1: stop at -1
        # C2: stop at -1, target at tgt
        s1 = None   # bar index at which the -1 stop fires
        s2 = None   # bar index at which C2 terminates, and its value
        v2 = None
        for i in range(fb, L):
            if s1 is None and adv[i] <= -1.0 + 1e-12:
                s1 = i
            if s2 is None:
                if adv[i] <= -1.0 + 1e-12:
                    s2 = i; v2 = -1.0
                elif fav[i] >= tgt - 1e-12:
                    s2 = i; v2 = tgt
            if s1 is not None and s2 is not None:
                break
        for t in range(H):
            if t < fb:
                continue
            j = min(t, L - 1)
            acc["C0"][t] += cls[j]
            acc["C1"][t] += (-1.0 if (s1 is not None and s1 <= t) else cls[j])
            acc["C2"][t] += (v2 if (s2 is not None and s2 <= t) else cls[j])
    return {k: [round(v / n, 6) for v in a] for k, a in acc.items()}


def cost(sub):
    n = len(sub)
    return {
        "C_frozen": round(sum(e["sp"] + e["cm"] + e["sww"] + e["sl"] for e in sub) / n, 6),
        "C_sp73": round(sum(e["sp"] / 7.3 + e["cm"] + e["sww"] + e["sl"] for e in sub) / n, 6),
        "C_sp85": round(sum(e["sp"] / 8.5 + e["cm"] + e["sww"] + e["sl"] for e in sub) / n, 6),
    }


def load(m):
    ents = []
    with gzip.open(os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % m), "rt") as f:
        for ln in f:
            r = json.loads(ln)
            mk = r["mkt_r_prev_close"]
            if mk is not None and mk <= -1.0:
                continue
            adv = r["adv"]
            fb = next((i for i in range(len(adv)) if adv[i] <= 1e-12), None)
            if fb is None:
                continue
            ents.append({"fav": r["fav"], "adv": adv, "cls": r["cls"], "fb": fb,
                         "tgt": (r.get("policy_target_r") or 2.0),
                         "sym": r.get("symbol"), "fam": r.get("origin_family"),
                         "sess": r.get("session_bucket"), "side": r.get("side"),
                         "sp": float(r.get("spread_r") or 0.0), "cm": float(r.get("commission_r") or 0.0),
                         "sww": float(r.get("swap_cost_r") or 0.0),
                         "sl": float(r.get("expected_slippage_r") or 0.0)})
    return ents


res = {"schema": "gtos.e5.time_curve.v1", "horizon_minutes": H}
for m in MONTHS:
    ents = load(m)
    c = curves(ents)
    ct = cost(ents)
    best = {k: (max(range(H), key=lambda i: v[i]) + 1, round(max(v), 6)) for k, v in c.items()}
    mm = {"n": len(ents), "cost": ct, "curves": c, "argmax": best,
          "C0_t120": c["C0"][-1], "C1_t120": c["C1"][-1], "C2_t120": c["C2"][-1],
          "stop_cost_at_120": round(c["C0"][-1] - c["C1"][-1], 6),
          "contract_cost_at_120": round(c["C0"][-1] - c["C2"][-1], 6)}
    # per cohort: C0 curve argmax and both-sides check at that t
    for label, kf in (("by_symbol", lambda e: e["sym"]), ("by_family", lambda e: e["fam"]),
                      ("by_session", lambda e: e["sess"])):
        g = {}
        grp = {}
        for e in ents:
            k = kf(e)
            if k:
                grp.setdefault(str(k), []).append(e)
        for k, sub in grp.items():
            if len(sub) < 150:
                continue
            cc = curves(sub)
            cs = cost(sub)
            t0 = max(range(H), key=lambda i: cc["C0"][i])
            lo = [e for e in sub if (e["side"] or "").startswith("L")]
            sh = [e for e in sub if (e["side"] or "").startswith("S")]
            cl = curves(lo)["C0"] if len(lo) >= 20 else None
            cs2 = curves(sh)["C0"] if len(sh) >= 20 else None
            g[k] = {"n": len(sub), **cs,
                    "C0_t120": cc["C0"][-1], "C1_t120": cc["C1"][-1], "C2_t120": cc["C2"][-1],
                    "C0_best_t": t0 + 1, "C0_best": cc["C0"][t0],
                    "gap120_sp73": round(cc["C0"][-1] - cs["C_sp73"], 6),
                    "gapbest_sp73": round(cc["C0"][t0] - cs["C_sp73"], 6),
                    "gap120_frozen": round(cc["C0"][-1] - cs["C_frozen"], 6),
                    "stop_cost_120": round(cc["C0"][-1] - cc["C1"][-1], 6),
                    "n_long": len(lo), "n_short": len(sh),
                    "C0_long_t120": (cl[-1] if cl else None),
                    "C0_short_t120": (cs2[-1] if cs2 else None),
                    "both_sides_positive_t120": bool(cl and cs2 and cl[-1] > 0 and cs2[-1] > 0)}
        mm[label] = dict(sorted(g.items(), key=lambda kv: -kv[1]["gap120_sp73"]))
    res[m] = mm
    print(m, "n", len(ents), "C0@120", mm["C0_t120"], "C1@120", mm["C1_t120"],
          "C2@120", mm["C2_t120"], "| stop costs", mm["stop_cost_at_120"],
          "| contract costs", mm["contract_cost_at_120"], "| C/7.3", ct["C_sp73"],
          "| argmax", best)

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
