"""e5 step 9 — the full repair stack, per step, per month, at constant bet size.

Every step is a per-trade R number at the ORIGINAL risk unit, so the steps are additive
and none of them is a disguised position-size change. The S(c) shrink is reported LAST
and separately, because it is a bet-size change and is therefore not comparable per trade.
Writes E5_STACK_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)

OUT = os.path.join(D, "E5_STACK_V1.json")
MONTHS = ["january", "february", "march"]


def load_all(m):
    rows = []
    with gzip.open(os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % m), "rt") as f:
        for ln in f:
            r = json.loads(ln)
            adv = r["adv"]
            fb = next((i for i in range(len(adv)) if adv[i] <= 1e-12), None)
            sp = float(r.get("spread_r") or 0); cm = float(r.get("commission_r") or 0)
            sw = float(r.get("swap_cost_r") or 0); sl = float(r.get("expected_slippage_r") or 0)
            rows.append({"fav": r["fav"], "adv": adv, "cls": r["cls"], "fb": fb,
                         "tgt": (r.get("policy_target_r") or 2.0), "sym": r["symbol"],
                         "mk": r["mkt_r_prev_close"],
                         "sp": sp, "cm": cm, "sww": sw, "sl": sl})
    return rows


def walk(e, trail=None):
    fav, adv, cls, fb, tgt = e["fav"], e["adv"], e["cls"], e["fb"], e["tgt"]
    if fb is None:
        return 0.0
    stop = -1.0; peak = -1e18
    for i in range(fb, len(fav)):
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


def cost(e, div):
    return e["sp"] / div + e["cm"] + e["sww"] + e["sl"]


def mean(v):
    return round(sum(v) / len(v), 6) if v else None


res = {"schema": "gtos.e5.stack.v1"}
for m in MONTHS:
    allr = load_all(m)
    steps = []

    def add(label, sub, div, trail, extra=None):
        v = [walk(e, trail) - cost(e, div) for e in sub]
        g = [walk(e, trail) for e in sub]
        c = [cost(e, div) for e in sub]
        d = {"step": label, "n": len(sub), "spread_divisor": div,
             "trail": trail, "net": mean(v), "G": mean(g), "C": mean(c)}
        if extra:
            d.update(extra)
        steps.append(d)
        return d

    add("0_as_shipped_full_pool_frozen", allr, 1.0, None)
    clean = [e for e in allr if not (e["mk"] is not None and e["mk"] <= -1.0)]
    add("1_drop_born_past_stop", clean, 1.0, None,
        {"dropped": len(allr) - len(clean),
         "dropped_pct": round(100 * (len(allr) - len(clean)) / len(allr), 3)})
    filled = [e for e in clean if e["fb"] is not None]
    add("2_require_fill", filled, 1.0, None, {"dropped": len(clean) - len(filled)})
    add("3_corrected_spread_7p3", filled, 7.3, None)
    add("4_trail_0p25R", filled, 7.3, 0.25)
    add("5_trail_0p10R", filled, 7.3, 0.10)
    cut = sorted(e["sp"] + e["cm"] + e["sww"] + e["sl"] for e in filled)[int(0.30 * len(filled)) - 1]
    cheap = [e for e in filled if (e["sp"] + e["cm"] + e["sww"] + e["sl"]) <= cut]
    add("6_cheapest_30pct_total_cost", cheap, 7.3, 0.10, {"cut_total_cost_r": round(cut, 6)})
    xau = [e for e in cheap if e["sym"] == "XAUUSD"]
    if len(xau) >= 100:
        add("7a_and_XAUUSD_only", xau, 7.3, 0.10)
    xau_all = [e for e in filled if e["sym"] == "XAUUSD"]
    add("7b_XAUUSD_only_no_cost_cut", xau_all, 7.3, 0.10)
    # bet-size lever, reported apart
    S10 = mean([(walk(e, 0.10) - cost(e, 7.3)) / max(1.0, 10 * e["sp"]) for e in filled])
    res[m] = {"steps": steps, "S10_shrink_on_top_of_step5_per_new_unit": S10,
              "n_pool": len(allr)}
    print("===", m, "n_pool", len(allr))
    prev = None
    for s in steps:
        d = ("      " if prev is None else "%+.5f" % (s["net"] - prev))
        print("  %-32s n=%6d  G=%+0.5f  C=%0.5f  net=%+0.5f  delta=%s"
              % (s["step"], s["n"], s["G"], s["C"], s["net"], d))
        prev = s["net"]
    print("  S(10) bet-size shrink applied on top of step 5 (per NEW risk unit): %+0.5f" % S10)

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
