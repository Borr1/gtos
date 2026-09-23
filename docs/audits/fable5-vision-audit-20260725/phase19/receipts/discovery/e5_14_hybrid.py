"""e5 step 14 — the honest fill-bar convention, split by BORN STATE.

V0 credits the fill bar's own favourable extreme; V1 refuses it. Neither is right for the
whole pool, because the fill bar means different things in different born states
(w0-capture's census):

  born_at_limit    entry == the decision-instant market price. The 'fill bar' is the first
                   bar AFTER the decision, so its high genuinely comes after entry.  V0 IS
                   CORRECT HERE.
  born_marketable  the market is already through the entry level; you fill at the open of
                   the first bar.  V0 IS CORRECT HERE.
  born_resting     a genuine limit on the far side; price has to travel to it, and inside
                   the bar that first reaches it the high is more likely BEFORE the fill.
                   V1 IS THE HONEST BOUND HERE.

HYBRID = V0 on at_limit/marketable, V1 on resting.
Writes E5_HYBRID_V1.json
"""
import sys, os, json, gzip, random
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)

OUT = os.path.join(D, "E5_HYBRID_V1.json")
MONTHS = ["january", "february", "march"]
SEED = 20260806
EPS = 1e-9


def born(mk):
    if mk is None:
        return "unknown"
    if mk <= -1.0:
        return "past_stop"
    if abs(mk) <= 1e-6:
        return "at_limit"
    if mk > 0:
        return "resting"
    return "marketable"


def load(m):
    rows = []
    with gzip.open(os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % m), "rt") as f:
        for ln in f:
            r = json.loads(ln)
            mk = r["mkt_r_prev_close"]
            b = born(mk)
            if b == "past_stop":
                continue
            adv = r["adv"]
            fb = next((i for i in range(len(adv)) if adv[i] <= 1e-12), None)
            if fb is None:
                continue
            sp = float(r.get("spread_r") or 0); cm = float(r.get("commission_r") or 0)
            sw = float(r.get("swap_cost_r") or 0); sl = float(r.get("expected_slippage_r") or 0)
            rows.append({"fav": r["fav"], "adv": adv, "cls": r["cls"], "fb": fb, "born": b,
                         "tgt": (r.get("policy_target_r") or 2.0), "mk": mk,
                         "cid": r["candidate_id"], "dt": r["decision_time_utc"],
                         "day": r["decision_time_utc"][:10],
                         "sym": r["symbol"], "fam": r.get("origin_family"),
                         "side": r.get("side"), "c73": sp / 7.3 + cm + sw + sl,
                         "cfr": sp + cm + sw + sl})
    return rows


def walk(e, trail, conservative):
    fav, adv, cls, fb, tgt = e["fav"], e["adv"], e["cls"], e["fb"], e["tgt"]
    stop = -1.0; peak = -1e18
    start = fb
    if conservative:
        if adv[fb] <= stop + 1e-12:
            return stop
        start = fb + 1
        if start >= len(fav):
            return cls[-1]
    for i in range(start, len(fav)):
        f, a = fav[i], adv[i]
        if a <= stop + 1e-12:
            return stop
        if f >= tgt - 1e-12:
            return tgt
        if f > peak:
            peak = f
        if trail is not None and peak >= trail:
            stop = max(stop, peak - trail)
    return cls[-1]


def hybrid(e, trail):
    return walk(e, trail, conservative=(e["born"] == "resting"))


def boot(v, n=1000, seed=SEED):
    if len(v) < 30:
        return None
    rnd = random.Random(seed); L = len(v)
    s = sorted(sum(v[rnd.randrange(L)] for _ in range(L)) / L for _ in range(n))
    return [round(s[int(0.025 * n)], 5), round(s[int(0.975 * n) - 1], 5)]


def blk(sub, trail):
    n = len(sub)
    v = [hybrid(e, trail) - e["c73"] for e in sub]
    lo = [hybrid(e, trail) - e["c73"] for e in sub if (e["side"] or "").startswith("L")]
    sh = [hybrid(e, trail) - e["c73"] for e in sub if (e["side"] or "").startswith("S")]
    return {"n": n, "net_sp73": round(sum(v) / n, 6), "ci95": boot(v),
            "net_frozen": round(sum(hybrid(e, trail) - e["cfr"] for e in sub) / n, 6),
            "G": round(sum(hybrid(e, trail) for e in sub) / n, 6),
            "pos_pct": round(100 * sum(1 for x in v if x > 0) / n, 2),
            "n_long": len(lo), "net_long": (round(sum(lo) / len(lo), 6) if lo else None),
            "n_short": len(sh), "net_short": (round(sum(sh) / len(sh), 6) if sh else None)}


def setup_day(sub):
    best = {}
    for e in sub:
        k = (e["cid"], e["day"])
        if k not in best or e["dt"] < best[k]["dt"]:
            best[k] = e
    return list(best.values())


res = {"schema": "gtos.e5.hybrid.v1", "seed": SEED}
for m in MONTHS:
    rows = load(m)
    cen = {}
    for e in rows:
        cen[e["born"]] = cen.get(e["born"], 0) + 1
    mm = {"n": len(rows), "born_census": cen}
    pops = {
        "POOL": rows,
        "POOL_at_limit": [e for e in rows if e["born"] == "at_limit"],
        "POOL_resting": [e for e in rows if e["born"] == "resting"],
        "POOL_marketable": [e for e in rows if e["born"] == "marketable"],
        "XAUUSD": [e for e in rows if e["sym"] == "XAUUSD"],
        "XAU_x_fvg": [e for e in rows if e["sym"] == "XAUUSD" and e["fam"] == "current_fvg_fill"],
        "XAU_x_fvg_setupday": setup_day([e for e in rows if e["sym"] == "XAUUSD"
                                         and e["fam"] == "current_fvg_fill"]),
    }
    for pn, sub in pops.items():
        if not sub:
            continue
        mm[pn] = {"as_shipped": blk(sub, None), "t0.25": blk(sub, 0.25), "t0.10": blk(sub, 0.10)}
    # every symbol under the hybrid
    tbl = {}
    for sym in sorted({e["sym"] for e in rows}):
        sub = [e for e in rows if e["sym"] == sym]
        if len(sub) < 100:
            continue
        tbl[sym] = blk(sub, 0.10)
    mm["by_symbol_t010"] = dict(sorted(tbl.items(), key=lambda kv: -kv[1]["net_sp73"]))
    res[m] = mm
    print("===", m, "born:", cen)
    for pn in pops:
        if pn not in mm:
            continue
        a = mm[pn]["as_shipped"]; b = mm[pn]["t0.10"]
        print("  %-20s n=%5d | as_shipped %+0.5f | trail0.10 %+0.5f ci%s | long %+0.5f short %+0.5f"
              % (pn, b["n"], a["net_sp73"], b["net_sp73"], b["ci95"],
                 b["net_long"] or 0, b["net_short"] or 0))

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
