"""l2 step 13 — the best combined stop rule, priced, and the per-family trail table.

Combines the only two levers that measured anything:
  * the spread floor S(c): k_i = max(1, c*spread_r)      -- rescales the bet, cuts R-denominated cost
  * a 0.25R price trail                                  -- the only dynamic lever above noise
Trail is held at 0.25 x the ORIGINAL risk distance in PRICE at every k, so it is the same trail.
Writes L2_COMBINED_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

OUT = os.path.join(D, "L2_COMBINED_V1.json")


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 6) if v else None


rows = w0_ws.load(); byk = {w0_ws.key(r): r for r in rows}
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln); anch[(a["candidate_id"], a["decision_time_utc"])] = a

P = []
for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"])
    r = byk.get(k)
    if r is None:
        continue
    a = anch.get(k)
    m = a["mkt_r_prev_close"] if a else None
    if m is not None and m <= -1.0:
        continue
    P.append((rp, r))
N = len(P)


def run(kf, trail, label):
    gr = []; nf = []; n73 = []; ex = []
    for rp, r in P:
        sp = r.get("spread_r") or 0.0; cm = r.get("commission_r") or 0.0
        swp = r.get("swap_cost_r") or 0.0; sl = r.get("expected_slippage_r") or 0.0
        kk = kf(sp)
        tgt = rp.get("policy_target_r") or 2.0
        w = w0_ws.walk(rp, target_r=tgt, stop_r=-kk, trail=trail, require_fill=True)
        gr.append(w["r"] / kk); ex.append(w["exit_reason"])
        nf.append(w["r"] / kk - ((sp + cm + swp) / kk + sl))
        n73.append(w["r"] / kk - ((sp / 7.3 + cm + swp) / kk + sl))
    return {"rule": label, "n": len(gr), "gross_newunit": mean(gr),
            "win_pct": round(100 * sum(1 for x in gr if x > 0) / len(gr), 3),
            "net_frozen": mean(nf), "net_sp73": mean(n73),
            "exit_mix": {e: round(100 * ex.count(e) / len(ex), 2) for e in sorted(set(ex))}}


res = {"n": N, "population": "filled-required inside the walk; born_past_stop excluded"}
res["baseline"] = run(lambda sp: 1.0, None, "baseline k=1, no trail")
res["trail_only"] = run(lambda sp: 1.0, 0.25, "k=1 + 0.25R trail")
for c in (5, 10, 20):
    res["S%d" % c] = run(lambda sp, c=c: max(1.0, c * sp), None, "S(%d) spread floor" % c)
    res["S%d_trail" % c] = run(lambda sp, c=c: max(1.0, c * sp), 0.25, "S(%d) + 0.25R trail" % c)
res["k3_trail"] = run(lambda sp: 3.0, 0.25, "flat k=3.0 + 0.25R trail")
res["k3"] = run(lambda sp: 3.0, None, "flat k=3.0")

# per-family: baseline vs 0.25R trail, price space
fam = {}
for rp, r in P:
    f = r.get("origin_family")
    if not f:
        continue
    tgt = rp.get("policy_target_r") or 2.0
    b = w0_ws.walk(rp, target_r=tgt, require_fill=True)["r"]
    t = w0_ws.walk(rp, target_r=tgt, trail=0.25, require_fill=True)["r"]
    d = fam.setdefault(f, {"n": 0, "b": 0.0, "t": 0.0})
    d["n"] += 1; d["b"] += b; d["t"] += t
res["per_family_trail025"] = {f: {"n": d["n"], "baseline_gross": round(d["b"] / d["n"], 6),
                                  "trail025_gross": round(d["t"] / d["n"], 6),
                                  "delta": round((d["t"] - d["b"]) / d["n"], 6)}
                              for f, d in sorted(fam.items(), key=lambda kv: -kv[1]["n"])}
with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT, "n", N)
print("%-28s %9s %8s %11s %10s" % ("rule", "gross", "win%", "netFROZEN", "net/7.3"))
for k in ("baseline", "trail_only", "S5", "S5_trail", "S10", "S10_trail", "S20", "S20_trail", "k3", "k3_trail"):
    b = res[k]
    print("%-28s %+9.5f %8.3f %+11.5f %+10.5f" % (b["rule"][:28], b["gross_newunit"], b["win_pct"],
                                                  b["net_frozen"], b["net_sp73"]))
print("--- per family, 0.25R trail, price space ---")
for f, d in res["per_family_trail025"].items():
    print("%-34s n=%5d base=%+.5f trail=%+.5f delta=%+.5f" % (f[:34], d["n"], d["baseline_gross"],
                                                              d["trail025_gross"], d["delta"]))
