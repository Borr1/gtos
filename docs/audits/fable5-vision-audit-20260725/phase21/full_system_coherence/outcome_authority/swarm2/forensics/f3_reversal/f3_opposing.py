#!/usr/bin/env python3
"""F3 (5) — THE SYSTEM'S OWN SIGNALS AT THE REVERSAL INSTANT.

Two questions nobody has asked:
  (a) At the moment a trade tops out, is the funnel generating an OPPOSING candidate
      on the same instrument?  Matched control: the same question at the trade's own
      earlier stalls (advances that retraced and resumed).
  (b) Over the whole corpus, how often does the book hold a long and a short on the
      same instrument at the same time?  If it does, one side's give-back is the
      other side's profit and the pair nets to a pure cost payment.
"""
import gzip, json, pickle, sys
from bisect import bisect_left, bisect_right
from collections import defaultdict
from pathlib import Path
import datetime as dt
import numpy as np

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
GEOM = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane2")
OUT = Path(__file__).resolve().parent
MONTHS = ["feb", "apr", "may", "jun", "jul"]
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
WIN = 15          # +/- minutes around the stall
R_USD = 250.0


def mins(s):
    return int((dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")) - EPOCH).total_seconds() // 60)


def ci_paired(dif, seed=9, n=2000):
    dif = np.asarray(dif, float)
    rng = np.random.default_rng(seed)
    b = rng.integers(0, len(dif), (n, len(dif)))
    mu = dif[b].mean(axis=1)
    return float(dif.mean()), [float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))], \
        float(2 * min((mu <= 0).mean(), (mu >= 0).mean()))


def main():
    # ---- candidate generation index: (symbol, side) -> sorted decision minutes ----
    gen = defaultdict(list)
    ncand = 0
    for m in MONTHS:
        with gzip.open(GEOM / f"geom_{m}.jsonl.gz", "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if not r.get("decision_time_utc"):
                    continue
                gen[(r["symbol"], str(r["side"]).upper())].append(mins(r["decision_time_utc"]))
                ncand += 1
    for k in gen:
        gen[k].sort()
    print(json.dumps({"stage": "gen_index", "candidates": ncand, "keys": len(gen)}), flush=True)

    trades, stalls = [], []
    for m in MONTHS:
        trades += pickle.load(gzip.open(TMP / f"f3_trades_{m}.pkl.gz", "rb"))
        stalls += pickle.load(gzip.open(TMP / f"f3_stalls_{m}.pkl.gz", "rb"))

    def count(sym, side, minute, w=WIN):
        a = gen.get((sym, side))
        if not a:
            return 0
        return bisect_right(a, minute + w) - bisect_left(a, minute - w)

    # ---- (a) opposing candidate at the stall, paired -------------------------
    byk = defaultdict(lambda: ([], []))
    bykS = defaultdict(lambda: ([], []))
    for s in stalls:
        opp = "SHORT" if str(s["side"]).upper() == "LONG" else "LONG"
        same = str(s["side"]).upper()
        o = 1.0 if count(s["sym"], opp, int(s["minute"])) > 0 else 0.0
        c = 1.0 if count(s["sym"], same, int(s["minute"])) > 0 else 0.0
        i = 0 if s["kind"] == "peak" else 1
        byk[s["k"]][i].append(o)
        bykS[s["k"]][i].append(c)
    out = {"schema": "gtos.f3.opposing.v1", "window_minutes": WIN,
           "n_candidates_indexed": ncand}
    for nm, D in (("opposing_side_candidate", byk), ("same_side_candidate", bykS)):
        dif, pk, pa = [], [], []
        for k, (P, Q) in D.items():
            if not P or not Q:
                continue
            dif.append(np.mean(P) - np.mean(Q)); pk.append(np.mean(P)); pa.append(np.mean(Q))
        d, c, p = ci_paired(dif)
        out[nm] = dict(n_trades=len(dif), peak_rate=float(np.mean(pk)),
                       pause_rate=float(np.mean(pa)), diff=d, ci95=c, p_two_sided=p)

    # ---- (b) simultaneous opposite exposure ---------------------------------
    bysym = defaultdict(list)
    for i, t in enumerate(trades):
        bysym[t["sym"]].append(i)
    net = np.array([t["term_gross"] - t["ded"] for t in trades])
    hedged = np.zeros(len(trades), dtype=bool)
    pairs = 0
    for sym, ids in bysym.items():
        ids.sort(key=lambda i: trades[i]["fill_min"])
        starts = [trades[i]["fill_min"] for i in ids]
        for a, i in enumerate(ids):
            ti = trades[i]
            hi = bisect_right(starts, ti["term_min"])
            for b in range(a + 1, hi):
                j = ids[b]
                tj = trades[j]
                if tj["fill_min"] >= ti["term_min"]:
                    break
                if str(tj["side"]).upper() != str(ti["side"]).upper():
                    hedged[i] = True; hedged[j] = True; pairs += 1
    out["simultaneous_opposite_exposure"] = dict(
        note="a filled trade whose life overlaps a filled trade of the OPPOSITE side "
             "on the SAME instrument, anywhere in the candidate pool",
        n_trades_involved=int(hedged.sum()), share_of_pool=float(hedged.mean()),
        overlapping_pairs=int(pairs),
        mean_net_R_hedged=float(net[hedged].mean()),
        mean_net_R_unhedged=float(net[~hedged].mean()),
        total_net_R_hedged=float(net[hedged].sum()),
        total_net_usd_hedged=float(net[hedged].sum() * R_USD))
    d, c, p = ci_paired(np.concatenate([net[hedged], -net[~hedged]])) if False else (None, None, None)
    a, b_ = net[hedged], net[~hedged]
    rng = np.random.default_rng(4)
    ia = rng.integers(0, len(a), (2000, len(a))); ib = rng.integers(0, len(b_), (2000, len(b_)))
    mu = a[ia].mean(axis=1) - b_[ib].mean(axis=1)
    out["simultaneous_opposite_exposure"].update(
        net_diff=float(a.mean() - b_.mean()),
        net_ci95=[float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))],
        net_p=float(2 * min((mu <= 0).mean(), (mu >= 0).mean())))
    (OUT / "F3_OPPOSING.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
