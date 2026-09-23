#!/usr/bin/env python3
"""l7 shared helpers."""
import gzip, json, os, math

D = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(D, "l7_BASE_V1.jsonl.gz")


def load(path=BASE):
    out = []
    with gzip.open(path, "rt") as f:
        for ln in f:
            if ln.strip():
                out.append(json.loads(ln))
    return out


def mean(v):
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else None


def r5(x):
    return None if x is None else round(x, 5)


def q(v, p):
    v = sorted(x for x in v if x is not None)
    if not v:
        return None
    return v[min(len(v) - 1, max(0, int(round(p * (len(v) - 1)))))]


def stats(rs):
    """rs = list of realized R. Returns n, mean, win%, winMean, lossMean, payoff, be_realized."""
    rs = [x for x in rs if x is not None]
    n = len(rs)
    if n == 0:
        return dict(n=0)
    w = [x for x in rs if x > 0]
    l = [x for x in rs if x <= 0]
    wm = sum(w) / len(w) if w else 0.0
    lm = sum(l) / len(l) if l else 0.0
    payoff = (wm / abs(lm)) if lm else None
    be = (abs(lm) / (wm + abs(lm))) if (wm + abs(lm)) > 0 else None
    sd = math.sqrt(sum((x - sum(rs) / n) ** 2 for x in rs) / n) if n > 1 else 0.0
    return dict(n=n, mean=round(sum(rs) / n, 5), win=round(len(w) / n, 5),
                win_mean=round(wm, 5), loss_mean=round(lm, 5),
                payoff=round(payoff, 4) if payoff else None,
                be_realized=round(be, 5) if be else None,
                sd=round(sd, 5), t=round((sum(rs) / n) / (sd / math.sqrt(n)), 3) if sd > 0 and n > 1 else None)


def clean(rows):
    """The honest tradeable population: born-state known and NOT past-stop."""
    return [r for r in rows if r["born"] is not None and r["born"] != "born_past_stop"]
