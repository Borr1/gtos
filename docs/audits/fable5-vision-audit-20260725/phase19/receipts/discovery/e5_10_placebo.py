"""e5 step 10 — the placebo that decides whether the trailed XAUUSD number is a signal
or a walk artifact.

A trailing stop cannot earn on a martingale (optional stopping). So if the walk is
unbiased, applying the SAME trail to the SAME paths with the trade's direction randomised
must return a mean of ~0 in price space. Three nulls:

  N1 SIGN-FLIP        every candidate's side reversed (fav<->-adv, cls<->-cls)
  N2 RANDOM SIGN      side flipped independently with p=0.5, 200 draws, seed 20260806
  N3 SHUFFLED PATHS   each candidate keeps its own geometry but is walked on ANOTHER
                      candidate's path from the same symbol (200 draws) -- destroys the
                      entry-timing information while keeping the instrument and the
                      trail mechanics identical

If the observed value sits outside the N2/N3 null, the entry timing carries the value.
Writes E5_PLACEBO_V1.json
"""
import sys, os, json, gzip, random
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)

OUT = os.path.join(D, "E5_PLACEBO_V1.json")
MONTHS = ["january", "february", "march"]
SEED = 20260806
NDRAW = 200
TRAILS = [0.10, 0.25]


def load(m):
    rows = []
    with gzip.open(os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % m), "rt") as f:
        for ln in f:
            r = json.loads(ln)
            mk = r["mkt_r_prev_close"]
            if mk is not None and mk <= -1.0:
                continue
            sp = float(r.get("spread_r") or 0); cm = float(r.get("commission_r") or 0)
            sw = float(r.get("swap_cost_r") or 0); sl = float(r.get("expected_slippage_r") or 0)
            rows.append({"fav": r["fav"], "adv": r["adv"], "cls": r["cls"],
                         "tgt": (r.get("policy_target_r") or 2.0), "sym": r["symbol"],
                         "side": r.get("side"), "sp": sp, "cm": cm, "sww": sw, "sl": sl,
                         "c73": sp / 7.3 + cm + sw + sl})
    return rows


def walk_arrays(fav, adv, cls, tgt, trail):
    fb = next((i for i in range(len(adv)) if adv[i] <= 1e-12), None)
    if fb is None:
        return None
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


def flip(e):
    return ([-x for x in e["adv"]], [-x for x in e["fav"]], [-x for x in e["cls"]])


def run(sub, trail, sign=None, paths=None):
    """sign: None = as-is; list of +-1 per row. paths: list of index into sub for the path swap."""
    vals = []
    for i, e in enumerate(sub):
        if paths is not None:
            p = sub[paths[i]]
            fav, adv, cls = p["fav"], p["adv"], p["cls"]
        else:
            fav, adv, cls = e["fav"], e["adv"], e["cls"]
        s = 1 if sign is None else sign[i]
        if s < 0:
            fav, adv, cls = ([-x for x in adv], [-x for x in fav], [-x for x in cls])
        r = walk_arrays(fav, adv, cls, e["tgt"], trail)
        if r is not None:
            vals.append(r)
    return (sum(vals) / len(vals)) if vals else None


res = {"schema": "gtos.e5.placebo.v1", "seed": SEED, "n_draw": NDRAW}
for m in MONTHS:
    rows = load(m)
    mm = {}
    for cohort, sub in (("ALL", rows), ("XAUUSD", [e for e in rows if e["sym"] == "XAUUSD"])):
        blk = {"n": len(sub), "C_sp73": round(sum(e["c73"] for e in sub) / len(sub), 6)}
        rnd = random.Random(SEED)
        bysym = {}
        for i, e in enumerate(sub):
            bysym.setdefault(e["sym"], []).append(i)
        for tr in TRAILS:
            obs = run(sub, tr)
            n1 = run(sub, tr, sign=[-1] * len(sub))
            n2 = []
            n3 = []
            for _ in range(NDRAW):
                sg = [1 if rnd.random() < 0.5 else -1 for _ in sub]
                n2.append(run(sub, tr, sign=sg))
                pth = []
                for i, e in enumerate(sub):
                    pool = bysym[e["sym"]]
                    pth.append(pool[rnd.randrange(len(pool))])
                n3.append(run(sub, tr, paths=pth))
            n2.sort(); n3.sort()
            blk["t%.2f" % tr] = {
                "observed_G": round(obs, 6),
                "N1_signflip_G": round(n1, 6),
                "N1_plus_obs": round(obs + n1, 6),
                "N2_randsign_mean": round(sum(n2) / NDRAW, 6),
                "N2_p5_p95": [round(n2[int(0.05 * NDRAW)], 6), round(n2[int(0.95 * NDRAW) - 1], 6)],
                "N2_p_ge_obs": round(sum(1 for x in n2 if x >= obs) / NDRAW, 5),
                "N3_shuffled_paths_mean": round(sum(n3) / NDRAW, 6),
                "N3_p5_p95": [round(n3[int(0.05 * NDRAW)], 6), round(n3[int(0.95 * NDRAW) - 1], 6)],
                "N3_p_ge_obs": round(sum(1 for x in n3 if x >= obs) / NDRAW, 5),
                "excess_over_N3": round(obs - sum(n3) / NDRAW, 6),
            }
        mm[cohort] = blk
        for tr in TRAILS:
            b = blk["t%.2f" % tr]
            print("%-9s %-7s trail=%.2f n=%5d obs %+0.5f | N1 flip %+0.5f (sum %+0.5f) | "
                  "N2 rand %+0.5f p=%.3f | N3 shuf %+0.5f p=%.3f excess %+0.5f | C/7.3 %.4f"
                  % (m, cohort, tr, blk["n"], b["observed_G"], b["N1_signflip_G"], b["N1_plus_obs"],
                     b["N2_randsign_mean"], b["N2_p_ge_obs"], b["N3_shuffled_paths_mean"],
                     b["N3_p_ge_obs"], b["excess_over_N3"], blk["C_sp73"]))
    res[m] = mm

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
