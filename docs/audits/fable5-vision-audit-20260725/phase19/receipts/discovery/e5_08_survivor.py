"""e5 step 8 — the one cohort where L2-F6's zero ceiling does NOT hold, put under every
control this lane can build.

Candidate: XAUUSD with a trailed stop. It is the only symbol whose trailed price-space
gross exceeds its own corrected-spread cost in ALL THREE months. Controls applied:
  * LONG / SHORT split           -- a directional edge must show on both sides
  * per-month, per-side, with n  -- no pooling across months
  * trail ladder                 -- is the effect a knife-edge in the parameter?
  * bootstrap 1000, seed 20260806
  * cost regime                  -- frozen / 7.3 / 8.5, and the break-even spread divisor
  * the same table for EVERY symbol so the boundary is stated, not asserted
Writes E5_SURVIVOR_V1.json
"""
import sys, os, json, gzip, random
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)

OUT = os.path.join(D, "E5_SURVIVOR_V1.json")
MONTHS = ["january", "february", "march"]
TRAILS = [0.1, 0.15, 0.2, 0.25, 0.35, 0.5]
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
                         "tgt": (r.get("policy_target_r") or 2.0), "sym": r["symbol"],
                         "fam": r.get("origin_family"), "side": r.get("side"),
                         "sess": r.get("session_bucket"),
                         "sp": sp, "cm": cm, "sww": sw, "sl": sl})
    return rows


def walk(e, trail):
    fav, adv, cls, fb, tgt = e["fav"], e["adv"], e["cls"], e["fb"], e["tgt"]
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


def boot(v, n=1000, seed=SEED):
    if len(v) < 30:
        return None
    rnd = random.Random(seed); L = len(v)
    s = sorted(sum(v[rnd.randrange(L)] for _ in range(L)) / L for _ in range(n))
    return [round(s[int(0.025 * n)], 5), round(s[int(0.975 * n) - 1], 5)]


def block(sub, trail):
    n = len(sub)
    net73 = [walk(e, trail) - (e["sp"] / 7.3 + e["cm"] + e["sww"] + e["sl"]) for e in sub]
    netfr = [walk(e, trail) - (e["sp"] + e["cm"] + e["sww"] + e["sl"]) for e in sub]
    net85 = [walk(e, trail) - (e["sp"] / 8.5 + e["cm"] + e["sww"] + e["sl"]) for e in sub]
    g = [walk(e, trail) for e in sub]
    mg = sum(g) / n
    csp = sum(e["sp"] for e in sub) / n
    cother = sum(e["cm"] + e["sww"] + e["sl"] for e in sub) / n
    # break-even spread divisor: mg = csp/x + cother  ->  x = csp/(mg - cother)
    be = (csp / (mg - cother)) if (mg - cother) > 1e-9 else None
    return {"n": n, "G": round(mg, 6),
            "net_frozen": round(sum(netfr) / n, 6),
            "net_sp73": round(sum(net73) / n, 6), "ci95_sp73": boot(net73),
            "net_sp85": round(sum(net85) / n, 6),
            "breakeven_spread_divisor": (round(be, 3) if be else None),
            "share_positive_pct": round(100 * sum(1 for x in net73 if x > 0) / n, 2)}


data = {m: load(m) for m in MONTHS}
res = {"schema": "gtos.e5.survivor.v1", "seed": SEED,
       "note": "net_sp73 = price-space gross under the trailed contract MINUS the corrected-spread "
               "cost. Positive means the cohort clears its own cost without any bet-size change."}

# every symbol, every month, trail 0.25 and 0.1, with the side split
allsym = {}
for sym in sorted({e["sym"] for m in MONTHS for e in data[m]}):
    rec = {}
    for m in MONTHS:
        sub = [e for e in data[m] if e["sym"] == sym]
        if len(sub) < 100:
            continue
        lo = [e for e in sub if (e["side"] or "").startswith("L")]
        sh = [e for e in sub if (e["side"] or "").startswith("S")]
        rec[m] = {"all_t025": block(sub, 0.25), "all_t010": block(sub, 0.10),
                  "long_t025": (block(lo, 0.25) if len(lo) >= 50 else None),
                  "short_t025": (block(sh, 0.25) if len(sh) >= 50 else None),
                  "long_t010": (block(lo, 0.10) if len(lo) >= 50 else None),
                  "short_t010": (block(sh, 0.10) if len(sh) >= 50 else None)}
    if len(rec) == 3:
        v = [rec[m]["all_t025"]["net_sp73"] for m in MONTHS]
        rec["min_net_sp73_t025"] = min(v)
        rec["all3_positive_t025"] = min(v) > 0
        v10 = [rec[m]["all_t010"]["net_sp73"] for m in MONTHS]
        rec["min_net_sp73_t010"] = min(v10)
        rec["all3_positive_t010"] = min(v10) > 0
        sides = []
        for m in MONTHS:
            a = rec[m]["long_t025"]; b = rec[m]["short_t025"]
            sides.append(bool(a and b and a["net_sp73"] > 0 and b["net_sp73"] > 0))
        rec["all3_both_sides_positive_t025"] = all(sides)
        rec["months_both_sides_positive_t025"] = sum(sides)
    allsym[sym] = rec
res["by_symbol"] = allsym

# the trail ladder on the surviving cohorts
surv = [s for s, r in allsym.items() if r.get("all3_positive_t025") or r.get("all3_positive_t010")]
res["survivors_t025_or_t010"] = surv
lad = {}
for s in surv:
    lad[s] = {m: {str(t): block([e for e in data[m] if e["sym"] == s], t) for t in TRAILS}
              for m in MONTHS}
res["survivor_trail_ladder"] = lad

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)

print("=== every symbol: trailed 0.25R net at the corrected spread, per month ===")
print("%-12s %9s %9s %9s %9s %6s %6s" % ("symbol", "JAN", "FEB", "MAR", "min", "3pos", "bothsides/3"))
rk = sorted([(r["min_net_sp73_t025"], s, r) for s, r in allsym.items() if "min_net_sp73_t025" in r], reverse=True)
for mn, s, r in rk:
    print("%-12s %+9.4f %+9.4f %+9.4f %+9.4f %6s %6d"
          % (s, r["january"]["all_t025"]["net_sp73"], r["february"]["all_t025"]["net_sp73"],
             r["march"]["all_t025"]["net_sp73"], mn, "YES" if r["all3_positive_t025"] else "",
             r["months_both_sides_positive_t025"]))
print()
print("SURVIVORS:", surv)
for s in surv:
    print("---", s)
    for m in MONTHS:
        r = allsym[s][m]
        print("  %-9s n=%4d  all t025 %+0.4f ci%s | LONG n=%d %+0.4f | SHORT n=%d %+0.4f | t010 %+0.4f | be_div %s"
              % (m, r["all_t025"]["n"], r["all_t025"]["net_sp73"], r["all_t025"]["ci95_sp73"],
                 (r["long_t025"] or {}).get("n", 0), (r["long_t025"] or {}).get("net_sp73", 0),
                 (r["short_t025"] or {}).get("n", 0), (r["short_t025"] or {}).get("net_sp73", 0),
                 r["all_t010"]["net_sp73"], r["all_t025"]["breakeven_spread_divisor"]))
print("wrote", OUT)
