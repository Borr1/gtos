#!/usr/bin/env python3
"""l8_lib — shared loading + cell statistics for lane 8."""
import gzip, json, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = os.path.join(HERE, "l8_FRAME.jsonl.gz")


def load(path=FRAME):
    with gzip.open(path, "rt") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def stats(rows, metric="gross_r"):
    """n, win%, mean R, sum R, t-stat, mean winner, mean loser, payoff, breakeven win%."""
    vs = [r[metric] for r in rows if r.get(metric) is not None]
    n = len(vs)
    if n == 0:
        return None
    s = sum(vs)
    m = s / n
    wins = [v for v in vs if v > 0]
    loss = [v for v in vs if v <= 0]
    var = sum((v - m) ** 2 for v in vs) / (n - 1) if n > 1 else 0.0
    sd = math.sqrt(var)
    t = m / (sd / math.sqrt(n)) if sd > 0 and n > 1 else 0.0
    mw = sum(wins) / len(wins) if wins else 0.0
    ml = sum(loss) / len(loss) if loss else 0.0
    payoff = (mw / -ml) if ml < 0 else float("inf")
    be = (1.0 / (1.0 + payoff)) if payoff not in (0.0, float("inf")) else 0.0
    return {"n": n, "win": len(wins) / n, "mean": m, "sum": s, "sd": sd, "t": t,
            "mean_win": mw, "mean_loss": ml, "payoff": payoff, "be_win": be}


def cellstats(rows, metric="gross_r"):
    """Full stat block: raw, plus born-clean (drops born_past_stop) and honest-fill."""
    out = {}
    out["raw"] = stats(rows, metric)
    clean = [r for r in rows if r["born"] != "born_past_stop"]
    out["clean"] = stats(clean, metric)
    out["honest"] = stats(rows, "honest_r")
    out["n_past_stop"] = len(rows) - len(clean)
    return out


def fmt(s):
    if s is None:
        return "n=0"
    return "n=%d win=%.3f mean=%+.4f t=%+.2f" % (s["n"], s["win"], s["mean"], s["t"])
