"""e5 step 13 — the intrabar-order bound on the survivor cell.

A resting limit is filled inside the bar whose adverse extreme first reaches entry_price.
Crediting that bar's FULL favourable extreme assumes the high came after the fill, which
for a limit sitting on the far side of the market is the optimistic ordering. Three walks:

  V0 as measured       favourable excursion credited from the fill bar (w0_ws convention)
  V1 conservative      favourable excursion credited only from the bar AFTER the fill bar;
                       the fill bar can still stop you out    <-- the honest lower bound
  V2 hostile           V1 and the fill bar's own adverse extreme is charged first

Reported for the pool, for XAUUSD, and for the XAUUSD x current_fvg_fill cell, per month,
as emitted and one-row-per-setup-day.
Writes E5_FILLBAR_V1.json
"""
import sys, os, json, gzip, random
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)

OUT = os.path.join(D, "E5_FILLBAR_V1.json")
MONTHS = ["january", "february", "march"]
SEED = 20260806


def load(m):
    rows = []
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
            sp = float(r.get("spread_r") or 0); cm = float(r.get("commission_r") or 0)
            sw = float(r.get("swap_cost_r") or 0); sl = float(r.get("expected_slippage_r") or 0)
            rows.append({"fav": r["fav"], "adv": adv, "cls": r["cls"], "fb": fb,
                         "tgt": (r.get("policy_target_r") or 2.0),
                         "cid": r["candidate_id"], "dt": r["decision_time_utc"],
                         "day": r["decision_time_utc"][:10],
                         "sym": r["symbol"], "fam": r.get("origin_family"),
                         "side": r.get("side"), "c73": sp / 7.3 + cm + sw + sl,
                         "cfr": sp + cm + sw + sl})
    return rows


def walk(e, trail=0.10, variant="V0"):
    fav, adv, cls, fb, tgt = e["fav"], e["adv"], e["cls"], e["fb"], e["tgt"]
    stop = -1.0; peak = -1e18
    start = fb
    if variant in ("V1", "V2"):
        # the fill bar can only hurt you
        if variant == "V2" and adv[fb] <= stop + 1e-12:
            return stop
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


def boot(v, n=1000, seed=SEED):
    if len(v) < 30:
        return None
    rnd = random.Random(seed); L = len(v)
    s = sorted(sum(v[rnd.randrange(L)] for _ in range(L)) / L for _ in range(n))
    return [round(s[int(0.025 * n)], 5), round(s[int(0.975 * n) - 1], 5)]


def blk(sub, trail, variant):
    n = len(sub)
    v = [walk(e, trail, variant) - e["c73"] for e in sub]
    lo = [walk(e, trail, variant) - e["c73"] for e in sub if (e["side"] or "").startswith("L")]
    sh = [walk(e, trail, variant) - e["c73"] for e in sub if (e["side"] or "").startswith("S")]
    return {"n": n, "net_sp73": round(sum(v) / n, 6), "ci95": boot(v),
            "net_frozen": round(sum(walk(e, trail, variant) - e["cfr"] for e in sub) / n, 6),
            "pos_pct": round(100 * sum(1 for x in v if x > 0) / n, 2),
            "net_long": (round(sum(lo) / len(lo), 6) if lo else None),
            "net_short": (round(sum(sh) / len(sh), 6) if sh else None)}


def setup_day(sub):
    best = {}
    for e in sub:
        k = (e["cid"], e["day"])
        if k not in best or e["dt"] < best[k]["dt"]:
            best[k] = e
    return list(best.values())


res = {"schema": "gtos.e5.fillbar.v1", "seed": SEED}
for m in MONTHS:
    rows = load(m)
    pops = {"POOL": rows,
            "XAUUSD": [e for e in rows if e["sym"] == "XAUUSD"],
            "XAU_x_fvg": [e for e in rows if e["sym"] == "XAUUSD" and e["fam"] == "current_fvg_fill"],
            "XAU_x_fvg_setupday": setup_day([e for e in rows if e["sym"] == "XAUUSD"
                                             and e["fam"] == "current_fvg_fill"])}
    mm = {}
    for pn, sub in pops.items():
        mm[pn] = {}
        for tr in (0.10, 0.25):
            for v in ("V0", "V1", "V2"):
                mm[pn]["t%.2f_%s" % (tr, v)] = blk(sub, tr, v)
        # also the as-shipped contract under V1, for reference
        mm[pn]["as_shipped_V1"] = blk(sub, None, "V1")
    res[m] = mm
    for pn in pops:
        a = mm[pn]["t0.10_V0"]; b = mm[pn]["t0.10_V1"]; c = mm[pn]["t0.10_V2"]
        print("%-9s %-20s n=%5d | V0 %+0.5f | V1 %+0.5f ci%s | V2 %+0.5f | V1 long %+0.5f short %+0.5f"
              % (m, pn, a["n"], a["net_sp73"], b["net_sp73"], b["ci95"], c["net_sp73"],
                 b["net_long"] or 0, b["net_short"] or 0))

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
