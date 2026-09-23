"""e5 step 6 — the trail is the ONLY non-shrink component of L2-F6's rule. Is it real?

Two controls, both in PRICE space (original R units, stop -1R, structural target held):
  (1) the best FIXED-TIME exit  max_t E[R | exit at bar t]  -- if the trail only beats
      the as-shipped contract because it exits sooner in a negatively drifting instrument,
      some fixed t matches it.
  (2) a HOLDING-TIME-MATCHED PERMUTATION -- exit each trade at a bar drawn from the
      trail's OWN exit-bar distribution, independent of that trade's path. Same marginal
      holding time, zero path information. 200 permutations, seed 20260806.
Plus a trail ladder, a break-even ladder, and the per-month/per-family boundary.
Writes E5_TRAIL_V1.json
"""
import sys, os, json, gzip, random
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)

OUT = os.path.join(D, "E5_TRAIL_V1.json")
MONTHS = ["january", "february", "march"]
SEED = 20260806
NPERM = 200


def load(m):
    out = []
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
            out.append({"fav": r["fav"], "adv": adv, "cls": r["cls"], "fb": fb,
                        "tgt": (r.get("policy_target_r") or 2.0),
                        "sym": r.get("symbol"), "fam": r.get("origin_family"),
                        "side": r.get("side"),
                        "c": (float(r.get("spread_r") or 0) + float(r.get("commission_r") or 0)
                              + float(r.get("swap_cost_r") or 0) + float(r.get("expected_slippage_r") or 0)),
                        "c73": (float(r.get("spread_r") or 0) / 7.3 + float(r.get("commission_r") or 0)
                                + float(r.get("swap_cost_r") or 0) + float(r.get("expected_slippage_r") or 0))})
    return out


def walk(e, stop_r=-1.0, trail=None, be_at=None, max_bars=None, use_target=True):
    fav, adv, cls, fb, tgt = e["fav"], e["adv"], e["cls"], e["fb"], e["tgt"]
    L = len(fav)
    last = min(L, max_bars) if max_bars else L
    if last <= fb:
        return cls[min(fb, L - 1)], fb + 1
    stop = stop_r
    peak = -1e18
    for i in range(fb, last):
        f, a = fav[i], adv[i]
        if a <= stop + 1e-12:
            return stop, i + 1
        if use_target and f >= tgt - 1e-12:
            return tgt, i + 1
        if f > peak:
            peak = f
        if be_at is not None and peak >= be_at - 1e-12 and stop < 0.0:
            stop = 0.0
        if trail is not None and peak >= trail:
            stop = max(stop, peak - trail)
    return cls[last - 1], last


def exit_at_bar(e, t, stop_r=-1.0, use_target=True):
    """as-shipped contract but forced flat at bar t (1-based)."""
    return walk(e, stop_r=stop_r, max_bars=t, use_target=use_target)[0]


def mean(v):
    return sum(v) / len(v)


res = {"schema": "gtos.e5.trail.v1", "seed": SEED, "n_perm": NPERM}
for m in MONTHS:
    ents = load(m)
    n = len(ents)
    C = mean([e["c"] for e in ents]); C73 = mean([e["c73"] for e in ents])
    mm = {"n": n, "C_frozen": round(C, 6), "C_sp73": round(C73, 6)}
    base = mean([walk(e)[0] for e in ents])
    mm["as_shipped_G"] = round(base, 6)
    # fixed-time ladder
    ladder = {}
    for t in (1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60, 90, 120):
        ladder[t] = round(mean([exit_at_bar(e, t) for e in ents]), 6)
    bt = max(ladder, key=lambda k: ladder[k])
    mm["fixed_time_ladder"] = ladder
    mm["best_fixed_time"] = {"t": bt, "G": ladder[bt], "vs_as_shipped": round(ladder[bt] - base, 6)}
    # trail ladder
    tl = {}
    for tr in (0.1, 0.15, 0.2, 0.25, 0.35, 0.5, 0.75, 1.0):
        w = [walk(e, trail=tr) for e in ents]
        tl[str(tr)] = {"G": round(mean([x[0] for x in w]), 6),
                       "mean_exit_bar": round(mean([x[1] for x in w]), 3),
                       "median_exit_bar": sorted(x[1] for x in w)[n // 2],
                       "vs_as_shipped": round(mean([x[0] for x in w]) - base, 6)}
    mm["trail_ladder"] = tl
    # BE ladder
    bl = {}
    for b in (0.25, 0.5, 0.75, 1.0):
        bl[str(b)] = round(mean([walk(e, be_at=b)[0] for e in ents]) - base, 6)
    mm["be_ladder_vs_as_shipped"] = bl
    # permutation control on trail=0.25
    w25 = [walk(e, trail=0.25) for e in ents]
    g25 = mean([x[0] for x in w25])
    bars = [x[1] for x in w25]
    rnd = random.Random(SEED)
    perm = []
    for _ in range(NPERM):
        shuffled = bars[:]
        rnd.shuffle(shuffled)
        perm.append(mean([exit_at_bar(e, t) for e, t in zip(ents, shuffled)]))
    perm.sort()
    mm["trail025"] = {
        "G": round(g25, 6), "vs_as_shipped": round(g25 - base, 6),
        "mean_exit_bar": round(mean(bars), 3), "median_exit_bar": sorted(bars)[n // 2],
        "perm_control_mean": round(mean(perm), 6),
        "perm_control_p5_p95": [round(perm[int(0.05 * NPERM)], 6), round(perm[int(0.95 * NPERM) - 1], 6)],
        "excess_over_perm": round(g25 - mean(perm), 6),
        "perm_p_value_ge": round(sum(1 for p in perm if p >= g25) / NPERM, 5),
        "gap_sp73_with_trail": round(g25 - C73, 6),
    }
    # per family / symbol boundary of the trail value
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
            b = mean([walk(e)[0] for e in sub])
            t25 = mean([walk(e, trail=0.25)[0] for e in sub])
            g[k] = {"n": len(sub), "as_shipped": round(b, 6), "trail025": round(t25, 6),
                    "delta": round(t25 - b, 6),
                    "C_sp73": round(mean([e["c73"] for e in sub]), 6),
                    "gap_sp73_trailed": round(t25 - mean([e["c73"] for e in sub]), 6)}
        mm[label] = dict(sorted(g.items(), key=lambda kv: -kv[1]["delta"]))
    res[m] = mm
    print("%-9s n=%d as_shipped %+.5f | best fixed-time t=%d %+.5f | trail0.25 %+.5f (%+.5f) | "
          "perm ctrl %+.5f  excess %+.5f  p=%.4f | C/7.3 %.4f"
          % (m, n, base, bt, ladder[bt], g25, g25 - base, mean(perm), g25 - mean(perm),
             mm["trail025"]["perm_p_value_ge"], C73))

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
