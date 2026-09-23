#!/usr/bin/env python3
"""l8_grid — evaluate any (target, stop) contract over any conditioning cell, honestly
(entry must be traded first; conservative same-bar tie -> stop; unresolved marked at the
2-hour wall close; unfilled = 0.0 R and counted separately)."""
import gzip, json, os
import l8_lib as L

HERE = os.path.dirname(os.path.abspath(__file__))
TGT = [0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0]
STP = [-0.25, -0.4, -0.5, -0.75, -1.0, -1.25, -1.5, -2.0]
LAD = os.path.join(HERE, "l8_LADDER.jsonl.gz")


def load_ladder(path=LAD):
    out = {}
    with gzip.open(path, "rt") as fh:
        for line in fh:
            d = json.loads(line)
            out[(d["cid"], d["dt"])] = d
    return out


def resolve(lad, ti, si, count_unfilled=True):
    """R of one candidate under target TGT[ti] / stop STP[si]. Returns (r, outcome)."""
    if lad["fill_bar"] < 0:
        return (0.0, "no_fill") if count_unfilled else (None, "no_fill")
    bt = lad["tfav"][ti]
    bs = lad["tadv"][si]
    if bs > 0 and (bt <= 0 or bs <= bt):
        return STP[si], "stop"
    if bt > 0:
        return TGT[ti], "target"
    return lad["r_end"], "mark"


def grid(rows, ladder, count_unfilled=True):
    """Full |TGT| x |STP| table over `rows`."""
    lads = [ladder[(r["cid"], r["dt"])] for r in rows if (r["cid"], r["dt"]) in ladder]
    out = []
    for ti, T in enumerate(TGT):
        for si, S in enumerate(STP):
            vs = []
            cnt = {"target": 0, "stop": 0, "mark": 0, "no_fill": 0}
            for l in lads:
                r, o = resolve(l, ti, si, count_unfilled)
                cnt[o] += 1
                if r is not None:
                    vs.append(r)
            if not vs:
                continue
            n = len(vs)
            m = sum(vs) / n
            wins = [v for v in vs if v > 0]
            loss = [v for v in vs if v < 0]
            sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5 if n > 1 else 0.0
            out.append({"target": T, "stop": S, "n": n, "mean": round(m, 5),
                        "win": round(len(wins) / n, 4),
                        "t": round(m / (sd / n ** 0.5), 3) if sd > 0 else 0.0,
                        "target_rate": round(cnt["target"] / len(lads), 4),
                        "stop_rate": round(cnt["stop"] / len(lads), 4),
                        "mark_rate": round(cnt["mark"] / len(lads), 4),
                        "nofill_rate": round(cnt["no_fill"] / len(lads), 4),
                        "mean_win": round(sum(wins) / len(wins), 4) if wins else 0.0,
                        "mean_loss": round(sum(loss) / len(loss), 4) if loss else 0.0})
    return out


def best(cells, key="mean"):
    return max(cells, key=lambda c: c[key]) if cells else None


if __name__ == "__main__":
    rows = L.load()
    ladder = load_ladder()
    clean = [r for r in rows if r["born"] != "born_past_stop"]
    for name, pop in (("ALL", rows), ("CLEAN", clean)):
        g = grid(pop, ladder)
        b = best(g)
        base = [c for c in g if c["target"] == 2.0 and c["stop"] == -1.0][0]
        print("%s n=%d | declared 2R/-1R: mean %+.5f win %.4f tgt%.3f stop%.3f mark%.3f nofill%.3f"
              % (name, len(pop), base["mean"], base["win"], base["target_rate"], base["stop_rate"],
                 base["mark_rate"], base["nofill_rate"]))
        print("   BEST cell T=%.2f S=%.2f mean %+.5f win %.4f t=%+.2f  (lift %+.5f)"
              % (b["target"], b["stop"], b["mean"], b["win"], b["t"], b["mean"] - base["mean"]))
        json.dump(g, open(os.path.join(HERE, "L8_GRID_%s_V1.json" % name), "w"), indent=1)
