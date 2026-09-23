"""e5 step 5 — the decisive test of L2-F6's own characterisation.

L2-F6 says the S(c) recovery is "loss reduction identical to trading smaller, not edge".
That is a factorisable claim and it has never been factorised. With per-row k_i from the
rule, the recovery splits EXACTLY into two additive parts:

  SHRINK  mean[(R_i(1)   - c_i)/k_i] - mean[R_i(1) - c_i]    -- same outcome, smaller bet
  WIDEN   mean[(R_i(k_i) - R_i(1))/k_i]                      -- the stop move itself
  (+ TRAIL, measured the same way on top of the widened stop)

If WIDEN ~ 0 then L2's characterisation is exactly right. If WIDEN > 0 the widening is
doing work of its own, and the size of that work is the honest value of the stop repair.
Also emits the per-family and per-symbol replication of S(10) across the three months.
Writes E5_DECOMPOSITION_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import e5_lib

OUT = os.path.join(D, "E5_DECOMPOSITION_V1.json")
MONTHS = ["january", "february", "march"]


def load(m):
    rows = []
    with gzip.open(os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % m), "rt") as f:
        for ln in f:
            rows.append(json.loads(ln))
    byk = {(r["candidate_id"], r["decision_time_utc"]): r for r in rows}
    anch = {k: {"mkt_r_prev_close": v["mkt_r_prev_close"]} for k, v in byk.items()}
    return e5_lib.build_entries(byk, iter(rows), anch)[0]


def walk_trail(e, kk, trail=0.25):
    """Same first-touch walk as w0_ws.walk but on the compressed ladder is not possible
    for a trail, so this replays the ladder's own source arrays. Returns R in ORIGINAL
    units with the stop at -kk and a trail of `trail` x ORIGINAL risk distance."""
    fav, adv, cls, fb, tgt = e["_fav"], e["_adv"], e["_cls"], e["_fb"], e["tgt"]
    stop = -kk
    peak = -1e18
    for i in range(fb, len(fav)):
        f, a = fav[i], adv[i]
        if a <= stop + 1e-12:
            return stop
        if f >= tgt - 1e-12:
            return tgt
        if f > peak:
            peak = f
        if peak >= trail:
            stop = max(stop, peak - trail)
    return cls[-1]


def decompose(ents, kf, label):
    n = len(ents)
    base_price = []          # R_i(1) - c_i           (as shipped, price space)
    shrunk = []              # (R_i(1) - c_i)/k_i     (pure bet reduction)
    widened = []             # (R_i(k)  - c_i)/k_i    (the rule)
    trailed = []             # (R_i(k,trail) - c_i)/k_i
    ks = []
    for e in ents:
        kk = kf(e)
        ks.append(kk)
        c = e["sp"] + e["cm"] + e["sww"] + e["sl"]
        r1 = e5_lib.walk_k(e, 1.0, "A")[0]
        rk = e5_lib.walk_k(e, kk, "A")[0]
        rt = walk_trail(e, kk)
        base_price.append(r1 - c)
        shrunk.append((r1 - c) / kk)
        widened.append((rk - c) / kk)
        trailed.append((rt - c) / kk)
    mb = sum(base_price) / n
    ms = sum(shrunk) / n
    mw = sum(widened) / n
    mt = sum(trailed) / n
    return {"rule": label, "n": n, "k_mean": round(sum(ks) / n, 4),
            "k_median": round(sorted(ks)[n // 2], 4),
            "net_as_shipped": round(mb, 6),
            "net_shrink_only": round(ms, 6),
            "net_rule": round(mw, 6),
            "net_rule_plus_trail": round(mt, 6),
            "part_SHRINK": round(ms - mb, 6),
            "part_WIDEN": round(mw - ms, 6),
            "part_TRAIL": round(mt - mw, 6),
            "total_recovery": round(mt - mb, 6),
            "widen_share_of_recovery_pct": (round(100 * (mw - ms) / (mt - mb), 2) if abs(mt - mb) > 1e-9 else None)}


res = {"schema": "gtos.e5.decomposition.v1",
       "note": "costs here are FROZEN and all four terms (spread+comm+swap+slip) scale with k "
               "(the physical reading). The corrected-spread variant divides spread_r by 7.3."}
for m in MONTHS:
    ents = load(m)
    # attach raw arrays for the trail walk
    rows = {}
    with gzip.open(os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % m), "rt") as f:
        for ln in f:
            r = json.loads(ln)
            rows[(r["candidate_id"], r["decision_time_utc"])] = r
    for e in ents:
        r = rows[(e["cid"], e["dt"])]
        e["_fav"], e["_adv"], e["_cls"] = r["fav"], r["adv"], r["cls"]
        e["_fb"] = next(i for i in range(len(r["adv"])) if r["adv"][i] <= 1e-12)
    mm = {"n": len(ents)}
    for c in (2, 5, 10, 20):
        mm["S%d_frozen" % c] = decompose(ents, (lambda e, c=c: max(1.0, c * e["sp"])), "S(%d) frozen spread" % c)
    mm["k3_flat"] = decompose(ents, lambda e: 3.0, "flat k=3")
    # the same decomposition with the CORRECTED spread inside the cost
    for e in ents:
        e["_sp_frozen"] = e["sp"]
        e["sp"] = e["_sp_frozen"] / 7.3
    for c in (5, 10, 20):
        mm["S%d_sp73cost" % c] = decompose(ents, (lambda e, c=c: max(1.0, c * e["_sp_frozen"])),
                                           "S(%d) rule on frozen spread, cost at /7.3" % c)
    for e in ents:
        e["sp"] = e["_sp_frozen"]
    # cohort replication of S(10)
    for label, kf in (("by_family", lambda e: e["fam"]), ("by_symbol", lambda e: e["sym"])):
        g = {}
        grp = {}
        for e in ents:
            k = kf(e)
            if k:
                grp.setdefault(str(k), []).append(e)
        for k, sub in grp.items():
            if len(sub) < 150:
                continue
            g[k] = decompose(sub, lambda e: max(1.0, 10 * e["sp"]), "S(10)")
        mm[label] = dict(sorted(g.items(), key=lambda kv: -kv[1]["part_WIDEN"]))
    res[m] = mm
    d = mm["S10_frozen"]
    print("%-9s S(10) kmed=%.2f | as_shipped %+.5f -> shrink %+.5f -> rule %+.5f -> +trail %+.5f | "
          "SHRINK %+.5f WIDEN %+.5f TRAIL %+.5f (widen=%.1f%% of recovery)"
          % (m, d["k_median"], d["net_as_shipped"], d["net_shrink_only"], d["net_rule"],
             d["net_rule_plus_trail"], d["part_SHRINK"], d["part_WIDEN"], d["part_TRAIL"],
             d["widen_share_of_recovery_pct"] or 0))

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
